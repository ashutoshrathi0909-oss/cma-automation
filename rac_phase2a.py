"""
RAC Phase 2a: Embedding Test
6-company database vs BCIPL holdout (448 items)
No LLM calls — pure vector similarity.
"""

import json
import os
import numpy as np
from collections import Counter
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent
EXTRACTIONS = BASE / "DOCS" / "extractions"
OUT = BASE / "DOCS" / "test-results" / "rac-phase2"
OUT.mkdir(parents=True, exist_ok=True)

DB_FILES = [
    ("SR_Papers",    EXTRACTIONS / "SR_Papers_classification_ground_truth.json",   "Trading"),
    ("SSSS",         EXTRACTIONS / "SSSS_classification_ground_truth.json",         "Trading"),
    ("MSL",          EXTRACTIONS / "MSL_classification_ground_truth.json",          "Manufacturing"),
    ("SLIPL",        EXTRACTIONS / "SLIPL_classification_ground_truth.json",        "Manufacturing"),
    ("Kurunji",      EXTRACTIONS / "Kurunji_Retail_classification_ground_truth.json","Partnership"),
    ("INPL",         EXTRACTIONS / "INPL_classification_ground_truth.json",         "Manufacturing"),
]
TEST_FILE = EXTRACTIONS / "BCIPL_classification_ground_truth.json"

# ── Load data ─────────────────────────────────────────────────────────────────
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

print("Loading database files...")
db_items = []
for name, path, industry in DB_FILES:
    items = load_json(path)
    for it in items:
        it["_source_company"] = name
        it["_industry"] = industry
    db_items.extend(items)
    print(f"  {name}: {len(items)} items")

print(f"  Total DB: {len(db_items)} items")

test_items = load_json(TEST_FILE)
print(f"  BCIPL test: {len(test_items)} items")

# ── Build context strings ─────────────────────────────────────────────────────
def make_context(item):
    sheet   = (item.get("sheet_name") or "").strip()
    section = (item.get("section")    or "").strip()
    raw     = (item.get("raw_text")   or "").strip()
    return f"{sheet} | {section} | {raw}"

db_contexts   = [make_context(it) for it in db_items]
test_contexts = [make_context(it) for it in test_items]

# ── Embed ─────────────────────────────────────────────────────────────────────
NPZ_PATH = OUT / "embeddings_phase2.npz"

if NPZ_PATH.exists():
    print("\nLoading cached embeddings...")
    data = np.load(NPZ_PATH, allow_pickle=False)
    db_emb   = data["db_emb"]
    test_emb = data["test_emb"]
    print(f"  DB emb shape: {db_emb.shape}, Test emb shape: {test_emb.shape}")
else:
    print("\nEmbedding with all-MiniLM-L6-v2 ...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("  Embedding DB items...")
    db_emb = model.encode(db_contexts, batch_size=64, show_progress_bar=True,
                          normalize_embeddings=True)

    print("  Embedding test items...")
    test_emb = model.encode(test_contexts, batch_size=64, show_progress_bar=True,
                            normalize_embeddings=True)

    np.savez_compressed(NPZ_PATH, db_emb=db_emb, test_emb=test_emb)
    print(f"  Saved embeddings to {NPZ_PATH}")

# ── Cosine similarity (batch) ─────────────────────────────────────────────────
# Embeddings already L2-normalised → dot product = cosine similarity
print("\nComputing similarities...")
# shape: (448, 1007)
sim_matrix = test_emb @ db_emb.T

# ── Top-10 retrieval & accuracy metrics ───────────────────────────────────────
TOP_K = 10

results = []

top1_correct = 0
top5_vote_correct = 0
top10_any_correct = 0
sheet_stats = {}   # sheet_name → {total, top1_correct}

print("Evaluating metrics...")
for i, (test_item, sims) in enumerate(zip(test_items, sim_matrix)):
    if i % 50 == 0:
        print(f"  Progress: {i}/{len(test_items)}")

    true_row = test_item["correct_cma_row"]
    sheet    = test_item.get("sheet_name", "Unknown")

    # Top-10 indices (sorted by similarity desc)
    top10_idx = np.argsort(sims)[::-1][:TOP_K]
    top10_items = [db_items[j] for j in top10_idx]
    top10_sims  = [float(sims[j]) for j in top10_idx]
    top10_rows  = [it["correct_cma_row"] for it in top10_items]

    # Top-1
    top1_row = top10_rows[0]
    t1_correct = (top1_row == true_row)
    if t1_correct:
        top1_correct += 1

    # Top-5 majority vote
    vote_counts = Counter(top10_rows[:5])
    top5_vote_row = vote_counts.most_common(1)[0][0]
    t5_correct = (top5_vote_row == true_row)
    if t5_correct:
        top5_vote_correct += 1

    # Top-10 any correct
    t10_any = (true_row in top10_rows)
    if t10_any:
        top10_any_correct += 1

    # Unique CMA rows in top-10
    unique_rows = list(dict.fromkeys(top10_rows))  # preserve order, dedupe

    # Sheet-level stats
    if sheet not in sheet_stats:
        sheet_stats[sheet] = {"total": 0, "top1_correct": 0}
    sheet_stats[sheet]["total"] += 1
    if t1_correct:
        sheet_stats[sheet]["top1_correct"] += 1

    results.append({
        "test_index":        i,
        "raw_text":          test_item["raw_text"],
        "sheet_name":        sheet,
        "section":           test_item.get("section", ""),
        "true_cma_row":      true_row,
        "true_cma_field":    test_item.get("correct_cma_field", ""),
        "top1_row":          top1_row,
        "top1_correct":      t1_correct,
        "top5_vote_row":     top5_vote_row,
        "top5_vote_correct": t5_correct,
        "top10_any_correct": t10_any,
        "unique_rows_top10": unique_rows,
        "num_unique_rows":   len(unique_rows),
        "top10_examples": [
            {
                "rank":          k + 1,
                "similarity":    round(top10_sims[k], 4),
                "raw_text":      top10_items[k]["raw_text"],
                "sheet_name":    top10_items[k].get("sheet_name", ""),
                "section":       top10_items[k].get("section", ""),
                "cma_row":       top10_items[k]["correct_cma_row"],
                "cma_field":     top10_items[k].get("correct_cma_field", ""),
                "source_company":top10_items[k]["_source_company"],
            }
            for k in range(TOP_K)
        ],
    })

n = len(test_items)
top1_acc       = top1_correct / n
top5_vote_acc  = top5_vote_correct / n
top10_any_acc  = top10_any_correct / n
avg_unique_rows = sum(r["num_unique_rows"] for r in results) / n

print(f"\n{'='*60}")
print(f"PHASE 2a RESULTS — BCIPL (n={n})")
print(f"{'='*60}")
print(f"Top-1 accuracy          : {top1_acc:.1%}  ({top1_correct}/{n})")
print(f"Top-5 majority vote acc : {top5_vote_acc:.1%}  ({top5_vote_correct}/{n})")
print(f"Top-10 any correct      : {top10_any_acc:.1%}  ({top10_any_correct}/{n})")
print(f"Avg unique rows in top-10: {avg_unique_rows:.2f}")
print(f"\nSheet-level Top-1 accuracy:")
for sheet, s in sorted(sheet_stats.items(), key=lambda x: -x[1]["total"]):
    acc = s["top1_correct"] / s["total"]
    print(f"  {sheet:<30} {acc:.1%}  ({s['top1_correct']}/{s['total']})")

# ── Save JSON results ─────────────────────────────────────────────────────────
json_out = OUT / "embedding_test_results_phase2.json"
summary = {
    "n_test":               n,
    "n_database":           len(db_items),
    "top1_accuracy":        round(top1_acc, 4),
    "top5_vote_accuracy":   round(top5_vote_acc, 4),
    "top10_any_accuracy":   round(top10_any_acc, 4),
    "avg_unique_rows_top10":round(avg_unique_rows, 2),
    "sheet_stats":          {
        sh: {"accuracy": round(s["top1_correct"]/s["total"], 4), **s}
        for sh, s in sheet_stats.items()
    },
    "items": results,
}
with open(json_out, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print(f"\nSaved results -> {json_out}")

# ── Save Markdown report ──────────────────────────────────────────────────────
md_lines = [
    "# RAC Phase 2a — Embedding Accuracy Report",
    "",
    f"**Database:** 6 companies, {len(db_items)} items",
    f"**Test set:** BCIPL, {n} items (holdout)",
    f"**Embedding model:** all-MiniLM-L6-v2",
    f"**Baseline to beat:** 87.4% (prompt-based)",
    "",
    "## Overall Metrics",
    "",
    f"| Metric | Value |",
    f"|--------|-------|",
    f"| Top-1 accuracy | {top1_acc:.1%} ({top1_correct}/{n}) |",
    f"| Top-5 majority vote accuracy | {top5_vote_acc:.1%} ({top5_vote_correct}/{n}) |",
    f"| Top-10 any correct (recall) | {top10_any_acc:.1%} ({top10_any_correct}/{n}) |",
    f"| Avg unique CMA rows in top-10 | {avg_unique_rows:.2f} |",
    f"| Baseline (prompt-based) | 87.4% |",
    "",
    "## Accuracy by Sheet",
    "",
    "| Sheet | Top-1 Accuracy | Correct | Total |",
    "|-------|---------------|---------|-------|",
]
for sheet, s in sorted(sheet_stats.items(), key=lambda x: -x[1]["total"]):
    acc = s["top1_correct"] / s["total"]
    md_lines.append(f"| {sheet} | {acc:.1%} | {s['top1_correct']} | {s['total']} |")

md_lines += [
    "",
    "## Key Observations",
    "",
    f"- Embedding recall (top-10 any): {top10_any_acc:.1%} — this is the ceiling for RAC",
    f"- Top-1 ({top1_acc:.1%}) vs top-5 vote ({top5_vote_acc:.1%}): voting {'helps' if top5_vote_acc > top1_acc else 'does not help'}",
    f"- Average {avg_unique_rows:.1f} unique candidate CMA rows in top-10 (lower = better narrowing)",
    "",
    "## Wrong Items Analysis",
    "",
    f"Items where top-1 is WRONG: {n - top1_correct}",
    f"Items where top-10 does NOT contain correct row: {n - top10_any_correct} (hardest cases — embedding cannot help)",
    "",
    "---",
    f"*Generated by rac_phase2a.py*",
]

md_out = OUT / "EMBEDDING_ACCURACY_REPORT_PHASE2.md"
with open(md_out, "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines))
print(f"Saved report -> {md_out}")

# ── Save selection for Phase 2b ───────────────────────────────────────────────
wrong_items = [r for r in results if not r["top1_correct"]]
right_items = [r for r in results if r["top1_correct"]]

# Sort wrong items by similarity of top-1 (pick most confusing — highest sim but still wrong)
wrong_sorted = sorted(wrong_items, key=lambda r: -r["top10_examples"][0]["similarity"])
right_sorted  = sorted(right_items, key=lambda r: -r["top10_examples"][0]["similarity"])

group_a = wrong_sorted[:40]   # 40 hard cases (wrong)
group_b  = right_sorted[:20]   # 20 sanity check (right)

phase2b_selection = {
    "group_a_wrong_40": group_a,
    "group_b_right_20": group_b,
}
sel_out = OUT / "phase2b_selection.json"
with open(sel_out, "w", encoding="utf-8") as f:
    json.dump(phase2b_selection, f, indent=2, ensure_ascii=False)
print(f"Saved Phase 2b selection -> {sel_out}")
print(f"\nGroup A (wrong): {len(group_a)} items")
print(f"Group B (right): {len(group_b)} items")
print("\nPhase 2a COMPLETE.")
