# Prompt 2: Company Name Redaction — Full Implementation

**Paste this entire prompt into a fresh Claude Code terminal (Sonnet). Use subagent-driven development with 4 parallel agents.**

---

## Context

You are implementing the Company Name Redaction feature for the CMA Automation System. This auto-detects and redacts company names (and custom terms) from PDFs using PyMuPDF's true redaction — permanently removes text data, not just visual overlay. The database migration has already been run — the `documents` table now has columns: `redacted_file_path`, `redaction_terms`, `redaction_count`.

## Project Overview
- **Backend:** Python FastAPI + Supabase + ARQ (Redis task queue) at `backend/`
- **Frontend:** Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui at `frontend/`
- **Docker:** `docker compose up` runs all services
- **Tests:** `pytest` in backend, existing test patterns in `backend/tests/`
- **Auth:** Supabase JWT, dev bypass with `DISABLE_AUTH=true`

## Important Rules
- Preserve existing code patterns. Read existing files before modifying.
- All new endpoints need tests. Target 90%+ coverage for new code.
- Use existing Supabase client pattern from `backend/app/dependencies.py`.
- Frontend components use shadcn/ui from `frontend/src/components/ui/`.
- NEVER silent guessing — user must confirm detected names before redaction.
- Do NOT modify any existing tests. Only add new ones.

## Implementation Plan — Execute with 4 Parallel Subagents

### Subagent 1: Backend Service (`redaction_service.py`)

**Create** `backend/app/services/pdf/redaction_service.py`:

```python
import re
import pymupdf  # PyMuPDF — imports as 'pymupdf' in newer versions, fallback to 'fitz'
from io import BytesIO
from dataclasses import dataclass

# Indian company name detection regex
INDIAN_COMPANY_PATTERN = re.compile(
    r'([A-Z][A-Za-z\s&\.\-]+?'
    r'(?:Private\s+Limited|Pvt\.?\s*Ltd\.?'
    r'|Corporation\s+Limited|Limited|Ltd\.?|LLP))',
    re.IGNORECASE
)

@dataclass
class RedactionStats:
    pages_processed: int
    total_redactions: int
    per_term: dict[str, int]  # {term: count}
    detected_names: list[str]


def detect_company_names(pdf_bytes: bytes) -> list[str]:
    """Auto-detect company names from first page of PDF.

    Strategy 1: Large font spans (size >= 14) in top 200px of page 1
    Strategy 2: Indian company name regex on header text
    Returns deduplicated list of candidates for user confirmation.
    """
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]

    candidates = []

    # Strategy 1: Large-font text in header region
    text_dict = page.get_text("dict")
    for block in text_dict["blocks"]:
        if block["type"] == 0:  # text block
            for line in block["lines"]:
                for span in line["spans"]:
                    if span["size"] >= 14 and span["origin"][1] < 200:
                        text = span["text"].strip()
                        if text and len(text) > 3:
                            candidates.append(text)

    # Strategy 2: Regex on header clip
    header_clip = pymupdf.Rect(0, 0, page.rect.width, 200)
    header_text = page.get_text(clip=header_clip)
    regex_matches = INDIAN_COMPANY_PATTERN.findall(header_text)
    candidates.extend([m.strip() for m in regex_matches])

    doc.close()

    # Deduplicate preserving order
    seen = set()
    unique = []
    for c in candidates:
        if c.lower() not in seen and len(c) > 3:
            seen.add(c.lower())
            unique.append(c)
    return unique


def preview_redaction(pdf_bytes: bytes, terms: list[str]) -> dict[str, int]:
    """Count instances of each term across all pages. No modifications.

    Returns: {term: instance_count}
    """
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    counts = {term: 0 for term in terms}

    for page in doc:
        for term in terms:
            instances = page.search_for(term)
            counts[term] += len(instances)

    doc.close()
    return counts


def apply_redaction(pdf_bytes: bytes, terms: list[str]) -> tuple[bytes, RedactionStats]:
    """Apply true redaction to PDF. Permanently removes text data.

    SECURITY:
    - White fill (1,1,1) — no OCR noise for downstream processing
    - Preserve table borders (PDF_REDACT_LINE_ART_NONE)
    - Handle scanned PDFs (PDF_REDACT_IMAGE_PIXELS blanks image pixels)
    - Full save with garbage=4 (no incremental — forensically sound)
    - Metadata scrubbed (author, title, dates, XMP)
    - Post-redaction verification: assert zero matches remain

    Returns: (redacted_pdf_bytes, stats)
    """
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    total = 0
    per_term = {term: 0 for term in terms}

    for page in doc:
        for term in terms:
            instances = page.search_for(term)
            for inst in instances:
                page.add_redact_annot(inst, fill=(1, 1, 1))  # white fill
                per_term[term] += 1
                total += 1
        # Apply ALL redactions for this page at once (performance)
        page.apply_redactions(
            images=pymupdf.PDF_REDACT_IMAGE_PIXELS,   # blanks image pixels too
            graphics=pymupdf.PDF_REDACT_LINE_ART_NONE, # preserves table borders
        )

    # Scrub metadata
    doc.set_metadata({k: "" for k in doc.metadata})
    doc.del_xml_metadata()

    # Full save — forensically sound (removes orphaned objects)
    output = BytesIO()
    doc.save(output, garbage=4, deflate=True)
    pages_processed = len(doc)
    doc.close()

    redacted_bytes = output.getvalue()

    # Post-redaction verification
    verify_doc = pymupdf.open(stream=redacted_bytes, filetype="pdf")
    for page in verify_doc:
        for term in terms:
            assert len(page.search_for(term)) == 0, f"Redaction failed: '{term}' still found"
    verify_doc.close()

    return redacted_bytes, RedactionStats(
        pages_processed=pages_processed,
        total_redactions=total,
        per_term=per_term,
        detected_names=[],  # filled by caller if auto-detect was used
    )
```

**Add** `pymupdf` to `backend/requirements.txt`.

**Note:** Check if `backend/app/services/pdf/__init__.py` exists (Feature 1 may have created it). If not, create it.

### Subagent 2: Backend Tests (`test_redaction.py`)

**Create** `backend/tests/test_redaction.py`:

You need a test PDF with known text. Create one using pymupdf in the test:

```python
import pymupdf

def create_test_pdf(company_name="ABC Industries Private Limited", pages=3):
    """Create a test PDF with known content for redaction testing."""
    doc = pymupdf.open()
    for i in range(pages):
        page = doc.new_page()
        # Header with company name (large font)
        page.insert_text((72, 50), company_name, fontsize=18)
        # Body content
        page.insert_text((72, 100), f"Financial Statement Page {i+1}", fontsize=12)
        page.insert_text((72, 130), "Revenue: Rs 45,23,456", fontsize=11)
        page.insert_text((72, 160), f"Prepared for {company_name}", fontsize=11)
    output = doc.tobytes()
    doc.close()
    return output
```

Test `detect_company_names()`:
- Detects "ABC Industries Private Limited"
- Detects "XYZ Pvt. Ltd."
- Detects "DEF Corporation Limited"
- Detects "GHI LLP"
- Returns empty list for PDF with no company names
- Does not detect short strings (< 4 chars)

Test `preview_redaction()`:
- Returns correct count per term
- Returns 0 for terms not in PDF
- Works across multiple pages

Test `apply_redaction()`:
- Redacted term not found in output text (page.get_text())
- Redacted term not found in raw bytes
- Metadata is empty after redaction
- Non-redacted text preserved (e.g., "Revenue" still present)
- Multiple terms redacted simultaneously
- Empty terms list → PDF unchanged
- Page count preserved after redaction

Test security:
- Raw bytes of output do not contain redacted string
- XMP metadata removed

### Subagent 3: Backend Router + API Tests

**Read** `backend/app/routers/documents.py` first. Follow exact same patterns.

**Add** 3 new endpoints to `backend/app/routers/documents.py`:

```python
# POST /api/documents/{document_id}/detect-names
@router.post("/{document_id}/detect-names")
async def detect_document_names(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    service = Depends(get_service_client),
):
    """Auto-detect company names from PDF header."""
    # 1. Fetch document, verify PDF type, verify ownership
    # 2. Download PDF from Storage
    # 3. Call detect_company_names()
    # 4. Return {"detected_names": [...]}

# POST /api/documents/{document_id}/preview-redaction
@router.post("/{document_id}/preview-redaction")
async def preview_document_redaction(
    document_id: str,
    body: RedactionPreviewRequest,  # {terms: list[str]}
    current_user: dict = Depends(get_current_user),
    service = Depends(get_service_client),
):
    """Preview redaction — count instances without modifying."""
    # 1. Fetch document, verify PDF, verify ownership
    # 2. Download PDF from Storage
    # 3. Call preview_redaction(pdf_bytes, body.terms)
    # 4. Return {"term_counts": {term: count}, "total": N}

# POST /api/documents/{document_id}/apply-redaction
@router.post("/{document_id}/apply-redaction")
async def apply_document_redaction(
    document_id: str,
    body: RedactionApplyRequest,  # {terms: list[str]}
    current_user: dict = Depends(get_current_user),
    service = Depends(get_service_client),
):
    """Apply true redaction to PDF. Creates redacted copy, preserves original."""
    # 1. Fetch document, verify PDF, verify ownership
    # 2. Download PDF from Storage (use filtered_file_path if exists, else file_path)
    # 3. Call apply_redaction(pdf_bytes, body.terms)
    # 4. Upload redacted PDF to Storage at "{path}_redacted.pdf"
    # 5. Update document: redacted_file_path, redaction_terms, redaction_count
    # 6. Return {redacted_file_path, redaction_count, per_term_counts}
```

**Add** Pydantic schemas to `backend/app/models/schemas.py`:
```python
class RedactionPreviewRequest(BaseModel):
    terms: list[str]

class RedactionPreviewResponse(BaseModel):
    document_id: str
    term_counts: dict[str, int]
    total_instances: int

class RedactionApplyRequest(BaseModel):
    terms: list[str]

class RedactionApplyResponse(BaseModel):
    document_id: str
    redacted_file_path: str
    redaction_count: int
    per_term_counts: dict[str, int]

class DetectNamesResponse(BaseModel):
    document_id: str
    detected_names: list[str]
```

**Modify** `backend/app/workers/extraction_tasks.py`:
- After determining which file to download, add priority chain:
  - If `document["redacted_file_path"]` → use redacted
  - Else if `document["filtered_file_path"]` → use filtered
  - Else → use original `file_path`
- This ensures redaction is applied before OCR

**Create** `backend/tests/test_redaction_api.py`:
- POST detect-names for PDF → 200 with names
- POST detect-names for xlsx → 400
- POST preview-redaction → 200 with counts
- POST apply-redaction → 200, creates redacted file, updates DB
- POST apply-redaction with empty terms → 400
- Extraction task uses redacted PDF when available

### Subagent 4: Frontend

**Read** these files first:
- `frontend/src/components/documents/DocumentList.tsx` or wherever documents are shown
- `frontend/src/components/ui/dialog.tsx` — shadcn Dialog component
- `frontend/src/lib/api.ts` — API client pattern
- `frontend/src/types/index.ts` — TypeScript types

**Update** `frontend/src/types/index.ts`:
- Add to Document type: `redacted_file_path?: string`, `redaction_terms?: string[]`, `redaction_count?: number`

**Create** `frontend/src/components/documents/RedactionModal.tsx`:

```tsx
// RedactionModal — 3-step flow inside a Dialog
// Props: documentId, isOpen, onClose, onRedactionComplete

// State machine: "detecting" → "previewing" → "applying" → "done"

// Step 1: Auto-detect
// - On open, call POST /api/documents/{id}/detect-names
// - Show detected names as checkboxes (pre-checked)
// - Textarea for custom terms (comma or newline separated)
// - Button: "Preview Redaction"

// Step 2: Preview
// - Call POST /api/documents/{id}/preview-redaction with selected terms
// - Show table: term | instances found
// - Total: "Found 47 instances across the document"
// - Button: "Apply Redaction" (with confirmation)

// Step 3: Apply
// - Call POST /api/documents/{id}/apply-redaction
// - Show loading spinner
// - On success: show summary, toast notification
// - Close modal, refresh document list

// UI Components used:
// Dialog, DialogContent, DialogHeader, DialogTitle (shadcn)
// Checkbox, Input/Textarea, Button, Badge
// Loading spinner (Loader2 from lucide-react)
```

**Modify** wherever documents are listed:
- Add "Redact" button (Shield icon from lucide-react) on PDF documents
- Show "Redacted" badge (green) on documents where `redaction_count > 0`
- "Redact" button opens `<RedactionModal>`

## After All Subagents Complete

1. Run `docker compose build backend` to install pymupdf
2. Run `docker compose exec backend pytest backend/tests/test_redaction.py backend/tests/test_redaction_api.py -v`
3. Verify frontend RedactionModal renders and flows through 3 steps
4. Test end-to-end: upload PDF → detect names → preview → apply → verify redacted PDF

## Definition of Done
- [ ] `redaction_service.py` with detect, preview, apply functions
- [ ] pymupdf added to requirements.txt
- [ ] 3 new endpoints in documents router
- [ ] Pydantic request/response schemas added
- [ ] extraction_tasks.py priority chain (redacted > filtered > original)
- [ ] Post-redaction verification (assert zero matches)
- [ ] Metadata scrub (author, title, XMP)
- [ ] 15+ unit tests passing
- [ ] 5+ API tests passing
- [ ] Frontend RedactionModal with 3-step flow
- [ ] Redact button + Redacted badge on document list
- [ ] TypeScript types updated
