# SR Papers Extraction Reference

**Company:** S.R. Papers Private Limited
**Industry:** Paper Trading / Distribution (multi-branch, import-heavy)
**CA Firm:** P.M. Chordia & Co., Chennai
**Financial Years Covered:** FY2023 (Mar 2023), FY2024 (Mar 2024), FY2025 (Mar 2025)
**All amounts in Indian Rupees (₹)**
**CMA prepared by:** Manual entry into CMA S.R.Papers 09032026 v2.xls

---

## How to Use This File

Compare these numbers cell-by-cell against what openpyxl extracts from the same Excel files.
The columns show: Description | FY2023 | FY2024 | FY2025 | Section

---

## Source File Structure

All 3 financial year files have the same sheet layout:
- **BS** — Balance Sheet summary (branch-wise columns)
- **P&L** — Profit & Loss summary (branch-wise columns)
- **Note 2** — Share Capital
- **Note 3-17** — Balance Sheet detail notes (Fixed Assets, Borrowings, Trade Payables, Loans & Advances)
- **Note 18-24** — P&L detail notes (Revenue, Other Income, Material Costs, Employee, Finance, Other Expenses)
- **Note bRANCH SCH** — Branch schedule
- **FA-Addition-hiddle** — Fixed Asset additions (hidden)
- **DEFFERED TAX** — Deferred tax workings
- **CASH FLOW** — Cash flow statement
- **Depreciation Chart** — Depreciation schedule

**Important:** Columns in Note 18-24 are:
- Col 1 = **TOTAL (all branches combined)** ← use this for CMA
- Col 2 = Chennai branch only
- Col 3–6 = Other branches (Pune, HYD, Gujarat, Bangalore)
- Col 7 = Prior year comparison

---

## PART 1: P&L LINE ITEMS

### Sheet: Note 18-24 (P&L Detail Notes)

#### Note 12: Revenue from Operations

| Line Item | FY2023 | FY2024 | FY2025 | CMA Field |
|-----------|--------|--------|--------|-----------|
| Paper & Paper Products (Sale of Products) | 32,66,19,171.63 | 33,95,27,844.07 | 36,31,51,560.28 | Domestic Sales (Row 22) |
| Networking Charges (Sale of Services) | 0 | 0 | 0 | — |
| Sales Return | 0 | 0 | 0 | — |
| **Total Revenue from Operations** | **32,66,19,171.63** | **33,95,27,844.07** | **36,31,51,560.28** | |

#### Note 13: Other Income

| Line Item | FY2023 | FY2024 | FY2025 | CMA Field |
|-----------|--------|--------|--------|-----------|
| Interest Income | 1,25,309 | 1,57,195.13 | 1,50,000 | Interest Received (Row 30) |
| Interest from FD | 0 | 1,99,004.79 | 18,40,101.44 | Interest Received (Row 30) |
| Rate Difference | 0 | 0 | 2,400 | Others (Non-Op Income) Row 34 |
| Discount Received | 31,88,891.18 | 36,55,025.12 | 69,622.83 | Others (Non-Op Income) Row 34 |
| Profit on Sale of Assets | 964 | 0 | 0 | Profit on sale of FA (Row 31) |
| Currency Exchange Profit | 79,608 | 0 | 0 | Gain on Exchange Fluctuations (Row 32) |
| Vehicle Haulting Charges | 10,000 | 0 | 0 | Others (Non-Op Income) Row 34 |
| Insurance Claim Received | 0 | 0 | 0 | — |
| Rent Received | 0 | 0 | 0 | — |
| Miscellaneous Income / Round Off | 0 | 0 | 0 | — |
| Delivery Charges (GST) | 0 | 0 | 0 | — |
| **Total Other Income** | **34,04,772.18** | **40,11,225.04** | **20,62,124.27** | |

#### Note 14: Cost of Material Consumed

| Line Item | FY2023 | FY2024 | FY2025 | CMA Field |
|-----------|--------|--------|--------|-----------|
| Purchase of Raw Materials | (included in total) | (included in total) | (included in total) | Raw Materials Indigenous (Row 42) |
| Purchase Return | 0 | 0 | 0 | — |
| **Total Cost of Material Consumed** | **23,07,54,135.60** | **23,61,03,955.10** | **25,43,28,290.17** | Raw Materials Indigenous (Row 42) |

> **Note:** No opening/closing stock adjustment shown in Note 14. The full purchase cost is
> treated as "consumed." Inventory movement is captured in the BS only.
> Customs Duty (Note 17) on imported paper is separately classified as Imported RM in CMA.

#### Note 15: Employee Benefits Expense

| Line Item | FY2023 | FY2024 | FY2025 | CMA Field |
|-----------|--------|--------|--------|-----------|
| Salary and Wages | 1,49,64,961 | 1,56,27,399 | 1,52,28,151 | Wages (Row 45) |
| Contributions to PF and other funds | 6,96,228 | 6,71,449 | 7,18,356 | Wages (Row 45) |
| Directors Remuneration | 49,20,000 | 49,20,000 | 49,20,000 | Audit Fees & Directors Rem. (Row 73) |
| Staff Welfare Expenses | 4,50,460.71 | 3,02,534.82 | 4,18,460.81 | Wages (Row 45) |
| **Total Employee Expenses** | **2,10,31,649.71** | **2,15,21,382.82** | **2,12,84,967.81** | |

> **CMA split:** Wages (Row 45) = Salary+Wages + PF + Staff Welfare
> Audit Fees & Directors Rem (Row 73) = Directors Remuneration + Audit Fees (from Note 17)

#### Note 16: Finance Cost

| Line Item | FY2023 | FY2024 | FY2025 | CMA Field |
|-----------|--------|--------|--------|-----------|
| Interest Expenses – Others (all types combined) | 2,83,88,410.50 | 3,34,35,150.17 | 3,49,89,599.33 | Split: TL (Row 83) + WC (Row 84) |
| **Total Finance Cost** | **2,83,88,410.50** | **3,34,35,150.17** | **3,49,89,599.33** | |

> **Note:** Finance Cost is shown as single "Others" line — no breakdown into TL vs WC.
> The CA splits it using the loan schedule in the Details/TL sheet.
> Bank Charges from Note 17 are added separately to Row 85.

#### Note 17: Other Expenses

| Line Item | FY2023 | FY2024 | FY2025 | CMA Field |
|-----------|--------|--------|--------|-----------|
| Advertisement | 0 | 0 | 0 | Advts & Sales Promotions (Row 70) |
| Audit Fees | 76,000 | 30,000 | 30,000 | Audit Fees & Directors Rem. (Row 73) |
| Admin Exp for PF | 25,300 | 25,254 | 26,711 | Salary and staff expenses (Row 67) |
| Barcode Charges | 22,557 | 0 | 0 | Others (Admin) (Row 71) |
| Power and Fuel | 18,62,538.50 | 14,48,512.46 | 15,62,728.37 | Power, Coal, Fuel and Water (Row 48) |
| Rent including lease rentals | 1,94,76,462 | 2,05,53,430 | 2,19,67,270 | Rent, Rates and Taxes (Row 68) |
| Forklift Charges | 2,300 | 0 | 0 | Others (Manufacturing) (Row 49) |
| Discount Allowed | 85,277.76 | 2,79,865.79 | 5,71,589.41 | Advts & Sales Promotions (Row 70) |
| Discount Reversal | (-)1,306 | 19,356 | 0 | Advts & Sales Promotions (Row 70) |
| Donation | 90,640 | 0 | 3,001 | Others (Non-Op Expenses) (Row 93) |
| Repairs and Maintenance | 17,57,801.83 | 17,90,987.06 | 15,44,063.61 | Repairs & Maintenance (Mfg) (Row 50) |
| Insurance | 4,85,537.43 | 5,25,503.50 | 5,36,444.89 | Others (Admin) (Row 71) |
| Rates and Taxes | 1,72,107.38 | 13,82,635.45 | 10,49,698.06 | Rent, Rates and Taxes (Row 68) |
| Communication and Connectivity | 1,73,040.57 | 1,43,560.80 | 3,24,235.59 | Others (Admin) (Row 71) |
| Computer Maintenance | 6,863.79 | 0 | 627.12 | Others (Admin) (Row 71) |
| Commission & Brokerage | 8,52,826.80 | 7,52,446 | 7,62,170 | Advts & Sales Promotions (Row 70) |
| Consultancy Fee | 1,57,900 | 0 | 4,60,000 | Others (Admin) (Row 71) |
| Gift | 0 | 0 | 0 | — |
| Entertainment Expenses | 1,030 | 0 | 0 | Others (Admin) (Row 71) |
| Travelling and Conveyance | 24,09,717.34 | 21,83,288.94 | 19,89,591.72 | Others (Admin) (Row 71) |
| Printing and Stationery | 4,47,863.15 | 2,02,691.01 | 84,987.95 | Others (Admin) (Row 71) |
| Stereo Charges | 1,06,763.20 | 1,90,354.17 | (-)5,500 | Advts & Sales Promotions (Row 70) |
| Packing & Forwarding | 1,72,133.42 | 93,895 | 1,03,263 | Others (Admin) (Row 71) |
| Postage | 54,144 | 50,131.20 | 13,985 | Others (Admin) (Row 71) |
| Processing Fee | 15,01,593.40 | 9,47,500 | 4,30,000 | Others (Admin) (Row 71) |
| Currency Exchange Loss | 24,843.33 | 1,50,279.56 | 0 | Loss on Exchange Fluctuations (Row 91) |
| Royalty Paid | 16,78,358.67 | 20,95,330.23 | 0 | Others (Manufacturing) (Row 49) |
| Round Off | 456.60 | 567.82 | (-)395.84 | — (immaterial) |
| Customs Duty | 13,12,396 | 5,80,553 | 90 | Raw Materials Consumed (Imported) (Row 41) |
| Clearance Charges | 1,48,750 | 45,200 | 1,072.38 | Other Manufacturing Exp CMA (Row 64) |
| CFS Charges | 2,13,843 | 99,500 | 0 | Other Manufacturing Exp CMA (Row 64) |
| Liner Charges | 3,09,772.30 | 1,18,876 | 0 | Other Manufacturing Exp CMA (Row 64) |
| Delivery Charges | 68,12,091.35 | 72,09,184.78 | 98,39,745.12 | Other Manufacturing Exp CMA (Row 64) |
| Unloading Charges – Mathadi | 2,18,260 | 90,415 | 92,110 | Freight and Transportation (Row 47) |
| Manpower Charges | 68,310 | 4,09,860 | 12,00,169 | Others (Manufacturing) (Row 49) |
| Design Charges | 32,900 | 5,300 | (-)31,000 | Advts & Sales Promotions (Row 70) |
| Business Promotion | 10,94,893.08 | 12,65,045.81 | 8,04,875.88 | Advts & Sales Promotions (Row 70) |
| Shop Expenses | 2,99,738.45 | 4,44,610.72 | 10,34,486.09 | Others (Admin) (Row 71) |
| Labour Charges | 1,03,606 | 0 | 0 | Others (Manufacturing) (Row 49) |
| FSC License Charges | 3,93,200 | 0 | 0 | Others (Admin) (Row 71) |
| Job Charges | 0 | 0 | 0 | — |
| Security Expenses | 0 | 0 | 0 | — |
| Training Expenses | 0 | 0 | 51,000 | Others (Admin) (Row 71) |
| Factory Expenses | 5,24,890 | 9,04,447 | 4,69,643 | Others (Manufacturing) (Row 49) |
| Tea & Food Expenses | 2,18,533 | 2,37,753 | 2,64,024 | Salary and staff expenses (Row 67) |
| Legal Fees | 25,500 | 0 | 0 | Others (Admin) (Row 71) |
| Late Payment Fees | 0 | 0 | 0 | — |
| Professional Fees | 16,66,954 | 33,25,089 | 28,63,777 | Others (Admin) (Row 71) |
| Bad Trade Receivables Written Off | 0 | 0 | 0 | Bad Debts (Row 69) |
| Loss on FA Sold/Scrapped | 0 | 0 | 0 | Loss on sale of FA (Row 89) |
| Miscellaneous Expenses | 2,380.03 | 0 | 0 | Others (Admin) (Row 71) |
| Membership Fees | 21,204 | 0 | 1,180 | Others (Admin) (Row 71) |
| Hamali Charges | 13,84,449 | 16,90,629 | 18,30,506 | Freight and Transportation (Row 47) |
| Bank Charges | 62,735.99 | 40,807.74 | 1,22,474.73 | Bank Charges (Row 85) |
| Furniture Exp | 0 | 0 | 2,37,412.13 | Repairs & Maintenance (Admin) (Row 72) |
| Contractor Fees | 0 | 0 | 1,53,826 | Others (Admin) (Row 71) |
| P&L on Sale of Car | 0 | 0 | 14,903 | Loss on sale of FA (Row 89) |
| **Total Other Expenses** | **4,65,57,606.37** | **4,93,32,860.04** | **5,04,04,765.21** | |

#### P&L Summary

| Line Item | FY2023 | FY2024 | FY2025 | CMA Field |
|-----------|--------|--------|--------|-----------|
| Depreciation and Amortisation | 26,60,559 | 23,72,101 | 22,76,838 | Depreciation (Row 56/63) |
| Profit / (Loss) Before Tax | 6,31,582.63 | (-)14,06,234.52 est. | (-)3,68,154.97 | — |
| Current Tax | 98,526 (FY2022) / 0 | 1,20,685 | 3,00,959 | Income Tax Provision (Row 99) |
| Deferred Tax (P&L) | (-)63,77,066 | +1,47,07,680 | +19,96,321 | Deferred Tax Liability (Row 100) |

---

## PART 2: BALANCE SHEET LINE ITEMS

### Source: BS Sheet + Note 3-17

#### EQUITY AND LIABILITIES

| Line Item | FY2023 | FY2024 | FY2025 | CMA Field |
|-----------|--------|--------|--------|-----------|
| **Share Capital** | | | | |
| Equity shares (200,000 shares × ₹10) | 20,00,000 | 20,00,000 | 20,00,000 | Issued, Subscribed, Paid Up (Row 116) |
| **Reserves and Surplus** | | | | |
| General Reserve | 75,00,000 | 75,00,000 | 75,00,000 | General Reserve (Row 121) |
| Share Premium | 1,92,00,000 | 1,92,00,000 | 1,92,00,000 | Share Premium A/c (Row 123) |
| P&L Balance (Surplus/Deficit) | (-)1,45,12,846.66 | (-)2,22,89,052.68 | (-)2,26,57,372.65 | Balance transferred from P&L (Row 122) |
| **Total Reserves** | 1,21,87,153.34 | 44,10,947.32 | 40,42,627.35 | |
| **Non-Current Liabilities** | | | | |
| Deferred Tax Liability (Net) | 1,30,70,573 | 2,14,01,187 | 2,14,01,187 | Deferred tax liability BS (Row 159) |
| Other Long Term Liabilities | 1,82,49,885.76 | 1,82,49,885.76 | 1,82,49,885.76 | Unsecured Loans – Quasi Equity (Row 152) |
| Long-term Provisions | 0 | 0 | 0 | — |
| **Current Liabilities** | | | | |
| Short-term Borrowings – Secured (Schedule Bank) | 17,94,69,358.18 | 18,32,27,592.25 | (included in total) | WC Bank Finance – HDFC Bank (Row 132) |
| Short-term Borrowings – Unsecured (Schedule Bank) | 10,70,49,239.59 | 13,35,65,333.12 | (see total) | WC Bank Finance – Indusind (Row 131) |
| Short-term Borrowings – Related Party | (inter-branch) | (inter-branch) | (see total) | (eliminated) |
| **Total Short-term Borrowings** | **28,65,18,597.77** | **31,67,92,925.37** | **35,77,24,613.25** | |
| Trade Payables – Other than Acceptances | 3,91,75,668.04 | 5,40,11,189.82 | 5,57,05,990.48 | Sundry Creditors for goods (Row 242) |
| Statutory Remittances (PF/GST/TDS) | (-)17,00,494.39 | (-)35,17,018.05 | (-)12,73,177.88 | Other statutory liabilities (Row 246) |
| Expenses Payable | 37,34,432.51 | 99,90,243.49 | (see OCL) | Creditors for Expenses (Row 249) |
| **Total Other Current Liabilities** | **20,33,938.12** | **64,73,225.44** | **(-)12,73,177.88** | |

> **Note on STL inter-branch:** The Short-term borrowings note shows Related Party unsecured
> amounts that are negative (inter-branch elimination). The consolidated total is what matters.
> Unsecured Related Party long-term loans (₹1,82,49,885.76) = Other Long Term Liabilities → Quasi Equity (Row 152).

#### ASSETS

| Line Item | FY2023 | FY2024 | FY2025 | CMA Field |
|-----------|--------|--------|--------|-----------|
| **Fixed Assets (Gross Block)** | | | | |
| Plant & Machinery (Gross) | 14,88,12,311.93 | 15,26,96,471.93 | (see total) | Gross Block (Row 162) |
| Electrical Equipment (Gross) | 19,16,588.26 | 19,16,588.26 | (see total) | Gross Block (Row 162) |
| Furniture & Fixtures (Gross) | 95,39,706.33 | 1,01,39,830.99 | (see total) | Gross Block (Row 162) |
| Vehicles (individual cars/bikes – list below) | 53,47,304.34 | 56,19,955.34 | (see total) | Gross Block (Row 162) |
| Office Equipment (AC, Computers) | 13,03,737.58 | 12,37,737.58 | (see total) | Gross Block (Row 162) |
| **Total Gross Block** | **16,95,48,648.44** | **17,40,82,933.10** | **17,21,93,913.10** | Gross Block (Row 162) |
| Less: Accumulated Depreciation | (-)2,08,86,020 | (-)2,32,58,121 | (-)2,37,80,842 | Less Accum. Depreciation (Row 163) |
| **Net Block** | **14,86,62,628.44** | **15,08,24,812.10** | **14,84,13,071.10** | |
| Capital Work in Progress | 0 | 0 | 0 | Capital WIP (Row 165) |
| **Vehicle list (FY2023):** Access 125, Grand i10, Car Jazz, Car XUV-500, Car XUV-300, Car Toyota Hyryder, Pulsar 150CC, Honda Activa, Jupiter, Jupiter 2023, Honda Dio, Yamaha FZ Bike 2022, Maruthi Nexa, Honda Unicorn | | | | Gross Block (Row 162) |
| **Current Assets** | | | | |
| Inventories (all paper stock) | 14,77,66,181.30 | 17,74,97,435.07 | 20,52,58,955.42 | Raw Material Indigenous BS (Row 194) |
| Trade Receivables (Unsecured – other) | 5,09,83,917.17 | 5,08,04,855.84 | 5,87,34,967.12 | Domestic Receivables (Row 206) |
| Debtors > 6 months | 0 | 0 | 0 | Debtors >6 months (Row 208) |
| Bank Balances (Current Accounts) | 1,51,923.72 | 9,13,727.90 | 9,13,727.90 | Bank Balances (Row 213) |
| Cash on Hand | 42,15,647.62 | 46,65,546.99 | 50,37,372.47 | Cash on Hand (Row 212) |
| **Total Cash & Bank** | **43,67,571.34** | **47,59,467.48** | **51,28,745.26** | |
| Loans to Related Parties (Unsecured) | 7,75,711.39 | 24,51,676.50 | (see total) | Advances recoverable (Row 219) |
| Security Deposits | 1,70,52,535.29 | 3,78,08,194.22 | 3,94,81,013.66 | Security deposits (Row 237) |
| Loans to Employees | 16,00,000 | 16,00,000 | (see total) | Advances recoverable (Row 219) |
| Prepaid Expenses | 0 | 0 | 0 | Prepaid Expenses (Row 222) |
| Other Loans & Advances | 17,60,569.87 | 15,20,113.35 | 28,30,758.75 | Other Advances / current asset (Row 223) |
| **Total Short-term Loans & Advances** | **2,11,88,816.55** | **3,93,28,307.57** | **4,22,62,622.39** | |
| TDS Receivable | 2,36,473.57 | 1,24,482.65 | 3,04,486.11 | Advance Income Tax (Row 221) |
| TCS Receivable | 30,227.66 | 0 | 45,822.56 | Advance Income Tax (Row 221) |
| **Total Other Current Assets** | **2,66,701.23** | **1,24,482.65** | **3,50,308.67** | |

---

## PART 3: DEPRECIATION BREAKDOWN

### Source: Note 3-17 (Fixed Assets section)

| Asset Category | FY2023 Gross | FY2023 Acc. Dep | FY2024 Gross | FY2024 Acc. Dep |
|----------------|-------------|-----------------|-------------|-----------------|
| Plant & Machinery + Electrical | 15,07,28,900.19 | 1,64,73,727 | 15,46,13,060.19 | 1,82,68,011 |
| Furniture & Fixtures | 95,39,706.33 | 2,62,059 | 1,01,39,830.99 | 4,92,725 |
| Vehicles | 53,47,304.34 | 34,48,238 | 56,19,955.34 | 37,09,156 |
| Office Equipment | 13,03,737.58 | 7,01,996 | 12,37,737.58 | 7,88,229 |

> **Note:** Depreciation total for FY2023 = ₹26,60,559 (from P&L).
> Note 3-17 shows additions/disposals by asset category.

---

## PART 4: VERIFICATION CHECKPOINTS

Use these to confirm openpyxl extractor is working correctly:

| Checkpoint | FY2023 Value | Sheet | Row |
|------------|-------------|-------|-----|
| Revenue from Operations (total) | 32,66,19,171.63 | Note 18-24 | Row 13 (Total) |
| Cost of Material Consumed (total) | 23,07,54,135.60 | Note 18-24 | Row 36 (Note 14 total) |
| Total Employee Expenses | 2,10,31,649.71 | Note 18-24 | Row 46 (Note 15 total) |
| Finance Cost (total) | 2,83,88,410.50 | Note 18-24 | Row 54 (Note 16 total) |
| Total Other Expenses | 4,65,57,606.37 | Note 18-24 | Row 123 (Note 17 total) |
| Total Assets (BS) | 37,32,35,816.03 | BS | Row 42 (TOTAL) |
| Inventories (BS) | 14,77,66,181.30 | BS | Row 36 |
| Trade Receivables (BS) | 5,09,83,917.17 | BS | Row 37 (first value) |
| Total Short-term Borrowings | 28,65,18,597.77 | BS | Row 18 (first value) |
| Trade Payables | 3,91,75,668.04 | Note 3-17 | Row 57 (total) |
| Gross Block (fixed assets) | 16,95,48,648.44 | Note 3-17 | Row 99 (total) ← Note: this is NET block in note; gross needs summing |
| Cash + Bank (total) | 43,67,571.34 | Note 3-17 | Row 159 (total) |
| Security Deposits | 1,70,52,535.29 | Note 3-17 | Row 169 (unsecured) |

---

## PART 5: NOTES ON MULTI-BRANCH STRUCTURE

SR Papers has 5 operational branches:
- Chennai (main, largest — ~70–80% of business)
- Pune
- Hyderabad
- Gujarat
- Bangalore

The CMA is prepared for the **consolidated company** (all branches combined).
The Note 18-24 column 1 (total) is what the app should extract.

Some inter-branch transactions appear as **negative amounts** in liabilities — these are internal eliminations. The app should recognize these and handle them (e.g., negative statutory remittances = refund due, not a liability).

---

## PART 6: ITEMS WITH ZERO VALUE (but present in template)

These appear in SR Papers' financials with ₹0 — important to confirm the extractor
does not skip them or treat them as missing:

- Sales Return (Note 12)
- Export Sales (all years = 0)
- Processing / Job Work Charges P&L (Row 46 CMA = 0)
- Stock in Process Opening/Closing (Rows 53/54 CMA = 0)
- Finished Goods Opening/Closing (Rows 58/59 CMA = 0)
- WIP Inventory BS (Row 200 = 0)
- Finished Goods BS (Row 201 = 0)
- Stores and Spares BS (Rows 197/198 = 0)
- All investments = 0
- Export receivables = 0
- Debtors > 6 months = 0
