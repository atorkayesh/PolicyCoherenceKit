"""
XLSX fixtures (plan Phase 2.8): `app._export_to_excel(matrices, [result], path)` for one result, saved with a JSON
dump of every sheet (title, cell values, bold, fill, font colour, number format, column widths).
"""

from pathlib import Path
from typing import Dict, List

import app
from openpyxl import load_workbook

from parity.io_utils import XLSX_DIR, write_json

BASE31 = "Department of Energy Transition"
DM_NAMES = ["A/B", "Aggregated (Average)", f"{BASE31} Unit A12", f"{BASE31} Unit B"]


def _colour(colour) -> str:
    """Return an RGB string or `None` for an openpyxl colour."""
    if colour is None or colour.type != "rgb":
        return None
    return colour.rgb


def dump(path: Path) -> Dict:
    """Dump every sheet of a workbook."""
    wb = load_workbook(path)
    sheets: List[Dict] = []
    for ws in wb.worksheets:
        cells = []
        for row in ws.iter_rows():
            for cell in row:
                if cell.value is None and not cell.has_style:
                    continue
                fill = cell.fill.fgColor if cell.fill and cell.fill.fill_type == "solid" else None
                cells.append(
                    {
                        "ref": cell.coordinate,
                        "value": cell.value,
                        "bold": bool(cell.font.b),
                        "italic": bool(cell.font.i),
                        "fill": _colour(fill),
                        "font_colour": _colour(cell.font.color),
                        "number_format": cell.number_format,
                    }
                )
        widths = {letter: dim.width for letter, dim in sorted(ws.column_dimensions.items())}
        sheets.append({"title": ws.title, "cells": cells, "column_widths": widths})
    return {"sheets": sheets}


def export(name: str, matrices, result) -> Dict:
    """Export one result with the legacy code and write the workbook plus its dump (or the error)."""
    XLSX_DIR.mkdir(parents=True, exist_ok=True)
    path = XLSX_DIR / f"{name}.xlsx"
    fixture: Dict = {"name": name, "file": path.name}
    try:
        app._export_to_excel(matrices, [result], str(path))
    except Exception as exc:  # the legacy export crashes on invalid sheet titles (L3)
        fixture["error_message"] = f"{type(exc).__name__}: {exc}"
        path.unlink(missing_ok=True)
        fixture["file"] = None
    else:
        fixture.update(dump(path))
    write_json(XLSX_DIR / f"{name}.json", fixture)
    return fixture
