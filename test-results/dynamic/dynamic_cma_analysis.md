# Dynamic Air Engineering — CMA Analysis Report
**File analyzed:** `CMA Dynamic 23082025.xls`
**Analyzed by:** Claude (pre-scan Agent P2)
**Date:** 2026-03-19

---

## File Structure

| Sheet | Purpose |
|-------|---------|
| **INPUT SHEET** | Raw financial data entry — 262 rows × 13 cols |
| **TL** | Term Loan repayment schedule |
| **Summary spread** | Computed ratios and summary |
| **Key Financials** | Key metrics |
| **Cash flows** | Cash flow statement |
| **Form_II through Form_VI** | Bank CMA format outputs |
| Details, Query, assumptions | Supporting worksheets |

## Financial Years Covered
- **FY22 (2021-22):** Audited
- **FY23 (2022-23):** Audited
- **FY24 (2023-24):** Audited
- **FY25 (2024-25):** Provisionals
- FY26-FY33: Projected (out of scope)

## Scale
**All values in the INPUT SHEET are in LAKHS (₹ lakhs).**
- 1 = ₹1,00,000 (one lakh rupees)
- Example: Domestic Sales FY22 = 46.08 = ₹46.08 lakhs = ₹46,07,932

## Industry
**Manufacturing / Engineering** — Dynamic Air Engineering India Private Limited
- Makes and sells air handling/engineering equipment
- Company address: No 4, Boopathy Nagar, Industrial Estate, Keelkattalai, Chennai - 600 117
- Confirmed manufacturing by: non-zero Factory Wages, Power & Fuel, Raw Materials, WIP inventory

---

## Key Financial Values (in lakhs)

| Row | CMA Field | FY22 | FY23 | FY24 | FY25 |
|-----|-----------|------|------|------|------|
| R22 | Domestic Sales | 46.079 | 69.437 | 67.150 | 77.579 |
| R26 | Net Sales | 46.079 | 69.437 | 67.150 | 77.579 |
| R30 | Interest Received | 0.039 | 0.061 | 0.059 | 0.067 |
| R42 | Raw Materials (Indigenous) | 29.900 | 56.489 | 48.455 | 52.245 |
| R41 | Raw Materials (Imported) | 0.000 | 0.000 | 0.000 | 0.269 |
| R45 | Factory Wages | 3.452 | 5.836 | 6.537 | 7.165 |
| R47 | Freight & Transport | 0.181 | 0.330 | 0.000 | 1.277 |
| R48 | Power, Coal, Fuel & Water | 0.672 | 0.957 | 0.818 | 1.197 |
| R49 | Other Manufacturing Exp | 0.150 | 0.000 | 4.139 | 0.906 |
| R50 | Repairs & Maintenance | 0.000 | 0.000 | 0.348 | 0.757 |
| R51 | Security Service Charges | 0.000 | 0.000 | 0.087 | 0.084 |
| R56 | Depreciation (Mfg) | 3.222 | 3.225 | 3.086 | 1.981 |
| R57 | Cost of Production | 36.064 | 63.981 | 58.729 | 69.875 |
| R61 | Cost of Sales | 38.455 | 62.782 | 59.544 | 69.762 |
| R67 | Salary & Staff Expenses | 0.280 | 0.520 | 0.547 | 1.188 |
| R68 | Rent, Rates & Taxes | 0.006 | 0.154 | 0.019 | 0.192 |
| R70 | Advertisements & Sales Promo | 0.559 | 0.370 | 0.790 | — |
| R83 | Interest on Term Loans | 1.990 | 2.292 | 3.084 | 0.940 |
| R84 | Interest on Working Capital | 0.607 | 0.317 | 0.910 | 2.087 |
| R85 | Bank Charges | 0.302 | 0.231 | 0.136 | 0.178 |
| R104 | Net Profit (PAT) | 0.789 | 0.693 | 0.390 | 0.966 |
| R136 | Term Loan (next 1 year) | 4.010 | 5.654 | 5.581 | 0.000 |
| R242 | Sundry Creditors for Goods | 8.176 | 10.376 | 8.451 | 15.851 |
| R260 | Total Assets | 43.649 | 55.757 | 52.505 | 58.037 |

---

## FY25 Provisional — Absolute Rupees Cross-Check

The FY25 `Provisional financial 31.03.25 (3).xlsx` stores values in **absolute rupees** (not lakhs).
Confirmed by cross-checking:
- Revenue from operations in Excel: ₹77,57,92,460 → in lakhs = **77.58** ✅ (matches CMA: 77.579)
- Net Profit in Excel: ₹96,60,162 → in lakhs = **0.966** ✅ (matches CMA: 0.966)

**Conclusion: CMA file is authoritative. Excel files are the source — values match perfectly.**

---

## Key Observations for Test

1. **Sales are growing:** FY22=46L → FY23=69L → FY24=67L → FY25=78L (slight dip in FY24)
2. **Raw materials dominant cost:** ~60-65% of sales — consistent with manufacturing
3. **WIP inventory growing:** FY22=2.5L → FY23=5.4L → FY24=10.1L → FY25=10.0L (sign of order backlog building)
4. **Term loan reducing:** Term loan repayable next year dropped to 0 in FY25 — loan nearly paid off
5. **Net profit thin:** 1-2% margins — typical for Indian engineering MSME firms
6. **R49 (Other Mfg Exp) jump in FY24:** 0 → 4.14 lakhs — check what this contains in Notes
7. **Factory wages R45 growing YoY:** Business expanding

---

## Validation Notes for App Testing

- When app generates CMA, compare values in **lakhs** (divide app's absolute values by 100,000)
- For FY24 Vision OCR test: target Sales ≈ 67.15 lakhs, Raw Materials ≈ 48.45 lakhs
- Manufacturing row R45 (Wages) should be non-zero — distinguishes this from trading companies
- R49 (Other Mfg Exp) at 4.14 lakhs in FY24 — likely in Notes to Accounts as sub-items
