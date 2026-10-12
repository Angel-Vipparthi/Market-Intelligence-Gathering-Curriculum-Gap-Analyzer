-- ============================================================================
-- Migration 020: Add course_name to url_registry
-- Description: Associates URLs with specific courses for filtering.
-- ============================================================================

ALTER TABLE url_registry ADD COLUMN IF NOT EXISTS course_name VARCHAR(500);

CREATE INDEX IF NOT EXISTS idx_url_registry_course_name ON url_registry (course_name);

-- Tag existing URLs as React (they were seeded from React course sheet)
UPDATE url_registry SET course_name = 'React' WHERE added_by = 'google_sheet_seed' AND course_name IS NULL;
