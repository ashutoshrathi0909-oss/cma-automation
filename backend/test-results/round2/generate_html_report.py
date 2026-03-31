#!/usr/bin/env python3
"""
Generate self-contained HTML review report for SR_Papers Round 2.

Reads SR_Papers_interview.json and SR_Papers_wrong_entries.json,
generates DOCS/test-results/round2/SR_Papers_review.html.

Run:
    docker compose exec -T worker bash -c "cd /app && python test-results/round2/generate_html_report.py"
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "/app")

# ─── Paths ────────────────────────────────────────────────────────────────────
INPUT_DIR = Path("/app/test-results/round2")
OUTPUT_PATH = Path("/app/DOCS/test-results/round2/SR_Papers_review.html")
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# ─── Load data ────────────────────────────────────────────────────────────────
with open(INPUT_DIR / "SR_Papers_interview.json", encoding="utf-8") as f:
    data = json.load(f)

meta = data["meta"]
acc = data["accuracy_summary"]
r1 = data["round1_baseline"]
analysis = data["analysis"]
interviews = data["interviews"]

print(f"Loaded {len(interviews)} interviews")
print(f"Round 1: {r1['accuracy_pct']}%  Round 2: {acc['accuracy_pct']}%")

# ─── Split by error type ──────────────────────────────────────────────────────
routing_bugs = [iv for iv in interviews if iv["error_type"] == "routing_bug"]
model_errors = [iv for iv in interviews if iv["error_type"] == "model_error"]
doubts_list  = [iv for iv in interviews if iv.get("is_doubt")]

print(f"Routing bugs: {len(routing_bugs)}  Model errors: {len(model_errors)}  Doubts: {len(doubts_list)}")

# ─── Helper: format amount ────────────────────────────────────────────────────
def fmt_amount(amount) -> str:
    if amount is None:
        return "—"
    try:
        v = float(amount)
        if v < 0:
            return f"(₹{abs(v):,.0f})"
        return f"₹{v:,.0f}"
    except Exception:
        return str(amount)


def html_escape(s: str) -> str:
    return (str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;"))


def section_label(s: str) -> str:
    """Convert section text to readable label."""
    if not s:
        return "—"
    s = s.strip()
    # Capitalize and truncate
    return s[:60] if len(s) <= 60 else s[:57] + "…"


def method_badge(method: str) -> str:
    if "scoped_v3" in method:
        return '<span class="badge badge-blue">scoped_v3</span>'
    if "doubt" in method:
        return '<span class="badge badge-yellow">doubt</span>'
    return f'<span class="badge badge-gray">{html_escape(method)}</span>'


def error_type_badge(et: str, is_doubt: bool) -> str:
    if is_doubt:
        return '<span class="badge badge-yellow">DOUBT</span>'
    if et == "routing_bug":
        return '<span class="badge badge-red">ROUTING BUG</span>'
    return '<span class="badge badge-orange">MODEL ERROR</span>'


# ─── Build item cards ─────────────────────────────────────────────────────────
def build_item_card(iv: dict, card_num: int) -> str:
    idx = iv["index"]
    raw_text = iv["raw_text"]
    section = iv.get("section", "")
    amount = iv.get("amount")
    correct_row = iv.get("correct_row")
    correct_row_gt = iv.get("correct_row_gt")
    correct_name = iv.get("correct_name", "—")
    predicted_row = iv.get("predicted_row")
    predicted_name = iv.get("predicted_name", "—")
    error_type = iv.get("error_type", "model_error")
    is_doubt = iv.get("is_doubt", False)
    conf = iv.get("confidence", 0)
    method = iv.get("classification_method", "")
    routed_to = iv.get("routed_to", [])
    model_resp_raw = iv.get("model_response", "")
    model_resp = model_resp_raw

    # Correct field from GT
    correct_field_gt = ""
    if "correct_cma_field" in iv:
        correct_field_gt = iv["correct_cma_field"]

    routing_path = " + ".join(routed_to) if routed_to else "—"

    # Pre-compute model response HTML (can't use backslash in f-string expressions)
    model_resp_html = html_escape(model_resp).replace("&#10;", "<br>").replace("\n", "<br>")

    correct_in_opts = iv.get("correct_in_options", False)
    availability = (
        '<span class="avail-yes">✓ In options</span>'
        if correct_in_opts else
        '<span class="avail-no">✗ Not in options</span>'
    )

    # Amount display
    amt_str = fmt_amount(amount)

    # Confidence bar
    conf_pct = int(conf * 100)
    conf_color = "#27ae60" if conf >= 0.85 else "#e67e22" if conf >= 0.6 else "#e74c3c"

    card_html = f"""
    <div class="item-card" id="card-{idx}" data-idx="{idx}" data-reviewed="0">
      <div class="item-header">
        <div class="item-num">{card_num}</div>
        <div class="item-title">
          <span class="item-text">{html_escape(raw_text)}</span>
          {error_type_badge(error_type, is_doubt)}
        </div>
        <div class="item-meta">
          <span class="meta-pill amt">{html_escape(amt_str)}</span>
          <span class="meta-pill sec" title="{html_escape(section)}">{html_escape(section_label(section))}</span>
        </div>
      </div>

      <div class="classification-grid">
        <div class="cls-box correct-box">
          <div class="cls-label">✓ Correct (CA-verified)</div>
          <div class="cls-row">R{correct_row_gt} → R{correct_row} (offset)</div>
          <div class="cls-name">{html_escape(correct_name)}</div>
        </div>
        <div class="cls-arrow">→</div>
        <div class="cls-box predicted-box">
          <div class="cls-label">AI Predicted</div>
          <div class="cls-row">R{predicted_row if predicted_row else '—'}</div>
          <div class="cls-name">{html_escape(predicted_name)}</div>
        </div>
      </div>

      <div class="detail-row">
        <span class="detail-label">Method:</span> {method_badge(method)}
        <span class="detail-sep">|</span>
        <span class="detail-label">Routed to:</span>
        <span class="detail-val">{html_escape(routing_path)}</span>
        <span class="detail-sep">|</span>
        <span class="detail-label">Correct row available:</span>
        {availability}
        <span class="detail-sep">|</span>
        <span class="detail-label">Confidence:</span>
        <span class="conf-bar-wrap">
          <span class="conf-bar" style="width:{conf_pct}%;background:{conf_color}"></span>
          <span class="conf-val">{conf_pct}%</span>
        </span>
      </div>

      <div class="ai-response-block">
        <div class="ai-response-hdr" onclick="toggleResponse(this)">
          <span>▶ AI Interview Response</span>
          <span class="ai-resp-hint">click to expand</span>
        </div>
        <div class="ai-response-body hidden">{model_resp_html}</div>
      </div>

      <div class="ca-review-block">
        <div class="ca-review-title">CA Review</div>
        <div class="ca-options">
          <label class="ca-opt">
            <input type="radio" name="review_{idx}" value="agree" onchange="onReview({idx}, 'agree')">
            <span class="ca-opt-text">Agree with AI prediction (R{predicted_row if predicted_row else '—'})</span>
          </label>
          <label class="ca-opt">
            <input type="radio" name="review_{idx}" value="correct" onchange="onReview({idx}, 'correct')">
            <span class="ca-opt-text">GT is correct (R{correct_row})</span>
          </label>
          <label class="ca-opt">
            <input type="radio" name="review_{idx}" value="other" onchange="onReview({idx}, 'other')">
            <span class="ca-opt-text">Neither — correct row is:
              <input type="number" id="other_row_{idx}" class="row-input" placeholder="row#"
                     min="1" max="400" oninput="onOtherRowChange({idx})">
              <input type="text" id="other_name_{idx}" class="name-input" placeholder="field name (optional)">
            </span>
          </label>
        </div>
        <div class="ca-note-row">
          <textarea id="note_{idx}" class="ca-note" placeholder="Optional note…" rows="1"
                    oninput="onNoteChange({idx})"></textarea>
        </div>
      </div>
    </div>"""
    return card_html


# ─── Build sections ────────────────────────────────────────────────────────────
routing_cards_html = ""
for n, iv in enumerate(routing_bugs, 1):
    routing_cards_html += build_item_card(iv, n)

model_error_cards_html = ""
for n, iv in enumerate(model_errors, len(routing_bugs) + 1):
    model_error_cards_html += build_item_card(iv, n)

doubt_cards_html = ""
for n, iv in enumerate(doubts_list, len(routing_bugs) + len(model_errors) + 1):
    if iv not in routing_bugs and iv not in model_errors:  # avoid duplicates
        doubt_cards_html += build_item_card(iv, n)

total_cards = len(interviews)
delta_str = f"+{acc['delta_pp']:.2f}" if acc["delta_pp"] >= 0 else f"{acc['delta_pp']:.2f}"
delta_color = "#27ae60" if acc["delta_pp"] > 0 else "#e74c3c" if acc["delta_pp"] < 0 else "#718096"

# Pre-compute doubt section HTML (avoids backslash in nested f-string)
if doubts_list:
    doubt_section_html = (
        '\n  <div class="sec-block" id="sec-doubt">'
        '\n    <div class="sec-hdr" onclick="toggleSection(\'sec-doubt\')">'
        '\n      <div class="sec-letter green">D</div>'
        '\n      <div class="sec-title">Doubts \u2014 Low Confidence or Classification Failure</div>'
        f'\n      <div class="sec-count">{len(doubts_list)} items</div>'
        '\n      <div class="chevron" id="chev-sec-doubt">\u25bc</div>'
        '\n    </div>'
        '\n    <div class="sec-body hidden" id="body-sec-doubt">'
        + doubt_cards_html +
        '\n    </div>'
        '\n  </div>'
    )
else:
    doubt_section_html = ""

# Embed the interviews data as JSON for export
interviews_json_str = json.dumps(interviews, ensure_ascii=False)

# ─── Full HTML ────────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SR Papers — Round 2 Accuracy Review</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f0f4f8;color:#2d3748;font-size:14px;line-height:1.6}}
.container{{max-width:980px;margin:0 auto;padding:16px}}

/* ── Page header ── */
.page-header{{background:#1a365d;color:#fff;padding:20px 24px;border-radius:10px;margin-bottom:14px}}
.page-header h1{{font-size:22px;font-weight:700;margin-bottom:4px}}
.page-header .sub{{opacity:.8;font-size:13px}}
.header-badges{{display:flex;gap:10px;margin-top:12px;flex-wrap:wrap}}
.hbadge{{background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.3);border-radius:6px;padding:6px 12px;font-size:12px;font-weight:600}}
.hbadge.green{{background:rgba(39,174,96,0.3);border-color:rgba(39,174,96,0.5)}}
.hbadge.orange{{background:rgba(230,126,34,0.3);border-color:rgba(230,126,34,0.5)}}
.hbadge.red{{background:rgba(231,76,60,0.25);border-color:rgba(231,76,60,0.4)}}

/* ── Progress ── */
.progress-box{{background:#fff;padding:14px 18px;border-radius:8px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.progress-lbl{{font-size:13px;color:#4a5568;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center}}
.progress-lbl strong{{color:#1a365d;font-size:15px}}
.pbar{{background:#e2e8f0;border-radius:99px;height:12px;overflow:hidden}}
.pbar-fill{{background:#27ae60;height:100%;border-radius:99px;transition:width .3s}}

/* ── Summary cards ── */
.stat-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px;margin-bottom:14px}}
.stat-card{{background:#fff;border-radius:8px;padding:14px 16px;box-shadow:0 1px 3px rgba(0,0,0,.08);text-align:center}}
.stat-val{{font-size:26px;font-weight:700;color:#1a365d;line-height:1.2}}
.stat-val.green{{color:#27ae60}}
.stat-val.orange{{color:#e67e22}}
.stat-val.red{{color:#e74c3c}}
.stat-val.blue{{color:#3182ce}}
.stat-lbl{{font-size:11px;color:#718096;text-transform:uppercase;letter-spacing:.05em;margin-top:3px}}

/* ── Delta card ── */
.delta-row{{background:#fff;border-radius:8px;padding:14px 20px;margin-bottom:14px;box-shadow:0 1px 3px rgba(0,0,0,.08);display:flex;align-items:center;gap:20px;flex-wrap:wrap}}
.delta-item{{display:flex;flex-direction:column;align-items:center}}
.delta-item .val{{font-size:22px;font-weight:700}}
.delta-item .lbl{{font-size:11px;color:#718096;text-transform:uppercase}}
.delta-arrow{{font-size:22px;color:#a0aec0}}
.delta-change{{font-size:24px;font-weight:700}}

/* ── Top actions ── */
.top-actions{{display:flex;gap:10px;align-items:center;margin-bottom:14px;flex-wrap:wrap}}
.btn{{padding:9px 18px;border-radius:6px;border:none;cursor:pointer;font-size:13px;font-weight:500;transition:all .15s;white-space:nowrap}}
.btn-navy{{background:#1a365d;color:#fff}}.btn-navy:hover{{background:#2c5282}}
.btn-orange{{background:#e67e22;color:#fff}}.btn-orange:hover{{background:#d35400}}
.btn-green{{background:#27ae60;color:#fff}}.btn-green:hover{{background:#229954}}
.btn-outline{{background:#fff;color:#4a5568;border:1px solid #cbd5e0}}.btn-outline:hover{{border-color:#1a365d;color:#1a365d}}

/* ── Section block ── */
.sec-block{{margin-bottom:16px}}
.sec-hdr{{background:#1a365d;color:#fff;padding:12px 18px;border-radius:8px 8px 0 0;display:flex;align-items:center;gap:12px;user-select:none;cursor:pointer}}
.sec-hdr.closed{{border-radius:8px;margin-bottom:4px}}
.sec-letter{{background:#e67e22;color:#fff;width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;flex-shrink:0}}
.sec-letter.blue{{background:#3182ce}}
.sec-letter.green{{background:#27ae60}}
.sec-title{{font-weight:600;flex:1;font-size:15px}}
.sec-count{{font-size:12px;opacity:.8;white-space:nowrap}}
.chevron{{transition:transform .2s;font-size:12px;opacity:.8}}
.chevron.rot{{transform:rotate(180deg)}}
.sec-body{{background:#fff;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;overflow:hidden}}
.sec-body.hidden{{display:none}}

/* ── Item card ── */
.item-card{{padding:18px;border-bottom:1px solid #f0f4f8;transition:background .15s}}
.item-card:last-child{{border-bottom:none}}
.item-card.reviewed{{background:#f0fff4}}
.item-header{{display:flex;align-items:flex-start;gap:10px;margin-bottom:12px;flex-wrap:wrap}}
.item-num{{background:#1a365d;color:#fff;width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;flex-shrink:0;margin-top:2px}}
.item-title{{flex:1;min-width:200px}}
.item-text{{font-size:15px;font-weight:600;color:#1a365d;display:block;margin-bottom:4px}}
.item-meta{{display:flex;gap:6px;flex-wrap:wrap;align-items:center}}
.meta-pill{{background:#edf2f7;color:#4a5568;padding:3px 9px;border-radius:99px;font-size:11px;white-space:nowrap;max-width:280px;overflow:hidden;text-overflow:ellipsis}}
.meta-pill.amt{{background:#ebf8ff;color:#2b6cb0;font-weight:600}}

/* ── Classification grid ── */
.classification-grid{{display:flex;align-items:center;gap:12px;margin:12px 0;flex-wrap:wrap}}
.cls-box{{flex:1;min-width:140px;border-radius:6px;padding:10px 14px;border:1px solid #e2e8f0}}
.correct-box{{background:#f0fff4;border-color:#9ae6b4}}
.predicted-box{{background:#fff5f5;border-color:#fed7d7}}
.cls-label{{font-size:10px;text-transform:uppercase;letter-spacing:.05em;font-weight:700;color:#718096;margin-bottom:3px}}
.correct-box .cls-label{{color:#276749}}
.predicted-box .cls-label{{color:#9b2c2c}}
.cls-row{{font-size:11px;color:#a0aec0;margin-bottom:2px}}
.cls-name{{font-size:14px;font-weight:600;color:#2d3748}}
.cls-arrow{{font-size:24px;color:#a0aec0;flex-shrink:0}}

/* ── Detail row ── */
.detail-row{{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:12px;color:#4a5568;margin-bottom:12px}}
.detail-label{{font-weight:600;color:#4a5568}}
.detail-val{{color:#2d3748}}
.detail-sep{{color:#cbd5e0}}
.avail-yes{{color:#276749;font-weight:600}}
.avail-no{{color:#c53030;font-weight:600}}
.conf-bar-wrap{{display:inline-flex;align-items:center;gap:6px}}
.conf-bar-track{{width:60px;height:8px;background:#e2e8f0;border-radius:99px;overflow:hidden;display:inline-block}}
.conf-bar{{height:100%;border-radius:99px;display:block}}
.conf-val{{font-size:11px;font-weight:600}}

/* ── Badge ── */
.badge{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;vertical-align:middle}}
.badge-red{{background:#fff5f5;color:#c53030;border:1px solid #fed7d7}}
.badge-orange{{background:#fffaf0;color:#c05621;border:1px solid #fbd38d}}
.badge-yellow{{background:#fffff0;color:#975a16;border:1px solid #faf089}}
.badge-blue{{background:#ebf8ff;color:#2b6cb0;border:1px solid #bee3f8}}
.badge-gray{{background:#f7fafc;color:#718096;border:1px solid #e2e8f0}}

/* ── AI Response ── */
.ai-response-block{{background:#f7fafc;border-radius:6px;margin-bottom:12px;overflow:hidden;border:1px solid #e2e8f0}}
.ai-response-hdr{{padding:8px 14px;cursor:pointer;display:flex;align-items:center;justify-content:space-between;font-size:12px;font-weight:600;color:#4a5568;user-select:none}}
.ai-response-hdr:hover{{background:#edf2f7}}
.ai-resp-hint{{font-weight:400;color:#a0aec0;font-size:11px}}
.ai-response-body{{padding:12px 14px;font-size:12px;color:#2d3748;line-height:1.7;white-space:pre-wrap;border-top:1px solid #e2e8f0}}
.ai-response-body.hidden{{display:none}}

/* ── CA Review ── */
.ca-review-block{{background:#fffbf5;border:1px solid #fbd38d;border-radius:6px;padding:12px 14px}}
.ca-review-title{{font-size:12px;font-weight:700;color:#c05621;text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px}}
.ca-options{{display:flex;flex-direction:column;gap:6px;margin-bottom:8px}}
.ca-opt{{display:flex;align-items:flex-start;gap:8px;cursor:pointer;padding:5px 8px;border-radius:4px;border:1px solid transparent}}
.ca-opt:hover{{background:#fef3cd;border-color:#fbd38d}}
.ca-opt input[type=radio]{{margin-top:2px;accent-color:#e67e22;flex-shrink:0}}
.ca-opt-text{{font-size:13px;color:#2d3748;display:flex;align-items:center;gap:8px;flex-wrap:wrap}}
.row-input{{width:70px;padding:3px 8px;border:1px solid #cbd5e0;border-radius:4px;font-size:13px}}
.name-input{{padding:3px 8px;border:1px solid #cbd5e0;border-radius:4px;font-size:13px;width:200px}}
.row-input:focus,.name-input:focus{{outline:none;border-color:#e67e22}}
.ca-note-row{{margin-top:6px}}
.ca-note{{width:100%;padding:6px 10px;border:1px solid #cbd5e0;border-radius:4px;font-size:12px;resize:vertical;font-family:inherit}}
.ca-note:focus{{outline:none;border-color:#e67e22}}

/* ── Filters ── */
.filter-bar{{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:12px}}
.filter-btn{{padding:5px 12px;border-radius:99px;border:1px solid #cbd5e0;background:#fff;cursor:pointer;font-size:12px;font-weight:500;color:#4a5568;transition:all .15s}}
.filter-btn:hover{{border-color:#1a365d;color:#1a365d}}
.filter-btn.active{{background:#1a365d;color:#fff;border-color:#1a365d}}
</style>
</head>
<body>
<div class="container">

  <!-- ── Page Header ── -->
  <div class="page-header">
    <h1>SR Papers — Round 2 Classification Review</h1>
    <div class="sub">Industry: Manufacturing &nbsp;|&nbsp; Date: {meta['date']} &nbsp;|&nbsp; {meta['context']}</div>
    <div class="header-badges">
      <div class="hbadge">Total Items: {acc['total_items']}</div>
      <div class="hbadge green">Correct: {acc['correct']} ({acc['accuracy_pct']:.2f}%)</div>
      <div class="hbadge orange">Wrong: {acc['wrong']}</div>
      <div class="hbadge">Doubts: {acc['doubts']}</div>
      <div class="hbadge">Tokens: {acc['tokens_used']:,}</div>
    </div>
  </div>

  <!-- ── Progress Bar ── -->
  <div class="progress-box">
    <div class="progress-lbl">
      <span>CA Review Progress</span>
      <strong id="progress-text">0 / {total_cards} reviewed</strong>
    </div>
    <div class="pbar"><div class="pbar-fill" id="pbar" style="width:0%"></div></div>
  </div>

  <!-- ── Summary Stats ── -->
  <div class="stat-grid">
    <div class="stat-card">
      <div class="stat-val">{acc['total_items']}</div>
      <div class="stat-lbl">Total Items</div>
    </div>
    <div class="stat-card">
      <div class="stat-val green">{acc['correct']}</div>
      <div class="stat-lbl">Correct</div>
    </div>
    <div class="stat-card">
      <div class="stat-val red">{acc['wrong']}</div>
      <div class="stat-lbl">Wrong</div>
    </div>
    <div class="stat-card">
      <div class="stat-val orange">{acc['doubts']}</div>
      <div class="stat-lbl">Doubts</div>
    </div>
    <div class="stat-card">
      <div class="stat-val blue">{acc['accuracy_pct']:.1f}%</div>
      <div class="stat-lbl">Accuracy R2</div>
    </div>
    <div class="stat-card">
      <div class="stat-val">{analysis['unique_wrong']}</div>
      <div class="stat-lbl">Unique Wrong</div>
    </div>
    <div class="stat-card">
      <div class="stat-val red">{analysis['routing_bugs']}</div>
      <div class="stat-lbl">Routing Bugs</div>
    </div>
    <div class="stat-card">
      <div class="stat-val orange">{analysis['model_errors']}</div>
      <div class="stat-lbl">Model Errors</div>
    </div>
  </div>

  <!-- ── Delta Comparison ── -->
  <div class="delta-row">
    <div class="delta-item">
      <span class="val">{r1['accuracy_pct']:.2f}%</span>
      <span class="lbl">Round 1</span>
    </div>
    <div class="delta-arrow">→</div>
    <div class="delta-item">
      <span class="val">{acc['accuracy_pct']:.2f}%</span>
      <span class="lbl">Round 2</span>
    </div>
    <div class="delta-arrow">=</div>
    <div class="delta-item">
      <span class="delta-change" style="color:{delta_color}">{delta_str}pp</span>
      <span class="lbl">Delta</span>
    </div>
    <div style="flex:1;min-width:200px;font-size:12px;color:#718096;border-left:1px solid #e2e8f0;padding-left:16px">
      <strong>Root cause split (50 items interviewed):</strong><br>
      Routing bugs (correct row not in options): <strong style="color:#c53030">{analysis['routing_bugs']}</strong> ({round(analysis['routing_bugs']/50*100)}%)<br>
      Model errors (correct row available, wrong pick): <strong style="color:#c05621">{analysis['model_errors']}</strong> ({round(analysis['model_errors']/50*100)}%)
    </div>
  </div>

  <!-- ── Actions ── -->
  <div class="top-actions">
    <button class="btn btn-green" onclick="exportJSON()">Export CA Responses (JSON)</button>
    <button class="btn btn-navy" onclick="expandAll()">Expand All Sections</button>
    <button class="btn btn-outline" onclick="collapseAll()">Collapse All</button>
    <button class="btn btn-outline" onclick="expandAllResponses()">Show All AI Responses</button>
    <button class="btn btn-outline" onclick="markAllAgreed()">Mark All as GT Correct</button>
  </div>

  <!-- ── Section A: Routing Bugs ── -->
  <div class="sec-block" id="sec-routing">
    <div class="sec-hdr" onclick="toggleSection('sec-routing')">
      <div class="sec-letter">R</div>
      <div class="sec-title">Routing Bugs — Correct Row Not In Options</div>
      <div class="sec-count">{len(routing_bugs)} items</div>
      <div class="chevron" id="chev-sec-routing">▼</div>
    </div>
    <div class="sec-body" id="body-sec-routing">
      <div style="background:#fff5f5;border-bottom:1px solid #fed7d7;padding:10px 16px;font-size:12px;color:#c53030">
        <strong>These items were routed to the wrong CMA section.</strong> The correct row was never shown to the AI — this is a classifier routing issue, not a model intelligence issue. Fixing the routing regex/section mapping would likely fix these.
      </div>
      {routing_cards_html}
    </div>
  </div>

  <!-- ── Section B: Model Errors ── -->
  <div class="sec-block" id="sec-model">
    <div class="sec-hdr" onclick="toggleSection('sec-model')">
      <div class="sec-letter blue">M</div>
      <div class="sec-title">Model Errors — Correct Row Was Available, Wrong Pick</div>
      <div class="sec-count">{len(model_errors)} items</div>
      <div class="chevron" id="chev-sec-model">▼</div>
    </div>
    <div class="sec-body hidden" id="body-sec-model">
      <div style="background:#fffaf0;border-bottom:1px solid #fbd38d;padding:10px 16px;font-size:12px;color:#c05621">
        <strong>The AI had the correct option but picked the wrong row.</strong> These require rule clarifications, disambiguation prompts, or training examples to fix.
      </div>
      {model_error_cards_html}
    </div>
  </div>

  {doubt_section_html}

</div><!-- /container -->

<script>
// ── Data ──────────────────────────────────────────────────────────────────────
const INTERVIEWS = {interviews_json_str};
const TOTAL_ITEMS = {total_cards};

// ── State ─────────────────────────────────────────────────────────────────────
const state = {{}};  // idx → {{ choice, otherRow, otherName, note }}

function onReview(idx, choice) {{
  if (!state[idx]) state[idx] = {{}};
  state[idx].choice = choice;
  const card = document.getElementById('card-' + idx);
  if (card) {{
    card.dataset.reviewed = '1';
    card.classList.add('reviewed');
  }}
  updateProgress();
}}

function onOtherRowChange(idx) {{
  const val = document.getElementById('other_row_' + idx)?.value;
  if (!state[idx]) state[idx] = {{}};
  state[idx].otherRow = val;
}}

function onNoteChange(idx) {{
  const val = document.getElementById('note_' + idx)?.value;
  if (!state[idx]) state[idx] = {{}};
  state[idx].note = val;
}}

// ── Progress ──────────────────────────────────────────────────────────────────
function updateProgress() {{
  const reviewed = Object.keys(state).filter(k => state[k]?.choice).length;
  const pct = Math.round(reviewed / TOTAL_ITEMS * 100);
  document.getElementById('pbar').style.width = pct + '%';
  document.getElementById('progress-text').textContent = reviewed + ' / ' + TOTAL_ITEMS + ' reviewed';
}}

// ── Toggle ────────────────────────────────────────────────────────────────────
function toggleSection(secId) {{
  const body = document.getElementById('body-' + secId);
  const chev = document.getElementById('chev-' + secId);
  const hdr = body?.previousElementSibling;
  if (!body) return;
  const isHidden = body.classList.contains('hidden');
  body.classList.toggle('hidden', !isHidden);
  chev?.classList.toggle('rot', isHidden);
  hdr?.classList.toggle('closed', !isHidden);
}}

function toggleResponse(hdr) {{
  const body = hdr.nextElementSibling;
  if (!body) return;
  const isHidden = body.classList.contains('hidden');
  body.classList.toggle('hidden', !isHidden);
  hdr.querySelector('span:first-child').textContent = isHidden ? '▼ AI Interview Response' : '▶ AI Interview Response';
  hdr.querySelector('.ai-resp-hint').textContent = isHidden ? 'click to collapse' : 'click to expand';
}}

function expandAll() {{
  ['sec-routing','sec-model','sec-doubt'].forEach(id => {{
    const body = document.getElementById('body-' + id);
    const chev = document.getElementById('chev-' + id);
    if (body) {{ body.classList.remove('hidden'); chev?.classList.add('rot'); }}
  }});
}}

function collapseAll() {{
  ['sec-routing','sec-model','sec-doubt'].forEach(id => {{
    const body = document.getElementById('body-' + id);
    const chev = document.getElementById('chev-' + id);
    if (body) {{ body.classList.add('hidden'); chev?.classList.remove('rot'); }}
  }});
  document.getElementById('body-sec-routing')?.classList.remove('hidden');
  document.getElementById('chev-sec-routing')?.classList.add('rot');
}}

function expandAllResponses() {{
  document.querySelectorAll('.ai-response-body').forEach(b => {{
    b.classList.remove('hidden');
    const hdr = b.previousElementSibling;
    if (hdr) {{
      hdr.querySelector('span:first-child').textContent = '▼ AI Interview Response';
      hdr.querySelector('.ai-resp-hint').textContent = 'click to collapse';
    }}
  }});
}}

function markAllAgreed() {{
  INTERVIEWS.forEach(iv => {{
    const radio = document.querySelector(`input[name="review_${{iv.index}}"][value="correct"]`);
    if (radio && !radio.checked) {{
      radio.checked = true;
      onReview(iv.index, 'correct');
    }}
  }});
}}

// ── Export ────────────────────────────────────────────────────────────────────
function exportJSON() {{
  const output = INTERVIEWS.map(iv => {{
    const s = state[iv.index] || {{}};
    return {{
      index: iv.index,
      raw_text: iv.raw_text,
      section: iv.section,
      amount: iv.amount,
      correct_row: iv.correct_row,
      correct_row_gt: iv.correct_row_gt,
      correct_name: iv.correct_name,
      predicted_row: iv.predicted_row,
      predicted_name: iv.predicted_name,
      error_type: iv.error_type,
      routed_to: iv.routed_to,
      ca_review: s.choice || null,
      ca_other_row: s.otherRow || null,
      ca_other_name: s.otherName || null,
      ca_note: s.note || null,
      reviewed: !!s.choice,
    }};
  }});

  const summary = {{
    company: "SR_Papers",
    round: 2,
    date: new Date().toISOString(),
    total_reviewed: output.filter(x => x.reviewed).length,
    total_items: TOTAL_ITEMS,
    agreed_with_ai: output.filter(x => x.ca_review === 'agree').length,
    gt_correct: output.filter(x => x.ca_review === 'correct').length,
    other: output.filter(x => x.ca_review === 'other').length,
  }};

  const blob = new Blob(
    [JSON.stringify({{summary, reviews: output}}, null, 2)],
    {{type: 'application/json'}}
  );
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'SR_Papers_round2_ca_review.json';
  a.click();
  URL.revokeObjectURL(url);
}}
</script>
</body>
</html>"""

# ─── Write file ───────────────────────────────────────────────────────────────
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(html)

size_kb = OUTPUT_PATH.stat().st_size // 1024
print(f"\nHTML report written → {OUTPUT_PATH}")
print(f"File size: {size_kb} KB")
print("Done!")
