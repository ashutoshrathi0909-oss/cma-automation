# BCIPL CMA Excel Comparison Report (v2)
**Date:** 2026-04-05
**Generated file:** BCIPL_generated_CMA.xlsm (109,259 bytes)
**Ground truth:** CMA BCIPL 12012024.xls (581,120 bytes)
**Output unit:** Crores
**Source units:** FY2021 = rupees, FY2022 = lakhs, FY2023 = rupees
**v1 baseline:** 8.6% accuracy (16/186) from run-2026-04-04

## 1. Structure Verification
| Check | Result | Details |
|-------|--------|---------|
| File format (.xlsm) | **PASS** | Correct format |
| VBA macros present | **PASS** | `vba_archive` is not None |
| INPUT SHEET exists | **PASS** | Present in generated file |
| Client name (Row 7) | **PASS** | Gen: "BCIPL" |
| Years (Row 8 B-D) | **PASS** | [2021, 2022, 2023] |
| Nature (Row 10 B-D) | **PASS** | ["audited", "audited", "audited"] |
| Units (Row 13 B) | **CHECK** | Gen: "In " (truncated -- missing "crs") |
| Projection years (E-H) | **PASS** | [2024, 2025, 2026, 2027] |
| Projection formulas preserved | **N/A** | Not in V1 scope |

## 2. Data-Entry Accuracy Summary
| Metric | Count |
|--------|-------|
| Total data-entry rows mapped | 130 |
| Total data-entry cells checked (130 rows x 3 FYs) | 390 |
| GT has value (non-empty, non-zero) | 186 |
| Matching (within 2%) | **20** |
| Mismatched | 25 |
| Missing (GT has value, generated empty) | **141** |
| Extra (generated has value, GT empty) | 6 |
| Both empty | 198 |
| **Data-entry accuracy** | **10.8% (20/186)** |

## 3. v1 vs v2 Comparison

### Overall Metrics
| Metric | v1 | v2 | Change |
|--------|-----|-----|--------|
| Data-entry accuracy | 8.6% (16/186) | 10.8% (20/186) | **+2.2pp** |
| Matching cells | 16 | 20 | **+4** |
| Mismatched | 101 | 25 | **-76** |
| Missing | 56 | 141 | **+85** |
| Extra | 36 | 6 | **-30** |

### Key Cell Comparisons (v1 vs v2)
| Row | CMA Field | FY | GT | v1 | v2 | Assessment |
|-----|-----------|-----|-----|-----|-----|-----------|
| 22 | Domestic Sales | B(2021) | 96.58 | 335.38 (247% off) | **EMPTY** | Worse: dedup removed all copies |
| 22 | Domestic Sales | C(2022) | 234.64 | 1030.79 (339% off) | **EMPTY** | Worse: dedup removed all copies |
| 22 | Domestic Sales | D(2023) | 256.95 | 1103.10 (329% off) | **EMPTY** | Worse: dedup removed all copies |
| 42 | Raw Materials | B(2021) | 84.35 | 91.30 (8% off) | **EMPTY** | **Worse**: was close in v1, now gone |
| 44 | Stores/Spares | B(2021) | 1.76 | 86.11 (4785% off) | **EMPTY** | Neutral: wrong value eliminated |
| 45 | Wages | B(2021) | 6.38 | 14.10 (121% off) | **EMPTY** | Worse: dedup removed all copies |
| 56 | Depreciation Mfg | B(2021) | 4.07 | 13.52 (232% off) | **EMPTY** | Neutral: bad value eliminated |
| 67 | Salary | C(2022) | 1.66 | 15482.98 | **EMPTY** | **Better**: unit error eliminated |
| 68 | Rent/Rates/Taxes | D(2023) | 0.07 | 92.91 | 0.07 (5%) | **Better**: now near-match |
| 71 | Others Admin | C(2022) | 3.38 | 2173.27 | **EMPTY** | **Better**: dump bucket eliminated |
| 73 | Audit/Directors | C(2022) | empty | 30942.00 | **EMPTY** | **Better**: unit error eliminated |
| 137 | TL > 1yr | C(2022) | 12.76 | 908.79 | **EMPTY** | **Better**: huge misroute eliminated |
| 206 | Dom Receivables | B(2021) | 17.92 | 32.63 (82% off) | 18.52 (3%) | **Much better**: dedup fixed |
| 206 | Dom Receivables | C(2022) | 34.70 | 54.89 (58% off) | 36.32 (5%) | **Much better**: dedup fixed |
| 206 | Dom Receivables | D(2023) | 15.48 | 52.93 (242% off) | 16.62 (7%) | **Much better**: dedup fixed |
| 242 | Sundry Creditors | B(2021) | 10.31 | 3.18 (69% off) | **EMPTY** | Worse: was partially there |

### Bug Fix Impact Analysis

| Bug Fix | Impact | Assessment |
|---------|--------|------------|
| **1. Cross-sheet dedup** | Mismatches dropped 101 -> 25. But 85 previously-present cells are now EMPTY. Revenue, Raw Materials, Wages, Depreciation -- entire P&L sections gutted. Receivables improved dramatically (3-7% off vs 58-242%). | **Overly aggressive** -- removes ALL copies instead of keeping the P&L face value. Most impactful fix, but needs refinement. |
| **2. Legacy golden rules** | Export Sales: still missing all 3 FYs. Interest on TL: still only 0.15/0.18 (expected 1.30/1.43). Deferred Tax: still missing. | **No visible improvement** -- golden rules either not firing or items not reaching the golden rule tier. |
| **3. notes_to_accounts = BS context** | Raw Materials/Stores cross-contamination cannot be evaluated because both rows are now entirely empty. | **Inconclusive** -- masked by dedup bug. |
| **4. Unroutable -> doubt** | Others Admin (Row 71): 285/2173/760 -> all empty. Eliminated the dump bucket problem completely. But also sent classifiable items to doubt. | **Working but too aggressive** -- 141 missing cells (vs 56 in v1) suggests many routable items are being excluded. |

**Most impactful fix:** Cross-sheet dedup (#1) had the largest effect -- it eliminated 76 mismatches but created 85 new missing cells. The net effect on accuracy is +4 cells (+2.2pp), but the error profile completely changed from "wrong values" to "no values."

## 4. Matching Cells (20 cells within 2%)
| Row | CMA Field | FY | Expected | Got | Diff% |
|-----|-----------|-----|----------|-----|-------|
| 46 | Processing / Job Work | C(2022) | 2.0517 | 2.0500 | 0.1% |
| 48 | Power, Coal, Fuel | B(2021) | 0.8037 | 0.8000 | 0.5% |
| 48 | Power, Coal, Fuel | D(2023) | 1.2164 | 1.2200 | 0.3% |
| 70 | Ads/Sales Promotions | C(2022) | 3.2085 | 3.2100 | 0.0% |
| 106 | Brought forward | B(2021) | 4.2646 | 4.2600 | 0.1% |
| 116 | Share Capital | B(2021) | 3.0942 | 3.0900 | 0.1% |
| 116 | Share Capital | C(2022) | 3.0942 | 3.0900 | 0.1% |
| 116 | Share Capital | D(2023) | 3.0900 | 3.0900 | 0.0% |
| 132 | WC Bank Finance 2 | B(2021) | 0.8975 | 0.9000 | 0.3% |
| 136 | TL Repayable < 1yr | B(2021) | 3.0047 | 3.0000 | 0.2% |
| 136 | TL Repayable < 1yr | C(2022) | 4.1154 | 4.1200 | 0.1% |
| 136 | TL Repayable < 1yr | D(2023) | 5.0519 | 5.0500 | 0.0% |
| 172 | Other Intangible | D(2023) | 0.0804 | 0.0800 | 0.5% |
| 219 | Advances recoverable | D(2023) | 2.2037 | 2.2000 | 0.2% |
| 220 | Advances to suppliers RM | B(2021) | 0.7549 | 0.7500 | 0.6% |
| 220 | Advances to suppliers RM | C(2022) | 1.2373 | 1.2400 | 0.2% |
| 220 | Advances to suppliers RM | D(2023) | 0.3528 | 0.3500 | 0.8% |
| 222 | Prepaid Expenses | B(2021) | 0.1191 | 0.1200 | 0.8% |
| 222 | Prepaid Expenses | D(2023) | 0.1428 | 0.1400 | 2.0% |
| 243 | Advance from customers | D(2023) | 0.8996 | 0.9000 | 0.0% |

**New matches in v2 (not matching in v1):** Term Loan < 1yr (Row 136, all 3 FYs), Advances to suppliers RM (Row 220, all 3 FYs), Processing/Job Work (Row 46 C), Power/Fuel (Row 48 B/D), Ads/Sales (Row 70 C), WC Bank 2 (Row 132 B), Prepaid (Row 222 B/D), Advances recoverable (Row 219 D), Intangible (Row 172 D), Brought forward (Row 106 B), Advance from customers (Row 243 D).

These are mostly Balance Sheet items that survived the dedup -- they had clean, single-source extractions.

## 5. Mismatched Cells (25 cells, detailed)
| Row | CMA Field | FY | Expected | Got | Diff% | Formula | Error Type | Root Cause |
|-----|-----------|-----|----------|-----|-------|---------|------------|------------|
| 30 | Interest Received | C(2022) | 0.06 | 6.55 | 11213% | `6.55` | F-Unit | FY2022 value in lakhs not converted (6.55L = 0.066 Cr) |
| 32 | Gain on Exchange | D(2023) | 0.03 | 0.20 | 573% | `0.2` | H-Misroute | Extra exchange gain item classified here |
| 34 | Others Non-Op Inc | B(2021) | 0.01 | 0.09 | 783% | `0.09` | H-Misroute | Extra items classified here |
| 68 | Rent/Rates/Taxes | B(2021) | 0.10 | 0.04 | 59% | `0.04` | I-Partial | Only partial rent captured |
| 68 | Rent/Rates/Taxes | D(2023) | 0.07 | 0.07 | 5% | `0.07` | D-Near | Nearly matching (5% off) |
| 70 | Ads/Sales Promo | D(2023) | 6.78 | 4.54 | 33% | `4.54` | I-Partial | Missing ~2.24 Cr of ad expense |
| 83 | Interest on TL | B(2021) | 1.30 | 0.15 | 88% | `0.15` | I-Partial | Only bank charges portion captured, bulk TL interest missing |
| 83 | Interest on TL | D(2023) | 1.43 | 0.18 | 87% | `0.18` | I-Partial | Same as above |
| 131 | WC Bank Finance 1 | D(2023) | 12.15 | 4.02 | 67% | `4.02` | I-Partial | Only one WC facility captured |
| 162 | Gross Block | B(2021) | 45.90 | 27.27 | 41% | `27.27` | I-Partial | Only intangible block; tangible assets (~18.6 Cr) missing |
| 162 | Gross Block | C(2022) | 49.86 | 27.32 | 45% | `27.32` | I-Partial | Same -- tangible not captured |
| 162 | Gross Block | D(2023) | 53.19 | 30.44 | 43% | `30.44` | I-Partial | Same |
| 165 | Capital WIP | C(2022) | 0.40 | 2.36 | 497% | `2.36` | H-Misroute | Extra capital item classified here |
| 172 | Other Intangible | B(2021) | 0.007 | 0.01 | 44% | `0.01` | D-Rounding | Rounding to 2dp |
| 206 | Dom Receivables | B(2021) | 17.92 | 18.52 | 3% | `18.52` | D-Near | Close -- slight overcount (~0.60 Cr extra) |
| 206 | Dom Receivables | C(2022) | 34.70 | 36.32 | 5% | `36.32` | D-Near | Close -- slight overcount (~1.62 Cr extra) |
| 206 | Dom Receivables | D(2023) | 15.48 | 16.62 | 7% | `16.62` | D-Near | Close -- includes debtors > 6mo |
| 212 | Cash on Hand | C(2022) | 0.009 | 1.75 | 19563% | `1.75` | H-Misroute | Cash & Bank combined item (175.03L) classified as Cash on Hand (doubt resolution from v1) |
| 219 | Advances recoverable | B(2021) | 0.04 | 0.04 | 6% | `0.04` | D-Near | Close |
| 219 | Advances recoverable | C(2022) | 0.67 | 1.21 | 79% | `1.21` | H-Misroute | Other advance merged here |
| 223 | Other Advances | C(2022) | 0.29 | 1.21 | 316% | `1.21` | H-Misroute | Same 1.21 value appearing in both Row 219 and 223 |
| 223 | Other Advances | D(2023) | 0.36 | 2.62 | 637% | `2.62` | H-Misroute | Large advance misclassified here |
| 236 | Advances to cap goods | B(2021) | 1.17 | -0.05 | 104% | `-0.05` | I-Partial | Almost entirely missing |
| 250 | Other current liab | B(2021) | 2.55 | 0.16 | 94% | `0.16` | I-Partial | Most liabilities missing |
| 250 | Other current liab | D(2023) | 1.45 | 3.24 | 123% | `3.24` | H-Misroute | Extra liabilities classified here |

### Improvement from v1: Mismatches that were FIXED
These v1 mismatches no longer appear as mismatches (either became matches or were cleared):
- **Row 22 Domestic Sales (all FYs)**: 335/1031/1103 -> empty (dedup removed duplicates, but also the original)
- **Row 44 Stores/Spares**: 86/200/222 -> empty (cross-contamination eliminated)
- **Row 56 Depreciation**: 14/68/62 -> empty (triplication eliminated)
- **Row 67 Salary C(2022)**: 15483 -> empty (unit error eliminated)
- **Row 71 Others Admin**: 285/2173/760 -> empty (dump bucket eliminated)
- **Row 73 Audit/Directors C(2022)**: 30942 -> empty (unit error eliminated)
- **Row 137 TL > 1yr C(2022)**: 909 -> empty (massive misroute eliminated)
- **Row 206 Dom Receivables**: 33/55/53 -> 19/36/17 (dedup worked correctly here -- **best improvement**)

## 6. Missing Cells (141 cells -- GT has value, generated empty)

### P&L Missing (71 cells)
| Row | CMA Field | FYs Missing | Expected Range | Likely Cause |
|-----|-----------|-------------|----------------|--------------|
| 22 | Domestic Sales | B, C, D | 96.58 -- 256.95 | **Dedup removed all copies** including P&L face value |
| 23 | Export Sales | B, C, D | 2.44 -- 8.86 | Revenue not split into domestic/export; dedup also involved |
| 30 | Interest Received | B, D | 0.06 -- 0.08 | Small amount; not classified |
| 34 | Others Non-Op Income | C, D | 0.02 -- 0.15 | Not classified |
| 42 | Raw Materials (Indigenous) | B, C, D | 84.35 -- 217.74 | **Dedup removed all copies** |
| 44 | Stores/Spares (Indigenous) | B, C, D | 1.76 -- 4.39 | Dedup removed |
| 45 | Wages | B, C, D | 6.38 -- 12.53 | **Dedup removed all copies** (employee benefit sub-items all excluded) |
| 46 | Processing / Job Work | B, D | 1.22 -- 2.26 | Not classified for these FYs |
| 48 | Power, Coal, Fuel | C | 0.98 | FY2022 not classified |
| 49 | Others (Manufacturing) | B, C, D | 0.03 -- 0.16 | Not classified |
| 50 | Repairs Mfg | C, D | 0.22 -- 0.42 | Not classified |
| 56 | Depreciation (Mfg) | B, C, D | 3.92 -- 4.30 | **Dedup removed all copies** |
| 58 | FG Opening | B, C, D | 1.19 -- 3.40 | Inventory opening not classified |
| 59 | FG Closing | B, C, D | 1.81 -- 3.40 | Inventory closing not classified |
| 63 | Depreciation (CMA) | B, C, D | 3.92 -- 4.30 | Should equal Row 56; both empty |
| 64 | Other Mfg Exp (CMA) | B, C, D | 8.48 -- 16.46 | CMA-specific field, not directly in source |
| 67 | Salary/Staff | B, C, D | 0.30 -- 1.66 | Dedup removed |
| 68 | Rent/Rates/Taxes | C | 0.09 | FY2022 not classified |
| 69 | Bad Debts | C, D | 0.001 -- 0.09 | Not classified |
| 71 | Others (Admin) | B, C, D | 1.68 -- 3.38 | All admin items excluded by unroutable->doubt |
| 72 | Repairs Admin | B | 0.05 | Not classified |
| 73 | Audit Fees/Directors | B | 1.99 | Not classified |
| 75 | Misc Expenses written off | C | 0.007 | Not classified |
| 83 | Interest on TL | C | 1.47 | FY2022 entirely missing |
| 84 | Interest on WC | B, C, D | 0.65 -- 2.59 | All FYs -- interest WC not classified |
| 85 | Bank Charges | B, C, D | 0.09 -- 0.17 | All FYs missing |
| 91 | Loss on Exchange | B | 0.16 | Not classified |
| 99 | Income Tax | B, C, D | 0.02 -- 2.20 | All FYs -- tax not classified |
| 100 | Deferred Tax Liab (P&L) | B, D | 0.08 -- 0.26 | Not classified |
| 101 | Deferred Tax Asset (P&L) | C | 0.34 | Not classified |
| 106 | Brought forward | C, D | 6.05 -- 12.90 | FY2022/2023 not classified |

### Balance Sheet Missing (70 cells)
| Row | CMA Field | FYs Missing | Expected Range | Likely Cause |
|-----|-----------|-------------|----------------|--------------|
| 122 | Balance from P&L | B, C, D | 6.05 -- 17.08 | Reserves detail not classified |
| 123 | Share Premium | B, C, D | 0.96 | All FYs -- not extracted from BS |
| 131 | WC Bank 1 | B, C | 11.13 -- 19.61 | Borrowing not classified to WC split |
| 132 | WC Bank 2 | C | 1.47 | Second bank not identified |
| 137 | TL > 1yr | B, C, D | 6.32 -- 16.68 | **Dedup removed all loan values** |
| 152 | Unsecured Quasi Equity | B, C, D | 4.13 | Director loans not classified |
| 153 | Unsecured LT Debt | D | 3.24 | Not classified |
| 159 | Deferred Tax (BS) | B, C, D | 0.82 -- 1.16 | Not extracted |
| 163 | Accum Depreciation | B, C, D | 18.63 -- 22.75 | Not classified separately |
| 165 | Capital WIP | B, D | 0.17 -- 0.31 | Not classified for these FYs |
| 172 | Other Intangible | C | 0.19 | FY2022 not classified |
| 194 | Raw Material Inv | B, C, D | 6.95 -- 16.83 | All FYs -- inventory not classified to BS |
| 198 | Stores Inv | B, C, D | 0.006 -- 0.018 | Very small, not extracted |
| 201 | Finished Goods (BS) | B, C, D | 1.81 -- 3.40 | Inventory closing not linked to BS |
| 207 | Export Receivables | B, C, D | 0.59 -- 1.62 | Not split from domestic |
| 208 | Debtors > 6 months | B, D | 0.008 -- 0.066 | Not extracted from aging |
| 212 | Cash on Hand | B, D | 0.01 -- 0.01 | Not classified |
| 213 | Bank Balances | B, C, D | 0.003 -- 0.64 | All FYs missing |
| 215 | Other FD | B, C, D | 0.63 -- 1.14 | Fixed deposits not classified |
| 221 | Advance Income Tax | B, C, D | 0.18 -- 0.45 | Not classified |
| 222 | Prepaid Expenses | C | 0.13 | FY2022 not classified |
| 223 | Other Advances | B | 0.25 | Not classified |
| 232 | Debtors > 6mo NC | B, D | 0.008 -- 0.066 | Not classified |
| 236 | Advances to cap goods | C, D | 0.17 -- 0.42 | Not classified |
| 237 | Security deposits | B, C, D | 0.25 -- 0.36 | All FYs -- not classified |
| 238 | Other NC assets | B | 0.34 | Not classified |
| 242 | Sundry Creditors | B, C, D | 10.31 -- 14.29 | **All FYs now empty** (was partially present in v1) |
| 244 | Provision for Tax | B | 0.32 | Not classified |
| 246 | Other statutory liab | B, C, D | 0.49 -- 1.34 | All FYs -- not classified |
| 249 | Creditors for Expenses | C, D | 0.38 -- 0.96 | Not classified |
| 250 | Other current liab | C | 4.65 | FY2022 not classified |

## 7. Extra Cells (6 cells -- generated has value, GT empty)
| Row | CMA Field | FY | Got | Formula |
|-----|-----------|-----|-----|---------|
| 50 | Repairs Mfg | B(2021) | 0.05 | `0.05` |
| 70 | Ads/Sales Promo | B(2021) | 1.96 | `1.96` |
| 154 | Unsecured ST Debt | C(2022) | 2.11 | `2.11` |
| 154 | Unsecured ST Debt | D(2023) | 0.74 | `0.74` |
| 243 | Advance from customers | B(2021) | 1.27 | `1.27` |
| 243 | Advance from customers | C(2022) | 1.37 | `1.37` |

Note: v1 had 36 extra cells; v2 has only 6. This is a significant improvement -- the pipeline is no longer generating phantom values.

## 8. Unit Conversion Verification
| Row | CMA Field | GT B(2021) | GT C(2022) | GT D(2023) | Gen B | Gen C | Gen D | Magnitude OK? |
|-----|-----------|------------|------------|------------|-------|-------|-------|---------------|
| 22 | Domestic Sales | 96.58 | 234.64 | 256.95 | empty | empty | empty | N/A |
| 42 | Raw Materials | 84.35 | 196.50 | 217.74 | empty | empty | empty | N/A |
| 45 | Wages | 6.38 | 10.32 | 12.53 | empty | empty | empty | N/A |
| 83 | Interest on TL | 1.30 | 1.47 | 1.43 | 0.15 | empty | 0.18 | OK (consistent) |
| 99 | Income Tax | 0.02 | 2.20 | 1.76 | empty | empty | empty | N/A |
| 116 | Share Capital | 3.09 | 3.09 | 3.09 | 3.09 | 3.09 | 3.09 | **YES** |
| 162 | Gross Block | 45.90 | 49.86 | 53.19 | 27.27 | 27.32 | 30.44 | OK (consistent) |
| 206 | Dom Receivables | 17.92 | 34.70 | 15.48 | 18.52 | 36.32 | 16.62 | OK (consistent) |
| 213 | Bank Balances | 0.64 | 0.02 | 0.00 | empty | empty | empty | N/A |
| 242 | Sundry Creditors | 10.31 | 12.79 | 14.29 | empty | empty | empty | N/A |

**v2 improvement**: No FY2022 values are wildly out of magnitude now. The FY2022 unit errors (Salary 15471, Audit Fees 30942, lakhs raw values) are all eliminated. The remaining populated cells show consistent magnitude across FYs.

**Remaining unit issue**: Row 30 Interest Received C(2022): 6.55 (should be 0.066 Cr from 6.55 lakhs).

## 9. Formula Analysis

v2 formulas are all **single scalar values** (e.g., `0.15`, `3.09`, `27.27`) -- not multi-item sums like v1 (e.g., `=105.43+0.55+105.43+123.97`). This confirms the dedup fix is working: items are no longer being summed from multiple sources. However, the fact that all P&L revenue/expense cells are empty means the primary extraction is not reaching the Excel writer.

## 10. Doubt-Related Cells

The v2 doubt resolutions file contains **32+ entries**, all resolved as `approve_unclassified`. Key patterns:
- BS section headers (Reserves & Surplus, Long-term Borrowings, Trade Payables, etc.)
- Cash flow statement items
- Loan facility names (Axis Term Loan accounts)
- Person names (directors)
- Aging schedule lines
- Revenue from Operations (section header)
- Equity Shares (section header)

**Critical observation**: "Revenue from operations" was sent to doubt and excluded. This is a section header, not a data line -- correct exclusion. But the underlying revenue LINE ITEMS (Sale of Products, Sale of Services) were likely also excluded by the dedup before they reached classification.

## 11. Error Breakdown by Type (v2)
| Error Type | v2 Count | v1 Count | Change |
|------------|----------|----------|--------|
| **I - Missing Item** | **141** | 56 | +85 |
| **D - Aggregation/Near** | **11** | 28 | -17 |
| **H - Misroute** | **8** | 48 | -40 |
| **I - Partial** | **4** | -- | new |
| **F - Unit Error** | **2** | ~10 | -8 |
| **D - Duplicate** | **0** | 25 | -25 |
| Total errors | **166** | 157 | +9 |

**Key shifts:**
- Duplicates **completely eliminated** (25 -> 0)
- Misroutes **reduced 83%** (48 -> 8)
- Unit errors **reduced 80%** (~10 -> 2)
- Missing items **increased 152%** (56 -> 141) -- the primary new problem

## 12. Key Ground Truth Values (sanity check)
| Row | CMA Field | B (2021) | C (2022) | D (2023) |
|-----|-----------|----------|----------|----------|
| 22 | Domestic Sales | 96.58 | 234.64 | 256.95 |
| 23 | Exports | 8.86 | 2.44 | 7.44 |
| 42 | Raw Materials Indigenous | 84.35 | 196.50 | 217.74 |
| 45 | Wages | 6.38 | 10.32 | 12.53 |
| 83 | Interest on TL | 1.30 | 1.47 | 1.43 |
| 116 | Share Capital | 3.09 | 3.09 | 3.09 |
| 162 | Gross Block | 45.90 | 49.86 | 53.19 |
| 206 | Domestic Receivables | 17.92 | 34.70 | 15.48 |
| 242 | Sundry Creditors | 10.31 | 12.79 | 14.29 |

All values confirmed correct in ground truth.

## 13. Overall Verdict

**Data-entry accuracy: 10.8% (20/186)**
**Target: >= 85%**
**Result: FAIL**

### Summary

v2 shows a dramatically different error profile from v1. The four bug fixes **successfully eliminated** the worst symptoms -- duplicate counting (eliminated), catch-all dump buckets (eliminated), unit conversion errors (mostly eliminated), and cross-contamination (eliminated). However, the fixes were **too aggressive**, removing valid data along with invalid data. The result is a pipeline that produces very few wrong values but also very few correct values.

The generated file is now essentially empty for the entire P&L section (Revenue, COGS, Manufacturing Expenses, Admin Expenses) and large parts of the Balance Sheet (Borrowings, Creditors, Inventory). Only 20 out of 186 cells match, though the cells that ARE present are much more accurate than v1.

**The core problem is clear**: the cross-sheet dedup removes ALL copies of an extracted item when duplicates are detected, instead of keeping exactly one (preferably the P&L face / BS face value). Fixing this single issue would likely restore 40-60 cells that were matching or close in v1 while keeping the dedup protection.

### Priority Fixes (in order of impact)

1. **Fix cross-sheet dedup to KEEP ONE copy** (est. +40-60 cells)
   The dedup currently removes all copies. It should keep the P&L face / BS face value and only remove Note/Schedule duplicates. This would restore Domestic Sales, Raw Materials, Wages, Depreciation, Stores/Spares, FG Inventory, and many more.
   Priority: **CRITICAL** -- this single fix accounts for ~60% of all missing cells.

2. **Fix "unroutable -> doubt" threshold** (est. +15-25 cells)
   The doubt pipeline is too aggressive. Items like Interest on WC, Bank Charges, Salary/Staff, Others Admin, Sundry Creditors, and Income Tax should be classifiable by the fuzzy/golden rule tiers but are being excluded. Investigate whether the dedup is removing them before they reach classification, or whether the classification tiers are failing to match.
   Priority: **HIGH**

3. **Add Gross Block tangible asset extraction** (est. +3 cells)
   Gross Block (Row 162) consistently shows only ~27-30 Cr (intangible block) vs GT 46-53 Cr. The tangible fixed assets (~18-23 Cr) are not being extracted or classified. This needs a specific extraction rule for "Tangible Assets" / "Property, Plant and Equipment" from the BS face.
   Priority: **MEDIUM**

4. **Fix remaining FY2022 unit conversion** (est. +1 cell)
   Interest Received C(2022): 6.55 should be 0.066 Cr. The lakhs->crores conversion is not being applied to this specific item.
   Priority: **LOW**

5. **Split Domestic vs Export Receivables** (est. +3 cells)
   Row 206 is slightly over (3-7%) because export receivables (~0.6-1.6 Cr) are included. Row 207 (Export Receivables) is empty. Add a classification rule to split receivables by domestic/export.
   Priority: **LOW**

### v2 vs v1 Scorecard
| Aspect | v1 | v2 | Winner |
|--------|-----|-----|--------|
| Accuracy | 8.6% | 10.8% | v2 |
| Wrong values (mismatches) | 101 | 25 | **v2** (much better) |
| Missing values | 56 | 141 | v1 (v2 much worse) |
| Worst single cell error | 30942 (93M% off) | 6.55 (11213% off) | **v2** |
| Unit errors | ~10 | 2 | **v2** |
| Duplicates | 25 | 0 | **v2** |
| Dump bucket (Row 71) | 2173 Cr | 0 | **v2** |
| Receivables accuracy | 58-242% off | 3-7% off | **v2** |
| Revenue accuracy | 247-339% off | empty | Tie (both wrong) |
| Overall quality of present values | Low | High | **v2** |

**Bottom line**: v2 values, when present, are significantly more trustworthy than v1. The problem is that 76% of expected cells are empty. Fix #1 (keep-one-copy dedup) should unlock a major accuracy jump.
