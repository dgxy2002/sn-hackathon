# E06 - Insurance Retrieval and RAG

| Field | Value |
|---|---|
| Primary owner | Darren |
| Priority | P1 |
| Status | In progress |
| Outcome | Product comparisons use small, dated evidence records retrieved from approved Singapore insurance sources. |

## Scope

- Acquire a narrow set of permitted insurer and official-source documents.
- Normalize products, versions, effective dates, source URLs, and evidence spans.
- Store products and chunks in local PostgreSQL/pgvector and retrieve evidence by need and product category.
- Expose retrieval through the backend API container with metadata, full-text, and filter fallback when embeddings are unavailable.
- Keep embedding and model providers configuration-driven rather than AWS-dependent.
- Migrate the same schema to RDS PostgreSQL/pgvector and permitted snapshots to S3 later.
- Return citations and freshness metadata without making the final recommendation.
- Expose typed exploration over the approved catalogue for conversational alternatives and temporary comparisons.

## Requirements traceability

- **URS:** [URS-FR-010, URS-FR-011, URS-FR-015, URS-FR-016, URS-FR-017, URS-FR-020, URS-FR-021, URS-FR-024, URS-FR-028, URS-FR-029, URS-NFR-004, URS-NFR-007, URS-NFR-010, URS-NFR-012, URS-NFR-015, URS-NFR-016, URS-NFR-017, URS-NFR-019](../urs/URS.md)
- **PRD:** [PRD-FR-007, PRD-FR-008, PRD-FR-017, PRD-FR-018, PRD-FR-021, PRD-FR-026, PRD-FR-029, PRD-FR-033, PRD-FR-034, PRD-FR-035, PRD-NFR-003, PRD-NFR-005, PRD-NFR-011, PRD-NFR-015, PRD-NFR-017, PRD-NFR-020, PRD-NFR-021, PRD-NFR-022](../prd/PRD.md)
- **Backlog:** [E06 tickets](../backlog/E06-insurance-retrieval-and-rag.md)

## Repository evidence

- [`backend/scraper/supabase_schema.sql`](../../backend/scraper/supabase_schema.sql) enables pgvector and defines insurers, policies, document chunks, and scrape logs.
- [`backend/scraper/card_scraper.py`](../../backend/scraper/card_scraper.py) provides the completed ingestion pattern from E05.
- [`docs/PLAN.md`](../PLAN.md) defines the information-system contract and sourcing constraints.

## Definition of done

- [ ] An approved source list documents terms and retrieval method for each source.
- [ ] At least one product category from at least two providers is ingested with version and effective date.
- [ ] Fixed evaluation queries retrieve the expected reviewed source in the top five at least 90% of the time.
- [ ] Every returned product claim includes an evidence span, URL, and retrieval or effective date.
- [ ] Missing or stale evidence produces an explicit unsupported result rather than a generated fact.
- [ ] Superseded and conflicting product versions remain auditable and are not silently merged into current results.
- [ ] Retrieval contract tests pass against local PostgreSQL/pgvector and the deterministic non-embedding fallback.
- [ ] The RDS PostgreSQL/pgvector and S3 migration mapping is documented without changing evidence contracts.
- [ ] Conversational search returns only approved catalogue records with eligibility, provenance, freshness, and explicit no-evidence behavior.

## POC boundary

No exhaustive market coverage, live scraping during the judged demo, or claim of independent whole-market advice is required.