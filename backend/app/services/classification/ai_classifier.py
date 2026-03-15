"""Tier 2 classification: Claude Haiku AI classifier with structured output.

Design principles:
- Uses tool_use to force structured JSON output from Claude
- confidence < 0.8 → doubt report (NEVER silent guessing)
- API errors → doubt result (never crash the pipeline)
- Industry context + fuzzy candidates included in every prompt
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from anthropic import Anthropic

from app.config import get_settings
from app.mappings.cma_field_rows import ALL_FIELD_TO_ROW
from app.models.ai_schemas import AIClassificationResponse, ClassificationCandidate
from app.services.classification.fuzzy_matcher import FuzzyMatchResult

logger = logging.getLogger(__name__)

# Model to use for AI classification
HAIKU_MODEL = "claude-haiku-4-5-20251001"

# Confidence threshold below which we flag as doubt
DOUBT_THRESHOLD = 0.8

# Tool schema for structured output (forces Claude to return valid JSON)
_TOOL_SCHEMA = {
    "name": "classify_line_item",
    "description": (
        "Classify a financial line item into the correct CMA (Credit Monitoring Arrangement) "
        "field. Return a best match with confidence score and up to 3 alternatives."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "best_match": {
                "type": "object",
                "description": "The most likely CMA field for this line item",
                "properties": {
                    "cma_field_name": {
                        "type": "string",
                        "description": "Exact CMA field name from the provided list",
                    },
                    "cma_row": {
                        "type": "integer",
                        "description": "Row number in the CMA INPUT SHEET",
                    },
                    "cma_sheet": {
                        "type": "string",
                        "enum": ["input_sheet", "tl_sheet"],
                        "description": "Which CMA sheet",
                    },
                    "broad_classification": {
                        "type": "string",
                        "description": "Category: revenue/manufacturing_expense/admin_expense/asset/liability/equity",
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Confidence score from 0.0 to 1.0",
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Brief reasoning for this classification",
                    },
                },
                "required": [
                    "cma_field_name",
                    "cma_row",
                    "cma_sheet",
                    "broad_classification",
                    "confidence",
                    "reasoning",
                ],
            },
            "alternatives": {
                "type": "array",
                "description": "Up to 3 alternative CMA fields (in descending confidence)",
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "properties": {
                        "cma_field_name": {"type": "string"},
                        "cma_row": {"type": "integer"},
                        "cma_sheet": {
                            "type": "string",
                            "enum": ["input_sheet", "tl_sheet"],
                        },
                        "broad_classification": {"type": "string"},
                        "confidence": {"type": "number"},
                        "reasoning": {"type": "string"},
                    },
                    "required": [
                        "cma_field_name",
                        "cma_row",
                        "cma_sheet",
                        "broad_classification",
                        "confidence",
                        "reasoning",
                    ],
                },
            },
            "is_uncertain": {
                "type": "boolean",
                "description": "Set True when confidence < 0.8 — this triggers a doubt report",
            },
            "uncertainty_reason": {
                "type": ["string", "null"],
                "description": "Required explanation when is_uncertain=True",
            },
        },
        "required": ["best_match", "alternatives", "is_uncertain"],
    },
}


@dataclass
class AIClassificationResult:
    """Result from the AI classifier for a single line item."""

    cma_field_name: str | None
    cma_row: int | None
    cma_sheet: str
    broad_classification: str
    confidence: float
    is_doubt: bool
    doubt_reason: str | None
    alternatives: list[ClassificationCandidate] = field(default_factory=list)
    classification_method: str = "ai_haiku"


class AIClassifier:
    """Classifies financial line items using Claude Haiku with structured output.

    Uses tool_use to guarantee JSON-structured responses. Confidence < 0.8
    always produces a doubt result — the pipeline never silently guesses.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._client = Anthropic(api_key=settings.anthropic_api_key)

    def classify(
        self,
        raw_text: str,
        amount: float | None,
        section: str | None,
        industry_type: str,
        document_type: str,
        fuzzy_candidates: list[FuzzyMatchResult],
    ) -> AIClassificationResult:
        """Classify a line item using Claude Haiku.

        Returns
        -------
        AIClassificationResult with is_doubt=True when confidence < 0.8.
        On API error, returns a doubt result instead of raising.
        """
        try:
            prompt = self._build_prompt(
                raw_text=raw_text,
                amount=amount,
                section=section,
                industry_type=industry_type,
                document_type=document_type,
                fuzzy_candidates=fuzzy_candidates,
            )

            response = self._client.messages.create(
                model=HAIKU_MODEL,
                max_tokens=1024,
                tools=[_TOOL_SCHEMA],
                tool_choice={"type": "tool", "name": "classify_line_item"},
                messages=[{"role": "user", "content": prompt}],
            )

            return self._parse_response(response)

        except Exception as exc:
            logger.error(
                "AI classification failed for text='%s' industry='%s': %s",
                raw_text,
                industry_type,
                type(exc).__name__,  # log error type only, not full message (may contain keys)
            )
            return AIClassificationResult(
                cma_field_name=None,
                cma_row=None,
                cma_sheet="input_sheet",
                broad_classification="",
                confidence=0.0,
                is_doubt=True,
                doubt_reason="AI classification unavailable — please classify manually",
                alternatives=[],
                classification_method="ai_haiku",
            )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_prompt(
        self,
        raw_text: str,
        amount: float | None,
        section: str | None,
        industry_type: str,
        document_type: str,
        fuzzy_candidates: list[FuzzyMatchResult],
    ) -> str:
        """Build the classification prompt for Claude Haiku."""
        # Format fuzzy candidates as context
        fuzzy_context = ""
        if fuzzy_candidates:
            lines = []
            for r in fuzzy_candidates[:5]:
                lines.append(
                    f"  - {r.cma_field_name} (row {r.cma_row}, score={r.score:.0f})"
                )
            fuzzy_context = "FUZZY MATCH SUGGESTIONS (top candidates):\n" + "\n".join(lines)
        else:
            fuzzy_context = "FUZZY MATCH SUGGESTIONS: none found"

        # Format all valid CMA fields
        all_fields = "\n".join(
            f"  Row {row}: {field_name}"
            for field_name, row in sorted(ALL_FIELD_TO_ROW.items(), key=lambda x: x[1])
        )

        amount_str = f"₹{amount:,.2f}" if amount is not None else "not provided"
        section_str = section or "not specified"

        return f"""You are a financial analyst classifying line items for Indian CMA (Credit Monitoring Arrangement) documents.

TASK: Classify the following accounting line item into the correct CMA field.

LINE ITEM DETAILS:
  Description: {raw_text}
  Amount: {amount_str}
  Section/Category: {section_str}
  Industry Type: {industry_type}
  Document Type: {document_type}

{fuzzy_context}

VALID CMA FIELDS (choose ONE — use exact field name):
{all_fields}

CLASSIFICATION RULES:
1. Match the line item to the single most appropriate CMA field from the list above
2. Use the EXACT field name from the list — do not invent new field names
3. Set confidence based on how certain you are (0.0 to 1.0)
4. If confidence < 0.8, set is_uncertain=True and explain why in uncertainty_reason
5. NEVER guess silently — always set is_uncertain=True when unsure
6. Consider the industry type: {industry_type} firms may have different terminology
7. Provide up to 3 alternatives in descending confidence order

Return your classification using the classify_line_item tool."""

    def _parse_response(self, response) -> AIClassificationResult:
        """Parse Anthropic tool_use response into AIClassificationResult."""
        # Find the tool_use block in the response
        tool_block = next(
            (c for c in response.content if getattr(c, "type", None) == "tool_use"),
            None,
        )

        if tool_block is None:
            logger.warning("AI response contained no tool_use block")
            return AIClassificationResult(
                cma_field_name=None,
                cma_row=None,
                cma_sheet="input_sheet",
                broad_classification="",
                confidence=0.0,
                is_doubt=True,
                doubt_reason="AI returned no structured output — please classify manually",
                alternatives=[],
                classification_method="ai_haiku",
            )

        # Parse using Pydantic model
        ai_resp = AIClassificationResponse.model_validate(tool_block.input)

        best = ai_resp.best_match
        confidence = best.confidence

        # Critical constraint: confidence < 0.8 → doubt
        is_doubt = confidence < DOUBT_THRESHOLD or ai_resp.is_uncertain
        doubt_reason: str | None = None
        if is_doubt:
            doubt_reason = ai_resp.uncertainty_reason or (
                f"AI confidence {confidence:.2f} below threshold {DOUBT_THRESHOLD}"
            )

        return AIClassificationResult(
            cma_field_name=best.cma_field_name,
            cma_row=best.cma_row,
            cma_sheet=best.cma_sheet,
            broad_classification=best.broad_classification,
            confidence=confidence,
            is_doubt=is_doubt,
            doubt_reason=doubt_reason,
            alternatives=ai_resp.alternatives,
            classification_method="ai_haiku",
        )
