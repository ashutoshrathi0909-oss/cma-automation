-- Add page_type and source_sheet columns to extracted_line_items
-- These track whether a line item comes from a face sheet (P&L, BS) or Notes/Schedules
-- NULL = unknown (backwards compatible with existing data)

ALTER TABLE extracted_line_items ADD COLUMN IF NOT EXISTS page_type text DEFAULT NULL;
ALTER TABLE extracted_line_items ADD COLUMN IF NOT EXISTS source_sheet text DEFAULT NULL;

COMMENT ON COLUMN extracted_line_items.page_type IS 'face | notes | unknown - tracks document source type';
COMMENT ON COLUMN extracted_line_items.source_sheet IS 'Original sheet name (Excel) or page type (PDF)';
