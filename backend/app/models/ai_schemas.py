"""Pydantic models for Claude Haiku structured output (Phase 5 classification).

These schemas are used with the Anthropic messages.create() tool-use pattern to
get type-safe, structured responses from the AI classifier.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ClassificationCandidate(BaseModel):
    """A single CMA field candidate returned by the AI classifier."""

    cma_field_name: str = Field(..., description="Exact CMA field name from ALL_FIELD_TO_ROW")
    cma_row: int = Field(..., description="Row number in CMA INPUT SHEET")
    cma_sheet: Literal["input_sheet", "tl_sheet"] = Field(
        "input_sheet", description="Which CMA sheet this field belongs to"
    )
    broad_classification: str = Field(
        ..., description="Category: revenue/expense/asset/liability/equity"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    reasoning: str = Field(..., description="Brief reasoning for this classification")


class AIClassificationResponse(BaseModel):
    """Structured output from Claude Haiku for a single line item classification.

    This is the schema Claude must conform to when classifying a line item.
    The `is_uncertain` flag is set when confidence < 0.8 — never silently guess.
    """

    best_match: ClassificationCandidate
    alternatives: list[ClassificationCandidate] = Field(
        default_factory=list, description="Up to 3 alternative CMA fields"
    )
    is_uncertain: bool = Field(
        ..., description="True when classifier confidence < 0.8 — triggers doubt report"
    )
    uncertainty_reason: str | None = Field(
        None, description="Explanation of why the classifier is uncertain"
    )
