# GLM-OCR PDF Extraction — Replace pdfplumber with AI Vision

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace pdfplumber (broken on multi-column Indian financial statements) with GLM-OCR 0.9B running locally via Ollama — zero API cost, understands document layout natively.

**Architecture:** Add Ollama as a Docker Compose sidecar service running `glm-ocr`. Create a new `GlmOcrExtractor` class that sends PDF page images to the local Ollama endpoint and parses structured Markdown/JSON output into `LineItem` instances. Wire it into the extractor factory as the primary PDF handler, keeping pdfplumber as dead-code-removable fallback. Update config to control the new behavior.

**Tech Stack:** Ollama (Docker), GLM-OCR 0.9B model, Python `requests` (HTTP to Ollama), pdf2image (PDF→PNG), existing `LineItem` dataclass

---

## Bug Fix: Extraction Quality Root Causes

**Root cause 1 — Column merging (BSheet.pdf):** pdfplumber reads 2-column Balance Sheets as single rows, merging "Capital Account 58,26,789.51" with "Fixed Assets 63,019.94" into one garbled item.

**Root cause 2 — Product catalog extraction (PandL.pdf):** pdfplumber extracts every table row including individual product SKUs ("4GB DDR3 RAM", "DELL 760.44"), phone numbers, and addresses. It has no concept of "this is detail data, not a summary line."

**Root cause 3 — No layout understanding:** pdfplumber is a text/table parser. It cannot distinguish financial statement structure (sections, sub-totals, notes) from raw tabular data.

**Fix:** GLM-OCR is a vision model that sees the page as an image. It understands document layout — column boundaries, section headers, summary vs. detail — because it was trained on document understanding tasks.

---

## File Structure

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `backend/app/services/extraction/glm_ocr_extractor.py` | New extractor: sends pages to Ollama GLM-OCR, parses response |
| Modify | `backend/app/services/extraction/extractor_factory.py` | Route PDFs to GlmOcrExtractor instead of PdfExtractor |
| Modify | `backend/app/config.py` | Add `pdf_extractor` setting ("glm_ocr" or "pdfplumber") |
| Modify | `docker-compose.yml` | Add `ollama` sidecar service |
| Create | `scripts/pull-glm-ocr.sh` | One-time model pull script |
| Create | `backend/tests/test_glm_ocr_extractor.py` | Unit tests for the new extractor |
| Modify | `backend/tests/conftest.py` | Add Ollama mock fixture |

---

### Task 1: Add Ollama Service to Docker Compose

**Files:**
- Modify: `docker-compose.yml`
- Create: `scripts/pull-glm-ocr.sh`

- [ ] **Step 1: Add ollama service to docker-compose.yml**

Add after the `redis` service block:

```yaml
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          memory: 2G
```

Add to the `volumes:` section at the bottom:

```yaml
  ollama_data:
```

Add `depends_on: ollama` to the `worker` service (since the worker runs extraction).

- [ ] **Step 2: Create model pull script**

Create `scripts/pull-glm-ocr.sh`:

```bash
#!/usr/bin/env bash
# Pull the GLM-OCR model into the Ollama container.
# Run once after first `docker compose up`.
set -euo pipefail

echo "Pulling glm-ocr model into Ollama container..."
docker compose exec ollama ollama pull glm-ocr
echo "Done. Model ready at http://localhost:11434"
```

- [ ] **Step 3: Start Ollama and pull model**

```bash
docker compose up -d ollama
bash scripts/pull-glm-ocr.sh
```

Verify: `curl -s http://localhost:11434/api/tags | python -m json.tool` should list `glm-ocr`.

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml scripts/pull-glm-ocr.sh
git commit -m "infra: add Ollama sidecar for GLM-OCR local vision model

Runs GLM-OCR 0.9B locally — zero API cost PDF extraction.
Replaces pdfplumber for document layout understanding."
```

---

### Task 2: Add Config Setting for PDF Extractor Choice

**Files:**
- Modify: `backend/app/config.py`

- [ ] **Step 1: Read config.py**

Read: `backend/app/config.py`

- [ ] **Step 2: Add pdf_extractor and ollama_url settings**

In the `Settings` class, add these fields (after the existing `classifier_mode` field):

```python
    # ── PDF extraction
    pdf_extractor: str = "glm_ocr"  # "glm_ocr" or "pdfplumber"
    ollama_url: str = "http://ollama:11434"  # Ollama service URL (Docker internal)
    glm_ocr_model: str = "glm-ocr"  # Ollama model name
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/config.py
git commit -m "config: add pdf_extractor and ollama_url settings

Defaults to glm_ocr. Set PDF_EXTRACTOR=pdfplumber to fall back."
```

---

### Task 3: Create GlmOcrExtractor

**Files:**
- Create: `backend/app/services/extraction/glm_ocr_extractor.py`

This is the core new file. It:
1. Converts PDF pages to PNG images using pdf2image (already installed)
2. Sends each page image to Ollama's `/api/chat` endpoint with a financial extraction prompt
3. Parses the structured response into `LineItem` instances

- [ ] **Step 1: Create the extractor file**

Create `backend/app/services/extraction/glm_ocr_extractor.py`:

```python
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
        """Extract financial line items from a PDF using GLM-OCR vision model.

        Converts each page to an image and sends it to the local Ollama endpoint.
        """
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
                # Try parse_amount for string amounts
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
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/extraction/glm_ocr_extractor.py
git commit -m "feat: add GlmOcrExtractor for PDF extraction via local GLM-OCR

0.9B vision model running on Ollama. Understands document layout,
handles multi-column Balance Sheets and detailed P&L formats.
Zero API cost — runs entirely local."
```

---

### Task 4: Wire GlmOcrExtractor into the Factory

**Files:**
- Modify: `backend/app/services/extraction/extractor_factory.py`

- [ ] **Step 1: Read current factory**

Read: `backend/app/services/extraction/extractor_factory.py`

- [ ] **Step 2: Add import and routing logic**

Add import at the top (after the existing extractor imports):

```python
from app.services.extraction.glm_ocr_extractor import GlmOcrExtractor  # noqa: F401
```

Replace the `if file_type == "pdf":` block (lines 99-127) with:

```python
        if file_type == "pdf":
            settings = get_settings()

            if settings.pdf_extractor == "glm_ocr":
                logger.info("PDF extraction via GLM-OCR (Ollama): %s", file_path)
                items = await GlmOcrExtractor().extract(file_content)
                if not items:
                    logger.warning(
                        "GLM-OCR returned 0 items for %s — falling back to pdfplumber",
                        file_path,
                    )
                    items = await PdfExtractor().extract(file_content)
                return items

            # Legacy path: pdfplumber + OCR fallback
            scanned = is_scanned_pdf(file_content)
            if scanned:
                logger.info("PDF detected as scanned (image-only) → using OcrExtractor: %s", file_path)
                extractor = OcrExtractor()
                items = await extractor.extract(file_content)
            else:
                logger.info("PDF detected as native (has text layer) → using PdfExtractor: %s", file_path)
                items = await PdfExtractor().extract(file_content)
                if not items:
                    logger.warning(
                        "PdfExtractor returned 0 items for %s — falling back to OcrExtractor",
                        file_path,
                    )
                    items = await OcrExtractor().extract(file_content)
                    if items:
                        logger.info(
                            "OcrExtractor fallback succeeded: %d items from %s",
                            len(items), file_path,
                        )
            if not items:
                logger.warning(
                    "PDF extraction returned 0 items after all extractors (scanned=%s, path=%s).",
                    scanned, file_path,
                )
            return items
```

Add the config import at the top:

```python
from app.config import get_settings
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/extraction/extractor_factory.py
git commit -m "feat: route PDF extraction through GLM-OCR by default

Falls back to pdfplumber if GLM-OCR returns 0 items.
Set PDF_EXTRACTOR=pdfplumber to use legacy path."
```

---

### Task 5: Write Unit Tests

**Files:**
- Create: `backend/tests/test_glm_ocr_extractor.py`

- [ ] **Step 1: Create test file**

Create `backend/tests/test_glm_ocr_extractor.py`:

```python
"""Tests for GlmOcrExtractor — GLM-OCR vision-based PDF extraction."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.extraction.glm_ocr_extractor import (
    GlmOcrExtractor,
    _parse_json_response,
)


# ── JSON parsing tests ────────────────────────────────────────────────────────


class TestParseJsonResponse:
    """Test the JSON response parser handles various GLM-OCR output formats."""

    def test_clean_json_array(self):
        text = '[{"description": "Sales", "amount": 500000, "section": "income", "ambiguity_question": null}]'
        result = _parse_json_response(text)
        assert len(result) == 1
        assert result[0]["description"] == "Sales"
        assert result[0]["amount"] == 500000

    def test_json_with_markdown_fences(self):
        text = '```json\n[{"description": "Rent", "amount": 50000, "section": "expenses", "ambiguity_question": null}]\n```'
        result = _parse_json_response(text)
        assert len(result) == 1
        assert result[0]["description"] == "Rent"

    def test_json_with_items_wrapper(self):
        text = '{"items": [{"description": "Cash", "amount": 100000, "section": "assets", "ambiguity_question": null}]}'
        result = _parse_json_response(text)
        assert len(result) == 1
        assert result[0]["description"] == "Cash"

    def test_empty_response(self):
        assert _parse_json_response("") == []
        assert _parse_json_response("No financial data found.") == []

    def test_embedded_json_in_text(self):
        text = 'Here are the items:\n[{"description": "Wages", "amount": 200000, "section": "expenses", "ambiguity_question": null}]\nEnd.'
        result = _parse_json_response(text)
        assert len(result) == 1
        assert result[0]["description"] == "Wages"


# ── Extractor integration tests (mocked Ollama) ──────────────────────────────


class TestGlmOcrExtractor:
    """Test GlmOcrExtractor with mocked Ollama responses."""

    def _mock_ollama_response(self, items: list[dict]) -> MagicMock:
        """Create a mock requests.post response with given items."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "message": {"content": json.dumps(items)}
        }
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    @pytest.mark.asyncio
    @patch("app.services.extraction.glm_ocr_extractor._convert_pdf_to_images")
    @patch("app.services.extraction.glm_ocr_extractor.requests.post")
    @patch("app.services.extraction.glm_ocr_extractor.get_settings")
    async def test_basic_extraction(self, mock_settings, mock_post, mock_convert):
        """Test that a well-formed Ollama response produces correct LineItems."""
        # Mock settings
        settings = MagicMock()
        settings.glm_ocr_model = "glm-ocr"
        settings.ollama_url = "http://ollama:11434"
        mock_settings.return_value = settings

        # Mock PDF → 1 page image
        from PIL import Image
        mock_image = Image.new("RGB", (100, 100))
        mock_convert.return_value = [mock_image]

        # Mock Ollama response
        mock_post.return_value = self._mock_ollama_response([
            {"description": "Domestic Sales", "amount": 5000000, "section": "income", "ambiguity_question": None},
            {"description": "Salary & Wages", "amount": 1200000, "section": "expenses", "ambiguity_question": None},
            {"description": "Sundry Debtors", "amount": 800000, "section": "assets", "ambiguity_question": None},
        ])

        extractor = GlmOcrExtractor()
        items = await extractor.extract(b"fake-pdf-bytes")

        assert len(items) == 3
        assert items[0].description == "Domestic Sales"
        assert items[0].amount == 5000000
        assert items[0].section == "income"
        assert items[1].description == "Salary & Wages"
        assert items[2].description == "Sundry Debtors"

    @pytest.mark.asyncio
    @patch("app.services.extraction.glm_ocr_extractor._convert_pdf_to_images")
    @patch("app.services.extraction.glm_ocr_extractor.requests.post")
    @patch("app.services.extraction.glm_ocr_extractor.get_settings")
    async def test_negative_amounts(self, mock_settings, mock_post, mock_convert):
        """Test that negative amounts (parenthesized in Indian accounting) are handled."""
        settings = MagicMock()
        settings.glm_ocr_model = "glm-ocr"
        settings.ollama_url = "http://ollama:11434"
        mock_settings.return_value = settings

        from PIL import Image
        mock_convert.return_value = [Image.new("RGB", (100, 100))]

        mock_post.return_value = self._mock_ollama_response([
            {"description": "Drawings", "amount": -91999, "section": "liabilities", "ambiguity_question": None},
        ])

        items = await GlmOcrExtractor().extract(b"fake-pdf")
        assert len(items) == 1
        assert items[0].amount == -91999

    @pytest.mark.asyncio
    @patch("app.services.extraction.glm_ocr_extractor._convert_pdf_to_images")
    @patch("app.services.extraction.glm_ocr_extractor.requests.post")
    @patch("app.services.extraction.glm_ocr_extractor.get_settings")
    async def test_skips_empty_descriptions(self, mock_settings, mock_post, mock_convert):
        """Test that items with empty descriptions are filtered out."""
        settings = MagicMock()
        settings.glm_ocr_model = "glm-ocr"
        settings.ollama_url = "http://ollama:11434"
        mock_settings.return_value = settings

        from PIL import Image
        mock_convert.return_value = [Image.new("RGB", (100, 100))]

        mock_post.return_value = self._mock_ollama_response([
            {"description": "", "amount": 1000, "section": "", "ambiguity_question": None},
            {"description": "Valid Item", "amount": 2000, "section": "income", "ambiguity_question": None},
        ])

        items = await GlmOcrExtractor().extract(b"fake-pdf")
        assert len(items) == 1
        assert items[0].description == "Valid Item"

    @pytest.mark.asyncio
    @patch("app.services.extraction.glm_ocr_extractor._convert_pdf_to_images")
    @patch("app.services.extraction.glm_ocr_extractor.requests.post")
    @patch("app.services.extraction.glm_ocr_extractor.get_settings")
    async def test_ollama_failure_returns_empty(self, mock_settings, mock_post, mock_convert):
        """Test that Ollama connection failure returns empty list (not exception)."""
        settings = MagicMock()
        settings.glm_ocr_model = "glm-ocr"
        settings.ollama_url = "http://ollama:11434"
        mock_settings.return_value = settings

        from PIL import Image
        mock_convert.return_value = [Image.new("RGB", (100, 100))]

        import requests as req
        mock_post.side_effect = req.ConnectionError("Ollama not running")

        items = await GlmOcrExtractor().extract(b"fake-pdf")
        assert items == []

    @pytest.mark.asyncio
    @patch("app.services.extraction.glm_ocr_extractor._convert_pdf_to_images")
    @patch("app.services.extraction.glm_ocr_extractor.requests.post")
    @patch("app.services.extraction.glm_ocr_extractor.get_settings")
    async def test_ambiguity_detection(self, mock_settings, mock_post, mock_convert):
        """Test that ambiguity questions are passed through to LineItems."""
        settings = MagicMock()
        settings.glm_ocr_model = "glm-ocr"
        settings.ollama_url = "http://ollama:11434"
        mock_settings.return_value = settings

        from PIL import Image
        mock_convert.return_value = [Image.new("RGB", (100, 100))]

        mock_post.return_value = self._mock_ollama_response([
            {
                "description": "Employee Benefit Expenses",
                "amount": 500000,
                "section": "expenses",
                "ambiguity_question": "CMA needs Wages (Row 45) vs Salary (Row 67) — which applies?",
            },
        ])

        items = await GlmOcrExtractor().extract(b"fake-pdf")
        assert len(items) == 1
        assert items[0].ambiguity_question is not None
        assert "Row 45" in items[0].ambiguity_question
```

- [ ] **Step 2: Run tests**

```bash
docker compose exec backend pytest tests/test_glm_ocr_extractor.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_glm_ocr_extractor.py
git commit -m "test: add unit tests for GlmOcrExtractor

6 tests: basic extraction, negative amounts, empty filtering,
Ollama failure handling, ambiguity detection, JSON parsing."
```

---

### Task 6: Integration Test with Mehta Computer

**Files:** None (uses running app)

This task verifies the full pipeline end-to-end with real Mehta Computer documents.

- [ ] **Step 1: Restart worker to pick up code changes**

```bash
docker compose restart worker backend
```

- [ ] **Step 2: Re-extract PandL.pdf via API**

```bash
TOKEN=$(curl -s http://localhost:8000/api/auth/login -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@cma-automation.in","password":"CmaAdmin@2026"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Re-extract PandL.pdf (document_id from Mehta Computer)
curl -s http://localhost:8000/api/documents/60fe94da-64e5-4a94-873e-5428b0f7335b/extract \
  -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

- [ ] **Step 3: Wait for extraction, then check results**

Poll task status until complete, then check extracted items:

```bash
# Check extraction status
curl -s "http://localhost:8000/api/documents/60fe94da-64e5-4a94-873e-5428b0f7335b" \
  -H "Authorization: Bearer $TOKEN" | python -c "
import sys,json
d = json.load(sys.stdin)
print(f'Status: {d[\"extraction_status\"]}')
"
```

- [ ] **Step 4: Compare old vs new extraction quality**

```bash
# Count items and check for garbage
curl -s "http://localhost:8000/api/cma-reports/ef924f63-ddbe-40af-ae61-ddb5c7dc2282/classifications" \
  -H "Authorization: Bearer $TOKEN" | python -c "
import sys,json
clfs = json.load(sys.stdin)
pdf_items = [c for c in clfs if c.get('document_name') == 'PandL.pdf']
print(f'PandL.pdf: {len(pdf_items)} items')
for c in pdf_items[:10]:
    desc = (c.get('line_item_description') or '?')[:60]
    amt = c.get('line_item_amount', 0)
    print(f'  {desc:60s} | {amt:>15,.2f}')
"
```

**Success criteria:**
- No phone numbers or addresses extracted
- No individual product SKUs (no "4GB DDR3 RAM", "DELL", "SANDISK")
- Balance sheet columns NOT merged
- Summary financial items present (Sales, Purchases, Expenses, etc.)

- [ ] **Step 5: Also re-extract BSheet.pdf and verify columns separated**

```bash
curl -s http://localhost:8000/api/documents/2e68611d-3991-46f8-ba6b-282b9fa60cb9/extract \
  -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

- [ ] **Step 6: Commit integration test results**

```bash
git add -A
git commit -m "test: verify GLM-OCR extraction quality with Mehta Computer

PandL.pdf and BSheet.pdf re-extracted via GLM-OCR.
Confirms: no column merging, no garbage items, summary-level extraction."
```

---

## Deployment Note

**"Will it work when we deploy?"**

Yes — Ollama runs as a Docker service alongside backend/frontend/redis. The model weights are stored in a Docker volume (`ollama_data`), so they persist across restarts. On first deploy to a new server:

1. `docker compose up -d` — starts all services including Ollama
2. `bash scripts/pull-glm-ocr.sh` — pulls the 0.9B model (~600MB download, one-time)
3. After that, extraction works automatically — the worker calls Ollama at `http://ollama:11434`

**Requirements:** The server needs ~2GB RAM for Ollama + the model. No GPU required (0.9B runs fine on CPU). Your Oracle Cloud VM has enough resources.

---

## Summary

| Task | What | Files |
|------|------|-------|
| 1 | Add Ollama Docker service | `docker-compose.yml`, `scripts/pull-glm-ocr.sh` |
| 2 | Config settings | `backend/app/config.py` |
| 3 | GlmOcrExtractor class | `backend/app/services/extraction/glm_ocr_extractor.py` |
| 4 | Wire into factory | `backend/app/services/extraction/extractor_factory.py` |
| 5 | Unit tests | `backend/tests/test_glm_ocr_extractor.py` |
| 6 | Integration test with Mehta Computer | API calls, verify quality |
