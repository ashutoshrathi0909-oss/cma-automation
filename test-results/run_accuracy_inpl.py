#!/usr/bin/env python3
"""
INPL (IFFCO-Nanoventions) accuracy benchmark — Phase 1 only (classify + compare).

Run: docker compose exec worker python /app/test-results/run_accuracy_inpl.py
Outputs:
  /app/test-results/INPL_accuracy_summary.json
  /app/test-results/INPL_wrong_entries.json
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
GT_FILE    = Path("/app/CMA_Ground_Truth_v1/companies/INPL/ground_truth_normalized.json")
OUTPUT_DIR = Path("/app/test-results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SUMMARY_FILE = OUTPUT_DIR / "INPL_accuracy_summary.json"
WRONG_FILE   = OUTPUT_DIR / "INPL_wrong_entries.json"

# ─── Cost guards ──────────────────────────────────────────────────────────────
MAX_ITEMS              = 500          # hard cap (INPL has 186, well under)
TOKEN_REINIT_THRESHOLD = 450_000      # reinit before 500K hard cap

COMPANY  = "INPL"
INDUSTRY = "manufacturing"


# ═════════════════════════════════════════════════════════════════════════════
# Helpers
# ═════════════════════════════════════════════════════════════════════════════

def make_classifier():
    from app.services.classification.scoped_classifier import ScopedClassifier
    sc = ScopedClassifier()
    print(f"  [ScopedClassifier] sections={len(sc._contexts)} "
          f"labels={len(sc._labels_by_row)} tokens=0")
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
        classification_method="script_error",
    )


def doc_type_for_row(cma_row: int | None) -> str:
    """Balance sheet rows >= 111, everything else is profit_and_loss."""
    if cma_row is not None and cma_row >= 111:
        return "balance_sheet"
    return "profit_and_loss"


# ═════════════════════════════════════════════════════════════════════════════
# Load ground truth
# ═════════════════════════════════════════════════════════════════════════════

print("=" * 60)
print("INPL Accuracy Benchmark")
print("=" * 60)

print(f"Loading ground truth from {GT_FILE} ...")
with open(GT_FILE) as f:
    gt_data = json.load(f)

entries = gt_data["database_entries"]
total_gt = len(entries)
print(f"  Loaded {total_gt} entries")
if total_gt > MAX_ITEMS:
    print(f"  [WARN] Cost guard: capping at {MAX_ITEMS} items")
    entries = entries[:MAX_ITEMS]
print()

# ═════════════════════════════════════════════════════════════════════════════
# Phase 1: Classify all items
# ═════════════════════════════════════════════════════════════════════════════

print("Initializing classifier ...")
sc = make_classifier()
print()

results: list[dict] = []
start_time = time.time()

for i, entry in enumerate(entries):
    raw_text      = entry["raw_text"]
    section       = entry.get("section", "")
    amount        = entry.get("amount")
    correct_row   = entry["cma_row"]
    correct_field = entry.get("cma_field_name")
    doc_type      = doc_type_for_row(correct_row)

    # Token budget guard
    if sc._total_tokens > TOKEN_REINIT_THRESHOLD:
        print(f"\n  [{i+1}] Token budget {sc._total_tokens} → reinitializing classifier")
        sc = make_classifier()

    # Classify
    try:
        result = sc.classify_sync(
            raw_text=raw_text,
            amount=amount,
            section=section,
            industry_type=INDUSTRY,
            document_type=doc_type,
            fuzzy_candidates=[],
        )
    except Exception as e:
        print(f"  [{i+1}] classify_sync exception: {e}")
        result = _doubt_result(f"Script exception: {e}")

    # Token-budget doubt → reinit and retry once
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
                industry_type=INDUSTRY,
                document_type=doc_type,
                fuzzy_candidates=[],
            )
        except Exception as e2:
            print(f"  [{i+1}] Retry failed: {e2}")
            result = _doubt_result(f"Retry failed: {e2}")

    predicted_row   = result.cma_row
    predicted_field = result.cma_field_name
    is_correct = (not result.is_doubt) and (predicted_row == correct_row)

    results.append({
        "index":                 i,
        "company":               COMPANY,
        "raw_text":              raw_text,
        "section":               section,
        "amount":                amount,
        "correct_cma_row":       correct_row,
        "correct_cma_field":     correct_field,
        "predicted_cma_row":     predicted_row,
        "predicted_cma_field":   predicted_field,
        "confidence":            result.confidence,
        "is_correct":            is_correct,
        "is_doubt":              result.is_doubt,
        "doubt_reason":          result.doubt_reason,
        "classification_method": result.classification_method,
        "industry_type":         INDUSTRY,
        "document_type":         doc_type,
    })

    # Progress every 25 items
    if (i + 1) % 25 == 0 or (i + 1) == len(entries):
        elapsed = time.time() - start_time
        n = i + 1
        correct_n = sum(r["is_correct"] for r in results)
        doubt_n   = sum(r["is_doubt"]   for r in results)
        acc = correct_n / n * 100
        dbt = doubt_n   / n * 100
        rate = n / elapsed if elapsed > 0 else 1
        eta  = (len(entries) - n) / rate
        print(
            f"[{n:3d}/{len(entries)}] "
            f"acc={acc:.1f}% doubt={dbt:.1f}% | "
            f"{elapsed:.0f}s elapsed eta={eta:.0f}s | "
            f"tokens={sc._total_tokens}"
        )
        sys.stdout.flush()

# ─── Aggregate ────────────────────────────────────────────────────────────────
total        = len(results)
correct      = sum(r["is_correct"] for r in results)
doubts       = sum(r["is_doubt"]   for r in results)
wrong        = total - correct - doubts
elapsed_total = time.time() - start_time
accuracy_pct  = round(correct / total * 100, 2) if total > 0 else 0.0

print()
print("=" * 60)
print("RESULTS")
print("=" * 60)
print(f"  Total:    {total}")
print(f"  Correct:  {correct}  ({accuracy_pct:.1f}%)")
print(f"  Wrong:    {wrong}")
print(f"  Doubts:   {doubts}  ({doubts/total*100:.1f}%)")
print(f"  Elapsed:  {elapsed_total:.1f}s")
print()

# ─── Save summary ─────────────────────────────────────────────────────────────
summary = {
    "company":         COMPANY,
    "industry":        INDUSTRY,
    "total_items":     total,
    "correct":         correct,
    "wrong":           wrong,
    "doubts":          doubts,
    "accuracy_pct":    accuracy_pct,
    "elapsed_seconds": round(elapsed_total, 2),
}
with open(SUMMARY_FILE, "w") as f:
    json.dump(summary, f, indent=2)
print(f"Summary saved → {SUMMARY_FILE}")

# ─── Save wrong entries ───────────────────────────────────────────────────────
wrong_entries = [
    {
        "company":               r["company"],
        "raw_text":              r["raw_text"],
        "section":               r["section"],
        "amount":                r["amount"],
        "correct_cma_row":       r["correct_cma_row"],
        "correct_cma_field":     r["correct_cma_field"],
        "predicted_cma_row":     r["predicted_cma_row"],
        "predicted_cma_field":   r["predicted_cma_field"],
        "confidence":            r["confidence"],
        "is_doubt":              r["is_doubt"],
        "doubt_reason":          r["doubt_reason"],
        "classification_method": r["classification_method"],
        "industry_type":         r["industry_type"],
        "document_type":         r["document_type"],
    }
    for r in results
    if not r["is_correct"]
]
with open(WRONG_FILE, "w") as f:
    json.dump(wrong_entries, f, indent=2)
print(f"Wrong entries saved → {WRONG_FILE}  ({len(wrong_entries)} items)")

# ─── Final summary table ──────────────────────────────────────────────────────
print()
print("=" * 60)
print("FINAL SUMMARY TABLE")
print("=" * 60)
print(f"  Company   : {COMPANY}")
print(f"  Industry  : {INDUSTRY}")
print(f"  Total     : {total}")
print(f"  Correct   : {correct}  ({accuracy_pct:.1f}%)")
print(f"  Wrong     : {wrong}    ({wrong/total*100:.1f}%)")
print(f"  Doubts    : {doubts}   ({doubts/total*100:.1f}%)")
print(f"  Elapsed   : {elapsed_total:.1f}s")
print("=" * 60)
