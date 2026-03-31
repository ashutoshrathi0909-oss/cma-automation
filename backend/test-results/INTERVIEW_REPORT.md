# Model Interview Results — Genuinely Wrong Items

**Date:** 2026-03-26 11:01
**Total wrong across all companies:** 1163
**GT offset bugs (not real errors):** 864
**Genuinely wrong:** 299
**Unique (deduplicated):** 201
**Interviewed:** 100

## Root Cause Split

- **Routing bug** (correct row not in options): 45 (45%)
- **Model error** (correct row available, picked wrong): 55 (55%)

## Items Where Correct Row Was NOT In Options (Routing Fix Needed)

| # | Item | Section | Correct Row | Predicted Row | Company | Routed To |
|---|------|---------|-------------|---------------|---------|-----------|
| 1 | Profit on Sale of Fixed Asset | Other Income | 22 (Domestic) | 31 (Profit on sale of fixed assets / Investments) | BCIPL | other_income |
| 2 | Sale of Duty Credit Scrips | Other Income | 22 (Domestic) | 34 (Others) | BCIPL | other_income |
| 7 | Rent | Other Expenses | 48 (Power, Coal, Fuel and Water) | 68 (Rent , Rates and Taxes) | BCIPL | admin_expense |
| 8 | Finished Goods (Opening) | Changes in Inventori | 57 (Row 57) | 201 (Finished Goods) | BCIPL | inventories,raw_materials |
| 10 | Directors Remuneration | Salaries & Wages | 66 (Row 66) | 73 (Audit Fees & Directors Remuneration) | BCIPL | employee_cost |
| 19 | Advances Written off | Other Expenses | 74 (Row 74) | 69 (Bad Debts) | BCIPL | admin_expense |
| 20 | Interest of Income Tax | Finance Costs | 82 (Row 82) | 99 (Income Tax  provision) | BCIPL | tax,finance_cost |
| 23 | Bank Charges | Other Expenses | 84 (Interest on Working capital loans) | 71 (Others) | BCIPL | admin_expense |
| 24 | Forex Rate Fluctuation Loss | Other Expenses | 90 (Sundry Balances Written off) | 71 (Others) | BCIPL | admin_expense |
| 26 | Surplus at the beginning of the year | Reserves & Surplus | 105 (Row 105) | 122 (Balance transferred from profit and loss a/c) | BCIPL | reserves |
| 27 | Other Bank Balances (Cr.) | Other Current Liabil | 130 (Row 130) | 213 (Bank Balances) | BCIPL | cash,current_liabilities |
| 30 | Current Maturities of Long-term Debt | Other Current Liabil | 135 (Row 135) | 250 (Other current liabilities) | BCIPL | current_liabilities |
| 31 | Current Maturities of Long-term Debt | Short-term Borrowing | 135 (Row 135) | None (DOUBT) | BCIPL | borrowings_short |
| 32 | Unsecured Loans from Directors | Long-term Borrowings | 151 (Row 151) | 153 (As Long Term Debt) | BCIPL | borrowings_long |
| 34 | Gross Block (Tangible) | Depreciation Schedul | 161 (Row 161) | None (DOUBT) | BCIPL | fixed_assets,depreciation |
| 38 | GST Input Recoverable | Other Current Assets | 218 (Row 218) | 223 (Other Advances / current asset) | BCIPL | other_assets |
| 39 | Exceeding 6 months | Trade Receivables | 231 (Row 231) | 208 (Debtors more than 6 months) | BCIPL | receivables |
| 42 | Long-term Loans and Advances | Non-Current Assets | 236 (Advances to suppliers of capital goods) | 153 (As Long Term Debt) | BCIPL | borrowings_long,fixed_assets |
| 44 | Other Non- Current Assets | Non-Current Assets | 237 (Security deposits with government departments) | 172 (Other Intangible assets) | BCIPL | fixed_assets |
| 53 | Interest on Delay in payment of taxes | Other Expenses - Adm | 83 (Interest on Fixed Loans / Term loans) | 71 (Others) | Dynamic_Air | admin_expense |
| 54 | Liquidty Damages | Other Expenses - Adm | 83 (Interest on Fixed Loans / Term loans) | 71 (Others) | Dynamic_Air | admin_expense |
| 57 | Surplus - Opening balance | Reserves and Surplus | 106 (Brought forward from previous year) | 122 (Balance transferred from profit and loss a/c) | Dynamic_Air | reserves |
| 58 | Rent - Factory | Cost of Materials Co | 68 (Rent , Rates and Taxes) | None (DOUBT) | Dynamic_Air | manufacturing_expense,raw_materials |
| 60 | Security Service Charges | Other Expenses - Adm | 51 (Security Service Charges) | 71 (Others) | Dynamic_Air | admin_expense |
| 63 | Loan from Banks - current maturities | Short-term Borrowing | 136 (Term Loan Repayable in next one year) | 131 (From Indian Bank) | Dynamic_Air | borrowings_short |
| 64 | Vehicle HP Loans - current maturities | Short-term Borrowing | 140 (Repayable in next one year) | 131 (From Indian Bank) | Dynamic_Air | admin_expense,borrowings_short |
| 66 | Vehicle HP Loans - current maturities | Short-term Borrowing | 140 (Repayable in next one year) | 71 (Others) | Dynamic_Air | admin_expense,borrowings_short |
| 71 | Labour charges Paid | Other Expenses | 45 (Wages) | 67 (Salary and staff expenses) | INPL | admin_expense |
| 74 | Material Handling Charges | Other Expenses | 46 (Processing / Job Work Charges) | 71 (Others) | INPL | admin_expense |
| 75 | Material Handling Charges (estimated) | Other Expenses | 46 (Processing / Job Work Charges) | 71 (Others) | INPL | admin_expense |
| 76 | Transportation charges | Other Expenses | 47 (Freight and Transportation Charges) | 71 (Others) | INPL | admin_expense |
| 77 | Transportation Charges (estimated) | Other Expenses | 47 (Freight and Transportation Charges) | 71 (Others) | INPL | admin_expense |
| 78 | Work in Progress | Inventories | 54 (Stock in process Closing Balance) | 200 (Stocks-in-process) | INPL | inventories |
| 79 | Finished Goods | Inventories | 59 (Finished Goods Closing Balance) | 201 (Finished Goods) | INPL | inventories |
| 85 | Surplus in profit and loss account: Bala | Reserves and Surplus | 106 (Brought forward from previous year) | 122 (Balance transferred from profit and loss a/c) | INPL | reserves |
| 86 | Surplus in P&L: Balance at beginning | Reserves and Surplus | 106 (Brought forward from previous year) | 122 (Balance transferred from profit and loss a/c) | INPL | reserves |
| 87 | Issue of Bonus Share (P&L surplus capita | Reserves and Surplus | 108 (Other Appropriation of profit) | 122 (Balance transferred from profit and loss a/c) | INPL | employee_cost,reserves |
| 91 | Display amount/Discount | P&L Account — Credit | 42 (Raw Materials Consumed ( Indigenous)) | None (DOUBT) | Kurunji_Retail | other_income |
| 92 | Opening Stock of Packing | P&L Account — Debit  | 44 (Stores and spares consumed ( Indigenous)) | 71 (Others) | Kurunji_Retail | admin_expense |
| 93 | Packing Expenses | P&L Account — Debit  | 44 (Stores and spares consumed ( Indigenous)) | 71 (Others) | Kurunji_Retail | admin_expense |
| 94 | Stock of Packing Materials | P&L Account — Credit | 44 (Stores and spares consumed ( Indigenous)) | 34 (Others) | Kurunji_Retail | other_income |
| 95 | Esi | P&L Account — Debit  | 45 (Wages) | 67 (Salary and staff expenses) | Kurunji_Retail | admin_expense |
| 98 | Electric Charges | P&L Account — Debit  | 48 (Power, Coal, Fuel and Water) | 71 (Others) | Kurunji_Retail | admin_expense |
| 99 | Tds on Rent | P&L Account — Debit  | 49 (Others) | 68 (Rent , Rates and Taxes) | Kurunji_Retail | admin_expense |
| 100 | Rent - Parking | P&L Account — Debit  | 49 (Others) | 68 (Rent , Rates and Taxes) | Kurunji_Retail | admin_expense |

## Items Where Model Had The Right Options But Chose Wrong

| # | Item | Correct | Predicted | V3 Explanation |
|---|------|---------|-----------|----------------|
| 3 | Other Materials Consumed | R41 (Raw Materials C) | R49 (Others) | **PART A — Why it went wrong:**   1. Yes, Row 41 (Raw Materials Consumed ( Imported)) was in the POSSIBLE CMA ROWS list. |
| 4 | Other Materials Consumed | R43 (Stores and spar) | R49 (Others) | **PART A — Why it went wrong:**   1. Yes, Row 43 was in the POSSIBLE CMA ROWS list.   2. I picked Row 49 because "Other  |
| 5 | Employee Benefits Expense | R44 (Stores and spar) | R67 (Salary and staf) | **PART A — Why it went wrong:**   1. Yes, Row 44 (Stores and spares consumed ( Indigenous)) was in the POSSIBLE CMA ROWS |
| 6 | Manufacturing Expenses | R48 (Power, Coal, Fu) | R64 (Other Manufactu) | **PART A — Why it went wrong:**   1. Yes, Row 48 was in the POSSIBLE CMA ROWS list.   2. I picked Row 64 because "Manufa |
| 9 | Finished Goods (Closing) | R58 (Finished Goods ) | R201 (Finished Goods) | **PART A — Why it went wrong:**   1. Yes, Row 58 (Finished Goods Opening Balance) was in the POSSIBLE CMA ROWS list.   2 |
| 11 | Selling & Distribution Expenses | R69 (Bad Debts) | R71 (Others) | **PART A — Why it went wrong:**   1. Yes, Row 69 (Bad Debts) was in the POSSIBLE CMA ROWS list.   2. I picked Row 71 (Ot |
| 12 | Administrative & General Expenses | R69 (Bad Debts) | R71 (Others) | **PART A — Why it went wrong:**   1. Yes, Row 69 (Bad Debts) was in the POSSIBLE CMA ROWS list.   2. I picked Row 71 (Ot |
| 13 | Rates & Taxes | R70 (Advertisements ) | R68 (Rent , Rates an) | **PART A — Why it went wrong:**   1. Yes, Row 70 was in the POSSIBLE CMA ROWS list.   2. I picked Row 68 because "Rates  |
| 14 | Bad debts written off | R70 (Advertisements ) | R69 (Bad Debts) | **PART A — Why it went wrong:**   1. Yes, Row 70 was in the POSSIBLE CMA ROWS list.   2. I picked Row 69 because "Bad de |
| 15 | Auditor's Remuneration - Statutory  | R70 (Advertisements ) | R73 (Audit Fees & Di) | ### PART A — Why it went wrong:   1. **Yes**, Row 70 was in the POSSIBLE CMA ROWS list.   2. **Incorrect pick reason:**  |
| 16 | Auditor's Remuneration - Tax Audit | R70 (Advertisements ) | R73 (Audit Fees & Di) | **PART A — Why it went wrong:**   1. Yes, Row 70 (Advertisements and Sales Promotions) was in the POSSIBLE CMA ROWS list |
| 17 | Advances Written off | R70 (Advertisements ) | R69 (Bad Debts) | **PART A — Why it went wrong:**   1. Yes, Row 70 (Advertisements and Sales Promotions) was in the POSSIBLE CMA ROWS list |
| 18 | Selling & Distribution Expenses | R72 (Repairs & Maint) | R71 (Others) | ### PART A — Why it went wrong: 1. **Yes**, Row 72 (Repairs & Maintenance) was in the POSSIBLE CMA ROWS list.   2. Picke |
| 21 | Bill Discounting Charges | R83 (Interest on Fix) | R133 ((o/s bill disco) | **PART A — Why it went wrong:**   1. Yes   2. Picked Row 133 due to "Bill Discounting" matching CA rule ("Bills discount |
| 22 | Interest on CC A/c | R83 (Interest on Fix) | RNone (DOUBT) | **PART A — Why it went wrong:**   1. **Yes**, Row 83 was in the POSSIBLE CMA ROWS list.   2. I picked "Row None" because |
| 25 | Deferred Tax | R100 (Deferred Tax Li) | R100 (Deferred Tax Li) | ### PART A — Why it went wrong:   1. **Yes**, Row 100 was in the POSSIBLE CMA ROWS list.   2. The rules explicitly state |
| 28 | Inland LC Discounting | R131 (From Indian Ban) | R133 ((o/s bill disco) | **PART A — Why it went wrong:**   1. Yes   2. "Inland LC Discounting" lacks explicit bank name, and "discounting" loosel |
| 29 | TATA Capital | R131 (From Indian Ban) | R131 (From Indian Ban) | **PART A — Why it went wrong:**   1. Yes, Row 131 (From Indian Bank) was in the POSSIBLE CMA ROWS list.   2. I picked Ro |
| 33 | Unsecured Loans (additional) | R152 (As Quasi Equity) | R137 (Balance Repayab) | **PART A — Why it went wrong:**   1. Yes, Row 152 (As Quasi Equity) was in the POSSIBLE CMA ROWS list.   2. I picked Row |
| 35 | Intangible Assets (Net Block) | R171 (Deferred Tax As) | R169 (Patents / goodw) | ### PART A — Why it went wrong:   1. **Yes**, Row 171 (Deferred Tax Asset) was in the POSSIBLE CMA ROWS list.   2. **Mis |
| 36 | Raw Materials | R193 (Imported) | R42 (Raw Materials C) | **PART A — Why it went wrong:**   1. **Yes** (Row 193 was in the list).   2. Picked Row 42 because:      - "Raw Material |
| 37 | Scraps | R197 (Imported) | RNone (DOUBT) | ### PART A — Why it went wrong:   1. **Yes** (Row 197 was in the POSSIBLE CMA ROWS list).   2. **Misclassification**: Th |
| 40 | Capital Advances | R235 (Dues from direc) | R223 (Other Advances ) | **PART A — Why it went wrong:**   1. Yes, Row 235 was in the POSSIBLE CMA ROWS list.   2. I picked Row 223 because "Capi |
| 41 | Capital Advances | R235 (Dues from direc) | R219 (Advances recove) | **PART A — Why it went wrong:**   1. Yes   2. "Capital Advances" lacked clear context (e.g., "to directors"). Row 219 wa |
| 43 | Other Non-Current Assets | R236 (Advances to sup) | R238 (Other non curre) | **PART A — Why it went wrong:**   1. Yes, Row 236 was in the POSSIBLE CMA ROWS list.   2. I picked Row 238 because "Othe |
| 45 | Leave Encashment | R243 (Advance receive) | RNone (DOUBT) | **PART A — Why it went wrong:**   1. **Yes**, Row 243 (Advance received from customers) was in the POSSIBLE CMA ROWS lis |
| 46 | Short-term Provisions | R248 (Interest Accrue) | R250 (Other current l) | **PART A — Why it went wrong:**   1. Yes, Row 248 (Interest Accrued and due) was in the POSSIBLE CMA ROWS list.   2. I p |
| 47 | Carriage Inwards | R47 (Freight and Tra) | R41 (Raw Materials C) | **PART A — Why it went wrong:**   1. Yes, Row 47 (Freight and Transportation Charges) was in the POSSIBLE CMA ROWS list. |
| 48 | Closing Stock - Work-in-Progress | R54 (Stock in proces) | R200 (Stocks-in-proce) | **PART A — Why it went wrong:**   1. Yes, Row 54 (Stock in process Closing Balance) was in the POSSIBLE CMA ROWS list.   |
| 49 | Closing Stock - Finished Goods | R59 (Finished Goods ) | R201 (Finished Goods) | **PART A — Why it went wrong:**   1. Yes, Row 59 (Finished Goods Closing Balance) was in the POSSIBLE CMA ROWS list.   2 |
| 50 | (d) Contribution to EPF and ESI | R67 (Salary and staf) | R45 (Wages) | **PART A — Why it went wrong:**   1. Yes, Row 67 (Salary and staff expenses) was in the POSSIBLE CMA ROWS list.   2. I p |
| 51 | Carriage Outward | R70 (Advertisements ) | R71 (Others) | **PART A — Why it went wrong:**   1. Yes, Row 70 (Advertisements and Sales Promotions) was in the POSSIBLE CMA ROWS list |
| 52 | Brokerage & Commission | R70 (Advertisements ) | R71 (Others) | **PART A — Why it went wrong:**   1. Yes   2. "Brokerage & Commission" lacked explicit keywords matching Row 70, and no  |
| 55 | (b) Interest on Bill discounting &  | R84 (Interest on Wor) | R133 ((o/s bill disco) | ### PART A — Why it went wrong: 1. **No**, Row 84 (Interest on Working capital loans) was not in the POSSIBLE CMA ROWS l |
| 56 | (a) Loan/Overdraft Processing Fee | R84 (Interest on Wor) | R85 (Bank Charges) | **PART A — Why it went wrong:**   1. Yes, Row 84 (Interest on Working capital loans) was in the POSSIBLE CMA ROWS list.  |
| 59 | (a) Loan/Overdraft Processing Fee | R83 (Interest on Fix) | R85 (Bank Charges) | **PART A — Why it went wrong:**   1. Yes, Row 83 (Interest on Fixed Loans / Term loans) was in the POSSIBLE CMA ROWS lis |
| 61 | (c) Staff Welfare Expenses | R67 (Salary and staf) | R45 (Wages) | **PART A — Why it went wrong:**   1. Yes, Row 67 (Salary and staff expenses) was in the POSSIBLE CMA ROWS list.   2. I p |
| 62 | (3) Deferred tax Liability / (Asset | R101 (Deferred Tax As) | R159 (Deferred tax li) | **PART A — Why it went wrong:**   1. Yes, Row 101 (Deferred Tax Asset) was in the POSSIBLE CMA ROWS list.   2. I picked  |
| 65 | Vehicle HP Loans - non-current | R141 (Balance Repayab) | R149 (Balance Other D) | ### PART A — Why it went wrong:   1. **Yes**, Row 141 ("Balance Repayable after one year") was in the POSSIBLE CMA ROWS  |
| 67 | Provision for employee benefits (Gr | R153 (As Long Term De) | R67 (Salary and staf) | **PART A — Why it went wrong:**   1. Yes, Row 153 (As Long Term Debt) was in the POSSIBLE CMA ROWS list.   2. I picked R |
| 68 | (b) Outstanding expenses - (i) Sala | R249 (Creditors for E) | R67 (Salary and staf) | **PART A — Why it went wrong:**   1. Yes, Row 249 (Creditors for Expenses) was in the POSSIBLE CMA ROWS list.   2. I pic |
| 69 | Changes in work-in-progress and sto | R42 (Raw Materials C) | R200 (Stocks-in-proce) | **PART A — Why it went wrong:**   1. **Yes**, Row 42 was in the list.   2. Picked Row 200 because "work-in-progress" exp |
| 70 | Purchase at Stock in Trade | R42 (Raw Materials C) | R49 (Others) | ### PART A — Why it went wrong:   1. **Yes** (Row 42 was in the POSSIBLE CMA ROWS list).   2. **Root Cause**: The classi |
| 72 | Staff Welfare Expenses | R45 (Wages) | R67 (Salary and staf) | **PART A — Why it went wrong:**   1. **Yes**, Row 45 (Wages) was in the POSSIBLE CMA ROWS list.   2. I picked Row 67 (Sa |
| 73 | Gratuity to Employees | R45 (Wages) | R67 (Salary and staf) | **PART A — Why it went wrong:**   1. **Yes**   2. Misinterpreted "Gratuity" as a generic staff expense (Row 67) despite  |
| 80 | Salary, Wages and Bonus | R67 (Salary and staf) | R45 (Wages) | **PART A — Why it went wrong:**   1. **Yes**   2. Your CA expert rules and examples overwhelmingly associate "Salary, Wa |
| 81 | Contribution to Provident Fund and  | R67 (Salary and staf) | R45 (Wages) | **PART A — Why it went wrong:**   1. Yes, Row 67 (Salary and staff expenses) was in the POSSIBLE CMA ROWS list.   2. I p |
| 82 | Licence And Subscription | R68 (Rent , Rates an) | R71 (Others) | ### PART A — Why it went wrong:    1. **Yes**, Row 68 (Rent, Rates and Taxes) was in the POSSIBLE CMA ROWS list.   2. ** |
| 83 | Miscellenious Expenses | R71 (Others) | R75 (Miscellaneous E) | **PART A — Why it went wrong:**   1. Yes, Row 71 (Others) was in the POSSIBLE CMA ROWS list.   2. I picked Row 75 becaus |
| 84 | Miscellaneous Expenses | R71 (Others) | R75 (Miscellaneous E) | **PART A — Why it went wrong:**   1. Yes, Row 71 (Others) was in the POSSIBLE CMA ROWS list.   2. I picked Row 75 becaus |
| 88 | Other Long Term Liability | R153 (As Long Term De) | RNone (DOUBT) | ### PART A — Why it went wrong: 1. **Yes**, Row 153 (As Long Term Debt) was in the POSSIBLE CMA ROWS list. 2. You picked |
| 89 | Raw materials + Packing + Consumabl | R194 (Indigenous) | R42 (Raw Materials C) | **PART A — Why it went wrong:**   1. Yes, Row 194 (Indigenous) was in the POSSIBLE CMA ROWS list.   2. I picked Row 42 b |
| 90 | Other Liabilities (Directors + Rela | R249 (Creditors for E) | R250 (Other current l) | ### PART A — Why it went wrong: 1. **Yes**, Row 249 (Creditors for Expenses) was in the POSSIBLE CMA ROWS list.   2. **R |
| 96 | Staff Welfare | R45 (Wages) | R67 (Salary and staf) | ### PART A — Why it went wrong:   1. **Yes**, Row 45 (Wages) was in the POSSIBLE CMA ROWS list.   2. **You picked Row 67 |
| 97 | Staff Mess Expenses | R45 (Wages) | R67 (Salary and staf) | **PART A — Why it went wrong:**   1. Yes, Row 45 (Wages) was in the POSSIBLE CMA ROWS list.   2. I picked Row 67 because |

## Suggested Fixes (extracted from V3 responses)

These are the concrete fixes V3 suggested to make it get the right answer.
Review with CA before implementing.

- **Profit on Sale of Fixed Asset** (correct: Row 22 (Domestic), type: routing)
  - - *Add Row 22 (Domestic) to the POSSIBLE CMA ROWS list* **AND**

- **Profit on Sale of Fixed Asset** (correct: Row 22 (Domestic), type: routing)
  - - *Add a rule: "Domestic income → Row 22 (Domestic)"*.

- **Profit on Sale of Fixed Asset** (correct: Row 22 (Domestic), type: routing)
  - 5. **Python regex pattern** to route to Row 22:

- **Sale of Duty Credit Scrips** (correct: Row 22 (Domestic), type: routing)
  - - *"Add Row 22 | II_B7 | Export Incentives / Duty Credit Scrips" to POSSIBLE CMA ROWS list"*

- **Sale of Duty Credit Scrips** (correct: Row 22 (Domestic), type: routing)
  - - *"Add rule: 'Sale of Duty Credit Scrips' → Row 22 (Domestic)'"*

- **Sale of Duty Credit Scrips** (correct: Row 22 (Domestic), type: routing)
  - 5. **Python regex pattern**:

- **Other Materials Consumed** (correct: Row 41 (Raw Materials Consumed ( Imported)), type: prompt)
  - 4. Add a rule: "'Materials Consumed' → Row 41 (Raw Materials Consumed ( Imported)) or Row 42 (Raw Materials Consumed ( Indigenous))".

- **Other Materials Consumed** (correct: Row 41 (Raw Materials Consumed ( Imported)), type: prompt)
  - 5. Routing regex pattern:

- **Other Materials Consumed** (correct: Row 41 (Raw Materials Consumed ( Imported)), type: prompt)
  - This pattern would ensure "Materials Consumed" is routed to Row 41 or Row 42, avoiding Row 49.

- **Other Materials Consumed** (correct: Row 43 (Stores and spares consumed ( Imported)), type: prompt)
  - 4. Add a rule: "'Materials Consumed' → Row 43 (Stores and spares consumed ( Imported))" or add an example: "'Other Materials Consumed' → Row 43 (Stores and spares consumed ( Imported))".

- **Other Materials Consumed** (correct: Row 43 (Stores and spares consumed ( Imported)), type: prompt)
  - 5. Routing regex pattern: `r"(?i)\b(materials\s*consumed|stores|spares)\b"`.

- **Employee Benefits Expense** (correct: Row 44 (Stores and spares consumed ( Indigenous)), type: prompt)
  - 4. Add a rule: "Employee Benefits Expense → Row 44 (Stores and spares consumed ( Indigenous))" to explicitly override the default routing to Row 67.

- **Employee Benefits Expense** (correct: Row 44 (Stores and spares consumed ( Indigenous)), type: prompt)
  - 5. Routing regex pattern:

- **Employee Benefits Expense** (correct: Row 44 (Stores and spares consumed ( Indigenous)), type: prompt)
  - This pattern would directly route the item to Row 44 if explicitly defined in the rules.

- **Employee Benefits Expense** (correct: Row 44 (Stores and spares consumed ( Indigenous)), type: prompt)
  - **Summary:** The error occurred because Row 67 was a more specific match for "Employee Benefits Expense." Adding a rule or regex pattern to explicitly route this item to Row 44 would resolve the issue.

- **Manufacturing Expenses** (correct: Row 48 (Power, Coal, Fuel and Water), type: prompt)
  - 4. Add a rule: "Manufacturing Expenses related to power, coal, fuel, or water → Row 48 (Power, Coal, Fuel and Water)."

- **Manufacturing Expenses** (correct: Row 48 (Power, Coal, Fuel and Water), type: prompt)
  - 5. Routing regex pattern:

- **Rent** (correct: Row 48 (Power, Coal, Fuel and Water), type: routing)
  - 4. Add Row 48 (Power, Coal, Fuel and Water) to the POSSIBLE CMA ROWS list.

- **Rent** (correct: Row 48 (Power, Coal, Fuel and Water), type: routing)
  - 5. Regex pattern: `r"(electric|power|coal|fuel|water)"`

- **Rent** (correct: Row 48 (Power, Coal, Fuel and Water), type: routing)
  - The correct row (Row 48) was not in the options, so adding it to the list is essential. The regex pattern ensures items related to power, coal, fuel, or water are routed correctly.

- **Finished Goods (Opening)** (correct: Row 57 (Row 57), type: routing)
  - 3. The keyword **"(Opening)"** should have triggered routing to **Row 58 (Finished Goods Opening Balance)** (since "Opening" is explicitly linked to opening balances in examples like "Work in progress - Opening" → Row 53).

- **Finished Goods (Opening)** (correct: Row 57 (Row 57), type: routing)
  - 4. **"Add an example: 'Finished Goods (Opening)' → Row 58 (Finished Goods Opening Balance)'"**

- **Finished Goods (Opening)** (correct: Row 57 (Row 57), type: routing)
  - - *Reason*: The current examples exclude "(Opening)" logic for finished goods, though similar patterns exist for other categories (e.g., work-in-progress).

- **Finished Goods (Opening)** (correct: Row 57 (Row 57), type: routing)
  - 5. **Regex pattern**:

- **Finished Goods (Closing)** (correct: Row 58 (Finished Goods Opening Balance), type: prompt)
  - 4. Add a rule: "'Finished Goods (Closing)' → Row 58 (Finished Goods Opening Balance)".

- **Finished Goods (Closing)** (correct: Row 58 (Finished Goods Opening Balance), type: prompt)
  - 5. Routing regex pattern:

- **Directors Remuneration** (correct: Row 66 (Row 66), type: routing)
  - - "Add Row 66 (Row 66) to the POSSIBLE CMA ROWS list."

- **Directors Remuneration** (correct: Row 66 (Row 66), type: routing)
  - - Alternatively, "Add a rule: 'Directors Remuneration → Row 66 (Row 66)'."

- **Directors Remuneration** (correct: Row 66 (Row 66), type: routing)
  - 5. **If you had to write ONE routing regex pattern that would correctly route this item, what would it be?**

- **Directors Remuneration** (correct: Row 66 (Row 66), type: routing)
  - This pattern would match "Directors Remuneration" case-insensitively and route it to Row 66.

- **Selling & Distribution Expenses** (correct: Row 69 (Bad Debts), type: prompt)
  - 4. Add a rule: "Selling & Distribution Expenses → Row 69 (Bad Debts)" or add an example: "Selling & Distribution Expenses" → Row 69 (Bad Debts).

- **Selling & Distribution Expenses** (correct: Row 69 (Bad Debts), type: prompt)
  - 5. The routing regex pattern in Python:

- **Selling & Distribution Expenses** (correct: Row 69 (Bad Debts), type: prompt)
  - This pattern would match "Selling & Distribution Expenses" case-insensitively and route it to Row 69.

- **Administrative & General Expenses** (correct: Row 69 (Bad Debts), type: prompt)
  - 2. I picked Row 71 (Others) because "Administrative & General Expenses" did not explicitly match any specific row keywords or rules, and the CA Expert Rules explicitly state that "General expenses" → Row 71 (Others).

- **Administrative & General Expenses** (correct: Row 69 (Bad Debts), type: prompt)
  - 4. Add a rule: "Administrative & General Expenses → Row 69 (Bad Debts)".

- **Administrative & General Expenses** (correct: Row 69 (Bad Debts), type: prompt)
  - 5. Routing regex pattern:

- **Rates & Taxes** (correct: Row 70 (Advertisements and Sales Promotions), type: prompt)
  - 4. Add a rule: "'Rates & Taxes' → Row 70 (Advertisements and Sales Promotions)" to explicitly override the default keyword match.

- **Rates & Taxes** (correct: Row 70 (Advertisements and Sales Promotions), type: prompt)
  - 5. Routing regex pattern:

- **Rates & Taxes** (correct: Row 70 (Advertisements and Sales Promotions), type: prompt)
  - This pattern would ensure "Rates & Taxes" is routed to Row 70, overriding the default match to Row 68.

- **Bad debts written off** (correct: Row 70 (Advertisements and Sales Promotions), type: prompt)
  - 4. Add a rule: "Bad debts written off → Row 70 (Advertisements and Sales Promotions)" to explicitly override the keyword match for "Bad Debts."

- **Bad debts written off** (correct: Row 70 (Advertisements and Sales Promotions), type: prompt)
  - 5. Routing regex pattern:

- **Bad debts written off** (correct: Row 70 (Advertisements and Sales Promotions), type: prompt)
  - r"Bad debts written off" → Row 70

- **Auditor's Remuneration - Statutory Audit** (correct: Row 70 (Advertisements and Sales Promotions), type: prompt)
  - 2. **Incorrect pick reason:** The item text ("Auditor's Remuneration") explicitly matches the keyword "Audit" in Row 73 ("Audit Fees & Directors Remuneration"), which overrides the section hint ("Other Expenses"). The CA Expert Rules also mandate "Audit Fees" → Row 73.

- **Auditor's Remuneration - Statutory Audit** (correct: Row 70 (Advertisements and Sales Promotions), type: prompt)
  - - *Add an exception rule:* `"Auditor's Remuneration - Statutory Audit" → Row 70 (Advertisements and Sales Promotions)` to override the default "Audit Fees" routing.

- **Auditor's Remuneration - Statutory Audit** (correct: Row 70 (Advertisements and Sales Promotions), type: prompt)
  - 5. **Python regex pattern:**

- **Auditor's Remuneration - Tax Audit** (correct: Row 70 (Advertisements and Sales Promotions), type: prompt)
  - 2. I picked Row 73 because the item text "Auditor's Remuneration - Tax Audit" contains "Audit," which directly matches the CA Expert Rule: "Audit Fees -> Row 73 (Audit Fees & Directors Remuneration)."

- **Auditor's Remuneration - Tax Audit** (correct: Row 70 (Advertisements and Sales Promotions), type: prompt)
  - 4. Add a rule: "Auditor's Remuneration - Tax Audit -> Row 70 (Advertisements and Sales Promotions)."

- **Auditor's Remuneration - Tax Audit** (correct: Row 70 (Advertisements and Sales Promotions), type: prompt)
  - 5. Routing regex pattern:

- **Auditor's Remuneration - Tax Audit** (correct: Row 70 (Advertisements and Sales Promotions), type: prompt)
  - This pattern would explicitly route "Auditor's Remuneration - Tax Audit" to Row 70.

- **Advances Written off** (correct: Row 70 (Advertisements and Sales Promotions), type: prompt)
  - 4. Add a rule: "Advances Written off → Row 70 (Advertisements and Sales Promotions)" to explicitly clarify the routing for this specific item.

- **Advances Written off** (correct: Row 70 (Advertisements and Sales Promotions), type: prompt)
  - 5. Routing regex pattern:

- **Advances Written off** (correct: Row 70 (Advertisements and Sales Promotions), type: prompt)
  - This pattern would match "Advances Written off" case-insensitively and route it to Row 70.

- **Selling & Distribution Expenses** (correct: Row 72 (Repairs & Maintenance), type: prompt)
  - 4. **Add an expert rule**: `"Selling & Distribution Expenses" → Row 72 (Repairs & Maintenance)`

- **Selling & Distribution Expenses** (correct: Row 72 (Repairs & Maintenance), type: prompt)
  - **Add an example**: `"Distribution Expenses" → Row 72 (Repairs & Maintenance)`

- **Selling & Distribution Expenses** (correct: Row 72 (Repairs & Maintenance), type: prompt)
  - 5. **Python regex pattern**:

- **Advances Written off** (correct: Row 74 (Row 74), type: routing)
  - **"Add Row 74 | II_E3b | Advances Written off"** to the POSSIBLE CMA ROWS list.

- **Advances Written off** (correct: Row 74 (Row 74), type: routing)
  - 5. **Routing regex pattern (Python):**

- **Interest of Income Tax** (correct: Row 82 (Row 82), type: routing)
  - 4. Add Row 82 (Row 82) to the POSSIBLE CMA ROWS list with a rule: "Interest of Income Tax → Row 82 (Row 82)".

- **Interest of Income Tax** (correct: Row 82 (Row 82), type: routing)
  - 5. Routing regex pattern: `r"(?i)interest\s+of\s+income\s+tax"`

- **Bill Discounting Charges** (correct: Row 83 (Interest on Fixed Loans / Term loans), type: prompt)
  - 2. Picked Row 133 due to "Bill Discounting" matching CA rule ("Bills discounted" → Row 133), misinterpreting "charges" as balance inclusion. Ignored that "Finance Costs" suggests interest.

- **Bill Discounting Charges** (correct: Row 83 (Interest on Fixed Loans / Term loans), type: prompt)
  - 4. Add a rule: `"Bill Discounting Charges" → Row 83 (Interest on Fixed Loans / Term loans)`

- **Bill Discounting Charges** (correct: Row 83 (Interest on Fixed Loans / Term loans), type: prompt)
  - 5. Regex pattern:

- **Bill Discounting Charges** (correct: Row 83 (Interest on Fixed Loans / Term loans), type: prompt)
  - r"(Bill Discounting Charges|Interest on .*bills? discounted)" → Row 83

- **Interest on CC A/c** (correct: Row 83 (Interest on Fixed Loans / Term loans), type: prompt)
  - 4. **Exact change:** Add a rule:

- **Interest on CC A/c** (correct: Row 83 (Interest on Fixed Loans / Term loans), type: prompt)
  - `"Interest on CC A/c" → Row 83 (Interest on Fixed Loans / Term loans)`

- **Interest on CC A/c** (correct: Row 83 (Interest on Fixed Loans / Term loans), type: prompt)
  - 5. **Regex pattern:**

- **Bank Charges** (correct: Row 84 (Interest on Working capital loans), type: routing)
  - 4. Add Row 84 (Interest on Working capital loans) to the POSSIBLE CMA ROWS list.

- **Bank Charges** (correct: Row 84 (Interest on Working capital loans), type: routing)
  - 5. Routing regex pattern:

- **Bank Charges** (correct: Row 84 (Interest on Working capital loans), type: routing)
  - This pattern would match "Bank Charges" and route it to the correct section.

- **Forex Rate Fluctuation Loss** (correct: Row 90 (Sundry Balances Written off), type: routing)
  - 4. "Add Row 90 (Sundry Balances Written off) to the POSSIBLE CMA ROWS list."

- **Forex Rate Fluctuation Loss** (correct: Row 90 (Sundry Balances Written off), type: routing)
  - 5. Regex pattern: `r"(?i)(forex.*loss|fluctuation.*loss)"`

- **Deferred Tax** (correct: Row 100 (Deferred Tax Liability), type: prompt)
  - - *"Deferred tax" → Row 100 (Deferred Tax Liability)* (CA EXPERT RULES).

- **Deferred Tax** (correct: Row 100 (Deferred Tax Liability), type: prompt)
  - - The examples reinforce this (e.g., *"Deferred tax" -> Row 100*).

- **Deferred Tax** (correct: Row 100 (Deferred Tax Liability), type: prompt)
  - 5. **Regex pattern** (`Python`):

- **Surplus at the beginning of the year** (correct: Row 105 (Row 105), type: routing)
  - 4. **"Add Row 105 (Row 105) to the POSSIBLE CMA ROWS list"** OR

- **Surplus at the beginning of the year** (correct: Row 105 (Row 105), type: routing)
  - **"Add a rule: 'Surplus at the beginning of the year → Row 105 (Row 105)'"**.

- **Surplus at the beginning of the year** (correct: Row 105 (Row 105), type: routing)
  - 5. **Python regex pattern:**

- **Other Bank Balances (Cr.)** (correct: Row 130 (Row 130), type: routing)
  - 4. **Exact change**: *"Add Row 130 | III_L10j | Other Bank Liabilities to POSSIBLE CMA ROWS list"*

- **Other Bank Balances (Cr.)** (correct: Row 130 (Row 130), type: routing)
  - 5. **Routing regex pattern**:

- **Other Bank Balances (Cr.)** (correct: Row 130 (Row 130), type: routing)
  - **Actionable fix**: Explicitly add Row 130 for bank-related liabilities or clarify in rules: *"Bank credit balances in liabilities → Row 130 (if present), else Row 250"*.

- **Inland LC Discounting** (correct: Row 131 (From Indian Bank), type: prompt)
  - 4. Add a rule: `"Inland LC Discounting" → Row 131 (From Indian Bank)` or include LC discounting under CA Expert Rules: `"LC Discounting" → Row 131`.

- **Inland LC Discounting** (correct: Row 131 (From Indian Bank), type: prompt)
  - 5. Regex pattern:

- **TATA Capital** (correct: Row 131 (From Indian Bank), type: prompt)
  - 2. I picked Row 131 because "TATA Capital" aligns with "Short-term Borrowings" and matches the pattern of bank-related borrowings (e.g., "Cash Credit from IDBI" → Row 131).

- **TATA Capital** (correct: Row 131 (From Indian Bank), type: prompt)
  - 4. Add a rule: "TATA Capital → Row 131 (From Indian Bank)" or add an example: "Short Term Borrowings - TATA Capital" → Row 131 (From Indian Bank).

- **TATA Capital** (correct: Row 131 (From Indian Bank), type: prompt)
  - 5. Routing regex pattern: `r"(TATA Capital|Indian Bank|Cash Credit|Short Term Borrowings)"`

- **Current Maturities of Long-term Debt** (correct: Row 135 (Row 135), type: routing)
  - - *"Add Row 135 | III_CL6 | Current maturities of long-term debt"* to the POSSIBLE CMA ROWS list.

- **Current Maturities of Long-term Debt** (correct: Row 135 (Row 135), type: routing)
  - - *"Add a rule: 'Current Maturities of Long-term Debt' → Row 135 (Current maturities of long-term debt)'"*.

- **Current Maturities of Long-term Debt** (correct: Row 135 (Row 135), type: routing)
  - 5. **Python regex pattern**:

- **Current Maturities of Long-term Debt** (correct: Row 135 (Row 135), type: routing)
  - **Key Fix**: The options lacked a specific row for debt reclassification. Adding Row 135 or a regex to catch "current

- **Current Maturities of Long-term Debt** (correct: Row 135 (Row 135), type: routing)
  - 4. "Add Row 135 (Row 135) to the POSSIBLE CMA ROWS list."

- **Current Maturities of Long-term Debt** (correct: Row 135 (Row 135), type: routing)
  - 5. Routing regex pattern:

- **Current Maturities of Long-term Debt** (correct: Row 135 (Row 135), type: routing)
  - This change ensures the item is correctly classified by adding the missing row and using a regex pattern to match relevant keywords.

- **Unsecured Loans from Directors** (correct: Row 151 (Row 151), type: routing)
  - - *"Add Row 151 | III_L8d | Directors' Loans (Quasi Equity)" to the POSSIBLE CMA ROWS list"*

- **Unsecured Loans from Directors** (correct: Row 151 (Row 151), type: routing)
  - - *"Add a rule: 'Loans from Directors → Row 151 (Quasi Equity)'"*

- **Unsecured Loans from Directors** (correct: Row 151 (Row 151), type: routing)
  - 5. **Routing regex pattern**:

- **Unsecured Loans (additional)** (correct: Row 152 (As Quasi Equity), type: prompt)
  - 2. I picked Row 137 because the item was under "Long-term Borrowings," which aligns with "Balance Repayable after one year." I overlooked the example "Unsecured loan → Row 152 (As Quasi Equity)" and did not prioritize it over the section context.

- **Unsecured Loans (additional)** (correct: Row 152 (As Quasi Equity), type: prompt)
  - 4. Add an explicit rule: "Unsecured Loans → Row 152 (As Quasi Equity)." This would override the section context and ensure correct classification.

- **Unsecured Loans (additional)** (correct: Row 152 (As Quasi Equity), type: prompt)
  - 5. Routing regex pattern:

- **Unsecured Loans (additional)** (correct: Row 152 (As Quasi Equity), type: prompt)
  - This pattern would match "Unsecured Loans" and route it to Row 152 (As Quasi Equity).

- **Gross Block (Tangible)** (correct: Row 161 (Row 161), type: routing)
  - - *"Add Row 161 | III_A | Gross Block (Tangible) to the POSSIBLE CMA ROWS list."*

- **Gross Block (Tangible)** (correct: Row 161 (Row 161), type: routing)
  - 5. **Routing regex pattern** (Python):

- **Gross Block (Tangible)** (correct: Row 161 (Row 161), type: routing)
  - **Key Fix**: Ensure Row 161 is explicitly listed as an option, or clarify if "Gross Block (Tangible)" should default to Row 162 (existing logic). The regex ensures "Tangible" is recognized as part of gross block terms.

- **Intangible Assets (Net Block)** (correct: Row 171 (Deferred Tax Asset), type: prompt)
  - 4. **Minimum change**: Add a rule:

- **Intangible Assets (Net Block)** (correct: Row 171 (Deferred Tax Asset), type: prompt)
  - - `"Intangible Assets (Net Block)" → Row 171 (Deferred Tax Asset)`

- **Intangible Assets (Net Block)** (correct: Row 171 (Deferred Tax Asset), type: prompt)
  - 5. **Routing regex**:

- **Raw Materials** (correct: Row 193 (Imported), type: prompt)
  - - "Raw Materials" defaulted to Indigenous (Row 42) per CA rules ("Purchases" → Row 42).

- **Raw Materials** (correct: Row 193 (Imported), type: prompt)
  - - Add a rule: `"Raw Materials (Inventories section)" → Check Rows 193/194 (Imported/Indigenous) first`.

- **Raw Materials** (correct: Row 193 (Imported), type: prompt)
  - 5. **Regex pattern**:

- **Raw Materials** (correct: Row 193 (Imported), type: prompt)
  - r"(?i)(raw materials).*inventories.*imported" → Row 193

- **Raw Materials** (correct: Row 193 (Imported), type: prompt)
  - (Or use section-aware logic: If "Inventories" → Rows 193-194; else → Rows 41-42.)

- **Scraps** (correct: Row 197 (Imported), type: prompt)
  - - Add a rule: `"Scraps" (Inventories) → Row 197 (Imported)`

- **Scraps** (correct: Row 197 (Imported), type: prompt)
  - - Or add an example: `"Scrap materials" → Row 197 (Imported)`

- **Scraps** (correct: Row 197 (Imported), type: prompt)
  - 5. **Regex pattern**:

- **GST Input Recoverable** (correct: Row 218 (Row 218), type: routing)
  - - "Add Row 218 (Row 218) to the POSSIBLE CMA ROWS list."

- **GST Input Recoverable** (correct: Row 218 (Row 218), type: routing)
  - - "Add a rule: 'GST Input Recoverable' → Row 218 (Row 218)."

- **GST Input Recoverable** (correct: Row 218 (Row 218), type: routing)
  - - "Add an example: 'GST Input Recoverable' → Row 218 (Row 218)."

- **GST Input Recoverable** (correct: Row 218 (Row 218), type: routing)
  - 5. **If you had to write ONE routing regex pattern that would correctly route this item, what would it be?**

- **Exceeding 6 months** (correct: Row 231 (Row 231), type: routing)
  - *"Add Row 231 (Row 231) to the POSSIBLE CMA ROWS list as:

- **Exceeding 6 months** (correct: Row 231 (Row 231), type: routing)
  - 5. **Regex pattern for routing**:

- **Exceeding 6 months** (correct: Row 231 (Row 231), type: routing)
  - **Why**: Row 231 was the correct answer *but missing from the options*. The regex captures keyword variations (e.g., ">6 months") to route to Row 231.

- **Capital Advances** (correct: Row 235 (Dues from directors / partners / promoters), type: prompt)
  - 4. Add a rule: "'Capital Advances' → Row 235 (Dues from directors / partners / promoters)."

- **Capital Advances** (correct: Row 235 (Dues from directors / partners / promoters), type: prompt)
  - 5. Routing regex pattern: `r"(?i)(capital\s*advances|loan\/advance\s*to\s*directors)"`

- **Capital Advances** (correct: Row 235 (Dues from directors / partners / promoters), type: prompt)
  - 4. Add a rule: `"Capital Advances" → Row 235 (Dues from directors / partners / promoters) if context implies internal stakeholders`.

- **Capital Advances** (correct: Row 235 (Dues from directors / partners / promoters), type: prompt)
  - 5. Regex: `r"(?i)(capital\s*advances.*(director|partner|promoter))"`

- **Capital Advances** (correct: Row 235 (Dues from directors / partners / promoters), type: prompt)
  - **Actionable fix:** Explicitly tie "Capital Advances" to Row 235 via rule or example, as the term alone is ambiguous. The regex ensures routing only when stakeholder context exists.

- **Long-term Loans and Advances** (correct: Row 236 (Advances to suppliers of capital goods), type: routing)
  - 4. Add Row 236 (Advances to suppliers of capital goods) to the POSSIBLE CMA ROWS list.

- **Long-term Loans and Advances** (correct: Row 236 (Advances to suppliers of capital goods), type: routing)
  - 5. Routing regex pattern:

- **Other Non-Current Assets** (correct: Row 236 (Advances to suppliers of capital goods), type: prompt)
  - 4. Add a rule: "Other Non-Current Assets → Row 236 (Advances to suppliers of capital goods)" or add an example: "Other Non-Current Assets" → Row 236 (Advances to suppliers of capital goods).

- **Other Non-Current Assets** (correct: Row 236 (Advances to suppliers of capital goods), type: prompt)
  - 5. Routing regex pattern: `r"(?i)(other\s*non\s*current\s*assets|advances\s*to\s*suppliers\s*of\s*capital\s*goods)"`

- **Other Non- Current Assets** (correct: Row 237 (Security deposits with government departments), type: routing)
  - - Add a rule: `"Security deposits" → Row 237 (Security deposits with government departments)`

- **Other Non- Current Assets** (correct: Row 237 (Security deposits with government departments), type: routing)
  - 5. **Regex pattern** (Python) to route this item correctly:

- **Leave Encashment** (correct: Row 243 (Advance received from customers), type: prompt)
  - 4. **Add a rule:** "Leave Encashment → Row 243 (Advance received from customers)" or **Add an example:** "Leave Encashment" → Row 243 (Advance received from customers).

- **Leave Encashment** (correct: Row 243 (Advance received from customers), type: prompt)
  - 5. **Routing regex pattern:**

- **Leave Encashment** (correct: Row 243 (Advance received from customers), type: prompt)
  - This pattern would explicitly route "Leave Encashment" to Row 243.

- **Short-term Provisions** (correct: Row 248 (Interest Accrued and due), type: prompt)
  - 4. Add a rule: "Short-term Provisions → Row 248 (Interest Accrued and due)" or add an example: "Short-term Provisions" → Row 248 (Interest Accrued and due).

- **Short-term Provisions** (correct: Row 248 (Interest Accrued and due), type: prompt)
  - 5. Routing regex pattern:

- **Short-term Provisions** (correct: Row 248 (Interest Accrued and due), type: prompt)
  - This pattern would match "Short-term Provisions" and route it to Row 248.

- **Carriage Inwards** (correct: Row 47 (Freight and Transportation Charges), type: prompt)
  - 2. I picked Row 41 because the CA Expert Rule explicitly states: "Freight inward / carriage inward" -> Row 41 (Raw Materials Consumed ( Imported)). This rule overrode the general logic that "Carriage Inwards" should align with Freight and Transportation Charges.

- **Carriage Inwards** (correct: Row 47 (Freight and Transportation Charges), type: prompt)
  - 4. **Exact change:** Modify the CA Expert Rule to: "Freight inward / carriage inward" -> Row 47 (Freight and Transportation Charges). This would ensure alignment with the general logic and correct classification.

- **Carriage Inwards** (correct: Row 47 (Freight and Transportation Charges), type: prompt)
  - 5. **Routing regex pattern:**

- **Carriage Inwards** (correct: Row 47 (Freight and Transportation Charges), type: prompt)
  - This pattern would correctly route "Carriage Inwards" to Row 47 (Freight and Transportation Charges).

- **Closing Stock - Work-in-Progress** (correct: Row 54 (Stock in process Closing Balance), type: prompt)
  - 2. I picked Row 200 because the CA Expert Rules explicitly state: "Inventories of work-in-progress" → Row 200 (Stocks-in-process), which seemed to match the item text "Closing Stock - Work-in-Progress."

- **Closing Stock - Work-in-Progress** (correct: Row 54 (Stock in process Closing Balance), type: prompt)
  - 4. Add a rule: "Closing Stock - Work-in-Progress" → Row 54 (Stock in process Closing Balance).

- **Closing Stock - Work-in-Progress** (correct: Row 54 (Stock in process Closing Balance), type: prompt)
  - 5. Routing regex pattern: `r"(?i)closing\s*stock\s*-\s*work\s*-\s*in\s*-\s*progress"`

- **Closing Stock - Finished Goods** (correct: Row 59 (Finished Goods Closing Balance), type: prompt)
  - 4. Add a rule: "'Closing Stock - Finished Goods' → Row 59 (Finished Goods Closing Balance)" to explicitly map the item text to the correct row.

- **Closing Stock - Finished Goods** (correct: Row 59 (Finished Goods Closing Balance), type: prompt)
  - 5. Routing regex pattern:

- **Closing Stock - Finished Goods** (correct: Row 59 (Finished Goods Closing Balance), type: prompt)
  - This pattern would ensure the item is correctly routed to Row 59 based on the exact text match.

- **(d) Contribution to EPF and ESI** (correct: Row 67 (Salary and staff expenses), type: prompt)
  - 4. Add a rule: "Contribution to EPF and ESI → Row 67 (Salary and staff expenses)" or add an example: "Contribution to EPF and ESI" → Row 67 (Salary and staff expenses). This would override the existing bias toward Row 45.

- **(d) Contribution to EPF and ESI** (correct: Row 67 (Salary and staff expenses), type: prompt)
  - 5. Routing regex pattern:

- **(d) Contribution to EPF and ESI** (correct: Row 67 (Salary and staff expenses), type: prompt)
  - This pattern would correctly route items containing "Contribution to EPF and ESI" or "Salary and staff expenses" to Row 67.

- **Carriage Outward** (correct: Row 70 (Advertisements and Sales Promotions), type: prompt)
  - 4. Add an example: "'Carriage Outward' → Row 70 (Advertisements and Sales Promotions)" to the prompt. This would explicitly link the item to the correct row.

- **Carriage Outward** (correct: Row 70 (Advertisements and Sales Promotions), type: prompt)
  - 5. The routing regex pattern in Python would be:

- **Carriage Outward** (correct: Row 70 (Advertisements and Sales Promotions), type: prompt)
  - This pattern would match "Carriage Outward" and similar terms, routing them to Row 70.

- **Brokerage & Commission** (correct: Row 70 (Advertisements and Sales Promotions), type: prompt)
  - 4. Add a rule:

- **Brokerage & Commission** (correct: Row 70 (Advertisements and Sales Promotions), type: prompt)
  - - `"Brokerage & Commission" → Row 70 (Advertisements and Sales Promotions)`

- **Brokerage & Commission** (correct: Row 70 (Advertisements and Sales Promotions), type: prompt)
  - - `"Brokerage & Commission" → Row 70 (Advertisements and Sales Promotions)`

- **Brokerage & Commission** (correct: Row 70 (Advertisements and Sales Promotions), type: prompt)
  - 5. Regex pattern:

- **Interest on Delay in payment of taxes** (correct: Row 83 (Interest on Fixed Loans / Term loans), type: routing)
  - 4. **Exact change:** "Add Row 83 (Interest on Fixed Loans / Term loans) to the POSSIBLE CMA ROWS list."

- **Interest on Delay in payment of taxes** (correct: Row 83 (Interest on Fixed Loans / Term loans), type: routing)
  - 5. **Routing regex pattern:**

- **Interest on Delay in payment of taxes** (correct: Row 83 (Interest on Fixed Loans / Term loans), type: routing)
  - This pattern would match "Interest on Delay in payment of taxes" and route it to Row 83 if available.

- **Liquidty Damages** (correct: Row 83 (Interest on Fixed Loans / Term loans), type: routing)
  - 4. Add Row 83 (Interest on Fixed Loans / Term loans) to the POSSIBLE CMA ROWS list and include a rule: "Liquidty Damages → Row 83 (Interest on Fixed Loans / Term loans)."

- **Liquidty Damages** (correct: Row 83 (Interest on Fixed Loans / Term loans), type: routing)
  - 5. Routing regex pattern:

- **Liquidty Damages** (correct: Row 83 (Interest on Fixed Loans / Term loans), type: routing)
  - This pattern would match "Liquidty Damages" and route it to Row 83.

- **(b) Interest on Bill discounting & charges** (correct: Row 84 (Interest on Working capital loans), type: prompt)
  - 3. Keywords like "Bill discounting" triggered the CA rule: `"Bills discounted / Bills Purchased" -> Row 133`, overriding the correct logic for working capital interest.

- **(b) Interest on Bill discounting & charges** (correct: Row 84 (Interest on Working capital loans), type: prompt)
  - 4. **Exact change**: Add Row 84 to the POSSIBLE CMA ROWS list and add a CA rule:

- **(b) Interest on Bill discounting & charges** (correct: Row 84 (Interest on Working capital loans), type: prompt)
  - `- "Interest on Bill discounting" -> Row 84 (Interest on Working capital loans)`

- **(b) Interest on Bill discounting & charges** (correct: Row 84 (Interest on Working capital loans), type: prompt)
  - 5. **Regex pattern**:

- **(a) Loan/Overdraft Processing Fee** (correct: Row 84 (Interest on Working capital loans), type: prompt)
  - 4. Add a rule: "Loan/Overdraft Processing Fee → Row 84 (Interest on Working capital loans)."

- **(a) Loan/Overdraft Processing Fee** (correct: Row 84 (Interest on Working capital loans), type: prompt)
  - 5. Routing regex pattern: `r"(Loan|Overdraft).*(Processing Fee)"` → Row 84.

- **(a) Loan/Overdraft Processing Fee** (correct: Row 84 (Interest on Working capital loans), type: prompt)
  - This change would explicitly link the item text to the correct row, overriding the default "fee" → "Bank Charges" association.

- **Surplus - Opening balance** (correct: Row 106 (Brought forward from previous year), type: routing)
  - 4. Add Row 106 (Brought forward from previous year) to the POSSIBLE CMA ROWS list.

- **Surplus - Opening balance** (correct: Row 106 (Brought forward from previous year), type: routing)
  - 5. Routing regex pattern:

- **Rent - Factory** (correct: Row 68 (Rent , Rates and Taxes), type: routing)
  - - `"Rent - Factory" → Row 68 (Rent, Rates and Taxes)`

- **Rent - Factory** (correct: Row 68 (Rent , Rates and Taxes), type: routing)
  - - *"Add Row 68 (Rent, Rates and Taxes) to the POSSIBLE CMA ROWS list."*

- **Rent - Factory** (correct: Row 68 (Rent , Rates and Taxes), type: routing)
  - - *"Add a rule: 'Rent - Factory' → Row 68 (Rent, Rates and Taxes)."*

- **Rent - Factory** (correct: Row 68 (Rent , Rates and Taxes), type: routing)
  - 5. **Regex pattern** (Python) to route "Rent" items correctly:

- **(a) Loan/Overdraft Processing Fee** (correct: Row 83 (Interest on Fixed Loans / Term loans), type: prompt)
  - 4. Add a rule: "Loan/Overdraft Processing Fee → Row 83 (Interest on Fixed Loans / Term loans)" or clarify in the CA EXPERT RULES that processing fees related to loans should be classified under interest.

- **(a) Loan/Overdraft Processing Fee** (correct: Row 83 (Interest on Fixed Loans / Term loans), type: prompt)
  - 5. Routing regex pattern:

- **(a) Loan/Overdraft Processing Fee** (correct: Row 83 (Interest on Fixed Loans / Term loans), type: prompt)
  - This pattern would ensure that items containing "Loan" or "Overdraft" combined with "Processing Fee" or "Interest" are routed to Row 83.

- **Security Service Charges** (correct: Row 51 (Security Service Charges), type: routing)
  - - *"Add Row 51 | II_D8 | Security Service Charges to the POSSIBLE CMA ROWS list"*

- **Security Service Charges** (correct: Row 51 (Security Service Charges), type: routing)
  - 5. **Python regex pattern** to route correctly:

- **Security Service Charges** (correct: Row 51 (Security Service Charges), type: routing)
  - - **Add Row 51 explicitly** to avoid "Others" default.

- **Security Service Charges** (correct: Row 51 (Security Service Charges), type: routing)
  - - **Regex** ensures future "Security"-related items route correctly.

- **Security Service Charges** (correct: Row 51 (Security Service Charges), type: routing)
  - **Actionable Summary**: Expand the row list or regex rules to

- **(c) Staff Welfare Expenses** (correct: Row 67 (Salary and staff expenses), type: prompt)
  - 4. Add an example: "Staff welfare expenses" → Row 67 (Salary and staff expenses). This would override the existing pattern of routing "Staff welfare expenses" to Row 45.

- **(c) Staff Welfare Expenses** (correct: Row 67 (Salary and staff expenses), type: prompt)
  - 5. Routing regex pattern:

- **(c) Staff Welfare Expenses** (correct: Row 67 (Salary and staff expenses), type: prompt)
  - This pattern would ensure items containing "staff welfare" or "employee benefit" are routed to Row 67.

- **(3) Deferred tax Liability / (Asset)** (correct: Row 101 (Deferred Tax Asset), type: prompt)
  - 2. I picked Row 159 because the item text included "Deferred tax Liability," which matched the CA EXPERT RULE: "Deferred tax liability" -> Row 159. I overlooked the "/ (Asset)" part, which should have triggered Row 101.

- **(3) Deferred tax Liability / (Asset)** (correct: Row 101 (Deferred Tax Asset), type: prompt)
  - 4. Add a rule: "Deferred tax Liability / (Asset)" -> Row 101 (Deferred Tax Asset).

- **(3) Deferred tax Liability / (Asset)** (correct: Row 101 (Deferred Tax Asset), type: prompt)
  - 5. Routing regex pattern:

- **(3) Deferred tax Liability / (Asset)** (correct: Row 101 (Deferred Tax Asset), type: prompt)
  - This pattern ensures items with "/ (Asset)" are routed to Row 101.

- **Loan from Banks - current maturities** (correct: Row 136 (Term Loan Repayable in next one year), type: routing)
  - 4. Add Row 136 (Term Loan Repayable in next one year) to the POSSIBLE CMA ROWS list.

- **Loan from Banks - current maturities** (correct: Row 136 (Term Loan Repayable in next one year), type: routing)
  - 5. Routing regex pattern: `r"(current maturities|loan from banks|term loan repayable)"`

- **Vehicle HP Loans - current maturities** (correct: Row 140 (Repayable in next one year), type: routing)
  - 4. Add Row 140 (Repayable in next one year) to the POSSIBLE CMA ROWS list.

- **Vehicle HP Loans - current maturities** (correct: Row 140 (Repayable in next one year), type: routing)
  - 5. Routing regex pattern:

- **Vehicle HP Loans - current maturities** (correct: Row 140 (Repayable in next one year), type: routing)
  - This pattern would correctly route items with these keywords to the appropriate section for short-term liabilities or repayments.

- **Vehicle HP Loans - non-current** (correct: Row 141 (Balance Repayable after one year), type: prompt)
  - - *"Add a rule: 'Vehicle HP Loans - non-current' → Row 141 (Balance Repayable after one year)"*

- **Vehicle HP Loans - non-current** (correct: Row 141 (Balance Repayable after one year), type: prompt)
  - - OR clarify in the prompt: "Non-current loans under 'Long-term Borrowings' → Row 141."

- **Vehicle HP Loans - non-current** (correct: Row 141 (Balance Repayable after one year), type: prompt)
  - 5. **Regex pattern** (Python) to route correctly:

- **Vehicle HP Loans - current maturities** (correct: Row 140 (Repayable in next one year), type: routing)
  - 4. **Add Row 140 (Repayable in next one year) to the POSSIBLE CMA ROWS list.** This would allow the item to be correctly classified based on its context as a short-term liability.

- **Vehicle HP Loans - current maturities** (correct: Row 140 (Repayable in next one year), type: routing)
  - 5. Routing regex pattern:

- **Vehicle HP Loans - current maturities** (correct: Row 140 (Repayable in next one year), type: routing)
  - This pattern would match the item's keywords and route it to the correct section.

- **Provision for employee benefits (Gratuity)** (correct: Row 153 (As Long Term Debt), type: prompt)
  - 4. Add a rule: "Provision for employee benefits (Gratuity) → Row 153 (As Long Term Debt)" or add an example: "Provision for employee benefits (Gratuity)" → Row 153 (As Long Term Debt).

- **Provision for employee benefits (Gratuity)** (correct: Row 153 (As Long Term Debt), type: prompt)
  - 5. Routing regex pattern:

- **Provision for employee benefits (Gratuity)** (correct: Row 153 (As Long Term Debt), type: prompt)
  - This pattern would explicitly route the item to Row 153.

- **(b) Outstanding expenses - (i) Salary and wages Pa** (correct: Row 249 (Creditors for Expenses), type: prompt)
  - 4. Add a rule: "Outstanding expenses → Row 249 (Creditors for Expenses)."

- **(b) Outstanding expenses - (i) Salary and wages Pa** (correct: Row 249 (Creditors for Expenses), type: prompt)
  - 5. Routing regex pattern:

- **(b) Outstanding expenses - (i) Salary and wages Pa** (correct: Row 249 (Creditors for Expenses), type: prompt)
  - This pattern would ensure items with "Outstanding expenses" or "Salary and wages Payable" are routed to Row 249.

- **Changes in work-in-progress and stock-in-trade** (correct: Row 42 (Raw Materials Consumed ( Indigenous)), type: prompt)
  - 2. Picked Row 200 because "work-in-progress" explicitly matched "Stocks-in-process" (Row 200) per **CA Expert Rules**, and the example "Work-in-progress → Row 200" reinforced this. Missed that "Raw Materials Consumed" could apply to changes in stock-in-trade (purchases/consumption).

- **Changes in work-in-progress and stock-in-trade** (correct: Row 42 (Raw Materials Consumed ( Indigenous)), type: prompt)
  - 4. **Add a rule**: *"Changes in stock-in-trade → Row 42 (Raw Materials Consumed)"* or **add an example**: *"Changes in work-in-progress and stock-in-trade → Row 42"*.

- **Changes in work-in-progress and stock-in-trade** (correct: Row 42 (Raw Materials Consumed ( Indigenous)), type: prompt)
  - 5. **Regex pattern**:

- **Purchase at Stock in Trade** (correct: Row 42 (Raw Materials Consumed ( Indigenous)), type: prompt)
  - 4. **Exact Change**: Add a rule:

- **Purchase at Stock in Trade** (correct: Row 42 (Raw Materials Consumed ( Indigenous)), type: prompt)
  - *`"Purchase at Stock in Trade" → Row 42 (Raw Materials Consumed ( Indigenous))`*

- **Purchase at Stock in Trade** (correct: Row 42 (Raw Materials Consumed ( Indigenous)), type: prompt)
  - Add an example: *`"Stock in Trade purchases" → Row 42`*.

- **Purchase at Stock in Trade** (correct: Row 42 (Raw Materials Consumed ( Indigenous)), type: prompt)
  - 5. **Regex Pattern** (Python):

- **Labour charges Paid** (correct: Row 45 (Wages), type: routing)
  - 4. **"Add Row 45 (Wages) to the POSSIBLE CMA ROWS list"** (required for correct routing).

- **Labour charges Paid** (correct: Row 45 (Wages), type: routing)
  - **"Add a rule: 'Labour charges → Row 45 (Wages)'"**.

- **Labour charges Paid** (correct: Row 45 (Wages), type: routing)
  - 5. Regex pattern for routing:

- **Labour charges Paid** (correct: Row 45 (Wages), type: routing)
  - **Key Fix:** Add Row 45 or clarify

- **Staff Welfare Expenses** (correct: Row 45 (Wages), type: prompt)
  - 4. **Add an example:** "'Staff welfare expenses' → Row 45 (Wages)" to clarify the routing.

- **Staff Welfare Expenses** (correct: Row 45 (Wages), type: prompt)
  - 5. **Routing regex pattern:**

- **Staff Welfare Expenses** (correct: Row 45 (Wages), type: prompt)
  - This pattern would correctly route items containing keywords like "wages," "salary," or "staff welfare" to Row 45 (Wages).

- **Gratuity to Employees** (correct: Row 45 (Wages), type: prompt)
  - `- "Gratuity to Employees" -> Row 45 (Wages)`

- **Gratuity to Employees** (correct: Row 45 (Wages), type: prompt)
  - 5. **Regex pattern for routing:**

- **Material Handling Charges** (correct: Row 46 (Processing / Job Work Charges), type: routing)
  - 3. **Keywords triggering Row 46**: "Material Handling" aligns with processing/job work (e.g., loading/unloading raw materials). Rule missing: *"Material Handling → Row 46 (Processing / Job Work Charges)"*.

- **Material Handling Charges** (correct: Row 46 (Processing / Job Work Charges), type: routing)
  - - Add rule: `"Material Handling Charges" → Row 46 (Processing / Job Work Charges)`.

- **Material Handling Charges** (correct: Row 46 (Processing / Job Work Charges), type: routing)
  - - Or add Row 46 to the POSSIBLE CMA ROWS list.

- **Material Handling Charges** (correct: Row 46 (Processing / Job Work Charges), type: routing)
  - 5. **Regex pattern**:

- **Material Handling Charges (estimated)** (correct: Row 46 (Processing / Job Work Charges), type: routing)
  - 4. **Add Row 46 (Processing / Job Work Charges) to the POSSIBLE CMA ROWS list.**

- **Material Handling Charges (estimated)** (correct: Row 46 (Processing / Job Work Charges), type: routing)
  - 5. Routing regex pattern:

- **Material Handling Charges (estimated)** (correct: Row 46 (Processing / Job Work Charges), type: routing)
  - This pattern would match "Material Handling" and route it to Row 46 if available.

- **Transportation charges** (correct: Row 47 (Freight and Transportation Charges), type: routing)
  - 4. **Exact change:** "Add Row 47 (Freight and Transportation Charges) to the POSSIBLE CMA ROWS list."

- **Transportation charges** (correct: Row 47 (Freight and Transportation Charges), type: routing)
  - 5. **Routing regex pattern:**

- **Transportation charges** (correct: Row 47 (Freight and Transportation Charges), type: routing)
  - This pattern would match keywords related to transportation and route the item to Row 47.

- **Transportation Charges (estimated)** (correct: Row 47 (Freight and Transportation Charges), type: routing)
  - - *"Add Row 47 (Freight and Transportation Charges) to the POSSIBLE CMA ROWS list."*

- **Transportation Charges (estimated)** (correct: Row 47 (Freight and Transportation Charges), type: routing)
  - 5. **Regex pattern** (Python) to auto-route similar items:

- **Transportation Charges (estimated)** (correct: Row 47 (Freight and Transportation Charges), type: routing)
  - **Key Fix**: The root issue was the absence of Row 47 in the options. With it added, the classifier would route "Transportation Charges" correctly. The regex above would generalize for future cases.

- **Work in Progress** (correct: Row 54 (Stock in process Closing Balance), type: routing)
  - 4. Add Row 54 (Stock in process Closing Balance) to the POSSIBLE CMA ROWS list.

- **Work in Progress** (correct: Row 54 (Stock in process Closing Balance), type: routing)
  - 5. Routing regex pattern:

- **Work in Progress** (correct: Row 54 (Stock in process Closing Balance), type: routing)
  - This pattern would correctly route "Work in Progress" to Row 54 if it were an option.

- **Finished Goods** (correct: Row 59 (Finished Goods Closing Balance), type: routing)
  - 4. Add Row 59 (Finished Goods Closing Balance) to the POSSIBLE CMA ROWS list.

- **Finished Goods** (correct: Row 59 (Finished Goods Closing Balance), type: routing)
  - 5. Routing regex pattern:

- **Finished Goods** (correct: Row 59 (Finished Goods Closing Balance), type: routing)
  - This pattern would match "Finished Goods Closing Balance" or "Finished Goods Opening Balance" and route it correctly.

- **Salary, Wages and Bonus** (correct: Row 67 (Salary and staff expenses), type: prompt)
  - 2. Your CA expert rules and examples overwhelmingly associate "Salary, Wages and Bonus" with **Row 45 (Wages)**, despite **Row 67** being a better semantic match. The expert rules explicitly state *"Wages & Salary → Row 45"*, and multiple examples (e.g., *"Salary, Wages and Bonus" → Row 45"*) reinforced this misleading pattern. **Row 67 was ignored due to conflicting rules/examples.**

- **Salary, Wages and Bonus** (correct: Row 67 (Salary and staff expenses), type: prompt)
  - 4. **Add/prioritize a rule**: *"Staff-related expenses (salary, bonuses, gratuity) → Row 67 (Salary and staff expenses)"*

- **Salary, Wages and Bonus** (correct: Row 67 (Salary and staff expenses), type: prompt)
  - **AND** **Revise examples**: Remove contradictory examples like *"Salary, Wages and Bonus" → Row 45"*.

- **Salary, Wages and Bonus** (correct: Row 67 (Salary and staff expenses), type: prompt)
  - 5. **Regex pattern** (Python):

- **Contribution to Provident Fund and ESI** (correct: Row 67 (Salary and staff expenses), type: prompt)
  - 2. I picked Row 45 because the CA EXPERT RULES and EXAMPLES FROM OTHER COMPANIES explicitly linked "Provident Fund" and "ESI" to Row 45 (Wages). For example, "Provident Fund - factory workers" -> Row 45 (Wages) and "ESI Fund" -> Row 45 (Wages). These rules and examples overrode the broader context of "Employee Benefits Expenses."

- **Contribution to Provident Fund and ESI** (correct: Row 67 (Salary and staff expenses), type: prompt)
  - 4. Add a rule: "Contribution to Provident Fund and ESI (non-factory) → Row 67 (Salary and staff expenses)" or modify the existing rule: "Provident Fund - factory workers" -> Row 45 (Wages), "Provident Fund - non-factory workers" -> Row 67 (Salary and staff expenses).

- **Contribution to Provident Fund and ESI** (correct: Row 67 (Salary and staff expenses), type: prompt)
  - 5. Routing regex pattern:

- **Licence And Subscription** (correct: Row 68 (Rent , Rates and Taxes), type: prompt)
  - - **Add a rule**: `"Licence Fees" → Row 68 (Rent, Rates and Taxes)` (assuming licence fees are treated as a tax-like statutory payment).

- **Licence And Subscription** (correct: Row 68 (Rent , Rates and Taxes), type: prompt)
  - 5. **Routing regex pattern**:

- **Miscellenious Expenses** (correct: Row 71 (Others), type: prompt)
  - 4. Add a rule: "Miscellenious Expenses → Row 71 (Others)" to explicitly route such items to the "Others" row.

- **Miscellenious Expenses** (correct: Row 71 (Others), type: prompt)
  - 5. Routing regex pattern:

- **Miscellenious Expenses** (correct: Row 71 (Others), type: prompt)
  - This pattern would match variations of "Miscellaneous Expenses" and route them to Row 71 (Others).

- **Miscellaneous Expenses** (correct: Row 71 (Others), type: prompt)
  - 4. Add a rule: "Miscellaneous Expenses → Row 71 (Others)" to explicitly prioritize Row 71 over Row 75 for such cases.

- **Miscellaneous Expenses** (correct: Row 71 (Others), type: prompt)
  - 5. Routing regex pattern:

- **Miscellaneous Expenses** (correct: Row 71 (Others), type: prompt)
  - This pattern would directly route "Miscellaneous Expenses" to Row 71 (Others).

- **Surplus in profit and loss account: Balance at beg** (correct: Row 106 (Brought forward from previous year), type: routing)
  - 4. **Exact change:** Add Row 106 (Brought forward from previous year) to the POSSIBLE CMA ROWS list.

- **Surplus in profit and loss account: Balance at beg** (correct: Row 106 (Brought forward from previous year), type: routing)
  - - **OR** add a rule: *"Balance at beginning" or "Brought forward" → Row 106*.

- **Surplus in profit and loss account: Balance at beg** (correct: Row 106 (Brought forward from previous year), type: routing)
  - - **OR** add an example: *"Surplus in profit and loss account: Balance at beginning" → Row 106*.

- **Surplus in profit and loss account: Balance at beg** (correct: Row 106 (Brought forward from previous year), type: routing)
  - 5. **Regex pattern:**

- **Surplus in P&L: Balance at beginning** (correct: Row 106 (Brought forward from previous year), type: routing)
  - 4. Add Row 106 (Brought forward from previous year) to the POSSIBLE CMA ROWS list.

- **Surplus in P&L: Balance at beginning** (correct: Row 106 (Brought forward from previous year), type: routing)
  - 5. Routing regex pattern:

- **Issue of Bonus Share (P&L surplus capitalised)** (correct: Row 108 (Other Appropriation of profit), type: routing)
  - 4. **Exact change:** *"Add Row 108 (Other Appropriation of profit) to the POSSIBLE CMA ROWS list"* + *"Add a rule: 'Bonus shares from P&L surplus → Row 108 (Other Appropriation of profit)'"*.

- **Issue of Bonus Share (P&L surplus capitalised)** (correct: Row 108 (Other Appropriation of profit), type: routing)
  - 5. **Routing regex pattern (Python):**

- **Other Long Term Liability** (correct: Row 153 (As Long Term Debt), type: prompt)
  - 3. Keywords like "Long Term Liability" **should** have triggered Row 153 per the **CA EXPERT RULES** (e.g., "Special Capital Incentive (refundable)" → Row 153).

- **Other Long Term Liability** (correct: Row 153 (As Long Term Debt), type: prompt)
  - Add a rule: `"Other Long Term Liability" → Row 153 (As Long Term Debt)`.

- **Other Long Term Liability** (correct: Row 153 (As Long Term Debt), type: prompt)
  - *Alternatively*, add an example: `"Other Long Term Liability" → Row 153 (As Long Term Debt)` to the EXAMPLES section.

- **Other Long Term Liability** (correct: Row 153 (As Long Term Debt), type: prompt)
  - 5. **Python regex pattern**:

- **Raw materials + Packing + Consumables** (correct: Row 194 (Indigenous), type: prompt)
  - 2. I picked Row 42 because the item text "Raw materials + Packing + Consumables" matched the CA Expert Rule: "Purchases of raw materials" -> Row 42 (Raw Materials Consumed ( Indigenous)).

- **Raw materials + Packing + Consumables** (correct: Row 194 (Indigenous), type: prompt)
  - 4. Add a rule: "Raw materials + Packing + Consumables" -> Row 194 (Indigenous).

- **Raw materials + Packing + Consumables** (correct: Row 194 (Indigenous), type: prompt)
  - 5. Routing regex pattern:

- **Raw materials + Packing + Consumables** (correct: Row 194 (Indigenous), type: prompt)
  - This pattern would explicitly route the item to Row 194 based on the exact text match.

- **Other Liabilities (Directors + Related + Others)** (correct: Row 249 (Creditors for Expenses), type: prompt)
  - 3. **Missing trigger keywords**: The text should have included "expenses" (e.g., "Creditors for Expenses") to clearly route to Row 249 per the CA EXPERT RULES ("Creditors for expenses -> Row 249").

- **Other Liabilities (Directors + Related + Others)** (correct: Row 249 (Creditors for Expenses), type: prompt)
  - - Add a rule: `"Directors + Related liabilities" → Row 249 (Creditors for Expenses)"`

- **Other Liabilities (Directors + Related + Others)** (correct: Row 249 (Creditors for Expenses), type: prompt)
  - - OR add an example: `"Other Liabilities (Directors)" → Row 249 (Creditors for Expenses)"`.

- **Other Liabilities (Directors + Related + Others)** (correct: Row 249 (Creditors for Expenses), type: prompt)
  - 5. **Routing regex pattern**:

- **Display amount/Discount** (correct: Row 42 (Raw Materials Consumed ( Indigenous)), type: routing)
  - - `"Discount" → Row 42 (Raw Materials Consumed)`

- **Display amount/Discount** (correct: Row 42 (Raw Materials Consumed ( Indigenous)), type: routing)
  - - *"Add Row 42 (Raw Materials Consumed (Indigenous)) to the POSSIBLE CMA ROWS list"*

- **Display amount/Discount** (correct: Row 42 (Raw Materials Consumed ( Indigenous)), type: routing)
  - - *"Add a rule: 'Display amount/Discount' → Row 42 (Raw Materials Consumed)"*

- **Display amount/Discount** (correct: Row 42 (Raw Materials Consumed ( Indigenous)), type: routing)
  - 5. **Python regex pattern for routing:**

- **Display amount/Discount** (correct: Row 42 (Raw Materials Consumed ( Indigenous)), type: routing)
  - **Reasoning:** The item was miscategorized because Row 42 wasn’t an available option, and no rule linked "Display amount/Discount" to raw materials. Adding the row or a keyword rule would fix this. The regex captures case-insensitive variants of the key terms.

- **Opening Stock of Packing** (correct: Row 44 (Stores and spares consumed ( Indigenous)), type: routing)
  - 5. **Python regex pattern**:

- **Opening Stock of Packing** (correct: Row 44 (Stores and spares consumed ( Indigenous)), type: routing)
  - Matches variations like "Opening Stock of Packing" → Row 44.

- **Packing Expenses** (correct: Row 44 (Stores and spares consumed ( Indigenous)), type: routing)
  - 3. Keywords like **"Packing"** should trigger routing to **stores/spares** (Row 44) per CA expert rules (e.g., "Packing charges" → Row 44).

- **Packing Expenses** (correct: Row 44 (Stores and spares consumed ( Indigenous)), type: routing)
  - - *"Add Row 44 (Stores and spares consumed ( Indigenous)) to the POSSIBLE CMA ROWS list"*

- **Packing Expenses** (correct: Row 44 (Stores and spares consumed ( Indigenous)), type: routing)
  - - *"Add a rule: 'Packing Expenses → Row 44 (Stores and spares consumed ( Indigenous))'"*

- **Packing Expenses** (correct: Row 44 (Stores and spares consumed ( Indigenous)), type: routing)
  - 5. **Regex pattern** (Python):

- **Stock of Packing Materials** (correct: Row 44 (Stores and spares consumed ( Indigenous)), type: routing)
  - 4. Add Row 44 (Stores and spares consumed ( Indigenous)) to the POSSIBLE CMA ROWS list.

- **Stock of Packing Materials** (correct: Row 44 (Stores and spares consumed ( Indigenous)), type: routing)
  - 5. Routing regex pattern:

- **Stock of Packing Materials** (correct: Row 44 (Stores and spares consumed ( Indigenous)), type: routing)
  - This pattern would match keywords like "Stock of Packing Materials" and route it to Row 44.

- **Esi** (correct: Row 45 (Wages), type: routing)
  - 4. Add Row 45 (Wages) to the POSSIBLE CMA ROWS list.

- **Esi** (correct: Row 45 (Wages), type: routing)
  - 5. Routing regex pattern:

- **Esi** (correct: Row 45 (Wages), type: routing)
  - This pattern would match "Esi" and similar keywords, routing them to the Wages section.

- **Staff Welfare** (correct: Row 45 (Wages), type: prompt)
  - 2. **You picked Row 67** because "Staff Welfare" lacks explicit keywords like "salary" or "wages." The prompt lacked a rule/explicit example mapping "Staff Welfare" → Row 45 (Wages), despite CA Expert Rules linking similar terms (e.g., "Provident Fund") to wages.

- **Staff Welfare** (correct: Row 45 (Wages), type: prompt)
  - 4. **Exact change**: Add a rule under **CA EXPERT RULES**:

- **Staff Welfare** (correct: Row 45 (Wages), type: prompt)
  - `"Staff welfare expenses" -> Row 45 (Wages)`

- **Staff Welfare** (correct: Row 45 (Wages), type: prompt)
  - 5. **Python regex pattern**:

- **Staff Mess Expenses** (correct: Row 45 (Wages), type: prompt)
  - 4. Add a CA Expert Rule: "Staff Mess Expenses → Row 45 (Wages)" or add an example: "Staff Mess Expenses → Row 45 (Wages)". This would explicitly link the item to the correct row.

- **Staff Mess Expenses** (correct: Row 45 (Wages), type: prompt)
  - 5. Routing regex pattern:

- **Staff Mess Expenses** (correct: Row 45 (Wages), type: prompt)
  - pattern = re.compile(r"(staff|wages|salary|mess|provident|esi|gratuity|labour|bonus)", re.IGNORECASE)

- **Staff Mess Expenses** (correct: Row 45 (Wages), type: prompt)
  - if pattern.search("Staff Mess Expenses"):

- **Staff Mess Expenses** (correct: Row 45 (Wages), type: prompt)
  - This pattern captures keywords related to staff and wages,

- **Electric Charges** (correct: Row 48 (Power, Coal, Fuel and Water), type: routing)
  - 4. Add Row 48 (Power, Coal, Fuel and Water) to the POSSIBLE CMA ROWS list.

- **Electric Charges** (correct: Row 48 (Power, Coal, Fuel and Water), type: routing)
  - 5. Routing regex pattern:

- **Tds on Rent** (correct: Row 49 (Others), type: routing)
  - 4. Add Row 71 (Others) to the POSSIBLE CMA ROWS list and include an example: "Tds on Rent" → Row 71 (Others).

- **Tds on Rent** (correct: Row 49 (Others), type: routing)
  - 5. Routing regex pattern:

- **Tds on Rent** (correct: Row 49 (Others), type: routing)
  - This pattern would correctly route items containing "Tds" or "Tax Deducted at Source" related to "Rent" or "Payment" to Row 71 (Others).

- **Rent - Parking** (correct: Row 49 (Others), type: routing)
  - 4. **Exact change:** Add an example: `"Rent - Parking" → Row 71 (Others)` to the prompt’s "EXAMPLES FROM OTHER COMPANIES" section.

- **Rent - Parking** (correct: Row 49 (Others), type: routing)
  - 5. **Regex pattern:**

- **Rent - Parking** (correct: Row 49 (Others), type: routing)
  - r"(?i)(rent.*parking|rent(?!.*office))" → Row 71


## Full Model Responses

### 1. `Profit on Sale of Fixed Asset` (BCIPL)
- Correct: Row 22 (Domestic)
- Predicted: Row 31 (Profit on sale of fixed assets / Investments)
- Correct in options: NO
- Routed to: other_income

**V3 Response:** ### PART A — Why it went wrong:  
1. **No**, Row 22 (Domestic) was **NOT** in the POSSIBLE CMA ROWS list.  
2. N/A (Row 22 wasn’t an option).  
3. Keywords like "Domestic Sales" or "Domestic Income" should trigger Row 22, but the item text ("Profit on Sale of Fixed Asset") lacks these.  

### PART B — What would make you get it RIGHT:  
4. **Exact change needed**:  
   - *Add Row 22 (Domestic) to the POSSIBLE CMA ROWS list* **AND**  
   - *Add a rule: "Domestic income → Row 22 (Domestic)"*.  

5. **Python regex pattern** to route to Row 22:  
   ```python  
   r"(domestic\b|local\b|home\b.*sale|revenue.*india)"
   ```  

**Key Fix**: The prompt must explicitly include Row 22 as an option *and* define routing logic for domestic-related income. The current rules prioritize profit-from-sale logic (Row 31) when domestic context is missing.

### 2. `Sale of Duty Credit Scrips` (BCIPL)
- Correct: Row 22 (Domestic)
- Predicted: Row 34 (Others)
- Correct in options: NO
- Routed to: other_income

**V3 Response:** ### PART A — Why it went wrong:  
1. **No** – Row 22 (Domestic) was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 22 unavailable).  
3. Keywords like **"Duty Credit Scrips"** should trigger routing to **Row 22 (Domestic)** (typically tied to export incentives/domestic trade schemes).  

### PART B — What would make you get it RIGHT:  
4. **Exact change**:  
   - *"Add Row 22 | II_B7 | Export Incentives / Duty Credit Scrips" to POSSIBLE CMA ROWS list"*  
   - *"Add rule: 'Sale of Duty Credit Scrips' → Row 22 (Domestic)'"*  

5. **Python regex pattern**:  
   ```python  
   r"(?i)(duty\s*credit\s*scrip|export\s*incentive)"  # Matches "Duty Credit Scrips" case-insensitively  
   ```  

**Reasoning**: The item was forced into "Others" due to missing options. Explicit rules or row additions would fix this.  

---

### 3. `Other Materials Consumed` (BCIPL)
- Correct: Row 41 (Raw Materials Consumed ( Imported))
- Predicted: Row 49 (Others)
- Correct in options: Yes
- Routed to: raw_materials

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 41 (Raw Materials Consumed ( Imported)) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 49 because "Other Materials Consumed" lacked explicit keywords like "Imported" or "Indigenous," making it seem generic.  
3. Keywords like "Materials Consumed" should have triggered consideration of Row 41 or Row 42, as they are specific to raw materials.  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "'Materials Consumed' → Row 41 (Raw Materials Consumed ( Imported)) or Row 42 (Raw Materials Consumed ( Indigenous))".  
5. Routing regex pattern:  
```python  
r"(?i)(materials\s*consumed|raw\s*materials)"  
```  
This pattern would ensure "Materials Consumed" is routed to Row 41 or Row 42, avoiding Row 49.

### 4. `Other Materials Consumed` (BCIPL)
- Correct: Row 43 (Stores and spares consumed ( Imported))
- Predicted: Row 49 (Others)
- Correct in options: Yes
- Routed to: raw_materials

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 43 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 49 because "Other Materials Consumed" lacked explicit keywords like "stores" or "spares," making it ambiguous. The absence of clear indicators led me to default to "Others" as a last resort.  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "'Materials Consumed' → Row 43 (Stores and spares consumed ( Imported))" or add an example: "'Other Materials Consumed' → Row 43 (Stores and spares consumed ( Imported))".  
5. Routing regex pattern: `r"(?i)\b(materials\s*consumed|stores|spares)\b"`.  

This change would explicitly link "Materials Consumed" to Row 43, ensuring correct classification.

### 5. `Employee Benefits Expense` (BCIPL)
- Correct: Row 44 (Stores and spares consumed ( Indigenous))
- Predicted: Row 67 (Salary and staff expenses)
- Correct in options: Yes
- Routed to: employee_cost

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 44 (Stores and spares consumed ( Indigenous)) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 67 because "Employee Benefits Expense" directly aligns with "Salary and staff expenses" (Row 67), which is a more specific match based on the item text and section.  
3. N/A (Row 44 was in the list, but the item text did not contain keywords like "stores" or "spares" to trigger routing to Row 44.)  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Employee Benefits Expense → Row 44 (Stores and spares consumed ( Indigenous))" to explicitly override the default routing to Row 67.  
5. Routing regex pattern:  
```python  
r"Employee Benefits Expense"  
```  
This pattern would directly route the item to Row 44 if explicitly defined in the rules.  

**Summary:** The error occurred because Row 67 was a more specific match for "Employee Benefits Expense." Adding a rule or regex pattern to explicitly route this item to Row 44 would resolve the issue.

### 6. `Manufacturing Expenses` (BCIPL)
- Correct: Row 48 (Power, Coal, Fuel and Water)
- Predicted: Row 64 (Other Manufacturing Exp)
- Correct in options: Yes
- Routed to: manufacturing_expense, admin_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 48 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 64 because "Manufacturing Expenses" is a broad term, and without specific keywords like "power," "coal," or "fuel," I defaulted to "Other Manufacturing Exp" as a last resort.  
3. N/A (Row 48 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Manufacturing Expenses related to power, coal, fuel, or water → Row 48 (Power, Coal, Fuel and Water)."  
5. Routing regex pattern:  
```python  
r"(manufacturing.*(power|coal|fuel|water))"  
```  
This would ensure items with "Manufacturing Expenses" and related keywords are routed to Row 48.

### 7. `Rent` (BCIPL)
- Correct: Row 48 (Power, Coal, Fuel and Water)
- Predicted: Row 68 (Rent , Rates and Taxes)
- Correct in options: NO
- Routed to: admin_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. No, Row 48 was NOT in the POSSIBLE CMA ROWS list.  
2. N/A (Row 48 was not an option).  
3. The keyword "Rent" correctly triggered Row 68 (Rent, Rates and Taxes) based on the rules and examples provided.  

**PART B — What would make you get it RIGHT:**  
4. Add Row 48 (Power, Coal, Fuel and Water) to the POSSIBLE CMA ROWS list.  
5. Regex pattern: `r"(electric|power|coal|fuel|water)"`  

**Reasoning:**  
The correct row (Row 48) was not in the options, so adding it to the list is essential. The regex pattern ensures items related to power, coal, fuel, or water are routed correctly.

### 8. `Finished Goods (Opening)` (BCIPL)
- Correct: Row 57 (Row 57)
- Predicted: Row 201 (Finished Goods)
- Correct in options: NO
- Routed to: inventories, raw_materials

**V3 Response:** ### PART A — Why it went wrong:  
1. **No** – Row 57 was not in the provided POSSIBLE CMA ROWS list.  
2. N/A (Row 57 wasn’t an option).  
3. The keyword **"(Opening)"** should have triggered routing to **Row 58 (Finished Goods Opening Balance)** (since "Opening" is explicitly linked to opening balances in examples like "Work in progress - Opening" → Row 53).  

### PART B — What would make you get it RIGHT:  
4. **"Add an example: 'Finished Goods (Opening)' → Row 58 (Finished Goods Opening Balance)'"**  
   - *Reason*: The current examples exclude "(Opening)" logic for finished goods, though similar patterns exist for other categories (e.g., work-in-progress).  

5. **Regex pattern**:  
   ```python  
   r'(?i)(finished\s*goods).*opening'  # Routes to Row 58 if "Finished Goods" + "Opening" appears  
   ```  

**Key Fix**: The prompt’s examples inconsistently handle "Opening" labels (prioritizing Row 201 over Row 58).

### 9. `Finished Goods (Closing)` (BCIPL)
- Correct: Row 58 (Finished Goods Opening Balance)
- Predicted: Row 201 (Finished Goods)
- Correct in options: Yes
- Routed to: inventories, raw_materials

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 58 (Finished Goods Opening Balance) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 201 because the item text "Finished Goods (Closing)" matched the keyword "Finished Goods" in Row 201, and I overlooked the "(Closing)" suffix, which should have routed it to Row 58 (Finished Goods Opening Balance).  
3. N/A (Row 58 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "'Finished Goods (Closing)' → Row 58 (Finished Goods Opening Balance)".  
5. Routing regex pattern:  
```python  
r"Finished Goods\s*\(Closing\)"  
```  

This change would explicitly map "Finished Goods (Closing)" to Row 58, ensuring correct classification.

### 10. `Directors Remuneration` (BCIPL)
- Correct: Row 66 (Row 66)
- Predicted: Row 73 (Audit Fees & Directors Remuneration)
- Correct in options: NO
- Routed to: employee_cost

**V3 Response:** **PART A — Why it went wrong:**  
1. **Was Row 66 (Row 66) in the POSSIBLE CMA ROWS list?** No.  
2. **If no: what keywords in the item text should have triggered routing to the correct section?** "Directors Remuneration" should have triggered a specific row for directors' payments, but Row 66 was not available.  

**PART B — What would make you get it RIGHT:**  
4. **Write the EXACT minimum change to the prompt that would make you confidently pick Row 66:**  
   - "Add Row 66 (Row 66) to the POSSIBLE CMA ROWS list."  
   - Alternatively, "Add a rule: 'Directors Remuneration → Row 66 (Row 66)'."  

5. **If you had to write ONE routing regex pattern that would correctly route this item, what would it be?**  
   ```python  
   r"(?i)directors\s*remuneration"  
   ```  
   This pattern would match "Directors Remuneration" case-insensitively and route it to Row 66.

### 11. `Selling & Distribution Expenses` (BCIPL)
- Correct: Row 69 (Bad Debts)
- Predicted: Row 71 (Others)
- Correct in options: Yes
- Routed to: selling_expense, admin_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 69 (Bad Debts) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 71 (Others) because "Selling & Distribution Expenses" did not explicitly match any specific row keywords or rules provided in the prompt. There was no direct rule or example linking "Selling & Distribution Expenses" to Row 69 (Bad Debts).  
3. N/A (Row 69 was in the list, but the item text lacked keywords like "bad debts" or "write-offs" to trigger routing to Row 69).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Selling & Distribution Expenses → Row 69 (Bad Debts)" or add an example: "Selling & Distribution Expenses" → Row 69 (Bad Debts).  
5. The routing regex pattern in Python:  
```python  
r"(?i)(selling\s*&\s*distribution\s*expenses)"  
```  
This pattern would match "Selling & Distribution Expenses" case-insensitively and route it to Row 69.

### 12. `Administrative & General Expenses` (BCIPL)
- Correct: Row 69 (Bad Debts)
- Predicted: Row 71 (Others)
- Correct in options: Yes
- Routed to: admin_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 69 (Bad Debts) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 71 (Others) because "Administrative & General Expenses" did not explicitly match any specific row keywords or rules, and the CA Expert Rules explicitly state that "General expenses" → Row 71 (Others).  
3. N/A (Row 69 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Administrative & General Expenses → Row 69 (Bad Debts)".  
5. Routing regex pattern:  
```python  
r"(?i)\b(administrative\s*&\s*general\s*expenses)\b"  
```  

This change would explicitly map "Administrative & General Expenses" to Row 69 (Bad Debts), overriding the default "Others" routing for general expenses.

### 13. `Rates & Taxes` (BCIPL)
- Correct: Row 70 (Advertisements and Sales Promotions)
- Predicted: Row 68 (Rent , Rates and Taxes)
- Correct in options: Yes
- Routed to: admin_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 70 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 68 because "Rates & Taxes" directly matched the keywords in Row 68 (Rent, Rates and Taxes).  
3. N/A (Row 70 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "'Rates & Taxes' → Row 70 (Advertisements and Sales Promotions)" to explicitly override the default keyword match.  
5. Routing regex pattern:  
```python  
r"(?i)(rates\s*&\s*taxes)"  
```  
This pattern would ensure "Rates & Taxes" is routed to Row 70, overriding the default match to Row 68.

### 14. `Bad debts written off` (BCIPL)
- Correct: Row 70 (Advertisements and Sales Promotions)
- Predicted: Row 69 (Bad Debts)
- Correct in options: Yes
- Routed to: admin_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 70 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 69 because "Bad debts written off" directly matched the keyword "Bad Debts" in Row 69, which seemed more specific and relevant.  
3. N/A (Row 70 was in the list.)  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Bad debts written off → Row 70 (Advertisements and Sales Promotions)" to explicitly override the keyword match for "Bad Debts."  
5. Routing regex pattern:  
```python  
r"Bad debts written off" → Row 70  
```  
This would ensure the item is routed correctly despite the keyword overlap.

### 15. `Auditor's Remuneration - Statutory Audit` (BCIPL)
- Correct: Row 70 (Advertisements and Sales Promotions)
- Predicted: Row 73 (Audit Fees & Directors Remuneration)
- Correct in options: Yes
- Routed to: admin_expense

**V3 Response:** ### PART A — Why it went wrong:  
1. **Yes**, Row 70 was in the POSSIBLE CMA ROWS list.  
2. **Incorrect pick reason:** The item text ("Auditor's Remuneration") explicitly matches the keyword "Audit" in Row 73 ("Audit Fees & Directors Remuneration"), which overrides the section hint ("Other Expenses"). The CA Expert Rules also mandate "Audit Fees" → Row 73.  
3. N/A (Row 70 was present).  

### PART B — What would make you get it RIGHT:  
4. **Exact change needed:**  
   - *Add an exception rule:* `"Auditor's Remuneration - Statutory Audit" → Row 70 (Advertisements and Sales Promotions)` to override the default "Audit Fees" routing.  

5. **Python regex pattern:**  
   ```python  
   r'(?i)(advertis|sales|promo|remuneration.*statutory\s*audit)'  
   ```  
   *(Matches "Advertisements/Sales Promotions" OR "Remuneration - Statutory Audit" case-insensitively.)*  

**Key fix

### 16. `Auditor's Remuneration - Tax Audit` (BCIPL)
- Correct: Row 70 (Advertisements and Sales Promotions)
- Predicted: Row 73 (Audit Fees & Directors Remuneration)
- Correct in options: Yes
- Routed to: admin_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 70 (Advertisements and Sales Promotions) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 73 because the item text "Auditor's Remuneration - Tax Audit" contains "Audit," which directly matches the CA Expert Rule: "Audit Fees -> Row 73 (Audit Fees & Directors Remuneration)."  
3. N/A (Row 70 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Auditor's Remuneration - Tax Audit -> Row 70 (Advertisements and Sales Promotions)."  
5. Routing regex pattern:  
```python  
r"(?i)(auditor.*remuneration.*tax.*audit)"  
```  
This pattern would explicitly route "Auditor's Remuneration - Tax Audit" to Row 70.

### 17. `Advances Written off` (BCIPL)
- Correct: Row 70 (Advertisements and Sales Promotions)
- Predicted: Row 69 (Bad Debts)
- Correct in options: Yes
- Routed to: admin_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 70 (Advertisements and Sales Promotions) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 69 (Bad Debts) because "Advances Written off" aligns with the concept of bad debts, which are unrecoverable amounts. I did not consider Row 70 as it seemed unrelated to advertisements or sales promotions.  
3. N/A (Row 70 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Advances Written off → Row 70 (Advertisements and Sales Promotions)" to explicitly clarify the routing for this specific item.  
5. Routing regex pattern:  
```python  
r"(?i)\b(advances\s*written\s*off)\b"  
```  
This pattern would match "Advances Written off" case-insensitively and route it to Row 70.

### 18. `Selling & Distribution Expenses` (BCIPL)
- Correct: Row 72 (Repairs & Maintenance)
- Predicted: Row 71 (Others)
- Correct in options: Yes
- Routed to: selling_expense, admin_expense

**V3 Response:** ### PART A — Why it went wrong:
1. **Yes**, Row 72 (Repairs & Maintenance) was in the POSSIBLE CMA ROWS list.  
2. Picked Row 71 (Others) because "Selling & Distribution Expenses" didn’t explicitly match keywords like "repairs" or "maintenance" to trigger Row 72, and no expert rule directly mapped it. Defaulted to "Others" as a last resort.  
3. Keywords like "Distribution Expenses" could imply logistical/maintenance costs, but the prompt lacked a rule linking such terms to Row 72.

### PART B — What would make you get it RIGHT:
4. **Add an expert rule**: `"Selling & Distribution Expenses" → Row 72 (Repairs & Maintenance)`  
   **OR**  
   **Add an example**: `"Distribution Expenses" → Row 72 (Repairs & Maintenance)`  

5. **Python regex pattern**:  
   ```python
   r"(?i)(distribution.*expenses|repairs|maintenance)"
   ```
   This would route items containing "distribution expenses" (case-insensitive) or repair-related terms to Row 72.  

**Key Fix**:

### 19. `Advances Written off` (BCIPL)
- Correct: Row 74 (Row 74)
- Predicted: Row 69 (Bad Debts)
- Correct in options: NO
- Routed to: admin_expense

**V3 Response:** ### PART A — Why it went wrong:  
1. **Was Row 74 in the POSSIBLE CMA ROWS list?**  
   **No** — Row 74 was not listed as an option.  

2. **Why pick Row 69 (Bad Debts)?**  
   "Advances Written off" implies unrecoverable loans/debts, which aligns closest with **Bad Debts** (Row 69) from the given options.  

3. **Keyword triggering correct section?**  
   The phrase **"Written off"** should ideally route to a dedicated "Advances Written off" row (Row 74), but this row was missing.  

### PART B — What would make you get it RIGHT:  
4. **Exact change needed:**  
   **"Add Row 74 | II_E3b | Advances Written off"** to the POSSIBLE CMA ROWS list.  

5. **Routing regex pattern (Python):**  
   ```python
   r".*\b(advances\s*written\s*off|bad\s*debts)\b.*"  
   ```  
   **Reason:** This catches both explicit "Advances Written off" and synonyms

### 20. `Interest of Income Tax` (BCIPL)
- Correct: Row 82 (Row 82)
- Predicted: Row 99 (Income Tax  provision)
- Correct in options: NO
- Routed to: tax, finance_cost

**V3 Response:** **PART A — Why it went wrong:**  
1. No, Row 82 was NOT in the POSSIBLE CMA ROWS list.  
2. N/A (Row 82 was not an option).  
3. Keywords like "Interest" and "Income Tax" should have triggered routing to a row combining both concepts, but no such row was available.  

**PART B — What would make you get it RIGHT:**  
4. Add Row 82 (Row 82) to the POSSIBLE CMA ROWS list with a rule: "Interest of Income Tax → Row 82 (Row 82)".  
5. Routing regex pattern: `r"(?i)interest\s+of\s+income\s+tax"`  

This ensures the item is correctly classified when Row 82 is available.

### 21. `Bill Discounting Charges` (BCIPL)
- Correct: Row 83 (Interest on Fixed Loans / Term loans)
- Predicted: Row 133 ((o/s bill discounting balance to be included))
- Correct in options: Yes
- Routed to: borrowings_short, finance_cost

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes  
2. Picked Row 133 due to "Bill Discounting" matching CA rule ("Bills discounted" → Row 133), misinterpreting "charges" as balance inclusion. Ignored that "Finance Costs" suggests interest.  
3. N/A  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: `"Bill Discounting Charges" → Row 83 (Interest on Fixed Loans / Term loans)`  
   OR clarify in CA rules: "For *interest* on discounted bills, use Row 83, not Row 133".  

5. Regex pattern:  
   ```python  
   r"(Bill Discounting Charges|Interest on .*bills? discounted)" → Row 83  
   ```  
   (Matches *charges* explicitly as interest, not contingent liability.)  

**Key fix:** Disambiguate "charges" (interest) vs. "balance" (liability) in rules.

### 22. `Interest on CC A/c` (BCIPL)
- Correct: Row 83 (Interest on Fixed Loans / Term loans)
- Predicted: Row None (DOUBT)
- Correct in options: Yes
- Routed to: finance_cost

**V3 Response:** **PART A — Why it went wrong:**  
1. **Yes**, Row 83 was in the POSSIBLE CMA ROWS list.  
2. I picked "Row None" because "CC A/c" (Cash Credit Account) implied a working capital loan, but the **CA Expert Rules** and **examples** prioritize assigning *all* interest terms (even ambiguous ones) to Row 83 unless explicitly labeled "Working Capital". Lacked clarity on this hierarchy.  

**PART B — What would make you get it RIGHT:**  
4. **Exact change:** Add a rule:  
   `"Interest on CC A/c" → Row 83 (Interest on Fixed Loans / Term loans)`  
   OR clarify in rules:  
   *"Default all interest items to Row 83 unless explicitly labeled 'Working Capital'."*  

5. **Regex pattern:**  
   ```python
   r"(?i)(interest\s(on|expense).*(loan|term|a\/c|debenture|partner|unsecured|bank))"
   ```  
   *(Matches "Interest on [anything] A/c" as Row 83, aligning with CA rules.)*  

**Key Fix:** Explicit

### 23. `Bank Charges` (BCIPL)
- Correct: Row 84 (Interest on Working capital loans)
- Predicted: Row 71 (Others)
- Correct in options: NO
- Routed to: admin_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. No, Row 84 was NOT in the POSSIBLE CMA ROWS list.  
2. N/A (Row 84 was not an option).  
3. Keywords like "Bank Charges" should have been routed to a section related to financial expenses or interest, but no such row was available in the options.  

**PART B — What would make you get it RIGHT:**  
4. Add Row 84 (Interest on Working capital loans) to the POSSIBLE CMA ROWS list.  
5. Routing regex pattern:  
   ```python  
   r"(?i)(bank\s*charges|interest\s*on\s*working\s*capital\s*loans)"  
   ```  
This pattern would match "Bank Charges" and route it to the correct section.

### 24. `Forex Rate Fluctuation Loss` (BCIPL)
- Correct: Row 90 (Sundry Balances Written off)
- Predicted: Row 71 (Others)
- Correct in options: NO
- Routed to: admin_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. No, Row 90 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 90 was not an option).  
3. Keywords like "Forex Rate Fluctuation Loss" should have triggered routing to a section handling financial adjustments or write-offs, but no such row was available.  

**PART B — What would make you get it RIGHT:**  
4. "Add Row 90 (Sundry Balances Written off) to the POSSIBLE CMA ROWS list."  
5. Regex pattern: `r"(?i)(forex.*loss|fluctuation.*loss)"`  

This would ensure "Forex Rate Fluctuation Loss" is correctly routed to Row 90 if it were an option.

### 25. `Deferred Tax` (BCIPL)
- Correct: Row 100 (Deferred Tax Liability)
- Predicted: Row 100 (Deferred Tax Liability)
- Correct in options: Yes
- Routed to: tax

**V3 Response:** ### PART A — Why it went wrong:  
1. **Yes**, Row 100 was in the POSSIBLE CMA ROWS list.  
2. The rules explicitly state:  
   - *"Deferred tax" → Row 100 (Deferred Tax Liability)* (CA EXPERT RULES).  
   - The examples reinforce this (e.g., *"Deferred tax" -> Row 100*).  
3. **Keyword trigger**: The text "Deferred Tax" directly matches the rule and examples for Row 100.  

### PART B — What would make you get it RIGHT:  
4. **Exact change needed**:  
   - *None*. The prompt already correctly lists Row 100 and includes rules/examples routing "Deferred Tax" to it. The error was likely a misclassification due to oversight.  

5. **Regex pattern** (`Python`):  
   ```python  
   r'(?i)\bdeferred\s*tax\b(?!\s*asset|\s*\(asset\))'  
   ```  
   - **Explanation**: Matches "Deferred Tax" (case-insensitive) unless followed by "Asset" or "(Asset)".  

**Root

### 26. `Surplus at the beginning of the year` (BCIPL)
- Correct: Row 105 (Row 105)
- Predicted: Row 122 (Balance transferred from profit and loss a/c)
- Correct in options: NO
- Routed to: reserves

**V3 Response:** ### **PART A — Why it went wrong:**  
1. **No** – Row 105 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 105 wasn’t an option, so Row 122 was the closest match for "Surplus" related to P&L).  
3. Keyword **"beginning of the year"** should trigger **Row 106 (Brought forward from previous year)** or **Row 105** if listed (common for surplus carried forward).  

### **PART B — What would make you get it RIGHT:**  
4. **"Add Row 105 (Row 105) to the POSSIBLE CMA ROWS list"** OR  
   **"Add a rule: 'Surplus at the beginning of the year → Row 105 (Row 105)'"**.  

5. **Python regex pattern:**  
   ```python
   r"(?i)(surplus|balance).*(beginning|brought forward|previous year)"
   ```  
   This would route items like "Surplus at the beginning of the year" to **Row 105** or **Row 106**.  

**Key Fix:** Include Row

### 27. `Other Bank Balances (Cr.)` (BCIPL)
- Correct: Row 130 (Row 130)
- Predicted: Row 213 (Bank Balances)
- Correct in options: NO
- Routed to: cash, current_liabilities

**V3 Response:** **PART A — Why it went wrong:**  
1. **No** (Row 130 was not in the POSSIBLE CMA ROWS list).  
2. N/A (Row 130 was not an option).  
3. The item text "Other Bank Balances (Cr.)" with "(Cr.)" (credit balance) and section "Other Current Liabilities" should have triggered routing to a liabilities-specific row like Row 250 (Other current liabilities), but **Row 130 was missing**.  

**PART B — What would make you get it RIGHT:**  
4. **Exact change**: *"Add Row 130 | III_L10j | Other Bank Liabilities to POSSIBLE CMA ROWS list"*  
5. **Routing regex pattern**:  
   ```python  
   r"(?i)(other\s+bank\s+balances\s*\(cr\.\)|bank\s+liabilities)"  
   ```  
   **Actionable fix**: Explicitly add Row 130 for bank-related liabilities or clarify in rules: *"Bank credit balances in liabilities → Row 130 (if present), else Row 250"*.  

(Word count: 128)

### 28. `Inland LC Discounting` (BCIPL)
- Correct: Row 131 (From Indian Bank)
- Predicted: Row 133 ((o/s bill discounting balance to be included))
- Correct in options: Yes
- Routed to: fixed_assets, borrowings_short

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes  
2. "Inland LC Discounting" lacks explicit bank name, and "discounting" loosely matched "o/s bill discounting" (Row 133). No CA rule explicitly routed LC discounting to Row 131.  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: `"Inland LC Discounting" → Row 131 (From Indian Bank)` or include LC discounting under CA Expert Rules: `"LC Discounting" → Row 131`.  

5. Regex pattern:  
```python 
r"(inland\s*lc\s*discounting|lc\s*discounting|factoring|packing\s*credit)" 
```  
This would catch "LC Discounting" variants and route to Row 131 (like other bank-related short-term borrowings).  

---  
**Key Issue:** Ambiguity in "discounting" led to partial match with Row 133. Explicit rules/examples for LC transactions would override this.

### 29. `TATA Capital` (BCIPL)
- Correct: Row 131 (From Indian Bank)
- Predicted: Row 131 (From Indian Bank)
- Correct in options: Yes
- Routed to: borrowings_short

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 131 (From Indian Bank) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 131 because "TATA Capital" aligns with "Short-term Borrowings" and matches the pattern of bank-related borrowings (e.g., "Cash Credit from IDBI" → Row 131).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "TATA Capital → Row 131 (From Indian Bank)" or add an example: "Short Term Borrowings - TATA Capital" → Row 131 (From Indian Bank).  
5. Routing regex pattern: `r"(TATA Capital|Indian Bank|Cash Credit|Short Term Borrowings)"`  

This ensures "TATA Capital" is explicitly linked to Row 131, eliminating ambiguity.

### 30. `Current Maturities of Long-term Debt` (BCIPL)
- Correct: Row 135 (Row 135)
- Predicted: Row 250 (Other current liabilities)
- Correct in options: NO
- Routed to: current_liabilities

**V3 Response:** ### PART A — Why it went wrong:  
1. **No**, Row 135 was **not** in the POSSIBLE CMA ROWS list.  
2. N/A (Row 135 unavailable).  
3. Keywords like **"Current Maturities"** and **"Long-term Debt"** imply debt reclassification, which should ideally map to a dedicated row (e.g., "Current portion of long-term debt").  

### PART B — What would make you get it RIGHT:  
4. **Exact change**:  
   - *"Add Row 135 | III_CL6 | Current maturities of long-term debt"* to the POSSIBLE CMA ROWS list.  
   - *"Add a rule: 'Current Maturities of Long-term Debt' → Row 135 (Current maturities of long-term debt)'"*.  

5. **Python regex pattern**:  
   ```python  
   r"(current\s+maturities|portion\s+of\s+long[\s-]term\s+debt)"  
   ```  

**Key Fix**: The options lacked a specific row for debt reclassification. Adding Row 135 or a regex to catch "current

### 31. `Current Maturities of Long-term Debt` (BCIPL)
- Correct: Row 135 (Row 135)
- Predicted: Row None (DOUBT)
- Correct in options: NO
- Routed to: borrowings_short

**V3 Response:** **PART A — Why it went wrong:**  
1. No, Row 135 was NOT in the POSSIBLE CMA ROWS list.  
2. N/A (Row 135 was not an option).  
3. Keywords like "Current Maturities of Long-term Debt" should have triggered routing to a section for term loans repayable within one year, but Row 135 was not available.  

**PART B — What would make you get it RIGHT:**  
4. "Add Row 135 (Row 135) to the POSSIBLE CMA ROWS list."  
5. Routing regex pattern:  
```python  
r"(current maturities of long-term debt|term loan repayable in next one year)"  
```  

This change ensures the item is correctly classified by adding the missing row and using a regex pattern to match relevant keywords.

### 32. `Unsecured Loans from Directors` (BCIPL)
- Correct: Row 151 (Row 151)
- Predicted: Row 153 (As Long Term Debt)
- Correct in options: NO
- Routed to: borrowings_long

**V3 Response:** ### PART A — Why it went wrong:
1. **No** — Row 151 was NOT in the POSSIBLE CMA ROWS list.  
2. N/A (since Row 151 wasn’t an option).  
3. Keywords like "Loans from Directors" should trigger **Row 151** (typically "Directors' Loans" or "Quasi Equity"), but this row was missing. The closest available option was Row 153 (As Long Term Debt), which is incorrect for loans from directors.  

### PART B — What would make you get it RIGHT:
4. **Exact change needed**:  
   - *"Add Row 151 | III_L8d | Directors' Loans (Quasi Equity)" to the POSSIBLE CMA ROWS list"*  
   - *"Add a rule: 'Loans from Directors → Row 151 (Quasi Equity)'"*  

5. **Routing regex pattern**:  
   ```python
   r"(?i)(directors?[']?\s*(loan|advance))|(unsecured\s*loan\s*from\s*directors?)"
   ```  

**Reasoning**:  
- Row 153

### 33. `Unsecured Loans (additional)` (BCIPL)
- Correct: Row 152 (As Quasi Equity)
- Predicted: Row 137 (Balance Repayable after one year)
- Correct in options: Yes
- Routed to: borrowings_long

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 152 (As Quasi Equity) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 137 because the item was under "Long-term Borrowings," which aligns with "Balance Repayable after one year." I overlooked the example "Unsecured loan → Row 152 (As Quasi Equity)" and did not prioritize it over the section context.  

**PART B — What would make you get it RIGHT:**  
4. Add an explicit rule: "Unsecured Loans → Row 152 (As Quasi Equity)." This would override the section context and ensure correct classification.  
5. Routing regex pattern:  
```python  
r"Unsecured\s*Loans?.*"  
```  
This pattern would match "Unsecured Loans" and route it to Row 152 (As Quasi Equity).

### 34. `Gross Block (Tangible)` (BCIPL)
- Correct: Row 161 (Row 161)
- Predicted: Row None (DOUBT)
- Correct in options: NO
- Routed to: fixed_assets, depreciation

**V3 Response:** **PART A — Why it went wrong:**  
1. **No** – Row 161 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 161 wasn’t an option).  
3. Keywords like "Gross Block (Tangible)" should match "Gross Block" (Row 162), but **Row 161 was missing** entirely.  

**PART B — What would make you get it RIGHT:**  
4. **Exact change needed**:  
   - *"Add Row 161 | III_A | Gross Block (Tangible) to the POSSIBLE CMA ROWS list."*  

5. **Routing regex pattern** (Python):  
   ```python
   r"Gross Block.*(Tangible|Plant|Equipment)|Tangible.*Gross Block"
   ```  

**Key Fix**: Ensure Row 161 is explicitly listed as an option, or clarify if "Gross Block (Tangible)" should default to Row 162 (existing logic). The regex ensures "Tangible" is recognized as part of gross block terms.

### 35. `Intangible Assets (Net Block)` (BCIPL)
- Correct: Row 171 (Deferred Tax Asset)
- Predicted: Row 169 (Patents / goodwill / copyrights etc)
- Correct in options: Yes
- Routed to: fixed_assets, depreciation

**V3 Response:** ### PART A — Why it went wrong:  
1. **Yes**, Row 171 (Deferred Tax Asset) was in the POSSIBLE CMA ROWS list.  
2. **Misclassification**: The item "Intangible Assets (Net Block)" was interpreted as related to patents/goodwill (Row 169) due to the "Intangible" keyword, while the correct classification (Deferred Tax Asset) was overlooked because the prompt lacked a specific rule linking "Net Block" to deferred tax.  

### PART B — What would make you get it RIGHT:  
4. **Minimum change**: Add a rule:  
   - `"Intangible Assets (Net Block)" → Row 171 (Deferred Tax Asset)`  
   *(This explicitly maps the item text to the correct row.)*  

5. **Routing regex**:  
   ```python  
   r"(?i)(net\s*block|deferred\s*tax\s*asset)"  # Matches "Net Block" or "Deferred Tax Asset"  
   ```  

**Key Fix**: Explicitly tie "Net Block" to deferred tax assets in rules/examples, as the term is context-specific in financial reporting.

### 36. `Raw Materials` (BCIPL)
- Correct: Row 193 (Imported)
- Predicted: Row 42 (Raw Materials Consumed ( Indigenous))
- Correct in options: Yes
- Routed to: raw_materials, inventories

**V3 Response:** **PART A — Why it went wrong:**  
1. **Yes** (Row 193 was in the list).  
2. Picked Row 42 because:  
   - "Raw Materials" defaulted to Indigenous (Row 42) per CA rules ("Purchases" → Row 42).  
   - Missed that "Imported" (Row 193) is under **Section: Inventories**, not "Consumed".  

**PART B — What would make you get it RIGHT:**  
4. **Exact change**:  
   - Add a rule: `"Raw Materials (Inventories section)" → Check Rows 193/194 (Imported/Indigenous) first`.  
   - Or clarify section hierarchy: Prioritize *III_A11a/A11b* over *II_C1/C2* for "Inventories" section.  

5. **Regex pattern**:  
   ```python  
   r"(?i)(raw materials).*inventories.*imported" → Row 193  
   ```  
   (Or use section-aware logic: If "Inventories" → Rows 193-194; else → Rows 41-42.)  

**Key Fix**:

### 37. `Scraps` (BCIPL)
- Correct: Row 197 (Imported)
- Predicted: Row None (DOUBT)
- Correct in options: Yes
- Routed to: inventories

**V3 Response:** ### PART A — Why it went wrong:  
1. **Yes** (Row 197 was in the POSSIBLE CMA ROWS list).  
2. **Misclassification**: The classifier picked "None" (DOUBT) due to low confidence from ambiguous item text ("Scraps") and lack of explicit rules/examples for scrap materials in inventories.  
3. **Missing trigger**: Keywords like "scraps" or "waste" should have routed to Row 197 (Imported) if defined as raw material leftovers.  

### PART B — What would make you get it RIGHT:  
4. **Exact change**:  
   - Add a rule: `"Scraps" (Inventories) → Row 197 (Imported)`  
   - Or add an example: `"Scrap materials" → Row 197 (Imported)`  

5. **Regex pattern**:  
   ```python  
   r'(?i)\b(scrap|waste|residual|leftover)\b.*inventor'  
   ```  
   *(Case-insensitive match for scrap-related terms in inventory context.)*  

**Key Fix**: Explicitly map "scraps" to imported

### 38. `GST Input Recoverable` (BCIPL)
- Correct: Row 218 (Row 218)
- Predicted: Row 223 (Other Advances / current asset)
- Correct in options: NO
- Routed to: other_assets

**V3 Response:** **PART A — Why it went wrong:**  
1. **Was Row 218 (Row 218) in the POSSIBLE CMA ROWS list?** No.  
2. **If no: what keywords in the item text should have triggered routing to the correct section?** "GST Input Recoverable" should have triggered a specific row for GST-related recoverables, but Row 218 was not available.  

**PART B — What would make you get it RIGHT:**  
4. **Write the EXACT minimum change to the prompt that would make you confidently pick Row 218.**  
   - "Add Row 218 (Row 218) to the POSSIBLE CMA ROWS list."  
   - "Add a rule: 'GST Input Recoverable' → Row 218 (Row 218)."  
   - "Add an example: 'GST Input Recoverable' → Row 218 (Row 218)."  

5. **If you had to write ONE routing regex pattern that would correctly route this item, what would it be?**  
   ```python  
   r"GST Input Recoverable"  
   ```  

This change ensures the item is correctly routed

### 39. `Exceeding 6 months` (BCIPL)
- Correct: Row 231 (Row 231)
- Predicted: Row 208 (Debtors more than 6 months)
- Correct in options: NO
- Routed to: receivables

**V3 Response:** ### PART A — Why it went wrong:  
1. **No**, Row 231 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 208 was the closest match among available options for "Exceeding 6 months").  
3. Keywords like "Row 231" or "Trade Receivables >6 months" should have triggered routing to Row 231, but it wasn’t an option.  

### PART B — What would make you get it RIGHT:  
4. **Exact change needed**:  
   *"Add Row 231 (Row 231) to the POSSIBLE CMA ROWS list as:  
   Row 231 | III_A15d | Trade Receivables >6 months"*  

5. **Regex pattern for routing**:  
   ```python  
   r"(?i)(exceeding|more|above|>\s?)?\s?6\s?months.*trade\s?receivables"  
   ```  

**Why**: Row 231 was the correct answer *but missing from the options*. The regex captures keyword variations (e.g., ">6 months") to route to Row 231.  

---  
**Word count

### 40. `Capital Advances` (BCIPL)
- Correct: Row 235 (Dues from directors / partners / promoters)
- Predicted: Row 223 (Other Advances / current asset)
- Correct in options: Yes
- Routed to: other_assets

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 235 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 223 because "Capital Advances" lacked explicit keywords like "directors," "partners," or "promoters," which are specific to Row 235.  
3. Keywords like "directors," "partners," or "promoters" should have triggered routing to Row 235.  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "'Capital Advances' → Row 235 (Dues from directors / partners / promoters)."  
5. Routing regex pattern: `r"(?i)(capital\s*advances|loan\/advance\s*to\s*directors)"`  

This change ensures "Capital Advances" is explicitly mapped to Row 235, avoiding ambiguity.

### 41. `Capital Advances` (BCIPL)
- Correct: Row 235 (Dues from directors / partners / promoters)
- Predicted: Row 219 (Advances recoverable in cash or in kind)
- Correct in options: Yes
- Routed to: other_assets

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes  
2. "Capital Advances" lacked clear context (e.g., "to directors"). Row 219 was a broader match for "advances," while Row 235 requires explicit director/partner linkage.  
3. N/A (Row 235 was present)  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: `"Capital Advances" → Row 235 (Dues from directors / partners / promoters) if context implies internal stakeholders`.  
5. Regex: `r"(?i)(capital\s*advances.*(director|partner|promoter))"`  

**Actionable fix:** Explicitly tie "Capital Advances" to Row 235 via rule or example, as the term alone is ambiguous. The regex ensures routing only when stakeholder context exists.  

Word count: 98

### 42. `Long-term Loans and Advances` (BCIPL)
- Correct: Row 236 (Advances to suppliers of capital goods)
- Predicted: Row 153 (As Long Term Debt)
- Correct in options: NO
- Routed to: borrowings_long, fixed_assets

**V3 Response:** **PART A — Why it went wrong:**  
1. No, Row 236 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 236 was not an option).  
3. Keywords like "Advances" and "suppliers of capital goods" should have triggered routing to the correct section, but Row 236 was not available.  

**PART B — What would make you get it RIGHT:**  
4. Add Row 236 (Advances to suppliers of capital goods) to the POSSIBLE CMA ROWS list.  
5. Routing regex pattern:  
```python  
r"(?i)(long-term\s*loans\s*and\s*advances|advances\s*to\s*suppliers\s*of\s*capital\s*goods)"  
```  

This change ensures the correct row is available and identifiable based on the item text.

### 43. `Other Non-Current Assets` (BCIPL)
- Correct: Row 236 (Advances to suppliers of capital goods)
- Predicted: Row 238 (Other non current assets)
- Correct in options: Yes
- Routed to: other_assets, fixed_assets

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 236 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 238 because "Other Non-Current Assets" directly matched its description, and I did not infer that it could relate to "Advances to suppliers of capital goods" without explicit keywords.  
3. N/A (Row 236 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Other Non-Current Assets → Row 236 (Advances to suppliers of capital goods)" or add an example: "Other Non-Current Assets" → Row 236 (Advances to suppliers of capital goods).  
5. Routing regex pattern: `r"(?i)(other\s*non\s*current\s*assets|advances\s*to\s*suppliers\s*of\s*capital\s*goods)"`  

This change would explicitly link "Other Non-Current Assets" to Row 236, ensuring correct classification.

### 44. `Other Non- Current Assets` (BCIPL)
- Correct: Row 237 (Security deposits with government departments)
- Predicted: Row 172 (Other Intangible assets)
- Correct in options: NO
- Routed to: fixed_assets

**V3 Response:** ### PART A — Why it went wrong:  
1. **No**, Row 237 was **not** in the POSSIBLE CMA ROWS list.  
2. N/A (Row 237 was not an option).  
3. The item text ("Other Non-Current Assets") and section ("Non-Current Assets") lacked keywords like "security deposits" or "government" to trigger Row 237.  

### PART B — What would make you get it RIGHT:  
4. **Exact change needed**:  
   - Add `Row 237 | III_A10 | Security deposits with government departments` to the POSSIBLE CMA ROWS list.  
   - Add a rule: `"Security deposits" → Row 237 (Security deposits with government departments)`  

5. **Regex pattern** (Python) to route this item correctly:  
   ```python
   r"(?i)security\s*deposits|government\s*deposits)"
   ```  

**Key Fix**: The correct row **must be in the allowed options**. Your error was unavoidable because Row 237 wasn’t listed. Add it explicitly.  

(Words: 120)

### 45. `Leave Encashment` (BCIPL)
- Correct: Row 243 (Advance received from customers)
- Predicted: Row None (DOUBT)
- Correct in options: Yes
- Routed to: current_liabilities

**V3 Response:** **PART A — Why it went wrong:**  
1. **Yes**, Row 243 (Advance received from customers) was in the POSSIBLE CMA ROWS list.  
2. I picked Row None because "Leave Encashment" did not match any keywords or rules explicitly tied to Row 243 or other specific rows.  
3. N/A (Row 243 was available).  

**PART B — What would make you get it RIGHT:**  
4. **Add a rule:** "Leave Encashment → Row 243 (Advance received from customers)" or **Add an example:** "Leave Encashment" → Row 243 (Advance received from customers).  
5. **Routing regex pattern:**  
```python  
r"(?i)(leave\s*encashment)"  
```  
This pattern would explicitly route "Leave Encashment" to Row 243.

### 46. `Short-term Provisions` (BCIPL)
- Correct: Row 248 (Interest Accrued and due)
- Predicted: Row 250 (Other current liabilities)
- Correct in options: Yes
- Routed to: current_liabilities

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 248 (Interest Accrued and due) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 250 because "Short-term Provisions" did not explicitly match any specific row, and I defaulted to "Other current liabilities" as a last resort.  
3. N/A (Row 248 was available, but the item text lacked keywords like "interest" or "accrued" to trigger routing to Row 248).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Short-term Provisions → Row 248 (Interest Accrued and due)" or add an example: "Short-term Provisions" → Row 248 (Interest Accrued and due).  
5. Routing regex pattern:  
```python  
r"(?i)(short-term\s*provisions|interest\s*accrued\s*and\s*due)"  
```  
This pattern would match "Short-term Provisions" and route it to Row 248.

### 47. `Carriage Inwards` (Dynamic_Air)
- Correct: Row 47 (Freight and Transportation Charges)
- Predicted: Row 41 (Raw Materials Consumed ( Imported))
- Correct in options: Yes
- Routed to: raw_materials

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 47 (Freight and Transportation Charges) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 41 because the CA Expert Rule explicitly states: "Freight inward / carriage inward" -> Row 41 (Raw Materials Consumed ( Imported)). This rule overrode the general logic that "Carriage Inwards" should align with Freight and Transportation Charges.  

**PART B — What would make you get it RIGHT:**  
4. **Exact change:** Modify the CA Expert Rule to: "Freight inward / carriage inward" -> Row 47 (Freight and Transportation Charges). This would ensure alignment with the general logic and correct classification.  
5. **Routing regex pattern:**  
```python  
r"(?i)(carriage\s*inwards|freight\s*inward)"  
```  
This pattern would correctly route "Carriage Inwards" to Row 47 (Freight and Transportation Charges).

### 48. `Closing Stock - Work-in-Progress` (Dynamic_Air)
- Correct: Row 54 (Stock in process Closing Balance)
- Predicted: Row 200 (Stocks-in-process)
- Correct in options: Yes
- Routed to: inventories, raw_materials

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 54 (Stock in process Closing Balance) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 200 because the CA Expert Rules explicitly state: "Inventories of work-in-progress" → Row 200 (Stocks-in-process), which seemed to match the item text "Closing Stock - Work-in-Progress."  
3. N/A (Row 54 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Closing Stock - Work-in-Progress" → Row 54 (Stock in process Closing Balance).  
5. Routing regex pattern: `r"(?i)closing\s*stock\s*-\s*work\s*-\s*in\s*-\s*progress"`  

This change ensures the specific keyword "Closing Stock" is explicitly routed to Row 54, overriding the general CA Expert Rule for "Inventories of work-in-progress."

### 49. `Closing Stock - Finished Goods` (Dynamic_Air)
- Correct: Row 59 (Finished Goods Closing Balance)
- Predicted: Row 201 (Finished Goods)
- Correct in options: Yes
- Routed to: inventories, raw_materials

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 59 (Finished Goods Closing Balance) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 201 because the item text "Closing Stock - Finished Goods" matched the keyword "Finished Goods" in Row 201, and I overlooked the specific "Closing Balance" context that should have routed it to Row 59.  
3. N/A (Row 59 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "'Closing Stock - Finished Goods' → Row 59 (Finished Goods Closing Balance)" to explicitly map the item text to the correct row.  
5. Routing regex pattern:  
```python  
r"Closing\s*Stock\s*-\s*Finished\s*Goods"  
```  
This pattern would ensure the item is correctly routed to Row 59 based on the exact text match.

### 50. `(d) Contribution to EPF and ESI` (Dynamic_Air)
- Correct: Row 67 (Salary and staff expenses)
- Predicted: Row 45 (Wages)
- Correct in options: Yes
- Routed to: employee_cost

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 67 (Salary and staff expenses) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 45 because the CA EXPERT RULES and EXAMPLES FROM OTHER COMPANIES explicitly linked "Contribution to EPF and ESI" and similar items to Row 45 (Wages). This created a strong bias toward Row 45 despite Row 67 being a better fit.  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Contribution to EPF and ESI → Row 67 (Salary and staff expenses)" or add an example: "Contribution to EPF and ESI" → Row 67 (Salary and staff expenses). This would override the existing bias toward Row 45.  
5. Routing regex pattern:  
```python  
r"(?i)(contribution\s*to\s*(epf|esi)|salary\s*and\s*staff\s*expenses)"  
```  
This pattern would correctly route items containing "Contribution to EPF and ESI" or "Salary and staff expenses" to Row 67.

### 51. `Carriage Outward` (Dynamic_Air)
- Correct: Row 70 (Advertisements and Sales Promotions)
- Predicted: Row 71 (Others)
- Correct in options: Yes
- Routed to: selling_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 70 (Advertisements and Sales Promotions) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 71 (Others) because "Carriage Outward" did not explicitly match any keywords or rules in the prompt, and I defaulted to "Others" as a last resort.  
3. N/A (Row 70 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add an example: "'Carriage Outward' → Row 70 (Advertisements and Sales Promotions)" to the prompt. This would explicitly link the item to the correct row.  
5. The routing regex pattern in Python would be:  
```python  
r"(?i)(carriage\s*outward|freight\s*outward|delivery\s*expenses)"  
```  
This pattern would match "Carriage Outward" and similar terms, routing them to Row 70.

### 52. `Brokerage & Commission` (Dynamic_Air)
- Correct: Row 70 (Advertisements and Sales Promotions)
- Predicted: Row 71 (Others)
- Correct in options: Yes
- Routed to: admin_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes  
2. "Brokerage & Commission" lacked explicit keywords matching Row 70, and no CA rule/explicitly linked it to "Advertisements and Sales Promotions." Defaulted to "Others" as a catch-all.  

**PART B — What would make you get it RIGHT:**  
4. Add a rule:  
   - `"Brokerage & Commission" → Row 70 (Advertisements and Sales Promotions)`  
   OR an example:  
   - `"Brokerage & Commission" → Row 70 (Advertisements and Sales Promotions)`  

5. Regex pattern:  
   ```python  
   r"(brokerage|commission|advertising|publicity)"  # Case-insensitive, broad match  
   ```  

**Key Fix:** Explicitly link "Brokerage & Commission" to Row 70 via rule/example. Current ambiguity defaults to "Others."  

(Words: 100)

### 53. `Interest on Delay in payment of taxes` (Dynamic_Air)
- Correct: Row 83 (Interest on Fixed Loans / Term loans)
- Predicted: Row 71 (Others)
- Correct in options: NO
- Routed to: admin_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. No, Row 83 was NOT in the POSSIBLE CMA ROWS list.  
2. N/A (Row 83 was not an option).  
3. Keywords like "Interest" and "taxes" should have triggered routing to an interest-related row, but Row 83 was unavailable.  

**PART B — What would make you get it RIGHT:**  
4. **Exact change:** "Add Row 83 (Interest on Fixed Loans / Term loans) to the POSSIBLE CMA ROWS list."  
5. **Routing regex pattern:**  
```python  
r"(interest|delay\s*payment\s*tax)"  
```  
This pattern would match "Interest on Delay in payment of taxes" and route it to Row 83 if available.

### 54. `Liquidty Damages` (Dynamic_Air)
- Correct: Row 83 (Interest on Fixed Loans / Term loans)
- Predicted: Row 71 (Others)
- Correct in options: NO
- Routed to: admin_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. No, Row 83 was NOT in the POSSIBLE CMA ROWS list.  
2. N/A (Row 83 was not an option).  
3. Keywords like "Liquidty Damages" should have been associated with interest or loan-related expenses, but this connection was not explicitly defined in the rules or examples.  

**PART B — What would make you get it RIGHT:**  
4. Add Row 83 (Interest on Fixed Loans / Term loans) to the POSSIBLE CMA ROWS list and include a rule: "Liquidty Damages → Row 83 (Interest on Fixed Loans / Term loans)."  
5. Routing regex pattern:  
```python  
r"(?i)\b(liquidty\s*damages|interest\s*on\s*loans)\b"  
```  
This pattern would match "Liquidty Damages" and route it to Row 83.

### 55. `(b) Interest on Bill discounting & charges` (Dynamic_Air)
- Correct: Row 84 (Interest on Working capital loans)
- Predicted: Row 133 ((o/s bill discounting balance to be included))
- Correct in options: Yes
- Routed to: borrowings_short, finance_cost

**V3 Response:** ### PART A — Why it went wrong:
1. **No**, Row 84 (Interest on Working capital loans) was not in the POSSIBLE CMA ROWS list provided.  
2. N/A (Row 84 wasn’t an option)  
3. Keywords like "Bill discounting" triggered the CA rule: `"Bills discounted / Bills Purchased" -> Row 133`, overriding the correct logic for working capital interest.  

### PART B — What would make you get it RIGHT:  
4. **Exact change**: Add Row 84 to the POSSIBLE CMA ROWS list and add a CA rule:  
   `- "Interest on Bill discounting" -> Row 84 (Interest on Working capital loans)`  

5. **Regex pattern**:  
   ```python
   r"(?i)(interest\s*on\s*(bill\s*discounting|working\s*capital))"
   ```  

**Why**: Bill discounting is a working capital tool, so its interest belongs to Row 84. The current rules misroute it to Row 133 (bill discounting balance) instead of interest expense.  

*(Words: 98)*

### 56. `(a) Loan/Overdraft Processing Fee` (Dynamic_Air)
- Correct: Row 84 (Interest on Working capital loans)
- Predicted: Row 85 (Bank Charges)
- Correct in options: Yes
- Routed to: borrowings_short, finance_cost

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 84 (Interest on Working capital loans) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 85 (Bank Charges) because the item text "Loan/Overdraft Processing Fee" explicitly mentions a "fee," which aligns with "Bank Charges" rather than "Interest on Working capital loans."  
3. N/A (Row 84 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Loan/Overdraft Processing Fee → Row 84 (Interest on Working capital loans)."  
5. Routing regex pattern: `r"(Loan|Overdraft).*(Processing Fee)"` → Row 84.  

This change would explicitly link the item text to the correct row, overriding the default "fee" → "Bank Charges" association.

### 57. `Surplus - Opening balance` (Dynamic_Air)
- Correct: Row 106 (Brought forward from previous year)
- Predicted: Row 122 (Balance transferred from profit and loss a/c)
- Correct in options: NO
- Routed to: reserves

**V3 Response:** **PART A — Why it went wrong:**  
1. No, Row 106 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 106 was not an option).  
3. Keywords like "Opening balance" or "Brought forward" should have triggered routing to Row 106, but it was not available.  

**PART B — What would make you get it RIGHT:**  
4. Add Row 106 (Brought forward from previous year) to the POSSIBLE CMA ROWS list.  
5. Routing regex pattern:  
```python  
r"(?i)(opening\s*balance|brought\s*forward|surplus\s*at\s*beginning)"  
```  

This change ensures the item is correctly classified based on its keywords.

### 58. `Rent - Factory` (Dynamic_Air)
- Correct: Row 68 (Rent , Rates and Taxes)
- Predicted: Row None (DOUBT)
- Correct in options: NO
- Routed to: manufacturing_expense, raw_materials

**V3 Response:** ### PART A — Why it went wrong:  
1. **No** - Row 68 was **not** in the provided POSSIBLE CMA ROWS list.  
2. N/A (since Row 68 was not an option).  
3. Keywords like "Rent" should trigger a rule like:  
   - `"Rent - Factory" → Row 68 (Rent, Rates and Taxes)`  

### PART B — What would make you get it RIGHT:  
4. **Exact change needed**:  
   - *"Add Row 68 (Rent, Rates and Taxes) to the POSSIBLE CMA ROWS list."*  
   - *"Add a rule: 'Rent - Factory' → Row 68 (Rent, Rates and Taxes)."*  

5. **Regex pattern** (Python) to route "Rent" items correctly:  
   ```python  
   r'(?i)\brent\b.*(factory|plant|manufacturing)'  
   ```  
   *(Matches "Rent" followed by factory/plant context, case-insensitive.)*  

### Key Fix:  
The root issue was **missing Row 68 in the options**.

### 59. `(a) Loan/Overdraft Processing Fee` (Dynamic_Air)
- Correct: Row 83 (Interest on Fixed Loans / Term loans)
- Predicted: Row 85 (Bank Charges)
- Correct in options: Yes
- Routed to: borrowings_short, finance_cost

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 83 (Interest on Fixed Loans / Term loans) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 85 (Bank Charges) because the item text "Loan/Overdraft Processing Fee" contains "Processing Fee," which aligns with bank charges. I did not associate it with interest, as "Processing Fee" is not explicitly linked to interest in the rules or examples.  
3. N/A (Row 83 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Loan/Overdraft Processing Fee → Row 83 (Interest on Fixed Loans / Term loans)" or clarify in the CA EXPERT RULES that processing fees related to loans should be classified under interest.  
5. Routing regex pattern:  
```python  
r"(Loan|Overdraft).*(Processing Fee|Interest)"  
```  
This pattern would ensure that items containing "Loan" or "Overdraft" combined with "Processing Fee" or "Interest" are routed to Row 83.

### 60. `Security Service Charges` (Dynamic_Air)
- Correct: Row 51 (Security Service Charges)
- Predicted: Row 71 (Others)
- Correct in options: NO
- Routed to: admin_expense

**V3 Response:** ### PART A — Why it went wrong:
1. **No**, Row 51 (Security Service Charges) was **not** in the POSSIBLE CMA ROWS list.  
2. N/A (Row 51 wasn’t an option, forcing a fallback to Row 71).  
3. The keywords **"Security Service"** should have triggered a dedicated row, but none existed in the given options.  

### PART B — What would make you get it RIGHT:
4. **Exact change needed**:  
   - *"Add Row 51 | II_D8 | Security Service Charges to the POSSIBLE CMA ROWS list"*  

5. **Python regex pattern** to route correctly:  
   ```python
   r"(?i)security\s*service|guard|patrol"
   ```

### Key Fixes:  
- **Add Row 51 explicitly** to avoid "Others" default.  
- **Regex** ensures future "Security"-related items route correctly.  
- **Confidence**: 1.0 (if Row 51 exists), else 0.2 (forced to "Others").  

**Actionable Summary**: Expand the row list or regex rules to

### 61. `(c) Staff Welfare Expenses` (Dynamic_Air)
- Correct: Row 67 (Salary and staff expenses)
- Predicted: Row 45 (Wages)
- Correct in options: Yes
- Routed to: employee_cost

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 67 (Salary and staff expenses) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 45 because the examples from other companies consistently routed "Staff welfare expenses" to Row 45 (Wages), overriding the specific context of "Employee Benefits Expense" and the existence of Row 67.  
3. N/A (Row 67 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. Add an example: "Staff welfare expenses" → Row 67 (Salary and staff expenses). This would override the existing pattern of routing "Staff welfare expenses" to Row 45.  
5. Routing regex pattern:  
   ```python  
   r"(?i)(staff welfare|employee benefit)"  
   ```  
This pattern would ensure items containing "staff welfare" or "employee benefit" are routed to Row 67.

### 62. `(3) Deferred tax Liability / (Asset)` (Dynamic_Air)
- Correct: Row 101 (Deferred Tax Asset)
- Predicted: Row 159 (Deferred tax liability)
- Correct in options: Yes
- Routed to: tax

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 101 (Deferred Tax Asset) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 159 because the item text included "Deferred tax Liability," which matched the CA EXPERT RULE: "Deferred tax liability" -> Row 159. I overlooked the "/ (Asset)" part, which should have triggered Row 101.  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Deferred tax Liability / (Asset)" -> Row 101 (Deferred Tax Asset).  
5. Routing regex pattern:  
```python  
r"Deferred tax Liability\s*\/\s*\(Asset\)"  
```  
This pattern ensures items with "/ (Asset)" are routed to Row 101.

### 63. `Loan from Banks - current maturities` (Dynamic_Air)
- Correct: Row 136 (Term Loan Repayable in next one year)
- Predicted: Row 131 (From Indian Bank)
- Correct in options: NO
- Routed to: borrowings_short

**V3 Response:** **PART A — Why it went wrong:**  
1. No, Row 136 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 136 was not an option).  
3. Keywords like "current maturities" and "Loan from Banks" should have triggered routing to the correct section (Term Loan Repayable in next one year).  

**PART B — What would make you get it RIGHT:**  
4. Add Row 136 (Term Loan Repayable in next one year) to the POSSIBLE CMA ROWS list.  
5. Routing regex pattern: `r"(current maturities|loan from banks|term loan repayable)"`  

This ensures the item is correctly classified based on its keywords.

### 64. `Vehicle HP Loans - current maturities` (Dynamic_Air)
- Correct: Row 140 (Repayable in next one year)
- Predicted: Row 131 (From Indian Bank)
- Correct in options: NO
- Routed to: admin_expense, borrowings_short

**V3 Response:** **PART A — Why it went wrong:**  
1. No, Row 140 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 140 was not an option).  
3. Keywords like "current maturities" and "Short-term Borrowings" should have triggered routing to a section for short-term liabilities or repayments within one year.  

**PART B — What would make you get it RIGHT:**  
4. Add Row 140 (Repayable in next one year) to the POSSIBLE CMA ROWS list.  
5. Routing regex pattern:  
```python  
r"(current maturities|repayable in next one year|short-term borrowings)"  
```  

This pattern would correctly route items with these keywords to the appropriate section for short-term liabilities or repayments.

### 65. `Vehicle HP Loans - non-current` (Dynamic_Air)
- Correct: Row 141 (Balance Repayable after one year)
- Predicted: Row 149 (Balance Other Debts)
- Correct in options: Yes
- Routed to: admin_expense, borrowings_long

**V3 Response:** ### PART A — Why it went wrong:  
1. **Yes**, Row 141 ("Balance Repayable after one year") was in the POSSIBLE CMA ROWS list.  
2. **Reason for picking Row 149**: The item text "Vehicle HP Loans - non-current" lacks explicit keywords (e.g., "repayable after one year") to trigger Row 141, and "Loans" defaults to "Balance Other Debts" (Row 149) as a catch-all for non-specified debt.  

### PART B — What would make you get it RIGHT:  
4. **Exact change needed**:  
   - *"Add a rule: 'Vehicle HP Loans - non-current' → Row 141 (Balance Repayable after one year)"*  
   - OR clarify in the prompt: "Non-current loans under 'Long-term Borrowings' → Row 141."  

5. **Regex pattern** (Python) to route correctly:  
   ```python  
   r'(?i)(vehicle\s*hp\s*loans.*non[- ]current|long[- ]term\s*borrowings.*repayable\s*after\s*one

### 66. `Vehicle HP Loans - current maturities` (Dynamic_Air)
- Correct: Row 140 (Repayable in next one year)
- Predicted: Row 71 (Others)
- Correct in options: NO
- Routed to: admin_expense, borrowings_short

**V3 Response:** **PART A — Why it went wrong:**  
1. **No**, Row 140 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 140 was not an option).  
3. Keywords like "current maturities" and "Short-term Borrowings" should have triggered routing to a section for repayable liabilities or short-term borrowings, but no such row was available.  

**PART B — What would make you get it RIGHT:**  
4. **Add Row 140 (Repayable in next one year) to the POSSIBLE CMA ROWS list.** This would allow the item to be correctly classified based on its context as a short-term liability.  
5. Routing regex pattern:  
   ```python  
   r"(current maturities|short-term borrowings|repayable in next one year)"  
   ```  
This pattern would match the item's keywords and route it to the correct section.

### 67. `Provision for employee benefits (Gratuity)` (Dynamic_Air)
- Correct: Row 153 (As Long Term Debt)
- Predicted: Row 67 (Salary and staff expenses)
- Correct in options: Yes
- Routed to: employee_cost, borrowings_long

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 153 (As Long Term Debt) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 67 because "Provision for employee benefits (Gratuity)" contains keywords like "employee" and "benefits," which are commonly associated with salary and staff expenses. The examples provided also routed similar items (e.g., "Gratuity to Employees") to Row 45 or Row 67, reinforcing this choice.  
3. N/A (Row 153 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Provision for employee benefits (Gratuity) → Row 153 (As Long Term Debt)" or add an example: "Provision for employee benefits (Gratuity)" → Row 153 (As Long Term Debt).  
5. Routing regex pattern:  
```python  
r"Provision for employee benefits \(Gratuity\)"  
```  
This pattern would explicitly route the item to Row 153.

### 68. `(b) Outstanding expenses - (i) Salary and wages Payable` (Dynamic_Air)
- Correct: Row 249 (Creditors for Expenses)
- Predicted: Row 67 (Salary and staff expenses)
- Correct in options: Yes
- Routed to: employee_cost, current_liabilities

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 249 (Creditors for Expenses) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 67 because the item text contained "Salary and wages," which matched the keyword "Salary" in Row 67 (Salary and staff expenses). I overlooked the broader context of "Outstanding expenses" and "Other Current Liabilities," which should have routed it to Row 249.  
3. N/A (Row 249 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Outstanding expenses → Row 249 (Creditors for Expenses)."  
5. Routing regex pattern:  
   ```python  
   r"(Outstanding expenses|Salary and wages Payable)"  
   ```  
This pattern would ensure items with "Outstanding expenses" or "Salary and wages Payable" are routed to Row 249.

### 69. `Changes in work-in-progress and stock-in-trade` (INPL)
- Correct: Row 42 (Raw Materials Consumed ( Indigenous))
- Predicted: Row 200 (Stocks-in-process)
- Correct in options: Yes
- Routed to: inventories, raw_materials

**V3 Response:** **PART A — Why it went wrong:**  
1. **Yes**, Row 42 was in the list.  
2. Picked Row 200 because "work-in-progress" explicitly matched "Stocks-in-process" (Row 200) per **CA Expert Rules**, and the example "Work-in-progress → Row 200" reinforced this. Missed that "Raw Materials Consumed" could apply to changes in stock-in-trade (purchases/consumption).  

**PART B — What would make you get it RIGHT:**  
4. **Add a rule**: *"Changes in stock-in-trade → Row 42 (Raw Materials Consumed)"* or **add an example**: *"Changes in work-in-progress and stock-in-trade → Row 42"*.  
5. **Regex pattern**:  
   ```python
   r"(?i)(changes\s*in\s*(stock|work)[-\s]*(in|of)[-\s]*(trade|progress))|(raw\s*material\s*consumed)"
   ```  
   Matches both the item text and links it to raw materials context.  

**Key Fix**: Prioritize "stock

### 70. `Purchase at Stock in Trade` (INPL)
- Correct: Row 42 (Raw Materials Consumed ( Indigenous))
- Predicted: Row 49 (Others)
- Correct in options: Yes
- Routed to: raw_materials

**V3 Response:** ### PART A — Why it went wrong:  
1. **Yes** (Row 42 was in the POSSIBLE CMA ROWS list).  
2. **Root Cause**: The classifier misinterpreted "Purchase at Stock in Trade" as a generic expense (Row 49) instead of recognizing it as a raw material purchase (Row 42). The prompt lacked explicit rules/examples linking "Stock in Trade" to raw materials.  

### PART B — What would make you get it RIGHT:  
4. **Exact Change**: Add a rule:  
   *`"Purchase at Stock in Trade" → Row 42 (Raw Materials Consumed ( Indigenous))`*  
   **OR**  
   Add an example: *`"Stock in Trade purchases" → Row 42`*.  

5. **Regex Pattern** (Python):  
   ```python
   r'(purchase.*stock.*trade|raw\s+materials?.*consumed|indigenous\s+materials?)'
   ```  
   **Why**: Matches keywords like "purchase," "stock," "trade," and "indigenous" to route to Row 42.  

---  
**Key Fix**: Explicitly tie "

### 71. `Labour charges Paid` (INPL)
- Correct: Row 45 (Wages)
- Predicted: Row 67 (Salary and staff expenses)
- Correct in options: NO
- Routed to: admin_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. **No** (Row 45 was not in the POSSIBLE CMA ROWS list).  
2. N/A (since Row 45 wasn’t an option).  
3. Keywords like *"Labour"* or *"Paid"* should trigger **Wages** (Row 45) if available. The closest match in the given options was Row 67 (*Salary and staff expenses*), as both relate to employee compensation.  

**PART B — What would make you get it RIGHT:**  
4. **"Add Row 45 (Wages) to the POSSIBLE CMA ROWS list"** (required for correct routing).  
   Alternatively, a rule like:  
   **"Add a rule: 'Labour charges → Row 45 (Wages)'"**.  
5. Regex pattern for routing:  
   ```python  
   r"(labour|wages|staff\scharges|salaries|paid\s(to|for)\sworkers?)"  
   ```  
   This would match terms like *"Labour charges Paid"* to **Wages**.  

**Key Fix:** Add Row 45 or clarify

### 72. `Staff Welfare Expenses` (INPL)
- Correct: Row 45 (Wages)
- Predicted: Row 67 (Salary and staff expenses)
- Correct in options: Yes
- Routed to: employee_cost

**V3 Response:** **PART A — Why it went wrong:**  
1. **Yes**, Row 45 (Wages) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 67 (Salary and staff expenses) because "Staff Welfare Expenses" seemed more aligned with general staff-related costs rather than direct wages.  
3. Keywords like "Welfare" and "Staff" could have been interpreted as broader employee benefits, leading to Row 67.  

**PART B — What would make you get it RIGHT:**  
4. **Add an example:** "'Staff welfare expenses' → Row 45 (Wages)" to clarify the routing.  
5. **Routing regex pattern:**  
```python  
r"(?i)(wages|salary|staff welfare|provident fund|esi|gratuity)"  
```  
This pattern would correctly route items containing keywords like "wages," "salary," or "staff welfare" to Row 45 (Wages).

### 73. `Gratuity to Employees` (INPL)
- Correct: Row 45 (Wages)
- Predicted: Row 67 (Salary and staff expenses)
- Correct in options: Yes
- Routed to: employee_cost

**V3 Response:** **PART A — Why it went wrong:**  
1. **Yes**  
2. Misinterpreted "Gratuity" as a generic staff expense (Row 67) despite CA rules/examples clearly routing gratuity to Row 45 (Wages) alongside PF/ESI. Overlooked precedence of expert rules over text ambiguity.  

**PART B — What would make you get it RIGHT:**  
4. **Exact change:** Add/modify the CA expert rule:  
   `- "Gratuity to Employees" -> Row 45 (Wages)`  
   (Currently, only examples mention gratuity, but explicit rules override example ambiguity.)  

5. **Regex pattern for routing:**  
   ```python  
   r"(?i)(gratuity|salary|wages|pf|esi|labour|provident\sfund|bonus)"  
   ```  
   (Would catch "Gratuity" and align with existing wage-related keywords in rules.)  

**Key fix:** Rules > examples. Ensure gratuity is explicitly tied to Row 45 like PF/ESI. Current examples conflict (one routes to Row 67), causing inconsistency.  

---  
**Word count

### 74. `Material Handling Charges` (INPL)
- Correct: Row 46 (Processing / Job Work Charges)
- Predicted: Row 71 (Others)
- Correct in options: NO
- Routed to: admin_expense

**V3 Response:** ### PART A — Why it went wrong:  
1. **No**, Row 46 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 46 wasn’t an option).  
3. **Keywords triggering Row 46**: "Material Handling" aligns with processing/job work (e.g., loading/unloading raw materials). Rule missing: *"Material Handling → Row 46 (Processing / Job Work Charges)"*.  

### PART B — What would make you get it RIGHT:  
4. **Exact change**:  
   - Add rule: `"Material Handling Charges" → Row 46 (Processing / Job Work Charges)`.  
   - Or add Row 46 to the POSSIBLE CMA ROWS list.  

5. **Regex pattern**:  
   ```python   
   r"(?i)(material\s*handling|loading|unloading|job\s*work)"  
   ```  
   This would route similar terms to Row 46.  

**Key Issue**: Row 46 wasn’t an option, and the default fallback was Row 71 ("Others"). Fix by adding the missing row or rule.  

---  
**Word count**:

### 75. `Material Handling Charges (estimated)` (INPL)
- Correct: Row 46 (Processing / Job Work Charges)
- Predicted: Row 71 (Others)
- Correct in options: NO
- Routed to: admin_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. **No**, Row 46 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 46 was not an option).  
3. Keywords like "Material Handling" or "Charges" should have triggered routing to a manufacturing or processing-related section, but Row 46 was unavailable.  

**PART B — What would make you get it RIGHT:**  
4. **Add Row 46 (Processing / Job Work Charges) to the POSSIBLE CMA ROWS list.**  
5. Routing regex pattern:  
   ```python  
   r"(?i)\b(material\s*handling|processing|job\s*work)\b"  
   ```  
This pattern would match "Material Handling" and route it to Row 46 if available.

### 76. `Transportation charges` (INPL)
- Correct: Row 47 (Freight and Transportation Charges)
- Predicted: Row 71 (Others)
- Correct in options: NO
- Routed to: admin_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. No, Row 47 was **not** in the POSSIBLE CMA ROWS list.  
2. N/A (Row 47 was not an option).  
3. Keywords like "Transportation" or "Freight" should have triggered routing to Row 47, but it wasn’t available.  

**PART B — What would make you get it RIGHT:**  
4. **Exact change:** "Add Row 47 (Freight and Transportation Charges) to the POSSIBLE CMA ROWS list."  
5. **Routing regex pattern:**  
```python  
r"(transportation|freight|cartage|shipping|carriage)"  
```  
This pattern would match keywords related to transportation and route the item to Row 47.

### 77. `Transportation Charges (estimated)` (INPL)
- Correct: Row 47 (Freight and Transportation Charges)
- Predicted: Row 71 (Others)
- Correct in options: NO
- Routed to: admin_expense

**V3 Response:** ### PART A — Why it went wrong:  
1. **No** – Row 47 (Freight and Transportation Charges) was **not** in the POSSIBLE CMA ROWS list.  
2. N/A (Row 47 wasn’t an option).  
3. Keywords like **"Transportation"** or **"Freight"** should trigger routing to a dedicated freight/transport row (Row 47), but this row was missing.  

### PART B — What would make you get it RIGHT:  
4. **Exact change needed**:  
   - *"Add Row 47 (Freight and Transportation Charges) to the POSSIBLE CMA ROWS list."*  

5. **Regex pattern** (Python) to auto-route similar items:  
   ```python  
   r"(transport|freight|cartage|carriage|logistics)\b.*charges"  
   ```  

**Key Fix**: The root issue was the absence of Row 47 in the options. With it added, the classifier would route "Transportation Charges" correctly. The regex above would generalize for future cases.  

---  
**Word count**: 120 | **Specificity**: Actionable (

### 78. `Work in Progress` (INPL)
- Correct: Row 54 (Stock in process Closing Balance)
- Predicted: Row 200 (Stocks-in-process)
- Correct in options: NO
- Routed to: inventories

**V3 Response:** **PART A — Why it went wrong:**  
1. No, Row 54 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 54 was not an option).  
3. Keywords like "Work in Progress" matched Row 200 (Stocks-in-process) based on the CA Expert Rules and examples provided.  

**PART B — What would make you get it RIGHT:**  
4. Add Row 54 (Stock in process Closing Balance) to the POSSIBLE CMA ROWS list.  
5. Routing regex pattern:  
```python  
r"(?i)(work\s*in\s*progress|stock\s*in\s*process\s*closing\s*balance)"  
```  
This pattern would correctly route "Work in Progress" to Row 54 if it were an option.

### 79. `Finished Goods` (INPL)
- Correct: Row 59 (Finished Goods Closing Balance)
- Predicted: Row 201 (Finished Goods)
- Correct in options: NO
- Routed to: inventories

**V3 Response:** **PART A — Why it went wrong:**  
1. No, Row 59 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 59 was not in the list).  
3. Keywords like "Closing Balance" or "Opening Balance" should have triggered routing to the correct section, but they were absent in the item text.  

**PART B — What would make you get it RIGHT:**  
4. Add Row 59 (Finished Goods Closing Balance) to the POSSIBLE CMA ROWS list.  
5. Routing regex pattern:  
   ```python  
   r"(?i)(finished\s*goods.*(closing|opening)\s*balance)"  
   ```  
This pattern would match "Finished Goods Closing Balance" or "Finished Goods Opening Balance" and route it correctly.

### 80. `Salary, Wages and Bonus` (INPL)
- Correct: Row 67 (Salary and staff expenses)
- Predicted: Row 45 (Wages)
- Correct in options: Yes
- Routed to: employee_cost

**V3 Response:** **PART A — Why it went wrong:**  
1. **Yes**  
2. Your CA expert rules and examples overwhelmingly associate "Salary, Wages and Bonus" with **Row 45 (Wages)**, despite **Row 67** being a better semantic match. The expert rules explicitly state *"Wages & Salary → Row 45"*, and multiple examples (e.g., *"Salary, Wages and Bonus" → Row 45"*) reinforced this misleading pattern. **Row 67 was ignored due to conflicting rules/examples.**  

**PART B — What would make you get it RIGHT:**  
4. **Add/prioritize a rule**: *"Staff-related expenses (salary, bonuses, gratuity) → Row 67 (Salary and staff expenses)"*  
   **AND** **Revise examples**: Remove contradictory examples like *"Salary, Wages and Bonus" → Row 45"*.  

5. **Regex pattern** (Python):  
   ```python
   r"(?i)(salary|staff|bonus|gratuity)(?!.*(factory|plant|wages))"
   ```  
   *(Matches salary-related terms ONLY if not factory/plant

### 81. `Contribution to Provident Fund and ESI` (INPL)
- Correct: Row 67 (Salary and staff expenses)
- Predicted: Row 45 (Wages)
- Correct in options: Yes
- Routed to: employee_cost

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 67 (Salary and staff expenses) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 45 because the CA EXPERT RULES and EXAMPLES FROM OTHER COMPANIES explicitly linked "Provident Fund" and "ESI" to Row 45 (Wages). For example, "Provident Fund - factory workers" -> Row 45 (Wages) and "ESI Fund" -> Row 45 (Wages). These rules and examples overrode the broader context of "Employee Benefits Expenses."  
3. N/A (Row 67 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Contribution to Provident Fund and ESI (non-factory) → Row 67 (Salary and staff expenses)" or modify the existing rule: "Provident Fund - factory workers" -> Row 45 (Wages), "Provident Fund - non-factory workers" -> Row 67 (Salary and staff expenses).  
5. Routing regex pattern:  
```python  
r"(?i)(contribution.*(provident|esi).*(

### 82. `Licence And Subscription` (INPL)
- Correct: Row 68 (Rent , Rates and Taxes)
- Predicted: Row 71 (Others)
- Correct in options: Yes
- Routed to: admin_expense

**V3 Response:** ### PART A — Why it went wrong:  

1. **Yes**, Row 68 (Rent, Rates and Taxes) was in the POSSIBLE CMA ROWS list.  
2. **Reason for picking Row 71 (Others) instead**:  
   - The item text **"Licence And Subscription"** did not explicitly match any keyword rules for Row 68 (e.g., "Rent", "Taxes").  
   - No explicit rule linked "Licence" or "Subscription" to Row 68.  

3. **Keywords that should have triggered Row 68 routing**:  
   - If the item text included "Taxes" or "Rent" (e.g., "Licence Tax"), it would trigger Row 68.  

### PART B — What would make you get it RIGHT:  

4. **Minimum change to prompt**:  
   - **Add a rule**: `"Licence Fees" → Row 68 (Rent, Rates and Taxes)` (assuming licence fees are treated as a tax-like statutory payment).  

5. **Routing regex pattern**:  
   ```python  
   r"\b(licen[cs]e|subscription|tax|rates?)\

### 83. `Miscellenious Expenses` (INPL)
- Correct: Row 71 (Others)
- Predicted: Row 75 (Miscellaneous Expenses written off)
- Correct in options: Yes
- Routed to: admin_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 71 (Others) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 75 because "Miscellenious Expenses" partially matched "Miscellaneous Expenses written off" (Row 75), and I overlooked the rule that "Others" rows should be used as a last resort when no specific row matches.  
3. N/A (Row 71 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Miscellenious Expenses → Row 71 (Others)" to explicitly route such items to the "Others" row.  
5. Routing regex pattern:  
```python  
r"(?i)miscell(aneous|enious)\s+expenses"  
```  
This pattern would match variations of "Miscellaneous Expenses" and route them to Row 71 (Others).

### 84. `Miscellaneous Expenses` (INPL)
- Correct: Row 71 (Others)
- Predicted: Row 75 (Miscellaneous Expenses written off)
- Correct in options: Yes
- Routed to: admin_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 71 (Others) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 75 because "Miscellaneous Expenses" matched the keyword "Miscellaneous" in Row 75 (Miscellaneous Expenses written off), even though Row 71 (Others) was a better fit.  
3. N/A (Row 71 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Miscellaneous Expenses → Row 71 (Others)" to explicitly prioritize Row 71 over Row 75 for such cases.  
5. Routing regex pattern:  
```python  
r"Miscellaneous\sExpenses"  
```  
This pattern would directly route "Miscellaneous Expenses" to Row 71 (Others).

### 85. `Surplus in profit and loss account: Balance at beginning` (INPL)
- Correct: Row 106 (Brought forward from previous year)
- Predicted: Row 122 (Balance transferred from profit and loss a/c)
- Correct in options: NO
- Routed to: reserves

**V3 Response:** **PART A — Why it went wrong:**  
1. **No** (Row 106 was not in the POSSIBLE CMA ROWS list).  
2. N/A (not applicable, since Row 106 wasn’t an option).  
3. Keywords like *"Balance at beginning"* or *"Brought forward"* should trigger routing to Row 106 (Brought forward from previous year), but this row wasn’t available.  

**PART B — What would make you get it RIGHT:**  
4. **Exact change:** Add Row 106 (Brought forward from previous year) to the POSSIBLE CMA ROWS list.  
   - **OR** add a rule: *"Balance at beginning" or "Brought forward" → Row 106*.  
   - **OR** add an example: *"Surplus in profit and loss account: Balance at beginning" → Row 106*.  

5. **Regex pattern:**  
   ```python
   r"(?i)(balance\s*at\s*beginning|brought\s*forward)"
   ```  

**Actionable fix:** The error occurred because Row 106 was missing. Either include Row

### 86. `Surplus in P&L: Balance at beginning` (INPL)
- Correct: Row 106 (Brought forward from previous year)
- Predicted: Row 122 (Balance transferred from profit and loss a/c)
- Correct in options: NO
- Routed to: reserves

**V3 Response:** **PART A — Why it went wrong:**  
1. No, Row 106 was NOT in the POSSIBLE CMA ROWS list.  
2. N/A (Row 106 was not an option).  
3. Keywords like "Balance at beginning" or "Brought forward" should have triggered routing to Row 106.  

**PART B — What would make you get it RIGHT:**  
4. Add Row 106 (Brought forward from previous year) to the POSSIBLE CMA ROWS list.  
5. Routing regex pattern:  
   ```python  
   r"(?i)(balance\s*at\s*beginning|brought\s*forward)"  
   ```  

This change ensures the correct row is available and identifiable based on the item's keywords.

### 87. `Issue of Bonus Share (P&L surplus capitalised)` (INPL)
- Correct: Row 108 (Other Appropriation of profit)
- Predicted: Row 122 (Balance transferred from profit and loss a/c)
- Correct in options: NO
- Routed to: employee_cost, reserves

**V3 Response:** **PART A — Why it went wrong:**  
1. **No** (Row 108 was not in the POSSIBLE CMA ROWS list).  
2. N/A (Row 108 was not an option).  
3. Keywords like **"Bonus Share"** and **"P&L surplus capitalised"** imply profit appropriation, but the available rows lacked this category (e.g., "Other Appropriation of profit").  

**PART B — What would make you get it RIGHT:**  
4. **Exact change:** *"Add Row 108 (Other Appropriation of profit) to the POSSIBLE CMA ROWS list"* + *"Add a rule: 'Bonus shares from P&L surplus → Row 108 (Other Appropriation of profit)'"*.  

5. **Routing regex pattern (Python):**  
   ```python
   r"(issue of bonus shares|p&l surplus capitalised|appropriation of profit)"
   ```  

**Root cause:** Missing row and rules for profit appropriation items. Fix by adding the row and explicit keyword mapping. (Words: 120)

### 88. `Other Long Term Liability` (INPL)
- Correct: Row 153 (As Long Term Debt)
- Predicted: Row None (DOUBT)
- Correct in options: Yes
- Routed to: borrowings_long

**V3 Response:** ### PART A — Why it went wrong:
1. **Yes**, Row 153 (As Long Term Debt) was in the POSSIBLE CMA ROWS list.
2. You picked "Row None (DOUBT)" because the item text "Other Long Term Liability" lacked specific keywords triggering the CA EXPERT RULES (e.g., "Refundable", "Term Loan", "Debentures"). The generic "Other" label defaults to "DOUBT" unless explicitly mapped.
3. Keywords like "Long Term Liability" **should** have triggered Row 153 per the **CA EXPERT RULES** (e.g., "Special Capital Incentive (refundable)" → Row 153).

### PART B — What would make you get it RIGHT:
4. **Exact change needed**:  
   Add a rule: `"Other Long Term Liability" → Row 153 (As Long Term Debt)`.  
   *Alternatively*, add an example: `"Other Long Term Liability" → Row 153 (As Long Term Debt)` to the EXAMPLES section.
   
5. **Python regex pattern**:  
   ```python
   r"(?i)\b(other\s*long\s*

### 89. `Raw materials + Packing + Consumables` (INPL)
- Correct: Row 194 (Indigenous)
- Predicted: Row 42 (Raw Materials Consumed ( Indigenous))
- Correct in options: Yes
- Routed to: raw_materials, inventories

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 194 (Indigenous) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 42 because the item text "Raw materials + Packing + Consumables" matched the CA Expert Rule: "Purchases of raw materials" -> Row 42 (Raw Materials Consumed ( Indigenous)).  
3. N/A (Row 194 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Raw materials + Packing + Consumables" -> Row 194 (Indigenous).  
5. Routing regex pattern:  
```python  
r"(?i)(raw\s*materials\s*\+\s*packing\s*\+\s*consumables)"  
```  

This pattern would explicitly route the item to Row 194 based on the exact text match.

### 90. `Other Liabilities (Directors + Related + Others)` (INPL)
- Correct: Row 249 (Creditors for Expenses)
- Predicted: Row 250 (Other current liabilities)
- Correct in options: Yes
- Routed to: current_liabilities

**V3 Response:** ### PART A — Why it went wrong:
1. **Yes**, Row 249 (Creditors for Expenses) was in the POSSIBLE CMA ROWS list.  
2. **Reason for picking Row 250 instead**: The item text "Other Liabilities (Directors + Related + Others)" lacked explicit keywords like "expenses" or direct matches to rules for Row 249. The "Others" label defaulted to Row 250 (Other current liabilities) as a last resort.  

3. **Missing trigger keywords**: The text should have included "expenses" (e.g., "Creditors for Expenses") to clearly route to Row 249 per the CA EXPERT RULES ("Creditors for expenses -> Row 249").  

### PART B — What would make you get it RIGHT:
4. **Exact change to prompt**:  
   - Add a rule: `"Directors + Related liabilities" → Row 249 (Creditors for Expenses)"`  
   - OR add an example: `"Other Liabilities (Directors)" → Row 249 (Creditors for Expenses)"`.  

5. **Routing regex pattern**:  
   ```python
   r"(?i)(directors|

### 91. `Display amount/Discount` (Kurunji_Retail)
- Correct: Row 42 (Raw Materials Consumed ( Indigenous))
- Predicted: Row None (DOUBT)
- Correct in options: NO
- Routed to: other_income

**V3 Response:** ### PART A — Why it went wrong:
1. **No** (Row 42 was not in the POSSIBLE CMA ROWS list).  
2. N/A (since Row 42 wasn't an option).  
3. Keywords like "Display amount/Discount" should have triggered a rule like:  
   - `"Discount" → Row 42 (Raw Materials Consumed)`  

### PART B — What would make you get it RIGHT:  
4. **Exact change needed:**  
   - *"Add Row 42 (Raw Materials Consumed (Indigenous)) to the POSSIBLE CMA ROWS list"*  
   - *"Add a rule: 'Display amount/Discount' → Row 42 (Raw Materials Consumed)"*  

5. **Python regex pattern for routing:**  
   ```python
   r"(?i)(display.*amount|discount)"
   ```  

**Reasoning:** The item was miscategorized because Row 42 wasn’t an available option, and no rule linked "Display amount/Discount" to raw materials. Adding the row or a keyword rule would fix this. The regex captures case-insensitive variants of the key terms.  

(Words: ~

### 92. `Opening Stock of Packing` (Kurunji_Retail)
- Correct: Row 44 (Stores and spares consumed ( Indigenous))
- Predicted: Row 71 (Others)
- Correct in options: NO
- Routed to: admin_expense

**V3 Response:** ### PART A — Why it went wrong:  
1. **No** – Row 44 was **not** in the POSSIBLE CMA ROWS list.  
2. N/A (Row 44 wasn’t an option).  
3. Keywords like **"Stock of Packing"** should trigger stores/spares (Row 44), but **only if listed**.  

### PART B — What would make you get it RIGHT:  
4. **Exact change**: Add `Row 44 | II_D8 | Stores and spares consumed (Indigenous)` to the POSSIBLE CMA ROWS list.  
   - **Reason**: "Opening Stock of Packing" is a stores/spares item by CA rules (see examples).  

5. **Python regex pattern**:  
   ```python
   r"(opening|closing)\s*(stock|inventory)\s*of\s*(packing|stores|spares)"
   ```  
   Matches variations like "Opening Stock of Packing" → Row 44.  

---  
**Key Fix**: Row 44 must *exist* in the dropdown. Rules/examples alone won’t help if the row is missing.

### 93. `Packing Expenses` (Kurunji_Retail)
- Correct: Row 44 (Stores and spares consumed ( Indigenous))
- Predicted: Row 71 (Others)
- Correct in options: NO
- Routed to: admin_expense

**V3 Response:** ### Part A — Why it went wrong:  
1. **No**, Row 44 was **not** in the POSSIBLE CMA ROWS list.  
2. N/A (Row 44 wasn’t an option).  
3. Keywords like **"Packing"** should trigger routing to **stores/spares** (Row 44) per CA expert rules (e.g., "Packing charges" → Row 44).  

### Part B — What would make you get it RIGHT:  
4. **Exact change**:  
   - *"Add Row 44 (Stores and spares consumed ( Indigenous)) to the POSSIBLE CMA ROWS list"*  
   - *"Add a rule: 'Packing Expenses → Row 44 (Stores and spares consumed ( Indigenous))'"*  

5. **Regex pattern** (Python):  
   ```python
   r'(packing|packages?|stores|spares)', re.IGNORECASE  # Matches "Packing Expenses" to Row 44
   ```  

**Key Fix**: Include Row 44 in options or explicitly map "Packing" to stores/spares. Rules precedence failed due to

### 94. `Stock of Packing Materials` (Kurunji_Retail)
- Correct: Row 44 (Stores and spares consumed ( Indigenous))
- Predicted: Row 34 (Others)
- Correct in options: NO
- Routed to: other_income

**V3 Response:** **PART A — Why it went wrong:**  
1. No, Row 44 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 44 was not an option).  
3. Keywords like "Stock of Packing Materials" should have triggered routing to a section related to stores or materials consumed, but Row 44 was unavailable.  

**PART B — What would make you get it RIGHT:**  
4. Add Row 44 (Stores and spares consumed ( Indigenous)) to the POSSIBLE CMA ROWS list.  
5. Routing regex pattern:  
```python  
r"(stock|packing|materials)"  
```  
This pattern would match keywords like "Stock of Packing Materials" and route it to Row 44.

### 95. `Esi` (Kurunji_Retail)
- Correct: Row 45 (Wages)
- Predicted: Row 67 (Salary and staff expenses)
- Correct in options: NO
- Routed to: admin_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. No, Row 45 (Wages) was NOT in the POSSIBLE CMA ROWS list.  
2. N/A (Row 45 was not an option).  
3. The keyword "Esi" should have triggered routing to the Wages section, as per CA-verified examples.  

**PART B — What would make you get it RIGHT:**  
4. Add Row 45 (Wages) to the POSSIBLE CMA ROWS list.  
5. Routing regex pattern:  
   ```python  
   r"(?i)\b(esi|salary|provident fund|staff welfare)\b"  
   ```  
This pattern would match "Esi" and similar keywords, routing them to the Wages section.

### 96. `Staff Welfare` (Kurunji_Retail)
- Correct: Row 45 (Wages)
- Predicted: Row 67 (Salary and staff expenses)
- Correct in options: Yes
- Routed to: employee_cost, admin_expense

**V3 Response:** ### PART A — Why it went wrong:  
1. **Yes**, Row 45 (Wages) was in the POSSIBLE CMA ROWS list.  
2. **You picked Row 67** because "Staff Welfare" lacks explicit keywords like "salary" or "wages." The prompt lacked a rule/explicit example mapping "Staff Welfare" → Row 45 (Wages), despite CA Expert Rules linking similar terms (e.g., "Provident Fund") to wages.  
3. **Keywords triggering Row 45**: "welfare," "staff," "ESI," "provident" (per CA rules).  

### PART B — What would make you get it RIGHT:  
4. **Exact change**: Add a rule under **CA EXPERT RULES**:  
   `"Staff welfare expenses" -> Row 45 (Wages)`  
   (Mirroring the verified example from "EXAMPLES FROM OTHER COMPANIES").  

5. **Python regex pattern**:  
   ```python  
   r"(?i)(staff\s*welfare|esi|provident\s*fund|wages?|salar(y|ies))"  
   ```  
   This catches variations

### 97. `Staff Mess Expenses` (Kurunji_Retail)
- Correct: Row 45 (Wages)
- Predicted: Row 67 (Salary and staff expenses)
- Correct in options: Yes
- Routed to: employee_cost, admin_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. Yes, Row 45 (Wages) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 67 because "Staff Mess Expenses" was interpreted as a general staff-related expense, aligning with "Salary and staff expenses" (Row 67). I overlooked the CA Expert Rule and examples that classify staff-related expenses under "Wages" (Row 45).  
3. N/A (Row 45 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add a CA Expert Rule: "Staff Mess Expenses → Row 45 (Wages)" or add an example: "Staff Mess Expenses → Row 45 (Wages)". This would explicitly link the item to the correct row.  

5. Routing regex pattern:  
```python  
import re  
pattern = re.compile(r"(staff|wages|salary|mess|provident|esi|gratuity|labour|bonus)", re.IGNORECASE)  
if pattern.search("Staff Mess Expenses"):  
    return "Row 45 (Wages)"  
```  
This pattern captures keywords related to staff and wages,

### 98. `Electric Charges` (Kurunji_Retail)
- Correct: Row 48 (Power, Coal, Fuel and Water)
- Predicted: Row 71 (Others)
- Correct in options: NO
- Routed to: admin_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. No, Row 48 (Power, Coal, Fuel and Water) was NOT in the POSSIBLE CMA ROWS list.  
2. N/A (Row 48 was not an option).  
3. Keywords like "Electric Charges" should have triggered routing to a section like "Power, Coal, Fuel and Water" based on CA expert rules and examples.  

**PART B — What would make you get it RIGHT:**  
4. Add Row 48 (Power, Coal, Fuel and Water) to the POSSIBLE CMA ROWS list.  
5. Routing regex pattern:  
```python  
r"(electric|power|coal|fuel|water|charges)", re.IGNORECASE  
```  

This change ensures "Electric Charges" is correctly classified under Row 48.

### 99. `Tds on Rent` (Kurunji_Retail)
- Correct: Row 49 (Others)
- Predicted: Row 68 (Rent , Rates and Taxes)
- Correct in options: NO
- Routed to: admin_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. No, Row 49 (Others) was NOT in the POSSIBLE CMA ROWS list.  
2. N/A (Row 49 was not an option).  
3. The keyword "Tds on Rent" should have triggered routing to "Others" (Row 71) since "Tds" (Tax Deducted at Source) is a generic term not explicitly tied to "Rent, Rates and Taxes."  

**PART B — What would make you get it RIGHT:**  
4. Add Row 71 (Others) to the POSSIBLE CMA ROWS list and include an example: "Tds on Rent" → Row 71 (Others).  
5. Routing regex pattern:  
```python  
r"(Tds|Tax Deducted at Source).*(Rent|Payment)"  
```  
This pattern would correctly route items containing "Tds" or "Tax Deducted at Source" related to "Rent" or "Payment" to Row 71 (Others).

### 100. `Rent - Parking` (Kurunji_Retail)
- Correct: Row 49 (Others)
- Predicted: Row 68 (Rent , Rates and Taxes)
- Correct in options: NO
- Routed to: admin_expense

**V3 Response:** **PART A — Why it went wrong:**  
1. No  
2. N/A (Row 49 wasn’t an option)  
3. The keyword "Rent - Parking" should trigger routing to "Others" based on CA expert rules (similar to "Rent" examples).  

**PART B — What would make you get it RIGHT:**  
4. **Exact change:** Add an example: `"Rent - Parking" → Row 71 (Others)` to the prompt’s "EXAMPLES FROM OTHER COMPANIES" section.  
5. **Regex pattern:**  
   ```python  
   r"(?i)(rent.*parking|rent(?!.*office))" → Row 71  
   ```  
   *Rationale:* Captures "Parking" rent variants while excluding "Office Rent" (Row 68).  

(Word count: 98)
