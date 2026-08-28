# E06 Backlog - Insurance Retrieval and RAG

**Epic:** [E06 - Insurance Retrieval and RAG](../epics/E06-insurance-retrieval-and-rag.md)
**Owner:** Darren

## E06-T01 - Approve the POC insurance source set

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P1 |
| Size | S |
| Depends on | E05-T01 |

**User story:** As the product team, we need every cached source registered with an explicit evidence state so broad exploration does not imply that every record is approved, current, or suitable.

**Requirements:** URS-NFR-001, URS-NFR-004; PRD-FR-007, PRD-NFR-003, PRD-NFR-009.

**Acceptance criteria:**

- [x] The inventory contains 79 cached brochures across four providers and normalizes to 71 unique policy slugs.
- [ ] Every cached source is assigned an approval state such as approved, unverified, restricted, or rejected.
- [ ] Each source records owner, URL, retrieval method, terms or robots decision, and review date.
- [ ] Official and provider sources are preferred over aggregators.
- [x] Search results expose source approval and evidence state; cache inclusion alone never implies suitability or source approval.
- [x] The demo does not depend on live scraping.

## E06-T02 - Ingest normalized insurance products and evidence

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P1 |
| Size | L |
| Depends on | E06-T01, E08-T01 |

**User story:** As a read-only evidence consumer, I need versioned insurance plans and evidence spans so questions and exploration use known product terms rather than embedded UI text.

**Requirements:** URS-FR-010, URS-FR-011, URS-FR-016, URS-FR-020, URS-NFR-004, URS-NFR-011, URS-NFR-012; PRD-FR-007, PRD-FR-017, PRD-FR-021, PRD-NFR-003, PRD-NFR-008, PRD-NFR-011, PRD-NFR-015.

**Acceptance criteria:**

- [x] The offline preparation path normalizes 87 policy rows into 71 unique policy slugs and 1,319 candidate chunks.
- [x] The seven Markdown-undated Great Eastern files have official PDF footer research for brochure as-of date and version label.
- [x] Plan, provider, product version, document as-of date, product effective date, retrieval date, evidence state, and synthetic status are represented distinctly.
- [ ] Benefits, premiums, exclusions, and eligibility retain source evidence where available.
- [ ] Scrape or ingest outcomes are logged.

**Current evidence:** [`backend/scraper/extract_insurance_openai.py`](../../backend/scraper/extract_insurance_openai.py), [`backend/scraper/ingest_insurance_supabase.py`](../../backend/scraper/ingest_insurance_supabase.py), and the committed extraction artifacts implement structured extraction and normalized preparation for 87 policy rows across four providers. Seventy-two Markdown files contain a recognizable as-of statement; PDF-level review resolves the other seven files, but none of the structured rows retains an explicit effective date or version. The file named GREAT SupremeHealth contains a GREAT TotalCare 2 rider brochure and requires identity correction. Source approval, date enrichment, complete URLs and premiums, and ingest-run logging remain incomplete.

**Approved integration direction:** [RAG and website integration decisions](../evaluation/2026-08-28-rag-website-integration-decisions.md).

## E06-T03 - Implement filtered semantic retrieval

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P1 |
| Size | L |
| Depends on | E06-T02 |

**User story:** As the website and conversational agent, I need small relevant evidence records for a user need and category so read-only answers and exploration remain grounded and inspectable.

**Requirements:** URS-FR-010, URS-FR-011, URS-FR-015, URS-FR-017, URS-FR-020, URS-NFR-007, URS-NFR-010; PRD-FR-008, PRD-FR-018, PRD-FR-021, PRD-NFR-005, PRD-NFR-010, PRD-NFR-015, PRD-NFR-017.

**Acceptance criteria:**

- [ ] Documents are chunked and embedded with versioned metadata.
- [ ] Category and eligibility filters run before vector similarity.
- [x] Search covers all cached policy records and results include evidence span, source URL where available, date type, evidence state, synthetic status, and score.
- [x] Supabase and deterministic fixture adapters return the same E10 evidence contract.
- [ ] Unsupported or stale queries return an explicit no-evidence result.

**Current evidence:** [`backend/scraper/query_insurance_rag.py`](../../backend/scraper/query_insurance_rag.py), [`backend/scraper/rag_common.py`](../../backend/scraper/rag_common.py), and [`backend/scraper/supabase_schema.sql`](../../backend/scraper/supabase_schema.sql) implement evidence chunks, cached OpenAI embeddings, pgvector similarity, metadata pre-filtering, and typed CLI results. The CLI is not an application service: versioned metadata, evidence-state and freshness enforcement, complete citation URLs, deterministic fallback, E10 API exposure, and retrieval evaluation remain incomplete.

## E06-T04 - Evaluate retrieval quality and citation coverage

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | M |
| Depends on | E06-T03 |

**User story:** As a reviewer, I need fixed retrieval tests so we can prove that shown product facts come from expected sources.

**Requirements:** URS-FR-011, URS-FR-015, URS-FR-018, URS-FR-019, URS-NFR-004, URS-NFR-013; PRD-FR-008, PRD-FR-018, PRD-NFR-003, PRD-NFR-015, PRD-NFR-016.

**Acceptance criteria:**

- [ ] Reviewed queries and expected sources are written before execution.
- [ ] At least 90% contain the expected source in the top five.
- [ ] One hundred percent of displayed product claims carry citation and date.
- [ ] Failed and unsupported cases are included in the report.

## E06-T05 - Enforce evidence version and freshness policy

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | M |
| Depends on | E06-T02, E06-T03 |

**User story:** As a reviewer, I need stale and conflicting product evidence identified before recommendation use so old terms do not appear current.

**Requirements:** URS-FR-016, URS-FR-020, URS-NFR-004, URS-NFR-012; PRD-FR-017, PRD-FR-018, PRD-NFR-003, PRD-NFR-011, PRD-NFR-015.

**Acceptance criteria:**

- [ ] Products and chunks retain source, product version, effective date, retrieval date, hash, and verification state.
- [ ] `document_as_of_date`, `product_effective_date`, and `retrieved_at` remain distinct and retain their source or derivation.
- [x] Official PDF footer review records as-of and version evidence for the seven files whose Markdown omitted it.
- [ ] As-of and version evidence from all 79 brochures is extracted into structured records, including correction of the GREAT SupremeHealth/GREAT TotalCare 2 identity mismatch.
- [ ] Superseded versions remain auditable but are excluded from current retrieval by default.
- [ ] A configurable freshness rule labels stale evidence and prevents unsupported recommendation claims.
- [ ] Conflicting source versions produce a warning or no-evidence result rather than silent merging.
- [ ] Every displayed claim can be traced to the selected evidence version.

## E06-T06 - Run retrieval on local PostgreSQL and pgvector

| Field | Value |
|---|---|
| Status | Done |
| Priority | P1 |
| Size | L |
| Depends on | E06-T03, E10-T06 |

**User story:** As a developer, I need evidence retrieval to work entirely in the local Docker Compose stack before any managed AWS database is introduced.

**Requirements:** URS-FR-017, URS-FR-021, URS-NFR-010, URS-NFR-015, URS-NFR-016, URS-NFR-017; PRD-FR-018, PRD-FR-026, PRD-NFR-017, PRD-NFR-020, PRD-NFR-021.

**Acceptance criteria:**

- [x] PostgreSQL migrations enable pgvector and create versioned product, evidence, chunk, and scrape-log storage.
- [x] The backend API queries the Compose database rather than a cloud-only endpoint.
- [x] Metadata, filter, and full-text retrieval work when embeddings or an external provider are unavailable.
- [x] Health checks report database and index readiness.
- [x] Retrieval contract tests pass against both database and fixture adapters.

**Evidence:** [`backend/app/evidence.py`](../../backend/app/evidence.py), [`compose.yaml`](../../compose.yaml), and the [integrated runtime acceptance](../evaluation/2026-08-28-integrated-runtime-browser-acceptance.md), which records a live database dependency and 1,777 local evidence rows.

## E06-T07 - Document and verify the RDS and S3 migration

| Field | Value |
|---|---|
| Status | In progress |
| Priority | P1 |
| Size | M |
| Depends on | E06-T06, E10-T07 |

**User story:** As a deployment owner, I need local data adapters mapped to AWS managed services so migration changes configuration rather than retrieval behavior.

**Requirements:** URS-FR-024, URS-NFR-015, URS-NFR-016, URS-NFR-017; PRD-FR-029, PRD-NFR-019, PRD-NFR-020, PRD-NFR-021.

**Acceptance criteria:**

- [ ] Local PostgreSQL/pgvector maps to private RDS PostgreSQL with the same migrations and extension requirements.
- [ ] Permitted local snapshots map to a private versioned S3 bucket with lifecycle rules.
- [ ] Database and object-store secrets map from `.env` names to Secrets Manager task injection.
- [ ] Migration, rollback, connection-pool, backup, and restore assumptions are documented.
- [ ] Evidence and retrieval contracts remain unchanged.

## E06-T08 - Expose cached catalogue exploration

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | M |
| Depends on | E06-T05, E10-T04 |

**User story:** As a user, I need to explore the broad cached catalogue without mistaking unverified evidence or a temporary comparison for a recommendation.

**Requirements:** URS-FR-028, URS-FR-029, URS-NFR-004, URS-NFR-019; PRD-FR-033, PRD-FR-034, PRD-FR-035, PRD-NFR-003, PRD-NFR-015.

**Acceptance criteria:**

- [ ] A typed search accepts structured product, affordability, eligibility, and comparison filters rather than arbitrary source URLs.
- [ ] All cached catalogue records can be searched, with approval and evidence state applied to every result.
- [ ] Results preserve eligibility, exclusions, source spans, document as-of date, product effective date, retrieval date, freshness, and synthetic status.
- [ ] Stale, conflicting, missing, and no-evidence outcomes are explicit and cannot become cited facts.
- [x] Real-product exploration remains read-only and is distinguished from deterministic E07 synthetic recommendations.

**Current evidence:** [`backend/app/evidence.py`](../../backend/app/evidence.py), [`backend/app/contracts.py`](../../backend/app/contracts.py), [`backend/tests/test_evidence.py`](../../backend/tests/test_evidence.py), and the [integrated runtime acceptance](../evaluation/2026-08-28-integrated-runtime-browser-acceptance.md). Affordability and structured eligibility filters, complete source governance, and fixed retrieval evaluation remain pending.

## E06-T09 - Build the comparison-eligible product projection

| Field | Value |
|---|---|
| Status | Ready |
| Priority | P1 |
| Size | M |
| Depends on | E06-T01, E06-T02, E06-T05 |

**User story:** As a user comparing real products, I need a reviewed subset with normalized, cited fields so missing brochure data cannot be mistaken for a factual difference or suitability signal.

**Requirements:** URS-FR-033, URS-FR-034, URS-NFR-004, URS-NFR-022; PRD-FR-039, PRD-FR-040, PRD-NFR-003, PRD-NFR-015, PRD-NFR-028.

**Acceptance criteria:**

- [ ] A pilot subset of at least two products in one category has approved reuse, authoritative URLs, unambiguous identities, and non-stale/non-conflicting evidence state.
- [x] Each product records separate searchable, comparison-eligible, and ranking-eligible states plus machine-readable gate reasons.
- [x] Comparison fields use stable keys and normalized units for benefits, premiums, eligibility, exclusions, term, and other available facts.
- [x] Every populated field resolves to evidence, source, document/version state, and date type; missing fields remain `Unknown`.
- [x] Comparison eligibility requires only the approved evidence-mode gates and does not imply ranking eligibility or suitability.
- [x] Records outside the pilot subset remain searchable evidence and cannot enter the comparison projection.

**Current evidence:** The projection and rejection reasons are implemented and contract-tested. The live gate check in the [integrated runtime acceptance](../evaluation/2026-08-28-integrated-runtime-browser-acceptance.md) confirms that cached products remain blocked; source approval for the first real pilot subset is the remaining acceptance item.