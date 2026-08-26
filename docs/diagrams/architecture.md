# Capability Architecture

## POC architecture

```mermaid
flowchart LR
    User[First-time working adult]

    subgraph Current[Current repository state]
        SPA[Vite vanilla-JS SPA]
        State[In-memory profile and navigation state]
        Fixtures[Synthetic OCR, benchmark, and plan fixtures]
        Scraper[Python source scraper CLI]
        SupabaseREST[Supabase REST API]
        ProductDB[(Product and scrape-log tables)]
    end

    subgraph External[Current external references]
        SingSaver[SingSaver product pages]
        MoneySense[MoneySense guidance]
        MAS[MAS representatives register]
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
        ScraperLoop[E05 continuous scraper singleton]
        Events[Run events and metrics]
    end

    subgraph Provider[External configured provider]
        OpenRouter[OpenRouter 5.6 Luna]
    end

    User --> SPA
    SPA --> State
    SPA --> Fixtures
    SPA --> MoneySense
    SPA --> MAS

    SingSaver --> Scraper
    Scraper --> SupabaseREST
    SupabaseREST --> ProductDB

    SPA -. versioned HTTP contracts .-> API
    SPA -. final-page panel and action timeline .-> SummaryAgent
    SummaryAgent -. conversation requests .-> API
    API -. /invocations .-> Coordinator
    API -. /conversations .-> Coordinator
    API -. capability routes .-> Extract
    API -. capability routes .-> Profile
    API -. capability routes .-> Retrieval
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
    class SPA,State,Scraper,SupabaseREST,ProductDB implemented;
    class Fixtures simulated;
    class API,DB,ObjectStore,Coordinator,SummaryAgent,ToolPolicy,Extract,Profile,Rules,Retrieval,ScraperLoop,Events,OpenRouter planned;
```

## Boundary notes

- The current user journey runs entirely in [`frontend/src/main.js`](../../frontend/src/main.js). It does not call a backend.
- Upload, OCR output, the pilot benchmark, and plan recommendations are currently simulated with synthetic values in the SPA.
- [`backend/scraper/card_scraper.py`](../../backend/scraper/card_scraper.py) is a separate working ingestion POC for credit cards; it is not yet an insurance retriever.
- [`backend/scraper/supabase_schema.sql`](../../backend/scraper/supabase_schema.sql) defines the insurance and pgvector foundation, but no frontend or RAG runtime currently consumes it.
- [E10](../epics/E10-backend-api-and-poc-persistence.md) owns transport, shared schema validation, typed errors, and disposable synthetic state; it does not own capability business rules.
- [E11](../epics/E11-runtime-orchestration-and-operations.md) owns the bounded coordinator, OpenRouter runtime integration, and operational coordination; capability services remain independently testable.
- [E12](../epics/E12-conversational-summary-agent.md) owns the final-page agent experience and integration. E11 executes its allowlisted typed tools; E03/E04/E06/E07 retain profile, extraction, retrieval, and deterministic decision authority.
- Navigation, focus, sorting, filtering, and temporary approved-plan exploration may apply immediately. Profile, canonical comparison, and reviewed extraction changes require confirmation, immutable input versions, and a fresh E07 result before the canonical summary changes.
- Model output cannot become HTML, JavaScript, selectors, coordinates, SQL, arbitrary URLs, or canonical recommendation values.
- The local target is Docker Compose with `.env` configuration. OpenRouter `5.6 Luna` handles policy extraction and grounded explanation; the exact model slug remains an explicit configuration decision.
- The implemented Supabase proof remains repository evidence, but the target local application store is PostgreSQL/pgvector so it can later move to RDS PostgreSQL.
- Amazon Bedrock and AgentCore are optional future adapters and are not required for local execution.
- Production identity, durable personal data, private document storage, and operational hardening are intentionally deferred to [E09](../epics/E09-productionisation-and-security.md).