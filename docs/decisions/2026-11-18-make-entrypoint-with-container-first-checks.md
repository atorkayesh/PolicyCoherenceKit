# Make Is The Entrypoint And Checks Run In The Containers

**Status:** Accepted
**Date:** 18 November, 2026
**Deciders:** Youpele Michael (owner), Claude Code

## Decision

The root `Makefile` (copied from DEMATELab) is the entrypoint: `make dev`, `make prod`, `make check`, `make check-api`, `make check-web`, `make test-api T=...`, `make format`, and the rest listed by `make help`. Checks run inside the dev containers (`require_dev` verifies the Compose project label), so the host needs only Docker or podman and make. Fixed ports are checked before Compose starts (`require_port`). The legacy app keeps `make -C tk-app ...`.

## Context

Host Python and Node versions differ between machines; running checks in the containers makes them reproducible and makes the Linux (OpenBLAS) parity run the default.

## Alternatives Considered

- **Host-only commands:** every developer needs uv, Python 3.13 and Node locally, and parity runs only on the host BLAS.

## Consequences

- Every make target wraps a plain `docker compose`, `uv` or `pnpm` command that also works without make.
- `make check` passes only once the web app exists; until then `make check-api` is the backend gate.

## Related Work

- Plan: [Port The Policy Coherence Kit Backend To A Dockerised FastAPI `apps/api`](../plans/2026-11-18-port-backend-to-fastapi-api-plan.md)
- Conventions source: DEMATELab's decision records of 16 November, 2026 (`dematelab/docs/decisions/`)
