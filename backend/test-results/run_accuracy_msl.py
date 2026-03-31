#!/usr/bin/env python3
"""
MSL (Matrix Stampi Limited) accuracy benchmark — Phase 1 only.

Reads ground truth from /app/CMA_Ground_Truth_v1/companies/MSL/ground_truth_normalized.json,
classifies each item via ScopedClassifier, and saves summary + wrong entries.

Run: docker compose exec worker python /app/test-results/run_accuracy_msl.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Ensure /app is on the path so `from app.services...` resolves correctly
# when the script is run from /app/test-results/
sys.path.insert(0, "/app")

# ─── Paths ────────────────────────────────────────────────────────────────────
GT_FILE = Path("/app/CMA_Ground_Truth_v1/companies/MSL/ground_truth_normalized.json")
OUTPUT_DIR = Path("/app/test-results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SUMMARY_FILE = OUTPUT_DIR / "MSL_accuracy_summary.json"
WRONG_FILE = OUTPUT_DIR / "MSL_wrong_entries.json"

# ─── Cost guards ──────────────────────────────────────────────────────────────
MAX_ITEMS = 500
TOKEN_REINIT_THRESHOLD = 450_000


# ═════════════════════════════════════════════════════════════════════════════
# Helpers
# ═════════════════════════════════════════════════════════════════════════════

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


def doc_type_for_row(cma_row: int) -> str:
    """Rows >= 111 are Balance Sheet; everything else is P&L."""
    return "balance_sheet" if cma_row >= 111 else "profit_and_loss"


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 1: Load GT + classify
# ═════════════════════════════════════════════════════════════════════════════

print("=" * 60)
print("MSL Accuracy Benchmark — Phase 1")
print("=" * 60)

print("Loading ground truth...")
with open(GT_FILE) as f:
    gt_data = json.load(f)

metadata = gt_data["company_metadata"]
ground_truth = gt_data["database_entries"]

print(f"  Company:   {metadata['company_name']}")
print(f"  Industry:  {metadata['industry_type']}")
print(f"  Entries:   {len(ground_truth)}")
print(f"  Keys:      {list(ground_truth[0].keys())}")
print()

# Apply cost guard
if len(ground_truth) > MAX_ITEMS:
    print(f"  Cost guard: capping at {MAX_ITEMS} items (found {len(ground_truth)})")
    ground_truth = ground_truth[:MAX_ITEMS]

print("Initializing classifier...")
sc = make_classifier()
print()

results: list[dict] = []
wrong_entries: list[dict] = []
start_time = time.time()

for i, entry in enumerate(ground_truth):
    raw_text = entry["raw_text"]
    amount = entry.get("amount")
    section = entry.get("section", "")
    correct_row = entry["cma_row"]
    correct_field = entry.get("cma_field_name")
    industry_type = entry.get("industry_type", "manufacturing")
    doc_type = doc_type_for_row(correct_row)

    # Token budget guard: reinitialize before hitting 500K hard cap
    if sc._total_tokens > TOKEN_REINIT_THRESHOLD:
        print(f"\n  [{i+1}] Token budget {sc._total_tokens} → reinitializing classifier")
        sc = make_classifier()

    # Classify
    try:
        result = sc.classify_sync(
            raw_text=raw_text,
            amount=amount,
            section=section,
            industry_type=industry_type,
            document_type=doc_type,
            fuzzy_candidates=[],
        )
    except Exception as e:
        print(f"  [{i+1}] classify_sync exception: {e}")
        result = _doubt_result(f"Script exception: {e}")

    # Detect token budget doubt → reinitialize and retry once
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
                industry_type=industry_type,
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
            "document_type": doc_type,
            "industry_type": industry_type,
            "correct_cma_row": correct_row,
            "correct_cma_field": correct_field,
            "predicted_cma_row": predicted_row,
            "predicted_cma_field": result.cma_field_name,
            "confidence": result.confidence,
            "is_correct": is_correct,
            "is_doubt": result.is_doubt,
            "doubt_reason": result.doubt_reason,
            "classification_method": result.classification_method,
        }
    )

    if not is_correct:
        wrong_entries.append(
            {
                "company": "MSL",
                "raw_text": raw_text,
                "section": section,
                "amount": amount,
                "correct_cma_row": correct_row,
                "correct_cma_field": correct_field,
                "predicted_cma_row": predicted_row,
                "predicted_cma_field": result.cma_field_name,
                "confidence": result.confidence,
                "is_doubt": result.is_doubt,
                "doubt_reason": result.doubt_reason,
                "classification_method": result.classification_method,
                "industry_type": industry_type,
                "document_type": doc_type,
            }
        )

    # Progress every 25 items
    if (i + 1) % 25 == 0:
        elapsed = time.time() - start_time
        n = i + 1
        correct_n = sum(r["is_correct"] for r in results)
        doubt_n = sum(r["is_doubt"] for r in results)
        err_n = n - correct_n - doubt_n
        acc = correct_n / n * 100
        dbt = doubt_n / n * 100
        rate = n / elapsed if elapsed > 0 else 1
        eta = (len(ground_truth) - n) / rate
        print(
            f"[{n:3d}/{len(ground_truth)}] "
            f"acc={acc:.1f}% doubt={dbt:.1f}% errors={err_n} | "
            f"{elapsed:.0f}s elapsed eta={eta:.0f}s | tokens={sc._total_tokens}"
        )
        sys.stdout.flush()


# ─── Summary ──────────────────────────────────────────────────────────────────
total = len(results)
correct = sum(r["is_correct"] for r in results)
doubts = sum(r["is_doubt"] for r in results)
wrong = total - correct - doubts
elapsed_total = time.time() - start_time

accuracy_pct = round(correct / total * 100, 2) if total > 0 else 0.0

summary = {
    "company": "MSL",
    "industry": "manufacturing",
    "total_items": total,
    "correct": correct,
    "wrong": wrong,
    "doubts": doubts,
    "accuracy_pct": accuracy_pct,
    "elapsed_seconds": round(elapsed_total, 1),
}

with open(SUMMARY_FILE, "w") as f:
    json.dump(summary, f, indent=2)

with open(WRONG_FILE, "w") as f:
    json.dump(wrong_entries, f, indent=2)

# ─── Print final table ────────────────────────────────────────────────────────
print()
print("=" * 60)
print("RESULTS")
print("=" * 60)
print(f"  Company:            MSL (Matrix Stampi Limited)")
print(f"  Total items:        {total}")
print(f"  Correct:            {correct}  ({accuracy_pct:.1f}%)")
print(f"  Wrong:              {wrong}")
print(f"  Doubts:             {doubts}  ({doubts/total*100:.1f}%)")
if total - doubts > 0:
    acc_classified = correct / (total - doubts) * 100
    print(f"  Acc (classified):   {acc_classified:.1f}%")
print(f"  Elapsed:            {elapsed_total:.0f}s")
print()
print(f"  Summary  → {SUMMARY_FILE}")
print(f"  Wrong    → {WRONG_FILE}  ({len(wrong_entries)} entries)")
print()

# PASS/FAIL vs BCIPL baseline (62.7%)
bcipl_baseline = 62.7
print("PASS/FAIL vs BCIPL baseline:")
print(f"  Accuracy vs BCIPL ({bcipl_baseline}%):  "
      f"{'+' if accuracy_pct >= bcipl_baseline else ''}{accuracy_pct - bcipl_baseline:.1f}pp  "
      f"({'BETTER' if accuracy_pct > bcipl_baseline else ('SAME' if accuracy_pct == bcipl_baseline else 'WORSE')})")
