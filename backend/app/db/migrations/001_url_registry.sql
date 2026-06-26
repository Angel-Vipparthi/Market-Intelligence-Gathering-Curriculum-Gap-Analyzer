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
