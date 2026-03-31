# SSSS Extraction Reference

**Company:** Salem Stainless Steel Suppliers Private Limited
**CIN:** U51909TN2009PTC071911
**Industry Type:** Trading — Stainless Steel Distribution
**Financial Years Covered:** FY2021-22, FY2022-23, FY2023-24, FY2024-25
**Units in source files:** Amounts in Rs. (raw) — converted to Crores (Cr) below
**Prepared by:** AI analysis for app verification
**Date:** 2026-03-22

---

## Purpose

This document lists every line item extracted from SSSS's financial statements across 3 years (FY23–FY25, with FY22 comparative).

**Use case:** Compare this against what the app's openpyxl extractor produces to verify correctness. Each item shows the exact source text, sheet name, and amount.

---

## Source Files

| File | Relevant Sheets |
|------|----------------|
| `SSSS - Consolidated FY 22-23 Final.xlsx` | `Conso - BS`, `Conso-p&L`, `Conso-sch`, `Conso-sch P&L`, `Conso-sch Bs` |
| `Consolidated_FY2023-24 V7_Updated Ageing.xlsx` | `Cons_BS`, `Cons_PL`, `Cons_SCH` |
| `Final-Consolidated_FY2024-25 V7.xlsx` | `Cons_BS`, `Cons_PL`, `Cons_SCH` |
| `CMA 4S 26122025.xlsx` | `INPUT SHEET` (ground truth CMA) |

---

## SECTION 1 — PROFIT & LOSS (Income Side)

### 1A. Revenue from Operations

| Line Item | Source Text (exact) | FY22 (Cr) | FY23 (Cr) | FY24 (Cr) | FY25 (Cr) | Sheet |
|-----------|---------------------|-----------|-----------|-----------|-----------|-------|
| Revenue from operations (gross) | `Revenue from operations (gross)` | 398.11 | 445.20 | 422.73 | 400.54 | Conso-p&L / Cons_PL |
| Sale of products | `Sale of products` / `Sales Account` | — | — | 422.73 | 400.54 | Cons_PL |

**Sub-schedule (FY22-23 only — from Conso-sch P&L "Schedule of Sales"):**

| Line Item | Source Text (exact) | FY23 (Rs.) | Sheet |
|-----------|---------------------|------------|-------|
| H.O. Net GST Local Sales | `Net GST Local Sales` | ₹19,78,42,607 | Conso-sch P&L |
| H.O. Net GST Interstate Sales | `Net GST Interstate Sales` | ₹6,92,95,658 | Conso-sch P&L |
| H.O. Net GST SEZ Sales 0% | `Net GST -SEZ Sales - 0%` | ₹8,07,359 | Conso-sch P&L |
| Coimbatore GST Local Sales | `GST Local Sales` | ₹1,54,94,070 | Conso-sch P&L |
| Coimbatore GST Interstate Sales | `GST Interstate Sales` | ₹8,85,801 | Conso-sch P&L |
| Kerala Local Sales | `Sales (Local)` | ₹3,19,35,525 | Conso-sch P&L |
| Kerala Interstate Sales | `Sales (Interstate)` | ₹18,50,839 | Conso-sch P&L |
| Mumbai Interstate Sales (net returns) | `GST - Interstate Sales (Net of Sales Return)` | ₹1,41,17,933 | Conso-sch P&L |
| Mumbai Local Sales (net returns) | `GST - Local Sales (Net of Sales Return)` | ₹1,50,25,256 | Conso-sch P&L |
| Secunderabad GST Local (net returns) | `GST Local Sales (Net of Returns)` | ₹9,22,02,286 | Conso-sch P&L |
| Secunderabad GST Interstate (net returns) | `GST Interstate Sales (Net of Returns)` | ₹12,11,403 | Conso-sch P&L |
| Secunderabad SEZ | `SEZ` | ₹5,96,130 | Conso-sch P&L |
| Haryana GST Local | `GST Local Sales (Net of Returns)` | ₹3,31,85,639 | Conso-sch P&L |
| Haryana GST Interstate | `GST Interstate Sales (Net of Returns)` | ₹15,84,28,559 | Conso-sch P&L |

**Sales Expense Reimbursements (billed to customers — included in gross revenue):**

| Line Item | Source Text (exact) | FY23 (Rs.) | Sheet |
|-----------|---------------------|------------|-------|
| Cutting Charges (HO) | `Cutting Charges` | ₹1,36,189 | Conso-sch P&L |
| Material Delivery Charges (HO) | `Material Delivery Charges` | ₹84,617 | Conso-sch P&L |
| P&F/Handling Charges (HO) | `P&F /Handling Charges` | ₹37,29,936 | Conso-sch P&L |
| Handling Charges HO | `Handling Charges` | ₹1,32,644 | Conso-sch P&L |
| P&F and Delivery Charges HO | `P&F and Delivery Charges` | ₹65,38,771 | Conso-sch P&L |
| Pallet Charges HO | `Pallet Charges` | ₹1,500 | Conso-sch P&L |
| Loading & Transport Charges HO | `Loading & Transportation Charges` | ₹1,466 | Conso-sch P&L |
| Discount (deduction from revenue) | `Discount` | -₹73,568 | Conso-sch P&L |
| CBE P&F, Handling & Transport | `P&F, Handling and Transport charges` | ₹4,14,174 | Conso-sch P&L |
| Kerala P&F, Handling | `P&F, Handling and Transport charges` | ₹3,31,106 | Conso-sch P&L |
| Kerala Rate & Weight Difference | `Rate & Weight Difference` | -₹72,104 | Conso-sch P&L |
| Mumbai Loading & Forwarding | `Loading & Forwarding charges` | ₹1,14,989 | Conso-sch P&L |
| Mumbai Material Delivery | `Material Delivery Expenses` | ₹44,247 | Conso-sch P&L |
| Mumbai P&F Handling | `P & F Handling Charges` | ₹1,04,689 | Conso-sch P&L |
| Mumbai Rate/Wt/Qty Difference | `Rate, Weight & Quantity difference` | -₹1,69,559 | Conso-sch P&L |
| Mumbai Transport | `Transportation Charges` | ₹2,43,082 | Conso-sch P&L |
| Secunderabad Loading/Unloading/Cutting | `Loading / Unloading / Shifting / Cutting charges` | ₹10,91,227 | Conso-sch P&L |
| Secunderabad P&F Handling | `P & F Handling charges` | ₹30,19,255 | Conso-sch P&L |
| Secunderabad Rate Difference | `Rate Difference - Sales` | -₹2,78,536 | Conso-sch P&L |
| Haryana P&F Handling | `P & F Handling charges` | ₹2,82,795 | Conso-sch P&L |
| Haryana Rate Difference | `Rate Difference - Sales` | -₹1,14,076 | Conso-sch P&L |

**Job Work Charges (income from cutting/processing for customers):**

| Line Item | Source Text | FY23 (Rs.) | Sheet |
|-----------|-------------|------------|-------|
| HO Job Work - SIVAMUKIL ENGINEERING | `SIVAMUKIL ENGINEERING PRODUCTS` | ₹3,675 | Conso-sch P&L |
| HO Job Work - PARTHRAJ TECH | `PARTHRAJ TECH INDUSTRIES PRIVATE LIMITED` | ₹58,400 | Conso-sch P&L |
| Secunderabad Job Work (various) | Multiple company names | ₹1,63,863 | Conso-sch P&L |

---

### 1B. Other Income

| Line Item | Source Text (exact) | FY22 (Cr) | FY23 (Cr) | FY24 (Cr) | FY25 (Cr) | Sheet |
|-----------|---------------------|-----------|-----------|-----------|-----------|-------|
| Other Income (total) | `Other income` | 2.57 | 8.32 | 10.61 | 1.96 | Conso-p&L / Cons_PL |
| Other Income (consolidated note) | `(a). Other Income` | — | — | 10.61 | 1.96 | Cons_SCH Note 15 |

**FY22-23 Other Income Sub-schedule (from Conso-sch "Schedule-20"):**

| Line Item | Source Text (exact) | FY23 (Rs.) | FY22 (Rs.) | Sheet |
|-----------|---------------------|------------|------------|-------|
| Advance Forfeiture | `Advance Forfeiture` | ₹16,65,239 | — | Conso-sch |
| Bad Debts Recovered | `Bad Debts Recovered` | ₹19,01,394 | ₹15,15,000 | Conso-sch |
| Discount availed against expenses | `Discount availed against expenses` | ₹2,72,248 | — | Conso-sch |
| **Quantity Discount Received** | `Quantity Discount Received` | **₹3,20,44,294** | — | Conso-sch |
| **JSL/JSHL Discount (others)** | `JSL/JSHL Discount (others)` | **₹3,02,30,618** | — | Conso-sch |
| SAIL quantity discount | `SAIL-quantity discount` | ₹11,71,166 | — | Conso-sch |
| Refund against sales tax appeal | `Refund against sales tax appeal case` | ₹1,40,330 | — | Conso-sch |
| Incentive (perquisites) | `Incentive (perquisites)` | ₹19,19,026 | ₹3,33,630 | Conso-sch |
| Dividend on Shares & Unit | `Dividend on Shares & Unit` | ₹6,89,792 | ₹34,43,220 | Conso-sch |
| Gain of Foreign Currency Fluctuation | `Gain of Foreign Currency Fluctuation` | ₹9,71,065 | ₹81,09,646 | Conso-sch |
| **FDR Interest (HO)** | `Indian Bank FD Interest` / `HDFC FD Interest` etc. | ₹25,06,687 | — | Conso-sch P&L |
| **Interest Trading** | `Interest` (interest from trade parties) | ₹34,09,927 | — | Conso-sch P&L |
| Interest Received (Kerala FDR) | `a) FDR Interest` (Kerala) | ₹3,936 | — | Conso-sch P&L |
| Interest from Secunderabad | `Jindal Stainless Ltd` interest | ₹2,47,615 | — | Conso-sch P&L |
| Interest Haryana | `Jindal Stainless (Hisar) Ltd` interest | ₹58,372 | — | Conso-sch P&L |
| Interest Received (TOTAL) | `Interest Received` | ₹62,25,551 | ₹22,94,402 | Conso-sch |
| Profit on Sale of Shares | `Profit on Sale of Shares` | ₹44,78,070 | ₹98,00,330 | Conso-sch |
| Profit on Sale of Fixed Assets | `Profit on Sale of Fixed Assets` | ₹3,11,015 | ₹44,91,056 | Conso-sch |
| Rent Receipts | `Rent Receipts` | ₹10,44,333 | ₹12,78,000 | Conso-sch P&L |
| Round Off | `Round Off` | ₹931 | ₹2,723 | Conso-sch |
| Sundry Written off | `Sundry Written off` | ₹70,836 | ₹47,291 | Conso-sch |
| Cash Discount / Quality Discount | `Cash Discount /Quality Discount` | ₹94,321 | ₹91,36,696 | Conso-sch |
| Other Income | `Other Income` | ₹1,000 | ₹6,126 | Conso-sch |

---

## SECTION 2 — PROFIT & LOSS (Expense Side)

### 2A. Purchases / Raw Materials

| Line Item | Source Text (exact) | FY22 (Cr) | FY23 (Cr) | FY24 (Cr) | FY25 (Cr) | Sheet |
|-----------|---------------------|-----------|-----------|-----------|-----------|-------|
| Purchases of Stock-in-Trade (total) | `(b) Purchases of stock-in-trade` / `Purchases of Goods` | 373.99 | 431.55 | 373.81 | 365.06 | P&L |
| Purchases of Goods (note) | `(a). Goods Purchased` | — | — | 373.81 | 365.06 | Cons_SCH Note 16 |
| Changes in Inventories | `(c) Changes in inventories...` / `Changes in Stock in trade` | -17.05 | -13.99 | 24.78 | -0.89 | P&L |
| Changes in Stock in Trade (note) | `(a). Stock In Trade` | — | — | 24.78 | -0.89 | Cons_SCH Note 17 |

**FY22-23 Purchases Sub-schedule (Conso-sch P&L "Schedule of Purchases"):**

| Line Item | Source Text (exact) | FY23 (Rs.) | Sheet |
|-----------|---------------------|------------|-------|
| H.O. Net GST Local Purchases | `Net GST Local Purchases` | ₹9,38,93,481 | Conso-sch P&L |
| H.O. Net GST Interstate Purchases | `Net GST Interstate Purchases` | ₹19,43,15,940 | Conso-sch P&L |
| **H.O. Net GST Import Purchases** | `Net GST Import Purchases` | **₹79,65,280** | Conso-sch P&L |
| Coimbatore GST Local Purchases | `GST Local Purchases` | ₹9,04,291 | Conso-sch P&L |
| Coimbatore GST Interstate Purchases | `GST Interstate Purchases` | ₹53,88,256 | Conso-sch P&L |
| Kerala Local Purchases | `Local` | ₹27,04,237 | Conso-sch P&L |
| Kerala Interstate Purchases | `Interstate` | ₹12,36,89,339 | Conso-sch P&L |
| Mumbai GST Local Purchases | `GST Local Purchases` | ₹20,94,45,944 | Conso-sch P&L |
| Mumbai GST Interstate Purchases | `Gst - Interstate Purchase` | ₹34,22,325 | Conso-sch P&L |
| Secunderabad Interstate (net returns) | `GST Interstate Purchases (Net of Returns)` | ₹47,29,71,433 | Conso-sch P&L |
| Secunderabad Local (net returns) | `GST Local Purchases (Net of Returns)` | ₹33,90,43,507 | Conso-sch P&L |
| Haryana Interstate (net returns) | `GST Interstate Purchases (Net of Returns)` | ₹12,07,58,436 | Conso-sch P&L |
| Haryana Local (net returns) | `GST Local Purchases (Net of Returns)` | ₹15,67,56,246 | Conso-sch P&L |

**Purchase Adjustments (netted against purchases):**

| Line Item | Source Text (exact) | FY23 (Rs.) | Sheet |
|-----------|---------------------|------------|-------|
| Rate & Weight Difference (HO) | `Rate & Weight Diff.` | -₹62,99,138 | Conso-sch P&L |
| Quality Difference (HO) | `Quality Difference` | -₹1,41,310 | Conso-sch P&L |
| Other Expenses on Purchases (HO) | `Other Expenses on Purchases` | ₹59,16,333 | Conso-sch P&L |
| **Custom Duty on Import (HO)** | `Custom Duty on Import` | **₹24,74,150** | Conso-sch P&L |
| **Discount received (HO)** | `Discount received` | **-₹5,48,41,919** | Conso-sch P&L |
| Secunderabad P&F Expenditure | `P&F Expenditure` | ₹1,56,916 | Conso-sch P&L |
| Secunderabad Rate Difference | `Rate Difference` | -₹2,21,56,230 | Conso-sch P&L |
| Secunderabad Other Expenses | `Other Expenses on Purchase` | ₹4,00,322 | Conso-sch P&L |
| Haryana Other Expenses | `Other Expenses on Purchases` | ₹1,38,826 | Conso-sch P&L |
| Haryana Rate Difference (Credit Note) | `Rate Difference (Credit Note)` | -₹1,76,919 | Conso-sch P&L |
| **Haryana Discount On Purchase** | `Discount On Purchase` | **-₹68,99,780** | Conso-sch P&L |

---

### 2B. Employee Benefits Expenses

| Line Item | Source Text (exact) | FY22 (Cr) | FY23 (Cr) | FY24 (Cr) | FY25 (Cr) | Sheet |
|-----------|---------------------|-----------|-----------|-----------|-----------|-------|
| Employee benefits expense (total) | `(d) Employee benefits expense` / `Employee benefits Expenses` | 2.86 | 3.78 | 3.37 | 5.39 | P&L |
| Employee Benefit Expense (note) | `(a). Employee Benefit Expense` | — | — | 3.37 | 5.39 | Cons_SCH Note 18 |

**FY22-23 Employee Expenses Sub-schedule (Conso-sch "Schedule-23"):**

| Line Item | Source Text (exact) | FY23 (Rs.) | FY22 (Rs.) | Sheet |
|-----------|---------------------|------------|------------|-------|
| ESI, EPF & Admin Expenses | `ESI, EPF & Administration Expenses` | ₹9,16,367 | ₹7,84,142 | Conso-sch |
| Bonus | `Bonus A/c` | ₹13,69,580 | ₹14,21,955 | Conso-sch |
| Beverages to Staff | `Beverages to Staff` | ₹17,20,785 | ₹13,51,892 | Conso-sch |
| Conveyance | `Conveyance` | ₹3,36,287 | ₹34,60,450 | Conso-sch |
| Directors Remuneration | `Directors Remuneration` | ₹1,14,00,000 | ₹69,00,000 | Conso-sch |
| Gratuity | `Gratuity` | ₹51,490 | ₹57,690 | Conso-sch |
| Incentives | `Incentives` | ₹27,000 | — | Conso-sch |
| Professional Tax | `Professional Tax` | ₹46,416 | — | Conso-sch |
| Salaries & Wages | `Salaries & Wages` | ₹2,07,25,135 | ₹1,67,32,419 | Conso-sch |
| Salary Allowance | `Salary Allowance` | ₹9,79,508 | ₹8,82,219 | Conso-sch |
| Staff Welfare Expenses | `Staff Welfare Expenses` | ₹2,61,019 | ₹1,05,914 | Conso-sch |
| Man Power Agency Expenses | `Man Power Agency Expenses` | ₹2,44,428 | — | Conso-sch |

---

### 2C. Other Expenses / Direct and Indirect Expenses

**FY22-23 (from Conso-sch "Schedule-24"):**

**Direct Expenses:**

| Line Item | Source Text (exact) | FY23 (Rs.) | FY22 (Rs.) | Sheet |
|-----------|---------------------|------------|------------|-------|
| Clearing Expenses | `Clearing Expenses` | ₹14,94,054 | ₹1,89,550 | Conso-sch |
| **Customs Duty & Excise** | `Customs Duty & Excise` | ₹15,858 | ₹15,870 | Conso-sch |
| **Cutting Labour Charges** | `Cutting Labour Charges` | **₹1,11,13,588** | **₹1,02,59,133** | Conso-sch |
| **Freight Inward/Outward** | `Freight Inward/Outward` | **₹3,01,74,782** | **₹2,65,21,814** | Conso-sch |
| Material Testing Charges | `Material Testing Charges` | ₹49,760 | ₹26,980 | Conso-sch |
| **Tempo/Van/Bullock Cart/Rickshaw Charges** | `Tempo/Van/Bullock cart/Rickshaw Charges` | **₹30,05,380** | **₹70,95,522** | Conso-sch |
| **Polishing Charges** | `Polishing Charges` | ₹41,328 | ₹11,29,100 | Conso-sch |
| Job Work | `Job Work` | — | ₹1,70,548 | Conso-sch |
| Direct Expenses Sub-Total | — | ₹4,58,94,751 | ₹4,40,53,956 | Conso-sch |

**Indirect/Admin Expenses:**

| Line Item | Source Text (exact) | FY23 (Rs.) | FY22 (Rs.) | Sheet |
|-----------|---------------------|------------|------------|-------|
| Audit Fees (Tax & Statutory) | `Audit Fees (Tax & Statutory Audit Fee)` | ₹3,30,500 | ₹3,00,000 | Conso-sch |
| Advertisement | `Advertisement` | ₹12,04,616 | ₹21,31,030 | Conso-sch |
| Bad debts | `Bad debts` | ₹1,49,267 | ₹50,75,986 | Conso-sch |
| Bank charges | `Bank charges` | — | ₹25,370 | Conso-sch |
| Books, Magazines & Periodicals | `BOOKS MAGAZINE & PERIODICALS` | ₹24,200 | — | Conso-sch |
| Building Maintenance | `Building Maintenance` | ₹41,921 | — | Conso-sch |
| Broadband Expenses | `BroadBand Expenses` | ₹89,075 | ₹65,734 | Conso-sch |
| **Commission on sales & purchases** | `Commission on sales & purchases` | **₹31,53,605** | **₹29,95,558** | Conso-sch |
| Commission on Renting | `Commission on Renting` | ₹1,60,000 | — | Conso-sch |
| Computer Consumables & Repairs | `Computer Consumables & Repairs` | ₹78,863 | ₹89,413 | Conso-sch |
| **Cooly and Cartage** | `Cooly and Cartage` | **₹81,37,255** | **₹13,07,585** | Conso-sch |
| Corporate Social Expenses | `Corporate Social Expenses` | ₹4,500 | ₹6,04,000 | Conso-sch |
| Corporation Tax/Property Tax/Water Tax | `Corportation Tax/Property Tax/Water Tax` | ₹4,11,814 | ₹2,47,407 | Conso-sch |
| Conveyance | `Conveyance` | ₹7,33,600 | — | Conso-sch |
| Court Fees | `Court Fees` | ₹47,568 | — | Conso-sch |
| Credit Card Charges (HDFC) | `Credit card charges(Hdfc)` | ₹483 | — | Conso-sch |
| Delivery charges | `Delievery charges` | ₹17,246 | — | Conso-sch |
| Designing Charges | `Designing Charges` | ₹33,500 | — | Conso-sch |
| Donation | `Donation` | ₹11,24,280 | ₹3,46,564 | Conso-sch |
| Document Registration Charges | `Document Registration Charges` | ₹76,200 | ₹3,80,896 | Conso-sch |
| Discount & Rebates | `Discount & Rebates` | ₹7,779 | ₹21,971 | Conso-sch |
| Electricity Expenses | `Electricity Expenses` | ₹32,67,894 | ₹23,81,170 | Conso-sch |
| Factory licence | `Factory licence` | ₹10,560 | — | Conso-sch |
| Fees, Rates & Taxes | `Fees, Rates & Taxes` | ₹13,87,530 | ₹3,83,950 | Conso-sch |
| Fixed Assets Written off | `Fixed Assets Written off` | ₹6,086 | ₹11,51,548 | Conso-sch |
| Hotel Room Rent (local) | `Hotel Room rent expenses (local)` | ₹3,35,858 | — | Conso-sch |
| Hotel Room Rent (foreign) | `Hotel Room rent expenses (foreign)` | ₹83,985 | — | Conso-sch |
| Insurance | `Insurance` | ₹10,62,656 | ₹7,76,667 | Conso-sch |
| Office & General Expenses | `Office & General Expenses` | ₹10,03,794 | ₹6,93,251 | Conso-sch |
| Legal & Consultancy Fees | `Legal & Consultancy fees` | ₹16,18,238 | ₹16,89,607 | Conso-sch |
| Legal Reimbursement | `Legal Reimbursement` | ₹4,92,500 | — | Conso-sch |
| Legal related expenses | `Legal related expenses` | ₹33,430 | — | Conso-sch |
| Loading & Unloading Charges | `Loading & Unloading Charges` | ₹31,820 | ₹49,784 | Conso-sch |
| Miscellaneous expense | `Miscellaneous expense` | ₹21,310 | — | Conso-sch |
| Membership & Subscription | `Membership & Subscription` | ₹1,66,584 | ₹97,154 | Conso-sch |
| Packing Material & Forwarding charges | `Packing Material & Forwarding charges` | ₹15,68,851 | ₹33,24,783 | Conso-sch |
| Petrol Expenses | `Petrol Expenses` | ₹25,66,796 | ₹24,69,150 | Conso-sch |
| Pooja Expenses | `Pooja Expenses` | ₹76,934 | ₹36,405 | Conso-sch |
| Postage and Courier | `Postage and Courier` | ₹1,92,788 | ₹1,47,035 | Conso-sch |
| Printing & Stationary | `Printing & Stationary` | ₹6,46,531 | ₹4,12,465 | Conso-sch |
| **Professional Fees** | `Professional Fees` | **₹3,82,37,200** | **₹3,64,30,152** | Conso-sch |
| Discount allowed / Quantity Discount | `Discount allowed/Quantity Discount` | ₹1,20,099 | ₹65,963 | Conso-sch |
| Rent | `Rent` | ₹1,12,41,218 | ₹82,70,970 | Conso-sch |
| Repairs and Maintenance | `Repairs and Maintenance` | ₹41,23,101 | ₹35,13,918 | Conso-sch |
| ROC Filing Charges | `ROC Filing Charges` | ₹11,100 | ₹80,098 | Conso-sch |
| Sales Promotion Expenses | `Sales Promotion Expenses` | ₹34,69,400 | ₹24,69,070 | Conso-sch |
| Security Service | `Security Service` | ₹2,52,000 | ₹2,93,378 | Conso-sch |
| Share Expense | `Share Expense` | ₹2,57,609 | ₹4,56,632 | Conso-sch |
| Sundry balance written off | `Sundry balance written off` | ₹44,891 | -₹1,34,329 | Conso-sch |
| Tally Software Renewal | `Tally Software Renewal Expenses` | ₹3,600 | ₹7,200 | Conso-sch |
| Taxi, Tempo & Auto Charges | `Taxi, Tempo & Auto Charges` | ₹5,09,400 | ₹3,50,250 | Conso-sch |
| Telephone & Internet Charges | `Telephone & Internet Charges` | ₹5,31,148 | ₹5,70,605 | Conso-sch |
| Trade License - GHMC | `Trade License - GHMC` | ₹5,875 | ₹4,954 | Conso-sch |
| Travelling Expenses - Local | `Travelling Expenses - Local` | ₹33,43,689 | ₹26,92,491 | Conso-sch |
| Travelling Expenses - Foreign | `Travelling Expenses - Foreign` | ₹16,59,519 | — | Conso-sch |
| Vehicle Maintenance & Insurance | `Vehicle Maintenance & Insurance` | ₹50,627 | ₹23,46,313 | Conso-sch |
| **Warehousing Expenses** | `Warehousing Expenses` | **₹9,020** | — | Conso-sch |
| Website expenses | `Website expenses` | ₹1,39,547 | ₹90,800 | Conso-sch |
| **Weighing Machine Maintenance** | `Weighing Machine Maintenance` | ₹7,410 | — | Conso-sch |
| **Weighment Expenses** | `Weighment Expenses` | **₹1,82,860** | **₹1,65,089** | Conso-sch |
| Indirect Expenses Sub-Total | — | ₹9,46,34,847 | ₹8,53,41,220 | Conso-sch |
| Other Expenses Total | — | ₹14,05,29,598 | ₹12,93,95,176 | Conso-sch |

**FY24 (from Cons_SCH Note 20 — only 11 line items visible at this level):**

| Line Item | Source Text (exact) | FY24 (Rs.) | FY23 (Rs.) | Sheet |
|-----------|---------------------|------------|------------|-------|
| Auditor's Remuneration | `(a) Auditor's Remuneration` | ₹2,00,000 | ₹2,00,000 | Cons_SCH |
| Advertisement and Sales Promotion | `(b) Advertisement and Sales Promotion Expenses` | ₹33,73,992 | ₹46,74,016 | Cons_SCH |
| Conveyance, Communication, Travelling | `(c) Conveyance, Communication and Travelling Expenses` | ₹5,37,74,306 | ₹5,84,85,465 | Cons_SCH |
| Fees and Subscription | `(d) Fees and Subscription` | ₹3,38,097 | ₹4,53,319 | Cons_SCH |
| Insurance Charges | `(e) Insurance Charges` | ₹11,02,640 | ₹22,35,264 | Cons_SCH |
| **Legal & Professional Fees** | `(f) Legal & Proffessional Fees` | **₹2,28,85,535** | **₹4,05,85,206** | Cons_SCH |
| Office and General Expenses | `(g) Office and General Expenses` | ₹27,62,915 | ₹28,84,175 | Cons_SCH |
| Other Expenses | `(h) Other Expenses` | ₹1,84,72,179 | ₹1,26,91,694 | Cons_SCH |
| **Power And Fuel** | `(i) Power And Fuel` | **₹60,93,815** | **₹58,33,970** | Cons_SCH |
| **Rent, Rates and Taxes** | `(j) Rent, Rates and Taxes` | **₹1,22,66,815** | **₹1,49,99,651** | Cons_SCH |
| **Repairs and Maintenance** | `(k) Repairs and Maintenance` | **₹48,13,180** | **₹42,43,885** | Cons_SCH |
| Other Expenses Total | — | ₹12,60,83,473 | ₹14,72,86,440 | Cons_SCH |

**FY25 (from Cons_SCH Note 20):**

| Line Item | Source Text (exact) | FY25 (Rs.) | FY24 (Rs.) | Sheet |
|-----------|---------------------|------------|------------|-------|
| Auditor's Remuneration | `(a) Auditor's Remuneration` | ₹1,50,000 | ₹2,00,000 | Cons_SCH |
| Advertisement and Sales Promotion | `(b) Advertisement and Sales Promotion Expenses` | ₹35,99,359 | ₹33,73,992 | Cons_SCH |
| Conveyance, Communication, Travelling | `(c) Conveyance, Communication and Travelling Expenses` | ₹1,40,51,133 | ₹5,37,74,306 | Cons_SCH |
| Fees and Subscription | `(d) Fees and Subscription` | ₹2,31,864 | ₹3,38,097 | Cons_SCH |
| Insurance Charges | `(e) Insurance Charges` | ₹12,04,080 | ₹11,02,640 | Cons_SCH |
| **Legal & Professional Fees** | `(f) Legal & Proffessional Fees` | **₹3,37,36,280** | **₹2,28,85,535** | Cons_SCH |
| Office and General Expenses | `(g) Office and General Expenses` | ₹14,27,901 | ₹27,62,915 | Cons_SCH |
| **Other Expenses (large)** | `(h) Other Expenses` | **₹6,78,68,067** | **₹1,84,72,179** | Cons_SCH |
| **Power And Fuel** | `(i) Power And Fuel` | **₹58,94,743** | **₹60,93,815** | Cons_SCH |
| **Rent, Rates and Taxes** | `(j) Rent, Rates and Taxes` | **₹1,42,87,582** | **₹1,22,66,815** | Cons_SCH |
| **Repairs and Maintenance** | `(k) Repairs and Maintenance` | **₹52,35,441** | **₹48,13,180** | Cons_SCH |
| Other Expenses Total | — | ₹14,76,86,451 | ₹12,60,83,473 | Cons_SCH |

---

### 2D. Finance Costs

| Line Item | Source Text (exact) | FY22 (Cr) | FY23 (Cr) | FY24 (Cr) | FY25 (Cr) | Sheet |
|-----------|---------------------|-----------|-----------|-----------|-----------|-------|
| Finance Cost (total) | `(f) Finance Cost` / `Finance costs` | 10.92 | 11.50 | 11.13 | 9.56 | P&L |
| Finance Costs (note) | `(a). Finance Costs` | — | — | 11.13 | 9.56 | Cons_SCH Note 19 |

**FY22-23 Finance Cost Sub-schedule (Conso-sch "Schedule-25"):**

| Line Item | Source Text (exact) | FY23 (Rs.) | FY22 (Rs.) | Sheet |
|-----------|---------------------|------------|------------|-------|
| **Bank Charges, Processing Fees** | `Bank Charges,Processing Fees` | **₹26,72,100** | **₹17,73,944** | Conso-sch |
| **Interest on Bank OD** | `Interest on Bank O.D` | **₹4,71,44,526** | **₹2,85,51,638** | Conso-sch |
| **Interest Paid on Trading** | `Interest Paid on Trading` | **₹15,37,446** | **₹15,87,665** | Conso-sch |
| **Interest Paid on Secured Loan** | `Interest Paid On Secured Loan` | **₹1,42,24,010** | **₹1,88,38,808** | Conso-sch |
| **Interest Paid on Unsecured Loan** | `Interest Paid On Unsecured Loan` | **₹4,94,38,053** | **₹5,98,50,582** | Conso-sch |
| Interest on delay payment | `Interest on delay payment` | — | ₹39,467 | Conso-sch |

---

### 2E. Depreciation

| Line Item | Source Text | FY22 (Cr) | FY23 (Cr) | FY24 (Cr) | FY25 (Cr) | Sheet |
|-----------|-------------|-----------|-----------|-----------|-----------|-------|
| Depreciation and Amortization | `(g) Depreciation and Amortization Exp` | 0.93 | 0.88 | 0.97 | 0.96 | P&L |

---

### 2F. Tax Expense

| Line Item | Source Text | FY22 (Cr) | FY23 (Cr) | FY24 (Cr) | FY25 (Cr) | Sheet |
|-----------|-------------|-----------|-----------|-----------|-----------|-------|
| Current tax expense | `(a) Current tax expense` | 3.76 | 1.94 | 1.83 | 1.93 | P&L |
| Current tax – prior years | `(c) Current tax expense relating to prior years` | — | 0.50 | — | 0.06 | P&L |
| Deferred tax | `(e) Deferred tax` | -0.02 | -0.06 | -0.02 | -0.02 | P&L |
| Profit after tax | `Profit / (Loss) for the year` | 12.63 | 3.88 | 4.86 | 5.66 | P&L |

---

## SECTION 3 — BALANCE SHEET (Liabilities Side)

### 3A. Shareholders' Funds

| Line Item | Source Text (exact) | FY22 (Cr) | FY23 (Cr) | FY24 (Cr) | FY25 (Cr) | Sheet |
|-----------|---------------------|-----------|-----------|-----------|-----------|-------|
| Share Capital | `(a) Share Capital` | 2.40 | 2.40 | 2.40 | 2.40 | BS |
| Reserves & Surplus | `(b) Reserves and Surplus` | 60.89 | 64.77 | 69.62 | 75.29 | BS |
| Share Premium A/c | `Share Premium` / `A. Share Premium A/c` | 19.75 | 19.75 | 19.75 | 19.75 | Conso-sch / Cons_SCH |
| P&L Brought Forward | `Profit & Loss Account (Brought Forward)` / `Opening balance` | 28.50 | 41.13 | 45.02 | 49.87 | Conso-sch / Cons_SCH |
| P&L Current Year | `Profit & Loss Account (Current Year)` / `(+) Net Profit/(Net Loss)` | 12.63 | 3.88 | 4.86 | 5.66 | Conso-sch / Cons_SCH |
| SHRI GANESH MAHARAJ | `SHRI GANESH MAHARAJ` | — | — | 0.000000125 | 0.000000125 | Cons_SCH |

---

### 3B. Long-Term Borrowings (Non-Current Liabilities)

| Line Item | Source Text (exact) | FY22 (Cr) | FY23 (Cr) | FY24 (Cr) | FY25 (Cr) | Sheet |
|-----------|---------------------|-----------|-----------|-----------|-----------|-------|
| Long-Term Borrowings (total) | `(a) Long-Term Borrowings` | 52.26 | 69.61 | 43.84 | 47.06 | BS |
| **Unsecured Loan – Four Star Estates LLP** | `Unsecured Loans` / `Unsecured - Four Star Estates LLP` | 36.50 | 57.71 | 38.21 | 35.68 | Conso-sch / Cons_SCH |
| Axis Bank Term Loan | `Axis Bank Term Loan A/C No...` / `Axis Bank Term Loan` | 1.09 | 1.09 | 0.37 | — | Conso-sch Bs / Cons_SCH |
| Kotak Mahindra Prime Car Loan | `Kotak Mahindra Prime -Car Loan` / `Kotak Bank A/c - Car Loan` | — | 0.10 | 0.45 | 0.28 | Conso-sch Bs / Cons_SCH |
| WCDL/HDFC Bank Term Loan | `WCDL HDFC Term Loan` / `HDFC Bank Term Loan` | 4.21 | 4.21 | 2.77 | 8.75 | Conso-sch Bs / Cons_SCH |
| WCDL HSBC Bank Term Loan | `WCDL HSBC Term Loan` / `HSBC Bank Term Loan` | 3.05 | 3.05 | 2.03 | 1.02 | Conso-sch Bs / Cons_SCH |
| WCDL Kotak Term Loan | `WCDL Kotak Term Loan` / `Kotak Bank Term Loan` | 3.39 | 3.39 | — | 1.32 | Conso-sch Bs / Cons_SCH |
| Secured Loans (total) | `Secured Loans` | 15.76 | 11.90 | 5.63 | 11.37 | Conso-sch |

---

### 3C. Short-Term Borrowings (Current Liabilities)

| Line Item | Source Text (exact) | FY22 (Cr) | FY23 (Cr) | FY24 (Cr) | FY25 (Cr) | Sheet |
|-----------|---------------------|-----------|-----------|-----------|-----------|-------|
| Short-Term Borrowings (total) | `(a) Short-Term Borrowings` | 58.16 | 61.57 | 58.73 | 39.81 | BS |
| **HSBC Ltd OD A/c** | `Hsbc Ltd A/C` / `HSBC OD A/C` | 21.82 | 26.62 | 42.09 | 26.75 | Conso-sch / Cons_SCH |
| **HDFC Bank OD A/c** | `HDCF Bank Od A/C` / `HDFC OD A/C` | 24.22 | 21.29 | 16.65 | 13.05 | Conso-sch / Cons_SCH |
| Kotak Mahindra OD | `Kotak Mahindra Bank Ltd O/D` / `KOTAK OD A/C` | 9.36 | 8.78 | — | — | Conso-sch / Cons_SCH |
| Mumbai HDFC Bank OD | `HDFC Bank OD` (Mumbai) | 0.12 | 0.48 | — | — | Conso-sch |
| Kerala HDFC Bank OD | `HDFC BANK OD` (Kerala) | — | 0.36 | — | — | Conso-sch |
| Coimbatore HDFC Bank OD | `HDFC BANK OD` (CBE) | — | 0.45 | — | — | Conso-sch |
| Haryana HDFC Bank OD | `HDFC BANK OD` (Haryana) | — | 0.47 | — | — | Conso-sch |
| Secunderabad HDFC Bank OD | `HDFC Bank Od A/c` (Secunderabad) | 2.76 | 3.13 | — | — | Conso-sch |

---

### 3D. Trade Payables

| Line Item | Source Text (exact) | FY22 (Cr) | FY23 (Cr) | FY24 (Cr) | FY25 (Cr) | Sheet |
|-----------|---------------------|-----------|-----------|-----------|-----------|-------|
| Trade Payables (total) | `(b) Trade Payables` | 14.34 | 20.25 | 2.60 | 6.65 | BS |
| **Sundry Creditors for purchases** | `(a) Sundry Creditors for purchases` | — | — | 1.92 | 4.09 | Cons_SCH |
| **Sundry Creditors for expenses** | `(B) Sundry Creditors for expenses` | — | — | 0.69 | 2.56 | Cons_SCH |

---

### 3E. Other Current Liabilities

| Line Item | Source Text (exact) | FY22 (Cr) | FY23 (Cr) | FY24 (Cr) | FY25 (Cr) | Sheet |
|-----------|---------------------|-----------|-----------|-----------|-----------|-------|
| Other Current Liabilities (total) | `(c) Other Current Liabilities` | 2.82 | 2.51 | 0.03 | 0.04 | BS |
| Advances from Customers | `Advances from Customers` | 2.76 | 2.01 | — | — | Conso-sch |
| HDFC Credit Card | `HDFC Credit Card` | 0.05 | 0.05 | — | — | Conso-sch |
| Statutory Liabilities (combined) | `Statutory Liabilities` | 0.04 | 0.47 | — | — | Conso-sch |
| Outstanding Expenses | `Outstanding Expenses` | 0.01 | 0.02 | — | — | Conso-sch |
| Other Current Liabilities (FY24/25) | `(a) Other Current Liabilities` | — | — | 0.03 | 0.04 | Cons_SCH |

---

### 3F. Short-Term Provisions

| Line Item | Source Text (exact) | FY22 (Cr) | FY23 (Cr) | FY24 (Cr) | FY25 (Cr) | Sheet |
|-----------|---------------------|-----------|-----------|-----------|-----------|-------|
| Short-Term Provisions (total) | `(d) Short-Term Provisions` | 4.64 | 2.20 | 4.62 | 5.08 | BS |
| **Provision for Income Tax** | `(a) Statutory Dues` / `Provision for Income Tax` | 3.76 | 1.44 | 4.48 / 1.83 | 2.98 | Conso-sch / Cons_SCH |
| Provision for Gratuity | `Provision for Gratuity` | 0.60 | 0.59 | — | — | Conso-sch |
| Other Provision | `Other Provision` | 0.29 | 0.17 | 0.14 | 2.10 | Conso-sch / Cons_SCH |
| Statutory Dues (FY24/25) | `(a) Statutory Dues` | — | — | 4.48 | 2.98 | Cons_SCH |
| Other Provisions (FY24/25) | `(b) Other Provisions` | — | — | 0.14 | 2.10 | Cons_SCH |

---

## SECTION 4 — BALANCE SHEET (Assets Side)

### 4A. Fixed Assets

| Line Item | Source Text (exact) | FY22 (Cr) | FY23 (Cr) | FY24 (Cr) | FY25 (Cr) | Sheet |
|-----------|---------------------|-----------|-----------|-----------|-----------|-------|
| Tangible Assets (Net Block) | `(i) Tangible Assets` / `Property, Plant And Equipments` | 10.19 | 9.70 | 9.92 | 9.52 | BS |
| Capital Work in Progress | `(iii) Capital work-in-progress` | — | — | — | — | BS |

---

### 4B. Non-Current Investments

| Line Item | Source Text (exact) | FY22 (Cr) | FY23 (Cr) | FY24 (Cr) | FY25 (Cr) | Sheet |
|-----------|---------------------|-----------|-----------|-----------|-----------|-------|
| Non-Current Investments (total) | `(b) Non-Current Investments` | 6.16 | 5.39 | 6.56 | 7.40 | BS |
| **Investment in Equity Instruments / Share Investments** | `Investment in Equity Instruments` / `Share Investments` | 6.16 | 5.39 | 6.56 | 7.40 | Conso-sch / Cons_SCH |

---

### 4C. Deferred Tax

| Line Item | Source Text (exact) | FY22 (Cr) | FY23 (Cr) | FY24 (Cr) | FY25 (Cr) | Sheet |
|-----------|---------------------|-----------|-----------|-----------|-----------|-------|
| Deferred Tax Assets (Net) | `(c) Deferred Tax Assets (Net)` | — | 0.06 | 0.08 | 0.10 | BS |
| Deferred Tax Liabilities (Net) | `(b) Deferred Tax Liabilities (Net)` | 0.006 | — | — | — | BS |

---

### 4D. Long-Term Loans and Advances

| Line Item | Source Text (exact) | FY22 (Cr) | FY23 (Cr) | FY24 (Cr) | FY25 (Cr) | Sheet |
|-----------|---------------------|-----------|-----------|-----------|-----------|-------|
| Long-Term Loans & Advances | `(d) Long-Term Loans and Advances` | 0.51 | 0.60 | — | — | BS |
| Long-Term Deposits/Advances (detail) | `Others-Unsecured,Considered Good` | 0.51 | 0.60 | — | — | Conso-sch |

**FY22-23 Long-Term Deposits Sub-schedule:**

| Line Item | Source Text (exact) | FY23 (Rs.) | Sheet |
|-----------|---------------------|------------|-------|
| Bharti Telenet Deposit | `Bharti Telenet Ltd - Deposit` | ₹2,000 | Conso-sch Bs |
| Deposit – Legal | `Deposit - Legal` | ₹50,000 | Conso-sch Bs |
| **Electricity Board Deposit** | `Electricity Board-Deposit` | **₹55,070** | Conso-sch Bs |
| Jindal Stainless Auction Deposit | `Jindal Stainless Ltd-Auction Deposit` | ₹5,00,000 | Conso-sch Bs |
| Sales Tax Deposit | `Sales Tax Deposit` | ₹2,000 | Conso-sch Bs |
| Other Advances (LT) | `Other Advances` | ₹7,00,000 | Conso-sch Bs |
| Custom Deposit | `Custom Deposit` | ₹5,75,633 | Conso-sch Bs |
| **EMD (Earnest Money Deposit)** | `EMD` | **₹20,44,249** | Conso-sch Bs |
| **Telephone Deposit** | `Telephone Deposit` | **₹26,318** | Conso-sch Bs |
| Mumbai Advance Tax | `Advance Tax` | ₹3,25,000 | Conso-sch Bs |
| Office Rent Deposit (Secunderabad) | `Office Rent (Deposit) R.S.Jaiswal` | ₹6,900 | Conso-sch Bs |
| Rental Advance (Godown) | `Rental Advance R.P.R.Jaiswal` | ₹5,00,000 | Conso-sch Bs |
| Rental Advance Jeedimetla Godown | `Rental Advance (Jeedimetla Godown)` | ₹6,00,000 | Conso-sch Bs |
| Rental Advance Pipe Godown | `Rental Advance Pipe Godown (DLP)` | ₹3,90,000 | Conso-sch Bs |

---

### 4E. Current Investments (FDs)

| Line Item | Source Text (exact) | FY22 (Cr) | FY23 (Cr) | FY24 (Cr) | FY25 (Cr) | Sheet |
|-----------|---------------------|-----------|-----------|-----------|-----------|-------|
| Current Investments / Fixed Deposits | `(a) Current Investments` / `Fixed Deposits` | 3.45 | 5.32 | — | — | BS / Conso-sch |
| Cash & Cash Equiv - Fixed Deposits | `(c) Fixed Deposits with Bank` | — | — | 5.25 | 5.21 | Cons_SCH |

**FY22-23 FD Detail (Conso-sch Bs "Details of FD"):**

| Line Item | Source Text (exact) | FY23 (Rs.) | Sheet |
|-----------|---------------------|------------|-------|
| HDFC FD 50300363161059 | `HDFC FD NO-50300363161059 (6.6%)` | ₹1,19,83,398 | Conso-sch Bs |
| HDFC FD (multiple LIEN MARKED) | Various HDFC FD numbers | Various | Conso-sch Bs |
| Kotak FD 4513852811 | `KOTAK FD 4513852811 (5%)` | ₹1,25,820 | Conso-sch Bs |
| SBI FD GST Case | `SBI-FD A/C-00000038740093627 (6.5%) GST CASE` | ₹14,19,602 | Conso-sch Bs |
| FD Total | — | ₹5,31,61,533 | Conso-sch Bs |

---

### 4F. Inventories

| Line Item | Source Text (exact) | FY22 (Cr) | FY23 (Cr) | FY24 (Cr) | FY25 (Cr) | Sheet |
|-----------|---------------------|-----------|-----------|-----------|-----------|-------|
| Inventories (total) | `(b) Inventories` | 87.54 | 101.53 | 76.75 | 77.64 | BS |
| **Finished Goods / Stock In Trade** | `Finished Goods.` / `(a) Stock In Trade` | 87.54 | 101.53 | 76.75 | 77.64 | Conso-sch / Cons_SCH |

---

### 4G. Trade Receivables

| Line Item | Source Text (exact) | FY22 (Cr) | FY23 (Cr) | FY24 (Cr) | FY25 (Cr) | Sheet |
|-----------|---------------------|-----------|-----------|-----------|-----------|-------|
| Trade Receivables (total) | `(c) Trade Receivables` | 76.27 | 85.68 | 73.57 | 68.54 | BS |
| Outstanding > 6 months | `(a) Outstanding for Period Above Six Month...` | — | — | 8.99 | 11.59 | Cons_SCH |
| Others (< 6 months) | `(b) Others Unsecured, considered good` | — | — | 64.58 | 56.96 | Cons_SCH |

---

### 4H. Cash and Cash Equivalents

| Line Item | Source Text (exact) | FY22 (Cr) | FY23 (Cr) | FY24 (Cr) | FY25 (Cr) | Sheet |
|-----------|---------------------|-----------|-----------|-----------|-----------|-------|
| Cash & Bank Balances (total) | `(d) Cash and Cash Equivalents` | 0.65 | 0.52 | 6.48 | 5.35 | BS |
| Cash in Hand (INR) | `Cash In Indian Rupees` | — | 0.23 | — | — | Conso-sch Bs |
| Cash in Hand (foreign currencies) | `Cash In China - Yuan` / Thai Baht / Vietnamese Dong | — | 0.027 | — | — | Conso-sch Bs |
| Cash in Hand (total) | `(a) Cash in Hand` / `(a) Cash Balances` | 0.32 | 0.39 | 0.50 | 0.45 | Conso-sch / Cons_SCH |
| **Bank Balances (Current accounts)** | `(i) In Current accounts` / `(b) Bank Balances` | 0.33 | 0.13 | 0.73 | -0.31 | Conso-sch / Cons_SCH |
| Fixed Deposits (all) | `(c) Fixed Deposits with Bank` | — | — | 5.25 | 5.21 | Cons_SCH |

**FY22-23 Bank Balance Detail (Conso-sch Bs "Details Of Bank Balances"):**

| Line Item | Source Text (exact) | FY23 (Rs.) | Sheet |
|-----------|---------------------|------------|-------|
| Axis Bank A/C 913020018937481 | `Axis Bank A/C.913020018937481` | ₹1,13,736 | Conso-sch Bs |
| Indian Bank 422163193 | `Indian Bank- 422163193` | ₹6,83,078 | Conso-sch Bs |
| HDFC Bank A/C 00042320006196 | `Hdfc Bank -A/C.00042320006196` | ₹1,43,576 | Conso-sch Bs |
| Kotak Mahindra CA 4512852041 | `Kotak Mahindra Bank - C/A No-4512852041` | ₹1,13,395 | Conso-sch Bs |
| Central Bank CA 3839802331 | `Central Bank of India C/A No.3839802331` | ₹9,528 | Conso-sch Bs |
| HDFC Card | `HDFC Card` | ₹4,51,085 | Conso-sch Bs |
| HSBC Bank | `HSBC Bank` | -₹1,60,704 | Conso-sch Bs |
| Axis Card | `Axis Card` | -₹43,636 | Conso-sch Bs |

---

### 4I. Short-Term Loans and Advances

| Line Item | Source Text (exact) | FY22 (Cr) | FY23 (Cr) | FY24 (Cr) | FY25 (Cr) | Sheet |
|-----------|---------------------|-----------|-----------|-----------|-----------|-------|
| Short-Term Loans and Advances (total) | `(e) Short-Term Loans and Advances` | 10.66 | 11.50 | 7.15 | 7.02 | BS |
| **Balance With Government Authorities** | `Balance With Government Authorities` | 8.88 | 7.69 | — | — | Conso-sch |
| **Balances with Statutory Authorities** | `(a) Balances with Statutory Authorities` | — | — | 6.53 | 6.48 | Cons_SCH |
| Advances-Unsecured | `Advances-Unsecured Considered Good` | 1.78 | 3.82 | — | — | Conso-sch |
| Others (ST) | `(b) Others` | — | — | 0.62 | 0.54 | Cons_SCH |

**FY22-23 Balance With Government Authorities (Conso-sch Bs "Schedule 10"):**

| Line Item | Source Text (exact) | FY23 (Rs.) | Sheet |
|-----------|---------------------|------------|-------|
| **GST Credit Ledger** | `Gst Credit Ledger` | ₹1,27,66,181 | Conso-sch Bs |
| Unclaimed ITC | `Unclaimed ITC` | ₹11,484 | Conso-sch Bs |
| GST TCS | `GST TCS` | ₹1,446 | Conso-sch Bs |
| TDS Receivable | `TDS Receivable` | ₹18,00,123 | Conso-sch Bs |
| TCS Receivable | `TCS Receivable` | ₹33,064 | Conso-sch Bs |
| TDS Excess paid | `TDS Excess paid` | ₹19,40,111 | Conso-sch Bs |
| **Advance Tax** | `Advance Tax` | **₹57,00,000** | Conso-sch Bs |
| Income Tax Refund Receivable FY20 | `Income Tax Refund Receivable - FY 2019-20` | ₹13,29,164 | Conso-sch Bs |
| Income Tax Refund FY18/19 | `Income Tax Refund Receivable - FY 2017-18/18-19` | ₹3,75,829 | Conso-sch Bs |
| Income Tax Paid on Regular Assessment | `Income Tax Paid on Regular Assessment` | ₹2,12,87,955 | Conso-sch Bs |
| Cash with IT Department | `Cash with Income tax Department` | ₹13,83,724 | Conso-sch Bs |
| CBE Advance Tax | `Advance Tax paid` | ₹18,00,000 | Conso-sch Bs |
| Kerala Advance Tax | `Advance Tax paid` | ₹7,50,000 | Conso-sch Bs |
| Govt Auth Total | — | ₹7,68,60,349 | Conso-sch Bs |

---

### 4J. Other Current Assets

| Line Item | Source Text (exact) | FY22 (Cr) | FY23 (Cr) | FY24 (Cr) | FY25 (Cr) | Sheet |
|-----------|---------------------|-----------|-----------|-----------|-----------|-------|
| Other Current Assets (total) | `(f) Other Current Assets` | 0.08 | 2.97 | 1.35 | 0.76 | BS |
| Other (consolidated) | `(a) Other` | — | — | 1.35 | 0.76 | Cons_SCH |

**FY22-23 Other Current Assets (Conso-sch "Schedule-17"):**

| Line Item | Source Text (exact) | FY23 (Rs.) | FY22 (Rs.) | Sheet |
|-----------|---------------------|------------|------------|-------|
| Prepaid Expenses (Insurance) | `Prepaid Expenses (Insurance)` | ₹4,23,704 | ₹3,42,917 | Conso-sch |
| Prepaid Membership | `Prepaid Membership` | ₹46,671 | ₹93,009 | Conso-sch |
| Prepaid Rent | `Prepaid Rent` | ₹1,80,000 | ₹1,80,000 | Conso-sch |
| Interest Receivable (FDR) | `Interest Receivable (FDR)` | ₹3,24,933 | — | Conso-sch |
| Dividend on Shares Receivable | `Dividend on shares Receivable` | ₹6,750 | ₹4,500 | Conso-sch |
| **JSL/JSHL Discount Receivable** | `JSL/JSHL Discount Receivable` | **₹2,87,52,999** | — | Conso-sch |
| Other Current Assets Total | — | ₹2,97,35,057 | ₹7,64,651 | Conso-sch |

---

## SECTION 5 — FINANCIAL SUMMARY (CMA Ground Truth mapping)

The following is from `CMA 4S 26122025.xlsx` INPUT SHEET — the CA's final mapping. **These are the "correct answer" values in Crores.**

| CMA Field | Row | FY22 | FY23 | FY24 | FY25 |
|-----------|-----|------|------|------|------|
| Domestic Sales | 22 | 398.11 | 445.20 | 422.73 | 400.54 |
| Export Sales | 23 | 0 | 0 | 0 | 0 |
| Interest Received | 30 | 0.23 | 0.62 | 1.20 | 0.70 |
| Profit on sale of FA/Investments | 31 | 1.02 | 0.48 | 0.85 | 0.03 |
| Gain on Exchange Fluctuations | 32 | 0.08 | 0.10 | 0.06 | 0.10 |
| Others (Non-Operating Income) | 34 | 0.32 | 0.78 | 0.21 | 1.12 |
| Raw Materials Consumed (Imported) | 41 | 3.58 | 0 | 3.51 | 6.03 |
| Raw Materials Consumed (Indigenous) | 42 | 369.49 | 425.20 | 362.02 | 359.03 |
| Wages | 45 | 0.15 | 0 | 0 | 0 |
| Processing / Job Work Charges | 46 | 1.37 | 1.27 | 0 | 0 |
| Freight and Transportation Charges | 47 | 3.36 | 3.32 | 0 | 0 |
| Power, Coal, Fuel and Water | 48 | 0.24 | 0.33 | 0.61 | 0.59 |
| Others (Manufacturing) | 49 | 0.10 | 0.16 | 0 | 0 |
| Depreciation (CMA) | 63 | 0.93 | 0.88 | 0.97 | 0.96 |
| Other Manufacturing Exp (CMA) | 64 | 5.22 | 5.07 | 0.61 | 0.59 |
| Salary and staff expenses | 67 | 2.17 | 2.64 | 3.37 | 4.31 |
| Rent, Rates and Taxes | 68 | 0.89 | 1.31 | 1.23 | 1.43 |
| Bad Debts | 69 | 0.51 | 0.01 | 0 | 0 |
| Advertisements and Sales Promotions | 70 | 0.86 | 0.48 | 0.34 | 0.36 |
| Others (Admin) | 71 | 4.85 | 7.13 | 9.93 | 11.81 |
| Repairs & Maintenance (Admin) | 72 | 0.38 | 0.02 | 0.48 | 0.52 |
| Audit Fees & Directors Remuneration | 73 | 0.73 | 1.17 | 0.02 | 1.14 |
| Interest on Fixed Loans / Term Loans | 83 | 7.87 | 6.37 | 4.70 | 2.39 |
| Interest on Working Capital Loans | 84 | 2.87 | 4.87 | 6.26 | 6.96 |
| Bank Charges | 85 | 0.18 | 0.27 | 0.17 | 0.21 |
| Income Tax Provision | 99 | 3.46 | 1.87 | 1.81 | 1.97 |
| Deferred Tax Asset (P&L) | 101 | 0.02 | 0.06 | 0.02 | 0 |
| **BS Fields** | | | | | |
| Issued, Subscribed and Paid up | 116 | 2.40 | 2.40 | 2.40 | 2.40 |
| Balance transferred from P&L | 122 | 41.13 | 45.01 | 49.86 | 55.52 |
| Share Premium A/c | 123 | 19.75 | 19.75 | 19.75 | 19.75 |
| Working Capital Bank Finance - Bank 1 | 131 | 58.16 | 61.57 | 58.73 | 48.93 |
| Term Loan Balance Repayable after 1 year | 137 | 15.76 | 11.90 | 5.63 | 2.62 |
| Unsecured Loans – Quasi Equity | 152 | 6.00 | 6.00 | 6.00 | 6.00 |
| Unsecured Loans – Long Term Debt | 153 | 30.50 | 51.71 | 32.21 | 29.68 |
| Gross Block | 162 | 14.70 | 14.79 | 16.68 | 17.07 |
| Less Accumulated Depreciation | 163 | 4.52 | 5.09 | 6.76 | 7.55 |
| Deferred Tax Asset (BS) | 171 | 0 | 0.06 | 0.08 | 0.10 |
| Other non current investments | 186 | 6.16 | 5.39 | 6.56 | 7.40 |
| Finished Goods | 201 | 87.54 | 101.53 | 76.75 | 77.64 |
| Domestic Receivables | 206 | 68.04 | 74.70 | 64.58 | 56.96 |
| Debtors more than 6 months | 208 | 8.23 | 11.05 | 8.99 | 11.59 |
| Cash on Hand | 212 | 0.32 | 0.39 | 0.50 | 0.45 |
| Bank Balances | 213 | 0.33 | 0.13 | 0.73 | 0.06 |
| Other Fixed Deposits | 215 | 3.45 | 5.32 | 5.25 | 5.21 |
| Advance Income Tax | 221 | 0 | 7.69 | 0 | 0 |
| Other Advances / current asset | 223 | 0.01 | 6.73 | 8.50 | 7.78 |
| Sundry Creditors for goods | 242 | 14.34 | 20.25 | 1.92 | 4.09 |
| Advance received from customers | 243 | 2.76 | 2.01 | 0 | 0 |
| Provision for Taxation | 244 | 3.76 | 1.44 | 1.83 | 0 |
| Other statutory liabilities | 246 | 0.05 | 0.47 | 2.65 | 2.98 |
| Creditors for Expenses | 249 | 0 | 0 | 0.69 | 2.56 |
| Other current liabilities | 250 | 0.90 | 0.79 | 0.17 | 2.14 |

---

## SECTION 6 — Items Verified vs CMA Ground Truth

| Source Item | Amount FY23 | CA Mapped To | CMA Row | Notes |
|-------------|-------------|--------------|---------|-------|
| Quantity Discount Received | ₹3,20,44,294 | **NETTED vs Purchases** | Row 42 | NOT shown as Other Income |
| JSL/JSHL Discount (others) | ₹3,02,30,618 | **NETTED vs Purchases** | Row 42 | NOT shown as Other Income |
| SAIL quantity discount | ₹11,71,166 | NETTED vs Purchases | Row 42 | NOT shown as Other Income |
| Discount received (purchase schedule) | ₹5,48,41,919 | NETTED vs Purchases | Row 42 | Negative in purchases |
| JSL/JSHL Discount Receivable (BS) | ₹2,87,52,999 | Other Advances / current asset | Row 223 | Balance sheet asset |
| Cutting Labour Charges | ₹1,11,13,588 | Processing / Job Work | Row 46 | Steel-specific |
| Freight Inward/Outward | ₹3,01,74,782 | Freight & Transportation | Row 47 | As expected |
| Interest on Bank OD | ₹4,71,44,526 | Interest on WC Loans | Row 84 | OD = working capital |
| Interest Paid on Secured Loan | ₹1,42,24,010 | Interest on Fixed Loans | Row 83 | Term loans |
| Interest Paid on Unsecured Loan | ₹4,94,38,053 | Interest on Fixed Loans | Row 83 | Four Star LLP loan |
| Interest Paid on Trading | ₹15,37,446 | Interest on WC Loans | Row 84 | Trade credit interest |
| Bank Charges, Processing Fees | ₹26,72,100 | Bank Charges | Row 85 | As expected |
| Four Star Estates LLP loan (partial) | ₹6,00,00,000 (fixed) | Quasi Equity | Row 152 | Manually decided by CA |
| Four Star Estates LLP loan (balance) | ₹51,71 Cr | Long Term Debt | Row 153 | |
| HDFC/HSBC/Kotak OD accounts | ₹61.57 Cr | WC Bank Finance Bank 1 | Row 131 | All OD combined |
| Secured Term Loans | ₹11.90 Cr | Term Loan Balance after 1 yr | Row 137 | |
| Advance Tax + IT Refund + IT Paid | ₹7,69 Cr | Advance Income Tax | Row 221 | ALL gov tax balances combined |
| GST Credit Ledger, TDS Receivable | Included above | Advance Income Tax | Row 221 | Merged into one row |
| Polishing Charges | ₹41,328 | Processing / Job Work | Row 46 | Insignificant but assigned |
| Cooly and Cartage | ₹81,37,255 | Others (Admin) | Row 71 | Large item — worth verifying |
| Professional Fees | ₹3,82,37,200 | Others (Admin) | Row 71 | Very large for Admin row |
| Commission on sales & purchases | ₹31,53,605 | Others (Admin) | Row 71 | Not a separate CMA row |
| Directors Remuneration | ₹1,14,00,000 | Audit Fees & Dir Rem | Row 73 | Confirmed |
| Rent | ₹1,12,41,218 | Rent, Rates and Taxes | Row 68 | Confirmed |
