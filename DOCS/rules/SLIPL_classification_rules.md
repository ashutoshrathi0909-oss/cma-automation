# SLIPL Classification Rules
**Company:** Suolificio Linea Italia (India) Private Limited
**Industry:** Footwear / Shoe Sole Manufacturing (Pondicherry + Agra)
**Financial Years:** FY2021-22 to FY2024-25
**Rule IDs:** SLI-001 to SLI-012
**Ground truth:** `SLI CMA 31102025.xls` → Sheet "INPUT In Lakhs" (CA-prepared, verified)
**Status:** Awaiting CA verification before code implementation

---

## Coverage Summary

| Coverage type | Count | Notes |
|---|---|---|
| **New rules** (SLI-001 to SLI-012) | 12 | Genuine gaps not covered by existing rules |
| **Conflict flags** | 3 | SLIPL CA mapping differs from an existing rule |
| **Existing rules that apply** (no new rule needed) | ~8 | Listed in the "Already Covered" section at end |

---

## CONFLICT FLAGS — Read These First

Three SLIPL classifications conflict with existing rules. The system will need CA guidance on which rule to use when it encounters ambiguous cases:

| Conflict | Existing Rule | SLIPL CA Treatment | Recommended Resolution |
|---|---|---|---|
| **KMP/Director Remuneration** | BCIPL-001: → Row 67 (Salary) | → Row 45 (Wages) | Industry-dependent: Manufacturing → Row 45; Trading/Services → Row 67 |
| **Packing Materials as manufacturing cost** | BCIPL-004: → Row 70 (Advertisements) | → Row 49 (Others Mfg) | Context-dependent: Production packing → Row 49; Sales/marketing packing → Row 70 |
| **Security Deposits (private landlords)** | V1 C-004: → Row 237 (Govt deposits) | → Row 238 (Other non-current) | Split needed: Govt entity deposits → 237; Private landlord/vendor deposits → 238 |

---

## New Rules

---

### SLI-001 — Duty Drawback / Export Incentives → Included in Export Sales (Row 23)

**Pattern it catches:**
- `Duty Drawback`
- `IGST Refund on Exports`
- `Export Incentive`
- `Drawback Received`

**Classification:** Export Sales → **Row 23** (added to export revenue, NOT separate row)

**Why this rule exists:**
Duty Drawback is a customs refund received by exporters on inputs used in exported goods. It is an export incentive — not other income. SLIPL's CA adds Duty Drawback directly to Export Sales (Row 23).

In P&L, it appears under "Other Income." But the CMA treatment is different: it augments export revenue. The AI would naturally put it in Row 34 (Others Non-Operating Income) by following the P&L structure — this rule overrides that.

**Real examples from SLIPL (verified against CMA ground truth):**
```
FY24:
  P&L Export Sales (FOB):     ₹639.53L
  P&L Duty Drawback:          ₹ 27.35L
  CMA Row 23 (Export Sales):  ₹666.88L  ✓ (639.53 + 27.35)

FY25:
  P&L Export Sales (FOB):     ₹194.86L
  P&L Export IGST/Drawback:   ₹ 31.64L
  CMA Row 23 (Export Sales):  ₹226.50L  ✓ (194.86 + 31.64)
```

**When this rule would be WRONG:**
If a firm shows Duty Drawback as part of P&L other income but the CA wants to keep it separate from export sales (some CA firms do this). In that case, Row 34 would be correct.

**Verify:** Does your firm always add Duty Drawback to Export Sales (Row 23)?
☐ Yes, add to Row 23   ☐ No, keep in Other Income (Row 34)

---

### SLI-002 — Factory / Manufacturing Rent → Row 49 (Others Manufacturing)

**Pattern it catches:**
- `Factory Rent`, `Plant Rent`, `Production Premises Rent`
- `Rent` where the party is a known factory landlord (related party context)
- `Lease Rent` + manufacturing premises context

**Classification:** Others (Manufacturing) → **Row 49**

**Why this rule exists:**
In manufacturing firms, rent for the factory/production facility is a manufacturing overhead, not an administration expense. SLIPL pays factory rent to Chemcrown Exports Pvt Ltd for the Pondicherry factory — this goes to Row 49.

Generic unqualified "Rent" (office, godown) goes to Row 68 (Rent Rates Taxes). This rule fires only when the rent is clearly for a manufacturing/production facility.

**Real example from SLIPL FY24:**
```
Source text:   "Rent" (paid to Chemcrown Exports — factory landlord)
Amount:        ₹38.42L
Correct field: Others (Manufacturing) [Row 49]
Old result:    Rent, Rates and Taxes [Row 68] (WRONG for factory rent)
New result:    Others (Manufacturing) [Row 49]  ✓

Verification: Row 49 FY24 total = 72.04 (packing) + 4.53 (moulds) + 9.96 (royalty) + 38.42 (rent) = 124.95 ✓
```

**When this rule would be WRONG:**
If the "Rent" is for an office or godown not connected to production — use Row 68 instead.

**Verify:** Should factory rent go to Row 49 (Manufacturing)?
☐ Yes, factory rent → Row 49   ☐ No, all rent → Row 68

---

### SLI-003 — Manufacturing Royalty / Technical Know-how Fees → Row 49 (Others Manufacturing)

**Pattern it catches:**
- `Royalty`
- `Mould Usage Charges`
- `Technical Know-how Fees`
- `Design Fees` (for manufacturing designs)
- `Technology Transfer Fee`

**Classification:** Others (Manufacturing) → **Row 49**

**Why this rule exists:**
Royalties paid to foreign principals for manufacturing designs, mould usage rights, or technical know-how are manufacturing costs — not admin or selling expenses. SLIPL pays royalty to Italian group companies for shoe mould designs.

**Real example from SLIPL FY24:**
```
Source text:   "Royalty" (paid to Italian parent for shoe sole designs/moulds)
Amount:        ₹9.96L
Correct field: Others (Manufacturing) [Row 49]
Classification method: SLI-003
```

**When this rule would be WRONG:**
Royalty for music, software, or brand licensing in a trading/service firm would likely go to Row 71 (Others Admin) or Row 70.

**Verify:** Does royalty for manufacturing IP go to Row 49?
☐ Yes, manufacturing royalty → Row 49   ☐ No, exception: _______

---

### SLI-004 — Packing Materials as Manufacturing Input → Row 49 (Others Manufacturing)

**Pattern it catches:**
- `Packing Materials` (as raw material / manufacturing input)
- `Packaging Cost` (production packaging)
- `Packing Charges` (when paid as part of production)

**⚠ CONFLICT FLAG — See BCIPL-004**

**Classification:** Others (Manufacturing) → **Row 49**

**Why this rule exists:**
Packing materials used to pack manufactured goods at the factory are a manufacturing overhead. SLIPL includes packing materials in Row 49 — not in Row 70 (Advertisements and Sales Promotions).

This conflicts with BCIPL-004 which classifies "Packing and Forwarding" → Row 70. The key distinction:
- **Production packing** (boxes, tape, wrapping at factory) = **Row 49**
- **Sales/marketing packing** (branded gift boxes, display materials) = **Row 70**
- **Forwarding/freight charges** = Row 47

**Real example from SLIPL FY24:**
```
Source text:   "Packing Materials"
Amount:        ₹72.04L  (largest component of Row 49)
Correct field: Others (Manufacturing) [Row 49]
BCIPL-004 would give: Advertisements and Sales Promotions [Row 70]  ← WRONG for SLIPL
```

**Industry guidance for the classifier:**
- Manufacturing firms: Packing materials → Row 49 (unless clearly sales/marketing)
- Trading firms: Packing and forwarding → Row 70 (per BCIPL-004)
- "Packing and Forwarding" combined line in trading → Row 70

**Verify:** In manufacturing firms, should production packing go to Row 49 instead of Row 70?
☐ Yes, manufacturing packing → Row 49   ☐ No, all packing → Row 70

---

### SLI-005 — All Repairs & Maintenance → Row 72 (R&M Admin) for this company

**Pattern it catches:**
- `Repairs — Buildings`
- `Repairs — Plant & Machinery`
- `Repairs & Maintenance` (any category)
- `Maintenance Charges`

**Classification:** Repairs & Maintenance (Admin) → **Row 72**
*(Row 50 — R&M Manufacturing — is NOT used)*

**Why this rule exists:**
The CMA template has two R&M rows: Row 50 (Manufacturing) and Row 72 (Admin). In SLIPL, the CA consolidates ALL repairs into Row 72 — including plant & machinery repairs that would logically belong to Row 50.

This is a simplification but it's the CA's verified treatment.

**Real example from SLIPL FY24:**
```
Note 25 Breakdown:
  Repairs — Buildings:      ₹8.55L
  Repairs — P&M:            ₹27.30L
  Repairs — Others:         ₹8.14L
  Total:                    ₹43.99L

CMA Row 72 (R&M Admin):     ₹43.99L  ✓
CMA Row 50 (R&M Mfg):      ₹ 0.00L  ← all repairs consolidated to Row 72
```

**Note for the AI classifier:**
For manufacturing firms that explicitly split repairs by location (factory vs office), use:
- Factory / production repairs → Row 50
- Office / admin repairs → Row 72

Only consolidate to Row 72 when the accounts show a single undifferentiated "Repairs" total.

**Verify:** Should all repairs go to Row 72, or should factory repairs go to Row 50?
☐ All to Row 72 (as CA has done)   ☐ Split: factory repairs → Row 50, office → Row 72

---

### SLI-006 — KMP / Director Remuneration → Row 45 (Wages) in Manufacturing

**Pattern it catches:**
- `Director Remuneration`
- `KMP Remuneration`
- `Managerial Remuneration`
- `Key Management Personnel Compensation`
- `MD Salary`

**Classification:** Wages → **Row 45** *(included in total employee cost, NOT in Row 67)*

**⚠ CONFLICT FLAG — See BCIPL-001**

**Why this rule exists:**
BCIPL-001 sends Director Remuneration → Row 67 (Salary and Staff Expenses). SLIPL's CA includes KMP remuneration in Row 45 (Wages) along with all other employee costs. Row 67 is zero across all four years.

In manufacturing, the MD / directors are often directly involved in production management — their remuneration is treated as part of the total employment cost (Row 45). In a trading or service firm, they may be separated as administrative staff (Row 67).

**Real example from SLIPL FY24:**
```
Note 23 Employee Benefits:
  Wages & salaries (workers + staff): large portion
  KMP Remuneration (per Related Party disclosure): ₹41.24L
  Total Employee Costs:              ₹773.22L

CMA Row 45 (Wages):   ₹773.22L  ✓  (KMP included)
CMA Row 67 (Salary):  ₹0.00L
```

**Industry-dependent rule:**
This conflict should be resolved by industry at the classification pipeline level:
- **Manufacturing:** All employee costs including KMP → Row 45
- **Trading/Services:** Directors separately → Row 67; staff → Row 67 or Row 45

**Verify:** In manufacturing firms, should KMP remuneration be included in Wages (Row 45)?
☐ Yes, all employee costs including KMP → Row 45
☐ No, always separate KMP → Row 67

---

### SLI-007 — Security Deposits (Private Landlords/Vendors) → Row 238 (Other Non-Current Assets)

**Pattern it catches:**
- `Security Deposit` (paid to private landlord, supplier, or vendor)
- `Rent Deposit`
- `Lease Security Deposit`
- `Office Deposit`

**Classification:** Other non-current assets → **Row 238**

**⚠ CONFLICT FLAG — See V1 Rule C-004**

**Why this rule exists:**
V1 Rule C-004 sends ALL security deposits → Row 237 (Security deposits with government departments). SLIPL's CA puts all deposits to Row 238 instead. The CMA ground truth shows Row 237 = **zero** across all years.

The distinction:
- **Row 237** = Deposits with **government entities** (electricity board, telephone department, municipal corporation)
- **Row 238** = Other non-current assets, including deposits with **private** landlords, vendors, customers

SLIPL's deposits are primarily the factory rent deposit with Chemcrown Exports (private company) → Row 238 is correct.

**Recommended rule update for V1 C-004:**
Split the existing C-004 rule:
- "Electricity Deposit", "Telephone Deposit", "Municipal Deposit" → Row 237 (government)
- "Security Deposit" (generic), "Rent Deposit" → Row 238 (other non-current)

**Real example from SLIPL:**
```
Source text:   "Security Deposit" (to factory landlord Chemcrown Exports)
Correct field: Other non-current assets [Row 238]
V1 C-004 would give: Security deposits with government departments [Row 237]  ← WRONG
CMA Row 237 across all 4 years: ₹0.00
```

**Verify:** Should rent/factory deposits go to Row 238, not Row 237?
☐ Yes, private deposits → Row 238   ☐ No, all deposits → Row 237

---

### SLI-008 — Manufacturing Moulds / Dies / Tooling → Row 162 (Gross Block)

**Pattern it catches:**
- `Moulds`
- `Dies`
- `Jigs and Fixtures`
- `Mould Set`
- `Manufacturing Tooling`
- `Shoe Moulds`

**Classification:** Gross Block → **Row 162**

**Why this rule exists:**
Moulds used in manufacturing (shoe soles, plastic moulding, metal casting) are specialized capital assets — not consumables. Even though they may wear out within 2-5 years, they meet the capitalization criteria and appear as fixed assets.

Without this rule, the AI might classify moulds as:
- Row 49 (Others Manufacturing) — if treated as consumables
- Row 44 (Stores and Spares) — if confused with spare parts

**Real example from SLIPL FY25:**
```
Source text:   "Moulds" (in Fixed Assets schedule)
Multiple types: Moulds Pondy, Moulds Agra
Correct field: Gross Block [Row 162]  ← capitalized in all years
```

**Note:** Small periodic mould replacement purchases (₹4.53L FY24 in Note 25) may be expensed to Row 49 as repairs. Larger new mould sets are capitalized to Row 162 or held in Row 165 while under fabrication.

**Verify:** Are moulds treated as fixed assets in your CMA practice?
☐ Yes, moulds → Row 162 (Gross Block)   ☐ No, expense as Others Mfg (Row 49)

---

### SLI-009 — Moulds / Capital Items Under Construction → Row 165 (Capital Work in Progress)

**Pattern it catches:**
- `Moulds — WIP`
- `Mould under Fabrication`
- `Dies under Construction`
- `Capital WIP` (any form)
- `Plant — under installation`

**Classification:** Capital Work in Progress → **Row 165**

**Why this rule exists:**
Assets under construction that are not yet ready for use must sit in Capital WIP (Row 165) until completion, then transferred to Gross Block (Row 162). SLIPL has a significant Moulds-WIP balance in FY25.

**Real example from SLIPL FY25:**
```
Trial Balance entry:   "Moulds - WIP"
Amount:                ₹3,17,98,569 = ₹317.99L
Correct field:         Capital Work in Progress [Row 165]
```

**Verify:** Capital WIP items (assets not yet commissioned) → Row 165?
☐ Yes, correct   ☐ No, exception: _______

---

### SLI-010 — Foreign Parent / Related Party Payables (Supply Agreement) → Row 153 (Unsecured Loans — Long Term)

**Pattern it catches:**
- Amounts payable to foreign parent/group companies under supply agreements
- "Amount payable to related party" (non-trade, structured)
- Long-term payables to promoter/parent companies
- `Payable to [Foreign Company Name]` where the relationship is a parent or principal

**Classification:** Unsecured Loans — Long Term Debt → **Row 153**

**Why this rule exists:**
Amounts owed to Italian parent companies (Suolificio Nuova Linea SRL, Suolificio Squadroni SRL) under supply agreements are NOT ordinary trade creditors. They are effectively structured payables — quasi-permanent balances that function as long-term debt. SLIPL's CA classifies them as Row 153 (Unsecured Loans LT), not Row 242 (Sundry Creditors).

Banks view these as soft funding from the parent, not trade credit — they belong on the liabilities side as unsecured debt.

**Distinguishing from normal trade creditors (Row 242):**
- Normal supplier (unrelated): → Row 242
- Related party supplier with long-standing balance under structured agreement: → Row 153
- Short-term related party trade payable (settled in 30-60 days): → Row 242

**Verify:** Should long-standing payables to foreign parent companies under supply agreements go to Row 153?
☐ Yes, treat as unsecured LT debt → Row 153
☐ No, treat as trade creditors → Row 242

---

### SLI-011 — Director / KMP / Promoter Unsecured Loans → Row 152 (Quasi Equity)

**Pattern it catches:**
- `Unsecured Loan from Director`
- `Director Loan`
- `Promoter Loan`
- `KMP Loan`
- `Loan from [Name of Director]`
- `MD Loan`

**Classification:** Unsecured Loans — Quasi Equity → **Row 152**

**Why this rule exists:**
Loans from directors/promoters/KMP are treated as quasi-equity in CMA analysis because:
1. They are subordinated to bank debt
2. They are unlikely to be recalled during financial stress
3. Banks treat them as owner's stake (quasi-equity), not as third-party debt

This is standard CMA practice across all industries.

**Real example from SLIPL FY24:**
```
Source text:   "Unsecured Loan — Manoj Kumar Bhaiya (Director)"
Amount:        ₹594.81L (FY24), ₹613.02L (FY25)
Correct field: Unsecured Loans — Quasi Equity [Row 152]

FY25 breakdown (Trial Balance):
  Manoj Kumar Bhaiya (Loan):        ₹4,30,51,579 = ₹430.52L
  Manoj Kumar Bhaiya (Loan — Agra): ₹1,82,50,000 = ₹182.50L
  Total:                            ₹613.02L → Row 152  ✓
```

**Verify:** Director / promoter unsecured loans → Row 152 (Quasi Equity)?
☐ Yes, correct   ☐ No, classify differently: _______

---

### SLI-012 — Service Charges Received (Processing Income) → Included in Domestic Sales (Row 22)

**Pattern it catches:**
- `Service Charges` (income side — received, not paid)
- `Processing Charges Received`
- `Job Work Revenue` (where SLIPL is the processor, not buyer)
- `Conversion Charges Income`

**Classification:** Domestic Sales → **Row 22** (included, not a separate row)

**Why this rule exists:**
When a manufacturing firm earns income from processing/service work for other parties, this goes to Domestic Sales (Row 22) — not to Other Income (Row 34). SLIPL earns a small amount of service/processing income that the CA includes in Row 22.

Note: This is the INCOME side. "Service Charges Paid" / "Job Work Charges Paid" by SLIPL → Row 46.

**Real example from SLIPL FY24:**
```
Note 19 Revenue breakdown:
  Sale of Products (Domestic): ₹4,321.52L
  Service Charges (received):  ₹     2.37L
  CMA Row 22 total:            ₹4,463.34L  (includes both + other items)
```

**Verify:** Should processing income / service charges received go into Domestic Sales (Row 22)?
☐ Yes, include in Row 22   ☐ No, keep in Other Income (Row 34)

---

## Items Covered by Existing Rules (No New Rule Needed)

| Line Item in SLIPL | Existing Rule | CMA Row |
|---|---|---|
| Motor vehicles (car) | V1 C-001 (Motor Vehicles → Row 162) | 162 |
| Computers, laptops | V1 C-002 (Electronics → Row 162 if ≥ ₹5,000) | 162 |
| Carriage Inward / Outward | V1 C-003 / SSSS-005 (Freight → Row 47) | 47 |
| Bank Interest (Income) | V1 B-001 (Bank Interest income → Row 30) | 30 |
| Bank Charges | V1 B-001 (Bank Charges → Row 85) | 85 |
| Stitching / Job Work paid | BCIPL-003 (Job Work → Row 46) | 46 |
| Audit Fees | Reference mapping (Audit Fees → Row 73) | 73 |
| Depreciation | Reference mapping (Depreciation CMA → Row 63) | 63 |

---

## CA Verification Checklist

Priority items requiring CA confirmation before implementing in code:

| # | Rule | Conflict? | Action needed |
|---|---|---|---|
| 1 | SLI-001: Duty Drawback → Row 23 | No conflict | Confirm with CA |
| 2 | SLI-004: Packing → Row 49 | **YES: vs BCIPL-004** | CA must confirm industry treatment |
| 3 | SLI-006: KMP Remuneration → Row 45 | **YES: vs BCIPL-001** | CA must confirm for manufacturing clients |
| 4 | SLI-007: Security Deposits → Row 238 | **YES: vs V1 C-004** | CA must confirm; may need to update V1 C-004 |
| 5 | SLI-010: Italian parent payables → Row 153 | No conflict | Confirm treatment |
| 6 | SLI-005: All repairs → Row 72 | No conflict | Confirm if Row 50 should be used |

---

## Recommended Updates to Existing Rules (Pending CA Verification)

1. **V1 Rule C-004 (Security Deposits):** Split into two sub-rules:
   - Deposits with government entities (electricity board, telephone, municipality) → Row 237
   - Deposits with private parties (landlords, vendors, customers) → Row 238

2. **BCIPL-001 (Director Remuneration):** Add industry flag:
   - Manufacturing: Director remuneration → Row 45 (included in Wages)
   - Trading/Services: Director remuneration → Row 67 (Salary and staff expenses)

3. **BCIPL-004 (Packing):** Add context flag:
   - Trading/selling packing → Row 70
   - Manufacturing production packing → Row 49
