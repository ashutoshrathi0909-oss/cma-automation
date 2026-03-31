# CMA Classification Rules — SSSS (Salem Stainless Steel Suppliers)

**Company:** Salem Stainless Steel Suppliers Private Limited
**Industry Type:** Trading — Stainless Steel Distribution (B2B)
**Financial Years Covered:** FY2021-22, FY2022-23, FY2023-24, FY2024-25
**Total Line Items Analysed:** ~120 distinct line items across P&L and BS
**New Rules Generated:** 14 (SSSS-001 through SSSS-014)
**Items covered by existing 384-item reference:** ~70 (purchases, sales, standard expenses)
**Rule IDs:** SSSS-001 to SSSS-014
**Prepared by:** AI analysis vs CMA ground truth
**Date:** 2026-03-22
**Verified by:** ☐ Pending CA sign-off

---

## Context

Salem Stainless Steel Suppliers (SSSS) is a **multi-branch stainless steel trading company** with operations in Salem (HO), Coimbatore, Kerala, Mumbai, Hyderabad/Secunderabad, Haryana, Chennai, and Tamil Nadu. They buy stainless steel (coils, sheets, plates, pipes) primarily from Jindal Stainless Limited (JSL) and Jindal Stainless Hisar Limited (JSHL) and resell to industrial customers.

**Key features of their accounting:**
- Revenue ≈ ₹400–445 Crores/year (FY22–FY25), all domestic trading
- Stock-in-Trade = their entire inventory (no manufacturing WIP or raw materials in BS)
- Large working capital loans (OD facilities with HDFC, HSBC)
- Significant related-party loan (Four Star Estates LLP — promoter group entity)
- Vendor rebates from JSL/JSHL are a major recurring feature (~₹6 Cr/year in FY23)
- Multi-branch consolidated financials — all branches appear in one file

---

## Why These Rules Are Needed

The 384-item reference handles standard trading firm items well (purchases, sales, standard expenses). But SSSS has 14 categories where either:

1. The item is **steel-trading specific** and not in the reference at all
2. The item **appears in an unexpected schedule location** (e.g., vendor discounts in "Other Income")
3. The CA made a **judgment call** (e.g., splitting a loan into quasi-equity vs. long-term debt)
4. The item has **different routing** compared to a generic trading firm (e.g., interest on unsecured related-party loans)

---

## RULE SSSS-001 — Vendor Quantity Discounts / Supplier Rebates → Net Against Purchases

**Applies to:** Steel trading industry (and any commodity trading firm receiving volume rebates)

**Pattern it catches:**
- `Quantity Discount Received`
- `JSL/JSHL Discount (others)` / `JSL/JSHL Discount`
- `SAIL-quantity discount` / `SAIL discount`
- `Discount received` (when appearing in the Purchases schedule, not Other Income)
- `Discount On Purchase` / `Purchase Discount`
- `Cash Discount /Quality Discount` (on the income side when it relates to purchases)
- Any discount received FROM suppliers (not discounts given TO customers)

**Classification:** Raw Materials Consumed (Indigenous) → Row 42
*(Amount will be negative — it reduces the cost of purchases)*

**Why this rule exists:**
In steel trading, large manufacturers (Jindal Stainless, SAIL) give **volume-based quantity rebates** to distributors based on annual purchase volumes. These rebates are formally credited to the distributor's account and appear in the books as "Quantity Discount Received" or "JSL/JSHL Discount."

The CA's correct treatment: these are **purchase price adjustments**, not trading income. They must be NETTED against the purchase cost in Raw Materials Consumed (Row 42), not shown as Other Income in Row 34.

Without this rule, the AI will see "Quantity Discount Received" in an "Income" section of the schedule and classify it as **Others (Non-Operating Income) Row 34** — which is wrong.

**Real example from SSSS FY2022-23:**
```
Source text:   "Quantity Discount Received"
Section:       Schedule-20 (Other Income schedule, HO)
Amount:        ₹3,20,44,294 (credit)
Correct field: Raw Materials Consumed (Indigenous)  [Row 42]  (as negative)
Old result:    Others (Non-Operating Income) Row 34  (WRONG)
New result:    Netted against Raw Materials Row 42   ✓

Source text:   "JSL/JSHL Discount (others)"
Amount:        ₹3,02,30,618 (credit)
Correct field: Raw Materials Consumed (Indigenous)  [Row 42]  (as negative)

Source text:   "Discount received"  (in Purchases schedule)
Amount:        -₹5,48,41,919 (already negative — deduction from purchases)
Correct field: Raw Materials Consumed (Indigenous)  [Row 42]
```

**Combined impact FY23:** ~₹9 Cr netted from purchases. Without this rule, both the purchase cost and "Other Income" would be overstated by ₹9 Cr.

**When this rule would be WRONG:**
If the discount text says "Discount allowed" or "Discount given to customer" — that goes to Row 71 (Others Admin) or Row 70.

**Verify:** Do you agree supplier quantity discounts and JSL/JSHL discounts should reduce Raw Materials cost (Row 42) rather than appear as Other Income?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE SSSS-002 — JSL/JSHL Discount Receivable (Balance Sheet) → Other Advances / Current Asset

**Applies to:** Steel trading companies dealing with Jindal Steel

**Pattern it catches:**
- `JSL/JSHL Discount Receivable`
- `Discount Receivable` (in the Other Current Assets / Balance Sheet context)
- `Vendor Rebate Receivable`
- `Quantity Discount Receivable`

**Classification:** Other Advances / current asset → Row 223

**Why this rule exists:**
At year-end, the quantity discount from JSL/JSHL may not yet be received in cash. The company books "JSL/JSHL Discount Receivable" as a current asset. This is **not a trade debtor** (not from a customer sale) — it's an amount owed by the supplier.

Without this rule, the AI would classify this as "Domestic Receivables" (Row 206) because it looks like a receivable, or as "Security deposits" (Row 237) — both wrong.

**Real example from SSSS FY2022-23:**
```
Source text:   "JSL/JSHL Discount Receivable"
Section:       Other Current Assets (Schedule-17)
Amount:        ₹2,87,52,999
Correct field: Other Advances / current asset  [Row 223]
Old result:    Domestic Receivables  [Row 206]  (WRONG — this is from supplier, not customer)
New result:    Other Advances / current asset  [Row 223]  ✓
```

**Verify:** Do you agree supplier discount receivables should go to Row 223 (Other Advances) not Row 206 (Trade Receivables)?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE SSSS-003 — Cutting Labour Charges / Slitting Charges → Processing / Job Work

**Applies to:** Steel trading industry

**Pattern it catches:**
- `Cutting Labour Charges`
- `Cutting Charges`
- `Slitting Charges`
- `Slitting Labour Charges`
- `Steel Cutting Charges`
- `Sheet Cutting Labour`

**Classification:** Processing / Job Work Charges → Row 46

**Why this rule exists:**
Stainless steel distributors often cut coils and sheets to customer-specified sizes before delivery. The "Cutting Labour Charges" are payments to workers or external job workers for this cutting/slitting service. This is a **direct manufacturing/processing cost**, not an admin or freight expense.

Without this rule, the AI sees "Labour" in the name and may classify it as "Wages" (Row 45), or sees "Charges" and puts it in "Others (Admin)" (Row 71). Neither is correct.

The CA consistently mapped Cutting Labour to Processing/Job Work (Row 46) for FY22 and FY23.

**Real example from SSSS FY2022-23:**
```
Source text:   "Cutting Labour Charges"
Section:       Schedule-24 Direct Expenses
Amount:        ₹1,11,13,588 (FY23)
Correct field: Processing / Job Work Charges  [Row 46]
Old result:    Wages [Row 45] or Others Admin [Row 71]  (WRONG)
New result:    Processing / Job Work Charges  [Row 46]  ✓

Source text:   "Polishing Charges"
Amount:        ₹41,328 (FY23)
Correct field: Processing / Job Work Charges  [Row 46]
```

**Verify:** Do you agree cutting/slitting charges in steel trading = Processing/Job Work (Row 46)?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE SSSS-004 — Material Testing Charges → Others (Manufacturing)

**Applies to:** Steel trading and steel manufacturing industries

**Pattern it catches:**
- `Material Testing Charges`
- `Material Testing`
- `Quality Testing Charges`
- `Testing Charges` (when in manufacturing/direct expense section)
- `Inspection Charges` (when for material quality)

**Classification:** Others (Manufacturing) → Row 49

**Why this rule exists:**
Steel distributors are often required to provide quality certificates and test reports to buyers (government projects, Railways, defense). They send samples to labs like RITES, MICROLAB, SGS, TÜV for testing. This is a **direct cost of the product**, not an admin expense.

Without this rule, the AI might classify "Material Testing Charges" as "Others (Admin)" (Row 71) or even "Audit Fees" — both wrong.

**Real example from SSSS FY2022-23:**
```
Source text:   "Material Testing Charges"
Section:       Schedule-24 Direct Expenses
Amount:        ₹49,760 (small but recurring)
Vendors:       MICROLAB, RITES LIMITED, TII TECHNO TESTING SERVICES PVT LTD
Correct field: Others (Manufacturing)  [Row 49]
Old result:    Others (Admin) [Row 71]  (WRONG)
New result:    Others (Manufacturing)  [Row 49]  ✓
```

**Note:** If the amount is very small (< ₹50,000 total), the CA may include it in Others (Admin) for simplicity. Verify with the CA.

**Verify:** Do you agree material/quality testing charges go to Others (Manufacturing) Row 49?
☐ Yes, correct   ☐ No, it should go to Others (Admin) Row 71: _______________________

---

## RULE SSSS-005 — Cooly and Cartage → Freight and Transportation

**Applies to:** Trading industry (especially bulk commodity traders)

**Pattern it catches:**
- `Cooly and Cartage`
- `Cooly Charges`
- `Cartage`
- `Cooly & Cartage`
- `Loading and Cartage`

**Classification:** Freight and Transportation Charges → Row 47

**Why this rule exists:**
"Cooly and Cartage" refers to **labour for loading/unloading heavy goods + small vehicle transport** (cycle rickshaws, hand carts, tempo vehicles) for last-mile material movement within a godown or depot. In steel trading, this is a direct delivery cost.

The AI may classify "Cooly" (labour-sounding word) as "Wages" (Row 45) or "Staff expenses" (Row 67). The correct mapping is Freight and Transportation (Row 47) because it's a goods-movement expense.

**Important note:** In FY23, this was ₹81.37L — the LARGEST item in SSSS's "Other Expenses" after Professional Fees and Rent. An incorrect classification here has significant impact.

**Real example from SSSS FY2022-23:**
```
Source text:   "Cooly and Cartage"
Section:       Schedule-24 Indirect Expenses
Amount:        ₹81,37,255 (FY23) — large item
Correct field: Freight and Transportation Charges  [Row 47]
Old result:    Wages [Row 45] or Others Admin [Row 71]  (WRONG)
New result:    Freight and Transportation Charges  [Row 47]  ✓
```

**Note:** The CA in FY23 did include this in the FY23 Freight total (₹3.32 Cr). For FY24/25, the detailed schedule is not available but this item type should always go to Row 47.

**Verify:** Do you agree "Cooly and Cartage" goes to Freight (Row 47) not Wages (Row 45)?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE SSSS-006 — Tempo/Van/Bullock Cart/Rickshaw Charges → Freight and Transportation

**Applies to:** Trading and manufacturing industries

**Pattern it catches:**
- `Tempo/Van/Bullock cart/Rickshaw Charges`
- `Tempo Charges`
- `Auto Rickshaw Charges`
- `Taxi, Tempo & Auto Charges`
- `Van Charges`

**Classification:** Freight and Transportation Charges → Row 47

**Why this rule exists:**
These are small vehicle hire costs for goods movement — categorically a freight/logistics cost. The AI might classify "Taxi, Tempo & Auto" as travel/conveyance (staff travel = Others Admin Row 71) rather than goods transport.

**Distinguish from:** Staff travel conveyance (which goes to Others Admin Row 71). The "Tempo/Van/Bullock cart" terminology almost always signals goods transport, not staff travel.

**Real example from SSSS FY2022-23:**
```
Source text:   "Tempo/Van/Bullock cart/Rickshaw Charges"
Section:       Schedule-24 Direct Expenses
Amount:        ₹30,05,380 (FY23)
Correct field: Freight and Transportation Charges  [Row 47]
Old result:    Others (Admin) or Wages  (WRONG — these are not staff)
New result:    Freight and Transportation Charges  [Row 47]  ✓
```

**Verify:** Do you agree tempo/van/auto charges for goods movement go to Freight (Row 47)?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE SSSS-007 — Weighment Expenses → Others (Manufacturing)

**Applies to:** Steel and bulk commodity trading

**Pattern it catches:**
- `Weighment Expenses`
- `Weighbridge Charges`
- `Weight Charges`
- `Weighment Charges`

**Classification:** Others (Manufacturing) → Row 49

**Why this rule exists:**
Steel is sold by weight. Weighbridge charges (for trucks to be weighed at entry/exit from godowns/factories) are a direct cost of the steel trading operation. This is NOT an admin expense.

The AI might classify "Weighment" as a miscellaneous admin expense (Row 71) — wrong.

**Real example from SSSS FY2022-23:**
```
Source text:   "Weighment Expenses"
Section:       Schedule-24 Indirect Expenses
Amount:        ₹1,82,860 (FY23)
Correct field: Others (Manufacturing)  [Row 49]
Old result:    Others (Admin) [Row 71]  (probable wrong classification)
New result:    Others (Manufacturing)  [Row 49]  ✓
```

**Verify:** Do you agree weighbridge/weighment charges go to Others (Manufacturing) Row 49?
☐ Yes, correct   ☐ No, it should go to Others (Admin) Row 71

---

## RULE SSSS-008 — Interest on Unsecured Loans from Related Parties → Fixed Loans Interest

**Applies to:** All industries (especially family-owned businesses with promoter loans)

**Pattern it catches:**
- `Interest Paid On Unsecured Loan`
- `Interest on Unsecured Loan`
- `Interest on Related Party Loan`
- `Interest on Loan from Relatives`
- `Interest on Promoter Loan`

**Classification:** Interest on Fixed Loans / Term Loans → Row 83

**Why this rule exists:**
SSSS borrows ₹50–60 Cr from "Four Star Estates LLP" — a promoter group entity. Although this loan is "unsecured" (no asset pledge), it functions exactly like a term loan — it's a long-term borrowing at a fixed interest rate, repaid over years.

The 384-item reference maps "unsecured loan" to the liability side (Rows 152-154), but the **interest on that unsecured loan** should go to Interest on Fixed Loans (Row 83), not to Interest on Working Capital (Row 84) which is for bank OD/CC facilities.

Without this rule:
- The AI sees "Interest Paid on Unsecured Loan" and is uncertain between Row 83 and Row 84
- It might put it in Working Capital interest (Row 84) — wrong
- Or worse, go to doubt report

**Real example from SSSS FY2022-23:**
```
Source text:   "Interest Paid On Unsecured Loan"
Section:       Schedule-25 (Finance Cost)
Amount:        ₹4,94,38,053 (FY23) — very large!
Correct field: Interest on Fixed Loans / Term Loans  [Row 83]
Old result:    DOUBT or Interest on Working Capital [Row 84]  (WRONG)
New result:    Interest on Fixed Loans / Term Loans  [Row 83]  ✓
```

**Contrast with:** "Interest on Bank OD" and "Interest Paid on Trading" → these are Working Capital interest (Row 84) because OD/CC facilities ARE working capital.

**Verify:** Do you agree interest on unsecured promoter/family loans goes to Fixed Loans Row 83?
☐ Yes, correct   ☐ No, it should go to WC interest Row 84: _______________________

---

## RULE SSSS-009 — Interest Paid on Trading → Working Capital Interest

**Applies to:** Trading industry only

**Pattern it catches:**
- `Interest Paid on Trading`
- `Interest on Trade Credit`
- `Trading Interest`
- `Interest on Purchases` (interest paid to suppliers for delayed payment)

**Classification:** Interest on Working Capital Loans → Row 84

**Why this rule exists:**
Steel traders sometimes buy on credit from suppliers and pay interest for delayed payments. This appears as "Interest Paid on Trading" in SSSS's books. Although it sounds different from bank OD interest, it's economically the same as working capital financing.

Without this rule, the AI might classify this as "Interest on Fixed Loans" (Row 83) because it says "loan" or it might send to doubt.

**Real example from SSSS FY2022-23:**
```
Source text:   "Interest Paid on Trading"
Section:       Schedule-25 Finance Cost
Amount:        ₹15,37,446 (FY23)
Correct field: Interest on Working Capital Loans  [Row 84]
Old result:    Interest on Fixed Loans [Row 83] or DOUBT  (WRONG)
New result:    Interest on Working Capital Loans  [Row 84]  ✓
```

**Verify:** Do you agree "Interest Paid on Trading" (supplier credit interest) goes to Working Capital Row 84?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE SSSS-010 — Sales Expense Reimbursements Charged to Customers → Domestic Sales

**Applies to:** Steel trading and commodity trading with value-added delivery

**Pattern it catches (when appearing in the Revenue / Sales schedule):**
- `P&F / Handling Charges` (when in sales schedule)
- `P&F and Delivery Charges` (when in sales schedule)
- `Material Delivery Charges` (billed to customer)
- `Loading & Transportation Charges` (when billed to customer)
- `Pallet Charges` (when billed to customer)
- `Rate & Weight Difference` (positive or negative adjustment to invoice)
- `Cutting Charges` (when in sales schedule — different from Cutting Labour in expenses)

**Classification:** Domestic Sales → Row 22

**Why this rule exists:**
In SSSS's schedule of sales, alongside the main GST sales amounts, there are additional recovery items that SSSS charges to its customers (delivery charges, packing charges, cutting charges, etc.). These are **part of net revenue** and must stay in Row 22.

The confusion: "Cutting Charges" appears in BOTH:
- The Revenue schedule (amounts *charged to customers*) → Row 22
- The Expense schedule (amounts *paid to workers*) → Row 46

The AI must use the **section context** to distinguish. If the item is in the revenue/income schedule, it goes to Row 22. If in the expense schedule, it's a cost (Row 46 or Row 47).

Similarly, "Rate & Weight Difference" adjustments (credit notes on sales) appear as negative amounts in the revenue schedule — they reduce gross sales and stay in Row 22.

**Real example from SSSS FY2022-23:**
```
Source text:   "P&F /Handling Charges"
Section:       Schedule-1 (Schedule of Sales) — Revenue section
Amount:        ₹37,29,936 (HO) — billed to customer on top of product price
Correct field: Domestic Sales  [Row 22]  (it's part of gross revenue)
Old result:    Freight & Transportation [Row 47]  (WRONG — this is income not expense)
New result:    Domestic Sales  [Row 22]  ✓

Source text:   "Rate Difference - Sales"
Section:       Schedule of Sales
Amount:        -₹2,78,536 (negative — sales credit note to customer)
Correct field: Domestic Sales  [Row 22]  (reduces gross sales)
Old result:    Loss on Exchange Fluctuations [Row 91] or DOUBT  (WRONG)
New result:    Domestic Sales  [Row 22]  ✓
```

**Verify:** Do you agree all items in the Sales Revenue schedule (including handling charges charged to customers) should be included in Domestic Sales Row 22?
☐ Yes, correct   ☐ No, some should be separated: _______________________

---

## RULE SSSS-011 — All Bank OD / Overdraft Accounts → Working Capital Bank Finance

**Applies to:** All industries with OD facilities

**Pattern it catches:**
- `HSBC Ltd A/C` / `HSBC OD A/C` (when in short-term borrowings section)
- `HDCF Bank Od A/C` / `HDFC OD A/C`
- `Kotak Mahindra Bank Ltd O/D`
- `[Bank Name] OD A/C` or `[Bank Name] O/D`
- `Working Capital Demand Loan` (WCDL) — when in short-term section
- `Cash Credit` / `CC Limit`

**Classification:** Working Capital Bank Finance - Bank 1 → Row 131
*(If two separate banks, use Bank 2 = Row 132)*

**Why this rule exists:**
SSSS uses OD (overdraft) facilities from multiple banks (HDFC, HSBC, Kotak) as working capital. The app should combine these into the Working Capital Bank Finance rows (131/132).

However, the SAME banks (HDFC, HSBC, Kotak) also have WCDL **term loans** that go into Row 137 (Term Loan Balance Repayable after 1 year). The key is the account name:
- `OD A/C` / `O/D` → Working Capital Row 131
- `Term Loan` / `WCDL Term Loan` → Term Loan Row 137

**Real example from SSSS FY2022-23:**
```
Source text:   "Hsbc Ltd A/C" (OD account)
Section:       Short-Term Borrowings (Schedule-4)
Amount:        ₹26,61,52,543 (FY23)
Correct field: Working Capital Bank Finance - Bank 1  [Row 131]
Old result:    Term Loan Balance after 1 year [Row 137]  (WRONG)
New result:    Working Capital Bank Finance  [Row 131]  ✓

Source text:   "WCDL HDFC Term Loan"
Section:       Long-Term Borrowings (Conso-sch Bs)
Amount:        ₹4,21,45,833 (FY23)
Correct field: Term Loan Balance Repayable after 1 year  [Row 137]
New result:    Term Loan  [Row 137]  ✓
```

**Verify:** Do you agree bank OD accounts = Working Capital (Row 131) and Term Loans (even from same banks) = Row 137?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE SSSS-012 — Related Party Unsecured Loan → Split Between Quasi Equity and Long-Term Debt

**Applies to:** Family-owned businesses with promoter group loans designated as quasi-equity by the bank

**Pattern it catches:**
- Unsecured loan from a promoter-group entity (LLP, family member) where the CA has specifically designated a portion as quasi-equity
- `Unsecured Loan From Relatives & Others` (when partially classified as quasi-equity)
- Any loan where the CMA specifically shows a fixed amount under "Quasi Equity" (Row 152)

**Classification:**
- Fixed amount (₹6 Cr in SSSS's case) → Unsecured Loans - Quasi Equity → Row 152
- Balance → Unsecured Loans - Long Term Debt → Row 153

**Why this rule exists:**
SSSS borrowed from Four Star Estates LLP (a promoter group entity). The bank treating this CMA requires a portion to be shown as "Quasi Equity" — this is a **banking requirement**, not a legal classification. The CA has consistently shown ₹6 Cr as quasi-equity and the balance as long-term debt.

This is a **CA JUDGMENT CALL** — the app cannot automatically determine how much of a promoter loan is quasi-equity vs. debt. This rule alerts the verification screen to ask the CA/user to confirm the split.

**Real example from SSSS (all years):**
```
Source text:   "Unsecured Loans" / "Four Star Estates LLP"
Section:       Long-Term Borrowings
Total amount:  ₹57.71 Cr (FY23)
CA Decision:   ₹6.00 Cr → Quasi Equity [Row 152]   (fixed, does not change with loan balance)
               ₹51.71 Cr → Long Term Debt [Row 153]

FY24 Total:    ₹38.21 Cr  → ₹6.00 Cr Quasi + ₹32.21 Cr LTD
FY25 Total:    ₹35.68 Cr  → ₹6.00 Cr Quasi + ₹29.68 Cr LTD
```

**App guidance:** When the extractor finds an unsecured related-party loan, it should:
1. Flag it on the verification screen with the question: "How much of this loan should be shown as Quasi Equity?"
2. Pre-fill with 0 (safe default — classify all as Long-Term Debt)
3. The CA enters the quasi-equity portion manually

**Verify:** Do you agree ₹6 Cr of the Four Star Estates LLP loan is quasi-equity per your bank's requirement?
☐ Yes, correct   ☐ No, it should be: ₹_______ Cr as quasi-equity

---

## RULE SSSS-013 — Statutory Authority Balances (GST, TDS) → Advance Income Tax or Other Advances

**Applies to:** All industries

**Pattern it catches (when in Short-Term Loans and Advances / Balance Sheet Assets):**
- `GST Credit Ledger` / `IGST Receivable` / `GST Input Credit`
- `TDS Receivable` / `TCS Receivable`
- `Advance Tax` / `Advance Tax paid`
- `Income Tax Refund Receivable`
- `TDS Excess paid`
- `Cash with Income tax Department`
- `Income Tax Paid on Regular Assessment`

**Classification:**
- If related to Income Tax (Advance Tax, IT refund, IT paid on assessment) → **Advance Income Tax → Row 221**
- If related to GST (GST Credit, ITC, GST TCS, TDS/TCS receivable) → **Other Advances / current asset → Row 223**

**Why this rule exists:**
SSSS bundles ALL statutory authority balances into "Balance With Government Authorities" in Schedule-16. The CMA has separate rows for Income Tax-related items (Row 221) vs. other advances (Row 223).

The CA's approach in FY23:
- The ENTIRE ₹7.69 Cr "Balance With Government Authorities" went to Advance Income Tax (Row 221) — because the dominant items were Advance Tax (₹5.70 Cr) + IT Paid on Assessment (₹2.13 Cr)
- GST Credit Ledger (₹1.28 Cr) was also included in Row 221 in this case

For FY24/25 (simplified notes), the consolidated "Balances with Statutory Authorities" = ₹6.53 Cr also goes entirely to Row 223 (Other Advances) since no specific advance tax distinction is made.

**App guidance:** When this schedule is unclear, put the full balance in "Other Advances / current asset" Row 223. Flag for CA verification if the amount is large.

**Real example from SSSS FY2022-23:**
```
Source text:   "Gst Credit Ledger"
Section:       Balance With Government Authorities (Schedule-16)
Amount:        ₹1,27,66,181
Correct field: Advance Income Tax [Row 221] (included in CA's consolidated entry)
               OR Other Advances [Row 223] (safer default if can't distinguish)

Source text:   "Advance Tax" + "Income Tax Paid on Regular Assessment"
Amount:        ₹57,00,000 + ₹2,12,87,955 = ₹2,69,87,955
Correct field: Advance Income Tax  [Row 221]  ✓
```

**Verify:** For FY24/25, do statutory authority balances (GST + TDS + Advance Tax) go entirely to Row 223 (Other Advances)?
☐ Yes, combine in Row 223   ☐ No, split — Income Tax to Row 221, GST to Row 223

---

## RULE SSSS-014 — Custom Duty / Customs Duty on Import → Part of Raw Materials (Imported)

**Applies to:** Any company importing goods

**Pattern it catches (in Purchases/Direct Expenses schedule):**
- `Custom Duty on Import`
- `Customs Duty`
- `Import Duty`
- `Basic Customs Duty (BCD)`
- `Clearing Expenses` (when related to imports)

**Classification:** Raw Materials Consumed (Imported) → Row 41
*(Added to the cost of imported goods — NOT a separate expense line)*

**Why this rule exists:**
Import customs duty is a **part of the landed cost of imported goods**, not a standalone expense. It should be added to the imported raw materials cost (Row 41) rather than classified as "Others (Manufacturing)" or "Fees, Rates & Taxes" or "Others (Admin)".

"Clearing Expenses" (freight forwarder, CHA charges) related to imports similarly forms part of the import cost.

**Real example from SSSS FY2022-23:**
```
Source text:   "Custom Duty on Import"
Section:       Schedule-2 (Purchases) — Other Expenses on Purchases, HO
Amount:        ₹24,74,150 (FY23)
Correct field: Raw Materials Consumed (Imported)  [Row 41]  (or netted into Row 42 if no imported)
Old result:    Others (Manufacturing) [Row 49] or Fees/Taxes  (WRONG)
New result:    Added to Raw Materials (Imported) cost  [Row 41]  ✓

Source text:   "Clearing Expenses"
Section:       Schedule-24 Direct Expenses
Amount:        ₹14,94,054 (FY23)
Correct field: Raw Materials Consumed (Imported)  [Row 41]
               OR Freight and Transportation Charges  [Row 47]  (if imports were minimal)
```

**Note:** If imported purchases are very small (< 1% of total purchases), some CAs include the customs duty and clearing costs in Row 42 (Indigenous) for simplicity. Verify with the CA.

**Verify:** Do customs duty and clearing charges go to imported Raw Materials Row 41?
☐ Yes, Row 41   ☐ No, include in Row 42 (domestic): _______________________

---

## ITEMS ALREADY COVERED BY EXISTING REFERENCE — No New Rule Needed

The following items in SSSS's financials are handled correctly by the existing 384-item reference or rules V1. No new rule needed:

| Item | Source Text | Correct Row | Covered By |
|------|-------------|-------------|------------|
| Purchases of Stock in Trade | `Purchases of stock-in-trade` / `Goods Purchased` | 42 | Reference |
| Opening / Closing Finished Goods | `Finished Goods Opening Balance` | 58/59, 201 | Reference |
| Salaries & Wages | `Salaries & Wages` | 67 | Reference |
| Directors Remuneration | `Directors Remuneration` | 73 | Reference |
| ESI, EPF | `ESI, EPF & Administration Expenses` | 67 | Reference |
| Rent | `Rent` | 68 | Reference |
| Advertisement | `Advertisement` / `Sales Promotion Expenses` | 70 | Reference |
| Bad Debts | `Bad debts` | 69 | Reference |
| Repairs & Maintenance | `Repairs and Maintenance` | 72 | Reference |
| Insurance | `Insurance` | 71 | Reference |
| Electricity Expenses | `Electricity Expenses` | 48 | Reference |
| Professional Fees / Legal Consultancy | `Professional Fees` / `Legal & Consultancy fees` | 71 | Reference |
| Interest on Bank OD | `Interest on Bank O.D` | 84 | Rule B-003 (modified) |
| Interest on Secured Loans (TL) | `Interest Paid On Secured Loan` | 83 | Reference |
| Bank Charges, Processing Fees | `Bank Charges,Processing Fees` | 85 | Reference |
| Depreciation | `Depreciation and Amortization Exp` | 63 | Reference |
| Income Tax Provision | `Current tax expense` | 99 | Reference |
| Deferred Tax | `Deferred tax` | 100/101 | Reference |
| Share Capital | `Share Capital` | 116 | Reference |
| Share Premium | `Share Premium A/c` | 123 | Reference |
| P&L Balance | `Balance transferred from profit and loss a/c` | 122 | Reference |
| Motor Vehicles / Car Loan | `Kotak Mahindra Prime - Car Loan` | 162 (Gross Block) | Rule C-001 |
| Telephone Deposit | `Telephone Deposit` | 237 | Rule C-004 |
| Security/Electricity Deposit | `Electricity Board-Deposit` | 237 | Rule C-004 |
| Provision for Income Tax (BS) | `Provision for Income Tax` | 244 | Reference |
| Interest on Investment/FD (income) | `FDR Interest` | 30 | Reference |
| Profit on Sale of Shares | `Profit on Sale of Shares` | 31 | Reference |
| Gain on Foreign Exchange | `Gain of Foreign Currency Fluctuation` | 32 | Reference |
| Sundry Balance Written Off | `Sundry balance written off` | 90 | Reference |
| Trade Payables / Sundry Creditors | `Trade Payables` | 242 | Reference |
| Advance from Customers | `Advances from Customers` | 243 | Reference |
| Statutory Liabilities (GST, TDS due) | `Statutory Liabilities` | 246 | Reference |
| Fixed Deposits (current) | `Fixed Deposits` | 215 | Reference |
| Share Investments | `Investment in Equity Instruments` | 186 | Reference |

---

## ITEMS REQUIRING CA JUDGMENT — NOT Automatable

The following items cannot be auto-classified by the app and require explicit input from the CA on the verification screen:

| Item | Issue | Verification Prompt |
|------|-------|---------------------|
| Four Star Estates LLP loan (Quasi Equity portion) | CA decides how much counts as quasi-equity | "How much of [amount] should be shown as Quasi Equity (Row 152)? Default = 0" |
| Advance Tax vs. GST Credit split | CA must confirm if IT and GST go to separate rows | "Does ₹X Cr represent Income Tax advances only? Or include GST credit?" |
| "Other Expenses" (FY24/25 Note 20) | Lumped — can't split internally without detailed schedule | Flag: "Note 20 'Other Expenses' = ₹X Cr. Classified to Others (Admin). Correct?" |
| FD allocation (lien vs. non-lien) | Lien FDs → Fixed Deposit under lien (Row 214); Free FDs → Other FDs (Row 215) | "FD of ₹X Cr — is it under lien with the bank? If yes → Row 214" |

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total distinct line items documented (FY22–FY25) | ~120 |
| Items handled by existing 384-item reference | ~65 |
| Items handled by existing V1 rules (A-001 to D-002) | ~8 |
| NEW rules created in this document | **14** |
| Items requiring CA judgment (not automatable) | **4** |
| Items with steel-trading specific patterns | **9** (SSSS-001 to SSSS-009) |
| Items with general applicability (all industries) | **5** (SSSS-010 to SSSS-014) |

---

## Testing Recommendations

To validate these rules work correctly, upload SSSS documents to the app and check:

1. **SSSS-001 test:** "Quantity Discount Received" should appear in Row 42 (negative), NOT Row 34
2. **SSSS-003 test:** "Cutting Labour Charges" should go to Row 46, NOT Row 45 or Row 71
3. **SSSS-008 test:** "Interest Paid On Unsecured Loan" should go to Row 83, NOT Row 84
4. **SSSS-010 test:** "P&F/Handling Charges" in sales schedule should go to Row 22, NOT Row 47
5. **SSSS-012 test:** App should flag the Four Star LLP loan and ask for quasi-equity split

Use `classification_method` column in the output to confirm which rule fired for each item.
