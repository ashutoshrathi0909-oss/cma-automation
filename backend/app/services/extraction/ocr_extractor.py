"""
ocr_extractor.py
================
Extracts financial line items from scanned (image-only) PDFs using vision models.

Supports two providers (configured via OCR_PROVIDER env var):
  - "anthropic": Claude Sonnet Vision (~Rs 2.30/page)
  - "openrouter": Gemini 2.5 Flash via OpenRouter (~Rs 0.05/page)

Pipeline:
  1. Convert PDF pages to PIL Images via pdf2image (wraps existing poppler-utils).
  2. Filter blank pages via page_filter.
  3. Send content pages to vision model in batches of MAX_PAGES_PER_BATCH.
  4. Parse structured JSON response into LineItem instances.
  5. Flag ambiguous items with ambiguity_question for CA review.
"""
from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import re
from typing import Any

import anthropic
from openai import OpenAI
from PIL import Image

from app.config import get_settings
from app.services.extraction._types import ExtractionError, LineItem
from app.services.extraction.page_filter import filter_pages
from app.services.extraction.vision_prompt import (
    EXTRACT_JSON_SCHEMA,
    EXTRACT_TOOL_SCHEMA,
    MAX_PAGES_PER_BATCH,
    SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)

# Anthropic model (fallback)
ANTHROPIC_VISION_MODEL = "claude-sonnet-4-6"

# DPI for PDF -> image conversion. 200 = good balance of quality vs cost.
CONVERSION_DPI = 200

# Max image width sent to model (controls token usage). 1600px is sufficient.
MAX_IMAGE_WIDTH = 1600


def convert_from_bytes(file_content: bytes, dpi: int = CONVERSION_DPI) -> list[Image.Image]:
    """Convert PDF bytes to PIL Images (one per page). Wraps pdf2image for testability."""
    from pdf2image import convert_from_bytes as _convert  # lazy import -- not installed in CI
    return _convert(file_content, dpi=dpi)


def _image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64-encoded JPEG string for vision API.

    Resizes to MAX_IMAGE_WIDTH preserving aspect ratio.
    Converts RGBA -> RGB. Uses JPEG for smaller payload vs PNG.
    """
    if image.width > MAX_IMAGE_WIDTH:
        ratio = MAX_IMAGE_WIDTH / image.width
        new_height = int(image.height * ratio)
        image = image.resize((MAX_IMAGE_WIDTH, new_height), Image.LANCZOS)

    if image.mode != "RGB":
        image = image.convert("RGB")

    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=85)
    return base64.standard_b64encode(buf.getvalue()).decode("utf-8")


def _get_scale_multiplier(scale: str) -> float:
    """Return multiplier to convert amounts to absolute rupees."""
    return {
        "absolute": 1.0,
        "in_thousands": 1_000.0,
        "in_lakhs": 100_000.0,
        "in_crores": 10_000_000.0,
    }.get(scale, 1.0)


def _normalize_page_type(ocr_page_type: str) -> str:
    """Map vision AI page_type to normalized value."""
    _FACE_TYPES = {"profit_and_loss", "balance_sheet", "trading_account"}
    _NOTE_TYPES = {"notes_to_accounts", "schedules"}
    if ocr_page_type in _FACE_TYPES:
        return "face"
    if ocr_page_type in _NOTE_TYPES:
        return "notes"
    return "unknown"


class OcrExtractor:
    """Extracts LineItems from scanned (image-only) PDFs using vision models.

    Supports both Anthropic (Claude Sonnet) and OpenRouter (Gemini 2.5 Flash)
    via the OCR_PROVIDER setting.
    """

    async def extract(self, file_content: bytes) -> list[LineItem]:
        """Extract financial line items from a scanned PDF.

        Returns an empty list (not an error) if no content pages are found.
        Raises ExtractionError on PDF conversion failure or unrecoverable API error.
        """
        try:
            # Step 1: Convert PDF -> images
            images = convert_from_bytes(file_content)
            logger.info("Converted PDF to %d page images (DPI=%d)", len(images), CONVERSION_DPI)

            # Step 2: Filter blank pages
            content_pages = filter_pages(images)
            logger.info("After blank-page filter: %d pages with content", len(content_pages))

            if not content_pages:
                logger.warning("No content pages found in scanned PDF -- returning empty list")
                return []

            # Step 3: Process in batches (async wrapper around sync API client)
            settings = get_settings()
            provider = settings.ocr_provider.lower()
            logger.info("Using OCR provider: %s", provider)

            all_items: list[LineItem] = []
            for batch_start in range(0, len(content_pages), MAX_PAGES_PER_BATCH):
                batch = content_pages[batch_start : batch_start + MAX_PAGES_PER_BATCH]

                if provider == "openrouter":
                    batch_items = await asyncio.to_thread(self._process_batch_openrouter, batch)
                else:
                    batch_items = await asyncio.to_thread(self._process_batch_anthropic, batch)

                all_items.extend(batch_items)
                logger.info(
                    "Batch %d-%d: extracted %d items",
                    batch_start + 1,
                    batch_start + len(batch),
                    len(batch_items),
                )

            logger.info("Vision OCR complete: %d total line items", len(all_items))
            return all_items

        except ExtractionError:
            raise
        except Exception as exc:
            raise ExtractionError(f"Vision OCR failed: {exc}") from exc

    # -- Anthropic provider -------------------------------------------------------

    def _process_batch_anthropic(
        self, pages: list[tuple[int, Image.Image]]
    ) -> list[LineItem]:
        """Send a batch of page images to Claude Sonnet Vision. Returns parsed LineItems."""
        settings = get_settings()
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        # Build message content: text label + image per page
        content: list[dict[str, Any]] = []
        for page_num, image in pages:
            content.append({"type": "text", "text": f"--- Page {page_num} ---"})
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": _image_to_base64(image),
                },
            })

        response = client.messages.create(
            model=ANTHROPIC_VISION_MODEL,
            max_tokens=24000,  # raised from 16k to handle 8-page batches with dense Notes
            system=SYSTEM_PROMPT,
            tools=[EXTRACT_TOOL_SCHEMA],
            tool_choice={"type": "tool", "name": "extract_financial_items"},
            messages=[{"role": "user", "content": content}],
        )

        return self._parse_anthropic_response(response)

    # -- OpenRouter provider (OpenAI-compatible) ----------------------------------

    def _process_batch_openrouter(
        self, pages: list[tuple[int, Image.Image]]
    ) -> list[LineItem]:
        """Send a batch of page images to OpenRouter vision model. Returns parsed LineItems."""
        settings = get_settings()
        client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        # Build content: images first, then instruction
        content: list[dict[str, Any]] = []
        for page_num, image in pages:
            content.append({"type": "text", "text": f"--- Page {page_num} ---"})
            b64 = _image_to_base64(image)
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
            })
        # Add extraction instruction AFTER all images
        content.append({
            "type": "text",
            "text": "Extract all financial line items from the pages above. Respond with JSON only.",
        })

        response = client.chat.completions.create(
            model=settings.ocr_model,
            max_tokens=24000,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "extract_financial_items",
                    "strict": True,
                    "schema": EXTRACT_JSON_SCHEMA,
                },
            },
        )

        return self._parse_openrouter_response(response)

    # -- Response parsers ---------------------------------------------------------

    def _parse_anthropic_response(self, response) -> list[LineItem]:
        """Parse Anthropic tool_use response into LineItem instances."""
        tool_block = next(
            (c for c in response.content if getattr(c, "type", None) == "tool_use"),
            None,
        )

        if tool_block is None:
            logger.warning("Vision OCR: no tool_use block in Anthropic response")
            return []

        return self._parse_tool_output(tool_block.input)

    def _parse_openrouter_response(self, response) -> list[LineItem]:
        """Parse structured JSON response from OpenRouter (Gemini structured output)."""
        # Detect output truncation — if model hit max_tokens, JSON is likely incomplete
        finish_reason = response.choices[0].finish_reason
        if finish_reason == "length":
            logger.error(
                "Vision OCR: response truncated (finish_reason=length). "
                "Batch may have too many items for max_tokens. Consider reducing batch size."
            )
            # Don't return early — try to parse anyway, _parse_tool_output handles partial data

        message = response.choices[0].message

        if not message.content:
            logger.warning("Vision OCR: empty response content")
            return []

        text = message.content.strip()

        # Minimal fallback: strip markdown fences if present (rare with json_schema mode)
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*\n?", "", text)
            text = re.sub(r"\n?```\s*$", "", text)
            text = text.strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.error("Vision OCR: failed to parse response JSON: %s — content: %s", exc, text[:500])
            return []

        return self._parse_tool_output(parsed)

    def _parse_tool_output(self, tool_output: dict) -> list[LineItem]:
        """Shared parser: convert tool output dict into LineItem instances.

        Works identically for both Anthropic and OpenRouter responses
        since the tool schema is the same.
        """
        items: list[LineItem] = []
        for page_result in tool_output.get("page_results", []):
            # Skip non-financial pages
            if page_result.get("page_type") in ("auditor_report", "other_non_financial"):
                continue

            multiplier = _get_scale_multiplier(page_result.get("scale_factor", "absolute"))
            page_num = page_result.get("page_number", "?")
            raw_page_type = page_result.get("page_type", "")
            normalized_page_type = _normalize_page_type(raw_page_type)

            for entry in page_result.get("items", []):
                description = str(entry.get("description", "")).strip()
                if not description:
                    continue

                raw_amount = entry.get("amount")
                if raw_amount is None:
                    continue

                try:
                    amount = float(raw_amount) * multiplier
                except (ValueError, TypeError):
                    continue

                ambiguity = entry.get("ambiguity_question")
                if ambiguity is not None:
                    ambiguity = str(ambiguity).strip() or None

                items.append(LineItem(
                    description=description,
                    amount=amount,
                    section=str(entry.get("section", "")).strip().lower(),
                    raw_text=f"[Page {page_num}] {description}  {raw_amount}",
                    page_type=normalized_page_type,
                    ambiguity_question=ambiguity,
                ))

        return items
