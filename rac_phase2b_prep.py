"""
RAC Phase 2b Prep: Build 6 batch prompts for Haiku (10 items each).
Outputs: DOCS/test-results/rac-phase2/batch_prompts.json
"""

import json
from pathlib import Path
from collections import Counter

BASE = Path(__file__).parent
OUT  = BASE / "DOCS" / "test-results" / "rac-phase2"

# ── Build row_to_field mapping from all ground truth files ───────────────────
row_to_field = {}
ALL_GT_FILES = [
    BASE / "DOCS" / "extractions" / "SR_Papers_classification_ground_truth.json",
    BASE / "DOCS" / "extractions" / "SSSS_classification_ground_truth.json",
    BASE / "DOCS" / "extractions" / "MSL_classification_ground_truth.json",
    BASE / "DOCS" / "extractions" / "SLIPL_classification_ground_truth.json",
    BASE / "DOCS" / "extractions" / "Kurunji_Retail_classification_ground_truth.json",
    BASE / "DOCS" / "extractions" / "INPL_classification_ground_truth.json",
    BASE / "DOCS" / "extractions" / "BCIPL_classification_ground_truth.json",
]
for gt_path in ALL_GT_FILES:
    with open(gt_path, encoding="utf-8") as f:
        items = json.load(f)
    for it in items:
        row = it.get("correct_cma_row")
        field = it.get("correct_cma_field", "")
        if row and field:
            row_to_field[int(row)] = field

print(f"row_to_field built from ground truth: {len(row_to_field)} unique rows")

# ── Sheet → valid row ranges ───────────────────────────────────────────────────
SHEET_ROW_RANGES = {
    "Notes to P & L":   list(range(22, 109)),      # rows 22-108
    "Notes to P&L":     list(range(22, 109)),
    "Subnotes to PL":   list(range(22, 109)),
    "Notes BS":         list(range(116, 259)),      # rows 116-258
    "Notes BS (1)":     list(range(116, 259)),
    "Notes BS (2)":     list(range(116, 259)),
    "Subnotes to BS":   list(range(116, 259)),
    "Co., Deprn":       [56, 63, 162, 163],
}

def get_sheet_candidates(sheet_name):
    """Return valid CMA rows for a given sheet."""
    for key, rows in SHEET_ROW_RANGES.items():
        if key.lower() in sheet_name.lower() or sheet_name.lower() in key.lower():
            return rows
    return []

# ── Load selection ────────────────────────────────────────────────────────────
with open(OUT / "phase2b_selection.json", encoding="utf-8") as f:
    sel = json.load(f)

group_a = sel["group_a_wrong_40"]   # 40 wrong
group_b = sel["group_b_right_20"]   # 20 right

all_60 = [(it, "A") for it in group_a] + [(it, "B") for it in group_b]
print(f"Total items: {len(all_60)} (A={len(group_a)}, B={len(group_b)})")

# ── Build candidate set for each item ────────────────────────────────────────
def build_candidates(item):
    """
    Build candidate CMA rows for this item.
    Priority order:
      1. Embedding top-10 unique rows (most relevant by similarity)
      2. Sheet-constrained rows that have known field names (fill to 15)
    Always filter to sheet-valid rows when sheet constraint applies.
    """
    top10 = item["top10_examples"]
    emb_rows = list(dict.fromkeys(ex["cma_row"] for ex in top10))  # dedup, rank order
    emb_fields = {ex["cma_row"]: ex["cma_field"] for ex in top10}

    sheet = item.get("sheet_name", "")
    sheet_rows_set = set(get_sheet_candidates(sheet))

    # Start with embedding rows, filtered to sheet-valid (if constraint exists)
    if sheet_rows_set:
        candidate_rows = [r for r in emb_rows if r in sheet_rows_set]
    else:
        candidate_rows = list(emb_rows)

    # Fill remaining slots from sheet range rows that have known names
    if sheet_rows_set and len(candidate_rows) < 15:
        known_sheet_rows = [r for r in sorted(sheet_rows_set)
                            if r in row_to_field and r not in candidate_rows]
        for r in known_sheet_rows:
            if len(candidate_rows) >= 15:
                break
            candidate_rows.append(r)

    # Cap at 15
    candidate_rows = candidate_rows[:15]

    # Build display strings
    candidates_display = []
    for r in candidate_rows:
        field = emb_fields.get(r) or row_to_field.get(r) or f"CMA Row {r}"
        candidates_display.append(f"Row {r}: {field}")

    return candidate_rows, candidates_display

# ── Format examples (top-5 most similar) ─────────────────────────────────────
def format_examples(item):
    top5 = item["top10_examples"][:5]
    lines = []
    for k, ex in enumerate(top5, 1):
        lines.append(
            f'{k}. "{ex["raw_text"]}" ({ex["sheet_name"]} | {ex["section"]}) '
            f'-> Row {ex["cma_row"]} ({ex["cma_field"]}) '
            f'[sim={ex["similarity"]:.3f}, company={ex["source_company"]}]'
        )
    return "\n".join(lines)

# ── Build batch prompts (6 batches of 10) ─────────────────────────────────────
BATCH_SIZE = 10
batches = []

for batch_idx in range(6):
    start = batch_idx * BATCH_SIZE
    end   = start + BATCH_SIZE
    batch_items = all_60[start:end]

    if not batch_items:
        break

    # Build prompt
    classify_lines = []
    meta = []

    for local_idx, (item, group) in enumerate(batch_items, 1):
        candidate_rows, cands_display = build_candidates(item)
        examples_text = format_examples(item)

        classify_lines.append(
            f'\n--- ITEM {local_idx} ---\n'
            f'raw_text: "{item["raw_text"]}"\n'
            f'sheet: {item["sheet_name"]}\n'
            f'section: {item.get("section", "")}\n'
            f'CANDIDATE CMA FIELDS for this item:\n'
            + "\n".join(f"  {c}" for c in cands_display) +
            f'\nSIMILAR CLASSIFIED EXAMPLES:\n{examples_text}'
        )
        meta.append({
            "local_idx":      local_idx,
            "global_idx":     start + local_idx - 1,
            "test_index":     item["test_index"],
            "group":          group,
            "raw_text":       item["raw_text"],
            "sheet_name":     item["sheet_name"],
            "section":        item.get("section", ""),
            "true_cma_row":   item["true_cma_row"],
            "true_cma_field": item["true_cma_field"],
            "embedding_top1": item["top1_row"],
            "embedding_correct": item["top1_correct"],
            "candidate_rows": candidate_rows,
        })

    prompt = f"""You are classifying Indian financial statement line items into CMA (Credit Monitoring Arrangement) fields used by Indian banks.

For each item below:
- CANDIDATE CMA FIELDS lists the only valid options (pick from these only)
- SIMILAR CLASSIFIED EXAMPLES shows already-classified items from other companies for reference
- Return the single best CMA row number for each item

{"".join(classify_lines)}

Return ONLY a JSON array with exactly {len(batch_items)} objects:
[
  {{"item_index": 1, "classified_cma_row": <row_number>, "confidence": <0.0-1.0>, "reasoning": "<brief reason>"}},
  ...
]

Rules:
- item_index must match the ITEM number above (1-{len(batch_items)})
- classified_cma_row must be one of the candidate row numbers listed for that item
- Do not include any text outside the JSON array"""

    batches.append({
        "batch_idx":  batch_idx + 1,
        "item_count": len(batch_items),
        "prompt":     prompt,
        "meta":       meta,
    })
    print(f"Batch {batch_idx+1}: {len(batch_items)} items (global {start+1}-{end})")

# ── Save ──────────────────────────────────────────────────────────────────────
out_path = OUT / "batch_prompts.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(batches, f, indent=2, ensure_ascii=False)
print(f"\nSaved {len(batches)} batch prompts -> {out_path}")

# Print first prompt for inspection
print("\n" + "="*60)
print("BATCH 1 PROMPT PREVIEW (first 2000 chars):")
print("="*60)
print(batches[0]["prompt"][:2000])
