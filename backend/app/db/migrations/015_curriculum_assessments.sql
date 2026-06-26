-- ============================================================================
-- Migration 015: Curriculum Assessments
-- Description: Structured assessment/quiz data linked to curriculum units.
-- ============================================================================

CREATE TABLE IF NOT EXISTS curriculum_assessments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unit_id         UUID NOT NULL,
    exam_title      VARCHAR(500) NOT NULL,
    exam_type       VARCHAR(100) NOT NULL
                        CHECK (exam_type IN (
                            'mcq_exam', 'mcq_quiz', 'course_quiz', 'coding_exam'
                        )),
    question_id     UUID NOT NULL,
    question_type   VARCHAR(100) NOT NULL,
    question_content TEXT NOT NULL,
    correct_answer  TEXT,
    available_options JSONB,
    parent_title    VARCHAR(500),
    parent_description TEXT,
    total_max_score FLOAT,
    metadata        JSONB,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uq_assessment_question UNIQUE (unit_id, question_id)
);

CREATE INDEX IF NOT EXISTS idx_curriculum_assessments_unit_id
    ON curriculum_assessments (unit_id);

CREATE INDEX IF NOT EXISTS idx_curriculum_assessments_exam_type
    ON curriculum_assessments (exam_type);

CREATE INDEX IF NOT EXISTS idx_curriculum_assessments_content_fts
    ON curriculum_assessments USING GIN (to_tsvector('english', question_content));
