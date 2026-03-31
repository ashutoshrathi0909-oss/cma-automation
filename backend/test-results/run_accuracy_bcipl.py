#!/usr/bin/env python3
"""
BCIPL accuracy benchmark — Phase 1 only (classify + compare).

Reads from: /app/CMA_Ground_Truth_v1/companies/BCIPL/ground_truth_normalized.json
Outputs:   /app/test-results/BCIPL_accuracy_summary.json
           /app/test-results/BCIPL_wrong_entries.json

Run: docker compose exec worker python /app/test-results/run_accuracy_bcipl.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
GT_FILE = Path("/app/CMA_Ground_Truth_v1/companies/BCIPL/ground_truth_normalized.json")
OUTPUT_DIR = Path("/app/test-results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SUMMARY_FILE = OUTPUT_DIR / "BCIPL_accuracy_summary.json"
WRONG_FILE = OUTPUT_DIR / "BCIPL_wrong_entries.json"

# ─── Cost guards ──────────────────────────────────────────────────────────────
MAX_ITEMS = 500
TOKEN_REINIT_THRESHOLD = 450_000

# ─── Row numbering note ───────────────────────────────────────────────────────
# The normalized GT uses cma_row numbers that are exactly 1 less than the
# sheet_row values in canonical_labels.json (e.g., GT row 21 = canonical 22).
# We compare by cma_code (e.g., "II_A1") which is stable across both systems.
# sheetrow_to_code is loaded at runtime from canonical_labels.json.

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


def doc_type_from_row(cma_row) -> str:
    """Infer document type from cma_row: >=111 = balance_sheet, else P&L."""
    if cma_row is not None and int(cma_row) >= 111:
        return "balance_sheet"
    return "profit_and_loss"


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 1: Classify all items and compare
# ═════════════════════════════════════════════════════════════════════════════

print("=" * 60)
print("BCIPL Accuracy Benchmark — Phase 1")
print("=" * 60)

# Load canonical labels: sheet_row → cma_code (for normalizing predicted rows)
CANONICAL_LABELS_PATH = Path("/app/CMA_Ground_Truth_v1/reference/canonical_labels.json")
with open(CANONICAL_LABELS_PATH) as f:
    _canonical = json.load(f)
sheetrow_to_code: dict[int, str] = {item["sheet_row"]: item["code"] for item in _canonical}
print(f"Loaded {len(sheetrow_to_code)} canonical label rows")

# Load ground truth
print("Loading ground truth...")
with open(GT_FILE) as f:
    data = json.load(f)

entries = data["database_entries"]
# Apply MAX_ITEMS cost guard
if len(entries) > MAX_ITEMS:
    print(f"  Cost guard: capping at {MAX_ITEMS} items (GT has {len(entries)})")
    entries = entries[:MAX_ITEMS]

total = len(entries)
print(f"  Items to classify: {total}")
print(f"  Company: {data['company_metadata']['company_name']}")
print()

# Initialize classifier
print("Initializing classifier...")
sc = make_classifier()
print()

results: list[dict] = []
wrong_entries: list[dict] = []
start_time = time.time()

for i, entry in enumerate(entries):
    raw_text = entry["raw_text"]
    section = entry.get("section", "")
    amount = entry.get("amount")       # in crores — pass as-is
    correct_row = entry["cma_row"]
    correct_code = entry.get("cma_code", "")  # stable across numbering systems
    correct_field = entry.get("cma_field_name", "")
    industry_type = entry.get("industry_type", "manufacturing")
    doc_type = doc_type_from_row(correct_row)

    # Token budget guard: reinitialize before hitting 500K hard cap
    if sc._total_tokens > TOKEN_REINIT_THRESHOLD:
        print(f"\n  [{i+1}] Token budget {sc._total_tokens:,} → reinitializing classifier")
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

    # Detect token-budget doubt → reinitialize and retry once
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
    # Normalize predicted row to cma_code for comparison (GT rows are offset by -1
    # relative to canonical sheet_row values used by the classifier).
    predicted_code = sheetrow_to_code.get(predicted_row) if predicted_row is not None else None
    is_correct = (not result.is_doubt) and bool(correct_code) and (predicted_code == correct_code)

    results.append({
        "is_correct": is_correct,
        "is_doubt": result.is_doubt,
    })

    # Collect wrong entries (wrong prediction OR doubt)
    if not is_correct:
        wrong_entries.append({
            "company": "BCIPL",
            "raw_text": raw_text,
            "section": section,
            "amount": amount,
            "correct_cma_row": correct_row,
            "correct_cma_code": correct_code,
            "correct_cma_field": correct_field,
            "predicted_cma_row": predicted_row,
            "predicted_cma_code": predicted_code,
            "predicted_cma_field": result.cma_field_name,
            "confidence": result.confidence,
            "is_doubt": result.is_doubt,
            "doubt_reason": result.doubt_reason,
            "classification_method": result.classification_method,
            "industry_type": industry_type,
            "document_type": doc_type,
        })

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
        eta = (total - n) / rate
        print(
            f"[{n:3d}/{total}] acc={acc:.1f}% doubt={dbt:.1f}% "
            f"errors={err_n} | {elapsed:.0f}s elapsed eta={eta:.0f}s "
            f"| tokens={sc._total_tokens:,}"
        )
        sys.stdout.flush()

# ── Final stats ────────────────────────────────────────────────────────────
elapsed_total = time.time() - start_time
correct = sum(r["is_correct"] for r in results)
doubts = sum(r["is_doubt"] for r in results)
wrong = total - correct - doubts
accuracy_pct = round(correct / total * 100, 2) if total > 0 else 0.0

print()
print("=" * 60)
print("RESULTS")
print("=" * 60)
print(f"  Total:       {total}")
print(f"  Correct:     {correct}  ({accuracy_pct:.1f}%)")
print(f"  Wrong:       {wrong}")
print(f"  Doubts:      {doubts}  ({doubts/total*100:.1f}%)")
print(f"  Elapsed:     {elapsed_total:.1f}s")
print()

# ── Save summary ──────────────────────────────────────────────────────────
summary = {
    "company": "BCIPL",
    "industry": "manufacturing",
    "total_items": total,
    "correct": correct,
    "wrong": wrong,
    "doubts": doubts,
    "accuracy_pct": accuracy_pct,
    "elapsed_seconds": round(elapsed_total, 2),
}

with open(SUMMARY_FILE, "w") as f:
    json.dump(summary, f, indent=2)
print(f"Summary saved     → {SUMMARY_FILE}")

# ── Save wrong entries ────────────────────────────────────────────────────
with open(WRONG_FILE, "w") as f:
    json.dump(wrong_entries, f, indent=2)
print(f"Wrong entries     → {WRONG_FILE}  ({len(wrong_entries)} items)")

# ── Final table ───────────────────────────────────────────────────────────
print()
print("┌─────────────────────┬──────────────────────────┐")
print("│ Metric              │ Value                    │")
print("├─────────────────────┼──────────────────────────┤")
print(f"│ Accuracy            │ {accuracy_pct:.1f}%                    │".ljust(50) + "│"[:0])
print(f"│ Correct             │ {correct}/{total}                   │".ljust(50) + "│"[:0])
print(f"│ Wrong               │ {wrong}                       │".ljust(50) + "│"[:0])
print(f"│ Doubts              │ {doubts} ({doubts/total*100:.1f}%)              │".ljust(50) + "│"[:0])
print(f"│ Time                │ {elapsed_total:.1f}s                   │".ljust(50) + "│"[:0])
print("└─────────────────────┴──────────────────────────┘")

# PASS/FAIL vs baseline (87% in prior scoped-v2 run was 62.7%)
print()
print("PASS/FAIL vs baselines:")
print(f"  Accuracy > 87%:   {'PASS' if accuracy_pct > 87 else 'FAIL'}  ({accuracy_pct:.1f}%)")
print(f"  Doubts < 15%:     {'PASS' if doubts/total*100 < 15 else 'FAIL'}  ({doubts/total*100:.1f}%)")
