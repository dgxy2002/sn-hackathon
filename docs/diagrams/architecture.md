# Capability Architecture

## POC architecture

```mermaid
flowchart LR
    User[First-time working adult]

    subgraph Current[Current repository state]
        SPA[Vite vanilla-JS SPA]
        State[In-memory profile and navigation state]
        Fixtures[Synthetic OCR, benchmark, and plan fixtures]
        CurrentAPI[FastAPI fixture API]
        FixtureAgent[Typed fixture conversation agent]
        CurrentEvidence[Typed cached evidence service]
        Corpus[79 cached insurer brochures]
        ExtractCLI[OpenAI extraction CLI]
        RAGScripts[Supabase ingestion and retrieval CLIs]
        EmbeddingCache[(Local embedding cache)]
        CardScraper[Credit-card scraper CLI]
        SupabaseREST[Supabase REST API]
        ProductDB[(Hosted PostgreSQL and pgvector)]
    end

    subgraph External[Current external references]
        ProviderSources[Insurer brochure sources]
        SingSaver[SingSaver product pages]
        MoneySense[MoneySense guidance]
        MAS[MAS representatives register]
        OpenAI[OpenAI extraction and embeddings]
    end

    subgraph LocalTarget[Planned local Docker Compose runtime]
        API[E10 backend API and tool gateway]
        DB[(PostgreSQL and pgvector)]
        ObjectStore[(Optional S3-compatible store)]
        Coordinator[E11 runtime coordinator]
        SummaryAgent[E12 conversational summary agent]
        ToolPolicy[Allowlisted typed action registry]
        Extract[E04 OpenRouter document extraction]
        Profile[Versioned profile service]
        Rules[Deterministic decision engine]
        Retrieval[Grounded retrieval service]
        Compare[Phase 3B evidence comparison projector]
        ScraperLoop[E05 continuous scraper singleton]
        Events[Run events and metrics]
    end

    subgraph Provider[External configured provider]
        OpenRouter[OpenRouter 5.6 Luna]
    end

    User --> SPA
    SPA --> State
    SPA --> Fixtures
    SPA --> CurrentAPI
    CurrentAPI --> FixtureAgent
    CurrentAPI --> CurrentEvidence
    CurrentEvidence --> Corpus
    SPA --> MoneySense
    SPA --> MAS

    ProviderSources --> Corpus
    Corpus --> ExtractCLI
    ExtractCLI --> OpenAI
    ExtractCLI --> RAGScripts
    RAGScripts --> OpenAI
    RAGScripts --> EmbeddingCache
    RAGScripts --> SupabaseREST
    SingSaver --> CardScraper
    CardScraper --> SupabaseREST
    SupabaseREST --> ProductDB

    SPA -. versioned HTTP contracts .-> API
    SPA -. final-page panel and action timeline .-> SummaryAgent
    SummaryAgent -. conversation requests .-> API
    API -. /invocations .-> Coordinator
    API -. /conversations .-> Coordinator
    API -. capability routes .-> Extract
    API -. capability routes .-> Profile
    API -. capability routes .-> Retrieval
    API -. /evidence/compare .-> Compare
    API -. capability routes .-> Rules
    Coordinator -.-> Extract
    Coordinator -.-> Profile
    Coordinator -.-> Rules
    Coordinator -. evidence query .-> Retrieval
    Coordinator -. validated action plan .-> ToolPolicy
    ToolPolicy -. read or presentation .-> Retrieval
    ToolPolicy -. confirmed profile patch .-> Profile
    ToolPolicy -. deterministic rerun .-> Rules
    Retrieval -.-> DB
    Compare -. comparison-eligible fields .-> Retrieval
    ScraperLoop -. normalized products .-> DB
    ScraperLoop -. permitted snapshots .-> ObjectStore
    Extract -. PDF or image .-> OpenRouter
    OpenRouter -. extracted fields .-> Extract
    Coordinator -. immutable decision .-> OpenRouter
    OpenRouter -. explanation .-> Coordinator
    Coordinator -.-> Events
    Events -.-> DB
    Coordinator -. result .-> API
    API -. cited answer, proposal, or revision .-> SummaryAgent
    SummaryAgent -. dynamic comparison delta .-> SPA

    classDef implemented fill:#e7f4ed,stroke:#246b45,color:#123b28;
    classDef simulated fill:#fff3d6,stroke:#a66500,color:#573900;
    classDef planned fill:#edf1f7,stroke:#53657d,color:#263545,stroke-dasharray: 5 4;
    class SPA,State,CurrentAPI,CurrentEvidence,Corpus,ExtractCLI,RAGScripts,EmbeddingCache,CardScraper,SupabaseREST,ProductDB,OpenAI implemented;
    class Fixtures,FixtureAgent simulated;
    class API,DB,ObjectStore,Coordinator,SummaryAgent,ToolPolicy,Extract,Profile,Rules,Retrieval,Compare,ScraperLoop,Events,OpenRouter planned;
```

## Boundary notes

- The current user journey keeps profile, upload, extraction, gap, and recommendation data in [`frontend/src/main.js`](../../frontend/src/main.js), but the final `Ask CoverCheck` panel calls the FastAPI conversation routes in [`backend/app/main.py`](../../backend/app/main.py).
- The conversation and evidence routes now use a typed cached evidence service for cited real-product exploration. They do not alter the synthetic plan ranking.
- Darren's separate RAG slice extracts 79 cached brochures into 87 policy rows, normalizes 71 unique policy slugs, prepares 1,319 candidate chunks, and retrieves typed evidence through a Supabase-backed CLI.
- `CurrentAPI` reads the committed cached corpus through a typed E10/E06 boundary. Supabase remains an optional adapter; local PostgreSQL/pgvector remains the target.
- All cached records may be searched for read-only questions and exploration, but every result carries approval/evidence state and cannot enter E07's synthetic ranking.
- Phase 3B adds a comparison projector for a small comparison-eligible subset. It returns neutrally ordered cited fields and cannot invoke E07 or mutate canonical state.
- OpenAI owns current offline brochure extraction and embeddings. OpenRouter remains the configured E04/E11 provider for user-document extraction and explanation.
- [E10](../epics/E10-backend-api-and-poc-persistence.md) owns transport, shared schema validation, typed errors, and disposable synthetic state; it does not own capability business rules.
- Direct read-only E10/E06 retrieval does not require E11. [E11](../epics/E11-runtime-orchestration-and-operations.md) owns consequential proposals, confirmed changes, deterministic reruns, revisions, replay, undo, OpenRouter runtime integration, and operational coordination.
- [E12](../epics/E12-conversational-summary-agent.md) owns the final-page agent experience and integration. E11 executes its allowlisted typed tools; E03/E04/E06/E07 retain profile, extraction, retrieval, and deterministic decision authority.
- Navigation, focus, sorting, filtering, and read-only cached-plan exploration may apply immediately. Profile, canonical comparison, and reviewed extraction changes require confirmation, immutable input versions, and a fresh E07 result before the canonical summary changes.
- Real-product ranking remains disabled until the separate Phase 6 data, E07, E08, DEC-004, and compliance gates pass. Public ranked mode additionally requires E09 approval.
- Model output cannot become HTML, JavaScript, selectors, coordinates, SQL, arbitrary URLs, or canonical recommendation values.
- The local target is Docker Compose with `.env` configuration. OpenRouter `5.6 Luna` handles policy extraction and grounded explanation; the exact model slug remains an explicit configuration decision.
- Supabase/PostgREST is the first RAG integration adapter because it is implemented. This temporary delivery deviation does not change the target local PostgreSQL/pgvector store or its later RDS PostgreSQL migration.
- Amazon Bedrock and AgentCore are optional future adapters and are not required for local execution.
- Production identity, durable personal data, private document storage, and operational hardening are intentionally deferred to [E09](../epics/E09-productionisation-and-security.md).