# Testing Workflow Research Review
*Reviewed by: Technical Architect Agent | Date: 2026-03-20*

---

## TL;DR — The 5 Things That Actually Matter

- **Use Claude + Playwright MCP directly, right now.** You already have the MCP tools running in this environment. No installation. No code. Write a plain-English test script and run it today. This is your App Testing Agent, and it costs nothing to set up.

- **The Excel Accuracy Agent is the highest-value investment in this project.** Build `excel_comparator.py` using openpyxl + xlrd. It is 100–150 lines of Python, requires no new dependencies, and gives you a cell-by-cell score against the CA's file. This is the one thing you cannot eyeball manually.

- **openpyxl `data_only=True` works for your specific setup, but only because of how your generator works.** This is not a general-purpose solution — it only works because you write floats, not formulas. The research documents this correctly. Do not deviate from this pattern.

- **The 1% tolerance is correct. The 0.50 lakh absolute fallback is necessary but may need tuning.** Financial data requires exact-ish matching. The hybrid tolerance correctly handles both large amounts (1% relative) and small amounts (0.50 lakh absolute). However, 0.50 lakh = ₹50,000, which is a wide tolerance for small amounts. Watch this in the first test run.

- **Stop writing pytest unit tests until you have a working end-to-end flow.** The research documents are technically excellent but they're solving the wrong problem first. You are a non-technical developer. Your risk is not "will my mocks cover every edge case" — your risk is "does the app actually work for a real PDF." Run the app against Dynamic Air Engineering first. Fix what breaks. Then write unit tests to lock in what you've learned.

---

## The Two-Agent Plan: Verdict

**APPROVE with one important clarification on what "two agents" actually means in practice.**

The split is right: App Testing Agent (operates the browser, tests the flow) and Excel Accuracy Agent (compares output files). These are genuinely distinct jobs with different tools, different timing, and different failure modes. One agent doing both would be unwieldy.

However, the research dodges the most important question: **how are these two agents coordinated?**

The App Testing Agent needs to download the generated Excel file and hand it to the Excel Accuracy Agent. This handoff needs a file path. The handoff needs to happen after the full pipeline completes. The research documents never address this concretely. Here is the answer: the App Agent saves the downloaded Excel to a known path (`test-results/{company}/generated_cma.xlsm`), then you run the Excel Agent as a separate script pointed at that path. These are not two agents running in parallel — they run sequentially. App Agent first, then Excel Agent reads the output. Simple. Implement it that way.

**Should it be three agents?** No. The research document for file 09 suggests a third agent for "classification validation," but for 7 companies tested one at a time, that is overkill. The Excel Accuracy Agent already catches classification failures indirectly: if the wrong items were classified into the wrong rows, the cell values in the Excel will be wrong, and the comparison will flag it. Item-level classification labels (the `dynamic_classification_labels.json` approach in file 09) require manual labelling effort that does not make sense to invest in before you have a single working test run.

---

## Section 1: Pipeline Integration Testing (Files 01–03)

### File 01: FastAPI + ARQ Pipeline Testing

**Verdict: APPROVE** for Approach 1 (direct task testing). ROAST everything else as premature.

The core recommendation — call ARQ tasks as plain async functions — is correct and is the right starting point. The actual `run_extraction()` code in `backend/app/workers/extraction_tasks.py` is straightforward: fetch document, delete old items, download file, extract, insert, update status. This is highly testable without a real database.

The mock fixture for Supabase's chained builder pattern (`.table().select().eq().single().execute()`) in file 01 is accurate and matches the actual code. The `SupabaseMockBuilder` class in file 03 is a cleaner version of the same idea.

**What the research gets right:** The observation that `ctx = {}` is safe to pass to ARQ tasks because the actual tasks in this codebase do not read from ctx is verified by looking at the real code. `run_extraction` takes `ctx: dict` but ignores it entirely.

**What the research does not warn you about:** Testing ARQ tasks as plain async functions is sufficient for verifying the logic of the task, but it does NOT test the retry behavior. ARQ's retry logic (exponential backoff, max retries) is configured in the `WorkerSettings` class and only activates when a real ARQ worker runs. If your retry configuration has a bug, the direct task tests will not catch it. This is a real gap for a pipeline that runs OCR on scanned PDFs — OCR failures are the most likely cause of retries.

**What the research recommends that you should skip:** The `SupabaseMockBuilder` class is intellectually pleasing but not worth building right now. `MagicMock()` with manual chain setup is ugly but works and you can have Claude write it for each test. The builder abstraction is something you add after you have 10+ test files and the repetition becomes painful. You have three task files. Skip the abstraction.

**The batch insert test for 501 items** is flagged in file 03 as a real production risk. This is correct. The Dynamic Air Engineering test has ~80+ OCR pages. Batch insert failure would silently truncate data. Write this test. It requires a real Supabase connection but it is a single-purpose test that you run once to verify the behavior.

### File 02: AI Pipeline Testing Patterns

**Verdict: APPROVE Layer 1 (pure mocks). ROAST VCR cassettes as impractical for this developer.**

The ground truth fixture approach for classification accuracy testing is the most valuable idea in all nine documents. Building a `GROUND_TRUTH` list of known `(source_text, expected_cma_field)` pairs and running parametrized tests against it gives you a free regression test that catches classification pipeline changes without spending a rupee. Start with 20–30 pairs from the 384-item reference mapping. Grow it after each test run.

The `block_real_api_calls_in_ci` autouse fixture is genuinely important. Without it, one accidental `pytest` run with a real API key will cost money. Add this.

**VCR cassettes: ROAST.**

This is the recommendation I have the strongest objection to. VCR cassettes record HTTP interactions to YAML files and replay them in future test runs. Conceptually clean. In practice, for a non-technical developer:

1. You must run the tests in `--record-mode=new_episodes` against the real API to generate cassettes. This means a real API call, real cost, and coordinating environment setup correctly.
2. The cassette files are hundreds of lines of YAML containing the full serialized HTTP request and response bodies. When Claude's response format changes slightly (which happens), the cassette breaks and must be re-recorded. You will spend time debugging cassette mismatch errors that have nothing to do with your code.
3. The credentials-scrubbing step is fiddly. Get it wrong and you commit a cassette with your real API key embedded in it.
4. For this project specifically, what you actually need to test is not "does Claude return valid JSON" — the AI response format is Claude's problem, not yours. What you need to test is "does `_parse_response()` correctly extract line items from a valid response." That is tested with pure mocks (Level 1), not cassettes.

The right strategy: mock the entire Anthropic client at Level 1 for all regular tests. Reserve real API calls for the actual Dynamic Air Engineering test run. Do not build a VCR infrastructure you will maintain forever.

### File 03: Database and State Testing

**Verdict: APPROVE the mock patterns. CONDITIONAL on the real Supabase integration tests.**

The idempotency tests are the highest-priority tests to write in this file. The `run_extraction` code explicitly deletes existing line items before re-inserting. A test that verifies the delete is called before each insert will catch any future refactoring that accidentally breaks this behavior. The test pattern shown (count `delete.call_args_list` and assert `len >= 1`) works correctly with `MagicMock`.

The `assert_document_status()` / `assert_line_items_count()` helper functions in `db_assertions.py` are worth building because they will be reused in every integration test. They are also small and mechanical — Claude can generate them in seconds.

**The "never run integration tests against production" rule** is obvious but must be stated explicitly. The test teardown deletes rows. One wrong env var and you delete real client data. This is not hypothetical for a developer who is still learning how environment variables work across Docker containers.

**Second Supabase project recommendation:** The research suggests creating a `cma-test` Supabase project. This is the right call but adds operational complexity (two sets of credentials, two storage buckets, schema must be kept in sync). A simpler approach for a non-technical developer: use a dedicated test user and a `test_` prefix convention on all test records. Less clean but manageable without maintaining a second project.

---

## Section 2: Browser Automation (Files 04–06)

### File 04: Playwright Async Job Patterns

**Verdict: APPROVE the polling patterns. The timeout fix is urgent.**

The current `playwright.config.ts` has `timeout: 60_000` (1 minute). This is already in the codebase and it will fail every classification test that takes longer than 60 seconds. The OCR extraction alone on a scanned PDF can take 5 minutes. Classification of a large document is documented as 5–30 minutes. This configuration will cause every E2E test to fail with a timeout error, not a real failure. Fix this before anything else.

The correct configuration:
- Per-test timeout: 35–40 minutes
- Per-assertion timeout: 30 seconds
- Action timeout: 15 seconds

The API polling pattern (Pattern 3) — polling `/api/documents/{id}` instead of waiting for UI text changes — is the correct approach for jobs longer than 1 minute. It is more reliable than text matching because it is not affected by UI copy changes, renders correctly even if the page has not refreshed, and can detect error states immediately. Use this pattern for extraction and classification waits.

**What the existing E2E test `full-journey.spec.ts` gets wrong:** The test uses `await expect(page.getByText(/classified|classification complete/i)).toBeVisible({ timeout: 60_000 })` for the classification step (Step 8). Classification takes up to 30 minutes. This will always time out. The test as written cannot pass for a large document. The API polling helper needs to replace these waits.

### File 05: AI-Agent Browser Testing

**Verdict: APPROVE Playwright MCP. CONDITIONAL on Stagehand. ROAST Browser Use.**

**Playwright MCP: USE THIS NOW.**

You are running Claude Code in an environment that already has the Playwright MCP tools available. This is not a future recommendation — you can do this today. Write a plain-English test script in a message like:

> Navigate to http://localhost:3002, log in as admin@test.local / testpassword, create a client called "Dynamic Air Test", upload [file path], wait for extraction to complete (poll every 30 seconds, up to 10 minutes), take a screenshot of the verification table, describe what you see, click Verify All, and report any errors.

Claude will execute this using the browser tools. This gives you an App Testing Agent with zero code, zero setup, and zero cost beyond the conversation tokens. For a non-technical developer, this is the right tool for validating the full flow.

**Stagehand: Consider after V1 is working.**

Stagehand's `act()` primitive is genuinely better than hardcoded selectors for UI elements that change frequently (button labels, form layouts). It costs $0.02–$0.15 per full journey at Haiku pricing, which is acceptable. However, installing Stagehand, integrating it with the existing Playwright setup, and learning its API is a non-trivial effort. The existing `full-journey.spec.ts` already exists and just needs its timeout fixed and a few selector improvements. Fix the existing test before adopting a new framework.

**Browser Use: ROAST.**

Browser Use is a Python library. Your test stack is TypeScript (Playwright). Your existing E2E test is TypeScript. Browser Use would introduce a third language and runtime (LangChain, Python asyncio) just for browser testing. The only scenario where this makes sense is if you have no TypeScript test infrastructure at all. You do. The research even notes Browser Use has "less control over exact assertions" — for financial data validation, you need exact assertions. Do not add Browser Use to this project.

**The model recommendation** (Haiku for browser navigation decisions) is correct. Haiku is fast and cheap for navigation tasks. Sonnet or Opus are not needed for "click the Login button." Save the expensive models for writing the test instructions, not executing them.

### File 06: File Upload and Download Testing

**Verdict: APPROVE the core patterns. Two specific fixes are urgent.**

The upload pattern (`locator('input[type="file"]').setInputFiles(path)`) works correctly with shadcn/ui's hidden file inputs, as the research correctly notes. The existing `full-journey.spec.ts` already uses this pattern.

**Urgent fix 1: The fixture is wrong.** The current E2E test uploads `e2e/fixtures/sample.xlsx`. The extraction pipeline processes PDFs. Uploading an Excel file and expecting the PDF extraction flow to work is broken by design. You need a real anonymized PDF (5–10 pages, scanned financial statement) as a fixture. The test will fail or produce empty results with an Excel fixture.

**Urgent fix 2: The document ID is never captured.** The current test navigates by constructing URL patterns from the `reportUrl`. If the URL pattern changes or the client page URL structure changes, all subsequent steps fail. Capturing the document ID from the upload API response (`waitForResponse` on `/api/documents POST`) and using it directly in `waitForDocumentStatus()` calls is more robust. This is a one-line change.

**The ZIP magic bytes check** for downloaded Excel files is a valuable sanity check. A common failure mode is that Excel generation fails silently and the "Download" button serves an HTML error page with the wrong Content-Type. The ZIP header check (`504b0304`) catches this in two lines of code.

**The `exceljs` library for sheet inspection** — the research recommends this for verifying that the downloaded file contains the correct sheets. This is worthwhile for the App Testing Agent step (verify the file is a valid Excel with the right sheets). However, for actual cell value comparison, use the Python `excel_comparator.py` script (the Excel Accuracy Agent), not TypeScript exceljs. Mixing cell comparison logic across two languages creates maintenance problems.

---

## Section 3: Excel Comparison (Files 07–09)

### File 07: Excel Comparison Libraries

**Verdict: The openpyxl + xlrd recommendation is correct. The caveat about `data_only=True` is critical and the research handles it well.**

The research correctly identifies the three-way problem:

1. `openpyxl data_only=True` returns `None` for formula cells in a file that was never opened and saved by Excel.
2. Your generated `.xlsm` file is written by openpyxl (not opened by Excel), so formula cells in the template that you did NOT write will return `None`.
3. You write floats, not formulas, into the input cells. So `data_only=True` returns your float values correctly from the generated file.

This works for your specific architecture. It would break if you ever changed the generator to write formulas instead of values. Don't do that.

**The "compare only cells you actually write" principle** is the most important design decision in the entire Excel comparison system. Comparing formula cells (subtotals, totals, cross-sheet references) requires running Excel, which requires Windows and the Excel application. The whole "no xlwings in Docker" constraint goes away if you limit comparison to input cells only. The research makes this clear and the code examples implement it correctly.

**One gap the research does not address:** The ground truth file is `CMA Dynamic 23082025.xls` (the old Excel 97-2003 format). xlrd handles `.xls` correctly. But when the CA produces future test files, they may save as `.xlsx` or `.xlsm`. The comparator as written only handles `.xls` for ground truth files. You need a fallback: if the ground truth file is `.xlsx` or `.xlsm`, use openpyxl to read it. Add this to the comparator before you share it with the CA for review.

**Scale mismatch detection** (the `detect_scale_mismatch()` function) is worth including. The CA may save values in absolute rupees while the pipeline stores in lakhs. The median-ratio approach in the code handles this correctly. Run it as a pre-check before the main comparison.

### File 08: Excel Accuracy Testing Patterns

**Verdict: APPROVE the comparison structure and report format. One tolerance issue.**

The `ComparisonReport` dataclass with `PASS`, `FAIL`, `BLANK_BOTH`, `MISSING` status values is the right data model. Separating "both blank" from "fail" is critical — most rows in a manufacturing CMA will be blank for some fields (trading sections), and you do not want those to count as failures.

**The `MISSING` status (expected non-blank, got blank) should carry more weight than `FAIL`.** A `MISSING` means we completely dropped a line item that the CA had classified. A `FAIL` means we classified it but got the amount slightly wrong. In practice, `MISSING` values indicate a classification failure (the item went to the doubt report and was not resolved). Weight these differently in your accuracy calculation or report them separately with emphasis.

**The 80% pass threshold as a pytest gate:** The `PASS_THRESHOLD = 80.0` in `test_excel_accuracy.py` is where you should start, but 80% is a low bar for financial data that will be submitted to a bank. For V1 testing on Dynamic Air Engineering, 80% is an acceptable minimum to verify the pipeline works at all. For production use, you want 95%+. Be explicit with the CA that 80% in V1 means "the system is working but needs tuning," not "this is production ready."

**On the 1% relative tolerance / 0.50 lakh absolute fallback:**

The 1% relative tolerance is the right choice for financial amounts. A 1% error on ₹45 lakhs is ₹45,000 — small enough to not materially affect the CMA document.

The 0.50 lakh absolute fallback is correct in concept but the specific value needs watching. For a cell containing ₹0.10 lakhs (₹10,000), a 0.50 lakh tolerance means you accept anything between ₹0 and ₹60,000. That is a 500% tolerance for a small amount. This may cause the comparator to pass cells that are genuinely wrong but small. In the first test run, manually check every "PASS" where the actual amount is less than ₹1 lakh to verify the tolerance is not hiding real errors.

**The scale detection function** shows ratios of `[1, 100, 1000, 10000, 100000]` — the 100000x scale factor covers the lakh conversion. This is necessary and correct.

### File 09: Output Validation for AI Pipelines

**Verdict: APPROVE the aggregation accuracy approach. ROAST the item-level labelling approach for now.**

**Aggregation accuracy (row-level)** is the right primary metric for V1. Compare the sum of classified amounts per CMA row against the CA's file value. This requires no manual item labelling, uses the ground truth you already have (the CA-prepared Excel), and catches the most important failure mode (a row value being significantly wrong).

**Item-level labelling (`dynamic_classification_labels.json`):** This requires a human to read each extracted line item and label it with the correct CMA field. For a 33-page document with 80+ items, this is 2–4 hours of manual work. Do not do this for V1. The aggregation accuracy check catches classification errors at the output level, which is what matters. If aggregation accuracy is 85%+, you do not need to know which specific items caused the 15% gap — you fix the pipeline and retest.

**The confusion matrix and systemic error detection** are genuinely useful as a second-round diagnostic tool. After your first full test run, you will have classification output data. Run `systemic_errors()` on whatever items you can label (start with the ones where the aggregated row value is most wrong — those are the highest-leverage items to diagnose). This will tell you exactly which CMA fields need to be added to `learned_mappings`.

**The doubt rate thresholds (manufacturing: <30%, trading: <15%):** These are reasonable starting targets. The Dynamic Air Engineering test (manufacturing) at <30% doubt means the pipeline classifies at least 70% of items without human doubt resolution. Given that the pipeline has been tuned against the 384-item reference mapping, 70% classification rate is achievable from the start. If first-run doubt rate is >40%, the fuzzy matcher thresholds need adjustment before AI tier tuning.

**The tier-weighted accuracy reporting** is genuinely useful for diagnosing where the pipeline is failing:
- High fuzzy accuracy but high doubt rate → fuzzy threshold is too conservative
- Low AI accuracy → prompt needs improvement or reference examples are wrong
- Low fuzzy accuracy → reference mapping has incorrect entries

Track these separately from the first test run.

---

## Section 4: What Was Missed

**None of the 9 files addressed these critical issues:**

**1. The verification step is a legal/contractual requirement, and it is not tested.**

The CLAUDE.md says: "Verification step is MANDATORY between extraction and classification." The existing `full-journey.spec.ts` tests clicking a "Verify All" button, but it does not test that classification is blocked if verification has not happened. This is the most important guard in the entire system. The research for file 01 shows how to test the `extraction_status == 'verified'` guard in `run_classification`, but there is no E2E test that tries to trigger classification on an unverified document and verifies it is rejected. This gap matters because it is a legal requirement, not just a technical one.

**2. The human verification editing step is completely untested.**

The `ExtractionVerifier.tsx` component allows the CA to edit line item amounts before verification. None of the 9 documents cover testing the edit flow: click an amount cell, modify the value, save, verify the change persists in the database. This is the step where the CA corrects OCR errors. If this flow is broken, the CA cannot correct wrong values, which means wrong values flow into the CMA. The research in file 06 mentions `LineItemEditor` testing but calls it "complex" without providing a complete test.

**3. The signed URL expiry problem for Excel downloads is not addressed.**

Supabase Storage signed URLs expire. The research mentions signed URLs in file 06 (Pattern 4) but does not address the scenario where a CA generates the Excel, walks away, comes back an hour later, and tries to download it. The signed URL has expired and the download fails silently (or returns a 403). This is a real UX bug. Either the download URL needs to be refreshed on demand or the signed URL expiry needs to be set to something long enough to cover a working session (4+ hours). No test in any of the 9 files would catch this.

**4. What happens when Docker is not running and the app still has data?**

All 9 files assume the Docker stack is running correctly. The ARQ worker must be running for extraction and classification to complete. If the worker container crashes mid-job (which happens on Windows when Docker Desktop suspends containers), the document stays in `processing` status forever. There is no test for the "stuck in processing" state and no recovery mechanism documented. A non-technical developer will hit this and not know what to do.

**5. The "correct answer" Excel file format will change.**

The CA prepares the ground truth Excel. Over 7 companies, the CA may save files as `.xls`, `.xlsx`, or `.xlsm`. The row numbers and column assignments may differ if the CA has a different version of the CMA template. The comparator assumes a fixed template. When it breaks on company 3, no one will know why. The research should have recommended verifying the ground truth file format and template version before running each comparison.

**6. Supabase RLS (Row Level Security) is mentioned but never tested in the E2E context.**

File 03 shows a unit-level RLS test, but there is no E2E test that verifies one user cannot access another user's documents. In a CA firm with multiple staff members, this is a real security requirement. The existing E2E test only tests the happy path with a single admin user.

---

## Final Recommended Testing Architecture

Build in this order. Do not jump ahead.

### Step 1: Fix the existing E2E test today (30 minutes)

The `full-journey.spec.ts` and `playwright.config.ts` have two bugs that will prevent any test from passing:

1. Update `playwright.config.ts` timeout from `60_000` to `35 * 60 * 1000` (35 minutes).
2. Replace `e2e/fixtures/sample.xlsx` with a real small PDF fixture (use an anonymized financial statement, even 5 pages of a P&L is enough).

These two changes are blocking everything else.

### Step 2: Run the App Testing Agent against Dynamic Air Engineering (this week)

Use Claude + Playwright MCP tools. Write a plain-English test script covering:
- Login
- Create client "Dynamic Air Engineering"
- Upload each of the 5 PDFs one by one
- Wait for extraction (10-minute timeout each)
- Verify all items in the verification UI
- Trigger classification
- Wait for classification (35-minute timeout)
- Download the generated Excel
- Save the Excel to `test-results/dynamic/generated_cma.xlsm`
- Report every error, every status message, and any UI anomalies observed

This run is exploratory. You are not asserting pass/fail. You are discovering what breaks in the real pipeline. Document every finding.

### Step 3: Build the Excel Accuracy Agent immediately after the first run

Write `backend/app/services/excel_comparator.py` using the code from files 07 and 08. The code is already provided — it is 150 lines of Python. Have Claude adapt it to your specific `ALL_FIELD_TO_ROW` and `YEAR_TO_COLUMN` mappings.

Run it: `python -m pytest tests/test_excel_accuracy.py -v`

This gives you the accuracy score for the first test run. You will see which cells are wrong, which rows are missing, and what the percentage error is. This is the feedback loop that drives all subsequent pipeline improvements.

### Step 4: Write the three unit test files for the pipeline tasks (next session)

In order of value:
1. `test_extraction_task.py` — test the happy path, the error/failed status, and the idempotency delete behavior
2. `test_classification_task.py` — test the `extraction_status == 'verified'` guard above all else
3. `test_excel_task.py` — test the already-complete idempotency check

Add the `block_real_api_calls_in_ci` autouse fixture to `conftest.py`. Add 20 ground truth pairs to `classification_ground_truth.py` using items from the Dynamic Air test run.

### Step 5: Add the API polling helper to the E2E test (after Step 4)

Write `e2e/helpers/api-poll.ts` with `waitForDocumentStatus()`. Replace the text-matching waits in `full-journey.spec.ts` with API polling. Capture the document ID from the upload response. This makes the E2E test reliable enough to run automatically.

### Step 6: Run the second company (after Dynamic Air is working)

Do not attempt all 7 companies before Step 5 is complete. Each new company will expose new classification failures. Fix the pipeline between companies, not all at once at the end.

### What to never build

- VCR cassettes. Use pure mocks.
- The `SupabaseMockBuilder` abstraction class. Write mock chains per test.
- Browser Use (Python). You have TypeScript Playwright and Playwright MCP.
- A second Supabase project for testing. Use test prefixes on a dedicated test user.
- Item-level classification labels for V1. Use aggregation accuracy instead.

---

*This review is based on reading all 9 research files, the actual `extraction_tasks.py` implementation, the existing `full-journey.spec.ts`, and the `playwright.config.ts`. Verdicts reflect the specific constraints of this project: non-technical developer, tight budget, 7 companies, mandatory human verification step.*
