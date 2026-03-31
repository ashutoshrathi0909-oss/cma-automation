# RAC Phase 1a — Embedding Accuracy Report

**Generated:** 2026-03-23 16:17 UTC
**Method:** sentence-transformers (all-MiniLM-L6-v2)
**Database:** SR Papers — 216 trading company items
**Test Set:** BCIPL — 448 manufacturing company items

---

## Overall Results

| Metric | Value |
|--------|-------|
| Top-1 Accuracy | **21.2%** (95/448) |
| Top-5 Majority Vote Accuracy | **22.1%** (99/448) |
| Average unique CMA rows in top-10 | **3.67** |
| Median unique CMA rows in top-10 | **4.0** |

---

## Candidate Narrowing Analysis

**Key finding:** Instead of asking the LLM to pick from all 139 CMA fields,
RAC narrows the candidate set to approximately **4 unique fields** on average.

> If we narrow to top-5 candidate fields and send to Haiku, the LLM only needs
> to pick from ~4 options instead of 139. This reduces the chance
> of hallucination and speeds up classification.

### Distribution of unique CMA rows in top-10

| Unique CMA rows | Items | % of total |
|----------------|-------|------------|
| 1 unique rows | 12 | 2.7% |
| 2 unique rows | 32 | 7.1% |
| 3 unique rows | 114 | 25.4% |
| 4 unique rows | 227 | 50.7% |
| 5 unique rows | 59 | 13.2% |
| 6 unique rows | 4 | 0.9% |

---

## Accuracy by Sheet Name

| Sheet Name | Count | Top-1 Acc | Top-5 MV Acc |
|-----------|-------|-----------|--------------|
| Notes BS (2) | 124 | 15.3% | 18.5% |
| Co., Deprn  | 120 | 2.5% | 2.5% |
| Notes to P & L | 116 | 47.4% | 46.6% |
| Subnotes to BS | 62 | 12.9% | 14.5% |
| Subnotes to PL | 20 | 35.0% | 35.0% |
| Notes BS (1) | 6 | 50.0% | 50.0% |

---

## Top-20 Worst Failures

*(Highest similarity score but wrong CMA row — these are the hardest cases)*

| # | Raw Text | Sheet | True CMA Field | Predicted Field | Similarity |
|---|----------|-------|---------------|-----------------|------------|
| 1 | `DPT-3 Unsecured Loans (LT portion FY23)` | Notes BS (2) | Unsecured Loans - Long Term De | Unsecured Loans - Quasi Equity | 0.814 |
| 2 | `ESI payable` | Notes BS (2) | Other statutory liabilities (d | Other current liabilities | 0.808 |
| 3 | `ESI payable (FY23)` | Notes BS (2) | Other statutory liabilities (d | Other current liabilities | 0.803 |
| 4 | `ESI payable (FY22)` | Notes BS (2) | Other statutory liabilities (d | Other current liabilities | 0.794 |
| 5 | `Bonus payable (FY23)` | Notes BS (2) | Other statutory liabilities (d | Other current liabilities | 0.784 |
| 6 | `TDS Payable Others (FY23)` | Notes BS (2) | Other statutory liabilities (d | Other current liabilities | 0.780 |
| 7 | `Job Work Charges & Contract Labour (FY23` | Notes to P & L | Processing / Job Work Charges | Wages | 0.779 |
| 8 | `Job Work Charges & Contract Labour (FY22` | Notes to P & L | Processing / Job Work Charges | Wages | 0.778 |
| 9 | `PF payable (FY23)` | Notes BS (2) | Other statutory liabilities (d | Other current liabilities | 0.772 |
| 10 | `Bonus payable (FY22)` | Notes BS (2) | Other statutory liabilities (d | Other current liabilities | 0.770 |
| 11 | `Unsecured Considered Good (non-current r` | Notes BS (2) | Other non current assets | Domestic Receivables | 0.770 |
| 12 | `PF payable` | Notes BS (2) | Other statutory liabilities (d | Other current liabilities | 0.768 |
| 13 | `TDS payable (FY22)` | Notes BS (2) | Other statutory liabilities (d | Other current liabilities | 0.766 |
| 14 | `TDS Payable - Others` | Notes BS (2) | Other statutory liabilities (d | Other current liabilities | 0.765 |
| 15 | `Bonus payable` | Notes BS (2) | Other statutory liabilities (d | Other current liabilities | 0.765 |
| 16 | `Security Deposits (BESCOM, KIADB etc)` | Notes BS (2) | Security deposits with governm | Other Advances / current asset | 0.759 |
| 17 | `PF payable (FY22)` | Notes BS (2) | Other statutory liabilities (d | Other current liabilities | 0.757 |
| 18 | `Axis Term Loan No. 879974 (FY23)` | Notes BS (2) | Term Loan Balance Repayable af | Working Capital Bank Finance - | 0.754 |
| 19 | `Job Work Charges & Contract Labour` | Notes to P & L | Processing / Job Work Charges | Wages | 0.749 |
| 20 | `Rates & Taxes` | Notes to P & L | Others (Admin) | Rent, Rates and Taxes | 0.742 |

---

## Interpretation

1. **Top-1 Accuracy (21.2%)**: Low — needs improvement — the single most similar SR item matches the BCIPL item's CMA row this % of the time.

2. **Top-5 MV Accuracy (22.1%)**: Majority voting over the top-5 nearest
   neighbors improves accuracy
   vs. top-1 alone (+0.9 pp).

3. **Candidate Narrowing (3.7 avg unique rows in top-10)**: RAC reduces
   the classification problem from 139 CMA fields to ~4 candidates.
   This is the main value proposition — even if RAC alone is imperfect, it dramatically
   constrains the search space for Haiku.

4. **Cross-domain gap**: SR Papers is a trading company; BCIPL is manufacturing.
   The accuracy reflects how well financial line-item language generalises across
   these two domains using only text similarity.

---

## Files

- `embeddings.npz` — compressed numpy arrays (sr_embeddings, bc_embeddings)
- `embedding_test_results.json` — full per-item results with top-10 matches
- `EMBEDDING_ACCURACY_REPORT.md` — this report
