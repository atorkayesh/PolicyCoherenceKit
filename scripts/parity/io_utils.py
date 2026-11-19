"""Paths, JSON conversion and environment details shared by the parity fixture generator."""

import json
import platform
import sys
from pathlib import Path
from typing import Any, Dict

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = REPO_ROOT / "apps" / "api" / "tests" / "fixtures"
PARITY_DIR = FIXTURES_DIR / "parity"
LAYOUTS_DIR = FIXTURES_DIR / "layouts"
IMPORTS_DIR = FIXTURES_DIR / "imports"
XLSX_DIR = FIXTURES_DIR / "xlsx"
EXAMPLE_WORKBOOK = REPO_ROOT / "data" / "examples" / "WEF Nexus Example.xlsx"


def to_jsonable(value: Any) -> Any:
    """Convert tuples, dict keys, numpy scalars and dataclass-like values into JSON-ready values."""
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def write_json(path: Path, data: Any) -> None:
    """Write JSON with a trailing newline; `-0.0` is kept as `-0.0`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_jsonable(data), indent=1, ensure_ascii=False, allow_nan=False) + "\n", "utf-8")


def environment() -> Dict[str, Any]:
    """Return the Python, numpy, platform and BLAS details recorded in every fixture."""
    config = np.show_config(mode="dicts")
    blas = config.get("Build Dependencies", {}).get("blas", {})
    return {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "platform": platform.platform(),
        "blas": blas.get("name", "unknown"),
    }


def scores_grid(scores: Dict, n: int) -> list:
    """Convert an `(i, j) -> value` dict into an `n x n` list (missing cells become None)."""
    return [[scores.get((i, j)) for j in range(n)] for i in range(n)]
