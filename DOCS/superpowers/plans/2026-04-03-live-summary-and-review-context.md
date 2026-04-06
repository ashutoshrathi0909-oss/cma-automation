# Live Classification Summary + Review Context — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** (1) Make the classification summary update live as the ARQ worker processes documents — no page refresh needed. (2) Add financial year, document name, and CMA row context to the Review and Doubts pages so the CA knows exactly where each item came from.

**Architecture:** Feature 1 uses polling on the report overview page (every 5 seconds while classification is running, stops when idle). Feature 2 adds a server-side join through `extracted_line_items → documents` to include document context in classification responses.

**Tech Stack:** Next.js (React hooks), FastAPI, Supabase PostgREST joins

---

## Bug Fix: "Total Increases on Every Click"

**Root cause:** The "Run Classification" button triggers classification for ALL documents every time. If classification already ran, clicking it again creates DUPLICATE classifications. The backend `classify_document` in `pipeline.py:353-440` deletes existing classifications first (idempotency), but only if triggered through the worker — the direct API call may queue multiple jobs.

**Fix:** Check if classifications already exist before showing the "Run Classification" button. Already handled by `!hasClassifications` guard — but the button re-appears during polling if `summary.total` briefly shows 0 between worker runs.

---

## File Structure

| Action | Path | Responsibility |
|--------|------|---------------|
| Modify | `frontend/src/app/(app)/cma/[id]/page.tsx` | Live polling for classification summary |
| Modify | `backend/app/routers/cma_reports.py` | Add document context to classification query |
| Modify | `backend/app/models/schemas.py` | Add document fields to ClassificationResponse |
| Modify | `frontend/src/types/index.ts` | Add document fields to Classification type |
| Modify | `frontend/src/components/classification/ClassificationReview.tsx` | Show document context |

---

### Task 1: Live Classification Summary (Polling)

**Files:**
- Modify: `frontend/src/app/(app)/cma/[id]/page.tsx`

The report overview page should poll `/api/cma-reports/{id}/confidence` every 5 seconds while classification is running, and stop when all items are processed.

- [ ] **Step 1: Read current page.tsx**

Read: `frontend/src/app/(app)/cma/[id]/page.tsx`

- [ ] **Step 2: Add auto-polling useEffect**

Add a new `useEffect` after the existing data-loading one. This polls only when `classifying` is true OR when `summary.total > 0` but items are still being processed (approved + corrected + needs_review < total).

```typescript
// Live polling — updates classification summary every 5s while worker is active
useEffect(() => {
  if (!reportId || !summary) return;

  // Poll if: classification was just triggered, OR items exist but not all are settled
  const workerMayBeActive =
    classifying ||
    (summary.total > 0 &&
      summary.approved + summary.corrected + summary.needs_review < summary.total);

  if (!workerMayBeActive) return;

  const interval = setInterval(async () => {
    try {
      const s = await apiClient<ConfidenceSummary>(
        `/api/cma-reports/${reportId}/confidence`
      );
      setSummary(s);
    } catch {
      // silently ignore polling errors
    }
  }, 5000);

  return () => clearInterval(interval);
}, [reportId, summary, classifying]);
```

- [ ] **Step 3: Remove the inline polling from handleRunClassification**

The `handleRunClassification` function currently has its own `setInterval` for polling. Remove that — the useEffect above handles it. Simplify to:

```typescript
const handleRunClassification = async () => {
  if (!report) return;
  setClassifying(true);
  try {
    for (const docId of report.document_ids) {
      await apiClient(`/api/documents/${docId}/classify`, { method: "POST" });
    }
    toast.success(
      `Classification triggered for ${report.document_ids.length} documents`
    );
    // useEffect polling will handle the rest
  } catch (err) {
    toast.error(err instanceof Error ? err.message : "Classification failed");
    setClassifying(false);
  }
};
```

- [ ] **Step 4: Auto-stop classifying when worker finishes**

Add logic to detect when classification is complete and set `classifying = false`:

```typescript
// Inside the polling useEffect, after setSummary(s):
if (classifying && s.total > 0) {
  setClassifying(false); // Worker has started producing results
}
```

- [ ] **Step 5: Prevent duplicate classification triggers**

The "Run Classification" button should be disabled if classification was already triggered (even if results haven't arrived yet):

```typescript
{!hasClassifications && !classifying && (
  <Button size="sm" onClick={handleRunClassification}>
    <Play className="mr-1.5 h-4 w-4" />
    Run Classification
  </Button>
)}
{classifying && (
  <Button size="sm" disabled>
    <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
    Classifying...
  </Button>
)}
```

- [ ] **Step 6: Test**

1. Open the report page
2. Click "Run Classification"
3. Watch the summary counters update automatically every 5 seconds
4. After all items are classified, polling stops
5. Clicking "Run Classification" again should not be possible (button hidden)

- [ ] **Step 7: Commit**

```bash
git add frontend/src/app/\(app\)/cma/\[id\]/page.tsx
git commit -m "feat: live-poll classification summary while worker is active

Auto-polls /confidence every 5s. Stops when all items settle.
Prevents duplicate classification triggers."
```

---

### Task 2: Add Document Context to Backend API

**Files:**
- Modify: `backend/app/routers/cma_reports.py:340-361`
- Modify: `backend/app/models/schemas.py:195-220`

The classification query currently joins only `extracted_line_items(source_text, amount)`. Extend the join to also fetch `document_id`, and then do a second query to get document metadata (file_name, financial_year, document_type).

- [ ] **Step 1: Extend the PostgREST select to include document_id**

In `cma_reports.py`, the classifications query at line 346:

```python
# BEFORE:
.select("*, extracted_line_items(source_text, amount)")

# AFTER:
.select("*, extracted_line_items(source_text, amount, document_id, section)")
```

- [ ] **Step 2: Fetch document metadata for all document_ids**

After the classification batch query, fetch document names in one query:

```python
# After the batch loop (line 351), add:
# Fetch document metadata for context
doc_map: dict[str, dict] = {}
if document_ids:
    doc_result = (
        service.table("documents")
        .select("id, file_name, financial_year, document_type")
        .in_("id", document_ids)
        .execute()
    )
    doc_map = {d["id"]: d for d in (doc_result.data or [])}
```

- [ ] **Step 3: Add document context to flattened rows**

Update the flattening loop (line 354-359):

```python
flat_rows: list[dict] = []
for row in all_rows:
    line_item = row.pop("extracted_line_items", None) or {}
    row["line_item_description"] = line_item.get("source_text")
    row["line_item_amount"] = line_item.get("amount")
    row["line_item_section"] = line_item.get("section")
    # Document context
    doc_id = line_item.get("document_id")
    doc = doc_map.get(doc_id, {}) if doc_id else {}
    row["document_name"] = doc.get("file_name")
    row["financial_year"] = doc.get("financial_year")
    row["document_type"] = doc.get("document_type")
    flat_rows.append(row)
```

- [ ] **Step 4: Update ClassificationResponse schema**

In `schemas.py`, add new fields to `ClassificationResponse`:

```python
class ClassificationResponse(BaseModel):
    # ... existing fields ...
    line_item_description: str | None = None
    line_item_amount: float | None = None
    # New context fields
    line_item_section: str | None = None
    document_name: str | None = None
    financial_year: int | None = None
    document_type: str | None = None
```

- [ ] **Step 5: Test the API**

```bash
curl -s http://localhost:8000/api/cma-reports/<report_id>/classifications \
  -H "Authorization: Bearer <token>" | python -m json.tool | head -30
```

Verify each classification now has `document_name`, `financial_year`, `document_type`, and `line_item_section`.

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/cma_reports.py backend/app/models/schemas.py
git commit -m "feat: add document context to classification API response

Each classification now includes document_name, financial_year,
document_type, and line_item_section for CA review context."
```

---

### Task 3: Update Frontend Types and Review UI

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/components/classification/ClassificationReview.tsx`

- [ ] **Step 1: Update the Classification TypeScript type**

Find the `Classification` type in `types/index.ts` and add:

```typescript
export interface Classification {
  // ... existing fields ...
  line_item_section?: string | null;
  document_name?: string | null;
  financial_year?: number | null;
  document_type?: string | null;
}
```

- [ ] **Step 2: Read the ClassificationReview component**

Read: `frontend/src/components/classification/ClassificationReview.tsx`

Understand the current layout — where line items are rendered, what columns exist.

- [ ] **Step 3: Add context columns to the review table**

In the ClassificationReview component, add a context row under each classification item showing:
- Financial year (e.g., "FY 2024")
- Document name (e.g., "Mehta_Computers_financials_2024.xlsx")
- Section (e.g., "employee benefits expense")
- CMA Row (e.g., "Row 45 — Wages")

This should be a subtle secondary row, not cluttering the main table. Use small muted text:

```tsx
{/* Context row — document reference */}
<div className="mt-1 flex flex-wrap gap-3 text-xs text-muted-foreground">
  {c.financial_year && (
    <span>FY {c.financial_year}</span>
  )}
  {c.document_name && (
    <span>{c.document_name}</span>
  )}
  {c.line_item_section && (
    <span>Section: {c.line_item_section}</span>
  )}
  {c.cma_row && c.cma_row > 0 && (
    <span>Row {c.cma_row}</span>
  )}
</div>
```

- [ ] **Step 4: Also update the Doubts page if it has a separate component**

Check `frontend/src/app/(app)/cma/[id]/doubts/page.tsx` — if it reuses `ClassificationReview`, the context will appear automatically. If it has its own rendering, add the same context info.

- [ ] **Step 5: Test in browser**

1. Go to the Review page
2. Verify each item shows: FY, document name, section, row number
3. Go to the Doubts page
4. Verify same context appears

- [ ] **Step 6: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/components/classification/ClassificationReview.tsx
git commit -m "feat: show document context in classification review

Each item now shows financial year, document name, section,
and CMA row for CA reference during review."
```

---

### Task 4: Final Verification

- [ ] **Step 1: Full flow test**

1. Create a new client
2. Upload documents
3. Extract and verify
4. Create CMA report
5. Click "Run Classification" — watch counters update live
6. Go to Review — verify context info shows for each item
7. Go to Doubts — verify context info shows
8. Approve/correct items — verify counters update

- [ ] **Step 2: Commit all remaining changes**

```bash
git add -A
git commit -m "feat: live classification summary + document context in review

- Auto-poll summary every 5s while classification runs
- Show financial year, document name, section, row in review/doubts
- Prevent duplicate classification triggers"
```

---

## Summary

| Feature | What Changes | Where |
|---------|-------------|-------|
| **Live summary** | Poll every 5s, auto-stop | Report overview page |
| **No duplicates** | Hide button after trigger | Report overview page |
| **Document context** | Join documents table | Backend API response |
| **Review context** | Show FY, doc name, section, row | Review + Doubts UI |
