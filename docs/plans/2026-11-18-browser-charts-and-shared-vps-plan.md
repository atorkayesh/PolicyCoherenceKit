# Draw Policy Coherence Kit's Charts In The Browser And Prepare For A Shared VPS Behind One Reverse Proxy

**Date:** 18 November, 2026 (created 18:33 CET; last modified 18 November, 2026, 19:50 CET: Part A moved into the
port plans for PCK by the owner decision of 2026-11-18)
**Status:** Draft (Part B only: blocked on the port landing and on owner decisions D6-D12; Part A is no longer
part of this plan, see below)
**Owner:** Youpele Michael (plan written by Claude Code)

## Summary

Two independent parts, both **after** the initial port to `apps/api` (FastAPI) and `apps/web` (TanStack Start):

- **Part A, browser charts: moved (2026-11-18).** By owner decision, Policy Coherence Kit's charts are drawn in the
  browser with Apache ECharts **in the initial port**, not in a follow-up. Phases A0–A3 and decisions P1–P9 (all
  adopted as recommended here, P2 = (b): no matplotlib at all) now live in
  `docs/plans/2026-11-18-port-backend-to-fastapi-api-plan.md` (Settled Decision 7, `NetworkChartData`, decision record
  `browser-charts-with-echarts`) and `docs/plans/2026-11-18-rebuild-ui-in-tanstack-start-plan.md` (Settled Decision 8,
  `components/general/charts/`, Phase 6). Part A text below is kept only as a pointer; implement from the port plans.
- **Part B, shared VPS.** Make PCK's production stack ready to sit behind one shared, Dockerised edge reverse
  proxy that also serves DEMATELab and possibly ice2kg, instead of publishing its own Nginx on `8081`. The edge
  proxy lives in a new small infrastructure repository.

User impact of Part B: HTTPS on a host name, with no public port of PCK's own.

## Related Work

- **Depends on (must land first):** `docs/plans/2026-11-18-port-backend-to-fastapi-api-plan.md` and
  `docs/plans/2026-11-18-rebuild-ui-in-tanstack-start-plan.md` (revision 3, which now contain PCK's browser charts).
- Research: [Which browser chart library could replace the server-rendered matplotlib charts?](../research/2026-11-18-browser-chart-libraries-research.md)
- Research: [How can DEMATELab, PCK and ice2kg share one VPS behind one Dockerised reverse proxy?](../research/2026-11-18-shared-vps-and-nginx-research.md)
- Report: [Tk app UI inventory](../reports/2026-11-18-tk-app-ui-inventory-report.md) (network and PCA tabs,
  exports, defects 2 and 17)
- Report: [Tk app logic inventory](../reports/2026-11-18-tk-app-logic-inventory-report.md) (layouts, PCA,
  centrality, plots and image export, Excel export)
- Report: [DEMATELab conventions inventory](../reports/2026-11-18-dematelab-conventions-inventory-report.md)
  (ports 3001/50002, Nginx 8081 proposal, files to copy)
- Sibling plan: `docs/plans/2026-11-18-browser-charts-and-shared-vps-plan.md` in the DEMATELab repository
  (`dematelab`); decisions D6-D11 are shared and should be answered once for both.
- Decisions: none yet in `docs/decisions/` (only the authoring guide); the port plans are expected to add the
  DEMATELab-equivalent decisions (Compose with Nginx as the only public entry, stateless API, …).
- Issue or merge request: none identified; see Open Questions.

## Problem

- (Part A problems, screen-grab exports, overlapping two-way arrows and static charts, are solved by the port
  plans' browser charts.)
- PCK will share a VPS with DEMATELab (and possibly ice2kg). Each stack ships its own public Nginx; the
  conventions report proposes `${HTTP_PORT:-8081}` only to avoid the port-80 clash, and HTTPS is not set up.

## Goals

- A1–A4: moved into the port plans (see Summary).
- B1. PCK runs behind the shared edge at `https://<pck host>/`, publishes no public port of its own, and still
  runs standalone with `make prod` on a developer machine.

## Non-Goals

- Any chart work (Part A moved to the port plans).
- Part B does not create the infrastructure repository, change DEMATELab or ice2kg, or touch the VPS.
- `tk-app/` stays read-only; `apps/` never imports from it (plan guide rules).

## Current State

Plan validity: written against branch `restructure/apps-api-web` at `00b610a`, with the uncommitted move of the
legacy app into `tk-app/` and of the example workbook into `data/examples/`, plus untracked `docs/`. `apps/` does
not exist yet. **Every `apps/...` path below is the expected path from the DEMATELab conventions report;
confirm it against the two port plans before implementing.**

### Legacy charts

Moved with Part A: the legacy chart reference now lives in the port plans (backend Phase 5 and API Contract, frontend
Parity Inventory and Phase 6).

### Expected state after the port (to confirm)

- API (FastAPI, stateless, port 50002) with ported `compute_*` functions and parity fixtures from `tk-app/`;
  no matplotlib; chart data from `POST /api/v1/analysis/charts/network` and `AnalysisData.pca`; charts drawn in the
  browser with ECharts (port plans, revision 3).
- Web (TanStack Start, port 3001) with result tabs Insights, Aggregated matrix, Coherence scores, Range of
  influence, PCA, Network, AI interpretation, and an export bar (UI inventory, web mapping row R).
- Prod: `docker-compose-prod.yml` with `policycoherencekit-nginx` on `${HTTP_PORT:-8081}:80`, upstreams
  `web:3001`, `api:50002`; `nginx/nginx.prod.conf` copied from DEMATELab with a commented HTTPS block; `make prod`
  without network setup (conventions report, Findings 8-9).

## Owner Decisions

| # | Decision | Options | Recommendation | Blocks |
|---|---|---|---|---|
| P1-P9 | Browser charts (library, interim matplotlib, layouts, two-way arrows, PCA, bar charts, downloads, interactivity, aspect) | Settled by the owner (2026-11-18) | **Adopted as recommended and moved into the port plans** (backend Settled Decision 7, frontend Settled Decision 8). P2 = (b): no matplotlib in PCK. | — |
| D6-D11 | VPS, routing, proxy technology, edge repository, certificates, rootless Podman ports | See the DEMATELab plan's table (same numbers) | Same recommendations: `metadb` if permitted, host names, static Nginx edge, new infra repository, Let's Encrypt via certbot, lower `ip_unprivileged_port_start` to 80. Decide once for both repositories. | B0-B3 |
| D12 | PCK Nginx publishing on the VPS, deploy downtime | `127.0.0.1:${HTTP_PORT:-8081}`; publish nothing; public `${HTTP_PORT:-8081}` | **Loopback `127.0.0.1:${HTTP_PORT:-8081}`** (keeps the 8081 default from the conventions report, but not public); accept a few seconds of 503 during deploys. | B2 |

## Phases

### Part A: Browser charts (moved)

Moved into the port plans on 2026-11-18 (see Summary). Former phases map as: A0 decision record → backend Phase 9
`browser-charts-with-echarts`; A1 chart-data endpoints → backend Phase 5 (`NetworkChartData`, `AnalysisData.pca`);
A2 web charts and A3 browser downloads → frontend Phase 6 (`components/general/charts/`); A4 is void (no matplotlib
is ever added).

### Part B: Shared VPS and shared edge proxy

#### Phase B0: Prerequisites (owner and VPS administrator)

Same as the DEMATELab plan, Phase B0, done once for all apps: DNS names, firewall 80/443, the rootless Podman
port setting (D11), permission from the hosting institution.

#### Phase B1: Edge proxy repository (outside PCK)

Same as the DEMATELab plan, Phase B1. PCK's host file: `server_name <pck host>`; upstream
`http://policycoherencekit-nginx:80` resolved per request; `client_max_body_size` matching PCK's Nginx (20m
unless the port plan sizes it differently); `proxy_read_timeout 300s` and `proxy_buffering off` on `/api/` (the
AI call has a 120 s timeout, `tk-app/llm_tab.py:220`).

#### Phase B2: Make PCK edge-ready

Depends on the port plans' Compose, Nginx and Makefile files existing, D7 and D12. Ideally folded into the port
plans while those files are created, so they change once.

1. `docker-compose-prod.yml`: `nginx` `ports` → `"127.0.0.1:${HTTP_PORT:-8081}:80"`; external network `edge`
   on the `nginx` service only; `web`/`api` on PCK's own network only; Nginx healthcheck on `/healthz`.
2. `nginx/nginx.prod.conf`: `location = /healthz`; keep the edge's `X-Forwarded-Proto` (map with `$scheme`
   fallback); `set_real_ip_from` the edge subnet; drop the commented HTTPS block (TLS at the edge).
3. `Makefile`: `_edge-network` helper (create when missing) before `prod`; local URL `http://localhost:8081`;
   port check for `HTTP_PORT`.
4. Docs: decision `docs/decisions/2026-11-xx-shared-edge-proxy-on-a-shared-vps.md` (or amend the port's
   "Nginx as only public entry" decision); `AGENTS.md`, `README.md`, `apps/api/.env.example`
   (`CORS_ORIGINS=https://<pck host>` on the VPS).

Exit: `make prod` locally serves at `http://localhost:8081`; through a local edge,
`curl -H "Host: pck.localhost" http://localhost/api/v1/health` returns 200.

#### Phase B3: Cutover on the VPS

Same order and rollback as the DEMATELab plan, Phase B3. PCK is stateless: rollback is reverting B2 and
`make prod` with a public `HTTP_PORT`. If PCK is first deployed after the edge exists, it simply joins: deploy,
add `conf.d/pck.conf` and its certificate in the edge repository, `make reload`.

## Risks And Decision Gates

- **Port not landed**: B2 does not start before the two port plans are merged.
- **Edge single point of failure**, **header trust**,
  **rootless Podman ports and client IPs**: as in the DEMATELab plan's Risks.

## Testing And Validation

- Part A: see the port plans' Testing And Validation.
- Part B: as in the DEMATELab plan (compose config, local two-proxy check with `pck.localhost`, VPS checks of
  HTTPS, health, body size limit, AI call completion, forwarded proto, 503 page, renewal dry run).

## Acceptance Criteria

- Part A: see the port plans' Acceptance Criteria.
- `make check` passes after every phase.
- PCK serves at `https://<pck host>/` through the edge with no public port of its own; `make prod` still works
  standalone at `http://localhost:8081`.

## Open Questions

- D6-D12 above (D6-D11 shared with DEMATELab). P1-P9 are settled (2026-11-18).
- When will the two port plans be written and merged, and does the UI plan already define the network and PCA
  components this plan should extend?
- Is there a JuGit issue to link?
- Host name for PCK (placeholder `pck.<domain>`)?
- Should the legacy `tk-app` noVNC stack ever be served on the shared VPS (it is loopback-only by default,
  `tk-app/docker-compose-prod.yml:17-18`)?
