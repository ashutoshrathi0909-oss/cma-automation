#!/usr/bin/env python3
"""
MSL Round 2 Accuracy Test + Interview + HTML Report.

Steps:
  1. Load MSL GT, filter EXCLUDED items, run ScopedClassifier
  2. Analyze wrong entries (filter offset bugs, deduplicate)
  3. Interview genuinely wrong items via DeepSeek V3 (MAX 50)
  4. Generate self-contained HTML review report

Run:
  docker compose exec -T worker bash -c "cd /app && python test-results/round2/run_msl.py"
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, "/app")

# ─── Paths ────────────────────────────────────────────────────────────────────
GT_PATH = Path("/app/DOCS/extractions/MSL_classification_ground_truth.json")
OUTPUT_DIR = Path("/app/test-results/round2")
ROUND1_SUMMARY_PATH = Path("/app/test-results/post-ca-rules/MSL_accuracy_summary.json")
CANONICAL_LABELS_PATH = Path("/app/CMA_Ground_Truth_v1/reference/canonical_labels.json")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── Cost guards ──────────────────────────────────────────────────────────────
MAX_ITEMS = 500
MAX_TOKENS = 500_000
MAX_INTERVIEWS = 50

RUN_DATE = time.strftime("%Y-%m-%d %H:%M")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def doc_type_from_section(section: str, sheet_name: str = "", cma_row=None) -> str:
    combined = f"{section} {sheet_name}".lower()
    if any(kw in combined for kw in ["balance sheet", "bs", "assets", "liabilities", "equity"]):
        return "balance_sheet"
    if cma_row is not None and cma_row and int(cma_row) >= 111:
        return "balance_sheet"
    return "profit_and_loss"


def doubt_result(reason: str):
    from app.services.classification.ai_classifier import AIClassificationResult
    return AIClassificationResult(
        cma_field_name=None, cma_row=None, cma_sheet="input_sheet",
        broad_classification="", confidence=0.0, is_doubt=True,
        doubt_reason=reason, alternatives=[], classification_method="scoped_doubt",
    )


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 1: LOAD GROUND TRUTH
# ═════════════════════════════════════════════════════════════════════════════

print("=" * 70)
print("  MSL ROUND 2: ACCURACY TEST + INTERVIEW")
print(f"  Date: {RUN_DATE}")
print("=" * 70)
print()

with open(GT_PATH, encoding="utf-8") as f:
    raw_gt = json.load(f)

raw_items = raw_gt if isinstance(raw_gt, list) else raw_gt.get("items", [])

entries = [
    {
        "raw_text": e.get("raw_text", ""),
        "section": e.get("section", ""),
        "amount": e.get("amount_rupees", e.get("amount")),
        "cma_row": e.get("correct_cma_row"),
        "cma_field_name": e.get("correct_cma_field", ""),
        "financial_year": e.get("financial_year", ""),
        "sheet_name": e.get("sheet_name", ""),
    }
    for e in raw_items
]

excluded = [
    e for e in entries
    if e["cma_row"] == 0 or str(e["cma_field_name"]).strip().upper() == "EXCLUDED"
]
scoreable = [
    e for e in entries
    if not (e["cma_row"] == 0 or str(e["cma_field_name"]).strip().upper() == "EXCLUDED")
]

print(f"GT loaded:          {len(entries)} items")
print(f"EXCLUDED (skipped): {len(excluded)}  (CA-specific exclusions, e.g. Export Incentive)")
print(f"Scoreable:          {len(scoreable)}")

if len(scoreable) > MAX_ITEMS:
    print(f"Cost guard: capping at {MAX_ITEMS}")
    scoreable = scoreable[:MAX_ITEMS]

# Load canonical labels for row→code mapping
with open(CANONICAL_LABELS_PATH) as f:
    _canonical = json.load(f)
sheetrow_to_code: dict[int, str] = {item["sheet_row"]: item["code"] for item in _canonical}
print(f"Canonical labels:   {len(sheetrow_to_code)} rows\n")


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 2: RUN CLASSIFIER
# ═════════════════════════════════════════════════════════════════════════════

from app.services.classification.scoped_classifier import ScopedClassifier

sc = ScopedClassifier()
print(f"ScopedClassifier ready: {len(sc._contexts)} sections, {len(sc._labels_by_row)} labels\n")

results: list[dict] = []
wrong_entries: list[dict] = []
phase2_start = time.time()
total = len(scoreable)

for i, entry in enumerate(scoreable):
    raw_text = entry["raw_text"]
    section = entry["section"]
    amount = entry["amount"]
    correct_row = entry["cma_row"]
    correct_field = entry["cma_field_name"]
    doc_type = doc_type_from_section(section, entry.get("sheet_name", ""), correct_row)

    # Token budget reinit
    if sc._total_tokens > MAX_TOKENS:
        print(f"  [{i+1}] Token budget {sc._total_tokens:,} → reinit")
        sc = ScopedClassifier()

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
        print(f"  [{i+1}] ERROR: {e}")
        result = doubt_result(f"Exception: {e}")

    # Reinit on token-budget doubt
    if result.is_doubt and result.doubt_reason and "token budget" in result.doubt_reason.lower():
        sc = ScopedClassifier()
        try:
            result = sc.classify_sync(
                raw_text=raw_text, amount=amount, section=section,
                industry_type="manufacturing", document_type=doc_type, fuzzy_candidates=[],
            )
        except Exception as e2:
            result = doubt_result(f"Retry failed: {e2}")

    predicted_row = result.cma_row
    predicted_code = sheetrow_to_code.get(predicted_row) if predicted_row else None

    # Correctness: field name comparison for extractions format
    if correct_field and result.cma_field_name:
        is_correct = (not result.is_doubt) and (
            correct_field.strip().lower() == result.cma_field_name.strip().lower()
        )
    else:
        is_correct = (not result.is_doubt) and (predicted_row == correct_row)

    results.append({"is_correct": is_correct, "is_doubt": result.is_doubt})

    if not is_correct:
        wrong_entries.append({
            "company": "MSL",
            "raw_text": raw_text,
            "section": section,
            "amount": amount,
            "financial_year": entry.get("financial_year", ""),
            "sheet_name": entry.get("sheet_name", ""),
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
            "industry_type": "manufacturing",
            "document_type": doc_type,
        })

    if (i + 1) % 25 == 0:
        n = i + 1
        correct_n = sum(r["is_correct"] for r in results)
        acc = correct_n / n * 100
        elapsed_so_far = time.time() - phase2_start
        print(
            f"  [{n:3d}/{total}] acc={acc:.1f}%  "
            f"tokens={sc._total_tokens:,}  elapsed={elapsed_so_far:.0f}s"
        )
        sys.stdout.flush()

# ─── Final stats ──────────────────────────────────────────────────────────────
phase2_elapsed = time.time() - phase2_start
correct_count = sum(r["is_correct"] for r in results)
doubts_count = sum(r["is_doubt"] for r in results)
wrong_count = total - correct_count - doubts_count
accuracy_pct = round(correct_count / total * 100, 2) if total else 0.0

print(
    f"\nRound 2: {correct_count}/{total} correct ({accuracy_pct}%)  "
    f"wrong={wrong_count}  doubts={doubts_count}  {phase2_elapsed:.0f}s"
)

summary: dict = {
    "company": "MSL",
    "round": 2,
    "industry": "manufacturing",
    "total_items": total,
    "excluded_items": len(excluded),
    "correct": correct_count,
    "wrong": wrong_count,
    "doubts": doubts_count,
    "accuracy_pct": accuracy_pct,
    "elapsed_seconds": round(phase2_elapsed, 2),
    "date": RUN_DATE,
}

with open(OUTPUT_DIR / "MSL_accuracy_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
with open(OUTPUT_DIR / "MSL_wrong_entries.json", "w") as f:
    json.dump(wrong_entries, f, indent=2)
print(f"Saved: MSL_accuracy_summary.json ({total} items), MSL_wrong_entries.json ({len(wrong_entries)} items)")


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 3: ANALYZE WRONG ENTRIES
# ═════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("  ANALYZING WRONG ENTRIES")
print("=" * 60)

genuinely_wrong: list[dict] = []
offset_bugs: list[dict] = []

for item in wrong_entries:
    cf = (item.get("correct_cma_field") or "").strip().lower()
    pf = (item.get("predicted_cma_field") or "").strip().lower()
    if item.get("is_doubt"):
        genuinely_wrong.append(item)
    elif cf and pf and cf == pf:
        # Field names match → GT row offset mismatch, not a real classification error
        offset_bugs.append(item)
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

print(f"Total wrong:        {len(wrong_entries)}")
print(f"GT offset bugs:     {len(offset_bugs)}  (field names match, row offset mismatch)")
print(f"Genuinely wrong:    {len(genuinely_wrong)}")
print(f"Unique:             {len(unique_wrong)}  (deduplicated)")


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 4: INTERVIEW WRONG ITEMS (MAX 50)
# ═════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print(f"  INTERVIEWING WRONG ITEMS (MAX {MAX_INTERVIEWS})")
print("=" * 60 + "\n")

from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

interview_results: list[dict] = []
interview_start = time.time()

for i, item in enumerate(unique_wrong[:MAX_INTERVIEWS]):
    raw_text = item["raw_text"]
    section = item.get("section", "")
    amount = item.get("amount")
    predicted_row = item.get("predicted_cma_row")
    doc_type = item.get("document_type", "profit_and_loss")

    # MSL is "extractions" format → apply +1 row offset for interview lookup
    correct_row_raw = item["correct_cma_row"]
    correct_row = (correct_row_raw + 1) if correct_row_raw else correct_row_raw

    correct_name = sc._labels_by_row.get(correct_row, {}).get("name", f"Row {correct_row}")
    predicted_name = (
        sc._labels_by_row.get(predicted_row, {}).get("name", f"Row {predicted_row}")
        if predicted_row else "DOUBT"
    )

    # Rebuild routing to check if correct row was in the classifier's options
    sections_routed = sc._route_section(raw_text, section or "", doc_type)
    if len(sections_routed) == 1:
        context = sc._contexts.get(sections_routed[0]) or sc._contexts["admin_expense"]
    else:
        context = sc._merge_contexts(sections_routed)

    available_rows = [r["sheet_row"] for r in context.cma_rows]
    correct_in_list = correct_row in available_rows
    error_type = "routing_bug" if not correct_in_list else "model_error"

    original_prompt = sc._build_prompt(raw_text, amount, section or "not specified", context)

    interview_q = f"""You classified this financial line item:
"{raw_text}" (section: "{section}", amount: {amount}, industry: manufacturing)

You chose: Row {predicted_row} ({predicted_name})
The CORRECT answer is: Row {correct_row} ({correct_name})
Was Row {correct_row} in the options you were shown? {"YES" if correct_in_list else "NO — NOT in options"}

Full prompt you received:
---
{original_prompt}
---

PART A — Root Cause:
1. Was Row {correct_row} ({correct_name}) in the POSSIBLE CMA ROWS list? (Yes/No)
2. If YES: why did you pick Row {predicted_row} instead?
3. If NO: what keyword/section should have routed this item to include Row {correct_row}?

PART B — Fix:
4. Minimum change to make you pick Row {correct_row} confidently?
5. One Python regex pattern to route this correctly.

PART C:
6. ROUTING BUG or MODEL ERROR?
7. Confidence you'd get it right with the fix: (0-100%)

Max 200 words."""

    try:
        resp = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[{"role": "user", "content": interview_q}],
            max_tokens=300,
            temperature=0.0,
        )
        answer = resp.choices[0].message.content.strip()
    except Exception as e:
        answer = f"ERROR: {e}"

    interview_results.append({
        "index": i,
        "raw_text": raw_text,
        "section": section,
        "amount": amount,
        "financial_year": item.get("financial_year", ""),
        "sheet_name": item.get("sheet_name", ""),
        "correct_cma_row_raw": correct_row_raw,
        "correct_cma_row": correct_row,
        "correct_cma_field": item.get("correct_cma_field", ""),
        "correct_name": correct_name,
        "predicted_cma_row": predicted_row,
        "predicted_cma_field": item.get("predicted_cma_field", ""),
        "predicted_name": predicted_name,
        "correct_in_options": correct_in_list,
        "error_type": error_type,
        "routed_to": sections_routed,
        "classification_method": item.get("classification_method", ""),
        "confidence": item.get("confidence", 0),
        "is_doubt": item.get("is_doubt", False),
        "doubt_reason": item.get("doubt_reason", ""),
        "model_response": answer,
    })

    print(
        f"[{i+1:2d}/{min(len(unique_wrong), MAX_INTERVIEWS)}] "
        f"{error_type.upper():>12} | "
        f"'{raw_text[:38]}' → R{correct_row} (pred=R{predicted_row})"
    )
    sys.stdout.flush()

routing_bugs = [r for r in interview_results if r["error_type"] == "routing_bug"]
model_errors = [r for r in interview_results if r["error_type"] == "model_error"]
interview_elapsed = time.time() - interview_start

print(
    f"\nInterviewed: {len(interview_results)}  "
    f"routing_bugs={len(routing_bugs)}  model_errors={len(model_errors)}  "
    f"{interview_elapsed:.0f}s"
)

# Load Round 1 summary for comparison
round1: dict = {
    "accuracy_pct": "N/A", "correct": "?", "wrong": "?", "doubts": "?", "total_items": "?"
}
if ROUND1_SUMMARY_PATH.exists():
    with open(ROUND1_SUMMARY_PATH) as f:
        round1 = json.load(f)

r1_acc = round1.get("accuracy_pct", "N/A")
r1_correct = round1.get("correct", "?")
r1_total = round1.get("total_items", "?")

if isinstance(r1_acc, (int, float)):
    delta = accuracy_pct - r1_acc
    delta_str = f"+{delta:.1f}pp" if delta >= 0 else f"{delta:.1f}pp"
else:
    delta_str = "N/A"

print(f"\nRound 1: {r1_correct}/{r1_total} ({r1_acc}%)")
print(f"Round 2: {correct_count}/{total} ({accuracy_pct}%)")
print(f"Delta:   {delta_str}")

# Save interview JSON
wrong_analysis = {
    "total_wrong": len(wrong_entries),
    "offset_bugs": len(offset_bugs),
    "genuinely_wrong": len(genuinely_wrong),
    "unique_wrong": len(unique_wrong),
    "interviewed": len(interview_results),
    "routing_bugs": len(routing_bugs),
    "model_errors": len(model_errors),
}

interview_output = {
    "meta": {
        "date": RUN_DATE,
        "company": "MSL",
        "round": 2,
        "context": "Round 2 post-CA-rules scoped_v3 classifier (CA-001 to CA-024)",
    },
    "round1_summary": round1,
    "round2_summary": summary,
    "wrong_analysis": wrong_analysis,
    "interviews": interview_results,
}

with open(OUTPUT_DIR / "MSL_interview.json", "w") as f:
    json.dump(interview_output, f, indent=2, ensure_ascii=False)
print(f"Saved: MSL_interview.json")


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 5: GENERATE HTML REPORT
# ═════════════════════════════════════════════════════════════════════════════

print("\nGenerating HTML review report...")

# Build display item list: interviewed first (with error_type), then uninterviewed
iv_lookup: dict[tuple, dict] = {
    (
        r["raw_text"].strip().lower(),
        (r.get("correct_cma_field") or "").lower(),
        (r.get("predicted_cma_field") or "").lower(),
    ): r
    for r in interview_results
}

html_items: list[dict] = []
for item in unique_wrong:
    key = (
        item["raw_text"].strip().lower(),
        (item.get("correct_cma_field") or "").lower(),
        (item.get("predicted_cma_field") or "").lower(),
    )
    iv = iv_lookup.get(key)
    html_items.append({
        "raw_text": item["raw_text"],
        "section": item.get("section", ""),
        "amount": item.get("amount"),
        "financial_year": item.get("financial_year", ""),
        "sheet_name": item.get("sheet_name", ""),
        "correct_cma_row": item.get("correct_cma_row"),
        "correct_cma_field": item.get("correct_cma_field", ""),
        "predicted_cma_row": item.get("predicted_cma_row"),
        "predicted_cma_field": item.get("predicted_cma_field", ""),
        "confidence": item.get("confidence", 0),
        "is_doubt": item.get("is_doubt", False),
        "doubt_reason": item.get("doubt_reason", ""),
        "classification_method": item.get("classification_method", ""),
        "error_type": iv["error_type"] if iv else "unanalyzed",
        "correct_in_options": iv["correct_in_options"] if iv else None,
        "routed_to": iv["routed_to"] if iv else [],
        "interview_response": iv["model_response"] if iv else None,
    })

# Sort: routing bugs → model errors → unanalyzed
_order = {"routing_bug": 0, "model_error": 1, "unanalyzed": 2}
html_items.sort(key=lambda x: _order.get(x["error_type"], 2))

data_json = json.dumps(html_items, ensure_ascii=False)
summary_json = json.dumps({
    "round1": {"accuracy_pct": r1_acc, "correct": r1_correct, "total": r1_total},
    "round2": {
        "accuracy_pct": accuracy_pct,
        "correct": correct_count,
        "wrong": wrong_count,
        "doubts": doubts_count,
        "total": total,
        "excluded": len(excluded),
    },
    "delta": delta_str,
    "wrong_analysis": wrong_analysis,
}, ensure_ascii=False)

r1_bar = r1_acc if isinstance(r1_acc, (int, float)) else 0
acc_card_class = "good" if accuracy_pct >= 70 else "warn" if accuracy_pct >= 50 else "bad"
delta_cls = (
    "delta-pos" if delta_str.startswith("+")
    else "delta-neg" if delta_str.startswith("-")
    else "delta-neutral"
)

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MSL — Round 2 Classification Review</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f0f4f8;color:#2d3748;font-size:14px;line-height:1.6}}
.container{{max-width:960px;margin:0 auto;padding:16px}}
.page-header{{background:#1a365d;color:#fff;padding:20px 24px;border-radius:8px;margin-bottom:14px}}
.page-header h1{{font-size:20px;font-weight:700;margin-bottom:4px}}
.page-header .sub{{opacity:.75;font-size:13px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:14px}}
.card{{background:#fff;padding:14px 16px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.08);text-align:center}}
.card-val{{font-size:24px;font-weight:700;color:#1a365d}}
.card-lbl{{font-size:11px;color:#718096;margin-top:2px;text-transform:uppercase;letter-spacing:.04em}}
.card.good .card-val{{color:#27ae60}}
.card.bad .card-val{{color:#e53e3e}}
.card.warn .card-val{{color:#e67e22}}
.compare-box,.analysis-box,.progress-box{{background:#fff;padding:14px 16px;border-radius:8px;margin-bottom:14px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.box-title{{font-size:14px;font-weight:700;color:#1a365d;margin-bottom:10px}}
.compare-row{{display:flex;align-items:center;gap:12px;padding:7px 0;border-bottom:1px solid #f0f4f8}}
.compare-row:last-child{{border-bottom:none}}
.compare-lbl{{font-size:13px;color:#4a5568;width:80px;flex-shrink:0}}
.compare-bar-wrap{{flex:1;background:#e2e8f0;border-radius:99px;height:14px;overflow:hidden}}
.compare-bar{{height:100%;border-radius:99px}}
.bar-r1{{background:#90cdf4}}
.bar-r2{{background:#27ae60}}
.compare-val{{font-size:13px;font-weight:700;width:110px;text-align:right;flex-shrink:0}}
.delta-badge{{padding:2px 9px;border-radius:4px;font-size:12px;font-weight:700;flex-shrink:0}}
.delta-pos{{background:#f0fff4;color:#276749;border:1px solid #9ae6b4}}
.delta-neg{{background:#fff5f5;color:#c53030;border:1px solid #fc8181}}
.delta-neutral{{background:#f7fafc;color:#4a5568;border:1px solid #e2e8f0}}
.stat-row{{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #f0f4f8;font-size:13px}}
.stat-row:last-child{{border-bottom:none}}
.stat-val{{font-weight:600;color:#1a365d}}
.stat-val.red{{color:#e53e3e}}
.stat-val.orange{{color:#e67e22}}
.pbar-lbl{{font-size:13px;color:#4a5568;margin-bottom:5px;display:flex;justify-content:space-between}}
.pbar{{background:#e2e8f0;border-radius:99px;height:10px;overflow:hidden}}
.pbar-fill{{background:#27ae60;height:100%;border-radius:99px;transition:width .3s}}
.sec-hdr{{background:#1a365d;color:#fff;padding:11px 16px;border-radius:8px;margin-bottom:8px;display:flex;align-items:center;gap:10px}}
.sec-hdr h2{{font-size:14px;font-weight:600;flex:1}}
.sec-badge{{background:#e67e22;color:#fff;padding:2px 10px;border-radius:99px;font-size:12px;font-weight:700}}
.item-card{{background:#fff;border:1px solid #e2e8f0;border-radius:8px;margin-bottom:10px;overflow:hidden;transition:border-color .2s}}
.item-card.routing-bug{{border-left:4px solid #e53e3e}}
.item-card.model-error{{border-left:4px solid #e67e22}}
.item-card.unanalyzed{{border-left:4px solid #a0aec0}}
.item-card.reviewed{{background:#f0fff4;border-color:#9ae6b4}}
.item-hdr{{padding:12px 16px;cursor:pointer;display:flex;align-items:flex-start;gap:10px;user-select:none}}
.item-hdr:hover{{background:#fafbfc}}
.item-num{{background:#1a365d;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;flex-shrink:0;margin-top:2px}}
.item-text{{font-size:14px;font-weight:600;color:#1a365d;flex:1}}
.item-meta{{font-size:11px;color:#718096;margin-top:2px}}
.err-pill{{padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;flex-shrink:0;white-space:nowrap}}
.pill-rb{{background:#fff5f5;color:#c53030;border:1px solid #fc8181}}
.pill-me{{background:#fef3e2;color:#c05621;border:1px solid #f6ad55}}
.pill-ua{{background:#f7fafc;color:#718096;border:1px solid #e2e8f0}}
.chevron{{color:#a0aec0;font-size:12px;margin-left:6px;flex-shrink:0}}
.item-body{{padding:14px 16px;border-top:1px solid #f0f4f8}}
.field-grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}}
.field-box{{background:#f7fafc;padding:10px 12px;border-radius:6px;border:1px solid #e2e8f0}}
.field-box.gt{{border-left:3px solid #27ae60}}
.field-box.ai{{border-left:3px solid #e67e22}}
.field-lbl{{font-size:10px;font-weight:700;color:#718096;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px}}
.field-val{{font-size:13px;font-weight:600;color:#2d3748}}
.field-row{{font-size:11px;color:#718096;margin-top:1px}}
.iv-toggle{{background:none;border:1px solid #e2e8f0;padding:3px 10px;border-radius:4px;font-size:11px;cursor:pointer;color:#4a5568;margin-bottom:8px}}
.iv-toggle:hover{{background:#f7fafc;border-color:#1a365d}}
.iv-text{{white-space:pre-wrap;font-size:11px;font-family:'Courier New',monospace;color:#4a5568;display:none;padding:10px;background:#f7fafc;border:1px solid #e2e8f0;border-radius:4px;margin-bottom:10px;line-height:1.5}}
.iv-text.open{{display:block}}
.review-lbl{{font-size:13px;font-weight:600;color:#2d3748;margin-bottom:8px}}
.opts{{list-style:none}}
.opt{{padding:7px 10px;border-radius:6px;margin-bottom:4px;display:flex;align-items:center;gap:8px;cursor:pointer;border:1px solid transparent;transition:background .1s;font-size:13px}}
.opt:hover{{background:#f7fafc}}
.opt.sel{{background:#f0fff4;border-color:#9ae6b4}}
.opt input[type=radio]{{accent-color:#27ae60;flex-shrink:0;cursor:pointer}}
.row-input{{padding:5px 9px;border:1px solid #cbd5e0;border-radius:4px;font-size:12px;width:100px}}
.row-input:focus{{outline:none;border-color:#1a365d}}
.name-input{{padding:5px 9px;border:1px solid #cbd5e0;border-radius:4px;font-size:12px;flex:1;min-width:140px}}
.name-input:focus{{outline:none;border-color:#27ae60;box-shadow:0 0 0 2px #c6f6d5}}
.name-input::placeholder{{color:#a0aec0;font-style:italic}}
.btn{{padding:8px 18px;border-radius:6px;border:none;cursor:pointer;font-size:13px;font-weight:500;transition:all .15s}}
.btn-navy{{background:#1a365d;color:#fff}}.btn-navy:hover{{background:#2c5282}}
.btn-outline{{background:#fff;color:#4a5568;border:1px solid #cbd5e0}}.btn-outline:hover{{border-color:#1a365d;color:#1a365d}}
.export-sec{{background:#fff;padding:18px;border-radius:8px;margin-top:14px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.export-sec h3{{color:#1a365d;margin-bottom:8px;font-size:15px}}
.export-note{{font-size:12px;color:#718096;margin-bottom:10px}}
.export-out{{width:100%;min-height:160px;padding:10px;border:1px solid #e2e8f0;border-radius:6px;font-family:'Courier New',monospace;font-size:11px;resize:vertical;display:none;margin-top:10px}}
.export-out.visible{{display:block}}
@media(max-width:600px){{.field-grid{{grid-template-columns:1fr}}.cards{{grid-template-columns:repeat(2,1fr)}}}}
</style>
</head>
<body>
<div class="container">

<div class="page-header">
  <h1>MSL — Round 2 Classification Review</h1>
  <div class="sub">
    Industry: Manufacturing (Metal) &nbsp;|&nbsp;
    Date: {RUN_DATE} &nbsp;|&nbsp;
    Classifier: scoped_v3 + CA-001 to CA-024 rules
  </div>
</div>

<div class="cards">
  <div class="card">
    <div class="card-val">{total}</div>
    <div class="card-lbl">Total Items</div>
  </div>
  <div class="card good">
    <div class="card-val">{correct_count}</div>
    <div class="card-lbl">Correct</div>
  </div>
  <div class="card bad">
    <div class="card-val">{wrong_count}</div>
    <div class="card-lbl">Wrong</div>
  </div>
  <div class="card">
    <div class="card-val">{doubts_count}</div>
    <div class="card-lbl">Doubts</div>
  </div>
  <div class="card {acc_card_class}">
    <div class="card-val">{accuracy_pct}%</div>
    <div class="card-lbl">Accuracy</div>
  </div>
  <div class="card">
    <div class="card-val" id="reviewed-val">0</div>
    <div class="card-lbl">CA Reviewed</div>
  </div>
</div>

<div class="compare-box">
  <div class="box-title">Round 1 vs Round 2 Comparison</div>
  <div class="compare-row">
    <span class="compare-lbl">Round 1</span>
    <div class="compare-bar-wrap">
      <div class="compare-bar bar-r1" style="width:{r1_bar}%"></div>
    </div>
    <span class="compare-val">{r1_acc}% ({r1_correct}/{r1_total})</span>
    <span class="delta-badge delta-neutral">Baseline</span>
  </div>
  <div class="compare-row">
    <span class="compare-lbl">Round 2</span>
    <div class="compare-bar-wrap">
      <div class="compare-bar bar-r2" style="width:{accuracy_pct}%"></div>
    </div>
    <span class="compare-val">{accuracy_pct}% ({correct_count}/{total})</span>
    <span class="delta-badge {delta_cls}">{delta_str}</span>
  </div>
</div>

<div class="analysis-box">
  <div class="box-title">Wrong Item Analysis</div>
  <div class="stat-row"><span>Total wrong items</span><span class="stat-val">{len(wrong_entries)}</span></div>
  <div class="stat-row"><span>GT offset bugs (field names match)</span><span class="stat-val">{len(offset_bugs)}</span></div>
  <div class="stat-row"><span>Genuinely wrong</span><span class="stat-val">{len(genuinely_wrong)}</span></div>
  <div class="stat-row"><span>Unique (deduplicated)</span><span class="stat-val">{len(unique_wrong)}</span></div>
  <div class="stat-row"><span>AI-interviewed</span><span class="stat-val">{len(interview_results)}</span></div>
  <div class="stat-row"><span>&nbsp;&nbsp;├─ Routing bugs (correct row not shown to AI)</span><span class="stat-val red">{len(routing_bugs)}</span></div>
  <div class="stat-row"><span>&nbsp;&nbsp;└─ Model errors (correct row shown, wrong pick)</span><span class="stat-val orange">{len(model_errors)}</span></div>
</div>

<div class="progress-box">
  <div class="pbar-lbl">
    <span>CA Review Progress</span>
    <span id="prog-text">0 / {len(unique_wrong)} items reviewed</span>
  </div>
  <div class="pbar"><div class="pbar-fill" id="prog-bar" style="width:0%"></div></div>
</div>

<div id="items-container"></div>

<div class="export-sec">
  <h3>Export CA Responses</h3>
  <div class="export-note">Download all CA verdicts as JSON for import into the learning system.</div>
  <div style="display:flex;gap:10px;flex-wrap:wrap">
    <button class="btn btn-navy" onclick="exportJSON()">Export JSON</button>
    <button class="btn btn-outline" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">↑ Back to Top</button>
  </div>
  <textarea id="export-out" class="export-out" readonly></textarea>
</div>

</div><!-- /container -->

<script>
const ITEMS = {data_json};
const SUMMARY = {summary_json};
const TOTAL_ITEMS = {len(unique_wrong)};

let answers = {{}};

function esc(s) {{
  if (!s && s !== 0) return '';
  return String(s)
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}}

function fmtAmt(a) {{
  if (!a && a !== 0) return 'N/A';
  const lakhs = (a / 100000).toFixed(2);
  return '\u20b9' + Number(a).toLocaleString('en-IN') + ' (' + lakhs + ' L)';
}}

function errPill(t) {{
  if (t === 'routing_bug')
    return '<span class="err-pill pill-rb">ROUTING BUG</span>';
  if (t === 'model_error')
    return '<span class="err-pill pill-me">MODEL ERROR</span>';
  return '<span class="err-pill pill-ua">UNANALYZED</span>';
}}

function renderItem(item, idx) {{
  const conf = item.confidence ? Math.round(item.confidence * 100) : 0;
  const confClr = conf >= 80 ? '#27ae60' : conf >= 60 ? '#e67e22' : '#e53e3e';
  const cardCls = item.error_type === 'routing_bug' ? 'routing-bug'
    : item.error_type === 'model_error' ? 'model-error' : 'unanalyzed';
  const routed = item.routed_to && item.routed_to.length
    ? ' &nbsp;|&nbsp; Routed: ' + esc(item.routed_to.join(' + ')) : '';

  let ivHtml = '';
  if (item.interview_response) {{
    ivHtml = `
      <button class="iv-toggle" onclick="toggleIv(${{idx}})">AI Interview Analysis ▾</button>
      <div class="iv-text" id="iv-${{idx}}">${{esc(item.interview_response)}}</div>`;
  }}

  return `
<div class="item-card ${{cardCls}}" id="card-${{idx}}">
  <div class="item-hdr" onclick="toggleBody(${{idx}})">
    <span class="item-num">#${{idx+1}}</span>
    <div style="flex:1;min-width:0">
      <div class="item-text">${{esc(item.raw_text)}}</div>
      <div class="item-meta">
        Section: ${{esc(item.section||'N/A')}} &nbsp;|&nbsp;
        FY${{item.financial_year||'?'}} &nbsp;|&nbsp;
        ${{fmtAmt(item.amount)}} &nbsp;|&nbsp;
        ${{item.is_doubt ? '<b style="color:#e53e3e">DOUBT</b>' : 'Conf: <b style="color:'+confClr+'">'+conf+'%</b>'}}
        ${{routed}}
      </div>
    </div>
    ${{errPill(item.error_type)}}
    <span class="chevron" id="chev-${{idx}}">▸</span>
  </div>
  <div class="item-body" id="body-${{idx}}" style="display:none">
    <div class="field-grid">
      <div class="field-box gt">
        <div class="field-lbl">CA Ground Truth</div>
        <div class="field-val">${{esc(item.correct_cma_field||'N/A')}}</div>
        <div class="field-row">Row ${{item.correct_cma_row||'?'}}</div>
      </div>
      <div class="field-box ai">
        <div class="field-lbl">AI Predicted</div>
        <div class="field-val">${{item.is_doubt ? '\u26a0 DOUBT' : esc(item.predicted_cma_field||'N/A')}}</div>
        <div class="field-row">Row ${{item.predicted_cma_row||'?'}}</div>
      </div>
    </div>
    ${{ivHtml}}
    <div class="review-lbl">CA Review — Is this classification acceptable?</div>
    <ul class="opts">
      <li class="opt" id="opt-${{idx}}-agree" onclick="selectOpt(${{idx}},'agree',this)">
        <input type="radio" name="r${{idx}}" value="agree">
        <span>Agree with AI — predicted field is correct (GT is wrong)</span>
      </li>
      <li class="opt" id="opt-${{idx}}-gt" onclick="selectOpt(${{idx}},'gt_correct',this)">
        <input type="radio" name="r${{idx}}" value="gt_correct">
        <span>GT is correct — AI should have picked <b>${{esc(item.correct_cma_field)}}</b></span>
      </li>
      <li class="opt" id="opt-${{idx}}-other" onclick="selectOpt(${{idx}},'other',this)">
        <input type="radio" name="r${{idx}}" value="other">
        <span>Different answer: &nbsp;Row&nbsp;
          <input class="row-input" id="orow-${{idx}}" type="number" placeholder="Row #" min="1" max="400"
            onclick="event.stopPropagation()">
          &nbsp;
          <input class="name-input" id="oname-${{idx}}" type="text" placeholder="Field name (optional)"
            onclick="event.stopPropagation()">
        </span>
      </li>
    </ul>
  </div>
</div>`;
}}

function toggleBody(idx) {{
  const b = document.getElementById('body-' + idx);
  const c = document.getElementById('chev-' + idx);
  if (b.style.display === 'none') {{ b.style.display = 'block'; c.textContent = '▾'; }}
  else {{ b.style.display = 'none'; c.textContent = '▸'; }}
}}

function toggleIv(idx) {{
  document.getElementById('iv-' + idx).classList.toggle('open');
}}

function selectOpt(idx, val, el) {{
  document.querySelectorAll(`[id^="opt-${{idx}}-"]`).forEach(o => o.classList.remove('sel'));
  el.classList.add('sel');
  el.querySelector('input[type=radio]').checked = true;

  const item = ITEMS[idx];
  answers[idx] = {{
    index: idx,
    raw_text: item.raw_text,
    section: item.section,
    correct_cma_field: item.correct_cma_field,
    correct_cma_row: item.correct_cma_row,
    predicted_cma_field: item.predicted_cma_field,
    predicted_cma_row: item.predicted_cma_row,
    error_type: item.error_type,
    ca_verdict: val,
    ca_correct_row: val === 'other' ? (parseInt(document.getElementById('orow-'+idx)?.value)||null) : null,
    ca_correct_name: val === 'other' ? (document.getElementById('oname-'+idx)?.value||null) : null,
  }};

  document.getElementById('card-' + idx).classList.add('reviewed');
  updateProgress();
}}

function updateProgress() {{
  const r = Object.keys(answers).length;
  document.getElementById('reviewed-val').textContent = r;
  document.getElementById('prog-text').textContent = r + ' / ' + TOTAL_ITEMS + ' items reviewed';
  document.getElementById('prog-bar').style.width = (r / TOTAL_ITEMS * 100).toFixed(1) + '%';
}}

function renderAll() {{
  const routing = ITEMS.filter(x => x.error_type === 'routing_bug');
  const model   = ITEMS.filter(x => x.error_type === 'model_error');
  const unana   = ITEMS.filter(x => x.error_type === 'unanalyzed');
  let html = '';

  if (routing.length) {{
    html += `<div class="sec-hdr">
      <h2>Routing Bugs — Correct Row Not Shown to AI</h2>
      <span class="sec-badge">${{routing.length}}</span>
    </div>`;
    routing.forEach(item => {{ html += renderItem(item, ITEMS.indexOf(item)); }});
  }}

  if (model.length) {{
    html += `<div class="sec-hdr" style="margin-top:16px">
      <h2>Model Errors — Correct Row Available, Wrong Pick</h2>
      <span class="sec-badge">${{model.length}}</span>
    </div>`;
    model.forEach(item => {{ html += renderItem(item, ITEMS.indexOf(item)); }});
  }}

  if (unana.length) {{
    html += `<div class="sec-hdr" style="margin-top:16px;background:#718096">
      <h2>Unanalyzed Wrong Items (beyond interview limit)</h2>
      <span class="sec-badge">${{unana.length}}</span>
    </div>`;
    unana.forEach(item => {{ html += renderItem(item, ITEMS.indexOf(item)); }});
  }}

  document.getElementById('items-container').innerHTML = html;
}}

function exportJSON() {{
  const out = {{
    meta: {{
      company: 'MSL',
      round: 2,
      date: '{RUN_DATE}',
      total_wrong_items: TOTAL_ITEMS,
      reviewed: Object.keys(answers).length,
    }},
    summary: SUMMARY,
    ca_answers: Object.values(answers),
  }};
  const json = JSON.stringify(out, null, 2);
  const el = document.getElementById('export-out');
  el.value = json;
  el.classList.add('visible');
  const blob = new Blob([json], {{type:'application/json'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'MSL_round2_ca_review_{time.strftime('%Y-%m-%d')}.json';
  a.click();
}}

renderAll();
updateProgress();
</script>
</body>
</html>"""

html_path = OUTPUT_DIR / "MSL_review.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)
print(f"Saved: MSL_review.html  ({len(html_content):,} bytes)")

# ─── Final summary ────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("  ALL DONE")
print("=" * 70)
print(f"  Round 1 accuracy:  {r1_correct}/{r1_total}  ({r1_acc}%)")
print(f"  Round 2 accuracy:  {correct_count}/{total}  ({accuracy_pct}%)")
print(f"  Delta:             {delta_str}")
print(f"  Excluded items:    {len(excluded)}  (not scored)")
print(f"  Genuinely wrong:   {len(genuinely_wrong)}  (unique: {len(unique_wrong)})")
print(f"  Routing bugs:      {len(routing_bugs)}")
print(f"  Model errors:      {len(model_errors)}")
print(f"\n  Outputs saved to: {OUTPUT_DIR}")
for fn in ["MSL_accuracy_summary.json", "MSL_wrong_entries.json", "MSL_interview.json", "MSL_review.html"]:
    p = OUTPUT_DIR / fn
    size = p.stat().st_size if p.exists() else 0
    print(f"    {fn:<35} {size:>10,} bytes")
