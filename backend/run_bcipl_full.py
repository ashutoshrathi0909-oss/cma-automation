#!/usr/bin/env python3
"""
Full 448-item BCIPL accuracy benchmark — all 4 phases.

Phase 1: Run benchmark (classify all 448 items via ScopedClassifier)
Phase 2: Error analysis by root cause
Phase 3: Model interrogation (top 30 confident-wrong items via OpenRouter)
Phase 4: Generate full diagnostic report

Run: docker compose exec worker python /app/run_bcipl_full.py
Outputs: /app/DOCS/test-results/scoped-v2/
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
GT_FILE = Path("/app/bcipl_gt.json")
OUTPUT_DIR = Path("/app/DOCS/test-results/scoped-v2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RESULTS_FILE = OUTPUT_DIR / "accuracy_results.json"
INTERROGATION_FILE = OUTPUT_DIR / "model_interrogation.json"
REPORT_FILE = OUTPUT_DIR / "ACCURACY_REPORT.md"

# ─── Benchmark config ─────────────────────────────────────────────────────────
# Reinitialize ScopedClassifier before hitting 500K hard cap
TOKEN_REINIT_THRESHOLD = 450_000
# Phase 3 cost guard
MAX_INTERROGATION_CALLS = 100
TOP_WRONG_FOR_INTERROGATION = 30


# ═════════════════════════════════════════════════════════════════════════════
# Helpers
# ═════════════════════════════════════════════════════════════════════════════

def make_classifier():
    """Create and initialize a fresh ScopedClassifier instance."""
    from app.services.classification.scoped_classifier import ScopedClassifier
    sc = ScopedClassifier()
    print(f"  [ScopedClassifier] sections={len(sc._contexts)} labels={len(sc._labels_by_row)} tokens=0")
    return sc


def _doubt_result(reason: str):
    """Create a doubt AIClassificationResult without importing the full module."""
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


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 1: Run full 448-item benchmark
# ═════════════════════════════════════════════════════════════════════════════

print("=" * 60)
print("PHASE 1: 448-item benchmark")
print("=" * 60)

print("Loading ground truth...")
with open(GT_FILE) as f:
    ground_truth = json.load(f)
print(f"  Loaded {len(ground_truth)} items")
print(f"  Keys: {list(ground_truth[0].keys())}")
print()

print("Initializing classifier...")
sc = make_classifier()
print()

results: list[dict] = []
start_time = time.time()

for i, item in enumerate(ground_truth):
    raw_text = item["raw_text"]
    amount = item.get("amount_rupees")
    section = item.get("section", "")
    doc_type = item.get("document_type", "profit_and_loss")
    correct_row = item["correct_cma_row"]

    # Record routing before the call (won't change between instances)
    routed_section = sc._route_section(section, doc_type)

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
            industry_type="manufacturing",
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
        print(f"  [{i+1}] Token-budget doubt detected → reinitializing and retrying")
        sc = make_classifier()
        try:
            result = sc.classify_sync(
                raw_text=raw_text,
                amount=amount,
                section=section,
                industry_type="manufacturing",
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
            "document_type": doc_type,
            "sheet_name": item.get("sheet_name", ""),
            "amount_rupees": amount,
            "correct_cma_row": correct_row,
            "correct_cma_field": item.get("correct_cma_field"),
            "predicted_cma_row": predicted_row,
            "predicted_cma_field": result.cma_field_name,
            "classification_method": result.classification_method,
            "is_correct": is_correct,
            "routed_section": routed_section,
            "is_doubt": result.is_doubt,
            "doubt_reason": result.doubt_reason,
            "confidence": result.confidence,
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

# ── Phase 1 summary ──────────────────────────────────────────────────────────
total = len(results)
correct = sum(r["is_correct"] for r in results)
doubts = sum(r["is_doubt"] for r in results)
wrong = total - correct - doubts
elapsed_total = time.time() - start_time

overall_acc = correct / total * 100 if total > 0 else 0
doubt_rate = doubts / total * 100 if total > 0 else 0
classified = total - doubts
acc_classified = correct / classified * 100 if classified > 0 else 0

print()
print("=" * 60)
print("PHASE 1 RESULTS")
print("=" * 60)
print(f"  Total:              {total}")
print(f"  Correct:            {correct}  ({overall_acc:.1f}%)  [baseline 87%, delta {overall_acc-87:+.1f}pp]")
print(f"  Doubts:             {doubts}  ({doubt_rate:.1f}%)  [baseline 13%, delta {doubt_rate-13:+.1f}pp]")
print(f"  Wrong:              {wrong}")
print(f"  Acc (classified):   {acc_classified:.1f}%")
print(f"  Elapsed:            {elapsed_total:.0f}s")
print()

# Save raw results immediately (before phases 2-4 that might fail)
with open(RESULTS_FILE, "w") as f:
    json.dump(results, f, indent=2)
print(f"Phase 1 results saved → {RESULTS_FILE}")

# ═════════════════════════════════════════════════════════════════════════════
# PHASE 2: Error analysis
# ═════════════════════════════════════════════════════════════════════════════

print()
print("=" * 60)
print("PHASE 2: Error Analysis")
print("=" * 60)

# Per-routed-section stats
section_stats: dict[str, dict] = defaultdict(
    lambda: {"total": 0, "correct": 0, "doubt": 0, "wrong": 0}
)
for r in results:
    sec = r["routed_section"]
    section_stats[sec]["total"] += 1
    if r["is_correct"]:
        section_stats[sec]["correct"] += 1
    elif r["is_doubt"]:
        section_stats[sec]["doubt"] += 1
    else:
        section_stats[sec]["wrong"] += 1

# Error categorization
confident_wrong = 0  # both models agreed on wrong row
debate_wrong = 0     # debate round still got it wrong
single_wrong = 0     # only one model responded, wrong
other_wrong_count = 0

wrong_items = [r for r in results if not r["is_correct"] and not r["is_doubt"]]
for r in wrong_items:
    method = r.get("classification_method", "")
    if "agree" in method:
        confident_wrong += 1
    elif "debate" in method:
        debate_wrong += 1
    elif "single" in method:
        single_wrong += 1
    else:
        other_wrong_count += 1

# Routing analysis: "other expenses" section
other_exp_items = [
    r for r in results if "other expense" in (r.get("section") or "").lower()
]
other_exp_admin = sum(1 for r in other_exp_items if r["routed_section"] == "admin_expense")
other_exp_mfg = sum(
    1 for r in other_exp_items if r["routed_section"] == "manufacturing_expense"
)

# Top 5 worst sections by accuracy
section_list = sorted(
    [(s, v) for s, v in section_stats.items() if v["total"] > 0],
    key=lambda x: x[1]["correct"] / x[1]["total"],
)

print(f"\nMetrics vs Baseline:")
print(f"  Overall accuracy:         {overall_acc:.1f}%  [baseline 87%, delta {overall_acc-87:+.1f}pp]")
print(f"  Doubt rate:               {doubt_rate:.1f}%  [baseline 13%, delta {doubt_rate-13:+.1f}pp]")
print(f"  Acc within classified:    {acc_classified:.1f}%")

print(f"\nError breakdown (total wrong: {wrong}):")
print(f"  Confident wrong (agree, both on wrong row):  {confident_wrong}")
print(f"  Debate wrong (debate round, still wrong):    {debate_wrong}")
print(f"  Single-model wrong:                          {single_wrong}")
print(f"  Other:                                       {other_wrong_count}")

print(f"\nSection routing — 'other expenses' items:")
print(f"  Total items:                {len(other_exp_items)}")
print(f"  Routed to admin_expense:    {other_exp_admin}")
print(f"  Routed to manufacturing:    {other_exp_mfg}")

print(f"\nTop 5 worst sections:")
for sec, v in section_list[:5]:
    acc_s = v["correct"] / v["total"] * 100
    print(
        f"  {sec:<32s}: {acc_s:5.1f}%  "
        f"({v['correct']}/{v['total']})  doubt={v['doubt']} wrong={v['wrong']}"
    )


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 3: Model interrogation
# ═════════════════════════════════════════════════════════════════════════════

print()
print("=" * 60)
print("PHASE 3: Model Interrogation")
print("=" * 60)

from openai import OpenAI  # noqa: E402

openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# Only confident-wrong items: both models agreed on the wrong row
confident_wrong_items = [
    r
    for r in results
    if not r["is_correct"]
    and not r["is_doubt"]
    and "agree" in r.get("classification_method", "")
]
print(f"Confident-wrong items (scoped_agree, wrong): {len(confident_wrong_items)}")

to_interrogate = confident_wrong_items[:TOP_WRONG_FOR_INTERROGATION]
print(f"Interrogating: {len(to_interrogate)} (cost guard: {MAX_INTERROGATION_CALLS} max calls)")
print()

interrogation_results: list[dict] = []
api_calls = 0

for idx, item in enumerate(to_interrogate):
    if api_calls >= MAX_INTERROGATION_CALLS:
        print(f"Cost guard: {api_calls} calls reached — stopping interrogation")
        break

    raw_text = item["raw_text"]
    section = item.get("section", "")
    doc_type = item.get("document_type", "profit_and_loss")
    correct_row = item["correct_cma_row"]
    predicted_row = item["predicted_cma_row"]

    correct_name = sc._labels_by_row.get(correct_row, {}).get("name", f"Row {correct_row}")
    predicted_name = (
        sc._labels_by_row.get(predicted_row, {}).get("name", f"Row {predicted_row}")
        if predicted_row is not None
        else "Unknown"
    )

    # Rebuild the exact prompt that was sent to the models
    sec_norm = sc._route_section(section, doc_type)
    context = sc._contexts.get(sec_norm) or sc._contexts["admin_expense"]
    prompt = sc._build_prompt(raw_text, item.get("amount_rupees"), section, context)

    interrogation_prompt = f"""You previously classified this item:
"{raw_text}" (section: {section})

You chose: Row {predicted_row} ({predicted_name})
The CORRECT answer is: Row {correct_row} ({correct_name})

Here was the full prompt you received:
{prompt}

Questions:
1. Was Row {correct_row} ({correct_name}) even in the list you were shown? (Yes/No)
2. If yes, why did you pick Row {predicted_row} instead?
3. What in the prompt confused you or led you to the wrong answer?
4. What change to the prompt would have helped you pick the correct row?

Be specific and honest."""

    print(
        f"[{idx+1}/{len(to_interrogate)}] '{raw_text[:70]}'"
        f"\n  Correct: Row {correct_row} ({correct_name}) | Predicted: Row {predicted_row} ({predicted_name})"
    )

    deepseek_resp: str | None = None
    gemini_resp: str | None = None

    # DeepSeek V3
    if api_calls < MAX_INTERROGATION_CALLS:
        try:
            r1 = openrouter_client.chat.completions.create(
                model="deepseek/deepseek-chat",
                messages=[{"role": "user", "content": interrogation_prompt}],
                max_tokens=300,
                temperature=0.0,
            )
            deepseek_resp = r1.choices[0].message.content.strip()
            api_calls += 1
            print(f"  DeepSeek: {deepseek_resp[:120]}")
        except Exception as e:
            deepseek_resp = f"ERROR: {e}"
            print(f"  DeepSeek FAILED: {e}")

    # Gemini Flash
    if api_calls < MAX_INTERROGATION_CALLS:
        try:
            r2 = openrouter_client.chat.completions.create(
                model="google/gemini-2.0-flash-001",
                messages=[{"role": "user", "content": interrogation_prompt}],
                max_tokens=300,
                temperature=0.0,
            )
            gemini_resp = r2.choices[0].message.content.strip()
            api_calls += 1
            print(f"  Gemini:   {gemini_resp[:120]}")
        except Exception as e:
            gemini_resp = f"ERROR: {e}"
            print(f"  Gemini FAILED: {e}")

    interrogation_results.append(
        {
            "index": item["index"],
            "raw_text": raw_text,
            "section": section,
            "routed_section": item["routed_section"],
            "correct_row": correct_row,
            "correct_name": correct_name,
            "predicted_row": predicted_row,
            "predicted_name": predicted_name,
            "deepseek_response": deepseek_resp,
            "gemini_response": gemini_resp,
        }
    )
    print()

print(f"Phase 3 done. {api_calls} API calls used.")

with open(INTERROGATION_FILE, "w") as f:
    json.dump(interrogation_results, f, indent=2)
print(f"Interrogation results saved → {INTERROGATION_FILE}")


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 4: Diagnostic report
# ═════════════════════════════════════════════════════════════════════════════

print()
print("=" * 60)
print("PHASE 4: Generating Diagnostic Report")
print("=" * 60)

# Pattern analysis
PATTERNS: dict[str, list[str]] = {
    "correct_row_not_in_list": ["not in the list", "was not shown", "not available", "not listed", "not present"],
    "defaulted_to_others":     ["defaulted to others", "defaulted to 'others'", "nothing matched", "no match", "closest match"],
    "ambiguous_item_text":     ["ambiguous", "unclear", "confusing", "similar", "overlap"],
    "conflicting_examples":    ["conflicting", "contradictory", "inconsistent"],
    "model_reasoning_error":   ["misclassified", "incorrectly", "mistake", "wrong", "error"],
}

deepseek_patterns: dict[str, int] = defaultdict(int)
gemini_patterns: dict[str, int] = defaultdict(int)
for ir in interrogation_results:
    ds = (ir.get("deepseek_response") or "").lower()
    gm = (ir.get("gemini_response") or "").lower()
    for pname, keywords in PATTERNS.items():
        if any(k in ds for k in keywords):
            deepseek_patterns[pname] += 1
        if any(k in gm for k in keywords):
            gemini_patterns[pname] += 1

# Build report
lines = [
    "# Scoped Classification v2 — Accuracy Report",
    "",
    f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
    f"Ground truth: BCIPL ({total} items)",
    "",
    "## Overall Metrics",
    "",
    "| Metric | Value | Baseline | Delta |",
    "|--------|-------|----------|-------|",
    f"| Overall accuracy | {overall_acc:.1f}% | 87% | {overall_acc-87:+.1f}pp |",
    f"| Doubt rate | {doubt_rate:.1f}% | 13% | {doubt_rate-13:+.1f}pp |",
    f"| Accuracy within classified | {acc_classified:.1f}% | — | — |",
    f"| Wrong items | {wrong} | — | — |",
    f"| Doubt items | {doubts} | — | — |",
    f"| Total elapsed | {elapsed_total:.0f}s | — | — |",
    "",
    "## Error Categories",
    "",
    "| Category | Count | % of errors | Fix |",
    "|----------|-------|-------------|-----|",
]

if wrong > 0:
    lines += [
        f"| Confident wrong (both agreed, wrong row) | {confident_wrong} | {confident_wrong/wrong*100:.0f}% | Improve prompt/examples |",
        f"| Debate wrong (debated, still wrong) | {debate_wrong} | {debate_wrong/wrong*100:.0f}% | Strengthen debate prompt |",
        f"| Single-model wrong | {single_wrong} | {single_wrong/wrong*100:.0f}% | Model failure / retry |",
        f"| Other wrong | {other_wrong_count} | {other_wrong_count/wrong*100:.0f}% | Investigate |",
    ]
else:
    lines.append("| — | 0 | — | — |")

lines += [
    "",
    "## Section Routing Analysis",
    "",
    f"Items whose section text contains 'other expenses': **{len(other_exp_items)}**",
    f"- Routed to `admin_expense`: {other_exp_admin}",
    f"- Routed to `manufacturing_expense`: {other_exp_mfg}",
    "",
    "## Top 5 Worst Sections",
    "",
    "| Section | Total | Correct | Accuracy | Wrong | Doubt |",
    "|---------|-------|---------|----------|-------|-------|",
]
for sec, v in section_list[:5]:
    acc_s = v["correct"] / v["total"] * 100
    lines.append(
        f"| {sec} | {v['total']} | {v['correct']} | {acc_s:.1f}% | {v['wrong']} | {v['doubt']} |"
    )

lines += [
    "",
    "## Model Self-Diagnosis (Top Patterns)",
    "",
    "Patterns detected in model interrogation responses:",
    "",
    "| Pattern | DeepSeek V3 | Gemini Flash |",
    "|---------|-------------|--------------|",
]
for pname in PATTERNS:
    lines.append(f"| {pname} | {deepseek_patterns[pname]} | {gemini_patterns[pname]} |")

lines += [
    "",
    "## Top 10 Worst Errors (with Model Explanations)",
    "",
]
for i2, ir in enumerate(interrogation_results[:10], 1):
    lines += [
        f"### {i2}. `{ir['raw_text'][:80]}`",
        f"- **Section:** `{ir['section']}` → routed to `{ir['routed_section']}`",
        f"- **Correct:** Row {ir['correct_row']} ({ir['correct_name']})",
        f"- **Predicted:** Row {ir['predicted_row']} ({ir['predicted_name']})",
        "",
        f"**DeepSeek V3:** {ir.get('deepseek_response', 'N/A')}",
        "",
        f"**Gemini Flash:** {ir.get('gemini_response', 'N/A')}",
        "",
    ]

lines += [
    "## Recommended Fixes (prioritized)",
    "",
]

# Auto-generate recommendations
rec_num = 1
if confident_wrong > 0:
    lines.append(
        f"{rec_num}. **{confident_wrong} items where both models agreed on the wrong row** "
        "— add more disambiguation examples in the scoped context for the worst sections"
    )
    rec_num += 1
if debate_wrong > 0:
    lines.append(
        f"{rec_num}. **{debate_wrong} items failed after debate** — strengthen the debate prompt "
        "to penalize 'Others' row selection and require explicit reasoning"
    )
    rec_num += 1
for sec, v in section_list[:3]:
    if v["total"] > 0 and (v["correct"] / v["total"] * 100) < 70:
        lines.append(
            f"{rec_num}. **Section `{sec}` accuracy {v['correct']/v['total']*100:.1f}%** "
            "— review routing regex and add more training examples"
        )
        rec_num += 1
if doubt_rate > 13:
    lines.append(
        f"{rec_num}. **Doubt rate {doubt_rate:.1f}% > 13% baseline** "
        "— review items sent to doubt and add rules to resolve common cases"
    )

lines += [
    "",
    "---",
    f"*Generated by `run_bcipl_full.py`. {total} items tested. "
    f"API calls in Phase 3: {api_calls}.*",
]

report_text = "\n".join(lines)
with open(REPORT_FILE, "w") as f:
    f.write(report_text)
print(f"Diagnostic report saved → {REPORT_FILE}")

# ─── Final summary ────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("ALL PHASES COMPLETE")
print("=" * 60)
print(f"  Results:       {RESULTS_FILE}")
print(f"  Interrogation: {INTERROGATION_FILE}")
print(f"  Report:        {REPORT_FILE}")
print()
print("PASS/FAIL vs targets:")
print(f"  Overall accuracy > 90%:           {'PASS' if overall_acc > 90 else ('ACCEPTABLE' if overall_acc > 87 else 'FAIL')} ({overall_acc:.1f}%)")
print(f"  Doubt rate < 10%:                 {'PASS' if doubt_rate < 10 else ('ACCEPTABLE' if doubt_rate < 13 else 'FAIL')} ({doubt_rate:.1f}%)")
print(f"  Acc within classified > 95%:      {'PASS' if acc_classified > 95 else ('ACCEPTABLE' if acc_classified > 90 else 'FAIL')} ({acc_classified:.1f}%)")
