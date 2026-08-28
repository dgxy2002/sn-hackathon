# Backlog Register

This folder contains the executable backlog for the CoverCheck SG POC. Each ticket belongs to one epic, has one owner, and traces to the [URS](../urs/URS.md) and [PRD](../prd/PRD.md).

## Ticket status

- **Done:** Acceptance criteria are met and repository evidence is linked.
- **In progress:** Work has started but at least one acceptance criterion remains open.
- **Ready:** Scoped and available to start when dependencies permit.
- **Deferred:** Deliberately outside the current POC critical path.

## Ticket sizing

- **S:** Narrow change with one primary output.
- **M:** Multi-step change within one capability.
- **L:** Cross-component work that should be split further before implementation if it cannot fit the hackathon window.

## Backlog by epic

| Epic backlog | Owner | Epic priority | Epic status | Ticket count |
|---|---|---:|---|---:|
| [E01 - POC Web Experience](E01-poc-web-experience.md) | Tim | P0 | In progress | 6 |
| [E02 - Readiness Quiz and Peer Benchmark](E02-readiness-quiz-and-peer-benchmark.md) | Jana | P0 | In progress | 5 |
| [E03 - User Profile and Personalization](E03-user-profile-and-personalization.md) | Jana | P1 | In progress | 7 |
| [E04 - Policy OCR and Extraction](E04-policy-ocr-and-extraction.md) | Tim | P1 | In progress | 6 |
| [E05 - Source Data Ingestion POC](E05-source-data-ingestion-poc.md) | Darren | P1 | In progress | 6 |
| [E06 - Insurance Retrieval and RAG](E06-insurance-retrieval-and-rag.md) | Darren | P1 | In progress | 9 |
| [E07 - Explainable Decision Support](E07-explainable-decision-support.md) | Deborah | P0 | In progress | 8 |
| [E08 - Integrated Demo and Evaluation](E08-integrated-demo-and-evaluation.md) | Tim | P0 | In progress | 11 |
| [E09 - Productionisation and Security](E09-productionisation-and-security.md) | Tim | P3 | Deferred | 5 |
| [E10 - Backend API and POC Persistence](E10-backend-api-and-poc-persistence.md) | Tim | P0 | In progress | 9 |
| [E11 - Runtime Orchestration and Operations](E11-runtime-orchestration-and-operations.md) | Jana | P0 | In progress | 8 |
| [E12 - Conversational Summary Agent](E12-conversational-summary-agent.md) | Tim | P1 | In progress | 6 |

## Execution order

Current checkpoint: direct E10/E06 retrieval, local PostgreSQL, the bounded fixture coordinator, the singleton scraper lease, and the budget proposal/revision path are implemented. The numbered sequence remains the dependency plan; source governance, real Phase 3B acceptance, live OpenRouter work, full evaluation, AWS, and E09 remain open.

1. Freeze E03 profile semantics, the no-policy state, and E10 shared contracts.
2. Approve the E07 grounded formulation before implementing deterministic ranking.
3. Build E10 Docker Compose, `.env`, PostgreSQL/pgvector, and object-store foundations.
4. Deliver E04 OpenRouter extraction, E05 continuous scraping, and E06 local retrieval behind E10 contracts.
5. Deliver Phase 3B through E06-T09, E10-T09, E01-T06, E12-T06, and E08-T10 as a read-only comparison slice that does not depend on E11.
6. Complete E11 runtime-neutral orchestration, scraper operations, and bounded run events.
7. Accept the local stack, verify AWS migration mappings, measure, rehearse, and record E08.
8. Deliver the remaining consequential E12 revision flow after profile, extraction, decision, API, and orchestration contracts support it.
9. Begin the internal Phase 6 ranked pilot only after E07-T08's dependencies and DEC-004/compliance approval pass; evaluate it through E08-T11.
10. Keep E09 deferred except for baseline safeguards; E09-T05 remains mandatory before public real-product ranked mode.

## Approved E06 website integration order

The [28 August RAG and website integration decision](../evaluation/2026-08-28-rag-website-integration-decisions.md) adds this delivery sequence without changing the local-first target in `docs/PLAN.md`:

1. Freeze the E06 evidence, evidence-state, and distinct date-field contract; correct source identity and enrich brochure metadata.
2. Wrap the existing Supabase retrieval path and a deterministic fixture fallback behind one E06 service interface.
3. Expose the read-only service through E10 and verify adapter parity, typed errors, timeouts, and credential boundaries.
4. Render broad cached-catalogue questions and exploration through E01/E12 without changing E07 synthetic ranking.
5. Build and accept Phase 3B for a small comparison-eligible subset through E06-T09, E10-T09, E01-T06, E12-T06, and E08-T10.
6. Evaluate grounding, top-five retrieval, citation/date coverage, stale/no-evidence behavior, and the read-only recommendation boundary through E08.
7. Complete local PostgreSQL/pgvector and Docker Compose parity before claiming the approved local runtime target.
8. Use E11 for consequential proposals, confirmations, deterministic reruns, revisions, replay, and undo.
9. After Phase 5 acceptance, use E07-T08 and E08-T11 for the separately approved Phase 6 internal ranked pilot; do not expose it publicly before E09-T05.

## Backlog maintenance rules

1. Ticket IDs are stable and use `E##-T##`.
2. A ticket cannot be Done without checked acceptance criteria and repository or test evidence.
3. Requirement changes begin in the URS or PRD, then flow to epics and tickets.
4. New cross-component work belongs in E08 unless it changes the responsibility of a capability epic.
5. Status and scope must not imply production readiness while E09 is deferred.