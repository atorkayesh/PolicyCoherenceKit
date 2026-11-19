"""
XLSX cell styling ported from `_export_to_excel` (`app.py:3093-3110`): `hcell`, `auto_width`, and text cells that
are always strings, never formulas (label fix L15).
"""

from typing import Any, Optional

from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.worksheet import Worksheet

from constants.export_constants import XLSX_STYLE


class ExcelStyler:
    """Writes styled cells."""

    def __init__(self) -> None:
        """Create the thin light-grey border used by headers and matrix cells."""
        thin = Side(style="thin", color=XLSX_STYLE["BORDER_COLOUR"])
        self.border = Border(left=thin, right=thin, top=thin, bottom=thin)

    def cell(self, ws: Worksheet, row: int, col: int, value: Any):
        """
        Write a value; text is stored as a string even when it starts with `=` (L15).

        Args:
            ws: Worksheet
            row: 1-based row
            col: 1-based column
            value: Text or number

        Returns:
            Cell: The written cell
        """
        cell = ws.cell(row=row, column=col, value=value)
        if isinstance(value, str):
            cell.data_type = "s"
        return cell

    def header(self, ws: Worksheet, row: int, col: int, value: Any):
        """`hcell`: white bold text on navy, centred, bordered."""
        cell = self.cell(ws, row, col, value)
        self.header_style(cell)
        return cell

    def header_style(self, cell) -> None:
        """Apply the header style to a cell."""
        cell.font = Font(bold=True, color=XLSX_STYLE["HEADER_FONT_COLOUR"])
        cell.fill = PatternFill("solid", fgColor=XLSX_STYLE["HEADER_FILL"])
        cell.alignment = Alignment(horizontal="center")
        cell.border = self.border

    def fill(self, colour: str) -> PatternFill:
        """Solid fill from a `#rrggbb` colour (`.lstrip("#").upper()` as legacy)."""
        return PatternFill("solid", fgColor=colour.lstrip("#").upper())

    def font(self, colour: Optional[str] = None, bold: bool = False, italic: bool = False) -> Font:
        """Font with an optional `#rrggbb` colour."""
        if colour is None:
            return Font(bold=bold, italic=italic)
        return Font(bold=bold, italic=italic, color=colour.lstrip("#").upper())

    def auto_width(self, ws: Worksheet) -> None:
        """`auto_width`: longest truthy value + 4, at least 14 (zero values are skipped)."""
        for col in ws.columns:
            letter = col[0].column_letter
            max_len = max((len(str(c.value)) for c in col if c.value), default=0)
            ws.column_dimensions[letter].width = max(
                max_len + XLSX_STYLE["COLUMN_PADDING"], XLSX_STYLE["MIN_COLUMN_WIDTH"]
            )


excel_styler = ExcelStyler()
