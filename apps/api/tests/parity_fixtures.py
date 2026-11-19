"""
Loader and comparison helpers for the fixtures generated from `tk-app/` by `scripts/generate_parity_fixtures.py`.

Never edit the fixtures by hand: regenerate them from the legacy app. Floats are compared with `rtol=0, atol=1e-12`
(Settled Decision 5) and zeros by sign as well (`-0.0` is kept, Known Tkinter Behaviour Kept 12).
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from constants.band_constants import COUNT_BANDS, VALUE_BANDS
from models.analysis_request_models import AnalysisRequest

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
ATOL = 1e-12
LAYOUT_ATOL = 1e-6
DEGENERATE_GAP = 1e-9
BOUNDARY_GAP = 1e-9


class ParityFixtures:
    """Reads parity, error, layout, import and XLSX fixtures."""

    def parity(self) -> List[Tuple[str, Dict]]:
        """Return (name, fixture) for every analysis fixture (`<case>__<variant>`), sorted by name."""
        paths = sorted((FIXTURES_DIR / "parity").glob("*.json"))
        return [(path.stem, self._load(path)) for path in paths if not path.stem.startswith("errors__")]

    def errors(self) -> List[Tuple[str, Dict]]:
        """Return (name, fixture) for every error fixture."""
        paths = sorted((FIXTURES_DIR / "parity").glob("errors__*.json"))
        return [(path.stem.removeprefix("errors__"), self._load(path)) for path in paths]

    def parity_case(self, name: str) -> Dict:
        """Return one analysis fixture by name."""
        return self._load(FIXTURES_DIR / "parity" / f"{name}.json")

    def request(self, name: str) -> AnalysisRequest:
        """Return the validated request of one analysis fixture."""
        return AnalysisRequest.model_validate(self.parity_case(name)["request"])

    def layouts(self) -> List[Tuple[str, Dict]]:
        """Return (name, fixture) for every layout fixture."""
        return [(path.stem, self._load(path)) for path in sorted((FIXTURES_DIR / "layouts").glob("*.json"))]

    def imports(self) -> List[Tuple[str, Dict, bytes]]:
        """Return (name, fixture, workbook bytes) for every import fixture."""
        folder = FIXTURES_DIR / "imports"
        return [
            (path.stem, fixture, (folder / fixture["file"]).read_bytes())
            for path in sorted(folder.glob("*.json"))
            for fixture in [self._load(path)]
        ]

    def xlsx(self, name: str) -> Dict:
        """Return the dump of a legacy-exported workbook (or its recorded error)."""
        return self._load(FIXTURES_DIR / "xlsx" / f"{name}.json")

    def is_degenerate(self, singular_values: Optional[List[float]]) -> bool:
        """PCA is degenerate when `(S0 - S1) / S0 < 1e-9` or `(S1 - S2) / S0 < 1e-9` (plan Phase 9.1)."""
        if not singular_values or singular_values[0] == 0:
            return True
        s = list(singular_values) + [0.0, 0.0]
        return (s[0] - s[1]) / s[0] < DEGENERATE_GAP or (s[1] - s[2]) / s[0] < DEGENERATE_GAP

    def _load(self, path: Path) -> Dict:
        return json.loads(path.read_text(encoding="utf-8"))


class ParityAssertions:
    """Float and band comparisons shared by the parity tests."""

    def floats(self, actual: Any, expected: Any, atol: float = ATOL, where: str = "") -> None:
        """Assert nested numbers match within `atol` and zeros match by sign; `None` must match `None`."""
        if isinstance(expected, list):
            assert isinstance(actual, list) and len(actual) == len(expected), f"{where}: shape"
            for k, (a, e) in enumerate(zip(actual, expected, strict=True)):
                self.floats(a, e, atol, f"{where}[{k}]")
            return
        if expected is None:
            assert actual is None, f"{where}: expected None, got {actual!r}"
            return
        np.testing.assert_allclose(actual, expected, rtol=0, atol=atol, err_msg=where)
        if expected == 0:
            assert math.copysign(1.0, actual) == math.copysign(1.0, expected), f"{where}: sign of zero"

    def value_band(self, colours: List[str]) -> str:
        """Band key of a legacy `_value_color` (fill, text) pair."""
        return next(band["key"] for band in VALUE_BANDS if [band["fill"], band["text"]] == list(colours))

    def count_band(self, colours: List[str], n: int) -> str:
        """Band key of a legacy `_count_color` pair (`none` only when n <= 1)."""
        bands = COUNT_BANDS if n <= 1 else COUNT_BANDS[:4]
        return next(band["key"] for band in bands if [band["fill"], band["text"]] == list(colours))

    def explained(self, actual: List[float], actual_unrounded: Optional[List[float]], legacy: Dict) -> None:
        """
        PCA `explained` must equal the fixture, except at a rounding boundary (decision record
        `2026-11-18-pca-explained-rounding-boundary`): when the fixture's unrounded percentage is within 1e-9 of
        an `x.x5` boundary, the unrounded values must agree at 1e-12 and either rounded neighbour is accepted.
        """
        unrounded = legacy.get("explained_unrounded")
        for k, rounded in enumerate(legacy["explained"]):
            value = unrounded[k] if unrounded else None
            boundary = (math.floor(value * 10) + 0.5) / 10 if value is not None else None
            if boundary is None or abs(value - boundary) >= BOUNDARY_GAP:
                assert actual[k] == rounded, f"explained[{k}]: {actual[k]} != {rounded}"
                continue
            self.floats(actual_unrounded[k], value, where=f"explained_unrounded[{k}]")
            neighbours = {round(math.floor(value * 10) / 10, 1), round(math.ceil(value * 10) / 10, 1)}
            assert actual[k] in neighbours, f"explained[{k}]: {actual[k]} not in {neighbours}"

    def aligned_pca(self, actual: List[List[float]], expected: List[List[float]]) -> List[List[float]]:
        """Flip each fixture component whose dot product with the API's is negative (PCA sign rule)."""
        a = np.asarray(actual, dtype=float)
        e = np.asarray(expected, dtype=float)
        signs = [(-1.0 if float(a[:, k] @ e[:, k]) < 0 else 1.0) for k in range(e.shape[1])]
        return (e * np.asarray(signs)).tolist()


parity_fixtures = ParityFixtures()
parity_assertions = ParityAssertions()
