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
