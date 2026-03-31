-- Migration: Add missing columns to cma_reports
-- Fixes BUG-5: output_path, document_ids, title columns missing
-- Fixes BUG-6: status check constraint outdated (needs 'generating' value)
--
-- Run against your Supabase project:
--   psql $DATABASE_URL -f migrations/fix_c4_cma_reports_columns.sql

-- ── BUG-5: Add missing columns ──────────────────────────────────────────────

ALTER TABLE cma_reports
  ADD COLUMN IF NOT EXISTS title TEXT,
  ADD COLUMN IF NOT EXISTS output_path TEXT,
  ADD COLUMN IF NOT EXISTS document_ids UUID[] DEFAULT '{}';

-- ── BUG-6: Update status check constraint ───────────────────────────────────
-- The original constraint only allowed: draft, in_review, approved, complete, failed
-- The app also uses 'generating' (set when Excel generation starts)

-- Drop the old constraint (name may vary — try both common patterns)
DO $$
BEGIN
  -- Try dropping by common constraint names
  ALTER TABLE cma_reports DROP CONSTRAINT IF EXISTS cma_reports_status_check;
  ALTER TABLE cma_reports DROP CONSTRAINT IF EXISTS cma_reports_check;
  ALTER TABLE cma_reports DROP CONSTRAINT IF EXISTS check_status;
EXCEPTION WHEN OTHERS THEN
  RAISE NOTICE 'No existing status constraint found, creating fresh';
END $$;

-- Create the updated constraint with all valid statuses
ALTER TABLE cma_reports
  ADD CONSTRAINT cma_reports_status_check
  CHECK (status IN ('draft', 'in_review', 'approved', 'generating', 'complete', 'failed'));

-- ── Verify ──────────────────────────────────────────────────────────────────

SELECT
  column_name,
  data_type,
  is_nullable
FROM information_schema.columns
WHERE table_name = 'cma_reports'
  AND column_name IN ('title', 'output_path', 'document_ids')
ORDER BY column_name;
