-- ============================================================================
-- Migration 018: Fix workflow_costs constraints
-- Description: Allow new workflow type names and make node_name nullable for flexibility
-- ============================================================================

ALTER TABLE workflow_costs DROP CONSTRAINT IF EXISTS workflow_costs_workflow_type_check;
ALTER TABLE workflow_costs ADD CONSTRAINT workflow_costs_workflow_type_check
    CHECK (workflow_type IN ('digest_agent', 'gap_agent', 'digest', 'gap_analysis'));
