# CMA Automation — Future Feature Ideas

**Date:** 2026-03-26
**Status:** Ideas for analysis — not committed. Discuss with CA before prioritizing.

---

## Tier 1: High Impact (would actually win clients)

### 1. Cross-Validation & Sanity Checks
After classification, before Excel generation — system auto-checks:
- Does Total Assets = Total Liabilities + Equity? (must balance)
- Does P&L Net Profit match what's carried to Balance Sheet?
- Is any amount suspiciously different from last year? (e.g., Salary was Rs 5,00,000 last year but Rs 500 this year — lakhs/rupees unit mismatch)
- Are there duplicate items? (same item classified twice)

*Why it matters:* Banks reject CMAs with arithmetic errors. Your father probably spends time manually checking these. This catches mistakes before the CA even sees the Excel.

### 2. Bank Ratio Dashboard
Banks don't just want the CMA — they evaluate it using ratios. Auto-calculate from the filled CMA:
- Current Ratio (Current Assets / Current Liabilities)
- DSCR (Debt Service Coverage Ratio)
- TOL/TNW (Total Outside Liabilities / Tangible Net Worth)
- Debt-Equity Ratio
- Interest Coverage Ratio
- Working Capital turnover

Show a simple dashboard: "This company's Current Ratio is 1.2 — banks typically want > 1.33. ⚠️"

*Why it matters:* If the ratios look bad, the CA knows BEFORE submitting. They can discuss with the client or check if something was misclassified that's hurting the ratios.

### 3. Variance Commentary Generator
When CMA has 3 years, banks ALWAYS ask: "Why did revenue drop 20% in FY23?" or "Why did borrowings increase?"

Auto-generate variance commentary:
```
Revenue: Rs 10.5 Cr (FY22) → Rs 8.2 Cr (FY23) — ↓22%
Suggested commentary: "Revenue decline of 22% primarily due to..."
[CA fills in the reason]
```

*Why it matters:* Banks require these explanations. CAs write them manually every time. Even a template with the numbers pre-filled saves significant time.

---

## Tier 2: Operational Efficiency

### 4. Duplicate Item Detection
During extraction, flag: "Warning: 'Salary and Wages' appears in BOTH Note 25 (Employee Benefits) AND Note 28 (Other Expenses). Is this a duplicate or two different line items?"

*Why it matters:* Double-counting is a common extraction error, especially when companies split expenses across multiple notes.

### 5. Document Checklist & Status Tracking
CA firms handle 50-100 CMAs per season. For each client:
```
☑ Balance Sheet received
☑ P&L received
☐ Notes to Accounts — pending
☐ Auditor's Report — pending
☐ Previous year CMA — pending
Status: 2 of 5 documents uploaded
```

Auto-send reminder: "Client XYZ — Notes to Accounts still pending (due in 3 days)"

*Why it matters:* The #1 bottleneck in CMA preparation is chasing clients for documents. This is basic but every CA firm struggles with it.

### 6. Multi-Format Export
- Excel (.xlsm) — current output
- PDF export — bank-submission-ready, formatted nicely
- Comparison PDF — side-by-side: last year's CMA vs this year's

*Why it matters:* Some banks want PDFs. Some want comparisons. Currently your father probably does this manually in Excel → Print to PDF.

---

## Tier 3: Competitive Moat (long-term)

### 7. Industry Benchmarking
As you process more CMAs, you build a dataset. Show the CA:
```
"This manufacturing company's Power & Fuel cost is 18% of revenue.
 Industry average (from 15 similar companies): 12-14%.
 ⚠️ Unusually high — bank may ask about this."
```

*Why it matters:* This is intelligence no other CMA tool can provide because they don't have the data. You do — from every CMA processed. Anonymized, aggregated benchmarks.

### 8. Bank-Specific CMA Templates
Different banks have slightly different CMA formats:
- SBI format vs PNB format vs HDFC format
- Some want projections, some don't
- Column layouts differ slightly

Let user select bank → auto-adjust template.

*Why it matters:* CAs waste time reformatting CMAs for different banks. This is pure workflow efficiency.

### 9. Version History & Diff
Keep every version of a CMA:
```
v1: Provisional (March 15)
v2: Audited data replaced (May 20)
v3: CA corrections applied (May 22)
v4: Bank feedback incorporated (June 5)
```

Click any two versions → see what changed (like git diff for Excel).

*Why it matters:* Banks often come back with "please revise XYZ." The CA needs to know what changed between versions. Currently they track this mentally or in notes.

---

## Priority Ranking

| # | Feature | Impact | Effort | Do When? |
|---|---------|--------|--------|----------|
| 1 | Cross-validation & sanity checks | Very High | Small | V1.1 — soon |
| 2 | Per-client approved mappings | Very High | Medium | V1.1 — soon |
| 3 | Bank ratio dashboard | High | Small | V1.2 |
| 4 | Duplicate item detection | High | Small | V1.2 |
| 5 | Rolling year update | High | Medium | V1.2 |
| 6 | Provisional → audited swap | High | Medium | V1.2 |
| 7 | Variance commentary | Medium | Medium | V2 |
| 8 | Document checklist & tracking | Medium | Medium | V2 |
| 9 | Version history & diff | Medium | Large | V2 |
| 10 | Industry benchmarking | High but needs data | Large | V3 |
| 11 | Bank-specific templates | Medium | Medium | V3 |
| 12 | PDF page removal + redaction | Medium | Medium | V2 |
| 13 | CA feedback loop | High | Large | V2 |

---

## Already Planned (saved separately)

These features are already saved in project memory with detailed specs:
- **CA Feedback Loop** — diff AI Excel vs CA-corrected, auto-learn rules (memory: project_future_feedback_loop.md)
- **PDF Security** — page removal + company name redaction (memory: project_future_pdf_security.md)
- **CMA Lifecycle** — rolling years, provisional→audited, per-client approved mappings (memory: project_future_cma_lifecycle.md)
- **Projections** — V1 explicitly excludes projections; planned for future version
