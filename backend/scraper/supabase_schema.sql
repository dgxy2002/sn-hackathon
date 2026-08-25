-- =============================================================================
-- FA AGENT — SUPABASE SCHEMA
-- Insurance Companies, Policies, Coverage + Credit Cards + pgvector RAG
-- =============================================================================
-- Run order:
--   1. Extensions
--   2. Enums
--   3. Insurance tables
--   4. Credit card tables
--   5. Vector / RAG tables
--   6. Indexes
--   7. RLS policies
--   8. Helper functions
-- =============================================================================


-- =============================================================================
-- 1. EXTENSIONS
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";          -- pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS "pg_trgm";         -- trigram search on text fields


-- =============================================================================
-- 2. ENUMS
-- =============================================================================

CREATE TYPE policy_category AS ENUM (
  'life',
  'health',
  'critical_illness',
  'personal_accident',
  'travel',
  'motor',
  'home',
  'endowment',
  'investment_linked',
  'disability'
);

CREATE TYPE policy_type AS ENUM (
  'term_life',
  'whole_life',
  'endowment',
  'investment_linked',
  'integrated_shield_plan',   -- ISP / IP Shield
  'direct_purchase_insurance', -- DPI (MAS-regulated, no commission)
  'critical_illness',
  'early_critical_illness',
  'multipay_critical_illness',
  'personal_accident',
  'travel',
  'motor',
  'home_contents',
  'maid',
  'disability_income'
);

CREATE TYPE ward_class AS ENUM (
  'C', 'B2', 'B1', 'A', 'private'
);

CREATE TYPE coverage_type AS ENUM (
  'as_charged',       -- full reimbursement up to limit
  'claims_based',     -- premium adjusts based on past claims
  'fixed_benefit',    -- fixed payout regardless of actual cost
  'percentage'        -- percentage of actual bill
);

CREATE TYPE card_type AS ENUM (
  'cashback',
  'miles',
  'rewards_points',
  'hybrid',           -- mix of cashback + miles
  'student',
  'business',
  'prepaid'
);

CREATE TYPE data_source AS ENUM (
  'comparefirst',     -- MAS/LIA portal
  'moh_website',      -- MOH ISP comparison tables
  'cpf_board',
  'singsaver',
  'moneysmart',
  'bank_website',
  'insurer_website',
  'manual_entry'
);


-- =============================================================================
-- 3. INSURANCE TABLES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 3a. Insurers
-- -----------------------------------------------------------------------------
CREATE TABLE insurers (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name            TEXT NOT NULL,                -- 'AIA Singapore Pte. Ltd.'
  short_name      TEXT NOT NULL UNIQUE,         -- 'AIA'
  logo_url        TEXT,
  website_url     TEXT,
  mas_license_no  TEXT,                         -- MAS Financial Institutions Directory
  comparefirst_id TEXT,                         -- ID used on comparefirst.sg if available
  is_active       BOOLEAN DEFAULT true,
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);

INSERT INTO insurers (name, short_name, website_url) VALUES
  ('AIA Singapore Pte. Ltd.',                    'AIA',      'https://www.aia.com.sg'),
  ('Great Eastern Life Assurance Co. Ltd.',      'GE',       'https://www.greateasternlife.com'),
  ('Prudential Assurance Company Singapore',     'PRU',      'https://www.prudential.com.sg'),
  ('Income Insurance Limited',                   'Income',   'https://www.income.com.sg'),
  ('Singlife with Aviva',                        'Singlife', 'https://singlife.com'),
  ('HSBC Life (Singapore) Pte. Ltd.',            'HSBC Life','https://www.hsbc.com.sg'),
  ('Manulife (Singapore) Pte. Ltd.',             'Manulife', 'https://www.manulife.com.sg'),
  ('FWD Singapore Pte. Ltd.',                    'FWD',      'https://www.fwd.com.sg'),
  ('Tokio Marine Life Insurance Singapore Ltd.', 'Tokio',    'https://www.tokiomarine.com/sg');


-- -----------------------------------------------------------------------------
-- 3b. Policies  (one row = one named product)
-- -----------------------------------------------------------------------------
CREATE TABLE policies (
  id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  insurer_id              UUID NOT NULL REFERENCES insurers(id) ON DELETE CASCADE,

  -- Identity
  name                    TEXT NOT NULL,        -- 'AIA HealthShield Gold Max A'
  short_code              TEXT,                 -- 'HSGMA' (internal reference)
  category                policy_category NOT NULL,
  type                    policy_type NOT NULL,
  plan_tier               TEXT,                 -- 'Premier', 'Plus', 'Standard', 'A', 'B', etc.

  -- Availability
  is_active               BOOLEAN DEFAULT true,
  available_to_new        BOOLEAN DEFAULT true, -- false = closed to new applicants

  -- Entry constraints
  min_entry_age           INT,                  -- minimum age to buy (years)
  max_entry_age           INT,                  -- maximum age to buy
  max_coverage_age        INT,                  -- age coverage ends (e.g. 99, 100)

  -- Coverage limits (top-level; granular detail in policy_coverage)
  annual_limit            NUMERIC(14,2),        -- SGD
  lifetime_limit          NUMERIC(14,2),        -- SGD, null = unlimited
  policy_year_limit       NUMERIC(14,2),        -- SGD

  -- For term life / CI products
  term_years              INT,                  -- null = whole-of-life or renewable annually
  renewable               BOOLEAN,

  -- For Integrated Shield Plans
  ward_class              ward_class,           -- highest ward class covered
  is_dpi                  BOOLEAN DEFAULT false,-- Direct Purchase Insurance (no commission)

  -- MediSave (Singapore-specific)
  medisave_payable        BOOLEAN DEFAULT false,
  medisave_withdrawal_limit_sgd INT,            -- annual MediSave withdrawal cap (SGD)

  -- Flexible extra fields (anything not covered above)
  extra_fields            JSONB DEFAULT '{}',
  -- e.g. {"ci_conditions_count": 112, "tpd_included": true, "waiver_of_premium": true}

  -- Data provenance
  source_url              TEXT,
  source_type             data_source,
  last_scraped_at         TIMESTAMPTZ,
  is_verified             BOOLEAN DEFAULT false,-- human-reviewed flag
  data_hash               TEXT,                 -- MD5 of scraped content; detect stale rows

  created_at              TIMESTAMPTZ DEFAULT now(),
  updated_at              TIMESTAMPTZ DEFAULT now()
);


-- -----------------------------------------------------------------------------
-- 3c. Policy premiums  (age-banded pricing table)
-- Separate rows for each age / gender / citizenship band.
-- -----------------------------------------------------------------------------
CREATE TABLE policy_premiums (
  id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  policy_id               UUID NOT NULL REFERENCES policies(id) ON DELETE CASCADE,

  -- Band keys
  age_next_birthday       INT NOT NULL,         -- ANB: standard unit in SG insurance
  gender                  CHAR(1),              -- 'M' | 'F' | null = unisex
  smoker_status           TEXT,                 -- 'smoker' | 'non_smoker' | null
  citizenship             TEXT,                 -- 'SC' | 'PR' | 'foreigner' | null

  -- Premium breakdown (all SGD per year)
  premium_total           NUMERIC(10,2) NOT NULL,
  premium_mshl_component  NUMERIC(10,2),        -- ISP: MediShield Life portion
  premium_private_component NUMERIC(10,2),      -- ISP: private insurer top-up portion

  -- For life products
  sum_assured             NUMERIC(14,2),        -- SGD

  notes                   TEXT,

  created_at              TIMESTAMPTZ DEFAULT now(),
  updated_at              TIMESTAMPTZ DEFAULT now(),

  UNIQUE (policy_id, age_next_birthday, gender, smoker_status, citizenship)
);


-- -----------------------------------------------------------------------------
-- 3d. Policy coverage  (per-benefit breakdown)
-- One row per named benefit within a policy.
-- -----------------------------------------------------------------------------
CREATE TABLE policy_coverage (
  id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  policy_id               UUID NOT NULL REFERENCES policies(id) ON DELETE CASCADE,

  benefit_name            TEXT NOT NULL,
  -- e.g. 'Inpatient & Day Surgery', 'Intensive Care Unit', 'Organ Transplant',
  --      'Cancer Drug Treatment', 'Pregnancy Complications'

  benefit_category        TEXT,
  -- 'inpatient', 'outpatient', 'surgical', 'cancer', 'mental_health', etc.

  coverage_type           coverage_type,
  limit_amount            NUMERIC(14,2),        -- SGD; null if as_charged with no cap
  limit_type              TEXT,
  -- 'per_day' | 'per_admission' | 'per_year' | 'lifetime' | 'per_disability'

  deductible_sgd          NUMERIC(10,2),        -- excess the insured pays first
  co_insurance_pct        NUMERIC(5,2),         -- % of bill after deductible (e.g. 10.00)
  co_insurance_cap_sgd    NUMERIC(10,2),        -- cap on co-insurance (stop-loss)

  covered                 BOOLEAN DEFAULT true, -- false = explicitly excluded here
  notes                   TEXT,

  created_at              TIMESTAMPTZ DEFAULT now()
);


-- -----------------------------------------------------------------------------
-- 3e. Policy exclusions
-- -----------------------------------------------------------------------------
CREATE TABLE policy_exclusions (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  policy_id   UUID NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
  exclusion   TEXT NOT NULL,
  category    TEXT,
  -- 'pre_existing_condition' | 'cosmetic' | 'dental' | 'pregnancy' |
  -- 'war_terrorism' | 'self_inflicted' | 'congenital'
  created_at  TIMESTAMPTZ DEFAULT now()
);


-- -----------------------------------------------------------------------------
-- 3f. Policy riders  (optional add-ons)
-- -----------------------------------------------------------------------------
CREATE TABLE policy_riders (
  id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  policy_id           UUID NOT NULL REFERENCES policies(id) ON DELETE CASCADE,

  name                TEXT NOT NULL,
  description         TEXT,
  rider_type          TEXT,
  -- 'copayment_waiver' | 'critical_illness' | 'tpd' |
  -- 'waiver_of_premium' | 'early_ci' | 'deductible_waiver'

  is_cash_only        BOOLEAN,      -- true = cannot pay with MediSave
  indicative_premium  NUMERIC(10,2),-- approx annual premium (age-dependent; store as guide)
  notes               TEXT,

  created_at          TIMESTAMPTZ DEFAULT now()
);


-- =============================================================================
-- 4. CREDIT CARDS
-- =============================================================================

-- One row = one SingSaver card product. Variable reward fields are stored in
-- benefits JSONB because cashback, miles, points and cap labels differ by card.
CREATE TABLE credit_cards (
  id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- Identity and display
  singsaver_id                TEXT NOT NULL UNIQUE,
  name                        TEXT NOT NULL,
  bank                        TEXT NOT NULL,
  card_type                   card_type,
  network                     TEXT,             -- Visa | Mastercard | Amex | UnionPay
  best_for                    TEXT,             -- e.g. 'Best for yuu shoppers'
  summary                     TEXT,
  image_url                   TEXT,
  rating                      NUMERIC(3,2),      -- e.g. 3.90 out of 5
  promo_code                  TEXT,

  -- Display-ready reward fields from the product card.
  -- Example:
  -- [{"label":"Cashback (Local)","value":"2.5 %","kind":"cashback",
  --   "category":"local","amount":2.5,"unit":"%"}]
  benefits                    JSONB NOT NULL DEFAULT '[]',

  -- Repayment details
  minimum_payment_pct         NUMERIC(5,2),
  late_payment_fee_sgd        NUMERIC(8,2),
  purchase_interest_pa        NUMERIC(5,2),
  cash_advance_interest_pa    NUMERIC(5,2),
  interest_free_days          INT,

  -- Fees
  annual_fee_sgd              NUMERIC(8,2),
  foreign_currency_fee_pct    NUMERIC(5,2),
  miles_conversion_fee_sgd    NUMERIC(8,2),
  cash_advance_fee_sgd        NUMERIC(8,2),

  -- Eligibility
  monthly_spend_sgd           NUMERIC(10,2),
  minimum_annual_income_sgd   INT,
  minimum_age                 INT,

  -- Offers, editorial content, links and lossless source capture
  offers                      JSONB NOT NULL DEFAULT '[]',
  highlights                  JSONB NOT NULL DEFAULT '[]',
  all_links                   JSONB NOT NULL DEFAULT '[]',
  raw_details                 JSONB NOT NULL DEFAULT '{}',

  detail_url                  TEXT NOT NULL,
  apply_url                   TEXT,

  -- Provenance
  source_type                 data_source NOT NULL DEFAULT 'singsaver',
  last_scraped_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  is_active                   BOOLEAN NOT NULL DEFAULT true,
  data_hash                   TEXT,

  created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- =============================================================================
-- 5. VECTOR / RAG TABLES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 5a. Document chunks  — the RAG knowledge base
-- Each row = one text chunk + its embedding vector.
-- Chunks come from:
--   • Scraped policy pages / PDFs (MOH ISP tables, comparefirst, insurer sites)
--   • Scraped card pages (SingSaver, bank websites)
--   • Financial literacy guides, FAQs
-- -----------------------------------------------------------------------------
CREATE TABLE document_chunks (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- ── Source reference ─────────────────────────────────────────────────────
  source_type     TEXT NOT NULL,
  -- 'policy' | 'card' | 'insurer_faq' | 'bank_faq' | 'guide' | 'regulatory'
  source_id       UUID,
  -- FK to policies.id OR credit_cards.id; null for generic guides
  source_url      TEXT,
  source_label    TEXT,            -- human-readable e.g. 'AIA HealthShield Gold Max A — MOH PDF'

  -- ── Chunk content ─────────────────────────────────────────────────────────
  chunk_text      TEXT NOT NULL,   -- raw text fed to the embedding model
  chunk_index     INT,             -- position within the source document (0-based)
  section_title   TEXT,            -- nearest heading above this chunk

  -- ── Metadata for filtered retrieval (pre-filter before vector search) ─────
  -- Keep metadata flat and queryable; mirror the most-searched dimensions.
  metadata        JSONB DEFAULT '{}',
  -- For policy chunks:
  --   {"type": "policy", "insurer": "AIA", "policy_type": "integrated_shield_plan",
  --    "ward_class": "A", "medisave_payable": true, "policy_id": "...uuid..."}
  -- For card chunks:
  --   {"type": "card", "bank": "DBS", "card_type": "miles",
  --    "min_income": 30000, "has_lounge": true, "card_id": "...uuid..."}

  -- ── Embedding vector ──────────────────────────────────────────────────────
  -- 1536 dims  → OpenAI text-embedding-3-small / ada-002
  -- 1024 dims  → Voyage AI (Anthropic's recommended partner), Cohere embed-v3
  -- 3072 dims  → OpenAI text-embedding-3-large
  -- Change the dimension to match whichever model you deploy.
  embedding       VECTOR(1536),

  -- ── Data quality ──────────────────────────────────────────────────────────
  token_count     INT,             -- number of tokens in chunk_text (for cost tracking)
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);


-- -----------------------------------------------------------------------------
-- 5b. Scrape / ingest log  — track freshness and cost
-- One row per scrape run per source URL.
-- -----------------------------------------------------------------------------
CREATE TABLE scrape_logs (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source_url      TEXT NOT NULL,
  source_type     data_source NOT NULL,
  linked_id       UUID,            -- policy_id or card_id updated by this run

  status          TEXT NOT NULL,   -- 'success' | 'failed' | 'unchanged' | 'partial'
  http_status     INT,
  error_message   TEXT,

  chunks_upserted INT DEFAULT 0,
  tokens_used     INT DEFAULT 0,   -- OCR / embedding tokens consumed
  cost_usd        NUMERIC(10,6),   -- estimated API cost

  scraped_at      TIMESTAMPTZ DEFAULT now(),
  next_scrape_due TIMESTAMPTZ      -- scheduler hint (e.g. +7 days)
);


-- =============================================================================
-- 6. INDEXES
-- =============================================================================

-- ── Insurance ────────────────────────────────────────────────────────────────
CREATE INDEX idx_policies_insurer     ON policies (insurer_id);
CREATE INDEX idx_policies_type        ON policies (type);
CREATE INDEX idx_policies_category    ON policies (category);
CREATE INDEX idx_policies_ward_class  ON policies (ward_class);
CREATE INDEX idx_policies_active      ON policies (is_active, available_to_new);

CREATE INDEX idx_premiums_policy_age  ON policy_premiums (policy_id, age_next_birthday);
CREATE INDEX idx_coverage_policy      ON policy_coverage (policy_id);
CREATE INDEX idx_exclusions_policy    ON policy_exclusions (policy_id);
CREATE INDEX idx_riders_policy        ON policy_riders (policy_id);

-- ── Credit cards ─────────────────────────────────────────────────────────────
CREATE INDEX idx_cards_bank           ON credit_cards (bank);
CREATE INDEX idx_cards_type           ON credit_cards (card_type);
CREATE INDEX idx_cards_income         ON credit_cards (minimum_annual_income_sgd);
CREATE INDEX idx_cards_active         ON credit_cards (is_active);
CREATE INDEX idx_cards_benefits       ON credit_cards USING GIN (benefits);

-- ── Vector store ─────────────────────────────────────────────────────────────
-- HNSW index: fast approximate nearest-neighbour search.
-- m=16, ef_construction=64 are good defaults; tune up if recall < 95%.
CREATE INDEX idx_chunks_embedding_hnsw ON document_chunks
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- GIN index for JSONB metadata filtering (pre-filter before vector search)
CREATE INDEX idx_chunks_metadata      ON document_chunks USING GIN (metadata);
CREATE INDEX idx_chunks_source_type   ON document_chunks (source_type);
CREATE INDEX idx_chunks_source_id     ON document_chunks (source_id);

-- Trigram indexes for fuzzy text search on names
CREATE INDEX idx_policies_name_trgm   ON policies      USING GIN (name gin_trgm_ops);
CREATE INDEX idx_cards_name_trgm      ON credit_cards  USING GIN (name gin_trgm_ops);

-- Scrape log indexes
CREATE INDEX idx_scrape_url           ON scrape_logs (source_url, scraped_at DESC);
CREATE INDEX idx_scrape_next_due      ON scrape_logs (next_scrape_due);


-- =============================================================================
-- 7. ROW LEVEL SECURITY
-- =============================================================================
-- Enable RLS on every table. The FA agent's backend service role bypasses RLS.
-- If you expose Supabase client directly, these policies protect the data.

ALTER TABLE insurers            ENABLE ROW LEVEL SECURITY;
ALTER TABLE policies            ENABLE ROW LEVEL SECURITY;
ALTER TABLE policy_premiums     ENABLE ROW LEVEL SECURITY;
ALTER TABLE policy_coverage     ENABLE ROW LEVEL SECURITY;
ALTER TABLE policy_exclusions   ENABLE ROW LEVEL SECURITY;
ALTER TABLE policy_riders       ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_cards        ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks     ENABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_logs         ENABLE ROW LEVEL SECURITY;

-- Public read access for reference / product data
CREATE POLICY "public_read_insurers"    ON insurers        FOR SELECT USING (true);
CREATE POLICY "public_read_policies"    ON policies        FOR SELECT USING (is_active = true);
CREATE POLICY "public_read_premiums"    ON policy_premiums FOR SELECT USING (true);
CREATE POLICY "public_read_coverage"    ON policy_coverage FOR SELECT USING (true);
CREATE POLICY "public_read_exclusions"  ON policy_exclusions FOR SELECT USING (true);
CREATE POLICY "public_read_riders"      ON policy_riders   FOR SELECT USING (true);
CREATE POLICY "public_read_cards"       ON credit_cards    FOR SELECT USING (is_active = true);
CREATE POLICY "public_read_chunks"      ON document_chunks FOR SELECT USING (true);

-- Scrape logs: only service role (no public policy = blocked for anon)


-- =============================================================================
-- 8. HELPER FUNCTIONS
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 8a. Vector similarity search with optional metadata pre-filter
-- Call from your backend: SELECT * FROM match_documents(embedding, 0.75, 8,
--   '{"policy_type": "integrated_shield_plan", "ward_class": "A"}');
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding   VECTOR(1536),
  match_threshold   FLOAT    DEFAULT 0.72,
  match_count       INT      DEFAULT 8,
  filter_metadata   JSONB    DEFAULT NULL    -- pass NULL to skip metadata filter
)
RETURNS TABLE (
  id            UUID,
  source_type   TEXT,
  source_id     UUID,
  source_label  TEXT,
  chunk_text    TEXT,
  metadata      JSONB,
  similarity    FLOAT
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.id,
    dc.source_type,
    dc.source_id,
    dc.source_label,
    dc.chunk_text,
    dc.metadata,
    1 - (dc.embedding <=> query_embedding) AS similarity
  FROM document_chunks dc
  WHERE
    (filter_metadata IS NULL OR dc.metadata @> filter_metadata)
    AND 1 - (dc.embedding <=> query_embedding) > match_threshold
  ORDER BY dc.embedding <=> query_embedding   -- ascending distance = descending similarity
  LIMIT match_count;
END;
$$;


-- -----------------------------------------------------------------------------
-- 8b. Match documents filtered by source_type
-- Convenience wrapper for when you only want policy chunks or only card chunks.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION match_documents_by_type(
  query_embedding   VECTOR(1536),
  p_source_type     TEXT,                    -- 'policy' | 'card' | 'guide'
  match_threshold   FLOAT    DEFAULT 0.72,
  match_count       INT      DEFAULT 8,
  filter_metadata   JSONB    DEFAULT NULL
)
RETURNS TABLE (
  id            UUID,
  source_type   TEXT,
  source_id     UUID,
  source_label  TEXT,
  chunk_text    TEXT,
  metadata      JSONB,
  similarity    FLOAT
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.id,
    dc.source_type,
    dc.source_id,
    dc.source_label,
    dc.chunk_text,
    dc.metadata,
    1 - (dc.embedding <=> query_embedding) AS similarity
  FROM document_chunks dc
  WHERE
    dc.source_type = p_source_type
    AND (filter_metadata IS NULL OR dc.metadata @> filter_metadata)
    AND 1 - (dc.embedding <=> query_embedding) > match_threshold
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;


-- -----------------------------------------------------------------------------
-- 8c. auto-update updated_at on any row change
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_insurers_updated_at
  BEFORE UPDATE ON insurers
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_policies_updated_at
  BEFORE UPDATE ON policies
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_premiums_updated_at
  BEFORE UPDATE ON policy_premiums
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_cards_updated_at
  BEFORE UPDATE ON credit_cards
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_chunks_updated_at
  BEFORE UPDATE ON document_chunks
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- =============================================================================
-- SCHEMA COMPLETE
-- =============================================================================
-- Table map:
--
-- INSURANCE
--   insurers
--     └── policies
--           ├── policy_premiums     (age-banded pricing)
--           ├── policy_coverage     (per-benefit limits, deductibles, co-insurance)
--           ├── policy_exclusions
--           └── policy_riders
--
-- CREDIT CARDS
--   credit_cards                    (one row per card; JSONB for variable details)
--
-- VECTOR / RAG
--   document_chunks                 (text + VECTOR(1536) + JSONB metadata)
--   scrape_logs                     (freshness & cost tracking)
--
-- FUNCTIONS
--   match_documents(embedding, threshold, count, metadata_filter)
--   match_documents_by_type(embedding, source_type, threshold, count, metadata_filter)
-- =============================================================================
