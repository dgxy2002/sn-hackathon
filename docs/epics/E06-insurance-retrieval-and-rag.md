# E06 - Insurance Retrieval and RAG

| Field | Value |
|---|---|
| Primary owner | Darren |
| Priority | P1 |
| Status | In progress |
| Outcome | Read-only questions, catalogue exploration, and neutral evidence comparison use dated records from cached Singapore insurance sources without changing synthetic recommendations. |

## Scope

- Register the complete cached insurer corpus, assign each record an explicit approval and evidence state, and never treat cache inclusion as source approval.
- Normalize products, document as-of dates, product effective dates, versions, retrieval dates, source URLs, and evidence spans without substituting one date type for another.
- Integrate the implemented Supabase/PostgREST store first behind a replaceable adapter while retaining local PostgreSQL/pgvector as the approved target.
- Expose retrieval through the backend API container with metadata, full-text, and filter fallback when embeddings are unavailable.
- Keep OpenAI brochure extraction and embeddings separate from the configured OpenRouter E04 user-document extraction and Amazon Bedrock E11 explanation capabilities.
- Migrate the same schema to RDS PostgreSQL/pgvector and permitted snapshots to S3 later.
- Return citations, approval state, and freshness metadata without making or changing a recommendation.
- Expose typed read-only questions and broad exploration across all cached records while keeping E07 ranking synthetic and deterministic.
- Classify records separately as searchable, comparison eligible, or ranking eligible and expose a normalized comparison projection for a reviewed pilot subset.

## Requirements traceability

- **URS:** [URS-FR-010, URS-FR-011, URS-FR-015, URS-FR-016, URS-FR-017, URS-FR-020, URS-FR-021, URS-FR-024, URS-FR-028, URS-FR-029, URS-NFR-004, URS-NFR-007, URS-NFR-010, URS-NFR-012, URS-NFR-015, URS-NFR-016, URS-NFR-017, URS-NFR-019](../urs/URS.md)
- **PRD:** [PRD-FR-007, PRD-FR-008, PRD-FR-017, PRD-FR-018, PRD-FR-021, PRD-FR-026, PRD-FR-029, PRD-FR-033, PRD-FR-034, PRD-FR-035, PRD-NFR-003, PRD-NFR-005, PRD-NFR-011, PRD-NFR-015, PRD-NFR-017, PRD-NFR-020, PRD-NFR-021, PRD-NFR-022](../prd/PRD.md)
- **Backlog:** [E06 tickets](../backlog/E06-insurance-retrieval-and-rag.md)
- **Phase 3B:** URS-FR-033, URS-FR-034, URS-NFR-022; PRD-FR-039, PRD-FR-040, PRD-NFR-028.

## Repository evidence

- [`backend/scraper/extract_insurance_openai.py`](../../backend/scraper/extract_insurance_openai.py) and the committed extraction artifacts cover 79 brochures and 87 structured policy rows.
- [`backend/scraper/ingest_insurance_supabase.py`](../../backend/scraper/ingest_insurance_supabase.py) normalizes 71 unique policy slugs and prepares 1,319 evidence chunks.
- [`backend/scraper/rag_common.py`](../../backend/scraper/rag_common.py) and [`backend/scraper/query_insurance_rag.py`](../../backend/scraper/query_insurance_rag.py) provide cached OpenAI embeddings, Supabase/PostgREST access, and a typed retrieval CLI.
- [`backend/scraper/supabase_schema.sql`](../../backend/scraper/supabase_schema.sql) enables pgvector and defines insurers, policies, document chunks, retrieval RPCs, and scrape logs.
- [`backend/app/evidence.py`](../../backend/app/evidence.py) exposes cached, synthetic, and Supabase adapters through one typed read-only service; [`backend/app/main.py`](../../backend/app/main.py) publishes it at `POST /v1/evidence/search`.
- The [cached evidence browser smoke test](../evaluation/2026-08-28-cached-evidence-browser-smoke-test.md) records the containerized website path and verifies that cached exploration does not alter E07's synthetic comparison.

## Definition of done

- [x] Offline preparation validates 79 cached brochures, 87 structured policy rows, 71 unique policy slugs, and 1,319 candidate chunks.
- [x] The seven Markdown-undated Great Eastern files have been checked against their downloaded official PDFs and their brochure as-of dates and version labels recorded in the [integration decision record](../evaluation/2026-08-28-rag-website-integration-decisions.md).
- [x] Every cached record has a source-governance and evidence state; unverified records remain visibly distinct from approved evidence.
- [ ] All 79 brochure as-of statements are retained in structured records, unresolved dates remain explicitly unknown, and the GREAT SupremeHealth/GREAT TotalCare 2 document-identity mismatch is resolved.
- [x] Document as-of date, product effective date, product version, and retrieval date are stored as distinct fields with provenance.
- [x] `POST /v1/evidence/search` returns one contract from Supabase and deterministic fixture adapters without coupling consumers to either store.
- [x] All cached records are available to read-only search, while real-product evidence cannot enter or alter E07 synthetic ranking.
- [ ] Fixed evaluation queries retrieve the expected reviewed source in the top five at least 90% of the time.
- [x] Every returned product claim includes an evidence span, URL where available, date type, evidence state, and synthetic status.
- [x] Missing or stale evidence produces an explicit unsupported result rather than a generated fact.
- [ ] Superseded and conflicting product versions remain auditable and are not silently merged into current results.
- [x] Retrieval contract tests pass against local PostgreSQL/pgvector and the deterministic non-embedding fallback.
- [x] The RDS PostgreSQL/pgvector and S3 migration mapping is documented without changing evidence contracts.
- [x] Conversational search exposes approval, eligibility, provenance, freshness, and explicit no-evidence behavior for every cached catalogue record.
- [ ] A small one-category subset passes source permission, product identity, freshness, comparable-unit, and field-provenance gates and is exposed through a comparison-eligible projection.
- [x] Searchable, comparison-eligible, and ranking-eligible states remain distinct and include machine-readable gate reasons.

**Acceptance evidence:** [Integrated runtime and browser acceptance](../evaluation/2026-08-28-integrated-runtime-browser-acceptance.md) records 1,777 local PostgreSQL evidence rows and the configured comparison gate. Source permission and the reviewed real-product Phase 3B subset remain incomplete.

## POC boundary

The cached catalogue is broad but not exhaustive and must not be described as whole-market coverage or the basis for an absolute-best-plan claim. Real RAG remains read-only educational evidence; E07 continues to rank only visibly synthetic plans. No live scraping during the judged demo is required.