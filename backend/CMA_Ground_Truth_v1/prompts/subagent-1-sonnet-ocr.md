# SUBAGENT 1: Sonnet OCR — Financial Statement Extraction from PDF

> **Model**: Sonnet (vision capable)
> **When to use**: Only when the company has a separate PDF of audited financials
> **Context**: Fresh window — upload ONLY the PDF, paste this prompt

---

## PROMPT (copy everything below this line)

You are extracting financial data from an Indian company's audited financial statements PDF. Your output will be used by a senior CA in another window for CMA reverse engineering — so completeness and accuracy are critical.

## WHAT TO EXTRACT

### 1. PROFIT & LOSS STATEMENT
- Every line item: description, current year amount, previous year amount
- Preserve the hierarchy exactly (main heads → sub-items → sub-sub-items)
- Capture note reference numbers (e.g., "Note 22", "Schedule IV")
- Include: Revenue, Other Income, Expenses (each head), Tax, PAT — everything

### 2. BALANCE SHEET
- Every line item: description, current year amount, previous year amount
- Separate clearly:
  - EQUITY & LIABILITIES: Shareholders' Equity, Non-current Liabilities, Current Liabilities
  - ASSETS: Non-current Assets, Current Assets
- Capture note reference numbers

### 3. NOTES TO ACCOUNTS (MOST CRITICAL — this has the detail)
- For EVERY note referenced in P&L or Balance Sheet:
  - Note number and title/heading
  - Every sub-item with exact description and amount
  - Preserve indentation/hierarchy (main item → sub-items → sub-sub-items)
  - If a note has a table (e.g., Fixed Assets schedule), extract the full table
- Common important notes:
  - Property, Plant & Equipment (with asset-wise breakdowns)
  - Investments (current and non-current)
  - Inventories (raw material, WIP, finished goods)
  - Trade Receivables / Payables
  - Revenue from Operations
  - Cost of Materials Consumed
  - Employee Benefit Expense
  - Other Expenses (this often has 15-30 sub-items — extract ALL)
  - Depreciation & Amortization
  - Finance Costs

### 4. DEPRECIATION SCHEDULE (if present as separate schedule)
- Asset class, opening gross block, additions, deletions, closing gross block
- Opening accumulated depreciation, depreciation for year, closing accumulated
- Net block (opening and closing)
- Depreciation rate if mentioned

### 5. MANUFACTURING / TRADING ACCOUNT (if present)
- Some companies show a separate manufacturing or trading account
- Extract every line item with amounts

### 6. SIGNIFICANT ACCOUNTING POLICIES (brief summary)
- Revenue recognition method
- Depreciation method (SLM/WDV)
- Inventory valuation method
- Any other policy that affects CMA classification

## OUTPUT FORMAT

```json
{
  "extraction_metadata": {
    "company_industry": "<identify from context: manufacturing/services/trading/construction/etc>",
    "entity_type": "<private_limited/partnership/llp/proprietorship/public_limited>",
    "financial_year": "<e.g., 2023-24>",
    "currency_unit": "<rupees/thousands/lakhs/crores>",
    "accounting_standards": "<Ind AS / Old GAAP / IFRS>",
    "auditor_name": "<if visible>",
    "pages_processed": "<number>"
  },

  "profit_and_loss": [
    {
      "description": "Revenue from Operations",
      "note_ref": "Note 22",
      "current_year": 45000000,
      "previous_year": 38000000,
      "is_heading": true,
      "sub_items": [
        {"description": "Sale of Products", "current_year": 42000000, "previous_year": 35000000},
        {"description": "Sale of Services", "current_year": 3000000, "previous_year": 3000000}
      ]
    }
  ],

  "balance_sheet": {
    "equity_and_liabilities": {
      "shareholders_equity": [
        {
          "description": "Share Capital",
          "note_ref": "Note 3",
          "current_year": 10000000,
          "previous_year": 10000000
        }
      ],
      "non_current_liabilities": [],
      "current_liabilities": []
    },
    "assets": {
      "non_current_assets": [],
      "current_assets": []
    }
  },

  "notes": {
    "Note 22": {
      "title": "Revenue from Operations",
      "items": [
        {
          "description": "Sale of Products — Domestic",
          "current_year": 40000000,
          "previous_year": 33000000
        },
        {
          "description": "Sale of Products — Export",
          "current_year": 2000000,
          "previous_year": 2000000
        },
        {
          "description": "Sale of Services",
          "current_year": 3000000,
          "previous_year": 3000000
        }
      ],
      "total": {"current_year": 45000000, "previous_year": 38000000}
    }
  },

  "depreciation_schedule": [
    {
      "asset_class": "Plant & Machinery",
      "gross_block_opening": 50000000,
      "additions": 5000000,
      "deletions": 0,
      "gross_block_closing": 55000000,
      "accumulated_dep_opening": 20000000,
      "depreciation_for_year": 5000000,
      "accumulated_dep_closing": 25000000,
      "net_block_opening": 30000000,
      "net_block_closing": 30000000,
      "dep_rate": "15%",
      "dep_method": "WDV"
    }
  ],

  "manufacturing_account": null,

  "other_schedules": [],

  "accounting_policies": {
    "depreciation_method": "WDV as per Companies Act 2013",
    "inventory_valuation": "Lower of cost or NRV",
    "revenue_recognition": "On transfer of significant risks and rewards"
  },

  "validation": {
    "pl_total_income": {"extracted": 45000000, "matches_document": true},
    "pl_total_expenses": {"extracted": 40000000, "matches_document": true},
    "pl_pat": {"extracted": 5000000, "matches_document": true},
    "bs_total_assets": {"extracted": 100000000, "matches_document": true},
    "bs_total_liabilities": {"extracted": 100000000, "matches_document": true},
    "bs_balanced": true,
    "issues_found": []
  }
}
```

## CRITICAL INSTRUCTIONS

1. **Do NOT skip any line items** — even small amounts matter for CMA mapping.
2. **Preserve EXACT descriptions** as written in the document. Don't normalize or clean text. "Salaries, Wages & Bonus" stays as "Salaries, Wages & Bonus".
3. **Numbers in brackets () or marked Cr.** = negative amounts. Store as negative numbers.
4. **Note the currency unit** (Rupees, Thousands, Lakhs, Crores) — this varies by company.
5. **If text is partially illegible**, extract what you can and mark with `[unclear]`.
6. **VALIDATE**: Check that extracted P&L totals match, BS balances, note totals match P&L/BS line items. Report any discrepancies in the validation section.
7. **Extract BOTH years** (current + previous) — we need both for the database.

## AFTER EXTRACTION

Once you output the JSON, do a self-check:
- Count total notes extracted vs notes referenced in P&L/BS — any missing?
- Do P&L expense sub-items sum to total expenses?
- Does BS balance (total assets = total equity + liabilities)?
- Flag any notes that seem incomplete

Output the complete JSON. This will be pasted into the main Opus window for CMA reverse engineering.
