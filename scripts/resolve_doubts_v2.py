"""Batch resolve doubts for BCIPL CMA v2 E2E test."""
import json
import sys
import requests

TOKEN = sys.argv[1]
BASE = "http://localhost:8000/api"
REPORT_ID = "7f82a84b-6945-46a8-9f44-8d41f36dc5c0"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# Fetch all doubts
resp = requests.get(f"{BASE}/cma-reports/{REPORT_ID}/classifications", headers=HEADERS)
data = resp.json()
doubts = [d for d in data if d.get("status") == "needs_review"]
print(f"Total doubts to resolve: {len(doubts)}")

# ── CA Domain Knowledge Correction Rules ──
CORRECTIONS = {
    "Sale of Manufactured Goods": {"field": "Sale of Products", "row": 22, "broad": "income", "reason": "Domestic sales of manufactured goods"},
    "Sale of Duty Credit Scrips": {"field": "Other Income", "row": 32, "broad": "income", "reason": "Duty credit scrips are other income"},
    "CRCA Sheets & Coils": {"field": "Raw Materials Consumed", "row": 42, "broad": "manufacturing_expenses", "reason": "Primary raw material for manufacturing"},
    "Aluminium": {"field": "Raw Materials Consumed", "row": 42, "broad": "manufacturing_expenses", "reason": "Raw material"},
    "Raw Materials & Consumables": {"field": "Raw Materials Consumed", "row": 42, "broad": "manufacturing_expenses", "reason": "Raw materials consumed"},
    "Labour Welfare Expenses": {"field": "Wages (Manufacturing)", "row": 45, "broad": "manufacturing_expenses", "reason": "Factory labour welfare"},
    "Manufacturing Expenses": {"field": "Other Manufacturing Expenses", "row": 53, "broad": "manufacturing_expenses", "reason": "General manufacturing expenses"},
    "Amortization Expenses": {"field": "Depreciation (General Admin)", "row": 63, "broad": "general_admin_expenses", "reason": "Amortization of intangible assets"},
    "Consultation  Fees": {"field": "Other Admin Expenses", "row": 71, "broad": "general_admin_expenses", "reason": "Professional/consultation fees"},
    "Interest on Late payment of TDS": {"field": "Interest on WC", "row": 84, "broad": "interest", "reason": "Interest penalty"},
    "Interest on C.C.  A/c": {"field": "Interest on WC", "row": 84, "broad": "interest", "reason": "Cash credit interest is working capital interest"},
    "Advacnes Written off": {"field": "Other Admin Expenses", "row": 71, "broad": "general_admin_expenses", "reason": "Advances written off"},
}

# Patterns that mean UNCLASSIFIED (approve as-is)
UNCLASSIFIED_PATTERNS = [
    "Reserves & Surplus", "Long-term Borrowings", "Short-term Borrowings",
    "Trade Payables", "Other Current Liabilities", "Short-term Provisions",
    "cash flow", "Cash and Cash Equivalent", "Net increase/(decrease)",
    "- Trade Receivables", "- Loans and Advances", "- Other Current",
    "- Trade Payables", "- Provisions", "- Purchase", "- Increase",
    "- Other Receivables", "- Earlier Year", "- Provisions / Payable",
    "- Purchase/Sale", "- Other Current/ Non-Current",
    "Equity Shares", "Outstanding at the Beginning", "Balance at the beginning",
    "Axis Term Loan", "Axis Bank", "Vechicle Loan", "Yes Bank",
    "TATA Capital", "Kotak Mahindra",
    "Mr. Chaitra", "Mrs. Ronak", "Mrs. Ashwini", "Mr. Nishanth",
    "Dues to Micro", "Dues to other than Micro",
    "S.T. Payable", "Unpaid Salary",
    "A+B", "(A + B)", "Tangible", "Unsecured Considered Good",
    "Other Bank Balances", "Balance With Bank", "3 months but less than",
    "Other Advances", "Capital Advances",
    "At 1st April", "At 31st March", "Additions", "Disposals", "For the Year",
    "No. 225657", "(i) Principal amount", "(iii) 6 months",
    "Gross Revenue", "Revenue from operations", "Total Revenue",
    "Intangible Assets", "Opening Stock of Raw Materials", "Add : Purchases",
    "Add: G S T Paid", "(Less): G S T Paid", "Add: Credit Availed",
    "- Local", "Less: Credit Notes", "- Scrap",
    "Exgratia Payable", "Scraps",
    "Current Liabilities",
]

resolutions = []
approve_ids = []
correct_items = []

for d in doubts:
    desc = d["line_item_description"]
    section = d.get("line_item_section", "")
    clf_id = d["id"]

    if desc in CORRECTIONS:
        corr = CORRECTIONS[desc]
        correct_items.append({
            "id": clf_id, "desc": desc,
            "cma_field_name": corr["field"],
            "cma_row": corr["row"],
            "broad_classification": corr["broad"],
            "reason": corr["reason"]
        })
        resolutions.append({
            "id": clf_id, "desc": desc, "action": "correct",
            "target": f"Row {corr['row']}: {corr['field']}",
            "reason": corr["reason"]
        })
        continue

    matched = False
    for pattern in UNCLASSIFIED_PATTERNS:
        if pattern.lower() in desc.lower():
            approve_ids.append(clf_id)
            resolutions.append({
                "id": clf_id, "desc": desc, "action": "approve_unclassified",
                "reason": f"Pattern: {pattern}"
            })
            matched = True
            break

    if not matched:
        # Default for remaining notes/cashflow/tangible/header items
        approve_ids.append(clf_id)
        resolutions.append({
            "id": clf_id, "desc": desc, "action": "approve_unclassified",
            "reason": f"Section-based default: {section}"
        })

print(f"Approvals (UNCLASSIFIED): {len(approve_ids)}")
print(f"Corrections: {len(correct_items)}")

# Save resolutions
with open("DOCS/test-results/bcipl/run-2026-04-04-v2/doubt-resolutions.json", "w") as f:
    json.dump(resolutions, f, indent=2)
print("Resolutions saved to doubt-resolutions.json")

# Execute approvals
approved_count = 0
for clf_id in approve_ids:
    resp = requests.post(
        f"{BASE}/classifications/{clf_id}/approve",
        headers=HEADERS,
        json={"note": "E2E v2 - UNCLASSIFIED (subtotal/breakdown/cash flow)", "cma_report_id": REPORT_ID}
    )
    if resp.status_code == 200:
        approved_count += 1
    else:
        print(f"  WARN: approve {clf_id[:8]} failed: {resp.status_code}")

print(f"\nApproved: {approved_count}/{len(approve_ids)}")

# Execute corrections
corrected_count = 0
for item in correct_items:
    resp = requests.post(
        f"{BASE}/classifications/{item['id']}/correct",
        headers=HEADERS,
        json={
            "cma_field_name": item["cma_field_name"],
            "cma_row": item["cma_row"],
            "cma_sheet": "input_sheet",
            "broad_classification": item["broad_classification"],
            "correction_reason": item["reason"],
            "cma_report_id": REPORT_ID
        }
    )
    if resp.status_code == 200:
        corrected_count += 1
        print(f"  Corrected: {item['desc'][:40]} -> Row {item['cma_row']}: {item['cma_field_name']}")
    else:
        print(f"  WARN: correct {item['id'][:8]} failed: {resp.status_code} {resp.text[:100]}")

print(f"\nCorrected: {corrected_count}/{len(correct_items)}")
print(f"\nTotal resolved: {approved_count + corrected_count}/{len(doubts)}")
