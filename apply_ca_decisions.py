#!/usr/bin/env python3
"""
Apply CA's resolved contradiction decisions to GT disputes HTML.

Reads:
  - DOCS/Rule_contradictions_responses.json   (CA decisions)
  - CMA_Ground_Truth_v1/validation/rule_contradictions.json
  - CMA_Ground_Truth_v1/validation/gt_validation_final.json
  - CMA_Ground_Truth_v1/reference/canonical_labels.json

Writes:
  - DOCS/test-results/round2/GT_disputes_review.html     (updated)
  - DOCS/test-results/round2/Golden_rule_violations_by_company.html (updated)
"""

import json, re
from pathlib import Path
from rapidfuzz import fuzz

BASE = Path(__file__).parent
VALIDATION = BASE / "CMA_Ground_Truth_v1" / "validation"
REFERENCE  = BASE / "CMA_Ground_Truth_v1" / "reference"
OUT_DIR    = BASE / "DOCS" / "test-results" / "round2"

# ── Load data ──────────────────────────────────────────────────────────────────
print("Loading data files...")
with open(BASE / "DOCS" / "Rule_contradictions_responses.json", encoding="utf-8") as f:
    CA_RESPONSES = json.load(f)["responses"]

with open(VALIDATION / "rule_contradictions.json", encoding="utf-8") as f:
    CONTRADICTIONS = json.load(f)

with open(VALIDATION / "gt_validation_final.json", encoding="utf-8") as f:
    GT = json.load(f)

with open(REFERENCE / "canonical_labels.json", encoding="utf-8") as f:
    LABELS = json.load(f)

DISPUTES  = GT["disputes"]
CROSS     = CONTRADICTIONS["cross_source_contradictions"]
INTERNAL  = CONTRADICTIONS["internal_contradictions"]
ROW_NAMES = {item["sheet_row"]: item["name"] for item in LABELS}

FUZZY_THRESHOLD = 75  # Lower threshold to catch variants like "(c) Staff Welfare"

# ── Step 1: Build resolved-rules lookup ──────────────────────────────────────
print("\nStep 1: Building resolved rules from CA responses...")

# A resolved rule = { text, industry, winning_row, winning_name, rule_id, notes, context_rules }
# context_rules = { 'debit': row, 'credit': row } for context-dependent items
resolved_rules = []  # list of rule dicts

# --- Cross-source contradictions ---
# cross_NNN -> CROSS[NNN-1]
for resp_id, resp in CA_RESPONSES.items():
    if not resp_id.startswith("cross_"):
        continue
    idx = int(resp_id.split("_")[1]) - 1
    if idx < 0 or idx >= len(CROSS):
        print(f"  WARN: {resp_id} -> index {idx} out of range")
        continue

    item = CROSS[idx]
    decision = resp.get("decision")
    notes    = resp.get("notes", "").strip()

    if decision == "s2":
        winning_row  = item["ca_row"]
        winning_name = ROW_NAMES.get(item["ca_row"], item.get("ca_name",""))
        winner_label = "CA Answers"
    elif decision == "s1":
        winning_row  = item["rule_row"]
        winning_name = ROW_NAMES.get(item["rule_row"], item.get("rule_name",""))
        winner_label = "Classification XLS"
    elif decision == "other":
        winning_row  = resp.get("selected_row")
        winning_name = resp.get("selected_name", ROW_NAMES.get(winning_row,""))
        winner_label = "CA Custom"
    else:
        continue  # No decision, skip

    # The canonical text to match against is the CA's item text (broader)
    canonical_text = item.get("ca_item_text", item.get("rule_fs_item",""))
    industry       = item.get("industry", "all")

    rule = {
        "id":           resp_id,
        "text":         canonical_text,
        "industry":     industry,
        "winning_row":  winning_row,
        "winning_name": winning_name,
        "winner_label": winner_label,
        "notes":        notes,
        "context_rules": None,
        "source_item":  item,
    }
    resolved_rules.append(rule)
    print(f"  {resp_id}: '{canonical_text}' ({industry}) -> Row {winning_row} ({winning_name})")

# --- Internal contradictions ---
# int_NNN -> INTERNAL[NNN - 15]  (14 cross items, so int_015 = INTERNAL[0])
for resp_id, resp in CA_RESPONSES.items():
    if not resp_id.startswith("int_"):
        continue
    idx = int(resp_id.split("_")[1]) - 15
    if idx < 0 or idx >= len(INTERNAL):
        print(f"  WARN: {resp_id} -> index {idx} out of range")
        continue

    item   = INTERNAL[idx]
    decision = resp.get("decision")
    notes    = resp.get("notes", "").strip()

    # Get the item text
    if "conflicting_rules" in item:
        canonical_text = item.get("fs_item", "")
        r1_row = item["conflicting_rules"][0]["row"]
        r2_row = item["conflicting_rules"][1]["row"]
        r1_name = item["conflicting_rules"][0].get("canonical_name","")
        r2_name = item["conflicting_rules"][1].get("canonical_name","")
    else:
        r1 = item.get("rule_1", {})
        r2 = item.get("rule_2", {})
        canonical_text = r1.get("fs_item", r2.get("fs_item",""))
        r1_row = r1.get("row"); r1_name = r1.get("canonical_name","")
        r2_row = r2.get("row"); r2_name = r2.get("canonical_name","")

    # Parse context-dependent notes (debit/credit, refundable/non-refundable)
    context_rules = None
    debit_match  = re.search(r'[Dd]ebit[^:]*:[-\s]*R?(\d+)', notes)
    credit_match = re.search(r'[Cc]redit[^:]*:[-\s]*R?(\d+)', notes.replace('\n', ' '))
    if debit_match and credit_match:
        d_row = int(debit_match.group(1))
        c_row = int(credit_match.group(1))
        context_rules = {"debit": d_row, "credit": c_row}
        winning_row  = None  # Context-dependent
        winning_name = None
        winner_label = f"Context-dependent (debit->R{d_row}, credit->R{c_row})"
    elif decision == "r1":
        winning_row  = r1_row
        winning_name = ROW_NAMES.get(r1_row, r1_name)
        winner_label = f"Rule 1 wins"
    elif decision == "r2":
        winning_row  = r2_row
        winning_name = ROW_NAMES.get(r2_row, r2_name)
        winner_label = f"Rule 2 wins"
    elif decision == "other":
        winning_row  = resp.get("selected_row")
        winning_name = resp.get("selected_name", ROW_NAMES.get(winning_row,"") if winning_row else "")
        winner_label = "CA Custom"
    else:
        continue

    rule = {
        "id":           resp_id,
        "text":         canonical_text,
        "industry":     "all",
        "winning_row":  winning_row,
        "winning_name": winning_name,
        "winner_label": winner_label,
        "notes":        notes,
        "context_rules": context_rules,
        "source_item":  item,
    }
    resolved_rules.append(rule)
    if context_rules:
        print(f"  {resp_id}: '{canonical_text}' -> context-dep (debit=R{context_rules['debit']}, credit=R{context_rules['credit']})")
    else:
        print(f"  {resp_id}: '{canonical_text}' -> Row {winning_row} ({winning_name})")

print(f"\nTotal resolved rules: {len(resolved_rules)}")

# ── Step 2: Match resolved rules against GT disputes ─────────────────────────
print("\nStep 2: Matching resolved rules against 175 GT disputes...")

def best_rule_match(raw_text, industry):
    """Return (rule, score) for the best matching resolved rule, or (None, 0)."""
    best_rule  = None
    best_score = 0

    for rule in resolved_rules:
        # Industry check: rule applies if industry matches OR rule is "all"
        if rule["industry"] != "all" and rule["industry"] != industry:
            continue

        score = fuzz.token_set_ratio(raw_text.lower(), rule["text"].lower())
        if score > best_score:
            best_score = score
            best_rule  = rule

    return best_rule, best_score


def determine_resolution(dispute, matched_rule):
    """
    Given a matched rule, determine how to auto-resolve this dispute.
    Returns dict: { decision, row, name, label, context_dep }
    """
    gt_row = dispute.get("gt_row")
    gr_row = dispute.get("golden_rule_row")
    context_rules = matched_rule.get("context_rules")

    if context_rules:
        # Can't auto-resolve without knowing balance direction
        return {
            "decision":    "context_dep",
            "row":         None,
            "name":        matched_rule["winner_label"],
            "context_dep": True,
            "debit_row":   context_rules["debit"],
            "credit_row":  context_rules["credit"],
        }

    winning_row = matched_rule["winning_row"]
    if winning_row is None:
        return None

    winning_name = matched_rule["winning_name"] or ROW_NAMES.get(winning_row, "")

    if winning_row == gt_row:
        decision = "gt"
        label    = f"GT correct (Row {winning_row}: {winning_name})"
    elif winning_row == gr_row:
        decision = "rule"
        label    = f"Golden Rule correct (Row {winning_row}: {winning_name})"
    else:
        decision = "other"
        label    = f"Other: Row {winning_row}: {winning_name}"

    return {
        "decision":    decision,
        "row":         winning_row,
        "name":        winning_name,
        "label":       label,
        "context_dep": False,
    }


pre_resolved = []   # list of (dispute_idx, dispute, rule, score, resolution)
unresolved   = []

for i, dispute in enumerate(DISPUTES):
    raw_text = dispute.get("raw_text", "")
    industry = dispute.get("industry_type", "all")

    rule, score = best_rule_match(raw_text, industry)

    if rule and score >= FUZZY_THRESHOLD:
        resolution = determine_resolution(dispute, rule)
        if resolution and resolution["decision"] != "context_dep":
            pre_resolved.append({
                "idx":        i,
                "dispute":    dispute,
                "rule":       rule,
                "score":      score,
                "resolution": resolution,
            })
            continue

    unresolved.append({"idx": i, "dispute": dispute})

print(f"\n  Pre-resolved: {len(pre_resolved)}")
print(f"  Remaining:    {len(unresolved)}")
print(f"\nPre-resolved breakdown:")
by_rule = {}
for pr in pre_resolved:
    rid = pr["rule"]["id"]
    by_rule.setdefault(rid, []).append(pr["dispute"]["raw_text"])
for rid, items in sorted(by_rule.items(), key=lambda x: -len(x[1])):
    print(f"  {rid} ({resolved_rules[[r['id'] for r in resolved_rules].index(rid)]['text']}): {len(items)} disputes")
    for txt in items:
        print(f"    - {txt}")

# ── Shared CSS (same as generator) ────────────────────────────────────────────
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
.btn-outline{background:#fff;color:#4a5568;border:1px solid #cbd5e0}.btn-outline:hover{border-color:#1a365d;color:#1a365d}
.restore-banner{background:#ebf8ff;border:1px solid #90cdf4;padding:10px 14px;border-radius:6px;margin-bottom:12px;display:flex;align-items:center;gap:10px;font-size:13px}
.restore-banner.hidden{display:none}
/* Section blocks */
.sec-block{margin-bottom:14px}
.sec-hdr{background:#1a365d;color:#fff;padding:11px 16px;border-radius:8px 8px 0 0;cursor:pointer;display:flex;align-items:center;gap:10px;user-select:none}
.sec-hdr.green{background:#276749}
.sec-hdr.closed{border-radius:8px;margin-bottom:0}
.sec-letter{background:#e67e22;color:#fff;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;flex-shrink:0}
.sec-letter.green{background:#48bb78}
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
/* Pre-resolved card */
.pr-card{padding:14px 16px;border-bottom:1px solid #c6f6d5;background:#f0fff4}
.pr-card:last-child{border-bottom:none}
.pr-top{display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap}
.pr-badge{background:#276749;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700}
.pr-raw{font-size:15px;font-weight:700;color:#276749;flex:1}
.pr-resolution{background:#c6f6d5;border-left:3px solid #48bb78;padding:6px 10px;font-size:12px;border-radius:0 4px 4px 0;margin-bottom:8px}
.pr-rule-text{font-size:11px;color:#718096;margin-bottom:6px}
.pr-override{margin-top:8px;border-top:1px solid #c6f6d5;padding-top:8px}
.pr-override-toggle{background:none;border:1px solid #c6f6d5;padding:3px 10px;border-radius:4px;font-size:11px;cursor:pointer;color:#276749}
.pr-override-toggle:hover{border-color:#276749}
.pr-override-body{display:none;margin-top:8px}
.pr-override-body.open{display:block}
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
.pill-green{background:#c6f6d5;color:#276749}
.cmp-table{width:100%;border-collapse:collapse;margin-bottom:12px;font-size:13px}
.cmp-table th{background:#f7fafc;padding:7px 10px;text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;color:#4a5568;letter-spacing:.05em;border:1px solid #e2e8f0}
.cmp-table td{padding:8px 10px;border:1px solid #e2e8f0;vertical-align:top}
.cmp-gt{background:#fff5f5}
.cmp-rule{background:#f0fff4}
.row-num{font-weight:700;color:#1a365d;font-size:13px}
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
.extra-toggle{background:none;border:1px solid #e2e8f0;padding:4px 10px;border-radius:4px;font-size:12px;cursor:pointer;color:#4a5568;display:flex;align-items:center;gap:5px;margin-bottom:6px}
.extra-toggle:hover{border-color:#1a365d;color:#1a365d}
.extra-body{display:none;padding:10px;background:#f7fafc;border:1px solid #e2e8f0;border-radius:6px;margin-bottom:8px}
.extra-body.open{display:block}
.ind-grid{width:100%;border-collapse:collapse;font-size:13px;margin-top:6px}
.ind-grid th{background:#edf2f7;padding:5px 8px;font-size:11px;text-align:left;font-weight:700;color:#4a5568;border:1px solid #e2e8f0}
.ind-grid td{padding:5px 8px;border:1px solid #e2e8f0;vertical-align:middle}
.ind-grid td:first-child{font-weight:600;font-size:12px;color:#2d3748;white-space:nowrap}
.ind-grid input{width:100%;padding:3px 6px;border:1px solid #cbd5e0;border-radius:3px;font-size:12px}
.ind-grid input:focus{outline:none;border-color:#1a365d}
.conf-row{margin-bottom:8px}
.conf-lbl{font-size:12px;font-weight:700;color:#4a5568;margin-bottom:4px;text-transform:uppercase;letter-spacing:.04em}
.conf-opts{display:flex;gap:16px;flex-wrap:wrap}
.conf-opt{display:flex;align-items:center;gap:5px;cursor:pointer;font-size:13px}
.conf-opt input{accent-color:#1a365d}
.notes-row{margin-bottom:8px}
.notes-row label{font-size:12px;font-weight:700;color:#4a5568;display:block;margin-bottom:3px;text-transform:uppercase;letter-spacing:.04em}
.notes-row textarea{width:100%;padding:6px 10px;border:1px solid #e2e8f0;border-radius:5px;font-size:13px;resize:vertical;min-height:34px;font-family:inherit}
.notes-row textarea:focus{outline:none;border-color:#1a365d}
.ai-box{background:#fef3e2;border-left:3px solid #e67e22;padding:8px 12px;font-size:12px;margin-bottom:10px;border-radius:0 4px 4px 0;color:#744210}
.d-section{font-size:11px;color:#718096;margin-bottom:6px}
.summary-cards{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.s-card{background:#fff;border-radius:8px;padding:12px 16px;box-shadow:0 1px 3px rgba(0,0,0,.08);flex:1;min-width:120px}
.s-card .val{font-size:24px;font-weight:700;color:#1a365d}
.s-card .val.green{color:#276749}
.s-card .lbl{font-size:12px;color:#718096;margin-top:2px}
.tabs{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:12px}
.tab{padding:6px 12px;border-radius:6px 6px 0 0;font-size:13px;font-weight:500;cursor:pointer;border:1px solid #e2e8f0;background:#f7fafc;color:#4a5568;transition:all .15s;border-bottom:none}
.tab.active{background:#1a365d;color:#fff;border-color:#1a365d}
.tab-content{display:none}
.tab-content.active{display:block}
.violations-table{width:100%;border-collapse:collapse;font-size:13px}
.violations-table th{background:#1a365d;color:#fff;padding:8px 10px;text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.04em}
.violations-table td{padding:8px 10px;border-bottom:1px solid #e2e8f0;vertical-align:middle}
.violations-table tr:hover td{background:#f7fafc}
.violations-table tr.pre-res td{background:#f0fff4}
.inline-radio{display:flex;align-items:center;gap:6px;white-space:nowrap}
.inline-radio input{accent-color:#1a365d}
.inline-note{width:120px;padding:3px 6px;border:1px solid #cbd5e0;border-radius:3px;font-size:12px}
.resolved-badge{background:#c6f6d5;color:#276749;padding:2px 7px;border-radius:4px;font-size:11px;font-weight:600}
"""

# ── Shared JS ──────────────────────────────────────────────────────────────────
SHARED_JS = """
function rowName(row){return ROW_NAMES[row]||''}
function saveResponse(key,id,data){
  var saved=JSON.parse(localStorage.getItem(key)||'{"responses":{}}');
  saved.responses[id]=data;saved.lastSaved=new Date().toISOString();
  var ca=document.getElementById('ca-name');if(ca)saved.reviewer=ca.value;
  localStorage.setItem(key,JSON.stringify(saved));
}
function exportJSON(key,fn){
  var saved=JSON.parse(localStorage.getItem(key)||'{"responses":{}}');
  var blob=new Blob([JSON.stringify(saved,null,2)],{type:'application/json'});
  var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=fn;a.click();
}
function setupSectionToggles(){
  document.querySelectorAll('.sec-hdr').forEach(function(hdr){
    hdr.addEventListener('click',function(){
      var qs=this.parentElement.querySelector('.sec-qs');
      var chev=this.querySelector('.chevron');
      if(qs){qs.classList.toggle('hidden');hdr.classList.toggle('closed',qs.classList.contains('hidden'));
        if(chev)chev.classList.toggle('rot',!qs.classList.contains('hidden'));}
    });
  });
}
function checkRestore(key,banner){
  var saved=JSON.parse(localStorage.getItem(key)||'{}');
  if(saved.lastSaved&&Object.keys(saved.responses||{}).length>0){
    if(banner){var c=Object.keys(saved.responses).length;
      banner.querySelector('.restore-msg').textContent='Restored '+c+' saved responses from '+new Date(saved.lastSaved).toLocaleString();
      banner.classList.remove('hidden');}
    restoreAllResponses(key);
  }
}
"""

# ── Helpers ────────────────────────────────────────────────────────────────────
def esc(s):
    if not s: return ""
    return (str(s).replace("&","&amp;").replace("<","&lt;")
                  .replace(">","&gt;").replace('"',"&quot;"))

def ind_pill(ind):
    cls = {"manufacturing":"pill-mfg","trading":"pill-trading",
           "services":"pill-services","construction":"pill-construction"}.get(ind,"pill-all")
    return f'<span class="pill {cls}">{esc(ind.capitalize())}</span>' if ind else ""

def ctx_pill(ctx):
    if not ctx: return ""
    return ('<span class="pill pill-pl">P&amp;L</span>' if ctx=="pl"
            else '<span class="pill pill-bs">B/S</span>')

def row_disp(row, name=""):
    n = name or ROW_NAMES.get(row, "")
    return f"<span class='row-num'>Row {row}</span> &mdash; {esc(n)}"

# ── Step 3: Build GT_disputes_review.html ─────────────────────────────────────
print("\nStep 3: Building updated GT_disputes_review.html...")

# Assign IDs to disputes (must match original for localStorage compat)
for i, d in enumerate(DISPUTES):
    d["_id"] = f"d{i+1:03d}"

# Build pre-resolved ID set for quick lookup
pr_ids = {pr["dispute"]["_id"]: pr for pr in pre_resolved}
# Build compact pre-resolved data for JS
pr_compact = []
for pr in pre_resolved:
    d   = pr["dispute"]
    res = pr["resolution"]
    pr_compact.append({
        "id":      d["_id"],
        "raw":     d["raw_text"],
        "section": d.get("section",""),
        "company": d.get("company",""),
        "industry":d.get("industry_type",""),
        "ctx":     d.get("document_context",""),
        "gt_row":  d.get("gt_row"),
        "gt_name": ROW_NAMES.get(d.get("gt_row"), d.get("gt_field","")),
        "gr_row":  d.get("golden_rule_row"),
        "gr_name": ROW_NAMES.get(d.get("golden_rule_row"), d.get("golden_rule_name","")),
        "decision":res["decision"],
        "win_row": res["row"],
        "win_name":res["name"],
        "win_lbl": res["label"],
        "rule_id": pr["rule"]["id"],
        "rule_text":pr["rule"]["text"],
        "score":   round(pr["score"],1),
        "ai":      d.get("agent_reasoning") or "",
    })

# Group remaining disputes for sections
industry_keywords = ["manufacturing","factory","industry","industries"]
unres_with_groups = []
for item in unresolved:
    d = item["dispute"]
    reasoning = (d.get("agent_reasoning") or "").lower()
    has_ind = any(kw in reasoning for kw in industry_keywords)
    if has_ind:
        grp = "industry"
    elif d.get("document_context") == "bs":
        grp = "bs"
    else:
        grp = d.get("company","unknown")
    item["group"] = grp
    unres_with_groups.append(item)

# Sorted company groups
companies = []
for item in unres_with_groups:
    if item["group"] not in ("industry","bs") and item["group"] not in companies:
        companies.append(item["group"])
companies.sort()
groups_order = ["industry","bs"] + companies

sections = []
for g in groups_order:
    items = [it for it in unres_with_groups if it["group"] == g]
    if not items: continue
    if g == "industry": label = "Industry-Dependent Disputes"
    elif g == "bs":     label = "Balance Sheet / Context-Dependent Disputes"
    else:
        ind = items[0]["dispute"].get("industry_type","")
        label = f"{g.replace('_',' ')} ({ind.capitalize()})"
    sections.append({"key": g, "label": label, "ids": [it["dispute"]["_id"] for it in items]})

# Compact unresolved for JS
unres_compact = []
for item in unres_with_groups:
    d = item["dispute"]
    unres_compact.append({
        "id":      d["_id"],
        "group":   item["group"],
        "raw":     d.get("raw_text",""),
        "section": d.get("section",""),
        "company": d.get("company",""),
        "industry":d.get("industry_type",""),
        "ctx":     d.get("document_context",""),
        "gt_row":  d.get("gt_row"),
        "gt_name": ROW_NAMES.get(d.get("gt_row"), d.get("gt_field","")),
        "gr_row":  d.get("golden_rule_row"),
        "gr_name": ROW_NAMES.get(d.get("golden_rule_row"), d.get("golden_rule_name","")),
        "method":  d.get("match_method",""),
        "score":   d.get("fuzzy_score"),
        "ai":      d.get("agent_reasoning") or "",
    })

# Static section skeletons
sections_html = ""
for idx, sec in enumerate(sections):
    count = len(sec["ids"])
    sections_html += f"""
<div class="sec-block" id="sec-{esc(sec['key'].replace(' ','_'))}">
  <div class="sec-hdr">
    <span class="sec-letter">{idx+1}</span>
    <span class="sec-title-text">{esc(sec['label'])}</span>
    <span class="sec-count">{count} disputes</span>
    <span class="chevron rot">&#9660;</span>
  </div>
  <div class="sec-qs" id="qs-{esc(sec['key'].replace(' ','_'))}"></div>
</div>"""

# Summary mini-cards
by_company = GT.get("by_company",{})
company_cards = "".join(
    f"<div class='s-card'><div class='val'>{v.get('dispute',0)}</div><div class='lbl'>{esc(k.replace('_',' '))}</div></div>"
    for k,v in by_company.items()
)

num_remaining = len(unresolved)
num_pre       = len(pre_resolved)

doc1_html = f"""<!DOCTYPE html>
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
  <div class="sub">{num_remaining} items need review &mdash; {num_pre} pre-resolved by CA golden rule decisions</div>
</div>

<div class="restore-banner hidden" id="restore-banner">
  &#128190;
  <span class="restore-msg"></span>
  <button class="btn btn-outline" onclick="localStorage.removeItem('cma_gt_disputes_v2');location.reload()">Clear &amp; Restart</button>
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
    <span id="prog-counter">0 of {num_remaining} reviewed</span>
    <span id="prog-pct">0%</span>
  </div>
  <div class="pbar"><div class="pbar-fill" id="prog-bar" style="width:0%"></div></div>
  <div style="font-size:11px;color:#718096;margin-top:4px">&#x2713; {num_pre} items pre-resolved by golden rule decisions (see section below)</div>
</div>

<div class="summary-cards">
  <div class="s-card"><div class="val">{num_remaining}</div><div class="lbl">Remaining to Review</div></div>
  <div class="s-card"><div class="val green">{num_pre}</div><div class="lbl">Pre-Resolved</div></div>
  {company_cards}
</div>

<!-- Pre-resolved section (collapsed, green) -->
<div class="sec-block" id="sec-pre-resolved">
  <div class="sec-hdr green closed">
    <span class="sec-letter green">&#x2713;</span>
    <span class="sec-title-text">Pre-Resolved by Golden Rule Decisions &mdash; {num_pre} items</span>
    <span class="sec-count">Expand to review or override</span>
    <span class="chevron">&#9660;</span>
  </div>
  <div class="sec-qs hidden" id="qs-pre-resolved"></div>
</div>

{sections_html}

</div>
<script>
const ROW_NAMES = {json.dumps(ROW_NAMES, separators=(',',':'))};
const PR_DATA   = {json.dumps(pr_compact, ensure_ascii=False, separators=(',',':'))};
const UNRES_DATA= {json.dumps(unres_compact, ensure_ascii=False, separators=(',',':'))};
const SECTIONS  = {json.dumps(sections, ensure_ascii=False, separators=(',',':'))};
const TOTAL_REMAINING = {num_remaining};
const STORAGE_KEY = 'cma_gt_disputes_v2';

{SHARED_JS}

const IND_CLS = {{manufacturing:'pill-mfg',trading:'pill-trading',services:'pill-services',construction:'pill-construction',all:'pill-all'}};
function indPill(i){{return i?'<span class="pill '+(IND_CLS[i]||'pill-all')+'">'+i.charAt(0).toUpperCase()+i.slice(1)+'</span>':''}}
function ctxPill(c){{return c==='pl'?'<span class="pill pill-pl">P&amp;L</span>':c==='bs'?'<span class="pill pill-bs">B/S</span>':''}}
function esc(s){{if(!s)return'';return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}}

// ── Pre-resolved card builder ─────────────────────────────────────────────────
function buildPrCard(d, num) {{
  const iid = d.id;
  const decLabel = d.decision==='gt' ? 'GT is correct' : d.decision==='rule' ? 'Golden Rule is correct' : 'Other row';
  const badge = d.decision==='gt' ? 'GT CORRECT' : d.decision==='rule' ? 'RULE CORRECT' : 'OTHER ROW';
  const badgeCls = d.decision==='gt' ? 'badge-gt' : 'badge-rule';
  return `<div class="pr-card" id="card-${{iid}}">
  <div class="pr-top">
    <span class="pr-badge">#${{num}} ${{badge}}</span>
    <span class="pr-raw">${{esc(d.raw)}}</span>
    ${{indPill(d.industry)}} ${{ctxPill(d.ctx)}}
  </div>
  <div style="font-size:11px;color:#718096;margin-bottom:6px">Section: ${{esc(d.section)}} | Company: <strong>${{d.company}}</strong></div>
  <div class="pr-resolution">
    <strong>&#x2713; Resolved:</strong> ${{esc(d.win_lbl)}}
    <span style="margin-left:8px;font-size:11px;color:#718096">via ${{esc(d.rule_id)}} (${{esc(d.rule_text)}}) &mdash; match ${{d.score}}%</span>
  </div>
  <table class="cmp-table" style="margin-bottom:6px">
    <tr><th>GT (Current)</th><th>Golden Rule (Expected)</th><th>&#x2713; Resolved Row</th></tr>
    <tr>
      <td class="cmp-gt"><span class="row-num">Row ${{d.gt_row}}</span> &mdash; ${{esc(d.gt_name)}}</td>
      <td class="cmp-rule"><span class="row-num">Row ${{d.gr_row}}</span> &mdash; ${{esc(d.gr_name)}}</td>
      <td style="background:#f0fff4;font-weight:700;color:#276749"><span class="row-num">Row ${{d.win_row}}</span> &mdash; ${{esc(d.win_name)}}</td>
    </tr>
  </table>
  <div class="pr-override">
    <button class="pr-override-toggle" onclick="togglePrOverride('${{iid}}',this)">&#9998; Override this decision</button>
    <div class="pr-override-body" id="pr-ov-${{iid}}">
      <div class="decision-block" style="margin-top:8px">
        <div class="decision-lbl">Override Decision</div>
        <div class="opt-row" onclick="selOpt('${{iid}}','gt',this)">
          <input type="radio" name="dec-${{iid}}" value="gt" id="gt-${{iid}}">
          <label for="gt-${{iid}}">GT is correct &mdash; Row ${{d.gt_row}}: ${{esc(d.gt_name)}}</label>
        </div>
        <div class="opt-row" onclick="selOpt('${{iid}}','rule',this)">
          <input type="radio" name="dec-${{iid}}" value="rule" id="rule-${{iid}}">
          <label for="rule-${{iid}}">Golden Rule is correct &mdash; Row ${{d.gr_row}}: ${{esc(d.gr_name)}}</label>
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
      <div class="notes-row">
        <label>Notes</label>
        <textarea id="notes-${{iid}}" rows="2" placeholder="Override reason..." oninput="saveCard('${{iid}}')"></textarea>
      </div>
    </div>
  </div>
</div>`;
}}

// ── Normal card builder ───────────────────────────────────────────────────────
function buildCard(d, num) {{
  const iid = d.id;
  const gtLabel = 'Row '+d.gt_row+': '+esc(d.gt_name);
  const grLabel = 'Row '+d.gr_row+': '+esc(d.gr_name);
  const methodBadge = d.method ? '<span style="font-size:10px;background:#e2e8f0;padding:1px 5px;border-radius:3px;color:#4a5568">'+d.method+(d.score?' '+Math.round(d.score)+'%':'')+'</span>' : '';
  const aiBox = d.ai ? '<div class="ai-box"><strong>AI:</strong> '+esc(d.ai)+'</div>' : '';
  return `<div class="d-card" id="card-${{iid}}">
  <div class="d-top">
    <span class="d-num">#${{num}}</span>
    <span class="d-raw">${{esc(d.raw)}}</span>
    ${{indPill(d.industry)}} ${{ctxPill(d.ctx)}} ${{methodBadge}}
  </div>
  <div class="d-section">Section: ${{esc(d.section)}} &nbsp;|&nbsp; Company: <strong>${{d.company}}</strong></div>
  ${{aiBox}}
  <table class="cmp-table">
    <tr><th>GT (Current)</th><th>Golden Rule (Expected)</th></tr>
    <tr>
      <td class="cmp-gt"><span class="row-num">Row ${{d.gt_row}}</span> &mdash; ${{esc(d.gt_name)}}</td>
      <td class="cmp-rule"><span class="row-num">Row ${{d.gr_row}}</span> &mdash; ${{esc(d.gr_name)}}</td>
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
        <input type="radio" name="it-${{iid}}" value="no" checked onchange="toggleGrid('ig-${{iid}}',false);saveCard('${{iid}}')"> No
      </label>
      <label style="display:flex;align-items:center;gap:5px;font-size:13px;cursor:pointer">
        <input type="radio" name="it-${{iid}}" value="yes" onchange="toggleGrid('ig-${{iid}}',true);saveCard('${{iid}}')"> Yes
      </label>
    </div>
    <div id="ig-${{iid}}" style="display:none">
      <table class="ind-grid">
        <tr><th>Industry</th><th>Row #</th><th>Field Name</th></tr>
        ${{['Manufacturing:mfg','Trading:trd','Services:svc','Construction:con'].map(p=>{{const a=p.split(':');const lbl=a[0];const k=a[1];return '<tr><td>'+lbl+'</td><td><input type="number" id="ir-'+iid+'-'+k+'" oninput="afInd(&apos;'+iid+'&apos;,&apos;'+k+'&apos;);saveCard(&apos;'+iid+'&apos;)">'+'</td><td><input type="text" id="in-'+iid+'-'+k+'" oninput="saveCard(&apos;'+iid+'&apos;)">'+'</td></tr>';}}).join('')}}
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
        <input type="radio" name="ct-${{iid}}" value="no" checked onchange="toggleGrid('cg-${{iid}}',false);saveCard('${{iid}}')"> No
      </label>
      <label style="display:flex;align-items:center;gap:5px;font-size:13px;cursor:pointer">
        <input type="radio" name="ct-${{iid}}" value="yes" onchange="toggleGrid('cg-${{iid}}',true);saveCard('${{iid}}')"> Yes
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

function toggleGrid(id,show){{var g=document.getElementById(id);if(g)g.style.display=show?'block':'none';}}
function toggleExtra(id,btn){{var el=document.getElementById(id);if(!el)return;el.classList.toggle('open');var a=btn.querySelector('.arrow');if(a)a.textContent=el.classList.contains('open')?'\\u25b2':'\\u25bc';}}
function togglePrOverride(iid,btn){{var b=document.getElementById('pr-ov-'+iid);if(b)b.classList.toggle('open');}}
function afName(iid){{var n=parseInt((document.getElementById('on-'+iid)||{{}}).value);if(n&&ROW_NAMES[n]){{var e=document.getElementById('oname-'+iid);if(e)e.value=ROW_NAMES[n];}}saveCard(iid);}}
function afInd(iid,k){{var n=parseInt((document.getElementById('ir-'+iid+'-'+k)||{{}}).value);if(n&&ROW_NAMES[n]){{var e=document.getElementById('in-'+iid+'-'+k);if(e)e.value=ROW_NAMES[n];}}}}
function afCtx(iid,k){{var n=parseInt((document.getElementById('cr-'+iid+'-'+k)||{{}}).value);if(n&&ROW_NAMES[n]){{var e=document.getElementById('cn-'+iid+'-'+k);if(e)e.value=ROW_NAMES[n];}}}}

function selOpt(iid,val,row){{
  document.querySelectorAll('[name="dec-'+iid+'"]').forEach(function(r){{r.closest('.opt-row').classList.remove('sel');}});
  var radio=document.getElementById(val+'-'+iid);
  if(radio){{radio.checked=true;if(row)row.classList.add('sel');}}
  var oi=document.getElementById('oi-'+iid);if(oi)oi.style.display=(val==='other')?'flex':'none';
  saveCard(iid);
}}

function getCardData(iid){{
  var dec=document.querySelector('[name="dec-'+iid+'"]:checked');
  var conf=document.querySelector('[name="conf-'+iid+'"]:checked');
  var itYes=document.querySelector('[name="it-'+iid+'"][value="yes"]:checked');
  var ctYes=document.querySelector('[name="ct-'+iid+'"][value="yes"]:checked');
  var data={{item_id:iid,decision:dec?dec.value:null,confidence:conf?conf.value:null,
    notes:(document.getElementById('notes-'+iid)||{{}}).value||'',industry_specific:null,context_specific:null}};
  if(data.decision==='other'){{
    data.selected_row=parseInt((document.getElementById('on-'+iid)||{{}}).value)||null;
    data.selected_name=(document.getElementById('oname-'+iid)||{{}}).value||'';
  }}
  if(itYes){{
    data.industry_specific={{}};
    [['manufacturing','mfg'],['trading','trd'],['services','svc'],['construction','con']].forEach(function(p){{
      data.industry_specific[p[0]]={{row:parseInt((document.getElementById('ir-'+iid+'-'+p[1])||{{}}).value)||null,name:(document.getElementById('in-'+iid+'-'+p[1])||{{}}).value||''}};
    }});
  }}
  if(ctYes){{
    data.context_specific={{
      pnl:{{row:parseInt((document.getElementById('cr-'+iid+'-pl')||{{}}).value)||null,name:(document.getElementById('cn-'+iid+'-pl')||{{}}).value||''}},
      bs: {{row:parseInt((document.getElementById('cr-'+iid+'-bs')||{{}}).value)||null,name:(document.getElementById('cn-'+iid+'-bs')||{{}}).value||''}}
    }};
  }}
  return data;
}}

function saveCard(iid){{
  var data=getCardData(iid);
  saveResponse(STORAGE_KEY,iid,data);
  var card=document.getElementById('card-'+iid);if(card&&data.decision)card.classList.add('done');
  refreshProgress();
}}

function refreshProgress(){{
  var saved=JSON.parse(localStorage.getItem(STORAGE_KEY)||'{{"responses":{{}}}}');
  // Count only unresolved items (pre-resolved don't count toward progress unless overridden)
  var PR_IDS = new Set(PR_DATA.map(function(d){{return d.id;}}));
  var reviewed=Object.keys(saved.responses||{{}}).filter(function(id){{return !PR_IDS.has(id);}}).length;
  var pct=Math.round((reviewed/TOTAL_REMAINING)*100);
  document.getElementById('prog-counter').textContent=reviewed+' of '+TOTAL_REMAINING+' reviewed';
  document.getElementById('prog-pct').textContent=pct+'%';
  document.getElementById('prog-bar').style.width=pct+'%';
}}

function saveMeta(){{
  var saved=JSON.parse(localStorage.getItem(STORAGE_KEY)||'{{"responses":{{}}}}');
  saved.reviewer=document.getElementById('ca-name').value;
  saved.date=document.getElementById('review-date').value;
  localStorage.setItem(STORAGE_KEY,JSON.stringify(saved));
}}

function restoreAllResponses(key){{
  var saved=JSON.parse(localStorage.getItem(key)||'{{"responses":{{}}}}');
  if(saved.reviewer){{var el=document.getElementById('ca-name');if(el)el.value=saved.reviewer;}}
  Object.entries(saved.responses||{{}}).forEach(function([iid,data]){{
    if(!data.decision)return;
    var card=document.getElementById('card-'+iid);if(!card)return;
    var radio=document.getElementById(data.decision+'-'+iid);
    if(radio){{radio.checked=true;var row=radio.closest('.opt-row');if(row)row.classList.add('sel');}}
    if(data.decision==='other'){{
      var oi=document.getElementById('oi-'+iid);if(oi)oi.style.display='flex';
      if(data.selected_row){{var n=document.getElementById('on-'+iid);if(n)n.value=data.selected_row;}}
      if(data.selected_name){{var nm=document.getElementById('oname-'+iid);if(nm)nm.value=data.selected_name;}}
    }}
    if(data.notes){{var el=document.getElementById('notes-'+iid);if(el)el.value=data.notes;}}
    if(data.confidence){{var el=document.querySelector('[name="conf-'+iid+'"][value="'+data.confidence+'"]');if(el)el.checked=true;}}
    if(card&&data.decision)card.classList.add('done');
  }});
  refreshProgress();
}}

// ── Render on load ─────────────────────────────────────────────────────────────
function renderAll(){{
  // Pre-resolved section
  var prContainer=document.getElementById('qs-pre-resolved');
  if(prContainer){{
    var html='';
    PR_DATA.forEach(function(d,i){{html+=buildPrCard(d,i+1);}});
    prContainer.innerHTML=html;
  }}
  // Inject pre-resolved decisions into localStorage so they appear in export
  var saved=JSON.parse(localStorage.getItem(STORAGE_KEY)||'{{"responses":{{}}}}');
  PR_DATA.forEach(function(d){{
    if(!saved.responses[d.id]){{
      saved.responses[d.id]={{item_id:d.id,decision:d.decision,
        selected_row:d.decision==='other'?d.win_row:null,
        selected_name:d.decision==='other'?d.win_name:null,
        notes:'[AUTO] via '+d.rule_id+': '+d.rule_text,
        pre_resolved:true,win_row:d.win_row,win_name:d.win_name}};
    }}
  }});
  localStorage.setItem(STORAGE_KEY,JSON.stringify(saved));

  // Unresolved sections
  var byId={{}};UNRES_DATA.forEach(function(d){{byId[d.id]=d;}});
  var globalNum=1;
  SECTIONS.forEach(function(sec){{
    var container=document.getElementById('qs-'+sec.key.replace(/ /g,'_'));
    if(!container)return;
    var html='';
    sec.ids.forEach(function(id){{var d=byId[id];if(d)html+=buildCard(d,globalNum++);}});
    container.innerHTML=html;
  }});

  setupSectionToggles();
  checkRestore(STORAGE_KEY,document.getElementById('restore-banner'));
  refreshProgress();
}}
document.addEventListener('DOMContentLoaded',renderAll);
</script>
</body>
</html>"""

out1 = OUT_DIR / "GT_disputes_review.html"
out1.write_text(doc1_html, encoding="utf-8")
print(f"  Written: {out1} ({len(doc1_html)//1024}KB)")

# ── Step 4: Regenerate Golden_rule_violations_by_company.html ─────────────────
print("\nStep 4: Building updated Golden_rule_violations_by_company.html...")

# Build pre-resolved set by company
pr_by_company = {}
for pr in pre_resolved:
    co = pr["dispute"].get("company","")
    pr_by_company.setdefault(co, set()).add(pr["dispute"]["_id"])

# Group disputes by company (same as original)
company_disputes = {}
for d in DISPUTES:
    company_disputes.setdefault(d["company"], []).append(d)
companies_sorted = sorted(company_disputes.keys())

# Tab headers
tabs_html = ""
for i, co in enumerate(companies_sorted):
    active = "active" if i==0 else ""
    n = len(company_disputes[co])
    pr_n = len(pr_by_company.get(co, set()))
    tabs_html += f'<div class="tab {active}" data-tab="{esc(co)}" onclick="showTab(\'{esc(co)}\')">{esc(co.replace("_"," "))} <span style="font-size:11px;opacity:.8">({n})</span></div>'

tabs_content_html = ""
for i, co in enumerate(companies_sorted):
    active  = "active" if i==0 else ""
    disputes = company_disputes[co]
    stats   = by_company.get(co, {})
    industry = disputes[0].get("industry_type","") if disputes else ""
    pr_set  = pr_by_company.get(co, set())
    pr_count = len(pr_set)
    rows_html = ""
    for j, d in enumerate(disputes):
        row_id   = f"{co}_{j}"
        gt_name  = ROW_NAMES.get(d["gt_row"], d.get("gt_field",""))
        gr_name  = ROW_NAMES.get(d["golden_rule_row"], d.get("golden_rule_name",""))
        src      = d.get("golden_rule_source","")
        context  = d.get("document_context","")
        ctx_lbl  = "P&L" if context=="pl" else "B/S" if context=="bs" else context
        dsp_id   = d["_id"]
        is_pre   = dsp_id in pr_set

        if is_pre:
            pr_info = next((p for p in pre_resolved if p["dispute"]["_id"]==dsp_id), None)
            res_row = pr_info["resolution"]["row"] if pr_info else None
            res_name = ROW_NAMES.get(res_row,"") if res_row else ""
            resolved_cell = f"<span class='resolved-badge'>&#x2713; Row {res_row}: {esc(res_name)}</span>"
            tr_cls = "class='pre-res'"
        else:
            resolved_cell = f"""<div class="inline-radio">
              <label><input type="radio" name="v-{row_id}" value="gt" onchange="saveViol('{esc(co)}','{row_id}')"> GT</label>
              <label><input type="radio" name="v-{row_id}" value="rule" onchange="saveViol('{esc(co)}','{row_id}')"> Rule</label>
              <label><input type="radio" name="v-{row_id}" value="other" onchange="saveViol('{esc(co)}','{row_id}')"> Other:</label>
              <input type="number" class="inline-note" id="vother-{row_id}" placeholder="row" style="width:55px"
                     oninput="saveViol('{esc(co)}','{row_id}')">
            </div>"""
            tr_cls = ""

        rows_html += f"""<tr id="vrow-{row_id}" {tr_cls}>
  <td style="font-weight:700;color:#1a365d;width:32px">{j+1}</td>
  <td style="max-width:200px"><strong>{esc(d["raw_text"])}</strong><br><span style="font-size:11px;color:#718096">{esc(d.get("section",""))}</span></td>
  <td style="font-size:12px">{esc(ctx_lbl)}</td>
  <td style="white-space:nowrap"><span style="font-weight:700">Row {d["gt_row"]}</span><br><span style="font-size:11px;color:#4a5568">{esc(gt_name)}</span></td>
  <td style="white-space:nowrap"><span style="font-weight:700">Row {d["golden_rule_row"]}</span><br><span style="font-size:11px;color:#4a5568">{esc(gr_name)}</span></td>
  <td style="font-size:11px;color:#718096">{esc(src)}</td>
  <td>{resolved_cell}</td>
  <td><input type="text" class="inline-note" id="vnote-{row_id}" placeholder="notes..." oninput="saveViol('{esc(co)}','{row_id}')"></td>
</tr>"""

    remaining_n = len(disputes) - pr_count
    tabs_content_html += f"""
<div class="tab-content {active}" id="tab-{esc(co)}">
  <div style="background:#fff;padding:14px 16px;border-radius:8px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.08)">
    <div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin-bottom:10px">
      <div>
        <div style="font-size:20px;font-weight:700;color:#1a365d">{esc(co.replace("_"," "))}</div>
        <div style="font-size:12px;color:#718096">{ind_pill(industry)} &nbsp; Total disputes: {len(disputes)} &nbsp;|&nbsp; Pre-resolved: <span style="color:#276749;font-weight:600">{pr_count}</span> &nbsp;|&nbsp; Remaining: {remaining_n}</div>
      </div>
      <button class="btn btn-outline" onclick="exportCompany('{esc(co)}')">Export {esc(co)}</button>
    </div>
    <div class="pbar"><div class="pbar-fill" id="vpbar-{esc(co)}" style="width:0%"></div></div>
    <div style="font-size:12px;color:#4a5568;margin-top:4px" id="vprog-{esc(co)}">0 of {remaining_n} reviewed</div>
  </div>
  <div style="overflow-x:auto">
    <table class="violations-table">
      <thead>
        <tr>
          <th>#</th><th>Item Text / Section</th><th>Context</th>
          <th>GT Used</th><th>Golden Rule Says</th><th>Source</th>
          <th>Decision</th><th>Notes</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>
</div>"""

company_counts_remaining = {co: len(company_disputes[co]) - len(pr_by_company.get(co,set())) for co in companies_sorted}

doc3_html = f"""<!DOCTYPE html>
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
  <div class="sub">Per-company view &mdash; {num_pre} pre-resolved (green), {num_remaining} remaining</div>
</div>
<div class="top-actions">
  <div class="ca-field">
    <label>CA Name</label>
    <input type="text" id="ca-name" placeholder="Your name..." oninput="saveMeta3()">
  </div>
  <button class="btn btn-orange" onclick="exportJSON('cma_violations_v2','Violations_responses.json')">Export All JSON</button>
</div>
<div class="tabs">{tabs_html}</div>
{tabs_content_html}
</div>
<script>
const ROW_NAMES = {json.dumps(ROW_NAMES, separators=(',',':'))};
const STORAGE_KEY = 'cma_violations_v2';
const COMPANY_COUNTS = {json.dumps(company_counts_remaining, separators=(',',':'))};

{SHARED_JS}

function showTab(co){{
  document.querySelectorAll('.tab').forEach(function(t){{t.classList.toggle('active',t.dataset.tab===co);}});
  document.querySelectorAll('.tab-content').forEach(function(c){{c.classList.toggle('active',c.id==='tab-'+co);}});
}}

function saveViol(co,rowId){{
  var radio=document.querySelector('[name="v-'+rowId+'"]:checked');
  var note=(document.getElementById('vnote-'+rowId)||{{}}).value||'';
  var other=(document.getElementById('vother-'+rowId)||{{}}).value||'';
  var data={{item_id:rowId,company:co,decision:radio?radio.value:null,
    other_row:radio&&radio.value==='other'?parseInt(other)||null:null,
    other_row_name:radio&&radio.value==='other'?(ROW_NAMES[parseInt(other)]||''):'',notes:note}};
  saveResponse(STORAGE_KEY,rowId,data);
  var row=document.getElementById('vrow-'+rowId);if(row&&data.decision)row.style.background='#f0fff4';
  refreshViolProgress(co);
}}

function refreshViolProgress(co){{
  var saved=JSON.parse(localStorage.getItem(STORAGE_KEY)||'{{"responses":{{}}}}');
  var total=COMPANY_COUNTS[co]||0;
  var reviewed=0;
  Object.values(saved.responses||{{}}).forEach(function(d){{if(d.company===co&&d.decision&&!d.pre_resolved)reviewed++;}});
  var pct=total>0?Math.round((reviewed/total)*100):0;
  var pb=document.getElementById('vpbar-'+co);if(pb)pb.style.width=pct+'%';
  var pc=document.getElementById('vprog-'+co);if(pc)pc.textContent=reviewed+' of '+total+' reviewed';
}}

function exportCompany(co){{
  var saved=JSON.parse(localStorage.getItem(STORAGE_KEY)||'{{"responses":{{}}}}');
  var filtered={{}};
  Object.entries(saved.responses||{{}}).forEach(function([k,v]){{if(v.company===co)filtered[k]=v;}});
  var out={{company:co,reviewer:saved.reviewer,responses:filtered}};
  var blob=new Blob([JSON.stringify(out,null,2)],{{type:'application/json'}});
  var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='violations_'+co+'.json';a.click();
}}

function saveMeta3(){{
  var saved=JSON.parse(localStorage.getItem(STORAGE_KEY)||'{{"responses":{{}}}}');
  saved.reviewer=document.getElementById('ca-name').value;
  localStorage.setItem(STORAGE_KEY,JSON.stringify(saved));
}}

function restoreAllResponses(key){{
  var saved=JSON.parse(localStorage.getItem(key)||'{{"responses":{{}}}}');
  if(saved.reviewer){{var el=document.getElementById('ca-name');if(el)el.value=saved.reviewer;}}
  Object.entries(saved.responses||{{}}).forEach(function([rowId,data]){{
    if(data.decision){{
      var radio=document.querySelector('[name="v-'+rowId+'"][value="'+data.decision+'"]');
      if(radio)radio.checked=true;
      if(data.decision==='other'&&data.other_row){{var oi=document.getElementById('vother-'+rowId);if(oi)oi.value=data.other_row;}}
      var row=document.getElementById('vrow-'+rowId);if(row)row.style.background='#f0fff4';
    }}
    if(data.notes){{var el=document.getElementById('vnote-'+rowId);if(el)el.value=data.notes;}}
  }});
  Object.keys(COMPANY_COUNTS).forEach(function(co){{refreshViolProgress(co);}});
}}

document.addEventListener('DOMContentLoaded',function(){{
  checkRestore(STORAGE_KEY,document.getElementById('restore-banner'));
}});
</script>
</body>
</html>"""

out3 = OUT_DIR / "Golden_rule_violations_by_company.html"
out3.write_text(doc3_html, encoding="utf-8")
print(f"  Written: {out3} ({len(doc3_html)//1024}KB)")

# ── Step 5: Syntax check ───────────────────────────────────────────────────────
print("\nStep 5: Syntax checking generated files...")
import subprocess, os, tempfile
for out_file in [out1, out3]:
    content = out_file.read_text(encoding="utf-8")
    start = content.find('<script>')
    end   = content.find('</script>')
    js    = content[start+8:end]
    tmp   = os.path.join(tempfile.gettempdir(), f"check_{out_file.stem}.js")
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(js)
    result = subprocess.run(['node','--check',tmp], capture_output=True, text=True)
    status = "OK" if result.returncode == 0 else f"FAIL: {result.stderr[:300]}"
    print(f"  {out_file.name}: {status}")

# ── Summary ────────────────────────────────────────────────────────────────────
print(f"""
{'='*60}
SUMMARY
{'='*60}
Total GT disputes:        175
Pre-resolved:             {num_pre}
Remaining for CA review:  {num_remaining}

Pre-resolved breakdown (by matched rule):""")
for rid, items in sorted(by_rule.items(), key=lambda x: -len(x[1])):
    rule_obj = next((r for r in resolved_rules if r["id"]==rid), None)
    label = rule_obj["text"] if rule_obj else rid
    print(f"  {rid} '{label}': {len(items)} disputes")
print(f"""
Files written:
  {out1}
  {out3}
{'='*60}""")
