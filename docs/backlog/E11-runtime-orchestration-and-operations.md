# E11 Backlog - Runtime Orchestration and Operations

**Epic:** [E11 - Runtime Orchestration and Operations](../epics/E11-runtime-orchestration-and-operations.md)
**Owner:** Jana

## E11-T01 - Freeze local runtime and OpenRouter configuration

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P0 |
| Size | S |
| Depends on | E04-T02, E10-T06 |

**User story:** As the implementation team, we need one local runtime and provider contract so coordinator work is independent of AWS access.

**Requirements:** URS-FR-021, URS-FR-022, URS-NFR-013, URS-NFR-014, URS-NFR-015; PRD-FR-013, PRD-FR-023, PRD-FR-027, PRD-NFR-013, PRD-NFR-018, PRD-NFR-022.

**Acceptance criteria:**

- [ ] Docker Compose and OpenRouter `5.6 Luna` are documented as the local default.
- [ ] The exact OpenRouter model slug is configured once through `OPENROUTER_MODEL` and recorded per run.
- [ ] Policy extraction and explanation provider modes are selected independently by environment variables.
- [ ] Amazon Bedrock and AgentCore are optional future adapters and do not block local startup.
- [ ] Fixture mode starts without an OpenRouter credential.

## E11-T02 - Implement the coordinator state machine and entrypoint

| Field | Value |
|---|---|
| Status | Done |
| Priority | P0 |
| Size | L |
| Depends on | E10-T02, E11-T01 |

**User story:** As a user, I need one bounded workflow to coordinate profile, optional policy, evidence, decision, and explanation in the correct order.

**Requirements:** URS-FR-006, URS-FR-012, URS-FR-015, URS-FR-017, URS-FR-023, URS-NFR-010, URS-NFR-011; PRD-FR-013, PRD-FR-020, PRD-FR-023, PRD-FR-028, PRD-NFR-010, PRD-NFR-014.

**Acceptance criteria:**

- [x] `POST /invocations` accepts the versioned invocation contract in the backend container.
- [x] States cover validation, optional extraction review, profile completion, retrieval, decision, explanation, and terminal outcomes.
- [x] The no-policy branch skips extraction and preserves existing-policy fields as unknown.
- [x] Missing information, no evidence, no eligible plan, dependency failure, and completion are explicit states.
- [x] Every state validates input and output before transition.

## E11-T03 - Enforce tool policy, loop caps, and adapter fallback

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P0 |
| Size | M |
| Depends on | E10-T04, E11-T02 |

**User story:** As a reviewer, I need tool use and retries constrained so the coordinator cannot call unapproved capabilities or loop indefinitely.

**Requirements:** URS-FR-018, URS-FR-020, URS-NFR-007, URS-NFR-010; PRD-FR-020, PRD-FR-021, PRD-NFR-005, PRD-NFR-014, PRD-NFR-017.

**Acceptance criteria:**

- [ ] The allowed tool registry contains only versioned E10 capability clients.
- [ ] Each state defines maximum calls, retries, timeout, and permitted next states.
- [ ] Exhausted limits return `LOOP_LIMIT_REACHED` or a typed dependency failure.
- [ ] Raw document content is not returned to or retained in explanation prompts.
- [ ] Fixture fallback uses the same contracts and visible mode labels.

## E11-T04 - Generate and validate OpenRouter explanations

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P0 |
| Size | M |
| Depends on | E07-T03, E11-T02 |

**User story:** As a user, I need plain-language reasons from the configured model that preserve the deterministic result.

**Requirements:** URS-FR-011, URS-FR-014, URS-FR-015, URS-FR-022, URS-NFR-003, URS-NFR-004, URS-NFR-010; PRD-FR-010, PRD-FR-020, PRD-FR-027, PRD-NFR-002, PRD-NFR-003, PRD-NFR-013, PRD-NFR-014, PRD-NFR-022.

**Acceptance criteria:**

- [ ] OpenRouter receives only the immutable decision contract and small cited evidence records.
- [ ] Output covers reasons, trade-offs, assumptions, missing data, confidence, and evidence references.
- [ ] Validation rejects changed ranks, numbers, eligibility, evidence IDs, unsupported claims, and cancellation language.
- [ ] Provider, exact model slug, prompt version, token use, latency, estimated cost, and result are recorded.

## E11-T05 - Emit run events, metrics, and replay metadata

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P0 |
| Size | M |
| Depends on | E10-T04, E11-T03, E11-T04 |

**User story:** As a judge, I need an ordered execution trace so I can see how the coordinator acted, stopped, and adapted.

**Requirements:** URS-FR-018, URS-FR-019, URS-NFR-007, URS-NFR-010, URS-NFR-013; PRD-FR-022, PRD-FR-023, PRD-FR-024, PRD-NFR-005, PRD-NFR-013, PRD-NFR-014, PRD-NFR-016.

**Acceptance criteria:**

- [ ] Events identify run, state, capability, tool, provider, model, prompt, contract, adapter, formulation, ruleset, and source versions.
- [ ] Metrics include validation, retries, iterations, latency, tokens, estimated cost, warnings, and errors.
- [ ] Events are available through E10 run inspection without raw log access.
- [ ] Normal, no-policy, missing-information, no-evidence, dependency-failure, loop-limit, and changed-goal fixtures are replayable.
- [ ] Expected correctness comes from E08 fixtures rather than model self-grading.

## E11-T06 - Coordinate continuous scraper operations

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | M |
| Depends on | E05-T05, E10-T03 |

**User story:** As an operator, I need the runtime to expose one scraper lifecycle and its freshness state alongside application runs.

**Requirements:** URS-FR-016, URS-FR-025, URS-NFR-010, URS-NFR-012, URS-NFR-017; PRD-FR-017, PRD-FR-030, PRD-NFR-011, PRD-NFR-015, PRD-NFR-021.

**Acceptance criteria:**

- [ ] Runtime status identifies the active lease owner, last cycle, next due source, and freshness state.
- [ ] The lifecycle emits events for due selection, fetch, parse, normalize, version, upsert, index, success, retry, and failure.
- [ ] Health degrades on repeated failures or source staleness without discarding the prior verified version.
- [ ] Only one active scraper loop can hold the lease.
- [ ] Scraper events contain no credentials or prohibited raw content.

## E11-T07 - Prepare the AWS runtime topology

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | M |
| Depends on | E05-T06, E06-T07, E10-T07, E11-T05, E11-T06 |

**User story:** As a deployment owner, I need the local runtime mapped module by module to AWS while OpenRouter remains the configured external provider.

**Requirements:** URS-FR-024, URS-FR-025, URS-NFR-014, URS-NFR-015, URS-NFR-016, URS-NFR-017; PRD-FR-029, PRD-FR-030, PRD-NFR-019, PRD-NFR-020, PRD-NFR-021, PRD-NFR-022.

**Acceptance criteria:**

- [ ] ECR stores the locally accepted web, backend, and scraper image digests.
- [ ] ECS Fargate runs web and backend services plus one scraper service task.
- [ ] RDS PostgreSQL/pgvector, S3, Secrets Manager, ALB, controlled egress, and CloudWatch mappings are explicit.
- [ ] OpenRouter remains external and is reached from private tasks through controlled outbound networking.
- [ ] Optional Bedrock or AgentCore adapters are documented separately and do not alter the local contract.

## E11-T08 - Orchestrate bounded conversational tools

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P1 |
| Size | L |
| Depends on | E10-T08, E11-T03, E11-T05 |

**User story:** As a reviewer, I need consequential conversational requests executed through a bounded state machine so the model can sequence useful actions without gaining arbitrary application control.

**Requirements:** URS-FR-027, URS-FR-028, URS-FR-029, URS-FR-030, URS-FR-032, URS-NFR-018, URS-NFR-019; PRD-FR-033, PRD-FR-034, PRD-FR-035, PRD-FR-036, PRD-FR-038, PRD-NFR-023, PRD-NFR-024, PRD-NFR-026.

**Acceptance criteria:**

- [x] The coordinator resolves supported intents and invokes only registered, schema-valid read, presentation, proposal, deterministic-rerun, revision, and undo tools.
- [x] Tool policy validates target, preconditions, base versions, idempotency, confirmation, allowed summary regions, loop cap, and terminal state.
- [x] Model output is never executed as HTML, JavaScript, selectors, coordinates, SQL, arbitrary URLs, or undeclared tool properties.
- [x] Ordered events expose intent, tool, target, status, evidence count, confirmation state, affected regions, versions, latency, tokens, cost, and errors without hidden reasoning.
- [ ] Fixture and configured OpenRouter adapters support identical normal, unsupported, stale, conflict, timeout, provider-failure, and loop-limit scenarios.

Read-only questions and cached-catalogue exploration may call the typed E10/E06 evidence service without entering this coordinator. Any proposal, canonical input change, deterministic rerun, summary revision, replay, or undo remains within E11's bounded tool policy.