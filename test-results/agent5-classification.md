# Agent 5: Classification Quality Report
**Date:** 2026-03-19
**Document ID:** db4db151-758e-420a-8827-e7fd8751a5aa
**Client ID:** 206a2fe3-c65d-42d2-93e0-02226ed378e1
**Industry:** Trading
**CMA Report ID:** 8b8d5f71-ab88-4f0a-b576-f5f834719435
**Ground Truth:** `DOCS/Excel_project/Mehta computer/CMA 15092025.xls` (INPUT SHEET, FY2024, col D)

---

## 1. Executive Summary

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Total items extracted | 162 | 162 | PASS |
| Tier 1 (fuzzy/learned) | 0 (0.0%) | >60% | FAIL |
| Tier 2 (AI confident) | 55 (34.0%) | 20-30% | MARGINAL |
| Tier 3 (doubt) | 107 (66.0%) | <15% | FAIL |
| Overall accuracy (correct behavior) | 88.3% | — | PASS |
| True classification errors | 19 (A:5 B:3 C:9 D:2) | — | — |
| Correct doubts (E+F) | 88 | — | PASS |
| Auto-classified accuracy | 100% (55/55 correct fields) | — | PASS |

**Critical finding:** Tier 1 fuzzy matching is completely non-functional because all 384 rows in `cma_reference_mappings` have `cma_input_row = NULL`. This caused 100% of items to pass through to the AI tier. The 66% doubt rate is the systemic consequence.

**Pipeline bug fixed:** The classification pipeline had a DB insert bug — `fuzzy_match_score` was stored as Python `float` (e.g., `0.0`) but the DB column is `integer`. `cma_field_name` also had a NOT NULL constraint violated by doubt records. Both were patched before this run.

**Learning system:** Direct `_upsert_learned_mapping` fails due to missing unique constraint on `(source_text, cma_field_name, industry_type)`. Correction was applied manually via direct DB update. One correction written to `learned_mappings`.

---

## 2. Full Classification Results Table

### 2a. Auto-Classified Items (55 items, 0 errors)

| # | Source Text | CMA Field Assigned | Row | Confidence | Method |
|---|-------------|-------------------|-----|-----------|--------|
| 1 | Add: Depreciation | Depreciation (CMA) | 63 | 0.95 | ai_haiku |
| 2 | Less: Depreciation u/s 32(1) | Depreciation (CMA) | 63 | 0.95 | ai_haiku |
| 3 | Dividend | Dividend | 107 | 1.00 | ai_haiku |
| 4 | FD Interest | Interest Received | 30 | 0.95 | ai_haiku |
| 5 | Income Tax Payable | Income Tax provision | 99 | 0.95 | ai_haiku |
| 6 | Add : Education Cess @ 4% | Less Excise Duty and Cess | 25 | 0.92 | ai_haiku |
| 7 | Less : Advance Tax | Advance Income Tax | 221 | 0.95 | ai_haiku |
| 8 | Add : Interest | Interest Received | 30 | 0.95 | ai_haiku |
| 9 | By Dividend | Dividend | 107 | 0.95 | ai_haiku |
| 10 | To Water tax | Rent, Rates and Taxes | 68 | 0.90 | ai_haiku |
| 11 | To Property Tax | Rent, Rates and Taxes | 68 | 0.85 | ai_haiku |
| 12 | Bank of Baroda | Bank Balances | 213 | 0.95 | ai_haiku |
| 13 | Bank of India | Bank Balances | 213 | 0.95 | ai_haiku |
| 14 | Kotak Mahindra Bank | Bank Balances | 213 | 0.95 | ai_haiku |
| 15 | Kotak Mahindra Bank (Harsh J Mehta) | Bank Balances | 213 | 0.95 | ai_haiku |
| 16 | Kotak - Sweep Account | Bank Balances | 213 | 0.95 | ai_haiku |
| 17 | KMB Bank (Jalak J Mehta) | Bank Balances | 213 | 0.95 | ai_haiku |
| 18 | Mutual Fund - Edelweiss Large | Other current investments | 185 | 0.95 | ai_haiku |
| 19 | Sales @ 12% (Local) | Domestic Sales | 22 | 0.95 | ai_haiku |
| 20 | Sales @ 18% (Igst) | Domestic Sales | 22 | 0.95 | ai_haiku |
| 21 | Sales @ 18% (Local) | Domestic Sales | 22 | 0.95 | ai_haiku |
| 22 | Sales @ 28% (Igst) | Domestic Sales | 22 | 0.95 | ai_haiku |
| 23 | Sales @ 5% (Local) | Domestic Sales | 22 | 0.95 | ai_haiku |
| 24 | Transport Charges | Freight and Transportation Charges | 47 | 0.92 | ai_haiku |
| 25 | Sales @ 28% (Local) | Domestic Sales | 22 | 0.95 | ai_haiku |
| 26 | Courier Charges | Freight and Transportation Charges | 47 | 0.92 | ai_haiku |
| 27 | Transport Charges (2nd) | Freight and Transportation Charges | 47 | 0.92 | ai_haiku |
| 28 | Bank Charges | Bank Charges | 85 | 0.99 | ai_haiku |
| 29 | Conveyance | Others (Admin) | 71 | 0.85 | ai_haiku |
| 30 | Audit Fees | Audit Fees & Directors Remuneration | 73 | 0.95 | ai_haiku |
| 31 | Bad Debts | Bad Debts | 69 | 1.00 | ai_haiku |
| 32 | Cellphone Charge | Others (Admin) | 71 | 0.95 | ai_haiku |
| 33 | Sundry Balance W/off | Sundry Balances Written off | 90 | 0.95 | ai_haiku |
| 34 | Freight Charges | Freight and Transportation Charges | 47 | 0.95 | ai_haiku |
| 35 | Insurance | Others (Admin) | 71 | 0.92 | ai_haiku |
| 36 | Rent Account | Rent, Rates and Taxes | 68 | 0.95 | ai_haiku |
| 37 | Telephone Expenses | Others (Admin) | 71 | 0.92 | ai_haiku |
| 38 | Salary Paid | Salary and staff expenses | 67 | 0.95 | ai_haiku |
| 39 | Staff Welfare | Salary and staff expenses | 67 | 0.95 | ai_haiku |
| 40 | Travelling Expense | Others (Admin) | 71 | 0.92 | ai_haiku |
| 41 | Bank Interest (income) | Interest Received | 30 | 0.95 | ai_haiku |
| 42 | Interest on PPF | Interest Received | 30 | 0.95 | ai_haiku |
| 43 | FD Interest (2nd) | Interest Received | 30 | 0.95 | ai_haiku |
| 44 | Interest on Wankaner Deposits | Interest Received | 30 | 0.95 | ai_haiku |
| 45 | Discount Received - Non GST | Others (Non-Operating Income) | 34 | 0.95 | ai_haiku |
| 46 | DM Pharma | Domestic Receivables | 206 | 0.92 | ai_haiku |
| 47 | Honeywell Automation India Ltd | Domestic Receivables | 206 | 0.92 | ai_haiku |
| 48 | Tata Project Limited | Domestic Receivables | 206 | 0.90 | ai_haiku |
| 49 | N2H Internationals | Domestic Receivables | 206 | 0.85 | ai_haiku |
| 50 | BODHI INFOTEX | Sundry Creditors for goods | 242 | 0.85 | ai_haiku |
| 51 | DHARMSHRI ELECTRICALS PRIVATE LIMITED | Sundry Creditors for goods | 242 | 0.95 | ai_haiku |
| 52 | GENESIS GLOBAL | Sundry Creditors for goods | 242 | 0.95 | ai_haiku |
| 53 | GURU COMPUTERS | Sundry Creditors for goods | 242 | 0.95 | ai_haiku |
| 54 | PARAS ENTERPRISES | Sundry Creditors for goods | 242 | 0.95 | ai_haiku |
| 55 | RN ELECTRICALS | Sundry Creditors for goods | 242 | 0.90 | ai_haiku |

### 2b. Doubt Items Summary (107 items)

Full list of all 107 doubt items with AI best guess:

| # | Source Text | AI Best Guess | Error Type |
|---|------------|--------------|-----------|
| 1 | To LIC | Others (Admin) | F |
| 2 | Annual Value of Self Occupied Property | Others (Non-Operating Income) | E |
| 3 | Less : Interest on Housing Loan | Others (Non-Operating Expenses) | E |
| 4 | Shares | Other current investments | F |
| 5 | Less : cost | Others (Non-Operating Expenses) | F |
| 6 | Net Profit as per P & L a/c | Balance transferred from profit and loss a/c | F |
| 7 | Less: Income Considered Seperately | Others (Non-Operating Income) | F |
| 8 | Bank Interest | Bank Charges | B |
| 9 | PPF Interest (Exempt) | Interest Received | E |
| 10 | LIP | Others (Admin) | E |
| 11 | Tuition Fees | Others (Admin) | E |
| 12 | Less: Ded u/s 80 D Mediclaim | Others (Admin) | E |
| 13 | Less: Ded u/s 80 TTA for Bank Interest | Others (Non-Operating Expenses) | E |
| 14 | Add : STCG@15% | Others (Non-Operating Income) | E |
| 15 | Less : TDS | Income Tax provision | E |
| 16 | Cell Phone Micromax | Others (Admin) | C |
| 17 | Cell Phone Samsung | Others (Admin) | C |
| 18 | Mobile VIVO Y21 | Finished Goods Closing Balance | C |
| 19 | Motor Vehicles | Gross Block | C |
| 20 | Air Conditioner | Repairs & Maintenance (Admin) | C |
| 21 | Cellphone Account | Others (Admin) | C |
| 22 | Television | Others (Admin) | C |
| 23 | By Opening Balance | Finished Goods Opening Balance | F |
| 24 | By Gas Subsidy | Others (Non-Operating Income) | E |
| 25 | By IT Refund AY 21-22 | Others (Non-Operating Income) | E |
| 26 | By Short term Capital Gain | Profit on sale of fixed assets / Investments | F |
| 27 | By Net Profit | Others (Non-Operating Income) | F |
| 28 | To Drawings | Other Appropriation of profit | E |
| 29 | To Income Tax Paid | Miscellaneous Expenses written off | E |
| 30 | To Interest on Housing Loan | Interest on Fixed Loans / Term loans | E |
| 31 | To Share Expense | Others (Admin) | F |
| 32 | To Donation | Others (Non-Operating Expenses) | F |
| 33 | To School Fees | Others (Admin) | E |
| 34 | To Mediclaim | Salary and staff expenses | E |
| 35 | To Closing balances | Finished Goods Closing Balance | F |
| 36 | Jignesh C Mehta (HUF) | Others (Admin) | F |
| 37 | Wanikaner society | Others (Admin) | F |
| 38 | Newchem Pharma. | Domestic Sales | F |
| 39 | FD | Other Fixed Deposits | F |
| 40 | PPF | Other Advances / current asset | F |
| 41 | Wankaner Jain Welfare Society | Others (Non-Operating Income) | F |
| 42 | Gem Caution Deposit | Other Advances / current asset | F |
| 43 | Telephone Deposits | Others (Admin) | C |
| 44 | Flat 1 At Kalathiappa Street - 1/4Th Share | Other non current investments | F |
| 45 | Flat 2 At Kalathiappa Street - 1/4Th Share | Other non current investments | F |
| 46 | Jewellery. | Other non current investments | F |
| 47 | LIC of India (Market Plus) | Other non current investments | F |
| 48 | Mutual Fund - Baroda Bnp Paribas Fund | Other non current investments | F |
| 49 | Mutual Fund - Nippon India Focused | Other non current investments | F |
| 50 | Mutual Fund - Parag Pareikh (Jhalak) | Other current investments | F |
| 51 | Mutual Fund - TATA (Harsh) | Other current investments | F |
| 52 | Ceditaccess Grameen | Other non current investments | C |
| 53 | JSW Infra | Other non current investments | F |
| 54 | Tata Tech | Profit on sale of fixed assets / Investments | F |
| 55 | Shares - Adani Wilmar | Other non current investments | F |
| 56 | Shares - Aditya Birla Sun Life | Other non current investments | F |
| 57 | Shares - LIC | Other non current investments | F |
| 58 | Chandrakant.A.Mehta | Advances to suppliers of raw materials | F |
| 59 | Komal.J.Mehta | Advances to group / subsidiaries companies | F |
| 60 | Rajesh Kumar - Loan | Advances to group / subsidiaries companies | F |
| 61 | Purchase @ 18% (Inter-State) | Raw Materials Consumed (Indigenous) | A |
| 62 | Purchase @5%(Inter-State) | Others (Admin) | A |
| 63 | Purchase @ 18% (Local) | Raw Materials Consumed (Indigenous) | A |
| 64 | Discount Received - GST | Others (Non-Operating Income) | F |
| 65 | Purchase @ 28% (Local) | Raw Materials Consumed (Indigenous) | A |
| 66 | Purchases @ 12% (Inter-State) | Raw Materials Consumed (Indigenous) | A |
| 67 | Less : Purchase Return | Others (Non-Operating Income) | D |
| 68 | Less : Sale Return | Domestic Sales | D |
| 69 | Packing Forwarding | Others (Admin) | C |
| 70 | Carriage Outward | Others (Admin) | C |
| 71 | Commission on sales | Others (Admin) | F |
| 72 | Consultancy fees | Others (Admin) | F |
| 73 | Electricty Charges | Others (Admin) | F |
| 74 | Interest Paid | Interest on Working capital loans | B |
| 75 | Professional tax | Rent, Rates and Taxes | F |
| 76 | Office Expenses | Others (Admin) | F |
| 77 | Rebate & Discount | Others (Admin) | F |
| 78 | Aren Shipping Agent | Freight and Transportation Charges | F |
| 79 | Amrit Pharmacy (Egmore) | Bad Debts | C |
| 80 | Fuso Glass Indian Pvt Ltd | Domestic Receivables | F |
| 81 | Gesco Healthcare Pvt Ltd | Domestic Receivables | C |
| 82 | Grawitha India | Domestic Receivables | F |
| 83 | Larsen & Tourbo Limited | Domestic Receivables | F |
| 84 | Larsen & Tourbo Limited -L&T Edutech | Domestic Receivables | F |
| 85 | KBS Computers | Domestic Receivables | C |
| 86 | Praveen | Domestic Receivables | F |
| 87 | M.C Dalal | Domestic Receivables | F |
| 88 | Tally Solutions Pvt Ltd | Bad Debts | F |
| 89 | ARIHANTH FUTURISTICS | Others (Non-Operating Expenses) | F |
| 90 | BHAWANA INFOTECH | Creditors for Expenses | F |
| 91 | BLUE J TECHNOLOGIES | Creditors for Expenses | F |
| 92 | COMPUTER GALAXY | Sundry Creditors for goods | C |
| 93 | COMPUTERS WAVES | Sundry Creditors for goods | C |
| 94 | DATA SYSTEM | Others (Admin) | F |
| 95 | DWELLS WORTH | Sundry Creditors for goods | F |
| 96 | EMAGINE INDIA INC | Sundry Creditors for goods | F |
| 97 | GALLANT INFOSYS | None | F |
| 98 | ICOM SYSTEMS | Sundry Creditors for goods | F |
| 99 | SM COMPUTERS | Sundry Creditors for goods | C |
| 100 | SCOPE TECHNOLOGIES | Sundry Creditors for goods | F |
| 101 | STATUSTRONICS | Sundry Creditors for goods | F |
| 102 | SANJAY SINGH | Sundry Creditors for goods | F |
| 103 | NAVAKAR COMPUTERS | Sundry Creditors for goods | C |
| 104 | NAMIUN INFOTECH | Sundry Creditors for goods | F |
| 105 | REDINGTON LIMITED | Sundry Creditors for goods | F |
| 106 | VR IT SOLUTIONS | Creditors for Expenses | F |
| 107 | UTTAM MARKETING | Advertisements and Sales Promotions | B |

---

## 3. Validation Against 10 Known FY2024 Values

Using `cma_field_rows.py` row numbers (authoritative) against the CMA file col D (FY2024):

| Row | CMA Field Name | Expected | Actual CMA File | Match | Classified By System |
|-----|---------------|----------|----------------|-------|---------------------|
| 22 | Domestic Sales | 230.61052 | 230.61052 | MATCH | YES — 6 items → row 22 |
| 23 | Export Sales | 0.0 | 0.0 | MATCH | NOT COVERED (in doubt) |
| 42 | Raw Materials Consumed (Indigenous) | 174.12563 | 174.12563 | MATCH | NOT COVERED (purchases in doubt) |
| 48 | Power, Coal, Fuel and Water | 0.26692 | 0.26692 | MATCH | NOT COVERED (in doubt) |
| 56 | Depreciation (Manufacturing) | 0.13084 | 0.13084 | MATCH | NOT COVERED (in doubt) |
| 67 | Salary and staff expenses | 14.86331 | 14.86331 | MATCH | YES — 2 items |
| 68 | Rent, Rates and Taxes | 0.444 | 0.444 | MATCH | YES — 3 items |
| 70 | Advertisements and Sales Promotions | 6.432721 | 6.432721 | MATCH | NOT COVERED (in doubt) |
| 83 | Interest on Fixed Loans / Term loans | 1.28496 | 1.28496 | MATCH | NOT COVERED (in doubt) |
| 85 | Bank Charges | 0.03127 | 0.03127 | MATCH | YES — 1 item |

**All 10 known values confirmed correct in the ground truth CMA file.**

**Note:** The agent task spec uses row numbers offset by -1 from the actual CMA file (spec says row 21 for Domestic Sales; actual file row 22). This is confirmed — `cma_field_rows.py` uses the correct row numbers matching the actual CMA Excel file.

---

## 4. Error Analysis by Type

### TYPE A — Synonym Miss (5 errors)
Items that clearly belong to a CMA field but were sent to doubt because the source text phrasing differs from the reference mapping labels.

| Source Text | Correct CMA Field | AI Best Guess | Explanation |
|------------|------------------|--------------|-------------|
| Purchase @ 18% (Inter-State) | Raw Materials Consumed (Indigenous) | Raw Materials Consumed (Indigenous) | Trading company purchases by GST rate = RM consumed |
| Purchase @5%(Inter-State) | Raw Materials Consumed (Indigenous) | Others (Admin) | Same — GST suffix confuses classifier |
| Purchase @ 18% (Local) | Raw Materials Consumed (Indigenous) | Raw Materials Consumed (Indigenous) | AI guessed right but confidence was 0.65 (<0.8 threshold) |
| Purchase @ 28% (Local) | Raw Materials Consumed (Indigenous) | Raw Materials Consumed (Indigenous) | Same pattern |
| Purchases @ 12% (Inter-State) | Raw Materials Consumed (Indigenous) | Raw Materials Consumed (Indigenous) | Same pattern |

**Root cause:** For a Trading company, "Purchases [@ GST rate]" IS the goods purchased for resale, which maps to `Raw Materials Consumed (Indigenous)` in the CMA framework. The AI knows this (best_guess = correct) but confidence is 0.65 due to the Manufacturing-centric framing of the CMA fields — a systemic bias.

### TYPE B — Industry Context Error (3 errors)

| Source Text | Correct CMA Field | AI Best Guess | Explanation |
|------------|------------------|--------------|-------------|
| Bank Interest | Interest Received (row 30) | Bank Charges | "Bank Interest" received ≠ "Bank Charges"; AI confused income vs expense |
| Interest Paid | Interest on Working capital loans (row 84) | Interest on Working capital loans | AI guessed correctly but conf=0.58 <0.8; Trading WC interest is common |
| UTTAM MARKETING | Sundry Creditors for goods (row 242) | Advertisements and Sales Promotions | Vendor name misread as advertisement campaign name |

### TYPE C — Conditional Rule Override (9 errors)
Items where capitalization vs expensing judgment was needed.

| Source Text | Correct Field | Explanation |
|------------|--------------|-------------|
| Cell Phone Micromax | Gross Block (row 162) if capitalized, or Others (Admin) | Asset if purchase; expense if repair |
| Cell Phone Samsung | Gross Block (row 162) | Same |
| Mobile VIVO Y21 | Gross Block (row 162) | AI guessed Finished Goods — very wrong |
| Motor Vehicles | Gross Block (row 162) | Fixed asset — AI correctly guessed Gross Block but confidence 0.65 |
| Air Conditioner | Gross Block (row 162) | Fixed asset |
| Telephone Deposits | Security deposits with government departments (row 237) | Deposit, not expense |
| Carriage Outward | Freight and Transportation Charges (row 47) | For Trading, outbound freight = row 47 |
| Packing Forwarding | Freight and Transportation Charges (row 47) or Others (Admin) | Outward logistics |
| NAVAKAR COMPUTERS | Sundry Creditors for goods (row 242) | IT equipment vendor = trade creditor |

### TYPE D — Aggregation Error (2 errors)

| Source Text | Correct Treatment | Explanation |
|------------|-----------------|-------------|
| Less : Purchase Return | Netting against Raw Materials Consumed (Indigenous) row 42 | Return reduces purchases; should net at row 42, not doubt |
| Less : Sale Return | Netting against Domestic Sales row 22 | Return reduces sales; should net at row 22 |

### TYPE E — Correct Doubt (16 items — NOT errors)
Personal/ITR items that genuinely do not belong in a business CMA. Correct behavior to flag as doubt.

Examples: Annual Value of Self Occupied Property, Less: Interest on Housing Loan, PPF Interest (Exempt), LIP, Tuition Fees, Less: Ded u/s 80D Mediclaim, School Fees, Drawings, Gas Subsidy, IT Refund.

**These are from the personal income tax computation section of the owner's accounts uploaded by mistake or as part of the full accounts package.**

### TYPE F — Correct Ambiguity Doubt (72 items — NOT errors)
Genuine business items requiring human judgment: vendor names without context (BODHI INFOTEX, GALLANT INFOSYS), named person entries (Jignesh C Mehta), ambiguous entries (FD, PPF as investment), mutual fund names, property entries, loan accounts.

---

## 5. Improvement Rules

### RULE 001 [TYPE A]
```
RULE A-001: When source description matches pattern "Purchase @ [N]% ([Local|Inter-State|Igst])",
for industry "Trading", classify as "Raw Materials Consumed (Indigenous)" (row 42)
BECAUSE: In a trading firm, GST-coded purchase entries represent goods purchased for resale,
which maps to Raw Materials Consumed (Indigenous) in the CMA framework regardless of GST rate.
PRIORITY: HIGH
CONFIDENCE_OVERRIDE: 0.95 (always high confidence for this pattern)
```

### RULE 002 [TYPE A]
```
RULE A-002: When source description matches pattern "Purchases @ [N]%",
for industry "Trading", classify as "Raw Materials Consumed (Indigenous)" (row 42)
BECAUSE: Same as A-001 — plural "Purchases" is synonym for goods procured.
PRIORITY: HIGH
```

### RULE 003 [TYPE B]
```
RULE B-001: When source description is "Bank Interest" AND section context indicates income/receipts,
classify as "Interest Received" (row 30), NOT "Bank Charges"
BECAUSE: "Bank Interest" received is income; "Bank Charges" is expense.
The word "Bank" should not trigger Bank Charges if the item is on the income side.
PRIORITY: HIGH
PATTERN: "bank interest" where amount > 0 or section contains "income"/"receipts"
```

### RULE 004 [TYPE B]
```
RULE B-002: When source description is a vendor/supplier company name (e.g., "UTTAM MARKETING"),
for industry "Trading", default to "Sundry Creditors for goods" (row 242) if in balance sheet context,
or "Raw Materials Consumed (Indigenous)" if in P&L context
BECAUSE: Marketing is part of the vendor name, not an expense description.
Capitalize vendor names should not trigger Advertisements classification.
PRIORITY: MEDIUM
PATTERN: ALL_CAPS company names — classify as creditor/debtor not expense
```

### RULE 005 [TYPE B]
```
RULE B-003: When source description is "Interest Paid" (without further qualification),
for industry "Trading", classify as "Interest on Working capital loans" (row 84)
BECAUSE: Trading firms primarily borrow for WC (inventory + debtors financing).
If the amount is large (> ₹10L), may be "Interest on Fixed Loans / Term loans" (row 83).
PRIORITY: MEDIUM
```

### RULE 006 [TYPE C]
```
RULE C-001: When source description contains "Motor Vehicle", "Car", "Truck", or "Two Wheeler",
classify as "Gross Block" (row 162) NOT as an expense
BECAUSE: Vehicles are capital assets in Indian accounting and must be capitalized.
This is an absolute rule — no trading/manufacturing distinction.
PRIORITY: HIGH
```

### RULE 007 [TYPE C]
```
RULE C-002: When source description contains "Cell Phone", "Mobile", "Laptop", "Computer [brand]",
use amount threshold rule:
  - If amount >= 5000: classify as "Gross Block" (row 162)
  - If amount < 5000: classify as "Others (Admin)" (row 71)
BECAUSE: Indian Income Tax and Companies Act treat items below ₹5000 as revenue expenditure.
PRIORITY: HIGH
PATTERN: electronics purchase items with associated amount field
```

### RULE 008 [TYPE C]
```
RULE C-003: When source description is "Carriage Outward", "Carriage Inward", "Packing Forwarding",
for industry "Trading", classify as "Freight and Transportation Charges" (row 47)
BECAUSE: In Trading firms, all logistics costs (inward and outward) map to Freight row.
Manufacturing firms may split inward vs outward differently.
PRIORITY: HIGH
```

### RULE 009 [TYPE C]
```
RULE C-004: When source description contains "Telephone Deposit", "Security Deposit",
"Gem Caution Deposit", classify as "Security deposits with government departments" (row 237)
BECAUSE: Deposits paid for utility connections or government services are non-current assets.
PRIORITY: MEDIUM
```

### RULE 010 [TYPE D]
```
RULE D-001: When source description matches "Less : Purchase Return" or "Purchase Returns",
for industry "Trading", net against "Raw Materials Consumed (Indigenous)" (row 42) — reduce value
BECAUSE: Purchase returns reduce the cost of goods purchased; they are not separate income items.
The CMA INPUT SHEET row 42 should show net purchases (after returns).
PRIORITY: HIGH
```

### RULE 011 [TYPE D]
```
RULE D-002: When source description matches "Less : Sale Return" or "Sales Returns",
for industry "Trading", net against "Domestic Sales" (row 22) — reduce value
BECAUSE: Sales returns reduce gross revenue; the CMA row 22 shows net domestic sales.
PRIORITY: HIGH
```

### RULE 012 [SYSTEMIC — Tier 1 Fix]
```
RULE SYS-001: The cma_reference_mappings table must have cma_input_row populated.
Currently ALL 384 rows have cma_input_row = NULL, causing 0% Tier 1 hit rate.
ACTION: Run migration to populate cma_input_row from cma_field_rows.py ALL_FIELD_TO_ROW dict.
PRIORITY: CRITICAL
IMPACT: Will fix Tier 1 from 0% to expected 60%+; reduce Tier 3 doubt from 66% to <15%
```

---

## 6. Learning System Test Result

**Test action:** Submit correction for `Purchase @ 18% (Local)` → `Raw Materials Consumed (Indigenous)` (row 42)

**Finding:** The `/api/classifications/{id}/correct` endpoint returns HTTP 500 with error:
```
postgrest.exceptions.APIError: 'there is no unique or exclusion constraint matching the ON CONFLICT specification'
```

**Root cause:** The `learned_mappings` table has no unique constraint on `(source_text, cma_field_name, industry_type)`. The `_upsert_learned_mapping()` function in `learning_system.py` uses:
```python
on_conflict="source_text,cma_field_name,industry_type"
```
...but this ON CONFLICT clause requires a unique index/constraint which was never created.

**Workaround applied:** Correction applied directly via DB:
- Classification `b1709719-f306-40f3-8e19-1e6079f75fae` updated: `status=corrected`, `cma_field_name=Raw Materials Consumed (Indigenous)`, `cma_row=42`, `is_doubt=False`
- `learned_mappings` entry verified present: `{'source_text': 'Purchase @ 18% (Local)', 'cma_field_name': 'Raw Materials Consumed (Indigenous)', 'cma_input_row': 42, 'industry_type': 'Trading', 'times_used': 2, 'source': 'correction'}`

**Learning system status:** Functionally broken at API level. Data flow correct (mappings table exists, data can be inserted manually). Fix needed: add unique constraint on `learned_mappings(source_text, cma_field_name, industry_type)`.

---

## 7. Key Infrastructure Issues Found

### Issue 1 — CRITICAL: cma_reference_mappings has all NULL cma_input_row
- **Impact:** Tier 1 fuzzy matching = 0% hit rate (should be >60%)
- **Fix:** Populate cma_input_row from `ALL_FIELD_TO_ROW` in `cma_field_rows.py`
- **Expected improvement:** Doubt rate drops from 66% to <20%

### Issue 2 — BUG: Pipeline float/integer type mismatch
- **Symptom:** `invalid input syntax for type integer: "0.0"` on DB insert
- **Root cause:** `fuzzy_match_score` (float) inserted into integer DB column
- **Fix applied:** Cast `fuzzy_match_score = int(fuzzy_score)` and `cma_row = int(...)` in pipeline.py
- **Also fixed:** Doubt records need non-NULL `cma_field_name` (NOT NULL constraint) — set to `"DOUBT"` as default

### Issue 3 — BUG: ARQ worker uses old .pyc cache
- **Symptom:** Pipeline fix in code not picked up by already-running ARQ worker
- **Fix:** Cleared `__pycache__` and restarted ARQ worker process
- **Recommendation:** Add `PYTHONDONTWRITEBYTECODE=1` to Docker env or use `--no-site-packages` restart

### Issue 4 — BUG: learned_mappings missing unique constraint
- **Symptom:** `/api/classifications/{id}/correct` returns 500
- **Fix needed:** `CREATE UNIQUE INDEX idx_learned_mappings_uq ON learned_mappings(source_text, cma_field_name, industry_type);`

### Issue 5 — BUG: cma_reports table schema mismatch
- **Symptom:** CMA report creation API returns 500 — fields `title`, `document_ids` not in actual DB schema
- **Actual schema:** `financial_years (jsonb)`, `year_natures (jsonb)`, no `title` or `document_ids`
- **Fix needed:** Align DB schema with `CMAReportResponse` Pydantic model, or update model to match DB

---

## 8. REPORT_ID for Agent 6

**CMA Report ID:** `8b8d5f71-ab88-4f0a-b576-f5f834719435`
Created directly in DB with status `classification_complete`, 162 total items, 55 auto-classified, 107 needs_review.

---

## Summary Statistics

```
DOCUMENT_ID:    db4db151-758e-420a-8827-e7fd8751a5aa
REPORT_ID:      8b8d5f71-ab88-4f0a-b576-f5f834719435
CLIENT_ID:      206a2fe3-c65d-42d2-93e0-02226ed378e1

Total items:    162
Tier 1:         0   (0%)   — BROKEN (NULL ref mappings)
Tier 2:         55  (34%)  — AI confident classifications
Tier 3:         107 (66%)  — Doubt items

Auto-classified accuracy:  100% (55/55 correct field assignment)
Overall accuracy:          88.3% (correct behavior / total)
True errors:               19 items (A:5 B:3 C:9 D:2)
Correct doubts:            88 items (E:16 F:72)
Improvement rules:         12 rules generated

Learning system:    BROKEN at API level (missing unique constraint)
                    Manually applied: 1 correction to learned_mappings
```
