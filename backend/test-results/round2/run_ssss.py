#!/usr/bin/env python3
"""
Round 2 Accuracy Test + Interview + HTML Report — SSSS (Salem Stainless Steel)

Steps:
  1. Load GT, run classify_sync on each item, save accuracy + wrong entries
  2. Filter GT offset bugs, deduplicate genuinely wrong
  3. Interview wrong items (MAX 50) — routing bug vs model error
  4. Generate self-contained HTML CA review report

Run:
  docker compose exec -T worker bash -c "cd /app && python test-results/round2/run_ssss.py"

Outputs (inside /app/test-results/round2/):
  - SSSS_accuracy_summary.json
  - SSSS_wrong_entries.json
  - SSSS_interview.json
  - /app/DOCS/test-results/round2/SSSS_review.html
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
GT_PATH = Path("/app/DOCS/extractions/SSSS_classification_ground_truth.json")
CANONICAL_LABELS_PATH = Path("/app/CMA_Ground_Truth_v1/reference/canonical_labels.json")
OUTPUT_DIR = Path("/app/test-results/round2")
HTML_OUTPUT_DIR = Path("/app/DOCS/test-results/round2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
HTML_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ROUND1_SUMMARY_PATH = Path("/app/test-results/post-ca-rules/SSSS_accuracy_summary.json")

# ─── Cost guards ───────────────────────────────────────────────────────────────
MAX_ITEMS = 500
MAX_TOKENS = 500_000
TOKEN_REINIT_THRESHOLD = 450_000
MAX_INTERVIEWS = 50

COMPANY = "SSSS"
INDUSTRY = "trading"  # Steel trading/distribution — corrected from Round 1 "manufacturing"


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
                                      "investment", "deposit", "current asset", "fixed asset",
                                      "capital", "reserve"]):
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
print("  ROUND 2 ACCURACY TEST — SSSS (Salem Stainless Steel)")
print(f"  Industry: {INDUSTRY}  |  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("=" * 70)
print()

# Load canonical labels
with open(CANONICAL_LABELS_PATH, encoding="utf-8") as f:
    _canonical = json.load(f)
sheetrow_to_code: dict[int, str] = {item["sheet_row"]: item["code"] for item in _canonical}
sheetrow_to_name: dict[int, str] = {item["sheet_row"]: item["name"] for item in _canonical}
print(f"Loaded {len(sheetrow_to_code)} canonical labels")

# Load ground truth — extractions format
with open(GT_PATH, encoding="utf-8") as f:
    gt_raw = json.load(f)

# Extractions GT: top-level list OR {"items": [...]}
gt_items = gt_raw if isinstance(gt_raw, list) else gt_raw.get("items", [])
print(f"GT entries: {len(gt_items)}")

if len(gt_items) > MAX_ITEMS:
    print(f"Cost guard: capping at {MAX_ITEMS}")
    gt_items = gt_items[:MAX_ITEMS]

total = len(gt_items)

# Normalize extractions → standard fields
entries = []
for e in gt_items:
    entries.append({
        "raw_text": e.get("raw_text", ""),
        "section": e.get("section", ""),
        "sheet_name": e.get("sheet_name", ""),
        "amount": e.get("amount_rupees", e.get("amount")),
        "correct_row": e.get("correct_cma_row"),
        "correct_field": e.get("correct_cma_field", ""),
        "correct_code": "",  # extractions GT doesn't have codes
        "financial_year": e.get("financial_year", ""),
    })

# Initialize classifier
sc = make_classifier()
print()

results = []
wrong_entries = []
start_time = time.time()

for i, entry in enumerate(entries):
    raw_text = entry["raw_text"]
    section = entry["section"]
    sheet_name = entry["sheet_name"]
    amount = entry["amount"]
    correct_row = entry["correct_row"]
    correct_field = entry["correct_field"]
    correct_code = entry["correct_code"]
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

    # Correctness — extractions GT: use field name comparison (no code available)
    if correct_field and result.cma_field_name:
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
            "financial_year": entry["financial_year"],
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
    "note": "Round 2: industry corrected to 'trading', CA rules CA-001..CA-024 active",
}

print(f"\n{COMPANY}: {correct_count}/{total} correct ({accuracy_pct}%)  wrong={wrong_count} doubt={doubt_count}  {elapsed:.0f}s")

# Save accuracy summary
with open(OUTPUT_DIR / f"{COMPANY}_accuracy_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(f"Saved → {OUTPUT_DIR}/{COMPANY}_accuracy_summary.json")

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

# Load Round 1 baseline
round1_summary = {}
if ROUND1_SUMMARY_PATH.exists():
    with open(ROUND1_SUMMARY_PATH, encoding="utf-8") as f:
        round1_summary = json.load(f)

round1_accuracy = round1_summary.get("accuracy_pct", 0)
round1_correct = round1_summary.get("correct", 0)
round1_wrong = round1_summary.get("wrong", 0)
round1_doubts = round1_summary.get("doubts", 0)
round1_total = round1_summary.get("total_items", 0)
delta = round(accuracy_pct - round1_accuracy, 2)

print(f"Round 1 accuracy: {round1_accuracy}%  ({round1_correct}/{round1_total} correct, {round1_wrong} wrong, {round1_doubts} doubts)")
print(f"Round 2 accuracy: {accuracy_pct}%  ({correct_count}/{total} correct, {wrong_count} wrong, {doubt_count} doubts)")
print(f"Delta:            {delta:+.2f}pp")
print()

# Filter GT offset bugs
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

print(f"Total wrong entries:         {len(wrong_entries)}")
print(f"GT offset bugs (same field): {len(offset_bugs)}")
print(f"Genuinely wrong:             {len(genuinely_wrong)}")

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

print(f"Unique genuinely wrong:      {len(unique_wrong)}")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3: INTERVIEW WRONG ITEMS (MAX 50)
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

    # GT row — extractions format: use raw value, check both raw and +1 for routing
    correct_row_raw = item.get("correct_cma_row")
    correct_row_offset = (correct_row_raw + 1) if correct_row_raw else correct_row_raw

    # Resolve names from labels (try both raw and offset)
    correct_name = (
        sc._labels_by_row.get(correct_row_raw, {}).get("name")
        or sc._labels_by_row.get(correct_row_offset, {}).get("name")
        or item.get("correct_cma_field", f"Row {correct_row_raw}")
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
    # Check both raw and offset rows
    correct_in_list = (correct_row_raw in available_rows) or (correct_row_offset in available_rows)

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
        "company": COMPANY,
        "raw_text": raw_text,
        "section": section,
        "sheet_name": sheet_name,
        "amount": amount,
        "correct_cma_row": correct_row_raw,
        "correct_cma_field": item.get("correct_cma_field", correct_name),
        "predicted_cma_row": predicted_row,
        "predicted_cma_field": item.get("predicted_cma_field"),
        "correct_row_in_options": correct_in_list,
        "routed_to": sections,
        "available_row_count": len(available_rows),
        "error_type": error_type,
        "classification_method": item.get("classification_method", ""),
        "confidence": item.get("confidence", 0),
        "is_doubt": item.get("is_doubt", False),
        "model_response": answer,
    })

    status = "IN_LIST" if correct_in_list else "NOT_IN_LIST"
    print(
        f"[{i+1:2d}/{min(len(unique_wrong), MAX_INTERVIEWS)}] {error_type:<14} | "
        f"'{raw_text[:45]}' | "
        f"correct=R{correct_row_raw} pred=R{predicted_row}"
    )
    sys.stdout.flush()

# Summary counts
routing_bugs = sum(1 for r in interview_results if r["error_type"] == "routing_bug")
model_errors = sum(1 for r in interview_results if r["error_type"] == "model_error")

print(f"\n{'='*60}")
print(f"INTERVIEW SUMMARY")
print(f"{'='*60}")
print(f"Total wrong:          {len(wrong_entries)}")
print(f"GT offset bugs:       {len(offset_bugs)}")
print(f"Genuinely wrong:      {len(genuinely_wrong)}")
print(f"Unique:               {len(unique_wrong)}")
print(f"Interviewed:          {len(interview_results)}")
print(f"Routing bugs:         {routing_bugs}  (correct row NOT in options)")
print(f"Model errors:         {model_errors}  (correct row available, wrong pick)")
print(f"Elapsed:              {time.time()-interview_start:.0f}s")

# Save interview JSON
interview_output = {
    "summary": {
        "company": COMPANY,
        "industry": INDUSTRY,
        "run_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "round1_accuracy": round1_accuracy,
        "round2_accuracy": accuracy_pct,
        "delta_pp": delta,
        "total_wrong": len(wrong_entries),
        "gt_offset_bugs": len(offset_bugs),
        "genuinely_wrong": len(genuinely_wrong),
        "unique_genuinely_wrong": len(unique_wrong),
        "interviewed": len(interview_results),
        "routing_bugs": routing_bugs,
        "model_errors": model_errors,
        "api_calls": api_calls,
    },
    "interviews": interview_results,
}

with open(OUTPUT_DIR / f"{COMPANY}_interview.json", "w", encoding="utf-8") as f:
    json.dump(interview_output, f, indent=2, ensure_ascii=False)
print(f"\nSaved interview → {OUTPUT_DIR}/{COMPANY}_interview.json")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4: GENERATE HTML REPORT
# ═══════════════════════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print("  STEP 4: GENERATE HTML REPORT")
print(f"{'='*70}\n")

run_date = datetime.now().strftime("%Y-%m-%d %H:%M")

# Separate into routing bugs and model errors for display
routing_items = [r for r in interview_results if r["error_type"] == "routing_bug"]
model_error_items = [r for r in interview_results if r["error_type"] == "model_error"]

# Non-interviewed genuinely wrong (beyond MAX_INTERVIEWS)
not_interviewed = unique_wrong[MAX_INTERVIEWS:]

# Build item cards HTML helper
def esc(s):
    """Escape HTML special characters."""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def format_amount(amt):
    if amt is None:
        return "—"
    try:
        return f"₹{int(amt):,}"
    except Exception:
        return str(amt)

def make_item_card(r: dict, idx: int, group: str) -> str:
    """Generate HTML for one wrong item with CA review radio buttons."""
    raw_text = esc(r.get("raw_text", ""))
    section = esc(r.get("section", ""))
    sheet = esc(r.get("sheet_name", ""))
    amount = format_amount(r.get("amount"))
    correct_field = esc(r.get("correct_cma_field", ""))
    correct_row = r.get("correct_cma_row", "")
    predicted_field = esc(r.get("predicted_cma_field") or "DOUBT")
    predicted_row = r.get("predicted_cma_row", "")
    confidence = r.get("confidence", 0)
    is_doubt = r.get("is_doubt", False)
    method = esc(r.get("classification_method", ""))
    routed_to = esc(", ".join(r.get("routed_to", [])))
    model_resp = esc(r.get("model_response", ""))
    error_type = r.get("error_type", "")
    card_id = f"{group}_{idx}"

    error_badge = (
        '<span class="badge badge-routing">Routing Bug</span>'
        if error_type == "routing_bug"
        else '<span class="badge badge-model">Model Error</span>'
    )
    doubt_badge = '<span class="badge badge-doubt">DOUBT</span>' if is_doubt else ""

    return f"""
<div class="item-card" id="card-{card_id}" data-idx="{card_id}">
  <div class="item-header">
    <span class="item-num">#{idx + 1}</span>
    {error_badge}{doubt_badge}
    <span class="item-text">{raw_text}</span>
  </div>
  <div class="item-meta">
    <span><b>Section:</b> {section}</span>
    <span><b>Sheet:</b> {sheet}</span>
    <span><b>Amount:</b> {amount}</span>
    <span><b>Routed to:</b> {routed_to}</span>
    <span><b>Method:</b> {method}</span>
    <span><b>Confidence:</b> {confidence:.0%}</span>
  </div>
  <div class="classification-row">
    <div class="cls-box cls-correct">
      <div class="cls-label">Correct (GT)</div>
      <div class="cls-value">Row {correct_row} — {correct_field}</div>
    </div>
    <div class="cls-arrow">→</div>
    <div class="cls-box cls-predicted">
      <div class="cls-label">AI Predicted</div>
      <div class="cls-value">Row {predicted_row} — {predicted_field}</div>
    </div>
  </div>
  <details class="interview-details">
    <summary>AI Interview Response</summary>
    <pre class="interview-pre">{model_resp}</pre>
  </details>
  <div class="ca-review">
    <div class="ca-review-label">CA Review:</div>
    <label class="ca-opt">
      <input type="radio" name="review-{card_id}" value="agree" onchange="updateReview('{card_id}', 'agree', '', '')">
      <span>AI classification is correct (GT is wrong)</span>
    </label>
    <label class="ca-opt">
      <input type="radio" name="review-{card_id}" value="gt_correct" onchange="updateReview('{card_id}', 'gt_correct', '{correct_row}', '{esc(r.get('correct_cma_field', ''))}')">
      <span>GT is correct, AI should have picked: <b>Row {correct_row} — {correct_field}</b></span>
    </label>
    <label class="ca-opt">
      <input type="radio" name="review-{card_id}" value="other" onchange="updateReview('{card_id}', 'other', '', '')">
      <span>Neither — correct row is:
        <input type="number" class="row-input" id="row-{card_id}" placeholder="row#" min="1" max="400"
               onchange="updateReview('{card_id}', 'other', this.value, document.getElementById('name-{card_id}').value)"
               onclick="document.querySelector('[name=\\'review-{card_id}\\'][value=other]').checked=true">
        <input type="text" class="name-input" id="name-{card_id}" placeholder="field name"
               onchange="updateReview('{card_id}', 'other', document.getElementById('row-{card_id}').value, this.value)"
               onclick="document.querySelector('[name=\\'review-{card_id}\\'][value=other]').checked=true">
      </span>
    </label>
    <div class="ca-note-row">
      <input type="text" class="note-input" id="note-{card_id}" placeholder="Optional note..."
             onchange="updateNote('{card_id}', this.value)">
    </div>
  </div>
  <div class="review-status" id="status-{card_id}"></div>
</div>"""

# Build all card sections
routing_cards_html = ""
for i, r in enumerate(routing_items):
    routing_cards_html += make_item_card(r, i, "routing")

model_error_cards_html = ""
for i, r in enumerate(model_error_items):
    model_error_cards_html += make_item_card(r, i, "model")

not_interviewed_rows = ""
for item in not_interviewed[:30]:  # show up to 30 non-interviewed
    not_interviewed_rows += f"""
<tr>
  <td>{esc(item.get('raw_text', '')[:60])}</td>
  <td>{esc(item.get('section', ''))}</td>
  <td>{format_amount(item.get('amount'))}</td>
  <td>{esc(item.get('correct_cma_field', ''))}</td>
  <td>{esc(item.get('predicted_cma_field') or 'DOUBT')}</td>
</tr>"""

# Serialise interview data for JS export
interview_json_str = json.dumps(interview_output, ensure_ascii=False)

# Pre-compute not-interviewed section HTML (avoids backslashes inside f-string expression)
if not_interviewed:
    _ni_count = len(not_interviewed)
    _ni_section = (
        '<div class="section-block">'
        '<div class="section-hdr" onclick="toggleSection(\'ni\')">'
        "<h2>C. Additional Wrong Items (Not Interviewed)</h2>"
        f'<span class="count">{_ni_count} items</span>'
        '<span class="chevron">\u25bc</span></div>'
        '<div class="section-body collapsed" id="body-ni">'
        '<div style="padding:12px 16px">'
        '<table class="ni-table"><thead><tr>'
        "<th>Item Text</th><th>Section</th><th>Amount</th><th>Correct Field</th><th>AI Predicted</th>"
        f"</tr></thead><tbody>{not_interviewed_rows}</tbody></table>"
        "</div></div></div>"
    )
else:
    _ni_section = ""

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SSSS — Round 2 CA Review Report</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f0f4f8;color:#2d3748;font-size:14px;line-height:1.6}}
.container{{max-width:980px;margin:0 auto;padding:16px}}

/* Header */
.page-header{{background:#1a365d;color:#fff;padding:22px 28px;border-radius:8px;margin-bottom:16px}}
.page-header h1{{font-size:22px;font-weight:700;margin-bottom:4px}}
.page-header .sub{{opacity:.78;font-size:13px}}

/* Stats cards */
.stats-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px;margin-bottom:16px}}
.stat-card{{background:#fff;border-radius:8px;padding:14px 16px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.stat-value{{font-size:28px;font-weight:700;color:#1a365d;line-height:1}}
.stat-value.green{{color:#27ae60}}.stat-value.red{{color:#e53e3e}}.stat-value.orange{{color:#e67e22}}.stat-value.delta-pos{{color:#27ae60}}.stat-value.delta-neg{{color:#e53e3e}}
.stat-label{{font-size:12px;color:#718096;margin-top:4px}}

/* Progress bar */
.progress-box{{background:#fff;padding:14px 18px;border-radius:8px;margin-bottom:14px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.progress-lbl{{font-size:13px;color:#4a5568;margin-bottom:6px;display:flex;justify-content:space-between}}
.pbar{{background:#e2e8f0;border-radius:99px;height:11px;overflow:hidden}}
.pbar-fill{{background:#27ae60;height:100%;border-radius:99px;transition:width .4s}}

/* Action bar */
.action-bar{{display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap;align-items:center}}
.btn{{padding:9px 18px;border-radius:6px;border:none;cursor:pointer;font-size:13px;font-weight:600;transition:all .15s;white-space:nowrap}}
.btn-navy{{background:#1a365d;color:#fff}}.btn-navy:hover{{background:#2c5282}}
.btn-green{{background:#27ae60;color:#fff}}.btn-green:hover{{background:#229954}}
.btn-orange{{background:#e67e22;color:#fff}}.btn-orange:hover{{background:#d35400}}
.btn-outline{{background:#fff;color:#4a5568;border:1px solid #cbd5e0}}.btn-outline:hover{{border-color:#1a365d;color:#1a365d}}

/* Comparison block */
.compare-block{{background:#fff;border-radius:8px;padding:16px 20px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.compare-block h3{{font-size:15px;font-weight:700;color:#1a365d;margin-bottom:10px}}
.compare-row{{display:flex;gap:24px;flex-wrap:wrap}}
.compare-col{{flex:1;min-width:180px}}
.compare-col label{{font-size:11px;font-weight:700;color:#718096;text-transform:uppercase;letter-spacing:.05em;display:block;margin-bottom:2px}}
.compare-col .val{{font-size:20px;font-weight:700;color:#2d3748}}
.compare-col .val.r1{{color:#e53e3e}}.compare-col .val.r2-better{{color:#27ae60}}.compare-col .val.r2-worse{{color:#e53e3e}}
.delta-chip{{display:inline-block;padding:2px 8px;border-radius:12px;font-size:12px;font-weight:700;margin-left:8px}}
.delta-pos{{background:#c6f6d5;color:#276749}}.delta-neg{{background:#fed7d7;color:#c53030}}

/* Section headers */
.section-hdr{{background:#1a365d;color:#fff;padding:12px 18px;border-radius:8px 8px 0 0;display:flex;align-items:center;gap:12px;cursor:pointer;user-select:none}}
.section-hdr h2{{font-size:16px;font-weight:700;flex:1}}
.section-hdr .count{{font-size:12px;opacity:.8;background:rgba(255,255,255,.15);padding:3px 8px;border-radius:12px}}
.section-hdr .chevron{{transition:transform .2s;font-size:14px}}
.section-hdr.open .chevron{{transform:rotate(180deg)}}
.section-body{{background:#fff;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;margin-bottom:16px;overflow:hidden}}
.section-body.collapsed{{display:none}}

/* Item cards */
.item-card{{border-bottom:1px solid #f0f4f8;padding:16px 18px;transition:background .15s}}
.item-card:last-child{{border-bottom:none}}
.item-card.reviewed{{background:#f0fff4}}
.item-header{{display:flex;align-items:flex-start;gap:8px;margin-bottom:8px;flex-wrap:wrap}}
.item-num{{background:#1a365d;color:#fff;padding:1px 7px;border-radius:4px;font-size:11px;font-weight:700;margin-top:2px;flex-shrink:0}}
.item-text{{font-size:15px;font-weight:600;color:#1a365d;flex:1;min-width:0;word-break:break-word}}
.item-meta{{display:flex;gap:12px;flex-wrap:wrap;font-size:12px;color:#718096;margin-bottom:10px}}
.item-meta span b{{color:#4a5568}}

/* Badges */
.badge{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;flex-shrink:0;margin-top:2px}}
.badge-routing{{background:#fed7d7;color:#c53030}}
.badge-model{{background:#fef3e2;color:#c05621}}
.badge-doubt{{background:#e9d8fd;color:#553c9a}}

/* Classification boxes */
.classification-row{{display:flex;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap}}
.cls-box{{flex:1;min-width:180px;padding:8px 12px;border-radius:6px;border:1px solid #e2e8f0}}
.cls-correct{{background:#f0fff4;border-color:#9ae6b4}}
.cls-predicted{{background:#fff5f0;border-color:#fbd38d}}
.cls-label{{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#718096;margin-bottom:2px}}
.cls-value{{font-size:13px;font-weight:600;color:#2d3748}}
.cls-arrow{{color:#718096;font-size:20px;flex-shrink:0}}

/* Interview details */
.interview-details{{margin-bottom:10px}}
.interview-details summary{{font-size:12px;color:#4a5568;cursor:pointer;padding:4px 0}}
.interview-pre{{background:#f7fafc;border:1px solid #e2e8f0;border-radius:6px;padding:10px 12px;font-size:12px;white-space:pre-wrap;word-break:break-word;margin-top:6px;color:#2d3748;line-height:1.5}}

/* CA Review */
.ca-review{{background:#fffbf5;border:1px solid #f6e2b8;border-radius:6px;padding:10px 14px}}
.ca-review-label{{font-size:12px;font-weight:700;color:#744210;margin-bottom:6px;text-transform:uppercase;letter-spacing:.04em}}
.ca-opt{{display:flex;align-items:flex-start;gap:8px;padding:4px 0;cursor:pointer;font-size:13px;color:#2d3748}}
.ca-opt input[type=radio]{{margin-top:3px;accent-color:#27ae60;cursor:pointer;flex-shrink:0}}
.row-input{{width:70px;padding:3px 6px;border:1px solid #cbd5e0;border-radius:4px;font-size:12px;margin:0 4px}}
.name-input{{width:180px;padding:3px 6px;border:1px solid #cbd5e0;border-radius:4px;font-size:12px}}
.row-input:focus,.name-input:focus{{outline:none;border-color:#1a365d;box-shadow:0 0 0 2px #bee3f8}}
.ca-note-row{{margin-top:6px}}
.note-input{{width:100%;padding:5px 8px;border:1px solid #cbd5e0;border-radius:4px;font-size:12px;color:#4a5568}}
.note-input:focus{{outline:none;border-color:#1a365d}}
.review-status{{font-size:11px;color:#27ae60;font-weight:700;min-height:16px;margin-top:4px}}

/* Non-interviewed table */
.ni-table{{width:100%;border-collapse:collapse;font-size:12px}}
.ni-table th{{background:#f7fafc;padding:8px 10px;text-align:left;font-weight:700;color:#4a5568;border-bottom:2px solid #e2e8f0}}
.ni-table td{{padding:7px 10px;border-bottom:1px solid #f0f4f8;color:#2d3748}}
.ni-table tr:last-child td{{border-bottom:none}}
.ni-table tr:hover td{{background:#f7fafc}}

/* Restore banner */
.restore-banner{{background:#ebf8ff;border:1px solid #90cdf4;padding:10px 14px;border-radius:6px;margin-bottom:14px;font-size:13px;display:flex;align-items:center;gap:10px}}
.restore-banner.hidden{{display:none}}
</style>
</head>
<body>
<div class="container">

<!-- Header -->
<div class="page-header">
  <h1>SSSS (Salem Stainless Steel) — Round 2 CA Review</h1>
  <div class="sub">Industry: Trading (Steel Distribution) &nbsp;|&nbsp; Run date: {run_date} &nbsp;|&nbsp; CA Rules: CA-001..CA-024 active</div>
</div>

<!-- Restore banner (shown if saved data found) -->
<div class="restore-banner hidden" id="restore-banner">
  <span>&#9998; Found saved responses — <a href="#" onclick="restoreAnswers();return false">Restore last session</a></span>
  <button class="btn btn-outline" style="padding:4px 10px;font-size:12px" onclick="document.getElementById('restore-banner').classList.add('hidden')">Dismiss</button>
</div>

<!-- Progress bar -->
<div class="progress-box">
  <div class="progress-lbl">
    <span>Review progress: <b id="reviewed-count">0</b> of <b>{len(interview_results)}</b> items reviewed</span>
    <span id="pct-lbl">0%</span>
  </div>
  <div class="pbar"><div class="pbar-fill" id="pbar-fill" style="width:0%"></div></div>
</div>

<!-- Stats cards -->
<div class="stats-grid">
  <div class="stat-card">
    <div class="stat-value">{total}</div>
    <div class="stat-label">Total Items</div>
  </div>
  <div class="stat-card">
    <div class="stat-value green">{correct_count}</div>
    <div class="stat-label">Correct</div>
  </div>
  <div class="stat-card">
    <div class="stat-value red">{wrong_count}</div>
    <div class="stat-label">Wrong</div>
  </div>
  <div class="stat-card">
    <div class="stat-value orange">{doubt_count}</div>
    <div class="stat-label">Doubts</div>
  </div>
  <div class="stat-card">
    <div class="stat-value {'green' if delta >= 0 else 'red'}">{accuracy_pct}%</div>
    <div class="stat-label">R2 Accuracy</div>
  </div>
  <div class="stat-card">
    <div class="stat-value {'delta-pos' if delta >= 0 else 'delta-neg'}">{delta:+.1f}pp</div>
    <div class="stat-label">vs Round 1</div>
  </div>
</div>

<!-- Round 1 vs Round 2 comparison -->
<div class="compare-block">
  <h3>Round 1 → Round 2 Comparison</h3>
  <div class="compare-row">
    <div class="compare-col">
      <label>Round 1 Accuracy</label>
      <div class="val r1">{round1_accuracy}%</div>
      <div style="font-size:12px;color:#718096">{round1_correct}/{round1_total} correct &nbsp;|&nbsp; {round1_wrong} wrong &nbsp;|&nbsp; {round1_doubts} doubts</div>
    </div>
    <div class="compare-col">
      <label>Round 2 Accuracy</label>
      <div class="val {'r2-better' if delta >= 0 else 'r2-worse'}">{accuracy_pct}%
        <span class="delta-chip {'delta-pos' if delta >= 0 else 'delta-neg'}">{delta:+.1f}pp</span>
      </div>
      <div style="font-size:12px;color:#718096">{correct_count}/{total} correct &nbsp;|&nbsp; {wrong_count} wrong &nbsp;|&nbsp; {doubt_count} doubts</div>
    </div>
    <div class="compare-col">
      <label>Error Analysis ({len(interview_results)} interviewed)</label>
      <div style="font-size:13px;margin-top:4px">
        <div><span style="color:#c53030;font-weight:700">{routing_bugs}</span> routing bugs — correct row not in options</div>
        <div><span style="color:#c05621;font-weight:700">{model_errors}</span> model errors — correct row available, wrong pick</div>
        <div><span style="color:#718096">{len(unique_wrong) - len(interview_results)}</span> not interviewed (beyond cap)</div>
      </div>
    </div>
  </div>
</div>

<!-- Action bar -->
<div class="action-bar">
  <button class="btn btn-green" onclick="exportJSON()">Export CA Responses (JSON)</button>
  <button class="btn btn-navy" onclick="expandAll()">Expand All</button>
  <button class="btn btn-outline" onclick="collapseAll()">Collapse All</button>
  <span style="font-size:12px;color:#718096;margin-left:auto">Responses auto-saved in browser localStorage</span>
</div>

<!-- SECTION A: Routing Bugs -->
<div class="section-block">
  <div class="section-hdr open" onclick="toggleSection('routing')">
    <h2>A. Routing Bugs — Correct Row Not in Options</h2>
    <span class="count">{routing_bugs} items</span>
    <span class="chevron">▼</span>
  </div>
  <div class="section-body" id="body-routing">
    <div style="background:#fff5f0;border-left:3px solid #e53e3e;padding:10px 16px;font-size:13px;color:#2d3748;border-right:1px solid #e2e8f0">
      <b>These items were routed to the wrong CMA section</b> — the correct row was never in the AI's option list.
      Fix requires a routing regex or section keyword update.
    </div>
    {routing_cards_html if routing_cards_html else '<div style="padding:16px;color:#718096">No routing bugs in interviewed items.</div>'}
  </div>
</div>

<!-- SECTION B: Model Errors -->
<div class="section-block">
  <div class="section-hdr open" onclick="toggleSection('model')">
    <h2>B. Model Errors — Correct Row Available, Wrong Pick</h2>
    <span class="count">{model_errors} items</span>
    <span class="chevron">▼</span>
  </div>
  <div class="section-body" id="body-model">
    <div style="background:#fffbf5;border-left:3px solid #e67e22;padding:10px 16px;font-size:13px;color:#2d3748;border-right:1px solid #e2e8f0">
      <b>The correct row was shown to the AI but it picked wrong</b> — fix requires a disambiguation rule or training example.
    </div>
    {model_error_cards_html if model_error_cards_html else '<div style="padding:16px;color:#718096">No model errors in interviewed items.</div>'}
  </div>
</div>

<!-- SECTION C: Not Interviewed -->
{_ni_section}

</div><!-- /container -->

<script>
// ── State ──────────────────────────────────────────────────────────────────────
const STATE_KEY = "ssss_round2_review";
let state = {{}};
let reviewedCount = 0;
const TOTAL_ITEMS = {len(interview_results)};

function loadState() {{
  try {{
    const saved = localStorage.getItem(STATE_KEY);
    if (saved) {{
      state = JSON.parse(saved);
      return true;
    }}
  }} catch(e) {{}}
  return false;
}}

function saveState() {{
  try {{ localStorage.setItem(STATE_KEY, JSON.stringify(state)); }} catch(e) {{}}
}}

// ── Restore saved answers ──────────────────────────────────────────────────────
function restoreAnswers() {{
  document.getElementById("restore-banner").classList.add("hidden");
  let restored = 0;
  for (const [cardId, val] of Object.entries(state)) {{
    if (cardId.startsWith("note_")) continue;
    const radio = document.querySelector(`[name="review-${{cardId}}"][value="${{val.choice}}"]`);
    if (radio) {{
      radio.checked = true;
      markCardReviewed(cardId, val.choice);
    }}
    if (val.row) {{
      const ri = document.getElementById(`row-${{cardId}}`);
      if (ri) ri.value = val.row;
    }}
    if (val.name) {{
      const ni = document.getElementById(`name-${{cardId}}`);
      if (ni) ni.value = val.name;
    }}
    const note = state[`note_${{cardId}}`];
    if (note) {{
      const ni = document.getElementById(`note-${{cardId}}`);
      if (ni) ni.value = note;
    }}
    restored++;
  }}
  updateProgress();
  console.log(`Restored ${{restored}} answers`);
}}

// ── Review update ──────────────────────────────────────────────────────────────
function updateReview(cardId, choice, row, name) {{
  state[cardId] = {{ choice, row, name }};
  saveState();
  markCardReviewed(cardId, choice);
  updateProgress();
}}

function updateNote(cardId, note) {{
  state[`note_${{cardId}}`] = note;
  saveState();
}}

function markCardReviewed(cardId, choice) {{
  const card = document.getElementById(`card-${{cardId}}`);
  if (card) card.classList.add("reviewed");
  const status = document.getElementById(`status-${{cardId}}`);
  if (status) {{
    const labels = {{ agree: "✓ Marked: AI correct, GT wrong", gt_correct: "✓ Marked: GT correct, AI wrong", other: "✓ Marked: Custom correction" }};
    status.textContent = labels[choice] || "✓ Reviewed";
  }}
}}

function updateProgress() {{
  const reviewed = Object.keys(state).filter(k => !k.startsWith("note_")).length;
  reviewedCount = reviewed;
  const pct = TOTAL_ITEMS > 0 ? Math.round(reviewed / TOTAL_ITEMS * 100) : 0;
  document.getElementById("reviewed-count").textContent = reviewed;
  document.getElementById("pct-lbl").textContent = pct + "%";
  document.getElementById("pbar-fill").style.width = pct + "%";
}}

// ── Export JSON ────────────────────────────────────────────────────────────────
function exportJSON() {{
  const interviewData = {interview_json_str};
  const caResponses = [];
  for (const [cardId, val] of Object.entries(state)) {{
    if (cardId.startsWith("note_")) continue;
    const note = state[`note_${{cardId}}`] || "";
    caResponses.push({{ card_id: cardId, choice: val.choice, correct_row: val.row, correct_name: val.name, note }});
  }}
  const output = {{
    export_date: new Date().toISOString(),
    company: "SSSS",
    round: 2,
    round2_accuracy: {accuracy_pct},
    round1_accuracy: {round1_accuracy},
    delta_pp: {delta},
    ca_responses: caResponses,
    interview_summary: interviewData.summary,
  }};
  const blob = new Blob([JSON.stringify(output, null, 2)], {{type: "application/json"}});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "SSSS_round2_ca_responses.json";
  a.click();
}}

// ── Section toggle ─────────────────────────────────────────────────────────────
function toggleSection(id) {{
  const body = document.getElementById("body-" + id);
  if (!body) return;
  body.classList.toggle("collapsed");
  // Toggle chevron on the clicked header
  const hdrs = document.querySelectorAll(".section-hdr");
  hdrs.forEach(h => {{
    if (h.getAttribute("onclick") && h.getAttribute("onclick").includes(`'${{id}}'`)) {{
      h.classList.toggle("open");
    }}
  }});
}}

function expandAll() {{
  document.querySelectorAll(".section-body").forEach(b => b.classList.remove("collapsed"));
  document.querySelectorAll(".section-hdr").forEach(h => h.classList.add("open"));
}}

function collapseAll() {{
  document.querySelectorAll(".section-body").forEach(b => b.classList.add("collapsed"));
  document.querySelectorAll(".section-hdr").forEach(h => h.classList.remove("open"));
}}

// ── Init ───────────────────────────────────────────────────────────────────────
window.addEventListener("DOMContentLoaded", () => {{
  const hasSaved = loadState();
  if (hasSaved && Object.keys(state).length > 0) {{
    document.getElementById("restore-banner").classList.remove("hidden");
  }}
  updateProgress();
}});
</script>
</body>
</html>"""

html_path = HTML_OUTPUT_DIR / "SSSS_review.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Saved HTML report → {html_path}")

print(f"\n{'='*70}")
print("  ALL DONE")
print(f"{'='*70}")
print(f"  Round 1 accuracy: {round1_accuracy}%")
print(f"  Round 2 accuracy: {accuracy_pct}%  (delta: {delta:+.2f}pp)")
print(f"  Routing bugs:     {routing_bugs}")
print(f"  Model errors:     {model_errors}")
print(f"  HTML report:      {html_path}")
print(f"  JSON files:       {OUTPUT_DIR}/SSSS_*.json")
