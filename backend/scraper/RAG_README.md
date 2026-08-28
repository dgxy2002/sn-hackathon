# Insurance RAG database

This folder contains the product-information RAG implementation for the `Darren` information system described in [`PLAN.md`](../../docs/PLAN.md). Its responsibility is narrow:

- ingest insurer brochure extractions into normalized Supabase tables;
- create evidence-rich policy chunks and embeddings;
- retrieve small, typed evidence records for another system to consume;
- preserve policy, plan, benefit, rider, exclusion, source, and confidence metadata.

It does **not** calculate a user's protection gap, decide eligibility, rank suitable products, or tell a user to replace an existing policy. Those belong to the deterministic decision-support system described in the project plan.

## Application integration boundary

The offline extraction, Supabase ingestion, and retrieval CLIs remain available in this folder. The website now consumes the same evidence boundary through E10's typed `POST /v1/evidence/search` API. Local PostgreSQL is the demonstrated cached adapter, Supabase is optional, and deterministic fixtures preserve the contract when external services are unavailable.

The approved scope, date research, delivery sequence, and remaining controls are recorded in the [RAG and website integration decisions](../../docs/evaluation/2026-08-28-rag-website-integration-decisions.md).

- Real-product RAG is read-only across the product: it may support cited questions and broad catalogue exploration, but it does not enter E07's synthetic-plan ranking or become a recommendation.
- All 71 cached policy records may be searched. Every result must expose an evidence state such as approved, unverified, stale, or unknown; inclusion in the cache is not source approval or proof of suitability.
- Local PostgreSQL/pgvector is the accepted credential-free POC adapter. Supabase/PostgREST remains an optional adapter for the existing hosted RAG store.
- PostgreSQL, Supabase, cached-corpus, and fixture paths return the same evidence contract. Metadata and full-text retrieval remain available when embeddings or external providers are unavailable.
- OpenAI remains the offline brochure-extraction and embedding provider. OpenRouter remains the configured E04/E11 document and explanation provider; neither provider's output may alter deterministic ranking.
- Consequential profile or extraction changes remain behind typed orchestration, confirmation, and E07 rerun controls. The accepted fixture path currently supports confirmed budget changes; other profile fields and extraction corrections remain open.

The evidence contract must distinguish three dates: `document_as_of_date` from brochure wording, `product_effective_date` from an authoritative product or policy source, and `retrieved_at` from capture or ingestion. A recent retrieval timestamp must not be presented as a product effective date.

## What is implemented

| Component | File | Purpose |
|---|---|---|
| Extraction | `extract_insurance_openai.py` | Converts brochure Markdown into strict structured JSON. |
| Shared clients | `rag_common.py` | Supabase PostgREST, OpenAI embeddings, retries, and local embedding cache. |
| Database ingestion | `ingest_insurance_supabase.py` | Upserts normalized policy facts, builds chunks, embeds them, and replaces each policy's RAG chunk set. |
| Retrieval | `query_insurance_rag.py` | Embeds a query and returns typed cited evidence from `match_documents_by_type`. |
| Database | `supabase_schema.sql` | Relational policy tables, `document_chunks`, pgvector HNSW index, and retrieval functions. |
| Application evidence service | `../app/evidence.py` | Exposes cached-corpus, local PostgreSQL, Supabase, and fixture adapters behind one read-only contract. |
| Application API | `../app/main.py` | Publishes evidence search and eligibility-gated comparison routes through E10. |
| Local database | `../docker/postgres-init.sql` | Initializes pgvector, source registry, scraper runtime, and cached evidence storage for Docker Compose. |

The current extraction contains 79 brochure documents and 87 extracted policy rows. Exact duplicate product/document pairs collapse to 71 unique policy slugs during ingestion. All document-quality labels are deliberately normalized to `good`, as requested. Extraction confidence, review notes, and evidence warnings remain available independently; changing the quality label does not manufacture missing facts.

## Supabase CLI prerequisites

These credentials are required only for the optional Supabase ingestion and retrieval CLIs. The default local application path uses Docker Compose and does not require them.

1. Apply `supabase_schema.sql` in the Supabase SQL editor. This has already been done for the current project.
2. Use the repository virtual environment with Python 3.11 or newer.
3. Ensure `backend/.env` contains:

```dotenv
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_SERVICE_ROLE_KEY=YOUR_SERVICE_ROLE_KEY
OPENAI_KEY=YOUR_OPENAI_API_KEY
```

Never expose `SUPABASE_SERVICE_ROLE_KEY` in the browser. Run ingestion and retrieval through a trusted backend or agent runtime.

The schema uses `VECTOR(1536)`. The scripts therefore default to `text-embedding-3-small` with 1,536 dimensions. The same embedding model and dimension must be used for ingestion and querying.

## Prepare the extraction artifacts

This performs no database or OpenAI calls. It marks every document quality as `good` in the individual JSON files, `documents.jsonl`, `manifest.csv`, and `extraction_report.json`, then reports the number of candidate chunks.

```powershell
& .\.venv\Scripts\python.exe .\backend\scraper\ingest_insurance_supabase.py --prepare-only
```

## Ingest everything

From the repository root:

```powershell
& .\.venv\Scripts\python.exe .\backend\scraper\ingest_insurance_supabase.py
```

The importer performs the following work:

1. Reads `insurance/extracted_openai/policies.jsonl` and `documents.jsonl`.
2. Enriches source records with product-page and brochure URLs from each insurer's `manifest.csv` where available.
3. Upserts insurers and policies.
4. Creates or updates policy documents using the content hash.
5. Replaces facts from the same document and inserts plans, benefits, plan-specific claim amounts, riders, and exclusions.
6. Generates purpose-specific chunks.
7. Creates and locally caches embeddings.
8. Replaces the complete `document_chunks` set for every touched policy.

The local embedding cache is:

```text
backend/scraper/insurance/extracted_openai/rag_embedding_cache.sqlite3
```

It prevents unchanged chunk text from being embedded again when ingestion is rerun. Database operations are idempotent by policy slug, document hash, plan identity, and policy-level chunk replacement. If a run is interrupted, rerun the same command.

Useful scoped commands:

```powershell
# Only one product or source-path match
& .\.venv\Scripts\python.exe .\backend\scraper\ingest_insurance_supabase.py --match "MultiCover CI"

# Load relational policy tables but do not build RAG chunks
& .\.venv\Scripts\python.exe .\backend\scraper\ingest_insurance_supabase.py --structured-only

# Build chunks with NULL embeddings; useful only when embeddings will be backfilled separately
& .\.venv\Scripts\python.exe .\backend\scraper\ingest_insurance_supabase.py --skip-embeddings
```

Do not use `--skip-embeddings` for a working vector search because NULL vectors cannot match a query.

## Chunk design

The importer creates separate chunks for:

- policy overview;
- eligibility and policy terms;
- each plan or tier;
- each plan-specific benefit or claim amount;
- each policy-level benefit;
- each rider;
- each explicit exclusion.

Every chunk repeats the insurer and policy name so it remains understandable when retrieved by itself. Evidence quotes and Markdown line locations are included in the chunk text. Flat metadata supports exact pgvector pre-filters:

```json
{
  "type": "policy",
  "policy_id": "uuid",
  "insurer": "FWD",
  "policy_name": "MultiCover CI",
  "category": "critical_illness",
  "policy_type": "multipay_critical_illness",
  "section_kind": "plan_benefit_amount",
  "plan_name": "Plan 1",
  "benefit_name": "Early-stage critical illness",
  "document_quality": "good",
  "extraction_confidence": "high",
  "product_page": "https://...",
  "brochure_url": "https://...pdf",
  "retrieved_at": "2026-08-26T...Z",
  "synthetic": false
}
```

## Querying the RAG store

Basic semantic retrieval:

```powershell
& .\.venv\Scripts\python.exe .\backend\scraper\query_insurance_rag.py `
  "critical illness plans with repeat claims and an early-stage payout"
```

Apply exact metadata filters before vector similarity:

```powershell
& .\.venv\Scripts\python.exe .\backend\scraper\query_insurance_rag.py `
  "monthly disability income replacement" `
  --filter category=disability `
  --filter section_kind=benefit `
  --count 10
```

Retrieve evidence and hydrate the complete normalized candidate policies:

```powershell
& .\.venv\Scripts\python.exe .\backend\scraper\query_insurance_rag.py `
  "personal accident medical reimbursement for sports injuries" `
  --filter category=personal_accident `
  --hydrate
```

The default result is deliberately small and typed:

```json
{
  "query": "...",
  "metadata_filter": {"category": "critical_illness"},
  "match_count": 5,
  "evidence": [
    {
      "evidence_id": "document_chunks.id",
      "policy_id": "policies.id",
      "provider": "FWD",
      "product": "MultiCover CI",
      "field": "benefit",
      "value": "retrieved evidence text and quoted source lines",
      "source_url": "https://...pdf",
      "retrieved_at": "2026-08-26T...Z",
      "synthetic": false,
      "extraction_confidence": "high",
      "similarity": 0.81
    }
  ]
}
```

Use each `evidence_id` in downstream recommendation results so every product claim can be traced back to the retrieved chunk.

## Using RAG with a user profile

Do not embed the entire user profile and ask the nearest-neighbour search to choose a policy. Convert the profile into explicit needs and filters first.

```text
Versioned user profile
        |
        v
Deterministic gap calculation
        |
        +--> hard product/category/eligibility constraints
        |
        v
One retrieval query per unmet need
        |
        v
Candidate policy IDs + typed evidence
        |
        v
Hydrate relational policy/plan/benefit records
        |
        v
Deterministic eligibility and weighted-fit ranking
        |
        v
LLM explanation using only calculated results and evidence IDs
```

For example, a profile may produce these retrieval inputs:

```json
{
  "need": "critical illness income replacement with early-stage cover",
  "required_category": "critical_illness",
  "target_coverage_sgd": 180000,
  "coverage_horizon_years": 20,
  "premium_budget_monthly_sgd": 150,
  "existing_coverage_sgd": 50000
}
```

Use vector retrieval for descriptive needs and terminology. Use SQL and deterministic code for exact numbers, eligibility, affordability, coverage gaps, and ranking. An absent extracted value must remain unknown; it must not be interpreted as zero, unrestricted, eligible, or affordable.

Recommended application flow:

1. The personalization system supplies a versioned profile and unmet needs.
2. The information system retrieves top evidence for each need, normally with a category filter.
3. Group results by `policy_id`; do not count multiple chunks from one policy as multiple candidates.
4. Hydrate the normalized policy rows.
5. The decision-support system removes hard-rule violations and calculates fit scores.
6. The explanation model receives only the user-approved profile fields, calculated result, trade-offs, and retrieved evidence.
7. Return evidence IDs and source URLs alongside every product claim.

## What is still lacking

The integrated evidence service is usable, but the following evidence, evaluation, and production controls remain incomplete:

1. **As-of, effective, and version dates:** none of the 87 structured policy rows currently stores an explicit effective date or product version. Seventy-two of the 79 cached brochure files contain a recognizable `information correct/accurate as at` statement, but extraction does not yet retain it. Extract those statements as `document_as_of_date`, research official sources for the seven undated Great Eastern files, preserve `unknown` where no authoritative date is available, and never substitute the 26-27 August 2026 capture date for product effectiveness.
2. **Six missing FWD source URLs:** the FWD extraction folder has no scraper `manifest.csv`, so Life PA, Personal Accident, MultiCover CI, Recover First, Future First, and Life Protection retain local evidence paths but no product-page or brochure URL. Restore a FWD manifest and rerun ingestion to populate them.
3. **Complete premium data:** brochures rarely contain a quote for a specific age, sex, smoking status, sum assured, and term. Affordability cannot be enforced until a premium source or quote workflow populates `policy_premiums`.
4. **Complete contractual exclusions:** brochure extraction contains only exclusions explicitly printed in the brochure. Policy wording would be a separate, higher-authority source.
5. **Comparison-eligible real-product subset:** the API and rejection gates are implemented, but no real product has approved reuse, complete comparison evidence, and the other Phase 3B gates required to enter the comparison projection.
6. **Durable decision-support persistence:** versioned profile, recommendation, conversation, proposal, revision, replay, and undo services exist for synthetic current-session use. Durable SQL repositories, session expiry cleanup, and real-customer data controls remain outside the accepted POC path.
7. **Retrieval evaluation set:** the plan requires expected-source-in-top-5 performance of at least 90%. A labelled query set and evaluation script have not yet been created.
8. **AWS and production migration:** the accepted POC runs on local PostgreSQL/pgvector. RDS, S3, Secrets Manager, CloudWatch, production identity, security, privacy, and compliance controls remain deferred; Bedrock and AgentCore remain optional future adapters.

For the hackathon MVP, the evidence service supports cited real-product retrieval now. Real records remain search-only until their next eligibility gate passes. The synthetic recommendation path must continue treating missing premium, eligibility, effective-date, or exclusion data as uncertainty and return `insufficient information` rather than manufacture a fit.
