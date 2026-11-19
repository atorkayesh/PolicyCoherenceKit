# Policy Coherence Kit - Agent Guidelines

The Policy Coherence Kit rates how policies influence each other (one directed matrix per decision-maker),
aggregates the decision-makers' ratings, and analyses the result (coherence scores, range of influence, PCA,
network centrality, results insights, AI interpretation). It is rebuilt as a web app in `apps/`; the legacy
Tkinter desktop app lives in `tk-app/` as the read-only reference. App-specific rules are in
[`apps/api/AGENTS.md`](apps/api/AGENTS.md) and [`apps/web/AGENTS.md`](apps/web/AGENTS.md).

---

## How the App Fits Together

```
browser ──► apps/web (TanStack Start, :3001) ──► apps/api (FastAPI, :50002, /api/v1) ──► AI providers (per-request keys)
                 ▲ production: nginx (:8081) routes /api/ to the API and everything else to the web app
```

- The API is stateless: every request carries the whole project (one project per browser session).
- The API computes every number and text; the browser draws charts with ECharts from API chart data and never
  computes values.
- Numbers equal the legacy app's (parity fixtures generated from `tk-app/`); wrong labels are fixed and listed.

### Repository layout

```
apps/api/        FastAPI API (see apps/api/AGENTS.md)
apps/web/        TanStack Start web app
nginx/           Production reverse proxy (the only public entry)
scripts/         generate_parity_fixtures.py + parity/ helpers: the only code that runs against tk-app/
tk-app/          Legacy Tk app with its own Makefile and Compose files (read-only)
data/examples/   Sample workbook (WEF Nexus Example.xlsx)
docs/            plans/, reports/, research/, decisions/
Makefile  docker-compose-dev.yml  docker-compose-prod.yml
```

### `tk-app/` is read-only

Never edit `tk-app/`. Nothing in `apps/` imports, reads or starts it (enforced by
`apps/api/tests/repository_rules_integration_test.py`). To capture legacy behaviour, extend
`scripts/generate_parity_fixtures.py` and regenerate:
`uv run --frozen --python 3.13 --project tk-app python scripts/generate_parity_fixtures.py`.

---

## Running the App

```bash
make setup       # create each service's .env from its .env.example (never overwrites)
make dev         # api and web with hot reload; prints the URLs (web http://localhost:3001, API http://localhost:50002)
make check-api   # Ruff format check, Ruff lint, pytest inside the api dev container
make check       # check-api + check-web
make prod        # production behind Nginx on HTTP_PORT (default 8081)
make help        # every target; legacy app: make -C tk-app help
```

### Docker services

| Service | Container | Port (dev) | Notes |
|---|---|---|---|
| api | `policycoherencekit-api` | 50002 | Healthcheck `/api/v1/is-alive`; source mounted in dev |
| web | `policycoherencekit-web` | 3001 | `make check-web` runs format, lint, typecheck and tests |
| nginx | `policycoherencekit-nginx` | `${HTTP_PORT:-8081}` | Production only |

Compose projects: `policycoherencekit-dev` and `policycoherencekit` (legacy: `policycoherencekit-tk-dev` /
`policycoherencekit-tk-prod`, so all can run on one host next to DEMATELab and ice2kg). Dev and prod use the
same container names: stop one before starting the other.

### Environment files

| File | Holds |
|---|---|
| `apps/api/.env` | `APP_ENV`, `CORS_ORIGINS`, `WEB_CONCURRENCY` |
| `apps/web/.env` | `VITE_APP_ENV`, `VITE_API_BASE_URL` (public, bundled into the client; empty in production) |
| `tk-app/.env` | Legacy only: `VNC_PASSWORD`, `SCREEN_GEOMETRY`, `NOVNC_PORT` |

There is no root `.env`. AI keys are never stored in env files.

---

## Development Workflow

1. Plan first: non-trivial work starts from a plan in `docs/plans/` (follow its authoring guide).
2. Respect the layers and rules in the app's AGENTS.md; record lasting choices in `docs/decisions/`.
3. Keep every code file at or below 300 lines; split by responsibility.
4. Never change maths or legacy-derived texts without regenerating the parity fixtures and recording a decision.
5. Before committing, run `make format` and `make check-api` (and `make check-web` for web changes).

## Pre-Commit Checklist

- [ ] Changes follow the app's AGENTS.md rules
- [ ] Tests written or updated, and all checks pass (`make check-api`)
- [ ] Parity fixtures regenerated from `tk-app/` if maths or legacy-derived behaviour changed
- [ ] Every code file in `apps/` is at or below 300 lines
- [ ] No hardcoded secrets; no AI keys in env files or logs
- [ ] Nothing in `apps/` imports or reads `tk-app/`
- [ ] Docs updated if behaviour or workflow changed

---

## Legacy Tk App (`tk-app/`)
### Run and verify
- This is a flat Python/Tkinter desktop app, not an installable package. Run from `tk-app/`: `cd tk-app && python3 main.py`; imports use `tk-app/` top-level module names.
- Install dependencies with `python3 -m pip install openpyxl numpy reportlab Pillow`. **Pillow is required at startup** (`app.py` imports `PIL` unconditionally), despite the README marking it optional. Python must also provide Tkinter/Tcl/Tk.
- `tk-app/pyproject.toml` (non-package, `[tool.uv] package = false`) and `tk-app/uv.lock` exist only for dependency management and the Docker images; after editing `pyproject.toml`, run `uv lock`. No automated tests, CI, or lint/format/typecheck configuration exists. Do not invent project check commands.
- Docker: `make -C tk-app dev` / `make -C tk-app prod` (`tk-app/Makefile`, wrapping `docker compose -f docker-compose-<dev|prod>.yml`; Compose projects `policycoherencekit-tk-dev` / `policycoherencekit-tk-prod`) runs the GUI in a container served over noVNC at `http://localhost:6090`; `make logs|restart|shell|status|down` act on whichever setup is running. The container starts as root only so `docker/start.sh` can give the `app` user the owner of `tk-app/exports/`, then drops privileges. It runs `python /app/main.py` from `/workspace`, where `examples/` and `exports/` are mounted.
- Syntax check (from `tk-app/`): `python3 -m compileall -q .`. Dependency/import smoke check without creating a window: `python3 -c "import app, aggregator, importer"`. Neither replaces functional testing.
- Manual smoke flow: import `data/examples/WEF Nexus Example.xlsx`, aggregate, open each analysis tab, and export Excel. The UI forces Average for fewer than three decision-makers; use at least three to exercise method selection and four for even-count Median choices.
- Launching `tk-app/main.py` requires a graphical session and installs missing bundled Inter fonts into `~/Library/Fonts` on macOS or `~/.local/share/fonts` on Linux (where it invokes `fc-cache`). Avoid launching it just to check imports.
- Preserve startup order: Windows DPI awareness before importing Tkinter, and `load_inter()` before creating `tk.Tk()`. The alternate `__init__.py:run()` launcher omits these steps.

### Wiring and state
- `app.py` owns project orchestration and Excel export (`_export_to_excel`); `models.py`, `aggregator.py`, and `importer.py` contain Tkinter-free data/aggregation/import logic.
- Each `app.py:Project` owns its matrices and aggregation history. `_create_analysis_tabs` replaces visible analysis tabs but appends to `agg_results`; Excel export includes the full history, not just the displayed run.
- Analysis widgets are created lazily via `_ensure_analysis_tab_loaded`. Register new analysis views in `_create_analysis_tabs` rather than eagerly building all widgets.
- Computations live alongside their views in `*_tab.py`: `compute_scores`, `compute_entropy`, `compute_pca`, `compute_centrality`, and `compute_insights`. Excel export and LLM prompts reuse scores, entropy, and centrality computations; changes affect more than the UI.
- `AggregationResult` caches scores/entropy/centrality/graph analysis in `_cached_*` fields. If mutating result scores after analysis, invalidate all affected caches or create a new result.
- UI tokens are split between `theme.py` (component styling) and `constants.py` (ratings, score mapping, shared palette/fonts/dimensions); check both before adding styling constants.

### Data contracts and gotchas
- Matrices are **directed**: row = influencing policy, column = influenced policy. Input data maps `(row, col)` to rating labels; aggregated scores map the same coordinates to numbers. Diagonal is always `Neutral` / `0.0`.
- Before calling aggregation functions directly, call `check_completeness`; their internal matrix validator checks policy-list compatibility, not blank cells. All decision-makers must use identical policy names **and order**.
- Majority ties have `None` scores until every `TiedCell.chosen` is set and `resolve_ties(result)` runs. Resolve ties before analysis; downstream computations often treat `None` as zero.
- Median is ordinal, not the arithmetic mean of two middle scores: `ordinal_cells` preserves both middle labels for even counts, while `scores` uses the selected lower/upper label. Use `aggregation_method_label` for display names.
- Excel import expects full policy names in row 1/column 1 headers and rating labels (case-insensitive), not numeric scores. Blank off-diagonal cells produce warnings and incomplete matrices. Exported workbooks use a different layout and are **not round-trip import files**.
- Network analysis includes both positive and negative nonzero edges, with shortest-path distance `1 / abs(score)`; entropy likewise uses absolute outgoing weights. Do not silently drop negative interactions.
- LLM calls use a daemon worker with Tk updates dispatched through `after(0, ...)`. Preserve clearing the API-key input on both success and failure; keys are not persisted to disk.
