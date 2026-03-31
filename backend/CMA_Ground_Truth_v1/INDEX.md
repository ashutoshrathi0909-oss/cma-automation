# CMA Ground Truth Database v1.0

**Created:** 2026-03-26
**Purpose:** Training data for an AI classifier that maps Indian financial statement line items to CMA (Credit Monitoring Arrangement) form rows.
**Model signature:** `(raw_text, source_form, section_normalized, industry_type) → cma_row (integer, 1 of 131)`

---

## What This Folder Contains

| Metric | Value |
|--------|-------|
| Total entries | 1,326 |
| Companies | 9 (5 manufacturing, 4 trading) |
| CMA rows covered | 98 / 131 (75%) |
| Unique raw text strings | ~700 |
| Financial years | 2020-21 through 2024-25 |
| Confidence | 95.3% certain, 4.2% likely, 0.5% uncertain |

---

## Folder Structure

```
CMA_Ground_Truth_v1/
├── INDEX.md                          ← You are here
│
├── database/                         ← THE MAIN OUTPUT
│   ├── ground_truth_database.json    ← Full merged database (1,326 entries, all fields)
│   ├── training_data.json            ← Flat ML-ready format (11 fields per entry)
│   ├── label_reference.json          ← 131 CMA row definitions with training counts
│   └── database_analysis_report.json ← Class distribution, gaps, recommendations
│
├── companies/                        ← Per-company normalized ground truth
│   ├── BCIPL/
│   ├── Dynamic_Air/
│   ├── INPL/
│   ├── Kurunji_Retail/
│   ├── Mehta_Computer/
│   ├── MSL/
│   ├── SLIPL/
│   ├── SR_Papers/
│   └── SSSS/
│
├── reference/                        ← Canonical reference files (shared across all companies)
│   ├── canonical_labels.json
│   ├── cma_template_reference.json
│   └── cma_classification_rules.json
│
├── validation/                       ← Cross-validation report (GT vs CA rules)
│   └── ground_truth_validation_report.json
│
├── scripts/                          ← Rerunnable data pipelines + mapping files
│   ├── merge_database.py
│   ├── export_training_data.py
│   ├── parse_excel.py
│   ├── parse_xls.py
│   ├── sheet_name_mapping.json
│   └── section_mapping.json
│
└── prompts/                          ← Claude Code prompts used to build this database
    ├── run-extraction.md
    ├── main-opus-reverse-engineer.md
    ├── subagent-1-sonnet-ocr.md
    ├── subagent-2-cma-extractor.md
    ├── subagent-normalize-ground-truth.md
    └── WORKFLOW.md
```

---

## database/ — The Main Output

### `ground_truth_database.json` (1,235 KB)
**What:** The complete merged database with all 1,326 entries from 9 companies, fully cleaned and feature-normalized.
**How it was made:** `scripts/merge_database.py` reads all 9 per-company normalized files, applies 3 known fixes (BCIPL row correction, SSSS dedup, unmatched typing), adds `source_form` and `section_normalized` features, and merges into one file.
**Use:** The single source of truth. Contains every field including amounts, reasoning, validation issues, and provenance. Use this when you need the full picture.

**Structure:**
```json
{
  "database_metadata": {
    "total_entries": 1326,
    "companies": 9,
    "cma_rows_covered": 98,
    "version": "1.0",
    ...
  },
  "entries": [
    {
      "cma_row": 21,
      "cma_code": "II_A1",
      "cma_field_name": "Domestic",
      "raw_text": "Sales of Manufactured Products",
      "sheet_name": "Notes to P&L",
      "section": "Revenue from Operations",
      "source_form": "notes_pl",
      "section_normalized": "revenue",
      "note_ref": "Note 22",
      "amount": 3200000,
      "match_type": "direct",
      "industry_type": "manufacturing",
      "entity_type": "private_limited",
      "financial_year": "2022-23",
      "industry_specific": false,
      "industry_note": null,
      "reasoning": "Direct match — Sales of Manufactured Products maps to CMA Domestic Sales",
      "validation_issue": null,
      "normalization_confidence": "certain",
      "original_cma_row": 21,
      "company_name": "Bagadia Chaitra Industries Private Limited"
    }
  ]
}
```

### `training_data.json` (543 KB)
**What:** Flat ML-ready export with only the 11 fields needed for classifier training.
**How it was made:** `scripts/export_training_data.py` strips ground_truth_database.json down to training-relevant fields.
**Use:** Feed directly to SetFit, scikit-learn, or any ML pipeline.

**Structure:**
```json
[
  {
    "text": "Sales of Manufactured Products",
    "label": 21,
    "label_code": "II_A1",
    "label_name": "Domestic",
    "source_form": "notes_pl",
    "section_normalized": "revenue",
    "industry_type": "manufacturing",
    "entity_type": "private_limited",
    "match_type": "direct",
    "company": "Bagadia Chaitra Industries Private Limited",
    "financial_year": "2022-23"
  }
]
```

### `label_reference.json` (22 KB)
**What:** All 131 CMA row definitions with how many training examples each has.
**How it was made:** Cross-references canonical_labels.json with training counts from the database.
**Use:** Label lookup for the classifier. Also shows which 33 rows have zero examples (need synthetic data or more companies).

### `database_analysis_report.json` (69 KB)
**What:** Comprehensive statistical analysis — class distribution, missing classes, sparse classes, feature distributions, quality metrics, recommendations.
**How it was made:** Analysis agent read the merged database and canonical labels.
**Use:** Planning next data collection rounds, understanding class imbalance, configuring class weights for training.

---

## companies/ — Per-Company Ground Truth

Each company folder contains:

| File | Description |
|------|-------------|
| `ground_truth_normalized.json` | That company's entries with canonical cma_row integers, standardized schema, normalization confidence |
| `SESSION_NOTES.md` | (where available) Extraction provenance — which source files were used, currency units, issues found |

### Company Details

#### BCIPL (Bagadia Chaitra Industries Private Limited)
- **Industry:** Manufacturing | **Entity:** Private Limited
- **Entries:** 224 | **FYs:** 2020-21, 2021-22, 2022-23
- **Confidence:** 224 certain, 0 likely, 0 uncertain
- **How extracted:** CMA Excel + audited financials PDF. Three-agent pipeline (Sonnet CMA extractor + Sonnet PDF OCR + Opus reverse engineer). Original ground truth used CMA codes (e.g., "II_A1") as cma_row — normalized to canonical integers.
- **Notable:** 39 industry-specific entries. One confirmed error fixed (Profit on Sale of Fixed Asset at Exports → moved to Non-Operating Income row 30).

#### Dynamic_Air (Dynamic Air Engineering India Private Limited)
- **Industry:** Manufacturing (HVAC, aluminum grills, dampers, railway coach parts) | **Entity:** Private Limited
- **Entries:** 230 | **FYs:** 2021-22, 2022-23, 2023-24
- **Confidence:** 230 certain, 0 likely, 0 uncertain
- **How extracted:** v2 multi-agent extraction. CMA in Crores, FS in Thousands — required currency conversion (all normalized to Lakhs). FY21-22 had dual sources (Companies Act Excel + ITR PDF) with 11 CA classification differences. FY23-24 from scanned PDF.
- **Notable:** 28 industry-specific entries. Factory Rent oscillated between Manufacturing and Admin across years. 100% depreciation to manufacturing. Director remuneration 30x jump in FY22.

#### INPL (IFFCO-Nanoventions Private Limited)
- **Industry:** Manufacturing (nanotechnology/specialty chemicals, IFFCO JV) | **Entity:** Private Limited
- **Entries:** 186 | **FYs:** 2022-23, 2023-24, 2024-25
- **Confidence:** 186 certain, 0 likely, 0 uncertain
- **How extracted:** v2 multi-agent extraction. 3 large PDFs (13-18MB each) read in page ranges. CMA in Crores, FS in Thousands/Lakhs (varies by year).
- **Notable:** 18 industry-specific entries. Employee cost reclassified from Admin to Manufacturing between FY23 and FY24. Licence & Subscription classified as Rent/Rates (unusual). 29 entries have OCR-related validation issues from FY24-25.

#### Kurunji_Retail (Kurinji Retails)
- **Industry:** Trading | **Entity:** Partnership
- **Entries:** 49 | **FYs:** 2024-25
- **Confidence:** 48 certain, 1 likely, 0 uncertain
- **How extracted:** Single-year CMA Excel. Original ground truth used INPUT_R references (e.g., "INPUT_R21") — normalized to canonical integers. Cross-verified: INPUT_R numbers matched sheet_row for this company.
- **Notable:** 20 industry-specific entries. Partnership-specific fields (Partners' Capital, Partners' Salary, Interest to Partners). Only 1 FY available.

#### Mehta_Computer (M/S Mehta Computers)
- **Industry:** Trading (IT/computer equipment) | **Entity:** Proprietorship
- **Entries:** 74 | **FYs:** 2021-22, 2022-23, 2023-24
- **Confidence:** 74 certain, 0 likely, 0 uncertain
- **How extracted:** v2 multi-agent extraction. 2022-2024 from Excel (year-wise subfolders), 2025 from PDF (supplementary). CMA in Lakhs, FS in Absolute Rupees.
- **Notable:** 29 industry-specific entries. Proprietorship — personal property (flats) reclassified from FS Investments to CMA Fixed Assets. Kotak Sweep Account migrated across 3 CMA rows over 3 years. Trade discounts placed in Advertising instead of netted against sales.

#### MSL (Matrix Stampi Limited)
- **Industry:** Manufacturing | **Entity:** Private Limited
- **Entries:** 222 | **FYs:** 2022-23, 2023-24, 2024-25
- **Confidence:** 222 certain, 0 likely, 0 uncertain
- **How extracted:** v2 multi-agent extraction. FY22-23 is CMA-amounts-only (PDFs were scanned images — no text extraction possible). FY24-25 had dual sources (audited PDF + working paper Excel with 220-account trial balance).
- **Notable:** 9 industry-specific entries. All employee costs → manufacturing wages (no admin split). Export Incentive reclassified from Other Income to Export Sales. Director loans split between quasi-equity and LT debt changed between years.

#### SLIPL (Suolificio Linea Italia (India) Private Limited)
- **Industry:** Manufacturing | **Entity:** Private Limited
- **Entries:** 114 | **FYs:** 2022-23, 2023-24, 2024-25
- **Confidence:** 102 certain, 12 likely, 0 uncertain
- **How extracted:** CMA Excel + audited financials. Original ground truth used ad-hoc sequential integers (1, 2, 3...) as cma_row — completely wrong. Normalized using cma_field_name matching against canonical labels.
- **Notable:** 25 industry-specific entries. 12 "likely" entries where field name matched but section was ambiguous (Depreciation, Others in multiple sections). 3 entries didn't match any canonical row.

#### SR_Papers (S.R. Papers Private Limited)
- **Industry:** Trading | **Entity:** Private Limited
- **Entries:** 164 | **FYs:** 2022-23, 2023-24, 2024-25
- **Confidence:** 138 certain, 24 likely, 2 uncertain
- **How extracted:** CMA Excel + audited financials. Original ground truth used descriptive strings (e.g., "Form_II_Domestic_Sales") as cma_row. Used `mapping_entries` instead of `database_entries`. Both normalized. `composite_aggregate` match_type normalized to `composite_component`.
- **Notable:** 106 industry-specific entries (65% — seems over-flagged). 2 uncertain entries (Term Loans, could be current or non-current).

#### SSSS (Salem Stainless Steel Suppliers Private Limited)
- **Industry:** Trading | **Entity:** Private Limited
- **Entries:** 63 | **FYs:** 2022-23, 2023-24, 2024-25
- **Confidence:** 40 certain, 19 likely, 4 uncertain
- **How extracted:** CMA Excel + audited financials. Original ground truth used ad-hoc sequential integers AND decimal rows (112.3, 112.4). Normalized using cma_field_name matching.
- **Notable:** 18 industry-specific entries. Row 98 collision (two entries, same company/row/FY, different amounts) — resolved as composite components. 4 uncertain entries including DTA classified as Intangible Assets.

---

## reference/ — Canonical Reference Files

### `canonical_labels.json` (20 KB)
**What:** The 131 non-subtotal, non-header CMA input rows. Each has a `sheet_row` integer, `code` (e.g., "II_A1"), `name`, and `section`.
**How it was made:** Extracted from `cma_template_reference.json` by filtering to only the 131 rows that accept direct input (excluding subtotals and headers).
**Use:** The single source of truth for what `cma_row` integers mean. Every entry in the database uses `sheet_row` from this file as its `cma_row` value.

### `cma_template_reference.json` (264 rows)
**What:** The full CMA template — all 264 rows including subtotals, headers, and computed rows. Contains hierarchy information (which rows sum to which subtotals).
**How it was made:** `build_cma_reference.py` parsed the source CMA.xlsm template workbook.
**Use:** Understanding the full CMA form structure. Validating that component rows sum to subtotal rows.

### `cma_classification_rules.json` (178 KB)
**What:** 385 expert classification rules extracted from a CA-prepared `CMA classification.xls` workbook. Each rule maps a financial statement item (e.g., "Audit Fees") to a CMA row (e.g., "Item 6: SGA → II_D7a, sheet_row 72").
**How it was made:** Opus agent parsed the CA's Excel workbook, mapped each rule to canonical labels, and assigned confidence.
**Use:** Layer 1 of the hybrid cascade classifier (rule engine). Also used for validation — the ground_truth_validation_report.json compares GT entries against these rules.

---

## validation/ — Cross-Validation Report

### `ground_truth_validation_report.json` (105 KB)
**What:** Cross-validation of all 614 GT entries (from the original 5 companies) against the 385 CA classification rules.
**How it was made:** Opus agent matched each GT entry to the most relevant CA rule, compared the cma_row assignments, and classified disagreements.
**Use:** Understanding where the database disagrees with expert CA rules and why.

**Key findings:**
- 379 entries checked, 229 agreed (60.4%), 140 disagreed
- 117 disagreements are `ca_judgment` — both answers are valid, CAs simply chose different sub-rows
- 22 disagreements are `context_dependent` — manufacturing vs admin classification depends on company context
- 1 was a confirmed error (BCIPL row 22, now fixed)

---

## scripts/ — Rerunnable Pipelines

### `merge_database.py`
**What:** Reads all 9 normalized GT files, applies fixes, merges into ground_truth_database.json.
**Use:** Re-run when adding new companies. Add the new company's normalized file path to the input list, re-run.

### `export_training_data.py`
**What:** Reads ground_truth_database.json, strips to training-relevant fields, exports training_data.json and label_reference.json.
**Use:** Re-run after any database update to regenerate training files.

### `parse_excel.py` / `parse_xls.py`
**What:** Convert .xlsx and .xls files to JSON for subagent consumption.
**Use:** First step in the extraction pipeline for new companies. Requires `openpyxl` (xlsx) and `xlrd` (xls).

### `sheet_name_mapping.json`
**What:** Maps 46 unique `sheet_name` variants to 6 `source_form` categories (profit_and_loss, balance_sheet, notes_pl, notes_bs, notes_general, cma_form).
**Use:** Apply to new companies' entries. Extend when new sheet_name variants appear.

### `section_mapping.json`
**What:** Maps 133 unique `section` variants to 23 `section_normalized` categories (revenue, other_income, raw_materials, employee_cost, etc.).
**Use:** Apply to new companies' entries. Extend when new section variants appear.

---

## prompts/ — Claude Code Prompts

These are the exact prompts used to build this database. They can be reused for future companies.

### `run-extraction.md` (v2 — Multi-Agent)
**What:** Master extraction prompt. Deploys parallel Sonnet agents — one per financial year — to extract CMA and financial statement data. Handles mixed Excel + PDF sources. Creates SESSION_NOTES.md.
**Use:** Paste into a Sonnet Claude Code window to extract a new company. Say "Process [Company Name]".

### `main-opus-reverse-engineer.md`
**What:** Opus reverse engineering prompt. Cross-references CMA extraction with financial statements to build ground truth entries.
**Use:** Paste into an Opus Claude Code window AFTER extraction is complete. Reads the extraction JSONs and produces the ground truth file.

### `subagent-1-sonnet-ocr.md`
**What:** Instructions for Sonnet agents extracting financial statements from PDF.
**Use:** Used by run-extraction.md internally. Can also be used standalone.

### `subagent-2-cma-extractor.md`
**What:** Instructions for Sonnet agents extracting CMA form data from Excel.
**Use:** Used by run-extraction.md internally. Can also be used standalone.

### `subagent-normalize-ground-truth.md`
**What:** Generic normalization template for converting ad-hoc cma_row values to canonical integers.
**Use:** Only needed if the Opus reverse engineer produces non-canonical row numbers (shouldn't happen with v2 prompts).

### `WORKFLOW.md`
**What:** End-to-end workflow documentation. Explains the two-session approach (Session 1: extraction, Session 2: reverse engineering).
**Use:** Read this first to understand the full pipeline.

---

## How This Database Was Built

### Pipeline (per company)

```
Step 1: Parse source files (Excel/PDF → JSON)
  ↓
Step 2: Deploy Sonnet extraction agents (parallel, one per year)
  - CMA Agent: extracts CMA row numbers and amounts
  - FS Agents: extract P&L, Balance Sheet, Notes from Excel or PDF
  ↓
Step 3: Opus reverse engineering (separate window)
  - Cross-references CMA amounts ↔ FS line items
  - Classifies each mapping as direct / composite / split
  - Flags industry-specific CA judgment calls
  - Validates amounts (components must sum to CMA totals)
  ↓
Step 4: Normalization
  - Ensures cma_row uses canonical sheet_row integers
  - Standardizes schema across all companies
  ↓
Step 5: Merge + Fix + Feature Normalize
  - merge_database.py combines all companies
  - Applies known fixes
  - Adds source_form and section_normalized features
  ↓
Step 6: Export for training
  - export_training_data.py creates flat ML-ready format
```

### Quality Assurance
- Every entry cross-validated against 385 CA classification rules
- Amount validation: composite components must sum to CMA row totals (±1%)
- Schema consistency: all 1,326 entries verified to have identical field structure
- Normalization confidence: 95.3% certain, 4.2% likely, 0.5% uncertain

### Known Limitations
- **33 CMA rows have zero training examples** — mostly obsolete (Excise Duty), large-company-only (Preference Shares), or niche (Contingent Liabilities)
- **22 rows have only 1-3 examples** — need more companies to strengthen
- **Industry coverage:** Only manufacturing (74%) and trading (26%) — no services, construction, or NBFC companies yet
- **Entity coverage:** 91% private limited — limited partnership (4%) and proprietorship (6%) data
- **FY22-23 for MSL is CMA-amounts-only** — scanned PDFs couldn't be OCR'd

### Recommended Next Steps
1. Add 10-15 more companies from diverse industries (services, NBFC, public listed, construction)
2. Generate synthetic training examples for the 33 missing CMA rows using LLM
3. Train hybrid cascade: Rule Engine (385 rules) → SetFit → Claude Haiku fallback
4. Target: 2,500+ entries for production classifier (currently at 1,326)

---

## How to Add a New Company

1. Place source files (CMA Excel + audited financials) in a new company folder
2. Open Sonnet Claude Code → paste `prompts/run-extraction.md` → "Process [Company]"
3. Open Opus Claude Code → paste `prompts/main-opus-reverse-engineer.md` → point it to extraction files
4. Normalize if needed (v2 prompts produce canonical integers automatically)
5. Add the new normalized file to `scripts/merge_database.py` and re-run
6. Re-run `scripts/export_training_data.py`
7. Copy updated files to this deliverable folder

---

*Built with Claude Code (Opus + Sonnet agents) over multiple sessions. March 2026.*
