# Prompt 3: Roll Forward — Full Implementation

**Paste this entire prompt into a fresh Claude Code terminal (Sonnet). Use subagent-driven development with 4 parallel agents.**

---

## Context

You are implementing the Roll Forward feature for the CMA Automation System. This allows CAs to create a new CMA report for the next year by reusing existing classifications for carried-forward years and only classifying the new year's data. The database migration has already been run — `cma_reports` table now has columns: `rolled_from_report_id`, `roll_forward_metadata`.

**IMPORTANT:** This is NOT the same as the existing `rollover_service.py` (which carries forward balance sheet closing balances as opening balances). This is a DIFFERENT feature that creates a new CMA report with a shifted year window. Both features coexist — do NOT modify rollover_service.py.

## Project Overview
- **Backend:** Python FastAPI + Supabase + ARQ (Redis task queue) at `backend/`
- **Frontend:** Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui at `frontend/`
- **Docker:** `docker compose up` runs all services
- **Tests:** `pytest` in backend, existing test patterns in `backend/tests/`
- **Auth:** Supabase JWT, dev bypass with `DISABLE_AUTH=true`
- **Key insight:** `backend/app/mappings/year_columns.py` already has `build_year_map()` which dynamically maps any set of years to Excel columns. NO changes needed to ExcelGenerator or year_columns.

## Important Rules
- Preserve existing code patterns. Read existing files before modifying.
- Read `backend/app/services/rollover_service.py` to understand the EXISTING rollover (do NOT modify it).
- Read `backend/app/routers/cma_reports.py` to understand report creation patterns.
- Read `backend/app/models/schemas.py` for existing schema patterns.
- All new endpoints need tests. Target 90%+ coverage.
- Do NOT modify any existing tests or services. Only add new ones.

## How Roll Forward Works

```
Source Report: "ABC Corp CMA FY2023"
  Years: [2021, 2022, 2023]
  document_ids: [doc_fy21_bs, doc_fy21_pl, doc_fy22_bs, doc_fy22_pl, doc_fy23_bs, doc_fy23_pl]
  status: "complete"

After Roll Forward:
New Report: "ABC Corp CMA FY2024"
  Years: [2022, 2023, 2024]
  document_ids: [doc_fy22_bs, doc_fy22_pl, doc_fy23_bs, doc_fy23_pl, doc_fy24_bs, doc_fy24_pl]
  ^^^ FY22/FY23 docs REUSED BY REFERENCE (no copy), FY24 docs are new
  rolled_from_report_id: source_report_id
  status: "draft"
```

Key: FY22/FY23 classifications are shared — not copied. The ExcelGenerator iterates document_ids and joins to classifications. When it processes the new report, it finds existing classifications for FY22/FY23 docs and new classifications for FY24 docs. The `build_year_map([2022, 2023, 2024])` automatically maps to columns B, C, D.

## Implementation Plan — Execute with 4 Parallel Subagents

### Subagent 1: Backend Service (`roll_forward_service.py`)

**Create** `backend/app/services/roll_forward_service.py`:

```python
from fastapi import HTTPException

def compute_roll_forward(existing_years: list[int], max_historical: int = 3) -> dict:
    """Pure function: compute which years to drop/keep/add.

    Args:
        existing_years: Current report years, e.g. [2021, 2022, 2023]
        max_historical: Maximum years in a CMA (default 3)

    Returns:
        {
            "drop_year": 2021 or None,
            "keep_years": [2022, 2023],
            "add_year": 2024,
            "target_years": [2022, 2023, 2024],
        }
    """
    sorted_years = sorted(existing_years)
    if len(sorted_years) < max_historical:
        return {
            "drop_year": None,
            "keep_years": sorted_years,
            "add_year": sorted_years[-1] + 1,
            "target_years": sorted_years + [sorted_years[-1] + 1],
        }
    return {
        "drop_year": sorted_years[0],
        "keep_years": sorted_years[1:],
        "add_year": sorted_years[-1] + 1,
        "target_years": sorted_years[1:] + [sorted_years[-1] + 1],
    }


async def preview_roll_forward(service, source_report_id: str, client_id: str, add_year: int | None = None):
    """Preview roll forward — no writes. Returns full preview data.

    1. Fetch source report, validate status = "complete"
    2. Compute year changes
    3. Partition source document_ids by financial_year → carried vs dropped
    4. Count carried classifications (non-doubt, from carried docs)
    5. Check if new year documents exist for this client and are verified
    6. Return preview with blocking_reasons if not ready
    """
    # Fetch source report
    result = service.table("cma_reports").select("*").eq("id", source_report_id).single().execute()
    report = result.data
    if not report:
        raise HTTPException(404, "Source report not found")
    if report["status"] != "complete":
        raise HTTPException(400, "Can only roll forward from a completed report")
    if report["client_id"] != client_id:
        raise HTTPException(403, "Report does not belong to this client")

    source_years = sorted(report.get("financial_years", []))
    if not source_years:
        raise HTTPException(400, "Source report has no financial years")

    roll = compute_roll_forward(source_years)
    if add_year is not None:
        roll["add_year"] = add_year
        roll["target_years"] = roll["keep_years"] + [add_year]

    # Fetch all source documents
    doc_ids = report.get("document_ids", [])
    docs_result = service.table("documents").select("id,file_name,financial_year,nature,document_type,extraction_status").in_("id", doc_ids).execute()
    all_docs = docs_result.data

    # Partition by year
    carried_docs = [d for d in all_docs if d["financial_year"] in roll["keep_years"]]
    dropped_docs = [d for d in all_docs if d.get("financial_year") == roll["drop_year"]]

    # Count carried classifications
    carried_doc_ids = [d["id"] for d in carried_docs]
    carried_clf_count = 0
    if carried_doc_ids:
        # Count classifications linked to carried documents via extracted_line_items
        items_result = service.table("extracted_line_items").select("id").in_("document_id", carried_doc_ids).execute()
        item_ids = [i["id"] for i in items_result.data]
        if item_ids:
            # Batch count in chunks of 100
            for i in range(0, len(item_ids), 100):
                batch = item_ids[i:i+100]
                clf_result = service.table("classifications").select("id", count="exact").in_("line_item_id", batch).eq("is_doubt", False).execute()
                carried_clf_count += clf_result.count or 0

    # Check new year docs
    new_year_docs_result = service.table("documents").select("id,file_name,financial_year,nature,document_type,extraction_status").eq("client_id", client_id).eq("financial_year", roll["add_year"]).execute()
    new_year_docs = new_year_docs_result.data
    all_verified = bool(new_year_docs) and all(d["extraction_status"] == "verified" for d in new_year_docs)

    blocking_reasons = []
    if not new_year_docs:
        blocking_reasons.append(f"No FY{roll['add_year']} documents uploaded yet")
    elif not all_verified:
        unverified = [d["file_name"] for d in new_year_docs if d["extraction_status"] != "verified"]
        blocking_reasons.append(f"Documents not yet verified: {', '.join(unverified)}")

    return {
        "source_report_id": source_report_id,
        "source_report_title": report.get("title", ""),
        "source_years": source_years,
        "drop_year": roll["drop_year"],
        "keep_years": roll["keep_years"],
        "add_year": roll["add_year"],
        "target_years": sorted(roll["target_years"]),
        "carried_documents": carried_docs,
        "dropped_documents": dropped_docs,
        "carried_classifications_count": carried_clf_count,
        "new_year_documents": new_year_docs,
        "new_year_docs_ready": all_verified,
        "can_confirm": bool(new_year_docs) and all_verified and len(blocking_reasons) == 0,
        "blocking_reasons": blocking_reasons,
    }


async def confirm_roll_forward(service, source_report_id: str, client_id: str, add_year: int, new_document_ids: list[str], title: str | None, cma_output_unit: str, user_id: str):
    """Execute roll forward — creates new CMA report.

    1. Validate source report (must be complete)
    2. Validate new documents (must be verified, correct year, correct client)
    3. Build combined document_ids (carried + new)
    4. Determine year_natures from all docs
    5. Create new cma_reports row
    6. Audit log
    7. Return new report details
    """
    # Fetch source report
    result = service.table("cma_reports").select("*").eq("id", source_report_id).single().execute()
    report = result.data
    if not report:
        raise HTTPException(404, "Source report not found")
    if report["status"] != "complete":
        raise HTTPException(400, "Can only roll forward from a completed report")
    if report["client_id"] != client_id:
        raise HTTPException(403, "Report does not belong to this client")

    source_years = sorted(report.get("financial_years", []))
    roll = compute_roll_forward(source_years)

    # Validate new documents
    new_docs_result = service.table("documents").select("*").in_("id", new_document_ids).execute()
    new_docs = new_docs_result.data
    for doc in new_docs:
        if doc["extraction_status"] != "verified":
            raise HTTPException(400, f"Document '{doc['file_name']}' is not verified")
        if doc["financial_year"] != add_year:
            raise HTTPException(400, f"Document '{doc['file_name']}' is FY{doc['financial_year']}, expected FY{add_year}")
        if doc["client_id"] != client_id:
            raise HTTPException(400, f"Document '{doc['file_name']}' belongs to a different client")

    # Build carried document IDs
    old_docs_result = service.table("documents").select("id,financial_year").in_("id", report.get("document_ids", [])).execute()
    carried_doc_ids = [d["id"] for d in old_docs_result.data if d["financial_year"] in roll["keep_years"]]

    # Combine
    all_doc_ids = carried_doc_ids + new_document_ids
    target_years = sorted(roll["keep_years"] + [add_year])

    # Determine year_natures
    all_docs_result = service.table("documents").select("nature").in_("id", all_doc_ids).execute()
    year_natures = sorted(set(d.get("nature", "").capitalize() for d in all_docs_result.data if d.get("nature")))

    # Get client name for default title
    if not title:
        client_result = service.table("clients").select("name").eq("id", client_id).single().execute()
        client_name = client_result.data.get("name", "Client") if client_result.data else "Client"
        title = f"{client_name} CMA FY{add_year}"

    # Create new report
    new_report = service.table("cma_reports").insert({
        "client_id": client_id,
        "title": title,
        "status": "draft",
        "document_ids": all_doc_ids,
        "financial_years": target_years,
        "year_natures": year_natures,
        "cma_output_unit": cma_output_unit,
        "created_by": user_id,
        "rolled_from_report_id": source_report_id,
        "roll_forward_metadata": {
            "source_years": source_years,
            "target_years": target_years,
            "dropped_year": roll["drop_year"],
            "added_year": add_year,
            "carried_document_ids": carried_doc_ids,
            "new_document_ids": new_document_ids,
        },
    }).execute()

    new_id = new_report.data[0]["id"]

    # Audit log
    service.table("cma_report_history").insert({
        "cma_report_id": new_id,
        "action": "roll_forward_created",
        "action_details": {
            "source_report_id": source_report_id,
            "source_years": source_years,
            "target_years": target_years,
            "carried_docs": len(carried_doc_ids),
            "new_docs": len(new_document_ids),
        },
        "performed_by": user_id,
    }).execute()

    return {
        "new_report_id": new_id,
        "title": title,
        "status": "draft",
        "document_ids": all_doc_ids,
        "financial_years": target_years,
        "carried_classifications_count": len(carried_doc_ids),  # approximate
        "pending_classification_docs": len(new_document_ids),
        "message": f"Report created. Classifications for {', '.join(f'FY{y}' for y in roll['keep_years'])} carried forward. FY{add_year} items need classification.",
    }
```

### Subagent 2: Backend Tests (`test_roll_forward.py`)

**Create** `backend/tests/test_roll_forward.py`:

Test `compute_roll_forward()`:
- `[2021, 2022, 2023]` → drop 2021, keep [2022, 2023], add 2024
- `[2022, 2023]` (only 2 years) → drop None, keep [2022, 2023], add 2024
- `[2023]` (1 year) → drop None, keep [2023], add 2024
- `[2020, 2022, 2023]` (non-contiguous) → drop 2020, keep [2022, 2023], add 2024
- `[2023, 2021, 2022]` (unsorted) → same as sorted

Test `preview_roll_forward()` (mock Supabase):
- Returns correct partitioning of documents
- Returns blocking_reasons when no FY24 docs
- Returns blocking_reasons when FY24 docs not verified
- Returns can_confirm=True when FY24 docs verified
- Rejects non-complete source report (400)
- Rejects non-existent report (404)

Test `confirm_roll_forward()` (mock Supabase):
- Creates new report with correct document_ids
- Sets rolled_from_report_id
- Sets roll_forward_metadata JSONB
- Rejects unverified new docs (400)
- Rejects wrong-year new docs (400)
- Creates audit log entry

### Subagent 3: Backend Router + API Tests

**Create** `backend/app/routers/roll_forward.py`:

```python
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user, get_service_client
from app.models.schemas import (
    RollForwardPreviewRequest, RollForwardPreviewResponse,
    RollForwardConfirmRequest, RollForwardConfirmResponse,
)
from app.services.roll_forward_service import preview_roll_forward, confirm_roll_forward

router = APIRouter(prefix="/api/roll-forward", tags=["roll-forward"])

@router.post("/preview")
async def preview(
    body: RollForwardPreviewRequest,
    current_user: dict = Depends(get_current_user),
    service = Depends(get_service_client),
):
    return await preview_roll_forward(
        service, body.source_report_id, body.client_id, body.add_year
    )

@router.post("/confirm")
async def confirm(
    body: RollForwardConfirmRequest,
    current_user: dict = Depends(get_current_user),
    service = Depends(get_service_client),
):
    return await confirm_roll_forward(
        service, body.source_report_id, body.client_id,
        body.add_year, body.new_document_ids,
        body.title, body.cma_output_unit, current_user["id"]
    )
```

**Register** in `backend/app/main.py`:
```python
from app.routers import roll_forward
app.include_router(roll_forward.router)
```

**Add** Pydantic schemas to `backend/app/models/schemas.py`:
```python
class RollForwardPreviewRequest(BaseModel):
    source_report_id: str
    client_id: str
    add_year: int | None = None

class RollForwardConfirmRequest(BaseModel):
    source_report_id: str
    client_id: str
    add_year: int
    new_document_ids: list[str]
    title: str | None = None
    cma_output_unit: str = "lakhs"
```

**Create** `backend/tests/test_roll_forward_api.py`:
- POST preview with valid data → 200
- POST preview with non-complete report → 400
- POST confirm with verified docs → 201 with new report
- POST confirm with unverified docs → 400
- New report has correct document_ids (carried + new)
- Audit trail entry created

### Subagent 4: Frontend

**Read** these files first:
- `frontend/src/components/cma/RolloverWizard.tsx` — existing wizard pattern to follow
- `frontend/src/app/(app)/cma/[id]/page.tsx` — report detail page (add Roll Forward button here)
- `frontend/src/lib/api.ts` — API client
- `frontend/src/types/index.ts` — TypeScript types

**Update** `frontend/src/types/index.ts`:
- Add to CMAReport type: `rolled_from_report_id?: string`, `roll_forward_metadata?: object`

**Create** `frontend/src/app/(app)/cma/[id]/roll-forward/page.tsx`:

3-step wizard page:

**Step 1 — Preview:**
- On mount, call POST /api/roll-forward/preview with report ID from params
- Show: source report title and years
- Show: "Dropping FY{X}" with document count (muted/gray)
- Show: "Keeping FY{Y}, FY{Z}" with classification counts (green checkmark)
- Show: "Adding FY{W}" section:
  - If no docs: warning message + "Upload Documents" link to `/clients/{id}/upload?year={W}`
  - If docs exist but unverified: show status per doc with warning
  - If docs ready: green checkmark
- "Next" button (disabled if can_confirm=false, show blocking_reasons)

**Step 2 — Confirm:**
- Show summary of what will happen
- Title input (pre-filled with auto-generated title)
- Output unit selector (lakhs/crores, default from source report)
- "Create Report" button

**Step 3 — Done:**
- Success message
- "Go to Report" button → navigates to `/cma/{new_report_id}/review`
- Shows: "X classifications carried forward. Y items need classification."

**Modify** CMA report detail page:
- Add "Roll Forward" button (visible when report status="complete")
- Uses `ArrowRight` icon from lucide-react
- Navigates to `/cma/{id}/roll-forward`

## After All Subagents Complete

1. Run `docker compose exec backend pytest backend/tests/test_roll_forward.py backend/tests/test_roll_forward_api.py -v`
2. Verify frontend wizard renders all 3 steps
3. Test: verify that existing ExcelGenerator correctly handles a rolled-forward report (years in correct columns)

## Definition of Done
- [ ] `roll_forward_service.py` with compute, preview, confirm functions
- [ ] `roll_forward.py` router registered in main.py
- [ ] Pydantic request/response schemas
- [ ] 10+ unit tests for compute + service logic
- [ ] 5+ API tests
- [ ] Audit trail on confirm
- [ ] Frontend 3-step wizard page
- [ ] "Roll Forward" button on report detail (complete reports only)
- [ ] TypeScript types updated
- [ ] No changes to excel_generator.py, year_columns.py, rollover_service.py
