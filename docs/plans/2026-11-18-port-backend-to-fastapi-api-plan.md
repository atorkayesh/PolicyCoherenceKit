# Port The Policy Coherence Kit Backend To A Dockerised FastAPI `apps/api`

**Date:** 18 November, 2026
**Status:** Ready for implementation
**Owner:** Youpele Michael (planned with Claude Code)
**Created:** 2026-11-18 18:30 CET · **Last modified:** 2026-11-18 19:40 CET (revision 3: owner decision of
2026-11-18, browser charts with Apache ECharts drawn from API chart data, replaces server-rendered matplotlib PNGs)
**Inspected:** `policycoherencekit`, branch `restructure/apps-api-web`, commit
`00b610a`. The worktree is not clean: the legacy app has been moved into `tk-app/` (staged renames; `tk-app/.dockerignore`,
`Makefile` and `docker-compose-{dev,prod}.yml` also have unstaged edits), the sample workbook has moved to
`data/examples/WEF Nexus Example.xlsx`, `.gitignore` has been modified and `docs/` is untracked. `apps/`, `nginx/` and
`scripts/` do not exist yet. Conventions source: `dematelab` at commit `6a76ae2`
(`apps/api`, root `Makefile`, `docker-compose-*.yml`, `nginx/`, `docs/decisions/`).

## Summary

This plan moves everything the Tk app does, apart from drawing widgets, into a stateless FastAPI service in `apps/api`:

- the four aggregation methods and every rule the GUI enforces;
- the five analyses (coherence scores, range of influence, PCA, network centrality, results insights);
- Excel import and XLSX export;
- the chart data the browser needs to draw the PCA and network plots with Apache ECharts (layout coordinates,
  edges, colours, axis bounds and texts), so the browser draws but never computes;
- the AI interpretation and its PDF export.

The service runs in Docker with the same Compose, Nginx and Make setup as DEMATELab.

**Same numbers, fixed labels.** For the same input, every number must equal the Tk app's. Parity fixtures generated from
`tk-app/` prove this. Wrong labels and texts are fixed, and each fix is listed.

The TanStack Start frontend has its own plan, `docs/plans/2026-11-18-rebuild-ui-in-tanstack-start-plan.md`, which is
written after this one and depends on the API contract below. This plan creates the root Compose, Nginx and Make files
with both services, so the frontend plan only fills in `apps/web`.

## Related Work

- Report: [Tk app logic inventory](../reports/2026-11-18-tk-app-logic-inventory-report.md). This is the source of the
  formulas, messages, parity traps and the fixture case list.
- Report: [Tk app UI inventory](../reports/2026-11-18-tk-app-ui-inventory-report.md). This is the source of the screens,
  texts, label inconsistencies and the step mapping.
- Report: [DEMATELab conventions inventory](../reports/2026-11-18-dematelab-conventions-inventory-report.md). It says
  what to copy, adapt or strip, and lists the ports, names and versions.
- Model plan: `dematelab/docs/plans/2026-11-16-port-backend-to-fastapi-api-plan.md`.
- Playbook: `dematelab/docs/reports/2026-11-16-qt-to-fastapi-and-tanstack-migration-playbook-report.md`
  (Findings 4, 6, 8 and 9).
- Frontend plan, to be written next: `docs/plans/2026-11-18-rebuild-ui-in-tanstack-start-plan.md`.
- Research: [browser chart libraries](../research/2026-11-18-browser-chart-libraries-research.md). Its ECharts findings
  and Part A (P1–P9) of `docs/plans/2026-11-18-browser-charts-and-shared-vps-plan.md` were moved into this plan and the
  frontend plan on 2026-11-18 (Settled Decision 7). That plan keeps only Part B (shared VPS).
- Decisions: none exist yet in `docs/decisions/`. Phase 9 creates them.
- JuGit issue or merge request: none identified. The work is tracked by this plan and the branch.

## Problem

All logic runs inside a Tkinter desktop app, which can also be served in Docker over noVNC. The app has no HTTP API and
no tests. About a third of its rules live in GUI files:

- the fewer-than-three-decision-makers rule and the run flow (`tk-app/app.py:2533-2611`);
- weight validation (`tk-app/aggregation_dialog.py:570-613`);
- project setup validation (`tk-app/dialogs.py:1080-1124`);
- the import policy-list check (`tk-app/app.py:2964-2978`);
- Excel export (`tk-app/app.py:3085-3217`);
- every analysis function, each in a `*_tab.py` that imports `tkinter`;
- the results-insights card texts, built inside Tk methods (`tk-app/results_insights_tab.py:739-1084`).

A web frontend cannot use any of this.

## Goals

- Every non-UI capability of the Tk app is available under `/api/v1`, using the endpoints in the API Contract. The
  contract supports a one-question-per-step (Typeform-style) web flow.
- Numerical parity with the Tk app, proven by frozen fixtures generated from `tk-app/`. Parity tolerance is
  `rtol=0, atol=1e-12`, and PCA is compared per component up to a sign flip.
- The exact legacy texts are produced by the API: the insights story, the interpretation and the card texts, plus the AI
  prompt. Exact-text fixtures check them.
- XLSX export reproduces the `_export_to_excel` layout for the current run, with the listed label fixes.
- Code follows DEMATELab's API rules, copied into `apps/api/AGENTS.md`:
  - routers → features → services/utils;
  - class-based modules with shared instances;
  - absolute imports and docstring-only `__init__.py` files;
  - `Optional[...]` typing and Google docstrings;
  - co-located `*_test.py` files;
  - Ruff E/F/I/B at 120 columns;
  - every code file ≤ 300 lines;
  - `AppError` subclasses only.
- `make dev` starts the API (and the web app once it exists) with hot reload. `make prod` runs gunicorn behind Nginx.
  `make check-api` passes inside the dev container.
- `apps/` never imports, reads or starts anything in `tk-app/`.

## Non-Goals

- The frontend content of `apps/web`. This plan only adds its Compose, Nginx and Make entries, guarded so that they work
  before `apps/web` exists (Phase 8).
- Changing any formula, rounding, ordering, threshold, the prompt text or the colour constants. Known odd behaviour is
  kept and listed under Known Tkinter Behaviour Kept.
- Persistence, accounts, authentication, multiple projects, and saving or loading projects.
- Run history. The legacy export appends every past run (`app.py:2617`), but the stateless API exports the current run
  only (Settled Decision 8).
- Exporting matrices before an analysis. The legacy `Export Excel` works without results; here export needs a complete,
  analysable request.
- Dead legacy code, which is not ported:
  - `NewMatrixDialog` and `_read_policies_from_file`;
  - the fpdf2 fallback;
  - `__init__.run()`;
  - the CSV policy-list import;
  - the never-rendered Results Insights builders (`_scatter_card`, `_agreement_heatmap_card`, `_relations_card`,
    `_configuration_card`, `_ranking_card` and the others in the logic report, Finding 4);
  - `_build_narrative`, the quadrants, `top_broker`, `top_prominent`, the `drivers`/`dependents`/`balanced` lists,
    `strong_consensus` and `top_*_rows`.

  The fixtures still record the dead `compute_insights` fields, but the API does not return them.
- Drawing charts, and any matplotlib. The API returns chart data only; the frontend plan draws it with ECharts and
  produces the PNG/SVG downloads in the browser. Chart tables (coherence scores, range of influence, the aggregated
  grid, health bars) are returned as data, and the web app renders them as tables (no new bar charts, P6).
- Any change to `tk-app/`. It is read-only.

## Settled Decisions (owner-approved; do not reopen without new evidence)

1. **Layout as DEMATELab.**
   - `apps/api`: FastAPI on Python 3.13 with uv, Ruff and pytest. Layers are routers → features → services/utils, plus
     `constants/`, `models/`, `errors/`, `middleware/` and `config/`. Every code file is ≤ 300 lines. Tests are
     co-located `*_test.py` files.
   - `apps/web`: covered by the separate frontend plan. This plan creates Compose, Nginx and Make entries for both
     services.
   - `tk-app/` is the read-only legacy reference.
   - `scripts/generate_parity_fixtures.py` (entry point) and its helper modules in `scripts/parity/` are the only code
     that runs against `tk-app/`.
   - `apps/` never imports `tk-app/`, and a repository-rules test enforces this (Phase 9). The legacy top-level modules
     `models` and `constants` share their names with the `apps/api` packages, so the test checks for legacy-only module
     names and for `tk-app` string literals, not for package names.
2. **Ports and names.**
   - Ports are the same in dev and inside the containers: web **3001**, API **50002**.
   - The production Nginx host port defaults to **8081** (`${HTTP_PORT:-8081}:80`) and can be overridden.
   - Compose projects are `policycoherencekit-dev` and `policycoherencekit`. Containers are `policycoherencekit-api`,
     `policycoherencekit-web` and `policycoherencekit-nginx`. Images use Compose's automatic names
     (`policycoherencekit-dev-api`, `policycoherencekit-api`, …). Networks are `app-network`.
   - There are no named volumes.
   - The legacy stack keeps `policycoherencekit-tk-dev` / `policycoherencekit-tk-prod`, so the new stacks, the legacy
     stacks, DEMATELab and ice2kg can all run on one host.
3. **Stateless API.**
   - Every results endpoint (analysis, network chart data, export, explanation) receives the full request and recomputes.
     That request holds the project name, policies, decision-makers with their rating matrices, the method,
     weights/median choice and tie choices.
   - Nothing is persisted, cached or logged that contains user data.
   - There is one project per browser session, and the multi-project sidebar is dropped.
4. **Numerical parity: "keep maths, fix labels".**
   - Numbers are ported exactly, including the calculation defects. These are listed under Known Tkinter Behaviour Kept
     as candidates for a later, separate change, which would need new fixtures and a decision record.
   - Wrong labels and texts are fixed and listed under Label Fixes.
   - Every method name comes from one function, the port of `aggregation_method_label` (`tk-app/aggregator.py:373-391`).
5. **Parity fixtures before maths.**
   - Run the legacy code with
     `uv run --frozen --python 3.13 --project tk-app python scripts/parity/generate_parity_fixtures.py`.
   - Use synthetic cases from the logic report (Finding 11; see Phase 2).
   - Float tolerance is `atol=1e-12`. PCA is compared per component up to a sign flip (only `explained` for degenerate
     cases, Phase 9), with platform BLAS differences documented.
   - Legacy texts (messages, card values, story) are **captured by running the legacy code**, not re-typed; only tag and
     hero labels built directly in `tk.Label(...)` calls are hand-copied (Phase 2).
   - Insights texts and the AI prompt are compared as exact text.
   - Numerical libraries are pinned to the legacy lock's Python ≥ 3.12 resolution: `numpy==2.5.4`, `openpyxl==3.1.5`,
     `reportlab==5.1.0`, `pillow==13.0.0`.
6. **Business rules hidden in GUI files move into the API; the browser does no maths.** See the table below.
7. **Charts are drawn in the browser with Apache ECharts from API chart data** (owner decision 2026-11-18; replaces
   the earlier server-side matplotlib PNG decision). The API computes every value the browser draws and **contains no
   matplotlib and no image rendering for charts**; there are no PNG chart endpoints, hotspot endpoints, chart fonts
   or dpi rules. Settled sub-decisions (from the follow-up plan's P decisions, adopted as recommended):
   - **P1** ECharts is the only chart library (frontend plan).
   - **P3** Network layouts (circular, force-directed, spectral, shell, in legacy order) and PCA coordinates are
     computed in the API. L16's spectral sign rule stays, and layout coordinates keep parity with legacy fixtures.
   - **P4** The overlapping two-way arrows (L7) are fixed as a display fix only: the API flags `two_way` edges and the
     browser curves each pair to opposite sides. No number changes.
   - **P5** PCA is a plain scatter as legacy (no loadings, no biplot, no quadrants; the legacy plot has none).
   - **P6** No new bar charts: only plots the legacy app draws get a chart.
   - **P9** Aspect ratio is kept: layouts are computed on a square logical canvas (Settled Decision 14), so circular
     and shell layouts are not distorted.
   - **P7/P8** (frontend): tooltips, legend toggle, zoom/pan with reset, no node dragging; downloads PNG 2400×1800 px
     with a 300 dpi `pHYs` chunk plus SVG, produced in the browser.
   - The legacy app draws exactly two plots on a Tk canvas: the **PCA scatter** and the **network graph** (full network
     and ego view, four layouts).
   - Coherence Scores, Range of Influence, the Aggregated grid and the health bars are tables or widgets, not plots
     (`coherence_scores_tab.py:313`, `range_of_influence_tab.py:360`, `aggregation_tab.py:417`). The API returns them as
     data with their colour-band keys, and no new chart is invented.
   - Nodes and PCA points carry the legacy hover text `label` (`{code}:  {policy}`, two spaces) for the browser
     tooltips.
8. **Exports.**
   - XLSX export uses the legacy `_export_to_excel` layout for the **current run only**. This is a settled change:
     stateless means there is no run history.
   - The sheet-name truncation and the crash on invalid characters are fixed as label fixes; numbers are unchanged.
   - The AI interpretation PDF export uses reportlab in the API, in the legacy layout.
   - The TXT download is produced client-side.
9. **AI interpretation.**
   - The same six providers as DEMATELab: Anthropic, Azure OpenAI, Gemini, Groq, OpenAI and OpenRouter.
   - Reused from DEMATELab: the provider service, the model catalogue and providers endpoint, error mapping, the Gemini
     fixes, 120 s timeouts, and the Azure https + host allow-list (SSRF guard).
   - Keys are supplied per request and are never stored or logged.
   - The prompt is exactly the legacy `build_prompt` text (`llm_tab.py:101-196`), and a fixture tests it.
10. **Excel import endpoint** with the legacy rules and verbatim messages:
    - The misleading "blank cells" heading for skipped sheets is fixed as a label fix.
    - `.xls` is not accepted.
    - Validation is added for duplicate policies, header gaps and decision-maker name clashes (see the table below).
11. **Docker, Compose, Nginx and the Makefile are copied from DEMATELab and adapted.**
    - `make dev`, `make check-api` and `make prod` work with docker or podman before `apps/web` exists. `make check`
      (which includes `check-web`) is expected to pass only once the frontend plan's Phase 1 has landed.
    - Each service has its own `.env`.
    - Nginx is the only public entry in production.
    - HTTPS is prepared but commented out.
12. **Docs.**
    - The root `README.md` and `AGENTS.md` are rewritten for the new layout.
    - Add `apps/api/AGENTS.md`, `apps/api/CLAUDE.md` and `apps/api/README.md`.
    - Add decision records in `docs/decisions/` that mirror DEMATELab's (Phase 9), plus three new ones:
      `keep-legacy-maths-fix-labels`, `one-project-per-browser-session` and `browser-charts-with-echarts`.
13. **Process.** Implementers never commit or push, never create worktrees or branches, and report every deviation from
    this plan with evidence.
14. **Planning-level choices made here, within the owner's decisions:**
    - **Resource limits** of 2–100 policies and 1–50 decision-makers. The legacy app has no limits. These match
      DEMATELab and bound the Brandes cost (about 1–3 s at the maximum).
    - **Header gap columns are rejected on import.** Legacy reads data positionally after skipping blank headers, which
      silently misaligns cells (logic report trap 14). Rejecting is validation, not maths.
    - **Duplicate policy names are rejected on import**, the same rule as the setup dialog.
    - **Analysis requests use exact canonical rating labels.** Only import matches labels case-insensitively.
    - **Network layout geometry is fixed** at a square logical canvas of 600×600 px with the legacy margin 80
      (`NETWORK_LAYOUT_CANVAS`). The ported legacy layout functions run unchanged on it (including the per-axis
      `_normalize_positions` stretch, kept for parity), and the browser maps the 600×600 box onto a square plot area,
      so the aspect ratio is kept (P9). Layout fixtures are generated on the same canvas.
    - **PCA axis bounds** are returned as the legacy `_redraw` computes them (`pca_tab.py:436-442`: min/max, range
      `or 1.0`), so the browser sets axis limits without computing them.

### Business rules moved into the API

| Rule | Legacy source | API behaviour |
| --- | --- | --- |
| Fewer than 3 DMs forces Average, with no dialog | `app.py:2558-2560` | Effective method `average`. `aggregation.method_forced = true` whenever the decision-maker count is below the method-choice minimum, whatever method was requested (coordinator change, 2026-11-18). Weights, median choice and tie choices are then ignored. `/matrices/check` reports `method_choice_available = false` and `forced_method = "average"`. |
| Median Lower/Upper only for an even DM count | `app.py:2578-2585`, `aggregator.py:269` | `median_choice` is used only when the count is even, defaulting to `"lower"` as the dialog does (`aggregation_dialog.py:247-428`). With an odd count it is ignored and `median_choice` is `null` in the result. |
| Weight validation | `aggregation_dialog.py:570-613`, `aggregator.py:351-363` | Required for `weighted`, one per DM, each in [0, 1]. The sum is accepted when `abs(round(sum, 10) - 1.0) <= 0.01`, and weights are **not** renormalised (`[0.335]*3` is accepted; `[0.34, 0.34, 0.33]` is rejected because the difference is 0.010000000000000009). Messages use the dialog wording with the label fix. `/weights/check`: `within_tolerance` is the legacy `_update_sum` colour rule `abs(total - 1.0) <= 0.01` over the non-empty inputs, unrounded (`aggregation_dialog.py:558-568`), `false` when any input fails to parse; the sum error is reported only when every DM weight is present, parseable and in range. |
| Completeness before aggregation | `aggregator.py:97-119`, `app.py:2546-2556` | `/matrices/check` reports it. Every aggregation endpoint returns 422 `incomplete_matrices` with the legacy message. |
| Every majority tie resolved before analysis | `app.py:2598-2603`, `aggregation_dialog.py:779-791` | `/aggregation/preview` returns ties and accepts partial choices. `/analysis`, the network chart data, export and explanation return 422 `unresolved_tie` for the first unresolved tie in row-major order. Validation is atomic, unlike the legacy dialog. |
| Setup names | `dialogs.py:1080-1124` | `/setup/validate` and every request: DM names and policy names are trimmed, non-empty and unique (case-sensitive), with ≥ 1 DM and ≥ 2 policies, checked in legacy order with legacy messages. The project name is required. Order: project name → DMs (required, unique) → limits → policies (count, unique). Names containing C0 control characters (U+0000–U+001F) are rejected with `invalid_setup`: `Names must not contain control characters.` (new; security). |
| One policy list for all DMs | `aggregator.py:337-348` | Structural: the request has a single `policies` list. Each DM's `ratings` must be n×n. |
| Import policy-list equality | `app.py:2964-2978`; "new project from import" skipped it (`app.py:3000-3035`) | Always enforced. The reference is the `policies` form field if given, otherwise the first imported sheet. Mismatches return 422 `policy_list_mismatch` with the legacy message. |
| Import DM name clash | `dialogs.py:1102-1108` (setup only) | When the `decision_makers` form field is given, clashes return 422 `existing_decision_makers` with the legacy message. |
| Import duplicate policies, header gaps | none (new) | 422 `invalid_import` (messages under Phase 5). |
| Import sheet names that trim to empty or collide after trimming | none (new) | 422 `invalid_import`: `Sheet names must be non-empty and unique after trimming spaces.` |
| Duplicate tie choices | none (new) | Two `tie_choices` for the same `(row, col)`: 422 `invalid_tie_choice`, `Cell {Pi} → {Pj} has more than one tie choice.` |
| `.xls` offered but unreadable | `app.py:2931` | 422 `unsupported_file`. |

## Known Tkinter Behaviour Kept (parity; candidates for a later, separate change)

Each item is ported verbatim and named in the docstring of the module that ports it.

1. **PCA feature misalignment.** Each row drops its own diagonal, so column `j` means a different target per row
   (`pca_tab.py:90-93`).
2. **PCA has no sign convention.** Coordinates are `X_std @ Vt[:2].T` as numpy returns them (`pca_tab.py:103-119`).
   Standardisation uses population std, with zero std mapped to 1. An all-Neutral matrix gives all coordinates `0.0`
   with `valid = true`. With n < 3, PCA is invalid.
3. **Strongest Link ignores negative edges.** The card and tag use `strongest_pos_pair` only and always describe a
   positive link (legacy word `Reinforcing`, relabelled by L13), and show `No non-zero relation` when there are no positive edges
   (`results_insights_tab.py:815-818, 1013-1024`).
4. **Most Contested always names a pair.** Every off-diagonal cell is a candidate, so it names a pair even at full
   agreement, with the caption `Moderate disagreement` (`results_insights_tab.py:439-442, 1035-1039`). As a result,
   the two story branches without a contested link (`results_insights_tab.py:546-559`) and the interpretations for
   "no contested link" (`:600-604`) are practically unreachable.
5. **Max entropy is 1.0 for 2 policies** (`range_of_influence_tab.py:96`). The category uses the rounded H divided by the
   unrounded hmax. `Low` means both "no outgoing influence" and "concentrated".
6. **The top driver and top dependent can be negative.** They are `max` by `(woi, prominence, net)` and
   `(wii, prominence, -net)` (`results_insights_tab.py:652-653`). The texts still say "strongest outward influence".
7. **Betweenness uses a `1e-9` equal-path tolerance** (`network_tab.py:208`). Back-propagation sorts `(d, v)` in reverse
   (`network_tab.py:261-262`). The result is normalised by `(n-1)(n-2)` (1 when n ≤ 2) and rounded to 4 dp.
8. **Closeness uses outgoing distances.** It is computed as `(reachable/(n-1)) / mean(dist)` and can exceed 1
   (`network_tab.py:298-307`).
9. **Ties go to the first in index or row-major order.** This applies to `max()` and stable `sorted()` for the top
   driver, top dependent, contested ordering, the strongest pair (strict `>`/`<`), the strongest link per row and the
   centrality ranking (`sorted(..., reverse=True)` is stable).
10. **Agreement is 1.0 at zero variance.** `_pearson_corr` returns 1.0 when either vector has zero variance, so one DM
    or identical DMs give `average_agreement = 1.0` (`results_insights_tab.py:370-414`).
11. **Unresolved ties read as 0.** Every analysis reads `scores.get(..., 0.0) or 0.0`. This is ported verbatim but
    unreachable through the API, because unresolved ties are rejected first.
12. **`-0.0` is kept.** An entropy with exactly one non-zero link is `-0.0`, and weighted scores can be `-0.0`. Both are
    returned as `-0.0` in JSON and written as-is to XLSX.
13. **Python `round` is half-to-even on the binary value** (`round(0.125, 2) = 0.12`; integer `round(12.5) = 12` in
    System Health). All rounding happens in the API.
14. **Weights are not renormalised.** The tolerance is ±0.01 after `round(sum, 10)`. Weighted scores are
    `round(sum(w*s), 2)` using a left-to-right generator `sum`.
15. **Median never averages.** Ordinal labels are sorted stably by score. An even count keeps both middle labels in
    `ordinal_cells` and scores the chosen one.
16. **Majority tie options** are the modal labels sorted by score descending (`aggregator.py:190-200`).
17. **The story tone is chosen by sign only** (`score > 0`), so a `Cancelling` link is described like any other
    negative link (`results_insights_tab.py:525, 540, 549`). The branching is kept; the words are relabelled by L13.
18. **Display bands:**
    - `_score_bucket` breaks ties toward +∞ (`aggregation_tab.py:82-86`);
    - WOI/WII bands use per-cell thresholds (±0.5, ±1.5) on row and column sums (`coherence_scores_tab.py:73-87`);
    - OI/II bands use `oi/(n-1)` (`coherence_scores_tab.py:89-100`).
19. **Import edge cases:**
    - diagonal cells are ignored whatever they contain;
    - blank, `None` and the text `none` count as blank;
    - numeric cells are rejected as unrecognised;
    - numeric headers become `str(v)`;
    - one bad sheet aborts the whole import;
    - rows and columns beyond n are ignored (`importer.py:39-192`).
20. **AI-text headers.** Any line starting with `##` or with `1.`…`7.` is a header in the PDF, including `10.` and
    numbered list items (`llm_tab.py:869-871, 958-966`).
21. **The centrality table and the XLSX `Centrality` sheet** are sorted by betweenness descending (stable). The API
    returns the index-ordered list plus `centrality_ranking`.

## Label Fixes (text only; no number changes)

| # | Legacy | Fixed in the API | Evidence |
| --- | --- | --- | --- |
| L1 | Method name spelled four ways: `Median (Ordinal)` / `Weighted by Importance` (dialog); `Median` without Lower/Upper (Results Insights, `results_insights_tab.py:291, 700, 878`); `Avg` / `Majority` (export, `app.py:3149-3158`) | One source, `aggregation_method_label`. The option labels are `Average`, `Median`, `Majority Rule` and `Weighted`, with the legacy descriptions kept. The result label is `Median (Lower)` / `Median (Upper)` for even-count median runs. Insights and XLSX use the result label. | UI report §4 item 20 |
| L2 | "Weights must sum to exactly 1.0" while ±0.01 is accepted | Method description: `You assign a weight (0–1) to each DM. Weights must sum to 1.0 (±0.01).` Weight-sum error: `Current sum is {round(total,4)}.\nPlease adjust the weights so they sum to 1.0 (±0.01).` | `aggregation_dialog.py:80, 477, 609`; `aggregator.py:361-363` |
| L3 | XLSX sheet titles cut to 31 characters, with run index lost or `…1` de-duplication; `/` and other forbidden characters crash; DM and result titles collide | Result titles use a sheet label made from the result label by replacing `" ("` with `" "` and removing `")"` (for example `Median Lower`). The four titles are `Aggregated ({sl})`, `Coh Scores ({sl})`, `Range Influence ({sl})` and `Centrality ({sl})`; the longest is `Range Influence (Majority Rule)` at 31 characters. DM titles: replace each of `\ / ? * [ ] :` with `_`, strip leading and trailing `'`, use `Sheet` if empty, then cut to 31. Result titles are reserved first; DM titles are de-duplicated case-insensitively with ` (2)`, ` (3)`, …, cutting the base so the title stays ≤ 31. | Logic report Finding 6 and trap 13 |
| L4 | Import "skipped" warnings shown under `The following sheets have blank cells:` | Warnings are grouped by kind with headings: `The following sheets were skipped:` (kind `skipped`) and `The following sheets have blank cells:` (kind `blank_cells`). The messages themselves are verbatim. | `app.py:2987-2992, 3022-3027` |
| L5 | File picker offers `*.xls`, which openpyxl cannot read | 422 `unsupported_file`: `Only .xlsx workbooks are supported.` | `app.py:2931` |
| L6 | PDF header lines not XML-escaped (`&` or `<` breaks reportlab) | Headers are escaped like body lines (`&` → `&amp;`, `<` → `&lt;`). | `llm_tab.py:958-966` |
| L7 | Two-way network arrows drawn on top of each other (the perpendicular offset flips sign twice) | Display fix only (P4). The API sets `two_way = true` on both edges of a pair; the browser draws them as two curves on opposite sides (frontend plan). No coordinate or number changes. | `network_tab.py:932-940, 1111-1118` |
| L8 | Ego view `{code} has no direct connections.` drawn underneath the grey node | The API returns the text as `empty_message`; the browser shows it below the node, never over it. | `network_tab.py:1076-1090` |
| L9 | Missing-key message differs between UI and engine | `missing_api_key` public message: `Please enter your API key before generating.` (the legacy UI text). | `llm_tab.py` UI box, UI report §1.11 |
| L10 | Export filename can contain characters that are invalid for a file name | The name is `{project_name}_coherence.xlsx` with spaces → `_` (legacy), and then `/ \ : * ? " < > |` and control characters → `_`. It is sent as `filename="<ASCII fallback>"; filename*=UTF-8''<percent-encoded>`. | `app.py:3053` |

| L11 | Arrows written four ways: `->` (story, cards, messages), `→` (tags), `P1->P2` without spaces (incomplete and import messages), `↔` (Most Contested) | Every API display text and message, including the new ones in this plan, uses one arrow `→` with a space on each side (`P1 → P2`, `A (P1) → B (P2)`). The only exception is the Most Contested card main text, which keeps `↔` because it names an undirected disagreement. Exact-text tests apply this mapping to legacy outputs: `results_insights_tab.py:308` (`_pair_label` default `->` → `→`, used by the story, Strongest Link card and contested pairs), `:830` and `:835` (tags, already `→`), `:1015` (card main via `_format_pair`), `:1037` (`↔` kept); `app.py:2550` and `importer.py:169` (`{r}->{c}` → `{r} → {c}`); `importer.py:153` (`{ci}->{cj}:` → `{ci} → {cj}:`); `aggregation_dialog.py:786` and `aggregator.py:283` (`{r} -> {c}` → `{r} → {c}`). | UI report §4 item 25 |
| L12 | `Agreement` names two metrics (rank agreement in the overview, modal-share on Most Contested) | Most Contested value text `Agreement: {r:.2f}` → `Rating agreement: {r:.2f}`. `/scales.texts.most_contested_value_label = "Rating agreement"` documents it. The overview label is web-owned. | `results_insights_tab.py:1038`; UI report §4 item 24 |
| L13 | Tone words `Reinforcing`/`Constraining` (also rating labels) describe the sign of any link | Owner decision: sign wording. Exact before → after: story `through the reinforcing relationship {link}` → `through the positive link {link}`; `through the constraining relationship {link}` → `through the negative link {link}` (`:540, :549`); `_strongest_link` suffix `({s:+.2f} Reinforcing)` → `({s:+.2f}, positive)` and `({s:+.2f} Constraining)` → `({s:+.2f}, negative)` (`:525-526`); Strongest Link card value `{s:+.2f} Reinforcing` → `{s:+.2f} positive link` (`:1016`). Numbers, branch conditions and `No strong link` / `No strong outgoing link` are unchanged. | Owner decision 2026-11-18 |
| L14 | `decision-maker(s)` style texts | Every API text that states a DM count (none of the ported texts does today; the rule binds any new one, and the frontend plan applies it to the Results subtitle) chooses `decision-maker` for 1 and `decision-makers` otherwise (the legacy status already does, `app.py:2605`). Texts that do not state a count (`across decision-makers`) stay as is. `matrix/matrices` and `cell(s)` are kept verbatim (not part of the decision). | Owner decision 2026-11-18 |
| L15 | XLSX text cells written with openpyxl's type inference, so a DM or policy name starting with `=` becomes a formula | Every text cell (names, headers, labels) is written as a string (`cell.data_type = "s"` after assignment, or an explicit string cell), never as a formula. Security fix; layout unchanged. | `app.py:3085-3217` |
| L16 | Spectral layout depends on the arbitrary sign `eigh` returns for each eigenvector, so the picture can mirror between platforms | Deterministic sign rule: after `np.linalg.eigh`, each eigenvector column is flipped so that its largest-magnitude entry is positive (first such index on ties). The rest of `_spectral_layout_positions` (`network_tab.py:800-830`, including `y = y_vec + degree_bias`) is unchanged. The generator applies the same rule by wrapping `np.linalg.eigh` before calling the legacy layout, and records the eigenvalues in the fixture. | `network_tab.py:817, 823-830` |

Exact-text parity fixtures are compared **after** applying only the fixes in this table. Phase 9 lists the mapping the
tests apply (L11–L14 are applied as literal before → after string replacements on the captured legacy text; no other
normalisation).

## Current State

Source files (all under `tk-app/`; line counts from `wc -l`):

| File | What it holds | Port target |
| --- | --- | --- |
| `constants.py` (100) | Ratings and order `:14-22`, `DIAGONAL_VALUE` `:24`, colours `:30-49`, `RATING_SCORES` `:92-100` | `constants/rating_constants.py` |
| `models.py` (109) | `PolicyMatrix` `:13-90` (diagonal forced Neutral), `generate_codes` `:97-99` | `models/aggregation_models.py` (internal), `utils/matrix_utils.py` |
| `aggregator.py` (391) | `TiedCell` `:38-45`, `AggregationResult` `:49-90`, `check_completeness` `:97-119`, the four methods `:126-330`, `resolve_ties` `:273-286`, validators `:337-370`, `aggregation_method_label` `:373-391` | `features/aggregation_feature.py`, `features/matrix_check_feature.py`, `utils/aggregation_label_utils.py` |
| `importer.py` (192) | `import_matrices_from_excel` `:39-182`, `_match_rating` `:187-192` | `utils/excel_import_utils.py`, `features/workbook_import_feature.py` |
| `coherence_scores_tab.py` (499) | `_value_color` `:73-87`, `_count_color` `:89-100`, `compute_scores` `:107-142` | `features/coherence_scores_feature.py`, band keys in `constants/band_constants.py` |
| `range_of_influence_tab.py` (500) | `_CAT_COLORS` `:55-62`, `compute_entropy` `:82-127`, `_categorise` `:130-141` | `features/entropy_feature.py` |
| `pca_tab.py` (527) | `compute_pca` `:65-121`, drawing `:416-506`, constants `:40-44` | `features/pca_feature.py` (points, bounds and axis texts in `AnalysisData.pca`) |
| `network_tab.py` (1342) | `_thickness` `:80-85`, `_normalize_positions` `:92-124`, `_build_graph` `:127-172`, Dijkstra/Brandes `:175-272`, `compute_centrality` `:275-320`, info bar `:381-393`, layouts `:690-886`, drawing `:890-979`, ego `:1039-1165` | `utils/graph_utils.py`, `features/centrality_feature.py`, `utils/network_layout_utils.py`, `features/network_chart_data_feature.py` |
| `results_insights_tab.py` (1412) | Pure helpers and `compute_insights` `:290-664`; displayed card texts `:739-1084` (tags `:815-830`, overview `:858-907`, health `:909-951`, driver/dependent `:953-1011`, strongest link `:1013-1033`, contested `:1035-1056`, conflict ratio `:1058-1084`) | `features/insights_feature.py`, `features/insights_text_feature.py` |
| `aggregation_tab.py` (481) | `_score_bucket` `:82-86` | `features/aggregation_feature.py` (bands) |
| `llm_tab.py` (1005) | `ENGINES` `:61-77`, `SYSTEM_PROMPT` `:79-84`, `SECTION_HEADERS` `:86-94`, `build_prompt` `:101-196`, HTTP `:204-272`, header rule `:860-875`, TXT `:886-903`, PDF `:905-1005` | `features/explanation_prompt_feature.py`, `features/interpretation_pdf_feature.py`; providers reuse DEMATELab |
| `app.py` (3217) | `Project` `:179-190`, run flow `:2533-2611`, `_create_analysis_tabs` `:2613`, import flow `:2919-3036`, export `:3042-3217` | `features/analysis_feature.py`, `features/workbook_import_feature.py`, `features/xlsx_export_feature.py` |
| `aggregation_dialog.py` (800) | Method options `:60-81`, median options `:258-269`, weight validation `:558-613`, ties `:628-800` | `constants/aggregation_constants.py`, `features/weight_check_feature.py` |
| `dialogs.py` (1671) | Setup validation `:1080-1124` | `features/setup_validation_feature.py` |

Locked versions (`tk-app/uv.lock`, Python ≥ 3.12 branch): numpy 2.5.4, openpyxl 3.1.5 (et-xmlfile 2.0.0), reportlab
5.1.0, Pillow 13.0.0. The legacy app has no matplotlib, and neither does the API (Settled Decision 7).

Verified facts this plan depends on:

- `compute_*` and `build_prompt` run headlessly when Tk is importable, with no display. The uv-managed Python 3.13.2
  ships Tk 8.6 (logic report, Method).
- Importing `app` imports Pillow and Tk but opens no window. The generator must not import `main` or `font_loader`.
- The bundled example has one sheet, 14 policies named `P1`…`P14`, and no blanks.

## API Contract

All JSON responses use DEMATELab's `ApiResponseModel[T]` (`success`, `message`, `data`, `metadata.timestamp`, `error`).
File and image responses are raw. Errors follow these rules:

- `ErrorInfo(code, fields)`, with Pydantic validation errors as 422 `validation_error` and field paths;
- feature errors are `AppError` subclasses whose `data` may carry `{title, …}`, where `title` is the legacy message-box
  title;
- unknown errors are 500 `internal_error`;
- no response ever contains a stack trace, a request body or an API key.

### Shared request models

```text
DecisionMakerInput
  name: str                      trimmed; non-empty
  ratings: list[list[str]]       n×n; each cell "" (blank) or an exact canonical label
                                 (Indivisible|Reinforcing|Enabling|Neutral|Constraining|Counteracting|Cancelling);
                                 diagonal ignored and forced to "Neutral"

ProjectInput
  project_name: str              trimmed; non-empty ("Please enter a project name.")
  policies: list[str]            2..100; trimmed; non-empty; unique case-sensitive (legacy messages)
  decision_makers: list[DecisionMakerInput]   1..50; names unique case-sensitive (legacy messages)

TieChoice    { row: int, col: int, rating: str }          0-based indices into policies

AggregationSettings
  method: "average" | "median" | "majority" | "weighted"   default "average"
  weights: list[float] | null       weighted only; one per DM, in DM order
  median_choice: "lower" | "upper" | null                   used only for median with an even DM count; default "lower"
  tie_choices: list[TieChoice] = []                          majority only; choices for non-tied cells are ignored

AnalysisRequest = ProjectInput + { aggregation: AggregationSettings }
```

Validation order: project name → DM required → DM unique → limits (`max_decision_makers`, `max_policies`) → ≥ 2
policies → policies unique → control characters → matrix shape (`Ratings for "{dm}" must be {n} x {n}.`) → labels
(`Unrecognised rating "{value}" for "{dm}" at {Pi} → {Pj}.`). The setup, count and label messages are the legacy ones;
the shape and label messages are new, because the API receives JSON.

### Endpoints (prefix `/api/v1`)

| Method + path | Body / query | Returns |
| --- | --- | --- |
| `GET /health` | – | `HealthCheckData{status: "healthy", services: {api: "up"}}` |
| `GET /is-alive` | – | `AliveData{status: "alive"}` (Docker healthcheck) |
| `GET /scales` | – | `ScalesData` (below): rating scale and colours, methods with labels and descriptions, median choices, rules and limits, band palettes, entropy categories, network layouts and colours, network layout canvas, import limits |
| `POST /setup/validate` | `{project_name?, decision_makers?: list[str], policies?: list[str], existing_decision_makers?: list[str]}` | `{project_name, decision_makers, policies, codes}`. Empty entries are dropped (legacy ignores empty rows) and names are trimmed. Only the parts present are validated, in legacy order. A failure is 422 `invalid_setup` with the legacy message and `data{title, field}`. |
| `POST /matrices/check` | `ProjectInput` (blanks allowed) | `MatrixCheckData`: `{complete, decision_makers: [{name, filled, total, complete, blank_count, blank_cells: [{row, col, code_row, code_col}]}], incomplete_message, aggregation_options}`. `blank_cells` holds at most the first 10 blanks in row-major order; `blank_count` is the full count. `incomplete_message` is the legacy text (L11 arrow) or `null`; `aggregation_options{decision_maker_count, method_choice_available, forced_method, median_choice_applies}`. |
| `POST /weights/check` | `{decision_makers: list[str], weights: list[str \| null]}` (raw text inputs) | `{total, sum_text, within_tolerance, valid, weights: list[float \| null], errors: [{index, decision_maker, title, message}], first_error}`. `sum_text` is `Sum: {round(total,4)}` or `Sum: —` when any input fails to parse, as `_update_sum` does (`aggregation_dialog.py:558-568`). `within_tolerance` is `abs(total - 1.0) <= 0.01` on the unrounded sum of the non-empty inputs (`false` when parsing fails). Errors follow the dialog order: missing → invalid → out of range per DM, then the sum (L2 text), which is added only when every DM weight is valid. Always 200. |
| `POST /aggregation/preview` | `AnalysisRequest` (ties may be unresolved) | `AggregationData` (below) with `scores` containing `null` for unresolved ties and `ready = false` until every tie has a valid choice |
| `POST /analysis` | `AnalysisRequest` | `AnalysisData` (below) |
| `POST /analysis/export/xlsx` | `AnalysisRequest` | XLSX download `{project}_coherence.xlsx` (L10) |
| `POST /analysis/charts/network?layout=force_directed\|circular\|spectral\|shell&focus=<index>` | `AnalysisRequest` | `NetworkChartData` (JSON, below). Defaults: `force_directed`, full network. `focus` is a 0-based policy index; out of range is 422 `invalid_focus_policy`. One request per layout/focus, because the ego view lays out only the ego subgraph (`network_tab.py:1052-1066`). |

PCA needs no extra endpoint: `AnalysisData.pca` already holds everything the scatter draws.
| `POST /imports/workbook` | multipart: `file`; optional repeated `policies`; optional repeated `decision_makers` | `ImportData` (below) |
| `GET /explanations/providers` | – | DEMATELab's `ExplanationProvidersData` |
| `POST /explanations` | `{analysis: AnalysisRequest, provider, api_key, model?, azure_endpoint?}` | `{text, provider, model}` |
| `POST /explanations/export/pdf` | `{text: str}` (1..200 000 characters; empty → 422 `empty_interpretation`, `Generate an interpretation first.`) | `application/pdf` download `policy_interpretation.pdf` |

### Response models

`ScalesData`:

- `ratings`: `[{label, score, fill, text}]` in legacy order, with `diagonal_label: "Neutral"`.
- `methods`: `[{key, label, description}]`, using the L1 labels and the legacy descriptions with the L2 text.
- `median_choices`: `[{key: "lower", label: "Lower Median", description}, {key: "upper", label: "Upper Median", description}]`.
- `rules`:

  ```text
  {min_policies: 2, max_policies: 100, min_decision_makers: 1, max_decision_makers: 50,
   method_choice_min_decision_makers: 3, forced_method: "average", default_method: "average",
   default_median_choice: "lower", weight_min: 0.0, weight_max: 1.0, weight_sum_target: 1.0,
   weight_sum_tolerance: 0.01}
  ```

- `count_bands`: `[{key, min_ratio, fill, text}]` for `very_high ≥0.75`, `high ≥0.5`, `medium ≥0.25`, `low`, and
  `none` (n ≤ 1).
- `value_bands`: `[{key, fill, text}]` for `strong_positive (>1.5)`, `positive (>0.5)`, `weak_positive (>0)`, `zero`,
  `weak_negative (≥-0.5)`, `negative (≥-1.5)`, `strong_negative`.
- `entropy_categories`: `[{label, threshold_text, fill, text}]` with the legacy `H < 25% of max`, ….
- `network`: `{layouts: [{key: "circular", label: "Circular"}, {key: "force_directed", label: "Force-Directed"},
  {key: "spectral", label: "Spectral"}, {key: "shell", label: "Shell"}]` (this order, `network_tab.py:64`),
  `default_layout: "force_directed", positive_colour: "#1a6e3c", negative_colour: "#b71c1c",
  isolated_colour: "#aaaaaa", node_colour: "#2c4a6e", focus_colour: "#5a7fa8", node_text_colour: "#ffffff",
  layout_canvas: [600, 600]}`.
- `pca`: `{point_colour: "#2c4a6e", axis_colour: "#cccccc"}` (entropy category colours come from `entropy_categories`).
- `texts`: `{most_contested_value_label: "Rating agreement"}` (L12).
- `imports`: `{accept: [".xlsx"], max_bytes: 5242880}`.

`AggregationData`:

```text
requested_method, method, method_label, method_forced: bool, decision_maker_count, decision_makers: list[str],
policies, codes, weights: list[float] | null, median_choice: "lower"|"upper"|null (= legacy median_even_choice),
scores: list[list[float | null]]       n×n; diagonal 0.0; Average/Weighted rounded to 2 dp as legacy
bands: list[list[str]]                 rating label from _score_bucket; diagonal and null → "Neutral"
ordinal_cells: list[list[list[str]]] | null      median only (1 label for odd, [lower, upper] for even)
ties: [{row, col, code_row, code_col, policy_row, policy_col,
        tied_options: [{label, score}],              legacy order (score descending)
        votes: [{decision_maker, rating}],           per DM, for the tie step (new data, no new maths)
        chosen: str | null}]
ready: bool
```

`AnalysisData` (every float exactly as legacy computes it):

```text
project_name, aggregation: AggregationData (ready = true, no nulls)
coherence_scores: [{code, policy, oi, ii, woi, wii, oi_band, ii_band, woi_band, wii_band}]          index order
range_of_influence: {hmax, rows: [{code, policy, entropy, category}]}       hmax = round(hmax, 4) as legacy rows
pca: {valid, explained: [pc1, pc2], total_explained = round(pc1 + pc2, 1),
      points: [{index, code, policy, label, x, y, entropy_category}],          label "{code}:  {policy}"
      bounds: {x_min, x_max, y_min, y_max} | null,                              legacy pca_tab.py:436-442 (range `or 1.0`)
      x_axis_label "PC1 ({p1}%)", y_axis_label "PC2 ({p2}%)", stats_text "PC1: {p1}%   PC2: {p2}%   Total explained: {t}%",
      message: "PCA requires at least 3 policies." | null}                    invalid → points [], bounds/labels null
network: {node_count, edge_count, density, isolated_count, stats_text,      legacy info bar network_tab.py:381-393
          edges: [{source, target, score, sign: "positive"|"negative", width, two_way}],   row-major, nonzero off-diagonal
          centrality: [{code, policy, betweenness, closeness}] (index order), centrality_ranking: list[code]}
insights: InsightsData
```

`InsightsData` holds only what the legacy tab displays, plus the per-policy fields the story colouring needs:

```text
rows: [{code, policy, oi, ii, woi, wii, net, prominence, entropy, entropy_category, betweenness, closeness,
        role: "driver"|"dependent"|"balanced"}]
graph: {positive_edges, negative_edges, zero_edges, density, polarity, strongest_pos, strongest_neg,
        strongest_pos_pair: [i, j] | null, strongest_neg_pair: [i, j] | null}
agreement: {average_agreement, average_correlation, contested: [{i, j, pair, score, agreement_ratio, spread}] (≤ 5)}
health: {score, synergy, conflict, neutral_uncertain}                       integers
texts:
  story                       _build_story_banner (exact)
  interpretation_label        "Interpretation:"
  interpretation_text         _build_supporting_interpretation without the prefix (exact)
  overview_agreement_text     f"{average_agreement:.2f}"
  tag_top_driver              "Top Driving Policy: {policy (code)}" | "Top Driving Policy: N/A"
  tag_strongest_link          "Strongest Link: {pair with →}" | "Strongest Link: No non-zero relation"
  tag_contested               "Contested: {pair with →}" | "Contested: None"
  top_driver   {hero, value_text}      hero "{policy} ({code})" | "N/A"; value "{woi:+.2f} WOI" | "N/A"
  top_dependent {hero, value_text}     value "{wii:+.2f} WII"
  strongest_link {main (pair with →), value_text "{s:+.2f} positive link" | "No strong link" (L13),
                  caption: "Strongest relation"}
  most_contested {main (pair with ↔, the only ↔ in the API), value_text "Rating agreement: {r:.2f}" | "Stable" (L12),
                  caption}
  conflict_ratio {ratio, main_text f"{ratio*100:.0f}%", value_text "{neg} of {active} active links", caption}
```

`NetworkChartData` (`POST /analysis/charts/network`; everything the ECharts `graph` series needs, no browser maths):

```text
layout, layout_label, focus: int | null, canvas: {width: 600, height: 600}     logical px, y grows downwards (legacy)
title: "Ego Network:  {code}  ({policy})" | null                             ego view only
empty_message: "{code} has no direct connections." | null                   ego view with no edges (L8)
nodes: [{index, code, policy, label, x, y, isolated, is_focus, radius, fill}] radius 18 (focus 22); fill node/isolated/focus colour
edges: [{source, target, score, sign, colour, width, two_way, label}]        label f"{score:+.2f}" in the ego view, else null
stats: {node_count, edge_count, density, isolated_count, text}               full-network values, as the legacy info bar
```

Nodes and edges are in legacy order (`_redraw_network` `:903-907`, `_redraw_ego` `:1052-1064`); `width` is `_thickness`
(4 / 2.5 / 1 px); `colour` is the positive or negative colour by sign. Coordinates equal the layout fixtures.

Display rule: the API returns numbers already rounded as the legacy app rounds them. It also returns text wherever the
legacy display precision is lower than the stored precision (agreement `.2f`, contested ratio `.2f`, conflict ratio
`.0f`), or where the text comes from a template. The frontend plan must format the remaining numbers like Python's
`format` at the same precision, including `-0.00` for `-0.0` and `+` signs for `+.2f`. It must never re-round.

`ImportData`:

```text
policies, codes, matrices: [{decision_maker, ratings}]     ratings n×n with "Neutral" diagonal and "" for blanks
warning_groups: [{kind: "skipped"|"blank_cells", heading, messages: list[str]}]     verbatim legacy messages (L4)
imported_count, summary_message                           "{k} matrix/matrices imported successfully." | "{k} matrix/matrices imported."
suggested_project_name                                    stem of the uploaded file name (legacy names new projects so)
```

Import errors (422 unless stated):

| Code | Message |
| --- | --- |
| `upload_too_large` (413) | `The workbook is larger than 5 MB.` |
| `unsupported_file` | `Only .xlsx workbooks are supported.` |
| `invalid_workbook` | `The file could not be read as an Excel workbook (.xlsx).` (also for chartsheets, zip-bomb entries and any other openpyxl/zip/XML exception) |
| `invalid_import` (sheets) | `The workbook has more than 50 sheets.` (checked before any sheet is parsed) |
| `invalid_import` | Legacy header-mismatch and unrecognised-rating messages verbatim. New messages: `Sheet "{sheet}": Policy names must be unique.` and `Sheet "{sheet}": header row has a blank policy name in column {letter}.` |
| `nothing_imported` | `No valid matrices were found in the workbook.`, with `data.warning_groups` |
| `policy_list_mismatch` | Legacy message (`app.py:2970-2975`) |
| `existing_decision_makers` | `These decision-maker names already exist in the project:\n\n{sorted names}` |
| `invalid_import` (limits) | `Please enter at most 100 policy names.` / `Please enter at most 50 decision-makers.` (the same texts as the request limits) |

Analysis errors: `incomplete_matrices` (legacy message with L11, `data.title = "Incomplete Matrices"`),
`invalid_weights`, `unresolved_tie` (`Please select a rating for cell {Pi} → {Pj}.`), `invalid_tie_choice`
(`"{rating}" is not one of the tied ratings for cell {Pi} → {Pj}.`, or the duplicate-choice message),
`invalid_focus_policy`.

Explanation errors: DEMATELab's `llm_errors.py`, with L9.

Limits:

- uploads are 5 MB, enforced while streaming (Phase 5.1);
- Nginx `client_max_body_size 20m`, because a 100-policy × 50-DM JSON request is about 7–8 MB;
- CPU-bound work runs through `asyncio.to_thread`.

## Target Layout

```text
apps/api/
  main.py  pyproject.toml  uv.lock  .python-version  .env.example  .dockerignore
  Dockerfile.dev  Dockerfile.prod  README.md  AGENTS.md  CLAUDE.md
  api/v1/api.py
  config/settings_config.py (+ test)
  constants/  app_constants.py  rating_constants.py  aggregation_constants.py  band_constants.py
              entropy_constants.py  insights_constants.py  chart_constants.py  import_constants.py
              export_constants.py  llm_constants.py
  models/     response_model.py  error_models.py  health_models.py  scale_models.py  setup_models.py
              project_models.py  analysis_request_models.py (+ test)  aggregation_models.py  check_models.py
              analysis_result_models.py  insights_models.py  chart_models.py  import_models.py
              explanation_models.py
  errors/     app_error.py  error_handlers.py (+ test)  error_presenter.py  health_errors.py  setup_errors.py
              analysis_errors.py  import_errors.py  llm_errors.py
  utils/      response_utils.py  matrix_utils.py  aggregation_label_utils.py  graph_utils.py
              network_layout_utils.py  excel_import_utils.py  excel_style_utils.py  sheet_title_utils.py
              filename_utils.py                                           (each + _test.py)
  features/   health_feature  scales_feature  setup_validation_feature  matrix_check_feature  weight_check_feature
              aggregation_feature  aggregation_flow_feature  coherence_scores_feature  entropy_feature  pca_feature
              centrality_feature  insights_feature  insights_text_feature  analysis_feature  network_chart_data_feature
              workbook_import_feature  xlsx_export_feature
              explanation_prompt_feature  explanation_feature  explanation_providers_feature
              interpretation_pdf_feature                                 (each .py + _test.py)
  services/   llm_provider_service.py  gemini_service.py                (each + _test.py)
  middleware/ cache_control_middleware.py (+ test)
  routers/    health  scales  setup  matrices  weights  aggregation  analysis  analysis_export  analysis_charts
              imports  explanations                                      (each .py + _test.py)
  tests/      __init__.py  parity_fixtures.py  parity_integration_test.py  insights_text_parity_integration_test.py
              prompt_parity_integration_test.py  layout_parity_integration_test.py  import_parity_integration_test.py
              xlsx_integration_test.py  repository_rules_integration_test.py
              fixtures/{parity,layouts,imports,xlsx}/
scripts/generate_parity_fixtures.py      repo root entry point; runs against tk-app/; never imported by apps/
scripts/parity/  __init__.py  cases.py  aggregation_capture.py  analysis_capture.py  text_capture.py
                 layout_capture.py  import_capture.py  xlsx_capture.py  errors_capture.py  io_utils.py
                 (each ≤ 300 lines; Ruff-checked, see Phase 2)
nginx/Dockerfile.prod  nginx/nginx.prod.conf
docker-compose-dev.yml  docker-compose-prod.yml  Makefile                       repo root
docs/decisions/2026-11-18-*.md                                                   Phase 9
```

Each `*_feature.py` and `*_service.py` holds one class and ends with a shared instance. Files approaching 300 lines are
split by responsibility, never by moving logic into routers. For example, `insights_text_feature.py` can be split into
story/interpretation and card texts.

## Phases

Order: 1 → 2 → 3 → 4 → **Linux parity gate** → (5, 6, 7 independent) → 8 → 9. Each phase writes its own tests.
Phase 9 is the completeness pass. Before Phase 1, record the legacy baseline (all three values must be identical at the
end):

```bash
git diff -- tk-app | shasum
git status --porcelain -- tk-app | shasum
git ls-files -z -co --exclude-standard tk-app | sort -z | xargs -0 shasum | shasum   # content hash; safe with spaces
```

### Phase 1: API skeleton (copied from DEMATELab)

1. `apps/api/pyproject.toml` (`name = "policycoherencekit-api"`, `description = "Policy Coherence Kit API"`,
   `requires-python = ">=3.13"`).
   - Runtime dependencies: `fastapi[standard]>=0.115.12`, `pydantic>=2.11.5`, `pydantic-settings>=2.6.0`,
     `python-dotenv>=1.1.0`, `gunicorn>=22.0.0`, `uvicorn-worker>=0.3.0`, `httpx==0.28.1`, `numpy==2.5.4`,
     `openpyxl==3.1.5`, `reportlab==5.1.0`, `pillow==13.0.0` (reportlab needs it), `google-genai==3.0.0`,
     `defusedxml` (openpyxl uses it automatically for XML parsing when installed; pin the version `uv lock` resolves).
   - Dev group: `ruff`, `pytest`, `pytest-cov`, `pytest-asyncio`.
   - Copy DEMATELab's `[tool.uv]`, `[tool.ruff]`, `[tool.pytest.ini_options]` and `[tool.coverage.*]` sections verbatim.
   - Add `.python-version` = `3.13` and `!apps/api/.python-version` in the root `.gitignore`.
   - Run `uv lock`. If the pins cannot co-resolve, stop and report; never unpin numpy or openpyxl.
2. Copy verbatim from `dematelab/apps/api`, changing only names and docstrings:
   - `models/{response_model,error_models,health_models}.py`;
   - `errors/{app_error,error_handlers,error_presenter,health_errors}.py` and `error_handlers_test.py`;
   - `utils/response_utils.py` and its test;
   - `middleware/cache_control_middleware.py` and its test;
   - `config/settings_config.py` and its test (default `cors_origins = "http://localhost:3001"`);
   - `features/health_feature.py` and `routers/health.py` with their tests;
   - not `utils/font_utils.py`, `utils/figure_utils.py` or any chart renderer (no matplotlib, Settled Decision 7);
   - `tests/__init__.py`.
3. Adapt:
   - `main.py`: DEMATELab's, without `matplotlib.use("Agg")` and without font registration.
   - `constants/app_constants.py`: `PORT = 50002`; `PROJECT_DETAILS` name `Policy Coherence Kit API`, version `0.1.0`;
     DEMATELab's `PROJECT_SETTINGS` and `CACHE_CONTROL_SETTINGS`; no `PROJECT_PATHS["FONTS_DIR"]`.
   - `api/v1/api.py`: health only for now.
4. `utils/response_utils.py`: `download_bytes` gains the RFC 5987 `filename*` (L10). `utils/filename_utils.py` builds the
   ASCII fallback and the encoded name.
5. No fonts are copied into `apps/api` (charts are drawn in the browser; the PDF uses reportlab's built-in fonts as
   legacy does).
6. Add the remaining files:
   - `.env.example`: `APP_ENV=development`, `CORS_ORIGINS=http://localhost:3001`, `WEB_CONCURRENCY=2`;
   - `.dockerignore`: DEMATELab's verbatim;
   - `CLAUDE.md`: `@AGENTS.md`;
   - placeholder `AGENTS.md` and `README.md`, which Phase 9 completes.
7. Copy `dematelab/apps/api/Dockerfile.dev` now (adapted as Phase 8.1 describes: `python:3.13-slim`, port 50002), so
   the Linux parity gate after Phase 4 can build it with `docker build -f apps/api/Dockerfile.dev apps/api` before
   Compose exists. Phase 8 only finishes it and adds `Dockerfile.prod`.

Done when `cd apps/api && uv run python main.py` serves `/api/docs`, `/api/v1/health` and `/api/v1/is-alive`, and
`uv run ruff format --check . && uv run ruff check . && uv run pytest` passes.

### Phase 2: Parity fixtures (before porting any maths)

1. Create `scripts/generate_parity_fixtures.py` at the repository root. Run it from the root with
   `uv run --frozen --python 3.13 --project tk-app python scripts/generate_parity_fixtures.py`.
   - The module docstring states this command.
   - The first statements are `sys.dont_write_bytecode = True`, then
     `sys.path.insert(0, str(REPO_ROOT / "tk-app"))`.
   - It imports `aggregator`, `importer`, `models`, `constants`, `coherence_scores_tab`, `range_of_influence_tab`,
     `pca_tab`, `network_tab`, `results_insights_tab`, `aggregation_tab`, `llm_tab` and `app` (for `_export_to_excel`).
   - It never imports `main` or `font_loader`, never creates `tk.Tk()`, and never imports anything from `apps/`.
   - It may create the gitignored `tk-app/.venv`. Nothing else under `tk-app/` may change.
   - If `import tkinter` fails, stop and report.
   - **Scope of `scripts/`:** the entry point stays thin and imports helper modules from `scripts/parity/` (Target
     Layout). Every file under `scripts/` is ≤ 300 lines (`wc -l scripts/*.py scripts/parity/*.py`) and passes, from
     the repository root after Phase 1:
     `uv run --project apps/api ruff check --config apps/api/pyproject.toml scripts` and
     `uv run --project apps/api ruff format --check --config apps/api/pyproject.toml scripts`.
     The Phase 9 repository-rules test does not cover `scripts/`; these commands are part of Phase 2's done criteria.
2. The generator **captures** legacy texts by running the legacy code paths, instead of re-typing f-strings:
   - It creates `app_obj = app.PolicyCoherenceApp.__new__(app.PolicyCoherenceApp)` with a stub `root` whose
     `wait_window` is a no-op, a `Project` holding the case's `PolicyMatrix` list, and patches:
     - `messagebox.showwarning` / `showerror` (in `app`, `aggregation_dialog`, `dialogs`) to record `(title, message)`;
     - `AggregationMethodDialog`, `WeightDialog`, `MedianChoiceDialog` and `TieResolutionDialog` in `app`'s namespace
       with fakes whose `.result` is preset from the case (the tie fake writes each `TiedCell.chosen` and returns the
       ties as `.result`);
     - `_create_analysis_tabs` to capture `(project, result)` and `_set_status` to capture the status text.
   - It calls `app_obj._run_aggregation()` (`app.py:2533-2611`), so forced Average, the median choice, the incomplete
     message and `resolve_ties` all come from legacy code. A **fresh** `AggregationResult` exists per variant, because
     `_cached_*` is never invalidated.
   - Card texts: it builds `ResultsInsightsTab.__new__`, sets `_result` and `_insights`, patches `_signal_card` (and
     `_metric_signal_card`) to return their positional and keyword arguments, and calls the `_top_driver_card`,
     `_top_dependent_card`, `_strongest_link_card`, `_most_contested_card` and `_conflict_ratio_card` builders.
     `_format_pair`, `_format_policy` and the story/interpretation helpers are called directly.
   - Only the tag and hero texts that legacy builds inline in direct `tk.Label(...)` calls
     (`results_insights_tab.py:815-835, 876-890`) are hand-copied, each with a file:line comment; a reviewer checks them
     before Phase 4.
   - Weight-dialog and tie-dialog messages are captured the same way: `WeightDialog.__new__` / `TieResolutionDialog.__new__`
     with `_vars` stubs (objects with `.get()`), `_entries` stubs with `focus_set()`, `_ties`, and the recorded
     `messagebox` patch, then `_on_ok()`.
3. Cases. Seeds are fixed, and every input matrix is stored in the fixture:

   | Case | Policies × DMs | Variants | Purpose |
   | --- | --- | --- | --- |
   | `example` (`data/examples/WEF Nexus Example.xlsx` via the legacy importer) | 14 × 1 | `average`, plus `requested_median` (forced to average) | Real data |
   | `r5x3` (seed 51) | 5 × 3 | `average`, `median`, `majority_first`, `majority_last`, `majority_middle`, `weighted_a` `[0.2, 0.3, 0.5]` | Core; a policy name contains `$5bn and $3bn` (literal `$` in labels and texts) |
   | `r6x4` (seed 64) | 6 × 4 | `median_lower`, `median_upper`, `majority_first`, `majority_last`, `average`, `weighted_equal` `[0.25]*4`, `weighted_b` `[0.1, 0.2, 0.3, 0.4]` | Even-count rules |
   | `r8x8` (seed 88) | 8 × 8 | `average`, `weighted_c` `[0.125]*8`, `weighted_d` (8 seeded weights rounded to 3 dp, last = 1 − sum of the others) | Half-to-even rounding |
   | `neutral3x3` | 3 × 3, all Neutral | all methods | Zero variance, entropy 0, centrality 0, agreement 1.0 |
   | `onelink3x1` | 3 × 1, one non-zero link | `average` | `entropy == -0.0`, isolated nodes, closeness 0 |
   | `two2x3` | 2 × 3 | all methods | `hmax = 1.0`, PCA invalid, betweenness normaliser 1 |
   | `two2x1` | 2 × 1, \|s\| = 3 | `average` | Closeness 3.0 |
   | `negative6x3` (seed 63, negative labels only) | 6 × 3 | all methods | Negative edges, negative-link tone (L13), conflict |
   | `paths7x4` (hand-designed equal-length paths with scores ±1/±2) | 7 × 4 | `average` | Brandes multi-path counting and the `1e-9` tolerance |
   | `identical5x3` | 5 × 3, three identical DMs | all methods | Spearman zero variance → 1.0; contested order by index |
   | `weighted_negzero` (one cell rated Constraining/Neutral/Neutral with weights `[0.004, 0.498, 0.498]`, so `round(-0.004, 2) == -0.0`) | 3 × 3 | `weighted` | Weighted `-0.0` (Python's `sum` starts at int 0, so `-0.0` arises only from rounding a small negative value) |
   | `r30x5` (seed 305) | 30 × 5 | `average`, `majority_first` | Larger graph and timing |

   "All methods" means `average`, `median`, `majority_first` and `weighted` with equal weights where the DM count allows
   it; with 2 DMs the requested methods are recorded as forced to average. `majority_first`, `_last` and `_middle` choose
   the entry at index `0`, `len - 1` or `len // 2` of `tied_labels` (so with two tied labels, `middle` is index 1, the
   same as `last`; the generator asserts the chosen label is in `tied_labels`).
4. Error fixtures (`fixtures/parity/errors__<name>.json`) store the exact legacy message captured from the code path that
   the user would see (step 2's patched `messagebox`). Each fixture records `source` and `api_message_rule`:
   - Setup validation: all six `dialogs.py:1080-1124` messages (project name required, DMs required, duplicate DMs,
     existing DMs, too few policies, duplicate policies), captured by calling `ProjectSetupDialog._on_ok`
     (`dialogs.py:1080`) on a `__new__`-built dialog whose attributes read by `_on_ok` are stubs (`.get()` values,
     `focus_set()` no-ops) and with `destroy` patched out. The rule is "identical"; `Duplicate Project` is stored as
     documentation (one project).
   - Weight range and sum errors store the **weight-dialog** text, captured from `aggregation_dialog.py:570-613`.
     The rule is "identical, except L2 for the sum".
     - Weights: `[0.3]*3` (sum 0.9), `[0.34, 0.34, 0.33]` and `[0.33, 0.33, 0.33]` (both just outside ±0.01),
       `[1.2, -0.1, -0.1]`.
     - `[0.335]*3` is accepted, so it is a normal variant, not an error fixture.
     - The aggregator text (`aggregator.py:351-363`) is stored too, as documentation.
   - `/weights/check` raw inputs `""`, `"abc"`, `"1.5"` and `"nan"`: the dialog texts. The rule is "identical".
   - Wrong weight count: `aggregator.py` text `Expected {n} weights, got {k}.` The rule is "identical".
   - A blank cell: the completeness message captured from `app.py:2546-2556`, including the `(+k more)` suffix. The
     rule is "identical after L11".
   - An unresolved tie: the dialog text `Please select a rating for cell {Pi} -> {Pj}.`, captured from
     `aggregation_dialog.py:779-787`. The rule is "identical after L11". The `resolve_ties` text is stored as
     documentation.
   - An invalid median choice, an empty matrix list and a policy mismatch are recorded as documentation only. In the API
     these inputs are rejected structurally (enum, `min_length`, single `policies` list) with Pydantic 422 or the setup
     messages.
5. Each analysis fixture is written to `apps/api/tests/fixtures/parity/<case>__<variant>.json` and contains:
   - `request`: the API `AnalysisRequest` JSON;
   - `aggregation`: every `AggregationResult` field (scores n×n with null, ties with `chosen`, `source_scores`,
     `ordinal_cells`, `median_even_choice`, `method`, and the `aggregation_method_label(result)` label), plus
     `requested_method`;
   - `bands`: `_score_bucket` per cell;
   - `scores` with `_value_color` and `_count_color` per row;
   - `entropy`;
   - `pca` (`coords`, `explained`, `valid`, and `singular_values` from the same `np.linalg.svd` call, captured by
     wrapping `np.linalg.svd` during `compute_pca`);
   - `graph_edges`;
   - `centrality`, plus `centrality_ranking` (sorted by betweenness, reverse, stable);
   - `network_info`: density and isolated count, replicated from `network_tab.py:381-388`;
   - `insights`: the full `compute_insights` JSON;
   - `texts` (raw legacy output, before L11–L14):
     - `_build_story_banner`;
     - `_build_supporting_interpretation`;
     - `_build_system_health`;
     - `_strongest_link(result, top_driver.index)`;
     - the card texts captured through the patched `_signal_card` (step 2), and the hand-copied tag/hero texts;
     - the status text captured from `_set_status`;
   - `prompt`: `llm_tab.build_prompt(result)`;
   - `env`: Python version, numpy version, `platform.platform()`, and the BLAS name from
     `numpy.show_config(mode="dicts")`.

   Error fixtures store `error_message`.
6. Layout fixtures go to `fixtures/layouts/<case>__<layout>__<focus>.json`.
   - Cases: `example`, `r6x4`, `negative6x3`, `two2x3`, `onelink3x1`.
   - Each case is run with all 4 layouts, for the full network and for focus 0.
   - Each fixture holds node positions on the square 600×600 layout canvas (Settled Decision 14), the same canvas
     the API uses.
   - The generator gets them by building `tab = network_tab.NetworkTab.__new__(network_tab.NetworkTab)`, setting
     `tab._result`, `tab._graph`, `tab._centrality` and a stub `tab._layout_var` with `get()`, and then calling
     `_compute_layout_positions`. The node and edge lists are built exactly as `_redraw_network` (`:903-907`) and
     `_redraw_ego` (`:1052-1064`) build them.
   - Spectral (L16): while computing spectral positions the generator replaces `network_tab.np.linalg.eigh` with a
     wrapper that calls the real `eigh` and flips each eigenvector column so its largest-magnitude entry is positive.
     The fixture records all eigenvalues and the two chosen indices. If the two chosen eigenvalues are within `1e-9`
     of each other (or of the next one), the eigenvectors are not unique: the fixture is marked
     `spectral_degenerate: true`, the test skips its position comparison, and `apps/api/AGENTS.md` lists the case.
7. Import fixtures. `apps/api/tests/fixtures/imports/<name>.xlsx`, each with a `.json` holding the legacy
   `ImportResult` (matrices and warnings) or the error message. The generator builds the workbooks with openpyxl:
   - case-insensitive labels with spaces;
   - `none`;
   - more than 10 blanks (the `+k more` suffix);
   - more than 10 bad values (`...`);
   - more than 5 header mismatches;
   - an empty sheet;
   - a header with fewer than 2 policies;
   - numeric headers;
   - numeric cells;
   - a gap column;
   - junk on the diagonal;
   - multiple sheets with one bad sheet;
   - two sheets with different policy lists;
   - duplicate policy names;
   - a copy of the example workbook (`wef_nexus_example.xlsx`).

   For gap-column and duplicate-policy inputs the JSON records the legacy result together with an `api_expected_error`
   (Settled Decision 14).
8. XLSX fixtures. For `r6x4__median_lower`, `r5x3__majority_first`, `example__average` and a `dm_names` case (DMs named
   `A/B`, `Aggregated (Average)`, a 40-character name and two names equal after cutting), run
   `app._export_to_excel(matrices, [result], path)`. Legacy crashes on `A/B`, so that case records `error_message` and
   the API expectation is defined by L3 alone. Save the legacy `.xlsx` and a `.json` dump of every sheet holding:
   - the title;
   - each cell's value, bold flag, fill colour, font colour and number format;
   - the column widths.
9. The script prints the fixture counts. Commit the script and the fixtures together (the owner commits).

Done when every case and variant has a fixture, every import and XLSX fixture has an expected output, the `scripts/`
Ruff and 300-line checks pass, and the three baseline hashes are unchanged.

### Phase 3: Constants, models, utils

1. `constants/rating_constants.py`: `RATING_LABELS` (ordered), `RATING_SCORES`, `RATING_FILLS`, `RATING_TEXT_COLOURS`,
   `DIAGONAL_LABEL`, all verbatim from `constants.py:14-49, 92-100`.
2. `constants/aggregation_constants.py`:
   - `AggregationMethod` enum;
   - the method options (L1 labels, legacy descriptions, L2 text);
   - `MedianChoice` enum and its options (`aggregation_dialog.py:258-269`);
   - `METHOD_CHOICE_MIN_DMS = 3`;
   - the weight limits and tolerance;
   - the policy and DM limits;
   - every legacy and new message and title from the Business Rules table, the API Contract and L2.
3. `constants/band_constants.py`: the value, count and score bands with their legacy thresholds and colours
   (`coherence_scores_tab.py:73-100`, `aggregation_tab.py:59-67`).
4. `constants/entropy_constants.py`: the categories, their order, colours (`range_of_influence_tab.py:55-62`) and
   threshold texts.
5. `constants/insights_constants.py`: the 0.05 net cut-off, the 0.75 and 0.5 agreement cut-offs, the conflict captions
   and the card captions and labels.
6. `constants/chart_constants.py`:
   - `NETWORK_LAYOUT_CANVAS = (600, 600)`, layout margin 80;
   - network: node radius 18, colours `:56-62`, `NetworkLayout` enum with legacy labels and order;
   - PCA: point colour `#2c4a6e`, axis colour `#cccccc`;
   - ego: colour `#5a7fa8` at radius 22;
   - text templates: ego title, empty message (L8), stats line, PCA axis labels and stats line, hover label.
   No dpi, canvas-border, `PX_TO_PT` or PNG constants.
7. `constants/import_constants.py` (5 MB, `.xlsx`, messages, L4 headings) and `constants/export_constants.py` (header
   fill `2C4A6E`, border `CCCCCC`, `XLSX_MEDIA_TYPE`, `PDF_MEDIA_TYPE`, filenames, sheet title templates).
8. Models implement the API Contract. Request validators live in `models/analysis_request_models.py`, delegating name
   checks to `features/setup_validation_feature.py` so that the messages have one source. Matrices are nested lists in
   models. `utils/matrix_utils.py` converts between `(i, j)` dicts and lists, and builds `generate_codes` (`P1…Pn`).
   `models/aggregation_models.py` holds the internal dataclasses `TiedCell` and `AggregationResult` with the legacy
   fields (no caches).
9. `utils/aggregation_label_utils.py`: `aggregation_method_label` verbatim, plus `sheet_label()` (L3).
   `utils/sheet_title_utils.py` implements L3. `utils/excel_style_utils.py` ports `hcell` and `auto_width` from
   `app.py:3097-3110`.

### Phase 4: Aggregation and analysis features

1. `features/aggregation_feature.py`: port `aggregate_average`, `_majority`, `_median`, `_weighted`, `resolve_ties`
   and `_validate_*` verbatim (`aggregator.py:126-370`). Keep these exactly:
   - integer sums before dividing;
   - generator `sum`;
   - `Counter` insertion order;
   - stable sorts.

   Also port `_score_bucket` for the bands. Validation keeps the legacy checks and their order (count, then range, then
   `abs(round(sum, 10) - 1.0) > 0.01`), but the user-facing texts are the weight dialog's, because users see those:
   - range: `Weight for "{dm}" must be between 0.0 and 1.0.`;
   - sum: the L2 text, with `data.title = "Weights Do Not Sum to 1"`;
   - count: the aggregator's `Expected {n} weights, got {k}.`

   An unresolved tie uses the dialog text with `data.title = "Unresolved Tie"`.
2. `features/matrix_check_feature.py`: `check_completeness` verbatim, the legacy incomplete message (`app.py:2546-2556`)
   and the `aggregation_options` (Business Rules table).
3. `features/weight_check_feature.py`: the dialog parsing and validation from `aggregation_dialog.py:558-613` (`float()`
   on the stripped text; the order is missing → invalid → range, then the sum), and `sum_text`.
4. `features/setup_validation_feature.py`: `dialogs.py:1080-1124` rules and messages, minus project-name uniqueness
   (one project), plus the limits.
5. `features/aggregation_flow_feature.py` takes an `AnalysisRequest` and returns an `AggregationResult`. Steps:
   1. completeness (422);
   2. effective method;
   3. weights or median choice;
   4. aggregate;
   5. apply valid tie choices (422 `invalid_tie_choice` for a rating outside the tied options or for two choices for
      the same cell);
   6. `require_resolved()` for the analysis endpoints.

   It is used by the preview, analysis, charts, export and explanation endpoints.
6. `features/coherence_scores_feature.py` (`coherence_scores_tab.py:107-142`), `features/entropy_feature.py`
   (`range_of_influence_tab.py:82-141`) and `features/pca_feature.py` (`pca_tab.py:65-121`, numpy, no sign
   normalisation) are ported verbatim, with band keys added.
7. `utils/graph_utils.py`: `_build_graph`, `_dijkstra_with_paths`, `_dijkstra_simple`, `_brandes_betweenness`
   (`network_tab.py:127-272`) verbatim, using heapq. Do not use networkx. `features/centrality_feature.py`:
   `compute_centrality` (`:275-320`), the info-bar stats (`:381-388`) and `centrality_ranking`.
8. `features/insights_feature.py`: `_build_graph_stats`, `_rank_values`, `_pearson_corr`,
   `_average_dm_spearman_agreement`, `_agreement_stats` and the displayed parts of `compute_insights`
   (`results_insights_tab.py:312-455, 607-664`), with `role` from `_role_for_row` (`:503-509`). The dead fields are
   omitted from the output, but their sorts must still not change the shown ones.
9. `features/insights_text_feature.py`: `_policy_label`, `_pair_label`, `_strongest_link`, `_build_story_banner`,
   `_build_system_health`, `_build_supporting_interpretation` (`:294-310, 512-604`), plus the card and tag texts
   (`:815-830, 880-890, 953-1084`) verbatim, with L11–L14 applied.
10. `features/analysis_feature.py`: request → aggregation flow → all analyses → `AnalysisData`. It runs in
    `asyncio.to_thread`.
11. `routers/analysis.py` (`POST /analysis`, one-statement handler) and its test, registered in `api/v1/api.py` now
    (moved here from Phase 7 so the done criterion below can run over HTTP).

Done when `tests/parity_integration_test.py` and `tests/insights_text_parity_integration_test.py` pass for every
fixture, at feature level and through `/analysis`.

### Linux parity gate (after Phase 4, before Phases 5–7)

Build the Phase 1 dev image and run the parity tests in Linux (`python:3.13-slim`, OpenBLAS):

```bash
docker build -f apps/api/Dockerfile.dev -t pck-api-parity apps/api
docker run --rm -v "$PWD/apps/api:/app:ro" -w /app pck-api-parity \
  python -m pytest -p no:cacheprovider tests/parity_integration_test.py tests/insights_text_parity_integration_test.py
```

(Use `podman` if that is the available engine.) Any non-degenerate difference above the tolerance stops the work and
is reported (Risks). Record the result before Phases 5–7 start.

### Phase 5: Import, export and chart data

1. `utils/excel_import_utils.py` and `features/workbook_import_feature.py`.
   - Hardening, before any legacy logic runs:
     - stream the upload in chunks and stop at 5 MB + 1 byte → 413 `upload_too_large` (never read the whole body
       first);
     - open the zip, reject any entry whose uncompressed size exceeds 50 MB or whose total exceeds 200 MB →
       `invalid_workbook`;
     - with `defusedxml` installed, call `load_workbook(BytesIO, read_only=True, data_only=True)`; reject more than 50
       sheets → `invalid_import` before parsing any sheet;
     - read at most `max_policies + 2` rows and columns per sheet (`iter_rows(max_row=…, max_col=…)`); a header row
       with more than `max_policies` policy names → `invalid_import` with the limit message;
     - map every other openpyxl, zip or XML exception (including chartsheets) to `invalid_workbook`.
   - Port `importer.py:39-192`: the sheet loop, header rules, `_match_rating` and the verbatim messages (L11 arrows).
   - Add the gap-column check and the duplicate-policy check (Settled Decision 14). The gap check comes after the
     "< 2 policies" skip and before the header-match check. The duplicate check comes after it.
   - Trim sheet names for DM names; a name that trims to empty or collides with another trimmed name → 422
     `invalid_import` (Business Rules table).
   - Then apply the limits, the policy-list check, the DM clash check and the nothing-imported check.
   - Order the warning groups as L4.
   - Size and extension checks come first.
2. `features/xlsx_export_feature.py` reproduces `app.py:3085-3217` for one result. It writes:
   - DM sheets with rating fills and font colours;
   - then `Aggregated`, `Coh Scores`, `Range Influence` and `Centrality` (sorted by betweenness, stable);
   - `number_format "0.00"` on aggregated values;
   - header styles and `auto_width`;
   - titles per L3;
   - every text cell as a string, never a formula (L15).

   Write to `BytesIO`. The router returns `download_bytes(..., filename, XLSX_MEDIA_TYPE)`.
3. `utils/network_layout_utils.py` ports `_normalize_positions`, `_circular_layout_positions`,
   `_undirected_strengths`, `_force_directed_layout_positions`, `_spectral_layout_positions` (numpy `eigh`) and
   `_shell_layout_positions` (`network_tab.py:92-124, 690-886`) verbatim, as functions taking `(node_ids, edges, width,
   height, centrality)`, with the L16 eigenvector sign rule as the only change. Callers pass
   `NETWORK_LAYOUT_CANVAS`.
4. `features/network_chart_data_feature.py` builds `NetworkChartData` (API Contract) from the aggregation flow, the
   ported centrality and `network_layout_utils`:
   - node and edge lists exactly as `_redraw_network` (`:903-907`) and `_redraw_ego` (`:1052-1064`) build them, in
     legacy order; `two_way` when the reverse nonzero edge exists; `sign`, `colour` and `width` (`_thickness`);
   - ego view: ego edges only, ego node first with `is_focus`, radius 22 and the focus colour, `label` `{s:+.2f}`,
     `title` and `empty_message` (L8);
   - `stats` from the full network (legacy info bar), `focus` validation (422 `invalid_focus_policy`).
   `features/pca_feature.py` adds `label`, `bounds`, axis labels and `stats_text` to `AnalysisData.pca`.
5. No chart-rendering, PCA-chart or hotspot features exist (Settled Decision 7). The legacy pixel rules (arrowheads
   12 px × 4 px half-width, node radius 18 / ego 22, 1.5 px white outline, white bold code labels, PCA point radius 16,
   dashed `#cccccc` zero axes, `#666666` axis texts, `network_tab.py:890-1165`, `pca_tab.py:416-506`) are presentation and
   are reproduced by the frontend plan's ECharts components from the values in `NetworkChartData`, `AnalysisData.pca`
   and `/scales`.
6. Routers: `imports.py` (`UploadFile`, `Form`), `analysis_export.py` and `analysis_charts.py` (`NetworkLayout`,
   `focus: Optional[int]`, JSON response envelope, work in `asyncio.to_thread`). Each handler is one statement.

### Phase 6: AI interpretation

1. Copy from DEMATELab, renaming `DEMATELab` → `Policy Coherence Kit`:
   - `services/llm_provider_service.py` and its test;
   - `services/gemini_service.py` and its test (the fixed client lifetime and `HttpOptions(timeout=120000)`);
   - `errors/llm_errors.py`, with L9;
   - `features/explanation_providers_feature.py` and its test;
   - `models/explanation_models.py`, with `analysis: AnalysisRequest`.
2. `constants/llm_constants.py` is DEMATELab's file with these changes:
   - `PROVIDER_MODELS` and `DEFAULT_MODELS` are copied verbatim (checked 2026-11-16, source URLs in comments);
   - `OPENROUTER_HEADERS["X-Title"] = "Policy Coherence Kit"`;
   - `LLM_SETTINGS["SYSTEM_MESSAGE"]` is the legacy `SYSTEM_PROMPT` (`llm_tab.py:79-84`);
   - `TEMPERATURE` is `0.3` (`llm_tab.py:249`);
   - `TIMEOUT_SECONDS` is `120.0`;
   - the Azure version, the v1 suffix and the host allow-list are unchanged;
   - `ANTHROPIC_SETTINGS["MAX_TOKENS"]` is `4096`.

   Request bodies stay as in DEMATELab. In particular there is no `max_tokens` on OpenAI-compatible and Azure calls,
   because newer OpenAI models reject it. This deviation from `llm_tab.py:248` is recorded in `apps/api/AGENTS.md`.
3. `features/explanation_prompt_feature.py`: `build_prompt` and `SECTION_HEADERS` verbatim (`llm_tab.py:86-196`).
4. `features/explanation_feature.py`: DEMATELab's validation (key, Azure endpoint and SSRF check, deployment, model
   catalogue). It then recomputes the analysis through `aggregation_flow_feature` (resolved ties required), builds the
   prompt and dispatches to the provider. `api_key` is `SecretStr(repr=False)`.
5. `features/interpretation_pdf_feature.py` follows `llm_tab.py:925-976` with reportlab:
   - `SimpleDocTemplate(BytesIO, A4, 2 cm margins)`;
   - the `Section` style (Heading2, `#2c4a6e`, `spaceAfter` 6) and the `Body` style (Normal, `spaceAfter` 8,
     `leading` 14);
   - the legacy header rule and `Spacer(1, 6)`;
   - body escaping, with header escaping per L6.
6. `routers/explanations.py`: `GET /providers`, `POST ""` and `POST /export/pdf`.

Tests use `httpx.MockTransport` and a mocked Gemini client, and cover:

- URLs, headers and bodies;
- the system message;
- temperature 0.3;
- Azure URL variants and SSRF rejections;
- 401/403/429/timeout mapping;
- that the key never appears in logs (`caplog`) or in error bodies, including 422s.

### Phase 7: Scales, setup, checks, preview, router registration

1. `features/scales_feature.py` and `routers/scales.py` (`ScalesData` from constants only).
2. `routers/setup.py`, `routers/matrices.py`, `routers/weights.py` and `routers/aggregation.py` (preview).
   `routers/analysis.py` already exists (Phase 4).
3. Register every remaining router in `api/v1/api.py`. All routes are public (no auth).

### Phase 8: Docker, Compose, Nginx, Make

1. `apps/api/Dockerfile.dev` and `Dockerfile.prod` are DEMATELab's, with `python:3.13-slim`, `uv==0.12.10`, `/opt/venv`,
   but without `MPLCONFIGDIR` and without the `fonts-dejavu-core` apt layer (no matplotlib).
   - Dev: `EXPOSE 50002` and `uvicorn main:app --host 0.0.0.0 --port 50002 --reload`.
   - Prod: `EXPOSE 50002`, gunicorn with `uvicorn_worker.UvicornWorker` bound to `0.0.0.0:50002`, user `app` with
     uid 1001, and `WEB_CONCURRENCY=2`.
2. Root `docker-compose-dev.yml` (`name: policycoherencekit-dev`):
   - `api`: container `policycoherencekit-api`, `50002:50002`, `env_file ./apps/api/.env`, `APP_ENV=development`, bind
     mount `./apps/api:/app:z`, and the healthcheck `http://localhost:50002/api/v1/is-alive` at `10s/5s/5/10s`;
   - `web`: container `policycoherencekit-web`, `3001:3001`, `./apps/web:/app:z` plus an anonymous `/app/node_modules`,
     `depends_on: api`, and `env_file: [{path: ./apps/web/.env, required: false}]` while the profile guard is in place
     (the same form in prod).

   Root `docker-compose-prod.yml` (`name: policycoherencekit`): `api` (healthcheck `30s/5s/3/10s`), `web`, and `nginx`
   (`policycoherencekit-nginx`), the only published service on `${HTTP_PORT:-8081}:80`, with `depends_on: {api:
   service_healthy, web: service_started}`. Both files use `app-network` and `restart: unless-stopped`; there are no
   volumes.

   **Temporary guard:** until the frontend plan's Phase 1 exists, `web` sits under the Compose profile `web` in both
   files, and prod `nginx` uses `web: {condition: service_started, required: false}` (as DEMATELab did). The
   coordinator removes both (frontend deferred edit D1, applied together with D2–D3 when the web Phase 1 scaffold
   lands). Until then only `make check-api` is expected to pass; `make check` and `make check-web` are not.
3. `nginx/Dockerfile.prod` is DEMATELab's verbatim. `nginx/nginx.prod.conf` is DEMATELab's with:
   - the runtime resolver and `set $web_upstream http://web:3001` / `set $api_upstream http://api:50002`;
   - the `/api/` block with `proxy_buffering off` and `proxy_read_timeout 300s` (AI calls take up to 120 s);
   - `client_max_body_size 20m`, commented with the PCK sizing;
   - the HTTPS server block commented out, with the same upstreams.
4. The root `Makefile` is DEMATELab's, with:
   - the header saying "Policy Coherence Kit";
   - `override WEB_PORT := 3001`, `override API_PORT := 50002`;
   - `DEV_PROJECT := policycoherencekit-dev`, `API_CONTAINER := policycoherencekit-api`,
     `WEB_CONTAINER := policycoherencekit-web`;
   - the port-clash message naming Policy Coherence Kit and 3001/50002;
   - the help footer `Legacy Tk app: make -C tk-app help`.

   All targets are kept: `help`, `setup`, `dev`, `api`, `web`, `down`, `restart`, `ps`, `logs`, `rebuild`, `urls`,
   `sh-api`, `sh-web`, `check`, `check-api`, `check-web`, `test`, `test-api`, `test-web`, `lint`, `typecheck`, `format`,
   `install`, `prod`, `prod-down`, `prod-restart`, `prod-ps`, `prod-logs`. The `WEB_READY` and `require_web` guards are
   kept until `apps/web/package.json` exists. Docker/podman detection and the `require_dev` and `require_port` macros
   are verbatim.
5. Before the first `make check-api`, grep `apps/api` (excluding `tests/fixtures/`, `.venv/` and `uv.lock`),
   `Makefile`, `docker-compose-*.yml` and `nginx/` for `3000|50001|DEMATELab|dematelab|qt-app|Qt|DEMATEL`. Allowed hits:
   conventions-source mentions in docstrings, and digit runs inside longer numbers (for example `0.30000…` floats);
   everything else is removed.
6. `tk-app/` keeps its own Makefile and Compose files, which are not edited.

### Phase 9: Tests and docs

1. Parity tests (`tests/parity_integration_test.py`) run for every parity fixture, at feature level and over HTTP:
   - aggregation scores, ties, `ordinal_cells`, `median_choice`, scores rows, entropy, centrality, centrality ranking,
     network info, insights fields and health use `assert_allclose(rtol=0, atol=1e-12)` for floats and exact equality
     for ints, strings and orders;
   - `-0.0` is checked with `math.copysign`;
   - PCA `explained` must be equal; coordinates are compared per component after aligning the sign with the fixture
     (flip a component if its dot product with the fixture is negative), at `atol=1e-12`. A case is degenerate when
     `(S0 - S1) / S0 < 1e-9` or `(S1 - S2) / S0 < 1e-9` (fixture `singular_values`); then only `explained` is compared
     and the case is listed in `apps/api/AGENTS.md`;
   - the method label is checked against the fixture label (identical, since the result label already includes
     Lower/Upper);
   - each error fixture's input gives the public message defined by its `api_message_rule` (Phase 2.4), and
     documentation-only fixtures are skipped.
2. `tests/insights_text_parity_integration_test.py` compares the story, interpretation, tags and card texts exactly,
   after applying to the raw legacy text only these literal replacements: L11 (`" -> "` → `" → "` in pairs and
   messages; `"{r}->{c}"` → `"{r} → {c}"`; Most Contested `↔` unchanged), L12 (`"Agreement: "` → `"Rating agreement: "`
   on the Most Contested value only), L13 (the exact before → after strings in the table) and L14. The prompt is not
   relabelled: `tests/prompt_parity_integration_test.py` compares it exactly with `build_prompt`'s output for every
   fixture (the prompt is out of scope for label fixes).
3. `tests/layout_parity_integration_test.py` compares positions at `atol=1e-6` px. Layouts are presentation, not
   computed results; this tolerance is set by this plan and not loosened later. Spectral positions are compared
   directly (both sides use the L16 sign rule); fixtures marked `spectral_degenerate` are skipped with a reason.
4. `tests/import_parity_integration_test.py`: every import fixture gives the same matrices, warnings (grouped per L4)
   or error message. Gap-column and duplicate-policy fixtures give `api_expected_error`.
5. `tests/xlsx_integration_test.py` opens the API export with openpyxl and compares it with the legacy dump: sheet order,
   cell values, fills, fonts, number formats and column widths. Titles are mapped with the L3 table (`Avg` → `Average`,
   `Majority` → `Majority Rule`, sheet labels). The `dm_names` case asserts the L3 titles directly.
6. Chart-data tests:
   - `NetworkChartData` node coordinates equal the layout fixtures (same `atol=1e-6` px) for every layout, full and
     ego view; nodes and edges in legacy order; `two_way`, `sign`, `colour`, `width`, ego `label`, `title`,
     `empty_message` and `stats.text` per the contract;
   - `AnalysisData.pca` `bounds`, labels and `stats_text` match legacy values (`bounds` and points against parity
     fixtures, sign-flip rule as for PCA); n < 3 gives `valid = false`, `message`, empty points and null bounds;
   - 422 `invalid_focus_policy` for an out-of-range focus;
   - the `r5x3` policy name `$5bn and $3bn` comes back verbatim in `label`;
   - no module in `apps/api` imports `matplotlib` (repository-rules test).
7. Unit tests for every util, feature, service and router, covering:
   - 422 paths in legacy order;
   - forced Average;
   - an odd median ignoring the choice;
   - tie-choice validation;
   - the `/weights/check` messages;
   - the limits;
   - the 413 upload limit (streamed), `.xls`, more than 50 sheets, an over-wide header, an oversized zip entry, a
     chartsheet;
   - the L10 filename;
   - the PDF header escaping, including a `## <img src="http://127.0.0.1/">` header line that must render as text
     (reportlab never fetches it);
   - control characters in names (422), duplicate tie choices (422), the validation order, empty/colliding sheet names;
   - an XLSX export with a DM and a policy named `=1+1`: the cells have `data_type == "s"` (L15);
   - `/matrices/check` `blank_count` and the 10-item `blank_cells` cap.
8. `tests/repository_rules_integration_test.py`, adapted from DEMATELab, checks that:
   - every code file is ≤ 300 lines;
   - `__init__.py` files hold only a docstring;
   - no non-docstring string literal contains `tk-app`;
   - the test excludes its own file from both literal and import checks;
   - for `ast.Import`, no alias name's top-level part, and for `ast.ImportFrom`, no `module`'s top-level part
     (alias names are not checked, so `from main import app` passes) is in `{aggregator, importer, app, theme, font_loader, dialogs, aggregation_dialog,
     aggregation_tab, coherence_scores_tab, range_of_influence_tab, pca_tab, network_tab, results_insights_tab,
     llm_tab, matrix_widget, tkinter}`;
   - no file manipulates `sys.path`.

   `matplotlib` is banned in `apps/api`. Pillow is not banned, because reportlab needs it.
9. Docs:
   - `apps/api/AGENTS.md`: DEMATELab's structure (Commands, Code Style, Error handling, Class-based code, File size,
     Numerical Parity, Architecture, Layers, API versioning, AI interpretation, Health, Environment, Adding an Endpoint,
     Testing, Pitfalls), rewritten for PCK. Its Numerical Parity section carries the generator command, the tolerance
     and the BLAS note, the Known Tkinter Behaviour Kept list, the Label Fixes list and the `max_tokens` deviation.
   - `apps/api/README.md`.
   - Root `AGENTS.md`, rewritten in DEMATELab's shape:
     - how the app fits together;
     - the layout, including `tk-app/` as read-only;
     - running with `make`;
     - the services and env files table (`apps/api/.env`, later `apps/web/.env`, and `tk-app/.env` with
       `VNC_PASSWORD`, `SCREEN_GEOMETRY`, `NOVNC_PORT`);
     - the workflow (plan first, ≤ 300 lines, `make format` and `make check-api`);
     - the pre-commit checklist;
     - a "Legacy Tk App (`tk-app/`)" section keeping today's guidance, with paths updated (`tk-app/main.py`,
       `data/examples/WEF Nexus Example.xlsx`, `make -C tk-app dev`, Compose project `policycoherencekit-tk-dev`).
   - Root `README.md`: an "Apps" section (make commands, URLs `http://localhost:50002/api/docs` and
     `http://localhost:8081`), with the Tk instructions kept as legacy and their paths updated.
10. Decision records in `docs/decisions/` follow the guide format, dated 2026-11-18, with Deciders "Youpele Michael
    (owner), Claude Code":
    - `rebuild-in-apps-with-fastapi-and-tanstack-start`;
    - `docker-compose-with-nginx-as-only-public-entry`;
    - `each-service-has-its-own-env-file`;
    - `make-entrypoint-with-container-first-checks`;
    - `stateless-api-with-browser-rendered-charts` (charts are browser-rendered from API chart data; the API returns
      data, never chart images; current-run XLSX);
    - `browser-charts-with-echarts` (new; replaces the planned server-rendered-charts decision: ECharts only, layouts
      and PCA computed in the API, P3–P9 as Settled Decision 7, downloads produced in the browser; the frontend plan
      adds its component and bundle-budget details);
    - `ai-keys-supplied-per-request` (six providers, SSRF allow-list, TLS before production AI use);
    - `keep-legacy-maths-fix-labels` (new);
    - `one-project-per-browser-session` (new).

    DEMATELab's seventh record, the warm-white theme, is a frontend decision and is written by the frontend plan.

## Risks And Decision Gates

- **Gate: fixtures before maths.** Phase 4 starts only after Phase 2's fixtures exist, and both sides pin the same
  numpy and openpyxl versions. A mismatch above `1e-12` is a bug in the port. Never loosen the tolerance without a new
  decision record.
- **Linux vs macOS.** Fixtures are generated on macOS (Accelerate BLAS), while the dev container runs Linux (OpenBLAS).
  - Non-PCA numbers are pure Python and are expected to be bit-exact. `math.log2` may differ by one ulp before rounding
    to 4 dp; that has not been observed.
  - PCA uses SVD. If a non-degenerate case differs above `1e-12` on Linux, stop and report.
  - Degenerate PCA cases (Phase 9.1 singular-value rule) compare `explained` only and are documented in
    `apps/api/AGENTS.md`, as DEMATELab did. Spectral layouts use L16 and skip near-equal eigenvalues. Do not change the
    tolerance.
  - The Linux parity gate after Phase 4 surfaces these differences before charts, import and export are built on them.
- **Generator replication.** Most texts are captured from legacy code (Phase 2.2). Only the tag/hero texts built in
  direct `tk.Label` calls and the network-info stats are hand-copied; a reviewer checks each against the cited lines
  before Phase 4 starts.
- **Hostile uploads.** Zip bombs, XML entity attacks, huge sheets and chartsheets are bounded by Phase 5.1's hardening
  and `defusedxml`.
- **Tk on the host.** The generator needs `import tkinter` (verified on uv's Python 3.13.2). If it fails, stop and
  report; never stub `tkinter` in a way that changes computations.
- **CPU cost.** Brandes and closeness in pure Python at 100 policies take about 1–3 s per request, and every chart and
  network chart-data call recomputes. This is acceptable for the limits. Use `asyncio.to_thread`, and gunicorn workers give process
  isolation.
- **Layout parity on the square canvas.** Fixtures and API both use 600×600; if a legacy layout helper reads the
  canvas size elsewhere than its arguments, stop and report rather than adjusting coordinates.
- **AI keys in transit.** HTTPS is only prepared, commented out, in Nginx. Production must enable TLS before the AI
  feature is used; this is documented in the README and the AI-keys decision.
- **Request size.** The maximum is about 8 MB of JSON; the Nginx limit is 20 MB.
- **Compose profile guard.** If the frontend lands first, skip the guard. If it is left in place after `apps/web`
  exists, prod Nginx serves 502 on `/`. The frontend plan's Phase 1 removes it.

## Testing And Validation

Fixture generation, from the repository root:

```bash
uv run --frozen --python 3.13 --project tk-app python scripts/generate_parity_fixtures.py
```

API on the host:

```bash
cd apps/api && uv sync --frozen && uv run ruff format --check . && uv run ruff check . && uv run pytest
```

Inside the dev container (`make setup && make dev` first):

```bash
make check-api
make test-api T="tests/parity_integration_test.py -v"
```

Legacy untouched:

```bash
git diff -- tk-app | shasum
git status --porcelain -- tk-app | shasum
git ls-files -z -co --exclude-standard tk-app | sort -z | xargs -0 shasum | shasum
```

All three must equal the values recorded before Phase 1.

Generator code quality (repository root):

```bash
uv run --project apps/api ruff check --config apps/api/pyproject.toml scripts
uv run --project apps/api ruff format --check --config apps/api/pyproject.toml scripts
```

Production smoke test:

```bash
make prod && curl -fsS http://localhost:8081/api/v1/health && make prod-down
```

Manual checks, recording the results in the implementation report:

1. Open `http://localhost:50002/api/docs` and check that every contract endpoint is listed.
2. Post `data/examples/WEF Nexus Example.xlsx` to `/imports/workbook`.
3. Post the resulting request to `/analysis`. Compare it with the legacy app on the same workbook (`make -C tk-app dev`,
   `http://localhost:6090`) for the coherence scores, entropy, centrality and insights cards.
4. Download the XLSX and compare it with the legacy export.
5. Post the request to `/analysis/charts/network` for each layout and one focus, and check the coordinates against the
   layout fixtures; the visual chart check is in the frontend plan.
6. With a real key for at least one provider, if available, generate an interpretation and export the PDF. If no key is
   available, record that this check was blocked.

## Acceptance Criteria

- Every endpoint in the API Contract exists, appears in `/api/docs` and returns the documented shapes.
- Every parity, text, prompt, layout, import and XLSX fixture test passes, both on the host and in `make check-api`
  (Linux).
- Every business rule in the table is enforced by the API, with the listed messages and codes.
- Every Label Fix is implemented and tested, and every Known Tkinter Behaviour Kept item is unchanged and documented.
- Invalid input returns 4xx with a public message and never a stack trace or an API key.
- `make check-api` passes, every code file in `apps/api` is ≤ 300 lines, and the repository-rules test passes.
- `make dev` and `make prod` start a healthy API (and Nginx in prod) before `apps/web` exists.
- `tk-app/` is byte-identical to the baseline (all three hashes).
- The Linux parity gate passed after Phase 4, and every Label Fix L1–L16 has a test.
- `apps/api/AGENTS.md`, `apps/api/README.md`, the root `AGENTS.md` and `README.md`, and the nine decision records
  describe the new setup. The Tk instructions remain as legacy.

## Plan Validity

This plan is valid for branch `restructure/apps-api-web` at `00b610a`, with the uncommitted restructure described in the
header and the `tk-app/*.py` contents unchanged by the move.

Revalidate if any of these change:

- `tk-app/*.py`, `tk-app/uv.lock` or `tk-app/assets/fonts/`;
- `data/examples/WEF Nexus Example.xlsx`;
- DEMATELab's `apps/api` skeleton, `llm_constants.py` or infra files (copy sources at `6a76ae2`);
- provider APIs (the model catalogue was checked by DEMATELab on 2026-11-16);
- the restructure commit, if it moves paths.

## Handoff Notes

- **Order:** 1 → 2 → 3 → 4 → Linux parity gate → 5/6/7 → 8 → 9. At most two implementation threads, with
  disjoint file ownership:
  - backend: `apps/api`, `scripts/`, root infra and `docs/`;
  - frontend: `apps/web` only.
- **Do not reopen:** the Settled Decisions, the Business Rules table, Known Tkinter Behaviour Kept and the Label Fixes,
  unless there is new evidence.
- **The contract is shared** with the frontend plan. Change it only by updating both plans.
- **Process rules:**
  - never commit or push;
  - no worktrees or branches;
  - no git state changes;
  - report every deviation with evidence;
  - run every check listed above.
- **Deferred root edits from the frontend plan (D1–D3)** are applied by the coordinator as soon as the web Phase 1
  scaffold lands, not at the end. Until then the backend thread expects only `make check-api` to pass.
- **Contract additions in revision 2** (both plans updated together): `MatrixCheckData.decision_makers[]` with
  `blank_count` and capped `blank_cells`; `/scales.network.layouts` contents and order; `/scales.texts`; L11–L16.
- **Contract changes in revision 3** (browser charts, both plans updated together): PNG chart and hotspot endpoints,
  `/scales.charts`, `ChartHotspotsData` and `pca_unavailable` removed; `POST /analysis/charts/network` returns
  `NetworkChartData` JSON; `AnalysisData.pca` gains `label`, `bounds`, axis labels and `stats_text`;
  `AnalysisData.network` gains `stats_text` and edge `sign`/`two_way`; `/scales.network` gains node colours and
  `layout_canvas`; `/scales.pca` added. Layout fixtures move to the 600×600 canvas.
- **No blockers.**

## Open Questions

None. There are no open product decisions.

One check depends on external access: the live AI provider check is manual and depends on a key being available. If it
is not, it is recorded as blocked and does not block acceptance.
