# E08 Backlog - Integrated Demo and Evaluation

**Epic:** [E08 - Integrated Demo and Evaluation](../epics/E08-integrated-demo-and-evaluation.md)
**Owner:** Tim

## E08-T01 - Accept shared contracts and fixtures

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P0 |
| Size | M |
| Depends on | E03-T02, E04-T02, E10-T02 |

**User story:** As the release owner, I need all capability owners to accept the same contracts and fixtures so integration has an explicit entry gate.

**Requirements:** URS-FR-017, URS-FR-019, URS-NFR-003, URS-NFR-004, URS-NFR-007, URS-NFR-011, URS-NFR-013; PRD-FR-024, PRD-NFR-005, PRD-NFR-008, PRD-NFR-013, PRD-NFR-016.

**Acceptance criteria:**

- [x] Profile, extraction, evidence, plan, recommendation, event, error, and run-metric schemas are versioned by E10.
- [x] Complete, incomplete, invalid, no-evidence, dependency-failure, and changed-profile fixtures are committed.
- [ ] E03, E04, E06, E07, E10, and E11 owners validate their boundaries against the same schema versions.
- [ ] Fixture ground truth identifies reviewer, review date, source, and limitations.
- [ ] Contract changes require an explicit version update and renewed acceptance.

## E08-T02 - Integrate the frontend, API, and coordinator

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P0 |
| Size | L |
| Depends on | E08-T01, E10-T05, E11-T05 |

**User story:** As a demo user, I need one continuous journey through the browser, backend API, and coordinator so the owned capabilities behave as one product.

**Requirements:** URS-FR-008, URS-FR-010, URS-FR-011, URS-FR-012, URS-FR-017, URS-FR-020, URS-NFR-006, URS-NFR-010, URS-NFR-011; PRD-FR-011, PRD-FR-013, PRD-FR-021, PRD-NFR-010, PRD-NFR-017.

**Acceptance criteria:**

- [x] The frontend can call E10 without embedded capability fixtures on the normal integration path.
- [x] Read-only RAG is available through E10 across applicable website contexts and cannot alter E07 synthetic recommendation inputs or results.
- [x] E11 invokes only allowed extraction, profile, retrieval, and decision tools.
- [x] No-plan and existing-plan scenarios return schema-valid results.
- [ ] One changed-goal conversational scenario returns a schema-valid deterministic difference explanation.
- [x] Live, cached, simulated, synthetic, approved, unverified, stale, and unknown evidence states are visibly distinguished where applicable.
- [ ] Missing-information, no-evidence, and dependency-failure outcomes render without presenting a recommendation.

## E08-T03 - Capture agent and evaluation metrics

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P0 |
| Size | M |
| Depends on | E04-T04, E06-T04, E07-T04, E08-T02, E11-T05 |

**User story:** As a judge, I need observable agent actions and measured results so the team can prove correctness, efficiency, and bounded behavior.

**Requirements:** URS-FR-018, URS-FR-019, URS-NFR-006, URS-NFR-007, URS-NFR-013; PRD-FR-022, PRD-FR-024, PRD-FR-025, PRD-NFR-005, PRD-NFR-006, PRD-NFR-013, PRD-NFR-016.

**Acceptance criteria:**

- [ ] Each run records schema validity, tool success, latency, errors, iterations, tokens, and estimated cost.
- [ ] Every loop has a hard cap and no evaluation run exceeds it.
- [ ] Quiz, OpenRouter extraction, retrieval, decision, contract, and orchestration metrics use predeclared fixtures and independent ground truth.
- [ ] Results are exportable for the deck and video.

## E08-T04 - Verify clean setup and demo scenarios

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P0 |
| Size | M |
| Depends on | E08-T02, E08-T03, E10-T05, E11-T05 |

**User story:** As the presenting team, we need a clean and repeatable run so environment drift does not block the judged demo.

**Requirements:** URS-FR-019, URS-FR-020, URS-NFR-006, URS-NFR-010, URS-NFR-013; PRD-FR-021, PRD-FR-024, PRD-NFR-006, PRD-NFR-013, PRD-NFR-017.

**Acceptance criteria:**

- [x] The frontend production build succeeds.
- [x] The README documents setup for every demonstrated component.
- [x] A clean environment completes the normal scenario.
- [ ] A clean environment completes the changed-goal scenario.
- [x] No synthetic data is presented as real.

**Current evidence:** The frontend production build passes. The [integrated runtime and browser acceptance](../evaluation/2026-08-28-integrated-runtime-browser-acceptance.md), [Bedrock integration](../evaluation/2026-09-03-bedrock-personalization-integration.md), and [Gen-Z journey review](../evaluation/2026-09-03-gen-z-journey-and-project-truth.md) record policy, no-policy, optional-quiz, live-provider, proposal, confirmation, replay, undo, desktop, and mobile paths. Changed-goal remains open.

## E08-T05 - Rehearse and record the five-minute demo

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P0 |
| Size | S |
| Depends on | E08-T04 |

**User story:** As the presenting team, we need a rehearsed story and fallback recording so the product value remains clear under time and network constraints.

**Requirements:** URS-NFR-006; PRD-NFR-006.

**Acceptance criteria:**

- [ ] The final story fits within five minutes twice consecutively.
- [ ] The demo shows plan, action, adaptation, evidence, and measured benefit.
- [ ] A preloaded scenario removes live-scraping dependency.
- [ ] A backup recording is accessible to the team.

## E08-T06 - Publish the POC evaluation report

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P0 |
| Size | M |
| Depends on | E02-T04, E04-T04, E06-T04, E07-T04, E08-T03 |

**User story:** As a judge or reviewer, I need one evidence pack containing measured benefits, correctness, failure cases, and limitations so project claims are independently inspectable.

**Requirements:** URS-FR-018, URS-FR-019, URS-NFR-006, URS-NFR-007, URS-NFR-013; PRD-FR-022, PRD-FR-024, PRD-FR-025, PRD-NFR-006, PRD-NFR-013, PRD-NFR-016.

**Acceptance criteria:**

- [ ] The report covers quiz comprehension, OpenRouter extraction accuracy, Bedrock explanation completeness and grounding, retrieval top-five results, citation coverage, decision-rule violations, category agreement, schema validity, loop caps, latency, tokens, and estimated cost.
- [ ] Every metric names fixture version, sample size, evaluator, run date, and limitations.
- [ ] Failed cases and unmet targets remain visible.
- [ ] Aspirational targets are visually distinct from measured results.
- [ ] Deck and demo numerical claims link back to the report.

## E08-T07 - Accept the local Docker Compose topology

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P0 |
| Size | M |
| Depends on | E04-T05, E05-T05, E06-T06, E10-T06, E11-T05 |

**User story:** As the release owner, I need one clean local command to start and test the entire POC without AWS access.

**Requirements:** URS-FR-021, URS-FR-022, URS-FR-025, URS-NFR-006, URS-NFR-014, URS-NFR-017; PRD-FR-026, PRD-FR-030, PRD-NFR-006, PRD-NFR-018, PRD-NFR-021.

**Acceptance criteria:**

- [x] One documented Docker Compose command starts healthy web, backend, one scraper, and PostgreSQL/pgvector services; local object storage is optional and unconfigured.
- [x] A fresh environment initializes schemas and synthetic fixtures without manual repair.
- [x] Normal existing-plan and no-policy scenarios pass.
- [ ] Changed-goal, OpenRouter-unavailable fallback, and stale-source scenarios pass.
- [x] No real secret is required for fixture mode and no secret reaches the browser or logs.
- [ ] Shutdown preserves intended database/object-store volumes and terminates application processes cleanly.

## E08-T08 - Review AWS deployment readiness

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | M |
| Depends on | E05-T06, E06-T07, E10-T07, E11-T07 |

**User story:** As the release owner, I need evidence that the locally accepted containers and contracts have a practical AWS destination without claiming production readiness.

**Requirements:** URS-FR-024, URS-NFR-014, URS-NFR-015, URS-NFR-016, URS-NFR-017; PRD-FR-029, PRD-NFR-019, PRD-NFR-020, PRD-NFR-021.

**Acceptance criteria:**

- [ ] The reviewed topology maps every module to ECR, ECS Fargate, ALB, RDS, S3, Secrets Manager, and CloudWatch as applicable.
- [ ] Web, backend, and scraper task definitions reference the same image digests accepted locally.
- [ ] Environment-variable mappings, networking, migrations, health checks, rollback, and cost assumptions are recorded.
- [ ] Scraper desired count one and database singleton lease are explicit.
- [ ] Remaining production controls are linked to deferred E09 tickets.

## E08-T09 - Evaluate conversational summary scenarios

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P1 |
| Size | M |
| Depends on | E12-T03, E12-T04 |

**User story:** As a judge, I need replayable evidence that conversational exploration changes the page usefully without bypassing confirmation, evidence, or deterministic ranking controls.

**Requirements:** URS-FR-027, URS-FR-028, URS-FR-029, URS-FR-030, URS-FR-031, URS-FR-032, URS-NFR-013; PRD-FR-032, PRD-FR-034, PRD-FR-036, PRD-FR-037, PRD-FR-038, PRD-NFR-013, PRD-NFR-016.

**Acceptance criteria:**

- [ ] Frozen scenarios cover grounded Q&A, cached-plan exploration with evidence states, presentation change, confirmed and cancelled profile changes, extraction correction, undo, stale evidence, no evidence, invalid action, dependency failure, and loop cap.
- [ ] Catalogue scenarios cover all 71 cached products and prove that unverified or stale evidence is labelled and no real product becomes an E07 recommendation.
- [ ] Independent expected outcomes identify allowed tools, confirmation boundary, citations, deterministic result changes, page regions, and terminal state.
- [ ] The report records completion, grounding, tool-validity, confirmation, revision-consistency, undo, latency, token, and estimated-cost results.
- [ ] Fixture and configured Bedrock explanation modes use the same schemas and disclose adapter, model, prompt, tool, formulation, ruleset, and catalogue versions; OpenRouter extraction is evaluated separately.
- [ ] No model self-grades its own conversational or page-changing output.

**Current evidence:** The [fixture-agent smoke test](../evaluation/2026-08-26-fixture-agent-smoke-test.md), the [integrated runtime and browser acceptance](../evaluation/2026-08-28-integrated-runtime-browser-acceptance.md), the [Bedrock and personalization integration](../evaluation/2026-09-03-bedrock-personalization-integration.md), the [Gen-Z journey review](../evaluation/2026-09-03-gen-z-journey-and-project-truth.md), and backend checks cover grounded Q&A, presentation changes, configured Bedrock explanation, confirmed and cancelled budget changes, deterministic rerun, replay, undo, idempotency, dependency failure, stale revision, and model contract validation. Extraction correction, loop-cap, and complete scenario metrics remain untested.

## E08-T10 - Accept Phase 3B real-product evidence comparison

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | M |
| Depends on | E01-T06, E06-T09, E10-T09, E12-T06 |

**User story:** As a reviewer, I need independent evidence that real-product comparison is factual, neutral, and isolated from recommendation state before it becomes a demo feature.

**Requirements:** URS-FR-033, URS-FR-034, URS-NFR-004, URS-NFR-013, URS-NFR-022; PRD-FR-039, PRD-FR-040, PRD-NFR-016, PRD-NFR-028, PRD-NFR-029.

**Acceptance criteria:**

- [ ] Predeclared fixtures cover two to four complete products, partial fields, mixed category, stale, conflicting, unapproved, unsupported, and no-evidence cases.
- [ ] One hundred percent of populated cells resolve to the expected field evidence, source, date/version state, and normalized unit.
- [ ] Unknown values remain unknown and prohibited recommendation language appears zero times.
- [ ] Discovery-result permutations always produce provider/product comparison ordering after the same user selection.
- [ ] Before and after profile, E07 catalogue, recommendation, and summary-revision contracts are byte-equivalent for presentation-only comparison actions.
- [ ] Desktop, mobile, keyboard, screen-reader, reduced-motion, cached-adapter, and fixture-adapter scenarios pass.

**Current evidence:** The neutral comparison contract, canonical-isolation tests, fixture rendering, and mobile layout are complete. This ticket remains ready because no real-product subset has passed E06-T09 source and field gates.

## E08-T11 - Evaluate the Phase 6 real-product ranked pilot

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | M |
| Depends on | E07-T08 |

**User story:** As an approving reviewer, I need independent real-product ranking tests so DEC-004 cannot be treated as satisfied by plausible model output or a successful evidence comparison.

**Requirements:** URS-FR-015, URS-FR-019, URS-FR-026, URS-FR-034, URS-FR-035, URS-NFR-003, URS-NFR-004, URS-NFR-013; PRD-FR-024, PRD-FR-031, PRD-FR-041, PRD-NFR-002, PRD-NFR-015, PRD-NFR-016.

**Acceptance criteria:**

- [ ] Real-product profile, catalogue, evidence, ruleset, expected eligibility, expected rank, and abstention fixtures are written before execution and name independent reviewers.
- [ ] Hard-rule violations equal zero and the approved ranking agreement target is met without model self-grading.
- [ ] Missing, stale, conflicting, or superseded decision inputs produce the expected exclusion or no-recommendation result.
- [ ] Repeated version-identical inputs produce identical eligibility, fit, ordering, reasons, and evidence references.
- [ ] Explanation fidelity, replacement safeguards, synthetic fallback, latency, and failure behavior are reported with limitations.
- [ ] Failure does not affect Phase 3B evidence comparison and leaves real-product ranked mode disabled.