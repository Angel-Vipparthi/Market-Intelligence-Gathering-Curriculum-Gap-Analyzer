-- ============================================================================
-- Migration 005: Curriculum Embeddings
-- Description: pgvector embeddings for semantic search over curriculum content.
-- ============================================================================

-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS curriculum_embeddings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES curriculum_documents(id) ON DELETE CASCADE,
    embedding       vector(1536),
    chunk_index     INT DEFAULT 0,
    chunk_text      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_curriculum_embeddings_document_id
    ON curriculum_embeddings (document_id);

CREATE INDEX IF NOT EXISTS idx_curriculum_embeddings_embedding
    ON curriculum_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Cosine similarity search function
CREATE OR REPLACE FUNCTION match_curriculum(
    query_embedding vector(1536),
    match_threshold FLOAT,
    match_count INT
)
RETURNS TABLE (
    id              UUID,
    document_id     UUID,
    chunk_text      TEXT,
    similarity      FLOAT
)
LANGUAGE sql STABLE
AS $$
    SELECT
        ce.id,
        ce.document_id,
        ce.chunk_text,
        1 - (ce.embedding <=> query_embedding) AS similarity
    FROM curriculum_embeddings ce
    WHERE 1 - (ce.embedding <=> query_embedding) > match_threshold
    ORDER BY ce.embedding <=> query_embedding
    LIMIT match_count;
$$;
