-- ============================================================================
-- Migration 004: Curriculum Documents
-- Description: Curriculum content used for retrieval and gap analysis.
-- ============================================================================

CREATE TABLE IF NOT EXISTS curriculum_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_type   VARCHAR(100) NOT NULL
                        CHECK (document_type IN (
                            'session',
                            'project',
                            'coding_challenge',
                            'assessment',
                            'quiz',
                            'module',
                            'course'
                        )),
    title           VARCHAR(1000) NOT NULL,
    content         TEXT NOT NULL,
    course_name     VARCHAR(500),
    module_name     VARCHAR(500),
    session_name    VARCHAR(500),
    tools           TEXT[],
    versions        JSONB,
    difficulty      VARCHAR(50),
    metadata        JSONB,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_curriculum_documents_document_type
    ON curriculum_documents (document_type);

CREATE INDEX IF NOT EXISTS idx_curriculum_documents_course_name
    ON curriculum_documents (course_name);

CREATE INDEX IF NOT EXISTS idx_curriculum_documents_tools
    ON curriculum_documents USING GIN (tools);

CREATE INDEX IF NOT EXISTS idx_curriculum_documents_content_fts
    ON curriculum_documents USING GIN (to_tsvector('english', content));
