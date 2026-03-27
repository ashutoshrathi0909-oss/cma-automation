"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# ── Shared type aliases ───────────────────────────────────────────────────────

FileType = Literal["pdf", "xlsx", "xls"]
DocumentType = Literal[
    "profit_and_loss",
    "balance_sheet",
    "notes_to_accounts",
    "schedules",
    "loan_repayment_schedule",
    "combined_financial_statement",
]
DocumentNature = Literal["audited", "provisional"]
ExtractionStatus = Literal["pending", "processing", "extracted", "verified", "failed"]
SourceUnit = Literal["rupees", "thousands", "lakhs", "crores"]
CMAOutputUnit = Literal["lakhs", "crores"]

UserRole = Literal["admin", "employee"]


# ── Auth schemas ──────────────────────────────────────────────────────────────


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    role: UserRole = "employee"


class UserProfile(BaseModel):
    id: str
    full_name: str
    role: UserRole
    is_active: bool = True  # Phase 8: user management
    created_at: datetime
    updated_at: datetime


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


# ── Client schemas ────────────────────────────────────────────────────────────


IndustryType = Literal["manufacturing", "service", "trading", "other"]


class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    industry_type: IndustryType
    financial_year_ending: str = Field("31st March", max_length=50)
    currency: str = Field("INR", min_length=1, max_length=10)
    notes: str | None = Field(None, max_length=2000)


class ClientUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    industry_type: IndustryType | None = None
    financial_year_ending: str | None = Field(None, max_length=50)
    currency: str | None = Field(None, min_length=1, max_length=10)
    notes: str | None = Field(None, max_length=2000)


class ClientResponse(BaseModel):
    id: str
    name: str
    industry_type: str
    financial_year_ending: str
    currency: str
    notes: str | None
    created_by: str | None
    created_at: datetime
    updated_at: datetime


# ── Document schemas ──────────────────────────────────────────────────────────


class DocumentResponse(BaseModel):
    id: str
    client_id: str
    file_name: str
    file_path: str
    file_type: FileType
    document_type: DocumentType
    financial_year: int
    nature: DocumentNature
    extraction_status: ExtractionStatus
    source_unit: SourceUnit = "rupees"
    uploaded_by: str
    uploaded_at: datetime


class FilterPagesRequest(BaseModel):
    pages_to_remove: str  # "1-2, 7, 10-15"


class FilterPagesResponse(BaseModel):
    document_id: str
    original_page_count: int
    removed_pages: list[int]
    filtered_page_count: int


class PageCountResponse(BaseModel):
    document_id: str
    page_count: int


# ── Extraction / Line Item schemas ────────────────────────────────────────────


class LineItemResponse(BaseModel):
    id: str
    document_id: str
    description: str
    amount: float | None
    section: str | None
    raw_text: str | None
    is_verified: bool
    ambiguity_question: str | None = None

    @classmethod
    def from_db(cls, row: dict) -> "LineItemResponse":
        """Construct from a DB row, mapping source_text → description/raw_text."""
        source = row.get("source_text") or row.get("description") or ""
        return cls(
            id=row["id"],
            document_id=row["document_id"],
            description=source,
            amount=row.get("amount"),
            section=row.get("section"),
            raw_text=row.get("raw_text") or source,
            is_verified=row.get("is_verified", False),
            ambiguity_question=row.get("ambiguity_question"),
        )


class LineItemUpdate(BaseModel):
    description: str | None = Field(None, min_length=1)
    amount: float | None = None
    section: str | None = None
    ambiguity_question: str | None = None


TaskStatus = Literal["queued", "in_progress", "complete", "failed", "not_found"]


class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    document_id: str | None = None
    progress: int | None = None  # 0-100


class ExtractionTriggerResponse(BaseModel):
    task_id: str
    document_id: str
    message: str


# ── Classification schemas ─────────────────────────────────────────────────────

ClassificationMethod = Literal[
    "fuzzy_match", "learned", "ai_haiku", "ai_sonnet", "manual"
]
ClassificationStatus = Literal[
    "pending", "auto_classified", "needs_review", "approved", "corrected"
]


class ClassificationResponse(BaseModel):
    """API response for a single classification result."""

    id: str
    line_item_id: str
    client_id: str
    cma_field_name: str | None
    cma_sheet: str | None
    cma_row: int | None
    cma_column: str | None
    broad_classification: str | None
    classification_method: str | None
    confidence_score: float | None
    fuzzy_match_score: float | None
    is_doubt: bool
    doubt_reason: str | None
    ai_best_guess: str | None
    alternative_fields: list | None
    status: str
    reviewed_by: str | None
    reviewed_at: datetime | None
    correction_note: str | None
    created_at: datetime
    # Joined from extracted_line_items for convenience
    line_item_description: str | None = None
    line_item_amount: float | None = None


class ClassificationApproveRequest(BaseModel):
    note: str | None = None
    cma_report_id: str | None = None  # When provided, writes audit log to cma_report_history


class ClassificationCorrectRequest(BaseModel):
    cma_field_name: str
    cma_row: int
    cma_sheet: str = "input_sheet"
    broad_classification: str
    correction_reason: str | None = None
    cma_report_id: str | None = None  # When provided, writes audit log to cma_report_history


class BulkApproveRequest(BaseModel):
    """Bulk approve request. If classification_ids is None, approve all high-confidence."""

    classification_ids: list[str] | None = None


class BulkApproveResponse(BaseModel):
    approved_count: int
    message: str


class ClassificationTriggerResponse(BaseModel):
    task_id: str
    document_id: str
    message: str


class ClassificationSummary(BaseModel):
    total: int
    high_confidence: int
    medium_confidence: int
    needs_review: int


# ── CMA Report schemas ─────────────────────────────────────────────────────


class CMAReportCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    document_ids: list[str] = Field(..., min_length=1)
    cma_output_unit: CMAOutputUnit = "lakhs"


class CMAReportResponse(BaseModel):
    id: str
    client_id: str
    title: str
    status: str
    document_ids: list[str]
    cma_output_unit: CMAOutputUnit = "lakhs"
    created_by: str
    output_path: str | None = None
    created_at: datetime
    updated_at: datetime


class ConfidenceSummary(BaseModel):
    total: int
    high_confidence: int
    medium_confidence: int
    needs_review: int
    approved: int
    corrected: int


class AuditEntry(BaseModel):
    id: str
    cma_report_id: str
    action: str
    action_details: dict | None
    performed_by: str
    performed_at: datetime


# ── Phase 7: Excel Generation schemas ──────────────────────────────────────


class GenerateTriggerResponse(BaseModel):
    task_id: str
    report_id: str
    message: str


class DownloadUrlResponse(BaseModel):
    signed_url: str
    expires_in: int = Field(default=60, description="Seconds until the signed URL expires.", gt=0)


# ── Phase 8: Conversion schemas ───────────────────────────────────────────

ChangeType = Literal["changed", "added", "removed"]


class ConversionDiffItem(BaseModel):
    description: str
    provisional_amount: float | None
    audited_amount: float | None
    change_type: ChangeType


class ConversionPreviewRequest(BaseModel):
    provisional_doc_id: str
    audited_doc_id: str


class ConversionDiffResponse(BaseModel):
    provisional_doc_id: str
    audited_doc_id: str
    changed: list[ConversionDiffItem]
    added: list[ConversionDiffItem]
    removed: list[ConversionDiffItem]


class ConversionConfirmRequest(BaseModel):
    provisional_doc_id: str
    audited_doc_id: str
    cma_report_id: str


class ConversionConfirmResponse(BaseModel):
    status: str
    updated_count: int
    flagged_for_review: int


# ── Phase 8: Conversion V2 schemas ──────────────────────────────────────

DiffCategoryType = Literal["unchanged", "amount_changed", "desc_changed", "added", "removed"]


class ConversionDiffItemV2(BaseModel):
    provisional_item_id: str | None = None
    audited_item_id: str | None = None
    provisional_desc: str | None = None
    audited_desc: str | None = None
    provisional_amount: float | None = None
    audited_amount: float | None = None
    category: DiffCategoryType
    match_score: float
    needs_reclassification: bool


class ConversionPreviewResponseV2(BaseModel):
    source_doc_id: str
    target_doc_id: str
    unchanged: list[ConversionDiffItemV2]
    amount_changed: list[ConversionDiffItemV2]
    desc_changed: list[ConversionDiffItemV2]
    added: list[ConversionDiffItemV2]
    removed: list[ConversionDiffItemV2]
    summary: dict


class ConversionConfirmResponseV2(BaseModel):
    unchanged: int
    amount_updated: int
    reclassified: int
    added: int
    removed: int
    message: str


# ── Phase 8: Rollover schemas ─────────────────────────────────────────────


class RolloverItem(BaseModel):
    description: str
    amount: float | None
    cma_field_name: str | None
    broad_classification: str | None


class RolloverPreviewRequest(BaseModel):
    client_id: str
    from_year: int
    to_year: int


class RolloverPreviewResponse(BaseModel):
    client_id: str
    from_year: int
    to_year: int
    items_to_carry_forward: list[RolloverItem]


class RolloverConfirmRequest(BaseModel):
    client_id: str
    from_year: int
    to_year: int


class RolloverConfirmResponse(BaseModel):
    status: str
    document_ids: list[str]
    items_created: int


# ── Phase 8: User Management schemas ────────────────────────────────────


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    role: UserRole | None = None


# ── Roll Forward schemas ─────────────────────────────────────────────────


class RollForwardPreviewRequest(BaseModel):
    source_report_id: str
    client_id: str
    add_year: int | None = None


class RollForwardConfirmRequest(BaseModel):
    source_report_id: str
    client_id: str
    add_year: int
    new_document_ids: list[str]
    title: str | None = None
    cma_output_unit: CMAOutputUnit = "lakhs"
