"""
Download file names (label fix L10).

The legacy export suggested `f"{project}_coherence.xlsx".replace(" ", "_")` (`app.py:3053`), which can contain
characters that are invalid in file names. Here those characters are replaced too, and the `Content-Disposition`
header carries an ASCII fallback plus the RFC 5987 `filename*` form for non-ASCII names.
"""

import re
from urllib.parse import quote

from constants.export_constants import EXPORT_FILENAMES

# Characters that are invalid in a file name on common systems, plus C0 control characters and DEL.
_INVALID_FILENAME_CHARS = re.compile(r'[/\\:*?"<>|\x00-\x1f\x7f]')
_NON_ASCII = re.compile(r"[^\x20-\x7e]")


class FilenameBuilder:
    """Builds safe download names and their `Content-Disposition` header."""

    def xlsx_export_name(self, project_name: str) -> str:
        """
        Build the XLSX export name for a project.

        Args:
            project_name: Trimmed project name

        Returns:
            str: `{project}_coherence.xlsx` with spaces and invalid characters replaced by `_`
        """
        name = EXPORT_FILENAMES["XLSX_TEMPLATE"].format(project=project_name).replace(" ", "_")
        return _INVALID_FILENAME_CHARS.sub("_", name)

    def content_disposition(self, filename: str) -> str:
        """
        Build an attachment header with an ASCII fallback and the UTF-8 `filename*` parameter.

        Args:
            filename: Suggested file name (may contain non-ASCII characters)

        Returns:
            str: `attachment; filename="<ascii>"; filename*=UTF-8''<percent-encoded>`
        """
        safe = _INVALID_FILENAME_CHARS.sub("_", filename)
        fallback = _NON_ASCII.sub("_", safe)
        return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{quote(safe, safe='')}"


filename_builder = FilenameBuilder()
