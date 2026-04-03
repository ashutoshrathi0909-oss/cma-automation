"""
glm_ocr_extractor.py
====================
Extracts financial line items from PDFs using GLM-OCR via local Ollama.

GLM-OCR is a 0.9B vision model that understands document layout natively.
It replaces pdfplumber for PDF extraction — handles multi-column Balance Sheets,
detailed P&L formats, and Indian financial statement conventions correctly.

Pipeline:
  1. Convert PDF pages to PNG images via pdf2image.
  2. Send each page to Ollama GLM-OCR with a financial extraction prompt.
  3. Parse Markdown/JSON response into LineItem instances.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import re

import requests
from PIL import Image

from app.config import get_settings
from app.services.extraction._types import ExtractionError, LineItem, parse_amount

logger = logging.getLogger(__name__)

# DPI for PDF → image conversion. 200 = good balance of quality vs token cost.
CONVERSION_DPI = 200

# Max image width sent to model (controls token usage).
MAX_IMAGE_WIDTH = 1600

EXTRACTION_PROMPT = """You are extracting financial data from an Indian financial statement page.

OUTPUT FORMAT: Return a JSON array of objects. Each object has these fields:
- "description": the line item name (e.g., "Salaries & Wages", "Sundry Debtors")
- "amount": the numeric amount as a number (no commas, no currency symbols). Negative for parenthesized amounts.
- "section": one of "income", "expenses", "assets", "liabilities", "equity", or ""
- "ambiguity_question": null, or a question if the line item is ambiguous for CMA classification

CRITICAL RULES:
1. Extract SUMMARY-LEVEL financial line items only. Skip individual product names, customer names, creditor names, invoice details.
2. For Balance Sheet: extract each line item from BOTH columns separately (Liabilities AND Assets). Do NOT merge columns.
3. For P&L: extract revenue items, expense categories, and profit/loss lines. Skip individual product SKUs.
4. For Notes to Accounts: extract sub-breakdowns (e.g., "Wages: 5,00,000", "Power: 2,00,000"), not just note totals.
5. Indian number format: "1,23,456" = 123456. Return amounts as plain numbers.
6. Amounts in parentheses are negative: (1,23,456) = -123456.
7. If the page header says "in Lakhs", multiply all amounts by 100000. If "in Crores", multiply by 10000000.
8. SKIP: auditor reports, directors' reports, addresses, phone numbers, registration numbers, signatures.
9. SKIP: "To Gross Profit", "To Net Profit", "By Gross Profit", "By Net Profit" — these are balancing figures, not real items.
10. For sub-ledger detail pages (list of individual creditors/debtors), extract ONLY the total line (e.g., "Sundry Creditors Total: X"), not each individual name.

Return ONLY the JSON array. No markdown fences. No explanation."""


def _convert_pdf_to_images(file_content: bytes) -> list[Image.Image]:
    """Convert PDF bytes to PIL Images (one per page)."""
    from pdf2image import convert_from_bytes
    return convert_from_bytes(file_content, dpi=CONVERSION_DPI)


def _image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64-encoded PNG string for Ollama."""
    if image.width > MAX_IMAGE_WIDTH:
        ratio = MAX_IMAGE_WIDTH / image.width
        new_height = int(image.height * ratio)
        image = image.resize((MAX_IMAGE_WIDTH, new_height), Image.LANCZOS)

    if image.mode != "RGB":
        image = image.convert("RGB")

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.standard_b64encode(buf.getvalue()).decode("utf-8")


def _parse_json_response(text: str) -> list[dict]:
    """Extract JSON array from model response, handling markdown fences."""
    text = text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
        text = text.strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict) and "items" in parsed:
            return parsed["items"]
        return []
    except json.JSONDecodeError:
        # Try to find a JSON array in the text
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        logger.warning("GLM-OCR: could not parse JSON from response: %s", text[:200])
        return []


class GlmOcrExtractor:
    """Extracts LineItems from PDFs using GLM-OCR via local Ollama."""

    async def extract(self, file_content: bytes) -> list[LineItem]:
        """Extract financial line items from a PDF using GLM-OCR vision model."""
        try:
            images = _convert_pdf_to_images(file_content)
            logger.info("GLM-OCR: converted PDF to %d page images", len(images))

            if not images:
                return []

            settings = get_settings()
            all_items: list[LineItem] = []

            for page_idx, image in enumerate(images, 1):
                page_items = await asyncio.to_thread(
                    self._extract_page, image, page_idx, settings
                )
                all_items.extend(page_items)
                logger.info(
                    "GLM-OCR: page %d/%d → %d items",
                    page_idx, len(images), len(page_items),
                )

            logger.info("GLM-OCR: extraction complete — %d total items", len(all_items))
            return all_items

        except ExtractionError:
            raise
        except Exception as exc:
            raise ExtractionError(f"GLM-OCR extraction failed: {exc}") from exc

    def _extract_page(
        self, image: Image.Image, page_num: int, settings
    ) -> list[LineItem]:
        """Send a single page image to Ollama GLM-OCR and parse the response."""
        b64_image = _image_to_base64(image)

        payload = {
            "model": settings.glm_ocr_model,
            "messages": [
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT,
                    "images": [b64_image],
                }
            ],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 4096,
            },
        }

        try:
            resp = requests.post(
                f"{settings.ollama_url}/api/chat",
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.error("GLM-OCR: Ollama request failed for page %d: %s", page_num, exc)
            return []

        result = resp.json()
        text = result.get("message", {}).get("content", "")

        if not text.strip():
            logger.warning("GLM-OCR: empty response for page %d", page_num)
            return []

        raw_items = _parse_json_response(text)
        items: list[LineItem] = []

        for entry in raw_items:
            description = str(entry.get("description", "")).strip()
            if not description:
                continue

            raw_amount = entry.get("amount")
            if raw_amount is None:
                continue

            try:
                amount = float(raw_amount)
            except (ValueError, TypeError):
                parsed = parse_amount(str(raw_amount))
                if parsed is None:
                    continue
                amount = parsed

            section = str(entry.get("section", "")).strip().lower()
            ambiguity = entry.get("ambiguity_question")
            if ambiguity is not None:
                ambiguity = str(ambiguity).strip() or None

            items.append(LineItem(
                description=description,
                amount=amount,
                section=section,
                raw_text=f"[Page {page_num}] {description}  {raw_amount}",
                ambiguity_question=ambiguity,
            ))

        return items
