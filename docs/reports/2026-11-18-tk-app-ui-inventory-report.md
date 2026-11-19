# The Tk App's UI Is One Workspace With Five Dialogs And Seven Result Tabs, And It Has About Forty Inconsistencies The Web Plan Must Settle

**Date:** 18 November, 2026
**Author:** Claude Code (research agent) for Youpele Michael
**Scope:** Every user-facing screen, control, text, table, chart, export and theme token in `tk-app/`, on branch `restructure/apps-api-web` at commit `00b610a` (files moved unchanged into `tk-app/`, not yet committed). Line numbers refer to `tk-app/<file>.py`.

## Summary

The legacy UI is a single window. It has a collapsible project sidebar, a top bar with five actions and a status bar. Each project holds two views, switched by a pill toggle: **Decision Makers**, with one matrix editor per decision-maker (DM), and **Analysis**, with seven lazily built result tabs. Five modal dialogs drive the flow:

1. Create Project / Add Decision-Makers, a shared dialog.
2. Aggregation Method.
3. Decision-Maker Weights.
4. Median Choice.
5. Resolve Majority Ties.

The top bar has three more action-specific dialogs: rename, import and export.

The result tabs are:

- Results Insights
- Aggregated
- Coherence Scores
- Range of Influence
- PCA
- Network Analysis
- LLM Interpretation

The texts, colours and thresholds are inventoried verbatim below. The flow maps well onto one-question-per-step screens: project, DMs, policies, one matrix step per DM, review, method, weights or median, ties, then results.

The plan must also settle several defects and pieces of dead UI before parity is defined:

- **Projects cannot be deleted or renamed from the UI.** The handlers exist but nothing calls them (app.py:2323, 2349).
- **Two-way network arrows are drawn on top of each other** (network_tab.py:932-940).
- **The PCA feature columns are misaligned** (pca_tab.py:90-93).
- **The Results Insights story highlighting is broken** (results_insights_tab.py:771).
- Method labels differ between the dialog, the tab titles and the Excel export ("Median (Ordinal)" / "Median (Lower)" / "Median"; "Weighted by Importance" / "Weighted"; "Average" / "Avg").
- The sidebar keeps showing old DM names after a DM is renamed or removed.
- Roughly half of `results_insights_tab.py` and several dialogs are dead code.

## Questions

1. What screens, dialogs and tabs exist, in user-flow order, and how do multiple projects work?
2. What controls exist (type, verbatim label, default, limits, options, enable rules, tooltips, keys)?
3. What user-facing messages exist, verbatim?
4. What tables, charts and insight templates exist, with formats, colours and thresholds?
5. How does the matrix editor behave?
6. What can be exported, and under which default names?
7. What theme tokens and assets exist?
8. Which inconsistencies, dead UI and wrong texts must the plan settle?
9. How should the legacy screens map onto a step-by-step web flow plus a results area?

## Method

- I read `AGENTS.md`, the report authoring guide, and the "Parity Inventory" section of `dematelab/docs/plans/2026-11-16-rebuild-ui-in-tanstack-start-plan.md` as the target level of detail.
- I read these files directly: `app.py` (all 3217 lines), `dialogs.py`, `aggregation_dialog.py`, `matrix_widget.py`, `theme.py`, `constants.py`, `models.py`, `importer.py`, `aggregator.py` (labels, validation, result model), `main.py`, `font_loader.py` and `__init__.py`.
- Three delegated read-only research agents read the remaining tabs in full:
  - `aggregation_tab.py`, `coherence_scores_tab.py`, `range_of_influence_tab.py`;
  - `network_tab.py`, `pca_tab.py`;
  - `results_insights_tab.py`, `llm_tab.py`.
- I spot-checked their most consequential claims against the source:
  - the PCA column misalignment;
  - the overlapping two-way arrows;
  - the story regex;
  - the Most Contested caption;
  - the LLM engine list.
- Nothing was executed. The GUI was not launched. All findings come from reading the code.

## Findings

### 1. Screens and flow, in user order

#### 1.1 Application shell

| Element | Behaviour | Source |
|---|---|---|
| Window | Title `Policy Coherence Kit`; size 1200×780, centred; minimum 900×600; background `#ffffff`; ttk theme `clam`. | app.py:313-320; constants.py:54-56 |
| Startup | Windows DPI awareness is set before Tk is imported. `load_inter()` runs before `tk.Tk()`. The window is brought to the front after 100 ms (`osascript` on macOS). | main.py:10-73 |
| Layout | Left: sidebar. Right: content column containing the top bar, a 1 px divider, the project area and the status bar. | app.py:373-386 |
| Project notebook | A `Headless.TNotebook` holds one hidden-tab page per project. Projects are switched only through the sidebar. | app.py:345-351, 1039-1052 |
| Status bar | 35 px tall, background `#ffffff`, text `#a6bcd3` Inter 10, `padx=12`, 1 px `#e6e6e6` top divider. Initial text `Ready`. | app.py:1444-1454 |

#### 1.2 Sidebar (projects list)

| Element | Text / behaviour | Source |
|---|---|---|
| Width | 380 px expanded, 80 px collapsed. Background `#fafbfc`, 1 px `#e6e6e6` right border. | app.py:388-399 |
| Header | Logo badge (35 px, `#1f2937`, radius 5) with a Lucide "waypoints" icon in `#f5f7fa`, drawn in code. Title `Policy Coherence Kit` (Inter 20 bold, Windows 17, `#1f2937`). Slogan `Evaluate interactions between policies using multiple decision-makers` (Inter 10, Windows 9, `#a3a3a3`, wrap 280). Header height 90 px (130 on Windows). **Clicking anywhere on the header collapses or expands the sidebar.** | app.py:404-477 |
| Collapsed header | Shows only the logo badge; clicking it expands the sidebar again. | app.py:479-511, 687-704 |
| Section label | `PROJECTS` (Inter 9 bold, `#a3a3a3`). When collapsed it is recoloured to the background colour, which hides it but keeps its spacing. | app.py:518-524, 698 |
| Empty state | `No projects available.\nCreate a new project to begin assessing interactions between policies across decision-makers.` (Inter 11, `#a3a3a3`, centred, wrap 300, 80 px from the top). | app.py:2036-2045 |
| Project row (expanded) | Chevron (right or down, `#a3a3a3`) toggles open/closed. Folder icon and name (Inter 14, `#2c3b4e`, wrap 236) select the project. A project's open state is stored by name and defaults to open for new projects. | app.py:2050-2070, 2284-2297, 1909 |
| `DECISION-MAKERS` row | Inter 11, `#a3a3a3`, with a plus icon. Hover background `#ebebeb`. **Clicking it opens the Add Decision-Makers dialog.** | app.py:2083-2165 |
| DM list items | User icon plus DM name (Inter 13, `#426387`, wrap 210). Hover `#eaeef4`, radius 5. Clicking selects the project and that DM's tab. | app.py:2170-2281 |
| Project badge (collapsed) | 37×37 px, `#eaeef4`, radius 4. Shows the first two characters of the project name, upper-cased (Inter 12 bold, `#30455c`). Clicking selects the project. | app.py:2006-2035 |
| New Project button | Pinned to the bottom. 40 px tall, `#eaeef4` (hover `#d0dbe7`), radius 5. Folder-plus icon and `New Project` (Inter 13, `#1f2937`). When collapsed it shows only the icon in a square. Hover is detected by polling the pointer every 30 ms. | app.py:560-683 |
| Scrolling | Mouse wheel scrolls the project list; there is a 5 px Tk scrollbar. | app.py:526-558, 2299-2311 |

#### 1.3 Top bar

The top bar is 70 px tall and grows if the buttons wrap. The left 4/12 holds the project name and stats; the right 8/12 holds a right-aligned, wrapping button row (app.py:706-962).

| Element | Text | Source |
|---|---|---|
| Project name | Current project name (Inter 12 bold, `#2c3b4e`). Empty when no project is open. | app.py:730-735, 978 |
| Stats, project has no DMs | `No decision-makers yet` | app.py:980-985 |
| Stats, matrix view | `{dm}'s workspace` (colour `#7799b9`), then `  .  ` (`#808080`), then `{n} policy` or `{n} policies` (`#a3a3a3`), then `  \|  `, then `{n_cells} cells to fill`. **`n_cells` is the total off-diagonal count, not the number still empty.** | app.py:999-1012 |
| Stats, analysis view | `{n} decision-maker(s)`, then `  .  `, then `{n} policies`, then `  \|  `, then `Analysis` | app.py:987-997 |
| Buttons, left to right | 1. `Rename Tab` (pencil icon, `#2c3b4e`). 2. `Delete Tab` (trash icon, `#DC2626`). 3. Separator. 4. `Import Excel` (file-down icon). 5. `Export Excel` (file-up icon). 6. Separator. 7. `Run Analysis` (play icon, background `#2c3b4e`, hover `#37506d`, text `#f5f7fa`). Secondary buttons are `#f5f7fa` with hover `#eaeef4`, border `#eaeef4`, 33 px tall, radius 5, Inter 11. **The buttons are always enabled.** Any precondition is reported in a message box. | app.py:753-959 |

#### 1.4 Empty workspace (no project)

This panel is centred and 500 px wide; it shrinks to between 280 px and the available width minus 80. It switches to a "compact" size when the window is less than 680 px tall (app.py:1073-1442).

- Icon badge: 58 px, `#eaeef4`, Lucide "network" icon in `#30455c`.
- Title: `Start a new policy coherence assessment` (Inter 23, compact 17, `#1f2937`).
- Subtitle: `Create a project to define policies, add decision-makers, and evaluate interactions across expert perspectives. The tool supports structured matrix input, aggregation methods, and advanced analytical outputs.` (Inter 12, `#808080`).
- Workflow box: label `WORKFLOW`, then five numbered steps, each with an icon:

  | Step | Text | Icon |
  |---|---|---|
  | `01` | `Create a project` | folder-plus |
  | `02` | `Add decision-makers` | user-plus |
  | `03` | `Define policies` | file-text |
  | `04` | `Complete the interaction matrix` | square-pointer |
  | `05` | `Run aggregation and analysis` | chart-network |

  Box styling: background `#fafbfc`, shadow `#e8eaed`. Steps are white, 55 px tall, numbers in `#d3d3d3`.
- Button: `New Project` with a plus icon. Background `#426387`, hover `#30455c`, text `#eaeef4`, 35 px tall.

#### 1.5 Project page

- **Switcher bar** (48 px, white, 1 px `#e8eaed` divider; app.py:1499-1864):
  - **Left: tab strip.** In matrix view it lists DM names; in analysis view it lists result tab titles.
    - Labels: Inter 12, inactive `#a3a3a3`, active `#30455c` with a 1 px `#557ca2` underline.
    - The strip scrolls horizontally with the mouse wheel (eased) and with drag-to-scroll with momentum.
    - A tab is selected on mouse release, and only if the gesture was not a drag.
  - **Analysis view only:** `<` and `>` chevrons (idle `#a3a3a3`, hover `#30455c`). Each click scrolls the strip by 160 px; they do not change the tab.
  - **Right: pill toggle.**
    - Track `#a6bcd3`, thumb `#e8eef4`. Active icon `#30455c`, inactive icon `#ffffff`.
    - Segment 1 has a user icon, tooltip `Decision Makers`; segment 2 has a chart-network icon, tooltip `Analysis`. Tooltips have background `#2c3b4e`, white Inter 10 text.
    - **Clicking Analysis does nothing until an analysis exists.** There is no feedback.
- **Matrix view:** one hidden notebook page per DM. Each `MatrixWidget` is built lazily on first selection (app.py:2412-2448).
  - Empty project text: `Click  "+ Add Decision-Maker"  to add the first matrix.` (Inter 11, `#666666`; app.py:1879-1886).
- **Analysis view:** a notebook of the seven result tabs (§1.11). Re-running replaces the visible tabs (app.py:2613-2658).

#### 1.6 Create Project / Add Decision-Makers dialog (`ProjectSetupDialog`, dialogs.py:301-1283)

- **Window:** borderless, rounded (radius 11, background `#eaeef4`, border `#d0dbe7`).
  - It can be dragged by the shell.
  - Width is at least 860 px. Height is 665 px (create) or 400 px (add); the content scrolls with a pill scrollbar.
  - On Linux the corners are square (dialogs.py:376-393).

| Part | Create mode | Add mode | Source |
|---|---|---|---|
| Title | `Create Project` | `Add Decision-Makers` | dialogs.py:456 |
| Subtitle | `Define the project, decision-makers, and policy set.` | `Add one or more decision-makers to the current project.` | dialogs.py:457-461 |
| Close | × icon, hover `#dfe5ec` | same | dialogs.py:486-493 |
| Import button | `Import from excel` (lowercase "excel"; file icon; white, hover `#f3f4f6`). Closes the dialog with `action=import_excel`, which opens the file picker. | same, but imports **into** the current project | dialogs.py:495, 562-652, 1126-1128; theme.py:101 |
| Project name | Label `Project Name`, hint `Use a clear descriptive title for this project.`, placeholder `e.g. EU Clean Mobility Policy Coherence Assessment` | (absent) | dialogs.py:839-858; theme.py:109-112 |
| DM section | Title `Add decision-maker names`, hint `Add one or more decision-maker names.`, `Add` button (plus icon, 70×30). Starts with **2 rows**. Placeholders are `e.g. Expert A`, `e.g. Expert B`, … (letters continue AA, AB…). | same | dialogs.py:502-508, 863-875 |
| Policy section | Title `Add policy names`, hint `Add at least 2 policy names.`, `Add` button. Starts with 2 rows; placeholders `e.g. Policy 1`, `e.g. Policy 2`, … | **Hidden** when the project already has matrices (policies are inherited). Shown when the project has no DMs. | dialogs.py:510-519 |
| Fixed policy section | `Add policy names` / `Policies are inherited from the current project.` with disabled fields | **Never shown.** The condition `fixed_policies and include_project_name` is never true. | dialogs.py:510-511, 946-976 |
| Rows | Rounded 35 px fields, white, border `#e6e6e6`. Placeholder text is `#d3d3d3` Inter 10. A red minus button (`#ef4444`) appears only on row 3 onwards. Rows lay out in 1 column, 2 columns above 6 rows, 3 columns above 12. | same | dialogs.py:978-1078 |
| Footer | `Cancel` (red `#DC2626` text on `#f5f7fa`), then `Create Project` (`#2c3b4e`, hover `#30455c`) | `Cancel`, then `Add Decision-Makers` | dialogs.py:521-552 |
| Keys | `Return` submits, `Escape` cancels. Focus starts in the project name (create) or first DM field (add). | same | dialogs.py:554-560 |

Validation runs in this order (dialogs.py:1080-1124). Names are trimmed, empty rows are ignored, and comparisons are case-sensitive.

| Check | Title | Message |
|---|---|---|
| Project name empty (create) | `Project Name Required` | `Please enter a project name.` |
| Project name duplicate | `Duplicate Project` | `A project named "{name}" already exists.` |
| No DM | `Decision-Makers Required` | `Please enter at least one decision-maker name.` |
| Duplicate DMs in the dialog | `Duplicate Decision-Makers` | `Decision-maker names must be unique.` |
| DM already exists in project | `Existing Decision-Makers` | `These decision-maker names already exist in the project:\n\n{names, one per line}` |
| Fewer than 2 policies | `Too Few Policies` | `Please enter at least 2 policy names.` |
| Duplicate policies | `Duplicate Policies` | `Policy names must be unique.` |

On success:
- Create mode: one empty matrix is made per DM and policy codes `P1..Pn` are assigned. Status: `Project "{name}" created.`, immediately replaced by `Project "{name}" created with {k} decision-maker(s).` (app.py:1460-1485, 1911).
- Add mode: status `Added {k} decision-maker(s) to project "{project}".` (app.py:2374-2410).

#### 1.7 Excel import (top bar `Import Excel` or the dialog's `Import from excel`)

| Step | Text | Source |
|---|---|---|
| No project | `No Project` / `Create a project first.` (top bar only) | app.py:2919-2925 |
| File picker | Title `Import matrices from Excel workbook`; filter `Excel Workbook` `*.xlsx *.xls`. `.xls` is offered but openpyxl cannot read it. | app.py:2927-2932 |
| Read error | `Import Error` / the exception text | app.py:2934-2939 |
| Missing openpyxl | `openpyxl is required for Excel import.\nInstall it with:  pip install openpyxl` | importer.py:62-65 |
| Header mismatch (error) | `Sheet "{sheet}": row and column headers do not match.\n` followed by up to 5 lines `  row {i}: "{row}" vs col "{col}"` | importer.py:101-112 |
| Unknown rating (error) | `Sheet "{sheet}": unrecognised rating values:\n` followed by up to 10 lines `  P1->P2: "{val}"` (`\n  ...` if more), then `\n\nAllowed values: Indivisible, Reinforcing, Enabling, Neutral, Constraining, Counteracting, Cancelling` | importer.py:151-165 |
| Sheet warnings | `Sheet "{sheet}": empty, skipped.` · `Sheet "{sheet}": fewer than 2 policies in header row, skipped.` · `"{sheet}": {k} blank cell(s): P1->P2, …{ (+N more)}` | importer.py:75-90, 168-173 |
| Nothing found | `Nothing Imported` / `No valid matrices were found in the workbook.` | app.py:2959-2963, 3010-3014 |
| Policy mismatch (into project) | `Policy List Mismatch` / `The following sheets have a different policy list and cannot be imported:\n\n  - {dm}\n…\n\nAll matrices must share the same policy list.` | app.py:2970-2978 |
| Success | `Import Complete` / `{k} matrix/matrices imported successfully.` | app.py:2994-2996, 3028-3031 |
| Success with warnings | `Import Complete with Warnings` / `{k} matrix/matrices imported.\n\nThe following sheets have blank cells:\n\n{warnings}`. **"Skipped" warnings also appear under this "blank cells" heading.** | app.py:2987-2992, 3022-3027 |
| Status | `Imported {k} matrix/matrices from: {path}` (into project) · `Project "{name}" created from import: {path}` (new project; name = file stem, made unique with ` 2`, ` 3`, …) | app.py:2941-2948, 2998, 3035 |

Rules: each sheet becomes one DM, and the sheet name becomes the DM name. Imported DM names are **not** checked against existing DMs. Ratings match case-insensitively; blank cells and the text `none` count as blank.

#### 1.8 DM tab actions (top bar)

| Action | Matrix view | Analysis view | Source |
|---|---|---|---|
| `Rename Tab` | Opens a `_SimpleInputDialog` titled `Rename Tab`, label `New decision-maker name:`, prefilled and selected, buttons `Cancel` / `OK`. Return = OK, Escape = cancel. An empty value makes OK do nothing. **There is no duplicate check, and the sidebar is not refreshed.** Status: `Renamed to "{name}".` | `Cannot Rename` / `Analysis result tabs cannot be renamed.` | app.py:2458-2479; dialogs.py:1516-1622 |
| `Delete Tab` | Confirm `Remove Matrix` / `Remove matrix for "{dm}"?` (Yes/No). Status: `Removed "{dm}".` **The sidebar is not refreshed.** | Confirm `Remove Tab` / `Remove this analysis result tab?`. Status: `Analysis tab removed.` The result stays in `agg_results`, so it is still exported. | app.py:2481-2527 |

#### 1.9 Matrix editor (`MatrixWidget`, matrix_widget.py)

**Layout** (matrix_widget.py:253-318). The editor uses four canvases:
- a fixed legend strip at the top;
- column headers, which scroll horizontally with the cells;
- row headers, which scroll vertically with the cells;
- the main cell canvas.

Pill scrollbars appear only when the content overflows.

**Sizes:**
- Cells are 40 px tall with 6 px gaps. Row headers are 120 px wide.
- With n ≤ 5, cells stretch to fill the width (minimum 60 px).
- With n > 5, cells are 200 px wide and the block is centred.

**Legend:**
- Text `Click a cell to rate it:` (Inter 9 italic, `#a3a3a3`).
- Followed by the seven rating badges, in order: Indivisible, Reinforcing, Enabling, Neutral, Constraining, Counteracting, Cancelling. Each badge is 25 px tall, radius 4, Inter 10, using the rating colours (§2).

**Axis label:** `<-- Influencing  |  Influenced -->` above the column headers (Inter 9 italic, `#a3a3a3`).

**Headers:**
- Codes `P1..Pn` on `#426387`, text `#f5f7fa`, Inter 10, radius 8.
- Hovering a header shows the tooltip `{code}:  {policy}` (two spaces after the colon). Tooltips are `#fffbe6`, text `#1e1e1e`, Inter 9, solid border, wrap 320.

**Cells** (matrix_widget.py:534-585):

| State | Fill | Text | Outline |
|---|---|---|---|
| Diagonal | `#f5f5f5` | `Neutral` in `#a3a3a3` | `#e6e6e6` |
| Not rated | `#ffffff` | `--` in `#a3a3a3` | `#f5f5f5` |
| Rated | the rating colour | the rating label in its text colour, Inter 12 | — |

- Every off-diagonal cell has a chevron in `#a3a3a3`.
- The diagonal is not clickable.

**Rating dropdown** (matrix_widget.py:615-689):
- Clicking a cell opens a borderless popup as wide as the cell, listing the seven ratings. Rows are 38 px, white, hover `#f0f4f8`.
- It opens below the cell, or above if there is no room.
- The active cell gets a `#426387` outline.
- Picking a rating saves it and updates the status bar to `"{dm}"  --  {filled}/{total} cells filled  |  P1 -> P2: {rating}` (app.py:2437-2443).
- Any click elsewhere, or Escape, closes the popup.

**Missing features:**
- no way to clear a cell back to blank;
- no keyboard navigation;
- no copy/paste;
- no fill helpers (row/column/all);
- no tooltips on cells;
- no highlighting of incomplete cells (`refresh_cell` exists but is never called).

**Validation** happens only when **Run Analysis** is pressed (§1.10).

**Scrolling:** wheel input is turned into velocity with decay 0.85 and step 0.15. The handler divides `delta` by 120, so it barely moves on macOS.

#### 1.10 Run Analysis → aggregation dialogs (app.py:2533-2611)

| Step | Condition | Dialog / message | Source |
|---|---|---|---|
| 0 | No project | `No Project` / `Create a project first.` | app.py:2535-2538 |
| 0 | No DMs | `No Matrices` / `Add at least 1 decision-maker matrix before running analysis.` | app.py:2540-2544 |
| 1 | Any blank cell | Error `Incomplete Matrices` / `Please fill all cells before aggregating.\n\n` followed by one line per DM, `  {dm}: P1->P2, P1->P3, …{ (+N more)}` (up to 10 cells listed) | app.py:2546-2556 |
| 2 | Fewer than 3 DMs | Method is forced to **Average**, with no dialog and no notice. | app.py:2558-2560 |
| 2 | 3 or more DMs | **Aggregation Method** dialog | aggregation_dialog.py:48-244 |
| 3 | Method is Weighted | **Decision-Maker Weights** dialog | aggregation_dialog.py:431-625 |
| 3 | Method is Median and the DM count is even | **Median Choice** dialog | aggregation_dialog.py:247-428 |
| 4 | Majority produced ties | **Resolve Majority Ties** dialog | aggregation_dialog.py:628-800 |
| 5 | Done | Tabs are built and the analysis view is shown. Status `Analysis complete for "{project}"  \|  method: {label}  \|  {n} decision-maker(s)` | app.py:2605-2611 |

**Aggregation Method dialog** (window 440 px):
- Title `Aggregation Method`.
- Subtitle `{n} decision-makers detected — choose how to combine their ratings.`
- Selectable radio cards, each 76 px:
  - Selected: background `#e8eef5`, 2 px `#2c4a6e` border.
  - Hovered: `#f5f7fa`, border `#b8cad8`.
  - Idle: `#ffffff`, border `#d0dbe7`.
- Default selection: `Average`.
- Buttons `Cancel` / `Continue`. Return = Continue, Escape = Cancel.

| Value | Title | Description |
|---|---|---|
| `average` | `Average` | `Each decision-maker is weighted equally. Cell score = mean of all scores.` |
| `median` | `Median (Ordinal)` | `Uses the ordered middle rating(s) and avoids assuming equal spacing.` |
| `majority` | `Majority Rule` | `The most common rating wins. Ties are flagged for manual resolution.` |
| `weighted` | `Weighted by Importance` | `You assign a weight (0–1) to each DM. Weights must sum to exactly 1.0.` |

**Decision-Maker Weights dialog** (420 px):
- Title `Decision-Maker Weights`.
- Subtitle `Enter a value between 0.0 and 1.0 for each decision-maker. Weights must sum to exactly 1.0.`
- One row per DM: the DM name in bold, then an 8-character centred entry. **Entries are empty by default.**
- A live sum label, right-aligned: `Sum: —` (when empty or invalid) or `Sum: {round(total,4)}`. It is `#2c4a6e` when within 0.01 of 1, otherwise `#b71c1c`.
- Buttons `Cancel` / `Aggregate`.

Errors:

| Title | Message |
|---|---|
| `Missing Weight` | `Please enter a weight for "{dm}".` |
| `Invalid Value` | `"{raw}" is not a valid number for "{dm}". Use a decimal like 0.3.` |
| `Out of Range` | `Weight for "{dm}" must be between 0.0 and 1.0.` |
| `Weights Do Not Sum to 1` | `Current sum is {sum}.\nPlease adjust the weights so they sum to exactly 1.0.` |

The actual tolerance is ±0.01.

**Median Choice dialog:**
- Title `Median Choice`.
- Subtitle `{n} decision-makers detected. Choose which median should be used for aggregation.`
- Cards:
  - `Lower Median` / `Use the lower of the two middle ratings in the ordered scale.` (default)
  - `Upper Median` / `Use the upper of the two middle ratings in the ordered scale.`
- Buttons `Cancel` / `Continue`.

**Resolve Majority Ties dialog** (500 px wide, at most 620 px tall, scrolls):
- Title `Resolve Majority Ties`.
- Subtitle `{k} cell(s) ended in a tie. Please select the rating for each one.`
- One card per tie:
  - heading `P{r} -> P{c}` (codes only; no policy names, no DM ratings);
  - `Tied options: Reinforcing (+2)  |  Enabling (+1)`;
  - label `Selected rating` with a read-only combobox limited to the tied labels, empty by default.
- Buttons `Cancel` / `Confirm`.
- Error `Unresolved Tie` / `Please select a rating for cell P{r} -> P{c}.`

Cancelling any of these dialogs aborts the run silently.

#### 1.11 Analysis tabs (app.py:2628-2636)

Tab titles (shown trimmed in the strip): `Results Insights ({m})`, `Aggregated ({m})`, `Coherence Scores ({m})`, `Range of Influence ({m})`, `PCA ({m})`, `Network Analysis ({m})`, `LLM Interpretation ({m})`.

`{m}` comes from `aggregation_method_label` and is one of `Average`, `Majority Rule`, `Weighted`, `Median`, `Median (Lower)`, `Median (Upper)` (aggregator.py:373-391). Results Insights opens first. The other tabs are built when first selected.

##### Results Insights (results_insights_tab.py)

**Layout:** a non-scrolling grid of 3 equal columns and 3 rows (row weights 2/1/1), with a 9 px gap around each card. Cards have radius 6. There are no interactive controls.

| Card | Contents (verbatim) | Colours |
|---|---|---|
| **Key Insights** (spans 2 columns) | - Title `Key Insights`.<br>- Story: a read-only text box of 6 lines with no scroll; overflow is clipped.<br>- `Interpretation:` followed by the interpretation sentence.<br>- Three tags: `Top Driving Policy: {policy (code)}`, `Strongest Link: {A (P1) → B (P2)}`, `Contested: {pair with →}` or `Contested: None`. | Card `#fffbeb`. Title Inter 30 `#2c3b4e`. Story Inter 15 `#37506d`; relation text `#30455c`. Codes coloured by role: driver `#2A9D8F`, dependent `#F4A261`, balanced `#6B7280`. Interpretation label `#30455c`, text `#426387` (wrap 540). Tags: `#DCFCE7`/`#166534`, `#DBEAFE`/`#1E40AF`, `#FEE2E2`/`#991B1B`. |
| **Analysis Overview** | Title `Analysis Overview`. Four value/label rows: `{n}` `Policies`; `{dm}` `Decision-makers`; `{method}` `Aggregation method`; `{agreement:.2f}` `Agreement` | Card `#eef2ff`. Values Inter 30 bold: Policies `#1D4ED8`, DMs `#0F766E`, method `#7C3AED`, agreement `#059669`. Labels Inter 10 `#475569`. |
| **System Health** | Title `System Health`. Bars `Synergy`, `Conflict`, `Neutral/Uncertain`, each with an integer value and **no % sign**. | Card `#f8fafc`. Bars 4 px tall on track `#f5f5f5`: `#15803d`, `#b91c1c`, `#2563EB`. Fill = max(3%, v/100). |
| **Top Driving Policy** | Hero `{policy} ({code})` or `N/A`. Subtitle `Top Driving Policy`. Value `{woi:+.2f} WOI`. | Card `#ecfdf5`. Hero Inter 30 `#2c3b4e`. Value Inter 40 bold `#15803d`. |
| **Top Influenced Policy** | Hero, subtitle `Top Influenced Policy`, value `{wii:+.2f} WII` | Card `#fff7ed`. Value `#b45309`. |
| **Strongest Link** | `Strongest Link`. Main `{A (P1)} -> {B (P2)}` or `No non-zero relation`. Value `{+x.xx} Reinforcing` or `No strong link`. Caption `Strongest relation`. Positive edges only. | Card `#eff6ff`. Title `#4f46e5`. Main Inter 25 bold `#1d4ed8`. Value Inter 20 bold `#3b82f6`. Caption `#a3a3a3`. |
| **Most Contested** | `Most Contested`. Main `{pair with ↔}` or `No contested link`. Value `Agreement: {ratio:.2f}` or `Stable`. Caption `⚠ High disagreement` (ratio < 0.5) or `Moderate disagreement`. | Card `#fef2f2`. Title `#F59E0B`. Main `#B45309`. Value `#D97706`. |
| **Conflict Ratio** | `Conflict Ratio`. Main `{ratio*100:.0f}%`. Value `{neg} of {active} active links`. Caption `Low systemic conflict` (≤ 0.2), `Moderate conflict pressure` (≤ 0.4), `High conflict pressure` (> 0.4). | Card `#fef2f2`. Title `#DC2626`. Main `#991B1B`. Value `#B91C1C`. |

On Windows, font sizes are smaller (results_insights_tab.py:152-181).

**Computations** (`compute_insights`, :607-664; not cached; used only by this tab):
- Per policy:
  - `net = woi − wii`
  - `prominence = Σ|out| + Σ|in|`
  - role: driver if net > 0.05, dependent if net < −0.05, otherwise balanced
- Top driver: highest `(woi, prominence, net)`. Top dependent: highest `(wii, prominence, −net)`.
- Graph statistics (:312-352):
  - counts of positive, negative and zero edges;
  - `density = active/(n(n−1))` (3 dp);
  - `polarity = pos/active` (0.5 if there are no active edges);
  - strongest positive and negative pair.
- Agreement statistics (:417-455):
  - per cell, `agreement_ratio` = share of DMs giving the most common rating, and `spread` = max − min;
  - `contested` = the 5 cells with the lowest agreement, **chosen from all cells, so it is never empty**;
  - `average_agreement` = (mean pairwise Spearman ρ between DMs + 1)/2, or 1.0 when there are fewer than 2 DMs.
- System health (:562-590):
  - `synergy = round(Σpos/(3·n(n−1))·100)`
  - `conflict = round(Σ|neg|/(3·n(n−1))·100)`
  - `neutral = round(zeros/(n(n−1))·100)`
  - Python rounding is banker's rounding.
- Story (:529-559). `{link}` is `{A (P1) -> B (P2)} ({±x.xx} Reinforcing|Constraining)` (:512-526). `{stable}` is `stable` if agreement ≥ 0.75, otherwise `not yet fully stable`. The branches are:
  - no driver: `The current result set is too sparse to describe a clear system story.`
  - a contested link exists: `{driver} emerges as the top driving policy in the system, with the highest weighted outgoing coherence score of {woi:+.2f} and its strongest influence through the {reinforcing|constraining} relationship {link}, which indicates a {stable} and structurally significant interaction. In contrast, the linkage {contested pair} remains contested across decision-makers, reflecting a lack of consensus and highlighting an area of uncertainty within the system.`
  - no contested link and a nonzero link: same opening, then `At the same time, the broader pattern shows an average agreement level of {a:.2f}, suggesting that the dominant structure is interpretable with reasonable confidence.`
  - otherwise: `{driver} emerges as the top driving policy in the system based on its weighted outgoing coherence score of {woi:+.2f}, but no single outgoing relationship yet dominates strongly enough to define the structure on its own. This suggests the system remains diffuse, with influence spread across multiple pathways that should be interpreted with care.`
- Interpretation (:593-604):

  | Condition | Text |
  |---|---|
  | contested and a ≥ 0.75 | `The system is relatively stable, but one important relation still lacks consensus.` |
  | contested and a ≥ 0.5 | `The system shows a workable pattern overall, though a few relations still need careful interpretation.` |
  | contested (otherwise) | `The system remains contested, so the strongest signals should be treated as provisional.` |
  | a ≥ 0.75 | `The system is highly consistent across decision-makers, so the main structure looks robust.` |
  | else | `The system is moderately stable, with some signals requiring additional scrutiny.` |

- Narrative (:470-500) is computed but never shown. Its lines:
  1. `{label} has the highest weighted outgoing coherence score of {woi:+.2f}, suggesting the strongest outward influence on the policy system.`
  2. `{label} has the highest weighted incoming coherence score of {wii:+.2f}, indicating that it receives the strongest aggregate influence.`
  3. `{label} shows the highest overall prominence ({p:.2f}), making it a central policy for interpretation and intervention sequencing.`
  4. `The aggregated structure contains {pos} positive and {neg} negative relations with density {d:.3f} and a positive polarity share of {pol:.3f}.`
  5. `Average inter-rater agreement is {a:.3f}, which helps separate robust links from contested relations.` (always cut by `[:4]` when lines 1-3 exist)

##### Aggregated (aggregation_tab.py)

- A read-only grid in the same style as the editor: cells 200×40, radius 8, Inter 12, showing the score to 2 decimals.
- Legend `Aggregated score scale:` (Inter 9 italic, `#666666`) with the seven badges. Axis `<-- Influencing  |  Influenced -->`.
- Cell colour: the score is clamped to ±3 and rounded to the nearest integer; .5 rounds up (0.5→1, −0.5→0). The rating colours are used (§2). Diagonal and `None` count as 0.
- Tooltips:
  - headers: `{code}: {policy}`;
  - cells: `P1 -> P2\nScore: {s:.2f}\nColour band: {rating}`;
  - diagonal: `P1 -> P1\nScore: 0.00 (diagonal)`.
- There is no page title, no empty state and no display of the Median ordinal labels.

##### Coherence Scores (coherence_scores_tab.py)

- Title `Coherence Scores  —  {m}` (Inter 30, `#37506d`).
- Legend rows (label Inter 11 `#1f2937`; description Inter 12 `#a3a3a3`):
  - `OI:` `Outgoing Influence — number of policies this policy affects (non-zero row cells)`
  - `II:` `Incoming Influence — number of policies that affect this policy (non-zero col cells)`
  - `WOI:` `Weighted Outgoing — sum of scores in the row (strength of influence exerted)`
  - `WII:` `Weighted Incoming — sum of scores in the column (strength of influence received)`
- Table columns: `Policy` (code, bold), `OI`, `II`, `WOI`, `WII`, `Full Policy Name`.
  - Header tooltips: `Policy code`, `Outgoing Influence\n(non-zero row count)`, `Incoming Influence\n(non-zero col count)`, `Weighted Outgoing\n(row sum)`, `Weighted Incoming\n(col sum)`.
  - Formats: OI and II are integers; WOI and WII are `+.2f`.
  - Rows are in fixed policy order and cannot be sorted. Row stripes `#f5f7fa` / `#eaeef4`; header `#426387` / `#f5f7fa`.
- OI/II colour by `ratio = v/(n−1)`:

  | Condition | Background | Text |
  |---|---|---|
  | ≥ 0.75 | `#7799b9` | `#ffffff` |
  | ≥ 0.5 | `#a6bcd3` | `#1f2937` |
  | ≥ 0.25 | `#d0dbe7` | `#1f2937` |
  | otherwise | `#eae7e0` | `#666666` |
  | n ≤ 1 | `#d9d9d9` | `#555555` |

- WOI/WII colour, with **absolute** thresholds:

  | Condition | Background |
  |---|---|
  | > 1.5 | `#177e40` |
  | > 0.5 | `#25c263` |
  | > 0 | `#88edaf` |
  | = 0 | `#d9d9d9` |
  | ≥ −0.5 | `#f5c07a` |
  | ≥ −1.5 | `#e07b39` |
  | otherwise | `#ef4444` |

- `compute_scores` (:107-142, cached): `oi`/`ii` count nonzero off-diagonal cells in the row/column; `woi`/`wii` are signed row/column sums rounded to 2 dp. `None` counts as 0.

##### Range of Influence (range_of_influence_tab.py)

- Title `Range of Influence  —  {m}`, with the subtitle `max entropy = {hmax:.4f}` (Inter 11 italic, `#a3a3a3`).
- Explanation: `Entropy measures how evenly a policy distributes its outgoing influence. High = spread across many policies. Low = concentrated on few.`
- `Categories:` row:

  | Badge | Threshold text |
  |---|---|
  | `Low` | `H < 25% of max` |
  | `Low-to-Medium` | `25% ≤ H < 50% of max` |
  | `Medium-to-High` | `50% ≤ H < 75% of max` |
  | `High` | `H ≥ 75% of max` |

- Table columns: `Policy`, `Entropy` (4 dp), `Category` (bold, coloured), `Full Policy Name`.
  - Header tooltips: `Policy code`; `Shannon entropy H (base 2)\n0 = fully concentrated\nlog2(n-1) = perfectly distributed`; `Influence distribution category\nbased on fraction of max entropy`.
- Category colours (also used by PCA):

  | Category | Background | Text |
  |---|---|---|
  | Low | `#a3a3a3` | `#ffffff` |
  | Low-to-Medium | `#a7f3d0` | `#2d2d2d` |
  | Medium-to-High | `#34d399` | `#ffffff` |
  | High | `#059669` | `#ffffff` |

- `compute_entropy` (:82-127, cached):
  - `p_j = |s_ij| / Σ|s_i·|` over nonzero outgoing scores; `H = −Σ p log2 p`, 4 dp.
  - `hmax = log2(n−1)` if n > 2; **1.0 if n = 2**; 0 otherwise.
  - Category by `H/hmax` at 0.25 / 0.5 / 0.75. No outgoing influence gives `Low`.

##### PCA (pca_tab.py)

- Title `PCA  —  {m}`.
- Stats line `PC1: {p1}%   PC2: {p2}%   Total explained: {p1+p2}%`.
- Invalid state, shown alone: `PCA requires at least 3 policies.`, or `numpy is required for PCA.\nInstall it with:  pip install numpy`.
- Control: label `Colour by entropy category:` followed by a checkbox with no text, default off. The label is not clickable.
- Scatter on a Tk canvas:
  - margin 60; x and y scaled independently;
  - dashed `#cccccc` axes at zero, or at the centre when zero is out of range;
  - axis labels `PC1 ({p1}%)` and `PC2 ({p2}%)` (Inter 9, `#666666`); no ticks.
- Points:
  - radius 16, outline 1.5, white code label (Inter 8 bold);
  - fill `#2c4a6e` with a white outline, or, in entropy mode, the category colour with the category text colour as outline.
- Hover tooltip `{code}:  {policy}`. Hint below the plot: `Hover over a point to see the full policy name.`
- In entropy mode a legend appears: `Entropy categories:` plus the four badges.
- `Save as PNG` sits below the plot, at the right.
- `compute_pca` (:65-121, not cached):
  - X is n×(n−1), each row with its own diagonal removed;
  - columns are standardised (population standard deviation, 0 → 1);
  - SVD; explained variance in % to 1 dp; coordinates = `X_std @ Vt[:2].T`;
  - n < 3 makes the result invalid.

##### Network Analysis (network_tab.py)

- Title `Network Analysis  —  {m}`.
- Stats line `{n} nodes  |  {e} directed edges  |  density: {d}`, plus `  |  {k} isolated` when k > 0. Density is `e/(n(n−1))`, 3 dp.
- `Save as PNG` is in the title bar, at the right.
- **Layout:** network on the left (2/3 width) and centrality table on the right (1/3).
- **Controls:**
  - `Layout:` dropdown with options `Circular`, `Force-Directed` (default), `Spectral`, `Shell`.
  - `Focus Policy:` dropdown with `Full Network` (default) followed by `{code}: {policy}` for each policy.
  - Custom dropdowns: border `#d3d3d3`, `#426387` when open; items 34 px, hover `#f0f4f8`; up to 9 visible, then scrolls.
- **Legend:** `━━` swatches labelled `Positive` (`#1a6e3c`), `Negative` (`#b71c1c`) and `Isolated` (`#aaaaaa`).
- **Canvas:** white, 2 px `#2c4a6e` border, redrawn 50 ms after a resize.
- **Edges:**
  - every nonzero off-diagonal score; green if positive, red if negative;
  - width 4 if |s| ≥ 2.5, 2.5 if |s| ≥ 1.5, otherwise 1;
  - arrowhead `(10,12,4)`;
  - for two-way pairs, the code intends a ±9 px offset (see §4).
- **Nodes:** radius 18, `#2c4a6e` (`#aaaaaa` if isolated), white outline 1.5, code label in white Inter 8 bold. Hover tooltip `{code}:  {policy}`.
- **Ego view (Focus Policy):**
  - a star of only the focus policy's edges, using the chosen layout;
  - heading `Ego Network:  {code}  ({policy})`;
  - the focus node is `#5a7fa8`, radius 22;
  - edge labels `{s:+.2f}` in the edge colour;
  - empty state `{code} has no direct connections.`, which is drawn underneath a grey node.
- **Layouts** (all deterministic; no random seed):

  | Layout | Algorithm |
  |---|---|
  | Circular | Starts at the top and runs clockwise. Radius `max(40, min(w,h)/2−80)`. |
  | Force-Directed | Fruchterman–Reingold, 90 iterations, starting from the circle. `k = √(4/n)`. Attraction is weighted by `0.55 + min(\|s_ij\|+\|s_ji\|, 6)/6`. Temperature `0.12·(1−t/90)+0.01`. Positions are clamped to ±1.2, then stretched to fill the canvas (aspect ratio not kept). |
  | Spectral | The two smallest nonzero eigenvectors of the undirected Laplacian. Adds `0.02·degree` to y. Falls back to Circular. |
  | Shell | Three rings by betweenness (20% / 30% / rest) at radii 0.28 / 0.58 / 0.88. |

- **Interactions:** no zoom, no pan, no node dragging, no edge hover, no threshold filter.
- **Centrality table** (drawn on a canvas):
  - Heading `Centrality Measures` (Inter 11 bold, `#2c4a6e`); subtitle `Betweenness: broker role  |  Closeness: reachability`.
  - Columns `Policy` (code), `Betweenness`, `Closeness`, `Full Name`. Numbers 4 dp.
  - **Sorted by betweenness, highest first**, and the user cannot change the sort. Row stripes as in the other tables.
- `compute_centrality` (:275-320, cached):
  - **Distance** `1/|s|`; positive and negative edges are both kept.
  - **Betweenness:** Brandes, divided by `(n−1)(n−2)`.
  - **Closeness:** out-distance Wasserman–Faust, `(r/(n−1))/mean d`.

##### LLM Interpretation (llm_tab.py)

- Title `LLM Interpretation  —  {m}`, with the subtitle `API key is used once and never stored.`
- Controls:

  | Control | Details |
  |---|---|
  | `Engine:` | Options `Groq` (default) and `OpenAI`. |
  | `Model:` | Groq: `llama-3.3-70b-versatile`. OpenAI: `gpt-4o-mini`, `gpt-4o`. Changing the engine resets the model to the first in the list. |
  | `API Key:` | Masked with `•`. No placeholder. |
  | `Show key` | Checkbox; unmasks the key. |
  | `Generate Interpretation` | Shows `Generating...` and is disabled (grey `#6b7280`) while running. |
  | `Download as TXT`, `Download as PDF` | Always enabled. |
  | `Interpretation:` | Label above a read-only output text box. |

- Status line:

  | When | Text |
  |---|---|
  | While running | `Calling {engine} / {model} ...` |
  | After success | `Done.` |
  | After failure | `Error.` |

- Message boxes:

  | Title | Message |
  |---|---|
  | `API Key Required` | `Please enter your API key before generating.` |
  | `LLM Error` | `The request failed:\n\n{error}` |
  | `Nothing to Save` | `Generate an interpretation first.` |
  | `Saved` | `Saved to:\n{path}` |
  | `PDF Error` | `{exception}` |

- Error texts:
  - `HTTP {code} from API:\n\n{msg}`
  - `Network error: {reason}`
  - `Unexpected response structure:\n{data}`
  - `PDF export requires reportlab or fpdf2.\nInstall with:  pip install reportlab\nor:            pip install fpdf2`
- **Request:**
  - POST to `{base}/chat/completions` with `temperature 0.3`, `max_tokens 4096`, timeout 120 s, no streaming.
  - Base URLs: `https://api.groq.com/openai/v1`, `https://api.openai.com/v1`.
  - Runs on a daemon thread, with UI updates via `after(0, …)`. The key field is cleared after both success and failure.
- **System prompt:** `You are an expert policy analyst specialising in policy coherence and systems thinking. You provide rigorous, evidence-based, in-depth interpretations of policy interaction analyses. Your responses are structured, analytical, and written for policy professionals.`
- **User prompt** (`build_prompt`, :101-196) contains:
  - the policy list;
  - the score matrix (`scale: -3=Cancelling to +3=Indivisible, 0=diagonal`);
  - the coherence scores;
  - Shannon entropy;
  - centrality, sorted by betweenness;
  - seven required sections: `## 1. Overall Coherence Assessment`, `## 2. Key Synergies`, `## 3. Key Conflicts`, `## 4. Influential Policies`, `## 5. Range of Influence`, `## 6. Network Structure`, `## 7. Strategic Recommendations`.

  PCA, per-DM agreement and Results Insights are **not** included.
- **Rendering:** lines starting with `##` or `1.`–`7.` are styled as headers (Inter 11 bold, `#2c4a6e`). Other markdown is shown as raw text.

#### 1.12 Multiple projects

- Any number of projects can exist at once, each with independent state (`Project` dataclass, app.py:179-188).
- Project names must be unique; this is enforced in the dialog, and imports add ` 2`, ` 3`, … to the file stem.
- Projects are switched only through the sidebar.
- **Each project is locked to the policy list of its first DM matrix.** Adding DMs reuses that list; imports must match it.
- If every DM is removed, the next Add Decision-Makers dialog asks for policies again.
- Nothing is saved to disk except exports. There is no "save project", and closing the app loses everything.

### 2. Rating scale and theme (constants.py, theme.py)

| Rating | Score | Fill | Text |
|---|---|---|---|
| Indivisible | +3 | `#0B6E6E` | `#ffffff` |
| Reinforcing | +2 | `#2A9D8F` | `#ffffff` |
| Enabling | +1 | `#6BAF92` | `#2d2d2d` |
| Neutral | 0 | `#B0B7C3` | `#555555` |
| Constraining | −1 | `#E9C46A` | `#2d2d2d` |
| Counteracting | −2 | `#E76F51` | `#ffffff` |
| Cancelling | −3 | `#9B2226` | `#ffffff` |

| Token group | Values |
|---|---|
| Fonts | Inter only: Regular, Medium, Bold and Italic TTFs in `assets/fonts/`. Sizes: small 9, normal 10, header 11, title 14, page title 30. |
| Core palette (constants.py:78-89) | bg `#ffffff` · panel `#eae7e0` · accent `#2c4a6e` · accent2 `#5a7fa8` · page title `#37506d` · text `#1e1e1e` · text light `#666666` · border `#c8c4bc` · tab bg `#d8d4cd` · button `#2c4a6e` / `#ffffff` · danger `#b71c1c` |
| Recurring hard-coded colours | sidebar `#fafbfc` · navy text `#2c3b4e` / `#30455c` · header cell `#426387` · muted `#a3a3a3` · divider `#e6e6e6` · soft fills `#f5f7fa` / `#eaeef4` / `#d0dbe7` · error `#DC2626` · tooltip `#fffbe6` · hover blue `#f0f4f8` |
| Modals (theme.py:59-116) | bg `#eaeef4`, border `#d0dbe7`, radius 11, title 22 `#1f2937`, subtitle 10 `#a3a3a3`, divider `#d3d3d3`, fields 35 px / radius 4 / border `#e6e6e6`, placeholder `#d3d3d3` |
| Buttons | 33 px tall, radius 5, icon 14 px, gap 7, padx 20 (18 for primary), Inter 11. Primary `#2c3b4e`→`#37506d` (modal primary `#2c4a6e`→`#1a3550`). Secondary `#f5f7fa`→`#eaeef4`. Hover is eased over about 16 ms frames. |
| Icons | All Lucide paths are drawn on canvases in code: waypoints, folder-plus, user, user-plus, chart-network, network, file-up, file-down, file, pencil, trash, play, plus, chevrons, image-down. |
| Assets | `assets/fonts/Inter-*.ttf` (4 files) and `assets/fonts/logo_icon_sidebar.png`. **The PNG is not referenced anywhere in code**; the sidebar logo is drawn on a canvas. |

`theme.py` is mostly **not** the source of truth: most of its tokens duplicate inline literals or are unused, and some disagree with the code (§4).

### 3. Exports

| Export | Trigger | Default name and format | Contents | Source |
|---|---|---|---|---|
| Project workbook | Top bar `Export Excel` | `{project}_coherence.xlsx` (spaces → `_`). Dialog title `Export project: {project}`; filter `Excel Workbook` `*.xlsx`. | One sheet per DM, then for **every past run**: `Aggregated ({pfx})`, `Coh Scores ({pfx})`, `Range Influence ({pfx})`, `Centrality ({pfx})`. `pfx` is `Avg`, `Median`, `Median (Lower)`, `Median (Upper)`, `Majority` or `Weighted`, plus ` {k}` when there are several runs. Sheet names are cut to 31 characters. | app.py:3042-3217 |
| Export messages | — | `No Project` / `Create a project first.` · `Nothing to Export` / `Add at least one matrix before exporting.` · `Export Complete` / `Saved to:\n{path}` · `Export Failed` / `{exc}` · `openpyxl is required.\nInstall: pip install openpyxl` · status `Exported to: {path}` | — | app.py:3043-3071, 3090 |
| Network plot | `Save as PNG` | `network_plot.png`. Dialog `Save Network plot`; message `Network plot saved to:\n{path}`. Fallback `.ps` with `Saved as PostScript:\n{path}\n\nOpen with any PS viewer or convert with Ghostscript.` | A screen grab of the canvas | network_tab.py:986-1013 |
| PCA plot | `Save as PNG` | `pca_plot.png`. Dialog `Save PCA plot`; message `PCA plot saved to:\n{path}`. The `.ps` fallback reports errors as `Save Error`. | A screen grab | pca_tab.py:337-368 |
| LLM text | `Download as TXT` / `Download as PDF` | `policy_interpretation.txt` / `.pdf`. Dialogs `Save interpretation as TXT` / `Save interpretation as PDF`. | Raw response; the PDF uses reportlab (A4, 2 cm margins) or fpdf2 | llm_tab.py:886-1005 |

**Workbook layout** (app.py:3117-3145):

| Cell(s) | Contents |
|---|---|
| `A1` | `Policy Index` |
| `B1…` | `{code}: {name}` |
| `A3` | `Influencing / Influenced` |
| Row 3 | Code headers, white bold on `2C4A6E` |
| Row headers | Codes |
| DM sheets | Rating labels, coloured |
| Aggregated sheets | `0.00` numbers |

Other sheets have the headers `Code, Policy, OI, II, WOI, WII` / `Code, Policy, Entropy, Category` / `Code, Policy, Betweenness, Closeness`. These do not use the Coherence Scores and Network tabs' column names (`Policy` = code, `Full Name`). PCA, Results Insights and `hmax` are not exported. The workbook is not a round-trip import file.

### 4. Inconsistencies, dead UI and wrong texts the plan must settle

**Defects (behaviour)**

1. **Projects cannot be renamed or deleted.** `_rename_project` and `_delete_project` are never called (app.py:2323-2368). The delete confirmation text `Permanently delete project "{name}" and all its data?\nThis cannot be undone.` and `Project renamed to "{name}".` are therefore dead. Decide whether the web version offers both.
2. **Two-way network arrows overlap.** The perpendicular offset flips sign twice (network_tab.py:932-940, 1111-1118).
3. **PCA feature columns are misaligned** because each row drops its own diagonal (pca_tab.py:90-93). This is a backend correctness decision.
4. **Story highlighting is broken.** The regex `.+?\(P\d+\)…` matches from the start of the text, so most of the story takes the relation colour and per-role code colouring never applies (results_insights_tab.py:771-786).
5. **"Most Contested" is never empty.** Every cell is a candidate, so it always names a pair, even at 100% agreement, with the caption `Moderate disagreement`. The fallback caption is also wrong (results_insights_tab.py:439-442, 1036-1039). As a result, story branches 3-4 and interpretations 4-5 are practically unreachable.
6. **Strongest Link ignores negative edges** and always labels its value `Reinforcing`. With only negative edges it shows `No non-zero relation` (results_insights_tab.py:1013-1024).
7. **Top driver and top dependent are chosen by maximum WOI/WII even when negative.** The text then claims "strongest outward influence" for a negative score.
8. **The sidebar is not refreshed** after `Rename Tab` or `Delete Tab` on a DM (app.py:2458-2527), so it shows stale DM names.
9. **Rename Tab has no duplicate-name check.** Imported sheets are also not checked against existing DM names. Both can create duplicate DMs.
10. **Removing an analysis tab leaves its run in the export** (`agg_results`). Re-running appends a new run, so the export grows with every run (app.py:2617, 2486-2507).
11. **Results go stale silently.** After matrices are edited, the analysis view still shows old results with no warning.
12. **Fewer than 3 DMs silently forces Average**, with no message. Users with two DMs never see the method choice.
13. **Unresolved ties appear as `0.00`.** The Aggregated tab, scores and the LLM prompt all treat `None` as 0. Ties are resolved first in the current flow, but the caches are not invalidated (`resolve_ties` does not clear `_cached_*`).
14. **`max entropy = 1.0000` when n = 2.** The tooltip formula `log2(n-1)` gives 0 (range_of_influence_tab.py:96).
15. **"Low" means two different things.** It is shown both for "no outgoing influence" and "concentrated on one policy" (H = 0).
16. **The LLM Generate button reverts on hover.** It returns to its enabled label and colour while a request is running. The previous `_response` stays downloadable after a failed rerun. Numbered list items `1.`–`7.` are styled as headers (llm_tab.py:694-736, 823, 869-872).
17. **Network and PCA PNGs are screen grabs.** They can capture overlapping windows and tooltips and are offset on HiDPI displays. The network save path has no error handling.
18. **Mouse wheel handling is inconsistent.** It divides by 120 even on macOS in the matrix editor, the Aggregated tab and the modal dialogs, while other tabs special-case macOS.
19. **Escape on the custom dropdown popups probably never fires.** They are borderless and never take focus.

**Inconsistent labels and texts**

20. **The method name has four spellings:**

    | Where | Average | Median | Majority | Weighted |
    |---|---|---|---|---|
    | Dialog | `Average` | `Median (Ordinal)` | `Majority Rule` | `Weighted by Importance` |
    | Tab titles | `Average` | `Median (Lower)` / `Median (Upper)` | `Majority Rule` | `Weighted` |
    | Insights card | `Average` | `Median` (drops Lower/Upper) | `Majority Rule` | `Weighted` |
    | Excel prefix | `Avg` | `Median` / `Median (Lower)` / `Median (Upper)` | `Majority` | `Weighted` |

21. **The weights text says "sum to exactly 1.0"** while the code accepts ±0.01 (aggregation_dialog.py:438, 474, 600; aggregator.py:361-363).
22. **The empty project text points to a button that does not exist.** It says `Click  "+ Add Decision-Maker"  to add the first matrix.`; the real control is the sidebar `DECISION-MAKERS` +, and the dialog is titled `Add Decision-Makers`.
23. **`{n} cells to fill` shows the total cell count**, not the remaining blanks.
24. **"Agreement" means two different metrics.** The Overview card's `Agreement` is scaled Spearman; the Most Contested card's `Agreement: x.xx` is the modal-share ratio.
25. **Arrows vary:** ASCII `->` in the story and Strongest Link, `→` in the tags, `↔` in Most Contested (which suggests a two-way link on a directed matrix), and `<-- Influencing  |  Influenced -->` on the axis.
26. **The axis label sits above the column headers**, but columns are the *influenced* side. The export uses a different wording, `Influencing / Influenced`.
27. **The same columns have different names.** In the tabs, `Policy` is the code and `Full Policy Name` / `Full Name` is the name; in the export the headers are `Code` / `Policy`.
28. **Small wording differences:**
    - `(non-zero col cells)` in the legend vs `(non-zero col count)` in the tooltip.
    - `Import from excel` (lowercase "excel") vs `Import Excel`.
    - `Colour` (British) vs `Color` elsewhere in code.
    - Title separators: `  —  ` in the tabs vs `  -  ` in dead code.
29. **Import warnings are mislabelled.** `Sheet "…": empty, skipped.` appears under the heading `The following sheets have blank cells:`.
30. **The file picker offers `.xls`**, which openpyxl cannot read.
31. **`Neutral/Uncertain` uses `#2563EB`** while the unused theme token says `#b45309`. Health values have no `%` sign.
32. **WOI/WII colour thresholds (±0.5, ±1.5) are per-cell values applied to row and column sums** (range up to ±3(n−1)), so most sums land in the extreme colours.
33. **`hmax` is stored in every entropy row**, and the PCA tab imports private `_CAT_COLORS` from range_of_influence_tab.

**Dead or duplicated UI**

34. **Dead dialogs:** `NewMatrixDialog` (title `Add Decision-Maker Matrix`, heading `New Policy Coherence Matrix`, a `.csv`/`.xlsx` policy-list import) and `_ProjectNameDialog` (`Give this project a unique name.`). Also dead: `_read_policies_from_file`, `style_button`, `_FlowFrame`'s stray `@dataclass`, and the breadcrumb remnants (`crumb_bar` height 0; `_rename_project` looks for a `Project:  {name}` header that no longer exists).
35. **Results Insights dead code.** About 18 render methods and their texts are never shown (Analysis Config pills, Cause-Effect Positioning scatter, Critical Relations, Conflict and Consensus Heatmap, System Overview, Prominence Ranking, the narrative). Quadrant labels (`System Driver`, `Strategic Lever`, …) are computed but not displayed. They conflict with the role names (`Strategic Driver`, `Balanced Node`).
36. **The fixed-policy section `Policies are inherited from the current project.`** can never appear (dialogs.py:510).
37. **`theme.py` has duplicates and conflicts.** `MATRIX_PADX` is defined twice (32 and 24). These tokens conflict with `matrix_widget.py`:

    | Token | theme.py | matrix_widget.py |
    |---|---|---|
    | `MATRIX_CELL_W_LARGE` | 160 | 200 |
    | `MATRIX_AXIS_H` | 22 | 40 |
    | `MATRIX_CELL_GAP` | 4 | 6 |

    In addition, `KEY_INSIGHTS_*`, `RESULTS_BANNER_*`, `EMPTY_STATE_*`, `TOPBAR_*`, `VIEW_TOGGLE_*` and `TAB_*` are largely unused; app.py hard-codes the same values. Fonts and other assets are covered in §2.
38. **Code is copied between files:** `_PillScrollbar` (2 copies), `_round_rect`/`_rrect_pts` (5+), tooltips, scroll inertia, the custom dropdown (network, LLM), and the save button (network, PCA).
39. **The `__init__.py:run()` launcher** skips DPI awareness and font loading (already noted in AGENTS.md).
40. **`style_button` and various `theme.py` constants** (`MODAL_DM_PLACEHOLDER`, `TOPBAR_RUN_ANALYSIS_ICON_*`) are unused.

### 5. Suggested web flow mapping

The flow below has one question per step, then a results area. Step texts reuse the legacy strings above.

| # | Web step (question) | Legacy source | Notes |
|---|---|---|---|
| 0 | Landing / empty state: `Start a new policy coherence assessment`, the WORKFLOW list, `New Project`, and a "Start from Excel" alternative | §1.4, `Import from excel` | Replaces the empty workspace and the sidebar empty state. |
| 1 | "What is this project called?" | Create dialog, Project Name | Hint and placeholder verbatim; uniqueness check only if projects are listed. |
| 2 | "Who are the decision-makers?" | DM section | List editor with `Add`; minimum 1, unique. The `e.g. Expert A…` placeholders. |
| 3 | "Which policies are you assessing?" | Policy section | Minimum 2, unique. Show the auto codes `P1…Pn`. |
| 3b | (alt) "Import matrices from Excel" | §1.7 | Uploads the workbook. Warnings and errors shown inline with verbatim texts. Fills steps 2-4. |
| 4..k | "Rate how {DM} sees each interaction" (one step per DM) | Matrix editor §1.9 | Grid of rating selects with the legend and axis label. Shows progress `{filled}/{total} cells filled`. Highlights blanks, which the legacy app lacks; the plan should decide whether to add it. |
| k+1 | Review: completeness per DM | `Incomplete Matrices` message | Blocks moving on until complete. Lists blanks with the `P1->P2` format. |
| k+2 | "How should ratings be combined?" | Aggregation Method dialog | Four cards with verbatim descriptions. Decide whether to keep the rule "fewer than 3 DMs → Average" (and say so). |
| k+3 | "How much weight does each decision-maker carry?" (Weighted only) | Weights dialog | Live `Sum:` and the four error texts. Decide on the tolerance wording. |
| k+3 | "Lower or upper median?" (Median with an even DM count only) | Median Choice | Two cards. |
| k+4 | "Resolve tied cells" (Majority with ties only) | Tie dialog | One select per tie. Show policy names and per-DM votes, which the legacy app lacks. |
| R | Results area: tabs **Insights · Aggregated matrix · Coherence scores · Range of influence · PCA · Network · AI interpretation**, plus an export bar | §1.11, §3 | Tab labels without the `({method})` suffix; show the method once in a header instead. Export bar: Excel workbook, Network PNG, PCA PNG, LLM TXT/PDF. |

**No natural web equivalent; needs a decision:**

1. **Multi-project sidebar and switching.** There is no persistence in Tk; the web version could hold a single project, a local list, or server-side storage.
2. **The DM / Analysis pill toggle and the scrolling tab strips with drag momentum.** These are replaced by step navigation and result tabs.
3. **`Rename Tab` / `Delete Tab` as top bar actions.** These become inline edits in steps 2-4. Deleting a result tab has no web purpose.
4. **The status bar `Ready` messages.** Replace them with toasts or inline status, or drop them. Their texts are listed above in case parity is wanted.
5. **Collapsing the sidebar, platform-specific font sizes, Windows DPI handling and font installation.** Web fonts replace all of these.
6. **Screenshot-based PNG saving.** Use server-rendered or SVG/canvas exports instead.
7. **Hover-polling button animations, custom dropdown popups and pill scrollbars.** These become ordinary components.
8. **The API-key promise `used once and never stored`.** In a web app the key passes through the API server, so the wording and the handling must be re-specified.

## Limitations

- Nothing was run. Layout and pixel values are as coded; how they render was not observed, especially on Windows and Linux, where several sizes differ.
- The details for `aggregation_tab.py`, `coherence_scores_tab.py`, `range_of_influence_tab.py`, `network_tab.py`, `pca_tab.py`, `results_insights_tab.py` and `llm_tab.py` come from delegated agents that read those files in full. I re-verified only the key defects (items 2, 3, 4, 5) and the LLM engine list. Other line numbers for those files should be re-checked when a plan cites them.
- Aggregation formulas in `aggregator.py` (average rounding, majority ordering, median, weighted) were outside this UI inventory except for labels, validation and the result model. The backend port plan should inventory them.
- Hover-only texts, such as tooltips, are listed as coded; whether they appear on every platform was not tested.

## Recommendations

1. In the web UI plan, adopt §1 and §3 as the parity checklist, and copy the verbatim strings into its UI text constants.
2. Before implementation, settle items 1-40 in §4 in the plan's "Settled Decisions". The most important are:
   - project lifecycle (create, rename, delete, persistence);
   - one canonical method label set;
   - whether the defect fixes (2, 3, 5, 6, 7, 14) change computed results, which would make them backend decisions;
   - stale-results behaviour;
   - whether the dead Results Insights views are revived or dropped.
3. Use §5 as the starting step map. Decide explicitly on the "fewer than 3 DMs → Average" rule and on the tie dialog content.
4. Have the backend port plan cover the computations listed in §1.11:
   - `compute_scores`
   - `compute_entropy`
   - `compute_pca`
   - `compute_centrality` and the layout algorithms
   - `compute_insights` and its story and interpretation templates
   - `build_prompt`

## References

- `tk-app/app.py` (shell, sidebar, top bar, project page, run flow, import, export)
- `tk-app/dialogs.py`, `tk-app/aggregation_dialog.py` (dialogs)
- `tk-app/matrix_widget.py` (matrix editor)
- `tk-app/aggregation_tab.py`, `coherence_scores_tab.py`, `range_of_influence_tab.py`, `pca_tab.py`, `network_tab.py`, `results_insights_tab.py`, `llm_tab.py` (result tabs)
- `tk-app/constants.py`, `tk-app/theme.py`, `tk-app/assets/fonts/` (theme and assets)
- `tk-app/importer.py`, `tk-app/aggregator.py`, `tk-app/models.py` (import messages, labels, data model)
- `AGENTS.md` (repository guidance)
- `dematelab/docs/plans/2026-11-16-rebuild-ui-in-tanstack-start-plan.md` ("Parity Inventory" model)
