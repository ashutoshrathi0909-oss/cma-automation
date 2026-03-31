# Claude Extraction & Rule Discovery — Master Prompt

> **Purpose:** Claude reads EVERY source financial document (Excel, digital PDF, scanned PDF),
> extracts ALL line items into structured JSON organized by CMA rows,
> then compares against the golden CMA to generate classification rules.
>
> **This is NOT the app pipeline.** Claude does the extraction directly — no API calls.
> The output becomes ground truth for comparing against the app later.

---

## How to Use

1. For each company, copy the **full prompt below** into a new Claude Code window
2. Fill in ALL `{{PLACEHOLDERS}}` with actual values
3. Paste and let it run — Claude handles everything autonomously
4. Output lands in `test-results/{{SLUG}}-extraction/`

---

# ════════════════════════════════════════════════════════════════
# FULL EXTRACTION PROMPT — Copy everything below this line
# ════════════════════════════════════════════════════════════════

```
# CMA Extraction Agent — {{COMPANY_NAME}} ({{INDUSTRY}})

> READ THIS ENTIRE PROMPT BEFORE DOING ANYTHING.
>
> You are a SENIOR CHARTERED ACCOUNTANT with 20 years of experience preparing CMA reports.
> Your job: read EVERY source financial document for this company, extract EVERY financial
> line item, map each item to the correct CMA INPUT SHEET row, and compare your mapping
> against the golden CMA to discover classification rules.
>
> You do NOT call any API. You read files directly and produce structured output.

## System State

Project root: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2
Output folder: test-results/{{SLUG}}-extraction/
No API calls — read-only analysis + file writing only.

## Company Profile

| Field | Value |
|-------|-------|
| Name | {{COMPANY_NAME}} |
| Industry | {{INDUSTRY}} (manufacturing / trading / services) |
| Slug | {{SLUG}} |
| Financial Years | {{FY_YEARS}} (e.g., FY22, FY23, FY24) |
| Golden CMA Path | DOCS/Financials/{{SLUG}}/{{GOLDEN_CMA_FILENAME}} |

## Source Documents

Base path: DOCS/Financials/{{SLUG}}/

| # | File | Subfolder | Year | Format | Notes |
|---|------|-----------|------|--------|-------|
| 1 | {{FILE_1}} | {{SUBFOLDER}} | {{YEAR}} | Excel / Digital PDF / Scanned PDF | |
| 2 | {{FILE_2}} | {{SUBFOLDER}} | {{YEAR}} | Excel / Digital PDF / Scanned PDF | |
| 3 | {{FILE_3}} | {{SUBFOLDER}} | {{YEAR}} | Excel / Digital PDF / Scanned PDF | |
| ... | ... | ... | ... | ... | |

### Documents to SKIP (do NOT read)
- Auditor Report / Directors Report — narrative text, no financial data
- Form 3CA / 3CB / 3CD — tax compliance forms
- Advance Tax challans / receipts
- EMI schedules, sanction letters, bank statements
- Any non-financial correspondence or letters

---

## CMA INPUT SHEET — ROW REFERENCE

Use this table to map EVERY extracted item to the correct CMA row.
If an item doesn't fit any row, use the closest "Others" row for its section.

### P&L Section

| Row | CMA Field | Section | Industry Notes |
|-----|-----------|---------|----------------|
| **22** | **Domestic Sales** | income | All |
| 23 | Export Sales | income | All |
| 25 | Less: Excise Duty and Cess | income | Legacy |
| 29 | Dividends received | income | Investments |
| **30** | **Interest Received** | income | Bank interest on INCOME side → here, NOT row 85 |
| 31 | Profit on sale of fixed assets/investments | income | One-time |
| 32 | Gain on Exchange Fluctuations | income | Forex |
| 33 | Extraordinary income | income | One-time items |
| 34 | Others (Non-Operating Income) | income | Catch-all for misc income |
| 41 | Raw Materials Consumed (Imported) | expenses | Manufacturing only |
| **42** | **Raw Materials Consumed (Indigenous)** | expenses | Trading: "Purchases" go here. Mfg: raw materials |
| 43 | Stores and Spares (Imported) | expenses | Manufacturing |
| 44 | Stores and Spares (Indigenous) | expenses | Manufacturing |
| **45** | **Wages** | expenses | FACTORY wages only (Mfg). Trading companies: 0 |
| 46 | Processing / Job Work Charges | expenses | Outsourced manufacturing |
| **47** | **Freight and Transportation** | expenses | Carriage inward/outward, freight, packing |
| **48** | **Power, Coal, Fuel and Water** | expenses | Manufacturing. Electricity, diesel, water |
| 49 | Others (Manufacturing) | expenses | Catch-all for mfg expenses |
| 50 | Repairs & Maintenance (Mfg) | expenses | Factory repairs |
| 51 | Security Service Charges | expenses | Facility security |
| 53 | Stock in Process — Opening | expenses | WIP inventory |
| 54 | Stock in Process — Closing | expenses | WIP inventory (usually negative) |
| **56** | **Depreciation (Manufacturing)** | expenses | Factory asset depreciation |
| 58 | Finished Goods — Opening | expenses | FG inventory |
| 59 | Finished Goods — Closing | expenses | FG inventory (usually negative) |
| 63 | Depreciation (CMA general) | expenses | Non-factory depreciation |
| 64 | Other Manufacturing Expenses | expenses | Catch-all |
| **67** | **Salary and Staff Expenses** | expenses | ADMIN/OFFICE staff (not factory wages) |
| 68 | Rent, Rates and Taxes | expenses | Office rent, property tax |
| 69 | Bad Debts | expenses | Write-offs |
| 70 | Advertisements and Sales Promotions | expenses | Marketing |
| **71** | **Others (Admin)** | expenses | Catch-all for admin/office expenses |
| 72 | Repairs & Maintenance (Admin) | expenses | Office repairs |
| 73 | Audit Fees & Directors Remuneration | expenses | Professional fees |
| 75 | Miscellaneous Expenses written off | expenses | Amortized items |
| 76 | Deferred Revenue Expenditures | expenses | Amortization |
| 77 | Other Amortisations | expenses | Amortization |
| **83** | **Interest on Term Loans** | expenses | Long-term borrowing interest |
| **84** | **Interest on Working Capital** | expenses | CC/OD interest. Trading: unqualified "Interest Paid" → here |
| **85** | **Bank Charges** | expenses | Bank fees, LC charges. NOT "Bank Interest" income |
| 89 | Loss on sale of fixed assets | expenses | One-time |
| 90 | Sundry Balances Written off | expenses | Write-offs |
| 91 | Loss on Exchange Fluctuations | expenses | Forex loss |
| 92 | Extraordinary losses | expenses | One-time |
| 93 | Others (Non-Operating Expenses) | expenses | Catch-all |
| 99 | Income Tax provision | expenses | Tax |
| 100 | Deferred Tax Liability | expenses | Tax timing |
| 101 | Deferred Tax Asset | expenses | Tax timing |
| **104** | **Net Profit after Tax** | computed | PAT — calculated, verify only |

### Balance Sheet Section

| Row | CMA Field | Section | Notes |
|-----|-----------|---------|-------|
| 116 | Paid-up Capital | equity | Share capital |
| 117 | Share Application Money | equity | |
| 121 | General Reserve | equity | |
| 122 | Share Premium | equity | |
| 123 | Revaluation Reserve | equity | |
| 125 | Other Reserves | equity | Surplus, retained earnings |
| 131 | Working Capital Bank Finance — Fund Based | liabilities | CC/OD limits |
| 132 | Working Capital Bank Finance — Non-Fund Based | liabilities | LC/BG limits |
| 136 | Term Loan — Current portion | liabilities | Due within 1 year |
| 137 | Term Loan — Non-current portion | liabilities | Due after 1 year |
| 140 | Debentures — Current | liabilities | |
| 141 | Debentures — Non-current | liabilities | |
| 152 | Unsecured Loans (Quasi Equity) | liabilities | Directors/promoters |
| 153 | Unsecured Loans — Long-term | liabilities | |
| 154 | Unsecured Loans — Short-term | liabilities | |
| **162** | **Gross Block** | assets | Total fixed assets at cost. Vehicles ALWAYS here |
| 163 | Less: Accumulated Depreciation | assets | Negative |
| 165 | Capital Work in Progress | assets | Under-construction assets |
| 169 | Patents / Goodwill / Copyrights | assets | Intangibles |
| 182 | Govt/Trust Securities (non-current) | assets | Investments |
| 183 | Other Investments (non-current) | assets | |
| 185 | Govt/Trust Securities (current) | assets | Short-term investments |
| 186 | Other Investments (current) | assets | |
| 188 | Investment in subsidiaries/group | assets | Related party |
| 193 | Raw Material Inventory (Imported) | assets | |
| 194 | Raw Material Inventory (Indigenous) | assets | |
| 200 | Stocks-in-Process | assets | WIP |
| 201 | Finished Goods | assets | |
| 206 | Receivables — Domestic | assets | Debtors < 6 months |
| 207 | Receivables — Export | assets | |
| 208 | Debtors > 6 months | assets | |
| 212 | Cash and Bank Balances | assets | |
| 213 | Fixed Deposits (current) | assets | Short-term FDs |
| 215 | Fixed Deposits (non-current) | assets | Long-term FDs |
| 219 | Advance to Suppliers | assets | |
| 220 | Advance Tax / TDS | assets | |
| 224 | Other Current Assets | assets | Catch-all |
| 232 | Non-current receivables | assets | |
| 237 | Security deposits | assets | Telephone/electricity/GEM deposits |
| 238 | Other non-current assets | assets | |
| **242** | **Sundry Creditors for goods** | liabilities | Trade payables. ALL CAPS vendor names → here |
| 243 | Advance from customers | liabilities | |
| 244 | Provision for Taxation | liabilities | |
| 246 | Other statutory liabilities | liabilities | GST/TDS/PF payable |
| 249 | Creditors for Expenses | liabilities | Expense payables |
| 250 | Other current liabilities | liabilities | Catch-all |
| **260** | **Total Assets** | computed | Verify only — must equal total liabilities+equity |

---

## KNOWN CLASSIFICATION RULES (apply these while mapping)

These rules were discovered from prior testing. Apply them when you encounter matching patterns:

| Rule | Pattern | Maps To | Row | Condition |
|------|---------|---------|-----|-----------|
| A-001 | Purchase @ N% (Local/Inter-State) | Raw Materials (Indigenous) | 42 | Trading only |
| A-002 | Purchases @ N% | Raw Materials (Indigenous) | 42 | Trading only |
| B-001 | Bank Interest + income section | Interest Received | 30 | All industries |
| B-002 | ALL CAPS vendor name + liability section | Sundry Creditors | 242 | Trading |
| B-003 | Interest Paid (unqualified) | Interest on WC loans | 84 | Trading |
| C-001 | Motor Vehicle / Car / Truck / Two Wheeler | Gross Block | 162 | ALL — absolute rule |
| C-002 | Mobile / Laptop / Computer (>= Rs 5000) | Gross Block | 162 | All industries |
| C-002b | Mobile / Laptop / Computer (< Rs 5000) | Others (Admin) | 71 | All industries |
| C-003 | Carriage / Freight / Packing / Loading | Freight & Transportation | 47 | Trading |
| C-004 | Security Deposit / Electricity Deposit | Security deposits | 237 | All industries |
| D-001 | Less: Purchase Return | Raw Materials (NEGATIVE) | 42 | Trading |
| D-002 | Less: Sale Return | Domestic Sales (NEGATIVE) | 22 | All industries |

---

## EXECUTION PHASES

### Phase 1: Setup & File Inventory

```python
import os, json

PROJECT = r"C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2"
COMPANY_DIR = os.path.join(PROJECT, r"DOCS\Financials\{{SLUG}}")
OUTPUT_DIR = os.path.join(PROJECT, r"test-results\{{SLUG}}-extraction")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# List all files
inventory = []
for root, dirs, files in os.walk(COMPANY_DIR):
    for f in files:
        filepath = os.path.join(root, f)
        rel = os.path.relpath(filepath, COMPANY_DIR)
        ext = os.path.splitext(f)[1].lower()
        fmt = "excel" if ext in (".xls", ".xlsx", ".xlsm") else "pdf" if ext == ".pdf" else "other"
        inventory.append({"file": f, "path": rel, "full_path": filepath, "format": fmt, "ext": ext})

# Print inventory
print(f"Company folder: {COMPANY_DIR}")
print(f"Files found: {len(inventory)}")
for item in inventory:
    print(f"  [{item['format'].upper():6}] {item['path']}")

with open(os.path.join(OUTPUT_DIR, "file-inventory.json"), "w") as fp:
    json.dump(inventory, fp, indent=2)
```

After running this, classify each file:
- Which are financial statements (P&L, BS, Notes)?
- Which are scanned vs digital?
- Which years does each cover?
- Which should be SKIPPED (audit reports, tax forms, letters)?

Record your classification decisions.

---

### Phase 2: Extract from Excel Files

For EVERY Excel file that contains financial data, run this script:

```python
import json
try:
    import openpyxl
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "openpyxl"])
    import openpyxl

try:
    import xlrd
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "xlrd"])
    import xlrd

def extract_excel(filepath, year_label):
    """Extract all data from an Excel file into structured format."""
    ext = filepath.lower().split(".")[-1]
    result = {
        "filename": os.path.basename(filepath),
        "year": year_label,
        "format": "excel",
        "sheets": []
    }

    if ext == "xls":
        wb = xlrd.open_workbook(filepath)
        for sheet_name in wb.sheet_names():
            sheet = wb.sheet_by_name(sheet_name)
            sheet_data = {"name": sheet_name, "rows": sheet.nrows, "cols": sheet.ncols, "items": []}
            for row_idx in range(sheet.nrows):
                row_values = []
                for col_idx in range(sheet.ncols):
                    cell = sheet.cell(row_idx, col_idx)
                    if cell.value not in (None, "", 0, 0.0):
                        row_values.append({"col": col_idx, "value": cell.value, "type": cell.ctype})
                if row_values:
                    sheet_data["items"].append({"row": row_idx, "cells": row_values})
            result["sheets"].append(sheet_data)
    else:
        wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            sheet_data = {"name": sheet_name, "rows": sheet.max_row, "cols": sheet.max_column, "items": []}
            for row in sheet.iter_rows(min_row=1, values_only=False):
                row_idx = row[0].row
                row_values = []
                for cell in row:
                    if cell.value not in (None, "", 0, 0.0):
                        row_values.append({"col": cell.column, "value": cell.value,
                                           "type": type(cell.value).__name__})
                if row_values:
                    sheet_data["items"].append({"row": row_idx, "cells": row_values})
            result["sheets"].append(sheet_data)
        wb.close()

    return result

# ─── Run for each Excel file ───
# Modify these paths for your actual files:
excel_files = [
    (r"DOCS\Financials\{{SLUG}}\{{EXCEL_FILE_1}}", "{{YEAR}}"),
    # Add more Excel files here...
]

all_excel = []
for fpath, year in excel_files:
    full = os.path.join(PROJECT, fpath)
    print(f"\nExtracting: {fpath}")
    data = extract_excel(full, year)
    all_excel.append(data)
    for s in data["sheets"]:
        print(f"  Sheet '{s['name']}': {len(s['items'])} non-empty rows")

with open(os.path.join(OUTPUT_DIR, "excel-raw-extraction.json"), "w") as fp:
    json.dump(all_excel, fp, indent=2, default=str)

print(f"\nSaved to {OUTPUT_DIR}/excel-raw-extraction.json")
```

After running the script, READ the output JSON and manually identify:
- Which cells contain descriptions vs amounts
- Which rows are headers vs data vs totals
- The scale factor (look for "in Lakhs" / "in Crores" / "(Rs.)" headers)
- The financial year for each column

---

### Phase 3: Extract from PDF Files

For EVERY PDF file (digital or scanned):

#### 3A: Try reading directly first

Use the Read tool to open each PDF file. The Read tool supports PDFs.

```
Read: DOCS/Financials/{{SLUG}}/{{PDF_FILE}}
```

If the PDF is digital (searchable text), you'll see the text content.
Extract every financial line item you find.

#### 3B: If scanned (images only), convert to images

```python
try:
    from pdf2image import convert_from_path
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "pdf2image"])
    from pdf2image import convert_from_path

import os

pdf_path = os.path.join(PROJECT, r"DOCS\Financials\{{SLUG}}\{{SCANNED_PDF}}")
output_pages = os.path.join(OUTPUT_DIR, "pages")
os.makedirs(output_pages, exist_ok=True)

images = convert_from_path(pdf_path, dpi=200)
for i, img in enumerate(images):
    page_path = os.path.join(output_pages, f"{{SLUG}}_page_{i+1}.jpg")
    img.save(page_path, "JPEG")
    print(f"Saved page {i+1}: {page_path}")

print(f"\nConverted {len(images)} pages. Now read each with the Read tool.")
```

Then use the Read tool on each saved image:
```
Read: test-results/{{SLUG}}-extraction/pages/{{SLUG}}_page_1.jpg
Read: test-results/{{SLUG}}-extraction/pages/{{SLUG}}_page_2.jpg
... (read ALL pages)
```

For EACH page you read, extract:
- Every line item with its description
- The amount (number) — look carefully at Indian number format (1,23,456)
- Parentheses mean NEGATIVE: (1,23,456) = -123456
- The section: income / expenses / assets / liabilities
- The scale factor from the page header ("in Lakhs" / "in Crores" / absolute)
- The financial year (from column headers)

---

### Phase 4: Build the Structured Extraction

After reading ALL documents, create a unified extraction in this EXACT format:

```json
{
  "company": "{{COMPANY_NAME}}",
  "industry": "{{INDUSTRY}}",
  "extracted_by": "claude",
  "extraction_date": "YYYY-MM-DD",
  "documents_read": [
    {"file": "filename.pdf", "format": "scanned_pdf", "pages": 5, "year": "FY24"},
    {"file": "financials.xlsx", "format": "excel", "sheets": 3, "year": "FY24"}
  ],
  "items": [
    {
      "id": 1,
      "description": "Revenue from Operations",
      "original_amount": 67.15,
      "scale": "in_lakhs",
      "amount_absolute": 6715000,
      "section": "income",
      "year": "FY24",
      "source_file": "P&L FY24.pdf",
      "source_page": 1,
      "cma_row": 22,
      "cma_field": "Domestic Sales",
      "mapping_confidence": "high",
      "mapping_rule": null,
      "mapping_reasoning": "Direct revenue from operations = Domestic Sales"
    },
    {
      "id": 2,
      "description": "Purchase @ 18% (Local)",
      "original_amount": 174.13,
      "scale": "in_lakhs",
      "amount_absolute": 17413000,
      "section": "expenses",
      "year": "FY24",
      "source_file": "P&L FY24.pdf",
      "source_page": 2,
      "cma_row": 42,
      "cma_field": "Raw Materials Consumed (Indigenous)",
      "mapping_confidence": "high",
      "mapping_rule": "A-001",
      "mapping_reasoning": "GST-coded purchase → Raw Materials per Rule A-001 (Trading)"
    }
  ]
}
```

### CRITICAL RULES for extraction:
1. **EVERY** non-zero financial line item must be captured — miss NOTHING
2. **Scale normalization**: Always calculate `amount_absolute` = `original_amount * scale_multiplier`
   - "in Lakhs" → multiply by 100,000
   - "in Crores" → multiply by 10,000,000
   - "absolute" or "in Rs." → multiply by 1
3. **Indian number format**: 1,23,456 = 123,456 (lakh system, NOT western)
4. **Parentheses** = negative: (5,67,890) = -567,890
5. **Notes to Accounts**: Extract DETAILED sub-items, NOT just the totals
6. **Multiple years**: If a document shows FY22, FY23, FY24 columns, extract ALL years
7. **Sub-totals**: Extract individual items, NOT sub-totals (unless the sub-total IS the CMA field)

Save to: `test-results/{{SLUG}}-extraction/structured-extraction.json`

---

### Phase 5: Build CMA-Mapped Summary

Now aggregate your extraction into the CMA row structure — this is the format
that's directly comparable to the golden CMA and the app's output:

```json
{
  "company": "{{COMPANY_NAME}}",
  "industry": "{{INDUSTRY}}",
  "cma_mapped": {
    "FY24": {
      "22": {"field": "Domestic Sales", "amount": 6715000, "sources": ["P&L:page1:item1"]},
      "42": {"field": "Raw Materials (Indigenous)", "amount": 17413000, "sources": ["P&L:page2:item2", "P&L:page2:item3"]},
      "45": {"field": "Wages", "amount": 653700, "sources": ["P&L:page2:item7"]},
      "67": {"field": "Salary and Staff Expenses", "amount": 54700, "sources": ["P&L:page3:item12"]},
      "83": {"field": "Interest on Term Loans", "amount": 308400, "sources": ["P&L:page3:item15"]},
      "85": {"field": "Bank Charges", "amount": 13600, "sources": ["P&L:page3:item16"]},
      "162": {"field": "Gross Block", "amount": 5200000, "sources": ["BS:page1:item3"]},
      "242": {"field": "Sundry Creditors", "amount": 845100, "sources": ["BS:page2:item8"]},
      "260": {"field": "Total Assets", "amount": 5250500, "sources": ["BS:page1:computed"]}
    },
    "FY23": {
      "22": {"field": "Domestic Sales", "amount": 0, "sources": []},
      "...": "..."
    }
  }
}
```

**IMPORTANT**: When multiple items map to the SAME CMA row (e.g., several purchase entries all going to Row 42), SUM their amounts and list ALL sources.

Save to: `test-results/{{SLUG}}-extraction/cma-mapped.json`

---

### Phase 6: Read Golden CMA

```python
import json
try:
    import xlrd
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "xlrd"])
    import xlrd

GOLDEN_PATH = os.path.join(PROJECT, r"DOCS\Financials\{{SLUG}}\{{GOLDEN_CMA_FILENAME}}")

wb = xlrd.open_workbook(GOLDEN_PATH)
print(f"Sheets: {wb.sheet_names()}")

# Find INPUT SHEET
sheet_name = "INPUT SHEET" if "INPUT SHEET" in wb.sheet_names() else wb.sheet_names()[0]
sheet = wb.sheet_by_name(sheet_name)

print(f"\nReading '{sheet_name}': {sheet.nrows} rows x {sheet.ncols} cols")

# Detect scale — check row 1-15 for "in Lakhs" or "in Crores"
scale_hint = "unknown"
for r in range(min(15, sheet.nrows)):
    for c in range(sheet.ncols):
        val = str(sheet.cell(r, c).value).lower()
        if "lakh" in val:
            scale_hint = "in_lakhs"
        elif "crore" in val:
            scale_hint = "in_crores"
print(f"Scale hint: {scale_hint}")

# Detect year columns — check row 9 (standard CMA layout)
year_cols = {}
if sheet.nrows > 9:
    for c in range(1, sheet.ncols):
        val = sheet.cell(9, c).value
        if isinstance(val, (int, float)) and 2015 <= val <= 2035:
            year_cols[f"FY{int(val) % 100}"] = c
            print(f"  Column {c}: FY{int(val) % 100}")
        elif isinstance(val, str) and any(str(y) in val for y in range(2015, 2035)):
            for y in range(2015, 2035):
                if str(y) in val:
                    year_cols[f"FY{y % 100}"] = c
                    print(f"  Column {c}: FY{y % 100}")

# If auto-detection failed, check row 8 or manually set:
if not year_cols:
    print("WARNING: Could not auto-detect year columns. Check rows 8-10 manually.")
    # Fallback: print first 12 rows for manual inspection
    for r in range(min(12, sheet.nrows)):
        vals = [sheet.cell(r, c).value for c in range(min(8, sheet.ncols))]
        print(f"  Row {r}: {vals}")

# Extract golden values for KEY CMA rows
KEY_ROWS = [22, 23, 30, 34, 42, 45, 47, 48, 56, 63, 67, 68, 71, 73, 83, 84, 85,
            99, 104, 116, 125, 131, 136, 137, 152, 162, 163, 165, 194, 200, 201,
            206, 212, 224, 237, 242, 246, 249, 250, 260]

golden_data = {"scale": scale_hint, "year_columns": year_cols, "rows": {}}

for r in KEY_ROWS:
    if r >= sheet.nrows:
        continue
    label = str(sheet.cell(r, 0).value or "").strip()
    if not label:
        continue
    row_data = {"field": label, "values": {}}
    for fy, col in year_cols.items():
        val = sheet.cell(r, col).value
        if val not in (None, "", 0, 0.0):
            row_data["values"][fy] = val
    if row_data["values"]:
        golden_data["rows"][str(r)] = row_data

# Also extract ALL non-empty rows (not just key rows)
golden_full = {"scale": scale_hint, "year_columns": year_cols, "all_rows": {}}
for r in range(sheet.nrows):
    label = str(sheet.cell(r, 0).value or "").strip()
    if not label:
        continue
    row_data = {"field": label, "values": {}}
    for fy, col in year_cols.items():
        val = sheet.cell(r, col).value
        if val not in (None, "", 0, 0.0):
            row_data["values"][fy] = val
    if row_data["values"]:
        golden_full["all_rows"][str(r)] = row_data

with open(os.path.join(OUTPUT_DIR, "golden-cma-data.json"), "w") as fp:
    json.dump(golden_full, fp, indent=2, default=str)

print(f"\nGolden CMA: {len(golden_full['all_rows'])} rows with data")
print(f"\nKEY VALUES:")
for r, data in golden_data["rows"].items():
    print(f"  Row {r:>3} | {data['field'][:40]:<40} | {data['values']}")
```

Save to: `test-results/{{SLUG}}-extraction/golden-cma-data.json`

---

### Phase 7: Compare Your Extraction vs Golden CMA

This is the most important step — cell-by-cell comparison.

```python
import json

# Load your extraction
with open(os.path.join(OUTPUT_DIR, "cma-mapped.json")) as f:
    my_extraction = json.load(f)

# Load golden CMA
with open(os.path.join(OUTPUT_DIR, "golden-cma-data.json")) as f:
    golden = json.load(f)

golden_scale = golden["scale"]  # "in_lakhs" or "in_crores"
SCALE_MULT = 100000 if golden_scale == "in_lakhs" else 10000000 if golden_scale == "in_crores" else 1

comparison = []

for fy, fy_data in my_extraction.get("cma_mapped", {}).items():
    for row_str, my_item in fy_data.items():
        my_amount = my_item["amount"]  # in absolute rupees
        golden_row = golden.get("all_rows", {}).get(row_str, {})
        golden_val = golden_row.get("values", {}).get(fy)

        if golden_val is not None:
            golden_abs = float(golden_val) * SCALE_MULT
            delta = abs(my_amount - golden_abs)
            tolerance = max(500, abs(golden_abs) * 0.01)  # Rs 500 or 1%, whichever is larger
            match = delta <= tolerance

            comparison.append({
                "year": fy,
                "row": int(row_str),
                "field": my_item.get("field", golden_row.get("field", "")),
                "my_amount_abs": my_amount,
                "golden_value": golden_val,
                "golden_abs": golden_abs,
                "delta": delta,
                "delta_pct": round(delta / max(abs(golden_abs), 1) * 100, 2),
                "match": match,
                "sources": my_item.get("sources", [])
            })
        elif my_amount != 0:
            # I found something that's NOT in golden CMA
            comparison.append({
                "year": fy,
                "row": int(row_str),
                "field": my_item.get("field", ""),
                "my_amount_abs": my_amount,
                "golden_value": None,
                "golden_abs": 0,
                "delta": abs(my_amount),
                "delta_pct": 100.0,
                "match": False,
                "issue": "EXTRA — not in golden CMA",
                "sources": my_item.get("sources", [])
            })

# Check for golden rows I MISSED
for row_str, golden_row in golden.get("all_rows", {}).items():
    for fy, golden_val in golden_row.get("values", {}).items():
        if golden_val in (None, "", 0, 0.0):
            continue
        # Check if I have this row+year
        my_fy = my_extraction.get("cma_mapped", {}).get(fy, {})
        if row_str not in my_fy:
            comparison.append({
                "year": fy,
                "row": int(row_str),
                "field": golden_row.get("field", ""),
                "my_amount_abs": 0,
                "golden_value": golden_val,
                "golden_abs": float(golden_val) * SCALE_MULT,
                "delta": abs(float(golden_val) * SCALE_MULT),
                "delta_pct": 100.0,
                "match": False,
                "issue": "MISSING — in golden but I didn't extract"
            })

# Sort by year, then row
comparison.sort(key=lambda x: (x["year"], x["row"]))

# Summary
matches = [c for c in comparison if c.get("match")]
mismatches = [c for c in comparison if not c.get("match")]
total = len(comparison)

print(f"=== COMPARISON RESULTS ===")
print(f"Total cells compared: {total}")
print(f"Matches: {len(matches)} ({len(matches)/max(total,1)*100:.1f}%)")
print(f"Mismatches: {len(mismatches)}")

if mismatches:
    print(f"\nMISMATCHES:")
    for m in mismatches:
        issue = m.get("issue", f"delta={m['delta_pct']}%")
        print(f"  {m['year']} Row {m['row']:>3} {m.get('field','')[:35]:<35} | "
              f"Mine={m['my_amount_abs']:>12,.0f} Golden={m['golden_abs']:>12,.0f} | {issue}")

with open(os.path.join(OUTPUT_DIR, "comparison-report.json"), "w") as fp:
    json.dump({
        "total": total,
        "matches": len(matches),
        "mismatches_count": len(mismatches),
        "match_rate": len(matches) / max(total, 1),
        "details": comparison
    }, fp, indent=2)

print(f"\nSaved to comparison-report.json")
```

---

### Phase 8: Discover Classification Rules

For EVERY mismatch, create a rule. This is the most valuable output of the entire process.

**For each mismatch, determine:**

1. **What happened?** — Did the source document say X but the golden CMA put it under Y?
2. **Why?** — What knowledge did the human CA use to make that mapping decision?
3. **Is this a pattern?** — Would this same mapping apply to other companies?
4. **Rule type:**
   - **A (Synonym)**: Different name, same meaning ("Staff Welfare" = "Salary & Staff" Row 67)
   - **B (Context)**: Same name, different mapping based on section/industry ("Interest" → income vs expense)
   - **C (Conditional)**: Amount or other condition determines field (Electronics > Rs 5000 → Gross Block)
   - **D (Aggregation)**: Multiple items net into one CMA field (Purchase Returns negate Raw Materials)
   - **E (Correct Doubt)**: Item genuinely ambiguous — human judgment needed
   - **F (Unwritten Rule)**: Your father's firm follows a convention NOT documented anywhere

**SPECIAL ATTENTION to Type F — Unwritten Rules:**
These are the most valuable discoveries. When the golden CMA maps an item in a way that's
NOT obvious from the description alone, that's an unwritten rule your firm follows.
Example: "Telephone Expenses" → some firms put under "Others (Admin)" Row 71,
but your firm might consistently put under "Rent, Rates and Taxes" Row 68.

Output format for each rule:

```json
{
  "id": "{{SLUG_PREFIX}}-A-001",
  "type": "A",
  "priority": "HIGH",
  "source_text": "Staff Welfare Expenses",
  "source_amount": 54700,
  "source_section": "expenses",
  "year": "FY24",
  "source_file": "P&L FY24.pdf",
  "my_mapping": {"field": "Others (Admin)", "row": 71},
  "golden_mapping": {"field": "Salary and staff expenses", "row": 67},
  "rule": "Staff Welfare Expenses maps to Salary & Staff (Row 67), not Others Admin",
  "reasoning": "Welfare is a staff cost — the CA groups all employee-related expenses under Row 67",
  "industry": "{{INDUSTRY}}",
  "company": "{{COMPANY_NAME}}",
  "is_unwritten_rule": false,
  "applies_to": "all"
}
```

Save ALL rules to: `test-results/{{SLUG}}-extraction/discovered-rules.json`

---

### Phase 9: Items I Could NOT Map (Doubt Items)

For items where you genuinely cannot determine the correct CMA row,
list them separately:

```json
{
  "doubt_items": [
    {
      "description": "Miscellaneous Charges",
      "amount": 12345,
      "year": "FY24",
      "source": "P&L page 4",
      "possible_rows": [
        {"row": 71, "field": "Others (Admin)", "reasoning": "Generic admin expense"},
        {"row": 93, "field": "Others (Non-Operating)", "reasoning": "Could be non-recurring"}
      ],
      "golden_row": 71,
      "golden_field": "Others (Admin)",
      "why_doubtful": "Description too vague to determine without domain knowledge"
    }
  ]
}
```

Save to: `test-results/{{SLUG}}-extraction/doubt-items.json`

---

### Phase 10: Generate Summary Report

Save to `test-results/{{SLUG}}-extraction/EXTRACTION-REPORT.md`:

```markdown
# Extraction Report — {{COMPANY_NAME}} ({{INDUSTRY}})

## Document Inventory
| # | File | Format | Year | Pages/Sheets | Items Extracted |
|---|------|--------|------|-------------|-----------------|
| 1 | ... | Excel | FY24 | 3 sheets | 45 items |
| 2 | ... | Scanned PDF | FY24 | 8 pages | 62 items |
| ... |

## Extraction Summary
| Metric | Value |
|--------|-------|
| Total documents read | N |
| Total line items extracted | N |
| Items mapped to CMA rows | N |
| Doubt items (could not map) | N |
| Financial years covered | FY22, FY23, FY24 |

## Golden CMA Comparison
| Metric | Value |
|--------|-------|
| Total cells compared | N |
| Exact matches | N (N%) |
| Close matches (within 1%) | N (N%) |
| Mismatches | N |
| Items I found but golden CMA doesn't have | N |
| Items in golden CMA that I missed | N |

## Rules Discovered
| # | Type | Rule | Priority |
|---|------|------|----------|
| {{SLUG_PREFIX}}-A-001 | Synonym | "X" = "Y" (Row N) | HIGH |
| {{SLUG_PREFIX}}-B-001 | Context | "X" in income → Row N, in expense → Row M | HIGH |
| ... |

## Unwritten Rules (Type F)
[List any mappings that are clearly firm-specific conventions]

## Scale Factor Notes
- Source documents use: [absolute / lakhs / crores]
- Golden CMA uses: [lakhs]
- Scale conversion verified: [YES/NO]

## Issues & Warnings
[Any problems encountered during extraction]
```

Save status to `test-results/{{SLUG}}-extraction/status.json`:

```json
{
  "company": "{{COMPANY_NAME}}",
  "slug": "{{SLUG}}",
  "industry": "{{INDUSTRY}}",
  "stage": "completed",
  "documents_read": 0,
  "items_extracted": 0,
  "items_mapped": 0,
  "doubt_items": 0,
  "golden_match_rate": 0.0,
  "rules_discovered": 0,
  "unwritten_rules": 0,
  "timestamp": "ISO-8601"
}
```

---

## QUALITY RULES (non-negotiable)

1. **Extract EVERYTHING** — If a number appears in a financial statement, capture it. Miss nothing.
2. **Notes to Accounts are CRITICAL** — They contain the detailed breakdowns. The P&L/BS only shows totals.
   Read Notes carefully and extract EVERY sub-item.
3. **Verify scale factor** — Check EVERY page's header for "in Lakhs" / "in Crores".
   Different pages in the SAME document can have different scales.
4. **Indian number format** — 1,23,456 = 1 lakh 23 thousand 456 = 123,456 in western notation.
5. **Cross-check totals** — After extraction, verify that your extracted sub-items sum to the totals shown.
   If they don't, you missed something.
6. **Manufacturing vs Trading** — Know the difference:
   - Manufacturing: Row 42 = actual raw materials, Row 45 = factory wages, Row 48 = power
   - Trading: Row 42 = purchases (often GST-coded), Row 45 = 0, Row 48 = usually 0
7. **Balance Sheet must balance** — Total Assets (Row 260) must equal Total Liabilities + Equity.
   If it doesn't, investigate.
8. **Negative amounts** — Purchase returns, sale returns, closing stock, accumulated depreciation
   are NEGATIVE. Preserve the sign.
9. **Do NOT guess** — If you can't determine the CMA row for an item, put it in doubt_items.
   NEVER silently assign to "Others" without flagging.
10. **Source traceability** — Every extracted amount must trace back to a specific file + page/cell.
```

---

# ════════════════════════════════════════════════════════════════
# PLACEHOLDER FILL-IN GUIDE
# ════════════════════════════════════════════════════════════════

When company files arrive, fill in these placeholders:

| Placeholder | What to put | Example |
|-------------|-------------|---------|
| `{{COMPANY_NAME}}` | Full legal name | Shree Industries Pvt Ltd |
| `{{INDUSTRY}}` | manufacturing / trading / services | trading |
| `{{SLUG}}` | Short folder name (no spaces) | shree-industries |
| `{{SLUG_PREFIX}}` | Rule ID prefix (2-3 chars) | SI |
| `{{FY_YEARS}}` | Financial years in documents | FY22, FY23, FY24 |
| `{{GOLDEN_CMA_FILENAME}}` | Golden CMA file name | CMA Shree 2025.xls |
| `{{FILE_1}}, {{FILE_2}}...` | Source document file names | P&L FY24.pdf |
| `{{SUBFOLDER}}` | Year subfolder if any | FY24 |
| `{{YEAR}}` | Financial year | FY24 |
| `{{EXCEL_FILE_1}}` | Excel file names (for Phase 2) | financials.xlsx |
| `{{SCANNED_PDF}}` | Scanned PDF names (for Phase 3B) | audit-report.pdf |

---

# ════════════════════════════════════════════════════════════════
# WAVE SCHEDULE (how to run 7 companies)
# ════════════════════════════════════════════════════════════════

```
WAVE 1:  Company 1 + Company 2 + Company 3  (3 parallel windows)
WAVE 2:  Company 4 + Company 5 + Company 6  (3 parallel windows)
WAVE 3:  Company 7                           (1 window)
WAVE 4:  Rule Combiner                       (1 window — needs all 7 done)
```

Total: 9 windows. ~20-40 min per company. Cost: $0 (Claude reads files directly, no API).

---

# ════════════════════════════════════════════════════════════════
# RULE COMBINER PROMPT (run after all 7 companies complete)
# ════════════════════════════════════════════════════════════════

```
# CMA Rule Combiner — All Companies

> Merge classification rules from ALL company extractions.
> Score by agreement level. Generate importable rule sets.

## System State

Project root: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2
Output: test-results/rules-combined/

## Input

Read discovered-rules.json from every completed company:
- test-results/company-1-extraction/discovered-rules.json
- test-results/company-2-extraction/discovered-rules.json
- ... (all available companies)

Also read prior rules:
- test-results/TEST_REPORT.md (Mehta v1 — 12 rules)
- backend/app/services/classification/rule_engine.py (existing rules in code)

## Task 1: Load & Deduplicate

Load all rules. Two rules are duplicates if:
- Same source_text pattern → same CMA field
- Keep the version with more context/reasoning

Print: total rules per company, total unique after dedup.

## Task 2: Score by Agreement

| Agreement Level | Classification | Action |
|-----------------|---------------|--------|
| 5+ companies agree | UNIVERSAL | Add to rule_engine.py |
| 3-4 companies agree | STRONG | Add with high confidence |
| Same industry agrees (2+) | INDUSTRY RULE | Add with industry condition |
| 1 company only | COMPANY-SPECIFIC | Log only, do not add |

## Task 3: Detect Conflicts

Same source_text → different CMA fields:
- Different industries → OK, make it an INDUSTRY RULE with condition
- Same industry → CONFLICT, flag for human review

## Task 4: Identify Unwritten Rules (Type F)

Collect all Type F rules across companies. These are your firm's conventions.
Group by theme:
- How does the firm handle "X" consistently?
- Is there a pattern across industries?
- Would a new employee need to be told this?

## Task 5: Generate Rule Engine Code

Read backend/app/services/classification/rule_engine.py.
For each UNIVERSAL or STRONG rule, write the Python implementation
in the same pattern as existing rules.

Save to: test-results/rules-combined/new-rules-code.py

## Task 6: Generate learned_mappings for Database

For rules that should be learned_mappings (not hard-coded):

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

Save to: test-results/rules-combined/learned-mappings-import.json

## Output Files

- all-rules.json — every unique rule
- universal-rules.json — 5+ agreement
- strong-rules.json — 3-4 agreement
- industry-rules.json — industry-specific
- unwritten-rules.json — Type F (firm conventions)
- conflicts.json — contradictions needing review
- new-rules-code.py — ready to paste into rule_engine.py
- learned-mappings-import.json — ready for Supabase import
- RULE-SUMMARY.md — human-readable summary
```
