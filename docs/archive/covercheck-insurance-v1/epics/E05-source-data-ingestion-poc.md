# E05 - Source Data Ingestion POC

| Field | Value |
|---|---|
| Primary owner | Darren |
| Priority | P1 |
| Status | In progress |
| Outcome | Target: one continuously running scraper keeps approved insurer offerings fresh through a reusable fetch, parse, normalize, version, and PostgreSQL-upsert pipeline; the current worker holds a singleton lease and waits because no insurance source is approved for fetching. |

## Scope

- In plain language, E05 collects what insurers currently offer; E04 reads what the user already has.
- Command-line scraping with limits, timeouts, delays, dry-run mode, and clear failures.
- Structured listing and detail-page parsing.
- Idempotent PostgreSQL upsert with source, hash, version, freshness, and scrape metadata.
- Relational schemas for product records and scrape logs.
- Package the scraper as a Docker image and run exactly one continuous loop in Docker Compose.
- Identify due sources, fetch, parse, normalize, hash, upsert, optionally index, log, update `next_scrape_due`, and retry with bounded backoff.
- Use a database-backed singleton lease in addition to one configured replica.
- Reuse the image on ECS Fargate with desired count one, Secrets Manager configuration, and CloudWatch logs and freshness alarms.

## Requirements traceability

- **URS:** [URS-FR-010, URS-FR-011, URS-FR-016, URS-FR-021, URS-FR-024, URS-FR-025, URS-NFR-004, URS-NFR-007, URS-NFR-012, URS-NFR-014, URS-NFR-015, URS-NFR-017](../urs/URS.md)
- **PRD:** [PRD-FR-007, PRD-FR-017, PRD-FR-026, PRD-FR-029, PRD-FR-030, PRD-NFR-003, PRD-NFR-005, PRD-NFR-008, PRD-NFR-011, PRD-NFR-018, PRD-NFR-019, PRD-NFR-021](../prd/PRD.md)
- **Backlog:** [E05 tickets](../backlog/E05-source-data-ingestion-poc.md)

## Repository evidence

- [`backend/scraper/card_scraper.py`](../../backend/scraper/card_scraper.py) implements the scraper and Supabase REST client.
- [`backend/scraper/credit_card_schema.sql`](../../backend/scraper/credit_card_schema.sql) defines the current credit-card and scrape-log tables.
- [`backend/scraper/supabase_schema.sql`](../../backend/scraper/supabase_schema.sql) defines broader insurance and retrieval-ready tables.
- [`backend/scraper/requirements.txt`](../../backend/scraper/requirements.txt) pins the scraper dependencies.

## Definition of done

- [x] The CLI can limit work and run without database writes.
- [x] Listing and detail content are normalized into structured records.
- [x] Records can be upserted through the Supabase REST API.
- [x] Source, retrieval time, raw details, and scrape outcomes can be retained.
- [x] Schema and dependency setup are committed with the scraper.
- [x] The scraper image runs one healthy continuous process in Docker Compose and shuts down cleanly.
- [x] A database lease prevents two scraper loops from processing due work concurrently.
- [ ] Each cycle records source hash, version, outcome, retry state, freshness, and `next_scrape_due`.
- [ ] An insurance-specific approved source passes the continuous pipeline into local PostgreSQL.
- [ ] The ECS target specifies one Fargate task, Secrets Manager injection, controlled egress, and CloudWatch health and freshness alarms.

## POC boundary

The original implemented source is a credit-card site. The insurance worker lifecycle, PostgreSQL lease, and idle behavior are operational, but no insurance source is approved for fetching, so insurance-specific acquisition and complete per-source lifecycle evidence remain incomplete; retrieval from cached data belongs to E06. See the [integrated runtime acceptance](../evaluation/2026-08-28-integrated-runtime-browser-acceptance.md).