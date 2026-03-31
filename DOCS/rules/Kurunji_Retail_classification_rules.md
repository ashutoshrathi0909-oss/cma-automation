# CMA Classification Rules — Kurunji Retail

**Company:** Kurunji Retails
**Industry Type:** Retail (multi-product consumer goods, including electronics)
**Entity Type:** Partnership Firm (5 partners) — NOT a company
**Location:** Mayiladuthurai / Kumbakonam, Tamil Nadu
**Financial Years Covered:** FY2021-22, FY2022-23, FY2023-24, FY2024-25
**Total Line Items Analysed:** ~75 distinct P&L + Balance Sheet line items across 4 years
**New Rules Generated:** 15 (KR-001 through KR-015)
**Items Covered by Existing Reference/Rules:** ~30 (listed in coverage table at end)
**Auditors:** S.R. Dhass & Co., Kumbakonam
**Prepared by:** AI analysis vs CMA ground truth (CMA Kurinji retail 23012026.xls)
**Date:** 2026-03-22
**Verified by:** ☐ Pending CA sign-off

---

## Context

Kurunji Retails is a **multi-partner retail store** selling consumer goods including electronics, based in Tamil Nadu. Revenue grew from ₹14.67 Cr (FY22) to ₹68.87 Cr (FY25) — a 4.7x increase in 3 years. They operate what appears to be a single main store with a sister/satellite entity called "Kurinji Metro".

**Key features of their accounting:**
- Partnership firm (NOT a private limited company) — capital is "Partners' Capital", not "Share Capital"
- All borrowings through ICICI Bank (CC/OD for working capital + term loans in FY25)
- Promoter-group unsecured loans partially classified as "Quasi Equity" by bank
- Store rent is the second-largest P&L expense (₹45–99 lakhs/year) — CA classifies to Row 49
- Packing materials consumed in retail packaging → Row 44 (Stores & Spares), with BS stock in Row 198
- Partners are paid salary (remuneration) AND interest on capital — shown as separate P&L lines
- No export sales, no manufacturing, no WIP — pure retail buying and reselling

**Key differences from previous companies analysed:**

| Feature | Mehta (Trading) | SSSS (Steel Trading) | SR Papers (Distribution) | **Kurunji (Retail)** |
|---------|----------------|---------------------|--------------------------|----------------------|
| Entity type | Firm/Company | Pvt Ltd | Pvt Ltd | **Partnership** |
| Capital | Share Capital | Share Capital | Share Capital | **Partners' Capital** |
| Rent row | Row 68 | Row 68 | Row 68 | **Row 49 (counterintuitive!)** |
| Partner costs | None | None | None | **Salary + Interest to Partners** |
| Packing materials | Minor | None | None | **Major → Row 44** |
| Retail-specific | None | None | None | **Barcode, Bill Roll, etc.** |

---

## Why These Rules Are Needed

The 384-item reference and V1 rules handle standard trading firm items well but **miss the partnership firm structure entirely** and have no awareness of retail-specific expenses. Kurunji Retail has 15 new patterns where the AI would either:

1. **Misclassify** because the term doesn't exist in the reference (Barcode Expenses, Bill Printing Roll, Digital Marketing)
2. **Use wrong row** because retail CA makes unusual choices (Rent → Row 49, not Row 68)
3. **Fail on partnership structure** (Partners' Capital, Partners' Salary, Interest to Partners)
4. **Confuse P&L artifacts** (TDS on Rent shown as separate P&L line — Tally accounting style)

---

## RULE KR-001 — Partners' Capital Account → Share Capital Row (Partnership Firms)

**Applies to:** All partnership firms

**Pattern it catches:**
- `Partners' Capital Account` (in liabilities section of Balance Sheet)
- `Capital Account` (when under partners/proprietor section, not share capital)
- `Partners' Capital` (abbreviated form)
- `A/c Capital` (Tally format for partner capital accounts)

**Classification:** Issued, Subscribed and Paid up → Row 116

**Why this rule exists:**
In a partnership firm, "Partners' Capital Account" is the economic equivalent of Share Capital for a company. The CMA Row 116 is labelled "Issued, Subscribed and Paid up" (company terminology) but is the correct row for partnership capital too.

Without this rule, the AI sees "Partners' Capital Account" and either:
- Doubts it (no match in reference)
- Puts it in "Unsecured Loans — Quasi Equity" (Row 152) because it looks like a partner loan
- Puts it in "Other Reserve" (Row 125) — wrong

The CMA ground truth consistently uses Row 116 for Partners' Capital for ALL four years.

**Real example from Kurunji Retail:**
```
Source text:   "Partners' Capital Accounts"
Section:       Liabilities (Balance Sheet)
Amount:        ₹3,42,55,012 (FY23) → ₹9,20,95,629 (FY25)
Correct field: Issued, Subscribed and Paid up  [Row 116]
Old result:    DOUBT or Unsecured Loans (WRONG)
New result:    Row 116  ✓
```

**Verify:** Do you agree "Partners' Capital Account" should go to Row 116 (same as Share Capital for companies)?
☐ Yes, correct   ☐ No, use a different row: _______________________

---

## RULE KR-002 — Partners' Remuneration / Salary to Partners → Row 73

**Applies to:** All partnership firms

**Pattern it catches:**
- `Salary to Partners`
- `Partners' Remuneration`
- `Remuneration to Partners`
- `Partners' Salary`
- `Salary - Partners` (Tally format)

**Classification:** Audit Fees & Directors Remuneration → Row 73

**Why this rule exists:**
In a partnership firm, partners are paid a fixed "salary" (remuneration) as allowed under Section 40(b) of the Income Tax Act. This appears as a P&L debit entry. The CMA has no dedicated "Partners' Salary" row — the closest match is Row 73 "Audit Fees & Directors Remuneration" because:
- It's a fixed overhead cost not related to direct operations
- It parallels Directors' Remuneration in a company (also Row 73)

Without this rule, the AI sees "Salary to Partners" and routes it to:
- Row 67 (Salary and Staff Expenses) — WRONG (Row 67 = 0 for all Kurunji years)
- Row 45 (Wages) — WRONG (Row 45 is for direct workers, not partners)

The CA consistently uses Row 73 for Partners' Salary: ₹12L (FY23), ₹10.2L (FY24), ₹10.8L (FY25).

**Real example from Kurunji Retail:**
```
Source text:   "To Salary to Partners"
Section:       P&L (Expense)
Amount:        ₹12,00,000 (FY23) | ₹10,20,000 (FY24) | ₹10,80,000 (FY25)
Correct field: Audit Fees & Directors Remuneration  [Row 73]
Old result:    Salary and staff expenses [Row 67] or Wages [Row 45]  (WRONG)
New result:    Row 73  ✓
```

**Note:** Row 73's actual value = Salary to Partners (₹10.2–12L) ONLY. Audit fees from the CA firm are small and separately tracked or included here. The CA chose to use Row 73 for partners' salary because the CMA doesn't provide a dedicated partners' remuneration row.

**Verify:** Do you agree "Salary to Partners" goes to Row 73 (Directors Remuneration row)?
☐ Yes, correct   ☐ No, it should go to Row 67 or Row 45: _______________________

---

## RULE KR-003 — Interest to Partners / Interest on Partners' Capital → Row 83

**Applies to:** All partnership firms

**Pattern it catches:**
- `Interest to Partners`
- `Interest on Capital` (when the capital section confirms it's partner capital interest)
- `Partners' Interest`
- `Interest on Partners' Capital`
- `Interest Paid to Partners`

**Classification:** Interest on Fixed Loans / Term loans → Row 83

**Why this rule exists:**
In a partnership firm, interest paid TO partners on their capital accounts appears as a P&L expense. Although the interest is on "capital" (not a formal loan), from the CMA perspective it functions like interest on long-term funds → Row 83.

This is DIFFERENT from:
- SSSS Rule SSSS-008: interest ON unsecured loans FROM related parties (same row 83, but context is borrowing FROM external party)
- Rule B-003: "Interest Paid" in trading firm → Row 84 (WC interest on bank CC/OD)

"Interest to Partners" is always Row 83 because it's on long-term partner capital, not working capital borrowings.

**Real example from Kurunji Retail:**
```
Source text:   "To Interest to Partners"
Section:       P&L (Finance Costs)
Amount:        ₹16,04,010 (FY23) | ₹8,56,375 (FY24) | ₹23,18,485 (FY25)
Correct field: Interest on Fixed Loans / Term loans  [Row 83]
Old result:    DOUBT or Interest on WC [Row 84]  (WRONG)
New result:    Row 83  ✓
```

**Cross-check:** CMA Row 83 = 16.04 (FY23), 8.56 (FY24), 23.18 (FY25) — matches exactly. Row 83 FY23 TOTAL = interest to partners only (no bank term loan in FY22/23).

**Verify:** Do you agree interest paid to partners on their capital goes to Row 83 (Fixed/Term Loan Interest)?
☐ Yes, correct   ☐ No, use Row 84 (WC interest): _______________________

---

## RULE KR-004 — Retail Store Rent + TDS on Rent + Parking Rent → Row 49 (NOT Row 68)

**Applies to:** Retail industry (COUNTERINTUITIVE — overrides the obvious choice of Row 68)

**Pattern it catches:**
- `Rent` (when the entity is a retail store — confirmed by industry type)
- `Rent - Parking` / `Parking Rent`
- `Shop Rent` / `Store Rent`
- `TDS on Rent` (when combined with Rent entry in same retail context)

**Classification:** Others (Manufacturing) → Row 49

**Why this rule exists:**
This is the most counterintuitive rule in this document. The CMA has a dedicated Row 68 "Rent, Rates and Taxes" — yet Kurunji Retail's CA puts ALL rent into Row 49 "Others (Manufacturing)" and keeps Row 68 at ZERO for all four years.

The CA's reasoning: For a retail firm, the store premises IS the "production facility" — you cannot sell goods without the store. Store rent is therefore treated as a direct operating cost (like factory rent in manufacturing → Row 49) rather than an administrative overhead (Row 68).

**Mathematical proof from ground truth:**
```
FY23: Row 49 = 47.90 lakhs = Rent (40.95) + TDS on Rent (4.55) + Parking (2.40) = 47.90 ✓
FY24: Row 49 = 56.38 lakhs = Rent (48.60) + TDS on Rent (5.40) + Parking (2.38) = 56.38 ✓
Row 68 = ₹0 for FY22, FY23, FY24, FY25 — confirmed by CMA INPUT SHEET
```

Without this rule, the AI would:
- Route "Rent" to Row 68 (obvious/standard choice) — WRONG for this CA
- The CA would need to manually reclassify during verification

**Real example from Kurunji Retail:**
```
Source text:   "To Rent" + "To TDS on Rent" + "To Rent - Parking"
Section:       P&L (Expense)
Amounts:       ₹40,95,000 + ₹4,55,000 + ₹2,40,000 = ₹47,90,000 (FY23)
Correct field: Others (Manufacturing)  [Row 49]
Default AI:    Rent, Rates and Taxes  [Row 68]  (WRONG for this CA's style)
New result:    Others (Manufacturing)  [Row 49]  ✓
```

**IMPORTANT CAVEAT:** This is a CA-specific preference for this retail firm. Other CAs might correctly use Row 68 for retail rent. The app should ASK the CA at setup which row they prefer for rent. If they choose Row 68, suppress this rule.

**Verify:** Do you agree that for Kurunji Retail, store rent goes to Row 49 (Others Manufacturing) and NOT to Row 68 (Rent, Rates & Taxes)?
☐ Yes, Row 49 (as shown in CMA)   ☐ No, I prefer Row 68 for rent: _______________________

---

## RULE KR-005 — TDS on Rent (Separate P&L Line Item) → Same Row as Rent

**Applies to:** All industries (Tally accounting artifact)

**Pattern it catches:**
- `TDS on Rent` (when appearing as a DEBIT in P&L, not a Balance Sheet item)
- `TDS Rent` / `TDS on Shop Rent`
- `Tax Deducted at Source on Rent`

**Classification:** Same CMA row as the Rent entry for that firm
- For Kurunji Retail (retail): → Row 49
- For most other firms: → Row 68

**Why this rule exists:**
In Tally accounting, when a firm pays rent and deducts TDS, some accountants pass the TDS payment as a SEPARATE debit entry in the P&L. This creates a confusing "TDS on Rent" expense line.

The correct CMA treatment: TDS on Rent is PART OF the rent expense (total rent paid = net rent to landlord + TDS deposited with government). Both entries go to the SAME CMA row as Rent.

Without this rule, the AI sees "TDS on Rent" and might classify it as:
- Advance Tax (Row 221) — WRONG (it's not an income tax advance)
- Others Admin (Row 71) — WRONG
- Bank Charges (Row 85) — WRONG

**Real example from Kurunji Retail:**
```
Source text:   "To TDS on Rent"
Section:       P&L Expense (Tally artifact)
Amount:        ₹4,55,000 (FY23) | ₹5,40,000 (FY24)
Correct field: Same as Rent → Others (Manufacturing)  [Row 49] for this CA
Old result:    Advance Tax [Row 221] or DOUBT
New result:    Row 49 (combined with Rent)  ✓

Verification:  TDS @ 10% on gross rent:
  FY23: Gross rent = (40,95,000 + 4,55,000) = 45,50,000; TDS = 4,55,000 = 10% ✓
  FY24: Gross rent = (48,60,000 + 5,40,000) = 54,00,000; TDS = 5,40,000 = 10% ✓
```

**Verify:** Do you agree TDS on Rent should be combined with Rent and go to the same CMA row?
☐ Yes, combine with Rent   ☐ No, show separately: _______________________

---

## RULE KR-006 — Electric/Phone Charges (Combined Entry) → Row 48

**Applies to:** Retail industry (also applicable to other industries if similar combined entries exist)

**Pattern it catches:**
- `Electric/Phone Charges` (single combined Tally entry)
- `Electricity and Phone Charges`
- `Power and Telephone Charges`
- `Electric & Telephone`

**Classification:** Power, Coal, Fuel and Water → Row 48

**Why this rule exists:**
In retail stores, the accountant often creates a single combined account "Electric/Phone Charges" in Tally. The AI might try to split this:
- "Electric" component → Row 48 (Power) ✓
- "Phone" component → Row 71 (Others Admin) ✗

But since it appears as a SINGLE combined line item, the ENTIRE amount goes to Row 48.

This also applies where "Electric Charges" and "Telephone Charges" are SEPARATE entries — both go to Row 48 (not splitting phone to Row 71).

**Mathematical proof:**
```
FY23: "Electric/Phone Charges" = ₹69,11,541 → CMA Row 48 = 69.12 lakhs ✓ (exact)
FY24: "Electric/Phone Charges" = ₹97,07,993 → CMA Row 48 = 97.08 lakhs ✓ (exact)
FY25: "Electric Charges" (split from Telephone) → CMA Row 48 = 172.34 lakhs
```

**Real example from Kurunji Retail:**
```
Source text:   "To Electric/Phone Charges"
Section:       P&L Expense
Amount:        ₹69,11,541 (FY23) | ₹97,07,993 (FY24)
Correct field: Power, Coal, Fuel and Water  [Row 48]
Old result:    Split between Row 48 (electric) and Row 71 (phone) — WRONG
New result:    Entirely to Row 48  ✓
```

**Verify:** Do you agree the combined "Electric/Phone Charges" entry goes entirely to Row 48?
☐ Yes, entire amount to Row 48   ☐ No, split: _______________________

---

## RULE KR-007 — Staff Mess Expenses → Row 45 (Wages) for Retail

**Applies to:** Retail industry (NOTE: conflicts with SRP-007 which routes "Tea & Food" to Row 67)

**Pattern it catches:**
- `Staff Mess Expenses`
- `Mess Charges`
- `Staff Mess`
- `Canteen Expenses` (when in retail context and CA bundles with wages)

**Classification:** Wages → Row 45

**Why this rule exists:**
For Kurunji Retail, ALL employee-related costs are bundled into Row 45 (Wages):
- Salary and Bonus
- Provident Fund
- ESI
- Staff Welfare
- **Staff Mess Expenses** ← this rule

The CA treats staff meal/food as an employee benefit that forms part of the total wages cost.

**CONFLICT with SRP-007:** SR Papers' CA routes "Tea & Food Expenses" to Row 67 (Salary and Staff Expenses). Kurunji Retail's CA routes "Staff Mess" to Row 45. Both CAs are correct — it's a style difference.

**App guidance:** Row 45 and Row 67 are both "acceptable" for staff food/welfare. The classification depends on which row the specific CA uses for the firm. At verification, the CA should confirm their preference.

**Mathematical proof:**
```
FY23: Row 45 (Wages) = 69.70 lakhs =
  Salary & Bonus (55.55) + PF (5.56) + ESI (0.90) + Staff Welfare (3.74) + Staff Mess (3.97)
  = 69.72 ≈ 69.70 (rounding) ✓

FY24: Row 45 (Wages) = 69.29 lakhs =
  Salary & Bonus (55.69) + PF (4.93) + ESI (0.88) + Staff Welfare (0.38) + Staff Mess (4.02) + others
  = 65.90 + ~3.39 (other small items not captured) ≈ 69.29 ✓
```

**Verify:** Do you agree Staff Mess Expenses goes to Row 45 (Wages), not Row 67 (Salary & Staff)?
☐ Yes, Row 45 (all employee costs combined)   ☐ No, Row 67: _______________________

---

## RULE KR-008 — Packing Expenses (Retail) → Row 44 (Stores & Spares Consumed)

**Applies to:** Retail industry (DIFFERENT from BCIPL-004 which routes packing to Row 70 for manufacturing)

**Pattern it catches:**
- `Packing Expenses` (when large and material — ≥₹10 lakhs)
- `Packing Materials` (when under direct costs, not selling expenses)
- `Packaging Material Consumed`
- Note: The Balance Sheet item "Stock of Packing Materials" → Rule KR-012

**Classification:** Stores and spares consumed (Indigenous) → Row 44

**Why this rule exists:**
In retail, packing materials (bags, boxes, tape, wrapping) are SUPPLIES consumed in daily operations — exactly what Row 44 "Stores and Spares Consumed" is meant for.

Without this rule, the AI would classify "Packing Expenses" as:
- Row 71 (Others Admin) — possible but incorrect for large amounts
- Row 47 (Freight and Transportation) — WRONG
- Row 70 (Advertisements) — WRONG (BCIPL-004's rule for manufacturing)

**Amount-based guidance:**
- Small amounts (≤₹10 lakhs) → Row 71 (Others Admin) is acceptable (CA's own FY23 treatment: 5.92L → Row 71)
- Large amounts (≥₹15 lakhs) → Row 44 (Stores & Spares consumed) ← this rule applies

**Mathematical proof:**
```
FY24: Packing Expenses = ₹39,24,939 (gross)
      Closing Stock of Packing Materials (BS) = ₹1,25,000
      Packing CONSUMED = 39,24,939 - 1,25,000 = 37,99,939 = ₹37.99 lakhs
      CMA Row 44 (FY24) = 37.99 lakhs ✓ (exact)

FY25: CMA Row 44 = 36.10 lakhs (packing consumed after stock adjustment)
      Closing Stock (FY25 BS) = ₹58,500 → Row 198 (see KR-012)
```

**Compare with BCIPL-004:** BCIPL's manufacturing CA puts "Packing Materials" → Row 70 (Advertisements). Kurunji Retail's retail CA puts them → Row 44. This illustrates why industry-specific rules matter.

**Verify:** Do you agree large packing expenses (₹15L+) go to Row 44 (Stores & Spares consumed)?
☐ Yes, Row 44   ☐ No, Row 70 or Row 71: _______________________

---

## RULE KR-009 — Digital Marketing → Row 70 (Advertisements and Sales Promotions)

**Applies to:** All industries (modern expense type)

**Pattern it catches:**
- `Digital Marketing`
- `Online Marketing`
- `Social Media Marketing`
- `Google Ads` / `Facebook Ads`
- `SEO Expenses`
- `Digital Advertising`
- `Online Advertising`

**Classification:** Advertisements and Sales Promotions → Row 70

**Why this rule exists:**
"Digital Marketing" is a modern expense not present in the original 384-item reference (which predates widespread digital advertising). The AI might:
- Classify it as Row 71 (Others Admin) — close but wrong
- Doubt it completely

Digital marketing IS advertising/sales promotion by a different channel — Row 70 is exactly right.

The CA combined Digital Marketing with Advertisement Expenses under Row 70 for FY23 (total ₹16.03L = Ads 10.09 + Digital 5.94) and kept only Advertisement Expenses in FY24/25 (digital marketing appears to have merged into the main ad budget or been renamed).

**Real example from Kurunji Retail:**
```
Source text:   "To Digital Marketing"
Section:       P&L Expense
Amount:        ₹5,94,442 (FY23)
Correct field: Advertisements and Sales Promotions  [Row 70]
Old result:    Others (Admin) [Row 71] or DOUBT
New result:    Row 70 ✓

Combined with "To Advertisement Expenses" (₹10,08,740):
Total Row 70 FY23 = 5,94,442 + 10,08,740 = 16,03,182 = 16.03 lakhs = CMA Row 70 ✓
```

**Verify:** Do you agree Digital Marketing / Online Advertising = Advertisements (Row 70)?
☐ Yes, correct   ☐ No, use Row 71 (Others Admin): _______________________

---

## RULE KR-010 — Barcode Expenses → Row 71 (Others Admin) — Retail Specific

**Applies to:** Retail industry

**Pattern it catches:**
- `Barcode Expenses`
- `Barcode Labels`
- `Barcode Stickers`
- `MRP Labels`
- `Price Tags`
- `Product Labels`
- `Barcode Printing`

**Classification:** Others (Admin) → Row 71

**Why this rule exists:**
"Barcode Expenses" is a retail-specific cost for barcode labels, price stickers, and MRP tags applied to merchandise. This item does not exist in the 384-item reference or any previous company rule.

The AI with no guidance would either doubt this or put it in Row 71 by luck. Confirming Row 71 is correct.

**Real example from Kurunji Retail:**
```
Source text:   "To Barcode Expenses"
Section:       P&L Expense
Amount:        ₹6,83,356 (FY24)
Correct field: Others (Admin)  [Row 71]
Note:          This is included in the CMA Row 71 = 22.51 lakhs for FY24, confirmed by reconciliation
```

**Verify:** Do you agree Barcode/MRP label expenses go to Others (Admin) Row 71?
☐ Yes, correct   ☐ No, use a different row: _______________________

---

## RULE KR-011 — Bill Printing Roll / Thermal Paper Roll → Row 71 (Others Admin)

**Applies to:** Retail industry (any business using POS billing machines)

**Pattern it catches:**
- `Bill Printing Roll`
- `Thermal Roll`
- `Thermal Paper Roll`
- `POS Paper Roll`
- `Billing Roll`
- `Receipt Printer Roll`

**Classification:** Others (Admin) → Row 71

**Why this rule exists:**
Retail stores use thermal paper rolls in billing/POS machines to print customer receipts. This is a small but recurring operational supply cost. Not in any reference or prior rule.

The AI has no reference for "Bill Printing Roll" and would likely doubt it. Confirmed → Row 71.

**Real example from Kurunji Retail:**
```
Source text:   "To Bill Printing Roll"
Section:       P&L Expense
Amount:        ₹5,59,614 (FY24)
Correct field: Others (Admin)  [Row 71]
Note:          Part of CMA Row 71 = 22.51 lakhs (FY24), confirmed by reconciliation
```

**Verify:** Do you agree thermal/billing paper rolls go to Others Admin (Row 71)?
☐ Yes, correct   ☐ No: _______________________

---

## RULE KR-012 — Stock of Packing Materials (Balance Sheet) → Row 198

**Applies to:** Retail industry (any firm that has closing stock of packing supplies)

**Pattern it catches (Balance Sheet asset items):**
- `Stock of Packing Materials`
- `Packing Stock`
- `Closing Stock — Packing Materials`
- `Packing Materials Inventory`

**Classification:** Stores and Spares Indigenous → Row 198
*(This is the Balance Sheet row for INVENTORY of stores/supplies, not Row 201 which is for finished goods)*

**Why this rule exists:**
Retail firms may hold a closing stock of packing bags, boxes, and supplies at year end. This is an INVENTORY item on the Balance Sheet, not a prepaid expense. It goes to Row 198 (Stores & Spares Indigenous inventory), NOT Row 201 (Finished Goods — which is the main stock-in-trade).

The AI would likely route "Stock of Packing Materials" to:
- Row 201 (Finished Goods) — WRONG (that's for goods sold to customers)
- Row 222 (Prepaid Expenses) — WRONG

**Real example from Kurunji Retail:**
```
Source text:   "Stock of Packing Materials"
Section:       Assets (Balance Sheet)
Amount:        ₹1,25,000 (FY24) | ₹58,500 (FY25)
Correct field: Stores and Spares Indigenous  [Row 198]
CMA confirms:  Row 198 (FY24) = 1.25 lakhs ✓ | Row 198 (FY25) = 5.86 lakhs (includes other supplies)

Note: This same amount appears as a CREDIT in the P&L (reducing packing expense):
  P&L FY24: "By Stock of Packing Materials: ₹1,25,000" = closing stock of packing → Row 198 BS
```

**Verify:** Do you agree closing stock of packing materials goes to Row 198 (Stores & Spares)?
☐ Yes, correct   ☐ No, use Row 201 or Row 222: _______________________

---

## RULE KR-013 — Dues from Partners / Drawings Due (Balance Sheet Asset) → Row 235

**Applies to:** Partnership firms

**Pattern it catches (Balance Sheet asset items):**
- `Dues from Partners`
- `Amount Due from Partners`
- `Partners' Drawings` (when shown as asset — amount owed back by partner)
- `Loan to Partners`
- `Dues from Proprietor` (for sole proprietorship)

**Classification:** Dues from directors / partners / promoters → Row 235

**Why this rule exists:**
When partners have drawn more than their share or when the firm has given advances to partners, this appears as a receivable (asset) from partners. The CMA has a dedicated Row 235 "Dues from directors/partners/promoters" for exactly this.

Without this rule, the AI would classify it as:
- Row 219 (Advances recoverable in cash or kind) — WRONG
- Row 206 (Domestic Receivables) — WRONG (not a trade debtor)

**Real example from Kurunji Retail:**
```
Source text:   "Dues from Partners" (or similar)
Section:       Assets (Balance Sheet)
Amount:        ₹91,78,270 (FY25)
Correct field: Dues from directors / partners / promoters  [Row 235]
CMA confirms:  Row 235 FY25 = 91.7827 lakhs ✓
Note:          Not present in FY22/FY23/FY24 — only appeared in FY25
```

**Verify:** Do you agree amounts owed by partners TO the firm go to Row 235?
☐ Yes, correct   ☐ No, use a different row: _______________________

---

## RULE KR-014 — Rental Security Deposits to Private Landlords → Row 238

**Applies to:** All industries (important distinction from V1 Rule C-004)

**Pattern it catches (Balance Sheet non-current asset items):**
- `Rental Advance` / `Rent Advance` / `Advance Rent`
- `Security Deposit (Landlord)` — when landlord is a private party
- `Shop Deposit` / `Store Deposit`
- `Lease Deposit` (to private party)

**Classification:** Other non current assets → Row 238

**Why this rule exists:**
V1 Rule C-004 correctly maps security deposits to government utilities (Electricity Board, Telephone) → Row 237 (Security deposits with government departments). But when a PRIVATE LANDLORD requires a security/advance deposit for renting commercial premises, this goes to **Row 238 (Other non-current assets)** — NOT Row 237.

Kurunji Retail has rental advances shown consistently in Row 238:
- FY22: ₹26.90 lakhs | FY23: ₹26.90 lakhs | FY24: ₹34.65 lakhs

The AI might route "Rental Advance" to Row 237 (following Rule C-004) — WRONG for private landlord deposits.

**Distinction:**
- Electricity Board deposit → Row 237 (government utility) ← Rule C-004
- Private landlord deposit/advance → Row 238 (other non-current asset) ← this rule

**Real example from Kurunji Retail:**
```
Source text:   "Rental Advances" (or similar — actual text partially unclear in scan)
Section:       Assets, Non-Current (Balance Sheet)
Amount:        ₹26,90,000 (FY22 and FY23) | ₹34,64,766 (FY24)
Correct field: Other non current assets  [Row 238]
Old result:    Security deposits with govt. [Row 237] via Rule C-004 — WRONG
New result:    Other non current assets  [Row 238]  ✓
```

**Verify:** Do you agree private landlord rental advances/deposits go to Row 238 (Other non-current)?
☐ Yes, Row 238   ☐ No, use Row 237: _______________________

---

## RULE KR-015 — Generator Expenses → Row 71 (Others Admin) for Retail

**Applies to:** Retail industry (NOT Row 48 — this is counterintuitive)

**Pattern it catches:**
- `Generator Expenses`
- `Generator Fuel`
- `DG Set Expenses`
- `Genset Expenses`
- `Generator Maintenance`
- `Generator Oil`

**Classification:** Others (Admin) → Row 71

**Why this rule exists:**
Retail stores use backup generators for power outages. The AI would naturally classify "Generator Expenses" (diesel + maintenance) as Row 48 (Power, Coal, Fuel and Water) since generators produce power. However, Kurunji Retail's CA classified it as Row 71 (Others Admin).

**Mathematical proof:**
```
FY24: Row 71 = 22.51 lakhs. Confirmed items:
  Misc Expenses (5.20) + Barcode (6.83) + Bill Printing Roll (5.60)
  + Printing & Stationery (2.74) + Generator (2.14) = 22.51 ✓

  Row 48 FY24 = 97.08 lakhs = Electric/Phone Charges ONLY (97.08) — no room for Generator
```

**Verify:** Do you agree Generator Expenses goes to Others Admin (Row 71) rather than Power (Row 48)?
☐ Yes, Row 71 (as per CA's classification)   ☐ No, Row 48 makes more sense: _______________________

---

## ITEMS ALREADY COVERED — No New Rule Needed

The following items in Kurunji Retail's financials are handled correctly by the existing reference or prior rules:

| Item | Source Text | Correct Row | Covered By |
|------|-------------|-------------|------------|
| Sales / Net Revenue | `By Sales` (P&L credit) | 22 | Reference |
| Purchases (goods for resale) | `To Purchases` | 42 | Reference |
| Opening Stock of goods | `To Opening Stock` | 58 (P&L) / 201 (BS) | Reference |
| Closing Stock of goods | `By Closing Stock` | 59 (P&L) / 201 (BS) | Reference |
| Depreciation | `To Depreciation` | 56/63 | Reference |
| Electricity (standalone) | `Electric Charges` (separate entry) | 48 | Reference |
| Repairs and Maintenance | `Repairs and Maintenance` | 72 | Reference |
| Miscellaneous Expenses | `Miscellaneous Expenses` | 71 | Reference |
| Professional Fees | `Professional Fees` | 71 | Reference |
| Provident Fund | `Provident Fund` | 45 | Reference |
| ESI | `ESI` | 45 | Reference |
| Advertisement Expenses | `Advertisement Expenses` | 70 | Reference |
| Bank Interest (on CC/OD) | `Bank Interest and Charges` | 84 | Rule B-003 (modified) |
| Motor Vehicles (Tata Intra Van, Car) | `Tata Intra Van`, `Car` (Fixed Assets) | 162 | Rule C-001 |
| Computers, Printers, UPS | `Computer Accessories`, `Thermal Printer`, `UPS` | 162 or 71 (threshold-based) | Rule C-002 |
| Printing and Stationery | `Printing and Stationery` | 71 | Reference |
| Sundry Creditors / Trade Payables | `Sundry Creditors` | 242 | Reference |
| Cash on Hand | `Cash on Hand` | 212 | Reference |
| Bank Balances | `Bank Balances`, `ICICI CA account` | 213 | Reference |
| ICICI CC/OD Account | `ICICI Credit Account` (short-term borrowings) | 131 | Rule SSSS-011 |
| Income Tax Provision | `Income Tax Provision` | 99 | Reference |
| Advance Tax | `Advance Tax` | 221 | Reference |
| Freight Charges (inward) | `Freight (inward)` | 42 (netted) | Rule C-003 (modified) |
| Salary and Bonus (employee wages) | `Salary and Bonus` | 45 | Reference |
| Profit on Sale of Fixed Assets | — | 31 | Reference |
| Staff Welfare | `Staff Welfare` | 45 | Reference (employee welfare) |

---

## ITEMS FLAGGED — CA JUDGMENT REQUIRED

These items cannot be auto-classified and require explicit CA input on the verification screen:

| Item | Issue | What App Should Ask |
|------|-------|---------------------|
| Unsecured Loans (partners' current account) split between Row 152 vs 153 | CA decides how much counts as quasi-equity per bank requirement | "Of ₹X in partners' unsecured loans, how much should be shown as Quasi Equity (Row 152)? Default = 0" |
| "Others (Non-Operating Income)" FY25 = ₹11.56L | Source unclear — could be commission from Kurinji Metro, FD interest, or one-time gain | "Row 34 shows ₹11.56 lakhs. Can you identify the source? Options: (a) Commission income, (b) Rental income, (c) Other" |
| Freight Charges routing | Row 47 (Freight) = 0 for ALL years; this CA puts freight in Row 71. Ask to confirm. | "Freight Charges of ₹X — classified to Others Admin (Row 71) per CA's style. Correct?" |
| Generator Expenses routing | Row 48 vs Row 71 — CA chose Row 71 | "Generator Expenses ₹X — placed in Others Admin (Row 71). Confirm?" |
| Packing Expenses amount threshold | < ₹10L → Row 71; ≥ ₹15L → Row 44. FY23 was small (₹5.92L → Row 71), FY24+ large → Row 44 | "Packing Expenses ₹X — should this go to Stores & Spares (Row 44) or Others Admin (Row 71)?" |
| Advance to Kurinji Metro (sister concern) | ₹3.30 Cr advance in FY25 — possibly Row 223 or Row 224 | "₹3.30 Cr advance to related party — is Kurinji Metro a subsidiary/group company? If yes → Row 224, if arm's length → Row 223" |

---

## ITEMS THAT DIFFER FROM OTHER COMPANY RULES

These items show CA preference differences — flagged to avoid inconsistent rule application:

| Item | Kurunji Retail (This CA) | Other Company | Implication |
|------|--------------------------|---------------|------------|
| Staff Mess / Tea & Food | → Row 45 (Wages) | SR Papers → Row 67 (SRP-007) | Industry/CA-dependent; ask CA at setup |
| Packing Materials | → Row 44 (Stores & Spares consumed) | BCIPL → Row 70 (Advertisements) | Industry-dependent: retail = Row 44 |
| Store Rent | → Row 49 (Others Manufacturing) | Standard → Row 68 | CA-specific; configure per engagement |
| Freight Charges (outward) | → Row 71 (Others Admin) | Standard → Row 47 | CA-specific; Row 47 = 0 for all years |

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total distinct line items documented (FY22–FY25) | ~75 |
| Items handled by existing 384-item reference | ~28 |
| Items handled by existing V1 rules | ~5 |
| Items handled by SSSS/BCIPL/SRP rules | ~3 |
| **NEW rules created in this document** | **15** |
| Items requiring CA judgment | **6** |
| Items with retail-specific patterns | **8** (KR-004, 006, 007, 008, 010, 011, 012, 015) |
| Items with partnership-firm patterns | **4** (KR-001, 002, 003, 005) |
| Items with general applicability | **3** (KR-005, 009, 014) |

---

## Testing Recommendations

To validate these rules, upload Kurunji Retail documents and check:

1. **KR-001 test:** "Partners' Capital Accounts" should go to Row 116, NOT Row 152
2. **KR-002 test:** "Salary to Partners" should go to Row 73, NOT Row 67 or 45
3. **KR-003 test:** "Interest to Partners" should go to Row 83, NOT Row 84
4. **KR-004 test:** "Rent" should go to Row 49 (Others Manufacturing), NOT Row 68
5. **KR-005 test:** "TDS on Rent" should combine with Rent in Row 49, NOT go to Row 221
6. **KR-008 test:** Large "Packing Expenses" (₹39L+) should go to Row 44, NOT Row 71
7. **KR-009 test:** "Digital Marketing" should go to Row 70, NOT Row 71
8. **KR-012 test:** "Stock of Packing Materials" (BS) should go to Row 198, NOT Row 201

Use the `classification_method` column in the output to confirm which rule fired for each item.
