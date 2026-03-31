# Output Validation for AI Classification Pipelines

**Research Date:** March 2026
**Context:** CMA Automation System — validating that the 3-tier classification pipeline
(fuzzy → Claude Haiku → doubt) correctly maps extracted line items to CMA field names,
compared against manually labelled ground truth.

---

## 1. The Classification Validation Problem

Our pipeline classifies free-text financial line items (e.g., "Factory Wages & Salaries -
Workers") into one of ~89 CMA field names (e.g., "Wages"). To validate:

- We need labelled examples — the correct CMA field for each extracted line item
- We need to compare the pipeline's output against those labels
- We need to identify which fields are systematically wrong (e.g., the AI always misclassifies
  "Depreciation on Plant" into the wrong depreciation bucket)
- We need to track accuracy across all three tiers separately

This is a **multi-class classification problem** with ~89 classes, evaluated on a
manually-labelled test set.

---

## 2. Ground Truth: How to Get It

### Source 1: The CA-prepared CMA file (indirect ground truth)

`CMA Dynamic 23082025.xls` tells us what values should appear in each CMA row for each year.
If we know which extracted line items were used to build those rows (from the CA's original
working), we have indirect ground truth.

**Limitation:** The CMA file tells us the aggregate total per row, not which individual line
items were classified there. Two line items summing to the correct total could each be wrong.

### Source 2: Manual labelling of extracted items (direct ground truth)

The best ground truth is a human reviewing each extracted line item and labelling it with the
correct CMA field name. For the Dynamic Air Engineering test:

```python
# test-results/dynamic/dynamic_classification_labels.json
# Structure: [{"raw_text": str, "amount": float, "year": int, "correct_field": str}]

LABELLED_EXAMPLES = [
    {
        "raw_text": "Factory Wages & Salaries - Workers",
        "amount": 45.23,
        "year": 2024,
        "correct_field": "Wages"
    },
    {
        "raw_text": "Power & Fuel - Electricity Units",
        "amount": 12.80,
        "year": 2024,
        "correct_field": "Power, Coal, Fuel and Water"
    },
    {
        "raw_text": "Depreciation on Plant & Machinery",
        "amount": 22.00,
        "year": 2024,
        "correct_field": "Depreciation (Manufacturing)"
    },
]
```

### Source 3: The existing CMA file as row-level aggregation check

Even without item-level labels, we can check: does the sum of our classified amounts in row 45
(Wages) match the CA's value in row 45? This is the "aggregation accuracy" check done in
Agent 5. It is the most practical ground truth for a production validation.

---

## 3. Metrics for Classification Accuracy

### 3.1 Top-1 Accuracy (exact match)

The most basic metric: did the pipeline pick the exactly correct CMA field?

```python
def top1_accuracy(predictions: list[str], labels: list[str]) -> float:
    """Fraction of items where predicted field exactly matches label."""
    if not labels:
        return 0.0
    correct = sum(p == l for p, l in zip(predictions, labels))
    return round(correct / len(labels) * 100, 1)
```

**Example:** 73 out of 100 items classified correctly → 73.0%

### 3.2 Tier-weighted accuracy

Our pipeline has three tiers. Report accuracy separately per tier:

```python
from collections import defaultdict

def tier_accuracy_report(results: list[dict]) -> dict:
    """
    results: list of {
        "tier": "fuzzy" | "ai" | "doubt",
        "predicted": str | None,   # None for doubt items
        "label": str
    }
    """
    by_tier = defaultdict(list)
    for r in results:
        by_tier[r["tier"]].append(r)

    report = {}
    for tier, items in by_tier.items():
        if tier == "doubt":
            # Doubt items are not classified — always "wrong" from accuracy perspective
            report[tier] = {
                "count": len(items),
                "pct_of_total": round(len(items) / len(results) * 100, 1),
                "note": "Doubt items require human review — not counted in accuracy"
            }
        else:
            correct = sum(1 for i in items if i["predicted"] == i["label"])
            report[tier] = {
                "count": len(items),
                "pct_of_total": round(len(items) / len(results) * 100, 1),
                "accuracy": round(correct / len(items) * 100, 1) if items else 0.0,
            }
    return report
```

**Example output:**

```
Tier Breakdown:
  fuzzy  : 42 items (42%) — accuracy 94.2%
  ai     : 35 items (35%) — accuracy 77.1%
  doubt  : 23 items (23%) — requires human review
  ──────────────────────────────────────────
  Non-doubt accuracy: 86.8%  (71 correct out of 77 classified)
  Doubt rate        : 23.0%
```

### 3.3 Doubt rate

The doubt rate is the fraction of items the pipeline could not classify:

```python
def doubt_rate(results: list[dict]) -> float:
    doubts = sum(1 for r in results if r["tier"] == "doubt")
    return round(doubts / len(results) * 100, 1)
```

For manufacturing companies, 20-30% doubt rate is acceptable (per test design spec §4 Agent 4).
For trading companies, <15% is the target.

### 3.4 Aggregation accuracy (row-level, no item labels needed)

Compare the sum of classified amounts per CMA row against the ground-truth CMA value:

```python
def aggregation_accuracy(
    classified_items: list[dict],   # [{cma_field_name, amount, year}]
    ground_truth: dict[tuple, float],  # {(field_name, year): expected_amount}
    rtol: float = 0.01,
) -> dict:
    from collections import defaultdict

    # Aggregate our classified amounts
    actual_sums = defaultdict(float)
    for item in classified_items:
        if item.get("cma_field_name") and not item.get("is_doubt"):
            key = (item["cma_field_name"], item["financial_year"])
            actual_sums[key] += item["amount"]

    rows_compared = 0
    rows_matched = 0
    failures = []

    for (field, year), expected in ground_truth.items():
        if expected is None or expected == 0:
            continue
        actual = actual_sums.get((field, year), 0.0)
        rows_compared += 1
        pct_error = abs(actual - expected) / abs(expected)
        if pct_error <= rtol:
            rows_matched += 1
        else:
            failures.append({
                "field": field, "year": year,
                "expected": expected, "actual": actual,
                "pct_error": round(pct_error * 100, 1),
            })

    return {
        "rows_compared": rows_compared,
        "rows_matched": rows_matched,
        "accuracy_pct": round(rows_matched / rows_compared * 100, 1) if rows_compared else 0.0,
        "failures": sorted(failures, key=lambda x: -x["pct_error"]),
    }
```

---

## 4. Confusion Matrix for Classification

A confusion matrix shows which CMA fields are confused with each other. For 89 classes, a
full 89×89 matrix is hard to read. Instead, show only the most common misclassifications:

```python
from collections import Counter

def top_misclassifications(
    results: list[dict],
    top_n: int = 10,
) -> list[dict]:
    """
    results: list of {"predicted": str, "label": str}
    Returns the top-N most common prediction errors.
    """
    errors = Counter()
    for r in results:
        if r["predicted"] != r["label"] and r.get("tier") != "doubt":
            errors[(r["label"], r["predicted"])] += 1

    return [
        {
            "correct_field": label,
            "predicted_as": predicted,
            "count": count,
            "note": _misclassification_note(label, predicted),
        }
        for (label, predicted), count in errors.most_common(top_n)
    ]


def _misclassification_note(correct: str, predicted: str) -> str:
    """Human-readable note about why this confusion is likely."""
    known_confusions = {
        ("Depreciation (Manufacturing)", "Depreciation (CMA)"): "Both depreciation fields — check Manufacturing vs CMA section",
        ("Wages", "Salary and staff expenses"): "Factory wages vs office salaries — check cost centre context",
        ("Raw Materials Consumed (Indigenous)", "Stores and spares consumed (Indigenous)"): "Similar items — check if stores or raw material",
        ("Interest on Fixed Loans / Term loans", "Bank Charges"): "Both financial costs — check if interest or charges",
    }
    return known_confusions.get((correct, predicted), "")
```

**Example output:**

```
Top Misclassifications:
  1. "Depreciation (Manufacturing)" → classified as "Depreciation (CMA)"      [8 items]
     Note: Both depreciation fields — check Manufacturing vs CMA section
  2. "Wages" → classified as "Salary and staff expenses"                        [5 items]
     Note: Factory wages vs office salaries — check cost centre context
  3. "Others (Manufacturing)" → classified as "Others (Admin)"                 [3 items]
```

---

## 5. Identifying Systemic Errors

Systemic errors are patterns where the AI consistently misclassifies a specific field,
suggesting the prompt, reference data, or fuzzy matcher needs updating.

### Detection

```python
def systemic_errors(
    results: list[dict],
    error_threshold: float = 0.5,  # field misclassified >50% of the time
) -> list[dict]:
    """Identify fields where the error rate is above threshold."""
    from collections import defaultdict

    by_field = defaultdict(lambda: {"total": 0, "wrong": 0})
    for r in results:
        if r.get("tier") == "doubt":
            continue
        by_field[r["label"]]["total"] += 1
        if r["predicted"] != r["label"]:
            by_field[r["label"]]["wrong"] += 1

    systemic = []
    for field, counts in by_field.items():
        if counts["total"] >= 3:  # need at least 3 samples
            error_rate = counts["wrong"] / counts["total"]
            if error_rate >= error_threshold:
                systemic.append({
                    "field": field,
                    "error_rate": round(error_rate * 100, 1),
                    "total_items": counts["total"],
                    "wrong_items": counts["wrong"],
                    "action": _recommend_action(field, error_rate),
                })

    return sorted(systemic, key=lambda x: -x["error_rate"])


def _recommend_action(field: str, error_rate: float) -> str:
    if error_rate >= 0.8:
        return "Add explicit examples to reference_mappings.json for this field"
    elif error_rate >= 0.5:
        return "Review fuzzy matcher threshold; consider adding learned_mappings entry"
    return "Monitor — borderline, may resolve with more data"
```

### Common systemic error patterns in Indian CMA data

Based on the project's classification reference (`DOCS/CMA classification.xls` — 384 items):

| Field confused | Common cause | Fix |
|---------------|-------------|-----|
| `Depreciation (Manufacturing)` vs `Depreciation (CMA)` | Two separate depreciation rows in CMA template | Add "manufacturing" keyword rule to rule_engine |
| `Wages` vs `Salary and staff expenses` | "Salaries & Wages" in source is ambiguous | Split by cost centre (factory=wages, office=salary) |
| `Raw Materials Consumed (Indigenous)` vs `Stores and spares` | Indian financials lump raw materials and stores | Check Notes to Accounts for breakdown |
| `Others (Manufacturing)` vs `Others (Admin)` | Generic "other expenses" lines | Context clue: appears in manufacturing section → Manufacturing |
| `Interest on Fixed Loans / Term loans` vs `Bank Charges` | Bank interest mixed with bank charges in notes | Amount clue: interest >> bank charges |

---

## 6. Classification Report Format

```python
def generate_classification_report(
    results: list[dict],
    ground_truth_row_sums: dict[tuple, float],
    classified_items: list[dict],
    output_path: str,
) -> None:
    """Write full classification accuracy report to markdown file."""

    top1 = top1_accuracy(
        [r["predicted"] for r in results if r.get("tier") != "doubt"],
        [r["label"] for r in results if r.get("tier") != "doubt"],
    )
    tier_report = tier_accuracy_report(results)
    doubt = doubt_rate(results)
    misclassifications = top_misclassifications(results, top_n=10)
    systemic = systemic_errors(results)
    agg = aggregation_accuracy(classified_items, ground_truth_row_sums)

    lines = [
        "# Classification Accuracy Report",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total items classified (non-doubt) | {sum(1 for r in results if r.get('tier') != 'doubt')} |",
        f"| Doubt rate | {doubt:.1f}% |",
        f"| Top-1 accuracy (non-doubt) | {top1:.1f}% |",
        f"| Row-level aggregation accuracy | {agg['accuracy_pct']:.1f}% |",
        "",
        "## Tier Breakdown",
        "",
        "| Tier | Count | % of Total | Accuracy |",
        "|------|-------|-----------|---------|",
    ]
    for tier, data in tier_report.items():
        acc = f"{data.get('accuracy', '—')}%" if "accuracy" in data else "N/A (doubt)"
        lines.append(f"| {tier} | {data['count']} | {data['pct_of_total']}% | {acc} |")

    lines += [
        "",
        "## Top Misclassifications",
        "",
        "| Correct Field | Predicted As | Count |",
        "|--------------|-------------|-------|",
    ]
    for m in misclassifications:
        note = f" _{m['note']}_" if m["note"] else ""
        lines.append(f"| {m['correct_field']} | {m['predicted_as']} | {m['count']} |{note}")

    if systemic:
        lines += [
            "",
            "## Systemic Errors (Action Required)",
            "",
            "| Field | Error Rate | Action |",
            "|-------|-----------|--------|",
        ]
        for s in systemic:
            lines.append(f"| {s['field']} | {s['error_rate']}% | {s['action']} |")

    lines += [
        "",
        "## Row-Level Aggregation Failures",
        "",
        "| CMA Field | Year | Expected | Actual | % Error |",
        "|-----------|------|----------|--------|---------|",
    ]
    for f in agg["failures"][:20]:  # top 20 worst
        lines.append(
            f"| {f['field']} | FY{f['year']} | {f['expected']:,.2f} | "
            f"{f['actual']:,.2f} | {f['pct_error']:.1f}% |"
        )

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
```

---

## 7. Industry Benchmark: What Good Looks Like

Based on similar NLP classification projects for structured financial data:

| Metric | Poor | Acceptable | Good | Excellent |
|--------|------|-----------|------|-----------|
| Top-1 accuracy (classified items) | <60% | 60-75% | 75-90% | >90% |
| Doubt rate | >40% | 20-40% | 10-20% | <10% |
| Row aggregation accuracy | <70% | 70-80% | 80-90% | >90% |
| Systemic errors | >5 fields | 3-5 fields | 1-3 fields | 0 fields |

**Our targets (from test design spec):**
- Tier 1 (fuzzy/learned): >30% of items
- Tier 2 (AI Haiku): 20-40% of items
- Tier 3 (doubt): <30% (manufacturing) / <15% (trading)
- Classification accuracy: ≥85% against known CMA values

---

## 8. Improving the Classifier Based on Report Findings

When the report identifies a systemic error, here is the remediation path:

### Step 1: Identify the root cause

```
Systemic error: "Depreciation (Manufacturing)" → misclassified as "Depreciation (CMA)"
Error rate: 75% (6 out of 8 items)
```

Root cause options:
- (a) Fuzzy matcher score for both candidates is similar — the wrong one scores slightly higher
- (b) AI prompt does not distinguish the two depreciation fields well
- (c) Reference mapping lacks examples for "Depreciation (Manufacturing)"

### Step 2: Add to `learned_mappings` (highest priority — checked first)

```python
# In classification pipeline — learned_mappings checked BEFORE reference_mappings
LEARNED_MAPPINGS = {
    "Depreciation on Plant and Machinery": "Depreciation (Manufacturing)",
    "Depreciation on Factory Building": "Depreciation (Manufacturing)",
    "Depreciation as per Companies Act": "Depreciation (CMA)",
}
```

### Step 3: Add classification rules to `rule_engine.py`

```python
# Rule: if description contains "plant" or "machinery" → Manufacturing depreciation
CLASSIFICATION_RULES = [
    {
        "keywords": ["plant", "machinery", "equipment", "tools"],
        "field": "Depreciation (Manufacturing)",
        "confidence": 0.85,
    },
    {
        "keywords": ["companies act", "as per act", "as applicable"],
        "field": "Depreciation (CMA)",
        "confidence": 0.75,
    },
]
```

### Step 4: Improve AI prompt

Add explicit disambiguation examples to the Haiku prompt for the confused pair. The prompt
should include: "When you see depreciation on plant or machinery, use 'Depreciation
(Manufacturing)', not 'Depreciation (CMA)'. The CMA row is only used for Companies Act
depreciation calculations in the P&L."

---

## 9. Pytest Integration for Classification Accuracy

```python
# tests/test_classification_accuracy.py

import json
import pytest
from pathlib import Path

LABELS_FILE = Path("test-results/dynamic/dynamic_classification_labels.json")
RESULTS_FILE = Path("test-results/dynamic/agent4-classification.json")
DOUBT_THRESHOLD = 30.0      # % — fail if doubt rate exceeds this
ACCURACY_THRESHOLD = 85.0   # % — fail if non-doubt accuracy drops below this

@pytest.mark.skipif(not LABELS_FILE.exists(), reason="Labels file not created yet")
@pytest.mark.skipif(not RESULTS_FILE.exists(), reason="Classification results not available")
def test_classification_accuracy():
    labels = json.loads(LABELS_FILE.read_text())
    results = json.loads(RESULTS_FILE.read_text())

    # Build label lookup by item_id
    label_map = {item["item_id"]: item["correct_field"] for item in labels}
    classified = [r for r in results if r["tier"] != "doubt"]
    non_doubt_with_labels = [
        r for r in classified if r["item_id"] in label_map
    ]

    # Accuracy
    correct = sum(
        1 for r in non_doubt_with_labels
        if r["predicted"] == label_map[r["item_id"]]
    )
    accuracy = correct / len(non_doubt_with_labels) * 100 if non_doubt_with_labels else 0

    # Doubt rate
    doubt_count = sum(1 for r in results if r["tier"] == "doubt")
    dr = doubt_count / len(results) * 100 if results else 0

    assert dr <= DOUBT_THRESHOLD, (
        f"Doubt rate {dr:.1f}% exceeds threshold {DOUBT_THRESHOLD}%"
    )
    assert accuracy >= ACCURACY_THRESHOLD, (
        f"Classification accuracy {accuracy:.1f}% below threshold {ACCURACY_THRESHOLD}%"
    )
```

---

## Recommended for Our Project

1. **Primary metric:** Row-level aggregation accuracy (compare classified sums vs CA's CMA
   values). This is the most practical metric because it does not require item-level labels.
   Target: ≥85% of key rows within 1%.

2. **Secondary metric:** Doubt rate per tier. Track separately for fuzzy, AI, and doubt tiers.
   Manufacturing target: doubt rate <30%. Trading target: <15%.

3. **Systemic error detection:** After the first full test run (Dynamic Air Engineering), run
   `systemic_errors()` on any labelled subset. Fields with >50% error rate get immediately
   added to `learned_mappings` or `rule_engine.py`.

4. **Report integration:** Agent 4 in the Dynamic test should produce a JSON file
   (`agent4-classification.json`) containing per-item results (tier, field assigned, amount).
   Agent 7 then compares this against `dynamic_cma_known_values.json` to compute aggregation
   accuracy without needing item-level manual labels.

5. **Improvement loop:** After each test run, promote correctly classified items with low fuzzy
   scores into `learned_mappings`. This continuously lowers the doubt rate without new
   Haiku API calls. The learning system in `learning_system.py` already supports this — the
   classification report feeds back into it.
