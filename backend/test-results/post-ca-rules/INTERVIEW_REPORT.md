# Post-CA-Rules: Interview Report — Genuinely Wrong Items

**Date:** 2026-03-26 19:20
**Context:** After implementing 24 CA-verified rules (CA-001 to CA-024)

## Accuracy Comparison (Before → After CA Rules)

| Company | Before | After | Delta | Items |
|---------|--------|-------|-------|-------|
| BCIPL | 63.84% | 67.86% | +4.0% | 224 |
| Dynamic_Air | 0% | 80.0% | +80.0% | 230 |
| Mehta_Computer | 1.35% | 74.32% | +73.0% | 74 |
| INPL | 1.61% | 20.97% | +19.4% | 186 |
| Kurunji_Retail | 0% | 26.47% | +26.5% | 136 |
| MSL | 2.25% | 33.64% | +31.4% | 110 |
| SLIPL | 0% | 30.77% | +30.8% | 65 |
| SR_Papers | 3.05% | 31.48% | +28.4% | 216 |
| SSSS | 9.52% | 21.77% | +12.2% | 294 |

**Overall:** 10.6% → 42.7% (+32.1pp)

## Interview Summary

- **Total wrong entries:** 880
- **GT offset bugs (not real errors):** 10
- **Genuinely wrong:** 870
- **Unique (deduplicated):** 549
- **Interviewed:** 100

## Root Cause Split

- **Routing bug** (correct row not in options): 36
- **Model error** (correct row available, picked wrong): 64

## Routing Bugs (correct row NOT in options)

| # | Item | Company | Correct Row | Predicted Row | Routed To |
|---|------|---------|-------------|---------------|-----------|
| 1 | Profit on Sale of Fixed Asset | BCIPL | R22 (Domestic) | R31 (Profit on sale of fi) | other_income |
| 2 | Sale of Duty Credit Scrips | BCIPL | R22 (Domestic) | R34 (Others) | other_income |
| 6 | Rent | BCIPL | R48 (Power, Coal, Fuel an) | R68 (Rent , Rates and Tax) | admin_expense |
| 7 | Directors Remuneration | BCIPL | R66 (Row 66) | R73 (Audit Fees & Directo) | employee_cost |
| 16 | Advances Written off | BCIPL | R74 (Row 74) | R69 (Bad Debts) | admin_expense |
| 17 | Interest of Income Tax | BCIPL | R82 (Row 82) | R99 (Income Tax  provisio) | tax,finance_cost |
| 19 | Forex Rate Fluctuation Loss | BCIPL | R90 (Sundry Balances Writ) | R71 (Others) | admin_expense |
| 21 | Surplus at the beginning of the year | BCIPL | R105 (Row 105) | R125 (Other Reserve) | reserves |
| 22 | Surplus at the beginning of the year | BCIPL | R105 (Row 105) | R122 (Balance transferred ) | reserves |
| 23 | Other Bank Balances (Cr.) | BCIPL | R130 (Row 130) | R213 (Bank Balances) | cash,current_liabilities |
| 26 | Current Maturities of Long-term Debt | BCIPL | R135 (Row 135) | R250 (Other current liabil) | current_liabilities |
| 27 | Current Maturities of Long-term Debt | BCIPL | R135 (Row 135) | R131 (From Indian Bank) | borrowings_short |
| 29 | Unsecured Loans from Directors | BCIPL | R151 (Row 151) | R153 (As Long Term Debt) | borrowings_long |
| 35 | GST Input Recoverable | BCIPL | R218 (Row 218) | R223 (Other Advances / cur) | other_assets |
| 36 | Exceeding 6 months | BCIPL | R231 (Row 231) | R208 (Debtors more than 6 ) | receivables |
| 39 | Long-term Loans and Advances | BCIPL | R236 (Advances to supplier) | R153 (As Long Term Debt) | borrowings_long,fixed_assets |
| 41 | Other Non- Current Assets | BCIPL | R237 (Security deposits wi) | R172 (Other Intangible ass) | fixed_assets |
| 47 | Interest on Delay in payment of taxes | Dynamic_Air | R83 (Interest on Fixed Lo) | R71 (Others) | admin_expense |
| 48 | Liquidty Damages | Dynamic_Air | R83 (Interest on Fixed Lo) | R71 (Others) | admin_expense |
| 52 | Surplus - Opening balance | Dynamic_Air | R106 (Brought forward from) | R122 (Balance transferred ) | reserves |
| 56 | Rent - Factory | Dynamic_Air | R68 (Rent , Rates and Tax) | R49 (Others) | manufacturing_expense,raw_materials |
| 60 | Loan from Banks - current maturities | Dynamic_Air | R136 (Term Loan Repayable ) | R131 (From Indian Bank) | borrowings_short |
| 61 | Vehicle HP Loans - current maturities | Dynamic_Air | R140 (Repayable in next on) | R131 (From Indian Bank) | admin_expense,borrowings_short |
| 62 | Vehicle HP Loans - current maturities | Dynamic_Air | R140 (Repayable in next on) | R71 (Others) | admin_expense,borrowings_short |
| 66 | Electricty Charges | Mehta_Computer | R48 (Power, Coal, Fuel an) | R71 (Others) | admin_expense |
| 70 | By Closing Stock | Mehta_Computer | R54 (Stock in process Clo) | R25 (Less Excise Duty and) | revenue |
| 74 | Bill Discount Charges | Mehta_Computer | R85 (Bank Charges) | R133 ((o/s bill discountin) | borrowings_short,admin_expense |
| 75 | Flat 1 At Kalathiappa Street - 1/4Th Sha | Mehta_Computer | R162 (Gross Block) | R186 (Other non current in) | investments |
| 76 | Flat 2 At Kalathiappa Street - 1/4Th Sha | Mehta_Computer | R162 (Gross Block) | R229 (Investments) | investments |
| 78 | Stock-in-Trade ( Valued at Cost Or Marke | Mehta_Computer | R200 (Stocks-in-process) | R223 (Other Advances / cur) | other_assets |
| 86 | Discount Received | INPL | R35 (Row 35) | R34 (Others) | other_income |
| 89 | Unbilled Services (WIP closing) | INPL | R55 (Row 55) | R54 (Stock in process Clo) | raw_materials |
| 93 | Directors Remuneration | INPL | R74 (Row 74) | R73 (Audit Fees & Directo) | employee_cost |
| 95 | Consultancy Charges | INPL | R50 (Repairs & Maintenanc) | R71 (Others) | admin_expense |
| 96 | Packing and Forwarding Charges | INPL | R48 (Power, Coal, Fuel an) | R71 (Others) | admin_expense |
| 98 | Transportation Charges | INPL | R48 (Power, Coal, Fuel an) | R71 (Others) | admin_expense |

## Model Errors (correct row available, wrong pick)

| # | Item | Company | Correct | Predicted | Method |
|---|------|---------|---------|-----------|--------|
| 3 | Other Materials Consumed | BCIPL | R41 | R49 | scoped_v3 |
| 4 | Other Materials Consumed | BCIPL | R43 | R49 | scoped_v3 |
| 5 | Employee Benefits Expense | BCIPL | R44 | R67 | scoped_v3 |
| 8 | Selling & Distribution Expenses | BCIPL | R69 | R71 | scoped_v3 |
| 9 | Administrative & General Expenses | BCIPL | R69 | R71 | scoped_v3 |
| 10 | Rates & Taxes | BCIPL | R70 | R68 | scoped_v3 |
| 11 | Bad debts written off | BCIPL | R70 | R69 | scoped_v3 |
| 12 | Auditor's Remuneration - Statutory  | BCIPL | R70 | R73 | scoped_v3 |
| 13 | Auditor's Remuneration - Tax Audit | BCIPL | R70 | R73 | scoped_v3 |
| 14 | Advances Written off | BCIPL | R70 | R69 | scoped_v3 |
| 15 | Selling & Distribution Expenses | BCIPL | R72 | R70 | scoped_v3 |
| 18 | Bill Discounting Charges | BCIPL | R83 | R133 | scoped_v3 |
| 20 | Deferred Tax | BCIPL | R100 | R100 | scoped_v3 |
| 24 | Inland LC Discounting | BCIPL | R131 | R133 | scoped_v3 |
| 25 | TATA Capital | BCIPL | R131 | R131 | scoped_v3 |
| 28 | Long-term Borrowings (Secured) | BCIPL | R136 | R153 | scoped_v3 |
| 30 | Intangible Assets (Net Block) | BCIPL | R171 | R169 | scoped_v3 |
| 31 | Raw Materials | BCIPL | R193 | R42 | scoped_v3 |
| 32 | Scraps | BCIPL | R197 | RNone | scoped_doubt |
| 33 | Finished Goods | BCIPL | R200 | RNone | scoped_doubt |
| 34 | Finished Goods | BCIPL | R200 | R198 | scoped_v3 |
| 37 | Capital Advances | BCIPL | R235 | R223 | scoped_v3 |
| 38 | Capital Advances | BCIPL | R235 | R230 | scoped_v3 |
| 40 | Other Non-Current Assets | BCIPL | R236 | R238 | scoped_v3 |
| 42 | Leave Encashment | BCIPL | R243 | R249 | scoped_v3 |
| 43 | Short-term Provisions | BCIPL | R248 | R250 | scoped_v3 |
| 44 | Carriage Inwards | Dynamic_Air | R47 | R41 | scoped_v3 |
| 45 | (d) Contribution to EPF and ESI | Dynamic_Air | R67 | R45 | scoped_v3 |
| 46 | Brokerage & Commission | Dynamic_Air | R70 | R71 | scoped_v3 |
| 49 | (b) Interest on Bill discounting &  | Dynamic_Air | R84 | R133 | scoped_v3 |
| 50 | (a) Loan/Overdraft Processing Fee | Dynamic_Air | R84 | R85 | scoped_v3 |
| 51 | (3) Deferred tax Liability / (Asset | Dynamic_Air | R101 | R159 | scoped_v3 |
| 53 | (a) Salaries and incentives | Dynamic_Air | R67 | R45 | scoped_v3 |
| 54 | (c) Staff Welfare | Dynamic_Air | R67 | R45 | scoped_v3 |
| 55 | (e) Gratuity | Dynamic_Air | R67 | R45 | scoped_v3 |
| 57 | (a) Loan/Overdraft Processing Fee | Dynamic_Air | R83 | R85 | scoped_v3 |
| 58 | (c) Staff Welfare Expenses | Dynamic_Air | R67 | R45 | scoped_v3 |
| 59 | Work-in-Progress | Dynamic_Air | R200 | RNone | scoped_doubt |
| 63 | Provision for employee benefits (Gr | Dynamic_Air | R153 | R45 | scoped_v3 |
| 64 | (c) Statutory Dues - (iii) ESI & PF | Dynamic_Air | R246 | R45 | scoped_v3 |
| 65 | Interest on PPF | Mehta_Computer | R34 | R30 | scoped_v3 |
| 67 | Packing Forwarding  | Mehta_Computer | R49 | R47 | scoped_v3 |
| 68 | Transport Charges | Mehta_Computer | R49 | R47 | scoped_v3 |
| 69 | To Opening Stock | Mehta_Computer | R53 | R58 | scoped_v3 |
| 71 | Carriage Outward | Mehta_Computer | R71 | R70 | scoped_v3 |
| 72 | Sundry Balance W/off | Mehta_Computer | R71 | R75 | scoped_v3 |
| 73 | Professional tax | Mehta_Computer | R71 | R68 | scoped_v3 |
| 77 | To Depreciation | Mehta_Computer | R163 | R56 | scoped_v3 |
| 79 | TDS Receivable | Mehta_Computer | R219 | R206 | scoped_v3 |
| 80 | Gst Receivable | Mehta_Computer | R219 | R223 | scoped_v3 |
| 81 | Telephone Deposits | Mehta_Computer | R237 | R222 | scoped_v3 |
| 82 | IT Refund Due 2021 | Mehta_Computer | R219 | R221 | scoped_v3 |
| 83 | FD Accrued Interest (reclassified f | Mehta_Computer | R182 | R229 | scoped_v3 |
| 84 | Sales of Products | INPL | R23 | R22 | scoped_v3 |
| 85 | Sale of Services | INPL | R23 | R22 | scoped_v3 |
| 87 | Interest Income | INPL | R31 | R30 | scoped_v3 |
| 88 | Cost of Material Consumed | INPL | R43 | R42 | scoped_v3 |
| 90 | Staff Welfare Expenses | INPL | R68 | R45 | scoped_v3 |
| 91 | Contribution to PF and ESI | INPL | R68 | R45 | scoped_v3 |
| 92 | Gratuity to Employees | INPL | R68 | R45 | scoped_v3 |
| 94 | Interest on Unsecured Loan | INPL | R84 | R83 | scoped_v3 |
| 97 | Power and Fuel | INPL | R49 | R48 | scoped_v3 |
| 99 | Insurance Paid | INPL | R72 | R71 | scoped_v3 |
| 100 | Office Expenses | INPL | R72 | R71 | scoped_v3 |

## Full Interview Responses

### 1. `Profit on Sale of Fixed Asset` (BCIPL)
- Correct: Row 22 (Domestic)
- Predicted: Row 31 (Profit on sale of fixed assets / Investments)
- Correct in options: NO
- Routed to: other_income
- Method: scoped_v3

**AI Response:**
```
### PART A — Why it went wrong:  
1. **No** – Row 22 ("Domestic") was **not** in the POSSIBLE CMA ROWS list.  
2. N/A (Row 22 unavailable).  
3. **Routing failure**: The prompt excluded "Domestic" as an option, forcing a suboptimal choice. Keywords like "Fixed Asset" defaulted to Row 31 (CA expert rule: *"Profit on sale of Asset" → Row 31*).  

### PART B — What would make it RIGHT:  
4. **Exact fix**: Add *"Row 22 | II_A1 | Domestic Sales"* to POSSIBLE CMA ROWS.  
5. **Routing regex**: `/(Profit|Gain).*Sale.*(Asset|Fixed Asset)/i → Row 31`  
   *(But Row 22 should override if "Domestic" context exists.)*  

**Key Issue**: The provided options lacked the correct row (Row 22). Rules forced Row 31 as the "least wrong" pick despite semantic mismatch.  

---  
**Word count**: 98. **Actionable**: Add missing rows *before* enforcing rules.
```

### 2. `Sale of Duty Credit Scrips` (BCIPL)
- Correct: Row 22 (Domestic)
- Predicted: Row 34 (Others)
- Correct in options: NO
- Routed to: other_income
- Method: scoped_v3

**AI Response:**
```
### **PART A — Why it went wrong:**  
1. **No**, Row 22 (Domestic) was **not** in the POSSIBLE CMA ROWS list.  
2. N/A (since Row 22 was not an option).  
3. **"Duty Credit Scrips"** should trigger routing to **Row 22 (Domestic)** because they are export incentives issued by the government.  

### **PART B — What would make you get it RIGHT:**  
4. **Exact minimum change to prompt:** Add **Row 22 | II_A4 | Domestic** to the POSSIBLE CMA ROWS list.  
5. **Routing regex pattern:**  
   ```regex
   /(duty\s*credit|scrips?|export\s*incentive)/i
   ```  

**Key Fix:** The classifier lacked **Row 22** as an option, despite "Duty Credit Scrips" being a known export incentive (domestic income). CA rules imply such items should never hit "Others" (Row 34) if the correct row exists.  

(Word count: 120)
```

### 3. `Other Materials Consumed` (BCIPL)
- Correct: Row 41 (Raw Materials Consumed ( Imported))
- Predicted: Row 49 (Others)
- Correct in options: Yes
- Routed to: raw_materials
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**, Row 41 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 49 because "Other Materials Consumed" lacked explicit keywords like "Imported" or "Indigenous," making it seem generic. I defaulted to "Others" as a last resort.  
3. Keywords like "Imported" or "Raw Materials" in the item text should have triggered routing to Row 41.  

**PART B — What would make you get it RIGHT:**  
4. **Exact change to the prompt:** Add a rule: "If 'Materials Consumed' appears in the item text, classify under Row 41 (Raw Materials Consumed ( Imported)) unless specified otherwise."  
5. **Routing regex pattern:** `/(Materials Consumed|Imported)/i` → Route to Row 41.  

This ensures "Materials Consumed" defaults to Row 41 unless explicitly contradicted.
```

### 4. `Other Materials Consumed` (BCIPL)
- Correct: Row 43 (Stores and spares consumed ( Imported))
- Predicted: Row 49 (Others)
- Correct in options: Yes
- Routed to: raw_materials
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**, Row 43 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 49 because "Other Materials Consumed" lacked explicit keywords like "stores" or "spares," making it seem generic.  
3. N/A (Row 43 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Materials consumed" → Row 43 (Stores and spares consumed ( Imported)).  
5. Routing regex: `/(?:stores|spares|materials consumed)/i`.  

**Actionable Steps:**  
- Update rules to explicitly link "Materials Consumed" to Row 43.  
- Use regex to catch "Materials Consumed" and route to Row 43.
```

### 5. `Employee Benefits Expense` (BCIPL)
- Correct: Row 44 (Stores and spares consumed ( Indigenous))
- Predicted: Row 67 (Salary and staff expenses)
- Correct in options: Yes
- Routed to: employee_cost
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**, Row 44 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 67 because "Employee Benefits Expense" directly matched "Salary and staff expenses" (Row 67) based on the CA-VERIFIED DISAMBIGUATION RULES, which state that "Employee Benefits" → Row 45 for manufacturing, Row 67 for trading.  
3. N/A (Row 44 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. **Exact change to the prompt:** Add a rule: "Employee Benefits Expense" → Row 44 (Stores and spares consumed ( Indigenous)).  
5. **Routing regex pattern:** `/(Employee Benefits Expense)/i → Row 44`.  

**Reasoning:** The error occurred because the prompt lacked a specific rule routing "Employee Benefits Expense" to Row 44. Adding a clear rule or regex pattern would ensure correct classification.
```

### 6. `Rent` (BCIPL)
- Correct: Row 48 (Power, Coal, Fuel and Water)
- Predicted: Row 68 (Rent , Rates and Taxes)
- Correct in options: NO
- Routed to: admin_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. No, Row 48 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 48 was not an option).  
3. Keywords like "Rent" typically align with Row 68 (Rent, Rates and Taxes) based on the provided rules and examples.  

**PART B — What would make you get it RIGHT:**  
4. Add Row 48 (Power, Coal, Fuel and Water) to the POSSIBLE CMA ROWS list.  
5. Routing regex pattern:  
   ```regex  
   /Rent.*(Power|Coal|Fuel|Water)/i  
   ```  
   This would ensure "Rent" items related to utilities are routed to Row 48.  

**Summary:**  
Row 48 was not an option, and "Rent" logically matched Row 68. Adding Row 48 and a regex pattern for utility-related rents would resolve this.
```

### 7. `Directors Remuneration` (BCIPL)
- Correct: Row 66 (Row 66)
- Predicted: Row 73 (Audit Fees & Directors Remuneration)
- Correct in options: NO
- Routed to: employee_cost
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. No, Row 66 was NOT in the POSSIBLE CMA ROWS list.  
2. N/A (Row 66 was not an option).  
3. Keywords like "Directors Remuneration" should have triggered routing to Row 66, but it wasn’t listed.  

**PART B — What would make you get it RIGHT:**  
4. Add Row 66 to the POSSIBLE CMA ROWS list:  
   `Row 66 | II_D1a | Directors Remuneration`.  
5. Routing regex pattern:  
   `/(Directors Remuneration)/i → Row 66`.  

This ensures the correct row is available and explicitly matched.
```

### 8. `Selling & Distribution Expenses` (BCIPL)
- Correct: Row 69 (Bad Debts)
- Predicted: Row 71 (Others)
- Correct in options: Yes
- Routed to: selling_expense, admin_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 69 (Bad Debts) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 71 because "Selling & Distribution Expenses" did not explicitly match any specific row keywords, and "Bad Debts" did not seem directly related to selling or distribution.  
3. N/A (Row 69 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. Add a CA-verified rule: "Selling & Distribution Expenses" → Row 69 (Bad Debts).  
5. Routing regex pattern: `/Selling & Distribution Expenses/i → Row 69`.  

This change would explicitly link the item to Row 69, overriding the default "Others" classification.
```

### 9. `Administrative & General Expenses` (BCIPL)
- Correct: Row 69 (Bad Debts)
- Predicted: Row 71 (Others)
- Correct in options: Yes
- Routed to: admin_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**, Row 69 (Bad Debts) was in the POSSIBLE CMA ROWS list.  
2. **Reason for picking Row 71:** The item text "Administrative & General Expenses" did not contain keywords directly matching "Bad Debts." Based on the CA Expert Rules, "General expenses" explicitly routes to Row 71 (Others), leading to the incorrect classification.  
3. N/A (Row 69 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. **Exact minimum change to the prompt:** Add a CA-VERIFIED DISAMBIGUATION RULE: "Administrative & General Expenses" → Row 69 (Bad Debts).  
5. **Routing regex pattern:** `/(Administrative.*General.*Expenses)|Bad Debts/i`  

This ensures "Administrative & General Expenses" is explicitly routed to Row 69 (Bad Debts) and avoids defaulting to Row 71 (Others).
```

### 10. `Rates & Taxes` (BCIPL)
- Correct: Row 70 (Advertisements and Sales Promotions)
- Predicted: Row 68 (Rent , Rates and Taxes)
- Correct in options: Yes
- Routed to: admin_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**, Row 70 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 68 because "Rates & Taxes" directly matched the keywords in Row 68 ("Rent, Rates and Taxes"), and I did not consider the broader context or disambiguation rules that might override this match.  
3. N/A (Row 70 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. **Exact change to the prompt:** Add a disambiguation rule: "If 'Rates & Taxes' appears in 'Other Expenses' and the amount is Rs.0, classify it as Row 70 (Advertisements and Sales Promotions)."  
5. **Routing regex pattern:** `^(?=.*Rates & Taxes)(?=.*Other Expenses)(?=.*Rs\.0).*` → Route to Row 70.  

This change ensures the specific context (section and amount) is considered, overriding the keyword match with Row 68.
```

### 11. `Bad debts written off` (BCIPL)
- Correct: Row 70 (Advertisements and Sales Promotions)
- Predicted: Row 69 (Bad Debts)
- Correct in options: Yes
- Routed to: admin_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**, Row 70 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 69 because the item text "Bad debts written off" directly matched the keyword "Bad Debts" in Row 69, and I did not consider Row 70 as a valid option for this item.  
3. N/A (Row 70 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. **Exact minimum change to the prompt:** Add a disambiguation rule: "Bad debts written off → Row 70 (Advertisements and Sales Promotions), NOT Row 69 (Bad Debts)."  
5. **Routing regex pattern:** `^(?i)(bad\sdebts\swritten\soff)$ → Row 70`  

This ensures the item is explicitly routed to Row 70, overriding the default keyword match to Row 69.
```

### 12. `Auditor's Remuneration - Statutory Audit` (BCIPL)
- Correct: Row 70 (Advertisements and Sales Promotions)
- Predicted: Row 73 (Audit Fees & Directors Remuneration)
- Correct in options: Yes
- Routed to: admin_expense
- Method: scoped_v3

**AI Response:**
```
### PART A — Why it went wrong:  
1. **Yes**, Row 70 (Advertisements and Sales Promotions) was in the POSSIBLE CMA ROWS list.  
2. **Incorrect keyword focus**: "Auditor's Remuneration" was misclassified under Row 73 (Audit Fees) due to the "Audit" keyword, but the *nature* (promotional/advertising) was ignored. The CA rule "Audit Fees → Row 73" overrode contextual clues.  
3. **Missed pattern**: "Sales Promotions" (Row 70) aligns with *remuneration for statutory audits tied to compliance publicity* (implied advertising of financial transparency).  

### PART B — What would make you get it RIGHT:  
4. **Minimum change**: Add "Statutory Audit" to the CA rule:  
   *"Audit Fees (except Statutory Audit)" → Row 73; "Auditor's Remuneration - Statutory Audit" → Row 70."*  
5. **Routing regex**:  
   ```^(?=.*\bAuditor['s]*\b)(?=.*\b(Statutory|Promotion|Advertisement
```

### 13. `Auditor's Remuneration - Tax Audit` (BCIPL)
- Correct: Row 70 (Advertisements and Sales Promotions)
- Predicted: Row 73 (Audit Fees & Directors Remuneration)
- Correct in options: Yes
- Routed to: admin_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes  
2. Focused on "Auditor's Remuneration" matching "Audit Fees" in Row 73, ignoring the "Tax Audit" modifier.  
3. N/A (Row 70 was listed)  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: *"Tax Audit fees → Row 70 (Advertisements), NOT Row 73 unless specified as statutory audit."*  
5. Regex: `/(Tax\s*Audit|Audit\s*Tax)/i → Row 70`  

**Key Issue:** The "Tax Audit" qualifier was overlooked. Explicit rules for tax-related audit fees would override the default "Audit Fees" mapping.
```

### 14. `Advances Written off` (BCIPL)
- Correct: Row 70 (Advertisements and Sales Promotions)
- Predicted: Row 69 (Bad Debts)
- Correct in options: Yes
- Routed to: admin_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**, Row 70 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 69 because "Advances Written off" aligns with the concept of **Bad Debts**, which is a common classification for unrecoverable advances.  
3. N/A (Row 70 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add a **disambiguation rule** to the prompt:  
   - "Advances Written off" → Row 70 (Advertisements and Sales Promotions) if related to promotional activities; otherwise, Row 69 (Bad Debts).  
5. **Regex pattern**:  
   `/(Advances Written off).*(promotion|advertisement|sales)/i`  
   This would route the item to Row 70 if the context includes promotional or advertising keywords.  

**Summary**: The misclassification occurred because "Advances Written off" typically aligns with Bad Debts. Adding a disambiguation rule or regex pattern to account for promotional contexts would ensure correct routing to Row 70.
```

### 15. `Selling & Distribution Expenses` (BCIPL)
- Correct: Row 72 (Repairs & Maintenance)
- Predicted: Row 70 (Advertisements and Sales Promotions)
- Correct in options: Yes
- Routed to: selling_expense, admin_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes  
2. "Selling & Distribution Expenses" is broad, and without specific keywords (e.g., "repairs"), the model defaulted to Row 70 due to the marketing/sales association.  
3. N/A (Row 72 was available).  

**PART B — What would make you get it RIGHT:**  
4. Exact change: Add "(incl. Repairs)" to the item text: *"Selling & Distribution Expenses (incl. Repairs)"*.  
5. Regex pattern: `/\b(repairs|maintenance|building\s?maintenance)\b/i`.  

**Key Fixes:**  
- Explicitly include repair-related keywords in the item text.  
- Prioritize "Repairs & Maintenance" for any expense containing repair terms, even under broader headers.  

*(Word count: 100)*-
```

### 16. `Advances Written off` (BCIPL)
- Correct: Row 74 (Row 74)
- Predicted: Row 69 (Bad Debts)
- Correct in options: NO
- Routed to: admin_expense
- Method: scoped_v3

**AI Response:**
```
### PART A — Why it went wrong:  
1. **No**, Row 74 was NOT in the POSSIBLE CMA ROWS list.  
2. N/A (Row 74 was not an option).  
3. **"Advances Written off"** should trigger "Bad Debts" (Row 69) per CA rules (similar to bad debt write-offs), but Row 74 (likely "Miscellaneous Expenses written off") was the correct answer despite not being listed.  

### PART B — What would make you get it RIGHT:  
4. **Exact change**: Add `Row 74 | II_E1 | Miscellaneous Expenses written off` to the POSSIBLE CMA ROWS list.  
5. **Routing regex**: `/(written\s*off|advances\s*wipe)/i` → Route to Row 74 (non-cash write-offs).  

**Key issue**: The prompt omitted Row 74 as an option, forcing a suboptimal choice. Rule clarification: "Advances written off" defaults to Row 74 (non-cash write-offs) unless explicitly mapped elsewhere.  

*(Words: 120)*
```

### 17. `Interest of Income Tax` (BCIPL)
- Correct: Row 82 (Row 82)
- Predicted: Row 99 (Income Tax  provision)
- Correct in options: NO
- Routed to: tax, finance_cost
- Method: scoped_v3

**AI Response:**
```
### PART A — Why it went wrong:  

1. **Was Row 82 in the POSSIBLE CMA ROWS list?**  
   **No** — Row 82 was not listed as an option.  

2. **If no: keywords triggering correct section?**  
   The item text **"Interest of Income Tax"** should decompose into:  
   - "Interest" → Row 83/84 (finance costs)  
   - "Income Tax" → Row 99 (tax provision).  
   Since Row 82 was absent, ambiguity arose.  

### PART B — What would make you get it RIGHT:  

4. **Minimum change to prompt for correct routing:**  
   Add **Row 82 | II_F0 | Interest on Income Tax** to the POSSIBLE CMA ROWS list.  

5. **ONE routing regex pattern:**  
   `/(Interest\s*(on|of)\s*Income\s*Tax)/i` → Route to **Row 82** if present.  

**Actionable fix**: Explicitly include tax-related interest rows (e.g., Row 82) in finance costs options.  

*(Words: 85)*
```

### 18. `Bill Discounting Charges` (BCIPL)
- Correct: Row 83 (Interest on Fixed Loans / Term loans)
- Predicted: Row 133 ((o/s bill discounting balance to be included))
- Correct in options: Yes
- Routed to: borrowings_short, finance_cost
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 83 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 133 because "Bill Discounting Charges" matched the CA EXPERT RULE: "Bills discounted / Bills Purchased" -> Row 133.  
3. N/A (Row 83 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add a CA EXPERT RULE: "Bill Discounting Charges" -> Row 83 (Interest on Fixed Loans / Term loans).  
5. Routing regex pattern: `/Bill Discounting Charges/i → Row 83`.  

This change would override the default routing to Row 133 and ensure correct classification based on the nature of the charge as interest-related.
```

### 19. `Forex Rate Fluctuation Loss` (BCIPL)
- Correct: Row 90 (Sundry Balances Written off)
- Predicted: Row 71 (Others)
- Correct in options: NO
- Routed to: admin_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. No, Row 90 was NOT in the POSSIBLE CMA ROWS list.  
2. N/A (Row 90 was not an option).  
3. Keywords like "Forex Rate Fluctuation Loss" suggest a non-cash write-off, which aligns with Row 90 (Sundry Balances Written off), but Row 90 was not available.  

**PART B — What would make you get it RIGHT:**  
4. Add Row 90 (Sundry Balances Written off) to the POSSIBLE CMA ROWS list.  
5. Routing regex pattern: `/(Forex Rate Fluctuation Loss|Exchange Rate Loss)/i` to map to Row 90.  

**Summary:** The error occurred because Row 90 was not in the options. Adding Row 90 and a regex pattern for "Forex Rate Fluctuation Loss" would ensure correct classification.
```

### 20. `Deferred Tax` (BCIPL)
- Correct: Row 100 (Deferred Tax Liability)
- Predicted: Row 100 (Deferred Tax Liability)
- Correct in options: Yes
- Routed to: tax
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 100 (Deferred Tax Liability) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 100 because the item text "Deferred Tax" directly matches the keyword "Deferred Tax Liability" in Row 100, aligning with the CA EXPERT RULES and EXAMPLES FROM OTHER COMPANIES.  

**PART B — What would make you get it RIGHT:**  
4. The EXACT minimum change to the prompt would be to explicitly state: "Deferred Tax" → Row 100 (Deferred Tax Liability).  
5. The routing regex pattern would be: `/(Deferred Tax|Deferred Tax Liability)/i`.  

This ensures clear alignment with the rules and examples provided.
```

### 21. `Surplus at the beginning of the year` (BCIPL)
- Correct: Row 105 (Row 105)
- Predicted: Row 125 (Other Reserve)
- Correct in options: NO
- Routed to: reserves
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. No, Row 105 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 105 was not an option).  
3. Keywords like "Surplus at the beginning of the year" should have triggered routing to "Brought forward from previous year" (Row 106), but Row 106 was not in the options.  

**PART B — What would make you get it RIGHT:**  
4. Add Row 106 (Brought forward from previous year) to the POSSIBLE CMA ROWS list.  
5. Routing regex pattern: `/(Surplus|Balance) at the beginning of the year/i` → Row 106.  

**Actionable Fix:** Include Row 106 in the options for items related to beginning-of-year surplus or balances.
```

### 22. `Surplus at the beginning of the year` (BCIPL)
- Correct: Row 105 (Row 105)
- Predicted: Row 122 (Balance transferred from profit and loss a/c)
- Correct in options: NO
- Routed to: reserves
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. No  
2. N/A  
3. "Surplus at the beginning of the year" should have matched "brought forward" keywords (like in the examples) pointing to Row 106 *if listed*. Since Row 105/106 were absent, and "Surplus" aligns with P&L transfers, Row 122 was the closest available.  

**PART B — What would make you get it RIGHT:**  
4. Add: `Row 106 | III_L2f | Brought forward from previous year` to the POSSIBLE CMA ROWS list.  
5. Regex: `"Surplus.*(beginning|start|brought forward)" → Route to Row 106`.  

**Key Fixes:**  
- Include Row 106 in options for opening balances.  
- Clarify that "Surplus at beginning" ≠ current-year P&L transfer (Row 122).  

(Words: 99)
```

### 23. `Other Bank Balances (Cr.)` (BCIPL)
- Correct: Row 130 (Row 130)
- Predicted: Row 213 (Bank Balances)
- Correct in options: NO
- Routed to: cash, current_liabilities
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **No** (Row 130 was not in the options).  
2. N/A (correct row not available).  
3. N/A (no keywords could route to an unavailable row).  

**PART B — What would make you get it RIGHT:**  
4. **Exact prompt change:** Add *"Bank overdrafts/Credit balances (Cr.)"* to the options (e.g., Row 130 *"Bank Overdrafts"*).  
5. **Regex pattern:** `/(Bank Balance.*Cr\.?|Overdraft|Credit Bal)/i` to flag liabilities.  

**Root issue:** The item was a *credit balance* (liability), but no "Bank Overdraft" or "Credit Balances" row was listed. Forced to pick the closest (Row 213).  

**Action:** Expand options to include liability-side bank items (e.g., overdrafts).  

*(Word count: 112)*
```

### 24. `Inland LC Discounting` (BCIPL)
- Correct: Row 131 (From Indian Bank)
- Predicted: Row 133 ((o/s bill discounting balance to be included))
- Correct in options: Yes
- Routed to: fixed_assets, borrowings_short
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 131 (From Indian Bank) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 133 because "Inland LC Discounting" was interpreted as "Bills discounted / Bills Purchased," which aligns with Row 133.  
3. N/A (Row 131 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Inland LC Discounting" → Row 131 (From Indian Bank).  
5. Routing regex pattern: `/(Inland LC Discounting|Factoring|Packing Credit|Pre-shipment Finance|Post-shipment Finance)/i` → Row 131.  

This change ensures "Inland LC Discounting" is explicitly mapped to Row 131, overriding the default interpretation.
```

### 25. `TATA Capital` (BCIPL)
- Correct: Row 131 (From Indian Bank)
- Predicted: Row 131 (From Indian Bank)
- Correct in options: Yes
- Routed to: borrowings_short
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**  
2. You picked Row 131 because "TATA Capital" is a non-bank entity, but the **CA EXPERT RULES** explicitly state that *only bank-related borrowings* (e.g., "Cash Credit," "Overdraft") map to Row 131. The item lacked a bank name or qualifying keyword (like "Cash Credit").  

**PART B — What would make you get it RIGHT:**  
4. **Exact change to prompt**: Add to **CA EXPERT RULES**:  
   `- "TATA Capital" -> Row 152 (As Quasi Equity)`.  
   (Since non-bank lenders default to Quasi Equity per examples like "Loan from Related Parties".)  

5. **Routing regex**:  
   ```regex
   /(Indian|HDFC|IDBI|Indusind|HSBC)\s?Bank|Cash Credit|Overdraft|WCDL/i  
   ```  
   (Matches bank names/keywords for Row 131; non-matches route elsewhere.)  

**Key Fix**: Clarify in rules that non-bank lenders (e.g.,
```

### 26. `Current Maturities of Long-term Debt` (BCIPL)
- Correct: Row 135 (Row 135)
- Predicted: Row 250 (Other current liabilities)
- Correct in options: NO
- Routed to: current_liabilities
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **No** (Row 135 was not in the options).  
2. N/A  
3. "**Current Maturities of Long-term Debt**" should have triggered a **long-term debt** section (not "Other Current Liabilities"). Keywords: "Debt," "Long-term."  

**PART B — What would make you get it RIGHT:**  
4. Add **Row 135** ("Current Maturities of Long-term Debt") to the POSSIBLE CMA ROWS list.  
5. **Regex pattern**:  
   ```regex
   /(current maturities|portion of .* debt due|repayable within .* year)/i
   ```  
   **Action**: Route matches to **long-term debt** rows (e.g., Row 135) if listed, else default to "Other current liabilities" (Row 250).  

---  
**Key Issue**: Missing row in options forced fallback to "Other." Fix by expanding debt-related rows in the list.
```

### 27. `Current Maturities of Long-term Debt` (BCIPL)
- Correct: Row 135 (Row 135)
- Predicted: Row 131 (From Indian Bank)
- Correct in options: NO
- Routed to: borrowings_short
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **No**, Row 135 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 135 was not an option).  
3. Keywords like "Current Maturities of Long-term Debt" should have triggered routing to a section for term loans repayable within one year, but Row 135 was not available.  

**PART B — What would make you get it RIGHT:**  
4. **Exact change to the prompt:** Add "Row 135 | III_L3d | Term Loan Repayable in next one year" to the POSSIBLE CMA ROWS list.  
5. **Routing regex pattern:** `/(Current Maturities of Long-term Debt|Term Loan Repayable in next one year)/i`  

This would ensure the item is correctly classified based on its nature and keywords.
```

### 28. `Long-term Borrowings (Secured)` (BCIPL)
- Correct: Row 136 (Term Loan Repayable in next one year)
- Predicted: Row 153 (As Long Term Debt)
- Correct in options: Yes
- Routed to: borrowings_long
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**, Row 136 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 153 because the item text "Long-term Borrowings (Secured)" aligned with "As Long Term Debt" (Row 153) based on the keyword "Long-term." I overlooked the CA Expert Rule that specifies "Term Loan from Bank (repayable within 1 year)" → Row 136.  
3. The keyword "Term Loan" in the CA Expert Rules should have triggered routing to Row 136.  

**PART B — What would make you get it RIGHT:**  
4. **Exact change to the prompt:** Add a CA Expert Rule: "Long-term Borrowings (Secured) (repayable within 1 year) → Row 136 (Term Loan Repayable in next one year)."  
5. **Routing regex pattern:** `/(Term Loan|Long-term Borrowings).*(repayable within 1 year)/i` → Row 136.  

This ensures the correct classification based on repayment timing.
```

### 29. `Unsecured Loans from Directors` (BCIPL)
- Correct: Row 151 (Row 151)
- Predicted: Row 153 (As Long Term Debt)
- Correct in options: NO
- Routed to: borrowings_long
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Was Row 151 in the POSSIBLE CMA ROWS list?** No.  
2. **If no: what keywords in the item text should have triggered routing to the correct section?** The keywords "Unsecured Loans from Directors" and "Long-term Borrowings" should have triggered routing to a row specifically for director-related loans, but Row 151 was not an option.  

**PART B — What would make you get it RIGHT:**  
4. **Write the EXACT minimum change to the prompt that would make you confidently pick Row 151.** Add Row 151 to the POSSIBLE CMA ROWS list with a description like "Loans from Directors (Long-term)."  
5. **If you had to write ONE routing regex pattern that would correctly route this item, what would it be?** `.*(director|directors).*(loan|borrowing).*`  

This ensures the item is routed to the correct section for director-related loans.
```

### 30. `Intangible Assets (Net Block)` (BCIPL)
- Correct: Row 171 (Deferred Tax Asset)
- Predicted: Row 169 (Patents / goodwill / copyrights etc)
- Correct in options: Yes
- Routed to: fixed_assets, depreciation
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 171 (Deferred Tax Asset) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 169 because "Intangible Assets" was interpreted as patents/goodwill/copyrights, ignoring the "Net Block" context.  
3. N/A (Row 171 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add "Deferred Tax Asset (Net Block)" to the item text to explicitly match Row 171.  
5. Routing regex: `/(Deferred Tax Asset|Net Block)/i` to prioritize Row 171 over other intangible asset rows.  

**Key Takeaway:** The item's "Net Block" context should have triggered Row 171, but the focus on "Intangible Assets" led to Row 169. Explicitly mentioning "Deferred Tax Asset" or refining the regex would resolve this.
```

### 31. `Raw Materials` (BCIPL)
- Correct: Row 193 (Imported)
- Predicted: Row 42 (Raw Materials Consumed ( Indigenous))
- Correct in options: Yes
- Routed to: raw_materials, inventories
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**, Row 193 (Imported) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 42 because the item text "Raw Materials" matched the CA Expert Rule: "Purchases of raw materials" -> Row 42 (Raw Materials Consumed ( Indigenous)). I overlooked the section "Inventories," which should have routed it to Row 193 (Imported).  
3. N/A (Row 193 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. Add to the prompt: **"If the section is 'Inventories,' classify under Row 193 (Imported) or Row 194 (Indigenous)."**  
5. Routing regex pattern:  
   `(Raw Materials).*(Inventories)` → Route to Row 193 (Imported) or Row 194 (Indigenous).  

This change ensures the section "Inventories" is prioritized over the item text "Raw Materials," aligning with the correct classification.
```

### 32. `Scraps` (BCIPL)
- Correct: Row 197 (Imported)
- Predicted: Row None (DOUBT)
- Correct in options: Yes
- Routed to: inventories
- Method: scoped_doubt

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 197 (Imported) was in the POSSIBLE CMA ROWS list.  
2. I picked Row None because "Scraps" did not explicitly match any keywords or examples provided in the prompt, and I lacked specific guidance for classifying "Scraps" under "Inventories."  
3. N/A (Row 197 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Scraps" → Row 197 (Imported) under "Inventories."  
5. Routing regex: `/(Scraps)/i` → Row 197 (Imported).  

This change would explicitly guide the classification of "Scraps" to Row 197, ensuring correct routing based on the item's nature and section.
```

### 33. `Finished Goods` (BCIPL)
- Correct: Row 200 (Stocks-in-process)
- Predicted: Row None (DOUBT)
- Correct in options: Yes
- Routed to: inventories
- Method: scoped_doubt

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**, Row 200 was in the POSSIBLE CMA ROWS list.  
2. I picked Row None because "Finished Goods" explicitly matched Row 201 (Finished Goods), which was **not** in the POSSIBLE CMA ROWS list. Since Row 201 was unavailable, I defaulted to Row None instead of considering Row 200 as a fallback.  
3. N/A (Row 200 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. **Exact change to the prompt:** Add Row 201 (Finished Goods) to the POSSIBLE CMA ROWS list.  
5. **Routing regex pattern:** `/(Finished Goods|Stocks-in-process)/i` to route both "Finished Goods" and "Stocks-in-process" to Row 200 when Row 201 is unavailable.  

**Summary:** The error occurred because Row 201 (Finished Goods) was missing from the POSSIBLE CMA ROWS list, and I didn’t default to Row 200 as a fallback. Adding Row 201 or routing "Finished Goods" to Row 200 via a regex pattern
```

### 34. `Finished Goods` (BCIPL)
- Correct: Row 200 (Stocks-in-process)
- Predicted: Row 198 (Indigenous)
- Correct in options: Yes
- Routed to: inventories
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **No**, Row 200 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 200 was missing from the options).  
3. Keywords like "Finished Goods" should map to Row 201 (per CA rules), but it was absent. Defaulted to Row 198 (Indigenous) as "Others" wasn’t forced.  

**PART B — What would make you get it RIGHT:**  
4. **Exact change:** Add `Row 200 | III_A13 | Stocks-in-process` to the POSSIBLE CMA ROWS list.  
5. **Routing regex:** `/(Finished Goods|Stock[\s-]in[\s-]Trade)/i → Row 201` (but Row 201 must be listed).  

**Key Fix:** Include Rows 200/201 in the options when classifying inventory items. The error occurred due to incomplete row options, not logic.  

*(Word count: 132)*
```

### 35. `GST Input Recoverable` (BCIPL)
- Correct: Row 218 (Row 218)
- Predicted: Row 223 (Other Advances / current asset)
- Correct in options: NO
- Routed to: other_assets
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. No  
2. N/A (Row 218 wasn’t an option)  
3. "GST Input Recoverable" implies tax-related receivables, suggesting "Advances recoverable in cash or in kind" (Row 219) or "Other Advances" (Row 223) were closest but imperfect fits.  

**PART B — What would make you get it RIGHT:**  
4. Add: **Row 218 | III_A17z | GST/Tax Recoverables** to the POSSIBLE CMA ROWS list.  
5. Regex: `/(GST|Tax)\s*(Input|Recoverable)/i` → Route to Row 218 if present.  

*Reasoning: The item is tax-related; lacking a dedicated tax recoverable row, "Other Advances" (Row 223) was picked as fallback.* (18 words)  

---  
**Total words: 113**  
**Actionable fixes:**  
- Add missing tax-specific row (critical).  
- Regex ensures future matches if row exists.  
- Prefer Row 219 over 223 for recoverable amounts when no tax row exists. (Confidence
```

### 36. `Exceeding 6 months` (BCIPL)
- Correct: Row 231 (Row 231)
- Predicted: Row 208 (Debtors more than 6 months)
- Correct in options: NO
- Routed to: receivables
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **No** – Row 231 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 231 was not an option).  
3. No keywords triggered routing because the correct section (Row 231) was **excluded** from the options.  

**PART B — What would make you get it RIGHT:**  
4. **Exact change:** Add `Row 231 | III_A15d | Debtors more than six months` to the POSSIBLE CMA ROWS list.  
5. **Regex pattern:**  
   ```regex  
   /(Exceeding|More than)\s*(6|six)\s*months/i  
   ```  
   → Would route to **Row 231** if included.  

**Key Issue:** The prompt **omitted** the correct row entirely. The existing examples (e.g., "Debtors more than six months" → Row 232) hinted at a pattern, but Row 208 was the closest available.  

**Action:** Ensure prompt includes **all relevant rows** for receivables aging (Rows 206-208 + 231-232).
```

### 37. `Capital Advances` (BCIPL)
- Correct: Row 235 (Dues from directors / partners / promoters)
- Predicted: Row 223 (Other Advances / current asset)
- Correct in options: Yes
- Routed to: other_assets
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 235 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 223 because "Capital Advances" lacked explicit keywords like "directors," "partners," or "promoters," which are specific to Row 235.  
3. N/A (Row 235 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add the keyword "directors," "partners," or "promoters" to the item text, e.g., "Capital Advances to Directors."  
5. Routing regex: `/(capital\s*advances.*(directors?|partners?|promoters?))/i`.  

This change ensures explicit routing to Row 235 by including key identifiers.
```

### 38. `Capital Advances` (BCIPL)
- Correct: Row 235 (Dues from directors / partners / promoters)
- Predicted: Row 230 (Advances)
- Correct in options: Yes
- Routed to: other_assets
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 235 was in the list.  
2. "Capital Advances" lacks explicit director/partner keywords (e.g., "director," "promoter"), so defaulted to the generic "Advances" (Row 230).  
3. N/A (Row 235 was present).  

**PART B — What would make you get it RIGHT:**  
4. Change item text to: *"Capital Advances to Directors"* (explicitly triggers Row 235 per CA rules).  
5. Regex: `/(capital\s*advances.*(director|partner|promoter)|loan\/advance.*director)/i`  

**Key Fixes:**  
- Clarify nature of "Capital Advances" in item text (e.g., link to directors).  
- Strengthen regex to catch implicit director-linked advances.  

*Word count: 98*
```

### 39. `Long-term Loans and Advances` (BCIPL)
- Correct: Row 236 (Advances to suppliers of capital goods)
- Predicted: Row 153 (As Long Term Debt)
- Correct in options: NO
- Routed to: borrowings_long, fixed_assets
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. No, Row 236 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 236 was not an option).  
3. Keywords like "Advances" and "suppliers" should have triggered routing to "Advances to suppliers of capital goods."  

**PART B — What would make you get it RIGHT:**  
4. Add Row 236 to the POSSIBLE CMA ROWS list:  
   `Row 236 | III_A10 | Advances to suppliers of capital goods`  
5. Routing regex pattern:  
   `/Advances.*suppliers.*capital goods/i`  

This ensures the item is correctly classified when the specific row is available.
```

### 40. `Other Non-Current Assets` (BCIPL)
- Correct: Row 236 (Advances to suppliers of capital goods)
- Predicted: Row 238 (Other non current assets)
- Correct in options: Yes
- Routed to: other_assets, fixed_assets
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 236 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 238 because "Other Non-Current Assets" directly matched its description, and I didn’t infer the underlying nature of the item as "Advances to suppliers of capital goods."  
3. N/A (Row 236 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add context to the item text: "Other Non-Current Assets (Advances to suppliers of capital goods)."  
5. Routing regex: `.*(advance.*capital goods).*`  

This change would explicitly link the item to Row 236, ensuring correct classification.
```

### 41. `Other Non- Current Assets` (BCIPL)
- Correct: Row 237 (Security deposits with government departments)
- Predicted: Row 172 (Other Intangible assets)
- Correct in options: NO
- Routed to: fixed_assets
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **No**, Row 237 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 237 was not an option).  
3. Keywords like "Security deposits" or "government departments" would have triggered routing to the correct section.  

**PART B — What would make you get it RIGHT:**  
4. **Exact change:** Add Row 237 (Security deposits with government departments) to the POSSIBLE CMA ROWS list.  
5. **Routing regex pattern:** `/(Security\s*Deposits|Government\s*Departments)/i`  

This ensures the item is correctly routed based on specific keywords.
```

### 42. `Leave Encashment` (BCIPL)
- Correct: Row 243 (Advance received from customers)
- Predicted: Row 249 (Creditors for Expenses)
- Correct in options: Yes
- Routed to: current_liabilities
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes  
2. I incorrectly followed the rule "*Leave Encashment* in BS → Row 249" without considering context. The item was under "Short-term Provisions," which aligns with employee liabilities, but the correct routing ("Advance received from customers") suggests this was a misclassified item in the source data.  
3. N/A (Row 243 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add to prompt: "*If 'Leave Encashment' is under 'Short-term Provisions' BUT labeled as advance/receivable, route to Row 243.*"  
5. Regex: `(Leave Encashment).*(advance|received|customer)` to override default routing when advance terms appear.  

**Actionable Fix**: Prioritize section-header keywords (e.g., "Advance") over general rules. Confidence drop to 0.7 when section contradicts default mapping.  

(Words: 120)
```

### 43. `Short-term Provisions` (BCIPL)
- Correct: Row 248 (Interest Accrued and due)
- Predicted: Row 250 (Other current liabilities)
- Correct in options: Yes
- Routed to: current_liabilities
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**, Row 248 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 250 because "Short-term Provisions" lacked explicit keywords like "interest" or "accrued," making it ambiguous. The section header "Short-term Provisions" didn’t clearly align with Row 248, so I defaulted to "Other current liabilities" as a last resort.  
3. N/A (Row 248 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. Add a CA-verified rule: **"Short-term Provisions" → Row 248 (Interest Accrued and due)**.  
5. Routing regex pattern:  
   `/(Short-term Provisions|Interest Accrued and due)/i`  

This change and pattern would explicitly link "Short-term Provisions" to Row 248, ensuring correct classification.
```

### 44. `Carriage Inwards` (Dynamic_Air)
- Correct: Row 47 (Freight and Transportation Charges)
- Predicted: Row 41 (Raw Materials Consumed ( Imported))
- Correct in options: Yes
- Routed to: raw_materials
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**, Row 47 was in the list.  
2. Picked Row 41 due to the CA expert rule: *"Freight inward / carriage inward -> Row 41 (Raw Materials Consumed (Imported))"*. Misapplied the rule without checking the specific "Freight and Transportation Charges" row. Overlooked literal keyword match ("Carriage" ≈ "Freight").  

**PART B — What would make you get it RIGHT:**  
4. **Exact prompt change:** Modify the CA expert rule to:  
   *"Freight inward / carriage inward -> Row 47 (Freight and Transportation Charges). Row 41 ONLY for direct import costs (customs duty, C&F for imports)."*  
5. **Routing regex:**  
   ```(carriage|freight|transport).*inwards?``` → Route to Row 47.  

**Key fix:** Prioritize direct keyword matches (e.g., "Freight" in row label) over broad expert rules. Clarify rules to exclude freight charges from Raw Materials unless explicitly tied to imports.  

(Word count: 139)
```

### 45. `(d) Contribution to EPF and ESI` (Dynamic_Air)
- Correct: Row 67 (Salary and staff expenses)
- Predicted: Row 45 (Wages)
- Correct in options: Yes
- Routed to: employee_cost
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 67 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 45 because the CA-VERIFIED DISAMBIGUATION RULES explicitly state: "Employee items (gratuity, EPF, ESI) → Row 45 (Wages) always." This rule overrode other considerations.  
3. N/A (Row 67 was available).  

**PART B — What would make you get it RIGHT:**  
4. The prompt should clarify that "Employee Benefits Expense" items, especially EPF and ESI contributions, should be classified under Row 67 (Salary and staff expenses) unless explicitly tied to manufacturing wages.  
5. Routing regex pattern:  
   `(EPF|ESI|Employee Benefits Expense).*` → Row 67 (Salary and staff expenses).  

This change ensures EPF/ESI contributions are correctly routed to Row 67, overriding the default "Wages" rule.
```

### 46. `Brokerage & Commission` (Dynamic_Air)
- Correct: Row 70 (Advertisements and Sales Promotions)
- Predicted: Row 71 (Others)
- Correct in options: Yes
- Routed to: admin_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 70 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 71 because "Brokerage & Commission" did not explicitly match keywords like "advertising" or "sales promotions," and I defaulted to "Others" as a last resort.  
3. N/A (Row 70 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Brokerage & Commission" → Row 70 (Advertisements and Sales Promotions).  
5. Routing regex: `/(Brokerage|Commission)/i` → Row 70.  

This change ensures explicit routing for "Brokerage & Commission" to Row 70, avoiding ambiguity.
```

### 47. `Interest on Delay in payment of taxes` (Dynamic_Air)
- Correct: Row 83 (Interest on Fixed Loans / Term loans)
- Predicted: Row 71 (Others)
- Correct in options: NO
- Routed to: admin_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. No, Row 83 was NOT in the POSSIBLE CMA ROWS list.  
2. N/A (Row 83 was not an option).  
3. Keywords like "Interest" and "taxes" should have routed to an interest-related row, but Row 83 was unavailable.  

**PART B — What would make you get it RIGHT:**  
4. Add Row 83 (Interest on Fixed Loans / Term loans) to the POSSIBLE CMA ROWS list.  
5. Routing regex: `/(Interest.*(taxes|delay))/i` to match interest-related tax delays.  

**Summary:**  
Row 83 was missing from the options, and the item's keywords ("Interest" and "taxes") didn't align with available rows. Adding Row 83 and a regex pattern for interest-related tax delays would fix this.
```

### 48. `Liquidty Damages` (Dynamic_Air)
- Correct: Row 83 (Interest on Fixed Loans / Term loans)
- Predicted: Row 71 (Others)
- Correct in options: NO
- Routed to: admin_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. No, Row 83 was NOT in the POSSIBLE CMA ROWS list.  
2. N/A (Row 83 was not an option).  
3. Keywords like "Liquidty Damages" should have been explicitly linked to interest-related rows (e.g., Row 83) in the CA rules or routing logic.  

**PART B — What would make you get it RIGHT:**  
4. Add Row 83 to the POSSIBLE CMA ROWS list and include a CA rule: "Liquidty Damages" → Row 83 (Interest on Fixed Loans / Term loans).  
5. Routing regex pattern: `/(Liquidty|Liquidity) Damages/i` → Route to Row 83.  

**Summary:**  
Row 83 was missing from the options, and "Liquidty Damages" lacked explicit routing rules. Adding Row 83 and a regex pattern would ensure correct classification.
```

### 49. `(b) Interest on Bill discounting & charges` (Dynamic_Air)
- Correct: Row 84 (Interest on Working capital loans)
- Predicted: Row 133 ((o/s bill discounting balance to be included))
- Correct in options: Yes
- Routed to: borrowings_short, finance_cost
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**, Row 84 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 133 because the item text contained "Bill discounting," which matched the CA EXPERT RULE: "Bills discounted / Bills Purchased" -> Row 133.  
3. N/A (Row 84 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. **Exact minimum change to the prompt:** Add a CA EXPERT RULE: "Interest on Bill discounting" -> Row 84 (Interest on Working capital loans).  
5. **Routing regex pattern:** `/(Interest on Bill discounting|Working capital loans)/i` to prioritize Row 84 over Row 133.  

**Reasoning:** The CA EXPERT RULES explicitly routed "Bill discounting" to Row 133, overriding the general nature of the item as interest on working capital. Adding a specific rule for "Interest on Bill discounting" would resolve this.
```

### 50. `(a) Loan/Overdraft Processing Fee` (Dynamic_Air)
- Correct: Row 84 (Interest on Working capital loans)
- Predicted: Row 85 (Bank Charges)
- Correct in options: Yes
- Routed to: borrowings_short, finance_cost
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**, Row 84 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 85 because the CA-VERIFIED DISAMBIGUATION RULES explicitly state: *"Loan Processing Fee" → Row 85 (Bank Charges), NOT Row 84 (WC Interest).* The item text "Loan/Overdraft Processing Fee" matched this rule.  
3. N/A (Row 84 was available).  

**PART B — What would make you get it RIGHT:**  
4. **Exact change to the prompt:** Add a rule: *"Loan/Overdraft Processing Fee" → Row 84 (Interest on Working capital loans), NOT Row 85 (Bank Charges).* This would override the existing CA rule.  
5. **Routing regex pattern:** `/(Loan|Overdraft)\s*Processing\s*Fee/i` → Route to Row 84.  

**Summary:** The error occurred due to a conflicting CA rule. Adding a specific override rule or regex pattern would ensure correct classification.
```

### 51. `(3) Deferred tax Liability / (Asset)` (Dynamic_Air)
- Correct: Row 101 (Deferred Tax Asset)
- Predicted: Row 159 (Deferred tax liability)
- Correct in options: Yes
- Routed to: tax
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 101 (Deferred Tax Asset) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 159 because the item text included "Deferred tax Liability," and the CA EXPERT RULES explicitly state "Deferred tax liability" -> Row 159. I overlooked the "/ (Asset)" part, which should have routed it to Row 101.  
3. N/A (Row 101 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "If the item text contains '/ (Asset)', classify as Row 101 (Deferred Tax Asset)."  
5. Routing regex pattern: `.*Deferred tax.*\/\s*\(Asset\).*` → Row 101.  

This change ensures "/ (Asset)" is explicitly considered, overriding the default routing to Row 159.
```

### 52. `Surplus - Opening balance` (Dynamic_Air)
- Correct: Row 106 (Brought forward from previous year)
- Predicted: Row 122 (Balance transferred from profit and loss a/c)
- Correct in options: NO
- Routed to: reserves
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **No**, Row 106 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 106 was not an option).  
3. Keywords like "Opening balance" or "Brought forward" should have triggered routing to Row 106, but it wasn’t an available option.  

**PART B — What would make you get it RIGHT:**  
4. **Add Row 106 (Brought forward from previous year) to the POSSIBLE CMA ROWS list.**  
5. **Regex pattern:** `(Opening balance|Brought forward|Surplus.*beginning)`  

This ensures items with these keywords are correctly routed to Row 106 when it’s an available option.
```

### 53. `(a) Salaries and incentives` (Dynamic_Air)
- Correct: Row 67 (Salary and staff expenses)
- Predicted: Row 45 (Wages)
- Correct in options: Yes
- Routed to: employee_cost
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**, Row 67 (Salary and staff expenses) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 45 because the item text "Salaries and incentives" contains "Salaries," which aligns with the CA EXPERT RULE: "Wages & Salary" -> Row 45 (Wages). Additionally, examples like "Salaries and wages" -> Row 45 reinforced this choice.  
3. N/A (Row 67 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. **Exact change to the prompt:** Add a CA-VERIFIED DISAMBIGUATION RULE: "Salaries and incentives" -> Row 67 (Salary and staff expenses).  
5. **Routing regex pattern:** `/(Salaries|Incentives)/i` → Route to Row 67 (Salary and staff expenses).  

**Summary:** The error occurred due to conflicting rules and examples favoring Row 45. Adding a specific disambiguation rule or regex pattern would ensure correct classification.
```

### 54. `(c) Staff Welfare` (Dynamic_Air)
- Correct: Row 67 (Salary and staff expenses)
- Predicted: Row 45 (Wages)
- Correct in options: Yes
- Routed to: employee_cost
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 67 (Salary and staff expenses) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 45 because "Staff Welfare" was classified under "Employee Benefits Expense," which aligns with examples like "Staff welfare expenses" -> Row 45 (Wages) in the CA-VERIFIED DISAMBIGUATION RULES and EXAMPLES FROM OTHER COMPANIES.  
3. N/A (Row 67 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Staff Welfare" in "Employee Benefits Expense" → Row 67 (Salary and staff expenses) for trading companies.  
5. Routing regex pattern: `/(Staff Welfare|Employee Benefits Expense)/i` → Row 67.  

**Summary:**  
The error occurred because the prompt lacked clarity on classifying "Staff Welfare" in "Employee Benefits Expense" for trading companies. Adding a specific rule or regex pattern would ensure correct classification.
```

### 55. `(e) Gratuity` (Dynamic_Air)
- Correct: Row 67 (Salary and staff expenses)
- Predicted: Row 45 (Wages)
- Correct in options: Yes
- Routed to: employee_cost
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes  
2. The CA rules explicitly stated "Employee items (gratuity, EPF, ESI) → Row 45 (Wages) always," overriding the context of "Salary and staff expenses" (Row 67). The examples also showed "Gratuity to Employees" mapped to Row 45.  
3. N/A (Row 67 was available)  

**PART B — What would make you get it RIGHT:**  
4. **Change the CA rule** to: "Employee items (gratuity, EPF, ESI) → Row 45 for manufacturing, Row 67 for admin/trading."  
5. **Regex**: `/(Gratuity|EPF|ESI)(?!.*factory|.*manufacturing)/i → Row 67`  
*(Match "Gratuity" unless it relates to factory/manufacturing, otherwise default to Row 45.)*  

**Key Fix**: Clarify in rules that "Gratuity" goes to Row 67 unless tied to direct labor (e.g., factory wages). Current rules overly prioritize Row 45.
```

### 56. `Rent - Factory` (Dynamic_Air)
- Correct: Row 68 (Rent , Rates and Taxes)
- Predicted: Row 49 (Others)
- Correct in options: NO
- Routed to: manufacturing_expense, raw_materials
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **No** (Row 68 was not in the options).  
2. N/A (Row 49 was the only plausible fallback for "Rent - Factory" without a dedicated Rent row).  
3. Keywords "Rent" should ideally trigger a Rent-specific row (e.g., Row 68), but it was unavailable.  

**PART B — What would make you get it RIGHT:**  
4. **Exact change to prompt**: Add `Row 68 | II_C11 | Rent, Rates and Taxes` to the POSSIBLE CMA ROWS list.  
5. **Routing regex**: `/(Rent|Lease|Tenancy)/i` → Route to Rent row (if present).  

**Actionable fix**: Expand the "POSSIBLE CMA ROWS" list to include Rent-specific rows for factory/office rent items.  

*(Words: 88)*
```

### 57. `(a) Loan/Overdraft Processing Fee` (Dynamic_Air)
- Correct: Row 83 (Interest on Fixed Loans / Term loans)
- Predicted: Row 85 (Bank Charges)
- Correct in options: Yes
- Routed to: borrowings_short, finance_cost
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 83 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 85 because the CA EXPERT RULES explicitly state: "Loan Processing Fee" → Row 85 (Bank Charges). The item text "Loan/Overdraft Processing Fee" closely matches this rule, overriding other considerations.  
3. N/A (Row 83 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add a CA EXPERT RULE: "Loan/Overdraft Processing Fee" → Row 83 (Interest on Fixed Loans / Term loans). This would override the existing rule for "Loan Processing Fee."  
5. Routing regex pattern: `/Loan\/Overdraft Processing Fee/i → Row 83`. This would explicitly route this specific item to Row 83.  

**Actionable Summary:**  
The error occurred because the CA EXPERT RULES prioritized "Loan Processing Fee" → Row 85. Adding a specific rule for "Loan/Overdraft Processing Fee" → Row 83 or a regex pattern would ensure correct classification.
```

### 58. `(c) Staff Welfare Expenses` (Dynamic_Air)
- Correct: Row 67 (Salary and staff expenses)
- Predicted: Row 45 (Wages)
- Correct in options: Yes
- Routed to: employee_cost
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**, Row 67 was in the list.  
2. Picked Row 45 due to:  
   - **Overriding "Employee Benefits" examples** (e.g., "Staff welfare expenses" → Row 45 in examples).  
   - **Section header ("Employee Benefits Expense")** biased toward manufacturing (Row 45 per CA rules).  

**PART B — How to fix it:**  
4. **Prompt change:** Add "*Trading company*" context or clarify:  
   *"Staff Welfare Expenses" → Row 67 for trading, Row 45 for manufacturing.*  
5. **Regex routing:**  
   ```regex  
   /(Staff Welfare|Employee Benefits)(?!.*factory|manufacturing)/i → Row 67  
   ```  
*(Excludes factory/manufacturing keywords to route to admin staff expenses.)*  

**Key Fixes:**  
- Disambiguate company type (manufacturing vs. trading).  
- Prioritize **section-independent matching** (e.g., "Staff Welfare" → Row 67 unless factory-linked).  

*(Words: 120)*
```

### 59. `Work-in-Progress` (Dynamic_Air)
- Correct: Row 200 (Stocks-in-process)
- Predicted: Row None (DOUBT)
- Correct in options: Yes
- Routed to: inventories
- Method: scoped_doubt

**AI Response:**
```
### PART A — Why it went wrong:  
1. **No** – Row 200 (Stocks-in-process) was **not** in the POSSIBLE CMA ROWS list.  
2. N/A (Row 200 wasn’t an option).  
3. Keywords **"Work-in-Progress"** should trigger **Row 200** per CA expert rules, but it wasn’t listed.  

### PART B — What would make you get it RIGHT:  
4. **Exact change**: Add `Row 200 | III_A13 | Stocks-in-process` to the POSSIBLE CMA ROWS list.  
5. **Regex pattern**: `/(work[- ]in[- ]progress|stocks?[- ]in[- ]process)/i` to route to Row 200.  

**Key Issue**: The provided options omitted the correct row (200) despite the item’s text clearly matching CA rules. Examples and rules consistently route "Work-in-Progress" to Stocks-in-process, but the forced choice led to "Doubt."  

---  
**Actionable Fix**: Expand inventory row options to include Row 200 for WIP items.
```

### 60. `Loan from Banks - current maturities` (Dynamic_Air)
- Correct: Row 136 (Term Loan Repayable in next one year)
- Predicted: Row 131 (From Indian Bank)
- Correct in options: NO
- Routed to: borrowings_short
- Method: scoped_v3

**AI Response:**
```
### PART A — Why it went wrong:  
1. **No** – Row 136 was **not** in the POSSIBLE CMA ROWS list.  
2. N/A (Row 136 absent → forced incorrect choice).  
3. Keywords **"current maturities"** should trigger **Term Loan Repayable in next one year** (Row 136), but this row wasn’t an option.  

### PART B — What would make you get it RIGHT:  
4. **Exact change**: Add `Row 136 | III_L3d | Term Loan Repayable in next one year` to POSSIBLE CMA ROWS.  
5. **Routing regex**:  
   ```regex
   /current maturities|repayable (within|next) one year/i
   ```  
   *(Matches "current maturities" or repayment timelines, overriding bank-specific rows.)*  

**Key Fix**: The options list lacked the correct row despite clear CA rules and examples (e.g., "Current maturities of long term debts" → Row 136). The regex would prioritize repayment terms over bank names.  

---  
**Word count**: 120 (focus: missing row + regex solution
```

### 61. `Vehicle HP Loans - current maturities` (Dynamic_Air)
- Correct: Row 140 (Repayable in next one year)
- Predicted: Row 131 (From Indian Bank)
- Correct in options: NO
- Routed to: admin_expense, borrowings_short
- Method: scoped_v3

**AI Response:**
```
### **PART A — Why it went wrong:**  
1. **No** – Row 140 ("Repayable in next one year") was **not** in the POSSIBLE CMA ROWS list.  
2. N/A (Row 140 wasn’t an option).  
3. Keywords triggering correct routing:  
   - **"current maturities"** → Implies short-term repayments (should route to "Repayable in next one year").  
   - **"HP Loans"** → Hire-purchase loans are typically classified under borrowings, but "current maturities" overrides this.  

### **PART B — What would make you get it RIGHT:**  
4. **Exact minimum change to prompt:**  
   Add:  
   `Row 140 | III_L4 | Repayable in next one year` to the POSSIBLE CMA ROWS list.  

5. **Routing regex pattern:**  
   ```regex  
   /current maturities|repayable.*next (one )?year/i  
   ```  
   This would catch all variants of "repayable within 1 year" or "current maturities".  

**Key Insight:** The missing row was
```

### 62. `Vehicle HP Loans - current maturities` (Dynamic_Air)
- Correct: Row 140 (Repayable in next one year)
- Predicted: Row 71 (Others)
- Correct in options: NO
- Routed to: admin_expense, borrowings_short
- Method: scoped_v3

**AI Response:**
```
### PART A — Why it went wrong:
1. **Was Row 140 in the POSSIBLE CMA ROWS list?**  
   **No** — It was not listed in the options provided.  

2. **Why pick Row 71?**  
   The closest matching rule was "Others" (Row 71) because "Vehicle HP Loans - current maturities" didn't align with any specific row in the given options (e.g., no "Repayable in next one year" or "Short-term Borrowings" row).  

3. **Keywords that should trigger correct routing:**  
   - "current maturities" → Should route to a short-term liability section.  
   - "HP Loans" (Hire Purchase Loans) → Should route to borrowings.  

---

### PART B — How to fix it:  
4. **Minimum change to prompt for correct routing:**  
   Add **Row 140 | III_L4 | Repayable in next one year** to the POSSIBLE CMA ROWS list.  

5. **ONE routing regex pattern:**  
   `/(current maturities|short.?term borrow)/i` → Would route to a short-term liabilities row.  

**
```

### 63. `Provision for employee benefits (Gratuity)` (Dynamic_Air)
- Correct: Row 153 (As Long Term Debt)
- Predicted: Row 45 (Wages)
- Correct in options: Yes
- Routed to: employee_cost, borrowings_long
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**, Row 153 was in the list.  
2. Picked Row 45 due to **CA-VERIFIED rule**: *"Employee items (gratuity, EPF, ESI) → Row 45 (Wages) always."* **Conflict** with *Long-term Provisions* section was overlooked.  
3. N/A (Row 153 was listed).  

**PART B — What would make you get it RIGHT:**  
4. **Exact change**: Add rule: *"Provisions for employee benefits (Gratuity) in 'Long-term Provisions' → Row 153 (As Long Term Debt)."*  
5. **Routing regex**: `/(?i)(provision.*gratuity).*long.?term/i → Row 153`.  

**Key fix**: Override default wage routing for balance-sheet provisions. (18 words)
```

### 64. `(c) Statutory Dues - (iii) ESI & PF Payable` (Dynamic_Air)
- Correct: Row 246 (Other statutory liabilities (due within 1 year))
- Predicted: Row 45 (Wages)
- Correct in options: Yes
- Routed to: employee_cost, current_liabilities
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 246 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 45 because the CA-VERIFIED DISAMBIGUATION RULES explicitly state: "Employee items (gratuity, EPF, ESI) → Row 45 (Wages) always." This rule overrode the specific context of "Statutory Dues" in the "Other Current Liabilities" section.  
3. N/A (Row 246 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Statutory Dues (ESI & PF Payable) in 'Other Current Liabilities' → Row 246 (Other statutory liabilities)." This would override the general ESI/PF rule for liabilities.  
5. Routing regex: `(Statutory Dues.*ESI & PF Payable.*Other Current Liabilities)` → Row 246.  

This change ensures context-specific classification overrides general rules.
```

### 65. `Interest on PPF` (Mehta_Computer)
- Correct: Row 34 (Others)
- Predicted: Row 30 (Interest Received)
- Correct in options: Yes
- Routed to: other_income
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 34 (Others) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 30 because "Interest on PPF" contains the keyword "Interest," which directly matches Row 30 (Interest Received).  
3. N/A (Row 34 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add a CA EXPERT RULE: "Interest on PPF" → Row 34 (Others). This would override the general "Interest" keyword rule.  
5. Routing regex pattern: `/(Interest on PPF)/i → Row 34`. This ensures "Interest on PPF" is explicitly routed to Row 34, bypassing the general "Interest" keyword match.  

**Summary:**  
The error occurred because "Interest" triggered Row 30, but "Interest on PPF" should be treated as an exception. Adding a specific rule or regex pattern would ensure correct classification.
```

### 66. `Electricty Charges` (Mehta_Computer)
- Correct: Row 48 (Power, Coal, Fuel and Water)
- Predicted: Row 71 (Others)
- Correct in options: NO
- Routed to: admin_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **No**, Row 48 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 48 was not an option).  
3. Keywords like "Electricity" or "Charges" should have triggered routing to a section like "Power, Coal, Fuel and Water," but Row 48 was unavailable.  

**PART B — What would make you get it RIGHT:**  
4. **Exact change:** Add Row 48 (Power, Coal, Fuel and Water) to the POSSIBLE CMA ROWS list.  
5. **Routing regex pattern:** `/(electricity|power|fuel|coal|water)/i` to match keywords and route to Row 48.  

**Actionable Summary:**  
Row 48 was missing from the options, leading to incorrect classification. Adding Row 48 and using a regex pattern for keywords like "electricity" would ensure correct routing.
```

### 67. `Packing Forwarding ` (Mehta_Computer)
- Correct: Row 49 (Others)
- Predicted: Row 47 (Freight and Transportation Charges)
- Correct in options: Yes
- Routed to: manufacturing_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 49 (Others) was in the POSSIBLE CMA ROWS list.  
2. "Packing Forwarding" partially matched "Freight and Transportation Charges" (Row 47) due to the transportation connotation of "forwarding," leading to misclassification. The examples lacked clarity for this specific item.  

**PART B — What would make you get it RIGHT:**  
4. Add to the **CA EXPERT RULES**:  
   - `"Packing Forwarding" -> Row 49 (Others)`  
   This direct mapping would override partial keyword matches.  

5. Regex for routing:  
   `^(?i)(packing\s*forwarding|courier)\b` → Row 49  
   Explicitly flags such terms as "Others" to avoid ambiguity.  

**Key Fixes**: Prioritize exact matches over partial keyword overlaps and add item-specific rules. (Word count: 117)
```

### 68. `Transport Charges` (Mehta_Computer)
- Correct: Row 49 (Others)
- Predicted: Row 47 (Freight and Transportation Charges)
- Correct in options: Yes
- Routed to: manufacturing_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 49 (Others) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 47 because "Transport Charges" directly matched the keyword "Freight and Transportation Charges" in Row 47, aligning with the rule to prefer specific rows over "Others" when keywords match.  
3. N/A (Row 49 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add a disambiguation rule: "Transport Charges" → Row 49 (Others), NOT Row 47 (Freight and Transportation Charges).  
5. Routing regex pattern: `^(Transport Charges)$` → Row 49 (Others).  

This change ensures "Transport Charges" is explicitly routed to Row 49, overriding the default keyword match with Row 47.
```

### 69. `To Opening Stock` (Mehta_Computer)
- Correct: Row 53 (Stock in process Opening Balance)
- Predicted: Row 58 (Finished Goods Opening Balance)
- Correct in options: Yes
- Routed to: raw_materials
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes  
2. Picked Row 58 due to "Opening Stock" matching examples like "Finished Goods Opening Balance" without distinguishing process vs. finished goods.  
3. N/A  

**PART B — What would make you get it RIGHT:**  
4. Add to examples: `"Opening Stock - Process" -> Row 53`. Explicitly map ambiguous "Opening Stock" to process/finished goods.  
5. Regex: `(?i)(opening\s*stock.*(process|wip|work\s*in\s*progress))` → Row 53.  

---  
**Key Fixes:**  
- Disambiguate "Opening Stock" in rules/examples by adding context (e.g., "process").  
- Prioritize "Stock in process" over "Finished Goods" for partial/mixed keywords.  
- Confidence drop (e.g., 0.7) if forced to choose between similar rows without clear signals.  

(Word count: 90)
```

### 70. `By Closing Stock` (Mehta_Computer)
- Correct: Row 54 (Stock in process Closing Balance)
- Predicted: Row 25 (Less Excise Duty and Cess)
- Correct in options: NO
- Routed to: revenue
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. No, Row 54 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 54 was not an option).  
3. Keywords like "Closing Stock" should have triggered routing to P&L stock-related rows (53-59), but these rows were not in the provided options.  

**PART B — What would make you get it RIGHT:**  
4. Add Row 54 (Stock in process Closing Balance) to the POSSIBLE CMA ROWS list.  
5. Routing regex pattern: `/(Closing Stock|Stock in process)/i` → Route to P&L stock rows (53-59).  

**Actionable Fix:** Include P&L stock-related rows (53-59) in the POSSIBLE CMA ROWS list for items with "Closing Stock" or similar keywords.
```

### 71. `Carriage Outward` (Mehta_Computer)
- Correct: Row 71 (Others)
- Predicted: Row 70 (Advertisements and Sales Promotions)
- Correct in options: Yes
- Routed to: selling_expense, admin_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 71 (Others) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 70 because "Carriage Outward" was incorrectly associated with sales-related expenses in the examples (e.g., "Carriage Outward" -> Row 70).  
3. N/A (Row 71 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add a CA EXPERT RULE: "Carriage Outward" -> Row 71 (Others).  
5. Routing regex pattern: `/Carriage Outward/i → Row 71`.  

**Reasoning:** The error occurred due to misleading examples associating "Carriage Outward" with Row 70. A clear rule or regex pattern would ensure correct classification.
```

### 72. `Sundry Balance W/off` (Mehta_Computer)
- Correct: Row 71 (Others)
- Predicted: Row 75 (Miscellaneous Expenses written off)
- Correct in options: Yes
- Routed to: admin_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**  
2. Picked Row 75 due to "W/off" (write-off), but ignored CA rule: "Row 75 is ONLY for non-cash write-offs." "Sundry Balance" implies administrative write-off (non-specific), fitting Row 71 per "Others" default.  
3. N/A (Row 71 was listed).  

**PART B — What would make you get it RIGHT:**  
4. **Add to CA rules**: "*'Sundry Balance W/off' → Row 71 (Others), unless explicitly non-cash.*"  
5. **Regex**: `/(sundry|balance)\s*w\s*off/i` → Route to Row 71.  

**Key Fixes**:  
- Emphasize "Others" for vague write-offs unless non-cash.  
- Clarify "W/off" alone ≠ Row 75 without explicit non-cash context.  

*(Words: 85)*
```

### 73. `Professional tax` (Mehta_Computer)
- Correct: Row 71 (Others)
- Predicted: Row 68 (Rent , Rates and Taxes)
- Correct in options: Yes
- Routed to: admin_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**, Row 71 was in the list.  
2. Incorrectly assumed "Professional tax" was a "tax" under Row 68 (Rates and Taxes) due to the keyword "tax," ignoring the CA rule that *specific* taxes (like sales tax, per expert rules) default to Row 71.  

**PART B — What would make you get it RIGHT:**  
4. **Prompt change**: Add CA rule: *"Professional tax" → Row 71 (Others), NOT Row 68 (Rates and Taxes).*  
5. **Regex pattern**: `/(Professional|Sales|Service)\s?Tax/i → Row 71`.  

**Key fix**: Explicitly distinguish "Rates and Taxes" (property/rent-related) from statutory taxes (Others).  

(Words: 88)
```

### 74. `Bill Discount Charges` (Mehta_Computer)
- Correct: Row 85 (Bank Charges)
- Predicted: Row 133 ((o/s bill discounting balance to be included))
- Correct in options: NO
- Routed to: borrowings_short, admin_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. No  
2. N/A (Row 85 was not an option)  
3. "Bill Discount Charges" aligns with CA Expert Rule: *"Bills discounted / Bills Purchased -> Row 133"*  

**PART B — What would make you get it RIGHT:**  
4. Add **Row 85 | II_D8 | Bank Charges** to POSSIBLE CMA ROWS.  
5. Regex: `/(bank charges|bill discount charges)/i` → Route to **Row 85** if present, else follow CA rules.  

**Key Fixes:**  
- Include **Row 85** in options.  
- Prioritize "Bank Charges" regex match over CA rules when conflicting.  

(Words: 98)
```

### 75. `Flat 1 At Kalathiappa Street - 1/4Th Share` (Mehta_Computer)
- Correct: Row 162 (Gross Block)
- Predicted: Row 186 (Other non current investments)
- Correct in options: NO
- Routed to: investments
- Method: scoped_v3

**AI Response:**
```
### PART A — Why it went wrong:  
1. **No**, Row 162 (Gross Block) was **not** in the POSSIBLE CMA ROWS list.  
2. N/A (Row 162 wasn’t an option, so I defaulted to Row 186 as the closest match for non-current investments).  
3. **Keywords triggering Gross Block**: "Flat" + "Street" (implies real estate asset) should route to fixed assets, but the **section "Investments" overrode this logic**.  

### PART B — What would make you get it RIGHT:  
4. **Add Row 162 to the POSSIBLE CMA ROWS list** OR **clarify that "Investments" includes fixed assets held for investment purposes**.  
5. **Regex pattern**: `/(Flat|Property|Real Estate).*?(Street|Road|Building)/i` → Route to Gross Block (Row 162) **unless section explicitly contradicts** (e.g., "Investments" supersedes for financial holdings).  

**Key Fix**: Either:  
- Add Row 162 to options, **or**  
- Add a rule: *"Investments in property (Flats, Buildings)
```

### 76. `Flat 2 At Kalathiappa Street - 1/4Th Share` (Mehta_Computer)
- Correct: Row 162 (Gross Block)
- Predicted: Row 229 (Investments)
- Correct in options: NO
- Routed to: investments
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **No**, Row 162 (Gross Block) was **not** in the POSSIBLE CMA ROWS list.  
2. N/A (Row 162 was not an option).  
3. Keywords like "Flat" and "Share" should have triggered routing to **Gross Block**, as per CA-verified examples.  

**PART B — What would make you get it RIGHT:**  
4. **Add Row 162 (Gross Block) to the POSSIBLE CMA ROWS list.**  
5. **Regex pattern:** `(Flat|Property|Building).*(Share|Ownership)`  

This would ensure items like "Flat 2 At Kalathiappa Street - 1/4Th Share" are correctly routed to **Gross Block**.
```

### 77. `To Depreciation` (Mehta_Computer)
- Correct: Row 163 (Less Accumulated Depreciation)
- Predicted: Row 56 (Depreciation)
- Correct in options: Yes
- Routed to: depreciation
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 163 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 56 because "To Depreciation" matched the keyword "Depreciation" in Row 56, and the example provided ("To Depreciation" -> Row 56) reinforced this choice.  
3. N/A (Row 163 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add a CA EXPERT RULE: "To Depreciation" -> Row 163 (Less Accumulated Depreciation).  
5. Routing regex pattern: `/(To|Total)\s*Depreciation/i` -> Row 163.  

This change would explicitly route "To Depreciation" to Row 163, overriding the ambiguous keyword match with Row 56.
```

### 78. `Stock-in-Trade ( Valued at Cost Or Market price Whichever Is` (Mehta_Computer)
- Correct: Row 200 (Stocks-in-process)
- Predicted: Row 223 (Other Advances / current asset)
- Correct in options: NO
- Routed to: other_assets
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. No  
2. N/A  
3. "Stock-in-Trade" should trigger inventory-related rows (e.g., "Stocks-in-process"), but these rows were missing from the options.  

**PART B — What would make you get it RIGHT:**  
4. Add *"Row 200 | III_A13 | Stocks-in-process"* to the POSSIBLE CMA ROWS list.  
5. Regex: `/\bStock[- ]in[- ](Trade|Process)\b/i`  

**Key Issue:** The correct row (200) was absent. The system defaults to "Other Advances" when inventory-specific rows are missing. Fix by expanding the options or improving routing logic for inventory terms.  

(Words: 95)
```

### 79. `TDS Receivable` (Mehta_Computer)
- Correct: Row 219 (Advances recoverable in cash or in kind)
- Predicted: Row 206 (Domestic Receivables ( including bills purchased and discounted))
- Correct in options: Yes
- Routed to: receivables, other_assets
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 219 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 206 because "TDS Receivable" was interpreted as a receivable, aligning with "Domestic Receivables," without considering that TDS is a recoverable advance.  
3. N/A (Row 219 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add a CA EXPERT RULE: "TDS Receivable" → Row 219 (Advances recoverable in cash or in kind).  
5. Routing regex pattern: `/(TDS|Tax Deducted at Source) Receivable/i` → Row 219.  

This change would explicitly link "TDS Receivable" to advances recoverable in cash or kind, ensuring correct classification.
```

### 80. `Gst Receivable` (Mehta_Computer)
- Correct: Row 219 (Advances recoverable in cash or in kind)
- Predicted: Row 223 (Other Advances / current asset)
- Correct in options: Yes
- Routed to: receivables, other_assets
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**, Row 219 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 223 because "Gst Receivable" was interpreted as a generic advance rather than explicitly matching the description of Row 219.  
3. N/A (Row 219 was available).  

**PART B — What would make you get it RIGHT:**  
4. **Exact change to the prompt:** Add a CA Expert Rule:  
   - "Gst Receivable" → Row 219 (Advances recoverable in cash or in kind).  
5. **Routing regex pattern:**  
   `/Gst Receivable|Tax Receivable|Advance Recoverable/i` → Row 219.  

This ensures "Gst Receivable" is explicitly routed to Row 219, avoiding ambiguity with generic "Other Advances."
```

### 81. `Telephone Deposits` (Mehta_Computer)
- Correct: Row 237 (Security deposits with government departments)
- Predicted: Row 222 (Prepaid Expenses)
- Correct in options: Yes
- Routed to: admin_expense, other_assets
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 237 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 222 (Prepaid Expenses) because "Telephone Deposits" was interpreted as a prepaid expense related to telephone services, rather than recognizing it as a security deposit with a government department.  
3. N/A (Row 237 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. Add explicit disambiguation: "Telephone Deposits" → Row 237 (Security deposits with government departments).  
5. Routing regex pattern: `/deposits.*(telephone|govt|government)/i` → Row 237.  

**Actionable Summary:**  
The error occurred due to misinterpretation of "Telephone Deposits" as a prepaid expense rather than a security deposit. Adding a specific rule or regex pattern to identify deposits related to government departments would ensure correct classification.
```

### 82. `IT Refund Due 2021` (Mehta_Computer)
- Correct: Row 219 (Advances recoverable in cash or in kind)
- Predicted: Row 221 (Advance Income Tax)
- Correct in options: Yes
- Routed to: other_assets
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 219 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 221 because "IT Refund Due" was interpreted as related to income tax, aligning with "Advance Income Tax."  
3. N/A (Row 219 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Refund Receivable" → Row 219 (Advances recoverable in cash or kind).  
5. Routing regex: `/(IT|Income Tax) Refund (Due|Receivable)/i` → Row 219.  

**Reasoning:**  
The item "IT Refund Due 2021" is a recoverable advance, not an advance payment of tax. A specific rule or regex would clarify this distinction.
```

### 83. `FD Accrued Interest (reclassified from Investments to Kotak ` (Mehta_Computer)
- Correct: Row 182 (Investment in Govt. Securities ( Current ))
- Predicted: Row 229 (Investments)
- Correct in options: Yes
- Routed to: investments
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**, Row 182 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 229 because the item text "FD Accrued Interest (reclassified from Investments to Kotak FD)" lacked explicit keywords like "Govt. Securities" or "NSC," which would have directly triggered Row 182. Instead, the mention of "Investments" led me to Row 229 as a broader match.  
3. N/A (Row 182 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. Add a **CA-VERIFIED DISAMBIGUATION RULE**:  
   - "FD Accrued Interest" → Row 182 (Investment in Govt. Securities ( Current )).  
5. **Routing regex pattern**:  
   `/FD Accrued Interest|Kotak FD|NSC/i` → Row 182.  

This change would explicitly link "FD Accrued Interest" to Row 182, overriding the broader "Investments" match. The regex would ensure similar items are correctly routed.
```

### 84. `Sales of Products` (INPL)
- Correct: Row 23 (Exports)
- Predicted: Row 22 (Domestic)
- Correct in options: Yes
- Routed to: revenue
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes  
2. The item text "Sales of Products" matched CA expert rules and examples defaulting to Row 22 (Domestic), lacking explicit export keywords (e.g., "export", "DEPB"). Section "note 21" was generic.  

**PART B — What would make you get it RIGHT:**  
4. Add "(Exports)" to the item text: *"Sales of Products (Exports)"*.  
5. Regex: `/(export|DEPB|sale of import license)/i` to override default domestic routing.  

*(Words: 74)*
```

### 85. `Sale of Services` (INPL)
- Correct: Row 23 (Exports)
- Predicted: Row 22 (Domestic)
- Correct in options: Yes
- Routed to: revenue
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes  
2. Defaulted to "Sale of Services" examples (Row 22) without export/domestic context in the item text.  
3. N/A  

**PART B — What would make you get it RIGHT:**  
4. Add "Exports" to the item text: *"Sale of Services (Exports)"*.  
5. Regex: `(Sale of Services.*Export|Export Sales)`  

**Key Fixes:**  
- Explicit export/domestic flags in item text override defaults.  
- Prefer Row 23 if "Export" appears anywhere in text/section.  

*(42 words)*
```

### 86. `Discount Received` (INPL)
- Correct: Row 35 (Row 35)
- Predicted: Row 34 (Others)
- Correct in options: NO
- Routed to: other_income
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. No  
2. N/A (Row 35 was not in options)  
3. "Discount Received" lacks keywords matching specific rows (e.g., "interest," "dividend"), forcing "Others" as default.  

**PART B — What would make you get it RIGHT:**  
4. Add `Row 35 | II_B6b | Discounts Received` to POSSIBLE CMA ROWS.  
5. Regex: `/(discount|rebate)s? (received|obtained)/i` → Route to Row 35.  

**Actionable Fix:**  
- Expand CMA rows to include common discount-specific lines.  
- Match patterns like "Discount Received" to dedicated rows before resorting to "Others."
```

### 87. `Interest Income` (INPL)
- Correct: Row 31 (Profit on sale of fixed assets / Investments)
- Predicted: Row 30 (Interest Received)
- Correct in options: Yes
- Routed to: other_income
- Method: scoped_v3

**AI Response:**
```
### PART A — Why it went wrong:  
1. **Yes**, Row 31 was in the POSSIBLE CMA ROWS list.  
2. **Misclassification reason**: The default rule for "Interest Income" is Row 30 (Interest Received), but the correct answer (Row 31) overrides this due to explicit CA-verified examples (e.g., "Profit on sale of Investment" → Row 31). The classifier overlooked context (section: "note 22 - other income") hinting at non-standard interest (e.g., investment-linked).  
3. **Trigger keywords**: "Profit on sale of" or "Investments" in the item text would explicitly route to Row 31.  

### PART B — What would make you get it RIGHT:  
4. **Exact change**: Modify the item text to *"Interest Income (from sale of investments)"* to align with Row 31’s nature.  
5. **Routing regex**:  
   ```regex  
   /(profit on sale|investment|fixed asset)/i  
   ```  
   This would catch Row 31 cases, even if "interest" is present.  

**Key Fix**: Prioritize investment-linked keywords over
```

### 88. `Cost of Material Consumed` (INPL)
- Correct: Row 43 (Stores and spares consumed ( Imported))
- Predicted: Row 42 (Raw Materials Consumed ( Indigenous))
- Correct in options: Yes
- Routed to: raw_materials
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**, Row 43 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 42 because "Cost of Material Consumed" aligns with "Raw Materials Consumed (Indigenous)" based on the CA EXPERT RULES and examples, which prioritize raw materials over stores and spares.  
3. N/A (Row 43 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. Add a disambiguation rule:  
   - **"Cost of Material Consumed" → Row 43 (Stores and spares consumed (Imported))**  
   This would override the default routing to Row 42.  
5. Routing regex pattern:  
   - **`/(Cost of Material Consumed)/i` → Row 43**  
   This ensures explicit routing for this specific item.  

**Summary:**  
The error occurred due to default routing to Row 42 based on general rules. Adding a specific disambiguation rule or regex pattern for "Cost of Material Consumed" would ensure correct classification to Row 43.
```

### 89. `Unbilled Services (WIP closing)` (INPL)
- Correct: Row 55 (Row 55)
- Predicted: Row 54 (Stock in process Closing Balance)
- Correct in options: NO
- Routed to: raw_materials
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **No**, Row 55 was **not** in the POSSIBLE CMA ROWS list.  
2. N/A (Row 55 was not an option).  
3. Keywords like "Unbilled Services" and "WIP closing" should have triggered routing to a section for unbilled services or work-in-progress, but Row 55 was not available.  

**PART B — What would make you get it RIGHT:**  
4. **Exact change:** Add Row 55 to the POSSIBLE CMA ROWS list with a description like "Unbilled Services (WIP closing)".  
5. **Routing regex pattern:** `(Unbilled Services|WIP closing)` → Row 55.  

This ensures the item is correctly classified when Row 55 is available.
```

### 90. `Staff Welfare Expenses` (INPL)
- Correct: Row 68 (Rent , Rates and Taxes)
- Predicted: Row 45 (Wages)
- Correct in options: Yes
- Routed to: employee_cost
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **Yes**, Row 68 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 45 because "Staff Welfare Expenses" aligns with employee-related expenses, and examples from other companies (e.g., "Staff welfare expenses" -> Row 45) reinforced this choice.  
3. N/A (Row 68 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. **Exact minimum change to the prompt:** Add a CA-VERIFIED DISAMBIGUATION RULE: "Staff Welfare Expenses" → Row 68 (Rent, Rates and Taxes).  
5. **Routing regex pattern:** `/(Staff Welfare Expenses)/i` → Row 68.  

**Actionable Summary:**  
- Add a specific rule for "Staff Welfare Expenses" to route to Row 68.  
- Use a regex pattern to directly map "Staff Welfare Expenses" to Row 68.
```

### 91. `Contribution to PF and ESI` (INPL)
- Correct: Row 68 (Rent , Rates and Taxes)
- Predicted: Row 45 (Wages)
- Correct in options: Yes
- Routed to: employee_cost
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 68 (Rent, Rates and Taxes) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 45 because the CA-VERIFIED DISAMBIGUATION RULES explicitly state: "Employee items (gratuity, EPF, ESI) → Row 45 (Wages) always." The item text "Contribution to PF and ESI" directly matches this rule, leading to Row 45.  
3. N/A (Row 68 was in the list, but the rules prioritized Row 45 for employee-related contributions.)  

**PART B — What would make you get it RIGHT:**  
4. The EXACT minimum change to the prompt would be to add a rule: "Contribution to PF and ESI → Row 68 (Rent, Rates and Taxes)." This would override the existing rule routing it to Row 45.  
5. A routing regex pattern: `/(Contribution to PF and ESI)/i → Row 68`. This would explicitly route the item to Row 68, bypassing the default employee-related rule.  

**Summary:** The error occurred because the
```

### 92. `Gratuity to Employees` (INPL)
- Correct: Row 68 (Rent , Rates and Taxes)
- Predicted: Row 45 (Wages)
- Correct in options: Yes
- Routed to: employee_cost
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 68 (Rent, Rates and Taxes) was in the POSSIBLE CMA ROWS list.  
2. Row 45 (Wages) was picked because the CA-VERIFIED DISAMBIGUATION RULES explicitly state: "Employee items (gratuity, EPF, ESI) → Row 45 (Wages) always." The item text "Gratuity to Employees" directly matched this rule.  
3. N/A (Row 68 was in the list).  

**PART B — What would make you get it RIGHT:**  
4. Add a CA-VERIFIED DISAMBIGUATION RULE: "Gratuity to Employees → Row 68 (Rent, Rates and Taxes) if in admin section." This would override the default routing to Row 45.  
5. Routing regex pattern:  
   `(Gratuity to Employees).*(note 25 - employee benefits expense) → Row 68`  
   This would explicitly route "Gratuity to Employees" in the specified section to Row 68.  

**Summary:** The error occurred due to a strict rule routing employee-related items
```

### 93. `Directors Remuneration` (INPL)
- Correct: Row 74 (Row 74)
- Predicted: Row 73 (Audit Fees & Directors Remuneration)
- Correct in options: NO
- Routed to: employee_cost
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. No, Row 74 was NOT in the POSSIBLE CMA ROWS list.  
2. N/A (Row 74 was not an option).  
3. The item text "Directors Remuneration" matched the CA-verified rule directing it to Row 73 (Audit Fees & Directors Remuneration), which was the closest available option.  

**PART B — What would make you get it RIGHT:**  
4. Add "Row 74 | II_D7b | Directors Remuneration" to the POSSIBLE CMA ROWS list.  
5. Routing regex pattern: `Directors Remuneration → Row 74`.  

This ensures the item is correctly classified when Row 74 is available.
```

### 94. `Interest on Unsecured Loan` (INPL)
- Correct: Row 84 (Interest on Working capital loans)
- Predicted: Row 83 (Interest on Fixed Loans / Term loans)
- Correct in options: Yes
- Routed to: borrowings_long, finance_cost
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 84 was in the POSSIBLE CMA ROWS list.  
2. I picked Row 83 because "Unsecured Loan" was interpreted as a fixed/term loan, not explicitly as a working capital loan.  
3. N/A (Row 84 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add a rule: "Unsecured Loan" → Row 84 (Interest on Working capital loans).  
5. Routing regex: `/(Interest on Unsecured Loan)/i → Row 84`.  

**Reasoning:**  
The classification error occurred due to ambiguity in interpreting "Unsecured Loan" as a fixed/term loan. A specific rule or regex pattern clarifying that "Unsecured Loan" maps to working capital loans would resolve this.
```

### 95. `Consultancy Charges` (INPL)
- Correct: Row 50 (Repairs & Maintenance)
- Predicted: Row 71 (Others)
- Correct in options: NO
- Routed to: admin_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. **No**, Row 50 was not in the POSSIBLE CMA ROWS list.  
2. N/A (Row 50 was not an option).  
3. The keywords "Consultancy Charges" did not match any specific row in the provided list, so it defaulted to Row 71 (Others) as per the rules.  

**PART B — What would make you get it RIGHT:**  
4. Add **Row 50 (Repairs & Maintenance)** to the POSSIBLE CMA ROWS list.  
5. Routing regex pattern:  
   `/(Consultancy Charges|Maintenance)/i`  
   This would ensure "Consultancy Charges" is routed to Row 50 if it’s available.  

**Summary:**  
Row 50 was missing from the options, and "Consultancy Charges" lacked matching keywords. Adding Row 50 and a regex pattern would fix this.
```

### 96. `Packing and Forwarding Charges` (INPL)
- Correct: Row 48 (Power, Coal, Fuel and Water)
- Predicted: Row 71 (Others)
- Correct in options: NO
- Routed to: admin_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. No, Row 48 was NOT in the POSSIBLE CMA ROWS list.  
2. N/A (Row 48 was not an option).  
3. Keywords like "Packing and Forwarding Charges" do not inherently suggest "Power, Coal, Fuel and Water." The correct routing likely depends on context or nature of the expense, which wasn’t clear from the text alone.  

**PART B — What would make you get it RIGHT:**  
4. Add Row 48 (Power, Coal, Fuel and Water) to the POSSIBLE CMA ROWS list and clarify that "Packing and Forwarding Charges" related to fuel or energy costs should be classified here.  
5. Routing regex: `/(Packing.*Forwarding.*Charges.*fuel|energy|power)/i`  

**Summary:**  
Row 48 wasn’t an option, and the item text lacked keywords to suggest it. Adding Row 48 and clarifying its applicability would fix this. A regex pattern could help route similar items correctly.
```

### 97. `Power and Fuel` (INPL)
- Correct: Row 49 (Others)
- Predicted: Row 48 (Power, Coal, Fuel and Water)
- Correct in options: Yes
- Routed to: manufacturing_expense, admin_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes, Row 49 (Others) was in the POSSIBLE CMA ROWS list.  
2. I picked Row 48 because "Power and Fuel" directly matched the keywords "Power, Coal, Fuel and Water" in Row 48, aligning with the rule to prefer specific rows over "Others."  
3. N/A (Row 49 was available).  

**PART B — What would make you get it RIGHT:**  
4. Add a disambiguation rule: "Power and Fuel" → Row 49 (Others Manufacturing) unless explicitly tied to factory operations.  
5. Routing regex: `/(Power|Fuel)/i` → Row 49 (Others Manufacturing) unless "factory" or "manufacturing" is explicitly mentioned.  

**Actionable Summary:**  
- Add a specific rule to clarify that "Power and Fuel" defaults to Row 49 unless explicitly linked to factory operations.  
- Use a regex pattern to route "Power and Fuel" to Row 49 unless context indicates factory usage.
```

### 98. `Transportation Charges` (INPL)
- Correct: Row 48 (Power, Coal, Fuel and Water)
- Predicted: Row 71 (Others)
- Correct in options: NO
- Routed to: admin_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. No, Row 48 was NOT in the POSSIBLE CMA ROWS list.  
2. N/A (Row 48 was not an option).  
3. Keywords like "Transportation Charges" could imply fuel or logistics costs, which align with Row 48 (Power, Coal, Fuel and Water).  

**PART B — What would make you get it RIGHT:**  
4. Add Row 48 (Power, Coal, Fuel and Water) to the POSSIBLE CMA ROWS list.  
5. Routing regex pattern: `/(transportation|fuel|coal|power|water)/i`.  

This ensures items related to transportation or fuel are correctly routed to Row 48.
```

### 99. `Insurance Paid` (INPL)
- Correct: Row 72 (Repairs & Maintenance)
- Predicted: Row 71 (Others)
- Correct in options: Yes
- Routed to: admin_expense
- Method: scoped_v3

**AI Response:**
```
### PART A — Why it went wrong:  
1. **Yes**, Row 72 was in the POSSIBLE CMA ROWS list.  
2. **Reason for picking Row 71 (Others):** The CA-EXPERT RULES explicitly state *"Insurance" → Row 71 (Others)*, overriding the section title ("other expenses"). The item text lacked keywords like "repairs" or "maintenance" to justify Row 72.  

### PART B — What would make you get it RIGHT:  
4. **Exact change to prompt:** Add *"Building Insurance"* or *"Equipment Insurance"* to the item text (e.g., *"Building Insurance Paid"*). This would trigger the CA-EXPERT RULE *"Building Maintenance (Others)" → Row 72*.  
5. **Routing regex pattern:**  
   ```regex
   /(repairs|maintenance|building|equipment)\s.*insurance/i  
   ```  
   This would route items explicitly tying insurance to assets under maintenance.  

### Key Takeaways:  
- **Current routing was technically correct** per the CA-EXPERT RULES for generic "Insurance".  
- **Specificity matters:**
```

### 100. `Office Expenses` (INPL)
- Correct: Row 72 (Repairs & Maintenance)
- Predicted: Row 71 (Others)
- Correct in options: Yes
- Routed to: admin_expense
- Method: scoped_v3

**AI Response:**
```
**PART A — Why it went wrong:**  
1. Yes  
2. Followed CA expert rule "Office Expenses" → Row 71 (Others) without considering possible repairs context in "other expenses" section.  
3. N/A  

**PART B — What would make you get it RIGHT:**  
4. Add disambiguation: *"Office Expenses under 'other expenses' section → Row 72 if maintenance-related."*  
5. Regex: `/office expenses/i && /other expenses/i && /maintain|repair/i → Row 72`  

(Words: 75)  

**Key Fixes:**  
- Override default "Office Expenses" rule when section hints at repairs.  
- Prioritize section context over generic keyword mapping.
```
