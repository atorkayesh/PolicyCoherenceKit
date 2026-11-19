"""
Run the legacy aggregation flow (`app.py:2533-2611`) headlessly.

`PolicyCoherenceApp._run_aggregation` runs unchanged on an instance built with `__new__`. The four dialogs are
replaced in `app`'s namespace by fakes whose `.result` is preset from the variant, `tkinter.messagebox` records
`(title, message)`, and `_create_analysis_tabs` / `_set_status` capture the result and the status text. A fresh
`AggregationResult` is produced per variant because legacy `_cached_*` fields are never invalidated.
"""

from contextlib import contextmanager
from tkinter import messagebox
from typing import Dict, Iterator, List, Optional, Tuple

import app
from models import PolicyMatrix, generate_codes

Matrix = List[List[str]]


class MessageRecorder:
    """Replaces `tkinter.messagebox.show*` and records every `(title, message)`."""

    def __init__(self) -> None:
        self.messages: List[Tuple[str, str]] = []

    def __call__(self, title: str, message: str, **_kwargs) -> None:
        self.messages.append((title, message))


@contextmanager
def recorded_messages() -> Iterator[MessageRecorder]:
    """Patch `showinfo`, `showwarning` and `showerror` for the duration of the block."""
    recorder = MessageRecorder()
    originals = {name: getattr(messagebox, name) for name in ("showinfo", "showwarning", "showerror")}
    for name in originals:
        setattr(messagebox, name, recorder)
    try:
        yield recorder
    finally:
        for name, original in originals.items():
            setattr(messagebox, name, original)


def build_matrices(policies: List[str], decision_makers: List[Tuple[str, Matrix]]) -> List[PolicyMatrix]:
    """Build legacy `PolicyMatrix` objects; blank cells stay unset as in the matrix editor."""
    codes = generate_codes(policies)
    matrices = []
    for name, ratings in decision_makers:
        matrix = PolicyMatrix(decision_maker=name, policies=list(policies), codes=list(codes))
        for i, row in enumerate(ratings):
            for j, label in enumerate(row):
                if label:
                    matrix.set_rating(i, j, label)
        matrices.append(matrix)
    return matrices


def _pick(labels: List[str], rule: str) -> str:
    """Return the tied label at index 0, len - 1 or len // 2 (plan Phase 2.3)."""
    index = {"first": 0, "last": len(labels) - 1, "middle": len(labels) // 2}[rule]
    chosen = labels[index]
    assert chosen in labels
    return chosen


def _fake_dialog(result_value):
    """Return a dialog class whose instances expose a preset `.result`."""

    class FakeDialog:
        def __init__(self, *_args, **_kwargs) -> None:
            self.result = result_value

    return FakeDialog


def _fake_tie_dialog(rule: Optional[str], picks: List[Dict]):
    """Return a tie dialog class that writes each `TiedCell.chosen` with the variant rule."""

    class FakeTieDialog:
        def __init__(self, _parent, ties) -> None:
            for tie in ties:
                tie.chosen = _pick(tie.tied_labels, rule)
                picks.append({"row": tie.row, "col": tie.col, "rating": tie.chosen})
            self.result = ties

    return FakeTieDialog


class _Root:
    """Stub Tk root: `wait_window` returns at once because the fake dialogs are already answered."""

    def wait_window(self, _window) -> None:
        return None


def run_aggregation(project_name: str, matrices: List[PolicyMatrix], variant: Dict) -> Dict:
    """
    Run `_run_aggregation` for one variant.

    Returns:
        Dict: `result` (AggregationResult or None), `status`, `messages` and the tie `picks`
    """
    project = app.Project(name=project_name, matrices=matrices)
    obj = app.PolicyCoherenceApp.__new__(app.PolicyCoherenceApp)
    obj.root = _Root()
    captured: Dict = {"result": None, "status": None, "picks": []}
    obj._current_project = lambda: project
    obj._create_analysis_tabs = lambda _proj, result: captured.__setitem__("result", result)
    obj._set_status = lambda text: captured.__setitem__("status", text)
    patches = {
        "AggregationMethodDialog": _fake_dialog(variant["method"]),
        "WeightDialog": _fake_dialog(variant.get("weights")),
        "MedianChoiceDialog": _fake_dialog(variant.get("median_choice") or "lower"),
        "TieResolutionDialog": _fake_tie_dialog(variant.get("tie_pick"), captured["picks"]),
    }
    originals = {name: getattr(app, name) for name in patches}
    try:
        for name, fake in patches.items():
            setattr(app, name, fake)
        with recorded_messages() as recorder:
            obj._run_aggregation()
    finally:
        for name, original in originals.items():
            setattr(app, name, original)
    captured["messages"] = recorder.messages
    return captured
