# BCIPL CMA Excel Comparison Report
**Date:** 2026-04-04
**Generated file:** BCIPL_generated_CMA.xlsm (109,888 bytes)
**Ground truth:** CMA BCIPL 12012024.xls (581,120 bytes)
**Output unit:** Crores
**Source units:** FY2021 = rupees, FY2022 = lakhs, FY2023 = rupees

## 1. Structure Verification
| Check | Result | Details |
|-------|--------|---------|
| File format (.xlsm) | **PASS** | Correct format |
| VBA macros present | **PASS** | `vba_archive` is not None |
| INPUT SHEET exists | **PASS** | Present in generated file |
| Client name (Row 7) | **PASS** | Gen: "BCIPL" |
| Years (Row 8 B-D) | **PASS** | [2021, 2022, 2023] |
| Nature (Row 10 B-D) | **PASS** | ["audited", "audited", "audited"] |
| Units (Row 13 B) | **CHECK** | Gen: "In " (truncated — missing "crs") |
| Projection years (E-H) | **PASS** | [2024, 2025, 2026, 2027] |
| Projection formulas preserved | **N/A** | Row 17 E-H empty (expected — projections not in V1 scope) |

## 2. Data-Entry Accuracy Summary
| Metric | Count |
|--------|-------|
| Total data-entry rows mapped | 130 |
| Total data-entry cells checked (130 rows x 3 FYs) | 390 |
| GT has value (non-empty, non-zero) | 186 |
| Matching (within 2%) | 16 |
| Mismatched | 101 |
| Missing (GT has value, generated empty) | 56 |
| Extra (generated has value, GT empty) | 36 |
| Both empty | 168 |
| **Data-entry accuracy** | **8.6% (16/186)** |

## 3. Mismatched Cells (detailed)
| Row | CMA Field | FY | Expected | Got | Diff% | Error Type | Root Cause |
|-----|-----------|-----|----------|-----|-------|------------|------------|
| 22 | Domestic Sales | B(2021) | 96.58 | 335.38 | 247% | D-Duplicate | Revenue items counted 2-3x from overlapping sheets |
| 22 | Domestic Sales | C(2022) | 234.64 | 1030.79 | 339% | D-Duplicate | Same: revenue extracted from P&L + Notes + Schedule |
| 22 | Domestic Sales | D(2023) | 256.95 | 1103.10 | 329% | D-Duplicate | Same: 264.07 appears twice in formula |
| 23 | Export Sales | C(2022) | 2.44 | None | - | I-Missing | Formula `=B23*1.05` but B23 is empty; FY2022 export not classified |
| 34 | Others (Non-Op Income) | B(2021) | 0.01 | 0.10 | 881% | H-Misroute | Extra items classified here |
| 34 | Others (Non-Op Income) | C(2022) | 0.02 | 6.55 | 34927% | H-Misroute | 6.55 lakhs raw value dumped here |
| 34 | Others (Non-Op Income) | D(2023) | 0.15 | 0.72 | 387% | H-Misroute | Extra items classified here |
| 42 | Raw Materials (Indigenous) | B(2021) | 84.35 | 91.30 | 8% | D-Aggregation | Stores/inventory amount (6.95) wrongly included |
| 42 | Raw Materials (Indigenous) | C(2022) | 196.50 | 204.47 | 4% | D-Aggregation | Stores amount (8.05) wrongly included |
| 42 | Raw Materials (Indigenous) | D(2023) | 217.74 | 234.54 | 8% | D-Aggregation | Stores amount (16.83) wrongly included |
| 44 | Stores/Spares (Indigenous) | B(2021) | 1.76 | 86.11 | 4785% | H-Misroute | Raw materials (84.35) classified here too |
| 44 | Stores/Spares (Indigenous) | C(2022) | 3.49 | 199.91 | 5629% | H-Misroute | Raw materials (196.42) classified here too |
| 44 | Stores/Spares (Indigenous) | D(2023) | 4.39 | 222.13 | 4957% | H-Misroute | Raw materials (217.71) classified here too |
| 45 | Wages | B(2021) | 6.38 | 14.10 | 121% | H-Misroute | Employee benefits + wages double-counted |
| 45 | Wages | C(2022) | 10.32 | 22.22 | 115% | H-Misroute | `=11.98+10.24` — two wage totals summed |
| 45 | Wages | D(2023) | 12.53 | 27.97 | 123% | H-Misroute | Sub-breakdowns of wages all individually classified |
| 56 | Depreciation (Mfg) | B(2021) | 4.07 | 13.52 | 232% | D-Duplicate | `=4.07+4.07+1.31+4.07` — same 4.07 appears 3x |
| 56 | Depreciation (Mfg) | C(2022) | 3.92 | 67.83 | 1631% | H-Misroute | Admin depreciation items all routed to Mfg |
| 56 | Depreciation (Mfg) | D(2023) | 4.30 | 61.89 | 1339% | H-Misroute | Same as above |
| 59 | FG Closing Balance | B(2021) | 3.01 | 9.98 | 231% | H-Misroute | `=6.95+3.03` — raw material inventory added |
| 59 | FG Closing Balance | C(2022) | 3.40 | 11.45 | 237% | H-Misroute | `=3.40+8.05` — stores inventory added |
| 59 | FG Closing Balance | D(2023) | 1.81 | 18.64 | 929% | H-Misroute | `=1.81+16.83` — raw material inventory added |
| 67 | Salary/Staff | C(2022) | 1.66 | 15482.98 | 930144% | F-Unit+Misroute | `=15471+11.98` — 15471 is raw lakhs, not crores |
| 68 | Rent/Rates/Taxes | B(2021) | 0.10 | 18.58 | 18858% | H-Misroute | Large rent (18.54 Cr) from wrong source |
| 68 | Rent/Rates/Taxes | C(2022) | 0.09 | 41.24 | 44054% | H-Misroute | 41.24 lakhs not converted |
| 68 | Rent/Rates/Taxes | D(2023) | 0.07 | 92.91 | 139618% | H-Misroute | `=46.48+46.48` — duplicate + misrouted |
| 70 | Ads/Sales Promotions | C(2022) | 3.21 | 240.24 | 7388% | H-Misroute | `=237.03+3.21` — 237 Cr misrouted item |
| 71 | Others (Admin) | B(2021) | 2.31 | 285.19 | 12240% | H-Misroute | Massive catchall — 103.77 Cr misrouted item |
| 71 | Others (Admin) | C(2022) | 3.38 | 2173.27 | 64227% | H-Misroute | Multiple large items dumped here |
| 71 | Others (Admin) | D(2023) | 1.68 | 759.78 | 45258% | H-Misroute | 258.44 Cr misrouted item |
| 73 | Audit Fees/Directors | C(2022) | empty | 30942.00 | - | F-Unit | `=15471+15471` — raw lakhs not converted |
| 83 | Interest on TL | B(2021) | 1.30 | 0.15 | 88% | H-Misroute | Most interest not classified here |
| 83 | Interest on TL | D(2023) | 1.43 | 0.18 | 87% | H-Misroute | Same — bulk of interest missing |
| 85 | Bank Charges | all FYs | ~0.1 | ~3 | 2000%+ | D-Duplicate | `=1.95+1.95-1.95+0.09` — duplicate add/subtract pattern |
| 99 | Income Tax | B(2021) | 0.02 | 2.31 | 12616% | H-Misroute | `=1.01+1.30` — deferred tax items routed here |
| 99 | Income Tax | C(2022) | 2.20 | 6.37 | 190% | H-Misroute | Multiple tax items aggregated |
| 131 | WC Bank Finance 1 | B(2021) | 11.13 | 26.60 | 139% | H-Misroute | Term loans classified as WC |
| 137 | TL Balance > 1yr | C(2022) | 12.76 | 908.79 | 7021% | H-Misroute | `=...+446.82+447.64` — huge misrouted items |
| 162 | Gross Block | B(2021) | 45.90 | 27.27 | 41% | D-Aggregation | Missing tangible assets; only 27.27 captured |
| 162 | Gross Block | C(2022) | 49.86 | 54.64 | 10% | D-Duplicate | `=27.32+27.32` — same value twice |
| 201 | Finished Goods (BS) | all FYs | ~2-3 | ~9-18 | 1600%+ | H-Misroute | Links to Row 59 which has raw material leak |
| 206 | Domestic Receivables | all FYs | 17-35 | 33-55 | 58-242% | D-Duplicate | Receivable amounts counted 2-3x |
| 212 | Cash on Hand | all FYs | ~0.01 | ~2-6 | 14000%+ | H-Misroute | Bank balances routed to Cash on Hand |
| 213 | Bank Balances | C(2022) | 0.02 | 11.28 | 67852% | H-Misroute | 11.28 lakhs raw value |
| 242 | Sundry Creditors | B(2021) | 10.31 | 3.18 | 69% | H-Misroute | `=10.31-7.13` — advance deducted wrongly |
| 249 | Creditors for expenses | C/D | ~0.5-1 | ~16-18 | 1500%+ | H-Misroute | Other payables dumped here |
| 250 | Other current liabilities | C(2022) | 4.65 | 33.57 | 622% | H-Misroute | Multiple large items misrouted |

## 4. Missing Cells (53 cells — GT has value, generated empty)
| Row | CMA Field | FYs Missing | Expected Range | Possible Cause |
|-----|-----------|-------------|----------------|----------------|
| 23 | Export Sales | B, D | 7.44-8.86 | Export revenue not classified separately from domestic |
| 30 | Interest Received | B, C, D | 0.06-0.08 | Small amount; not extracted or classified to wrong row |
| 32 | Gain on Exchange Fluctuations | C, D | 0.03-0.15 | Not extracted or classified elsewhere |
| 48 | Power/Coal/Fuel | C | 0.98 | FY2022 power costs not classified |
| 83 | Interest on TL | C | 1.47 | FY2022 interest entirely missing |
| 84 | Interest on WC | C | 1.27 | FY2022 interest entirely missing |
| 100 | Deferred Tax Liability (P&L) | B, D | 0.08-0.26 | Not classified |
| 123 | Share Premium | B, C, D | 0.96 | All FYs missing — not extracted from BS |
| 132 | WC Bank Finance 2 | C | 1.47 | Second bank not identified |
| 152 | Unsecured Quasi Equity | B, C, D | 4.13 | All FYs — director loans not classified |
| 159 | Deferred Tax (BS) | B, C, D | 0.82-1.16 | All FYs — not extracted |
| 163 | Less Accum Depreciation | B | 18.63 | FY2021 depreciation not captured |
| 194 | Raw Material Indigenous (inv) | B, C, D | 6.95-16.83 | All FYs — inventory not classified separately |
| 198 | Stores Indigenous (inv) | B, C, D | 0.006-0.018 | All FYs — very small, not extracted |
| 207 | Export Receivables | B, C, D | 0.59-1.62 | All FYs — not split from domestic |
| 208 | Debtors > 6 months | B, D | 0.008-0.066 | Not extracted from aging schedule |
| 215 | Other FD | B, C, D | 0.63-1.14 | Fixed deposits not classified |
| 222 | Prepaid Expenses | C | 0.13 | Not extracted |
| 236 | Advances to cap goods | C, D | 0.17-0.42 | Not classified |
| 237 | Security deposits | B, C, D | 0.25-0.36 | All FYs — not classified |
| 244 | Provision for Tax | B | 0.32 | Not classified |
| 246 | Other statutory liabilities | B, C, D | 0.49-1.34 | All FYs — not classified |

## 5. Multi-Item Cell Breakdowns (key examples)
| Row | CMA Field | FY | Formula | Components | Sum | GT | Match? |
|-----|-----------|-----|---------|------------|-----|-----|--------|
| 22 | Domestic Sales | B | `=105.43+0.55+105.43+123.97` | 4 items (1 dup) | 335.38 | 96.58 | NO |
| 22 | Domestic Sales | C | `=237.08+278.31+278.32+237.08` | 4 items (1 dup) | 1030.79 | 234.64 | NO |
| 42 | Raw Materials | B | `=84.35+6.95` | 2 items | 91.30 | 84.35 | NO — 6.95 is inventory |
| 44 | Stores/Spares | B | `=-0.01+84.35+1.77` | 3 items | 86.11 | 1.76 | NO — 84.35 is raw materials |
| 45 | Wages | B | `=6.68-0.06-0.09+0.80+0.32+0.23+0.08+5.60+0.54` | 9 items | 14.10 | 6.38 | NO — sub-items from Notes |
| 56 | Depreciation | B | `=4.07+4.07+1.31+4.07` | 4 items (3 dup) | 13.52 | 4.07 | NO |
| 67 | Salary | C | `=15471+11.98` | 2 items | 15482.98 | 1.66 | NO — 15471 is lakhs |
| 71 | Others Admin | C | `=448.13+5+3.09+228.60+...` | 20+ items | 2173.27 | 3.38 | NO — dump bucket |
| 137 | TL > 1yr | C | `=...+446.82+447.64` | 12 items | 908.79 | 12.76 | NO — huge misroutes |

## 6. Unit Conversion Verification
| Row | CMA Field | GT B(2021) | GT C(2022) | GT D(2023) | Gen B | Gen C | Gen D | Same Magnitude? |
|-----|-----------|------------|------------|------------|-------|-------|-------|-----------------|
| 22 | Domestic Sales | 96.58 | 234.64 | 256.95 | 335.38 | 1030.79 | 1103.10 | NO — Gen C is 4x |
| 42 | Raw Materials | 84.35 | 196.50 | 217.74 | 91.30 | 204.47 | 234.54 | ~OK (close) |
| 45 | Wages | 6.38 | 10.32 | 12.53 | 14.10 | 22.22 | 27.97 | ~OK (2x off all) |
| 83 | Interest on TL | 1.30 | 1.47 | 1.43 | 0.15 | 0.00 | 0.18 | NO — Gen ~0 |
| 99 | Income Tax | 0.02 | 2.20 | 1.76 | 2.31 | 6.37 | 3.58 | NO |
| 116 | Share Capital | 3.09 | 3.09 | 3.09 | 3.09 | 3.09 | 3.09 | **YES** |
| 162 | Gross Block | 45.90 | 49.86 | 53.19 | 27.27 | 54.64 | 60.88 | NO — Gen B low |
| 206 | Domestic Receivables | 17.92 | 34.70 | 15.48 | 32.63 | 54.89 | 52.93 | NO — Gen 2-3x |
| 213 | Bank Balances | 0.64 | 0.02 | 0.00 | -1.14 | 11.28 | 9.81 | NO — wildly off |
| 242 | Sundry Creditors | 10.31 | 12.79 | 14.29 | 3.18 | 15.28 | 15.79 | NO — Gen B low |

**RED FLAG**: FY2022 (lakhs source) has specific unit conversion failures for at least 10 rows where raw lakhs values appear instead of crores conversion.

## 7. Formula Rows (excluded from accuracy)
38 formula/subtotal rows have values in the ground truth but are NOT data-entry rows. These are computed by Excel macros and are **excluded from accuracy calculation**.

Key formula rows:
| Row | Label | Note |
|-----|-------|------|
| 24 | Sub Total (Sales) | =Row 22 + Row 23 |
| 26 | Net Sales | =Row 24 - Row 25 |
| 52 | Mfg Costs subtotal | Sum of rows 41-51 |
| 57 | Cost of Production | =Row 52 + Row 55 + Row 56 |
| 61 | Cost of Goods Sold | =Row 57 + Row 60 |
| 80 | Total Operating Expenses | Sum of admin + selling |
| 96 | Profit Before Tax | Computed from revenue - expenses |
| 104 | Net Profit After Tax | Computed |
| 109 | Balance carried to BS | =Row 104 + Row 106 - Row 107 - Row 108 |
| 260 | Total Assets | Sum of all asset rows |
| 261 | Total Liabilities | Sum of all liability rows |

## 8. Doubt-Related Cells
All 17 doubt items from the E2E test were **correctly resolved as UNCLASSIFIED** (excluded). They were all:
- Cash flow statement subtotals (5)
- P&L computed totals like PBT/PAT (4)
- Note-level loan/bank facility names (3)
- Aging schedule buckets (4)
- Related party names (2)

One exception: "Cash & Bank Balances" (FY2022, 175.03 lakhs) was approved as "Cash on Hand" (Row 212). This contributed to the Cash on Hand misroute — 175.03 lakhs = 1.75 crores, which shows up in the formula `=1.75+2.90+1.75`.

## 9. Error Breakdown by Type
| Error Type | Count | Key Examples |
|------------|-------|----------|
| **I - Missing Item** | **56** | Export Sales, Interest Received, Share Premium, Unsecured Quasi Equity, Deferred Tax, Security Deposits, Other Statutory Liabilities |
| **H - Misroute** | **48** | Raw Materials in Stores row, Admin expenses in wrong rows, Bank balances in Cash, Interest TL nearly empty |
| **D - Aggregation** | **28** | Raw Materials + inventory, Wages sub-items, Depreciation duplicates |
| **D - Duplicate** | **25** | Domestic Sales counted 2-3x, Depreciation same value 3x, Receivables doubled |
| **F - Unit Error** | **~10** | FY2022 Salary 15471 lakhs, Audit Fees 30942, Others Admin FY2022 |
| Total errors | **157** | Out of 186 cells with GT values |

## 10. Key Ground Truth Values (sanity check)
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

## 11. Overall Verdict

**Data-entry accuracy: 8.6% (16/186)**
**Target: >= 85%**
**Result: FAIL**

### Summary

The CMA Excel generation pipeline produces a structurally correct file (macros, sheets, headers all intact) but the **data content is severely inaccurate**. Only 16 out of 186 data-entry cells match the ground truth within 2% tolerance. The failures stem from three systemic bugs, not one-off classification errors:

1. **Duplicate extraction (25 errors)**: The same line item is extracted from multiple places (P&L face, Notes to Accounts, Schedules) and all copies are summed into the same CMA cell. For example, "Revenue from Operations" appears in the P&L, in Note 28, and in the Schedule — the app sums all three instead of deduplicating. This causes values to be 2-4x the correct amount.

2. **Cross-row misclassification (48 errors)**: Items are classified to the wrong CMA row. The worst cases are "catch-all" rows like Others (Admin) Row 71 which received 2173 Cr in FY2022 (expected: 3.38 Cr). Raw materials and stores are cross-contaminated. Employee benefits sub-items are each classified independently instead of recognizing the parent total.

3. **FY2022 unit conversion failures (~10 errors)**: FY2022 source documents are in lakhs, requiring division by 100 to convert to crores. Several values bypass this conversion entirely, resulting in values that are 50-9000x too large.

### Priority Fixes (in order of impact)

1. **De-duplicate extracted items before classification** — When the same amount appears in both a P&L face and a Note/Schedule, keep only the parent P&L amount. This single fix would resolve ~25 duplicate errors and improve Domestic Sales, Depreciation, Receivables, and Inventory accuracy.

2. **Fix classification of Raw Materials vs Stores vs Inventory** — The classifier confuses:
   - Raw Materials Consumed (P&L Row 42) vs Raw Material Inventory (BS Row 194)
   - Stores & Spares Consumed (P&L Row 44) vs Stores Inventory (BS Row 198)
   - Finished Goods Closing (P&L Row 59) vs FG Inventory (BS Row 201)
   Add golden rules to route inventory amounts to BS rows and consumption amounts to P&L rows.

3. **Fix FY2022 lakhs→crores conversion** — Audit the unit conversion pipeline for FY2022. At least 10 values are being written in raw lakhs. Check whether the conversion divisor is being applied to all classified items or only to some.

4. **Fix catch-all "Others" rows** — Row 71 (Others Admin) is receiving hundreds of crores of misrouted items. The classifier needs stricter routing rules so that only genuinely unclassifiable admin items land here.

5. **Add missing BS items to classification rules** — 53 cells are entirely missing. Key gaps: Export Receivables, Share Premium, Unsecured Quasi Equity, Deferred Tax (BS), Security Deposits, Other Statutory Liabilities, Fixed Deposits. These likely exist in the extraction but have no fuzzy/golden rule matches.

6. **Fix Interest on Term Loans classification** — Row 83 shows only 0.15 Cr (expected 1.30 Cr). The bulk of interest expense is not being routed to the correct TL vs WC split.
