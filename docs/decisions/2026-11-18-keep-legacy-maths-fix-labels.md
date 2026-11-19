# Keep The Legacy Maths, Fix The Labels

**Status:** Accepted
**Date:** 18 November, 2026
**Deciders:** Youpele Michael (owner), Claude Code

## Decision

Every number equals the Tk app's for the same input, including known calculation oddities (the plan's "Known Tkinter Behaviour Kept" list, repeated in `apps/api/AGENTS.md`). Wrong or inconsistent labels and texts are fixed (L1–L16 in the plan) and every fix has a test. Parity fixtures are generated from `tk-app/` (`scripts/generate_parity_fixtures.py`) and compared at `rtol=0, atol=1e-12`; texts are compared exactly after only the literal L11–L14 replacements; the prompt is compared exactly.

## Context

Users compare results with the desktop app, and the legacy app has no tests, so the fixtures are the only specification of its numbers. The logic report lists the label drift (`Avg`, `Median` without Lower/Upper, arrows written four ways, `Reinforcing` used for any positive link).

## Alternatives Considered

- **Fix the maths too:** would make every comparison with the desktop app ambiguous.
- **Keep the labels too:** keeps known inconsistencies in a new product.

## Consequences

- Changing a formula, rounding, threshold, the prompt or a colour needs new fixtures and a new decision record.
- Tolerances are never loosened without a decision record (see the PCA rounding-boundary decision).

## Related Work

- Plan: [Port The Policy Coherence Kit Backend To A Dockerised FastAPI `apps/api`](../plans/2026-11-18-port-backend-to-fastapi-api-plan.md)
- Conventions source: DEMATELab's decision records of 16 November, 2026 (`dematelab/docs/decisions/`)
