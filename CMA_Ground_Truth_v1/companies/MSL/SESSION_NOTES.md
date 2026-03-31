# Matrix Stampi Limited (MSL) — Extraction Session Notes
**Date:** 2026-03-25
**Extracted by:** Claude Code (Sonnet subagents)
**Company folder:** `MSL - Manufacturing/`

---

## Source Files Inventory

| File | Type | Size | Year | Used By |
|------|------|------|------|---------|
| `MSL CMA 24102025.xls` | CMA workbook (Excel) | 513 KB | FY22-23, FY23-24, FY24-25 | CMA Agent |
| `MSL - B.S -2024-25 Final 151025.xlsx` | Working paper Excel (BS + P&L + Notes + TB) | 136 KB | FY24-25 (current) + FY23-24 (comparative) | Excel FS Agent |
| `MSL Audited financial with Audit Report_FY24-25.pdf` | Audited financials PDF | 2.5 MB | FY24-25 | PDF OCR Agent (FY25) |
| `MSL Audited Financial fy23-24.pdf` | Audited financials PDF | 1.0 MB | FY23-24 | **SCANNED — NO TEXT** |
| `MSL FY 2023.pdf` | Audited financials PDF | 1.8 MB | FY22-23 | **SCANNED — NO TEXT** |

---

## Extraction Outputs

| Output File | Source(s) | Agent Type | Status | Key Stats |
|-------------|-----------|------------|--------|-----------|
| `MSL_subagent2_cma_extraction.json` | `MSL CMA 24102025.xls` | CMA Extractor (Sonnet) | ✅ Complete | 88 CMA rows, 3 actual years (FY23/FY24/FY25) |
| `MSL_subagent1_fy2425_extraction.json` | `MSL Audited financial...FY24-25.pdf` | PDF OCR (Sonnet) | ✅ Complete | P&L + BS + Notes 19-26 + Depreciation |
| `MSL_fs_excel_fy2425.json` | `MSL - B.S -2024-25 Final 151025.xlsx` | Excel FS (Sonnet) | ✅ Complete | P&L + BS + 24 notes + Trial Balance (220 accounts) |
| `MSL_fs_excel_fy2324.json` | `MSL - B.S -2024-25 Final 151025.xlsx` (comparative col) | Excel FS (Sonnet) | ✅ Complete | P&L + BS + 24 notes (comparative FY23-24 data) |

---

## Financial Years Covered

| FY | Financial Statements | Source | Notes |
|----|---------------------|--------|-------|
| FY2022-23 | ❌ NOT AVAILABLE | Scanned PDF (`MSL FY 2023.pdf`, 28 pages) | pdfplumber extracts no text; Read tool unavailable (pdftoppm not installed). **CMA amounts only** for this year. |
| FY2023-24 | ✅ Available (comparative) | `MSL - B.S -2024-25 Final 151025.xlsx` (prev-year columns) + comparative in `MSL_subagent1_fy2425_extraction.json` | Full P&L + BS + Notes. Scanned PDF (`MSL Audited Financial fy23-24.pdf`, 16 pages) not usable. |
| FY2024-25 | ✅ Available (2 sources) | Audited PDF + Working paper Excel | PDF has 29 pages; Excel has more granular trial balance (220 accounts in rupees). Cross-reference both. |

---

## Company Profile

- **Full name:** Matrix Stampi Limited
- **Industry:** Manufacturing — stamping / press components
- **Entity type:** Private Limited (Ltd)
- **Bankers:** IDBI Bank (Cash Credit + Term Loans)
- **Auditor:** L.B. Jha & Co. CA (FRN: 301088E), Partner: Saurabh Tibrewal (M.No.300388), Kolkata
- **Directors:** Mukund Kumar Bhaiya (DIN:00793057), Manoj Kumar Bhaiya (DIN:00182872)
- **Currency in CMA:** Lakhs
- **Currency in PDFs:** Thousands ('000) — converted to lakhs (÷100) in all extraction JSONs
- **Currency in Trial Balance:** Absolute rupees — NOT converted (see `MSL_fs_excel_fy2425.json` TB section)

---

## Issues & Observations

1. **FY2022-23 scanned PDF**: `MSL FY 2023.pdf` is a scanned image (28 pages). pdfplumber returns no text from page 1. The Read tool also cannot render it (pdftoppm not installed on this Windows machine). **Only CMA amounts available for FY22-23** — Opus will have to work without a source FS for this year.

2. **FY2023-24 scanned PDF**: `MSL Audited Financial fy23-24.pdf` is also scanned (16 pages). However, FY23-24 data IS available as the comparative/previous year column in the working paper Excel (`MSL - B.S -2024-25 Final 151025.xlsx`).

3. **Qualified audit opinion (FY24-25)**:
   - No provision on receivables of Rs.7.38 lakhs outstanding >5 years (profit overstated)
   - No provision on PF arrears: Rs.24.25L + Rs.17.67L (impact unascertainable)
   - GST ITC reconciliation pending
   - Income tax assessments from earlier years not reflected
   - Accounting software lacks audit trail — Rule 3(1) non-compliance

4. **Director/related party loans**: Rs.417.68L of director/related party loans classified as **quasi-equity** in FY25 CMA (important for CMA Form III classification).

5. **Note 25 #REF! error**: In the source Excel, Note 25 "Other Expenses" FY23-24 second column shows `#REF!` formula error. First column value (186.75 lakhs) was used.

6. **Trial balance in absolute rupees**: The `TRIAL BALANANCE` sheet in the Excel has closing balances in individual rupees, not thousands. The TB section in `MSL_fs_excel_fy2425.json` preserves this as-is (not converted to lakhs). Opus agent must apply ÷100,000 to convert TB amounts to lakhs.

7. **"Purchase of Stock in Trade" anomaly**: The P&L shows this as the largest expense item (Rs.1967.54L in FY25). For a manufacturing company, this typically suggests trading activity alongside manufacturing. The CMA likely maps this to "Raw Materials Consumed" or "Purchase of Traded Goods" — worth flagging for industry-specific classification.

---

## CMA Data Summary (from `MSL_subagent2_cma_extraction.json`)

- **88 CMA rows** extracted across 3 actual years
- All 3 years audited (per CMA INPUT SHEET)
- FY2021-22 data also present in CMA but excluded (older than 3-year window)
- Balance sheets balance for all 3 years (verified during CMA extraction)
- Revenue trend: FY22-23 → FY23-24 → FY24-25 = growth pattern (see CMA)

---

## Ready for Reverse Engineering

- [x] CMA rows extracted (all 3 years)
- [x] FY2024-25 financial statements extracted (2 sources: PDF + Excel)
- [x] FY2023-24 financial statements extracted (from comparative Excel)
- [ ] FY2022-23 financial statements — NOT AVAILABLE (scanned PDF, no extraction possible)
- [x] All outputs validated
- [x] Session notes complete

**Next step:** Open a NEW Claude Code window and run the Opus reverse engineering prompt.

---

## Opus Reverse Engineering Handoff

Tell Opus to read these files:
1. `MSL - Manufacturing/MSL_subagent2_cma_extraction.json` — CMA 3-year data (88 rows)
2. `MSL - Manufacturing/MSL_subagent1_fy2425_extraction.json` — FY24-25 audited PDF financials
3. `MSL - Manufacturing/MSL_fs_excel_fy2425.json` — FY24-25 working paper Excel (includes Trial Balance — 220 accounts in rupees)
4. `MSL - Manufacturing/MSL_fs_excel_fy2324.json` — FY23-24 comparative financials (from Excel)
5. `cma_template_reference.json` — CMA row codes and hierarchy reference
6. `canonical_labels.json` — Canonical labels reference

**Important instructions for Opus:**
- Trial balance amounts in `MSL_fs_excel_fy2425.json` TB section are in **absolute rupees** (not thousands, not lakhs) — convert with ÷100,000 for comparison with CMA
- FY22-23 reverse engineering will be CMA-amount-only (no FS source available for that year)
- The "Purchase of Stock in Trade" line should be investigated — for a manufacturing company, this is unusual and may indicate split/industry-specific mapping
- Director loans (Rs.417.68L) classified as quasi-equity in CMA Form III — flag this mapping
