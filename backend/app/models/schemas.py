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
