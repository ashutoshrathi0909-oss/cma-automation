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
  cma_field_name: string;
  cma_sheet: "input_sheet" | "tl_sheet";
  cma_row: number;
  cma_column: string | null;
  broad_classification: string | null;
  classification_method: ClassificationMethod;
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
}

export type ReportStatus =
  | "draft"
  | "extraction_pending"
  | "extraction_complete"
  | "classification_pending"
  | "classification_complete"
  | "review_in_progress"
  | "approved"
  | "excel_generated";

export interface CMAReport {
  id: string;
  client_id: string;
  financial_years: number[];
  year_natures: Record<string, DocumentNature>;
  status: ReportStatus;
  total_line_items: number;
  high_confidence_count: number;
  medium_confidence_count: number;
  needs_review_count: number;
  output_file_path: string | null;
  generated_at: string | null;
  approved_by: string | null;
  approved_at: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}
