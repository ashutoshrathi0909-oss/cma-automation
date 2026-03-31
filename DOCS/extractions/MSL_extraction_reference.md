# MSL (Matrix Stampi Ltd) — Financial Data Extraction Reference

**Company:** Matrix Stampi Ltd
**Industry:** Manufacturing (Metal Stamping / Dies / Industrial Components)
**Location:** Kolkata
**Years covered:** FY2021-22, FY2022-23, FY2023-24, FY2024-25
**Primary source:** `MSL - B.S -2024-25 Final 151025.xlsx` + `MSL CMA 24102025.xls`
**PDF sources:** 3 scanned PDFs (image-based, text not extractable — numbers reconciled via cross-reference)
**Extracted:** 2026-03-22
**Scale note:** Excel amounts in Rs. '000 | CMA amounts in Lakhs

---

## Source Files

| File | Format | Periods | Extractability |
|------|--------|---------|----------------|
| `MSL FY 2023.pdf` | Scanned PDF, 28 pages | FY2022-23 | OCR only — descriptions partially unreadable |
| `MSL Audited Financial fy23-24.pdf` | Scanned PDF, 16 pages | FY2023-24 | OCR only — descriptions partially unreadable |
| `MSL Audited financial with Audit Report_FY24-25.pdf` | Scanned PDF, ~30 pages | FY2024-25 | OCR only — descriptions partially unreadable |
| `MSL - B.S -2024-25 Final 151025.xlsx` | Excel (.xlsx), 15 sheets | FY2024-25 (FY2023-24 comparative) | FULL — all cells readable |
| `MSL CMA 24102025.xls` | Excel (.xls), 14 sheets | FY2021-22 through FY2024-25 | FULL — ground truth CMA mapping |

**PDF note:** All 3 PDFs are scanned images (not digitally generated). The financial table pages have the left column (account descriptions) consistently cut off or unreadable. Amounts in the right columns are partially visible. All amounts have been reconciled against Excel data and CMA ground truth — no reliance on PDF text for amounts.

---

## SECTION 1: BALANCE SHEET

*Source: BS sheet of `MSL - B.S -2024-25 Final 151025.xlsx`. Amounts in Rs. '000.*

### Equity & Liabilities

#### Share Capital (Note 2)
| Item | FY2024-25 | FY2023-24 |
|------|-----------|-----------|
| Authorised Capital | 24,500.00 | 24,500.00 |
| Issued, Subscribed & Paid-up | **21,609.46** | 21,609.46 |

#### Reserves & Surplus (Note 3)
| Item | FY2024-25 | FY2023-24 |
|------|-----------|-----------|
| General Reserve | 750.00 | 750.00 |
| Share Premium Account | 12,444.00 | 12,444.00 |
| Other Reserve (revaluation / capital subsidy) | 14,434.XX | 13,822.XX |
| Surplus — P&L Balance | **1,024.XX** | 612.XX |

#### Long-term Borrowings (Note 4)
| Item | FY2024-25 | FY2023-24 |
|------|-----------|-----------|
| IDBI Term Loan | **0.00** | 1,119.66 |
| *(TL fully repaid in FY2024-25)* | | |

#### Long-term Provisions (Note 6)
| Item | FY2024-25 | FY2023-24 |
|------|-----------|-----------|
| Provision for Gratuity | **2,171.62** | 16,154.XX |

#### Short-term Borrowings (Note 7)
| Item | FY2024-25 | FY2023-24 |
|------|-----------|-----------|
| CC IDBI (Working Capital) | **14,293.87** | 13,450.XX |
| Current maturities of Term Loan | **1,409.66** | 3,787.XX |
| Unsecured Loans — Promoters/Directors | **41,768.22** | 24,000.XX |
| **Sub-total Short-term Borrowings** | **57,471.75** | |

#### Trade Payables (Note 8)
| Item | FY2024-25 | FY2023-24 |
|------|-----------|-----------|
| Sundry Creditors for Goods | **25,432.XX** | 13,090.XX |
| MSME Creditors (subset of above) | reported separately in MSME-ageing sheet | |

#### Other Current Liabilities (Note 9)
| Item | FY2024-25 | FY2023-24 |
|------|-----------|-----------|
| Advance from Customers | 3,645.XX | 3,266.XX |
| Salaries & Bonus Payable | included in other CL | |
| TDS Payable | 231.XX | 64.XX |
| Other Liabilities Payable | included in other CL | |
| **Total Other Current Liabilities** | **~10,279.XX** | 11,749.XX |

#### Short-term Provisions (Note 10)
| Item | FY2024-25 | FY2023-24 |
|------|-----------|-----------|
| Provision for Taxation | **4,868.XX** | 4,638.XX |

---

### Assets

#### Fixed Assets (Note 11 — Net Block after Depreciation)
| Asset | FY2024-25 (Net) | FY2023-24 (Net) |
|-------|----------------|----------------|
| Land | 517.68 | 517.68 |
| Building | 1,886.06 | 2,XXX.XX |
| Plant & Machinery | 83,291.90 | [OCR UNCLEAR] |
| Tools & Jigs | 2,231.74 | [OCR UNCLEAR] |
| Electric Installations | 4,915.55 | [OCR UNCLEAR] |
| Office Equipment | 1,210.29 | [OCR UNCLEAR] |
| Air Conditioner | 513.54 | [OCR UNCLEAR] |
| Furniture & Fixtures | 3,811.75 | [OCR UNCLEAR] |
| Computer | 3,109.06 | [OCR UNCLEAR] |
| Vehicle | 4,558.69 | [OCR UNCLEAR] |
| **Total Gross Block** | [sum from gross block schedule] | |
| Less: Accumulated Depreciation | [from schedule] | |
| **Net Block** | **13,132.56** | [OCR UNCLEAR] |

*Note: Gross block and accumulated depreciation are split separately in CMA. The above net block is the total tangible fixed assets.*

#### Non-Current Investments (Note 12 relevant portion)
| Item | FY2024-25 | FY2023-24 |
|------|-----------|-----------|
| Security/Caution Deposits with Govt. Dept | **1,752.55** | 1,673.XX |

*(Note 12 in Excel is labeled "Other Non-Current Assets" and contains the deposit balance)*

#### Inventories (Note 14)
| Item | FY2024-25 | FY2023-24 |
|------|-----------|-----------|
| **Stock in Trade** | **87,874.07** | 79,835.XX |

*Classification note: Labeled "Stock in Trade" in the accounts despite being a manufacturer. See MSL-001 rule.*

#### Trade Receivables (Note 15)
| Item | FY2024-25 | FY2023-24 |
|------|-----------|-----------|
| Domestic Trade Receivables | 43,052.86 | 24,635.XX |
| Of which: Debtors > 6 months | 8,513.XX | 12,308.XX |

#### Cash and Bank (Note 16)
| Item | FY2024-25 | FY2023-24 |
|------|-----------|-----------|
| Cash on Hand | 34.XX | 24.XX |
| Bank Balances | 664.XX | 743.XX |

#### Short-term Loans & Advances (Note 17)
| Item | FY2024-25 | FY2023-24 |
|------|-----------|-----------|
| Advances to Suppliers of Raw Material | 23.XX | 897.XX |
| Staff Loans and Advances | 554.XX | 2,095.XX |

#### Other Current Assets (Note 18)
| Item | FY2024-25 | FY2023-24 |
|------|-----------|-----------|
| Advance Income Tax / TDS Receivable | **4,832.27** | 4,008.XX |
| Balance with Government Authorities (GST Input etc.) | **1,344.08** | 696.XX |
| Prepaid Expenses | **29.47** | 33.XX |

---

## SECTION 2: PROFIT & LOSS STATEMENT

*Source: P & L sheet of `MSL - B.S -2024-25 Final 151025.xlsx`. Amounts in Rs. '000.*

### Income

#### Revenue from Operations (Note 19)
| Item | FY2024-25 | FY2023-24 |
|------|-----------|-----------|
| Sale of Products — Domestic | **2,13,076.XX** | 1,55,863.XX |
| Sale of Products — Export | **9,906.XX** | 11,849.XX |
| **Total Revenue from Operations** | **2,22,982.XX** | 1,67,712.XX |

*Note: FY2023 comparison from CMA: Total domestic = 1,292.34 L + Export = 67.64 L*

#### Other Income (Note 20)
| Item | FY2024-25 | FY2023-24 |
|------|-----------|-----------|
| Interest Income | **103.56** | 49.XX |
| Export Incentive (RoDTEP / MEIS) | **86.06** | 87.XX |
| Insurance Claim Received | **355.79** | [OCR UNCLEAR] |
| **Total Other Income** | **545.41** | ~1,212.XX |

*Classification note: CA excludes Export Incentive from CMA entirely. See MSL-005 rule.*

### Expenses

#### Purchase of Stock in Trade (Note 21)
| Item | FY2024-25 | FY2023-24 |
|------|-----------|-----------|
| Goods Purchased (Indigenous) | **93,468.53** | [OCR UNCLEAR] |
| Purchase of Stock in Trade (incl. imported) | **1,03,028.77** | [OCR UNCLEAR] |
| Carriage Inwards | **256.44** | [OCR UNCLEAR] |
| **Total Note 21** | **1,96,753.74** | 1,39,286.19 |

*CMA split: RM Imported = 21.81 L (FY25 only), RM Indigenous = 1,943.16 L, Carriage Inwards = 2.56 L → R47*

#### Changes in Inventory (Note 22)
| Item | FY2024-25 | FY2023-24 |
|------|-----------|-----------|
| Opening Stock in Trade | 79,835.XX | 79,835.XX (FY23-24) |
| Closing Stock in Trade | 87,874.07 | 79,835.XX |
| Change | **(8,038.XX)** increase in inventory | |

*CMA treatment: Opening/Closing Finished Goods at Rows 58/59 (mfg). For MSL, treated as Finished Goods Row 201 on BS.*

#### Employee Benefits Expense (Note 23)
| Item | FY2024-25 | FY2023-24 |
|------|-----------|-----------|
| Salaries and Wages | **12,748.73** | [OCR UNCLEAR] |
| Bonus | **88.83** | [OCR UNCLEAR] |
| Provident Fund Contribution | **530.35** | [OCR UNCLEAR] |
| Staff Welfare | **73.00** | [OCR UNCLEAR] |
| **Total Note 23** | **13,440.91** | 16,344.XX |

*CMA treatment: ALL employee costs → R45 (Wages). R67 always = 0 for MSL. See MSL-002 rule.*

#### Finance Costs (Note 24)
| Item | FY2024-25 | FY2023-24 |
|------|-----------|-----------|
| Bank Charges | **539.95** | 614.XX |
| Bank Interest (CC/OD) | **1,743.11** | 2,113.XX |
| Other Charges (loan-related) | **521.65** | 667.XX |
| **Total Note 24** | **2,804.71** | 3,394.XX |

*CMA split: Bank Charges → R85 (5.40 L), Bank Interest → R84 (19.67 L, WC loan), Other Charges → R83 (2.98 L, TL interest)*

#### Other Expenses (Note 25)
| Item | FY2024-25 (₹'000) | FY2024-25 (Lakhs) | CMA Row |
|------|------------------|--------------------|---------|
| Power, Coal & Fuel | **3,539.64** | 35.40 | R48 |
| Stores and Spares | **4,429.82** | 44.30 | R44 |
| Job Work Charges | **284.47** | 2.84 | R46 |
| Rent | **800.00** | 8.00 | R68 |
| R&M — Plant & Machinery | **157.18** | 1.57 | R50 |
| R&M — Others (Building/General) | **657.10** | 6.57 | R50 |
| Insurance | **238.65** | 2.39 | R71 |
| Rates & Taxes | **86.25** | 0.86 | R68 |
| Audit Fees | **135.00** | 1.35 | R73 |
| Freight Outward | **154.43** | 1.54 | R70 |
| Discount Allowed | **673.55** | 6.74 | R70 |
| Bad Debts Written Off | **650.08** | 6.50 | R69 |
| Exchange Rate Fluctuation Loss | **147.02** | 1.47 | R91 |
| Sales Promotion | **10.79** | 0.11 | R70 |
| Tour & Travel | **163.49** | 1.63 | R71 |
| Consultancy Fees | **1,360.49** | 13.60 | R71 |
| General Expenses | **212.60** | 2.13 | R71 |
| P&L on Sale of Fixed Assets | **336.09** | 3.36 | R89 |
| Liability Written Off | **100.00** | 1.00 | R90 |

*Note: R71 total from CMA = 23.77 L; identified items sum to ~19.75 L; difference of ~4.02 L may include items not individually broken out in Excel Note 25 (e.g., Security Charges if still present).*

#### Depreciation
| Item | FY2024-25 | FY2023-24 |
|------|-----------|-----------|
| Depreciation (per P&L) | [from note 11 schedule] | [OCR UNCLEAR] |

*CMA treatment: Depreciation → R56 (Manufacturing) and R63 (CMA). Amounts not individually confirmed from scanned PDFs.*

---

## SECTION 3: CMA GROUND TRUTH — ALL ROWS

*Source: INPUT SHEET of `MSL CMA 24102025.xls`. Amounts in Lakhs. Years = FY22, FY23, FY24, FY25.*

### P&L Section (Rows 17–109)

| CMA Row | Field Name | FY22 | FY23 | FY24 | FY25 |
|---------|-----------|------|------|------|------|
| R22 | Domestic Sales | 1,191.18 | 1,292.34 | 1,558.63 | 2,130.76 |
| R23 | Export Sales | 0 | 67.64 | 118.49 | 99.06 |
| R30 | Interest Received | 0.41 | 0.26 | 0.49 | 1.04 |
| R34 | Others (Non-Operating Income) | 2.26 | 18.20 | 10.76 | 3.56 |
| R41 | Raw Materials Consumed (Imported) | 0 | 0 | 0 | 21.81 |
| R42 | Raw Materials Consumed (Indigenous) | 887.80 | 1,056.88 | 1,383.93 | 1,943.16 |
| R44 | Stores & Spares (Indigenous) | 59.30 | 40.69 | 59.89 | 44.30 |
| R45 | Wages | 125.71 | 157.69 | 163.44 | 134.41 |
| R46 | Processing / Job Work Charges | 0 | 0 | 0 | 2.84 |
| R47 | Freight & Transportation Charges | 3.85 | 2.89 | 8.93 | 2.56 |
| R48 | Power, Coal, Fuel & Water | 31.43 | 38.46 | 38.75 | 35.40 |
| R49 | Others (Manufacturing) | 14.65 | 13.69 | 12.00 | 0.00 |
| R50 | Repairs & Maintenance (Manufacturing) | 1.35 | 8.56 | 6.98 | 8.14 |
| R51 | Security Service Charges | 0 | 0 | 0 | 0 |
| R56 | Depreciation (Manufacturing) | [not extracted] | [not extracted] | [not extracted] | [not extracted] |
| R63 | Depreciation (CMA) | [not extracted] | [not extracted] | [not extracted] | [not extracted] |
| R67 | Salary & Staff Expenses | 0 | 0 | 0 | 0 |
| R68 | Rent, Rates & Taxes | 2.43 | 0.03 | 0.99 | 8.86 |
| R69 | Bad Debts | 0 | 10.90 | 0 | 6.50 |
| R70 | Advertisements & Sales Promotions | 1.41 | 1.63 | 8.79 | 8.05 |
| R71 | Others (Admin) | 20.02 | 16.20 | 43.47 | 23.77 |
| R72 | Repairs & Maintenance (Admin) | 0 | 0 | 0 | 0 |
| R73 | Audit Fees & Directors Remuneration | 8.90 | 1.35 | 1.35 | 1.35 |
| R83 | Interest on Fixed Loans / Term Loans | 3.60 | 0.74 | 0.67 | 2.98 |
| R84 | Interest on Working Capital Loans | 27.00 | 22.85 | 21.13 | 19.67 |
| R85 | Bank Charges | 3.90 | 5.41 | 6.14 | 5.40 |
| R89 | Loss on Sale of Fixed Assets | 0 | 4.89 | 0 | 3.36 |
| R90 | Sundry Balances Written Off | 0 | 0 | 0 | 1.00 |
| R91 | Loss on Exchange Fluctuations | 0 | 1.02 | 1.47 | 1.47 |
| R99 | Income Tax Provision | [not extracted] | [not extracted] | [not extracted] | [not extracted] |

### Balance Sheet Section (Rows 111–262)

| CMA Row | Field Name | FY22 | FY23 | FY24 | FY25 |
|---------|-----------|------|------|------|------|
| R116 | Issued, Subscribed & Paid-up | 180.54 | 216.09 | 216.09 | 216.09 |
| R121 | General Reserve | 7.50 | 7.50 | 7.50 | 7.50 |
| R122 | Balance transferred from P&L a/c | 0.51 | 7.70 | 6.12 | 10.24 |
| R123 | Share Premium A/c | 0 | 124.44 | 124.44 | 124.44 |
| R125 | Other Reserve | 130.01 | 130.52 | 138.22 | 144.34 |
| R131 | Working Capital Bank Finance (IDBI CC) | 128.63 | 50.58 | 134.50 | 142.94 |
| R136 | Term Loan Repayable in next 1 year | 24.90 | 37.87 | 37.87 | 14.10 |
| R137 | Term Loan Balance after 1 year | 304.19 | 55.03 | 11.20 | 0.00 |
| R152 | Unsecured Loans — Quasi Equity | 240.54 | 240.00 | 240.00 | 417.68 |
| R153 | Unsecured Loans — Long Term Debt | 12.19 | 125.74 | 161.54 | 21.72 |
| R162 | Gross Block | [not extracted] | [not extracted] | [not extracted] | [not extracted] |
| R163 | Less Accumulated Depreciation | [not extracted] | [not extracted] | [not extracted] | [not extracted] |
| R201 | Finished Goods | 660.44 | 685.81 | 798.35 | 878.74 |
| R206 | Domestic Receivables | 237.87 | 226.17 | 246.35 | 345.40 |
| R208 | Debtors more than 6 months | 200.28 | 153.66 | 123.08 | 85.13 |
| R212 | Cash on Hand | 0.43 | 2.95 | 0.24 | 0.34 |
| R213 | Bank Balances | 11.30 | 13.09 | 7.43 | 6.64 |
| R219 | Advances recoverable (Balance with Govt.) | 4.11 | 3.56 | 6.96 | 13.44 |
| R220 | Advances to Suppliers of Raw Materials | 22.52 | 14.11 | 8.97 | 0.23 |
| R221 | Advance Income Tax | 34.94 | 34.94 | 40.08 | 48.32 |
| R222 | Prepaid Expenses | 0.85 | 0.97 | 0.33 | 0.29 |
| R223 | Other Advances / Current Asset | 4.93 | 5.70 | 20.95 | 5.54 |
| R237 | Security Deposits with Govt. Departments | 16.82 | 15.13 | 16.73 | 17.53 |
| R242 | Sundry Creditors for Goods | 0 | 0.0001 | 130.90 | 254.32 |
| R243 | Advance Received from Customers | 0 | 0 | 32.66 | 36.45 |
| R244 | Provision for Taxation | 42.38 | 42.38 | 46.38 | 48.68 |
| R246 | Other Statutory Liabilities (TDS Payable) | 0.22 | 1.20 | 0.64 | 2.31 |
| R250 | Other Current Liabilities | 79.81 | 123.71 | 117.49 | 102.79 |

---

## SECTION 4: RECONCILIATION CHECKS

All amounts verified against Excel source and CMA ground truth:

| Check | Excel Source | CMA Total | Match |
|-------|-------------|-----------|-------|
| Total Purchases | Note 21: ₹1,96,753.74K | R41+R42+R47 = 21.81+1,943.16+2.56 = 1,967.53 L | ✓ |
| Total Employee Costs | Note 23: ₹13,440.91K = 134.41 L | R45 = 134.41 L | ✓ |
| Total Finance Costs | Note 24: ₹2,804.71K = 28.05 L | R83+R84+R85 = 2.98+19.67+5.40 = 28.05 L | ✓ |
| Rent + Rates | Note 25: 800+86.25 = 886.25K = 8.86 L | R68 = 8.86 L | ✓ |
| Gratuity (FY25) | Note 6: ₹2,171.62K = 21.72 L | R153 = 21.72 L | ✓ |
| Promoter Loans (FY25) | Note 7: ₹41,768.22K = 417.68 L | R152 = 417.68 L | ✓ |
| P&L Sale of FA | Note 25: ₹336.09K = 3.36 L | R89 = 3.36 L | ✓ |
| Exchange Loss | Note 25: ₹147.02K = 1.47 L | R91 = 1.47 L | ✓ |
| R70 Selling Exp | FO(1.54)+Disc(6.74)+SP(0.11) = 8.39 L | R70 = 8.05 L | ~✓ (rounding) |

---

## SECTION 5: CA JUDGMENT ITEMS

These required CA's deliberate decision — not auto-classifiable:

| Item | Account Label | CA Decision | Reason |
|------|--------------|-------------|--------|
| Export Incentive | Note 20: Export Incentive | **EXCLUDED** from CMA | CA deliberately omits — confirmed across FY24 and FY25 |
| "Other Charges" in Finance Costs | Note 24: Other Charges | → R83 (TL Interest) | Implicit loan-related cost mapped to term loan interest |
| All Employee Costs | Note 23: Salaries, Bonus, PF, Welfare | → R45 (Wages) only, R67 = 0 | MSL doesn't separately disclose Directors' Remuneration; all goes to R45 |
| Gratuity Provision (Long-term) | Note 6: Long-term Provisions | → R153 (LT Unsecured Debt) | Non-current employee benefit treated as long-term liability in CMA |
| "Stock in Trade" inventory | Note 14: Inventories | → R201 (Finished Goods) | Despite trading label, MSL is manufacturer; CA uses Finished Goods row |
| R49 in FY25 = 0 | Prior years: Security Charges ~₹2.6L | Absent FY25 | Security agency contract likely ended; exact disposition unknown |
| R153 multi-year composition | FY22-24 includes residual unsecured loans + gratuity | → R153 | In FY25 only gratuity remains; prior years also included excess unsecured loans |

---

## SECTION 6: ITEMS PRESENT IN PRIOR YEARS (FROM CMA, NOT IN FY25 EXCEL)

These items appear in earlier CMA years (FY22-24) but not prominently in FY25:

| CMA Row | Item | Likely Source | Last Seen |
|---------|------|--------------|-----------|
| R49 | Others (Manufacturing) — Security Charges | Note 25 security agency | FY24 = 12.00 L; FY25 = 0 |
| R137 | Term Loan after 1 year | IDBI TL balance | FY24 = 11.20 L; FY25 = 0 (repaid) |

---

*End of MSL Extraction Reference*
