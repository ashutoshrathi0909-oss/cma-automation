## E2E Test Results — Scoped Classification v2 (DeepSeek V3 + Gemini Flash)

**Date:** 2026-03-26
**Tester:** Claude (automated browser test via Playwright MCP)
**Document used:** `DOCS/Financials/FY-23/DYNAMIC Provisional FY-23.xlsx` (P&L + B&S + Notes, 154 items)
**Client:** Scoped v2 E2E Test (ID: 04c7f0e2-2f5f-4d97-a98f-c120ea9cbef7)
**CMA Report:** bce4306d-3597-4d9a-830e-1f9a4ead4355

---

### Environment
- Docker: Y — all 4 services Up (backend, frontend, redis, worker)
- Frontend: Y — http://localhost:3002 accessible (307 redirect → auth bypass working)
- Backend: Y — /health returns `{"status":"ok","db":"ok"}`

---

### Workflow Steps

| Step | Description | Result | Notes |
|------|-------------|--------|-------|
| 1 | Login | PASS | DISABLE_AUTH=true bypass works; landed on /clients as Dev Admin |
| 2 | Create client (NEW) | PASS | "Scoped v2 E2E Test" / Manufacturing created |
| 3 | Upload document | PASS | DYNAMIC Provisional FY-23.xlsx uploaded (30KB), status Pending |
| 4 | Extraction | PASS | 154 items extracted in 1.78s (P&L + B&S + Notes sheets) |
| 5 | Verification | PASS | "Verify All" clicked; all 154 items verified in one click |
| 6 | Classification | **FAIL** | Completes with status `classified` in 63.52s BUT Bug #1 NOT fixed — all AI calls fail; only learned (127) + fuzzy (4) tiers ran. 23 items failed. Zero scoped_* methods used. |
| 7 | Review UI | PARTIAL | 154 total, 131 auto-approved, 23 UNCLASSIFIED with "Classification error: APIError". No scoped_agree/scoped_debate method shown anywhere. |
| 8 | Doubt report | PARTIAL | 23 doubts exist (15% — below 20% threshold) but all reason = "Classification error: APIError". No real debate reasoning since AI never ran. |
| 9 | Approve/correct | PASS | Approve saves correctly (status→approved, Re-correct button appears). Correct action shows CMA field search dropdown, saves correction, count decrements 23→22. |
| 10 | Excel generation | PASS | Generated in 5.89s after manually resolving 22 doubts via API. UI button was blocked by doubt guard; resolved via direct API calls. |
| 11 | Excel verification | PASS | .xlsm 108KB (>10KB ✓), 16 sheets ✓, INPUT SHEET (sheet4) has 349 cells + 40 non-zero B-column values in Lakhs. ⚠️ VBA macros absent (template issue — see Non-Blocking). |

---

### Classification Details (from worker logs)

- **Classification method:** learned (127 items) + fuzzy_match (4 items) + manual/UNCLASSIFIED (23 items)
- **scoped_* methods:** NONE — zero instances of `scoped_agree`, `scoped_debate`, `scoped_single_deepseek`, or `scoped_single_gemini`
- **Models used:** NONE (DeepSeek V3 / Gemini Flash never reached — classify_sync crashes before any model call)
- **ai_haiku:** NOT seen in logs (code never reaches model dispatch — crash occurs earlier in classify_sync)
- **Items classified successfully (tier 1+2):** 131/154 (85%)
- **Items flagged as doubt (AI tier failed):** 23/154 (15%)
- **Agreement rate:** N/A (scoped classifier never ran)
- **Total classification time:** 63.52s (within minutes threshold ✓)
- **Error pattern:** `classify_sync failed: There is no current event loop in thread 'asyncio_0'.` — fired 7+ times

### Worker Log Evidence

```
05:44:44:   0.18s → 7a0de3ecb21d411faa6679608e76792c:run_classification('2091e813-abd7-431c-b427-f522154311eb')
classify_sync failed: There is no current event loop in thread 'asyncio_0'.
classify_sync failed: There is no current event loop in thread 'asyncio_0'.
[...repeated 7 times...]
05:45:47:  63.52s ← 7a0de3ecb21d411faa6679608e76792c:run_classification ● {status: classified}
```

---

### Blocking Issues

1. **[BUG #1 NOT FIXED] classify_sync event loop crash** — `classify_sync failed: There is no current event loop in thread 'asyncio_0'` fires for every item reaching the AI classification tier. The fix (using `asyncio.new_event_loop()`) is either not applied to the source or the Docker worker image was not rebuilt. **Impact: The entire scoped classification engine (DeepSeek V3 + Gemini Flash) is completely inoperative. Zero scoped_* classifications. Cannot verify Bug #5 fix (pipeline.py hardcoded method) because the code never reaches model dispatch.**

2. **[UX ISSUE] Classification not auto-triggered after CMA Report creation** — After creating a CMA report, classification does not start automatically. Requires manual call to `POST /api/documents/{doc_id}/classify`. No "Classify" button exists in the UI.

3. **[WORKFLOW BLOCKER] Excel generation blocked by UNCLASSIFIED doubts** — Items failing AI become UNCLASSIFIED doubts (is_doubt=True, cma_field=None). The `is_doubt` flag only clears via Correct (not Approve), requiring full `cma_row + broad_classification + cma_field_name` for each item. Blocks Excel until every doubt is manually corrected.

---

### Non-Blocking Issues

1. **Audit log FK constraint** — `cma_report_history` FK fails for mock user UUID (00000000-0000-0000-0000-000000000001). Audit logging silently fails for all dev-bypass operations. Non-critical for core functionality.

2. **VBA macros absent from CMA template** — Generated output.xlsm has no `xl/vbaProject.bin`. The SOURCE template `DOCS/CMA.xlsm` also lacks macros (likely stripped during a recent modification — `M DOCS/CMA.xlsm` in git status). File extension and MIME type are correct. The macro must be restored to the template file.

3. **Row offset (Bug #3)** — Appears FIXED. Data lands in expected rows in the INPUT SHEET (B6=2023 year, B9=12 months, financial values in rows 19–82+). No evidence of off-by-one errors.

---

### Excel File Verification

| Property | Expected | Actual | Status |
|----------|----------|--------|--------|
| Extension | .xlsm | .xlsm | ✓ |
| MIME type | application/vnd.ms-excel.sheet.macroenabled.12 | Same | ✓ |
| File size | > 10 KB | 108 KB | ✓ |
| Valid ZIP/OOXML | Yes | Yes | ✓ |
| VBA macros | Present | ABSENT | ✗ (template issue) |
| Sheet count | 16 | 16 | ✓ |
| INPUT SHEET (sheet4) | Has data | 349 cells, 40 B-col non-zero | ✓ |
| TL Sheet (sheet3) | Has data | 49 cells | ✓ |
| Data unit | Lakhs | Values consistent with Lakhs | ✓ |
| Row offset fix | Correct rows | Verified correct | ✓ |

---

### Summary

The pipeline infrastructure is **functionally complete end-to-end** — Steps 10 and 11 PASS with real financial data in the Excel. However, **the core scoped classification engine is completely non-functional** due to Bug #1 (event loop crash) not being fixed in the running Docker image. The system silently degrades to tier-1/tier-2 only with no AI assistance.

**Recommended immediate action:** Check `classify_sync` in `classification_tasks.py` — confirm the `asyncio.new_event_loop()` fix is in the source, then rebuild the worker Docker image (`docker compose build worker && docker compose up -d worker`).
