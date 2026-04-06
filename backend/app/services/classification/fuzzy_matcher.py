"""FuzzyMatchResult dataclass — kept for backwards compatibility.

The FuzzyMatcher class was removed in April 2026 when the classification
pipeline was simplified to AI-only. This dataclass remains because
ai_classifier.py (legacy, unchanged) imports it for type hints.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FuzzyMatchResult:
    """Result of a fuzzy match against the CMA mapping tables."""

    cma_field_name: str
    cma_row: int
    cma_sheet: str
    broad_classification: str
    score: float
    source: str
