# CMA Classification — Questions for CA Clarification

**Date:** 2026-03-26
**Context:** We ran accuracy tests on 9 companies (1,326 items) and interviewed the AI model on 100 genuinely wrong classifications. These questions arise from ambiguities the system cannot resolve without CA expert judgment.

**How to answer:** For each question, please circle/write the correct CMA row number or option. Add any notes where the answer depends on context.

---

## SECTION A: Wages vs Salary Boundary (Row 45 vs Row 67)

This is the #1 confusion — ~15 items across multiple companies. The CMA has two employee cost rows:
- **Row 45** = Wages (Manufacturing Expenses section)
- **Row 67** = Salary and staff expenses (Admin & Selling Expenses section)

**Q1.** When a company lists the following under "Employee Benefits" or "Other Expenses", which row should each go to?

| # | Item | Row 45 (Wages) | Row 67 (Salary) | Depends on? |
|---|------|:-:|:-:|---|
| a | Staff Welfare Expenses | ☐ | ☐ | |
| b | Gratuity / Gratuity to Employees | ☐ | ☐ | |
| c | Contribution to EPF | ☐ | ☐ | |
| d | Contribution to ESI | ☐ | ☐ | |
| e | Staff Mess Expenses | ☐ | ☐ | |
| f | Leave Encashment | ☐ | ☐ | |
| g | Bonus | ☐ | ☐ | |
| h | "Salary, Wages and Bonus" (combined line) | ☐ | ☐ | |
| i | "Employee Benefits Expense" (combined line) | ☐ | ☐ | |
| j | Labour Charges Paid | ☐ | ☐ | |

**Q2.** Is the rule: "If the company is manufacturing and the item appears under direct/manufacturing expenses, use Row 45; if under admin expenses, use Row 67"? Or is it always one row regardless of section?

Answer: _______________________________________________________________

---

## SECTION B: The "Others" Problem (Row 49 vs Row 71 vs Row 75)

Three "Others" rows exist in CMA:
- **Row 49** = Others (Manufacturing Expenses) — for miscellaneous manufacturing costs
- **Row 71** = Others (Admin & Selling Expenses) — for miscellaneous admin costs
- **Row 75** = Miscellaneous Expenses Written off — for write-offs/amortisations

**Q3.** Where should these items go?

| # | Item | R49 (Mfg Others) | R71 (Admin Others) | R75 (Misc Written off) | Other Row? |
|---|------|:-:|:-:|:-:|---|
| a | Miscellaneous Expenses | ☐ | ☐ | ☐ | |
| b | Selling & Distribution Expenses | ☐ | ☐ | ☐ | Row 70? |
| c | Administrative & General Expenses | ☐ | ☐ | ☐ | Row 69? |
| d | Carriage Outward | ☐ | ☐ | ☐ | Row 70? |
| e | Brokerage & Commission | ☐ | ☐ | ☐ | Row 70? |
| f | Licence & Subscription fees | ☐ | ☐ | ☐ | Row 68? |

**Q4.** Row 75 is labelled "Miscellaneous Expenses Written off." Should "Miscellaneous Expenses" (without "written off") ever go to Row 75, or always Row 71?

Answer: _______________________________________________________________

---

## SECTION C: Carriage / Freight Classification

**Q5.** Our current rule says "Carriage Inward / Freight Inward → Row 41 (Raw Materials Consumed)." But the GT says it should be **Row 47 (Freight and Transportation Charges)**. Which is correct?

- ☐ Row 41 (Raw Materials Consumed) — freight is part of material cost
- ☐ Row 47 (Freight and Transportation Charges) — freight is a separate manufacturing expense
- ☐ Depends on: _______________________________________________________________

**Q6.** "Carriage Outward" — should it go to:
- ☐ Row 47 (Freight and Transportation Charges) — it's a freight cost
- ☐ Row 70 (Advertisements and Sales Promotions) — it's a selling expense
- ☐ Other: _______________________________________________________________

---

## SECTION D: P&L Stock Rows vs Balance Sheet Stock Rows

The CMA has stock items in TWO places:
- **P&L rows**: Row 53-54 (WIP Opening/Closing), Row 57-58 (FG Opening/Closing), Row 59 (FG Closing Balance)
- **BS rows**: Row 200 (Stocks-in-process), Row 201 (Finished Goods)

**Q7.** When extracted from P&L "Changes in Inventories" section:
- "Closing Stock - Work in Progress" → Row _____ (54 or 200?)
- "Opening Stock - Work in Progress" → Row _____ (53 or 200?)
- "Closing Stock - Finished Goods" → Row _____ (59 or 201?)
- "Opening Stock - Finished Goods" → Row _____ (57 or 201?)

**Q8.** When extracted from Balance Sheet "Inventories" section:
- "Work in Progress" → Row _____ (54 or 200?)
- "Finished Goods" → Row _____ (59 or 201?)

**Q9.** Is the rule simply: "P&L context → P&L rows (53-59), Balance Sheet context → BS rows (200-201)"?

Answer: _______________________________________________________________

---

## SECTION E: Finance Cost Items Under "Other Expenses"

Many companies list finance-related items under the generic "Other Expenses" header instead of "Finance Costs."

**Q10.** When these appear under "Other Expenses" (not under "Finance Costs"), which row?

| # | Item | Row 83 (Interest on Fixed Loans) | Row 84 (Interest on WC Loans) | Row 85 (Bank Charges) | Row 71 (Others) |
|---|------|:-:|:-:|:-:|:-:|
| a | Bank Charges | ☐ | ☐ | ☐ | ☐ |
| b | Interest on Delay in Payment of Taxes | ☐ | ☐ | ☐ | ☐ |
| c | Forex Rate Fluctuation Loss | ☐ | ☐ | ☐ | ☐ |
| d | Liquidated Damages | ☐ | ☐ | ☐ | ☐ |
| e | Bill Discounting Charges | ☐ | ☐ | ☐ | ☐ |
| f | Interest on Bill Discounting | ☐ | ☐ | ☐ | ☐ |
| g | Loan/Overdraft Processing Fee | ☐ | ☐ | ☐ | ☐ |
| h | Interest on CC A/c | ☐ | ☐ | ☐ | ☐ |

**Q11.** Should Forex Rate Fluctuation Loss go to Row 90 (Sundry Balances Written off) or Row 91 (Loss on Sale/Discard of Assets) or somewhere else?

Answer: _______________________________________________________________

---

## SECTION F: Manufacturing vs Admin Routing

Items under "Other Expenses" that may actually be manufacturing costs.

**Q12.** For a MANUFACTURING company, where should these go?

| # | Item | Mfg Row | Admin Row | Notes |
|---|------|---------|-----------|-------|
| a | Electric Charges | R48 (Power/Coal/Fuel) ☐ | R71 (Others) ☐ | |
| b | Transportation Charges | R47 (Freight) ☐ | R71 (Others) ☐ | |
| c | Material Handling Charges | R46 (Processing/Job Work) ☐ | R71 (Others) ☐ | |
| d | Packing Expenses | R44 (Stores & Spares) ☐ | R71 (Others) ☐ | R49? |
| e | Security Service Charges | R51 (Security) ☐ | R71 (Others) ☐ | |
| f | Rent - Factory | R49 (Others Mfg) ☐ | R68 (Rent) ☐ | |
| g | Repairs & Maintenance - Machinery | R50 (R&M) ☐ | R72 (R&M Admin) ☐ | |

**Q13.** Is the rule: "If the company is manufacturing, these items should ALWAYS go to manufacturing rows regardless of which section header they appear under"? Or does the section header in the financial statement matter?

Answer: _______________________________________________________________

---

## SECTION G: Reserves & Surplus Items

**Q14.** Opening balance of P&L surplus in "Reserves & Surplus" section:
- "Surplus at the beginning of the year" → Row _____ (105 or 106 or 122?)
- "Surplus - Opening Balance" → Row _____ (105 or 106 or 122?)
- "Balance brought forward from previous year" → Row _____ (106?)

**Q15.** "Issue of Bonus Shares" (capitalization of P&L surplus) → Row _____ (108 Other Appropriation?)

---

## SECTION H: Borrowings Classification

**Q16.** "Current Maturities of Long-term Debt" appears under "Other Current Liabilities":
- ☐ Row 135 (Term Loan Repayable in next one year) — it's a debt reclassification
- ☐ Row 136 (Term Loan Repayable in next one year — another sub-row)
- ☐ Row 250 (Other current liabilities) — it's listed under current liabilities
- ☐ Other: _____

**Q17.** "Vehicle HP Loans - Current Maturities" under Short-term Borrowings:
- ☐ Row 140 (Repayable in next one year — Debentures section)
- ☐ Row 136 (Term Loan Repayable in next one year)
- ☐ Row 131 (From Indian Bank)
- ☐ Other: _____

**Q18.** "Loan from Banks - Current Maturities" under Short-term Borrowings:
- ☐ Row 136 (Term Loan Repayable in next one year)
- ☐ Row 131 (From Indian Bank)
- ☐ Other: _____

**Q19.** "Unsecured Loans from Directors" under Long-term Borrowings:
- ☐ Row 151 (Directors' Loans — Quasi Equity)
- ☐ Row 152 (As Quasi Equity)
- ☐ Row 153 (As Long Term Debt)
- ☐ Other: _____

**Q20.** "Other Long Term Liability" (non-borrowing):
- ☐ Row 153 (As Long Term Debt)
- ☐ Row 149 (Balance Other Debts)
- ☐ Other: _____

---

## SECTION I: Audit Fees & Directors Remuneration

**Q21.** Row 73 in CMA is labelled "Audit Fees & Directors Remuneration." But we've seen:
- "Directors Remuneration" going to Row 67 (Salary) in some GTs
- "Auditor's Remuneration" going to Row 70 (Ads & Sales) in some GTs

Please confirm:
- Directors Remuneration → Row _____ (66, 67, or 73?)
- Auditor's Remuneration (Statutory Audit) → Row _____ (70 or 73?)
- Auditor's Remuneration (Tax Audit) → Row _____ (70 or 73?)

---

## SECTION J: Specific Items Needing Clarification

**Q22.** "Profit on Sale of Fixed Asset" — appears under Other Income:
- ☐ Row 22 (Domestic Sales) — it's revenue
- ☐ Row 31 (Profit on sale of fixed assets/Investments) — non-operating income
- ☐ Other: _____

**Q23.** "Sale of Duty Credit Scrips" — appears under Other Income:
- ☐ Row 22 (Domestic) — export-related revenue
- ☐ Row 34 (Others — Non-Operating Income)
- ☐ Other: _____

**Q24.** "Advances Written Off" — appears under Other Expenses:
- ☐ Row 69 (Bad Debts)
- ☐ Row 70 (Advertisements and Sales Promotions — catch-all admin)
- ☐ Row 74 (specific written-off row)
- ☐ Other: _____

**Q25.** "Bad Debts Written Off":
- ☐ Row 69 (Bad Debts)
- ☐ Row 70 (Advertisements and Sales Promotions)
- ☐ Other: _____

**Q26.** "Rates & Taxes":
- ☐ Row 68 (Rent, Rates and Taxes) — grouped with rent
- ☐ Row 70 (Advertisements and Sales Promotions)
- ☐ Other: _____

**Q27.** "TDS on Rent" — paid as expense:
- ☐ Row 49 (Others Manufacturing) — it's an overhead
- ☐ Row 68 (Rent, Rates and Taxes)
- ☐ Row 71 (Others Admin)
- ☐ Other: _____

**Q28.** "Rent - Parking":
- ☐ Row 49 (Others Manufacturing)
- ☐ Row 68 (Rent, Rates and Taxes)
- ☐ Other: _____

**Q29.** "Display Amount / Discount" (trading company, under Credit side of P&L):
- ☐ Row 42 (Raw Materials Consumed — Indigenous, as negative purchase adjustment)
- ☐ Row 34 (Others Non-Operating Income)
- ☐ Other: _____

**Q30.** "Opening Stock of Packing Materials" and "Packing Expenses" (trading company):
- ☐ Row 44 (Stores and Spares Consumed)
- ☐ Row 49 (Others Manufacturing)
- ☐ Row 71 (Others Admin)
- ☐ Other: _____

**Q31.** "Provision for Employee Benefits (Gratuity)" under Long-term Provisions:
- ☐ Row 153 (As Long Term Debt) — it's a non-current liability
- ☐ Row 67 (Salary and staff expenses) — it's an employee cost
- ☐ Other: _____

**Q32.** "Outstanding Expenses - Salary" under Current Liabilities:
- ☐ Row 249 (Creditors for Expenses)
- ☐ Row 67 (Salary and staff expenses)
- ☐ Row 250 (Other current liabilities)
- ☐ Other: _____

**Q33.** "Leave Encashment" under Current Liabilities/Short-term Provisions:
- ☐ Row 243 (Advance received from customers)
- ☐ Row 248 (Interest Accrued and due)
- ☐ Row 249 (Creditors for Expenses)
- ☐ Row 250 (Other current liabilities)
- ☐ Other: _____

**Q34.** "Short-term Provisions" (as a generic line):
- ☐ Row 248 (Interest Accrued and due)
- ☐ Row 250 (Other current liabilities)
- ☐ Other: _____

**Q35.** "Raw Materials" in Balance Sheet Inventories section:
- ☐ Row 193 (Imported) or Row 194 (Indigenous) — BS inventory rows
- ☐ Row 41/42 (P&L consumption rows)
- ☐ Rule: Inventories section → 193/194, P&L section → 41/42?

**Q36.** "Scraps" in Balance Sheet Inventories section:
- ☐ Row 197 (Imported — Stores & Spares)
- ☐ Row 198 (Indigenous — Stores & Spares)
- ☐ Row 44 (Stores and Spares Consumed in P&L)
- ☐ Other: _____

**Q37.** "Capital Advances" under Non-Current Assets:
- ☐ Row 235 (Dues from directors/partners/promoters)
- ☐ Row 236 (Advances to suppliers of capital goods)
- ☐ Other: _____

**Q38.** "Other Non-Current Assets" (generic line):
- ☐ Row 236 (Advances to suppliers of capital goods)
- ☐ Row 237 (Security deposits with government departments)
- ☐ Row 238 (Other non-current assets)
- ☐ Other: _____

**Q39.** "Deferred Tax Liability / (Asset)" — single combined line in P&L:
- ☐ Row 100 (Deferred Tax Liability) — P&L provision
- ☐ Row 101 (Deferred Tax Asset) — P&L provision
- ☐ Row 159 (Deferred tax liability — Balance Sheet)
- ☐ Rule: _______________________________________________________________

**Q40.** "Other Bank Balances (Cr.)" under Other Current Liabilities:
- ☐ Row 130 (Bank liabilities)
- ☐ Row 213 (Bank Balances — asset side)
- ☐ Row 250 (Other current liabilities)
- ☐ Other: _____

---

## SECTION K: General Rules

**Q41.** Should the section header in the financial statement (where the item appears) affect classification? For example, if "Bank Charges" appears under "Other Expenses" instead of "Finance Costs", should it still go to a finance row (R83/84/85)?

- ☐ Yes — always classify by the NATURE of the item, regardless of where the company put it
- ☐ No — respect the company's section placement
- ☐ Depends: _______________________________________________________________

**Q42.** For a TRADING company (no manufacturing), should items like Electric Charges, Packing, Transportation go to:
- ☐ Manufacturing rows (R47, R48, R49) — same as manufacturing company
- ☐ Admin rows (R68, R71) — trading companies don't have manufacturing expenses
- ☐ Depends: _______________________________________________________________

**Q43.** "Loan/Overdraft Processing Fee" — is this Row 83 (Interest on Fixed Loans) or Row 84 (Interest on WC Loans) or Row 85 (Bank Charges)?

Answer: _______________________________________________________________

---

## Notes for the CA

1. **Row numbers** refer to the CMA INPUT SHEET row numbers (as per CMA.xlsm template)
2. **"Correct" answers** in this document come from ground truth we built by manually mapping items — but some may be wrong, which is why we need your review
3. **Priority:** Questions A (Wages/Salary) and B (Others) affect the most items (~25 total). Getting these right will have the biggest impact.
4. **When in doubt**, please write "DEPENDS ON [condition]" rather than picking one — we can code conditional logic

---

*Thank you! Your answers will be directly coded into the classification system.*
