# BCIPL CMA Excel Comparison Report (v3 — New AI-Only Pipeline)
**Date:** 2026-04-05
**Generated file:** BCIPL_generated_CMA_newpipeline.xlsm (109,439 bytes)
**Ground truth:** CMA BCIPL 12012024.xls (581,120 bytes)
**Output unit:** Crores
**Source units:** FY2021 = rupees, FY2022 = lakhs, FY2023 = rupees
**Pipeline:** AI-only (ScopedClassifier via DeepSeek V3) — no regex, golden rules, or fuzzy matching
**v1 baseline:** 8.6% accuracy (16/186) — 5-tier pipeline, first run
**v2 baseline:** 10.8% accuracy (20/186) — 5-tier pipeline with dedup/doubt fixes

**NOTE:** The v3 generated file has no cached formula values (never opened in Excel). Formulas like `=105.43+0.95+123.97+104.97` were evaluated programmatically. 44 formulas with cell references (e.g., `=SUM(C75:C77)`, `=C214`) could not be evaluated — those cells count as empty.

---

## 1. Structure Verification
| Check | Result | Details |
|-------|--------|---------|
| File format (.xlsm) | **PASS** | Correct format |
| VBA macros present | **PASS** | `vba_archive` is not None |
| INPUT SHEET exists | **PASS** | Present in generated file |
| Client name (Row 7) | **PASS** | Gen: "BCIPL" |
| Years (Row 8 B-D) | **PASS** | [2021, 2022, 2023] |
| Nature (Row 10 B-D) | **PASS** | ["audited", "audited", "audited"] |
| Units (Row 13 B) | **CHECK** | Gen: "In " (truncated — missing "crs") — same as v1/v2 |
| Projection years (E-H) | **PASS** | [2024, 2025, 2026, 2027] |
| Projection formulas preserved | **N/A** | Not in V1 scope |

---

## 2. Data-Entry Accuracy Summary

| Metric | Count |
|--------|-------|
| Total data-entry rows mapped | 130 |
| Total data-entry cells checked (130 rows x 3 FYs) | 390 |
| GT has value (non-empty, non-zero) | 186 |
| Matching (within 2%) | **7** |
| Mismatched | **79** |
| Missing (GT has value, generated empty) | **100** |
| Extra (generated has value, GT empty) | 13 |
| Both empty | 191 |
| **Data-entry accuracy** | **3.8% (7/186)** |

---

## 3. v1 vs v2 vs v3 Three-Way Comparison

### Overall Metrics
| Metric | v1 | v2 | v3 | v1→v2 | v2→v3 |
|--------|-----|-----|-----|-------|-------|
| **Data-entry accuracy** | **8.6% (16/186)** | **10.8% (20/186)** | **3.8% (7/186)** | +2.2pp | **-7.0pp** |
| Matching cells | 16 | 20 | 7 | +4 | **-13** |
| Mismatched | 101 | 25 | 79 | -76 | **+54** |
| Missing (GT has, gen empty) | 56 | 141 | 100 | +85 | -41 |
| Extra (gen has, GT empty) | 36 | 6 | 13 | -30 | +7 |
| Both empty | 168 | 198 | 191 | +30 | -7 |

### Key Cell Comparisons (v1 vs v2 vs v3)
| Row | CMA Field | FY | GT | v1 | v2 | v3 | v3 Assessment |
|-----|-----------|-----|-----|-----|-----|-----|--------------|
| 22 | Domestic Sales | B(2021) | 96.58 | 335.38 (247%) | EMPTY | **335.32 (247%)** | **v1 bug returned** — duplicate counting back |
| 22 | Domestic Sales | C(2022) | 234.64 | 1030.79 (339%) | EMPTY | **752.43 (221%)** | Slightly less duplicated than v1, still 3x off |
| 22 | Domestic Sales | D(2023) | 256.95 | 1103.10 (329%) | EMPTY | **841.98 (228%)** | Same pattern |
| 42 | Raw Materials | B(2021) | 84.35 | 91.30 (8%) | EMPTY | **165.42 (96%)** | **Worse than v1** — doubled instead of +8% |
| 42 | Raw Materials | C(2022) | 196.50 | 204.47 (4%) | EMPTY | **393.93 (100%)** | Exactly doubled |
| 44 | Stores/Spares | B(2021) | 1.76 | 86.11 (4785%) | EMPTY | EMPTY | Stayed empty (better than v1) |
| 45 | Wages | B(2021) | 6.38 | 14.10 (121%) | EMPTY | **8.01 (26%)** | Better than v1's 121%, but still 26% off |
| 45 | Wages | C(2022) | 10.32 | 22.22 (115%) | EMPTY | **24.27 (135%)** | Worse than v1 |
| 56 | Depreciation Mfg | B(2021) | 4.07 | 13.52 (232%) | EMPTY | **4.07 (0.1%)** | **MATCH! Best cell in v3** |
| 56 | Depreciation Mfg | C(2022) | 3.92 | 67.83 (1631%) | EMPTY | **61.58 (1472%)** | Massive misroute returned |
| 67 | Salary/Staff | C(2022) | 1.66 | 15482.98 | EMPTY | **11.98 (620%)** | Better than v1's unit error, but 7x off |
| 71 | Others Admin | B(2021) | 2.31 | 285.19 | EMPTY | **136.83 (5821%)** | Dump bucket back (smaller but still huge) |
| 71 | Others Admin | C(2022) | 3.38 | 2173.27 | EMPTY | **86.90 (2472%)** | Significantly less than v1's 2173, still 26x off |
| 83 | Interest on TL | B(2021) | 1.30 | 0.15 (88%) | 0.15 (88%) | **3.73 (187%)** | Now OVER-counted instead of under-counted |
| 99 | Income Tax | C(2022) | 2.20 | 6.37 (190%) | EMPTY | **2.19 (0.5%)** | **MATCH! New in v3** |
| 116 | Share Capital | B(2021) | 3.09 | 3.09 (0%) | 3.09 (0%) | **3.90 (26%)** | **Regressed** from exact match |
| 116 | Share Capital | C(2022) | 3.09 | 3.09 (0%) | 3.09 (0%) | **11.18 (261%)** | Catastrophic: `=3.09+3.09+5` |
| 137 | TL > 1yr | C(2022) | 12.76 | 908.79 | EMPTY | **18.36 (44%)** | Much better than v1's 909, but still 44% off |
| 162 | Gross Block | all | 45-53 | 27-55 | 27-30 | **27-30** | Same as v2 — tangible assets still missing |
| 198 | Stores Inv | C(2022) | 0.009 | N/A | EMPTY | **599.14 (7M%)** | **Catastrophic** — raw materials leaking |
| 206 | Dom Receivables | B(2021) | 17.92 | 32.63 (82%) | 18.52 (3%) | **14.12 (21%)** | **Regressed from v2's near-match** |
| 206 | Dom Receivables | C(2022) | 34.70 | 54.89 (58%) | 36.32 (5%) | **18.57 (46%)** | Worse — subtracting something |
| 242 | Sundry Creditors | all | 10-14 | 3-15 | EMPTY | **EMPTY** | Still missing (same as v2) |

### Pipeline Error Profile Shift
| Error Profile | v1 | v2 | v3 |
|---------------|-----|-----|-----|
| **Dominant error** | Duplicates + Misroutes | Missing (too aggressive dedup) | Duplicates + Misroutes (v1 problems returned) |
| Duplicate counting | 25 cells affected | 0 | **~30+ cells** (regressed) |
| Dump bucket (Row 71) | 2173 Cr max | 0 | **137 Cr max** (partial regression) |
| Unit errors | ~10 cells | 2 | **~5 cells** (partial regression) |
| Missing cells | 56 | 141 | 100 |
| Worst single cell | 30,942 (93M%) | 6.55 (11K%) | **599.14 (7M%)** |

---

## 4. Matching Cells (7 cells within 2%)

| Row | CMA Field | FY | Expected | Got | Diff% | Formula |
|-----|-----------|-----|----------|-----|-------|---------|
| 56 | Depreciation (Manufacturing) | B(2021) | 4.0746 | 4.0700 | 0.1% | scalar |
| 99 | Income Tax provision | C(2022) | 2.2000 | 2.1900 | 0.5% | scalar |
| 100 | Deferred Tax Liability (P&L) | D(2023) | 0.2604 | 0.2600 | 0.2% | scalar |
| 136 | TL Repayable < 1yr | B(2021) | 3.0047 | 3.0000 | 0.2% | scalar |
| 136 | TL Repayable < 1yr | C(2022) | 4.1154 | 4.1200 | 0.1% | scalar |
| 136 | TL Repayable < 1yr | D(2023) | 5.0519 | 5.0500 | 0.0% | scalar |
| 172 | Other Intangible assets | D(2023) | 0.0804 | 0.0800 | 0.5% | scalar |

### Matches gained vs v2
- **NEW matches**: Depreciation Mfg B (was empty in v2), Income Tax C (was empty), Deferred Tax Liab D (was empty)
- **LOST from v2** (13 cells): Share Capital (B/C/D), Processing/Job Work C, Power/Fuel (B/D), Ads/Sales C, Brought Forward B, WC Bank 2 B, Advances to suppliers RM (B/C/D), Prepaid (B/D), Advances recoverable D, Advance from customers D, Intangible D stayed

**Net: -13 matches.** Most of the lost matches were clean single-source items in v2 that now have wrong values due to the AI + auto-correction pipeline summing multiple sources.

---

## 5. Mismatched Cells (79 — detailed)

### P&L Mismatches (49 cells)
| Row | CMA Field | FY | Expected | Got | Diff% | Formula | Error Type |
|-----|-----------|-----|----------|-----|-------|---------|------------|
| 22 | Domestic Sales | B | 96.58 | 335.32 | 247% | `=105.43+0.95+123.97+104.97` | D-Duplicate |
| 22 | Domestic Sales | C | 234.64 | 752.43 | 221% | `=237.08+278.32+237.03` | D-Duplicate |
| 22 | Domestic Sales | D | 256.95 | 841.98 | 228% | `=264.07+1.72+2.95+262.70+310.54` | D-Duplicate |
| 30 | Interest Received | B | 0.08 | 0.18 | 121% | `=-0.08+0.09+0.08+0.02+0.08-0.01` | D-Duplicate |
| 30 | Interest Received | C | 0.06 | 18.01 | 31005% | `=6.55+11.46` | F-Unit (lakhs) |
| 30 | Interest Received | D | 0.06 | 0.82 | 1175% | `=0.06-0.06+0.57+0.15+0.06+0.01+0.03` | H-Misroute |
| 34 | Others Non-Op Inc | B | 0.01 | 10.23 | 100K% | scalar | H-Misroute |
| 34 | Others Non-Op Inc | D | 0.15 | 8.05 | 5343% | scalar | H-Misroute |
| 42 | Raw Materials Ind | B | 84.35 | 165.42 | 96% | `=84.35+81.07` | D-Duplicate |
| 42 | Raw Materials Ind | C | 196.50 | 393.93 | 100% | `=196.42+197.51` | D-Duplicate |
| 42 | Raw Materials Ind | D | 217.74 | 461.02 | 112% | `=217.71+226.48+16.83` | D-Duplicate |
| 45 | Wages | B | 6.38 | 8.01 | 26% | `=-0.09-0.06+0.23+...+5.60+0.53` | D-Sub-items |
| 45 | Wages | C | 10.32 | 24.27 | 135% | `=10.24+11.98+2.05` | D-Duplicate |
| 45 | Wages | D | 12.53 | 15.48 | 24% | `=-0.19-0.12+...+11.54+1.15` | D-Sub-items |
| 49 | Others (Mfg) | B | 0.08 | 107.79 | 131K% | `=-0.01+103.77+...+1.22+0.80` | H-Misroute |
| 49 | Others (Mfg) | C | 0.16 | 232.09 | 146K% | `=228.60+3.49` | H-Misroute |
| 49 | Others (Mfg) | D | 0.03 | 8.19 | 25K% | `=0.12+0.03+...+4.39+2.26+...` | H-Misroute |
| 56 | Depreciation Mfg | C | 3.92 | 61.58 | 1472% | `=3.92+11.07+11.23+2.75+...` | H-Misroute |
| 56 | Depreciation Mfg | D | 4.30 | 51.91 | 1107% | `=4.30+11.14+2.75+...+8.48` | H-Misroute |
| 59 | FG Closing | B | 3.01 | -1.84 | 161% | scalar | H-Misroute |
| 59 | FG Closing | C | 3.40 | -1.84 | 154% | scalar | H-Misroute |
| 67 | Salary/Staff | B | 0.30 | 6.68 | 2127% | scalar | H-Misroute |
| 67 | Salary/Staff | C | 1.66 | 11.98 | 620% | scalar | H-Misroute |
| 67 | Salary/Staff | D | 1.26 | 13.79 | 999% | scalar | H-Misroute |
| 68 | Rent/Rates/Taxes | B | 0.10 | 0.14 | 43% | `=0.10+0.04` | D-Duplicate |
| 68 | Rent/Rates/Taxes | D | 0.07 | 0.20 | 201% | `=0.13+0.07` | D-Duplicate |
| 71 | Others (Admin) | B | 2.31 | 136.83 | 5821% | `=8.57+...+84.21+...+18.54+4.07+1.30+...` (20+ items) | H-Misroute (dump bucket) |
| 71 | Others (Admin) | C | 3.38 | 86.90 | 2472% | `=3.92+13.82+12.55+...+41.24+...` | H-Misroute (dump bucket) |
| 71 | Others (Admin) | D | 1.68 | 86.99 | 5093% | `=16.84+...+4.30+...+46.48+...` | H-Misroute (dump bucket) |
| 73 | Audit/Directors | B | 1.99 | 0.05 | 97% | `=0.03+0.02` | I-Partial |
| 83 | Interest on TL | B | 1.30 | 3.73 | 187% | `=1.95+0.48+1.15+0.15` | D-Duplicate + H-Misroute |
| 83 | Interest on TL | C | 1.47 | 4.06 | 175% | `=2.75+1.31` | D-Duplicate |
| 83 | Interest on TL | D | 1.43 | 5.59 | 292% | `=4.19+1.22+0.18` | D-Duplicate |
| 85 | Bank Charges | B | 0.09 | 0.74 | 744% | `=0.09+0.65` | H-Misroute (WC interest in bank charges) |
| 85 | Bank Charges | D | 0.17 | 2.06 | 1082% | `=1.89+0.17` | H-Misroute |
| 99 | Income Tax | D | 1.76 | 1.64 | 7% | scalar | D-Near (close) |
| 250 | Other current liab | B | 2.55 | 1.66 | 35% | `=0.32+0.05+0.02+0+1.27` | I-Partial |
| 250 | Other current liab | C | 4.65 | 3.38 | 27% | `=1.37+2.01` | I-Partial |
| 250 | Other current liab | D | 1.45 | 2.07 | 42% | `=-0.26+0.70+0.70+0.03+0.90` | H-Misroute |

### Balance Sheet Mismatches (30 cells)
| Row | CMA Field | FY | Expected | Got | Diff% | Formula | Error Type |
|-----|-----------|-----|----------|-----|-------|---------|------------|
| 116 | Share Capital | B | 3.09 | 3.90 | 26% | `=0.31+3.09+0.50` | D-Duplicate |
| 116 | Share Capital | C | 3.09 | 11.18 | 261% | `=3.09+3.09+5` | D-Duplicate + Misroute |
| 116 | Share Capital | D | 3.09 | 3.90 | 26% | `=0.31+0.50+3.09` | D-Duplicate |
| 131 | WC Bank 1 | B | 11.13 | 12.93 | 16% | `=12.03+0.90` | D-Duplicate (Bank 2 merged) |
| 131 | WC Bank 1 | C | 19.61 | 13.91 | 29% | scalar | I-Partial |
| 131 | WC Bank 1 | D | 12.15 | 9.07 | 25% | scalar | I-Partial |
| 137 | TL > 1yr | B | 16.68 | 20.82 | 25% | scalar | D-Duplicate |
| 137 | TL > 1yr | C | 12.76 | 18.36 | 44% | `=16.89+1.47` | D-Duplicate |
| 137 | TL > 1yr | D | 6.32 | 11.93 | 89% | `=10.46+1.47` | D-Duplicate |
| 159 | Deferred Tax BS | B | 1.16 | 3.48 | 201% | `=1.16+1.16+1.16` | **D-Triplicate** |
| 159 | Deferred Tax BS | C | 0.82 | 3.48 | 326% | `=1.16+1.16+1.16` | **D-Triplicate** |
| 159 | Deferred Tax BS | D | 1.08 | 3.24 | 201% | `=1.08+1.08+1.08` | **D-Triplicate** |
| 162 | Gross Block | B | 45.90 | 27.27 | 41% | scalar | I-Partial (tangible missing) |
| 162 | Gross Block | C | 49.86 | 27.32 | 45% | scalar | I-Partial |
| 162 | Gross Block | D | 53.19 | 30.44 | 43% | scalar | I-Partial |
| 163 | Accum Depreciation | C | 22.54 | 11.14 | 51% | `=1.87+9.27` | I-Partial |
| 163 | Accum Depreciation | D | 22.75 | 3.49 | 85% | `=1.87+1.62` | I-Partial |
| 165 | Capital WIP | B | 0.17 | -1.33 | 882% | `=-1.64-0.03+0.17+0.17` | H-Misroute |
| 165 | Capital WIP | C | 0.40 | -1.79 | 552% | `=-4.15+2.36` | H-Misroute |
| 165 | Capital WIP | D | 0.31 | -1.72 | 653% | `=-7.19+0.08+0.31+...` | H-Misroute |
| 172 | Other Intangible | B | 0.007 | 0.01 | 44% | scalar | D-Rounding |
| 172 | Other Intangible | C | 0.19 | 27.51 | 14206% | scalar | H-Misroute |
| 194 | Raw Material Inv | C | 8.05 | 11.46 | 42% | scalar | D-Partial |
| 198 | Stores Inv | B | 0.018 | 105.89 | 577K% | `=10+1.42+0.14+84.35+6.95+3.03` | **H-Catastrophic Misroute** |
| 198 | Stores Inv | C | 0.009 | 599.14 | 7M% | `=8.05+3.40-1.45+196.42+196.30+196.42` | **H-Catastrophic Misroute** |
| 198 | Stores Inv | D | 0.006 | 448.69 | 7.5M% | `=18.64-7.18+215.40+2.31+1.81+217.71` | **H-Catastrophic Misroute** |
| 206 | Dom Receivables | B | 17.92 | 14.12 | 21% | `=18.52-4.40` | D-Over-subtract |
| 206 | Dom Receivables | C | 34.70 | 18.57 | 46% | `=36.32-17.75` | D-Over-subtract |
| 206 | Dom Receivables | D | 15.48 | 36.35 | 135% | `=19.73+16.62` | D-Over-add |
| 212 | Cash on Hand | B | 0.014 | 1.75 | 12672% | scalar | H-Misroute |
| 213 | Bank Balances | C | 0.017 | 1.75 | 10442% | scalar | H-Misroute |
| 213 | Bank Balances | D | 0.003 | 1.16 | 46514% | scalar | H-Misroute |
| 221 | Advance Income Tax | B | 0.18 | 1.19 | 561% | `=1.07+0.12` | H-Misroute |
| 221 | Advance Income Tax | C | 0.45 | 2.38 | 427% | scalar | H-Misroute |
| 221 | Advance Income Tax | D | -0.11 | 1.83 | 1709% | `=1.57+0.26` | H-Misroute |
| 223 | Other Advances | B | 0.25 | 23.60 | 9527% | `=1.30+1.21-0.05+18.51+...` | H-Misroute (dump) |
| 223 | Other Advances | C | 0.29 | 44.60 | 15232% | `=36.32+1.34+2.11+...` | H-Misroute (dump) |
| 223 | Other Advances | D | 0.36 | 23.20 | 6428% | `=2.62+0.35+...+16.58+...` | H-Misroute (dump) |
| 238 | Other NC assets | B | 0.34 | 0.59 | 74% | `=0.25+0.34` | D-Duplicate |
| 249 | Creditors Expenses | D | 0.38 | 18.07 | 4653% | scalar | H-Misroute |

---

## 6. Missing Cells (100 — grouped by row)

### P&L Missing (55 cells)
| Row | CMA Field | FYs Missing | Expected Range | Has Formula? | Likely Cause |
|-----|-----------|-------------|----------------|-------------|--------------|
| 23 | Export Sales | B, C, D | 2.44-8.86 | `=B23*1.05` (unevaluable) | Revenue not split domestic/export |
| 32 | Gain on Exchange | C, D | 0.03-0.15 | - | Not classified |
| 34 | Others Non-Op Inc | C | 0.02 | - | Classified for B/D but not C |
| 44 | Stores/Spares Ind | B, C, D | 1.76-4.39 | `=0` | **Forced to zero** — items went to Row 198 or 49 instead |
| 46 | Processing/Job Work | B, C, D | 1.22-2.26 | `=0` | Forced to zero |
| 48 | Power/Fuel | B, C, D | 0.80-1.22 | `=0` | Forced to zero |
| 50 | Repairs Mfg | C, D | 0.22-0.42 | `=0` | Forced to zero |
| 58 | FG Opening | B, C, D | 1.19-3.40 | `=C59` (cross-ref) | Depends on Row 59 which is wrong |
| 59 | FG Closing | D | 1.81 | `=0` | Forced to zero |
| 63 | Depreciation (CMA) | B, C, D | 3.92-4.30 | `=D56` (cross-ref) | Depends on Row 56 |
| 64 | Other Mfg Exp (CMA) | B, C, D | 8.48-16.46 | `=D52-D41-...` (cross-ref) | CMA computed field |
| 68 | Rent/Rates/Taxes | C | 0.09 | `=0` | Forced to zero |
| 69 | Bad Debts | C, D | 0.001-0.09 | `=0` | Forced to zero |
| 70 | Ads/Sales | C, D | 3.21-6.78 | `=0` | Forced to zero |
| 72 | Repairs Admin | B | 0.05 | `=0` | Forced to zero |
| 75 | Misc Exp written off | C | 0.007 | - | Not classified |
| 84 | Interest on WC | B, C, D | 0.65-2.59 | `=0` | **All forced to zero** — interest items all went to Row 83 |
| 85 | Bank Charges | C | 0.15 | `=0` | Forced to zero |
| 91 | Loss on Exchange | B | 0.16 | - | Not classified |
| 99 | Income Tax | B | 0.02 | `=0` | Forced to zero |
| 100 | Deferred Tax Liab | B | -0.08 | `=0` | Forced to zero |
| 101 | Deferred Tax Asset | C | 0.34 | `=0` | Forced to zero |
| 106 | Brought forward | B, C, D | 4.26-12.90 | `=C109` (cross-ref) | Depends on computed row |

### Balance Sheet Missing (45 cells)
| Row | CMA Field | FYs Missing | Expected Range | Has Formula? | Likely Cause |
|-----|-----------|-------------|----------------|-------------|--------------|
| 122 | Balance from P&L | B, C, D | 6.05-17.08 | `=D109` (cross-ref) | Computed field |
| 123 | Share Premium | B, C, D | 0.96 | - | Not classified (same as v1/v2) |
| 132 | WC Bank 2 | B, C | 0.90-1.47 | - | Second bank not split |
| 152 | Unsecured Quasi Equity | B, C, D | 4.13 | - | Director loans not classified (same as v1/v2) |
| 153 | Unsecured LT Debt | D | 3.24 | - | Not classified |
| 163 | Accum Depreciation | B | 18.63 | - | Not classified for FY2021 |
| 194 | Raw Material Inv | B, D | 6.95-16.83 | - | Classified for C only; B/D items went to Row 198 |
| 201 | Finished Goods BS | B, C, D | 1.81-3.40 | `=D59` (cross-ref) | Depends on Row 59 |
| 207 | Export Receivables | B, C, D | 0.59-1.62 | - | Not split from domestic (same as v1/v2) |
| 208 | Debtors > 6 months | B, D | 0.01-0.07 | - | Not extracted |
| 212 | Cash on Hand | C, D | 0.01 | - | Not classified for C/D (B has wrong value) |
| 213 | Bank Balances | B | 0.64 | - | Not classified for FY2021 |
| 215 | Other FD | B, C, D | 0.63-1.14 | - | Not classified (same as v1/v2) |
| 219 | Advances recoverable | B, C, D | 0.04-2.20 | - | Not classified |
| 220 | Advances to suppliers RM | B, C, D | 0.35-1.24 | - | Not classified (was matching in v2!) |
| 222 | Prepaid Expenses | B, C, D | 0.12-0.14 | - | Not classified (was matching in v2!) |
| 232 | Debtors > 6mo NC | B, D | 0.01-0.07 | `=D208` (cross-ref) | Depends on Row 208 |
| 236 | Advances to cap goods | B, C, D | 0.17-1.17 | - | Not classified |
| 237 | Security deposits | B, C, D | 0.25-0.36 | - | Not classified (same as v1/v2) |
| 242 | Sundry Creditors | B, C, D | 10.31-14.29 | - | **All empty** (same as v2, regressed from v1) |
| 243 | Advance from customers | D | 0.90 | - | Not classified for D |
| 244 | Provision for Tax | B | 0.32 | - | Not classified |
| 246 | Other statutory liab | B, C, D | 0.48-1.34 | - | Not classified (same as v1/v2) |
| 249 | Creditors Expenses | C | 0.96 | - | Not classified for C |

---

## 7. Extra Cells (13 — generated has value, GT is empty)

| Row | CMA Field | FY | Got | Formula | Assessment |
|-----|-----------|-----|-----|---------|------------|
| 47 | Freight/Transport | D | 4.54 | scalar | Misclassified — likely belongs elsewhere |
| 73 | Audit/Directors | D | 0.09 | `=0.05+0.04` | Small amount, but GT is empty for D |
| 93 | Others Non-Op Exp | B | 1.75 | scalar | Misclassified item |
| 93 | Others Non-Op Exp | C | 17.40 | `=8.70+8.70` | Doubled — same 8.70 counted twice |
| 93 | Others Non-Op Exp | D | 12.38 | `=6.19+6.19` | Doubled — same 6.19 counted twice |
| 101 | Deferred Tax Asset | B | -0.08 | scalar | Close to GT's -0.077 but GT filed under Row 100 |
| 121 | General Reserve | B | 7.05 | scalar | GT has this in Reserve subtotals, not Row 121 |
| 121 | General Reserve | C | 13.89 | scalar | Same — misclassified reserves |
| 154 | Unsecured ST Debt | D | 0.74 | scalar | Same as v2 |
| 214 | FD under lien | B | 0.01 | scalar | Small — GT has this elsewhere |
| 214 | FD under lien | D | 0.01 | scalar | Small |
| 238 | Other NC assets | D | 0.38 | scalar | GT has this in FY2021 not FY2023 |
| 249 | Creditors Expenses | B | 4.35 | `=4.23+0.12` | Misclassified items |

---

## 8. Multi-Item Formula Breakdowns (key examples)

| Row | CMA Field | FY | Formula | Components | Sum | GT | Root Cause |
|-----|-----------|-----|---------|------------|-----|-----|------------|
| 22 | Domestic Sales | B | `=105.43+0.95+123.97+104.97` | 4 items | 335.32 | 96.58 | Revenue extracted from P&L + Notes + Schedules; no dedup |
| 22 | Domestic Sales | C | `=237.08+278.32+237.03` | 3 items (237 appears 2x) | 752.43 | 234.64 | Duplicate: 237.08 and 237.03 are same source |
| 42 | Raw Materials | B | `=84.35+81.07` | 2 items | 165.42 | 84.35 | Consumption (84.35) + purchase (81.07) summed |
| 42 | Raw Materials | C | `=196.42+197.51` | 2 items | 393.93 | 196.50 | Same pattern — doubled |
| 49 | Others Mfg | B | `=-0.01+103.77+0+0.24+1.77+1.22+0.80` | 7 items | 107.79 | 0.08 | 103.77 Cr = massive misroute (admin item in mfg) |
| 56 | Depreciation | C | `=3.92+11.07+11.23+2.75+11.14+8.88+2.12+1.99+8.48` | 9 items | 61.58 | 3.92 | All depreciation line items from Notes classified here |
| 71 | Others Admin | B | `=8.57+...+84.21+...+18.54+4.07+1.30+...` | 20+ items | 136.83 | 2.31 | Dump bucket: 84.21 Cr raw material, 18.54 rent, interest... |
| 116 | Share Capital | C | `=3.09+3.09+5` | 3 items | 11.18 | 3.09 | Share capital tripled (same value from 3 sources) + 5 Cr mystery |
| 159 | Deferred Tax | B | `=1.16+1.16+1.16` | 3 items (same value!) | 3.48 | 1.16 | **Exact triplication** — same amount from 3 sheets |
| 198 | Stores Inv | C | `=8.05+3.40-1.45+196.42+196.30+196.42` | 6 items | 599.14 | 0.009 | **Catastrophic**: raw materials (196 Cr x3) in stores inventory |
| 206 | Receivables | C | `=36.32-17.75` | subtraction | 18.57 | 34.70 | Subtracting instead of just reporting 36.32 |
| 223 | Other Advances | C | `=36.32+1.34+2.11+1.24+1.21+1.17+1.21` | 7 items | 44.60 | 0.29 | Receivables (36.32), loans, and random items dumped here |

---

## 9. Unit Conversion Verification

| Row | CMA Field | GT B(2021) | GT C(2022) | GT D(2023) | Gen B | Gen C | Gen D | Magnitude OK? |
|-----|-----------|------------|------------|------------|-------|-------|-------|---------------|
| 22 | Domestic Sales | 96.58 | 234.64 | 256.95 | 335.32 | 752.43 | 841.98 | OK (consistent 2-3x over) |
| 42 | Raw Materials | 84.35 | 196.50 | 217.74 | 165.42 | 393.93 | 461.02 | OK (consistent 2x) |
| 45 | Wages | 6.38 | 10.32 | 12.53 | 8.01 | 24.27 | 15.48 | **WARN** — C is 2.4x but B/D are 1.2x |
| 83 | Interest on TL | 1.30 | 1.47 | 1.43 | 3.73 | 4.06 | 5.59 | OK (consistent 2-4x over) |
| 99 | Income Tax | 0.02 | 2.20 | 1.76 | EMPTY | 2.19 | 1.64 | OK |
| 116 | Share Capital | 3.09 | 3.09 | 3.09 | 3.90 | 11.18 | 3.90 | **NO** — C is 3.6x, B/D are 1.3x |
| 162 | Gross Block | 45.90 | 49.86 | 53.19 | 27.27 | 27.32 | 30.44 | OK (consistent 0.6x) |
| 206 | Dom Receivables | 17.92 | 34.70 | 15.48 | 14.12 | 18.57 | 36.35 | **NO** — D/C swapped magnitude |
| 213 | Bank Balances | 0.64 | 0.02 | 0.00 | EMPTY | 1.75 | 1.16 | **NO** — Gen C/D wildly off |
| 242 | Sundry Creditors | 10.31 | 12.79 | 14.29 | EMPTY | EMPTY | EMPTY | N/A |

**Notable**: The v1-era FY2022 unit conversion errors (15471 lakhs, 30942) are NOT present in v3. Unit conversion appears to be working correctly for most items. The errors are classification/aggregation, not unit-based.

---

## 10. Doubt Resolution Impact Analysis

### Resolution Statistics
| Category | Count | Impact |
|----------|-------|--------|
| Section headers / subtotals → approved unclassified | 82 | **Correct** — these should not be classified |
| Bank / loan sub-accounts → approved unclassified | 102 | **Mostly correct** — but some had classifiable amounts |
| Auto-corrected via reference rules | 215 | **PROBLEM** — many corrections were wrong |
| Remaining → approved unclassified | 38 | Correct |

### Auto-Correction Problems
The 215 auto-corrected items are the primary source of v3's new errors. Examples of wrong corrections:

| Doubted Item | Corrected To | Actual Target | Impact |
|-------------|-------------|---------------|--------|
| "Long-term Borrowings" (20.82 Cr) | Row 137 (TL > 1yr) | Row 137 | Correct but duplicated (appears 3x from different sources) |
| "Deferred Tax Liabilities (Net)" (1.16 Cr) | Row 159 | Row 159 | Correct but **triplicated** (`=1.16+1.16+1.16`) |
| "Gross Revenue from operations" (multiple) | Row 22 (Domestic Sales) | Row 22 | Correct field but creates duplicates |
| "Depreciation & Amortization" | Row 71 (Others Admin) | Row 56 or Row 63 | **Wrong row** — should be depreciation, not admin |
| "Profit on sale of Fixed Asset" | Row 71 (Others Admin) | Row 31 or Row 177 | **Wrong row** |
| "Inventories" | Row 198 (Stores Indigenous) | Row 194 or 200/201 | **Wrong row** — raw materials leaking into stores |

**Root cause**: The auto-correction matching rules don't distinguish between:
1. The same item from different source sheets (creates duplicates)
2. Different items with similar names (creates misroutes)
3. Parent vs child items in a hierarchy (creates double-counting)

---

## 11. Error Breakdown by Type (Three-Way)

| Error Type | v1 | v2 | v3 | Trend |
|------------|-----|-----|-----|-------|
| **D - Duplicate** | 25 | 0 | **~30** | Regressed to worse than v1 |
| **H - Misroute** | 48 | 8 | **~35** | Partial regression |
| **I - Missing** | 56 | 141 | **100** | Improved from v2, worse than v1 |
| **I - Partial** | 0 | 4 | **~8** | New category |
| **F - Unit Error** | ~10 | 2 | **~3** | Improved (mostly fixed) |
| **D - Near (3-10% off)** | 0 | 11 | **~5** | Some near-misses |
| **H - Catastrophic (>1000x)** | 3 (30942) | 0 | **6** (599, 448, 106) | **New catastrophic misroutes** |
| Total error cells | 139 | 155 | **179** | **Worst of all three versions** |

---

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

---

## 13. Overall Verdict

**Data-entry accuracy: 3.8% (7/186)**
**Target: >= 85%**
**Result: FAIL**

### v1 vs v2 vs v3 Scorecard

| Aspect | v1 | v2 | v3 | Best |
|--------|-----|-----|-----|------|
| **Accuracy** | 8.6% | **10.8%** | 3.8% | **v2** |
| Wrong values (mismatches) | 101 | **25** | 79 | **v2** |
| Missing values | **56** | 141 | 100 | **v1** |
| Worst single cell error | 30,942 | **6.55** | 599.14 | **v2** |
| Unit errors | ~10 | **2** | ~3 | **v2** |
| Duplicates | 25 | **0** | ~30 | **v2** |
| Dump bucket max (Row 71) | 2,173 | **0** | 137 | **v2** |
| Receivables accuracy | 58-242% | **3-7%** | 21-135% | **v2** |
| Cells populated (non-empty) | 153 | 51 | **101** | v1 (but v1 values wrong) |
| Catastrophic errors (>1000x) | 3 | **0** | 6 | **v2** |
| **Overall** | | | | **v2 is best** |

### Summary

**v3 is a regression across all dimensions.** The AI-only pipeline (ScopedClassifier + auto-corrected doubts) performed worse than both the v1 original pipeline and the v2 dedup-fixed pipeline. The specific failures:

1. **Duplicate counting returned** (~30 cells): The old multi-tier pipeline's dedup (fixed in v2) is gone. Items extracted from P&L face, Notes, and Schedules are all classified independently and summed. Row 22 Domestic Sales = 335 Cr (expected 97 Cr) because revenue is counted 3-4x from different document sections.

2. **Misroutes returned** (~35 cells): Without golden rules and fuzzy matching providing targeted routing, the AI classifier sends items to wrong rows. Row 49 (Others Manufacturing) received 232 Cr in FY2022 (expected 0.16 Cr). Row 198 (Stores Indigenous) received 599 Cr (expected 0.009 Cr).

3. **Auto-correction created new errors** (215 corrections): The doubt resolution auto-matched items by name without deduplication awareness. "Deferred Tax Liabilities" was tripled (`=1.16+1.16+1.16`). Revenue items were corrected to Row 22 from all sources.

4. **Critical rows now catastrophically wrong**: Row 198 Stores Inventory: 599 Cr (GT: 0.009 Cr) = 6,966,644% off — raw material consumption, inventory, and purchase amounts all classified as stores inventory. This is the worst single error across all three versions.

5. **v2's best improvements were lost**: Receivables (was 3-7% off in v2, now 21-135%), Share Capital (was exact match, now 26-261%), all 13 cells that matched in v2 but not v1 are now lost.

### Diagnosis: Why v3 Failed

The fundamental issue is **removing structured tiers without replacing their functions**:

| Function | v2 (5-tier) | v3 (AI-only) |
|----------|------------|-------------|
| **Deduplication** | Cross-sheet dedup (overly aggressive but present) | **None** — same item from 3 sources creates 3 entries |
| **Precision routing** | Golden rules v2 (594 rules) + fuzzy matching | **None** — AI guesses, doubts 75%, auto-correction maps by name |
| **Hierarchy awareness** | Learned mappings knew parent vs child items | **None** — "Employee Benefits" and "Salaries" both classified independently |
| **Guard rails** | Unroutable items → doubt → manual review | Auto-correction blindly applies reference rules |

### Recommended Next Steps

**Do NOT deploy v3.** Roll back to v2 pipeline and apply targeted fixes:

1. **Fix v2's dedup to keep-one-copy** (est. +40-60 cells from v2 baseline)
   The v2 dedup removes ALL copies. Fix it to keep the P&L/BS face value and only remove Note/Schedule duplicates. This was the #1 priority fix from v2 and would have been more impactful than rebuilding the entire pipeline.

2. **Re-enable learned mappings** (est. +10-20 cells)
   v3 report confirms 0% learned mappings consulted. The learning system has 594 golden rules that were providing 38% coverage — re-enable them.

3. **Improve AI classifier's hierarchy awareness**
   When "Employee Benefits" has sub-items "Salaries", "Contribution to PF", etc., classify ONLY the parent OR the children, never both. This requires extraction-level metadata about parent-child relationships.

4. **Add dedup at classification level, not just extraction**
   Even if the same item reaches classification from multiple sources, the classifier should detect "I've already classified 84.35 Cr to Row 42 for FY2021" and skip the duplicate.
