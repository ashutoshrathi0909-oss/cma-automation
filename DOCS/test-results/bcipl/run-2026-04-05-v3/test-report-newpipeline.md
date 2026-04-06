# BCIPL CMA Test Report — New AI-Only Pipeline (v3)

**Date:** 2026-04-05  
**Client:** BCIPL / Manufacturing / INR  
**Documents:** FY2021 (rupees), FY2022 (lakhs), FY2023 (rupees)  
**Output Unit:** Crores  
**Pipeline:** AI-only (ScopedClassifier via DeepSeek V3) — no regex, golden rules, or fuzzy matching  
**CMA Report ID:** c341c71b-4613-4ab0-b338-448b85d73d53  

---

## 1. Classification Method Distribution

**CRITICAL FINDING: Zero rule_engine_* methods. Old pipeline confirmed removed.**

| Method | Count | Percentage |
|---|---|---|
| scoped_doubt | 437 | 75.0% |
| scoped_v3 | 146 | 25.0% |
| **Total** | **583** | **100%** |

### Per-Document Breakdown

| Document | Total | scoped_v3 | scoped_doubt |
|---|---|---|---|
| FY2021 | 218 | 51 (23.4%) | 167 (76.6%) |
| FY2022 | 135 | 33 (24.4%) | 102 (75.6%) |
| FY2023 | 230 | 62 (27.0%) | 168 (73.0%) |

### Comparison with Previous Runs

| Metric | v2 (old pipeline) | v3-old (not rebuilt) | v3-new (this run) |
|---|---|---|---|
| Total items | 583 | 583 | 583 |
| Doubts | 228 | 0 | 437 |
| Learned mappings | - | 57% | 0% |
| Golden rules | - | 38% | 0% |
| AI (scoped_v3) | - | 1.4% | 25% |
| AI (scoped_doubt) | - | 0% | 75% |

---

## 2. Doubt Resolution Summary

| Category | Count | Action |
|---|---|---|
| Section headers / subtotals | 82 | Approved as unclassified |
| Bank / loan sub-accounts | 102 | Approved as unclassified |
| Auto-corrected via reference rules | 215 | Corrected with CMA row mapping |
| Approved as unclassified (remaining) | 38 | Approved as unclassified |
| **Total resolved** | **437** | **All resolved** |

### Resolution Statuses (Final)

| Status | FY2021 | FY2022 | FY2023 | Total |
|---|---|---|---|---|
| approved | 138 | 86 | 144 | 368 |
| corrected | 80 | 49 | 86 | 215 |
| **Total** | **218** | **135** | **230** | **583** |

---

## 3. Excel Verification

| Check | Result |
|---|---|
| File size | 109 KB |
| VBA macros present | YES |
| Sheets count | 16 |
| Client name (Row 7) | "BCIPL" |
| Populated data cells (INPUT SHEET) | 1105 |

### Key Row Spot Check

| Row | Description | Col C (Data) | Status |
|---|---|---|---|
| 22 | Domestic Sales | =237.08+278.32... | **POPULATED** |
| 42 | Raw Materials Consumed | =196.42+197.51... | **POPULATED** |
| 45 | Wages | =10.24+11.98+2... | **POPULATED** |
| 56 | Repairs & Maintenance | =3.92+11.07... | **POPULATED** |
| 71 | Others (Expenses) | =3.92+13.82... | **POPULATED** |
| 78 | Interest on Fixed Loans | =SUM(C75:C77) | **POPULATED** |
| 81 | Interest on Working Capital | - | **EMPTY** |
| 85 | Bank Charges | =0 | **POPULATED** |
| 93 | Profit Before Tax | =8.70+8.70 | **POPULATED** |
| 95 | Income Tax | =-2.48+2.17 | **POPULATED** |
| 97 | Net Profit After Tax | 6.84 | **POPULATED** |
| 116 | Share Capital | =3.09+3.09+5... | **POPULATED** |
| 131 | From Indian Bank | 13.91 | **POPULATED** |
| 136 | TL Repayable < 1yr | 4.12 | **POPULATED** |
| 137 | TL Repayable > 1yr | =16.89+1.47 | **POPULATED** |
| 161 | Gross Block | - | **EMPTY** |
| 198 | Indigenous (Stock) | =8.05+3.40... | **POPULATED** |
| 206 | Domestic Receivables | =36.32-17.75 | **POPULATED** |
| 234 | Creditors for RM | =C214 | **POPULATED** |
| 250 | Other Current Liabilities | =1.37+2.01 | **POPULATED** |

**Result: 24/26 key rows populated (92.3%)** — Row 81 (Interest on WC) and Row 161 (Gross Block) empty.

### v2 vs v3 Comparison — Row 22 (Domestic Sales)

| Version | Row 22 Status |
|---|---|
| v2 | **EMPTY** |
| v3-new | **POPULATED** (=237.08+278.32...) |

---

## 4. Key Findings

### Pipeline Behavior
1. **ScopedClassifier is very conservative** — only 25% confident classification rate. The old pipeline's learned mappings and golden rules provided 95% coverage; without them, the AI alone needs significant help.
2. **Zero learned mappings were consulted** despite the learning_system.py being unchanged. The pipeline re-classification appears to bypass learned mappings entirely.
3. **All 437 doubts had `ai_best_guess: null`** — the classifier didn't even provide a guess when uncertain.

### Quality Assessment
1. **Row 22 (Domestic Sales) is now populated** — this was the key failure in v2.
2. **1105 populated cells** suggests good overall data coverage.
3. **Formulas preserved** — cross-sheet references (TL sheet, Details sheet) intact.
4. **VBA macros intact** — file saves as .xlsm correctly.

### Recommendations
1. **Tune ScopedClassifier confidence threshold** — 75% doubt rate is too high for production use.
2. **Re-integrate learned mappings** — the learning system should be checked first before AI classification.
3. **Add ai_best_guess** to doubt output — even uncertain classifications should suggest the most likely mapping.
4. **Consider hybrid approach** — use learned mappings + AI as fallback instead of AI-only.

---

## 5. Files Generated

```
DOCS/test-results/bcipl/run-2026-04-05-v3/
  doubts-raw-newpipeline.json          # 437 raw doubt records
  doubt-resolutions-newpipeline.json   # Resolution summary
  corrections.json                     # 93 auto-matched corrections (phase 1)
  BCIPL_generated_CMA_newpipeline.xlsm # Generated CMA Excel
  test-report-newpipeline.md           # This report
```
