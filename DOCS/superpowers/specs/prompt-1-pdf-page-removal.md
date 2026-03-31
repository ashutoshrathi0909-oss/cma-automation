# Prompt 1: PDF Page Removal — Full Implementation

**Paste this entire prompt into a fresh Claude Code terminal (Sonnet). Use subagent-driven development with 4 parallel agents.**

---

## Context

You are implementing the PDF Page Removal feature for the CMA Automation System. This lets CAs select which PDF pages to send to OCR, saving API cost (Rs 2.30/page). The database migration has already been run — the `documents` table now has columns: `filtered_file_path`, `removed_pages`, `original_page_count`.

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
- Follow existing router patterns (see `backend/app/routers/documents.py`).
- Do NOT modify any existing tests. Only add new ones.

## Implementation Plan — Execute with 4 Parallel Subagents

### Subagent 1: Backend Service (`page_manager.py`)

**Create** `backend/app/services/pdf/__init__.py` (empty)

**Create** `backend/app/services/pdf/page_manager.py` with these functions:

```python
import pikepdf
from io import BytesIO

def get_page_count(pdf_bytes: bytes) -> int:
    """Return total page count of a PDF."""
    with pikepdf.Pdf.open(BytesIO(pdf_bytes)) as pdf:
        return len(pdf.pages)

def parse_page_ranges(range_str: str, total_pages: int) -> list[int]:
    """Parse '1-3, 7, 10-15' into sorted list of pages to REMOVE (1-indexed).

    Handles: empty string, invalid ranges, out-of-bounds, duplicates.
    Returns only valid page numbers within [1, total_pages].
    """
    if not range_str or not range_str.strip():
        return []
    to_remove = set()
    for part in range_str.split(","):
        part = part.strip()
        if "-" in part:
            try:
                start, end = part.split("-", 1)
                s, e = int(start.strip()), int(end.strip())
                to_remove.update(range(max(1, s), min(e, total_pages) + 1))
            except ValueError:
                continue
        else:
            try:
                p = int(part.strip())
                if 1 <= p <= total_pages:
                    to_remove.add(p)
            except ValueError:
                continue
    return sorted(to_remove)

def pages_to_keep(range_str: str, total_pages: int) -> list[int]:
    """Return 1-indexed list of pages to KEEP after removing specified pages."""
    removing = set(parse_page_ranges(range_str, total_pages))
    return [p for p in range(1, total_pages + 1) if p not in removing]

def remove_pages(pdf_bytes: bytes, keep_pages: list[int]) -> bytes:
    """Create new PDF with only the specified pages (1-indexed).

    Uses pikepdf for lossless page removal with automatic dead object cleanup.
    """
    with pikepdf.Pdf.open(BytesIO(pdf_bytes)) as pdf:
        total = len(pdf.pages)
        keep_indices = sorted(set(p - 1 for p in keep_pages if 1 <= p <= total))
        to_delete = [i for i in range(total) if i not in keep_indices]
        for idx in reversed(to_delete):
            del pdf.pages[idx]
        output = BytesIO()
        pdf.save(output)
        return output.getvalue()
```

**Add** `pikepdf` to `backend/requirements.txt`.

### Subagent 2: Backend Tests (`test_page_manager.py`)

**Create** `backend/tests/test_page_manager.py`:

Test `parse_page_ranges()`:
- Empty string → `[]`
- `"1-2"` with 10 pages → `[1, 2]`
- `"1, 3, 5"` with 10 pages → `[1, 3, 5]`
- `"1-3, 7, 10-12"` with 15 pages → `[1, 2, 3, 7, 10, 11, 12]`
- `"abc, 1-2"` (invalid mixed) → `[1, 2]` (ignores invalid)
- `"0, 100"` with 10 pages → `[]` (out of range)
- `"5-3"` (reversed range) → `[]`
- `"1-1"` → `[1]` (single page range)

Test `pages_to_keep()`:
- `"1-2"` with 5 pages → `[3, 4, 5]`
- `""` with 5 pages → `[1, 2, 3, 4, 5]`

Test `remove_pages()`:
- Create a simple multi-page PDF with pikepdf for testing
- Remove pages → verify output page count
- Keep all pages → verify output equals input page count
- Keep single page → verify output has 1 page

Test `get_page_count()`:
- Returns correct count for test PDF

### Subagent 3: Backend Router + API Tests

**Read** `backend/app/routers/documents.py` first. Follow the exact same patterns.

**Add** to `backend/app/routers/documents.py` (do NOT create a new router file — these are document operations):

```python
# New endpoint: GET /api/documents/{document_id}/page-count
@router.get("/{document_id}/page-count")
async def get_document_page_count(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    service = Depends(get_service_client),
):
    """Return total page count for a PDF document."""
    # 1. Fetch document record, verify ownership
    # 2. Download PDF from Supabase Storage (file_path)
    # 3. Call get_page_count()
    # 4. Update original_page_count in DB if not set
    # 5. Return {"page_count": N}
    # Only works for PDFs — return 400 for xlsx/xls

# New endpoint: POST /api/documents/{document_id}/filter-pages
@router.post("/{document_id}/filter-pages")
async def filter_document_pages(
    document_id: str,
    body: FilterPagesRequest,  # {pages_to_remove: str}
    current_user: dict = Depends(get_current_user),
    service = Depends(get_service_client),
):
    """Remove specified pages from PDF, save filtered version for OCR."""
    # 1. Fetch document, verify PDF, verify ownership
    # 2. Download original PDF from Storage
    # 3. Get page count, validate pages_to_remove string
    # 4. Compute pages_to_keep, call remove_pages()
    # 5. Upload filtered PDF to Storage at "{path}_filtered.pdf"
    # 6. Update document: filtered_file_path, removed_pages, original_page_count
    # 7. Return {filtered_page_count, removed_pages, original_page_count}
```

**Add** Pydantic schemas to `backend/app/models/schemas.py`:
```python
class FilterPagesRequest(BaseModel):
    pages_to_remove: str  # "1-2, 7, 10-15"

class FilterPagesResponse(BaseModel):
    document_id: str
    original_page_count: int
    removed_pages: list[int]
    filtered_page_count: int

class PageCountResponse(BaseModel):
    document_id: str
    page_count: int
```

**Modify** `backend/app/workers/extraction_tasks.py`:
- In the extraction task function, after downloading the document:
- Check if `document["filtered_file_path"]` exists
- If yes, download the filtered PDF from Storage instead of the original
- This is the key integration point — everything else in OCR stays the same

**Create** `backend/tests/test_page_filter_api.py` with API tests:
- GET page-count for PDF → 200 with count
- GET page-count for xlsx → 400
- POST filter-pages with valid range → creates filtered file
- POST filter-pages with empty range → 400 or no-op
- POST filter-pages for non-PDF → 400

### Subagent 4: Frontend

**Phase 1 only** (text range input). Read existing frontend patterns first.

**Read** these files to understand patterns:
- `frontend/src/app/(app)/cma/[id]/verify/page.tsx` — the extraction verification page
- `frontend/src/components/documents/DocumentUploader.tsx` — upload flow
- `frontend/src/types/index.ts` — TypeScript types
- `frontend/src/lib/api.ts` — API client

**Update** `frontend/src/types/index.ts`:
- Add `filtered_file_path?: string`, `removed_pages?: number[]`, `original_page_count?: number` to Document type

**Modify** the extraction trigger flow (wherever "Start Extraction" button lives):
- Before the extraction button, add a collapsible section "Page Selection (Optional)"
- Show the document's page count (call GET /api/documents/{id}/page-count on mount)
- Text input: "Pages to remove (e.g., 1-2, 7, 10-15)"
- Helper text: "Remove cover pages, auditor reports, or blank pages to save processing time. Leave blank to keep all pages."
- When user enters pages and clicks "Apply", call POST /api/documents/{id}/filter-pages
- Show success: "Removed pages [1, 2]. Keeping 13 of 15 pages."
- If pages already filtered, show current state with option to reset

**Use existing shadcn/ui components**: `Input`, `Button`, `Label`, `Collapsible` (or just a div with toggle).

## After All Subagents Complete

1. Run `docker compose build backend` to install pikepdf
2. Run `docker compose exec backend pytest backend/tests/test_page_manager.py backend/tests/test_page_filter_api.py -v`
3. Verify frontend renders page selection UI
4. Test end-to-end: upload PDF → filter pages → trigger extraction → verify only kept pages were OCR'd

## Definition of Done
- [ ] `page_manager.py` service with 4 functions
- [ ] pikepdf added to requirements.txt
- [ ] 2 new endpoints in documents router (page-count, filter-pages)
- [ ] Pydantic request/response schemas added
- [ ] extraction_tasks.py uses filtered PDF when available
- [ ] 15+ unit tests passing
- [ ] 5+ API tests passing
- [ ] Frontend page selection UI with text input
- [ ] TypeScript types updated
