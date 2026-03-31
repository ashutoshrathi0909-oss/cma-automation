"""Analyze MSL classification results against expected mapping."""
import json

# Load data
with open("C:/Users/ASHUTOSH/OneDrive/Desktop/CMA project -2/test-results/MSL_classification_output.json") as f:
    classifications = json.load(f)

with open("C:/Users/ASHUTOSH/OneDrive/Desktop/CMA project -2/test-results/MSL_line_items.json") as f:
    line_items = json.load(f)

# Build lookup: line_item_id -> description
item_lookup = {item["id"]: item["description"] for item in line_items}

# Attach descriptions to classifications
for clf in classifications:
    clf["_desc"] = item_lookup.get(clf["line_item_id"], "")

# Summary stats
total = len(classifications)
doubts = [c for c in classifications if c["is_doubt"]]
by_method = {}
for c in classifications:
    m = c["classification_method"]
    by_method[m] = by_method.get(m, 0) + 1

print(f"Total classified: {total}")
print(f"By method: {json.dumps(by_method, indent=2)}")
print(f"Doubts: {len(doubts)}")
print()

# Expected mappings - (source_text_fragment, expected_row, expected_field, expected_method)
expected_pl = [
    ("Sale of Products Domestic", 22, "Domestic Sales", "fuzzy"),
    ("Sale of Products Export", 23, "Export Sales", "fuzzy"),
    ("Interest Income", 30, "Interest Received", "fuzzy"),
    ("Export Incentive", None, None, "doubt"),  # should be doubt
    ("Insurance Claim Received", 34, "Others Non-Op", "rule"),
    ("Goods Purchased Indigenous", 42, "RM Indigenous", "fuzzy"),
    ("Carriage Inwards", 47, "Freight & Transport", "rule"),
    ("Salaries and Wages", 45, "Wages", "fuzzy"),
    ("Bonus", 45, "Wages", "fuzzy"),
    ("PF Contribution", 45, "Wages", "fuzzy"),
    ("Staff Welfare", 45, "Wages", "fuzzy"),
    ("Bank Charges", 85, "Bank Charges", "fuzzy"),
    ("Bank Interest CC", 84, "Interest on WC", "fuzzy"),
    ("Other Charges", 83, "Interest on TL", "ai"),
    ("Power Coal Fuel", 48, "Power Coal Fuel", "fuzzy"),
    ("Stores and Spares", 44, "Stores & Spares", "fuzzy"),
    ("Job Work Charges", 46, "Job Work", "rule"),
    ("Rent", 68, "Rent Rates Taxes", "fuzzy"),
    ("R&M Plant", 50, "R&M Manufacturing", "rule"),
    ("R&M Others", 50, "R&M Manufacturing", "rule"),
    ("Insurance", 71, "Others Admin", "rule"),
    ("Rates & Taxes", 68, "Rent Rates Taxes", "fuzzy"),
    ("Audit Fees", 73, "Audit Fees", "fuzzy"),
    ("Freight Outward", 70, "Advertisements Selling", "rule"),
    ("Discount Allowed", 70, "Advertisements Selling", "rule"),
    ("Bad Debts Written Off", 69, "Bad Debts", "fuzzy"),
    ("Exchange Rate Fluctuation", 91, "Loss on Exchange", "fuzzy"),
    ("Sales Promotion", 70, "Advertisements Selling", "rule"),
    ("Tour & Travel", 71, "Others Admin", "rule"),
    ("Consultancy Fees", 71, "Others Admin", "rule"),
    ("General Expenses", 71, "Others Admin", "rule"),
    ("P&L on Sale of FA", 89, "Loss on Sale FA", "fuzzy"),
    ("Liability Written Off", 90, "Sundry Balances", "rule"),
]

expected_bs = [
    ("Paid-up Capital", 116, "Share Capital"),
    ("General Reserve", 121, "General Reserve"),
    ("Share Premium", 123, "Share Premium"),
    ("P&L Balance", 122, "Balance from P&L"),
    ("Other Reserve", 125, "Other Reserve"),
    ("CC IDBI Working Capital", 131, "WC Bank Finance"),
    ("Current maturities TL", 136, "TL in 1 year"),
    ("Unsecured Loans Promoters", 152, "Quasi Equity"),
    ("Provision for Gratuity", 153, "LT Unsecured Debt"),
    ("Stock in Trade", 201, "Finished Goods"),
    ("Trade Receivables", 206, "Domestic Receivables"),
    ("Cash on Hand", 212, "Cash on Hand"),
    ("Bank Balances", 213, "Bank Balances"),
    ("GST Balance", 219, "Advances recoverable"),
    ("Advances to Suppliers", 220, "Advances to Suppliers RM"),
    ("Advance Income Tax", 221, "Advance Income Tax"),
    ("Prepaid Expenses", 222, "Prepaid Expenses"),
    ("Security Deposits", 237, "Security Deposits Govt"),
    ("Sundry Creditors", 242, "Sundry Creditors"),
    ("Advance from Customers", 243, "Advance from Customers"),
    ("Provision for Taxation", 244, "Provision for Taxation"),
    ("TDS Payable", 246, "Other Statutory Liab"),
]

def find_clf_by_desc(classifications, desc_fragment):
    """Find best matching classification by description fragment."""
    fragment_lower = desc_fragment.lower()
    matches = []
    for c in classifications:
        d = (c["_desc"] or "").lower()
        if fragment_lower in d:
            matches.append(c)
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        # Return shortest match (most specific)
        matches.sort(key=lambda x: len(x["_desc"] or ""))
        return matches[0]
    return None

print("=" * 80)
print("P&L ITEMS ANALYSIS")
print("=" * 80)

correct_count = 0
wrong_count = 0
doubt_correct = 0
not_found = 0
wrong_items = []
approved_items = []  # (classification_id, is_correct)

for frag, exp_row, exp_field, exp_method in expected_pl:
    clf = find_clf_by_desc(classifications, frag)
    if clf is None:
        print(f"  NOT FOUND: '{frag}'")
        not_found += 1
        continue

    desc = clf["_desc"]
    got_row = clf["cma_row"]
    got_field = clf["cma_field_name"]
    got_method = clf["classification_method"]
    is_doubt = clf["is_doubt"]

    if exp_row is None:  # Expected to be doubt
        if is_doubt:
            print(f"  OK (DOUBT)  '{desc}' -> is_doubt=True (correct)")
            doubt_correct += 1
            correct_count += 1
            approved_items.append((clf["id"], True, None, None, None, None))
        else:
            print(f"  WRONG      '{desc}' -> NOT flagged as doubt! got row={got_row} field={got_field}")
            wrong_count += 1
            wrong_items.append((desc, got_row, None, clf["id"]))
    else:
        if got_row == exp_row:
            print(f"  OK         '{desc}' row={got_row} field={got_field} method={got_method}")
            correct_count += 1
            approved_items.append((clf["id"], True, None, None, None, None))
        else:
            print(f"  WRONG      '{desc}' got row={got_row} field={got_field} | expected row={exp_row} field={exp_field}")
            wrong_count += 1
            wrong_items.append((desc, got_row, exp_row, clf["id"], exp_field, is_doubt))
            approved_items.append((clf["id"], False, exp_row, exp_field, clf["cma_sheet"], clf["broad_classification"]))

print()
print("=" * 80)
print("BS ITEMS ANALYSIS")
print("=" * 80)

for frag, exp_row, exp_field in expected_bs:
    clf = find_clf_by_desc(classifications, frag)
    if clf is None:
        print(f"  NOT FOUND: '{frag}'")
        not_found += 1
        continue

    desc = clf["_desc"]
    got_row = clf["cma_row"]
    got_field = clf["cma_field_name"]
    got_method = clf["classification_method"]

    if got_row == exp_row:
        print(f"  OK         '{desc}' row={got_row} field={got_field} method={got_method}")
        correct_count += 1
        approved_items.append((clf["id"], True, None, None, None, None))
    else:
        print(f"  WRONG      '{desc}' got row={got_row} field={got_field} | expected row={exp_row} field={exp_field}")
        wrong_count += 1
        wrong_items.append((desc, got_row, exp_row, clf["id"], exp_field, False))
        approved_items.append((clf["id"], False, exp_row, exp_field, clf["cma_sheet"], clf["broad_classification"]))

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Correct: {correct_count}")
print(f"Wrong:   {wrong_count}")
print(f"Not found: {not_found}")

print()
print("WRONG ITEMS:")
for item in wrong_items:
    print(f"  {item}")

print()
print("DOUBT ITEMS (all):")
for d in doubts:
    desc = d["_desc"]
    print(f"  '{desc}' -> {d['doubt_reason']}")

# Write actions to JSON for the next step
actions = {"report_id": "c49c1092-9dca-4b71-9cfe-27f19b00f7cc", "items": approved_items}
with open("C:/Users/ASHUTOSH/OneDrive/Desktop/CMA project -2/test-results/MSL_actions.json", "w") as f:
    json.dump(actions, f)

print()
print("Method breakdown:")
for m, cnt in sorted(by_method.items()):
    print(f"  {m}: {cnt}")
