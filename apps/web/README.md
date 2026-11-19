# Policy Coherence Kit Web

TanStack Start frontend for Policy Coherence Kit. It replaces the Tkinter desktop window (kept for
reference, read-only) with a web app; every number, label, limit and validation result comes from the
API in `apps/api`.

The home page (`/`) asks one question per screen (Typeform style): project name (or start from an Excel
workbook), decision-makers, policies, an optional Excel import, one rating matrix per decision-maker,
a review, the aggregation method, then weights, the median choice or tie resolution where they apply.
Results open full width with seven tabs (Results Insights, Aggregated, Coherence Scores, Range of
Influence, PCA, Network Analysis, AI Interpretation) and an export bar. The PCA scatter and the network
graph are drawn in the browser with Apache ECharts from the API's chart data. Browser Back/Forward move
between steps (`?step=`); earlier answers can be changed and results then show an "out of date" banner
with Re-run. The API health is at `/status` (not linked).

Nothing is saved: a reload starts a new assessment.

The logo is the legacy sidebar badge (Lucide "waypoints" on a `#1f2937` square), drawn by `AppHeader`
with `lucide-react` and shipped as `public/favicon.svg`. There is no PNG logo: the only legacy bitmap is
64×64 and would blur.

Agent and coding guidelines: [`AGENTS.md`](./AGENTS.md).

## Run with Docker (recommended)

From the repository root:

```bash
make setup    # creates apps/web/.env and apps/api/.env from their examples
make dev
```

The web app runs at `http://localhost:3001` with hot reload, the API at `http://localhost:50002`.
See the root [`README.md`](../../README.md).

## Run locally

Requires Node.js 24 and pnpm 12, and a running API (see [`apps/api/README.md`](../api/README.md)).

```bash
cd apps/web
cp .env.example .env
pnpm install --frozen-lockfile
pnpm run dev          # http://localhost:3001
```

## Checks

```bash
pnpm run format:check && pnpm run lint && pnpm run typecheck && pnpm run test && pnpm run build
```

In Docker: `make check-web` from the repository root.

## Environment

| Variable | Development | Production |
| --- | --- | --- |
| `VITE_APP_ENV` | `development` | `production` |
| `VITE_API_BASE_URL` | `http://localhost:50002` | empty (same origin through Nginx) |

`VITE_*` values end up in the browser bundle: never put secrets in `apps/web/.env`.
