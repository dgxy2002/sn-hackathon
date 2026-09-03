# Integrated Runtime and Browser Acceptance - 2026-08-28

## Scope

This record accepts specific local fixture/runtime slices spanning E01, E03-E08,
and E10-E12; it does not close those epics. The accepted slices are the synthetic
decision path, local PostgreSQL evidence, neutral synthetic evidence comparison,
the bounded fixture invocation path, an idle singleton scraper lease, and
confirmed budget summary revisions. E04 extraction remains simulated, no
insurance source is approved for E05 fetching, and live OpenRouter orchestration
is not exercised. This record does not approve real-product comparison or
ranking, the draft E07 formulation, source reuse, or production use.

**Subsequent status (3 September 2026):** E11 explanation was reassigned from
OpenRouter to required Amazon Bedrock. A typed, mocked Converse integration is
now implemented; this dated record still accurately reports that no live model
call occurred during the 28 August acceptance.

| Field | Value |
|---|---|
| Evaluator | Tim implementation pass using pytest, Docker Compose, API checks, and Playwright |
| Repository revision | `90aab4b0bbd3ace43d24e562eb2aa9ca7c60ac90` |
| Contract version | `1.0.0` |
| Frontend | Vite 8.2.2 production build behind unprivileged Nginx |
| Backend | FastAPI on Python 3.11 |
| Evidence adapter | Local PostgreSQL, mode `cached` |
| Extraction and decision modes | `simulated` extraction; `synthetic` decision catalogue |
| Model, tokens, and cost | Not applicable; OpenRouter was not configured and no model call occurred |

## Automated checks

| Check | Observed outcome |
|---|---|
| Backend suite | `38 passed` with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` |
| Frontend build | `npm --prefix frontend run build` completed successfully |
| Repository verification | `scripts/verify-poc.sh` exited successfully |
| Compose deployment | Web, backend, scraper, and PostgreSQL were running and healthy |
| API health | Database reported `ready`/`live`; object store and OpenRouter reported `not_configured`/`simulated` |
| PostgreSQL evidence | `evidence_records` contained 1,777 rows |
| Real-product comparison gate | Configured cached products returned `EVIDENCE_COMPARISON_NOT_ELIGIBLE` with machine-readable source, evidence, freshness, URL, version, and mixed-category reasons |

## Browser acceptance

Playwright exercised the rebuilt Compose application at
`http://127.0.0.1:4180/` through the same-origin API proxy.

| Scenario | Observed outcome |
|---|---|
| Policy supplied | Synthetic fixture submission, extraction review, invocation, and recommendation completed through the API |
| No policy | Extraction was skipped and the page rendered the no-policy recommendation without fabricated existing cover |
| Decision result | Backend gaps, eligible-plan ordering, scores, assumptions, exclusions, ruleset version, and evidence IDs rendered on the comparison page |
| Neutral evidence mode | Two labelled synthetic critical-illness fixtures rendered without rank, fit, or suitability signals and remained separate from E07 ranking |
| Profile proposal | A budget change displayed `180 -> 100` and required confirmation before mutation |
| Confirmation | One immutable revision reran E07 and updated the visible budget to `$100`; the ranking stayed coherent |
| Cancellation | A second proposal was cancelled and did not change the active revision |
| Replay | Nine ordered events showed creation, proposals, resolution, confirmation, rerun, revision, and cancellation |
| Undo | The prior coherent profile and recommendation were restored; replay added `revision undone` and the visible budget returned to `$180` |
| Mobile | At 390 by 844, document and body widths remained 390 pixels and neutral comparison cards stacked in one column |
| Browser errors | No console or page errors occurred during the successful policy and no-policy paths |

## Accepted boundaries

- Browser-authored actions are mapped to typed local handlers. Server or model
  output is rendered as escaped text and cannot execute markup, selectors, SQL,
  arbitrary URLs, coordinates, or canonical decision values.
- The synthetic fixture comparison uses the same versioned comparison response
  shape as configured evidence, but is explicitly selected and labelled
  `synthetic_fixture`.
- Configured cached evidence remains searchable only. No current cached product
  is comparison eligible or ranking eligible.
- The scraper owns one database lease and remains healthy while waiting. It does
  not fetch because no insurance source has an approved reuse decision.

## Unmet gates

- Source permission, authoritative URLs, complete field provenance, freshness,
  and product-identity review are not approved for a real Phase 3B subset.
- The E07 formulation remains draft and has no named independent reviewer,
  approval date, or 20-profile evaluation.
- OpenRouter extraction selection and credentials plus credentialed Bedrock
  explanation evaluation, cost, and latency measurements remain unavailable.
- Conversational canonical mutation currently supports budget changes only;
  goal, dependant, preference, declared-cover, and extraction corrections remain
  unimplemented.
- The scraper lifecycle is operational, but no approved insurance source has
  passed fetch, normalize, version, and freshness processing.
- Object storage, AWS deployment, E09 security/regulatory acceptance, target-user
  research, and the recorded five-minute demo remain pending.

## Reproduction

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=backend \
  backend/.venv/bin/python -m pytest backend/tests -q
npm --prefix frontend run build
bash scripts/verify-poc.sh
API_PORT=8012 WEB_PORT=4180 docker compose up -d --build
```

Open `http://127.0.0.1:4180/`. The backend health endpoint is available at
`http://127.0.0.1:8012/health`.