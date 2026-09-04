# Local Docker Compose Topology

## Accepted local topology

The implemented website and API share a typed read-only evidence service. Runtime migrations load the committed corpus into local PostgreSQL, which is the demonstrated credential-free adapter. Supabase remains optional.

```mermaid
flowchart LR
    Browser[Browser]
    Web[Vite or Nginx web service]
    API[FastAPI API]
    Agent[Typed conversation service]
    Evidence[Typed read-only evidence service]

    Corpus[79 cached brochures]
    Cached[Deterministic cached adapter]
    Live[Optional Supabase adapter]
    Supabase[(Hosted Supabase<br/>PostgreSQL and pgvector)]
    LocalDB[(Compose PostgreSQL<br/>pgvector and evidence records)]
    Scraper[Singleton scraper<br/>lease and heartbeat]

    Browser --> Web
    Web --> API
    API --> Agent
    Agent --> Evidence
    API --> Evidence
    Evidence --> Cached
    Cached --> Corpus
    Evidence --> LocalDB
    Evidence --> Live
    Live --> Supabase
    Scraper -->|waits without approved sources| LocalDB
```

The local-database path and scraper lease were accepted on 28 August 2026. Provider credentials stay server-side, adapter mode is returned in contracts, and read-only evidence cannot change E07's synthetic ranking. No cached source is approved for live fetching or real-product comparison.

## Remaining configured-service topology

Web, backend, scraper, PostgreSQL retrieval, fixture workflows, and the typed Bedrock explanation adapter are implemented. This diagram adds the credentialed Bedrock call, still-pending OpenRouter extraction, and optional object-store paths.

```mermaid
flowchart TB
    Browser[Desktop or mobile browser]
    Env[Uncommitted .env]
    OpenRouter[OpenRouter API<br/>E04 extraction pending]
    Bedrock[Amazon Bedrock<br/>E11 grounded explanation]
    Sources[Approved public sources]

    subgraph Host[Developer machine]
        subgraph Compose[Docker Compose network]
            Web[web container<br/>Vite application, E12 panel,<br/>action timeline and dynamic summary]
            API[backend container<br/>API, conversation and revisions,<br/>profile, extraction, retrieval,<br/>decision and coordinator]
            Scraper[scraper container<br/>one continuous process]
            DB[(postgres container<br/>PostgreSQL and pgvector)]
            Store[(optional object-store container<br/>S3-compatible snapshots)]
            DBVolume[(database volume)]
            StoreVolume[(object volume)]
        end
    end

    Browser -->|HTTP| Web
    Web -->|versioned HTTP API| API
    API -->|SQL| DB
    API -->|temporary or permitted objects| Store
    API -->|HTTPS: extraction| OpenRouter
    API -->|Converse: immutable E07 result| Bedrock
    Scraper -->|HTTPS with allowlist and limits| Sources
    Scraper -->|lease, upsert, logs, freshness| DB
    Scraper -->|permitted source snapshots| Store
    DB --- DBVolume
    Store --- StoreVolume
    Env -. runtime configuration .-> Web
    Env -. runtime configuration and secrets .-> API
    Env -. runtime configuration and secrets .-> Scraper
```

## Service contract

| Service | Epic ownership | Required health behavior | AWS target |
|---|---|---|---|
| `web` | E01, E08, E10, E12 | Static application, final-page agent, and dynamic summary respond; backend URL is configured | ECR image on ECS Fargate behind ALB, optionally CloudFront later |
| `backend` | E03, E04, E06, E07, E10, E11, E12 | Process, database, object store, provider, conversation, action-policy, and revision modes are reported without secrets | ECR image on ECS Fargate behind ALB |
| `scraper` | E05, E11 | Exactly one loop holds the database lease; last success and source freshness are visible | ECR image on ECS Fargate Service with desired count one |
| `postgres` | E05, E06, E10 | Ready for SQL, required migrations, and pgvector | RDS PostgreSQL with pgvector |
| `object-store` | E04, E05, E06, E10 | Optional S3-compatible endpoint and bucket are ready | Amazon S3 |

## Configuration boundary

Local `.env` contains values such as `APP_ENV`, `DATABASE_URL`, `OBJECT_STORE_ENDPOINT`, `OBJECT_STORE_BUCKET`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `LLM_PROVIDER`, `BEDROCK_MODEL_ID`, `AWS_REGION`, `DOCUMENT_AI_PROVIDER`, `AGENT_MAX_ACTIONS`, `CONVERSATION_MAX_TURNS`, `SUMMARY_REVISION_LIMIT`, `SCRAPE_INTERVAL_SECONDS`, and `SCRAPE_LEASE_TTL_SECONDS`. Only `.env.example` with safe placeholders belongs in version control.

The web browser never receives provider, database, or object-store credentials. E12 adds no container: it uses the web and backend images plus disposable PostgreSQL session state. Fixture mode works without AWS or OpenRouter credentials; live E11 mode uses boto3's standard credential chain.