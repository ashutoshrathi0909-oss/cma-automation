# Session Report — 2026-03-22
# Files Created: 7-Company Classification Analysis

## Overview

**Date:** 2026-03-22
**Session Goal:** Analyze financial data from 7 real companies to build classification rules for the CMA Automation System. Each company's financials (3-4 years) were extracted and compared against a manually-prepared CMA (ground truth) to identify line items that the app's existing 384-item reference mapping does NOT cover.

**Source Data Location:** `FInancials main/` — contains 7 company folders with PDFs, Excel files, and ground truth CMA files.

**What was produced:** 14 files — 7 extraction references + 7 classification rule sets.

---

## Files Created

### A. Extraction References (7 files)

These files document EVERY line item extracted from each company's financial statements. They serve as the **ground truth for testing the app's extraction pipeline** — we compare what the app extracts (via openpyxl for Excel, Qwen vision for PDFs) against these reference documents.

| # | File Path | Size | Company | Source Files | Purpose |
|---|-----------|------|---------|-------------|---------|
| 1 | `DOCS/extractions/BCIPL_extraction_reference.md` | 42 KB | BCIPL (Manufacturing) | 3 Excel files (FY20-23) | Reference for openpyxl extraction testing. Contains 1,656 line items across 3 years. Flags FY21-22 "lakhs" unit issue. |
| 2 | `DOCS/extractions/SR_Papers_extraction_reference.md` | 19 KB | SR Papers (Distribution) | 3 Excel files (FY23-26) | Reference for openpyxl extraction testing. ~100 line items per year. Includes verification checkpoints. |
| 3 | `DOCS/extractions/SSSS_extraction_reference.md` | 47 KB | SSSS (Steel Trading) | 3 Excel files (FY22-25) | Reference for openpyxl extraction testing. FY23 most detailed (~85 items), FY24-25 summarized (~35 items). |
| 4 | `DOCS/extractions/MSL_extraction_reference.md` | 18 KB | MSL (Manufacturing) | 3 PDFs + 1 Excel (FY23-25) | Mixed reference — Excel is primary source (PDFs were partially unreadable). 8 reconciliation cross-checks verified. |
| 5 | `DOCS/extractions/SLIPL_extraction_reference.md` | 14 KB | SLIPL (Shoe Manufacturing) | 3 PDFs + 1 Excel (FY22-25) | Mixed reference — Excel best for FY25, PDFs for FY22-24. Notes auditor qualifications affecting Row 69 and Row 255. |
| 6 | `DOCS/extractions/INPL_extraction_reference.md` | 23 KB | INPL (Mfg + R&D Hybrid) | 3 scanned PDFs (FY22-25) | **First fully-scanned PDF extraction.** ~120 items. All pages clear. Flags unit change (Rs.'000 → Lakhs in FY25). 5 OCR uncertainty items documented. |
| 7 | `DOCS/extractions/Kurunji_Retail_extraction_reference.md` | 19 KB | Kurunji Retail (Retail Partnership) | 2 ITR PDFs + 1 audited PDF (FY22-25) | **First ITR-format extraction.** ~75 items. Large files (245MB, 266MB) required PyMuPDF rendering. Moderate OCR reliability. |

#### How to use these files:
1. Upload a company's financial files to the app
2. Trigger extraction in the app
3. Compare the app's extracted line items against the corresponding extraction reference file
4. Any mismatches indicate extraction bugs to fix

---

### B. Classification Rules (7 files)

These files document NEW classification rules discovered from each company — patterns that the existing 384-item reference mapping and V1 rules do NOT cover. Each rule follows a standard format with: pattern, CMA row, real example, and CA verification checkbox.

| # | File Path | Size | Company | Industry | New Rules | Key Findings |
|---|-----------|------|---------|----------|-----------|-------------|
| 1 | `DOCS/rules/BCIPL_classification_rules.md` | 34 KB | BCIPL | Manufacturing (stamping/sheet metal) | 22 rules (BCIPL-001 to BCIPL-022) | First manufacturing company. Directors Remuneration split (R67), Job Work override to R46, Bill Discounting to R84, ECGS/ECLGS loans, Forex sign-dependent routing. 3 rules override the 384-ref with more correct mappings. |
| 2 | `DOCS/rules/SR_Papers_classification_rules.md` | 39 KB | SR Papers | Distribution (paper distributor, NOT manufacturer) | 22 rules (SRP-001 to SRP-022) | India-specific terms (Hamali, Mathadi). Finance Cost → DOUBT rule (SRP-015). Discount Received vs Allowed pair. ~8 rules overlap with BCIPL. |
| 3 | `DOCS/rules/SSSS_classification_rules.md` | 33 KB | SSSS (Salem Stainless Steel) | Trading (stainless steel) | 14 rules (SSSS-001 to SSSS-014) | ₹9 Cr vendor discount impact (SSSS-001). Steel-specific terms (Cutting Labour, Weighment). 4 duplicates of prior rules (validates existing rules). Promoter loan split not automatable. |
| 4 | `DOCS/rules/MSL_classification_rules.md` | 24 KB | MSL | Manufacturing (metal stamping/dies) | 10 rules (MSL-001 to MSL-010) | "Stock in Trade" mislabel in mfg inventory (MSL-001). Export Incentive EXCLUDED from CMA (MSL-005) — conflicts with BCIPL-022. Gratuity provision to R153 (new). Suggests updates to C-003 and BCIPL-015. |
| 5 | `DOCS/rules/SLIPL_classification_rules.md` | 20 KB | SLIPL | Manufacturing (shoe soles) | 12 rules (SLI-001 to SLI-012) | **3 critical conflicts identified:** Packing (R49 vs R70), KMP Remuneration (R45 vs R67), Private Deposits (R238 vs R237). Factory Rent to R49. Moulds/Dies to R162. V1 C-004 must be split. |
| 6 | `DOCS/rules/INPL_classification_rules.md` | 38 KB | INPL (Nanoventions) | Manufacturing + R&D Services (hybrid) | 14 rules (INPL-001 to INPL-014) | **First hybrid company** — 9 genuinely novel rules. Service Revenue to R22, Unbilled Services to R206, R&D Expenses to R49, Digital Wallet to R223. Directors Remuneration to R73 (3rd conflicting treatment). ~70 items covered by existing rules = validation of rule maturity. |
| 7 | `DOCS/rules/Kurunji_Retail_classification_rules.md` | 34 KB | Kurunji Retail | Retail Trading (Partnership firm) | 15 rules (KR-001 to KR-015) | **First partnership firm** — Partners' Capital (R116), Salary (R73), Interest (R83). Retail-specific: Barcode Expenses, Bill Printing Roll, Digital Marketing. Packing now 3-way conflict (R44 vs R49 vs R70). Private deposits R238 confirmed by 3rd company. |

#### How to use these files:
1. Get CA (Boss) verification on the checkbox items in each file
2. After verification, merge all rules into a single `classification_rules_v2.md`
3. Implement verified rules in `backend/app/services/classification/rule_engine.py`
4. Add industry-axis support to the rule engine (rules need to know: manufacturing vs trading vs retail vs service)

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total files created | 14 |
| Total file size | ~385 KB |
| Total rules created | 119 |
| Unique rules (after deduplication) | ~85-90 |
| Rules confirmed by 2+ companies | ~15 |
| Unresolved conflicts | 8 (pending CA verification) |
| Industries covered | Manufacturing (3), Trading (2), Distribution (1), Hybrid Mfg+R&D (1) |
| Entity types covered | Pvt Ltd (6), Partnership (1) |
| Financial years covered | FY2020-21 through FY2025-26 |
| File types processed | Excel (.xls, .xlsx), PDF (native), PDF (scanned), ITR PDF |

---

## Unresolved Conflicts (8 items for CA)

These conflicts arose because different CAs classified the same type of line item to different CMA rows. The Boss must decide the firm's standard practice for each.

| # | Conflict | Company A | Company B | Company C | Priority |
|---|----------|-----------|-----------|-----------|----------|
| 1 | Directors/Partners Remuneration | BCIPL → R67 | SLIPL/MSL → R45 | INPL/Kurunji → R73 | 🔴 HIGH |
| 2 | Packing Materials | BCIPL → R70 | SLIPL → R49 | Kurunji → R44 | 🔴 HIGH |
| 3 | Related Party Loans (LT) | BCIPL/SSSS → R152 | INPL → R137 | — | 🔴 HIGH |
| 4 | Discount Received | SR Papers → R34 | SSSS → R42 | — | 🟡 MEDIUM |
| 5 | Retail Store Rent | Kurunji → R49 | All others → R68 | — | 🟡 MEDIUM |
| 6 | Generator Expenses | Kurunji → R71 | Standard → R48 | — | 🟡 MEDIUM |
| 7 | Export Incentives | MSL → Exclude | SLIPL → R23 | BCIPL → R34 | 🟡 MEDIUM |
| 8 | R&M in Manufacturing | MSL/INPL/BCIPL → R50 | SLIPL → R72 | — | 🟡 MEDIUM |

---

## Already Resolved (No conflict)

These patterns were confirmed by multiple companies and can be implemented immediately:

| Pattern | CMA Row | Confirmed By |
|---------|---------|-------------|
| Motor Vehicles → Gross Block | R162 | All 7 companies |
| Job Work Charges → Processing | R46 | BCIPL + SSSS + SLIPL + MSL |
| Interest on Unsecured/Partner Loans | R83 | BCIPL + SSSS + INPL + Kurunji |
| Promoter/Director Loans → Quasi Equity | R152 | BCIPL + SSSS + SLIPL + MSL |
| Security Deposits: Govt → R237, Private → R238 | R237/R238 | SLIPL + INPL + Kurunji |
| Customs Duty → Imported RM | R41 | SR Papers + SSSS |
| All R&M → Manufacturing (for mfg firms) | R50 | MSL + INPL + BCIPL |
| Hamali/Cooly/Cartage → Freight | R47 | SR Papers + SSSS |
| Digital Marketing → Advertisements | R70 | Kurunji |
| TDS on Rent → combine with Rent | Same row | Kurunji |

---

## What Comes Next

### Immediate (when Boss is available)
1. Show Boss the 8 conflicts — get his rulings
2. Show Boss the individual rule files — get checkbox verifications

### After CA Verification
3. Merge all verified rules into `DOCS/classification_rules_v2.md`
4. Implement in `backend/app/services/classification/rule_engine.py`
5. Add industry-axis to rule engine (manufacturing / trading / retail / service / partnership)

### Testing Phase
6. Start Docker services
7. Upload BCIPL files (Excel-only, easiest)
8. Compare app's openpyxl extraction against `DOCS/extractions/BCIPL_extraction_reference.md`
9. Run classification → compare against `DOCS/rules/BCIPL_classification_rules.md`
10. Generate Excel → compare against ground truth CMA
11. Repeat for all 7 companies

### Known Blockers for Testing
- **Kurunji Retail PDFs (245MB, 266MB)** exceed the app's 50MB upload limit — need compression or limit increase
- **INPL unit change** (Rs.'000 → Lakhs) — app needs unit detection/confirmation
- **MSL scanned PDFs** — partially unreadable, Excel was primary source

---

## Source Data Reference

All source financials are in `FInancials main/`:

| Company Folder | Financial Files | Ground Truth CMA |
|---------------|----------------|-----------------|
| `FInancials main/BCIPL/` | 3 × .xls (FY20-23) | `CMA BCIPL 12012024.xls` |
| `FInancials main/SR Papers/` | 3 × .xls (FY23-26) | `CMA S.R.Papers 09032026 v2.xls` |
| `FInancials main/SSSS/` | 3 × .xlsx (FY22-25) | `CMA 4S 26122025.xlsx` |
| `FInancials main/MSL - Manufacturing/` | 3 × .pdf + 1 × .xlsx | `MSL CMA 24102025.xls` |
| `FInancials main/SLIPL/` | 3 × .pdf + 1 × .xlsx | `SLI CMA 31102025.xls` |
| `FInancials main/INPL/` | 3 × .pdf (scanned) | `Nanoventions CMA 10032026.xls` |
| `FInancials main/Kurunji Retail/` | 2 × ITR .pdf + 1 × .pdf | `CMA Kurinji retail 23012026.xls` |
