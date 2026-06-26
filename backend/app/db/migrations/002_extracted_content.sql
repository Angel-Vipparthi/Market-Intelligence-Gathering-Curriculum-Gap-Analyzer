-- ============================================================================
-- Migration 002: Extracted Content
-- Description: Stores raw scraped content from registered URLs.
-- ============================================================================

CREATE TABLE IF NOT EXISTS extracted_content (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url_id              UUID REFERENCES url_registry(id),
    url                 TEXT NOT NULL,
    raw_content         TEXT,
    content_length      INT,
    extraction_method   VARCHAR(50),
    extraction_status   VARCHAR(50) NOT NULL,
    error_message       TEXT,
    metadata            JSONB,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_extracted_content_url_id
    ON extracted_content (url_id);

CREATE INDEX IF NOT EXISTS idx_extracted_content_extraction_status
    ON extracted_content (extraction_status);
