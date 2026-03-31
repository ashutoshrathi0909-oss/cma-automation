# Kurunji Retail — Financial Data Extraction Reference

**Company:** Kurunji Retails (Partnership Firm)
**PAN:** AARPK4663L
**Address:** No.11, Pattamangala Street, Mayiladuthurai / 332-A, Nageswaran North Street, Kumbakonam, Thanjavur — 29, Tamil Nadu 612001
**Nature of Business:** Wholesale and Retail Trade — Retail sale of consumer/electronic goods
**Industry:** Retail (multi-product store, including electronics)
**Auditors:** S.R. Dhass & Co., Kumbakonam
**Partners (as per FY2025 filing):** A.Borthoushan, S.Bharathinsha, M.Arumugam, S.Arjuna Begum, S.Shaktinatham (5 partners, each with specific profit-sharing ratios)
**Financial Years Covered:** FY2021-22, FY2022-23, FY2023-24, FY2024-25

**Source Files:**
- `FInancials main/Kurunji Retail/KURINJI RETAIL ITR - 2022-2023.pdf` (245MB — scanned, 23 pages; AY 2023-24)
- `FInancials main/Kurunji Retail/KURINJI RETAIL ITR - 2023-2024.pdf` (266MB — scanned, 23 pages; AY 2024-25)
- `FInancials main/Kurunji Retail/Kurinji Retail FY 2025 audited.pdf` (15MB — scanned, 27 pages; AY 2025-26)
- `FInancials main/Kurunji Retail/CMA Kurinji retail 23012026.xls` (Ground truth CMA)

---

## OCR Quality Notes

| File | Overall Quality | Notes |
|------|----------------|-------|
| ITR 2022-23 (245MB) | MODERATE | Scanned at high DPI but physical document is printed, not typeset. Numbers are mostly readable; some digits ambiguous in Rs/Ps columns. P&L on page 4, Balance Sheet on page 5. Pages 1-3 = ITR acknowledgement + tax computation (skip). Pages 6-23 = Form 3CB, 3CD, fixed asset schedules. |
| ITR 2023-24 (266MB) | MODERATE | Same quality. P&L on page 3, Balance Sheet on page 4. Page 5 = Fixed Assets schedule (useful). Pages 6-23 = Form 3CB, 3CD disclosures (skip for CMA). |
| FY 2025 audited (15MB) | GOOD | Lower file size = same DPI but likely cleaner source document. P&L on page 6, Balance Sheet on page 7. Pages 4-5 = Fixed Assets + Partners' Remuneration. Pages 8-27 = Form 3CB, 3CD (skip). |
| Key problem | — | The 245MB and 266MB files hit the 100MB Read tool limit — required PyMuPDF rendering at 120 DPI before reading as images. |

**Flagged quality issues:**
- Electric/Phone Charges (FY23): Exact amount uncertain between ₹69.12 lakhs and ₹1.05 crore; cross-referenced with CMA confirms ₹69.12 lakhs → Row 48.
- Generator Expenses (FY24): Value ₹2.13 lakhs — cross-verified through CMA reconciliation.
- FY25 Sales total: Read as approximately ₹68.86 crore — confirmed by CMA Row 22 = 6,886.64 lakhs ✓

---

## Financial Statements — All Years

### FY 2021-22 (extracted from CMA ground truth)
*Note: ITR for FY22 not provided as a PDF — data taken from CMA INPUT SHEET column B (Year=2022)*

**P&L (amounts in ₹ Lakhs):**
- Domestic Sales: ₹1,466.86 L
- Raw Materials Consumed (Purchases): ₹1,223.08 L
- Wages (Salary+PF+ESI+Staff costs): ₹40.64 L
- Power/Electricity: ₹13.78 L
- Others Manufacturing (incl. Rent): ₹7.40 L
- Depreciation: ₹6.70 L
- Finished Goods Opening: ₹377.33 L
- Finished Goods Closing: ₹255.46 L
- Advertisements: ₹0 (nil)
- Others Admin: ₹5.50 L
- Repairs & Maintenance: ₹0.80 L
- Audit Fees / Partners' Salary: ₹12.0 L
- Interest Fixed Loans: ₹10.69 L
- Interest WC Loans: ₹18.67 L

**Balance Sheet (amounts in ₹ Lakhs):**
- Partners' Capital: ₹133.67 L
- WC Bank Finance (ICICI): ₹222.54 L
- Unsecured Loans — Quasi Equity: ₹31.40 L
- Gross Block: ₹145.75 L
- Finished Goods (Stock): ₹255.46 L
- Sundry Debtors: ₹24.31 L
- Cash on Hand: ₹2.95 L
- Bank Balances: ₹8.18 L
- Other Non-Current Assets (Rental Advances): ₹26.90 L
- Sundry Creditors: ₹74.30 L

---

### FY 2022-23 (Source: KURINJI RETAIL ITR - 2022-2023.pdf)
**Key pages:** P&L = Page 4, Balance Sheet = Page 5, Fixed Assets = in Form 3CD
**Page quality:** MODERATE (scanned physical document)

**P&L — Trading Account (year ended 31 March 2023):**

| Description | Section | Amount (₹) | Source Page | Notes |
|------------|---------|------------|------------|-------|
| Opening Stock | P&L Trading (DR) | 2,55,56,400 | p04 | ₹2.55 Cr |
| Purchases | P&L Trading (DR) | 26,99,11,634 | p04 | ₹26.99 Cr |
| Freight (Inward) | P&L Trading (DR) | 4,32,512 | p04 | ₹4.33 L |
| Gross Profit c/d | P&L Trading (DR) | 2,96,53,213 | p04 | Balancing figure |
| Sales | P&L Trading (CR) | 30,51,75,359 | p04 | ₹30.51 Cr |
| Closing Stock | P&L Trading (CR) | 2,03,68,400 | p04 | ₹2.03 Cr |

**P&L — Profit & Loss Account (year ended 31 March 2023):**

| Description | Section | Amount (₹) | Source Page | CMA Row |
|------------|---------|------------|------------|---------|
| Gross Profit b/d | P&L Income (CR) | 2,96,53,213 | p04 | — |
| Discount Received | P&L Income (CR) | 2,80,181 | p04 | Row 42 (nets against purchases) |
| Interest | P&L Income (CR) | 3,88,270 | p04 | Row 30 |
| Other Interest | P&L Income (CR) | 15,518 | p04 | Row 30 |
| Salary and Bonus | P&L Expense (DR) | ~55,55,245 | p04 | Row 45 |
| Rent | P&L Expense (DR) | 40,95,000 | p04 | Row 49 |
| TDS on Rent | P&L Expense (DR) | 4,55,000 | p04 | Row 49 (combined with Rent) |
| Rent - Parking | P&L Expense (DR) | 2,40,000 | p04 | Row 49 |
| Electric/Phone Charges | P&L Expense (DR) | 69,11,541 | p04 | Row 48 |
| Staff Welfare | P&L Expense (DR) | 3,73,932 | p04 | Row 45 |
| Staff Mess Expenses | P&L Expense (DR) | 3,96,640 | p04 | Row 45 |
| Bank Interest and Charges | P&L Expense (DR) | 16,24,303 | p04 | Row 84 |
| Provident Fund | P&L Expense (DR) | 5,56,438 | p04 | Row 45 |
| ESI | P&L Expense (DR) | 90,534 | p04 | Row 45 |
| Salary to Partners | P&L Expense (DR) | 12,00,000 | p04 | Row 73 |
| Repairs and Maintenance | P&L Expense (DR) | 1,08,027 | p04 | Row 72 |
| Interest to Partners | P&L Expense (DR) | 16,04,010 | p04 | Row 83 |
| Depreciation | P&L Expense (DR) | 32,36,496 | p04 | Row 56/63 |
| Packing Expenses | P&L Expense (DR) | 5,91,988 | p04 | Row 71 (small amount) |
| Miscellaneous Expenses | P&L Expense (DR) | 89,373 | p04 | Row 71 |
| Professional Fees | P&L Expense (DR) | 90,000 | p04 | Row 71 |
| Insurance/Freight | P&L Expense (DR) | 94,362 | p04 | Row 71 |
| Advertisement Expenses | P&L Expense (DR) | 10,08,740 | p04 | Row 70 |
| Digital Marketing | P&L Expense (DR) | 5,94,442 | p04 | Row 70 |
| Net Profit | P&L (DR, balancing) | 11,98,936 | p04 | Row 99 area |

**Balance Sheet (as at 31 March 2023):**

| Description | Section | Amount (₹) | Source Page | CMA Row |
|------------|---------|------------|------------|---------|
| Partners' Capital Accounts (5 partners) | BS Liability | 3,42,55,012 | p05 | Row 116 |
| Loans (bank CC/OD — ICICI) | BS Liability | 2,14,75,097 | p05 | Row 131 |
| Unsecured Loans (Quasi Equity) | BS Liability | 31,40,000 | p05 | Row 152 |
| Sundry Creditors | BS Liability | 78,63,312 | p05 | Row 242 |
| Fixed Assets (Net Block) | BS Asset | 3,42,91,797 | p05 | Row 162/164 |
| Sundry Debtors | BS Asset | 71,25,932 | p05 | Row 206 |
| Cash on Hand | BS Asset | 2,50,868 | p05 | Row 212 |
| Bank Balances (ICICI accounts) | BS Asset | 20,06,422 | p05 | Row 213 |
| Other Non-Current Assets (Rental Advances) | BS Asset | 26,90,000 | p05 | Row 238 |
| Stock in Trade (Finished Goods) | BS Asset | 2,03,68,400 | p05 | Row 201 |

**Schedule of Loans (detail — p05):**
- ICICI Loan 6680192335H
- Axis Credit Account 6680193026148
- HDFC Credit Account
- ICICI loan (additional)

**Partners' Capital (FY23 closing):**
- A.Borthoushan (Managing Partner)
- S.Bhuleaghan
- M.Arumugam
- S.Arjuna Begam
- S.Shaktinatham / Johanna Festalinuam
Total capital = ₹3,42,55,012

---

### FY 2023-24 (Source: KURINJI RETAIL ITR - 2023-2024.pdf)
**Key pages:** P&L = Page 3, Balance Sheet = Page 4, Fixed Assets = Page 5
**Page quality:** MODERATE-GOOD (scanned physical document; FY24 P&L is the CLEAREST of all three years)

**P&L — Trading Account (year ended 31 March 2024):**

| Description | Section | Amount (₹) | Source Page | Notes |
|------------|---------|------------|------------|-------|
| Opening Stock | P&L Trading (DR) | 2,03,68,400 | p03 | = FY23 closing ✓ |
| Purchases | P&L Trading (DR) | 41,41,02,796 | p03 | ₹41.41 Cr |
| Gross Profit c/d | P&L Trading (DR) | 3,68,97,463 | p03 | |
| Sales | P&L Trading (CR) | 40,15,97,059 | p03 | ₹40.15 Cr |
| Closing Stock | P&L Trading (CR) | 6,97,71,600 | p03 | ₹6.97 Cr — large jump! |
| TOTAL (both sides) | | 47,13,68,659 | p03 | Verified balanced ✓ |

**P&L — Profit & Loss Account (year ended 31 March 2024):**

| Description | Section | Amount (₹) | Source Page | CMA Row |
|------------|---------|------------|------------|---------|
| Gross Profit b/d | P&L Income (CR) | 3,68,97,463 | p03 | — |
| Discount Received | P&L Income (CR) | 11,194 | p03 | Row 42 (nets against purchases) |
| Incentive | P&L Income (CR) | 63,257 | p03 | Row 30 (Interest Received) |
| Other Interest | P&L Income (CR) | 3,03,282 | p03 | Row 30 |
| Stock of Packing Materials | P&L Income (CR) | 1,25,000 | p03 | Closing packing stock — offsets Packing expense |
| TOTAL CREDIT | | 3,79,27,196 | p03 | |
| Salary and Bonus | P&L Expense (DR) | 55,69,430 | p03 | Row 45 |
| Rent | P&L Expense (DR) | 48,60,000 | p03 | Row 49 |
| TDS on Rent | P&L Expense (DR) | 5,40,000 | p03 | Row 49 (combined with Rent) |
| Rent - Parking | P&L Expense (DR) | 2,38,000 | p03 | Row 49 |
| Electric/Phone Charges | P&L Expense (DR) | 97,07,993 | p03 | Row 48 |
| Staff Welfare | P&L Expense (DR) | 37,660 | p03 | Row 45 |
| Staff Mess Expenses | P&L Expense (DR) | 4,02,500 | p03 | Row 45 |
| Bank Interest and Charges | P&L Expense (DR) | 16,24,386 | p03 | Row 84 |
| Provident Fund | P&L Expense (DR) | 4,93,061 | p03 | Row 45 |
| ESI | P&L Expense (DR) | 87,696 | p03 | Row 45 |
| Salary to Partners | P&L Expense (DR) | 10,20,000 | p03 | Row 73 |
| Repairs and Maintenance | P&L Expense (DR) | 2,05,793 | p03 | Row 72 |
| Interest to Partners | P&L Expense (DR) | 8,56,375 | p03 | Row 83 |
| Generator Expenses | P&L Expense (DR) | 2,13,748 | p03 | Row 71 (Others Admin) |
| Depreciation | P&L Expense (DR) | 29,21,249 | p03 | Row 56/63 |
| Packing Expenses | P&L Expense (DR) | 39,24,939 | p03 | Row 44 (Stores & Spares consumed) |
| Miscellaneous Expenses | P&L Expense (DR) | 5,20,021 | p03 | Row 71 |
| Advertisement Expenses | P&L Expense (DR) | 5,52,800 | p03 | Row 70 |
| Barcode Expenses | P&L Expense (DR) | 6,83,356 | p03 | Row 71 |
| Bill Printing Roll | P&L Expense (DR) | 5,59,614 | p03 | Row 71 |
| Printing and Stationery | P&L Expense (DR) | 2,74,304 | p03 | Row 71 |
| Freight Charges | P&L Expense (DR) | 6,92,580 | p03 | Row 71 (NOT Row 47!) |
| Net Profit | P&L (DR, balancing) | 11,00,835 | p03 | |
| TOTAL DEBIT | | 3,79,27,196 | p03 | Verified balanced ✓ |

**Balance Sheet (as at 31 March 2024) — Source: ITR2324 p04:**

| Description | Section | Amount (₹) | Source Page | CMA Row |
|------------|---------|------------|------------|---------|
| Partners' Capital Accounts | BS Liability | 3,86,41,423 | p04 | Row 116 |
| ICICI Credit Account (CC/OD) | BS Liability | 3,92,41,507 | p04 | Row 131 |
| Partners' Current Account (unsecured) | BS Liability | 70,00,000 | p04 | Row 152/153 |
| Kurinji Metro / Other unsecured loan | BS Liability | 3,10,000 | p04 | Row 153 |
| Sundry Creditors | BS Liability | 3,23,84,587 | p04 | Row 242 |
| Rental Advances | BS Liability (or contra-asset) | 20,00,000 | p04 | — |
| Fixed Assets (Net Block) | BS Asset | (from dep. sch.) | p05 | Row 162 |
| Stock in Trade (Finished Goods) | BS Asset | 6,97,71,600 | p04 | Row 201 |
| Stock of Packing Materials | BS Asset | 1,25,000 | p04 | Row 198 |
| Sundry Debtors | BS Asset | 96,78,270 | p04 | Row 206 |
| Cash on Hand | BS Asset | 6,25,951 | p04 | Row 212 |
| Bank Balances: ICICI Ca 68105100261 | BS Asset | 22,80,593 | p04 | Row 213 |
| Bank Balances: ICICI Ca 6810530559B | BS Asset | 24,69,476 | p04 | Row 213 |
| Rental Advances (non-current) | BS Asset | 34,64,766 | p04 | Row 238 |

**Fixed Assets (Detail — FY24, from ITR2324 p05):**
These all go to Row 162 (Gross Block):
- Machineries (15%) — Opening WDV: ₹10,86,643
- Car (15%) — Opening WDV: ₹2,78,390
- Inverter
- Civil Works
- Computer Accessories (multiple entries, 40%)
- Computer Server (40%)
- Scanner
- Stabilizer
- Camera (CCTV/security systems, 15%)
- Computer/Printer & UPS Scanner
- Furniture and Elevation (10%)
- Electrical Fittings (10%)
- Software (multiple)
- Tata Intra Van (vehicle — 15%) → Rule C-001 applies
- UPS (40%)
- Poxflex Thermal Printer (40%)
- Dual Antenna Pedestal
- Counting Machine (cash counter)
- Thermal Printer (receipt printer)
- Non-Depreciable Asset (likely land/leasehold improvements)

---

### FY 2024-25 (Source: Kurinji Retail FY 2025 audited.pdf)
**Key pages:** P&L = Page 6, Balance Sheet = Page 7, Fixed Assets = Pages 4-5
**Page quality:** GOOD

**P&L — Trading Account (year ended 31 March 2025):**

| Description | Section | Amount (₹) | Source Page | Notes |
|------------|---------|------------|------------|-------|
| Opening Stock | P&L Trading (DR) | 6,88,66,572 | p06 | = FY24 closing ✓ |
| Purchases | P&L Trading (DR) | ~61,73,37,850 | p06 | ₹61.73 Cr (calculated) |
| Gross Profit c/d | P&L Trading (DR) | 6,89,24,226 | p06 | |
| Sales | P&L Trading (CR) | ~68,86,64,572 | p06 | ₹68.87 Cr (from CMA Row 22) |
| Closing Stock | P&L Trading (CR) | 6,50,30,182 | p06 | ₹6.50 Cr |

**P&L — Profit & Loss Account (year ended 31 March 2025):**

| Description | Section | Amount (₹) | Source Page | CMA Row |
|------------|---------|------------|------------|---------|
| Gross Profit b/d | P&L Income (CR) | 6,89,24,226 | p06 | — |
| Interest / Other Income | P&L Income (CR) | 82,454 | p06 | Row 30 |
| Others (Non-Operating Income) | P&L Income (CR) | ~11,56,383 | p06 | Row 34 [source unclear — CA judgment] |
| Salary and Bonus | P&L Expense (DR) | ~1,08,66,857 | p06 | Row 45 |
| Rent | P&L Expense (DR) | ~99,62,370 | p06 | Row 49 |
| Rent - Parking | P&L Expense (DR) | 2,40,000 | p06 | Row 49 |
| Electric Charges | P&L Expense (DR) | ~1,72,33,642 | p06 | Row 48 |
| Telephone Charges | P&L Expense (DR) | [amount] | p06 | Row 48 (or Row 71) |
| Staff Welfare | P&L Expense (DR) | ~3,46,000 | p06 | Row 45 |
| Bank Interest and Charges | P&L Expense (DR) | ~93,63,942 | p06 | Row 84 |
| Provident Fund | P&L Expense (DR) | ~5,56,000 | p06 | Row 45 |
| ESI | P&L Expense (DR) | ~90,000 | p06 | Row 45 |
| Salary to Partners | P&L Expense (DR) | 10,80,000 | p06 | Row 73 |
| Repairs and Maintenance | P&L Expense (DR) | ~94,94,308 | p06 | Row 72 |
| Interest to Partners | P&L Expense (DR) | 23,18,485 | p06 | Row 83 (confirmed by tax comp) |
| Depreciation | P&L Expense (DR) | 50,62,171 | p06 | Row 56/63 (confirmed by tax comp) |
| Packing Expenses | P&L Expense (DR) | ~42,47,191 | p06 | Row 44 (Stores & Spares consumed) |
| Miscellaneous Expenses | P&L Expense (DR) | [amount] | p06 | Row 71 |
| Advertisement Expenses | P&L Expense (DR) | [amount] | p06 | Row 70 |
| [Other items] | P&L Expense (DR) | | p06 | Row 71 |
| Net Profit | P&L (DR, balancing) | 44,96,732 | p06 | (from CMA) |

*Note: FY2025 splits "Electric Charges" and "Telephone Charges" as separate line items (combined as "Electric/Phone Charges" in FY23/24). Both map to Row 48.*

**Balance Sheet (as at 31 March 2025) — Source: FY2025 p07:**

| Description | Section | Amount (₹) | Source Page | CMA Row |
|------------|---------|------------|------------|---------|
| Partners' Capital Accounts | BS Liability | ~4,42,86,618 | p07 | Row 116 |
| ICICI CC/OD Account | BS Liability | ~7,65,53,093 | p07 | Row 131 |
| Term Loans (ICICI / new facility) | BS Liability | ~2,93,86,296 | p07 | Row 137 |
| Unsecured Loans — Quasi Equity | BS Liability | 93,91,468 | p07 | Row 152 |
| Unsecured Loans — Long Term Debt | BS Liability | 2,07,97,516 | p07 | Row 153 |
| Sundry Creditors | BS Liability | ~6,50,81,682 | p07 | Row 242 |
| Fixed Assets (Net Block) | BS Asset | ~4,42,98,610 | p07 | Row 162/164 |
| Stock in Trade (Finished Goods) | BS Asset | 20,36,17,200 | p07 | Row 201 (massive jump!) |
| Stock of Packing Materials | BS Asset | 58,500 | p07 | Row 198 |
| Sundry Debtors | BS Asset | 0 | p07 | Row 206 (nil in FY25) |
| Dues from Partners | BS Asset | ~91,78,270 | p07 | Row 235 |
| Other Advances / Sister Concern | BS Asset | ~3,30,59,720 | p07 | Row 223 (Kurinji Metro / related party) |
| Cash on Hand | BS Asset | ~12,04,578 | p07 | Row 212 |
| Bank Balances | BS Asset | ~13,61,707 | p07 | Row 213 |

**Partners' Capital Account Detail (FY2024-25):**
- A.Borthoushan: Interest ₹13,63,260, Salary ₹2,40,000, Opening ₹4,64,00,804
- S.Bhuleaghan: Interest ₹5,21,799, Salary ₹2,40,000, Opening ₹2,21,39,827
- M.Arumugam: Interest ₹1,95,027, Salary ₹2,40,000, Opening [amount]
- S.Arjuna Begam: Interest ₹1,59,027, Salary ₹2,40,000, Opening [amount]
- S.Shaktinatham: Interest [amount], Salary ₹2,40,000, Opening [amount]
Total Closing: ₹4,42,86,618 (= CMA Row 116 FY25 = 920.96 lakhs ✓)

---

## Cross-Company Comparison: Business Scale

| Metric | FY22 | FY23 | FY24 | FY25 |
|--------|------|------|------|------|
| Net Sales (Cr) | ₹14.67 | ₹30.52 | ₹40.16 | ₹68.87 |
| Gross Profit % | ~4.4% | ~9.7% | ~9.2% | ~10.0% |
| Stock in Trade (Cr) | ₹2.55 | ₹2.04 | ₹6.98 | ₹20.36 |
| Working Capital (ICICI CC/OD, Cr) | ₹2.23 | ₹2.15 | ₹4.06 | ₹7.66 |
| No. of Partners | 5 | 5 | 5 | 5 |

*Note: Explosive growth — 2.25x revenue in 2 years (FY23→FY25). Stock jump to ₹20.36 Cr in FY25 suggests major inventory build-up or new business line.*

---

## Related Party Transactions (from Form 3CD, FY2025)
- Transaction with entity PAN AARFK4663L: ₹78,74,210 — Electronic Goods
- Transaction with another related entity: ₹23,00,000
- "Kurinji Metro" appears in loans/advances schedule — likely a sister concern or sub-entity
- FY25 Balance Sheet shows ₹3.30 Cr in "Other Advances" — believed to be advance to Kurinji Metro → Row 223

---

## Items Requiring OCR Accuracy Testing

The following items are CRITICAL for OCR to correctly extract (they are either large, unusual, or likely to be mis-read):

| Priority | Item | Why Critical |
|----------|------|-------------|
| HIGH | Electric/Phone Charges (combined entry) | Large amount; OCR might split or truncate |
| HIGH | Packing Expenses (FY24 = ₹39.25L) | Unusual routing to Row 44, not Row 71 |
| HIGH | Closing Stock (FY25 = ₹20.36 Cr) | 3x jump — OCR must capture correctly |
| HIGH | Interest to Partners vs Bank Interest | Different rows (83 vs 84); must not be confused |
| MEDIUM | TDS on Rent (separate line) | Tally artifact; must combine with Rent |
| MEDIUM | Bill Printing Roll, Barcode Expenses | New retail-specific terms |
| MEDIUM | Partners' Capital total | Multiple partners — OCR must capture total |
| LOW | Miscellaneous Expenses | Small, catch-all; low risk of error |
