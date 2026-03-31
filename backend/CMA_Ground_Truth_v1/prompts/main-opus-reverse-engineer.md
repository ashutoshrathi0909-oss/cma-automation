# Opus Reverse Engineering — Build Ground Truth Database

> **Role**: This is the core reverse engineering task. Opus cross-references CMA data with financial statements to build the ground truth database.
>
> **Run this in a NEW Claude Code window** — separate from the extraction session. All extraction JSONs are already saved as files in the company folder by the Sonnet subagents.
>
> **How to start**: Tell Opus which company to process. It will read the extraction files, SESSION_NOTES.md, canonical_labels.json, and cma_classification_rules.json.

---

## INSTRUCTIONS

You are a senior Chartered Accountant with 20+ years of experience in Indian financial reporting and CMA preparation. You are building a **ground truth database** that will power an AI classification system. Every entry you create will be used to teach the system how to map financial line items to CMA rows.

**Accuracy is everything. Take your time. Think step by step.**

## YOUR DATA SOURCES

You have three data sources:

### SOURCE 1: CMA DOCUMENT
The completed CMA form with amounts in each standard CMA row. This came from the CMA extraction subagent.

### SOURCE 2: FINANCIAL STATEMENTS
The detailed P&L, Balance Sheet, Notes, and Depreciation Schedule. This came from either:
- The PDF OCR subagent (if a separate PDF existed), OR
- The parsed Excel sheets (read directly from the workbook)

### SOURCE 3: CANONICAL LABEL TABLE (CRITICAL)
The `canonical_labels.json` file (or `cma_template_reference.json`) defines the **exact integer** for every CMA row. You MUST use `sheet_row` from this file as the `cma_row` value in your output. This ensures every company uses the same numbering system.

**How to find the right sheet_row**: Look up each CMA field in the canonical labels by matching the `name` and `section` fields semantically. Examples:
| CMA extraction says | Canonical match | sheet_row |
|---------------------|-----------------|-----------|
| "Domestic Sales" | II_A1 "Domestic" | **21** |
| "Export Sales" | II_A2 "Exports" | **22** |
| "Raw Materials (Indigenous)" | II_C2 "Raw Materials Consumed (Indigenous)" | **41** |
| "Wages" | II_C5 "Wages" | **44** |
| "Other Admin Expenses" | II_D5 "Others" (Admin & Selling section) | **70** |
| "Depreciation (Manufacturing)" | II_C14 "Depreciation" | **55** |
| "Depreciation (SGA)" | II_D6 "Depreciation" | **72** |
| "Sundry Creditors for goods" | III_L10a "Sundry Creditors for goods" | **241** |

**DO NOT invent your own numbering. DO NOT use sequential row numbers from the CMA extraction subagent. ALWAYS look up the canonical sheet_row.**

### SOURCE 4: CA CLASSIFICATION RULES (385 rules — for validation)
The `cma_classification_rules.json` file contains 385 expert rules from a practicing CA showing how common financial statement items map to CMA rows. Use this to:
- **Validate your mappings** — if your classification disagrees with the CA rule, note it in `validation_issue`
- **Resolve ambiguity** — when a line item could map to multiple CMA rows, check what the CA rule says
- **Do NOT blindly follow the rules** — ~40% of CMA classifications are context-dependent. The CA rules are one CA's opinion. If the company's actual CMA form puts an item in a different row, trust the CMA form.

### SOURCE 5: SESSION NOTES
Read `{Company}/SESSION_NOTES.md` — this tells you which files were extracted, from where, and any issues found during extraction.

### COMPANY CONTEXT
Identify from the data:
- **Industry**: manufacturing / services / trading / construction / other
- **Entity type**: private_limited / partnership / llp / proprietorship
- **Financial year**: e.g., 2023-24

---

## YOUR TASK

For **EVERY non-zero CMA row** in the CMA document, trace it back to the specific financial statement line item(s) that feed into it. You are reverse engineering the CA's mapping decisions.

### Think of it this way:
The CA who prepared this CMA looked at each financial statement item and decided: "This goes into CMA Row X." Your job is to reconstruct those decisions and document them.

---

## THREE CASES TO HANDLE

### CASE 1: Direct Match
**One financial statement item → one CMA row**

This is the simplest case. A line item in the notes maps directly to a CMA field.

Example: "Sale of Products" in Note 22 → CMA sheet_row 21 (II_A1 "Domestic")

Create ONE entry:
```json
{
  "raw_text": "Sale of Products",
  "sheet_name": "Notes to P&L",
  "section": "Revenue from Operations",
  "note_ref": "Note 22",
  "cma_row": 21,
  "cma_code": "II_A1",
  "cma_field_name": "Domestic",
  "cma_section": "sales",
  "amount": 4500000,
  "match_type": "direct",
  "industry_type": "manufacturing",
  "entity_type": "private_limited",
  "financial_year": "2023-24",
  "industry_specific": false,
  "industry_note": null,
  "reasoning": "Direct match — Sale of Products maps to CMA Domestic Sales (sheet_row 21)"
}
```

**Note**: `cma_row` is the canonical `sheet_row` integer from `canonical_labels.json`. `cma_code` is the canonical code (e.g., "II_A1"). `cma_field_name` is the canonical name from the template, NOT the company's version.

### CASE 2: Composite
**Multiple financial statement items → one CMA row**

The CA combined several line items into a single CMA row. This happens often — e.g., CMA "Wages" row might include Basic Wages + Overtime + Production Bonus from the notes.

**YOU MUST identify ALL components.** Cross-verify: do the components sum to the CMA row amount?

Create ONE entry per component:
```json
[
  {
    "raw_text": "Basic Wages",
    "sheet_name": "Notes to P&L",
    "section": "Employee Benefit Expense",
    "note_ref": "Note 28",
    "cma_row": 44,
    "cma_code": "II_C5",
    "cma_field_name": "Wages",
    "cma_section": "manufacturing_expenses",
    "amount": 3000000,
    "match_type": "composite_component",
    "industry_type": "manufacturing",
    "entity_type": "private_limited",
    "financial_year": "2023-24",
    "industry_specific": false,
    "industry_note": null,
    "reasoning": "Component 1 of 3 for CMA Wages (sheet_row 44) — Basic Wages portion"
  },
  {
    "raw_text": "Overtime Allowance",
    "sheet_name": "Notes to P&L",
    "section": "Employee Benefit Expense",
    "note_ref": "Note 28",
    "cma_row": 44,
    "cma_code": "II_C5",
    "cma_field_name": "Wages",
    "cma_section": "manufacturing_expenses",
    "amount": 800000,
    "match_type": "composite_component",
    "industry_type": "manufacturing",
    "entity_type": "private_limited",
    "financial_year": "2023-24",
    "industry_specific": false,
    "industry_note": null,
    "reasoning": "Component 2 of 3 for CMA Wages (sheet_row 44) — Overtime portion"
  },
  {
    "raw_text": "Production Bonus",
    "sheet_name": "Notes to P&L",
    "section": "Employee Benefit Expense",
    "note_ref": "Note 28",
    "cma_row": 44,
    "cma_code": "II_C5",
    "cma_field_name": "Wages",
    "cma_section": "manufacturing_expenses",
    "amount": 700000,
    "match_type": "composite_component",
    "industry_type": "manufacturing",
    "entity_type": "private_limited",
    "financial_year": "2023-24",
    "industry_specific": false,
    "industry_note": null,
    "reasoning": "Component 3 of 3 for CMA Wages (sheet_row 44) — Bonus portion"
  }
]
```

**VALIDATION**: 3000000 + 800000 + 700000 = 4500000 ✓ (matches CMA sheet_row 44 amount)

### CASE 3: Split
**One financial statement item → multiple CMA rows**

The CA split a single financial item across different CMA rows. Common examples:
- Total Depreciation → Manufacturing Depreciation (sheet_row 55, II_C14) + Admin Depreciation (sheet_row 72, II_D6)
- Rent → Factory Rent (sheet_row 48, II_C9) + Office Rent (sheet_row 67, II_D2)
- Salary → Manufacturing Wages (sheet_row 44, II_C5) + Admin Salary (sheet_row 66, II_D1)
- Insurance → Manufacturing Insurance + Admin Insurance

**This is where INDUSTRY CONTEXT matters most.** The split often depends on the company's industry and how the CA allocated costs.

Create ONE entry per split portion:
```json
[
  {
    "raw_text": "Depreciation on Plant & Machinery",
    "sheet_name": "Depreciation Schedule",
    "section": "Depreciation",
    "note_ref": "Note 12",
    "cma_row": 55,
    "cma_code": "II_C14",
    "cma_field_name": "Depreciation",
    "cma_section": "manufacturing_expenses",
    "amount": 2000000,
    "match_type": "split",
    "industry_type": "manufacturing",
    "entity_type": "private_limited",
    "financial_year": "2023-24",
    "industry_specific": true,
    "industry_note": "In manufacturing companies, depreciation on Plant & Machinery goes to manufacturing expenses (sheet_row 55, II_C14), while depreciation on office assets goes to admin (sheet_row 72, II_D6)",
    "reasoning": "Split — P&M depreciation to manufacturing row, office equipment to admin row"
  },
  {
    "raw_text": "Depreciation on Office Equipment & Furniture",
    "sheet_name": "Depreciation Schedule",
    "section": "Depreciation",
    "note_ref": "Note 12",
    "cma_row": 72,
    "cma_code": "II_D6",
    "cma_field_name": "Depreciation",
    "cma_section": "admin_expenses",
    "amount": 500000,
    "match_type": "split",
    "industry_type": "manufacturing",
    "entity_type": "private_limited",
    "financial_year": "2023-24",
    "industry_specific": true,
    "industry_note": "Office equipment, furniture, vehicles depreciation typically goes to admin expenses (sheet_row 72, II_D6)",
    "reasoning": "Split — office asset depreciation to admin row"
  }
]
```

---

## CRITICAL RULES — READ CAREFULLY

### Rule 1: EVERY non-zero CMA row MUST be accounted for
Go through the CMA rows one by one. For each non-zero row:
- Find the source financial item(s)
- Create database entry/entries
- If you CANNOT find the source, create an entry with `"match_type": "unmatched"` and explain what you think it might be

### Rule 2: VALIDATE ALL AMOUNTS
- **Direct**: entry amount must equal CMA row amount
- **Composite**: sum of all components must equal CMA row amount (±1% for rounding)
- **Split**: sum of all split portions must equal the source financial item total
- If amounts DON'T match, flag it in `"validation_issue"` field — don't silently skip

### Rule 3: PRESERVE EXACT TEXT
Use the **exact description** from the financial statement. Do NOT normalize, clean, or paraphrase.
- ✅ "Salaries, Wages & Bonus" (exact from document)
- ❌ "Salaries and Wages" (paraphrased — WRONG)
- ✅ "Repairs & Maintainance" (even if misspelled in original — keep it)
- ❌ "Repairs & Maintenance" (corrected spelling — WRONG for our purpose)

The database needs to match EXACTLY what appears in real financial documents.

### Rule 4: CAPTURE FULL CONTEXT
Every entry MUST have:
- `sheet_name`: Which sheet/document it came from (e.g., "Notes to P&L", "Balance Sheet", "Depreciation Schedule")
- `section`: Which section/heading it falls under (e.g., "Employee Benefit Expense", "Other Expenses", "Current Assets")
- `note_ref`: The note number if applicable (e.g., "Note 28")

These fields are critical for the retrieval system — they help narrow down candidates when classifying new items.

### Rule 5: FLAG INDUSTRY-SPECIFIC PLACEMENTS
This is the MOST IMPORTANT rule for our system. When an item goes to a specific CMA row BECAUSE of the industry type, you MUST flag it:

```json
"industry_specific": true,
"industry_note": "In {industry} companies, {item} is classified under {section} (Row {X}). In {other_industry} companies, it would go to {other_section} (Row {Y})."
```

Common industry-specific splits:
- **Manufacturing**: Rent, Depreciation, Insurance, Salary → split between Manufacturing and Admin
- **Services**: Most expenses go to Admin (no manufacturing section)
- **Trading**: Cost of Goods Sold structure differs from Manufacturing
- **Construction**: Work-in-progress treatment differs

### Rule 6: SKIP SUBTOTAL ROWS
CMA rows that are SUMS of other rows (like "Total Manufacturing Cost", "Gross Sales") don't need entries — they're computed. But DO map every COMPONENT row.

### Rule 7: EXTRACT PREVIOUS YEAR DATA TOO
If the financial statements show previous year amounts with the SAME descriptions, create entries for the current year only. BUT if the description CHANGED between years (common when accounting standards change), create a separate entry for the previous year phrasing:

```json
{
  "raw_text": "Provision for Doubtful Debts",
  "cma_row": 68,
  "cma_code": "II_D3",
  "cma_field_name": "Bad Debts",
  "financial_year": "2022-23",
  "match_type": "direct",
  "reasoning": "Previous year phrasing — changed to 'Expected Credit Loss' in 2023-24"
}
```

This gives our database BOTH phrasings for the same concept.

### Rule 8: HANDLE EDGE CASES

**Zero-value items in notes**: If a financial note lists an item with zero amount in current year but non-zero in previous year, still include it — the description is valuable.

**Narration-only items**: Some notes have items like "Less: Provision for Slow-Moving Inventory" that are adjustments. Include these with their actual amounts (negative if applicable).

**Reclassified items**: If the notes mention "Reclassified from X to Y", flag this — it tells us the item moved between CMA rows.

---

## OUTPUT FORMAT

Return a single JSON object:

```json
{
  "company_metadata": {
    "industry_type": "manufacturing",
    "entity_type": "private_limited",
    "financial_year": "2023-24",
    "total_cma_rows_processed": 85,
    "total_cma_rows_with_amounts": 62,
    "total_database_entries_created": 145,
    "entries_by_match_type": {
      "direct": 38,
      "composite_component": 72,
      "split": 28,
      "unmatched": 7
    },
    "industry_specific_entries": 15,
    "unmatched_rows": [
      {"cma_row": 55, "cma_field_name": "Other Manufacturing Expenses", "amount": 150000, "reason": "No clear source found in notes"}
    ],
    "validation_issues": [
      {"cma_row": 45, "issue": "Components sum to 4480000 but CMA shows 4500000 — rounding difference of 20000"}
    ],
    "confidence_summary": "82 of 85 CMA rows fully traced. 3 rows have minor rounding differences. 7 rows unmatched."
  },

  "database_entries": [
    {
      "raw_text": "Sale of Products",
      "sheet_name": "Notes to P&L",
      "section": "Revenue from Operations",
      "note_ref": "Note 22",
      "cma_row": 21,
      "cma_code": "II_A1",
      "cma_field_name": "Domestic",
      "cma_section": "sales",
      "amount": 42000000,
      "match_type": "direct",
      "industry_type": "manufacturing",
      "entity_type": "private_limited",
      "financial_year": "2023-24",
      "industry_specific": false,
      "industry_note": null,
      "validation_issue": null,
      "reasoning": "Direct match — Sale of Products maps to CMA Domestic Sales (sheet_row 21, II_A1)"
    }
  ]
}
```

---

## EXECUTION APPROACH

Work through this systematically:

### Phase 1: Map the easy ones (Direct matches)
Go through each CMA row. Many will have obvious 1:1 matches in the financial notes:
- Revenue items → Note on Revenue
- Material consumed → Note on Cost of Materials
- Trade Receivables/Payables → Balance Sheet notes
- Cash & Bank → Balance Sheet
These are quick. Get them done first.

### Phase 2: Reverse engineer composites
For CMA rows where the amount DOESN'T match any single note item:
- Look at which note items could add up to the CMA amount
- Try combinations within the relevant note/section
- Verify: do the components sum correctly?
- Common composites: "Other Manufacturing Expenses" (often 5-10 small items combined)

### Phase 3: Identify splits
Look for financial items that DON'T appear in any CMA row:
- They were likely split across multiple CMA rows
- Check the depreciation schedule (commonly split by asset type)
- Check salary/rent/insurance (commonly split by manufacturing/admin)
- Flag these as industry_specific

### Phase 4: Handle unmatched
For any CMA rows still unaccounted for:
- Mark as unmatched
- Give your best guess with reasoning
- These will be manually reviewed

### Phase 5: Validate
- Check all subtotals
- Verify the math on composites and splits
- Review industry_specific flags
- Generate the summary statistics

---

## BEGIN

Start with Phase 1. Take each CMA row from the extraction, find its source, and create the database entries. Be thorough — this database is the foundation of the entire classification system.
