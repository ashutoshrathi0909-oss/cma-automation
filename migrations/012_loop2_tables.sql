-- Loop 2: Father review — questionnaires, answers, and proposed rules

CREATE TABLE IF NOT EXISTS questionnaires (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cma_report_id UUID NOT NULL REFERENCES cma_reports(id) ON DELETE CASCADE,
  ai_file_path TEXT,
  corrected_file_path TEXT,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'answered', 'processed')),
  created_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS questionnaire_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  questionnaire_id UUID NOT NULL REFERENCES questionnaires(id) ON DELETE CASCADE,
  question_id TEXT NOT NULL,
  cma_row INTEGER NOT NULL,
  cma_column TEXT NOT NULL,
  ai_value FLOAT,
  father_value FLOAT,
  source_items JSONB DEFAULT '[]',
  options JSONB DEFAULT '[]',
  selected_option TEXT,
  cma_row_correction INTEGER,
  note TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS proposed_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  questionnaire_id UUID REFERENCES questionnaires(id),
  source_pattern TEXT NOT NULL,
  original_cma_row INTEGER,
  target_cma_row INTEGER NOT NULL,
  specialist TEXT NOT NULL,
  industry_type TEXT NOT NULL DEFAULT 'manufacturing',
  tier_tag TEXT NOT NULL DEFAULT 'CA_VERIFIED_2026',
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'promoted')),
  created_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_questionnaires_report ON questionnaires(cma_report_id);
CREATE INDEX idx_questionnaire_items_qid ON questionnaire_items(questionnaire_id);
CREATE INDEX idx_proposed_rules_status ON proposed_rules(status);

ALTER TABLE questionnaires ENABLE ROW LEVEL SECURITY;
ALTER TABLE questionnaire_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE proposed_rules ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access" ON questionnaires FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON questionnaire_items FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON proposed_rules FOR ALL USING (true) WITH CHECK (true);
