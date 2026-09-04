-- Migrate an existing Supabase vector store from 1,536-dimensional OpenAI
-- embeddings to 1,024-dimensional Amazon Titan Text Embeddings V2 vectors.
--
-- This intentionally clears existing embeddings because vectors produced by
-- different models cannot share a similarity space. Relational product data and
-- chunk text are retained. Rerun ingest_insurance_supabase.py after this script.

BEGIN;

DROP INDEX IF EXISTS idx_chunks_embedding_hnsw;
DROP FUNCTION IF EXISTS match_documents(vector, double precision, integer, jsonb);
DROP FUNCTION IF EXISTS match_documents_by_type(vector, text, double precision, integer, jsonb);

DO $$
DECLARE
  current_type TEXT;
BEGIN
  SELECT format_type(attribute.atttypid, attribute.atttypmod)
    INTO current_type
  FROM pg_attribute attribute
  JOIN pg_class relation ON relation.oid = attribute.attrelid
  JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
  WHERE namespace.nspname = current_schema()
    AND relation.relname = 'document_chunks'
    AND attribute.attname = 'embedding'
    AND NOT attribute.attisdropped;

  IF current_type IS NULL THEN
    RAISE EXCEPTION 'document_chunks.embedding does not exist; apply supabase_schema.sql first';
  ELSIF current_type = 'vector(1536)' THEN
    UPDATE document_chunks SET embedding = NULL WHERE embedding IS NOT NULL;
    EXECUTE 'ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(1024)';
  ELSIF current_type <> 'vector(1024)' THEN
    RAISE EXCEPTION 'Unsupported embedding column type: %', current_type;
  END IF;
END;
$$;

CREATE INDEX idx_chunks_embedding_hnsw ON document_chunks
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

CREATE OR REPLACE FUNCTION match_documents(
  query_embedding   VECTOR(1024),
  match_threshold   FLOAT DEFAULT 0.72,
  match_count       INT DEFAULT 8,
  filter_metadata   JSONB DEFAULT NULL
)
RETURNS TABLE (
  id UUID,
  source_type TEXT,
  source_id UUID,
  source_label TEXT,
  chunk_text TEXT,
  metadata JSONB,
  similarity FLOAT
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
    AND dc.embedding IS NOT NULL
    AND 1 - (dc.embedding <=> query_embedding) > match_threshold
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

CREATE OR REPLACE FUNCTION match_documents_by_type(
  query_embedding   VECTOR(1024),
  p_source_type     TEXT,
  match_threshold   FLOAT DEFAULT 0.72,
  match_count       INT DEFAULT 8,
  filter_metadata   JSONB DEFAULT NULL
)
RETURNS TABLE (
  id UUID,
  source_type TEXT,
  source_id UUID,
  source_label TEXT,
  chunk_text TEXT,
  metadata JSONB,
  similarity FLOAT
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
    AND dc.embedding IS NOT NULL
    AND 1 - (dc.embedding <=> query_embedding) > match_threshold
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

NOTIFY pgrst, 'reload schema';

COMMIT;
