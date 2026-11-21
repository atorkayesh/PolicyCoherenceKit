# Policy Coherence Kit: dev, check, and production entrypoints for the rebuilt app (apps/). `just` lists every
# recipe. The legacy Tk app has its own Makefile: make -C tk-app dev (see README.md).
#
# Container first: the stack and every check run in Docker, so the host needs only Docker and just. Each
# recipe wraps a plain docker compose, uv, or pnpm command (just echoes it), and those commands keep working
# without just.
#
#   just dev      start the api and web with hot reload
#   just check    the pre-commit checks, inside the dev containers
#   just prod     start production web and api on the VPS (served by the shared HTTPS proxy, whose config
#                 and orchestration live in the DEMATELab repo: nginx/, `just proxy …` there)
#
# Narrow some recipes with a service (`just logs api`, `just prod-restart web`) or test arguments
# (`just test-api tests/parity_integration_test.py -v`).

set shell := ["bash", "-euo", "pipefail", "-c"]

# Fixed ports, the same inside and outside the containers. These values only feed the printed URLs and the
# port checks.
web_port := "3001"
api_port := "50002"

# Container engine: docker when installed, otherwise podman. Override with `DOCKER=podman just <recipe>`.
docker := env("DOCKER", `command -v docker >/dev/null 2>&1 && echo docker || echo podman`)

dev_compose  := docker + " compose -f docker-compose-dev.yml"
prod_compose := docker + " compose -f docker-compose-prod.yml"

dev_project   := "policycoherencekit-dev"
api_container := "policycoherencekit-api"
web_container := "policycoherencekit-web"

# -t only when a terminal is attached, so recipes also work from scripts and pipes.
tty      := if `[ -t 0 ] && echo yes || true` == "yes" { "-t" } else { "" }
api_exec := docker + " exec -i " + tty + " " + api_container
web_exec := docker + " exec -i " + tty + " " + web_container

# List every recipe
[group('help')]
help:
    @{{just_executable()}} --list --unsorted
    @echo
    @echo "Legacy Tk app: make -C tk-app help"

# ── Setup ────────────────────────────────────────────────────────────────────────────────────────

# Create each service's .env from its .env.example (never overwrites; skips missing examples)
[group('setup')]
setup:
    @for f in apps/api/.env apps/web/.env; do \
        if [ -f $f ]; then echo "→ $f already exists, left unchanged"; \
        elif [ ! -f $f.example ]; then echo "→ $f.example does not exist, skipped"; \
        else cp $f.example $f && echo "→ created $f from $f.example"; fi; \
    done

# ── Development stack ────────────────────────────────────────────────────────────────────────────

# Start the api and web with hot reload (detached; then just logs)
[group('dev')]
dev: _require-web (_require-port api_port api_container) (_require-port web_port web_container)
    {{dev_compose}} up -d --build --wait
    @{{just_executable()}} urls

# Start only the api
[group('dev')]
api: (_require-port api_port api_container)
    {{dev_compose}} up -d --build --wait api
    @echo "→ API docs http://localhost:{{api_port}}/api/docs"

# Start the web app (and the api it needs)
[group('dev')]
web: _require-web (_require-port api_port api_container) (_require-port web_port web_container)
    {{dev_compose}} up -d --build --wait web
    @{{just_executable()}} urls

# Stop and remove the dev containers
[group('dev')]
down:
    {{dev_compose}} down

# Restart the dev services, or one: just restart api
[group('dev')]
restart service="":
    {{dev_compose}} restart {{service}}

# Show the dev containers and their health
[group('dev')]
ps:
    {{dev_compose}} ps

# Follow dev logs, or one service's: just logs api
[group('dev')]
logs service="":
    {{dev_compose}} logs -f --tail=100 {{service}}

# Rebuild the dev images and containers (after dependency changes)
[group('dev')]
rebuild: (_require-port api_port api_container)
    {{dev_compose}} up -d --build --force-recreate --renew-anon-volumes --wait
    @{{just_executable()}} urls

# Print the dev URLs
[group('dev')]
urls:
    @echo "→ Web           http://localhost:{{web_port}}"
    @echo "→ API docs      http://localhost:{{api_port}}/api/docs"
    @echo "→ API health    http://localhost:{{api_port}}/api/v1/health"

# ── Shells ───────────────────────────────────────────────────────────────────────────────────────

# Open a shell in the api container
[group('shells')]
sh-api:
    {{api_exec}} bash

# Open a shell in the web container
[group('shells')]
sh-web: _require-web
    {{web_exec}} bash

# ── Checks (inside the dev containers) ───────────────────────────────────────────────────────────

# All pre-commit checks for both apps
[group('checks')]
check: check-api check-web

# API checks: Ruff format check, Ruff lint, pytest
[group('checks')]
check-api: _api-up
    {{api_exec}} uv run ruff format --check .
    {{api_exec}} uv run ruff check .
    {{api_exec}} uv run pytest

# Web checks: format check, lint, typecheck, tests
[group('checks')]
check-web: _web-up
    {{web_exec}} pnpm run format:check
    {{web_exec}} pnpm run lint
    {{web_exec}} pnpm run typecheck
    {{web_exec}} pnpm run test

# Fixture-generator scripts: Ruff lint and format check with the api config (on the host, needs uv)
[group('checks')]
check-scripts:
    uv run --project apps/api ruff check --config apps/api/pyproject.toml scripts
    uv run --project apps/api ruff format --check --config apps/api/pyproject.toml scripts

# Run the api and web tests
[group('checks')]
test: test-api test-web

# Run pytest with optional arguments: just test-api tests/parity_integration_test.py -v
[group('checks')]
test-api *args: _api-up
    {{api_exec}} uv run pytest {{args}}

# Run the web tests with an optional filter: just test-web charts
[group('checks')]
test-web *args: _web-up
    {{web_exec}} pnpm run test {{args}}

# Lint both apps (Ruff, the web linter)
[group('checks')]
lint: _api-up _web-up
    {{api_exec}} uv run ruff check .
    {{web_exec}} pnpm run lint

# Typecheck the web app
[group('checks')]
typecheck: _web-up
    {{web_exec}} pnpm run typecheck

# Format both apps (Ruff, the web formatter); run before committing
[group('checks')]
format: _api-up _web-up
    {{api_exec}} uv run ruff format .
    {{web_exec}} pnpm run format

# ── Dependencies ─────────────────────────────────────────────────────────────────────────────────

# Install dependencies in the dev containers from the lockfiles (after a pull)
[group('dependencies')]
install: _api-up _web-up
    {{api_exec}} uv sync --frozen
    {{web_exec}} pnpm install --frozen-lockfile

# ── Production (on the VPS) ──────────────────────────────────────────────────────────────────────

# Build and start production web and api (served by the shared proxy in the DEMATELab repo's nginx/)
[group('production')]
prod: prod-network
    {{prod_compose}} up -d --build --wait

# Stop and remove the production containers
[group('production')]
prod-down:
    {{prod_compose}} down

# Restart production, or one service: just prod-restart api
[group('production')]
prod-restart service="":
    {{prod_compose}} restart {{service}}

# Show the production containers and their health
[group('production')]
prod-ps:
    {{prod_compose}} ps

# Follow production logs, or one service's: just prod-logs api
[group('production')]
prod-logs service="":
    {{prod_compose}} logs -f --tail=100 {{service}}

# Create the external network shared with the HTTPS proxy (DEMATELab's nginx/) if missing; never removed here
[group('production')]
prod-network:
    @{{docker}} network inspect proxy >/dev/null 2>&1 || {{docker}} network create proxy

# ── Guards ───────────────────────────────────────────────────────────────────────────────────────

# Checks need the dev containers: prod uses the same container names, but its images have no dev tools.
[private]
_require-dev container:
    @test "$({{docker}} inspect -f '{{{{.State.Running}} {{{{index .Config.Labels "com.docker.compose.project"}}' {{container}} 2>/dev/null)" = "true {{dev_project}}" \
        || { echo "→ {{container}} is not running from docker-compose-dev.yml (just dev)" >&2; exit 1; }

[private]
_api-up: (_require-dev api_container)

[private]
_web-up: _require-web (_require-dev web_container)

# Web recipes explain themselves when apps/web is missing (for example in a partial checkout).
[private]
_require-web:
    @test -f apps/web/package.json \
        || { echo "→ apps/web/package.json is missing: the web recipes need apps/web" >&2; exit 1; }

# Fail before Compose starts when a fixed port is taken by something else (for example another app using
# 3001/50002). Reuses a running dev container that already publishes the port.
[private]
_require-port port container:
    #!/usr/bin/env bash
    set -euo pipefail
    state="$({{docker}} inspect -f '{{{{.State.Running}} {{{{index .Config.Labels "com.docker.compose.project"}}' {{container}} 2>/dev/null || true)"
    if [ "$state" = "true {{dev_project}}" ] && {{docker}} port {{container}} {{port}}/tcp 2>/dev/null | grep -q ':{{port}}$'; then
        exit 0
    fi
    occupied=false
    if command -v nc >/dev/null 2>&1; then
        nc -z localhost {{port}} >/dev/null 2>&1 && occupied=true
    elif command -v ss >/dev/null 2>&1; then
        ss -H -ltn 'sport = :{{port}}' | grep -q . && occupied=true
    else
        echo "→ checking fixed ports requires nc (macOS/Linux) or ss (Linux); install one and retry" >&2
        exit 1
    fi
    if [ "$occupied" = true ]; then
        echo "→ port {{port}} is already in use; free it and retry (Policy Coherence Kit uses fixed ports, see AGENTS.md)" >&2
        exit 1
    fi
