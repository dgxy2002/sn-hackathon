# E05 Backlog - Source Data Ingestion POC

**Epic:** [E05 - Source Data Ingestion POC](../epics/E05-source-data-ingestion-poc.md)
**Owner:** Darren

## E05-T01 - Build controlled scraping CLI

| Field | Value |
|---|---|
| Status | Done |
| Priority | P1 |
| Size | M |
| Depends on | None |

**User story:** As a data operator, I need bounded and observable scraping controls so I can validate ingestion without uncontrolled writes or traffic.

**Requirements:** URS-FR-016, URS-NFR-004, URS-NFR-007, URS-NFR-012; PRD-FR-007, PRD-FR-017, PRD-NFR-005, PRD-NFR-011.

**Acceptance criteria:**

- [x] The CLI supports dry-run, limit, source selection, delay, timeout, and verbose modes.
- [x] Network and configuration failures return clear nonzero exits.
- [x] Database writes require explicit credentials and non-dry-run execution.

**Evidence:** [`backend/scraper/card_scraper.py`](../../backend/scraper/card_scraper.py).

## E05-T02 - Normalize listing and detail records

| Field | Value |
|---|---|
| Status | Done |
| Priority | P1 |
| Size | M |
| Depends on | E05-T01 |

**User story:** As a retrieval developer, I need source pages normalized into typed records so downstream ingestion does not depend on raw HTML.

**Requirements:** URS-FR-010, URS-FR-011, URS-FR-016, URS-NFR-004, URS-NFR-012; PRD-FR-007, PRD-FR-017, PRD-NFR-003, PRD-NFR-011.

**Acceptance criteria:**

- [x] Listing identity, links, issuer, image, and summary fields are parsed.
- [x] Detail fields and raw source details are retained.
- [x] Records carry source and scrape timestamps.

**Evidence:** `ListingCard`, `CardPage`, `parse_listing`, and `parse_page` in [`backend/scraper/card_scraper.py`](../../backend/scraper/card_scraper.py).

## E05-T03 - Persist idempotent product and scrape metadata

| Field | Value |
|---|---|
| Status | Done |
| Priority | P1 |
| Size | M |
| Depends on | E05-T02 |

**User story:** As a data operator, I need repeatable upserts and scrape logs so freshness and failed runs can be inspected.

**Requirements:** URS-FR-016, URS-NFR-004, URS-NFR-007, URS-NFR-012; PRD-FR-007, PRD-FR-017, PRD-NFR-003, PRD-NFR-008, PRD-NFR-011.

**Acceptance criteria:**

- [x] Product records have stable source IDs and data hashes.
- [x] Supabase REST upsert is implemented.
- [x] Schemas retain scrape status, timestamps, token counts, and cost fields.

**Evidence:** [`backend/scraper/card_scraper.py`](../../backend/scraper/card_scraper.py), [`backend/scraper/credit_card_schema.sql`](../../backend/scraper/credit_card_schema.sql), [`backend/scraper/supabase_schema.sql`](../../backend/scraper/supabase_schema.sql).

## E05-T04 - Package one continuous local scraper

| Field | Value |
|---|---|
| Status | Done |
| Priority | P1 |
| Size | M |
| Depends on | E05-T03, E10-T06 |

**User story:** As a data operator, I need one Dockerized scraper process that continuously refreshes due sources without manual CLI execution.

**Requirements:** URS-FR-021, URS-FR-025, URS-NFR-012, URS-NFR-014, URS-NFR-017; PRD-FR-026, PRD-FR-030, PRD-NFR-018, PRD-NFR-021.

**Acceptance criteria:**

- [x] A scraper image runs one long-lived loop and handles termination cleanly.
- [x] Docker Compose configures exactly one scraper service instance.
- [x] `.env.example` documents source allowlist, freshness interval, timeout, delay, retry, and database settings.
- [x] Each cycle identifies due approved sources and sleeps or waits without busy polling when none are due.
- [x] Health behavior distinguishes running, degraded, stale, and failed states.

## E05-T05 - Enforce singleton lease and freshness lifecycle

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P1 |
| Size | L |
| Depends on | E05-T04, E06-T01 |

**User story:** As a data operator, I need idempotent leasing, versioning, and retries so the continuous scraper cannot create concurrent or stale active records.

**Requirements:** URS-FR-016, URS-FR-025, URS-NFR-010, URS-NFR-012; PRD-FR-017, PRD-FR-030, PRD-NFR-011, PRD-NFR-015.

**Acceptance criteria:**

- [x] A database-backed lease prevents concurrent active scraper loops even if two processes start.
- [ ] The lifecycle is due-source selection, fetch, parse, normalize, hash/version, upsert, optional index, log, and `next_scrape_due` update.
- [ ] Unchanged content does not create a new active version.
- [ ] Failures use bounded exponential backoff and retain the prior verified version.
- [ ] Metrics expose last success, last failure, consecutive failures, source age, records changed, and next due time.

## E05-T06 - Prepare the scraper for AWS Fargate

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | M |
| Depends on | E05-T05, E10-T07 |

**User story:** As a deployment owner, I need the locally tested scraper image mapped to one managed AWS runtime without changing scraper code.

**Requirements:** URS-FR-024, URS-FR-025, URS-NFR-014, URS-NFR-015, URS-NFR-017; PRD-FR-029, PRD-FR-030, PRD-NFR-019, PRD-NFR-021.

**Acceptance criteria:**

- [ ] The image publish target is ECR and the runtime target is an ECS Fargate service with desired count one.
- [ ] Secrets come from Secrets Manager and approved-source settings use task configuration or Parameter Store.
- [ ] The task uses private networking with controlled outbound access to approved sites and dependencies.
- [ ] CloudWatch collects logs and alarms on stopped tasks, repeated failures, and stale sources.
- [ ] The database lease remains enabled as defense in depth.