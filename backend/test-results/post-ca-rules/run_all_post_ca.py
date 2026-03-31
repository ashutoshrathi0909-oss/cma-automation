#!/usr/bin/env python3
"""
Post-CA-Rules Accuracy Benchmark — All 9 Companies + Interview.

Runs classification accuracy for all companies with the new CA-verified rules,
saves results to post-ca-rules/ directory, then compares with baseline results
from the parent test-results/ directory.

After accuracy tests, interviews DeepSeek V3 about genuinely wrong items.

Run: docker compose exec worker python /app/test-results/post-ca-rules/run_all_post_ca.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# Ensure /app is on sys.path
sys.path.insert(0, "/app")

# ─── Paths ────────────────────────────────────────────────────────────────────
BASELINE_DIR = Path("/app/test-results")
OUTPUT_DIR = Path("/app/test-results/post-ca-rules")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

GT_COMPANIES_DIR = Path("/app/CMA_Ground_Truth_v1/companies")
EXTRACTIONS_DIR = Path("/app/DOCS/extractions")
CANONICAL_LABELS_PATH = Path("/app/CMA_Ground_Truth_v1/reference/canonical_labels.json")

# ─── Cost guards ──────────────────────────────────────────────────────────────
MAX_ITEMS_PER_COMPANY = 500
TOKEN_REINIT_THRESHOLD = 450_000
MAX_INTERVIEWS = 100

# ─── Company configs ─────────────────────────────────────────────────────────
COMPANIES = {
    "BCIPL": {
        "gt_path": GT_COMPANIES_DIR / "BCIPL" / "ground_truth_normalized.json",
        "gt_format": "companies",
        "industry": "manufacturing",
    },
    "Dynamic_Air": {
        "gt_path": GT_COMPANIES_DIR / "Dynamic_Air" / "ground_truth_normalized.json",
        "gt_format": "companies",
        "industry": "manufacturing",
    },
    "Mehta_Computer": {
        "gt_path": GT_COMPANIES_DIR / "Mehta_Computer" / "ground_truth_normalized.json",
        "gt_format": "companies",
        "industry": "trading",
    },
    "INPL": {
        "gt_path": EXTRACTIONS_DIR / "INPL_classification_ground_truth.json",
        "gt_format": "extractions",
        "industry": "manufacturing",
    },
    "Kurunji_Retail": {
        "gt_path": EXTRACTIONS_DIR / "Kurunji_Retail_classification_ground_truth.json",
        "gt_format": "extractions",
        "industry": "trading",
    },
    "MSL": {
        "gt_path": EXTRACTIONS_DIR / "MSL_classification_ground_truth.json",
        "gt_format": "extractions",
        "industry": "manufacturing",
    },
    "SLIPL": {
        "gt_path": EXTRACTIONS_DIR / "SLIPL_classification_ground_truth.json",
        "gt_format": "extractions",
        "industry": "manufacturing",
    },
    "SR_Papers": {
        "gt_path": EXTRACTIONS_DIR / "SR_Papers_classification_ground_truth.json",
        "gt_format": "extractions",
        "industry": "manufacturing",
    },
    "SSSS": {
        "gt_path": EXTRACTIONS_DIR / "SSSS_classification_ground_truth.json",
        "gt_format": "extractions",
        "industry": "manufacturing",
    },
}


# ═════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def make_classifier():
    from app.services.classification.scoped_classifier import ScopedClassifier
    sc = ScopedClassifier()
    print(f"  [ScopedClassifier] sections={len(sc._contexts)} labels={len(sc._labels_by_row)}")
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


def doc_type_from_section(section: str, sheet_name: str = "", cma_row=None) -> str:
    """Infer document type."""
    combined = f"{section} {sheet_name}".lower()
    if any(kw in combined for kw in ["balance sheet", "bs", "assets", "liabilities", "equity"]):
        return "balance_sheet"
    if cma_row is not None and int(cma_row) >= 111:
        return "balance_sheet"
    return "profit_and_loss"


def load_gt(company: str, config: dict) -> list[dict]:
    """Load and normalize ground truth for a company."""
    gt_path = config["gt_path"]
    if not gt_path.exists():
        print(f"  WARNING: GT file not found: {gt_path}")
        return []

    with open(gt_path, encoding="utf-8") as f:
        data = json.load(f)

    if config["gt_format"] == "companies":
        entries = data.get("database_entries", [])
        return [{
            "raw_text": e.get("raw_text", ""),
            "section": e.get("section", ""),
            "amount": e.get("amount"),
            "cma_row": e.get("cma_row"),
            "cma_code": e.get("cma_code", ""),
            "cma_field_name": e.get("cma_field_name", ""),
            "industry_type": e.get("industry_type", config["industry"]),
            "financial_year": e.get("financial_year", ""),
            "sheet_name": e.get("sheet_name", ""),
        } for e in entries]
    else:
        items = data if isinstance(data, list) else data.get("items", [])
        return [{
            "raw_text": e.get("raw_text", ""),
            "section": e.get("section", ""),
            "amount": e.get("amount_rupees", e.get("amount")),
            "cma_row": e.get("correct_cma_row"),
            "cma_code": "",  # extractions GT doesn't have codes
            "cma_field_name": e.get("correct_cma_field", ""),
            "industry_type": config["industry"],
            "financial_year": e.get("financial_year", ""),
            "sheet_name": e.get("sheet_name", ""),
        } for e in items]


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 1: RUN ACCURACY TEST FOR ALL COMPANIES
# ═════════════════════════════════════════════════════════════════════════════

print("=" * 70)
print("  POST-CA-RULES ACCURACY BENCHMARK — ALL 9 COMPANIES")
print("=" * 70)
print()

# Load canonical labels for code-based comparison
with open(CANONICAL_LABELS_PATH) as f:
    _canonical = json.load(f)
sheetrow_to_code: dict[int, str] = {item["sheet_row"]: item["code"] for item in _canonical}
print(f"Loaded {len(sheetrow_to_code)} canonical label rows")

# Initialize classifier once
sc = make_classifier()
print()

all_summaries = []
all_wrong_entries: list[dict] = []

for company, config in COMPANIES.items():
    print(f"\n{'='*60}")
    print(f"  {company}")
    print(f"{'='*60}")

    entries = load_gt(company, config)
    if not entries:
        print(f"  SKIPPED (no GT data)")
        continue

    if len(entries) > MAX_ITEMS_PER_COMPANY:
        print(f"  Cost guard: capping at {MAX_ITEMS_PER_COMPANY} (GT has {len(entries)})")
        entries = entries[:MAX_ITEMS_PER_COMPANY]

    total = len(entries)
    print(f"  Items: {total}")

    results = []
    wrong_entries = []
    start = time.time()

    for i, entry in enumerate(entries):
        raw_text = entry["raw_text"]
        section = entry["section"]
        amount = entry["amount"]
        correct_row = entry["cma_row"]
        correct_code = entry.get("cma_code", "")
        correct_field = entry.get("cma_field_name", "")
        industry = entry.get("industry_type", config["industry"])
        doc_type = doc_type_from_section(section, entry.get("sheet_name", ""), correct_row)

        # Token budget guard
        if sc._total_tokens > TOKEN_REINIT_THRESHOLD:
            print(f"  [{i+1}] Token budget {sc._total_tokens:,} → reinitializing")
            sc = make_classifier()

        try:
            result = sc.classify_sync(
                raw_text=raw_text,
                amount=amount,
                section=section,
                industry_type=industry,
                document_type=doc_type,
                fuzzy_candidates=[],
            )
        except Exception as e:
            print(f"  [{i+1}] ERROR: {e}")
            result = _doubt_result(f"Exception: {e}")

        # Token-budget doubt → reinit + retry
        if result.is_doubt and result.doubt_reason and "token budget" in result.doubt_reason.lower():
            sc = make_classifier()
            try:
                result = sc.classify_sync(
                    raw_text=raw_text, amount=amount, section=section,
                    industry_type=industry, document_type=doc_type, fuzzy_candidates=[],
                )
            except Exception as e2:
                result = _doubt_result(f"Retry failed: {e2}")

        predicted_row = result.cma_row
        predicted_code = sheetrow_to_code.get(predicted_row) if predicted_row else None

        # Determine correctness: by code if available, else by field name, else by row
        if correct_code and predicted_code:
            is_correct = (not result.is_doubt) and (predicted_code == correct_code)
        elif correct_field and result.cma_field_name:
            is_correct = (not result.is_doubt) and (correct_field.strip().lower() == result.cma_field_name.strip().lower())
        else:
            is_correct = (not result.is_doubt) and (predicted_row == correct_row)

        results.append({"is_correct": is_correct, "is_doubt": result.is_doubt})

        if not is_correct:
            wrong_entries.append({
                "company": company,
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
                "industry_type": industry,
                "document_type": doc_type,
            })

        # Progress every 25 items
        if (i + 1) % 25 == 0:
            elapsed = time.time() - start
            n = i + 1
            correct_n = sum(r["is_correct"] for r in results)
            acc = correct_n / n * 100
            print(f"  [{n:3d}/{total}] acc={acc:.1f}% tokens={sc._total_tokens:,} elapsed={elapsed:.0f}s")
            sys.stdout.flush()

    # Final stats for this company
    elapsed = time.time() - start
    correct = sum(r["is_correct"] for r in results)
    doubts = sum(r["is_doubt"] for r in results)
    wrong = total - correct - doubts
    accuracy_pct = round(correct / total * 100, 2) if total else 0

    summary = {
        "company": company,
        "industry": config["industry"],
        "total_items": total,
        "correct": correct,
        "wrong": wrong,
        "doubts": doubts,
        "accuracy_pct": accuracy_pct,
        "elapsed_seconds": round(elapsed, 2),
    }
    all_summaries.append(summary)
    all_wrong_entries.extend(wrong_entries)

    # Save per-company results
    with open(OUTPUT_DIR / f"{company}_accuracy_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    with open(OUTPUT_DIR / f"{company}_wrong_entries.json", "w") as f:
        json.dump(wrong_entries, f, indent=2)

    print(f"\n  {company}: {correct}/{total} correct ({accuracy_pct}%)  wrong={wrong} doubt={doubts}  {elapsed:.0f}s")


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 2: BEFORE/AFTER COMPARISON
# ═════════════════════════════════════════════════════════════════════════════

print(f"\n\n{'='*70}")
print("  BEFORE vs AFTER COMPARISON")
print(f"{'='*70}\n")

comparison = []
for s in all_summaries:
    company = s["company"]
    baseline_file = BASELINE_DIR / f"{company}_accuracy_summary.json"
    before = {"accuracy_pct": "N/A", "correct": "?", "wrong": "?", "doubts": "?", "total_items": "?"}
    if baseline_file.exists():
        with open(baseline_file) as f:
            before = json.load(f)

    before_acc = before.get("accuracy_pct", 0) or 0
    after_acc = s["accuracy_pct"]
    delta = after_acc - before_acc if isinstance(before_acc, (int, float)) else "N/A"

    comparison.append({
        "company": company,
        "before_accuracy": before_acc,
        "after_accuracy": after_acc,
        "delta": delta,
        "before_correct": before.get("correct", "?"),
        "after_correct": s["correct"],
        "before_wrong": before.get("wrong", "?"),
        "after_wrong": s["wrong"],
        "total": s["total_items"],
    })

# Print comparison table
print(f"{'Company':<20} {'Before':>8} {'After':>8} {'Delta':>8} {'Correct':>10} {'Wrong':>10}")
print("-" * 70)
total_before_correct = 0
total_after_correct = 0
total_items = 0
for c in comparison:
    delta_str = f"+{c['delta']:.1f}" if isinstance(c['delta'], float) and c['delta'] > 0 else f"{c['delta']}"
    print(f"{c['company']:<20} {c['before_accuracy']:>7}% {c['after_accuracy']:>7}% {delta_str:>8} {c['before_correct']:>4}→{c['after_correct']:<4} {c['before_wrong']:>4}→{c['after_wrong']:<4}")
    if isinstance(c['before_correct'], int):
        total_before_correct += c['before_correct']
    if isinstance(c['after_correct'], int):
        total_after_correct += c['after_correct']
    total_items += c['total']

print("-" * 70)
before_total_acc = total_before_correct / total_items * 100 if total_items else 0
after_total_acc = total_after_correct / total_items * 100 if total_items else 0
print(f"{'OVERALL':<20} {before_total_acc:>7.1f}% {after_total_acc:>7.1f}% {after_total_acc-before_total_acc:>+7.1f} {total_before_correct:>4}→{total_after_correct:<4} items={total_items}")

# Save comparison
with open(OUTPUT_DIR / "comparison_report.json", "w") as f:
    json.dump({"comparison": comparison, "all_summaries": all_summaries}, f, indent=2)

print(f"\nComparison saved → {OUTPUT_DIR / 'comparison_report.json'}")


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 3: INTERVIEW WRONG ITEMS
# ═════════════════════════════════════════════════════════════════════════════

print(f"\n\n{'='*70}")
print("  INTERVIEW — WHY DID WRONG ITEMS GO WRONG?")
print(f"{'='*70}\n")

# Filter out GT offset bugs (same field name = not a real error)
genuinely_wrong = []
offset_bug = []

for item in all_wrong_entries:
    correct_field = (item.get("correct_cma_field") or "").strip().lower()
    predicted_field = (item.get("predicted_cma_field") or "").strip().lower()

    if item.get("is_doubt"):
        genuinely_wrong.append(item)
    elif correct_field and predicted_field and correct_field == predicted_field:
        offset_bug.append(item)
    else:
        genuinely_wrong.append(item)

print(f"Total wrong entries:        {len(all_wrong_entries)}")
print(f"GT offset bug (same field): {len(offset_bug)}")
print(f"Genuinely wrong:            {len(genuinely_wrong)}")

# Deduplicate
seen: set[tuple] = set()
unique_wrong: list[dict] = []
for item in genuinely_wrong:
    key = (
        item["raw_text"].strip().lower(),
        (item.get("correct_cma_field") or "").lower(),
        (item.get("predicted_cma_field") or "").lower(),
    )
    if key not in seen:
        seen.add(key)
        unique_wrong.append(item)

print(f"Unique genuinely wrong:     {len(unique_wrong)}")
print()

# Initialize interview
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

interview_results: list[dict] = []
api_calls = 0
interview_start = time.time()

for i, item in enumerate(unique_wrong[:MAX_INTERVIEWS]):
    raw_text = item["raw_text"]
    section = item.get("section", "")
    amount = item.get("amount")
    predicted_row = item.get("predicted_cma_row")
    doc_type = item.get("document_type", "profit_and_loss")

    # Adjust row for GT offset (BCIPL rows are already correct, others need +1)
    correct_row_raw = item["correct_cma_row"]
    if item.get("company") == "BCIPL":
        correct_row = correct_row_raw
    else:
        correct_row = correct_row_raw + 1 if correct_row_raw else correct_row_raw

    # Get field names
    correct_name = sc._labels_by_row.get(correct_row, {}).get("name", f"Row {correct_row}")
    predicted_name = (
        sc._labels_by_row.get(predicted_row, {}).get("name", f"Row {predicted_row}")
        if predicted_row else "DOUBT"
    )

    # Rebuild the routing
    sections = sc._route_section(raw_text, section or "", doc_type)
    if len(sections) == 1:
        context = sc._contexts.get(sections[0]) or sc._contexts["admin_expense"]
    else:
        context = sc._merge_contexts(sections)
    original_prompt = sc._build_prompt(raw_text, amount, section or "not specified", context)

    available_rows = [r["sheet_row"] for r in context.cma_rows]
    correct_in_list = correct_row in available_rows

    interview_q = f"""You classified this financial line item:
"{raw_text}" (section: "{section}", amount: {amount})

You chose: Row {predicted_row} ({predicted_name})
The CORRECT answer is: Row {correct_row} ({correct_name})
Was Row {correct_row} in the options you were shown? {"YES" if correct_in_list else "NO — it was NOT in your options"}

Here was the full prompt you received:
---
{original_prompt}
---

Answer ALL of these:

PART A — Why it went wrong:
1. Was Row {correct_row} ({correct_name}) in the POSSIBLE CMA ROWS list? (Yes/No)
2. If yes: why did you pick Row {predicted_row} instead?
3. If no: what keywords in the item text should have triggered routing to the correct section?

PART B — What would make you get it RIGHT:
4. Write the EXACT minimum change to the prompt that would make you confidently pick Row {correct_row}.
5. If you had to write ONE routing regex pattern that would correctly route this item, what would it be?

Be specific and actionable. Max 200 words."""

    try:
        resp = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[{"role": "user", "content": interview_q}],
            max_tokens=250,
            temperature=0.0,
        )
        answer = resp.choices[0].message.content.strip()
        api_calls += 1
    except Exception as e:
        answer = f"ERROR: {e}"

    interview_results.append({
        "index": i,
        "company": item.get("company", "unknown"),
        "raw_text": raw_text,
        "section": section,
        "correct_row_adjusted": correct_row,
        "correct_name": correct_name,
        "predicted_row": predicted_row,
        "predicted_name": predicted_name,
        "correct_row_in_options": correct_in_list,
        "routed_to": sections,
        "classification_method": item.get("classification_method", ""),
        "model_response": answer,
    })

    status = "IN_LIST" if correct_in_list else "NOT_IN_LIST"
    print(
        f"[{i+1}/{min(len(unique_wrong), MAX_INTERVIEWS)}] {status} | "
        f"'{raw_text[:50]}' | correct={correct_row} pred={predicted_row} | {item.get('company','?')}"
    )
    sys.stdout.flush()

# ═════════════════════════════════════════════════════════════════════════════
# PHASE 4: SAVE INTERVIEW RESULTS + REPORT
# ═════════════════════════════════════════════════════════════════════════════

not_in_list = sum(1 for r in interview_results if not r["correct_row_in_options"])
in_list_wrong = sum(1 for r in interview_results if r["correct_row_in_options"])

print(f"\n{'='*60}")
print(f"INTERVIEW SUMMARY")
print(f"{'='*60}")
print(f"Total wrong (all companies):  {len(all_wrong_entries)}")
print(f"GT offset bug (field match):  {len(offset_bug)}")
print(f"Genuinely wrong:              {len(genuinely_wrong)}")
print(f"Unique genuinely wrong:       {len(unique_wrong)}")
print(f"Interviewed:                  {len(interview_results)}")
print(f"Correct row NOT in list:      {not_in_list} — ROUTING BUG")
print(f"Correct row IN list:          {in_list_wrong} — MODEL ERROR")
print(f"Elapsed:                      {time.time()-interview_start:.0f}s")

# Save JSON
output = {
    "summary": {
        "total_wrong_all_companies": len(all_wrong_entries),
        "gt_offset_bug": len(offset_bug),
        "genuinely_wrong": len(genuinely_wrong),
        "unique_genuinely_wrong": len(unique_wrong),
        "interviewed": len(interview_results),
        "correct_not_in_options": not_in_list,
        "correct_in_options_but_wrong": in_list_wrong,
        "api_calls": api_calls,
    },
    "interviews": interview_results,
}

with open(OUTPUT_DIR / "INTERVIEW_RESULTS.json", "w") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

# Save markdown report
lines = [
    "# Post-CA-Rules: Interview Report — Genuinely Wrong Items",
    "",
    f"**Date:** {time.strftime('%Y-%m-%d %H:%M')}",
    f"**Context:** After implementing 24 CA-verified rules (CA-001 to CA-024)",
    "",
    "## Accuracy Comparison (Before → After CA Rules)",
    "",
    "| Company | Before | After | Delta | Items |",
    "|---------|--------|-------|-------|-------|",
]

for c in comparison:
    delta_str = f"+{c['delta']:.1f}" if isinstance(c['delta'], float) and c['delta'] > 0 else f"{c['delta']}"
    lines.append(f"| {c['company']} | {c['before_accuracy']}% | {c['after_accuracy']}% | {delta_str}% | {c['total']} |")

lines += [
    "",
    f"**Overall:** {before_total_acc:.1f}% → {after_total_acc:.1f}% ({after_total_acc-before_total_acc:+.1f}pp)",
    "",
    "## Interview Summary",
    "",
    f"- **Total wrong entries:** {len(all_wrong_entries)}",
    f"- **GT offset bugs (not real errors):** {len(offset_bug)}",
    f"- **Genuinely wrong:** {len(genuinely_wrong)}",
    f"- **Unique (deduplicated):** {len(unique_wrong)}",
    f"- **Interviewed:** {len(interview_results)}",
    "",
    "## Root Cause Split",
    "",
    f"- **Routing bug** (correct row not in options): {not_in_list}",
    f"- **Model error** (correct row available, picked wrong): {in_list_wrong}",
    "",
    "## Routing Bugs (correct row NOT in options)",
    "",
    "| # | Item | Company | Correct Row | Predicted Row | Routed To |",
    "|---|------|---------|-------------|---------------|-----------|",
]

for r in interview_results:
    if not r["correct_row_in_options"]:
        lines.append(
            f"| {r['index']+1} | {r['raw_text'][:40]} | {r['company']} | "
            f"R{r['correct_row_adjusted']} ({r['correct_name'][:20]}) | "
            f"R{r['predicted_row']} ({r['predicted_name'][:20]}) | "
            f"{','.join(r['routed_to'])} |"
        )

lines += [
    "",
    "## Model Errors (correct row available, wrong pick)",
    "",
    "| # | Item | Company | Correct | Predicted | Method |",
    "|---|------|---------|---------|-----------|--------|",
]

for r in interview_results:
    if r["correct_row_in_options"]:
        lines.append(
            f"| {r['index']+1} | {r['raw_text'][:35]} | {r['company']} | "
            f"R{r['correct_row_adjusted']} | R{r['predicted_row']} | "
            f"{r.get('classification_method', '')} |"
        )

lines += [
    "",
    "## Full Interview Responses",
    "",
]

for r in interview_results:
    lines += [
        f"### {r['index']+1}. `{r['raw_text'][:60]}` ({r['company']})",
        f"- Correct: Row {r['correct_row_adjusted']} ({r['correct_name']})",
        f"- Predicted: Row {r['predicted_row']} ({r['predicted_name']})",
        f"- Correct in options: {'Yes' if r['correct_row_in_options'] else 'NO'}",
        f"- Routed to: {', '.join(r['routed_to'])}",
        f"- Method: {r.get('classification_method', 'unknown')}",
        "",
        f"**AI Response:**",
        f"```",
        r["model_response"],
        f"```",
        "",
    ]

with open(OUTPUT_DIR / "INTERVIEW_REPORT.md", "w") as f:
    f.write("\n".join(lines))

print(f"\nAll files saved to: {OUTPUT_DIR}")
print(f"  - comparison_report.json")
print(f"  - *_accuracy_summary.json (per company)")
print(f"  - *_wrong_entries.json (per company)")
print(f"  - INTERVIEW_RESULTS.json")
print(f"  - INTERVIEW_REPORT.md")
print(f"\nDone!")
