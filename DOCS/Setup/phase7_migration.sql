-- Phase 7 migration: add output_path column to cma_reports
-- Run this in the Supabase SQL Editor before starting Phase 7.
--
-- cma_reports table after Phase 6:
--   id, client_id, title, status, document_ids, created_by, created_at, updated_at
--
-- Phase 7 adds:
--   output_path TEXT  — Supabase Storage path to generated .xlsm (set on completion)

ALTER TABLE cma_reports
  ADD COLUMN IF NOT EXISTS output_path TEXT;
