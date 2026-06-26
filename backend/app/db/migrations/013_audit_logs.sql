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
