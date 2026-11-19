# Policy Coherence Kit API

FastAPI service behind the Policy Coherence Kit web app. It ports everything the legacy Tk app (`tk-app/`) does
apart from drawing widgets: aggregation (Average, Median, Majority Rule, Weighted) with the legacy rules, the five
analyses, chart data for the browser, Excel import, XLSX export, and the AI interpretation with PDF export.
Numbers equal the legacy app's; see [`AGENTS.md`](./AGENTS.md) for the rules and parity details.

## Run

With Docker (recommended), from the repository root:

```bash
make setup && make dev      # http://localhost:50002/api/docs
make check-api              # Ruff format check, Ruff lint, pytest (inside the container)
```

On the host:

```bash
cd apps/api
cp .env.example .env
uv sync --frozen
uv run python main.py       # http://localhost:50002/api/docs
uv run ruff format --check . && uv run ruff check . && uv run pytest
```

## Endpoints (`/api/v1`)

| Method + path | Purpose |
|---|---|
| `GET /health`, `GET /is-alive` | Health and liveness |
| `GET /scales` | Rating scale, methods, rules, colour bands, layouts, limits |
| `POST /setup/validate` | Project, decision-maker and policy names (legacy messages) |
| `POST /matrices/check` | Completeness (first 10 blanks) and aggregation options |
| `POST /weights/check` | Weight-dialog sum and messages (always 200) |
| `POST /aggregation/preview` | Aggregation with ties left open (the tie step) |
| `POST /analysis` | Aggregation and every analysis |
| `POST /analysis/export/xlsx` | `{project}_coherence.xlsx` (current run) |
| `POST /analysis/charts/network?layout=&focus=` | Network chart data (full or ego view) |
| `POST /imports/workbook` | One matrix per sheet (`.xlsx`, ≤ 5 MB) |
| `GET /explanations/providers` | AI providers and models |
| `POST /explanations` | AI interpretation (key per request, never stored) |
| `POST /explanations/export/pdf` | `policy_interpretation.pdf` |

Every results endpoint receives the whole project (`AnalysisRequest`) and recomputes; nothing is stored. JSON
responses use `{success, message, data, metadata, error}`; errors carry a stable `error.code` and, for legacy
messages, `data.title`.

## Parity fixtures

Generated from the legacy app, never edited by hand:

```bash
uv run --frozen --python 3.13 --project tk-app python scripts/generate_parity_fixtures.py   # repository root
```

## Security notes

- AI keys travel with each request: enable HTTPS (`nginx/nginx.prod.conf`) before using the AI feature in production.
- Uploads are size-limited while streaming; zip bombs, XML entities (defusedxml), oversized sheets and
  chartsheets are rejected; exported text cells are never formulas.
