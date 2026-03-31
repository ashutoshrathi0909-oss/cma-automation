# Prompt 0: Run Shared Database Migration

**Run this FIRST, before any of the 4 feature prompts.**

---

## Instructions

Run this SQL migration against your Supabase database. You can do this via:
1. Supabase Dashboard → SQL Editor → paste and run, OR
2. Claude Code terminal with the Supabase MCP tool

```sql
-- Migration: 2026-03-27 Four Production Features
-- Run this ONCE before starting any feature implementation

-- Feature 1: PDF Page Removal
ALTER TABLE documents
  ADD COLUMN IF NOT EXISTS filtered_file_path TEXT,
  ADD COLUMN IF NOT EXISTS removed_pages INTEGER[],
  ADD COLUMN IF NOT EXISTS original_page_count INTEGER;

-- Feature 2: Company Name Redaction
ALTER TABLE documents
  ADD COLUMN IF NOT EXISTS redacted_file_path TEXT,
  ADD COLUMN IF NOT EXISTS redaction_terms TEXT[],
  ADD COLUMN IF NOT EXISTS redaction_count INTEGER DEFAULT 0;

-- Feature 3: Roll Forward
ALTER TABLE cma_reports
  ADD COLUMN IF NOT EXISTS rolled_from_report_id UUID REFERENCES cma_reports(id),
  ADD COLUMN IF NOT EXISTS roll_forward_metadata JSONB;

CREATE INDEX IF NOT EXISTS idx_cma_reports_rolled_from
  ON cma_reports(rolled_from_report_id)
  WHERE rolled_from_report_id IS NOT NULL;

-- Feature 4: Provisional → Audited Upgrade
ALTER TABLE documents
  ADD COLUMN IF NOT EXISTS version_number INTEGER NOT NULL DEFAULT 1,
  ADD COLUMN IF NOT EXISTS parent_document_id UUID REFERENCES documents(id),
  ADD COLUMN IF NOT EXISTS superseded_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS superseded_by UUID REFERENCES documents(id);

CREATE TABLE IF NOT EXISTS conversion_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cma_report_id UUID NOT NULL REFERENCES cma_reports(id),
  provisional_doc_id UUID NOT NULL REFERENCES documents(id),
  audited_doc_id UUID NOT NULL REFERENCES documents(id),
  diff_summary JSONB NOT NULL,
  diff_details JSONB NOT NULL,
  performed_by UUID NOT NULL,
  performed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Also save this migration file locally:
```bash
# Save migration SQL to the migrations folder
cat > migrations/008_four_features.sql << 'MIGRATION_EOF'
-- (paste the SQL above)
MIGRATION_EOF
```

After running, verify:
```sql
-- Check new columns exist
SELECT column_name FROM information_schema.columns WHERE table_name = 'documents' AND column_name IN ('filtered_file_path', 'redacted_file_path', 'version_number');
SELECT column_name FROM information_schema.columns WHERE table_name = 'cma_reports' AND column_name = 'rolled_from_report_id';
SELECT table_name FROM information_schema.tables WHERE table_name = 'conversion_events';
```
