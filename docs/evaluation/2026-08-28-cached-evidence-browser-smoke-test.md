# Cached Evidence Browser Smoke Test - 2026-08-28

## Scope

This record covers the direct E10/E06 read-only evidence path, its E12 browser
rendering, and the containerized web/API path. It does not accept local database
retrieval, source permissions, recommendation quality, OpenRouter, revisions,
or the complete E08 Docker topology.

| Field | Value |
|---|---|
| Evaluator | Tim implementation pass, executed through API checks and browser automation |
| Contract version | 1.0.0 |
| Evidence adapter | `cached` local corpus |
| Corpus | 79 brochures, 87 extracted rows, 71 normalized policy slugs |
| Frontend | Vite 8.2.2 production build behind unprivileged Nginx |
| Backend | FastAPI on Python 3.11, non-root container user |
| Model, prompt, tokens, cost | Not applicable; no model call occurred |

## Observed checks

| Check | Observed outcome |
|---|---|
| Direct evidence search | `POST /v1/evidence/search` returned `matched`, mode `cached`, and three non-synthetic records for `critical illness protection` |
| Container health | Web and backend became healthy; PostgreSQL became healthy with the `vector` extension installed |
| Database boundary | Backend health reported database `not_configured`; cached evidence did not claim PostgreSQL retrieval |
| Browser API path | Conversation creation returned 201 and the evidence message returned 200 through the same-origin `/api` proxy |
| Evidence rendering | Five cached records rendered with provider, product, quoted span, evidence state, freshness, brochure as-of date, product-effective date, and cached source file |
| Unknown data | Missing dates rendered as `Unknown`; stale and unverified records remained visibly labelled |
| Ranking boundary | LionCity Term Flex, Harbour Essential CI, and Orchid Income Shield remained unchanged after cached exploration |
| Browser errors | No console errors occurred during the successful containerized evidence request |
| Responsive layout | The evidence panel rendered at 390 by 844 without page-level horizontal overflow |

## Reproduction

```bash
cp .env.example .env
docker compose up --build -d
```

Open `http://localhost:4173`, complete the synthetic journey, then choose
`Explore cached CI plans`. The direct API remains available at
`http://localhost:8000/health`.

## Unmet coverage

This section records the state at the time of this smoke test. The later
[integrated runtime and browser acceptance](2026-08-28-integrated-runtime-browser-acceptance.md)
closes PostgreSQL retrieval, complete Compose topology, and revision-flow items
listed below; source approval and live-provider gates remain open.

- Source approval, authoritative URLs, effective dates, premiums, eligibility,
  exclusions, and source-permission review remain incomplete across the corpus.
- The PostgreSQL container does not yet store or retrieve evidence; the API uses
  the committed JSONL and Markdown corpus.
- Supabase browser parity, local PostgreSQL adapter parity, fixed top-five
  retrieval evaluation, and continuous scraper operation were not tested.
- OpenRouter extraction and explanation, changed-goal reruns, proposals,
  confirmation, revision history, replay, and undo remain pending.
- The Compose stack is a working web/API slice, not acceptance of the complete
  E08 topology or a production deployment.