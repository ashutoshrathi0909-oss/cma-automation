# SUBAGENT: Normalize Ground Truth — Fix cma_row to Canonical Integers

> **Model**: Sonnet (via Agent tool)
> **Purpose**: Fix inconsistent `cma_row` identifiers in existing ground truth files so they all use the canonical `sheet_row` integer from `cma_template_reference.json`.

---

## THE PROBLEM

Our ground truth files use 4 different `cma_row` formats:
- `"II_A1"` (CMA codes) — BCIPL
- `"INPUT_R21"` (Excel row refs) — Kurunji Retail
- `1`, `2`, `3` (ad-hoc sequential) — SLIPL, SSSS
- `"Form_II_Domestic_Sales"` (descriptive strings) — SR Papers

The downstream classification model needs **one consistent integer** per CMA row. The canonical integer is `sheet_row` from `cma_template_reference.json`.

## YOUR INPUTS

You will receive:
1. **One company's ground truth JSON** — the file to normalize
2. **canonical_labels.json** — the 131 canonical target labels (sheet_row → field_name → section)

## YOUR TASK

For **every entry** in `database_entries` (or `mapping_entries` for SR Papers):

### Step 1: Identify the intended CMA row
Use ALL available clues in each entry:
- `cma_field_name` — the most reliable field (e.g., "Domestic Sales")
- `cma_section` — narrows the search (e.g., "sales", "manufacturing_expenses")
- `cma_row` — the current (broken) identifier
- `reasoning` — sometimes explains the mapping logic

Match each entry to the correct row in `canonical_labels.json` using **semantic understanding**, not string matching. Examples:
- `"Domestic Sales"` → sheet_row 21 (II_A1 "Domestic")
- `"Raw Materials — Indigenous"` → sheet_row 41 (II_C2 "Raw Materials Consumed (Indigenous)")
- `"Other Admin Expenses"` → sheet_row 70 (II_D5 "Others" in Admin section)
- `"Cash Credit from IDBI"` → sheet_row 192 (III_L3a "Working Capital borrowings from banks")

### Step 2: Assign confidence
For each mapping, assign one of:
- `"certain"` — field name clearly matches one canonical row
- `"likely"` — small ambiguity but one row is the obvious fit
- `"uncertain"` — could be 2+ canonical rows, or the CA made an unusual placement

### Step 3: Normalize the schema

Rewrite each entry with this EXACT structure:
```json
{
  "cma_row": 21,
  "cma_code": "II_A1",
  "cma_field_name": "Domestic",
  "raw_text": "<preserved exactly from original>",
  "sheet_name": "<preserved>",
  "section": "<preserved>",
  "note_ref": "<preserved>",
  "amount": "<preserved>",
  "match_type": "direct|composite_component|split",
  "industry_type": "<preserved>",
  "entity_type": "<preserved>",
  "financial_year": "<preserved>",
  "industry_specific": true/false,
  "industry_note": "<preserved or null>",
  "reasoning": "<preserved>",
  "validation_issue": "<preserved or null>",
  "normalization_confidence": "certain|likely|uncertain",
  "original_cma_row": "<the original value before normalization>"
}
```

Key rules:
- `cma_row` = the canonical `sheet_row` integer from canonical_labels.json
- `cma_code` = the canonical code (e.g., "II_A1") from canonical_labels.json
- `cma_field_name` = the canonical field name from canonical_labels.json (NOT the company's version)
- `original_cma_row` = whatever the entry had before (for audit trail)
- `match_type` must be one of: `direct`, `composite_component`, `split` — normalize `composite_aggregate` to `composite_component`
- **DO NOT change** `raw_text`, `reasoning`, `industry_note`, `validation_issue` — these are the training signal
- Drop any fields not in the schema above (e.g., `amount_cr`, `amount_rupees`, `composite_total`, `split_from`, etc.)

### Step 4: Normalize the top-level structure

Output this exact structure:
```json
{
  "company_metadata": {
    "company_name": "<from original>",
    "industry_type": "<from original>",
    "entity_type": "<from original>",
    "financial_years": ["<array of FY strings>"],
    "currency_unit": "<from original>",
    "total_entries": <count>,
    "normalization_summary": {
      "certain": <count>,
      "likely": <count>,
      "uncertain": <count>
    }
  },
  "database_entries": [ ... ]
}
```

### Step 5: Flag problems

At the end of your output, list:
1. Any entries where you're `"uncertain"` — with your top 2 candidate sheet_rows and why
2. Any entries that don't match ANY canonical row (e.g., DTA mapped to "Intangible Assets" in SSSS)
3. Any entries where the original file had extra fields with useful info that got dropped — mention what was lost

## IMPORTANT

- The canonical_labels.json has exactly 131 rows. If a ground truth entry maps to a CMA row that ISN'T in the 131 (e.g., a subtotal, header, or derived Form IV/V/VI row), flag it — it shouldn't be a training example.
- Some entries may map to the same sheet_row (that's normal — composites have multiple entries per CMA row).
- Preserve the exact count of entries. Don't merge, split, or drop entries — just fix the identifiers.
