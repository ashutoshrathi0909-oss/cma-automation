-- Phase 6 migration: add document_ids column to cma_reports
-- Run this in the Supabase SQL Editor before starting Phase 6.
--
-- The cma_reports table was created in Phase 0 with columns:
--   id, client_id, title, status, created_by, created_at, updated_at
--
-- Phase 6 adds document_ids (JSONB array) to link a report to its documents.

ALTER TABLE cma_reports
  ADD COLUMN IF NOT EXISTS document_ids JSONB NOT NULL DEFAULT '[]'::jsonb;

-- Index for querying reports by client
CREATE INDEX IF NOT EXISTS idx_cma_reports_client_id ON cma_reports (client_id);

-- The cma_report_history table (created in Phase 0) should already have:
--   id, cma_report_id, action, action_details (JSONB), performed_by, performed_at
-- No changes needed to that table for Phase 6.
