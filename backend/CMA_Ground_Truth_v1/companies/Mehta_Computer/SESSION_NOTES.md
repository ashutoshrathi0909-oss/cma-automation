# Mehta Computer — Extraction Session Notes
**Date:** 2026-03-25
**Extracted by:** Claude Code (Sonnet subagents, parallel extraction)

---

## Source Files Inventory

| File | Type | Size | Year | Used By |
|------|------|------|------|---------|
| CMA 15092025.xls | CMA workbook | 473KB | FY2021-22, FY2022-23, FY2023-24 (actuals) | CMA Agent |
| 2022/Mehta_Computers_financials_2022.xls | Excel FS | 89KB | FY2021-22 | FS Agent 2022 |
| 2023/Mehta Computers financials 2023.xls | Excel FS | 100KB | FY2022-23 | FS Agent 2023 |
| 2024/Mehta_Computers_financials_2024.xlsx | Excel FS | 44KB | FY2023-24 | FS Agent 2024 |
| 2025/BSheet.pdf | PDF | 3.3KB | FY2024-25 | FS Agent 2025 (PDF) |
| 2025/PandL.pdf | PDF | 10KB | FY2024-25 | FS Agent 2025 (PDF) |
| 2025/TrialBal.pdf | PDF | 6.8KB | FY2024-25 | FS Agent 2025 (PDF) |

---

## Extraction Outputs

| Output File | Source(s) | Agent Type | Status | Key Stats |
|-------------|-----------|------------|--------|-----------|
| mehta_cma_extraction.json | CMA 15092025.xls | CMA Extractor | Complete | 146 rows, 3 actual years (FY22–FY24) |
| mehta_fs_2022.json | Mehta_Computers_financials_2022.xls | Excel FS | Complete | P&L: Trading + P&L format, BS: 2 sides balance (Rs 1,31,06,535.59) |
| mehta_fs_2023.json | Mehta Computers financials 2023.xls | Excel FS | Complete | P&L: Trading + P&L, BS balances (Rs 1,71,96,059, ~Rs 0.41 rounding artefact) |
| mehta_fs_2024.json | Mehta_Computers_financials_2024.xlsx | Excel FS | Complete | P&L: Trading + P&L, BS off by Rs 9,599.90 (discrepancy in source file) |
| mehta_fs_2025.json | BSheet.pdf + PandL.pdf + TrialBal.pdf | PDF OCR | Complete | P&L + BS + Trial Balance; BS balances (Rs 1,42,77,594.81); no previous year figures |

---

## Financial Years Covered

| FY | Source | Audited/Provisional | Notes |
|----|--------|--------------------|----|
| FY2021-22 | Excel | Audited | Net Sales Rs 1,82,55,080 |
| FY2022-23 | Excel | Audited | Net Sales Rs 3,27,00,628 |
| FY2023-24 | Excel | Audited | Net Sales Rs 2,30,61,052 |
| FY2024-25 | PDF | Provisional/Estimated | Net Sales Rs 5,19,51,328; no prev year in PDFs |

**Note:** The CMA file (dated 15 Sep 2025) covers FY2021-22, FY2022-23, and FY2023-24 as actuals. FY2024-25 appears as a projected/estimated column in the CMA — do NOT use CMA amounts for FY2025 (use mehta_fs_2025.json only).

---

## Company Profile

- **Company name:** M/S Mehta Computers
- **Proprietor:** Jignesh Chandrakant Mehta
- **Location:** Chennai
- **Industry:** Trading — computer hardware, IT equipment, electronics (resale; no manufacturing)
- **Entity type:** Proprietorship firm (NOT Private Limited, NOT Partnership)
- **Currency unit in FS files:** Absolute Indian Rupees (not lakhs or crores)
- **Currency unit in CMA file:** INR in Lakhs
- **⚠️ CONVERSION REQUIRED:** When cross-referencing FS amounts to CMA rows, divide FS amounts by 1,00,000 to convert to lakhs

---

## Revenue Trend (for context)

| FY | Net Sales | Gross Profit | Net Profit |
|----|-----------|-------------|-----------|
| FY2021-22 | Rs 1,82,55,080 | Rs 20,25,394 | Rs 9,30,028 |
| FY2022-23 | Rs 3,27,00,628 | Rs 32,06,133 | Rs 12,07,035 |
| FY2023-24 | Rs 2,30,61,052 | Rs 42,08,434 | Rs 12,29,352 |
| FY2024-25 | Rs 5,19,51,328 | Rs 48,50,453 | Rs 10,47,504 |

---

## Industry-Specific Quirks (IMPORTANT for Reverse Engineering)

1. **Proprietorship structure**: Capital account includes personal drawings, LIC premiums, school fees, income tax, personal utility bills, and capital gains. These are non-business items — map only trading/business portions to CMA rows.

2. **Personal investments on BS**: Investments include flat shares, jewellery, mutual funds, LIC policies — these are personal assets of the proprietor, not business assets. Will require careful handling in CMA Form III.

3. **Rebates & Discounts as major expense**: Rs 10.64L (FY23), Rs 14.20L (FY25) — largest single expense item. Likely maps to "Sundry Expenses" or "Selling Expenses" in CMA Form II. This is a trading-firm-specific placement worth flagging.

4. **Zero tax provision**: No income tax provision across all years (proprietorship taxed at individual level, not entity level). PAT = PBT throughout.

5. **WIP Stock FY2022-23**: Rs 16.65L WIP in a trading firm is unusual — likely goods in transit or goods received but not yet billed.

6. **Housing Loan classified as Secured Loan**: Rs 17.58L (FY22) → Rs 16L (FY23) → Rs 14.28L (FY24). This is a personal housing loan, classified under secured loans in CMA. CA judgment call on how to treat this.

7. **FD under lien**: Large swings in fixed deposits — FD under lien Rs 17.6L (FY22), Other FDs Rs 47.1L (FY23), then nil (FY24). Needs careful CMA Form III mapping.

8. **No Depreciation on most assets**: Only 5–7 small assets (phones, car, AC, TV) at 15% WDV. Total depreciation is tiny (Rs 11K–14K range). Not a significant CMA item.

9. **FY2024 BS discrepancy**: Source Excel file has a Rs 9,599.90 imbalance. This is in the source data itself — flag for the Opus agent but do not attempt to correct.

10. **FY2025 PDFs have no previous year data**: The three FY2025 PDFs contain only current year (2024-25) figures. No FY2023-24 comparative column available from PDFs. Cross-check with mehta_fs_2024.json for prior year.

---

## Issues & Observations

- CMA INPUT SHEET contains 146 non-zero rows — above typical 50-100 range, because projected year rows are also present (skip them in reverse engineering)
- FA schedule in FY2024 xlsx has headers referencing FY2022-23 dates — cosmetic error, amounts are correct for FY2023-24
- Duplicate asset serial number 2 in FY2022 FA sheet — minor data entry error
- Sch BS sheet in FY2023 shows previous year figure in Direct Income row — minor cosmetic issue
- All profits fully appropriated each year (zero retained earnings carried forward on BS) — consistent with proprietorship drawings pattern

---

## Ready for Reverse Engineering

- [x] All CMA rows extracted (146 rows, FY2021-22 to FY2023-24)
- [x] All financial years extracted (FY2022, FY2023, FY2024 from Excel; FY2025 from PDF)
- [x] All outputs validated (5/5 files are valid JSON, sizes confirmed)
- [x] Session notes complete

**Next step:** Open a NEW Claude Code window and run the Opus reverse engineering prompt.

Read these files for reverse engineering:
```
Mehta computer/mehta_cma_extraction.json    ← CMA rows with amounts (in lakhs)
Mehta computer/mehta_fs_2022.json           ← FY2021-22 FS (amounts in rupees ÷ 1L = lakhs)
Mehta computer/mehta_fs_2023.json           ← FY2022-23 FS (amounts in rupees ÷ 1L = lakhs)
Mehta computer/mehta_fs_2024.json           ← FY2023-24 FS (amounts in rupees ÷ 1L = lakhs)
Mehta computer/mehta_fs_2025.json           ← FY2024-25 FS from PDFs (for context only — not in CMA actuals)
cma_template_reference.json                 ← CMA row definitions and hierarchy
```

**⚠️ Key instruction for Opus**: All FS amounts are in absolute rupees. CMA amounts are in lakhs. Divide FS amounts by 1,00,000 before comparing to CMA rows.
