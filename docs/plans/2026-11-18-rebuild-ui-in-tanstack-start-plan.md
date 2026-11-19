# Rebuild The Policy Coherence Kit UI In TanStack Start (`apps/web`)

**Date:** 18 November, 2026
**Status:** Ready for implementation (Phases 3–7 integrate against the backend plan's API Contract; see Risks And
Decision Gates)
**Owner:** Youpele Michael (planned with Claude Code)
**Created:** 2026-11-18 18:43 CET · **Last modified:** 2026-11-18 19:45 CET (revision 3: owner decision of 2026-11-18,
browser charts with Apache ECharts replace server-rendered PNGs)
**Inspected:** `policycoherencekit`, branch `restructure/apps-api-web`, commit `00b610a`.
The worktree is not clean: the legacy app is moved into `tk-app/` (staged renames; `tk-app/.dockerignore`, `Makefile`
and `docker-compose-{dev,prod}.yml` also have unstaged edits), the sample workbook is at
`data/examples/WEF Nexus Example.xlsx`, `.gitignore` is modified and `docs/` is untracked. `apps/` does not exist yet.
Conventions and components source: `dematelab` at commit `6a76ae2` (`apps/web`,
`docs/decisions/2026-11-16-warm-white-variant-of-the-ice2kg-theme.md`). API source of truth:
`docs/plans/2026-11-18-port-backend-to-fastapi-api-plan.md` (header "Last modified 2026-11-18 19:40 CET", revision 3).

## Summary

The Tkinter workspace (`tk-app/`) is rebuilt as a TanStack Start web app in `apps/web`, copying DEMATELab's already
reviewed web app (`dematelab/apps/web`, commit `6a76ae2`) and customising it for Policy Coherence Kit (PCK):

- a Typeform-style flow, one question per step: project name, decision-makers, policies, an optional Excel import, one
  matrix step per decision-maker, review, aggregation method, then weights, median choice or tie resolution where they
  apply;
- a full-width Results screen with the seven legacy analysis tabs (Results Insights, Aggregated, Coherence Scores,
  Range of Influence, PCA, Network Analysis, AI Interpretation) and an export bar;
- the PCA scatter and the network graph drawn in the browser with Apache ECharts from API chart data, through
  reusable themed chart components, with PNG/SVG downloads produced in the browser;
- DEMATELab's warm-white variant of the ice2kg theme, with the seven legacy rating colours checked for WCAG AA.

The browser computes nothing about policy coherence. Labels, limits, defaults, ratings and method names come from
`GET /api/v1/scales`; validation, aggregation, analyses, chart data (layout coordinates, edges, colours, axis bounds), import and the
XLSX/PDF exports come from the FastAPI service in
`apps/api`. Legacy texts are kept verbatim except for the label fixes listed in this plan.

## Related Work

- Backend plan (dependency; its API Contract is binding here):
  [Port The Policy Coherence Kit Backend To A Dockerised FastAPI `apps/api`](2026-11-18-port-backend-to-fastapi-api-plan.md).
  It also creates the root `Makefile`, `docker-compose-{dev,prod}.yml` and `nginx/` with a temporary `web` profile guard
  that this plan removes (deferred cross-area edit D1).
- Report: [Tk app UI inventory](../reports/2026-11-18-tk-app-ui-inventory-report.md): every legacy text and control,
  the 40 inconsistencies (§4) and the flow mapping (§5).
- Report: [Tk app logic inventory](../reports/2026-11-18-tk-app-logic-inventory-report.md): business rules, messages,
  exports and parity traps (formatting trap 2 and 3 are relevant here).
- Report: [DEMATELab conventions inventory](../reports/2026-11-18-dematelab-conventions-inventory-report.md): what to copy,
  adapt and strip in `apps/web` (Finding 4), versions (Finding 5), theme tokens (Finding 6), the missing web 300-line
  test (Finding 7), the playbook lessons (Finding 10).
- Model plan: `dematelab/docs/plans/2026-11-16-rebuild-ui-in-tanstack-start-plan.md`.
- Model code: `dematelab/apps/web` (AGENTS.md, `src/`), commit `6a76ae2`.
- Model decision: `dematelab/docs/decisions/2026-11-16-warm-white-variant-of-the-ice2kg-theme.md`.
- Playbook: `dematelab/docs/reports/2026-11-16-qt-to-fastapi-and-tanstack-migration-playbook-report.md`,
  Finding 4 (settled UI decisions) and Finding 8 (review findings: Enter submitted the unclamped stepper value, focus
  landed on hidden inputs, stale "answered" matrix steps).
- Research: [browser chart libraries](../research/2026-11-18-browser-chart-libraries-research.md) (ECharts graph,
  scatter, export, SSR, accessibility and theming findings). Part A of
  `docs/plans/2026-11-18-browser-charts-and-shared-vps-plan.md` (phases A0–A3, P1–P9) was moved into this plan and the
  backend plan on 2026-11-18; that plan keeps only Part B (shared VPS), which stays future work.
- Decisions: none exist yet in `docs/decisions/`. This plan supplies the text of
  `2026-11-18-warm-white-variant-of-the-ice2kg-theme.md` (deferred cross-area edit D5).
- JuGit issue or merge request: none identified. The work is tracked by this plan and the branch.

## Problem

The only UI is a Tkinter desktop window (`tk-app/main.py`), served in Docker over noVNC for remote use. It has a
multi-project sidebar, a top bar with always-enabled buttons whose preconditions are reported in message boxes
(`tk-app/app.py:753-959`), five modal dialogs that drive aggregation (`tk-app/aggregation_dialog.py`), and seven result
tabs that are partly broken or inconsistent (UI report §4: overlapping network arrows, broken story highlighting, four
spellings of the method name, silently stale results, silently forced Average). The backend plan moves every non-UI
rule into a stateless API; a browser UI is needed that uses it, works on phones and desktops, and keeps the legacy
texts and behaviour that users know.

## Goals

- Every legacy screen, control, text and export listed in the Parity Inventory works in the browser against the API,
  with the label fixes in Legacy Inconsistencies Settled.
- The flow is one question per step with progress, Back/OK, Enter / Shift+Enter, `?step=` in the URL and browser
  history, a step list, a Review step with Edit links and full-width Results; earlier answers can be changed and later
  work is kept where valid.
- No policy-coherence computation in the browser: every number, label, limit, default and validation result comes from
  the API. The browser only formats numbers (Python-compatible formatting) and counts filled cells for progress text.
- Visual design: DEMATELab's warm-white ice2kg theme (Manrope), rating colours from the Tk app at WCAG AA, usable from
  320 px wide.
- Code follows DEMATELab's `apps/web/AGENTS.md`, plus a Vitest test that enforces the 300-line limit and the
  "no `tk-app` references" rule for `apps/web`.
- `make dev` serves the web app on `http://localhost:3001`; `make prod` serves it behind Nginx on
  `http://localhost:8081`; `make check-web` passes.

## Non-Goals

- Any policy-coherence maths, rounding of computed values, validation rules or business rules in the browser.
- Persistence: no accounts, no saved projects, no localStorage of answers. A refresh starts over at step 1 (Settled
  Decision 4). Only a one-time "refresh notice shown" flag is kept in `sessionStorage`, as in DEMATELab.
- The legacy multi-project sidebar, project switching, saved run history, `Rename Tab` / `Delete Tab`, the DM/Analysis
  pill toggle, scrolling tab strips, the status bar, platform-specific font sizes and font installation (dropped; see
  the Parity Inventory "Dropped" table).
- Node dragging or graph editing, PCA loadings/biplot or quadrants (P5), new bar charts for range of influence or
  coherence scores (P6), a second chart library (shadcn charts/Recharts), server-side chart rendering or ECharts SSR.
- Table sorting (legacy tables are fixed order), dark mode (the `.dark` block is kept unused, as in DEMATELab), a
  client-side PNG capture of the Results Insights cards (legacy has no such export; `html-to-image` is not added).
- Showing median ordinal label pairs (`ordinal_cells`); legacy never shows them (logic report trap 11). The API keeps
  them for a later change.
- Any change to `tk-app/` (read-only) or to `apps/api` (backend thread). Root files are changed only through the
  deferred cross-area edits listed in Phase 8.

## Current State

- `apps/web` does not exist. The backend plan (Phase 8) creates the root `Makefile`, `docker-compose-dev.yml`,
  `docker-compose-prod.yml` and `nginx/`, with the `web` service under the Compose profile `web` and prod Nginx using
  `web: {condition: service_started, required: false}` until this plan's Phase 1 (deferred edit D1).
- Root `.gitignore` ignores `.vscode/` (line "`.vscode/`"), so `apps/web/.vscode/settings.json` needs a negation
  (deferred edit D3).
- DEMATELab's `apps/web` (commit `6a76ae2`) has every mechanism this plan needs, already reviewed and fixed:
  `FlowShell`, `FlowStep`, `StepFrame` (Enter/Shift+Enter, `initialFocus` skipping hidden inputs), `StepNavigation`,
  `StepProgress`, `StepList`, `StartOverButton`, `ResetConfirmDialog`, `OutdatedResultsBanner`, `ReviewStep`/`ReviewRow`,
  `MatrixGrid`/`MatrixCell` (virtualised, per-cell store subscription), `MatrixImportActions`, `ResultsCard`,
  `ResultTabs`, `ExportBar`, `ChartImage`, `ZoomableImage` (image charts; not used by PCK, Settled Decision 8), `DownloadButton`, `ExplanationPanel`,
  `ExplanationSettings`, `ApiKeyInput`, `AzureEndpointDialog`, `NumberStepper`, `utils/flow.utils.ts`,
  `hooks/refresh-notice.hook.ts`, `store/analysis.store.ts`, `utils/api.utils.ts`, `components/ui/*` (shadcn
  base-nova on Base UI), `styles.css` (warm-white tokens), `__root.tsx` with one themed `<Toaster />`.
- Legacy UI sources (line numbers in `tk-app/`): shell and flow `app.py` (3217 lines), setup dialog `dialogs.py:301-1283`,
  aggregation dialogs `aggregation_dialog.py`, matrix editor `matrix_widget.py`, tabs `*_tab.py`, rating colours
  `constants.py:30-49`.

## Settled Decisions (owner-approved; do not reopen without new evidence)

1. **Stack and structure as DEMATELab.** TanStack Start (React 19, file routes, Vite, Nitro), TypeScript strict, pnpm,
   Biome, Vitest, shadcn on Base UI (`base-nova`), Tailwind v4, Zustand store holding the **request snapshot** used for
   results, charts and exports, Zod interfaces, TanStack Query. Layout `src/routes/`, `components/{ui,general,
   page-specific/<page>}`, `hooks/`, `services/`, `interfaces/`, `utils/`, `constants/`, `store/` (plus `lib/`, `test/`).
   Every code file ≤ 300 lines, enforced for the web by a new Vitest test. Port **3001**
   (`vite dev --port 3001 --strictPort`), `VITE_API_BASE_URL=http://localhost:50002` in dev and empty in production.
   Versions exactly as the conventions report Finding 5 (TanStack Start 1.169.4, React 19.3.1 resolved, Router 1.170.46,
   Query 5.105.0, Biome 2.4.5, Vitest 5.0.5, Node 24, pnpm 12.9.1, …).
2. **Look.** DEMATELab's warm-white variant of the ice2kg theme: identical tokens, Manrope Variable. The seven rating
   colours come from the Tk app (`tk-app/constants.py:30-49`); text/background pairs are checked for WCAG AA (4.5:1) and
   only the failing ones are adjusted in lightness, as recorded in the Theme table and the decision record (D5).
3. **Flow.** Typeform-style, one question per step, progress bar, Back/OK, Enter / Shift+Enter, `?step=` in the URL and
   browser history, step list, Review step with Edit links, Start over (quiet text button at the far end of the Back/OK
   row and on Results, hidden when nothing is answered, confirm dialog, red **text** on hover only, no background),
   pointer cursors, responsive 320 px → desktop, themed Sonner toasts including a one-time notice that refreshing starts
   over. Changing earlier answers keeps later work where valid; removals that lose ratings ask first; results stay
   visible with an out-of-date banner and Re-run. Step order (UI report §5): project name, decision-makers, policies,
   Excel import option, one matrix step per decision-maker (virtualised editor, themed selects, a cell can be cleared,
   keyboard use), review, aggregation method (choice only with ≥ 3 decision-makers, otherwise Average with an
   explanation), weights or median lower/upper (even count only), tie resolution for Majority, then full-width Results
   with the seven tabs and an export bar (XLSX via API; network/PCA PNG 2400×1800 + SVG generated in the browser; AI
   text as TXT client-side
   and PDF via API).
4. **One project per browser session.** Nothing is persisted; a refresh returns to step 1. The legacy multi-project
   sidebar and saved run history are dropped (backend Settled Decision 3 and 8: stateless, current run only).
5. **No policy-coherence maths in the browser.** Labels, limits, defaults, ratings, method names, median choices, band
   keys, entropy categories, network layouts, chart colours and the layout canvas come from `GET /scales`; layout
   coordinates, PCA points, axis bounds, edge widths and chart texts come from the API (Settled Decision 8). Name validation
   (`POST /setup/validate`), completeness and method availability (`POST /matrices/check`), weight parsing and the live
   sum (`POST /weights/check`), ties (`POST /aggregation/preview`) and every analysis value come from the API.
6. **Keep maths, fix labels.** Method names are the API's single labels (`Average`, `Median`, `Majority Rule`,
   `Weighted`; result label `Median (Lower)` / `Median (Upper)` for even counts; backend L1). Wrong or misleading legacy
   texts are fixed and each one is decided in Legacy Inconsistencies Settled; every other text is verbatim and listed in
   the Parity Inventory.
7. **AI panel as DEMATELab.** Six providers and their model lists from `GET /explanations/providers`, the Azure
   deployment field and endpoint dialog, a show/hide API key field. The privacy note is reworded truthfully: the key
   passes through our server for this one request and is never stored or logged. The key field is cleared after both
   success and failure (legacy `llm_tab.py:841, 848`; DEMATELab does not do this, so it is added).
8. **Charts are drawn in the browser with Apache ECharts** (owner decision 2026-11-18; replaces server-rendered
   matplotlib PNGs, `ChartImage`, `ZoomableImage` and hotspot overlays). Settled sub-decisions, adopted from the
   follow-up plan's recommendations:
   - **P1 ECharts only**, `echarts` 6.1.0 (research), tree-shaken through `echarts/core` with only `GraphChart`,
     `ScatterChart`, `GridComponent`, `TooltipComponent`, `LegendComponent`, `DataZoomComponent`,
     `MarkLineComponent`, `TitleComponent`, `AriaComponent`, `CanvasRenderer` and `SVGRenderer`. No
     `echarts-for-react`, no Recharts/shadcn charts, no second library.
   - **P3** The browser computes nothing: layouts (circular, force-directed, spectral, shell, legacy order) come from
     `POST /analysis/charts/network`; PCA points, bounds and axis texts from `AnalysisData.pca`.
   - **P4** Two-way edges (`two_way`) are drawn as two curves on opposite sides (display fix for legacy defect 2).
   - **P5** PCA is a plain scatter as legacy; **P6** no new bar charts (tables stay tables).
   - **P7** Downloads are produced in the browser: PNG 2400×1800 px (off-screen 800×600 instance, `pixelRatio: 3`,
     white background, fonts loaded) with a 300 dpi `pHYs` chunk inserted, plus SVG from the SVG renderer; files
     `network_plot.png`/`.svg` (current layout and focus) and `pca_plot.png`/`.svg` (current colour mode).
   - **P8** Tooltips with the legacy `{code}:  {policy}` labels, legend toggle, zoom/pan (`roam` for the graph,
     `dataZoom` inside for PCA) with a Reset view button; no node dragging (`draggable: false`). Layout and focus stay
     as selects above the chart.
   - **P9** Aspect ratio kept: the network's 600×600 layout box maps to a square plot area; nothing is stretched.
   - **Styling:** chart colours, font family, sizes, radii and spacing are read from the theme CSS variables
     (warm-white tokens; domain colours from `/scales`), tooltips and legends look like shadcn popovers/cards
     (`--popover`, `--border`, `--radius`, Manrope), charts sit in `SectionCard`s.
   - **Reusable components:** one themed base `EChart` in `components/general/charts/` plus typed per-type components
     (`DirectedNetworkChart`, `ScatterChart`) that `NetworkPanel` and `PcaPanel` compose. `HeatmapChart`/`BarChart`
     are not built (no legacy plot needs them).
   - **Bundle budget:** the lazily loaded chart chunk is ≤ 250 KB gzip (the DEMATELab plan's suggested budget);
     measured in Phase 6 and recorded in the implementation report.
9. **Infra.** Dev and prod run through the root Compose files and `Makefile` created by the backend plan. This plan fills
   `apps/web` only, plus `apps/web/AGENTS.md`, `apps/web/README.md` and `apps/web/CLAUDE.md` (`@AGENTS.md`), and lists
   the root-file edits it needs as deferred cross-area edits for the coordinator (Phase 8).
10. **Process.** Implementers never commit or push, never create worktrees or branches, make no git state changes, and
    report every deviation with evidence. The frontend implementer owns `apps/web` only.
11. **Planning-level choices made here, within the owner's decisions** (recorded so they are not reopened):
    1. **Two import entry points, matching the legacy's two import modes.** Step 1 offers "Import from Excel" (legacy
       Create Project dialog button, `dialogs.py:495`; "new project from import", `app.py:3000-3035`): the workbook
       replaces decision-makers, policies and ratings. The optional `import` step after Policies is the legacy
       "import into the project" (`app.py:2919-2998`): the policy list must match (sent as `policies`, legacy
       `policy_list_mismatch` message); a sheet named like an existing decision-maker fills that matrix, other sheets
       are added as new decision-makers. The web never sends `decision_makers` to `/imports/workbook`.
    2. **Answers are drafts until OK** on the name steps (project, decision-makers, policies): edits live in component
       state, OK validates through `/setup/validate` and commits to the store. Leaving the step without OK discards the
       draft. Matrix cells, weights, method, median and tie choices are written to the store immediately (as DEMATELab
       does for matrices).
    3. **Matrices, weights, tie choices and "answered" matrix steps are keyed by stable ids** of decision-makers and
       policies, not positions, so renames, removals and imports never attach ratings to the wrong person or cell
       (playbook Finding 8, stale answered matrix steps).
    4. **The analysis runs from the last question step** (method, weights, median or ties, whichever is last), whose OK
       button reads `Run Analysis`. Majority always calls `/aggregation/preview` first and opens the ties step only if
       ties exist.
    5. **Blank cells** are shown as `--` while editing (legacy) and are not highlighted; the Review step lists them per
       decision-maker from `/matrices/check` and blocks moving on until complete.
    6. **Colour tokens live in `styles.css`**, keyed by the API's keys (rating labels, band keys, entropy category
       labels). The API's legacy colours remain the source for XLSX and for chart series (nodes, edges, PCA points,
       entropy categories); chart legends use the same API colours as swatches with ink text beside them, so legend
       and chart always match. Chart chrome (text, axes, grid, tooltip, legend) uses theme tokens.
    7. **Logo:** the legacy sidebar badge (Lucide "waypoints" in `#f5f7fa` on a `#1f2937` rounded square,
       `app.py:404-477`) rendered by `AppHeader` with `lucide-react`'s `WaypointsIcon`, plus `public/favicon.svg` with
       the same drawing. No PNG logo or `apple-touch-icon.png`: the only bitmap source is 64×64
       (`tk-app/assets/fonts/logo_icon_sidebar.png`) and would blur.
    8. **Footer:** `Policy Coherence Kit · {year}` with no institutional link (none is evidenced in this repository).
    9. **AI downloads are always enabled** (legacy); without text they show `Generate an interpretation first.`

## Theme

Copy DEMATELab's `apps/web/src/styles.css` (180 lines) verbatim, then replace the DEMATEL domain tokens (`--cause`,
`--cause-foreground`, `--effect`, `--effect-foreground`, `--cell-edited`) with the PCK domain tokens below and register
each in `@theme inline` as `--color-<name>`.

### Base tokens (unchanged from DEMATELab)

| Token | Value | Token | Value |
| --- | --- | --- | --- |
| `--background` | `#faf8f4` | `--foreground`, `--primary`, `--*-foreground` inks | `#023d6b` |
| `--card`, `--popover`, `--primary-foreground` | `#fffdf9` | `--secondary`, `--muted`, `--accent` | `#f4f1ea` |
| `--soft-2` | `#eeeae1` | `--border`, `--input` | `#e8e3d9` |
| `--line-strong` | `#d6cfc2` | `--muted-foreground` | `#6f6a60` |
| `--ring`, `--placeholder` | `#a39d91` | `--destructive` | `oklch(0.577 0.245 27.325)` |
| `--sidebar` | `oklch(0.985 0.006 85)` | body gradient | `#fffdf9` / `#fbf9f5` / `#f4f1ea` |
| `--radius` | `0.625rem` | font | `'Manrope Variable', 'Helvetica Neue', Helvetica, sans-serif` |

Measured (WCAG 2.x relative luminance): ink `#023d6b` 10.98 / 10.52 / 9.89 on card / background / muted; muted text
`#6f6a60` 5.29 / 5.07 / 4.77. Placeholder `#a39d91` stays below AA and is used only for placeholders, as in DEMATELab.

### Domain tokens (new; legacy value → web value, contrast after adjustment)

Adjustment rule, applied in this order to each failing text/background pair: (1) a dark legacy text colour is darkened
(HLS lightness only); (2) a white legacy text is replaced by the legacy dark ink `#2d2d2d` if that reaches 4.5:1;
(3) otherwise the fill is darkened (HLS lightness only, steps of 0.005) until white text reaches 4.5:1. Values below were
computed with these rules; Phase 2 re-measures them with a contrast checker and the theme test.

| Token pair (`--x` / `--x-foreground`) | Legacy fill / text (source) | Legacy ratio | Web fill / text | Web ratio |
| --- | --- | --- | --- | --- |
| `rating-indivisible` | `#0B6E6E` / `#ffffff` (`constants.py:30-49`) | 6.05 | unchanged | 6.05 |
| `rating-reinforcing` | `#2A9D8F` / `#ffffff` | 3.32 | `#238377` / `#ffffff` (rule 3; dark ink only 4.14) | 4.58 |
| `rating-enabling` | `#6BAF92` / `#2d2d2d` | 5.36 | unchanged | 5.36 |
| `rating-neutral` | `#B0B7C3` / `#555555` | 3.69 | `#B0B7C3` / `#484848` (rule 1) | 4.53 |
| `rating-constraining` | `#E9C46A` / `#2d2d2d` | 8.24 | unchanged | 8.24 |
| `rating-counteracting` | `#E76F51` / `#ffffff` | 3.09 | `#d6421d` / `#ffffff` (rule 3; dark ink only 4.45) | 4.51 |
| `rating-cancelling` | `#9B2226` / `#ffffff` | 7.92 | unchanged | 7.92 |
| `value-strong-positive` | `#177e40` / `#ffffff` (`coherence_scores_tab.py:73-87`) | 5.13 | unchanged | 5.13 |
| `value-positive` | `#25c263` / `#ffffff` | 2.34 | `#25c263` / `#2d2d2d` (rule 2) | 5.89 |
| `value-weak-positive` | `#88edaf` / `#2d2d2d` | 9.69 | unchanged | 9.69 |
| `value-zero` | `#d9d9d9` / `#555555` | 5.28 | unchanged | 5.28 |
| `value-weak-negative` | `#f5c07a` / `#2d2d2d` | 8.33 | unchanged | 8.33 |
| `value-negative` | `#e07b39` / `#ffffff` | 2.97 | `#e07b39` / `#2d2d2d` (rule 2) | 4.63 |
| `value-strong-negative` | `#ef4444` / `#ffffff` | 3.76 | `#eb1515` / `#ffffff` (rule 3; dark ink only 3.66) | 4.52 |
| `count-very-high` | `#7799b9` / `#ffffff` (`coherence_scores_tab.py:89-100`) | 2.98 | `#7799b9` / `#2d2d2d` (rule 2) | 4.62 |
| `count-high` | `#a6bcd3` / `#1f2937` | 7.52 | unchanged | 7.52 |
| `count-medium` | `#d0dbe7` / `#1f2937` | 10.46 | unchanged | 10.46 |
| `count-low` | `#eae7e0` / `#666666` | 4.65 | unchanged | 4.65 |
| `count-none` | `#d9d9d9` / `#555555` | 5.28 | unchanged | 5.28 |
| `entropy-low` | `#a3a3a3` / `#ffffff` (`range_of_influence_tab.py:55-62`) | 2.52 | `#a3a3a3` / `#2d2d2d` (rule 2) | 5.46 |
| `entropy-low-to-medium` | `#a7f3d0` / `#2d2d2d` | 10.74 | unchanged | 10.74 |
| `entropy-medium-to-high` | `#34d399` / `#ffffff` | 1.92 | `#34d399` / `#2d2d2d` (rule 2) | 7.16 |
| `entropy-high` | `#059669` / `#ffffff` | 3.77 | `#05875f` / `#ffffff` (rule 3; dark ink only 3.65) | 4.53 |

Role text colours on the card surface `#fffdf9` (story code colouring, `results_insights_tab.py` driver/dependent/
balanced): `--role-driver` `#2A9D8F` → `#238377` (3.27 → 4.51), `--role-dependent` `#F4A261` → `#b9590d` (2.03 → 4.60),
`--role-balanced` `#6B7280` unchanged (4.76).

Non-text graphics keep legacy colours (WCAG 1.4.3 does not apply; they sit next to ink labels): health bars
`--health-synergy #15803d`, `--health-conflict #b91c1c`, `--health-neutral #2563EB` on track `#f5f5f5`
(`results_insights_tab.py:909-951`). Network legend and PCA entropy legend swatches use the colours returned by
`/scales` (`network.positive_colour`, `negative_colour`, `isolated_colour`, `node_colour`, `focus_colour`;
`entropy_categories[].fill`), the same values the ECharts series use, so legend and chart match exactly. Chart chrome
tokens (read by `chart-theme.utils.ts` with `getComputedStyle`): `--foreground` text, `--muted-foreground` axis names and
hints, `--line-strong` zero axes (dashed), `--border` grid/tooltip border, `--popover` tooltip surface, `--radius`
tooltip radius, Manrope font family; spacing from Tailwind's `--spacing`.

Matrix cells: unrated cell `bg-card` with `--` in `text-muted-foreground` (legacy `#a3a3a3` on white is 2.5:1);
diagonal disabled, `bg-muted` with the diagonal label in `text-muted-foreground`. Insight cards use the theme surfaces
and ink; the legacy per-card pastel backgrounds and accent colours (`results_insights_tab.py` card constants) are not
ported.

## Flow

Route `/` with a Zod-validated `step` search param (`flowSearchSchema`, copied). Step ids:

```text
project · decision-makers · policies · import · matrix-1 … matrix-k · review · method · [weights | median] · [ties] · results
```

`questionSteps(state)` (in `utils/flow.utils.ts`) returns the ordered question steps for the current store state:

- Weight texts and parsed weights are keyed by decision-maker id; the request lists them in the current decision-maker
  order, so reordering never moves a weight to another person.
- `matrix-i` exists for each committed decision-maker (1-based, in list order); answered-ness of a matrix step is read
  from `answeredMatrices` (decision-maker ids), so removing or reordering never marks the wrong step answered.
- `weights` is included only when `method === "weighted"` and the stored `aggregationOptions.method_choice_available`;
  `median` only when `method === "median"`, choice available and `aggregationOptions.median_choice_applies`; `ties` only
  when `method === "majority"`, choice available and the stored preview reported at least one tie.
- `aggregationOptions` is the last `/matrices/check` result together with the decision-maker names it was computed for;
  it counts as unknown (steps after `method` hidden) when the names differ.

Guards and navigation are DEMATELab's (`canOpenStep`, `firstUnansweredStep`, `nextStep`, `previousStep`, `isStepId`
extended for the new ids): opening a step whose earlier steps are not answered redirects to the first unanswered step;
`results` opens only with results. `?step=` is pushed on each move, so browser Back/Forward move between steps. Enter
continues (ignored in selects, textareas, buttons, links), Shift+Enter goes back. Each step slides in (≤ 200 ms, off under
`prefers-reduced-motion`) and focuses its first visible, enabled control (`StepFrame.initialFocus`, which already skips
hidden inputs). The first-unanswered redirect on `/` with no `step` opens `project`.

Errors from the API appear inline under the question (`InlineError`), with the legacy message-box title in bold when the
legacy showed one. OK stays enabled (Typeform behaviour); while a request runs, OK shows a spinner and Back/OK/Start over
are disabled.

### Step 1 — `project`

- Eyebrow `Start a new policy coherence assessment` (app.py:1170); title `What is this project called?`; help: the legacy
  empty-state subtitle (app.py:1180-1182).
- Field: label `Project Name`, hint `Use a clear descriptive title for this project.`, placeholder
  `e.g. EU Clean Mobility Policy Coherence Assessment` (dialogs.py:842; theme.py:109-112).
- OK: `POST /setup/validate {project_name}`; on 422 `invalid_setup` show `Project Name Required` /
  `Please enter a project name.` inline. On success commit the trimmed name.
- Secondary action **Import from Excel** (legacy `Import from excel`, theme.py:101), with the line
  `Or start from an Excel workbook: one sheet per decision-maker, with the policy names in row 1 and column 1.`
  Upload: `POST /imports/workbook` with only the file (`accept` from `/scales.imports.accept`). On success, if any
  decision-maker, policy or rating already exists, confirm `Replace your answers?` / `The workbook replaces the
  decision-makers, policies and ratings you entered.` (Replace / Cancel). Applying sets decision-makers = sheets,
  policies and codes = the workbook's, matrices = imported ratings (blank `""` kept), keeps a typed project name or uses
  `suggested_project_name` when the field is empty, marks `project`, `decision-makers`, `policies`, `import` and every
  imported matrix step answered, stores the import report, and opens the `import` step (which shows the report).
- Step list label `Project`.

### Step 2 — `decision-makers`

- Title `Who are the decision-makers?`; help `Add one or more decision-maker names.` (theme.py:113); list label
  `Add decision-maker names` (dialogs.py:503).
- List editor (`NameListEditor`, shared with Step 3): starts with the committed names, or 2 empty rows (legacy);
  placeholders `e.g. Expert A`, `e.g. Expert B`, … continuing `AA`, `AB` (dialogs.py:862-872); `Add` button (theme.py:89)
  adds a row and focuses it, disabled at `/scales.rules.max_decision_makers`; a remove button (aria-label
  `Remove row {i}`) on rows 3 and up (legacy); empty rows are ignored (legacy). Enter in any row submits the step, as
  `Return` submitted the legacy dialog (dialogs.py:554); Tab moves between rows.
- OK: `POST /setup/validate {decision_makers: draft names}`. Inline errors with legacy titles: `Decision-Makers Required`
  / `Please enter at least one decision-maker name.`, `Duplicate Decision-Makers` / `Decision-maker names must be
  unique.`, the limit message. If decision-makers that have at least one rated cell are removed (by id), confirm
  `Discard ratings?` / `The removed decision-makers have ratings that will be lost. Continue?` (Continue / Cancel).
  Commit: renamed rows keep their id, matrix, weight text and answered matrix step; new rows get a new id and a blank
  matrix (diagonal = `/scales.ratings.diagonal_label`); removed ids lose matrix, weight text and answered flag;
  `weights` (parsed, keyed by id) and the `weights`/`ties` answered flags are cleared when the set of ids changes;
  a reorder keeps them (ids).
- The one-time refresh toast fires on this step (Settled Decision 3).
- Step list label `Decision-makers`.

### Step 3 — `policies`

- Title `Which policies are you assessing?`; help `Add at least 2 policy names. Each policy gets a code (P1, P2, …)
  that the matrices use.`; list label `Add policy names` (dialogs.py:514); placeholders `e.g. Policy 1`, `e.g. Policy 2`, …
  (dialogs.py:875); `Add` disabled at `max_policies`.
- OK: `POST /setup/validate {policies}` → trimmed names and `codes`. Inline errors: `Too Few Policies` /
  `Please enter at least 2 policy names.`, `Duplicate Policies` / `Policy names must be unique.`, the limit message. If
  removed policies have rated cells in any matrix, confirm `Discard ratings?` / `The removed policies have ratings that
  will be lost. Continue?`. Commit: each matrix is remapped by policy id (kept rows/columns keep their cells, new ones are
  blank, removed ones are dropped); tie choices are keyed by policy ids and survive; codes are replaced by the API's.
- Step list label `Policies`.

### Step 4 — `import` (optional)

- Title `Do you want to import ratings from Excel?`; help `This step is optional: press OK to rate the interactions
  here instead.` and the format line `The workbook needs one sheet per decision-maker. Row 1 and column 1 hold your policy
  names in the same order, and the cells hold rating labels. Sheets named like one of your decision-makers fill that
  decision-maker's matrix; other sheets are added as new decision-makers.`
- Button `Import from Excel` (hidden file input, `accept` from `/scales`). `POST /imports/workbook` with the file and the
  committed `policies` (repeated form field). Errors inline with legacy titles: `policy_list_mismatch` →
  `Policy List Mismatch`, `nothing_imported` → `Nothing Imported` (plus its `data.warning_groups`), any other code →
  `Import Error`; the message is the API's.
- Before merging, count the decision-makers after the merge (existing + sheets whose names match none); if it exceeds
  `/scales.rules.max_decision_makers`, show `Import Error` / `Please enter at most 50 decision-makers.` (the API's limit
  text, with the number from `/scales`) inline and apply nothing.
- Success: if a sheet would replace a decision-maker's matrix that has rated cells, confirm `Replace ratings?` /
  `The workbook has ratings for {names}, who already have ratings here. They will be replaced.` Then apply (same-name
  sheets replace that matrix; other sheets are appended with new ids and blank weights), mark imported matrix steps
  answered, store the report, toast `Import Complete` (no warnings) or `Import Complete with Warnings` (app.py:2991,
  2994) with the API's `summary_message`.
- The step shows the last import report: `summary_message`, then each `warning_groups[]` heading and its messages
  (verbatim, `whitespace-pre-line`).
- OK marks `import` answered and opens the first unanswered step after it (so imported matrices are skipped); if every
  later step is answered, it opens the next step in order.
- Step list label `Import`.

### Steps 5…(4+k) — `matrix-i`

- Title `Decision-maker {i} of {k}: {name}`; help `How does each policy (row) influence each policy (column)? Each row is
  an influencing policy and each column an influenced policy; diagonal cells are fixed to {diagonal_label}.`
- Above the grid: legend `Click a cell to rate it:` (matrix_widget.py:437) and the seven rating badges in `/scales`
  order; progress `{filled}/{total} cells filled` (app.py:2441 format; counted in the browser over off-diagonal cells).
- `MatrixGrid` (copied, adapted): virtualised rows and columns (`@tanstack/react-virtual`, fixed sizes in
  `MATRIX_GRID`: row 40 px, header 40 px, cell 152 px, overscan 4), sticky header row and column, corner text
  `Row → Column`. Column headers show codes; row headers show `{code} {policy}` truncated; both carry
  `title="{code}:  {policy}"` (legacy tooltip, two spaces, matrix_widget.py:499, 524).
- `MatrixCell` (copied, adapted): shadcn `Select` per cell, subscribed to its own cell; trigger coloured with the rating
  tokens; blank shows `--`; options = the seven ratings from `/scales`, plus `Clear rating` (sets `""`) when the cell has
  a value; Delete/Backspace on a focused trigger also clears; diagonal disabled. Accessible name
  `{code_row} {policy_row} → {code_col} {policy_col}`. Tab order row-major; Enter/Space opens the select (StepFrame
  ignores Enter on buttons); first editable cell (row 1, column 2) is the initial focus.
- OK marks the decision-maker's matrix answered (no completeness check here; legacy validates at run).
- Only the open matrix step is mounted. Step list label `Matrix {i}`.

### Review — `review`

- Title `Review your answers`; help `Check your answers, then choose how to combine the ratings. Every cell must be
  rated.`
- On mount and whenever the request changes, `useMatrixCheck` (`POST /matrices/check`, `useQuery` keyed by the request
  hash) supplies `decision_makers[]` (`name`, `filled`, `total`, `complete`, `blank_count`, `blank_cells` capped at
  10) and `aggregation_options`.
- Rows (`ReviewRow`, copied) with `Edit` links: `Project Name` → `project`; `Decision-makers` (names, comma-separated) →
  `decision-makers`; `Policies` (`P1: name, …` from codes) → `policies`; `Import` (`{summary_message}` or
  `Rated in the browser`) → `import`; one `Matrix: {name}` row per decision-maker → `matrix-i`, showing
  `{filled}/{total} cells filled` and, when incomplete, `{blank_count} blank cells` (`blank cell` when it is 1) followed by
  the returned `blank_cells` as `{code_row} → {code_col}`, plus `(+{blank_count - 10} more)` when `blank_count` > 10.
- OK: refetch the check; if `complete` is false, show inline `Incomplete Matrices` and the API's `incomplete_message`
  (legacy text, app.py:2546-2556) and stay. Otherwise store `aggregation_options`, mark `review` answered, open `method`.
- Step list label `Review`.

### Method — `method`

- Title `How should the ratings be combined?`.
- With `method_choice_available`: help `{n} decision-makers detected — choose how to combine their ratings.`
  (aggregation_dialog.py:119); `ChoiceList` (copied) of `/scales.methods` (label + description, L1/L2 texts), keyboard
  letters A–D, default `rules.default_method` (`average`).
- Without it (fewer than `rules.method_choice_min_decision_makers`): help `{n} decision-maker detected.` /
  `{n} decision-makers detected.` and a note `With fewer than {min} decision-makers, the ratings are combined with
  {label of rules.forced_method}. Choosing a method needs at least {min} decision-makers.` (fix for UI report §4 item 12);
  no choice list.
- OK label: `Run Analysis` when this is the last step (forced Average, Average, Median with odd count, Majority);
  otherwise `OK`. Majority OK calls `/aggregation/preview`; ties → store the preview and open `ties`; no ties → run.
- If the stored `aggregationOptions` are unknown for the current decision-makers, the step refetches
  `/matrices/check` first (loading text `Checking the matrices…`).
- Step list label `Method`.

### Weights — `weights` (Weighted only)

- Title `How much weight does each decision-maker carry?`; help `Enter a value between {weight_min} and {weight_max}
  for each decision-maker. Weights must sum to {weight_sum_target} (±{weight_sum_tolerance}).` (fixed legacy subtitle,
  aggregation_dialog.py:477; numbers from `/scales.rules`, formatted `0.0`, `1.0`, `0.01`).
- One text input per decision-maker (label = name, `inputMode="decimal"`, empty by default, legacy), stored live as raw
  text by decision-maker id.
- Live sum: `useWeightCheck` (`POST /weights/check` with the raw texts, `useQuery` keyed by the texts, debounced
  250 ms, `placeholderData: keepPreviousData`) shows `sum_text` right-aligned, in ink when `within_tolerance`, in
  `text-destructive` otherwise (legacy `#2c4a6e` / `#b71c1c`, aggregation_dialog.py:558-568).
- OK (label `Run Analysis`; legacy `Aggregate`): refetch the check; if not `valid`, show `first_error.title` and
  `first_error.message` inline and focus that decision-maker's input; else store `weights` (the API's parsed list, mapped to decision-maker ids by position in the request) and run.
- Step list label `Weights`.

### Median — `median` (Median with an even count only)

- Title `Lower or upper median?`; help `{n} decision-makers detected. Choose which median should be used for
  aggregation.` (aggregation_dialog.py:305-310); `ChoiceList` of `/scales.median_choices`, default
  `rules.default_median_choice`. OK `Run Analysis`. Step list label `Median`.

### Ties — `ties` (Majority with ties only)

- Title `Resolve majority ties` (legacy `Resolve Majority Ties`); help `{k} cell(s) ended in a tie. Please select the
  rating for each one.` (aggregation_dialog.py:672-674).
- `useAggregationPreview` (`useQuery`, request hash) supplies `ties`. One `TieCard` per tie: heading
  `{code_row} → {code_col}` and `{policy_row} → {policy_col}`; `Tied options: {label} ({score:+d})  |  …`
  (aggregation_dialog.py:722-729); `Votes:` `{decision_maker}: {rating}` per decision-maker (new, from `votes`); a select
  labelled `Selected rating` (aggregation_dialog.py:739), options = `tied_options`, empty by default, placeholder
  `Select a rating`. Choices are stored by `(row policy id, column policy id)`. More than 50 ties render in a virtualised
  list.
- OK (label `Run Analysis`; legacy `Confirm`): run; a 422 `unresolved_tie` / `invalid_tie_choice` shows the API message
  inline (API `Please select a rating for cell P{r} → P{c}.`, backend L11).
- If the preview returns no ties (inputs changed), the step shows `No ties remain.` and OK runs.
- Step list label `Ties`.

### Run and Results — `results`

- Run = `POST /analysis` with the request built from the store (`analysis-request.utils.ts`). On success
  `setResults(snapshot, data)`, mark the running step answered, open `results`. On error stay on the step with the API
  message inline; `incomplete_matrices` adds a `Review` link; `unresolved_tie` adds a `Ties` link.
- Results (full width): `Back to inputs` (opens `review`) and `Start over` above the card; card title `Results`,
  subtitle `Analysis complete for "{project}"  |  method: {method_label}  |  {n} {dm_word}` (app.py:2605-2610, where
  `dm_word` is `decision-maker` for 1 and `decision-makers` otherwise; `n` = `aggregation.decision_maker_count`); when `aggregation.method_forced`, the note `Fewer than {min} decision-makers:
  the ratings were combined with {method_label}.`; `OutdatedResultsBanner`; `ExportBar`; `ResultTabs`.
- Results, charts, exports and the AI request always use `snapshot` (never current answers). `ResultTabs` is keyed by
  `snapshotHash`.

### Changing earlier answers

| Change | Effect |
| --- | --- |
| Project name | Kept everywhere; results become out of date (the name is part of the request and the XLSX file name). |
| Rename decision-maker or policy | Matrix, weight text, tie choices and answered flags kept (ids). |
| Add decision-maker | Blank matrix and a new unanswered matrix step (the guard opens it); `weights` cleared; method availability rechecked. |
| Remove decision-maker with ratings | Confirm first; Cancel keeps the draft open and commits nothing. |
| Add policy | Blank row and column in every matrix; matrix steps stay answered; Review lists the new blanks. |
| Remove policy with ratings | Confirm first; matrices remapped by id. |
| Import (step 1) | Confirm before replacing; replaces decision-makers, policies, matrices. |
| Import (`import` step) | Confirm before replacing rated matrices; appends new decision-makers. |
| Edit a cell, method, weights, median, ties | Stored at once; results become out of date. |
| Any change after a run | Results stay, with `Your inputs changed since this analysis. Run again to update.` and `Re-run`. |

**Re-run** (`useRerun`): `/matrices/check` → incomplete: open `review` with the message; method needs weights and the
stored weights are missing or of the wrong count: open `weights`; Majority: `/aggregation/preview` → unresolved ties:
open `ties`; otherwise `POST /analysis` and stay on Results with the new snapshot.

**Start over**: DEMATELab's `StartOverButton` and texts; confirming calls `reset()` and opens `project`.

## Parity Inventory

Legacy text → web text. "Verbatim" means identical characters. "API" means the text is produced by the API exactly as the
backend plan specifies; the web shows it verbatim. File references are `tk-app/<file>:<line>`.

### Shell, header and landing

| Legacy text | Source | Web |
| --- | --- | --- |
| Window title `Policy Coherence Kit` | app.py:313-320 | `APP_NAME` in the header and `<title>` |
| Slogan `Evaluate interactions between policies using multiple decision-makers` | app.py:469 | `APP_SUBTITLE` under the name in `AppHeader` |
| Sidebar logo (waypoints badge) | app.py:404-477 | `AppHeader` badge and `favicon.svg` (Settled Decision 11.7) |
| `Start a new policy coherence assessment` | app.py:1170 | Eyebrow on step `project` |
| `Create a project to define policies, add decision-makers, and evaluate interactions across expert perspectives. The tool supports structured matrix input, aggregation methods, and advanced analytical outputs.` | app.py:1180-1182 | Help text of step `project` (verbatim) |
| `WORKFLOW` and `01 Create a project` … `05 Run aggregation and analysis` | app.py:1206-1236 | Dropped: the step list shows the workflow |
| `New Project` (empty state and sidebar) | app.py:568, 1356 | Dropped: the app opens on step `project`; `Start over` replaces a new project |

### Create Project / Add Decision-Makers dialog

| Legacy text | Source | Web |
| --- | --- | --- |
| `Create Project` / `Add Decision-Makers` (titles, OK buttons) | dialogs.py:456, 539 | Dropped: steps `project`, `decision-makers`, `policies`; OK button `OK` |
| `Define the project, decision-makers, and policy set.` / `Add one or more decision-makers to the current project.` | dialogs.py:457-461 | Dropped (each step has its own help) |
| `Import from excel` | theme.py:101; dialogs.py:495 | `Import from Excel` (fixed capitalisation, item 28) on step `project` and step `import` |
| `Project Name` / `Use a clear descriptive title for this project.` / `e.g. EU Clean Mobility Policy Coherence Assessment` | dialogs.py:842; theme.py:109, 112 | Verbatim on step `project` |
| `Add decision-maker names` / `Add one or more decision-maker names.` | dialogs.py:503; theme.py:113 | Verbatim on step `decision-makers` (list label, help) |
| `Add policy names` / `Add at least 2 policy names.` | dialogs.py:514; theme.py:114 | Verbatim on step `policies` |
| `e.g. Expert {A, B, …, AA}` / `e.g. Policy {n}` | dialogs.py:862-875 | Verbatim placeholders |
| `Add` | theme.py:89 | Verbatim |
| `Cancel` | dialogs.py:521-537 | Dropped (Back) |
| `Project Name Required` / `Please enter a project name.` | dialogs.py:1090 | API (`/setup/validate`), title shown inline |
| `Duplicate Project` / `A project named "{name}" already exists.` | dialogs.py:1093 | Dropped (one project; backend drops the check) |
| `Decision-Makers Required` / `Please enter at least one decision-maker name.` | dialogs.py:1097 | API, inline |
| `Duplicate Decision-Makers` / `Decision-maker names must be unique.` | dialogs.py:1100 | API, inline |
| `Existing Decision-Makers` / `These decision-maker names already exist in the project:\n\n{names}` | dialogs.py:1102-1108 | Not reachable: the whole list is validated at once; imports match by name (Settled Decision 11.1) |
| `Too Few Policies` / `Please enter at least 2 policy names.` | dialogs.py:1111 | API, inline |
| `Duplicate Policies` / `Policy names must be unique.` | dialogs.py:1114 | API, inline |
| `Policies are inherited from the current project.` | dialogs.py:946-976 | Dropped (dead, item 36) |

### Excel import

| Legacy text | Source | Web |
| --- | --- | --- |
| File dialog `Import matrices from Excel workbook`, filter `*.xlsx *.xls` | app.py:2927-2932 | Browser file picker, `accept=".xlsx"` from `/scales` (item 30) |
| `Import Error` / exception text | app.py:2938 | Inline title `Import Error` + API message |
| Header mismatch, unrecognised rating, `empty, skipped`, `fewer than 2 policies`, blank-cell warnings | importer.py:75-173 | API (verbatim messages, L4 grouping) |
| `Nothing Imported` / `No valid matrices were found in the workbook.` | app.py:2959-2963 | Inline title + API message and warning groups |
| `Policy List Mismatch` / `The following sheets have a different policy list and cannot be imported:\n\n  - {dm}…\n\nAll matrices must share the same policy list.` | app.py:2970-2977 | Inline title + API message (`import` step only) |
| `Import Complete` / `{k} matrix/matrices imported successfully.` | app.py:2994-2995 | Toast title verbatim, description API `summary_message` |
| `Import Complete with Warnings` / `{k} matrix/matrices imported.\n\nThe following sheets have blank cells:\n\n{warnings}` | app.py:2987-2992 | Toast title verbatim; report on the `import` step with the API's grouped headings (L4) |
| `openpyxl is required for Excel import.…` | importer.py:62-65 | Dropped (server dependency) |
| Status `Imported {k} matrix/matrices from: {path}` / `Project "{name}" created from import: {path}` | app.py:2998, 3035 | Dropped (status bar); the toast replaces them |

### Matrix editor

| Legacy text | Source | Web |
| --- | --- | --- |
| `Click a cell to rate it:` | matrix_widget.py:437 | Verbatim legend label |
| Seven rating labels and order | constants.py:14-22 | From `/scales.ratings` |
| `<-- Influencing  \|  Influenced -->` | matrix_widget.py:483 | Fixed (item 26): corner `Row → Column` and the step help sentence |
| Header tooltip `{code}:  {policy}` | matrix_widget.py:499, 524 | Verbatim `title` |
| Unrated `--`; diagonal `Neutral` | matrix_widget.py:534-585 | Verbatim (`--`; diagonal label from `/scales`) |
| Status `"{dm}"  --  {filled}/{total} cells filled  \|  P1 -> P2: {rating}` | app.py:2437-2443 | `{filled}/{total} cells filled` above the grid; the rest dropped (status bar) |
| `{dm}'s workspace  .  {n} policies  \|  {n_cells} cells to fill` | app.py:999-1012 | Fixed (item 23): step title names the decision-maker; `{filled}/{total} cells filled` |
| `No decision-makers yet` | app.py:981 | Dropped (validation requires ≥ 1) |
| `Click  "+ Add Decision-Maker"  to add the first matrix.` | app.py:1881 | Dropped (item 22) |

### Run Analysis and aggregation dialogs

| Legacy text | Source | Web |
| --- | --- | --- |
| `Run Analysis` | app.py:891, 926 | OK label of the last question step |
| `No Project` / `Create a project first.`; `No Matrices` / `Add at least 1 decision-maker matrix before running analysis.` | app.py:2535-2544 | Dropped: unreachable (guards and validation) |
| `Incomplete Matrices` / `Please fill all cells before aggregating.\n\n  {dm}: …` | app.py:2546-2556 | Review: title inline + API `incomplete_message` (`P1 → P2` cells, backend L11) |
| `Aggregation Method` (title) | aggregation_dialog.py:86, 109 | Step `method` title `How should the ratings be combined?`; step label `Method` |
| `{n} decision-makers detected — choose how to combine their ratings.` | aggregation_dialog.py:119 | Verbatim help (choice available) |
| `Average` / `Median (Ordinal)` / `Majority Rule` / `Weighted by Importance` and descriptions | aggregation_dialog.py:64-80 | API `/scales.methods` (L1 labels; L2 description) |
| `Cancel` / `Continue` | aggregation_dialog.py:151-160, 341-348 | Back / OK |
| `Decision-Maker Weights` | aggregation_dialog.py:444, 468 | Step `weights` title `How much weight does each decision-maker carry?`; label `Weights` |
| `Enter a value between 0.0 and 1.0 for each decision-maker. Weights must sum to exactly 1.0.` | aggregation_dialog.py:477 | Fixed: `… Weights must sum to 1.0 (±0.01).` (item 21) |
| `Sum: —` / `Sum: {round(total,4)}` | aggregation_dialog.py:517, 558-568 | API `sum_text` |
| `Aggregate` | aggregation_dialog.py:544 | `Run Analysis` |
| `Missing Weight`, `Invalid Value`, `Out of Range`, `Weights Do Not Sum to 1` and messages | aggregation_dialog.py:570-613 | API `/weights/check` errors (L2 sum text), title + message inline |
| `Median Choice` | aggregation_dialog.py:275, 296 | Step `median` title `Lower or upper median?`; label `Median` |
| `{n} decision-makers detected. Choose which median should be used for aggregation.` | aggregation_dialog.py:305-310 | Verbatim help |
| `Lower Median` / `Upper Median` and descriptions | aggregation_dialog.py:263-269 | API `/scales.median_choices` |
| `Resolve Majority Ties` | aggregation_dialog.py:642, 664 | `Resolve majority ties`; label `Ties` |
| `{k} cell(s) ended in a tie. Please select the rating for each one.` | aggregation_dialog.py:672-674 | Verbatim help |
| `P{r} -> P{c}` heading | aggregation_dialog.py:717 | `{code_row} → {code_col}` plus policy names (item 25) |
| `Tied options: {label} ({score:+d})  \|  …` | aggregation_dialog.py:722-729 | Verbatim format from `tied_options` |
| `Selected rating` | aggregation_dialog.py:739 | Verbatim select label |
| `Confirm` | aggregation_dialog.py:768 | `Run Analysis` |
| `Unresolved Tie` / `Please select a rating for cell P{r} -> P{c}.` | aggregation_dialog.py:784-786 | API message inline (`P{r} → P{c}`, backend L11) |
| Status `Analysis complete for "{project}"  \|  method: {label}  \|  {n} decision-maker` or `decision-makers` | app.py:2605-2610 | Results subtitle (verbatim pattern, singular/plural as legacy) |

### Result tabs

| Legacy text | Source | Web |
| --- | --- | --- |
| `Results Insights ({m})`, `Aggregated ({m})`, `Coherence Scores ({m})`, `Range of Influence ({m})`, `PCA ({m})`, `Network Analysis ({m})`, `LLM Interpretation ({m})` | app.py:2629-2635 | Tabs `Results Insights`, `Aggregated`, `Coherence Scores`, `Range of Influence`, `PCA`, `Network Analysis`, `AI Interpretation`; the method appears once in the Results subtitle |
| Panel titles `{Tab}  —  {m}` | coherence_scores_tab.py:185; range_of_influence_tab.py:182; pca_tab.py:186; network_tab.py:376; llm_tab.py:314 | Panel headings without the method suffix |

### Results Insights (results_insights_tab.py)

| Legacy text | Source | Web |
| --- | --- | --- |
| `Key Insights` | :752 | Verbatim card title |
| Story text | :529-559 | API `texts.story` (`positive link`/`negative link` wording, backend L13; `→` arrows, L11); `({code})` occurrences coloured by `insights.rows[].role` (item 4 fix) |
| `Interpretation:` + sentence | :795, :593-604 | API `texts.interpretation_label` + `texts.interpretation_text` |
| Tags `Top Driving Policy: …`, `Strongest Link: …`, `Contested: …` | :815-835 | API `texts.tag_*` |
| `Analysis Overview` | :869 | Verbatim |
| `Policies`, `Decision-makers`, `Aggregation method` | :876-878 | Verbatim labels; values = `policies.length`, `decision_maker_count`, `method_label` |
| `Agreement` (value `{a:.2f}`) | :879 | Label fixed `Decision-maker agreement` with help `Average rank agreement between decision-makers (0 to 1).` (item 24); value API `overview_agreement_text` |
| `System Health`; `Synergy`, `Conflict`, `Neutral/Uncertain` | :912-916 | Verbatim; values API `health.*` shown with `%` (item 31); bar width `max(3, value)%` |
| `Top Driving Policy` / `Top Influenced Policy` cards (hero, `{woi:+.2f} WOI`, `{wii:+.2f} WII`, `N/A`) | :953-1011 | Titles verbatim; hero/value API `texts.top_driver`, `texts.top_dependent` |
| `Strongest Link`, `{s:+.2f} Reinforcing`, `Strongest relation`, `No strong link`, `No non-zero relation` | :1013-1024, :1405 | Title verbatim; API `texts.strongest_link` (value `{s:+.2f} positive link`, backend L13; pair with `→`, L11) |
| `Most Contested`, `Agreement: {r:.2f}`, `Stable`, `⚠ High disagreement`, `Moderate disagreement`, `No contested link` | :1035-1042 | Title verbatim; API `texts.most_contested` (value `Rating agreement: {r:.2f}`, backend L12; `↔` kept); web help `Rating agreement is the share of decision-makers giving the most common rating.` (item 24) |
| `Conflict Ratio`, `{p}%`, `{neg} of {active} active links`, captions | :1058-1072 | Title verbatim; API `texts.conflict_ratio` |

### Aggregated (aggregation_tab.py)

| Legacy text | Source | Web |
| --- | --- | --- |
| `Aggregated score scale:` + seven badges | :319 | Verbatim legend |
| Axis `<-- Influencing  \|  Influenced -->` | aggregation_tab.py (same as editor) | Corner `Row → Column` |
| Cell text `{score:.2f}`, band colour | :82-86, :417-449 | `formatFixed(score, 2)`; colour = rating token of API `bands[i][j]` |
| Cell tooltip `P1 -> P2\nScore: {s:.2f}\nColour band: {rating}`; diagonal `P1 -> P1\nScore: 0.00 (diagonal)` | :443-449 | `title` with `→` (item 25), otherwise verbatim |
| Header tooltip `{code}: {policy}` | aggregation_tab.py | `{code}:  {policy}` (one format everywhere, item 28) |

### Coherence Scores (coherence_scores_tab.py)

| Legacy text | Source | Web |
| --- | --- | --- |
| Legend `OI:` … `WII:` with four descriptions | :197-200 | Verbatim |
| Columns `Policy`, `OI`, `II`, `WOI`, `WII`, `Full Policy Name` | :65-69, :360 | `Code`, `OI`, `II`, `WOI`, `WII`, `Policy` (item 27, matches the XLSX) |
| Header tooltips `Policy code`, `Outgoing Influence\n(non-zero row count)`, `Incoming Influence\n(non-zero col count)`, `Weighted Outgoing\n(row sum)`, `Weighted Incoming\n(col sum)` | :65-69, :320-324 | Verbatim (`title`) |
| Formats: OI/II integers, WOI/WII `+.2f`; band colours | :73-100 | `formatSigned(v, 2)`; colours = tokens of API `*_band` keys |

### Range of Influence (range_of_influence_tab.py)

| Legacy text | Source | Web |
| --- | --- | --- |
| Subtitle `max entropy = {hmax:.4f}` | :190 | Verbatim with `formatFixed(hmax, 4)` |
| `Entropy measures how evenly a policy distributes its outgoing influence. High = spread across many policies. Low = concentrated on few.` | :203-205 | Verbatim, plus `Low also covers policies with no outgoing influence.` (item 15) |
| `Categories:` and `Low` `H < 25% of max` … `High` `H ≥ 75% of max` | :216-225 | Label verbatim; badges and texts from API `entropy_categories` |
| Columns `Policy`, `Entropy`, `Category`, `Full Policy Name` | :375-377, :398 | `Code`, `Entropy` (4 dp), `Category` (badge), `Policy` |
| Tooltips `Policy code`; `Shannon entropy H (base 2)\n0 = fully concentrated\nlog2(n-1) = perfectly distributed`; `Influence distribution category\nbased on fraction of max entropy` | :375-377 | Verbatim; the entropy tooltip adds `\n(max = 1 with 2 policies)` (item 14) |

### PCA (pca_tab.py)

| Legacy text | Source | Web |
| --- | --- | --- |
| `PC1: {p1}%   PC2: {p2}%   Total explained: {total}%` | :195-196 | Verbatim; numbers via `pyFloatStr` from API `pca.explained`, `total_explained` |
| `PCA requires at least 3 policies.` | :158 | API `pca.message` when `pca.valid` is false; no chart drawn |
| `numpy is required for PCA.…` | pca_tab.py | Dropped (server dependency) |
| `Colour by entropy category:` (checkbox, label not clickable) | :289 | `Colour by entropy category` with a clickable label (item 28) |
| Hover `{code}:  {policy}` | :502 | ECharts tooltip (API `points[].label`) |
| `Hover over a point to see the full policy name.` | :322 | `Hover over or tap a point to see the full policy name.` (touch support) |
| `Entropy categories:` + badges (colour mode only) | :389 | Verbatim; API-colour swatches + ink labels |
| `Save as PNG`; `Save PCA plot`; `pca_plot.png`; `PCA plot saved to:\n{path}` | :202, :337-368 | Export bar `Save PCA plot as PNG` and `Save PCA plot as SVG`, files `pca_plot.png` (2400×1800, 300 dpi `pHYs`) / `pca_plot.svg`, current colour mode, generated in the browser; the saved message is replaced by the browser download |

### Network Analysis (network_tab.py)

| Legacy text | Source | Web |
| --- | --- | --- |
| `{n} nodes  \|  {e} directed edges  \|  density: {d}` + `  \|  {k} isolated` | :381-393 | Verbatim from API `network` (density via `pyFloatStr`) |
| `Layout:` with `Circular`, `Force-Directed`, `Spectral`, `Shell` | :64, :411 | `Layout` select; options (`circular` Circular, `force_directed` Force-Directed, `spectral` Spectral, `shell` Shell, in that order) and default `force_directed` from `/scales.network` |
| `Focus Policy:` with `Full Network`, `{code}: {policy}` | :425-431 | `Focus policy` select, verbatim options |
| Legend `Positive`, `Negative`, `Isolated` | :443-445 | Verbatim with API-colour swatches |
| `Ego Network:  {code}  ({policy})`; `{code} has no direct connections.` | :1070, :1078 | Chart title and empty-state text from API `title` / `empty_message` (L8: shown below the node) |
| Hover `{code}:  {policy}` | :975, :1161 | ECharts tooltip (API `nodes[].label`) |
| `Centrality Measures`; `Betweenness: broker role  \|  Closeness: reachability` | :1173, :1180 | Verbatim |
| Columns `Policy`, `Betweenness`, `Closeness`, `Full Name` | :1262 | `Code`, `Betweenness`, `Closeness`, `Policy` (item 27); rows in `centrality_ranking` order; 4 dp |
| `Save as PNG`; `Save Network plot`; `network_plot.png`; `Network plot saved to:\n{path}`; PostScript fallback | :606, :986-1013 | Export bar `Save Network plot as PNG` and `Save Network plot as SVG`, files `network_plot.png` (2400×1800, 300 dpi `pHYs`) / `network_plot.svg`, current layout and focus, generated in the browser; fallback dropped |

### LLM Interpretation (llm_tab.py) → AI Interpretation

| Legacy text | Source | Web |
| --- | --- | --- |
| `API key is used once and never stored.` | :321 | Fixed: `Your API key is sent through our server to the AI provider for this request only. It is never saved, stored or logged.` |
| `Engine:` (`Groq`, `OpenAI`) | :336, :61-77 | `AI Provider` select of six providers from the API |
| `Model:` | :352 | `Model` select (Azure: free-text deployment, DEMATELab text) |
| `API Key:`; `Show key` checkbox | :369, :407 | `API Key`; eye button `Show API key` / `Hide API key` |
| `Generate Interpretation`; `Generating...` | :638, :821 | Verbatim; button disabled with spinner while pending |
| `Calling {engine} / {model} ...`; `Done.`; `Error.` | :822, :838, :846 | Verbatim status (provider label / model or deployment) |
| `API Key Required` / `Please enter your API key before generating.` | :812 | Inline, verbatim (same text as API L9) |
| `LLM Error` / `The request failed:\n\n{error}` | :850 | Toast title `The request failed`, description = API message |
| `Interpretation:` | :561 | Verbatim output label; header lines (`##`, `1.`–`7.`) bold ink with `#` stripped (llm_tab.py:860-875 rule) |
| `Download as TXT` / `Download as PDF`; `policy_interpretation.txt` / `.pdf` | :657-665, :897, :916 | Export bar, verbatim labels and file names (TXT client-side UTF-8, PDF via API) |
| `Nothing to Save` / `Generate an interpretation first.` | :888, :907 | Inline under the export bar, verbatim |
| `Saved` / `Saved to:\n{path}`; `PDF Error` | :903, :922-924 | Dropped (browser download); PDF failures show the API message inline |
| Azure endpoint dialog (DEMATELab) | DEMATELab `explanation.constants.ts` | Verbatim from DEMATELab |

### Exports (app.py)

| Legacy text | Source | Web |
| --- | --- | --- |
| `Export Excel` | app.py:875 | Export bar `Export Excel`; file name from the API's `Content-Disposition` (L10) |
| `Export project: {name}`; `Nothing to Export`; `Export Complete` / `Saved to:\n{path}`; `Export Failed` / `{exc}`; status `Exported to: {path}` | app.py:3043-3071 | Dropped except failure: inline API message |

### Dropped legacy UI (no web equivalent; Settled Decision 4)

| Legacy | Source | Reason |
| --- | --- | --- |
| Sidebar: `PROJECTS`, `No projects available.…`, project rows, `DECISION-MAKERS` +, badges, collapse | app.py:388-704, 2006-2311 | One project per session |
| Top bar `Rename Tab`, `Delete Tab`, `Import Excel`, `Export Excel`, `Run Analysis`, stats | app.py:706-1012 | Steps, inline list editing, export bar |
| `Rename Tab` dialog `New decision-maker name:`, `Renamed to "{name}".`, `Cannot Rename` | app.py:2458-2479 | Rename in step `decision-makers` |
| `Remove Matrix` / `Remove matrix for "{dm}"?`, `Removed "{dm}".`, `Remove Tab`, `Analysis tab removed.` | app.py:2481-2527 | Removal in step `decision-makers` with confirm; result tabs are not removable |
| Project rename/delete texts (dead) | app.py:2323-2368 | Dead in legacy; Start over |
| DM/Analysis pill toggle tooltips `Decision Makers`, `Analysis` | app.py:1499-1864 | Steps and Results |
| Status bar `Ready` and status messages | app.py:1444-1454 | Toasts and inline status |

## Legacy Inconsistencies Settled (UI report §4)

Consistent with the backend plan's Known Tkinter Behaviour Kept (K#) and Label Fixes (L#).

| # | Item | Decision | Why / where |
| --- | --- | --- | --- |
| 1 | Projects cannot be renamed or deleted | Dropped | One project; project name editable on step `project`; `Start over` clears |
| 2 | Two-way network arrows overlap | Fixed in web (display only) | Backend L7/P4: API flags `two_way`; `DirectedNetworkChart` curves the pair to opposite sides |
| 3 | PCA feature columns misaligned | Kept | Maths (backend K1) |
| 4 | Story highlighting broken | Fixed in web | `StoryText` colours each `({code})` by `rows[].role` with the role tokens; display only |
| 5 | Most Contested never empty | Kept | Maths/text parity (K4) |
| 6 | Strongest Link ignores negative edges | Kept | K3 |
| 7 | Top driver/dependent may be negative | Kept | K6 |
| 8 | Sidebar not refreshed after rename/delete | Dropped | No sidebar |
| 9 | Rename without duplicate check; imports can duplicate DMs | Fixed | Every list commit goes through `/setup/validate`; `import` step fills same-name decision-makers instead of duplicating |
| 10 | Removed analysis tab stays in export; export grows per run | Dropped | Stateless current-run export (backend SD 8) |
| 11 | Results go stale silently | Fixed | `OutdatedResultsBanner` + Re-run |
| 12 | Fewer than 3 DMs silently forces Average | Fixed | Explanation on step `method` and the forced note on Results (`method_forced`) |
| 13 | Unresolved ties appear as 0.00 | Fixed | API rejects unresolved ties (backend business rules); ties step required |
| 14 | `max entropy = 1.0000` for n = 2 vs tooltip `log2(n-1)` | Value kept (K5); tooltip text fixed | Tooltip adds `(max = 1 with 2 policies)` |
| 15 | "Low" has two meanings | Kept (K5); explained | Range of Influence text adds `Low also covers policies with no outgoing influence.` |
| 16 | Generate button reverts on hover; old response downloadable after failure; numbered items styled as headers | Fixed / fixed / kept | Button disabled while pending; output and stored text cleared when a new generation starts; header rule kept (K20) for display parity with the PDF |
| 17 | PNGs are screen grabs | Fixed | Browser-rendered PNG 2400×1800 with 300 dpi `pHYs` + SVG from the chart data (Settled Decision 8) |
| 18 | Inconsistent mouse wheel | N/A | Native browser scrolling |
| 19 | Escape on dropdown popups never fires | Fixed | Base UI Select closes on Escape (tested) |
| 20 | Four method spellings | Fixed in API | L1; the web only shows API labels |
| 21 | Weights "sum to exactly 1.0" | Fixed | L2 in API texts; web help text `Weights must sum to 1.0 (±0.01).` |
| 22 | Hint names a nonexistent `+ Add Decision-Maker` | Dropped | No empty project page |
| 23 | `{n} cells to fill` shows the total | Fixed | `{filled}/{total} cells filled` |
| 24 | "Agreement" means two metrics | Fixed in web and API | Overview label `Decision-maker agreement` + help; Most Contested value is the API's `Rating agreement: {r:.2f}` (backend L12) with the help `Rating agreement is the share of decision-makers giving the most common rating.` |
| 25 | Mixed arrows `->`, `→`, `↔`, `<-- … -->` | Fixed everywhere | One arrow `→` with spaces (`P1 → P2`) in web texts (tie headings, tooltips, blank lists, aria-labels) and in every API text and message (backend L11). Only the Most Contested main text keeps `↔` (undirected disagreement) |
| 26 | Axis label above the influenced columns | Fixed | Corner `Row → Column` + help sentence |
| 27 | Same columns named differently | Fixed | Web tables use `Code` / `Policy` like the XLSX |
| 28 | Small wording differences | Decided per text | `(non-zero col cells)` vs `(non-zero col count)` kept verbatim (both true); `Import from excel` → `Import from Excel`; British `Colour` kept (legacy UI spelling); tab title separators dropped with the suffix; header tooltips unified to `{code}:  {policy}` |
| 29 | Skipped sheets under "blank cells" heading | Fixed in API | L4 grouped headings |
| 30 | File picker offers `.xls` | Fixed | `accept=".xlsx"`; API L5 |
| 31 | `Neutral/Uncertain` colour conflict; no `%` | Code colour kept (`#2563EB`); `%` added | The theme token was unused; values are percentages by formula |
| 32 | WOI/WII per-cell thresholds on sums | Kept | K18; colours from API band keys |
| 33 | `hmax` stored in every row; PCA imports private colours | N/A | API returns `hmax` once; colours are tokens |
| 34 | Dead dialogs and helpers | Dropped | Not ported |
| 35 | Dead Results Insights views | Dropped | Backend Non-Goals; only displayed cards are built |
| 36 | Fixed-policy section unreachable | Dropped | — |
| 37 | `theme.py` duplicates/conflicts | Dropped | Web theme tokens replace them |
| 38 | Copied code between files | N/A | Shared components (`EChart`, `DirectedNetworkChart`, `ScatterChart`, `RatingBadge`, `CodeTable`) |
| 39 | `__init__.py:run()` launcher | Dropped | `tk-app/` untouched |
| 40 | Unused `style_button` / theme constants | Dropped | — |
| 41 | Story and Strongest Link call any positive link `Reinforcing` and any negative link `Constraining`, clashing with the rating labels (owner decision 2026-11-18) | Fixed in API | Backend L13 (`positive link` / `negative link` wording); the web shows the API text |
| 42 | `decision-maker(s)` counts (owner decision 2026-11-18) | Fixed | Every web text that states a decision-maker count picks `decision-maker` for 1 and `decision-makers` otherwise (Results subtitle, method help, forced note, Review); backend L14 for API texts |

## Target Layout

```text
apps/web/
  package.json  pnpm-lock.yaml  pnpm-workspace.yaml  biome.json  components.json  tsconfig.json  tsr.config.json
  vite.config.ts  vitest.config.ts  .env.example  .dockerignore  .gitignore  .vscode/settings.json
  Dockerfile.dev  Dockerfile.prod  AGENTS.md  CLAUDE.md  README.md  scripts/.gitkeep
  public/  favicon.svg
  src/
    router.tsx  routeTree.gen.ts  styles.css  env.ts (+test)  vite-env.d.ts
    routes/  __root.tsx  index.tsx  status.tsx
    lib/  utils.ts  query-client.ts (+test)  query-devtools.tsx
    components/
      ui/        (shadcn, copied) alert-dialog badge button card checkbox dialog input scroll-area select separator
                 sonner tabs; added by CLI: tooltip
      general/   AppLayout AppHeader AppFooter PageHeader SectionCard InlineError DownloadButton NotFound
                 (+ AppHeader/AppFooter tests)
        charts/  EChart (themed base: ClientOnly + lazy import, init/dispose, ResizeObserver, theme from CSS
                 variables, aria, ref API `getInstance`/`download`) DirectedNetworkChart ScatterChart
                 ChartToolbar (Reset view) ChartLegend (+ EChart/DirectedNetworkChart/ScatterChart tests)
      page-specific/
        assessment/   FlowShell FlowStep StepFrame StepNavigation StepProgress StepList StartOverButton
                      ResetConfirmDialog ChoiceList NameListEditor
                      ProjectStep WorkbookStartAction DecisionMakersStep PoliciesStep ImportStep ImportReport
                      MatrixStep MatrixGrid MatrixCell RatingLegend RatingBadge ReviewStep ReviewRow
                      MethodStep WeightsStep MedianStep TiesStep TieCard
                      ResultsCard OutdatedResultsBanner ExportBar ResultTabs
                      InsightsPanel KeyInsightsCard StoryText OverviewCard HealthCard SignalCard
                      AggregatedPanel AggregatedGrid CoherenceScoresPanel RangeOfInfluencePanel CodeTable
                      PcaPanel NetworkPanel CentralityTable
                      ExplanationPanel ExplanationSettings ApiKeyInput AzureEndpointDialog InterpretationText
                      (co-located *.test.tsx per area: SetupSteps, ImportStep, MatrixStep, ReviewStep, AggregationSteps,
                      FlowShell, FlowHistory, StartOverButton, ResultsCard, InsightsPanel, ChartPanels,
                      ExplanationPanel)
        status/       ApiHealthCard (+test) StatusRow
    constants/  api.constants.ts  query.constants.ts  layout.constants.ts  health.constants.ts  flow.constants.ts
                steps.constants.ts  import.constants.ts  results.constants.ts  insights.constants.ts
                explanation.constants.ts  theme.constants.ts  chart.constants.ts (export size 800×600, pixel ratio 3,
                dpi 300, file names, UI texts)
    interfaces/ api.interface.ts  health.interface.ts  scales.interface.ts  setup.interface.ts  check.interface.ts
                weights.interface.ts  aggregation.interface.ts  analysis.interface.ts  insights.interface.ts
                chart.interface.ts  import.interface.ts  explanation.interface.ts  project.interface.ts
    services/   health scales setup matrices weights aggregation analysis export charts import explanation
                (*.service.ts, each with *.service.test.ts)
    hooks/      health scales setup matrix-check weights aggregation analysis rerun network-chart export import explanation
                flow refresh-notice object-url (*.hook.ts; tests for flow, refresh-notice, rerun)
    store/      project.store.ts (+test)
    utils/      api.utils.ts  api-error.utils.ts  download.utils.ts  format.utils.ts  flow.utils.ts  matrix.utils.ts
                project-state.utils.ts  analysis-request.utils.ts  interpretation.utils.ts  content-disposition.utils.ts
                echarts.utils.ts (tree-shaken `echarts/core` registration)  chart-theme.utils.ts  chart-export.utils.ts
                (PNG `pHYs`, SVG)  network-chart.utils.ts  pca-chart.utils.ts (pure option builders)
                (each with *.test.ts where it has logic)
    test/       render.tsx  select.ts  fixtures/{scales,setup,check,aggregation,analysis,import,explanation}.fixture.ts
                contrast.ts  repository-rules.test.ts  theme-contrast.test.ts
```

Notes: the page folder is `assessment` (not DEMATELab's `analysis`) because the flow is a policy coherence assessment;
DEMATELab components are copied into it and renamed only where their DEMATEL meaning changes. `constants/` holds only
UI text the API does not provide (step titles and help, button labels, dialog texts, file names, column headers,
tooltips). Any file approaching 300 lines is split by responsibility.

Key interfaces (types only, to remove ambiguity):

```ts
interface NamedItem { id: string; name: string }          // ids from crypto.randomUUID()
interface ProjectState {
  projectName: string; decisionMakers: NamedItem[]; policies: NamedItem[]; codes: string[];
  matrices: Record<string, string[][]>;                     // dmId → n×n labels, "" = blank, aligned to policies
  answered: FixedStepId[]; answeredMatrices: string[];      // dm ids
  importReport: ImportReport | null;
  method: string | null; weightTexts: Record<string, string>; weights: Record<string, number> | null;  // dmId → weight
  medianChoice: string | null; tieChoices: Record<string, string>;   // `${rowPolicyId}>${colPolicyId}` → label
  aggregationOptions: (AggregationOptions & { forNames: string }) | null; tieCount: number | null;
  snapshot: AnalysisRequest | null; snapshotHash: string; results: AnalysisData | null;
  interpretationText: string;
  chartView: { pcaColourByEntropy: boolean; networkLayout: string | null; networkFocus: number | null };
}
```

`analysis-request.utils.ts` builds `ProjectInput` / `AnalysisRequest` exactly as the backend contract: trimmed names;
`ratings` from `matrices[dm.id]`; `aggregation = {method: method ?? rules.default_method, weights: method === "weighted"
? decisionMakers.map((dm) => weights[dm.id]) : null, median_choice: method === "median"
? medianChoice ?? rules.default_median_choice : null,
tie_choices: method === "majority" ? [{row, col, rating}] (indices from policy ids) : []}`. `requestKey`/`hashString`
are DEMATELab's.

## Phases

Order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8. Each phase writes its tests and ends with `make check-web` (or the host commands
in Testing And Validation) passing. Never edit `routeTree.gen.ts` by hand.

### Phase 1: Scaffold from DEMATELab

1. Copy from `dematelab/apps/web` (commit `6a76ae2`): `package.json`, `pnpm-workspace.yaml`, `pnpm-lock.yaml`,
   `biome.json`, `components.json`, `tsconfig.json`, `tsr.config.json`, `vite.config.ts`, `vitest.config.ts`,
   `.env.example`, `.dockerignore`, `.gitignore`, `.vscode/settings.json`, `Dockerfile.dev`, `Dockerfile.prod`,
   `scripts/.gitkeep`, `src/{router.tsx,env.ts,env.test.ts,vite-env.d.ts,styles.css}`, `src/lib/*`,
   `src/routes/{__root,status}.tsx`, `src/components/ui/*`, `src/components/general/*` (except `NumberStepper` and its
   test, and `utils/stepper.utils.ts`: PCK has no number steps), `src/components/page-specific/status/*`,
   `src/utils/{api,api-error,download}.utils.ts` (+ tests), `src/interfaces/{api,health}.interface.ts`,
   `src/services/health.service.ts` (+ test), `src/hooks/{health,object-url}.hook.ts`, `src/constants/{api,query,health,layout}.constants.ts`,
   `src/test/{render.tsx,select.ts}`. Do not copy `.env`.
2. Adapt (conventions report Finding 4 and Finding 9):
   - `package.json`: `name: "policycoherencekit-web"`; `dev`/`preview` on `--port 3001 --strictPort`; remove
     `html-to-image`; keep every other version and `packageManager: "pnpm@12.9.1"`. Run `pnpm install` to update the
     lock (only `html-to-image` may disappear and only `echarts`, `zrender` and `tslib` may be added in step 2; if any
     other version changes, stop and report).
   - `vitest.config.ts` `VITE_API_BASE_URL: "http://localhost:50002"`; `.env.example` `VITE_API_BASE_URL=http://localhost:50002`;
     `env.ts` comment and `env.test.ts` URLs; `utils/api.utils.ts` comment; tests' URLs.
   - `Dockerfile.dev` `EXPOSE 3001`; `Dockerfile.prod` `ENV PORT=3001`, `EXPOSE 3001`.
   - `components/ui/sonner.tsx` docstring names Policy Coherence Kit.
   - `layout.constants.ts`: `APP_NAME = "Policy Coherence Kit"`, `APP_SUBTITLE` = the legacy slogan, `APP_FULL_NAME =
     "Policy Coherence Kit"`, `FOOTER_LINKS = []`, `PAGE_TITLES = {HOME: "Policy Coherence Kit", STATUS: "Status · Policy
     Coherence Kit"}`, `NOT_FOUND_TEXT.LINK = "Go to the assessment"`; remove `APP_LOGO_PATH`.
   - `api.constants.ts` endpoints for the whole contract (`/health`, `/scales`, `/setup/validate`, `/matrices/check`,
     `/weights/check`, `/aggregation/preview`, `/analysis`, `/analysis/export/xlsx`, `/analysis/charts/network`
     (JSON chart data), `/imports/workbook`, `/explanations`, `/explanations/providers`, `/explanations/export/pdf`).
   - Do not copy `components/general/ZoomableImage.tsx` (no image charts).
   - Add `echarts@6.1.0` (exact pin) with `pnpm add`; the lock may gain only `echarts`, `zrender` and `tslib` besides
     losing `html-to-image`.
   - `routes/index.tsx`: placeholder component until Phase 4.
3. Add `src/test/repository-rules.test.ts` (`// @vitest-environment node`): walks `apps/web` (skipping `node_modules`,
   `.output`, `.nitro`, `.tanstack`, `dist`, `coverage`, `public`, `src/routeTree.gen.ts`) and asserts every
   `.ts/.tsx/.js/.mjs/.css` file has ≤ 300 lines, and that no such file contains the string `tk-app`. The test excludes
   its own file from the `tk-app` check. Code comments that cite legacy sources write the path without the prefix
   (`app.py:1170`, `aggregation_dialog.py:477`), as this plan does.
4. `apps/web/CLAUDE.md` = `@AGENTS.md`; placeholder `AGENTS.md` and `README.md` (completed in Phase 8).
5. Grep `apps/web` (excluding `node_modules`, `pnpm-lock.yaml`, `.output`, `src/routeTree.gen.ts` and
   `src/test/fixtures/`) for `3000|50001|DEMATELab|dematelab|DEMATEL|qt-app`; nothing may remain except digit runs
   inside longer numbers. Also review every hit of `factor|cause|effect|solver|threshold` (DEMATEL vocabulary) and
   remove it from copied code and texts. Allowed hits: `useEffect`/`useLayoutEffect` and other React or library APIs,
   `threshold` where it describes legacy PCK rules (entropy `threshold_text`, band thresholds) and fixture floats;
   `expert` stays only in the legacy placeholders and help text.
6. Request deferred edits D1–D3 from the coordinator (Phase 8 list). The coordinator applies them as soon as this
   scaffold lands, so `make dev` builds the `web` service from then on.

Done when `/` and `/status` render on `http://localhost:3001` (header, footer, `/status` showing the API healthy) and
the host commands in Testing And Validation (`pnpm install --frozen-lockfile`, `format:check`, `lint`, `typecheck`,
`test`, `build`) pass. Until D1–D3 are applied the page may be served with `pnpm run dev` on the host against the API
container; once they are applied, `make dev` and `make check-web` are the done criteria for every later phase.

### Phase 2: Theme and layout

1. `styles.css`: replace DEMATEL domain tokens with the Theme domain tokens (`--rating-*`, `--value-*`, `--count-*`,
   `--entropy-*`, each with `-foreground`; `--role-*`; `--health-*`), registered in `@theme inline`. Keep the pointer
   cursor and disabled cursor rules of DEMATELab's base layer.
2. `constants/theme.constants.ts`: maps API keys to token class names (`RATING_TOKENS["Reinforcing"] =
   "bg-rating-reinforcing text-rating-reinforcing-foreground"`, likewise value/count band keys and entropy labels,
   roles). `RatingBadge` uses it.
3. `AppHeader`: `WaypointsIcon` (`lucide-react`) in a `size-8 rounded-md bg-[#1f2937] text-[#f5f7fa]` badge, name and
   subtitle; `public/favicon.svg` (the Lucide waypoints paths, ISC licence comment, on a `#1f2937` rounded square); head
   link `{rel: "icon", type: "image/svg+xml", href: "/favicon.svg"}`; remove the PNG links. Update header/footer tests.
4. `src/test/contrast.ts` (WCAG luminance helper, test-only) and `src/test/theme-contrast.test.ts`: reads `styles.css`,
   asserts every domain pair in the Theme table and the base ink/muted pairs reach ≥ 4.5:1, and that unchanged pairs equal
   the legacy values listed in the test fixture of `/scales` colours.
5. Re-measure with a contrast checker; if any value differs from the Theme table, stop and report (only lightness may
   change).

Done when the theme test passes and `/status` renders in the new theme at 320 px and desktop widths.

### Phase 3: API layer

Depends on: the backend API Contract (endpoints may still be mocked; see Gate G1).

1. `interfaces/*.interface.ts`: Zod schemas for every contract model: `ScalesData`, setup validate request/response,
   `MatrixCheckData` (`decision_makers: [{name, filled, total, complete, blank_count, blank_cells}]`), weight check, `AggregationData` (ties with `tied_options`, `votes`, `chosen`), `AnalysisData`,
   `InsightsData` (including `texts`), `NetworkChartData` (`nodes`, `edges` with `two_way`, `canvas`, `title`,
   `empty_message`, `stats`), `AnalysisData.pca` (`points[].label`, `bounds`, axis labels, `stats_text`), `ImportData` (`warning_groups`), explanation models
   (copied), `HealthCheckData`. Numbers are `z.number()` (accepting `-0`); nullable where the contract says `| null`.
2. `utils/api.utils.ts`: extend `ApiError` with `code: string | null` and `data: unknown` read from the error body
   (`apiErrorBodySchema` gains `data: z.unknown().nullish()`); add `apiFile(path, init) → {blob, filename}` reading
   `Content-Disposition` through `content-disposition.utils.ts` (`filename*=UTF-8''…` preferred, then `filename="…"`,
   then a supplied fallback).
3. `utils/format.utils.ts`: Python-compatible display formatting of API numbers, never re-rounding beyond the API's
   precision: `formatFixed(value, digits)` (like `f"{v:.Nf}"`, `-0.0` → `-0.00`), `formatSigned(value, digits)` (like
   `+.Nf`: `0.0` → `+0.00`, `-0.0` → `-0.00`), `pyFloatStr(value)` (like `str(float)`: `42.0` → `"42.0"`, `0.123` →
   `"0.123"`), `formatInt(value)`. Tests cover `-0`, signs, integers-as-floats and 2/4 dp.
4. Services (one per area, `apiData` with `apiResponseSchema(...)`, binaries with `apiFile`/`apiBlob`): `scales`,
   `setup` (`validateSetup`), `matrices` (`checkMatrices`), `weights` (`checkWeights`), `aggregation` (`previewAggregation`),
   `analysis` (`runAnalysis`), `export` (`exportXlsx`), `charts` (`getNetworkChartData(request, layout, focus)` → `NetworkChartData`), `import` (`importWorkbook(file,
   policies?)` as multipart with repeated `policies`), `explanation` (`getExplanationProviders`, `explain`,
   `exportInterpretationPdf(text)`).
5. Hooks: `useScales` (`staleTime: Infinity`); `useValidateSetup` (mutation); `useMatrixCheck` (query, request hash);
   `useWeightCheck` (query, debounced texts); `useAggregationPreview` (query, request hash); `useRunAnalysis` (mutation →
   `setResults`); `useCurrentRequest`, `useResultsOutdated` (DEMATELab pattern); `useNetworkChartData` keyed by
   `["network-chart", snapshotHash, layout, focus]` with `staleTime: Infinity, retry: false` (PCA needs no query); `useExportFile` (mutation per
   kind); `useImportWorkbook` (mutation); `useExplanation` (DEMATELab ref pattern, `gcTime: 0`),
   `useExplanationProviders`.
6. `test/fixtures/*.fixture.ts`: API-shaped fixtures built from the backend contract (for example a 5 × 3 majority run
   with two ties, a 2-decision-maker forced Average, a 2-policy PCA-invalid case, network chart data for the full view
   with a two-way pair and an isolated node, and an ego view with an empty state).
7. Service tests with `vi.stubGlobal("fetch")`: request bodies and query strings, Zod parsing, 4xx error bodies (message,
   `code`, `data`), blob downloads with `Content-Disposition`, multipart fields.

Done when every contract endpoint has a typed service and a passing test.

### Phase 4: Flow shell and setup steps

1. `store/project.store.ts` with the state above and actions: `setProjectName`, `commitDecisionMakers(rows)`,
   `commitPolicies(rows, codes)`, `setCell(dmId, row, col, value)` (copies only the changed row), `applyWorkbook(mode,
   data)` (`"replace"` | `"merge"`), `markAnswered`, `markMatrixAnswered`, `setMethod`, `setWeightText`, `setWeights`,
   `setMedianChoice`, `setTieChoice`, `setAggregationOptions`, `setTieCount`, `setResults`, `setInterpretationText`,
   `setChartView`, `reset`. Pure helpers (remap matrices by ids, rated-cell detection for confirms, row id assignment) in
   `utils/project-state.utils.ts` and `utils/matrix.utils.ts`. Unit tests cover every rule in "Changing earlier
   answers", including that matrices and answered flags follow ids across rename/remove/reorder and both import modes.
2. `utils/flow.utils.ts` (DEMATELab's, with the PCK step ids and `questionSteps(state)`), `hooks/flow.hook.ts`,
   `constants/steps.constants.ts` (titles, labels, help texts from the Flow section), `constants/flow.constants.ts`
   (`FLOW_TEXT`, `START_OVER_TEXT`, `RESET_CONFIRM_TEXT`, `REFRESH_NOTICE` with step `decision-makers` and key
   `policycoherencekit:refresh-notice-shown`).
3. Copy and adapt `FlowShell` (loads `/scales`; loading `Loading the assessment options…`, error `The assessment options
   could not be loaded from the API.`, `Try again`), `FlowStep`, `StepFrame` (unchanged: Enter / Shift+Enter, focus,
   animation), `StepNavigation`, `StepProgress`, `StepList`, `StartOverButton` (opens `project`), `ResetConfirmDialog`,
   `ChoiceList`, `hooks/refresh-notice.hook.ts`.
4. `ProjectStep`, `WorkbookStartAction`, `DecisionMakersStep`, `PoliciesStep`, `NameListEditor` per the Flow section
   (drafts in component state; `/setup/validate` on OK; confirms on removals; commit).
5. Tests (Testing Library, mocked services, mocked router as DEMATELab): each step's happy path and legacy error texts;
   guards redirect to the first unanswered step; Back/OK/Enter/Shift+Enter; browser history (`FlowHistory`); Start over
   hidden when empty, confirm, red text on hover class; draft discarded on Back; removal confirm Cancel keeps data;
   refresh toast once.

Done when steps `project` → `policies` work end to end against the API (or fixtures) and all tests pass.

### Phase 5: Import, matrices, review, method, weights, median, ties, run

1. `ImportStep` and `ImportReport` (both modes' report), `WorkbookStartAction` finished (replace confirm), hidden file
   inputs reset after each pick so the same file can be re-picked (DEMATELab `takeFile`).
2. `MatrixStep`, `MatrixGrid`, `MatrixCell`, `RatingLegend`, `RatingBadge` per the Flow section. Only the open matrix
   step is mounted.
3. `ReviewStep`, `ReviewRow` with `/matrices/check`.
4. `MethodStep`, `WeightsStep`, `MedianStep`, `TiesStep`, `TieCard`; the run orchestration in `hooks/analysis.hook.ts`
   (preview for Majority, then `/analysis`), error links to Review/Ties.
5. Tests: import errors and warnings (titles, grouped headings), merge vs replace and their confirms, the merge
   decision-maker limit (nothing applied), `accept=".xlsx"`;
   matrix cell select/clear/Delete key, diagonal disabled, `{filled}/{total}`; Enter inside a cell select does not
   advance; review blocks on `incomplete_message`; method forced explanation with 2 decision-makers; even/odd median step
   visibility; weights live `sum_text` and error focus; ties step rendering (`Tied options`, votes) and run errors;
   successful run opens Results.

Performance check (manual, recorded): a 100 × 100 matrix stays responsive; changing one cell re-renders only that cell
(React DevTools Profiler).

Done when the full flow reaches Results against the API for Average, Median (even), Majority with ties and Weighted.

### Phase 6: Results tabs and exports

1. `ResultsCard` (header, subtitle, forced note), `OutdatedResultsBanner` (Re-run via `hooks/rerun.hook.ts`),
   `ResultTabs` (shadcn Tabs as a horizontally scrolling segmented control; only the open tab mounted, AI tab
   `keepMounted`; default `Results Insights`).
2. `InsightsPanel` (grid: Key Insights spans 2 columns on `lg`, one column below `md`), `KeyInsightsCard`, `StoryText`,
   `OverviewCard`, `HealthCard`, `SignalCard` (Top Driving Policy, Top Influenced Policy, Strongest Link, Most Contested,
   Conflict Ratio).
3. `AggregatedPanel` + `AggregatedGrid` (read-only virtualised grid sharing `MATRIX_GRID` sizes, cells coloured by
   `bands`, tooltips per Parity Inventory).
4. `CoherenceScoresPanel`, `RangeOfInfluencePanel`, `CodeTable` (shared striped table, horizontal scroll, header
   tooltips).
5. Chart components (`components/general/charts/`, all generic, no PCK maths):
   - `utils/echarts.utils.ts` registers the tree-shaken modules (Settled Decision 8) once and exports `echarts`.
   - `EChart`: rendered inside TanStack Router `ClientOnly` with a skeleton fallback; the module chunk is loaded with
     dynamic `import()` (SSR-safe; no `window` access at module scope); `init` on mount with the theme from
     `chart-theme.utils.ts` (`buildChartTheme()` reads the CSS variables listed in Theme), `setOption(option, {notMerge:
     true})` on change, `ResizeObserver` → `resize()`, `dispose` on unmount; props `option`, `ariaDescription`,
     `height`/`aspectRatio`, `renderer`; an imperative ref with `resetView()` and `download(kind: "png" | "svg",
     fileName)`.
   - `utils/chart-export.utils.ts`: `download` creates an off-screen 800×600 instance with the same option (canvas
     renderer, `pixelRatio: 3`, white background, after `document.fonts.ready`) → PNG data URL → inserts a `pHYs`
     chunk (11811 px/m = 300 dpi) before `IDAT` with CRC → `saveBlob`; SVG through an off-screen `SVGRenderer`
     instance and `renderToSVGString()`. Interactive-only components (dataZoom slider, toolbox) are excluded.
   - `DirectedNetworkChart` (props: `NetworkChartData`, colours from `/scales`): `graph` series, `layout: "none"`,
     node `x/y` from the API in a square box, `symbolSize = 2·radius`, `itemStyle.color = fill`, white bold code labels,
     `edgeSymbol: ["none", "arrow"]`, per-edge `lineStyle.color`/`width`, `curveness` ±0.2 for `two_way` edges (sign by
     `source < target`, verified visually so the arrows separate), ego `edgeLabel` from `label`, `roam: true`,
     `draggable: false`, tooltip formatter returning the API `label` (escaped), legend Positive/Negative/Isolated as
     categories that toggle edges/nodes.
   - `ScatterChart` (props: points, bounds, axis labels, colour mode, colours): `scatter` series, symbol size 32, code
     labels inside, value axes with `min/max` from `bounds`, dashed `markLine` at x = 0 and y = 0 in `--line-strong`,
     axis names from the API, `dataZoom` inside (x and y), tooltip from `label`, legend of entropy categories when
     colour mode is on.
   - `ChartToolbar` (Reset view) and `ChartLegend` (API-colour swatches, ink labels, shadcn badge look) are shared.
   - `ariaDescription` per chart: `aria.enabled` with a description built from the API texts (stats line, layout,
     node and edge counts or PCA stats); the tables beside the charts remain the text alternative.
6. `PcaPanel` (stats `pca.stats_text`, colour checkbox, `ScatterChart`, hint) and `NetworkPanel` (stats `stats.text`,
   Layout and Focus selects, `DirectedNetworkChart` with title/empty state from the API, `CentralityTable` in
   `centrality_ranking` order). Controls write `chartView` in the store. PCA invalid → `pca.message`, no chart.
   Layout: network 2/3 and table 1/3 from `lg`, stacked below; charts keep their aspect ratio (network square, PCA
   4:3).
7. `ExportBar`: `Export Excel` (`exportXlsx(snapshot)`, file name from `Content-Disposition`, fallback
   `coherence.xlsx`), `Save Network plot as PNG` / `as SVG` (`network_plot.png` / `.svg`, from the cached
   `NetworkChartData` of the current layout/focus through `chart-export.utils.ts`; disabled until it is loaded),
   `Save PCA plot as PNG` / `as SVG` (`pca_plot.png` / `.svg`, current colour mode; disabled with `PCA requires at
   least 3 policies.` as its title when PCA is invalid). The export bar works from any tab: it builds the option with
   the pure builders and renders off-screen, so the chart tab need not be open. `Download as TXT` (client-side `Blob` `text/plain;charset=utf-8`,
   `policy_interpretation.txt`), `Download as PDF` (`/explanations/export/pdf`, `policy_interpretation.pdf`). TXT/PDF
   with an empty `interpretationText` show `Generate an interpretation first.` inline. Downloads use `saveBlob`.
8. Tests: tab switching and default tab; story code colouring by role; overview/health/signal texts and `%`; table
   headers and formats (`-0.00`, `+0.00`, 4 dp); band classes from API keys; chart tests (Vitest, jsdom) with
   `vi.mock("@/utils/echarts.utils")` returning a fake instance that records `init`/`setOption`/`resize`/`dispose`/
   `getDataURL` calls (no canvas in jsdom): `EChart` disposes on unmount, resizes on `ResizeObserver`, renders the
   fallback on the server path; option builders (pure, no mock) for node positions, colours, widths, opposite
   curveness on a two-way pair, ego labels, title/empty message, tooltip label text, markLines, axis bounds, category
   colours, aria description; `chart-export.utils` inserts a valid `pHYs` chunk (300 dpi, correct CRC) into a fixture
   PNG and names files correctly; one `ScatterChart` smoke test with the real `SVGRenderer` and `ssr: true`
   (`renderToSVGString`) checks codes appear in the SVG; panels' loading, error and success states; Layout/Focus
   changes refetch with the right query key; export calls with the snapshot (not current answers) and file names;
   outdated banner and Re-run branches.
9. Bundle budget: `pnpm run build`, then measure the gzip size of the chunk(s) containing `echarts`/`zrender` (for
   example `gzip -c <chunk> | wc -c` over `.output/public/assets/*.js`); record it in the implementation report. Over
   250 KB gzip → stop and report (do not add a second library or drop features silently). Confirm the initial route
   chunk does not contain `echarts`.

Done when every Results tab matches the Parity Inventory for a fixture and a live API run, both charts are
interactive, and the chart chunk is within budget.

### Phase 7: AI Interpretation

1. Copy `ExplanationPanel`, `ExplanationSettings`, `ApiKeyInput`, `AzureEndpointDialog`, `hooks/explanation.hook.ts`,
   `interfaces/explanation.interface.ts`, `constants/explanation.constants.ts`, and adapt:
   - texts per the Parity Inventory (title `AI Interpretation`; privacy note; `Generate Interpretation` /
     `Generating...`; status `Calling {provider} / {model} ...`, `Done.`, `Error.`; missing key
     `Please enter your API key before generating.`; toast title `The request failed`);
   - NOTE text: `This section provides an AI-assisted interpretation of the policy coherence results. After choosing a
     provider and model and entering an API key, a structured interpretation is generated covering overall coherence,
     key synergies and conflicts, influential policies, range of influence, network structure and strategic
     recommendations.` (summarises the legacy prompt's seven sections, `llm_tab.py:86-94`);
   - clear the key (`setApiKey("")`) in both `onSuccess` and `onError`; clear the output and `interpretationText` when a
     generation starts; on success store the text with `setInterpretationText`;
   - `InterpretationText` renders the output with `utils/interpretation.utils.ts` `isHeaderLine` (strip, starts with
     `##` or `1.`–`7.`) as bold ink lines with leading `#` removed, other lines as plain text.
2. Tests (DEMATELab's `ExplanationPanel.test.tsx` adapted): request body uses the snapshot; key never in the store,
   query cache, mutation variables or URLs; key field empty after success and after failure; Azure dialog and disabled
   Generate until a deployment is typed; provider change resets the model; header rendering; TXT/PDF downloads.

### Phase 8: Docs, deferred cross-area edits and finish

1. `apps/web/AGENTS.md`: DEMATELab's file rewritten for PCK (stack, commands with port 3001 / API 50002, file
   organisation with `page-specific/assessment`, conventions, the 300-line and `tk-app` test, architecture: layout, flow
   and steps, changing answers, store rule with ids and snapshot, matrix editor, results and the chart components (base `EChart`, per-type charts, theme from CSS variables, browser
   downloads, no chart maths), AI key rule
   including clearing after success/failure, number formatting rule, theme tokens and the contrast rule, environment,
   testing, pitfalls including "no policy-coherence maths in the browser").
2. `apps/web/README.md` (DEMATELab's shape; URLs `http://localhost:3001` and `http://localhost:50002`; "Nothing is
   saved: a reload starts a new assessment"; logo note) and `apps/web/CLAUDE.md` (`@AGENTS.md`).
3. Deferred cross-area edits (the frontend implementer lists them in its report with exact diffs). The coordinator
   applies D1–D3 as soon as the Phase 1 scaffold lands (see Phase 1.6) and D4–D6 after the backend thread finishes:
   - **D1** `docker-compose-dev.yml` and `docker-compose-prod.yml`: remove `profiles: [web]` from `web`; in prod remove
     `required: false` from Nginx's `web` dependency; `web`'s `env_file` becomes `./apps/web/.env` (required) once
     `make setup` has created it (backend plan Phase 8.2 guard).
   - **D2** `Makefile`: nothing required (`WEB_READY`/`require_web` already pass once `apps/web/package.json` exists);
     confirm `make setup` copies `apps/web/.env.example`.
   - **D3** root `.gitignore`: add `!apps/web/.vscode/` and `!apps/web/.vscode/settings.json` after `.vscode/`.
   - **D4** root `AGENTS.md` and `README.md` (written by the backend plan): add the web app (`make dev` URL
     `http://localhost:3001`, `make check-web`, `apps/web/.env` in the env table, link to `apps/web/AGENTS.md`).
   - **D6** new `docs/decisions/2026-11-18-browser-charts-with-echarts.md` is written by the backend plan (Phase 9);
     the frontend implementer supplies its frontend paragraph: base `EChart` + per-type components in
     `components/general/charts/`, tree-shaken imports, the measured chart-chunk size against the 250 KB budget,
     theme from CSS variables, browser downloads (PNG 2400×1800 with `pHYs` + SVG).
   - **D5** new `docs/decisions/2026-11-18-warm-white-variant-of-the-ice2kg-theme.md` (guide format; Deciders
     "Youpele Michael (owner), Claude Code"): Decision = DEMATELab's token table unchanged, plus the PCK domain tokens
     and measured ratios from the Theme section; Context = owner's request for the same look as DEMATELab and the legacy
     rating colours; Alternatives = legacy Tk palette (rejected: below AA, inconsistent with DEMATELab), ice2kg cool
     whites (rejected by the owner for DEMATELab); Consequences = theme changes go through this table, a failed
     contrast check may change lightness only (fill or text, rules 1–3), XLSX and chart series keep legacy colours; Related Work =
     this plan, DEMATELab's decision.
4. Final checks (Testing And Validation) and the manual smoke flow; record results in the implementation report.

## Risks And Decision Gates

- **G1 — API availability.** Phases 1–2 need no API. Phases 3–7 can be developed against fixtures and mocked services,
  but each phase's "done" needs the backend endpoints it uses (backend Phases 4–7; `make dev` with the API healthy). If a
  backend response differs from the contract, stop and report; do not adapt the web silently. The contract changes only
  by updating both plans.
- **G2 — Deferred edits.** `make dev`/`make prod` with the `web` service need D1, which the coordinator applies when the
  Phase 1 scaffold lands. Until then run the web on the host (`pnpm run dev`) against the API container; only
  `make check-api` passes inside containers.
- **Large inputs.** 100 policies × 50 decision-makers: one mounted matrix step, virtualised grid, per-cell subscriptions.
  Each check/preview/network-chart/export call sends the full request (≈ 7–8 MB at the maximum) and the API recomputes
  (≈ 1–3 s). Queries are keyed by `snapshotHash`/request hash, so a request is sent once per change; live weight sums
  are debounced. Acceptable for the limits; caching is out of scope.
- **Ties at scale.** Majority with even counts produces many ties (13 of 20 cells in a 5 × 4 case); the ties list is
  virtualised above 50; no bulk "choose for all" (not in legacy).
- **Number formatting.** JavaScript `toFixed` differs from Python on exact halves; the API pre-rounds every number it
  returns to the display precision and returns text where precision is lower, so `formatFixed` at the same precision is
  exact. `-0.0` must survive JSON parsing (`JSON.parse("-0.0")` is `-0`) and display as `-0.00`.
- **ECharts in SSR and jsdom.** ECharts touches `window`/canvas: it is only imported inside `ClientOnly` and loaded
  lazily; unit tests mock the instance and use the SVG renderer with `ssr: true` for the one rendering test.
- **Bundle size.** Whole ECharts is 359 KB gzip; tree-shaking to graph + scatter is expected but unmeasured (research).
  The 250 KB budget is checked in Phase 6.9.
- **Two-way curves.** ECharts `curveness` is relative to edge direction; the sign rule is confirmed visually with the
  fixture pair before Phase 6 is done.
- **Download fonts.** Off-screen exports wait for `document.fonts.ready`, otherwise Manrope may fall back in the PNG.
- **Dense networks.** Up to 100 nodes overlap on narrow screens; zoom/pan and the centrality table mitigate; checked
  with a 30-policy synthetic case at 320 px.
- **Lockfile.** Removing `html-to-image` and adding `echarts` must not change other resolved versions; if `pnpm install` re-resolves anything
  else, stop and report.
- **AI keys in transit.** Production must enable TLS before AI use (backend risk); the web never stores or logs keys.
- **Refresh loses work.** By decision; mitigated by the one-time toast. The persistent note under Back/OK was removed.

## Testing And Validation

In the dev container (after `make setup && make dev`, with D1 applied):

```bash
make check-web                                  # biome format check, lint, typecheck, vitest
make test-web T="src/store"                     # focused runs
make test-web T="src/test/repository-rules.test.ts"
```

On the host (Node 24, pnpm 12.9.1):

```bash
cd apps/web && pnpm install --frozen-lockfile && pnpm run format:check && pnpm run lint && pnpm run typecheck \
  && pnpm run test && pnpm run build
```

Production smoke (after D1):

```bash
make prod && curl -fsS http://localhost:8081/ >/dev/null && curl -fsS http://localhost:8081/api/v1/health && make prod-down
```

Legacy untouched:

```bash
git diff -- tk-app | shasum
git status --porcelain -- tk-app | shasum
git ls-files -z -co --exclude-standard tk-app | sort -z | xargs -0 shasum | shasum   # content hash; safe with spaces
```

All three equal the values recorded before Phase 1 (record them first if the backend thread has not).

Tests by layer: theme contrast; repository rules; Zod schemas through service tests; `format.utils`, `flow.utils`,
`matrix.utils`, `project-state.utils`, `analysis-request.utils`, `content-disposition.utils`, `interpretation.utils`
unit tests; store actions; components (each step, Results tabs, export bar, AI panel) with loading, error and
accessibility checks (labels, focus, keyboard).

Manual checks in `make dev` (record results):

1. Smoke flow: step `project` → `Import from Excel` with `data/examples/WEF Nexus Example.xlsx` → Review → method step
   shows the forced-Average explanation (1 decision-maker) → Run → open every tab → every export downloads and opens
   (XLSX in a spreadsheet app, both PNGs at 2400×1800 with 300 dpi metadata, both SVGs, TXT, PDF after an interpretation if a key is
   available; otherwise record "blocked").
2. Compare numbers and texts with the legacy app on the same workbook (`make -C tk-app dev`, `http://localhost:6090`):
   Results Insights cards, Coherence Scores, Range of Influence, PCA stats, network stats and centrality.
   Charts: every layout; focus on a connected and an isolated policy (empty state); a two-way pair shows two arrows;
   negative edges red; PCA plain and entropy-coloured; hover texts; legend toggle; zoom/pan and Reset view; no node
   dragging; charts follow the warm-white theme.
3. Synthetic 4-decision-maker project: Median lower and upper, Majority with ties (votes shown), Weighted with
   `[0.335, 0.335, 0.335]`-style edge cases and the error texts.
4. Changing answers: rename/remove a decision-maker and a policy after a run → confirms, outdated banner, Re-run.
5. Keyboard only through the whole flow; Enter/Shift+Enter; browser Back/Forward; refresh returns to step 1 and the
   toast shows once per tab.
6. Layout at 320 px, tablet and desktop; a 100 × 100 matrix stays responsive.
7. `make prod`: the same smoke through `http://localhost:8081`.

## Acceptance Criteria

- Every row of the Parity Inventory works in the browser with the listed web text, and every item of Legacy
  Inconsistencies Settled is implemented as decided.
- The flow matches the Flow section: step order and skip rules, guards, `?step=` history, step list, Review with Edit
  links, Enter / Shift+Enter, Start over, refresh notice, confirms on data loss, outdated banner and Re-run.
- No policy-coherence value, label, limit, default or validation result is produced in the browser; all come from the
  API. The browser only formats numbers and counts filled cells.
- Results, charts, exports and the AI request use the stored snapshot.
- The network and PCA charts are drawn with ECharts from API chart data only, through the base `EChart` and the
  per-type components; no PNG is fetched for display; there is no other chart library; downloads are PNG 2400×1800
  with 300 dpi `pHYs` and SVG under the legacy names; the chart chunk is lazily loaded and ≤ 250 KB gzip (measured).
- Charts expose an aria description and tooltips with the legacy labels; their colours come from `/scales` and theme
  tokens.
- The API key is never stored, cached or logged, and the key field is empty after success and after failure.
- Theme tokens match the Theme section; every text pair passes WCAG AA (placeholder text excepted, as in DEMATELab);
  the app is usable from 320 px.
- `make check-web` passes; every code file ≤ 300 lines (`routeTree.gen.ts` exempt) and no `tk-app` reference, both
  enforced by `repository-rules.test.ts`.
- `make dev` serves the app on 3001 and `make prod` serves it behind Nginx on 8081 (after D1).
- `apps/web/AGENTS.md`, `README.md`, `CLAUDE.md` exist; deferred edits D1–D6 are listed with exact content in the
  implementation report; `tk-app/` is byte-identical to the baseline.

## Plan Validity

Valid for branch `restructure/apps-api-web` at `00b610a` with the uncommitted restructure described in the header,
DEMATELab `apps/web` at `6a76ae2`, and the backend plan as last modified 2026-11-18 19:40 CET (revision 3). Revalidate if:

- the backend API Contract, Label Fixes or Settled Decisions change;
- DEMATELab's `apps/web` changes after `6a76ae2` (copy sources) or its theme decision changes;
- `tk-app/*.py` or `tk-app/constants.py` colours change (Parity Inventory, Theme);
- `echarts` 6.1.0 behaviour (graph `curveness`, `ClientOnly`, export APIs) differs from the research of 2026-11-18;
- the pinned web versions are no longer installable (pnpm `minimumReleaseAge`, registry removals).

## Handoff Notes

- **Order:** backend plan Phases 1–7 (at least the contract endpoints) and its Phase 8 root files, then this plan's
  Phases 1–8. Phases 1–2 can start at once. At most two implementation threads with disjoint ownership: backend
  (`apps/api`, `scripts/`, root infra, `docs/`) and frontend (`apps/web` only).
- **Do not reopen** without new evidence: the Settled Decisions (including the planning-level choices in 11), the Theme
  values (a failed contrast check may change lightness only), the Flow, the Parity Inventory decisions and Legacy
  Inconsistencies Settled.
- **Copy before rebuilding:** take DEMATELab's fixed `StepFrame` (Enter handling, `initialFocus` skipping hidden
  inputs), `flow.utils.ts`, `MatrixGrid`/`MatrixCell`, the `ExplanationPanel` family and their tests, and adapt them; do
  not re-derive them (playbook Finding 8).
- **API texts are shown as returned** (no web rewriting). Since backend revision 2 they already follow the web text
  rules: one arrow `→` with spaces (L11, `↔` only on Most Contested), `Rating agreement` (L12), `positive link` /
  `negative link` (L13) and singular/plural counts (L14). There is no remaining exception. Further text changes go
  through backend label fixes in both plans.
- **Process:** never commit or push; no worktrees or branches; no git state changes; report deviations with evidence;
  list deferred edits D1–D6 with exact content instead of editing root files or `docs/`. The coordinator applies D1–D3
  when the Phase 1 scaffold lands and D4–D6 at the end.
- **Revision 3 contract** (browser charts, shared with the backend plan): `POST /analysis/charts/network` returns
  `NetworkChartData` JSON; `AnalysisData.pca` carries `label`, `bounds`, axis labels and `stats_text`; `/scales` has no
  `charts` block and gains node colours, `layout_canvas` and `pca`; no hotspot or PNG chart endpoints.
- **No blockers.**

## Open Questions

None. There are no open product decisions.

The live AI check depends on a provider key being available; if none is, it is recorded as blocked and does not block
acceptance.
