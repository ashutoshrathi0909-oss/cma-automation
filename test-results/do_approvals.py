"""Execute approve and correct API calls for MSL classification review."""
import json
import subprocess
import time

REPORT_ID = "c49c1092-9dca-4b71-9cfe-27f19b00f7cc"
BASE_URL = "http://localhost:8000"
AUTH = "Authorization: Bearer dev-bypass"

def api_call(method, url, data=None):
    cmd = ["curl", "-s", "-X", method, url, "-H", AUTH]
    if data:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(data)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except:
        return {"error": result.stdout, "stderr": result.stderr}

# Items to APPROVE (correct row matched)
approve_ids = [
    # desc, clf_id
    ("Local Sales Accounts -> R22 Domestic Sales", "NEED_ID"),
    ("Salary & Wages -> R45 Wages", "NEED_ID"),
    ("Power & Fuel -> R48 Power Coal Fuel", "NEED_ID"),
    ("Consultancy Charges -> R71 Others Admin", "NEED_ID"),
    ("Export Incentive -> DOUBT correct", "NEED_ID"),
    ("General Reserve -> R121", "NEED_ID"),
    ("Share Premium -> R123", "NEED_ID"),
    ("Provision for Taxation -> R244", "NEED_ID"),
]

# Load actions from analysis
with open("C:/Users/ASHUTOSH/OneDrive/Desktop/CMA project -2/test-results/MSL_actions2.json") as f:
    actions = json.load(f)

correct_items = actions["correct"]
wrong_items = actions["wrong"]

print(f"Items to approve: {len(correct_items)}")
print(f"Items to correct: {len(wrong_items)}")

approved_count = 0
corrected_count = 0
errors = []

# Step 1: Approve correct items
print("\n=== APPROVALS ===")
for item in correct_items:
    clf_id = item["id"]
    resp = api_call("POST", f"{BASE_URL}/api/classifications/{clf_id}/approve", {
        "cma_report_id": REPORT_ID,
        "note": "Verified vs MSL ground truth"
    })
    if "id" in resp or "status" in resp:
        print(f"  OK approve {clf_id[:8]}... -> {resp.get('cma_field_name','?')}")
        approved_count += 1
    else:
        print(f"  ERR approve {clf_id[:8]}...: {resp}")
        errors.append(f"approve {clf_id}: {resp}")

# Step 2: Correct wrong items
print("\n=== CORRECTIONS ===")
# Broad classification mapping
broad_map = {
    "Gross Sales": "Gross Sales",
    "Manufacturing Expenses": "Manufacturing Expenses",
    "Selling, Gen. & Adm. Exp.": "Selling, Gen. & Adm. Exp.",
    "Non-operating Income": "Non-operating Income",
    "Interest": "Interest",
    "Tax": "Tax",
    "Current Assets": "Current Assets",
    "Term Liability": "Term Liability",
    None: None,
}

# Expected row -> broad classification mapping
row_to_broad = {
    22: "Gross Sales",
    23: "Gross Sales",
    30: "Non-operating Income",
    34: "Non-operating Income",
    45: "Manufacturing Expenses",
    46: "Manufacturing Expenses",
    47: "Manufacturing Expenses",
    48: "Manufacturing Expenses",
    50: "Manufacturing Expenses",
    68: "Selling, Gen. & Adm. Exp.",
    69: "Selling, Gen. & Adm. Exp.",
    70: "Selling, Gen. & Adm. Exp.",
    71: "Selling, Gen. & Adm. Exp.",
    73: "Selling, Gen. & Adm. Exp.",
    83: "Interest",
    84: "Interest",
    85: "Interest",
    89: "Non-operating Income",
    90: "Non-operating Income",
    91: "Non-operating Income",
    116: "Capital",
    121: "Capital",
    122: "Capital",
    123: "Capital",
    125: "Capital",
    131: "Working Capital",
    136: "Term Liability",
    152: "Term Liability",
    153: "Term Liability",
    162: "Fixed Assets",
    169: "Fixed Assets",
    201: "Current Assets",
    206: "Current Assets",
    212: "Current Assets",
    213: "Current Assets",
    219: "Current Assets",
    220: "Current Assets",
    221: "Current Assets",
    222: "Current Assets",
    223: "Current Assets",
    237: "Current Assets",
    242: "Current Liabilities",
    243: "Current Liabilities",
    244: "Current Liabilities",
    246: "Current Liabilities",
    250: "Current Liabilities",
}

# Process corrections (bounded to first 100)
MAX_CORRECTIONS = 100
done = 0
for item in wrong_items[:MAX_CORRECTIONS]:
    clf_id = item["id"]
    exp_row = item["exp_row"]
    exp_field = item.get("exp_field", "UNKNOWN")
    broad = row_to_broad.get(exp_row, item.get("broad"))
    sheet = item.get("sheet", "input_sheet") or "input_sheet"
    desc = item.get("desc", "")

    if exp_row is None:
        print(f"  SKIP (no exp_row): {desc}")
        continue

    resp = api_call("POST", f"{BASE_URL}/api/classifications/{clf_id}/correct", {
        "cma_report_id": REPORT_ID,
        "cma_field_name": exp_field,
        "cma_row": exp_row,
        "cma_sheet": sheet,
        "broad_classification": broad,
        "note": f"Corrected per MSL ground truth: {exp_field} (R{exp_row})"
    })

    if "id" in resp or "status" in resp:
        print(f"  OK correct '{desc}' -> R{exp_row} {exp_field}")
        corrected_count += 1
        done += 1
    else:
        print(f"  ERR correct '{desc}': {resp}")
        errors.append(f"correct {clf_id}: {resp}")

print(f"\n=== SUMMARY ===")
print(f"Approved: {approved_count}")
print(f"Corrected: {corrected_count}")
print(f"Errors: {len(errors)}")
for e in errors:
    print(f"  {e}")
