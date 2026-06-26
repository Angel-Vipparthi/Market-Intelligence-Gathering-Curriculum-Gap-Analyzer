-- Add 'tool_registry' to curriculum_documents document_type CHECK
ALTER TABLE curriculum_documents DROP CONSTRAINT IF EXISTS curriculum_documents_document_type_check;
ALTER TABLE curriculum_documents ADD CONSTRAINT curriculum_documents_document_type_check
  CHECK (document_type IN ('session', 'project', 'coding_challenge', 'assessment', 'quiz', 'module', 'course', 'tool_registry'));

-- Unique index for upsert support in seed script
CREATE UNIQUE INDEX IF NOT EXISTS idx_curriculum_documents_title ON curriculum_documents (title);
CREATE UNIQUE INDEX IF NOT EXISTS idx_curriculum_gaps_gap_statement ON curriculum_gaps (gap_statement);
CREATE UNIQUE INDEX IF NOT EXISTS idx_url_registry_url ON url_registry (url);
