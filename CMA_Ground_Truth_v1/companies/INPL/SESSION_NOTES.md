# INPL (IFFCO-Nanoventions Private Limited) — Extraction Session Notes
**Date:** 2026-03-25
**Extracted by:** Claude Code (Sonnet subagents, 4 parallel agents)

---

## Source Files Inventory

| File | Type | Size | Year(s) | Used By |
|------|------|------|---------|---------|
| `Nanoventions CMA 10032026.xls` | CMA workbook | 487KB | All years | CMA Agent |
| `2. Audited Statement 2022-2023.PDF` | Financial statements PDF | 14MB | FY2022-23 | FS Agent FY22-23 |
| `3. Audited Statement 2023-2024.pdf` | Financial statements PDF | 18MB | FY2023-24 | FS Agent FY23-24 |
| `Audit Financial Statement 2024-2025.pdf` | Financial statements PDF | 17MB | FY2024-25 | FS Agent FY24-25 |

---

## Extraction Outputs

| Output File | Source(s) | Agent Type | Status | Key Stats |
|-------------|-----------|------------|--------|-----------|
| `inpl_cma_extraction.json` | `Nanoventions CMA 10032026.xls` | CMA Extractor | Complete | 115 rows (54 Form II + 61 Form III), 3 years |
| `inpl_fs_2022_23.json` | `2. Audited Statement 2022-2023.PDF` | PDF OCR | Complete | P&L: 16 items, Notes: 24, BS balanced |
| `inpl_fs_2023_24.json` | `3. Audited Statement 2023-2024.pdf` | PDF OCR | Complete | P&L: 16 items, Notes: 24, BS balanced |
| `inpl_fs_2024_25.json` | `Audit Financial Statement 2024-2025.pdf` | PDF OCR | Complete | P&L: 17 items, Notes: 23, BS balanced |

---

## Financial Years Covered

| Year | Source | Status | Currency in FS | Revenue (CMA Crores) |
|------|--------|--------|----------------|----------------------|
| FY2022-23 | PDF (14MB) | Audited | Rs. Thousands | 10.56 Cr |
| FY2023-24 | PDF (18MB) | Audited | Rs. Thousands | 65.10 Cr |
| FY2024-25 | PDF (17MB) | Audited | Rs. Lakhs | 140.27 Cr |

---

## CRITICAL: Currency Unit Inconsistency

**This is the most important note for the Opus reverse engineering agent.**

The three financial statement PDFs use DIFFERENT currency units:

| Source | Currency Unit | Conversion to Crores |
|--------|--------------|----------------------|
| CMA workbook | Crores | 1x |
| FY2022-23 FS PDF | Rs. Thousands (Rs.'000) | Divide by 1,00,000 |
| FY2023-24 FS PDF | Rs. Thousands (Rs.'000) | Divide by 1,00,000 |
| FY2024-25 FS PDF | Rs. Lakhs | Divide by 100 |

**Cross-validation (all match CMA):**
- FY2022-23: FS Revenue = 1,05,639.44 thousands = **10.56 Cr** ✓
- FY2023-24: FS Revenue = 6,50,967.14 thousands = **65.10 Cr** ✓
- FY2024-25: FS Revenue = 14,027.47 lakhs = **140.27 Cr** ✓

---

## Company Profile

- **Full Name:** IFFCO-Nanoventions Private Limited (formerly Nanoventions Private Limited)
- **CIN:** U73100TZ2021PTC036398
- **Location:** Coimbatore, Tamil Nadu
- **Industry:** Manufacturing and trading of Nano and Bio Formulations, including R&D
- **Entity type:** Private Limited (IFFCO joint venture)
- **Incorporated:** June 2021 (very young company)
- **Auditor:** NVP and Co., Chartered Accountants (N V Palanisamy, M.No. 212460), Coimbatore
- **Accounting Standards:** Indian GAAP / Old GAAP (SMC framework — Small and Medium Company)
- **Currency unit in CMA:** Crores

---

## Key Financial Highlights

### Revenue Growth (explosive)
| Year | Net Sales (Cr) | YoY Growth |
|------|----------------|-----------|
| FY2022-23 | 10.56 | — |
| FY2023-24 | 65.10 | +516% |
| FY2024-25 | 140.27 | +115% |

### PAT (₹ Crores)
| Year | PAT |
|------|-----|
| FY2022-23 | ~2.51 Cr |
| FY2023-24 | ~11.38 Cr |
| FY2024-25 | ~33.96 Cr |

### Business Model
- Company is essentially a **captive supplier to IFFCO Limited** (parent/associate)
- FY2023-24: ~63% revenue from "Services to IFFCO Limited"
- FY2024-25: Revenue includes both Products (Cost of Materials + SIT) and Services

---

## Issues & Observations

### Critical Issues
1. **Currency unit varies by year:** FY22-23 and FY23-24 FS use Thousands; FY24-25 FS uses Lakhs. CMA uses Crores. Opus must apply correct conversion per year.
2. **FY25 BS minor gap (0.049 Cr):** Pre-existing in the CMA workbook — not an extraction error.
3. **Note 12 OCR ambiguity (FY22-23):** OCL balance initially misread as 30,209.07 but corrected to 35,809.07 via Note 12 sub-items sum. Extracted value is correct.

### Notable Events
4. **Bonus issue in FY2024-25:** Share capital jumped from Rs.2 lakhs (20,000 shares at Rs.10 face value) to Rs.1,500 lakhs (1,500,000 shares). Securities premium and P&L surplus were capitalised. CMA reflects this as 0.02 Cr → 15 Cr.
5. **IFFCO equity infusion:** CMA shows share capital jump from 0.02 Cr to 15 Cr in FY25 (the bonus issue restructuring).
6. **Long-term borrowings:** Unsecured loans from IFFCO New Delhi and Ideal Energy Projects; rescheduled in FY25 to repay FY2027-28 through FY2031-32.
7. **MPBF near zero for all 3 years:** Company has no working capital bank borrowing — self-funded through IFFCO group.
8. **Salary & R&M classification shift FY22-23 → FY23-24:** Expenses reclassified from Administrative to Manufacturing in the CMA.
9. **"Other Appropriation" FY25:** Rs.13.63 Cr transferred from P&L — likely bonus issue capitalisation. Confirm from audited financials.
10. **Capital commitments:** Rs.4,999 lakhs (~50 Cr) outstanding for factory/lab construction as at FY25. CWIP = Rs.19.42 Cr (FY25).
11. **Depreciation schedule partial obscurity (FY25):** Plant & Equipment row figures partially illegible from scan in the FY2024-25 PDF. Extracted values may need verification.
12. **R&D intensity:** Research & Development expense = Rs.66.2M in FY23-24 (~10% of revenue). Classified under "Other Expenses."

---

## Ready for Reverse Engineering
- [x] All CMA rows extracted (115 rows across 3 years)
- [x] All financial years extracted (FY2022-23, FY2023-24, FY2024-25)
- [x] All outputs validated (JSON valid, BS balanced for all years)
- [x] Session notes complete
- [ ] **Next step:** Open a new Claude Code window and run the Opus reverse engineering prompt

## Reverse Engineering Handoff

Open a **NEW Claude Code window** and paste the prompt from:
`prompts/prompts/main-opus-reverse-engineer.md`

Tell it to read these files:
- `INPL/inpl_cma_extraction.json`
- `INPL/inpl_fs_2022_23.json`
- `INPL/inpl_fs_2023_24.json`
- `INPL/inpl_fs_2024_25.json`
- `canonical_labels.json` (if it exists)

**Special instructions for Opus:**
1. Apply correct currency conversions per year (see Currency table above)
2. Note the IFFCO captive supplier business model — most revenue is inter-company services
3. The "Purchases — Stock in Trade" line appears in FY2024-25 but not earlier — track this split
4. Flag R&D expenses classification (Under "Other Expenses" in FS, maps to which CMA row?)
5. Validate bonus issue treatment: share capital + securities premium capitalisation in FY25
6. The company changed name from "Nanoventions Private Limited" to "IFFCO-Nanoventions Private Limited" — verify which name is on which year's FS

It will produce: `INPL/inpl_ground_truth.json`
