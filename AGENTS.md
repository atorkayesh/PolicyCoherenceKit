# Repository guidance

## Run and verify
- This is a flat Python/Tkinter desktop app, not an installable package. Run from the repository root: `python3 main.py`; imports use root-level module names.
- Install dependencies with `python3 -m pip install openpyxl numpy reportlab Pillow`. **Pillow is required at startup** (`app.py` imports `PIL` unconditionally), despite the README marking it optional. Python must also provide Tkinter/Tcl/Tk.
- No dependency manifest/lockfile, automated tests, CI, or lint/format/typecheck configuration exists. Do not invent project check commands.
- Syntax check: `python3 -m compileall -q .`. Dependency/import smoke check without creating a window: `python3 -c "import app, aggregator, importer"`. Neither replaces functional testing.
- Manual smoke flow: import `Example data/WEF Nexus Example.xlsx`, aggregate, open each analysis tab, and export Excel. The UI forces Average for fewer than three decision-makers; use at least three to exercise method selection and four for even-count Median choices.
- Launching `main.py` requires a graphical session and installs missing bundled Inter fonts into `~/Library/Fonts` on macOS or `~/.local/share/fonts` on Linux (where it invokes `fc-cache`). Avoid launching it just to check imports.
- Preserve startup order: Windows DPI awareness before importing Tkinter, and `load_inter()` before creating `tk.Tk()`. The alternate `__init__.py:run()` launcher omits these steps.

## Wiring and state
- `app.py` owns project orchestration and Excel export (`_export_to_excel`); `models.py`, `aggregator.py`, and `importer.py` contain Tkinter-free data/aggregation/import logic.
- Each `app.py:Project` owns its matrices and aggregation history. `_create_analysis_tabs` replaces visible analysis tabs but appends to `agg_results`; Excel export includes the full history, not just the displayed run.
- Analysis widgets are created lazily via `_ensure_analysis_tab_loaded`. Register new analysis views in `_create_analysis_tabs` rather than eagerly building all widgets.
- Computations live alongside their views in `*_tab.py`: `compute_scores`, `compute_entropy`, `compute_pca`, `compute_centrality`, and `compute_insights`. Excel export and LLM prompts reuse scores, entropy, and centrality computations; changes affect more than the UI.
- `AggregationResult` caches scores/entropy/centrality/graph analysis in `_cached_*` fields. If mutating result scores after analysis, invalidate all affected caches or create a new result.
- UI tokens are split between `theme.py` (component styling) and `constants.py` (ratings, score mapping, shared palette/fonts/dimensions); check both before adding styling constants.

## Data contracts and gotchas
- Matrices are **directed**: row = influencing policy, column = influenced policy. Input data maps `(row, col)` to rating labels; aggregated scores map the same coordinates to numbers. Diagonal is always `Neutral` / `0.0`.
- Before calling aggregation functions directly, call `check_completeness`; their internal matrix validator checks policy-list compatibility, not blank cells. All decision-makers must use identical policy names **and order**.
- Majority ties have `None` scores until every `TiedCell.chosen` is set and `resolve_ties(result)` runs. Resolve ties before analysis; downstream computations often treat `None` as zero.
- Median is ordinal, not the arithmetic mean of two middle scores: `ordinal_cells` preserves both middle labels for even counts, while `scores` uses the selected lower/upper label. Use `aggregation_method_label` for display names.
- Excel import expects full policy names in row 1/column 1 headers and rating labels (case-insensitive), not numeric scores. Blank off-diagonal cells produce warnings and incomplete matrices. Exported workbooks use a different layout and are **not round-trip import files**.
- Network analysis includes both positive and negative nonzero edges, with shortest-path distance `1 / abs(score)`; entropy likewise uses absolute outgoing weights. Do not silently drop negative interactions.
- LLM calls use a daemon worker with Tk updates dispatched through `after(0, ...)`. Preserve clearing the API-key input on both success and failure; keys are not persisted to disk.
