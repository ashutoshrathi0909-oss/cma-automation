"""Detailed analysis of MSL classification - what was classified correctly vs wrong."""
import json

with open("C:/Users/ASHUTOSH/OneDrive/Desktop/CMA project -2/test-results/MSL_classification_output.json") as f:
    classifications = json.load(f)

with open("C:/Users/ASHUTOSH/OneDrive/Desktop/CMA project -2/test-results/MSL_line_items.json") as f:
    line_items = json.load(f)

# Build lookup: line_item_id -> description
item_lookup = {item["id"]: item["description"] for item in line_items}

# Attach descriptions to classifications
for clf in classifications:
    clf["_desc"] = item_lookup.get(clf["line_item_id"], "")

# Fuzzy matches (non-doubt)
fuzzy = [c for c in classifications if c["classification_method"] == "fuzzy_match" and not c["is_doubt"]]
manual = [c for c in classifications if c["classification_method"] == "manual" and not c["is_doubt"]]
ai = [c for c in classifications if c["classification_method"] == "ai_haiku" and not c["is_doubt"]]
doubts = [c for c in classifications if c["is_doubt"]]

print(f"Total: {len(classifications)}")
print(f"Fuzzy (non-doubt): {len(fuzzy)}")
print(f"Manual (non-doubt): {len(manual)}")
print(f"AI (non-doubt): {len(ai)}")
print(f"Doubts total: {len(doubts)}")
print()

print("=" * 80)
print(f"FUZZY MATCHES ({len(fuzzy)}):")
print("=" * 80)
for c in sorted(fuzzy, key=lambda x: x["cma_row"]):
    print(f"  R{c['cma_row']:03d} | {c['cma_field_name'][:40]:<40} | '{c['_desc']}'")

print()
print("=" * 80)
print(f"MANUAL MATCHES ({len(manual)}):")
print("=" * 80)
for c in sorted(manual, key=lambda x: x["cma_row"]):
    print(f"  R{c['cma_row']:03d} | {c['cma_field_name'][:40]:<40} | '{c['_desc']}'")

print()
print("=" * 80)
print(f"AI MATCHES ({len(ai)}):")
print("=" * 80)
for c in sorted(ai, key=lambda x: x["cma_row"]):
    print(f"  R{c['cma_row']:03d} | {c['cma_field_name'][:40]:<40} | '{c['_desc']}'")

# Now map against expected items using actual descriptions
print()
print("=" * 80)
print("EXPECTED ITEMS - MATCHING AGAINST ACTUAL DESCRIPTIONS:")
print("=" * 80)

# Build lookup: desc -> classification
desc_to_clf = {}
for clf in classifications:
    desc = clf["_desc"].lower().strip()
    if desc not in desc_to_clf:
        desc_to_clf[desc] = clf

def find_best(desc_fragment):
    frag = desc_fragment.lower()
    for d, c in desc_to_clf.items():
        if frag == d:
            return c, "exact"
    for d, c in desc_to_clf.items():
        if frag in d:
            return c, "contains"
    return None, None

# Expected PL items with corrected actual descriptions
pl_expected = [
    # (actual_desc_fragment, expected_row, expected_field)
    ("export sales", 23, "Export Sales"),
    ("local sales accounts", 22, "Domestic Sales"),
    ("salary & wages", 45, "Wages"),
    ("bonus", 45, "Wages"),
    ("power & fuel", 48, "Power Coal Fuel"),
    ("statutory audit fee", 73, "Audit Fees"),
    ("tax audit fee", 73, "Audit Fees"),
    ("rates and tax", 68, "Rent Rates Taxes"),
    ("consultancy  charges", 71, "Others Admin"),
    ("repairs and maintainance", 50, "R&M Manufacturing"),
    ("repairs and maintenance-plant", 50, "R&M Manufacturing"),
    ("sales promotion", 70, "Advertisements Selling"),
    ("liability written back", 90, "Sundry Balances"),
    ("foreign exchange rate", 91, "Loss on Exchange"),
    ("profit on sale of fa", 89, "Loss on Sale FA"),
    ("interest income", 30, "Interest Received"),
    ("export incentive", None, None),  # expected doubt
    ("insurance", 71, "Others Admin"),
    ("freight outward", 70, "Advertisements Selling"),
    ("discount allowed", 70, "Advertisements Selling"),
    ("bad debts", 69, "Bad Debts"),
    ("bank charges", 85, "Bank Charges"),
    ("job work", 46, "Job Work"),
]

bs_expected = [
    ("general reserve", 121, "General Reserve"),
    ("share premium", 123, "Share Premium"),
    ("provision for taxation", 244, "Provision for Taxation"),
    ("current maturities of long term", 136, "TL in 1 year"),
    ("unsecured loans", 152, "Quasi Equity"),
    ("stock in trade", 201, "Finished Goods"),
    ("cash in hand", 212, "Cash on Hand"),
    ("cash-in-hand", 212, "Cash on Hand"),
    ("advance income tax", 221, "Advance Income Tax"),
    ("prepaid expenses", 222, "Prepaid Expenses"),
    ("sundry creditors", 242, "Sundry Creditors"),
    ("tds payable", 246, "Other Statutory Liab"),
    ("trade receivable", 206, "Domestic Receivables"),
]

report_id = "c49c1092-9dca-4b71-9cfe-27f19b00f7cc"

correct = []
wrong = []
not_found = []

all_expected = [("PL", *x) for x in pl_expected] + [("BS", *x) for x in bs_expected]

for sheet, frag, exp_row, exp_field in all_expected:
    clf, match_type = find_best(frag)
    if clf is None:
        not_found.append(frag)
        print(f"  NOT_FOUND  [{sheet}] '{frag}'")
        continue

    got_row = clf["cma_row"]
    got_field = clf["cma_field_name"]
    is_doubt = clf["is_doubt"]
    clf_id = clf["id"]

    if exp_row is None:  # expected doubt
        if is_doubt:
            print(f"  OK(DOUBT)  [{sheet}] '{clf['_desc']}' -> is_doubt=True")
            correct.append({"id": clf_id, "action": "approve"})
        else:
            print(f"  WRONG      [{sheet}] '{clf['_desc']}' should be doubt, got R{got_row} {got_field}")
            wrong.append({"id": clf_id, "desc": clf["_desc"], "got_row": got_row, "exp_row": None})
    elif got_row == exp_row:
        print(f"  OK         [{sheet}] R{got_row:03d} '{clf['_desc']}' -> {got_field} (method={clf['classification_method']})")
        correct.append({"id": clf_id, "action": "approve"})
    else:
        print(f"  WRONG      [{sheet}] '{clf['_desc']}' got R{got_row}({got_field}) | exp R{exp_row}({exp_field}) | is_doubt={is_doubt} method={clf['classification_method']}")
        wrong.append({"id": clf_id, "desc": clf["_desc"], "got_row": got_row, "exp_row": exp_row, "exp_field": exp_field, "broad": clf.get("broad_classification"), "sheet": clf.get("cma_sheet")})

print()
print(f"Correct: {len(correct)}, Wrong: {len(wrong)}, Not found: {len(not_found)}")
print()

print("WRONG ITEMS for correction:")
for w in wrong:
    print(f"  {w}")

# Save actions
with open("C:/Users/ASHUTOSH/OneDrive/Desktop/CMA project -2/test-results/MSL_actions2.json", "w") as f:
    json.dump({"correct": correct, "wrong": wrong, "report_id": report_id}, f, indent=2)
