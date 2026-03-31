"""
RAC Phase 2b Analysis: Combine Haiku results, calculate accuracy, save reports.
"""

import json
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent
OUT  = BASE / "DOCS" / "test-results" / "rac-phase2"

# ── Haiku results (pasted from 6 Agent calls) ─────────────────────────────────
# Format: list of 6 batches, each with 10 items
HAIKU_RESULTS = [
    # Batch 1
    [
        {"item_index": 1, "classified_cma_row": 68, "confidence": 0.95, "reasoning": "Direct match with high-similarity examples. 'Rates & Taxes' maps to Row 68."},
        {"item_index": 2, "classified_cma_row": 59, "confidence": 0.92, "reasoning": "Opening Finished Goods is counterpart to Closing Finished Goods (Row 59)."},
        {"item_index": 3, "classified_cma_row": 71, "confidence": 0.80, "reasoning": "Administrative & General Expenses broader than audit/director fees; Row 71 appropriate."},
        {"item_index": 4, "classified_cma_row": 71, "confidence": 0.75, "reasoning": "Selling & Distribution Expenses is broader selling/admin category; Row 71 appropriate."},
        {"item_index": 5, "classified_cma_row": 71, "confidence": 0.78, "reasoning": "Administrative & General Expenses not specifically audit/director fees; Row 71."},
        {"item_index": 6, "classified_cma_row": 49, "confidence": 0.82, "reasoning": "Manufacturing Expenses broad category; Row 49 (Others Manufacturing)."},
        {"item_index": 7, "classified_cma_row": 46, "confidence": 0.90, "reasoning": "Job Work Charges -> Row 46 (Processing/Job Work Charges)."},
        {"item_index": 8, "classified_cma_row": 71, "confidence": 0.80, "reasoning": "Consultation Fees is professional service; Row 71 (Others Admin)."},
        {"item_index": 9, "classified_cma_row": 67, "confidence": 0.90, "reasoning": "Labour Welfare Expenses -> Row 67 (Salary and Staff Expenses)."},
        {"item_index": 10, "classified_cma_row": 49, "confidence": 0.77, "reasoning": "Manufacturing Expenses (FY23) -> Row 49 (Others Manufacturing)."},
    ],
    # Batch 2
    [
        {"item_index": 1, "classified_cma_row": 73, "confidence": 0.94, "reasoning": "Selling & Distribution in auditor's remuneration section -> Row 73."},
        {"item_index": 2, "classified_cma_row": 71, "confidence": 0.86, "reasoning": "Consultation Fees -> Row 71 (Others Admin)."},
        {"item_index": 3, "classified_cma_row": 46, "confidence": 0.92, "reasoning": "Job Work Charges -> Row 46."},
        {"item_index": 4, "classified_cma_row": 46, "confidence": 0.91, "reasoning": "Job Work Charges (FY22) -> Row 46."},
        {"item_index": 5, "classified_cma_row": 67, "confidence": 0.88, "reasoning": "Labour Welfare (FY23) -> Row 67 (Salary and Staff)."},
        {"item_index": 6, "classified_cma_row": 67, "confidence": 0.87, "reasoning": "Labour Welfare (FY22) -> Row 67 (Salary and Staff)."},
        {"item_index": 7, "classified_cma_row": 50, "confidence": 0.93, "reasoning": "Machinery Maintenance -> Row 50 (Repairs and Maintenance Manufacturing)."},
        {"item_index": 8, "classified_cma_row": 56, "confidence": 0.97, "reasoning": "Depreciation -> Row 56."},
        {"item_index": 9, "classified_cma_row": 69, "confidence": 0.86, "reasoning": "Bad Debts Written Back -> Row 69 (Bad Debts)."},
        {"item_index": 10, "classified_cma_row": 69, "confidence": 0.86, "reasoning": "Bad Debts Written Back (duplicate) -> Row 69."},
    ],
    # Batch 3
    [
        {"item_index": 1, "classified_cma_row": 23, "confidence": 0.92, "reasoning": "Duty Drawback Received (FY23) -> Row 23 (Export Sales)."},
        {"item_index": 2, "classified_cma_row": 56, "confidence": 0.95, "reasoning": "Amortization Expenses -> Row 56 (Depreciation)."},
        {"item_index": 3, "classified_cma_row": 69, "confidence": 0.88, "reasoning": "Bad debts written off -> Row 69 (Bad Debts)."},
        {"item_index": 4, "classified_cma_row": 69, "confidence": 0.87, "reasoning": "Bad debts (FY23) -> Row 69 (Bad Debts)."},
        {"item_index": 5, "classified_cma_row": 85, "confidence": 0.90, "reasoning": "Bill Discounting Charges (FY23) -> Row 85 (Bank Charges)."},
        {"item_index": 6, "classified_cma_row": 69, "confidence": 0.85, "reasoning": "Bad Debts Written Back (FY23) -> Row 69."},
        {"item_index": 7, "classified_cma_row": 71, "confidence": 0.88, "reasoning": "Administrative & General Expenses (FY22) -> Row 71."},
        {"item_index": 8, "classified_cma_row": 31, "confidence": 0.93, "reasoning": "Profit on Sale of Fixed Asset -> Row 31."},
        {"item_index": 9, "classified_cma_row": 47, "confidence": 0.82, "reasoning": "Selling & Distribution Expenses (FY22) includes freight -> Row 47."},
        {"item_index": 10, "classified_cma_row": 31, "confidence": 0.94, "reasoning": "Profit on Sale of Fixed Assets (FY23) -> Row 31."},
    ],
    # Batch 4
    [
        {"item_index": 1, "classified_cma_row": 34, "confidence": 0.85, "reasoning": "Brought forward P&L - no exact candidate; Row 34 as fallback."},
        {"item_index": 2, "classified_cma_row": 45, "confidence": 0.82, "reasoning": "Opening Finished Goods (FY23) misplaced in employee benefits; Row 45 by precedent."},
        {"item_index": 3, "classified_cma_row": 85, "confidence": 0.88, "reasoning": "Bill Discounting Charges (FY22) -> Row 85 (Bank Charges)."},
        {"item_index": 4, "classified_cma_row": 22, "confidence": 0.90, "reasoning": "Sales of Trading Goods -> Row 22 (Domestic Sales)."},
        {"item_index": 5, "classified_cma_row": 22, "confidence": 0.90, "reasoning": "Sales of Trading Goods (duplicate) -> Row 22."},
        {"item_index": 6, "classified_cma_row": 153, "confidence": 0.80, "reasoning": "DPT-3 Unsecured Loans LT portion -> Row 153 (Unsecured Loans Long Term)."},
        {"item_index": 7, "classified_cma_row": 45, "confidence": 0.81, "reasoning": "Opening Finished Goods (FY22) -> Row 45 by precedent."},
        {"item_index": 8, "classified_cma_row": 73, "confidence": 0.88, "reasoning": "Tax Audit is audit fee -> Row 73."},
        {"item_index": 9, "classified_cma_row": 250, "confidence": 0.86, "reasoning": "ESI payable -> Row 250 (Other Current Liabilities)."},
        {"item_index": 10, "classified_cma_row": 85, "confidence": 0.89, "reasoning": "Bill Discounting Charges -> Row 85 (Bank Charges)."},
    ],
    # Batch 5
    [
        {"item_index": 1, "classified_cma_row": 45, "confidence": 0.96, "reasoning": "Salaries & Wages -> Row 45."},
        {"item_index": 2, "classified_cma_row": 68, "confidence": 0.94, "reasoning": "Rent -> Row 68 (Rent, Rates and Taxes)."},
        {"item_index": 3, "classified_cma_row": 71, "confidence": 0.94, "reasoning": "Insurance -> Row 71 (Others Admin and Selling)."},
        {"item_index": 4, "classified_cma_row": 45, "confidence": 0.94, "reasoning": "Salaries & Wages (FY23) -> Row 45."},
        {"item_index": 5, "classified_cma_row": 45, "confidence": 0.94, "reasoning": "Salaries & Wages (FY22) -> Row 45."},
        {"item_index": 6, "classified_cma_row": 48, "confidence": 0.93, "reasoning": "Power & Fuel -> Row 48."},
        {"item_index": 7, "classified_cma_row": 59, "confidence": 0.93, "reasoning": "Less: Closing - Finished Goods -> Row 59."},
        {"item_index": 8, "classified_cma_row": 30, "confidence": 0.93, "reasoning": "Interest Income -> Row 30."},
        {"item_index": 9, "classified_cma_row": 30, "confidence": 0.93, "reasoning": "Interest Income (duplicate) -> Row 30."},
        {"item_index": 10, "classified_cma_row": 83, "confidence": 0.93, "reasoning": "Interest - Term Loan & Others -> Row 83."},
    ],
    # Batch 6
    [
        {"item_index": 1, "classified_cma_row": 68, "confidence": 0.95, "reasoning": "Rent (FY23) -> Row 68."},
        {"item_index": 2, "classified_cma_row": 68, "confidence": 0.95, "reasoning": "Rent (FY22) -> Row 68."},
        {"item_index": 3, "classified_cma_row": 68, "confidence": 0.96, "reasoning": "Rates & Taxes (FY23) -> Row 68."},
        {"item_index": 4, "classified_cma_row": 71, "confidence": 0.95, "reasoning": "Insurance (FY23) -> Row 71."},
        {"item_index": 5, "classified_cma_row": 42, "confidence": 0.96, "reasoning": "Total Raw Materials - Indigenous (FY22) -> Row 42."},
        {"item_index": 6, "classified_cma_row": 68, "confidence": 0.96, "reasoning": "Rates & Taxes (FY22) -> Row 68."},
        {"item_index": 7, "classified_cma_row": 71, "confidence": 0.95, "reasoning": "Insurance (FY22) -> Row 71."},
        {"item_index": 8, "classified_cma_row": 42, "confidence": 0.96, "reasoning": "Total Raw Materials - Indigenous -> Row 42."},
        {"item_index": 9, "classified_cma_row": 67, "confidence": 0.88, "reasoning": "Contribution to PF & Other Funds -> Row 67."},
        {"item_index": 10, "classified_cma_row": 67, "confidence": 0.88, "reasoning": "Contribution to PF & Other Funds (FY23) -> Row 67."},
    ],
]

# ── Load metadata ─────────────────────────────────────────────────────────────
with open(OUT / "batch_prompts.json", encoding="utf-8") as f:
    batches = json.load(f)

# Flatten metadata: global_idx -> meta dict
meta_by_global = {}
for b in batches:
    for m in b["meta"]:
        meta_by_global[m["global_idx"]] = m

# ── Merge results ─────────────────────────────────────────────────────────────
all_results = []
for batch_idx, (batch_results, batch_data) in enumerate(zip(HAIKU_RESULTS, batches)):
    for item_res in batch_results:
        local_idx  = item_res["item_index"]
        global_idx = (batch_idx * 10) + (local_idx - 1)
        meta       = meta_by_global.get(global_idx, {})

        true_row  = meta.get("true_cma_row")
        haiku_row = item_res["classified_cma_row"]
        correct   = (haiku_row == true_row)
        group     = meta.get("group", "?")

        all_results.append({
            "global_idx":       global_idx,
            "batch":            batch_idx + 1,
            "group":            group,
            "raw_text":         meta.get("raw_text", ""),
            "sheet_name":       meta.get("sheet_name", ""),
            "section":          meta.get("section", ""),
            "true_cma_row":     true_row,
            "true_cma_field":   meta.get("true_cma_field", ""),
            "embedding_top1":   meta.get("embedding_top1"),
            "embedding_correct":meta.get("embedding_correct"),
            "haiku_row":        haiku_row,
            "haiku_correct":    correct,
            "confidence":       item_res.get("confidence"),
            "reasoning":        item_res.get("reasoning", ""),
        })

# ── Accuracy by group ──────────────────────────────────────────────────────────
group_a = [r for r in all_results if r["group"] == "A"]
group_b = [r for r in all_results if r["group"] == "B"]

a_correct = sum(1 for r in group_a if r["haiku_correct"])
b_correct = sum(1 for r in group_b if r["haiku_correct"])

a_acc = a_correct / len(group_a) if group_a else 0
b_acc = b_correct / len(group_b) if group_b else 0

total_correct = a_correct + b_correct
total_acc     = total_correct / len(all_results)

# Embedding accuracy on same 60 items
emb_correct = sum(1 for r in all_results if r["embedding_correct"])
emb_acc     = emb_correct / len(all_results)

# RAC improvement over embedding on Group A (hard cases)
emb_a_correct = sum(1 for r in group_a if r["embedding_correct"])
emb_a_acc     = emb_a_correct / len(group_a) if group_a else 0

print(f"{'='*60}")
print(f"PHASE 2b RESULTS")
print(f"{'='*60}")
print(f"Group A (embedding WRONG, n={len(group_a)}): Haiku {a_acc:.1%} ({a_correct}/{len(group_a)}), Embedding {emb_a_acc:.1%}")
print(f"Group B (embedding RIGHT, n={len(group_b)}): Haiku {b_acc:.1%} ({b_correct}/{len(group_b)})")
print(f"Combined 60 items: Haiku {total_acc:.1%}, Embedding {emb_acc:.1%}")
print()

# ── Failure analysis ──────────────────────────────────────────────────────────
failures = [r for r in all_results if not r["haiku_correct"]]
print(f"FAILURES ({len(failures)} items):")
for f in failures:
    print(f"  [{f['group']}] '{f['raw_text']}' | {f['sheet_name']} | {f['section']}")
    print(f"       True={f['true_cma_row']} ({f['true_cma_field']}), Haiku={f['haiku_row']}, Emb={f['embedding_top1']}")

# ── Projected accuracy for all 448 items ──────────────────────────────────────
# Phase 2a: embedding top-1 acc = 44.4% (199/448)
# For the 249 items embedding got WRONG: Haiku would classify at rate a_acc
# For the 199 items embedding got RIGHT: Haiku would classify at rate b_acc
# But note: our Group A is sorted by highest similarity (most confusing wrong) — actual wrong items may be easier
# So project conservatively:
emb_total_correct = 199
emb_total_wrong   = 249

projected_rac = (emb_total_correct * b_acc + emb_total_wrong * a_acc) / 448

# Baseline comparison
baseline = 0.874

print(f"\n{'='*60}")
print(f"PROJECTED ACCURACY FOR ALL 448 ITEMS")
print(f"{'='*60}")
print(f"Embedding top-1:       44.4%")
print(f"RAC (Haiku) projected: {projected_rac:.1%}")
print(f"Baseline (prompt):     {baseline:.1%}")
print(f"Delta vs baseline:     {projected_rac - baseline:+.1%}")
print()

# ── Save JSON ─────────────────────────────────────────────────────────────────
json_out = {
    "n_group_a":       len(group_a),
    "n_group_b":       len(group_b),
    "n_total":         len(all_results),
    "group_a_accuracy":round(a_acc, 4),
    "group_b_accuracy":round(b_acc, 4),
    "combined_accuracy":round(total_acc, 4),
    "embedding_accuracy_60": round(emb_acc, 4),
    "projected_rac_448": round(projected_rac, 4),
    "baseline": baseline,
    "items": all_results,
}
with open(OUT / "rac_haiku_results_phase2.json", "w", encoding="utf-8") as f:
    json.dump(json_out, f, indent=2, ensure_ascii=False)
print(f"Saved -> rac_haiku_results_phase2.json")

# ── Save Markdown report ──────────────────────────────────────────────────────
md = [
    "# RAC Phase 2b — Accuracy Report (Haiku + Retrieval)",
    "",
    f"**Test set:** BCIPL (60 selected items: 40 hard / 20 easy)**",
    f"**Database:** 6 companies, 1,007 items**",
    f"**Baseline to beat:** 87.4% (prompt-based approach on 448 items)**",
    "",
    "## Results Summary",
    "",
    "| Metric | Value |",
    "|--------|-------|",
    f"| Group A accuracy (embedding WRONG, n={len(group_a)}) | {a_acc:.1%} ({a_correct}/{len(group_a)}) |",
    f"| Group B accuracy (embedding RIGHT, n={len(group_b)}) | {b_acc:.1%} ({b_correct}/{len(group_b)}) |",
    f"| Combined 60-item accuracy | {total_acc:.1%} ({total_correct}/{len(all_results)}) |",
    f"| Embedding-only accuracy (same 60 items) | {emb_acc:.1%} |",
    "",
    "## Projected Full-Dataset Accuracy (448 items)",
    "",
    "| Method | Accuracy | vs Baseline |",
    "|--------|----------|-------------|",
    f"| Embedding only (top-1) | 44.4% | -43.0% |",
    f"| **RAC (Embedding + Haiku) projected** | **{projected_rac:.1%}** | **{projected_rac - baseline:+.1%}** |",
    f"| Baseline (prompt-based) | 87.4% | — |",
    "",
    "### Projection Methodology",
    f"- {emb_total_correct} items embedding got right × Group B rate ({b_acc:.1%}) = {emb_total_correct * b_acc:.0f} correct",
    f"- {emb_total_wrong} items embedding got wrong × Group A rate ({a_acc:.1%}) = {emb_total_wrong * a_acc:.0f} correct",
    f"- Total projected: {projected_rac * 448:.0f} / 448 = {projected_rac:.1%}",
    "",
    "## Failure Analysis",
    "",
    f"**Items where RAC failed:** {len(failures)} / {len(all_results)}",
    "",
    "| Group | raw_text | Sheet | True Row | Haiku Row |",
    "|-------|----------|-------|----------|-----------|",
]
for f in failures:
    md.append(f"| {f['group']} | {f['raw_text'][:40]} | {f['sheet_name'][:20]} | {f['true_cma_row']} ({f['true_cma_field']}) | {f['haiku_row']} |")

md += [
    "",
    "## Verdict",
    "",
]
if projected_rac > baseline:
    md.append(f"**RAC BEATS THE BASELINE**: Projected {projected_rac:.1%} vs {baseline:.1%} (+{projected_rac - baseline:.1%})")
else:
    md.append(f"**RAC DOES NOT BEAT BASELINE**: Projected {projected_rac:.1%} vs {baseline:.1%} ({projected_rac - baseline:.1%})")
    md.append("")
    md.append("**Root causes of underperformance:**")
    md.append("1. Embedding top-10 recall is only 72.3% — correct answer not in candidates for 27.7% of items")
    md.append("2. BCIPL has BCIPL-specific items (Co., Deprn sheet, subnotes) not well represented in 6-company DB")
    md.append("3. Section mismatch noise: OCR section labels differ across companies, confusing retrieval")

md += [
    "",
    "## Comparison Table",
    "",
    "| Approach | Accuracy | Notes |",
    "|----------|----------|-------|",
    "| Prompt-based (baseline) | 87.4% | Uses full 384-item CMA reference |",
    f"| Embedding-only (top-1) | 44.4% | all-MiniLM-L6-v2, 6-company DB |",
    f"| RAC projected | {projected_rac:.1%} | Embedding candidates + Haiku |",
    "",
    "---",
    "*Generated by rac_phase2b_analyze.py*",
]

with open(OUT / "RAC_ACCURACY_REPORT_PHASE2.md", "w", encoding="utf-8") as f:
    f.write("\n".join(md))
print(f"Saved -> RAC_ACCURACY_REPORT_PHASE2.md")
print("\nPhase 2b COMPLETE.")
