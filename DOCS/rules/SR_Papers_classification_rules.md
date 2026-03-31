# CMA Classification Rules — SR Papers

**Company:** S.R. Papers Private Limited
**Industry:** Paper Trading / Distribution (multi-branch, import-heavy)
**Financial Years Covered:** FY2023, FY2024, FY2025
**Total line items analysed:** 68 (P&L) + 32 (Balance Sheet) = 100
**New rules generated:** 22 (SRP-001 to SRP-022)
**Items already covered by existing 384-item reference:** ~48
**Items with no CMA impact (round-off, zero values):** ~10

---

## Coverage Summary

### Already Handled by 384-Item Reference (no new rule needed)
These items were present in SR Papers but the reference should correctly classify them:
- Power and Fuel → Row 48
- Rent → Row 68; Rates and Taxes → Row 68
- Bank Interest → Row 30
- Audit Fees → Row 73
- Depreciation → Row 56
- Insurance → Row 71
- Travelling and Conveyance → Row 71
- Printing and Stationery → Row 71
- Professional Fees → Row 71
- Communication/Connectivity → Row 71
- Computer Maintenance → Row 71
- Miscellaneous Expenses → Row 71
- Repairs and Maintenance → Row 50
- Share Capital → Row 116
- General Reserve → Row 121
- Share Premium → Row 123
- Trade Payables → Row 242
- Cash on Hand → Row 212
- Bank Balances → Row 213
- Trade Receivables → Row 206

### Already Handled by classification_rules_v1.md
- Security Deposits (Rule C-004) → Row 237
- Motor Vehicles (Rule C-001) → Row 162 (Gross Block)
- ALL CAPS vendor names as creditors (Rule B-002) → Row 242

---

## NEW RULES

---

## RULE SRP-001 — Customs Duty → Imported Raw Materials (NOT Admin Expense)

**Applies to:** All industries with imported goods

**Pattern it catches:**
- `Customs Duty`
- `Import Duty`
- `Basic Customs Duty`
- `BCD` (Basic Customs Duty abbreviation)
- Located in P&L Other Expenses / Indirect Expenses section

**Classification:** Raw Materials Consumed (Imported) → Row 41

**Why this rule exists:**
Customs duty paid on imported raw materials is part of the LANDED COST of those materials,
not an administrative expense. Without this rule, the AI sees "Customs Duty" in the
Other Expenses section and classifies it as a duty/tax expense under Row 71 (Others Admin)
or doubts it.

For SR Papers (paper importer), customs duty = cost of importing paper reels from abroad.
The CA correctly places it in Row 41 (Imported Raw Materials) because it's indistinguishable
from the raw material cost itself.

This pattern is common for ANY company that imports raw materials or traded goods.

**Real example from SR Papers:**
```
Source text:   "Customs Duty"
Section:       Other Expenses (Note 17)
Amount:        FY2023: ₹13,12,396 | FY2024: ₹5,80,553 | FY2025: ₹90
Correct field: Raw Materials Consumed (Imported)  [Row 41]
Old result:    Others (Admin) or DOUBT
New result:    Raw Materials Consumed (Imported), confidence 0.97  ✓
```

**Exception — when this rule would be WRONG:**
If customs duty appears on the BALANCE SHEET (as "Customs Duty Recoverable") — that's a
current asset, not raw materials. The rule should only fire for P&L expense items.

**Verify:** Do you agree customs duty on imports = imported raw material cost?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE SRP-002 — Hamali Charges → Freight and Transportation

**Applies to:** All industries (especially trading, manufacturing, warehousing)

**Pattern it catches:**
- `Hamali Charges`
- `Hamali`
- `Hamali Labour`
- `Mathadi` (Pune/Maharashtra-specific labor union term)
- `Unloading Charges`
- `Unloading Charges – Mathadi`
- `Loading Charges`
- `Loading and Unloading`

**Classification:** Freight and Transportation Charges → Row 47

**Why this rule exists:**
"Hamali" is the traditional Indian term for loading/unloading workers (also called "coolies"
or "mathadi workers" in Maharashtra). These charges appear in almost every trading and
manufacturing company's accounts but are NOT in any international accounting terminology.

The AI, having no knowledge of this term, either doubts it or classifies it as wages/labor.
But it belongs in Freight and Transportation because it is the cost of physically handling
goods — inseparable from transportation costs.

In SR Papers, Hamali + Unloading Charges Mathadi = EXACTLY the CMA Row 47 value:
FY2023: ₹13,84,449 + ₹2,18,260 = ₹16,02,709 = CMA Row 47 ✓

**Real example from SR Papers:**
```
Source text:   "Hamali Charges"
Amount:        ₹13,84,449 (FY2023)
Correct field: Freight and Transportation Charges  [Row 47]
Old result:    Wages (WRONG) or DOUBT
New result:    Freight and Transportation Charges  ✓

Source text:   "Unloading Charges - Mathadi"
Amount:        ₹2,18,260 (FY2023)
Correct field: Freight and Transportation Charges  [Row 47]
```

**Verify:** Do you agree Hamali/loading-unloading charges go to Freight and Transportation?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE SRP-003 — Customs-Related Import Charges → Other Manufacturing Exp (CMA)

**Applies to:** Companies that import goods (trading, manufacturing)

**Pattern it catches:**
- `CFS Charges` (Container Freight Station)
- `CFS` in expense context
- `Clearance Charges`
- `Port Clearance`
- `Liner Charges`
- `Ocean Freight`
- `Detention Charges` (port)
- `Demurrage`

**Classification:** Other Manufacturing Exp (CMA) → Row 64

**Why this rule exists:**
CFS (Container Freight Station), clearance, and liner charges are import logistics costs
that sit BETWEEN customs duty (Row 41) and normal domestic freight (Row 47).

The AI might classify these as:
- Bank Charges (wrong)
- Others (Admin) (wrong — these are not administrative)
- Freight and Transportation Charges (close, but the CA separates import logistics into Row 64)

For SR Papers, the CA places all import-chain costs (Clearance + CFS + Liner) into
"Other Manufacturing Exp (CMA)" Row 64 along with Delivery Charges — treating the
full distribution overhead as a manufacturing cost for CMA reporting.

**Real examples from SR Papers:**
```
"CFS Charges"         FY2023: ₹2,13,843  → Row 64
"Clearance Charges"   FY2023: ₹1,48,750  → Row 64
"Liner Charges"       FY2023: ₹3,09,772  → Row 64
```

**Important note for CA to verify:**
This rule places import logistics in Row 64. Some CAs may prefer Row 47 (Freight).
The key question: does your CA place import freight separately from domestic freight?

**Verify:** Do you agree CFS/Clearance/Liner charges go to Row 64 (Other Mfg Exp)?
☐ Yes, Row 64   ☐ No, use Row 47 (Freight)   ☐ No, other: _______

---

## RULE SRP-004 — Delivery Charges (Outward/Distribution) → Other Manufacturing Exp

**Applies to:** Trading companies, distributors

**Pattern it catches:**
- `Delivery Charges`
- `Courier Charges` (when large amounts for goods distribution)
- `Distribution Charges`
- `Outward Freight`
- Note: ONLY when in the manufacturing/distribution cost section, large amounts

**Classification:** Other Manufacturing Exp (CMA) → Row 64

**Why this rule exists:**
For paper distributors, "Delivery Charges" is the cost of getting paper from the warehouse
to customers — a core part of the distribution operation, NOT just an admin delivery cost.

SR Papers spends ₹68–98 lakhs/year on delivery charges — this is their primary distribution
expense. The CA classifies this as a manufacturing/distribution overhead (Row 64) rather
than selling expense (Row 71 Others Admin).

The AI without this rule will likely put Delivery Charges in Freight Row 47 or Admin Row 71.
Both are wrong for this CA's style — it goes to Row 64.

**Real example from SR Papers:**
```
Source text:   "Delivery Charges"
Amount:        FY2023: ₹68,12,091 | FY2024: ₹72,09,185 | FY2025: ₹98,39,745
Correct field: Other Manufacturing Exp (CMA)  [Row 64]
Old result:    Freight (Row 47) or Others Admin (Row 71) — WRONG
New result:    Row 64  ✓
```

**Caution:** "Delivery Charges" may be a small petty amount in other companies (₹500–2000)
where it represents courier/speed-post. In that case Row 71 (Others Admin) is correct.
This rule only applies when delivery = large distribution operation.

**Verify:** Do you agree large delivery/courier charges for paper distribution go to Row 64?
☐ Yes, Row 64   ☐ No, use Row 47 Freight   ☐ Depends on amount: _______

---

## RULE SRP-005 — Discount Received → Others (Non-Operating Income)

**Applies to:** All industries (especially trading companies)

**Pattern it catches:**
- `Discount Received`
- `Discount Rec'd`
- `Discount Income`
- `Trade Discount Received`
- Located in INCOME section (Other Income / Non-Operating Income)

**Classification:** Others (Non-Operating Income) → Row 34

**Why this rule exists:**
When a buyer receives a trade discount from their supplier, it reduces their purchase cost.
Some companies record this as a credit in their "Other Income" note. The CA treats this as
non-operating income (Row 34) rather than netting it against raw material purchases.

Without this rule, the AI sees "Discount Received" and either:
- Confuses it with "Discount Allowed" (an expense, Row 70) — reversed direction
- Classifies it as Domestic Sales (Row 22) — wrong type

For SR Papers, Discount Received is ₹31–36 lakhs/year — their second-largest other income item.

**Real example from SR Papers:**
```
Source text:   "Discount Recieved"  [note: misspelling in source]
Section:       Note 13: Other Income
Amount:        FY2023: ₹31,88,891 | FY2024: ₹36,55,025 | FY2025: ₹69,623
Correct field: Others (Non-Operating Income)  [Row 34]
Old result:    Domestic Sales (WRONG) or Advertisements (WRONG)
New result:    Others (Non-Operating Income)  ✓
```

**Contrast with "Discount Allowed":**
```
"Discount Allowed"  (expense) → Advertisements and Sales Promotions  [Row 70]
"Discount Received" (income) → Others (Non-Operating Income)         [Row 34]
```

**Verify:** Do you agree supplier discounts received = non-operating income Row 34?
☐ Yes, correct   ☐ No, it should net against raw materials: _______

---

## RULE SRP-006 — Admin Exp for PF → Salary and Staff Expenses

**Applies to:** All industries

**Pattern it catches:**
- `Admin Exp for PF`
- `Admin Charges for PF`
- `PF Admin Charges`
- `EPFO Admin Charges`
- `Employees Provident Fund – Admin`
- `PF Administration Charges`

**Classification:** Salary and staff expenses → Row 67

**Why this rule exists:**
The EPFO (Employees' Provident Fund Organisation) charges a small administration fee
on provident fund contributions — currently 0.5% of wages. Accountants record this as
"Admin Exp for PF" or similar. This is an employee-related cost but is NOT part of PF
contributions themselves (which go to Row 45 Wages).

The CA groups this in Row 67 (Salary and staff expenses) — the admin overhead portion
of employee costs. The AI, not knowing this term, may put it in:
- Others (Admin) Row 71 (close but wrong)
- Wages Row 45 (wrong — it's admin overhead, not wages)

**Real example from SR Papers:**
```
Source text:   "Admin Exp for PF"
Amount:        FY2023: ₹25,300 | FY2024: ₹25,254 | FY2025: ₹26,711
Correct field: Salary and staff expenses  [Row 67]
Old result:    Others (Admin) (Row 71) or DOUBT
New result:    Salary and staff expenses  ✓
```

**Verify:** Do you agree EPFO admin charges go to Salary and staff expenses (Row 67)?
☐ Yes, correct   ☐ No, use Row 71 Others (Admin): _______

---

## RULE SRP-007 — Tea & Food Expenses → Salary and Staff Expenses

**Applies to:** All industries

**Pattern it catches:**
- `Tea & Food Expenses`
- `Tea and Food`
- `Tea Expenses`
- `Staff Refreshments`
- `Office Tea/Coffee`
- `Canteen Expenses`
- `Meal Expenses` (small amounts)

**Classification:** Salary and staff expenses → Row 67

**Why this rule exists:**
Staff tea/food/refreshment expenses are a sub-type of employee welfare. SR Papers' CA
groups them with "Salary and staff expenses" (Row 67) — treating them as a non-cash
component of staff compensation.

Without this rule, the AI would likely put Tea & Food under:
- Others (Admin) Row 71 (plausible but wrong per this CA's style)
- Entertainment Expenses → Others (Admin) Row 71 (also wrong)

Confirmed across all 3 years — consistent pattern:
FY2023: Admin PF (25,300) + Tea & Food (2,18,533) = 2,43,833 = CMA Row 67 ✓
FY2024: Admin PF (25,254) + Tea & Food (2,37,753) = 2,63,007 = CMA Row 67 ✓
FY2025: Admin PF (26,711) + Tea & Food (2,64,024) = 2,90,735 = CMA Row 67 ✓

**Real example from SR Papers:**
```
Source text:   "Tea & Food Expenses"
Amount:        FY2023: ₹2,18,533 | FY2024: ₹2,37,753 | FY2025: ₹2,64,024
Correct field: Salary and staff expenses  [Row 67]
Old result:    Others (Admin) (Row 71) — different bucket
New result:    Salary and staff expenses  ✓
```

**Verify:** Do you agree staff tea/food goes to Salary and staff expenses (Row 67)?
☐ Yes, correct   ☐ No, use Others (Admin) Row 71: _______

---

## RULE SRP-008 — Factory Expenses → Others (Manufacturing)

**Applies to:** Manufacturing and distribution companies

**Pattern it catches:**
- `Factory Expenses`
- `Factory Exp`
- `Factory Overheads`
- `Factory Running Expenses`
- `Godown Expenses`
- `Warehouse Expenses`
- `Godown Running Expenses`

**Classification:** Others (Manufacturing) → Row 49

**Why this rule exists:**
"Factory Expenses" is a catch-all for manufacturing overhead — electricity, water, cleaning,
maintenance supplies that cannot be attributed to a specific asset. For a paper distribution
company like SR Papers, this represents godown/warehouse operating expenses.

The AI may classify this as:
- Others (Admin) Row 71 (wrong category — this is production overhead)
- Power, Coal, Fuel Row 48 (wrong — Factory Exp is more general)

**Real example from SR Papers:**
```
Source text:   "Factory Expences"  [note: misspelling in source]
Amount:        FY2023: ₹5,24,890 | FY2024: ₹9,04,447 | FY2025: ₹4,69,643
Correct field: Others (Manufacturing)  [Row 49]
Old result:    Others (Admin) (Row 71) — WRONG
New result:    Others (Manufacturing)  ✓
```

**Verify:** Do you agree factory/godown expenses go to Others (Manufacturing) Row 49?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE SRP-009 — Royalty Paid → Others (Manufacturing)

**Applies to:** Manufacturing, licensing, trading companies

**Pattern it catches:**
- `Royalty Paid`
- `Royalty`
- `License Fee` (product brand license)
- `Brand License`
- `Trademark License`
- Note: Context must be product/brand licensing, NOT intangible asset amortization

**Classification:** Others (Manufacturing) → Row 49

**Why this rule exists:**
Royalty paid for using a brand name or product license is a cost of goods sold — it's
paid per unit of sales or as a percentage of revenue. For SR Papers, royalty is paid
for the right to distribute specific paper brands.

The AI might confuse this with:
- Deferred Revenue Expenditures Row 76 (wrong — royalties are current period costs)
- Others (Admin) Row 71 (wrong — this is a production/distribution cost)
- Miscellaneous Expenses Row 75 (wrong)

**Real example from SR Papers:**
```
Source text:   "Royality Paid"  [note: misspelling in source — "Royality" not "Royalty"]
Amount:        FY2023: ₹16,78,359 | FY2024: ₹20,95,330 | FY2025: ₹0
Correct field: Others (Manufacturing)  [Row 49]
Old result:    DOUBT or Others Admin (Row 71)
New result:    Others (Manufacturing)  ✓
```

**Alert for OCR:** The source text misspells "Royalty" as "Royality" — OCR and fuzzy matching
must catch this variant.

**Verify:** Do you agree royalty/license fees for product distribution = Others (Mfg) Row 49?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE SRP-010 — Stereo Charges → Advertisements and Sales Promotions

**Applies to:** Paper, printing, packaging industries

**Pattern it catches:**
- `Stereo Charges`
- `Stereo`
- `Printing Plate Charges`
- `Block Charges` (in printing context)
- `Plate Charges`
- `Cliché Charges`

**Classification:** Advertisements and Sales Promotions → Row 70

**Why this rule exists:**
"Stereo" or "printing stereo" refers to the printing plates or blocks used to create
packaging, labels, and promotional materials. For paper companies, stereo charges are
incurred to print company branding on paper products.

The AI has no knowledge of this printing industry term and will likely doubt it or
classify it as machinery maintenance (Row 50) or miscellaneous (Row 71).

**Real example from SR Papers:**
```
Source text:   "Stereo Charges"
Amount:        FY2023: ₹1,06,763 | FY2024: ₹1,90,354 | FY2025: (-)₹5,500 [reversal]
Correct field: Advertisements and Sales Promotions  [Row 70]
Old result:    DOUBT (AI unfamiliar with term)
New result:    Advertisements and Sales Promotions  ✓
```

**Note on negative amount (FY2025):** A negative Stereo Charges = reversal of a prior
booking. It should still go to Row 70 (as a deduction from advertisements expense).

**Verify:** Do you agree stereo/printing plate charges = Advertisements (Row 70)?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE SRP-011 — Discount Allowed → Advertisements and Sales Promotions

**Applies to:** All industries (especially trading companies)

**Pattern it catches:**
- `Discount Allowed`
- `Discount Given`
- `Cash Discount Allowed`
- `Trade Discount Allowed`
- Located in EXPENSE section
- Note: This is the EXPENSE side (not "Discount Received" which is income)

**Classification:** Advertisements and Sales Promotions → Row 70

**Why this rule exists:**
Trade/cash discounts given to customers are a form of sales promotion — they incentivize
purchases. The CA classifies them with advertising and sales promotion expenses.

The AI may classify "Discount Allowed" as:
- Others (Admin) Row 71 (wrong bucket)
- Less: Excise Duty Row 25 (very wrong)
- Sales deduction (wrong — it's an expense not a revenue reduction in this format)

**Real example from SR Papers:**
```
Source text:   "Discount Allowed"
Section:       Note 17: Other Expenses
Amount:        FY2023: ₹85,278 | FY2024: ₹2,79,866 | FY2025: ₹5,71,589
Correct field: Advertisements and Sales Promotions  [Row 70]
Old result:    Others (Admin) — wrong bucket
New result:    Advertisements and Sales Promotions  ✓
```

**Note on "Discount Reversal":**
SR Papers also has "Discount Reversal" — a reversal of previously given discounts.
This also goes to Row 70 (as a negative/credit entry reducing total promotions expense).

**Verify:** Do you agree trade discounts given to customers = Advertisements Row 70?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE SRP-012 — Commission & Brokerage → Advertisements and Sales Promotions

**Applies to:** All industries

**Pattern it catches:**
- `Commission & Brokerage`
- `Commission Paid`
- `Sales Commission`
- `Brokerage`
- `Agent Commission`
- `Marketing Commission`
- Note: Only P&L expense items — NOT commission income

**Classification:** Advertisements and Sales Promotions → Row 70

**Why this rule exists:**
Commission paid to sales agents and brokers is a selling expense — it's the cost of
acquiring customers or completing transactions. The CA groups it with other sales promotion
expenses in Row 70.

The AI might put this in:
- Others (Admin) Row 71 (close but wrong — it's a selling cost, not admin)
- Others (Non-Operating Expenses) Row 93 (very wrong)

This is consistent with Rule D in the existing rules — the CA treats commission as
a revenue/selling expense.

**Real example from SR Papers:**
```
Source text:   "Commission & Brokerage"
Amount:        FY2023: ₹8,52,827 | FY2024: ₹7,52,446 | FY2025: ₹7,62,170
Correct field: Advertisements and Sales Promotions  [Row 70]
Old result:    Others (Admin) (Row 71) — wrong bucket
New result:    Advertisements and Sales Promotions  ✓
```

**Verify:** Do you agree commission and brokerage = Advertisements and Sales Promotions Row 70?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE SRP-013 — Business Promotion → Advertisements and Sales Promotions

**Applies to:** All industries

**Pattern it catches:**
- `Business Promotion`
- `Business Promotion Expenses`
- `Sales Promotion`
- `Marketing Expenses`

**Classification:** Advertisements and Sales Promotions → Row 70

**Why this rule exists:**
"Business Promotion" is a common expense label in Indian accounting that covers customer
entertainment, gifts to dealers/retailers, participation in trade shows, and direct
marketing activities. This clearly belongs in Row 70.

The AI should handle this, but the 384-item reference may or may not include it. The CA
consistently puts it in Row 70.

**Real example from SR Papers:**
```
Source text:   "Business promotion"
Amount:        FY2023: ₹10,94,893 | FY2024: ₹12,65,046 | FY2025: ₹8,04,876
Correct field: Advertisements and Sales Promotions  [Row 70]
```

**Verify:** Do you agree business promotion = Advertisements and Sales Promotions Row 70?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE SRP-014 — FSC License Charges → Others (Admin)

**Applies to:** Paper, forestry, wood products industries

**Pattern it catches:**
- `FSC License Charges`
- `FSC Certification`
- `Forest Stewardship Council`
- `FSC`
- `ISO Certification Charges`
- `Certification Charges`
- `BIS Registration`
- `FSSAI License`

**Classification:** Others (Admin) → Row 71

**Why this rule exists:**
FSC (Forest Stewardship Council) certification is mandatory for paper companies that
source from responsibly managed forests. It's a regulatory compliance cost — similar
to ISO certification fees. This is an administrative/regulatory overhead.

The AI might classify this as:
- Others (Manufacturing) Row 49 (wrong — it's compliance, not production)
- Miscellaneous Expenses Row 75 (wrong)
- DOUBT (AI doesn't know FSC)

**Real example from SR Papers:**
```
Source text:   "FSC License Charges"
Amount:        FY2023: ₹3,93,200 | FY2024: ₹0 | FY2025: ₹0
Correct field: Others (Admin)  [Row 71]
Old result:    DOUBT (AI unfamiliar with FSC)
New result:    Others (Admin)  ✓
```

**Verify:** Do you agree FSC/certification license fees = Others (Admin) Row 71?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE SRP-015 — Finance Cost Split into TL vs WC Interest

**Applies to:** Companies with BOTH term loans AND cash credit/overdraft

**Pattern it catches:**
- `Finance Cost` → single combined line in P&L
- `Interest Expenses – Others` → combined interest line
- `Interest Paid` → when no loan type specified
- Combined interest when Note 16 shows only one line

**Classification:**
- Interest relating to term loans → Interest on Fixed Loans / Term Loans → Row 83
- Interest relating to CC/OD → Interest on Working Capital Loans → Row 84
- Bank processing fees from Note 17 → Bank Charges → Row 85

**Why this rule exists:**
SR Papers' Note 16 shows all interest as a single "Others" line. The CA manually splits it
into TL interest (Row 83), WC interest (Row 84), and Bank Charges (Row 85) using the
loan schedule from the Details/TL sheet — information NOT available in the P&L notes alone.

The app CANNOT automatically split interest without the loan schedule. This item MUST
go to the verification screen (doubt report) so the user can enter the correct split.

**Real example from SR Papers:**
```
Source text:   "Finance Cost – Others"
Total Amount:  FY2023: ₹2,83,88,411
CA split:      TL interest: ₹54,61,590 (Row 83)
               WC interest: ₹1,27,66,043 (Row 84)
               Bank charges: ₹1,02,23,514 (Row 85)
               + Note 17 Bank charges: ₹62,736 (also Row 85)
Old result:    DOUBT (correct — this requires manual split)
New result:    → DOUBT with prompt: "Split Finance Cost into TL/WC/Bank per loan schedule"
```

**Note on Bank Charges:** Bank charges from Note 17 = actual bank service charges.
These are ADDED to the interest from Note 16 to get total Row 85.
For FY2025, Bank Charges (Note 17) = ₹1,22,475 → Row 85

**Verify:** Is the interest split across TL/WC/Bank only possible from the loan schedule?
☐ Yes, always needs manual split   ☐ No, sometimes stated separately: _______

---

## RULE SRP-016 — TDS Receivable + TCS Receivable → Advance Income Tax

**Applies to:** All industries

**Pattern it catches:**
- `TDS Receivable`
- `TCS Receivable`
- `TDS Refundable`
- `TDS Credit`
- `Income Tax Refund Receivable`
- Located in Balance Sheet, current assets section (Other Assets / Other Current Assets)

**Classification:** Advance Income Tax → Row 221

**Why this rule exists:**
TDS (Tax Deducted at Source) and TCS (Tax Collected at Source) are advance tax payments
made by third parties on behalf of the company. They are tax receivables — the company
has pre-paid income tax and can offset it against final tax liability.

The CA groups TDS/TCS receivables with Advance Income Tax (Row 221). The AI might put these in:
- Advances recoverable in cash or kind (Row 219) — wrong category
- Other Advances / current asset (Row 223) — close but wrong
- DOUBT (AI uncertain if TDS = advance tax)

**Real example from SR Papers:**
```
Balance Sheet (FY2023):
Source text:   "TDS Receivable" = ₹2,36,473.57
               "TCS Receivable" = ₹30,227.66
Combined:      ₹2,66,701.23 → Advance Income Tax  [Row 221]
Old result:    Other Advances (Row 223) or DOUBT
New result:    Advance Income Tax  ✓
```

**Verify:** Do you agree TDS/TCS receivables = Advance Income Tax (Row 221)?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE SRP-017 — Deferred Tax Liability P&L Entry

**Applies to:** All companies with deferred tax

**Pattern it catches:**
- `Deferred Tax` (in P&L)
- `Deferred Tax Liability`
- `Deferred Tax Asset` (in P&L)
- `Deferred Tax (Net)` in P&L section
- Note: Must be located in P&L below the line (taxation section), not Balance Sheet

**Classification:**
- If it INCREASES the company's tax burden → Deferred Tax Liability (P&L) → Row 100
- If it DECREASES the company's tax burden → Deferred Tax Asset (P&L) → Row 101

**Why this rule exists:**
Deferred tax in the P&L is the movement in timing differences between book depreciation
and tax depreciation. The CA has:
- FY2023: (-)₹63,77,066 in Row 100 — a NEGATIVE DTL = DTL reversal (or DTA created)
- FY2024: +₹1,47,07,680 in Row 100 — positive DTL = additional tax expense

The AI might confuse the P&L DTL entry with the Balance Sheet DTL (Row 159) or might
classify it as Income Tax Provision (Row 99) — both are wrong.

**Real example from SR Papers:**
```
P&L Section below Profit Before Tax:
Source text:   "Deferred tax"  (FY2023: -₹63,77,066 / FY2024: +₹1,47,07,680)
Correct field: Deferred Tax Liability (P&L)  [Row 100]
Not to be confused with:
- "Deferred tax Liability (Net)" in Balance Sheet → Row 159
```

**Verify:** Do you agree Deferred Tax in P&L = Row 100?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE SRP-018 — Other Long Term Liabilities → Unsecured Loans Quasi Equity

**Applies to:** Companies with promoter/director/group company loans

**Pattern it catches:**
- `Other Long Term Liabilities` (when amount is significant and consistent)
- `Long-term Liabilities – Others`
- `Loans from Directors`
- `Loans from Promoters`
- `Loans from Related Parties` (in non-current liabilities section)
- `Group Company Loans` (non-current)

**Classification:** Unsecured Loans – Quasi Equity → Row 152

**Why this rule exists:**
SR Papers has ₹1,82,49,886 "Other Long Term Liabilities" for all 3 years (amount unchanged
= long-standing related party loan). The CA treats these as Quasi Equity (Row 152) because:
1. They are from promoters/directors (not banks)
2. They have no fixed repayment schedule
3. They are subordinated to bank debt

Without this rule, the AI might classify these as:
- Working Capital Bank Finance (wrong — not bank loans)
- Other Current Liabilities (wrong — these are non-current)
- Balance Sheet Reserves (wrong — these are liabilities)

**Real example from SR Papers:**
```
Balance Sheet (Non-Current Liabilities):
Source text:   "Other Long Term Liabilities"
Amount:        ₹1,82,49,885.76 (all 3 years — same amount = promoter loan)
Correct field: Unsecured Loans – Quasi Equity  [Row 152]
Old result:    DOUBT or Other non-current assets (WRONG)
New result:    Unsecured Loans – Quasi Equity  ✓
```

**Verify:** Do you agree Other Long-Term Liabilities from promoters = Quasi Equity (Row 152)?
☐ Yes, correct   ☐ No, it should be: _______________________

---

## RULE SRP-019 — Inventory (All Types) as Raw Material for Trading Firms

**Applies to:** Trading and distribution companies (NOT pure manufacturers)

**Pattern it catches:**
- `Inventories` on Balance Sheet — when NO breakdown by type is provided
- `Stock` (general) — balance sheet
- `Closing Stock` (balance sheet item)
- `Stock of Goods` (trading firm)
- `Stocks – Paper` or similar product-specific stock

**Classification:**
- If no WIP/Finished Goods breakdown: All inventory → Raw Material Indigenous (BS) → Row 194
- Stocks-in-process BS (Row 200) = 0
- Finished Goods BS (Row 201) = 0

**Why this rule exists:**
For a paper trading company:
- There is NO manufacturing process, so no WIP exists
- "Finished goods" = their purchased inventory ready for sale
- The CA treats ALL inventory as "Raw Material" on the BS because they are inputs to sales

The AI might try to classify paper stock as "Finished Goods BS" (Row 201) because it's
ready for sale. But for trading companies, the CMA convention is Raw Material Indigenous.

**Real example from SR Papers:**
```
Balance Sheet:
"Inventories"  FY2023: ₹14,77,66,181  FY2024: ₹17,74,97,435  FY2025: ₹20,52,58,955
ALL → Raw Material Indigenous (BS)  [Row 194]
Stocks-in-process → 0  [Row 200]
Finished Goods → 0  [Row 201]
```

**Exception — when this rule would be WRONG:**
If the company is a true manufacturer with separate raw materials, WIP, and finished goods —
in that case break into all three rows. This rule only applies when inventory is undifferentiated
trading stock.

**Verify:** Do you agree ALL inventory for trading firms = Raw Material Indigenous (Row 194)?
☐ Yes, correct   ☐ No, we have WIP/FG: _______________________

---

## RULE SRP-020 — Donations → Others (Non-Operating Expenses)

**Applies to:** All industries

**Pattern it catches:**
- `Donation`
- `Donations`
- `CSR Expenses` (small amounts)
- `Charity`

**Classification:** Others (Non-Operating Expenses) → Row 93

**Why this rule exists:**
Donations are non-recurring non-business expenses. The CA correctly places them in
non-operating expenses (Row 93), not in administrative expenses (Row 71).

The AI may put donations in:
- Others (Admin) Row 71 (wrong — these are not admin costs)
- Miscellaneous Expenses Row 75 (wrong)

**Real example from SR Papers:**
```
Source text:   "Donation"
Amount:        FY2023: ₹90,640 | FY2024: ₹0 | FY2025: ₹3,001
Correct field: Others (Non-Operating Expenses)  [Row 93]
Old result:    Others (Admin) (Row 71)
New result:    Others (Non-Op Expenses)  ✓
```

**Verify:** Do you agree donations = Others (Non-Operating Expenses) Row 93?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE SRP-021 — Vehicle Haulting Charges (Income) → Others (Non-Operating Income)

**Applies to:** Companies that hire out vehicles

**Pattern it catches:**
- `Vehicle Haulting Charges` (income)
- `Vehicle Hire Charges` (income)
- `Transport Income`
- `Haulage Income`
- Located in INCOME section (Other Income)

**Classification:** Others (Non-Operating Income) → Row 34

**Why this rule exists:**
SR Papers occasionally earns income by hiring out company vehicles to third parties.
"Vehicle Haulting Charges" is income received for this — a non-core, non-operating item.

The AI may confuse this with:
- Freight and Transportation Charges (expense Row 47) — completely wrong direction
- Domestic Sales Row 22 — wrong (it's not paper sales)
- DOUBT (AI unfamiliar with this income type)

**Real example from SR Papers:**
```
Source text:   "Vehicle Haulting Charges"
Section:       Note 13: Other Income
Amount:        FY2023: ₹10,000 | FY2024: ₹0 | FY2025: ₹0
Correct field: Others (Non-Operating Income)  [Row 34]
Old result:    Freight expense (Row 47) — WRONG direction!
New result:    Others (Non-Operating Income)  ✓
```

**Verify:** Do you agree vehicle hire income = Others (Non-Operating Income) Row 34?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE SRP-022 — Currency Exchange Profit/Loss → Rows 32/91

**Applies to:** All industries with import/export transactions

**Pattern it catches:**
- `Currency Exchange Profit` (income) → Row 32
- `Currency Fluctuation Profit` (income) → Row 32
- `Exchange Profit` (income) → Row 32
- `Currency Exchange Loss` (expense) → Row 91
- `Currency Fluctuation Loss` (expense) → Row 91
- `Forex Loss`/`Forex Gain`
- Note: Must be in income/expense section respectively

**Classification:**
- Income side: Gain on Exchange Fluctuations → Row 32
- Expense side: Loss on Exchange Fluctuations → Row 91

**Why this rule exists:**
Exchange fluctuation on import/export transactions creates either a gain (income) or loss
(expense). The CA splits these correctly into the non-operating income/expense rows.

The AI, without context, may confuse:
- "Currency Exchange Profit" → Domestic Sales (Row 22) — wrong
- "Currency Exchange Loss" → Bank Charges (Row 85) — wrong
- Both items together → Others (Admin) — wrong

**Real example from SR Papers:**
```
Source text:   "Currency Exchange Profit"
Section:       Note 13: Other Income
Amount:        FY2023: ₹79,608 | FY2024: ₹0
Correct field: Gain on Exchange Fluctuations  [Row 32]

Source text:   "Currency Exchange Loss"
Section:       Note 17: Other Expenses
Amount:        FY2023: ₹24,843 | FY2024: ₹1,50,280
Correct field: Loss on Exchange Fluctuations  [Row 91]
```

**Verify:** Do you agree currency exchange profit/loss = Rows 32/91?
☐ Yes, correct   ☐ No, exception: _______________________

---

## PRIORITY RULES (implement first)

| Priority | Rule | Impact | Reason |
|----------|------|--------|--------|
| 🔴 CRITICAL | SRP-001 — Customs Duty → Imported RM | High | Large amount, completely wrong without rule |
| 🔴 CRITICAL | SRP-002 — Hamali → Freight | High | Very common across India; AI has zero knowledge |
| 🔴 CRITICAL | SRP-015 — Interest Split | High | Always needs manual split; must go to doubt |
| 🟠 HIGH | SRP-004 — Delivery Charges → Row 64 | High | ₹68–98 lakhs misclassified without rule |
| 🟠 HIGH | SRP-005 — Discount Received → Non-op Income | High | Easy to confuse with Discount Allowed (expense) |
| 🟡 MEDIUM | SRP-007 — Tea & Food → Staff Expenses | Medium | Consistently present across companies |
| 🟡 MEDIUM | SRP-006 — Admin Exp for PF → Staff Exp | Medium | Very common in all Indian companies |
| 🟡 MEDIUM | SRP-019 — All Inventory → Raw Material (trading) | Medium | Prevents WIP/FG misclassification |
| 🟢 LOW | SRP-009 — Royalty → Mfg Others | Low | Only paper/IP companies |
| 🟢 LOW | SRP-010 — Stereo Charges → Advts | Low | Paper/printing industry only |
| 🟢 LOW | SRP-014 — FSC License → Admin | Low | Paper industry only |

---

## MANUFACTURING-SPECIFIC OBSERVATIONS

### SR Papers is NOT a Classic Manufacturer

Despite being labelled "manufacturing" by the user, SR Papers is a **paper distributor**.
Key evidence:
- No WIP inventory (Row 200 = 0 all years)
- No Finished Goods (Row 201 = 0 all years)
- No factory wages (no separate wage/salary for factory workers)
- No raw material consumption schedule (just "Cost of Material Consumed" = purchases)
- Revenue = "Paper & Paper Products" (sale of products, not manufactured output)

### CMA Treatment for Trading-as-Manufacturing

The CA uses the CMA "manufacturing" sections as follows for trading companies:
- Row 42 (Raw Materials Consumed Indigenous) = Total purchase cost of goods
- Row 41 (Raw Materials Consumed Imported) = Customs duty on imports
- Row 45 (Wages) = All employee salary + PF + welfare (no factory/office distinction)
- Row 49 (Others Manufacturing) = Warehouse/godown operating expenses
- Row 64 (Other Manufacturing Exp CMA) = Distribution overhead (delivery, import logistics)

### Rules from classification_rules_v1.md that NOW APPLY to Manufacturing:

These rules were written for Mehta Computers (trading firm) but also apply to SR Papers:
- Rule C-001 (Motor Vehicles → Gross Block): ✓ SR Papers has many vehicles
- Rule C-004 (Security Deposits): ✓ SR Papers has large security deposits (₹1.7–3.9 Cr)
- Rule B-002 (ALL CAPS vendor names): ✓ May appear in trade payables

### Rules from classification_rules_v1.md that do NOT apply to SR Papers:

- Rule A-001/A-002 (GST-coded purchases → Raw Materials): Not needed — SR Papers
  records purchases as "Cost of Material Consumed" (Note 14 line), not "Purchase @ 18%"
- Rule B-003 (Unqualified "Interest Paid" → WC loans): Not needed — Finance Cost is
  always split manually from loan schedule

---

## ITEMS NEEDING CA VERIFICATION (Not Auto-Classifiable)

| Item | Amount | Doubt Reason | Ask CA |
|------|--------|--------------|--------|
| Processing Fee | ₹15,01,593 (FY2023) | Is this bank LC processing or job work? | Row 71 (admin) or Row 46 (job work)? |
| Manpower Charges | ₹68,310 (FY2023) to ₹12,00,169 (FY2025) | Contract labor — mfg or admin? | Row 49 (mfg) or Row 71 (admin)? |
| Shop Expenses | ₹2,99,738 (FY2023) | Branch shop operating costs | Row 71 (admin) or Row 49 (mfg)? |
| Finance Cost split | ₹2,83,88,411 | Cannot split without loan schedule | Provide TL and WC interest amounts |
| Packing & Forwarding | ₹1,72,133 (FY2023) | Outward packing vs inward packaging? | Row 47 (freight) or Row 71 (admin)? |

---

## DEDUPLICATION NOTES (for merge with BCIPL rules)

When merging with BCIPL classification rules, these SR Papers rules likely apply broadly:

| SR Papers Rule | Expected in BCIPL too? |
|----------------|------------------------|
| SRP-001 Customs Duty | Only if BCIPL imports |
| SRP-002 Hamali Charges | YES — very common India-wide |
| SRP-005 Discount Received | Likely YES — common |
| SRP-006 Admin Exp for PF | YES — common India-wide |
| SRP-007 Tea & Food → Staff | YES — common India-wide |
| SRP-011 Discount Allowed → Advts | YES — common |
| SRP-012 Commission → Advts | YES — common |
| SRP-020 Donations → Non-op | YES — common |
| SRP-022 Currency Exchange | Only if BCIPL has forex |
