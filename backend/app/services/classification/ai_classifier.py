"""Tier 2 classification: AI classifier with structured output.

Supports two providers (configured via CLASSIFIER_PROVIDER env var):
  - "anthropic": Claude Haiku ($0.80/$4.00 per M tokens)
  - "openrouter": Qwen3.5 via OpenRouter ($0.05-$0.26 per M tokens)

Design principles:
- Uses tool_use / function calling to force structured JSON output
- confidence < 0.8 -> doubt report (NEVER silent guessing)
- API errors -> doubt result (never crash the pipeline)
- Industry context + fuzzy candidates included in every prompt
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field

from anthropic import Anthropic, RateLimitError
from openai import OpenAI

from app.config import get_settings
from app.mappings.cma_field_rows import ALL_FIELD_TO_ROW
from app.models.ai_schemas import AIClassificationResponse, ClassificationCandidate
from app.services.classification.fuzzy_matcher import FuzzyMatchResult

logger = logging.getLogger(__name__)

# Anthropic model (fallback)
ANTHROPIC_HAIKU_MODEL = "claude-haiku-4-5-20251001"

# Confidence threshold below which we flag as doubt
DOUBT_THRESHOLD = 0.8

# Tool schema for structured output (Anthropic format -- converted for OpenRouter)
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
                "description": "Set True when confidence < 0.8 -- this triggers a doubt report",
            },
            "uncertainty_reason": {
                "type": ["string", "null"],
                "description": "Required explanation when is_uncertain=True",
            },
        },
        "required": ["best_match", "alternatives", "is_uncertain"],
    },
}


def _anthropic_tool_to_openai(tool: dict) -> dict:
    """Convert Anthropic tool schema format to OpenAI function calling format."""
    return {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["input_schema"],
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
    """Classifies financial line items using AI with structured output.

    Supports both Anthropic (Claude Haiku) and OpenRouter (Qwen3.5, etc.)
    via the CLASSIFIER_PROVIDER setting.

    Uses tool_use / function calling to guarantee JSON-structured responses.
    Confidence < 0.8 always produces a doubt result -- the pipeline never silently guesses.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._provider = settings.classifier_provider.lower()

        if self._provider == "openrouter":
            self._openai_client = OpenAI(
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
            )
            self._model = settings.classifier_model
            self._method = "ai_openrouter"
        else:
            self._anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
            self._model = ANTHROPIC_HAIKU_MODEL
            self._method = "ai_haiku"

    def classify(
        self,
        raw_text: str,
        amount: float | None,
        section: str | None,
        industry_type: str,
        document_type: str,
        fuzzy_candidates: list[FuzzyMatchResult],
    ) -> AIClassificationResult:
        """Classify a line item using AI.

        Returns
        -------
        AIClassificationResult with is_doubt=True when confidence < 0.8.
        On API error, returns a doubt result instead of raising.
        """
        prompt = self._build_prompt(
            raw_text=raw_text,
            amount=amount,
            section=section,
            industry_type=industry_type,
            document_type=document_type,
            fuzzy_candidates=fuzzy_candidates,
        )

        if self._provider == "openrouter":
            return self._classify_openrouter(prompt, raw_text, industry_type)
        else:
            return self._classify_anthropic(prompt, raw_text, industry_type)

    # -- Anthropic provider -------------------------------------------------------

    def _classify_anthropic(
        self, prompt: str, raw_text: str, industry_type: str
    ) -> AIClassificationResult:
        """Classify using Anthropic Claude Haiku."""
        _delays = [5, 15, 30]
        for attempt, delay in enumerate(_delays, start=1):
            try:
                response = self._anthropic_client.messages.create(
                    model=self._model,
                    max_tokens=1024,
                    tools=[_TOOL_SCHEMA],
                    tool_choice={"type": "tool", "name": "classify_line_item"},
                    messages=[{"role": "user", "content": prompt}],
                )
                return self._parse_anthropic_response(response)

            except RateLimitError:
                if attempt < len(_delays):
                    logger.warning(
                        "Rate limit hit for '%s' (attempt %d/%d) -- sleeping %ds",
                        raw_text[:60], attempt, len(_delays), delay,
                    )
                    time.sleep(delay)
                    continue
                logger.error(
                    "AI classification failed for text='%s' industry='%s': RateLimitError (exhausted retries)",
                    raw_text, industry_type,
                )
                return self._make_doubt_result(
                    "AI classification unavailable (rate limit) -- please classify manually"
                )

            except Exception as exc:
                if attempt < len(_delays):
                    logger.warning(
                        "AI error for '%s' (attempt %d/%d, %s) -- retrying in %ds",
                        raw_text[:60], attempt, len(_delays), type(exc).__name__, delay,
                    )
                    time.sleep(delay)
                    continue
                logger.error(
                    "AI classification failed for text='%s' industry='%s': %s",
                    raw_text, industry_type, type(exc).__name__,
                )
                return self._make_doubt_result(
                    "AI classification unavailable -- please classify manually"
                )

    # -- OpenRouter provider (OpenAI-compatible) ----------------------------------

    def _classify_openrouter(
        self, prompt: str, raw_text: str, industry_type: str
    ) -> AIClassificationResult:
        """Classify using OpenRouter (Qwen3.5, etc.)."""
        openai_tool = _anthropic_tool_to_openai(_TOOL_SCHEMA)

        _delays = [5, 15, 30]
        for attempt, delay in enumerate(_delays, start=1):
            try:
                response = self._openai_client.chat.completions.create(
                    model=self._model,
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}],
                    tools=[openai_tool],
                    tool_choice={"type": "function", "function": {"name": "classify_line_item"}},
                )
                return self._parse_openrouter_response(response)

            except Exception as exc:
                # Check if it's a rate limit (OpenAI SDK raises different exception)
                is_rate_limit = "rate" in str(exc).lower() or getattr(exc, "status_code", 0) == 429
                # Retry on ANY error (rate limit or otherwise) if attempts remain
                if attempt < len(_delays):
                    logger.warning(
                        "AI error for '%s' (%s, attempt %d/%d) -- retrying in %ds",
                        raw_text[:60], type(exc).__name__, attempt, len(_delays), delay,
                    )
                    time.sleep(delay)
                    continue

                logger.error(
                    "AI classification failed for text='%s' industry='%s': %s",
                    raw_text, industry_type, type(exc).__name__,
                )
                return self._make_doubt_result(
                    "AI classification unavailable -- please classify manually"
                )

    # -- Response parsers ---------------------------------------------------------

    def _parse_anthropic_response(self, response) -> AIClassificationResult:
        """Parse Anthropic tool_use response into AIClassificationResult."""
        tool_block = next(
            (c for c in response.content if getattr(c, "type", None) == "tool_use"),
            None,
        )

        if tool_block is None:
            logger.warning("AI response contained no tool_use block")
            return self._make_doubt_result(
                "AI returned no structured output -- please classify manually"
            )

        return self._parse_tool_output(tool_block.input)

    def _parse_openrouter_response(self, response) -> AIClassificationResult:
        """Parse OpenAI-format tool call response into AIClassificationResult."""
        message = response.choices[0].message

        if not message.tool_calls:
            logger.warning("AI response contained no tool_calls")
            return self._make_doubt_result(
                "AI returned no structured output -- please classify manually"
            )

        tool_call = message.tool_calls[0]
        raw_args = tool_call.function.arguments
        try:
            tool_output = json.loads(raw_args)
        except json.JSONDecodeError:
            # Attempt JSON repair: strip trailing commas, fix common issues
            repaired = self._repair_json(raw_args)
            if repaired is not None:
                tool_output = repaired
                logger.info("Repaired malformed JSON from OpenRouter model")
            else:
                logger.error(
                    "Failed to parse OpenRouter tool arguments (even after repair): %s",
                    raw_args[:200],
                )
                return self._make_doubt_result(
                    "AI returned malformed output -- please classify manually"
                )

        return self._parse_tool_output(tool_output)

    def _parse_tool_output(self, tool_output: dict) -> AIClassificationResult:
        """Shared parser: convert tool output dict into AIClassificationResult.

        Works identically for both Anthropic and OpenRouter responses.
        """
        ai_resp = AIClassificationResponse.model_validate(tool_output)

        best = ai_resp.best_match
        confidence = best.confidence

        # Critical constraint: confidence < 0.8 -> doubt
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
            classification_method=self._method,
        )

    # -- Helpers ------------------------------------------------------------------

    def _make_doubt_result(self, reason: str) -> AIClassificationResult:
        """Create a doubt result for error cases."""
        return AIClassificationResult(
            cma_field_name=None,
            cma_row=None,
            cma_sheet="input_sheet",
            broad_classification="",
            confidence=0.0,
            is_doubt=True,
            doubt_reason=reason,
            alternatives=[],
            classification_method=self._method,
        )

    @staticmethod
    def _repair_json(raw: str) -> dict | None:
        """Attempt to repair common JSON issues from LLM tool call outputs.

        Handles: trailing commas, unescaped newlines, truncated output.
        Returns parsed dict on success, None on failure.
        """
        import re as _re

        try:
            # Strip trailing commas before } or ]
            cleaned = _re.sub(r",\s*([}\]])", r"\1", raw)
            # Fix unescaped newlines inside strings
            cleaned = cleaned.replace("\n", "\\n")
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Try extracting JSON object from surrounding text
        try:
            start = raw.index("{")
            end = raw.rindex("}") + 1
            return json.loads(raw[start:end])
        except (ValueError, json.JSONDecodeError):
            return None

    def _build_prompt(
        self,
        raw_text: str,
        amount: float | None,
        section: str | None,
        industry_type: str,
        document_type: str,
        fuzzy_candidates: list[FuzzyMatchResult],
    ) -> str:
        """Build the classification prompt for the AI model."""
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

        amount_str = f"Rs {amount:,.2f}" if amount is not None else "not provided"
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

VALID CMA FIELDS (choose ONE -- use exact field name):
{all_fields}

CLASSIFICATION RULES:
1. Match the line item to the single most appropriate CMA field from the list above
2. Use the EXACT field name from the list -- do not invent new field names
3. Set confidence based on how certain you are (0.0 to 1.0)
4. If confidence < 0.8, set is_uncertain=True and explain why in uncertainty_reason
5. NEVER guess silently -- always set is_uncertain=True when unsure
6. Consider the industry type: {industry_type} firms may have different terminology
7. Provide up to 3 alternatives in descending confidence order

Return your classification using the classify_line_item tool."""
