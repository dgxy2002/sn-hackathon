# E08 - Integrated Demo and Evaluation

| Field | Value |
|---|---|
| Primary owner | Tim |
| Priority | P0 |
| Status | In progress |
| Outcome | The team can accept, measure, rehearse, and record one reliable end-to-end POC assembled from the owned backend and agent capabilities. |

## Scope

- Accept shared contracts and fixtures produced by E10 and all capability owners.
- Integrate the frontend with the E10 API and E11 coordinator.
- Accept the complete local Docker Compose topology from a clean setup.
- Replay extraction, retrieval, decision, and changed-profile evaluation suites.
- Verify that real-product RAG remains read-only across the website and cannot alter E07 synthetic recommendations.
- Accept Phase 3B real-product evidence comparison against citation, neutrality, unknown-state, canonical-isolation, and accessibility fixtures.
- Independently evaluate any Phase 6 real-product ranked pilot before it can be enabled beyond its internal test configuration.
- Replay conversational Q&A, cached-plan exploration with evidence states, presentation, confirmation, revision, cancellation, conflict, and undo scenarios.
- Aggregate OpenRouter extraction and explanation correctness, latency, tool success, token, cost, and bounded-loop metrics.
- Verify that locally tested image digests are ready for ECR and that ECS, RDS, S3, Secrets Manager, and CloudWatch mappings are documented.
- Provide a preloaded scenario and recorded fallback.

## Requirements traceability

- **URS:** [URS-FR-008, URS-FR-010, URS-FR-011, URS-FR-012, URS-FR-018, URS-FR-019, URS-FR-020, URS-FR-021, URS-FR-022, URS-FR-024, URS-FR-027, URS-FR-028, URS-FR-029, URS-FR-030, URS-FR-031, URS-FR-032, URS-NFR-006, URS-NFR-007, URS-NFR-013, URS-NFR-015, URS-NFR-017](../urs/URS.md)
- **PRD:** [PRD-FR-022, PRD-FR-024, PRD-FR-025, PRD-FR-026, PRD-FR-029, PRD-FR-032, PRD-FR-034, PRD-FR-036, PRD-FR-037, PRD-FR-038, PRD-NFR-006, PRD-NFR-013, PRD-NFR-016, PRD-NFR-017, PRD-NFR-021](../prd/PRD.md)
- **Backlog:** [E08 tickets](../backlog/E08-integrated-demo-and-evaluation.md)
- **Staged real products:** URS-FR-033 to URS-FR-035, URS-NFR-022; PRD-FR-039 to PRD-FR-041, PRD-NFR-028, PRD-NFR-029.

## Repository evidence

- [`frontend/src/main.js`](../../frontend/src/main.js) already provides the complete simulated user journey.
- [`frontend/package.json`](../../frontend/package.json) provides a successful production build command.
- [`compose.yaml`](../../compose.yaml) builds healthy web, API, scraper, and PostgreSQL/pgvector services; the backend queries the local database for cached evidence.
- The [cached evidence browser smoke test](../evaluation/2026-08-28-cached-evidence-browser-smoke-test.md) records the successful containerized conversation and read-only evidence flow.
- [`docs/PLAN.md`](../PLAN.md) defines shared contracts, AWS assumptions, acceptance metrics, and the five-minute demo story.

## Definition of done

- [x] The four capability outputs and API routes validate against frozen shared contracts.
- [ ] One end-to-end scenario and one changed-goal scenario complete without manual data repair.
- [x] The demo visibly distinguishes live, cached, synthetic, and simulated data.
- [x] All 71 cached real-product records are searchable with approval/evidence state, and explored products remain visibly separate from synthetic recommendations.
- [ ] A small comparison-eligible subset passes Phase 3B field-citation, neutral-ordering, canonical-isolation, and browser acceptance tests.
- [ ] Any Phase 6 real-product ranked pilot passes independent deterministic correctness, abstention, stability, explanation-fidelity, and safeguard tests before enablement.
- [ ] Extraction, retrieval, recommendation, and orchestration acceptance targets are reported from predeclared fixtures.
- [ ] Conversational scenarios report grounding, valid-tool, confirmation, revision-consistency, replay, undo, latency, token, and estimated-cost outcomes against independent expected results.
- [ ] Model and tool runs report token, latency, cost, retry, iteration, and error metrics.
- [x] A clean setup follows the README and the frontend build succeeds.
- [ ] One documented Docker Compose command starts healthy web, API, scraper, PostgreSQL/pgvector, and configured local object-store services.
- [x] The normal and no-policy scenarios pass through the containerized API.
- [ ] An AWS readiness check maps the same image digests and environment contract to ECR/ECS, RDS, S3, Secrets Manager, and CloudWatch.
- [ ] The five-minute demo is rehearsed twice and has a recorded fallback.

**Acceptance evidence:** [Integrated runtime and browser acceptance](../evaluation/2026-08-28-integrated-runtime-browser-acceptance.md). Changed-goal, live-model metrics, real Phase 3B acceptance, AWS review, and demo rehearsal remain open.

## POC boundary

The goal is a stable judged demonstration and migration-ready container contract, not a highly available public service. Full production security and operational hardening remain in E09.