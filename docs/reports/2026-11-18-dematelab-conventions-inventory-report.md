# What To Copy, Adapt And Strip From DEMATELab To Rebuild Policy Coherence Kit As FastAPI + TanStack Start

**Date:** 18 November, 2026
**Author:** Claude Code (research agent) for Youpele Michael
**Scope:** Read-only inventory of `dematelab` at commit `6a76ae2` ("Added: FastAPI API
and TanStack Start web app replacing the Qt GUI", branch `restructure/apps-api-web`), compared with
`policycoherencekit` on branch `restructure/apps-api-web` (uncommitted restructure:
legacy app moved to `tk-app/`, sample data to `data/examples/`). Nothing was run except file reads, `wc`, `md5`,
`grep`, and `tomllib` parsing of the lockfiles.

## Summary

DEMATELab's rebuild can be copied almost file for file. About 80% of the infrastructure and skeleton is generic
and needs only **name and port substitutions**; the DEMATEL maths, Qt-specific parity rules and the DEMATEL flow
steps must be stripped. The values that must change for Policy Coherence Kit (PCK) are:

- **Ports:** web `3000 → 3001`, API `50001 → 50002`, used the same inside and outside the containers (Nginx
  upstreams, healthchecks, Dockerfile `CMD`/`EXPOSE`/`ENV PORT`, `package.json` scripts, `CORS_ORIGINS`,
  `VITE_API_BASE_URL`, tests). 26 hard-coded occurrences are listed in Finding 9.
- **Names:** Compose projects `policycoherencekit-dev` / `policycoherencekit`; containers
  `policycoherencekit-{api,web,nginx}`; packages `policycoherencekit-api` / `policycoherencekit-web`. None clash with
  DEMATELab, ice2kg, or the legacy `policycoherencekit-tk-{dev,prod}` stack.
- **One real clash remains:** the production Nginx host port defaults to `${HTTP_PORT:-80}` in DEMATELab (and
  ice2kg). If both production stacks share one host, PCK needs another default (proposed `8081`, an owner
  decision).
- **A new trap DEMATELab did not have:** the legacy Tk modules are flat top-level modules named `models` and
  `constants`, which are also package names in `apps/api`. The "no legacy imports" repository test cannot be
  copied as-is (it matches a package name, `DEMATELab`); it must check for the `tk-app` path and a list of
  legacy-only module names (Finding 7).

The stack versions to pin are listed in Finding 5 (Python 3.13, uv 0.12.10, FastAPI 0.163.1, numpy 2.5.4, Node
24, pnpm 12.9.1, TanStack Start 1.169.4, React 19.3.1, Biome 2.4.5, Vitest 5.0.5). The theme is copied verbatim
from `apps/web/src/styles.css` (Finding 6), with DEMATELab's cause/effect domain tokens replaced by PCK's
rating colours.

## Questions

1. For each generic DEMATELab file: what to copy verbatim, what to adapt, and what to strip?
2. Which exact dependency versions do `apps/api` and `apps/web` pin and lock?
3. What are the full theme tokens, fonts, and how is the logo handled?
4. Which code-structure rules exist, and which are enforced by tests rather than only documented?
5. Which make targets exist, and how do `make check`, `make dev`, `make prod` work?
6. Which values clash when DEMATELab and PCK run on one host, and what replaces them?
7. Which lessons from the DEMATELab playbook's "Problems hit" table apply up front?

## Method

- Read in DEMATELab: `docs/reports/2026-11-16-qt-to-fastapi-and-tanstack-migration-playbook-report.md`, root
  `AGENTS.md`, `apps/api/AGENTS.md`, `apps/web/AGENTS.md`, all seven `docs/decisions/2026-11-16-*.md`, the phase
  sections of both `docs/plans/2026-11-16-*.md`, `Makefile`, `docker-compose-dev.yml`, `docker-compose-prod.yml`,
  `nginx/Dockerfile.prod`, `nginx/nginx.prod.conf`, `.gitignore`, `.gitattributes`, `scripts/generate_parity_fixtures.py`
  (header, function list, `__main__`), `qt-app/docker-compose-*.yml` (names/ports only).
- `apps/api`: `pyproject.toml`, `uv.lock` (parsed), `.python-version`, `.dockerignore`, `Dockerfile.dev/.prod`,
  `.env.example`, `main.py`, `api/v1/api.py`, `config/settings_config.py`, `errors/{app_error,error_handlers,error_presenter,health_errors,llm_errors}.py`,
  `middleware/cache_control_middleware.py`, `models/{response_model,error_models,health_models}.py`,
  `utils/{response_utils,font_utils}.py`, `routers/health.py`, `features/health_feature.py`,
  `constants/{app_constants,llm_constants}.py`, `services/llm_provider_service.py` (first 80 lines),
  `tests/repository_rules_integration_test.py`, `tests/parity_fixtures.py` (head).
- `apps/web`: `package.json`, `pnpm-lock.yaml` (importer section), `pnpm-workspace.yaml`, `biome.json`,
  `components.json`, `tsconfig.json`, `tsr.config.json`, `vite.config.ts`, `vitest.config.ts`, `Dockerfile.dev/.prod`,
  `.env.example`, `.dockerignore`, `.gitignore`, `.vscode/settings.json`, `src/styles.css`, `src/env.ts`, `src/router.tsx`,
  `src/routes/*`, `src/lib/*`, `src/components/general/{AppLayout,AppHeader,AppFooter,PageHeader,SectionCard,NotFound,InlineError}.tsx`,
  `src/components/ui/sonner.tsx`, `src/components/page-specific/analysis/{FlowShell,StepFrame,StepNavigation,StepProgress}.tsx`,
  `src/constants/{layout,api,query,health}.constants.ts`, `src/utils/{api,api-error,flow,download}.utils.ts`,
  `src/interfaces/{api,health}.interface.ts`, `src/services/health.service(.test).ts`, `src/hooks/{health,flow,object-url}.hook.ts`,
  `src/store/analysis.store.ts` (first 80 of 225 lines), `src/test/render.tsx`.
- In PCK: `tk-app/{Makefile,docker-compose-dev.yml,docker-compose-prod.yml,.env.example,pyproject.toml,uv.lock,Dockerfile.dev,docker/start.sh,constants.py,theme.py,llm_tab.py}`
  (relevant parts), import lines of every `tk-app/*_tab.py`, `aggregator.py`, `importer.py`, `models.py`,
  root `.gitignore`, `.gitattributes`, `AGENTS.md`, `README.md`, and `git diff` of the restructure.
- ice2kg: only its compose names and ports (`docker-compose-dev.yml`, `docker-compose-prod.yml`, `Makefile:23-26`)
  to check three-way port clashes.

## Findings

### 1. What the DEMATELab commit contains (shape to reproduce)

```text
apps/api/   main.py · api/v1/api.py · routers/ · features/ · services/ · utils/ · constants/ · models/ · errors/
            config/ · middleware/ · assets/fonts/ (9 Inter TTFs) · tests/{fixtures/{parity,imports,xlsx},*_integration_test.py}
            pyproject.toml · uv.lock · .python-version · .env.example · .dockerignore · Dockerfile.dev/.prod
            AGENTS.md · CLAUDE.md ("@AGENTS.md") · README.md
apps/web/   src/{routes,components/{ui,general,page-specific/<page>},hooks,services,store,utils,interfaces,constants,
            test,lib}, router.tsx, routeTree.gen.ts, styles.css, env.ts, vite-env.d.ts · public/{logo.png,favicon.ico,
            apple-touch-icon.png} · scripts/.gitkeep · .vscode/settings.json · package.json · pnpm-lock.yaml ·
            pnpm-workspace.yaml · biome.json · components.json · tsconfig.json · tsr.config.json · vite.config.ts ·
            vitest.config.ts · .env.example · .dockerignore · .gitignore · Dockerfile.dev/.prod · AGENTS.md · CLAUDE.md · README.md
nginx/      Dockerfile.prod · nginx.prod.conf
scripts/    generate_parity_fixtures.py
docs/       decisions/ (7 + guide) · plans/ (2 + guide) · reports/ (playbook + guide) · research/ (guide)
root        Makefile · docker-compose-dev.yml · docker-compose-prod.yml · AGENTS.md · README.md · .gitignore · .gitattributes
```

PCK already has: `data/examples/`, `docs/{decisions,plans,reports,research}/` with the four authoring guides,
`tk-app/` with its own Makefile/compose, and an identical `.gitattributes` (LF for `*.sh`, `Makefile`, `.env.example`).

### 2. Root infrastructure: copy, adapt, strip

| DEMATELab file | Copy verbatim | Adapt for PCK | Strip |
| --- | --- | --- | --- |
| `Makefile` (205 lines) | Whole structure: `ENV_FILES`, `DOCKER` docker/podman detection, `WEB_READY`, `DEV`/`PROD`, `TTY`, `API_EXEC`/`WEB_EXEC`, `require_dev`, `require_web`, `require_port` macros, all targets (Finding 8) | Header comment ("DEMATELab" → "Policy Coherence Kit", `make -C qt-app dev` → `make -C tk-app dev`); `override WEB_PORT := 3001`, `override API_PORT := 50002`; `DEV_PROJECT := policycoherencekit-dev`; `API_CONTAINER := policycoherencekit-api`; `WEB_CONTAINER := policycoherencekit-web`; port-clash message "(DEMATELab uses fixed ports …)" → "(Policy Coherence Kit uses fixed ports …)" and comment "3000/50001" → "3001/50002"; `help` footer "Legacy Qt app: make -C qt-app help" → "Legacy Tk app: make -C tk-app help"; `test-api` example `T="tests/parity_integration_test.py -v"` keeps working if the parity test keeps that name | `WEB_READY` / `require_web` "comes with the frontend plan" scaffolding is only needed if the API lands before the web app; keep it (harmless) or drop once both exist |
| `docker-compose-dev.yml` | Service layout, `env_file`, `environment: APP_ENV=development`, bind mounts `./apps/api:/app:z`, `./apps/web:/app:z` + anonymous `/app/node_modules`, `depends_on: api`, `networks: app-network` (bridge), `restart: unless-stopped`, healthcheck timing `10s/5s/5/10s` | `name: policycoherencekit-dev`; `container_name: policycoherencekit-web` / `policycoherencekit-api`; ports `"3001:3001"`, `"50002:50002"`; healthcheck URL `http://localhost:50002/api/v1/is-alive` | – |
| `docker-compose-prod.yml` | Same three services; api healthcheck `30s/5s/3/10s`; Nginx `depends_on: {api: service_healthy, web: service_started}`; comment "Stateless: no volume" | `name: policycoherencekit`; containers `policycoherencekit-{web,api,nginx}`; healthcheck URL port 50002; Nginx host port default (see Finding 9: `${HTTP_PORT:-80}` clashes if both prods share a host) | Do **not** add the temporary Compose `profiles: [web]` + `required: false` dance unless the web app really lands after the API (playbook problem 2) |
| `nginx/Dockerfile.prod` | Verbatim (`nginx:stable-alpine`, `NGINX_ENTRYPOINT_LOCAL_RESOLVERS=1`, template at `/etc/nginx/templates/default.conf.template`, `EXPOSE 80 443`) | – | – |
| `nginx/nginx.prod.conf` | Runtime resolver `resolver ${NGINX_LOCAL_RESOLVERS} valid=10s ipv6=off;`, `set $web_upstream` / `set $api_upstream`, proxy headers, `/api/` block with `proxy_http_version 1.1; proxy_buffering off; proxy_read_timeout 300s;`, commented HTTPS block | Upstreams `http://web:3001` and `http://api:50002` (both in the HTTP and the commented HTTPS server); `client_max_body_size` comment ("100-factor x 50-expert" is DEMATEL-specific): size it from PCK's real request (policies × decision-makers of rating labels) or keep `20m` with a PCK comment; the `proxy_read_timeout` comment ("AI explanations … 120 s") still holds (PCK `llm_tab.py:220` uses `timeout=120`) | – |
| `.gitignore` (root) | `!apps/api/.python-version` (needed because global ignores may drop it), `.env`, Python caches | Keep PCK's existing `tk-app/exports/*` + `!tk-app/exports/.gitkeep` | Note PCK's root `.gitignore` ignores `.vscode/`; DEMATELab tracks `apps/web/.vscode/settings.json`. Add `!apps/web/.vscode/` + `!apps/web/.vscode/settings.json` if that file is wanted |
| `.gitattributes` | Already identical in PCK | – | – |
| `AGENTS.md` (root) | Structure: app overview, "How the App Fits Together" diagram, repo layout, "`<legacy>/` is read-only", "Running the App" (make commands), Docker services table, env files table, Development Workflow (plan first, ≤300 lines, `make format` + `make check-api` before commit), Pre-Commit Checklist | Names, ports, `qt-app/` → `tk-app/`, "Numerical parity" wording for PCK (aggregation, scores, entropy, PCA, centrality, insights), env table (`tk-app/.env` holds `VNC_PASSWORD`, `SCREEN_GEOMETRY`, `NOVNC_PORT`); keep the whole current PCK AGENTS.md (Tk run/verify, data contracts) as the "Legacy Tk App (`tk-app/`)" section with paths updated (`tk-app/main.py`, `data/examples/WEF Nexus Example.xlsx`, `make -C tk-app dev`) | DEMATELab "Legacy Qt App" section; "Its dev Compose project is also called `dematelab-dev`; run one at a time" (PCK already renamed the legacy project) |
| `CLAUDE.md` (each app) | Single line `@AGENTS.md` | – | – |
| `docs/decisions/*` | Format (Status, Date, Deciders, Decision, Context, Alternatives, Consequences, Related Work) and all seven topics: rebuild in `apps/`; Compose + Nginx as only public entry; own env file per service; Make entrypoint with container-first checks; stateless API (with server-rendered charts only if PCK keeps server charts); AI keys per request; warm-white theme | Ports, names, legacy folder, PCK's providers (Groq, OpenAI) and charts decision | DEMATEL-specific consequences (10 MB requests, matplotlib dpi, cause/effect hues) |
| `scripts/generate_parity_fixtures.py` | Structure: module docstring with the exact run command; env defaults before imports; `REPO_ROOT = Path(__file__).resolve().parents[1]`; output dirs under `apps/api/tests/fixtures/{parity,imports,…}`; `build_cases()` incl. `example_case(path)` from `data/examples`; `to_jsonable`; `run_case` writing request + every result field; `write_json`; import fixtures that record either `expected` or `error_message`; `__main__` printing counts | Command: `uv run --frozen --python 3.13 --project tk-app python scripts/generate_parity_fixtures.py`; `sys.path.insert(0, str(REPO_ROOT / "tk-app"))` before importing `aggregator`, `importer`, `models`, and the `compute_*` functions from `coherence_scores_tab`, `range_of_influence_tab`, `pca_tab`, `network_tab`, `results_insights_tab` (all import `tkinter` and `theme` at module level, so the interpreter needs Tk but no display); cases = methods × decision-maker counts (≥3 for method choice, 4 for even-count Median lower/upper, ties for Majority) | `QT_QPA_PLATFORM`, `QApplication`, PySide6 widget drivers, DEMATEL solver/threshold grid, XLSX-export fixtures unless PCK's `_export_to_excel` is ported (then add them) |

### 3. `apps/api`: copy, adapt, strip

| File | Copy verbatim | Adapt | Strip |
| --- | --- | --- | --- |
| `pyproject.toml` | `[tool.uv] package = false`; `[tool.ruff] line-length = 120`, `target-version = "py313"`; `[tool.ruff.lint] select = ["E","F","I","B"]`; whole `[tool.pytest.ini_options]` (`testpaths = [".", "tests"]`, `python_files = ["*_test.py","test_*.py"]`, `python_classes = ["Test*"]`, `python_functions = ["test_*"]`, `addopts = ["-v","--strict-markers","--tb=short"]`, markers `unit`/`integration`/`slow`); `[tool.coverage.*]`; dev group `ruff>=0.8.0`, `pytest>=8.0.0`, `pytest-cov>=4.1.0`, `pytest-asyncio>=0.23.0` | `name = "policycoherencekit-api"`, `description = "Policy Coherence Kit API"`; runtime deps: keep `fastapi[standard]>=0.115.12`, `pydantic>=2.11.5`, `pydantic-settings>=2.6.0`, `python-dotenv>=1.1.0`, `gunicorn>=22.0.0`, `uvicorn-worker>=0.3.0`, `httpx==0.28.1`; pin the numeric libs to **tk-app's lock for Python ≥3.12**: `numpy==2.5.4`, `openpyxl==3.1.5`; add `reportlab==5.1.0` only if the PDF export of the AI text moves server-side | `pandas`, `matplotlib`, `scikit-learn`, `google-genai` (PCK's legacy uses none of them; add back only by decision, e.g. matplotlib for server charts or google-genai if Gemini is added) |
| `.python-version` | `3.13` | – | – |
| `.dockerignore` | Verbatim (venv, caches, `.env`, `.env.*`, `Dockerfile.*`, `.dockerignore`, `.DS_Store`, `*.log`) | – | – |
| `Dockerfile.dev` | `python:3.13-slim`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`, `pip install --no-cache-dir uv==0.12.10`, `UV_PROJECT_ENVIRONMENT=/opt/venv`, `UV_LINK_MODE=copy`, `PATH="/opt/venv/bin:$PATH"`, `COPY pyproject.toml uv.lock` → `uv sync --frozen`, `COPY . /app/` | `EXPOSE 50002`; `CMD ["uvicorn","main:app","--host","0.0.0.0","--port","50002","--reload"]` | `MPLCONFIGDIR=/tmp/matplotlib` and the `fonts-dejavu-core` apt layer unless matplotlib is kept |
| `Dockerfile.prod` | Same base + `UV_COMPILE_BYTECODE=1`, `uv sync --frozen --no-dev`, `useradd --system --no-create-home --uid 1001 app`, `USER app`, `ENV WEB_CONCURRENCY=2` | `EXPOSE 50002`; `CMD ["gunicorn","-k","uvicorn_worker.UvicornWorker","main:app","--bind","0.0.0.0:50002"]` | Same matplotlib/font lines |
| `.env.example` | Comments and three keys: `APP_ENV=development`, `CORS_ORIGINS=…`, `WEB_CONCURRENCY=2` | `CORS_ORIGINS=http://localhost:3001` | – |
| `main.py` | `logging.basicConfig(level=INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")`; `lifespan` logging name/version/env and docs URL; `FastAPI(title, version, description, docs_url, redoc_url, openapi_url, lifespan)`; `error_handlers.register(app)`; `CacheControlMiddleware`; `CORSMiddleware(allow_origins=get_settings().cors_origins_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"], expose_headers=["Content-Disposition"])`; `include_router(api_router, prefix="/api/v1")`; `uvicorn.run("main:app", host="127.0.0.1", port=PORT, …, reload=True, reload_dirs=["."])` | Docstring "Policy Coherence Kit API" | `matplotlib.use("Agg")` and `font_registrar.register_inter_fonts()` (and `utils/font_utils.py`, `assets/fonts/`) unless server charts are kept |
| `api/v1/api.py` | Pattern: one `include_router` per router | Router list for PCK | DEMATEL routers |
| `config/settings_config.py` (+ test) | Verbatim (`Settings(BaseSettings)` with `env_file=".env"`, `extra="ignore"`, `app_env: Literal["development","production"]`, `cors_origins_list`, `@lru_cache get_settings()`) | Default `cors_origins = "http://localhost:3001"`; test line 45 expects `["http://localhost:3001"]` | – |
| `constants/app_constants.py` | `PROJECT_SETTINGS` (`/api/docs`, `/api/redoc`, `/api/openapi.json`), `API_ROOT`, `CACHE_CONTROL_SETTINGS` (`/api/`, `no-store`) | `PORT = 50002`; `PROJECT_DETAILS` name "Policy Coherence Kit API", description, version `0.1.0` | `PROJECT_PATHS["FONTS_DIR"]` unless fonts are kept |
| `errors/app_error.py`, `error_handlers.py` (+ test), `error_presenter.py`, `health_errors.py` | Verbatim | – | – |
| `errors/llm_errors.py` | `MissingApiKeyError` (422 `missing_api_key`), `LlmAuthError` (502 `llm_auth_failed`), `LlmRateLimitError` (502 `llm_rate_limited`), `LlmTimeoutError` (504 `llm_timeout`), `LlmProviderError` (502 `llm_provider_error`), `UnsupportedModelError` (422 `unsupported_model`) | – | Azure errors (`missing_azure_endpoint`, `missing_azure_deployment`, `invalid_azure_endpoint`, `azure_deployment_not_found`) unless Azure is added |
| `middleware/cache_control_middleware.py` (+ test) | Verbatim | – | – |
| `models/response_model.py`, `error_models.py`, `health_models.py` | Verbatim (docstring "for the DEMATELab API" → PCK) | – | – |
| `utils/response_utils.py` (+ test) | Verbatim: `ok`, `error`, `stream` (SSE), `download` (text), `download_bytes`, `image`, `_metadata` (`timestamp` UTC with `Z`) | – | `image` only if no charts are served (harmless to keep) |
| `routers/health.py` (+ test), `features/health_feature.py` (+ test) | Verbatim: `GET /health` → `HealthCheckData(status="healthy", services={"api": up})`, `GET /is-alive` → `AliveData(status="alive")` | Docstrings | – |
| `services/llm_provider_service.py` (+ test) | Class with injectable `httpx.AsyncBaseTransport`, one `AsyncClient` per call, `openai_compatible(url, api_key, model, prompt, extra_headers)`, `_post` mapping 401/403/429/timeout/other into `AppError`s, key stripped from logged bodies | System message and temperature from PCK (`llm_tab.py:79` `SYSTEM_PROMPT`, `llm_tab.py:249` `temperature 0.3`) | `azure()`, Anthropic method, unless those providers are added by decision |
| `services/gemini_service.py` (+ test) | – | – | Strip (PCK has no Gemini); if added later, copy it with the already-fixed client lifetime and `HttpOptions(timeout=120000)` |
| `constants/llm_constants.py` | Pattern: `LlmProvider(str, Enum)`, `PROVIDER_MODELS` with source URLs, `DEFAULT_MODELS`, `OPENAI_COMPATIBLE_URLS`, `LLM_SETTINGS` | Providers from `tk-app/llm_tab.py:61-77`: Groq (`https://api.groq.com/openai/v1`, model `llama-3.3-70b-versatile`) and OpenAI (`https://api.openai.com/v1`, `gpt-4o-mini`, `gpt-4o`); `TIMEOUT_SECONDS: 120.0`; `OPENROUTER_HEADERS["X-Title"]` → "Policy Coherence Kit" if OpenRouter is added. Whether to refresh the legacy model lists (DEMATELab did, 2026-11-16) is an owner decision | DEMATELab model catalogue, Azure host allow-list (unless Azure added) |
| `tests/repository_rules_integration_test.py` | 300-line test, `__init__.py`-docstring-only test, `SKIP_PARTS = {".venv","__pycache__",".pytest_cache",".ruff_cache","fixtures"}` | **Legacy-import check must be rewritten** (Finding 7): keep the string-literal check with `"tk-app"`; replace `name.split(".")[0] == "DEMATELab"` by a set of legacy-only module names | `DEMATELab` package check |
| `tests/parity_fixtures.py`, `tests/parity_integration_test.py` | Loader class pattern (`FIXTURES_DIR`, sorted glob, `parity_case(name)`), tolerance `rtol=0, atol=1e-12` | PCK fixture names (e.g. `<case>__<method>.json`) | DEMATEL solver conversion |
| `AGENTS.md` (api) | Commands, Code Style (imports, `__init__.py`, Ruff, typing `Optional`/`List`/`Dict`, naming table, Google docstrings), Error handling, Class-based code, File size, Layers table, API versioning and responses, Health checks, Environment, Adding an Endpoint, Testing, Pitfalls | Stack line, ports, "Numerical Parity" rewritten for PCK aggregation/analysis, layout block | DEMATEL parity specifics, analysis flow, AI-provider list beyond PCK's |

### 4. `apps/web`: copy, adapt, strip

| File | Copy verbatim | Adapt | Strip |
| --- | --- | --- | --- |
| `package.json` | `private`, `type: module`, every script except the ports, all versions (Finding 5), `engines` (`node >=24.0.0`, `pnpm >=12.0.0`), `packageManager: "pnpm@12.9.1"` | `name: "policycoherencekit-web"`; `"dev": "vite dev --port 3001 --strictPort"`; `"preview": "vite preview --port 3001 --strictPort"` | `@tanstack/react-virtual` and `html-to-image` only if PCK has no large virtualised matrix / browser PNG capture (PCK matrices are policies × policies, likely needs virtualisation; decide in the plan) |
| `pnpm-workspace.yaml` | `allowBuilds: {esbuild: true, lightningcss: true}`, `minimumReleaseAgeExclude` for the four `@tanstack/*query*@5.105.0` packages | – | – |
| `biome.json`, `components.json` (`style: base-nova`, `baseColor: neutral`, `iconLibrary: lucide`, aliases `@/…`), `tsconfig.json` (strict, `@/*`→`./src/*`, bundler resolution, `types: ["vite/client","vitest/globals"]`), `tsr.config.json` (`{"target":"react"}`), `vite.config.ts` (`devtools(), nitro(), tailwindcss(), tanstackStart(), viteReact()`, `resolve.tsconfigPaths`) | Verbatim | – | – |
| `vitest.config.ts` | jsdom, globals, `src/**/*.test.{ts,tsx}`, coverage v8 excluding tests, `routeTree.gen.ts`, `components/ui/**` | `VITE_API_BASE_URL: "http://localhost:50002"` | – |
| `Dockerfile.dev` | `node:24-slim`, `ARG PNPM_VERSION=12.9.1`, `pnpm install --frozen-lockfile`, `CMD ["pnpm","dev","--host","0.0.0.0"]` | `EXPOSE 3001` (the port itself comes from the `dev` script) | – |
| `Dockerfile.prod` | Builder/runner stages, `.env` presence check before `pnpm build`, `.output` copied `--chown=node:node`, `USER node`, `CMD ["node",".output/server/index.mjs"]` | `ENV PORT=3001`, `EXPOSE 3001` | – |
| `.env.example` | Comments, `VITE_APP_ENV=development` | `VITE_API_BASE_URL=http://localhost:50002` and its comment | – |
| `.dockerignore`, `.gitignore`, `.vscode/settings.json` | Verbatim (note `.dockerignore` keeps `.env` because the prod build reads `VITE_*`) | – | – |
| `src/env.ts` (+ test) | Verbatim (`VITE_APP_ENV` enum, `VITE_API_BASE_URL` `""` or URL, trailing slashes removed, error lists keys only) | Comment and test URLs to 50002 | – |
| `src/router.tsx`, `src/lib/{query-client,query-devtools,utils}.ts(x)` (+ test) | Verbatim (`staleTime` 5 min, `gcTime` 30 min, mutations `retry: false`; `cn` from package `cn`) | – | – |
| `src/routes/__root.tsx` | Verbatim (head meta/links, `AppLayout`, one `<Toaster />`, devtools in DEV) | – | – |
| `src/routes/index.tsx`, `status.tsx` | Pattern: `validateSearch: flowSearchSchema`, `component: FlowShell`; status page with `PageHeader` + `ApiHealthCard` | Flow schema for PCK steps | – |
| `src/styles.css` | Verbatim (Finding 6) | Replace domain tokens `--cause*`, `--effect*`, `--cell-edited` by PCK rating tokens | DEMATEL domain tokens |
| `components/general/AppLayout`, `AppHeader`, `AppFooter`, `PageHeader`, `SectionCard`, `NotFound`, `InlineError`, `DownloadButton`, `ZoomableImage`, `NumberStepper` (+ tests) | Verbatim | Header/footer tests assert app name | `ZoomableImage` if no PNG charts |
| `components/ui/*` (shadcn base-nova: alert-dialog, badge, button, card, checkbox, dialog, input, scroll-area, select, separator, sonner, tabs) | Verbatim; add new ones with `pnpm dlx shadcn@latest add <component>` and switch `from "cn"` imports to `@/lib/utils` | `sonner.tsx` docstring names DEMATELab | – |
| `constants/layout.constants.ts` | Shape | `APP_NAME = "Policy Coherence Kit"`, `APP_SUBTITLE` (owner text; legacy theme has a slogan colour, slogan text not inventoried here), `APP_FULL_NAME`, `FOOTER_LINKS` (Forschungszentrum Jülich link if applicable), `PAGE_TITLES`, `NOT_FOUND_TEXT.LINK` | – |
| `constants/api.constants.ts`, `query.constants.ts`, `health.constants.ts` | `API_V1_PREFIX = "/api/v1"`, health constants verbatim | PCK endpoints and keys; `HEALTH_API_ROW.description` | DEMATEL endpoints, `CHART_DPI` unless server charts |
| `utils/api.utils.ts`, `api-error.utils.ts`, `download.utils.ts`, `interfaces/api.interface.ts`, `health.interface.ts`, `services/health.service.ts`, `hooks/health.hook.ts`, `hooks/object-url.hook.ts`, `test/render.tsx` (+ tests) | Verbatim (`buildApiUrl`, `ApiError`, `apiFetch`, `jsonPost`, `ensureOk`, `apiData` with Zod, `apiBlob`, `errorMessage`; `readErrorMessage` strips Pydantic's `Value error, ` prefix; `saveBlob`; `renderWithQuery`, `stubLayout`) | Test URLs to `http://localhost:50002/api/v1/...`; comment in `api.utils.ts:6` | – |
| `page-specific/analysis/FlowShell.tsx`, `StepFrame.tsx`, `StepNavigation.tsx`, `StepProgress.tsx`, `StepList.tsx`, `StartOverButton.tsx`, `ResetConfirmDialog`, `OutdatedResultsBanner`, `utils/flow.utils.ts`, `hooks/flow.hook.ts`, `hooks/refresh-notice.hook.ts` | The flow mechanics: `?step=` search param, redirect to first unanswered step, `canOpenStep`/`nextStep`/`previousStep`, Enter/Shift+Enter, `initialFocus`, slide-in animation off under `prefers-reduced-motion`, progress bar, step list, Start over with confirm, results "out of date" banner | `SETUP_STEPS` and per-item steps for PCK (e.g. project → policies → decision-makers → one matrix per decision-maker → review → aggregation method → results); `FLOW_TEXT`, `STEP_TEXT` | DEMATEL steps (solver, threshold, expert weights, `SolverChangeDialog`) |
| `store/analysis.store.ts` | Pattern: Zustand `create`, `AnalysisState` + `AnalysisActions`, `initialAnalysisState`, `answered: StepId[]`, request **snapshot** + `snapshotHash` + `results`, `setCell` copying only the changed row, nothing persisted | PCK state (policies, decision-makers, rating matrices, method, tie choices) | DEMATEL fields |

### 5. Exact dependency versions

API (`apps/api/pyproject.toml` specifier → `uv.lock` resolved; lock `version = 1`, `revision = 3`, `requires-python >=3.13`):

| Package | Specifier | Locked | PCK recommendation |
| --- | --- | --- | --- |
| fastapi[standard] | `>=0.115.12` | 0.163.1 (fastapi-cli 0.0.34, starlette 1.10.0, uvicorn 0.54.0) | Same |
| pydantic | `>=2.11.5` | 2.14.3 | Same |
| pydantic-settings | `>=2.6.0` | 2.16.3 | Same |
| python-dotenv | `>=1.1.0` | 1.2.4 | Same |
| gunicorn | `>=22.0.0` | 27.0.1 | Same |
| uvicorn-worker | `>=0.3.0` | 0.4.0 | Same |
| httpx | `==0.28.1` | 0.28.1 | Same |
| numpy | `==2.5.4` | 2.5.4 | Same: tk-app's `uv.lock` resolves numpy 2.5.4 for Python ≥3.12 |
| openpyxl | `==3.1.5` | 3.1.5 | Same: tk-app lock 3.1.5 |
| pandas / matplotlib / scikit-learn / google-genai | `==3.1.1` / `==3.11.2` / `==1.9.1` / `==3.0.0` | same | Not needed by PCK legacy; strip unless decided |
| reportlab | – | – | `==5.1.0` (tk-app lock) only if PDF export moves to the API |
| ruff (dev) | `>=0.8.0` | 0.17.5 | Same |
| pytest / pytest-cov / pytest-asyncio (dev) | `>=8.0.0` / `>=4.1.0` / `>=0.23.0` | 9.2.0 / 7.1.0 / 1.5.0 (coverage 7.17.3) | Same |

Toolchain: Python image `python:3.13-slim`; uv `0.12.10` (`pip install uv==0.12.10` in the API images; tk-app uses
`COPY --from=astral/uv:0.12.10`); Node image `node:24-slim`; pnpm `12.9.1` (`packageManager` + `ARG PNPM_VERSION`,
change together); Nginx `nginx:stable-alpine`.

Web (`apps/web/package.json` specifier → `pnpm-lock.yaml` resolved; lockfile v9.0, multi-document with the pnpm
`packageManagerDependencies` header):

| Package | Specifier | Locked |
| --- | --- | --- |
| @base-ui/react | ^1.9.0 | 1.9.0 |
| @fontsource-variable/manrope | ^5.3.0 | 5.3.0 |
| @tailwindcss/vite / tailwindcss | ^4.1.18 / ^4.1.18 | 4.3.3 / 4.3.3 |
| @tanstack/react-devtools | 0.10.13 | 0.10.13 |
| @tanstack/react-query / -devtools | 5.105.0 / 5.105.0 | 5.105.0 / 5.105.0 |
| @tanstack/react-router | 1.170.46 | 1.170.46 (router-core 1.171.39) |
| @tanstack/react-router-devtools | 1.167.2 | 1.167.2 |
| @tanstack/react-router-ssr-query | 1.167.3 | 1.167.3 |
| @tanstack/react-start | 1.169.4 | 1.169.4 |
| @tanstack/react-virtual | ^3.14.26 | 3.14.26 |
| class-variance-authority | ^0.7.1 | 0.7.1 |
| cn | ^0.5.0 | 0.5.0 |
| html-to-image | ^1.11.13 | 1.11.13 |
| lucide-react | ^0.577.0 | 0.577.0 |
| nitro | 3.0.260610-beta | 3.0.260610-beta |
| react / react-dom | ^19.2.0 | 19.3.1 |
| shadcn | ^4.22.1 | 4.22.1 |
| sonner | ^2.0.8 | 2.0.8 |
| tw-animate-css | ^1.3.6 | 1.4.0 |
| zod | ^4.6.7 | 4.6.7 |
| zustand | ^5.1.0 | 5.1.0 |
| @biomejs/biome (dev) | 2.4.5 | 2.4.5 |
| @tanstack/devtools-vite (dev) | 0.8.5 | 0.8.5 |
| @tanstack/router-cli (dev) | ^1.132.0 | 1.167.46 |
| @testing-library/dom / react (dev) | ^10.4.2 / ^16.3.3 | 10.4.2 / 16.3.3 |
| @types/node / react / react-dom (dev) | ^24.19.2 / ^19.2.0 / ^19.2.0 | 24.19.2 / 19.3.0 / 19.3.0 |
| @vitejs/plugin-react (dev) | ^6.0.1 | 6.1.2 |
| @vitest/coverage-v8 / vitest (dev) | ^5.0.5 | 5.0.5 |
| jsdom (dev) | ^30.1.3 | 30.1.3 |
| typescript (dev) | ^6.0.2 | 6.0.3 |
| vite (dev) | ^8.0.0 | 8.3.5 |

Simplest faithful route: copy `package.json`, `pnpm-workspace.yaml` and `pnpm-lock.yaml`, rename, drop unused
packages, then `pnpm install` to re-resolve the lock to the same versions.

### 6. Theme tokens, fonts, logo

`apps/web/src/styles.css` (180 lines) imports, in order: `tailwindcss`, `tw-animate-css`, `shadcn/tailwind.css`,
`@fontsource-variable/manrope`; `@custom-variant dark (&:is(.dark *));`.

`:root` (light; the app has no theme switch):

| Token | Value | Token | Value |
| --- | --- | --- | --- |
| `--background` | `#faf8f4` | `--foreground` | `#023d6b` |
| `--card` | `#fffdf9` | `--card-foreground` | `#023d6b` |
| `--popover` | `#fffdf9` | `--popover-foreground` | `#023d6b` |
| `--primary` | `#023d6b` | `--primary-foreground` | `#fffdf9` |
| `--secondary` | `#f4f1ea` | `--secondary-foreground` | `#023d6b` |
| `--muted` | `#f4f1ea` | `--muted-foreground` | `#6f6a60` |
| `--accent` | `#f4f1ea` | `--accent-foreground` | `#023d6b` |
| `--destructive` | `oklch(0.577 0.245 27.325)` | `--destructive-foreground` | `oklch(0.577 0.245 27.325)` |
| `--border` | `#e8e3d9` | `--input` | `#e8e3d9` |
| `--ring` | `#a39d91` | `--placeholder` | `#a39d91` |
| `--soft-2` | `#eeeae1` | `--line-strong` | `#d6cfc2` |
| `--chart-1…5` | `oklch(0.87 0 0)`, `oklch(0.556 0 0)`, `oklch(0.439 0 0)`, `oklch(0.371 0 0)`, `oklch(0.269 0 0)` | `--radius` | `0.625rem` |
| `--sidebar` | `oklch(0.985 0.006 85)` | `--sidebar-foreground` | `oklch(0.145 0 0)` |
| `--sidebar-primary` | `oklch(0.205 0 0)` | `--sidebar-primary-foreground` | `oklch(0.985 0 0)` |
| `--sidebar-accent` | `oklch(0.97 0 0)` | `--sidebar-accent-foreground` | `oklch(0.205 0 0)` |
| `--sidebar-border` | `oklch(0.922 0 0)` | `--sidebar-ring` | `oklch(0.708 0 0)` |
| DEMATEL domain (strip) | `--cause #3f7c52`, `--cause-foreground #f3faf5`, `--effect #b65105`, `--effect-foreground #fff4e5`, `--cell-edited #eef4f8` | | |

`.dark` holds shadcn's default neutral dark values (copy verbatim; unused). `@theme inline` maps every token to
`--color-*`, plus `--font-sans: 'Manrope Variable', 'Helvetica Neue', Helvetica, sans-serif`, `--font-heading:
var(--font-sans)`, `--shadow-soft: 0 1px 0 rgba(17, 24, 39, 0.04)`, radii `--radius-sm/md/lg/xl` (`-4px`, `-2px`, `=`,
`+4px`) and `--radius-2xl/3xl/4xl` (`×1.8`, `×2.2`, `×2.6`). `@theme { --container-layout: 1200px; }` gives
`max-w-layout`. `@layer base`: `* { @apply border-border outline-ring/50; }`, pointer cursor on every enabled
clickable role/control, `not-allowed` on disabled buttons/selects, `body` with `font-sans antialiased bg-background
text-foreground`, background `radial-gradient(ellipse 80% 50% at 50% -10%, #fffdf9 0%, transparent 55%),
linear-gradient(180deg, #fbf9f5 0%, var(--background) 40%, #f4f1ea 100%)`, `min-height: 100vh`.

The decision record (`docs/decisions/2026-11-16-warm-white-variant-of-the-ice2kg-theme.md`) lists the ice2kg →
warm-white mapping and measured contrast (ink 9.29–10.98:1, muted 4.77–5.29:1, placeholder 2.65:1, below AA, used
only for placeholders). Rule: "a failed contrast check may change lightness only".

PCK domain tokens to add (replacing cause/effect): the seven rating colours from `tk-app/constants.py:30-48`
(`Indivisible #0B6E6E/#ffffff`, `Reinforcing #2A9D8F/#ffffff`, `Enabling #6BAF92/#2d2d2d`, `Neutral #B0B7C3/#555555`,
`Constraining #E9C46A/#2d2d2d`, `Counteracting #E76F51/#ffffff`, `Cancelling #9B2226/#ffffff`). Their text contrast was
not measured here; DEMATELab darkened its domain hues in lightness only to pass WCAG AA, and the same check should
be done for these pairs (e.g. white on `#2A9D8F` and `#E76F51` is likely below 4.5:1).

Fonts: the **web uses Manrope Variable** (npm `@fontsource-variable/manrope`), not the legacy font. DEMATELab's
API bundles Inter TTFs only because its server-side matplotlib charts use the Qt font. PCK's Tk app uses Inter
(`tk-app/assets/fonts/Inter-{Regular,Medium,Bold,Italic}.ttf`); copy them to `apps/api/assets/fonts/` only if the
API renders charts or PDFs.

Logo: `apps/web/public/logo.png` (256×256 RGB), `favicon.ico` (48×48), `apple-touch-icon.png` (180×180 RGB), rendered
from the legacy app's logo (`apps/web/README.md:16-17`); referenced by `APP_LOGO_PATH = "/logo.png"`, the
`__root.tsx` head links, and `AppHeader` (`size-8 rounded-md`, `alt=""`). PCK's only logo asset is
`tk-app/assets/fonts/logo_icon_sidebar.png` (64×64 RGBA). Upscaling 64 px to 256 px will blur; a higher-resolution
source is needed for `logo.png` and `apple-touch-icon.png` (the 48 px favicon can be made from it).

### 7. Code-structure rules and how they are enforced

| Rule | Where stated | Enforced by |
| --- | --- | --- |
| Every code file ≤ 300 lines, tests included (fixtures, lockfiles, `.md`, `.json`, `routeTree.gen.ts` exempt) | root `AGENTS.md` Development Workflow 5; `apps/api/AGENTS.md` File size; `apps/web/AGENTS.md` Conventions | **API:** `tests/repository_rules_integration_test.py::test_files_at_most_300_lines`. **Web: not enforced by any test** (no file-reading test exists in `apps/web/src`; checked by grep). Consider adding a Vitest or script check in PCK |
| `apps/` never imports/reads the legacy folder | root `AGENTS.md`; both app AGENTS | API test `test_no_qt_app_references` (imports whose top-level name is `DEMATELab`; non-docstring string literals containing `qt-app`). Web: documentation only |
| `__init__.py` holds only a docstring; absolute imports from `apps/api` root; no relative imports; import from module files, not re-exports | `apps/api/AGENTS.md` Imports | Docstring rule by test; ordering by Ruff `I` |
| Layers: `routers/` (one statement per handler, via `ResponseBuilder`) → `features/` (all logic) → `services/` (I/O only, called by features only) / `utils/` (no I/O); `errors/`, `models/`; one router per file; routers never touch services | `apps/api/AGENTS.md` Layers | Review only |
| Class-based modules with constructor injection, one module-level instance at the end (`gemini_service = GeminiService()`); standalone `def` only for route handlers, `lifespan`, `get_settings()` and justified stateless utils | `apps/api/AGENTS.md` Class-based code | Review only |
| Typing: hints on every function; `Optional[T]` not `T | None`; `List`/`Dict`/`Tuple` from `typing`; Google docstrings on public APIs | `apps/api/AGENTS.md` | Review only |
| API naming: `*_feature.py`, `*_service.py`, `*_model(s).py`, `*_config.py`, `constants/*_constants.py`, `*_utils.py`, `errors/*_errors.py` (`app_error.py` base) | `apps/api/AGENTS.md` Naming | Review only |
| Response envelope `ApiResponseModel{success, message, data, metadata{timestamp}, error{code, fields?}}`; routes under `/api/v1`; files via `download_bytes`/`image` | `apps/api/AGENTS.md` | Unit tests of `ResponseBuilder` and routers |
| Errors: every expected failure is an `AppError` subclass (`code`, `status_code`, `public_message`, internal `detail`, optional `data`); validation → 422 `validation_error` with `error.fields`; unknown → 500 `internal_error`; never `HTTPException`, never internal text in responses | `apps/api/AGENTS.md` Error handling | `errors/error_handlers_test.py` |
| Tests: co-located `<module>_test.py`; integration tests `tests/*_integration_test.py`; classes `Test<ClassName>` on `unittest.TestCase`/`IsolatedAsyncioTestCase`; markers `unit`/`integration`/`slow` with `--strict-markers`; mock providers with `httpx.MockTransport` | `apps/api/AGENTS.md` Testing; `pyproject.toml` | pytest config |
| Ruff only, line length 120, rules E/F/I/B; Black not used | `apps/api/AGENTS.md` | `make check-api` |
| Web naming: PascalCase components (one per file, named function components); `*.utils.ts`, `*.service.ts`, `*.hook.ts`, `*.interface.ts`, `*.constants.ts`, `*.store.ts`; tests co-located `<name>.test.ts(x)` | `apps/web/AGENTS.md` | Review only |
| Web placement: `components/ui` (shadcn, never by hand), `components/general` (shared), `components/page-specific/<page>`; types in `interfaces/` (Zod); UI text in `constants/`; static files in `public/` | `apps/web/AGENTS.md` | Review only |
| No `useEffect` for data fetching (TanStack Query hooks in `hooks/`; `useMutation` for every POST); Zod validates every response and the env; no domain maths in the browser; `env` from `@/env`, never raw `import.meta.env`; Base UI with `render` prop, never Radix/`asChild`; `@/*` imports | `apps/web/AGENTS.md` | Tests per component; Biome; tsc |
| Store rule: results/exports/AI use the request snapshot, never current answers; nothing persisted | `apps/web/AGENTS.md` | `store/analysis.store.test.ts` |
| API key only in component state; never in store, query keys, mutation variables, URLs, logs; API side `SecretStr(repr=False)`, validation logs paths/types only | `apps/web/AGENTS.md`, `apps/api/AGENTS.md`, AI-keys decision | `ExplanationPanel.test.tsx`, API tests |
| Debug `console.log` committed only commented out with a purpose comment | `apps/web/AGENTS.md` | Review only |

**PCK-specific adaptation of the legacy-import test.** The legacy Tk app is flat: `tk-app/models.py` and
`tk-app/constants.py` share their names with `apps/api/models/` and `apps/api/constants/`, so a name-based check
cannot flag them. Proposed check: (a) non-docstring string literals containing `"tk-app"`; (b) top-level imports
of legacy-only names `{"aggregator", "importer", "app", "theme", "font_loader", "dialogs", "aggregation_dialog",
"aggregation_tab", "coherence_scores_tab", "range_of_influence_tab", "pca_tab", "network_tab",
"results_insights_tab", "llm_tab", "matrix_widget", "tkinter", "PIL"}`; (c) never add `tk-app` to `sys.path`
anywhere under `apps/`. The parity script must likewise not import anything from `apps/api` (same name clash).

### 8. Make targets and how `check`, `dev`, `prod` work

| Group | Target | Runs |
| --- | --- | --- |
| Help | `help` (default) | awk over `##@` sections and `## ` comments; footer about `S=`/`T=` and the legacy Makefile |
| Setup | `setup` | For each of `apps/api/.env`, `apps/web/.env`: keep if present, skip if `.env.example` missing, else copy |
| Dev | `dev` | `require_port API`, `require_port WEB` (if web exists), `$(DEV) up -d --build --wait`, then `urls` |
| | `api` / `web` | Same for one service (`web` also checks the API port) |
| | `down`, `restart [S=]`, `ps`, `logs [S=]` (`-f --tail=100`), `rebuild` (`--force-recreate --renew-anon-volumes`), `urls` | Plain `docker compose -f docker-compose-dev.yml …` |
| Shells | `sh-api`, `sh-web` | `$(DOCKER) exec -i [-t] <container> bash` |
| Checks | `check` = `check-api` + `check-web` | API: `uv run ruff format --check .`, `uv run ruff check .`, `uv run pytest`. Web: `pnpm run format:check`, `lint`, `typecheck`, `test` |
| | `test`, `test-api [T=]`, `test-web [T=]`, `lint`, `typecheck`, `format` | Inside the dev containers |
| Deps | `install` | `uv sync --frozen`; `pnpm install --frozen-lockfile` |
| Prod | `prod`, `prod-down`, `prod-restart [S=]`, `prod-ps`, `prod-logs [S=]` | `$(DOCKER) compose -f docker-compose-prod.yml …` (`prod` = `up -d --build --wait`) |

Mechanics:

- **Engine:** `DOCKER` is `docker` when `command -v docker` succeeds, else `podman`; overridable (`make DOCKER=podman …`).
- **Container-first checks:** every check target depends on `_api-up` / `_web-up`, which call `require_dev`:
  `docker inspect -f '{{.State.Running}} {{index .Config.Labels "com.docker.compose.project"}}' <container>` must
  print `true <DEV_PROJECT>`. Prod uses the same container names but its images lack dev tools, so the label check
  stops checks from running against prod. `TTY := -t` only when stdin is a terminal.
- **Port guard:** `require_port PORT CONTAINER` passes if the dev container of this project already publishes the
  port, else fails when `nc -z localhost PORT` (or `ss -H -ltn 'sport = :PORT'`) shows it occupied, and errors if
  neither tool exists. Prod targets have no port guard (Nginx's `HTTP_PORT` is not checked).
- `WEB_PORT`/`API_PORT` are `override` constants, used only for messages and port checks; the real ports live in
  compose, Dockerfiles, `package.json`, Nginx.

### 9. Clashes when both stacks run on one host, and PCK values

| Item | DEMATELab (new / legacy) | PCK legacy (`tk-app/`) | PCK new (proposed) | Clash? |
| --- | --- | --- | --- | --- |
| Dev web host+container port | 3000 (ice2kg also 3000) | – | **3001** | Resolved |
| Dev API host+container port | 50001 (ice2kg also 50001) | – | **50002** | Resolved |
| Legacy noVNC | `127.0.0.1:6080` | `127.0.0.1:${NOVNC_PORT:-6090}` | – | None |
| Prod public port | Nginx `${HTTP_PORT:-80}:80` (ice2kg same) | – | Nginx `${HTTP_PORT:-8081}:80` proposed | **Clash at default 80** if both prods share a host; owner decision (keep 80 if PCK gets its own VPS) |
| Compose project, dev | `dematelab-dev` (new **and** qt, an unresolved DEMATELab clash) | `policycoherencekit-tk-dev` | `policycoherencekit-dev` | None |
| Compose project, prod | `dematelab` / `dematelab-prod` | `policycoherencekit-tk-prod` | `policycoherencekit` | None |
| Container names (global) | `dematelab-{api,web,nginx}`; `dematelab-dev`, `dematelab-prod` | `policycoherencekit-tk-dev`, `policycoherencekit-tk-prod` | `policycoherencekit-api`, `policycoherencekit-web`, `policycoherencekit-nginx` | None. The legacy Makefile's filter `name=^policycoherencekit-tk-(dev|prod)$` is anchored, so it never matches the new containers |
| Image names | No `image:` key → `<project>-<service>`: `dematelab-dev-api`, `dematelab-dev-web`, `dematelab-api`, `dematelab-web`, `dematelab-nginx`; qt `dematelab:dev/:prod` | `policycoherencekit-tk:dev`, `policycoherencekit-tk:prod` | Auto: `policycoherencekit-dev-api`, `policycoherencekit-dev-web`, `policycoherencekit-api`, `policycoherencekit-web`, `policycoherencekit-nginx` | None |
| Networks | `dematelab-dev_app-network`, `dematelab_app-network` | `policycoherencekit-tk-{dev,prod}_default` | `policycoherencekit-dev_app-network`, `policycoherencekit_app-network` | None (service DNS `web`/`api` is per network) |
| Named volumes | New: none (anonymous `/app/node_modules`); qt `dematelab-exports` | `policycoherencekit-exports` (explicit global `name:`) | None (stateless) | None today. If a volume is ever added, do not call it `policycoherencekit-exports` |
| Nginx upstreams | `web:3000`, `api:50001` | – | `web:3001`, `api:50002` | Internal only; changed for consistency with "same port inside and outside" |
| API healthcheck | `http://localhost:50001/api/v1/is-alive` | `http://127.0.0.1:6080/` | `http://localhost:50002/api/v1/is-alive` | – |
| `CORS_ORIGINS` | `http://localhost:3000` | – | `http://localhost:3001` | Would silently break CORS if left |
| `VITE_API_BASE_URL` | `http://localhost:50001` | – | `http://localhost:50002` | Would silently call DEMATELab's API if left |
| Package names | `dematelab-api`, `dematelab-web` | `policycoherencekit` | `policycoherencekit-api`, `policycoherencekit-web` | – |
| Make constants | `DEV_PROJECT dematelab-dev`, `API_CONTAINER dematelab-api`, `WEB_CONTAINER dematelab-web` | `PROJECT policycoherencekit-tk` | `policycoherencekit-dev`, `policycoherencekit-api`, `policycoherencekit-web` | – |

Every hard-coded `3000`/`50001` in DEMATELab outside docs, lockfiles and fixtures (grep), to change to 3001/50002:
`Makefile:20,21,53`; `docker-compose-dev.yml:11,29,38`; `docker-compose-prod.yml:29`; `nginx/nginx.prod.conf:14,15,55,56`;
`apps/api/{.env.example:11, Dockerfile.dev:29,32, Dockerfile.prod:33,37, config/settings_config.py:26,
config/settings_config_test.py:45, constants/app_constants.py:7, AGENTS.md:41,294, README.md:19,33,34,91,103}`;
`apps/web/{package.json:6,9, Dockerfile.dev:16, Dockerfile.prod:27,36, .env.example:9,11, vitest.config.ts:13,
src/env.ts:5, src/env.test.ts:8,13, src/utils/api.utils.ts:6, src/utils/api.utils.test.ts:22,23,32,48,
src/services/analysis.service.test.ts:18, src/services/health.service.test.ts:52, AGENTS.md:23, README.md:30,44,61}`;
root `AGENTS.md:20,61,75,86,87`, `README.md:188,189,191`. Name strings ("DEMATELab"/"dematelab") also appear in
`apps/api/{pyproject.toml, main.py, constants/app_constants.py, constants/llm_constants.py, models/response_model.py,
tests/repository_rules_integration_test.py, config/settings_config_test.py, services/llm_provider_service_test.py}`,
`apps/web/{package.json, src/constants/layout.constants.ts, src/components/general/AppHeader(.test).tsx,
AppFooter.test.tsx, src/components/ui/sonner.tsx}`.

### 10. Lessons from the playbook's "Problems hit" table that apply up front

| DEMATELab problem (playbook Finding 8) | Applies to PCK? | Up-front action |
| --- | --- | --- |
| Moving sample data broke legacy compose mounts | Already handled: `tk-app/docker-compose-{dev,prod}.yml` mount `../data/examples`, `.gitignore` uses `tk-app/exports/*`, `.dockerignore` dropped `Example data` | Still stale: root `AGENTS.md:4,7,9` and `README.md:123,176,195,204` describe root-level `python3 main.py`, root `make dev`, and `Example data/…`; `tk-app/Makefile:3` says "Run from the repository root". Fix with the restructure commit |
| Prod Nginx failed without `web` (Compose rejects dependency on a disabled profile) | Yes, if API lands first | Either build web scaffold before `make prod`, or use `required: false` + runtime resolver temporarily (already in the copied conf) and remove it after |
| Ports held by another stack | Avoided by design (3001/50002) | Keep the `require_port` guard; decide the prod `HTTP_PORT` default |
| Legacy and new dev stacks share a Compose project name | Avoided (`policycoherencekit-tk-dev` vs `policycoherencekit-dev`) | Document both names in root `AGENTS.md` |
| Gemini client closed early, unwrapped network errors, no SDK timeout | Only if Gemini is added | Copy DEMATELab's fixed `gemini_service.py`; httpx service already maps errors and uses 120 s |
| Azure endpoint SSRF | Only if Azure is added | Copy the https + host-suffix allow-list |
| Business rules hidden in GUI files | Very likely: PCK's AGENTS.md says `compute_scores`, `compute_entropy`, `compute_pca`, `compute_centrality`, `compute_insights` live in `*_tab.py`, Excel export in `app.py:_export_to_excel`, and the "Average forced below three decision-makers" rule is in the UI | Inventory every computation inside `tk-app/*_tab.py`, `app.py`, `aggregation_dialog.py` with file:line before planning |
| Plan values contradicting each other / the code (dpi, tie order) | Yes | Independent plan review against `tk-app/` code; plan file is the single source of truth |
| Enter submitted unclamped stepper value; focus on hidden inputs; stale "answered" steps | Yes if the flow is copied | Copy the fixed `StepFrame`, `NumberStepper`, `flow.utils.ts`, and their tests rather than re-deriving |
| Legacy behaviour unstable (singular matrix, exact ties) | PCK has Majority ties (`TiedCell.chosen`, `resolve_ties`) and even-count Median lower/upper choice | Generate fixtures for tie and even-count cases explicitly; record which outputs depend on user choice |
| New for PCK: flat legacy module names clash with `apps/api` packages | Yes (`models`, `constants`) | Rewrite the repository-rules legacy check (Finding 7); parity script inserts `tk-app` on `sys.path` and imports nothing from `apps/api` |
| New for PCK: multi-Python legacy lock | `tk-app/pyproject.toml` `requires-python >=3.9`; lock has four numpy versions (2.0.2 / 2.2.6 / 2.4.6 / 2.5.4) | Always pass `--python 3.13` (and `--frozen`) to the fixture script, so fixtures use numpy 2.5.4, the version the API pins |

## Limitations

- Nothing was built or run; versions come from the manifests and lockfiles at `6a76ae2`, not from a fresh install.
- Only the first 80 lines of `services/llm_provider_service.py` and `store/analysis.store.ts` and the head of
  the parity script and plans were read; finer behaviour in the unread parts is not inventoried.
- `apps/web/src/components/page-specific/analysis/*` beyond the flow shell, step frame, navigation and progress
  was not read (it is DEMATEL-specific and listed as "strip" by type).
- The claim that the web 300-line rule is not enforced rests on a grep for file-reading code in `apps/web/src`
  and `apps/web/scripts` (only `.gitkeep`).
- The rating-colour contrast ratios for PCK were not measured.
- The proposed prod `HTTP_PORT` default (`8081`) is a suggestion, not checked against other services on the
  target host.

## Recommendations

1. Owner decisions before planning: prod `HTTP_PORT` default (80 on an own VPS vs `8081` on a shared host);
   AI providers (keep legacy Groq + OpenAI, or add DEMATELab's set); server-side charts (matplotlib PNG) vs
   browser rendering for the network/PCA/entropy views; whether the AI-text PDF export moves to the API; the app
   subtitle and a high-resolution logo source.
2. Write the backend and frontend plans using DEMATELab's plan structure (playbook Finding 9 step 5), with
   this report as the conventions input and a separate Tk logic/UI inventory as the other two inputs.
3. In Phase 1, copy the files in Findings 2–4 and apply the Finding 9 substitutions with one grep pass for
   `3000|50001|DEMATELab|dematelab|qt-app|Qt` before the first `make check`.
4. Add a web-side 300-line check (DEMATELab only enforces it in the API).
5. Fix the stale root `AGENTS.md`, `README.md` and `tk-app/Makefile` comments in the restructure commit.

## References

- DEMATELab playbook: `dematelab/docs/reports/2026-11-16-qt-to-fastapi-and-tanstack-migration-playbook-report.md`
  (Findings 3, 4, 8, 9)
- DEMATELab decisions: `dematelab/docs/decisions/2026-11-16-*.md` (7 files)
- DEMATELab plans: `dematelab/docs/plans/2026-11-16-port-backend-to-fastapi-api-plan.md`
  (Phase 1 lines 242-271, Phase 8 lines 419-450), `dematelab/docs/plans/2026-11-16-rebuild-ui-in-tanstack-start-plan.md`
  (Phases 1-3 lines 258-290)
- DEMATELab infra: `Makefile`, `docker-compose-dev.yml`, `docker-compose-prod.yml`, `nginx/Dockerfile.prod`,
  `nginx/nginx.prod.conf`, `scripts/generate_parity_fixtures.py`
- DEMATELab API: `apps/api/{AGENTS.md, pyproject.toml, uv.lock, Dockerfile.dev, Dockerfile.prod, .env.example, main.py,
  config/settings_config.py, constants/{app_constants,llm_constants}.py, errors/*, middleware/cache_control_middleware.py,
  models/{response_model,error_models,health_models}.py, utils/response_utils.py, routers/health.py,
  features/health_feature.py, services/llm_provider_service.py, tests/repository_rules_integration_test.py}`
- DEMATELab web: `apps/web/{AGENTS.md, package.json, pnpm-lock.yaml, pnpm-workspace.yaml, biome.json, components.json,
  tsconfig.json, vite.config.ts, vitest.config.ts, Dockerfile.dev, Dockerfile.prod, .env.example, src/styles.css,
  src/env.ts, src/routes/*, src/components/general/*, src/components/page-specific/analysis/FlowShell.tsx,
  src/store/analysis.store.ts, src/utils/api.utils.ts}`
- PCK legacy: `tk-app/{Makefile, docker-compose-dev.yml, docker-compose-prod.yml, .env.example, pyproject.toml, uv.lock,
  constants.py:30-48,76-100, llm_tab.py:61-79,208-249}`; root `AGENTS.md`, `README.md`, `.gitignore`
- ice2kg ports/names: `ice2kg/{docker-compose-dev.yml, docker-compose-prod.yml, Makefile:23-26}`
