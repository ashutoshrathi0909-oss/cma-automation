# CMA Automation — New Session Cold Start

Paste this into a fresh Claude Code session. It will orient you on the project, read the testing framework, and prepare you to run an E2E test for any company.

**IMPORTANT:** Do NOT start testing yet. First, understand the project. The user will tell you which company to test.

---

## STEP 1: Read the project

Read these files in order to understand the CMA Automation System:

```
CLAUDE.md                                          — Project overview, tech stack, constraints
DOCS/testing/BCIPL_e2e_browser_test.md             — Full E2E test template (read the LESSONS LEARNED section at the bottom carefully)
DOCS/session-2026-03-23-fixes.md                   — Latest bug fixes and review burden reduction
DOCS/session-2026-03-23-rule-engine-v2.md          — Rule Engine V2: 61 deterministic rules from 7-company analysis
```

After reading, you should understand:
- What CMA documents are (Credit Monitoring Arrangement for Indian bank loans)
- The pipeline: Upload → Extract → Verify → Classify → Review → Generate Excel
- Tech stack: FastAPI backend (port 8000), Next.js frontend (port 3002), Redis + ARQ worker, Supabase DB
- Key constraint: classification uses **4-tier pipeline** (Rule Engine → fuzzy → AI → doubt report)
- **Rule Engine (Tier 0)** has 61 deterministic rules that fire BEFORE fuzzy/AI, saving API cost
- The CMA Excel template has an INPUT SHEET where data goes (rows 17-262, P&L + Balance Sheet)

## STEP 2: Read the lessons learned

The LESSONS LEARNED section at the bottom of `DOCS/testing/BCIPL_e2e_browser_test.md` contains 8 critical rules from real test failures. The most important ones:

1. **ALWAYS use a fresh client** — never reuse pre-classified data from an old session
2. **Confirm ground truth units** before comparing (lakhs vs crores vs rupees)
3. **Exclude formula/subtotal rows** from accuracy calculation (only compare rows in `cma_field_rows.py`)
4. **Check source_unit per document** — they can differ across financial years for the same company
5. **Budget 90 minutes** for a 3-document test (classification alone takes ~60 min)
6. **Known bugs:** GET /api/documents/{id} returns 405 (use API fallback), root URL redirects to /login (navigate to /clients directly)

## STEP 3: Understand available companies

The financial source files are in `FInancials main/`. Each subfolder has:
- Source financial documents (Excel .xls/.xlsx and/or scanned PDF)
- A ground truth CMA file (the CA-prepared CMA to compare against)

Available companies:

| Company | Folder | Industry | Source Files | Ground Truth |
|---------|--------|----------|--------------|--------------|
| BCIPL | `FInancials main/BCIPL/` | Manufacturing | 3 × .xls (FY2021-2023) | `CMA BCIPL 12012024.xls` |
| SR Papers | `FInancials main/SR Papers/` | Trading (paper distribution) | 3 × .xls (FY2023-2026) | `CMA S.R.Papers 09032026 v2.xls` |
| SSSS | `FInancials main/SSSS/` | Trading (steel) | 3 × .xlsx (FY2022-2025) | `CMA 4S 26122025.xlsx` |
| MSL | `FInancials main/MSL - Manufacturing/` | Manufacturing (metal stamping) | 1 × .xlsx + 3 × PDF | `MSL CMA 24102025.xls` |
| SLIPL | `FInancials main/SLIPL/` | Manufacturing (shoes) | 1 × .xlsx + 3 × PDF | `SLI CMA 31102025.xls` |
| INPL | `FInancials main/INPL/` | Manufacturing + R&D | 3 × scanned PDF | `Nanoventions CMA 10032026.xls` |
| Kurunji Retail | `FInancials main/Kurunji Retail/` | Retail trading (partnership) | 1 × PDF + 2 × ITR PDF | `CMA Kurinji retail 23012026.xls` |

**PDF companies (MSL, SLIPL, INPL, Kurunji) require OCR extraction — these are slower and may take 25-35 min per document for scanned PDFs.**

## STEP 4: When the user tells you which company to test

Once the user says which company to test, do this BEFORE writing the test prompt:

### 4a. Inspect the source files
```bash
ls -la "FInancials main/{COMPANY_FOLDER}/"
```

### 4b. Determine the ground truth unit — READ CELL B13

The ground truth CMA file always has the unit in cell **B13** of the INPUT SHEET.

```python
# For .xls files (xlrd)
import xlrd
wb = xlrd.open_workbook("path/to/ground_truth.xls")
ws = wb.sheet_by_name("INPUT SHEET")  # may vary — find sheet with "input" in name (case-insensitive)
unit = ws.cell_value(12, 1)  # row 13 (0-indexed=12), col B (0-indexed=1)
print(f"Ground truth unit: {unit}")

# For .xlsx files (openpyxl)
import openpyxl
wb = openpyxl.load_workbook("path/to/ground_truth.xlsx", data_only=True)
ws = wb["INPUT SHEET"]
unit = ws["B13"].value
print(f"Ground truth unit: {unit}")
```

Known values across all 7 companies:

| Company | B13 Value | Normalized Unit |
|---------|-----------|-----------------|
| BCIPL | `'In crs'` | crores |
| SR Papers | `'In Crs'` | crores |
| MSL | `'In Lakhs'` | lakhs |
| SLIPL | `'In Millions'` | millions |
| Kurunji | `'In Lakhs '` | lakhs |
| INPL | `'In Crs'` | crores |
| SSSS | `'Crores'` | crores |

**Normalize the value:** strip whitespace, lowercase, then map:
- Contains `crs` or `crore` → `crores`
- Contains `lakh` → `lakhs`
- Contains `million` or `mn` → millions (not supported by app yet — treat as lakhs × 10)
- Contains `thousand` or `000` → `thousands`

**The CMA output unit in the test MUST match this.** If B13 says "In Lakhs", set `cma_output_unit=lakhs`.

**IMPORTANT: SLIPL exception** — SLIPL's ground truth has TWO input sheets: `'INPUT In Mn'` (millions) and `'INPUT In Lakhs'` (lakhs). Use the lakhs sheet since the app supports lakhs natively.

### 4c. Determine source_unit per document

Source financial documents do NOT have a standardized unit cell. Detect the unit by:

1. **For Excel files:** Search rows 1-10 across all sheets for text containing "rupees", "lakhs", "thousands", "'000", or "crores". Example: SR Papers row 3 says `"(All amounts in Indian Rupees...)"`.
2. **If no text indicator found:** Check the magnitude of a known value. Find Share Capital or Revenue and compare:
   - 7+ digits (e.g., `30,942,000`) → `rupees`
   - 4-6 digits (e.g., `3094.20`) → `thousands`
   - 2-3 digits (e.g., `309.42`) → `lakhs`
   - 0-2 digits (e.g., `3.09`) → `crores`
3. **For PDF files:** Read the first page header for unit mentions. If none, check the magnitude of the first large number.
4. **Cross-check:** Take the source value, apply the conversion to the ground truth unit, and see if it matches the ground truth. Example: if source Share Capital = 30,942,000 and ground truth = 3.09 crores → 30,942,000 ÷ 10,000,000 = 3.09 ✓ → source is in rupees.

**Document the unit per file in the test prompt — they CAN differ across years for the same company.**

### 4d. Determine document_type per file

- If a file contains both P&L and Balance Sheet → `combined_financial_statement`
- If it's only P&L → `profit_and_loss`
- If it's only BS → `balance_sheet`
- If it has notes/schedules only → `notes_to_accounts`
- Most files in this project are `combined_financial_statement`

### 4e. Determine financial_year per file

- Look at the filename: "2020-21" → FY2021 (use the ending year)
- "FY 2023" → 2023
- "2024-25" → 2025

### 4f. Check if classification rules exist for this company

```bash
ls DOCS/rules/ | grep -i "{COMPANY_NAME}"
```

If rules exist, note them — they feed the rule engine (Tier 0) in the classification pipeline.

**Rule Engine V2 status (as of 2026-03-23):** 61 deterministic rules are already coded in `backend/app/services/classification/rule_engine.py`. These cover all 7 companies. The rule engine fires BEFORE fuzzy match and AI, so many common line items (GST, statutory dues, freight, capital advances, partner accounts, etc.) are classified instantly without API calls. Read `DOCS/session-2026-03-23-rule-engine-v2.md` for the full rule list.

## STEP 5: Write the test prompt

Adapt the BCIPL test template (`DOCS/testing/BCIPL_e2e_browser_test.md`) for the new company:

1. Replace COMPANY DETAILS table with the new company's info
2. Replace source file paths (exact filenames matter — copy them exactly, spaces and all)
3. Set `source_unit` per document (may differ per file — verify each one)
4. Set `cma_output_unit` to match the ground truth file's B13 cell value (already read in step 4b)
5. Update the output directory to `DOCS/test-results/{company}/run-YYYY-MM-DD/`
6. Keep ALL lessons learned, constraints, failure modes, and API fallbacks
7. Keep the comparison methodology (INPUT SHEET only, rows 17-262, 2% tolerance)
8. Add: compare ONLY rows listed in `cma_field_rows.py` for the primary accuracy number

### Key differences by company type

**Excel-only companies (BCIPL, SR Papers, SSSS):**
- Fastest to test (~90 min total, potentially faster now with Rule Engine V2 reducing AI calls)
- Extraction takes seconds
- Trial Balance sheets are auto-filtered by `excel_extractor.py` (confirmed working)
- Main risk: wrong sheet selection

**PDF companies (MSL, SLIPL, INPL, Kurunji):**
- Slower — OCR extraction takes 5-25 min per document
- Scanned PDFs need Vision OCR (surya-ocr or Anthropic Vision)
- Budget 2-3 hours total
- Main risk: OCR misreads, wrong page selection

**Mixed companies (MSL, SLIPL):**
- Have both Excel and PDF source files
- Each file may have different source_unit
- Upload each with correct metadata

## STEP 6: Present the prompt to the user

Show the user the complete test prompt and ask for confirmation before running. The user may want to:
- Adjust source_unit values
- Change the CMA output unit
- Skip certain documents
- Modify the comparison scope

---

## REFERENCE: Project file structure

```
C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2\
├── backend/
│   ├── app/
│   │   ├── routers/           — API endpoints (documents, extraction, classification, cma_reports)
│   │   ├── services/
│   │   │   ├── classification/ — 4-tier pipeline (rule_engine [61 rules], fuzzy_matcher, ai_classifier, pipeline)
│   │   │   ├── extraction/     — Excel extractor, OCR extractor, page filter
│   │   │   └── excel_generator.py — Writes CMA Excel from classified data
│   │   ├── mappings/
│   │   │   ├── cma_field_rows.py  — Which CMA rows the generator writes to (KEY for comparison)
│   │   │   └── year_columns.py    — FY → column mapping (2021→B, 2022→C, etc.)
│   │   └── workers/            — ARQ background tasks (extraction, classification, excel generation)
│   └── tests/
├── frontend/
│   └── src/app/(app)/          — Next.js pages (clients, upload, verify, review, generate)
├── FInancials main/            — Source financial documents per company
│   ├── BCIPL/
│   ├── SR Papers/
│   ├── SSSS/
│   ├── MSL - Manufacturing/
│   ├── SLIPL/
│   ├── INPL/
│   └── Kurunji Retail/
├── DOCS/
│   ├── testing/                — Test prompts and methodology
│   ├── test-results/           — Test outputs (screenshots, generated Excel, comparison reports)
│   ├── rules/                  — Classification rules per company
│   ├── extractions/            — Extraction reference data per company
│   └── CMA.xlsm               — CMA Excel template with macros
└── docker-compose.yml
```

## REFERENCE: Key URLs

| Service | URL |
|---------|-----|
| Frontend | `http://localhost:3002/clients` (NOT `/` — it redirects to login) |
| Backend API | `http://localhost:8000` |
| Health check | `http://localhost:8000/health` |

## REFERENCE: Classification pipeline (as of 2026-03-23)

```
Tier 0: Rule Engine (61 deterministic rules) — instant, no API cost
  ↓ (if no rule fires)
Tier 1: Fuzzy Match (learned_mappings → reference_mappings) — instant, no API cost
  ↓ (if no match ≥ 85%)
Tier 2: AI Classifier (OpenRouter) — ~2-5 sec per item, API cost
  ↓ (if confidence < 0.80)
Tier 3: Doubt Report — flagged for CA manual review
```

Rule Engine V2 covers: GST items, statutory dues, freight/transport, capital advances, partner accounts, forex, interest types, factory expenses, vehicle/electronics capitalization, and more. See `DOCS/session-2026-03-23-rule-engine-v2.md` for the complete list.

## REFERENCE: Known bugs (as of 2026-03-23)

1. `GET /api/documents/{id}` → 405 Method Not Allowed (breaks verify page UI — use API fallback)
2. Root URL `/` → redirects to `/login` even with DISABLE_AUTH=true (navigate to `/clients`)
3. Classification takes 20-30 min per document due to API rate limits (should be faster now with Rule Engine V2 handling many items before AI)

---

**After reading all files, tell the user: "I've read the project. Which company do you want to test?"**
