"""
Part 2: Rapidfuzz First Pass
Fuzzy match all 1,326 GT entries against combined golden rules (Source 1 + Source 2).
Produces confirmed/dispute/unverified classification for each entry.
"""
import json
import os
import re
from collections import defaultdict
from rapidfuzz import fuzz, process

BASE = os.path.dirname(os.path.abspath(__file__))
RULES_PATH = os.path.join(BASE, "CMA_Ground_Truth_v1", "reference", "cma_classification_rules.json")
CA_ANSWERS_PATH = os.path.join(BASE, "DOCS", "ca_answers_2026-03-26.json")
CANONICAL_PATH = os.path.join(BASE, "CMA_Ground_Truth_v1", "reference", "canonical_labels.json")
COMPANIES_DIR = os.path.join(BASE, "CMA_Ground_Truth_v1", "companies")
OUTPUT_PATH = os.path.join(BASE, "CMA_Ground_Truth_v1", "validation", "rapidfuzz_pass.json")

# Company metadata
COMPANY_META = {
    "BCIPL": "manufacturing",
    "Dynamic_Air": "manufacturing",
    "INPL": "manufacturing",
    "Kurunji_Retail": "trading",
    "Mehta_Computer": "trading",
    "MSL": "manufacturing",
    "SLIPL": "manufacturing",
    "SR_Papers": "manufacturing",
    "SSSS": "trading",
}

# Load data
with open(RULES_PATH, "r", encoding="utf-8") as f:
    rules_data = json.load(f)
rules = rules_data["rules"]

with open(CA_ANSWERS_PATH, "r", encoding="utf-8") as f:
    ca_data = json.load(f)
ca_answers = ca_data["answers"]

with open(CANONICAL_PATH, "r", encoding="utf-8") as f:
    canonical = json.load(f)

canonical_lookup = {c["sheet_row"]: c["name"] for c in canonical}

# =====================================================================
# Build combined golden rules lookup
# Each rule: {text, row, name, source, industry_specific, context_specific}
# =====================================================================

golden_rules = []

# Source 1: Classification rules
for r in rules:
    golden_rules.append({
        "text": r["fs_item"].lower().strip(),
        "row": r["canonical_sheet_row"],
        "name": r.get("canonical_name", ""),
        "source": f"Source1_rule_{r['rule_id']}",
        "source_sheet": r.get("source_sheet", ""),
        "industry_specific": None,
        "context_specific": None,
        "broad_classification": r.get("broad_classification", ""),
    })

# Source 2: CA answers (with proper row resolution)
for a in ca_answers:
    item_text = a["item_text"].lower().strip()

    if a.get("industry_specific"):
        # Industry-specific: add one rule per industry
        for industry, ind_data in a["industry_specific"].items():
            if ind_data.get("row"):
                golden_rules.append({
                    "text": item_text,
                    "row": ind_data["row"],
                    "name": ind_data.get("name", ""),
                    "source": f"CA_{a['question_id']}_{industry}",
                    "source_sheet": "",
                    "industry_specific": industry,
                    "context_specific": None,
                    "broad_classification": "",
                })
    elif a.get("context_specific"):
        # Context-specific: add one rule per context (P&L vs BS)
        for ctx, ctx_data in a["context_specific"].items():
            if ctx_data.get("row"):
                golden_rules.append({
                    "text": item_text,
                    "row": ctx_data["row"],
                    "name": ctx_data.get("name", ""),
                    "source": f"CA_{a['question_id']}_{ctx}",
                    "source_sheet": "",
                    "industry_specific": None,
                    "context_specific": ctx,  # "pl" or "bs"
                    "broad_classification": "",
                })
    else:
        # Determine the correct row
        if a.get("agreed_with_ai") is False and a.get("default_row"):
            row = a["default_row"]
            name = a.get("default_name", "")
            src_note = "CA_disagreed_use_default"
        elif a.get("agreed_with_ai") is True:
            row = a["ai_suggested_row"]
            name = a.get("ai_suggested_name", "")
            src_note = "CA_agreed"
        elif a.get("default_row"):
            row = a["default_row"]
            name = a.get("default_name", "")
            src_note = "default"
        elif a.get("ai_suggested_row"):
            row = a["ai_suggested_row"]
            name = a.get("ai_suggested_name", "")
            src_note = "ai_suggested_no_default"
        else:
            continue

        golden_rules.append({
            "text": item_text,
            "row": row,
            "name": name,
            "source": f"CA_{a['question_id']}_{src_note}",
            "source_sheet": "",
            "industry_specific": None,
            "context_specific": None,
            "broad_classification": "",
        })

print(f"Total combined golden rules: {len(golden_rules)}")

# Build text list for rapidfuzz
golden_texts = [r["text"] for r in golden_rules]

# =====================================================================
# Text normalization for matching
# =====================================================================

STRIP_SUFFIXES = [
    "expenses", "expense", "charges", "charge", "paid", "received",
    "payable", "receivable", "account", "a/c", "acct",
]

def normalize_text(text):
    """Normalize raw_text for better matching."""
    t = text.lower().strip()
    # Remove common parenthetical notes
    t = re.sub(r'\(.*?\)', '', t)
    # Remove special chars except &
    t = re.sub(r'[^\w\s&/]', '', t)
    # Normalize whitespace
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def determine_document_context(entry):
    """Determine if entry is from P&L or BS based on sheet_name and section."""
    sheet = entry.get("sheet_name", "").lower()
    section = entry.get("section", "").lower()
    cma_row = entry.get("cma_row", 0)

    # Row ranges: P&L = 22-108, BS = 116-258
    if cma_row and 22 <= cma_row <= 108:
        return "pl"
    elif cma_row and cma_row >= 116:
        return "bs"

    if "p & l" in sheet or "p&l" in sheet or "profit" in sheet or "loss" in sheet:
        return "pl"
    if "balance" in sheet or "b/s" in sheet:
        return "bs"

    # Section-based
    pl_keywords = ["revenue", "income", "expense", "depreciation", "interest",
                   "tax", "profit", "loss", "sales", "cost of", "employee",
                   "finance", "manufacturing", "other expenses"]
    bs_keywords = ["asset", "liability", "capital", "reserve", "loan",
                   "inventory", "debtor", "creditor", "investment", "cash",
                   "bank balance", "fixed asset", "current"]

    for kw in pl_keywords:
        if kw in section:
            return "pl"
    for kw in bs_keywords:
        if kw in section:
            return "bs"

    return "unknown"

def find_best_golden_rule(raw_text, industry, doc_context, gt_row):
    """Find the best matching golden rule for a GT entry."""
    normalized = normalize_text(raw_text)

    # Try exact match first
    exact_matches = []
    for i, rule in enumerate(golden_rules):
        if rule["text"] == normalized or rule["text"] == raw_text.lower().strip():
            exact_matches.append((rule, 100.0, i))

    # If no exact match, use rapidfuzz
    if not exact_matches:
        results = process.extract(normalized, golden_texts, scorer=fuzz.token_sort_ratio, limit=10)
        for text, score, idx in results:
            if score >= 80:
                exact_matches.append((golden_rules[idx], score, idx))

    if not exact_matches:
        # Try with raw text too
        results2 = process.extract(raw_text.lower().strip(), golden_texts, scorer=fuzz.token_sort_ratio, limit=5)
        for text, score, idx in results2:
            if score >= 80:
                exact_matches.append((golden_rules[idx], score, idx))

    if not exact_matches:
        return None, None, None

    # Filter and rank matches based on industry and context
    best_match = None
    best_score = 0
    best_idx = None

    for rule, score, idx in exact_matches:
        # Prefer industry-specific matches
        priority = score

        if rule["industry_specific"]:
            if rule["industry_specific"] == industry:
                priority += 10  # Boost for matching industry
            else:
                continue  # Skip wrong industry

        if rule["context_specific"]:
            if rule["context_specific"] == doc_context:
                priority += 10  # Boost for matching context
            elif doc_context != "unknown":
                continue  # Skip wrong context

        # Boost for source_sheet match
        if rule["source_sheet"]:
            if ("balance" in rule["source_sheet"].lower() and doc_context == "bs") or \
               ("profit" in rule["source_sheet"].lower() and doc_context == "pl"):
                priority += 5

        if priority > best_score:
            best_score = priority
            best_match = rule
            best_idx = idx

    # If no context/industry filtered match, fall back to best raw score
    if not best_match and exact_matches:
        # Pick highest fuzzy score from unfiltered
        exact_matches.sort(key=lambda x: x[1], reverse=True)
        best_match = exact_matches[0][0]
        best_score = exact_matches[0][1]
        best_idx = exact_matches[0][2]

    return best_match, best_score, best_idx

# =====================================================================
# Process all companies
# =====================================================================

all_results = []
summary = {
    "total": 0,
    "confirmed": 0,
    "dispute": 0,
    "unverified_pending_agent": 0,
    "excluded": 0,
}
by_company = {}

for company, industry in COMPANY_META.items():
    gt_path = os.path.join(COMPANIES_DIR, company, "ground_truth_corrected.json")
    if not os.path.exists(gt_path):
        print(f"  SKIP {company}: no corrected GT file")
        continue

    with open(gt_path, "r", encoding="utf-8") as f:
        gt_data = json.load(f)

    entries = gt_data.get("database_entries", [])
    company_stats = {"total": len(entries), "confirmed": 0, "dispute": 0,
                     "unverified_pending_agent": 0, "excluded": 0}

    # De-duplicate entries by (raw_text, cma_row, section) to avoid processing same item multiple years
    seen = set()
    unique_entries = []
    for entry in entries:
        key = (entry.get("raw_text", ""), entry.get("cma_row", 0), entry.get("section", ""))
        if key not in seen:
            seen.add(key)
            unique_entries.append(entry)

    for entry in unique_entries:
        raw_text = entry.get("raw_text", "")
        gt_row = entry.get("cma_row", 0)
        gt_field = entry.get("cma_field_name", "")
        section = entry.get("section", "")
        sheet_name = entry.get("sheet_name", "")
        doc_context = determine_document_context(entry)

        summary["total"] += 1
        company_stats["total"] = len(unique_entries)

        # Row 0 = excluded
        if gt_row == 0:
            status = "excluded"
            summary["excluded"] += 1
            company_stats["excluded"] += 1
            all_results.append({
                "company": company,
                "raw_text": raw_text,
                "section": section,
                "sheet_name": sheet_name,
                "gt_row": gt_row,
                "gt_field": gt_field,
                "industry_type": industry,
                "document_context": doc_context,
                "status": "excluded",
                "golden_rule_row": None,
                "golden_rule_name": None,
                "golden_rule_source": None,
                "fuzzy_score": None,
                "match_method": "excluded_row_0",
            })
            continue

        # Find best golden rule match
        best_rule, best_score, best_idx = find_best_golden_rule(raw_text, industry, doc_context, gt_row)

        if best_rule:
            golden_row = best_rule["row"]
            if golden_row == gt_row:
                status = "confirmed"
                summary["confirmed"] += 1
                company_stats["confirmed"] += 1
            else:
                status = "dispute"
                summary["dispute"] += 1
                company_stats["dispute"] += 1

            actual_score = best_score if best_score <= 100 else best_score - 10  # Remove priority boost for display

            all_results.append({
                "company": company,
                "raw_text": raw_text,
                "section": section,
                "sheet_name": sheet_name,
                "gt_row": gt_row,
                "gt_field": gt_field,
                "industry_type": industry,
                "document_context": doc_context,
                "status": status,
                "golden_rule_row": golden_row,
                "golden_rule_name": best_rule["name"],
                "golden_rule_source": best_rule["source"],
                "fuzzy_score": round(min(actual_score, 100), 1),
                "match_method": "rapidfuzz",
            })
        else:
            status = "unverified_pending_agent"
            summary["unverified_pending_agent"] += 1
            company_stats["unverified_pending_agent"] += 1
            all_results.append({
                "company": company,
                "raw_text": raw_text,
                "section": section,
                "sheet_name": sheet_name,
                "gt_row": gt_row,
                "gt_field": gt_field,
                "industry_type": industry,
                "document_context": doc_context,
                "status": "unverified_pending_agent",
                "golden_rule_row": None,
                "golden_rule_name": None,
                "golden_rule_source": None,
                "fuzzy_score": None,
                "match_method": None,
            })

    by_company[company] = company_stats
    print(f"  {company} ({industry}): {company_stats['total']} unique entries -> "
          f"confirmed={company_stats['confirmed']}, dispute={company_stats['dispute']}, "
          f"unverified={company_stats['unverified_pending_agent']}, excluded={company_stats['excluded']}")

# =====================================================================
# Save results
# =====================================================================

output = {
    "metadata": {
        "date": "2026-03-27",
        "golden_rules_count": len(golden_rules),
        "fuzzy_threshold": 80,
        "deduplicated": True,
    },
    "summary": summary,
    "by_company": by_company,
    "results": all_results,
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n=== Rapidfuzz First Pass Summary ===")
print(f"Total unique entries processed: {summary['total']}")
print(f"Confirmed: {summary['confirmed']}")
print(f"Disputes: {summary['dispute']}")
print(f"Unverified (pending agent): {summary['unverified_pending_agent']}")
print(f"Excluded (row 0): {summary['excluded']}")
print(f"\nSaved to: {OUTPUT_PATH}")

# Print disputes for review
disputes = [r for r in all_results if r["status"] == "dispute"]
if disputes:
    print(f"\n--- Top Disputes ---")
    for d in disputes[:30]:
        print(f"  [{d['company']}] '{d['raw_text']}' (section={d['section']})")
        print(f"    GT: row {d['gt_row']} ({d['gt_field']})")
        print(f"    Golden: row {d['golden_rule_row']} ({d['golden_rule_name']}) [score={d['fuzzy_score']}, src={d['golden_rule_source']}]")

# Print unverified for review
unverified = [r for r in all_results if r["status"] == "unverified_pending_agent"]
if unverified:
    print(f"\n--- Unverified Items (need agent review) ---")
    for u in unverified[:30]:
        print(f"  [{u['company']}] '{u['raw_text']}' (gt_row={u['gt_row']}, section={u['section']})")
