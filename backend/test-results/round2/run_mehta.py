#!/usr/bin/env python3
"""
Round 2 Accuracy Test + Interview + HTML Report — Mehta_Computer

Steps:
  1. Load GT, run classify_sync on each item, save accuracy + wrong entries
  2. Filter GT offset bugs, deduplicate genuinely wrong
  3. Interview wrong items (MAX 50) — routing bug vs model error
  4. Generate self-contained HTML CA review report

Run:
  docker compose exec -T worker bash -c "cd /app && python test-results/round2/run_mehta.py"

Outputs (inside /app/test-results/round2/):
  - Mehta_Computer_accuracy_summary.json
  - Mehta_Computer_wrong_entries.json
  - Mehta_Computer_interview.json
  - Mehta_Computer_review.html
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, "/app")

# ─── Paths ─────────────────────────────────────────────────────────────────────
GT_PATH = Path("/app/CMA_Ground_Truth_v1/companies/Mehta_Computer/ground_truth_normalized.json")
CANONICAL_LABELS_PATH = Path("/app/CMA_Ground_Truth_v1/reference/canonical_labels.json")
OUTPUT_DIR = Path("/app/test-results/round2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ROUND1_SUMMARY_PATH = Path("/app/test-results/post-ca-rules/Mehta_Computer_accuracy_summary.json")

# ─── Cost guards ───────────────────────────────────────────────────────────────
MAX_ITEMS = 500
MAX_TOKENS = 500_000
TOKEN_REINIT_THRESHOLD = 450_000
MAX_INTERVIEWS = 50

COMPANY = "Mehta_Computer"
INDUSTRY = "trading"

# ─── Helpers ───────────────────────────────────────────────────────────────────

def _doubt_result(reason: str):
    from app.services.classification.ai_classifier import AIClassificationResult
    return AIClassificationResult(
        cma_field_name=None, cma_row=None, cma_sheet="input_sheet",
        broad_classification="", confidence=0.0, is_doubt=True,
        doubt_reason=reason, alternatives=[], classification_method="scoped_doubt",
    )


def doc_type_from_section(section: str, sheet_name: str = "", cma_row=None) -> str:
    combined = f"{section} {sheet_name}".lower()
    if any(kw in combined for kw in ["balance sheet", "bs", "asset", "liabilit", "equity",
                                      "investment", "deposit", "current asset", "fixed asset"]):
        return "balance_sheet"
    if cma_row is not None and int(cma_row) >= 111:
        return "balance_sheet"
    return "profit_and_loss"


def make_classifier():
    from app.services.classification.scoped_classifier import ScopedClassifier
    sc = ScopedClassifier()
    print(f"  [ScopedClassifier] sections={len(sc._contexts)} labels={len(sc._labels_by_row)}")
    return sc


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1: ACCURACY TEST
# ═══════════════════════════════════════════════════════════════════════════════

print("=" * 70)
print("  ROUND 2 ACCURACY TEST — Mehta_Computer")
print("=" * 70)
print()

# Load canonical labels for code lookup
with open(CANONICAL_LABELS_PATH, encoding="utf-8") as f:
    _canonical = json.load(f)
sheetrow_to_code: dict[int, str] = {item["sheet_row"]: item["code"] for item in _canonical}
sheetrow_to_name: dict[int, str] = {item["sheet_row"]: item["name"] for item in _canonical}
print(f"Loaded {len(sheetrow_to_code)} canonical labels")

# Load ground truth
with open(GT_PATH, encoding="utf-8") as f:
    gt_data = json.load(f)

entries = gt_data.get("database_entries", [])
print(f"GT entries: {len(entries)}")

if len(entries) > MAX_ITEMS:
    print(f"Cost guard: capping at {MAX_ITEMS}")
    entries = entries[:MAX_ITEMS]

total = len(entries)

# Initialize classifier
sc = make_classifier()
print()

results = []
wrong_entries = []
start_time = time.time()

for i, entry in enumerate(entries):
    raw_text = entry.get("raw_text", "")
    section = entry.get("section", "")
    sheet_name = entry.get("sheet_name", "")
    amount = entry.get("amount")
    correct_row = entry.get("cma_row")
    correct_code = entry.get("cma_code", "")
    correct_field = entry.get("cma_field_name", "")
    doc_type = doc_type_from_section(section, sheet_name, correct_row)

    # Token budget guard
    if sc._total_tokens > TOKEN_REINIT_THRESHOLD:
        print(f"  [{i+1}] Token budget {sc._total_tokens:,} → reinitializing")
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
    except Exception as e:
        print(f"  [{i+1}] ERROR: {e}")
        result = _doubt_result(f"Exception: {e}")

    # Token-budget doubt → reinit + retry
    if result.is_doubt and result.doubt_reason and "token budget" in result.doubt_reason.lower():
        sc = make_classifier()
        try:
            result = sc.classify_sync(
                raw_text=raw_text, amount=amount, section=section,
                industry_type=INDUSTRY, document_type=doc_type, fuzzy_candidates=[],
            )
        except Exception as e2:
            result = _doubt_result(f"Retry failed: {e2}")

    predicted_row = result.cma_row
    predicted_code = sheetrow_to_code.get(predicted_row) if predicted_row else None

    # Correctness: by code if available, else field name, else row
    if correct_code and predicted_code:
        is_correct = (not result.is_doubt) and (predicted_code == correct_code)
    elif correct_field and result.cma_field_name:
        is_correct = (not result.is_doubt) and (correct_field.strip().lower() == result.cma_field_name.strip().lower())
    else:
        is_correct = (not result.is_doubt) and (predicted_row == correct_row)

    results.append({"is_correct": is_correct, "is_doubt": result.is_doubt})

    if not is_correct:
        wrong_entries.append({
            "company": COMPANY,
            "raw_text": raw_text,
            "section": section,
            "sheet_name": sheet_name,
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
            "industry_type": INDUSTRY,
            "document_type": doc_type,
        })

    if (i + 1) % 25 == 0:
        elapsed = time.time() - start_time
        n = i + 1
        correct_n = sum(r["is_correct"] for r in results)
        acc = correct_n / n * 100
        print(f"  [{n:3d}/{total}] acc={acc:.1f}% tokens={sc._total_tokens:,} elapsed={elapsed:.0f}s")
        sys.stdout.flush()

elapsed = time.time() - start_time
correct_count = sum(r["is_correct"] for r in results)
doubt_count = sum(r["is_doubt"] for r in results)
wrong_count = total - correct_count - doubt_count
accuracy_pct = round(correct_count / total * 100, 2) if total else 0

summary = {
    "company": COMPANY,
    "industry": INDUSTRY,
    "total_items": total,
    "correct": correct_count,
    "wrong": wrong_count,
    "doubts": doubt_count,
    "accuracy_pct": accuracy_pct,
    "elapsed_seconds": round(elapsed, 2),
    "total_tokens": sc._total_tokens,
    "run_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
}

print(f"\n{COMPANY}: {correct_count}/{total} correct ({accuracy_pct}%)  wrong={wrong_count} doubt={doubt_count}  {elapsed:.0f}s")

# Save accuracy summary
with open(OUTPUT_DIR / f"{COMPANY}_accuracy_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(f"Saved accuracy summary → {OUTPUT_DIR}/{COMPANY}_accuracy_summary.json")

# Save wrong entries
with open(OUTPUT_DIR / f"{COMPANY}_wrong_entries.json", "w") as f:
    json.dump(wrong_entries, f, indent=2)
print(f"Saved wrong entries ({len(wrong_entries)}) → {OUTPUT_DIR}/{COMPANY}_wrong_entries.json")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2: ANALYZE WRONG ENTRIES
# ═══════════════════════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print("  STEP 2: ANALYZE WRONG ENTRIES")
print(f"{'='*70}\n")

# Load Round 1 baseline for comparison
round1_summary = {}
if ROUND1_SUMMARY_PATH.exists():
    with open(ROUND1_SUMMARY_PATH, encoding="utf-8") as f:
        round1_summary = json.load(f)

round1_accuracy = round1_summary.get("accuracy_pct", 0)
round1_correct = round1_summary.get("correct", 0)
round1_wrong = round1_summary.get("wrong", 0)
delta = round(accuracy_pct - round1_accuracy, 2)

print(f"Round 1 accuracy: {round1_accuracy}%  ({round1_correct} correct, {round1_wrong} wrong)")
print(f"Round 2 accuracy: {accuracy_pct}%  ({correct_count} correct, {wrong_count} wrong)")
print(f"Delta: {delta:+.2f}pp")
print()

# Filter GT offset bugs: same field name = not a real error
offset_bugs = []
genuinely_wrong = []

for item in wrong_entries:
    correct_field = (item.get("correct_cma_field") or "").strip().lower()
    predicted_field = (item.get("predicted_cma_field") or "").strip().lower()

    if item.get("is_doubt"):
        genuinely_wrong.append(item)
    elif correct_field and predicted_field and correct_field == predicted_field:
        offset_bugs.append(item)
    else:
        genuinely_wrong.append(item)

print(f"Total wrong entries:        {len(wrong_entries)}")
print(f"GT offset bugs (same field):{len(offset_bugs)}")
print(f"Genuinely wrong:            {len(genuinely_wrong)}")

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

print(f"Unique genuinely wrong:     {len(unique_wrong)}")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3: INTERVIEW WRONG ITEMS
# ═══════════════════════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  STEP 3: INTERVIEW (MAX {MAX_INTERVIEWS})")
print(f"{'='*70}\n")

from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

interview_results: list[dict] = []
interview_start = time.time()
api_calls = 0

for i, item in enumerate(unique_wrong[:MAX_INTERVIEWS]):
    raw_text = item["raw_text"]
    section = item.get("section", "")
    sheet_name = item.get("sheet_name", "")
    amount = item.get("amount")
    predicted_row = item.get("predicted_cma_row")
    doc_type = item.get("document_type", "profit_and_loss")

    # GT row for Mehta: use raw GT row as-is (companies format, not extractions format)
    correct_row_raw = item.get("correct_cma_row")
    # Apply +1 offset for labels lookup (same as run_all_post_ca.py for non-BCIPL)
    correct_row_for_lookup = correct_row_raw + 1 if correct_row_raw else correct_row_raw

    # Resolve names from labels
    correct_name = (
        sc._labels_by_row.get(correct_row_for_lookup, {}).get("name")
        or sheetrow_to_name.get(correct_row_raw, f"Row {correct_row_raw}")
        or f"Row {correct_row_raw}"
    )
    predicted_name = (
        sc._labels_by_row.get(predicted_row, {}).get("name", f"Row {predicted_row}")
        if predicted_row else "DOUBT"
    )

    # Rebuild routing to check if correct row was available
    sections = sc._route_section(raw_text, section or "", doc_type)
    if len(sections) == 1:
        context = sc._contexts.get(sections[0]) or sc._contexts["admin_expense"]
    else:
        context = sc._merge_contexts(sections)

    available_rows = [r["sheet_row"] for r in context.cma_rows]
    # Check with both raw and offset rows
    correct_in_list = (correct_row_raw in available_rows) or (correct_row_for_lookup in available_rows)

    original_prompt = sc._build_prompt(raw_text, amount, section or "not specified", context)

    # Error type based on routing
    error_type = "routing_bug" if not correct_in_list else "model_error"

    interview_q = f"""You classified this financial line item:
"{raw_text}" (section: "{section}", sheet: "{sheet_name}", amount: {amount})

You chose: Row {predicted_row} ({predicted_name})
The CORRECT answer is: Row {correct_row_raw} ({item.get('correct_cma_field', correct_name)})
Was the correct row in the options you were shown? {"YES" if correct_in_list else "NO — it was NOT in your options"}

PART A — Why it went wrong:
1. Was the correct CMA row in the POSSIBLE CMA ROWS list? (Yes/No)
2. If yes: why did you pick Row {predicted_row} instead?
3. If no: what keywords should have triggered routing to the correct section?

PART B — Fix:
4. Write the minimum prompt change to get this right.
5. One routing regex that would correctly route this item.

Be specific. Max 150 words."""

    try:
        resp = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[{"role": "user", "content": interview_q}],
            max_tokens=220,
            temperature=0.0,
        )
        answer = resp.choices[0].message.content.strip()
        api_calls += 1
    except Exception as e:
        answer = f"ERROR: {e}"

    interview_results.append({
        "index": i,
        "raw_text": raw_text,
        "section": section,
        "sheet_name": sheet_name,
        "amount": amount,
        "correct_cma_row": correct_row_raw,
        "correct_cma_field": item.get("correct_cma_field", ""),
        "correct_cma_code": item.get("correct_cma_code", ""),
        "predicted_cma_row": predicted_row,
        "predicted_cma_field": item.get("predicted_cma_field", ""),
        "predicted_cma_code": item.get("predicted_cma_code", ""),
        "confidence": item.get("confidence", 0),
        "classification_method": item.get("classification_method", ""),
        "is_doubt": item.get("is_doubt", False),
        "doubt_reason": item.get("doubt_reason"),
        "error_type": error_type,
        "correct_row_in_options": correct_in_list,
        "routed_to": sections,
        "document_type": doc_type,
        "model_response": answer,
    })

    status = "ROUTING_BUG" if not correct_in_list else "MODEL_ERROR"
    print(
        f"[{i+1:2d}/{min(len(unique_wrong), MAX_INTERVIEWS)}] {status} | "
        f"'{raw_text[:45]}' → correct={correct_row_raw} pred={predicted_row}"
    )
    sys.stdout.flush()

routing_bugs = sum(1 for r in interview_results if not r["correct_row_in_options"])
model_errors = sum(1 for r in interview_results if r["correct_row_in_options"])

print(f"\nRouting bugs: {routing_bugs}  Model errors: {model_errors}  (of {len(interview_results)} interviewed)")
print(f"Elapsed: {time.time() - interview_start:.0f}s  API calls: {api_calls}")

interview_output = {
    "summary": {
        "company": COMPANY,
        "round": 2,
        "run_date": summary["run_date"],
        "total_wrong": len(wrong_entries),
        "offset_bugs": len(offset_bugs),
        "genuinely_wrong": len(genuinely_wrong),
        "unique_genuinely_wrong": len(unique_wrong),
        "interviewed": len(interview_results),
        "routing_bugs": routing_bugs,
        "model_errors": model_errors,
        "api_calls": api_calls,
    },
    "interviews": interview_results,
}

with open(OUTPUT_DIR / f"{COMPANY}_interview.json", "w") as f:
    json.dump(interview_output, f, indent=2, ensure_ascii=False)
print(f"Saved interview results → {OUTPUT_DIR}/{COMPANY}_interview.json")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4: GENERATE HTML REPORT
# ═══════════════════════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print("  STEP 4: GENERATING HTML REPORT")
print(f"{'='*70}\n")

# Sort interview results: routing bugs first, then model errors
sorted_interviews = sorted(interview_results, key=lambda x: (0 if not x["correct_row_in_options"] else 1, x["index"]))

# Pre-serialize data for embedding in HTML
data_json = json.dumps({
    "company": COMPANY,
    "industry": INDUSTRY,
    "run_date": summary["run_date"],
    "round1": {"accuracy": round1_accuracy, "correct": round1_correct, "wrong": round1_wrong, "total": total},
    "round2": {"accuracy": accuracy_pct, "correct": correct_count, "wrong": wrong_count, "doubts": doubt_count, "total": total},
    "delta": delta,
    "offset_bugs": len(offset_bugs),
    "routing_bugs": routing_bugs,
    "model_errors": model_errors,
    "items": sorted_interviews,
}, ensure_ascii=False, indent=2)

# Build item cards HTML
def _amt(v):
    if v is None:
        return "—"
    try:
        return f"₹{float(v):,.0f}"
    except Exception:
        return str(v)

def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

item_cards_html = ""
for idx, item in enumerate(sorted_interviews):
    error_cls = "routing-bug" if not item["correct_row_in_options"] else "model-error"
    error_label = "ROUTING BUG" if not item["correct_row_in_options"] else "MODEL ERROR"
    error_color = "#e53e3e" if not item["correct_row_in_options"] else "#d69e2e"
    error_bg = "#fff5f5" if not item["correct_row_in_options"] else "#fffff0"
    error_border = "#fc8181" if not item["correct_row_in_options"] else "#f6e05e"

    sections_str = ", ".join(item.get("routed_to", []))
    method = _esc(item.get("classification_method", ""))
    conf_pct = f"{float(item.get('confidence', 0))*100:.0f}%"
    doubt_note = f'<div class="doubt-note">Doubt: {_esc(item.get("doubt_reason", ""))}</div>' if item.get("is_doubt") else ""

    model_resp_html = _esc(item.get("model_response", "")).replace("\n", "<br>")

    item_cards_html += f"""
    <div class="item-card {error_cls}" id="item-{idx}" data-index="{idx}">
      <div class="item-header" style="border-left:4px solid {error_color};background:{error_bg}">
        <div class="item-header-top">
          <span class="item-num">#{idx+1}</span>
          <span class="error-badge" style="background:{error_color}">{error_label}</span>
          <span class="item-text">"{_esc(item['raw_text'])}"</span>
        </div>
        <div class="item-meta">
          <span class="meta-tag">Section: {_esc(item.get('section','—'))}</span>
          <span class="meta-tag">Sheet: {_esc(item.get('sheet_name','—'))}</span>
          <span class="meta-tag">Amount: {_amt(item.get('amount'))}</span>
          <span class="meta-tag">Routed→ {_esc(sections_str)}</span>
          <span class="meta-tag">Method: {method}</span>
          <span class="meta-tag conf">Conf: {conf_pct}</span>
        </div>
      </div>
      <div class="item-body">
        <div class="classification-grid">
          <div class="cls-box correct-box">
            <div class="cls-label">CORRECT (GT)</div>
            <div class="cls-row-num">Row {_esc(str(item.get('correct_cma_row','?')))}</div>
            <div class="cls-code">{_esc(item.get('correct_cma_code',''))}</div>
            <div class="cls-field">{_esc(item.get('correct_cma_field',''))}</div>
          </div>
          <div class="cls-arrow">→</div>
          <div class="cls-box predicted-box" style="border-color:{error_color}">
            <div class="cls-label">AI PREDICTED</div>
            <div class="cls-row-num">Row {_esc(str(item.get('predicted_cma_row','?')))}</div>
            <div class="cls-code">{_esc(item.get('predicted_cma_code',''))}</div>
            <div class="cls-field">{_esc(item.get('predicted_cma_field','DOUBT' if item.get('is_doubt') else ''))}</div>
          </div>
        </div>
        {doubt_note}
        <details class="ai-reasoning">
          <summary>AI Self-Analysis (Interview Response)</summary>
          <div class="reasoning-body">{model_resp_html}</div>
        </details>
        <div class="ca-review-box" data-idx="{idx}">
          <div class="ca-review-label">CA Review</div>
          <label class="ca-opt">
            <input type="radio" name="ca_{idx}" value="agree"> AI is correct — GT is wrong
          </label>
          <label class="ca-opt">
            <input type="radio" name="ca_{idx}" value="gt_correct"> GT is correct — AI made an error
          </label>
          <label class="ca-opt">
            <input type="radio" name="ca_{idx}" value="override">
            Override: correct row is &nbsp;
            <input type="number" class="row-override" id="override_{idx}" placeholder="row#" min="1" max="400">
            &nbsp;
            <input type="text" class="field-override" id="field_{idx}" placeholder="field name">
          </label>
          <div class="ca-notes-row">
            <label>Notes: <textarea class="ca-notes" id="notes_{idx}" placeholder="optional notes"></textarea></label>
          </div>
        </div>
      </div>
    </div>"""

# Count items by type for display
routing_count = sum(1 for r in sorted_interviews if not r.get("correct_row_in_options"))
model_count = sum(1 for r in sorted_interviews if r.get("correct_row_in_options"))

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>CMA Round 2 Review — {COMPANY}</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f0f4f8;color:#2d3748;font-size:14px;line-height:1.6}}
.container{{max-width:960px;margin:0 auto;padding:16px}}
/* Header */
.page-header{{background:#1a365d;color:#fff;padding:20px 24px;border-radius:8px;margin-bottom:14px}}
.page-header h1{{font-size:22px;font-weight:700;margin-bottom:4px}}
.page-header .sub{{opacity:.75;font-size:13px}}
/* Summary cards */
.stats-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:14px}}
.stat-card{{background:#fff;border-radius:8px;padding:14px 16px;box-shadow:0 1px 3px rgba(0,0,0,.08);text-align:center}}
.stat-val{{font-size:28px;font-weight:700;color:#1a365d}}
.stat-val.green{{color:#27ae60}}
.stat-val.red{{color:#e53e3e}}
.stat-val.orange{{color:#e67e22}}
.stat-val.delta-pos{{color:#27ae60}}
.stat-val.delta-neg{{color:#e53e3e}}
.stat-lbl{{font-size:11px;color:#718096;text-transform:uppercase;letter-spacing:.04em;margin-top:2px}}
/* Accuracy comparison */
.compare-box{{background:#fff;border-radius:8px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,.08);margin-bottom:14px}}
.compare-box h3{{font-size:14px;font-weight:700;color:#1a365d;margin-bottom:12px}}
.compare-row{{display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid #f0f4f8}}
.compare-row:last-child{{border-bottom:none}}
.compare-lbl{{width:120px;font-size:13px;color:#4a5568;font-weight:600}}
.compare-bar-wrap{{flex:1;background:#e2e8f0;border-radius:99px;height:18px;overflow:hidden;position:relative}}
.compare-bar{{height:100%;border-radius:99px;display:flex;align-items:center;padding-left:8px;font-size:11px;color:#fff;font-weight:700;white-space:nowrap;transition:width .4s}}
.bar-r1{{background:#718096}}
.bar-r2{{background:#1a365d}}
.compare-pct{{width:55px;text-align:right;font-weight:700;font-size:14px}}
/* Error type breakdown */
.error-breakdown{{display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap}}
.error-card{{flex:1;min-width:160px;background:#fff;border-radius:8px;padding:14px;box-shadow:0 1px 3px rgba(0,0,0,.08);border-top:4px solid}}
.error-card.routing{{border-color:#e53e3e}}
.error-card.model{{border-color:#d69e2e}}
.error-card h4{{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px}}
.error-card .error-count{{font-size:32px;font-weight:700}}
.error-card.routing .error-count{{color:#e53e3e}}
.error-card.model .error-count{{color:#d69e2e}}
.error-card .error-desc{{font-size:12px;color:#718096;margin-top:4px}}
/* Progress bar */
.progress-box{{background:#fff;padding:12px 16px;border-radius:8px;margin-bottom:14px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.progress-lbl{{font-size:13px;color:#4a5568;margin-bottom:5px;display:flex;justify-content:space-between}}
.pbar{{background:#e2e8f0;border-radius:99px;height:10px;overflow:hidden}}
.pbar-fill{{background:#27ae60;height:100%;border-radius:99px;transition:width .3s}}
/* Filters */
.filters{{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap;align-items:center}}
.filter-btn{{padding:6px 14px;border-radius:6px;border:1px solid #cbd5e0;cursor:pointer;font-size:13px;background:#fff;color:#4a5568;transition:all .15s}}
.filter-btn:hover,.filter-btn.active{{background:#1a365d;color:#fff;border-color:#1a365d}}
.filter-btn.routing-active{{background:#e53e3e;border-color:#e53e3e;color:#fff}}
.filter-btn.model-active{{background:#d69e2e;border-color:#d69e2e;color:#fff}}
/* Actions */
.actions-row{{display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap}}
.btn{{padding:9px 18px;border-radius:6px;border:none;cursor:pointer;font-size:13px;font-weight:600;transition:all .15s}}
.btn-navy{{background:#1a365d;color:#fff}}.btn-navy:hover{{background:#2c5282}}
.btn-green{{background:#27ae60;color:#fff}}.btn-green:hover{{background:#229954}}
.btn-orange{{background:#e67e22;color:#fff}}.btn-orange:hover{{background:#d35400}}
/* Item cards */
.item-card{{background:#fff;border-radius:8px;margin-bottom:12px;box-shadow:0 1px 4px rgba(0,0,0,.08);overflow:hidden;transition:box-shadow .15s}}
.item-card:hover{{box-shadow:0 2px 8px rgba(0,0,0,.12)}}
.item-card.hidden{{display:none}}
.item-header{{padding:12px 16px}}
.item-header-top{{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:6px}}
.item-num{{font-size:12px;font-weight:700;color:#718096;min-width:28px}}
.error-badge{{padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;color:#fff;white-space:nowrap}}
.item-text{{font-size:15px;font-weight:700;color:#1a365d;flex:1}}
.item-meta{{display:flex;flex-wrap:wrap;gap:6px}}
.meta-tag{{background:#edf2f7;padding:2px 8px;border-radius:4px;font-size:11px;color:#4a5568}}
.meta-tag.conf{{background:#fef3e2;color:#c05621}}
.item-body{{padding:14px 16px;border-top:1px solid #f0f4f8}}
/* Classification grid */
.classification-grid{{display:flex;align-items:center;gap:12px;margin-bottom:12px;flex-wrap:wrap}}
.cls-box{{flex:1;min-width:140px;padding:10px 12px;border-radius:6px;border:2px solid}}
.correct-box{{border-color:#9ae6b4;background:#f0fff4}}
.predicted-box{{background:#fff5f5}}
.cls-label{{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#718096;margin-bottom:4px}}
.cls-row-num{{font-size:18px;font-weight:700;color:#1a365d}}
.cls-code{{font-size:11px;color:#718096;font-family:monospace}}
.cls-field{{font-size:13px;color:#2d3748;font-weight:600;margin-top:2px}}
.cls-arrow{{font-size:24px;color:#cbd5e0;flex-shrink:0}}
.doubt-note{{background:#fff3cd;border:1px solid #ffc107;border-radius:4px;padding:6px 10px;font-size:12px;color:#856404;margin-bottom:10px}}
/* AI reasoning */
.ai-reasoning{{margin-bottom:12px;border:1px solid #e2e8f0;border-radius:6px;overflow:hidden}}
.ai-reasoning summary{{padding:8px 12px;cursor:pointer;font-size:13px;font-weight:600;color:#4a5568;background:#f7fafc;user-select:none}}
.ai-reasoning summary:hover{{background:#edf2f7}}
.reasoning-body{{padding:10px 12px;font-size:12px;color:#4a5568;border-top:1px solid #e2e8f0;line-height:1.7;background:#fafafa}}
/* CA review */
.ca-review-box{{background:#f7fafc;border:1px solid #e2e8f0;border-radius:6px;padding:12px}}
.ca-review-label{{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#4a5568;margin-bottom:8px}}
.ca-opt{{display:flex;align-items:center;gap:8px;padding:5px 0;cursor:pointer;font-size:13px}}
.ca-opt input[type=radio]{{accent-color:#27ae60;cursor:pointer}}
.ca-opt.selected{{color:#1a365d;font-weight:600}}
.row-override{{width:70px;padding:3px 6px;border:1px solid #cbd5e0;border-radius:4px;font-size:13px}}
.field-override{{width:200px;padding:3px 6px;border:1px solid #cbd5e0;border-radius:4px;font-size:13px}}
.row-override:focus,.field-override:focus{{outline:none;border-color:#1a365d}}
.ca-notes-row{{margin-top:8px}}
.ca-notes-row label{{font-size:12px;color:#4a5568}}
.ca-notes{{width:100%;padding:5px 8px;border:1px solid #e2e8f0;border-radius:4px;font-size:12px;min-height:32px;resize:vertical;margin-top:2px;font-family:inherit}}
.ca-notes:focus{{outline:none;border-color:#1a365d}}
/* Section dividers */
.section-divider{{background:#edf2f7;padding:8px 14px;border-radius:6px;margin:16px 0 10px;font-size:13px;font-weight:700;color:#4a5568;display:flex;align-items:center;gap:8px}}
.divider-badge{{padding:2px 8px;border-radius:4px;font-size:11px;color:#fff}}
/* Reviewed indicator */
.item-card.reviewed{{box-shadow:0 0 0 2px #9ae6b4}}
.reviewed-tick{{display:none;margin-left:auto;color:#27ae60;font-size:16px;font-weight:700}}
.item-card.reviewed .reviewed-tick{{display:inline}}
/* Toast */
.toast{{position:fixed;bottom:24px;right:24px;background:#1a365d;color:#fff;padding:12px 20px;border-radius:8px;font-size:14px;box-shadow:0 4px 12px rgba(0,0,0,.2);z-index:1000;transform:translateY(100px);opacity:0;transition:all .3s}}
.toast.show{{transform:translateY(0);opacity:1}}
</style>
</head>
<body>
<div class="container">

  <div class="page-header">
    <h1>CMA Round 2 Review — {COMPANY}</h1>
    <div class="sub">Industry: {INDUSTRY} &nbsp;|&nbsp; Run date: {summary["run_date"]} &nbsp;|&nbsp; {len(sorted_interviews)} items to review</div>
  </div>

  <!-- Summary Stats -->
  <div class="stats-row">
    <div class="stat-card">
      <div class="stat-val">{total}</div>
      <div class="stat-lbl">Total Items</div>
    </div>
    <div class="stat-card">
      <div class="stat-val green">{correct_count}</div>
      <div class="stat-lbl">Correct</div>
    </div>
    <div class="stat-card">
      <div class="stat-val red">{wrong_count}</div>
      <div class="stat-lbl">Wrong</div>
    </div>
    <div class="stat-card">
      <div class="stat-val orange">{doubt_count}</div>
      <div class="stat-lbl">Doubts</div>
    </div>
    <div class="stat-card">
      <div class="stat-val">{accuracy_pct}%</div>
      <div class="stat-lbl">R2 Accuracy</div>
    </div>
    <div class="stat-card">
      <div class="stat-val {'delta-pos' if delta >= 0 else 'delta-neg'}">{'+' if delta >= 0 else ''}{delta}pp</div>
      <div class="stat-lbl">vs Round 1</div>
    </div>
  </div>

  <!-- Accuracy Comparison Bar -->
  <div class="compare-box">
    <h3>Accuracy: Round 1 vs Round 2</h3>
    <div class="compare-row">
      <div class="compare-lbl">Round 1</div>
      <div class="compare-bar-wrap">
        <div class="compare-bar bar-r1" style="width:{round1_accuracy}%">{round1_accuracy}%</div>
      </div>
      <div class="compare-pct" style="color:#718096">{round1_accuracy}%</div>
    </div>
    <div class="compare-row">
      <div class="compare-lbl">Round 2</div>
      <div class="compare-bar-wrap">
        <div class="compare-bar bar-r2" style="width:{accuracy_pct}%">{accuracy_pct}%</div>
      </div>
      <div class="compare-pct" style="color:#1a365d">{accuracy_pct}%</div>
    </div>
    <div style="margin-top:10px;font-size:13px;color:#4a5568">
      R1: {round1_correct}/{total} correct, {round1_wrong} wrong &nbsp;|&nbsp;
      R2: {correct_count}/{total} correct, {wrong_count} wrong &nbsp;|&nbsp;
      GT offset bugs (not real errors): {len(offset_bugs)}
    </div>
  </div>

  <!-- Error Type Breakdown -->
  <div class="error-breakdown">
    <div class="error-card routing">
      <h4>Routing Bugs</h4>
      <div class="error-count">{routing_count}</div>
      <div class="error-desc">Correct row was NOT in the options presented to the model. Fix requires new keyword routing.</div>
    </div>
    <div class="error-card model">
      <h4>Model Errors</h4>
      <div class="error-count">{model_count}</div>
      <div class="error-desc">Correct row WAS available, but the model picked wrong. Fix requires prompt or rule changes.</div>
    </div>
  </div>

  <!-- Progress Bar -->
  <div class="progress-box">
    <div class="progress-lbl">
      <span>CA Review Progress</span>
      <span id="progress-text">0 / {len(sorted_interviews)} reviewed</span>
    </div>
    <div class="pbar"><div class="pbar-fill" id="progress-bar" style="width:0%"></div></div>
  </div>

  <!-- Actions -->
  <div class="actions-row">
    <button class="btn btn-green" onclick="exportJSON()">Export CA Responses (JSON)</button>
    <button class="btn btn-navy" onclick="filterItems('all')" id="filter-all">Show All ({len(sorted_interviews)})</button>
    <button class="btn btn-navy" onclick="filterItems('routing')" id="filter-routing">Routing Bugs ({routing_count})</button>
    <button class="btn btn-navy" onclick="filterItems('model')" id="filter-model">Model Errors ({model_count})</button>
    <button class="btn btn-orange" onclick="filterItems('unreviewed')" id="filter-unreviewed">Unreviewed Only</button>
  </div>

  <!-- Items -->
  <div id="items-container">

    {"" if routing_count == 0 else '<div class="section-divider"><span class="divider-badge" style="background:#e53e3e">ROUTING BUGS</span> Correct row was NOT available to the model — routing fix needed</div>'}

{item_cards_html}

  </div>

  <div style="height:60px"></div>
</div>

<div class="toast" id="toast"></div>

<script>
// ─── Data ─────────────────────────────────────────────────────────────────────
const DATA = {data_json};

// ─── State ────────────────────────────────────────────────────────────────────
let caResponses = {{}};
let currentFilter = 'all';

// ─── Progress ─────────────────────────────────────────────────────────────────
function updateProgress() {{
  const total = DATA.items.length;
  const reviewed = Object.keys(caResponses).length;
  document.getElementById('progress-text').textContent = reviewed + ' / ' + total + ' reviewed';
  document.getElementById('progress-bar').style.width = (reviewed / total * 100) + '%';
}}

// ─── Radio change ─────────────────────────────────────────────────────────────
document.addEventListener('change', function(e) {{
  if (e.target.type === 'radio' && e.target.name.startsWith('ca_')) {{
    const idx = parseInt(e.target.name.replace('ca_', ''));
    const card = document.getElementById('item-' + idx);
    if (card) card.classList.add('reviewed');
    const val = e.target.value;
    if (!caResponses[idx]) caResponses[idx] = {{}};
    caResponses[idx].choice = val;
    caResponses[idx].raw_text = DATA.items[idx].raw_text;
    caResponses[idx].correct_cma_field = DATA.items[idx].correct_cma_field;
    caResponses[idx].predicted_cma_field = DATA.items[idx].predicted_cma_field;
    caResponses[idx].error_type = DATA.items[idx].error_type;
    updateProgress();
  }}
}});

// ─── Input change ─────────────────────────────────────────────────────────────
document.addEventListener('input', function(e) {{
  if (e.target.classList.contains('row-override')) {{
    const idx = e.target.id.replace('override_', '');
    if (!caResponses[idx]) caResponses[idx] = {{}};
    caResponses[idx].override_row = e.target.value;
  }}
  if (e.target.classList.contains('field-override')) {{
    const idx = e.target.id.replace('field_', '');
    if (!caResponses[idx]) caResponses[idx] = {{}};
    caResponses[idx].override_field = e.target.value;
  }}
  if (e.target.classList.contains('ca-notes')) {{
    const idx = e.target.id.replace('notes_', '');
    if (!caResponses[idx]) caResponses[idx] = {{}};
    caResponses[idx].notes = e.target.value;
  }}
}});

// ─── Filter ───────────────────────────────────────────────────────────────────
function filterItems(type) {{
  currentFilter = type;
  ['all','routing','model','unreviewed'].forEach(f => {{
    const btn = document.getElementById('filter-' + f);
    if (btn) btn.classList.remove('active');
  }});
  const activeBtn = document.getElementById('filter-' + type);
  if (activeBtn) activeBtn.classList.add('active');

  const cards = document.querySelectorAll('.item-card');
  cards.forEach(card => {{
    const idx = card.dataset.index;
    const item = DATA.items[parseInt(idx)];
    if (!item) return;
    let show = true;
    if (type === 'routing') show = !item.correct_row_in_options;
    else if (type === 'model') show = item.correct_row_in_options;
    else if (type === 'unreviewed') show = !caResponses[idx];
    card.classList.toggle('hidden', !show);
  }});
}}

// Initialize filter
document.addEventListener('DOMContentLoaded', function() {{
  document.getElementById('filter-all')?.classList.add('active');
}});

// ─── Export ───────────────────────────────────────────────────────────────────
function exportJSON() {{
  const out = {{
    meta: {{
      company: DATA.company,
      industry: DATA.industry,
      run_date: DATA.run_date,
      export_time: new Date().toISOString(),
      round2_accuracy: DATA.round2.accuracy,
      round1_accuracy: DATA.round1.accuracy,
      delta_pp: DATA.delta,
    }},
    summary: {{
      total_wrong: DATA.items.length,
      routing_bugs: DATA.routing_bugs,
      model_errors: DATA.model_errors,
      reviewed: Object.keys(caResponses).length,
    }},
    ca_responses: caResponses,
    items: DATA.items.map((item, i) => ({{
      ...item,
      ca_response: caResponses[i] || null,
    }})),
  }};
  const blob = new Blob([JSON.stringify(out, null, 2)], {{type: 'application/json'}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'Mehta_Computer_round2_ca_responses.json';
  a.click();
  URL.revokeObjectURL(url);
  showToast('Exported ' + Object.keys(caResponses).length + ' CA responses');
}}

// ─── Toast ────────────────────────────────────────────────────────────────────
function showToast(msg) {{
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2800);
}}
</script>
</body>
</html>"""

html_path = OUTPUT_DIR / f"{COMPANY}_review.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"HTML report saved → {html_path}")
print(f"  Size: {len(html):,} bytes")

# ─── Final summary ─────────────────────────────────────────────────────────────
print(f"""
{'='*70}
  DONE — Round 2 Mehta_Computer
{'='*70}
  Accuracy:     R1={round1_accuracy}% → R2={accuracy_pct}%  ({'+' if delta >= 0 else ''}{delta}pp)
  Items:        {total} total, {correct_count} correct, {wrong_count} wrong, {doubt_count} doubts
  Wrong:        {len(offset_bugs)} offset bugs, {len(genuinely_wrong)} genuine, {len(unique_wrong)} unique
  Interviewed:  {len(interview_results)} items → {routing_bugs} routing bugs, {model_errors} model errors
  Tokens used:  {sc._total_tokens:,}

  Files:
    {OUTPUT_DIR}/{COMPANY}_accuracy_summary.json
    {OUTPUT_DIR}/{COMPANY}_wrong_entries.json
    {OUTPUT_DIR}/{COMPANY}_interview.json
    {OUTPUT_DIR}/{COMPANY}_review.html
{'='*70}
""")
