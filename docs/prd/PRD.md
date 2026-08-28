# Product Requirements Document

## Document control

| Field | Value |
|---|---|
| Product | CoverCheck SG |
| Version | 1.3 |
| Status | POC baseline |
| Date | 26 August 2026 |
| Product objective | Demonstrate an evidence-backed insurance-readiness journey for first-time working adults in Singapore |
| User requirements | [URS v1.0](../urs/URS.md) |

## 1. Product summary

CoverCheck SG is a web-based educational assistant that moves a first-time working adult from curiosity to an explainable insurance comparison. The POC combines a readiness quiz, structured profile, policy extraction demonstration, grounded product retrieval, deterministic decision support, and plain-language explanations.

## 2. Goals

1. Help users identify what they do and do not know about inherited and existing insurance.
2. Gather enough explicit context to calculate protection gaps without inferring sensitive facts.
3. Demonstrate that policy fields and product claims can retain confidence, provenance, and dates.
4. Produce reproducible synthetic recommendations with reasons, alternatives, and safe failure states.
5. Show measurable model and tool activity through OpenRouter `5.6 Luna` within a five-minute demo.
6. Provide a contract-first backend that allows all four capability owners to integrate and test independently.
7. Make every data, model, prompt, tool, and decision version inspectable and replayable for evaluation.
8. Run the complete POC locally with Docker Compose before introducing AWS runtime dependencies.
9. Reuse the same container images and service contracts when deploying to AWS later.
10. Let users investigate, reshape, and replay their final comparison through a grounded conversational agent without weakening deterministic decision controls.

## 3. Non-goals

- Regulated financial advice or insurance transactions.
- Recommending policy cancellation or replacement.
- Production identity, sensitive-data storage, or public launch readiness.
- Exhaustive provider coverage or live scraping during the judged demo.
- Unqualified claims of independence, unbiasedness, or population representativeness.
- Amazon Bedrock or AgentCore as a prerequisite for local development; these remain optional future adapters if credits and organizer requirements justify them.

## 4. Success measures

| Area | POC success measure |
|---|---|
| Quiz | At least 4 of 5 observed target users complete it and can explain the result. |
| Extraction | At least 0.90 key-field exact match or F1 on labelled synthetic documents; all low-confidence values are reviewable. |
| Retrieval | Expected reviewed source appears in the top five for at least 90% of fixed queries; all shown claims include a source and date. |
| Decision support | Zero hard-rule violations across at least 20 reviewed synthetic profiles; at least 90% top-category agreement with prewritten ground truth. |
| Explanation | Every result includes a reason, trade-off, assumptions, missing data, and evidence status. |
| Reliability | At least 95% first-pass schema validation and zero runs beyond the configured loop cap. |
| Demo | One normal scenario and one changed-goal scenario complete within the rehearsed five-minute story. |

## 5. Functional product requirements

| ID | Product requirement | Priority | Related URS | Acceptance criteria |
|---|---|---:|---|---|
| PRD-FR-001 | Provide a responsive single-page journey from landing through recommendation and adviser verification. | P0 | URS-FR-001, URS-FR-004, URS-FR-013, URS-FR-014 | All POC views are reachable without a backend and preserve clear state and trust messaging. |
| PRD-FR-002 | Implement a deterministic readiness quiz and dimension-level result. | P0 | URS-FR-001, URS-FR-002 | Fixed answer fixtures produce stable scores and known/unclear result rows. |
| PRD-FR-003 | Render a contextual pilot benchmark without unsupported population claims. | P0 | URS-FR-003 | Cohort label, age range, sample size, and collection date are displayed. |
| PRD-FR-004 | Provide a mock account, consent transition, and structured minimum user profile. | P0 | URS-FR-004, URS-FR-005 | The user can complete onboarding and see how the collected fields affect analysis. |
| PRD-FR-005 | Represent profile versions, explicit unknowns, missing-field prompts, and material changes. | P1 | URS-FR-005, URS-FR-006, URS-FR-012 | Decision-critical unknowns are preserved and material changes trigger an explained rerun. |
| PRD-FR-006 | Accept synthetic policy documents and return reviewable extracted fields with confidence and page evidence. | P1 | URS-FR-007, URS-FR-008 | At least three labelled synthetic pages pass through the configured OpenRouter extraction path and allow correction. |
| PRD-FR-007 | Ingest and normalize permitted product sources with retrieval dates, effective dates, versions, and scrape outcomes. | P1 | URS-FR-010, URS-FR-011 | At least two providers in one category produce typed product and evidence records. |
| PRD-FR-008 | Retrieve small dated evidence records for comparison queries using filtered semantic search. | P1 | URS-FR-010, URS-FR-011, URS-FR-015 | Fixed queries meet top-five retrieval targets and unsupported queries return no evidence. |
| PRD-FR-009 | Calculate gaps, apply hard constraints, rank eligible synthetic plans, and support no-recommendation outcomes. | P0 | URS-FR-009, URS-FR-010, URS-FR-015 | Reviewed test profiles meet the decision correctness targets without LLM-authored eligibility. |
| PRD-FR-010 | Generate a grounded explanation from the fixed decision result without changing rank or eligibility. | P0 | URS-FR-011, URS-FR-014 | Output contains reasons, alternatives, trade-offs, assumptions, confidence, and evidence IDs. |
| PRD-FR-011 | Re-run analysis after material profile or policy changes and explain the delta. | P1 | URS-FR-012 | Changed-goal and changed-dependant scenarios produce a stated reason for any result change. |
| PRD-FR-012 | Surface educational boundaries, synthetic labels, source links, and MAS adviser verification throughout the journey. | P0 | URS-FR-013, URS-FR-014 | No screen implies transaction capability or licensed advice. |
| PRD-FR-013 | Integrate the smallest reliable model-assisted slices through a runtime-neutral coordinator using OpenRouter locally. | P0 | URS-FR-008, URS-FR-010, URS-FR-011, URS-FR-017, URS-FR-018, URS-FR-022, URS-NFR-010, URS-NFR-011 | One end-to-end run returns schema-valid extraction, evidence, deterministic decision, grounded explanation, and run metrics. |
| PRD-FR-014 | Expose a versioned POC backend API for health, capability metadata, profiles, extraction, evidence search, recommendations, orchestration runs, and run inspection. | P0 | URS-FR-017, URS-NFR-010, URS-NFR-011 | The API publishes request, response, and typed error contracts and can be exercised locally without the frontend. |
| PRD-FR-015 | Maintain POC session state and versioned synthetic profiles, including consent state, explicit unknowns, provenance, and material-change history. | P1 | URS-FR-004, URS-FR-005, URS-FR-006, URS-FR-012, URS-FR-017 | A profile can be created, read, versioned, and supplied to decision support without conflating unknown, zero, and not-applicable values. |
| PRD-FR-016 | Provide an extraction job interface that accepts a consented synthetic document, reports status, returns field-level confidence and page evidence, and accepts reviewed corrections. | P1 | URS-FR-007, URS-FR-008, URS-FR-017 | The same extraction contract is returned by real and fixture adapters, and corrected values retain original and reviewed provenance. |
| PRD-FR-017 | Operate an allowlisted, idempotent ingestion pipeline that records source approval, versions, effective dates, retrieval dates, hashes, and scrape outcomes. | P1 | URS-FR-016, URS-NFR-004, URS-NFR-012 | Reingesting unchanged content does not duplicate active records, and changed product versions remain auditable. |
| PRD-FR-018 | Expose filtered evidence search by user need, product category, eligibility attributes, and effective date, returning top-k typed evidence or an explicit no-evidence result. | P1 | URS-FR-010, URS-FR-011, URS-FR-015, URS-FR-017 | Results include score, source URL, quoted span, provider, product, field, value, and retrieval or effective date. |
| PRD-FR-019 | Expose deterministic gap-analysis and recommendation evaluation using versioned profile, plan, and ruleset inputs. | P0 | URS-FR-009, URS-FR-010, URS-FR-011, URS-FR-015, URS-FR-017 | The service returns gaps, eligible and excluded plans, reason codes, fit components, assumptions, missing fields, confidence, and evidence IDs. |
| PRD-FR-020 | Provide one coordinator entrypoint that invokes personalization, extraction, retrieval, decision, and explanation capabilities according to explicit state transitions. | P0 | URS-FR-017, URS-FR-018, URS-NFR-010, URS-NFR-011 | Every transition validates its input, emits an event, and stops on defined insufficient-data, no-evidence, or tool-failure states. |
| PRD-FR-021 | Support live-approved, cached, synthetic, and simulated adapters behind the same capability contracts. | P1 | URS-FR-020, URS-NFR-004, URS-NFR-006 | Adapter mode is configuration-driven and visible in API output and the UI; fallback never masquerades as live data. |
| PRD-FR-022 | Record and expose orchestration run events and aggregate metrics for schema validation, tools, models, prompts, retries, iterations, latency, tokens, estimated cost, and errors. | P0 | URS-FR-018, URS-NFR-007, URS-NFR-013 | A reviewer can reconstruct the run sequence and export metrics for the deck without reading application logs. |
| PRD-FR-023 | Package the coordinator with the backend container and expose a local `POST /invocations` entrypoint that remains portable to ECS Fargate. | P0 | URS-FR-017, URS-FR-018, URS-FR-024 | Provider, model, allowed tools, runtime configuration, and local invocation instructions are documented and verified. |
| PRD-FR-024 | Maintain versioned synthetic fixtures and prewritten ground truth for profiles, plans, rules, policy pages, retrieval queries, and recommendation outcomes. | P0 | URS-FR-019, URS-NFR-003, URS-NFR-013 | Fixtures cover complete, incomplete, invalid, no-evidence, and material-change scenarios and identify reviewer and review date. |
| PRD-FR-025 | Evaluate the configured OpenRouter policy-extraction path against labelled synthetic pages and publish measured field accuracy, latency, tokens, estimated cost, context size, and corrections. | P1 | URS-FR-008, URS-FR-018, URS-FR-019, URS-FR-022 | The report includes provider, exact model slug, run date, pricing assumptions, and no unsupported savings claim. |
| PRD-FR-026 | Provide one Docker Compose topology containing the web, backend API, one continuous scraper, PostgreSQL with pgvector, and an optional S3-compatible local object store. | P0 | URS-FR-021, URS-NFR-006, URS-NFR-015, URS-NFR-016, URS-NFR-017 | A documented local command builds and starts all required services, and health checks reach a ready state without AWS access. |
| PRD-FR-027 | Use an OpenRouter provider adapter configured for `5.6 Luna` for language tasks and direct policy PDF/image ingestion, OCR, and structured extraction. | P0 | URS-FR-008, URS-FR-022, URS-NFR-013 | The provider, exact model slug, prompt version, token usage, and extraction metrics are recorded for every call. |
| PRD-FR-028 | Support an explicit no-policy path that bypasses document extraction and preserves existing-policy fields as unknown. | P0 | URS-FR-023, URS-FR-006, URS-FR-015 | Users can continue without upload, no coverage is invented, and recommendation rules handle the resulting uncertainty. |
| PRD-FR-029 | Package web, API, and scraper as environment-neutral images that can be pushed to ECR and run on ECS Fargate. | P1 | URS-FR-024, URS-NFR-015, URS-NFR-017 | AWS deployment uses the same image digests tested locally and supplies only environment-specific configuration and managed-service endpoints. |
| PRD-FR-030 | Operate exactly one continuous scraper loop that leases work, refreshes due approved sources, versions changed content, records outcomes, and retries bounded failures. | P1 | URS-FR-016, URS-FR-025, URS-NFR-012, URS-NFR-017 | Docker Compose runs one scraper container; ECS later runs a Fargate service with desired count one plus a database-backed singleton lease. |
| PRD-FR-031 | Require an approved grounded formulation document before enabling plan ranking. | P0 | URS-FR-009, URS-FR-010, URS-FR-011, URS-FR-026, URS-NFR-003 | The document defines formulas, inputs, units, constraints, weights, reason codes, missing-data behavior, replacement safeguards, worked examples, and reviewer sign-off. |
| PRD-FR-032 | Embed an `Ask CoverCheck` conversational agent in the final summary page with contextual follow-ups, suggested tasks, progress, and cited responses. | P1 | URS-FR-027, URS-FR-028, URS-NFR-021 | The panel retains current-session context and exposes idle, planning, acting, waiting-for-confirmation, completed, unsupported, and failed states. |
| PRD-FR-033 | Convert each user request into one or more schema-valid intents and allowlisted typed tools. | P1 | URS-FR-029, URS-FR-030, URS-FR-032, URS-NFR-018 | Supported intents include `ANSWER_QUESTION`, `SEARCH_PLANS`, `FOCUS_SECTION`, `FILTER_COMPARISON`, `PROPOSE_PROFILE_PATCH`, `PROPOSE_EXTRACTION_PATCH`, `RUN_RECOMMENDATION`, `APPLY_SUMMARY_REVISION`, and `UNDO_REVISION`. |
| PRD-FR-034 | Search and compare additional plans only from the approved E06 catalogue. | P1 | URS-FR-028, URS-FR-031 | Results preserve eligibility, source, effective or retrieval date, freshness, evidence spans, and synthetic status; unsupported requests return no evidence. |
| PRD-FR-035 | Let presentation-only actions navigate, focus, filter, sort, and temporarily alter the visible comparison without confirmation. | P1 | URS-FR-029, URS-FR-031 | The page visibly follows the agent's action trace while canonical profile and recommendation versions remain unchanged. |
| PRD-FR-036 | Preview and confirm proposed profile, comparison-membership, or extracted-policy changes before applying them. | P1 | URS-FR-030, URS-FR-031 | The preview identifies old and proposed values, affected calculations, required review, evidence impact, and available cancel action. |
| PRD-FR-037 | After confirmation, version changed inputs, rerun E07 deterministically, and replace affected summary sections from the validated result contract. | P1 | URS-FR-012, URS-FR-031, URS-NFR-019 | Updated gaps, eligibility, rankings, comparison rows, assumptions, and explanation share one revision ID and a visible before/after delta. |
| PRD-FR-038 | Preserve an ordered conversational action trace, revision history, and undo behavior for the current POC session. | P1 | URS-FR-032, URS-NFR-020 | A reviewer can replay tool calls and revisions, while the user can undo an applied revision through a new deterministic rerun or restore. |

## 6. Non-functional product requirements

| ID | Product requirement | Priority | Related URS | Acceptance criteria |
|---|---|---:|---|---|
| PRD-NFR-001 | The core journey shall be responsive, keyboard operable, and respectful of reduced-motion preferences. | P0 | URS-NFR-002 | Desktop and mobile checks pass and the main path is keyboard accessible. |
| PRD-NFR-002 | Numerical decisions shall be deterministic, testable, and isolated from LLM explanation generation. | P0 | URS-NFR-003 | The same versioned inputs and ruleset produce the same decision contract. |
| PRD-NFR-003 | Evidence shall retain source URL, effective or retrieval date, synthetic status, and field or chunk provenance. | P0 | URS-NFR-004 | Every displayed product fact resolves to evidence or is visibly synthetic. |
| PRD-NFR-004 | The POC shall use synthetic documents, minimize profile data, and keep secrets outside source and browser bundles. | P0 | URS-NFR-005 | The judged demo uses no real customer or sensitive medical data. |
| PRD-NFR-005 | Agent runs shall use typed contracts, restricted tools, hard loop caps, and usage metrics. | P1 | URS-FR-018, URS-NFR-007, URS-NFR-010, URS-NFR-011 | Invalid contracts fail visibly and no run exceeds its configured cap. |
| PRD-NFR-006 | The demo shall build from documented setup, use frozen fixtures where needed, and include a recorded fallback. | P0 | URS-NFR-006 | Clean build, normal scenario, changed-goal scenario, and backup recording are verified. |
| PRD-NFR-007 | Production identity, privacy, security, resilience, monitoring, and regulatory controls shall remain a tracked deferred scope. | P3 | URS-NFR-008 | E09 retains an explicit DOD and is not treated as complete for public use. |
| PRD-NFR-008 | Shared profile, plan, evidence, extraction, recommendation, and run-metric contracts shall be versioned. | P0 | URS-FR-017, URS-FR-019, URS-NFR-003, URS-NFR-004, URS-NFR-007, URS-NFR-011, URS-NFR-013 | Integrated components validate the same frozen schemas before the demo. |
| PRD-NFR-009 | Singapore terminology and peer-comparison guardrails shall be applied consistently. | P0 | URS-NFR-001, URS-NFR-009 | SGD, official Singapore references, pilot labels, and non-shaming copy are used. |
| PRD-NFR-010 | API boundaries shall reject incompatible schema versions and return stable machine-readable error codes with a correlation or run ID. | P0 | URS-NFR-010, URS-NFR-011 | Validation, missing-data, unsupported, conflict, dependency, timeout, and internal failures are distinguishable. |
| PRD-NFR-011 | Mutating POC operations shall be idempotent where retried, with bounded timeouts and retries and no duplicate active records. | P1 | URS-NFR-010, URS-NFR-012 | Replayed profile, extraction, ingestion, and run requests have documented idempotency behavior. |
| PRD-NFR-012 | POC persistence shall separate public product evidence from synthetic session data and shall not retain uploaded document bytes by default. | P0 | URS-NFR-005, URS-NFR-008 | Storage inventory and retention behavior are documented; the demo uses only synthetic personal and policy data. |
| PRD-NFR-013 | Every run shall record contract, fixture, profile, ruleset, prompt, model, tool, and source versions needed for replay. | P0 | URS-NFR-013 | Two executions with the same deterministic inputs reproduce the same decision contract. |
| PRD-NFR-014 | Resolved provider and model IDs shall be configuration-driven and recorded per run; tool allowlists shall be explicit; tool results shall be small and typed; and each loop shall have a hard state counter. | P0 | URS-NFR-007, URS-NFR-010, URS-NFR-013 | No run exceeds its cap, unlisted tools cannot execute, and large source documents remain outside explanation context. |
| PRD-NFR-015 | Evidence freshness rules shall identify stale, superseded, unverified, and unsupported product data before recommendation use. | P1 | URS-NFR-004, URS-NFR-012 | Stale or version-conflicted evidence is excluded or surfaced as an explicit limitation. |
| PRD-NFR-016 | Evaluation outputs shall be generated from predeclared fixtures and ground truth rather than self-grading model output. | P0 | URS-FR-019, URS-NFR-003, URS-NFR-013 | Test data, expected outcomes, reviewer, ruleset, and run results are independently inspectable. |
| PRD-NFR-017 | The backend shall provide deterministic fixture adapters so the full judged journey remains runnable when OCR, source websites, vector services, or model endpoints are unavailable. | P0 | URS-FR-020, URS-NFR-006, URS-NFR-010 | A fallback run completes with visible simulated or cached labels and the same response schemas. |
| PRD-NFR-018 | Local configuration and secrets shall be loaded from `.env`, with `.env.example` documenting names and safe placeholders. | P0 | URS-NFR-005, URS-NFR-014 | `.env` is ignored by version control and no secret is embedded in source, Docker images, Compose files, logs, or frontend bundles. |
| PRD-NFR-019 | AWS tasks shall obtain secrets from AWS Secrets Manager and non-secret configuration from task definitions or Parameter Store. | P1 | URS-FR-024, URS-NFR-014, URS-NFR-015 | The application uses the same environment-variable names locally and on AWS and requires no code change during migration. |
| PRD-NFR-020 | Local and AWS data services shall use portable interfaces: PostgreSQL/pgvector locally and RDS PostgreSQL/pgvector on AWS; S3-compatible storage locally and Amazon S3 on AWS. | P1 | URS-NFR-015, URS-NFR-016 | Migrations, queries, and object-store calls pass against both adapters without environment-specific business logic. |
| PRD-NFR-021 | Containers shall be immutable, run as non-root where practical, expose health checks, handle termination signals, and write logs to stdout/stderr. | P0 | URS-NFR-017 | Docker Compose and ECS can restart failed processes and CloudWatch can collect AWS task logs without application-specific log shipping. |
| PRD-NFR-022 | OpenRouter and all external dependencies shall be selected through provider interfaces and environment variables. | P0 | URS-FR-020, URS-FR-022, URS-NFR-015 | Provider changes do not alter profile, extraction, evidence, recommendation, or run contracts. |
| PRD-NFR-023 | Conversational tools shall validate authorization, input schema, preconditions, idempotency, and permitted summary regions before execution. | P1 | URS-NFR-010, URS-NFR-011, URS-NFR-018 | Invalid, stale, disallowed, or conflicting actions terminate visibly without a partial canonical update. |
| PRD-NFR-024 | Model output shall never be executed as HTML, JavaScript, selectors, coordinates, SQL, or an unregistered tool call. | P0 | URS-NFR-005, URS-NFR-018, URS-NFR-019 | The frontend renders trusted result schemas and the backend rejects undeclared intents, properties, tools, and targets. |
| PRD-NFR-025 | Any mutation of decision inputs or reviewed extraction fields shall require explicit user confirmation and produce an auditable version. | P0 | URS-FR-030, URS-NFR-019 | Navigation and temporary presentation actions may run immediately, but no canonical input changes before confirmation. |
| PRD-NFR-026 | Conversation context shall use bounded current-session history and compact typed state rather than unbounded transcripts or raw documents. | P1 | URS-NFR-007, URS-NFR-020 | Turn, token, tool, latency, and history-size caps are enforced and fixture fallback remains available. |
| PRD-NFR-027 | Dynamic summary changes shall preserve accessibility, visible focus, reduced-motion support, and stable layout dimensions. | P1 | URS-NFR-002, URS-NFR-021 | Action progress, confirmation, changed regions, citations, and undo are keyboard operable and announced without incoherent layout shifts. |

## 7. Capability boundaries

| Capability | Responsibility | Must not do |
|---|---|---|
| POC backend API | Validate contracts, route requests, manage synthetic session state, and return typed failures. | Contain hidden decision rules or persist real customer documents. |
| Readiness and personalization | Gather explicit context, preserve unknowns, and identify missing information. | Infer sensitive facts that can be asked directly. |
| Extraction | Convert a policy document into fields, confidence, and page evidence. | Guess low-confidence values. |
| Source ingestion | Acquire permitted content, normalize versions, and record freshness and failures. | Bypass source approval or silently overwrite product history. |
| Information retrieval | Return small, dated product evidence records. | Make the final recommendation or merge product versions silently. |
| Decision support | Calculate gaps, enforce eligibility, and rank plans reproducibly. | Delegate hard rules or arithmetic to an LLM. |
| Explanation | Express the fixed result in clear language. | Change rank, eligibility, evidence, or numerical results. |
| Agent orchestration | Sequence capability calls, validate state transitions, restrict tools, and record run events. | Reimplement capability logic or continue after a terminal failure. |
| Conversational summary agent | Interpret final-page requests, operate allowlisted page tools, explore approved alternatives, request confirmation, and present validated revisions. | Execute arbitrary page code, search unapproved sources, or directly author canonical decision values. |
| Evaluation and release | Replay fixtures, aggregate independently reviewed metrics, and package the judged demo. | Let a model grade itself or report aspirational results as measured results. |

## 8. Domain rules and field coverage

### Insurance Readiness Score

The target score is a transparent 0-100 measure of readiness to make an informed decision, not wealth, risk, or personal worth.

| Dimension | Weight | Minimum evidence |
|---|---:|---|
| Coverage visibility | 30 | Policy name, ownership, payer, benefits, premiums, term, riders, and exclusions |
| Protection foundations | 25 | Government and employer cover plus death/TPD, critical illness, hospital, disability-income, and dependant needs |
| Affordability and resilience | 25 | Premium burden, emergency fund, debts, cash flow, and ability to maintain premiums |
| Action literacy | 20 | Compare beyond price, verify advisers, understand free-look rights, and avoid unsafe replacement |

Every component exposes its source and calculation. `unknown` is excluded or flagged according to the published formula and never converted to `no`.

### Singapore educational benchmarks

| Benchmark | Reference value | POC use |
|---|---:|---|
| Emergency fund | 3-6 months of expenses | Resilience indicator, not an eligibility rule |
| Death and TPD protection | 9 times annual income | Transparent gap reference |
| Critical illness protection | 4 times annual income | Transparent gap reference |
| Protection spending | At most 15% of income | Affordability warning threshold |
| Retirement and other goal investing | At least 10% of income | Educational context when relevant |
| General saving | At least 20% of monthly income | Educational context, not a product recommendation |

### Minimum onboarding coverage

The profile covers life stage, residency, employment and expected changes, goals and horizons, income, expenses, savings, assets, liabilities, dependants and support duration, inherited and current policies, MediShield Life, Integrated Shield Plans, CareShield Life, DPS and HPS where relevant, employer benefits and expiry, health-care preferences, product preferences, sustainable premium budget, and investment risk and knowledge only when investment-linked products are in scope.

### Extraction target fields

| Group | Fields |
|---|---|
| Identity | Insurer, product, policy type, policy owner, life assured |
| Benefits | Benefit name, sum assured, coverage amount, coverage basis |
| Premium | Amount, currency, frequency, payment period |
| Duration | Issue or effective date, coverage term, maturity, renewable state |
| Add-ons | Riders and rider terms |
| Limitations | Exclusions, deductibles, co-insurance, caps, waiting periods |
| Replacement context | Surrender implications and other document-stated consequences |

Each extracted field carries confidence and page or region evidence. Missing values remain unresolved.

## 9. Backend product model

### Component ownership

| Component | Owner epic | POC responsibility |
|---|---|---|
| Browser application | [E01](../epics/E01-poc-web-experience.md) | Collect inputs and render state, evidence, confidence, and results. |
| POC backend API and repositories | [E10](../epics/E10-backend-api-and-poc-persistence.md) | Validate schemas, expose capability routes, manage synthetic session state, and translate failures. |
| Readiness and profile service | [E02](../epics/E02-readiness-quiz-and-peer-benchmark.md), [E03](../epics/E03-user-profile-and-personalization.md) | Score readiness, normalize profile fields, preserve unknowns, and version material changes. |
| Policy document extraction adapter | [E04](../epics/E04-policy-ocr-and-extraction.md) | Use OpenRouter or a fixture adapter to read what the user already owns and return reviewable fields with provenance. |
| Source ingestion | [E05](../epics/E05-source-data-ingestion-poc.md) | Continuously collect approved insurer offerings through bounded fetch, parse, normalize, hash, and upsert behavior. |
| Insurance evidence retrieval | [E06](../epics/E06-insurance-retrieval-and-rag.md) | Ingest approved sources and return dated evidence records or no-evidence. |
| Decision service | [E07](../epics/E07-explainable-decision-support.md) | Calculate gaps, apply hard constraints, rank synthetic plans, and emit an immutable result. |
| Runtime and model coordinator | [E11](../epics/E11-runtime-orchestration-and-operations.md) | Sequence tools, call configured OpenRouter adapters, enforce state and tool policy, coordinate the scraper lifecycle, and emit run events. |
| Conversational summary agent | [E12](../epics/E12-conversational-summary-agent.md) | Answer contextual questions, visibly operate typed page tools, explore approved alternatives, and apply confirmed deterministic summary revisions. |
| Evaluation and demo release | [E08](../epics/E08-integrated-demo-and-evaluation.md) | Accept the integrated system, replay scenarios, aggregate metrics, and prepare the judged demo. |
| Production controls | [E09](../epics/E09-productionisation-and-security.md) | Deferred identity, sensitive-data, resilience, security, privacy, and regulatory hardening. |

### Minimum API surface

The route names are a POC contract and may be implemented in one service. Capability logic remains owned by its epic.

| Method and route | Owner | Purpose | Successful result |
|---|---|---|---|
| `GET /health` | E10 | Process health and dependency summary | Service version, status, and dependency modes |
| `GET /v1/capabilities` | E10 | Discover contract versions and live/cached/synthetic/simulated modes | Capability and schema-version map |
| `POST /v1/sessions` | E10 | Create an anonymous synthetic POC session | Session ID, consent state, and expiry |
| `POST /v1/profiles` | E03 through E10 | Create or version a normalized profile | Profile version, missing fields, and provenance |
| `GET /v1/profiles/{profile_id}` | E10 | Load a synthetic POC profile | Current profile version and history summary |
| `POST /v1/extractions` | E04 through E10 | Submit a consented synthetic document or fixture | Extraction ID, status, fields, warnings, and metrics |
| `PATCH /v1/extractions/{extraction_id}` | E04 through E10 | Record reviewed field corrections | Revised extraction with original and reviewed provenance |
| `POST /v1/evidence/search` | E06 through E10 | Retrieve product evidence for a typed query | Dated evidence records or explicit no-evidence |
| `POST /v1/recommendations` | E07 through E10 | Evaluate deterministic rules against profile and plans | Immutable recommendation result |
| `POST /invocations` | E11 | Run the provider-neutral coordinator in the backend container | Final state, result, events, and run metrics |
| `POST /v1/conversations` | E12 through E10 | Start a current-session conversation over a recommendation revision | Conversation ID, active revision, capabilities, and suggested prompts |
| `POST /v1/conversations/{conversation_id}/messages` | E12 through E10 | Submit a follow-up or page-change request | Assistant message, intent plan, action events, citations, and optional proposal |
| `POST /v1/conversations/{conversation_id}/proposals/{proposal_id}/confirm` | E12 through E10 | Confirm a decision-input or extraction-field proposal | Applied profile, extraction, recommendation, and summary revision IDs plus delta |
| `POST /v1/conversations/{conversation_id}/revisions/{revision_id}/undo` | E12 through E10 | Undo an applied summary revision | Restored or recalculated revision and visible delta |
| `GET /v1/runs/{run_id}` | E10 and E11 | Inspect an orchestration or evaluation run | Ordered events, versions, status, and aggregate metrics |

### POC persistence policy

| Data | POC store | Retention posture | Notes |
|---|---|---|---|
| Insurers, products, premiums, coverage, exclusions, riders | Local PostgreSQL or frozen fixture adapter | Retain for the demo with source versions | Real records require approved sources; synthetic records require `synthetic: true`. AWS target is RDS PostgreSQL. |
| Evidence chunks and embeddings | Local PostgreSQL/pgvector or frozen retrieval fixture | Retain only permitted text and metadata | Every chunk retains source and retrieval date. AWS target is RDS PostgreSQL with pgvector. |
| Permitted source snapshots and temporary synthetic files | Local S3-compatible object store or filesystem adapter | Retain only when source terms and the POC policy permit | AWS target is Amazon S3; raw user policy bytes are deleted after extraction by default. |
| Scrape logs | Local PostgreSQL or local evaluation artifact | Retain for freshness and failure analysis | Logs include outcome, hash, counts, next due time, lease owner, and cost where applicable. |
| Anonymous POC sessions and profile versions | In-memory or synthetic-only POC repository | Short-lived and disposable | Mock account identifiers are not production identity. |
| Uploaded policy bytes | Process memory or temporary file only | Delete after extraction by default | The judged demo uses synthetic files only. |
| Extraction fields and corrections | In-memory or synthetic-only POC repository | Retain for scenario replay | Original and reviewed values remain distinguishable. |
| Recommendation and run records | Local artifact or synthetic-only POC repository | Retain for evaluation and deck evidence | Record all input and configuration versions. |
| Conversations, proposals, actions, and summary revisions | Synthetic-only current-session repository | Delete with the anonymous POC session unless retained as a named fixture | Store typed content and version references, not raw document bytes or hidden model reasoning. |

### Error contract

Every backend failure returns `error_code`, `message`, `retryable`, `run_id`, and relevant `details` without exposing secrets or raw documents. Minimum error codes are `VALIDATION_ERROR`, `CONSENT_REQUIRED`, `MISSING_INFORMATION`, `UNSUPPORTED_DOCUMENT`, `LOW_CONFIDENCE_REVIEW_REQUIRED`, `NO_EVIDENCE`, `STALE_EVIDENCE`, `NO_ELIGIBLE_PLAN`, `ACTION_NOT_ALLOWED`, `CONFIRMATION_REQUIRED`, `REVISION_CONFLICT`, `DEPENDENCY_UNAVAILABLE`, `LOOP_LIMIT_REACHED`, `TIMEOUT`, and `INTERNAL_ERROR`.

## 10. Data contracts

### User profile

Profile ID, version, as-of date, consent state, life stage, employment, goals and horizons, cash flow, assets, liabilities, dependants and support duration, government, employer and private coverage, budget, product and explanation preferences, change set, and field provenance. Each field state is `present`, `unknown`, or `not_applicable`; absence is never interpreted as zero.

### Extraction result

Extraction ID, document label and synthetic status, adapter and model version, status, typed fields, raw and reviewed value, confidence, page and region evidence, warnings, unresolved fields, corrections, and run metrics. Document bytes are excluded from downstream contracts.

### Plan evidence

Plan and provider IDs; product version and effective date; category; eligibility; benefits; premiums and assumptions; terms and riders; exclusions and limitations; fees and surrender implications; source URL; quoted evidence spans; retrieval date; verification and freshness state; and synthetic status.

### Recommendation result

Profile and ruleset versions; calculated gaps; eligible and excluded plans with reason codes; fit components; trade-offs; assumptions; missing data; confidence; evidence IDs; and run metrics.

### Run event and metrics

Run and thread IDs; capability and contract versions; adapter mode; ordered state transitions; tool and model identifiers; prompt version; input and output schema status; retry and iteration counts; latency; token use; estimated cost; warnings; error code; and terminal status.

### Conversation and summary revision

Conversation, session, message, proposal, action, run, and revision IDs; active profile, extraction, recommendation, formulation, ruleset, catalogue, and evidence versions; user request; resolved intent; typed tool and target; confirmation requirement and outcome; old, proposed, and applied values; affected summary regions; citations; visible delta; undo lineage; mode; metrics; and terminal status. Hidden model reasoning and arbitrary executable page instructions are excluded.

## 11. Epic traceability

| Epic | PRD requirements | Primary URS outcomes |
|---|---|---|
| [E01](../epics/E01-poc-web-experience.md) | PRD-FR-001, PRD-FR-004, PRD-FR-012, PRD-FR-032, PRD-FR-035, PRD-FR-037; PRD-NFR-001, PRD-NFR-006, PRD-NFR-027 | Public, usable, clearly bounded journey with validated dynamic summary rendering |
| [E02](../epics/E02-readiness-quiz-and-peer-benchmark.md) | PRD-FR-002, PRD-FR-003; PRD-NFR-002, PRD-NFR-009 | Readiness discovery and responsible peer context |
| [E03](../epics/E03-user-profile-and-personalization.md) | PRD-FR-004, PRD-FR-005, PRD-FR-011, PRD-FR-015, PRD-FR-028, PRD-FR-033, PRD-FR-036, PRD-FR-037; PRD-NFR-008, PRD-NFR-013, PRD-NFR-023, PRD-NFR-025 | Explicit, versioned, confirmable user understanding including a no-policy path |
| [E04](../epics/E04-policy-ocr-and-extraction.md) | PRD-FR-006, PRD-FR-016, PRD-FR-021, PRD-FR-025, PRD-FR-027, PRD-FR-036, PRD-FR-037; PRD-NFR-003, PRD-NFR-004, PRD-NFR-010, PRD-NFR-017, PRD-NFR-022, PRD-NFR-025 | Reviewable OpenRouter-or-fixture extraction with confirmed provenance-preserving corrections |
| [E05](../epics/E05-source-data-ingestion-poc.md) | PRD-FR-007, PRD-FR-017, PRD-FR-030; PRD-NFR-003, PRD-NFR-008, PRD-NFR-011, PRD-NFR-021 | Proven bounded, idempotent, continuously running ingestion pattern |
| [E06](../epics/E06-insurance-retrieval-and-rag.md) | PRD-FR-007, PRD-FR-008, PRD-FR-017, PRD-FR-018, PRD-FR-021, PRD-FR-033, PRD-FR-034, PRD-FR-035; PRD-NFR-003, PRD-NFR-005, PRD-NFR-011, PRD-NFR-015, PRD-NFR-017, PRD-NFR-020 | Dated approved-catalogue evidence and conversational exploration from portable PostgreSQL/pgvector storage |
| [E07](../epics/E07-explainable-decision-support.md) | PRD-FR-009, PRD-FR-010, PRD-FR-019, PRD-FR-024, PRD-FR-031, PRD-FR-037; PRD-NFR-002, PRD-NFR-003, PRD-NFR-013, PRD-NFR-015, PRD-NFR-016, PRD-NFR-025 | Approved formulation and reproducible comparisons with deterministic revision deltas |
| [E08](../epics/E08-integrated-demo-and-evaluation.md) | PRD-FR-022, PRD-FR-024, PRD-FR-025, PRD-FR-026, PRD-FR-029, PRD-FR-032, PRD-FR-034, PRD-FR-036, PRD-FR-037, PRD-FR-038; PRD-NFR-006, PRD-NFR-013, PRD-NFR-015, PRD-NFR-016, PRD-NFR-017, PRD-NFR-021 | Docker Compose and conversational acceptance, measured results, and AWS deployment readiness |
| [E09](../epics/E09-productionisation-and-security.md) | PRD-NFR-007, PRD-NFR-012 | Tracked post-POC production readiness |
| [E10](../epics/E10-backend-api-and-poc-persistence.md) | PRD-FR-014, PRD-FR-015, PRD-FR-016, PRD-FR-018, PRD-FR-019, PRD-FR-021, PRD-FR-026, PRD-FR-029, PRD-FR-032, PRD-FR-033, PRD-FR-036, PRD-FR-037, PRD-FR-038; PRD-NFR-008, PRD-NFR-010, PRD-NFR-011, PRD-NFR-012, PRD-NFR-017 to PRD-NFR-021, PRD-NFR-023, PRD-NFR-025, PRD-NFR-026 | Contract-first API, disposable conversational state, revisions, and portable service adapters |
| [E11](../epics/E11-runtime-orchestration-and-operations.md) | PRD-FR-013, PRD-FR-020 to PRD-FR-023, PRD-FR-027, PRD-FR-030, PRD-FR-033 to PRD-FR-036, PRD-FR-038; PRD-NFR-005, PRD-NFR-010, PRD-NFR-013, PRD-NFR-014, PRD-NFR-017, PRD-NFR-019, PRD-NFR-021 to PRD-NFR-024, PRD-NFR-026 | Bounded local-first orchestration, typed conversational tools, OpenRouter calls, and observable runtime operations |
| [E12](../epics/E12-conversational-summary-agent.md) | PRD-FR-032 to PRD-FR-038; PRD-NFR-003, PRD-NFR-005, PRD-NFR-010, PRD-NFR-013 to PRD-NFR-017, PRD-NFR-022 to PRD-NFR-027 | Grounded conversation, visible typed page actions, and confirmed deterministic summary revisions |

## 12. Source coverage matrix

This matrix demonstrates that the PRD covers the complete source scope rather than one implementation workstream.

| Source area | PRD coverage | Owning epics |
|---|---|---|
| Problem, audience, and trust boundary | Goals, non-goals, PRD-FR-012, PRD-NFR-004, PRD-NFR-007, PRD-NFR-009 | E01, E02, E09 |
| Public quiz, readiness score, and peer comparison | PRD-FR-001 to PRD-FR-003; Section 8 score policy | E01, E02 |
| Account, consent, FNA onboarding, and adaptation | PRD-FR-004, PRD-FR-005, PRD-FR-011, PRD-FR-015; Section 8 onboarding coverage | E03, E10 |
| Optional policy upload, OpenRouter extraction, correction, and measured evaluation | PRD-FR-006, PRD-FR-016, PRD-FR-025, PRD-FR-027, PRD-FR-028; Section 8 extraction fields | E03, E04, E08, E10 |
| Source approval, continuous scraping, normalization, versioning, leasing, and freshness | PRD-FR-007, PRD-FR-017, PRD-FR-030, PRD-NFR-011, PRD-NFR-015, PRD-NFR-021 | E05, E06, E11 |
| Vector retrieval, citations, and unsupported-answer behavior | PRD-FR-008, PRD-FR-018, PRD-FR-021, PRD-NFR-003, PRD-NFR-017 | E06, E10 |
| Deterministic gaps, constraints, approved formulation, ranking, explanation, and no recommendation | PRD-FR-009, PRD-FR-010, PRD-FR-019, PRD-FR-031, PRD-NFR-002, PRD-NFR-016 | E07, E11 |
| Shared data contracts, backend API, local persistence, configuration, and AWS adapters | PRD-FR-014 to PRD-FR-016, PRD-FR-026, PRD-FR-029, PRD-NFR-008, PRD-NFR-010 to PRD-NFR-013, PRD-NFR-018 to PRD-NFR-021 | E10 |
| OpenRouter, runtime entrypoint, tools, loops, state, prompts, scraper lifecycle, and metrics | PRD-FR-013, PRD-FR-020, PRD-FR-022, PRD-FR-023, PRD-FR-027, PRD-FR-030, PRD-NFR-005, PRD-NFR-014, PRD-NFR-022 | E11 |
| Final-page conversation, approved-plan exploration, visible page actions, confirmations, revisions, replay, and undo | PRD-FR-032 to PRD-FR-038, PRD-NFR-023 to PRD-NFR-027 | E01, E03, E04, E06, E07, E08, E10, E11, E12 |
| Docker Compose acceptance and same-image AWS migration | PRD-FR-026, PRD-FR-029, PRD-NFR-015, PRD-NFR-018 to PRD-NFR-021 | E08, E10, E11 |
| Evaluation targets, ground truth, OCR experiment, demo, and fallback | Success measures, PRD-FR-024, PRD-FR-025, PRD-NFR-006, PRD-NFR-016, PRD-NFR-017 | E02, E04, E06, E07, E08 |
| Production identity, privacy, security, resilience, and regulatory review | PRD-NFR-007, PRD-NFR-012 | E09 |
| Team ownership and Friday integration sequence | Epic traceability and backlog dependencies | E01 to E12 |

## 13. Decision register

| ID | Decision | Status | Owner | POC rule until resolved |
|---|---|---|---|---|
| DEC-001 | Use Docker Compose and OpenRouter as the default runtime; treat Amazon Bedrock and AgentCore as optional later adapters. | Resolved for POC | Jana | AWS credits or organizer requirements may add an adapter but cannot block local execution. |
| DEC-002 | Confirm the exact OpenRouter model slug represented by `5.6 Luna`. | Open | Tim | Set `OPENROUTER_MODEL` explicitly; never invent a slug in source or deployment configuration. |
| DEC-003 | Verify the source and exact wording of the draft 26% Gen Z statistic. | Open | Jana | Omit the claim from product and presentation copy. |
| DEC-004 | Decide whether real retrieved products can feed recommendations in the demo. | Resolved for POC | Deborah | Keep sourced real-evidence retrieval and synthetic-plan ranking visibly separate unless compliance approves otherwise. |
| DEC-005 | Confirm minimum pilot cohort and consent wording. | Baseline defined | Jana | Require at least 10 for a percentile; otherwise show an official benchmark and label any mock cohort. |
| DEC-006 | Confirm provider sites permitted for automated retrieval and reuse. | Open | Darren | Use approved cached or synthetic fixtures and never depend on live scraping during the demo. |
| DEC-007 | Use local PostgreSQL/pgvector first and migrate the same schema to RDS PostgreSQL/pgvector later. | Resolved for POC | Darren | Keep metadata and full-text retrieval available when embeddings or external providers are unavailable. |
| DEC-008 | Implement the final-page agent with visible, typed application tools rather than screenshot-coordinate computer use. | Resolved for POC | Tim | Allow immediate presentation actions; preview and confirm decision-input or reviewed-extraction changes; search only the approved catalogue. |

## 14. Release posture

The POC release is demo-ready when all P0 acceptance criteria required by the rehearsed scenario are met, synthetic and simulated states are visible, and open P1 limitations are disclosed. It is not approved for real customer data or public financial decision-making.

Execution tickets are maintained in the [backlog register](../backlog/README.md).