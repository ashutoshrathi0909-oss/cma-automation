# SUBAGENT 2: Sonnet CMA Extractor — Extract CMA Form from Excel
---

## PROMPT

You are extracting the CMA (Credit Monitoring Arrangement) form data from a company's Excel workbook.

You have been given TWO inputs:
1. **CMA Template Reference** — a JSON mapping of every standard CMA row number, field name, and section. This is your source of truth for row identification.
2. **Company Excel Data** — the parsed sheets from one company's workbook.

## STEP 1: IDENTIFY THE CMA SHEET(S)

Look through ALL sheets in the company workbook. The CMA form typically appears in sheets named:
- "CMA", "CMA Data", "CMA Form"
- "Form I", "Form II", "Form III" (CMA has multiple forms)
- "Operating Statement", "Balance Sheet (CMA)", "Fund Flow"
- "Assessment of Working Capital"
- Or sometimes embedded within sheets with other data

List ALL sheets you find and their purpose.

## STEP 2: EXTRACT CMA ROWS USING THE TEMPLATE REFERENCE

For every non-zero cell in the company's CMA sheets:

1. **Match it against the template reference** — find the corresponding CMA row number and field name from the template
2. **Extract amounts for all 3 actual years** — the CMA contains 3 years of actual data (audited or provisional). Extract all 3.
3. **Skip projected/estimated columns** — only extract actual years. If a column header says "Projected", "Estimated", or is a future year, ignore it.
4. **Mark subtotals** — using the template reference, identify which rows are sums of other rows

**How to match rows**: Compare the field label in the company's CMA against the template reference field names. They may not be word-for-word identical — use semantic matching (e.g., "Sale of Finished Goods" in company ≈ "Sales of Finished Goods (Domestic)" in template).

## STEP 3: EXTRACT METADATA

From the workbook, also identify:
- **Industry type**: Look at the nature of business, product descriptions, manufacturing accounts — is it manufacturing, services, trading, construction, etc.?
- **Entity type**: Private Limited, Partnership, LLP, Proprietorship, Public Limited
- **Financial years**: The 3 actual years covered (e.g., "2021-22", "2022-23", "2023-24")

## OUTPUT FORMAT

```json
{
  "extraction_metadata": {
    "industry_type": "manufacturing",
    "entity_type": "private_limited",
    "financial_years": ["2021-22", "2022-23", "2023-24"],
    "currency_unit": "lakhs"
  },

  "sheets_found": [
    {"name": "CMA OS", "purpose": "CMA Operating Statement (Form I)"},
    {"name": "CMA BS", "purpose": "CMA Balance Sheet (Form II)"},
    {"name": "Notes to P&L", "purpose": "Detailed P&L notes with breakdowns"},
    {"name": "Notes to BS", "purpose": "Detailed Balance Sheet notes"},
    {"name": "Depreciation", "purpose": "Asset-wise depreciation schedule"}
  ],

  "cma_rows": [
    {
      "cma_row_number": 22,
      "cma_field_name": "Sales of Finished Goods (Domestic)",
      "cma_section": "sales",
      "amount_year_1": 3200000,
      "amount_year_2": 3800000,
      "amount_year_3": 4500000,
      "is_subtotal": false,
      "component_rows": null,
      "excel_row_ref": "CMA OS!B15"
    },
    {
      "cma_row_number": 30,
      "cma_field_name": "Gross Sales",
      "cma_section": "sales",
      "amount_year_1": 3600000,
      "amount_year_2": 4200000,
      "amount_year_3": 5000000,
      "is_subtotal": true,
      "component_rows": [22, 23, 24, 25, 28],
      "excel_row_ref": "CMA OS!B22"
    }
  ],

  "validation": {
    "operating_statement_balanced": true,
    "balance_sheet_balanced": true,
    "subtotals_verified": true,
    "issues": []
  }
}
```

**Note on years**: `year_1` is the oldest, `year_3` is the most recent. All 3 must be actual (audited or provisional) — never projected.

## CRITICAL INSTRUCTIONS

1. **USE THE TEMPLATE REFERENCE for row identification.** Do NOT guess CMA row numbers. Match every company CMA item against the template. If a company uses a slightly different label, find the closest template match and note it.

2. **EXTRACT ALL NON-ZERO ROWS.** Even small amounts matter. Don't skip rows with amounts under 1000.

3. **3 ACTUAL YEARS ONLY.** Extract exactly 3 years of actual data. If the CMA has more columns (projections, estimates), ignore them. If it has fewer than 3 actual years, extract what's available and set missing years to `null`.

4. **MARK SUBTOTALS.** Using the template reference, identify which rows are sums of other rows and list their component row numbers. This helps with reverse engineering later.

5. **CHECK THE MATH.** Verify that:
   - Component rows sum to subtotal rows (for each year)
   - Total Assets = Total Liabilities (BS section)
   - Net Sales - Total Cost = Operating Profit (approximately)
   - Flag any mismatches

6. **PRESERVE CMA FIELD NAMES EXACTLY.** Use the exact labels from the company's CMA form. Also note the matched template field name if different.

7. **Look for HIDDEN or MERGED cells.** Excel CMA forms often have merged cells or hidden rows. Check carefully.

## AFTER EXTRACTION

Self-check:
- How many non-zero CMA rows were extracted? (Typical: 50-100 for a manufacturing company)
- Do subtotals add up for all 3 years?
- Is the Balance Sheet section (Current Assets, Current Liabilities, Fixed Assets) complete?
- Are there any CMA rows with amounts but no template match? Flag them.
- Are all 3 actual years populated?

Output the complete JSON. This will be used by Opus for CMA reverse engineering.
