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
    uploaded_by: str
    uploaded_at: datetime


# ── Extraction / Line Item schemas ────────────────────────────────────────────


class LineItemResponse(BaseModel):
    id: str
    document_id: str
    description: str
    amount: float | None
    section: str | None
    raw_text: str | None
    is_verified: bool


class LineItemUpdate(BaseModel):
    description: str | None = Field(None, min_length=1)
    amount: float | None = None
    section: str | None = None


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


class ClassificationCorrectRequest(BaseModel):
    cma_field_name: str
    cma_row: int
    cma_sheet: str = "input_sheet"
    broad_classification: str
    correction_reason: str | None = None


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


class CMAReportResponse(BaseModel):
    id: str
    client_id: str
    title: str
    status: str
    document_ids: list[str]
    created_by: str
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
