#!/usr/bin/env python3
"""BCIPL accuracy benchmark for the ScopedClassifier (v2).

Run inside the Docker worker container:
  python /app/run_accuracy_test.py

Measures accuracy against 448-item BCIPL holdout ground truth.
DO NOT modify the classifier — this is a read-only test script.
"""
import asyncio
import json
import os
import time
from collections import defaultdict
from pathlib import Path

GROUND_TRUTH_PATH = "/app/DOCS/extractions/BCIPL_classification_ground_truth.json"
RESULTS_DIR = Path("/app/test-results/scoped-v2")

# Cost guard: stop if total tokens exceed this
# DeepSeek R1 ~$0.55/M tokens, Gemini Flash ~$0.10/M tokens (avg ~$0.30/M)
# 448 items × 4 API calls × 1500 tokens = ~2.7M tokens max → ~$0.80
# $5 guard = ~16M tokens, far above expected
COST_STOP_TOKENS = 16_000_000

# Token cost estimate (blended rate for mixed DeepSeek + Gemini Flash)
TOKENS_PER_USD = 3_000_000  # $1 per 3M tokens (conservative estimate)


def map_sheet_to_doc_type(sheet_name: str) -> str:
    """Map source sheet name to document_type hint for the section router."""
    s = (sheet_name or "").lower()
    if "notes" in s and ("p & l" in s or "p&l" in s or "pl" in s):
        return "notes_pl"
    if "notes" in s and ("bs" in s or "balance" in s):
        return "notes_bs"
    if "balance" in s:
        return "balance_sheet"
    if "p & l" in s or "p&l" in s or "profit" in s:
        return "pl"
    if "deprn" in s or "depreciation" in s or "schedule" in s:
        return "notes_bs"
    return "notes_pl"  # safe default for income statement items


async def run_test():
    from app.services.classification.scoped_classifier import ScopedClassifier

    print("Initializing ScopedClassifier...")
    sc = ScopedClassifier()
    print(f"ScopedClassifier ready: {len(sc._contexts)} sections loaded")

    with open(GROUND_TRUTH_PATH, encoding="utf-8") as f:
        items = json.load(f)
    total = len(items)
    print(f"Ground truth: {total} BCIPL items loaded\n")

    # Counters
    correct = 0
    doubt = 0
    wrong = 0
    errors_count = 0  # Python exceptions, treated as doubt per spec

    # Agreement tracking
    round1_agreed = 0    # scoped_agree
    debate_triggered = 0  # any item that went to round 2
    debate_agreed = 0    # scoped_debate
    single_model = 0     # scoped_single_*

    # For per-method accuracy
    round1_correct = 0
    debate_correct = 0

    # Per-section stats
    section_stats: dict[str, dict] = defaultdict(
        lambda: {"correct": 0, "wrong": 0, "doubt": 0, "total": 0}
    )

    errors_detail: list[dict] = []
    all_results: list[dict] = []

    start_time = time.time()

    for i, item in enumerate(items):
        raw_text = item["raw_text"]
        amount = item.get("amount_rupees")
        section = item.get("section", "") or ""
        correct_row = item.get("correct_cma_row")
        correct_field = item.get("correct_cma_field", "")
        sheet_name = item.get("sheet_name", "")
        doc_type = map_sheet_to_doc_type(sheet_name)

        # Cost guard
        estimated_cost = sc._total_tokens / TOKENS_PER_USD
        if estimated_cost > 5.0:
            print(f"\n[COST GUARD] Estimated cost ${estimated_cost:.2f} exceeds $5 limit. Stopping at item {i}.")
            break

        try:
            result = await sc.classify(
                raw_text=raw_text,
                amount=amount,
                section=section,
                industry_type="manufacturing",
                document_type=doc_type,
                fuzzy_candidates=[],
            )

            method = result.classification_method or ""

            # Track agreement method
            if method == "scoped_agree":
                round1_agreed += 1
            elif method == "scoped_debate":
                debate_triggered += 1
                debate_agreed += 1
            elif method == "scoped_doubt":
                debate_triggered += 1  # debate was triggered but didn't agree
            elif method.startswith("scoped_single"):
                single_model += 1

            if result.is_doubt:
                doubt += 1
                is_correct = False
                pred_row = None
                pred_field = None
                section_stats[section]["doubt"] += 1
            elif result.cma_row == correct_row:
                correct += 1
                is_correct = True
                pred_row = result.cma_row
                pred_field = result.cma_field_name
                section_stats[section]["correct"] += 1
                if method == "scoped_agree":
                    round1_correct += 1
                elif method == "scoped_debate":
                    debate_correct += 1
            else:
                wrong += 1
                is_correct = False
                pred_row = result.cma_row
                pred_field = result.cma_field_name
                section_stats[section]["wrong"] += 1
                errors_detail.append({
                    "raw_text": raw_text,
                    "section": section,
                    "sheet_name": sheet_name,
                    "correct_row": correct_row,
                    "correct_field": correct_field,
                    "predicted_row": pred_row,
                    "predicted_field": pred_field,
                    "method": method,
                    "confidence": result.confidence,
                })

            section_stats[section]["total"] += 1

            all_results.append({
                "index": i,
                "raw_text": raw_text,
                "section": section,
                "sheet_name": sheet_name,
                "correct_row": correct_row,
                "correct_field": correct_field,
                "predicted_row": pred_row,
                "predicted_field": pred_field,
                "is_correct": is_correct,
                "is_doubt": result.is_doubt,
                "method": method,
                "confidence": result.confidence,
                "doubt_reason": result.doubt_reason,
            })

        except Exception as e:
            errors_count += 1
            doubt += 1  # count errors as doubt per spec
            section_stats[section]["doubt"] += 1
            section_stats[section]["total"] += 1
            all_results.append({
                "index": i,
                "raw_text": raw_text,
                "section": section,
                "correct_row": correct_row,
                "is_correct": False,
                "is_doubt": True,
                "method": "python_error",
                "error": str(e),
            })

        if (i + 1) % 25 == 0 or (i + 1) == total:
            elapsed = time.time() - start_time
            done = correct + doubt + wrong
            acc = correct / done * 100 if done > 0 else 0
            est_cost = sc._total_tokens / TOKENS_PER_USD
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (total - i - 1) / rate if rate > 0 else 0
            print(
                f"[{i+1:3d}/{total}] Correct={correct} Wrong={wrong} Doubt={doubt} "
                f"Acc={acc:.1f}% Tokens={sc._total_tokens:,} ~${est_cost:.3f} "
                f"Elapsed={elapsed:.0f}s ETA={eta:.0f}s"
            )

    elapsed_total = time.time() - start_time
    done = correct + wrong + doubt
    classified = correct + wrong

    # ── Compute metrics ────────────────────────────────────────────────────────
    overall_accuracy = correct / done * 100 if done > 0 else 0
    doubt_rate = doubt / done * 100 if done > 0 else 0
    acc_within_classified = correct / classified * 100 if classified > 0 else 0
    round1_agreement_rate = round1_agreed / done * 100 if done > 0 else 0
    estimated_cost = sc._total_tokens / TOKENS_PER_USD

    round1_acc = round1_correct / round1_agreed * 100 if round1_agreed > 0 else 0
    debate_acc = debate_correct / debate_agreed * 100 if debate_agreed > 0 else 0

    # ── Print report ───────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  BCIPL ACCURACY BENCHMARK — FINAL RESULTS")
    print(f"{'='*70}")
    print(f"| {'Metric':<28} | {'Value':<10} | {'Baseline':<8} | {'Delta':<8} |")
    print(f"|{'-'*30}|{'-'*12}|{'-'*10}|{'-'*10}|")

    delta_acc = overall_accuracy - 87.0
    delta_doubt = doubt_rate - 13.0
    print(f"| {'Overall accuracy':<28} | {overall_accuracy:>7.1f}%   | 87.0%    | {delta_acc:+.1f}pp   |")
    print(f"| {'Doubt rate':<28} | {doubt_rate:>7.1f}%   | 13.0%    | {delta_doubt:+.1f}pp   |")
    print(f"| {'Accuracy within classified':<28} | {acc_within_classified:>7.1f}%   | —        | —        |")
    print(f"| {'Errors (wrong, not doubt)':<28} | {wrong:<10} | —        | —        |")
    print(f"| {'Agreement rate (both models)':<28} | {round1_agreement_rate:>7.1f}%   | —        | —        |")
    print(f"| {'Debate rounds triggered':<28} | {debate_triggered:<10} | —        | —        |")
    print(f"| {'Total tokens':<28} | {sc._total_tokens:<10,} | —        | —        |")
    print(f"| {'Estimated cost':<28} | ${estimated_cost:<9.3f} | ~$0.10   | —        |")
    print(f"| {'Time elapsed':<28} | {elapsed_total:<7.0f}s    | —        | —        |")
    print(f"{'='*70}")

    print(f"\n--- Agreement vs Debate Accuracy ---")
    print(f"Round 1 agreement: {round1_agreed} items ({round1_agreement_rate:.1f}%) → accuracy {round1_acc:.1f}% ({round1_correct}/{round1_agreed})")
    print(f"Debate triggered:  {debate_triggered} items → agreed after debate: {debate_agreed}, accuracy {debate_acc:.1f}% ({debate_correct}/{debate_agreed})")
    print(f"Single model:      {single_model} items")
    print(f"Python errors:     {errors_count} items (counted as doubt)")

    # ── Worst sections ─────────────────────────────────────────────────────────
    print(f"\n--- Top 5 Worst Sections (min 3 items) ---")
    sortable = [
        (sec, stats)
        for sec, stats in section_stats.items()
        if stats["total"] >= 3
    ]
    sortable.sort(key=lambda x: x[1]["correct"] / x[1]["total"])
    for sec, stats in sortable[:5]:
        acc_s = stats["correct"] / stats["total"] * 100
        print(
            f"  [{acc_s:5.1f}%] {sec[:55]:<55} "
            f"({stats['correct']}/{stats['total']} correct, {stats['doubt']} doubt)"
        )

    # ── Top 10 errors ─────────────────────────────────────────────────────────
    print(f"\n--- Top 10 Specific Errors ---")
    for err in errors_detail[:10]:
        print(
            f"  Text: '{err['raw_text'][:45]}'"
            f"\n    Predicted: Row {err['predicted_row']} ({err['predicted_field']})"
            f"\n    Correct:   Row {err['correct_row']} ({err['correct_field']})"
            f"\n    Method: {err['method']}, Confidence: {err.get('confidence', '?')}"
        )

    # ── Save results ───────────────────────────────────────────────────────────
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    accuracy_results = {
        "run_info": {
            "total_items": done,
            "elapsed_seconds": elapsed_total,
            "total_tokens": sc._total_tokens,
            "estimated_cost_usd": estimated_cost,
        },
        "summary": {
            "correct": correct,
            "wrong": wrong,
            "doubt": doubt,
            "python_errors": errors_count,
            "overall_accuracy_pct": round(overall_accuracy, 2),
            "doubt_rate_pct": round(doubt_rate, 2),
            "acc_within_classified_pct": round(acc_within_classified, 2),
            "round1_agreed": round1_agreed,
            "debate_triggered": debate_triggered,
            "debate_agreed": debate_agreed,
            "single_model": single_model,
            "round1_agreement_rate_pct": round(round1_agreement_rate, 2),
            "round1_accuracy_pct": round(round1_acc, 2),
            "debate_accuracy_pct": round(debate_acc, 2),
        },
        "section_accuracy": {
            sec: {
                "accuracy_pct": round(s["correct"] / s["total"] * 100, 1) if s["total"] > 0 else 0,
                **s,
            }
            for sec, s in section_stats.items()
        },
        "errors_detail": errors_detail,
        "all_results": all_results,
    }

    results_path = RESULTS_DIR / "accuracy_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(accuracy_results, f, indent=2, ensure_ascii=False)
    print(f"\nDetailed results saved to: {results_path}")

    # ── Pass/Fail criteria ─────────────────────────────────────────────────────
    print(f"\n--- Success Criteria ---")
    checks = [
        ("Overall accuracy > 90%", overall_accuracy > 90, overall_accuracy > 87, f"{overall_accuracy:.1f}%"),
        ("Doubt rate < 10%", doubt_rate < 10, doubt_rate < 13, f"{doubt_rate:.1f}%"),
        ("Acc within classified > 95%", acc_within_classified > 95, acc_within_classified > 90, f"{acc_within_classified:.1f}%"),
        ("Cost < $2", estimated_cost < 2, estimated_cost < 5, f"${estimated_cost:.3f}"),
    ]
    for label, passes, acceptable, value in checks:
        status = "PASS" if passes else ("ACCEPTABLE" if acceptable else "FAIL")
        print(f"  [{status:^10}] {label}: {value}")

    return accuracy_results


if __name__ == "__main__":
    asyncio.run(run_test())
