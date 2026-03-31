# Baseline Accuracy Report

**Date:** 2026-03-23
**Prompt:** baseline (from ai_classifier.py)

## Summary

| Metric | Value |
|--------|-------|
| Total items tested | 352 |
| Correct | 276 (78.4%) |
| Wrong | 76 (21.6%) |
| Uncertain (conf < 0.8) | 26 |

## By Confidence Level

| Confidence | Items | Correct | Accuracy |
|------------|-------|---------|----------|
| >= 0.9 | 241 | 207 | 85.9% |
| 0.8-0.89 | 85 | 56 | 65.9% |
| < 0.8 | 26 | 13 | 50.0% |

## By Sheet

| Sheet | Items | Correct | Accuracy |
|-------|-------|---------|----------|
| Co., Deprn  | 40 | 37 | 92.5% |
| Notes BS (1) | 6 | 6 | 100.0% |
| Notes BS (2) | 124 | 100 | 80.6% |
| Notes to P & L | 112 | 90 | 80.4% |
| Subnotes to BS | 51 | 36 | 70.6% |
| Subnotes to PL | 19 | 7 | 36.8% |

## Failure Patterns (76 failures)

| Pattern | Count | % of Failures |
|---------|-------|---------------|
| Adjacent field (within 5 rows) | 37 | 48.7% |
| Depreciation / Fixed asset routing | 8 | 10.5% |
| Loan classification | 7 | 9.2% |
| Other | 6 | 7.9% |
| Employee expense routing | 5 | 6.6% |
| Statutory dues / provisions | 4 | 5.3% |
| Others overflow | 3 | 3.9% |
| Section confusion (P&L vs BS) | 2 | 2.6% |
| Creditors / payables routing | 2 | 2.6% |
| Interest routing (term/WC/bank) | 1 | 1.3% |
| Inventory / stock confusion | 1 | 1.3% |

## Detailed Failures by Pattern


### Adjacent field (within 5 rows) (37 items)

| Raw Text | Expected (Row) | Predicted (Row) | Conf | Section |
|----------|----------------|-----------------|------|---------|
| Other Materials Comsumed - Scrap | Stores and spares consumed (Indigenous) (44) | Others (Manufacturing) (49) | 0.85 | note 21 - other materials consumed |
| Machinery Maintenance | Others (Manufacturing) (49) | Repairs & Maintenance (Manufacturing) (50) | 0.95 | other expenses |
| Selling & Distribution Expenses | Advertisements and Sales Promotions (70) | Others (Admin) (71) | 0.75 | auditor's remuneration: |
| Packing Materials - GST @ 12% | Advertisements and Sales Promotions (70) | Others (Admin) (71) | 0.70 | selling and distribution expenses - subn |
| Packing Materials - GST @ 18% | Advertisements and Sales Promotions (70) | Others (Admin) (71) | 0.70 | selling and distribution expenses - subn |
| Discount Allowed | Advertisements and Sales Promotions (70) | Others (Admin) (71) | 0.80 | selling & distribution expenses |
| Rates & Taxes | Others (Admin) (71) | Rent, Rates and Taxes (68) | 0.95 | other expenses |
| Interest on C.C. A/c | Interest on Fixed Loans / Term loans (83) | Interest on Working capital loans (84) | 0.95 | interest expenses: |
| Axis Bank Channel Financing | Working Capital Bank Finance - Bank 1 (131) | Working Capital Bank Finance - Bank 2 (132) | 0.85 | secured |
| Axis Bank Sellers Credit Fongei - I | Term Loan Balance Repayable after one year (137) | Term Loan Repayable in next one year (136) | 0.80 | term loans from banks  - secured: non cu |
| Electronic Cash Ledger (GST) | Security deposits with government departments (237) | Other non current assets (238) | 0.75 | security deposits: |
| GST Input Recoverable | Advances recoverable in cash or in kind (219) | Other Advances / current asset (223) | 0.85 | other current assets |
| TDS Recoverable | Advance Income Tax (221) | Other Advances / current asset (223) | 0.82 | note 16 - short-term loans and advances |
| Bonus payable | Other statutory liabilities (due within 1 year) (246) | Other current liabilities (250) | 0.90 | note 7 - other current liabilities |
| Other Materials Comsumed - Scrap (FY22) | Stores and spares consumed (Indigenous) (44) | Others (Manufacturing) (49) | 0.78 | note 22 - changes in inventories |
| Selling & Distribution Expenses (FY22) | Advertisements and Sales Promotions (70) | Others (Admin) (71) | 0.75 | tax audit |
| Bill Discounting Charges (FY22) | Interest on Working capital loans (84) | Bank Charges (85) | 0.88 | other borrowing costs: |
| Axis Term Loan No. 312175 (FY22) | Term Loan Balance Repayable after one year (137) | Term Loan Repayable in next one year (136) | 0.90 | term loans from banks  - secured: non cu |
| GST Input Recoverable (FY22) | Advances recoverable in cash or in kind (219) | Other Advances / current asset (223) | 0.80 | other current assets |
| Bonus payable (FY22) | Other statutory liabilities (due within 1 year) (246) | Other current liabilities (250) | 0.88 | note 7 - other current liabilities |
| Other Materials Comsumed - Scrap (FY23) | Stores and spares consumed (Indigenous) (44) | Raw Materials Consumed (Indigenous) (42) | 0.80 | note 22 - changes in inventories |
| Selling & Distribution Expenses (FY23) | Advertisements and Sales Promotions (70) | Others (Admin) (71) | 0.70 | auditor's remuneration: |
| Discount Allowed (FY23) | Advertisements and Sales Promotions (70) | Others (Admin) (71) | 0.75 | selling & distribution expenses |
| Rent (in Admin row) (FY23) | Others (Admin) (71) | Rent, Rates and Taxes (68) | 0.95 | note 27 |
| Administrative & General Expenses (FY23) | Advertisements and Sales Promotions (70) | Others (Admin) (71) | 0.90 | auditor's remuneration: |
| Bill Discounting Charges (FY23) | Interest on Working capital loans (84) | Bank Charges (85) | 0.85 | other finance costs: |
| Yes Bank Channel Finance (FY23) | Working Capital Bank Finance - Bank 1 (131) | Working Capital Bank Finance - Bank 2 (132) | 0.75 | secured |
| Axis Bank TL-V Business Empower (FY23) | Term Loan Balance Repayable after one year (137) | Term Loan Repayable in next one year (136) | 0.85 | note 5 - short-term borrowings |
| Axis Term Loan No. 879974 (FY23) | Term Loan Balance Repayable after one year (137) | Term Loan Repayable in next one year (136) | 0.90 | note 5 - short-term borrowings |
| GST Input Recoverable (FY23) | Advances recoverable in cash or in kind (219) | Other Advances / current asset (223) | 0.85 | other current assets |
| Bonus payable (FY23) | Other statutory liabilities (due within 1 year) (246) | Other current liabilities (250) | 0.85 | note 7 - other current liabilities |
| YELLOW  SPECTRUM TECHNOLOGIES | Other Advances / current asset (223) | Advances to suppliers of raw materials (220) | 0.85 | subnotes to BS - advance to suppliers -  |
| More than 365 days | Domestic Receivables (206) | Debtors more than six months (208) | 0.90 | subnotes to BS - trade receivables |
| Unpaid Trainee Stipend | Other statutory liabilities (due within 1 year) (246) | Other current liabilities (250) | 0.85 | subnotes to BS - unpaid salary & wages |
| NMTG Mechtrans Techiques Pvt Ltd | Other Advances / current asset (223) | Advances to suppliers of raw materials (220) | 0.85 | subnotes to BS - advance to suppliers -  |
| Kone Cranes and Demag Pvt Ltd | Other current liabilities (250) | Creditors for Expenses (249) | 0.75 | subnotes to BS - creditors for fixed ass |
| ELRKE INDUSTRIAL ENTERPRIESES | Other current liabilities (250) | Creditors for Expenses (249) | 0.75 | subnotes to BS - creditors for fixed ass |

### Depreciation / Fixed asset routing (8 items)

| Raw Text | Expected (Row) | Predicted (Row) | Conf | Section |
|----------|----------------|-----------------|------|---------|
| Depreciation | Depreciation (CMA) (63) | Depreciation (Manufacturing) (56) | 0.85 | depreciation & amortisation expense |
| Amortization Expenses | Depreciation (CMA) (63) | Other Amortisations (77) | 0.90 | depreciation & amortisation expense |
| Depreciation (FY22) | Depreciation (CMA) (63) | Depreciation (Manufacturing) (56) | 0.88 | depreciation & amortisation expense |
| Amortization Expenses (FY22) | Depreciation (CMA) (63) | Other Amortisations (77) | 0.95 | depreciation & amortisation expense |
| Amortization Expenses (FY23) | Depreciation (CMA) (63) | Other Amortisations (77) | 0.90 | depreciation & amortisation expense |
| Depreciation - Building (For the Year) | Depreciation (CMA) (63) | Depreciation (Manufacturing) (56) | 0.90 | depreciation schedule - for the year |
| Depreciation - Software (Intangible) (For the Year | Depreciation (Manufacturing) (56) | Other Amortisations (77) | 0.92 | depreciation schedule - intangible asset |
| Total Depreciation for the Year (All Assets - Tang | Depreciation (Manufacturing) (56) | Depreciation (CMA) (63) | 0.85 | depreciation schedule - grand total |

### Loan classification (7 items)

| Raw Text | Expected (Row) | Predicted (Row) | Conf | Section |
|----------|----------------|-----------------|------|---------|
| Mr. Chaitra Sunderesh (Director Loan) | Unsecured Loans - Quasi Equity (152) | Dues from directors / partners / promoters (235) | 0.95 | (i) due to directors |
| Mrs. Ronak S. Bagadia (Director Loan) | Unsecured Loans - Quasi Equity (152) | Dues from directors / partners / promoters (235) | 0.95 | (i) due to directors |
| Mr. Nishanth Sunderesh (Director Loan) | Unsecured Loans - Quasi Equity (152) | Dues from directors / partners / promoters (235) | 0.95 | (i) due to directors |
| Axis Bank ECGS/ECLGC (FY22) | Term Loan Balance Repayable after one year (137) | Working Capital Bank Finance - Bank 1 (131) | 0.80 | note 5 - short-term borrowings |
| Mr. Chaitra Sundaresh (FY23 Director Loan) | Unsecured Loans - Quasi Equity (152) | Dues from directors / partners / promoters (235) | 0.92 | (i) due to directors |
| Mrs. Ronak S. Bagadia (FY23 Director Loan) | Unsecured Loans - Quasi Equity (152) | Dues from directors / partners / promoters (235) | 0.92 | (i) due to directors |
| Mr. Nishanth Sunderesh (FY23 Director Loan) | Unsecured Loans - Quasi Equity (152) | Dues from directors / partners / promoters (235) | 0.92 | (i) due to directors |

### Other (6 items)

| Raw Text | Expected (Row) | Predicted (Row) | Conf | Section |
|----------|----------------|-----------------|------|---------|
| Carriage Outwards | Advertisements and Sales Promotions (70) | Freight and Transportation Charges (47) | 0.95 | selling & distribution expenses |
| Unsecured Considered Good (non-current receivable) | Other non current assets (238) | Debtors more than six months (Non-Current) (232) | 0.85 | long-term trade  receivables |
| Advances Written off (FY22) | Bad Debts (69) | Miscellaneous Expenses written off (75) | 0.92 | note 27 |
| Trade Receivables > 6 months (FY22) | Debtors more than 6 months (208) | Debtors more than six months (Non-Current) (232) | 0.95 | note 14 - trade receivables |
| Carriage Outwards (FY23) | Advertisements and Sales Promotions (70) | Freight and Transportation Charges (47) | 0.95 | selling & distribution expenses |
| Scrap Loading & Unloading Charges (FY23) | Advertisements and Sales Promotions (70) | Freight and Transportation Charges (47) | 0.85 | selling & distribution expenses |

### Employee expense routing (5 items)

| Raw Text | Expected (Row) | Predicted (Row) | Conf | Section |
|----------|----------------|-----------------|------|---------|
| Contribution to PF & Other Funds | Wages (45) | Salary and staff expenses (67) | 0.88 | employee benefits expense |
| Labour Welfare Expenses | Wages (45) | Salary and staff expenses (67) | 0.85 | employee benefits expense |
| Directors Remuneration | Salary and staff expenses (67) | Audit Fees & Directors Remuneration (73) | 0.95 | salaries & wages |
| Directors Remuneration (FY22) | Salary and staff expenses (67) | Audit Fees & Directors Remuneration (73) | 0.95 | salaries & wages |
| Directors Remuneration (FY23) | Salary and staff expenses (67) | Audit Fees & Directors Remuneration (73) | 0.98 | salaries & wages |

### Statutory dues / provisions (4 items)

| Raw Text | Expected (Row) | Predicted (Row) | Conf | Section |
|----------|----------------|-----------------|------|---------|
| TDS-Rent-94I | Advance Income Tax (221) | Other statutory liabilities (due within 1 year) (246) | 0.88 | subnotes to BS - tds & tcs payable |
| TDS 2021-22 | Advance Income Tax (221) | Other statutory liabilities (due within 1 year) (246) | 0.90 | subnotes to BS - tax deducted @ source |
| TDS 2022-23 | Advance Income Tax (221) | Other statutory liabilities (due within 1 year) (246) | 0.95 | subnotes to BS - tax deducted @ source |
| TAX COLLECTED AT SOURCE 1% | Advance Income Tax (221) | Other statutory liabilities (due within 1 year) (246) | 0.90 | subnotes to BS - tds & tcs payable |

### Others overflow (3 items)

| Raw Text | Expected (Row) | Predicted (Row) | Conf | Section |
|----------|----------------|-----------------|------|---------|
| Leave Encashment (Short-term Provision) | Provision for Taxation (244) | Other current liabilities (250) | 0.85 | provision  for employee benefits |
| Packing Materials @ 12% (FY23) | Advertisements and Sales Promotions (70) | Others (Manufacturing) (49) | 0.80 | selling and distribution expenses - subn |
| Packing Materials @ 18% (FY23) | Advertisements and Sales Promotions (70) | Others (Manufacturing) (49) | 0.80 | selling and distribution expenses - subn |

### Section confusion (P&L vs BS) (2 items)

| Raw Text | Expected (Row) | Predicted (Row) | Conf | Section |
|----------|----------------|-----------------|------|---------|
| Ronak.S. Bagadia - Remuneration | Creditors for Expenses (249) | Audit Fees & Directors Remuneration (73) | 0.95 | subnotes to BS - director remuneration p |
| ASHWINI M CHAITRA REMUNERATION | Creditors for Expenses (249) | Audit Fees & Directors Remuneration (73) | 0.95 | subnotes to BS - director remuneration p |

### Creditors / payables routing (2 items)

| Raw Text | Expected (Row) | Predicted (Row) | Conf | Section |
|----------|----------------|-----------------|------|---------|
| Bisineer Sales & Marketing | Sundry Creditors for goods (242) | Creditors for Expenses (249) | 0.90 | subnotes to BS - sundry creditors - purc |
| STARLINE PACKERS PVT LTD | Sundry Creditors for goods (242) | Creditors for Expenses (249) | 0.90 | subnotes to BS - sundry creditors - purc |

### Interest routing (term/WC/bank) (1 items)

| Raw Text | Expected (Row) | Predicted (Row) | Conf | Section |
|----------|----------------|-----------------|------|---------|
| Interest Paid on Unsecured Loan | Interest on Fixed Loans / Term loans (83) | Others (Non-Operating Expenses) (93) | 0.75 | interest expenses: |

### Inventory / stock confusion (1 items)

| Raw Text | Expected (Row) | Predicted (Row) | Conf | Section |
|----------|----------------|-----------------|------|---------|
| Scraps (FY22 inventory) | Stores and Spares Indigenous (198) | Other current assets (223) | 0.75 | inventories |

## Token Usage & Cost

| Metric | Value |
|--------|-------|
| Total input tokens | 72,140 |
| Total output tokens | 40,270 |
| Avg input per item | 205 |
| Avg output per item | 114 |
| Batches | 24 |
| Est. input cost | $0.058 |
| Est. output cost | $0.161 |
| **Est. total cost** | **$0.219** |