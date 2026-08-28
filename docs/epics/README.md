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
| [E01 - POC Web Experience](E01-poc-web-experience.md) | Tim | P0 | In progress | [Tickets](../backlog/E01-poc-web-experience.md) | API-backed journey, typed proposals, revisions, replay, undo, and synthetic neutral comparison work; real Phase 3B remains gated |
| [E02 - Readiness Quiz and Peer Benchmark](E02-readiness-quiz-and-peer-benchmark.md) | Jana | P0 | In progress | [Tickets](../backlog/E02-readiness-quiz-and-peer-benchmark.md) | Quiz and pilot benchmark work; full weighted IRS and user validation pending |
| [E03 - User Profile and Personalization](E03-user-profile-and-personalization.md) | Jana | P1 | In progress | [Tickets](../backlog/E03-user-profile-and-personalization.md) | Versioned API profile, no-policy path, focused missing fields, and confirmed budget patches work; full FNA and other patch types remain |
| [E04 - Policy OCR and Extraction](E04-policy-ocr-and-extraction.md) | Tim | P1 | In progress | [Tickets](../backlog/E04-policy-ocr-and-extraction.md) | Labelled fixture extraction and review work; OpenRouter and user-applied correction remain gated |
| [E05 - Source Data Ingestion POC](E05-source-data-ingestion-poc.md) | Darren | P1 | In progress | [Tickets](../backlog/E05-source-data-ingestion-poc.md) | Continuous singleton worker and database lease work; approved insurance-source fetching remains blocked |
| [E06 - Insurance Retrieval and RAG](E06-insurance-retrieval-and-rag.md) | Darren | P1 | In progress | [Tickets](../backlog/E06-insurance-retrieval-and-rag.md) | Typed PostgreSQL evidence API and comparison gates work; source approval, real pilot projection, and fixed evaluation remain |
| [E07 - Explainable Decision Support](E07-explainable-decision-support.md) | Deborah | P0 | In progress | [Tickets](../backlog/E07-explainable-decision-support.md) | Deterministic data-driven synthetic decisions and coherent reruns work; formulation approval and 20-profile evaluation remain |
| [E08 - Integrated Demo and Evaluation](E08-integrated-demo-and-evaluation.md) | Tim | P0 | In progress | [Tickets](../backlog/E08-integrated-demo-and-evaluation.md) | Four-service Compose, policy/no-policy browser flows, and revisions pass; real Phase 3B, live-model metrics, AWS, and rehearsal remain |
| [E09 - Productionisation and Security](E09-productionisation-and-security.md) | Tim | P3 | Deferred | [Tickets](../backlog/E09-productionisation-and-security.md) | Basic POC trust messaging and secret handling only |
| [E10 - Backend API and POC Persistence](E10-backend-api-and-poc-persistence.md) | Tim | P0 | In progress | [Tickets](../backlog/E10-backend-api-and-poc-persistence.md) | Versioned capability, comparison, conversation, revision, replay, undo, and run-inspection routes work; session cleanup and AWS remain |
| [E11 - Runtime Orchestration and Operations](E11-runtime-orchestration-and-operations.md) | Jana | P0 | In progress | [Tickets](../backlog/E11-runtime-orchestration-and-operations.md) | Bounded invocation coordinator and continuous scraper operate locally; OpenRouter, full failure matrix, freshness cycles, and AWS remain |
| [E12 - Conversational Summary Agent](E12-conversational-summary-agent.md) | Tim | P1 | In progress | [Tickets](../backlog/E12-conversational-summary-agent.md) | Contextual agent, budget proposals, reruns, replay, and undo work; other patch types, real Phase 3B tools, and OpenRouter remain |

## Ownership rules

1. Each epic has one primary owner who is accountable for its DOD.
2. Contributors may help without becoming co-owners.
3. Status changes must include updated repository evidence.
4. A POC-complete epic can still have production follow-ups; those belong in E09 or a later roadmap.
5. Scope changes should update both the epic file and the summary table above.

## Current focus

The direct E10/E06 read path, local PostgreSQL runtime, bounded fixture coordinator, and budget proposal/revision path are implemented. Follow the approved [RAG and website integration decisions](../evaluation/2026-08-28-rag-website-integration-decisions.md) and [staged real-product decision](../evaluation/2026-08-28-real-product-comparison-and-ranking-stages.md) to close source governance and deliver Phase 3B neutral real-product evidence comparison. In parallel, complete the still-open OpenRouter, formulation, evaluation, scraper-freshness, and broader mutation gates. Keep real-product ranking disabled until the Phase 6 E07, E08, data, DEC-004, and compliance gates pass. E09 remains deferred except for baseline safeguards and remains mandatory before public ranked use.