# GT Validation Final Summary

**Date:** 2026-03-27
**Methodology:** 3-pass validation (rapidfuzz threshold=80 -> agent CA reasoning -> cross-company consistency)
**Golden Rules:** 481 combined (398 from CMA Classification XLS + 69 CA answers + 14 CA-verified rules)

---

## Overall Summary

| Metric | Count | % |
|--------|-------|---|
| **Total unique entries** | 844 | 100% |
| **Confirmed** | 692 | 82.0% |
| **Disputes (from GT entries)** | 152 | 18.0% |
| **Truly Unverified** | 0 | 0.0% |
| **Excluded (row 0)** | 0 | 0.0% |
| **+ Cross-check disputes (Step 1)** | 22 | (addl) |
| **= Total disputes for CA review** | 174 | - |
| **Cross-company inconsistencies** | 88 | - |
| **Rule contradictions (golden vs golden)** | 14 | - |

### Match Method Breakdown

| Method | Confirmed | Dispute |
|--------|-----------|---------|
| Rapidfuzz | 174 | 111 |
| Agent Reasoning | 507 | 41 |
| Cross-check | - | 22 |

---

## Per-Company Breakdown

| Company | Industry | Total | Confirmed | Disputes | Unverified | Excluded |
|---------|----------|-------|-----------|----------|------------|----------|
| BCIPL | mfg | 107 | 86 | 21 | 0 | 0 |
| Dynamic_Air | mfg | 110 | 87 | 23 | 0 | 0 |
| INPL | mfg | 129 | 110 | 19 | 0 | 0 |
| Kurunji_Retail | trading | 49 | 39 | 10 | 0 | 0 |
| Mehta_Computer | trading | 71 | 47 | 15 | 9 | 0 |
| MSL | mfg | 152 | 129 | 23 | 0 | 0 |
| SLIPL | mfg | 101 | 85 | 16 | 0 | 0 |
| SR_Papers | mfg | 64 | 51 | 13 | 0 | 0 |
| SSSS | trading | 61 | 47 | 12 | 2 | 0 |

---

## Rule Contradictions (Golden Rules Disagreeing With Each Other)

Found **14 cross-source contradictions** and **21 internal contradictions**.

### Key Cross-Source Contradictions:
- **Staff Welfare Expenses** (manufacturing): CA says row 45 (Wages), Source 1 says row 67 (Salary and staff expenses)
- **Staff Welfare Expenses** (trading): CA says row 67 (Salary and staff expenses), Source 1 says row 45 (Wages)
- **Staff Welfare Expenses** (services): CA says row 67 (Salary and staff expenses), Source 1 says row 45 (Wages)
- **Bonus** (manufacturing): CA says row 45 (Wages), Source 1 says row 67 (Salary and staff expenses)
- **Miscellaneous Expenses** (all): CA says row 71 (Others (Admin & Selling)), Source 1 says row 170 (Misc Expenditure (to the extent not w/o))
- **Miscellaneous Expenses** (all): CA says row 71 (Others (Admin & Selling)), Source 1 says row 238 (Other non current assets)
- **Miscellaneous Expenses** (all): CA says row 71 (Others (Admin & Selling)), Source 1 says row 34 (Others)
- **Selling & Distribution Expenses** (all): CA says row 70 (Advertisements and Sales Promotions), Source 1 says row 71 (Others)
- **Carriage Inward / Freight Inward** (all): CA says row 47 (Freight and Transportation Charges), Source 1 says row 41 (Raw Materials Consumed ( Imported))
- **Water Charges** (all): CA says row 48 (Power, Coal, Fuel and Water), Source 1 says row 49 (Others)

### Incomplete Rules (CA has industry split, Source 1 doesn't):
- **Staff Welfare Expenses**: Rule gives single row 67, CA splits by industry: {'manufacturing': 45, 'trading': 67, 'services': 67, 'construction': 45}
- **Staff Welfare Expenses**: Rule gives single row 45, CA splits by industry: {'manufacturing': 45, 'trading': 67, 'services': 67, 'construction': 45}
- **Bonus**: Rule gives single row 67, CA splits by industry: {'manufacturing': 45, 'trading': 67, 'services': 67, 'construction': 45}

---

## Top 20 Most Common Disputes

1. **"prepaid expenses"** (x7 across INPL, SLIPL, BCIPL, MSL)
   - GT: row 222 (Prepaid Expenses) vs Golden: row 223 (Other Advances / current asset)
   - Reasoning: Source1_rule_127

2. **"rent"** (x4 across SLIPL, Kurunji_Retail, BCIPL, MSL)
   - GT: row 49 (Others) vs Golden: row 68 (Rent , Rates and Taxes)
   - Reasoning: Rent generally maps to row 68. GT has 49 (Others Mfg) - could be factory rent. | DISPUTE: Golden rule says row 68 but GT

3. **"deferred tax"** (x4 across INPL, SLIPL, SR_Papers, BCIPL)
   - GT: row 100 (Deferred Tax Liability) vs Golden: row 171 (Deferred Tax Asset)
   - Reasoning: Source1_rule_131

4. **"creditors for expenses"** (x3 across INPL, BCIPL, MSL)
   - GT: row 249 (Creditors for Expenses) vs Golden: row 250 (Other current liabilities)
   - Reasoning: Source1_rule_70

5. **"rates and taxes"** (x3 across SR_Papers, Dynamic_Air)
   - GT: row 68 (Rent , Rates and Taxes) vs Golden: row 49 (Others)
   - Reasoning: Source1_rule_195

6. **"consultancy charges"** (x3 across INPL)
   - GT: row 71 (Others) vs Golden: row 49 (Others)
   - Reasoning: Location A (GT) says row 71, Location B says row 49 for FY 2023

7. **"manpower charges"** (x3 across SR_Papers)
   - GT: row 49 (Others) vs Golden: row 45 (Wages)
   - Reasoning: Location A (GT) says row 49, Location B says row 45 for FY 2023

8. **"rates & taxes"** (x2 across INPL, BCIPL)
   - GT: row 68 (Rent , Rates and Taxes) vs Golden: row 49 (Others)
   - Reasoning: Source1_rule_195

9. **"security service charges"** (x2 across INPL, Dynamic_Air)
   - GT: row 51 (Security Service Charges) vs Golden: row 71 (Others)
   - Reasoning: Source1_rule_264

10. **"advances recoverable in cash or in kind"** (x2 across MSL, Dynamic_Air)
   - GT: row 219 (Advances recoverable in cash or in kind) vs Golden: row 223 (Other Advances / current asset)
   - Reasoning: Source1_rule_130

11. **"staff welfare expenses"** (x2 across INPL)
   - GT: row 45 (Wages) vs Golden: row 67 (Salary and staff expenses)
   - Reasoning: Location A (GT) says row 45, Location B says row 67 for FY 2024

12. **"gratuity to employees"** (x2 across INPL)
   - GT: row 45 (Wages) vs Golden: row 67 (Salary and staff expenses)
   - Reasoning: Location A (GT) says row 45, Location B says row 67 for FY 2024

13. **"computer maintanance"** (x2 across SR_Papers)
   - GT: row 72 (Repairs & Maintenance) vs Golden: row 71 (Others)
   - Reasoning: Location A (GT) says row 72, Location B says row 71 for FY 2023

14. **"profit on sale of fixed asset"** (x1 across BCIPL)
   - GT: row 23 (Exports) vs Golden: row 31 (Profit on sale of fixed assets / Investments)
   - Reasoning: Source1_rule_355

15. **"forex rate fluctuation gain/(loss)"** (x1 across BCIPL)
   - GT: row 32 (Gain on Exchange Fluctuations) vs Golden: row 91 (Loss on Exchange Fluctuations)
   - Reasoning: CA_Q10c_CA_agreed

16. **"machinery maintenance"** (x1 across BCIPL)
   - GT: row 50 (Repairs & Maintenance) vs Golden: row 49 (Others)
   - Reasoning: Source1_rule_170

17. **"directors remuneration"** (x1 across BCIPL)
   - GT: row 67 (Salary and staff expenses) vs Golden: row 73 (Audit Fees & Directors Remuneration)
   - Reasoning: Source1_rule_231

18. **"selling & distribution expenses"** (x1 across BCIPL)
   - GT: row 70 (Advertisements and Sales Promotions) vs Golden: row 71 (Others)
   - Reasoning: Source1_rule_302

19. **"administrative & general expenses"** (x1 across BCIPL)
   - GT: row 70 (Advertisements and Sales Promotions) vs Golden: row 71 (Others)
   - Reasoning: CA_Q3c_CA_agreed

20. **"rates & taxes"** (x1 across BCIPL)
   - GT: row 71 (Others) vs Golden: row 49 (Others)
   - Reasoning: Source1_rule_195

---

## Cross-Company Inconsistencies

Found **88** cases where the same text + industry has different GT rows across companies.

### "sales" (manufacturing)
Rows found: [22, 23]
- BCIPL: row 23 (section: Sale of Manufactured Goods)
- Dynamic_Air: row 22 (section: Revenue from Operations)
- MSL: row 23 (section: Revenue from Operations)

### "income" (manufacturing)
Rows found: [30, 34]
- BCIPL: row 30 (section: Other Income)
- Dynamic_Air: row 34 (section: Other Income)
- SLIPL: row 30 (section: Other Income)
- SLIPL: row 34 (section: Other Income)
- SR_Papers: row 30 (section: Other Income)

### "materials consumed" (manufacturing)
Rows found: [42, 44]
- BCIPL: row 42 (section: Expenditure)
- BCIPL: row 44 (section: Expenditure)
- MSL: row 42 (section: manufacturing_expenses)

### "expenses" (manufacturing)
Rows found: [49, 70, 71, 222, 249]
- BCIPL: row 49 (section: Other Expenses)
- BCIPL: row 71 (section: Other Expenses)
- BCIPL: row 222 (section: Short-term Loans and Advances)
- Dynamic_Air: row 71 (section: Other Expenses - Admin)
- Dynamic_Air: row 71 (section: Other Expenses - Admin)
- Dynamic_Air: row 70 (section: Other Expenses - Selling)
- Dynamic_Air: row 71 (section: Other Expenses - Admin)
- Dynamic_Air: row 249 (section: Other Current Liabilities)
- INPL: row 71 (section: Other Expenses)
- INPL: row 71 (section: Other Expenses)
- INPL: row 71 (section: Other Expenses)
- INPL: row 222 (section: Other Current Asset)
- INPL: row 222 (section: Other Current Asset)
- INPL: row 222 (section: Other Current Assets)
- MSL: row 71 (section: Other Expenses - Admin)
- MSL: row 71 (section: Other Expenses - Admin)
- MSL: row 222 (section: Other Current Assets)
- MSL: row 222 (section: loans_advances)
- SLIPL: row 49 (section: Other Expenses)
- SLIPL: row 71 (section: Other Expenses - Administration & Other Expenses)
- SLIPL: row 71 (section: Other Expenses - Administration & Other Expenses)
- SLIPL: row 222 (section: Other Current Assets)

### "rent" (manufacturing)
Rows found: [49, 68, 71]
- BCIPL: row 49 (section: Other Expenses)
- BCIPL: row 68 (section: Other Expenses)
- BCIPL: row 71 (section: Other Expenses)
- MSL: row 49 (section: Other Expenses)
- MSL: row 68 (section: Other Expenses)
- SLIPL: row 49 (section: Other Expenses)

### "maintenance" (manufacturing)
Rows found: [50, 72]
- BCIPL: row 50 (section: Other Expenses)
- BCIPL: row 72 (section: Other Expenses)

### "and amortization expenses" (manufacturing)
Rows found: [56, 63]
- BCIPL: row 56 (section: Expenditure)
- BCIPL: row 63 (section: Expenditure)
- INPL: row 56 (section: Expenses)

### "goods" (manufacturing)
Rows found: [58, 59, 201]
- BCIPL: row 58 (section: Changes in Inventories)
- BCIPL: row 59 (section: Changes in Inventories)
- BCIPL: row 201 (section: Inventories)
- Dynamic_Air: row 201 (section: Inventories)
- INPL: row 59 (section: Inventories)
- INPL: row 58 (section: Changes in Inventories)
- INPL: row 201 (section: Inventories)
- MSL: row 201 (section: inventories)
- SLIPL: row 201 (section: Inventories)

### "remuneration" (manufacturing)
Rows found: [67, 73]
- BCIPL: row 67 (section: Salaries & Wages)
- BCIPL: row 73 (section: Other Expenses)
- Dynamic_Air: row 73 (section: Employee Benefits Expense)
- Dynamic_Air: row 73 (section: Employee Benefits Expense)
- INPL: row 73 (section: Employee Benefits Expenses)
- INPL: row 73 (section: Other Expenses)
- SR_Papers: row 73 (section: Employee Benefit Expense)

### "& taxes" (manufacturing)
Rows found: [68, 71]
- BCIPL: row 68 (section: Other Expenses)
- BCIPL: row 71 (section: Other Expenses)
- INPL: row 68 (section: Other Expenses)

### "debts written off" (manufacturing)
Rows found: [69, 71, 90]
- BCIPL: row 69 (section: Other Expenses)
- BCIPL: row 71 (section: Other Expenses)
- SLIPL: row 69 (section: Other Expenses - Administration & Other Expenses)
- SLIPL: row 90 (section: Other Expenses - Administration & Other Expenses)

### "& distribution expenses" (manufacturing)
Rows found: [70, 73]
- BCIPL: row 70 (section: Other Expenses)
- BCIPL: row 73 (section: Other Expenses)

### "& general expenses" (manufacturing)
Rows found: [70, 71]
- BCIPL: row 70 (section: Other Expenses)
- BCIPL: row 71 (section: Other Expenses)

### "fees" (manufacturing)
Rows found: [71, 73]
- BCIPL: row 71 (section: Other Expenses)
- MSL: row 73 (section: Other Expenses - Auditors)
- SLIPL: row 73 (section: Other Expenses - Payment to Auditors)
- SR_Papers: row 73 (section: Other Expenses)

### "written off" (manufacturing)
Rows found: [71, 75, 90]
- BCIPL: row 71 (section: Other Expenses)
- BCIPL: row 75 (section: Other Expenses)
- MSL: row 90 (section: Other Expenses - Admin)

### "charges" (manufacturing)
Rows found: [22, 34, 45, 46, 47, 49, 71, 83, 84, 85]
- BCIPL: row 85 (section: Other Expenses)
- BCIPL: row 85 (section: Finance Costs)
- Dynamic_Air: row 22 (section: Revenue from Operations)
- Dynamic_Air: row 85 (section: Other Expenses - Admin)
- INPL: row 47 (section: Other Expenses)
- INPL: row 47 (section: Other Expenses)
- INPL: row 47 (section: Other Expenses)
- INPL: row 49 (section: Other Expenses)
- INPL: row 71 (section: Other Expenses)
- INPL: row 85 (section: Finance cost)
- INPL: row 85 (section: Finance cost)
- INPL: row 85 (section: Finance Cost)
- MSL: row 45 (section: Other Expenses)
- MSL: row 71 (section: Other Expenses - Admin)
- MSL: row 71 (section: Other Expenses - Admin)
- MSL: row 84 (section: Finance Costs)
- MSL: row 85 (section: Finance Costs)
- MSL: row 83 (section: Finance Costs)
- MSL: row 85 (section: finance_charges)
- SLIPL: row 34 (section: Other Income)
- SLIPL: row 46 (section: Other Expenses)
- SLIPL: row 85 (section: Finance Costs)
- SLIPL: row 85 (section: Other Expenses - Administration & Other Expenses)
- SR_Papers: row 47 (section: Other Expenses)
- SR_Papers: row 49 (section: Other Expenses)
- SR_Papers: row 49 (section: Other Expenses)
- SR_Papers: row 85 (section: Other Expenses)

### "tax" (manufacturing)
Rows found: [99, 100, 101, 221]
- BCIPL: row 99 (section: Tax Expense)
- BCIPL: row 100 (section: Tax Expense)
- BCIPL: row 101 (section: Tax Expense)
- BCIPL: row 221 (section: Short-term Loans and Advances)
- Dynamic_Air: row 99 (section: Tax Expense)
- INPL: row 99 (section: Tax Expense)
- INPL: row 100 (section: Tax Expense)
- INPL: row 101 (section: Tax Expense)
- MSL: row 99 (section: Tax Expense)
- MSL: row 100 (section: Tax Expense)
- SLIPL: row 100 (section: Tax expense)
- SLIPL: row 101 (section: Tax expense)
- SR_Papers: row 99 (section: Provision for taxation)
- SR_Papers: row 100 (section: Provision for taxation)

### "borrowings" (manufacturing)
Rows found: [131, 137]
- BCIPL: row 131 (section: Current Liabilities)
- BCIPL: row 137 (section: Non-Current Liabilities)

### "capital" (manufacturing)
Rows found: [116, 132]
- BCIPL: row 132 (section: Short-term Borrowings)
- SLIPL: row 116 (section: Shareholders' Funds)
- SR_Papers: row 116 (section: Equity)

### "depreciation" (manufacturing)
Rows found: [56, 163]
- BCIPL: row 163 (section: Depreciation Schedule)
- Dynamic_Air: row 163 (section: Fixed Assets)
- MSL: row 56 (section: manufacturing_expenses)
- SR_Papers: row 163 (section: Fixed Assets)

... and 68 more inconsistencies.

---

## Truly Unverified Items

Found **11** items with no golden rule match.

- [Mehta_Computer] "Packing Forwarding " (gt_row=49, section=Direct Expenses)
- [Mehta_Computer] " - From Parties" (gt_row=152, section=Unsecured Loans)
- [Mehta_Computer] " FIXED ASSETS (At book value)" (gt_row=162, section=Assets)
- [Mehta_Computer] " Bank Balance" (gt_row=213, section=Cash & Bank Balances)
- [Mehta_Computer] " - For Purchases" (gt_row=242, section=Current Liabilities - Sundry Creditors)
- [Mehta_Computer] " - For Duties & Taxes" (gt_row=246, section=Current Liabilities - Sundry Creditors)
- [Mehta_Computer] " - For TDS Payable" (gt_row=246, section=Current Liabilities - Sundry Creditors)
- [Mehta_Computer] " - For Expense Payable" (gt_row=249, section=Current Liabilities - Sundry Creditors)
- [Mehta_Computer] "FA Schedule — Additions (Mobile VIVO Y21)" (gt_row=175, section=Fixed Asset Additions)
- [SSSS] "TOTAL — GROSS BLOCK as at 31.03.2025" (gt_row=162, section=Property, Plant and Equipments — Gross Block)
- [SSSS] "TOTAL — DEPRECIATION Upto 31.03.2025" (gt_row=163, section=Property, Plant and Equipments — Depreciation)

---

## All Disputes Detail (174 total)

**1. [BCIPL] "Profit on Sale of Fixed Asset"**
   GT: row 23 (Exports)
   Golden: row 31 (Profit on sale of fixed assets / Investments)
   Source: Source1_rule_355 | Method: rapidfuzz

**2. [BCIPL] "Forex Rate Fluctuation Gain/(Loss)"**
   GT: row 32 (Gain on Exchange Fluctuations)
   Golden: row 91 (Loss on Exchange Fluctuations)
   Source: CA_Q10c_CA_agreed | Method: rapidfuzz

**3. [BCIPL] "Rent"**
   GT: row 49 (Others)
   Golden: row 68 (Rent, Rates and Taxes)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Rent generally maps to row 68. GT has 49 (Others Mfg) - could be factory rent. | DISPUTE: Golden rule says row 68 but GT has row 49.

**4. [BCIPL] "Machinery Maintenance"**
   GT: row 50 (Repairs & Maintenance)
   Golden: row 49 (Others)
   Source: Source1_rule_170 | Method: rapidfuzz

**5. [BCIPL] "Directors Remuneration"**
   GT: row 67 (Salary and staff expenses)
   Golden: row 73 (Audit Fees & Directors Remuneration)
   Source: Source1_rule_231 | Method: rapidfuzz

**6. [BCIPL] "Rates & Taxes"**
   GT: row 68 (Rent , Rates and Taxes)
   Golden: row 49 (Others)
   Source: Source1_rule_195 | Method: rapidfuzz

**7. [BCIPL] "Selling & Distribution Expenses"**
   GT: row 70 (Advertisements and Sales Promotions)
   Golden: row 71 (Others)
   Source: Source1_rule_302 | Method: rapidfuzz

**8. [BCIPL] "Administrative & General Expenses"**
   GT: row 70 (Advertisements and Sales Promotions)
   Golden: row 71 (Others (Admin & Selling))
   Source: CA_Q3c_CA_agreed | Method: rapidfuzz

**9. [BCIPL] "Rates & Taxes"**
   GT: row 71 (Others)
   Golden: row 49 (Others)
   Source: Source1_rule_195 | Method: rapidfuzz

**10. [BCIPL] "Bad debts written off"**
   GT: row 71 (Others)
   Golden: row 69 (Bad Debts)
   Source: CA_Q27_CA_agreed | Method: rapidfuzz

**11. [BCIPL] "Auditor's Remuneration - Statutory Audit"**
   GT: row 71 (Others)
   Golden: row 73 (Audit Fees & Directors Remuneration)
   Source: CA_Q21b_CA_agreed | Method: rapidfuzz

**12. [BCIPL] "Auditor's Remuneration - Tax Audit"**
   GT: row 71 (Others)
   Golden: row 73 (Audit Fees & Directors Remuneration)
   Source: CA_Q21c_CA_agreed | Method: rapidfuzz

**13. [BCIPL] "Rent"**
   GT: row 71 (Others)
   Golden: row 68 (Rent, Rates and Taxes)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Rent generally maps to row 68. GT has 71 (Others Admin). | DISPUTE: Golden rule says row 68 but GT has row 71.

**14. [BCIPL] "Machinery Maintenance"**
   GT: row 72 (Repairs & Maintenance)
   Golden: row 49 (Others)
   Source: Source1_rule_170 | Method: rapidfuzz

**15. [BCIPL] "Selling & Distribution Expenses"**
   GT: row 73 (Audit Fees & Directors Remuneration)
   Golden: row 71 (Others)
   Source: Source1_rule_302 | Method: rapidfuzz

**16. [BCIPL] "Interest of Income Tax"**
   GT: row 83 (Interest on Fixed Loans / Term loans)
   Golden: row 84 (Interest on WC / Tax Delay)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Interest on Income Tax delay maps to row 84 per CA rules | DISPUTE: Golden rule says row 84 but GT has row 83.

**17. [BCIPL] "Deferred Tax"**
   GT: row 100 (Deferred Tax Liability)
   Golden: row 171 (Deferred Tax Asset)
   Source: Source1_rule_131 | Method: rapidfuzz

**18. [BCIPL] "Deferred Tax"**
   GT: row 101 (Deferred Tax Asset)
   Golden: row 171 (Deferred Tax Asset)
   Source: Source1_rule_131 | Method: rapidfuzz

**19. [BCIPL] "Prepaid Expenses"**
   GT: row 222 (Prepaid Expenses)
   Golden: row 223 (Other Advances / current asset)
   Source: Source1_rule_127 | Method: rapidfuzz

**20. [BCIPL] "Leave Encashment"**
   GT: row 244 (Provision for Taxation)
   Golden: row 249 (Creditors for Expenses)
   Source: CA_Q1f_bs | Method: rapidfuzz

**21. [BCIPL] "Creditors for Expenses"**
   GT: row 249 (Creditors for Expenses)
   Golden: row 250 (Other current liabilities)
   Source: Source1_rule_70 | Method: rapidfuzz

**22. [Dynamic_Air] "Carriage Inwards"**
   GT: row 47 (Freight and Transportation Charges)
   Golden: row 70 (Advertisements and Sales Promotions)
   Source: CA_Q3d_CA_agreed | Method: rapidfuzz

**23. [Dynamic_Air] "(a) Salaries and incentives"**
   GT: row 67 (Salary and staff expenses)
   Golden: row 45 (Wages (Manufacturing - Salaries))
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Salaries and incentives for manufacturing maps to row 45 per CA rules | DISPUTE: Golden rule says row 45 but GT has row 67.

**24. [Dynamic_Air] "(c) Staff Welfare"**
   GT: row 67 (Salary and staff expenses)
   Golden: row 45 (Wages (Manufacturing - Staff Welfare))
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Staff Welfare for manufacturing maps to row 45 per CA rules | DISPUTE: Golden rule says row 45 but GT has row 67.

**25. [Dynamic_Air] "(d) Contribution to EPF and ESI"**
   GT: row 67 (Salary and staff expenses)
   Golden: row 45 (Wages)
   Source: CA_Q1c_CA_disagreed_use_default | Method: rapidfuzz

**26. [Dynamic_Air] "Rates and taxes"**
   GT: row 68 (Rent , Rates and Taxes)
   Golden: row 49 (Others)
   Source: Source1_rule_195 | Method: rapidfuzz

**27. [Dynamic_Air] "Interest on Delay in payment of taxes"**
   GT: row 83 (Interest on Fixed Loans / Term loans)
   Golden: row 84 (Interest on Working capital loans)
   Source: CA_Q10b_CA_disagreed_use_default | Method: rapidfuzz

**28. [Dynamic_Air] "Liquidty Damages"**
   GT: row 83 (Interest on Fixed Loans / Term loans)
   Golden: row 71 (Others (Admin))
   Source: Source1_rule_CA_R04 | Method: rapidfuzz

**29. [Dynamic_Air] "(a) Loan/Overdraft Processing Fee"**
   GT: row 84 (Interest on Working capital loans)
   Golden: row 85 (Bank Charges)
   Source: CA_Q10g_CA_disagreed_use_default | Method: rapidfuzz

**30. [Dynamic_Air] "(3) Deferred tax Liability / (Asset)"**
   GT: row 101 (Deferred Tax Asset)
   Golden: row 159 (Deferred tax liability)
   Source: Source1_rule_34 | Method: rapidfuzz

**31. [Dynamic_Air] "(e) Gratuity"**
   GT: row 67 (Salary and staff expenses)
   Golden: row 45 (Wages)
   Source: Source1_rule_CA_R02 | Method: rapidfuzz

**32. [Dynamic_Air] "Rent - Factory"**
   GT: row 68 (Rent , Rates and Taxes)
   Golden: row 49 (Others)
   Source: Source1_rule_193 | Method: rapidfuzz

**33. [Dynamic_Air] "Rates and taxes"**
   GT: row 68 (Rent , Rates and Taxes)
   Golden: row 49 (Others)
   Source: Source1_rule_195 | Method: rapidfuzz

**34. [Dynamic_Air] "Brokerage & Commission"**
   GT: row 71 (Others)
   Golden: row 70 (Advertisements and Sales Promotions)
   Source: CA_Q3e_CA_agreed | Method: rapidfuzz

**35. [Dynamic_Air] "Interest on Delay in payment of taxes"**
   GT: row 71 (Others)
   Golden: row 84 (Interest on Working capital loans)
   Source: CA_Q10b_CA_disagreed_use_default | Method: rapidfuzz

**36. [Dynamic_Air] "(a) Loan/Overdraft Processing Fee"**
   GT: row 83 (Interest on Fixed Loans / Term loans)
   Golden: row 85 (Bank Charges)
   Source: CA_Q10g_CA_disagreed_use_default | Method: rapidfuzz

**37. [Dynamic_Air] "(3) Deferred tax Liability / (Asset)"**
   GT: row 100 (Deferred Tax Liability)
   Golden: row 159 (Deferred tax liability)
   Source: Source1_rule_34 | Method: rapidfuzz

**38. [Dynamic_Air] "Security Service Charges"**
   GT: row 51 (Security Service Charges)
   Golden: row 71 (Others)
   Source: Source1_rule_264 | Method: rapidfuzz

**39. [Dynamic_Air] "(c) Staff Welfare Expenses"**
   GT: row 67 (Salary and staff expenses)
   Golden: row 45 (Wages)
   Source: CA_Q1a_manufacturing | Method: rapidfuzz

**40. [Dynamic_Air] "Interest due to Delay in payment of taxes"**
   GT: row 71 (Others)
   Golden: row 84 (Interest on Working capital loans)
   Source: CA_Q10b_CA_disagreed_use_default | Method: rapidfuzz

**41. [Dynamic_Air] "Advances recoverable in cash or in kind"**
   GT: row 219 (Advances recoverable in cash or in kind)
   Golden: row 223 (Other Advances / current asset)
   Source: Source1_rule_130 | Method: rapidfuzz

**42. [Dynamic_Air] "Vehicle HP Loans - current maturities"**
   GT: row 140 (Repayable in next one year)
   Golden: row 148 (Repayable in next one year)
   Source: Source1_rule_CA_R08 | Method: rapidfuzz

**43. [Dynamic_Air] "Vehicle HP Loans - non-current"**
   GT: row 141 (Balance Repayable after one year)
   Golden: row 148 (Other Debts (Vehicle HP))
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Vehicle HP Loans non-current maps to row 148 (Other Debts). GT has 141 (Debentures). | DISPUTE: Golden rule says row 148 but GT has row 141.

**44. [Dynamic_Air] "Outstanding expenses (Salary + Other)"**
   GT: row 249 (Creditors for Expenses)
   Golden: row 250 (Other current liabilities)
   Source: Source1_rule_73 | Method: rapidfuzz

**45. [INPL] "Discount received"**
   GT: row 34 (Others)
   Golden: row 42 (Raw Materials Consumed ( Indigenous))
   Source: Source1_rule_363 | Method: rapidfuzz

**46. [INPL] "Changes in work-in-progress and stock-in-trade"**
   GT: row 42 (Raw Materials Consumed ( Indigenous))
   Golden: row None (None)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Changes in WIP/stock-in-trade is a NET change, not raw materials. Should be split into Opening/Closing rows (53/54). GT maps to 42 which seems incorrect.

**47. [INPL] "Security Service Charges"**
   GT: row 51 (Security Service Charges)
   Golden: row 71 (Others)
   Source: Source1_rule_264 | Method: rapidfuzz

**48. [INPL] "Work in Progress"**
   GT: row 54 (Stock in process Closing Balance)
   Golden: row 165 (Add : Capital Work in Progress)
   Source: Source1_rule_92 | Method: rapidfuzz

**49. [INPL] "Work in Progress (Opening)"**
   GT: row 53 (Stock in process Opening Balance)
   Golden: row 165 (Add : Capital Work in Progress)
   Source: Source1_rule_92 | Method: rapidfuzz

**50. [INPL] "Salary, Wages and Bonus"**
   GT: row 67 (Salary and staff expenses)
   Golden: row 45 (Wages (Manufacturing))
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: 'Salary, Wages and Bonus' for manufacturing maps to row 45 per CA rules (Salary/Wages/Bonus combined) | DISPUTE: Golden rule says row 45 but GT has row 67.

**51. [INPL] "Staff welfare Expenses"**
   GT: row 67 (Salary and staff expenses)
   Golden: row 45 (Wages)
   Source: CA_Q1a_manufacturing | Method: rapidfuzz

**52. [INPL] "Contribution to Provident Fund and ESI"**
   GT: row 67 (Salary and staff expenses)
   Golden: row 45 (Wages (Manufacturing - EPF/ESI))
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: EPF/ESI contribution for manufacturing maps to row 45 per CA rules | DISPUTE: Golden rule says row 45 but GT has row 67.

**53. [INPL] "Gratutity to employees"**
   GT: row 67 (Salary and staff expenses)
   Golden: row 45 (Wages)
   Source: CA_Q1b_CA_disagreed_use_default | Method: rapidfuzz

**54. [INPL] "Rates & Taxes"**
   GT: row 68 (Rent , Rates and Taxes)
   Golden: row 49 (Others)
   Source: Source1_rule_195 | Method: rapidfuzz

**55. [INPL] "Licence And Subscription"**
   GT: row 68 (Rent , Rates and Taxes)
   Golden: row 71 (Others (Admin))
   Source: Source1_rule_CA_R06 | Method: rapidfuzz

**56. [INPL] "Deferred Tax"**
   GT: row 100 (Deferred Tax Liability)
   Golden: row 171 (Deferred Tax Asset)
   Source: Source1_rule_131 | Method: rapidfuzz

**57. [INPL] "Deferred Tax (Asset)"**
   GT: row 101 (Deferred Tax Asset)
   Golden: row 171 (Deferred Tax Asset)
   Source: Source1_rule_131 | Method: rapidfuzz

**58. [INPL] "Work in Progress"**
   GT: row 200 (Stocks-in-process)
   Golden: row 165 (Add : Capital Work in Progress)
   Source: Source1_rule_92 | Method: rapidfuzz

**59. [INPL] "Finished Goods + Stock in Trade"**
   GT: row 201 (Finished Goods)
   Golden: row 58 (Finished Goods Opening Balance)
   Source: Source1_rule_CA_R10 | Method: rapidfuzz

**60. [INPL] "Prepaid expenses"**
   GT: row 222 (Prepaid Expenses)
   Golden: row 223 (Other Advances / current asset)
   Source: Source1_rule_127 | Method: rapidfuzz

**61. [INPL] "Prepaid Expenses"**
   GT: row 222 (Prepaid Expenses)
   Golden: row 223 (Other Advances / current asset)
   Source: Source1_rule_127 | Method: rapidfuzz

**62. [INPL] "Prepaid Expenses"**
   GT: row 222 (Prepaid Expenses)
   Golden: row 223 (Other Advances / current asset)
   Source: Source1_rule_127 | Method: rapidfuzz

**63. [INPL] "Creditors for Expenses"**
   GT: row 249 (Creditors for Expenses)
   Golden: row 250 (Other current liabilities)
   Source: Source1_rule_70 | Method: rapidfuzz

**64. [Kurunji_Retail] "Packing Expenses"**
   GT: row 44 (Stores and spares consumed ( Indigenous))
   Golden: row 70 (Advertisements and Sales Promotions)
   Source: Source1_rule_301 | Method: rapidfuzz

**65. [Kurunji_Retail] "Staff Welfare"**
   GT: row 45 (Wages)
   Golden: row 67 (Salary/Staff)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Trading rule: Staff Welfare->67 [DISPUTE golden=67 vs GT=45]

**66. [Kurunji_Retail] "Electric Charges"**
   GT: row 48 (Power, Coal, Fuel and Water)
   Golden: row 71 (Others Admin)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Trading rule: Electric->71 not 48 [DISPUTE golden=71 vs GT=48]

**67. [Kurunji_Retail] "Rent"**
   GT: row 49 (Others)
   Golden: row 68 (Rent/Rates/Taxes)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Rent->68 [DISPUTE golden=68 vs GT=49]

**68. [Kurunji_Retail] "Tds on Rent"**
   GT: row 49 (Others)
   Golden: row 68 (Rent/Rates/Taxes)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: TDS on Rent is rent compliance->68 [DISPUTE golden=68 vs GT=49]

**69. [Kurunji_Retail] "Rent - Parking"**
   GT: row 49 (Others)
   Golden: row 68 (Rent/Rates/Taxes)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Rent Parking->68 [DISPUTE golden=68 vs GT=49]

**70. [Kurunji_Retail] "Generator Expenses"**
   GT: row 71 (Others)
   Golden: row 49 (Others)
   Source: Source1_rule_244 | Method: rapidfuzz

**71. [Kurunji_Retail] "Delivery Charges"**
   GT: row 71 (Others)
   Golden: row 22 (Domestic)
   Source: Source1_rule_359 | Method: rapidfuzz

**72. [Kurunji_Retail] "Salary to Partners"**
   GT: row 73 (Audit Fees & Directors Remuneration)
   Golden: row 67 (Salary and staff expenses)
   Source: Source1_rule_232 | Method: rapidfuzz

**73. [Kurunji_Retail] "Partners Current Account"**
   GT: row 152 (As Quasi Equity)
   Golden: row 116 (Issued, Subscribed and Paid up)
   Source: Source1_rule_10 | Method: rapidfuzz

**74. [Mehta_Computer] "Bank Interest"**
   GT: row 30 (Interest Received)
   Golden: row 83 (Interest on Fixed Loans / Term loans)
   Source: Source1_rule_234 | Method: rapidfuzz

**75. [Mehta_Computer] "Interest on PPF"**
   GT: row 34 (Others)
   Golden: row 30 (Interest Received)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Interest on deposits/PPF->30 [DISPUTE golden=30 vs GT=34]

**76. [Mehta_Computer] "Electricty Charges"**
   GT: row 48 (Power, Coal, Fuel and Water)
   Golden: row 71 (Others)
   Source: Source1_rule_264 | Method: rapidfuzz

**77. [Mehta_Computer] "Courier Charges"**
   GT: row 49 (Others)
   Golden: row 71 (Others)
   Source: Source1_rule_186 | Method: rapidfuzz

**78. [Mehta_Computer] "Transport Charges"**
   GT: row 49 (Others)
   Golden: row 47 (Freight/Transport)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Transport/Freight in direct expenses->47 [DISPUTE golden=47 vs GT=49]

**79. [Mehta_Computer] "To Opening Stock"**
   GT: row 53 (Stock in process Opening Balance)
   Golden: row 58 (FG Opening)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Opening Stock P&L->58 (standard CMA: FG Opening; GT may use 53 SIP for trading cos) [DISPUTE golden=58 vs GT=53]

**80. [Mehta_Computer] "By Closing Stock"**
   GT: row 54 (Stock in process Closing Balance)
   Golden: row 59 (FG Closing)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Closing Stock P&L->59 (standard CMA: FG Closing; GT may use 54 SIP for trading cos) [DISPUTE golden=59 vs GT=54]

**81. [Mehta_Computer] "Carriage Outward"**
   GT: row 71 (Others)
   Golden: row 70 (Advertisements and Sales Promotions)
   Source: CA_Q3d_CA_agreed | Method: rapidfuzz

**82. [Mehta_Computer] "Commission on sales"**
   GT: row 71 (Others)
   Golden: row 70 (Ads/Sales(Commission))
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: CA rule: Commission->70 [DISPUTE golden=70 vs GT=71]

**83. [Mehta_Computer] "Sundry Balance W/off"**
   GT: row 71 (Others)
   Golden: row 90 (Sundry Written off)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Sundry Balance W/off->90 [DISPUTE golden=90 vs GT=71]

**84. [Mehta_Computer] "Freight Charges"**
   GT: row 71 (Others)
   Golden: row 47 (Freight/Transport)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Freight in admin (trading): CA default Freight->47; could be 70 if outward or 71 if admin misc [DISPUTE golden=47 vs GT=71]

**85. [Mehta_Computer] "Bill Discount Charges"**
   GT: row 85 (Bank Charges)
   Golden: row 84 (Interest on Working capital loans)
   Source: CA_Q10e_CA_disagreed_use_default | Method: rapidfuzz

**86. [Mehta_Computer] "Stock-in-Trade ( Valued at Cost Or Market price Whichever Is Lower)"**
   GT: row 200 (Stocks-in-process)
   Golden: row 201 (Finished Goods)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Stock-in-Trade (BS)->201 [DISPUTE golden=201 vs GT=200]

**87. [Mehta_Computer] "Gst Receivable"**
   GT: row 219 (Advances recoverable in cash or in kind)
   Golden: row 206 (Domestic Receivables ( including bills purchased and discounted))
   Source: Source1_rule_109 | Method: rapidfuzz

**88. [Mehta_Computer] "FD Accrued Interest (reclassified from Investments to Kotak FD)"**
   GT: row 182 (Investment in Govt. Securities ( Current ))
   Golden: row 215 (Other FDs)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: FD Accrued Interest->215 (reclassified) [DISPUTE golden=215 vs GT=182]

**89. [MSL] "(d) Insurance Claim Received"**
   GT: row 34 (Others)
   Golden: row 223 (Other Advances / current asset)
   Source: Source1_rule_107 | Method: rapidfuzz

**90. [MSL] "Raw Material Import Purchases"**
   GT: row 41 (Raw Materials Consumed ( Imported))
   Golden: row 42 (Raw Materials Consumed ( Indigenous))
   Source: Source1_rule_157 | Method: rapidfuzz

**91. [MSL] "(iii) Job Work Charges"**
   GT: row 46 (Processing / Job Work Charges)
   Golden: row 49 (Others)
   Source: Source1_rule_242 | Method: rapidfuzz

**92. [MSL] "(b) Carriage Inwards"**
   GT: row 47 (Freight and Transportation Charges)
   Golden: row 70 (Advertisements and Sales Promotions)
   Source: CA_Q3d_CA_agreed | Method: rapidfuzz

**93. [MSL] "Security Charges"**
   GT: row 45 (Wages)
   Golden: row 71 (Others)
   Source: Source1_rule_264 | Method: rapidfuzz

**94. [MSL] "Rent"**
   GT: row 49 (Others)
   Golden: row 68 (Rent/Rates/Taxes)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Rent->68 [DISPUTE golden=68 vs GT=49]

**95. [MSL] "Stores and spares consumed ( Indigenous)"**
   GT: row 44 (Stores and spares consumed ( Indigenous))
   Golden: row 198 (Indigenous)
   Source: Source1_rule_139 | Method: rapidfuzz

**96. [MSL] "Rates and taxes (excluding, taxes on income)"**
   GT: row 68 (Rent , Rates and Taxes)
   Golden: row 49 (Others)
   Source: Source1_rule_195 | Method: rapidfuzz

**97. [MSL] "(iv) Discount Allowed"**
   GT: row 70 (Advertisements and Sales Promotions)
   Golden: row 22 (Domestic)
   Source: Source1_rule_262 | Method: rapidfuzz

**98. [MSL] "(iii) Freight Outwards"**
   GT: row 70 (Advertisements and Sales Promotions)
   Golden: row 71 (Others)
   Source: Source1_rule_192 | Method: rapidfuzz

**99. [MSL] "(ii) Tour & Travel Expenses"**
   GT: row 71 (Others)
   Golden: row 70 (Ads/Sales(Travel))
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Tour & Travel under selling->70 [DISPUTE golden=70 vs GT=71]

**100. [MSL] "(b) Bank Interest"**
   GT: row 84 (Interest on Working capital loans)
   Golden: row 83 (Interest on Fixed Loans / Term loans)
   Source: Source1_rule_234 | Method: rapidfuzz

**101. [MSL] "(c) Other Charges"**
   GT: row 84 (Interest on Working capital loans)
   Golden: row 49 (Others)
   Source: Source1_rule_162 | Method: rapidfuzz

**102. [MSL] "(2) Deferred tax"**
   GT: row 100 (Deferred Tax Liability)
   Golden: row 171 (Deferred Tax Asset)
   Source: Source1_rule_131 | Method: rapidfuzz

**103. [MSL] "(i) Commission"**
   GT: row 71 (Others)
   Golden: row 70 (Ads/Sales(Commission))
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: CA rule: Commission->70 [DISPUTE golden=70 vs GT=71]

**104. [MSL] "(iv) Discount Allowed"**
   GT: row 71 (Others)
   Golden: row 22 (Domestic)
   Source: Source1_rule_262 | Method: rapidfuzz

**105. [MSL] "(c) Other Charges"**
   GT: row 83 (Interest on Fixed Loans / Term loans)
   Golden: row 49 (Others)
   Source: Source1_rule_162 | Method: rapidfuzz

**106. [MSL] "Deferred Tax Liability"**
   GT: row 100 (Deferred Tax Liability)
   Golden: row 159 (Deferred tax liability)
   Source: Source1_rule_34 | Method: rapidfuzz

**107. [MSL] "Prepaid Expenses"**
   GT: row 222 (Prepaid Expenses)
   Golden: row 223 (Other Advances / current asset)
   Source: Source1_rule_127 | Method: rapidfuzz

**108. [MSL] "Provision for Gratuity (short-term)"**
   GT: row 250 (Other current liabilities)
   Golden: row 67 (Salary and staff expenses)
   Source: Source1_rule_225 | Method: rapidfuzz

**109. [MSL] "Advances recoverable in cash or in kind"**
   GT: row 219 (Advances recoverable in cash or in kind)
   Golden: row 223 (Other Advances / current asset)
   Source: Source1_rule_130 | Method: rapidfuzz

**110. [MSL] "Prepaid Expenses"**
   GT: row 222 (Prepaid Expenses)
   Golden: row 223 (Other Advances / current asset)
   Source: Source1_rule_127 | Method: rapidfuzz

**111. [MSL] "Creditors for Expenses"**
   GT: row 249 (Creditors for Expenses)
   Golden: row 250 (Other current liabilities)
   Source: Source1_rule_70 | Method: rapidfuzz

**112. [SLIPL] "Duty drawback / IGST received"**
   GT: row 23 (Exports)
   Golden: row 34 (Others (Non-Op Income))
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Duty drawback/IGST is in Other Income section. Not actual export revenue. Should be 34 not 23.

**113. [SLIPL] "Consultancy Charges"**
   GT: row 34 (Others)
   Golden: row 71 (Others)
   Source: Source1_rule_190 | Method: rapidfuzz

**114. [SLIPL] "Packing Expenses"**
   GT: row 49 (Others)
   Golden: row 70 (Advertisements and Sales Promotions)
   Source: Source1_rule_301 | Method: rapidfuzz

**115. [SLIPL] "Rent"**
   GT: row 49 (Others)
   Golden: row 68 (Rent/Rates/Taxes)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Rent should be 68 per CA rules. GT says 49 (factory rent). Without factory designation, standard is 68.

**116. [SLIPL] "Rates and taxes (excluding taxes on income)"**
   GT: row 68 (Rent , Rates and Taxes)
   Golden: row 49 (Others)
   Source: Source1_rule_195 | Method: rapidfuzz

**117. [SLIPL] "Sundries"**
   GT: row 69 (Bad Debts)
   Golden: row 71 (Others (Admin))
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Sundries is generic admin expense -> 71. GT says 69 Bad Debts which is wrong for sundries.

**118. [SLIPL] "Repairs to Plant & Machinery"**
   GT: row 72 (Repairs & Maintenance)
   Golden: row 50 (Repairs (Mfg))
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Repairs to Plant and Machinery -> row 50 per CA rules. GT says 72 which is admin repairs.

**119. [SLIPL] "Interest expense"**
   GT: row 84 (Interest on Working capital loans)
   Golden: row 71 (Others)
   Source: Source1_rule_249 | Method: rapidfuzz

**120. [SLIPL] "Other Charges (Finance Costs)"**
   GT: row 85 (Bank Charges)
   Golden: row 49 (Others)
   Source: Source1_rule_162 | Method: rapidfuzz

**121. [SLIPL] "Bad Debts Written off"**
   GT: row 90 (Sundry Balances Written off)
   Golden: row 69 (Bad Debts)
   Source: CA_Q27_CA_agreed | Method: rapidfuzz

**122. [SLIPL] "Deferred tax"**
   GT: row 100 (Deferred Tax Liability)
   Golden: row 171 (Deferred Tax Asset)
   Source: Source1_rule_131 | Method: rapidfuzz

**123. [SLIPL] "Deferred tax (credit)"**
   GT: row 101 (Deferred Tax Asset)
   Golden: row 171 (Deferred Tax Asset)
   Source: Source1_rule_131 | Method: rapidfuzz

**124. [SLIPL] "Margin money deposits"**
   GT: row 215 (Other Fixed Deposits)
   Golden: row 237 (Security deposits with government departments)
   Source: Source1_rule_111 | Method: rapidfuzz

**125. [SLIPL] "Prepaid Expenses"**
   GT: row 222 (Prepaid Expenses)
   Golden: row 223 (Other Advances / current asset)
   Source: Source1_rule_127 | Method: rapidfuzz

**126. [SLIPL] "Security Deposits - Others"**
   GT: row 238 (Other non current assets)
   Golden: row 237 (Security deposits with government departments)
   Source: Source1_rule_110 | Method: rapidfuzz

**127. [SLIPL] "Freight Outward"**
   GT: row 47 (Freight and Transportation Charges)
   Golden: row 71 (Others)
   Source: Source1_rule_192 | Method: rapidfuzz

**128. [SR_Papers] "Unloading Charges - Mathadi"**
   GT: row 47 (Freight and Transportation Charges)
   Golden: row 45 (Wages)
   Source: Source1_rule_169 | Method: rapidfuzz

**129. [SR_Papers] "Labour Charges"**
   GT: row 49 (Others)
   Golden: row 45 (Wages)
   Source: Source1_rule_168 | Method: rapidfuzz

**130. [SR_Papers] "Admin Exp for PF"**
   GT: row 67 (Salary and staff expenses)
   Golden: row 45 (Wages (EPF Admin))
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Admin Exp for PF is EPFO admin charge. Per CA rules EPF -> 45. GT says 67.

**131. [SR_Papers] "Tea & Food Expenses"**
   GT: row 67 (Salary and staff expenses)
   Golden: row 45 (Wages (Staff Welfare))
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Tea and Food in manufacturing: staff welfare -> 45 per industry rules. GT says 67.

**132. [SR_Papers] "Rates and taxes"**
   GT: row 68 (Rent , Rates and Taxes)
   Golden: row 49 (Others)
   Source: Source1_rule_195 | Method: rapidfuzz

**133. [SR_Papers] "Discount Recieved"**
   GT: row 29 (Dividends received from Mutual Funds)
   Golden: row 42 (Raw Materials Consumed ( Indigenous))
   Source: Source1_rule_363 | Method: rapidfuzz

**134. [SR_Papers] "Discount Recieved"**
   GT: row 34 (Others)
   Golden: row 42 (Raw Materials Consumed ( Indigenous))
   Source: Source1_rule_363 | Method: rapidfuzz

**135. [SR_Papers] "Rate Difference"**
   GT: row 34 (Others)
   Golden: row 22 (Domestic)
   Source: Source1_rule_254 | Method: rapidfuzz

**136. [SR_Papers] "Deferred tax"**
   GT: row 100 (Deferred Tax Liability)
   Golden: row 171 (Deferred Tax Asset)
   Source: Source1_rule_131 | Method: rapidfuzz

**137. [SR_Papers] "Expenses Payable"**
   GT: row 250 (Other current liabilities)
   Golden: row 249 (Creditors for Expenses)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Expenses Payable should be 249. GT says 250 Other CL.

**138. [SR_Papers] "Short Term Borrowings - Debentures portion"**
   GT: row 141 (Balance Repayable after one year)
   Golden: row 140 (Debentures in 1yr)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: ST debentures should be 140 (within 1yr). GT says 141 (after 1yr).

**139. [SR_Papers] "Term Loans from banks"**
   GT: row 137 (Balance Repayable after one year)
   Golden: row 131 (From Indian Bank)
   Source: Source1_rule_41 | Method: rapidfuzz

**140. [SR_Papers] "Security deposits - Unsecured, considered good"**
   GT: row 237 (Security deposits with government departments)
   Golden: row 238 (Other NCA)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: General security deposits should be 238 per CA rules. GT says 237 (govt depts only).

**141. [SSSS] "(i) Power And Fuel"**
   GT: row 49 (Others)
   Golden: row 71 (Others (Admin))
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Power/Fuel in TRADING -> 71 per industry rules. GT says 49 (manufacturing only).

**142. [SSSS] "(a). Employee Benefit Expense"**
   GT: row 71 (Others)
   Golden: row 67 (Salary/Staff Expenses)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Employee Benefits in TRADING -> 67 per industry rules. GT says 71.

**143. [SSSS] "(a) Auditor's Remuneration"**
   GT: row 71 (Others)
   Golden: row 73 (Audit Fees & Directors Remuneration)
   Source: Source1_rule_231 | Method: rapidfuzz

**144. [SSSS] "(b) Advertisement and Sales Promotion Expenses"**
   GT: row 71 (Others)
   Golden: row 70 (Ads/Sales Promotions)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Advertisement -> 70 per CA rules. GT says 71.

**145. [SSSS] "(j) Rent, Rates and Taxes"**
   GT: row 71 (Others)
   Golden: row 68 (Rent, Rates and Taxes)
   Source: Source1_rule_196 | Method: rapidfuzz

**146. [SSSS] "(k) Repairs and Maintenance"**
   GT: row 71 (Others)
   Golden: row 72 (Repairs (Admin))
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Repairs in trading -> 72 Repairs(Admin). GT says 71.

**147. [SSSS] "Loss on disposal of fixed assets (estimated)"**
   GT: row 93 (Others)
   Golden: row 89 (Loss on Sale)
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: Loss on disposal of fixed assets -> 89. GT says 93 Others Non-Op.

**148. [SSSS] "(d) Deferred tax"**
   GT: row 101 (Deferred Tax Asset)
   Golden: row 171 (Deferred Tax Asset)
   Source: Source1_rule_131 | Method: rapidfuzz

**149. [SSSS] "HSBC OD A/C"**
   GT: row 131 (From Indian Bank)
   Golden: row 132 (WC Bank Finance (Bank 2))
   Source: agent_reasoning | Method: agent_reasoning
   Reasoning: HSBC OD should be 132 (second bank). GT says 131 combining both.

**150. [SSSS] "Current Maturities of Long-term Debt (CMLTD)"**
   GT: row 131 (From Indian Bank)
   Golden: row 136 (Term Loan Repayable in next one year)
   Source: CA_Q16_CA_agreed | Method: rapidfuzz

**151. [SSSS] "(B) Sundry Creditors for expenses"**
   GT: row 249 (Creditors for Expenses)
   Golden: row 250 (Other current liabilities)
   Source: Source1_rule_70 | Method: rapidfuzz

**152. [SSSS] "Share Investments"**
   GT: row 188 (Investment in group companies / subsidiaries)
   Golden: row 233 (Investments)
   Source: Source1_rule_94 | Method: rapidfuzz

**153. [INPL] "Consultancy Charges"**
   GT: row 71 (Others)
   Golden: row 49 (Others)
   Source: cross_check_step1 | Method: cross_check
   Reasoning: Location A (GT) says row 71, Location B says row 49 for FY 2023

**154. [INPL] "Packing and Forwarding Charges"**
   GT: row 49 (Others)
   Golden: row 47 (Freight and Transportation Charges)
   Source: cross_check_step1 | Method: cross_check
   Reasoning: Location A (GT) says row 49, Location B says row 47 for FY 2023

**155. [INPL] "Project Cost"**
   GT: row 71 (Others)
   Golden: row 93 (Others)
   Source: cross_check_step1 | Method: cross_check
   Reasoning: Location A (GT) says row 71, Location B says row 93 for FY 2023

**156. [INPL] "Research and Development"**
   GT: row 71 (Others)
   Golden: row 49 (Others)
   Source: cross_check_step1 | Method: cross_check
   Reasoning: Location A (GT) says row 71, Location B says row 49 for FY 2023

**157. [INPL] "Staff Welfare Expenses"**
   GT: row 45 (Wages)
   Golden: row 67 (Salary and staff expenses)
   Source: cross_check_step1 | Method: cross_check
   Reasoning: Location A (GT) says row 45, Location B says row 67 for FY 2024

**158. [INPL] "Gratuity to Employees"**
   GT: row 45 (Wages)
   Golden: row 67 (Salary and staff expenses)
   Source: cross_check_step1 | Method: cross_check
   Reasoning: Location A (GT) says row 45, Location B says row 67 for FY 2024

**159. [INPL] "Consultancy Charges"**
   GT: row 71 (Others)
   Golden: row 49 (Others)
   Source: cross_check_step1 | Method: cross_check
   Reasoning: Location A (GT) says row 71, Location B says row 49 for FY 2024

**160. [INPL] "Material Handling Charges"**
   GT: row 46 (Processing / Job Work Charges)
   Golden: row 49 (Others)
   Source: cross_check_step1 | Method: cross_check
   Reasoning: Location A (GT) says row 46, Location B says row 49 for FY 2024

**161. [INPL] "Staff Welfare Expenses"**
   GT: row 45 (Wages)
   Golden: row 67 (Salary and staff expenses)
   Source: cross_check_step1 | Method: cross_check
   Reasoning: Location A (GT) says row 45, Location B says row 67 for FY 2025

**162. [INPL] "Gratuity to Employees"**
   GT: row 45 (Wages)
   Golden: row 67 (Salary and staff expenses)
   Source: cross_check_step1 | Method: cross_check
   Reasoning: Location A (GT) says row 45, Location B says row 67 for FY 2025

**163. [INPL] "Consultancy Charges"**
   GT: row 71 (Others)
   Golden: row 49 (Others)
   Source: cross_check_step1 | Method: cross_check
   Reasoning: Location A (GT) says row 71, Location B says row 49 for FY 2025

**164. [INPL] "Finished Goods"**
   GT: row 59 (Finished Goods Closing Balance)
   Golden: row 201 (Finished Goods)
   Source: cross_check_step1 | Method: cross_check
   Reasoning: Location A (GT) says row 59, Location B says row 201 for FY 2025

**165. [Kurunji_Retail] "Closing Stock"**
   GT: row 59 (Finished Goods Closing Balance)
   Golden: row 201 (Finished Goods)
   Source: cross_check_step1 | Method: cross_check
   Reasoning: Location A (GT) says row 59, Location B says row 201 for FY 2025

**166. [Kurunji_Retail] "Depreciation"**
   GT: row 56 (Depreciation)
   Golden: row 63 (Depreciation)
   Source: cross_check_step1 | Method: cross_check
   Reasoning: Location A (GT) says row 56, Location B says row 63 for FY 2025

**167. [SR_Papers] "Computer Maintanance"**
   GT: row 72 (Repairs & Maintenance)
   Golden: row 71 (Others)
   Source: cross_check_step1 | Method: cross_check
   Reasoning: Location A (GT) says row 72, Location B says row 71 for FY 2023

**168. [SR_Papers] "Manpower Charges"**
   GT: row 49 (Others)
   Golden: row 45 (Wages)
   Source: cross_check_step1 | Method: cross_check
   Reasoning: Location A (GT) says row 49, Location B says row 45 for FY 2023

**169. [SR_Papers] "TDS Receivable"**
   GT: row 219 (Advances recoverable in cash or in kind)
   Golden: row 221 (Advance Income Tax)
   Source: cross_check_step1 | Method: cross_check
   Reasoning: Location A (GT) says row 219, Location B says row 221 for FY 2023

**170. [SR_Papers] "TCS Receivable"**
   GT: row 219 (Advances recoverable in cash or in kind)
   Golden: row 221 (Advance Income Tax)
   Source: cross_check_step1 | Method: cross_check
   Reasoning: Location A (GT) says row 219, Location B says row 221 for FY 2023

**171. [SR_Papers] "Manpower Charges"**
   GT: row 49 (Others)
   Golden: row 45 (Wages)
   Source: cross_check_step1 | Method: cross_check
   Reasoning: Location A (GT) says row 49, Location B says row 45 for FY 2024

**172. [SR_Papers] "Computer Maintanance"**
   GT: row 72 (Repairs & Maintenance)
   Golden: row 71 (Others)
   Source: cross_check_step1 | Method: cross_check
   Reasoning: Location A (GT) says row 72, Location B says row 71 for FY 2025

**173. [SR_Papers] "Manpower Charges"**
   GT: row 49 (Others)
   Golden: row 45 (Wages)
   Source: cross_check_step1 | Method: cross_check
   Reasoning: Location A (GT) says row 49, Location B says row 45 for FY 2025

**174. [SSSS] "Current tax expense"**
   GT: row 244 (Provision for Taxation)
   Golden: row 99 (Income Tax  provision)
   Source: cross_check_step1 | Method: cross_check
   Reasoning: Location A (GT) says row 244, Location B says row 99 for FY 2024

