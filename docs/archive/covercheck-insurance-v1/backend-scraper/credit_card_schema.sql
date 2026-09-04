-- Standalone installer for the simplified SingSaver credit-card scraper.
-- Safe to run when the insurance/vector portions of supabase_schema.sql have
-- not been installed yet. Existing tables are not dropped.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'card_type') THEN
    CREATE TYPE card_type AS ENUM (
      'cashback',
      'miles',
      'rewards_points',
      'hybrid',
      'student',
      'business',
      'prepaid'
    );
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'data_source') THEN
    CREATE TYPE data_source AS ENUM (
      'comparefirst',
      'moh_website',
      'cpf_board',
      'singsaver',
      'moneysmart',
      'bank_website',
      'insurer_website',
      'manual_entry'
    );
  END IF;
END
$$;

CREATE TABLE IF NOT EXISTS credit_cards (
  id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  singsaver_id                TEXT NOT NULL UNIQUE,
  name                        TEXT NOT NULL,
  bank                        TEXT NOT NULL,
  card_type                   card_type,
  network                     TEXT,
  best_for                    TEXT,
  summary                     TEXT,
  image_url                   TEXT,
  rating                      NUMERIC(3,2),
  promo_code                  TEXT,
  benefits                    JSONB NOT NULL DEFAULT '[]',

  minimum_payment_pct         NUMERIC(5,2),
  late_payment_fee_sgd        NUMERIC(8,2),
  purchase_interest_pa        NUMERIC(5,2),
  cash_advance_interest_pa    NUMERIC(5,2),
  interest_free_days          INT,

  annual_fee_sgd              NUMERIC(8,2),
  foreign_currency_fee_pct    NUMERIC(5,2),
  miles_conversion_fee_sgd    NUMERIC(8,2),
  cash_advance_fee_sgd        NUMERIC(8,2),

  monthly_spend_sgd           NUMERIC(10,2),
  minimum_annual_income_sgd   INT,
  minimum_age                 INT,

  offers                      JSONB NOT NULL DEFAULT '[]',
  highlights                  JSONB NOT NULL DEFAULT '[]',
  all_links                   JSONB NOT NULL DEFAULT '[]',
  raw_details                 JSONB NOT NULL DEFAULT '{}',
  detail_url                  TEXT NOT NULL,
  apply_url                   TEXT,

  source_type                 data_source NOT NULL DEFAULT 'singsaver',
  last_scraped_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  is_active                   BOOLEAN NOT NULL DEFAULT true,
  data_hash                   TEXT,
  created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS scrape_logs (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source_url      TEXT NOT NULL,
  source_type     data_source NOT NULL,
  linked_id       UUID,
  status          TEXT NOT NULL,
  http_status     INT,
  error_message   TEXT,
  chunks_upserted INT DEFAULT 0,
  tokens_used     INT DEFAULT 0,
  cost_usd        NUMERIC(10,6),
  scraped_at      TIMESTAMPTZ DEFAULT now(),
  next_scrape_due TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_cards_bank
  ON credit_cards (bank);
CREATE INDEX IF NOT EXISTS idx_cards_type
  ON credit_cards (card_type);
CREATE INDEX IF NOT EXISTS idx_cards_income
  ON credit_cards (minimum_annual_income_sgd);
CREATE INDEX IF NOT EXISTS idx_cards_active
  ON credit_cards (is_active);
CREATE INDEX IF NOT EXISTS idx_cards_benefits
  ON credit_cards USING GIN (benefits);
CREATE INDEX IF NOT EXISTS idx_scrape_url
  ON scrape_logs (source_url, scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_scrape_next_due
  ON scrape_logs (next_scrape_due);

ALTER TABLE credit_cards ENABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "public_read_cards" ON credit_cards;
CREATE POLICY "public_read_cards"
  ON credit_cards FOR SELECT
  USING (is_active = true);

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_cards_updated_at ON credit_cards;
CREATE TRIGGER trg_cards_updated_at
  BEFORE UPDATE ON credit_cards
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Ask PostgREST to expose newly-created tables immediately.
NOTIFY pgrst, 'reload schema';
