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

CREATE TABLE IF NOT EXISTS analysis_sessions (
	analysis_id UUID PRIMARY KEY,
	schema_version TEXT NOT NULL,
	purpose TEXT NOT NULL CHECK (
		purpose IN ('considering_offer', 'reviewing_issued_policy')
	),
	stage TEXT NOT NULL,
	decision_date DATE,
	model_consent BOOLEAN NOT NULL DEFAULT FALSE,
	model_consent_acknowledged_at TIMESTAMPTZ,
	input_hashes JSONB NOT NULL DEFAULT '[]'::jsonb,
	created_at TIMESTAMPTZ NOT NULL,
	expires_at TIMESTAMPTZ NOT NULL,
	deleted_at TIMESTAMPTZ,
	CHECK (expires_at > created_at),
	CHECK (NOT model_consent OR model_consent_acknowledged_at IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS analysis_sessions_expiry_idx
	ON analysis_sessions (expires_at)
	WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS uploaded_documents (
	document_id UUID PRIMARY KEY,
	analysis_id UUID NOT NULL REFERENCES analysis_sessions(analysis_id) ON DELETE CASCADE,
	schema_version TEXT NOT NULL,
	document_type TEXT NOT NULL,
	state TEXT NOT NULL,
	content_sha256 TEXT NOT NULL CHECK (content_sha256 ~ '^[a-f0-9]{64}$'),
	media_type TEXT NOT NULL CHECK (media_type = 'application/pdf'),
	parser_path TEXT NOT NULL CHECK (parser_path IN ('text', 'ocr', 'mixed')),
	page_count INTEGER NOT NULL CHECK (page_count > 0),
	size_bytes BIGINT NOT NULL CHECK (size_bytes > 0),
	uploaded_at TIMESTAMPTZ NOT NULL,
	transient_artifacts_deleted BOOLEAN NOT NULL DEFAULT FALSE,
	UNIQUE (analysis_id, content_sha256)
);

ALTER TABLE uploaded_documents
	ADD COLUMN IF NOT EXISTS parser_path TEXT NOT NULL DEFAULT 'text';

CREATE TABLE IF NOT EXISTS analysis_artifacts (
	artifact_id UUID PRIMARY KEY,
	analysis_id UUID NOT NULL REFERENCES analysis_sessions(analysis_id) ON DELETE CASCADE,
	document_id UUID REFERENCES uploaded_documents(document_id) ON DELETE CASCADE,
	artifact_type TEXT NOT NULL,
	schema_version TEXT NOT NULL,
	input_sha256 TEXT NOT NULL CHECK (input_sha256 ~ '^[a-f0-9]{64}$'),
	payload JSONB NOT NULL,
	created_at TIMESTAMPTZ NOT NULL,
	expires_at TIMESTAMPTZ NOT NULL,
	CHECK (expires_at > created_at)
);

CREATE INDEX IF NOT EXISTS analysis_artifacts_expiry_idx
	ON analysis_artifacts (expires_at);

CREATE TABLE IF NOT EXISTS analysis_tasks (
	task_id UUID PRIMARY KEY,
	analysis_id UUID NOT NULL REFERENCES analysis_sessions(analysis_id) ON DELETE CASCADE,
	capability TEXT NOT NULL,
	state TEXT NOT NULL,
	attempt INTEGER NOT NULL CHECK (attempt > 0),
	capsule_sha256 TEXT NOT NULL CHECK (capsule_sha256 ~ '^[a-f0-9]{64}$'),
	dependency_task_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
	artifact_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
	started_at TIMESTAMPTZ,
	finished_at TIMESTAMPTZ,
	error_code TEXT
);

CREATE TABLE IF NOT EXISTS analysis_run_events (
	event_id UUID PRIMARY KEY,
	analysis_id UUID NOT NULL REFERENCES analysis_sessions(analysis_id) ON DELETE CASCADE,
	run_id UUID NOT NULL,
	task_id UUID REFERENCES analysis_tasks(task_id) ON DELETE SET NULL,
	event_type TEXT NOT NULL,
	occurred_at TIMESTAMPTZ NOT NULL,
	metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS analysis_run_events_lookup_idx
	ON analysis_run_events (analysis_id, run_id, occurred_at);

CREATE TABLE IF NOT EXISTS analysis_revisions (
	revision_id UUID PRIMARY KEY,
	analysis_id UUID NOT NULL REFERENCES analysis_sessions(analysis_id) ON DELETE CASCADE,
	version INTEGER NOT NULL CHECK (version > 0),
	parent_version INTEGER,
	patch JSONB NOT NULL,
	affected_task_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
	created_at TIMESTAMPTZ NOT NULL,
	UNIQUE (analysis_id, version)
);

CREATE TABLE IF NOT EXISTS guidance_documents (
	document_id TEXT PRIMARY KEY,
	source_id TEXT NOT NULL REFERENCES source_registry(source_id),
	canonical_url TEXT NOT NULL UNIQUE,
	title TEXT NOT NULL,
	publisher TEXT NOT NULL,
	document_date DATE,
	content_sha256 TEXT NOT NULL CHECK (content_sha256 ~ '^[a-f0-9]{64}$'),
	crawled_at TIMESTAMPTZ NOT NULL,
	index_version TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS guidance_chunks (
	chunk_id TEXT PRIMARY KEY,
	document_id TEXT NOT NULL REFERENCES guidance_documents(document_id) ON DELETE CASCADE,
	heading_path JSONB NOT NULL DEFAULT '[]'::jsonb,
	content TEXT NOT NULL,
	chunk_sha256 TEXT NOT NULL CHECK (chunk_sha256 ~ '^[a-f0-9]{64}$'),
	embedding VECTOR(1536),
	search_document TSVECTOR GENERATED ALWAYS AS (
		to_tsvector('english', content)
	) STORED,
	UNIQUE (document_id, chunk_sha256)
);

CREATE INDEX IF NOT EXISTS guidance_chunks_search_idx
	ON guidance_chunks USING GIN (search_document);