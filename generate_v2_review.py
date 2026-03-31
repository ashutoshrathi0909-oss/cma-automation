#!/usr/bin/env python
"""
Generate GT Disputes Review v2 HTML files.
"""

import json
import os
import sys
import subprocess
import tempfile
from datetime import datetime, timezone

# ── Paths ────────────────────────────────────────────────────────────────────
BASE = r"C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2"
GT_FILE = os.path.join(BASE, "CMA_Ground_Truth_v1", "validation", "gt_validation_final.json")
RESP_FILE = os.path.join(BASE, "DOCS", "GT_disputes_responses -3.json")
OUT_DIR = os.path.join(BASE, "DOCS", "test-results", "round2")
OUT_V2 = os.path.join(OUT_DIR, "GT_disputes_review_v2.html")
OUT_V2_VIOL = os.path.join(OUT_DIR, "Golden_rule_violations_by_company_v2.html")

os.makedirs(OUT_DIR, exist_ok=True)

# ── Step 1: Load data ─────────────────────────────────────────────────────────
print("Step 1: Loading data...")
with open(GT_FILE, encoding="utf-8") as f:
    gt_data = json.load(f)

raw_disputes = gt_data["disputes"]

# Build disputes dict with _id
disputes = {}
all_ids = []
for i, d in enumerate(raw_disputes):
    iid = "d" + str(i + 1).zfill(3)
    disputes[iid] = dict(d, _id=iid)
    all_ids.append(iid)

with open(RESP_FILE, encoding="utf-8") as f:
    resp_data = json.load(f)

responses = resp_data.get("responses", {})
print(f"  Loaded {len(disputes)} disputes, {len(responses)} existing responses")

# ── Step 2: Add 8 new entries ─────────────────────────────────────────────────
print("Step 2: Adding 8 new entries...")

new_entries = {
    "d006": {
        "item_id": "d006",
        "decision": "gt",
        "confidence": None,
        "notes": "[AUTO-DEDUP] Same pattern as d054 (INPL, rates & taxes, gt=68 rule=49) -> gt",
        "pre_resolved": True,
        "industry_specific": None,
        "context_specific": None,
    },
    "d017": {
        "item_id": "d017",
        "decision": "gt",
        "confidence": None,
        "notes": "[AUTO-DEDUP] Same pattern as d056 (INPL, deferred tax, gt=100 rule=171) -> gt",
        "pre_resolved": True,
        "industry_specific": None,
        "context_specific": None,
    },
    "d122": {
        "item_id": "d122",
        "decision": "gt",
        "confidence": None,
        "notes": "[AUTO-DEDUP] Same pattern as d056 (INPL, deferred tax, gt=100 rule=171) -> gt",
        "pre_resolved": True,
        "industry_specific": None,
        "context_specific": None,
    },
    "d132": {
        "item_id": "d132",
        "decision": "gt",
        "confidence": None,
        "notes": "[AUTO-DEDUP] Same pattern as d026 (Dynamic_Air, rates and taxes, gt=68 rule=49) -> gt",
        "pre_resolved": True,
        "industry_specific": None,
        "context_specific": None,
    },
    "d136": {
        "item_id": "d136",
        "decision": "gt",
        "confidence": None,
        "notes": "[AUTO-DEDUP] Same pattern as d056 (INPL, deferred tax, gt=100 rule=171) -> gt",
        "pre_resolved": True,
        "industry_specific": None,
        "context_specific": None,
    },
    "d172": {
        "item_id": "d172",
        "decision": None,
        "notes": "[DEDUP-PENDING] Same as d167, will inherit answer",
        "pre_resolved": False,
        "dedup_canonical": "d167",
    },
    "d171": {
        "item_id": "d171",
        "decision": None,
        "notes": "[DEDUP-PENDING] Same as d168, will inherit answer",
        "pre_resolved": False,
        "dedup_canonical": "d168",
    },
    "d173": {
        "item_id": "d173",
        "decision": None,
        "notes": "[DEDUP-PENDING] Same as d168, will inherit answer",
        "pre_resolved": False,
        "dedup_canonical": "d168",
    },
}

for iid, entry in new_entries.items():
    responses[iid] = entry

# Update lastSaved and save
resp_data["responses"] = responses
resp_data["lastSaved"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

with open(RESP_FILE, "w", encoding="utf-8") as f:
    json.dump(resp_data, f, indent=2, ensure_ascii=False)

print(f"  Saved {len(responses)} responses to {RESP_FILE}")

# ── Step 3: Compute unanswered items ──────────────────────────────────────────
print("Step 3: Computing unanswered items...")

auto_resolved_ids = {"d006", "d017", "d122", "d132", "d136"}
dedup_pending_ids = {"d171", "d172", "d173"}
special_ids = {"d045", "d100"}

needs_review = []
for iid in all_ids:
    r = responses.get(iid)
    if r is None:
        needs_review.append(iid)
    elif r.get("decision") is None and not r.get("dedup_canonical"):
        needs_review.append(iid)

special_items = [iid for iid in needs_review if responses.get(iid) and responses[iid].get("notes")]

# Per-company breakdown
company_remaining = {}
for iid in needs_review:
    if iid in special_ids:
        continue
    d = disputes.get(iid, {})
    c = d.get("company", "Unknown")
    company_remaining[c] = company_remaining.get(c, 0) + 1

print(f"  Needs review: {len(needs_review)}")
print(f"  Special items (null decision + notes): {len(special_items)}")
for c, n in sorted(company_remaining.items()):
    print(f"    {c}: {n}")

# ── Step 4: Compute resolved items ───────────────────────────────────────────
print("Step 4: Computing resolved items...")

resolved_items = []
for iid in all_ids:
    r = responses.get(iid)
    if r and r.get("decision") is not None and iid not in dedup_pending_ids:
        resolved_items.append(iid)

print(f"  Resolved: {len(resolved_items)}")

# ── Build ROW_NAMES from disputes data ───────────────────────────────────────
row_names = {}
for d in disputes.values():
    if d.get("gt_row") and d.get("gt_field"):
        row_names[d["gt_row"]] = d["gt_field"]
    if d.get("golden_rule_row") and d.get("golden_rule_name"):
        row_names[d["golden_rule_row"]] = d["golden_rule_name"]

# ── Build ITEMS_DATA (unanswered, non-special, non-dedup-pending) ─────────────
items_data = []
for iid in needs_review:
    if iid in special_ids:
        continue
    d = disputes.get(iid, {})
    r = responses.get(iid, {})
    # Check if canonical (dedup_pending) — skip them from main review (handled separately)
    if r and r.get("dedup_canonical"):
        continue
    items_data.append({
        "id": iid,
        "company": d.get("company", ""),
        "raw_text": d.get("raw_text", ""),
        "section": d.get("section", ""),
        "gt_row": d.get("gt_row"),
        "gt_field": d.get("gt_field", ""),
        "golden_rule_row": d.get("golden_rule_row"),
        "golden_rule_name": d.get("golden_rule_name", ""),
        "golden_rule_source": d.get("golden_rule_source", ""),
        "industry_type": d.get("industry_type", ""),
        "document_context": d.get("document_context", ""),
        "agent_reasoning": d.get("agent_reasoning"),
        "fuzzy_score": d.get("fuzzy_score"),
    })

# Also include dedup_pending items in items_data with canonical info
for iid in dedup_pending_ids:
    d = disputes.get(iid, {})
    r = responses.get(iid, {})
    canonical = r.get("dedup_canonical") if r else None
    # Find other pending items that share same canonical
    siblings = [x for x in dedup_pending_ids if responses.get(x, {}).get("dedup_canonical") == canonical and x != iid]
    # We won't show dedup-pending separately - they are handled via autoPropagate
    # But we mark them in items_data for the canonical item
    pass

# Find which canonicals have pending dependents
canonical_to_pending = {}
for iid in dedup_pending_ids:
    r = responses.get(iid, {})
    canonical = r.get("dedup_canonical") if r else None
    if canonical:
        if canonical not in canonical_to_pending:
            canonical_to_pending[canonical] = []
        canonical_to_pending[canonical].append(iid)

# Add canonical info to items_data items
for item in items_data:
    iid = item["id"]
    pending = canonical_to_pending.get(iid, [])
    item["dedup_dependents"] = pending

# Build SPECIAL_DATA
special_data = []
for iid in special_ids:
    if iid in needs_review:
        d = disputes.get(iid, {})
        r = responses.get(iid, {})
        special_data.append({
            "id": iid,
            "company": d.get("company", ""),
            "raw_text": d.get("raw_text", ""),
            "section": d.get("section", ""),
            "gt_row": d.get("gt_row"),
            "gt_field": d.get("gt_field", ""),
            "golden_rule_row": d.get("golden_rule_row"),
            "golden_rule_name": d.get("golden_rule_name", ""),
            "notes": r.get("notes", "") if r else "",
            "industry_type": d.get("industry_type", ""),
            "document_context": d.get("document_context", ""),
        })

# Build RESOLVED_DATA
resolved_data = []
for iid in resolved_items:
    d = disputes.get(iid, {})
    r = responses.get(iid, {})
    resolved_data.append({
        "id": iid,
        "company": d.get("company", ""),
        "raw_text": d.get("raw_text", ""),
        "decision": r.get("decision") if r else None,
        "notes": r.get("notes", "") if r else "",
        "pre_resolved": r.get("pre_resolved", False) if r else False,
    })

# Counts for header
total_resolved_display = len(resolved_items) + len(auto_resolved_ids) + len(dedup_pending_ids)
pct = round(total_resolved_display / 175 * 100)
total_truly_answered = len([iid for iid in all_ids
                             if responses.get(iid) and responses[iid].get("decision") is not None
                             and iid not in dedup_pending_ids])

print(f"  Items data (for review cards): {len(items_data)}")
print(f"  Special data: {len(special_data)}")
print(f"  Resolved data: {len(resolved_data)}")


# ── Step 5: Generate GT_disputes_review_v2.html ───────────────────────────────
print("Step 5: Generating GT_disputes_review_v2.html...")

items_json = json.dumps(items_data, ensure_ascii=False)
resolved_json = json.dumps(resolved_data, ensure_ascii=False)
special_json = json.dumps(special_data, ensure_ascii=False)
row_names_json = json.dumps(row_names, ensure_ascii=False)
canonical_json = json.dumps(canonical_to_pending, ensure_ascii=False)

# Compute unique companies in needs_review (excluding special_ids)
nr_companies = []
seen_c = set()
for iid in needs_review:
    if iid in special_ids:
        continue
    r = responses.get(iid, {})
    if r and r.get("dedup_canonical"):
        continue  # skip dedup-pending from company list (shown under canonical)
    d = disputes.get(iid, {})
    c = d.get("company", "")
    if c and c not in seen_c:
        nr_companies.append(c)
        seen_c.add(c)

needs_review_count_display = len(items_data)

html_v2 = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CMA GT Disputes &mdash; Final Review v2</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f0f4f8;color:#2d3748;font-size:14px;line-height:1.6}}
.container{{max-width:980px;margin:0 auto;padding:16px}}
.page-header{{background:#1a365d;color:#fff;padding:20px 24px;border-radius:8px;margin-bottom:14px}}
.page-header h1{{font-size:22px;font-weight:700;margin-bottom:4px}}
.page-header .sub{{opacity:.8;font-size:13px}}
.ca-bar{{background:#fff;padding:12px 16px;border-radius:8px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.08);display:flex;gap:12px;align-items:flex-end;flex-wrap:wrap}}
.ca-field{{flex:1;min-width:180px}}
.ca-field label{{font-size:12px;font-weight:600;color:#4a5568;display:block;margin-bottom:3px}}
.ca-field input{{width:100%;padding:8px 12px;border:1px solid #cbd5e0;border-radius:6px;font-size:14px}}
.ca-field input:focus{{outline:none;border-color:#1a365d;box-shadow:0 0 0 2px #bee3f8}}
.btn{{padding:8px 16px;border-radius:6px;border:none;cursor:pointer;font-size:13px;font-weight:500;transition:all .15s;white-space:nowrap}}
.btn-navy{{background:#1a365d;color:#fff}}.btn-navy:hover{{background:#2c5282}}
.btn-orange{{background:#e07b39;color:#fff}}.btn-orange:hover{{background:#c96a2a}}
.btn-green{{background:#276749;color:#fff}}.btn-green:hover{{background:#1e4f36}}
.btn-outline{{background:#fff;color:#4a5568;border:1px solid #cbd5e0}}.btn-outline:hover{{border-color:#1a365d;color:#1a365d}}
.progress-box{{background:#fff;padding:12px 16px;border-radius:8px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.progress-lbl{{font-size:13px;color:#4a5568;margin-bottom:5px;display:flex;justify-content:space-between}}
.pbar{{background:#e2e8f0;border-radius:99px;height:12px;overflow:hidden}}
.pbar-fill{{background:#e07b39;height:100%;border-radius:99px;transition:width .3s}}
.stats-row{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}}
.stat-card{{background:#fff;border-radius:8px;padding:12px 16px;box-shadow:0 1px 3px rgba(0,0,0,.08);flex:1;min-width:110px;text-align:center}}
.stat-card .val{{font-size:26px;font-weight:700;color:#1a365d}}
.stat-card .val.orange{{color:#e07b39}}
.stat-card .val.green{{color:#276749}}
.stat-card .val.yellow{{color:#92400e}}
.stat-card .lbl{{font-size:11px;color:#718096;margin-top:2px}}
.special-box{{background:#fef3c7;border:2px solid #f59e0b;border-radius:8px;padding:14px 16px;margin-bottom:12px}}
.special-box h3{{color:#92400e;font-size:15px;margin-bottom:8px}}
.sec-block{{margin-bottom:14px}}
.sec-hdr{{background:#1a365d;color:#fff;padding:11px 16px;border-radius:8px 8px 0 0;cursor:pointer;display:flex;align-items:center;gap:10px;user-select:none}}
.sec-hdr.open-state{{border-radius:8px 8px 0 0}}
.sec-hdr.closed-state{{border-radius:8px}}
.sec-hdr.green{{background:#276749}}
.sec-letter{{background:#e07b39;color:#fff;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;flex-shrink:0}}
.sec-letter.green{{background:#48bb78}}
.sec-title-text{{font-weight:600;flex:1;font-size:15px}}
.sec-count{{font-size:12px;opacity:.8;white-space:nowrap}}
.chevron{{transition:transform .2s;font-size:12px}}
.chevron.rot{{transform:rotate(180deg)}}
.sec-body{{background:#fff;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;overflow:hidden}}
.sec-body.hidden{{display:none}}
.d-card{{padding:16px;border-bottom:1px solid #f0f4f8;transition:background .15s}}
.d-card:last-child{{border-bottom:none}}
.d-card.done{{background:#f0fff4}}
.d-top{{display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap}}
.d-num{{background:#1a365d;color:#fff;padding:2px 9px;border-radius:4px;font-size:11px;font-weight:700;flex-shrink:0}}
.d-raw{{font-size:16px;font-weight:700;color:#1a365d;flex:1}}
.pill{{padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600}}
.pill-mfg{{background:#bee3f8;color:#2b6cb0}}
.pill-trading{{background:#feebc8;color:#c05621}}
.pill-services{{background:#c6f6d5;color:#276749}}
.pill-construction{{background:#fed7d7;color:#9b2c2c}}
.pill-pl{{background:#e9d8fd;color:#553c9a}}
.pill-bs{{background:#b2f5ea;color:#234e52}}
.cmp-table{{width:100%;border-collapse:collapse;margin-bottom:12px;font-size:13px}}
.cmp-table th{{background:#f7fafc;padding:7px 10px;text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;color:#4a5568;letter-spacing:.05em;border:1px solid #e2e8f0}}
.cmp-table td{{padding:8px 10px;border:1px solid #e2e8f0;vertical-align:top}}
.cmp-gt{{background:#fff5f5}}
.cmp-rule{{background:#f0fff4}}
.row-num{{font-weight:700;color:#1a365d}}
.decision-block{{margin-bottom:10px}}
.decision-lbl{{font-size:12px;font-weight:700;color:#4a5568;margin-bottom:5px;text-transform:uppercase;letter-spacing:.04em}}
.opt-row{{display:flex;align-items:center;gap:8px;padding:5px 8px;border-radius:5px;margin-bottom:2px;cursor:pointer;border:1px solid transparent;transition:background .1s}}
.opt-row:hover{{background:#f7fafc}}
.opt-row.sel{{background:#f0fff4;border-color:#9ae6b4}}
.opt-row input[type=radio]{{accent-color:#27ae60;cursor:pointer;flex-shrink:0}}
.opt-row label{{cursor:pointer;flex:1;font-size:13px}}
.other-inputs{{display:flex;gap:6px;align-items:center;flex-wrap:wrap;padding:4px 8px 6px 28px}}
.other-inputs input{{padding:4px 8px;border:1px solid #cbd5e0;border-radius:4px;font-size:13px}}
.other-num{{width:70px}}
.other-name{{flex:1;min-width:150px}}
.conf-row{{margin-bottom:8px}}
.conf-lbl{{font-size:12px;font-weight:700;color:#4a5568;margin-bottom:4px;text-transform:uppercase;letter-spacing:.04em}}
.conf-opts{{display:flex;gap:16px;flex-wrap:wrap}}
.conf-opt{{display:flex;align-items:center;gap:5px;cursor:pointer;font-size:13px}}
.conf-opt input{{accent-color:#1a365d}}
.notes-row{{margin-bottom:8px}}
.notes-row label{{font-size:12px;font-weight:700;color:#4a5568;display:block;margin-bottom:3px;text-transform:uppercase;letter-spacing:.04em}}
.notes-row textarea{{width:100%;padding:6px 10px;border:1px solid #e2e8f0;border-radius:5px;font-size:13px;resize:vertical;min-height:34px;font-family:inherit}}
.notes-row textarea:focus{{outline:none;border-color:#1a365d}}
.ai-toggle{{background:none;border:1px solid #e2e8f0;padding:4px 10px;border-radius:4px;font-size:12px;cursor:pointer;color:#4a5568;display:flex;align-items:center;gap:5px;margin-bottom:6px}}
.ai-toggle:hover{{border-color:#1a365d;color:#1a365d}}
.ai-box{{background:#fef3e2;border-left:3px solid #e67e22;padding:8px 12px;font-size:12px;border-radius:0 4px 4px 0;color:#744210;margin-bottom:10px;display:none}}
.ai-box.open{{display:block}}
.dedup-badge{{background:#7c3aed;color:#fff;padding:3px 9px;border-radius:4px;font-size:11px;font-weight:700}}
.resolved-section .d-card{{background:#f0fff4}}
.resolved-row{{padding:8px 12px;border-bottom:1px solid #c6f6d5;display:flex;gap:8px;align-items:center;flex-wrap:wrap;font-size:13px}}
.resolved-row:last-child{{border-bottom:none}}
.resolved-id{{background:#276749;color:#fff;padding:1px 7px;border-radius:4px;font-size:11px;font-weight:700;flex-shrink:0}}
.resolved-dec{{font-weight:600;font-size:12px}}
.dec-gt{{color:#276749}}
.dec-rule{{color:#2b6cb0}}
.dec-other{{color:#c05621}}
.d-section{{font-size:11px;color:#718096;margin-bottom:6px}}
.raw-text-box{{background:#f7fafc;border-left:3px solid #1a365d;padding:6px 10px;font-size:14px;font-weight:600;margin-bottom:10px;border-radius:0 4px 4px 0}}
</style>
</head>
<body>
<div class="container">

<div class="page-header">
  <h1>CMA GT Disputes &mdash; Final Review (v2)</h1>
  <p class="sub">Resolved: {total_resolved_display} / 175 ({pct}%) &nbsp;|&nbsp; Remaining: {needs_review_count_display} unique questions</p>
</div>

<div class="ca-bar">
  <div class="ca-field">
    <label>CA Name</label>
    <input type="text" id="ca-name" placeholder="Your name..." oninput="saveMeta()">
  </div>
  <div class="ca-field">
    <label>Date</label>
    <input type="date" id="ca-date" oninput="saveMeta()">
  </div>
  <button class="btn btn-navy" onclick="importData()">&#8593; Import</button>
  <button class="btn btn-orange" onclick="exportData()">&#8595; Export JSON</button>
</div>

<div class="progress-box">
  <div class="progress-lbl">
    <span>Overall Progress</span>
    <span id="prog-label">0 / {needs_review_count_display} reviewed</span>
  </div>
  <div class="pbar"><div class="pbar-fill" id="prog-bar" style="width:0%"></div></div>
</div>

<div class="stats-row">
  <div class="stat-card"><div class="val orange" id="stat-remaining">{needs_review_count_display}</div><div class="lbl">Remaining</div></div>
  <div class="stat-card"><div class="val green">5</div><div class="lbl">Auto-Resolved</div></div>
  <div class="stat-card"><div class="val" style="color:#7c3aed">3</div><div class="lbl">Pending-Dedup</div></div>
  <div class="stat-card"><div class="val green">{len(resolved_items)}</div><div class="lbl">Total Resolved</div></div>
</div>

<div id="special-section" style="display:none" class="special-box">
  <h3>&#9888; Items needing clarification (notes exist, no decision selected)</h3>
  <div id="special-cards"></div>
</div>

<div id="sections-container"></div>

<div class="sec-block" id="resolved-block">
  <div class="sec-hdr green closed-state" onclick="toggleSection('resolved-body','resolved-chev')">
    <div class="sec-letter green">&#10003;</div>
    <div class="sec-title-text">Already Resolved ({len(resolved_items)} items)</div>
    <span class="chevron" id="resolved-chev">&#9660;</span>
  </div>
  <div class="sec-body hidden" id="resolved-body">
    <div id="resolved-list"></div>
  </div>
</div>

</div><!-- /container -->

<script>
const ITEMS_DATA = {items_json};
const RESOLVED_DATA = {resolved_json};
const SPECIAL_DATA = {special_json};
const ROW_NAMES = {row_names_json};
const DEDUP_MAP = {canonical_json};
const LS_KEY = "gt_disputes_v2_responses";
const TOTAL_REVIEW = {needs_review_count_display};

let saved = {{}};

function loadSaved() {{
  try {{
    const s = localStorage.getItem(LS_KEY);
    if (s) saved = JSON.parse(s);
  }} catch(e) {{}}
  // restore meta
  try {{
    const m = localStorage.getItem(LS_KEY + "_meta");
    if (m) {{
      const meta = JSON.parse(m);
      if (meta.name) document.getElementById("ca-name").value = meta.name;
      if (meta.date) document.getElementById("ca-date").value = meta.date;
    }}
  }} catch(e) {{}}
}}

function saveMeta() {{
  const meta = {{
    name: document.getElementById("ca-name").value,
    date: document.getElementById("ca-date").value
  }};
  localStorage.setItem(LS_KEY + "_meta", JSON.stringify(meta));
}}

function saveCard(iid) {{
  const card = document.getElementById("card-" + iid);
  if (!card) return;
  const radios = card.querySelectorAll('input[type=radio][name="dec-' + iid + '"]');
  let decision = null;
  radios.forEach(function(r) {{ if (r.checked) decision = r.value; }});
  const confRadios = card.querySelectorAll('input[type=radio][name="conf-' + iid + '"]');
  let confidence = null;
  confRadios.forEach(function(r) {{ if (r.checked) confidence = r.value; }});
  const notesEl = document.getElementById("notes-" + iid);
  const notes = notesEl ? notesEl.value : "";
  const otherNumEl = document.getElementById("other-num-" + iid);
  const otherNum = otherNumEl ? otherNumEl.value : "";
  const entry = {{ decision: decision, confidence: confidence, notes: notes, other_row: otherNum }};
  saved[iid] = entry;
  localStorage.setItem(LS_KEY, JSON.stringify(saved));
  // Update card style
  if (decision) {{
    card.classList.add("done");
  }} else {{
    card.classList.remove("done");
  }}
  updateProgress();
  if (decision) autoPropagate(iid, decision, confidence, notes);
}}

function autoPropagate(iid, decision, confidence, notes) {{
  const deps = DEDUP_MAP[iid] || [];
  deps.forEach(function(dep) {{
    saved[dep] = {{ decision: decision, confidence: confidence, notes: "[DEDUP-AUTO] Copied from " + iid + ": " + notes }};
    localStorage.setItem(LS_KEY, JSON.stringify(saved));
  }});
  if (deps.length > 0) {{
    const msg = document.getElementById("dedup-msg-" + iid);
    if (msg) msg.textContent = "&#10003; Auto-applied to " + deps.join(", ");
  }}
}}

function updateProgress() {{
  let answered = 0;
  ITEMS_DATA.forEach(function(d) {{
    if (saved[d.id] && saved[d.id].decision) answered++;
  }});
  const pct = TOTAL_REVIEW > 0 ? Math.round(answered / TOTAL_REVIEW * 100) : 0;
  document.getElementById("prog-bar").style.width = pct + "%";
  document.getElementById("prog-label").textContent = answered + " / " + TOTAL_REVIEW + " reviewed";
  document.getElementById("stat-remaining").textContent = (TOTAL_REVIEW - answered);
}}

function toggleSection(bodyId, chevId) {{
  const body = document.getElementById(bodyId);
  const chev = document.getElementById(chevId);
  if (body.classList.contains("hidden")) {{
    body.classList.remove("hidden");
    if (chev) chev.classList.add("rot");
  }} else {{
    body.classList.add("hidden");
    if (chev) chev.classList.remove("rot");
  }}
}}

function toggleAI(iid) {{
  const box = document.getElementById("ai-" + iid);
  if (box) box.classList.toggle("open");
}}

function pillClass(industry) {{
  if (!industry) return "pill";
  const lc = industry.toLowerCase();
  if (lc === "manufacturing") return "pill pill-mfg";
  if (lc === "trading") return "pill pill-trading";
  if (lc === "services") return "pill pill-services";
  if (lc === "construction") return "pill pill-construction";
  return "pill";
}}

function ctxPill(ctx) {{
  if (!ctx) return "";
  return ctx.toLowerCase() === "pl" ? '<span class="pill pill-pl">P&amp;L</span>' : '<span class="pill pill-bs">BS</span>';
}}

function esc(s) {{
  if (!s) return "";
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}}

function buildSpecialCard(d) {{
  return '<div class="d-card" id="card-' + d.id + '">' +
    '<div class="d-top">' +
      '<span class="d-num">' + d.id + '</span>' +
      '<span class="d-raw">' + esc(d.raw_text) + '</span>' +
      '<span class="' + pillClass(d.industry_type) + '">' + esc(d.industry_type) + '</span>' +
      ctxPill(d.document_context) +
    '</div>' +
    '<div class="d-section">' + esc(d.company) + ' &bull; ' + esc(d.section) + '</div>' +
    '<div style="background:#fef9c3;border-left:3px solid #f59e0b;padding:8px 12px;margin-bottom:10px;border-radius:0 4px 4px 0;font-size:13px;color:#92400e"><strong>Note:</strong> ' + esc(d.notes) + '</div>' +
    '<table class="cmp-table"><thead><tr><th></th><th>Row</th><th>Field Name</th></tr></thead><tbody>' +
      '<tr class="cmp-gt"><td style="font-weight:700;color:#c05621">GT says</td><td class="row-num">' + (d.gt_row || '') + '</td><td>' + esc(d.gt_field) + '</td></tr>' +
      '<tr class="cmp-rule"><td style="font-weight:700;color:#276749">Rule says</td><td class="row-num">' + (d.golden_rule_row || '') + '</td><td>' + esc(d.golden_rule_name) + '</td></tr>' +
    '</tbody></table>' +
    '<div class="decision-block">' +
      '<div class="decision-lbl">Your Decision</div>' +
      '<div class="opt-row" id="opt-gt-' + d.id + '" onclick="selectOpt(&apos;' + d.id + '&apos;,&apos;gt&apos;)">' +
        '<input type="radio" name="dec-' + d.id + '" value="gt" id="radio-gt-' + d.id + '"> ' +
        '<label for="radio-gt-' + d.id + '">GT Correct (row ' + (d.gt_row || '') + ')</label>' +
      '</div>' +
      '<div class="opt-row" id="opt-rule-' + d.id + '" onclick="selectOpt(&apos;' + d.id + '&apos;,&apos;rule&apos;)">' +
        '<input type="radio" name="dec-' + d.id + '" value="rule" id="radio-rule-' + d.id + '"> ' +
        '<label for="radio-rule-' + d.id + '">Rule Correct (row ' + (d.golden_rule_row || '') + ')</label>' +
      '</div>' +
      '<div class="opt-row" id="opt-other-' + d.id + '" onclick="selectOpt(&apos;' + d.id + '&apos;,&apos;other&apos;)">' +
        '<input type="radio" name="dec-' + d.id + '" value="other" id="radio-other-' + d.id + '"> ' +
        '<label for="radio-other-' + d.id + '">Other &rarr;</label>' +
      '</div>' +
      '<div class="other-inputs" id="other-inputs-' + d.id + '" style="display:none">' +
        '<input type="number" class="other-num" id="other-num-' + d.id + '" placeholder="Row#" oninput="saveCard(&apos;' + d.id + '&apos;)">' +
      '</div>' +
    '</div>' +
    '<div class="notes-row"><label>Notes</label><textarea id="notes-' + d.id + '" oninput="saveCard(&apos;' + d.id + '&apos;)" placeholder="Additional context..."></textarea></div>' +
    '<div id="dedup-msg-' + d.id + '" style="font-size:12px;color:#276749;margin-top:4px"></div>' +
  '</div>';
}}

function buildCard(d) {{
  const sv = saved[d.id] || {{}};
  const isDone = sv.decision ? true : false;
  const doneClass = isDone ? " done" : "";
  const dedupBadge = d.dedup_dependents && d.dedup_dependents.length > 0
    ? '<span class="dedup-badge">&#9889; Your answer auto-applies to: ' + d.dedup_dependents.join(", ") + '</span>'
    : "";
  const aiSection = d.agent_reasoning
    ? '<button class="ai-toggle" onclick="toggleAI(&apos;' + d.id + '&apos;)">&#129302; Agent reasoning &#9660;</button>' +
      '<div class="ai-box" id="ai-' + d.id + '">' + esc(d.agent_reasoning) + '</div>'
    : "";
  return '<div class="d-card' + doneClass + '" id="card-' + d.id + '">' +
    '<div class="d-top">' +
      '<span class="d-num">' + d.id + '</span>' +
      '<span class="d-raw">' + esc(d.raw_text) + '</span>' +
      '<span class="' + pillClass(d.industry_type) + '">' + esc(d.industry_type) + '</span>' +
      ctxPill(d.document_context) +
      dedupBadge +
    '</div>' +
    '<div class="d-section">' + esc(d.section) + '</div>' +
    '<div class="raw-text-box">' + esc(d.raw_text) + '</div>' +
    '<table class="cmp-table"><thead><tr><th></th><th>Row</th><th>Field Name</th></tr></thead><tbody>' +
      '<tr class="cmp-gt"><td style="font-weight:700;color:#c05621">GT says</td><td class="row-num">' + (d.gt_row || '') + '</td><td>' + esc(d.gt_field) + '</td></tr>' +
      '<tr class="cmp-rule"><td style="font-weight:700;color:#276749">Rule says</td><td class="row-num">' + (d.golden_rule_row || '') + '</td><td>' + esc(d.golden_rule_name) + '</td></tr>' +
    '</tbody></table>' +
    aiSection +
    '<div class="decision-block">' +
      '<div class="decision-lbl">Your Decision</div>' +
      '<div class="opt-row" id="opt-gt-' + d.id + '" onclick="selectOpt(&apos;' + d.id + '&apos;,&apos;gt&apos;)">' +
        '<input type="radio" name="dec-' + d.id + '" value="gt" id="radio-gt-' + d.id + '"' + (sv.decision === "gt" ? " checked" : "") + '> ' +
        '<label for="radio-gt-' + d.id + '">&#10003; GT Correct &mdash; row ' + (d.gt_row || '') + ' (' + esc(d.gt_field) + ')</label>' +
      '</div>' +
      '<div class="opt-row" id="opt-rule-' + d.id + '" onclick="selectOpt(&apos;' + d.id + '&apos;,&apos;rule&apos;)">' +
        '<input type="radio" name="dec-' + d.id + '" value="rule" id="radio-rule-' + d.id + '"' + (sv.decision === "rule" ? " checked" : "") + '> ' +
        '<label for="radio-rule-' + d.id + '">&#10006; Rule Correct &mdash; row ' + (d.golden_rule_row || '') + ' (' + esc(d.golden_rule_name) + ')</label>' +
      '</div>' +
      '<div class="opt-row" id="opt-other-' + d.id + '" onclick="selectOpt(&apos;' + d.id + '&apos;,&apos;other&apos;)">' +
        '<input type="radio" name="dec-' + d.id + '" value="other" id="radio-other-' + d.id + '"' + (sv.decision === "other" ? " checked" : "") + '> ' +
        '<label for="radio-other-' + d.id + '">Other row &rarr; enter row number</label>' +
      '</div>' +
      '<div class="other-inputs" id="other-inputs-' + d.id + '" style="' + (sv.decision === "other" ? "" : "display:none") + '">' +
        '<input type="number" class="other-num" id="other-num-' + d.id + '" placeholder="Row#" value="' + (sv.other_row || '') + '" oninput="saveCard(&apos;' + d.id + '&apos;)">' +
      '</div>' +
    '</div>' +
    '<div class="conf-row">' +
      '<div class="conf-lbl">Confidence</div>' +
      '<div class="conf-opts">' +
        '<label class="conf-opt"><input type="radio" name="conf-' + d.id + '" value="certain" onchange="saveCard(&apos;' + d.id + '&apos;)"' + (sv.confidence === "certain" ? " checked" : "") + '> Certain</label>' +
        '<label class="conf-opt"><input type="radio" name="conf-' + d.id + '" value="likely" onchange="saveCard(&apos;' + d.id + '&apos;)"' + (sv.confidence === "likely" ? " checked" : "") + '> Likely</label>' +
        '<label class="conf-opt"><input type="radio" name="conf-' + d.id + '" value="unsure" onchange="saveCard(&apos;' + d.id + '&apos;)"' + (sv.confidence === "unsure" ? " checked" : "") + '> Unsure</label>' +
      '</div>' +
    '</div>' +
    '<div class="notes-row">' +
      '<label>Notes</label>' +
      '<textarea id="notes-' + d.id + '" oninput="saveCard(&apos;' + d.id + '&apos;)" placeholder="Any context or rule clarification...">' + esc(sv.notes || '') + '</textarea>' +
    '</div>' +
    '<div id="dedup-msg-' + d.id + '" style="font-size:12px;color:#276749;margin-top:4px"></div>' +
  '</div>';
}}

function selectOpt(iid, val) {{
  document.getElementById("radio-" + val + "-" + iid).checked = true;
  const otherInputs = document.getElementById("other-inputs-" + iid);
  if (otherInputs) {{
    otherInputs.style.display = val === "other" ? "flex" : "none";
  }}
  ["gt","rule","other"].forEach(function(v) {{
    const row = document.getElementById("opt-" + v + "-" + iid);
    if (row) row.classList.toggle("sel", v === val);
  }});
  saveCard(iid);
}}

function renderSections() {{
  // Group items by company
  const byCompany = {{}};
  ITEMS_DATA.forEach(function(d) {{
    if (!byCompany[d.company]) byCompany[d.company] = [];
    byCompany[d.company].push(d);
  }});
  const container = document.getElementById("sections-container");
  const companies = Object.keys(byCompany).sort();
  companies.forEach(function(co, idx) {{
    const items = byCompany[co];
    const bodyId = "sec-body-" + co;
    const chevId = "sec-chev-" + co;
    const letter = co.charAt(0).toUpperCase();
    const block = document.createElement("div");
    block.className = "sec-block";
    const hdrHtml = '<div class="sec-hdr open-state" onclick="toggleSection(&apos;' + bodyId + '&apos;,&apos;' + chevId + '&apos;)">' +
      '<div class="sec-letter">' + letter + '</div>' +
      '<div class="sec-title-text">' + esc(co.replace(/_/g," ")) + '</div>' +
      '<span class="sec-count" id="sec-count-' + co + '">' + items.length + ' remaining</span>' +
      '<span class="chevron rot" id="' + chevId + '">&#9660;</span>' +
    '</div>';
    const bodyHtml = '<div class="sec-body" id="' + bodyId + '">' +
      items.map(function(d) {{ return buildCard(d); }}).join("") +
    '</div>';
    block.innerHTML = hdrHtml + bodyHtml;
    container.appendChild(block);
    // Restore sel state
    items.forEach(function(d) {{
      const sv = saved[d.id] || {{}};
      if (sv.decision) {{
        const row = document.getElementById("opt-" + sv.decision + "-" + d.id);
        if (row) row.classList.add("sel");
        const card = document.getElementById("card-" + d.id);
        if (card) card.classList.add("done");
      }}
    }});
  }});
}}

function renderSpecial() {{
  if (!SPECIAL_DATA || SPECIAL_DATA.length === 0) return;
  const box = document.getElementById("special-section");
  const container = document.getElementById("special-cards");
  box.style.display = "block";
  container.innerHTML = SPECIAL_DATA.map(function(d) {{ return buildSpecialCard(d); }}).join("");
  SPECIAL_DATA.forEach(function(d) {{
    const sv = saved[d.id] || {{}};
    if (sv.decision) {{
      const row = document.getElementById("opt-" + sv.decision + "-" + d.id);
      if (row) row.classList.add("sel");
      const card = document.getElementById("card-" + d.id);
      if (card) card.classList.add("done");
    }}
  }});
}}

function renderResolved() {{
  const list = document.getElementById("resolved-list");
  if (!list) return;
  list.innerHTML = RESOLVED_DATA.map(function(r) {{
    const decClass = r.decision === "gt" ? "dec-gt" : r.decision === "rule" ? "dec-rule" : "dec-other";
    const badge = r.pre_resolved ? '<span style="background:#bee3f8;color:#2b6cb0;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:700;margin-left:4px">AUTO</span>' : "";
    return '<div class="resolved-row">' +
      '<span class="resolved-id">' + r.id + '</span>' +
      '<span style="font-size:12px;color:#4a5568;flex-shrink:0">' + esc(r.company) + '</span>' +
      '<span style="flex:1;font-size:13px">' + esc(r.raw_text) + '</span>' +
      '<span class="resolved-dec ' + decClass + '">' + (r.decision || '').toUpperCase() + badge + '</span>' +
      (r.notes ? '<span style="font-size:11px;color:#718096;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + esc(r.notes) + '</span>' : '') +
    '</div>';
  }}).join("");
}}

function exportData() {{
  const name = document.getElementById("ca-name").value || "CA";
  const date = document.getElementById("ca-date").value || new Date().toISOString().split("T")[0];
  const out = {{ reviewer: name, date: date, responses: saved, exported_at: new Date().toISOString() }};
  const blob = new Blob([JSON.stringify(out, null, 2)], {{type:"application/json"}});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "GT_disputes_v2_responses.json";
  a.click();
}}

function importData() {{
  const input = document.createElement("input");
  input.type = "file";
  input.accept = ".json";
  input.onchange = function(e) {{
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(ev) {{
      try {{
        const data = JSON.parse(ev.target.result);
        if (data.responses) {{
          saved = data.responses;
          localStorage.setItem(LS_KEY, JSON.stringify(saved));
          alert("Imported " + Object.keys(saved).length + " responses. Refreshing...");
          location.reload();
        }}
      }} catch(err) {{
        alert("Error parsing JSON: " + err.message);
      }}
    }};
    reader.readAsText(file);
  }};
  input.click();
}}

// Init
loadSaved();
renderSpecial();
renderSections();
renderResolved();
updateProgress();
</script>
</body>
</html>"""

with open(OUT_V2, "w", encoding="utf-8") as f:
    f.write(html_v2)

size_v2 = os.path.getsize(OUT_V2)
print(f"  Written: {OUT_V2} ({size_v2 // 1024} KB)")


# ── Step 6: Generate Golden_rule_violations_by_company_v2.html ─────────────────
print("Step 6: Generating Golden_rule_violations_by_company_v2.html...")

# Build per-company data
companies_order = ["BCIPL", "Dynamic_Air", "INPL", "Kurunji_Retail", "Mehta_Computer", "MSL", "SLIPL", "SR_Papers", "SSSS"]

# needs_review set for quick lookup (excluding special and dedup-pending)
nr_set = set()
for iid in needs_review:
    if iid in special_ids:
        continue
    r = responses.get(iid, {})
    if r and r.get("dedup_canonical"):
        continue
    nr_set.add(iid)

# also include specials in company view
for iid in special_ids:
    if iid in needs_review:
        nr_set.add(iid)

company_disputes = {}
company_resolved = {}
for co in companies_order:
    company_disputes[co] = []
    company_resolved[co] = []

for iid in all_ids:
    d = disputes.get(iid, {})
    co = d.get("company", "")
    if co not in companies_order:
        continue
    r = responses.get(iid)
    if iid in dedup_pending_ids:
        continue  # skip dedup-pending from company view
    if iid in nr_set:
        company_disputes[co].append(iid)
    elif r and r.get("decision") is not None:
        company_resolved[co].append(iid)
    elif iid in auto_resolved_ids:
        company_resolved[co].append(iid)

def make_company_label(co):
    return co.replace("_", " ")

def pill_html(industry, ctx):
    p = ""
    lc = (industry or "").lower()
    if lc == "manufacturing":
        p = '<span class="pill pill-mfg">Mfg</span>'
    elif lc == "trading":
        p = '<span class="pill pill-trading">Trading</span>'
    elif lc == "services":
        p = '<span class="pill pill-svc">Services</span>'
    elif lc == "construction":
        p = '<span class="pill pill-con">Construction</span>'
    c = ""
    if ctx:
        if ctx.lower() == "pl":
            c = '<span class="pill pill-pl">P&L</span>'
        else:
            c = '<span class="pill pill-bs">BS</span>'
    return p + " " + c

def make_tab_content(co):
    pending = company_disputes[co]
    resolved_co = company_resolved[co]
    total_co = len(pending) + len(resolved_co)
    lines = []
    lines.append(f'<div class="tab-content" id="tab-{co}">')
    lines.append(f'<div class="co-header">')
    lines.append(f'  <div style="font-size:20px;font-weight:700;color:#1a365d">{make_company_label(co)}</div>')
    lines.append(f'  <div style="font-size:12px;color:#718096">Total disputes: {total_co} &nbsp;|&nbsp; Resolved: <span style="color:#276749;font-weight:600">{len(resolved_co)}</span> &nbsp;|&nbsp; Remaining: <span style="color:#e07b39;font-weight:600">{len(pending)}</span></div>')
    lines.append(f'  <div class="pbar" style="margin-top:8px"><div class="pbar-fill" style="width:{round(len(resolved_co)/total_co*100) if total_co else 0}%"></div></div>')
    lines.append(f'</div>')

    if pending:
        lines.append('<table class="vtable"><thead><tr><th>#</th><th>Item / Section</th><th>Context</th><th>GT Row</th><th>Rule Row</th><th>Decision</th><th>Notes</th></tr></thead><tbody>')
        for idx, iid in enumerate(pending):
            d = disputes.get(iid, {})
            r = responses.get(iid, {}) or {}
            note = r.get("notes", "")
            lines.append(f'<tr id="vr2-{iid}">')
            lines.append(f'<td style="font-weight:700;color:#1a365d;width:30px">{idx+1}</td>')
            lines.append(f'<td style="max-width:200px"><strong>{d.get("raw_text","")}</strong><br><span style="font-size:11px;color:#718096">{d.get("section","")}</span></td>')
            lines.append(f'<td>{pill_html(d.get("industry_type",""), d.get("document_context",""))}</td>')
            lines.append(f'<td style="white-space:nowrap"><span style="font-weight:700">Row {d.get("gt_row","")}</span><br><span style="font-size:11px;color:#4a5568">{d.get("gt_field","")}</span></td>')
            lines.append(f'<td style="white-space:nowrap"><span style="font-weight:700">Row {d.get("golden_rule_row","")}</span><br><span style="font-size:11px;color:#4a5568">{d.get("golden_rule_name","")}</span></td>')
            lines.append(f'<td><div class="iradio">')
            lines.append(f'  <label><input type="radio" name="v2-{iid}" value="gt" onchange="saveV2(&apos;{iid}&apos;)"> GT</label>')
            lines.append(f'  <label><input type="radio" name="v2-{iid}" value="rule" onchange="saveV2(&apos;{iid}&apos;)"> Rule</label>')
            lines.append(f'  <label><input type="radio" name="v2-{iid}" value="other" onchange="saveV2(&apos;{iid}&apos;)"> Other:</label>')
            lines.append(f'  <input type="number" id="v2-other-{iid}" class="other-num" placeholder="Row#" oninput="saveV2(&apos;{iid}&apos;)" style="width:60px">')
            lines.append(f'</div></td>')
            lines.append(f'<td><input class="inline-note" type="text" id="v2-note-{iid}" value="{note[:40] if note else ""}" oninput="saveV2(&apos;{iid}&apos;)" placeholder="notes..."></td>')
            lines.append('</tr>')
        lines.append('</tbody></table>')
    else:
        lines.append('<div style="padding:16px;color:#276749;font-weight:600">&#10003; All items resolved for this company!</div>')

    if resolved_co:
        lines.append(f'<div class="sec-block" style="margin-top:12px">')
        lines.append(f'<div class="sec-hdr green closed-state" onclick="toggleSec2(&apos;res2-{co}&apos;,&apos;rchev2-{co}&apos;)">')
        lines.append(f'  <div class="sec-letter green">&#10003;</div>')
        lines.append(f'  <div class="sec-title-text">Resolved ({len(resolved_co)} items)</div>')
        lines.append(f'  <span class="chevron" id="rchev2-{co}">&#9660;</span>')
        lines.append(f'</div>')
        lines.append(f'<div class="sec-body hidden" id="res2-{co}">')
        for iid in resolved_co:
            d = disputes.get(iid, {})
            r = responses.get(iid, {}) or {}
            dec = (r.get("decision") or "").upper()
            dec_color = "#276749" if dec == "GT" else "#2b6cb0" if dec == "RULE" else "#c05621"
            auto_badge = ' <span style="background:#bee3f8;color:#2b6cb0;padding:1px 5px;border-radius:3px;font-size:10px;font-weight:700">AUTO</span>' if r.get("pre_resolved") else ""
            lines.append(f'<div class="resolved-row">')
            lines.append(f'  <span class="resolved-id">{iid}</span>')
            lines.append(f'  <span style="flex:1;font-size:13px">{d.get("raw_text","")}</span>')
            lines.append(f'  <span style="font-weight:700;color:{dec_color};font-size:12px">{dec}{auto_badge}</span>')
            if r.get("notes"):
                notes_val = r.get("notes", "")
                lines.append(f'  <span style="font-size:11px;color:#718096;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="{notes_val}">{notes_val[:50]}</span>')
            lines.append('</div>')
        lines.append('</div></div>')

    lines.append('</div>')  # /tab-content
    return "\n".join(lines)

# Build tabs
tab_buttons = ""
for i, co in enumerate(companies_order):
    pending_count = len(company_disputes[co])
    active_class = " active" if i == 0 else ""
    label = make_company_label(co)
    tab_buttons += f'<div class="tab{active_class}" data-tab="{co}" onclick="showTab2(&apos;{co}&apos;)">{label} <span style="font-size:11px;opacity:.8">({pending_count}&#9744;)</span></div>'

tab_contents = "\n".join(make_tab_content(co) for co in companies_order)
# Set first tab active
tab_contents = tab_contents.replace(f'<div class="tab-content" id="tab-{companies_order[0]}">', f'<div class="tab-content active" id="tab-{companies_order[0]}">', 1)

total_remaining_v2 = sum(len(company_disputes[co]) for co in companies_order)
total_resolved_v2 = sum(len(company_resolved[co]) for co in companies_order)

html_viol = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Golden Rule Violations &mdash; By Company v2</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f0f4f8;color:#2d3748;font-size:14px;line-height:1.6}}
.container{{max-width:1060px;margin:0 auto;padding:16px}}
.page-header{{background:#1a365d;color:#fff;padding:20px 24px;border-radius:8px;margin-bottom:14px}}
.page-header h1{{font-size:22px;font-weight:700;margin-bottom:4px}}
.page-header .sub{{opacity:.75;font-size:13px}}
.top-actions{{display:flex;gap:10px;align-items:center;margin-bottom:12px;flex-wrap:wrap}}
.ca-field{{flex:1;min-width:200px}}
.ca-field label{{font-size:12px;font-weight:600;color:#4a5568;display:block;margin-bottom:3px}}
.ca-field input{{width:100%;padding:8px 12px;border:1px solid #cbd5e0;border-radius:6px;font-size:14px}}
.btn{{padding:8px 16px;border-radius:6px;border:none;cursor:pointer;font-size:13px;font-weight:500;transition:all .15s}}
.btn-orange{{background:#e07b39;color:#fff}}.btn-orange:hover{{background:#c96a2a}}
.btn-navy{{background:#1a365d;color:#fff}}.btn-navy:hover{{background:#2c5282}}
.btn-outline{{background:#fff;color:#4a5568;border:1px solid #cbd5e0}}.btn-outline:hover{{border-color:#1a365d;color:#1a365d}}
.pbar{{background:#e2e8f0;border-radius:99px;height:8px;overflow:hidden}}
.pbar-fill{{background:#e07b39;height:100%;border-radius:99px;transition:width .3s}}
.tabs{{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:12px}}
.tab{{padding:6px 12px;border-radius:6px 6px 0 0;font-size:13px;font-weight:500;cursor:pointer;border:1px solid #e2e8f0;background:#f7fafc;color:#4a5568;transition:all .15s;border-bottom:none}}
.tab.active{{background:#1a365d;color:#fff;border-color:#1a365d}}
.tab-content{{display:none}}
.tab-content.active{{display:block}}
.co-header{{background:#fff;padding:14px 16px;border-radius:8px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.vtable{{width:100%;border-collapse:collapse;font-size:13px;margin-bottom:12px}}
.vtable th{{background:#1a365d;color:#fff;padding:8px 10px;text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.04em}}
.vtable td{{padding:8px 10px;border-bottom:1px solid #e2e8f0;vertical-align:middle}}
.vtable tr:hover td{{background:#f7fafc}}
.iradio{{display:flex;align-items:center;gap:6px;flex-wrap:wrap}}
.iradio input[type=radio]{{accent-color:#1a365d}}
.iradio label{{display:flex;align-items:center;gap:3px;font-size:12px;cursor:pointer}}
.other-num{{padding:3px 6px;border:1px solid #cbd5e0;border-radius:3px;font-size:12px}}
.inline-note{{padding:3px 6px;border:1px solid #cbd5e0;border-radius:3px;font-size:12px;width:120px}}
.pill{{padding:1px 6px;border-radius:4px;font-size:11px;font-weight:600}}
.pill-mfg{{background:#bee3f8;color:#2b6cb0}}
.pill-trading{{background:#feebc8;color:#c05621}}
.pill-svc{{background:#c6f6d5;color:#276749}}
.pill-con{{background:#fed7d7;color:#9b2c2c}}
.pill-pl{{background:#e9d8fd;color:#553c9a}}
.pill-bs{{background:#b2f5ea;color:#234e52}}
.sec-block{{margin-bottom:12px}}
.sec-hdr{{background:#1a365d;color:#fff;padding:10px 16px;border-radius:8px 8px 0 0;cursor:pointer;display:flex;align-items:center;gap:10px;user-select:none}}
.sec-hdr.closed-state{{border-radius:8px}}
.sec-hdr.green{{background:#276749}}
.sec-letter{{background:#e07b39;color:#fff;width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;flex-shrink:0}}
.sec-letter.green{{background:#48bb78}}
.sec-title-text{{font-weight:600;flex:1}}
.chevron{{transition:transform .2s;font-size:12px}}
.chevron.rot{{transform:rotate(180deg)}}
.sec-body{{background:#fff;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;overflow:hidden}}
.sec-body.hidden{{display:none}}
.resolved-row{{padding:8px 12px;border-bottom:1px solid #c6f6d5;display:flex;gap:8px;align-items:center;flex-wrap:wrap;font-size:13px}}
.resolved-row:last-child{{border-bottom:none}}
.resolved-id{{background:#276749;color:#fff;padding:1px 7px;border-radius:4px;font-size:11px;font-weight:700;flex-shrink:0}}
</style>
</head>
<body>
<div class="container">
<div class="page-header">
  <h1>Golden Rule Violations &mdash; By Company (v2)</h1>
  <div class="sub">Resolved: {total_resolved_v2} / 175 &nbsp;|&nbsp; Remaining: {total_remaining_v2}</div>
</div>
<div class="top-actions">
  <div class="ca-field">
    <label>CA Name</label>
    <input type="text" id="ca2-name" placeholder="Your name..." oninput="saveMeta2()">
  </div>
  <button class="btn btn-orange" onclick="exportV2()">&#8595; Export JSON</button>
  <button class="btn btn-navy" onclick="importV2()">&#8593; Import</button>
</div>
<div class="tabs">{tab_buttons}</div>
{tab_contents}
</div>
<script>
const LS_KEY2 = "gt_violations_v2_responses";
let saved2 = {{}};

function loadSaved2() {{
  try {{
    const s = localStorage.getItem(LS_KEY2);
    if (s) saved2 = JSON.parse(s);
    const m = localStorage.getItem(LS_KEY2+"_meta");
    if (m) {{
      const meta = JSON.parse(m);
      if (meta.name) document.getElementById("ca2-name").value = meta.name;
    }}
    // Restore radio states
    Object.keys(saved2).forEach(function(iid) {{
      const sv = saved2[iid];
      if (sv.decision) {{
        const radio = document.querySelector('input[name="v2-' + iid + '"][value="' + sv.decision + '"]');
        if (radio) radio.checked = true;
      }}
      if (sv.other_row) {{
        const el = document.getElementById("v2-other-" + iid);
        if (el) el.value = sv.other_row;
      }}
      if (sv.notes) {{
        const el = document.getElementById("v2-note-" + iid);
        if (el) el.value = sv.notes;
      }}
    }});
  }} catch(e) {{}}
}}

function saveMeta2() {{
  const meta = {{ name: document.getElementById("ca2-name").value }};
  localStorage.setItem(LS_KEY2+"_meta", JSON.stringify(meta));
}}

function saveV2(iid) {{
  const radios = document.querySelectorAll('input[name="v2-' + iid + '"]');
  let decision = null;
  radios.forEach(function(r) {{ if (r.checked) decision = r.value; }});
  const otherEl = document.getElementById("v2-other-" + iid);
  const noteEl = document.getElementById("v2-note-" + iid);
  saved2[iid] = {{
    decision: decision,
    other_row: otherEl ? otherEl.value : "",
    notes: noteEl ? noteEl.value : ""
  }};
  localStorage.setItem(LS_KEY2, JSON.stringify(saved2));
  // Green row
  const row = document.getElementById("vr2-" + iid);
  if (row) row.style.background = decision ? "#f0fff4" : "";
}}

function showTab2(co) {{
  document.querySelectorAll(".tab").forEach(function(t) {{ t.classList.remove("active"); }});
  document.querySelectorAll(".tab-content").forEach(function(t) {{ t.classList.remove("active"); }});
  const tab = document.querySelector('[data-tab="' + co + '"]');
  if (tab) tab.classList.add("active");
  const content = document.getElementById("tab-" + co);
  if (content) content.classList.add("active");
}}

function toggleSec2(bodyId, chevId) {{
  const body = document.getElementById(bodyId);
  const chev = document.getElementById(chevId);
  if (body.classList.contains("hidden")) {{
    body.classList.remove("hidden");
    if (chev) chev.classList.add("rot");
  }} else {{
    body.classList.add("hidden");
    if (chev) chev.classList.remove("rot");
  }}
}}

function exportV2() {{
  const name = document.getElementById("ca2-name").value || "CA";
  const out = {{ reviewer: name, responses: saved2, exported_at: new Date().toISOString() }};
  const blob = new Blob([JSON.stringify(out, null, 2)], {{type:"application/json"}});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "GT_violations_v2_responses.json";
  a.click();
}}

function importV2() {{
  const input = document.createElement("input");
  input.type = "file";
  input.accept = ".json";
  input.onchange = function(e) {{
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(ev) {{
      try {{
        const data = JSON.parse(ev.target.result);
        if (data.responses) {{
          saved2 = data.responses;
          localStorage.setItem(LS_KEY2, JSON.stringify(saved2));
          alert("Imported. Refreshing...");
          location.reload();
        }}
      }} catch(err) {{ alert("Error: " + err.message); }}
    }};
    reader.readAsText(file);
  }};
  input.click();
}}

loadSaved2();
</script>
</body>
</html>"""

with open(OUT_V2_VIOL, "w", encoding="utf-8") as f:
    f.write(html_viol)

size_viol = os.path.getsize(OUT_V2_VIOL)
print(f"  Written: {OUT_V2_VIOL} ({size_viol // 1024} KB)")


# ── Step 7: Validate JS syntax ────────────────────────────────────────────────
print("Step 7: Validating JS syntax with node --check...")

def validate_html_js(html_path, label):
    """Extract <script> content and run node --check."""
    with open(html_path, encoding="utf-8") as f:
        content = f.read()
    # Find script block(s)
    import re
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
    if not scripts:
        print(f"  [{label}] No script found")
        return False
    js_code = "\n".join(scripts)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False, encoding="utf-8") as tf:
        tf.write(js_code)
        tmp_path = tf.name
    try:
        result = subprocess.run(
            ["node", "--check", tmp_path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print(f"  [{label}] JS syntax OK")
            return True
        else:
            print(f"  [{label}] JS syntax ERROR:")
            print(result.stderr[:500])
            return False
    except FileNotFoundError:
        print(f"  [{label}] node not found, skipping JS check")
        return True
    except Exception as e:
        print(f"  [{label}] Error: {e}")
        return False
    finally:
        os.unlink(tmp_path)

v2_ok = validate_html_js(OUT_V2, "GT_disputes_review_v2.html")
viol_ok = validate_html_js(OUT_V2_VIOL, "Golden_rule_violations_by_company_v2.html")


# ── Summary ───────────────────────────────────────────────────────────────────
print()
print("=== SUMMARY ===")
print(f"Total disputes: 175")
print(f"Truly answered (decision not null, not dedup-pending): {total_truly_answered}")
print(f"Auto-resolved (dedup): 5")
print(f"Dedup-pending: 3")
print(f"Special (null decision, notes): {len(special_items)}")
print(f"Needs CA review: {len(items_data)}")
print()
print("Per company remaining:")
for co in companies_order:
    n = len(company_disputes[co])
    if n > 0:
        print(f"  {co}: {n}")
print()
print("Files:")
print(f"  GT_disputes_review_v2.html: {size_v2 // 1024} KB")
print(f"  Golden_rule_violations_by_company_v2.html: {size_viol // 1024} KB")
