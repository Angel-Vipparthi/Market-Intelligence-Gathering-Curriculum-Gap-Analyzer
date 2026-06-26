-- ============================================================================
-- Migration 003: Market Digests
-- Description: Structured digest output from the digest agent pipeline.
-- ============================================================================

CREATE TABLE IF NOT EXISTS market_digests (
    digest_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url_id          UUID REFERENCES url_registry(id),
    url             TEXT NOT NULL,
    source_title    VARCHAR(1000),
    source_type     VARCHAR(100),
    topic           VARCHAR(500),
    summary         TEXT,
    market_signal   VARCHAR(100),
    evidence_snippet TEXT,
    tools_versions  JSONB DEFAULT '[]'::jsonb,
    relevance_score FLOAT,
    relevance_reason TEXT,
    confidence      FLOAT,
    credibility_score FLOAT,
    status          VARCHAR(50) DEFAULT 'pending',
    workflow_run_id UUID,
    total_tokens    INT DEFAULT 0,
    total_cost      FLOAT DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_market_digests_status
    ON market_digests (status);

CREATE INDEX IF NOT EXISTS idx_market_digests_market_signal
    ON market_digests (market_signal);

CREATE INDEX IF NOT EXISTS idx_market_digests_created_at
    ON market_digests (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_market_digests_tools_versions
    ON market_digests USING GIN (tools_versions);
