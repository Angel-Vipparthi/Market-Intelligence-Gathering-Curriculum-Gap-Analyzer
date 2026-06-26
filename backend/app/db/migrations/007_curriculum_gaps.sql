-- ============================================================================
-- Migration 007: Curriculum Gaps
-- Description: Detected gaps between market signals and current curriculum.
-- ============================================================================

CREATE TABLE IF NOT EXISTS curriculum_gaps (
    gap_id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    digest_id               UUID REFERENCES market_digests(digest_id),
    gap_type                VARCHAR(100) NOT NULL,
    market_signal           VARCHAR(500),
    curriculum_evidence     TEXT,
    gap_statement           TEXT NOT NULL,
    what_to_act             TEXT,
    why_to_act              TEXT,
    when_to_act             DATE,
    when_to_act_rationale   TEXT,
    severity                VARCHAR(50),
    severity_score          FLOAT,
    severity_factors        JSONB,
    impacted_content_area   TEXT,
    impacted_courses        TEXT[],
    impacted_sessions       TEXT[],
    impacted_projects       TEXT[],
    impacted_assessments    TEXT[],
    impacted_quizzes        TEXT[],
    impacted_tools          TEXT[],
    action_items            JSONB DEFAULT '[]'::jsonb,
    recommended_owner       VARCHAR(255),
    evidence_source         TEXT,
    confidence              FLOAT,
    critic_feedback         JSONB DEFAULT '[]'::jsonb,
    decision_status         VARCHAR(50) DEFAULT 'pending_review',
    workflow_run_id         UUID,
    total_tokens            INT DEFAULT 0,
    total_cost              FLOAT DEFAULT 0,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_curriculum_gaps_decision_status
    ON curriculum_gaps (decision_status);

CREATE INDEX IF NOT EXISTS idx_curriculum_gaps_severity
    ON curriculum_gaps (severity);

CREATE INDEX IF NOT EXISTS idx_curriculum_gaps_gap_type
    ON curriculum_gaps (gap_type);

CREATE INDEX IF NOT EXISTS idx_curriculum_gaps_when_to_act
    ON curriculum_gaps (when_to_act);

CREATE INDEX IF NOT EXISTS idx_curriculum_gaps_digest_id
    ON curriculum_gaps (digest_id);

CREATE INDEX IF NOT EXISTS idx_curriculum_gaps_created_at
    ON curriculum_gaps (created_at DESC);
