# Epic Register

This folder is the source of truth for CoverCheck SG epic ownership, priority, status, and definition of done (DOD). The project is currently a proof of concept (POC) for the IGNITE hackathon.

Epics implement the [User Requirements Specification](../urs/URS.md) and [Product Requirements Document](../prd/PRD.md). Executable work is maintained in the [backlog register](../backlog/README.md).

## Status vocabulary

- **Done:** The stated POC DOD is met in the repository. This does not imply production readiness.
- **In progress:** A usable slice or mock exists, but the epic DOD is not yet met.
- **Planned:** The epic is scoped but has no working implementation.
- **Deferred:** Deliberately outside the current POC critical path.

## Priority vocabulary

- **P0:** Required for the judged end-to-end POC.
- **P1:** Important capability; deliver the smallest demoable slice after P0.
- **P3:** Low priority until the POC is validated.

## Portfolio

| Epic | Primary owner | Priority | Status | Backlog | Current repository evidence |
|---|---|---:|---|---|---|
| [E01 - POC Web Experience](E01-poc-web-experience.md) | Tim | P0 | In progress | [Tickets](../backlog/E01-poc-web-experience.md) | Interactive Vite journey, typed agent, and cached-evidence disclosures exist; proposals, revisions, replay, and undo remain |
| [E02 - Readiness Quiz and Peer Benchmark](E02-readiness-quiz-and-peer-benchmark.md) | Jana | P0 | In progress | [Tickets](../backlog/E02-readiness-quiz-and-peer-benchmark.md) | Quiz and pilot benchmark work; full weighted IRS and user validation pending |
| [E03 - User Profile and Personalization](E03-user-profile-and-personalization.md) | Jana | P1 | In progress | [Tickets](../backlog/E03-user-profile-and-personalization.md) | Five-step onboarding and in-memory profile |
| [E04 - Policy OCR and Extraction](E04-policy-ocr-and-extraction.md) | Tim | P1 | In progress | [Tickets](../backlog/E04-policy-ocr-and-extraction.md) | Upload and extraction-result simulation |
| [E05 - Source Data Ingestion POC](E05-source-data-ingestion-poc.md) | Darren | P1 | In progress | [Tickets](../backlog/E05-source-data-ingestion-poc.md) | Credit-card scraper pattern exists; continuous insurance runtime is pending |
| [E06 - Insurance Retrieval and RAG](E06-insurance-retrieval-and-rag.md) | Darren | P1 | In progress | [Tickets](../backlog/E06-insurance-retrieval-and-rag.md) | Cached, synthetic, and Supabase adapters now expose one typed evidence API; source governance, local PostgreSQL parity, and fixed evaluation remain |
| [E07 - Explainable Decision Support](E07-explainable-decision-support.md) | Deborah | P0 | In progress | [Tickets](../backlog/E07-explainable-decision-support.md) | Gap calculations and static synthetic comparison |
| [E08 - Integrated Demo and Evaluation](E08-integrated-demo-and-evaluation.md) | Tim | P0 | In progress | [Tickets](../backlog/E08-integrated-demo-and-evaluation.md) | Containerized frontend/API and cached evidence exploration pass; complete Compose topology, orchestration, changed-goal flow, and measurements remain |
| [E09 - Productionisation and Security](E09-productionisation-and-security.md) | Tim | P3 | Deferred | [Tickets](../backlog/E09-productionisation-and-security.md) | Basic POC trust messaging and secret handling only |
| [E10 - Backend API and POC Persistence](E10-backend-api-and-poc-persistence.md) | Tim | P0 | In progress | [Tickets](../backlog/E10-backend-api-and-poc-persistence.md) | Containerized API, typed evidence adapters, manifests, conversation errors, and idempotent replay exist; remaining capability and persistence routes remain |
| [E11 - Runtime Orchestration and Operations](E11-runtime-orchestration-and-operations.md) | Jana | P0 | Planned | [Tickets](../backlog/E11-runtime-orchestration-and-operations.md) | Local/AWS runtime contract documented; coordinator and continuous scraper are not implemented |
| [E12 - Conversational Summary Agent](E12-conversational-summary-agent.md) | Tim | P1 | In progress | [Tickets](../backlog/E12-conversational-summary-agent.md) | Final-page agent, typed-action trace, cached catalogue search, and focus/filter actions exist; proposals, reruns, replay, and undo remain |

## Ownership rules

1. Each epic has one primary owner who is accountable for its DOD.
2. Contributors may help without becoming co-owners.
3. Status changes must include updated repository evidence.
4. A POC-complete epic can still have production follow-ups; those belong in E09 or a later roadmap.
5. Scope changes should update both the epic file and the summary table above.

## Current focus

Follow the approved [RAG and website integration decisions](../evaluation/2026-08-28-rag-website-integration-decisions.md): complete the direct read-only E10/E06 path and evidence-state rendering before E11 consequential orchestration. In parallel, complete the P0 deterministic foundations, Docker Compose target, and E08 acceptance while preserving the working E01-E02 demo. E09 remains deferred except for baseline safeguards that prevent secret exposure, real-data use, or misleading claims.