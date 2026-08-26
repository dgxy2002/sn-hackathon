# Technical Diagrams

These diagrams describe the CoverCheck SG POC and its smallest intended integration path. They deliberately distinguish repository-backed behavior from simulated or planned behavior.

| Document | Purpose |
|---|---|
| [Architecture diagram](architecture.md) | Current repository state and target local capability architecture |
| [Local topology](local-topology.md) | Docker Compose services, health boundaries, local `.env`, volumes, and OpenRouter access |
| [AWS topology](aws-topology.md) | AWS target topology and service mapping for each epic/module |
| [Workflow diagram](workflow.md) | User and system workflow from readiness quiz through conversational exploration and dynamic revision |
| [Sequence diagram](sequence.md) | Current browser-only flow, target local OpenRouter flow, and conversational read/change paths |
| [ER diagram](er-diagram.md) | Current SQL model plus proposed workflow, conversation, action, and summary-revision state |

## Notation

- **Solid edge:** Implemented repository behavior or an enforced database relationship.
- **Dashed edge:** Planned integration or logical relationship without a database foreign key.
- **Simulated:** Interactive POC UI backed by embedded synthetic values rather than a live service.
- **POC target:** The smallest integration intended for the hackathon, not a production deployment.
- **AWS target:** A planned managed-service migration for the same containers and contracts, not evidence that deployment exists.

The related ownership and DOD live in the [epic register](../epics/README.md).