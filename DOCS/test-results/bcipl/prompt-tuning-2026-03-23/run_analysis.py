"""
Phase 3: Failure analysis — score baseline results, group error patterns.
Outputs baseline_accuracy.md
"""
import json
from collections import defaultdict
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent

# Load results
with open(OUTPUT_DIR / "baseline_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

results = data["results"]
total = len(results)
correct = sum(1 for r in results if r["is_correct"])
wrong = [r for r in results if not r["is_correct"]]

# ── By confidence level ──
conf_buckets = {">= 0.9": [], "0.8-0.89": [], "< 0.8": []}
for r in results:
    c = r["confidence"]
    if c >= 0.9:
        conf_buckets[">= 0.9"].append(r)
    elif c >= 0.8:
        conf_buckets["0.8-0.89"].append(r)
    else:
        conf_buckets["< 0.8"].append(r)

# ── By sheet ──
by_sheet = defaultdict(list)
for r in results:
    by_sheet[r["sheet_name"]].append(r)

# ── Group failures by pattern ──
patterns = defaultdict(list)

for r in wrong:
    exp_row = r["expected_cma_row"]
    pred_row = r["predicted_cma_row"]
    sheet = r["sheet_name"]
    raw = r["raw_text"]
    section = r.get("section", "")

    # Determine pattern
    # 1. P&L item classified as BS field or vice versa
    exp_is_pnl = exp_row <= 108
    pred_is_pnl = pred_row <= 108 if pred_row > 0 else False
    if exp_is_pnl != pred_is_pnl and pred_row > 0:
        patterns["Section confusion (P&L vs BS)"].append(r)
        continue

    # 2. Adjacent field (within 5 rows)
    if pred_row > 0 and abs(exp_row - pred_row) <= 5:
        patterns["Adjacent field (within 5 rows)"].append(r)
        continue

    # 3. Depreciation routing
    if exp_row in (56, 63, 162, 163, 165, 175) or pred_row in (56, 63, 162, 163, 165, 175):
        patterns["Depreciation / Fixed asset routing"].append(r)
        continue

    # 4. Interest routing
    if exp_row in (83, 84, 85) or pred_row in (83, 84, 85):
        patterns["Interest routing (term/WC/bank)"].append(r)
        continue

    # 5. "Others" overflow — specific field exists but "Others" chosen
    others_rows = {34, 49, 64, 71, 93, 125, 238, 250}
    if pred_row in others_rows:
        patterns["Others overflow"].append(r)
        continue

    # 6. Inventory confusion
    if exp_row in (193, 194, 197, 198, 200, 201) or pred_row in (193, 194, 197, 198, 200, 201):
        patterns["Inventory / stock confusion"].append(r)
        continue

    # 7. Sundry creditors / trade payables
    if exp_row in (242, 243, 249, 250) or pred_row in (242, 243, 249, 250):
        patterns["Creditors / payables routing"].append(r)
        continue

    # 8. Statutory dues
    if exp_row in (244, 246) or pred_row in (244, 246):
        patterns["Statutory dues / provisions"].append(r)
        continue

    # 9. Loan classification
    if exp_row in (131, 132, 136, 137, 148, 149, 152, 153, 154) or \
       pred_row in (131, 132, 136, 137, 148, 149, 152, 153, 154):
        patterns["Loan classification"].append(r)
        continue

    # 10. Advances / receivables
    if exp_row in (219, 220, 221, 222, 223, 224, 235, 236, 237) or \
       pred_row in (219, 220, 221, 222, 223, 224, 235, 236, 237):
        patterns["Advances / receivables routing"].append(r)
        continue

    # 11. Salary / employee expenses
    if exp_row in (45, 67, 73) or pred_row in (45, 67, 73):
        patterns["Employee expense routing"].append(r)
        continue

    # Catch-all
    patterns["Other"].append(r)

# ── Build the report ──
lines = []
lines.append("# Baseline Accuracy Report")
lines.append(f"\n**Date:** {data['timestamp'][:10]}")
lines.append(f"**Prompt:** {data['prompt_version']}")
lines.append(f"\n## Summary\n")
lines.append(f"| Metric | Value |")
lines.append(f"|--------|-------|")
lines.append(f"| Total items tested | {total} |")
lines.append(f"| Correct | {correct} ({correct/total*100:.1f}%) |")
lines.append(f"| Wrong | {len(wrong)} ({len(wrong)/total*100:.1f}%) |")

uncertain = sum(1 for r in results if r["confidence"] < 0.8)
lines.append(f"| Uncertain (conf < 0.8) | {uncertain} |")

lines.append(f"\n## By Confidence Level\n")
lines.append(f"| Confidence | Items | Correct | Accuracy |")
lines.append(f"|------------|-------|---------|----------|")
for label, items in conf_buckets.items():
    n = len(items)
    c = sum(1 for r in items if r["is_correct"])
    pct = f"{c/n*100:.1f}%" if n else "N/A"
    lines.append(f"| {label} | {n} | {c} | {pct} |")

lines.append(f"\n## By Sheet\n")
lines.append(f"| Sheet | Items | Correct | Accuracy |")
lines.append(f"|-------|-------|---------|----------|")
for sheet in sorted(by_sheet.keys()):
    items = by_sheet[sheet]
    n = len(items)
    c = sum(1 for r in items if r["is_correct"])
    pct = f"{c/n*100:.1f}%" if n else "N/A"
    lines.append(f"| {sheet} | {n} | {c} | {pct} |")

lines.append(f"\n## Failure Patterns ({len(wrong)} failures)\n")
lines.append(f"| Pattern | Count | % of Failures |")
lines.append(f"|---------|-------|---------------|")
for pattern, items in sorted(patterns.items(), key=lambda x: -len(x[1])):
    n = len(items)
    pct = f"{n/len(wrong)*100:.1f}%"
    lines.append(f"| {pattern} | {n} | {pct} |")

# Detailed failure listing per pattern
lines.append(f"\n## Detailed Failures by Pattern\n")
for pattern, items in sorted(patterns.items(), key=lambda x: -len(x[1])):
    lines.append(f"\n### {pattern} ({len(items)} items)\n")
    lines.append(f"| Raw Text | Expected (Row) | Predicted (Row) | Conf | Section |")
    lines.append(f"|----------|----------------|-----------------|------|---------|")
    for r in items:
        raw = r["raw_text"][:50]
        exp = f"{r['expected_cma_field']} ({r['expected_cma_row']})"
        pred = f"{r['predicted_cma_field']} ({r['predicted_cma_row']})"
        conf = f"{r['confidence']:.2f}"
        sec = r.get("section", "")[:40]
        lines.append(f"| {raw} | {exp} | {pred} | {conf} | {sec} |")

# Token cost summary
tok = data["token_estimate"]
lines.append(f"\n## Token Usage & Cost\n")
lines.append(f"| Metric | Value |")
lines.append(f"|--------|-------|")
lines.append(f"| Total input tokens | {tok['total_input_tokens']:,} |")
lines.append(f"| Total output tokens | {tok['total_output_tokens']:,} |")
lines.append(f"| Avg input per item | {tok['avg_input_tokens_per_item']:,} |")
lines.append(f"| Avg output per item | {tok['avg_output_tokens_per_item']:,} |")
lines.append(f"| Batches | {tok['total_batches']} |")
# OpenRouter Haiku pricing
input_cost = tok['total_input_tokens'] / 1_000_000 * 0.80
output_cost = tok['total_output_tokens'] / 1_000_000 * 4.00
lines.append(f"| Est. input cost | ${input_cost:.3f} |")
lines.append(f"| Est. output cost | ${output_cost:.3f} |")
lines.append(f"| **Est. total cost** | **${input_cost + output_cost:.3f}** |")

report = "\n".join(lines)
out_file = OUTPUT_DIR / "baseline_accuracy.md"
out_file.write_text(report, encoding="utf-8")
print(report)
print(f"\nSaved to: {out_file}")
