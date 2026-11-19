# One Project Per Browser Session

**Status:** Accepted
**Date:** 18 November, 2026
**Deciders:** Youpele Michael (owner), Claude Code

## Decision

The web app holds one project at a time in the browser and sends it with every request. The legacy multi-project sidebar, project-name uniqueness and run history are dropped. Limits are 2–100 policies and 1–50 decision-makers.

## Context

The API is stateless and has no accounts (see the stateless-API decision). The legacy `Project` list lives only in memory (`app.py:179-190`).

## Alternatives Considered

- **Several projects in browser storage:** adds persistence the owner ruled out.

## Consequences

- `/setup/validate` checks project, decision-maker and policy names without the `Duplicate Project` rule.
- Import uses the project's policy list as the reference whenever one exists.

## Related Work

- Plan: [Port The Policy Coherence Kit Backend To A Dockerised FastAPI `apps/api`](../plans/2026-11-18-port-backend-to-fastapi-api-plan.md)
- Plan: [Rebuild The UI In TanStack Start](../plans/2026-11-18-rebuild-ui-in-tanstack-start-plan.md)
- Conventions source: DEMATELab's decision records of 16 November, 2026 (`dematelab/docs/decisions/`)
