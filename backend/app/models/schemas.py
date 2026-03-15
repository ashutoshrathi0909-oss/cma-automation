"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

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


class ClientCreate(BaseModel):
    name: str
    industry_type: Literal["manufacturing", "service", "trading", "other"]
    financial_year_ending: str = "31st March"
    currency: str = "INR"
    notes: str | None = None


class ClientUpdate(BaseModel):
    name: str | None = None
    industry_type: Literal["manufacturing", "service", "trading", "other"] | None = None
    financial_year_ending: str | None = None
    currency: str | None = None
    notes: str | None = None


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
