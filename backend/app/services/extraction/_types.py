"""
_types.py
=========
Shared types for the extraction pipeline.

Placed in a private module so that extractors can import LineItem and
parse_amount without creating circular imports with extractor_factory.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ── LineItem ──────────────────────────────────────────────────────────────────


@dataclass
class LineItem:
    """A single financial line item extracted from a document."""

    description: str   # "Salaries & Wages"
    amount: float      # 1234567.89 — always normalised to float
    section: str       # "expenses", "income", "assets", "liabilities", ""
    raw_text: str      # original text / cell value before parsing


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
