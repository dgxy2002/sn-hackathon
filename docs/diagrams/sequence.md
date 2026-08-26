# Sequence Diagram

## Current browser-only sequence

```mermaid
sequenceDiagram
    actor User
    participant SPA as Vite SPA
    participant State as In-memory state
    participant Fixtures as Synthetic fixtures

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
```

No document bytes, profile data, retrieval request, or recommendation request leave the browser in the current sequence.

## Target local Docker Compose sequence

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
    participant OpenRouter as OpenRouter 5.6 Luna
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
        Coordinator->>Coordinator: Skip extraction and preserve policy fields as unknown
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
        API->>Rules: Profile, extracted policy, plans, and ruleset
        Rules-->>API: Gaps, exclusions, ranking, and trade-offs
        API-->>Coordinator: Immutable decision contract
        Coordinator->>OpenRouter: Immutable result and small evidence for explanation
        OpenRouter-->>Coordinator: Explanation without ranking changes
        Coordinator->>Runs: Store ordered events, versions, and metrics
        Coordinator-->>API: Final result and terminal state
        API-->>SPA: Recommendation contract and run metrics
        SPA-->>User: Reasons, alternatives, assumptions, and citations
    end
```

The local sequence runs in Docker Compose and uses `.env` configuration. Every transition validates its schema, every loop is bounded, and the deterministic decision result is immutable before the OpenRouter explanation call. The same backend image and contract later run on ECS Fargate; Bedrock or AgentCore may be added only as optional adapters.

## Target conversational summary sequence

```mermaid
sequenceDiagram
    actor User
    participant SPA as E01 final summary and E12 panel
    participant API as E10 conversation API
    participant Coordinator as E11 bounded coordinator
    participant Catalogue as E06 approved catalogue
    participant Profile as E03 profile service
    participant Extraction as E04 extraction review
    participant Rules as E07 deterministic engine
    participant Store as Current-session repository

    User->>SPA: Ask a follow-up or request a page change
    SPA->>API: POST conversation message with active revision
    API->>Coordinator: Validated context and allowed tools

    alt Read-only question or approved-plan exploration
        Coordinator->>Catalogue: Search approved records and evidence
        Catalogue-->>Coordinator: Dated cited results or no evidence
        Coordinator-->>API: Cited answer and typed presentation actions
        API->>Store: Record messages, actions, versions, and metrics
        API-->>SPA: Stream visible actions and answer
        SPA-->>User: Focus, filter, sort, or show temporary alternatives
    else Profile, comparison, or extracted-policy change
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
            Coordinator->>Rules: Rerun with versioned inputs and approved catalogue
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

The model selects only registered typed actions. It cannot execute page code or coordinates, search outside the approved catalogue, bypass confirmation, or directly author profile versions, extracted values, eligibility, rankings, or displayed decision numbers.