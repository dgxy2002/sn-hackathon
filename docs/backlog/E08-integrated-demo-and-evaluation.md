# E08 Backlog - Integrated Demo and Evaluation

**Epic:** [E08 - Integrated Demo and Evaluation](../epics/E08-integrated-demo-and-evaluation.md)
**Owner:** Tim

## E08-T01 - Accept shared contracts and fixtures

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P0 |
| Size | M |
| Depends on | E03-T02, E04-T02, E10-T02 |

**User story:** As the release owner, I need all capability owners to accept the same contracts and fixtures so integration has an explicit entry gate.

**Requirements:** URS-FR-017, URS-FR-019, URS-NFR-003, URS-NFR-004, URS-NFR-007, URS-NFR-011, URS-NFR-013; PRD-FR-024, PRD-NFR-005, PRD-NFR-008, PRD-NFR-013, PRD-NFR-016.

**Acceptance criteria:**

- [ ] Profile, extraction, evidence, plan, recommendation, event, error, and run-metric schemas are versioned by E10.
- [ ] Complete, incomplete, invalid, no-evidence, dependency-failure, and changed-profile fixtures are committed.
- [ ] E03, E04, E06, E07, E10, and E11 owners validate their boundaries against the same schema versions.
- [ ] Fixture ground truth identifies reviewer, review date, source, and limitations.
- [ ] Contract changes require an explicit version update and renewed acceptance.

## E08-T02 - Integrate the frontend, API, and coordinator

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P0 |
| Size | L |
| Depends on | E08-T01, E10-T05, E11-T05 |

**User story:** As a demo user, I need one continuous journey through the browser, backend API, and coordinator so the owned capabilities behave as one product.

**Requirements:** URS-FR-008, URS-FR-010, URS-FR-011, URS-FR-012, URS-FR-017, URS-FR-020, URS-NFR-006, URS-NFR-010, URS-NFR-011; PRD-FR-011, PRD-FR-013, PRD-FR-021, PRD-NFR-010, PRD-NFR-017.

**Acceptance criteria:**

- [ ] The frontend can call E10 without embedded capability fixtures on the normal integration path.
- [ ] E11 invokes only allowed extraction, profile, retrieval, and decision tools.
- [ ] One normal and one changed-goal scenario return schema-valid results.
- [ ] Live, cached, simulated, and synthetic data are visibly distinguished.
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
- [ ] The README documents setup for every demonstrated component.
- [ ] A clean environment completes the normal scenario.
- [ ] A clean environment completes the changed-goal scenario.
- [ ] No synthetic data is presented as real.

**Current evidence:** `npm --prefix frontend run build` passes.

## E08-T05 - Rehearse and record the five-minute demo

| Field | Value |
|---|---|
| Status | Ready |
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

- [ ] The report covers quiz comprehension, OpenRouter extraction accuracy, retrieval top-five results, citation coverage, decision-rule violations, category agreement, explanation completeness, schema validity, loop caps, latency, tokens, and estimated cost.
- [ ] Every metric names fixture version, sample size, evaluator, run date, and limitations.
- [ ] Failed cases and unmet targets remain visible.
- [ ] Aspirational targets are visually distinct from measured results.
- [ ] Deck and demo numerical claims link back to the report.

## E08-T07 - Accept the local Docker Compose topology

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P0 |
| Size | M |
| Depends on | E04-T05, E05-T05, E06-T06, E10-T06, E11-T05 |

**User story:** As the release owner, I need one clean local command to start and test the entire POC without AWS access.

**Requirements:** URS-FR-021, URS-FR-022, URS-FR-025, URS-NFR-006, URS-NFR-014, URS-NFR-017; PRD-FR-026, PRD-FR-030, PRD-NFR-006, PRD-NFR-018, PRD-NFR-021.

**Acceptance criteria:**

- [ ] One documented Docker Compose command starts healthy web, backend, one scraper, PostgreSQL/pgvector, and configured local object-store services.
- [ ] A fresh environment initializes schemas and synthetic fixtures without manual repair.
- [ ] Normal, no-policy, changed-goal, OpenRouter-unavailable fallback, and stale-source scenarios pass.
- [ ] No real secret is required for fixture mode and no secret reaches the browser or logs.
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
| Status | Ready |
| Priority | P1 |
| Size | M |
| Depends on | E12-T03, E12-T04 |

**User story:** As a judge, I need replayable evidence that conversational exploration changes the page usefully without bypassing confirmation, evidence, or deterministic ranking controls.

**Requirements:** URS-FR-027, URS-FR-028, URS-FR-029, URS-FR-030, URS-FR-031, URS-FR-032, URS-NFR-013; PRD-FR-032, PRD-FR-034, PRD-FR-036, PRD-FR-037, PRD-FR-038, PRD-NFR-013, PRD-NFR-016.

**Acceptance criteria:**

- [ ] Frozen scenarios cover grounded Q&A, approved-plan exploration, presentation change, confirmed and cancelled profile changes, extraction correction, undo, stale evidence, no evidence, invalid action, dependency failure, and loop cap.
- [ ] Independent expected outcomes identify allowed tools, confirmation boundary, citations, deterministic result changes, page regions, and terminal state.
- [ ] The report records completion, grounding, tool-validity, confirmation, revision-consistency, undo, latency, token, and estimated-cost results.
- [ ] Fixture and configured OpenRouter modes use the same schemas and disclose adapter, model, prompt, tool, formulation, ruleset, and catalogue versions.
- [ ] No model self-grades its own conversational or page-changing output.