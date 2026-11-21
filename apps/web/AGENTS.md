# Policy Coherence Kit web app (`apps/web`)

## Stack and commands
- TanStack Start (React 19, file routes, Vite, Nitro), TypeScript strict, pnpm 12 (Node 24), Biome,
  Vitest + Testing Library (jsdom), shadcn on Base UI (`base-nova`), Tailwind v4, Zustand, Zod,
  TanStack Query, `@tanstack/react-virtual`, Apache ECharts 6.1.0 (exact pin).
- Dev server on port **3001** (`pnpm run dev`, `--strictPort`); API on **50002**
  (`VITE_API_BASE_URL=http://localhost:50002` in dev, empty in production behind Nginx).
- Checks: `pnpm run format:check && pnpm run lint && pnpm run typecheck && pnpm run test && pnpm run build`
  (Docker: `just check-web`). Never edit `src/routeTree.gen.ts` by hand (`pnpm run generate-routes`).
- Versions are pinned by `pnpm-lock.yaml`; do not upgrade as a side effect.

## File organisation
- `src/routes/` (`__root.tsx`, `index.tsx` = the flow, `status.tsx`), `components/ui` (shadcn, copied),
  `components/general` (layout, `InlineError`, `DownloadButton`, `SectionCard`, `charts/`),
  `components/page-specific/assessment` (flow, steps, results), `components/page-specific/status`.
- `constants/` holds only UI text the API does not provide (titles, help, labels, file names, column
  headers, tooltips) and token maps. `interfaces/` are Zod schemas of the API contract. `services/` call
  one endpoint each; `hooks/` wrap them in TanStack Query; `utils/` are pure helpers; `store/` is the
  Zustand project store; `test/` has fixtures and helpers.
- Every code file has at most 300 lines and no file mentions the legacy app directory: enforced by
  `src/test/repository-rules.test.ts`. Cite legacy sources without the directory prefix (`app.py:1170`).
- Tests are co-located `*.test.ts(x)`.

## Architecture
- **No policy-coherence maths in the browser.** Ratings, methods, rules, limits, colours and layouts
  come from `GET /scales`; validation (`/setup/validate`), completeness and method availability
  (`/matrices/check`), weight parsing and the live sum (`/weights/check`), ties
  (`/aggregation/preview`), every analysis value, chart positions and texts come from the API. The
  browser only formats numbers and counts filled cells for progress text.
- **Flow** (`utils/flow.utils.ts`, `FlowShell`): steps `project · decision-makers · policies · import ·
  matrix-1…k · review · method · [weights | median | ties] · results`. `questionSteps(state)` decides
  the optional step from the method and the stored `aggregationOptions` (valid only for the
  decision-maker names they were computed for). Opening a step with unanswered earlier steps redirects
  to the first unanswered one; `results` needs results. `?step=` is pushed, so browser history works.
  `StepFrame` handles Enter (continue, ignored in selects/buttons/links/textareas), Shift+Enter (back),
  focus and the slide-in animation. The last question step's OK reads `Run Analysis`.
- **Changing answers:** name steps are drafts until OK (validated, then committed). Decision-makers and
  policies have stable ids (`crypto.randomUUID()`); matrices, weight texts, parsed weights, tie choices
  and answered matrix steps are keyed by ids, so renames, reorders, removals and imports never move
  ratings. Removals that lose ratings ask first. Matrix cells, method, weights, median and tie choices
  are stored at once.
- **Store rule:** results, charts, exports and the AI request always use `snapshot` (the request of the
  last run), never the current answers. `ResultTabs`/`ExportBar` are keyed by `snapshotHash`.
  Changed answers show `OutdatedResultsBanner` with Re-run (`hooks/rerun.hook.ts`).
- **Matrix editor:** virtualised rows and columns (`MATRIX_GRID`), one store subscription per cell
  (`MatrixCell`), blank `--`, `Clear rating`/Delete/Backspace clear, diagonal disabled. Only the open
  matrix step is mounted.
- **Charts:** `components/general/charts/EChart` is the themed base (inside `ClientOnly`, the chunk
  loaded with dynamic `import("@/utils/echarts.utils")`, init/dispose, `ResizeObserver`, aria
  description, ref with `resetView`/`download`). `DirectedNetworkChart` and `ScatterChart` map API data
  to options through the pure builders `utils/network-chart.utils.ts` / `utils/pca-chart.utils.ts`.
  Chart chrome comes from the CSS variables (`utils/chart-theme.utils.ts`); series colours come from
  `/scales`. Downloads are rendered off-screen in the browser (`utils/chart-export.utils.ts`): PNG
  2400×1800 with a 300 dpi `pHYs` chunk, SVG from the SVG renderer. Both edges of a two-way pair use the
  same curveness (ECharts bends relative to the edge direction, so they separate). Never import
  `echarts` at module scope of a route; keep the chart chunk ≤ 250 KB gzip.
- **AI key rule:** the API key lives only in `ExplanationPanel` state, goes only into the request body
  (through a ref, never mutation variables or query keys) and is cleared after success and after
  failure. It is never stored, cached or logged.
- **Number formatting:** `utils/format.utils.ts` formats API numbers like Python at the same precision
  (`formatFixed`, `formatSigned`, `pyFloatStr`); `-0.0` stays `-0.00`. Never re-round.
- **API texts are shown verbatim**; arrows, wording and counts are fixed in the API.

## Theme
- The warm-white ice2kg tokens (unchanged base tokens) in `src/styles.css`, Manrope Variable. PCK domain tokens
  (`--rating-*`, `--value-*`, `--count-*`, `--entropy-*` with `-foreground`, `--role-*`, `--health-*`)
  are mapped from API keys in `constants/theme.constants.ts`.
- Every text/background pair must reach WCAG AA 4.5:1 (`src/test/theme-contrast.test.ts`); a failing
  pair may change lightness only (decision record `docs/decisions/2026-11-18-warm-white-variant-of-the-ice2kg-theme.md`).

## Environment
- `apps/web/.env` from `.env.example`: `VITE_APP_ENV`, `VITE_API_BASE_URL` (validated in `src/env.ts`).
  Values are public (bundled); never put secrets there.

## Testing
- Mock services with `vi.mock("@/services/…")` and the router as in `FlowShell.test.tsx`;
  `FlowHistory.test.tsx` uses a real memory router. `test/render.tsx` (`renderWithQuery`, `stubLayout`
  for virtualised grids), `test/select.ts` (`pickOption`), `test/project.ts` (`seedProject`),
  `test/fixtures/*` (contract-shaped data). Chart tests mock `@/utils/echarts.utils`; one test renders a
  real SVG with `ssr: true`.

## Pitfalls
- Do not compute scores, bands, ties, completeness or layouts in the browser.
- Do not read current answers in Results; use the snapshot.
- Do not key data by position; use ids.
- Do not persist answers (only the one-time refresh-notice flag in `sessionStorage`).
- Do not add a second chart library or server-rendered chart images.
