"""
Excel import (`POST /imports/workbook`): the legacy importer and app checks (`importer.py:39-192`,
`app.py:2950-2998`) behind the upload hardening.

Order: request `Content-Length` (checked by `UploadLimitMiddleware` before the body is read) → extension → size
(5 MB) → workbook read (`utils/excel_import_utils.py`) → sheet names → limits →
policy-list check (always; reference is the `policies` field, else the first sheet) → decision-maker clash (when
`decision_makers` is given) → nothing imported. Warnings are grouped by kind (L4).
"""

import asyncio
from pathlib import PurePath
from typing import List, Optional

from fastapi import UploadFile

from constants.aggregation_constants import AGGREGATION_RULES, SETUP_MESSAGES
from constants.import_constants import IMPORT_MESSAGES, IMPORT_SETTINGS, IMPORT_TITLES, IMPORT_WARNING_GROUPS
from errors.import_errors import (
    ExistingDecisionMakersError,
    InvalidImportError,
    NothingImportedError,
    PolicyListMismatchError,
    UnsupportedFileError,
    UploadTooLargeError,
)
from models.import_models import ImportData, ImportedMatrix, ImportErrorData, WarningGroup
from utils.excel_import_utils import ParsedWorkbook, WorkbookReader, workbook_reader


class WorkbookImportFeature:
    """Imports one decision-maker matrix per sheet."""

    def __init__(self, reader: Optional[WorkbookReader] = None, max_bytes: int = IMPORT_SETTINGS["MAX_UPLOAD_BYTES"]):
        """
        Create the feature.

        Args:
            reader: Workbook reader; defaults to the shared instance
            max_bytes: Largest accepted upload
        """
        self._reader = reader or workbook_reader
        self._max_bytes = max_bytes

    async def import_workbook(
        self, file: UploadFile, policies: Optional[List[str]], decision_makers: Optional[List[str]]
    ) -> ImportData:
        """
        Import an uploaded workbook.

        Args:
            file: The upload
            policies: The project's policy list, if it has one
            decision_makers: The project's decision-makers, if any

        Returns:
            ImportData: Matrices, grouped warnings and the summary message
        """
        filename = file.filename or ""
        if not filename.lower().endswith(IMPORT_SETTINGS["ALLOWED_EXTENSIONS"]):
            raise UnsupportedFileError("extension rejected")
        content = await self._read(file)
        return await asyncio.to_thread(self.import_bytes, content, filename, policies, decision_makers)

    def check_content_length(self, value: Optional[str]) -> None:
        """
        Reject a request whose declared size exceeds the limit plus the multipart overhead.

        Args:
            value: The `Content-Length` header, if any (missing or malformed values are left to `_read`)

        Raises:
            UploadTooLargeError: When the declared body is too large
        """
        if value is not None and value.isdigit():
            if int(value) > self._max_bytes + IMPORT_SETTINGS["MULTIPART_OVERHEAD_BYTES"]:
                raise UploadTooLargeError("Content-Length over the limit")

    def import_bytes(
        self, content: bytes, filename: str, policies: Optional[List[str]], decision_makers: Optional[List[str]]
    ) -> ImportData:
        """
        Import workbook bytes (see the module docstring for the order of checks).

        Returns:
            ImportData: The imported matrices
        """
        parsed = self._reader.read(content)
        names = [sheet.sheet.strip() for sheet in parsed.sheets]
        if any(not name for name in names) or len(set(names)) != len(names):
            self._invalid(IMPORT_MESSAGES["SHEET_NAMES"])
        if len(names) > AGGREGATION_RULES["MAX_DECISION_MAKERS"]:
            self._invalid(SETUP_MESSAGES["TOO_MANY_DECISION_MAKERS"][1])
        groups = self._groups(parsed)
        reference = [name.strip() for name in policies or [] if name.strip()]
        if not reference and parsed.sheets:
            reference = parsed.sheets[0].policies
        mismatches = [name for name, sheet in zip(names, parsed.sheets, strict=True) if sheet.policies != reference]
        if mismatches:
            lines = "\n".join(IMPORT_MESSAGES["POLICY_LIST_MISMATCH_LINE"].format(dm=dm) for dm in mismatches)
            raise PolicyListMismatchError(
                "policy list mismatch",
                public_message=IMPORT_MESSAGES["POLICY_LIST_MISMATCH"].format(lines=lines),
                data=ImportErrorData(title=IMPORT_TITLES["POLICY_LIST_MISMATCH"]),
            )
        existing = {name.strip() for name in decision_makers or [] if name.strip()}
        clashes = sorted(set(names) & existing)
        if clashes:
            message = SETUP_MESSAGES["EXISTING_DECISION_MAKERS"][1].format(names="\n".join(clashes))
            raise ExistingDecisionMakersError(
                "decision-maker clash",
                public_message=message,
                data=ImportErrorData(title=IMPORT_TITLES["EXISTING_DECISION_MAKERS"]),
            )
        if not parsed.sheets:
            raise NothingImportedError(
                "nothing imported", data=ImportErrorData(title=IMPORT_TITLES["NOTHING_IMPORTED"], warning_groups=groups)
            )
        count = len(parsed.sheets)
        summary = IMPORT_MESSAGES["WITH_WARNINGS" if groups else "SUCCESS"].format(count=count)
        return ImportData(
            policies=reference,
            codes=[f"P{i + 1}" for i in range(len(reference))],
            matrices=[
                ImportedMatrix(decision_maker=name, ratings=sheet.ratings)
                for name, sheet in zip(names, parsed.sheets, strict=True)
            ],
            warning_groups=groups,
            imported_count=count,
            summary_message=summary,
            suggested_project_name=PurePath(filename.replace("\\", "/")).stem,
        )

    def _groups(self, parsed: ParsedWorkbook) -> List[WarningGroup]:
        """Warnings grouped by kind with the L4 headings, in display order; empty groups are left out."""
        return [
            WarningGroup(kind=kind, heading=heading, messages=parsed.warnings[kind])
            for kind, heading in IMPORT_WARNING_GROUPS
            if parsed.warnings[kind]
        ]

    async def _read(self, file: UploadFile) -> bytes:
        """
        Check the upload's size in chunks and stop at the limit + 1 byte.

        FastAPI has already received the whole multipart body (spooled to disk) before this runs, so this only
        bounds the bytes kept in memory; `check_content_length` rejects declared oversize bodies before they are read.
        """
        chunks: List[bytes] = []
        size = 0
        while True:
            chunk = await file.read(IMPORT_SETTINGS["CHUNK_BYTES"])
            if not chunk:
                return b"".join(chunks)
            size += len(chunk)
            if size > self._max_bytes:
                raise UploadTooLargeError("upload over the limit")
            chunks.append(chunk)

    def _invalid(self, message: str) -> None:
        raise InvalidImportError(
            "import rule", public_message=message, data=ImportErrorData(title=IMPORT_TITLES["ERROR"])
        )


workbook_import_feature = WorkbookImportFeature()
