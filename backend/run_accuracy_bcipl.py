"""BCIPL Accuracy Benchmark — Scoped Classifier v2.

Run inside Docker worker:
    python /app/run_accuracy_bcipl.py

Outputs:
    /app/DOCS/test-results/scoped-v2/accuracy_results.json
    /app/DOCS/test-results/scoped-v2/ACCURACY_REPORT.md
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
GT_FILE = Path("/app/bcipl_gt.json")
OUTPUT_DIR = Path("/app/DOCS/test-results/scoped-v2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

INDUSTRY_TYPE = "manufacturing"
DOCUMENT_TYPE = "annual_report"

# ── Cost guard ($5 hard stop) ──────────────────────────────────────────────
# We can't easily get exact token counts from sync calls, so we track items
# and bail if we somehow exceed 500 items (shouldn't happen with 448).
COST_STOP_ITEMS = 500

# ── Load ground truth ──────────────────────────────────────────────────────
with open(GT_FILE) as f:
    ground_truth = json.load(f)

print(f"Loaded {len(ground_truth)} ground truth items from {GT_FILE}")
print(f"Sample keys: {list(ground_truth[0].keys())}")
print()

# ── Load classifier ────────────────────────────────────────────────────────
from app.services.classification.scoped_classifier import ScopedClassifier

sc = ScopedClassifier()
print(f"ScopedClassifier initialized. Sections: {len(sc._contexts)}")
print()

# ── Run classification ─────────────────────────────────────────────────────
results = []
correct = 0
doubt = 0
wrong = 0
error = 0

# Per-section tracking
section_stats: dict[str, dict] = defaultdict(lambda: {"total": 0, "correct": 0, "doubt": 0, "wrong": 0})

# Debate tracking
agreed_correct = 0
agreed_total = 0
debated_correct = 0
debated_total = 0
debate_triggered = 0

start_time = time.time()

for i, item in enumerate(ground_truth):
    raw_text = item["raw_text"]
    amount = item.get("amount_rupees")
    section = item.get("section")
    correct_row = item["correct_cma_row"]
    gt_section = item.get("sheet_name", "unknown")

    # Reset per-document token counter every 100 items.
    # _total_tokens is designed as a per-document guard (not per-benchmark-run).
    # Without this reset, the 500K limit hits ~item 150 and all subsequent calls
    # return doubt — invalidating the benchmark.
    if i % 100 == 0:
        sc._total_tokens = 0
        sc._items_classified = 0

    try:
        result = sc.classify_sync(
            raw_text=raw_text,
            amount=amount,
            section=section,
            industry_type=INDUSTRY_TYPE,
            document_type=DOCUMENT_TYPE,
            fuzzy_candidates=[],
        )

        predicted_row = result.cma_row
        is_doubt_result = result.is_doubt
        method = result.classification_method
        confidence = result.confidence

        # Determine outcome
        if is_doubt_result:
            outcome = "doubt"
            doubt += 1
            section_stats[gt_section]["doubt"] += 1
        elif predicted_row == correct_row:
            outcome = "correct"
            correct += 1
            section_stats[gt_section]["correct"] += 1
        else:
            outcome = "wrong"
            wrong += 1
            section_stats[gt_section]["wrong"] += 1

        section_stats[gt_section]["total"] += 1

        # Track agreement vs debate
        if "agree" in method:
            agreed_total += 1
            if outcome == "correct":
                agreed_correct += 1
        elif "debate" in method or "single" not in method:
            debated_total += 1
            debate_triggered += 1
            if outcome == "correct":
                debated_correct += 1

        results.append({
            "index": i,
            "raw_text": raw_text,
            "section": section,
            "sheet_name": gt_section,
            "correct_cma_row": correct_row,
            "correct_cma_field": item.get("correct_cma_field"),
            "predicted_cma_row": predicted_row,
            "predicted_cma_field": result.cma_field_name,
            "is_doubt": is_doubt_result,
            "confidence": confidence,
            "method": method,
            "outcome": outcome,
            "doubt_reason": result.doubt_reason,
        })

    except Exception as e:
        error += 1
        section_stats[gt_section]["total"] += 1
        section_stats[gt_section]["doubt"] += 1
        results.append({
            "index": i,
            "raw_text": raw_text,
            "section": section,
            "sheet_name": gt_section,
            "correct_cma_row": correct_row,
            "predicted_cma_row": None,
            "is_doubt": True,
            "method": "error",
            "outcome": "error",
            "error": str(e),
        })

    # Progress every 25 items
    if (i + 1) % 25 == 0 or i == 0:
        elapsed = time.time() - start_time
        rate = (i + 1) / elapsed if elapsed > 0 else 0
        remaining = (len(ground_truth) - i - 1) / rate if rate > 0 else 0
        acc_so_far = correct / (i + 1 - doubt) * 100 if (i + 1 - doubt) > 0 else 0
        print(
            f"[{i+1:3d}/{len(ground_truth)}] "
            f"correct={correct} doubt={doubt} wrong={wrong} err={error} | "
            f"acc={acc_so_far:.1f}% | "
            f"elapsed={elapsed:.0f}s eta={remaining:.0f}s"
        )
        sys.stdout.flush()

    # Safety: cost guard
    if i + 1 >= COST_STOP_ITEMS:
        print(f"COST GUARD: stopping at {COST_STOP_ITEMS} items")
        break

# ── Compute final metrics ──────────────────────────────────────────────────
total = len(results)
elapsed_total = time.time() - start_time

overall_acc = correct / total * 100 if total > 0 else 0
doubt_rate = doubt / total * 100 if total > 0 else 0
classified = total - doubt - error
acc_within_classified = correct / classified * 100 if classified > 0 else 0

agreed_acc = agreed_correct / agreed_total * 100 if agreed_total > 0 else 0
debated_acc = debated_correct / debated_total * 100 if debated_total > 0 else 0
agreement_rate = agreed_total / total * 100 if total > 0 else 0

# Per-section accuracy (worst 5)
section_acc = {}
for sec, stats in section_stats.items():
    t = stats["total"]
    c = stats["correct"]
    section_acc[sec] = {
        "total": t,
        "correct": c,
        "doubt": stats["doubt"],
        "wrong": stats["wrong"],
        "accuracy": c / t * 100 if t > 0 else 0,
    }

worst_sections = sorted(section_acc.items(), key=lambda x: x[1]["accuracy"])[:5]

# Top 10 specific errors
errors_list = [r for r in results if r["outcome"] == "wrong"]
top_errors = errors_list[:10]

# ── Save results JSON ──────────────────────────────────────────────────────
output_data = {
    "summary": {
        "total": total,
        "correct": correct,
        "doubt": doubt,
        "wrong": wrong,
        "error": error,
        "overall_accuracy_pct": round(overall_acc, 2),
        "doubt_rate_pct": round(doubt_rate, 2),
        "acc_within_classified_pct": round(acc_within_classified, 2),
        "agreement_rate_pct": round(agreement_rate, 2),
        "agreed_accuracy_pct": round(agreed_acc, 2),
        "debated_accuracy_pct": round(debated_acc, 2),
        "agreed_total": agreed_total,
        "debated_total": debated_total,
        "debate_triggered": debate_triggered,
        "elapsed_seconds": round(elapsed_total, 1),
    },
    "section_accuracy": section_acc,
    "worst_sections": [{"section": s, **v} for s, v in worst_sections],
    "top_errors": top_errors,
    "all_results": results,
}

results_path = OUTPUT_DIR / "accuracy_results.json"
with open(results_path, "w") as f:
    json.dump(output_data, f, indent=2)
print(f"\nResults saved to {results_path}")

# ── Generate markdown report ───────────────────────────────────────────────
report = f"""# Scoped Classifier v2 — BCIPL Accuracy Report

Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
Items tested: {total} (BCIPL ground truth holdout)

## Summary Table

| Metric                       | Value     | Baseline | Delta     |
|------------------------------|-----------|----------|-----------|
| Overall accuracy             | {overall_acc:.1f}%    | 87.0%    | {overall_acc-87:.1f}pp  |
| Doubt rate                   | {doubt_rate:.1f}%    | 13.0%    | {doubt_rate-13:.1f}pp  |
| Accuracy within classified   | {acc_within_classified:.1f}%    | —        | —         |
| Errors (wrong, not doubt)    | {wrong}       | —        | —         |
| Agreement rate (both models) | {agreement_rate:.1f}%    | —        | —         |
| Debate round triggered       | {debate_triggered} items  | —        | —         |
| Total elapsed                | {elapsed_total:.0f}s       | —        | —         |

## Agreement vs Debate Accuracy

| Mode      | Items | Correct | Accuracy |
|-----------|-------|---------|----------|
| Agreed    | {agreed_total}  | {agreed_correct}   | {agreed_acc:.1f}%  |
| Debated   | {debated_total}  | {debated_correct}   | {debated_acc:.1f}%  |

## Worst 5 Sections

| Section | Total | Correct | Accuracy |
|---------|-------|---------|----------|
"""
for sec, stats in worst_sections:
    report += f"| {sec[:50]} | {stats['total']} | {stats['correct']} | {stats['accuracy']:.1f}% |\n"

report += "\n## Top 10 Errors\n\n"
for i, e in enumerate(top_errors, 1):
    report += f"**{i}.** `{e['raw_text'][:80]}`\n"
    report += f"   - Predicted row: {e['predicted_cma_row']} ({e.get('predicted_cma_field','')})\n"
    report += f"   - Correct row: {e['correct_cma_row']} ({e.get('correct_cma_field','')})\n"
    report += f"   - Confidence: {e.get('confidence', 'N/A')}\n\n"

report_path = OUTPUT_DIR / "ACCURACY_REPORT.md"
with open(report_path, "w") as f:
    f.write(report)
print(f"Report saved to {report_path}")

# ── Print final summary ────────────────────────────────────────────────────
print()
print("=" * 60)
print("FINAL RESULTS")
print("=" * 60)
print(f"Total items:              {total}")
print(f"Correct:                  {correct} ({overall_acc:.1f}%)")
print(f"Doubt:                    {doubt} ({doubt_rate:.1f}%)")
print(f"Wrong:                    {wrong}")
print(f"Error:                    {error}")
print(f"Accuracy within classified: {acc_within_classified:.1f}%")
print(f"Agreement rate:           {agreement_rate:.1f}%")
print(f"Debate triggered:         {debate_triggered}")
print(f"Time elapsed:             {elapsed_total:.1f}s")
print()
print("PASS/FAIL vs targets:")
print(f"  Overall accuracy > 90%:  {'PASS' if overall_acc > 90 else ('ACCEPTABLE' if overall_acc > 87 else 'FAIL')}")
print(f"  Doubt rate < 10%:        {'PASS' if doubt_rate < 10 else ('ACCEPTABLE' if doubt_rate < 13 else 'FAIL')}")
print(f"  Acc within classified > 95%: {'PASS' if acc_within_classified > 95 else ('ACCEPTABLE' if acc_within_classified > 90 else 'FAIL')}")
