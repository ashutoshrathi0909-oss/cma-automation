# GT Row Verification Summary

**Date:** 2026-03-27  
**Canonical labels:** 131  

---

## Location A — `CMA_Ground_Truth_v1/companies/`

| Company | Entries | Dominant Offset | % Affected | Corrected? |
|---------|---------|-----------------|------------|------------|
| BCIPL | 224 | -1 | 100.0% | ✅ Yes |
| Dynamic_Air | 230 | -1 | 100.0% | ✅ Yes |
| INPL | 186 | -1 | 100.0% | ✅ Yes |
| Kurunji_Retail | 49 | -1 | 100.0% | ✅ Yes |
| Mehta_Computer | 74 | -1 | 100.0% | ✅ Yes |
| MSL | 222 | -1 | 100.0% | ✅ Yes |
| SLIPL | 114 | -1 | 100.0% | ✅ Yes |
| SR_Papers | 164 | -1 | 100.0% | ✅ Yes |
| SSSS | 63 | -1 | 100.0% | ✅ Yes |

## Location B — `DOCS/extractions/`

| Company | Entries | Row Valid | Field Mismatches | Corrected? |
|---------|---------|-----------|-----------------|------------|
| BCIPL | 448 | 448 | 39 | ✅ Yes |
| INPL | 186 | 185 | 73 | ✅ Yes |
| Kurunji_Retail | 136 | 136 | 39 | ✅ Yes |
| MSL | 110 | 108 | 40 | ✅ Yes |
| SLIPL | 65 | 65 | 21 | ✅ Yes |
| SR_Papers | 216 | 216 | 17 | ✅ Yes |
| SSSS | 294 | 294 | 86 | ✅ Yes |

## Cross-Check (Location A corrected vs Location B)

| Company | A Entries | B Entries | Agree | Disagree |
|---------|-----------|-----------|-------|----------|
| BCIPL | 224 | 448 | 27 | 3 |
| INPL | 186 | 186 | 54 | 13 |
| Kurunji_Retail | 49 | 136 | 18 | 2 |
| MSL | 222 | 110 | 10 | 0 |
| SLIPL | 114 | 65 | 4 | 0 |
| SR_Papers | 164 | 216 | 72 | 9 |
| SSSS | 63 | 294 | 2 | 2 |

---

## Notes

- Original GT files are **not modified**. Corrected versions saved as `*_corrected.json`.
- Canonical source of truth: `CMA_Ground_Truth_v1/reference/canonical_labels.json`
- Cross-check matches entries by `(raw_text, financial_year)` — only exact-text matches are compared.
- Field name comparison uses substring matching (canonical name inside stored field or vice versa).

## Disagreement Details

### BCIPL
| Raw Text | FY | Location A Row | Location B Row |
|----------|----|----------------|----------------|
| Machinery Maintenance | 2021 | 72 | 49 |
| Bad debts written off | 2021 | 71 | 69 |
| Selling & Distribution Expenses | 2021 | 73 | 70 |

### INPL
| Raw Text | FY | Location A Row | Location B Row |
|----------|----|----------------|----------------|
| Salary, Wages and Bonus | 2023 | 67 | 45 |
| Consultancy Charges | 2023 | 71 | 49 |
| Packing and Forwarding Charges | 2023 | 49 | 47 |
| Project Cost | 2023 | 71 | 93 |
| Research and Development | 2023 | 71 | 49 |
| Staff Welfare Expenses | 2024 | 45 | 67 |
| Gratuity to Employees | 2024 | 45 | 67 |
| Consultancy Charges | 2024 | 71 | 49 |
| Material Handling Charges | 2024 | 46 | 49 |
| Staff Welfare Expenses | 2025 | 45 | 67 |
| Gratuity to Employees | 2025 | 45 | 67 |
| Consultancy Charges | 2025 | 71 | 49 |
| Finished Goods | 2025 | 59 | 201 |

### Kurunji_Retail
| Raw Text | FY | Location A Row | Location B Row |
|----------|----|----------------|----------------|
| Closing Stock | 2025 | 59 | 201 |
| Depreciation | 2025 | 56 | 63 |

### SR_Papers
| Raw Text | FY | Location A Row | Location B Row |
|----------|----|----------------|----------------|
| Computer Maintanance | 2023 | 72 | 71 |
| Manpower Charges | 2023 | 49 | 45 |
| Labour Charges | 2023 | 49 | 45 |
| TDS Receivable | 2023 | 219 | 221 |
| TCS Receivable | 2023 | 219 | 221 |
| Manpower Charges | 2024 | 49 | 45 |
| Discount Recieved | 2025 | 29 | 34 |
| Computer Maintanance | 2025 | 72 | 71 |
| Manpower Charges | 2025 | 49 | 45 |

### SSSS
| Raw Text | FY | Location A Row | Location B Row |
|----------|----|----------------|----------------|
| Current tax expense | 2024 | 244 | 99 |
| Share Investments | 2025 | 188 | 186 |
