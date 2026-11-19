# Each Service Has Its Own Env File

**Status:** Accepted
**Date:** 18 November, 2026
**Deciders:** Youpele Michael (owner), Claude Code

## Decision

Each service reads only its own env file, created from the `.env.example` next to it by `make setup`: `apps/api/.env` (`APP_ENV`, `CORS_ORIGINS`, `WEB_CONCURRENCY`) and `apps/web/.env`. There is no root `.env`. Compose overrides only `APP_ENV`. The legacy app keeps `tk-app/.env` (`VNC_PASSWORD`, `SCREEN_GEOMETRY`, `NOVNC_PORT`).

## Context

A shared env file leaks settings into services that do not need them and hides which service a variable belongs to. DEMATELab and ice2kg follow the same rule.

## Alternatives Considered

- **One root `.env`:** simpler to create, but every container receives every value.

## Consequences

- `make setup` never overwrites a file and skips missing examples.
- AI provider keys are never in an env file.
- `.env` files are never committed.

## Related Work

- Plan: [Port The Policy Coherence Kit Backend To A Dockerised FastAPI `apps/api`](../plans/2026-11-18-port-backend-to-fastapi-api-plan.md)
- Conventions source: DEMATELab's decision records of 16 November, 2026 (`dematelab/docs/decisions/`)
