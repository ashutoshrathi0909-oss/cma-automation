-- Add optional cell_note column to classifications
-- Populated by agents when a NOTE_ROW instruction applies to the classified cell.
-- Rendered by the excel generator as an openpyxl Comment on the target cell.
-- NULL = no note (backwards compatible with existing rows).

ALTER TABLE classifications ADD COLUMN IF NOT EXISTS cell_note text DEFAULT NULL;

COMMENT ON COLUMN classifications.cell_note IS
  'Optional agent-emitted cell note rendered as openpyxl comment in the final Excel.';
