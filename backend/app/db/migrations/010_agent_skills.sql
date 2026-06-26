-- ============================================================================
-- Migration 010: Agent Skills
-- Description: Reusable agent skills with performance tracking.
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_skills (
    skill_id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_name              VARCHAR(255) NOT NULL UNIQUE,
    agent_type              VARCHAR(100) NOT NULL
                                CHECK (agent_type IN ('digest_agent', 'gap_agent')),
    description             TEXT,
    current_prompt_version  VARCHAR(50),
    evaluation_score        FLOAT,
    usage_count             INT DEFAULT 0,
    success_rate            FLOAT,
    last_used_at            TIMESTAMPTZ,
    is_active               BOOLEAN DEFAULT true,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_agent_skills_agent_type
    ON agent_skills (agent_type);

CREATE INDEX IF NOT EXISTS idx_agent_skills_is_active
    ON agent_skills (is_active);
