# E10 Backlog - Backend API and POC Persistence

**Epic:** [E10 - Backend API and POC Persistence](../epics/E10-backend-api-and-poc-persistence.md)
**Owner:** Tim

## E10-T01 - Scaffold the backend service and capability manifest

| Field | Value |
|---|---|
| Status | Done |
| Priority | P0 |
| Size | M |
| Depends on | None |

**User story:** As a developer, I need one locally runnable backend process with discoverable capability modes so frontend and agent work has a stable integration target.

**Requirements:** URS-FR-017, URS-FR-020, URS-NFR-006, URS-NFR-010; PRD-FR-014, PRD-FR-021, PRD-NFR-006, PRD-NFR-010, PRD-NFR-017.

**Acceptance criteria:**

- [x] A documented command starts the service without production credentials when fixture mode is selected.
- [x] `GET /health` reports service version and dependency status.
- [x] `GET /v1/capabilities` reports contract versions and live, cached, synthetic, or simulated mode for each capability.
- [x] Configuration validates at startup and secrets are absent from client output and logs.
- [x] Local frontend origins are configurable without a wildcard production policy.

**Evidence:** [`backend/app/main.py`](../../backend/app/main.py), [`backend/app/config.py`](../../backend/app/config.py), [`backend/.env.example`](../../backend/.env.example), [`backend/tests/test_system_routes.py`](../../backend/tests/test_system_routes.py), and the root [`README.md`](../../README.md).

## E10-T02 - Publish shared schemas and typed errors

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P0 |
| Size | M |
| Depends on | E03-T02, E10-T01 |

**User story:** As a capability owner, I need versioned machine-readable schemas and common errors so independently built modules reject incompatible payloads early.

**Requirements:** URS-FR-017, URS-FR-019, URS-NFR-010, URS-NFR-011, URS-NFR-013; PRD-FR-014, PRD-FR-024, PRD-NFR-008, PRD-NFR-010, PRD-NFR-013.

**Acceptance criteria:**

- [ ] Schemas exist for profile, extraction, evidence, plan, recommendation, invocation, run event, run metrics, and error envelope.
- [ ] Every schema has a stable ID and explicit version.
- [ ] Complete, incomplete, invalid, and terminal-failure examples are committed.
- [x] Errors include code, message, retryable state, run ID, and safe details.

**Current evidence:** [`backend/app/contracts.py`](../../backend/app/contracts.py) and [`backend/tests/test_conversations.py`](../../backend/tests/test_conversations.py). Capability-owned schemas remain blocked by E03/E04/E06/E07 contracts.
- [ ] Contract tests fail on incompatible versions, missing fields, and wrong types.

## E10-T03 - Implement synthetic session and repository adapters

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | L |
| Depends on | E10-T02 |

**User story:** As a POC user, I need my synthetic profile, reviewed extraction, and result to survive API steps so the integrated journey can be replayed without production identity.

**Requirements:** URS-FR-004, URS-FR-005, URS-FR-006, URS-FR-012, URS-FR-017, URS-NFR-005, URS-NFR-011, URS-NFR-013; PRD-FR-015, PRD-NFR-011, PRD-NFR-012, PRD-NFR-013.

**Acceptance criteria:**

- [ ] Anonymous POC sessions record consent state and expiry.
- [ ] Profiles retain version, change set, provenance, and present, unknown, or not-applicable field state.
- [ ] Extraction corrections preserve original and reviewed values.
- [ ] Recommendation and run records retain all versions needed for replay.
- [ ] Repository interfaces support fixture and local PostgreSQL/pgvector storage without changing capability contracts.
- [ ] Uploaded document bytes are deleted after extraction by default.

## E10-T04 - Expose capability routes and adapters

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P0 |
| Size | L |
| Depends on | E04-T03, E06-T03, E07-T02, E10-T02, E10-T03 |

**User story:** As a frontend or coordinator developer, I need one API for profile, extraction, evidence, decision, and run inspection so I do not couple to each capability implementation.

**Requirements:** URS-FR-007, URS-FR-008, URS-FR-010, URS-FR-011, URS-FR-015, URS-FR-017, URS-FR-020, URS-NFR-010, URS-NFR-011; PRD-FR-014, PRD-FR-015, PRD-FR-016, PRD-FR-018, PRD-FR-019, PRD-FR-021, PRD-NFR-010, PRD-NFR-017.

**Acceptance criteria:**

- [ ] Profile create/read/version, extraction submit/review, evidence search, recommendation evaluation, and run-inspection routes match the PRD API surface.
- [x] `POST /v1/evidence/search` calls an E06 service through Supabase or deterministic fixture adapters and returns identical versioned response schemas.
- [x] Evidence responses distinguish source approval, evidence state, document as-of date, product effective date, retrieval date, provenance, and synthetic status.
- [x] Real, cached, synthetic, and simulated adapters return the same response schemas.
- [x] Each response includes mode, contract version, and run or correlation ID.
- [ ] Missing information, low-confidence review, no evidence, no eligible plan, stale evidence, timeout, and dependency failure are typed outcomes.
- [x] Capability-specific business logic remains outside route handlers.

**Delivery order:** Implement the direct read-only E10/E06 path first. E11 is not required to relay a typed evidence query, but remains mandatory for proposals, confirmed input changes, deterministic reruns, revisions, and undo.

## E10-T05 - Verify API contracts, idempotency, and frontend integration

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P0 |
| Size | M |
| Depends on | E10-T04 |

**User story:** As the release owner, I need executable API tests and a browser integration path so the backend contract is proven beyond documentation.

**Requirements:** URS-FR-017, URS-FR-019, URS-FR-020, URS-NFR-006, URS-NFR-010, URS-NFR-011, URS-NFR-012; PRD-FR-014, PRD-FR-021, PRD-FR-024, PRD-NFR-010, PRD-NFR-011, PRD-NFR-017.

**Acceptance criteria:**

- [ ] Contract tests exercise every success and terminal-error response.
- [ ] Repeated mutating requests follow documented idempotency behavior.
- [ ] Dependency timeouts and retries are bounded and tested.
- [x] The frontend completes one normal fixture scenario through the API.
- [ ] The frontend completes read-only RAG questions and broad cached-catalogue exploration through both Supabase and fixture modes without changing the synthetic recommendation.
- [x] Clean setup and test commands are documented in the repository README.

**Current evidence:** Idempotent conversation messages, typed conflicts, cached evidence, and the live frontend/API path are covered by [`backend/tests/test_conversations.py`](../../backend/tests/test_conversations.py), [`backend/tests/test_evidence.py`](../../backend/tests/test_evidence.py), the [fixture-agent smoke test](../evaluation/2026-08-26-fixture-agent-smoke-test.md), and the [cached evidence browser smoke test](../evaluation/2026-08-28-cached-evidence-browser-smoke-test.md). Supabase browser parity and full capability-route coverage remain pending.

## E10-T06 - Containerize the local API and state services

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P0 |
| Size | L |
| Depends on | E10-T01 |

**User story:** As a developer, I need the API and local dependencies in Docker Compose so the POC starts consistently without cloud services.

**Requirements:** URS-FR-021, URS-NFR-006, URS-NFR-014, URS-NFR-015, URS-NFR-016, URS-NFR-017; PRD-FR-026, PRD-NFR-006, PRD-NFR-018, PRD-NFR-020, PRD-NFR-021.

**Acceptance criteria:**

- [ ] Dockerfiles build immutable web, backend, and scraper images; application processes run as non-root where practical.
- [ ] Docker Compose defines web, backend, scraper, PostgreSQL/pgvector, and optional S3-compatible object-store services with health checks, networks, and volumes.
- [ ] The scraper service is configured as one instance and is not duplicated by startup profiles.
- [ ] `.env.example` documents safe placeholders for `APP_ENV`, `DATABASE_URL`, storage settings, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, provider modes, and scraper freshness settings.
- [ ] `.env` and generated secrets are ignored; no secret appears in images, Compose configuration, logs, or frontend bundles.
- [ ] Containers handle termination and write structured logs to stdout/stderr.

## E10-T07 - Map local adapters and images to AWS

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | M |
| Depends on | E10-T06 |

**User story:** As a deployment owner, I need a documented AWS mapping that reuses local images and environment contracts so migration is a service swap rather than an application rewrite.

**Requirements:** URS-FR-024, URS-NFR-014, URS-NFR-015, URS-NFR-016, URS-NFR-017; PRD-FR-029, PRD-NFR-019, PRD-NFR-020, PRD-NFR-021.

**Acceptance criteria:**

- [ ] Web, backend, and scraper images map to ECR and ECS Fargate task definitions.
- [ ] PostgreSQL/pgvector maps to RDS PostgreSQL and local object storage maps to S3.
- [ ] `.env` secret names map to Secrets Manager injection and non-secret values map to task configuration or Parameter Store.
- [ ] ALB routes web/API traffic, private subnets contain backend, scraper, and RDS, and controlled egress reaches OpenRouter and approved sources.
- [ ] CloudWatch receives logs, health metrics, scraper freshness metrics, and alarms.
- [ ] The mapping documents image promotion, migrations, rollback, and the boundary with deferred E09 hardening.

## E10-T08 - Expose conversation and summary revision APIs

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P1 |
| Size | L |
| Depends on | E10-T02, E10-T03, E10-T05 |

**User story:** As the web experience, I need versioned conversation, proposal, confirmation, revision, replay, and undo APIs so dynamic summary changes remain coherent and inspectable.

**Requirements:** URS-FR-027, URS-FR-030, URS-FR-031, URS-FR-032, URS-NFR-010, URS-NFR-020; PRD-FR-032, PRD-FR-033, PRD-FR-036, PRD-FR-037, PRD-FR-038, PRD-NFR-023, PRD-NFR-025, PRD-NFR-026.

**Acceptance criteria:**

- [ ] Routes create conversations, accept messages, expose action events, confirm or reject proposals, list revisions, replay runs, and undo applied revisions.
- [ ] Conversation, message, proposal, action, confirmation, revision, and delta schemas reference immutable capability versions.
- [ ] Idempotency and optimistic version checks prevent duplicate confirmations, stale proposals, and partial canonical updates.
- [ ] Synthetic current-session repositories delete conversation and revision state with the session unless a named fixture retains it.
- [ ] Typed errors include action not allowed, confirmation required, revision conflict, no evidence, dependency unavailable, timeout, and loop limit.

**Current evidence:** Conversation creation, idempotent messages, action events, action-not-allowed behavior, dependency blocking, and optimistic revision conflicts are implemented in [`backend/app/conversations.py`](../../backend/app/conversations.py). Proposal, confirmation, revision, replay, undo, no-evidence, timeout, and loop-limit routes remain pending.