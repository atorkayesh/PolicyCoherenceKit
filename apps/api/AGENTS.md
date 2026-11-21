# Policy Coherence Kit API - Agent Guidelines

FastAPI API for the Policy Coherence Kit: the four aggregation methods and the rules the legacy GUI enforced, the
five analyses (coherence scores, range of influence, PCA, network centrality, results insights), chart data for
the browser, Excel import, XLSX export, and the AI interpretation with its PDF export, ported from the legacy Tk
app (`tk-app/`). Conventions are copied from DEMATELab. For the whole-app workflow see the
[root `AGENTS.md`](../../AGENTS.md); human-facing setup is in [`apps/api/README.md`](./README.md).

**Stack:** Python 3.13, FastAPI, numpy, openpyxl (with defusedxml), reportlab, httpx, google-genai,
Pydantic Settings, uv, Ruff, pytest

---

## Commands

Run these in the dev container from the repo root: `just check-api`, `just test-api <pytest args>`,
`just format`, `just lint`, `just sh-api` (root `AGENTS.md` → Running the App). The commands below
are what they run, and also work outside Docker.

`scripts/` (the fixture generator) is not mounted in the api container: lint and format-check it on the host
with `just check-scripts` (`uv run --project apps/api ruff check --config apps/api/pyproject.toml scripts`, then
`ruff format --check` with the same options). `tests/repository_rules_integration_test.py` also holds `scripts/**/*.py`
to 300 lines when `scripts/` is present.

```bash
cd apps/api

# Run locally (no other service needed)
cp .env.example .env
uv sync
uv run python main.py

# Format and lint (Ruff replaces Black; line length 120)
uv run ruff format .
uv run ruff check --fix .

# Checks to run before committing
uv run ruff format --check . && uv run ruff check . && uv run pytest

# Tests
uv run pytest -v                                   # All tests
uv run pytest -m "not integration" -v              # Skip integration (parity) tests
uv run pytest tests/parity_integration_test.py -v  # Numerical parity with the Tk app
uv run pytest --cov=. --cov-report=html            # Coverage
```

API docs are live at `http://localhost:50002/api/docs` when the API runs.

---

## Code Style

### Imports

Group imports (standard library, third-party, local), separated by blank lines and sorted
alphabetically within groups. Ruff's `I` rules enforce the order (`uv run ruff check --fix .`).

```python
# 1. Standard library
import time
from typing import Dict, Optional

# 2. Third-party
from fastapi import APIRouter

# 3. Local application
from models.aggregation_models import AggregationResult
from services.llm_provider_service import LlmProviderService
```

- Use **absolute imports** from the `apps/api` root (`from services.llm_provider_service import ...`).
- **Never** use relative imports between packages (`from . import`, `from .. import`).
- Import directly from module files, never through `__init__.py` re-exports.

### `__init__.py` files

`__init__.py` files contain **only a docstring**, nothing else:

```python
"""Features module."""
```

### Formatting and linting

- **Ruff** only: `ruff format` (Black-compatible) and `ruff check` (rules `E`, `F`, `I`, `B`), configured
  in `pyproject.toml` with a **120-character** line length. Black is not used.
- 4-space indentation, double quotes, trailing commas in multi-line structures.

### Type hints (required on every function)

- Use `Optional[T]`, not `T | None`.
- Use `List`, `Dict`, `Tuple` from `typing`, not `list`, `dict`, `tuple`.
- Avoid `Any` unless necessary.

### Naming

| Kind | Convention | Example |
|---|---|---|
| Functions, methods, modules | `snake_case` | `health_check`, `gemini_service.py` |
| Classes | `PascalCase` | `GeminiService` |
| Constants | `UPPER_SNAKE_CASE` | `PROJECT_DETAILS` |
| Private members | `_` prefix | `_get_driver` |
| Feature files | `*_feature.py` | `health_feature.py` |
| Service files | `*_service.py` | `llm_provider_service.py` |
| Model files | `*_model.py` / `*_models.py` | `response_model.py`, `health_models.py` |
| Config files | `*_config.py` | `settings_config.py` |
| Constant files | `*_constants.py` in `constants/` | `rating_constants.py` |
| Util files | `*_utils.py` | `response_utils.py` |
| Error files | `*_errors.py` (`app_error.py` for the base) | `analysis_errors.py` |

### Docstrings (Google style, required for public APIs)

```python
def compute_entropy(self, result: AggregationResult) -> List[Dict]:
    """
    Compute the entropy of every policy.

    Args:
        result: Aggregation result

    Returns:
        List[Dict]: One row per policy
    """
```

### Error handling (`errors/`)

- Every expected failure is an `AppError` subclass from `errors/` (one `*_errors.py` file per area).
  An `AppError` carries a stable `code` (e.g. `incomplete_matrices`), its `status_code`, a
  `public_message` that is safe to show, optional `data` to return with the error (e.g. health
  details), and an internal `detail` that is logged and never returned.
- Services wrap HTTP and SDK errors in the matching `AppError`, so features never handle raw
  library exceptions. Features raise `AppError`s; routers never catch anything.
- `ErrorHandlers` (registered in `main.py`) packages every failure, including request validation
  (422) and unexpected exceptions (500), as an `ApiResponseModel` with `success: false` and
  `error.code`. `ErrorPresenter` logs the details server-side.
- **Never expose internal errors in API responses** (exception text, URIs, credentials, stack traces).

### Class-based code

- Every module except routers is class-based: features, services, utils, error handlers, and
  middleware are classes with methods. Dependencies are passed to `__init__`, defaulting to the
  module-level instances (`AnalysisFeature(flow=...)`).
- Each feature and service module ends with one module-level instance, like
  `gemini_service = GeminiService()`. Import that instance; tests pass mocks to the constructor
  instead of patching import paths.
- Utils get real classes where they hold settings or state (`ExcelStyler`). A standalone
  `def` in `utils/` is allowed only when it is stateless, used in several places, and fits nowhere
  better; its docstring must say why it is not a method.
- Standalone `def`s allowed elsewhere: FastAPI route handlers, `lifespan` in `main.py`, and the cached
  `get_settings()`.

### File size

Every code file, tests included, stays at or below **300 lines**. Split by responsibility into a
second class or module (e.g. `insights_feature.py` + `insights_text_feature.py`), never
arbitrarily. See the [root `AGENTS.md`](../../AGENTS.md) → Development Workflow.

### Committing

Run `just format` and `just check-api`, fix every failure,
and re-run until they pass before committing (root `AGENTS.md` → Development Workflow).

---

## Numerical Parity

The API reproduces the legacy Tk app number for number ("keep maths, fix labels",
`docs/decisions/2026-11-18-keep-legacy-maths-fix-labels.md`). Each ported module names its legacy file and lines.

- **Never change a formula, rounding, ordering, threshold, the prompt text or a colour without regenerating the
  fixtures from `tk-app/`** and recording a decision. Fixtures are generated, never hand-written:

  ```bash
  # From the repository root, with the legacy environment (Tk must be importable; no window is opened)
  uv run --frozen --python 3.13 --project tk-app python scripts/generate_parity_fixtures.py
  ```

  It writes `tests/fixtures/parity/<case>__<variant>.json` and `errors__<name>.json`,
  `tests/fixtures/layouts/<case>__<layout>__<full|focus0>.json`, `tests/fixtures/imports/*.xlsx` + `.json`, and
  `tests/fixtures/xlsx/*.xlsx` + `.json`. `apps/api` never imports or reads `tk-app/`;
  `tests/repository_rules_integration_test.py` checks this, `matplotlib`, `sys.path` and the 300-line limit.
- Tolerance is `rtol=0, atol=1e-12`; zeros are compared by sign (`-0.0` is kept). Layout positions use
  `atol=1e-6` px. Texts are compared exactly after only the literal L11–L14 replacements; the prompt exactly.
- BLAS: fixtures are generated on macOS (Accelerate); the dev container is Linux (OpenBLAS). Pure-Python results
  are bit-exact. PCA is compared per component up to a sign flip.
  - **Degenerate PCA** (`(S0-S1)/S0 < 1e-9` or `(S1-S2)/S0 < 1e-9`): only `explained` is compared:
    `neutral3x3__average`, `neutral3x3__majority_first`, `neutral3x3__median`, `neutral3x3__weighted` (all
    singular values 0) and `onelink3x1__average` (S1 = S2 = 0).
  - **Rounding boundary** (`docs/decisions/2026-11-18-pca-explained-rounding-boundary.md`): when the fixture's
    unrounded percentage (`pca.explained_unrounded`) is within 1e-9 of an `x.x5` boundary, the unrounded values
    are compared at 1e-12 and either rounded neighbour is accepted. Known case: `r5x3__majority_last` (PC1 is
    exactly 56.25%: 56.2 on macOS, 56.3 on Linux).
  - **Degenerate spectral layout** (two chosen eigenvalues within 1e-9): position comparison skipped:
    `example__spectral__focus0` (eigenvalues 2.0, 2.0).
- **Known Tkinter behaviour kept** (plan list 1–21): PCA rows drop their own diagonal and have no sign convention;
  Strongest Link uses positive edges only; Most Contested always names a pair; Hmax is 1.0 for 2 policies and the
  category divides rounded H by unrounded Hmax; the top driver/dependent can be negative; betweenness uses a 1e-9
  equal-path tolerance and `(n-1)(n-2)`; closeness uses outgoing distances and can exceed 1; ties go to the first
  index; agreement is 1.0 at zero variance; unresolved ties read as 0 (unreachable: rejected first); `-0.0` kept;
  half-to-even `round`; weights not renormalised (±0.01 after `round(sum, 10)`); median never averages; tie
  options by score descending; story tone by sign only; display bands as legacy; import edge cases; any line
  starting with `##` or `1.`–`7.` is a PDF header (`10.` is not: it does not start with `1.`); the centrality
  table is sorted by betweenness, descending (stable).
- **Label fixes** (L1–L16, each tested): one method label source (`Median (Lower)`, `Majority Rule`, ...); weight
  texts say `1.0 (±0.01)`; XLSX sheet titles (`utils/sheet_title_utils.py`); import warning groups; `.xls`
  rejected; PDF headers escaped; two-way edges flagged; ego empty message returned; L9 missing-key text; safe
  download names; one arrow `→` (Most Contested keeps `↔`); `Rating agreement`; `positive/negative link`; DM-count
  wording; text cells never formulas; spectral eigenvector sign rule.
- **AI request deviation:** OpenAI-compatible and Azure bodies send no `max_tokens` (legacy `llm_tab.py:248` sent
  4096; newer OpenAI models reject it). Anthropic sends `max_tokens` 4096.

---

## Architecture

```
apps/api/
├── main.py              # FastAPI app, CORS, error handlers, cache-control middleware
├── constants/           # rating, aggregation, band, entropy, insights, chart, import, export, llm, app
├── api/v1/api.py        # Router aggregation; every route is public (no accounts)
├── routers/             # One-statement handlers: health, scales, setup, matrices, weights, aggregation,
│                        # analysis, analysis_export, analysis_charts, imports, explanations
├── features/            # All logic: setup rules, checks, aggregation and its flow, analyses, insights texts,
│                        # chart data, import, XLSX export, prompt, interpretation and its PDF
├── services/            # I/O only: llm_provider_service (httpx), gemini_service (google-genai)
├── models/              # Pydantic request/response models; aggregation_models.py holds internal dataclasses
├── utils/               # No I/O: responses, file names, matrices, labels, graph, layouts, Excel read/style
├── errors/              # AppError hierarchy, ErrorPresenter, ErrorHandlers
├── config/  middleware/
└── tests/               # Parity, text, prompt, layout, import, XLSX and repository-rule tests; fixtures/
```

### Analysis flow

```
AnalysisRequest (validated in legacy order: names → limits → policies → control characters → shape → labels)
  → AggregationFlowFeature: completeness → effective method (< 3 DMs: Average) → weights / median choice
    → aggregate → tie choices (atomic) → every tie resolved
  → AnalysisFeature.compute: graph, scores, entropy, centrality (shared by analysis, XLSX, prompt, charts)
  → AnalysisData (scores, range of influence, PCA, network, insights)
```

Request validation errors are `AppError`s raised in the Pydantic validator (422 `invalid_setup` /
`invalid_ratings` with the legacy message and `data.title`), not `validation_error`.

### Layers

| Layer | Holds | May call | Called by |
|---|---|---|---|
| `routers/` | One-statement handlers returning through `ResponseBuilder` | features, `ResponseBuilder`, models | FastAPI |
| `features/` | All business logic | other features (no cycles), services, utils, models, errors | routers, features |
| `services/` | External I/O only | utils, models, errors, config | **features only** |
| `utils/` | Helpers without I/O | utils, models, errors | features, services, routers (`ResponseBuilder`) |
| `errors/` | Error types and their packaging | models, utils | anywhere |
| `models/` | Pydantic schemas and internal dataclasses | models, the setup feature (validators) | everything |

### API versioning and responses

- Routes under `/api/v1`; JSON uses `ApiResponseModel`; downloads use `download_bytes` with an ASCII
  `filename` plus RFC 5987 `filename*` (L10).
- Uploads stream in 64 KB chunks and stop at 5 MB + 1 byte (413); zip entries over 50 MB (200 MB total), more than
  50 sheets, or more than 102 rows/columns read are rejected before legacy parsing.
- CPU-bound work runs in `asyncio.to_thread`.

### AI interpretation

- Keys come per request (`SecretStr`, `repr=False`), are used once, never stored, logged or returned.
- Providers: Anthropic, Azure OpenAI (https + host allow-list), Gemini, Groq, OpenAI, OpenRouter;
  `constants/llm_constants.py` is the single catalogue (`GET /explanations/providers`).
- The interpretation recomputes the analysis (ties must be resolved) and sends the legacy prompt.
- `POST /explanations/export/pdf` writes the legacy PDF layout (`policy_interpretation.pdf`).

### Health checks

| Route | Checks | Status codes |
|---|---|---|
| `GET /api/v1/health` | API only (no dependencies) | 200 |
| `GET /api/v1/is-alive` | Liveness (Docker healthcheck) | 200 |

---

## Environment

`apps/api/.env` (template `.env.example`). Compose loads it and overrides only `APP_ENV`.

```bash
APP_ENV=development                  # development | production
CORS_ORIGINS=http://localhost:3001   # Comma-separated; the public origin on the VPS
WEB_CONCURRENCY=2                    # Gunicorn workers (production image only)
```

No AI keys or other secrets belong here.

---

## Adding an Endpoint

1. Define Pydantic models in `models/<area>_models.py`.
2. Put logic in a feature class (I/O in a service), with constructor injection and a module-level instance.
3. Add failures as `AppError` subclasses in `errors/<area>_errors.py`; keep user data out of the log `detail`.
4. Create `routers/<area>.py`; one statement per handler. Register it in `api/v1/api.py`.
5. Add co-located tests, and parity fixtures if legacy behaviour is involved. Document it in `README.md`.

---

## Testing

- Co-located unit tests (`features/x_feature.py` → `features/x_feature_test.py`) for every feature, util,
  service and router; integration tests in `tests/*_integration_test.py`.
- Classes `Test[ClassName]` on `unittest.TestCase` / `IsolatedAsyncioTestCase`; markers `unit`, `integration`,
  `slow` (`--strict-markers`). Mock providers with `httpx.MockTransport` and a fake Gemini client factory.

---

## Pitfalls

❌ Relative imports between packages → ✅ Absolute imports from the `apps/api` root  
❌ Re-exports in `__init__.py` → ✅ Docstring only; import from source files  
❌ Changing a formula or label "to fix it" → ✅ Regenerate fixtures from `tk-app/` and record a decision  
❌ Loosening a parity tolerance → ✅ A decision record first (see the rounding-boundary decision)  
❌ User names or ratings in an error `detail` → ✅ A fixed detail; the user text goes in `public_message`  
❌ Maths in the browser → ✅ Return values and texts from the API  
❌ `HTTPException` → ✅ An `AppError` subclass
