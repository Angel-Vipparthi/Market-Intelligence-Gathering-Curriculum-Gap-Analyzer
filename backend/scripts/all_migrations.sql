-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- Migration 001: URL Registry
-- Description: Stores registered URLs for crawling and content extraction.
-- ============================================================================

CREATE TABLE IF NOT EXISTS url_registry (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url             TEXT UNIQUE NOT NULL,
    domain          VARCHAR(500),
    source_name     VARCHAR(500),
    credibility_tier VARCHAR(50) DEFAULT 'unknown'
                        CHECK (credibility_tier IN (
                            'official_docs',
                            'major_blog',
                            'tech_publication',
                            'personal_blog',
                            'social_media',
                            'unknown'
                        )),
    category        VARCHAR(100),
    tags            TEXT[],
    is_active       BOOLEAN DEFAULT true,
    last_crawled_at TIMESTAMPTZ,
    crawl_frequency VARCHAR(50) DEFAULT 'weekly',
    added_by        VARCHAR(255),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_url_registry_domain
    ON url_registry (domain);

CREATE INDEX IF NOT EXISTS idx_url_registry_is_active
    ON url_registry (is_active);

CREATE INDEX IF NOT EXISTS idx_url_registry_category
    ON url_registry (category);
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
-- ============================================================================
-- Migration 005: Curriculum Embeddings
-- Description: pgvector embeddings for semantic search over curriculum content.
-- ============================================================================

-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS curriculum_embeddings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES curriculum_documents(id) ON DELETE CASCADE,
    embedding       vector(1536),
    chunk_index     INT DEFAULT 0,
    chunk_text      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_curriculum_embeddings_document_id
    ON curriculum_embeddings (document_id);

CREATE INDEX IF NOT EXISTS idx_curriculum_embeddings_embedding
    ON curriculum_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Cosine similarity search function
CREATE OR REPLACE FUNCTION match_curriculum(
    query_embedding vector(1536),
    match_threshold FLOAT,
    match_count INT
)
RETURNS TABLE (
    id              UUID,
    document_id     UUID,
    chunk_text      TEXT,
    similarity      FLOAT
)
LANGUAGE sql STABLE
AS $$
    SELECT
        ce.id,
        ce.document_id,
        ce.chunk_text,
        1 - (ce.embedding <=> query_embedding) AS similarity
    FROM curriculum_embeddings ce
    WHERE 1 - (ce.embedding <=> query_embedding) > match_threshold
    ORDER BY ce.embedding <=> query_embedding
    LIMIT match_count;
$$;
-- ============================================================================
-- Migration 006: Curriculum Graph
-- Description: Knowledge graph tables for curriculum structure and relationships.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- Nodes
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS curriculum_graph_nodes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_type       VARCHAR(100) NOT NULL
                        CHECK (node_type IN (
                            'course',
                            'learning_path',
                            'module',
                            'session',
                            'topic',
                            'subtopic',
                            'project',
                            'coding_challenge',
                            'assessment',
                            'quiz',
                            'tool',
                            'framework',
                            'version',
                            'market_signal',
                            'curriculum_gap'
                        )),
    name            VARCHAR(1000) NOT NULL,
    properties      JSONB,
    document_id     UUID REFERENCES curriculum_documents(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Node indexes
CREATE INDEX IF NOT EXISTS idx_curriculum_graph_nodes_node_type
    ON curriculum_graph_nodes (node_type);

CREATE INDEX IF NOT EXISTS idx_curriculum_graph_nodes_name
    ON curriculum_graph_nodes (name);

CREATE INDEX IF NOT EXISTS idx_curriculum_graph_nodes_properties
    ON curriculum_graph_nodes USING GIN (properties);

-- ---------------------------------------------------------------------------
-- Edges
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS curriculum_graph_edges (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_node_id      UUID NOT NULL REFERENCES curriculum_graph_nodes(id) ON DELETE CASCADE,
    target_node_id      UUID NOT NULL REFERENCES curriculum_graph_nodes(id) ON DELETE CASCADE,
    relationship_type   VARCHAR(100) NOT NULL
                            CHECK (relationship_type IN (
                                'PREREQUISITE_OF',
                                'PART_OF',
                                'USES_TOOL',
                                'USES_VERSION',
                                'TESTED_BY',
                                'PRACTICED_BY',
                                'IMPLEMENTS',
                                'DEPENDS_ON',
                                'IMPACTS',
                                'COVERS'
                            )),
    properties          JSONB,
    weight              FLOAT DEFAULT 1.0,
    created_at          TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uq_graph_edge UNIQUE (source_node_id, target_node_id, relationship_type)
);

-- Edge indexes
CREATE INDEX IF NOT EXISTS idx_curriculum_graph_edges_source_node_id
    ON curriculum_graph_edges (source_node_id);

CREATE INDEX IF NOT EXISTS idx_curriculum_graph_edges_target_node_id
    ON curriculum_graph_edges (target_node_id);

CREATE INDEX IF NOT EXISTS idx_curriculum_graph_edges_relationship_type
    ON curriculum_graph_edges (relationship_type);

-- ---------------------------------------------------------------------------
-- Graph traversal function
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION find_connected_nodes(
    start_node_id UUID,
    rel_type VARCHAR,
    max_depth INT DEFAULT 3
)
RETURNS TABLE (
    id              UUID,
    node_type       VARCHAR(100),
    name            VARCHAR(1000),
    properties      JSONB,
    depth           INT
)
LANGUAGE sql STABLE
AS $$
    WITH RECURSIVE traversal AS (
        -- Base case: the start node
        SELECT
            n.id,
            n.node_type,
            n.name,
            n.properties,
            0 AS depth
        FROM curriculum_graph_nodes n
        WHERE n.id = start_node_id

        UNION ALL

        -- Recursive case: follow edges of the given relationship type
        SELECT
            n.id,
            n.node_type,
            n.name,
            n.properties,
            t.depth + 1
        FROM traversal t
        JOIN curriculum_graph_edges e
            ON e.source_node_id = t.id
            AND e.relationship_type = rel_type
        JOIN curriculum_graph_nodes n
            ON n.id = e.target_node_id
        WHERE t.depth < max_depth
    )
    SELECT DISTINCT
        traversal.id,
        traversal.node_type,
        traversal.name,
        traversal.properties,
        traversal.depth
    FROM traversal
    ORDER BY traversal.depth;
$$;
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
-- ============================================================================
-- Migration 009: Workflow Costs
-- Description: Per-node cost tracking for agent workflow runs.
-- ============================================================================

CREATE TABLE IF NOT EXISTS workflow_costs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_run_id UUID NOT NULL,
    workflow_type   VARCHAR(100) NOT NULL
                        CHECK (workflow_type IN ('digest_agent', 'gap_agent')),
    node_name       VARCHAR(255) NOT NULL,
    model           VARCHAR(100),
    input_tokens    INT DEFAULT 0,
    output_tokens   INT DEFAULT 0,
    total_tokens    INT DEFAULT 0,
    latency_ms      INT,
    estimated_cost  FLOAT DEFAULT 0,
    metadata        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_workflow_costs_workflow_run_id
    ON workflow_costs (workflow_run_id);

CREATE INDEX IF NOT EXISTS idx_workflow_costs_workflow_type
    ON workflow_costs (workflow_type);

CREATE INDEX IF NOT EXISTS idx_workflow_costs_node_name
    ON workflow_costs (node_name);

CREATE INDEX IF NOT EXISTS idx_workflow_costs_created_at
    ON workflow_costs (created_at DESC);

-- ---------------------------------------------------------------------------
-- Aggregated cost summary view
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW cost_summary AS
SELECT
    workflow_type,
    node_name,
    COUNT(*)::INT                           AS total_runs,
    SUM(total_tokens)::BIGINT               AS total_tokens,
    SUM(estimated_cost)                     AS total_cost,
    AVG(latency_ms)                         AS avg_latency,
    SUM(estimated_cost) / NULLIF(COUNT(*), 0) AS avg_cost_per_run
FROM workflow_costs
GROUP BY workflow_type, node_name;
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
-- ============================================================================
-- Migration 012: Evaluation Runs
-- Description: Promptfoo evaluation results for agent prompt testing.
-- ============================================================================

CREATE TABLE IF NOT EXISTS evaluation_runs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    suite_name          VARCHAR(255) NOT NULL
                            CHECK (suite_name IN ('digest_agent', 'gap_agent')),
    prompt_version_id   UUID REFERENCES prompt_versions(id),
    total_tests         INT,
    passed_tests        INT,
    failed_tests        INT,
    score               FLOAT,
    results_detail      JSONB,
    run_by              VARCHAR(255),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_evaluation_runs_suite_name
    ON evaluation_runs (suite_name);

CREATE INDEX IF NOT EXISTS idx_evaluation_runs_created_at
    ON evaluation_runs (created_at DESC);
-- ============================================================================
-- Migration 013: Audit Logs
-- Description: Full audit trail with Row Level Security for service_role access.
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action          VARCHAR(255) NOT NULL,
    entity_type     VARCHAR(100),
    entity_id       UUID,
    actor           VARCHAR(255),
    details         JSONB,
    ip_address      VARCHAR(45),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_action
    ON audit_logs (action);

CREATE INDEX IF NOT EXISTS idx_audit_logs_entity
    ON audit_logs (entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_actor
    ON audit_logs (actor);

CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at
    ON audit_logs (created_at DESC);

-- ---------------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------------
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Allow service_role full access (read + write)
CREATE POLICY service_role_all_access
    ON audit_logs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
-- Add 'tool_registry' to curriculum_documents document_type CHECK
ALTER TABLE curriculum_documents DROP CONSTRAINT IF EXISTS curriculum_documents_document_type_check;
ALTER TABLE curriculum_documents ADD CONSTRAINT curriculum_documents_document_type_check
  CHECK (document_type IN ('session', 'project', 'coding_challenge', 'assessment', 'quiz', 'module', 'course', 'tool_registry'));

-- Unique index for upsert support in seed script
CREATE UNIQUE INDEX IF NOT EXISTS idx_curriculum_documents_title ON curriculum_documents (title);
CREATE UNIQUE INDEX IF NOT EXISTS idx_curriculum_gaps_gap_statement ON curriculum_gaps (gap_statement);
CREATE UNIQUE INDEX IF NOT EXISTS idx_url_registry_url ON url_registry (url);
