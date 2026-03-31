import json

cma_fields = {
    22: 'Domestic Sales', 23: 'Export Sales', 30: 'Interest Received',
    31: 'Profit on Sale of Fixed Assets / Investments', 32: 'Gain on Exchange Fluctuations',
    34: 'Others (Non-Operating Income)', 41: 'Raw Materials Consumed (Imported)',
    42: 'Raw Materials Consumed (Indigenous)', 44: 'Stores and Spares Consumed (Indigenous)',
    45: 'Wages', 46: 'Processing / Job Work Charges', 47: 'Freight and Transportation Charges',
    48: 'Power, Coal, Fuel and Water', 49: 'Others (Manufacturing)',
    58: 'Opening Inventory (Finished Goods)', 59: 'Closing Inventory (Finished Goods)',
    63: 'Depreciation', 67: 'Salary and Staff Expenses', 68: 'Rent, Rates and Taxes',
    69: 'Bad Debts', 70: 'Advertisements and Sales Promotions', 71: 'Others (Admin)',
    72: 'Repairs and Maintenance', 73: 'Audit Fees and Directors Remuneration',
    83: 'Interest on Fixed Loans / Term Loans', 84: 'Interest on Working Capital Loans',
    85: 'Bank Charges', 90: 'Sundry Balance Written Off', 99: 'Income Tax Provision',
    101: 'Deferred Tax Asset (P&L)', 116: 'Issued Subscribed and Paid up',
    122: 'Balance transferred from P&L', 123: 'Share Premium',
    131: 'Working Capital Bank Finance - Bank 1', 137: 'Term Loan Balance Repayable after 1 year',
    152: 'Unsecured Loans - Quasi Equity', 153: 'Unsecured Loans - Long Term Debt',
    162: 'Gross Block', 163: 'Less Accumulated Depreciation', 164: 'Net Block',
    171: 'Deferred Tax Assets (BS)', 186: 'Other Non-Current Investments',
    198: 'Stores and Spares Indigenous (Inventory)', 201: 'Finished Goods',
    206: 'Domestic Receivables', 208: 'Debtors More Than 6 Months',
    212: 'Cash on Hand', 213: 'Bank Balances', 214: 'Fixed Deposits Under Lien',
    215: 'Other Fixed Deposits', 221: 'Advance Income Tax',
    223: 'Other Advances / Current Asset', 235: 'Dues from Directors / Partners / Promoters',
    237: 'Security Deposits with Government Departments', 238: 'Other Non-Current Assets',
    242: 'Sundry Creditors for Goods', 243: 'Advance from Customers',
    244: 'Provision for Taxation', 246: 'Other Statutory Liabilities',
    249: 'Creditors for Expenses', 250: 'Other Current Liabilities'
}

def mk(raw, amt, fy, sec, sheet, row, conf, reason):
    return {
        'raw_text': raw,
        'amount_rupees': amt,
        'financial_year': fy,
        'section': sec,
        'sheet_name': sheet,
        'correct_cma_field': cma_fields.get(row, f'Row {row}'),
        'correct_cma_row': row,
        'confidence_note': conf,
        'reasoning': reason
    }

# ============================================================
# SSSS GROUND TRUTH
# ============================================================
ssss = []

# FY23 Revenue sub-schedule (all Row 22)
rev23 = [
    ('Net GST Local Sales', 197842607, 'HO local GST sales'),
    ('Net GST Interstate Sales', 69295658, 'HO interstate sales'),
    ('Net GST -SEZ Sales - 0%', 807359, 'HO SEZ zero-rated sales; domestic revenue'),
    ('GST Local Sales', 15494070, 'Coimbatore branch local sales'),
    ('GST Interstate Sales', 885801, 'Coimbatore interstate sales'),
    ('Sales (Local)', 31935525, 'Kerala branch local sales'),
    ('Sales (Interstate)', 1850839, 'Kerala branch interstate sales'),
    ('GST - Interstate Sales (Net of Sales Return)', 14117933, 'Mumbai interstate net of returns'),
    ('GST - Local Sales (Net of Sales Return)', 15025256, 'Mumbai local net of returns'),
    ('GST Local Sales (Net of Returns)', 92202286, 'Secunderabad local net of returns'),
    ('GST Interstate Sales (Net of Returns)', 1211403, 'Secunderabad interstate net of returns'),
    ('SEZ', 596130, 'Secunderabad SEZ sales'),
    ('GST Local Sales (Net of Returns)', 33185639, 'Haryana local sales'),
    ('GST Interstate Sales (Net of Returns)', 158428559, 'Haryana interstate sales'),
]
for r, a, n in rev23:
    ssss.append(mk(r, a, 2023, 'schedule of sales', 'Conso-sch P&L', 22, 'high', f'{n} -> Domestic Sales Row 22'))

# SSSS-010: handling charges in sales schedule -> Row 22
handling23 = [
    ('Cutting Charges', 136189, 'SSSS-010: Cutting charges BILLED TO CUSTOMER in revenue schedule -> Row 22. Contrast: cutting PAID TO WORKER in expense schedule -> Row 46.'),
    ('Material Delivery Charges', 84617, 'SSSS-010: Delivery billed to customer -> Row 22'),
    ('P&F /Handling Charges', 3729936, 'SSSS-010: HO packing/forwarding/handling charged to customers -> Row 22'),
    ('Handling Charges', 132644, 'SSSS-010: Handling charged to customers -> Row 22'),
    ('P&F and Delivery Charges', 6538771, 'SSSS-010: P&F+delivery billed to customers -> Row 22'),
    ('Pallet Charges', 1500, 'SSSS-010: Pallet charges billed to customer -> Row 22'),
    ('Loading & Transportation Charges', 1466, 'SSSS-010: Loading/transport in sales schedule = customer charge -> Row 22'),
    ('Discount', -73568, 'SSSS-010: Discount deducted from invoice reduces Row 22'),
    ('P&F, Handling and Transport charges', 414174, 'SSSS-010: CBE branch P&F/handling to customers -> Row 22'),
    ('P&F, Handling and Transport charges', 331106, 'SSSS-010: Kerala P&F/handling to customers -> Row 22'),
    ('Rate & Weight Difference', -72104, 'SSSS-010: Kerala rate/weight credit note in sales schedule -> reduces Row 22'),
    ('Loading & Forwarding charges', 114989, 'SSSS-010: Mumbai loading/forwarding to customers -> Row 22'),
    ('Material Delivery Expenses', 44247, 'SSSS-010: Mumbai delivery to customers -> Row 22'),
    ('P & F Handling Charges', 104689, 'SSSS-010: Mumbai P&F to customers -> Row 22'),
    ('Rate, Weight & Quantity difference', -169559, 'SSSS-010: Mumbai rate/wt/qty credit note -> reduces Row 22'),
    ('Transportation Charges', 243082, 'SSSS-010: Mumbai transport to customers -> Row 22'),
    ('Loading / Unloading / Shifting / Cutting charges', 1091227, 'SSSS-010: Secunderabad L/U/cutting billed to customers -> Row 22'),
    ('P & F Handling charges', 3019255, 'SSSS-010: Secunderabad P&F to customers -> Row 22'),
    ('Rate Difference - Sales', -278536, 'SSSS-010: Secunderabad sales credit note -> reduces Row 22'),
    ('P & F Handling charges', 282795, 'SSSS-010: Haryana P&F to customers -> Row 22'),
    ('Rate Difference - Sales', -114076, 'SSSS-010: Haryana sales credit note -> reduces Row 22'),
]
for r, a, n in handling23:
    ssss.append(mk(r, a, 2023, 'schedule of sales', 'Conso-sch P&L', 22, 'verified', n))

# Job work income FY23 -> Row 22
for r, a, n in [
    ('SIVAMUKIL ENGINEERING PRODUCTS', 3675, 'HO job work income (cutting for customer) -> Row 22'),
    ('PARTHRAJ TECH INDUSTRIES PRIVATE LIMITED', 58400, 'HO job work income -> Row 22'),
    ('Secunderabad Job Work (various customers)', 163863, 'Secunderabad job work income -> Row 22'),
]:
    ssss.append(mk(r, a, 2023, 'schedule of sales', 'Conso-sch P&L', 22, 'high', n))

# FY22/24/25 aggregate revenue
ssss.append(mk('Revenue from operations (gross)', 3981100000, 2022, 'profit and loss', 'Conso-p&L', 22, 'high', 'FY22 total domestic steel sales -> Row 22'))
ssss.append(mk('Sale of products', 4227300000, 2024, 'profit and loss', 'Cons_PL', 22, 'high', 'FY24 product sales (422.73 Cr) -> Row 22'))
ssss.append(mk('Sale of products', 4005400000, 2025, 'profit and loss', 'Cons_PL', 22, 'high', 'FY25 product sales (400.54 Cr) -> Row 22'))

# FY23 Other Income (Schedule-20)
oi23 = [
    ('Advance Forfeiture', 1665239, 34, 'high', 'Non-operating windfall income -> Row 34'),
    ('Bad Debts Recovered', 1901394, 34, 'high', 'Recovery of written-off trade debts -> Row 34'),
    ('Discount availed against expenses', 272248, 34, 'high', 'Discount on expenses paid -> Row 34'),
    ('Quantity Discount Received', 32044294, 42, 'verified', 'SSSS-001: JSL/JSHL volume rebate appears in Other Income schedule but is a PURCHASE PRICE ADJUSTMENT -> Row 42 (negative). Without this rule AI routes to Row 34.'),
    ('JSL/JSHL Discount (others)', 30230618, 42, 'verified', 'SSSS-001: Jindal Stainless vendor rebate -> nets against Row 42'),
    ('SAIL-quantity discount', 1171166, 42, 'verified', 'SSSS-001: SAIL supplier rebate -> Row 42'),
    ('Refund against sales tax appeal case', 140330, 34, 'high', 'One-time sales tax refund -> Row 34'),
    ('Incentive (perquisites)', 1919026, 34, 'high', 'Supplier perquisite incentives (not volume discounts) -> Row 34'),
    ('Dividend on Shares & Unit', 689792, 30, 'high', 'Investment dividends -> Row 30 Interest Received'),
    ('Gain of Foreign Currency Fluctuation', 971065, 32, 'verified', 'Forex gain -> Row 32'),
    ('FDR Interest (HO)', 2506687, 30, 'verified', 'Fixed deposit interest -> Row 30'),
    ('Interest', 3409927, 30, 'high', 'Interest from trade parties -> Row 30'),
    ('FDR Interest (Kerala)', 3936, 30, 'high', 'Kerala FD interest -> Row 30'),
    ('Interest received from Jindal Stainless Ltd', 247615, 30, 'high', 'Secunderabad JSL interest -> Row 30'),
    ('Interest received from Jindal Stainless (Hisar) Ltd', 58372, 30, 'high', 'Haryana JSHL interest -> Row 30'),
    ('Profit on Sale of Shares', 4478070, 31, 'verified', 'Capital gain on equity sale -> Row 31'),
    ('Profit on Sale of Fixed Assets', 311015, 31, 'high', 'FA disposal gain -> Row 31'),
    ('Rent Receipts', 1044333, 34, 'high', 'Rental income from leased property -> Row 34'),
    ('Sundry Written off', 70836, 34, 'high', 'Written-off payables recognized as income -> Row 34'),
    ('Cash Discount /Quality Discount', 94321, 42, 'verified', 'SSSS-001: Cash/quality discount from supplier -> Row 42 (purchase price adjustment)'),
    ('Other Income', 1000, 34, 'high', 'Residual other income -> Row 34'),
]
for r, a, row, conf, n in oi23:
    ssss.append(mk(r, a, 2023, 'schedule-20 other income', 'Conso-sch', row, conf, n))

# FY22 other income comparatives
oi22 = [
    ('Bad Debts Recovered', 1515000, 34, 'high', 'FY22: debt recovery -> Row 34'),
    ('Incentive (perquisites)', 333630, 34, 'high', 'FY22: supplier incentives -> Row 34'),
    ('Dividend on Shares & Unit', 3443220, 30, 'high', 'FY22: dividends -> Row 30'),
    ('Gain of Foreign Currency Fluctuation', 8109646, 32, 'verified', 'FY22: forex gain -> Row 32'),
    ('Interest Received', 2294402, 30, 'high', 'FY22: total interest received -> Row 30'),
    ('Profit on Sale of Shares', 9800330, 31, 'high', 'FY22: share sale gain -> Row 31'),
    ('Profit on Sale of Fixed Assets', 4491056, 31, 'high', 'FY22: FA gain -> Row 31'),
    ('Rent Receipts', 1278000, 34, 'high', 'FY22: rental income -> Row 34'),
    ('Cash Discount /Quality Discount', 9136696, 42, 'verified', 'SSSS-001: FY22 large supplier quality discount (0.91 Cr) -> Row 42. Size confirms it is a purchase rebate not Row 34.'),
    ('Sundry Written off', 47291, 34, 'high', 'FY22: written-off payables income -> Row 34'),
    ('Round Off', 2723, 34, 'high', 'FY22: rounding -> Row 34'),
    ('Other Income', 6126, 34, 'high', 'FY22: residual -> Row 34'),
]
for r, a, row, conf, n in oi22:
    ssss.append(mk(r, a, 2022, 'schedule-20 other income', 'Conso-sch', row, conf, n))

# FY23 Purchases sub-schedule
purch23 = [
    ('Net GST Local Purchases', 93893481, 42, 'high', 'HO local purchases -> Row 42'),
    ('Net GST Interstate Purchases', 194315940, 42, 'high', 'HO interstate purchases -> Row 42'),
    ('Net GST Import Purchases', 7965280, 41, 'verified', 'Import purchases -> Row 41 Raw Materials Imported'),
    ('GST Local Purchases', 904291, 42, 'high', 'Coimbatore local purchases -> Row 42'),
    ('GST Interstate Purchases', 5388256, 42, 'high', 'Coimbatore interstate purchases -> Row 42'),
    ('Local', 2704237, 42, 'high', 'Kerala local purchases -> Row 42'),
    ('Interstate', 123689339, 42, 'high', 'Kerala interstate purchases -> Row 42'),
    ('GST Local Purchases', 209445944, 42, 'high', 'Mumbai local purchases -> Row 42'),
    ('Gst - Interstate Purchase', 3422325, 42, 'high', 'Mumbai interstate purchases -> Row 42'),
    ('GST Interstate Purchases (Net of Returns)', 472971433, 42, 'high', 'Secunderabad interstate net of returns -> Row 42'),
    ('GST Local Purchases (Net of Returns)', 339043507, 42, 'high', 'Secunderabad local net of returns -> Row 42'),
    ('GST Interstate Purchases (Net of Returns)', 120758436, 42, 'high', 'Haryana interstate -> Row 42'),
    ('GST Local Purchases (Net of Returns)', 156756246, 42, 'high', 'Haryana local -> Row 42'),
    ('Rate & Weight Diff.', -6299138, 42, 'high', 'HO rate/weight credit note -> reduces Row 42'),
    ('Quality Difference', -141310, 42, 'high', 'Quality adjustment -> reduces Row 42'),
    ('Other Expenses on Purchases', 5916333, 42, 'high', 'Other purchase incidentals -> Row 42'),
    ('Custom Duty on Import', 2474150, 41, 'verified', 'SSSS-014: Import customs duty = part of landed cost -> Row 41'),
    ('Discount received', -54841919, 42, 'verified', 'SSSS-001: Large supplier discount in purchase schedule -> Row 42 (negative)'),
    ('P&F Expenditure', 156916, 42, 'high', 'Secunderabad packing costs on purchases -> Row 42'),
    ('Rate Difference', -22156230, 42, 'high', 'Secunderabad purchase credit note -> reduces Row 42'),
    ('Other Expenses on Purchase', 400322, 42, 'high', 'Secunderabad other purchase costs -> Row 42'),
    ('Other Expenses on Purchases', 138826, 42, 'high', 'Haryana other purchase costs -> Row 42'),
    ('Rate Difference (Credit Note)', -176919, 42, 'high', 'Haryana rate difference credit note -> reduces Row 42'),
    ('Discount On Purchase', -6899780, 42, 'verified', 'SSSS-001: Haryana purchase discount from supplier -> Row 42 (negative)'),
]
for r, a, row, conf, n in purch23:
    ssss.append(mk(r, a, 2023, 'schedule of purchases', 'Conso-sch P&L', row, conf, n))

ssss.append(mk('Purchases of Goods', 3739900000, 2022, 'profit and loss', 'Conso-p&L', 42, 'high', 'FY22 total purchases -> Row 42'))
ssss.append(mk('Purchases of Goods', 3738100000, 2024, 'note 16 purchases', 'Cons_SCH', 42, 'high', 'FY24 goods purchased (373.81 Cr) -> Row 42'))
ssss.append(mk('Purchases of Goods', 3650600000, 2025, 'note 16 purchases', 'Cons_SCH', 42, 'high', 'FY25 goods purchased (365.06 Cr) -> Row 42'))

# Employee expenses FY23
emp23 = [
    ('ESI, EPF & Administration Expenses', 916367, 67, 'high', 'ESI/EPF -> Salary and Staff Expenses Row 67'),
    ('Bonus A/c', 1369580, 67, 'high', 'Employee bonus -> Row 67'),
    ('Beverages to Staff', 1720785, 67, 'high', 'Staff beverages = staff welfare -> Row 67'),
    ('Conveyance', 336287, 67, 'high', 'Employee conveyance allowance -> Row 67'),
    ('Directors Remuneration', 11400000, 73, 'verified', 'Directors salary -> Row 73 Audit Fees & Directors Remuneration'),
    ('Gratuity', 51490, 67, 'high', 'Gratuity provision -> Row 67'),
    ('Incentives', 27000, 67, 'high', 'Employee incentive payments -> Row 67'),
    ('Professional Tax', 46416, 67, 'high', 'Professional tax on salary -> Row 67'),
    ('Salaries & Wages', 20725135, 67, 'high', 'Regular salaries and wages -> Row 67'),
    ('Salary Allowance', 979508, 67, 'high', 'Salary allowances -> Row 67'),
    ('Staff Welfare Expenses', 261019, 67, 'high', 'Staff welfare -> Row 67'),
    ('Man Power Agency Expenses', 244428, 67, 'high', 'Contract manpower agency charges -> Row 67'),
]
for r, a, row, conf, n in emp23:
    ssss.append(mk(r, a, 2023, 'schedule-23 employee benefits', 'Conso-sch', row, conf, n))

# Employee FY22
emp22 = [
    ('ESI, EPF & Administration Expenses', 784142, 67, 'high', 'FY22: ESI/EPF -> Row 67'),
    ('Bonus A/c', 1421955, 67, 'high', 'FY22: bonus -> Row 67'),
    ('Beverages to Staff', 1351892, 67, 'high', 'FY22: beverages -> Row 67'),
    ('Conveyance', 3460450, 67, 'high', 'FY22: conveyance -> Row 67'),
    ('Directors Remuneration', 6900000, 73, 'verified', 'FY22: directors remuneration -> Row 73'),
    ('Gratuity', 57690, 67, 'high', 'FY22: gratuity -> Row 67'),
    ('Salaries & Wages', 16732419, 67, 'high', 'FY22: salaries -> Row 67'),
    ('Salary Allowance', 882219, 67, 'high', 'FY22: salary allowances -> Row 67'),
    ('Staff Welfare Expenses', 105914, 67, 'high', 'FY22: staff welfare -> Row 67'),
]
for r, a, row, conf, n in emp22:
    ssss.append(mk(r, a, 2022, 'schedule-23 employee benefits', 'Conso-sch', row, conf, n))

# Direct expenses FY23
dir23 = [
    ('Clearing Expenses', 1494054, 41, 'verified', 'SSSS-014: CHA/clearing charges on imports = part of imported goods landed cost -> Row 41'),
    ('Customs Duty & Excise', 15858, 41, 'verified', 'SSSS-014: Customs duty on imported steel -> Row 41'),
    ('Cutting Labour Charges', 11113588, 46, 'verified', 'SSSS-003: Payments to cutting workers (steel slitting) = direct processing -> Row 46. NOT wages (Row 45).'),
    ('Freight Inward/Outward', 30174782, 47, 'verified', 'Freight for goods movement -> Row 47 Freight and Transportation'),
    ('Material Testing Charges', 49760, 49, 'verified', 'SSSS-004: Lab quality testing for customer certificates -> Others Manufacturing Row 49'),
    ('Tempo/Van/Bullock cart/Rickshaw Charges', 3005380, 47, 'verified', 'SSSS-006: Small vehicle goods movement -> Row 47. NOT staff travel.'),
    ('Polishing Charges', 41328, 46, 'verified', 'SSSS-003: Polishing service on steel products -> Processing/Job Work Row 46'),
]
for r, a, row, conf, n in dir23:
    ssss.append(mk(r, a, 2023, 'schedule-24 direct expenses', 'Conso-sch', row, conf, n))

# Direct expenses FY22
dir22 = [
    ('Clearing Expenses', 189550, 41, 'verified', 'SSSS-014: FY22 import clearing -> Row 41'),
    ('Customs Duty & Excise', 15870, 41, 'verified', 'SSSS-014: FY22 customs duty -> Row 41'),
    ('Cutting Labour Charges', 10259133, 46, 'verified', 'SSSS-003: FY22 cutting labour -> Row 46'),
    ('Freight Inward/Outward', 26521814, 47, 'verified', 'FY22: freight -> Row 47'),
    ('Material Testing Charges', 26980, 49, 'verified', 'SSSS-004: FY22 material testing -> Row 49'),
    ('Tempo/Van/Bullock cart/Rickshaw Charges', 7095522, 47, 'verified', 'SSSS-006: FY22 vehicle goods movement -> Row 47'),
    ('Polishing Charges', 1129100, 46, 'verified', 'SSSS-003: FY22 polishing -> Row 46'),
    ('Job Work', 170548, 46, 'high', 'FY22: job work paid to external processors -> Row 46'),
]
for r, a, row, conf, n in dir22:
    ssss.append(mk(r, a, 2022, 'schedule-24 direct expenses', 'Conso-sch', row, conf, n))

# Indirect expenses FY23
ind23 = [
    ('Audit Fees (Tax & Statutory Audit Fee)', 330500, 73, 'verified', 'Audit fees -> Row 73'),
    ('Advertisement', 1204616, 70, 'high', 'Advertisement -> Row 70'),
    ('Bad debts', 149267, 69, 'high', 'Bad debt write-off -> Row 69'),
    ('Broadband Expenses', 89075, 71, 'high', 'Internet/broadband -> Row 71'),
    ('Commission on sales & purchases', 3153605, 71, 'verified', 'Sales/purchase commissions -> Row 71 (no dedicated CMA row for commission)'),
    ('Commission on Renting', 160000, 71, 'high', 'Rental commission -> Row 71'),
    ('Computer Consumables & Repairs', 78863, 71, 'high', 'Computer maintenance -> Row 71'),
    ('Cooly and Cartage', 8137255, 71, 'verified', 'CMA ground truth (Section 6) maps Cooly & Cartage -> Row 71. CA treated as admin, not freight. Rule SSSS-005 aspirational only.'),
    ('Corporate Social Expenses', 4500, 71, 'high', 'CSR expenses -> Row 71'),
    ('Corportation Tax/Property Tax/Water Tax', 411814, 68, 'high', 'Property/water tax -> Rent Rates Taxes Row 68'),
    ('Electricity Expenses', 3267894, 48, 'high', 'Electricity -> Row 48 Power Coal Fuel'),
    ('Fees, Rates & Taxes', 1387530, 68, 'high', 'Fees and taxes -> Row 68'),
    ('Insurance', 1062656, 71, 'high', 'Insurance premiums -> Row 71'),
    ('Legal & Consultancy fees', 1618238, 71, 'high', 'Legal/consulting -> Row 71'),
    ('Membership & Subscription', 166584, 71, 'high', 'Memberships -> Row 71'),
    ('Office & General Expenses', 1003794, 71, 'high', 'Office/general -> Row 71'),
    ('Packing Material & Forwarding charges', 1568851, 71, 'high', 'Packing materials used internally (not billed to customer) -> Row 71'),
    ('Petrol Expenses', 2566796, 71, 'high', 'Vehicle petrol -> Row 71'),
    ('Printing & Stationary', 646531, 71, 'high', 'Printing/stationery -> Row 71'),
    ('Professional Fees', 38237200, 71, 'verified', 'Very large professional fees (3.82 Cr) -> Row 71. Verified in CMA ground truth Section 6.'),
    ('Rent', 11241218, 68, 'verified', 'Office/godown rent -> Row 68. Verified in CMA ground truth Section 6.'),
    ('Repairs and Maintenance', 4123101, 72, 'high', 'Repairs -> Row 72'),
    ('Sales Promotion Expenses', 3469400, 70, 'high', 'Sales promotions -> Row 70'),
    ('Telephone & Internet Charges', 531148, 71, 'high', 'Phone/internet -> Row 71'),
    ('Travelling Expenses - Local', 3343689, 71, 'high', 'Local travel -> Row 71'),
    ('Travelling Expenses - Foreign', 1659519, 71, 'high', 'Foreign travel -> Row 71'),
    ('Vehicle Maintenance & Insurance', 50627, 71, 'high', 'Vehicle maintenance -> Row 71'),
    ('Weighment Expenses', 182860, 49, 'verified', 'SSSS-007: Weighbridge charges = direct cost of steel-by-weight trading -> Others Manufacturing Row 49'),
    ('Discount & Rebates', 7779, 71, 'high', 'Discounts given to customers -> Row 71'),
    ('Loading & Unloading Charges', 31820, 71, 'high', 'Small loading/unloading -> Row 71'),
    ('Donation', 1124280, 71, 'high', 'Donations -> Row 71'),
    ('Security Service', 252000, 71, 'high', 'Security guards -> Row 71'),
]
for r, a, row, conf, n in ind23:
    ssss.append(mk(r, a, 2023, 'schedule-24 indirect expenses', 'Conso-sch', row, conf, n))

# Indirect expenses FY22 key items
ind22 = [
    ('Advertisement', 2131030, 70, 'high', 'FY22: advertisement -> Row 70'),
    ('Bad debts', 5075986, 69, 'high', 'FY22: bad debts -> Row 69'),
    ('Cooly and Cartage', 1307585, 71, 'verified', 'FY22: Cooly & Cartage -> Row 71 (consistent with FY23 CA treatment)'),
    ('Electricity Expenses', 2381170, 48, 'high', 'FY22: electricity -> Row 48'),
    ('Professional Fees', 36430152, 71, 'verified', 'FY22: professional fees (3.64 Cr) -> Row 71'),
    ('Rent', 8270970, 68, 'verified', 'FY22: rent -> Row 68'),
    ('Repairs and Maintenance', 3513918, 72, 'high', 'FY22: repairs -> Row 72'),
    ('Sales Promotion Expenses', 2469070, 70, 'high', 'FY22: sales promotion -> Row 70'),
    ('Weighment Expenses', 165089, 49, 'verified', 'SSSS-007: FY22 weighment -> Row 49'),
    ('Petrol Expenses', 2469150, 71, 'high', 'FY22: petrol -> Row 71'),
    ('Travelling Expenses - Local', 2692491, 71, 'high', 'FY22: local travel -> Row 71'),
    ('Vehicle Maintenance & Insurance', 2346313, 71, 'high', 'FY22: vehicle maintenance -> Row 71'),
    ('Insurance', 776667, 71, 'high', 'FY22: insurance -> Row 71'),
]
for r, a, row, conf, n in ind22:
    ssss.append(mk(r, a, 2022, 'schedule-24 indirect expenses', 'Conso-sch', row, conf, n))

# FY24/25 Note 20 expenses
note20 = [
    ("Auditor's Remuneration", 200000, 2024, 73, 'high', 'FY24: auditor fees -> Row 73'),
    ('Advertisement and Sales Promotion Expenses', 3373992, 2024, 70, 'high', 'FY24: ads+sales promotion -> Row 70'),
    ('Conveyance, Communication and Travelling Expenses', 53774306, 2024, 71, 'inferred', 'FY24: combined travel/comms/conveyance -> Row 71'),
    ('Fees and Subscription', 338097, 2024, 71, 'inferred', 'FY24: fees and subscriptions -> Row 71'),
    ('Insurance Charges', 1102640, 2024, 71, 'high', 'FY24: insurance -> Row 71'),
    ('Legal & Proffessional Fees', 22885535, 2024, 71, 'verified', 'FY24: legal/professional (2.29 Cr) -> Row 71'),
    ('Office and General Expenses', 2762915, 2024, 71, 'high', 'FY24: office and general -> Row 71'),
    ('Other Expenses', 18472179, 2024, 71, 'inferred', 'FY24: catch-all other expenses -> Row 71'),
    ('Power And Fuel', 6093815, 2024, 48, 'high', 'FY24: power and fuel -> Row 48'),
    ('Rent, Rates and Taxes', 12266815, 2024, 68, 'verified', 'FY24: rent/rates/taxes -> Row 68'),
    ('Repairs and Maintenance', 4813180, 2024, 72, 'high', 'FY24: repairs -> Row 72'),
    ("Auditor's Remuneration", 150000, 2025, 73, 'high', 'FY25: auditor fees -> Row 73'),
    ('Advertisement and Sales Promotion Expenses', 3599359, 2025, 70, 'high', 'FY25: ads -> Row 70'),
    ('Conveyance, Communication and Travelling Expenses', 14051133, 2025, 71, 'inferred', 'FY25: combined travel/comms -> Row 71'),
    ('Fees and Subscription', 231864, 2025, 71, 'inferred', 'FY25: fees/subscriptions -> Row 71'),
    ('Insurance Charges', 1204080, 2025, 71, 'high', 'FY25: insurance -> Row 71'),
    ('Legal & Proffessional Fees', 33736280, 2025, 71, 'verified', 'FY25: legal/professional (3.37 Cr) -> Row 71'),
    ('Office and General Expenses', 1427901, 2025, 71, 'high', 'FY25: office and general -> Row 71'),
    ('Other Expenses', 67868067, 2025, 71, 'inferred', 'FY25: large catch-all other expenses (6.79 Cr) -> Row 71'),
    ('Power And Fuel', 5894743, 2025, 48, 'high', 'FY25: power/fuel -> Row 48'),
    ('Rent, Rates and Taxes', 14287582, 2025, 68, 'verified', 'FY25: rent/rates/taxes -> Row 68'),
    ('Repairs and Maintenance', 5235441, 2025, 72, 'high', 'FY25: repairs -> Row 72'),
]
for r, a, fy, row, conf, n in note20:
    ssss.append(mk(r, a, fy, 'note 20 other expenses', 'Cons_SCH', row, conf, n))

# Finance costs
fin = [
    ('Bank Charges,Processing Fees', 2672100, 2023, 85, 'verified', 'Bank charges/processing fees -> Row 85'),
    ('Interest on Bank O.D', 47144526, 2023, 84, 'verified', 'Bank OD/overdraft interest = working capital -> Row 84 (not Row 83)'),
    ('Interest Paid on Trading', 1537446, 2023, 84, 'verified', 'SSSS-009: Interest on supplier credit = trade financing -> Row 84 Working Capital'),
    ('Interest Paid On Secured Loan', 14224010, 2023, 83, 'verified', 'Interest on secured term loans -> Row 83 Fixed Loans'),
    ('Interest Paid On Unsecured Loan', 49438053, 2023, 83, 'verified', 'SSSS-008: Four Star Estates LLP promoter loan interest (unsecured but long-term) -> Row 83. NOT Row 84.'),
    ('Bank Charges,Processing Fees', 1773944, 2022, 85, 'verified', 'FY22: bank charges -> Row 85'),
    ('Interest on Bank O.D', 28551638, 2022, 84, 'verified', 'FY22: OD interest -> Row 84'),
    ('Interest Paid on Trading', 1587665, 2022, 84, 'verified', 'SSSS-009: FY22 trade interest -> Row 84'),
    ('Interest Paid On Secured Loan', 18838808, 2022, 83, 'verified', 'FY22: secured loan interest -> Row 83'),
    ('Interest Paid On Unsecured Loan', 59850582, 2022, 83, 'verified', 'SSSS-008: FY22 Four Star Estates LLP interest -> Row 83'),
]
for r, a, fy, row, conf, n in fin:
    sheet = 'Conso-sch' if fy <= 2023 else 'Cons_SCH'
    ssss.append(mk(r, a, fy, 'schedule-25 finance costs', sheet, row, conf, n))

# Depreciation and Tax
for r, a, fy, row in [
    ('Depreciation and Amortization Exp', 9300000, 2022, 63),
    ('Depreciation and Amortization Exp', 8800000, 2023, 63),
    ('Depreciation and Amortization Exp', 9700000, 2024, 63),
    ('Depreciation and Amortization Exp', 9600000, 2025, 63),
    ('Current tax expense', 37600000, 2022, 99),
    ('Current tax expense', 19400000, 2023, 99),
    ('Current tax expense', 18300000, 2024, 99),
    ('Current tax expense', 19700000, 2025, 99),
    ('Deferred tax', -200000, 2022, 101),
    ('Deferred tax', -600000, 2023, 101),
]:
    sheet = 'Conso-p&L' if fy <= 2023 else 'Cons_PL'
    ssss.append(mk(r, a, fy, 'profit and loss', sheet, row, 'high', f'FY{fy}: {cma_fields.get(row, "")} -> Row {row}'))

# Balance Sheet Liabilities
bsl = [
    ('Share Capital', 24000000, 2022, 'Conso - BS', 116, 'high', 'Share capital -> Row 116'),
    ('Share Capital', 24000000, 2023, 'Conso - BS', 116, 'high', 'Share capital -> Row 116'),
    ('Share Capital', 24000000, 2024, 'Cons_BS', 116, 'high', 'Share capital -> Row 116'),
    ('Share Capital', 24000000, 2025, 'Cons_BS', 116, 'high', 'Share capital -> Row 116'),
    ('Share Premium A/c', 197500000, 2023, 'Conso-sch Bs', 123, 'high', 'Share premium -> Row 123'),
    ('Profit & Loss Account (Brought Forward)', 285000000, 2022, 'Conso-sch Bs', 122, 'high', 'Accumulated P&L -> Row 122'),
    ('Profit & Loss Account (Brought Forward)', 411300000, 2023, 'Conso-sch Bs', 122, 'high', 'FY23 opening P&L balance -> Row 122'),
    ('Unsecured - Four Star Estates LLP (Quasi Equity portion)', 60000000, 2022, 'Conso-sch Bs', 152, 'verified', 'SSSS-012: CA designates fixed 6 Cr as quasi equity per bank requirement -> Row 152'),
    ('Unsecured - Four Star Estates LLP (balance)', 305000000, 2022, 'Conso-sch Bs', 153, 'verified', 'SSSS-012: FY22 LTD balance (36.50-6=30.50 Cr) -> Row 153'),
    ('Unsecured - Four Star Estates LLP (Quasi Equity portion)', 60000000, 2023, 'Conso-sch Bs', 152, 'verified', 'SSSS-012: FY23 quasi equity 6 Cr -> Row 152'),
    ('Unsecured - Four Star Estates LLP (balance)', 517100000, 2023, 'Conso-sch Bs', 153, 'verified', 'SSSS-012: FY23 LTD (57.71-6=51.71 Cr) -> Row 153'),
    ('Unsecured - Four Star Estates LLP (Quasi Equity portion)', 60000000, 2024, 'Cons_SCH', 152, 'verified', 'SSSS-012: FY24 quasi equity -> Row 152'),
    ('Unsecured - Four Star Estates LLP (balance)', 322100000, 2024, 'Cons_SCH', 153, 'verified', 'SSSS-012: FY24 LTD (38.21-6=32.21 Cr) -> Row 153'),
    ('Unsecured - Four Star Estates LLP (Quasi Equity portion)', 60000000, 2025, 'Cons_SCH', 152, 'verified', 'SSSS-012: FY25 quasi equity -> Row 152'),
    ('Unsecured - Four Star Estates LLP (balance)', 296800000, 2025, 'Cons_SCH', 153, 'verified', 'SSSS-012: FY25 LTD (35.68-6=29.68 Cr) -> Row 153'),
    ('Axis Bank Term Loan', 10900000, 2023, 'Conso-sch Bs', 137, 'high', 'Axis secured term loan -> Row 137'),
    ('Kotak Mahindra Prime -Car Loan', 1000000, 2023, 'Conso-sch Bs', 137, 'high', 'Car loan (liability) -> Row 137'),
    ('WCDL HDFC Term Loan', 42100000, 2022, 'Conso-sch Bs', 137, 'verified', 'SSSS-011: HDFC WCDL = term loan (NOT OD) -> Row 137'),
    ('WCDL HDFC Term Loan', 42100000, 2023, 'Conso-sch Bs', 137, 'verified', 'SSSS-011: HDFC WCDL term loan -> Row 137'),
    ('WCDL HSBC Term Loan', 30500000, 2022, 'Conso-sch Bs', 137, 'verified', 'SSSS-011: HSBC WCDL term loan -> Row 137'),
    ('WCDL HSBC Term Loan', 30500000, 2023, 'Conso-sch Bs', 137, 'verified', 'SSSS-011: HSBC WCDL -> Row 137'),
    ('WCDL Kotak Term Loan', 33900000, 2022, 'Conso-sch Bs', 137, 'verified', 'SSSS-011: Kotak WCDL -> Row 137'),
    ('Hsbc Ltd A/C', 218200000, 2022, 'Conso-sch Bs', 131, 'verified', 'SSSS-011: HSBC OD account = working capital -> Row 131'),
    ('Hsbc Ltd A/C', 266152543, 2023, 'Conso-sch Bs', 131, 'verified', 'SSSS-011: HSBC OD -> Row 131'),
    ('HDCF Bank Od A/C', 242200000, 2022, 'Conso-sch Bs', 131, 'verified', 'SSSS-011: HDFC OD account -> Row 131'),
    ('HDCF Bank Od A/C', 212900000, 2023, 'Conso-sch Bs', 131, 'verified', 'SSSS-011: HDFC OD -> Row 131'),
    ('Kotak Mahindra Bank Ltd O/D', 93600000, 2022, 'Conso-sch Bs', 131, 'verified', 'SSSS-011: Kotak OD -> Row 131'),
    ('Kotak Mahindra Bank Ltd O/D', 87800000, 2023, 'Conso-sch Bs', 131, 'verified', 'SSSS-011: Kotak OD -> Row 131'),
    ('Trade Payables', 143400000, 2022, 'Conso - BS', 242, 'high', 'FY22: trade creditors -> Row 242'),
    ('Trade Payables', 202500000, 2023, 'Conso - BS', 242, 'high', 'FY23: trade creditors -> Row 242'),
    ('Sundry Creditors for purchases', 19200000, 2024, 'Cons_SCH', 242, 'high', 'FY24: purchase creditors -> Row 242'),
    ('Sundry Creditors for expenses', 6900000, 2024, 'Cons_SCH', 249, 'high', 'FY24: expense creditors -> Row 249'),
    ('Sundry Creditors for purchases', 40900000, 2025, 'Cons_SCH', 242, 'high', 'FY25: purchase creditors -> Row 242'),
    ('Sundry Creditors for expenses', 25600000, 2025, 'Cons_SCH', 249, 'high', 'FY25: expense creditors -> Row 249'),
]
for r, a, fy, sheet, row, conf, n in bsl:
    ssss.append(mk(r, a, fy, 'balance sheet liabilities', sheet, row, conf, n))

# Balance Sheet Assets
bsa = [
    ('Tangible Assets', 101900000, 2022, 'Conso - BS', 162, 'high', 'FY22 fixed assets -> Row 162 Gross Block'),
    ('Tangible Assets', 97000000, 2023, 'Conso - BS', 162, 'high', 'FY23 fixed assets -> Row 162'),
    ('Property, Plant And Equipments', 99200000, 2024, 'Cons_BS', 162, 'high', 'FY24 fixed assets -> Row 162'),
    ('Property, Plant And Equipments', 95200000, 2025, 'Cons_BS', 162, 'high', 'FY25 fixed assets -> Row 162'),
    ('Investment in Equity Instruments', 61600000, 2022, 'Conso - BS', 186, 'high', 'Non-current equity investments -> Row 186'),
    ('Investment in Equity Instruments', 53900000, 2023, 'Conso - BS', 186, 'high', 'Non-current investments -> Row 186'),
    ('Share Investments', 65600000, 2024, 'Cons_SCH', 186, 'high', 'Non-current investments -> Row 186'),
    ('Share Investments', 74000000, 2025, 'Cons_SCH', 186, 'high', 'Non-current investments -> Row 186'),
    ('Finished Goods.', 875400000, 2022, 'Conso-sch Bs', 201, 'high', 'FY22 stock in trade -> Row 201'),
    ('Finished Goods.', 1015300000, 2023, 'Conso-sch Bs', 201, 'high', 'FY23 stock in trade -> Row 201'),
    ('Stock In Trade', 767500000, 2024, 'Cons_SCH', 201, 'high', 'FY24 stock in trade -> Row 201'),
    ('Stock In Trade', 776400000, 2025, 'Cons_SCH', 201, 'high', 'FY25 stock in trade -> Row 201'),
    ('Trade Receivables', 762700000, 2022, 'Conso - BS', 206, 'high', 'FY22 trade receivables -> Row 206'),
    ('Others Unsecured, considered good', 645800000, 2024, 'Cons_SCH', 206, 'high', 'FY24 debtors < 6 months -> Row 206'),
    ('Others Unsecured, considered good', 569600000, 2025, 'Cons_SCH', 206, 'high', 'FY25 debtors < 6 months -> Row 206'),
    ('Outstanding for Period Above Six Month', 89900000, 2024, 'Cons_SCH', 208, 'high', 'FY24 debtors > 6 months -> Row 208'),
    ('Outstanding for Period Above Six Month', 115900000, 2025, 'Cons_SCH', 208, 'high', 'FY25 debtors > 6 months -> Row 208'),
    ('Cash In Indian Rupees', 3900000, 2023, 'Conso-sch Bs', 212, 'high', 'Cash in hand -> Row 212'),
    ('Cash Balances', 3200000, 2022, 'Conso-sch Bs', 212, 'high', 'FY22 cash in hand -> Row 212'),
    ('Cash Balances', 5000000, 2024, 'Cons_SCH', 212, 'high', 'FY24 cash -> Row 212'),
    ('Cash Balances', 4500000, 2025, 'Cons_SCH', 212, 'high', 'FY25 cash -> Row 212'),
    ('Bank Balances (current accounts)', 1300000, 2023, 'Conso-sch Bs', 213, 'high', 'Bank current accounts -> Row 213'),
    ('Bank Balances (current accounts)', 3300000, 2022, 'Conso-sch Bs', 213, 'high', 'FY22 bank balances -> Row 213'),
    ('Fixed Deposits with Bank', 52500000, 2024, 'Cons_SCH', 215, 'high', 'FY24 fixed deposits -> Row 215'),
    ('Fixed Deposits with Bank', 52100000, 2025, 'Cons_SCH', 215, 'high', 'FY25 FDs -> Row 215'),
    ('Fixed Deposits (total)', 53161533, 2023, 'Conso-sch Bs', 215, 'high', 'FY23 FDs -> Row 215 (lien FDs may be Row 214; default Row 215)'),
    ('Balance With Government Authorities', 76860349, 2023, 'Conso-sch Bs', 221, 'verified', 'SSSS-013: All govt balances (Advance Tax+IT Paid+GST+TDS) -> Row 221 per CA FY23 treatment'),
    ('Balances with Statutory Authorities', 65300000, 2024, 'Cons_SCH', 223, 'verified', 'SSSS-013: FY24 statutory balances -> Row 223 (CA uses Row 223 for FY24/25)'),
    ('Balances with Statutory Authorities', 64800000, 2025, 'Cons_SCH', 223, 'verified', 'SSSS-013: FY25 statutory balances -> Row 223'),
    ('Gst Credit Ledger', 12766181, 2023, 'Conso-sch Bs', 221, 'verified', 'SSSS-013: GST ITC balance included in CAs consolidated Row 221 for FY23'),
    ('Advance Tax', 5700000, 2023, 'Conso-sch Bs', 221, 'verified', 'SSSS-013: Advance tax paid -> Row 221'),
    ('Income Tax Paid on Regular Assessment', 21287955, 2023, 'Conso-sch Bs', 221, 'verified', 'SSSS-013: IT paid on assessment -> Row 221'),
    ('JSL/JSHL Discount Receivable', 28752999, 2023, 'Conso-sch', 223, 'verified', 'SSSS-002: Supplier discount receivable from Jindal Stainless -> Row 223 Other Advances. NOT Row 206 (trade debtors from customers).'),
    ('Electricity Board-Deposit', 55070, 2023, 'Conso-sch Bs', 237, 'high', 'Electricity board security deposit -> Row 237 govt utility deposit'),
    ('Telephone Deposit', 26318, 2023, 'Conso-sch Bs', 237, 'high', 'Telecom security deposit -> Row 237'),
    ('EMD', 2044249, 2023, 'Conso-sch Bs', 223, 'high', 'Earnest money deposits for tenders/auctions -> Row 223 Other Advances'),
]
for r, a, fy, sheet, row, conf, n in bsa:
    ssss.append(mk(r, a, fy, 'balance sheet assets', sheet, row, conf, n))

print(f'SSSS items: {len(ssss)}')
with open('DOCS/extractions/SSSS_classification_ground_truth.json', 'w', encoding='utf-8') as f:
    json.dump(ssss, f, ensure_ascii=False, indent=2)
print('SSSS done')

# ============================================================
# KURUNJI RETAIL GROUND TRUTH
# ============================================================
kr = []

# FY22 (from CMA ground truth - all verified)
fy22_pl = [
    ('Domestic Sales', 146686000, 2022, 'profit and loss', 'CMA INPUT SHEET', 22, 'verified', 'FY22 net retail sales -> Row 22'),
    ('Purchases', 122308000, 2022, 'trading account', 'CMA INPUT SHEET', 42, 'verified', 'FY22 goods purchases -> Row 42'),
    ('Opening Stock', 37733000, 2022, 'trading account', 'CMA INPUT SHEET', 58, 'verified', 'FY22 opening stock of retail goods -> Row 58'),
    ('Closing Stock', 25546000, 2022, 'trading account', 'CMA INPUT SHEET', 59, 'verified', 'FY22 closing stock -> Row 59 (P&L) and Row 201 (BS)'),
    ('Wages (Salary+PF+ESI+Staff costs)', 4064000, 2022, 'profit and loss', 'CMA INPUT SHEET', 45, 'verified', 'FY22 all employee costs combined -> Row 45'),
    ('Power/Electricity', 1378000, 2022, 'profit and loss', 'CMA INPUT SHEET', 48, 'verified', 'FY22 electricity -> Row 48'),
    ('Others Manufacturing (incl. Rent)', 740000, 2022, 'profit and loss', 'CMA INPUT SHEET', 49, 'verified', 'KR-004: FY22 rent + other mfg -> Row 49 (retail CA treats store rent as manufacturing cost)'),
    ('Depreciation', 670000, 2022, 'profit and loss', 'CMA INPUT SHEET', 63, 'verified', 'FY22 depreciation -> Row 63'),
    ('Others Admin', 550000, 2022, 'profit and loss', 'CMA INPUT SHEET', 71, 'verified', 'FY22 others admin -> Row 71'),
    ('Repairs & Maintenance', 80000, 2022, 'profit and loss', 'CMA INPUT SHEET', 72, 'verified', 'FY22 repairs -> Row 72'),
    ('Partners Salary', 1200000, 2022, 'profit and loss', 'CMA INPUT SHEET', 73, 'verified', 'KR-002: FY22 partners salary -> Row 73 (Directors Remuneration equivalent for firms)'),
    ('Interest Fixed Loans', 1069000, 2022, 'profit and loss', 'CMA INPUT SHEET', 83, 'verified', 'KR-003: FY22 interest on partner capital -> Row 83'),
    ('Interest WC Loans', 1867000, 2022, 'profit and loss', 'CMA INPUT SHEET', 84, 'verified', 'FY22 bank CC/OD interest -> Row 84'),
]
for r, a, fy, sec, sheet, row, conf, n in fy22_pl:
    kr.append(mk(r, a, fy, sec, sheet, row, conf, n))

fy22_bs = [
    ("Partners' Capital", 13367000, 2022, 'balance sheet liabilities', 'CMA INPUT SHEET', 116, 'verified', 'KR-001: Partners capital = equivalent of Share Capital -> Row 116'),
    ('WC Bank Finance (ICICI)', 22254000, 2022, 'balance sheet liabilities', 'CMA INPUT SHEET', 131, 'verified', 'ICICI CC/OD facility -> Row 131'),
    ('Unsecured Loans Quasi Equity', 3140000, 2022, 'balance sheet liabilities', 'CMA INPUT SHEET', 152, 'verified', 'Quasi equity portion of partner/promoter loans -> Row 152'),
    ('Gross Block', 14575000, 2022, 'balance sheet assets', 'CMA INPUT SHEET', 162, 'verified', 'Fixed assets gross block -> Row 162'),
    ('Finished Goods (Stock)', 25546000, 2022, 'balance sheet assets', 'CMA INPUT SHEET', 201, 'verified', 'Closing stock of retail goods -> Row 201'),
    ('Sundry Debtors', 2431000, 2022, 'balance sheet assets', 'CMA INPUT SHEET', 206, 'verified', 'Trade debtors -> Row 206'),
    ('Cash on Hand', 295000, 2022, 'balance sheet assets', 'CMA INPUT SHEET', 212, 'verified', 'Cash in hand -> Row 212'),
    ('Bank Balances', 818000, 2022, 'balance sheet assets', 'CMA INPUT SHEET', 213, 'verified', 'Bank current accounts -> Row 213'),
    ('Other Non-Current Assets (Rental Advances)', 2690000, 2022, 'balance sheet assets', 'CMA INPUT SHEET', 238, 'verified', 'KR-014: Private landlord rental advance deposit -> Row 238. NOT Row 237 (govt utility deposits).'),
    ('Sundry Creditors', 7430000, 2022, 'balance sheet liabilities', 'CMA INPUT SHEET', 242, 'verified', 'Trade creditors -> Row 242'),
]
for r, a, fy, sec, sheet, row, conf, n in fy22_bs:
    kr.append(mk(r, a, fy, sec, sheet, row, conf, n))

# FY23 P&L (from ITR 2022-2023.pdf)
fy23_pl = [
    ('Opening Stock', 25556400, 2023, 'trading account', 'P&L p04', 58, 'high', 'FY23 opening stock (= FY22 closing 2.55 Cr) -> Row 58'),
    ('Purchases', 269911634, 2023, 'trading account', 'P&L p04', 42, 'verified', 'FY23 goods purchases (26.99 Cr) -> Row 42'),
    ('Freight (Inward)', 432512, 2023, 'trading account', 'P&L p04', 47, 'high', 'Inward freight on purchases -> Row 47 Freight and Transportation'),
    ('Sales', 305175359, 2023, 'trading account', 'P&L p04', 22, 'verified', 'FY23 net retail sales (30.52 Cr) -> Row 22'),
    ('Closing Stock', 20368400, 2023, 'trading account', 'P&L p04', 201, 'verified', 'FY23 closing retail inventory -> Row 201 (Balance Sheet)'),
    ('Discount Received', 280181, 2023, 'profit and loss account', 'P&L p04', 42, 'high', 'Supplier discount on purchases -> nets against Row 42'),
    ('Interest', 388270, 2023, 'profit and loss account', 'P&L p04', 30, 'high', 'Interest income -> Row 30'),
    ('Other Interest', 15518, 2023, 'profit and loss account', 'P&L p04', 30, 'high', 'Other interest income -> Row 30'),
    ('Salary and Bonus', 5555245, 2023, 'profit and loss account', 'P&L p04', 45, 'verified', 'FY23 salaries to employees -> Row 45 (retail CA bundles all employee costs here)'),
    ('Rent', 4095000, 2023, 'profit and loss account', 'P&L p04', 49, 'verified', 'KR-004: Store rent -> Row 49 (NOT Row 68). Retail CA treats store as production facility.'),
    ('TDS on Rent', 455000, 2023, 'profit and loss account', 'P&L p04', 49, 'verified', 'KR-005: TDS on rent (Tally artifact) -> same row as Rent = Row 49. Mathematical proof: 40.95+4.55=45.50 gross; TDS=10% confirms it is part of rent.'),
    ('Rent - Parking', 240000, 2023, 'profit and loss account', 'P&L p04', 49, 'verified', 'KR-004: Parking rent -> Row 49 (same CA style as store rent)'),
    ('Electric/Phone Charges', 6911541, 2023, 'profit and loss account', 'P&L p04', 48, 'verified', 'KR-006: Combined electricity+phone single entry -> ENTIRE amount to Row 48. Confirmed: CMA Row 48 FY23 = 69.12 lakhs = exact match.'),
    ('Staff Welfare', 373932, 2023, 'profit and loss account', 'P&L p04', 45, 'verified', 'KR-007: Staff welfare -> Row 45 (all employee costs bundled in wages for retail)'),
    ('Staff Mess Expenses', 396640, 2023, 'profit and loss account', 'P&L p04', 45, 'verified', 'KR-007: Staff mess/food -> Row 45'),
    ('Bank Interest and Charges', 1624303, 2023, 'profit and loss account', 'P&L p04', 84, 'high', 'Bank CC/OD interest -> Row 84 Working Capital Interest'),
    ('Provident Fund', 556438, 2023, 'profit and loss account', 'P&L p04', 45, 'verified', 'PF contribution -> Row 45'),
    ('ESI', 90534, 2023, 'profit and loss account', 'P&L p04', 45, 'verified', 'ESI contribution -> Row 45'),
    ('Salary to Partners', 1200000, 2023, 'profit and loss account', 'P&L p04', 73, 'verified', 'KR-002: Partners salary/remuneration -> Row 73 (Directors Remuneration row; CMA has no dedicated partners salary row)'),
    ('Repairs and Maintenance', 108027, 2023, 'profit and loss account', 'P&L p04', 72, 'high', 'Repairs -> Row 72'),
    ('Interest to Partners', 1604010, 2023, 'profit and loss account', 'P&L p04', 83, 'verified', 'KR-003: Interest on partner capital -> Row 83 Fixed Loans Interest. CMA Row 83 FY23 = 16.04 lakhs = exact match.'),
    ('Depreciation', 3236496, 2023, 'profit and loss account', 'P&L p04', 63, 'high', 'Depreciation -> Row 63'),
    ('Packing Expenses', 591988, 2023, 'profit and loss account', 'P&L p04', 71, 'verified', 'KR-008: Small packing expenses (5.92L < 10L threshold) -> Row 71 (NOT Row 44; large amounts go to Row 44)'),
    ('Miscellaneous Expenses', 89373, 2023, 'profit and loss account', 'P&L p04', 71, 'high', 'Miscellaneous -> Row 71'),
    ('Professional Fees', 90000, 2023, 'profit and loss account', 'P&L p04', 71, 'high', 'Audit/professional fees -> Row 71'),
    ('Insurance/Freight', 94362, 2023, 'profit and loss account', 'P&L p04', 71, 'high', 'Insurance and small freight -> Row 71'),
    ('Advertisement Expenses', 1008740, 2023, 'profit and loss account', 'P&L p04', 70, 'high', 'Advertisement -> Row 70'),
    ('Digital Marketing', 594442, 2023, 'profit and loss account', 'P&L p04', 70, 'verified', 'KR-009: Digital marketing = advertising by digital channel -> Row 70. Combined with Ads = 16.03 lakhs = CMA Row 70 FY23.'),
]
for r, a, fy, sec, sheet, row, conf, n in fy23_pl:
    kr.append(mk(r, a, fy, sec, sheet, row, conf, n))

fy23_bs = [
    ("Partners' Capital Accounts", 34255012, 2023, 'balance sheet liabilities', 'BS p05', 116, 'verified', 'KR-001: Partners capital (5 partners, total 3.43 Cr) -> Row 116'),
    ('Loans (bank CC/OD ICICI)', 21475097, 2023, 'balance sheet liabilities', 'BS p05', 131, 'verified', 'ICICI CC/OD working capital loan -> Row 131'),
    ('Unsecured Loans (Quasi Equity)', 3140000, 2023, 'balance sheet liabilities', 'BS p05', 152, 'verified', 'Quasi equity designation by bank -> Row 152'),
    ('Sundry Creditors', 7863312, 2023, 'balance sheet liabilities', 'BS p05', 242, 'high', 'Trade creditors -> Row 242'),
    ('Fixed Assets (Net Block)', 34291797, 2023, 'balance sheet assets', 'BS p05', 162, 'high', 'FY23 net block of fixed assets -> Row 162'),
    ('Sundry Debtors', 7125932, 2023, 'balance sheet assets', 'BS p05', 206, 'high', 'Trade debtors -> Row 206'),
    ('Cash on Hand', 250868, 2023, 'balance sheet assets', 'BS p05', 212, 'high', 'Cash in hand -> Row 212'),
    ('Bank Balances (ICICI accounts)', 2006422, 2023, 'balance sheet assets', 'BS p05', 213, 'high', 'Bank current accounts -> Row 213'),
    ('Other Non-Current Assets (Rental Advances)', 2690000, 2023, 'balance sheet assets', 'BS p05', 238, 'verified', 'KR-014: Rental advance to private landlord -> Row 238 (NOT Row 237)'),
    ('Stock in Trade (Finished Goods)', 20368400, 2023, 'balance sheet assets', 'BS p05', 201, 'verified', 'FY23 retail inventory -> Row 201'),
]
for r, a, fy, sec, sheet, row, conf, n in fy23_bs:
    kr.append(mk(r, a, fy, sec, sheet, row, conf, n))

# FY24 P&L
fy24_pl = [
    ('Opening Stock', 20368400, 2024, 'trading account', 'P&L p03', 58, 'high', 'FY24 opening stock (= FY23 closing 2.04 Cr) -> Row 58'),
    ('Purchases', 414102796, 2024, 'trading account', 'P&L p03', 42, 'verified', 'FY24 goods purchases (41.41 Cr) -> Row 42'),
    ('Sales', 401597059, 2024, 'trading account', 'P&L p03', 22, 'verified', 'FY24 net sales (40.16 Cr) -> Row 22. Verified balanced with trading account totals.'),
    ('Closing Stock', 69771600, 2024, 'trading account', 'P&L p03', 201, 'verified', 'FY24 closing inventory (6.98 Cr - large jump from FY23 2.04 Cr) -> Row 201'),
    ('Discount Received', 11194, 2024, 'profit and loss account', 'P&L p03', 42, 'high', 'Supplier discount -> nets against Row 42'),
    ('Incentive', 63257, 2024, 'profit and loss account', 'P&L p03', 30, 'high', 'Incentive income -> Row 30'),
    ('Other Interest', 303282, 2024, 'profit and loss account', 'P&L p03', 30, 'high', 'Interest income -> Row 30'),
    ('Stock of Packing Materials', 125000, 2024, 'profit and loss account', 'P&L p03', 198, 'verified', 'KR-012: Closing stock of packing materials (P&L credit entry) -> Row 198 Stores & Spares BS inventory. Not Row 201 (that is for goods sold).'),
    ('Salary and Bonus', 5569430, 2024, 'profit and loss account', 'P&L p03', 45, 'verified', 'FY24 salaries -> Row 45'),
    ('Rent', 4860000, 2024, 'profit and loss account', 'P&L p03', 49, 'verified', 'KR-004: Store rent -> Row 49'),
    ('TDS on Rent', 540000, 2024, 'profit and loss account', 'P&L p03', 49, 'verified', 'KR-005: TDS on rent -> Row 49 (same as Rent). Verified: gross rent = 48.60+5.40=54.00; TDS=10%.'),
    ('Rent - Parking', 238000, 2024, 'profit and loss account', 'P&L p03', 49, 'verified', 'KR-004: Parking rent -> Row 49'),
    ('Electric/Phone Charges', 9707993, 2024, 'profit and loss account', 'P&L p03', 48, 'verified', 'KR-006: Combined electricity+phone -> Row 48 entirely. CMA Row 48 FY24 = 97.08 lakhs = exact match.'),
    ('Staff Welfare', 37660, 2024, 'profit and loss account', 'P&L p03', 45, 'high', 'Staff welfare -> Row 45'),
    ('Staff Mess Expenses', 402500, 2024, 'profit and loss account', 'P&L p03', 45, 'verified', 'KR-007: Staff mess -> Row 45'),
    ('Bank Interest and Charges', 1624386, 2024, 'profit and loss account', 'P&L p03', 84, 'high', 'Bank CC/OD interest -> Row 84'),
    ('Provident Fund', 493061, 2024, 'profit and loss account', 'P&L p03', 45, 'high', 'PF -> Row 45'),
    ('ESI', 87696, 2024, 'profit and loss account', 'P&L p03', 45, 'high', 'ESI -> Row 45'),
    ('Salary to Partners', 1020000, 2024, 'profit and loss account', 'P&L p03', 73, 'verified', 'KR-002: Partners salary -> Row 73'),
    ('Repairs and Maintenance', 205793, 2024, 'profit and loss account', 'P&L p03', 72, 'high', 'Repairs -> Row 72'),
    ('Interest to Partners', 856375, 2024, 'profit and loss account', 'P&L p03', 83, 'verified', 'KR-003: Interest on partner capital -> Row 83'),
    ('Generator Expenses', 213748, 2024, 'profit and loss account', 'P&L p03', 71, 'verified', 'KR-015: Generator expenses -> Row 71 (NOT Row 48). CA classified as admin. Proof: Row 48 FY24 = 97.08L = Electric/Phone only; no room for Generator in Row 48.'),
    ('Depreciation', 2921249, 2024, 'profit and loss account', 'P&L p03', 63, 'high', 'Depreciation -> Row 63'),
    ('Packing Expenses', 39249390, 2024, 'profit and loss account', 'P&L p03', 44, 'verified', 'KR-008: Large packing expenses (39.25L > 15L threshold) -> Row 44 Stores & Spares. Net of closing stock: 39.25-1.25=37.99L = CMA Row 44 FY24 exactly.'),
    ('Miscellaneous Expenses', 520021, 2024, 'profit and loss account', 'P&L p03', 71, 'high', 'Misc -> Row 71'),
    ('Advertisement Expenses', 552800, 2024, 'profit and loss account', 'P&L p03', 70, 'high', 'Advertisement -> Row 70'),
    ('Barcode Expenses', 683356, 2024, 'profit and loss account', 'P&L p03', 71, 'verified', 'KR-010: Barcode/MRP labels (retail-specific cost) -> Row 71. Not in 384-item reference.'),
    ('Bill Printing Roll', 559614, 2024, 'profit and loss account', 'P&L p03', 71, 'verified', 'KR-011: POS thermal paper rolls for billing machines -> Row 71. Retail-specific cost not in reference.'),
    ('Printing and Stationery', 274304, 2024, 'profit and loss account', 'P&L p03', 71, 'high', 'Printing and stationery -> Row 71'),
    ('Freight Charges', 692580, 2024, 'profit and loss account', 'P&L p03', 71, 'verified', 'Freight charges FY24 -> Row 71 (small retail delivery costs treated as admin, not Row 47)'),
]
for r, a, fy, sec, sheet, row, conf, n in fy24_pl:
    kr.append(mk(r, a, fy, sec, sheet, row, conf, n))

fy24_bs = [
    ("Partners' Capital Accounts", 38641423, 2024, 'balance sheet liabilities', 'BS p04', 116, 'verified', 'KR-001: FY24 partners capital -> Row 116'),
    ('ICICI Credit Account (CC/OD)', 39241507, 2024, 'balance sheet liabilities', 'BS p04', 131, 'verified', 'ICICI working capital CC/OD -> Row 131'),
    ("Partners' Current Account (unsecured)", 7000000, 2024, 'balance sheet liabilities', 'BS p04', 152, 'high', 'Partners current account loans -> Row 152 quasi equity treatment for partner funds'),
    ('Kurinji Metro / Other unsecured loan', 310000, 2024, 'balance sheet liabilities', 'BS p04', 153, 'high', 'Small unsecured loan -> Row 153 Long Term Debt'),
    ('Sundry Creditors', 32384587, 2024, 'balance sheet liabilities', 'BS p04', 242, 'high', 'Trade creditors -> Row 242'),
    ('Stock in Trade (Finished Goods)', 69771600, 2024, 'balance sheet assets', 'BS p04', 201, 'verified', 'FY24 retail inventory (6.98 Cr) -> Row 201'),
    ('Stock of Packing Materials', 125000, 2024, 'balance sheet assets', 'BS p04', 198, 'verified', 'KR-012: Closing stock of packing materials -> Row 198 Stores & Spares inventory'),
    ('Sundry Debtors', 9678270, 2024, 'balance sheet assets', 'BS p04', 206, 'high', 'Trade debtors -> Row 206'),
    ('Cash on Hand', 625951, 2024, 'balance sheet assets', 'BS p04', 212, 'high', 'Cash -> Row 212'),
    ('Bank Balances: ICICI Ca 68105100261', 2280593, 2024, 'balance sheet assets', 'BS p04', 213, 'high', 'Bank current account -> Row 213'),
    ('Bank Balances: ICICI Ca 6810530559B', 2469476, 2024, 'balance sheet assets', 'BS p04', 213, 'high', 'Second ICICI current account -> Row 213'),
    ('Rental Advances (non-current)', 3464766, 2024, 'balance sheet assets', 'BS p04', 238, 'verified', 'KR-014: Rental advance to private landlord -> Row 238'),
]
for r, a, fy, sec, sheet, row, conf, n in fy24_bs:
    kr.append(mk(r, a, fy, sec, sheet, row, conf, n))

# FY25 P&L
fy25_pl = [
    ('Opening Stock', 68866572, 2025, 'trading account', 'P&L p06', 58, 'high', 'FY25 opening stock (= FY24 closing 6.89 Cr) -> Row 58'),
    ('Purchases', 617337850, 2025, 'trading account', 'P&L p06', 42, 'verified', 'FY25 goods purchases (61.73 Cr calculated) -> Row 42'),
    ('Sales', 688664572, 2025, 'trading account', 'P&L p06', 22, 'verified', 'FY25 net sales (68.87 Cr) -> Row 22. Confirmed by CMA Row 22 = 6886.64 lakhs.'),
    ('Closing Stock', 65030182, 2025, 'trading account', 'P&L p06', 201, 'verified', 'FY25 closing retail inventory (6.50 Cr) -> Row 201'),
    ('Interest / Other Income', 82454, 2025, 'profit and loss account', 'P&L p06', 30, 'high', 'Interest and other income -> Row 30'),
    ('Others (Non-Operating Income)', 11563830, 2025, 'profit and loss account', 'P&L p06', 34, 'inferred', 'FY25 non-operating other income (source unclear - CA judgment) -> Row 34'),
    ('Salary and Bonus', 10866857, 2025, 'profit and loss account', 'P&L p06', 45, 'verified', 'FY25 salaries (1.09 Cr) -> Row 45'),
    ('Rent', 9962370, 2025, 'profit and loss account', 'P&L p06', 49, 'verified', 'KR-004: FY25 store rent -> Row 49'),
    ('Rent - Parking', 240000, 2025, 'profit and loss account', 'P&L p06', 49, 'verified', 'KR-004: Parking rent -> Row 49'),
    ('Electric Charges', 17233642, 2025, 'profit and loss account', 'P&L p06', 48, 'verified', 'KR-006: FY25 splits Electric from Telephone; electric charges still -> Row 48'),
    ('Staff Welfare', 346000, 2025, 'profit and loss account', 'P&L p06', 45, 'high', 'Staff welfare -> Row 45'),
    ('Bank Interest and Charges', 9363942, 2025, 'profit and loss account', 'P&L p06', 84, 'high', 'Bank CC/OD interest (large 93.64L in FY25) -> Row 84'),
    ('Provident Fund', 556000, 2025, 'profit and loss account', 'P&L p06', 45, 'high', 'PF -> Row 45'),
    ('ESI', 90000, 2025, 'profit and loss account', 'P&L p06', 45, 'high', 'ESI -> Row 45'),
    ('Salary to Partners', 1080000, 2025, 'profit and loss account', 'P&L p06', 73, 'verified', 'KR-002: FY25 partners salary -> Row 73'),
    ('Repairs and Maintenance', 9494308, 2025, 'profit and loss account', 'P&L p06', 72, 'high', 'FY25 repairs (large 94.94L) -> Row 72'),
    ('Interest to Partners', 2318485, 2025, 'profit and loss account', 'P&L p06', 83, 'verified', 'KR-003: FY25 partner interest (confirmed by tax computation) -> Row 83'),
    ('Depreciation', 5062171, 2025, 'profit and loss account', 'P&L p06', 63, 'verified', 'FY25 depreciation (confirmed by tax computation) -> Row 63'),
    ('Packing Expenses', 42471910, 2025, 'profit and loss account', 'P&L p06', 44, 'verified', 'KR-008: Large packing expenses (42.47L) -> Row 44 Stores & Spares'),
]
for r, a, fy, sec, sheet, row, conf, n in fy25_pl:
    kr.append(mk(r, a, fy, sec, sheet, row, conf, n))

fy25_bs = [
    ("Partners' Capital Accounts", 44286618, 2025, 'balance sheet liabilities', 'BS p07', 116, 'verified', 'KR-001: FY25 partners capital total -> Row 116'),
    ('ICICI CC/OD Account', 76553093, 2025, 'balance sheet liabilities', 'BS p07', 131, 'verified', 'FY25 ICICI CC/OD working capital -> Row 131'),
    ('Term Loans (ICICI / new facility)', 29386296, 2025, 'balance sheet liabilities', 'BS p07', 137, 'verified', 'FY25 new term loan facility -> Row 137'),
    ('Unsecured Loans Quasi Equity', 9391468, 2025, 'balance sheet liabilities', 'BS p07', 152, 'verified', 'FY25 quasi equity portion -> Row 152'),
    ('Unsecured Loans Long Term Debt', 20797516, 2025, 'balance sheet liabilities', 'BS p07', 153, 'high', 'FY25 unsecured LTD -> Row 153'),
    ('Sundry Creditors', 65081682, 2025, 'balance sheet liabilities', 'BS p07', 242, 'high', 'FY25 trade creditors -> Row 242'),
    ('Fixed Assets (Net Block)', 44298610, 2025, 'balance sheet assets', 'BS p07', 162, 'high', 'FY25 fixed assets net block -> Row 162'),
    ('Stock in Trade (Finished Goods)', 203617200, 2025, 'balance sheet assets', 'BS p07', 201, 'verified', 'FY25 retail inventory (20.36 Cr - massive jump) -> Row 201'),
    ('Stock of Packing Materials', 58500, 2025, 'balance sheet assets', 'BS p07', 198, 'verified', 'KR-012: FY25 closing packing stock -> Row 198'),
    ('Sundry Debtors', 0, 2025, 'balance sheet assets', 'BS p07', 206, 'verified', 'FY25 debtors = nil (confirmed) -> Row 206'),
    ('Dues from Partners', 9178270, 2025, 'balance sheet assets', 'BS p07', 235, 'verified', 'KR-013: Amounts owed by partners to firm -> Row 235 Dues from Directors/Partners/Promoters'),
    ('Other Advances / Sister Concern', 33059720, 2025, 'balance sheet assets', 'BS p07', 223, 'inferred', 'Advances to Kurinji Metro (sister concern) -> Row 223 Other Advances'),
    ('Cash on Hand', 1204578, 2025, 'balance sheet assets', 'BS p07', 212, 'high', 'Cash -> Row 212'),
    ('Bank Balances', 1361707, 2025, 'balance sheet assets', 'BS p07', 213, 'high', 'Bank accounts -> Row 213'),
]
for r, a, fy, sec, sheet, row, conf, n in fy25_bs:
    kr.append(mk(r, a, fy, sec, sheet, row, conf, n))

print(f'Kurunji items: {len(kr)}')
with open('DOCS/extractions/Kurunji_Retail_classification_ground_truth.json', 'w', encoding='utf-8') as f:
    json.dump(kr, f, ensure_ascii=False, indent=2)
print('Kurunji done')
print(f'Total: {len(ssss)} SSSS + {len(kr)} Kurunji = {len(ssss)+len(kr)} items')
