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
  extraction_status: ExtractionStatus;
  uploaded_by: string;
  uploaded_at: string;
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
}

export interface LineItemResponse {
  id: string;
  document_id: string;
  description: string;
  amount: number | null;
  section: string | null;
  raw_text: string | null;
  is_verified: boolean;
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
  created_by: string;
  output_path: string | null;
  created_at: string;
  updated_at: string;
}

export interface CMAReportCreate {
  title: string;
  document_ids: string[];
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
