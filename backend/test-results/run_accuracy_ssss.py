#!/usr/bin/env python3
"""
SSSS (Salem Stainless Steel Suppliers) accuracy benchmark — Phase 1 only.

Classifies all 63 items via ScopedClassifier, compares predicted cma_row
to ground truth cma_row, and saves summary + wrong entries.

Run: docker compose exec worker python /app/test-results/run_accuracy_ssss.py
Outputs: /app/test-results/SSSS_accuracy_summary.json
         /app/test-results/SSSS_wrong_entries.json
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Ensure /app is on the path so `from app.services...` works from this subdir
sys.path.insert(0, "/app")

# ─── Paths ────────────────────────────────────────────────────────────────────
GT_FILE = Path("/app/CMA_Ground_Truth_v1/companies/SSSS/ground_truth_normalized.json")
OUTPUT_DIR = Path("/app/test-results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SUMMARY_FILE = OUTPUT_DIR / "SSSS_accuracy_summary.json"
WRONG_FILE = OUTPUT_DIR / "SSSS_wrong_entries.json"

# ─── Config ───────────────────────────────────────────────────────────────────
MAX_ITEMS = 500                  # cost guard (SSSS has 63)
TOKEN_REINIT_THRESHOLD = 450_000  # reinit before 500K hard cap
PROGRESS_EVERY = 25


# ─── Helpers ──────────────────────────────────────────────────────────────────

def make_classifier():
    from app.services.classification.scoped_classifier import ScopedClassifier
    sc = ScopedClassifier()
    print(f"  [ScopedClassifier] initialized | tokens=0")
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
    """Balance sheet rows start at 111; P&L rows are below that."""
    return "balance_sheet" if cma_row >= 111 else "profit_and_loss"


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 1: Classify all SSSS items
# ═════════════════════════════════════════════════════════════════════════════

print("=" * 60)
print("SSSS Accuracy Benchmark — Phase 1")
print("=" * 60)

print(f"Loading ground truth from {GT_FILE} ...")
with open(GT_FILE) as f:
    gt_data = json.load(f)

entries = gt_data["database_entries"]
total_available = len(entries)
entries = entries[:MAX_ITEMS]  # cost guard (no-op for SSSS)

print(f"  Company: {gt_data['company_metadata']['company_name']}")
print(f"  Industry: {gt_data['company_metadata']['industry_type']}")
print(f"  Entries: {total_available} (processing {len(entries)})")
print()

print("Initializing classifier...")
sc = make_classifier()
print()

results: list[dict] = []
start_time = time.time()

for i, entry in enumerate(entries):
    raw_text = entry["raw_text"]
    amount = entry.get("amount")
    section = entry.get("section", "")
    industry_type = entry["industry_type"]
    correct_row = entry["cma_row"]
    correct_field = entry.get("cma_field_name")
    doc_type = doc_type_for(correct_row)

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
            industry_type=industry_type,
            document_type=doc_type,
            fuzzy_candidates=[],
        )
    except Exception as e:
        print(f"  [{i+1}] classify_sync exception: {e}")
        result = _doubt_result(f"Script exception: {e}")

    # Retry on token-budget doubt
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
            "index": i,
            "raw_text": raw_text,
            "section": section,
            "amount": amount,
            "industry_type": industry_type,
            "document_type": doc_type,
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

    # Progress every 25 items
    if (i + 1) % PROGRESS_EVERY == 0:
        elapsed = time.time() - start_time
        n = i + 1
        correct_n = sum(r["is_correct"] for r in results)
        doubt_n = sum(r["is_doubt"] for r in results)
        err_n = n - correct_n - doubt_n
        acc = correct_n / n * 100
        rate = n / elapsed if elapsed > 0 else 1
        eta = (len(entries) - n) / rate
        print(
            f"[{n:3d}/{len(entries)}] "
            f"acc={acc:.1f}% doubts={doubt_n} errors={err_n} | "
            f"{elapsed:.0f}s elapsed eta={eta:.0f}s | tokens={sc._total_tokens}"
        )
        sys.stdout.flush()

# ─── Summary ──────────────────────────────────────────────────────────────────
elapsed_total = time.time() - start_time
total = len(results)
correct = sum(r["is_correct"] for r in results)
doubts = sum(r["is_doubt"] for r in results)
wrong = total - correct - doubts
accuracy_pct = round(correct / total * 100, 2) if total > 0 else 0.0

summary = {
    "company": "SSSS",
    "industry": "trading",
    "total_items": total,
    "correct": correct,
    "wrong": wrong,
    "doubts": doubts,
    "accuracy_pct": accuracy_pct,
    "elapsed_seconds": round(elapsed_total, 1),
}

# ─── Wrong entries (predicted != correct, including doubts) ───────────────────
wrong_entries = [
    {
        "company": "SSSS",
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
with open(SUMMARY_FILE, "w") as f:
    json.dump(summary, f, indent=2)
print(f"\nSummary saved → {SUMMARY_FILE}")

with open(WRONG_FILE, "w") as f:
    json.dump(wrong_entries, f, indent=2)
print(f"Wrong entries saved → {WRONG_FILE}")

# ─── Final summary table ──────────────────────────────────────────────────────
print()
print("=" * 60)
print("SSSS ACCURACY RESULTS")
print("=" * 60)
print(f"  Total items:    {total}")
print(f"  Correct:        {correct}  ({accuracy_pct:.1f}%)")
print(f"  Doubts:         {doubts}  ({doubts/total*100:.1f}%)")
print(f"  Wrong:          {wrong}  ({wrong/total*100:.1f}%)")
print(f"  Elapsed:        {elapsed_total:.0f}s")
print()

if wrong_entries:
    print(f"WRONG / DOUBT ENTRIES ({len(wrong_entries)}):")
    print("-" * 60)
    for e in wrong_entries:
        tag = "DOUBT" if e["is_doubt"] else "WRONG"
        print(
            f"  [{tag}] '{e['raw_text'][:55]}'"
            f"\n         section='{e['section']}'"
            f"\n         correct=row {e['correct_cma_row']} ({e['correct_cma_field']})"
            f"\n         predicted=row {e['predicted_cma_row']} ({e['predicted_cma_field']})"
            f"\n         method={e['classification_method']} conf={e['confidence']:.2f}"
        )
        if e["is_doubt"]:
            print(f"         doubt_reason={e['doubt_reason']}")
        print()
else:
    print("  All items classified correctly!")
