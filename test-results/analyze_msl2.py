"""Search for specific MSL items in extracted line items to understand descriptions."""
import json

with open("C:/Users/ASHUTOSH/OneDrive/Desktop/CMA project -2/test-results/MSL_line_items.json") as f:
    line_items = json.load(f)

# Search fragments we couldn't find
search_terms = [
    "Sale of Products Domestic",
    "Sale of Products Export",
    "Goods Purchased Indigenous",
    "Carriage Inwards",
    "Salaries",
    "PF Contribution",
    "Bank Interest",
    "Other Charges",
    "Power",
    "Stores",
    "R&M Plant",
    "R&M Others",
    "Rates",
    "Audit",
    "Exchange Rate",
    "Tour",
    "Consultancy",
    "General Expenses",
    "P&L on Sale",
    "Liability Written",
    "Paid-up Capital",
    "P&L Balance",
    "Other Reserve",
    "CC IDBI",
    "Current maturities",
    "Unsecured Loans",
    "GST Balance",
    "Advances to Suppliers",
    "Security Deposits",
    "Advance from Customers",
    "Bank Balances",
]

print("Descriptions in extracted items (searching for key terms):")
for term in search_terms:
    matches = [item for item in line_items if term.lower() in (item.get("description") or "").lower()]
    if matches:
        for m in matches[:3]:
            print(f"  FOUND '{term}' -> '{m['description']}' (section: {m.get('section', '')})")
    else:
        print(f"  NOT IN ITEMS: '{term}'")

print()
print("All unique descriptions containing 'sale':")
for item in line_items:
    d = (item.get("description") or "").lower()
    if "sale" in d:
        print(f"  '{item['description']}'")

print()
print("All unique descriptions containing 'salary' or 'wage':")
for item in line_items:
    d = (item.get("description") or "").lower()
    if "salary" in d or "wage" in d or "salaries" in d:
        print(f"  '{item['description']}'")

print()
print("All unique descriptions containing 'power' or 'fuel' or 'coal':")
for item in line_items:
    d = (item.get("description") or "").lower()
    if "power" in d or "fuel" in d or "coal" in d:
        print(f"  '{item['description']}'")

print()
print("All unique descriptions containing 'repair' or 'r&m':")
for item in line_items:
    d = (item.get("description") or "").lower()
    if "repair" in d or "r&m" in d or "maintenance" in d:
        print(f"  '{item['description']}'")
