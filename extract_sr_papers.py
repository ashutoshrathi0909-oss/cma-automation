#!/usr/bin/env python3
"""
SR Papers Ground Truth Extraction
Extracts line items from SR Papers financial files and creates classification ground truth JSON.
Steps 3-7 of DOCS/testing/sr-papers-ground-truth-extraction.md
"""
import xlrd
import json
import re
import os

# ── Helpers ────────────────────────────────────────────────────────────────

def clean(s):
    if not isinstance(s, str):
        return str(s) if s else ''
    return re.sub(r'\s+', ' ', s.strip().replace('\n', ' '))


def is_total_row(label):
    lc = label.lower().strip()
    return (lc in ('total', 'sub total', 'sub-total', 'grand total', 'net total') or
            lc.startswith('total ') or lc.startswith('sub total'))


def is_skip_row(label):
    lc = label.lower().strip()
    skip = {'particulars', '', ' ', 'equity and liabilities', 'assets',
            'tangible assets', 'intangible assets', 's.no.', 'purchase', 'asset',
            'date of', 'numbers', 'rs', 'name of the shareholder', 'holding company'}
    return (lc in skip or lc.startswith('note ') or lc.startswith('s.r.papers') or
            lc.startswith('notes forming') or lc.startswith('(all amounts') or
            lc.startswith('balance at the beginning') or lc.startswith('add:') or
            lc.startswith('less:') or lc.startswith('balance at the end') or
            lc.startswith('add: profit') or lc.startswith('less: interim') or
            lc.startswith('there are no shares'))


def to_crores(amount):
    if not isinstance(amount, (int, float)):
        return None
    return round(amount / 1e7, 6)


# ── CMA Field → Row mapping ────────────────────────────────────────────────

FIELD_TO_ROW = {
    'Domestic Sales': 22,
    'Export Sales': 23,
    'Dividends received from Mutual Funds': 29,
    'Interest Received': 30,
    'Profit on sale of fixed assets / Investments': 31,
    'Gain on Exchange Fluctuations': 32,
    'Extraordinary income': 33,
    'Others (Non-Operating Income)': 34,
    'Raw Materials Consumed (Imported)': 41,
    'Raw Materials Consumed (Indigenous)': 42,
    'Wages': 45,
    'Processing / Job Work Charges': 46,
    'Freight and Transportation Charges': 47,
    'Power, Coal, Fuel and Water': 48,
    'Others (Manufacturing)': 49,
    'Repairs & Maintenance (Manufacturing)': 50,
    'Security Service Charges': 51,
    'Depreciation (Manufacturing)': 56,
    'Depreciation (CMA)': 63,
    'Other Manufacturing Exp (CMA)': 64,
    'Salary and staff expenses': 67,
    'Rent, Rates and Taxes': 68,
    'Bad Debts': 69,
    'Advertisements and Sales Promotions': 70,
    'Others (Admin)': 71,
    'Repairs & Maintenance (Admin)': 72,
    'Audit Fees & Directors Remuneration': 73,
    'Miscellaneous Expenses written off': 75,
    'Interest on Fixed Loans / Term loans': 83,
    'Interest on Working capital loans': 84,
    'Bank Charges': 85,
    'Loss on sale of fixed assets / Investments': 89,
    'Loss on Exchange Fluctuations': 91,
    'Others (Non-Operating Expenses)': 93,
    'Income Tax provision': 99,
    'Deferred Tax Liability (P&L)': 100,
    'Issued, Subscribed and Paid up': 116,
    'General Reserve': 121,
    'Share Premium A/c': 123,
    'Working Capital Bank Finance - Bank 1': 131,
    'Working Capital Bank Finance - Bank 2': 132,
    'Unsecured Loans - Quasi Equity': 152,
    'Unsecured Loans - Long Term Debt': 153,
    'Deferred tax liability (BS)': 159,
    'Gross Block': 162,
    'Less Accumulated Depreciation': 163,
    'Raw Material Indigenous': 194,
    'Domestic Receivables': 206,
    'Cash on Hand': 212,
    'Bank Balances': 213,
    'Advance Income Tax': 221,
    'Other Advances / current asset': 223,
    'Advances to group / subsidiaries companies': 224,
    'Security deposits with government departments': 237,
    'Sundry Creditors for goods': 242,
    'Other statutory liabilities (due within 1 year)': 246,
    'Other current liabilities': 250,
}

ROW_TO_FIELD = {v: k for k, v in FIELD_TO_ROW.items()}


# ── SR Papers Rule Engine ─────────────────────────────────────────────────

def classify_item(raw_text, section, sheet_name, amount_rupees, fy, cma_data):
    text = raw_text.lower().strip()
    sec = section.lower()

    # SRP-001: Customs Duty → Imported RM (Row 41)
    if re.search(r'customs.?duty|import.?duty|basic.?customs|^bcd$', text):
        return 'Raw Materials Consumed (Imported)', 41, 'verified', 'SRP-001: Customs Duty on imports → Row 41'

    # SRP-002: Hamali / Loading-Unloading → Freight (Row 47)
    if re.search(r'hamali|mathadi|unloading.?charges|loading.?charges', text):
        return 'Freight and Transportation Charges', 47, 'verified', 'SRP-002: Hamali/Unloading charges → Row 47'

    # SRP-003: CFS / Clearance / Liner → Other Mfg Exp (Row 64)
    if re.search(r'cfs.?charges|clearance.?charges|port.?clearance|liner.?charges|ocean.?freight|detention.?charges|demurrage', text):
        return 'Other Manufacturing Exp (CMA)', 64, 'verified', 'SRP-003: Import logistics (CFS/Clearance/Liner) → Row 64'

    # SRP-004: Delivery Charges → Other Mfg Exp (Row 64)
    if re.search(r'delivery.?charges', text) and ('note 17' in sec or 'other.?exp' in sec):
        return 'Other Manufacturing Exp (CMA)', 64, 'verified', 'SRP-004: Delivery Charges (distribution) → Row 64'

    # SRP-005: Discount Received → Non-Op Income (Row 34)
    if re.search(r'discount.?rec|discount.?income|trade.?discount.?received', text):
        return 'Others (Non-Operating Income)', 34, 'verified', 'SRP-005: Discount Received → Row 34'

    # SRP-006: Admin Exp for PF → Salary (Row 67)
    if re.search(r'admin.?exp.?for.?pf|pf.?admin|admin.?charges.?for.?pf|epfo.?admin', text):
        return 'Salary and staff expenses', 67, 'verified', 'SRP-006: PF Admin charges → Row 67'

    # SRP-007: Tea & Food → Salary (Row 67)
    if re.search(r'tea.?&.?food|tea.?and.?food|staff.?refreshment|canteen', text):
        return 'Salary and staff expenses', 67, 'verified', 'SRP-007: Tea & Food → Row 67'

    # SRP-008: Factory Expenses → Others Mfg (Row 49)
    if re.search(r'factory.?exp|factory.?overhead|godown.?exp|warehouse.?exp', text):
        return 'Others (Manufacturing)', 49, 'verified', 'SRP-008: Factory/Godown expenses → Row 49'

    # SRP-009: Royalty → Others Mfg (Row 49)
    if re.search(r'royalt|royali', text):
        return 'Others (Manufacturing)', 49, 'verified', 'SRP-009: Royalty (misspelled as Royality in source) → Row 49'

    # SRP-010: Stereo Charges → Advts (Row 70)
    if re.search(r'stereo.?charges|printing.?plate|block.?charges|plate.?charges', text):
        return 'Advertisements and Sales Promotions', 70, 'verified', 'SRP-010: Stereo/printing plate charges → Row 70'

    # SRP-011: Discount Allowed / Reversal → Advts (Row 70)
    if re.search(r'discount.?allow|discount.?given|discount.?reversal', text):
        return 'Advertisements and Sales Promotions', 70, 'verified', 'SRP-011: Discount Allowed/Reversal → Row 70'

    # SRP-012: Commission & Brokerage → Advts (Row 70)
    if re.search(r'commission.?&.?brokerage|commission.?paid|sales.?commission|brokerage', text):
        return 'Advertisements and Sales Promotions', 70, 'verified', 'SRP-012: Commission & Brokerage → Row 70'

    # SRP-013: Business Promotion → Advts (Row 70)
    if re.search(r'business.?promo|sales.?promo|marketing.?exp', text):
        return 'Advertisements and Sales Promotions', 70, 'verified', 'SRP-013: Business Promotion → Row 70'

    # SRP-014: FSC License → Others Admin (Row 71)
    if re.search(r'fsc.?license|fsc.?certif|forest.?stewardship|iso.?certif|certification.?charges', text):
        return 'Others (Admin)', 71, 'verified', 'SRP-014: FSC/certification license fees → Row 71'

    # SRP-016: TDS / TCS Receivable → Advance Income Tax (Row 221)
    if re.search(r'tds.?receivable|tcs.?receivable|tds.?refund|tds.?credit', text):
        return 'Advance Income Tax', 221, 'verified', 'SRP-016: TDS/TCS Receivable → Advance Income Tax Row 221'

    # SRP-018: Other Long Term Liabilities → Quasi Equity (Row 152)
    if re.search(r'other.?long.?term.?liabilit', text):
        return 'Unsecured Loans - Quasi Equity', 152, 'verified', 'SRP-018: Other Long-Term Liabilities → Quasi Equity Row 152'

    # SRP-020: Donations → Non-Op Expenses (Row 93)
    if re.search(r'^donation', text):
        return 'Others (Non-Operating Expenses)', 93, 'verified', 'SRP-020: Donation → Row 93'

    # SRP-021: Vehicle Haulting Income → Non-Op Income (Row 34)
    if re.search(r'vehicle.?haulting|vehicle.?hire.?charge|haulage.?income', text):
        return 'Others (Non-Operating Income)', 34, 'verified', 'SRP-021: Vehicle hire income → Row 34'

    # SRP-022: Currency Exchange → Row 32 / Row 91
    if re.search(r'currency.?exchange.?profit|currency.?fluctuation.?profit|exchange.?profit|forex.?gain', text):
        return 'Gain on Exchange Fluctuations', 32, 'verified', 'SRP-022: Currency Exchange Profit → Row 32'
    if re.search(r'currency.?exchange.?loss|currency.?fluctuation.?loss|forex.?loss', text):
        return 'Loss on Exchange Fluctuations', 91, 'verified', 'SRP-022: Currency Exchange Loss → Row 91'

    # ── Standard semantic mappings ─────────────────────────────────────────

    # P&L Income
    if re.search(r'paper.?&.?paper.?products', text):
        return 'Domestic Sales', 22, 'high', 'Paper & Paper Products = core sales → Domestic Sales Row 22'
    if re.search(r'interest.?income|interest.?from.?(banks?|fd|deposit)|bank.?interest', text):
        return 'Interest Received', 30, 'high', 'Interest income → Row 30'
    if re.search(r'rate.?difference', text) and ('note 13' in sec or 'income' in sec):
        return 'Others (Non-Operating Income)', 34, 'inferred', 'Rate difference (non-op income) → Row 34'
    if re.search(r'profit.?on.?sale.?of.?ass|profit.?on.?sale.?of.?fixed|gain.?on.?sale', text):
        return 'Profit on sale of fixed assets / Investments', 31, 'high', 'Profit on asset sale → Row 31'
    if re.search(r'insurance.?claim', text):
        return 'Others (Non-Operating Income)', 34, 'inferred', 'Insurance claim received = non-op income → Row 34'
    if re.search(r'miscellaneous.?income|misc.?income|round.?off', text) and ('note 13' in sec or 'income' in sec):
        return 'Others (Non-Operating Income)', 34, 'inferred', 'Misc income → Row 34'
    if re.search(r'dividend.?income', text):
        return 'Dividends received from Mutual Funds', 29, 'high', 'Dividend income → Row 29'

    # P&L Cost
    if re.search(r'cost.?of.?material.?consumed|purchase.?of.?raw.?material', text) and 'note 14' in sec:
        return 'Raw Materials Consumed (Indigenous)', 42, 'high', 'Cost of material consumed = Raw Materials Indigenous Row 42 (trading firm - SRP-019)'
    if re.search(r'salary.?and.?wages|salary.?&.?wages', text) and 'note 15' in sec:
        return 'Wages', 45, 'high', 'Salary and Wages → Row 45'
    if re.search(r'contribution.?to.?provident|pf.?contribution|provident.?fund|contributions? to pf|contributions? to provident', text):
        return 'Wages', 45, 'high', 'PF/provident fund contributions → Row 45 (wage pool)'
    if re.search(r'staff.?welfare', text) and 'note 15' in sec:
        return 'Wages', 45, 'high', 'Staff welfare expenses → Row 45 (wage pool)'
    if re.search(r'directors?.?remuneration', text) and 'note 15' in sec:
        return 'Audit Fees & Directors Remuneration', 73, 'high', 'Directors Remuneration → Row 73'
    # Note 16 Finance Cost - marked as inferred (SRP-015 requires manual split)
    if re.search(r'others?$', text) and 'note 16' in sec:
        return 'Interest on Fixed Loans / Term loans', 83, 'inferred', 'SRP-015: Finance Cost Others (combined) - NEEDS MANUAL SPLIT into TL(R83)/WC(R84)/BankChg(R85)'
    if re.search(r'audit.?fees?', text):
        return 'Audit Fees & Directors Remuneration', 73, 'high', 'Audit Fees → Row 73'
    if re.search(r'power.?and.?fuel|power.?&.?fuel|fuel.?&.?power|electricity', text):
        return 'Power, Coal, Fuel and Water', 48, 'high', 'Power and fuel → Row 48'
    if re.search(r'rent.?incl|rent.?including|rent.?and.?lease|rental', text):
        return 'Rent, Rates and Taxes', 68, 'high', 'Rent (including lease rentals) → Row 68'
    if re.search(r'^rent$', text):
        return 'Rent, Rates and Taxes', 68, 'high', 'Rent → Row 68'
    if re.search(r'rates.?and.?taxes|rate.?and.?tax', text):
        return 'Rent, Rates and Taxes', 68, 'high', 'Rates and Taxes → Row 68'
    if re.search(r'repairs.?and.?maintenance|repair.?.?maintenance', text):
        return 'Repairs & Maintenance (Manufacturing)', 50, 'high', 'Repairs & Maintenance → Row 50'
    if re.search(r'^insurance$', text):
        return 'Others (Admin)', 71, 'high', 'Insurance → Row 71'
    if re.search(r'communication|connectivity|telecom|telephone', text):
        return 'Others (Admin)', 71, 'high', 'Communication/connectivity → Row 71'
    if re.search(r'computer.?maint', text):
        return 'Others (Admin)', 71, 'high', 'Computer maintenance → Row 71'
    if re.search(r'consultancy.?fee|consulting', text):
        return 'Others (Admin)', 71, 'high', 'Consultancy fees → Row 71'
    if re.search(r'travelling|travel.?and.?conv|conveyance', text):
        return 'Others (Admin)', 71, 'high', 'Travel and conveyance → Row 71'
    if re.search(r'printing.?and.?station|stationery', text):
        return 'Others (Admin)', 71, 'high', 'Printing and stationery → Row 71'
    if re.search(r'^postage', text):
        return 'Others (Admin)', 71, 'high', 'Postage → Row 71'
    if re.search(r'professional.?fees?', text):
        return 'Others (Admin)', 71, 'high', 'Professional fees → Row 71'
    if re.search(r'packing.?&.?forwarding|packing.?and.?forwarding', text):
        return 'Others (Admin)', 71, 'inferred', 'Packing & Forwarding → Row 71'
    if re.search(r'membership.?fees?|membership.?charge', text):
        return 'Others (Admin)', 71, 'inferred', 'Membership fees → Row 71'
    if re.search(r'legal.?fees?', text):
        return 'Others (Admin)', 71, 'high', 'Legal fees → Row 71'
    if re.search(r'miscellaneous.?exp', text):
        return 'Others (Admin)', 71, 'high', 'Miscellaneous expenses → Row 71'
    if re.search(r'shop.?exp|shop.?expences', text):
        return 'Others (Admin)', 71, 'inferred', 'Shop expenses → Row 71'
    if re.search(r'design.?charges', text):
        return 'Others (Admin)', 71, 'inferred', 'Design charges → Row 71'
    if re.search(r'entertainment', text):
        return 'Others (Admin)', 71, 'inferred', 'Entertainment expenses → Row 71'
    if re.search(r'manpower.?charges|labour.?charges', text):
        return 'Wages', 45, 'inferred', 'Manpower/Labour charges → Row 45'
    if re.search(r'processing.?fee', text):
        return 'Bank Charges', 85, 'inferred', 'Processing fee (loan-related) → Row 85'
    if re.search(r'bank.?charges?', text):
        return 'Bank Charges', 85, 'high', 'Bank charges → Row 85'
    if re.search(r'^advertisement', text):
        return 'Advertisements and Sales Promotions', 70, 'high', 'Advertisement → Row 70'
    if re.search(r'gst.?expenditure|gst\s*-\s*expenditure|service.?tax.?exp|excise.?duty.?exp|vat.?exp', text):
        return None, None, 'skip', 'Historical tax expenditure - not classifiable'
    if re.search(r'forklift.?charges', text):
        return 'Other Manufacturing Exp (CMA)', 64, 'inferred', 'Forklift handling → Row 64'
    if re.search(r'barcode.?charges', text):
        return 'Others (Admin)', 71, 'inferred', 'Barcode charges → Row 71'
    if re.search(r'income.?tax.?provision|provision.?for.?income.?tax', text):
        return 'Income Tax provision', 99, 'high', 'Income tax provision → Row 99'
    if re.search(r'deferred.?tax', text):
        return 'Deferred Tax Liability (P&L)', 100, 'high', 'Deferred tax movement → Row 100'

    # BS items
    if re.search(r'issued.?subscribed.?and.?paid|equity.?shares.?of', text) and 'note 2' in sec:
        return 'Issued, Subscribed and Paid up', 116, 'high', 'Share capital → Row 116'
    if re.search(r'general.?reserve', text):
        return 'General Reserve', 121, 'high', 'General Reserve → Row 121'
    if re.search(r'share.?premium', text):
        return 'Share Premium A/c', 123, 'high', 'Share Premium → Row 123'
    if re.search(r'other.?than.?acceptances', text) and 'note 5' in sec:
        return 'Sundry Creditors for goods', 242, 'high', 'Trade payables → Row 242'
    if re.search(r'trade.?payable', text):
        return 'Sundry Creditors for goods', 242, 'high', 'Trade payables → Row 242'
    if re.search(r'statutory.?remittance', text):
        return 'Other statutory liabilities (due within 1 year)', 246, 'high', 'Statutory liabilities → Row 246'
    if re.search(r'expenses.?payable', text):
        return 'Other current liabilities', 250, 'high', 'Expenses payable → Row 250'
    if re.search(r'cash.?on.?hand', text):
        return 'Cash on Hand', 212, 'high', 'Cash on hand → Row 212'
    if re.search(r'current.?accounts?', text) and ('note 9' in sec or 'cash' in sec):
        return 'Bank Balances', 213, 'high', 'Current account balances → Row 213'
    if re.search(r'unsecured.?considered.?good', text) and ('note 8' in sec or 'receivable' in sec):
        return 'Domestic Receivables', 206, 'high', 'Trade receivables (unsecured) → Row 206'
    if re.search(r'trade.?receivable', text):
        return 'Domestic Receivables', 206, 'high', 'Trade receivables → Row 206'
    if re.search(r'security.?deposit', text):
        return 'Security deposits with government departments', 237, 'high', 'Security deposits → Row 237'
    if re.search(r'loans.?and.?advances.?to.?rel|related.?part', text) and 'note 10' in sec:
        return 'Advances to group / subsidiaries companies', 224, 'high', 'Related party L&A → Row 224'
    if re.search(r'other.?loans.?and.?advances', text) and 'note 10' in sec:
        return 'Other Advances / current asset', 223, 'high', 'Other L&A → Row 223'
    if re.search(r'loans.?and.?advances.?to.?emp', text):
        return 'Other Advances / current asset', 223, 'inferred', 'Employee advances → Row 223'
    if re.search(r'inventori', text) and 'note' in sec:
        return 'Raw Material Indigenous', 194, 'high', 'Inventories (trading) = Raw Material Indigenous Row 194 (SRP-019)'
    if re.search(r'deferred.?tax.?liabilit', text) and 'note 4' in sec:
        return 'Deferred tax liability (BS)', 159, 'high', 'Deferred tax liability on BS → Row 159'

    # FA individual asset items → Gross Block (Row 162)
    if re.search(r'plant.?&.?machinery|plant.?and.?machinery|electrical.?equipment|furniture|vehicles?$|office.?equipment|air.?conditioner|computers?$', text) and 'fixed asset' in sec:
        return 'Gross Block', 162, 'high', 'Fixed asset category → Gross Block Row 162'

    # Short-term borrowings - bank credit
    if re.search(r'^secured$', text) and 'borrowing' in sec:
        return 'Working Capital Bank Finance - Bank 1', 131, 'inferred', 'Secured bank borrowings → WC Bank Finance Row 131'
    if re.search(r'^unsecured$', text) and 'borrowing' in sec:
        return 'Unsecured Loans - Quasi Equity', 152, 'inferred', 'Unsecured borrowings (related party) → Quasi Equity Row 152'

    # IT Refund / income tax refund → Row 221
    if re.search(r'it.?refund|income.?tax.?refund|tax.?refund', text):
        return 'Advance Income Tax', 221, 'high', 'Income tax refund → Advance Income Tax Row 221'

    # Furniture Exp (expense, not asset) → Others Admin
    if re.search(r'furniture.?exp', text) and 'note 17' in sec:
        return 'Others (Admin)', 71, 'inferred', 'Furniture expenses → Others Admin Row 71'

    # Contractor Fees → Wages or Admin
    if re.search(r'contractor.?fees?', text):
        return 'Wages', 45, 'inferred', 'Contractor fees → Row 45 (wage pool)'

    # P&L on sale of car → Row 89 (loss) or Row 31 (profit)
    if re.search(r'p.?&.?l.?on.?sale|profit.?on.?sale.?of.?car|loss.?on.?sale.?of.?car', text):
        return 'Others (Non-Operating Expenses)', 93, 'inferred', 'P&L on sale of car → Non-Op Expenses Row 93 (verify sign)'

    # Training expenses → Salary and staff
    if re.search(r'training.?exp', text):
        return 'Salary and staff expenses', 67, 'inferred', 'Training expenses → Row 67 (staff development)'

    # Round off → skip
    if re.search(r'^round.?off$', text):
        return None, None, 'skip', 'Round-off entry - negligible'

    # GST/ST/ED/VAT expenditures → skip
    if re.search(r'gst.?expenditure|service.?tax.?exp|excise.?duty.?exp|vat.?exp|swatch.?bharat|krishi.?kalyan', text):
        return None, None, 'skip', 'Historical tax expenditure - not classifiable to CMA field'

    # Unsecured considered good (under Note 10 loans) → Other Advances
    if re.search(r'unsecured.*considered.?good', text) and 'note 10' in sec:
        return 'Other Advances / current asset', 223, 'high', 'Unsecured loans/advances (Note 10) → Row 223'

    # Amount-based matching fallback
    if amount_rupees and fy in cma_data:
        crores = to_crores(abs(amount_rupees))
        for row_num, fy_values in cma_data[fy].items():
            cma_val = fy_values.get('value', 0)
            if isinstance(cma_val, float) and cma_val > 0 and crores and crores > 0.001:
                if abs(cma_val - crores) / cma_val <= 0.02:  # 2% tolerance
                    field = ROW_TO_FIELD.get(row_num)
                    if field:
                        return field, row_num, 'high', f'Amount match: {crores:.4f} Cr ≈ CMA Row {row_num} ({cma_val:.4f} Cr)'

    return None, None, 'unknown', f'No rule matched for: "{raw_text[:50]}" in section "{section[:40]}"'


# ── CMA Data Loader ────────────────────────────────────────────────────────

def load_cma_data(cma_path):
    """Build CMA row → {FY: value} lookup from INPUT SHEET."""
    wb = xlrd.open_workbook(cma_path)
    ws = wb.sheet_by_name('INPUT SHEET')
    # Row 8 has years: col1=2023, col2=2024, col3=2025, col4=2026
    fy_cols = {2023: 1, 2024: 2, 2025: 3}
    cma_by_fy = {}
    for fy, col in fy_cols.items():
        cma_by_fy[fy] = {}
        for row in range(16, ws.nrows):
            v = ws.cell_value(row, col)
            if isinstance(v, float) and v != 0.0:
                cma_by_fy[fy][row + 1] = {'value': v, 'label': clean(ws.cell_value(row, 0))}
    return cma_by_fy


# ── Sheet Extractors ───────────────────────────────────────────────────────

def extract_note_18_24(wb, fy, cma_data):
    """Extract P&L line items from Note 18-24 sheet."""
    ws = wb.sheet_by_name('Note 18-24')
    items = []
    current_section = ''

    SKIP_ROW_LABELS = {
        'sale of services', 'sale of products', 'a) interest expenses on',
        'b) foreign exchange fluctuati', 'a) interest expenses',
        'purchase return', 'sales return',
    }

    for row in range(ws.nrows):
        label_raw = ws.cell_value(row, 0)
        label = clean(label_raw)
        if not label:
            continue

        # Track section from Note headers
        if re.match(r'note\s+\d+', label.lower()):
            current_section = label.lower()[:30]
            # Note 14 is a special case: the header row carries the total amount
            if 'note 14' in current_section:
                amount = ws.cell_value(row, 2)
                if isinstance(amount, float) and amount != 0:
                    field, row_num, confidence, reasoning = classify_item(
                        'Cost of Material Consumed', current_section, 'Note 18-24',
                        amount, fy, cma_data
                    )
                    if field and confidence != 'skip':
                        items.append({
                            'raw_text': 'Cost of Material Consumed',
                            'amount_rupees': amount,
                            'financial_year': fy,
                            'section': current_section,
                            'sheet_name': 'Note 18-24',
                            'correct_cma_field': field,
                            'correct_cma_row': row_num,
                            'confidence_note': confidence,
                            'reasoning': reasoning,
                        })
            continue

        # Skip total rows and non-data rows
        if is_total_row(label) or is_skip_row(label):
            continue
        if label.lower().strip() in SKIP_ROW_LABELS:
            continue

        # Get consolidated amount (col 2)
        amount = ws.cell_value(row, 2)
        if not isinstance(amount, float) or amount == 0.0:
            continue
        if abs(amount) < 100:  # skip tiny round-off amounts
            continue

        field, row_num, confidence, reasoning = classify_item(
            label, current_section, 'Note 18-24', amount, fy, cma_data
        )
        if confidence == 'skip':
            continue
        if field is None:
            confidence = 'unknown'

        items.append({
            'raw_text': label,
            'amount_rupees': round(amount, 2),
            'financial_year': fy,
            'section': current_section,
            'sheet_name': 'Note 18-24',
            'correct_cma_field': field,
            'correct_cma_row': row_num,
            'confidence_note': confidence,
            'reasoning': reasoning,
        })

    return items


def extract_note_3_17(wb, fy, cma_data):
    """Extract BS line items from Note 3-17 sheet."""
    ws = wb.sheet_by_name('Note 3-17')
    items = []
    current_section = ''

    # Determine amount column - for Note 3-17, col 2 is the consolidated total
    for row in range(ws.nrows):
        label_raw = ws.cell_value(row, 0)
        label = clean(label_raw)
        if not label:
            continue

        # Track section from Note headers in col 0
        note_match = re.match(r'note\s+\d+', label.lower())
        if note_match:
            current_section = label.lower()[:30]
            continue

        # Also check for section headers like 'DETAILS OF FIXED ASSETS'
        if re.match(r'details.?of.?fixed', label.lower()):
            current_section = 'fixed assets detail'
            continue

        if is_total_row(label) or is_skip_row(label):
            continue

        # Get consolidated amount - try col 2 first, then col 1
        amount = ws.cell_value(row, 2)
        if not isinstance(amount, float) or amount == 0.0:
            amount = ws.cell_value(row, 1)
            if not isinstance(amount, float) or amount == 0.0:
                continue

        if abs(amount) < 100:
            continue

        # Skip individual vehicle/asset detail lines in FA section
        if current_section == 'fixed assets detail' and (
            'car ' in label.lower() or 'honda' in label.lower() or
            'yamaha' in label.lower() or 'pulsar' in label.lower() or
            'jupiter' in label.lower() or 'maruthi' in label.lower() or
            'access' in label.lower()[:10]
        ):
            continue

        # Skip accumulated depreciation rows (negative sub-items under FA)
        if re.search(r'less.?accumulated.?depr|less.?accum.?depr', label.lower()):
            continue

        # Skip opening/closing balance rows in Reserves
        if re.search(r'balance at the (beginning|end)|add:.?profit|add:.?transferred|less:.?utilised', label.lower()):
            continue

        field, row_num, confidence, reasoning = classify_item(
            label, current_section, 'Note 3-17', amount, fy, cma_data
        )
        if confidence == 'skip':
            continue
        if field is None:
            confidence = 'unknown'

        items.append({
            'raw_text': label,
            'amount_rupees': round(amount, 2),
            'financial_year': fy,
            'section': current_section,
            'sheet_name': 'Note 3-17',
            'correct_cma_field': field,
            'correct_cma_row': row_num,
            'confidence_note': confidence,
            'reasoning': reasoning,
        })

    return items


def extract_note_2(wb, fy, cma_data):
    """Extract Share Capital from Note 2."""
    ws = wb.sheet_by_name('Note 2')
    items = []

    for row in range(ws.nrows):
        label = clean(ws.cell_value(row, 0))
        if not label:
            continue
        if re.search(r'equity shares of', label.lower()) and 'issued' not in label.lower():
            # Skip authorised shares rows - we want issued/subscribed
            pass
        if re.search(r'issued.?subscribed.?and.?paid|outstanding.?at.?the.?end', label.lower()):
            amount = ws.cell_value(row, 2)
            if isinstance(amount, float) and amount > 0:
                items.append({
                    'raw_text': 'Issued, Subscribed and Paid up (Share Capital)',
                    'amount_rupees': round(amount, 2),
                    'financial_year': fy,
                    'section': 'note 2 : share capital',
                    'sheet_name': 'Note 2',
                    'correct_cma_field': 'Issued, Subscribed and Paid up',
                    'correct_cma_row': 116,
                    'confidence_note': 'high',
                    'reasoning': 'Share capital directly maps to Row 116',
                })
                break  # Only capture once

    return items


# ── Main Extraction ────────────────────────────────────────────────────────

def main():
    base = os.path.dirname(os.path.abspath(__file__))

    files_config = [
        {
            'path': os.path.join(base, 'FInancials main/SR Papers/SRPAPERS_2023 - 24 - Updated.xls'),
            'fy': 2023,
            'actual_fy': 'March 31, 2023',
        },
        {
            'path': os.path.join(base, 'FInancials main/SR Papers/SRPAPERS_2024 - 25 - Updated.xls'),
            'fy': 2024,
            'actual_fy': 'March 31, 2024',
        },
        {
            'path': os.path.join(base, 'FInancials main/SR Papers/SRPAPERS_2025-26_-_Updated.xls'),
            'fy': 2025,
            'actual_fy': 'March 31, 2025',
        },
    ]

    cma_path = os.path.join(base, 'FInancials main/SR Papers/CMA S.R.Papers 09032026 v2.xls')

    print('Loading CMA ground truth data...')
    cma_data = load_cma_data(cma_path)
    print(f'  CMA rows loaded: FY2023={len(cma_data[2023])}, FY2024={len(cma_data[2024])}, FY2025={len(cma_data[2025])}')

    all_items = []

    for cfg in files_config:
        fy = cfg['fy']
        print(f'\nProcessing FY{fy} ({cfg["actual_fy"]})...')

        wb = xlrd.open_workbook(cfg['path'])
        sheets_used = []

        # Note 18-24 (P&L)
        items_18_24 = extract_note_18_24(wb, fy, cma_data)
        print(f'  Note 18-24: {len(items_18_24)} items')
        sheets_used.append(f'Note 18-24 ({len(items_18_24)} items)')
        all_items.extend(items_18_24)

        # Note 3-17 (BS)
        items_3_17 = extract_note_3_17(wb, fy, cma_data)
        print(f'  Note 3-17: {len(items_3_17)} items')
        sheets_used.append(f'Note 3-17 ({len(items_3_17)} items)')
        all_items.extend(items_3_17)

        # Note 2 (Share Capital)
        items_note2 = extract_note_2(wb, fy, cma_data)
        print(f'  Note 2: {len(items_note2)} items')
        if items_note2:
            sheets_used.append(f'Note 2 ({len(items_note2)} items)')
        all_items.extend(items_note2)

    # Write output
    output_path = os.path.join(base, 'DOCS/extractions/SR_Papers_classification_ground_truth.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_items, f, indent=2, ensure_ascii=False)

    print(f'\nWritten: {output_path}')
    print(f'  Total items: {len(all_items)}')

    return all_items, cma_data


if __name__ == '__main__':
    all_items, cma_data = main()
