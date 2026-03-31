# CMA Classification Rules — INPL (IFFCO-Nanoventions Private Limited)

**Company:** IFFCO-NANOVENTIONS PRIVATE LIMITED (formerly Nanoventions Private Limited)
**Industry Type:** Manufacturing — Nano & Bio Formulation Products + R&D Services
(Hybrid: manufactures products AND provides technical/consulting services to group companies)
**Location:** Coimbatore, Tamil Nadu
**Financial Years Covered:** FY2022-23, FY2023-24, FY2024-25
**Total Line Items Analysed:** ~120 distinct items across P&L and Balance Sheet (3 years)
**New Rules Generated:** 14 (INPL-001 through INPL-014)
**Items Covered by Existing Reference/Rules:** ~70 (listed at end)
**Rule IDs:** INPL-001 to INPL-014
**Prepared by:** AI analysis vs CMA ground truth (Nanoventions CMA 10032026.xls)
**Date:** 2026-03-22
**Verified by:** ☐ Pending CA sign-off

---

## Context

IFFCO-Nanoventions is a **young manufacturing company** (incorporated 2021) in Coimbatore that:
1. **Manufactures** nano and bio formulation products at its Thondamuthur factory
2. **Provides services** to IFCO group companies (formerly SIPCO) — this is a major revenue stream
3. Is **rapidly growing**: Revenue ₹10.56 Cr (FY23) → ₹65.70 Cr (FY24) → ₹140.27 Cr (FY25)
4. Has **heavy related-party transactions**: majority of revenue from and loans from associated companies
5. Has **no imports or exports** (FY23/24); small exports started FY25

**Key features of their accounting:**
- Revenue = Products + Services combined in Domestic Sales (Row 22)
- No working capital bank loans (FY23-FY24); CC facility only projected from FY27
- Related party unsecured loans = primary long-term financing (treated as term loans in CMA)
- Large capital expenditure on factory construction (via MKS Construction Pvt Ltd, related party)
- Employee cost includes very high Directors' Remuneration (classified to Row 73, not Row 67)
- WIP build-up in FY24 (₹6.15 Cr) consumed in FY25 (released to Cost of Sales)

---

## Why These Rules Are Needed

The 384-item reference and existing V1/BCIPL/SRP/SSSS rules handle most standard items. But INPL has 14 categories where:

1. The item is **manufacturing + service hybrid specific** and not in the reference
2. The CA **mapped differently** from prior company rules (especially Directors Remuneration, security deposits)
3. The item **appears in an unexpected CMA row** given its description (e.g., consultancy in Row 49 not Row 71)
4. There is a **judgment call** that conflicts with another company's rule (documented as conflicts)

---

## RULE INPL-001 — Service Revenue → Domestic Sales (Row 22)

**Applies to:** Manufacturing + Service hybrid companies (and pure service companies)

**Pattern it catches:**
- `Sale of Services`
- `Revenue from Services`
- `Service Income`
- `Service Charges` (when in revenue/income section)
- `Job Work Income` (when in revenue section, not expenses)
- `Contract Revenue`
- `Technical Services Income`

**Classification:** Domestic Sales → Row 22

**Why this rule exists:**
INPL earns revenue BOTH from selling manufactured products AND from providing technical services to IFCO group companies. The AI, seeing "Sale of Services" or "Service Income," might route it to:
- Row 34 (Others Non-Operating Income) — thinking it's "other" income, not core sales
- Or flag as DOUBT because the 384-item reference focuses on product sales

The CA's correct treatment: **All service revenue is part of core operations and belongs in Row 22 (Domestic Sales)**, regardless of whether it's product-based or service-based.

This is consistent with Indian GAAP: companies report "Revenue from Operations" which includes both.

**Real example from INPL:**
```
Source text:   "Sale of Services"
Section:       Note 21/20 — Revenue from Operations
Amount (FY23): ₹20,104.24 thousand (₹2.01 Crores) — 19% of total revenue
Amount (FY24): ₹4,11,153.18 thousand (₹41.12 Crores) — 63% of total revenue
Correct field: Domestic Sales  [Row 22]
Old result:    Others (Non-Operating Income) [Row 34] or DOUBT  (WRONG)
New result:    Domestic Sales  [Row 22]  ✓
```

**When this rule would be WRONG:**
If a pure service company's "service income" is classified as Other Income (e.g., rental income from incidental property letting). But core business service revenue always → Row 22.

**Verify:** Do you agree that "Sale of Services" revenue from core operations should go to Domestic Sales (Row 22)?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE INPL-002 — Unbilled Services → Domestic Receivables (Row 206)

**Applies to:** Service companies and manufacturing companies that bill on project completion

**Pattern it catches (in Trade Receivables / Other Current Assets section of Balance Sheet):**
- `Unbilled Services`
- `Unbilled Revenue`
- `Revenue in excess of billings`
- `Work completed not billed`
- `Accrued Revenue`

**Classification:** Domestic Receivables → Row 206

**Why this rule exists:**
INPL renders technical/consulting services to IFCO group companies on an ongoing basis. At year-end, services rendered but not yet invoiced are recorded as "Unbilled Services" — a current asset.

The AI might misclassify this as:
- Row 223 (Other Advances) — because it's in "Other Current Assets" section
- Row 222 (Prepaid Expenses) — because it looks like an accrual
- Or DOUBT — because the text doesn't look like a traditional trade receivable

The correct classification: "Unbilled Services" is functionally a trade receivable (money the company has EARNED but not yet invoiced), so it belongs in Row 206 (Domestic Receivables).

**Real example from INPL FY2022-23:**
```
Source text:   "Unbilled Services"
Section:       Note 16 (Trade Receivables)
Amount:        ₹1,650.45 thousand (₹1.65 Lakhs)
               Included alongside trade receivables of ₹54,844.88 thousand
Correct field: Domestic Receivables  [Row 206]
Old result:    Other Advances [Row 223] or DOUBT  (WRONG)
New result:    Domestic Receivables  [Row 206]  ✓
```

**Verify:** Do you agree unbilled services (accrued revenue) should be part of Trade Receivables (Row 206)?
☐ Yes, correct   ☐ No, it should go to Row 223 (Other Advances): _______________________

---

## RULE INPL-003 — Consultancy Charges → Others Manufacturing (Row 49)

**Applies to:** Manufacturing and R&D companies where consultancy is a direct production cost

**Pattern it catches (in P&L Expenses section):**
- `Consultancy Charges`
- `Consultancy Fees`
- `Technical Consultancy`
- `R&D Consultancy`
- `Scientific Consultancy`
- `Process Consultancy`

**Classification:** Others (Manufacturing) → Row 49

**Why this rule exists:**
For INPL (nano/bio formulation manufacturer), consultancy fees are paid to scientists, technical experts, and research consultants who directly contribute to the manufacturing/R&D process. This is a **direct production cost**, not an administrative overhead.

Without this rule, the AI sees "Consultancy Charges" and routes it to:
- Row 71 (Others Admin) — the default for consultancy in trading/admin companies
- This is WRONG for a manufacturing/R&D company where consultancy is core production input

The CA consistently maps consultancy to Row 49 (Others Manufacturing) across all 3 years, reflecting the manufacturing nature of the expense.

**Real example from INPL FY2022-23:**
```
Source text:   "Consultancy Charges"
Section:       Note 27 (Other Expenses)
Amount (FY23): ₹3,110.37 thousand (₹3.11 Lakhs)  → Row 49
Amount (FY24): ₹24,453.18 thousand (₹24.45 Lakhs) → Row 49 (part of ₹117.87 Lakh Row 49 total)
Amount (FY25): ₹17.91 Lakhs (smaller — reduced consultancy dependency)
Correct field: Others (Manufacturing)  [Row 49]
Old result:    Others (Admin) [Row 71]  (WRONG for manufacturing/R&D company)
New result:    Others (Manufacturing)  [Row 49]  ✓
```

**When this rule would be WRONG:**
For a trading firm or pure admin company where consultancy is for HR, legal, or IT purposes — those should go to Row 71. The manufacturing/R&D context distinguishes INPL's consultancy from admin consultancy.

**Verify:** Do you agree consultancy charges for INPL's manufacturing/R&D operations go to Row 49 (Others Manufacturing)?
☐ Yes, correct   ☐ No, they should go to Row 71 (Others Admin): _______________________

---

## RULE INPL-004 — Warehouse Charges Paid → Others Manufacturing (Row 49)

**Applies to:** Manufacturing companies using third-party warehouses for raw material/product storage

**Pattern it catches:**
- `Warehouse Charges Paid`
- `Warehouse Charges`
- `Warehousing Charges`
- `Godown Rent` (when for goods storage, not office premises)
- `Storage Charges` (for goods)
- `Cold Storage Charges`

**Classification:** Others (Manufacturing) → Row 49

**Why this rule exists:**
INPL stores raw materials and finished goods in third-party warehouses and pays warehouse charges. This is a **direct manufacturing/distribution cost** (cost of handling/storing the product), not an administrative expense.

Without this rule, the AI might route "Warehouse Charges" to:
- Row 68 (Rent, Rates and Taxes) — confusing warehouse rent with office rent
- Row 71 (Others Admin) — treating it as a general overhead
- Row 47 (Freight) — confusing storage with transport

The CA maps warehouse charges to Row 49 (Others Manufacturing) consistently.

**Real example from INPL FY2022-23:**
```
Source text:   "Warehouse Charges Paid"
Section:       Note 27 (Other Expenses)
Amount (FY23): ₹2,088.50 thousand (₹2.09 Lakhs)
Correct field: Others (Manufacturing)  [Row 49]
Old result:    Rent, Rates and Taxes [Row 68] or Others Admin [Row 71]  (WRONG)
New result:    Others (Manufacturing)  [Row 49]  ✓
```

**Distinguish from office rent** which goes to Row 68. Key: "Warehouse charges" or "Godown rent" for goods = Row 49. "Office Rent" = Row 68.

**Verify:** Do you agree warehouse storage charges go to Others Manufacturing (Row 49)?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE INPL-005 — Material Handling Charges → Others Manufacturing (Row 49)

**Applies to:** Manufacturing companies with significant material movement between factory and warehouse

**Pattern it catches:**
- `Material Handling Charges`
- `Material Handling`
- `Handling Charges` (when in manufacturing context, not at sales/dispatch stage)
- `Goods Handling Charges`
- `Loading/Unloading Charges` (when for raw material or WIP movement within plant)

**Classification:** Others (Manufacturing) → Row 49

**Why this rule exists:**
INPL incurs significant material handling charges as materials are moved between storage, processing areas, and dispatch. This is a **core manufacturing cost** — ₹1.94 Crores (FY24) and ₹2.52 Crores (FY25) making it one of the top 5 manufacturing expenses.

Without this rule, the AI sees "Material Handling Charges" and routes to:
- Row 47 (Freight and Transportation) — confusing material movement within plant with outward freight
- Row 71 (Others Admin) — misidentifying it as overhead

**Note:** If "Material Handling Charges" appear in the SALES schedule (charges billed TO customers), they go to Row 22 (Domestic Sales) per SSSS-010.

**Real example from INPL:**
```
Source text:   "Material Handling Charges"
Section:       Note 27 (Other Expenses) — expense side
Amount (FY24): ₹19,444.01 thousand (₹19.44 Lakhs)
Amount (FY25): ₹2.518 Crores (₹251.80 Lakhs)  — growing rapidly
Correct field: Others (Manufacturing)  [Row 49]
Old result:    Freight & Transportation [Row 47] or Others Admin [Row 71]  (WRONG)
New result:    Others (Manufacturing)  [Row 49]  ✓
```

**Verify:** Do you agree material handling charges (inbound/within plant) go to Row 49?
☐ Yes, correct   ☐ No, it should go to Row 47 (Freight): _______________________

---

## RULE INPL-006 — Research and Development Expenses → Others Manufacturing (Row 49)

**Applies to:** Manufacturing and pharma/biotech companies with in-house R&D

**Pattern it catches (in P&L expense section):**
- `Research and Development`
- `Research & Development`
- `R&D Expenses`
- `Research Expenses`
- `Development Costs`
- `Product Development`

**Classification:** Others (Manufacturing) → Row 49

**Why this rule exists:**
INPL is a nano/bio formulation company — R&D is core to their manufacturing process. R&D costs = improving and developing the products they manufacture. This is a **manufacturing expense**, not admin.

Without this rule, the AI might route R&D to:
- Row 76 (Deferred Revenue Expenditures) — if it thinks R&D will be capitalised
- Row 75 (Miscellaneous Expenses written off) — another common error
- Row 71 (Others Admin) — wrong category entirely

The CA maps R&D directly to Row 49 (Others Manufacturing) for all years.

**Real example from INPL FY2022-23:**
```
Source text:   "Research and development"
Section:       Note 27 (Other Expenses)
Amount (FY23): ₹370.90 thousand (₹3.71 Lakhs)
Amount (FY25): ₹443.95 Lakhs (₹4.44 Crores) — major growth as company expands R&D
Correct field: Others (Manufacturing)  [Row 49]
Old result:    Deferred Revenue [Row 76] or Others Admin [Row 71]  (WRONG)
New result:    Others (Manufacturing)  [Row 49]  ✓
```

**Verify:** Do you agree R&D expenses go to Others Manufacturing (Row 49)?
☐ Yes, correct   ☐ No, should be capitalised or go elsewhere: _______________________

---

## RULE INPL-007 — Related Party Unsecured Loans (Associates) → Term Loan after 1 Year (Row 137)

**Applies to:** Manufacturing companies financed primarily by promoter/associate group loans

**Pattern it catches (in Long-Term Borrowings section of Balance Sheet):**
- `Unsecured Loan from [Associate Company Name]`
- `Loan from [Related Party]` (when classified as LT in balance sheet)
- `Loan from [LLP/Partnership Firm]` (promoter group)
- `Director's Loan` (large amount, LT)
- Specifically: "Ideal Energy Transmission LLP", "IFCO Limited", "SIPCO New Delhi"

**Classification:** Term Loan Balance Repayable after one year → Row 137

**Why this rule exists:**
INPL's primary financing is through unsecured loans from associated companies (Ideal Energy Transmission LLP, IFCO/SIPCO, and Director Arjun Pal Ganga). Although these are "unsecured" in legal terms, the CA treats them as **long-term term loans** in the CMA.

The CA's approach: these loans are:
1. Long-term in nature (repayment over years)
2. The primary source of capital for factory construction
3. Treated equivalently to bank term loans for CMA purposes

**IMPORTANT CONFLICT WITH SSSS-012:** The SSSS company CA used Row 152/153 (Unsecured Loans) for similar related-party loans. INPL's CA uses Row 137 (Term Loans). Both approaches exist in practice. The app should FLAG this for CA verification rather than auto-classifying.

**Real example from INPL FY2022-23:**
```
Source text:   "Ideal Energy Transmission LLP" / "Unsecured Loan"
Section:       Note 6 (Long Term Borrowings)
Amount:        ₹89,050.00 thousand (₹8.91 Crores)
Also:          "SIPCO New Delhi, Associate Company" ₹21,400 thousand + "Arjun Pal Ganga" ₹7,000 thousand
Total:         ₹1,17,450.00 thousand (₹11.75 Crores) — 97% of total LT borrowing
Correct field: Term Loan Balance Repayable after 1 year  [Row 137]
Old result:    Unsecured Loans Long-Term [Row 153] per SSSS-012 logic  (DIFFERENT approach)
INPL CA:       Term Loan Balance after 1 year  [Row 137]  ✓ per INPL CMA
```

**App guidance:** When a large unsecured loan from a related party appears in the LT Borrowings section, the verification screen should ask:
- "Is this loan to be shown as a Term Loan (Row 137) or Unsecured Loan (Row 152/153)?"
- Pre-fill with Row 137 for INPL; CA can override

**Verify:** Do you agree related party (associate company) loans should go to Term Loans (Row 137) rather than Unsecured Loans (Row 152/153)?
☐ Yes, Row 137 correct   ☐ No, use Row 152/153: _______________________

---

## RULE INPL-008 — Accrued Interest on Related Party Loans → Other Current Liabilities (Row 250)

**Applies to:** All industries with related party borrowings where interest is accrued but unpaid

**Pattern it catches (in Other Long-Term Liabilities OR Other Current Liabilities section):**
- `Accrued Interest Payable — Related Parties`
- `Interest Payable — [Related Party Name]`
- `Interest Accrued but not paid`
- `Interest Payable on Unsecured Loan`

**Classification:** Other Current Liabilities → Row 250

**Why this rule exists:**
INPL accrues large amounts of interest on its related-party loans that remain unpaid at year-end. In FY23, this was ₹3,214.38 thousand (₹3.21 Lakhs). In FY24, this ballooned to ₹1,40,147 thousand (₹14.01 Crores!) — because the interest accumulated for multiple years without cash payment.

In the actual Balance Sheet, the company shows this under "Other Long-Term Liabilities" (since accrual has been building for years). But in the CMA, the CA includes it in Row 250 (Other Current Liabilities) — treating it as payable rather than long-term.

Without this rule, the AI might put accrued interest in:
- Row 247 (Interest Accrued but not due) or Row 248 (Interest Accrued and due) — these rows exist in the CMA but are separate lines
- Or simply classify it as Row 83/84 (Finance cost, which is wrong — it's a BS item, not P&L)

**Real example from INPL:**
```
Source text:   "Accrued Interest payable - Related Parties"
Section:       Note 8 (Other Long-Term Liabilities) in Balance Sheet
Amount (FY23): ₹3,214.38 thousand (₹3.21 Lakhs)
Amount (FY24): ₹1,40,147 thousand (₹14.01 Crores) — 3 years of unpaid interest!
Correct field: Other Current Liabilities  [Row 250]  (per CMA ground truth)
Old result:    Interest Accrued but not due [Row 247] or DOUBT  (WRONG)
New result:    Other Current Liabilities  [Row 250]  ✓
```

**Verify:** Do you agree accrued unpaid interest on related party loans goes to Row 250 (Other Current Liabilities)?
☐ Yes, correct   ☐ No, it should go to Row 247/248: _______________________

---

## RULE INPL-009 — Private Security Deposits (Lease, Electricity, Gas) → Other Non-Current Assets (Row 238)

**Applies to:** All industries with deposits paid to private parties (landlords, utilities, equipment lessors)

**Pattern it catches (in Non-Current Assets section of Balance Sheet):**
- `Deposit for Lease Rental`
- `Security Deposit for Lease`
- `Deposit for Electricity`
- `Deposit for Gas`
- `Security Deposit` (when paid to PRIVATE entities, not government)
- `Refundable Deposit`

**Classification:** Other Non-Current Assets → Row 238

**Why this rule exists:**
INPL pays deposits to:
- Landlord (for lease rental)
- Electricity board (for power connection)
- Gas company (for gas connection)

These appear in the Balance Sheet under "Other Non-Current Assets."

**IMPORTANT CONFLICT WITH V1 RULE C-004:** Rule C-004 maps "Security Deposits" to Row 237 (Security deposits with government departments). INPL's CA uses Row 238 (Other Non-Current Assets) instead.

The reason: Row 237 is specifically for **government departments**. INPL's deposits are paid to:
- Private electricity company (not necessarily a government entity)
- Private landlord
- Gas company (private)

When the deposit recipient is private (not a government department), the correct row is Row 238, not Row 237.

**Real example from INPL FY2022-23:**
```
Source text:   "Security and other deposits"   ₹288.00 thousand
               "Deposit for Electricity"         ₹37.03 thousand
               "Deposit for Gas"                 ₹12.00 thousand
Section:       Note 14 (Other Non-Current Assets)
Total:         ₹337.03 thousand (₹3.37 Lakhs)
Correct field: Other Non-Current Assets  [Row 238]
C-004 says:    Security deposits with government departments  [Row 237]  (WRONG for private deposits)
INPL CA uses:  Other Non-Current Assets  [Row 238]  ✓
```

**Guidance for app:** Default to Row 237 (C-004 rule) for any government utility (electricity board, BSNL, water authority). Use Row 238 for private party deposits.

**Verify:** Should deposits to private landlords and private utilities go to Row 238 (Other Non-Current Assets)?
☐ Yes, Row 238 for private   ☐ No, use Row 237 for all deposits: _______________________

---

## RULE INPL-010 — All Repairs & Maintenance (Buildings + Plant + Others) → Row 50

**Applies to:** Manufacturing companies

**Pattern it catches (in P&L expenses, Manufacturing section):**
- `Repairs and Maintenance: Buildings`
- `Repairs and Maintenance: Plant and Machinery`
- `Repairs and Maintenance: Others`
- `Building Repairs`
- `Plant Maintenance`
- `Factory Maintenance`

**Classification:** Repairs & Maintenance (Manufacturing) → Row 50

**Why this rule exists:**
The CMA has TWO Repairs rows:
- Row 50: Repairs & Maintenance (Manufacturing) — for factory/plant repairs
- Row 72: Repairs & Maintenance (Admin) — for office/admin premises repairs

For INPL, the CA puts ALL repairs (buildings, plant & machinery, and others) into Row 50 (Manufacturing). This includes building repairs, even though "building" might seem like it should go to the admin row.

The reason: INPL's buildings are primarily the factory building, not office buildings. So all building repairs = factory repairs = Row 50.

**Real example from INPL FY2022-23:**
```
Source text (breakdown):
  "Repairs & Maintenance: Buildings"      ₹1,404.29 thousand
  "Repairs & Maintenance: Plant and Machinery" ₹4,240.94 thousand
  "Repairs & Maintenance: Others"         ₹443.35 thousand
Section:   Note 27 (Other Expenses)
Total:     ₹6,088.58 thousand (₹6.09 Lakhs)
All → Correct field: Repairs & Maintenance (Manufacturing)  [Row 50]
Old result: Building repairs → Row 72 (Admin), Plant → Row 50  (SPLIT — WRONG)
INPL CA:   ALL to Row 50  ✓
```

CMA Row 50 FY23 = 0.564523 Crores ≈ 5,645 Rs.'000 (Building + Plant repairs, excluding "Others" which went elsewhere)

**Verify:** For INPL, should ALL repairs go to Row 50 (Manufacturing), not Row 72 (Admin)?
☐ Yes, all to Row 50   ☐ No, split office vs factory repairs: _______________________

---

## RULE INPL-011 — General "Labour Charges Paid" (External, Unspecified) → Wages (Row 45)

**Applies to:** Manufacturing companies using contract/daily labour for general work

**Pattern it catches (in P&L Other Expenses section):**
- `Labour Charges Paid`
- `Labour Charges`
- `Contract Labour Charges` (when no specific process mentioned)
- `Labour Cost` (unspecified)
- `Daily Labour`
- `Casual Labour`

**Classification:** Wages → Row 45

**Why this rule exists:**
INPL hires external contract workers for general factory work (loading, cleaning, material handling, etc.) and books this as "Labour Charges Paid" in Other Expenses. This is economically equivalent to wages paid to permanent employees and goes to Row 45 (Wages).

**DISTINGUISH FROM:**
- SSSS-003: "Cutting Labour Charges" → Row 46 (Processing/Job Work) — for specific manufacturing process labour
- BCIPL-003: "Job Work Charges" → Row 46 — for sub-contracting specific production steps
- INPL-011: **General, unspecified "Labour Charges Paid"** → Row 45 (Wages) — for daily/casual labour with no specific process

The key differentiator: if labour is for a **specific named manufacturing process** (cutting, welding, assembly), → Row 46. If it's general/unspecified labour, → Row 45.

**Real example from INPL FY2022-23:**
```
Source text:   "Labour charges Paid"
Section:       Note 27 (Other Expenses)
Amount:        ₹355.67 thousand (₹3.56 Lakhs)
Note:          This is external casual labour, not permanent employees
Correct field: Wages  [Row 45]  (not Row 46 Processing)
Old result:    Others Admin [Row 71] or DOUBT  (WRONG)
New result:    Wages  [Row 45]  ✓
```

**Verify:** Do you agree general "Labour Charges Paid" (unspecified external labour) = Wages (Row 45)?
☐ Yes, correct   ☐ No, it should go to Row 46 (Processing): _______________________

---

## RULE INPL-012 — Directors Remuneration → Audit Fees & Directors Remuneration (Row 73)

**Applies to:** All industries

**Pattern it catches:**
- `Directors Remuneration`
- `Director's Remuneration`
- `Managing Director Remuneration`
- `Directors' Salary` (when it is literally directors' compensation, not salaried staff)
- `Managerial Remuneration`

**Classification:** Audit Fees & Directors Remuneration → Row 73

**Why this rule exists:**
The CMA field name for Row 73 is literally **"Audit Fees & Directors Remuneration"** — this is the correct CMA row for Directors Remuneration. INPL's CA consistently places Directors Remuneration in Row 73.

**CONFLICT WITH BCIPL-001:** BCIPL's rule says Directors Remuneration → Row 67 (Salary and staff expenses). INPL's approach (Row 73) is more aligned with the actual CMA field name.

Real data confirms: INPL's CMA shows:
- Row 67 (Salary) FY24/25 = 0.00 (Directors Remuneration is NOT in Row 67)
- Row 73 (Audit & Directors) FY24 = 1.56 Crores = Audit Fees (~0.75 Lakhs) + Directors Rem (₹11.60 Lakhs)

**Real example from INPL FY2022-23:**
```
Source text:   "Directors Remuneration"
Section:       Note 25 (Employee Benefits Expense)
Amount (FY23): ₹3,490.00 thousand (₹3.49 Lakhs) — Dr. A Lakshmanan + C. Rajesh Srinivasan
Amount (FY24): ₹11,600.00 thousand (₹11.60 Lakhs)
Amount (FY25): ₹1,064.89 Lakhs (₹10.65 Crores) — major scale-up
Correct field: Audit Fees & Directors Remuneration  [Row 73]
BCIPL-001 says: Salary and staff expenses [Row 67]  (DIFFERENT — verify which is correct)
INPL CA uses:  Audit Fees & Directors Remuneration  [Row 73]  ✓
```

**Why Row 73 makes more sense:** The CMA field is explicitly named "Audit Fees & Directors Remuneration" — the field name itself directs Directors Remuneration here. Row 67 is named "Salary and staff expenses" which better suits non-director employee salaries.

**Recommendation:** OVERRIDE BCIPL-001 for Directors Remuneration. Use Row 73, not Row 67.

**Verify:** Do you agree Directors Remuneration should go to Row 73 (Audit Fees & Directors Remuneration), NOT Row 67 (Salary)?
☐ Yes, Row 73 is correct — override BCIPL-001   ☐ No, use Row 67: _______________________

---

## RULE INPL-013 — Capital Expenditure Payable → Other Current Liabilities (Row 250)

**Applies to:** Manufacturing companies under construction / expanding their factory

**Pattern it catches (in Current Liabilities / Other Current Liabilities section of Balance Sheet):**
- `Capital expenditure Payable`
- `Capital Creditors`
- `Creditors for Capital Goods`
- `Payable for Fixed Assets`
- `Construction Work Payable`
- `Creditors for Plant and Machinery`

**Classification:** Other Current Liabilities → Row 250

**Why this rule exists:**
INPL is actively building its factory (via MKS Construction Pvt Ltd) and buying lab equipment (via Awarify Tech Systems). At year-end, amounts owed to these capital goods suppliers are classified as "Capital expenditure Payable" — a current liability.

The AI might put this in:
- Row 242 (Sundry Creditors for Goods) — because it's an amount owed to a supplier
- Row 249 (Creditors for Expenses) — because it looks like an expense payable
- DOUBT — because capital creditors is an unusual line item

The CA's correct classification: Row 250 (Other Current Liabilities), distinguishing it from trade payables for goods.

**Real example from INPL FY2022-23:**
```
Source text:   "Capital expenditure Payable"
Section:       Note 12 (Other Current Liabilities)
Amount (FY23): ₹20,503.55 thousand (₹20.50 Lakhs) — payable to MKS Construction & Awarify Tech
Correct field: Other Current Liabilities  [Row 250]
Old result:    Sundry Creditors [Row 242] or Creditors for Expenses [Row 249]  (WRONG)
New result:    Other Current Liabilities  [Row 250]  ✓
```

**Note:** FY23 amount (₹20.50 Lakhs) is very large vs total trade payables (₹21.21 Lakhs). This confirms it's capital-related, not goods purchases.

**Verify:** Do you agree capital equipment payables go to Row 250 (Other Current Liabilities), not Row 242 (Sundry Creditors)?
☐ Yes, correct   ☐ No, it should go to Row 242: _______________________

---

## RULE INPL-014 — Digital Wallet Balance → Other Advances / Current Asset (Row 223)

**Applies to:** All industries with company-owned digital payment wallets

**Pattern it catches (in Other Current Assets / Short Term Loans section):**
- `Deposit in Wallet`
- `Wallet Balance`
- `Digital Wallet`
- `Paytm Balance`
- `PhonePe Balance`
- `UPI Wallet`
- `Prepaid Payment Instrument`

**Classification:** Other Advances / current asset → Row 223

**Why this rule exists:**
INPL maintains a balance in a digital wallet (for payments, petty cash, vendor payments) that appears as "Deposit in Wallet" in Other Current Assets. This is common for modern Indian companies using digital payment platforms.

The AI might misclassify this as:
- Row 212 (Cash on Hand) — because wallet balance seems like cash
- Row 213 (Bank Balances) — because digital payments are bank-adjacent
- Row 222 (Prepaid Expenses) — because "prepaid" wallet

The correct classification: Row 223 (Other Advances / current asset) — wallet balances are neither cash nor bank balances; they're prepaid amounts held with a payment service provider.

**Real example from INPL FY2022-23:**
```
Source text:   "Deposit in Wallet"
Section:       Note 19 (Other Current Assets)
Amount:        ₹209.73 thousand (₹2.10 Lakhs)
Correct field: Other Advances / current asset  [Row 223]
Old result:    Cash on Hand [Row 212] or Bank Balances [Row 213]  (WRONG)
New result:    Other Advances / current asset  [Row 223]  ✓
```

**Verify:** Do you agree digital wallet balances should go to Other Advances (Row 223)?
☐ Yes, correct   ☐ No, it should be Cash (Row 212): _______________________

---

## ITEMS ALREADY COVERED BY EXISTING REFERENCE — No New Rule Needed

The following items in INPL's financials are handled correctly by the existing 384-item reference or prior rules. No new rule needed:

| Item | Source Text | Correct Row | Covered By |
|------|-------------|-------------|------------|
| Domestic Sales (products) | `Sales of Products` | 22 | Reference |
| Export Sales | `Export Sales` | 23 | Reference |
| Interest on Fixed Deposit | `Interest on Fixed Deposit` | 30 | Reference / Rule B-001 |
| Gain on FX | `Gain on Foreign Exchange Fluctuation` | 32 | Reference |
| Other miscellaneous income | `Discount Received` (small, FY23) | 34 | Reference |
| Raw Materials Consumed | `Cost of Material Consumed` | 42 | Reference |
| Packing Materials (inventory) | Combined into Raw Materials row | 42 | Reference |
| All Employee Wages/Salaries | `Employee Benefits Expenses` | 45 | Reference |
| Packing and Forwarding | `Packing and Forwarding Charges` | 47 | Rule C-003 |
| Power and Fuel | `Power and Fuel` | 48 | Reference |
| Security Service Charges | `Security Charges` | 51 | Reference |
| WIP Opening/Closing | `Stock in process Opening/Closing` | 53/54 | Reference |
| Finished Goods Opening/Closing | `Finished Goods Opening/Closing` | 58/59 | Reference |
| Depreciation | `Depreciation and Amortisation Expenses` | 56+63 | Reference |
| Rent Paid | `Rent Paid` | 68 | Reference |
| Rates & Taxes | `Rates & Taxes` | 68 | Reference |
| Advertisements / Business Promotion | `Business Promotion Expenses` | 70 | Reference / BCIPL-004 |
| Office Expenses | `Office Expenses` | 71 | Reference |
| Insurance | `Insurance Paid` | 71 | Reference |
| Travelling and Conveyance | `Travelling and Conveyance Expenses` | 71 | Reference |
| Printing and Stationery | `Printing & Stationery` | 71 | Reference |
| Licence and Subscription | `Licence and Subscription` | 71 | Reference |
| Internet & Telephone | `Internet and Telephone Expenses` | 71 | Reference |
| Miscellaneous Expenses | `Miscellaneous Expenses` | 71 | Reference |
| Audit Fees | `Auditors Remuneration` | 73 | Reference |
| Interest on Loans (unsecured/LT) | `Interest on Unsecured Loan` | 83 | BCIPL-006 / SSSS-008 |
| Bank Charges | `Bank Charges` | 85 | Reference |
| Other Non-Operating Expenses | `Project Cost` (small FY23) | 93 | Reference |
| Income Tax Provision | `Provision for Taxation` | 99 | Reference |
| Deferred Tax Liability | `Deferred Tax Liability` | 100 | Reference |
| Deferred Tax Asset | `Deferred Tax Asset` | 101 | Reference |
| Share Capital (paid-up) | `Issued, Subscribed and Paid Up` | 116 | Reference |
| Share Premium | `Share Premium A/c` | 123 | Reference |
| Retained Earnings | `Balance transferred from P&L a/c` | 122 | Reference |
| Bank Term Loan (vehicle loan) | `ICICI Bank — Vehicle Loan` | 136/137 | Reference |
| WC Bank Finance | `From ICICI` (CC facility — FY26+ only) | 131 | Reference |
| Gross Block | All fixed assets combined | 162 | Reference |
| Motor Vehicles | `Vehicle` (ICICI vehicle loan asset) | 162 | Rule C-001 |
| Raw Material Inventory | Combined raw+packing+consumables | 194 | Reference |
| WIP Inventory | `Stocks-in-process` | 200 | Reference |
| Finished Goods Inventory | `Finished Goods` | 201 | Reference |
| Cash on Hand | `Cash on Hand` | 212 | Reference |
| Bank Balances | `Balance with Banks` | 213 | Reference |
| FD under Lien | `Fixed Deposit under Lien` | 214 | Reference |
| Other FDs | `Other Fixed Deposits` | 215 | Reference |
| Salary Advance | `Salary Advance` | 219 | Reference |
| Advance for Capital Expenses | `Advance for Capital Expenses` | 219 | Reference |
| Advances to Suppliers | `Advances to Suppliers` | 220 | Reference |
| Advance Income Tax | `Advance Tax / TDS Receivable` | 221 | SSSS-013 |
| Prepaid Expenses | `Prepaid Expenses` | 222 | Reference |
| GST ITC / Tax Credit | `Tax Credit Pending Utilisation` | 223 | SSSS-013 |
| Expense Advances (Kotak card) | `Advance for Expenses — Kotak` | 223 | Reference |
| Trade Payables (non-MSME) | `Trade Payables — Others` | 242 | Reference |
| Advance from Customers | `Advance from Customers` | 243 | Reference |
| Tax Provision (net) | `Provision for Taxation` | 244 | Reference |
| GST/TDS/PF Payable | `Statutory Liability` | 246 | SSSS-013 (partial) |
| Expense Creditors | `Creditors for Expenses` | 249 | Reference |
| Director payable | `To Directors` (current amounts) | 250 | Reference |
| Related party payable (current) | `To Related Parties` | 250 | Reference |
| Audit Fees & Directors Rem (combined) | See CMA Row 73 field | 73 | Rule INPL-012 |

---

## ITEMS REQUIRING CA JUDGMENT — NOT Automatable

| Item | Issue | Verification Prompt |
|------|-------|---------------------|
| Related party loans (Ideal Energy, IFCO) | Whether to classify as Term Loans (Row 137) vs Unsecured Loans (Row 153) | "These loans from associate companies total ₹X Cr. Should they go to Term Loans (Row 137) as per INPL's CA, or Unsecured Loans (Row 153) as per standard practice? Default: Row 137" |
| Accrued interest on related party loans | Large balance (₹14 Cr in FY24) — is it current or long-term? | "₹X Cr of accrued unpaid interest on related party loans. Classified to Other Current Liabilities (Row 250). Confirm?" |
| Directors Remuneration split | FY25 shows ₹10.65 Crores Directors Remuneration — confirm this large amount | "Directors Remuneration = ₹X Cr. Is this for multiple directors including Managing Director remuneration?" |
| FY25 PAT discrepancy | CMA shows 34.01 Crores PAT vs P&L reading of ~13.56 Crores | "Verify FY25 PAT figure in CMA vs audited P&L. CMA shows ₹34 Cr, our extraction reads ₹13.56 Cr." |
| Revenue unit change FY25 | FY25 PDF changed from Rs.'000 to Rs. Lakhs | Flag to user when processing FY25: "This file uses Rs. Lakhs (not Rs. thousands). Please confirm scale." |
| Export Sales (Row 23) vs Domestic (Row 22) | FY25 has ₹1.92 Cr exports — first time. Need to verify if INPL separately identifies export bills | "FY25 shows export revenue ₹1.92 Cr. Do you want this in Export Sales (Row 23) or combined with Domestic (Row 22)?" |

---

## CONFLICTS WITH EXISTING RULES

| Rule | Existing Rule | INPL Approach | Recommendation |
|------|--------------|---------------|----------------|
| Directors Remuneration | BCIPL-001: → Row 67 (Salary) | INPL: → Row 73 (Audit & Dir. Rem.) | **Override BCIPL-001**. Row 73 is named "Audit Fees & Directors Remuneration" — this is clearly correct. BCIPL-001 should be updated. |
| Related Party Loans | SSSS-012: → Row 152/153 (Unsecured Loans) | INPL: → Row 137 (Term Loans) | **Flag for CA judgment**. Both approaches exist. App should ask CA each time. |
| Security Deposits | C-004: → Row 237 (Govt departments) | INPL: → Row 238 (Other Non-Current) | **Coexist**. C-004 for govt deposits. INPL-009 for private party deposits. |

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total distinct line items documented (FY23–FY25) | ~120 |
| Items handled by existing 384-item reference | ~65 |
| Items handled by existing V1 rules (A-001 to D-002) | ~5 |
| Items handled by BCIPL rules | ~5 |
| Items handled by SRP rules | ~3 |
| Items handled by SSSS rules | ~3 |
| **NEW rules created in this document** | **14** |
| Items requiring CA judgment (not automatable) | **6** |
| Conflicts with existing rules discovered | **3** (documented above) |

---

## Testing Recommendations

To validate these rules when INPL documents are processed through the app:

1. **INPL-001 test:** "Sale of Services" should appear in Row 22 (Domestic Sales), NOT Row 34 (Others Non-Op Income)
2. **INPL-002 test:** "Unbilled Services" in receivables section should go to Row 206, NOT Row 223
3. **INPL-003 test:** "Consultancy Charges" should go to Row 49 (Others Mfg), NOT Row 71 (Others Admin)
4. **INPL-005 test:** "Material Handling Charges" should go to Row 49, NOT Row 47 (Freight)
5. **INPL-007 test:** "Ideal Energy Transmission LLP" loan should be flagged for CA judgment on Row 137 vs 153
6. **INPL-012 test:** "Directors Remuneration" should go to Row 73, NOT Row 67
7. **Unit change test:** FY25 report numbers should be ÷100 for Crores (Lakhs scale), not ÷10,000 (thousands scale)

Use the `classification_method` column in output to confirm which rule fired for each item.
