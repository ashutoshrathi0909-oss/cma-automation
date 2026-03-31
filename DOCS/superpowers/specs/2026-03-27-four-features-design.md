# Design Spec: 4 Production Features

**Date:** 2026-03-27
**Status:** Approved
**Features:** PDF Page Removal, Company Name Redaction, Roll Forward, Provisional→Audited Upgrade

---

## Feature 1: PDF Page Removal

### Purpose
Let the CA select which PDF pages to send to OCR, saving API cost (Rs 2.30/page Anthropic, Rs 0.05/page OpenRouter).

### User Flow
1. Upload PDF → stored in Supabase Storage
2. Before extraction, CA sees page selector
   - Phase 1: Text input — "Pages to remove: 1-2, 15"
   - Phase 2: Thumbnail grid (4 columns), click to toggle, shift+click for range
3. Backend creates filtered PDF via pikepdf (lossless)
4. Filtered PDF stored as `{filename}_filtered.pdf` (original preserved)
5. OCR runs on filtered PDF only

### Database Migration
```sql
ALTER TABLE documents
  ADD COLUMN filtered_file_path TEXT,
  ADD COLUMN removed_pages INTEGER[],
  ADD COLUMN original_page_count INTEGER;
```

### Backend Architecture

**New file:** `backend/app/services/pdf/page_manager.py`
```python
# Functions:
def get_page_count(pdf_bytes: bytes) -> int
def parse_page_ranges(range_str: str, total_pages: int) -> list[int]  # returns pages to REMOVE
def pages_to_keep(range_str: str, total_pages: int) -> list[int]  # inverse
def remove_pages(pdf_bytes: bytes, pages_to_keep: list[int]) -> bytes  # pikepdf
```

**New file:** `backend/app/services/pdf/__init__.py`

**New endpoints in documents router:**
- `GET /api/documents/{id}/page-count` — returns `{page_count: int}`
- `POST /api/documents/{id}/filter-pages` — body: `{pages_to_remove: "1-2, 15"}`, creates filtered PDF, updates document record

**Modify:** `backend/app/workers/extraction_tasks.py`
- If `document.filtered_file_path` exists, download and OCR that instead of original `file_path`

### Frontend Architecture

**Phase 1 — add to extraction trigger flow:**
- In the page between upload and "Start Extraction", add an `<Input>` for page ranges
- Show `original_page_count` so user knows range
- Helper text: "Remove cover pages, blank pages, etc. Leave blank to keep all."

**Phase 2 — new component:**
- `frontend/src/components/documents/PageSelector.tsx`
- Uses `react-pdf` with `next/dynamic` (SSR disabled)
- Grid of `<Thumbnail>` components with click-to-toggle overlay
- Summary: "Keeping X of Y pages"
- `npm install react-pdf` required

### Dependencies
- Backend: `pikepdf` (add to requirements.txt)
- Frontend Phase 2: `react-pdf` (add to package.json)

### Test Requirements
- Unit: `parse_page_ranges()` with edge cases (empty, invalid, out of range, overlapping)
- Unit: `remove_pages()` — verify page count of output PDF
- API: filter-pages endpoint — creates filtered file, updates DB
- Integration: extraction uses filtered PDF when available

---

## Feature 2: Company Name Redaction

### Purpose
Auto-detect and redact company names (and custom terms) from PDFs for data security. True redaction that removes text data, not just overlay.

### User Flow
1. On document detail, CA clicks "Redact Sensitive Info"
2. Modal opens:
   - Auto-detected company names shown with checkboxes (from page 1 header)
   - Text area for custom terms (director names, addresses, PAN numbers)
3. "Preview" button shows: "Found 47 instances across 15 pages"
4. "Apply Redaction" — creates redacted PDF
5. All downstream processing uses redacted version
6. Badge shows "Redacted" on processed documents

### Database Migration
```sql
ALTER TABLE documents
  ADD COLUMN redacted_file_path TEXT,
  ADD COLUMN redaction_terms TEXT[],
  ADD COLUMN redaction_count INTEGER DEFAULT 0;
```

### Backend Architecture

**New file:** `backend/app/services/pdf/redaction_service.py`
```python
# Indian company name regex pattern
INDIAN_COMPANY_PATTERN = re.compile(
    r'([A-Z][A-Za-z\s&\.\-]+?'
    r'(?:Private\s+Limited|Pvt\.?\s*Ltd\.?'
    r'|Corporation\s+Limited|Limited|Ltd\.?|LLP))',
    re.IGNORECASE
)

# Functions:
def detect_company_names(pdf_bytes: bytes) -> list[str]
    # Strategy 1: Large font spans (size >= 14) in top 200px of page 1
    # Strategy 2: Regex on header text
    # Deduplicate and return candidates

def preview_redaction(pdf_bytes: bytes, terms: list[str]) -> dict
    # Returns {term: instance_count} without modifying PDF

def apply_redaction(pdf_bytes: bytes, terms: list[str]) -> tuple[bytes, dict]
    # True redaction via PyMuPDF:
    # - add_redact_annot() with fill=(1,1,1) white
    # - apply_redactions(images=PDF_REDACT_IMAGE_PIXELS, graphics=PDF_REDACT_LINE_ART_NONE)
    # - Scrub metadata: set_metadata empty, del_xml_metadata
    # - Save with garbage=4, deflate=True
    # Returns (redacted_bytes, stats)
```

**New endpoints in documents router:**
- `POST /api/documents/{id}/detect-names` — returns `{detected_names: ["BCIPL Industries Pvt Ltd", ...]}`
- `POST /api/documents/{id}/preview-redaction` — body: `{terms: [...]}`, returns instance counts
- `POST /api/documents/{id}/apply-redaction` — body: `{terms: [...]}`, applies redaction, uploads new file

**Modify:** `backend/app/workers/extraction_tasks.py`
- Priority: use `redacted_file_path` > `filtered_file_path` > `file_path`
- If both redacted and filtered exist, use redacted (redaction should be applied to already-filtered PDF)

### Frontend Architecture

**New component:** `frontend/src/components/documents/RedactionModal.tsx`
- Modal dialog (shadcn AlertDialog or Dialog)
- Auto-detected names as checkboxes (pre-checked)
- Custom terms textarea (comma or newline separated)
- Preview button → shows stats
- Apply button → calls endpoint, shows success toast
- Loading states for each step

**Modify:** Document detail/list — add "Redact" button, "Redacted" badge

### Security Requirements
- White fill (1,1,1) — no OCR noise
- Preserve table borders (PDF_REDACT_LINE_ART_NONE)
- Handle scanned PDFs (PDF_REDACT_IMAGE_PIXELS blanks image pixels)
- Full save with garbage=4 (no incremental — forensically sound)
- Metadata scrub (author, title, dates, XMP)
- Post-redaction verification: search output for redacted terms, assert zero matches

### Dependencies
- Backend: `PyMuPDF` aka `pymupdf` (add to requirements.txt)

### Test Requirements
- Unit: `detect_company_names()` with various Indian company name formats
- Unit: `apply_redaction()` — verify term not found in output bytes
- Unit: metadata scrubbed after redaction
- API: full redaction flow endpoint tests
- Security: raw byte search confirms no trace of redacted terms

---

## Feature 3: Roll Forward

### Purpose
Create a new CMA report for the next year by reusing existing classifications for carried-forward years and only classifying the new year's data.

### Important Distinction
This is NOT the existing `rollover_service.py` (which carries forward balance sheet closing balances). This creates a new CMA report with a shifted year window. Both features coexist.

### User Flow
1. On a completed CMA report, CA clicks "Roll Forward to Next Year"
2. **Step 1 — Preview:**
   - Shows: dropping FY21 (X docs, Y classifications)
   - Shows: keeping FY22 + FY23 (reused by reference)
   - Shows: adding FY24 — lists uploaded docs or "upload needed"
3. **Step 2 — Upload/verify FY24 docs** (if needed):
   - Links to upload page with year pre-set
   - Shows extraction/verification status of FY24 docs
   - Cannot proceed until all FY24 docs are verified
4. **Step 3 — Confirm:**
   - Creates new cma_reports record
   - Redirects to new report's review page
   - FY22/FY23 show as "all approved (carried forward)"
   - FY24 items go through standard classification pipeline
5. **Generate Excel** — existing flow, zero changes needed

### Database Migration
```sql
ALTER TABLE cma_reports
  ADD COLUMN rolled_from_report_id UUID REFERENCES cma_reports(id),
  ADD COLUMN roll_forward_metadata JSONB;

CREATE INDEX idx_cma_reports_rolled_from
  ON cma_reports(rolled_from_report_id)
  WHERE rolled_from_report_id IS NOT NULL;
```

### Backend Architecture

**New file:** `backend/app/services/roll_forward_service.py`
```python
# Pure function — computes year changes
def compute_roll_forward(existing_years: list[int], max_historical: int = 3) -> dict:
    # Returns: {drop_year, keep_years, add_year, target_years}

# Preview — no writes
async def preview_roll_forward(service, source_report_id, add_year=None) -> RollForwardPreviewResponse:
    # 1. Fetch source report + its financial_years
    # 2. Compute year changes
    # 3. Partition document_ids by year → carried vs dropped
    # 4. Count carried classifications
    # 5. Check if new year docs exist + are verified
    # 6. Return preview with blocking_reasons if not ready

# Confirm — creates new report
async def confirm_roll_forward(service, request, user_id) -> RollForwardConfirmResponse:
    # 1. Validate source report exists
    # 2. Validate new year docs are verified
    # 3. Build combined document_ids (carried + new)
    # 4. Create new cma_reports row with rolled_from_report_id
    # 5. Audit log
    # 6. Return new report details
```

**Key design:** No data is copied. FY22/FY23 `extracted_line_items` and `classifications` rows are shared by reference via `document_ids`. The `ExcelGenerator` already iterates doc IDs and joins to classifications — works without changes.

**New file:** `backend/app/routers/roll_forward.py`
- `POST /api/roll-forward/preview` — body: `{source_report_id, add_year?}`
- `POST /api/roll-forward/confirm` — body: `{source_report_id, add_year, new_document_ids[], title?, cma_output_unit?}`
- Register in `main.py`

**New schemas in `schemas.py`:**
- `RollForwardPreviewRequest`, `RollForwardPreviewResponse`
- `RollForwardConfirmRequest`, `RollForwardConfirmResponse`

### Frontend Architecture

**New page:** `frontend/src/app/(app)/cma/[id]/roll-forward/page.tsx`
- 3-step wizard (similar pattern to existing RolloverWizard)
- Step 1: Preview (shows dropped/kept/added years with doc counts)
- Step 2: Upload/verify status (links to upload page, shows doc statuses)
- Step 3: Confirm + redirect to new report

**Modify:** CMA report detail page — add "Roll Forward" button (visible when status="complete")

### What Does NOT Change
- `excel_generator.py` — dynamic year mapping already works
- `year_columns.py` — `build_year_map()` already handles any year set
- `classification/pipeline.py` — FY24 items go through standard flow
- `rollover_service.py` — different feature, coexists

### Test Requirements
- Unit: `compute_roll_forward()` with various year sets (2 years, 3 years, gaps)
- Unit: preview returns correct partitioning of documents
- API: preview endpoint returns blocking_reasons when docs not ready
- API: confirm creates new report with correct document_ids
- API: confirm rejects if new year docs not verified
- Integration: generated Excel has correct years in correct columns

---

## Feature 4: Provisional → Audited Swap (Upgrade)

### Purpose
Upgrade the existing `conversion_service.py` with a better diff algorithm, selective reclassification, and production-quality UI.

### Bugs Fixed
1. `_fetch_line_items()` selects `description` but DB column is `source_text` — diff matches on null
2. Amount changes unnecessarily flagged as `is_doubt=True` — creates pointless CA work

### User Flow
1. On a CMA report with provisional documents, CA clicks "Update to Audited"
2. **Step 1 — Select:** Choose which document to swap (e.g., "P&L FY2023 Provisional")
3. **Step 2 — Upload audited version** (if not already uploaded)
4. **Step 3 — Diff preview:**
   - Summary bar: "45 unchanged | 12 amounts updated | 3 descriptions changed | 2 new | 1 removed"
   - Color-coded table (green/yellow/red/blue/gray)
   - Unchanged hidden by default, toggle to show all
   - Amount diff shows old (strikethrough) → new (bold) with % delta
5. **Step 4 — Confirm:**
   - Applies changes selectively
   - Only new items + significantly-changed descriptions go through classification
   - Amount-only changes just update the number
   - Summary audit log recorded

### Database Migration
```sql
ALTER TABLE documents
  ADD COLUMN version_number INTEGER NOT NULL DEFAULT 1,
  ADD COLUMN parent_document_id UUID REFERENCES documents(id),
  ADD COLUMN superseded_at TIMESTAMPTZ,
  ADD COLUMN superseded_by UUID REFERENCES documents(id);

CREATE TABLE conversion_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cma_report_id UUID NOT NULL REFERENCES cma_reports(id),
  provisional_doc_id UUID NOT NULL REFERENCES documents(id),
  audited_doc_id UUID NOT NULL REFERENCES documents(id),
  diff_summary JSONB NOT NULL,
  diff_details JSONB NOT NULL,
  performed_by UUID NOT NULL,
  performed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Backend Architecture

**Upgrade:** `backend/app/services/conversion_service.py`

Replace `diff_line_items()` with 4-pass algorithm:
```python
class DiffCategory(str, Enum):
    UNCHANGED = "unchanged"
    AMOUNT_CHANGED = "amount_changed"
    DESC_CHANGED = "desc_changed"
    ADDED = "added"
    REMOVED = "removed"

# Pass 1: Exact normalized match (O(1) dict lookup)
# Pass 2: Fuzzy match remaining (token_set_ratio >= 75)
# Pass 3: Unmatched → added/removed

# Thresholds:
FUZZY_HIGH_THRESHOLD = 90   # keep classification
FUZZY_LOW_THRESHOLD = 75    # flag for review
AMOUNT_TOLERANCE_PCT = 0.5  # 0.5% = rounding tolerance
```

Replace `confirm_conversion()` with selective apply:
```python
# UNCHANGED: no action
# AMOUNT_CHANGED: update amount only, keep classification
# DESC_CHANGED (>=90): update desc+amount, keep classification
# DESC_CHANGED (75-89): update desc+amount, flag needs_review
# ADDED: insert new line item, run through classification pipeline
# REMOVED: de-verify (soft delete), flag classification
```

Fix `_fetch_line_items()`: change `description` to `source_text` in select.

Document versioning in confirm:
```python
# 1. Supersede provisional doc (set superseded_at, superseded_by)
# 2. Mark audited doc as version 2 (parent_document_id = provisional)
# 3. Update cma_reports.document_ids (swap provisional ID for audited ID)
# 4. Apply selective changes
# 5. Record conversion_event
# 6. Audit log with rich diff summary
```

**Update schemas in `schemas.py`:**
- `ConversionDiffItem` → add `category`, `match_score`, `needs_reclassification`, both item IDs
- `ConversionDiffResponse` → 5 category arrays instead of 3
- `ConversionConfirmResponse` → include swap summary

### Frontend Architecture

**Upgrade:** `frontend/src/components/cma/ConversionDiff.tsx`
- 5-category color-coded rows:
  - Green (bg-green-50, border-green-500): unchanged
  - Yellow (bg-yellow-50, border-yellow-500): amount changed
  - Red (bg-red-50, border-red-500): description changed
  - Blue (bg-blue-50, border-blue-500): new item
  - Gray (bg-gray-100, border-gray-400): removed
- Summary bar with clickable filter badges
- Amount diff component: old (strikethrough, muted) → new (bold), % delta
- "Accept All Amount Changes" bulk action button
- Unchanged items hidden by default, "Show All" toggle

**Upgrade:** `frontend/src/app/(app)/cma/[id]/convert/page.tsx`
- Better document selector flow
- Step-by-step wizard instead of single page

### Test Requirements
- Unit: 4-pass diff with exact matches, fuzzy matches, added, removed
- Unit: amount tolerance (0.5% treated as unchanged)
- Unit: normalize_line_text integration (note prefixes stripped)
- API: preview returns 5-category diff
- API: confirm applies selective changes correctly
- API: confirm creates conversion_event record
- Integration: amount-only changes do NOT trigger reclassification
- Integration: new items go through classification pipeline
- Regression: fix source_text bug verified

---

## Shared Migration File

All 4 features share one migration:

```sql
-- Migration: 2026-03-27 Four Production Features

-- Feature 1: PDF Page Removal
ALTER TABLE documents
  ADD COLUMN IF NOT EXISTS filtered_file_path TEXT,
  ADD COLUMN IF NOT EXISTS removed_pages INTEGER[],
  ADD COLUMN IF NOT EXISTS original_page_count INTEGER;

-- Feature 2: Company Name Redaction
ALTER TABLE documents
  ADD COLUMN IF NOT EXISTS redacted_file_path TEXT,
  ADD COLUMN IF NOT EXISTS redaction_terms TEXT[],
  ADD COLUMN IF NOT EXISTS redaction_count INTEGER DEFAULT 0;

-- Feature 3: Roll Forward
ALTER TABLE cma_reports
  ADD COLUMN IF NOT EXISTS rolled_from_report_id UUID REFERENCES cma_reports(id),
  ADD COLUMN IF NOT EXISTS roll_forward_metadata JSONB;

CREATE INDEX IF NOT EXISTS idx_cma_reports_rolled_from
  ON cma_reports(rolled_from_report_id)
  WHERE rolled_from_report_id IS NOT NULL;

-- Feature 4: Provisional → Audited Upgrade
ALTER TABLE documents
  ADD COLUMN IF NOT EXISTS version_number INTEGER NOT NULL DEFAULT 1,
  ADD COLUMN IF NOT EXISTS parent_document_id UUID REFERENCES documents(id),
  ADD COLUMN IF NOT EXISTS superseded_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS superseded_by UUID REFERENCES documents(id);

CREATE TABLE IF NOT EXISTS conversion_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cma_report_id UUID NOT NULL REFERENCES cma_reports(id),
  provisional_doc_id UUID NOT NULL REFERENCES documents(id),
  audited_doc_id UUID NOT NULL REFERENCES documents(id),
  diff_summary JSONB NOT NULL,
  diff_details JSONB NOT NULL,
  performed_by UUID NOT NULL,
  performed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## Execution Plan

| Prompt | Feature | Can Parallel? | New Deps |
|--------|---------|--------------|----------|
| 1 | PDF Page Removal | Yes | pikepdf, react-pdf |
| 2 | Company Name Redaction | Yes | PyMuPDF |
| 3 | Roll Forward | Yes | None |
| 4 | Prov→Audited Upgrade | Yes | None |

All 4 are independent. Run migration first (shared), then any/all prompts in parallel terminals.

**Execution order recommendation:**
1. Run migration (one-time, in any terminal)
2. Open 4 terminals, paste one prompt each
3. Each prompt uses subagent-driven development for parallel internal execution
