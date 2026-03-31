"""
RAC Phase 1a — Embedding-Only Accuracy Test
Uses sentence-transformers (all-MiniLM-L6-v2) for embedding.
Computes cosine similarity between BCIPL items and SR Papers items.
"""

import json
import os
import numpy as np
from collections import Counter
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE = "C:/Users/ASHUTOSH/OneDrive/Desktop/CMA project -2"
SR_PATH   = f"{BASE}/DOCS/extractions/SR_Papers_classification_ground_truth.json"
BC_PATH   = f"{BASE}/DOCS/extractions/BCIPL_classification_ground_truth.json"
REF_PATH  = f"{BASE}/DOCS/extractions/_cma_ref_384.json"
OUT_DIR   = f"{BASE}/DOCS/test-results/rac-phase1"

os.makedirs(OUT_DIR, exist_ok=True)

# ── Load data ──────────────────────────────────────────────────────────────────
print("Loading data files...")
with open(SR_PATH, "r", encoding="utf-8") as f:
    sr_items = json.load(f)
with open(BC_PATH, "r", encoding="utf-8") as f:
    bc_items = json.load(f)
with open(REF_PATH, "r", encoding="utf-8") as f:
    cma_ref = json.load(f)

print(f"SR Papers: {len(sr_items)} items")
print(f"BCIPL:     {len(bc_items)} items")

# ── Build context strings ─────────────────────────────────────────────────────
def context_string(item):
    sheet   = item.get("sheet_name", "").strip()
    section = item.get("section", "").strip()
    raw     = item.get("raw_text", "").strip()
    return f"{sheet} | {section} | {raw}"

sr_contexts = [context_string(i) for i in sr_items]
bc_contexts = [context_string(i) for i in bc_items]

print("\nSample SR context:  ", sr_contexts[0])
print("Sample BCIPL context:", bc_contexts[0])

# ── Embed using sentence-transformers ─────────────────────────────────────────
print("\nLoading sentence-transformers model (all-MiniLM-L6-v2)...")
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    METHOD = "sentence-transformers (all-MiniLM-L6-v2)"

    print("Encoding SR Papers database (216 items)...")
    sr_embeddings = model.encode(sr_contexts, batch_size=32, show_progress_bar=True,
                                  convert_to_numpy=True, normalize_embeddings=True)

    print("Encoding BCIPL test set (448 items)...")
    bc_embeddings = model.encode(bc_contexts, batch_size=32, show_progress_bar=True,
                                  convert_to_numpy=True, normalize_embeddings=True)

except Exception as e:
    print(f"sentence-transformers failed: {e}")
    print("Falling back to TF-IDF...")
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.preprocessing import normalize
    METHOD = "TF-IDF (sklearn fallback)"

    all_texts = sr_contexts + bc_contexts
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
    all_vecs = vectorizer.fit_transform(all_texts).toarray()
    all_vecs = normalize(all_vecs, norm="l2")
    sr_embeddings = all_vecs[:len(sr_items)]
    bc_embeddings = all_vecs[len(sr_items):]

print(f"\nMethod: {METHOD}")
print(f"SR embedding shape:  {sr_embeddings.shape}")
print(f"BCIPL embedding shape: {bc_embeddings.shape}")

# Save embeddings
emb_path = f"{OUT_DIR}/embeddings.npz"
np.savez_compressed(emb_path,
                    sr_embeddings=sr_embeddings,
                    bc_embeddings=bc_embeddings)
print(f"Embeddings saved to: {emb_path}")

# ── Cosine similarity (normalized embeddings → dot product = cosine sim) ───────
print("\nComputing cosine similarity matrix (448 x 216)...")
# bc_embeddings: (448, D), sr_embeddings: (216, D)
sim_matrix = bc_embeddings @ sr_embeddings.T   # shape (448, 216)
print(f"Similarity matrix shape: {sim_matrix.shape}")

# ── Run evaluation ─────────────────────────────────────────────────────────────
TOP_K = 10
results = []

top1_correct   = 0
top5_mv_correct = 0
unique_cma_counts = []

print("\nEvaluating 448 BCIPL items...")
for idx, bc_item in enumerate(bc_items):
    if (idx + 1) % 50 == 0:
        print(f"  Progress: {idx+1}/448")

    true_row   = bc_item["correct_cma_row"]
    true_field = bc_item["correct_cma_field"]

    sims = sim_matrix[idx]  # (216,)
    top10_indices = np.argsort(sims)[::-1][:TOP_K]
    top10_sims    = sims[top10_indices]
    top10_rows    = [sr_items[i]["correct_cma_row"] for i in top10_indices]
    top10_fields  = [sr_items[i]["correct_cma_field"] for i in top10_indices]

    # Top-1 accuracy
    top1_match = (top10_rows[0] == true_row)
    if top1_match:
        top1_correct += 1

    # Top-5 majority vote accuracy
    top5_rows = top10_rows[:5]
    vote_counts = Counter(top5_rows)
    majority_row, majority_count = vote_counts.most_common(1)[0]
    top5_mv_match = (majority_row == true_row)
    if top5_mv_match:
        top5_mv_correct += 1

    # Unique CMA rows in top-10
    unique_rows = len(set(top10_rows))
    unique_cma_counts.append(unique_rows)

    results.append({
        "bcipl_index": idx,
        "raw_text": bc_item["raw_text"],
        "sheet_name": bc_item.get("sheet_name", ""),
        "section": bc_item.get("section", ""),
        "context_string": bc_contexts[idx],
        "true_cma_row": true_row,
        "true_cma_field": true_field,
        "top1_sim": float(top10_sims[0]),
        "top1_cma_row": top10_rows[0],
        "top1_cma_field": top10_fields[0],
        "top1_correct": top1_match,
        "top5_majority_row": majority_row,
        "top5_majority_field": top10_fields[top10_rows.index(majority_row)],
        "top5_majority_correct": top5_mv_match,
        "top10_cma_rows": top10_rows,
        "top10_cma_fields": top10_fields,
        "top10_similarities": [float(s) for s in top10_sims],
        "unique_cma_rows_in_top10": unique_rows,
        "top10_matches": [
            {
                "rank": r + 1,
                "sr_raw_text": sr_items[top10_indices[r]]["raw_text"],
                "sr_sheet": sr_items[top10_indices[r]].get("sheet_name", ""),
                "sr_section": sr_items[top10_indices[r]].get("section", ""),
                "sr_cma_row": sr_items[top10_indices[r]]["correct_cma_row"],
                "sr_cma_field": sr_items[top10_indices[r]]["correct_cma_field"],
                "similarity": float(top10_sims[r])
            }
            for r in range(TOP_K)
        ]
    })

print(f"  Progress: 448/448 — done!")

# ── Compute summary statistics ─────────────────────────────────────────────────
n = len(bc_items)
top1_acc      = top1_correct / n * 100
top5_mv_acc   = top5_mv_correct / n * 100
avg_unique     = np.mean(unique_cma_counts)
median_unique  = np.median(unique_cma_counts)

# Per sheet accuracy
sheets = list(set(r["sheet_name"] for r in results))
sheet_stats = {}
for sheet in sheets:
    items = [r for r in results if r["sheet_name"] == sheet]
    if not items:
        continue
    t1 = sum(1 for r in items if r["top1_correct"])
    t5 = sum(1 for r in items if r["top5_majority_correct"])
    sheet_stats[sheet] = {
        "count": len(items),
        "top1_correct": t1,
        "top5_mv_correct": t5,
        "top1_accuracy_pct": round(t1 / len(items) * 100, 1),
        "top5_mv_accuracy_pct": round(t5 / len(items) * 100, 1)
    }

# 20 worst failures: high similarity but wrong CMA row
# Failures = top1 wrong
failures = [r for r in results if not r["top1_correct"]]
failures_sorted = sorted(failures, key=lambda x: x["top1_sim"], reverse=True)
worst_20 = failures_sorted[:20]

print(f"\n{'='*60}")
print(f"RESULTS SUMMARY")
print(f"{'='*60}")
print(f"Method:              {METHOD}")
print(f"Total items tested:  {n}")
print(f"Top-1 accuracy:      {top1_acc:.1f}%  ({top1_correct}/{n})")
print(f"Top-5 majority vote: {top5_mv_acc:.1f}%  ({top5_mv_correct}/{n})")
print(f"Avg unique CMA rows in top-10: {avg_unique:.2f}")
print(f"Median unique CMA rows in top-10: {median_unique:.1f}")

# Distribution of unique_cma_counts
dist = Counter(unique_cma_counts)
print(f"\nDistribution of unique CMA rows in top-10:")
for k in sorted(dist.keys()):
    print(f"  {k} unique rows: {dist[k]} items ({dist[k]/n*100:.1f}%)")

print(f"\nPer-sheet accuracy:")
for sheet, stats in sorted(sheet_stats.items(), key=lambda x: -x[1]["count"]):
    print(f"  {sheet:35s}  n={stats['count']:3d}  top1={stats['top1_accuracy_pct']:5.1f}%  top5mv={stats['top5_mv_accuracy_pct']:5.1f}%")

# ── Save full results JSON ─────────────────────────────────────────────────────
results_path = f"{OUT_DIR}/embedding_test_results.json"
with open(results_path, "w", encoding="utf-8") as f:
    json.dump({
        "metadata": {
            "method": METHOD,
            "model": "all-MiniLM-L6-v2",
            "database": "SR_Papers (216 items)",
            "test_set": "BCIPL (448 items)",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "top_k": TOP_K
        },
        "summary": {
            "total_items": n,
            "top1_correct": top1_correct,
            "top1_accuracy_pct": round(top1_acc, 2),
            "top5_mv_correct": top5_mv_correct,
            "top5_mv_accuracy_pct": round(top5_mv_acc, 2),
            "avg_unique_cma_rows_top10": round(float(avg_unique), 2),
            "median_unique_cma_rows_top10": float(median_unique)
        },
        "per_sheet_stats": sheet_stats,
        "unique_cma_count_distribution": {str(k): v for k, v in sorted(dist.items())},
        "worst_20_failures": worst_20,
        "all_results": results
    }, f, indent=2, ensure_ascii=False)

print(f"\nFull results saved to: {results_path}")

# ── Save markdown report ───────────────────────────────────────────────────────
report_path = f"{OUT_DIR}/EMBEDDING_ACCURACY_REPORT.md"

worst_20_md = "\n".join([
    f"| {i+1} | `{w['raw_text'][:40]}` | {w['sheet_name'][:25]} | {w['true_cma_field'][:30]} | {w['top1_cma_field'][:30]} | {w['top1_sim']:.3f} |"
    for i, w in enumerate(worst_20)
])

sheet_md = "\n".join([
    f"| {sheet[:35]} | {stats['count']} | {stats['top1_accuracy_pct']}% | {stats['top5_mv_accuracy_pct']}% |"
    for sheet, stats in sorted(sheet_stats.items(), key=lambda x: -x[1]["count"])
])

dist_md = "\n".join([
    f"| {k} unique rows | {v} | {v/n*100:.1f}% |"
    for k, v in sorted(dist.items())
])

report = f"""# RAC Phase 1a — Embedding Accuracy Report

**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
**Method:** {METHOD}
**Database:** SR Papers — 216 trading company items
**Test Set:** BCIPL — 448 manufacturing company items

---

## Overall Results

| Metric | Value |
|--------|-------|
| Top-1 Accuracy | **{top1_acc:.1f}%** ({top1_correct}/{n}) |
| Top-5 Majority Vote Accuracy | **{top5_mv_acc:.1f}%** ({top5_mv_correct}/{n}) |
| Average unique CMA rows in top-10 | **{avg_unique:.2f}** |
| Median unique CMA rows in top-10 | **{median_unique:.1f}** |

---

## Candidate Narrowing Analysis

**Key finding:** Instead of asking the LLM to pick from all 139 CMA fields,
RAC narrows the candidate set to approximately **{avg_unique:.0f} unique fields** on average.

> If we narrow to top-5 candidate fields and send to Haiku, the LLM only needs
> to pick from ~{avg_unique:.0f} options instead of 139. This reduces the chance
> of hallucination and speeds up classification.

### Distribution of unique CMA rows in top-10

| Unique CMA rows | Items | % of total |
|----------------|-------|------------|
{dist_md}

---

## Accuracy by Sheet Name

| Sheet Name | Count | Top-1 Acc | Top-5 MV Acc |
|-----------|-------|-----------|--------------|
{sheet_md}

---

## Top-20 Worst Failures

*(Highest similarity score but wrong CMA row — these are the hardest cases)*

| # | Raw Text | Sheet | True CMA Field | Predicted Field | Similarity |
|---|----------|-------|---------------|-----------------|------------|
{worst_20_md}

---

## Interpretation

1. **Top-1 Accuracy ({top1_acc:.1f}%)**: {
    "Excellent" if top1_acc >= 80 else
    "Good" if top1_acc >= 65 else
    "Moderate" if top1_acc >= 50 else
    "Low — needs improvement"
} — the single most similar SR item matches the BCIPL item's CMA row this % of the time.

2. **Top-5 MV Accuracy ({top5_mv_acc:.1f}%)**: Majority voting over the top-5 nearest
   neighbors {'improves' if top5_mv_acc > top1_acc else 'does not significantly change'} accuracy
   vs. top-1 alone ({'+' if top5_mv_acc >= top1_acc else ''}{top5_mv_acc - top1_acc:.1f} pp).

3. **Candidate Narrowing ({avg_unique:.1f} avg unique rows in top-10)**: RAC reduces
   the classification problem from 139 CMA fields to ~{avg_unique:.0f} candidates.
   This is the main value proposition — even if RAC alone is imperfect, it dramatically
   constrains the search space for Haiku.

4. **Cross-domain gap**: SR Papers is a trading company; BCIPL is manufacturing.
   The accuracy reflects how well financial line-item language generalises across
   these two domains using only text similarity.

---

## Files

- `embeddings.npz` — compressed numpy arrays (sr_embeddings, bc_embeddings)
- `embedding_test_results.json` — full per-item results with top-10 matches
- `EMBEDDING_ACCURACY_REPORT.md` — this report
"""

with open(report_path, "w", encoding="utf-8") as f:
    f.write(report)

print(f"Report saved to: {report_path}")
print("\nAll done.")
