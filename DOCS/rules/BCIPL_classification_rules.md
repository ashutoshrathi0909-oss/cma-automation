# BCIPL Classification Rules

**Company:** Bagadia Chaitra Industries Private Limited
**Industry:** Manufacturing (Metal Stamping / Laminations — CRCA Sheets & Coils, Aluminium)
**Location:** KIADB Industrial Area, Tumakuru, Karnataka
**Financial Years Covered:** FY2020-21, FY2021-22, FY2022-23
**Total Line Items Analysed:** 1,656 (across 3 years, all sheets)
**Number of New Rules Generated:** 22
**Items Already Covered by Existing Reference/Rules:** ~180 (items matching the 384-item reference or V1 rules directly)

**Source Files:**
- `FInancials main/BCIPL/6. BCIPL_ Final Accounts_2020-21.xls`
- `FInancials main/BCIPL/6. BCIPL_ Final Accounts_2021-22.xls`
- `FInancials main/BCIPL/BCIPL_ FY 2023 Final Accounts_25092023.xls`
- `FInancials main/BCIPL/CMA BCIPL 12012024.xls` (ground truth)

---

## Summary of Key Differences from Trading Firm (Mehta Computers)

| Aspect | Mehta Computers (Trading) | BCIPL (Manufacturing) |
|--------|--------------------------|----------------------|
| Revenue | "Purchase @ 18%" style entries | "Sales of Manufactured Products" + "Sales of Trading Goods" + "Job Work Charges" |
| Raw Materials | Simple purchases for resale | Opening stock + Purchases - Closing stock formula |
| Inventory | Just stock-in-trade | Raw Materials + WIP + Finished Goods + Tools + Scrap |
| Wages | None (no factory) | Factory wages, PF, ESIC, Gratuity, Labour Welfare — all separate |
| Depreciation | Minimal (electronics) | Heavy (machinery, factory building, tools & dies) |
| Borrowings | Simple CC/OD | Term loans + Channel Finance + Sellers Credit + ECGS + Vehicle loans |
| Selling expenses | Simple freight | Carriage outward + Packing materials + Scrap handling |

---

## RULE BCIPL-001 — Directors Remuneration: Split from Employee Benefits

**Applies to:** Manufacturing, All industries

**Pattern it catches:**
- `Directors Remuneration`
- `Director Remuneration`
- `Managing Director Remuneration`
- `Directors' Salary`

**Classification:** Salary and staff expenses → Row 67

**Why this rule exists:**
In manufacturing financial statements, "Employee Benefits Expense" is reported as a SINGLE total
that includes both factory wages AND directors' remuneration. The CMA requires them separated:
- Factory wages/salaries/PF/ESIC/welfare → **Wages (Row 45)** (Cost of Sales)
- Directors' remuneration → **Salary and staff expenses (Row 67)** (Admin)

Without this rule, the entire Employee Benefits total would go to Wages, overstating Cost of Sales.
The AI might also confuse "Directors Remuneration" with "Salary" and put it in Wages.

**Real example from BCIPL FY2020-21:**
```
Source text:   "Directors Remuneration"  (subnote under Salaries & Wages)
Amount:        ₹30,00,000
Correct field: Salary and staff expenses  [Row 67]
Wrong result:  Wages [Row 45] (if grouped with other employee expenses)
```

**Real example from BCIPL FY2022-23:**
```
Source text:   "Directors Remuneration"
Amount:        ₹1,25,50,000
Correct field: Salary and staff expenses  [Row 67]
```

**Verify:** Do you agree Directors Remuneration should always go to Row 67 (Admin), not Row 45 (Wages)?
- [ ] Yes, correct   - [ ] No, exception: _______________________

---

## RULE BCIPL-002 — Scrap / Other Materials Consumed: Net Against Stores & Spares

**Applies to:** Manufacturing only

**Pattern it catches:**
- `Other Materials Consumed`
- `Scrap Consumption`
- `Scrap` (when negative or under "Other Materials")
- `Less: Scrap`

**Classification:** Stores and spares consumed (Indigenous) → Row 44 (netted as negative)

**Why this rule exists:**
In manufacturing, "Other Materials Consumed" often refers to scrap material that gets consumed or
offset against stores. The CMA ground truth shows the CA NETTED this value against Stores & Spares:

FY2020-21: Stores & Spares (₹1,77,40,031) + Other Materials (-₹1,11,230) = ₹1,76,28,801 = CMA Row 44

The 384-item reference has NO entry for "Other Materials Consumed" or "Scrap Consumption".
Without this rule, scrap would go to DOUBT or be misclassified as a separate expense.

**Real example from BCIPL FY2020-21:**
```
Source text:   "Other Materials Comsumed - Scrap"  (Note 21)
Amount:        -₹1,11,230  (negative)
Correct field: Stores and spares consumed (Indigenous) [Row 44]  (netted)
CMA value:     ₹1,76,28,801 = Stores ₹1,77,40,031 + Scrap -₹1,11,230
```

**Verify:** Do you agree scrap/other materials should net against Stores & Spares?
- [ ] Yes, correct   - [ ] No, exception: _______________________

---

## RULE BCIPL-003 — Job Work Charges (Paid): Processing / Job Work Charges

**Applies to:** Manufacturing only

**Pattern it catches:**
- `Job Work Charges`
- `Job Work Charges & Contract Labour`
- `Contract Labour`
- `Job Work Paid`
- `Processing Charges`

**Classification:** Processing / Job Work Charges → Row 46

**Why this rule exists:**
The 384-item reference maps "Job Work Charges paid" to "Item 5(v): Other manufacturing expenses"
which is **Row 49 (Others Manufacturing)**. But the BCIPL CMA ground truth maps it to **Row 46
(Processing / Job Work Charges)** — a dedicated CMA field for exactly this expense.

In manufacturing, job work is a direct production cost (outsourced manufacturing steps), not
"other" manufacturing. Row 46 is the correct, more specific field.

**Real example from BCIPL FY2020-21:**
```
Source text:   "Job Work Charges & Contract Labour"  (Note 26)
Amount:        ₹1,21,69,220
Correct field: Processing / Job Work Charges  [Row 46]
384-ref says:  Others (Manufacturing)  [Row 49]  ← OVERRIDE THIS
```

**Verify:** Do you agree Job Work Charges should go to Row 46 (Processing), not Row 49 (Others Mfg)?
- [ ] Yes, correct   - [ ] No, keep at Row 49: _______________________

---

## RULE BCIPL-004 — Selling & Distribution Expenses → Advertisements Row

**Applies to:** Manufacturing, All industries

**Pattern it catches:**
- `Selling & Distribution Expenses`
- `Selling and Distribution`
- `Carriage Outwards`
- `Packing Materials`
- `Packing and Forwarding`
- `Discount Allowed` (when under selling expenses)
- `Scrap Loading & Unloading Charges`

**Classification:** Advertisements and Sales Promotions → Row 70

**Why this rule exists:**
"Advertisements and Sales Promotions" (Row 70) is the CMA catch-all field for ALL selling expenses,
not just advertising. The name is misleading. In manufacturing, the main selling expenses are:
- Carriage Outward (freight to customers)
- Packing Materials (GST @ 12% and 18%)
- Discount Allowed
- Scrap Loading & Unloading

The 384-ref correctly maps "Selling & Distribution expenses → Item 6: SGA" but doesn't specify
which SGA sub-row. The CMA ground truth consistently uses Row 70.

**Real example from BCIPL FY2022-23:**
```
Source text:   "Selling & Distribution Expenses"
Amount:        ₹4,54,15,946
Correct field: Advertisements and Sales Promotions  [Row 70]
Breakdown:     Carriage Outwards ₹2,99,88,329
               Packing Materials 12% ₹71,03,358
               Packing Materials 18% ₹42,75,087
               Scrap Loading ₹39,97,979
               Discount Allowed ₹51,192
```

**Sub-items that also go to Row 70:**
```
"Carriage Outwards"           → Row 70  (NOT Row 47 Freight - that's for inward freight)
"Packing Materials"           → Row 70
"Scrap Loading & Unloading"   → Row 70
"Discount Allowed"            → Row 70  (when under selling expenses)
```

**Verify:** Do you agree all selling/distribution expenses go to Row 70 (Advertisements)?
- [ ] Yes, correct   - [ ] No, some should go elsewhere: _______________________

---

## RULE BCIPL-005 — Bill Discounting Charges → Working Capital Interest

**Applies to:** All industries

**Pattern it catches:**
- `Bill Discounting Charges`
- `Bill Discounting`
- `Discount on Bills`

**Classification:** Interest on Working capital loans → Row 84

**Why this rule exists:**
Bill discounting is when a company gets early payment from a bank by "selling" customer invoices
at a discount. The discount charged is effectively interest on working capital. The 384-item
reference does NOT have this item. Without this rule, it would go to DOUBT.

The CMA ground truth consistently classifies bill discounting charges as working capital interest,
separate from term loan interest.

**Real example from BCIPL FY2020-21:**
```
Source text:   "Bill Discounting Charges"  (under Finance Costs, Note 24)
Amount:        ₹65,04,465
Correct field: Interest on Working capital loans  [Row 84]
Wrong guess:   Bank Charges [Row 85] or DOUBT
```

**Real example from BCIPL FY2022-23:**
```
Source text:   "Bill Discounting Charges"
Amount:        ₹1,89,22,324
Correct field: Interest on Working capital loans  [Row 84]
```

**Verify:** Do you agree Bill Discounting Charges = Interest on Working Capital?
- [ ] Yes, correct   - [ ] No, exception: _______________________

---

## RULE BCIPL-006 — Interest on Unsecured Loan → Term Loan Interest

**Applies to:** All industries

**Pattern it catches:**
- `Interest Paid on Unsecured Loan`
- `Interest on Unsecured Loan`
- `Interest on Directors Loan`
- `Interest on Promoter Loan`

**Classification:** Interest on Fixed Loans / Term loans → Row 83

**Why this rule exists:**
When directors/promoters lend money to the company (as unsecured loans), the interest paid on
these loans is classified as term loan interest (Row 83), not working capital interest (Row 84).

The 384-ref has "Interest on unsecured loans from friends and relatives → Interest" but doesn't
specify Row 83 vs Row 84. The CMA ground truth puts it in Row 83.

**Real example from BCIPL FY2020-21:**
```
Source text:   "Interest Paid on Unsecured Loan"  (Note 24)
Amount:        ₹14,75,862
Correct field: Interest on Fixed Loans / Term loans  [Row 83]
```

**Verify:** Do you agree interest on unsecured loans goes to Row 83 (Fixed/Term)?
- [ ] Yes, correct   - [ ] No, it should go to Row 84 (WC): _______________________

---

## RULE BCIPL-007 — Interest on CC/OD Account → Term Loan Interest

**Applies to:** All industries (when CC/OD interest is small relative to total)

**Pattern it catches:**
- `Interest on C.C. A/c`
- `Interest on Cash Credit`
- `Interest on OD`
- `Interest on Overdraft`

**Classification:** Interest on Fixed Loans / Term loans → Row 83

**Why this rule exists:**
Technically, CC/OD interest should go to Working Capital Interest (Row 84). However, the BCIPL
CMA ground truth shows the CA combined CC interest with term loan interest in Row 83.

FY2020-21: CC Interest (₹21,049) + TL Interest (₹1,15,16,847) + Unsecured Interest (₹14,75,862)
= ₹1,30,13,758 = CMA Row 83 ✓

This may be because the CC interest was negligible (₹21K vs ₹1.3 Cr total). For firms where
CC/OD interest is substantial, this rule should be overridden.

**Real example from BCIPL FY2020-21:**
```
Source text:   "Interest on C.C.  A/c"
Amount:        ₹21,049
Correct field: Interest on Fixed Loans / Term loans  [Row 83]
Note:          In FY2022-23, CC interest grew to ₹69,52,054 and was STILL in Row 83
```

**Verify:** Do you agree CC/OD interest goes to Row 83 with term loan interest?
- [ ] Yes, correct   - [ ] No, CC interest should go to Row 84 (WC): _______________________

---

## RULE BCIPL-008 — Channel Financing → Working Capital Bank Finance

**Applies to:** All industries

**Pattern it catches:**
- `Channel Financ` (matches Channel Finance, Channel Financing)
- `Supply Chain Finance`
- `Vendor Financing`

**Classification:** Working Capital Bank Finance - Bank 1 → Row 131

**Why this rule exists:**
"Channel Financing" is a bank product where the bank pays the company's suppliers directly and
the company repays the bank later. It's a form of working capital borrowing, NOT a term loan.

The 384-ref doesn't have this item. Without this rule, the AI might classify "Axis Bank Channel
Financing" as a term loan because it contains "Axis Bank" + "Loan" context.

**Real example from BCIPL FY2020-21:**
```
Source text:   "Axis Bank Channel Financing"  (Note 5: Short-Term Borrowings)
Amount:        ₹5,14,98,578
Correct field: Working Capital Bank Finance - Bank 1  [Row 131]

Source text:   "Yes Bank Channel Finance"
Amount:        ₹5,97,99,035
Correct field: Working Capital Bank Finance - Bank 1  [Row 131]
```

**Note:** When multiple banks provide working capital, aggregate into Bank 1 (Row 131).
Use Bank 2 (Row 132) only when the CMA needs to show separate bank limits.

**Verify:** Do you agree channel financing = Working Capital, not Term Loan?
- [ ] Yes, correct   - [ ] No, exception: _______________________

---

## RULE BCIPL-009 — Inland LC Discounting → Working Capital (Others)

**Applies to:** All industries

**Pattern it catches:**
- `Inland LC`
- `LC Discounting`
- `Letter of Credit Discounting`
- `In Land LC`

**Classification:** Working Capital Bank Finance - From Others → Row 132

**Why this rule exists:**
LC discounting is when a company discounts (sells) Letters of Credit to a bank for immediate
cash. It's working capital financing but often from a different facility than regular CC/OD.

The CMA ground truth shows BCIPL's Inland LC Discounting under "From Others" (Row 132),
separate from the main bank working capital (Row 131).

**Real example from BCIPL FY2020-21:**
```
Source text:   "Inland LC Discounting"  (Note 5)
Amount:        ₹89,75,441
Correct field: Working Capital Bank Finance - From Others  [Row 132]
```

**Verify:** Do you agree LC discounting = Working Capital (Others)?
- [ ] Yes, correct   - [ ] No, exception: _______________________

---

## RULE BCIPL-010 — Unsecured Loans from Directors → Quasi Equity

**Applies to:** All industries (Private Limited Companies)

**Pattern it catches:**
- Director/promoter names as loan accounts (e.g., `Mr. Chaitra Sundaresh`, `Mrs. Ronak S. Bagadia`)
- `Loans from Directors`
- `Director Loan`
- `Promoter Loan`
- `Due to Directors`
- Located in Unsecured Loans section of Balance Sheet

**Classification:** Unsecured Loans - Quasi Equity → Row 152

**Why this rule exists:**
In Indian private companies, directors/promoters often lend personal funds to the company.
Banks consider these loans as "quasi equity" (almost like owner's capital) because they are
subordinated to bank debt. The CMA specifically tracks these in Row 152.

The 384-ref doesn't have this distinction. Without this rule, director loans might go to
"Long Term Debt" (Row 153) or "Short Term Debt" (Row 154), which overstates the company's
real debt burden.

**Real example from BCIPL FY2020-21:**
```
Source text:   "Mr. Chaitra Sundaresh"  (Unsecured Loans - Due to Directors)
Amount:        ₹1,24,00,000

Source text:   "Mrs. Ronak S. Bagadia"
Amount:        ₹1,94,01,126

Source text:   "Mr. Nishanth Sunderesh"
Amount:        ₹96,32,173

Total:         ₹4,14,33,299
Correct field: Unsecured Loans - Quasi Equity  [Row 152]
CMA value:     4.1313 Cr ✓  (minor rounding)
```

**Verify:** Do you agree all director/promoter unsecured loans = Quasi Equity?
- [ ] Yes, correct   - [ ] No, some should be Long Term Debt: _______________________

---

## RULE BCIPL-011 — ECGS / ECLGS Loans → Term Loans

**Applies to:** Manufacturing, Exporting firms

**Pattern it catches:**
- `ECGS` (Export Credit Guarantee Scheme)
- `ECLGS` (Emergency Credit Line Guarantee Scheme)
- `ECLGC` (Emergency Credit Line Guarantee Corporation)

**Classification:**
- Non-current portion → Term Loan Balance Repayable after one year → Row 137
- Current portion → Term Loan Repayable in next one year → Row 136

**Why this rule exists:**
ECGS and ECLGS are government-guaranteed lending schemes. Banks provide these as term loans
with government guarantee. The AI might not recognize these acronyms and send them to DOUBT.

**Real example from BCIPL FY2020-21:**
```
Source text:   "Axis Bank ECGS A/C NO:920060046321519"
Amount:        ₹2,87,06,957  (full amount in non-current)
Correct field: Term Loan Balance Repayable after one year  [Row 137]
```

**Real example from BCIPL FY2022-23:**
```
Source text:   "Axis Bank ELGC A/C NO:920060046321519"
Amount:        Non-current ₹23,75,022 + Current ₹94,99,992
Correct field: Row 137 (non-current) + Row 136 (current)
```

**Verify:** Do you agree ECGS/ECLGS loans are always Term Loans?
- [ ] Yes, correct   - [ ] No, exception: _______________________

---

## RULE BCIPL-012 — Sellers Credit (Import Financing) → Term Loans

**Applies to:** Manufacturing, Importing firms

**Pattern it catches:**
- `Sellers Credit`
- `Suppliers Credit`
- `Buyers Credit`
- Followed by foreign company names (e.g., `Fongei`, `Ming Xu`, `Fair Oaks`, `KENT`)

**Classification:**
- Non-current portion → Term Loan Balance Repayable after one year → Row 137
- Current portion → Term Loan Repayable in next one year → Row 136

**Why this rule exists:**
"Sellers Credit" is a trade finance product where a foreign bank/entity finances the import of
machinery or goods, and the Indian company repays over time (typically 36 months). Despite being
import-related, these are structured as term loans in the CMA.

The 384-ref doesn't cover this banking product. The AI would likely send "Axis Bank Sellers
Credit Fongei" to DOUBT because "Sellers Credit" is an unusual term.

**Real example from BCIPL FY2020-21:**
```
Source text:   "Axis Bank Sellers Credit Fongei - I"
Amount:        ₹50,19,756
Correct field: Term Loan  [Row 137]

Source text:   "Axis Bank Suppliers Credit - Fair Oaks"
Amount:        ₹2,28,40,532
Correct field: Term Loan  [Row 137]
```

**Verify:** Do you agree Sellers/Suppliers Credit = Term Loans?
- [ ] Yes, correct   - [ ] No, exception: _______________________

---

## RULE BCIPL-013 — Forex Rate Fluctuation → Gain or Loss

**Applies to:** All industries (firms with foreign currency transactions)

**Pattern it catches:**
- `Forex Rate Fluctuation` (gain or loss determined by sign)
- `Foreign Exchange Fluctuation`
- `Exchange Rate Difference`
- `Forex Gain/Loss`

**Classification:**
- If positive (gain) → Gain on Exchange Fluctuations → Row 32
- If negative (loss) → Loss on Exchange Fluctuations → Row 91

**Why this rule exists:**
The 384-ref has "Foreign Exchange expenditure → Other non-operating expenses" and "Foreign Exchange
earning → Non-operating income" but uses generic field names. The CMA has SPECIFIC fields:
Row 32 (Gain on Exchange Fluctuations) and Row 91 (Loss on Exchange Fluctuations).

The same line item can flip between gain and loss across years (FY21: loss ₹16.4L, FY22: gain ₹14.7L).
The classification depends on the SIGN, not just the description.

**Real example from BCIPL:**
```
FY2020-21:  "Forex Rate Fluctuation Loss (Net)"  → ₹16,44,770 (loss)
            Correct: Loss on Exchange Fluctuations  [Row 91]

FY2021-22:  "Forex Rate Fluctuation Gain/(Loss)"  → ₹14,70,654 (gain)
            Correct: Gain on Exchange Fluctuations  [Row 32]
```

**Verify:** Do you agree forex fluctuations are sign-dependent (Row 32 vs Row 91)?
- [ ] Yes, correct   - [ ] No, exception: _______________________

---

## RULE BCIPL-014 — Testing Fees / Manufacturing Expenses → Others (Manufacturing)

**Applies to:** Manufacturing only

**Pattern it catches:**
- `Testing Fees`
- `Weighment Charges`
- `Manufacturing Expenses` (as a sub-category, not the broad CMA section)
- `Quality Testing`

**Classification:** Others (Manufacturing) → Row 49

**Why this rule exists:**
These are factory-specific expenses that don't fit any named manufacturing CMA field. They are
small amounts but need to go to "Others (Manufacturing)" Row 49, not admin expenses.

**Real example from BCIPL FY2022-23:**
```
Source text:   "Testing Fees"  (Subnotes to PL, under Manufacturing Expenses)
Amount:        ₹3,30,910

Source text:   "Weighment Charges"
Amount:        ₹100

Correct field: Others (Manufacturing)  [Row 49]
```

**Verify:** Do you agree testing/weighment charges = Others (Manufacturing)?
- [ ] Yes, correct   - [ ] No, exception: _______________________

---

## RULE BCIPL-015 — Machinery Maintenance → Repairs & Maintenance (Manufacturing)

**Applies to:** Manufacturing only

**Pattern it catches:**
- `Machinery Maintenance`
- `Machine Maintenance`
- `Plant Maintenance`
- `Factory Maintenance`
- `Purchase - Machinery Maintenance`

**Classification:** Repairs & Maintenance (Manufacturing) → Row 50

**Why this rule exists:**
The 384-ref maps "Machinery Maintenance → Item 5(v): Other manufacturing expenses" which is Row 49.
But the CMA has a specific field "Repairs & Maintenance (Manufacturing)" at Row 50.

The BCIPL ground truth maps Machinery Maintenance to Row 50 (CMA field "Repairs & Maintenance
Manufacturing") in FY22/23 — the correct, more specific field.

**Real example from BCIPL FY2022-23:**
```
Source text:   "Machinery Maintenance"  (Note 27)
Amount:        ₹41,77,378
Correct field: Repairs & Maintenance (Manufacturing)  [Row 50]
384-ref says:  Others (Manufacturing) [Row 49]  ← OVERRIDE
```

**Verify:** Do you agree Machinery Maintenance → Row 50 (R&M Mfg), not Row 49 (Others Mfg)?
- [ ] Yes, correct   - [ ] No, keep at Row 49: _______________________

---

## RULE BCIPL-016 — Capital Advances → Advances to Suppliers of Capital Goods

**Applies to:** All industries

**Pattern it catches:**
- `Capital Advance`
- Advances to foreign machinery suppliers (e.g., `MING XU`, `FAIR OAKES`, `CHINA INTERNATIONAL`)
- Advances under "Capital Work in Progress" section

**Classification:** Advances to suppliers of capital goods → Row 236

**Why this rule exists:**
When a company makes advance payments for machinery imports or construction, these are non-current
assets. The 384-ref doesn't specifically cover "Capital Advances". Without this rule, advances
to foreign companies might be classified as trade advances (Row 220) or sent to DOUBT.

**Real example from BCIPL FY2020-21:**
```
Source text:   "MING XU (DONGGUAN) PRECISION MACHINERY CO"  (Capital Advances)
Amount:        ₹87,34,537

Source text:   "FAIR OAKES PRECISION MACHINERY CO. LTD."
Amount:        ₹73,970

Total Capital Advances: ₹1,17,02,349
Correct field: Advances to suppliers of capital goods  [Row 236]
CMA value:     1.1702 Cr ✓
```

**Verify:** Do you agree capital advances go to Row 236 (Non-Current)?
- [ ] Yes, correct   - [ ] No, exception: _______________________

---

## RULE BCIPL-017 — GST Input Recoverable → Advances Recoverable

**Applies to:** All industries

**Pattern it catches:**
- `GST Input Recoverable`
- `GST Input Credit`
- `IGST Receivable`
- `CGST Receivable`
- `SGST Receivable`
- `Duties & Taxes` (debit balance under current assets)

**Classification:** Advances recoverable in cash or in kind → Row 219

**Why this rule exists:**
GST input credit is a current asset (government owes you money). The 384-ref doesn't cover GST
items. The CMA ground truth puts it in "Advances recoverable in cash or in kind" (Row 219).

**Real example from BCIPL FY2020-21:**
```
Source text:   "GST Input Recoverable"  (Note 17: Other Current Assets)
Amount:        ₹4,25,099
Correct field: Advances recoverable in cash or in kind  [Row 219]
CMA value:     0.0425 Cr ✓
```

**Verify:** Do you agree GST input credit goes to Row 219 (Advances recoverable)?
- [ ] Yes, correct   - [ ] No, it should go elsewhere: _______________________

---

## RULE BCIPL-018 — Electronic Cash Ledger → Security Deposits (Govt)

**Applies to:** All industries

**Pattern it catches:**
- `Electronic Cash Ledger`
- `Electronic Credit Ledger`
- `GST Electronic Ledger`

**Classification:** Security deposits with government departments → Row 237

**Why this rule exists:**
The GST Electronic Cash Ledger is a pre-deposit with the government for GST payments. It's
treated as a security deposit with a government department in the CMA.

The 384-ref doesn't cover this GST-era item. The existing V1 Rule C-004 covers "GEM Caution
Deposit" and "Electricity Deposit" but not GST Electronic Ledger.

**Real example from BCIPL FY2020-21:**
```
Source text:   "Electronic Cash Ledger"  (under Deposits)
Amount:        ₹1,72,928
Correct field: Security deposits with government departments  [Row 237]
```

**Verify:** Do you agree Electronic Cash Ledger = Security Deposit (Govt)?
- [ ] Yes, correct   - [ ] No, exception: _______________________

---

## RULE BCIPL-019 — MAT Credit Entitlement → Other Non-Current Assets

**Applies to:** All industries (companies paying Minimum Alternate Tax)

**Pattern it catches:**
- `MAT Credit Entitlement`
- `MAT Credit`
- `Minimum Alternate Tax Credit`

**Classification:** Other non current assets → Row 238

**Why this rule exists:**
MAT Credit is a long-term asset that can be set off against regular income tax in future years.
It's classified as a non-current asset. The 384-ref doesn't have this item.

**Real example from BCIPL FY2020-21:**
```
Source text:   "MAT Credit Entitlement"  (Note 12: Other Non-Current Assets)
Amount:        ₹2,66,591 (opening) + ₹29,29,119 (credit availed) - ₹31,95,710 (set off)
Correct field: Other non current assets  [Row 238]
```

**Verify:** Do you agree MAT Credit = Other Non-Current Asset?
- [ ] Yes, correct   - [ ] No, exception: _______________________

---

## RULE BCIPL-020 — Creditors for Capital Goods → Other Current Liabilities

**Applies to:** All industries

**Pattern it catches:**
- `Creditors for Capital Goods`
- `Creditors for Fixed Assets`
- `Creditors for Fixed Assets Purchased`
- `Creditors for Machinery`

**Classification:** Other current liabilities → Row 250

**Why this rule exists:**
Outstanding payments for machinery/equipment purchases are NOT trade creditors (Row 242).
They are "Other current liabilities" (Row 250). The 384-ref doesn't distinguish between
creditors for goods vs capital goods.

If misclassified as Sundry Creditors (Row 242), it inflates the trade creditor figure and
distorts working capital calculations.

**Real example from BCIPL FY2020-21:**
```
Source text:   "Creditors for Capital Goods"  (Note 7)
Amount:        ₹15,55,591  (CREAZIONE TOOLS, ELRKE, IMPACT MACHINES)
Correct field: Other current liabilities  [Row 250]
Wrong result:  Sundry Creditors for goods [Row 242]
```

**Verify:** Do you agree creditors for capital goods ≠ trade creditors?
- [ ] Yes, correct   - [ ] No, exception: _______________________

---

## RULE BCIPL-021 — Statutory Dues (Bonus, ESI, PF, TDS) → Other Statutory Liabilities

**Applies to:** All industries

**Pattern it catches:**
- `Bonus Payable`
- `Employee State Insurance` / `ESI Payable`
- `Provident Fund Payable` / `EPF Payable`
- `EPS Payable`
- `G.S.T. Payable`
- `Profession Tax Payable`
- `Tax Deducted at Source` (payable, under liabilities)
- `TDS Payable`

**Classification:** Other statutory liabilities (due within 1 year) → Row 246

**Why this rule exists:**
These are amounts owed to government authorities (PF/ESI/GST/TDS) that must be remitted within
statutory deadlines. The CMA aggregates them into "Other statutory liabilities" Row 246.

The AI might confuse "Bonus Payable" with an expense item, or "EPF Payable" with employee
benefits. These are LIABILITIES, not expenses.

**Real example from BCIPL FY2020-21:**
```
Statutory Dues aggregate:
  Bonus Payable:           ₹22,79,234
  ESI Payable:             ₹1,97,405
  PF Payable:              ₹7,62,538
  EPS & Other Charges:     ₹4,25,324
  GST Payable:             ₹630
  Profession Tax:          ₹51,400
  TDS Payable (Salary):    ₹3,72,953
  TDS Payable (Others):    ₹7,60,180
  Total:                   ₹48,49,663
Correct field: Other statutory liabilities  [Row 246]
CMA value:     0.4850 Cr ✓
```

**Verify:** Do you agree all statutory dues payable go to Row 246?
- [ ] Yes, correct   - [ ] No, exception: _______________________

---

## RULE BCIPL-022 — Duty Drawback / Export Incentives → Others (Non-Operating Income)

**Applies to:** Manufacturing, Exporting firms

**Pattern it catches:**
- `Duty Drawback`
- `Duty Drawback Received`
- `Sale of Duty Credit Scrips`
- `DEPB License` (when received, not sold)
- `Export Incentive`
- `MEIS` (Merchandise Exports from India Scheme)
- `RoDTEP` (Remission of Duties and Taxes on Exported Products)

**Classification:** Others (Non-Operating Income) → Row 34

**Why this rule exists:**
The 384-item reference says "Duty Drawback → Item 1: Domestic / Export sales as applicable [Gross Sales]".
However, the BCIPL CMA ground truth maps duty drawback and export incentives to **Others
(Non-Operating Income) Row 34**, not to Sales.

This is a common area of debate among CAs. Some treat export incentives as part of export revenue,
others as non-operating income. BCIPL's CA treats them as non-operating.

**IMPORTANT:** This contradicts the 384-item reference. Flag for CA verification.

**Real example from BCIPL FY2022-23:**
```
Source text:   "Sale of Duty Credit Scrips"  (Note 20: Other Income)
Amount:        ₹20,17,372
Correct field: Others (Non-Operating Income)  [Row 34]
384-ref says:  Gross Sales  ← EXCEPTION

Source text:   "Duty drawback Received"
Amount:        ₹14,59,090
Correct field: Others (Non-Operating Income)  [Row 34]
384-ref says:  Gross Sales  ← EXCEPTION
```

**Verify:** Do you map Duty Drawback to Sales or Other Income?
- [ ] Other Income (Row 34) — as in BCIPL CMA
- [ ] Sales (Row 22/23) — as in 384-ref
- [ ] Exception: _______________________

---

## Summary: Items Already Covered by Existing Reference

The following BCIPL line items are correctly handled by the existing 384-item reference
and/or V1 classification rules WITHOUT needing new rules:

| Source Line Item | 384-Ref Match | CMA Field | Row |
|-----------------|---------------|-----------|-----|
| Purchases of raw materials | "Purchases of raw materials" | RM Indigenous | 42 |
| Power & Fuel | "Power" / "Fuel Expenses" | Power, Coal, Fuel and Water | 48 |
| Rent | "Office Rent" | Rent, Rates and Taxes | 68 |
| Insurance | "Insurance" | Others (Admin) | 71 |
| Consultation Fees | "Consultancy Charges" | Others (Admin) | 71 |
| Bad debts | "Bad debts" | Bad Debts | 69 |
| Depreciation | "Depreciation on machinery" | Depreciation (CMA) | 63 |
| Interest Received | "Interest received" | Interest Received | 30 |
| Bad Debts Written Back | "Bad debts recovered" | Others (Non-Operating) | 34 |
| Share Capital | "Equity Share Capital" | Issued, Subscribed and Paid up | 116 |
| Share Premium | "Share Premium" | Share Premium A/c | 123 |
| Deferred Tax Liability | "Deferred tax liability" | Deferred tax liability (BS) | 159 |
| Trade Payables / Sundry Creditors | Covered by V1 Rule B-002 | Sundry Creditors for goods | 242 |
| Security Deposits (Telephone, BESCOM) | Covered by V1 Rule C-004 | Security deposits with govt | 237 |
| Vehicle Loan | Covered by V1 Rule C-001 | Gross Block | 162 |
| Conveyance | "Conveyance" | Others (Admin) | 71 |
| Printing and Stationery | "Printing & Stationery" | Others (Admin) | 71 |
| Security Services | "Security Charges" | Others (Admin) | 71 |
| Pooja Expenses | "Pooja expenses" | Others (Admin) | 71 |
| Donations | "Donation" | Others (Non-Operating Exp) | 93 |
| Travelling Expenses | "Traveling Expenses" | Others (Admin) | 71 |
| Income Tax provision | "Income Tax" | Income Tax provision | 99 |
| Advance from Customers | Covered in 384-ref BS items | Advance received from customers | 243 |
| Prepaid Expenses | Covered in 384-ref BS items | Prepaid Expenses | 222 |

---

## Manufacturing-Specific Items NOT in Trading Firms

These items appear in BCIPL but would NEVER appear in a trading firm like Mehta Computers.
They test the manufacturing-specific CMA fields:

| Item | CMA Field | Row | Notes |
|------|-----------|-----|-------|
| Cost of Raw Materials Consumed (formula) | RM Indigenous | 42 | Opening + Purchases - Closing |
| Stores & Spares Consumed | Stores & spares (Indigenous) | 44 | Separate from RM |
| Factory Wages (Basic, DA, HRA, etc.) | Wages | 45 | Multiple sub-components |
| Job Work / Contract Labour | Processing / Job Work | 46 | Direct production cost |
| Changes in Inventories - Finished Goods | FG Opening/Closing | 58/59 | Stock valuation |
| Changes in Inventories - Tools | Others (Mfg) | 49 | Manufacturing tools |
| Factory Depreciation | Depreciation (Mfg) | 56 | Heavy asset base |
| Capital WIP | Capital Work in Progress | 165 | Machinery under installation |
| Gross Block (Factory) | Gross Block | 162 | ₹45-53 Cr |
| Accumulated Depreciation | Less Accumulated Depreciation | 163 | ₹18-22 Cr |
| Intangible Assets (Software) | Other Intangible assets | 172 | Amortization applicable |
| Sellers Credit (Import Finance) | Term Loans | 136/137 | Machinery imports |
| ECGS/ECLGS Loans | Term Loans | 136/137 | Govt guarantee schemes |
| Capital Advances | Advances for capital goods | 236 | Machinery import advances |
| Security Deposit - ATS Trainee | Other current liabilities | 250 | Manufacturing workforce |
| MSME Creditors disclosure | Sundry Creditors | 242 | MSME Act compliance |
| Raw Material Inventory (Closing) | Raw Material Indigenous | 194 | BS inventory item |
| Finished Goods Inventory | Finished Goods | 201 | BS inventory item |
| Stores & Spares Inventory | Stores and Spares Indigenous | 198 | BS inventory item |

---

## How to Use These Rules

1. **Implement in rule_engine.py** — Rules BCIPL-001 through BCIPL-022 should be added as
   Tier 0 deterministic rules that fire BEFORE the AI classifier.

2. **Industry detection** — Rules marked "Manufacturing only" should only fire when the
   document is from a manufacturing firm. Detect via: presence of "Cost of Raw Materials
   Consumed" or "Changes in Inventories" or "Wages" in the P&L.

3. **Override the 384-ref** — Rules BCIPL-003, BCIPL-015, and BCIPL-022 CONTRADICT the
   384-item reference. The CMA ground truth should take precedence.

4. **Verify with CA** — Every rule has a verification checkbox. Get Ashutosh/CA firm to
   confirm before implementing.

5. **Test with other manufacturing clients** — These rules are derived from ONE company.
   Test against other manufacturing clients to validate generalizability.
