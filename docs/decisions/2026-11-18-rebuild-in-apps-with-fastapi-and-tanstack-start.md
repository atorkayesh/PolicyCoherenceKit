# Rebuild In `apps/` With FastAPI And TanStack Start

**Status:** Accepted
**Date:** 18 November, 2026
**Deciders:** Youpele Michael (owner), Claude Code

## Decision

The Policy Coherence Kit is rebuilt as a FastAPI API in `apps/api` (Python 3.13, uv, Ruff, pytest) and a TanStack Start web app in `apps/web`. The legacy Tkinter app moves to `tk-app/`, stays runnable with its own Makefile and Compose files, and is read-only. Nothing in `apps/` imports, reads or starts `tk-app/`; only `scripts/generate_parity_fixtures.py` runs against it.

## Context

The Tk app is a desktop GUI with no HTTP API and no tests; about a third of its rules sit in GUI files (`tk-app/app.py:2533-2611`, `aggregation_dialog.py:570-613`, `dialogs.py:1080-1124`, the `*_tab.py` compute functions). DEMATELab already went through the same rebuild, so its layout and conventions are copied (`docs/reports/2026-11-18-dematelab-conventions-inventory-report.md`).

## Alternatives Considered

- **Keep Tkinter and serve it over noVNC:** works today, but it cannot become a web product and keeps the logic untestable.
- **Port the GUI to another desktop toolkit:** does not solve web delivery.

## Consequences

- Code rules (routers → features → services/utils, class-based modules, ≤ 300 lines, co-located tests) are documented in `apps/api/AGENTS.md` and enforced by `tests/repository_rules_integration_test.py`.
- Every number must equal the legacy app's (parity fixtures, see the keep-legacy-maths decision).
- `tk-app/` stays available as the reference until the owner retires it.

## Related Work

- Plan: [Port The Policy Coherence Kit Backend To A Dockerised FastAPI `apps/api`](../plans/2026-11-18-port-backend-to-fastapi-api-plan.md)
- Plan: [Rebuild The UI In TanStack Start](../plans/2026-11-18-rebuild-ui-in-tanstack-start-plan.md)
- Conventions source: DEMATELab's decision records of 16 November, 2026 (`dematelab/docs/decisions/`)
