"""Apply corrections and approve remaining unmatched as unclassified."""
import json
import urllib.request
import os
import sys

TOKEN = sys.argv[1] if len(sys.argv) > 1 else ""
OUTDIR = r'C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2\DOCS\test-results\bcipl\run-2026-04-05-v3'

# Additional mappings for previously unmatched items
EXTRA_MAPPINGS = {
    'opening': None,  # approve as unclassified - section header
    'finished goods': {'row': 198, 'name': 'Indigenous', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    '- other receivables': {'row': 223, 'name': 'Other Advances / current asset', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'advance to suppliers / contractors': {'row': 223, 'name': 'Other Advances / current asset', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'less : provision for income tax': {'row': 95, 'name': 'Income Tax provision', 'broad': 'P&L', 'sheet': 'input_sheet'},
    '(a + b)': None,  # subtotal
    'a+b': None,  # subtotal
    'add : purchases': {'row': 42, 'name': 'Raw Materials Consumed (Indigenous)', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'consumption of stores & spares': {'row': 49, 'name': 'Others', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'at 31st march, 2021': None,  # date header
    'at 31st march, 2020': None,  # date header
    'at 1st april, 2019': None,  # date header
    '- income tax paid [net of refund]': {'row': 95, 'name': 'Income Tax provision', 'broad': 'P&L', 'sheet': 'input_sheet'},
    '- finance costs': {'row': 78, 'name': 'Interest on Fixed Loans / Term loans', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'net increase/(decrease) in cash & cash equivalents': None,  # subtotal
    'tax deducted at source - others': {'row': 223, 'name': 'Other Advances / current asset', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'scraps': {'row': 30, 'name': 'Any Other Operating Income', 'broad': 'Income', 'sheet': 'input_sheet'},
    '- scrap': {'row': 30, 'name': 'Any Other Operating Income', 'broad': 'Income', 'sheet': 'input_sheet'},
    'capital advances': {'row': 223, 'name': 'Other Advances / current asset', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    '- capital advance': {'row': 223, 'name': 'Other Advances / current asset', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'gst input recoverable': {'row': 223, 'name': 'Other Advances / current asset', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'add: g s t paid': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'aluminium': {'row': 198, 'name': 'Indigenous', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'operating profit before changes working capital': None,  # subtotal
    '- indigenous': {'row': 198, 'name': 'Indigenous', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'unsecured considered good': None,  # header
    'raw materials': {'row': 198, 'name': 'Indigenous', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'interest on c.c.  a/c': {'row': 81, 'name': 'Interest on working capital', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'additions': None,  # header
    'disposals': None,  # header
    'reserves & surplus': {'row': 121, 'name': 'General Reserve', 'broad': 'Networth', 'sheet': 'input_sheet'},
    'short-term provisions': {'row': 250, 'name': 'Other current liabilities', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    '- earlier year taxes written off': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    '- unrealised forex rate fluctuation loss /(gain)': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    '- provisions / payables written-back': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    '- provisions': {'row': 250, 'name': 'Other current liabilities', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    'eps & other charges': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'security deposit - ats trainee': {'row': 223, 'name': 'Other Advances / current asset', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'capital wip - others': {'row': 165, 'name': 'Add : Capital Work in Progress', 'broad': 'Fixed Assets', 'sheet': 'input_sheet'},
    'from the date they are due for payment': None,  # header
    'other advances': {'row': 223, 'name': 'Other Advances / current asset', 'broad': 'Current Asset', 'sheet': 'input_sheet'},
    'sales of trading goods': {'row': 22, 'name': 'Domestic Sales', 'broad': 'Income', 'sheet': 'input_sheet'},
    'sale of manufactured goods': {'row': 22, 'name': 'Domestic Sales', 'broad': 'Income', 'sheet': 'input_sheet'},
    'sales of manufactured products': {'row': 22, 'name': 'Domestic Sales', 'broad': 'Income', 'sheet': 'input_sheet'},
    'job work charges - interstate': {'row': 49, 'name': 'Others', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'job work charges - local': {'row': 49, 'name': 'Others', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'job work charges & contract labour': {'row': 49, 'name': 'Others', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'interest income': {'row': 30, 'name': 'Any Other Operating Income', 'broad': 'Income', 'sheet': 'input_sheet'},
    'opening stock of raw materials': {'row': 34, 'name': 'Raw Materials Opening Balance', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'power & fuel': {'row': 49, 'name': 'Others', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'tax audit': {'row': 60, 'name': 'Audit Fees & Directors Remuneration', 'broad': 'Expense', 'sheet': 'input_sheet'},
    's.t. payable': {'row': 250, 'name': 'Other current liabilities', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    'bad debts written back': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'profit after tax (v-vi)': {'row': 97, 'name': 'Net Profit After Tax', 'broad': 'P&L', 'sheet': 'input_sheet'},
    'no. 225657': None,  # reference number, not a line item
    '- purchase/sale of fixed assets': {'row': 165, 'name': 'Add : Capital Work in Progress', 'broad': 'Fixed Assets', 'sheet': 'input_sheet'},
    '- purchase of fixed assets': {'row': 165, 'name': 'Add : Capital Work in Progress', 'broad': 'Fixed Assets', 'sheet': 'input_sheet'},
    'current maturities of long - term debts  [ref. note 5]': {'row': 136, 'name': 'Term Loan Repayable in next one year', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    'tata capital financial services ltd': {'row': 137, 'name': 'Balance Repayable after one year', 'broad': 'Term Liability', 'sheet': 'input_sheet'},
    'amortization expenses': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'machinery': {'row': 161, 'name': 'Gross Block', 'broad': 'Fixed Assets', 'sheet': 'input_sheet'},
    'tangible': {'row': 161, 'name': 'Gross Block', 'broad': 'Fixed Assets', 'sheet': 'input_sheet'},
    'interest on income tax': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'interest on income tax payable': {'row': 250, 'name': 'Other current liabilities', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    'interest of income tax': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'forex rate fluctuation loss (net)': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'forex rate fluctuation gain/(loss)': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'inland lc discounting': {'row': 131, 'name': 'From Indian Bank', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    '- local': None,  # header
    'bill discounting charges': {'row': 85, 'name': 'Bank Charges', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'changes in inventories': {'row': 36, 'name': 'Stock in process Opening Balance', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    '- profit on sale of fixed asset': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'profit on sale of fixed assets': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    '(iii)  2 year to 3 years': None,  # header
    '(v)  2 year to 3 years': None,  # header
    '(iii) 6 months to 1 year': None,  # header
    'exgratia payable': {'row': 250, 'name': 'Other current liabilities', 'broad': 'Current Liability', 'sheet': 'input_sheet'},
    'advacnes written off': {'row': 71, 'name': 'Others', 'broad': 'Expense', 'sheet': 'input_sheet'},
    'raw materials & consumables': {'row': 42, 'name': 'Raw Materials Consumed (Indigenous)', 'broad': 'Manufacturing Expense', 'sheet': 'input_sheet'},
    'duty drawback received': {'row': 30, 'name': 'Any Other Operating Income', 'broad': 'Income', 'sheet': 'input_sheet'},
}

# Load corrections from matching phase
with open(os.path.join(OUTDIR, 'corrections.json')) as f:
    corrections = json.load(f)

# Get remaining doubts to apply extra mappings
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

print("Current remaining doubts: %d" % len(remaining))

# Find which remaining items match corrections.json IDs
correction_ids = set(c['id'] for c in corrections)
extra_corrections = []
approve_unclassified_ids = []
still_unmatched = []

for d in remaining:
    if d['id'] in correction_ids:
        continue  # Already have a correction

    desc_lower = (d.get('line_item_description') or '').strip().lower()

    if desc_lower in EXTRA_MAPPINGS:
        mapping = EXTRA_MAPPINGS[desc_lower]
        if mapping is None:
            approve_unclassified_ids.append(d['id'])
        else:
            extra_corrections.append({
                'id': d['id'],
                'desc': d.get('line_item_description', ''),
                'cma_field_name': mapping['name'],
                'cma_row': mapping['row'],
                'cma_sheet': mapping['sheet'],
                'broad_classification': mapping['broad']
            })
    else:
        still_unmatched.append(d)

all_corrections = corrections + extra_corrections
print("Total corrections to apply: %d" % len(all_corrections))
print("To approve as unclassified: %d" % len(approve_unclassified_ids))
print("Still unmatched: %d" % len(still_unmatched))

# Apply corrections
print("\n--- Applying corrections ---")
success_correct = 0
fail_correct = 0
for i, c in enumerate(all_corrections):
    try:
        body = json.dumps({
            'cma_field_name': c['cma_field_name'],
            'cma_row': c['cma_row'],
            'cma_sheet': c['cma_sheet'],
            'broad_classification': c['broad_classification'],
            'correction_reason': 'Automated correction from reference rules'
        }).encode()
        req = urllib.request.Request(
            'http://localhost:8000/api/classifications/%s/correct' % c['id'],
            data=body,
            headers={
                'Authorization': 'Bearer %s' % TOKEN,
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        with urllib.request.urlopen(req) as resp:
            json.loads(resp.read())
            success_correct += 1
    except Exception as e:
        fail_correct += 1
        if fail_correct <= 3:
            print("  Error correcting %s (%s): %s" % (c['id'], c['desc'][:40], str(e)[:80]))

    if (i + 1) % 50 == 0:
        print("  Progress: %d/%d" % (i + 1, len(all_corrections)))

print("Corrections: %d success, %d failed" % (success_correct, fail_correct))

# Approve unclassified
print("\n--- Approving %d as unclassified ---" % len(approve_unclassified_ids))
success_approve = 0
fail_approve = 0
for cid in approve_unclassified_ids:
    try:
        data = json.dumps({"action": "approve_unclassified"}).encode()
        req = urllib.request.Request(
            'http://localhost:8000/api/classifications/%s/approve' % cid,
            data=data,
            headers={
                'Authorization': 'Bearer %s' % TOKEN,
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        with urllib.request.urlopen(req) as resp:
            json.loads(resp.read())
            success_approve += 1
    except Exception as e:
        fail_approve += 1

print("Approvals: %d success, %d failed" % (success_approve, fail_approve))

# Approve remaining unmatched as unclassified too (to clear all doubts)
print("\n--- Approving %d remaining unmatched as unclassified ---" % len(still_unmatched))
success_remaining = 0
fail_remaining = 0
for d in still_unmatched:
    try:
        data = json.dumps({"action": "approve_unclassified"}).encode()
        req = urllib.request.Request(
            'http://localhost:8000/api/classifications/%s/approve' % d['id'],
            data=data,
            headers={
                'Authorization': 'Bearer %s' % TOKEN,
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        with urllib.request.urlopen(req) as resp:
            json.loads(resp.read())
            success_remaining += 1
    except Exception as e:
        fail_remaining += 1

print("Remaining approvals: %d success, %d failed" % (success_remaining, fail_remaining))

# Save resolution summary
resolution = {
    'corrections_applied': success_correct,
    'corrections_failed': fail_correct,
    'approved_unclassified': success_approve + success_remaining,
    'approved_failed': fail_approve + fail_remaining,
    'still_unmatched_items': [{'desc': d.get('line_item_description',''), 'amount': d.get('line_item_amount',0)} for d in still_unmatched]
}

with open(os.path.join(OUTDIR, 'doubt-resolutions-newpipeline.json'), 'w') as f:
    json.dump(resolution, f, indent=2)

print("\nSaved resolution summary.")
