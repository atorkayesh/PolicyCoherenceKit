# The API Is Stateless And Returns Chart Data, Never Chart Images

**Status:** Accepted
**Date:** 18 November, 2026
**Deciders:** Youpele Michael (owner), Claude Code

## Decision

Every results endpoint (`/analysis`, `/analysis/charts/network`, `/analysis/export/xlsx`, `/explanations`) receives the full request (project, policies, decision-makers with ratings, method, weights, median choice, tie choices) and recomputes. Nothing is stored, cached or logged that holds user data; error log details never contain names or ratings. Charts are drawn in the browser from API chart data; the API contains no matplotlib and no image rendering. The XLSX export covers the current run only.

## Context

The legacy app keeps projects and a run history in memory (`app.py:179-190`, `:2617`) and draws its two plots on a Tk canvas. A web API with sessions would need storage, accounts and cleanup; recomputation costs about 1–3 s at the 100-policy limit.

## Alternatives Considered

- **Server-side sessions or a database:** persistence and accounts are non-goals.
- **Server-rendered PNG charts (matplotlib):** the earlier plan; replaced by the owner on 2026-11-18 (see the ECharts decision).

## Consequences

- The XLSX export no longer contains past runs; the legacy `Avg`/`Median` sheet history is gone.
- CPU-bound work runs in `asyncio.to_thread`; gunicorn workers isolate processes.

## Related Work

- Plan: [Port The Policy Coherence Kit Backend To A Dockerised FastAPI `apps/api`](../plans/2026-11-18-port-backend-to-fastapi-api-plan.md)
- Conventions source: DEMATELab's decision records of 16 November, 2026 (`dematelab/docs/decisions/`)
