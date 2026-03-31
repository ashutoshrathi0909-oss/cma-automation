# Agent 8: Chaos Monkey Report

## Summary: 8/10 edge cases handled correctly

| Test | Input | Expected | Got | HTTP | Result | Severity if Failed |
|------|-------|----------|-----|------|--------|--------------------|
| 1 Blank Excel | empty.xlsx | graceful error | Status="extracted", 0 items, no error message | 202 trigger / "extracted" | FAIL | HIGH |
| 2 Fake PDF | 9-byte text file | 400 or graceful fail | 400 "File content does not match declared type .pdf." | 400 | PASS | MEDIUM |
| 3 Special chars | Sharma & Sons (Pvt.) Ltd. | stored intact | Name stored exactly: `'Sharma & Sons (Pvt.) Ltd.'` | 201 | PASS | MEDIUM |
| 4 300-char name | A*300 | 422 or truncated | 422 "String should have at most 255 characters" | 422 | PASS | MEDIUM |
| 5 Classify before verify | unverified doc | 400/403 blocked | 403 "Document extraction has not been verified. Complete the verification step before proceeding to classification." | 403 | PASS | CRITICAL |
| 6 Excel with doubts | report 8b8d5f71 (0 doubts, already generated) | blocked or noted | 409 "Report is already generating or complete." — report GET returns 500 (Pydantic validation error on null title) | 409/500 | PARTIAL PASS | MEDIUM |
| 7 Concurrent extraction | same doc x2 in <1s | 409 or idempotent | Request 1: 202 Accepted; Request 2: 409 "Document extraction_status is 'processing'. Can only trigger from 'pending' or 'failed'." | 202 / 409 | PASS | HIGH |
| 8 Large amount | 99999999.99 | stored correctly | 200, amount returned as 99999999.99, float equality confirmed | 200 | PASS | LOW |
| 9 Year 1850 | financial_year=1850 | 422 | 400 "financial_year must be between 1990 and 2100." | 400 | PASS | LOW |
| 10 SQL injection | `'; DROP TABLE clients; --` | safe or 422 | 201 — stored as literal string, table not dropped, 8 clients still listed | 201 | PASS | CRITICAL |

---

## Detailed Findings

### Test 1 — Blank Excel Upload
- Empty .xlsx uploaded successfully (201), extraction triggered (202), extraction completed with status="extracted" and 0 items extracted.
- **Problem:** The system should return status="failed" with a meaningful error message like "No data found in document". Instead it silently succeeds with zero items, giving the user no feedback that their file was empty.
- The user can then proceed to verify an empty extraction, wasting time.

### Test 2 — Fake PDF
- Content-type magic byte check correctly rejects a plain-text file disguised as PDF.
- Returns 400 with clear error: `"File content does not match declared type .pdf."`

### Test 3 — Special Characters in Client Name
- Unicode `\u0026` (&), parentheses `()`, and period `.` all stored and retrieved intact.
- No HTML escaping or mangling observed.

### Test 4 — 300-char Client Name
- Schema enforces `maxLength: 255` via Pydantic.
- Returns 422 with field-level error message pointing to the `name` field.

### Test 5 — Classify Before Verification (CRITICAL gate)
- Correctly blocked with HTTP 403: "Document extraction has not been verified. Complete the verification step before proceeding to classification."
- The mandatory verification gate is enforced.

### Test 6 — Generate Excel with Unresolved Doubts
- The target report (8b8d5f71) had 0 unresolved doubts (all 162 items approved), so the doubts-blocking scenario could not be triggered directly.
- The generate endpoint returned 409 because the report was already generated — this is correct idempotency behavior.
- **Secondary issue found:** `GET /api/cma-reports/{report_id}` returns 500 Internal Server Error due to a Pydantic validation error: `CMAReportResponse` fails when `title` is `None` (null value in DB). This is a **data integrity + serialization bug**.
- Also found: `POST /api/clients/{client_id}/cma-reports` returns 500 due to a DB not-null constraint on `financial_years` column — the router doesn't populate this field from the provided `document_ids`.

### Test 7 — Concurrent Extraction
- First request got 202 (accepted, status moved to "processing").
- Second concurrent request got 409 because status was already "processing".
- Race condition protection works correctly via status-check guard.
- The chaos.pdf (minimal valid PDF with no content) ultimately failed extraction — expected, as a page-only PDF yields no financial data.

### Test 8 — Very Large Amount
- `99999999.99` stored and retrieved with full precision.
- Float comparison `item['amount'] == 99999999.99` returned True — no float precision drift observed at this scale.

### Test 9 — Year 1850
- Correctly rejected with HTTP 400: "financial_year must be between 1990 and 2100."
- Note: this returns 400 not 422 — the validation is done manually in the route rather than via Pydantic schema (the OpenAPI schema shows `financial_year` as an unconstrained integer).

### Test 10 — SQL Injection
- Injection string `Test'; DROP TABLE clients; --` stored as a literal string.
- Table was not dropped; clients table intact with 8 rows.
- Supabase PostgREST uses parameterized queries — SQL injection is fully mitigated.

---

## Unexpected Behaviours Found

1. **Blank Excel silently "succeeds"** — empty file extracts as "extracted" with 0 items instead of "failed" with an error. User gets no warning.
2. **GET /api/cma-reports/{report_id} returns 500** — Pydantic validation fails when `title` is None. The `CMAReportResponse` model does not allow nullable `title` but the DB allows it (null constraint only caught at insert for certain paths).
3. **POST /api/clients/{client_id}/cma-reports returns 500** — DB not-null constraint on `financial_years` column is not populated by the router when creating a report from `document_ids` alone. This breaks CMA report creation for single-year documents.
4. **Year validation returns 400 not 422** — inconsistent with other validation errors (e.g., long name returns 422). Minor but inconsistent API contract.

---

## Issues by Severity

### CRITICAL
- None that are unhandled. Test 5 (classify before verify) is correctly blocked. Test 10 (SQL injection) is safe.

### HIGH
- **Test 1:** Blank Excel extraction silently succeeds with 0 items — no "failed" status, no error message. Users cannot distinguish between "empty document" and "document with no matched items". Should fail with a clear message.

### MEDIUM
- **Test 6 (secondary):** `GET /api/cma-reports/{report_id}` returns 500 when the report's `title` field is null in the DB. This means existing reports may be unreadable via the API. Pydantic model needs to allow `Optional[str]` for `title`, or the DB constraint must be enforced on insert.
- **Test 6 (tertiary):** `POST /api/clients/{client_id}/cma-reports` returns 500 — `financial_years` is not being set by the router, causing a DB not-null constraint violation. CMA report creation is broken.

### LOW
- **Test 9:** `financial_year` validation returns HTTP 400 instead of 422 — inconsistent with Pydantic-driven validation errors elsewhere in the API.
- The OpenAPI schema for `financial_year` does not declare `minimum`/`maximum` constraints, so API clients cannot discover the 1990–2100 rule from the schema alone.
