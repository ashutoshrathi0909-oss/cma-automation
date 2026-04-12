CREATE TABLE IF NOT EXISTS cell_provenance (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cma_report_id UUID NOT NULL REFERENCES cma_reports(id) ON DELETE CASCADE,
  cma_row INTEGER NOT NULL,
  cma_column TEXT NOT NULL,
  financial_year INTEGER NOT NULL,
  line_item_id UUID NOT NULL REFERENCES extracted_line_items(id),
  classification_id UUID REFERENCES classifications(id),
  source_text TEXT,
  raw_amount FLOAT,
  converted_amount FLOAT,
  document_id UUID REFERENCES documents(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_cell_provenance_report ON cell_provenance(cma_report_id);
CREATE INDEX idx_cell_provenance_cell ON cell_provenance(cma_report_id, cma_row, cma_column);

ALTER TABLE cell_provenance ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access" ON cell_provenance FOR ALL USING (true) WITH CHECK (true);
