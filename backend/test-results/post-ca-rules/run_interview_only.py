#!/usr/bin/env python3
"""
Post-CA-Rules Interview — Why did wrong items go wrong?

Reads wrong_entries from the post-ca-rules accuracy test (BCIPL, Dynamic_Air,
Mehta_Computer), filters GT offset bugs, deduplicates, then interviews
DeepSeek V3 about each genuinely wrong item.

Run: docker compose exec -T worker bash -c "cd /app && python test-results/post-ca-rules/run_interview_only.py"
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, "/app")

RESULTS_DIR = Path("/app/test-results/post-ca-rules")
BASELINE_DIR = Path("/app/test-results")

# ─── Cost guard ───────────────────────────────────────────────────────────────
MAX_INTERVIEWS = 100

# ═══════════════════════════════════════════════════════════════════════════════
# 1. LOAD ALL WRONG ENTRIES
# ═══════════════════════════════════════════════════════════════════════════════

print("=" * 70)
print("  POST-CA INTERVIEW — Why Did Wrong Items Go Wrong?")
print("=" * 70)
print()

wrong_files = sorted(RESULTS_DIR.glob("*_wrong_entries.json"))
all_wrong: list[dict] = []
for f in wrong_files:
    with open(f, encoding="utf-8") as fh:
        entries = json.load(fh)
        all_wrong.extend(entries)
    print(f"  {f.name}: {len(entries)} items")

print(f"\nTotal wrong entries: {len(all_wrong)}")

# ═══════════════════════════════════════════════════════════════════════════════
# 2. FILTER GT OFFSET BUGS + DEDUPLICATE
# ═══════════════════════════════════════════════════════════════════════════════

genuinely_wrong = []
offset_bug = []

for item in all_wrong:
    correct_field = (item.get("correct_cma_field") or "").strip().lower()
    predicted_field = (item.get("predicted_cma_field") or "").strip().lower()

    if item.get("is_doubt"):
        genuinely_wrong.append(item)
    elif correct_field and predicted_field and correct_field == predicted_field:
        offset_bug.append(item)
    else:
        genuinely_wrong.append(item)

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

# ═══════════════════════════════════════════════════════════════════════════════
# 3. BEFORE vs AFTER SUMMARY (quick table from saved results)
# ═══════════════════════════════════════════════════════════════════════════════

print("─" * 60)
print("ACCURACY COMPARISON (Before CA Rules → After CA Rules)")
print("─" * 60)

comparison = []
for sf in sorted(RESULTS_DIR.glob("*_accuracy_summary.json")):
    with open(sf) as f:
        after = json.load(f)
    company = after["company"]
    bf = BASELINE_DIR / f"{company}_accuracy_summary.json"
    before = {}
    if bf.exists():
        with open(bf) as f:
            before = json.load(f)

    before_acc = before.get("accuracy_pct", 0) or 0
    after_acc = after.get("accuracy_pct", 0) or 0
    delta = after_acc - before_acc

    comparison.append({
        "company": company,
        "before": before_acc,
        "after": after_acc,
        "delta": delta,
        "before_correct": before.get("correct", "?"),
        "after_correct": after.get("correct", "?"),
        "total": after.get("total_items", "?"),
    })
    delta_s = f"+{delta:.1f}" if delta > 0 else f"{delta:.1f}"
    print(f"  {company:<20} {before_acc:>6}% → {after_acc:>6}%  ({delta_s}pp)  [{after.get('correct','?')}/{after.get('total_items','?')} correct]")

print()

# ═══════════════════════════════════════════════════════════════════════════════
# 4. INTERVIEW — Ask DeepSeek V3 about each wrong item
# ═══════════════════════════════════════════════════════════════════════════════

print("=" * 70)
print("  INTERVIEWING AI ON WRONG CLASSIFICATIONS")
print("=" * 70)
print()

from app.services.classification.scoped_classifier import ScopedClassifier
from openai import OpenAI

sc = ScopedClassifier()
print(f"ScopedClassifier: {len(sc._contexts)} sections, {len(sc._labels_by_row)} labels")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

interview_results: list[dict] = []
api_calls = 0
start_time = time.time()

for i, item in enumerate(unique_wrong[:MAX_INTERVIEWS]):
    raw_text = item["raw_text"]
    section = item.get("section", "")
    amount = item.get("amount")
    predicted_row = item.get("predicted_cma_row")
    doc_type = item.get("document_type", "profit_and_loss")
    company = item.get("company", "unknown")

    # Adjust for GT offset (BCIPL rows already correct, others +1)
    correct_row_raw = item["correct_cma_row"]
    if company == "BCIPL":
        correct_row = correct_row_raw
    else:
        correct_row = (correct_row_raw + 1) if correct_row_raw else correct_row_raw

    # Get field names from classifier label map
    correct_name = sc._labels_by_row.get(correct_row, {}).get("name", f"Row {correct_row}")
    predicted_name = (
        sc._labels_by_row.get(predicted_row, {}).get("name", f"Row {predicted_row}")
        if predicted_row else "DOUBT"
    )

    # Rebuild routing to check if correct row was available
    sections_routed = sc._route_section(raw_text, section or "", doc_type)
    if len(sections_routed) == 1:
        context = sc._contexts.get(sections_routed[0]) or sc._contexts["admin_expense"]
    else:
        context = sc._merge_contexts(sections_routed)
    original_prompt = sc._build_prompt(raw_text, amount, section or "not specified", context)

    available_rows = [r["sheet_row"] for r in context.cma_rows]
    correct_in_list = correct_row in available_rows

    # Build interview question
    interview_q = f"""You classified this financial line item:
"{raw_text}" (section: "{section}", amount: {amount}, company type: {item.get('industry_type', 'unknown')})

You chose: Row {predicted_row} ({predicted_name})
The CORRECT answer is: Row {correct_row} ({correct_name})
Was Row {correct_row} in the options you were shown? {"YES" if correct_in_list else "NO — it was NOT in your options"}

Here was the full prompt you received:
---
{original_prompt}
---

Answer ALL of these:

PART A — Root Cause:
1. Was Row {correct_row} ({correct_name}) in the POSSIBLE CMA ROWS list? (Yes/No)
2. If YES: why did you pick Row {predicted_row} instead? What was ambiguous?
3. If NO: what keyword/section should have routed this item to include Row {correct_row}?

PART B — Fix:
4. What is the EXACT minimum change needed to make you pick Row {correct_row} confidently?
   Examples: "Add a rule: X → Row Y", "Change routing pattern", "Add Row Y to options"
5. Write ONE Python regex pattern that would correctly route this item to the right CMA section.

PART C — Classification:
6. Is this a ROUTING BUG (correct row not shown) or MODEL ERROR (correct row shown, wrong pick)?
7. Confidence you'd get it right with the fix from #4: (0-100%)

Be specific. Max 200 words."""

    try:
        resp = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[{"role": "user", "content": interview_q}],
            max_tokens=300,
            temperature=0.0,
        )
        answer = resp.choices[0].message.content.strip()
        api_calls += 1
    except Exception as e:
        answer = f"ERROR: {e}"

    # Parse error type from response
    error_type = "routing_bug" if not correct_in_list else "model_error"

    interview_results.append({
        "index": i,
        "company": company,
        "raw_text": raw_text,
        "section": section,
        "amount": amount,
        "industry_type": item.get("industry_type", ""),
        "correct_row": correct_row,
        "correct_name": correct_name,
        "predicted_row": predicted_row,
        "predicted_name": predicted_name,
        "correct_in_options": correct_in_list,
        "error_type": error_type,
        "routed_to": sections_routed,
        "classification_method": item.get("classification_method", ""),
        "confidence": item.get("confidence", 0),
        "model_response": answer,
    })

    print(
        f"[{i+1}/{min(len(unique_wrong), MAX_INTERVIEWS)}] "
        f"{error_type.upper():>12} | {company:<15} | "
        f"'{raw_text[:45]}' | correct=R{correct_row} pred=R{predicted_row}"
    )
    sys.stdout.flush()

# ═══════════════════════════════════════════════════════════════════════════════
# 5. ANALYZE + SAVE RESULTS
# ═══════════════════════════════════════════════════════════════════════════════

routing_bugs = [r for r in interview_results if r["error_type"] == "routing_bug"]
model_errors = [r for r in interview_results if r["error_type"] == "model_error"]

elapsed = time.time() - start_time

print(f"\n{'='*70}")
print(f"  INTERVIEW SUMMARY")
print(f"{'='*70}")
print(f"  Total wrong (3 companies):    {len(all_wrong)}")
print(f"  GT offset bugs filtered:      {len(offset_bug)}")
print(f"  Genuinely wrong:              {len(genuinely_wrong)}")
print(f"  Unique (deduplicated):        {len(unique_wrong)}")
print(f"  Interviewed:                  {len(interview_results)}")
print(f"  ├─ Routing bugs:              {len(routing_bugs)} ({len(routing_bugs)/max(len(interview_results),1)*100:.0f}%)")
print(f"  └─ Model errors:              {len(model_errors)} ({len(model_errors)/max(len(interview_results),1)*100:.0f}%)")
print(f"  API calls:                    {api_calls}")
print(f"  Elapsed:                      {elapsed:.0f}s")

# ── Save JSON ────────────────────────────────────────────────────────────────
output = {
    "meta": {
        "date": time.strftime("%Y-%m-%d %H:%M"),
        "context": "Post CA-rules implementation (CA-001 to CA-024)",
        "companies_tested": [c["company"] for c in comparison],
    },
    "accuracy_comparison": comparison,
    "interview_summary": {
        "total_wrong": len(all_wrong),
        "gt_offset_bugs": len(offset_bug),
        "genuinely_wrong": len(genuinely_wrong),
        "unique_wrong": len(unique_wrong),
        "interviewed": len(interview_results),
        "routing_bugs": len(routing_bugs),
        "model_errors": len(model_errors),
    },
    "interviews": interview_results,
}

with open(RESULTS_DIR / "INTERVIEW_RESULTS.json", "w") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

# ── Save Markdown Report ─────────────────────────────────────────────────────
lines = [
    "# Post-CA Interview Report — Why Wrong Items Go Wrong",
    "",
    f"**Date:** {time.strftime('%Y-%m-%d %H:%M')}",
    f"**Context:** After implementing 24 CA-verified classification rules",
    "",
    "---",
    "",
    "## 1. Accuracy Comparison (Before → After CA Rules)",
    "",
    "| Company | Before | After | Delta | Correct/Total |",
    "|---------|--------|-------|-------|---------------|",
]

for c in comparison:
    delta_s = f"+{c['delta']:.1f}" if c['delta'] > 0 else f"{c['delta']:.1f}"
    lines.append(f"| {c['company']} | {c['before']}% | {c['after']}% | {delta_s}pp | {c['after_correct']}/{c['total']} |")

lines += [
    "",
    "---",
    "",
    "## 2. Interview Summary",
    "",
    f"- **Total wrong entries (3 companies):** {len(all_wrong)}",
    f"- **GT offset bugs (not real errors):** {len(offset_bug)}",
    f"- **Genuinely wrong:** {len(genuinely_wrong)}",
    f"- **Unique (deduplicated):** {len(unique_wrong)}",
    f"- **Interviewed:** {len(interview_results)}",
    "",
    "### Root Cause Split",
    "",
    f"| Type | Count | % | Meaning |",
    f"|------|-------|---|---------|",
    f"| **Routing Bug** | {len(routing_bugs)} | {len(routing_bugs)/max(len(interview_results),1)*100:.0f}% | Correct CMA row was NOT shown to the AI |",
    f"| **Model Error** | {len(model_errors)} | {len(model_errors)/max(len(interview_results),1)*100:.0f}% | Correct row WAS available, AI picked wrong |",
    "",
    "---",
    "",
    "## 3. Routing Bugs — Correct Row Not In Options",
    "",
    "These items were routed to the wrong CMA section, so the AI never had a chance to pick correctly.",
    "",
    "| # | Item | Company | Correct Row | Predicted Row | Routed To |",
    "|---|------|---------|-------------|---------------|-----------|",
]

for r in routing_bugs:
    lines.append(
        f"| {r['index']+1} | {r['raw_text'][:40]} | {r['company']} | "
        f"R{r['correct_row']} ({r['correct_name'][:25]}) | "
        f"R{r['predicted_row']} ({r['predicted_name'][:25]}) | "
        f"{', '.join(r['routed_to'])} |"
    )

lines += [
    "",
    "---",
    "",
    "## 4. Model Errors — Correct Row Available, Wrong Pick",
    "",
    "The AI had the correct option but chose differently.",
    "",
    "| # | Item | Company | Correct | Predicted | Method | Conf |",
    "|---|------|---------|---------|-----------|--------|------|",
]

for r in model_errors:
    lines.append(
        f"| {r['index']+1} | {r['raw_text'][:35]} | {r['company']} | "
        f"R{r['correct_row']} ({r['correct_name'][:20]}) | "
        f"R{r['predicted_row']} ({r['predicted_name'][:20]}) | "
        f"{r.get('classification_method', '')} | {r.get('confidence', 0):.2f} |"
    )

lines += [
    "",
    "---",
    "",
    "## 5. Full Interview Responses",
    "",
]

for r in interview_results:
    lines += [
        f"### {r['index']+1}. `{r['raw_text'][:60]}` ({r['company']})",
        f"- **Error Type:** {r['error_type'].replace('_', ' ').title()}",
        f"- **Correct:** Row {r['correct_row']} ({r['correct_name']})",
        f"- **Predicted:** Row {r['predicted_row']} ({r['predicted_name']})",
        f"- **Correct in options:** {'Yes' if r['correct_in_options'] else 'NO'}",
        f"- **Routed to:** {', '.join(r['routed_to'])}",
        f"- **Method:** {r.get('classification_method', 'unknown')}",
        f"- **Industry:** {r.get('industry_type', 'unknown')}",
        "",
        "**AI Response:**",
        "```",
        r["model_response"],
        "```",
        "",
        "---",
        "",
    ]

# ── Actionable fix suggestions ───────────────────────────────────────────────
lines += [
    "## 6. Extracted Fix Suggestions",
    "",
    "Concrete changes suggested by the AI to fix each wrong classification.",
    "",
]

fix_suggestions = []
for r in interview_results:
    resp = r.get("model_response", "")
    for line in resp.split("\n"):
        line = line.strip()
        if any(kw in line.lower() for kw in [
            "add row", "add a rule", "add an example", "change the routing",
            "regex", "pattern", "→", "->",
        ]):
            fix_suggestions.append({
                "item": r["raw_text"][:50],
                "company": r["company"],
                "correct": f"R{r['correct_row']} ({r['correct_name']})",
                "fix": line,
                "type": r["error_type"],
            })

for fs in fix_suggestions:
    lines.append(f"- **{fs['item']}** ({fs['company']}) → {fs['correct']} [{fs['type']}]")
    lines.append(f"  - {fs['fix']}")
    lines.append("")

if not fix_suggestions:
    lines.append("(No structured fix suggestions extracted — see full responses above)")

with open(RESULTS_DIR / "INTERVIEW_REPORT.md", "w") as f:
    f.write("\n".join(lines))

print(f"\nFiles saved:")
print(f"  {RESULTS_DIR / 'INTERVIEW_RESULTS.json'}")
print(f"  {RESULTS_DIR / 'INTERVIEW_REPORT.md'}")
print("\nDone!")
