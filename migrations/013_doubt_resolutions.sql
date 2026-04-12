CREATE TABLE IF NOT EXISTS doubt_resolutions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  classification_id UUID NOT NULL REFERENCES classifications(id) ON DELETE CASCADE,
  cma_report_id UUID REFERENCES cma_reports(id),
  original_source_text TEXT,
  resolved_cma_row INTEGER,
  resolved_cma_field TEXT,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
  resolved_by UUID,
  approved_by UUID,
  rejected_by UUID,
  rejection_reason TEXT,
  note TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_doubt_resolutions_report ON doubt_resolutions(cma_report_id);
CREATE INDEX idx_doubt_resolutions_status ON doubt_resolutions(status);
CREATE INDEX idx_doubt_resolutions_classification ON doubt_resolutions(classification_id);

ALTER TABLE doubt_resolutions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access" ON doubt_resolutions FOR ALL USING (true) WITH CHECK (true);
