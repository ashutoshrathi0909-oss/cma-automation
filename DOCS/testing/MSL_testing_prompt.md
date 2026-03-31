# MSL (Matrix Stampi Ltd) — Agent-Team App Verification

**Purpose:** Paste this into a fresh Claude Code session. It will deploy **4 focused agents** sequentially, each handling one phase. This prevents context overflow and keeps each task clean.

**Priority:** The #1 goal is verifying the generated CMA Excel has the correct numbers in the correct cells.

---

## HOW THIS WORKS

You are the **orchestrator**. You deploy agents for each phase, passing results between them:

```
AGENT 1: Code Changes (rules + pipeline integration)
    ↓ restart Docker
AGENT 2: Extraction Test (upload, extract, verify)
    ↓ passes document_id, client_id
AGENT 3: Classification Test (classify, review, approve)
    ↓ passes report_id
AGENT 4: Excel Verification (generate, download, compare)
    ↓ final report
```

**IMPORTANT orchestration rules:**
- Deploy agents ONE AT A TIME (each depends on the previous)
- After Agent 1 completes, YOU run `docker compose restart backend worker` before deploying Agent 2
- After Agent 2, extract the `client_id` and `document_id` from its result and pass them to Agent 3
- After Agent 3, extract the `report_id` and pass it to Agent 4
- After Agent 4, compile the final test report yourself

---

## ORCHESTRATOR STEPS

### Step 0: Pre-flight
Run these yourself (don't use an agent):
```bash
cd "C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2"
docker compose up -d
curl http://localhost:8000/health
```
Verify all 4 services are up (backend, frontend, worker, redis).

### Step 1: Deploy AGENT 1 — Code Changes
Use the Agent tool with the prompt from Section A below.
Wait for completion. Then restart services:
```bash
docker compose restart backend worker
```
Wait 10 seconds for services to stabilize.

### Step 2: Deploy AGENT 2 — Extraction Test
Use the Agent tool with the prompt from Section B below.
Capture `client_id` and `document_id` from the result.

### Step 3: Deploy AGENT 3 — Classification Test
Use the Agent tool with the prompt from Section C below.
Replace `{{CLIENT_ID}}` and `{{DOCUMENT_ID}}` with values from Agent 2.
Capture `report_id` from the result.

### Step 4: Deploy AGENT 4 — Excel Verification
Use the Agent tool with the prompt from Section D below.
Replace `{{REPORT_ID}}`, `{{CLIENT_ID}}`, `{{DOCUMENT_ID}}` with actual values.

### Step 5: Compile Results
After all agents complete, create `test-results/MSL_test_results.md` by combining all agent outputs.

---

## SECTION A — AGENT 1 PROMPT: Code Changes

```
You are working on the CMA Automation System. Your task is to make TWO code changes and verify they compile.

PROJECT ROOT: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2

═══════════════════════════════════════════════════════════════
TASK A1: Integrate RuleEngine into Classification Pipeline
═══════════════════════════════════════════════════════════════

The file `backend/app/services/classification/rule_engine.py` contains a RuleEngine class
with a method `apply(raw_text, amount, section, industry_type) -> RuleMatchResult | None`.

The file `backend/app/services/classification/pipeline.py` contains ClassificationPipeline
which does: Fuzzy (Tier 1) → AI (Tier 2) → Doubt (Tier 3).

RuleEngine is NEVER imported or called. You must add it as Tier 0.

Steps:
1. Read both files fully
2. In pipeline.py:
   - Import: `from app.services.classification.rule_engine import RuleEngine, RuleMatchResult`
   - In __init__: add `self._rules = RuleEngine()`
   - In classify_item(), BEFORE the Tier 1 fuzzy section, add Tier 0:

   ```python
   # ── Tier 0: Deterministic rules ──────────────────────────────────
   rule_result = self._rules.apply(description, amount, section, industry)
   if rule_result:
       logger.debug(
           "Tier 0 rule: '%s' → %s (rule=%s)",
           description, rule_result.cma_field_name, rule_result.rule_id,
       )
       return {
           "line_item_id": item["id"],
           "client_id": client_id,
           "cma_field_name": rule_result.cma_field_name,
           "cma_sheet": rule_result.cma_sheet,
           "cma_row": rule_result.cma_row,
           "cma_column": cma_column,
           "broad_classification": rule_result.broad_classification,
           "classification_method": f"rule_{rule_result.rule_id}",
           "confidence_score": rule_result.confidence,
           "fuzzy_match_score": 0,
           "is_doubt": False,
           "doubt_reason": None,
           "ai_best_guess": rule_result.cma_field_name,
           "alternative_fields": [],
           "status": "auto_classified",
       }
   ```

   Note: `industry` variable is not currently in classify_item. The industry_type parameter
   IS passed in but may need to be lowercased. Check the existing code to see how it's used —
   fuzzy matcher receives industry_type. Use the same value.

═══════════════════════════════════════════════════════════════
TASK A2: Add Confirmed Classification Rules to RuleEngine
═══════════════════════════════════════════════════════════════

Read `backend/app/services/classification/rule_engine.py` fully.
It has V1 rules: A-001/002, B-001/002/003, C-001/002/003/004, D-001/002.

ADD these new rules to the `apply()` method. Follow the EXACT same pattern as existing rules
(regex helpers, RuleMatchResult returns, priority ordering).

MODIFICATION to existing rules:
1. C-003 (Freight): Remove "industry == trading" restriction. Apply to ALL industries.
   Reason: MSL (manufacturing) confirms Carriage Inwards → R47 works for manufacturing too.

2. C-004 (Security Deposits): Split into two:
   - Government deposits (electricity, telephone, GEM, caution) → R237
   - Private deposits (landlord deposit, security deposit with private party) → R238
   Pattern for R238: "deposit" + ("landlord"|"private"|"lessor"|"owner")

NEW RULES TO ADD (after existing rules, before `return None`):

JOB-001: Job Work / Processing Charges → R46 (all industries, mfg priority)
  Pattern: job\s*work|processing\s*charges
  Row: R46, sheet: input_sheet, broad: manufacturing_expense
  Confidence: 0.97

FRE-001: Hamali / Cooly / Cartage / Mathadi → R47 (Freight) (all industries)
  Pattern: hamali|cooly|coolie|cartage|mathadi|loading\s+unloading
  Row: R47, sheet: input_sheet, broad: manufacturing_expense
  Confidence: 0.95

RNM-001: ALL R&M in Manufacturing → R50 (not R72) (manufacturing only)
  Pattern: repair|r\s*&\s*m|r\s*and\s*m|maintenance (broad match)
  Condition: industry == "manufacturing"
  Row: R50, sheet: input_sheet, broad: manufacturing_expense
  Confidence: 0.95

MSL-001: "Stock in Trade" in Manufacturing inventory → R201 (Finished Goods)
  Pattern: stock[\s-]*in[\s-]*trade|trading\s*stock
  Condition: industry == "manufacturing" AND section contains "inventor" or "current asset"
  Row: R201, sheet: input_sheet, broad: Current Assets
  Confidence: 0.95

MSL-003: Provision for Gratuity (LT on BS) → R153 (LT Unsecured Debt)
  Pattern: provision\s*(for\s*)?gratuity|gratuity\s*(liability|provision)
  Condition: section contains "long" or "non-current" or "provision"
  Row: R153, sheet: input_sheet, broad: Term Liabilities
  Confidence: 0.93

MSL-005: Export Incentive → DOUBT (EXCLUDE from CMA)
  Pattern: export\s*incentive|rodtep|meis\s*incentive|duty\s*drawback
  This is special: return a DOUBT result, not a normal classification.
  Set is_doubt=True, doubt_reason="Export Incentive: CA may exclude from CMA — verify"
  Do NOT return a RuleMatchResult. Instead return None and handle it specially, OR
  create a new return type. Simplest: just let it fall to doubt naturally by returning None
  and NOT adding export incentive to the fuzzy reference mapping. The AI should flag it.
  ACTUALLY: safest approach is to return None here and document this as a known gap.
  The AI classifier should send it to doubt since it's unusual.

MSL-006: Insurance Claim Received → R34 (Others Non-Op Income)
  Pattern: insurance\s*claim|claim\s*(from|received)\s*insurance
  Condition: section is income/revenue side
  Row: R34, sheet: input_sheet, broad: Non-operating Income
  Confidence: 0.93

MSL-007: Freight OUTWARD / Discount Allowed / Sales Promotion → R70 (Mfg)
  Pattern: freight\s*out(ward)?|discount\s*allowed|trade\s*discount|sales?\s*promotion
  Condition: industry == "manufacturing"
  Row: R70, sheet: input_sheet, broad: admin_expense
  Confidence: 0.93
  NOTE: This must NOT conflict with C-003 (Carriage/Freight INWARD → R47).
  C-003 matches "carriage inward|freight inward|freight charges" (INBOUND).
  MSL-007 matches "freight outward" (OUTBOUND). Different patterns, no conflict.

MSL-008: Admin catch-all → R71 (Others Admin)
  Pattern: tour\s*(and|&)?\s*travel|consultancy\s*fees|professional\s*charges|
           general\s*expenses|miscellaneous\s*exp|sundry\s*expenses
  Condition: NOT matching audit fees (audit → R73 via fuzzy)
  Row: R71, sheet: input_sheet, broad: admin_expense
  Confidence: 0.90
  NOTE: Insurance PREMIUM (not claim) also goes here. Add pattern:
  ^insurance$|insurance\s*(premium|charges)
  But NOT "insurance claim" (that's MSL-006 → R34)

MSL-010: Liability Written Off → R90 (Sundry Balances Written Off)
  Pattern: liabilit(y|ies)\s*written\s*(off|back)|excess\s*provision\s*written\s*back|
           old\s*payable
  Row: R90, sheet: input_sheet, broad: Non-operating Expense
  Confidence: 0.93

RULE ORDERING in apply():
Place new rules in this order within the method:
1. Existing C-type rules (C-001, C-002, C-003 modified, C-004 modified)
2. JOB-001 (Job Work)
3. RNM-001 (R&M in Manufacturing)
4. MSL-001 (Stock in Trade in Manufacturing)
5. MSL-007 (Freight Outward/Discount/Sales Promo in Manufacturing)
6. Existing A-type rules (A-001, A-002)
7. Existing D-type rules (D-001, D-002)
8. MSL-010 (Liability Written Off)
9. MSL-003 (Gratuity Provision)
10. MSL-006 (Insurance Claim)
11. FRE-001 (Hamali/Cooly/Cartage)
12. MSL-008 (Admin catch-all — LAST among content rules, lowest priority)
13. Existing B-type rules (B-001, B-002, B-003) — context-dependent, last

After making changes, verify syntax:
```bash
docker compose exec backend python -c "from app.services.classification.rule_engine import RuleEngine; print('OK')"
docker compose exec backend python -c "from app.services.classification.pipeline import ClassificationPipeline; print('OK')"
```

RETURN a summary of:
- How many new rules added
- Which existing rules modified
- Any compilation errors and fixes
```

---

## SECTION B — AGENT 2 PROMPT: Extraction Test

```
You are testing the CMA Automation System's extraction pipeline using MSL financial data.

PROJECT ROOT: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2

═══════════════════════════════════════════════════════════════
CONTEXT
═══════════════════════════════════════════════════════════════

MSL (Matrix Stampi Ltd) is a manufacturing company. We are uploading their Excel file
to test if the app correctly extracts all financial line items.

The app runs on Docker:
- Backend API: http://localhost:8000
- Auth: dev-bypass mode (use header: Authorization: Bearer dev-bypass)

Source file: "FInancials main/MSL - Manufacturing/MSL - B.S -2024-25 Final 151025.xlsx"
This is an Excel (.xlsx) with 15 sheets covering FY2024-25 (with FY2023-24 comparatives).
Amounts are in Rs. '000 (thousands).

═══════════════════════════════════════════════════════════════
STEP 1: Create Client
═══════════════════════════════════════════════════════════════

```bash
curl -s -X POST http://localhost:8000/api/clients \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-bypass" \
  -d '{
    "name": "Matrix Stampi Ltd",
    "industry_type": "manufacturing",
    "financial_year_ending": "March",
    "currency": "INR",
    "notes": "Metal Stamping / Dies. Kolkata. Test company."
  }'
```
SAVE the client_id from the response.

═══════════════════════════════════════════════════════════════
STEP 2: Upload Excel File
═══════════════════════════════════════════════════════════════

```bash
curl -s -X POST http://localhost:8000/api/documents \
  -H "Authorization: Bearer dev-bypass" \
  -F "file=@\"C:/Users/ASHUTOSH/OneDrive/Desktop/CMA project -2/FInancials main/MSL - Manufacturing/MSL - B.S -2024-25 Final 151025.xlsx\"" \
  -F "client_id={{CLIENT_ID}}" \
  -F "document_type=combined_financial_statement" \
  -F "financial_year=2025" \
  -F "nature=audited"
```
SAVE the document_id from the response.

If upload fails, check:
- Is the file path correct? List the directory first.
- Is Supabase Storage configured? Check .env for SUPABASE_URL and keys.
- Is the backend healthy? curl http://localhost:8000/health

═══════════════════════════════════════════════════════════════
STEP 3: Trigger Extraction & Wait
═══════════════════════════════════════════════════════════════

```bash
curl -s -X POST http://localhost:8000/api/documents/{{DOCUMENT_ID}}/extract \
  -H "Authorization: Bearer dev-bypass"
```
Get the task_id. Poll every 5 seconds (MAX 20 polls — do NOT loop forever):
```bash
curl -s http://localhost:8000/api/tasks/{{TASK_ID}} -H "Authorization: Bearer dev-bypass"
```
Wait until status = "complete". If it fails, check Docker worker logs:
```bash
docker compose logs worker --tail 50
```

═══════════════════════════════════════════════════════════════
STEP 4: Get Extracted Items & Compare
═══════════════════════════════════════════════════════════════

```bash
curl -s http://localhost:8000/api/documents/{{DOCUMENT_ID}}/items \
  -H "Authorization: Bearer dev-bypass" | python -m json.tool > test-results/MSL_extraction_output.json
```

Compare the extracted items against this EXPECTED list.
For each item, check: (a) present? (b) amount correct? (c) section correct?

EXPECTED P&L ITEMS (key ones):
| Description (approximate match) | Expected Amount (Rs.'000) |
|--------------------------------|--------------------------|
| Sale of Products Domestic | ~213,076 |
| Sale of Products Export | ~9,906 |
| Interest Income | ~103.56 |
| Export Incentive / RoDTEP | ~86.06 |
| Insurance Claim Received | ~355.79 |
| Goods Purchased Indigenous | ~93,468.53 |
| Carriage Inwards | ~256.44 |
| Salaries and Wages | ~12,748.73 |
| Bonus | ~88.83 |
| PF Contribution | ~530.35 |
| Staff Welfare | ~73.00 |
| Bank Charges | ~539.95 |
| Bank Interest CC/OD | ~1,743.11 |
| Other Charges (finance) | ~521.65 |
| Power Coal Fuel | ~3,539.64 |
| Stores and Spares | ~4,429.82 |
| Job Work Charges | ~284.47 |
| Rent | ~800.00 |
| R&M Plant & Machinery | ~157.18 |
| R&M Others | ~657.10 |
| Insurance | ~238.65 |
| Rates & Taxes | ~86.25 |
| Audit Fees | ~135.00 |
| Freight Outward | ~154.43 |
| Discount Allowed | ~673.55 |
| Bad Debts Written Off | ~650.08 |
| Exchange Rate Fluctuation | ~147.02 |
| Tour & Travel | ~163.49 |
| Consultancy Fees | ~1,360.49 |
| General Expenses | ~212.60 |
| P&L on Sale of FA | ~336.09 |
| Liability Written Off | ~100.00 |

EXPECTED BS ITEMS (key ones):
| Description (approximate match) | Expected Amount (Rs.'000) |
|--------------------------------|--------------------------|
| Paid-up Capital | ~21,609.46 |
| General Reserve | ~750.00 |
| Share Premium | ~12,444.00 |
| Provision for Gratuity | ~2,171.62 |
| CC IDBI Working Capital | ~14,293.87 |
| Current maturities TL | ~1,409.66 |
| Unsecured Loans Promoters | ~41,768.22 |
| Sundry Creditors | ~25,432 |
| Stock in Trade | ~87,874.07 |
| Trade Receivables | ~43,052.86 |
| Security Deposits | ~1,752.55 |
| Advance Income Tax | ~4,832.27 |
| GST Balance Govt Auth | ~1,344.08 |

═══════════════════════════════════════════════════════════════
STEP 5: Verify Extraction
═══════════════════════════════════════════════════════════════

If extraction looks correct, mark as verified:
```bash
curl -s -X POST http://localhost:8000/api/documents/{{DOCUMENT_ID}}/verify \
  -H "Authorization: Bearer dev-bypass"
```

═══════════════════════════════════════════════════════════════
RETURN these values in your response:
═══════════════════════════════════════════════════════════════

1. client_id: ___
2. document_id: ___
3. Total items extracted: ___
4. Items matching expected list: ___/___
5. Missing items: [list]
6. Wrong amounts: [list with expected vs actual]
7. Extra/unexpected items: [list]
8. Any errors encountered: [description]
```

---

## SECTION C — AGENT 3 PROMPT: Classification Test

```
You are testing the CMA classification pipeline for MSL (Matrix Stampi Ltd).
Extraction is already done. You need to classify and review results.

PROJECT ROOT: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2
Backend API: http://localhost:8000
Auth header: Authorization: Bearer dev-bypass

client_id: {{CLIENT_ID}}
document_id: {{DOCUMENT_ID}}
Industry: manufacturing

═══════════════════════════════════════════════════════════════
STEP 1: Create CMA Report
═══════════════════════════════════════════════════════════════

```bash
curl -s -X POST http://localhost:8000/api/clients/{{CLIENT_ID}}/cma-reports \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-bypass" \
  -d '{
    "title": "MSL CMA FY2024-25 Test",
    "document_ids": ["{{DOCUMENT_ID}}"]
  }'
```
SAVE the report_id (id field in response).

═══════════════════════════════════════════════════════════════
STEP 2: Trigger Classification & Wait
═══════════════════════════════════════════════════════════════

```bash
curl -s -X POST http://localhost:8000/api/documents/{{DOCUMENT_ID}}/classify \
  -H "Authorization: Bearer dev-bypass"
```
Get task_id. Poll (MAX 30 polls, 5s intervals):
```bash
curl -s http://localhost:8000/api/tasks/{{TASK_ID}} -H "Authorization: Bearer dev-bypass"
```

If classification involves AI calls, this may take 5-15 minutes.
If it fails, check: docker compose logs worker --tail 100

═══════════════════════════════════════════════════════════════
STEP 3: Get Classifications & Compare
═══════════════════════════════════════════════════════════════

```bash
curl -s http://localhost:8000/api/documents/{{DOCUMENT_ID}}/classifications \
  -H "Authorization: Bearer dev-bypass" | python -m json.tool > test-results/MSL_classification_output.json
```

Compare EACH classification against this expected mapping.
For each item check: (a) correct CMA row? (b) correct method? (c) is_doubt correct?

EXPECTED CLASSIFICATION MAPPING (P&L items):

| Source Text (approx) | Expected Row | Expected Field | Expected Method |
|----------------------|-------------|---------------|----------------|
| Sale of Products Domestic | R22 | Domestic Sales | fuzzy |
| Sale of Products Export | R23 | Export Sales | fuzzy |
| Interest Income | R30 | Interest Received | rule_B-001 or fuzzy |
| Export Incentive | DOUBT | — | should be is_doubt=True |
| Insurance Claim Received | R34 | Others Non-Op | rule_MSL-006 |
| Goods Purchased Indigenous | R42 | RM Indigenous | fuzzy/AI |
| Carriage Inwards | R47 | Freight & Transport | rule_C-003 |
| Salaries and Wages | R45 | Wages | fuzzy |
| Bonus | R45 | Wages | fuzzy/AI |
| PF Contribution | R45 | Wages | fuzzy/AI |
| Staff Welfare | R45 | Wages | fuzzy/AI |
| Bank Charges | R85 | Bank Charges | fuzzy |
| Bank Interest CC/OD | R84 | Interest on WC | fuzzy/rule |
| Other Charges (finance) | R83 | Interest on TL | AI/doubt |
| Power Coal Fuel | R48 | Power Coal Fuel | fuzzy |
| Stores and Spares | R44 | Stores & Spares | fuzzy |
| Job Work Charges | R46 | Job Work | rule_JOB-001 |
| Rent | R68 | Rent Rates Taxes | fuzzy |
| R&M Plant & Machinery | R50 | R&M Manufacturing | rule_RNM-001 |
| R&M Others | R50 | R&M Manufacturing | rule_RNM-001 |
| Insurance (premium) | R71 | Others Admin | rule_MSL-008 |
| Rates & Taxes | R68 | Rent Rates Taxes | fuzzy |
| Audit Fees | R73 | Audit Fees | fuzzy |
| Freight Outward | R70 | Advertisements Selling | rule_MSL-007 |
| Discount Allowed | R70 | Advertisements Selling | rule_MSL-007 |
| Bad Debts Written Off | R69 | Bad Debts | fuzzy |
| Exchange Rate Fluctuation | R91 | Loss on Exchange | fuzzy |
| Sales Promotion | R70 | Advertisements Selling | rule_MSL-007 |
| Tour & Travel | R71 | Others Admin | rule_MSL-008 |
| Consultancy Fees | R71 | Others Admin | rule_MSL-008 |
| General Expenses | R71 | Others Admin | rule_MSL-008 |
| P&L on Sale of FA | R89 | Loss on Sale FA | fuzzy |
| Liability Written Off | R90 | Sundry Balances | rule_MSL-010 |

EXPECTED CLASSIFICATION MAPPING (BS items):

| Source Text (approx) | Expected Row | Expected Field |
|----------------------|-------------|---------------|
| Paid-up Capital | R116 | Share Capital |
| General Reserve | R121 | General Reserve |
| Share Premium | R123 | Share Premium |
| P&L Balance | R122 | Balance from P&L |
| Other Reserve | R125 | Other Reserve |
| CC IDBI Working Capital | R131 | WC Bank Finance |
| Current maturities TL | R136 | TL in 1 year |
| Unsecured Loans Promoters | R152 | Quasi Equity |
| Provision for Gratuity | R153 | LT Unsecured Debt |
| Stock in Trade | R201 | Finished Goods |
| Trade Receivables | R206 | Domestic Receivables |
| Cash on Hand | R212 | Cash on Hand |
| Bank Balances | R213 | Bank Balances |
| GST Balance | R219 | Advances recoverable |
| Advances to Suppliers | R220 | Advances to Suppliers RM |
| Advance Income Tax | R221 | Advance Income Tax |
| Prepaid Expenses | R222 | Prepaid Expenses |
| Security Deposits | R237 | Security Deposits Govt |
| Sundry Creditors | R242 | Sundry Creditors |
| Advance from Customers | R243 | Advance from Customers |
| Provision for Taxation | R244 | Provision for Taxation |
| TDS Payable | R246 | Other Statutory Liab |

═══════════════════════════════════════════════════════════════
STEP 4: Approve Correct / Correct Wrong
═══════════════════════════════════════════════════════════════

Read the classification output JSON. For each classification:

If the cma_row MATCHES the expected row → APPROVE:
```bash
curl -s -X POST http://localhost:8000/api/classifications/{{CLASSIFICATION_ID}}/approve \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-bypass" \
  -d '{"cma_report_id": "{{REPORT_ID}}", "note": "Verified vs ground truth"}'
```

If the cma_row is WRONG → CORRECT it to the expected value:
```bash
curl -s -X POST http://localhost:8000/api/classifications/{{CLASSIFICATION_ID}}/correct \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-bypass" \
  -d '{
    "cma_report_id": "{{REPORT_ID}}",
    "cma_field_name": "CORRECT_FIELD_NAME",
    "cma_row": CORRECT_ROW_NUMBER,
    "cma_sheet": "input_sheet",
    "broad_classification": "appropriate_broad_class",
    "note": "Corrected per ground truth"
  }'
```

IMPORTANT: Do NOT loop unboundedly. Process items in batches. If there are >100 items,
do the first 100 and report. Use bounded iteration (max 100 API calls).

═══════════════════════════════════════════════════════════════
STEP 5: Check Confidence Summary
═══════════════════════════════════════════════════════════════

```bash
curl -s http://localhost:8000/api/cma-reports/{{REPORT_ID}}/confidence-summary \
  -H "Authorization: Bearer dev-bypass"
```

═══════════════════════════════════════════════════════════════
RETURN these values:
═══════════════════════════════════════════════════════════════

1. report_id: ___
2. Total classified: ___
3. Rule matches (Tier 0): ___ — list which rules fired
4. Fuzzy matches (Tier 1): ___
5. AI matches (Tier 2): ___
6. Doubts (Tier 3): ___ — list items
7. WRONG auto-classifications: ___ — list each (item, got, expected)
8. Items approved: ___
9. Items corrected: ___
10. Confidence summary from API: (paste)
11. Any errors: [description]
```

---

## SECTION D — AGENT 4 PROMPT: Excel Verification

```
You are testing the CMA Excel generation for MSL (Matrix Stampi Ltd).
Classification is done and approved. Now generate the CMA Excel and verify it.

PROJECT ROOT: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2
Backend API: http://localhost:8000
Auth header: Authorization: Bearer dev-bypass

report_id: {{REPORT_ID}}
client_id: {{CLIENT_ID}}

═══════════════════════════════════════════════════════════════
STEP 1: Generate CMA Excel
═══════════════════════════════════════════════════════════════

```bash
curl -s -X POST http://localhost:8000/api/cma-reports/{{REPORT_ID}}/generate \
  -H "Authorization: Bearer dev-bypass"
```
Get task_id. Poll (MAX 20 polls, 5s intervals):
```bash
curl -s http://localhost:8000/api/tasks/{{TASK_ID}} -H "Authorization: Bearer dev-bypass"
```

═══════════════════════════════════════════════════════════════
STEP 2: Download Generated Excel
═══════════════════════════════════════════════════════════════

```bash
mkdir -p test-results
curl -s http://localhost:8000/api/cma-reports/{{REPORT_ID}}/download \
  -H "Authorization: Bearer dev-bypass" \
  -o "test-results/MSL_generated_CMA.xlsm"
```

If the download endpoint returns a signed URL instead of the file directly,
fetch the URL from the response and download separately.

═══════════════════════════════════════════════════════════════
STEP 3: Write & Run Comparison Script
═══════════════════════════════════════════════════════════════

Write a Python script at test-results/compare_msl_cma.py that:
1. Opens the generated CMA Excel (test-results/MSL_generated_CMA.xlsm)
2. Opens the ground truth CMA (FInancials main/MSL - Manufacturing/MSL CMA 24102025.xls)
3. Reads the INPUT SHEET from both
4. Compares cell-by-cell against the expected values below
5. Reports matches, mismatches, and missing values

IMPORTANT: First check what column letters correspond to which financial years.
Open the ground truth CMA and inspect the INPUT SHEET header rows to map columns.
The year_columns.py mapping is: {2023: "B", 2024: "C", 2025: "D"}

GROUND TRUTH — P&L SECTION (Row → Column → Expected Lakhs value):
Focus on FY25 (Column D) as that's what we uploaded:

Row 22, Domestic Sales: 2130.76
Row 23, Export Sales: 99.06
Row 30, Interest Received: 1.04
Row 34, Others Non-Op Income: 3.56
Row 41, RM Imported: 21.81
Row 42, RM Indigenous: 1943.16
Row 44, Stores & Spares: 44.30
Row 45, Wages: 134.41
Row 46, Job Work: 2.84
Row 47, Freight: 2.56
Row 48, Power Coal Fuel: 35.40
Row 49, Others Manufacturing: 0.00
Row 50, R&M Manufacturing: 8.14
Row 67, Salary Staff: 0.00 (MUST be zero for MSL)
Row 68, Rent Rates Taxes: 8.86
Row 69, Bad Debts: 6.50
Row 70, Advertisements: 8.05
Row 71, Others Admin: 23.77
Row 72, R&M Admin: 0.00 (MUST be zero for MSL manufacturing)
Row 73, Audit Fees: 1.35
Row 83, Interest TL: 2.98
Row 84, Interest WC: 19.67
Row 85, Bank Charges: 5.40
Row 89, Loss Sale FA: 3.36
Row 90, Sundry Balances: 1.00
Row 91, Exchange Loss: 1.47

GROUND TRUTH — BS SECTION (Row → Column → Expected Lakhs value):
Focus on FY25 (Column D):

Row 116, Paid-up Capital: 216.09
Row 121, General Reserve: 7.50
Row 122, P&L Balance: 10.24
Row 123, Share Premium: 124.44
Row 125, Other Reserve: 144.34
Row 131, WC Bank Finance: 142.94
Row 136, TL in 1 year: 14.10
Row 137, TL after 1 year: 0.00
Row 152, Quasi Equity: 417.68
Row 153, LT Unsecured Debt: 21.72
Row 201, Finished Goods: 878.74
Row 206, Domestic Receivables: 345.40
Row 208, Debtors > 6 months: 85.13
Row 212, Cash on Hand: 0.34
Row 213, Bank Balances: 6.64
Row 219, Advances Govt: 13.44
Row 220, Advances Suppliers RM: 0.23
Row 221, Advance Income Tax: 48.32
Row 222, Prepaid Expenses: 0.29
Row 223, Other Advances: 5.54
Row 237, Security Deposits: 17.53
Row 242, Sundry Creditors: 254.32
Row 243, Advance from Customers: 36.45
Row 244, Provision for Taxation: 48.68
Row 246, Other Statutory Liab: 2.31
Row 250, Other Current Liab: 102.79

UNIT CONVERSION WARNING:
The source Excel has amounts in Rs.'000. The CMA expects Lakhs.
Conversion: Lakhs = Rs.'000 / 100
If the generated CMA shows values 100x too large, the app didn't convert units.
Document this as a bug but still check if the ROW assignments are correct.

Tolerance: ±0.5 Lakhs (rounding differences are OK).

Run the script:
```bash
cd "C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2"
python test-results/compare_msl_cma.py
```

═══════════════════════════════════════════════════════════════
STEP 4: Check Macro Preservation
═══════════════════════════════════════════════════════════════

Verify the generated file is .xlsm (not .xlsx) and VBA macros are present:
```python
import openpyxl
wb = openpyxl.load_workbook("test-results/MSL_generated_CMA.xlsm", keep_vba=True)
print(f"Has VBA: {wb.vba_archive is not None}")
print(f"Sheets: {wb.sheetnames}")
```

═══════════════════════════════════════════════════════════════
RETURN these values:
═══════════════════════════════════════════════════════════════

1. Excel generated successfully: Yes/No
2. File format: .xlsm / .xlsx
3. VBA macros preserved: Yes/No
4. Total cells checked: ___
5. MATCHING cells: ___
6. MISMATCHED cells: ___ (list each: row, expected, actual)
7. MISSING cells (None/empty): ___ (list each)
8. Unit conversion handled: Yes/No (if No, factor off by: ___)
9. Row assignments correct (ignoring unit): Yes/No
10. Comparison script output: (paste full output)
11. Any errors: [description]
```

---

## SECTION E — FINAL RESULTS TEMPLATE

After all 4 agents complete, the orchestrator compiles results into `test-results/MSL_test_results.md`:

```markdown
# MSL End-to-End Test Results — [DATE]

## Agent 1: Code Changes
- Rules added: ___
- Rules modified: ___
- Pipeline integration: OK / FAILED
- Compilation: OK / ERRORS

## Agent 2: Extraction
- Items extracted: ___
- Expected items found: ___/___
- Missing: [list]
- Wrong amounts: [list]

## Agent 3: Classification
- Total classified: ___
- Rule (Tier 0): ___
- Fuzzy (Tier 1): ___
- AI (Tier 2): ___
- Doubt (Tier 3): ___
- Wrong auto-classifications: [list]
- Items approved: ___
- Items corrected: ___

## Agent 4: Excel Verification
- Cells checked: ___
- Matching: ___
- Mismatched: [list]
- Missing: [list]
- Unit conversion: OK / BUG (factor ___)
- VBA preserved: Yes/No

## Overall Verdict
- Extraction pipeline: PASS / PARTIAL / FAIL
- Classification pipeline: PASS / PARTIAL / FAIL
- Excel generation: PASS / PARTIAL / FAIL
- CMA accuracy: ___% cells correct

## Bugs Found
1. [severity] [description]
2. ...

## Next Steps
1. ...
```

---

## KNOWN ISSUES & GOTCHAS

| Issue | Impact | Mitigation |
|-------|--------|------------|
| RuleEngine not integrated | Rules won't fire | Agent 1 fixes this |
| FY2022 not in YEAR_TO_COLUMN | FY22 data won't get a column | We're testing FY25 only (Column D) — OK for now |
| Excel amounts Rs.'000, CMA expects Lakhs | Values 100x off | Document as bug, verify row assignments separately |
| MSL PDFs scanned/unreadable | Can't test PDF extraction | Using Excel only — OK |
| Export Incentive should be EXCLUDED | May auto-classify | Should go to doubt |
| R67 must be 0 for MSL | Employee costs may split wrong | Check classification output |
| "Stock in Trade" mislabel | Needs MSL-001 rule | Agent 1 adds this |
| Bounded iteration | Context overflow prevention | Max 100 API calls per agent, max 20 polls |

---

*End of MSL Agent-Team Testing Prompt. Paste into a fresh Claude Code session.*
