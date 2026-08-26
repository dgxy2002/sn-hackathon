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
| [E01 - POC Web Experience](E01-poc-web-experience.md) | Tim | P0 | In progress | 5 |
| [E02 - Readiness Quiz and Peer Benchmark](E02-readiness-quiz-and-peer-benchmark.md) | Jana | P0 | In progress | 5 |
| [E03 - User Profile and Personalization](E03-user-profile-and-personalization.md) | Jana | P1 | In progress | 7 |
| [E04 - Policy OCR and Extraction](E04-policy-ocr-and-extraction.md) | Tim | P1 | In progress | 6 |
| [E05 - Source Data Ingestion POC](E05-source-data-ingestion-poc.md) | Darren | P1 | In progress | 6 |
| [E06 - Insurance Retrieval and RAG](E06-insurance-retrieval-and-rag.md) | Darren | P1 | Planned | 8 |
| [E07 - Explainable Decision Support](E07-explainable-decision-support.md) | Deborah | P0 | In progress | 7 |
| [E08 - Integrated Demo and Evaluation](E08-integrated-demo-and-evaluation.md) | Tim | P0 | In progress | 9 |
| [E09 - Productionisation and Security](E09-productionisation-and-security.md) | Tim | P3 | Deferred | 4 |
| [E10 - Backend API and POC Persistence](E10-backend-api-and-poc-persistence.md) | Tim | P0 | Planned | 8 |
| [E11 - Runtime Orchestration and Operations](E11-runtime-orchestration-and-operations.md) | Jana | P0 | Planned | 8 |
| [E12 - Conversational Summary Agent](E12-conversational-summary-agent.md) | Tim | P1 | Planned | 5 |

## Execution order

1. Freeze E03 profile semantics, the no-policy state, and E10 shared contracts.
2. Approve the E07 grounded formulation before implementing deterministic ranking.
3. Build E10 Docker Compose, `.env`, PostgreSQL/pgvector, and object-store foundations.
4. Deliver E04 OpenRouter extraction, E05 continuous scraping, and E06 local retrieval behind E10 contracts.
5. Complete E11 runtime-neutral orchestration, scraper operations, and bounded run events.
6. Accept the local stack, verify AWS migration mappings, measure, rehearse, and record E08.
7. Deliver E12 after the profile, extraction, retrieval, decision, API, and orchestration contracts support safe dynamic revisions.
8. Keep E09 deferred except for baseline safeguards that prevent secret exposure, real-data use, or misleading claims.

## Backlog maintenance rules

1. Ticket IDs are stable and use `E##-T##`.
2. A ticket cannot be Done without checked acceptance criteria and repository or test evidence.
3. Requirement changes begin in the URS or PRD, then flow to epics and tickets.
4. New cross-component work belongs in E08 unless it changes the responsibility of a capability epic.
5. Status and scope must not imply production readiness while E09 is deferred.