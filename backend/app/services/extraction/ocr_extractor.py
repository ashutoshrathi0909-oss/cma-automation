"""
ocr_extractor.py
================
Extracts financial line items from scanned (image-only) PDFs via OCR + AI.

Pipeline
--------
1. Convert PDF pages to PIL Images using pdf2image.convert_from_bytes().
2. Run surya-ocr on the images to get raw text (one string per page).
3. Send the combined OCR text to Claude Haiku, which returns a JSON array
   of {description, amount, section} objects.
4. Parse the JSON response into LineItem instances.

Notes
-----
- surya-ocr is NOT installed in the dev Docker image (heavy PyTorch deps).
  The function `run_surya_ocr()` is designed to be easily patched in tests.
- pdf2image requires poppler; if unavailable, it raises ImportError / FileNotFoundError.
  Tests mock `convert_from_bytes` directly.
- anthropic client is instantiated per-call; tests patch `anthropic.Anthropic`.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import anthropic

from app.config import get_settings
from app.services.extraction._types import ExtractionError, LineItem, parse_amount

logger = logging.getLogger(__name__)

# ── Surya-OCR wrapper ────────────────────────────────────────────────────────
# Isolated in its own function so tests can patch it without importing surya.


def run_surya_ocr(images: list) -> list[str]:
    """
    Run surya-ocr on a list of PIL Images and return one text string per image.

    Parameters
    ----------
    images : list[PIL.Image.Image]
        Page images to run OCR on.

    Returns
    -------
    list[str]
        One OCR text string per page/image.
    """
    try:
        from surya.ocr import run_ocr  # type: ignore[import]
        from surya.model.detection.model import load_model as load_det  # type: ignore[import]
        from surya.model.detection.processor import load_processor as load_det_proc  # type: ignore[import]
        from surya.model.recognition.model import load_model as load_rec  # type: ignore[import]
        from surya.model.recognition.processor import load_processor as load_rec_proc  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "surya-ocr is not installed. Install it with: pip install surya-ocr"
        ) from exc

    det_model = load_det()
    det_processor = load_det_proc()
    rec_model = load_rec()
    rec_processor = load_rec_proc()

    langs = [["en"]] * len(images)
    results = run_ocr(images, langs, det_model, det_processor, rec_model, rec_processor)

    page_texts: list[str] = []
    for page_result in results:
        lines = [line.text for line in page_result.text_lines]
        page_texts.append("\n".join(lines))

    return page_texts


# ── pdf2image wrapper ─────────────────────────────────────────────────────────
# Also isolated so tests can mock it.

def convert_from_bytes(file_content: bytes) -> list:
    """
    Convert PDF bytes to a list of PIL Images (one per page).

    Wraps pdf2image.convert_from_bytes for easy mocking in tests.
    """
    from pdf2image import convert_from_bytes as _convert  # type: ignore[import]
    return _convert(file_content)


# ── Haiku prompt ──────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = (
    "You are a financial document parser for an Indian CA firm. "
    "Given raw OCR text from a financial statement, extract all financial line items. "
    "Return a JSON array where each element has exactly these fields: "
    '{"description": string, "amount": string, "section": string}. '
    "The 'section' should be one of: income, expenses, assets, liabilities, or empty string. "
    "The 'amount' should be the numeric value as a string, with no commas. "
    "Return ONLY the JSON array, no markdown, no explanation."
)


def _build_user_message(ocr_text: str) -> str:
    return (
        f"Extract all financial line items from this OCR text:\n\n"
        f"{ocr_text}\n\n"
        f"Return a JSON array of line items."
    )


# ── OcrExtractor ─────────────────────────────────────────────────────────────


class OcrExtractor:
    """Extracts LineItems from scanned PDFs using surya-ocr + Claude Haiku."""

    async def extract(self, file_content: bytes) -> list[LineItem]:
        """
        Extract financial line items from a scanned (image-only) PDF.

        Parameters
        ----------
        file_content : bytes
            Raw PDF bytes.

        Returns
        -------
        list[LineItem]
        """
        try:
            # Step 1: Convert PDF pages to PIL Images
            images = convert_from_bytes(file_content)

            # Step 2: Run surya-ocr on the page images
            page_texts = run_surya_ocr(images)
            combined_text = "\n\n".join(page_texts)

            # Step 3: Send OCR text to Claude Haiku for structuring
            # Use asyncio.to_thread to avoid blocking the event loop with sync call
            raw_items = await asyncio.to_thread(self._call_haiku, combined_text)

            # Step 4: Parse Haiku's JSON response into LineItem instances
            return self._parse_haiku_response(raw_items)
        except ExtractionError:
            raise
        except Exception as e:
            raise ExtractionError(f"Failed to OCR-extract document: {e}") from e

    # ── Haiku integration ─────────────────────────────────────────────────────

    def _call_haiku(self, ocr_text: str) -> str:
        """Call Claude Haiku synchronously to structure OCR text into JSON."""
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is not configured")

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": _build_user_message(ocr_text)}
            ],
        )
        return response.content[0].text

    # ── Response parsing ──────────────────────────────────────────────────────

    def _parse_haiku_response(self, raw_json: str) -> list[LineItem]:
        """
        Parse a JSON array returned by Haiku into LineItem instances.

        Returns an empty list (not an exception) if the JSON is malformed,
        so callers always receive a list[LineItem].
        """
        try:
            data: list[dict[str, Any]] = json.loads(raw_json)
        except json.JSONDecodeError:
            logger.warning("OcrExtractor: Haiku returned malformed JSON: %r", raw_json[:200])
            return []

        if not isinstance(data, list):
            logger.warning("OcrExtractor: expected JSON array, got %s", type(data).__name__)
            return []

        items: list[LineItem] = []
        for entry in data:
            description = entry.get("description", "").strip()
            raw_amount = str(entry.get("amount", "")).strip()
            section = entry.get("section", "").strip().lower()

            if not description:
                continue

            amount = parse_amount(raw_amount)
            if amount is None:
                continue

            items.append(
                LineItem(
                    description=description,
                    amount=amount,
                    section=section,
                    raw_text=f"{description}  {raw_amount}",
                )
            )

        return items
