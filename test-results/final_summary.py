"""Generate final MSL classification test summary."""
import json

with open("C:/Users/ASHUTOSH/OneDrive/Desktop/CMA project -2/test-results/MSL_classification_output.json") as f:
    classifications = json.load(f)

with open("C:/Users/ASHUTOSH/OneDrive/Desktop/CMA project -2/test-results/MSL_line_items.json") as f:
    line_items = json.load(f)

item_lookup = {item["id"]: item.get("description") or item.get("source_text", "") for item in line_items}
for clf in classifications:
    clf["_desc"] = item_lookup.get(clf["line_item_id"], "")

# Stats
total = len(classifications)
by_method = {}
for c in classifications:
    m = c["classification_method"]
    by_method[m] = by_method.get(m, 0) + 1

doubts = [c for c in classifications if c["is_doubt"]]
fuzzy = [c for c in classifications if c["classification_method"] == "fuzzy_match" and not c["is_doubt"]]
manual = [c for c in classifications if c["classification_method"] == "manual" and not c["is_doubt"]]
ai_ok = [c for c in classifications if c["classification_method"] == "ai_haiku" and not c["is_doubt"]]

print("=" * 80)
print("MSL CLASSIFICATION TEST - FINAL SUMMARY")
print("=" * 80)
print(f"report_id: c49c1092-9dca-4b71-9cfe-27f19b00f7cc")
print(f"Total classified: {total}")
print()
print(f"Rule matches (Tier 0): 0 — no rule_engine rules fired (classification_method='rule_engine' = 0)")
print(f"  (Note: 'manual' method={by_method.get('manual',0)} items = items that failed AI and were inserted as doubt/manual)")
print(f"Fuzzy matches (Tier 1): {len(fuzzy)} (non-doubt fuzzy_match)")
print(f"AI matches (Tier 2): {len(ai_ok)} (non-doubt ai_haiku)")
print(f"Doubts (Tier 3): {len(doubts)}")
print()

# Key doubts from expected list
key_doubts = [c for c in doubts if (c["_desc"] or "").lower() in [
    "export incentive", "export incentive receivable",
]]
print("Key doubts from expected list:")
for d in key_doubts:
    print(f"  '{d['_desc']}' -> is_doubt=True (CORRECT per spec)")

print()
print("All method counts:", json.dumps(by_method))

# Wrong auto-classifications from analysis
print()
print("WRONG auto-classifications (items that needed correction):")
wrong_list = [
    ("Export Sales", "R22 (Domestic Sales)", "R23 (Export Sales)"),
    ("Bonus", "R71 (S,G&A Exp.)", "R45 (Wages)"),
    ("Statutory Audit Fee", "R0 UNCLASSIFIED", "R73 (Audit Fees)"),
    ("Tax Audit Fee", "R0 UNCLASSIFIED", "R73 (Audit Fees)"),
    ("Rates and Tax", "R0 UNCLASSIFIED", "R68 (Rent Rates Taxes)"),
    ("Repairs and Maintainance", "R0 UNCLASSIFIED", "R50 (R&M Manufacturing)"),
    ("Repairs and Maintenance-Plant & Machinery", "R0 UNCLASSIFIED", "R50 (R&M Manufacturing)"),
    ("Sales Promotion", "R0 UNCLASSIFIED", "R70 (Advertisements Selling)"),
    ("Liability Written Back", "R0 UNCLASSIFIED", "R90 (Sundry Balances)"),
    ("Foreign Exchange Rate", "R34 (Non-op Income)", "R91 (Loss on Exchange)"),
    ("Profit on sale of FA", "R34 (Non-op Income)", "R89 (Loss on Sale FA)"),
    ("Interest Income", "R0 UNCLASSIFIED", "R30 (Interest Received)"),
    ("Insurance", "R0 UNCLASSIFIED", "R71 (Others Admin)"),
    ("Freight Outward", "R0 UNCLASSIFIED", "R70 (Advertisements Selling)"),
    ("Discount Allowed", "R0 UNCLASSIFIED", "R70 (Advertisements Selling)"),
    ("Bad Debts Written Off", "R0 UNCLASSIFIED", "R69 (Bad Debts)"),
    ("Bank Charges", "R83 (Interest)", "R85 (Bank Charges)"),
    ("Job Work Sales - 12%", "R0 UNCLASSIFIED", "R46 (Job Work)"),
    ("(ii) Current maturities of Long Term Borrowings", "R0 UNCLASSIFIED", "R136 (TL in 1 year)"),
    ("Unsecured Loans", "R153 (LT Liab)", "R152 (Quasi Equity)"),
    ("Stock in Trade", "R0 UNCLASSIFIED", "R201 (Finished Goods)"),
    ("Cash-in-hand", "R0 UNCLASSIFIED", "R212 (Cash on Hand)"),
    ("Advance Income Tax", "R99 (Prov Tax)", "R221 (Advance Income Tax)"),
    ("Prepaid Expenses", "R223 (Other CA)", "R222 (Prepaid Expenses)"),
    ("Sundry Creditors", "R0 UNCLASSIFIED", "R242 (Sundry Creditors)"),
    ("TDS Payable", "R0 UNCLASSIFIED", "R246 (Other Statutory Liab)"),
    ("Decrease/(Increase) in trade receivables", "R0 UNCLASSIFIED", "R206 (Domestic Receivables)"),
]
for item, got, exp in wrong_list:
    print(f"  '{item}' | got {got} | expected {exp}")

print(f"\nTotal wrong: {len(wrong_list)}")
print(f"Items approved: 8")
print(f"Items corrected: 27")
