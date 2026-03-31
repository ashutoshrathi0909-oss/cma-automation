#!/usr/bin/env python3
"""
SLIPL accuracy benchmark — Phase 1 only (classify + compare).

Run: docker compose exec worker python /app/test-results/run_accuracy_slipl.py
Outputs:
  /app/test-results/SLIPL_accuracy_summary.json
  /app/test-results/SLIPL_wrong_entries.json
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
GT_FILE = Path("/app/CMA_Ground_Truth_v1/companies/SLIPL/ground_truth_normalized.json")
OUTPUT_DIR = Path("/app/test-results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SUMMARY_FILE = OUTPUT_DIR / "SLIPL_accuracy_summary.json"
WRONG_FILE = OUTPUT_DIR / "SLIPL_wrong_entries.json"

# ─── Cost guards ──────────────────────────────────────────────────────────────
MAX_ITEMS = 500
TOKEN_REINIT_THRESHOLD = 450_000

# ─── Helpers ──────────────────────────────────────────────────────────────────

def make_classifier():
    from app.services.classification.scoped_classifier import ScopedClassifier
    sc = ScopedClassifier()
    print(f"  [ScopedClassifier] sections={len(sc._contexts)} labels={len(sc._labels_by_row)} tokens=0")
    return sc


def _doubt_result(reason: str):
    from app.services.classification.ai_classifier import AIClassificationResult
    return AIClassificationResult(
        cma_field_name=None,
        cma_row=None,
        cma_sheet="input_sheet",
        broad_classification="",
        confidence=0.0,
        is_doubt=True,
        doubt_reason=reason,
        alternatives=[],
        classification_method="scoped_doubt",
    )


def doc_type_for(cma_row: int) -> str:
    return "balance_sheet" if cma_row >= 111 else "profit_and_loss"


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

print("=" * 60)
print("SLIPL Accuracy Benchmark — Phase 1")
print("=" * 60)

print("Loading ground truth...")
with open(GT_FILE) as f:
    gt_data = json.load(f)

ground_truth = gt_data["database_entries"]
company_meta = gt_data["company_metadata"]

total_items = len(ground_truth)
print(f"  Company:  {company_meta['company_name']}")
print(f"  Industry: {company_meta['industry_type']}")
print(f"  Items:    {total_items}")
print(f"  Keys:     {list(ground_truth[0].keys())}")
print()

if total_items > MAX_ITEMS:
    print(f"WARNING: {total_items} items exceeds MAX_ITEMS={MAX_ITEMS} — truncating")
    ground_truth = ground_truth[:MAX_ITEMS]
    total_items = MAX_ITEMS

print("Initializing classifier...")
sc = make_classifier()
print()

results: list[dict] = []
start_time = time.time()

for i, entry in enumerate(ground_truth):
    raw_text = entry["raw_text"]
    amount = entry.get("amount")
    section = entry.get("section", "")
    correct_row = entry["cma_row"]
    correct_field = entry.get("cma_field_name")
    doc_type = doc_type_for(correct_row)

    # Token budget guard — reinitialize before hitting 500K hard cap
    if sc._total_tokens > TOKEN_REINIT_THRESHOLD:
        print(f"\n  [{i+1}] Token budget {sc._total_tokens} → reinitializing classifier")
        sc = make_classifier()

    # Classify
    try:
        result = sc.classify_sync(
            raw_text=raw_text,
            amount=amount,
            section=section,
            industry_type=entry["industry_type"],
            document_type=doc_type,
            fuzzy_candidates=[],
        )
    except Exception as e:
        print(f"  [{i+1}] classify_sync exception: {e}")
        result = _doubt_result(f"Script exception: {e}")

    # Token-budget doubt → reinitialize and retry once
    if (
        result.is_doubt
        and result.doubt_reason
        and (
            "token budget" in result.doubt_reason.lower()
            or "budget exceeded" in result.doubt_reason.lower()
        )
    ):
        print(f"  [{i+1}] Token-budget doubt → reinitializing and retrying")
        sc = make_classifier()
        try:
            result = sc.classify_sync(
                raw_text=raw_text,
                amount=amount,
                section=section,
                industry_type=entry["industry_type"],
                document_type=doc_type,
                fuzzy_candidates=[],
            )
        except Exception as e2:
            print(f"  [{i+1}] Retry failed: {e2}")
            result = _doubt_result(f"Retry failed: {e2}")

    predicted_row = result.cma_row
    is_correct = (not result.is_doubt) and (predicted_row == correct_row)

    results.append(
        {
            "raw_text": raw_text,
            "section": section,
            "amount": amount,
            "correct_cma_row": correct_row,
            "correct_cma_field": correct_field,
            "predicted_cma_row": predicted_row,
            "predicted_cma_field": result.cma_field_name,
            "confidence": result.confidence,
            "is_correct": is_correct,
            "is_doubt": result.is_doubt,
            "doubt_reason": result.doubt_reason,
            "classification_method": result.classification_method,
            "industry_type": entry["industry_type"],
            "document_type": doc_type,
        }
    )

    # Progress every 25 items
    if (i + 1) % 25 == 0:
        elapsed = time.time() - start_time
        n = i + 1
        correct_n = sum(r["is_correct"] for r in results)
        doubt_n = sum(r["is_doubt"] for r in results)
        acc = correct_n / n * 100
        dbt = doubt_n / n * 100
        rate = n / elapsed if elapsed > 0 else 1
        eta = (total_items - n) / rate
        print(
            f"[{n:3d}/{total_items}] "
            f"acc={acc:.1f}% doubt={dbt:.1f}% | "
            f"{elapsed:.0f}s elapsed eta={eta:.0f}s | tokens={sc._total_tokens}"
        )
        sys.stdout.flush()

# ─── Compute final metrics ────────────────────────────────────────────────────
total = len(results)
correct = sum(r["is_correct"] for r in results)
doubts = sum(r["is_doubt"] for r in results)
wrong = total - correct - doubts
elapsed_total = time.time() - start_time

accuracy_pct = correct / total * 100 if total > 0 else 0.0
classified = total - doubts
acc_classified = correct / classified * 100 if classified > 0 else 0.0
doubt_rate = doubts / total * 100 if total > 0 else 0.0

# ─── Summary table ────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("RESULTS")
print("=" * 60)
print(f"  Company:            SLIPL")
print(f"  Total items:        {total}")
print(f"  Correct:            {correct}  ({accuracy_pct:.1f}%)")
print(f"  Wrong:              {wrong}")
print(f"  Doubts:             {doubts}  ({doubt_rate:.1f}%)")
print(f"  Acc (classified):   {acc_classified:.1f}%")
print(f"  Elapsed:            {elapsed_total:.1f}s")
print()

# Wrong + doubt entries for inspection
wrong_entries = [
    {
        "company": "SLIPL",
        "raw_text": r["raw_text"],
        "section": r["section"],
        "amount": r["amount"],
        "correct_cma_row": r["correct_cma_row"],
        "correct_cma_field": r["correct_cma_field"],
        "predicted_cma_row": r["predicted_cma_row"],
        "predicted_cma_field": r["predicted_cma_field"],
        "confidence": r["confidence"],
        "is_doubt": r["is_doubt"],
        "doubt_reason": r["doubt_reason"],
        "classification_method": r["classification_method"],
        "industry_type": r["industry_type"],
        "document_type": r["document_type"],
    }
    for r in results
    if not r["is_correct"]
]

# ─── Save outputs ─────────────────────────────────────────────────────────────
summary = {
    "company": "SLIPL",
    "industry": "manufacturing",
    "total_items": total,
    "correct": correct,
    "wrong": wrong,
    "doubts": doubts,
    "accuracy_pct": round(accuracy_pct, 2),
    "elapsed_seconds": round(elapsed_total, 1),
}

with open(SUMMARY_FILE, "w") as f:
    json.dump(summary, f, indent=2)
print(f"Summary saved → {SUMMARY_FILE}")

with open(WRONG_FILE, "w") as f:
    json.dump(wrong_entries, f, indent=2)
print(f"Wrong entries ({len(wrong_entries)}) saved → {WRONG_FILE}")

# ─── Wrong entries table (top 20) ─────────────────────────────────────────────
if wrong_entries:
    print()
    print(f"{'#':<4} {'raw_text':<45} {'correct':>7} {'predicted':>10} {'method':<20} {'doubt'}")
    print("-" * 100)
    for idx, w in enumerate(wrong_entries[:20], 1):
        text = (w["raw_text"] or "")[:44]
        pred = str(w["predicted_cma_row"]) if w["predicted_cma_row"] is not None else "None"
        method = (w["classification_method"] or "")[:19]
        doubt_flag = "DOUBT" if w["is_doubt"] else ""
        print(f"{idx:<4} {text:<45} {w['correct_cma_row']:>7} {pred:>10} {method:<20} {doubt_flag}")
    if len(wrong_entries) > 20:
        print(f"  ... and {len(wrong_entries) - 20} more — see {WRONG_FILE}")
