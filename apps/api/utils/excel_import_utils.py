"""
Hardened workbook reading and the legacy sheet parser (`importer.py:39-192`).

Before any legacy logic: every zip entry ≤ 50 MB uncompressed and ≤ 200 MB in total, `defusedxml` (used by
openpyxl automatically), at most 50 sheets, and at most `max_policies + 2` rows and columns read per sheet. Any
openpyxl, zip or XML failure (chartsheets included) becomes `invalid_workbook`.

Known Tkinter Behaviour Kept 19: diagonal cells are ignored whatever they hold; blank, `None` and `none` are
blank; numbers are unrecognised ratings; numeric headers become `str(v)`; one bad sheet aborts the import; rows and
columns beyond n are ignored. New (Settled Decision 14): header gaps and duplicate policies are rejected.
"""

import zipfile
from dataclasses import dataclass, field
from io import BytesIO
from typing import Dict, List, Optional, Tuple

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

from constants.aggregation_constants import AGGREGATION_RULES, SETUP_MESSAGES
from constants.import_constants import IMPORT_MESSAGES, IMPORT_SETTINGS
from constants.rating_constants import DIAGONAL_LABEL, RATING_LABELS
from errors.import_errors import InvalidImportError, InvalidWorkbookError
from models.import_models import ImportErrorData

_RATINGS_LOWER = {label.lower(): label for label in RATING_LABELS}


@dataclass
class ParsedSheet:
    """One imported sheet."""

    sheet: str
    policies: List[str]
    ratings: List[List[str]]


@dataclass
class ParsedWorkbook:
    """Every imported sheet plus the legacy warnings by kind."""

    sheets: List[ParsedSheet] = field(default_factory=list)
    warnings: Dict[str, List[str]] = field(default_factory=lambda: {"skipped": [], "blank_cells": []})


class WorkbookReader:
    """Reads `.xlsx` bytes into decision-maker matrices."""

    def read(self, content: bytes) -> ParsedWorkbook:
        """
        Read every sheet as one matrix, in workbook order.

        Args:
            content: Workbook bytes (size already checked)

        Returns:
            ParsedWorkbook: Sheets and warnings

        Raises:
            InvalidWorkbookError: Unreadable, oversized zip entries, chartsheets
            InvalidImportError: Too many sheets or a sheet that breaks an import rule
        """
        self._check_zip(content)
        try:
            workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
        except Exception as exc:  # any openpyxl / zip / XML failure
            raise InvalidWorkbookError(f"load failed: {type(exc).__name__}") from exc
        try:
            if len(workbook.sheetnames) > IMPORT_SETTINGS["MAX_SHEETS"]:
                self._fail(IMPORT_MESSAGES["TOO_MANY_SHEETS"])
            parsed = ParsedWorkbook()
            for name in workbook.sheetnames:
                rows = self._rows(workbook, name)
                sheet = self.parse_sheet(name, rows, parsed.warnings)
                if sheet is not None:
                    parsed.sheets.append(sheet)
            return parsed
        finally:
            workbook.close()

    def parse_sheet(self, name: str, rows: List[Tuple], warnings: Dict[str, List[str]]) -> Optional[ParsedSheet]:
        """
        Port of the legacy sheet loop with the new header checks.

        Args:
            name: Sheet name
            rows: Cell values, row by row
            warnings: Warnings by kind, appended to

        Returns:
            Optional[ParsedSheet]: The matrix, or None when the sheet is skipped
        """
        if not rows:
            warnings["skipped"].append(IMPORT_MESSAGES["EMPTY_SHEET"].format(sheet=name))
            return None
        header = list(rows[0][1:])
        col_headers = [str(v).strip() for v in header if v is not None and str(v).strip()]
        if len(col_headers) < 2:
            warnings["skipped"].append(IMPORT_MESSAGES["SHORT_HEADER"].format(sheet=name))
            return None
        if len(col_headers) > AGGREGATION_RULES["MAX_POLICIES"]:
            self._fail(SETUP_MESSAGES["TOO_MANY_POLICIES"][1])
        self._check_gap(name, header)
        n = len(col_headers)
        row_headers = [str(row[0]).strip() if row and row[0] is not None else "" for row in rows[1 : n + 1]]
        if row_headers != col_headers:
            mismatches = [
                IMPORT_MESSAGES["HEADER_MISMATCH_LINE"].format(
                    row=i + 1, row_header=row_headers[i], col_header=col_headers[i]
                )
                for i in range(min(len(row_headers), len(col_headers)))
                if row_headers[i] != col_headers[i]
            ]
            detail = "\n".join(mismatches[: IMPORT_SETTINGS["HEADER_MISMATCHES_SHOWN"]])
            self._fail(IMPORT_MESSAGES["HEADER_MISMATCH"].format(sheet=name, detail=detail))
        if len(set(col_headers)) != n:
            self._fail(IMPORT_MESSAGES["DUPLICATE_POLICIES"].format(sheet=name))
        return self._cells(name, rows, col_headers, warnings)

    def _cells(self, name: str, rows: List[Tuple], policies: List[str], warnings) -> ParsedSheet:
        """Read the data cells: blanks are warnings, unrecognised values abort the import."""
        n = len(policies)
        codes = [f"P{i + 1}" for i in range(n)]
        ratings = [[DIAGONAL_LABEL if i == j else "" for j in range(n)] for i in range(n)]
        blanks: List[Tuple[str, str]] = []
        bad_values: List[str] = []
        for i in range(n):
            if i + 1 >= len(rows):
                blanks.extend((codes[i], codes[j]) for j in range(n) if i != j)
                continue
            row_data = rows[i + 1]
            for j in range(n):
                if i == j:
                    continue
                raw = row_data[j + 1] if j + 1 < len(row_data) else None
                val = str(raw).strip() if raw is not None else ""
                if not val or val.lower() == "none":
                    blanks.append((codes[i], codes[j]))
                    continue
                matched = _RATINGS_LOWER.get(val.lower())
                if matched is None:
                    bad_values.append(IMPORT_MESSAGES["BAD_VALUE_LINE"].format(row=codes[i], col=codes[j], value=val))
                else:
                    ratings[i][j] = matched
        if bad_values:
            shown = IMPORT_SETTINGS["BAD_VALUES_SHOWN"]
            more = IMPORT_MESSAGES["BAD_VALUES_MORE"] if len(bad_values) > shown else ""
            lines = "\n".join(bad_values[:shown])
            self._fail(
                IMPORT_MESSAGES["BAD_VALUES"].format(
                    sheet=name, lines=lines, more=more, allowed=", ".join(RATING_LABELS)
                )
            )
        if blanks:
            shown = IMPORT_SETTINGS["BLANK_CELLS_SHOWN"]
            cells = ", ".join(IMPORT_MESSAGES["BLANK_CELL"].format(row=r, col=c) for r, c in blanks[:shown])
            suffix = IMPORT_MESSAGES["BLANKS_SUFFIX"].format(count=len(blanks) - shown) if len(blanks) > shown else ""
            warnings["blank_cells"].append(
                IMPORT_MESSAGES["BLANKS"].format(sheet=name, count=len(blanks), cells=cells, suffix=suffix)
            )
        return ParsedSheet(sheet=name, policies=policies, ratings=ratings)

    def _check_gap(self, name: str, header: List) -> None:
        """Reject a blank header cell followed by a policy name (legacy reads data positionally, trap 14)."""
        filled = [v is not None and bool(str(v).strip()) for v in header]
        last = max(k for k, value in enumerate(filled) if value)
        for k in range(last):
            if not filled[k]:
                self._fail(IMPORT_MESSAGES["HEADER_GAP"].format(sheet=name, letter=get_column_letter(k + 2)))

    def _rows(self, workbook, name: str) -> List[Tuple]:
        """Read at most `max_policies + 2` rows and columns of one sheet."""
        limit = AGGREGATION_RULES["MAX_POLICIES"] + 2
        try:
            return list(workbook[name].iter_rows(max_row=limit, max_col=limit, values_only=True))
        except Exception as exc:  # chartsheets and malformed sheet XML
            raise InvalidWorkbookError(f"sheet read failed: {type(exc).__name__}") from exc

    def _check_zip(self, content: bytes) -> None:
        """Reject unreadable zips and entries that inflate beyond the limits (zip bombs)."""
        try:
            with zipfile.ZipFile(BytesIO(content)) as archive:
                sizes = [info.file_size for info in archive.infolist()]
        except (zipfile.BadZipFile, OSError, ValueError) as exc:
            raise InvalidWorkbookError(f"zip failed: {type(exc).__name__}") from exc
        if (
            any(size > IMPORT_SETTINGS["MAX_ENTRY_BYTES"] for size in sizes)
            or sum(sizes) > IMPORT_SETTINGS["MAX_TOTAL_BYTES"]
        ):
            raise InvalidWorkbookError("zip entry too large")

    def _fail(self, message: str) -> None:
        raise InvalidImportError("sheet rule", public_message=message, data=ImportErrorData(title="Import Error"))


workbook_reader = WorkbookReader()
