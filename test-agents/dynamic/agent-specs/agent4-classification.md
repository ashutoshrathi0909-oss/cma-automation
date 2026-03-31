# Agent 4: Classification Quality

## Your Job
Trigger classification for all extracted line items, measure accuracy against the existing CMA ground truth, and identify any improvement rules needed for manufacturing companies.

## Inputs Required from Orchestrator
- REPORT_ID (from Agent 3)
- Path to `test-results/dynamic/dynamic_cma_known_values.json` (from pre-scan Agent P2)

## System State
- Backend: http://localhost:8000
- Auth headers: `X-User-Id: 00000000-0000-0000-0000-000000000001`, `X-User-Role: admin`

## Step 1: Trigger Classification

```bash
curl -s -X POST http://localhost:8000/api/cma-reports/$REPORT_ID/classify \
  -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
  -H "X-User-Role: admin"
```

Poll until complete (classification runs in background via ARQ worker):
```bash
# Poll every 15 seconds
while true; do
  STATUS=$(curl -s http://localhost:8000/api/cma-reports/$REPORT_ID \
    -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
    -H "X-User-Role: admin" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('classification_status', 'unknown'))")
  echo "Classification status: $STATUS"
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then break; fi
  sleep 15
done
```

## Step 2: Fetch Classification Results

```python
import requests, json

BASE = "http://localhost:8000"
HEADERS = {
    "X-User-Id": "00000000-0000-0000-0000-000000000001",
    "X-User-Role": "admin"
}

resp = requests.get(f"{BASE}/api/cma-reports/{REPORT_ID}/line-items", headers=HEADERS)
items = resp.json()

# Categorize by classification tier
tier1 = [i for i in items if i.get("classification_tier") == 1]
tier2 = [i for i in items if i.get("classification_tier") == 2]
tier3 = [i for i in items if i.get("classification_tier") == 3 or i.get("is_doubt")]

total = len(items)
print(f"Total: {total}")
print(f"Tier 1 (fuzzy/learned): {len(tier1)} ({100*len(tier1)/total:.1f}%)")
print(f"Tier 2 (AI Haiku): {len(tier2)} ({100*len(tier2)/total:.1f}%)")
print(f"Tier 3 (doubt): {len(tier3)} ({100*len(tier3)/total:.1f}%)")
```

## Step 3: Manufacturing-Specific Row Validation

Load ground truth values:
```python
with open(r"test-results\dynamic\dynamic_cma_known_values.json") as f:
    known = json.load(f)

key_rows = known.get("key_validation_rows", {})
```

Check that these manufacturing CMA rows are populated (non-zero for at least one year):

| Row | Field | Expected for Manufacturing | Critical |
|-----|-------|--------------------------|---------|
| R22 | Domestic Sales | Must match — primary revenue | ⭐ HIGH |
| R42 | Raw Materials Consumed (Indigenous) | Materials bought for production | ⭐ HIGH |
| R45 | Factory Wages / Direct Wages | Workers on shop floor | ⭐ HIGH |
| R48 | Power, Coal, Fuel and Water | Electricity for machines | ⭐ HIGH |
| R49 | Other Manufacturing Expenses | Misc factory costs | MEDIUM |
| R56 | Depreciation (Manufacturing) | Plant & machinery depreciation | ⭐ HIGH |
| R57 | Depreciation (Non-Manufacturing) | Office equipment depreciation | MEDIUM |
| R67 | Salary and Staff Expenses | Admin/office salaries | HIGH |
| R68 | Rent, Rates and Taxes | Office/factory rent | MEDIUM |
| R70 | Advertisement and Sales Promotions | Marketing costs | LOW |
| R83 | Interest on Fixed Loans / Term Loans | Bank term loan interest | HIGH |
| R85 | Bank Charges | Bank processing fees | LOW |
| R167| Sundry Debtors | Outstanding receivables | HIGH |
| R242| Sundry Creditors | Outstanding payables | HIGH |

For each key row, compare app's classified total vs known value:
```python
def compare_row(row_name, app_value, known_value, year):
    if known_value == 0:
        return "N/A"
    diff_pct = abs(app_value - known_value) / abs(known_value) * 100
    if diff_pct < 1:
        return f"✅ MATCH ({diff_pct:.2f}% diff)"
    elif diff_pct < 10:
        return f"⚠️ CLOSE ({diff_pct:.2f}% diff)"
    else:
        return f"❌ MISMATCH ({diff_pct:.2f}% diff)"
```

## Step 4: Tier Analysis

For manufacturing companies, higher doubt rate is acceptable vs trading:
- Tier 3 doubt rate **target: < 30%** (vs Mehta's target of <15% — manufacturing is more complex)
- If doubt rate > 50%: check if `cma_reference_mappings.cma_input_row` is populated (same root cause as Mehta's 66% doubt rate)

Check the mapping table:
```bash
docker compose exec backend python -c "
import asyncio
from app.dependencies import get_db
# Quick check: how many reference mappings have NULL row numbers
"
```

Or via API if available:
```bash
curl -s http://localhost:8000/api/classification/stats \
  -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
  -H "X-User-Role: admin"
```

## Step 5: Industry-Specific Rules to Generate

Look for patterns in misclassified items and generate improvement rules (same format as Mehta agent5):

```
RULE D-001 [HIGH — Manufacturing]
When: description matches "Power and Fuel" or "Electricity Charges"
Classify as: Power, Coal, Fuel and Water (Row 48)
Confidence: 0.95

RULE D-002 [HIGH — Manufacturing]
When: description matches "Labour Charges" or "Contract Labour" or "Job Work"
Classify as: Factory Wages / Direct Wages (Row 45)
Confidence: 0.90

RULE D-003 [HIGH — Manufacturing]
When: description matches "Raw Material" or "Purchase of Material" or "Input Material"
Classify as: Raw Materials Consumed (Indigenous) (Row 42)
Confidence: 0.95
```

Document any NEW rules discovered that aren't in the above list.

## Output File
Write to `test-results/dynamic/agent4-classification.md`:

```markdown
# Agent 4: Classification Results

## Tier Breakdown
| Tier | Count | % | Target |
|------|-------|---|--------|
| Tier 1 (fuzzy/learned) | N | N% | >30% |
| Tier 2 (AI Haiku) | N | N% | 20-40% |
| Tier 3 (doubt) | N | N% | <30% |

## Manufacturing Row Validation (FY24 — most complete year)
| Row | CMA Field | Known Value | App Value | Match |
|-----|-----------|------------|-----------|-------|
| R22 | Domestic Sales | N | N | ✅/⚠️/❌ |
| R42 | Raw Materials | N | N | ✅/⚠️/❌ |
| R45 | Factory Wages | N | N | ✅/⚠️/❌ |
| R48 | Power/Fuel | N | N | ✅/⚠️/❌ |
| R56 | Depreciation | N | N | ✅/⚠️/❌ |
| R67 | Salary | N | N | ✅/⚠️/❌ |
| R83 | Interest TL | N | N | ✅/⚠️/❌ |

**Overall Accuracy: N/7 key rows matched (N%)**

## Improvement Rules Generated
[List all rules in RULE X-NNN format]

## Doubt Items — Top 10
[List 10 items that went to doubt with explanation of why]
```

## Gate Condition
- PASS if accuracy on key rows ≥ 85% (6/7 or better)
- WARNING if 70-84% (5/7) — note which rows failed
- FAIL if < 70% — stop, investigate classification pipeline
