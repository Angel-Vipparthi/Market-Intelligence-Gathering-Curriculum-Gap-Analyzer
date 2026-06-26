-- ============================================================================
-- Migration 011: Prompt Versions
-- Description: Version-controlled prompt templates linked to agent skills.
-- ============================================================================

CREATE TABLE IF NOT EXISTS prompt_versions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id            UUID REFERENCES agent_skills(skill_id),
    version             VARCHAR(50) NOT NULL,
    prompt_template     TEXT NOT NULL,
    variables           JSONB DEFAULT '[]'::jsonb,
    change_description  TEXT,
    evaluation_score    FLOAT,
    is_active           BOOLEAN DEFAULT false,
    created_by          VARCHAR(255),
    approved_by         VARCHAR(255),
    approved_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uq_prompt_skill_version UNIQUE (skill_id, version)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_prompt_versions_skill_id
    ON prompt_versions (skill_id);

CREATE INDEX IF NOT EXISTS idx_prompt_versions_is_active
    ON prompt_versions (is_active);
