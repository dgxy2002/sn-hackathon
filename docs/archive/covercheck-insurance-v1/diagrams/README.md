# Technical Diagrams

These diagrams describe the CoverCheck SG POC and its smallest intended integration path. They deliberately distinguish repository-backed behavior from simulated or planned behavior.

| Document | Purpose |
|---|---|
| [Architecture diagram](architecture.md) | Accepted repository/runtime state plus provider and pending capability paths |
| [Local topology](local-topology.md) | Accepted Docker Compose services, health boundaries, local `.env`, volumes, and pending configured services |
| [AWS topology](aws-topology.md) | AWS target topology and service mapping for each epic/module |
| [Workflow diagram](workflow.md) | User and system workflow from readiness quiz through conversational exploration and dynamic revision |
| [Sequence diagram](sequence.md) | Dated initial flows, Phase 3B evidence comparison, accepted fixture flow, Bedrock explanation, and pending OpenRouter extraction |
| [ER diagram](er-diagram.md) | Supabase and local POC SQL models plus proposed durable workflow, conversation, action, and summary-revision persistence |

## Notation

- **Solid edge:** Implemented repository behavior or an enforced database relationship.
- **Dashed edge:** Planned integration or logical relationship without a database foreign key.
- **Simulated:** Interactive POC UI backed by embedded synthetic values rather than a live service.
- **POC target:** The smallest integration intended for the hackathon, not a production deployment.
- **AWS target:** A planned managed-service migration for the same containers and contracts, not evidence that deployment exists.

The related ownership and DOD live in the [epic register](../epics/README.md).

The approved interim adapter, catalogue, provider, date-field, and orchestration decisions are recorded in the [RAG and website integration decision](../evaluation/2026-08-28-rag-website-integration-decisions.md). Phase 3B comparison and Phase 6 ranking gates are recorded in the [staged real-product decision](../evaluation/2026-08-28-real-product-comparison-and-ranking-stages.md). The interim Supabase path does not replace the local topology target.