# The Legacy Tk App's Logic Is Mostly Pure And Portable, But About A Third Of The Rules Live In GUI Files And Several Outputs Are Unstable Or Inconsistent

**Date:** 18 November, 2026
**Author:** Claude Code (research agent) for Youpele Michael
**Scope:** Every computation, validation rule, message and I/O path in `tk-app/` (the legacy Tkinter "Policy Coherence Kit"), on branch `restructure/apps-api-web` at HEAD `00b610a` plus the uncommitted move of the app into `tk-app/` (files unchanged by the move). Locked environment: `tk-app/uv.lock` resolved on Python 3.13.2 (uv-managed) on macOS arm64 → numpy 2.5.4 (Accelerate BLAS/LAPACK), openpyxl 3.1.5, reportlab 5.1.0, Pillow 13.0.0, Tk 8.6. Example data: `data/examples/WEF Nexus Example.xlsx`.

## Summary

- **The numerical core is small and headless-callable.** `aggregator.py`, `importer.py` and `models.py` are Tk-free. The five analysis functions (`compute_scores`, `compute_entropy`, `compute_pca`, `compute_centrality`, `compute_insights`) are pure but live in `*_tab.py` modules that `import tkinter` at module level. Importing works without a display (verified). The same holds for `app._export_to_excel` (app.py imports Pillow at module level) and `llm_tab.build_prompt`. All were run headlessly against the locked env in `/tmp` with no repo writes.
- **Hidden GUI rules that the API must reproduce:**
  - fewer than 3 decision-makers forces Average (`app.py:2558-2560`);
  - the median Lower/Upper dialog appears only for an even DM count (`app.py:2579`);
  - weights are validated twice, in the dialog and in `aggregator` (both allow ±0.01 on the sum, and the weights are **not renormalised**);
  - every majority tie must be resolved before analysis;
  - project-setup validation (unique DM names, unique policies, at least 2 policies) lives in `dialogs.py:1080-1124`. Import does **not** apply these checks.
- **Parity traps:**
  - PCA has no sign convention, and macOS wheels use Accelerate while Linux wheels use OpenBLAS.
  - Python `round()` is half-to-even on exact binary halves (for example, Average with 8 DMs gives `0.125 → 0.12`).
  - Entropy returns `-0.0` for a policy with exactly one non-zero outgoing link.
  - Weighted can produce `-0.0`.
  - Brandes path counting uses a `1e-9` equality tolerance.
  - Closeness uses outgoing distances and can exceed 1.
  - Ties in `max()`/`sorted()` resolve by policy index.
  - Unresolved ties (`None`) are read as `0.0` everywhere downstream.
- **Inconsistencies a port must decide on:**
  - Median's ordinal pair (`ordinal_cells`) is computed but never shown or exported.
  - Results Insights shows "Median" while every other tab shows "Median (Lower/Upper)".
  - Excel export labels Average as "Avg" and truncates sheet names so that the run index is lost or deduplicated (`…(Median (Lower)1`).
  - DM names containing `/` (and other characters Excel forbids) crash the export.
  - Import silently misaligns data when a header column is blank.
  - Import shows skipped-sheet warnings under the heading "blank cells".
  - The story banner calls every negative link "constraining" (even `-3 Cancelling`).
  - `_build_narrative`, quadrants, the broker and ~11 card builders are dead code.
- **The bundled example has one sheet ("Research Team"), 14 policies whose full names are literally `P1`…`P14`, and no blanks.** It can only exercise Average, because the UI forces Average below 3 DMs. Every multi-DM parity case must use synthetic workbooks.
- **There is no persistence.** Nothing is saved except user-initiated Excel/PNG/TXT/PDF exports and the Inter font copy at start-up. API keys are never stored.

## Questions

1. What data model, constants and result fields exist, including caches?
2. What workbook layout does import accept, and what are its exact errors and warnings?
3. Which aggregation methods exist, and with which rules, messages and GUI-enforced constraints?
4. What are the exact formulas, rounding, ordering and edge cases of every analysis? Which are pure, and which are nondeterministic or version-sensitive?
5. How are plots drawn and exported?
6. What is the exact Excel export layout, and how are LLM TXT/PDF exports built?
7. How do LLM calls work (providers, models, prompt, errors, key handling)?
8. Is anything persisted?
9. Which dependency versions are locked, and do they resolve on Python 3.13?
10. Which parity traps, bugs and inconsistencies exist?
11. Which parity fixtures should a generator produce, and what headless obstacles does it face?

## Method

- Read in full: `aggregator.py`, `importer.py`, `models.py`, `constants.py`, `coherence_scores_tab.py`, `range_of_influence_tab.py` (logic parts), `pca_tab.py`, `network_tab.py` (logic, layouts, ego, report), `results_insights_tab.py` (logic and the cards that are actually built), `llm_tab.py` (prompt, HTTP, generate, downloads), `aggregation_dialog.py`, `main.py`, `font_loader.py`, `__init__.py`, `pyproject.toml`, `uv.lock` (relevant parts). Read the relevant parts of `app.py` (Project, aggregation flow, import, export, topbar), `dialogs.py` (validation), `aggregation_tab.py` (colour buckets) and `matrix_widget.py` (editing). Grepped for persistence, randomness and dead code.
- Ran the legacy code headlessly with its own lock, without touching the repo:
  `UV_PROJECT_ENVIRONMENT=/tmp/pck-inv/venv PYTHONDONTWRITEBYTECODE=1 uv run --frozen --no-dev --python 3.13 --project tk-app python /tmp/pck-inv/scripts/probe*.py …`
  The probes imported the example workbook, ran every method on it and on seeded random 3–8 policy × 1–4 DM matrices, and exercised these edge cases:
  - entropy with one link;
  - n = 2;
  - an all-Neutral matrix;
  - majority ties;
  - even median;
  - weight validation;
  - export with several runs and colliding or invalid sheet names;
  - import of blank, case-variant, numeric, mismatched and gap-column sheets.
  Output values quoted below come from those runs unless marked "read only".
- Line numbers refer to files under `tk-app/`.

## Findings

### 1. Data model

**Rating vocabulary and score mapping** (`constants.py:14-22, 92-100`). The order is significant: it drives the UI drop-down, the legend and the error text.

| Label | Score | Cell bg (`RATING_COLORS`, :30-38) | Text (`RATING_TEXT_COLORS`, :41-49) |
| --- | --- | --- | --- |
| Indivisible | 3 | `#0B6E6E` | `#ffffff` |
| Reinforcing | 2 | `#2A9D8F` | `#ffffff` |
| Enabling | 1 | `#6BAF92` | `#2d2d2d` |
| Neutral | 0 | `#B0B7C3` | `#555555` |
| Constraining | -1 | `#E9C46A` | `#2d2d2d` |
| Counteracting | -2 | `#E76F51` | `#ffffff` |
| Cancelling | -3 | `#9B2226` | `#ffffff` |

`DIAGONAL_VALUE = "Neutral"` (:24). Scores are Python `int`. Aggregators convert them to `float` (Average sums ints first, then divides).

**`PolicyMatrix`** (`models.py:12-90`, dataclass). Fields:

- `decision_maker: str`
- `policies: List[str]` (full names)
- `codes: List[str]`
- `data: Dict[(row, col), str]`

Behaviour:

- `__post_init__` forces every diagonal cell to `"Neutral"`.
- `set_rating` ignores the diagonal.
- `get_rating` returns `""` when a cell is unset.
- `filled_count`, `total_cells` (= n² − n) and `is_complete` are used only for status text. `is_complete` and `to_dict_records` are unused.
- `generate_codes` → `P1…Pn` (:97-99).
- `make_empty_matrix(dm, policies)` (:102-109).

Codes are always positional; the user never chooses them.

**`TiedCell`** (`aggregator.py:37-45`). Fields: `row`, `col`, `code_r`, `code_c`, `tied_labels` (sorted by score descending) and `chosen: Optional[str]`.

**`AggregationResult`** (`aggregator.py:48-90`):

| Field | Type / meaning |
| --- | --- |
| `scores` | `(i,j) → float`. Diagonal `0.0`. Majority ties are `None` until `resolve_ties`. Average/Weighted are rounded to 2 dp. Median/Majority are exact integers as floats. |
| `ties` | `List[TiedCell]`, non-empty only for majority |
| `n`, `codes`, `policies` | Copied from `matrices[0]`. These are the *same list objects*, not copies. |
| `method` | `"average" \| "median" \| "majority" \| "weighted"`. The docstring at :60 omits median. |
| `decision_makers` | Count of DMs |
| `decision_maker_names` | DM names in order |
| `source_scores` | `(i,j) → [float per DM]`, diagonal `[0.0]*k`. Used only by Results Insights agreement. |
| `ordinal_cells` | Median only: `(i,j) → (label,)` for odd counts, `(lower, upper)` for even counts, diagonal `("Neutral",)`. **Never read anywhere else** (grep). |
| `median_even_choice` | `"lower"`/`"upper"` only when method is median **and** the DM count is even, otherwise `None` (:269) |
| `_cached_scores`, `_cached_entropy`, `_cached_centrality`, `_cached_graph` | Filled on first call of `compute_scores`, `compute_entropy`, `compute_centrality` and `_build_graph`. Never invalidated. PCA and insights are not cached. |

**`Project`** (`app.py:179-190`, dataclass). Fields: `name`, `matrices`, `agg_results` (append-only history), `agg_tab_ids`, `analysis_tab_meta`, plus Tk handles. It lives in memory only.

**`ImportResult`** (`importer.py:23-32`): `matrices` and `warnings`.

### 2. Import (`importer.py:39-192`, wrappers in `app.py:2919-3036`)

Layout, one sheet per DM in workbook order:

- The sheet name becomes `decision_maker`.
- Row 1, columns 2+ are policy names: `str(v).strip()`, **skipping `None`/blank cells** (:81-84).
- Column 1, rows 2…n+1 are the row headers. They must equal the column headers exactly (case-sensitive, after strip).
- Cells in rows 2…n+1 and columns 2…n+1 hold the ratings.
- The workbook is opened with `read_only=True, data_only=True`, so formulas yield cached values.

Cell rules:

- Diagonal cells are **ignored whatever they contain** (verified: a junk value on the diagonal is accepted).
- Blank, `None` or the literal string `"none"` (any case, after strip) counts as a blank.
- Ratings are matched case-insensitively after strip (`_match_rating`, :185-192); `" ENABLING "` → `Enabling` was verified.
- Numbers are not accepted: `3` → `"3"` → error.
- Rows and columns beyond n are ignored.

Messages (verbatim; `{…}` are substitutions):

| Situation | Kind | Text |
| --- | --- | --- |
| openpyxl missing | `ImportError` | `openpyxl is required for Excel import.\nInstall it with:  pip install openpyxl` |
| Sheet has no rows | warning, sheet skipped | `Sheet "{sheet}": empty, skipped.` |
| Fewer than 2 non-blank column headers | warning, skipped | `Sheet "{sheet}": fewer than 2 policies in header row, skipped.` |
| Row headers ≠ column headers | `ValueError` (aborts the **whole** import) | `Sheet "{sheet}": row and column headers do not match.\n` followed by up to 5 lines `  row {i+1}: "{row}" vs col "{col}"`, joined by `\n` |
| Unrecognised ratings | `ValueError` (aborts the whole import) | `Sheet "{sheet}": unrecognised rating values:\n` followed by up to 10 lines `  {Pi}->{Pj}: "{val}"`, then `\n  ...` if there are more than 10, then `\n\nAllowed values: Indivisible, Reinforcing, Enabling, Neutral, Constraining, Counteracting, Cancelling` |
| Blanks | warning, matrix kept (incomplete) | `"{sheet}": {count} blank cell(s): {P1->P2, …first 10}` plus ` (+{count-10} more)` |

Verified example: `'Sheet "S1": unrecognised rating values:\n  P1->P2: "good"\n  P2->P1: "3"\n\nAllowed values: …'`.

App-level behaviour (`app.py`):

- Dialog title `Import matrices from Excel workbook`, filter `*.xlsx *.xls`. openpyxl cannot read `.xls`.
- `ValueError`/`ImportError` → `Import Error` box.
- No matrices → `Nothing Imported`: `No valid matrices were found in the workbook.`
- When importing into an existing project, every sheet's `policies` must equal the project's (name **and order**). Otherwise the `Policy List Mismatch` box shows: `The following sheets have a different policy list and cannot be imported:\n\n  - {dm}…\n\nAll matrices must share the same policy list.` In that case nothing is imported.
- Success shows `{added} matrix/matrices imported successfully.` With warnings it shows `{added} matrix/matrices imported.\n\nThe following sheets have blank cells:\n\n{warnings joined by \n}`. That heading also covers "empty, skipped" warnings, which is misleading.
- "New project from import" names the project after the file stem, de-duplicated as `"{stem} 2"`, `"{stem} 3"`… (:2941-2948).

Import does **not** check:

- duplicate policy names (the setup dialog does);
- duplicate DM names (sheet names are unique anyway, but importing into a project can duplicate existing DM names);
- an empty policy list beyond the `< 2` rule.

### 3. Aggregation

Entry point `app._run_aggregation` (`app.py:2533-2611`). The order matters:

1. No project → `No Project`: `Create a project first.` No matrices → `No Matrices`: `Add at least 1 decision-maker matrix before running analysis.`
2. `check_completeness` (`aggregator.py:97-119`) returns `[(dm, [(code_r, code_c), …])]` in row-major order. If anything is incomplete, the `Incomplete Matrices` box shows `Please fill all cells before aggregating.\n\n` followed by lines `  {dm}: {first 10 "Pi->Pj" joined ", "}{" (+k more)"}`.
3. **`n_dms < 3` → method forced to `"average"` with no dialog** (:2559-2560). This includes 1 DM. Otherwise `AggregationMethodDialog` offers:
   - "Average": "Each decision-maker is weighted equally. Cell score = mean of all scores."
   - "Median (Ordinal)": "Uses the ordered middle rating(s) and avoids assuming equal spacing."
   - "Majority Rule": "The most common rating wins. Ties are flagged for manual resolution."
   - "Weighted by Importance": "You assign a weight (0–1) to each DM. Weights must sum to exactly 1.0."

   The default selection is Average (`aggregation_dialog.py:48-94`).
4. Weighted → `WeightDialog` (:431-616). Inputs are blank by default, with a live `Sum: {round(total,4)}` (red if `|total−1| > 0.01`). Validation runs in order:
   - `Missing Weight`: `Please enter a weight for "{dm}".`
   - `Invalid Value`: `"{raw}" is not a valid number for "{dm}". Use a decimal like 0.3.`
   - `Out of Range`: `Weight for "{dm}" must be between 0.0 and 1.0.`
   - `Weights Do Not Sum to 1`: `Current sum is {round(total,4)}.\nPlease adjust the weights so they sum to exactly 1.0.`

   The total is `round(sum, 10)` with tolerance `> 0.01`.
5. Median with an **even** `n_dms` → `MedianChoiceDialog`: "Lower Median" / "Upper Median", default `lower` (:247-428). With an odd count, `"lower"` is passed but ignored.
6. The aggregation function is called (below).
7. If `result.ties`, `TieResolutionDialog` lists `"{code_r} -> {code_c}"` with `Tied options: {label} ({score:+d})  |  …` and a read-only combobox (no default). An empty pick gives `Unresolved Tie`: `Please select a rating for cell {code_r} -> {code_c}.` Cancel aborts the whole run. Then `resolve_ties(result)` runs.
8. `_create_analysis_tabs` **appends** the result to `proj.agg_results` (history) and replaces the visible tabs. The status reads `Analysis complete for "{proj}"  |  method: {label}  |  {k} decision-maker(s)`.

Methods (`aggregator.py`):

| Method | Off-diagonal cell formula | Rounding | Notes |
| --- | --- | --- | --- |
| `aggregate_average` (:126-155) | `round(sum(int scores) / k, 2)` | Python `round` (half-even on the binary value) | `source_scores` holds the per-DM floats |
| `aggregate_median(even_choice="lower")` (:213-270) | Labels sorted ascending by score (stable, so equal labels keep DM order). Odd k: `ordered[k//2]`. Even k: `ordinal_cells = (ordered[k/2−1], ordered[k/2])` and the score is the lower or upper element. | none (integer) | Never averages the two middle values. Verified: 4 DMs, cell `('Constraining','Neutral')`, lower `-1.0`, upper `0.0`. |
| `aggregate_majority` (:158-210) | `Counter(labels)`. A unique mode gives `float(score)`. Otherwise the score is `None` and a `TiedCell` is created with the winners sorted by score descending. | none | With an even k, ties are frequent (13 of 20 cells in a random 5×4 case) |
| `aggregate_weighted(weights)` (:289-330) | `round(Σ wᵢ·scoreᵢ, 2)` (generator `sum`, left to right) | half-even | Weights are **not normalised**; `[0.335]*3` (sum 1.005) is accepted. Can yield `-0.0`. |
| `resolve_ties` (:273-286) | Writes `float(RATING_SCORES[chosen])` and mutates in place | — | `ValueError("Tie at {code_r} -> {code_c} has not been resolved.")` |

Validators (verbatim):

- `No matrices provided for aggregation.`
- `Matrix "{dm}" has a different policy list from "{dm0}". All matrices must share the same policies to be aggregated.` (list equality, so order matters)
- `Expected {n} weights, got {len}.`
- `Weight {i} is {w:.4f} — must be between 0.0 and 1.0.`
- `Weights sum to {round(total,4)} — must sum to exactly 1.0.`
- `Invalid median choice "{choice}". Expected "lower" or "upper".`

The validators do **not** detect blank cells. A blank `""` raises `KeyError` in `RATING_SCORES[...]`, which is why `check_completeness` must come first.

`aggregation_method_label` (:373-391):

- `average` → `Average`
- `majority` → `Majority Rule`
- `weighted` → `Weighted`
- `median` → `Median (Lower)` / `Median (Upper)` when `median_even_choice` is set, otherwise `Median`
- unknown → `.title()`
- A plain string `"median"` gives `Median`.

### 4. Analyses

All analyses read `scores.get((i,j), 0.0) or 0.0`, so `None` (an unresolved tie) and missing cells count as 0.

| Function (file:line) | Pure? | Formula / output | Rounding & ordering |
| --- | --- | --- | --- |
| `compute_scores` (`coherence_scores_tab.py:107-142`) | Pure, but the module imports tkinter | Per policy i: `oi` = count of j≠i with score ∉ {None, 0}; `ii` = the same on the column; `woi` = Σ row; `wii` = Σ column. Returns `[{code, policy, oi, ii, woi, wii}]` in index order. | `woi`/`wii` are `round(x, 2)`. The UI shows `{:+.2f}`. |
| `compute_entropy` (`range_of_influence_tab.py:82-141`) | Pure (tk import) | `abs_vals` = \|s\| for j≠i, s≠0. `p = v/Σ`. `H = −Σ p·log2 p` (math.log2). `H = round(H, 4)`. No non-zero values → `H = 0.0`, `"Low"`. `hmax = log2(n−1)` if n>2, `1.0` if n==2, `0.0` otherwise. Category uses `ratio = H_rounded / hmax_unrounded`: `<0.25` Low, `<0.50` Low-to-Medium, `<0.75` Medium-to-High, else High. `hmax==0` → Low. | Row output `{code, policy, entropy, category, hmax: round(hmax,4)}`. **A single non-zero link gives `entropy == -0.0`** (verified `repr` → `-0.0`). |
| `compute_pca` (`pca_tab.py:65-121`) | Pure (tk import; numpy imported lazily) | `n<3` → `([], (0.0,0.0), False)`. X is n×(n−1) (row i = outgoing scores, diagonal dropped, so column j means "target j, skipping self" and differs per row). Standardise by column with **population** std (`ddof=0`), std 0 → 1. Then `np.linalg.svd(X_std, full_matrices=False)`, `explained = round(S²/ΣS²·100, 1)` for PC1 and PC2 (`(0.0,0.0)` if ΣS²=0), `coords = X_std @ Vt[:2].T` as a list of tuples. | **No sign normalisation.** Example: `(42.0, 18.6)`, P1 `(-1.4850536222898432, -1.339817678022225)`. An all-Neutral matrix gives all coords `0.0` with `valid=True` and `(0.0, 0.0)`. Not cached. |
| `_build_graph` (`network_tab.py:127-172`) | Pure | Edges are every s≠0 (positive **and** negative), in row-major order. `dist = 1/abs(s)`. `adj`/`adj_rev` lists. | Cached in `_cached_graph` |
| `compute_centrality` (`network_tab.py:275-320`) | Pure (tk import) | Betweenness: Brandes over Dijkstra (heapq, `(dist,node)` entries) with path counting. An equal-distance path is accepted when `abs(new−d) < 1e-9` (:208). Back-propagation sorts `(d, v)` in reverse (ties go to the higher index first). Normalised by `(n−1)(n−2)` (1 if n≤2) and rounded to 4 dp. Closeness: **outgoing** Dijkstra from i, `finite` = reachable others, `clo = round((len(finite)/(n−1)) / mean(finite), 4)`; nothing reachable → `0.0`. | `{code, policy, betweenness, closeness}` in index order. **Closeness is not bounded by 1** (n=2 with \|s\|=3 gives `3.0`; the example has `1.6957`). Not `networkx` semantics: networkx uses incoming distance for directed closeness. |
| `compute_insights` (`results_insights_tab.py:607-664`) | Pure (tk import) | See the table below | See below |

`compute_insights` details:

- **`_build_graph_stats`** (:312-352): `positive_edges`, `negative_edges`, `zero_edges` (off-diagonal); `density = round((pos+neg)/(n(n−1)), 3)`; `polarity = round(pos/(pos+neg), 3)`, or `0.5` if there are no edges. `strongest_pos`/`strongest_neg` use a strict `>`/`<`, so the first in row-major order wins ties, with defaults `0.0`. The `*_pair` fields are `(i,j)` or `None`.
- **`_agreement_stats`** (:417-455). `dm_count = max(1, decision_makers or len(names) or 1)`. Per off-diagonal cell:
  - `agreement_ratio = round(max(Counter(values))/dm_count, 3)`;
  - `spread = round(max−min, 2)`;
  - `score`;
  - `pair = "{policy} ({code}) -> {policy} ({code})"`.

  The lists are built as follows:
  - `contested` = the first 5 sorted by `(agreement_ratio, −spread, −|score|)`. The sort is stable, so ties stay in row-major order.
  - `strong_consensus` = rows with `|score| > 0`, sorted by `(−ratio, −|score|)`, first 5.
- **`_average_dm_spearman_agreement`** (:384-414): per DM, the vector of off-diagonal source scores in row-major order. Average-rank ties (`_rank_values`), then Pearson for each DM pair. A **zero-variance vector gives a correlation of 1.0** (:379-380), and the result is clamped to [−1, 1]. It returns `(round(avg,3), round((avg+1)/2, 3))`. For ≤1 DM or no data it returns `(1.0, 1.0)`.
- Enriched rows (:617-641) contain the `compute_scores` fields plus:
  - `index`;
  - `net = round(woi−wii, 2)`;
  - `prominence = round(Σ|row| + Σ|col|, 2)`;
  - `entropy`, `entropy_category`, `betweenness`, `closeness`;
  - `quadrant`, with `threshold = sorted(prominences)[n//2]` (the *upper* median). Labels: System Driver / System Dependent / Strategic Lever / Vulnerable Node / Balanced, with net cut-offs ±0.05.
- `drivers`: `net>0.05`. `dependents`: `net<−0.05`. `balanced`: the rest.
- `top_driver = max(key=(woi, prominence, net))`. `top_dependent = max(key=(wii, prominence, −net))`. `top_prominent`, `top_broker`. Ties go to the **first** (lowest index) row, since `max` returns the first maximum.
- `top_*_rows` are reverse-stable sorts (ties keep index order), first 5.
- `narrative` = `_build_narrative(...)[:4]`, so the agreement sentence (5th) is always cut whenever the first three exist.

These GUI-side text and score builders are also pure:

- `_build_story_banner` (:529-559): three templates, `stable` if `average_agreement ≥ 0.75`.
- `_strongest_link` (:512-526): strict `abs >`, so ties go to the lower j. The tone is `"Reinforcing"` if >0, otherwise `"Constraining"`.
- `_build_system_health` (:562-590) computes, with `max_strength = 3·n(n−1)`:
  - `synergy = round(Σpos/max_strength·100)`;
  - `conflict = round(Σ|neg|/…·100)`;
  - `neutral_uncertain = round(zeros/n(n−1)·100)`;
  - `score = clamp(0,100, 50 + synergy − conflict − round(neutral·0.35))`.

  `round` here is a half-even int. Example: `{'score': 73, 'synergy': 37, 'conflict': 3, 'neutral_uncertain': 32}`.
- `_build_supporting_interpretation` (:593-604): five fixed sentences keyed on contested present/absent and agreement ≥0.75 / ≥0.5.
- Conflict-ratio card (:1058-1084): `neg/(pos+neg)` with captions at ≤0.2 / ≤0.4 / else.
- Most-contested caption: `⚠ High disagreement` if ratio < 0.5.

**Shown vs computed in Results Insights.** The tab builds only three rows of cards (`_build_key_insight`, `_build_primary_signal_row`, `_build_secondary_signal_row`, :722-737):

- the story banner with tags (Top Driving Policy / Strongest Link, which uses `strongest_pos_pair` only / Contested);
- the Analysis Overview stats;
- System Health;
- Top Driving Policy;
- Top Influenced Policy;
- Strongest Link;
- Most Contested;
- Conflict Ratio.

These are **never instantiated (dead):**

- `_scatter_card`
- `_agreement_heatmap_card`
- `_relations_card`
- `_configuration_card`
- `_ranking_card`
- `_metric_signal_card`
- `_mini_stat_card`
- `_analysis_config_card`
- `_compact_group_block`
- `_prominence_strip_block`
- `_metric_card`

As a result, `narrative`, `quadrant`, `top_broker`, the `drivers`/`dependents`/`balanced` lists, `strong_consensus` and `top_*_rows` are computed but never displayed.

**Other GUI-side derived values:**

- Aggregated tab colour band: `_score_bucket` (`aggregation_tab.py:82-86`) clamps to ±3 and picks the nearest integer, with ties going toward **+∞** (dict key order 3…−3). The cell text is `{score or 0:.2f}`.
- Coherence Scores colours: `_value_color` thresholds `>1.5, >0.5, >0, ==0, ≥−0.5, ≥−1.5, else` and `_count_color` ratio `oi/(n−1)` thresholds `0.75/0.5/0.25` (`coherence_scores_tab.py:73-100`).
- Network info bar: `density = round(edges/(n(n−1)), 3)` and an isolated count (`network_tab.py:381-393`).
- Network report: rows sorted by betweenness, descending and stable (:1263).
- Ego network: the edges touching the ego only, neighbours sorted by index (:1053-1063). Edge labels use `{score:+.2f}`.
- Network edge width `_thickness`: \|s\| ≥ 2.5 → 4.0, ≥ 1.5 → 2.5, else 1.0. Edge colour: >0 `#1a6e3c`, else `#b71c1c`.

**Network layouts** (`network_tab.py:690-886`; GUI methods that take canvas size; all deterministic, no randomness anywhere — grep):

- Circular: start at −π/2, radius `max(40, min(w,h)/2 − 80)`.
- Force-Directed (default):
  - 90 iterations;
  - `k = √(4/count)`;
  - repulsion `k²/d`;
  - attraction `d²/k·(0.55 + min(strength,6)/6)` on undirected summed \|s\|;
  - temperature `0.12·(1−step/90)+0.01`;
  - clamp ±1.2;
  - then normalisation.
- Spectral: `np.linalg.eigh` of the unnormalised Laplacian, the first two eigenvalues > 1e-9, a y bias of `degree·0.02`, with eigenvector sign ambiguity.
- Shell: betweenness rank with code as the secondary key in reverse; shells of 20%, 30% and the rest at radii 0.28/0.58/0.88.

Layouts are presentation only and need not be in numeric parity, but the web app may want to port them.

### 5. Plots and image export

Every chart is drawn on a **Tk Canvas** (no matplotlib). The charts are:

- PCA scatter: radius 16; colour `#2c4a6e`, or the entropy category colour (`Low #a3a3a3`, `Low-to-Medium #a7f3d0`, `Medium-to-High #34d399`, `High #059669`); margin 60; dashed axes `#cccccc`; labels `PC1 ({pct}%)`, `PC2 ({pct}%)`; hover text `"{code}:  {name}"`.
- Network graph: node radius 18, node `#2c4a6e`, isolated `#aaaaaa`, ego `COLOR_ACCENT2 #5a7fa8` at r+4.
- Aggregated matrix.
- Health bars.

Image export (`pca_tab.py:331-368`, `network_tab.py:981-1013`) is a **screen grab** with `PIL.ImageGrab.grab(bbox=canvas on-screen rect)`. That means:

- the image size equals the on-screen canvas size, with no DPI setting;
- the default names are `pca_plot.png` / `network_plot.png`, with the titles `Save PCA plot` / `Save Network plot`;
- it fails on Linux without X screenshot support.

Without Pillow, the fallback is a Tk `postscript()` to `pca_plot.ps` / `network_plot.ps`. Confirmation messages: `PCA plot saved to:\n{path}` and `Network plot saved to:\n{path}`.

### 6. Exports

**Excel** (`app._export_to_excel`, `app.py:3085-3217`; pure, needs openpyxl). The default name is `f"{proj.name}_coherence.xlsx".replace(" ", "_")` and the title `Export project: {name}`. The project must have matrices (`Nothing to Export`: `Add at least one matrix before exporting.`). Success → `Export Complete`, `Saved to:\n{path}`; failure → `Export Failed`, `str(exc)`. The default first sheet is removed. Sheets appear in this order:

1. **One sheet per DM**, title `decision_maker[:31]`:
   - A1 = `Policy Index` (bold);
   - B1… = `"{code}: {name}"`;
   - row 2 empty;
   - A3 = `Influencing / Influenced` (bold italic);
   - B3… are code headers (white bold on `2C4A6E`, centred, thin `CCCCCC` border);
   - A4… are code row headers in the same style;
   - the cells are rating labels (blank `""` if unrated), centred, bordered, filled with `RATING_COLORS` and font `RATING_TEXT_COLORS` (diagonal Neutral included).
2. **For each result in `agg_results` (full history, including runs whose tabs were closed)**, the prefix is `ml + (" {idx+1}" if len>1)`. `ml` is `Avg` / `Median` / `Median (Lower)` / `Median (Upper)` / `Majority` / `Weighted`. **Note "Avg", not "Average", and "Majority", not "Majority Rule".** Four sheets follow:
   - `Aggregated ({pfx})`: the same frame as the DM sheet. The values are `scores or 0.0` (unresolved → 0.0), `number_format "0.00"`.
   - `Coh Scores ({pfx})`: header `Code, Policy, OI, II, WOI, WII`, rows in index order.
   - `Range Influence ({pfx})`: `Code, Policy, Entropy, Category` (raw floats; `-0.0` possible).
   - `Centrality ({pfx})`: `Code, Policy, Betweenness, Closeness`, **sorted by betweenness descending (stable)**.

   All titles are cut with `[:31]`.
3. `auto_width`: width = `max(len(str(v)) for truthy v) + 4`, minimum 14. Zero values are skipped.

Not exported: PCA, insights, ordinal median pairs, tie choices, weights, DM names per run, method parameters.

Verified sheet-name behaviour:

- Repeating a median run produces `Range Influence (Median (Lower)` and then openpyxl's de-duplicated `Range Influence (Median (Lower)1`, with a "Title is more than 31 characters" `UserWarning`.
- A DM named `Aggregated (Avg)` pushes the real aggregated sheet to `Aggregated (Avg)1`.
- A DM named `A/B` → `ValueError: Invalid character / found in sheet title`. Excel also forbids `\ ? * [ ] :`.
- Exported workbooks fail re-import: `Sheet "DM1": row and column headers do not match…`.

**LLM TXT** (`llm_tab.py:886-903`): the raw response written as UTF-8 to `policy_interpretation.txt`. Without a response: `Nothing to Save` / `Generate an interpretation first.`

**LLM PDF** (`llm_tab.py:905-1005`): reportlab `SimpleDocTemplate(A4, margins 2 cm all round)`.

- A line is a header if, after strip, it starts with `##` or with `"1."`…`"7."`. That includes `"10."` and any numbered list item.
- Headers are `Paragraph(clean, ParagraphStyle("Section", parent=Heading2, textColor=#2c4a6e, spaceAfter=6))`. They are **not XML-escaped**, so `&` or `<` in a header can break reportlab.
- Body lines are `Paragraph(line with & → &amp; and < → &lt;, Normal, spaceAfter=8, leading=14)`.
- Empty lines become `Spacer(1, 6)`.
- No title, date or metadata. Markdown `**bold**` is not interpreted.
- Fallback when reportlab is missing: fpdf2 (Helvetica B12 `#2c4a6e` headers, 10 pt body). fpdf2 is not in the lock.
- Errors → `PDF Error`. Default name `policy_interpretation.pdf`.

### 7. LLM (`llm_tab.py`)

| Item | Value |
| --- | --- |
| Engines (:61-77) | `Groq`: models `["llama-3.3-70b-versatile"]`, base `https://api.groq.com/openai/v1`. `OpenAI`: `["gpt-4o-mini", "gpt-4o"]`, base `https://api.openai.com/v1`. Both use `openai_compat`. The default is the first engine and its first model. |
| Request (:238-259) | `POST {base}/chat/completions` with JSON `{"model", "messages": [system, user], "max_tokens": 4096, "temperature": 0.3}`. Headers: `User-Agent: Mozilla/5.0 (compatible; PolicyCoherenceKit/1.0)`, `Accept: application/json`, `Content-Type: application/json`, `Authorization: Bearer {key}`. `urllib`, timeout 120 s, no streaming, no retry. |
| System prompt (:79-84) | `You are an expert policy analyst specialising in policy coherence and systems thinking. You provide rigorous, evidence-based, in-depth interpretations of policy interaction analyses. Your responses are structured, analytical, and written for policy professionals.` |
| User prompt (`build_prompt`, :101-196) | See below |
| Errors | HTTP error → `HTTP {code} from API:\n\n{error.message \| message \| body}`. URL error → `Network error: {reason}`. Bad shape → `Unexpected response structure:\n{data}`. Empty key → `API key is empty. Please enter a valid API key.` The UI wraps these as `LLM Error` / `The request failed:\n\n{error}`. A missing key before sending → `API Key Required` / `Please enter your API key before generating.` |
| Threading | A daemon thread; results come back via `self.after(0, …)`. The status line reads `Calling {engine} / {model} ...` → `Done.` / `Error.` The button reads `Generating...`. |
| Key handling | The key is stripped. `_api_key_var.set("")` runs on **both** success and error (:841, :848). The key is never persisted. Hint text: `API key is used once and never stored.` |
| Display | Header lines (same rule as the PDF) are shown bold navy with `#` stripped. |

The prompt, built from a list of lines joined with `\n`, contains these sections in order:

1. **Header:** `You are given the results of a policy coherence analysis for {n} policies, aggregated using the {aggregation_method_label(result)} method.\n`
2. **Policy list:** `POLICY LIST:` followed by `  {code}: {name}` lines.
3. **Aggregated matrix:** `AGGREGATED SCORE MATRIX (rows = influencing policy, columns = influenced policy, scale: -3=Cancelling to +3=Indivisible, 0=diagonal):`. The header row is 9 spaces plus `"  ".join(f"{c:>6}")`. Each matrix row is `f"  {code:>5}  "` plus `"  ".join(f"{s:>6.2f}")`.
4. **Coherence scores:** `COHERENCE SCORES (OI=…, II=…, WOI=…, WII=…):`, the header `f"  {'Code':<6} {'OI':>4} {'II':>4} {'WOI':>7} {'WII':>7}  Policy"`, then the rows.
5. **Entropy:** `RANGE OF INFLUENCE — SHANNON ENTROPY (…):`, with rows formatted `{entropy:>8.4f}  {category:<14}`.
6. **Centrality:** `NETWORK CENTRALITY (Betweenness: broker role 0-1; Closeness: reachability, higher=more central):`, rows sorted by betweenness descending, formatted `{:>12.4f} {:>10.4f}`.
7. **Instruction:** the instruction paragraph, the 7 `## {header}` lines (`1. Overall Coherence Assessment` … `7. Strategic Recommendations`), and the closing paragraph.

The prompt is a deterministic pure function, so it is ideal for a parity fixture. It never includes PCA or insights.

### 8. Persistence and settings

There is no project save or load, no settings file, and no JSON or pickle (grep: the only `open(` calls are the TXT export and the dead CSV reader). All state is lost on exit. Side effects:

- `font_loader.load_inter()` copies `Inter-{Regular,Medium,Bold,Italic}.ttf` into `~/Library/Fonts` (macOS) or `~/.local/share/fonts` plus `fc-cache -f` (Linux). On Windows it uses `AddFontResourceExW(FR_PRIVATE)`.
- The exports listed above.

`assets/fonts/logo_icon_sidebar.png` (2.3 KB) is the sidebar logo.

### 9. Dependencies

`tk-app/pyproject.toml`:

- `requires-python >=3.9`;
- dependencies unpinned: `openpyxl`, `numpy`, `reportlab`, `Pillow`;
- dev dependency `watchfiles>=1.0.0`;
- `[tool.uv] package = false`.

`uv.lock` (revision 3) splits on Python version:

| Package | <3.10 | 3.10 | 3.11 | **≥3.12 (incl. 3.13)** |
| --- | --- | --- | --- | --- |
| numpy | 2.0.2 | 2.2.6 | 2.4.6 | **2.5.4** (11 cp313 wheels in the lock) |
| Pillow | 11.3.0 | 12.3.0 | 13.0.0 | **13.0.0** (12 cp313 wheels) |
| openpyxl | 3.1.5 | ← | ← | **3.1.5** (needs et-xmlfile 2.0.0) |
| reportlab | 5.1.0 | ← | ← | **5.1.0** (needs charset-normalizer 3.5.2 and Pillow) |
| watchfiles (dev) | 1.1.1 | 1.3.0 | 1.3.0 | 1.3.0 |

Verified: `uv run --frozen --no-dev --python 3.13` installs and imports these versions; `tkinter.TkVersion` 8.6 in the uv-managed 3.13.2. The Dockerfiles use `python:3.13-slim` with `uv sync --frozen`. numpy on macOS arm64 is built against **Accelerate**, while Linux wheels use OpenBLAS (read only for Linux), so SVD/eigh low bits and signs may differ across platforms. Pillow is imported unconditionally by `app.py:12` but is only *needed* for ImageGrab and the icons. The API does not need Pillow, unless it is kept for reportlab images (reportlab declares it as a dependency).

### 10. Parity traps, bugs and inconsistencies

| # | Trap / bug | Evidence | Port guidance |
| --- | --- | --- | --- |
| 1 | PCA eigenvector signs are arbitrary and BLAS-dependent (Accelerate vs OpenBLAS); no sign convention | `pca_tab.py:103-119` | Compare fixtures per component up to a sign flip, or record a sign convention as a deliberate decision. Explained % is sign-free. |
| 2 | Python `round()` is half-to-even on binary values: `round(0.125,2)=0.12`, `round(2.675,2)=2.67`, int `round(12.5)=12` | Run output | Keep the computation in Python and send rounded floats. The web app must only format with `toFixed`, never re-round, and should be aware that `toFixed` differs on halves. |
| 3 | `entropy` can be `-0.0` (and weighted scores `-0.0`); `f"{-0.0:+.2f}"` → `-0.00` | Verified `repr(-0.0)` | Decide whether to preserve it (JSON `-0.0`) or normalise. Fixtures must compare numerically, not textually. |
| 4 | Unresolved ties (`None`) are read as 0 by every analysis and the export | `or 0.0` everywhere | The API must refuse analysis until all ties are resolved (the UI enforces this). |
| 5 | Average with fewer than 3 DMs is a **UI** rule, not an aggregator rule | `app.py:2558-2560` | Enforce it in the API request validation, or document it as UI-only. |
| 6 | Weights are not renormalised and the tolerance is ±0.01 | `aggregator.py:360-364`, `[0.335]*3` accepted | Port it as is |
| 7 | Brandes tolerance `1e-9` with left-to-right float sums; back-prop tie order is `(d,v)` descending | `network_tab.py:208, 261-262` | Port the algorithm verbatim; do not use networkx (closeness semantics differ too) |
| 8 | Closeness uses outgoing distances, can exceed 1, and multiplies by the reachability fraction | `network_tab.py:298-307` | Port verbatim |
| 9 | `max`/stable `sorted` tie-breaking by index (top driver, contested, strongest link, centrality order) | `results_insights_tab.py:327-333, 439-446, 652-658` | Port with identical keys and stable sorts |
| 10 | `_pearson_corr` returns 1.0 for zero variance, so a single-DM run or identical DMs give agreement 1.0 | :379-380, :386-387 | Port verbatim |
| 11 | Median `ordinal_cells` is never displayed or exported; the even-count pair is invisible to users | grep | Decide whether the web UI shows the pair (AGENTS.md says to preserve both labels) |
| 12 | Label drift: Results Insights uses `aggregation_method_label(method_str)` → "Median" without Lower/Upper, and `" - "` instead of `" — "`; export uses "Avg"/"Majority" | `results_insights_tab.py:291, 700, 878`; `app.py:3149-3158` | Pick one label source (`aggregation_method_label(result)`) and record a decision |
| 13 | Export sheet names are truncated to 31 characters and lose the run index; openpyxl de-duplicates with `…1`; invalid characters in DM names crash the export; DM and result sheet names can collide | Verified | Sanitise and de-duplicate in the port, and record a decision. Byte-for-byte XLSX parity is impossible anyway. |
| 14 | Import ignores blank header cells but reads data positionally, so a gap column silently misaligns the data | Verified: sheet `S3`, `X->Y` read from the blank column | Reject or warn in the port (decision) |
| 15 | One bad sheet aborts the whole import; "empty/skipped" warnings are shown under the heading "blank cells" | `importer.py:109,160`; `app.py:2988-2990` | Keep or improve (decision) |
| 16 | Import does not reject duplicate policy names; the setup dialog does | `dialogs.py:1118` vs importer | Add validation (decision) |
| 17 | The story banner and `_strongest_link` call every negative link "constraining" (including Cancelling); the "Strongest Link" tag and card ignore negative links | :525, :540, :830, :1016 | Port the text verbatim for parity, or fix it by decision |
| 18 | `_build_narrative()[:4]` always drops the agreement sentence; narrative, quadrants, top broker, consensus and ~11 card builders are dead | Grep | Do not port the dead UI; keep the pure fields only if useful |
| 19 | Cached analyses are never invalidated (`_cached_*`); `resolve_ties` mutates in place | `aggregator.py:87-90, 280-286` | The stateless API recomputes per request, so the issue does not arise |
| 20 | `TieResolutionDialog._on_ok` writes `chosen` to the earlier ties before failing on a later blank | `aggregation_dialog.py:779-791` | UI-only; the API should validate atomically |
| 21 | `PolicyMatrix` shares the `policies` list object across DMs and results | `app.py:2398`, `aggregator.py:134` | Irrelevant for a stateless API |
| 22 | Dead code: `NewMatrixDialog`, `_read_policies_from_file` (CSV/XLSX policy list import), `_ProjectNameDialog`, `PolicyMatrix.is_complete`/`to_dict_records`, `__init__.run()` (skips DPI and font setup), the fpdf2 fallback | Grep | Do not port |
| 23 | LLM header detection treats any line starting with `1.`–`7.` (also `10.`) as a header; PDF headers are unescaped | `llm_tab.py:869-871, 958-966` | Port the rule, escape headers |
| 24 | The aggregator header says scores are "rounded to 2 dp" for all methods, and the docstring method list omits median | `aggregator.py:17, 60` | Documentation only |
| 25 | Example workbook: 1 DM, policy "names" = `P1..P14`, so labels read like `P14 (P14)`; it cannot exercise Median, Majority or Weighted through the UI | Probe output | Use synthetic workbooks for parity |

### 11. Proposed parity fixture plan

**Entrypoints to call (all headless-safe once `tk-app/` is on `sys.path`; tkinter must be importable but no display or `Tk()` is needed):**

- `importer.import_matrices_from_excel(path)`: matrices (name, policies, codes, data) and warnings, or the error string.
- `aggregator.check_completeness`, `aggregate_average`, `aggregate_median(even_choice)`, `aggregate_majority`, `resolve_ties` (after setting `TiedCell.chosen`), `aggregate_weighted`, `aggregation_method_label`. Record every `AggregationResult` field, including `ties`, `source_scores`, `ordinal_cells` and `median_even_choice`.
- `coherence_scores_tab.compute_scores`, `range_of_influence_tab.compute_entropy`, `pca_tab.compute_pca`, `network_tab._build_graph` and `compute_centrality`, `results_insights_tab.compute_insights`, `_build_story_banner`, `_build_system_health`, `_build_supporting_interpretation`, `_strongest_link`.
- GUI-derived values worth capturing:
  - `aggregation_tab._score_bucket` per cell;
  - `coherence_scores_tab._value_color`/`_count_color`;
  - the network density and isolated count (re-implement the 3 lines from `network_tab.py:381-388`, because they sit inside `_build_info_bar`);
  - the centrality report order;
  - the conflict ratio and caption.
- `llm_tab.build_prompt(result)`: the exact prompt string.
- `app._export_to_excel(matrices, results, path)`: save the XLSX and also a JSON dump of every sheet's cell values. Compare values, not bytes.

**Headless obstacles:**

- Every `*_tab.py` imports `tkinter` and `theme` at module level, and `app.py` imports Pillow. The locked env provides both, and uv's Python 3.13.2 has Tk 8.6. Run with `PYTHONDONTWRITEBYTECODE=1` so no `__pycache__` lands in `tk-app/`, and use `UV_PROJECT_ENVIRONMENT` outside the repo (or accept `tk-app/.venv`, which is gitignored if configured).
- Do not import `main` or `font_loader`: importing `main` creates no window, but calling `main()` or `load_inter()` would install fonts.
- `compute_*` cache into the result, so build a fresh result per call, or call them in a fixed order.
- Layout functions and plot exports need a canvas or screen. Exclude them from numeric parity (or instantiate the class without `__init__` and call `_force_directed_layout_positions` with a fixed w/h if layout parity is wanted).
- The dialogs (method, weights, median, ties) cannot run headlessly. The generator must replicate `_run_aggregation`'s branching (`<3` → average, even → median choice, ties → chosen).

**Cases (inputs × methods):**

| Input | Policies × DMs | Methods to run | Purpose |
| --- | --- | --- | --- |
| `WEF Nexus Example.xlsx` | 14 × 1 | average (forced), plus all methods directly at aggregator level | Real data, import fixture; checks forced Average |
| Synthetic seeded random | 5 × 3 | average, median (odd → `Median`), majority (ties likely, resolve with first, last and middle label), weighted `[0.2,0.3,0.5]` | Core |
| Synthetic seeded random | 6 × 4 | median lower, median upper (pairs differ), majority with ties, average (`x.25`/`x.75` rounding), weighted `[0.25]*4` and `[0.1,0.2,0.3,0.4]` | Even-count rules |
| Synthetic seeded random | 8 × 8 | average (exact `.125`/`.375` halves → half-even), weighted with float sums | Rounding traps |
| Synthetic | 3 × 3 with all Neutral | all | PCA zero variance, entropy 0, centrality 0, agreement 1.0 |
| Synthetic | 3 × 1 with one non-zero link | average | `entropy == -0.0`, isolated nodes, closeness 0 |
| Synthetic | 2 × 3 | all | `hmax = 1.0`, PCA invalid (`n<3`), betweenness normalisation `1` |
| Synthetic | 2 × 1 | average | Minimal; closeness 3.0 |
| Synthetic | 6 × 3, all-negative ratings | all | Negative edges in graph and centrality; banner tone; health conflict |
| Synthetic | 7 × 4 with designed equal-length paths (e.g. scores ±1 and ±2, so 1/1 + 1/1 = 1/0.5) | average | Brandes multi-path counting and the `1e-9` tolerance |
| Synthetic | 5 × 3 with identical DMs | all | Zero-variance Spearman → 1.0, contested ordering by index |
| Weights edge cases | 3 DMs | `[0.335]*3` (accepted), `[0.3]*3`, `[1.2,−.1,−.1]`, wrong length | Exact error strings |
| Median invalid choice, empty list, policy mismatch, blank cell (KeyError path), unresolved tie | — | — | Exact error strings |
| Import workbooks | Built by openpyxl in the generator | — | Case-insensitive labels with spaces; `"none"`; blanks over 10 (`+k more`); bad values over 10 (`...`); header mismatch over 5; empty sheet; header with fewer than 2 policies; numeric headers; numeric cells; gap column (misalignment); diagonal junk; multi-sheet with one bad sheet (whole-import error) |
| Export | 4 DMs × 3 runs (avg, median lower ×2) + 1 run | `_export_to_excel` | Sheet naming, truncation and de-duplication, "Avg", sort order, `0.00` formatting, unresolved → 0 |
| LLM prompt | One per method | `build_prompt` | Exact text |

Record the numpy version, the platform and the BLAS name in every fixture. Use `atol=1e-12` for floats, compare PCA coordinates up to a per-component sign, and use exact equality for strings, orders and integer counts.

## Limitations

- The Linux (OpenBLAS) PCA output was not run. The claim that signs or low bits may differ comes from the BLAS difference, not from an observed diff.
- Layout functions, the Tk drawing code, ImageGrab exports, the reportlab PDF and live LLM calls were read, not executed. LLM endpoints and model availability were not checked against the providers.
- `matrix_widget.py`, `dialogs.py` (styling parts), `theme.py` and the app shell (sidebar, tabs, animations) were skimmed for logic only. A separate UI inventory is needed for exact visual strings, sizes and colours beyond those quoted here.
- Random cases used `random.Random(seed)`. Fixture authors should pin their own seeds and store the matrices in the fixtures.
- Docker files were checked only for the base image and the `uv sync --frozen` usage.

## Recommendations

1. Write `scripts/generate_parity_fixtures.py` (repo root) that runs under `uv run --frozen --no-dev --python 3.13 --project tk-app` with `PYTHONDONTWRITEBYTECODE=1` and covers the case table in Finding 11. The API should pin numpy 2.5.4 and openpyxl 3.1.5, and reportlab 5.1.0 if PDF export moves server-side.
2. Record decisions in `docs/decisions/` for:
   - the PCA sign convention or a sign-tolerant comparison;
   - one method-label source (fix "Avg"/"Median" drift or keep it);
   - showing the even-median ordinal pair;
   - sheet-name sanitising and de-duplication;
   - import gap-column handling and duplicate-policy validation;
   - whether `<3 DMs → Average` and weight validation are API rules;
   - whether to keep the "constraining" wording bug and the `-0.0` outputs.
3. Port `aggregator.py`, `importer.py`, the five `compute_*` functions, the Results Insights helpers and `build_prompt` verbatim into Tk-free modules. Do not port the dead cards, dialogs or the fpdf2 fallback.
4. Keep the LLM key handling contract (stripped, used once, never logged or persisted, cleared on success and failure). Server-side, that means never logging the request headers.
5. Replace ImageGrab plot export with client-side SVG/PNG export in the web app. Keep the default names `pca_plot.png`, `network_plot.png`, `policy_interpretation.txt/.pdf` and `{project}_coherence.xlsx` (spaces → `_`).

## References

- `tk-app/aggregator.py`, `tk-app/importer.py`, `tk-app/models.py`, `tk-app/constants.py`
- `tk-app/coherence_scores_tab.py:73-142`, `tk-app/range_of_influence_tab.py:55-141`, `tk-app/pca_tab.py:39-121, 331-368`, `tk-app/network_tab.py:56-320, 690-1013`, `tk-app/results_insights_tab.py:290-664, 694-1084`, `tk-app/llm_tab.py:61-272, 802-1005`
- `tk-app/app.py:179-190, 2533-2682, 2919-3217`, `tk-app/aggregation_dialog.py`, `tk-app/dialogs.py:1080-1124, 1625-1671`, `tk-app/aggregation_tab.py:50-86`
- `tk-app/pyproject.toml`, `tk-app/uv.lock`, `tk-app/Dockerfile.dev`, `tk-app/Dockerfile.prod`, `tk-app/font_loader.py`, `tk-app/main.py`
- `AGENTS.md` (repository root)
- Sibling playbook: `dematelab/docs/reports/2026-11-16-qt-to-fastapi-and-tanstack-migration-playbook-report.md` (Findings 3 and 6)
- Probe scripts (outside the repo, not committed): `/tmp/pck-inv/scripts/probe.py`, `probe2.py`, `probe3.py`, `probe4.py`
