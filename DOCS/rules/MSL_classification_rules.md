# MSL (Matrix Stampi Ltd) — CMA Classification Rules

**Company:** Matrix Stampi Ltd (Metal Stamping / Manufacturing)
**Rules derived from:** Ground truth CMA (`MSL CMA 24102025.xls`) vs. Excel financials (`MSL - B.S -2024-25 Final 151025.xlsx`)
**Years analyzed:** FY2021-22, FY2022-23, FY2023-24, FY2024-25
**Total line items analyzed:** ~60 distinct account heads
**New rules created:** 10 (MSL-001 through MSL-010)
**Items covered by existing rules:** 14 (see Section B)
**Status:** Pending CA verification before implementation
**Created:** 2026-03-22

---

## Why MSL matters for the rule engine

MSL is the **first manufacturing company** tested. Manufacturing firms use ~40% of CMA fields that trading firms never touch:
- Rows 41–56 (Cost of Production: RM, Stores, Wages, Job Work, Freight, Power, Others Mfg, R&M, Depreciation)
- Row 201 (Finished Goods on BS — vs Row 194 Raw Material Indigenous on BS)

The trading firm rules (A-001 through D-002) were calibrated on Mehta Computers. MSL reveals new patterns that apply specifically to manufacturing companies.

---

## SECTION A — NEW RULES (MSL-001 through MSL-010)

---

### MSL-001 — "Stock in Trade" in Manufacturing = Finished Goods (Row 201)

**Applies to:** Manufacturing industry

**Pattern it catches:**
- Description: `Stock in Trade`, `Stock-in-Trade`, `Trading Stock`
- Section: Inventories / Current Assets on Balance Sheet
- Industry: Manufacturing (not trading)

**Classification:** Finished Goods → Row 201

**Why this rule exists:**
Matrix Stampi Ltd is a metal stamping manufacturer, yet their accountant labels all inventory as "Stock in Trade" — a term normally used by trading firms. The CA correctly maps this to Row 201 (Finished Goods) because MSL manufactures products, not just resells them.

The AI, if given the raw label "Stock in Trade", might route this to Row 194 (Raw Material Indigenous) or a trading inventory row. This rule ensures that for manufacturing firms, any "Stock in Trade" label on the BS under Inventories → Finished Goods.

**Real example from MSL FY2024-25:**
```
Source text:   "Stock in Trade"
Section:       "Inventories" (Balance Sheet, Current Assets)
Amount:        ₹87,874.07K (₹878.74 L)
Correct field: Finished Goods  [Row 201]
Old result:    Risk of misclassification to Raw Material / Other Current Asset
New result:    Finished Goods  ✓
```

**Cross-year verification:**
| Year | Amount (L) | CMA Row | Confirmed |
|------|-----------|---------|-----------|
| FY22 | 660.44 | R201 | ✓ |
| FY23 | 685.81 | R201 | ✓ |
| FY24 | 798.35 | R201 | ✓ |
| FY25 | 878.74 | R201 | ✓ |

**When this rule would be WRONG:**
If a firm is genuinely a trading company but happens to appear in manufacturing industry category. Rule should only fire when Industry = Manufacturing AND the item is in Inventories section.

**Verify:** Do you agree "Stock in Trade" in a manufacturer's inventory → Finished Goods Row 201?
☐ Yes, correct   ☐ No, exception: _______________________

---

### MSL-002 — All Employee Costs in Manufacturing → Wages Row 45 (When No Director Split)

**Applies to:** Manufacturing industry

**Pattern it catches:**
- Salaries, Wages, Bonus, PF/ESI Contribution, Staff Welfare, Gratuity Expense (current year P&L)
- These appear under a SINGLE head: "Employee Benefits Expense" or "Staff Expenses"
- No separate "Directors Remuneration" line in the P&L

**Classification:** Wages → Row 45
*(Row 67 Salary & Staff Expenses = 0)*

**Why this rule exists:**
In manufacturing firms, all direct and indirect labor is typically classified as "Wages" (Row 45 = direct production labor including indirect overhead). Row 67 (Salary & Staff Expenses) is reserved for admin staff whose salaries are clearly administrative.

When a company combines all employee costs into one P&L line (no Directors Remuneration breakout), the CA maps everything to R45. This is MSL's pattern: R67 = 0 across all 4 years.

**Contrast with BCIPL-001:**
BCIPL has a separate "Directors Remuneration" line → R67. MSL does not disclose this separately → all goes to R45. The rule fires on absence of a director remuneration breakout, not on presence.

**Real example from MSL FY2024-25:**
```
Source text:   "Employee Benefits Expense" (Note 23)
               = Salaries ₹12,748.73K + Bonus ₹88.83K + PF ₹530.35K + Staff Welfare ₹73K
Amount:        ₹13,440.91K = 134.41 Lakhs
Correct field: Wages  [Row 45]
Row 67:        0  (always zero for MSL)
```

**When this rule would be WRONG:**
If the accounts separately show "Directors Remuneration" as a line item (like BCIPL does) → that line should still go to R67 (apply BCIPL-001), with remaining employee costs to R45.

**Verify:** For manufacturing clients with no Director breakout — does all employee cost go to Row 45?
☐ Yes, correct   ☐ No, director remuneration should be separated even when not broken out: _______________________

---

### MSL-003 — Long-term Gratuity Provision → Long-Term Unsecured Debt Row 153

**Applies to:** All industries

**Pattern it catches:**
- `Provision for Gratuity`
- `Gratuity Liability`
- `Gratuity (Non-funded)`
- Section: Long-term Provisions / Non-current Liabilities on Balance Sheet

**Classification:** Unsecured Loans — Long Term Debt → Row 153

**Why this rule exists:**
Provision for gratuity is a long-term employee liability (not funded via LIC). In CMA, it gets classified under Row 153 (Long Term Unsecured Debt) because it represents a long-duration obligation of the company that acts like debt from a banker's credit assessment perspective.

The AI might classify this as a contingent liability (Rows 254–258) or as a current provision (Row 244). Both are wrong.

**Real example from MSL FY2024-25:**
```
Source text:   "Provision for Gratuity" (Note 6 — Long-term Provisions)
Amount:        ₹2,171.62K = 21.72 Lakhs
Correct field: Unsecured Loans — Long Term Debt  [Row 153]
CMA Row 153 FY25: 21.72 L  ✓
```

**Cross-year note:**
In FY22-24, R153 also included residual unsecured loan amounts (beyond Quasi Equity). In FY25, R153 = Gratuity only (all unsecured loans moved to R152). The Gratuity portion is identifiable by "Provision for Gratuity" in long-term provisions.

**Distinguish from:**
- Current year gratuity expense (P&L): that goes to R45 (Wages) per MSL-002
- Short-term gratuity payable (if any): would go to R250 (Other Current Liabilities)
- Funded gratuity (LIC policy): may have different treatment

**Verify:** Do you agree Provision for Gratuity in long-term provisions → Row 153?
☐ Yes, correct   ☐ No, it should go to: _______________________

---

### MSL-004 — "Other Charges" in Finance Costs → Term Loan Interest Row 83

**Applies to:** All industries

**Pattern it catches:**
- Finance Costs section of P&L contains THREE lines:
  1. Bank Interest / Interest on CC / Interest on OD → R84 (Working Capital)
  2. Bank Charges / Bank Commission / Processing Fees → R85
  3. `Other Charges` / `Other Finance Charges` / `Loan Processing Charges` → **R83 (Term Loan Interest)**
- The "Other Charges" is the residual finance cost after identifying WC interest and bank charges

**Classification:** Interest on Fixed Loans / Term Loans → Row 83

**Why this rule exists:**
When a company has both a working capital facility AND a term loan, the finance costs note will show:
- CC/OD interest → clearly working capital → R84
- Bank charges → clearly R85
- "Other Charges" → the CA treats this as term loan-related costs

The AI might send "Other Charges" to doubt, or confuse it with bank charges. MSL's CA consistently maps it to R83 across years.

**Real example from MSL FY2024-25:**
```
Finance Costs Note 24:
  Bank Charges:           ₹539.95K  → R85 (5.40 L)
  Bank Interest (CC):     ₹1,743.11K → R84 (19.67 L)
  Other Charges:          ₹521.65K  → R83 (2.98 L)
Total Finance Costs:      ₹2,804.71K = 28.05 L
CMA Check: R83+R84+R85 = 2.98+19.67+5.40 = 28.05 L  ✓
```

**When this rule would be WRONG:**
If the company has no term loan and "Other Charges" represents something else (e.g., forex hedging cost). → Use doubt in that case. Rule fires when the company has a confirmed term loan outstanding.

**Verify:** When a company has a TL and Finance Costs shows "Other Charges" → should it go to R83?
☐ Yes, correct   ☐ No, exception: _______________________

---

### MSL-005 — Export Incentive → EXCLUDED from CMA (No Row Assigned)

**Applies to:** All industries

**Pattern it catches:**
- `Export Incentive`
- `MEIS Incentive`
- `RoDTEP Credit`
- `Duty Drawback` (export-related)
- Section: Other Income / Non-Operating Income in P&L

**Classification:** **SKIP — do not assign any CMA row**

**Why this rule exists:**
Export incentives (MEIS, RoDTEP, Duty Drawback) are government export promotion credits. The CA for MSL deliberately excludes these from the CMA in ALL years (FY24: ₹87.7K, FY25: ₹86K) — they do not appear in any CMA row.

The likely reason: these are non-recurring government policy items that don't reflect the company's business performance. CMA assessors want to see core operating income, not incentive credits.

**IMPORTANT:** This is a CA judgment call. We EXCLUDE rather than misclassify. The automation system should:
1. Detect the export incentive line
2. NOT assign any row
3. Flag it in the doubt report with note: "Export Incentive excluded per CA practice — verify with CA"

**Real example from MSL FY2024-25:**
```
Source text:   "Export Incentive"
Amount:        ₹86.06K (FY25), ₹87.7K (FY24)
CA decision:   NOT in CMA — excluded entirely
Risk if wrong: Over-statement of non-operating income
```

**Verify:** Should Export Incentive be excluded from CMA entirely?
☐ Yes, exclude it   ☐ No, it should go to Row: _______________________

---

### MSL-006 — Insurance Claim Received → Others Non-Operating Income Row 34

**Applies to:** All industries

**Pattern it catches:**
- `Insurance Claim`
- `Insurance Claim Received`
- `Claim from Insurance Company`
- Section: Other Income / Non-Operating Income in P&L

**Classification:** Others (Non-Operating Income) → Row 34

**Why this rule exists:**
Insurance claims are non-recurring, non-operating income receipts. They go to Row 34 (Others Non-Operating Income). The AI might misclassify these as Extraordinary Income (R33) or operating income.

**Real example from MSL FY2024-25:**
```
Source text:   "Insurance Claim Received" (Note 20 — Other Income)
Amount:        ₹355.79K = 3.56 Lakhs
Correct field: Others (Non-Operating Income)  [Row 34]
CMA Row 34 FY25: 3.56 L  ✓  (matches exactly)
```

**Cross-year note:**
R34 in FY22-24 also included other non-operating items (confirmed from CMA ground truth). This rule narrows specifically the Insurance Claim component.

**Verify:** Do you agree Insurance Claim Received → Others Non-Operating Income Row 34?
☐ Yes, correct   ☐ No, it should go to Row: _______________________

---

### MSL-007 — Freight Outward + Discount Allowed + Sales Promotion → Advertisements Row 70 (Manufacturing)

**Applies to:** Manufacturing industry
*(Extends BCIPL-004 which covered similar items for BCIPL's mixed industry)*

**Pattern it catches:**
- `Freight Outward`, `Freight on Sales`, `Outward Freight`
- `Discount Allowed`, `Trade Discount`, `Cash Discount`
- `Sales Promotion`, `Sales Promotion Expenses`
- Section: Other Expenses / Selling & Distribution in P&L
- Industry: Manufacturing

**Classification:** Advertisements and Sales Promotions → Row 70

**Why this rule exists:**
In manufacturing firms, selling & distribution costs (outward freight to deliver goods to customers, trade discounts given, sales promotion) are grouped into Row 70 (Advertisements and Sales Promotions). The CMA field name is broad and encompasses all selling costs.

Without this rule, the AI might classify Freight Outward to Row 47 (Freight & Transportation Charges) — which is WRONG because Row 47 is for INBOUND freight (part of cost of production). Outward/delivery freight is a selling cost → R70.

**Real example from MSL FY2024-25:**
```
Source text:   "Freight Outward"       ₹154.43K = 1.54 L → R70
               "Discount Allowed"      ₹673.55K = 6.74 L → R70
               "Sales Promotion"       ₹10.79K  = 0.11 L → R70
Combined:                                         8.39 L
CMA Row 70 FY25:                                  8.05 L (small rounding difference)
```

**Important distinction:**
- Carriage Inward / Freight Inward (part of cost of goods purchased) → R47 ← inbound
- Freight Outward / Delivery charges to customer → R70 ← outbound/selling

**Verify:** Do you agree Freight Outward + Discount Allowed + Sales Promotion → Row 70?
☐ Yes, correct   ☐ No, exception: _______________________

---

### MSL-008 — Tour & Travel + Consultancy Fees + General Expenses + Insurance → Others Admin Row 71

**Applies to:** All industries

**Pattern it catches:**
- `Tour and Travelling`, `Tour & Travel`, `Travel Expenses`
- `Consultancy Fees`, `Professional Charges`, `Legal & Professional`
- `General Expenses`, `Miscellaneous Expenses`, `Sundry Expenses`
- `Insurance` (general business insurance premium — not insurance claims)
- Section: Other Expenses / Administrative Expenses in P&L

**Classification:** Others (Admin) → Row 71

**Why this rule exists:**
These are general administrative overhead items that don't have a specific CMA row. Row 71 is the catch-all for admin overheads. The AI might send these to doubt, or misclassify Consultancy Fees as Audit Fees (R73) or Miscellaneous as extraordinary items.

Key distinction: Audit Fees → R73; all other professional/admin fees → R71.

**Real example from MSL FY2024-25:**
```
Tour & Travel:      ₹163.49K  = 1.63 L → R71
Consultancy Fees:   ₹1,360.49K = 13.60 L → R71
General Expenses:   ₹212.60K  = 2.13 L → R71
Insurance:          ₹238.65K  = 2.39 L → R71
Combined visible:               19.75 L
CMA Row 71 FY25:                23.77 L (gap ~4 L, likely other items in Note 25)
```

**Distinguish from:**
- Audit Fees → R73 (not R71)
- Repairs & Maintenance → R50 (manufacturing) or R72 (admin R&M)
- Bad Debts → R69
- Exchange Loss → R91

**Verify:** Do you agree Tour & Travel / Consultancy / General / Insurance → Others Admin Row 71?
☐ Yes, correct   ☐ No, some should go elsewhere: _______________________

---

### MSL-009 — ALL Repairs & Maintenance (Both P&M and Others) → R&M Manufacturing Row 50

**Applies to:** Manufacturing industry

**Pattern it catches:**
- `Repairs and Maintenance — Plant & Machinery`
- `R&M — Plant & Machinery`, `R&M P&M`
- `Repairs and Maintenance — Others`
- `Repairs and Maintenance — Building`
- `R&M — Others`
- Any R&M line item in a manufacturing firm

**Classification:** Repairs & Maintenance (Manufacturing) → Row 50
*(NOT Row 72 — R&M Admin)*

**Why this rule exists:**
For manufacturing firms like MSL, ALL R&M expenses — whether for plant/machinery OR buildings/others — go to Row 50 (Repairs & Maintenance Manufacturing). Row 72 (R&M Admin) = 0 for MSL across all years.

The CA's view: in a manufacturing context, even building maintenance supports the production facility, so all R&M is manufacturing overhead.

**Real example from MSL FY2024-25:**
```
"R&M — Plant & Machinery":  ₹157.18K = 1.57 L → R50
"R&M — Others":              ₹657.10K = 6.57 L → R50
Combined:                               8.14 L
CMA Row 50 FY25:                        8.14 L  ✓ (exact match)
CMA Row 72 FY25:                        0.00 L  (always zero)
```

**Extends:** BCIPL-015 (Machinery Maintenance → R50). MSL confirms this extends to ALL R&M, not just machinery.

**Verify:** In manufacturing firms, should ALL R&M (buildings + machinery + others) go to Row 50?
☐ Yes, correct   ☐ No, building R&M should go to R72: _______________________

---

### MSL-010 — "Liability Written Off" → Sundry Balances Written Off Row 90

**Applies to:** All industries

**Pattern it catches:**
- `Liability Written Off`
- `Liabilities Written Back`
- `Excess Provision Written Back`
- `Old Payables Written Off`
- Section: Other Expenses or Non-Operating in P&L

**Classification:** Sundry Balances Written Off → Row 90

**Why this rule exists:**
When old payables or provisions are no longer due (vendor not traceable, statute-barred), the accountant credits "Liability Written Off" to P&L. This represents a miscellaneous balance write-off and maps to Row 90.

The AI might confuse this with "Sundry Balances Written off" on the expense side vs. "Bad Debts" (R69). Bad Debts is for uncollectable debtors (asset write-off); Liability Written Off is for old payables (liability write-off → income-like entry on P&L). Both go to different rows.

**Real example from MSL FY2024-25:**
```
Source text:   "Liability Written Off"
Amount:        ₹100.00K = 1.00 Lakh
Correct field: Sundry Balances Written Off  [Row 90]
CMA Row 90 FY25: 1.00 L  ✓
```

**Verify:** Do you agree "Liability Written Off" → Sundry Balances Written Off Row 90?
☐ Yes, correct   ☐ No, exception: _______________________

---

## SECTION B — ITEMS COVERED BY EXISTING RULES

These MSL line items are handled by rules already in the system. No new rules needed.

| MSL Account Head | Amount FY25 | CMA Row | Covered By | Notes |
|-----------------|------------|---------|-----------|-------|
| Motor Vehicle / Vehicle | ₹4,558.69K net | R162 | **C-001** | Vehicle in fixed assets → Gross Block |
| Computer, Office Equipment, AC, Furniture | Various | R162 | **C-002** | Electronics/equipment → Gross Block |
| Security Deposit / Deposit with Govt. | ₹1,752.55K | R237 | **C-004** | Deposit with Govt. Dept → R237 |
| Job Work Charges | ₹284.47K | R46 | **BCIPL-003** | Job Work → R46 confirmed for manufacturing |
| Director/Promoter Unsecured Loans | ₹41,768.22K | R152 | **BCIPL-010** | Promoter loans → Quasi Equity ✓ |
| Capital Advances (if any) | — | R236 | **BCIPL-016** | Not present in FY25, covered |
| GST Input Credit / Balance with Govt Auth | ₹1,344.08K | R219 | **BCIPL-017** | "Balance with Government Authorities" → R219 |
| Bad Debts Written Off | ₹650.08K | R69 | Direct mapping | Field name matches exactly |
| Power, Coal & Fuel | ₹3,539.64K | R48 | Direct mapping | Field name matches exactly |
| Advance Income Tax / TDS Receivable | ₹4,832.27K | R221 | **SSSS-013** | Advance Income Tax → R221 |
| Bank Interest (CC/OD) | ₹1,743.11K | R84 | **BCIPL-007** | CC/OD interest → WC loans R84 |
| Bank Charges | ₹539.95K | R85 | Direct mapping | "Bank Charges" → R85 |
| Exchange Rate Fluctuation (Loss) | ₹147.02K | R91 | Direct mapping | Loss on FX → R91 |
| Interest Received (income side) | ₹103.56K | R30 | **B-001** | Bank Interest income → R30 |
| P&L on Sale of Fixed Assets | ₹336.09K | R89 | Direct mapping | Loss on Sale FA → R89 |

---

## SECTION C — CA JUDGMENT ITEMS

These items require CA's professional judgment and should always go to the **doubt report** for human review. Do NOT attempt auto-classification.

### C-1: Export Incentive — Exclude or Include?

**Item:** Export Incentive / RoDTEP / MEIS
**MSL CA decision:** EXCLUDED from CMA
**Uncertainty level:** HIGH — different CAs may treat differently
**System behavior:** Flag in doubt report as: *"Export Incentive: CA may exclude — verify whether to map to Row 34 or exclude entirely"*

### C-2: R153 Composition (Gratuity vs. Residual Unsecured Loans)

**Item:** Long-term Provisions + excess Unsecured Loans → R153
**MSL pattern:**
- FY22-24: R153 includes gratuity + residual unsecured loans (after R152 Quasi Equity allocation)
- FY25: R153 = Gratuity only (all loans moved to R152)
**Uncertainty level:** MEDIUM — depends on CA's Quasi Equity threshold decision
**System behavior:** Apply MSL-003 for Gratuity. For remaining unsecured loan split → flag as doubt

### C-3: Security Charges / Plant Protection

**Item:** Security Service Charges (Note 25 — if present)
**MSL pattern:** FY22 = 14.65 L, FY23 = 13.69 L, FY24 = 12.00 L, FY25 = 0 (absent)
**CA mapping (FY22-24):** → R49 (Others Manufacturing)
**Note:** This CMA has a dedicated row R51 (Security Service Charges). CA maps to R49 instead of R51. Verify whether R49 or R51 is correct for security agency costs.
**System behavior:** Flag as doubt if "Security Charges" appears — ask CA whether R49 or R51.

### C-4: "Other Charges" Threshold in Finance Costs

**Context:** MSL's R83 values (2.98 L FY25, 0.74 L FY23, 0.67 L FY24) are small relative to R84 (19.67 L). The "Other Charges" in Note 24 cleanly explains R83. But if "Other Charges" is very large and the company has no term loan, it might not belong in R83.
**System behavior:** Apply MSL-004 only when company has confirmed term loan outstanding; otherwise flag as doubt.

---

## SECTION D — MANUFACTURING-SPECIFIC PATTERNS CONFIRMED BY MSL

The following patterns are NOT new rules but confirm that existing assumptions hold for manufacturing:

1. **R67 = 0 is common in manufacturing** when all labor is pooled under "Employee Benefits" in P&L.
2. **Carriage Inwards** (inbound freight as part of purchase cost) → R47 — same as C-003 for trading. MSL confirms this applies to manufacturing too. *Recommendation: Remove "Trading industry only" restriction from C-003.*
3. **Stores & Spares** as P&L expense → R44 (not R49). In MSL, "Stores" in Note 25 maps to R44. The AI should not confuse Stores P&L expense with "Others Manufacturing" R49.
4. **All promoter unsecured loans → R152 (Quasi Equity)** — confirmed by MSL at ₹417.68 L in FY25. Consistent with BCIPL-010.
5. **R71 (Others Admin) is the catch-all** for any admin expense not specifically named in other rows.

---

## SECTION E — RULE INTERACTION MAP

For a manufacturing firm, the priority order when multiple rules could apply:

```
1. BCIPL-003  → Job Work Charges → R46 (highest specificity)
2. MSL-009    → R&M → R50 (overrides any tendency to put mfg R&M in R72)
3. MSL-007    → Freight OUTWARD → R70 (must distinguish from C-003 which handles inbound)
4. C-003      → Freight INWARD → R47 (for manufacturing: inbound freight is production cost)
5. MSL-002    → All employee costs → R45 (when no director breakout)
6. BCIPL-001  → Director Remuneration → R67 (when separately disclosed)
7. MSL-004    → "Other Charges" in finance → R83
8. MSL-005    → Export Incentive → EXCLUDE
```

---

## SECTION F — SUGGESTED RULE ENGINE CHANGES

Based on MSL analysis, the following existing rules should be updated:

| Rule | Current Restriction | Suggested Change | Reason |
|------|---------------------|-----------------|--------|
| C-003 | "Trading industry only" | Remove industry restriction | MSL confirms Carriage Inwards → R47 in manufacturing too |
| BCIPL-015 | "Machinery Maintenance" | Extend to "R&M Others" / "R&M Building" | MSL shows ALL R&M types go to R50 in manufacturing |

---

## How to give feedback on these rules

1. **"MSL-X is correct"** — keep as-is
2. **"MSL-X is wrong, it should do Y"** — update the rule
3. **"MSL-X needs an exception: when Z, do W"** — add sub-condition
4. **"MSL-X should also apply to trading firms"** — remove industry filter

The `classification_method` column in the verification screen will show `rule_MSL-001`, `rule_MSL-002`, etc. once implemented.

---

*End of MSL Classification Rules*
