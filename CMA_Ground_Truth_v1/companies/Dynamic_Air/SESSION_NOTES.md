# Dynamic Air Engineering India Private Limited — Extraction Session Notes
**Date:** 2026-03-25
**Extracted by:** Claude Code (Sonnet subagents, 6 parallel agents)
**CIN:** U29192TN2008PTC066303

---

## Source Files Inventory

| File | Type | Size | Year | Used By |
|------|------|------|------|---------|
| CMA Dynamic 23082025.xls | CMA workbook | 566KB | FY21-22 to FY23-24 | CMA Agent |
| FY_22/Financials/BS-Dynamic 2022 - Companies Act.xlsx | Excel financial statements | 631KB | FY2021-22 | FY22 Excel Agent |
| FY_22/Financials/ITR BS P&L.pdf | PDF (ITR format, 8 pages) | 2MB | FY2021-22 | FY22 PDF Agent |
| FY_22/Financials/Notes to Financials.pdf | PDF (notes, 16 pages) | 4.1MB | FY2021-22 | FY22 PDF Agent |
| FY_22/Financials/Auditors Report.pdf | Supporting doc | — | FY2021-22 | Not used |
| FY_22/Financials/Form 3CA 3CD.pdf | Supporting doc (Tax Audit) | — | FY2021-22 | Not used |
| FY_22/Financials/ICDS.pdf | Supporting doc | — | FY2021-22 | Not used |
| FY_22/Turnover Details.xlsx | Supporting doc | — | FY2021-22 | Not used |
| FY-23/ITR PL & BS.pdf | PDF (ITR format) | 2MB | FY2022-23 | FY23 PDF Agent |
| FY-23/Notes..pdf | PDF (notes) | 3.8MB | FY2022-23 | FY23 PDF Agent |
| FY-23/~$DYNAMIC Provisional FY-23.xlsx | **TEMP FILE (Excel lock file)** | — | — | **IGNORE** |
| FY-24/Audited Financials FY-2024 (1).pdf | PDF (audited, 33 pages, scanned) | **15MB** | FY2023-24 | FY24 PDF Agent |
| FY2025/Provisional financial 31.03.25 (3).xlsx | Excel provisional | 29KB | FY2024-25 | FY25 Excel Agent |
| FY2025/Orders on Hand.xlsx | Supporting doc | — | FY2024-25 | Not used |
| FY-24/various supporting docs | Supporting docs | — | FY2023-24 | Not used |

---

## Extraction Outputs

| Output File | Source(s) | Agent Type | Status | Key Stats |
|-------------|-----------|------------|--------|-----------|
| dynamic_cma_extraction.json | CMA Dynamic 23082025.xls | CMA Extractor | ✅ Complete | 88 non-zero rows, 3 years |
| dynamic_fs_fy22_excel.json | BS-Dynamic 2022.xlsx | Excel FS | ✅ Complete | P&L: full, BS: full, Notes 2-23, Dep: 11 classes |
| dynamic_fs_fy22_pdf.json | ITR BS P&L.pdf + Notes to Financials.pdf | PDF OCR | ✅ Complete | ITR format P&L/BS, Notes 17-26, 11 differences flagged |
| dynamic_fs_fy23.json | ITR PL & BS.pdf + Notes..pdf | PDF OCR | ✅ Complete | P&L full, BS full, 34 notes |
| dynamic_fs_fy24.json | Audited Financials FY-2024 (1).pdf | PDF OCR (scanned) | ✅ Complete | P&L full, BS full, 34 notes, 33 pages |
| dynamic_fs_fy25.json | Provisional financial 31.03.25 (3).xlsx | Excel FS (provisional) | ✅ Complete | P&L, BS, 20 notes, FA schedule; no prev-year comparatives |

---

## Financial Years Covered

| Year | Source | Audited/Provisional | CMA Included |
|------|--------|--------------------:|:---:|
| FY 2020-21 | FY22 Excel (prior year column) | Audited | No |
| FY 2021-22 | Excel + PDFs (dual-source) | Audited | Year 1 (CMA) |
| FY 2022-23 | PDFs (ITR + Notes) | Audited | Year 2 (CMA) |
| FY 2023-24 | PDF (audited, 33pp, scanned) | Audited | Year 3 (CMA) |
| FY 2024-25 | Excel (provisional) | **Provisional** | Not in CMA |

---

## ⚠️ CRITICAL: Currency Inconsistencies

**This company uses DIFFERENT currency units across different files. The Opus reverse engineering agent MUST apply conversions.**

| Source | Currency Unit | Conversion to Absolute Rupees |
|--------|--------------|-------------------------------|
| CMA workbook (dynamic_cma_extraction.json) | **Crores** | × 1,00,00,000 |
| FY22 Excel (dynamic_fs_fy22_excel.json) | **INR Thousands** | × 1,000 |
| FY22 PDFs (dynamic_fs_fy22_pdf.json) | **INR Thousands** (some ITR figures in absolute) | × 1,000 |
| FY23 PDFs (dynamic_fs_fy23.json) | **INR Thousands** | × 1,000 |
| FY24 PDF (dynamic_fs_fy24.json) | **INR Thousands** | × 1,000 |
| FY25 Excel (dynamic_fs_fy25.json) | **Absolute Rupees** | × 1 |

**Cross-validation example (FY23-24 revenue):**
- CMA Year 3 revenue: ~6.71 Cr = Rs 6,71,00,000
- FY24 FS revenue: Rs 6,71,496.95 thousands = Rs 6,71,49,69,500 — **WAIT**: these don't match.
- CMA shows 6.71 Cr; FS shows 671 Cr — 100x difference!
- **Possible explanation**: CMA may be using a different unit or the FS figures include GST while CMA is net. Opus must reconcile this discrepancy carefully.

---

## Company Profile

- **Company name:** Dynamic Air Engineering India Private Limited
- **CIN:** U29192TN2008PTC066303
- **Registered office:** Keelkattalai, Chennai - 600 117
- **Industry:** Manufacturing — Aluminum Grills, Dampers & Diffusers, parts for Railway coaches; HVAC/Air Engineering equipment
- **Entity type:** Private Limited Company
- **Accounting standards:** Old GAAP (AS — Companies Accounting Standards Rules 2006) — **NOT Ind AS**
- **Auditor:** S. Ravi & Associates (FRN 009261S) — Note: CMA has a **qualified audit opinion**
- **Export activity:** Negligible (FY22: export earnings Rs 41.66K only; no export sales in CMA)
- **Import activity:** Some raw material imports (FY22: Rs 362.50K)

---

## Issues & Observations

### High Priority (Opus must address)

1. **Currency mismatch between CMA and FS**: CMA is in Crores, FS are in thousands. The numbers appear ~100x different — Opus must verify which is correct and apply appropriate conversion factors before reverse-engineering.

2. **FY25 has no previous-year comparatives**: The provisional FY25 file only has current year (FY24-25) figures. No FY23-24 column for cross-verification.

3. **FY24 PDF was scanned** (image-based, 15MB): OCR extraction may have minor errors — cross-validate key totals against CMA Year 3 figures.

4. **~$DYNAMIC Provisional FY-23.xlsx**: This is a Windows temp/lock file (Excel lock prefix ~$). It is NOT a real Excel file and cannot be parsed. Ignored.

### Medium Priority (note for reverse engineering)

5. **Director remuneration 30× jump in FY22**: K. Karthikeyan remuneration went from Rs 600K (FY21) to Rs 18,000K (FY22). Related party: Girija Karthikeyan Rs 4,200K. This will affect Employee Benefit Expense CMA mapping significantly.

6. **Factory Rent classified as Direct Cost** (not overhead): Rs 1,498.50K in FY22. This is an industry-specific placement — the CA mapped it under direct/manufacturing costs rather than Other Expenses or Admin. Flagged explicitly in dynamic_fs_fy22_pdf.json differences_from_companies_act.

7. **Freight charges included in Revenue**: Rs 2,570.50K in FY22 included in Revenue from Operations (Note 17), not netted. CMA treatment may differ.

8. **Capital subsidy reducing fixed asset cost**: Rs 1,500K government subsidy reducing fixed asset cost in FY22. Affects net block and depreciation.

9. **NSIC government-backed loan**: Rs 29,505.83K appearing in FY22 — affects long-term borrowings classification in CMA Form III.

10. **WIP inventory growing rapidly**: Rs 2.50 Cr → Rs 5.36 Cr → Rs 10.10 Cr (CMA values). Indicates large projects in progress — affects working capital assessment.

11. **PAT declining trend** (audited years): FY22: Rs 7,892K → FY23: Rs 6,928K → FY24: Rs 3,904K. FY25 provisional shows Rs 96,60,162 absolute = Rs 9,660K (recovery if correct).

12. **ITR vs Book depreciation difference**: FY22 ITR depreciation Rs 3,28,52,960 absolute vs book Rs 3,22,21,600 (Rs 32,221.60K) — difference is due to additional depreciation claimed in ITR.

### FY24 PDF-specific Issues
13. Four minor issues noted by the agent (see dynamic_fs_fy24.json validation.issues_found).

---

## Accounting Policies (consistent across FY22-FY24)
- **Depreciation**: WDV method per Companies Act 2013 Schedule II
- **Inventory**: Lower of cost or NRV; cost = FIFO / weighted average
- **Revenue recognition**: On transfer of significant risks and rewards (Old GAAP)
- **Standards**: Old GAAP (AS), NOT Ind AS

---

## Ready for Reverse Engineering
- [x] All CMA rows extracted (88 non-zero rows, FY21-22 to FY23-24)
- [x] All financial years extracted (FY22 dual-source, FY23, FY24, FY25)
- [x] All outputs validated (balance sheets balance, P&L totals cross-check)
- [x] Session notes complete
- [ ] Currency reconciliation required before Opus can map amounts

**Next step:** Open a new Claude Code window and run the Opus reverse engineering prompt (`prompts/prompts/main-opus-reverse-engineer.md`).

Tell it to read these files:
- `Dynamic air engenerring/dynamic_cma_extraction.json`
- `Dynamic air engenerring/dynamic_fs_fy22_excel.json`
- `Dynamic air engenerring/dynamic_fs_fy22_pdf.json`
- `Dynamic air engenerring/dynamic_fs_fy23.json`
- `Dynamic air engenerring/dynamic_fs_fy24.json`
- `Dynamic air engenerring/dynamic_fs_fy25.json`
- `Dynamic air engenerring/SESSION_NOTES.md` (this file — for currency context)
- `canonical_labels.json`

**Primary instruction for Opus:** Resolve the currency mismatch first (CMA in Crores vs FS in thousands). Convert all figures to a common unit (recommend lakhs) before attempting CMA-to-FS matching.
