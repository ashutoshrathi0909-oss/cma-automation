# CMA Testing Harness V2 — Master Prompt Document

> Built on the proven agent framework from `test-agents/dynamic/MASTER_EXECUTION_PROMPT.md`.
> Incorporates error taxonomy from `test-results/TEST_REPORT.md`.
> Updated for OpenRouter/Qwen3.5 models (replacing Claude Vision + Haiku).

---

## Prerequisites

1. Docker running: `docker compose up --build -d` (all 4 containers: backend, frontend, redis, worker)
2. `.env` has: `OPENROUTER_API_KEY=sk-or-...`, `OCR_PROVIDER=openrouter`, `CLASSIFIER_PROVIDER=openrouter`
3. `.env` does NOT have `SKIP_AI_CLASSIFICATION=true` (remove it)
4. $5 topped up on OpenRouter

## Auth Headers (use on EVERY API call)

```
X-User-Id: 00000000-0000-0000-0000-000000000001
X-User-Role: admin
```

## Wave Schedule

```
Wave 0  [1 window]   Window 0: Setup + bug fixes        (5 min)
Wave 1  [2 windows]  Window 1: Dynamic Air Engineering   (30-45 min)
                     Window 2: Mehta Computers           (15-20 min)
Wave 2  [2 windows]  Window 3: Rule Aggregation          (10 min, after 1+2)
                     Window 4: OCR Quality Comparison    (10 min, after 1)
```

## Error Taxonomy (use consistently across all windows)

| Type | Name | Description | Example |
|------|------|-------------|---------|
| A | Synonym Miss | Same thing, different name | "Purchases @ 5%" = Raw Materials |
| B | Industry Context | Industry changes the mapping | "Bank Interest" = income vs expense |
| C | Conditional | Amount/context determines field | Motor Vehicle > 5K = Gross Block |
| D | Aggregation | Sub-items need netting | Purchase Returns net against Purchases |
| E | Correct Doubt | AI rightly flagged uncertainty | Ambiguous vendor name |
| F | Correct Ambiguity | Genuinely needs human judgment | Combined expenses needing split |

---

# WINDOW 0: Setup & Smoke Test

> Open FIRST. Complete before opening any other windows.

```
PASTE THIS INTO A NEW CLAUDE CODE WINDOW
─────────────────────────────────────────
```

```
# CMA Test Harness — Window 0: Setup & Smoke Test

> READ THIS ENTIRE PROMPT BEFORE DOING ANYTHING.
> Execute exactly what is described here, in exact order.

## System State

Backend:      http://localhost:8000
Frontend:     http://localhost:3002
Redis:        localhost:6379
Auth bypass:  DISABLE_AUTH=true
Headers for ALL API calls:
  X-User-Id: 00000000-0000-0000-0000-000000000001
  X-User-Role: admin
Project root: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2

## Task 1: Fix Unbounded Polling Bugs (CRITICAL)

Two files have infinite polling loops that waste money. Fix them:

### 1a. frontend/src/components/common/ProgressTracker.tsx
- Find the polling interval (setInterval/setTimeout)
- Add MAX_POLLS = 150 (5 min at 2s intervals)
- After MAX_POLLS, clear the interval and show: "Processing timed out. Please refresh the page."
- Track poll count with a ref or state variable

### 1b. frontend/src/app/(app)/cma/[id]/generate/page.tsx
- Same fix: MAX_POLLS = 150
- Stop silently swallowing errors in the catch block — show them via toast or state

## Task 2: Verify Docker Build

```bash
docker compose up --build -d
# Wait 30 seconds for services to start
docker compose ps
```

All containers must show "Up" (running). If not, check logs:
```bash
docker compose logs backend --tail=20
```

## Task 3: Verify OpenRouter Config

```bash
docker compose exec backend python -c "
from app.config import get_settings
s = get_settings()
print(f'OCR Provider: {s.ocr_provider}')
print(f'OCR Model: {s.ocr_model}')
print(f'Classifier Provider: {s.classifier_provider}')
print(f'Classifier Model: {s.classifier_model}')
print(f'OpenRouter Key Set: {bool(s.openrouter_api_key)}')
print(f'Key prefix: {s.openrouter_api_key[:10]}...' if s.openrouter_api_key else 'NO KEY')
"
```

Expected output:
```
OCR Provider: openrouter
OCR Model: qwen/qwen3.5-9b
Classifier Provider: openrouter
Classifier Model: qwen/qwen3.5-122b-a10b
OpenRouter Key Set: True
Key prefix: sk-or-v1-0...
```

If OCR_PROVIDER shows "anthropic", the .env change wasn't picked up. Rebuild: `docker compose down && docker compose up --build -d`

## Task 4: Backend Health Check

```bash
curl -s http://localhost:8000/api/health \
  -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
  -H "X-User-Role: admin" | python -m json.tool
```

## Task 5: Verify Golden Files Exist

```bash
ls -la "DOCS/Financials/CMA Dynamic 23082025.xls" && echo "Dynamic Air golden: OK"
ls -la "DOCS/Excel_project/Mehta computer/CMA 15092025.xls" && echo "Mehta golden: OK"
```

## Task 6: Create Output Directories

```bash
mkdir -p test-results/dynamic-air-v2 test-results/mehta-computers-v2 test-results/rules-v2 test-results/ocr-comparison-v2
```

## Task 7: Verify SKIP_AI_CLASSIFICATION is OFF

```bash
grep -n "SKIP_AI_CLASSIFICATION" .env || echo "Not found — GOOD"
```

If it shows `SKIP_AI_CLASSIFICATION=true`, you must remove or comment that line for classification to work.

## Output

Write to `test-results/window0-setup.md`:

```markdown
# Window 0: Setup Complete

## Checklist
- [ ] Polling bugs fixed (ProgressTracker.tsx + generate/page.tsx)
- [ ] Docker: all containers running
- [ ] OpenRouter config verified (provider=openrouter, key set)
- [ ] Backend health: OK
- [ ] Golden files: both exist
- [ ] Output directories: created
- [ ] SKIP_AI_CLASSIFICATION: removed

## Ready for Wave 1: YES / NO
```

## Cost Safety
- This window makes ZERO API calls to OpenRouter
- Code changes only — no cost risk
```

---

# WINDOW 1: Dynamic Air Engineering — Full Pipeline

> Open AFTER Window 0 completes. Run in PARALLEL with Window 2.

```
PASTE THIS INTO A NEW CLAUDE CODE WINDOW
─────────────────────────────────────────
```

```
# CMA Test Agent — Dynamic Air Engineering (Manufacturing)

> READ THIS ENTIRE PROMPT BEFORE DOING ANYTHING.
> You are testing the full CMA pipeline for Dynamic Air Engineering.
> Execute steps in exact order. Do not skip steps.

## System State

Backend:      http://localhost:8000
Auth bypass:  DISABLE_AUTH=true
Headers for ALL API calls:
  X-User-Id: 00000000-0000-0000-0000-000000000001
  X-User-Role: admin
Project root: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2
OCR Model:    OpenRouter qwen/qwen3.5-9b
Classifier:   OpenRouter qwen/qwen3.5-122b-a10b

## Company Profile

Name:     Dynamic Air Engineering
Industry: manufacturing (air handling equipment — engineering/fabrication)
Slug:     dynamic-air-v2
Years:    FY22, FY23, FY24, FY25
Output:   test-results/dynamic-air-v2/

## Document Manifest (DO NOT DEVIATE)

Base path: DOCS\Financials\

| # | File | Path (relative to base) | Year | Type | Extractor |
|---|------|------------------------|------|------|-----------|
| 1 | BS-Dynamic 2022 - Companies Act.xlsx | FY_22/Financials/ | FY22 | Excel (Audited) | ExcelExtractor |
| 2 | Notes to Financials.pdf | FY_22/Financials/ | FY22 | PDF text (Notes) | PdfExtractor |
| 3 | ITR BS P&L.pdf | FY_22/Financials/ | FY22 | PDF text (ITR) | PdfExtractor |
| 4 | ITR PL & BS.pdf | FY-23/ | FY23 | PDF text (Audited) | PdfExtractor |
| 5 | Notes..pdf | FY-23/ | FY23 | PDF text (Notes) | PdfExtractor |
| 6 | Audited Financials FY-2024 (1).pdf | FY-24/ | FY24 | SCANNED PDF | OcrExtractor (OpenRouter Vision) |
| 7 | Provisional financial 31.03.25 (3).xlsx | FY2025/ | FY25 | Excel (Provisional) | ExcelExtractor |

### Documents to SKIP (do NOT upload)
- Auditor Report.pdf — narrative text, no financial data
- Form 3CA & 3CD.pdf — tax compliance form
- Advance Tax Q*.pdf — tax challans
- Any EMI schedule, sanction letter, bank statement

## Golden CMA File

Path:  DOCS/Financials/CMA Dynamic 23082025.xls
Sheet: INPUT SHEET
Scale: Values in LAKHS (1 = Rs 1,00,000)

## Known Correct Values (from golden CMA — all in LAKHS)

| Row | CMA Field | FY22 | FY23 | FY24 | FY25 |
|-----|-----------|------|------|------|------|
| R22 | Domestic Sales | 46.079 | 69.437 | 67.150 | 77.579 |
| R42 | Raw Materials (Indigenous) | 29.900 | 56.489 | 48.455 | 52.245 |
| R45 | Factory Wages | 3.452 | 5.836 | 6.537 | 7.165 |
| R48 | Power, Coal, Fuel & Water | 0.672 | 0.957 | 0.818 | 1.197 |
| R56 | Depreciation (Mfg) | 3.222 | 3.225 | 3.086 | 1.981 |
| R67 | Salary & Staff Expenses | 0.280 | 0.520 | 0.547 | 1.188 |
| R83 | Interest on Term Loans | 1.990 | 2.292 | 3.084 | 0.940 |
| R85 | Bank Charges | 0.302 | 0.231 | 0.136 | 0.178 |
| R104 | Net Profit (PAT) | 0.789 | 0.693 | 0.390 | 0.966 |
| R242 | Sundry Creditors | 8.176 | 10.376 | 8.451 | 15.851 |
| R260 | Total Assets | 43.649 | 55.757 | 52.505 | 58.037 |

SCALE NOTE: App stores values in absolute rupees. Divide by 1,00,000 before comparing.
FY25 cross-check: Revenue in source Excel = Rs 7,75,79,246 / 1,00,000 = 77.58 lakhs

## Accuracy Thresholds

| Metric | Target |
|--------|--------|
| Numerical field exact match rate | > 95% |
| Vision OCR item recall | > 90% |
| Tier 1 (fuzzy) classification | > 98% |
| Tier 2 (AI) classification | > 90% |
| Doubt/escalation rate | < 15% |
| Silent misclassification rate | 0% (non-negotiable) |
| Sign inversion errors | 0% (non-negotiable) |

---

## EXECUTION STEPS

### Step 1: Read Golden CMA

Write a Python script to extract all values from the golden CMA:

```python
import xlrd, json

wb = xlrd.open_workbook("DOCS/Financials/CMA Dynamic 23082025.xls")
snapshot = {"sheets": {}, "company": "Dynamic Air Engineering"}

for sheet_name in wb.sheet_names():
    sheet = wb.sheet_by_name(sheet_name)
    rows_data = {}
    for row_idx in range(sheet.nrows):
        row_values = []
        for col_idx in range(sheet.ncols):
            cell = sheet.cell(row_idx, col_idx)
            if cell.value not in (None, "", 0, 0.0):
                row_values.append({"col": col_idx, "value": cell.value, "type": cell.ctype})
        if row_values:
            rows_data[row_idx] = row_values
    if rows_data:
        snapshot["sheets"][sheet_name] = rows_data

with open("test-results/dynamic-air-v2/golden-cma-snapshot.json", "w") as f:
    json.dump(snapshot, f, indent=2, default=str)
print(f"Golden CMA: {len(snapshot['sheets'])} sheets extracted")
```

### Step 2: Create Client

```bash
curl -s -X POST http://localhost:8000/api/clients/ \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
  -H "X-User-Role: admin" \
  -d '{"name": "Dynamic Air Engineering V2", "industry_type": "manufacturing", "contact_email": "dynamic@test.com"}' \
  | python -m json.tool
```

Save returned `id` as CLIENT_ID. If 409 conflict, fetch existing:
```bash
curl -s http://localhost:8000/api/clients/ \
  -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
  -H "X-User-Role: admin" \
  | python -c "import sys,json; [print(c['id'], c['name']) for c in json.load(sys.stdin)]"
```

### Step 3: Upload & Extract All 7 Documents

Use this Python script (saves IDs + tracks progress):

```python
import requests, json, time, os

BASE = "http://localhost:8000"
HEADERS = {
    "X-User-Id": "00000000-0000-0000-0000-000000000001",
    "X-User-Role": "admin"
}
CLIENT_ID = "<PASTE_CLIENT_ID_HERE>"
PROJECT = r"C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2"

DOCUMENTS = [
    {"file": r"DOCS\Financials\FY_22\Financials\BS-Dynamic 2022 - Companies Act.xlsx",
     "year": 2022, "type": "audited_financials", "nature": "digital", "label": "FY22 BS Excel"},
    {"file": r"DOCS\Financials\FY_22\Financials\Notes to Financials.pdf",
     "year": 2022, "type": "audited_financials", "nature": "digital", "label": "FY22 Notes PDF"},
    {"file": r"DOCS\Financials\FY_22\Financials\ITR BS P&L.pdf",
     "year": 2022, "type": "audited_financials", "nature": "digital", "label": "FY22 ITR PDF"},
    {"file": r"DOCS\Financials\FY-23\ITR PL & BS.pdf",
     "year": 2023, "type": "audited_financials", "nature": "digital", "label": "FY23 ITR PDF"},
    {"file": r"DOCS\Financials\FY-23\Notes..pdf",
     "year": 2023, "type": "audited_financials", "nature": "digital", "label": "FY23 Notes PDF"},
    {"file": r"DOCS\Financials\FY-24\Audited Financials FY-2024 (1).pdf",
     "year": 2024, "type": "audited_financials", "nature": "scanned", "label": "FY24 SCANNED"},
    {"file": r"DOCS\Financials\FY2025\Provisional financial 31.03.25 (3).xlsx",
     "year": 2025, "type": "provisional", "nature": "digital", "label": "FY25 Provisional"},
]

results = []
for doc in DOCUMENTS:
    filepath = os.path.join(PROJECT, doc["file"])
    filename = os.path.basename(filepath)
    print(f"\n--- Uploading: {doc['label']} ---")

    # Upload
    with open(filepath, "rb") as f:
        resp = requests.post(f"{BASE}/api/documents/",
            headers=HEADERS,
            data={
                "client_id": CLIENT_ID,
                "document_type": doc["type"],
                "financial_year": doc["year"],
                "nature": doc["nature"],
            },
            files={"file": (filename, f)}
        )
    if resp.status_code != 201:
        print(f"  UPLOAD FAILED: {resp.status_code} {resp.text[:200]}")
        results.append({"label": doc["label"], "status": "upload_failed", "error": resp.text[:200]})
        continue

    doc_data = resp.json()
    doc_id = doc_data["id"]
    print(f"  Uploaded: doc_id={doc_id}")

    # Trigger extraction
    resp = requests.post(f"{BASE}/api/documents/{doc_id}/extract", headers=HEADERS)
    if resp.status_code not in (200, 202):
        print(f"  EXTRACT TRIGGER FAILED: {resp.status_code}")
        results.append({"label": doc["label"], "doc_id": doc_id, "status": "trigger_failed"})
        continue

    task_data = resp.json()
    task_id = task_data.get("task_id", "")
    print(f"  Extraction started: task_id={task_id}")

    # Poll (MAX 150 iterations = 5 min at 2s)
    MAX_POLLS = 150
    for poll in range(MAX_POLLS):
        time.sleep(2)
        resp = requests.get(f"{BASE}/api/tasks/{task_id}", headers=HEADERS)
        if resp.status_code != 200:
            continue
        status = resp.json().get("status", "")
        if status in ("completed", "complete", "failed"):
            print(f"  Extraction {status} after {poll * 2}s")
            break
        if poll % 15 == 0:
            print(f"  Polling... ({poll * 2}s, status={status})")
    else:
        print(f"  TIMEOUT after {MAX_POLLS * 2}s")
        results.append({"label": doc["label"], "doc_id": doc_id, "status": "timeout"})
        continue

    # Fetch extraction results
    resp = requests.get(f"{BASE}/api/documents/{doc_id}/extraction", headers=HEADERS)
    items = resp.json() if resp.status_code == 200 else []
    item_count = len(items) if isinstance(items, list) else 0
    print(f"  Items extracted: {item_count}")

    results.append({
        "label": doc["label"],
        "doc_id": doc_id,
        "task_id": task_id,
        "year": doc["year"],
        "status": status,
        "item_count": item_count,
    })

# Save results
with open("test-results/dynamic-air-v2/extraction-results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\n=== Extraction complete: {len(results)} documents ===")
for r in results:
    print(f"  {r['label']}: {r.get('item_count', 'N/A')} items ({r['status']})")
```

### Step 4: Gate Check — Extraction Quality

After extraction completes, check:
- FY24 scanned PDF MUST produce > 50 items (hard gate)
- Total across all docs > 135 items (soft gate)
- No documents in "failed" status

If FY24 < 50 items, STOP and report: "Vision OCR failed. Check worker logs."

### Step 5: Verify All Extractions

For each document, mark extraction as verified:
```bash
# Verify each document (replace DOC_IDs from Step 3 results)
for DOC_ID in <id1> <id2> <id3> <id4> <id5> <id6> <id7>; do
  curl -s -X POST "http://localhost:8000/api/documents/$DOC_ID/extraction/verify" \
    -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
    -H "X-User-Role: admin"
  echo " verified: $DOC_ID"
done
```

### Step 6: Trigger Classification

For each document, trigger classification:
```bash
for DOC_ID in <id1> <id2> <id3> <id4> <id5> <id6> <id7>; do
  curl -s -X POST "http://localhost:8000/api/documents/$DOC_ID/classify" \
    -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
    -H "X-User-Role: admin"
  echo " classification triggered: $DOC_ID"
done
```

Poll each task (MAX 150 polls per task, 2s intervals).

### Step 7: Review Classification Results

```python
import requests, json

BASE = "http://localhost:8000"
HEADERS = {
    "X-User-Id": "00000000-0000-0000-0000-000000000001",
    "X-User-Role": "admin"
}

DOC_IDS = ["<id1>", "<id2>", ...]  # from Step 3

all_classifications = []
for doc_id in DOC_IDS:
    resp = requests.get(f"{BASE}/api/documents/{doc_id}/classifications", headers=HEADERS)
    if resp.status_code == 200:
        classifications = resp.json()
        all_classifications.extend(classifications)

# Analyze
confident = [c for c in all_classifications if c.get("confidence", 0) >= 0.8 and not c.get("is_doubt")]
doubts = [c for c in all_classifications if c.get("is_doubt")]
methods = {}
for c in all_classifications:
    m = c.get("classification_method", "unknown")
    methods[m] = methods.get(m, 0) + 1

print(f"Total classified: {len(all_classifications)}")
print(f"Confident (>=0.8): {len(confident)}")
print(f"Doubts: {len(doubts)}")
print(f"Methods: {methods}")

# Save
with open("test-results/dynamic-air-v2/classification-results.json", "w") as f:
    json.dump(all_classifications, f, indent=2, default=str)
```

### Step 8: Resolve Doubts Using Golden CMA

For each doubt item:
1. Read the line item description from the classification result
2. Look up where that item is placed in the golden CMA (golden-cma-snapshot.json)
3. Resolve the doubt via API:

```bash
curl -s -X POST "http://localhost:8000/api/documents/<DOC_ID>/classifications/<CLASS_ID>/resolve" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
  -H "X-User-Role: admin" \
  -d '{"cma_field_name": "Wages", "cma_row": 45, "cma_sheet": "input_sheet"}'
```

Log each resolution to `test-results/dynamic-air-v2/doubt-resolutions.json`.

### Step 9: Create CMA Report & Generate Excel

```bash
# Create CMA report
curl -s -X POST "http://localhost:8000/api/clients/$CLIENT_ID/cma-reports" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
  -H "X-User-Role: admin" \
  -d '{"document_ids": ["<id1>","<id2>","<id3>","<id4>","<id5>","<id6>","<id7>"], "title": "Dynamic Air FY22-25 V2 Test"}'

# Save REPORT_ID from response

# Generate Excel
curl -s -X POST "http://localhost:8000/api/cma-reports/$REPORT_ID/generate" \
  -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
  -H "X-User-Role: admin"
```

Poll task, then download the generated .xlsm file.

### Step 10: Cell-by-Cell Golden Comparison

```python
import xlrd, json

# Load golden CMA
golden = xlrd.open_workbook("DOCS/Financials/CMA Dynamic 23082025.xls")
golden_sheet = golden.sheet_by_name("INPUT SHEET")  # or first sheet

# Load generated CMA (use openpyxl for .xlsm)
import openpyxl
generated = openpyxl.load_workbook("test-results/dynamic-air-v2/generated_cma.xlsm", keep_vba=True)
gen_sheet = generated["INPUT SHEET"]  # or first sheet

# Compare key rows
KNOWN_ROWS = {
    22: "Domestic Sales", 42: "Raw Materials", 45: "Factory Wages",
    48: "Power Coal Fuel", 56: "Depreciation Mfg", 67: "Salary Staff",
    83: "Interest Term Loans", 85: "Bank Charges", 104: "Net Profit PAT",
    242: "Sundry Creditors", 260: "Total Assets"
}

TOLERANCE = 500  # Rs 500 absolute tolerance
comparison = []

for row_num, field_name in KNOWN_ROWS.items():
    for col_idx, fy_label in [(1, "FY22"), (2, "FY23"), (3, "FY24"), (4, "FY25")]:
        golden_val = golden_sheet.cell(row_num, col_idx).value or 0
        gen_cell = gen_sheet.cell(row=row_num + 1, column=col_idx + 1)  # openpyxl is 1-indexed
        gen_val = gen_cell.value or 0

        # Golden is in lakhs, app is in absolute rupees
        golden_abs = golden_val * 100000
        delta = abs(golden_abs - gen_val)
        match = delta <= TOLERANCE

        comparison.append({
            "row": row_num, "field": field_name, "year": fy_label,
            "golden_lakhs": golden_val, "golden_abs": golden_abs,
            "generated": gen_val, "delta": delta, "match": match
        })

# Summary
matches = sum(1 for c in comparison if c["match"])
total = len(comparison)
print(f"Match rate: {matches}/{total} ({matches/total*100:.1f}%)")

with open("test-results/dynamic-air-v2/comparison-report.json", "w") as f:
    json.dump(comparison, f, indent=2)
```

### Step 11: Discover Classification Rules

For EVERY mismatch from Step 10:
1. Find what the source document said (extraction results)
2. Find what the app classified it as (classification results)
3. Find what the golden CMA says it should be
4. Create a rule

Save to `test-results/dynamic-air-v2/discovered-rules.json`:

```json
[
  {
    "id": "DYN-A-001",
    "type": "A",
    "priority": "HIGH",
    "source_text": "Wages & Salaries",
    "golden_field": "Factory Wages",
    "golden_row": 45,
    "golden_sheet": "input_sheet",
    "app_classified_as": "Salary and staff expenses",
    "app_row": 67,
    "rule": "Manufacturing: 'Wages & Salaries' maps to Factory Wages (R45), not Salary (R67)",
    "company": "Dynamic Air Engineering",
    "industry": "manufacturing"
  }
]
```

### Step 12: Write Summary

Save to `test-results/dynamic-air-v2/SUMMARY.md`:

```markdown
# Dynamic Air Engineering — Test Report

## Pipeline Results
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Documents processed | N/7 | 7 | |
| Total items extracted | N | >135 | |
| FY24 Vision OCR items | N | >50 | |
| Classification accuracy | N% | >90% | |
| Doubt rate | N% | <15% | |
| Golden match rate (key rows) | N% | >95% | |
| Silent misclassifications | N | 0 | |
| Sign inversions | N | 0 | |

## Classification Method Distribution
| Method | Count | Percentage |
|--------|-------|-----------|
| rule_engine | N | N% |
| fuzzy | N | N% |
| ai_openrouter | N | N% |
| doubt | N | N% |

## Top Misclassifications
[List top 5 errors with error type A-F]

## Rules Discovered
[Count and summary of rules]

## OpenRouter Cost
[Token usage from response headers if available]
```

Also write `test-results/dynamic-air-v2/status.json`:

```json
{
  "company": "Dynamic Air Engineering",
  "slug": "dynamic-air-v2",
  "industry": "manufacturing",
  "stage": "completed",
  "extraction_items": 0,
  "classification_accuracy": 0.0,
  "golden_match_rate": 0.0,
  "doubt_count": 0,
  "rules_generated": 0,
  "timestamp": "2026-03-21T...",
  "failure_reason": null
}
```

## Gate Conditions

| Gate | Condition | Action |
|------|-----------|--------|
| G1: FY24 items | < 50 items from scanned PDF | HARD STOP. Report OCR failure. |
| G2: Total items | < 135 total | WARNING. Continue but flag. |
| G3: Classification | < 70% accuracy | WARNING. Continue. |
| G4: Golden match | < 60% key rows | WARNING. Likely scale issue. |

## Cost Safety (NON-NEGOTIABLE)

- MAX 150 polling iterations per task (2s intervals = 5 min)
- If any API call fails 3 times consecutively, STOP and record error
- Do NOT re-upload/re-extract documents that already succeeded
- If estimated cost exceeds $2 for this company, STOP and report
- Track poll counts explicitly — no unbounded loops
```

---

# WINDOW 2: Mehta Computers — Full Pipeline

> Open AFTER Window 0 completes. Run in PARALLEL with Window 1.

```
PASTE THIS INTO A NEW CLAUDE CODE WINDOW
─────────────────────────────────────────
```

```
# CMA Test Agent — Mehta Computers (Trading)

> READ THIS ENTIRE PROMPT BEFORE DOING ANYTHING.
> Execute steps in exact order. Do not skip steps.

## System State

Backend:      http://localhost:8000
Auth bypass:  DISABLE_AUTH=true
Headers for ALL API calls:
  X-User-Id: 00000000-0000-0000-0000-000000000001
  X-User-Role: admin
Project root: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2
OCR Model:    OpenRouter qwen/qwen3.5-9b
Classifier:   OpenRouter qwen/qwen3.5-122b-a10b

## Company Profile

Name:     Mehta Computers (M/S MEHTA COMPUTERS, Prop. Jignesh Chandrakant Mehta)
Industry: trading (computer hardware reseller)
Slug:     mehta-computers-v2
Years:    FY22, FY23, FY24, FY25
Output:   test-results/mehta-computers-v2/

## Document Manifest

Base path: DOCS\Excel_project\Mehta computer\

| # | File | Path | Year | Type | Extractor |
|---|------|------|------|------|-----------|
| 1 | Mehta_Computers_financials_2022.xls | 2022/ | FY22 | Excel | ExcelExtractor |
| 2 | Mehta Computers financials 2023.xls | 2023/ | FY23 | Excel | ExcelExtractor |
| 3 | Mehta_Computers_financials_2024.xls | 2024/ | FY24 | Excel | ExcelExtractor |
| 4 | BSheet.pdf | 2025/ | FY25 | Scanned PDF | OcrExtractor |
| 5 | PandL.pdf | 2025/ | FY25 | Scanned PDF | OcrExtractor |
| 6 | TrialBal.pdf | 2025/ | FY25 | Scanned PDF | OcrExtractor |

### Documents to SKIP
- ITR one page *.jpeg — image, not financial data
- ITR Acknowledgement *.pdf — acknowledgement only
- ITR Intimation *.pdf — intimation only
- EMI Schedule.pdf — loan schedule
- testpdf.pdf — test file
- Wankaner - Letter.pdf — correspondence
- *.zip — archives

## Golden CMA File

Path:  DOCS/Excel_project/Mehta computer/CMA 15092025.xls
Sheet: INPUT SHEET
Scale: Values in LAKHS

## Known Correct Values (from golden CMA — all in LAKHS, FY24)

| Row | CMA Field | FY24 Value |
|-----|-----------|-----------|
| R22 | Domestic Sales | 230.611 |
| R23 | Export Sales | 0.0 |
| R42 | Raw Materials Consumed (Indigenous) | 174.126 |
| R48 | Power, Coal, Fuel and Water | 0.267 |
| R56 | Depreciation (Manufacturing) | 0.131 |
| R67 | Salary and staff expenses | 14.863 |
| R68 | Rent, Rates and Taxes | 0.444 |
| R70 | Advertisements and Sales Promotions | 6.433 |
| R83 | Interest on Fixed Loans | 1.285 |
| R85 | Bank Charges | 0.031 |

## Previous Test Results (from Mehta test run on 2026-03-19)

The last test found:
- 162 items extracted from FY24 Excel
- 88.3% classification accuracy
- 66% doubt rate (root cause: cma_input_row = NULL in reference_mappings)
- 12 improvement rules generated (A-001 through D-001)

This V2 run tests with OpenRouter models instead of Claude Haiku.

---

## EXECUTION STEPS

Follow EXACTLY the same 12-step process as the Dynamic Air window:

1. Read golden CMA → save to test-results/mehta-computers-v2/golden-cma-snapshot.json
2. Create client: "Mehta Computers V2", industry_type: "trading"
3. Upload & extract all 6 documents (use same Python script pattern)
4. Gate check: FY25 scanned PDFs should produce > 20 items each
5. Verify all extractions
6. Trigger classification for all docs
7. Review classification results
8. Resolve doubts using golden CMA
9. Create CMA report + generate Excel
10. Cell-by-cell golden comparison (Rs 500 tolerance)
11. Discover rules (use same JSON format, prefix "MHT-")
12. Write SUMMARY.md + status.json

## Trading Industry Notes

Trading companies differ from manufacturing:
- "Purchase @ N% (Local/Inter-State/IGST)" = Raw Materials Consumed (R42) — TYPE A rule
- No factory wages, power, or manufacturing expenses
- "Carriage Inward/Outward" = Freight (R47) — TYPE C rule
- ALL_CAPS vendor names on BS = Sundry Creditors (R242) — TYPE B rule
- "Bank Interest" on income side = Interest Received (R30), NOT Bank Charges — TYPE B rule

## Cost Safety (NON-NEGOTIABLE)

Same rules as Window 1:
- MAX 150 polls per task
- 3 consecutive failures = STOP
- $2 cost cap for this company
- No unbounded loops
```

---

# WINDOW 3: Rule Aggregation

> Open AFTER Windows 1 AND 2 are BOTH complete.

```
PASTE THIS INTO A NEW CLAUDE CODE WINDOW
─────────────────────────────────────────
```

```
# CMA Test Harness — Window 3: Rule Aggregation

> You combine and deduplicate classification rules from all company tests.
> This is analysis only — ZERO API calls.

## System State

Project root: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2
Input files:
  - test-results/dynamic-air-v2/discovered-rules.json
  - test-results/mehta-computers-v2/discovered-rules.json
  - test-results/TEST_REPORT.md (previous Mehta test — 12 rules, A-001 through D-001)
Output:
  - test-results/rules-v2/

## Error Taxonomy (for categorizing rules)

| Type | Name | Example |
|------|------|---------|
| A | Synonym Miss | "Purchases @ 5%" = Raw Materials |
| B | Industry Context | "Bank Interest" = income vs expense |
| C | Conditional | Motor Vehicle > 5K = Gross Block |
| D | Aggregation | Purchase Returns net against Purchases |

## Tasks

### Task 1: Load All Rules

Read discovered-rules.json from both company test directories.
Also read the 12 existing rules from test-results/TEST_REPORT.md (the Mehta v1 run).

### Task 2: Deduplicate

Two rules are duplicates if:
- Same source_text pattern (fuzzy match OK)
- Same target CMA field + row
- Same industry context

Keep the most specific version.

### Task 3: Categorize

Group rules into:
1. Universal rules — apply to ALL industries
2. Industry-specific — only manufacturing OR trading
3. Company-specific — unique naming conventions

### Task 4: Check for Conflicts

Find rules that contradict:
- Same source text → different CMA fields for different industries (OK — industry-specific)
- Same source text → different CMA fields for SAME industry (CONFLICT — needs human review)

### Task 5: Format for Pipeline Integration

Read the rule engine file to understand the format:
```bash
cat backend/app/services/classification/rule_engine.py
```

Convert aggregated rules into the format expected by the rule engine.

### Task 6: Generate learned_mappings

Create entries for the learned_mappings table:
```json
[
  {
    "source_text_pattern": "Purchase @ %",
    "cma_field_name": "Raw Materials Consumed (Indigenous)",
    "cma_row": 42,
    "cma_sheet": "input_sheet",
    "industry": "trading",
    "confidence": 0.95,
    "source": "golden_comparison"
  }
]
```

### Output Files

Save to test-results/rules-v2/:
- aggregated-rules.json — all unique rules
- conflicts.json — contradicting rules
- learned-mappings-import.json — ready for DB import
- RULE-SUMMARY.md — human-readable summary

## Cost Safety
- ZERO API calls in this window
- Pure file reading and analysis
- No cost risk whatsoever
```

---

# WINDOW 4: OCR Quality Comparison

> Open AFTER Window 1 (Dynamic Air) completes.

```
PASTE THIS INTO A NEW CLAUDE CODE WINDOW
─────────────────────────────────────────
```

```
# CMA Test Harness — Window 4: OCR Quality Comparison

> You compare the app's Qwen3.5-9B OCR extraction against YOUR independent
> extraction to find gaps in the vision model's output.

## System State

Project root: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2
Input:
  - test-results/dynamic-air-v2/extraction-results.json (app's extraction)
  - DOCS/Financials/FY-24/Audited Financials FY-2024 (1).pdf (source scanned PDF)
Output:
  - test-results/ocr-comparison-v2/

## Why This Matters

The app now uses Qwen3.5-9B ($0.05/M) instead of Claude Sonnet ($3/M) for OCR.
That's 60x cheaper but we need to verify quality hasn't dropped significantly.
The FY24 scanned PDF is the primary test — it's a 33-page audited financial document.

## Tasks

### Task 1: Load App's Extraction

Read test-results/dynamic-air-v2/extraction-results.json.
Filter to the FY24 document (the scanned PDF).
List all line items the app extracted with amounts.

### Task 2: Independent Extraction

Convert 2-3 representative pages from the FY24 PDF to images:
```python
from pdf2image import convert_from_path
images = convert_from_path(
    r"DOCS\Financials\FY-24\Audited Financials FY-2024 (1).pdf",
    dpi=200, first_page=1, last_page=3
)
for i, img in enumerate(images):
    img.save(f"test-results/ocr-comparison-v2/page_{i+1}.jpg", "JPEG")
```

Then use YOUR vision capabilities to read each page image.
Extract every line item + amount you can see.

Focus on:
- Scale factor headers ("in Lakhs" / "in Crores" / "Rs.")
- Indian number format: 1,23,456 = 123456
- Negative amounts in parentheses: (1,23,456) = -123456
- Notes to Accounts sub-breakdowns (not just totals)
- Column alignment (current year vs previous year)

### Task 3: Compare Side-by-Side

For each page:
| # | Line Item | App Amount | Your Amount | Match? | Issue |
|---|-----------|-----------|-------------|--------|-------|

### Task 4: Error Categories

| Category | Count | Examples |
|----------|-------|---------|
| Missing item (app missed it) | N | |
| Wrong amount | N | |
| Wrong scale factor | N | |
| Merged items | N | |
| Split items | N | |
| OCR misread | N | |

### Task 5: Calculate Metrics

- Item recall: items_found / items_expected
- Amount accuracy: correct_amounts / items_found
- Scale detection: correct_scale / total_pages

### Task 6: Qwen3.5-9B Verdict

Based on the comparison, is Qwen3.5-9B adequate for production?
Or do we need to upgrade to qwen/qwen3.5-122b-a10b for OCR?

### Output

Save to test-results/ocr-comparison-v2/OCR-QUALITY-REPORT.md

## Cost Safety
- Do NOT call the app's API
- Only read saved extraction results
- Your own vision analysis uses your built-in capabilities
- ZERO OpenRouter cost
```

---

# TEMPLATE: Additional Company (Companies 3-7)

> Copy this template. Replace all {{PLACEHOLDERS}}.

```
# CMA Test Agent — {{COMPANY_NAME}} ({{INDUSTRY_TYPE}})

> READ THIS ENTIRE PROMPT BEFORE DOING ANYTHING.

## System State
Backend:      http://localhost:8000
Auth bypass:  DISABLE_AUTH=true
Headers:      X-User-Id: 00000000-0000-0000-0000-000000000001 / X-User-Role: admin
Project root: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2
OCR:          OpenRouter qwen/qwen3.5-9b
Classifier:   OpenRouter qwen/qwen3.5-122b-a10b

## Company Profile
Name:     {{COMPANY_NAME}}
Industry: {{INDUSTRY_TYPE}}
Slug:     {{company-slug}}
Years:    {{FY_LIST}}
Output:   test-results/{{company-slug}}/

## Document Manifest
| # | File | Path | Year | Type | Extractor |
|---|------|------|------|------|-----------|
{{DOCUMENT_TABLE}}

## Documents to SKIP
{{SKIP_LIST}}

## Golden CMA File
Path: {{GOLDEN_CMA_PATH}}

## Known Correct Values (all in LAKHS)
| Row | CMA Field | {{FY_COLUMNS}} |
|-----|-----------|{{FY_VALUES}}  |

## Execute the 12-step pipeline:
1. Read golden CMA
2. Create client
3. Upload & extract all docs (MAX 150 polls each)
4. Gate check extraction counts
5. Verify all extractions
6. Trigger classification (MAX 150 polls each)
7. Review classification results
8. Resolve doubts from golden CMA
9. Create CMA report + generate Excel
10. Cell-by-cell golden comparison (Rs 500 tolerance)
11. Discover rules (use error taxonomy A-F, prefix "{{PREFIX}}-")
12. Write SUMMARY.md + status.json

## Cost Safety
- MAX 150 polls per task, $2 cost cap, 3 failures = STOP
```
