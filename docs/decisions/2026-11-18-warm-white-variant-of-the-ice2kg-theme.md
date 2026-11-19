# The Web App Uses DEMATELab's Warm-White Variant Of The ice2kg Theme, With The Legacy Rating Colours Made WCAG AA

**Status:** Accepted
**Date:** 18 November, 2026
**Deciders:** Youpele Michael (owner), Claude Code

## Decision

`apps/web` uses DEMATELab's warm-white token table unchanged (ink `#023d6b`: 10.98 / 10.52 / 9.89 on card / background / muted; muted text `#6f6a60`: 5.29 / 5.07 / 4.77), plus the Policy Coherence Kit domain tokens exactly as listed in the frontend plan's Theme table. When a text/background pair fails WCAG AA (4.5:1), the rule order is: darken a dark text colour; otherwise use dark ink `#2d2d2d`; otherwise darken the fill in 0.005 lightness steps. Role inks: `#238377` (4.51), `#b9590d` (4.60), `#6B7280` (4.76). Health bars keep their legacy colours. The table is enforced by `apps/web/src/test/theme-contrast.test.ts`.

## Context

The owner asked for the same look as DEMATELab while keeping the seven legacy rating colours from the Tkinter app (`tk-app/constants.py:30-49`). Several legacy pairs are below AA contrast.

## Alternatives Considered

- **The legacy Tk palette as is:** rejected; below AA and inconsistent with DEMATELab.
- **ice2kg's cool whites:** rejected by the owner for DEMATELab, and kept consistent here.

## Consequences

- Theme changes go through this table; a failed contrast check may change lightness only.
- XLSX export and chart series keep the legacy colours served by `/scales`.

## Related Work

- Plan: [Rebuild The UI In TanStack Start](../plans/2026-11-18-rebuild-ui-in-tanstack-start-plan.md)
- DEMATELab decision `docs/decisions/2026-11-16-warm-white-variant-of-the-ice2kg-theme.md` (`dematelab`)
