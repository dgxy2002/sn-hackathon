CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS source_registry (
	source_id TEXT PRIMARY KEY,
	source_url TEXT NOT NULL,
	approval_state TEXT NOT NULL CHECK (
		approval_state IN ('approved', 'unverified', 'restricted', 'rejected')
	),
	owner_name TEXT,
	review_date DATE,
	next_scrape_due TIMESTAMPTZ,
	consecutive_failures INTEGER NOT NULL DEFAULT 0,
	last_success_at TIMESTAMPTZ,
	last_failure_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS scraper_runtime (
	worker_name TEXT PRIMARY KEY,
	state TEXT NOT NULL CHECK (
		state IN ('running', 'degraded', 'stale', 'failed', 'stopped')
	),
	lease_owner TEXT,
	last_heartbeat TIMESTAMPTZ NOT NULL,
	details JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS evidence_records (
	evidence_id TEXT PRIMARY KEY,
	policy_id TEXT NOT NULL,
	provider TEXT NOT NULL,
	product TEXT NOT NULL,
	category TEXT NOT NULL,
	field_name TEXT NOT NULL,
	payload JSONB NOT NULL,
	search_document TSVECTOR GENERATED ALWAYS AS (
		to_tsvector(
			'simple',
			provider || ' ' || product || ' ' || category || ' ' || field_name ||
			' ' || coalesce(payload ->> 'section_title', '') ||
			' ' || coalesce(payload ->> 'value', '')
		)
	) STORED
);

CREATE INDEX IF NOT EXISTS evidence_records_search_idx
	ON evidence_records USING GIN (search_document);