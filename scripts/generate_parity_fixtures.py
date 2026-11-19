"""
Generate the parity fixtures for `apps/api` from the legacy Tk app in `tk-app/`.

Run from the repository root (never from `apps/api`, which must not import `tk-app/`):

    uv run --frozen --python 3.13 --project tk-app python scripts/generate_parity_fixtures.py

The legacy modules are imported from `tk-app/` (Tk must be importable; no window is created, and `main` and
`font_loader` are never imported). Nothing under `tk-app/` is written except the gitignored `tk-app/.venv`.

Output (overwritten on every run), under `apps/api/tests/fixtures/`:
    parity/<case>__<variant>.json and parity/errors__<name>.json
    layouts/<case>__<layout>__<full|focus0>.json
    imports/<name>.xlsx and <name>.json
    xlsx/<name>.xlsx and <name>.json
"""

import sys
from pathlib import Path

sys.dont_write_bytecode = True
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tk-app"))

try:
    import tkinter  # noqa: F401
except ImportError as exc:  # the plan says: stop and report
    raise SystemExit(f"tkinter is not importable ({exc}); stop and report (plan Phase 2.1).") from exc

from typing import Dict, List  # noqa: E402

import importer  # noqa: E402
from parity import errors_capture, import_capture, layout_capture, xlsx_capture  # noqa: E402
from parity.aggregation_capture import build_matrices, run_aggregation  # noqa: E402
from parity.analysis_capture import aggregation_fields, analysis_outputs  # noqa: E402
from parity.cases import build_cases, seeded  # noqa: E402
from parity.io_utils import (  # noqa: E402
    EXAMPLE_WORKBOOK,
    FIXTURES_DIR,
    LAYOUTS_DIR,
    PARITY_DIR,
    environment,
    write_json,
)
from parity.text_capture import prompt, texts  # noqa: E402

LAYOUT_CASES = ["example", "r6x4", "negative6x3", "two2x3", "onelink3x1"]
XLSX_CASES = ["r6x4__median_lower", "r5x3__majority_first", "example__average"]


def example_case():
    """Import the bundled workbook with the legacy importer."""
    result = importer.import_matrices_from_excel(str(EXAMPLE_WORKBOOK))
    policies = result.matrices[0].policies
    size = range(len(policies))
    return policies, [(m.decision_maker, [[m.get_rating(i, j) for j in size] for i in size]) for m in result.matrices]


def request(project_name: str, policies: List[str], dms, variant: Dict, picks: List[Dict]) -> Dict:
    """The API `AnalysisRequest` for a variant (tie choices are the picks of the fake tie dialog)."""
    return {
        "project_name": project_name,
        "policies": policies,
        "decision_makers": [{"name": name, "ratings": ratings} for name, ratings in dms],
        "aggregation": {
            "method": variant["method"],
            "weights": variant.get("weights"),
            "median_choice": variant.get("median_choice"),
            "tie_choices": picks,
        },
    }


def run_variant(case, variant: Dict):
    """Run one variant through the legacy flow and write its fixture; return (key, matrices, result, request)."""
    name, project_name, policies, dms, _ = case
    matrices = build_matrices(policies, dms)
    captured = run_aggregation(project_name, matrices, variant)
    result = captured["result"]
    assert result is not None, captured["messages"]
    outputs = analysis_outputs(result)
    body = request(project_name, policies, dms, variant, captured["picks"])
    key = f"{name}__{variant['name']}"
    fixture = {
        "request": body,
        "aggregation": aggregation_fields(result, variant["method"]),
        **outputs,
        "texts": texts(result, outputs["insights"], captured["status"]),
        "prompt": prompt(result),
        "env": environment(),
    }
    write_json(PARITY_DIR / f"{key}.json", fixture)
    return key, matrices, result, body


def write_layouts(case_name: str, result, body: Dict) -> int:
    """Write the eight layout fixtures of one case."""
    count = 0
    for layout in layout_capture.all_layouts(result):
        focus = "full" if layout["focus"] is None else f"focus{layout['focus']}"
        write_json(LAYOUTS_DIR / f"{case_name}__{layout['layout']}__{focus}.json", {"request": body, **layout})
        count += 1
    return count


def dm_names_case() -> int:
    """XLSX `dm_names` case: names the legacy export crashes on or truncates (L3)."""
    policies = ["Alpha", "Beta", "Gamma"]
    dms = [(dm, matrix) for dm, (_, matrix) in zip(xlsx_capture.DM_NAMES, seeded(41, 3, 4), strict=True)]
    variant = {"name": "average", "method": "average"}
    matrices = build_matrices(policies, dms)
    result = run_aggregation("DM names", matrices, variant)["result"]
    fixture = xlsx_capture.export("dm_names", matrices, result)
    fixture["request"] = request("DM names", policies, dms, variant, [])
    write_json(FIXTURES_DIR / "xlsx" / "dm_names.json", fixture)
    return 1


def clear_outputs() -> None:
    """Remove fixtures from earlier runs so renamed cases leave nothing stale."""
    for folder in ("parity", "layouts", "imports", "xlsx"):
        for path in (FIXTURES_DIR / folder).glob("*.*"):
            path.unlink()


def run() -> None:
    """Generate every fixture and print the counts."""
    clear_outputs()
    counts = {"parity": 0, "errors": 0, "layouts": 0, "imports": 0, "xlsx": 0}
    for case in build_cases(example_case()):
        for variant in case[4]:
            key, matrices, result, body = run_variant(case, variant)
            counts["parity"] += 1
            if key in XLSX_CASES:
                xlsx_capture.export(key, matrices, result)
                counts["xlsx"] += 1
            if case[0] in LAYOUT_CASES and variant["name"] == "average":
                counts["layouts"] += write_layouts(case[0], result, body)
    counts["xlsx"] += dm_names_case()
    counts["errors"] = errors_capture.setup_errors() + errors_capture.weight_errors() + errors_capture.flow_errors()
    counts["imports"] = import_capture.generate()
    for kind, count in counts.items():
        print(f"{kind}: {count}")


if __name__ == "__main__":
    run()
