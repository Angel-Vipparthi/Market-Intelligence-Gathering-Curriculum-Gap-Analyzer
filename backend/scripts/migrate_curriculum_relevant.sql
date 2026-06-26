-- market_digests: add curriculum_relevant, drop confidence and relevance_score
ALTER TABLE market_digests ADD COLUMN IF NOT EXISTS curriculum_relevant TEXT DEFAULT 'No';
ALTER TABLE market_digests DROP COLUMN IF EXISTS confidence;
ALTER TABLE market_digests DROP COLUMN IF EXISTS relevance_score;

-- curriculum_gaps: drop confidence
ALTER TABLE curriculum_gaps DROP COLUMN IF EXISTS confidence;
