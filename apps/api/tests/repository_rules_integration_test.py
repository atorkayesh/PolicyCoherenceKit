"""
Repository rules for `apps/api`.

Tests cover:
- Every code file, and every `scripts/**/*.py` file at the repository root (when present: the api container
  mounts only `apps/api`), is at most 300 lines; `__init__.py` files hold only a docstring
- Nothing imports the legacy Tk modules or `tkinter`, no string literal (outside docstrings) points into the
  legacy folder, and no file manipulates `sys.path` (the legacy `models` and `constants` share names with API
  packages, so legacy-only module names are checked)
- No module imports `matplotlib` (charts are drawn in the browser)
"""

import ast
import unittest
from pathlib import Path

import pytest

API_ROOT = Path(__file__).resolve().parents[1]
# In the api container apps/api is mounted at /app, which has no grandparent repository root.
SCRIPTS_ROOT = API_ROOT.parents[1] / "scripts" if len(API_ROOT.parents) > 1 else API_ROOT / "__no_scripts__"
SKIP_PARTS = {".venv", "__pycache__", ".pytest_cache", ".ruff_cache", "fixtures"}
LEGACY_MODULES = {
    "aggregator",
    "importer",
    "app",
    "theme",
    "font_loader",
    "dialogs",
    "aggregation_dialog",
    "aggregation_tab",
    "coherence_scores_tab",
    "range_of_influence_tab",
    "pca_tab",
    "network_tab",
    "results_insights_tab",
    "llm_tab",
    "matrix_widget",
    "tkinter",
    "matplotlib",
}
LEGACY_FOLDER = "tk" + "-app"


def code_files():
    """Yield every Python file of the API (not the virtualenv or fixtures)."""
    for path in API_ROOT.rglob("*.py"):
        if not SKIP_PARTS.intersection(path.relative_to(API_ROOT).parts):
            yield path


@pytest.mark.integration
class TestRepositoryRules(unittest.TestCase):
    """Static checks of the code base."""

    def test_files_at_most_300_lines(self):
        """Test the 300-line limit."""
        long_files = [str(p) for p in code_files() if len(p.read_text(encoding="utf-8").splitlines()) > 300]
        self.assertEqual(long_files, [])

    @unittest.skipUnless(SCRIPTS_ROOT.is_dir(), "scripts/ is not available (the api container mounts only apps/api)")
    def test_scripts_at_most_300_lines(self):
        """Test the 300-line limit for the fixture generator scripts."""
        long_files = [
            str(p)
            for p in SCRIPTS_ROOT.rglob("*.py")
            if "__pycache__" not in p.parts and len(p.read_text(encoding="utf-8").splitlines()) > 300
        ]
        self.assertEqual(long_files, [])

    def test_no_legacy_references(self):
        """Test imports, string literals and `sys.path` use."""
        offenders = []
        for path in code_files():
            if path.name == Path(__file__).name:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            docstrings = {id(node.value) for node in ast.walk(tree) if isinstance(node, ast.Expr)}
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                else:
                    names = []
                if any(name.split(".")[0] in LEGACY_MODULES for name in names):
                    offenders.append(f"{path}: import {names}")
                if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
                    if LEGACY_FOLDER in node.value:
                        offenders.append(f"{path}: {node.value[:40]}")
                if isinstance(node, ast.Attribute) and node.attr == "path" and getattr(node.value, "id", "") == "sys":
                    offenders.append(f"{path}: sys.path")
        self.assertEqual(offenders, [])

    def test_init_files_hold_only_a_docstring(self):
        """Test `__init__.py` files contain a docstring and nothing else."""
        for path in code_files():
            if path.name == "__init__.py":
                body = ast.parse(path.read_text(encoding="utf-8")).body
                self.assertEqual(len(body), 1, str(path))
                self.assertIsInstance(body[0].value, ast.Constant, str(path))
