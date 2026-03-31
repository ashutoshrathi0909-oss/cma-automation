# SR Papers — Ground Truth Extraction Prompt

Paste this into a **fresh Claude Code window**. It will extract all line items from SR Papers financial files and create a classification ground truth JSON file.

---

## TASK

Create a complete line-item-to-CMA-field mapping for SR Papers by:
1. Reading all 3 source Excel files (FY2023, FY2024, FY2025)
2. Reading the ground truth CMA Excel
3. Cross-referencing amounts to determine correct CMA row for each item
4. Outputting a JSON file matching the BCIPL format

**Do NOT modify any app source code. This is data extraction only.**

---

## COMPANY DETAILS

| Field | Value |
|-------|-------|
| Company | S.R. Papers Private Limited |
| Industry | Trading / Distribution (paper, import-heavy) |
| Entity Type | Private Limited Company |
| Financial Years | FY2023 (Mar 2023), FY2024 (Mar 2024), FY2025 (Mar 2025) |
| Source Unit | Rupees (all 3 files — verify by checking row 1-10 headers for "All amounts in Indian Rupees") |
| Ground Truth CMA Unit | Read cell B13 of INPUT SHEET — expected "In Crs" (crores) |

---

## SOURCE FILES (exact paths from project root)

```
FInancials main/SR Papers/SRPAPERS_2023 - 24 - Updated.xls    → FY2024
FInancials main/SR Papers/SRPAPERS_2024 - 25 - Updated.xls    → FY2025
FInancials main/SR Papers/SRPAPERS_2025-26_-_Updated.xls       → FY2026
```

**IMPORTANT — FILE NAMING IS CONFUSING:** The filenames say "2023-24" but that means FY ending March 2024. Check the actual content to confirm which FY each file covers. The extraction reference says FY2023, FY2024, FY2025 — verify against file contents.

### Ground Truth CMA File
```
FInancials main/SR Papers/CMA S.R.Papers 09032026 v2.xls
```

---

## STEP 1: DISCOVER SHEET NAMES

For each of the 3 source files, list ALL sheet names with row counts:

```python
import xlrd
files = [
    "FInancials main/SR Papers/SRPAPERS_2023 - 24 - Updated.xls",
    "FInancials main/SR Papers/SRPAPERS_2024 - 25 - Updated.xls",
    "FInancials main/SR Papers/SRPAPERS_2025-26_-_Updated.xls",
]
for f in files:
    wb = xlrd.open_workbook(f)
    print(f"\n=== {f.split('/')[-1]} ===")
    for s in wb.sheets():
        print(f"  Sheet: '{s.name}' ({s.nrows} rows)")
```

Print the results — this is critical for understanding the data structure.

---

## STEP 2: READ GROUND TRUTH CMA

Read the ground truth CMA file:
```python
import xlrd
wb = xlrd.open_workbook("FInancials main/SR Papers/CMA S.R.Papers 09032026 v2.xls")
```

1. Find the INPUT SHEET (search for sheet with "input" in name, case-insensitive)
2. Read cell B13 — confirm unit (expected "In Crs")
3. Read rows 17-262, columns A (labels), B, C, D (FY values)
4. Store as a lookup: `{(row_number, column_index): value}`
5. Print the first 15 non-empty values as sanity check

---

## STEP 3: EXTRACT LINE ITEMS FROM EACH SOURCE FILE

### Sheets to INCLUDE:
- **All "Note" sheets** (Note 2, Note 3-17, Note 18-24, etc.)
- **Fixed Asset / Depreciation schedule** (look for "FA", "Deprn", "Depreciation", "Fixed Asset" in sheet name)
- **Any other detail sheets** with line-item breakdowns

### Sheets to EXCLUDE:
- Trial Balance / TB
- Cash Flow
- Deferred Tax / DEFFERED TAX
- Branch Schedule (Note bRANCH SCH) — branch-level splits, not classifiable line items
- BS summary (just totals)
- P&L summary (just totals)
- Any hidden sheets that are clearly working papers
- Pivot / Comparison / Memo sheets

### For each INCLUDED sheet:
1. Iterate all rows
2. Identify **section headers** (rows with text but no numeric amount)
3. For rows with text + numeric amount → this is a line item
4. Record: `raw_text`, `amount`, `section` (current section header), `sheet_name`, `financial_year`

### Unit verification per file:
- Check rows 1-10 for unit indicators ("All amounts in Indian Rupees", "Rs.", "in Lakhs", "in '000s")
- If amounts are 7+ digits → rupees
- If amounts are 2-4 digits → likely lakhs or crores
- SR Papers is expected to be in rupees (verify!)

---

## STEP 4: MAP EACH LINE ITEM TO CMA FIELD

### Reference files to read:
```
backend/app/mappings/cma_field_rows.py                    — 139 valid CMA fields
DOCS/rules/SR_Papers_classification_rules.md              — 22 verified rules for SR Papers
DOCS/extractions/SR_Papers_extraction_reference.md        — Categorized extraction data
```

### Mapping methodology (in priority order):

1. **SR Papers rules file** (22 verified rules) → confidence_note = "verified"
2. **Amount matching**: Convert source amount (rupees) to crores (÷ 10,000,000). Find matching CMA row value within 2% tolerance → confidence_note = "high"
3. **Semantic matching**: Use description + section + sheet to determine CMA field → confidence_note = "high" if clear, "inferred" if ambiguous
4. **Unknown**: If can't determine → confidence_note = "unknown", include with reasoning

### Key SR Papers specifics:
- **Trading company** — no manufacturing. Raw materials = purchased goods for resale
- **Import-heavy** — look for customs duty, CFS charges, import purchases
- Multiple branches — branch schedule is NOT line items, skip it
- Notes 3-17 are BS detail, Notes 18-24 are P&L detail

---

## STEP 5: CREATE OUTPUT FILE

Write to: `DOCS/extractions/SR_Papers_classification_ground_truth.json`

### Format (must match BCIPL format exactly):
```json
[
  {
    "raw_text": "Paper Purchase - Imported",
    "amount_rupees": 123456789.00,
    "financial_year": 2024,
    "section": "note 20 - cost of materials consumed",
    "sheet_name": "Note 18-24",
    "correct_cma_field": "Raw Materials Consumed (Imported)",
    "correct_cma_row": 41,
    "confidence_note": "verified",
    "reasoning": "SR Papers rule SRP-001: Customs Duty on Import -> R41"
  },
  ...
]
```

### Requirements:
- Include ALL leaf-level line items (not subtotals, not headers)
- Skip items with zero or negligible amounts
- Include items from ALL 3 FYs
- Every item must have `sheet_name` (exact Excel sheet name) and `section` (section header within sheet)
- Target: 150+ items minimum (SR Papers has fewer notes than BCIPL, so may be ~150-250)

---

## STEP 6: VALIDATE

After creating the JSON:
1. Count items by FY, by sheet, by confidence_note
2. Verify at least 3 FYs are represented
3. Spot-check 5 items: convert amount to crores and verify it matches the CMA INPUT SHEET value
4. Print validation summary

---

## STEP 7: CREATE RETURN PROMPT

**This is critical.** After completing all steps, create a summary block that I can paste back to the original session. Format it EXACTLY like this:

```
=== SR PAPERS GROUND TRUTH — RETURN TO MAIN SESSION ===

FILES CREATED:
  DOCS/extractions/SR_Papers_classification_ground_truth.json

COMPANY: S.R. Papers Private Limited
INDUSTRY: Trading (paper distribution, import-heavy)
ENTITY TYPE: Private Limited Company

SOURCE FILES:
  File 1: [exact filename] → FY[YYYY], source_unit=[rupees/lakhs], sheets used: [list]
  File 2: [exact filename] → FY[YYYY], source_unit=[rupees/lakhs], sheets used: [list]
  File 3: [exact filename] → FY[YYYY], source_unit=[rupees/lakhs], sheets used: [list]

GROUND TRUTH CMA: CMA S.R.Papers 09032026 v2.xls
  Unit (B13): [value]
  FY columns: B=[YYYY], C=[YYYY], D=[YYYY]

ITEM COUNTS:
  Total: XX items
  FY breakdown: FY[YYYY]=XX, FY[YYYY]=XX, FY[YYYY]=XX

SHEET DISTRIBUTION:
  [sheet_name]: XX items
  [sheet_name]: XX items
  ...

CONFIDENCE:
  verified: XX
  high: XX
  inferred: XX
  unknown: XX

UNIQUE raw_text VALUES: XX (out of XX total)

NOTES:
  - [any anomalies, unit issues, missing data, or things to watch out for]
  - [which sheets were skipped and why]
  - [any items that were hard to map]

=== END RETURN PROMPT ===
```

Print this at the very end so the user can copy it.

---

## CONSTRAINTS

1. Use `xlrd` for all .xls files (install if needed: `pip install xlrd`)
2. Do NOT modify any app source code
3. Do NOT call any external APIs
4. Save output ONLY to `DOCS/extractions/SR_Papers_classification_ground_truth.json`
5. If a sheet has >300 items, it's probably a ledger dump — skip it and note why
6. Maximum 60 minutes wall time

---

**START by running Step 1 (discover sheets) for all 3 files. Then proceed sequentially through Steps 2-7.**
