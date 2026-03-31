"""
Part 1: Find Rule Contradictions (Golden Rules vs Golden Rules)
Compares Source 1 (398 classification rules) against Source 2 (68 CA answers)
to find contradictions, incomplete rules, and internal inconsistencies.
"""
import json
import sys
import os

try:
    from rapidfuzz import fuzz, process
except ImportError:
    os.system("pip install rapidfuzz")
    from rapidfuzz import fuzz, process

BASE = os.path.dirname(os.path.abspath(__file__))
RULES_PATH = os.path.join(BASE, "CMA_Ground_Truth_v1", "reference", "cma_classification_rules.json")
CA_ANSWERS_PATH = os.path.join(BASE, "DOCS", "ca_answers_2026-03-26.json")
CANONICAL_PATH = os.path.join(BASE, "CMA_Ground_Truth_v1", "reference", "canonical_labels.json")
OUTPUT_DIR = os.path.join(BASE, "CMA_Ground_Truth_v1", "validation")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "rule_contradictions.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load data
with open(RULES_PATH, "r", encoding="utf-8") as f:
    rules_data = json.load(f)
rules = rules_data["rules"]

with open(CA_ANSWERS_PATH, "r", encoding="utf-8") as f:
    ca_data = json.load(f)
ca_answers = ca_data["answers"]

with open(CANONICAL_PATH, "r", encoding="utf-8") as f:
    canonical = json.load(f)

# Build canonical lookup
canonical_lookup = {c["sheet_row"]: c["name"] for c in canonical}

# Build rules lookup by fs_item text (lowercased)
rule_texts = [(r["fs_item"].lower().strip(), r) for r in rules]
rule_text_list = [t[0] for t in rule_texts]

def get_ca_answer_row(answer, industry=None):
    """Determine the correct row for a CA answer given industry context."""
    # If industry_specific exists and industry is provided, use that
    if answer.get("industry_specific") and industry:
        ind_data = answer["industry_specific"].get(industry)
        if ind_data:
            return ind_data["row"], ind_data["name"], f"industry_specific[{industry}]"

    # If agreed_with_ai is False, use default_row
    if answer.get("agreed_with_ai") is False:
        if answer.get("default_row"):
            return answer["default_row"], answer.get("default_name", ""), "default_row (CA disagreed)"

    # If agreed_with_ai is True, use ai_suggested_row
    if answer.get("agreed_with_ai") is True:
        return answer["ai_suggested_row"], answer.get("ai_suggested_name", ""), "ai_suggested (CA agreed)"

    # If default_row exists, use it
    if answer.get("default_row"):
        return answer["default_row"], answer.get("default_name", ""), "default_row"

    # Fallback to ai_suggested
    if answer.get("ai_suggested_row"):
        return answer["ai_suggested_row"], answer.get("ai_suggested_name", ""), "ai_suggested (no default)"

    return None, None, "no_row"

# === PART A: Cross-source contradictions (Source 2 vs Source 1) ===
cross_contradictions = []
incomplete_rules = []
ca_matches = []

for answer in ca_answers:
    item_text = answer["item_text"].lower().strip()
    qid = answer["question_id"]

    # Fuzzy match against Source 1 rules
    matches = process.extract(item_text, rule_text_list, scorer=fuzz.token_sort_ratio, limit=5)

    best_matches = [(m[0], m[1], m[2]) for m in matches if m[1] >= 75]  # (text, score, index)

    if not best_matches:
        continue

    for match_text, score, idx in best_matches:
        rule = rule_texts[idx][1]
        rule_row = rule["canonical_sheet_row"]
        rule_source_sheet = rule["source_sheet"]

        # Check for each industry type
        industries_to_check = ["manufacturing", "trading", "services"]

        if answer.get("industry_specific"):
            for industry in industries_to_check:
                ca_row, ca_name, source = get_ca_answer_row(answer, industry)
                if ca_row and ca_row != rule_row:
                    cross_contradictions.append({
                        "question_id": qid,
                        "ca_item_text": answer["item_text"],
                        "rule_fs_item": rule["fs_item"],
                        "fuzzy_score": score,
                        "industry": industry,
                        "ca_row": ca_row,
                        "ca_name": ca_name,
                        "ca_source": source,
                        "rule_row": rule_row,
                        "rule_name": rule.get("canonical_name", ""),
                        "rule_id": rule["rule_id"],
                        "rule_source_sheet": rule_source_sheet,
                        "type": "cross_source_contradiction"
                    })
        else:
            # No industry split in CA answer - check default
            ca_row, ca_name, source = get_ca_answer_row(answer)
            if ca_row and ca_row != rule_row:
                cross_contradictions.append({
                    "question_id": qid,
                    "ca_item_text": answer["item_text"],
                    "rule_fs_item": rule["fs_item"],
                    "fuzzy_score": score,
                    "industry": "all",
                    "ca_row": ca_row,
                    "ca_name": ca_name,
                    "ca_source": source,
                    "rule_row": rule_row,
                    "rule_name": rule.get("canonical_name", ""),
                    "rule_id": rule["rule_id"],
                    "rule_source_sheet": rule_source_sheet,
                    "type": "cross_source_contradiction"
                })

        ca_matches.append({
            "question_id": qid,
            "ca_item_text": answer["item_text"],
            "rule_fs_item": rule["fs_item"],
            "score": score,
            "matched": True
        })

    # Check for INCOMPLETE RULES: CA answer has industry_specific but Source 1 gives only ONE row
    if answer.get("industry_specific"):
        ca_industries = answer["industry_specific"]
        ca_rows_by_industry = {}
        for ind, ind_data in ca_industries.items():
            if ind_data.get("row"):
                ca_rows_by_industry[ind] = ind_data["row"]

        unique_ca_rows = set(ca_rows_by_industry.values())

        if len(unique_ca_rows) > 1:
            # CA says different industries get different rows
            for match_text, score, idx in best_matches:
                rule = rule_texts[idx][1]
                rule_row = rule["canonical_sheet_row"]
                # Source 1 gives only one row - is it missing the industry split?
                incomplete_rules.append({
                    "question_id": qid,
                    "ca_item_text": answer["item_text"],
                    "rule_fs_item": rule["fs_item"],
                    "fuzzy_score": score,
                    "rule_row": rule_row,
                    "rule_id": rule["rule_id"],
                    "ca_industry_rows": ca_rows_by_industry,
                    "type": "incomplete_rule_no_industry_split"
                })

# === PART B: Internal contradictions within Source 1 ===
internal_contradictions = []

# Group rules by similar text
from collections import defaultdict
text_to_rules = defaultdict(list)
for r in rules:
    text_to_rules[r["fs_item"].lower().strip()].append(r)

# Check for exact-text duplicates with different rows (same source sheet)
for text, rule_list in text_to_rules.items():
    if len(rule_list) > 1:
        # Group by source_sheet
        by_sheet = defaultdict(list)
        for r in rule_list:
            by_sheet[r["source_sheet"]].append(r)

        for sheet, sheet_rules in by_sheet.items():
            rows = set(r["canonical_sheet_row"] for r in sheet_rules)
            if len(rows) > 1:
                internal_contradictions.append({
                    "fs_item": text,
                    "source_sheet": sheet,
                    "conflicting_rules": [
                        {"rule_id": r["rule_id"], "row": r["canonical_sheet_row"],
                         "canonical_name": r.get("canonical_name", ""),
                         "broad_classification": r.get("broad_classification", "")}
                        for r in sheet_rules
                    ],
                    "type": "internal_exact_duplicate_different_row"
                })

# Fuzzy check: similar texts (score >= 90) with different rows in same sheet
checked_pairs = set()
for i, (text_i, rule_i) in enumerate(rule_texts):
    for j, (text_j, rule_j) in enumerate(rule_texts):
        if i >= j:
            continue
        pair_key = tuple(sorted([str(rule_i["rule_id"]), str(rule_j["rule_id"])]))
        if pair_key in checked_pairs:
            continue

        if rule_i["source_sheet"] != rule_j["source_sheet"]:
            continue

        if rule_i["canonical_sheet_row"] == rule_j["canonical_sheet_row"]:
            continue

        score = fuzz.token_sort_ratio(text_i, text_j)
        if score >= 90:
            checked_pairs.add(pair_key)
            internal_contradictions.append({
                "rule_1": {"rule_id": rule_i["rule_id"], "fs_item": rule_i["fs_item"],
                          "row": rule_i["canonical_sheet_row"], "canonical_name": rule_i.get("canonical_name", "")},
                "rule_2": {"rule_id": rule_j["rule_id"], "fs_item": rule_j["fs_item"],
                          "row": rule_j["canonical_sheet_row"], "canonical_name": rule_j.get("canonical_name", "")},
                "fuzzy_score": score,
                "source_sheet": rule_i["source_sheet"],
                "type": "internal_similar_different_row"
            })

# === Output ===
result = {
    "metadata": {
        "date": "2026-03-27",
        "source_1_rules": len(rules),
        "source_2_answers": len(ca_answers),
        "total_cross_contradictions": len(cross_contradictions),
        "total_incomplete_rules": len(incomplete_rules),
        "total_internal_contradictions": len(internal_contradictions)
    },
    "cross_source_contradictions": cross_contradictions,
    "incomplete_rules": incomplete_rules,
    "internal_contradictions": internal_contradictions
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"\n=== Rule Contradictions Report ===")
print(f"Source 1 rules: {len(rules)}")
print(f"Source 2 CA answers: {len(ca_answers)}")
print(f"Cross-source contradictions: {len(cross_contradictions)}")
print(f"Incomplete rules (no industry split): {len(incomplete_rules)}")
print(f"Internal contradictions (Source 1): {len(internal_contradictions)}")
print(f"\nSaved to: {OUTPUT_PATH}")

# Print details
if cross_contradictions:
    print(f"\n--- Cross-Source Contradictions ---")
    for c in cross_contradictions[:20]:
        print(f"  {c['question_id']}: '{c['ca_item_text']}' ~ '{c['rule_fs_item']}' (score={c['fuzzy_score']})")
        print(f"    CA says row {c['ca_row']} ({c['ca_name']}) [{c['ca_source']}]")
        print(f"    Rule says row {c['rule_row']} ({c['rule_name']}) [rule_id={c['rule_id']}]")
        print(f"    Industry: {c['industry']}")

if incomplete_rules:
    print(f"\n--- Incomplete Rules (Missing Industry Split) ---")
    for c in incomplete_rules[:10]:
        print(f"  {c['question_id']}: '{c['ca_item_text']}' ~ '{c['rule_fs_item']}' (score={c['fuzzy_score']})")
        print(f"    Rule gives single row: {c['rule_row']}")
        print(f"    CA gives industry-specific: {c['ca_industry_rows']}")

if internal_contradictions:
    print(f"\n--- Internal Contradictions (Source 1) ---")
    for c in internal_contradictions[:10]:
        if c["type"] == "internal_exact_duplicate_different_row":
            print(f"  '{c['fs_item']}' ({c['source_sheet']}): {[r['row'] for r in c['conflicting_rules']]}")
        else:
            print(f"  Rule {c['rule_1']['rule_id']} '{c['rule_1']['fs_item']}' (row {c['rule_1']['row']}) vs")
            print(f"  Rule {c['rule_2']['rule_id']} '{c['rule_2']['fs_item']}' (row {c['rule_2']['row']}) score={c['fuzzy_score']}")
