#!/usr/bin/env python3
"""Generate 3 self-contained HTML review documents for CA from GT validation results."""

import json
import os
from pathlib import Path

BASE = Path(__file__).parent
VALIDATION = BASE / "CMA_Ground_Truth_v1" / "validation"
REFERENCE = BASE / "CMA_Ground_Truth_v1" / "reference"
OUT_DIR = BASE / "DOCS" / "test-results" / "round2"

# ── Load data ──────────────────────────────────────────────────────────────────
with open(VALIDATION / "gt_validation_final.json", encoding="utf-8") as f:
    GT = json.load(f)

with open(VALIDATION / "rule_contradictions.json", encoding="utf-8") as f:
    CONTRADICTIONS = json.load(f)

with open(REFERENCE / "canonical_labels.json", encoding="utf-8") as f:
    LABELS = json.load(f)

DISPUTES = GT["disputes"]
CROSS = CONTRADICTIONS["cross_source_contradictions"]
INTERNAL = CONTRADICTIONS["internal_contradictions"]
BY_COMPANY = GT["by_company"]

# Build row→name lookup
ROW_NAMES = {item["sheet_row"]: item["name"] for item in LABELS}


# ── Shared CSS ──────────────────────────────────────────────────────────────────
SHARED_CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f0f4f8;color:#2d3748;font-size:14px;line-height:1.6}
.container{max-width:960px;margin:0 auto;padding:16px}
.page-header{background:#1a365d;color:#fff;padding:20px 24px;border-radius:8px;margin-bottom:14px}
.page-header h1{font-size:22px;font-weight:700;margin-bottom:4px}
.page-header .sub{opacity:.75;font-size:13px}
.progress-box{background:#fff;padding:12px 16px;border-radius:8px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.progress-lbl{font-size:13px;color:#4a5568;margin-bottom:5px;display:flex;justify-content:space-between}
.pbar{background:#e2e8f0;border-radius:99px;height:10px;overflow:hidden}
.pbar-fill{background:#27ae60;height:100%;border-radius:99px;transition:width .3s}
.top-actions{display:flex;gap:10px;align-items:center;margin-bottom:12px;flex-wrap:wrap}
.ca-field{flex:1;min-width:200px}
.ca-field label{font-size:12px;font-weight:600;color:#4a5568;display:block;margin-bottom:3px}
.ca-field input{width:100%;padding:8px 12px;border:1px solid #cbd5e0;border-radius:6px;font-size:14px}
.ca-field input:focus{outline:none;border-color:#1a365d;box-shadow:0 0 0 2px #bee3f8}
.btn{padding:8px 16px;border-radius:6px;border:none;cursor:pointer;font-size:13px;font-weight:500;transition:all .15s;white-space:nowrap}
.btn-navy{background:#1a365d;color:#fff}.btn-navy:hover{background:#2c5282}
.btn-orange{background:#e67e22;color:#fff}.btn-orange:hover{background:#d35400}
.btn-green{background:#27ae60;color:#fff}.btn-green:hover{background:#229954}
.btn-outline{background:#fff;color:#4a5568;border:1px solid #cbd5e0}.btn-outline:hover{border-color:#1a365d;color:#1a365d}
.restore-banner{background:#ebf8ff;border:1px solid #90cdf4;padding:10px 14px;border-radius:6px;margin-bottom:12px;display:flex;align-items:center;gap:10px;font-size:13px}
.restore-banner.hidden{display:none}
/* Section blocks */
.sec-block{margin-bottom:14px}
.sec-hdr{background:#1a365d;color:#fff;padding:11px 16px;border-radius:8px 8px 0 0;cursor:pointer;display:flex;align-items:center;gap:10px;user-select:none}
.sec-hdr.closed{border-radius:8px;margin-bottom:0}
.sec-letter{background:#e67e22;color:#fff;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;flex-shrink:0}
.sec-title-text{font-weight:600;flex:1;font-size:15px}
.sec-count{font-size:12px;opacity:.8;white-space:nowrap}
.chevron{transition:transform .2s;font-size:12px}
.chevron.rot{transform:rotate(180deg)}
.sec-qs{background:#fff;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;overflow:hidden}
.sec-qs.hidden{display:none}
/* Dispute card */
.d-card{padding:16px;border-bottom:1px solid #f0f4f8;transition:background .15s}
.d-card:last-child{border-bottom:none}
.d-card.done{background:#f0fff4}
.d-top{display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap}
.d-num{background:#1a365d;color:#fff;padding:2px 9px;border-radius:4px;font-size:11px;font-weight:700;flex-shrink:0}
.d-raw{font-size:16px;font-weight:700;color:#1a365d;flex:1}
.pill{padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600}
.pill-mfg{background:#bee3f8;color:#2b6cb0}
.pill-trading{background:#feebc8;color:#c05621}
.pill-services{background:#c6f6d5;color:#276749}
.pill-construction{background:#fed7d7;color:#9b2c2c}
.pill-all{background:#e9d8fd;color:#553c9a}
.pill-pl{background:#e9d8fd;color:#553c9a}
.pill-bs{background:#b2f5ea;color:#234e52}
/* Comparison table */
.cmp-table{width:100%;border-collapse:collapse;margin-bottom:12px;font-size:13px}
.cmp-table th{background:#f7fafc;padding:7px 10px;text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;color:#4a5568;letter-spacing:.05em;border:1px solid #e2e8f0}
.cmp-table td{padding:8px 10px;border:1px solid #e2e8f0;vertical-align:top}
.cmp-gt{background:#fff5f5}
.cmp-rule{background:#f0fff4}
.row-num{font-weight:700;color:#1a365d;font-size:13px}
.row-name{color:#2d3748}
/* Decision section */
.decision-block{margin-bottom:10px}
.decision-lbl{font-size:12px;font-weight:700;color:#4a5568;margin-bottom:5px;text-transform:uppercase;letter-spacing:.04em}
.opt-row{display:flex;align-items:center;gap:8px;padding:5px 8px;border-radius:5px;margin-bottom:2px;cursor:pointer;border:1px solid transparent;transition:background .1s}
.opt-row:hover{background:#f7fafc}
.opt-row.sel{background:#f0fff4;border-color:#9ae6b4}
.opt-row input[type=radio]{accent-color:#27ae60;cursor:pointer;flex-shrink:0}
.opt-row label{cursor:pointer;flex:1;font-size:13px}
.other-inputs{display:flex;gap:6px;align-items:center;flex-wrap:wrap;padding:4px 8px 6px 28px}
.other-inputs input{padding:4px 8px;border:1px solid #cbd5e0;border-radius:4px;font-size:13px}
.other-inputs input:focus{outline:none;border-color:#1a365d}
.other-num{width:70px}
.other-name{flex:1;min-width:150px}
/* Collapsible extra rows */
.extra-toggle{background:none;border:1px solid #e2e8f0;padding:4px 10px;border-radius:4px;font-size:12px;cursor:pointer;color:#4a5568;display:flex;align-items:center;gap:5px;margin-bottom:6px}
.extra-toggle:hover{border-color:#1a365d;color:#1a365d}
.extra-body{display:none;padding:10px;background:#f7fafc;border:1px solid #e2e8f0;border-radius:6px;margin-bottom:8px}
.extra-body.open{display:block}
/* Industry grid */
.ind-grid{width:100%;border-collapse:collapse;font-size:13px;margin-top:6px}
.ind-grid th{background:#edf2f7;padding:5px 8px;font-size:11px;text-align:left;font-weight:700;color:#4a5568;border:1px solid #e2e8f0}
.ind-grid td{padding:5px 8px;border:1px solid #e2e8f0;vertical-align:middle}
.ind-grid td:first-child{font-weight:600;font-size:12px;color:#2d3748;white-space:nowrap}
.ind-grid input{width:100%;padding:3px 6px;border:1px solid #cbd5e0;border-radius:3px;font-size:12px}
.ind-grid input:focus{outline:none;border-color:#1a365d}
/* Confidence */
.conf-row{margin-bottom:8px}
.conf-lbl{font-size:12px;font-weight:700;color:#4a5568;margin-bottom:4px;text-transform:uppercase;letter-spacing:.04em}
.conf-opts{display:flex;gap:16px;flex-wrap:wrap}
.conf-opt{display:flex;align-items:center;gap:5px;cursor:pointer;font-size:13px}
.conf-opt input{accent-color:#1a365d}
/* Notes */
.notes-row{margin-bottom:8px}
.notes-row label{font-size:12px;font-weight:700;color:#4a5568;display:block;margin-bottom:3px;text-transform:uppercase;letter-spacing:.04em}
.notes-row textarea{width:100%;padding:6px 10px;border:1px solid #e2e8f0;border-radius:5px;font-size:13px;resize:vertical;min-height:34px;font-family:inherit}
.notes-row textarea:focus{outline:none;border-color:#1a365d}
/* AI analysis box */
.ai-box{background:#fef3e2;border-left:3px solid #e67e22;padding:8px 12px;font-size:12px;margin-bottom:10px;border-radius:0 4px 4px 0;color:#744210}
.ai-box strong{color:#e67e22}
/* Section label */
.d-section{font-size:11px;color:#718096;margin-bottom:6px}
/* Summary cards */
.summary-cards{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.s-card{background:#fff;border-radius:8px;padding:12px 16px;box-shadow:0 1px 3px rgba(0,0,0,.08);flex:1;min-width:120px}
.s-card .val{font-size:24px;font-weight:700;color:#1a365d}
.s-card .lbl{font-size:12px;color:#718096;margin-top:2px}
/* Company tabs */
.tabs{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:12px}
.tab{padding:6px 12px;border-radius:6px 6px 0 0;font-size:13px;font-weight:500;cursor:pointer;border:1px solid #e2e8f0;background:#f7fafc;color:#4a5568;transition:all .15s;border-bottom:none}
.tab.active{background:#1a365d;color:#fff;border-color:#1a365d}
.tab-content{display:none}
.tab-content.active{display:block}
.violations-table{width:100%;border-collapse:collapse;font-size:13px}
.violations-table th{background:#1a365d;color:#fff;padding:8px 10px;text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.04em}
.violations-table td{padding:8px 10px;border-bottom:1px solid #e2e8f0;vertical-align:middle}
.violations-table tr:hover td{background:#f7fafc}
.inline-radio{display:flex;align-items:center;gap:6px;white-space:nowrap}
.inline-radio input{accent-color:#1a365d}
.inline-note{width:120px;padding:3px 6px;border:1px solid #cbd5e0;border-radius:3px;font-size:12px}
.resolved-badge{background:#c6f6d5;color:#276749;padding:2px 7px;border-radius:4px;font-size:11px;font-weight:600}
"""

# ── Shared JS helpers ──────────────────────────────────────────────────────────
SHARED_JS = """
// Row name lookup
function rowName(row) {
  return ROW_NAMES[row] || '';
}

// Auto-fill row name when number is typed
function setupRowNameAutoFill(numInput, nameInput) {
  numInput.addEventListener('input', function() {
    const n = parseInt(this.value);
    if (n && ROW_NAMES[n]) nameInput.value = ROW_NAMES[n];
  });
}

// Progress tracking
function updateProgress(storageKey, total, counterEl, barEl) {
  const saved = JSON.parse(localStorage.getItem(storageKey) || '{"responses":{}}');
  const reviewed = Object.keys(saved.responses || {}).length;
  if (counterEl) counterEl.textContent = reviewed + ' of ' + total + ' reviewed';
  if (barEl) barEl.style.width = Math.round((reviewed/total)*100) + '%';
  return reviewed;
}

// Save to localStorage
function saveResponse(storageKey, itemId, data) {
  let saved = JSON.parse(localStorage.getItem(storageKey) || '{"responses":{}}');
  saved.responses[itemId] = data;
  saved.lastSaved = new Date().toISOString();
  const caInput = document.getElementById('ca-name');
  if (caInput) saved.reviewer = caInput.value;
  localStorage.setItem(storageKey, JSON.stringify(saved));
}

// Export JSON
function exportJSON(storageKey, filename) {
  const saved = JSON.parse(localStorage.getItem(storageKey) || '{"responses":{}}');
  const blob = new Blob([JSON.stringify(saved, null, 2)], {type:'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
}

// Collapsible section headers
function setupSectionToggles() {
  document.querySelectorAll('.sec-hdr').forEach(function(hdr) {
    hdr.addEventListener('click', function() {
      const qs = this.parentElement.querySelector('.sec-qs');
      const chev = this.querySelector('.chevron');
      if (qs) {
        qs.classList.toggle('hidden');
        hdr.classList.toggle('closed', qs.classList.contains('hidden'));
        if (chev) chev.classList.toggle('rot', !qs.classList.contains('hidden'));
      }
    });
  });
}

// Extra toggle (industry/context rows)
function setupExtraToggles() {
  document.querySelectorAll('.extra-toggle').forEach(function(btn) {
    btn.addEventListener('click', function() {
      const target = document.getElementById(this.dataset.target);
      if (target) {
        target.classList.toggle('open');
        const arrow = this.querySelector('.arrow');
        if (arrow) arrow.textContent = target.classList.contains('open') ? '▲' : '▼';
      }
    });
  });
}

// Industry/context Yes toggle
function setupIndustryToggles() {
  document.querySelectorAll('.ind-toggle').forEach(function(radio) {
    radio.addEventListener('change', function() {
      const gridId = this.dataset.grid;
      const grid = document.getElementById(gridId);
      if (!grid) return;
      if (this.value === 'yes') {
        grid.style.display = 'block';
      } else {
        grid.style.display = 'none';
      }
    });
  });
}

// Restore banner
function checkRestore(storageKey, bannerEl) {
  const saved = JSON.parse(localStorage.getItem(storageKey) || '{}');
  if (saved.lastSaved && Object.keys(saved.responses || {}).length > 0) {
    if (bannerEl) {
      const count = Object.keys(saved.responses).length;
      const ts = new Date(saved.lastSaved).toLocaleString();
      bannerEl.querySelector('.restore-msg').textContent =
        'Restored ' + count + ' saved responses from ' + ts;
      bannerEl.classList.remove('hidden');
    }
    restoreAllResponses(storageKey);
  }
}

function clearSaved(storageKey, bannerEl) {
  localStorage.removeItem(storageKey);
  if (bannerEl) bannerEl.classList.add('hidden');
  location.reload();
}
"""


def industry_pill(industry):
    cls = {
        "manufacturing": "pill-mfg",
        "trading": "pill-trading",
        "services": "pill-services",
        "construction": "pill-construction",
        "all": "pill-all",
    }.get(industry, "pill-all")
    return f'<span class="pill {cls}">{industry.capitalize()}</span>'


def context_pill(ctx):
    if not ctx:
        return ""
    cls = "pill-pl" if ctx == "pl" else "pill-bs"
    label = "P&L" if ctx == "pl" else "B/S"
    return f'<span class="pill {cls}">{label}</span>'


def row_display(row, name):
    if not row:
        return "—"
    n = name or ROW_NAMES.get(row, "")
    return f"<span class='row-num'>Row {row}</span> — <span class='row-name'>{n}</span>"


# ══════════════════════════════════════════════════════════════════════════════
#  DOCUMENT 1 — GT Disputes Review
# ══════════════════════════════════════════════════════════════════════════════
def build_disputes_html():
    """Build Document 1 using JS-based rendering to keep file under 500KB."""
    # Assign IDs and group disputes
    industry_keywords = ["manufacturing", "factory", "industry", "industries"]
    all_disputes = []
    for i, d in enumerate(DISPUTES):
        d2 = dict(d)
        d2["_id"] = f"d{i+1:03d}"
        reasoning = (d2.get("agent_reasoning") or "").lower()
        has_industry = any(kw in reasoning for kw in industry_keywords)
        if has_industry:
            d2["_group"] = "industry"
        elif d2.get("document_context") == "bs":
            d2["_group"] = "bs"
        else:
            d2["_group"] = d2.get("company", "unknown")
        all_disputes.append(d2)

    # Build compact data payload for JS (only needed fields)
    compact = []
    for d in all_disputes:
        gt_name = ROW_NAMES.get(d.get("gt_row"), d.get("gt_field", ""))
        gr_name = ROW_NAMES.get(d.get("golden_rule_row"), d.get("golden_rule_name", ""))
        compact.append({
            "id": d["_id"],
            "group": d["_group"],
            "raw": d.get("raw_text", ""),
            "section": d.get("section", ""),
            "company": d.get("company", ""),
            "industry": d.get("industry_type", ""),
            "ctx": d.get("document_context", ""),
            "gt_row": d.get("gt_row"),
            "gt_name": gt_name,
            "gr_row": d.get("golden_rule_row"),
            "gr_name": gr_name,
            "method": d.get("match_method", ""),
            "score": d.get("fuzzy_score"),
            "ai": d.get("agent_reasoning") or "",
        })

    # Build sections list for rendering order
    groups_order = ["industry", "bs"]
    companies_seen = []
    for d in all_disputes:
        g = d["_group"]
        if g not in groups_order and g not in companies_seen:
            companies_seen.append(g)
    companies_seen.sort()
    groups_order.extend(companies_seen)

    # Section definitions
    sections = []
    for g in groups_order:
        items = [d for d in compact if d["group"] == g]
        if not items:
            continue
        if g == "industry":
            label = "Industry-Dependent Disputes"
        elif g == "bs":
            label = "Balance Sheet / Context-Dependent Disputes"
        else:
            ind = items[0]["industry"] if items else ""
            label = f"{g.replace('_',' ')} ({ind.capitalize()})"
        sections.append({"key": g, "label": label, "ids": [d["id"] for d in items]})

    # Summary mini-cards
    company_cards = "".join(
        f"<div class='s-card'><div class='val'>{v['dispute']}</div><div class='lbl'>{k.replace('_',' ')}</div></div>"
        for k, v in BY_COMPANY.items()
    )

    # Build static section skeleton (empty containers, JS fills them)
    sections_html = ""
    for idx, sec in enumerate(sections):
        letter = str(idx + 1)
        count = len(sec["ids"])
        sections_html += f"""
<div class="sec-block" id="sec-{sec['key'].replace(' ','_')}">
  <div class="sec-hdr">
    <span class="sec-letter">{letter}</span>
    <span class="sec-title-text">{sec['label']}</span>
    <span class="sec-count">{count} disputes</span>
    <span class="chevron rot">&#9660;</span>
  </div>
  <div class="sec-qs" id="qs-{sec['key'].replace(' ','_')}"></div>
</div>"""

    data_json = json.dumps(compact, ensure_ascii=False, separators=(",", ":"))
    sections_json = json.dumps(sections, ensure_ascii=False, separators=(",", ":"))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CMA Ground Truth &mdash; Dispute Review</title>
<style>
{SHARED_CSS}
</style>
</head>
<body>
<div class="container">

<div class="page-header">
  <h1>CMA Ground Truth &mdash; Dispute Review</h1>
  <div class="sub">175 items where GT differs from golden rules &mdash; resolve each one</div>
</div>

<div class="restore-banner hidden" id="restore-banner">
  &#128190;
  <span class="restore-msg"></span>
  <button class="btn btn-outline" onclick="clearAll()">Clear &amp; Restart</button>
</div>

<div class="top-actions">
  <div class="ca-field">
    <label>CA Name</label>
    <input type="text" id="ca-name" placeholder="Your name..." oninput="saveMeta()">
  </div>
  <div class="ca-field">
    <label>Date</label>
    <input type="text" id="review-date" value="2026-03-27">
  </div>
  <button class="btn btn-orange" onclick="exportJSON('cma_gt_disputes_v2','GT_disputes_responses.json')">Export JSON</button>
</div>

<div class="progress-box">
  <div class="progress-lbl">
    <span id="prog-counter">0 of 175 reviewed</span>
    <span id="prog-pct">0%</span>
  </div>
  <div class="pbar"><div class="pbar-fill" id="prog-bar" style="width:0%"></div></div>
</div>

<div class="summary-cards">
  <div class="s-card"><div class="val">175</div><div class="lbl">Total Disputes</div></div>
  <div class="s-card"><div class="val">88</div><div class="lbl">Cross-Company</div></div>
  {company_cards}
</div>

{sections_html}

</div>
<script>
const ROW_NAMES = {json.dumps(ROW_NAMES, separators=(',', ':'))};
const DISPUTES_DATA = {data_json};
const SECTIONS = {sections_json};
const STORAGE_KEY = 'cma_gt_disputes_v2';
const TOTAL = 175;

{SHARED_JS}

// ── Pill helpers ──────────────────────────────────────────────────────────────
const IND_CLS = {{manufacturing:'pill-mfg',trading:'pill-trading',services:'pill-services',construction:'pill-construction',all:'pill-all'}};
function indPill(i){{return i?'<span class="pill '+(IND_CLS[i]||'pill-all')+'">'+i.charAt(0).toUpperCase()+i.slice(1)+'</span>':''}}
function ctxPill(c){{if(!c)return'';return c==='pl'?'<span class="pill pill-pl">P&amp;L</span>':'<span class="pill pill-bs">B/S</span>'}}

// ── Card renderer ─────────────────────────────────────────────────────────────
function buildCard(d, num) {{
  const iid = d.id;
  const gtLabel = 'Row '+d.gt_row+': '+d.gt_name;
  const grLabel = 'Row '+d.gr_row+': '+d.gr_name;
  const methodBadge = d.method ? '<span style="font-size:10px;background:#e2e8f0;padding:1px 5px;border-radius:3px;color:#4a5568">'+d.method+(d.score?' '+Math.round(d.score)+'%':'')+'</span>' : '';
  const aiBox = d.ai ? '<div class="ai-box"><strong>AI:</strong> '+escHtml(d.ai)+'</div>' : '';

  return `<div class="d-card" id="card-${{iid}}">
  <div class="d-top">
    <span class="d-num">#${{num}}</span>
    <span class="d-raw">${{escHtml(d.raw)}}</span>
    ${{indPill(d.industry)}} ${{ctxPill(d.ctx)}} ${{methodBadge}}
  </div>
  <div class="d-section">Section: ${{escHtml(d.section)}} &nbsp;|&nbsp; Company: <strong>${{d.company}}</strong></div>
  ${{aiBox}}
  <table class="cmp-table">
    <tr><th>GT (Current)</th><th>Golden Rule (Expected)</th></tr>
    <tr>
      <td class="cmp-gt"><span class="row-num">Row ${{d.gt_row}}</span> &mdash; ${{escHtml(d.gt_name)}}</td>
      <td class="cmp-rule"><span class="row-num">Row ${{d.gr_row}}</span> &mdash; ${{escHtml(d.gr_name)}}</td>
    </tr>
  </table>

  <div class="decision-block">
    <div class="decision-lbl">A. Your Decision</div>
    <div class="opt-row" onclick="selOpt('${{iid}}','gt',this)">
      <input type="radio" name="dec-${{iid}}" value="gt" id="gt-${{iid}}">
      <label for="gt-${{iid}}">GT is correct &mdash; ${{gtLabel}}</label>
    </div>
    <div class="opt-row" onclick="selOpt('${{iid}}','rule',this)">
      <input type="radio" name="dec-${{iid}}" value="rule" id="rule-${{iid}}">
      <label for="rule-${{iid}}">Golden Rule is correct &mdash; ${{grLabel}}</label>
    </div>
    <div class="opt-row" onclick="selOpt('${{iid}}','other',this)">
      <input type="radio" name="dec-${{iid}}" value="other" id="other-${{iid}}">
      <label for="other-${{iid}}">Other:</label>
    </div>
    <div class="other-inputs" id="oi-${{iid}}" style="display:none">
      <span>Row</span>
      <input type="number" class="other-num" id="on-${{iid}}" placeholder="e.g. 49" oninput="afName('${{iid}}')">
      <input type="text" class="other-name" id="oname-${{iid}}" placeholder="Field name">
    </div>
  </div>

  <button class="extra-toggle" onclick="toggleExtra('ind-${{iid}}',this)">
    <span>B. Industry-specific mapping?</span> <span class="arrow">&#9660;</span>
  </button>
  <div class="extra-body" id="ind-${{iid}}">
    <div style="font-size:12px;color:#4a5568;margin-bottom:6px">Different row per industry?</div>
    <div style="display:flex;gap:12px;margin-bottom:8px">
      <label style="display:flex;align-items:center;gap:5px;font-size:13px;cursor:pointer">
        <input type="radio" name="it-${{iid}}" value="no" checked onchange="toggleIndGrid('${{iid}}',false);saveCard('${{iid}}')"> No
      </label>
      <label style="display:flex;align-items:center;gap:5px;font-size:13px;cursor:pointer">
        <input type="radio" name="it-${{iid}}" value="yes" onchange="toggleIndGrid('${{iid}}',true);saveCard('${{iid}}')"> Yes
      </label>
    </div>
    <div id="ig-${{iid}}" style="display:none">
      <table class="ind-grid">
        <tr><th>Industry</th><th>Row #</th><th>Field Name</th></tr>
        ${{['Manufacturing:mfg','Trading:trd','Services:svc','Construction:con'].map(p=>{{const[lbl,k]=p.split(':');return`<tr><td>${{lbl}}</td><td><input type="number" id="ir-${{iid}}-${{k}}" oninput="afInd('${{iid}}','${{k}}');saveCard('${{iid}}')"></td><td><input type="text" id="in-${{iid}}-${{k}}" oninput="saveCard('${{iid}}')"></td></tr>`;}}).join('')}}
      </table>
    </div>
  </div>

  <button class="extra-toggle" onclick="toggleExtra('ctx-${{iid}}',this)">
    <span>C. P&amp;L vs Balance Sheet?</span> <span class="arrow">&#9660;</span>
  </button>
  <div class="extra-body" id="ctx-${{iid}}">
    <div style="font-size:12px;color:#4a5568;margin-bottom:6px">Different row in P&amp;L vs B/S?</div>
    <div style="display:flex;gap:12px;margin-bottom:8px">
      <label style="display:flex;align-items:center;gap:5px;font-size:13px;cursor:pointer">
        <input type="radio" name="ct-${{iid}}" value="no" checked onchange="toggleCtxGrid('${{iid}}',false);saveCard('${{iid}}')"> No
      </label>
      <label style="display:flex;align-items:center;gap:5px;font-size:13px;cursor:pointer">
        <input type="radio" name="ct-${{iid}}" value="yes" onchange="toggleCtxGrid('${{iid}}',true);saveCard('${{iid}}')"> Yes
      </label>
    </div>
    <div id="cg-${{iid}}" style="display:none">
      <table class="ind-grid">
        <tr><th>Context</th><th>Row #</th><th>Field Name</th></tr>
        <tr><td>P&amp;L</td><td><input type="number" id="cr-${{iid}}-pl" oninput="afCtx('${{iid}}','pl');saveCard('${{iid}}')"></td><td><input type="text" id="cn-${{iid}}-pl" oninput="saveCard('${{iid}}')"></td></tr>
        <tr><td>B/S</td><td><input type="number" id="cr-${{iid}}-bs" oninput="afCtx('${{iid}}','bs');saveCard('${{iid}}')"></td><td><input type="text" id="cn-${{iid}}-bs" oninput="saveCard('${{iid}}')"></td></tr>
      </table>
    </div>
  </div>

  <div class="notes-row">
    <label>D. Notes / Special Conditions</label>
    <textarea id="notes-${{iid}}" rows="2" placeholder="Notes, reasoning, edge cases..." oninput="saveCard('${{iid}}')"></textarea>
  </div>
  <div class="conf-row">
    <div class="conf-lbl">E. Confidence</div>
    <div class="conf-opts">
      <label class="conf-opt"><input type="radio" name="conf-${{iid}}" value="certain" onchange="saveCard('${{iid}}')"> Certain</label>
      <label class="conf-opt"><input type="radio" name="conf-${{iid}}" value="likely" onchange="saveCard('${{iid}}')"> Likely</label>
      <label class="conf-opt"><input type="radio" name="conf-${{iid}}" value="discuss" onchange="saveCard('${{iid}}')"> Needs Discussion</label>
    </div>
  </div>
</div>`;
}}

function escHtml(s){{
  if(!s)return'';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}

function toggleExtra(id, btn) {{
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.toggle('open');
  const arrow = btn.querySelector('.arrow');
  if (arrow) arrow.textContent = el.classList.contains('open') ? '\\u25b2' : '\\u25bc';
}}

function toggleIndGrid(iid, show) {{
  const g = document.getElementById('ig-'+iid);
  if (g) g.style.display = show ? 'block' : 'none';
}}
function toggleCtxGrid(iid, show) {{
  const g = document.getElementById('cg-'+iid);
  if (g) g.style.display = show ? 'block' : 'none';
}}

function afName(iid) {{
  const n = parseInt(document.getElementById('on-'+iid).value);
  if (n && ROW_NAMES[n]) document.getElementById('oname-'+iid).value = ROW_NAMES[n];
  saveCard(iid);
}}
function afInd(iid, k) {{
  const n = parseInt((document.getElementById('ir-'+iid+'-'+k)||{{}}).value);
  if (n && ROW_NAMES[n]) {{ const el = document.getElementById('in-'+iid+'-'+k); if(el) el.value = ROW_NAMES[n]; }}
}}
function afCtx(iid, k) {{
  const n = parseInt((document.getElementById('cr-'+iid+'-'+k)||{{}}).value);
  if (n && ROW_NAMES[n]) {{ const el = document.getElementById('cn-'+iid+'-'+k); if(el) el.value = ROW_NAMES[n]; }}
}}

function selOpt(iid, val, row) {{
  document.querySelectorAll('[name="dec-'+iid+'"]').forEach(function(r){{r.closest('.opt-row').classList.remove('sel');}});
  const radio = document.getElementById(val+'-'+iid);
  if (radio) {{ radio.checked = true; if(row) row.classList.add('sel'); }}
  const oi = document.getElementById('oi-'+iid);
  if (oi) oi.style.display = (val === 'other') ? 'flex' : 'none';
  saveCard(iid);
}}

function getCardData(iid) {{
  const dec = document.querySelector('[name="dec-'+iid+'"]:checked');
  const conf = document.querySelector('[name="conf-'+iid+'"]:checked');
  const itYes = document.querySelector('[name="it-'+iid+'"][value="yes"]:checked');
  const ctYes = document.querySelector('[name="ct-'+iid+'"][value="yes"]:checked');
  const data = {{
    item_id: iid,
    decision: dec ? dec.value : null,
    confidence: conf ? conf.value : null,
    notes: (document.getElementById('notes-'+iid)||{{}}).value || '',
    industry_specific: null,
    context_specific: null
  }};
  if (data.decision === 'other') {{
    data.selected_row = parseInt((document.getElementById('on-'+iid)||{{}}).value)||null;
    data.selected_name = (document.getElementById('oname-'+iid)||{{}}).value||'';
  }}
  if (itYes) {{
    data.industry_specific = {{}};
    [['manufacturing','mfg'],['trading','trd'],['services','svc'],['construction','con']].forEach(function(p) {{
      data.industry_specific[p[0]] = {{
        row: parseInt((document.getElementById('ir-'+iid+'-'+p[1])||{{}}).value)||null,
        name: (document.getElementById('in-'+iid+'-'+p[1])||{{}}).value||''
      }};
    }});
  }}
  if (ctYes) {{
    data.context_specific = {{
      pnl: {{ row: parseInt((document.getElementById('cr-'+iid+'-pl')||{{}}).value)||null, name: (document.getElementById('cn-'+iid+'-pl')||{{}}).value||'' }},
      bs:  {{ row: parseInt((document.getElementById('cr-'+iid+'-bs')||{{}}).value)||null, name: (document.getElementById('cn-'+iid+'-bs')||{{}}).value||'' }}
    }};
  }}
  return data;
}}

function saveCard(iid) {{
  const data = getCardData(iid);
  saveResponse(STORAGE_KEY, iid, data);
  const card = document.getElementById('card-'+iid);
  if (card && data.decision) card.classList.add('done');
  refreshProgress();
}}

function refreshProgress() {{
  const saved = JSON.parse(localStorage.getItem(STORAGE_KEY)||'{{"responses":{{}}}}');
  const reviewed = Object.keys(saved.responses||{{}}).length;
  const pct = Math.round((reviewed/TOTAL)*100);
  document.getElementById('prog-counter').textContent = reviewed+' of '+TOTAL+' reviewed';
  document.getElementById('prog-pct').textContent = pct+'%';
  document.getElementById('prog-bar').style.width = pct+'%';
}}

function saveMeta() {{
  let saved = JSON.parse(localStorage.getItem(STORAGE_KEY)||'{{"responses":{{}}}}');
  saved.reviewer = document.getElementById('ca-name').value;
  saved.date = document.getElementById('review-date').value;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(saved));
}}

function clearAll() {{
  localStorage.removeItem(STORAGE_KEY);
  document.getElementById('restore-banner').classList.add('hidden');
  location.reload();
}}

function restoreAllResponses(key) {{
  const saved = JSON.parse(localStorage.getItem(key)||'{{"responses":{{}}}}');
  if (saved.reviewer) {{ const el = document.getElementById('ca-name'); if(el) el.value = saved.reviewer; }}
  Object.entries(saved.responses||{{}}).forEach(function([iid, data]) {{
    if (!data.decision) return;
    const card = document.getElementById('card-'+iid);
    if (!card) return; // card not yet rendered
    const radio = document.getElementById(data.decision+'-'+iid);
    if (radio) {{
      radio.checked = true;
      const row = radio.closest('.opt-row');
      if (row) row.classList.add('sel');
    }}
    if (data.decision === 'other') {{
      const oi = document.getElementById('oi-'+iid);
      if (oi) oi.style.display = 'flex';
      if (data.selected_row) {{ const n = document.getElementById('on-'+iid); if(n) n.value = data.selected_row; }}
      if (data.selected_name) {{ const n = document.getElementById('oname-'+iid); if(n) n.value = data.selected_name; }}
    }}
    if (data.notes) {{ const el = document.getElementById('notes-'+iid); if(el) el.value = data.notes; }}
    if (data.confidence) {{
      const el = document.querySelector('[name="conf-'+iid+'"][value="'+data.confidence+'"]');
      if (el) el.checked = true;
    }}
    if (data.industry_specific) {{
      const yes = document.querySelector('[name="it-'+iid+'"][value="yes"]');
      if (yes) {{ yes.checked = true; toggleIndGrid(iid, true); }}
      Object.entries(data.industry_specific).forEach(function([ind, info]) {{
        const k = {{manufacturing:'mfg',trading:'trd',services:'svc',construction:'con'}}[ind];
        if (k && info) {{
          if (info.row) {{ const el = document.getElementById('ir-'+iid+'-'+k); if(el) el.value = info.row; }}
          if (info.name) {{ const el = document.getElementById('in-'+iid+'-'+k); if(el) el.value = info.name; }}
        }}
      }});
    }}
    if (data.context_specific) {{
      const yes = document.querySelector('[name="ct-'+iid+'"][value="yes"]');
      if (yes) {{ yes.checked = true; toggleCtxGrid(iid, true); }}
      ['pnl','bs'].forEach(function(k) {{
        const info = data.context_specific[k];
        const mk = k === 'pnl' ? 'pl' : 'bs';
        if (info) {{
          if (info.row) {{ const el = document.getElementById('cr-'+iid+'-'+mk); if(el) el.value = info.row; }}
          if (info.name) {{ const el = document.getElementById('cn-'+iid+'-'+mk); if(el) el.value = info.name; }}
        }}
      }});
    }}
    if (card && data.decision) card.classList.add('done');
  }});
  refreshProgress();
}}

// ── Render cards into sections on load ────────────────────────────────────────
function renderSections() {{
  const byId = {{}};
  DISPUTES_DATA.forEach(function(d){{ byId[d.id] = d; }});
  let globalNum = 1;
  SECTIONS.forEach(function(sec) {{
    const container = document.getElementById('qs-'+sec.key.replace(/ /g,'_'));
    if (!container) return;
    let html = '';
    sec.ids.forEach(function(id) {{
      const d = byId[id];
      if (d) html += buildCard(d, globalNum++);
    }});
    container.innerHTML = html;
  }});
  // Section toggle
  setupSectionToggles();
  // Restore saved data
  checkRestore(STORAGE_KEY, document.getElementById('restore-banner'));
  refreshProgress();
}}

document.addEventListener('DOMContentLoaded', renderSections);
</script>
</body>
</html>"""
    return html


# ══════════════════════════════════════════════════════════════════════════════
#  DOCUMENT 2 — Rule Contradictions Review
# ══════════════════════════════════════════════════════════════════════════════
def build_contradictions_html():
    total = len(CROSS) + len(INTERNAL)

    def cross_card(item, num):
        iid = f"cross_{num:03d}"
        text = item.get("ca_item_text", item.get("rule_fs_item", ""))
        ca_row = item.get("ca_row")
        ca_name = item.get("ca_name", "")
        rule_row = item.get("rule_row")
        rule_name = item.get("rule_name", "")
        industry = item.get("industry", "all")
        source = item.get("ca_source", "")
        q_id = item.get("question_id", "")
        score = item.get("fuzzy_score")

        ca_name_full = ROW_NAMES.get(ca_row, ca_name)
        rule_name_full = ROW_NAMES.get(rule_row, rule_name)

        score_badge = f"<span style='font-size:10px;background:#e2e8f0;padding:1px 5px;border-radius:3px'>{score:.0f}% match</span>" if score else ""

        return f"""
<div class="d-card" id="card-{iid}">
  <div class="d-top">
    <span class="d-num">#{num}</span>
    <span class="d-raw">{text}</span>
    {industry_pill(industry)}
    {score_badge}
  </div>
  <div class="d-section">Question ID: <strong>{q_id}</strong> &nbsp;|&nbsp; CA Source: {source}</div>
  <table class="cmp-table">
    <tr>
      <th>Source 1 (Classification XLS)</th>
      <th>Source 2 (CA Answers 2026-03-26)</th>
    </tr>
    <tr>
      <td class="cmp-gt">{row_display(rule_row, rule_name_full)}</td>
      <td class="cmp-rule">{row_display(ca_row, ca_name_full)}</td>
    </tr>
  </table>

  <div class="decision-block">
    <div class="decision-lbl">Your Decision</div>
    <div class="opt-row" onclick="selectOpt2('{iid}','s1',this)">
      <input type="radio" name="dec-{iid}" value="s1" id="s1-{iid}">
      <label for="s1-{iid}">Source 1 is correct — Row {rule_row}: {rule_name_full}</label>
    </div>
    <div class="opt-row" onclick="selectOpt2('{iid}','s2',this)">
      <input type="radio" name="dec-{iid}" value="s2" id="s2-{iid}">
      <label for="s2-{iid}">Source 2 is correct — Row {ca_row}: {ca_name_full}</label>
    </div>
    <div class="opt-row" onclick="selectOpt2('{iid}','ind',this)">
      <input type="radio" name="dec-{iid}" value="ind" id="ind-{iid}">
      <label for="ind-{iid}">Industry-dependent (different per industry)</label>
    </div>
    <div class="opt-row" onclick="selectOpt2('{iid}','ctx',this)">
      <input type="radio" name="dec-{iid}" value="ctx" id="ctx-{iid}">
      <label for="ctx-{iid}">Context-dependent (P&amp;L vs B/S)</label>
    </div>
    <div class="opt-row" onclick="selectOpt2('{iid}','other',this)">
      <input type="radio" name="dec-{iid}" value="other" id="other-{iid}">
      <label for="other-{iid}">Other:</label>
    </div>
    <div class="other-inputs" id="other-inputs-{iid}" style="display:none">
      <span>Row</span>
      <input type="number" class="other-num" id="other-num-{iid}" placeholder="e.g. 49"
             oninput="autoFill2('{iid}','other-num-{iid}','other-name-{iid}')">
      <input type="text" class="other-name" id="other-name-{iid}" placeholder="Field name">
    </div>
  </div>

  <!-- Industry grid (hidden unless ind selected) -->
  <div class="extra-body" id="ind-grid-wrap-{iid}" style="display:none">
    <table class="ind-grid">
      <tr><th>Industry</th><th>Row #</th><th>Field Name</th></tr>
      <tr><td>Manufacturing</td><td><input type="number" id="ind-mfg-row-{iid}" oninput="autoFillInd2('{iid}','mfg');saveCard2('{iid}')"></td><td><input type="text" id="ind-mfg-name-{iid}" oninput="saveCard2('{iid}')"></td></tr>
      <tr><td>Trading</td><td><input type="number" id="ind-trd-row-{iid}" oninput="autoFillInd2('{iid}','trd');saveCard2('{iid}')"></td><td><input type="text" id="ind-trd-name-{iid}" oninput="saveCard2('{iid}')"></td></tr>
      <tr><td>Services</td><td><input type="number" id="ind-svc-row-{iid}" oninput="autoFillInd2('{iid}','svc');saveCard2('{iid}')"></td><td><input type="text" id="ind-svc-name-{iid}" oninput="saveCard2('{iid}')"></td></tr>
      <tr><td>Construction</td><td><input type="number" id="ind-con-row-{iid}" oninput="autoFillInd2('{iid}','con');saveCard2('{iid}')"></td><td><input type="text" id="ind-con-name-{iid}" oninput="saveCard2('{iid}')"></td></tr>
    </table>
  </div>
  <!-- Context grid -->
  <div class="extra-body" id="ctx-grid-wrap-{iid}" style="display:none">
    <table class="ind-grid">
      <tr><th>Context</th><th>Row #</th><th>Field Name</th></tr>
      <tr><td>Profit &amp; Loss</td><td><input type="number" id="ctx-pl-row-{iid}" oninput="autoFillCtx2('{iid}','pl');saveCard2('{iid}')"></td><td><input type="text" id="ctx-pl-name-{iid}" oninput="saveCard2('{iid}')"></td></tr>
      <tr><td>Balance Sheet</td><td><input type="number" id="ctx-bs-row-{iid}" oninput="autoFillCtx2('{iid}','bs');saveCard2('{iid}')"></td><td><input type="text" id="ctx-bs-name-{iid}" oninput="saveCard2('{iid}')"></td></tr>
    </table>
  </div>

  <div class="notes-row">
    <label>Notes</label>
    <textarea id="notes-{iid}" rows="2" placeholder="Add reasoning..." oninput="saveCard2('{iid}')"></textarea>
  </div>
  <div class="conf-row">
    <div class="conf-lbl">Confidence</div>
    <div class="conf-opts">
      <label class="conf-opt"><input type="radio" name="conf-{iid}" value="certain" onchange="saveCard2('{iid}')"> Certain</label>
      <label class="conf-opt"><input type="radio" name="conf-{iid}" value="likely" onchange="saveCard2('{iid}')"> Likely</label>
      <label class="conf-opt"><input type="radio" name="conf-{iid}" value="discuss" onchange="saveCard2('{iid}')"> Needs Discussion</label>
    </div>
  </div>
</div>"""

    def internal_card(item, num):
        iid = f"int_{num:03d}"
        # Handle two structure types
        if "conflicting_rules" in item:
            fs_item = item.get("fs_item", "")
            r1 = item["conflicting_rules"][0]
            r2 = item["conflicting_rules"][1]
            text = fs_item
            row1, name1 = r1["row"], r1.get("canonical_name", "")
            row2, name2 = r2["row"], r2.get("canonical_name", "")
            sheet = item.get("source_sheet", "")
            score = None
        else:
            r1 = item.get("rule_1", {})
            r2 = item.get("rule_2", {})
            text = r1.get("fs_item", r2.get("fs_item", ""))
            row1, name1 = r1.get("row"), r1.get("canonical_name", "")
            row2, name2 = r2.get("row"), r2.get("canonical_name", "")
            sheet = item.get("source_sheet", "")
            score = item.get("fuzzy_score")

        name1_full = ROW_NAMES.get(row1, name1)
        name2_full = ROW_NAMES.get(row2, name2)
        score_badge = f"<span style='font-size:10px;background:#fef3e2;padding:1px 5px;border-radius:3px;color:#c05621'>{score:.0f}% similar</span>" if score else ""
        itype = item.get("type", "").replace("_", " ")

        return f"""
<div class="d-card" id="card-{iid}">
  <div class="d-top">
    <span class="d-num">#{num}</span>
    <span class="d-raw">{text}</span>
    {score_badge}
    <span style="font-size:10px;background:#e2e8f0;padding:1px 5px;border-radius:3px;color:#4a5568">{itype}</span>
  </div>
  <div class="d-section">Sheet: <strong>{sheet}</strong></div>
  <table class="cmp-table">
    <tr>
      <th>Rule 1</th>
      <th>Rule 2</th>
    </tr>
    <tr>
      <td class="cmp-gt">{row_display(row1, name1_full)}</td>
      <td class="cmp-rule">{row_display(row2, name2_full)}</td>
    </tr>
  </table>

  <div class="decision-block">
    <div class="decision-lbl">Your Decision</div>
    <div class="opt-row" onclick="selectOpt2('{iid}','r1',this)">
      <input type="radio" name="dec-{iid}" value="r1" id="r1-{iid}">
      <label for="r1-{iid}">Rule 1 is correct — Row {row1}: {name1_full}</label>
    </div>
    <div class="opt-row" onclick="selectOpt2('{iid}','r2',this)">
      <input type="radio" name="dec-{iid}" value="r2" id="r2-{iid}">
      <label for="r2-{iid}">Rule 2 is correct — Row {row2}: {name2_full}</label>
    </div>
    <div class="opt-row" onclick="selectOpt2('{iid}','ind',this)">
      <input type="radio" name="dec-{iid}" value="ind" id="ind-{iid}">
      <label for="ind-{iid}">Industry-dependent</label>
    </div>
    <div class="opt-row" onclick="selectOpt2('{iid}','ctx',this)">
      <input type="radio" name="dec-{iid}" value="ctx" id="ctx-{iid}">
      <label for="ctx-{iid}">Context-dependent (P&amp;L vs B/S)</label>
    </div>
    <div class="opt-row" onclick="selectOpt2('{iid}','other',this)">
      <input type="radio" name="dec-{iid}" value="other" id="other-{iid}">
      <label for="other-{iid}">Other:</label>
    </div>
    <div class="other-inputs" id="other-inputs-{iid}" style="display:none">
      <span>Row</span>
      <input type="number" class="other-num" id="other-num-{iid}" placeholder="e.g. 49"
             oninput="autoFill2('{iid}','other-num-{iid}','other-name-{iid}')">
      <input type="text" class="other-name" id="other-name-{iid}" placeholder="Field name">
    </div>
  </div>

  <div class="extra-body" id="ind-grid-wrap-{iid}" style="display:none">
    <table class="ind-grid">
      <tr><th>Industry</th><th>Row #</th><th>Field Name</th></tr>
      <tr><td>Manufacturing</td><td><input type="number" id="ind-mfg-row-{iid}" oninput="autoFillInd2('{iid}','mfg');saveCard2('{iid}')"></td><td><input type="text" id="ind-mfg-name-{iid}" oninput="saveCard2('{iid}')"></td></tr>
      <tr><td>Trading</td><td><input type="number" id="ind-trd-row-{iid}" oninput="autoFillInd2('{iid}','trd');saveCard2('{iid}')"></td><td><input type="text" id="ind-trd-name-{iid}" oninput="saveCard2('{iid}')"></td></tr>
      <tr><td>Services</td><td><input type="number" id="ind-svc-row-{iid}" oninput="autoFillInd2('{iid}','svc');saveCard2('{iid}')"></td><td><input type="text" id="ind-svc-name-{iid}" oninput="saveCard2('{iid}')"></td></tr>
      <tr><td>Construction</td><td><input type="number" id="ind-con-row-{iid}" oninput="autoFillInd2('{iid}','con');saveCard2('{iid}')"></td><td><input type="text" id="ind-con-name-{iid}" oninput="saveCard2('{iid}')"></td></tr>
    </table>
  </div>
  <div class="extra-body" id="ctx-grid-wrap-{iid}" style="display:none">
    <table class="ind-grid">
      <tr><th>Context</th><th>Row #</th><th>Field Name</th></tr>
      <tr><td>Profit &amp; Loss</td><td><input type="number" id="ctx-pl-row-{iid}" oninput="autoFillCtx2('{iid}','pl');saveCard2('{iid}')"></td><td><input type="text" id="ctx-pl-name-{iid}" oninput="saveCard2('{iid}')"></td></tr>
      <tr><td>Balance Sheet</td><td><input type="number" id="ctx-bs-row-{iid}" oninput="autoFillCtx2('{iid}','bs');saveCard2('{iid}')"></td><td><input type="text" id="ctx-bs-name-{iid}" oninput="saveCard2('{iid}')"></td></tr>
    </table>
  </div>

  <div class="notes-row">
    <label>Notes</label>
    <textarea id="notes-{iid}" rows="2" placeholder="Add reasoning..." oninput="saveCard2('{iid}')"></textarea>
  </div>
  <div class="conf-row">
    <div class="conf-lbl">Confidence</div>
    <div class="conf-opts">
      <label class="conf-opt"><input type="radio" name="conf-{iid}" value="certain" onchange="saveCard2('{iid}')"> Certain</label>
      <label class="conf-opt"><input type="radio" name="conf-{iid}" value="likely" onchange="saveCard2('{iid}')"> Likely</label>
      <label class="conf-opt"><input type="radio" name="conf-{iid}" value="discuss" onchange="saveCard2('{iid}')"> Needs Discussion</label>
    </div>
  </div>
</div>"""

    cross_cards = "".join(cross_card(item, i + 1) for i, item in enumerate(CROSS))
    internal_cards = "".join(internal_card(item, len(CROSS) + i + 1) for i, item in enumerate(INTERNAL))

    all_ids_json = json.dumps(
        [f"cross_{i+1:03d}" for i in range(len(CROSS))] +
        [f"int_{i+1:03d}" for i in range(len(INTERNAL))]
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CMA Golden Rules &mdash; Contradiction Review</title>
<style>
{SHARED_CSS}
</style>
</head>
<body>
<div class="container">

<div class="page-header">
  <h1>CMA Golden Rules &mdash; Contradiction Review</h1>
  <div class="sub">14 cross-source + 21 internal contradictions &mdash; resolve each conflict</div>
</div>

<div class="restore-banner hidden" id="restore-banner">
  <span>&#128190;</span>
  <span class="restore-msg"></span>
  <button class="btn btn-outline" onclick="clearSaved('cma_rule_contradictions_v2',document.getElementById('restore-banner'))">Clear &amp; Restart</button>
</div>

<div class="top-actions">
  <div class="ca-field">
    <label>CA Name</label>
    <input type="text" id="ca-name" placeholder="Your name..." oninput="saveMeta2()">
  </div>
  <div class="ca-field">
    <label>Date</label>
    <input type="text" id="review-date" value="2026-03-27">
  </div>
  <button class="btn btn-orange" onclick="exportJSON('cma_rule_contradictions_v2','Rule_contradictions_responses.json')">Export JSON</button>
</div>

<div class="progress-box">
  <div class="progress-lbl">
    <span id="prog-counter">0 of {total} reviewed</span>
    <span id="prog-pct">0%</span>
  </div>
  <div class="pbar"><div class="pbar-fill" id="prog-bar" style="width:0%"></div></div>
</div>

<div class="summary-cards">
  <div class="s-card"><div class="val">{len(CROSS)}</div><div class="lbl">Cross-Source Contradictions</div></div>
  <div class="s-card"><div class="val">{len(INTERNAL)}</div><div class="lbl">Internal Contradictions</div></div>
  <div class="s-card"><div class="val">{total}</div><div class="lbl">Total to Resolve</div></div>
</div>

<!-- Section A: Cross-source -->
<div class="sec-block">
  <div class="sec-hdr">
    <span class="sec-letter">A</span>
    <span class="sec-title-text">Cross-Source Contradictions &mdash; Source 1 vs CA Answers</span>
    <span class="sec-count">{len(CROSS)} items</span>
    <span class="chevron rot">▼</span>
  </div>
  <div class="sec-qs">{cross_cards}</div>
</div>

<!-- Section B: Internal -->
<div class="sec-block">
  <div class="sec-hdr">
    <span class="sec-letter">B</span>
    <span class="sec-title-text">Internal Contradictions &mdash; Within Same Source</span>
    <span class="sec-count">{len(INTERNAL)} items</span>
    <span class="chevron rot">▼</span>
  </div>
  <div class="sec-qs">{internal_cards}</div>
</div>

</div>

<script>
const ROW_NAMES = {json.dumps(ROW_NAMES)};
const TOTAL = {total};
const STORAGE_KEY = 'cma_rule_contradictions_v2';

{SHARED_JS}

function autoFill2(iid, numId, nameId) {{
  const n = parseInt(document.getElementById(numId).value);
  if (n && ROW_NAMES[n]) document.getElementById(nameId).value = ROW_NAMES[n];
  saveCard2(iid);
}}

function autoFillInd2(iid, ind) {{
  const n = parseInt(document.getElementById('ind-'+ind+'-row-'+iid).value);
  if (n && ROW_NAMES[n]) document.getElementById('ind-'+ind+'-name-'+iid).value = ROW_NAMES[n];
}}

function autoFillCtx2(iid, ctx) {{
  const n = parseInt(document.getElementById('ctx-'+ctx+'-row-'+iid).value);
  if (n && ROW_NAMES[n]) document.getElementById('ctx-'+ctx+'-name-'+iid).value = ROW_NAMES[n];
}}

function selectOpt2(iid, val, row) {{
  document.querySelectorAll('[name="dec-'+iid+'"]').forEach(function(r) {{
    r.closest('.opt-row').classList.remove('sel');
  }});
  const radio = document.getElementById(val+'-'+iid);
  if (radio) {{ radio.checked = true; if(row) row.classList.add('sel'); }}
  // Show/hide sub-grids
  const oi = document.getElementById('other-inputs-'+iid);
  if (oi) oi.style.display = (val === 'other') ? 'flex' : 'none';
  const ig = document.getElementById('ind-grid-wrap-'+iid);
  if (ig) ig.style.display = (val === 'ind') ? 'block' : 'none';
  const cg = document.getElementById('ctx-grid-wrap-'+iid);
  if (cg) cg.style.display = (val === 'ctx') ? 'block' : 'none';
  saveCard2(iid);
}}

function getCardData2(iid) {{
  const decRadio = document.querySelector('[name="dec-'+iid+'"]:checked');
  const confRadio = document.querySelector('[name="conf-'+iid+'"]:checked');
  const data = {{
    item_id: iid,
    decision: decRadio ? decRadio.value : null,
    confidence: confRadio ? confRadio.value : null,
    notes: (document.getElementById('notes-'+iid)||{{}}).value || ''
  }};
  if (data.decision === 'other') {{
    data.selected_row = parseInt((document.getElementById('other-num-'+iid)||{{}}).value)||null;
    data.selected_name = (document.getElementById('other-name-'+iid)||{{}}).value||'';
  }}
  return data;
}}

function saveCard2(iid) {{
  const data = getCardData2(iid);
  saveResponse(STORAGE_KEY, iid, data);
  const card = document.getElementById('card-'+iid);
  if (card && data.decision) card.classList.add('done');
  refreshProgress2();
}}

function refreshProgress2() {{
  const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{{"responses":{{}}}}');
  const reviewed = Object.keys(saved.responses || {{}}).length;
  const pct = Math.round((reviewed/TOTAL)*100);
  document.getElementById('prog-counter').textContent = reviewed + ' of ' + TOTAL + ' reviewed';
  document.getElementById('prog-pct').textContent = pct + '%';
  document.getElementById('prog-bar').style.width = pct + '%';
}}

function saveMeta2() {{
  let saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{{"responses":{{}}}}');
  saved.reviewer = document.getElementById('ca-name').value;
  saved.date = document.getElementById('review-date').value;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(saved));
}}

function restoreAllResponses(key) {{
  const saved = JSON.parse(localStorage.getItem(key) || '{{"responses":{{}}}}');
  if (saved.reviewer) {{ const el = document.getElementById('ca-name'); if(el) el.value = saved.reviewer; }}
  Object.entries(saved.responses || {{}}).forEach(function([iid, data]) {{
    if (data.decision) {{
      const radio = document.getElementById(data.decision+'-'+iid);
      if (radio) {{
        radio.checked = true;
        const row = radio.closest('.opt-row');
        if(row) row.classList.add('sel');
      }}
      selectOpt2(iid, data.decision, null);
      const card = document.getElementById('card-'+iid);
      if (card) card.classList.add('done');
    }}
    if (data.notes) {{ const el = document.getElementById('notes-'+iid); if(el) el.value = data.notes; }}
    if (data.confidence) {{
      const el = document.querySelector('[name="conf-'+iid+'"][value="'+data.confidence+'"]');
      if (el) el.checked = true;
    }}
  }});
  refreshProgress2();
}}

document.addEventListener('DOMContentLoaded', function() {{
  setupSectionToggles();
  checkRestore(STORAGE_KEY, document.getElementById('restore-banner'));
  refreshProgress2();
}});
</script>
</body>
</html>"""
    return html


# ══════════════════════════════════════════════════════════════════════════════
#  DOCUMENT 3 — Golden Rule Violations by Company
# ══════════════════════════════════════════════════════════════════════════════
def build_violations_html():
    # Group disputes by company
    company_disputes = {}
    for d in DISPUTES:
        company_disputes.setdefault(d["company"], []).append(d)

    companies = sorted(company_disputes.keys())

    # Tab headers
    tabs_html = ""
    for i, co in enumerate(companies):
        active = "active" if i == 0 else ""
        n = len(company_disputes[co])
        tabs_html += f'<div class="tab {active}" data-tab="{co}" onclick="showTab(\'{co}\')">{co.replace("_"," ")} <span style="font-size:11px;opacity:.8">({n})</span></div>'

    # Tab content for each company
    tabs_content_html = ""
    for i, co in enumerate(companies):
        active = "active" if i == 0 else ""
        disputes = company_disputes[co]
        stats = BY_COMPANY.get(co, {})
        industry = disputes[0].get("industry_type", "") if disputes else ""
        total_entries = stats.get("total", 0)
        confirmed = stats.get("confirmed", 0)
        dispute_count = stats.get("dispute", 0)

        # Build violation rows
        rows_html = ""
        for j, d in enumerate(disputes):
            row_id = f"{co}_{j}"
            gt_name = ROW_NAMES.get(d["gt_row"], d.get("gt_field", ""))
            gr_name = ROW_NAMES.get(d["golden_rule_row"], d.get("golden_rule_name", ""))
            src = d.get("golden_rule_source", "")
            method = d.get("match_method", "")
            context = d.get("document_context", "")
            ctx_label = "P&L" if context == "pl" else "B/S" if context == "bs" else context

            rows_html += f"""
<tr id="vrow-{row_id}">
  <td style="font-weight:700;color:#1a365d;width:32px">{j+1}</td>
  <td style="max-width:200px"><strong>{d["raw_text"]}</strong><br><span style="font-size:11px;color:#718096">{d.get("section","")}</span></td>
  <td style="font-size:12px">{ctx_label}</td>
  <td style="white-space:nowrap"><span style="font-weight:700">Row {d["gt_row"]}</span><br><span style="font-size:11px;color:#4a5568">{gt_name}</span></td>
  <td style="white-space:nowrap"><span style="font-weight:700">Row {d["golden_rule_row"]}</span><br><span style="font-size:11px;color:#4a5568">{gr_name}</span></td>
  <td style="font-size:11px;color:#718096">{src}<br>{method}</td>
  <td>
    <div class="inline-radio">
      <label><input type="radio" name="v-{row_id}" value="gt" onchange="saveViol('{co}','{row_id}')"> GT</label>
      <label><input type="radio" name="v-{row_id}" value="rule" onchange="saveViol('{co}','{row_id}')"> Rule</label>
      <label><input type="radio" name="v-{row_id}" value="other" onchange="saveViol('{co}','{row_id}')"> Other:</label>
      <input type="number" class="inline-note" id="vother-{row_id}" placeholder="row" style="width:55px"
             oninput="autoFillV('{row_id}');saveViol('{co}','{row_id}')">
    </div>
  </td>
  <td><input type="text" class="inline-note" id="vnote-{row_id}" placeholder="notes..." oninput="saveViol('{co}','{row_id}')"></td>
</tr>"""

        # Company summary
        tabs_content_html += f"""
<div class="tab-content {active}" id="tab-{co}">
  <div style="background:#fff;padding:14px 16px;border-radius:8px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.08)">
    <div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin-bottom:10px">
      <div>
        <div style="font-size:20px;font-weight:700;color:#1a365d">{co.replace("_"," ")}</div>
        <div style="font-size:12px;color:#718096">{industry_pill(industry)} &nbsp; Total entries: {total_entries} &nbsp;|&nbsp; Confirmed: {confirmed} &nbsp;|&nbsp; Disputes: {dispute_count}</div>
      </div>
      <button class="btn btn-outline" onclick="exportCompany('{co}')">Export {co}</button>
    </div>
    <div class="pbar"><div class="pbar-fill" id="vpbar-{co}" style="width:0%"></div></div>
    <div style="font-size:12px;color:#4a5568;margin-top:4px" id="vprog-{co}">0 of {dispute_count} reviewed</div>
  </div>

  <div style="overflow-x:auto">
    <table class="violations-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Item Text / Section</th>
          <th>Context</th>
          <th>GT Used</th>
          <th>Golden Rule Says</th>
          <th>Source</th>
          <th>Decision</th>
          <th>Notes</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>
</div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Golden Rule Violations &mdash; By Company</title>
<style>
{SHARED_CSS}
</style>
</head>
<body>
<div class="container">

<div class="page-header">
  <h1>Golden Rule Violations &mdash; By Company</h1>
  <div class="sub">Which golden rules were not applied in each company&apos;s GT &mdash; resolve per company</div>
</div>

<div class="restore-banner hidden" id="restore-banner">
  <span>&#128190;</span>
  <span class="restore-msg"></span>
  <button class="btn btn-outline" onclick="clearSaved('cma_violations_v2',document.getElementById('restore-banner'))">Clear &amp; Restart</button>
</div>

<div class="top-actions">
  <div class="ca-field">
    <label>CA Name</label>
    <input type="text" id="ca-name" placeholder="Your name..." oninput="saveMeta3()">
  </div>
  <div class="ca-field">
    <label>Date</label>
    <input type="text" id="review-date" value="2026-03-27">
  </div>
  <button class="btn btn-orange" onclick="exportJSON('cma_violations_v2','Violations_responses.json')">Export All JSON</button>
</div>

<div class="tabs">{tabs_html}</div>

{tabs_content_html}

</div>

<script>
const ROW_NAMES = {json.dumps(ROW_NAMES)};
const STORAGE_KEY = 'cma_violations_v2';
const COMPANY_COUNTS = {json.dumps({co: len(disputes) for co, disputes in company_disputes.items()})};

{SHARED_JS}

function showTab(co) {{
  document.querySelectorAll('.tab').forEach(function(t) {{ t.classList.toggle('active', t.dataset.tab === co); }});
  document.querySelectorAll('.tab-content').forEach(function(c) {{ c.classList.toggle('active', c.id === 'tab-'+co); }});
}}

function autoFillV(rowId) {{
  const n = parseInt((document.getElementById('vother-'+rowId)||{{}}).value);
  // No separate name field in inline view — just saves row number
}}

function saveViol(co, rowId) {{
  const radio = document.querySelector('[name="v-'+rowId+'"]:checked');
  const note = (document.getElementById('vnote-'+rowId)||{{}}).value || '';
  const other = (document.getElementById('vother-'+rowId)||{{}}).value || '';
  const data = {{
    item_id: rowId,
    company: co,
    decision: radio ? radio.value : null,
    other_row: radio && radio.value === 'other' ? parseInt(other)||null : null,
    other_row_name: radio && radio.value === 'other' ? (ROW_NAMES[parseInt(other)]||'') : '',
    notes: note
  }};
  saveResponse(STORAGE_KEY, rowId, data);
  // Highlight resolved row
  const row = document.getElementById('vrow-'+rowId);
  if (row && data.decision) row.style.background = '#f0fff4';
  refreshViolProgress(co);
}}

function refreshViolProgress(co) {{
  const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{{"responses":{{}}}}');
  const total = COMPANY_COUNTS[co] || 0;
  // Count responses for this company
  let reviewed = 0;
  Object.values(saved.responses || {{}}).forEach(function(d) {{
    if (d.company === co && d.decision) reviewed++;
  }});
  const pct = total > 0 ? Math.round((reviewed/total)*100) : 0;
  const pb = document.getElementById('vpbar-'+co);
  const pc = document.getElementById('vprog-'+co);
  if (pb) pb.style.width = pct + '%';
  if (pc) pc.textContent = reviewed + ' of ' + total + ' reviewed';
}}

function exportCompany(co) {{
  const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{{"responses":{{}}}}');
  const filtered = {{}};
  Object.entries(saved.responses || {{}}).forEach(function([k, v]) {{
    if (v.company === co) filtered[k] = v;
  }});
  const out = {{ company: co, reviewer: saved.reviewer, responses: filtered }};
  const blob = new Blob([JSON.stringify(out, null, 2)], {{type:'application/json'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'violations_' + co + '.json';
  a.click();
}}

function saveMeta3() {{
  let saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{{"responses":{{}}}}');
  saved.reviewer = document.getElementById('ca-name').value;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(saved));
}}

function restoreAllResponses(key) {{
  const saved = JSON.parse(localStorage.getItem(key) || '{{"responses":{{}}}}');
  if (saved.reviewer) {{ const el = document.getElementById('ca-name'); if(el) el.value = saved.reviewer; }}
  Object.entries(saved.responses || {{}}).forEach(function([rowId, data]) {{
    if (data.decision) {{
      const radio = document.querySelector('[name="v-'+rowId+'"][value="'+data.decision+'"]');
      if (radio) radio.checked = true;
      if (data.decision === 'other' && data.other_row) {{
        const oi = document.getElementById('vother-'+rowId);
        if (oi) oi.value = data.other_row;
      }}
      const row = document.getElementById('vrow-'+rowId);
      if (row) row.style.background = '#f0fff4';
    }}
    if (data.notes) {{ const el = document.getElementById('vnote-'+rowId); if(el) el.value = data.notes; }}
  }});
  // Refresh all company progress bars
  Object.keys(COMPANY_COUNTS).forEach(function(co) {{ refreshViolProgress(co); }});
}}

document.addEventListener('DOMContentLoaded', function() {{
  checkRestore(STORAGE_KEY, document.getElementById('restore-banner'));
}});
</script>
</body>
</html>"""
    return html


# ── Write files ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Building Document 1: GT Disputes Review...")
    doc1 = build_disputes_html()
    out1 = OUT_DIR / "GT_disputes_review.html"
    out1.write_text(doc1, encoding="utf-8")
    print(f"  Written: {out1} ({len(doc1)//1024}KB)")

    print("Building Document 2: Rule Contradictions Review...")
    doc2 = build_contradictions_html()
    out2 = OUT_DIR / "Rule_contradictions_review.html"
    out2.write_text(doc2, encoding="utf-8")
    print(f"  Written: {out2} ({len(doc2)//1024}KB)")

    print("Building Document 3: Golden Rule Violations by Company...")
    doc3 = build_violations_html()
    out3 = OUT_DIR / "Golden_rule_violations_by_company.html"
    out3.write_text(doc3, encoding="utf-8")
    print(f"  Written: {out3} ({len(doc3)//1024}KB)")

    print("\nDone! All 3 documents generated.")
