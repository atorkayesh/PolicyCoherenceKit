# Docker Compose With Nginx As The Only Public Entry

**Status:** Accepted
**Date:** 18 November, 2026
**Deciders:** Youpele Michael (owner), Claude Code

## Decision

Development and production run with Docker Compose (`docker-compose-dev.yml`, project `policycoherencekit-dev`; `docker-compose-prod.yml`, project `policycoherencekit`). Ports are the same inside and outside the containers: web 3001, API 50002. In production only Nginx (`policycoherencekit-nginx`) is published, on `${HTTP_PORT:-8081}:80`; it routes `/api/` to `api:50002` and everything else to `web:3001`, with a runtime resolver, `client_max_body_size 20m` and `proxy_read_timeout 300s`. HTTPS is prepared in `nginx/nginx.prod.conf` but commented out. There are no volumes.

## Context

DEMATELab and ice2kg use 3000/50001 and port 80, and the legacy stack uses `policycoherencekit-tk-dev`/`-prod`, so the new names and ports avoid every clash on one host. A 100-policy × 50-decision-maker request is about 7–8 MB of JSON.

## Alternatives Considered

- **Publish the API and web ports directly in production:** two public entry points and no place for TLS.
- **Default `HTTP_PORT` 80:** clashes with DEMATELab and ice2kg on a shared host.

## Consequences

- Until `apps/web` lands (frontend deferred edit D1), `web` sits under the Compose profile `web` and Nginx depends on it with `required: false`; `/` answers 502 until then.
- TLS must be enabled before the AI interpretation is used in production (see the AI-keys decision).

## Related Work

- Plan: [Port The Policy Coherence Kit Backend To A Dockerised FastAPI `apps/api`](../plans/2026-11-18-port-backend-to-fastapi-api-plan.md)
- Conventions source: DEMATELab's decision records of 16 November, 2026 (`dematelab/docs/decisions/`)
