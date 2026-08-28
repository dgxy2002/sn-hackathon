# E10 - Backend API and POC Persistence

| Field | Value |
|---|---|
| Primary owner | Tim |
| Priority | P0 |
| Status | In progress |
| Outcome | Every frontend and model-assisted capability can be invoked through a containerized local API with validated contracts, typed failures, portable PostgreSQL/object-store adapters, and disposable synthetic POC state. |

## Scope

- Create the backend application shell, health route, capability manifest, Docker image, and Docker Compose service.
- Load local configuration from an uncommitted `.env` documented by `.env.example`.
- Publish versioned request, response, event, and error schemas for profiles, extraction, evidence, recommendations, conversations, proposals, actions, summary revisions, and runs.
- Expose capability routes while preserving ownership of business logic in E03, E04, E06, E07, and E11.
- Integrate E06 first through the existing Supabase/PostgREST implementation and a deterministic fixture fallback behind one evidence-service interface.
- Maintain anonymous POC sessions, profile versions, extraction reviews, recommendation results, conversations, proposals, actions, summary revisions, and run records using replaceable repositories.
- Provide fixture and local PostgreSQL/pgvector adapters by default plus an S3-compatible object-store adapter where permitted snapshots are needed.
- Preserve the same environment-variable contract when moving to ECS Fargate, RDS PostgreSQL, Amazon S3, and AWS Secrets Manager.
- Apply validation, idempotency, timeout, correlation-ID, and dependency-failure behavior consistently.

## Requirements traceability

- **URS:** [URS-FR-004, URS-FR-005, URS-FR-006, URS-FR-007, URS-FR-008, URS-FR-010, URS-FR-011, URS-FR-015, URS-FR-017, URS-FR-020, URS-FR-021, URS-FR-024, URS-FR-027, URS-FR-030, URS-FR-031, URS-FR-032, URS-NFR-005, URS-NFR-010, URS-NFR-011, URS-NFR-012, URS-NFR-013, URS-NFR-014, URS-NFR-015, URS-NFR-016, URS-NFR-017, URS-NFR-020](../urs/URS.md)
- **PRD:** [PRD-FR-014, PRD-FR-015, PRD-FR-016, PRD-FR-018, PRD-FR-019, PRD-FR-021, PRD-FR-026, PRD-FR-029, PRD-FR-032, PRD-FR-033, PRD-FR-036, PRD-FR-037, PRD-FR-038, PRD-NFR-008, PRD-NFR-010, PRD-NFR-011, PRD-NFR-012, PRD-NFR-017, PRD-NFR-018, PRD-NFR-019, PRD-NFR-020, PRD-NFR-021, PRD-NFR-023, PRD-NFR-025, PRD-NFR-026](../prd/PRD.md)
- **Backlog:** [E10 tickets](../backlog/E10-backend-api-and-poc-persistence.md)

## API ownership boundary

E10 owns transport, schema validation, repositories, and common errors. It does not own profile semantics, OCR models, retrieval ranking, insurance decision rules, or orchestration policy; those remain in their capability epics.

## Definition of done

- [x] A documented command starts the backend and `GET /health` and `GET /v1/capabilities` report version and adapter modes.
- [ ] Docker Compose starts the API with healthy PostgreSQL/pgvector and optional local object-store dependencies.
- [x] `.env.example` documents `APP_ENV`, `DATABASE_URL`, object-store settings, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, provider modes, and scrape freshness settings without real secrets.
- [ ] Profile, extraction, evidence-search, recommendation, invocation, conversation, proposal-confirmation, summary-revision, undo, and run-inspection routes publish versioned schemas and typed errors.
- [ ] `POST /v1/evidence/search` returns the same read-only contract from Supabase and fixture adapters, including source approval, evidence state, distinct date fields, provenance, and explicit no-evidence outcomes.
- [ ] Complete, incomplete, invalid, no-evidence, and dependency-failure fixtures pass API contract tests.
- [ ] Anonymous synthetic sessions can retain profile versions, extraction corrections, recommendation results, conversations, action traces, summary revisions, and run events for replay and undo.
- [ ] Repeated mutating requests follow documented idempotency rules and do not create duplicate active records.
- [ ] Uploaded document bytes are deleted after extraction by default and the POC stores no real customer data.
- [ ] The frontend can complete the normal fixture scenario through the API rather than embedded view data.
- [ ] The AWS mapping injects secrets through Secrets Manager and swaps only endpoints and adapters for ECS, RDS, and S3.
- [ ] The API image exposes health checks, handles termination, logs to stdout/stderr, and runs as non-root where practical.

## POC boundary

Mock identity and disposable synthetic state are sufficient. Supabase is the first E06 integration adapter because it is already implemented, but this temporary delivery choice does not replace the local PostgreSQL/pgvector target or complete the Docker Compose DOD. Production authentication, tenant isolation, encryption operations, retention controls, backups, and public-service reliability remain in E09.