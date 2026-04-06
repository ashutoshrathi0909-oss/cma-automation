# Changelog — 3 April 2026

## Summary

Two features added, one major infrastructure change, and several quality improvements across backend and frontend.

---

## Feature 1: Live Classification Summary

**What:** The CMA report overview page now auto-updates the classification summary (Total, High, Medium, Doubts, Approved, Corrected) every 5 seconds while the ARQ worker is classifying documents. Previously, the user had to manually refresh the page.

**How it works:**
- A `useEffect` polls `/api/cma-reports/{id}/confidence` every 5 seconds while `classifying` is true
- Polling stops automatically when first results arrive (`total > 0`)
- Safety timeout of 2 minutes prevents infinite polling
- The "Run Classification" button is hidden once classification is triggered (prevents duplicate runs)

**Files changed:**
- `frontend/src/app/(app)/cma/[id]/page.tsx` — Added polling useEffect, simplified handleRunClassification

---

## Feature 2: Document Context in Review & Doubts Pages

**What:** Each classification item on the Review and Doubts pages now shows which document it came from, which section, and which CMA row — so the CA reviewer knows exactly where each item originated.

**How it works:**
- Backend: The `/api/cma-reports/{id}/classifications` endpoint now joins `extracted_line_items.document_id` and `extracted_line_items.section`, then fetches document metadata (file_name, document_type) in a single query
- Frontend: A subtle context row under each line item displays document name (truncated to 30 chars), section, and CMA row number

**Fields added to ClassificationResponse:**
- `line_item_section` (string) — e.g., "expenditure", "investments"
- `document_name` (string) — e.g., "PandL.pdf", "Mehta_Computers_financials_2024.xlsx"
- `document_type` (string) — e.g., "profit_and_loss", "balance_sheet"

**Files changed:**
- `backend/app/models/schemas.py` — Added 3 fields to ClassificationResponse
- `backend/app/routers/cma_reports.py` — Extended PostgREST select, added document metadata fetch
- `frontend/src/types/index.ts` — Added 3 fields to Classification interface
- `frontend/src/components/classification/ClassificationReview.tsx` — Added context row
- `frontend/src/components/classification/DoubtReport.tsx` — Added context row

---

## Feature 3: Linked Documents Show File Names

**What:** The "Linked Documents" card on the CMA report overview page now shows actual file names with FY badges and document type labels instead of raw UUIDs.

**Example:** `PandL.pdf | FY 2024-2025 | Profit And Loss` instead of `60fe94da-64e5-4a94-873e-5428b0f7335b`

**Files changed:**
- `frontend/src/app/(app)/cma/[id]/page.tsx` — Fetches document metadata, renders names with Badge components

---

## Infrastructure: PDF Extraction — pdfplumber Replaced with Gemini 2.5 Flash

**What:** All PDF extraction now goes through Gemini 2.5 Flash (via OpenRouter) instead of pdfplumber. pdfplumber has been completely removed from the PDF extraction pipeline.

**Why:**
- pdfplumber merged columns on 2-column Balance Sheets ("Capital Account 58,26,789.51 Fixed Assets" as one garbled item)
- pdfplumber extracted phone numbers, addresses, and non-financial text as line items
- pdfplumber had no document layout understanding — couldn't distinguish summary P&L from a product catalog

**How it works now:**
1. PDF pages are converted to images via pdf2image (already installed)
2. Each page image is sent to Gemini 2.5 Flash via OpenRouter's vision API
3. Gemini returns structured JSON with line items, amounts, and sections
4. The JSON is parsed into LineItem instances for the classification pipeline

**Results (Mehta Computer BSheet.pdf):**
- Before (pdfplumber): 35 garbled items, columns merged, phone numbers extracted
- After (Gemini Flash): 42 clean items, columns properly separated, sections tagged (equity/liabilities/assets)

**Cost:** ~$0.50/month for ~750 pages via OpenRouter paid tier (data is NOT used for training)

**Configuration:**
- `OCR_MODEL=google/gemini-2.5-flash` in `.env`
- `OCR_PROVIDER=openrouter` (unchanged)
- Set `PDF_EXTRACTOR=pdfplumber` to fall back to legacy path (not recommended)

**Files changed:**
- `backend/app/config.py` — Changed default `ocr_model` to `google/gemini-2.5-flash`
- `backend/app/services/extraction/extractor_factory.py` — Simplified: all PDFs route to OcrExtractor, removed pdfplumber/GLM-OCR paths
- `backend/app/services/extraction/ocr_extractor.py` — Added Gemini JSON fallback parser (handles non-tool-call responses)
- `backend/app/services/extraction/vision_prompt.py` — Updated prompt with Indian financial statement rules
- `.env` — Updated `OCR_MODEL`

**Files deleted:**
- `backend/app/services/extraction/pdf_extractor.py` — pdfplumber extractor (249 lines removed)
- `backend/app/services/extraction/glm_ocr_extractor.py` — GLM-OCR/Ollama extractor (attempted but abandoned due to RAM constraints)
- `backend/tests/test_glm_ocr_extractor.py` — Tests for deleted extractor
- `scripts/pull-glm-ocr.sh` — Ollama model pull script

---

## Other Changes

### Vision Prompt Upgrade
- Added rules for multi-column Balance Sheet handling
- Added rules to skip addresses, phone numbers, GSTIN, signatures
- Added rules to skip balancing figures ("To Gross Profit", "To Net Profit")
- Added sub-ledger handling (extract totals only, not individual creditor/debtor names)

### Scoped Classifier — Golden Rules v2 Merge
- Merged golden rules v2 (594 CA-verified rules) with legacy rules as gap-fillers
- Exact text dedup with priority sorting (ca_override > ca_interview > legacy)

### Gemini Response Parser Fix
- Gemini Flash on OpenRouter doesn't always return tool_calls format
- Added fallback: parses message.content as JSON when tool_calls is empty
- Handles markdown fences, dict wrappers, flat arrays

### Test Cleanup
- Removed `TestIsScannedPdf` class (function no longer in factory)
- Removed `TestPdfExtractor` class (file deleted)
- Removed stale factory routing tests
- Added new `test_factory_routes_pdf_to_vision_ai` test
- Deleted stale `backend/.env` (root `.env` is source of truth)

### Frontend Fixes
- Fixed React Fragment key warning in ExtractionVerifier

---

## Known Issues / Pending

1. **Extraction prompt needs tuning** — Current prompt says "summary-level only" which skips product-level detail. For trading companies (like Mehta Computer), individual product items (keyboards, mice, RAM) ARE the financial data and should be extracted. Prompt needs to be updated to extract ALL items.

2. **Ollama service still in docker-compose.yml** — The `depends_on: ollama` was removed from worker but the service definition may still be present. Verify and clean up if needed.

3. **PandL.pdf needs re-extraction** — After prompt fix, PandL.pdf should be re-extracted to capture all 4 pages of product/trading data.

---

## Verification Done

- API verified: 26/26 checks passed (100%) on Mehta Computer data
- Browser verified: Review page shows document context correctly (Playwright screenshots saved)
- BSheet.pdf: 42 clean items with proper column separation confirmed
- PandL.pdf: 38 items extracted but needs prompt fix for complete coverage
