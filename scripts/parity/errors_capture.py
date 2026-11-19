"""
Error fixtures (plan Phase 2.4): the exact legacy message the user sees, captured from the legacy code path with
the patched `messagebox`. Each fixture records `source`, `api_message_rule` and the input the API test replays.
Rules: `identical`, `identical_except_L2`, `identical_after_L11`, `documentation` (not replayed).
"""

import random
from typing import Dict, List, Optional

import aggregation_dialog
import aggregator
import dialogs
from constants import COHERENCE_RATINGS

from parity.aggregation_capture import build_matrices, recorded_messages, run_aggregation
from parity.cases import random_matrix
from parity.io_utils import PARITY_DIR, write_json

DMS = ["Expert A", "Expert B", "Expert C"]
POLICIES = ["Alpha", "Beta", "Gamma", "Delta"]


class _Var:
    """Stub for `StringVar` / entries: `.get()` and `focus_set()`."""

    def __init__(self, value: str = "") -> None:
        self._value = value

    def get(self) -> str:
        return self._value

    def focus_set(self) -> None:
        return None


def _setup(project: str, dms: List[str], policies: List[str], existing_dms=(), existing_projects=()) -> List:
    dlg = dialogs.ProjectSetupDialog.__new__(dialogs.ProjectSetupDialog)
    dlg._include_project_name = True
    dlg._existing_project_names = set(existing_projects)
    dlg._existing_dm_names = set(existing_dms)
    dlg._fixed_policies = []
    dlg._dm_vars = [_Var(name) for name in dms]
    dlg._policy_vars = [_Var(name) for name in policies]
    dlg._entry_fields = {}
    dlg._get_project_name = lambda: project.strip()
    dlg._close = lambda: None
    with recorded_messages() as recorder:
        dlg._on_ok()
    return recorder.messages


def _weights_dialog(raw: List[str]) -> List:
    dlg = aggregation_dialog.WeightDialog.__new__(aggregation_dialog.WeightDialog)
    dlg._decision_makers = DMS
    dlg._vars = [_Var(value) for value in raw]
    dlg._entries = [_Var() for _ in raw]
    dlg.destroy = lambda: None
    with recorded_messages() as recorder:
        dlg._on_ok()
    return recorder.messages


def _aggregator_error(call) -> Optional[str]:
    try:
        call()
    except ValueError as exc:
        return str(exc)
    return None


def _project(seed: int, blanks: int = 0) -> List:
    rng = random.Random(seed)
    matrices = [(name, random_matrix(rng, len(POLICIES), COHERENCE_RATINGS)) for name in DMS]
    cells = [(i, j) for i in range(len(POLICIES)) for j in range(len(POLICIES)) if i != j]
    for i, j in cells[:blanks]:
        matrices[0][1][i][j] = ""
    return matrices


def _request(matrices, method: str, weights=None) -> Dict:
    return {
        "project_name": "Errors",
        "policies": POLICIES,
        "decision_makers": [{"name": name, "ratings": ratings} for name, ratings in matrices],
        "aggregation": {"method": method, "weights": weights, "median_choice": None, "tie_choices": []},
    }


def _write(name: str, source: str, rule: str, messages: List, **extra) -> None:
    title, message = messages[0] if messages else (None, None)
    fixture = {"name": name, "source": source, "api_message_rule": rule, "title": title, "error_message": message}
    write_json(PARITY_DIR / f"errors__{name}.json", {**fixture, **extra})


def setup_errors() -> int:
    """All `dialogs.py:1080-1124` messages."""
    cases = {
        "setup_project_name_required": ("", DMS, POLICIES, (), ()),
        "setup_duplicate_project": ("Errors", DMS, POLICIES, (), ("Errors",)),
        "setup_decision_makers_required": ("Errors", [], POLICIES, (), ()),
        "setup_duplicate_decision_makers": ("Errors", ["A", "B", "A"], POLICIES, (), ()),
        "setup_existing_decision_makers": ("Errors", ["Zed", "Bea", "Al"], POLICIES, ("Al", "Zed"), ()),
        "setup_too_few_policies": ("Errors", DMS, ["Alpha"], (), ()),
        "setup_duplicate_policies": ("Errors", DMS, ["Alpha", "Beta", "Alpha"], (), ()),
    }
    for name, (project, dms, policies, existing, projects) in cases.items():
        rule = "documentation" if name == "setup_duplicate_project" else "identical"
        setup = {"project_name": project, "decision_makers": dms, "policies": policies}
        setup["existing_decision_makers"] = list(existing)
        _write(name, "dialogs.py:1080-1124", rule, _setup(project, dms, policies, existing, projects), setup=setup)
    return len(cases)


def weight_errors() -> int:
    """Weight dialog messages (`aggregation_dialog.py:570-613`) and the aggregator texts as documentation."""
    matrices = _project(7)
    cases = {
        "weights_sum_0_9": [0.3, 0.3, 0.3],
        "weights_034_034_033": [0.34, 0.34, 0.33],
        "weights_033_x3": [0.33, 0.33, 0.33],
        "weights_out_of_range": [1.2, -0.1, -0.1],
    }
    for name, weights in cases.items():
        messages = _weights_dialog([repr(w) for w in weights])
        rule = "identical_except_L2" if messages[0][0] == "Weights Do Not Sum to 1" else "identical"
        doc = _aggregator_error(lambda w=weights: aggregator._validate_weights(w, 3))
        _write(
            name,
            "aggregation_dialog.py:570-613",
            rule,
            messages,
            request=_request(matrices, "weighted", weights),
            raw_weights=[repr(w) for w in weights],
            aggregator_message=doc,
        )
    raws = {
        "weights_check_missing": ["", "0.5", "0.5"],
        "weights_check_invalid": ["abc", "0.5", "0.5"],
        "weights_check_range": ["1.5", "0.5", "0.5"],
        "weights_check_nan": ["nan", "0.5", "0.5"],
    }
    for name, raw in raws.items():
        _write(
            name,
            "aggregation_dialog.py:570-613",
            "identical",
            _weights_dialog(raw),
            raw_weights=raw,
            decision_makers=DMS,
        )
    count = _aggregator_error(lambda: aggregator._validate_weights([0.5, 0.5], 3))
    _write(
        "weights_count",
        "aggregator.py:351-354",
        "identical",
        [("Invalid Weights", count)],
        request=_request(matrices, "weighted", [0.5, 0.5]),
    )
    return len(cases) + len(raws) + 1


def flow_errors() -> int:
    """Incomplete matrices and an unresolved tie, plus documentation-only aggregator messages."""
    blank = _project(11, blanks=12)
    captured = run_aggregation("Errors", build_matrices(POLICIES, blank), {"method": "average"})
    _write(
        "incomplete",
        "app.py:2546-2556",
        "identical_after_L11",
        captured["messages"],
        request=_request(blank, "average"),
    )
    seed = next(s for s in range(100) if aggregator.aggregate_majority(build_matrices(POLICIES, _project(s))).ties)
    tied = _project(seed)
    result = aggregator.aggregate_majority(build_matrices(POLICIES, tied))
    dlg = aggregation_dialog.TieResolutionDialog.__new__(aggregation_dialog.TieResolutionDialog)
    dlg._ties = result.ties
    dlg._vars = [_Var("") for _ in result.ties]
    dlg.destroy = lambda: None
    with recorded_messages() as recorder:
        dlg._on_ok()
    resolve = _aggregator_error(lambda: aggregator.resolve_ties(result))
    _write(
        "unresolved_tie",
        "aggregation_dialog.py:779-787",
        "identical_after_L11",
        recorder.messages,
        request=_request(tied, "majority"),
        resolve_ties_message=resolve,
    )
    complete = build_matrices(POLICIES, _project(3))
    docs = {
        "median_invalid_choice": lambda: aggregator.aggregate_median(complete, even_choice="middle"),
        "empty_matrix_list": lambda: aggregator.aggregate_average([]),
        "policy_mismatch": lambda: aggregator.aggregate_average(
            complete[:1] + build_matrices(["Alpha", "Beta", "Delta", "Gamma"], _project(3)[1:2])
        ),
    }
    for name, call in docs.items():
        _write(name, "aggregator.py:337-370", "documentation", [(None, _aggregator_error(call))])
    return 2 + len(docs)
