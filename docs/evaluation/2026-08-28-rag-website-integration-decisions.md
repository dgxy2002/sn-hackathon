# RAG and Website Integration Decisions - 2026-08-28

## Document control

| Field | Value |
|---|---|
| Status | Approved implementation direction; documentation pass only |
| Decision date | 28 August 2026 |
| Scope | Connect Darren's read-only real-product RAG to the website through E10 without changing E07 synthetic ranking |
| Change boundary | No application, pipeline, schema, or corpus files changed in this pass |
| Plan boundary | `docs/PLAN.md` remains unchanged; local PostgreSQL/pgvector remains the approved target |

## Verified current state

Two working slices exist but are not connected:

1. Darren's RAG pipeline reads 79 cached brochure files, produces 87 structured policy rows, normalizes 71 unique policy slugs, prepares 1,319 candidate chunks, caches OpenAI embeddings locally, and retrieves typed evidence through a Supabase/PostgREST CLI.
2. The website calls FastAPI conversation routes for a typed fixture agent. It can render fixture citations and allowlisted focus/filter actions, but it does not call the RAG pipeline.

The extraction report was generated on 26 August 2026 and the database work is recent. Those timestamps establish processing recency only. They do not establish when policy terms became effective or whether a brochure remains the provider's current contractual source.

## Approved decisions

### Real-product usage

Real-product RAG is read-only throughout applicable website and conversational contexts. It may answer cited questions and support catalogue exploration. It cannot enter, replace, reorder, or otherwise alter E07's synthetic-plan ranking.

### Catalogue breadth and evidence state

All 71 cached policy records may be searched to improve discovery and avoid an artificially narrow view. Each result must expose an evidence state such as `approved`, `unverified`, `stale`, `conflicting`, or `unknown` plus its synthetic status. Cache inclusion does not mean source approval, currency, eligibility, affordability, or suitability.

Broad search cannot support an "absolute best plan" claim. The corpus is not exhaustive and has incomplete premiums, eligibility, exclusions, URLs, source approvals, and product-effective dates. The system must describe results as potentially relevant evidence from the cached corpus and preserve explicit unsupported outcomes.

### Runtime and adapters

The first integration uses the existing Supabase/PostgREST implementation because it is the only working RAG store. E10 will place it behind a typed evidence-service interface and provide a deterministic fixture adapter with the same contract. This is a temporary delivery deviation; it does not replace the local PostgreSQL/pgvector and Docker Compose target in the project plan.

The Supabase service-role key remains backend-only and must never reach the browser. Adapter mode must be visible in responses and the interface.

### Providers

OpenAI remains responsible for Darren's offline brochure extraction and `text-embedding-3-small` embeddings. OpenRouter remains the configured provider for E04 user-document extraction and E11 explanation/orchestration work. Provider IDs, model IDs, prompt versions, and usage must remain separately attributable.

### Orchestration order

Read-only evidence requests go directly through E10 to E06. E11 is not required as a relay for a typed query. E11 remains mandatory for consequential proposals, confirmed profile or extraction changes, deterministic E07 reruns, summary revisions, replay, and undo.

## Date and version research

The evidence contract must keep these fields distinct:

| Field | Meaning |
|---|---|
| `document_as_of_date` | Date the brochure says its information is correct or accurate as at |
| `product_effective_date` | Authoritative effective date for the product or policy terms |
| `retrieved_at` | Date and time the source was captured or processed |
| `document_version` | Provider-published brochure or document version label |

Seventy-two cached Markdown files contain a recognizable brochure as-of statement. The seven remaining Markdown files were checked against their downloaded official PDFs:

| Cached source | Brochure as-of date | Version evidence | Finding |
|---|---|---|---|
| GREAT Life Advantage 4, duplicated across two category folders | 17 October 2025 | `GLA4P/Ver3.0/202510` | Footer recovered from the downloaded official PDF |
| GREAT Life Multiplier, duplicated across two category folders | 1 October 2025 | `GLM/Ver4.0/202510` | Footer recovered from the downloaded official PDF |
| PayAssure | 17 August 2026 | `PAP/Ver 1.0/202608` | Footer recovered from the downloaded official PDF |
| PA Supreme | 17 August 2026 | `PASP/Ver 1.0/202608` | Footer recovered from the downloaded official PDF |
| File named GREAT SupremeHealth | 1 April 2026 | `GSHP/Ver1.0/202604` | The asset content describes GREAT TotalCare 2 as a rider complementing GREAT SupremeHealth; document identity must be corrected before approval |

All 79 cached source files therefore have recoverable brochure as-of evidence, but none of the 87 structured policy rows currently stores an explicit effective date or product version. The footer dates are document as-of dates, not contractual product-effective dates.

## Delivery sequence

### Phase 0 - Evidence integrity and contract

Owner: Darren with E10 contract review.

- Define one evidence response with stable evidence ID, policy ID, provider, product, field, quoted span, source URL, evidence state, synthetic status, similarity, and the three distinct date fields.
- Register all cached records and assign source-approval/evidence state.
- Extract as-of and version evidence from all 79 brochures.
- Correct the GREAT SupremeHealth/GREAT TotalCare 2 identity mismatch.
- Restore the six missing FWD source URLs where authoritative URLs can be verified.
- Preserve unknown values; do not infer premiums, exclusions, eligibility, or product-effective dates from capture time.

### Phase 1 - E06 application service

Owner: Darren.

- Refactor the CLI retrieval path behind an injectable read-only service interface.
- Implement the existing Supabase/PostgREST adapter without exposing service credentials.
- Implement a deterministic fixture adapter with the same response and error contract.
- Search all cached records while enforcing evidence-state labels and explicit no-evidence behavior.
- Add metadata/full-text fallback for embedding-provider outages.

### Phase 2 - E10 API integration

Owner: Tim with Darren's adapter acceptance.

- Implement the versioned `POST /v1/evidence/search` route.
- Keep retrieval logic outside route handlers.
- Return adapter mode, contract version, correlation/run ID, evidence state, provenance, and typed dependency/no-evidence failures.
- Add contract, adapter-parity, timeout, and credential-boundary tests.

### Phase 3 - Website and E12 read-only integration

Owner: Tim.

- Make RAG questions and broad catalogue exploration available wherever the website has relevant context.
- Render source, date type, evidence state, synthetic status, and unsupported limitations.
- Keep explored real products visually and semantically separate from the synthetic recommendation.
- Ensure no read-only action mutates profile, extraction, recommendation, or revision state.

### Phase 4 - E11 consequential path

Owner: Jana and Tim, after the direct read path is accepted.

- Route proposals and confirmed changes through bounded typed tools.
- Require confirmation and immutable input versions.
- Invoke E07 only with the synthetic plan catalogue.
- Preserve coherent revision, replay, and undo behavior.

### Phase 5 - E08 evaluation and local-target completion

Owner: Tim with capability owners.

- Predeclare retrieval queries, expected sources, stale/no-evidence cases, and adapter parity cases.
- Meet or report the top-five and citation-coverage targets without self-grading.
- Verify that no real-product result changes synthetic ranking.
- Complete local PostgreSQL/pgvector parity and Docker Compose acceptance before claiming the approved local runtime target is met.

## Open controls

These items remain incomplete and must not be implied by recent ingestion:

- DEC-006 source permission and reuse review for every cached source.
- Product-effective dates and auditable superseded versions.
- Complete premium, eligibility, exclusion, and policy-wording coverage.
- Stable evidence identity when a policy's chunk set is replaced.
- Fixed retrieval evaluation and deterministic non-embedding fallback.
- Local PostgreSQL/pgvector adapter and Docker Compose acceptance.
- Public-use compliance, security, and operational hardening under E09.
