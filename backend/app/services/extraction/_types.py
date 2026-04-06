"""
_types.py
=========
Shared types for the extraction pipeline.

Placed in a private module so that extractors can import LineItem and
parse_amount without creating circular imports with extractor_factory.py.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


# ── Text normalisation ────────────────────────────────────────────────────────

# Strips Excel note/item prefixes like "Item 1 (i) : Domestic sales" → "Domestic sales"
_NOTE_PREFIX = re.compile(
    r'^(?:(?:Item|Note|Particulars)\s*\d*\s*(?:\([^)]*\))?\s*[:.\-]\s*)',
    re.IGNORECASE,
)
_NUMBERED = re.compile(r'^\d+[.)]\s*')
_LETTERED = re.compile(r'^[a-z][.)]\s*', re.IGNORECASE)


def normalize_line_text(raw: str) -> str:
    """Strip Excel note prefixes, numbered/lettered list markers, and whitespace.

    Examples
    --------
    "Item 1 (i) : Domestic sales"  → "Domestic sales"
    "Note 3 - Depreciation"        → "Depreciation"
    "1. Salaries & Wages"          → "Salaries & Wages"
    "a) Travel expenses"           → "Travel expenses"
    "  Raw Materials  "            → "Raw Materials"
    """
    text = raw.strip()
    text = _NOTE_PREFIX.sub('', text)
    text = _NUMBERED.sub('', text)
    text = _LETTERED.sub('', text)
    return text.strip()


# ── LineItem ──────────────────────────────────────────────────────────────────


@dataclass
class LineItem:
    """A single financial line item extracted from a document."""

    description: str   # "Salaries & Wages"
    amount: float      # 1234567.89 — always normalised to float
    section: str       # "expenses", "income", "assets", "liabilities", ""
    raw_text: str      # original text / cell value before parsing
    source_sheet: str = field(default="", kw_only=True)  # sheet name for dedup priority
    page_type: str = field(default="", kw_only=True)     # NEW: "face" | "notes" | "unknown" | ""
    ambiguity_question: str | None = field(default=None, kw_only=True)


# ── Domain exception ──────────────────────────────────────────────────────────


class ExtractionError(Exception):
    """Raised when a document cannot be extracted due to file corruption or format issues."""
    pass


# ── Number parsing ─────────────────────────────────────────────────────────────


def parse_amount(text: str) -> Optional[float]:
    """Parse amount string to float, handling Indian (1,23,456) and Western (1,234,567) formats.
    Parentheses indicate negative values per Indian accounting convention: (1,23,456) → -123456.0

    Examples
    --------
    "1,23,456"     → 123456.0   (Indian lakh system)
    "1,234,567"    → 1234567.0  (Western million system)
    "500000"       → 500000.0
    "1,23,456.78"  → 123456.78
    "(1,23,456)"   → -123456.0  (parentheses = negative, Indian accounting)
    ""             → None
    "N/A"          → None
    """
    if not text or not text.strip():
        return None

    stripped = text.strip()

    # Strip leading currency symbols to normalise before negative detection
    # e.g. "₹(45,00,000)" → "(45,00,000)"
    stripped_no_currency = stripped.lstrip("₹$ ")

    # Detect parentheses-notation negative: (1,23,456) or ₹(45,00,000) → negative
    is_paren_negative = stripped_no_currency.startswith("(") and stripped_no_currency.endswith(")")

    # Detect plain leading minus: -500000 → negative
    is_minus_negative = stripped_no_currency.startswith("-")

    is_negative = is_paren_negative or is_minus_negative

    # Strip all non-numeric characters (parentheses, spaces, minus, currency)
    cleaned = stripped_no_currency.lstrip("( -").rstrip(") ").replace(",", "").strip()

    if not cleaned:
        return None

    try:
        amount = float(cleaned)
        return -amount if is_negative else amount
    except ValueError:
        return None
