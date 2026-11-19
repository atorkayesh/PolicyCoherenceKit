"""
Import fixtures (plan Phase 2.7): workbooks built with openpyxl, the legacy `ImportResult` (or error), and the
messages of the legacy app flow (`app.py:2950-2998`) importing into an empty project.
"""

import shutil
from pathlib import Path
from typing import Dict, List, Optional

import app
import importer
from openpyxl import Workbook

from parity.aggregation_capture import recorded_messages
from parity.io_utils import EXAMPLE_WORKBOOK, IMPORTS_DIR, write_json

P3 = ["Alpha", "Beta", "Gamma"]


def _sheet(wb: Workbook, title: str, header: List, rows: List[List]) -> None:
    ws = wb.create_sheet(title)
    ws.append([None, *header])
    for row in rows:
        ws.append(row)


def _square(policies: List, fill) -> List[List]:
    """Rows `[name, cells...]` where `fill(i, j)` gives each cell (diagonal included)."""
    return [[name, *[fill(i, j) for j in range(len(policies))]] for i, name in enumerate(policies)]


def _ok(i: int, j: int) -> str:
    return "Neutral" if i == j else ["Enabling", "Constraining", "Reinforcing"][(i + j) % 3]


def workbooks() -> Dict[str, Dict]:
    """Return `{name: {"sheets": [(title, header, rows)], "api_expected_error": ...}}`."""
    p12 = [f"Policy {k}" for k in range(1, 13)]
    return {
        "labels_case_spaces": {"sheets": [("Expert A", P3, _square(P3, lambda i, j: f"  {_ok(i, j).upper()} "))]},
        "none_cells": {
            "sheets": [("Expert A", P3, _square(P3, lambda i, j: "none" if (i, j) == (0, 1) else _ok(i, j)))]
        },
        "many_blanks": {
            "sheets": [("Expert A", p12, _square(p12, lambda i, j: None if i < 2 and i != j else _ok(i, j)))]
        },
        "many_bad_values": {"sheets": [("Expert A", p12, _square(p12, lambda i, j: "good" if i == 0 else _ok(i, j)))]},
        "header_mismatch": {
            "sheets": [("Expert A", p12, [[f"Other {k}", *[_ok(k, j) for j in range(12)]] for k in range(12)])]
        },
        "empty_sheet": {"sheets": [("Empty", None, []), ("Expert A", P3, _square(P3, _ok))]},
        "short_header": {"sheets": [("Short", ["Only"], [["Only", "Neutral"]]), ("Expert A", P3, _square(P3, _ok))]},
        "numeric_headers": {"sheets": [("Expert A", [1, 2, 3], _square([1, 2, 3], _ok))]},
        "numeric_cells": {"sheets": [("Expert A", P3, _square(P3, lambda i, j: 3 if (i, j) == (0, 1) else _ok(i, j)))]},
        "gap_column": {
            "sheets": [("Expert A", ["Alpha", None, "Beta", "Gamma"], _square(P3, _ok))],
            "api_expected_error": 'Sheet "Expert A": header row has a blank policy name in column C.',
        },
        "diagonal_junk": {"sheets": [("Expert A", P3, _square(P3, lambda i, j: "junk" if i == j else _ok(i, j)))]},
        "one_bad_sheet": {
            "sheets": [
                ("Expert A", P3, _square(P3, _ok)),
                ("Expert B", P3, _square(P3, lambda i, j: "maybe" if (i, j) == (1, 2) else _ok(i, j))),
            ]
        },
        "different_policy_lists": {
            "sheets": [
                ("Expert A", P3, _square(P3, _ok)),
                ("Expert B", ["Alpha", "Beta"], _square(["Alpha", "Beta"], _ok)),
            ]
        },
        "duplicate_policies": {
            "sheets": [("Expert A", ["Alpha", "Beta", "Alpha"], _square(["Alpha", "Beta", "Alpha"], _ok))],
            "api_expected_error": 'Sheet "Expert A": Policy names must be unique.',
        },
    }


def _build(path: Path, sheets) -> None:
    wb = Workbook()
    wb.remove(wb.active)
    for title, header, rows in sheets:
        if header is None:
            wb.create_sheet(title)
        else:
            _sheet(wb, title, header, rows)
    wb.save(path)


def _legacy_import(path: Path) -> Dict:
    try:
        result = importer.import_matrices_from_excel(str(path))
    except (ValueError, ImportError) as exc:
        return {"error_message": str(exc)}
    return {
        "matrices": [
            {
                "decision_maker": m.decision_maker,
                "policies": m.policies,
                "ratings": [[m.get_rating(i, j) for j in range(len(m.policies))] for i in range(len(m.policies))],
            }
            for m in result.matrices
        ],
        "warnings": result.warnings,
    }


def _app_flow(path: Path) -> List:
    """Messages of `_import_excel_into_project` for an empty project (reference = first sheet)."""
    obj = app.PolicyCoherenceApp.__new__(app.PolicyCoherenceApp)
    obj.root = None
    obj._ask_excel_path = lambda: str(path)
    obj._create_dm_tab = lambda _proj, _matrix: None
    obj._set_status = lambda _text: None
    obj._update_topbar = lambda: None
    with recorded_messages() as recorder:
        obj._import_excel_into_project(app.Project(name="Import"))
    return recorder.messages


def generate() -> int:
    """Write every import workbook and its expected-output JSON; return the count."""
    IMPORTS_DIR.mkdir(parents=True, exist_ok=True)
    cases: Dict[str, Optional[Dict]] = workbooks()
    cases["wef_nexus_example"] = None
    for name, spec in cases.items():
        path = IMPORTS_DIR / f"{name}.xlsx"
        if spec is None:
            shutil.copyfile(EXAMPLE_WORKBOOK, path)
            spec = {}
        else:
            _build(path, spec["sheets"])
        fixture = {"file": path.name, "legacy": _legacy_import(path), "app_messages": _app_flow(path)}
        if spec.get("api_expected_error"):
            fixture["api_expected_error"] = spec["api_expected_error"]
        write_json(IMPORTS_DIR / f"{name}.json", fixture)
    return len(cases)
