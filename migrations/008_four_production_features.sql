-- Migration: 2026-03-27 Four Production Features
-- Applied to Supabase via execute_sql on 2026-03-27

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

-- Feature 4: Provisional to Audited Upgrade
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

-- RLS
ALTER TABLE conversion_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access" ON conversion_events
  FOR ALL
  USING (true)
  WITH CHECK (true);
