-- Migration: Add unit tracking columns
-- Run in Supabase SQL Editor BEFORE starting Docker
--
-- source_unit:     what unit the source financial document uses
-- cma_output_unit: what unit the CA wants the CMA output in

-- 1. Add source_unit to documents table
ALTER TABLE documents
  ADD COLUMN IF NOT EXISTS source_unit TEXT
  DEFAULT 'rupees'
  CHECK (source_unit IN ('rupees', 'thousands', 'lakhs', 'crores'));

-- 2. Add cma_output_unit to cma_reports table
ALTER TABLE cma_reports
  ADD COLUMN IF NOT EXISTS cma_output_unit TEXT
  DEFAULT 'lakhs'
  CHECK (cma_output_unit IN ('lakhs', 'crores'));
