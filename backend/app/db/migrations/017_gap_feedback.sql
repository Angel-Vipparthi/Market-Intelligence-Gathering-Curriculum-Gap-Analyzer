-- ============================================================================
-- Migration 017: Gap Feedback Fields
-- Description: User feedback on what/why/when to act for gap improvement loop
-- ============================================================================

ALTER TABLE curriculum_gaps ADD COLUMN IF NOT EXISTS feedback_what TEXT;
ALTER TABLE curriculum_gaps ADD COLUMN IF NOT EXISTS feedback_why TEXT;
ALTER TABLE curriculum_gaps ADD COLUMN IF NOT EXISTS feedback_when TEXT;
ALTER TABLE curriculum_gaps ADD COLUMN IF NOT EXISTS has_feedback BOOLEAN DEFAULT false;
ALTER TABLE curriculum_gaps ADD COLUMN IF NOT EXISTS feedback_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_curriculum_gaps_has_feedback
    ON curriculum_gaps (has_feedback) WHERE has_feedback = true;
