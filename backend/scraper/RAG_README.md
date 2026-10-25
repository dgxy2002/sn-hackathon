# Insurance RAG database

This folder contains the product-information RAG implementation for the `Darren` information system described in [`PLAN.md`](../../docs/PLAN.md). Its responsibility is narrow:

- ingest insurer brochure extractions into normalized Supabase tables;
- create evidence-rich policy chunks and embeddings;
- retrieve small, typed evidence records for another system to consume;
- preserve policy, plan, benefit, rider, exclusion, source, and confidence metadata.

Downloaded brochures, extracted corpora, manifests, and embedding caches are
local-only artifacts under `backend/scraper/insurance/`. They are intentionally
excluded from Git and must not contain personal customer documents.

It does **not** calculate a user's protection gap, decide eligibility, rank suitable products, or tell a user to replace an existing policy. Those belong to the deterministic decision-support system described in the project plan.

## Application integration boundary

The offline extraction, Supabase ingestion, and retrieval CLIs remain available in this folder. The website now consumes the same evidence boundary through E10's typed `POST /v1/evidence/search` API. Supabase and local PostgreSQL are optional adapters, and deterministic fixtures preserve the contract when external services are unavailable.

The approved scope, date research, delivery sequence, and remaining controls are recorded in the [RAG and website integration decisions](../../docs/evaluation/2026-08-28-rag-website-integration-decisions.md).

- Real-product RAG is read-only across the product: it may support cited questions and broad catalogue exploration, but it does not enter E07's synthetic-plan ranking or become a recommendation.
- All 71 cached policy records may be searched. Every result must expose an evidence state such as approved, unverified, stale, or unknown; inclusion in the cache is not source approval or proof of suitability.
- Local PostgreSQL/pgvector is the accepted credential-free POC adapter. Supabase/PostgREST remains an optional adapter for the existing hosted RAG store.
- PostgreSQL, Supabase, cached-corpus, and fixture paths return the same evidence contract. Metadata and full-text retrieval remain available when embeddings or external providers are unavailable.
- OpenAI remains the offline brochure-extraction provider. Amazon Titan Text Embeddings V2 on Bedrock provides ingestion and query embeddings. OpenRouter remains the configured E04 user-document extraction provider. Amazon Bedrock is also the required E11 grounded-explanation provider; no model output may alter deterministic ranking.
- Consequential profile or extraction changes remain behind typed orchestration, confirmation, and E07 rerun controls. The accepted fixture path currently supports confirmed budget changes; other profile fields and extraction corrections remain open.

The evidence contract must distinguish three dates: `document_as_of_date` from brochure wording, `product_effective_date` from an authoritative product or policy source, and `retrieved_at` from capture or ingestion. A recent retrieval timestamp must not be presented as a product effective date.

## What is implemented

| Component | File | Purpose |
|---|---|---|
| Extraction | `extract_insurance_openai.py` | Converts brochure Markdown into strict structured JSON. |
| Shared clients | `rag_common.py` | Supabase PostgREST, Bedrock Titan embeddings, retries, and local embedding cache. |
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
AWS_REGION=us-east-1
BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
BEDROCK_EMBEDDING_DIMENSIONS=1024
```

Never expose `SUPABASE_SERVICE_ROLE_KEY` in the browser. Run ingestion and retrieval through a trusted backend or agent runtime.

Bedrock authentication uses boto3's standard credential chain: environment variables, a local AWS profile, or an IAM role. The AWS identity needs `bedrock:InvokeModel` permission for `amazon.titan-embed-text-v2:0`. The schema and scripts use that model with 1,024 normalized dimensions. Ingestion and querying must use the same model and dimension.

For an existing database created with the previous 1,536-dimensional OpenAI schema, run `migrate_embeddings_to_bedrock.sql` once in the Supabase SQL editor before re-ingesting. It clears incompatible vectors while retaining product records and chunk text.

## Prepare the extraction artifacts

This performs no database or embedding-provider calls. It marks every document quality as `good` in the individual JSON files, `documents.jsonl`, `manifest.csv`, and `extraction_report.json`, then reports the number of candidate chunks.

```powershell
& .\.venv\Scripts\python.exe .\backend\scraper\ingest_insurance_supabase.py --prepare-only
```

## Ingest everything

From the repository root:

```powershell
& .\.venv\Scripts\python.exe .\backend\scraper\ingest_insurance_supabase.py
```

The importer performs the following work one policy at a time:

1. Reads `insurance/extracted_openai/policies.jsonl` and `documents.jsonl`.
2. Enriches source records with product-page and brochure URLs from each insurer's `manifest.csv` where available.
3. Upserts the insurer, policy, and source document.
4. Replaces facts from the same document and inserts plans, benefits, plan-specific claim amounts, riders, and exclusions.
5. Generates purpose-specific chunks and creates any uncached Bedrock embeddings.
6. Replaces that policy's complete `document_chunks` set using deterministic chunk IDs.
7. Saves a checkpoint only after the policy's facts and chunks are complete.

The local embedding cache is:

```text
backend/scraper/insurance/extracted_openai/rag_embedding_cache.sqlite3
```

Each successful vector is committed to this cache immediately. It prevents unchanged chunk text from being embedded again, including vectors generated before a later network failure.

The in-progress checkpoint is:

```text
backend/scraper/insurance/extracted_openai/.ingest_checkpoint.json
```

Transient Supabase and Bedrock failures are retried with backoff. If retries are exhausted or the process is interrupted, rerun the same command. Completed policies print as `RESUME_SKIP`; an incomplete policy is safely reprocessed, reusing its cached embeddings. The checkpoint is removed after the entire selected job succeeds. Database writes are idempotent by policy slug, document hash, plan identity, and deterministic chunk ID.

To deliberately discard the checkpoint and start the selected job again:

```powershell
& .\.venv\Scripts\python.exe .\backend\scraper\ingest_insurance_supabase.py --reset-checkpoint
```

Use `--max-attempts N` to change the default of five attempts for transient remote-service failures.

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
8. **AWS and production migration:** the accepted POC runs on local PostgreSQL/pgvector. Bedrock embeddings and explanation are implemented locally through boto3, but credentialed acceptance and the RDS, S3, IAM, Secrets Manager, CloudWatch, production identity, security, privacy, and compliance controls remain open. AgentCore remains optional.

For the hackathon MVP, the evidence service supports cited real-product retrieval now. Real records remain search-only until their next eligibility gate passes. The synthetic recommendation path must continue treating missing premium, eligibility, effective-date, or exclusion data as uncertainty and return `insufficient information` rather than manufacture a fit.
