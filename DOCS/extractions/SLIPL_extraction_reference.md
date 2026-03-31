# SLIPL Extraction Reference
**Company:** Suolificio Linea Italia (India) Private Limited (SLIPL)
**Industry:** Footwear / Shoe Sole Manufacturing
**Locations:** Sedarapet, Pondicherry (factory) + Agra (branch operations)
**Financial Years Covered:** FY2021-22, FY2022-23, FY2023-24, FY2024-25
**Amounts:** CMA amounts in **Lakhs (₹)**; Audit amounts in **₹'000** unless noted

---

## Source Files

| # | File | Format | Coverage | Key Use |
|---|------|---------|----------|---------|
| 1 | `SLI AUDITED FINANCIALS FY 22-23.pdf` | PDF (24 pages) | FY23 + FY22 comparative | Notes 1-18, BS, P&L |
| 2 | `SLI Audit Reports & Balance Sheet as on 31.03.2024.pdf` | PDF (23 pages) | FY24 + FY23 comparative | Notes 19-27, most complete P&L breakdown |
| 3 | `Signed BS 24-25.pdf` | PDF (25 pages) | FY25 + FY24 comparative | FY25 BS + P&L (partially OCR-unclear) |
| 4 | `FINAL BS SLI - 24-25.xlsx` | Excel (multi-sheet) | FY25 (primary) | Cleanest FY25 data; Trial Balance; detailed notes |
| 5 | `SLI CMA 31102025.xls` | Excel (INPUT In Lakhs) | FY22–FY25 | **Ground truth** — CA's actual CMA row mappings |

**Extraction methodology:** PDFs extracted via `pdfplumber` (Python); Excel files via `openpyxl` (xlsx) and `xlrd` (xls). Ground-truth amounts taken from `SLI CMA 31102025.xls` Sheet "INPUT In Lakhs" which was prepared by the CA and is authoritative.

---

## Auditor Qualified Opinions (FY22–FY25)

All four years carry **qualified opinions**:
- Bad debt provisioning not done on debtors >3 years (amounts not quantified in report)
- Employee benefit provisioning (gratuity, leave encashment) not done as required under Ind AS 19
- Impact on profit/reserves is not ascertainable from the reports

This is relevant for CMA Row 69 (Bad Debts) — currently nil in all years — and Row 255 (Gratuity liability not provided for).

---

## INCOME STATEMENT (P&L) — CMA Mapping

### Section: Revenue from Operations

| Line Item (as in accounts) | Source | FY22 | FY23 | FY24 | FY25 | CMA Row |
|---|---|---|---|---|---|---|
| Sale of Products — Domestic | Note 19, FY24 PDF | — | 3,786.18 | 4,321.52 | ~2,821 | 22 |
| Sale of Products — Export (FOB) | Note 19, FY24 PDF | — | 566.15 | 639.53 | 194.86 | 23 (part) |
| Service Charges (processing income) | Note 19, FY24 PDF | — | — | 2.37 | — | 22 (included) |
| **Duty Drawback** | Other Income note | — | 27.35 | 27.35 | 31.64 | **23 (added to exports)** |
| Export IGST / Incentive | FY25 P&L | — | — | — | ~31.64 | 23 |
| Interest Received | Other Income | small | small | small | small | 30 |
| **CMA Row 22 (Domestic Sales)** | Ground truth | — | 3,786.18 | 4,463.34 | ~2,961 | 22 |
| **CMA Row 23 (Export Sales)** | Ground truth | — | 593.50 | 666.88 | 226.50 | 23 |

**Key finding:** Duty Drawback (export incentive received from Customs) is **added to Export Sales (Row 23)**, not classified as Other Income (Row 34). Verified:
- FY24: FOB 639.53 + Duty Drawback 27.35 = **666.88** ✓ (matches CMA Row 23)
- FY25: FOB 194.86 + Drawback/IGST 31.64 = **226.50** ✓ (matches CMA Row 23)
- Service Charges 2.37 included in Domestic Sales Row 22: 4,321.52 + 139.45 (other) + 2.37 = 4,463.34 ✓

---

### Section: Cost of Materials / Raw Materials

| Line Item | Source | FY23 | FY24 | FY25 | CMA Row |
|---|---|---|---|---|---|
| EVA Materials | Note 21, FY24 PDF | — | large portion | — | 42 |
| PU Materials | Note 21, FY24 PDF | — | portion | — | 42 |
| Other Raw Materials (rubber, chemicals) | Note 21, FY24 PDF | — | portion | — | 42 |
| Components and Accessories | Note 21 | — | portion | — | 42 |
| **CMA Row 42 (Raw Materials Indigenous)** | Ground truth | ~2,884 | 3,432.51 | — | 42 |
| Imported raw materials (if any) | Audit notes | — | nil/small | — | 41 |

**Note:** SLIPL is predominantly an indigenous raw material user. Import content is disclosed separately in Note 26 (FY24 Audit) — verify if non-zero amounts need Row 41.

---

### Section: Changes in Inventories

| Line Item | Source | FY23 | FY24 | FY25 | CMA Row |
|---|---|---|---|---|---|
| Opening WIP (Stock-in-process) | P&L Note | prior yr close | prior yr close | — | 53 |
| Closing WIP (Stock-in-process) | P&L Note | current yr | current yr | — | 54 |
| Opening Finished Goods | P&L Note | prior yr close | prior yr close | — | 58 |
| Closing Finished Goods | P&L Note | current yr | current yr | — | 59 |

---

### Section: Employee Benefits Expense

| Line Item | Source | FY23 | FY24 | FY25 | CMA Row |
|---|---|---|---|---|---|
| Salaries & Wages (workers + staff) | Note 23, FY24 PDF | — | large portion | — | 45 |
| Bonus | Note 23 | — | portion | — | 45 |
| EPF/ESI contributions | Note 23 | — | portion | — | 45 |
| Gratuity (provision) | Note 23 | — | portion | — | 45 |
| **KMP Remuneration (Directors)** | Note 27 (Related Party) | — | 41.24 | — | **45** |
| **CMA Row 45 (Wages — ALL employee costs)** | Ground truth | ~620 | 773.22 | — | 45 |
| **CMA Row 67 (Salary and Staff Expenses)** | Ground truth | 0 | 0 | 0 | 67 |

**Key finding:** ALL employee costs including KMP/Director remuneration go to **Row 45 (Wages)**, not Row 67. Row 67 is zero across all years. This **conflicts with BCIPL-001** which sends Director Remuneration to Row 67.

---

### Section: Manufacturing Expenses

| Line Item | Source | FY23 | FY24 | FY25 | CMA Row |
|---|---|---|---|---|---|
| Power and Fuel (Electricity) | Note 25, FY24 PDF | — | ~xxx | — | 48 |
| **Factory Rent (to Chemcrown Exports)** | Note 25 + Related Party | — | 38.42 | — | **49** |
| **Packing Materials** | Note 25 | — | 72.04 | — | **49** |
| **Moulds (consumable/periodic replacement)** | Note 25 | — | 4.53 | — | **49** |
| **Royalty (Italian design/mould royalty)** | Note 25 | — | 9.96 | — | **49** |
| **CMA Row 49 (Others Manufacturing)** | Ground truth | — | 124.95 | — | 49 |

Verified: 38.42 (rent) + 72.04 (packing) + 4.53 (moulds) + 9.96 (royalty) = **124.95** ✓

| Line Item | Source | FY23 | FY24 | FY25 | CMA Row |
|---|---|---|---|---|---|
| Stitching Charges / Job Work Paid | Note 25 or P&L | — | — | — | 46 |
| Carriage Inward | Note 25 | — | — | — | 47 |
| Carriage Outward / Freight | Note 25 | — | — | — | 47 |

---

### Section: Repairs & Maintenance

| Line Item | Source | FY24 | CMA Row |
|---|---|---|---|
| Repairs — Buildings | Note 25, FY24 PDF | 8.55 | 72 |
| Repairs — Plant & Machinery | Note 25 | 27.30 | 72 |
| Repairs — Others | Note 25 | 8.14 | 72 |
| **CMA Row 72 (R&M Admin — ALL repairs)** | Ground truth | **43.99** | 72 |
| **CMA Row 50 (R&M Manufacturing)** | Ground truth | **0** | 50 |

Verified: 8.55 + 27.30 + 8.14 = **43.99** ✓. All repairs (including P&M repairs) go to Row 72. Row 50 is unused.

---

### Section: Selling & Distribution / Admin Expenses

| Line Item | Source | FY24 | CMA Row |
|---|---|---|---|
| Professional / Consultancy Fees | Note 25 | — | 71 |
| Travelling & Conveyance | Note 25 | — | 71 |
| Office Expenses / Stationery | Note 25 | — | 71 |
| Advertisement | Note 25 | small | 70 |
| Bad Debts | Note 25 | 0 | 69 |
| Rent (office, non-factory) | Note 25 | — | 68 |
| Audit Fees / Statutory Audit | Note 25 | — | 73 |
| Miscellaneous Expenses | Note 25 | — | 71 |

---

### Section: Finance Costs

| Line Item | Source | FY24 | CMA Row |
|---|---|---|---|
| Interest on Term Loans (Banks) | Note 24, FY24 PDF | — | 83 |
| Interest on Unsecured Loans (Directors) | Note 24 | — | 83 |
| Bank Charges / Processing Fees | Note 24 | — | 85 |
| **CMA Row 83 (Interest on Fixed/Term Loans)** | Ground truth | — | 83 |
| **CMA Row 84 (Interest on WC Loans)** | Ground truth | — | 84 |

**Note:** SLIPL uses term loans (not CC/OD), so Row 83 is primary finance cost. Verify if any CC facility exists that would populate Row 84.

---

### Section: Depreciation

| Line Item | Source | FY24 | CMA Row |
|---|---|---|---|
| Depreciation on all fixed assets | P&L / Note | — | 63 |

---

## BALANCE SHEET — CMA Mapping

### Equity & Reserves

| Line Item | FY22 | FY23 | FY24 | FY25 | CMA Row |
|---|---|---|---|---|---|
| Issued, Subscribed & Paid-up Capital | 10.00 | 10.00 | 10.00 | 10.00 | 116 |
| Retained Earnings / P&L balance | — | — | — | — | 122 |

---

### Borrowings — Long Term

| Line Item | Source | FY24 | FY25 | CMA Row |
|---|---|---|---|---|
| Term Loan — Banks (current portion) | BS Note | — | — | 136 |
| Term Loan — Banks (LT portion >1yr) | BS Note | — | — | 137 |
| **Unsecured Loan — Manoj Kumar Bhaiya (Director)** | BS + Trial Balance | 594.81 | ~613.01* | **152** |
| **Unsecured Loan — Swati Bhaiya** | BS | — | 0 | 152 |
| **Payable to Suolificio Nuova Linea SRL (Italy)** | BS Note | — | — | **153** |
| **Payable to Suolificio Squadroni SRL (Italy)** | BS Note | — | — | **153** |

*FY25 Trial Balance: Manoj Kumar Bhaiya Loan = ₹4,30,51,579 + Agra Loan ₹1,82,50,000 = ₹6,13,01,579 = **613.02L** → Row 152

**Key finding:** Italian parent payables under supply agreements → **Row 153** (not trade creditors Row 242). KMP/Director unsecured loans → **Row 152** (Quasi Equity).

---

### Fixed Assets

| Asset Class | Source | FY25 Gross Block | CMA Row |
|---|---|---|---|
| Moulds (shoe manufacturing dies) | Trial Balance / Note | Large — largest asset class | **162** |
| Plant & Machinery | Trial Balance | significant | 162 |
| Buildings (factory, Pondy + Agra) | Trial Balance | significant | 162 |
| Electrical Installations | Trial Balance | — | 162 |
| Furniture & Fixtures | Trial Balance | — | 162 |
| Computers | Trial Balance | — | 162 |
| Vehicles (car/two-wheeler) | Trial Balance | — | 162 |
| Less: Accumulated Depreciation | BS | — | 163 |
| **Moulds — WIP** (under fabrication) | Trial Balance | **317.99L** | **165** |

**Key finding:** Moulds are capitalized as fixed assets (Row 162), not expensed. Moulds WIP → Row 165 (Capital Work in Progress).

---

### Non-Current Assets

| Line Item | Source | FY24 | FY25 | CMA Row |
|---|---|---|---|---|
| Deferred Tax Asset | BS | — | — | 171 |
| **Security Deposit — Chemcrown Exports** | BS Notes | — | — | **238** |
| **Security Deposit — Others** | BS Notes | — | — | **238** |
| **CMA Row 237 (Govt security deposits)** | Ground truth | **0** | **0** | 237 |
| **CMA Row 238 (Other non-current assets)** | Ground truth | has value | has value | 238 |

**Key finding:** ALL security deposits go to **Row 238**, not Row 237. Row 237 (Security deposits with government departments) is **zero** in SLIPL's CMA. This conflicts with V1 Rule C-004.

---

### Inventories (Current Assets)

| Item | Source | FY24 | CMA Row |
|---|---|---|---|
| Raw Materials | BS / Note | — | 194 |
| Work-in-Progress (WIP) | BS / Note | — | 200 |
| Finished Goods | BS / Note | — | 201 |
| Stores & Spares (Indigenous) | BS / Note | — | 198 |
| Packing Materials (inventory) | BS / Note | — | 198 |

---

### Trade Receivables (Current Assets)

| Item | Source | CMA Row |
|---|---|---|
| Domestic Debtors (≤ 6 months) | BS | 206 |
| Export Receivables | BS | 207 |
| Debtors > 6 months | BS | 208 |

**Note:** Auditor qualification covers debtors >3 years — provisioning not done.

---

### Cash & Bank

| Item | CMA Row |
|---|---|
| Cash on Hand | 212 |
| Bank Balances (current accounts) | 213 |
| Fixed Deposits under lien (bank security) | 214 |
| Other Fixed Deposits | 215 |

---

### Other Current Assets / Advances

| Item | Source | CMA Row |
|---|---|---|
| Advance Income Tax / TDS Receivable | BS | 221 |
| Prepaid Expenses | BS | 222 |
| Other Advances | BS | 223 |
| GST Input Credit / IGST Receivable | BS | 223 |

---

### Current Liabilities

| Line Item | Source | CMA Row |
|---|---|---|
| Working Capital Bank Finance (CC/OD) | BS — if any | 131 |
| Sundry Creditors for Goods | BS | 242 |
| **Italian parent payables (if classified as current)** | BS | 242 or 153 |
| Advance from Customers | BS | 243 |
| Statutory Liabilities (EPF, ESI, TDS payable) | BS + Trial Balance | 246 |
| Provision for Income Tax | BS | 244 |
| Interest Accrued but not due | BS | 247 or 248 |
| Creditors for Expenses | BS | 249 |
| Bonus Provision | BS | 249 |
| Gratuity Provision (if provided) | BS | 249 |

---

## Key Related Party Relationships (FY24)

| Party | Relationship | Transaction type | CMA Impact |
|---|---|---|---|
| Suolificio Nuova Linea SRL (Italy) | Italian parent company | Raw material supply + amount payable | Row 153 (if structured LT payable) |
| Suolificio Squadroni SRL (Italy) | Italian group company | Mould supply + payables | Row 153 |
| Matrix Stampi (Italy) | Related party | Mould dies supply | Row 162 when capitalized |
| Chemcrown Exports Pvt Ltd | Factory landlord | Factory premises lease (rent) | Row 49 (manufacturing rent) |
| Manoj Kumar Bhaiya | Director / KMP | Unsecured loan + remuneration | Row 152 (loan), Row 45 (remuneration) |
| Swati Bhaiya | KMP relative / Director | Unsecured loan | Row 152 |

---

## Data Quality Notes

1. **FY25 amounts**: Best from `FINAL BS SLI - 24-25.xlsx` (exact figures). PDF (Signed BS 24-25) has some OCR ambiguity on detailed notes.
2. **FY22 amounts**: Available as comparative columns in FY23 audit — less detail on note-level breakdown.
3. **Duty Drawback**: Appears in "Other Income" section of P&L in audit, but CA reclassifies to Row 23. AI classifier must not simply follow the P&L line placement.
4. **Mould expenses**: Small annual mould replacement cost (₹4.53L FY24) expensed to Row 49; larger mould sets capitalized to Row 162 / Row 165.
5. **Qualified opinion items**: Bad Debts (Row 69) = 0 across all years despite auditor's qualification — CA has chosen not to provide. Gratuity provision (Row 255) may be understated.
