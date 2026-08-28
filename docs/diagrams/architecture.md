# Capability Architecture

## POC architecture

```mermaid
flowchart LR
    User[First-time working adult]

    subgraph Local[Accepted local Docker Compose runtime]
        Web[Vite build behind Nginx]
        API[E10 FastAPI and typed routes]
        Profile[Versioned in-memory profile service]
        Extraction[Simulated E04 extraction]
        Evidence[E06 read-only evidence service]
        Compare[Eligibility-gated comparison projector]
        Rules[Deterministic E07 decision engine]
        Coordinator[Bounded E11 invocation coordinator]
        Conversation[E12 conversation, revisions, replay, undo]
        Scraper[E05 singleton scraper worker]
        DB[(PostgreSQL 16 and pgvector)]
        Corpus[79 brochure documents<br/>71 normalized products]
        Fixtures[Synthetic policies and plans]
    end

    subgraph Optional[Optional or offline adapters]
        Supabase[Hosted Supabase and pgvector]
        OpenAI[Offline extraction and embeddings]
        OpenRouter[OpenRouter model slug unresolved]
        Store[Optional S3-compatible object store]
        Sources[Approved live insurance sources pending]
    end

    User --> Web --> API
    API --> Profile
    API --> Extraction
    API --> Evidence
    API --> Compare
    API --> Rules
    API --> Coordinator
    API --> Conversation
    Extraction --> Fixtures
    Coordinator --> Profile
    Coordinator --> Extraction
    Coordinator --> Rules
    Conversation --> Evidence
    Conversation --> Rules
    Compare --> Evidence
    Evidence --> DB
    Corpus --> DB
    Scraper -->|lease and heartbeat; idle without approved source| DB
    Corpus --> OpenAI
    Evidence -. optional adapter .-> Supabase
    Sources -. approval required .-> Scraper
    API -. live extraction and explanation pending .-> OpenRouter
    API -. permitted objects pending .-> Store

    classDef implemented fill:#e7f4ed,stroke:#246b45,color:#123b28;
    classDef simulated fill:#fff3d6,stroke:#a66500,color:#573900;
    classDef planned fill:#edf1f7,stroke:#53657d,color:#263545,stroke-dasharray: 5 4;
    class Web,API,Profile,Evidence,Compare,Rules,Coordinator,Conversation,Scraper,DB,Corpus,OpenAI,Supabase implemented;
    class Extraction,Fixtures simulated;
    class OpenRouter,Store,Sources planned;
```

## Boundary notes

- The browser uses versioned FastAPI routes for profile, simulated extraction, recommendation, invocation, evidence, comparison, conversation, proposal, revision, replay, and undo behavior. UI navigation state remains in [`frontend/src/main.js`](../../frontend/src/main.js).
- The conversation and evidence routes use a typed local PostgreSQL evidence service for cited real-product exploration. They do not alter the synthetic plan ranking.
- Darren's separate RAG slice extracts 79 cached brochures into 87 policy rows, normalizes 71 unique policy slugs, prepares 1,319 candidate chunks, and retrieves typed evidence through a Supabase-backed CLI.
- Runtime migrations load the committed corpus into local PostgreSQL through the typed E10/E06 boundary. Supabase remains an optional adapter.
- All cached records may be searched for read-only questions and exploration, but every result carries approval/evidence state and cannot enter E07's synthetic ranking.
- Phase 3B adds a comparison projector for a small comparison-eligible subset. It returns neutrally ordered cited fields and cannot invoke E07 or mutate canonical state.
- OpenAI owns current offline brochure extraction and embeddings. OpenRouter remains the configured E04/E11 provider for user-document extraction and explanation.
- [E10](../epics/E10-backend-api-and-poc-persistence.md) owns transport, shared schema validation, typed errors, and disposable synthetic state; it does not own capability business rules.
- Direct read-only E10/E06 retrieval does not require E11. [E11](../epics/E11-runtime-orchestration-and-operations.md) owns consequential proposals, confirmed changes, deterministic reruns, revisions, replay, undo, OpenRouter runtime integration, and operational coordination.
- [E12](../epics/E12-conversational-summary-agent.md) owns the final-page agent experience and integration. E11 executes its allowlisted typed tools; E03/E04/E06/E07 retain profile, extraction, retrieval, and deterministic decision authority.
- Navigation, focus, sorting, filtering, and read-only cached-plan exploration may apply immediately. Profile, canonical comparison, and reviewed extraction changes require confirmation, immutable input versions, and a fresh E07 result before the canonical summary changes.
- Real-product ranking remains disabled until the separate Phase 6 data, E07, E08, DEC-004, and compliance gates pass. Public ranked mode additionally requires E09 approval.
- Model output cannot become HTML, JavaScript, selectors, coordinates, SQL, arbitrary URLs, or canonical recommendation values.
- The accepted local target is Docker Compose with `.env` configuration. Fixture mode requires no provider credential. OpenRouter policy extraction and grounded explanation remain pending because the exact model slug is unresolved.
- Local PostgreSQL/pgvector is the default POC evidence store. Supabase/PostgREST remains an optional adapter, and RDS PostgreSQL/pgvector remains a later migration target.
- Amazon Bedrock and AgentCore are optional future adapters and are not required for local execution.
- Production identity, durable personal data, private document storage, and operational hardening are intentionally deferred to [E09](../epics/E09-productionisation-and-security.md).