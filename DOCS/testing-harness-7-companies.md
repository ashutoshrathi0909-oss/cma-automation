# CMA Testing Harness — 7 New Companies

> 7 companies x 2 windows each (Pipeline + OCR) = 14 company windows
> Plus: 1 Rule Combiner + 1 Final Report = **16 windows total**
> Run in waves, 3 companies in parallel

---

## How To Use This Document

1. Get the 7 company files + their golden CMAs from your father's firm
2. For each company, fill in the `{{PLACEHOLDERS}}` in both prompts (Pipeline + OCR)
3. Drop the files into `DOCS/Financials/<company-name>/`
4. Open windows in the wave order below

## What You Need For Each Company

| Item | Example | Where to get it |
|------|---------|-----------------|
| Company name | "Shree Industries" | From your firm |
| Industry type | manufacturing / trading / services | From your firm |
| Financial documents (PDFs/Excel) | BS, P&L, Notes, ITR | From your firm's files |
| Golden CMA file (.xls/.xlsm) | "CMA Shree 2025.xls" | The CMA your firm already prepared manually |
| Financial years covered | FY22, FY23, FY24 | Check the documents |

## Folder Structure (create before starting)

```
DOCS/Financials/
  company-1/
    FY22/          ← put FY22 PDFs/Excel here
    FY23/          ← put FY23 PDFs/Excel here
    FY24/          ← put FY24 PDFs/Excel here
    golden-cma.xls ← the manually prepared CMA
  company-2/
    ...
  company-7/
    ...
```

---

## Wave Schedule

```
WAVE 0   [1 window]    Setup (already done — Window 0 from earlier)

WAVE 1   [3 parallel]  Company 1 Pipeline | Company 2 Pipeline | Company 3 Pipeline
WAVE 2   [3+3 parallel] Company 4-6 Pipeline | Company 1-3 OCR (needs Wave 1 results)
WAVE 3   [1+3 parallel] Company 7 Pipeline | Company 4-6 OCR
WAVE 4   [1+1 parallel] Company 7 OCR | Rule Combiner (needs all 7 pipeline results)
WAVE 5   [1 window]    Final Report (needs Rule Combiner + all results)

Timeline: ~2-3 hours total if running 3 parallel
Cost: ~Rs 63 ($0.75) for all 7 companies at Qwen3.5 prices
```

---

## Auth Headers (use on EVERY API call in EVERY window)

```
X-User-Id: 00000000-0000-0000-0000-000000000001
X-User-Role: admin
```

## Error Taxonomy (consistent across ALL windows)

| Type | Name | Example |
|------|------|---------|
| A | Synonym Miss | "Purchases @ 5%" = Raw Materials |
| B | Industry Context | "Bank Interest" income vs expense |
| C | Conditional | Amount/context determines field |
| D | Aggregation | Sub-items need netting |
| E | Correct Doubt | AI rightly flagged |
| F | Correct Ambiguity | Needs human judgment |

---

# ============================================================
# PIPELINE PROMPTS (one per company — 7 total)
# ============================================================

# COMPANY 1 — PIPELINE WINDOW

```
PASTE INTO A NEW CLAUDE CODE WINDOW
────────────────────────────────────
```

```
# CMA Test Agent — {{COMPANY_1_NAME}} ({{INDUSTRY_1}})

> READ THIS ENTIRE PROMPT BEFORE DOING ANYTHING.
> You test the FULL CMA pipeline for this ONE company.
> Execute steps in exact order. Write ALL output to your folder.
> Do NOT touch other companies' folders or data.

## System State

Backend:      http://localhost:8000
Auth bypass:  DISABLE_AUTH=true
Headers for ALL API calls:
  X-User-Id: 00000000-0000-0000-0000-000000000001
  X-User-Role: admin
Project root: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2
OCR Model:    OpenRouter qwen/qwen3.5-9b ($0.05/$0.15 per M tokens)
Classifier:   OpenRouter qwen/qwen3.5-122b-a10b ($0.26/$2.08 per M tokens)

## Company Profile

Name:     {{COMPANY_1_NAME}}
Industry: {{INDUSTRY_1}}  (manufacturing / trading / services)
Slug:     company-1
Years:    {{FY_YEARS_1}}  (e.g., FY22, FY23, FY24)
Output:   test-results/company-1/

## ISOLATION RULES (non-negotiable)

1. Create your OWN client via POST /api/clients/ with a UNIQUE name
2. Write ALL output to test-results/company-1/ — NEVER read or write other company folders
3. Use your own CLIENT_ID, REPORT_ID, DOCUMENT_IDs — NEVER reference another window's IDs
4. If the API returns data from another company, FILTER to your own
5. Do NOT restart Docker, modify .env, or touch the database schema
6. If you hit a 500 error, record it and continue — do not fix backend code

## Document Manifest

Base path: DOCS\Financials\company-1\

| # | File | Subfolder | Year | Type | Expected Extractor |
|---|------|-----------|------|------|--------------------|
| 1 | {{FILE_1}} | {{SUBFOLDER}} | {{YEAR}} | {{Excel/PDF/Scanned}} | {{Excel/Pdf/OcrExtractor}} |
| 2 | {{FILE_2}} | {{SUBFOLDER}} | {{YEAR}} | {{Excel/PDF/Scanned}} | {{Excel/Pdf/OcrExtractor}} |
| 3 | {{FILE_3}} | {{SUBFOLDER}} | {{YEAR}} | {{Excel/PDF/Scanned}} | {{Excel/Pdf/OcrExtractor}} |
| ... | ... | ... | ... | ... | ... |

### Documents to SKIP (do NOT upload)
- Auditor Report / Directors Report — narrative text
- Form 3CA / 3CD — tax compliance forms
- Advance Tax challans
- EMI schedules, sanction letters, bank statements
- Any non-financial correspondence

## Golden CMA File

Path:  DOCS/Financials/company-1/{{GOLDEN_CMA_FILENAME}}
Sheet: INPUT SHEET (or first sheet)
Scale: Values likely in LAKHS (1 = Rs 1,00,000) — verify from file

## Known Correct Values (fill after reading golden CMA)

| Row | CMA Field | {{FY_COL_1}} | {{FY_COL_2}} | {{FY_COL_3}} |
|-----|-----------|-------------|-------------|-------------|
| R22 | Domestic Sales | | | |
| R42 | Raw Materials | | | |
| R45 | Factory Wages | | | |
| R67 | Salary & Staff | | | |
| R83 | Interest on Term Loans | | | |
| R85 | Bank Charges | | | |
| R104 | Net Profit (PAT) | | | |
| R260 | Total Assets | | | |

NOTE: If this is a TRADING company, R45 (Factory Wages) and R48 (Power) will be 0.
If MANUFACTURING, R42 will be actual raw materials not "purchases".

## Accuracy Thresholds

| Metric | Target |
|--------|--------|
| Numerical exact match | > 95% |
| Vision OCR item recall (scanned PDFs) | > 90% |
| Classification accuracy | > 90% |
| Doubt rate | < 15% |
| Silent misclassification | 0% |
| Sign inversion | 0% |

---

## EXECUTION STEPS (12 steps — do ALL in order)

### Step 1: Read Golden CMA & Save Snapshot

```python
import xlrd, json, os

GOLDEN_PATH = r"DOCS\Financials\company-1\{{GOLDEN_CMA_FILENAME}}"
OUTPUT_DIR = "test-results/company-1"
os.makedirs(OUTPUT_DIR, exist_ok=True)

wb = xlrd.open_workbook(GOLDEN_PATH)
snapshot = {"company": "{{COMPANY_1_NAME}}", "industry": "{{INDUSTRY_1}}", "sheets": {}}

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
            rows_data[str(row_idx)] = row_values
    if rows_data:
        snapshot["sheets"][sheet_name] = rows_data

with open(f"{OUTPUT_DIR}/golden-cma-snapshot.json", "w") as f:
    json.dump(snapshot, f, indent=2, default=str)

# Print key values for the Known Correct Values table
input_sheet = wb.sheet_by_name("INPUT SHEET") if "INPUT SHEET" in wb.sheet_names() else wb.sheet_by_index(0)
KEY_ROWS = [22, 42, 45, 48, 56, 67, 83, 85, 104, 242, 260]
print("\\nKEY VALUES (for spot-checking):")
for r in KEY_ROWS:
    if r < input_sheet.nrows:
        vals = [input_sheet.cell(r, c).value for c in range(input_sheet.ncols)]
        label = input_sheet.cell(r, 0).value
        print(f"  Row {r}: {label} = {vals[1:]}")
```

Record the known values from this output — you'll use them in Step 10.

### Step 2: Create Client

```bash
curl -s -X POST http://localhost:8000/api/clients/ \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
  -H "X-User-Role: admin" \
  -d '{"name": "{{COMPANY_1_NAME}}", "industry_type": "{{INDUSTRY_1}}", "contact_email": "company1@test.com"}'
```

Save `CLIENT_ID` from response. If 409 (already exists), fetch with GET /api/clients/.

### Step 3: Upload & Extract All Documents

```python
import requests, json, time, os

BASE = "http://localhost:8000"
HEADERS = {
    "X-User-Id": "00000000-0000-0000-0000-000000000001",
    "X-User-Role": "admin"
}
CLIENT_ID = "<PASTE_CLIENT_ID>"
PROJECT = r"C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2"

# ─── FILL IN YOUR DOCUMENTS HERE ───
DOCUMENTS = [
    {"file": r"DOCS\Financials\company-1\{{SUBFOLDER}}\{{FILE_1}}",
     "year": {{YEAR}}, "type": "audited_financials", "nature": "{{digital/scanned}}", "label": "{{LABEL}}"},
    # ... add all documents
]

results = []
for doc in DOCUMENTS:
    filepath = os.path.join(PROJECT, doc["file"])
    filename = os.path.basename(filepath)
    print(f"\\n--- Uploading: {doc['label']} ---")

    # Upload
    with open(filepath, "rb") as f:
        resp = requests.post(f"{BASE}/api/documents/",
            headers=HEADERS,
            data={"client_id": CLIENT_ID, "document_type": doc["type"],
                  "financial_year": doc["year"], "nature": doc["nature"]},
            files={"file": (filename, f)})

    if resp.status_code != 201:
        print(f"  UPLOAD FAILED: {resp.status_code} {resp.text[:200]}")
        results.append({"label": doc["label"], "status": "upload_failed"})
        continue

    doc_id = resp.json()["id"]
    print(f"  doc_id={doc_id}")

    # Trigger extraction
    resp = requests.post(f"{BASE}/api/documents/{doc_id}/extract", headers=HEADERS)
    if resp.status_code not in (200, 202):
        print(f"  EXTRACT FAILED: {resp.status_code}")
        results.append({"label": doc["label"], "doc_id": doc_id, "status": "trigger_failed"})
        continue

    task_id = resp.json().get("task_id", "")

    # Poll (MAX 150 = 5 min at 2s intervals)
    MAX_POLLS = 150
    status = "unknown"
    for poll in range(MAX_POLLS):
        time.sleep(2)
        resp = requests.get(f"{BASE}/api/tasks/{task_id}", headers=HEADERS)
        if resp.status_code == 200:
            status = resp.json().get("status", "")
            if status in ("completed", "complete", "failed"):
                print(f"  Extraction {status} ({poll*2}s)")
                break
        if poll % 15 == 0 and poll > 0:
            print(f"  Polling... {poll*2}s")
    else:
        print(f"  TIMEOUT after {MAX_POLLS*2}s")
        status = "timeout"

    # Fetch items
    resp = requests.get(f"{BASE}/api/documents/{doc_id}/extraction", headers=HEADERS)
    items = resp.json() if resp.status_code == 200 else []
    count = len(items) if isinstance(items, list) else 0
    print(f"  Items: {count}")

    results.append({"label": doc["label"], "doc_id": doc_id, "task_id": task_id,
                     "year": doc["year"], "status": status, "item_count": count})

# Save
with open("test-results/company-1/extraction-results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\\n=== EXTRACTION SUMMARY ===")
total = sum(r.get("item_count", 0) for r in results)
for r in results:
    print(f"  {r['label']}: {r.get('item_count','N/A')} items ({r['status']})")
print(f"  TOTAL: {total} items")
```

### Step 4: Gate Check

- Any scanned PDF must produce > 30 items (HARD GATE — if less, OCR failed)
- Total items across all docs > 100 (SOFT GATE — continue with warning)
- No documents in "failed" or "timeout" status

If HARD GATE fails: STOP. Write failure to status.json and exit.

### Step 5: Verify All Extractions

```bash
for DOC_ID in {{id1}} {{id2}} {{id3}}; do
  curl -s -X POST "http://localhost:8000/api/documents/$DOC_ID/extraction/verify" \
    -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
    -H "X-User-Role: admin"
  echo " verified: $DOC_ID"
done
```

### Step 6: Trigger Classification

```bash
for DOC_ID in {{id1}} {{id2}} {{id3}}; do
  resp=$(curl -s -X POST "http://localhost:8000/api/documents/$DOC_ID/classify" \
    -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
    -H "X-User-Role: admin")
  echo "Classification triggered: $DOC_ID -> $resp"
done
```

Poll each task (MAX 150 polls, 2s intervals). Classification is faster than extraction (~1-2 min per doc).

### Step 7: Review Classification Results

```python
import requests, json

BASE = "http://localhost:8000"
HEADERS = {"X-User-Id": "00000000-0000-0000-0000-000000000001", "X-User-Role": "admin"}
DOC_IDS = [{{LIST_OF_DOC_IDS}}]

all_class = []
for did in DOC_IDS:
    resp = requests.get(f"{BASE}/api/documents/{did}/classifications", headers=HEADERS)
    if resp.status_code == 200:
        all_class.extend(resp.json())

confident = [c for c in all_class if c.get("confidence", 0) >= 0.8 and not c.get("is_doubt")]
doubts = [c for c in all_class if c.get("is_doubt")]
methods = {}
for c in all_class:
    m = c.get("classification_method", "unknown")
    methods[m] = methods.get(m, 0) + 1

print(f"Total: {len(all_class)} | Confident: {len(confident)} | Doubts: {len(doubts)}")
print(f"Methods: {methods}")

with open("test-results/company-1/classification-results.json", "w") as f:
    json.dump(all_class, f, indent=2, default=str)
```

### Step 8: Resolve Doubts Using Golden CMA

For EACH doubt item:
1. Read its description from classification results
2. Search golden-cma-snapshot.json for where this item belongs
3. Resolve via API:

```bash
curl -s -X POST "http://localhost:8000/api/documents/{{DOC_ID}}/classifications/{{CLASS_ID}}/resolve" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
  -H "X-User-Role: admin" \
  -d '{"cma_field_name": "{{FIELD}}", "cma_row": {{ROW}}, "cma_sheet": "input_sheet"}'
```

You are acting as an EMPLOYEE who already knows the correct answers from the golden CMA.
Log every resolution to `test-results/company-1/doubt-resolutions.json`.

### Step 9: Generate CMA Excel

```bash
# Create CMA report
curl -s -X POST "http://localhost:8000/api/clients/$CLIENT_ID/cma-reports" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
  -H "X-User-Role: admin" \
  -d '{"document_ids": [{{DOC_ID_LIST}}], "title": "{{COMPANY_1_NAME}} Test"}'

# Generate Excel (after all doubts resolved)
curl -s -X POST "http://localhost:8000/api/cma-reports/$REPORT_ID/generate" \
  -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
  -H "X-User-Role: admin"
```

Poll task, then download generated .xlsm to `test-results/company-1/generated_cma.xlsm`.

### Step 10: Cell-by-Cell Golden Comparison

```python
import xlrd, openpyxl, json

golden = xlrd.open_workbook(r"DOCS\Financials\company-1\{{GOLDEN_CMA_FILENAME}}")
golden_sheet = golden.sheet_by_name("INPUT SHEET") if "INPUT SHEET" in golden.sheet_names() else golden.sheet_by_index(0)

generated = openpyxl.load_workbook("test-results/company-1/generated_cma.xlsm", keep_vba=True)
gen_sheet = generated.worksheets[0]

TOLERANCE = 500  # Rs 500 absolute
comparison = []

for row_idx in range(golden_sheet.nrows):
    label = str(golden_sheet.cell(row_idx, 0).value or "").strip()
    if not label:
        continue
    for col_idx in range(1, golden_sheet.ncols):
        golden_val = golden_sheet.cell(row_idx, col_idx).value
        if golden_val is None or golden_val == "" or golden_val == 0:
            continue
        try:
            golden_abs = float(golden_val) * 100000  # lakhs to absolute
        except (ValueError, TypeError):
            continue

        gen_cell = gen_sheet.cell(row=row_idx+1, column=col_idx+1)
        gen_val = float(gen_cell.value or 0)
        delta = abs(golden_abs - gen_val)

        comparison.append({
            "row": row_idx, "field": label, "col": col_idx,
            "golden_lakhs": golden_val, "golden_abs": golden_abs,
            "generated": gen_val, "delta": delta,
            "match": delta <= TOLERANCE,
            "delta_pct": round(delta / max(abs(golden_abs), 1) * 100, 2)
        })

matches = sum(1 for c in comparison if c["match"])
total = len(comparison)
print(f"Match rate: {matches}/{total} ({matches/total*100:.1f}%)")

mismatches = [c for c in comparison if not c["match"]]
print(f"\\nMISMATCHES ({len(mismatches)}):")
for m in mismatches[:10]:
    print(f"  Row {m['row']} {m['field']}: golden={m['golden_lakhs']}L, gen={m['generated']}, delta={m['delta_pct']}%")

with open("test-results/company-1/comparison-report.json", "w") as f:
    json.dump({"match_rate": matches/max(total,1), "total": total,
               "matches": matches, "mismatches": mismatches, "all": comparison}, f, indent=2)
```

### Step 11: Discover Classification Rules

For EVERY mismatch from Step 10, create a rule:

```json
{
  "id": "C1-A-001",
  "type": "A/B/C/D/E/F",
  "priority": "HIGH/MEDIUM/LOW",
  "source_text": "what the source document said",
  "golden_field": "where golden CMA placed it",
  "golden_row": 42,
  "golden_sheet": "input_sheet",
  "app_classified_as": "where the app placed it",
  "app_row": 67,
  "rule": "Human-readable rule explanation",
  "company": "{{COMPANY_1_NAME}}",
  "industry": "{{INDUSTRY_1}}"
}
```

Save to `test-results/company-1/discovered-rules.json`.

### Step 12: Write Summary + Status

Save `test-results/company-1/SUMMARY.md`:

```markdown
# {{COMPANY_1_NAME}} — Test Report

## Pipeline Results
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Documents processed | N | | |
| Total items extracted | N | >100 | |
| Scanned PDF items | N | >30 | |
| Classification accuracy | N% | >90% | |
| Doubt rate | N% | <15% | |
| Golden match rate | N% | >95% | |
| Silent misclassifications | N | 0 | |
| Rules discovered | N | | |
```

Save `test-results/company-1/status.json`:

```json
{
  "company": "{{COMPANY_1_NAME}}",
  "slug": "company-1",
  "industry": "{{INDUSTRY_1}}",
  "stage": "completed",
  "extraction_items": 0,
  "classification_accuracy": 0.0,
  "golden_match_rate": 0.0,
  "doubt_count": 0,
  "rules_generated": 0,
  "timestamp": "ISO-8601",
  "failure_reason": null
}
```

## Gate Conditions

| Gate | Condition | Action |
|------|-----------|--------|
| Scanned PDF items | < 30 | HARD STOP |
| Total items | < 100 | WARNING, continue |
| Classification accuracy | < 70% | WARNING, continue |
| Golden match | < 60% | WARNING, likely scale issue |

## Cost Safety (NON-NEGOTIABLE)

- MAX 150 polling iterations per task (2s = 5 min)
- 3 consecutive API failures = STOP and record
- Do NOT re-extract successful documents
- Total cost cap: $2 for this company
- NEVER create unbounded loops
```

---

# COMPANY 2 — PIPELINE WINDOW

```
PASTE INTO A NEW CLAUDE CODE WINDOW
────────────────────────────────────
```

```
# CMA Test Agent — {{COMPANY_2_NAME}} ({{INDUSTRY_2}})

[IDENTICAL to Company 1 prompt above, with these replacements:]

- Company name: {{COMPANY_2_NAME}}
- Industry: {{INDUSTRY_2}}
- Slug: company-2
- Output: test-results/company-2/
- Document manifest: fill in with Company 2's files
- Golden CMA: fill in with Company 2's golden file
- Rule prefix: "C2-" (e.g., C2-A-001)

[Copy the full Company 1 Pipeline prompt and replace all instances of:
  company-1 → company-2
  {{COMPANY_1_NAME}} → {{COMPANY_2_NAME}}
  {{INDUSTRY_1}} → {{INDUSTRY_2}}
  C1- → C2-
]
```

---

# COMPANY 3 — PIPELINE WINDOW

```
Same structure. Replace: company-3, {{COMPANY_3_NAME}}, {{INDUSTRY_3}}, C3-
```

# COMPANY 4 — PIPELINE WINDOW

```
Same structure. Replace: company-4, {{COMPANY_4_NAME}}, {{INDUSTRY_4}}, C4-
```

# COMPANY 5 — PIPELINE WINDOW

```
Same structure. Replace: company-5, {{COMPANY_5_NAME}}, {{INDUSTRY_5}}, C5-
```

# COMPANY 6 — PIPELINE WINDOW

```
Same structure. Replace: company-6, {{COMPANY_6_NAME}}, {{INDUSTRY_6}}, C6-
```

# COMPANY 7 — PIPELINE WINDOW

```
Same structure. Replace: company-7, {{COMPANY_7_NAME}}, {{INDUSTRY_7}}, C7-
```

---

# ============================================================
# OCR COMPARISON PROMPTS (one per company — 7 total)
# ============================================================

# COMPANY 1 — OCR WINDOW

> Open AFTER Company 1's Pipeline window completes (needs extraction results).

```
PASTE INTO A NEW CLAUDE CODE WINDOW
────────────────────────────────────
```

```
# CMA OCR Quality Agent — {{COMPANY_1_NAME}}

> You independently read this company's scanned financial documents
> and compare YOUR extraction against what the app (Qwen3.5-9B) extracted.
> This measures OCR quality without any API calls.

## System State

Project root: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2
No API calls needed — read-only analysis
Output: test-results/company-1-ocr/

## Company

Name:     {{COMPANY_1_NAME}}
Industry: {{INDUSTRY_1}}
Slug:     company-1

## Input Files

### App's extraction (from pipeline window):
- test-results/company-1/extraction-results.json

### Source scanned PDFs (for YOUR independent reading):
- DOCS/Financials/company-1/{{SCANNED_PDF_1}}
- DOCS/Financials/company-1/{{SCANNED_PDF_2}}
(Only include SCANNED PDFs — skip Excel and digital PDFs)

### Golden CMA (ground truth for amounts):
- DOCS/Financials/company-1/{{GOLDEN_CMA_FILENAME}}

## EXECUTION STEPS

### Step 1: Load App's Extraction

```python
import json
with open("test-results/company-1/extraction-results.json") as f:
    app_results = json.load(f)

# Filter to scanned PDF documents only
scanned_docs = [r for r in app_results if r.get("nature") == "scanned" or "scanned" in r.get("label", "").lower()]
print(f"Scanned docs: {len(scanned_docs)}")
for doc in scanned_docs:
    print(f"  {doc['label']}: {doc.get('item_count', 0)} items")
```

### Step 2: Convert Scanned PDFs to Images

```python
from pdf2image import convert_from_path
import os

os.makedirs("test-results/company-1-ocr/pages", exist_ok=True)

# Convert first 5 pages of each scanned PDF (representative sample)
for pdf_path in [r"DOCS\Financials\company-1\{{SCANNED_PDF_1}}"]:
    images = convert_from_path(pdf_path, dpi=200, first_page=1, last_page=5)
    for i, img in enumerate(images):
        img.save(f"test-results/company-1-ocr/pages/page_{i+1}.jpg", "JPEG")
    print(f"Converted {len(images)} pages from {os.path.basename(pdf_path)}")
```

### Step 3: YOUR Independent Extraction

Read each saved page image using YOUR vision capabilities.
For each page, extract:
- Every financial line item with its description
- The amount (number) for each item
- The scale factor (absolute / in Lakhs / in Crores)
- The section (income / expenses / assets / liabilities)
- Whether amounts are in parentheses (negative)

Use the golden CMA as reference for expected values but do NOT copy from it.
You are doing a genuine independent read of the source document.

Save YOUR extraction to `test-results/company-1-ocr/independent-extraction.json`:
```json
{
  "pages": [
    {
      "page_number": 1,
      "scale_factor": "in_lakhs",
      "items": [
        {"description": "Revenue from Operations", "amount": 67.15, "section": "income"},
        {"description": "Cost of Materials Consumed", "amount": 48.455, "section": "expenses"}
      ]
    }
  ]
}
```

### Step 4: Side-by-Side Comparison

For each page you extracted:
- How many items did the APP find vs how many YOU found?
- Which items did the app MISS?
- Which amounts did the app get WRONG?
- Did the app detect the correct scale factor?

Create a comparison table:

| # | Description | App Amount | Your Amount | Match? | Issue Type |
|---|------------|-----------|-------------|--------|------------|
| 1 | Revenue | 67.15 | 67.15 | YES | — |
| 2 | Raw Materials | 48.45 | 48.455 | CLOSE | Rounding |
| 3 | Factory Rent | MISSING | 1.23 | NO | Missing item |

### Step 5: Error Categorization

| Category | Count | Examples |
|----------|-------|---------|
| Missing item (app didn't find it) | N | |
| Wrong amount (number mismatch) | N | |
| Wrong scale (lakhs vs crores vs absolute) | N | |
| Merged items (app combined two into one) | N | |
| Split items (app split one into two) | N | |
| OCR misread (garbled text/numbers) | N | |
| Extra items (app found, you didn't) | N | |

### Step 6: Calculate Metrics

```
Item Recall     = items_app_found / items_you_found
Amount Accuracy = correct_amounts / items_both_found
Scale Detection = pages_correct_scale / pages_with_scale_header
```

### Step 7: Cross-Reference with Golden CMA

For items the app MISSED — check if they appear in the golden CMA.
If a missed item IS in the golden CMA, it's a critical OCR gap.
If a missed item is NOT in the golden CMA, it may be intentionally excluded.

### Step 8: Qwen3.5-9B Quality Verdict

Based on your analysis:
- Is Qwen3.5-9B ($0.05/M) adequate for this company's documents?
- Would upgrading to Qwen3.5-122B ($0.26/M) improve quality enough to justify 5x cost?
- Are there specific page types (Notes, Schedules, Balance Sheet) where OCR struggles?

### Output

Save to `test-results/company-1-ocr/OCR-REPORT.md`:

```markdown
# OCR Quality Report — {{COMPANY_1_NAME}}

## Summary
| Metric | Value |
|--------|-------|
| Pages analyzed | N |
| Item recall | N% |
| Amount accuracy | N% |
| Scale detection | N% |
| Critical misses (in golden CMA) | N |

## Error Breakdown
[table from Step 5]

## Specific Failures
[list each missed/wrong item with page reference]

## Verdict
Qwen3.5-9B: ADEQUATE / NEEDS UPGRADE / CRITICAL ISSUES
Recommendation: [keep 9B / upgrade to 122B / specific prompt changes needed]
```

## Cost Safety
- ZERO OpenRouter API calls
- Only reads saved files + uses your built-in vision
- No cost risk whatsoever
```

---

# COMPANY 2-7 — OCR WINDOWS

```
For each company 2-7, copy the Company 1 OCR prompt and replace:
  company-1 → company-N
  company-1-ocr → company-N-ocr
  {{COMPANY_1_NAME}} → {{COMPANY_N_NAME}}
  {{SCANNED_PDF_1}} → that company's scanned PDF files
```

---

# ============================================================
# RULE COMBINER WINDOW (runs after all 7 pipelines complete)
# ============================================================

```
PASTE INTO A NEW CLAUDE CODE WINDOW
────────────────────────────────────
```

```
# CMA Rule Combiner — All 7 Companies

> You merge classification rules from all 7 company tests.
> ZERO API calls. Pure analysis.

## System State

Project root: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2
Output: test-results/rules-combined/

## Input Files

Read discovered-rules.json from ALL 7 companies:
- test-results/company-1/discovered-rules.json
- test-results/company-2/discovered-rules.json
- test-results/company-3/discovered-rules.json
- test-results/company-4/discovered-rules.json
- test-results/company-5/discovered-rules.json
- test-results/company-6/discovered-rules.json
- test-results/company-7/discovered-rules.json

Also read existing rules from prior test runs:
- test-results/TEST_REPORT.md (Mehta v1 — 12 rules, A-001 through D-001)
- test-results/dynamic-air-v2/discovered-rules.json (if exists)
- test-results/mehta-computers-v2/discovered-rules.json (if exists)

## Tasks

### Task 1: Load & Count All Rules
Read every discovered-rules.json. Print total count per company.

### Task 2: Deduplicate
Two rules are duplicates if same source_text pattern → same CMA field.
Keep the version with more context.

### Task 3: Score by Agreement

| Agreement | Classification | Action |
|-----------|---------------|--------|
| 5+ companies agree | UNIVERSAL RULE | Add to rule_engine.py immediately |
| 3-4 companies agree | STRONG RULE | Add with high confidence |
| Same industry agrees | INDUSTRY RULE | Add with industry condition |
| 1 company only | COMPANY-SPECIFIC | Log, don't add |

### Task 4: Detect Conflicts
Same source text → different CMA fields for SAME industry = CONFLICT.
Same source text → different CMA fields for DIFFERENT industries = OK (industry rule).

### Task 5: Format for Rule Engine

Read `backend/app/services/classification/rule_engine.py` to understand the expected format.
Convert universal + strong rules into that format.

### Task 6: Generate learned_mappings for Supabase

```json
[
  {
    "source_text_pattern": "Purchase @ %",
    "cma_field_name": "Raw Materials Consumed (Indigenous)",
    "cma_row": 42,
    "cma_sheet": "input_sheet",
    "industry": "trading",
    "confidence": 0.95,
    "source": "golden_comparison",
    "agreement_count": 5
  }
]
```

### Output Files

- test-results/rules-combined/all-rules.json — every unique rule
- test-results/rules-combined/universal-rules.json — 5+ agreement
- test-results/rules-combined/industry-rules.json — industry-specific
- test-results/rules-combined/conflicts.json — contradictions
- test-results/rules-combined/learned-mappings-import.json — DB-ready
- test-results/rules-combined/RULE-SUMMARY.md
```

---

# ============================================================
# FINAL REPORT WINDOW (runs last)
# ============================================================

```
PASTE INTO A NEW CLAUDE CODE WINDOW
────────────────────────────────────
```

```
# CMA Test Harness — Final Report

> Aggregate all 7 company results + 7 OCR reports + combined rules
> into a single master dashboard.

## System State

Project root: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2
Output: test-results/FINAL-REPORT.md

## Input

Read status.json from all 7 companies:
- test-results/company-{1..7}/status.json

Read OCR reports:
- test-results/company-{1..7}-ocr/OCR-REPORT.md

Read combined rules:
- test-results/rules-combined/RULE-SUMMARY.md

## Generate This Report

```markdown
# CMA Automation V1 — Full Test Report (7 Companies)

## Overall Dashboard
| Company | Industry | Items | Classification % | Golden Match % | Doubt % | Rules | OCR Verdict | Status |
|---------|----------|-------|-------------------|----------------|---------|-------|-------------|--------|
| {{C1}} | {{I1}} | N | N% | N% | N% | N | OK/UPGRADE | PASS/FAIL |
| ... x7 | | | | | | | | |
| **AVG** | | | **N%** | **N%** | **N%** | **N** | | |

## Cross-Company Patterns

### Systemic Errors (appear in 3+ companies)
[List patterns that fail consistently]

### Industry-Specific (Trading vs Manufacturing vs Services)
[Compare accuracy between industry types]

### Extraction Quality by Document Type
| Doc Type | Avg Items | Recall | Issues |
|----------|-----------|--------|--------|
| Excel | N | N% | |
| Digital PDF | N | N% | |
| Scanned PDF | N | N% | |

## OCR Model Verdict
- Companies where Qwen3.5-9B was adequate: N/7
- Companies needing upgrade to larger model: N/7
- Common OCR failure patterns: [list]

## Classification Rules Summary
- Total unique rules: N
- Universal (5+ agreement): N → auto-import to rule_engine.py
- Industry-specific: N → import with industry condition
- Conflicts needing human review: N
- Company-specific (skip): N

## Unwritten Rules Discovered
[The rules your father's firm follows but never documented]
[Ranked by importance — universal rules first]

## Recommendations
1. [Most impactful fix]
2. [Second most impactful]
3. ...

## Cost Report
| Company | OCR Tokens | Classification Tokens | Est. Cost |
|---------|-----------|----------------------|-----------|
| ... x7 | | | |
| **TOTAL** | | | **$N** |
```

## Final Deliverables Checklist
- [ ] All 7 company SUMMARY.md files exist
- [ ] All 7 OCR-REPORT.md files exist
- [ ] rules-combined/RULE-SUMMARY.md exists
- [ ] FINAL-REPORT.md written
- [ ] learned-mappings-import.json ready for DB import
```

---

## Quick-Fill Guide

When you get the 7 company files, here's exactly what to do:

### For EACH company:

1. Create folder: `DOCS/Financials/company-N/FY22/`, `FY23/`, `FY24/`
2. Drop PDFs/Excel files into the year folders
3. Drop golden CMA into `DOCS/Financials/company-N/`
4. In the Pipeline prompt, fill in:
   - `{{COMPANY_N_NAME}}` → actual company name
   - `{{INDUSTRY_N}}` → manufacturing / trading / services
   - Document manifest table → list each file with year and type
   - `{{GOLDEN_CMA_FILENAME}}` → actual filename
5. In the OCR prompt, fill in:
   - `{{SCANNED_PDF_1}}` → only the SCANNED PDFs (not Excel/digital)
6. Open the window and paste

### Time estimate per company: ~20-30 min (pipeline) + ~10 min (OCR)
### Cost estimate per company: ~Rs 9 ($0.11) on OpenRouter
### Total for 7 companies: ~Rs 63 ($0.75)
