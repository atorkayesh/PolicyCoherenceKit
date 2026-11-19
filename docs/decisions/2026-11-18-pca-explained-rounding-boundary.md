# PCA Explained Variance At A Rounding Boundary Accepts Either Rounded Neighbour

**Status:** Accepted
**Date:** 18 November, 2026
**Deciders:** Youpele Michael (owner), Claude Code

## Decision

When the legacy fixture's unrounded PCA percentage lies within 1e-9 of a one-decimal rounding boundary (`x.x5`), the parity test compares the unrounded percentage at `atol=1e-12` and accepts either rounded neighbour for `explained`. The fixtures record the unrounded percentages (`pca.explained_unrounded`). Every other value and every other tolerance is unchanged; the API still returns `round(pct, 1)` exactly as legacy.

## Context

The Linux parity gate failed on `r5x3__majority_last`: the exact PC1 share is 56.25%. macOS Accelerate computes `56.24999999999998` (→ 56.2) and Linux OpenBLAS `56.25000000000002` (→ 56.3). Singular values agree within about 2e-15 and coordinates within 1.8e-15; only half-to-even rounding of the binary value turns a 4e-14 difference into 0.1. The legacy app itself shows 56.3 on Linux. Coordinator decision (Option A) of 18 November, 2026, recorded in the same way DEMATELab documented its BLAS-dependent edge cases.

## Alternatives Considered

- **Generate the fixtures on Linux:** the macOS host run would then fail the same way.
- **Change the case seed:** hides the behaviour instead of documenting it.

## Consequences

- `tests/parity_fixtures.py` (`ParityAssertions.explained`) implements the rule; `apps/api/AGENTS.md` lists it under Numerical Parity.
- Users may see a 0.1 difference in `explained` between the desktop app on macOS and the web app on Linux at exact boundaries.

## Related Work

- Plan: [Port The Policy Coherence Kit Backend To A Dockerised FastAPI `apps/api`](../plans/2026-11-18-port-backend-to-fastapi-api-plan.md)
- Conventions source: DEMATELab's decision records of 16 November, 2026 (`dematelab/docs/decisions/`)
