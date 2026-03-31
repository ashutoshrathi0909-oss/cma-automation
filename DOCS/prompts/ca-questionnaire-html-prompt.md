# Prompt: Build Interactive CA Questionnaire (Single HTML File)

**Use this prompt in a fresh Claude Sonnet session. Copy-paste everything below.**

---

## TASK

Build a single self-contained HTML file (no external dependencies — inline CSS + JS) that serves as an interactive questionnaire for a Chartered Accountant (CA) to answer CMA classification questions. The CA is not technical — the UI must be clean, professional, and easy to use on a laptop or tablet.

## REQUIREMENTS

### 1. Overall Structure

- **Single HTML file**, no frameworks, no CDN links — everything inline
- Professional look: clean white background, subtle borders, good typography (system fonts)
- Color scheme: Use a warm professional palette — dark navy headers (#1a365d), white cards, orange accent (#e67e22) for the AI's suggested answer, green (#27ae60) for selected answers
- Mobile-responsive (CA might use tablet)
- Progress bar at top showing "X of 43 questions answered"
- Sections collapsible — click section header to expand/collapse

### 2. Question Format

Each question should be a **card** with:

```
┌─────────────────────────────────────────────────────┐
│ Q1a. Staff Welfare Expenses                         │
│                                                     │
│ AI Suggests: Row 67 (Salary) ← orange highlight     │
│                                                     │
│ ○ Row 45 — Wages (Manufacturing Expenses)           │
│ ○ Row 67 — Salary and staff expenses (Admin)  ★     │
│ ○ Row 49 — Others (Manufacturing)                   │
│ ○ Other: [________] (free text for row number)      │
│                                                     │
│ Confidence: ○ Certain  ○ Usually  ○ Depends          │
│ Notes: [___________________________________]        │
│                                                     │
│ [▶ Show Examples]  ← collapsible                    │
│ ┌─────────────────────────────────────────────────┐ │
│ │ 📄 From BCIPL (Manufacturing, FY2021):          │ │
│ │    "Staff Welfare Expenses" — Rs 2,14,500       │ │
│ │    Section: Employee Benefits Expense            │ │
│ │                                                 │ │
│ │ 📄 From INPL (Manufacturing, FY2023):           │ │
│ │    "Staff Welfare" — Rs 1,87,000                │ │
│ │    Section: Other Expenses                       │ │
│ │                                                 │ │
│ │ 💡 Why AI picked Row 67: "Staff" keyword        │ │
│ │    matches salary pattern. But some GTs          │ │
│ │    map welfare items to Wages (R45).             │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### 3. Answer Options

For each question, show:
- **Radio buttons** for the main CMA row options (2-5 options per question)
- Each option shows: `Row [number] — [CMA field name] ([section name])`
- The **AI's suggested answer** gets a small orange "★ AI Suggests" badge
- An **"Other"** option with a free-text input for row number + name
- A **confidence** selector: Certain / Usually / Depends on context
- A **notes** text field (optional — for CA to write conditions like "only for manufacturing")

### 4. Collapsible Examples

Each question has a "Show Examples" button that expands to show:
- **2 real examples** from the extraction data (company name, item text, amount in Rs, section header, financial year)
- **AI's reasoning** — a 1-2 sentence explanation of why the model chose what it chose and why it might be wrong
- Examples should be formatted clearly with company name, amount, and section

### 5. Export Functionality

At the bottom of the page:
- **"Export Answers" button** — generates a JSON blob and:
  - Downloads it as `ca_answers_YYYY-MM-DD.json`
  - Also displays it in a copyable textarea (in case download doesn't work)
- **JSON format:**

```json
{
  "metadata": {
    "answered_by": "CA Name (text input at top)",
    "date": "2026-03-26",
    "total_questions": 43,
    "answered": 38,
    "skipped": 5
  },
  "answers": [
    {
      "question_id": "Q1a",
      "item_text": "Staff Welfare Expenses",
      "section": "A_wages_vs_salary",
      "selected_row": 67,
      "selected_name": "Salary and staff expenses",
      "ai_suggested_row": 67,
      "agreed_with_ai": true,
      "confidence": "certain",
      "notes": "",
      "depends_on": null
    },
    {
      "question_id": "Q2",
      "item_text": "Wages vs Salary general rule",
      "section": "A_wages_vs_salary",
      "selected_row": null,
      "selected_name": null,
      "ai_suggested_row": null,
      "agreed_with_ai": null,
      "confidence": "depends",
      "notes": "Manufacturing section = Row 45, Admin section = Row 67",
      "depends_on": "section_header"
    }
  ],
  "general_rules": [
    {
      "rule_id": "Q41",
      "question": "Nature vs section placement",
      "answer": "nature",
      "notes": "Always classify by nature of item"
    }
  ]
}
```

### 6. Additional Features

- **"Select All AI Suggestions"** button at top — pre-fills all answers with AI suggestion (CA can then just review and change the ones they disagree with)
- **Unanswered questions highlighted** in light red when trying to export
- **Auto-save** to localStorage every time an answer changes (so CA doesn't lose work if browser closes)
- **Restore from localStorage** on page load with a small banner: "Previous answers found. [Restore] [Start Fresh]"
- Section-level summary: "Section A: 8/10 answered" next to each section header

---

## QUESTION DATA

Below is the complete data for all 43 questions. Build the HTML with this data hardcoded.

### SECTION A: Wages vs Salary Boundary (Row 45 vs Row 67)

Context for CA: "The CMA has two employee cost rows: Row 45 = Wages (in Manufacturing Expenses section) and Row 67 = Salary and staff expenses (in Admin & Selling Expenses section). Our AI classifier confuses these ~15 times across 9 companies."

**Q1a. Staff Welfare Expenses**
- Options: Row 45 (Wages), Row 67 (Salary and staff expenses)
- AI Suggests: Row 67
- Examples:
  - BCIPL (Manufacturing, FY2021): "Staff Welfare Expenses" — Rs 2,14,500, Section: Employee Benefits
  - Kurunji Retail (Trading, FY2023): "Staff Welfare" — Rs 85,000, Section: P&L Debit Side
- AI Reasoning: "Staff" keyword matches salary/staff pattern, but some ground truths map welfare to Wages (R45) since welfare is a labor cost.

**Q1b. Gratuity / Gratuity to Employees**
- Options: Row 45 (Wages), Row 67 (Salary and staff expenses)
- AI Suggests: Row 67
- Examples:
  - INPL (Manufacturing, FY2023): "Gratuity to Employees" — Rs 3,50,000, Section: Employee Benefits
  - BCIPL (Manufacturing, FY2022): "Gratuity" — Rs 1,25,000, Section: Employee Benefits
- AI Reasoning: Gratuity is a retirement benefit. Model confused because it appears alongside both wage and salary items.

**Q1c. Contribution to EPF**
- Options: Row 45 (Wages), Row 67 (Salary and staff expenses)
- AI Suggests: Row 67
- Examples:
  - Dynamic Air (Manufacturing, FY2023): "(d) Contribution to EPF and ESI" — Rs 4,80,000, Section: Employee Benefits
  - INPL (Manufacturing, FY2023): "Contribution to Provident Fund" — Rs 2,15,000, Section: Employee Benefits
- AI Reasoning: EPF contributions often listed under employee benefits. Model picks R67 but some GTs say R45.

**Q1d. Contribution to ESI**
- Options: Row 45 (Wages), Row 67 (Salary and staff expenses)
- AI Suggests: Row 45
- Examples:
  - Kurunji Retail (Trading, FY2023): "ESI" — Rs 12,500, Section: P&L Debit Side
  - INPL (Manufacturing, FY2023): "ESI Contribution" — Rs 95,000, Section: Other Expenses
- AI Reasoning: ESI is a statutory labor cost, typically factory-floor. But some companies list it under admin.

**Q1e. Staff Mess Expenses**
- Options: Row 45 (Wages), Row 67 (Salary and staff expenses)
- AI Suggests: Row 67
- Examples:
  - Kurunji Retail (Trading, FY2023): "Staff Mess Expenses" — Rs 45,000, Section: P&L Debit Side
- AI Reasoning: "Staff" keyword pulls to R67. Could be manufacturing overhead (R45) if it's a factory canteen.

**Q1f. Leave Encashment**
- Options: Row 45 (Wages), Row 67 (Salary and staff expenses), Row 249 (Creditors for Expenses), Row 250 (Other current liabilities)
- AI Suggests: Row 67
- Examples:
  - BCIPL (Manufacturing, FY2022): "Leave Encashment" — Rs 1,85,000, Section: Short-term Provisions
- AI Reasoning: Leave encashment is an employee benefit but when appearing under current liabilities it might be a provision (R249/R250).

**Q1g. Bonus**
- Options: Row 45 (Wages), Row 67 (Salary and staff expenses)
- AI Suggests: Row 45
- Examples:
  - INPL (Manufacturing, FY2023): "Bonus" — Rs 4,50,000, Section: Employee Benefits
- AI Reasoning: Bonus is a statutory payment to workers under the Payment of Bonus Act — typically classified as wages.

**Q1h. "Salary, Wages and Bonus" (combined line)**
- Options: Row 45 (Wages), Row 67 (Salary and staff expenses)
- AI Suggests: Row 67
- Examples:
  - INPL (Manufacturing, FY2023): "Salary, Wages and Bonus" — Rs 9,592,430, Section: Employee Benefits (Note 25)
- AI Reasoning: Combined line with "Salary" first. Model picks R67 because "Salary" is the leading keyword. Some GTs say R45 (Wages) for manufacturing companies.

**Q1i. "Employee Benefits Expense" (combined line)**
- Options: Row 45 (Wages), Row 67 (Salary and staff expenses)
- AI Suggests: Row 67
- Examples:
  - Dynamic Air (Manufacturing, FY2023): "Employee Benefits Expense" — Rs 12,50,000, Section: Employee Benefits
- AI Reasoning: Generic header — could be either. Model defaults to R67 because "Employee" sounds admin.

**Q1j. Labour Charges Paid**
- Options: Row 45 (Wages), Row 67 (Salary and staff expenses)
- AI Suggests: Row 45
- Examples:
  - INPL (Manufacturing, FY2023): "Labour charges Paid" — Rs 6,75,000, Section: Other Expenses
- AI Reasoning: "Labour" is clearly manufacturing. But was routed to admin_expense section, so R45 wasn't available — routing bug.

**Q2. General Rule: Section-based or always one row?**
- Type: Open-ended
- AI Suggests: "If manufacturing company AND item under direct/manufacturing expenses → Row 45; if under admin → Row 67"
- Context: The ambiguity is whether the SECTION in the financial statement matters or whether it's always one row.

### SECTION B: The "Others" Problem (Row 49 vs Row 71 vs Row 75)

Context for CA: "Three 'Others' rows exist: Row 49 (Manufacturing Others), Row 71 (Admin Others), Row 75 (Misc Expenses Written off). The AI defaults to Row 71 too often."

**Q3a. Miscellaneous Expenses**
- Options: Row 49, Row 71, Row 75
- AI Suggests: Row 71
- Examples:
  - MSL (Manufacturing, FY2025): "Miscellaneous Expenses" — Rs 1,23,000, Section: Other Expenses
  - SLIPL (Manufacturing, FY2023): "Miscellenious Expenses" (sic) — Rs 67,000, Section: Other Expenses
- AI Reasoning: "Miscellaneous" name matches R75 literally, but R71 (Others) is the correct P&L catch-all. R75 is only for write-offs.

**Q3b. Selling & Distribution Expenses**
- Options: Row 69 (Bad Debts), Row 70 (Advertisements and Sales Promotions), Row 71 (Others), Row 72 (Repairs & Maintenance)
- AI Suggests: Row 70
- Examples:
  - BCIPL (Manufacturing, FY2021): "Selling & Distribution Expenses" — Rs 3,45,000, Section: Other Expenses
  - Dynamic Air (Manufacturing, FY2023): "Selling & Distribution Expenses" — Rs 5,20,000, Section: Admin Expenses
- AI Reasoning: Selling expenses are sales-related → R70 (Ads & Sales). But GT sometimes says R69 or R72 which seems wrong.

**Q3c. Administrative & General Expenses**
- Options: Row 69, Row 70, Row 71
- AI Suggests: Row 71
- Examples:
  - BCIPL (Manufacturing, FY2022): "Administrative & General Expenses" — Rs 2,10,000, Section: Other Expenses
- AI Reasoning: Generic admin → Others (R71). GT says R69 (Bad Debts) which seems like a GT error.

**Q3d. Carriage Outward**
- Options: Row 47 (Freight), Row 70 (Ads & Sales Promotions), Row 71 (Others)
- AI Suggests: Row 70
- Examples:
  - Dynamic Air (Manufacturing, FY2023): "Carriage Outward" — Rs 8,50,000, Section: Other Expenses
  - MSL (Manufacturing, FY2025): "Carriage Outward" — Rs 2,56,440, Section: Admin Expenses
- AI Reasoning: Carriage Outward is a selling/distribution cost → R70. Not freight inward (R47).

**Q3e. Brokerage & Commission**
- Options: Row 70 (Ads & Sales), Row 71 (Others)
- AI Suggests: Row 70
- Examples:
  - Dynamic Air (Manufacturing, FY2023): "Brokerage & Commission" — Rs 3,20,000, Section: Other Expenses
- AI Reasoning: Brokerage is a sales cost → R70. Model defaulted to R71 because no explicit keyword match.

**Q3f. Licence & Subscription Fees**
- Options: Row 68 (Rent, Rates and Taxes), Row 71 (Others)
- AI Suggests: Row 68
- Examples:
  - SLIPL (Manufacturing, FY2023): "Licence And Subscription" — Rs 45,000, Section: Other Expenses
- AI Reasoning: Licences are similar to rates/taxes → R68. But model picked R71 (Others).

**Q4. Row 75 usage rule**
- Type: Open-ended
- AI Suggests: "Row 75 is ONLY for actual write-offs (amortisation of preliminary expenses, etc.). Regular 'Miscellaneous Expenses' → Row 71"

### SECTION C: Carriage / Freight Classification

**Q5. Carriage Inward / Freight Inward**
- Options: Row 41 (Raw Materials Consumed), Row 47 (Freight and Transportation Charges)
- AI Suggests: Row 47
- Examples:
  - MSL (Manufacturing, FY2025): "Carriage Inwards" — Rs 2,56,440, Section: Manufacturing Expenses (Note 21)
  - BCIPL (Manufacturing, FY2021): "Freight Inward" — Rs 4,50,000, Section: Direct Expenses
- AI Reasoning: Current rule says R41 but V3 interview says it should be R47. Existing rule_engine has C-003 pointing to R47.

**Q6. Carriage Outward**
- Options: Row 47 (Freight), Row 70 (Ads & Sales)
- AI Suggests: Row 70
- Examples: Same as Q3d above
- AI Reasoning: Outward freight is a selling expense, not a manufacturing transport cost.

### SECTION D: P&L Stock vs Balance Sheet Stock

Context for CA: "CMA has stock items in P&L (rows 53-59) AND Balance Sheet (rows 200-201). Model confuses them."

**Q7. P&L Context stocks**
- Sub-items with options:
  - Closing Stock WIP: Row 54 vs Row 200 (AI suggests R54)
  - Opening Stock WIP: Row 53 vs Row 200 (AI suggests R53)
  - Closing Stock FG: Row 59 vs Row 201 (AI suggests R59)
  - Opening Stock FG: Row 57 vs Row 201 (AI suggests R57 or R58)
- Examples:
  - SR Papers (Manufacturing): "Closing Stock - Finished Goods" — Rs 12,50,000, Section: Changes in Inventories
  - INPL (Manufacturing): "Finished Goods" — Rs 8,30,000, Section: Inventories (BS)

**Q8. BS Context stocks**
- WIP in BS → Row 200 (AI suggests R200)
- FG in BS → Row 201 (AI suggests R201)

**Q9. General rule**
- AI Suggests: "P&L context → P&L rows (53-59), BS context → BS rows (200-201)"

### SECTION E: Finance Cost Items Under "Other Expenses"

**Q10a-h.** Each item as separate question card with:
- a. Bank Charges — AI suggests R85, options R83/R84/R85/R71
- b. Interest on Delay in Payment of Taxes — AI suggests R83, options R83/R84/R71
- c. Forex Rate Fluctuation Loss — AI suggests R91, options R90/R91/R71
- d. Liquidated Damages — AI suggests R83, options R83/R71
- e. Bill Discounting Charges — AI suggests R83, options R83/R84/R133
- f. Interest on Bill Discounting — AI suggests R84, options R83/R84/R133
- g. Loan/Overdraft Processing Fee — AI suggests R84, options R83/R84/R85
- h. Interest on CC A/c — AI suggests R84, options R83/R84

**Q11. Forex Loss row**
- AI Suggests: Row 91 (for loss), Row 32 (for gain)

### SECTION F: Manufacturing vs Admin Routing

**Q12a-g.** Each as separate card. AI suggests manufacturing rows for all.
**Q13.** General rule — AI suggests: "Nature of item matters more than section header"

### SECTION G: Reserves & Surplus

**Q14.** Surplus opening → AI suggests Row 106
**Q15.** Issue of Bonus Shares → AI suggests Row 108

### SECTION H: Borrowings

**Q16.** Current Maturities of LT Debt → AI suggests Row 136
**Q17.** Vehicle HP Current Maturities → AI suggests Row 140
**Q18.** Bank Loan Current Maturities → AI suggests Row 136
**Q19.** Unsecured Loans from Directors → AI suggests Row 152
**Q20.** Other Long Term Liability → AI suggests Row 153

### SECTION I: Audit Fees & Directors Remuneration

**Q21.** Directors Remuneration → AI suggests Row 67
- Auditor's Remuneration Statutory → AI suggests Row 73
- Auditor's Remuneration Tax Audit → AI suggests Row 73

### SECTION J: Specific Items (Q22-Q40)

Use the data from the markdown document below for all items. Each gets its own card with options, AI suggestion, and examples.

### SECTION K: General Rules (Q41-Q43)

**Q41.** Nature vs placement → AI suggests "Nature"
**Q42.** Trading company items → AI suggests "Manufacturing rows still"
**Q43.** Loan Processing Fee → AI suggests R84

---

## CMA ROW REFERENCE TABLE

Include a collapsible "CMA Row Reference" at the top of the page with this data (so the CA can look up any row):

```
Operating Statement — Income:
  Row 22 | II_A1  | Domestic
  Row 23 | II_A2  | Exports
  Row 25 | II_A4  | Less Excise Duty and Cess

Operating Statement — Non-Operating Income:
  Row 29 | II_B1  | Dividends received
  Row 30 | II_B2  | Interest Received
  Row 31 | II_B3  | Profit on sale of fixed assets / Investments
  Row 32 | II_B4  | Gain on Exchange Fluctuations
  Row 33 | II_B5  | Extraordinary income
  Row 34 | II_B6a | Others

Operating Statement — Manufacturing Expenses:
  Row 41 | II_C1  | Raw Materials Consumed (Imported)
  Row 42 | II_C2  | Raw Materials Consumed (Indigenous)
  Row 43 | II_C3  | Stores and spares consumed (Imported)
  Row 44 | II_C4  | Stores and spares consumed (Indigenous)
  Row 45 | II_C5  | Wages
  Row 46 | II_C6  | Processing / Job Work Charges
  Row 47 | II_C7  | Freight and Transportation Charges
  Row 48 | II_C8  | Power, Coal, Fuel and Water
  Row 49 | II_C9  | Others
  Row 50 | II_C10 | Repairs & Maintenance
  Row 51 | II_C10a| Security Service Charges
  Row 53 | II_C12 | Stock in process Opening Balance
  Row 54 | II_C13a| Stock in process Closing Balance
  Row 56 | II_C14 | Depreciation
  Row 57 | II_C16 | Finished Goods Opening Balance (approx)
  Row 58 | II_C17 | Finished Goods Opening Balance
  Row 59 | II_C18a| Finished Goods Closing Balance

Operating Statement — Admin & Selling Expenses:
  Row 67 | II_D1  | Salary and staff expenses
  Row 68 | II_D2  | Rent, Rates and Taxes
  Row 69 | II_D3  | Bad Debts
  Row 70 | II_D4  | Advertisements and Sales Promotions
  Row 71 | II_D5  | Others
  Row 72 | II_D6  | Repairs & Maintenance
  Row 73 | II_D7  | Audit Fees & Directors Remuneration
  Row 74 | II_E3b | Advances Written Off (approx)
  Row 75 | II_E3a | Miscellaneous Expenses Written off

Operating Statement — Finance Charges:
  Row 83 | II_F1  | Interest on Fixed Loans / Term loans
  Row 84 | II_F2  | Interest on Working capital loans
  Row 85 | II_F3  | Bank Charges

Operating Statement — Non-Operating Expenses:
  Row 89 | II_G1  | Loss on sale of fixed assets
  Row 90 | II_G2  | Sundry Balances Written off
  Row 91 | II_G3  | Loss on Exchange Fluctuations
  Row 93 | II_G5  | Others

Operating Statement — Tax:
  Row 99  | II_H1  | Income Tax provision
  Row 100 | II_H2  | Deferred Tax Liability
  Row 101 | II_H3  | Deferred Tax Asset

Operating Statement — Profit Appropriation:
  Row 105 | II_I1  | (Row 105 — surplus/reserves link)
  Row 106 | II_I2  | Brought forward from previous year
  Row 108 | II_I4  | Other Appropriation of profit

Balance Sheet — Share Capital:
  Row 116 | III_L1  | Issued, Subscribed and Paid up
  Row 117 | III_L1a | Share Application Money

Balance Sheet — Reserves and Surplus:
  Row 121 | III_L2a | General Reserve
  Row 122 | III_L2b | Balance transferred from P&L a/c
  Row 123 | III_L2c | Share Premium A/c
  Row 125 | III_L2e | Other Reserves

Balance Sheet — Working Capital Bank Finance:
  Row 130 | III_L10j| (Bank liabilities)
  Row 131 | III_L3a | From Indian Bank
  Row 132 | III_L3b | From Other Banks
  Row 133 | III_L3c | (o/s bill discounting, LC)

Balance Sheet — Term Loans:
  Row 135 | III_CL6 | Current maturities (approx)
  Row 136 | III_L4a | Term Loan Repayable in next one year
  Row 137 | III_L4b | Balance Repayable after one year

Balance Sheet — Debentures:
  Row 140 | III_L5a | Repayable in next one year
  Row 141 | III_L5b | Balance Repayable after one year

Balance Sheet — Other Debts:
  Row 148 | III_L7a | Repayable in next one year
  Row 149 | III_L7b | Balance Other Debts

Balance Sheet — Unsecured Loans:
  Row 151 | III_L8d | Directors' Loans (Quasi Equity)
  Row 152 | III_L8a | As Quasi Equity
  Row 153 | III_L8b | As Long Term Debt
  Row 154 | III_L8c | As Short Term Debt

Balance Sheet — Deferred Tax:
  Row 159 | III_L9  | Deferred tax liability

Balance Sheet — Fixed Assets:
  Row 161 | III_A   | Gross Block (Tangible) header
  Row 162 | III_A1  | Gross Block
  Row 163 | III_A2  | Less Accumulated Depreciation
  Row 165 | III_A4  | Capital Work in Progress

Balance Sheet — Intangibles:
  Row 169 | III_A5  | Patents / goodwill
  Row 171 | III_A7  | Deferred Tax Asset (BS)
  Row 172 | III_A8  | Other Intangible assets

Balance Sheet — Investments:
  Row 182-188 | Various investment rows

Balance Sheet — Inventories:
  Row 193 | III_A10a| Raw Materials (Imported)
  Row 194 | III_A10b| Raw Materials (Indigenous)
  Row 197 | III_A11a| Stores & Spares (Imported)
  Row 198 | III_A11b| Stores & Spares (Indigenous)
  Row 200 | III_A12 | Stocks-in-process
  Row 201 | III_A13 | Finished Goods

Balance Sheet — Receivables:
  Row 206 | III_A15a| Domestic Receivables
  Row 208 | III_A15c| Debtors more than 6 months

Balance Sheet — Cash:
  Row 212-215 | Cash and Bank Balances

Balance Sheet — Loans and Advances:
  Row 218 | III_A18 | (GST/tax related)
  Row 219 | III_A19a| Advances recoverable
  Row 221 | III_A19c| Advance Income Tax
  Row 223 | III_A19e| Other Advances
  Row 224 | III_A19f| Prepaid Expenses

Balance Sheet — Non-Current Assets:
  Row 231 | III_A23 | Trade receivables > 6 months
  Row 235 | III_A27 | Dues from directors/partners
  Row 236 | III_A28 | Advances to suppliers of capital goods
  Row 237 | III_A29 | Security deposits with govt
  Row 238 | III_A30 | Other non-current assets

Balance Sheet — Current Liabilities:
  Row 242 | III_CL1 | Sundry Creditors
  Row 243 | III_CL2 | Advance received from customers
  Row 246 | III_CL3b| Statutory Liabilities
  Row 248 | III_CL5 | Interest Accrued and due
  Row 249 | III_CL6a| Creditors for Expenses
  Row 250 | III_CL7 | Other current liabilities
```

---

## DESIGN NOTES

1. **Header**: "CMA Classification — CA Expert Review" with a subtitle: "43 questions from accuracy testing of 9 companies (1,326 items)"
2. **CA Name input** at the top (required for export)
3. **Sections** are accordion-style — only one open at a time, or all expandable
4. **Visual hierarchy**: Section letter (A-K) in a colored circle, question number bold, item name in larger font
5. **The AI suggestion should look like a gentle recommendation, not a forced choice** — badge saying "AI suggests" not "AI says"
6. **Make the "Other" row input smart** — when CA types a row number, auto-fill the row name from the reference table
7. **Export JSON structure must be exactly as specified above** — this will be machine-parsed

## SIZE CONSTRAINT

The HTML file should be self-contained and under 200KB. No images — use Unicode symbols and CSS for all visual elements.

---

## IMPORTANT: DO NOT HALLUCINATE DATA

All real-world examples in this prompt come from actual extraction data. Where I've written approximate amounts (e.g., "Rs 2,14,500"), keep those. Do NOT invent new company names or amounts — use only the companies listed: BCIPL, SR Papers, SSSS, INPL, MSL, SLIPL, Kurunji Retail, Dynamic Air, Mehta Computer.

For questions where I haven't provided specific examples, use a placeholder: "Example data not available — please use your professional judgment."
