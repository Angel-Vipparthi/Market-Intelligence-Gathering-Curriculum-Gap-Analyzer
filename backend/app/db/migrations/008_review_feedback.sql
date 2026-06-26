-- ============================================================================
-- Migration 008: Review Feedback
-- Description: Human review decisions and feedback on digests and gaps.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- Review Decisions
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS review_decisions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type     VARCHAR(50) NOT NULL
                        CHECK (entity_type IN ('digest', 'gap')),
    entity_id       UUID NOT NULL,
    reviewer_id     VARCHAR(255) NOT NULL,
    decision        VARCHAR(50) NOT NULL
                        CHECK (decision IN ('approved', 'rejected', 'needs_review')),
    previous_status VARCHAR(50),
    comments        TEXT,
    edited_fields   JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_review_decisions_entity
    ON review_decisions (entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_review_decisions_reviewer_id
    ON review_decisions (reviewer_id);

CREATE INDEX IF NOT EXISTS idx_review_decisions_decision
    ON review_decisions (decision);

CREATE INDEX IF NOT EXISTS idx_review_decisions_created_at
    ON review_decisions (created_at DESC);

-- ---------------------------------------------------------------------------
-- Review Feedback
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS review_feedback (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id             UUID REFERENCES review_decisions(id),
    feedback_type           VARCHAR(100),
    feedback_content        TEXT,
    applied_to_skill        VARCHAR(255),
    applied_to_prompt_version VARCHAR(255),
    is_actionable           BOOLEAN DEFAULT true,
    is_processed            BOOLEAN DEFAULT false,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_review_feedback_is_processed
    ON review_feedback (is_processed);

CREATE INDEX IF NOT EXISTS idx_review_feedback_feedback_type
    ON review_feedback (feedback_type);
