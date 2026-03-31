"""
Part 4: Merge and Output Final Validation Report
Combines rapidfuzz_pass.json, agent batch results, cross-check disagreements,
and runs cross-company consistency check.
"""
import json
import os
import re
from collections import defaultdict, Counter
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
VAL_DIR = os.path.join(BASE, "CMA_Ground_Truth_v1", "validation")

# Load all data sources
with open(os.path.join(VAL_DIR, "rapidfuzz_pass.json"), "r", encoding="utf-8") as f:
    rapidfuzz_data = json.load(f)

with open(os.path.join(VAL_DIR, "agent_batch1_results.json"), "r", encoding="utf-8") as f:
    agent_batch1 = json.load(f)
with open(os.path.join(VAL_DIR, "agent_batch2_results.json"), "r", encoding="utf-8") as f:
    agent_batch2 = json.load(f)
with open(os.path.join(VAL_DIR, "agent_batch3_results.json"), "r", encoding="utf-8") as f:
    agent_batch3 = json.load(f)

with open(os.path.join(VAL_DIR, "row_verification_report.json"), "r", encoding="utf-8") as f:
    cross_check_data = json.load(f)

with open(os.path.join(VAL_DIR, "rule_contradictions.json"), "r", encoding="utf-8") as f:
    contradictions_data = json.load(f)

with open(os.path.join(BASE, "CMA_Ground_Truth_v1", "reference", "canonical_labels.json"), "r", encoding="utf-8") as f:
    canonical = json.load(f)

canonical_lookup = {c["sheet_row"]: c["name"] for c in canonical}

# =====================================================================
# Step 1: Merge rapidfuzz results with agent results
# =====================================================================

# Build agent results lookup by (company, raw_text, gt_row)
agent_all = agent_batch1 + agent_batch2 + agent_batch3
agent_lookup = {}
for item in agent_all:
    key = (item["company"], item["raw_text"], item.get("gt_row", 0))
    agent_lookup[key] = item

# Process all rapidfuzz results
merged_results = []
for entry in rapidfuzz_data["results"]:
    company = entry["company"]
    raw_text = entry["raw_text"]
    gt_row = entry["gt_row"]
    status = entry["status"]

    if status == "unverified_pending_agent":
        # Replace with agent result
        key = (company, raw_text, gt_row)
        agent_result = agent_lookup.get(key)
        if agent_result:
            merged_entry = {
                "company": company,
                "raw_text": raw_text,
                "section": entry.get("section", ""),
                "sheet_name": entry.get("sheet_name", ""),
                "gt_row": gt_row,
                "gt_field": entry.get("gt_field", agent_result.get("gt_field", "")),
                "industry_type": entry.get("industry_type", ""),
                "document_context": entry.get("document_context", ""),
                "status": agent_result["status"],
                "golden_rule_row": agent_result.get("golden_rule_row"),
                "golden_rule_name": agent_result.get("golden_rule_name"),
                "golden_rule_source": agent_result.get("golden_rule_source", "agent_reasoning"),
                "match_method": "agent_reasoning",
                "fuzzy_score": None,
                "agent_reasoning": agent_result.get("agent_reasoning", ""),
            }
            merged_results.append(merged_entry)
        else:
            # No agent result found — mark as truly_unverified
            entry["status"] = "truly_unverified"
            entry["match_method"] = "no_match"
            merged_results.append(entry)
    else:
        # Keep rapidfuzz result as-is
        entry["agent_reasoning"] = None
        merged_results.append(entry)

print(f"Merged results: {len(merged_results)} entries")

# =====================================================================
# Step 2: Add cross-check disagreements as additional disputes
# =====================================================================

cross_check_disputes = []
for company, company_data in cross_check_data.get("companies", {}).items():
    cc = company_data.get("cross_check")
    if not cc or not cc.get("disagree_details"):
        continue
    for d in cc["disagree_details"]:
        cross_check_disputes.append({
            "company": company,
            "raw_text": d["raw_text"],
            "financial_year": d.get("financial_year"),
            "location_a_row": d["location_a_row"],
            "location_b_row": d["location_b_row"],
            "source": "cross_check_step1",
        })

print(f"Cross-check disagreements to incorporate: {len(cross_check_disputes)}")

# Check if cross-check disputes are already captured in merged results
new_cross_check_disputes = []
for cc_dispute in cross_check_disputes:
    already_captured = False
    for r in merged_results:
        if (r["company"] == cc_dispute["company"] and
            r["raw_text"] == cc_dispute["raw_text"] and
            r["status"] == "dispute"):
            already_captured = True
            break
    if not already_captured:
        new_cross_check_disputes.append(cc_dispute)

print(f"New cross-check disputes (not already in merged): {len(new_cross_check_disputes)}")

# =====================================================================
# Step 3: Cross-company consistency check
# =====================================================================

def normalize_for_grouping(text):
    """Normalize text for cross-company grouping."""
    t = text.lower().strip()
    t = re.sub(r'\(.*?\)', '', t)
    t = re.sub(r'[^\w\s&/]', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    # Remove common prefixes like (a), (b), (i), (ii) etc.
    t = re.sub(r'^[\(\)a-z0-9]+\s+', '', t)
    return t

# Group by normalized text + industry
text_industry_groups = defaultdict(list)
for r in merged_results:
    normalized = normalize_for_grouping(r["raw_text"])
    if not normalized or len(normalized) < 3:
        continue
    key = (normalized, r["industry_type"])
    text_industry_groups[key].append({
        "company": r["company"],
        "raw_text": r["raw_text"],
        "gt_row": r["gt_row"],
        "gt_field": r.get("gt_field", ""),
        "section": r.get("section", ""),
        "status": r["status"],
    })

cross_company_inconsistencies = []
for (text, industry), items in text_industry_groups.items():
    if len(items) < 2:
        continue
    rows = set(item["gt_row"] for item in items)
    if len(rows) > 1:
        cross_company_inconsistencies.append({
            "normalized_text": text,
            "industry_type": industry,
            "rows_found": sorted(list(rows)),
            "companies": [
                {"company": item["company"], "raw_text": item["raw_text"],
                 "gt_row": item["gt_row"], "section": item["section"]}
                for item in items
            ],
        })

print(f"Cross-company inconsistencies: {len(cross_company_inconsistencies)}")

# =====================================================================
# Step 4: Compile final statistics
# =====================================================================

status_counts = Counter(r["status"] for r in merged_results)
by_company = defaultdict(lambda: {"total": 0, "confirmed": 0, "dispute": 0,
                                    "truly_unverified": 0, "excluded": 0})

for r in merged_results:
    co = r["company"]
    by_company[co]["total"] += 1
    by_company[co][r["status"]] += 1

# Collect all disputes with full details
all_disputes = []
for r in merged_results:
    if r["status"] == "dispute":
        all_disputes.append({
            "company": r["company"],
            "raw_text": r["raw_text"],
            "section": r.get("section", ""),
            "gt_row": r["gt_row"],
            "gt_field": r.get("gt_field", ""),
            "golden_rule_row": r.get("golden_rule_row"),
            "golden_rule_name": r.get("golden_rule_name", ""),
            "golden_rule_source": r.get("golden_rule_source", ""),
            "industry_type": r.get("industry_type", ""),
            "document_context": r.get("document_context", ""),
            "match_method": r.get("match_method", ""),
            "fuzzy_score": r.get("fuzzy_score"),
            "agent_reasoning": r.get("agent_reasoning"),
        })

# Add new cross-check disputes
for cc in new_cross_check_disputes:
    all_disputes.append({
        "company": cc["company"],
        "raw_text": cc["raw_text"],
        "section": "",
        "gt_row": cc["location_a_row"],
        "gt_field": canonical_lookup.get(cc["location_a_row"], ""),
        "golden_rule_row": cc["location_b_row"],
        "golden_rule_name": canonical_lookup.get(cc["location_b_row"], ""),
        "golden_rule_source": "cross_check_step1",
        "industry_type": "",
        "document_context": "",
        "match_method": "cross_check",
        "fuzzy_score": None,
        "agent_reasoning": f"Location A (GT) says row {cc['location_a_row']}, Location B says row {cc['location_b_row']} for FY {cc.get('financial_year', 'unknown')}",
    })

truly_unverified = [r for r in merged_results if r["status"] == "truly_unverified"]

# =====================================================================
# Step 5: Build final output
# =====================================================================

final_output = {
    "metadata": {
        "date": "2026-03-27",
        "description": "Cross-validation of GT against 450+ golden rules (Source 1 + Source 2 + CA answers)",
        "methodology": "3-pass: rapidfuzz (threshold 80) -> agent CA reasoning -> cross-company consistency",
        "total_golden_rules": 481,
        "rule_contradictions_found": contradictions_data["metadata"]["total_cross_contradictions"],
    },
    "summary": {
        "total_entries": len(merged_results),
        "confirmed": status_counts.get("confirmed", 0),
        "disputes": status_counts.get("dispute", 0) + len(new_cross_check_disputes),
        "truly_unverified": status_counts.get("truly_unverified", 0),
        "excluded": status_counts.get("excluded", 0),
        "cross_company_inconsistencies": len(cross_company_inconsistencies),
        "cross_check_disputes_added": len(new_cross_check_disputes),
        "rule_contradictions_count": contradictions_data["metadata"]["total_cross_contradictions"],
    },
    "by_company": dict(by_company),
    "disputes": all_disputes,
    "truly_unverified": truly_unverified,
    "cross_company_inconsistencies": cross_company_inconsistencies,
    "new_cross_check_disputes": new_cross_check_disputes,
}

# Save final JSON
output_path = os.path.join(VAL_DIR, "gt_validation_final.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(final_output, f, indent=2, ensure_ascii=False)
print(f"\nSaved: {output_path}")

# =====================================================================
# Step 6: Generate human-readable summary
# =====================================================================

# Count disputes by type pattern
dispute_patterns = Counter()
for d in all_disputes:
    if d.get("golden_rule_row") and d.get("gt_row"):
        pattern = f"GT={d['gt_row']} vs Golden={d['golden_rule_row']}"
        dispute_patterns[pattern] += 1

summary_md = f"""# GT Validation Final Summary

**Date:** 2026-03-27
**Methodology:** 3-pass validation (rapidfuzz threshold=80 -> agent CA reasoning -> cross-company consistency)
**Golden Rules:** 481 combined (398 from CMA Classification XLS + 69 CA answers + 14 CA-verified rules)

---

## Overall Summary

| Metric | Count | % |
|--------|-------|---|
| **Total unique entries** | {len(merged_results)} | 100% |
| **Confirmed** | {status_counts.get('confirmed', 0)} | {status_counts.get('confirmed', 0) * 100 / len(merged_results):.1f}% |
| **Disputes** | {status_counts.get('dispute', 0) + len(new_cross_check_disputes)} | {(status_counts.get('dispute', 0) + len(new_cross_check_disputes)) * 100 / len(merged_results):.1f}% |
| **Truly Unverified** | {status_counts.get('truly_unverified', 0)} | {status_counts.get('truly_unverified', 0) * 100 / len(merged_results):.1f}% |
| **Excluded (row 0)** | {status_counts.get('excluded', 0)} | {status_counts.get('excluded', 0) * 100 / len(merged_results):.1f}% |
| **Cross-company inconsistencies** | {len(cross_company_inconsistencies)} | - |
| **Rule contradictions (golden vs golden)** | {contradictions_data['metadata']['total_cross_contradictions']} | - |

### Match Method Breakdown

| Method | Confirmed | Dispute |
|--------|-----------|---------|
| Rapidfuzz | {sum(1 for r in merged_results if r['status']=='confirmed' and r.get('match_method')=='rapidfuzz')} | {sum(1 for r in merged_results if r['status']=='dispute' and r.get('match_method')=='rapidfuzz')} |
| Agent Reasoning | {sum(1 for r in merged_results if r['status']=='confirmed' and r.get('match_method')=='agent_reasoning')} | {sum(1 for r in merged_results if r['status']=='dispute' and r.get('match_method')=='agent_reasoning')} |
| Cross-check | - | {len(new_cross_check_disputes)} |

---

## Per-Company Breakdown

| Company | Industry | Total | Confirmed | Disputes | Unverified | Excluded |
|---------|----------|-------|-----------|----------|------------|----------|
"""

for co in ["BCIPL", "Dynamic_Air", "INPL", "Kurunji_Retail", "Mehta_Computer", "MSL", "SLIPL", "SR_Papers", "SSSS"]:
    stats = by_company.get(co, {})
    industry = {"BCIPL": "mfg", "Dynamic_Air": "mfg", "INPL": "mfg",
                "Kurunji_Retail": "trading", "Mehta_Computer": "trading",
                "MSL": "mfg", "SLIPL": "mfg", "SR_Papers": "mfg", "SSSS": "trading"}.get(co, "?")
    summary_md += f"| {co} | {industry} | {stats.get('total', 0)} | {stats.get('confirmed', 0)} | {stats.get('dispute', 0)} | {stats.get('truly_unverified', 0)} | {stats.get('excluded', 0)} |\n"

summary_md += f"""
---

## Rule Contradictions (Golden Rules Disagreeing With Each Other)

Found **{contradictions_data['metadata']['total_cross_contradictions']} cross-source contradictions** and **{contradictions_data['metadata']['total_internal_contradictions']} internal contradictions**.

### Key Cross-Source Contradictions:
"""

for c in contradictions_data.get("cross_source_contradictions", [])[:10]:
    summary_md += f"- **{c['ca_item_text']}** ({c['industry']}): CA says row {c['ca_row']} ({c['ca_name']}), Source 1 says row {c['rule_row']} ({c['rule_name']})\n"

summary_md += f"""
### Incomplete Rules (CA has industry split, Source 1 doesn't):
"""
for c in contradictions_data.get("incomplete_rules", []):
    summary_md += f"- **{c['ca_item_text']}**: Rule gives single row {c['rule_row']}, CA splits by industry: {c['ca_industry_rows']}\n"

summary_md += f"""
---

## Top 20 Most Common Disputes

"""

# Group disputes by (raw_text pattern, gt_row vs golden_row)
dispute_groups = defaultdict(list)
for d in all_disputes:
    key = (d.get("raw_text", "").lower().strip(), d.get("gt_row"), d.get("golden_rule_row"))
    dispute_groups[key].append(d)

sorted_dispute_groups = sorted(dispute_groups.items(), key=lambda x: -len(x[1]))

for i, ((text, gt_row, golden_row), items) in enumerate(sorted_dispute_groups[:20], 1):
    companies = ", ".join(set(d["company"] for d in items))
    reasoning = items[0].get("agent_reasoning") or items[0].get("golden_rule_source", "")
    gt_name = canonical_lookup.get(gt_row, "?")
    golden_name = canonical_lookup.get(golden_row, "?") if golden_row else "?"
    summary_md += f"{i}. **\"{text}\"** (x{len(items)} across {companies})\n"
    summary_md += f"   - GT: row {gt_row} ({gt_name}) vs Golden: row {golden_row} ({golden_name})\n"
    if reasoning:
        summary_md += f"   - Reasoning: {reasoning[:120]}\n"
    summary_md += "\n"

summary_md += f"""---

## Cross-Company Inconsistencies

Found **{len(cross_company_inconsistencies)}** cases where the same text + industry has different GT rows across companies.

"""

for inc in cross_company_inconsistencies[:20]:
    summary_md += f"### \"{inc['normalized_text']}\" ({inc['industry_type']})\n"
    summary_md += f"Rows found: {inc['rows_found']}\n"
    for c in inc["companies"]:
        summary_md += f"- {c['company']}: row {c['gt_row']} (section: {c['section']})\n"
    summary_md += "\n"

if len(cross_company_inconsistencies) > 20:
    summary_md += f"... and {len(cross_company_inconsistencies) - 20} more inconsistencies.\n\n"

summary_md += f"""---

## Truly Unverified Items

Found **{len(truly_unverified)}** items with no golden rule match.

"""

for item in truly_unverified[:30]:
    summary_md += f"- [{item['company']}] \"{item['raw_text']}\" (gt_row={item['gt_row']}, section={item.get('section', '')})\n"

summary_md += f"""
---

## All Disputes Detail ({len(all_disputes)} total)

"""

for i, d in enumerate(all_disputes, 1):
    summary_md += f"**{i}. [{d['company']}] \"{d['raw_text']}\"**\n"
    summary_md += f"   GT: row {d['gt_row']} ({d.get('gt_field', '')})\n"
    golden_row = d.get('golden_rule_row', '?')
    golden_name = d.get('golden_rule_name', '')
    summary_md += f"   Golden: row {golden_row} ({golden_name})\n"
    summary_md += f"   Source: {d.get('golden_rule_source', '')} | Method: {d.get('match_method', '')}\n"
    if d.get('agent_reasoning'):
        summary_md += f"   Reasoning: {d['agent_reasoning'][:200]}\n"
    summary_md += "\n"

# Save summary
summary_path = os.path.join(VAL_DIR, "GT_VALIDATION_FINAL_SUMMARY.md")
with open(summary_path, "w", encoding="utf-8") as f:
    f.write(summary_md)
print(f"Saved: {summary_path}")

# =====================================================================
# Print final console summary
# =====================================================================

print(f"\n{'='*60}")
print(f"GT VALIDATION COMPLETE")
print(f"{'='*60}")
print(f"Total unique entries: {len(merged_results)}")
print(f"Confirmed:           {status_counts.get('confirmed', 0)} ({status_counts.get('confirmed', 0)*100/len(merged_results):.1f}%)")
print(f"Disputes:            {status_counts.get('dispute', 0) + len(new_cross_check_disputes)} ({(status_counts.get('dispute', 0) + len(new_cross_check_disputes))*100/len(merged_results):.1f}%)")
print(f"Truly Unverified:    {status_counts.get('truly_unverified', 0)}")
print(f"Excluded:            {status_counts.get('excluded', 0)}")
print(f"Cross-co inconsist.: {len(cross_company_inconsistencies)}")
print(f"Rule contradictions: {contradictions_data['metadata']['total_cross_contradictions']}")
print(f"{'='*60}")
