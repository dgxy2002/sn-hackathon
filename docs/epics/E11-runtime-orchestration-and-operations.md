# E11 - Runtime Orchestration and Operations

| Field | Value |
|---|---|
| Primary owner | Jana |
| Priority | P0 |
| Status | In progress |
| Outcome | A bounded local-first runtime coordinates typed capability calls, required Bedrock grounded explanation, and one continuously running scraper while remaining deployable to AWS through configuration. |

## Scope

- Run the coordinator with the backend container and expose `POST /invocations`.
- Select Amazon Bedrock through `LLM_PROVIDER`, `BEDROCK_MODEL_ID`, and `AWS_REGION` for grounded explanation; keep OpenRouter independently configured for E04 policy extraction.
- Define coordinator states, terminal outcomes, tool allowlists, retry policy, and loop counters.
- Invoke E03, E04, E06, and E07 through E10 contracts and validate every transition.
- Resolve conversational intents and sequence only allowlisted typed read, presentation, proposal, deterministic-rerun, revision, and undo tools.
- Use the model only for document extraction, focused information gathering, and grounded explanation; eligibility, arithmetic, and ranking remain deterministic in E07.
- Emit ordered model, tool, validation, metric, warning, and error events.
- Coordinate one continuous scraper lifecycle: identify due source, acquire singleton lease, fetch, parse, normalize, hash/version, upsert, optionally chunk/index, log, update `next_scrape_due`, retry with bounded backoff, and publish health/freshness metrics.
- Run one scraper container in Docker Compose; later run one ECS Fargate service task with desired count one and retain the database lease.
- Use local `.env` values now and the same environment names from AWS Secrets Manager or task configuration later.
- Require Amazon Bedrock for live E11 explanation while retaining a credential-free fixture adapter; keep AgentCore deferred.

## Repository evidence

- [`backend/app/model_gateway.py`](../../backend/app/model_gateway.py) calls the Bedrock Converse API with the immutable E07 recommendation and compact E03 personalization context, validates the response, and rejects unknown plan IDs.
- [`backend/app/orchestration.py`](../../backend/app/orchestration.py) records explanation events and token usage and returns a typed failed run when Bedrock is unavailable without changing the deterministic result.
- [`backend/tests/test_model_gateway.py`](../../backend/tests/test_model_gateway.py) verifies immutable ranking, model-output rejection, prompt context, and token telemetry with a mocked Bedrock client.

## Requirements traceability

- **URS:** [URS-FR-006, URS-FR-011, URS-FR-012, URS-FR-015, URS-FR-017, URS-FR-018, URS-FR-020, URS-FR-021, URS-FR-022, URS-FR-024, URS-FR-025, URS-FR-027, URS-FR-028, URS-FR-029, URS-FR-030, URS-FR-032, URS-NFR-003, URS-NFR-007, URS-NFR-010, URS-NFR-011, URS-NFR-012, URS-NFR-013, URS-NFR-014, URS-NFR-015, URS-NFR-017, URS-NFR-018, URS-NFR-019](../urs/URS.md)
- **PRD:** [PRD-FR-013, PRD-FR-020, PRD-FR-021, PRD-FR-022, PRD-FR-023, PRD-FR-027, PRD-FR-030, PRD-FR-033, PRD-FR-034, PRD-FR-035, PRD-FR-036, PRD-FR-038, PRD-NFR-005, PRD-NFR-010, PRD-NFR-013, PRD-NFR-014, PRD-NFR-017, PRD-NFR-019, PRD-NFR-021, PRD-NFR-022, PRD-NFR-023, PRD-NFR-024, PRD-NFR-026](../prd/PRD.md)
- **Backlog:** [E11 tickets](../backlog/E11-runtime-orchestration-and-operations.md)

## State model

```mermaid
stateDiagram-v2
    [*] --> ValidateInput
    ValidateInput --> NeedUserInput: critical profile data missing
    ValidateInput --> ExtractPolicy: policy supplied
    ValidateInput --> BuildProfile: no policy supplied
    ExtractPolicy --> ReviewExtraction: unresolved or low confidence
    ExtractPolicy --> BuildProfile: accepted extraction
    ReviewExtraction --> BuildProfile: user confirms corrections
    BuildProfile --> RetrieveEvidence
    RetrieveEvidence --> Unsupported: no current evidence
    RetrieveEvidence --> Decide: evidence available
    Decide --> InsufficientData: critical inputs missing
    Decide --> Explain: immutable decision ready
    Explain --> Complete
    NeedUserInput --> [*]
    Unsupported --> [*]
    InsufficientData --> [*]
    Complete --> [*]
```

## Definition of done

- [ ] Docker Compose starts healthy backend, scraper, database, and configured local object-store services without AWS access.
- [x] The invocation contract accepts a versioned request and returns final state, result, ordered events, and run metrics.
- [x] Only declared tools execute, every result validates before transition, and raw documents remain outside explanation prompts.
- [x] Conversational tool policy validates action schema, target, base version, preconditions, idempotency, confirmation, allowed summary regions, and terminal state.
- [x] Model output never executes as page code, selectors, coordinates, SQL, arbitrary URLs, or direct canonical decision values.
- [ ] Every loop and retry path has a tested cap with `LOOP_LIMIT_REACHED` as a terminal failure.
- [ ] Bedrock calls record provider, exact model or inference-profile ID, prompt version, tokens, latency, estimated cost, and outcome. Provider, model, prompt, token, latency, and outcome fields are implemented; priced cost evaluation remains open.
- [x] Explanation uses the immutable E07 decision contract and cannot mutate rank, eligibility, evidence, or numbers.
- [x] Live, cached, synthetic, and simulated adapters emit the same contracts and visible mode labels.
- [ ] Exactly one scraper loop runs, retains a database lease, records source freshness, and recovers from bounded failures.
- [ ] The AWS topology maps images to ECR/ECS, PostgreSQL to RDS, snapshots to S3, secrets to Secrets Manager, and logs/metrics/alarms to CloudWatch.
- [ ] Normal, no-policy, missing-information, no-evidence, dependency-failure, changed-goal, and stale-source scenarios reach their expected terminal states.

**Acceptance evidence:** [Integrated runtime and browser acceptance](../evaluation/2026-08-28-integrated-runtime-browser-acceptance.md) and [Bedrock and personalization integration](../evaluation/2026-09-03-bedrock-personalization-integration.md). A credentialed live-model acceptance run, priced cost evaluation, full loop-limit acceptance, scraper freshness cycles, changed-goal coverage, and AWS deployment remain open.

## POC boundary

This epic coordinates capability calls and runtime lifecycle; it does not grant a model arbitrary application or browser control and does not require AWS to run locally. Production identity, durable conversation memory, multi-region availability, secret rotation, and incident response remain in E09.