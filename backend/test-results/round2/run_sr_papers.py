#!/usr/bin/env python3
"""
Round 2 Accuracy Test + Interview — SR_Papers (Manufacturing)

Runs classification accuracy against CA-verified GT, then interviews
DeepSeek V3 about genuinely wrong items to categorize root causes.

Run:
    docker compose exec -T worker bash -c "cd /app && python test-results/round2/run_sr_papers.py"

Outputs (all in /app/test-results/round2/):
    SR_Papers_accuracy_summary.json
    SR_Papers_wrong_entries.json
    SR_Papers_interview.json
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, "/app")

# ─── Paths ────────────────────────────────────────────────────────────────────
GT_PATH = Path("/app/DOCS/extractions/SR_Papers_classification_ground_truth.json")
CANONICAL_LABELS_PATH = Path("/app/CMA_Ground_Truth_v1/reference/canonical_labels.json")
ROUND1_SUMMARY_PATH = Path("/app/test-results/post-ca-rules/SR_Papers_accuracy_summary.json")

OUTPUT_DIR = Path("/app/test-results/round2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── Cost guards ──────────────────────────────────────────────────────────────
MAX_ITEMS = 500
MAX_TOKENS = 500_000
TOKEN_REINIT_THRESHOLD = 450_000
MAX_INTERVIEWS = 50

COMPANY = "SR_Papers"
INDUSTRY = "manufacturing"

print("=" * 70)
print("  ROUND 2 ACCURACY TEST — SR_Papers (Manufacturing)")
print("=" * 70)
print()

# ─── Load canonical labels for row→code lookup ────────────────────────────────
with open(CANONICAL_LABELS_PATH) as f:
    _canonical = json.load(f)
sheetrow_to_code: dict[int, str] = {item["sheet_row"]: item["code"] for item in _canonical}
print(f"Loaded {len(sheetrow_to_code)} canonical label rows")

# ─── Load Ground Truth ────────────────────────────────────────────────────────
with open(GT_PATH, encoding="utf-8") as f:
    gt_raw = json.load(f)

# GT is a list directly or wrapped in "items"
items_raw = gt_raw if isinstance(gt_raw, list) else gt_raw.get("items", [])

entries = [{
    "raw_text": e.get("raw_text", ""),
    "section": e.get("section", ""),
    "amount": e.get("amount_rupees", e.get("amount")),
    "cma_row": e.get("correct_cma_row"),
    "cma_field_name": e.get("correct_cma_field", ""),
    "financial_year": e.get("financial_year", ""),
    "sheet_name": e.get("sheet_name", ""),
} for e in items_raw]

print(f"GT items loaded: {len(entries)}")

if len(entries) > MAX_ITEMS:
    print(f"Cost guard: capping at {MAX_ITEMS} (GT has {len(entries)})")
    entries = entries[:MAX_ITEMS]

total = len(entries)
print(f"Running on: {total} items")
print()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def doc_type_from_section(section: str, sheet_name: str = "", cma_row=None) -> str:
    """Infer document type from section/sheet_name/row number."""
    combined = f"{section} {sheet_name}".lower()
    if any(kw in combined for kw in ["balance sheet", " bs ", "assets", "liabilities", "equity"]):
        return "balance_sheet"
    if cma_row is not None and int(cma_row) >= 111:
        return "balance_sheet"
    return "profit_and_loss"


def make_classifier():
    from app.services.classification.scoped_classifier import ScopedClassifier
    sc = ScopedClassifier()
    print(f"  [ScopedClassifier] sections={len(sc._contexts)} labels={len(sc._labels_by_row)}")
    return sc


def doubt_result(reason: str):
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
# PHASE 1: RUN ACCURACY TEST
# ═════════════════════════════════════════════════════════════════════════════

print(f"{'─'*60}")
print("  PHASE 1: Running classification on all items")
print(f"{'─'*60}")

sc = make_classifier()
print()

results = []
wrong_entries = []
start = time.time()

for i, entry in enumerate(entries):
    raw_text = entry["raw_text"]
    section = entry["section"]
    amount = entry["amount"]
    correct_row = entry["cma_row"]
    correct_field = entry["cma_field_name"]
    doc_type = doc_type_from_section(section, entry.get("sheet_name", ""), correct_row)

    # Token budget guard — reinitialize classifier if approaching limit
    if sc._total_tokens > TOKEN_REINIT_THRESHOLD:
        print(f"  [{i+1}] Token budget {sc._total_tokens:,} → reinitializing classifier")
        sc = make_classifier()

    # Hard token cap
    if sc._total_tokens > MAX_TOKENS:
        print(f"  COST GUARD: exceeded {MAX_TOKENS:,} tokens — stopping at item {i+1}")
        break

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
        print(f"  [{i+1}] ERROR: {e}")
        result = doubt_result(f"Exception: {e}")

    # Retry if token budget exceeded inside the call
    if result.is_doubt and result.doubt_reason and "token budget" in (result.doubt_reason or "").lower():
        sc = make_classifier()
        try:
            result = sc.classify_sync(
                raw_text=raw_text, amount=amount, section=section,
                industry_type=INDUSTRY, document_type=doc_type, fuzzy_candidates=[],
            )
        except Exception as e2:
            result = doubt_result(f"Retry failed: {e2}")

    predicted_row = result.cma_row
    predicted_code = sheetrow_to_code.get(predicted_row) if predicted_row else None

    # Correctness: by field name (extractions GT has no codes)
    if correct_field and result.cma_field_name:
        is_correct = (not result.is_doubt) and (
            correct_field.strip().lower() == result.cma_field_name.strip().lower()
        )
    else:
        is_correct = (not result.is_doubt) and (predicted_row == correct_row)

    results.append({"is_correct": is_correct, "is_doubt": result.is_doubt})

    if not is_correct:
        wrong_entries.append({
            "company": COMPANY,
            "raw_text": raw_text,
            "section": section,
            "amount": amount,
            "correct_cma_row": correct_row,
            "correct_cma_code": "",
            "correct_cma_field": correct_field,
            "predicted_cma_row": predicted_row,
            "predicted_cma_code": predicted_code,
            "predicted_cma_field": result.cma_field_name,
            "confidence": result.confidence,
            "is_doubt": result.is_doubt,
            "doubt_reason": result.doubt_reason,
            "classification_method": result.classification_method,
            "industry_type": INDUSTRY,
            "document_type": doc_type,
            "financial_year": entry.get("financial_year", ""),
        })

    if (i + 1) % 25 == 0:
        elapsed = time.time() - start
        n = i + 1
        correct_n = sum(r["is_correct"] for r in results)
        acc = correct_n / n * 100
        print(f"  [{n:3d}/{total}] acc={acc:.1f}%  tokens={sc._total_tokens:,}  elapsed={elapsed:.0f}s")
        sys.stdout.flush()

# ─── Final stats ──────────────────────────────────────────────────────────────
elapsed = time.time() - start
correct = sum(r["is_correct"] for r in results)
doubts = sum(r["is_doubt"] for r in results)
wrong = len(results) - correct - doubts
accuracy_pct = round(correct / len(results) * 100, 2) if results else 0

# Load Round 1 baseline
round1_acc = 31.48
round1_correct = 68
round1_total = 216
if ROUND1_SUMMARY_PATH.exists():
    with open(ROUND1_SUMMARY_PATH) as f:
        r1 = json.load(f)
    round1_acc = r1.get("accuracy_pct", 31.48)
    round1_correct = r1.get("correct", 68)
    round1_total = r1.get("total_items", 216)

delta = round(accuracy_pct - round1_acc, 2)
delta_str = f"+{delta:.2f}" if delta > 0 else f"{delta:.2f}"

summary = {
    "company": COMPANY,
    "industry": INDUSTRY,
    "round": 2,
    "total_items": len(results),
    "correct": correct,
    "wrong": wrong,
    "doubts": doubts,
    "accuracy_pct": accuracy_pct,
    "round1_accuracy_pct": round1_acc,
    "delta_pp": delta,
    "elapsed_seconds": round(elapsed, 2),
    "tokens_used": sc._total_tokens,
    "date": time.strftime("%Y-%m-%d %H:%M"),
}

print(f"\n{'='*60}")
print(f"  PHASE 1 RESULTS")
print(f"{'='*60}")
print(f"  Items:       {len(results)}")
print(f"  Correct:     {correct} ({accuracy_pct:.2f}%)")
print(f"  Wrong:       {wrong}")
print(f"  Doubts:      {doubts}")
print(f"  Round 1:     {round1_correct}/{round1_total} ({round1_acc:.2f}%)")
print(f"  Delta:       {delta_str}pp")
print(f"  Tokens used: {sc._total_tokens:,}")
print(f"  Elapsed:     {elapsed:.0f}s")

with open(OUTPUT_DIR / "SR_Papers_accuracy_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
with open(OUTPUT_DIR / "SR_Papers_wrong_entries.json", "w") as f:
    json.dump(wrong_entries, f, indent=2)

print(f"\n  Saved → {OUTPUT_DIR / 'SR_Papers_accuracy_summary.json'}")
print(f"  Saved → {OUTPUT_DIR / 'SR_Papers_wrong_entries.json'}")


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 2: ANALYZE WRONG ENTRIES
# ═════════════════════════════════════════════════════════════════════════════

print(f"\n{'─'*60}")
print("  PHASE 2: Analyzing wrong entries")
print(f"{'─'*60}")

genuinely_wrong = []
offset_bug = []

for item in wrong_entries:
    correct_field_lc = (item.get("correct_cma_field") or "").strip().lower()
    predicted_field_lc = (item.get("predicted_cma_field") or "").strip().lower()

    # Offset bug: field names match but something else caused the mismatch
    if item.get("is_doubt"):
        genuinely_wrong.append(item)
    elif correct_field_lc and predicted_field_lc and correct_field_lc == predicted_field_lc:
        offset_bug.append(item)
    else:
        genuinely_wrong.append(item)

# Deduplicate by (raw_text, correct_field, predicted_field)
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

print(f"  Total wrong entries:    {len(wrong_entries)}")
print(f"  GT offset bugs:         {len(offset_bug)}")
print(f"  Genuinely wrong:        {len(genuinely_wrong)}")
print(f"  Unique genuinely wrong: {len(unique_wrong)}")


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 3: INTERVIEW WRONG ITEMS (MAX 50)
# ═════════════════════════════════════════════════════════════════════════════

print(f"\n{'─'*60}")
print(f"  PHASE 3: Interviewing {min(len(unique_wrong), MAX_INTERVIEWS)} wrong items")
print(f"{'─'*60}")

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

    # Apply +1 GT offset for extraction-format GT (non-BCIPL)
    correct_row_raw = item["correct_cma_row"]
    correct_row = (correct_row_raw + 1) if correct_row_raw else correct_row_raw

    # Get field names from label map
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

    available_rows = [r["sheet_row"] for r in context.cma_rows]
    correct_in_list = correct_row in available_rows

    # Determine error type purely by routing (not model response)
    error_type = "routing_bug" if not correct_in_list else "model_error"

    original_prompt = sc._build_prompt(raw_text, amount, section or "not specified", context)

    interview_q = f"""You classified this financial line item:
"{raw_text}" (section: "{section}", amount: {amount}, industry: manufacturing)

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
4. What is the EXACT minimum change to make you pick Row {correct_row} confidently?
   Examples: "Add a rule: X → Row Y", "Change routing pattern", "Add example"
5. Write ONE Python regex pattern that would correctly route this item.

PART C — Classification:
6. Is this a ROUTING BUG or MODEL ERROR?
7. Confidence you'd get it right with the fix: (0-100%)

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

    interview_results.append({
        "index": i,
        "company": COMPANY,
        "raw_text": raw_text,
        "section": section,
        "amount": amount,
        "industry_type": INDUSTRY,
        "correct_row": correct_row,
        "correct_row_gt": correct_row_raw,
        "correct_name": correct_name,
        "predicted_row": predicted_row,
        "predicted_name": predicted_name,
        "correct_in_options": correct_in_list,
        "error_type": error_type,
        "routed_to": sections_routed,
        "classification_method": item.get("classification_method", ""),
        "confidence": item.get("confidence", 0),
        "is_doubt": item.get("is_doubt", False),
        "document_type": doc_type,
        "model_response": answer,
    })

    status = "ROUTING_BUG" if not correct_in_list else "MODEL_ERROR"
    print(
        f"  [{i+1:2d}/{min(len(unique_wrong), MAX_INTERVIEWS)}] {status:>12} | "
        f"'{raw_text[:45]}'  correct=R{correct_row} pred=R{predicted_row}"
    )
    sys.stdout.flush()

# ─── Interview summary ────────────────────────────────────────────────────────
routing_bugs = [r for r in interview_results if r["error_type"] == "routing_bug"]
model_errors = [r for r in interview_results if r["error_type"] == "model_error"]
doubt_items = [r for r in interview_results if r.get("is_doubt")]

interview_elapsed = time.time() - interview_start

print(f"\n{'='*60}")
print(f"  PHASE 3 SUMMARY")
print(f"{'='*60}")
print(f"  Total wrong:            {len(wrong_entries)}")
print(f"  GT offset bugs:         {len(offset_bug)}")
print(f"  Genuinely wrong:        {len(genuinely_wrong)}")
print(f"  Unique genuinely wrong: {len(unique_wrong)}")
print(f"  Interviewed:            {len(interview_results)}")
n_iv = max(len(interview_results), 1)
print(f"  ├─ Routing bugs:        {len(routing_bugs)} ({len(routing_bugs)/n_iv*100:.0f}%)")
print(f"  ├─ Model errors:        {len(model_errors)} ({len(model_errors)/n_iv*100:.0f}%)")
print(f"  └─ Doubts:              {len(doubt_items)}")
print(f"  API calls:              {api_calls}")
print(f"  Elapsed:                {interview_elapsed:.0f}s")

# ─── Save interview JSON ──────────────────────────────────────────────────────
interview_output = {
    "meta": {
        "company": COMPANY,
        "industry": INDUSTRY,
        "round": 2,
        "date": time.strftime("%Y-%m-%d %H:%M"),
        "context": "After implementing CA-verified rules (CA-001 to CA-024)",
    },
    "accuracy_summary": summary,
    "round1_baseline": {
        "accuracy_pct": round1_acc,
        "correct": round1_correct,
        "total_items": round1_total,
    },
    "analysis": {
        "total_wrong": len(wrong_entries),
        "gt_offset_bugs": len(offset_bug),
        "genuinely_wrong": len(genuinely_wrong),
        "unique_wrong": len(unique_wrong),
        "interviewed": len(interview_results),
        "routing_bugs": len(routing_bugs),
        "model_errors": len(model_errors),
        "doubt_items": len(doubt_items),
    },
    "interviews": interview_results,
}

with open(OUTPUT_DIR / "SR_Papers_interview.json", "w") as f:
    json.dump(interview_output, f, indent=2, ensure_ascii=False)

print(f"\n  Saved → {OUTPUT_DIR / 'SR_Papers_interview.json'}")
print()
print("=" * 70)
print("  ALL PHASES COMPLETE")
print("=" * 70)
print(f"  Round 1 accuracy: {round1_acc:.2f}%  ({round1_correct}/{round1_total})")
print(f"  Round 2 accuracy: {accuracy_pct:.2f}%  ({correct}/{len(results)})")
print(f"  Delta:            {delta_str}pp")
print(f"\n  Output files:")
print(f"    {OUTPUT_DIR / 'SR_Papers_accuracy_summary.json'}")
print(f"    {OUTPUT_DIR / 'SR_Papers_wrong_entries.json'}")
print(f"    {OUTPUT_DIR / 'SR_Papers_interview.json'}")
print()
