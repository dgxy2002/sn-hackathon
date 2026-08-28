# Fixture Agent Smoke Test - 2026-08-26

## Scope

This record covers the first fixture-only E10/E12 vertical slice. It does not
measure OpenRouter, retrieval, deterministic recommendation quality, summary
revisions, Docker Compose, or production readiness.

| Field | Value |
|---|---|
| Run time | 2026-08-26T10:37:27Z |
| Evaluator | Tim implementation pass, executed through automated tests and browser inspection |
| Backend | FastAPI 0.141.1, Python 3.11 |
| Frontend | Vite 8.2.2, Node.js 22.22.2 |
| Contract version | 1.0.0 |
| Policy fixture version | 1.0.0 |
| Agent mode | Simulated typed-action fixture |
| Model, prompt, tokens, cost | Not applicable; no model call occurred |

## Executable checks

Run from the repository root:

```bash
bash scripts/verify-poc.sh
```

The run passed 10 backend tests and the frontend production build. The tests
cover system manifests, safe configuration, labelled extraction fixtures,
grounded Q&A, presentation filtering, duplicate-message replay, blocked
decision-input changes, and stale-revision conflicts.

## Browser scenario

The browser was driven from landing through quiz, demo account, five onboarding
steps, synthetic policy review, and final comparison against the live local
fixture API.

| Scenario | Expected outcome | Observed outcome |
|---|---|---|
| Explain ranking | Focus the ranking drawer and retain summary revision | Completed; `ranking-reason` opened and received focus |
| Filter critical illness | Hide unrelated plan columns without changing ranking | Completed; only label and critical-illness columns remained visible, with a reset control |
| Change budget | Require confirmation and deterministic rerun; do not mutate when dependencies are absent | Stopped with `DEPENDENCY_UNAVAILABLE`; comparison remained filtered and otherwise unchanged |
| Mobile layout | Preserve controls and avoid horizontal overflow at 390 x 844 | Passed; agent section `scrollWidth` equalled `clientWidth` at 375 CSS pixels |

The visible trace showed tool, target, status, evidence count, confirmation
boundary, affected regions, and safe error code. Citation links were selected
from a frontend evidence-ID allowlist rather than trusted from response URLs.

## Unmet coverage

- E03 profile versions, E06 approved-catalogue search, E07 deterministic reruns,
  and E11 orchestration are not implemented.
- Confirmation, proposal application, coherent revision, replay, and undo paths
  remain unimplemented and are not claimed as passing.
- The exact `OPENROUTER_MODEL` decision is unresolved; no model quality, latency,
  token, or cost result exists.
- Docker Compose, PostgreSQL/pgvector, object storage, continuous scraping, and
  AWS image promotion remain pending.
- This result uses synthetic fixtures only and is not financial advice or a
  production-security assessment.