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
