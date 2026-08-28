# ER Diagram

## Implemented core RAG schema

```mermaid
erDiagram
    INSURERS ||--o{ POLICIES : offers
    POLICIES ||--o{ POLICY_PREMIUMS : prices
    POLICIES ||--o{ POLICY_COVERAGE : includes
    POLICIES ||--o{ POLICY_EXCLUSIONS : excludes
    POLICIES ||--o{ POLICY_RIDERS : supports

    INSURERS {
        UUID id PK
        TEXT name
        TEXT short_name UK
        TEXT mas_license_no
        TEXT website_url
        BOOLEAN is_active
    }

    POLICIES {
        UUID id PK
        UUID insurer_id FK
        TEXT name
        POLICY_CATEGORY category
        POLICY_TYPE type
        TEXT plan_tier
        BOOLEAN available_to_new
        TEXT source_url
        DATA_SOURCE source_type
        TIMESTAMPTZ last_scraped_at
        BOOLEAN is_verified
        TEXT data_hash
    }

    POLICY_PREMIUMS {
        UUID id PK
        UUID policy_id FK
        INT age_next_birthday
        CHAR gender
        TEXT smoker_status
        TEXT citizenship
        NUMERIC premium_total
        NUMERIC sum_assured
    }

    POLICY_COVERAGE {
        UUID id PK
        UUID policy_id FK
        TEXT benefit_name
        TEXT benefit_category
        COVERAGE_TYPE coverage_type
        NUMERIC limit_amount
        NUMERIC deductible_sgd
        NUMERIC co_insurance_pct
        BOOLEAN covered
    }

    POLICY_EXCLUSIONS {
        UUID id PK
        UUID policy_id FK
        TEXT exclusion
        TEXT category
    }

    POLICY_RIDERS {
        UUID id PK
        UUID policy_id FK
        TEXT name
        TEXT rider_type
        BOOLEAN is_cash_only
        NUMERIC indicative_premium
    }

    CREDIT_CARDS {
        UUID id PK
        TEXT singsaver_id UK
        TEXT name
        TEXT bank
        CARD_TYPE card_type
        JSONB benefits
        TEXT detail_url
        DATA_SOURCE source_type
        TIMESTAMPTZ last_scraped_at
        TEXT data_hash
    }

    DOCUMENT_CHUNKS {
        UUID id PK
        TEXT source_type
        UUID source_id
        TEXT source_url
        TEXT chunk_text
        INT chunk_index
        JSONB metadata
        VECTOR embedding
        INT token_count
    }

    SCRAPE_LOGS {
        UUID id PK
        TEXT source_url
        DATA_SOURCE source_type
        UUID linked_id
        TEXT status
        INT http_status
        INT chunks_upserted
        INT tokens_used
        NUMERIC cost_usd
        TIMESTAMPTZ scraped_at
        TIMESTAMPTZ next_scrape_due
    }
```

This is the core of [`backend/scraper/supabase_schema.sql`](../../backend/scraper/supabase_schema.sql), which the current ingestion and retrieval CLIs consume through Supabase/PostgREST. The diagram omits some normalized support tables for readability. It does not imply that the same schema is wired into E10 or the website.

## Provenance relationships

```mermaid
flowchart LR
    P[POLICIES]
    C[CREDIT_CARDS]
    D[DOCUMENT_CHUNKS]
    S[SCRAPE_LOGS]

    P -. logical source_id .-> D
    C -. logical source_id .-> D
    S -. logical linked_id .-> P
    S -. logical linked_id .-> C
```

The solid relationships in the ER diagram are enforced foreign keys with cascading deletes. `document_chunks.source_id` and `scrape_logs.linked_id` are polymorphic logical references and are not database foreign keys.

## Approved read-only evidence contract

The first website integration adds a typed logical contract before any storage migration is chosen. These fields may be derived from existing policy, document, chunk, and metadata records; they are not current SQL-column claims.

```mermaid
erDiagram
    EVIDENCE_RESPONSE ||--o{ EVIDENCE_RESULT : contains
    EVIDENCE_RESULT }o--|| POLICY_REFERENCE : identifies
    EVIDENCE_RESULT }o--|| SOURCE_REFERENCE : cites

    EVIDENCE_RESPONSE {
        TEXT contract_version
        TEXT adapter_mode
        TEXT query_status
        TEXT correlation_id
    }

    EVIDENCE_RESULT {
        TEXT evidence_id
        TEXT field
        TEXT quoted_span
        TEXT evidence_state
        BOOLEAN synthetic
        NUMERIC similarity
    }

    POLICY_REFERENCE {
        TEXT policy_id
        TEXT provider
        TEXT product
        TEXT category
    }

    SOURCE_REFERENCE {
        TEXT source_url
        DATE document_as_of_date
        DATE product_effective_date
        TIMESTAMPTZ retrieved_at
        TEXT document_version
    }
```

`document_as_of_date`, `product_effective_date`, and `retrieved_at` are distinct. Unknown values remain null. `evidence_state` records approval, freshness, conflict, or uncertainty; broad cache inclusion alone never means approved or suitable.

## Proposed POC runtime model

The E10 repository contract adds disposable synthetic workflow state without claiming that these tables already exist.

```mermaid
erDiagram
    POC_SESSIONS ||--o{ PROFILE_VERSIONS : owns
    POC_SESSIONS ||--o{ EXTRACTION_RUNS : submits
    POC_SESSIONS ||--o{ AGENT_RUNS : starts
    POC_SESSIONS ||--o{ CONVERSATIONS : opens
    PROFILE_VERSIONS ||--o{ RECOMMENDATION_RUNS : evaluates
    EXTRACTION_RUNS ||--o{ EXTRACTED_FIELDS : produces
    CONVERSATIONS ||--o{ CONVERSATION_MESSAGES : contains
    CONVERSATIONS ||--o{ ACTION_PROPOSALS : proposes
    CONVERSATIONS ||--o{ AGENT_RUNS : invokes
    CONVERSATIONS ||--o{ SUMMARY_REVISIONS : versions
    AGENT_RUNS ||--o{ RUN_EVENTS : records
    AGENT_RUNS ||--o{ AGENT_ACTIONS : executes
    AGENT_RUNS ||--o| RECOMMENDATION_RUNS : completes_with
    ACTION_PROPOSALS ||--o| SUMMARY_REVISIONS : applies_as
    RECOMMENDATION_RUNS ||--o{ SUMMARY_REVISIONS : renders_as

    POC_SESSIONS {
        UUID id PK
        TEXT consent_state
        BOOLEAN synthetic
        TIMESTAMPTZ expires_at
        TIMESTAMPTZ created_at
    }

    PROFILE_VERSIONS {
        UUID id PK
        UUID session_id FK
        INT version
        DATE as_of_date
        JSONB profile_data
        JSONB field_provenance
        JSONB change_set
    }

    EXTRACTION_RUNS {
        UUID id PK
        UUID session_id FK
        TEXT status
        TEXT adapter_mode
        TEXT model_version
        TEXT document_label
        JSONB metrics
    }

    EXTRACTED_FIELDS {
        UUID id PK
        UUID extraction_run_id FK
        TEXT field_name
        JSONB raw_value
        JSONB reviewed_value
        NUMERIC confidence
        INT page_number
        JSONB region
        TEXT review_status
    }

    AGENT_RUNS {
        UUID id PK
        UUID session_id FK
        UUID conversation_id FK
        TEXT thread_id
        TEXT status
        TEXT contract_version
        TEXT adapter_mode
        JSONB aggregate_metrics
    }

    RUN_EVENTS {
        UUID id PK
        UUID agent_run_id FK
        INT sequence_number
        TEXT state
        TEXT event_type
        TEXT capability
        JSONB version_refs
        JSONB metrics
        TEXT error_code
    }

    CONVERSATIONS {
        UUID id PK
        UUID session_id FK
        UUID active_revision_id
        TEXT status
        JSONB context_limits
        TIMESTAMPTZ created_at
    }

    CONVERSATION_MESSAGES {
        UUID id PK
        UUID conversation_id FK
        TEXT role
        JSONB typed_content
        JSONB citation_ids
        TIMESTAMPTZ created_at
    }

    ACTION_PROPOSALS {
        UUID id PK
        UUID conversation_id FK
        UUID base_revision_id
        TEXT proposal_type
        JSONB old_values
        JSONB proposed_patch
        TEXT confirmation_status
        TIMESTAMPTZ expires_at
    }

    AGENT_ACTIONS {
        UUID id PK
        UUID agent_run_id FK
        INT sequence_number
        TEXT intent
        TEXT tool_name
        TEXT target
        TEXT status
        JSONB version_refs
        JSONB affected_regions
        JSONB metrics
        TEXT error_code
    }

    RECOMMENDATION_RUNS {
        UUID id PK
        UUID profile_version_id FK
        UUID agent_run_id FK
        TEXT ruleset_version
        JSONB calculated_gaps
        JSONB eligible_plans
        JSONB excluded_plans
        JSONB trade_offs
        JSONB evidence_ids
    }

    SUMMARY_REVISIONS {
        UUID id PK
        UUID conversation_id FK
        UUID recommendation_run_id FK
        UUID source_proposal_id FK
        UUID parent_revision_id
        UUID undo_of_revision_id
        INT revision_number
        JSONB affected_regions
        JSONB visible_delta
        TIMESTAMPTZ created_at
    }
```

## Scope notes

- The current RAG CLIs actively consume [`backend/scraper/supabase_schema.sql`](../../backend/scraper/supabase_schema.sql) through hosted Supabase/PostgREST. Hosted database contents still depend on the configured environment and are not a website-integration claim.
- [`backend/scraper/credit_card_schema.sql`](../../backend/scraper/credit_card_schema.sql) is a standalone subset for `credit_cards` and `scrape_logs`.
- User accounts, profile versions, extraction jobs, recommendations, conversations, action proposals, summary revisions, and run events are absent from the current SQL and shown separately as a proposed POC repository model.
- Conversation and revision records are synthetic-only current-session state by default. They retain typed content and version lineage, not raw document bytes, hidden model reasoning, or executable page instructions.
- Presentation-only revisions may retain the same recommendation run; confirmed decision-input or extraction changes reference a fresh deterministic recommendation run. Parent and undo fields are logical self-references.
- The first E10/E06 integration adapter may use the existing Supabase path, with a schema-identical deterministic fixture adapter for fallback. E10 still targets local PostgreSQL/pgvector in Docker Compose; the same migrations later target RDS PostgreSQL/pgvector.
- Permitted source snapshots may use local S3-compatible storage and later Amazon S3; uploaded user document bytes are not persisted by default.
- Production identity and user-data controls remain in [E09](../epics/E09-productionisation-and-security.md).