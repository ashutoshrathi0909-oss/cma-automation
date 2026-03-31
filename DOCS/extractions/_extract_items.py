import json
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("../..")  # Go to project root

files = {
    "FY2020-21": json.load(open("DOCS/extractions/_bcipl_FY2020-21.json", encoding="utf-8")),
    "FY2021-22": json.load(open("DOCS/extractions/_bcipl_FY2021-22.json", encoding="utf-8")),
    "FY2022-23": json.load(open("DOCS/extractions/_bcipl_FY2022-23.json", encoding="utf-8")),
}

SKIP_DESCS = {
    "Amount in", "PARTICULARS", "BAGADIA CHAITRA INDUSTRIES PRIVATE LIMITED",
    "NOTES TO FINANCIAL STATEMENTS  ", "consumption", "         ",
    "% of total ", "Amount", "Gross", "Returns", "Stamping tools",
    "As per tally", "BCIPL  20-21", "BCIPL  21-22", "BCIPL  22-23",
    "[      in 100,000 ]", "Amount in ", "No. of shares", "% of holding",
    "No. of     shares", "Share       holding %", "Number of Shares",
    "Share      holding %", "% ofholding", "%  of Changes",
    "Name of the Share holders ", "Name of the Promoters",
    "Non Current", "Current", "Nos.",
}

SKIP_DATES = {
    "Year ended 31.03.2021", "Year ended 31.03.2022", "Year ended 31.03.2023",
    "Year ended 31.03.2020", "As at 31.03.2021", "As at 31.03.2022",
    "As at 31.03.2023", "As at 31.03.2020", " AS AT 31.03.2021",
    " AS AT 31.03.2022", " AS AT 31.03.2023",
}

SKIP_HEADERS = {
    "STATEMENT OF PROFIT AND LOSS FOR THE YEAR ENDED 31ST MARCH, 2021",
    "STATEMENT OF PROFIT AND LOSS FOR THE YEAR ENDED 31ST MARCH, 2022",
    "STATEMENT OF PROFIT AND LOSS FOR THE YEAR ENDED 31ST MARCH, 2023",
    "[Amount in      ]", "SL. NO.", "SL. \nNO.", "PARTICULARS", "NOTE NO.",
    "INCOME", "EXPENDITURE",
    "BALANCE SHEET AS AT 31ST MARCH, 2021",
    "BALANCE SHEET AS AT 31ST MARCH, 2022",
    "BALANCE SHEET AS AT 31ST MARCH, 2023",
}

ALL_SKIP = SKIP_DESCS | SKIP_DATES | SKIP_HEADERS


def extract_items_from_sheet(data, sheet_key, year, section, multiplier=1):
    items = []
    if sheet_key not in data:
        return items

    rows = data[sheet_key]
    current_note = ""

    for i, row in enumerate(rows):
        if len(row) < 2:
            continue

        # Detect note number headers
        if isinstance(row[0], float) and row[0] > 0 and row[0] == int(row[0]):
            if isinstance(row[1], str) and len(row[1].strip()) > 2:
                current_note = row[1].strip()

        desc = None
        amount = None

        for j, v in enumerate(row):
            if isinstance(v, str) and v.strip() and len(v.strip()) > 1:
                clean = v.strip()
                if desc is None and clean not in ALL_SKIP:
                    desc = clean
            elif isinstance(v, (int, float)) and v != 0:
                if amount is None and abs(v) > 0.5:
                    amount = v * multiplier

        if desc and amount is not None:
            items.append({
                "description": desc,
                "amount": round(amount, 2),
                "section": section,
                "note": current_note,
                "sheet": sheet_key,
                "year": year,
                "row_idx": i,
            })

    return items


def extract_all(data, year, multiplier=1):
    items = []

    # P&L main
    items.extend(extract_items_from_sheet(data, "P & L Ac", year, "P&L (Main)", multiplier))

    # Notes to P&L
    items.extend(extract_items_from_sheet(data, "Notes to P & L", year, "P&L (Notes)", multiplier))

    # Subnotes to PL
    for key in data:
        if "subnote" in key.lower() and "pl" in key.lower():
            items.extend(extract_items_from_sheet(data, key, year, "P&L (Subnotes)", multiplier))

    # BS main
    items.extend(extract_items_from_sheet(data, "BS", year, "BS (Main)", multiplier))

    # Notes BS
    for key in ["Notes BS (1)", "Notes BS (2)"]:
        items.extend(extract_items_from_sheet(data, key, year, "BS (Notes)", multiplier))

    # Subnotes to BS
    for key in data:
        if "subnote" in key.lower() and "bs" in key.lower():
            items.extend(extract_items_from_sheet(data, key, year, "BS (Subnotes)", multiplier))

    # Depreciation schedule
    for key in data:
        if "deprn" in key.lower() or "depn" in key.lower():
            items.extend(extract_items_from_sheet(data, key, year, "Depreciation", multiplier))

    return items


all_items = []
all_items.extend(extract_all(files["FY2020-21"], "FY2020-21", multiplier=1))
all_items.extend(extract_all(files["FY2021-22"], "FY2021-22", multiplier=100000))
all_items.extend(extract_all(files["FY2022-23"], "FY2022-23", multiplier=1))

print(f"Total extracted items: {len(all_items)}")
for yr in ["FY2020-21", "FY2021-22", "FY2022-23"]:
    count = sum(1 for i in all_items if i["year"] == yr)
    print(f"  {yr}: {count} items")

# Save JSON
with open("DOCS/extractions/_all_items.json", "w", encoding="utf-8") as f:
    json.dump(all_items, f, ensure_ascii=False, indent=2)

print("\nSaved to DOCS/extractions/_all_items.json")

# Get unique descriptions across all years
unique_descs = {}
for item in all_items:
    key = (item["description"], item["section"].split(" ")[0])
    if key not in unique_descs:
        unique_descs[key] = []
    unique_descs[key].append(item)

print(f"\nUnique line item descriptions: {len(unique_descs)}")
