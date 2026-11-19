# Charts Are Drawn In The Browser With Apache ECharts From API Chart Data

**Status:** Accepted
**Date:** 18 November, 2026
**Deciders:** Youpele Michael (owner), Claude Code

## Decision

Apache ECharts is the only chart library (P1). The API computes everything the browser draws: network layouts (circular, force-directed, spectral, shell, in legacy order) on a square 600 × 600 logical canvas, PCA coordinates, axis bounds and texts (P3, P9). The browser only maps the canvas onto a square plot. Two-way network arrows are flagged (`two_way`) and drawn as opposite curves (P4, display only). PCA is a plain scatter (P5). No new bar charts (P6). Tooltips, legend toggle, zoom/pan without dragging, and PNG (2400×1800, 300 dpi `pHYs`) and SVG downloads are produced in the browser (P7, P8). The frontend plan adds component and bundle-budget details.

The web draws charts with one themed base component, `EChart` (client only, lazily imported, init/dispose, resize observer, aria description, reset and download), plus `DirectedNetworkChart` and `ScatterChart` in `apps/web/src/components/general/charts/`. They are built from pure option builders over the API's chart data, with no maths in the browser. ECharts is tree-shaken through `echarts/core` (graph and scatter charts, grid, tooltip, legend, data zoom, mark line, title, aria, canvas and SVG renderers); the lazy chart chunk is 207,088 bytes gzip, under the 250 KB budget. Chart chrome is read from the theme CSS variables and series colours come from `/scales`. Downloads are made in the browser: PNG 2400×1800 (800×600 at pixel ratio 3) with a 300 dpi `pHYs` chunk, and SVG from the SVG renderer. Both edges of a two-way pair use the same curveness (+0.2), because ECharts bends each edge relative to its own direction, so they bulge to opposite sides.

## Context

The legacy app draws exactly two plots on a Tk canvas, the PCA scatter and the network graph (`pca_tab.py:416-506`, `network_tab.py:890-1165`), and exports them by screen grab. Owner decision of 2026-11-18, based on `docs/research/2026-11-18-browser-chart-libraries-research.md`.

## Alternatives Considered

- **Server-rendered PNGs (matplotlib):** heavy images, no interactivity, fonts and dpi rules in the API.
- **Layouts computed in the browser:** would put maths in the browser and break layout parity.

## Consequences

- Layout positions are tested against legacy fixtures at `atol=1e-6` px; the spectral layout uses the L16 sign rule.
- The browser never computes values; it formats numbers like Python's `format` without re-rounding.

## Related Work

- Plan: [Port The Policy Coherence Kit Backend To A Dockerised FastAPI `apps/api`](../plans/2026-11-18-port-backend-to-fastapi-api-plan.md)
- Plan: [Rebuild The UI In TanStack Start](../plans/2026-11-18-rebuild-ui-in-tanstack-start-plan.md)
- Conventions source: DEMATELab's decision records of 16 November, 2026 (`dematelab/docs/decisions/`)
