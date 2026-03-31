# Prompt 4: Provisional → Audited Swap Upgrade — Full Implementation

**Paste this entire prompt into a fresh Claude Code terminal (Sonnet). Use subagent-driven development with 4 parallel agents.**

---

## Context

You are upgrading the existing Provisional → Audited conversion feature in the CMA Automation System. The current `conversion_service.py` has two bugs and needs a more sophisticated diff algorithm with selective reclassification. The database migration has already been run — `documents` table has new columns (`version_number`, `parent_document_id`, `superseded_at`, `superseded_by`) and a new `conversion_events` table exists.

## Bugs to Fix
1. **`_fetch_line_items()`** selects `description` but the actual DB column is `source_text`. The diff is currently matching on null/empty values. Fix: change to `source_text`.
2. **Amount changes trigger `is_doubt=True`** — this is wrong. In CMA, field mapping is based on description ("Salaries & Wages" → Row 45), not amount. Amount-only changes should just update the number and keep the existing classification.

## Project Overview
- **Backend:** Python FastAPI + Supabase + ARQ (Redis task queue) at `backend/`
- **Frontend:** Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui at `frontend/`
- **Docker:** `docker compose up` runs all services
- **Tests:** `pytest` in backend, existing test patterns in `backend/tests/`
- **Auth:** Supabase JWT, dev bypass with `DISABLE_AUTH=true`

## Important Rules
- READ `backend/app/services/conversion_service.py` FIRST — understand current code before changing.
- READ `frontend/src/components/cma/ConversionDiff.tsx` FIRST — understand current UI.
- READ `frontend/src/app/(app)/cma/[id]/convert/page.tsx` FIRST — understand current page.
- Preserve the existing preview/confirm 2-step pattern.
- Use `normalize_line_text()` from `backend/app/services/extraction/_types.py` for text normalization.
- `rapidfuzz` is already in requirements.txt — no new dependencies needed.
- Do NOT modify existing tests that pass. Add new tests for new behavior.

## New Diff Algorithm — 4-Pass

Replace the existing `diff_line_items()` with this 4-pass algorithm:

```
Pass 1: Exact normalized match
  - Normalize both sides with normalize_line_text().lower().strip()
  - O(1) dict lookup
  - If found: categorize as UNCHANGED (same amount) or AMOUNT_CHANGED (different amount)
  - Amount tolerance: 0.5% difference treated as UNCHANGED (handles rounding)

Pass 2: Fuzzy match (remaining unmatched items only)
  - Use rapidfuzz.fuzz.token_set_ratio (same as existing FuzzyMatcher)
  - Score >= 90: DESC_CHANGED, keep classification (minor rewording)
  - Score 75-89: DESC_CHANGED, flag for review (significant change)
  - Score < 75: not matched, continues to Pass 3

Pass 3: Unmatched
  - Remaining provisional items → REMOVED
  - Remaining audited items → ADDED
```

### Selective Reclassification Rules

| Category | Amount Same? | Action | Reclassify? |
|----------|-------------|--------|-------------|
| UNCHANGED | Yes | No action | No |
| AMOUNT_CHANGED | No | Update amount in extracted_line_items | No |
| DESC_CHANGED (>=90) | Either | Update source_text + amount | No |
| DESC_CHANGED (75-89) | Either | Update source_text + amount, flag needs_review | Yes (flag only) |
| ADDED | N/A | Insert new line item, classify via pipeline | Yes |
| REMOVED | N/A | De-verify (is_verified=false), flag classification | No |

## Implementation Plan — Execute with 4 Parallel Subagents

### Subagent 1: Backend Service Upgrade

**Read** `backend/app/services/conversion_service.py` thoroughly first.
**Read** `backend/app/services/extraction/_types.py` for `normalize_line_text()`.

**Modify** `backend/app/services/conversion_service.py`:

1. **Add DiffCategory enum** at top of file:
```python
from enum import Enum

class DiffCategory(str, Enum):
    UNCHANGED = "unchanged"
    AMOUNT_CHANGED = "amount_changed"
    DESC_CHANGED = "desc_changed"
    ADDED = "added"
    REMOVED = "removed"
```

2. **Add constants:**
```python
FUZZY_HIGH_THRESHOLD = 90
FUZZY_LOW_THRESHOLD = 75
AMOUNT_TOLERANCE_PCT = 0.5  # 0.5% for rounding
```

3. **Fix `_fetch_line_items()`:** Change `description` to `source_text` in the select query. The DB column is `source_text`, and `LineItemResponse.from_db()` maps it to `description`.

4. **Replace `diff_line_items()`** with 4-pass `diff_financial_items()`:
```python
from dataclasses import dataclass
from app.services.extraction._types import normalize_line_text
from rapidfuzz import fuzz

@dataclass
class DiffResult:
    provisional_item_id: str | None
    audited_item_id: str | None
    provisional_desc: str | None
    audited_desc: str | None
    provisional_amount: float | None
    audited_amount: float | None
    category: DiffCategory
    match_score: float
    needs_reclassification: bool

def _normalize(text: str) -> str:
    return " ".join(normalize_line_text(text).lower().split())

def _amounts_equal(a: float | None, b: float | None) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if a == b:
        return True
    if a != 0:
        return abs(b - a) / abs(a) * 100 <= AMOUNT_TOLERANCE_PCT
    return False

def diff_financial_items(
    provisional: list[dict],
    audited: list[dict],
) -> list[DiffResult]:
    results = []

    # Index provisional by normalized description
    prov_by_norm = {}
    for item in provisional:
        norm = _normalize(item["source_text"])
        prov_by_norm[norm] = item

    aud_by_norm = {}
    for item in audited:
        norm = _normalize(item["source_text"])
        aud_by_norm[norm] = item

    # Pass 1: Exact normalized match
    matched_prov = set()
    matched_aud = set()

    for norm, p in list(prov_by_norm.items()):
        if norm in aud_by_norm:
            a = aud_by_norm[norm]
            amounts_same = _amounts_equal(p.get("amount"), a.get("amount"))
            cat = DiffCategory.UNCHANGED if amounts_same else DiffCategory.AMOUNT_CHANGED
            results.append(DiffResult(
                provisional_item_id=p["id"],
                audited_item_id=a["id"],
                provisional_desc=p["source_text"],
                audited_desc=a["source_text"],
                provisional_amount=p.get("amount"),
                audited_amount=a.get("amount"),
                category=cat,
                match_score=100.0,
                needs_reclassification=False,  # amount changes don't need reclass
            ))
            matched_prov.add(p["id"])
            matched_aud.add(a["id"])

    # Pass 2: Fuzzy match remaining
    remaining_prov = [p for p in provisional if p["id"] not in matched_prov]
    remaining_aud = [a for a in audited if a["id"] not in matched_aud]
    aud_pool = list(remaining_aud)

    for p in remaining_prov:
        if not aud_pool:
            break
        p_norm = _normalize(p["source_text"])
        best_score = 0
        best_aud = None
        best_idx = -1
        for idx, a in enumerate(aud_pool):
            a_norm = _normalize(a["source_text"])
            score = fuzz.token_set_ratio(p_norm, a_norm)
            if score > best_score:
                best_score = score
                best_aud = a
                best_idx = idx

        if best_score >= FUZZY_LOW_THRESHOLD and best_aud:
            aud_pool.pop(best_idx)
            needs_reclass = best_score < FUZZY_HIGH_THRESHOLD
            results.append(DiffResult(
                provisional_item_id=p["id"],
                audited_item_id=best_aud["id"],
                provisional_desc=p["source_text"],
                audited_desc=best_aud["source_text"],
                provisional_amount=p.get("amount"),
                audited_amount=best_aud.get("amount"),
                category=DiffCategory.DESC_CHANGED,
                match_score=best_score,
                needs_reclassification=needs_reclass,
            ))
            matched_prov.add(p["id"])
            matched_aud.add(best_aud["id"])

    # Pass 3: Unmatched
    for p in provisional:
        if p["id"] not in matched_prov:
            results.append(DiffResult(
                provisional_item_id=p["id"],
                audited_item_id=None,
                provisional_desc=p["source_text"],
                audited_desc=None,
                provisional_amount=p.get("amount"),
                audited_amount=None,
                category=DiffCategory.REMOVED,
                match_score=0,
                needs_reclassification=False,
            ))

    for a in aud_pool:
        results.append(DiffResult(
            provisional_item_id=None,
            audited_item_id=a["id"],
            provisional_desc=None,
            audited_desc=a["source_text"],
            provisional_amount=None,
            audited_amount=a.get("amount"),
            category=DiffCategory.ADDED,
            match_score=0,
            needs_reclassification=True,
        ))

    return results
```

5. **Replace `confirm_conversion()`** with selective apply:
```python
async def confirm_conversion(service, source_doc_id, target_doc_id, client_id, cma_report_id, user_id):
    # 1. Validate documents (same as before)
    # 2. Fetch line items using FIXED _fetch_line_items (source_text not description)
    # 3. Run diff_financial_items()
    # 4. Apply selectively:
    #    - UNCHANGED: skip
    #    - AMOUNT_CHANGED: update amount only
    #    - DESC_CHANGED: update source_text + amount, maybe flag
    #    - ADDED: insert new line item (into provisional doc's items)
    #    - REMOVED: set is_verified=False on provisional item
    # 5. Supersede provisional doc (superseded_at, superseded_by)
    # 6. Mark audited doc (parent_document_id, version_number=2)
    # 7. Update cma_reports.document_ids (swap provisional→audited)
    # 8. Record conversion_event
    # 9. Audit log with rich summary
    # 10. Return summary
```

6. **Update `preview_conversion()`** to return the new 5-category diff format.

### Subagent 2: Backend Tests

**Read** existing `backend/tests/test_conversion_service.py` (if it exists) to understand current tests.

**Create** `backend/tests/test_conversion_upgrade.py`:

Test `diff_financial_items()`:
- Exact match same amounts → UNCHANGED
- Exact match different amounts → AMOUNT_CHANGED
- Exact match within 0.5% tolerance → UNCHANGED (not AMOUNT_CHANGED)
- Fuzzy match score >= 90 → DESC_CHANGED, needs_reclassification=False
- Fuzzy match score 75-89 → DESC_CHANGED, needs_reclassification=True
- Fuzzy match score < 75 → not matched (becomes ADDED/REMOVED)
- Item only in provisional → REMOVED
- Item only in audited → ADDED
- Note prefix normalization: "Note 23: Wages" matches "Wages"
- Empty lists → empty results
- Single item both sides exact match → UNCHANGED

Test `_normalize()`:
- Strips note prefixes via normalize_line_text
- Lowercases
- Collapses whitespace

Test `_amounts_equal()`:
- Same amount → True
- 0.5% difference → True
- 1% difference → False
- None vs None → True
- None vs number → False
- Zero vs zero → True

Test confirm flow (mock Supabase):
- AMOUNT_CHANGED: updates amount only, classification untouched
- DESC_CHANGED (>=90): updates source_text, classification kept
- DESC_CHANGED (75-89): updates source_text, classification flagged needs_review
- ADDED: new line item inserted
- REMOVED: is_verified set to False
- Provisional doc superseded (superseded_at set)
- conversion_event record created
- Audit log created with diff summary

Test bug fix:
- `_fetch_line_items()` now selects `source_text` (regression test)

### Subagent 3: Backend Router Updates

**Read** the existing conversion router. It might be in `backend/app/routers/cma_reports.py` or a separate file. Search for the existing preview/confirm conversion endpoints.

**Update** the existing preview endpoint to return the new 5-category format.

**Update** the existing confirm endpoint to use the new selective apply.

**Add** schemas to `backend/app/models/schemas.py`:
```python
class ConversionDiffItemV2(BaseModel):
    provisional_item_id: str | None = None
    audited_item_id: str | None = None
    provisional_desc: str | None = None
    audited_desc: str | None = None
    provisional_amount: float | None = None
    audited_amount: float | None = None
    category: str  # "unchanged", "amount_changed", "desc_changed", "added", "removed"
    match_score: float
    needs_reclassification: bool

class ConversionPreviewResponseV2(BaseModel):
    source_doc_id: str
    target_doc_id: str
    unchanged: list[ConversionDiffItemV2]
    amount_changed: list[ConversionDiffItemV2]
    desc_changed: list[ConversionDiffItemV2]
    added: list[ConversionDiffItemV2]
    removed: list[ConversionDiffItemV2]
    summary: dict  # {unchanged: N, amount_changed: N, ...}

class ConversionConfirmResponseV2(BaseModel):
    unchanged: int
    amount_updated: int
    reclassified: int
    added: int
    removed: int
    message: str
```

### Subagent 4: Frontend Upgrade

**Read** these files FIRST:
- `frontend/src/components/cma/ConversionDiff.tsx` — current UI
- `frontend/src/app/(app)/cma/[id]/convert/page.tsx` — current page
- `frontend/src/types/index.ts` — TypeScript types

**Upgrade** `frontend/src/components/cma/ConversionDiff.tsx`:

Replace the current 3-category display with a 5-category production UI:

```tsx
// Color scheme for each category
const diffStyles = {
  unchanged:      { bg: "bg-green-50",  border: "border-l-4 border-green-500",  label: "Unchanged",   icon: "CheckCircle" },
  amount_changed: { bg: "bg-yellow-50", border: "border-l-4 border-yellow-500", label: "Amount Updated", icon: "ArrowUpDown" },
  desc_changed:   { bg: "bg-red-50",    border: "border-l-4 border-red-500",    label: "Description Changed", icon: "AlertTriangle" },
  added:          { bg: "bg-blue-50",   border: "border-l-4 border-blue-500",   label: "New Item",    icon: "Plus" },
  removed:        { bg: "bg-gray-100",  border: "border-l-4 border-gray-400",   label: "Removed",     icon: "Minus" },
};
```

**Add Summary Bar component:**
- Shows count badges for each category
- Clickable to filter (show only that category)
- Default: hide "unchanged" items
- "Show All" toggle

**Add AmountDiff component:**
```tsx
function AmountDiff({ provisional, audited }) {
  // If same: show amount normally
  // If different:
  //   old amount (strikethrough, text-muted-foreground, text-sm)
  //   new amount (font-semibold)
  //   % delta (text-xs, red if increase, green if decrease)
}
```

**Add bulk actions:**
- "Accept All Amount Changes" button (since amount changes are safe)
- Individual approve/reject for desc_changed items

**Upgrade** the convert page to be a proper wizard flow:
- Step 1: Select provisional document to replace
- Step 2: Select/upload audited document
- Step 3: Diff preview with 5-category table
- Step 4: Confirm + summary

**Update** TypeScript types in `frontend/src/types/index.ts`:
- Add `ConversionDiffItemV2` type matching backend schema
- Add `version_number?: number`, `parent_document_id?: string`, `superseded_at?: string` to Document type

## After All Subagents Complete

1. Run `docker compose exec backend pytest backend/tests/test_conversion_upgrade.py -v`
2. Run existing conversion tests to ensure no regressions
3. Verify frontend renders 5-category diff with color coding
4. Test: amount-only change does NOT flag as doubt
5. Test: source_text bug is fixed (diff actually matches descriptions)

## Definition of Done
- [ ] Bug fix: `source_text` column name in `_fetch_line_items()`
- [ ] Bug fix: amount changes no longer trigger is_doubt
- [ ] 4-pass diff algorithm with 5 categories
- [ ] Selective reclassification (only new + significantly changed items)
- [ ] Document versioning (superseded_at, parent_document_id)
- [ ] conversion_events table populated on confirm
- [ ] Rich audit log with diff summary
- [ ] 15+ unit tests for diff algorithm
- [ ] 5+ API tests for endpoints
- [ ] Frontend: 5-category color-coded diff table
- [ ] Frontend: summary bar with filter badges
- [ ] Frontend: AmountDiff component with % delta
- [ ] Frontend: "Accept All Amount Changes" bulk action
- [ ] Frontend: wizard flow (4 steps)
- [ ] TypeScript types updated
