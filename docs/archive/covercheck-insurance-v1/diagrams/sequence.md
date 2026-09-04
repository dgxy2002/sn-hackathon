# Sequence Diagram

## Initial browser and fixture-API sequence - 2026-08-26

```mermaid
sequenceDiagram
    actor User
    participant SPA as Vite SPA
    participant State as In-memory state
    participant Fixtures as Synthetic fixtures
    participant API as FastAPI conversation API
    participant Agent as Typed fixture agent

    User->>SPA: Open landing page
    loop Five readiness questions
        SPA->>User: Show question and progress
        User->>SPA: Select answer
        SPA->>State: Store answer
    end
    SPA->>State: Calculate readiness score
    SPA->>Fixtures: Read pilot benchmark
    SPA-->>User: Show score, coverage map, and benchmark
    User->>SPA: Submit mock account and consent
    SPA->>State: Store profile fields
    loop Five onboarding steps
        SPA->>User: Request explicit profile data
        User->>SPA: Submit step
        SPA->>State: Update profile
    end
    User->>SPA: Select file or synthetic sample
    SPA->>Fixtures: Load synthetic extraction
    SPA-->>User: Show hard-coded fields and confidence
    User->>SPA: Confirm fields
    SPA->>State: Calculate death and CI gaps
    SPA->>Fixtures: Load three synthetic plans
    SPA-->>User: Show static comparison and reasons
    User->>SPA: Ask a final-page question or presentation request
    SPA->>API: Create conversation and send typed message
    API->>Agent: Resolve fixture intent and allowlisted action
    Agent->>Fixtures: Select synthetic answer and citation
    Agent-->>API: Typed message, action events, and status
    API-->>SPA: Versioned fixture response
    SPA-->>User: Show answer and focus or filter the summary
```

This records the initial fixture slice accepted on 26 August 2026. At that point, conversation messages left the browser but profile, evidence-search, and recommendation requests did not. The later integrated sequence below supersedes it as the current runtime.

## Initial read-only RAG integration design

```mermaid
sequenceDiagram
    actor User
    participant SPA as Website and Ask CoverCheck
    participant API as E10 API
    participant Evidence as E06 evidence service
    participant OpenAI as OpenAI embeddings
    participant Supabase as Supabase PostgreSQL and pgvector
    participant Fixture as Deterministic evidence fixture

    User->>SPA: Ask a product question or explore cached plans
    SPA->>API: POST typed evidence search or conversation message
    API->>Evidence: Validated read-only query and filters
    alt Supabase adapter available
        Evidence->>OpenAI: Embed the bounded query
        OpenAI-->>Evidence: Query vector
        Evidence->>Supabase: Metadata filter and pgvector search
        Supabase-->>Evidence: Cached chunks and policy IDs
    else Dependency unavailable
        Evidence->>Fixture: Run deterministic fallback query
        Fixture-->>Evidence: Schema-identical evidence records
    end
    Evidence-->>API: Evidence or explicit no-evidence state
    API-->>SPA: Citations, date types, approval/evidence state, and mode
    SPA-->>User: Read-only answer or broad catalogue exploration
```

This design introduced the direct E10/E06 read path without treating every cached record as approved. The accepted implementation now uses local PostgreSQL as the default adapter, retains Supabase as optional, keeps the three date types distinct, and cannot change the E07 synthetic recommendation.

## Phase 3B real-product evidence-comparison sequence

```mermaid
sequenceDiagram
    actor User
    participant SPA as E01 comparison surface
    participant API as E10 API
    participant Evidence as E06 comparison projection
    participant E07 as Synthetic recommendation state

    User->>SPA: Select two to four real products in one category
    SPA->>API: POST /v1/evidence/compare with selected product IDs
    API->>Evidence: Validate comparison eligibility and requested fields
    Evidence->>Evidence: Normalize units and resolve field evidence
    alt All products are comparison eligible
        Evidence-->>API: Neutral product order, cited cells, unknowns, and gate state
        API-->>SPA: Read-only comparison plus unchanged canonical references
        SPA-->>User: Show "Real-product evidence comparison - not a recommendation"
    else Selection or evidence fails a gate
        Evidence-->>API: Typed stale, conflict, mixed-category, or unsupported result
        API-->>SPA: Failure without partial comparison
        SPA-->>User: Show why the product cannot be compared
    end
    Note over API,E07: E07 is not invoked and its catalogue, result, and revision remain unchanged
```

Phase 3B may follow the direct read-only integration before E11 exists. Discovery relevance can help the user find products, but the comparison uses provider/product ordering and contains no fit score, recommendation badge, or suitability claim.

## Accepted runtime, live Bedrock explanation, and pending OpenRouter extraction

The local API, PostgreSQL evidence path, deterministic E07 engine, invocation coordinator, run events, and typed Bedrock explanation adapter are implemented. Credentialed Bedrock completed through the Docker/Nginx/API path. OpenRouter extraction remains pending; fixture mode supplies the same explanation boundary without a provider credential.

```mermaid
sequenceDiagram
    actor User
    participant SPA as Vite SPA
    participant API as E10 API and tool gateway
    participant Coordinator as E11 coordinator
    participant Extract as OpenRouter extraction adapter
    participant Profile as Profile service
    participant RAG as Retrieval service
    participant DB as Local PostgreSQL and pgvector
    participant Rules as Decision engine
    participant OpenRouter as OpenRouter extraction
    participant Bedrock as Amazon Bedrock Converse
    participant Runs as POC run repository

    User->>SPA: Submit consented profile and optional synthetic policy
    SPA->>API: POST session and profile
    API->>Profile: Normalize explicit answers
    Profile-->>API: Versioned profile and missing fields
    API->>Runs: Store synthetic session and profile version
    SPA->>API: POST /invocations
    API->>Coordinator: Versioned invocation contract
    Coordinator->>API: Load profile version
    API-->>Coordinator: Validated profile contract
    alt Policy document supplied
        Coordinator->>API: Submit extraction tool call
        API->>Extract: Extract approved fields
        Extract->>OpenRouter: Synthetic PDF/image and versioned prompt
        OpenRouter-->>Extract: Structured fields and usage
        Extract-->>API: Values, confidence, page evidence, and metrics
        API-->>Coordinator: Validated extraction contract
    else No policy supplied
        Coordinator->>Coordinator: Skip extraction and mark policy fields not applicable
    end

    alt Decision-critical fields are missing
        Coordinator-->>API: Need-user-input terminal state
        API-->>SPA: Focused follow-up questions
        SPA-->>User: Request missing information
    else Profile is sufficient
        Coordinator->>API: Search evidence tool call
        API->>RAG: Query product category and dated evidence
        RAG->>DB: Filter and retrieve relevant chunks
        DB-->>RAG: Product records and evidence spans
        RAG-->>API: Typed evidence records or no-evidence
        API-->>Coordinator: Validated evidence contract
        Coordinator->>API: Evaluate recommendation tool call
        API->>Rules: Profile, extracted policy, synthetic plans, and ruleset
        Rules-->>API: Gaps, exclusions, ranking, and trade-offs
        API-->>Coordinator: Immutable decision contract
        Coordinator->>Bedrock: Immutable synthetic result and compact personalization context
        Bedrock-->>Coordinator: Schema-validated explanation without ranking fields
        Coordinator->>Runs: Store ordered events, versions, and metrics
        Coordinator-->>API: Final result and terminal state
        API-->>SPA: Recommendation contract and run metrics
        SPA-->>User: Reasons, alternatives, assumptions, and citations
    end
```

The accepted sequence runs in Docker Compose and uses `.env` configuration. The tested coordinator validates transitions, records Bedrock provider/model/prompt/token metadata, rejects unknown plan IDs, and preserves the deterministic result on provider failure. Credentialed live Bedrock acceptance is complete. Priced cost metrics, full loop-limit acceptance, live OpenRouter extraction, and the later ECS Fargate deployment remain open. AgentCore remains optional.

## Current budget-revision sequence and remaining patch types

```mermaid
sequenceDiagram
    actor User
    participant SPA as E01 final summary and E12 panel
    participant API as E10 conversation API
    participant Coordinator as E11 bounded coordinator
    participant Catalogue as E06 cached catalogue
    participant Profile as E03 profile service
    participant Extraction as E04 extraction review
    participant Rules as E07 deterministic engine
    participant Store as Current-session repository

    User->>SPA: Ask a follow-up or request a page change
    SPA->>API: POST conversation message with active revision

    alt Read-only question or cached-plan exploration
        API->>Catalogue: Validated typed evidence query
        Catalogue-->>API: Dated results with evidence state or no evidence
        API->>Store: Record messages, actions, versions, and metrics
        API-->>SPA: Stream visible actions and answer
        SPA-->>User: Focus, filter, sort, or show temporary alternatives
    else Profile, comparison, or extracted-policy change
        API->>Coordinator: Validated context and allowed tools
        Coordinator-->>API: Typed proposal with old and proposed values
        API->>Store: Save pending proposal and action trace
        API-->>SPA: Confirmation required
        SPA-->>User: Preview impact and request confirmation
        alt User cancels
            User->>SPA: Cancel
            SPA->>API: Reject proposal
            API->>Store: Record rejection; retain active versions
            API-->>SPA: Unchanged canonical summary
        else User confirms
            User->>SPA: Confirm proposal
            SPA->>API: POST proposal confirmation with base version
            API->>Coordinator: Resume validated plan
            alt Profile or canonical comparison patch
                Coordinator->>Profile: Create confirmed immutable version
                Profile-->>Coordinator: New profile version
            else Extraction-field correction
                Coordinator->>Extraction: Create confirmed reviewed version
                Extraction-->>Coordinator: New extraction version
            end
            Coordinator->>Rules: Rerun with versioned inputs and synthetic plan catalogue
            Rules-->>Coordinator: Deterministic result and before/after delta
            Coordinator->>Store: Atomically store run, actions, and summary revision
            Coordinator-->>API: Validated revision and undo lineage
            API-->>SPA: Changed regions and terminal state
            SPA-->>User: Highlight recalculated comparison changes
        end
    end

    opt User chooses undo
        User->>SPA: Undo revision
        SPA->>API: POST undo with active revision
        API->>Rules: Restore or deterministically recalculate prior inputs
        Rules-->>API: Coherent restored result
        API->>Store: Append undo revision
        API-->>SPA: Restored delta and replay record
    end
```

Read-only E06 retrieval and Phase 3B comparison may bypass E11 but not E10 schema validation, comparison-eligibility, or evidence-state rules. Consequential actions enter E11 and select only registered typed tools. Before the separately approved Phase 6 path, model output cannot execute page code or coordinates, search outside the cached E06 corpus, bypass confirmation, place real retrieved products into E07 ranking, or directly author profile versions, extracted values, eligibility, rankings, or displayed decision numbers. Phase 6 still uses E07 deterministically and never lets the model author rank.

The proposal, confirmation, cancellation, deterministic rerun, revision, replay, and undo sequence is accepted for budget changes. Goal, dependant, preference, declared-coverage, and extraction-field changes remain pending and must use the same confirmation boundary before they are claimed.