"""Match remaining doubts to CMA reference rules and build corrections."""
import json
import urllib.request
import os
import sys

TOKEN = sys.argv[1] if len(sys.argv) > 1 else ""
OUTDIR = r'C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2\DOCS\test-results\bcipl\run-2026-04-05-v3'

# Load reference rules
ref_path = r'C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2\CMA_Ground_Truth_v1\reference\cma_classification_rules.json'
with open(ref_path) as f:
    ref_data = json.load(f)
rules = ref_data['rules']

def normalize(s):
    return s.lower().strip().replace('&', 'and').replace('-', ' ').replace('  ', ' ')

rule_lookup = {}
for r in rules:
    key = normalize(r.get('fs_item', ''))
    if key not in rule_lookup:
        rule_lookup[key] = r

# Get remaining doubts
docs = {
    '8abbd713-e9ff-47c9-b004-d4fd3f7121ca': 'FY2021',
    'ae7a05a1-a6ef-4135-8097-0dd87529def8': 'FY2022',
    '2754473d-a725-4193-92ad-999c2399aa0d': 'FY2023'
}

remaining = []
for doc_id, label in docs.items():
    req = urllib.request.Request(
        'http://localhost:8000/api/documents/%s/doubts' % doc_id,
        headers={'Authorization': 'Bearer %s' % TOKEN}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        for d in data:
            d['_doc_label'] = label
        remaining.extend(data)

print("Remaining doubts to resolve: %d" % len(remaining))

# Manual mappings for common items
MANUAL_MAPPINGS = {
    'long-term borrowings': {'row': 137, 'name': 'Balance Repayable after one year', 'broad': 'Term Liability', 'sheet': 'input_sheet'},
    'long term borrowings': {'row': 137, 'name': 'Balance Repayable after one year', 'broad': 'Term Liability', 'sheet': 'input_sheet'},
    'deferred tax liabilities (net)': {'row': 159, 'name': 'Deferred tax liability', 'broad': 'Term Liability', 'sheet': 'input_sheet'},
    'deferred tax liabilities / (assets) (net)': {'row': 159, 'name': 'Deferred tax liability', 'broad': 'Term Liability', 'sheet': 'input_sheet'},
    'closing balance - deferred tax liabilities/(assets)': {'row': 159, 'name': 'Deferred tax liability', 'broad': 'Term Liability', 'sheet': 'input_sheet'},
    'opening balance - deferred tax liability': {'row': 159, 'name': 'Deferred tax liability', 'broad': 'Term Liability', 'sheet': 'input_sheet'},
    'opening balance - deferred tax liabilities/(assets)': {'row': 159, 'name': 'Deferred tax liability', 'broad': 'Term Liability', 'sheet': 'input_sheet'},
    'short-term borrowings': {'row': 131, 'name': 'From Indian Bank', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    'short term borrowings': {'row': 131, 'name': 'From Indian Bank', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    'trade payables': {'row': 234, 'name': 'Creditors for purchase of raw material & stores', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    'dues to micro, small and medium enterprises': {'row': 234, 'name': 'Creditors for purchase of raw material & stores', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    'dues to micro, small & medium enterprises': {'row': 234, 'name': 'Creditors for purchase of raw material & stores', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    'dues to other than micro, small and medium enterprises': {'row': 234, 'name': 'Creditors for purchase of raw material & stores', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    'dues to other than micro, small & medium enterprises': {'row': 234, 'name': 'Creditors for purchase of raw material & stores', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    'gross revenue from operations': {'row': 22, 'name': 'Domestic Sales', 'broad': 'Income', 'sheet': 'input_sheet'},
    'revenue from operations': {'row': 22, 'name': 'Domestic Sales', 'broad': 'Income', 'sheet': 'input_sheet'},
    'profit after tax': {'row': 97, 'name': 'Net Profit After Tax', 'broad': 'P&L', 'sheet': 'input_sheet'},
    'profit before tax': {'row': 93, 'name': 'Profit before tax', 'broad': 'P&L', 'sheet': 'input_sheet'},
    'profit before tax (iii-iv)': {'row': 93, 'name': 'Profit before tax', 'broad': 'P&L', 'sheet': 'input_sheet'},
    'depreciation and amortization': {'row': 71, 'name': 'Depreciation', 'broad': 'Expense', 'sheet': 'input_sheet'},
    '- depreciation & amortization': {'row': 71, 'name': 'Depreciation', 'broad': 'Expense', 'sheet': 'input_sheet'},
    '-profit on sale of fixed asset': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'profit on sale of fixed asset': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    '- bad debts written off': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'bad debts written off': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    '- inventories': {'row': 198, 'name': 'Indigenous', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    '- trade payables': {'row': 234, 'name': 'Creditors for purchase of raw material & stores', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    '- trade receivables': {'row': 206, 'name': 'Domestic Receivables', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    '- capital work in progress': {'row': 165, 'name': 'Add : Capital Work in Progress', 'broad': 'Fixed Assets', 'sheet': 'input_sheet'},
    'equity shares': {'row': 116, 'name': 'Issued, Subscribed and Paid up', 'broad': 'Networth', 'sheet': 'input_sheet'},
    'current maturities of long - term debts  [ref. note 3]': {'row': 136, 'name': 'Term Loan Repayable in next one year', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    'current maturities of long-term debts': {'row': 136, 'name': 'Term Loan Repayable in next one year', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    'current maturities of long - term debts': {'row': 136, 'name': 'Term Loan Repayable in next one year', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    'profession tax': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'unpaid salary': {'row': 250, 'name': 'Other current liabilities', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    'advance from customers': {'row': 250, 'name': 'Other current liabilities', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    'provision for income tax': {'row': 95, 'name': 'Income Tax provision', 'broad': 'P&L', 'sheet': 'input_sheet'},
    'gst paid': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'tds - others': {'row': 223, 'name': 'Other Advances / current asset', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'tds others': {'row': 223, 'name': 'Other Advances / current asset', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'interest on c.c. a/c': {'row': 81, 'name': 'Interest on working capital', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'security deposits': {'row': 223, 'name': 'Other Advances / current asset', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'other income': {'row': 30, 'name': 'Any Other Operating Income', 'broad': 'Income', 'sheet': 'input_sheet'},
    'export sales': {'row': 24, 'name': 'Export Sales', 'broad': 'Income', 'sheet': 'input_sheet'},
    'employee benefit expense': {'row': 45, 'name': 'Wages', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'other expenses': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'finance costs': {'row': 78, 'name': 'Interest on Fixed Loans / Term loans', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'interest expense': {'row': 78, 'name': 'Interest on Fixed Loans / Term loans', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'tangible assets': {'row': 161, 'name': 'Gross Block', 'broad': 'Fixed Assets', 'sheet': 'input_sheet'},
    '(i) property, plant and equipment': {'row': 161, 'name': 'Gross Block', 'broad': 'Fixed Assets', 'sheet': 'input_sheet'},
    'trade receivables': {'row': 206, 'name': 'Domestic Receivables', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'cash and bank balances': {'row': 215, 'name': 'Bank Balances', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'cash and cash equivalents': {'row': 214, 'name': 'Cash on Hand', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'cash and cash equivalent at the beginning of the year': {'row': 214, 'name': 'Cash on Hand', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'cash and cash equivalent  at the end of the year': {'row': 214, 'name': 'Cash on Hand', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'reserves and surplus': {'row': 121, 'name': 'General Reserve', 'broad': 'Networth', 'sheet': 'input_sheet'},
    'creditors for capital goods': {'row': 247, 'name': 'Creditors for capital goods', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    'income tax  provision': {'row': 95, 'name': 'Income Tax provision', 'broad': 'P&L', 'sheet': 'input_sheet'},
    'income tax provision': {'row': 95, 'name': 'Income Tax provision', 'broad': 'P&L', 'sheet': 'input_sheet'},
    'share capital': {'row': 116, 'name': 'Issued, Subscribed and Paid up', 'broad': 'Networth', 'sheet': 'input_sheet'},
    'deferred tax asset': {'row': 155, 'name': 'Deferred Tax Asset', 'broad': 'Fixed Assets', 'sheet': 'input_sheet'},
    'gst receivable': {'row': 223, 'name': 'Other Advances / current asset', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'interest received': {'row': 30, 'name': 'Any Other Operating Income', 'broad': 'Income', 'sheet': 'input_sheet'},
    '- interest received': {'row': 30, 'name': 'Any Other Operating Income', 'broad': 'Income', 'sheet': 'input_sheet'},
    'interest on term loan': {'row': 78, 'name': 'Interest on Fixed Loans / Term loans', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'raw materials consumed': {'row': 42, 'name': 'Raw Materials Consumed (Indigenous)', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'cost of raw materials consumed': {'row': 42, 'name': 'Raw Materials Consumed (Indigenous)', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'power and fuel': {'row': 49, 'name': 'Others', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'deferred tax liability': {'row': 159, 'name': 'Deferred tax liability', 'broad': 'Term Liability', 'sheet': 'input_sheet'},
    'aluminium billets': {'row': 198, 'name': 'Indigenous', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'aluminium dross': {'row': 198, 'name': 'Indigenous', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    't. payable': {'row': 234, 'name': 'Creditors for purchase of raw material & stores', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    'staff welfare expenses': {'row': 45, 'name': 'Wages', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'repairs and maintenance': {'row': 54, 'name': 'Repairs and Maintenance', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'provision for gratuity': {'row': 45, 'name': 'Wages', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'travelling and conveyance': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'sundry balance written off': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'stores and spare parts consumed': {'row': 49, 'name': 'Others', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'other current liabilities': {'row': 250, 'name': 'Other current liabilities', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    '- other current liabilities': {'row': 250, 'name': 'Other current liabilities', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    'statutory dues': {'row': 250, 'name': 'Other current liabilities', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    'total income (i+ii)': {'row': 0, 'name': 'SKIP', 'broad': 'SKIP', 'sheet': 'input_sheet'},
    'total revenue': {'row': 0, 'name': 'SKIP', 'broad': 'SKIP', 'sheet': 'input_sheet'},
    'total': {'row': 0, 'name': 'SKIP', 'broad': 'SKIP', 'sheet': 'input_sheet'},
    'unrealised forex exchange gain / (loss)': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'provisions written-back': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'taxes written off': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'crca sheets & coils': {'row': 198, 'name': 'Indigenous', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'gi sheets & coils': {'row': 198, 'name': 'Indigenous', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'hrca sheets & coils': {'row': 198, 'name': 'Indigenous', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'gi & crca coils': {'row': 198, 'name': 'Indigenous', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'aluminium wire rods': {'row': 198, 'name': 'Indigenous', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'hr sheets & coils': {'row': 198, 'name': 'Indigenous', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'ms plates & beams': {'row': 198, 'name': 'Indigenous', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'color coated sheets & coils': {'row': 198, 'name': 'Indigenous', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'other materials consumed': {'row': 49, 'name': 'Others', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'short-term loans and advances': {'row': 223, 'name': 'Other Advances / current asset', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'inventories': {'row': 198, 'name': 'Indigenous', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'other non- current assets': {'row': 238, 'name': 'Other non current assets', 'broad': 'Fixed Assets', 'sheet': 'input_sheet'},
    'other non-current assets': {'row': 238, 'name': 'Other non current assets', 'broad': 'Fixed Assets', 'sheet': 'input_sheet'},
    'capital work-in-progress': {'row': 165, 'name': 'Add : Capital Work in Progress', 'broad': 'Fixed Assets', 'sheet': 'input_sheet'},
    '(iii) capital work-in-progress': {'row': 165, 'name': 'Add : Capital Work in Progress', 'broad': 'Fixed Assets', 'sheet': 'input_sheet'},
    '(ii) intangible assets': {'row': 172, 'name': 'Other Intangible assets', 'broad': 'Fixed Assets', 'sheet': 'input_sheet'},
    'intangible assets': {'row': 172, 'name': 'Other Intangible assets', 'broad': 'Fixed Assets', 'sheet': 'input_sheet'},
    'manufacturing expenses': {'row': 71, 'name': 'Others', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'consultation  fees': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'consultation fees': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'administrative & general expenses': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'administrative and general expenses': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'bonus': {'row': 45, 'name': 'Wages', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'tax deducted at source - salary': {'row': 45, 'name': 'Wages', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'salary & wages': {'row': 45, 'name': 'Wages', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'salary and wages': {'row': 45, 'name': 'Wages', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'earlier year tax': {'row': 49, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    '- book and tax depreciation on wdv': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    '- provision for bonus': {'row': 45, 'name': 'Wages', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'audit fees & directors remuneration': {'row': 60, 'name': 'Audit Fees & Directors Remuneration', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'rent, rates and taxes': {'row': 57, 'name': 'Rent, Rates and Taxes', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'rent , rates and taxes': {'row': 57, 'name': 'Rent, Rates and Taxes', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'freight and transportation charges': {'row': 63, 'name': 'Freight and Transportation Charges', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'bank charges': {'row': 85, 'name': 'Bank Charges', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'insurance': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'depreciation': {'row': 71, 'name': 'Depreciation', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'stock in process opening balance': {'row': 36, 'name': 'Stock in process Opening Balance', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'finished goods closing balance': {'row': 39, 'name': 'Finished Goods Closing Balance', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'finished goods opening balance': {'row': 38, 'name': 'Finished Goods Opening Balance', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'less accumulated depreciation': {'row': 163, 'name': 'Less Accumulated Depreciation', 'broad': 'Fixed Assets', 'sheet': 'input_sheet'},
    'gross block': {'row': 161, 'name': 'Gross Block', 'broad': 'Fixed Assets', 'sheet': 'input_sheet'},
    'cash on hand': {'row': 214, 'name': 'Cash on Hand', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'bank balances': {'row': 215, 'name': 'Bank Balances', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'other advances / current asset': {'row': 223, 'name': 'Other Advances / current asset', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'creditors for expenses': {'row': 248, 'name': 'Creditors for Expenses', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    'salary and staff expenses': {'row': 45, 'name': 'Wages', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
}

matched = 0
unmatched = 0
unmatched_items = []
skip_items = []
corrections = []

for d in remaining:
    desc = (d.get('line_item_description') or '').strip()
    desc_lower = desc.lower().strip()

    mapping = None
    # Try exact match in manual mappings
    if desc_lower in MANUAL_MAPPINGS:
        mapping = MANUAL_MAPPINGS[desc_lower]
    # Try reference rules
    elif normalize(desc) in rule_lookup:
        r = rule_lookup[normalize(desc)]
        mapping = {
            'row': r['canonical_sheet_row'],
            'name': r['canonical_name'],
            'broad': r['broad_classification'],
            'sheet': 'input_sheet'
        }

    if mapping:
        if mapping.get('name') == 'SKIP':
            skip_items.append(d['id'])
        else:
            matched += 1
            corrections.append({
                'id': d['id'],
                'desc': desc,
                'cma_field_name': mapping['name'],
                'cma_row': mapping['row'],
                'cma_sheet': mapping['sheet'],
                'broad_classification': mapping['broad']
            })
    else:
        unmatched += 1
        unmatched_items.append(desc)

print("Matched (can correct): %d" % matched)
print("Skip (subtotals): %d" % len(skip_items))
print("Unmatched (will approve as unclassified): %d" % unmatched)

# Save corrections for application
with open(os.path.join(OUTDIR, 'corrections.json'), 'w') as f:
    json.dump(corrections, f, indent=2)

with open(os.path.join(OUTDIR, 'skip_ids.json'), 'w') as f:
    json.dump(skip_items, f)

# Show unmatched items
from collections import Counter
unmatched_counter = Counter(unmatched_items)
print("\nUnmatched items (%d unique):" % len(unmatched_counter))
for item, count in unmatched_counter.most_common():
    print("  [%dx] %s" % (count, item[:80]))
