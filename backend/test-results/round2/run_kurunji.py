#!/usr/bin/env python3
"""
Round 2: Kurunji_Retail — Accuracy Test + Interview + HTML Report.

Steps:
  1. Accuracy test (classify all GT items with current scoped_classifier)
  2. Analyze wrong entries (filter offset bugs, deduplicate)
  3. Interview (routing check for all + model explanation for MAX 50)
  4. Generate self-contained HTML report

Run:
  docker compose exec -T worker bash -c "cd /app && python test-results/round2/run_kurunji.py"
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, "/app")

# ─── Configuration ────────────────────────────────────────────────────────────
COMPANY  = "Kurunji_Retail"
INDUSTRY = "trading"

GT_PATH             = Path("/app/DOCS/extractions/Kurunji_Retail_classification_ground_truth.json")
ROUND1_SUMMARY_PATH = Path("/app/test-results/post-ca-rules/Kurunji_Retail_accuracy_summary.json")
CANONICAL_LABELS    = Path("/app/CMA_Ground_Truth_v1/reference/canonical_labels.json")

OUTPUT_DIR = Path("/app/test-results/round2")
HTML_DIR   = Path("/app/DOCS/test-results/round2")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
HTML_DIR.mkdir(parents=True, exist_ok=True)

# Cost guards
MAX_ITEMS        = 500
TOKEN_REINIT     = 450_000
MAX_INTERVIEWS   = 50   # API calls for model explanation


# ─── Helpers ─────────────────────────────────────────────────────────────────

def doc_type_from_section(section: str, sheet_name: str = "", cma_row=None) -> str:
    combined = f"{section} {sheet_name}".lower()
    if any(kw in combined for kw in ["balance sheet", "bs", "assets", "liabilities", "equity"]):
        return "balance_sheet"
    if cma_row is not None and int(cma_row) >= 111:
        return "balance_sheet"
    return "profit_and_loss"


def make_classifier():
    from app.services.classification.scoped_classifier import ScopedClassifier
    sc = ScopedClassifier()
    print(f"    [SC] sections={len(sc._contexts)} labels={len(sc._labels_by_row)}")
    return sc


def make_doubt(reason: str):
    from app.services.classification.ai_classifier import AIClassificationResult
    return AIClassificationResult(
        cma_field_name=None, cma_row=None, cma_sheet="input_sheet",
        broad_classification="", confidence=0.0, is_doubt=True,
        doubt_reason=reason, alternatives=[], classification_method="scoped_doubt",
    )


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 1 — ACCURACY TEST
# ═════════════════════════════════════════════════════════════════════════════

print("=" * 70)
print(f"  ROUND 2 — {COMPANY} — ACCURACY TEST")
print("=" * 70)

with open(GT_PATH, encoding="utf-8") as fh:
    raw = json.load(fh)

items_raw = raw if isinstance(raw, list) else raw.get("items", [])
entries = [
    {
        "raw_text":      e.get("raw_text", ""),
        "section":       e.get("section", ""),
        "amount":        e.get("amount_rupees", e.get("amount")),
        "correct_row":   e.get("correct_cma_row"),
        "correct_field": e.get("correct_cma_field", ""),
        "sheet_name":    e.get("sheet_name", ""),
    }
    for e in items_raw
]

if len(entries) > MAX_ITEMS:
    print(f"Cost guard: capping at {MAX_ITEMS} (GT has {len(entries)})")
    entries = entries[:MAX_ITEMS]

total = len(entries)
print(f"GT items: {total}\n")

with open(CANONICAL_LABELS) as fh:
    _canonical = json.load(fh)
sheetrow_to_code: dict[int, str] = {item["sheet_row"]: item["code"] for item in _canonical}

sc = make_classifier()
print()

results: list[dict]     = []
wrong_entries: list[dict] = []
t0 = time.time()

for i, e in enumerate(entries):
    raw_text      = e["raw_text"]
    section       = e["section"]
    amount        = e["amount"]
    correct_row   = e["correct_row"]
    correct_field = e["correct_field"]
    doc_type      = doc_type_from_section(section, e.get("sheet_name", ""), correct_row)

    if sc._total_tokens > TOKEN_REINIT:
        print(f"  [{i+1}] Reinit (tokens={sc._total_tokens:,})")
        sc = make_classifier()

    try:
        res = sc.classify_sync(
            raw_text=raw_text, amount=amount, section=section,
            industry_type=INDUSTRY, document_type=doc_type, fuzzy_candidates=[],
        )
    except Exception as ex:
        res = make_doubt(f"Exception: {ex}")

    # Reinit + retry on token-budget doubt
    if res.is_doubt and res.doubt_reason and "token budget" in res.doubt_reason.lower():
        sc = make_classifier()
        try:
            res = sc.classify_sync(
                raw_text=raw_text, amount=amount, section=section,
                industry_type=INDUSTRY, document_type=doc_type, fuzzy_candidates=[],
            )
        except Exception as ex2:
            res = make_doubt(f"Retry failed: {ex2}")

    predicted_row = res.cma_row

    # Correctness: field name comparison (extractions GT has no codes)
    if correct_field and res.cma_field_name:
        ok = (not res.is_doubt) and (
            correct_field.strip().lower() == res.cma_field_name.strip().lower()
        )
    else:
        ok = (not res.is_doubt) and (predicted_row == correct_row)

    results.append({"ok": ok, "doubt": res.is_doubt})

    if not ok:
        wrong_entries.append({
            "raw_text":              raw_text,
            "section":               section,
            "amount":                amount,
            "correct_cma_row":       correct_row,
            "correct_cma_field":     correct_field,
            "predicted_cma_row":     predicted_row,
            "predicted_cma_field":   res.cma_field_name,
            "confidence":            res.confidence,
            "is_doubt":              res.is_doubt,
            "doubt_reason":          res.doubt_reason,
            "classification_method": res.classification_method,
            "document_type":         doc_type,
            "sheet_name":            e.get("sheet_name", ""),
        })

    if (i + 1) % 25 == 0:
        n   = i + 1
        acc = sum(r["ok"] for r in results) / n * 100
        print(f"  [{n:3d}/{total}] acc={acc:.1f}% tokens={sc._total_tokens:,} t={time.time()-t0:.0f}s")
        sys.stdout.flush()

elapsed  = time.time() - t0
correct  = sum(r["ok"] for r in results)
doubts   = sum(r["doubt"] for r in results)
wrong_n  = total - correct - doubts
acc_pct  = round(correct / total * 100, 2) if total else 0.0

print(f"\n  RESULT: {correct}/{total} ({acc_pct}%)  wrong={wrong_n} doubt={doubts}  {elapsed:.0f}s")

summary = {
    "company": COMPANY, "industry": INDUSTRY, "total_items": total,
    "correct": correct, "wrong": wrong_n, "doubts": doubts,
    "accuracy_pct": acc_pct, "elapsed_seconds": round(elapsed, 2),
}

with open(OUTPUT_DIR / f"{COMPANY}_accuracy_summary.json", "w") as fh:
    json.dump(summary, fh, indent=2)
with open(OUTPUT_DIR / f"{COMPANY}_wrong_entries.json", "w") as fh:
    json.dump(wrong_entries, fh, indent=2)
print(f"Saved accuracy summary + {len(wrong_entries)} wrong entries → {OUTPUT_DIR}")


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 2 — ANALYZE WRONG ENTRIES
# ═════════════════════════════════════════════════════════════════════════════

print(f"\n{'─'*60}")
print("  ANALYZE WRONG ENTRIES")
print(f"{'─'*60}")

genuinely_wrong: list[dict] = []
offset_bugs:     list[dict] = []

for item in wrong_entries:
    cf = (item.get("correct_cma_field") or "").strip().lower()
    pf = (item.get("predicted_cma_field") or "").strip().lower()
    if item.get("is_doubt"):
        genuinely_wrong.append(item)
    elif cf and pf and cf == pf:
        offset_bugs.append(item)
    else:
        genuinely_wrong.append(item)

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

print(f"  Total wrong:     {len(wrong_entries)}")
print(f"  GT offset bugs:  {len(offset_bugs)}")
print(f"  Genuinely wrong: {len(genuinely_wrong)}")
print(f"  Unique:          {len(unique_wrong)}")


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 3 — INTERVIEW
# ═════════════════════════════════════════════════════════════════════════════

print(f"\n{'─'*60}")
print(f"  INTERVIEW — ROUTING CHECK (all) + EXPLANATION (max {MAX_INTERVIEWS})")
print(f"{'─'*60}")

from openai import OpenAI
oai = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

interview_results: list[dict] = []
api_calls = 0
t1 = time.time()

for i, item in enumerate(unique_wrong):
    raw_text  = item["raw_text"]
    section   = item.get("section", "")
    amount    = item.get("amount")
    pred_row  = item.get("predicted_cma_row")
    doc_type  = item.get("document_type", "profit_and_loss")

    # GT offset: extractions format rows are 1 behind canonical labels
    crr         = item["correct_cma_row"]
    correct_row = (crr + 1) if crr is not None else crr

    correct_name = sc._labels_by_row.get(correct_row, {}).get("name", f"Row {correct_row}")
    pred_name    = (
        sc._labels_by_row.get(pred_row, {}).get("name", f"Row {pred_row}")
        if pred_row else "DOUBT"
    )

    # Routing check — deterministic, no API call
    sections = sc._route_section(raw_text, section or "", doc_type)
    if len(sections) == 1:
        ctx = sc._contexts.get(sections[0]) or sc._contexts["admin_expense"]
    else:
        ctx = sc._merge_contexts(sections)

    avail   = [r["sheet_row"] for r in ctx.cma_rows]
    in_list = correct_row in avail
    error_type = "routing_bug" if not in_list else "model_error"

    # Model explanation — API call, max MAX_INTERVIEWS
    model_response = None
    if i < MAX_INTERVIEWS:
        snippet = sc._build_prompt(raw_text, amount, section or "n/a", ctx)[:1500]
        q = (
            f'You classified: "{raw_text}" (section: "{section}")\n'
            f"You chose: Row {pred_row} ({pred_name})\n"
            f"Correct: Row {correct_row} ({correct_name})\n"
            f'Was correct row in your options? {"YES" if in_list else "NO"}\n\n'
            f"Prompt (truncated):\n---\n{snippet}\n---\n\n"
            f"Briefly (<=80 words): why did classification fail? What would fix it?"
        )
        try:
            resp = oai.chat.completions.create(
                model="deepseek/deepseek-chat",
                messages=[{"role": "user", "content": q}],
                max_tokens=150,
                temperature=0.0,
            )
            model_response = resp.choices[0].message.content.strip()
            api_calls += 1
        except Exception as ex:
            model_response = f"ERROR: {ex}"

    interview_results.append({
        "index":               i,
        "raw_text":            raw_text,
        "section":             section,
        "amount":              amount,
        "correct_cma_row_gt":  crr,
        "correct_cma_row":     correct_row,
        "correct_cma_name":    correct_name,
        "correct_cma_field":   item.get("correct_cma_field", ""),
        "predicted_cma_row":   pred_row,
        "predicted_cma_name":  pred_name,
        "predicted_cma_field": item.get("predicted_cma_field", ""),
        "confidence":          item.get("confidence", 0.0),
        "is_doubt":            item.get("is_doubt", False),
        "doubt_reason":        item.get("doubt_reason", ""),
        "classification_method": item.get("classification_method", ""),
        "routed_to":           sections,
        "correct_row_in_options": in_list,
        "error_type":          error_type,
        "model_response":      model_response,
        "document_type":       doc_type,
    })

    tag = "ROUT" if not in_list else "MODL"
    print(
        f"[{i+1:2d}] {tag} | {raw_text[:44]:<44} | "
        f"c={correct_row} p={pred_row if pred_row else 'D'}"
    )
    sys.stdout.flush()

routing_bugs = sum(1 for r in interview_results if r["error_type"] == "routing_bug")
model_errors = sum(1 for r in interview_results if r["error_type"] == "model_error")

print(f"\n  Routing bugs: {routing_bugs}  |  Model errors: {model_errors}  |  API calls: {api_calls}")

interview_out = {
    "summary": {
        "company": COMPANY, "industry": INDUSTRY,
        "total_wrong":         len(wrong_entries),
        "offset_bugs":         len(offset_bugs),
        "genuinely_wrong":     len(genuinely_wrong),
        "unique_genuinely_wrong": len(unique_wrong),
        "analyzed":            len(interview_results),
        "routing_bugs":        routing_bugs,
        "model_errors":        model_errors,
        "api_calls":           api_calls,
        "elapsed_seconds":     round(time.time() - t1, 2),
    },
    "interviews": interview_results,
}

with open(OUTPUT_DIR / f"{COMPANY}_interview.json", "w", encoding="utf-8") as fh:
    json.dump(interview_out, fh, indent=2, ensure_ascii=False)
print(f"Saved interview → {OUTPUT_DIR / f'{COMPANY}_interview.json'}")


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 4 — GENERATE HTML REPORT
# ═════════════════════════════════════════════════════════════════════════════

print(f"\n{'─'*60}")
print("  GENERATE HTML REPORT")
print(f"{'─'*60}")

round1 = {"accuracy_pct": 26.47, "correct": 36, "wrong": 61, "doubts": 39, "total_items": 136}
if ROUND1_SUMMARY_PATH.exists():
    with open(ROUND1_SUMMARY_PATH) as fh:
        round1 = json.load(fh)

delta     = round(acc_pct - round1["accuracy_pct"], 2)
delta_str = f"+{delta:.2f}" if delta >= 0 else f"{delta:.2f}"
today     = time.strftime("%Y-%m-%d")

routing_bug_items = [r for r in interview_results if r["error_type"] == "routing_bug"]
model_error_items = [r for r in interview_results if r["error_type"] == "model_error"]

# ── Build data dict for JavaScript embedding ──────────────────────────────────
report_data = {
    "company":         COMPANY,
    "industry":        INDUSTRY,
    "date":            today,
    "round2":          summary,
    "round1":          round1,
    "delta":           delta,
    "offset_bugs":     len(offset_bugs),
    "genuinely_wrong": len(genuinely_wrong),
    "unique_wrong":    len(unique_wrong),
    "routing_bugs":    routing_bugs,
    "model_errors":    model_errors,
    "items":           interview_results,
}
data_json = json.dumps(report_data, ensure_ascii=False, indent=None)


# ── Item card HTML builder ────────────────────────────────────────────────────

def item_card_html(item: dict) -> str:
    idx        = item["index"]
    rt         = item["raw_text"].replace("<", "&lt;").replace(">", "&gt;")
    sec        = (item.get("section") or "—").replace("<", "&lt;")
    amount     = item.get("amount")
    amt_str    = f"&#8377;{amount:,.0f}" if amount else "N/A"

    cf         = (item.get("correct_cma_field") or "").replace("<", "&lt;")
    cr         = item.get("correct_cma_row", "")
    cn         = (item.get("correct_cma_name") or cf).replace("<", "&lt;")

    pf         = (item.get("predicted_cma_field") or "").replace("<", "&lt;")
    pr         = item.get("predicted_cma_row", "")
    pn         = (item.get("predicted_cma_name") or pf or "DOUBT").replace("<", "&lt;")

    conf       = item.get("confidence", 0.0)
    is_doubt   = item.get("is_doubt", False)
    dr         = (item.get("doubt_reason") or "")[:80]
    method     = item.get("classification_method", "")
    error_type = item.get("error_type", "")
    routed     = ", ".join(item.get("routed_to", []))
    in_opts    = item.get("correct_row_in_options", False)
    model_resp = item.get("model_response") or ""

    # Error type badge
    if error_type == "routing_bug":
        tag = '<span class="tag tag-routing">&#9888; Routing Bug &mdash; correct row was NOT in AI&rsquo;s options</span>'
    elif error_type == "model_error":
        tag = '<span class="tag tag-model">&#8226; Model Error &mdash; correct row was available</span>'
    else:
        tag = '<span class="tag tag-neutral">Unanalyzed</span>'

    # Predicted box
    if is_doubt:
        pred_box = (
            '<div class="row-box doubt">'
            '<div class="row-lbl doubt">AI Result</div>'
            f'<div class="row-name">Doubt &mdash; low confidence</div>'
            f'<div class="row-num">{dr}</div>'
            '</div>'
        )
    else:
        pred_box = (
            '<div class="row-box predicted">'
            '<div class="row-lbl predicted">AI Predicted</div>'
            f'<div class="row-name">{pn}</div>'
            f'<div class="row-num">Row {pr} &middot; {method} &middot; conf={conf:.2f}</div>'
            '</div>'
        )

    # Model explanation block
    exp_html = ""
    if model_resp:
        safe_resp = model_resp.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        exp_html = (
            '<div class="explanation-hdr">DeepSeek V3 self-explanation:</div>'
            f'<div class="explanation">{safe_resp}</div>'
        )

    # Agree label
    if is_doubt:
        agree_lbl = "Doubt is justified &mdash; item belongs to no specific CMA row"
    else:
        agree_lbl = f"AI is correct &mdash; &ldquo;{pn}&rdquo; is the right classification"

    return (
        f'<div class="item-card" id="item-{idx}">'
        f'<div class="item-hdr">'
        f'<div class="item-badge">#{idx+1}</div>'
        f'<div class="item-text">{rt}</div>'
        f'</div>'
        f'<div class="item-meta">'
        f'<div class="meta-item">Section: <span>{sec}</span></div>'
        f'<div class="meta-item">Amount: <span>{amt_str}</span></div>'
        f'<div class="meta-item">Routed to: <span>{routed}</span></div>'
        f'<div class="meta-item">Correct row in options: <span>{"Yes" if in_opts else "No"}</span></div>'
        f'</div>'
        f'{tag}'
        f'<div class="rows-grid">'
        f'<div class="row-box correct">'
        f'<div class="row-lbl correct">Ground Truth</div>'
        f'<div class="row-name">{cf or cn}</div>'
        f'<div class="row-num">GT Row {cr}</div>'
        f'</div>'
        f'{pred_box}'
        f'</div>'
        f'{exp_html}'
        f'<div class="ca-review">'
        f'<div class="ca-review-lbl">&#x2713; CA Review</div>'
        f'<ul class="opt-list">'
        f'<li class="opt-item" onclick="selectOpt(this,{idx},\'agree\')">'
        f'<input type="radio" name="rev-{idx}" id="r{idx}-agree">'
        f'<label for="r{idx}-agree">{agree_lbl}</label>'
        f'</li>'
        f'<li class="opt-item" onclick="selectOpt(this,{idx},\'gt_correct\')">'
        f'<input type="radio" name="rev-{idx}" id="r{idx}-gtc">'
        f'<label for="r{idx}-gtc">GT is correct &mdash; AI should have classified as: <strong>{cf}</strong></label>'
        f'</li>'
        f'<li class="correct-input-row">'
        f'<input type="radio" name="rev-{idx}" id="r{idx}-other" onclick="selectOptOther({idx})">'
        f'<label for="r{idx}-other" style="font-size:13px;cursor:pointer;flex-shrink:0">Different row:</label>'
        f'<input type="number" class="corr-row-input" id="row-{idx}" placeholder="Row #"'
        f' onfocus="selectOptOther({idx})" onchange="updateOther({idx})">'
        f'<input type="text" class="corr-field-input" id="field-{idx}"'
        f' placeholder="Field name (e.g. Wages and Salaries)"'
        f' onfocus="selectOptOther({idx})" oninput="updateOther({idx})">'
        f'</li>'
        f'<li class="opt-item" onclick="selectOpt(this,{idx},\'skip\')">'
        f'<input type="radio" name="rev-{idx}" id="r{idx}-skip">'
        f'<label for="r{idx}-skip">Skip &mdash; not sure</label>'
        f'</li>'
        f'</ul>'
        f'</div>'
        f'</div>'
    )


rb_html = "".join(item_card_html(item) for item in routing_bug_items)
me_html = "".join(item_card_html(item) for item in model_error_items)

# ── CSS (plain string — no f-string, avoids {{ }} escaping) ──────────────────
CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f0f4f8;color:#2d3748;font-size:14px;line-height:1.6}
.container{max-width:960px;margin:0 auto;padding:16px}
.page-header{background:#1a365d;color:#fff;padding:22px 26px;border-radius:10px;margin-bottom:14px}
.page-header h1{font-size:21px;font-weight:700;margin-bottom:4px}
.page-header .sub{opacity:.75;font-size:13px}
/* Cards */
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:14px}
.card{background:#fff;border-radius:8px;padding:14px 16px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.card .lbl{font-size:12px;color:#718096;font-weight:500;margin-bottom:2px}
.card .val{font-size:24px;font-weight:700;color:#1a365d}
.card .sub{font-size:11px;color:#a0aec0;margin-top:1px}
.card.green .val{color:#27ae60}.card.red .val{color:#e53e3e}.card.orange .val{color:#e67e22}
/* Compare table */
.compare{background:#fff;border-radius:8px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,.08);margin-bottom:14px}
.compare h2{font-size:15px;font-weight:700;color:#1a365d;margin-bottom:12px;border-bottom:1px solid #e2e8f0;padding-bottom:8px}
.cg{display:grid;gap:1px;background:#e2e8f0;border-radius:6px;overflow:hidden}
.cg3{grid-template-columns:1fr 1fr 1fr}
.cg4{grid-template-columns:2fr 1fr 2fr}
.cg-cell{background:#fff;padding:10px 14px;text-align:center}
.cg-cell.hdr{background:#f7fafc;font-weight:600;font-size:12px;color:#4a5568;text-transform:uppercase;letter-spacing:.05em}
.cg-cell.left{text-align:left}
.cg-cell .big{font-size:20px;font-weight:700;margin-bottom:2px}
.cg-cell .label{font-size:11px;color:#718096}
.badge-delta{display:inline-block;padding:2px 10px;border-radius:99px;font-size:13px;font-weight:700;margin-left:6px}
.badge-pos{background:#c6f6d5;color:#276749}.badge-neg{background:#fed7d7;color:#9b2c2c}
/* Progress */
.progress-box{background:#fff;padding:14px 16px;border-radius:8px;margin-bottom:14px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.progress-lbl{display:flex;justify-content:space-between;font-size:13px;color:#4a5568;margin-bottom:6px;font-weight:500}
.pbar{background:#e2e8f0;border-radius:99px;height:10px;overflow:hidden}
.pbar-fill{background:#27ae60;height:100%;border-radius:99px;transition:width .3s}
/* Buttons */
.top-actions{display:flex;gap:10px;align-items:center;margin-bottom:14px;flex-wrap:wrap}
.btn{padding:9px 18px;border-radius:6px;border:none;cursor:pointer;font-size:13px;font-weight:600;transition:all .15s}
.btn-navy{background:#1a365d;color:#fff}.btn-navy:hover{background:#2c5282}
.btn-orange{background:#e67e22;color:#fff}.btn-orange:hover{background:#d35400}
.btn-green{background:#27ae60;color:#fff}.btn-green:hover{background:#229954}
.btn-outline{background:#fff;color:#4a5568;border:1px solid #cbd5e0}.btn-outline:hover{border-color:#1a365d;color:#1a365d}
/* Sections */
.sec-block{margin-bottom:14px}
.sec-hdr{background:#1a365d;color:#fff;padding:12px 18px;border-radius:8px 8px 0 0;display:flex;align-items:center;gap:10px;cursor:pointer;user-select:none}
.sec-hdr.closed{border-radius:8px;margin-bottom:0}
.sec-letter{width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;flex-shrink:0;background:#e67e22;color:#fff}
.sec-letter.blue{background:#3182ce}
.sec-title-text{font-weight:600;flex:1;font-size:15px}
.sec-count{font-size:12px;opacity:.8}
.chevron{transition:transform .2s;font-size:12px}
.chevron.rot{transform:rotate(180deg)}
.sec-body{background:#fff;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;overflow:hidden}
.sec-body.hidden{display:none}
/* Item cards */
.item-card{padding:18px;border-bottom:1px solid #f0f4f8;border-left:4px solid transparent;transition:border-color .2s}
.item-card:last-child{border-bottom:none}
.item-card.reviewed{border-left-color:#27ae60}
.item-hdr{display:flex;align-items:flex-start;gap:10px;margin-bottom:10px}
.item-badge{background:#1a365d;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;flex-shrink:0;margin-top:3px}
.item-text{font-size:15px;font-weight:600;color:#1a365d;flex:1}
.item-meta{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:10px;font-size:12px;color:#718096}
.meta-item span{font-weight:600;color:#2d3748}
.rows-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px}
.row-box{border:1px solid #e2e8f0;border-radius:6px;padding:10px 12px}
.row-box.correct{border-color:#9ae6b4;background:#f0fff4}
.row-box.predicted{border-color:#fbd38d;background:#fffbf0}
.row-box.doubt{border-color:#fc8181;background:#fff5f5}
.row-lbl{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px}
.row-lbl.correct{color:#27ae60}.row-lbl.predicted{color:#e67e22}.row-lbl.doubt{color:#e53e3e}
.row-name{font-size:14px;font-weight:600;color:#1a365d}
.row-num{font-size:11px;color:#718096;margin-top:2px}
.tag{display:inline-block;padding:3px 10px;border-radius:4px;font-size:12px;font-weight:600;margin-bottom:10px}
.tag-routing{background:#fed7d7;color:#9b2c2c}
.tag-model{background:#bee3f8;color:#2b6cb0}
.tag-neutral{background:#e2e8f0;color:#4a5568}
.explanation-hdr{font-size:11px;font-weight:700;color:#2b6cb0;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px}
.explanation{background:#f7fafc;border-left:3px solid #4299e1;padding:10px 14px;border-radius:4px;margin-bottom:12px;font-size:13px;color:#2d3748;white-space:pre-wrap;word-break:break-word}
/* CA Review */
.ca-review{background:#f7fafc;border:1px solid #e2e8f0;border-radius:6px;padding:12px 14px}
.ca-review-lbl{font-size:12px;font-weight:700;color:#4a5568;margin-bottom:8px;text-transform:uppercase;letter-spacing:.05em}
.opt-list{list-style:none}
.opt-item{padding:6px 10px;border-radius:6px;margin-bottom:3px;display:flex;align-items:center;gap:8px;cursor:pointer;border:1px solid transparent;transition:background .1s}
.opt-item:hover{background:#edf2f7}
.opt-item.sel{background:#f0fff4;border-color:#9ae6b4}
.opt-item input[type=radio]{accent-color:#27ae60;cursor:pointer;flex-shrink:0}
.opt-item label{cursor:pointer;flex:1;font-size:13px}
.correct-input-row{display:flex;align-items:center;gap:8px;padding:6px 10px;flex-wrap:wrap}
.correct-input-row input[type=radio]{accent-color:#27ae60;flex-shrink:0}
.corr-row-input{padding:5px 8px;border:1px solid #cbd5e0;border-radius:4px;width:72px;font-size:13px}
.corr-field-input{padding:5px 8px;border:1px solid #cbd5e0;border-radius:4px;font-size:13px;flex:1;min-width:180px}
.corr-row-input:focus,.corr-field-input:focus{outline:none;border-color:#1a365d;box-shadow:0 0 0 2px #bee3f8}
/* Footer */
.footer{text-align:center;padding:24px;color:#718096;font-size:12px;margin-top:8px}
@media(max-width:640px){
  .rows-grid{grid-template-columns:1fr}
  .cg3,.cg4{grid-template-columns:1fr}
}
"""

# ── JavaScript (plain string — no f-string) ────────────────────────────────────
JS = r"""
const responses = {};
const totalItems = DATA.items.length;

function updateProgress() {
  const reviewed = Object.keys(responses).filter(k => responses[k].choice && responses[k].choice !== 'skip').length;
  const pct = totalItems > 0 ? (reviewed / totalItems * 100).toFixed(1) : 0;
  const fill = document.getElementById('pbar');
  const lbl  = document.getElementById('prog-lbl');
  if (fill) fill.style.width = pct + '%';
  if (lbl)  lbl.textContent  = reviewed + ' / ' + totalItems + ' reviewed';
}

function selectOpt(li, idx, choice) {
  const ul = li.closest('.opt-list');
  if (ul) ul.querySelectorAll('.opt-item').forEach(l => l.classList.remove('sel'));
  li.classList.add('sel');
  const radio = li.querySelector('input[type=radio]');
  if (radio) radio.checked = true;
  responses[idx] = { choice, row: null, field: null };
  const card = document.getElementById('item-' + idx);
  if (card) card.classList.toggle('reviewed', choice !== 'skip');
  updateProgress();
}

function selectOptOther(idx) {
  const radio = document.getElementById('r' + idx + '-other');
  if (radio) radio.checked = true;
  const ul = radio ? radio.closest('.opt-list') : null;
  if (ul) ul.querySelectorAll('.opt-item').forEach(l => l.classList.remove('sel'));
  if (!responses[idx]) responses[idx] = { choice: 'other', row: null, field: null };
  responses[idx].choice = 'other';
  updateProgress();
}

function updateOther(idx) {
  const rowEl   = document.getElementById('row-'   + idx);
  const fieldEl = document.getElementById('field-' + idx);
  responses[idx] = {
    choice: 'other',
    row:   rowEl   ? rowEl.value   : null,
    field: fieldEl ? fieldEl.value : null,
  };
  const card = document.getElementById('item-' + idx);
  if (card) card.classList.add('reviewed');
  updateProgress();
}

function toggleSec(secId, chevId) {
  const sec  = document.getElementById(secId);
  const chev = document.getElementById(chevId);
  if (!sec) return;
  sec.classList.toggle('hidden');
  if (chev) chev.classList.toggle('rot', !sec.classList.contains('hidden'));
}

function expandAll() {
  document.querySelectorAll('.sec-body').forEach(s => s.classList.remove('hidden'));
  document.querySelectorAll('.chevron').forEach(c => c.classList.add('rot'));
}

function collapseAll() {
  document.querySelectorAll('.sec-body').forEach(s => s.classList.add('hidden'));
  document.querySelectorAll('.chevron').forEach(c => c.classList.remove('rot'));
}

function exportJSON() {
  const out = {
    company:          DATA.company,
    industry:         DATA.industry,
    date:             DATA.date,
    accuracy_round2:  DATA.round2.accuracy_pct,
    accuracy_round1:  DATA.round1.accuracy_pct,
    delta_pp:         DATA.delta,
    exported_at:      new Date().toISOString(),
    responses: DATA.items.map(item => {
      const r = responses[item.index] || { choice: null };
      return {
        index:               item.index,
        raw_text:            item.raw_text,
        section:             item.section,
        error_type:          item.error_type,
        is_doubt:            item.is_doubt,
        correct_cma_field:   item.correct_cma_field,
        predicted_cma_field: item.predicted_cma_field,
        correct_cma_row_gt:  item.correct_cma_row_gt,
        ca_choice:           r.choice,
        ca_correct_row:      r.row   || null,
        ca_correct_field:    r.field || null,
      };
    }),
  };
  const blob = new Blob([JSON.stringify(out, null, 2)], { type: 'application/json' });
  const a    = document.createElement('a');
  a.href     = URL.createObjectURL(blob);
  a.download = 'Kurunji_Retail_round2_ca_responses.json';
  a.click();
}

updateProgress();
"""

# ── Assemble HTML (split to avoid f-string + JSON escaping issues) ─────────────
delta_badge_cls = "badge-pos" if delta >= 0 else "badge-neg"
rb_empty = '<div style="padding:20px;color:#718096;text-align:center;font-style:italic">No routing bugs found in this run.</div>'
me_empty = '<div style="padding:20px;color:#718096;text-align:center;font-style:italic">No model errors found in this run.</div>'

html_head = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{COMPANY} — Round 2 Classification Review</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">

<div class="page-header">
  <h1>{COMPANY} &mdash; Round 2 Classification Review</h1>
  <div class="sub">Industry: {INDUSTRY.title()} &nbsp;&middot;&nbsp; Date: {today} &nbsp;&middot;&nbsp; {len(unique_wrong)} items need CA verification</div>
</div>

<div class="cards">
  <div class="card"><div class="lbl">Total Items</div><div class="val">{total}</div><div class="sub">GT entries</div></div>
  <div class="card green"><div class="lbl">Correct</div><div class="val">{correct}</div><div class="sub">{acc_pct:.1f}%</div></div>
  <div class="card red"><div class="lbl">Wrong</div><div class="val">{wrong_n}</div><div class="sub">misclassified</div></div>
  <div class="card orange"><div class="lbl">Doubts</div><div class="val">{doubts}</div><div class="sub">low confidence</div></div>
  <div class="card"><div class="lbl">Unique Wrong</div><div class="val">{len(unique_wrong)}</div><div class="sub">deduplicated</div></div>
</div>

<div class="compare">
  <h2>Round 1 &rarr; Round 2 Comparison</h2>
  <div class="cg cg3">
    <div class="cg-cell hdr">Metric</div>
    <div class="cg-cell hdr">Round 1 (Post-CA Rules)</div>
    <div class="cg-cell hdr">Round 2 (Current)</div>
    <div class="cg-cell left">Accuracy</div>
    <div class="cg-cell"><div class="big">{round1["accuracy_pct"]:.1f}%</div></div>
    <div class="cg-cell"><div class="big">{acc_pct:.1f}%</div><span class="badge-delta {delta_badge_cls}">{delta_str}pp</span></div>
    <div class="cg-cell left">Correct</div>
    <div class="cg-cell"><div class="big">{round1["correct"]}</div><div class="label">of {round1["total_items"]}</div></div>
    <div class="cg-cell"><div class="big">{correct}</div><div class="label">of {total}</div></div>
    <div class="cg-cell left">Wrong</div>
    <div class="cg-cell"><div class="big">{round1["wrong"]}</div></div>
    <div class="cg-cell"><div class="big">{wrong_n}</div></div>
    <div class="cg-cell left">Doubts</div>
    <div class="cg-cell"><div class="big">{round1["doubts"]}</div></div>
    <div class="cg-cell"><div class="big">{doubts}</div></div>
  </div>
</div>

<div class="compare">
  <h2>Error Analysis &mdash; {len(unique_wrong)} unique wrong items</h2>
  <div class="cg cg4">
    <div class="cg-cell hdr left">Error Type</div>
    <div class="cg-cell hdr">Count</div>
    <div class="cg-cell hdr left">Meaning</div>
    <div class="cg-cell left"><span class="tag tag-routing">Routing Bug</span></div>
    <div class="cg-cell"><div class="big">{routing_bugs}</div></div>
    <div class="cg-cell left" style="font-size:13px;color:#4a5568">Correct CMA row was NOT in the options presented to AI &mdash; fix requires a routing/keyword rule change</div>
    <div class="cg-cell left"><span class="tag tag-model">Model Error</span></div>
    <div class="cg-cell"><div class="big">{model_errors}</div></div>
    <div class="cg-cell left" style="font-size:13px;color:#4a5568">Correct CMA row WAS available, but AI chose the wrong one &mdash; fix requires prompt/rule tuning</div>
    <div class="cg-cell left"><span class="tag tag-neutral">GT Offset Bug</span></div>
    <div class="cg-cell"><div class="big">{len(offset_bugs)}</div></div>
    <div class="cg-cell left" style="font-size:13px;color:#4a5568">Same field name, different row number &mdash; ground truth row numbering offset (not a real AI error)</div>
  </div>
</div>

<div class="progress-box">
  <div class="progress-lbl">
    <span>CA Review Progress</span>
    <span id="prog-lbl">0 / {len(unique_wrong)} reviewed</span>
  </div>
  <div class="pbar"><div class="pbar-fill" id="pbar" style="width:0%"></div></div>
</div>

<div class="top-actions">
  <button class="btn btn-green" onclick="exportJSON()">&#8659; Export CA Responses (JSON)</button>
  <button class="btn btn-navy" onclick="expandAll()">Expand All</button>
  <button class="btn btn-outline" onclick="collapseAll()">Collapse All</button>
  <span style="font-size:12px;color:#718096">Review each item and select your assessment, then export.</span>
</div>

<div class="sec-block">
  <div class="sec-hdr" onclick="toggleSec('sec-a','chev-a')">
    <div class="sec-letter">A</div>
    <div class="sec-title-text">Routing Bugs &mdash; correct row was NOT in AI&rsquo;s options ({routing_bugs} items)</div>
    <span class="chevron rot" id="chev-a">&#9660;</span>
  </div>
  <div class="sec-body" id="sec-a">
"""

html_mid = f"""  </div>
</div>

<div class="sec-block">
  <div class="sec-hdr" onclick="toggleSec('sec-b','chev-b')">
    <div class="sec-letter blue">B</div>
    <div class="sec-title-text">Model Errors &mdash; correct row was available, AI chose wrong ({model_errors} items)</div>
    <span class="chevron rot" id="chev-b">&#9660;</span>
  </div>
  <div class="sec-body" id="sec-b">
"""

html_end = f"""  </div>
</div>

<div class="top-actions" style="margin-top:20px">
  <button class="btn btn-green" onclick="exportJSON()">&#8659; Export CA Responses (JSON)</button>
</div>

<div class="footer">
  {COMPANY} &mdash; Round 2 Classification Review &mdash; Generated {today}<br>
  {len(unique_wrong)} wrong items for CA review &middot; {routing_bugs} routing bugs &middot; {model_errors} model errors
</div>

</div>
"""

# Script block: use concatenation so data_json is NOT inside an f-string
html_script = (
    '<script>\n'
    'const DATA = '
    + data_json
    + ';\n'
    + JS
    + '\n</script>\n</body>\n</html>'
)

html = (
    html_head
    + (rb_html if rb_html else rb_empty)
    + html_mid
    + (me_html if me_html else me_empty)
    + html_end
    + html_script
)

html_path = HTML_DIR / f"{COMPANY}_review.html"
with open(html_path, "w", encoding="utf-8") as fh:
    fh.write(html)

print(f"HTML report saved → {html_path} ({len(html):,} chars)")


# ═════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═════════════════════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print(f"  ALL DONE — {COMPANY} ROUND 2")
print(f"{'='*70}")
print(f"  Accuracy:     {acc_pct:.2f}%  (Round 1: {round1['accuracy_pct']:.2f}%,  delta: {delta_str}pp)")
print(f"  Total:        {total}   Correct: {correct}   Wrong: {wrong_n}   Doubts: {doubts}")
print(f"  Unique wrong: {len(unique_wrong)}   Offset bugs: {len(offset_bugs)}")
print(f"  Routing bugs: {routing_bugs}   Model errors: {model_errors}")
print(f"")
print(f"  JSON outputs: {OUTPUT_DIR}/")
print(f"    - {COMPANY}_accuracy_summary.json")
print(f"    - {COMPANY}_wrong_entries.json")
print(f"    - {COMPANY}_interview.json")
print(f"  HTML report:  {html_path}")
print(f"{'='*70}")
