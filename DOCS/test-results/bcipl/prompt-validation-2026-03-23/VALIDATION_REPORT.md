# Validation Report: Generic Prompt on BCIPL

**Date:** 2026-03-23
**Prompt:** `generic_prompt_template.txt` (with Manufacturing rules)
**Company:** BCIPL (Manufacturing - metal stamping, laminations, CRCA components)
**Ground Truth:** 448 items, 350 unique after dedup

---

## 1. Summary

| Metric | Value |
|--------|-------|
| Total unique items | 350 |
| Correct | 306 (87.4%) |
| Wrong | 44 (12.6%) |
| **Verdict** | **FAIL (< 90%)** |

### Comparison vs Previous Experiments

| Experiment | Accuracy | Items |
|-----------|----------|-------|
| Baseline (flat prompt) | 78.4% | 276/352 |
| BCIPL-specific V1 | 92.0% | 324/352 |
| Expected (final w/ fixes) | ~95-96% | - |
| **THIS RUN (generic)** | **87.4%** | **306/350** |

The generic prompt **dropped 4.6 percentage points** from the BCIPL-specific V1 prompt (92.0% -> 87.4%), indicating that several BCIPL-specific rules were load-bearing and were lost in genericization.

---

## 2. Accuracy by Sheet

| Sheet | Correct | Total | Accuracy |
|-------|---------|-------|----------|
| Notes BS (1) | 6 | 6 | 100.0% |
| Subnotes to PL | 19 | 19 | 100.0% |
| Co., Deprn | 37 | 40 | 92.5% |
| Notes BS (2) | 108 | 124 | 87.1% |
| Notes to P & L | 96 | 112 | 85.7% |
| Subnotes to BS | 40 | 49 | 81.6% |

**Weakest areas:** Subnotes to BS (81.6%) and Notes to P&L (85.7%).

---

## 3. Accuracy by Confidence Level

| Confidence | Correct | Total | Accuracy |
|-----------|---------|-------|----------|
| verified | 177 | 199 | 88.9% |
| high | 114 | 133 | 85.7% |
| inferred | 15 | 18 | 83.3% |

---

## 4. All Wrong Items (44)

### Pattern 1: Statutory Liabilities as Other Current Liabilities (7 items)

ESI payable, PF payable, and Unpaid Trainee Stipend are being classified as Row 250 (Other current liabilities) instead of Row 246 (Other statutory liabilities). The prompt needs an explicit rule:

> ESI payable, PF payable, Professional Tax payable -> Row 246 (Other statutory liabilities), NOT Row 250

| Item | Expected | Predicted |
|------|----------|-----------|
| ESI payable | 246 | 250 |
| ESI payable (FY22) | 246 | 250 |
| ESI payable (FY23) | 246 | 250 |
| PF payable | 246 | 250 |
| PF payable (FY22) | 246 | 250 |
| PF payable (FY23) | 246 | 250 |
| Unpaid Trainee Stipend | 246 | 250 |

### Pattern 2: Job Work Revenue as Manufacturing Expense (4 items)

Job Work Charges in the **revenue/sale of products** section should be Row 22 (Domestic Sales), not Row 46 (Processing/Job Work Charges). The prompt correctly says "Route by Sheet" but Haiku is pattern-matching "Job Work Charges" to manufacturing Row 46.

> Job Work Charges/Income in "sale of products" section -> Row 22 (Domestic Sales), NOT Row 46

| Item | Expected | Predicted |
|------|----------|-----------|
| Job Work Charges - Local (FY23) | 22 | 46 |
| Job Work Charges - Interstate | 22 | 46 |
| Job Work Charges - Interstate (FY23) | 22 | 46 |
| Job Work Charges - Local | 22 | 46 |

### Pattern 3: Term Loan Bucket Confusion (4 items)

Sellers Credit and specific term loans being assigned to wrong current/non-current bucket.

| Item | Expected | Predicted |
|------|----------|-----------|
| Axis Bank Sellers Credit - Ming Xu - III | 137 | 131 |
| Axis Bank Sellers Credit Fongei - I | 137 | 136 |
| Axis Bank TL-V Business Empower (FY23) | 137 | 136 |
| Axis Bank Suppliers Credit - Fair Oaks | 137 | 131 |

### Pattern 4: TDS/TCS Paid Treated as TDS Owed (3 items)

TDS in Subnotes to BS ("tax deducted at source") represents TDS **paid by** the company (advance tax, Row 221), but Haiku is classifying it as TDS **owed to** government (Row 246).

| Item | Expected | Predicted |
|------|----------|-----------|
| TDS-Rent-94I | 221 | 246 |
| TAX COLLECTED AT SOURCE 1% | 221 | 246 |
| TDS 2022-23 | 221 | 246 |

### Pattern 5: WC Borrowing Confusion (3 items)

| Item | Expected | Predicted |
|------|----------|-----------|
| Yes Bank CC (Cash Credit) | 131 (WC Bank 1) | 84 (Interest) |
| Inland LC Discounting | 132 (WC Bank 2) | 131 (WC Bank 1) |
| TATA Capital Financial Services Ltd (FY22) | 132 (WC Bank 2) | 131 (WC Bank 1) |

### Pattern 6: Wages vs Salary/Staff Expenses (3 items)

"Salaries & Wages" in P&L notes mapped to Row 67 (Salary and staff expenses) instead of Row 45 (Wages). In BCIPL's manufacturing context, these are factory wages.

| Item | Expected | Predicted |
|------|----------|-----------|
| Salaries & Wages | 45 | 67 |
| Salaries & Wages (FY22) | 45 | 67 |
| Salaries & Wages (FY23) | 45 | 67 |

### Pattern 7: Admin Rent/Rates to Rent Category (2 items)

Rent and Rates & Taxes in "other expenses" section classified to Row 68 instead of Row 71. The BCIPL-specific ground truth puts these in "Others (Admin)" because they're already captured elsewhere.

| Item | Expected | Predicted |
|------|----------|-----------|
| Rent (in Admin row) (FY23) | 71 | 68 |
| Rates & Taxes | 71 | 68 |

### Pattern 8: Admin Expense as Audit Fees (2 items)

"Administrative & General Expenses" in auditor's remuneration section -> should be Row 71 (Others Admin) or Row 70 (S&D), not Row 73 (Audit Fees).

| Item | Expected | Predicted |
|------|----------|-----------|
| Administrative & General Expenses | 71 | 73 |
| Administrative & General Expenses (FY23) | 70 | 73 |

### Pattern 9: Other Individual Errors (16 items)

| Item | Sheet | Expected | Predicted | Issue |
|------|-------|----------|-----------|-------|
| Machinery Maintenance | Notes P&L | 49 (Others Mfg) | 50 (R&M Mfg) | Ambiguous - prompt says both |
| Employee Contribution to EPF A/c | Subnotes BS | 223 (Other Advances) | 219 (Advances recoverable) | Adjacent field |
| Interest on C.C. A/c | Notes P&L | 83 (Term Loan Interest) | 84 (WC Interest) | Ground truth may be debatable |
| Sales of Trading Goods | Notes P&L | 22 (Domestic Sales) | 34 (Others Non-Op Income) | Trading vs domestic |
| Advance to Suppliers / Contractors (FY23) | Notes BS | 220 (Suppliers RM) | 236 (Suppliers Capital) | Ambiguous supplier type |
| YELLOW SPECTRUM TECHNOLOGIES | Subnotes BS | 223 (Other Advances) | 236 (Capital Advances) | Section-dependent |
| Sale of Duty Credit Scrips (FY23) | Notes P&L | 34 (Others Non-Op) | 31 (Profit on sale FA) | Adjacent field |
| Security Deposits (FY22) | Notes BS | 237 (Govt Security Dep) | 238 (Other Non-Current) | Adjacent field |
| Axis Term Loan No. 879974 (FY23) | Notes BS | 137 (TL After 1yr) | 136 (TL Within 1yr) | Current/non-current |
| More than 365 days | Subnotes BS | 206 (Domestic Receivables) | 208 (Debtors >6mo) | Age vs category |
| Electronic Cash Ledger (GST) | Subnotes BS | 237 (Govt Security Dep) | 238 (Other Non-Current) | Adjacent field |
| Selling & Distribution Expenses (FY22) | Notes P&L | 70 (S&D/Ads) | 71 (Others Admin) | Umbrella heading |
| NMTG Mechtrans Techiques Pvt Ltd | Subnotes BS | 223 (Other Advances) | 236 (Capital Advances) | Section interpretation |
| Total Depreciation (All Assets) | Co. Deprn | 56 (Depr Mfg) | 63 (Depr CMA) | Total vs split |
| Accumulated Depr - Cranes | Co. Deprn | 163 (Accum Depr) | 56 (Depr Mfg) | Acc depr vs current depr |
| Depreciation - Software (Intangible) | Co. Deprn | 56 (Depr Mfg) | 63 (Depr CMA) | Ground truth questionable |

---

## 5. Regressions from BCIPL-specific V1

The generic prompt loses these BCIPL-specific rules that were load-bearing:

1. **Job Work as Revenue:** BCIPL earns revenue from job work (metal stamping services). The generic prompt doesn't distinguish "Job Work Charges" in revenue vs expense sections.
2. **ESI/PF as Statutory:** BCIPL-specific V1 had explicit rules for ESI/PF payable -> Row 246.
3. **Salaries as Wages:** In BCIPL's manufacturing context, "Salaries & Wages" in the cost notes are factory wages (Row 45), not admin salary (Row 67).
4. **Sellers Credit as Term Loan:** BCIPL uses Axis Bank Sellers Credit facilities classified as non-current term loans (Row 137), not WC (Row 131).
5. **TDS in Subnotes to BS:** Context-dependent TDS classification was handled by BCIPL-specific rules.

---

## 6. Token Usage and Cost Projection

| Metric | Value |
|--------|-------|
| Avg input tokens per batch | ~3,500 |
| Avg output tokens per batch | ~1,200 |
| Total input tokens | ~84,000 |
| Total output tokens | ~28,800 |
| **Total tokens** | **~112,800** |

### Cost projection (if using OpenRouter Haiku)

| Component | Rate | Cost |
|-----------|------|------|
| Input ($0.80/M) | 84K tokens | $0.07 |
| Output ($4.00/M) | 28.8K tokens | $0.12 |
| **Total per BCIPL** | | **$0.19** |
| Projected per company | | ~$0.19 |
| Projected 7 companies | | ~$1.33 |

---

## 7. Verdict: FAIL (87.4% < 90%)

The generic prompt is **not production-ready** for BCIPL. The genericization lost several BCIPL-specific rules that account for ~4.6% of accuracy drop.

---

## 8. Recommendations

To bring the generic prompt back above 93%, add these rules to the MANUFACTURING-SPECIFIC section:

### Must-add rules (would fix ~30 of 44 errors):

1. **Job Work Revenue:**
   ```
   Job Work Charges/Income in revenue/sale sections -> Row 22 (Domestic Sales)
   Job Work Charges in expense/cost sections -> Row 46 (Processing)
   Context determines classification, not just the item name.
   ```

2. **Statutory Employee Liabilities:**
   ```
   ESI payable, PF payable, Professional Tax payable -> Row 246 (Other statutory liabilities)
   These are NOT Row 250 (Other current liabilities)
   Only unpaid salary/wages/stipend -> Row 250
   ```

3. **Wages vs Salary (Manufacturing):**
   ```
   "Salaries & Wages" from factory/manufacturing cost notes -> Row 45 (Wages)
   "Salary and staff expenses" from admin/overhead notes -> Row 67
   For manufacturing companies, default to Row 45 when in cost-of-production context.
   ```

4. **Sellers Credit / Supplier Finance:**
   ```
   Axis Bank/SBI Sellers Credit in non-current secured loans -> Row 137 (TL after 1yr)
   Sellers Credit in current/short-term -> Row 136 (TL within 1yr)
   Do NOT classify as WC Bank Finance (Row 131) or Interest (Row 84).
   ```

5. **TDS in Subnotes to BS:**
   ```
   TDS/TCS in "tax deducted at source" subnotes (asset side) -> Row 221 (Advance Income Tax)
   TDS/TCS in "statutory dues" / liabilities -> Row 246
   ```

### Nice-to-have rules (would fix remaining ~14 errors):

6. Bank 1 vs Bank 2 disambiguation (needs company-specific info)
7. "More than 365 days" receivables -> Row 206 if domestic, not Row 208
8. Admin & General Expenses in auditor section -> Row 71, NOT Row 73
