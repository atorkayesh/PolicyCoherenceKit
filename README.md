# Policy Coherence Kit

A desktop application for assessing, aggregating, and analysing policy coherence across multiple decision-makers.

---

## What It Does

Policy Coherence Kit allows researchers and policy professionals to:

- Build **n×n policy interaction matrices** for multiple decision-makers or experts
- Rate how policies influence each other using a structured 7-point linguistic scale
- **Aggregate** views across decision-makers using average, majority rule, or weighted methods
- Run a suite of **analytical tools** on the aggregated results
- Generate **LLM-powered interpretations** of the results using your preferred AI engine
- Manage multiple independent **projects** in a single session
- **Export** all results to Excel

---

## Coherence Rating Scale

| Rating | Score | Meaning |
|---|---|---|
| Indivisible | +3 | Policies are fully intertwined and inseparable |
| Reinforcing | +2 | Policies mutually strengthen each other |
| Enabling | +1 | One policy helps the other work better |
| Neutral | 0 | No meaningful interaction |
| Constraining | -1 | One policy limits the other's effectiveness |
| Counteracting | -2 | Policies work against each other |
| Cancelling | -3 | One policy completely negates the other |

---

## Features

### Project Management
- Create multiple independent projects in a single session
- Each project has its own decision-makers, matrices, and analysis results

### Matrix Input
- Enter policy names manually (one per line)
- Import full matrices from **multi-sheet Excel workbooks** — each sheet becomes one decision-maker
- Diagonal cells are permanently locked to *Neutral*
- Colour-coded dropdowns for rating each cell

### Aggregation
- **Average**: arithmetic mean across decision-makers
- **Median**: ordinal median aggregation, with lower/upper choice when the number of decision-makers is even
- **Majority Rule**: most common rating at each cell
- **Weighted**: weighted aggregation using user-defined decision-maker weights

### Analysis Tabs (generated per aggregation run)

| Tab | Description |
|---|---|
| **Aggregated Matrix** | Numeric score matrix (-3 to +3), colour-coded |
| **Coherence Scores** | OI, II, WOI, WII — outgoing/incoming influence counts and sums |
| **Range of Influence** | Shannon entropy per policy — concentrated vs distributed influence |
| **PCA** | 2D scatter plot of policy influence profiles (PC1 + PC2), with entropy colouring option |
| **Network Analysis** | Directed weighted network with 4 layout options + betweenness/closeness centrality |
| **LLM Interpretation** | Structured AI-generated interpretation using your API key |

### Network Layouts
- **Circular** — equal spacing baseline
- **Force-Directed** (default) — Fruchterman-Reingold spring model
- **Spectral** — eigenvector-based clustering of similar policies
- **Shell** — high-betweenness policies in the centre ring

### Export
- **Excel** — one workbook per project with sheets for: all DM matrices, aggregated matrix, coherence scores, range of influence, and network centrality
- **LLM interpretation** — downloadable as `.txt` or `.pdf`
- **PCA and Network plots** — saveable as PNG (requires Pillow) or PostScript

---

## Installation

### Requirements

- Python 3.9 or higher
- Required packages:
  - `openpyxl`
  - `numpy`
  - `reportlab`
- Optional package for PNG export:
  - `Pillow`
  
Install dependencies: 
```bash
pip install openpyxl numpy reportlab Pillow
```
### Setup

1. Clone or download this repository:
```bash
git clone https://github.com/atorkayesh/PolicyCoherenceKit.git
```
2. Navigate to the project root folder:
```bash
cd PolicyCoherenceKit
```
Main application files are located at the repository root.

```
- `main.py` - application launcher
- `app.py` - main GUI and workflow logic
- `aggregator.py` - aggregation methods
- `aggregation_dialog.py` - aggregation dialogs
- `aggregation_tab.py` - aggregated matrix view
- `coherence_scores_tab.py` - coherence scores module
- `range_of_influence_tab.py` - entropy / range of influence module
- `pca_tab.py` - PCA module
- `network_tab.py` - network analysis module
- `results_insights_tab.py` - consensus, disagreement, and summary insights
- `llm_tab.py` - LLM interpretation module
- `importer.py` - Excel import logic
- `dialogs.py` - reusable dialogs
- `models.py` - data models
- `matrix_widget.py` - matrix input widget
- `constants.py` - shared constants and labels
- `theme.py` - theme and UI styling
- `Example data/WEF Nexus Example.xlsx` - sample workbook for testing
```

3. Run the app:

```bash
python main.py
```

---

## LLM Interpretation

The LLM tab supports the following engines:

| Engine | Notes |
|---|---|
| **Groq** | Free tier available |
| **OpenAI** | Requires paid API key |

> **Privacy:** API keys are used for a single request and cleared from memory immediately. They are never stored to disk.

The interpretation covers seven structured sections:
1. Overall Coherence Assessment
2. Key Synergies
3. Key Conflicts
4. Influential Policies
5. Range of Influence
6. Network Structure
7. Strategic Recommendations

---

## Excel Import Format

When importing a multi-sheet workbook, each sheet must follow this structure:

```
[blank]          Climate Policy   Energy Reform   Urban Mobility
Climate Policy   Neutral          Reinforcing     Enabling
Energy Reform    Constraining     Neutral         Indivisible
Urban Mobility   Cancelling       Enabling        Neutral
```

- **Row 1, Col 1**: ignored (corner cell)
- **Row 1, Col 2+**: full policy names (column headers)
- **Col 1, Row 2+**: full policy names (row headers, must match column headers exactly)
- **Data cells**: one of the 7 rating labels (case-insensitive)
- **Sheet name**: becomes the decision-maker name

---

## Example Data
A sample workbook is provided in the repository: Example data/WEF Nexus Example.xlsx

---

## Running with Docker

The app can also run in a container and be used from a browser (via noVNC), with no local Python or Tk setup. You need Docker and [uv](https://docs.astral.sh/uv/). All commands run from the repository root:

```bash
uv run scripts/docker.py up          # build, start, and open http://localhost:6090
uv run scripts/docker.py logs -f     # follow logs
uv run scripts/docker.py restart     # restart the container
uv run scripts/docker.py status      # show container status
uv run scripts/docker.py shell       # open a shell in the container
uv run scripts/docker.py down        # stop and remove the container
```

Add `--prod` to any command to use the production setup instead of the dev one. Use `up --no-build` to skip rebuilding the image and `up --no-open` to skip opening the browser.

| | Dev (`docker-compose-dev.yml`) | Prod (`docker-compose-prod.yml`) |
|---|---|---|
| Image | `Dockerfile.dev` (includes dev tools) | `Dockerfile.prod` (runtime only) |
| Source | Mounted from the repository; the app restarts when a `.py` file changes | Baked into the image; rebuild to update |
| Password | None by default | `VNC_PASSWORD` required in `.env` |
| Exports | `./exports/` on the host | `policycoherencekit-exports` Docker volume |
| Address | `127.0.0.1:${NOVNC_PORT:-6090}` | `127.0.0.1:${NOVNC_PORT:-6090}` (`NOVNC_BIND` to change the interface) |

Setup for production:

```bash
cp .env.example .env   # then set VNC_PASSWORD
uv run scripts/docker.py up --prod
```

Notes:
- In the app's file dialogs, the example workbook is in `examples/` (read-only) and exports should be saved to `exports/`.
- Everyone who opens the URL shares the same app session, so the production setup suits one user at a time. noVNC traffic is not encrypted: before exposing it beyond `localhost`, put it behind a TLS reverse proxy with its own login. VNC passwords are limited to 8 characters.
- Dev and prod share `.env`, so setting `VNC_PASSWORD` for prod also adds a password to the dev session. `NOVNC_PORT` and the other settings there apply when you start with `scripts/docker.py`.
- On Linux, `scripts/docker.py` builds the image for your user ID so `exports/` stays writable. If you run `docker compose` directly, set `APP_UID`/`APP_GID` yourself.
- Dependencies are listed in `pyproject.toml` (used for dependency management only; the app still runs with `python main.py`) and locked in `uv.lock`. After changing `pyproject.toml`, run `uv lock` and rebuild.

---

## License

MIT License — free to use, modify, and distribute with attribution.

---
