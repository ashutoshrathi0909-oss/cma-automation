#!/usr/bin/env python3
"""
Round 2 Accuracy Test + Interview + HTML Report — INPL only.

Steps:
  1. Load INPL GT and run ScopedClassifier on all items
  2. Analyze wrong entries (filter GT naming bugs, deduplicate)
  3. Interview up to 50 unique genuinely wrong items via DeepSeek V3
  4. Generate self-contained HTML report for CA review

Run:
  docker compose exec -T worker bash -c "cd /app && python test-results/round2/run_inpl.py"

Outputs (all in /app/test-results/round2/):
  INPL_accuracy_summary.json
  INPL_wrong_entries.json
  INPL_interview.json
  INPL_review.html
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, "/app")

# ─── Paths ────────────────────────────────────────────────────────────────────
GT_PATH = Path("/app/DOCS/extractions/INPL_classification_ground_truth.json")
CANONICAL_LABELS_PATH = Path("/app/CMA_Ground_Truth_v1/reference/canonical_labels.json")
OUTPUT_DIR = Path("/app/test-results/round2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── Cost guards ──────────────────────────────────────────────────────────────
MAX_ITEMS = 500
MAX_TOKENS = 500_000
TOKEN_REINIT = 450_000
MAX_INTERVIEWS = 50

# ─── Round 1 reference (post-CA-rules test, 2026-03-26) ──────────────────────
ROUND1 = {"total": 186, "correct": 39, "wrong": 139, "doubts": 8, "accuracy_pct": 20.97}

COMPANY = "INPL"
INDUSTRY = "manufacturing"


# ═════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def make_classifier():
    from app.services.classification.scoped_classifier import ScopedClassifier
    sc = ScopedClassifier()
    print(f"  [ScopedClassifier] sections={len(sc._contexts)} labels={len(sc._labels_by_row)}")
    return sc


def doubt_result(reason: str):
    from app.services.classification.ai_classifier import AIClassificationResult
    return AIClassificationResult(
        cma_field_name=None, cma_row=None, cma_sheet="input_sheet",
        broad_classification="", confidence=0.0, is_doubt=True,
        doubt_reason=reason, alternatives=[], classification_method="scoped_doubt",
    )


def doc_type_from_section(section: str, sheet_name: str = "", cma_row=None) -> str:
    """Infer document type from section text and sheet name."""
    combined = f"{section} {sheet_name}".lower()
    if any(kw in combined for kw in ["balance sheet", "bs", "assets", "liabilities", "equity"]):
        return "balance_sheet"
    if cma_row is not None and int(cma_row) >= 111:
        return "balance_sheet"
    return "profit_and_loss"


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 1: ACCURACY TEST
# ═════════════════════════════════════════════════════════════════════════════

print("=" * 70)
print(f"  ROUND 2 ACCURACY TEST — {COMPANY} ({INDUSTRY})")
print("=" * 70)
print()

# Load canonical labels for code-based lookup
with open(CANONICAL_LABELS_PATH) as f:
    _canonical = json.load(f)
sheetrow_to_code: dict[int, str] = {item["sheet_row"]: item["code"] for item in _canonical}
print(f"Loaded {len(sheetrow_to_code)} canonical label rows")

# Load INPL ground truth
with open(GT_PATH, encoding="utf-8") as f:
    raw_gt = json.load(f)

entries_raw = raw_gt if isinstance(raw_gt, list) else raw_gt.get("items", [])
entries = [
    {
        "raw_text": e.get("raw_text", ""),
        "section": e.get("section", ""),
        "amount": e.get("amount_rupees", e.get("amount")),
        "cma_row": e.get("correct_cma_row"),
        "cma_field_name": e.get("correct_cma_field", ""),
        "sheet_name": e.get("sheet_name", ""),
        "financial_year": e.get("financial_year", ""),
    }
    for e in entries_raw
]

if len(entries) > MAX_ITEMS:
    print(f"Cost guard: capping at {MAX_ITEMS} (GT has {len(entries)})")
    entries = entries[:MAX_ITEMS]

total = len(entries)
print(f"GT items: {total}")
print()

# Initialize classifier
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

    # Token budget guard — reinitialize if approaching limit
    if sc._total_tokens > TOKEN_REINIT:
        print(f"  [{i+1}] Token budget {sc._total_tokens:,} → reinitializing classifier")
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
        result = doubt_result(f"Exception: {e}")

    # Retry if token-budget doubt
    if result.is_doubt and result.doubt_reason and "token budget" in result.doubt_reason.lower():
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

    # Compare by field name (extractions GT has no cma_code)
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
            "financial_year": entry.get("financial_year", ""),
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
        })

    # Progress every 25 items
    if (i + 1) % 25 == 0:
        elapsed = time.time() - start
        n = i + 1
        correct_n = sum(r["is_correct"] for r in results)
        acc = correct_n / n * 100
        print(f"  [{n:3d}/{total}] acc={acc:.1f}%  tokens={sc._total_tokens:,}  elapsed={elapsed:.0f}s")
        sys.stdout.flush()

# Final stats
elapsed = time.time() - start
correct = sum(r["is_correct"] for r in results)
doubts = sum(r["is_doubt"] for r in results)
wrong = total - correct - doubts
accuracy_pct = round(correct / total * 100, 2) if total else 0.0

summary = {
    "company": COMPANY,
    "industry": INDUSTRY,
    "round": 2,
    "date": time.strftime("%Y-%m-%d"),
    "total_items": total,
    "correct": correct,
    "wrong": wrong,
    "doubts": doubts,
    "accuracy_pct": accuracy_pct,
    "elapsed_seconds": round(elapsed, 2),
    "tokens_used": sc._total_tokens,
    "round1_accuracy_pct": ROUND1["accuracy_pct"],
    "delta_pct": round(accuracy_pct - ROUND1["accuracy_pct"], 2),
}

with open(OUTPUT_DIR / "INPL_accuracy_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
with open(OUTPUT_DIR / "INPL_wrong_entries.json", "w") as f:
    json.dump(wrong_entries, f, indent=2, ensure_ascii=False)

delta_str = f"+{summary['delta_pct']:.2f}" if summary["delta_pct"] > 0 else f"{summary['delta_pct']:.2f}"
print(f"\n  {COMPANY}: {correct}/{total} correct ({accuracy_pct}%)")
print(f"  Round 1: {ROUND1['accuracy_pct']}%  →  Round 2: {accuracy_pct}%  ({delta_str}pp)")
print(f"  Wrong={wrong}  Doubts={doubts}  Elapsed={elapsed:.0f}s")


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 2: ANALYZE WRONG ENTRIES
# ═════════════════════════════════════════════════════════════════════════════

print(f"\n\n{'='*70}")
print("  PHASE 2: ANALYZING WRONG ENTRIES")
print(f"{'='*70}\n")

genuinely_wrong: list[dict] = []
offset_bugs: list[dict] = []

for item in wrong_entries:
    correct_f = (item.get("correct_cma_field") or "").strip().lower()
    predicted_f = (item.get("predicted_cma_field") or "").strip().lower()

    if item.get("is_doubt"):
        genuinely_wrong.append(item)
    elif correct_f and predicted_f and correct_f == predicted_f:
        # Field names match → GT row offset bug (row differs but field is same name)
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

print(f"  Total wrong:              {len(wrong_entries)}")
print(f"  GT naming offset bugs:    {len(offset_bugs)}")
print(f"  Genuinely wrong:          {len(genuinely_wrong)}")
print(f"  Unique genuinely wrong:   {len(unique_wrong)}")


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 3: INTERVIEW WRONG ITEMS
# ═════════════════════════════════════════════════════════════════════════════

print(f"\n\n{'='*70}")
print(f"  PHASE 3: INTERVIEWING WRONG ITEMS (max {MAX_INTERVIEWS})")
print(f"{'='*70}\n")

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

    # INPL is non-BCIPL → apply +1 offset for canonical label lookup
    correct_row_raw = item["correct_cma_row"]
    correct_row = (correct_row_raw + 1) if correct_row_raw else correct_row_raw

    # Look up names from classifier label map
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

    # Error type determination (before interview — routing check is definitive)
    error_type = "routing_bug" if not correct_in_list else "model_error"

    original_prompt = sc._build_prompt(raw_text, amount, section or "not specified", context)

    interview_q = f"""You classified this financial line item:
"{raw_text}" (section: "{section}", amount: {amount}, industry: {INDUSTRY})

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
   Examples: "Add a rule: X → Row Y", "Change routing pattern for X", "Add Row Y to options"
5. Write ONE Python regex pattern that would correctly route this item.

PART C — Classification:
6. Is this a ROUTING BUG or MODEL ERROR?
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

    interview_results.append({
        "index": i,
        "raw_text": raw_text,
        "section": section,
        "amount": amount,
        "financial_year": item.get("financial_year", ""),
        "correct_cma_row": correct_row,
        "correct_cma_row_gt": correct_row_raw,
        "correct_cma_field": item.get("correct_cma_field", ""),
        "correct_name": correct_name,
        "predicted_cma_row": predicted_row,
        "predicted_cma_field": item.get("predicted_cma_field", ""),
        "predicted_name": predicted_name,
        "confidence": item.get("confidence", 0),
        "is_doubt": item.get("is_doubt", False),
        "doubt_reason": item.get("doubt_reason"),
        "correct_in_options": correct_in_list,
        "error_type": error_type,
        "routed_to": sections_routed,
        "classification_method": item.get("classification_method", ""),
        "model_response": answer,
    })

    status = "IN_LIST" if correct_in_list else "NOT_IN_LIST"
    print(
        f"  [{i+1:2d}/{min(len(unique_wrong), MAX_INTERVIEWS)}] "
        f"{error_type:<12} | {status} | '{raw_text[:45]}'"
    )
    sys.stdout.flush()

# Summary
routing_bugs_count = sum(1 for r in interview_results if r["error_type"] == "routing_bug")
model_errors_count = sum(1 for r in interview_results if r["error_type"] == "model_error")

print(f"\n  Interviewed: {len(interview_results)}")
print(f"  Routing bugs (correct row not shown): {routing_bugs_count}")
print(f"  Model errors (correct row available):  {model_errors_count}")
print(f"  API calls: {api_calls}  Elapsed: {time.time()-interview_start:.0f}s")

# Save interview JSON
interview_output = {
    "meta": {
        "company": COMPANY,
        "industry": INDUSTRY,
        "date": time.strftime("%Y-%m-%d %H:%M"),
        "round": 2,
        "max_interviews": MAX_INTERVIEWS,
    },
    "accuracy": {
        "round1": ROUND1,
        "round2": summary,
    },
    "wrong_analysis": {
        "total_wrong": len(wrong_entries),
        "gt_naming_bugs": len(offset_bugs),
        "genuinely_wrong": len(genuinely_wrong),
        "unique_genuinely_wrong": len(unique_wrong),
        "interviewed": len(interview_results),
        "routing_bugs": routing_bugs_count,
        "model_errors": model_errors_count,
    },
    "interviews": interview_results,
}

with open(OUTPUT_DIR / "INPL_interview.json", "w") as f:
    json.dump(interview_output, f, indent=2, ensure_ascii=False)

print(f"\n  Saved → {OUTPUT_DIR / 'INPL_interview.json'}")


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 4: GENERATE HTML REPORT
# ═════════════════════════════════════════════════════════════════════════════

print(f"\n\n{'='*70}")
print("  PHASE 4: GENERATING HTML REPORT")
print(f"{'='*70}\n")


def _fmt_amount(amt) -> str:
    if amt is None:
        return "—"
    try:
        return f"₹{int(amt):,}"
    except Exception:
        return str(amt)


def _esc(s: str) -> str:
    """HTML-escape a string."""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _badge(text: str, cls: str) -> str:
    return f'<span class="badge badge-{cls}">{_esc(text)}</span>'


def build_html(
    summary: dict,
    wrong_entries: list[dict],
    offset_bugs: list[dict],
    genuinely_wrong: list[dict],
    unique_wrong: list[dict],
    interview_results: list[dict],
) -> str:
    r1 = summary.get("round1_accuracy_pct", ROUND1["accuracy_pct"])
    r2 = summary.get("accuracy_pct", 0)
    delta = summary.get("delta_pct", round(r2 - r1, 2))
    delta_str = f"+{delta:.2f}pp" if delta >= 0 else f"{delta:.2f}pp"
    delta_cls = "positive" if delta >= 0 else "negative"

    # Index interview results by raw_text + predicted for quick lookup
    interviewed_index: dict[str, dict] = {}
    for ir in interview_results:
        key = ir["raw_text"].strip().lower()
        interviewed_index[key] = ir

    # Prepare items for display (all wrong entries, enriched with interview data)
    items_html = []
    item_idx = 0

    # Group: routing bugs first (from interview), then model errors, then not analyzed
    routing_bug_items = [r for r in interview_results if r["error_type"] == "routing_bug"]
    model_error_items = [r for r in interview_results if r["error_type"] == "model_error"]

    def _render_interview_item(ir: dict, group_label: str) -> str:
        nonlocal item_idx
        item_idx += 1
        idx = item_idx
        raw = _esc(ir["raw_text"])
        section = _esc(ir.get("section", "—"))
        amt = _fmt_amount(ir.get("amount"))
        correct_field = _esc(ir.get("correct_cma_field", "—"))
        correct_row = ir.get("correct_cma_row_gt", ir.get("correct_cma_row", "?"))
        pred_field = _esc(ir.get("predicted_cma_field") or "DOUBT")
        pred_row = ir.get("predicted_cma_row", "?")
        conf = ir.get("confidence", 0)
        method = _esc(ir.get("classification_method", "—"))
        error_type = ir.get("error_type", "")
        routed = ", ".join(ir.get("routed_to", []))
        model_resp = _esc(ir.get("model_response", "—"))
        is_doubt = ir.get("is_doubt", False)

        badge = _badge("ROUTING BUG", "red") if error_type == "routing_bug" else _badge("MODEL ERROR", "orange")

        if is_doubt:
            pred_display = f'<span style="color:#c05621">DOUBT — {_esc(ir.get("doubt_reason",""))}</span>'
        else:
            pred_display = f"Row {pred_row} · {pred_field}"

        return f"""
<div class="q-card" data-type="{error_type}" id="item-{idx}">
  <div class="q-hdr">
    <span class="q-badge">#{idx}</span>
    <div style="flex:1">
      <div class="q-text">{raw}</div>
      <div style="font-size:12px;color:#718096;margin-top:3px">{section} · {amt} · FY{ir.get("financial_year","?")}</div>
    </div>
    {badge}
  </div>

  <table class="detail-table">
    <tr><td class="dt-label">Correct (GT)</td><td>Row {correct_row} · {correct_field}</td></tr>
    <tr><td class="dt-label">Predicted</td><td>{pred_display}</td></tr>
    <tr><td class="dt-label">Confidence</td><td>{conf:.2f} · Method: {method}</td></tr>
    <tr><td class="dt-label">Routed to</td><td>{_esc(routed)}</td></tr>
  </table>

  <details class="ai-resp">
    <summary>AI Interview Response</summary>
    <pre>{model_resp}</pre>
  </details>

  <div class="ca-review" data-item-id="{idx}">
    <div class="ca-review-label">CA Review:</div>
    <ul class="opts">
      <li class="opt" onclick="selectOpt(this)">
        <input type="radio" name="item_{idx}" value="agree_ai" data-item="{idx}">
        <span class="opt-name">Agree with AI — prediction Row {pred_row} ({pred_field}) is correct</span>
      </li>
      <li class="opt" onclick="selectOpt(this)">
        <input type="radio" name="item_{idx}" value="agree_gt" data-item="{idx}">
        <span class="opt-name">GT is correct — AI should have picked Row {correct_row} ({correct_field})</span>
      </li>
    </ul>
    <div class="other-row">
      <input type="radio" name="item_{idx}" value="other" data-item="{idx}" id="other_{idx}">
      <label for="other_{idx}" style="font-size:13px;cursor:pointer">AI is wrong, correct row is:</label>
      <input type="number" class="other-num" id="other_row_{idx}" placeholder="Row #" oninput="document.getElementById('other_{idx}').checked=true">
      <input type="text" class="other-name-input" id="other_name_{idx}" placeholder="field name (optional)" oninput="document.getElementById('other_{idx}').checked=true">
    </div>
  </div>
</div>"""

    def _render_not_analyzed_item(entry: dict) -> str:
        nonlocal item_idx
        item_idx += 1
        idx = item_idx
        raw = _esc(entry["raw_text"])
        section = _esc(entry.get("section", "—"))
        amt = _fmt_amount(entry.get("amount"))
        correct_field = _esc(entry.get("correct_cma_field", "—"))
        correct_row = entry.get("correct_cma_row", "?")
        pred_field = _esc(entry.get("predicted_cma_field") or "DOUBT")
        pred_row = entry.get("predicted_cma_row", "?")
        conf = entry.get("confidence", 0)
        method = _esc(entry.get("classification_method", "—"))
        is_doubt = entry.get("is_doubt", False)

        if is_doubt:
            pred_display = f'<span style="color:#c05621">DOUBT — {_esc(entry.get("doubt_reason",""))}</span>'
        else:
            pred_display = f"Row {pred_row} · {pred_field}"

        return f"""
<div class="q-card" data-type="not_analyzed" id="item-{idx}">
  <div class="q-hdr">
    <span class="q-badge" style="background:#718096">#{idx}</span>
    <div style="flex:1">
      <div class="q-text">{raw}</div>
      <div style="font-size:12px;color:#718096;margin-top:3px">{section} · {amt}</div>
    </div>
    <span class="badge badge-gray">NOT ANALYZED</span>
  </div>
  <table class="detail-table">
    <tr><td class="dt-label">Correct (GT)</td><td>Row {correct_row} · {correct_field}</td></tr>
    <tr><td class="dt-label">Predicted</td><td>{pred_display}</td></tr>
    <tr><td class="dt-label">Confidence</td><td>{conf:.2f} · Method: {method}</td></tr>
  </table>
  <div class="ca-review" data-item-id="{idx}">
    <div class="ca-review-label">CA Review:</div>
    <ul class="opts">
      <li class="opt" onclick="selectOpt(this)">
        <input type="radio" name="item_{idx}" value="agree_ai" data-item="{idx}">
        <span class="opt-name">Agree with AI — prediction Row {pred_row} ({pred_field}) is correct</span>
      </li>
      <li class="opt" onclick="selectOpt(this)">
        <input type="radio" name="item_{idx}" value="agree_gt" data-item="{idx}">
        <span class="opt-name">GT is correct — AI should have picked Row {correct_row} ({correct_field})</span>
      </li>
    </ul>
    <div class="other-row">
      <input type="radio" name="item_{idx}" value="other" data-item="{idx}" id="other_{idx}">
      <label for="other_{idx}" style="font-size:13px;cursor:pointer">AI is wrong, correct row is:</label>
      <input type="number" class="other-num" id="other_row_{idx}" placeholder="Row #" oninput="document.getElementById('other_{idx}').checked=true">
      <input type="text" class="other-name-input" id="other_name_{idx}" placeholder="field name (optional)" oninput="document.getElementById('other_{idx}').checked=true">
    </div>
  </div>
</div>"""

    # Build routing bug section
    routing_html = ""
    if routing_bug_items:
        routing_html = f"""
<div class="sec-block">
  <div class="sec-hdr" onclick="toggleSec(this)">
    <span class="sec-letter">R</span>
    <span class="sec-title-text">Routing Bugs — Correct Row Not Shown to AI</span>
    <span class="sec-count">{len(routing_bug_items)} items</span>
    <span class="chevron">▼</span>
  </div>
  <div class="sec-ctx">
    The AI was routed to the wrong CMA section — the correct CMA row was never in the options.
    These are fixable by improving keyword routing patterns.
  </div>
  <div class="sec-qs">
    {"".join(_render_interview_item(ir, "routing_bug") for ir in routing_bug_items)}
  </div>
</div>"""

    # Build model error section
    model_error_html = ""
    if model_error_items:
        model_error_html = f"""
<div class="sec-block">
  <div class="sec-hdr" onclick="toggleSec(this)">
    <span class="sec-letter">M</span>
    <span class="sec-title-text">Model Errors — Correct Row Available, AI Picked Wrong</span>
    <span class="sec-count">{len(model_error_items)} items</span>
    <span class="chevron">▼</span>
  </div>
  <div class="sec-ctx">
    The correct CMA row was presented to the AI but it selected a different row.
    These need rule additions or prompt improvements.
  </div>
  <div class="sec-qs">
    {"".join(_render_interview_item(ir, "model_error") for ir in model_error_items)}
  </div>
</div>"""

    # Build not-analyzed section (genuinely wrong items not in interview list)
    interviewed_texts = {ir["raw_text"].strip().lower() for ir in interview_results}
    not_analyzed = [
        e for e in genuinely_wrong
        if e["raw_text"].strip().lower() not in interviewed_texts
    ]

    not_analyzed_html = ""
    if not_analyzed:
        not_analyzed_html = f"""
<div class="sec-block">
  <div class="sec-hdr" onclick="toggleSec(this)">
    <span class="sec-letter">N</span>
    <span class="sec-title-text">Not Analyzed — Wrong Items Beyond Interview Limit</span>
    <span class="sec-count">{len(not_analyzed)} items</span>
    <span class="chevron rot">▼</span>
  </div>
  <div class="sec-ctx">
    These items were wrong but exceeded the {MAX_INTERVIEWS}-item interview limit. No AI analysis available.
  </div>
  <div class="sec-qs">
    {"".join(_render_not_analyzed_item(e) for e in not_analyzed[:100])}
  </div>
</div>"""

    total_ca_items = item_idx  # will be set after all sections rendered above
    # We need to know total BEFORE building HTML, so compute it:
    total_ca_items = len(routing_bug_items) + len(model_error_items) + len(not_analyzed[:100])

    # Offset bugs section (collapsed by default)
    offset_bugs_rows = "".join(
        f"""<tr>
          <td style="padding:4px 8px">{_esc(e['raw_text'][:60])}</td>
          <td style="padding:4px 8px">{_esc(e.get('correct_cma_field',''))}</td>
          <td style="padding:4px 8px">{_esc(e.get('predicted_cma_field',''))}</td>
          <td style="padding:4px 8px">{e.get('correct_cma_row','')}</td>
          <td style="padding:4px 8px">{e.get('predicted_cma_row','')}</td>
        </tr>"""
        for e in offset_bugs[:50]
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>INPL — Round 2 CMA Classification Review</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f0f4f8;color:#2d3748;font-size:14px;line-height:1.6}}
.container{{max-width:960px;margin:0 auto;padding:16px}}
.page-header{{background:#1a365d;color:#fff;padding:20px 24px;border-radius:8px;margin-bottom:14px}}
.page-header h1{{font-size:22px;font-weight:700;margin-bottom:4px}}
.page-header .sub{{opacity:.75;font-size:13px}}
.progress-box{{background:#fff;padding:12px 16px;border-radius:8px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.progress-lbl{{font-size:13px;color:#4a5568;margin-bottom:5px;display:flex;justify-content:space-between}}
.pbar{{background:#e2e8f0;border-radius:99px;height:10px;overflow:hidden}}
.pbar-fill{{background:#27ae60;height:100%;border-radius:99px;transition:width .3s}}
/* Summary grid */
.summary-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px;margin-bottom:14px}}
.stat-card{{background:#fff;border-radius:8px;padding:14px;box-shadow:0 1px 3px rgba(0,0,0,.08);text-align:center}}
.stat-card .value{{font-size:28px;font-weight:700;color:#1a365d}}
.stat-card .label{{font-size:12px;color:#718096;margin-top:2px}}
.stat-card.green .value{{color:#27ae60}}
.stat-card.red .value{{color:#e53e3e}}
.stat-card.orange .value{{color:#e67e22}}
.stat-card.positive{{border-top:3px solid #27ae60}}
.stat-card.negative{{border-top:3px solid #e53e3e}}
/* Comparison row */
.compare-row{{background:#fff;border-radius:8px;padding:14px 20px;margin-bottom:14px;box-shadow:0 1px 3px rgba(0,0,0,.08);display:flex;align-items:center;gap:24px;flex-wrap:wrap}}
.compare-block{{text-align:center;min-width:100px}}
.compare-block .val{{font-size:24px;font-weight:700}}
.compare-block .lbl{{font-size:11px;color:#718096;text-transform:uppercase}}
.compare-arrow{{font-size:28px;color:#4a5568}}
.delta-block{{background:#f0fff4;border:1px solid #9ae6b4;border-radius:8px;padding:8px 16px;text-align:center}}
.delta-block.neg{{background:#fff5f5;border-color:#feb2b2}}
.delta-val{{font-size:22px;font-weight:700;color:#27ae60}}
.delta-val.neg{{color:#e53e3e}}
/* Filter bar */
.filter-bar{{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;align-items:center}}
.filter-bar label{{font-size:13px;color:#4a5568;font-weight:500}}
.btn{{padding:8px 16px;border-radius:6px;border:none;cursor:pointer;font-size:13px;font-weight:500;transition:all .15s;white-space:nowrap}}
.btn-navy{{background:#1a365d;color:#fff}}.btn-navy:hover{{background:#2c5282}}
.btn-orange{{background:#e67e22;color:#fff}}.btn-orange:hover{{background:#d35400}}
.btn-green{{background:#27ae60;color:#fff}}.btn-green:hover{{background:#229954}}
.btn-outline{{background:#fff;color:#4a5568;border:1px solid #cbd5e0}}.btn-outline:hover{{border-color:#1a365d;color:#1a365d}}
.btn-outline.active{{background:#1a365d;color:#fff;border-color:#1a365d}}
/* Section */
.sec-block{{margin-bottom:14px}}
.sec-hdr{{background:#1a365d;color:#fff;padding:11px 16px;border-radius:8px 8px 0 0;cursor:pointer;display:flex;align-items:center;gap:10px;user-select:none}}
.sec-hdr.closed{{border-radius:8px}}
.sec-letter{{background:#e67e22;color:#fff;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;flex-shrink:0}}
.sec-letter.gray{{background:#718096}}
.sec-title-text{{font-weight:600;flex:1;font-size:15px}}
.sec-count{{font-size:12px;opacity:.8}}
.chevron{{transition:transform .2s;font-size:12px}}
.chevron.rot{{transform:rotate(180deg)}}
.sec-ctx{{background:#fffbf5;border-left:3px solid #e67e22;padding:10px 14px;font-size:13px;color:#2d3748;border-right:1px solid #e2e8f0}}
.sec-qs{{background:#fff;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;overflow:hidden}}
/* Question card */
.q-card{{padding:16px;border-bottom:1px solid #f0f4f8;transition:background .15s}}
.q-card:last-child{{border-bottom:none}}
.q-card.reviewed{{background:#f0fff4}}
.q-hdr{{display:flex;align-items:flex-start;gap:9px;margin-bottom:8px}}
.q-badge{{background:#1a365d;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;flex-shrink:0;margin-top:2px}}
.q-text{{font-size:15px;font-weight:600;color:#1a365d}}
/* Badges */
.badge{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;white-space:nowrap}}
.badge-red{{background:#fff5f5;color:#c53030;border:1px solid #feb2b2}}
.badge-orange{{background:#fffaf0;color:#c05621;border:1px solid #fbd38d}}
.badge-gray{{background:#f7fafc;color:#4a5568;border:1px solid #e2e8f0}}
/* Detail table */
.detail-table{{width:100%;border-collapse:collapse;margin-bottom:10px;font-size:13px}}
.detail-table tr:nth-child(even){{background:#f7fafc}}
.detail-table td{{padding:5px 10px;border:1px solid #e2e8f0;vertical-align:top}}
.dt-label{{font-weight:600;color:#4a5568;white-space:nowrap;width:130px}}
/* AI response */
.ai-resp{{margin-bottom:10px;font-size:13px}}
.ai-resp summary{{cursor:pointer;color:#4a5568;font-weight:500;padding:4px 0}}
.ai-resp pre{{background:#f7fafc;border:1px solid #e2e8f0;border-radius:4px;padding:10px;white-space:pre-wrap;word-wrap:break-word;font-size:12px;margin-top:6px;line-height:1.5}}
/* CA review */
.ca-review{{background:#f7fafc;border:1px solid #e2e8f0;border-radius:6px;padding:12px}}
.ca-review-label{{font-size:12px;font-weight:700;color:#1a365d;margin-bottom:8px;text-transform:uppercase;letter-spacing:.04em}}
.opts{{list-style:none;margin-bottom:8px}}
.opt{{padding:6px 10px;border-radius:6px;margin-bottom:3px;display:flex;align-items:center;gap:8px;cursor:pointer;border:1px solid transparent}}
.opt:hover{{background:#ebf8ff}}
.opt.sel{{background:#f0fff4;border-color:#9ae6b4}}
.opt input[type=radio]{{accent-color:#27ae60;cursor:pointer;flex-shrink:0}}
.opt-name{{color:#2d3748;flex:1;font-size:13px}}
.other-row{{display:flex;align-items:center;gap:8px;padding:4px 10px;flex-wrap:wrap}}
.other-row input[type=radio]{{accent-color:#27ae60}}
.other-num{{padding:4px 8px;border:1px solid #cbd5e0;border-radius:4px;width:80px;font-size:13px}}
.other-num:focus{{outline:none;border-color:#1a365d}}
.other-name-input{{padding:4px 8px;border:1px solid #cbd5e0;border-radius:4px;font-size:13px;flex:1;min-width:160px}}
.other-name-input:focus{{outline:none;border-color:#27ae60}}
/* Offset bugs table */
.bugs-table{{width:100%;border-collapse:collapse;font-size:12px}}
.bugs-table th{{background:#e2e8f0;padding:5px 8px;text-align:left;border:1px solid #cbd5e0}}
.bugs-table td{{border:1px solid #e2e8f0}}
/* Bottom actions */
.bottom-actions{{display:flex;gap:10px;margin-top:20px;flex-wrap:wrap;justify-content:center}}
</style>
</head>
<body>
<div class="container">

<!-- Header -->
<div class="page-header">
  <h1>INPL — Round 2 CMA Classification Review</h1>
  <div class="sub">Manufacturing Industry · {summary.get('date', time.strftime('%Y-%m-%d'))} · {total} items tested</div>
</div>

<!-- Progress bar -->
<div class="progress-box">
  <div class="progress-lbl">
    <span>CA Review Progress</span>
    <span id="progress-text">0 / {total_ca_items} reviewed</span>
  </div>
  <div class="pbar"><div class="pbar-fill" id="pbar-fill" style="width:0%"></div></div>
</div>

<!-- Round 1 vs Round 2 comparison -->
<div class="compare-row">
  <div class="compare-block">
    <div class="val" style="color:#718096">{ROUND1['accuracy_pct']}%</div>
    <div class="lbl">Round 1 Accuracy</div>
    <div style="font-size:11px;color:#a0aec0">{ROUND1['correct']}/{ROUND1['total']} correct</div>
  </div>
  <div class="compare-arrow">→</div>
  <div class="compare-block">
    <div class="val" style="color:#1a365d">{r2}%</div>
    <div class="lbl">Round 2 Accuracy</div>
    <div style="font-size:11px;color:#a0aec0">{summary['correct']}/{summary['total_items']} correct</div>
  </div>
  <div class="delta-block{' neg' if delta < 0 else ''}">
    <div class="delta-val{' neg' if delta < 0 else ''}">{delta_str}</div>
    <div style="font-size:11px;color:#718096">delta</div>
  </div>
</div>

<!-- Summary cards -->
<div class="summary-grid">
  <div class="stat-card"><div class="value">{summary['total_items']}</div><div class="label">Total Items</div></div>
  <div class="stat-card green"><div class="value">{summary['correct']}</div><div class="label">Correct</div></div>
  <div class="stat-card red"><div class="value">{summary['wrong']}</div><div class="label">Wrong</div></div>
  <div class="stat-card orange"><div class="value">{summary['doubts']}</div><div class="label">Doubts</div></div>
  <div class="stat-card {'positive' if delta >= 0 else 'negative'}"><div class="value">{r2}%</div><div class="label">Round 2 Accuracy</div></div>
  <div class="stat-card"><div class="value">{len(offset_bugs)}</div><div class="label">GT Naming Bugs</div></div>
  <div class="stat-card"><div class="value">{routing_bugs_count}</div><div class="label">Routing Bugs</div></div>
  <div class="stat-card"><div class="value">{model_errors_count}</div><div class="label">Model Errors</div></div>
</div>

<!-- Filter bar -->
<div class="filter-bar">
  <label>Filter:</label>
  <button class="btn btn-outline active" id="filter-all" onclick="filterItems('all', this)">All ({total_ca_items})</button>
  <button class="btn btn-outline" id="filter-routing_bug" onclick="filterItems('routing_bug', this)">Routing Bugs ({routing_bugs_count})</button>
  <button class="btn btn-outline" id="filter-model_error" onclick="filterItems('model_error', this)">Model Errors ({model_errors_count})</button>
  <button class="btn btn-outline" id="filter-not_analyzed" onclick="filterItems('not_analyzed', this)">Not Analyzed ({len(not_analyzed[:100])})</button>
</div>

<!-- MAIN CONTENT: Items grouped by error type -->
{routing_html}
{model_error_html}
{not_analyzed_html}

<!-- GT Naming Bugs (collapsed) -->
<details style="margin-bottom:14px">
  <summary style="cursor:pointer;background:#fff;padding:12px 16px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.08);font-weight:600;color:#4a5568">
    GT Naming Bugs — Same Row, Different Field Name ({len(offset_bugs)} items, not real errors)
  </summary>
  <div style="background:#fff;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;overflow:hidden;margin-top:-2px">
    <table class="bugs-table">
      <thead><tr><th>Item</th><th>GT Field</th><th>Predicted Field</th><th>GT Row</th><th>Pred Row</th></tr></thead>
      <tbody>{offset_bugs_rows}</tbody>
    </table>
  </div>
</details>

<!-- Bottom actions -->
<div class="bottom-actions">
  <button class="btn btn-green" onclick="exportJSON()">Export CA Responses (JSON)</button>
  <button class="btn btn-navy" onclick="window.scrollTo(0,0)">Back to Top</button>
</div>

</div><!-- /container -->

<script>
const TOTAL_ITEMS = {total_ca_items};
let reviewedCount = 0;
const reviewedSet = new Set();

function updateProgress() {{
  const pct = TOTAL_ITEMS > 0 ? (reviewedCount / TOTAL_ITEMS) * 100 : 0;
  document.getElementById('pbar-fill').style.width = pct + '%';
  document.getElementById('progress-text').textContent = reviewedCount + ' / ' + TOTAL_ITEMS + ' reviewed';
}}

function selectOpt(optEl) {{
  const radioEl = optEl.querySelector('input[type=radio]');
  if (!radioEl) return;
  radioEl.checked = true;
  const card = optEl.closest('.q-card');
  if (!card) return;
  card.querySelectorAll('.opt').forEach(o => o.classList.remove('sel'));
  optEl.classList.add('sel');
  const itemId = card.id;
  if (!reviewedSet.has(itemId)) {{
    reviewedSet.add(itemId);
    reviewedCount++;
    updateProgress();
  }}
  card.classList.add('reviewed');
}}

function toggleSec(hdr) {{
  const qs = hdr.nextElementSibling;
  const ctx = qs ? qs.nextElementSibling : null;
  const chevron = hdr.querySelector('.chevron');
  // Find the sec-qs element
  let el = hdr.nextElementSibling;
  while (el && !el.classList.contains('sec-qs')) el = el.nextElementSibling;
  if (!el) return;
  const isHidden = el.style.display === 'none';
  el.style.display = isHidden ? '' : 'none';
  if (chevron) chevron.classList.toggle('rot', isHidden);
  hdr.classList.toggle('closed', !isHidden);
}}

function filterItems(type, btn) {{
  document.querySelectorAll('.filter-bar .btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.q-card').forEach(card => {{
    if (type === 'all' || card.dataset.type === type) {{
      card.style.display = '';
    }} else {{
      card.style.display = 'none';
    }}
  }});
}}

function exportJSON() {{
  const out = {{}};
  document.querySelectorAll('.ca-review').forEach(rv => {{
    const itemId = rv.dataset.itemId;
    const radios = rv.querySelectorAll('input[type=radio]');
    let selected = null;
    radios.forEach(r => {{ if (r.checked) selected = r.value; }});
    const otherRow = rv.querySelector('.other-num') ? rv.querySelector('.other-num').value : '';
    const otherName = rv.querySelector('.other-name-input') ? rv.querySelector('.other-name-input').value : '';
    const rawText = rv.closest('.q-card').querySelector('.q-text').textContent;
    out['item_' + itemId] = {{
      raw_text: rawText,
      ca_response: selected,
      correct_row_if_other: otherRow || null,
      correct_name_if_other: otherName || null,
    }};
  }});
  const blob = new Blob([JSON.stringify(out, null, 2)], {{type: 'application/json'}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'INPL_round2_ca_responses.json';
  a.click();
  URL.revokeObjectURL(url);
}}

// Wire up all opts on page load
document.querySelectorAll('.opt').forEach(opt => {{
  opt.addEventListener('click', function() {{ selectOpt(this); }});
}});
</script>
</body>
</html>"""
    return html


# ── Generate and save ──────────────────────────────────────────────────────────
html_content = build_html(
    summary=summary,
    wrong_entries=wrong_entries,
    offset_bugs=offset_bugs,
    genuinely_wrong=genuinely_wrong,
    unique_wrong=unique_wrong,
    interview_results=interview_results,
)

html_path = OUTPUT_DIR / "INPL_review.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"  HTML report saved → {html_path}")
print(f"  Size: {html_path.stat().st_size / 1024:.1f} KB")


# ═════════════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ═════════════════════════════════════════════════════════════════════════════

print(f"\n\n{'='*70}")
print(f"  DONE — ALL OUTPUTS IN {OUTPUT_DIR}")
print(f"{'='*70}")
print(f"  INPL_accuracy_summary.json")
print(f"  INPL_wrong_entries.json  ({len(wrong_entries)} items)")
print(f"  INPL_interview.json      ({len(interview_results)} interviews)")
print(f"  INPL_review.html         (CA review report)")
print()
print(f"  Round 1 accuracy: {ROUND1['accuracy_pct']}%  ({ROUND1['correct']}/{ROUND1['total']})")
print(f"  Round 2 accuracy: {accuracy_pct}%  ({correct}/{total})")
delta = accuracy_pct - ROUND1["accuracy_pct"]
delta_s = f"+{delta:.2f}" if delta >= 0 else f"{delta:.2f}"
print(f"  Delta:            {delta_s}pp")
print()
print(f"  GT naming bugs:   {len(offset_bugs)}")
print(f"  Genuinely wrong:  {len(genuinely_wrong)}")
print(f"  Routing bugs:     {routing_bugs_count}")
print(f"  Model errors:     {model_errors_count}")
print(f"  Tokens used:      {sc._total_tokens:,}")
print()
