# Agent 5: Excel Generation & Validation

## Your Job
Generate the CMA Excel file from the classified data, download it, and compare it row-by-row against the existing human-prepared CMA (`CMA Dynamic 23082025.xls`).

## Inputs Required from Orchestrator
- REPORT_ID (from Agent 3)

## System State
- Backend: http://localhost:8000
- Auth headers: `X-User-Id: 00000000-0000-0000-0000-000000000001`, `X-User-Role: admin`

## Step 1: Resolve All Doubt Items (Optional but Recommended)

Before generating, check if there are high-confidence doubt items that can be auto-resolved:
```bash
curl -s http://localhost:8000/api/cma-reports/$REPORT_ID/doubts \
  -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
  -H "X-User-Role: admin" \
  | python -c "import sys,json; items=json.load(sys.stdin); print(f'Doubt items: {len(items)}')"
```

If > 50 doubt items: proceed anyway — they'll appear in the report as blanks or best-guess values.

## Step 2: Generate CMA Excel

```bash
curl -s -X POST http://localhost:8000/api/cma-reports/$REPORT_ID/generate \
  -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
  -H "X-User-Role: admin" \
  | python -m json.tool
```

Poll until complete:
```python
import requests, time
BASE = "http://localhost:8000"
HEADERS = {"X-User-Id": "00000000-0000-0000-0000-000000000001", "X-User-Role": "admin"}

for _ in range(60):  # Max 10 minutes
    resp = requests.get(f"{BASE}/api/cma-reports/{REPORT_ID}", headers=HEADERS)
    status = resp.json().get("generation_status", "")
    print(f"Generation status: {status}")
    if status in ("completed", "failed"):
        break
    time.sleep(10)
```

## Step 3: Download the Generated CMA

```bash
curl -s -o "test-results/dynamic/generated_dynamic_cma.xlsm" \
  http://localhost:8000/api/cma-reports/$REPORT_ID/download \
  -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
  -H "X-User-Role: admin"

# Verify file was downloaded
ls -lh test-results/dynamic/generated_dynamic_cma.xlsm
```

Expected: File size > 50 KB (CMA template + data)

## Step 4: Read Generated CMA and Compare

```python
import openpyxl, xlrd, json

# Read generated CMA
gen_wb = openpyxl.load_workbook(
    r"test-results\dynamic\generated_dynamic_cma.xlsm",
    keep_vba=True, data_only=True
)
print("Generated CMA sheets:", gen_wb.sheetnames)

# Find INPUT SHEET
gen_ws = None
for name in gen_wb.sheetnames:
    if "INPUT" in name.upper():
        gen_ws = gen_wb[name]
        print(f"Found input sheet: {name}")
        break

if gen_ws is None:
    print("ERROR: No INPUT SHEET found in generated CMA")
    exit(1)

# Read original CMA for comparison
orig_wb = xlrd.open_workbook(r"DOCS\Financials\CMA Dynamic 23082025.xls")
print("Original CMA sheets:", orig_wb.sheet_names())

# Find INPUT SHEET in original
orig_ws = None
for name in orig_wb.sheet_names():
    if "INPUT" in name.upper():
        orig_ws = orig_wb.sheet_by_name(name)
        print(f"Found original input sheet: {name}")
        break

# Determine column mapping (B=FY22, C=FY23, D=FY24, E=FY25 typically)
# Verify by reading the header row
print("\nGenerated CMA - First 5 rows:")
for row in gen_ws.iter_rows(min_row=1, max_row=5, values_only=True):
    print(row)

print("\nOriginal CMA - First 5 rows:")
for i in range(5):
    print(orig_ws.row_values(i))
```

### Row-by-Row Comparison

```python
# Key rows to validate (row numbers in CMA INPUT SHEET — 1-indexed)
KEY_ROWS = {
    22: "Domestic Sales",
    23: "Export Sales",
    42: "Raw Materials (Indigenous)",
    45: "Factory Wages",
    48: "Power, Coal, Fuel",
    49: "Other Manufacturing Expenses",
    56: "Depreciation (Manufacturing)",
    67: "Salary and Staff",
    68: "Rent, Rates and Taxes",
    83: "Interest on Term Loans",
    85: "Bank Charges",
    167: "Sundry Debtors",
    242: "Sundry Creditors",
}

YEARS = {"FY22": 1, "FY23": 2, "FY24": 3, "FY25": 4}  # col offset from col B (index 1)

results = []
for row_num, field_name in KEY_ROWS.items():
    row_idx = row_num - 1  # 0-indexed for xlrd
    for year, col_offset in YEARS.items():
        # Get original value
        try:
            orig_val = float(orig_ws.cell_value(row_idx, col_offset) or 0)
        except:
            orig_val = 0.0

        # Get generated value
        try:
            gen_cell = gen_ws.cell(row=row_num, column=col_offset + 1)  # 1-indexed + B offset
            gen_val = float(gen_cell.value or 0)
        except:
            gen_val = 0.0

        if orig_val == 0 and gen_val == 0:
            status = "N/A"
            diff_pct = 0
        elif orig_val == 0:
            status = "⚠️ UNEXPECTED"
            diff_pct = 100
        else:
            diff_pct = abs(gen_val - orig_val) / abs(orig_val) * 100
            if diff_pct < 1:
                status = "✅ MATCH"
            elif diff_pct < 10:
                status = "⚠️ CLOSE"
            else:
                status = "❌ MISMATCH"

        results.append({
            "row": row_num, "field": field_name, "year": year,
            "original": orig_val, "generated": gen_val,
            "diff_pct": diff_pct, "status": status
        })
        print(f"R{row_num} {field_name} {year}: orig={orig_val:.5f} gen={gen_val:.5f} {status}")

# Summary
matches = sum(1 for r in results if r["status"] == "✅ MATCH")
total_non_na = sum(1 for r in results if r["status"] != "N/A")
print(f"\nOverall: {matches}/{total_non_na} rows match within 1% = {100*matches/total_non_na:.1f}%")
```

## Step 5: Verify VBA/Macros Preserved

```bash
# File must be .xlsm (not .xlsx) and contain VBA
python -c "
import openpyxl
wb = openpyxl.load_workbook(r'test-results\dynamic\generated_dynamic_cma.xlsm', keep_vba=True)
print('VBA present:', wb.vba_archive is not None)
print('Extension check: should be .xlsm')
"
```

## Scale Normalization Note
The CMA Dynamic file likely uses **lakhs** (values like 12.5 = ₹12.5 lakhs = ₹12,50,000).
The app may store values in **absolute rupees** (1250000).
Before comparison, normalize: divide app values by 100,000 if they appear to be in absolute form.

Detection heuristic:
```python
# If generated values are ~100,000x larger than original → app uses absolute, original uses lakhs
sample_gen = gen_ws.cell(row=22, column=2).value  # Domestic Sales FY22
sample_orig = float(orig_ws.cell_value(21, 1))    # Same cell in original
if sample_gen and sample_orig and abs(sample_gen / sample_orig) > 10000:
    print("SCALE MISMATCH: dividing generated values by 100000 (absolute → lakhs)")
    SCALE_FACTOR = 100000
else:
    SCALE_FACTOR = 1
```

## Output File
Write to `test-results/dynamic/agent5-excel.md`:

```markdown
# Agent 5: Excel Generation & Validation

## File Generated
- Path: test-results/dynamic/generated_dynamic_cma.xlsm
- Size: N KB
- VBA preserved: ✅/❌
- Sheets found: [list]

## Scale
- Original CMA scale: lakhs / absolute
- Generated CMA scale: lakhs / absolute
- Scale factor applied: N

## Row-by-Row Comparison (Key Rows)
| Row | Field | FY22 Orig | FY22 Gen | FY22 | FY24 Orig | FY24 Gen | FY24 |
|-----|-------|-----------|----------|------|-----------|----------|------|
| R22 | Domestic Sales | N | N | ✅ | N | N | ✅ |
...

## Overall Score
- Rows matched within 1%: N/N (N%)
- Rows within 10%: N/N (N%)
- Rows mismatched > 10%: N
```

## Gate Condition
- PASS if ≥ 80% of non-zero key rows match within 1%
- WARNING if 60-79%
- FAIL if < 60% — classification or Excel generation has a significant bug
