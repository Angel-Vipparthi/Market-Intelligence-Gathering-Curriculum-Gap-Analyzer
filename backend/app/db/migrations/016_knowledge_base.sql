-- ============================================================================
-- Migration 016: Knowledge Base Layer
-- Description: Structured curriculum hierarchy — Course → Module → Session
-- ============================================================================

CREATE TABLE IF NOT EXISTS kb_courses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_name    VARCHAR(255) NOT NULL,
    course_name     VARCHAR(500) NOT NULL,
    description     TEXT,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uq_kb_course UNIQUE (product_name, course_name)
);

CREATE TABLE IF NOT EXISTS kb_modules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id       UUID NOT NULL REFERENCES kb_courses(id) ON DELETE CASCADE,
    module_name     VARCHAR(500) NOT NULL,
    description     TEXT,
    sort_order      INT DEFAULT 0,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uq_kb_module UNIQUE (course_id, module_name)
);

CREATE TABLE IF NOT EXISTS kb_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id       UUID NOT NULL REFERENCES kb_modules(id) ON DELETE CASCADE,
    title           VARCHAR(500) NOT NULL,
    content_types   TEXT[] NOT NULL DEFAULT '{}',
    level           INT NOT NULL CHECK (level BETWEEN 1 AND 7),
    skills          TEXT[] NOT NULL DEFAULT '{}',
    description     TEXT,
    prerequisites   TEXT[] NOT NULL DEFAULT '{}',
    sort_order      INT DEFAULT 0,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uq_kb_session UNIQUE (module_id, title),
    CONSTRAINT chk_content_types CHECK (
        content_types <@ ARRAY['reading', 'coding', 'quiz', 'video']::TEXT[]
    )
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_kb_courses_product ON kb_courses (product_name);
CREATE INDEX IF NOT EXISTS idx_kb_modules_course ON kb_modules (course_id);
CREATE INDEX IF NOT EXISTS idx_kb_sessions_module ON kb_sessions (module_id);
CREATE INDEX IF NOT EXISTS idx_kb_sessions_level ON kb_sessions (level);
CREATE INDEX IF NOT EXISTS idx_kb_sessions_skills ON kb_sessions USING GIN (skills);
CREATE INDEX IF NOT EXISTS idx_kb_sessions_content_types ON kb_sessions USING GIN (content_types);
