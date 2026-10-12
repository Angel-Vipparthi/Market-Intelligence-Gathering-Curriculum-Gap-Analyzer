-- ============================================================================
-- Migration 019: KB Sheet Configs
-- Description: Stores Google Sheet URLs per course for loading knowledge base.
-- ============================================================================

CREATE TABLE IF NOT EXISTS kb_sheet_configs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_name    VARCHAR(255) NOT NULL,
    course_name     VARCHAR(500) NOT NULL,
    sheet_url       TEXT NOT NULL,
    spreadsheet_id  VARCHAR(255) NOT NULL,
    is_active       BOOLEAN DEFAULT true,
    last_loaded_at  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_kb_sheet_config UNIQUE (product_name, course_name)
);
