export type UserRole = "admin" | "employee";

export interface UserProfile {
  id: string;
  full_name: string;
  role: UserRole;
  created_at: string;
  updated_at: string;
}

export type IndustryType = "manufacturing" | "service" | "trading" | "other";

export interface Client {
  id: string;
  name: string;
  industry_type: IndustryType;
  financial_year_ending: string;
  currency: string;
  notes: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export type FileType = "pdf" | "xlsx" | "xls";
export type DocumentType =
  | "profit_and_loss"
  | "balance_sheet"
  | "notes_to_accounts"
  | "schedules"
  | "loan_repayment_schedule"
  | "combined_financial_statement";
export type DocumentNature = "audited" | "provisional";
export type ExtractionStatus = "pending" | "processing" | "extracted" | "verified" | "failed";

export interface Document {
  id: string;
  client_id: string;
  file_name: string;
  file_path: string;
  file_type: FileType;
  document_type: DocumentType;
  financial_year: number;
  nature: DocumentNature;
  source_unit?: "rupees" | "thousands" | "lakhs" | "crores";
  extraction_status: ExtractionStatus;
  uploaded_by: string;
  uploaded_at: string;
  filtered_file_path?: string;
  removed_pages?: number[];
  original_page_count?: number;
  version_number?: number;
  parent_document_id?: string;
  superseded_at?: string;
  superseded_by?: string;
  redacted_file_path?: string;
  redaction_terms?: string[];
  redaction_count?: number;
}

export interface ExtractedLineItem {
  id: string;
  document_id: string;
  client_id: string;
  source_text: string;
  amount: number | null;
  page_number: number | null;
  section: string | null;
  financial_year: number;
  is_verified: boolean;
  verified_by: string | null;
  verified_at: string | null;
  created_at: string;
  ambiguity_question: string | null;
  page_type: string | null;
  source_sheet: string | null;
}

export type ClassificationMethod = "fuzzy_match" | "ai_haiku" | "ai_sonnet" | "manual" | "learned";
export type ClassificationStatus = "pending" | "auto_classified" | "needs_review" | "approved" | "corrected";

export interface Classification {
  id: string;
  line_item_id: string;
  client_id: string;
  cma_field_name: string | null;
  cma_sheet: "input_sheet" | "tl_sheet" | null;
  cma_row: number | null;
  cma_column: string | null;
  broad_classification: string | null;
  classification_method: ClassificationMethod | null;
  confidence_score: number | null;
  fuzzy_match_score: number | null;
  is_doubt: boolean;
  doubt_reason: string | null;
  ai_best_guess: string | null;
  alternative_fields: string[] | null;
  status: ClassificationStatus;
  reviewed_by: string | null;
  reviewed_at: string | null;
  correction_note: string | null;
  created_at: string;
  // Joined from extracted_line_items (present in API responses)
  line_item_description?: string | null;
  line_item_amount?: number | null;
  // Document context for review (joined server-side)
  line_item_section?: string | null;
  document_name?: string | null;
  document_type?: string | null;
}

export interface LineItemResponse {
  id: string;
  document_id: string;
  description: string;
  amount: number | null;
  section: string | null;
  raw_text: string | null;
  is_verified: boolean;
  ambiguity_question: string | null;
  page_type: string | null;
  source_sheet: string | null;
}

// ── Sheet preview (Excel files) ──────────────────────────────────────────

export interface SheetInfo {
  name: string;
  rows: number;
  auto_included: boolean;
}

export interface SheetsPreviewResponse {
  document_id: string;
  file_type: string;
  sheets: SheetInfo[];
}

export interface TaskStatusResponse {
  task_id: string;
  status: "queued" | "in_progress" | "complete" | "failed" | "not_found";
  document_id: string | null;
  progress: number | null;
}

export interface ExtractionTriggerResponse {
  task_id: string;
  document_id: string;
  message: string;
}

// ── CMA Report schemas (Phase 6) ─────────────────────────────────────────

export type CMAReportStatus = "draft" | "in_review" | "approved" | "generating" | "complete" | "failed";

export interface CMAReport {
  id: string;
  client_id: string;
  title: string;
  status: CMAReportStatus;
  document_ids: string[];
  cma_output_unit?: "lakhs" | "crores";
  created_by: string;
  output_path: string | null;
  created_at: string;
  updated_at: string;
  rolled_from_report_id?: string;
  roll_forward_metadata?: Record<string, unknown>;
}

export interface CMAReportCreate {
  title: string;
  document_ids: string[];
  cma_output_unit?: "lakhs" | "crores";
}

export interface ConfidenceSummary {
  total: number;
  high_confidence: number;
  medium_confidence: number;
  needs_review: number;
  approved: number;
  corrected: number;
}

export interface AuditEntry {
  id: string;
  cma_report_id: string;
  action: string;
  action_details: Record<string, unknown> | null;
  performed_by: string;
  performed_at: string;
}

// ── Phase 7: Excel Generation ─────────────────────────────────────────────

export interface GenerateTriggerResponse {
  task_id: string;
  report_id: string;
  message: string;
}

export interface DownloadUrlResponse {
  signed_url: string;
  expires_in: number;
}

// ── Phase 8: Advanced Features ────────────────────────────────────────────

export type ChangeType = "changed" | "added" | "removed";

export interface ConversionDiffItem {
  description: string;
  provisional_amount: number | null;
  audited_amount: number | null;
  change_type: ChangeType;
}

export interface ConversionDiffResponse {
  provisional_doc_id: string;
  audited_doc_id: string;
  changed: ConversionDiffItem[];
  added: ConversionDiffItem[];
  removed: ConversionDiffItem[];
}

export interface ConversionConfirmResponse {
  status: string;
  updated_count: number;
  flagged_for_review: number;
}

// ── Phase 8: Conversion V2 ──────────────────────────────────────────────

export type DiffCategory = "unchanged" | "amount_changed" | "desc_changed" | "added" | "removed";

export interface ConversionDiffItemV2 {
  provisional_item_id: string | null;
  audited_item_id: string | null;
  provisional_desc: string | null;
  audited_desc: string | null;
  provisional_amount: number | null;
  audited_amount: number | null;
  category: DiffCategory;
  match_score: number;
  needs_reclassification: boolean;
}

export interface ConversionPreviewResponseV2 {
  source_doc_id: string;
  target_doc_id: string;
  unchanged: ConversionDiffItemV2[];
  amount_changed: ConversionDiffItemV2[];
  desc_changed: ConversionDiffItemV2[];
  added: ConversionDiffItemV2[];
  removed: ConversionDiffItemV2[];
  summary: Record<DiffCategory, number>;
}

export interface ConversionConfirmResponseV2 {
  unchanged: number;
  amount_updated: number;
  reclassified: number;
  added: number;
  removed: number;
  message: string;
}

export interface RolloverItem {
  description: string;
  amount: number | null;
  cma_field_name: string | null;
  broad_classification: string | null;
}

export interface RolloverPreviewResponse {
  client_id: string;
  from_year: number;
  to_year: number;
  items_to_carry_forward: RolloverItem[];
}

export interface RolloverConfirmResponse {
  status: string;
  document_ids: string[];
  items_created: number;
}

export interface UserProfileFull extends UserProfile {
  is_active: boolean;
}

// ── Roll Forward ──────────────────────────────────────────────────────────

export interface RollForwardPreviewResponse {
  source_report_id: string;
  source_report_title: string;
  source_years: number[];
  drop_year: number | null;
  keep_years: number[];
  add_year: number;
  target_years: number[];
  carried_documents: Document[];
  dropped_documents: Document[];
  carried_classifications_count: number;
  new_year_documents: Document[];
  new_year_docs_ready: boolean;
  can_confirm: boolean;
  blocking_reasons: string[];
}

export interface RollForwardConfirmResponse {
  new_report_id: string;
  title: string;
  status: string;
  document_ids: string[];
  financial_years: number[];
  carried_classifications_count: number;
  pending_classification_docs: number;
  message: string;
}
