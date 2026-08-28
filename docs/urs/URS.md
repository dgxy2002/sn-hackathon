# User Requirements Specification

## Document control

| Field | Value |
|---|---|
| Product | CoverCheck SG |
| Version | 1.3 |
| Status | POC baseline |
| Date | 26 August 2026 |
| Audience | Product, engineering, research, and hackathon reviewers |
| Source documents | [Project plan](../PLAN.md) and [initial product brief](../OnboardingPrompt.md) |

## 1. Purpose

This User Requirements Specification (URS) defines what first-time working adults and project stakeholders need from the CoverCheck SG proof of concept. It describes user outcomes and constraints without prescribing the implementation.

CoverCheck SG is an educational insurance-readiness and comparison assistant for Singapore. It is not a licensed financial adviser and does not transact, replace, surrender, or recommend cancelling policies.

## 2. Problem statement

A first-time working adult in Singapore who has inherited insurance bought by their parents needs an independent way to understand what they own, what it covers, and whether it still fits their budget, responsibilities, and goals. Existing policies may be poorly understood, while product information is difficult to compare and often presented by sellers with limited panels or commercial interests.

## 3. Users and stakeholders

### Primary user

A first-time working adult in Singapore, primarily aged 19-29, who may have inherited policies, employer coverage, limited insurance knowledge, and a new responsibility for premiums and financial decisions.

### Secondary stakeholders

- Hackathon judges evaluating agentic behavior, correctness, evidence, and measurable benefit.
- Team members operating the quiz, extraction, retrieval, recommendation, and demo components.
- Data operators maintaining approved source ingestion, freshness, and retrieval evidence.
- Developers integrating independently owned components through shared contracts and a backend API.
- Authorized financial representatives who may verify information or complete regulated transactions outside the product.

## 4. User assumptions

- The user may not know policy names, benefits, exclusions, premiums, ownership, or employment-related coverage limits.
- Unknown information is valid and must not be treated as no coverage.
- The POC uses synthetic plans and synthetic policy documents unless explicitly labelled otherwise.
- Peer results are based only on a labelled hackathon pilot cohort, not the Singapore population.
- The user remains responsible for confirming information with official sources or an authorized representative.

## 5. Functional user requirements

| ID | User requirement | POC priority | Acceptance statement |
|---|---|---:|---|
| URS-FR-001 | The user shall be able to complete a public insurance-readiness quiz without signing in. | P0 | The quiz can be started and completed before account creation. |
| URS-FR-002 | The user shall receive a repeatable readiness result that distinguishes known, unclear, and missing coverage information. | P0 | Identical answers produce the same score and dimension results. |
| URS-FR-003 | The user shall see a constructive peer or benchmark comparison with cohort label, sample size, and collection date. | P0 | No unlabeled or fabricated population percentile is shown. |
| URS-FR-004 | The user shall be able to continue through a POC account and consent step before providing personal profile details. | P0 | The purpose and POC storage behavior are shown before onboarding. |
| URS-FR-005 | The user shall be able to provide life stage, goals, cash flow, dependants, debts, existing coverage, budget, and product preferences. | P1 | The minimum profile can be completed through a structured questionnaire. |
| URS-FR-006 | The user shall be told when decision-critical information is unknown and be asked only for information needed to improve the result. | P1 | Missing data is not converted to a negative answer or invented value. |
| URS-FR-007 | The user shall be able to provide a policy PDF or image, or choose a clearly labelled synthetic sample. | P1 | Supported input choices are visible before extraction begins. |
| URS-FR-008 | The user shall be able to review extracted policy fields, confidence, page evidence, warnings, and unresolved values before use. | P1 | Low-confidence fields can remain unresolved or be corrected. |
| URS-FR-009 | The user shall see protection gaps and affordability calculations with their assumptions and Singapore reference points. | P0 | Calculations expose inputs, formula intent, and source links. |
| URS-FR-010 | The user shall be able to compare eligible synthetic plans or plan categories against their profile and budget. | P0 | Alternatives and excluded options are distinguishable. |
| URS-FR-011 | The user shall receive reasons, trade-offs, assumptions, missing data, confidence, and dated evidence for comparison outputs. | P0 | Every product claim is linked to an evidence identifier or marked synthetic. |
| URS-FR-012 | The user shall be able to change a goal, budget, dependant, or policy and understand why the result changed. | P1 | A material input change reruns analysis and produces a change explanation. |
| URS-FR-013 | The user shall be able to open the MAS representatives register before engaging an adviser or transacting elsewhere. | P0 | A visible verification link is available from the result journey. |
| URS-FR-014 | The user shall be told that outputs are educational, whether data is synthetic, and what the product cannot do. | P0 | Trust-boundary messaging is visible at relevant decision points. |
| URS-FR-015 | The user shall receive an insufficient-data or unsupported result when a reliable comparison cannot be made. | P0 | The system can decline to rank rather than inventing an answer. |
| URS-FR-016 | A data operator shall be able to ingest only approved insurance sources and inspect source version, freshness, and ingest outcomes. | P1 | Every ingested source has an approval record, retrieval status, and timestamp. |
| URS-FR-017 | A developer shall be able to invoke profile, extraction, retrieval, decision, and orchestration capabilities through stable backend contracts. | P0 | Each capability has a versioned request, response, and error contract with representative fixtures. |
| URS-FR-018 | A reviewer shall be able to observe what models and tools acted, whether contracts passed, and what latency, token, cost, retry, and error outcomes occurred. | P0 | A run summary exposes the complete POC execution path and metrics. |
| URS-FR-019 | A reviewer shall be able to replay fixed synthetic scenarios against prewritten expected outcomes. | P0 | Versioned profiles, plans, rules, documents, queries, and expected results can be rerun without manual repair. |
| URS-FR-020 | The team shall be able to switch between live-approved, cached, synthetic, and simulated adapters without changing consumer contracts. | P1 | Every output identifies its data mode and all modes validate against the same schema. |
| URS-FR-021 | A developer shall be able to start the web application, backend API, continuously running scraper, PostgreSQL/pgvector database, and local object store with Docker Compose. | P0 | One documented local command starts healthy containers without requiring AWS resources. |
| URS-FR-022 | The system shall use OpenRouter `5.6 Luna` for language-model tasks and policy PDF/image ingestion, OCR, and structured extraction. | P0 | Provider and model are selected through configuration, and extraction output retains confidence and page evidence. |
| URS-FR-023 | A user who has no policy document shall be able to skip upload and continue with explicitly unknown existing-policy fields. | P0 | The no-policy path reaches gap analysis without creating synthetic coverage facts. |
| URS-FR-024 | An operator shall be able to deploy the same web, backend, and scraper container images to AWS without changing application code. | P1 | Deployment changes configuration and managed-service adapters, not capability contracts or business logic. |
| URS-FR-025 | A data operator shall have exactly one continuously running scraper runtime that refreshes due approved sources and exposes freshness and failure status. | P1 | The runtime prevents concurrent active scraper loops and records each source outcome. |
| URS-FR-026 | A reviewer shall be able to inspect the approved mathematical formulation used by plan ranking. | P0 | Every recommendation records the formulation and ruleset versions used to calculate gaps, exclusions, and fit. |
| URS-FR-027 | The user shall be able to ask contextual follow-up questions from the final summary page. | P1 | The conversation retains the active profile, recommendation, evidence, and prior-turn context within the POC session. |
| URS-FR-028 | The user shall be able to ask about approved plans and alternatives not shown in the initial comparison. | P1 | Answers and explored alternatives come only from the approved catalogue and retain source, date, freshness, and synthetic status. |
| URS-FR-029 | The user shall be able to ask the agent to navigate, focus, filter, sort, or otherwise change the summary presentation. | P1 | Harmless presentation changes update the page through visible, allowlisted actions without changing decision inputs. |
| URS-FR-030 | The user shall be able to request changes to profile inputs, comparison plans, or extracted policy fields from the conversation. | P1 | The system shows the proposed changes and requires confirmation before changing any decision input or reviewed policy field. |
| URS-FR-031 | The user shall see the summary update dynamically after an approved request and understand what changed. | P1 | A confirmed request creates a versioned revision, reruns deterministic analysis where required, highlights the delta, and offers undo. |
| URS-FR-032 | A reviewer shall be able to inspect and replay the conversational agent's actions and resulting summary revisions. | P1 | The run exposes ordered intents, tools, evidence, confirmations, deterministic reruns, page revisions, and terminal status. |

## 6. Non-functional user requirements

| ID | User requirement | POC priority | Acceptance statement |
|---|---|---:|---|
| URS-NFR-001 | Content, currency, public schemes, sources, and terminology shall be appropriate to Singapore. | P0 | Examples use SGD and relevant Singapore guidance. |
| URS-NFR-002 | The journey shall be usable on current desktop and mobile browsers with keyboard-accessible core interactions. | P0 | The POC is responsive and the main path does not require a pointer. |
| URS-NFR-003 | Scoring, gap calculations, eligibility, and ranking shall be deterministic and reproducible. | P0 | Reviewed fixtures produce stable outputs independent of explanation wording. |
| URS-NFR-004 | Product and policy facts shall retain source, date, synthetic status, and field-level provenance where available. | P0 | Unsupported facts do not appear as verified claims. |
| URS-NFR-005 | The POC shall minimize personal data and use synthetic documents; secrets shall not be exposed in the browser or repository. | P0 | The demo requires no real NRIC, diagnosis, payment, or customer policy data. |
| URS-NFR-006 | The judged journey shall run reliably from a documented clean setup and have a recorded fallback. | P0 | The build passes and the rehearsed scenario can be completed within the demo window. |
| URS-NFR-007 | Agent and model activity shall be bounded and measurable. | P1 | Runs expose iteration, latency, error, tool, token, and estimated-cost metrics. |
| URS-NFR-008 | Full production identity, security, privacy, availability, and regulatory controls shall be completed before use with real customers. | P3 | The requirement is tracked but does not block the synthetic POC. |
| URS-NFR-009 | Peer comparison shall avoid shame, unsupported population claims, and statistically weak precision. | P0 | Pilot labels and cohort context are visible, with no fabricated live claim. |
| URS-NFR-010 | Backend and agent failures shall be explicit, typed, bounded, and recoverable without presenting partial output as a valid recommendation. | P0 | Invalid input, unavailable tools, stale evidence, and exhausted retries produce defined failure states. |
| URS-NFR-011 | Independently owned components shall interoperate through versioned schemas and reject incompatible payloads. | P0 | Schema version and validation outcome are available at every component boundary. |
| URS-NFR-012 | Source ingestion and storage shall be repeatable, idempotent, and freshness-aware. | P1 | Reprocessing the same source does not create duplicate active records and stale versions remain distinguishable. |
| URS-NFR-013 | POC results shall be reproducible from recorded fixture, contract, ruleset, model, prompt, and source versions. | P0 | A run can be traced to all inputs and configuration needed to explain or replay it. |
| URS-NFR-014 | Local secrets shall be read from an uncommitted `.env` file and later supplied through AWS Secrets Manager. | P0 | Secrets are absent from source, images, Compose files, browser bundles, and logs in both environments. |
| URS-NFR-015 | Local and AWS environments shall use the same container images and environment-variable contract. | P1 | Switching environments changes endpoints, credentials, and adapters without rebuilding environment-specific application code. |
| URS-NFR-016 | Local state services shall use portable protocols with documented AWS equivalents. | P1 | PostgreSQL/pgvector can move to RDS PostgreSQL and S3-compatible local storage can move to Amazon S3. |
| URS-NFR-017 | Every container shall expose health behavior and shut down cleanly. | P0 | Docker Compose and ECS can detect unhealthy web, API, scraper, database, and storage dependencies. |
| URS-NFR-018 | Conversational page actions shall use allowlisted typed tools rather than unconstrained model-authored page code or coordinate clicks. | P1 | Every action validates against an explicit schema and permission before execution. |
| URS-NFR-019 | Conversational requests shall not bypass deterministic calculation, eligibility, ranking, extraction-review, or evidence rules. | P0 | The model can propose inputs and actions but cannot directly author canonical recommendation values. |
| URS-NFR-020 | Conversation and summary-revision state shall be disposable and limited to the current synthetic POC session by default. | P1 | Starting a new session removes chat and revision history unless a versioned evaluation fixture explicitly retains it. |
| URS-NFR-021 | The conversational interface shall expose progress, evidence, confirmation, failure, completion, and undo states accessibly. | P1 | Keyboard and screen-reader users can follow and control the same action lifecycle as pointer users. |

## 7. User journey acceptance

```mermaid
flowchart LR
    A[Discover readiness gap]
    B[Understand result and benchmark]
    C[Consent and build profile]
    D{Existing policy available?}
    D1[Upload and review extracted policy]
    D2[Continue with policy fields unknown]
    E[See calculated gaps]
    F[Compare evidence-backed options]
    G[Ask follow-up or explore alternatives]
    H{Request changes?}
    I[Preview and confirm decision inputs]
    J[Recalculate and update summary]
    K[Verify adviser]

    A --> B --> C --> D
    D -- Yes --> D1 --> E
    D -- No --> D2 --> E
    E --> F --> G --> H
    H -- No --> K
    H -- Yes --> I --> J --> G
```

The minimum POC journey is accepted when one target user can complete it without team intervention and can explain the result, its assumptions, and its synthetic or sourced evidence.

## 8. Out of scope for the POC

- Buying, applying for, replacing, switching, or surrendering insurance.
- A complete investment, retirement, or financial-planning portfolio.
- Real customer medical, identity, payment, beneficiary, or policy data.
- Exhaustive whole-market insurance coverage.
- Production authentication, document retention, payments, or adviser communication.
- Claims that the product is an independent financial adviser.

## 9. Traceability

Product-level implementation and acceptance criteria are defined in the [PRD](../prd/PRD.md). Epic ownership and delivery status are defined in the [epic register](../epics/README.md). Backlog execution is defined in the [backlog register](../backlog/README.md).