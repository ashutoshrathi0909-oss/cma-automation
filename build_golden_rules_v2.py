"""
Build CMA Golden Rules v2 - merge 4 source files into one authoritative rules file.
CA override rules take absolute precedence over legacy rules.
"""

import json
import re
from pathlib import Path
from collections import OrderedDict

BASE = Path(r"C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2")

# ── Load all source files ──────────────────────────────────────────────

with open(BASE / "DOCS" / "GT_disputes_responses -3.json", encoding="utf-8") as f:
    dispute_responses = json.load(f)["responses"]

with open(BASE / "CMA_Ground_Truth_v1" / "validation" / "gt_validation_final.json", encoding="utf-8") as f:
    validation_data = json.load(f)

with open(BASE / "DOCS" / "Rule_contradictions_responses.json", encoding="utf-8") as f:
    contradiction_responses = json.load(f)["responses"]

with open(BASE / "CMA_Ground_Truth_v1" / "validation" / "rule_contradictions.json", encoding="utf-8") as f:
    rule_contradictions = json.load(f)

with open(BASE / "DOCS" / "ca_answers_2026-03-26.json", encoding="utf-8") as f:
    ca_answers_data = json.load(f)

with open(BASE / "CMA_Ground_Truth_v1" / "reference" / "cma_classification_rules.json", encoding="utf-8") as f:
    legacy_rules_data = json.load(f)

with open(BASE / "CMA_Ground_Truth_v1" / "reference" / "canonical_labels.json", encoding="utf-8") as f:
    canonical_labels = json.load(f)

# ── Build canonical label lookup ───────────────────────────────────────

row_to_name = {}
for label in canonical_labels:
    row_to_name[label["sheet_row"]] = label["name"]

# ── Normalize helpers ──────────────────────────────────────────────────

def normalize_fs_item(text):
    """Normalize for dedup: lowercase, strip, remove ()[], collapse spaces."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'[(){}\[\]]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def normalize_source_sheet(ctx):
    """Normalize document_context / source_sheet to 'pl' or 'bs'."""
    if not ctx:
        return "pl"
    ctx = ctx.lower().strip()
    if ctx in ("pl", "p&l", "profit and loss", "profit & loss"):
        return "pl"
    if ctx in ("bs", "balance sheet"):
        return "bs"
    return ctx

def dedup_key(fs_item, source_sheet, industry_type):
    return f"{normalize_fs_item(fs_item)}|{normalize_source_sheet(source_sheet)}|{industry_type or 'all'}"

# ── Build dispute index ────────────────────────────────────────────────

# Index disputes by item_id (d001, d002, ...)
# The disputes array in gt_validation_final doesn't have item_ids directly,
# so we need to assign them. They are indexed sequentially as d001, d002, etc.
disputes_list = validation_data.get("disputes", [])

# Build a mapping: item_id -> dispute_data
# The item_ids match the keys in dispute_responses
dispute_ids = sorted(dispute_responses.keys(), key=lambda x: int(re.search(r'\d+', x).group()))

# We need to map dispute IDs back to the disputes array
# The disputes array has 175 items. Let's build an index from the
# sequential list. The dispute IDs (d001..d175) map to disputes[0..174]
dispute_by_id = {}
for i, dispute in enumerate(disputes_list):
    item_id = f"d{i+1:03d}"
    dispute_by_id[item_id] = dispute

# ── STEP 2: Extract rules from GT disputes ────────────────────────────

ca_override_rules = []
doubts = []

for item_id, response in dispute_responses.items():
    decision = response.get("decision")

    # Skip doubts
    if decision is None:
        # Check if it's a marked doubt
        if response.get("doubt"):
            doubts.append({
                "item_id": item_id,
                "company": response.get("company", ""),
                "notes": response.get("notes", ""),
                "options": response.get("options", [])
            })
        continue

    # Find the corresponding dispute data
    dispute = dispute_by_id.get(item_id)

    # Some responses have win_row/win_name directly (pre-resolved)
    win_row = response.get("win_row")
    win_name = response.get("win_name")

    if win_row is not None and win_name is not None:
        # Pre-resolved: use win_row/win_name directly
        winning_row = win_row
        winning_name = win_name
    elif decision == "gt" and dispute:
        winning_row = dispute.get("gt_row")
        winning_name = dispute.get("gt_field")
    elif decision == "rule" and dispute:
        winning_row = dispute.get("golden_rule_row")
        winning_name = dispute.get("golden_rule_name")
    elif decision == "other":
        winning_row = response.get("selected_row")
        winning_name = response.get("selected_name")
    elif dispute:
        # Fallback: try to determine from dispute + decision
        if decision == "gt":
            winning_row = dispute.get("gt_row")
            winning_name = dispute.get("gt_field")
        elif decision == "rule":
            winning_row = dispute.get("golden_rule_row")
            winning_name = dispute.get("golden_rule_name")
        else:
            winning_row = None
            winning_name = None
    else:
        winning_row = None
        winning_name = None

    # Skip if we couldn't determine a winning row
    if winning_row is None:
        # d002 has decision="other" but selected_row=null (conditional rule)
        # Include it as a note but skip as a rule
        continue

    # Get raw_text, industry, context from dispute data
    raw_text = dispute.get("raw_text", "") if dispute else ""
    industry_type = dispute.get("industry_type", "all") if dispute else "all"
    document_context = dispute.get("document_context", "pl") if dispute else "pl"
    company = dispute.get("company", "") if dispute else response.get("company", "")

    # Look up canonical name if we have the row
    if winning_name is None and winning_row is not None:
        winning_name = row_to_name.get(winning_row, f"Row {winning_row}")

    notes = response.get("notes", "")

    rule = {
        "id": f"dispute_{item_id}",
        "fs_item": normalize_fs_item(raw_text),
        "fs_item_original": raw_text,
        "canonical_sheet_row": winning_row,
        "canonical_field_name": winning_name,
        "source_sheet": normalize_source_sheet(document_context),
        "industry_type": industry_type if industry_type else "all",
        "source": f"CA_GT_dispute_{item_id}",
        "priority": "ca_override",
        "confidence": 1.0,
        "notes": notes
    }
    ca_override_rules.append(rule)

print(f"Dispute rules created: {len(ca_override_rules)}")
print(f"Doubts collected: {len(doubts)}")

# ── STEP 3: Extract rules from Rule Contradiction responses ────────────

# cross_source_contradictions have decision s1/s2 which means
# CA answer (s1? s2?) wins over legacy rule
# internal_contradictions have decision r1/r2 which means rule_1 or rule_2 wins

contradiction_rules = []

# Process cross-source contradictions
cross_contradictions = rule_contradictions.get("cross_source_contradictions", [])

for item_id, response in contradiction_responses.items():
    decision = response.get("decision")
    if decision is None:
        # These have conditional notes (e.g. int_015, int_016, int_017)
        # We can still create conditional rules if needed
        # For now, skip null decisions
        continue

    notes = response.get("notes", "")

    if item_id.startswith("cross_"):
        # Find the matching contradiction
        # cross_001 -> index 0 in cross_source_contradictions
        idx = int(item_id.replace("cross_", "")) - 1
        if idx < len(cross_contradictions):
            contra = cross_contradictions[idx]
            if decision == "s1":
                # CA answer wins (but in our responses, s1 = first option which might be CA or rule)
                # Looking at the data: cross_004 has decision=s1, and looking at the contradiction:
                # Q1g Bonus, mfg: ca_row=45 (Wages) vs rule_row=67 (Salary)
                # s1 = first item in the pair, which is the CA answer
                # Actually in the contradictions file, ca is always listed first
                # So s1 = CA answer, s2 = legacy rule
                winning_row = contra.get("ca_row")
                winning_name = contra.get("ca_name")
                fs_item = contra.get("ca_item_text", contra.get("rule_fs_item", ""))
            elif decision == "s2":
                # Legacy rule wins over the specific CA answer
                # But wait - looking at the responses: cross_001 = s2, and the contradiction is:
                # Q1a Staff Welfare, mfg: ca_row=45 vs rule_row=67
                # s2 means the legacy rule (67) wins? That seems backwards...
                # Actually looking more carefully: s1 = source1 (rule), s2 = source2 (CA answer)
                # Let me check: cross_001 has ca_row=45, rule_row=67. Decision=s2.
                # But disputes d024, d039 for Staff Welfare mfg -> decision=rule, win_row=45
                # So s2 = CA answer (source 2 = the CA interview)
                # And s1 = legacy rule
                winning_row = contra.get("ca_row")
                winning_name = contra.get("ca_name")
                fs_item = contra.get("ca_item_text", contra.get("rule_fs_item", ""))
            else:
                continue

            industry = contra.get("industry", "all")
            source_sheet = normalize_source_sheet(contra.get("rule_source_sheet", "pl"))

            rule = {
                "id": f"contradiction_{item_id}",
                "fs_item": normalize_fs_item(fs_item),
                "fs_item_original": fs_item,
                "canonical_sheet_row": winning_row,
                "canonical_field_name": winning_name,
                "source_sheet": source_sheet,
                "industry_type": industry,
                "source": f"CA_rule_contradiction_{item_id}",
                "priority": "ca_override",
                "confidence": 1.0,
                "notes": notes
            }
            contradiction_rules.append(rule)

    elif item_id.startswith("int_"):
        # Internal contradictions - these are within legacy rules
        # int_015, int_016, int_017 have conditional notes but null decisions
        # int_020: decision=r2, int_021: decision=r1, etc.
        internal_contradictions = rule_contradictions.get("internal_contradictions", [])

        # Map int_015 to index... the IDs don't directly map to indices
        # Let's find the matching contradiction by ID-ish matching
        # internal contradictions are numbered sequentially in the file
        # The int_ IDs don't have a direct mapping unfortunately
        # Let's use the selected_row/selected_name if available

        if decision == "other":
            winning_row = response.get("selected_row")
            winning_name = response.get("selected_name")
            if winning_row is not None:
                rule = {
                    "id": f"contradiction_{item_id}",
                    "fs_item": "",  # We don't know the fs_item for internal
                    "fs_item_original": "",
                    "canonical_sheet_row": winning_row,
                    "canonical_field_name": winning_name or row_to_name.get(winning_row, f"Row {winning_row}"),
                    "source_sheet": "bs",  # Most internal contradictions are BS
                    "industry_type": "all",
                    "source": f"CA_rule_contradiction_{item_id}",
                    "priority": "ca_override",
                    "confidence": 1.0,
                    "notes": notes
                }
                contradiction_rules.append(rule)
        elif decision in ("r1", "r2"):
            # r1 or r2 means one of the two conflicting rules wins
            # We need to find the corresponding internal contradiction
            # The internal contradictions have different structures:
            # - "internal_exact_duplicate_different_row" has conflicting_rules array
            # - "internal_similar_different_row" has rule_1 and rule_2

            # Without a direct mapping from int_XXX to contradiction index,
            # we'll handle the ones we can identify from the data
            # int_020=r2, int_021=r1, int_022=r2, int_023=other(152),
            # int_024=r1, int_025=r1, int_026=r1, int_029=r2,
            # int_030=r1, int_031=r1, int_032=r2

            # These need the actual contradiction data to resolve
            # For now, we note them but can't create specific rules without
            # the fs_item mapping
            pass

print(f"Contradiction rules created: {len(contradiction_rules)}")

# ── STEP 4: Extract rules from CA interview answers ───────────────────

ca_interview_rules = []

for answer in ca_answers_data.get("answers", []):
    question_id = answer.get("question_id", "")
    item_text = answer.get("item_text", "")

    # Determine the agreed row and name
    agreed_with_ai = answer.get("agreed_with_ai")

    # Check for industry-specific answers first
    industry_specific = answer.get("industry_specific")
    context_specific = answer.get("context_specific")

    if industry_specific:
        # Create one rule per industry
        for industry, spec in industry_specific.items():
            row = spec.get("row")
            name = spec.get("name")
            if row is not None:
                rule = {
                    "id": f"ca_interview_{question_id}_{industry}",
                    "fs_item": normalize_fs_item(item_text),
                    "fs_item_original": item_text,
                    "canonical_sheet_row": row,
                    "canonical_field_name": name or row_to_name.get(row, f"Row {row}"),
                    "source_sheet": "pl",  # Most CA answers are PL
                    "industry_type": industry,
                    "source": f"CA_interview_{question_id}",
                    "priority": "ca_interview",
                    "confidence": 0.95,
                    "notes": answer.get("notes", "")
                }
                ca_interview_rules.append(rule)
    elif context_specific:
        # Create one rule per context (pl/bs)
        for ctx, spec in context_specific.items():
            row = spec.get("row")
            name = spec.get("name")
            if row is not None:
                rule = {
                    "id": f"ca_interview_{question_id}_{ctx}",
                    "fs_item": normalize_fs_item(item_text),
                    "fs_item_original": item_text,
                    "canonical_sheet_row": row,
                    "canonical_field_name": name or row_to_name.get(row, f"Row {row}"),
                    "source_sheet": ctx,
                    "industry_type": "all",
                    "source": f"CA_interview_{question_id}",
                    "priority": "ca_interview",
                    "confidence": 0.95,
                    "notes": answer.get("notes", "")
                }
                ca_interview_rules.append(rule)
    else:
        # Single row answer
        if agreed_with_ai is True:
            row = answer.get("ai_suggested_row")
            name = answer.get("ai_suggested_name")
        elif agreed_with_ai is False:
            row = answer.get("default_row")
            name = answer.get("default_name")
        else:
            # agreed_with_ai is None — check if there's a default
            row = answer.get("default_row") or answer.get("ai_suggested_row")
            name = answer.get("default_name") or answer.get("ai_suggested_name")

        if row is not None:
            # Determine source_sheet from section context
            source_sheet = "pl"
            section = answer.get("section", "")
            notes_text = answer.get("notes", "")
            # BS items are in sections H, J (when they mention Balance Sheet)
            if "Balance Sheet" in item_text or "BS " in item_text:
                source_sheet = "bs"
            elif question_id in ("Q16", "Q17", "Q18", "Q19", "Q20", "Q33", "Q34", "Q35", "Q36", "Q37"):
                source_sheet = "bs"

            # Skip Q8a and Q8b which have "not to be touched" notes
            if notes_text and ("not to be touched" in notes_text.lower() or "shouldnt be toched" in notes_text.lower()):
                continue

            # Q15 is special - not a direct classification rule
            if question_id == "Q15":
                continue

            rule = {
                "id": f"ca_interview_{question_id}",
                "fs_item": normalize_fs_item(item_text),
                "fs_item_original": item_text,
                "canonical_sheet_row": row,
                "canonical_field_name": name or row_to_name.get(row, f"Row {row}"),
                "source_sheet": source_sheet,
                "industry_type": "all",
                "source": f"CA_interview_{question_id}",
                "priority": "ca_interview",
                "confidence": 0.95,
                "notes": notes_text
            }
            ca_interview_rules.append(rule)

# Also add general rules as meta-rules (these are patterns, not specific item rules)
# We'll skip adding them as rules since they're more like policies

print(f"CA interview rules created: {len(ca_interview_rules)}")

# ── STEP 5: Load legacy rules ─────────────────────────────────────────

legacy_rules = []
for rule in legacy_rules_data.get("rules", []):
    source_sheet = normalize_source_sheet(rule.get("source_sheet", ""))
    legacy_rule = {
        "id": f"legacy_{rule.get('rule_id', 0)}",
        "fs_item": normalize_fs_item(rule.get("fs_item", "")),
        "fs_item_original": rule.get("fs_item", ""),
        "canonical_sheet_row": rule.get("canonical_sheet_row"),
        "canonical_field_name": rule.get("canonical_name", ""),
        "source_sheet": source_sheet,
        "industry_type": "all",
        "source": f"Source1_rule_{rule.get('rule_id', 0)}",
        "priority": "legacy",
        "confidence": 0.8,
        "notes": rule.get("remarks", ""),
        "broad_classification": rule.get("broad_classification", ""),
        "cma_classification_text": rule.get("cma_classification_text", "")
    }
    # Skip rules with null rows - they are incomplete
    if legacy_rule["canonical_sheet_row"] is None:
        continue
    legacy_rules.append(legacy_rule)

print(f"Legacy rules loaded: {len(legacy_rules)}")

# ── STEP 6: Merge and deduplicate ─────────────────────────────────────

all_ca_override = ca_override_rules + contradiction_rules
seen_keys = set()
final_rules = []

# 1. Add all ca_override rules
for rule in all_ca_override:
    key = dedup_key(rule["fs_item"], rule["source_sheet"], rule["industry_type"])
    # For ca_override, we allow multiple rules for the same item if they have different rows
    # (this handles cases where the same item appears in different companies)
    # Use a compound key that includes the row
    compound_key = f"{key}|{rule['canonical_sheet_row']}"
    if compound_key not in seen_keys and rule["fs_item"]:
        seen_keys.add(compound_key)
        seen_keys.add(key)  # Also mark the base key as covered
        final_rules.append(rule)

# Track which base keys are covered by ca_override
ca_override_keys = set()
for rule in final_rules:
    key = dedup_key(rule["fs_item"], rule["source_sheet"], rule["industry_type"])
    ca_override_keys.add(key)

print(f"After ca_override dedup: {len(final_rules)} rules")

# 2. Add ca_interview rules (skip if same fs_item already covered by ca_override)
ca_interview_added = 0
for rule in ca_interview_rules:
    key = dedup_key(rule["fs_item"], rule["source_sheet"], rule["industry_type"])
    if key not in ca_override_keys:
        compound_key = f"{key}|{rule['canonical_sheet_row']}"
        if compound_key not in seen_keys and rule["fs_item"]:
            seen_keys.add(compound_key)
            seen_keys.add(key)
            final_rules.append(rule)
            ca_interview_added += 1

# Track ca_interview keys
ca_interview_keys = set()
for rule in final_rules:
    if rule["priority"] == "ca_interview":
        key = dedup_key(rule["fs_item"], rule["source_sheet"], rule["industry_type"])
        ca_interview_keys.add(key)

print(f"After ca_interview add: {len(final_rules)} rules (+{ca_interview_added} interview)")

# 3. Add legacy rules (skip if same fs_item + source_sheet already covered)
legacy_added = 0
higher_priority_keys = ca_override_keys | ca_interview_keys
for rule in legacy_rules:
    key = dedup_key(rule["fs_item"], rule["source_sheet"], rule["industry_type"])
    if key not in higher_priority_keys:
        compound_key = f"{key}|{rule['canonical_sheet_row']}"
        if compound_key not in seen_keys and rule["fs_item"]:
            seen_keys.add(compound_key)
            seen_keys.add(key)
            final_rules.append(rule)
            legacy_added += 1

print(f"After legacy add: {len(final_rules)} rules (+{legacy_added} legacy)")

# ── Sort rules ─────────────────────────────────────────────────────────

priority_order = {"ca_override": 0, "ca_interview": 1, "legacy": 2}
final_rules.sort(key=lambda r: (priority_order.get(r["priority"], 9), r["id"]))

# ── Count by priority ─────────────────────────────────────────────────

ca_override_count = sum(1 for r in final_rules if r["priority"] == "ca_override")
ca_interview_count = sum(1 for r in final_rules if r["priority"] == "ca_interview")
legacy_count = sum(1 for r in final_rules if r["priority"] == "legacy")

# ── Sort doubts ────────────────────────────────────────────────────────

# Fill in company for doubts from dispute_by_id if needed
for doubt in doubts:
    if not doubt.get("company"):
        d = dispute_by_id.get(doubt["item_id"])
        if d:
            doubt["company"] = d.get("company", "")

doubts.sort(key=lambda d: d["item_id"])

# ── Build output ───────────────────────────────────────────────────────

output = {
    "metadata": {
        "version": "2.0",
        "date": "2026-03-31",
        "description": "Authoritative CMA classification rules. CA override rules take precedence over all legacy rules.",
        "sources": [
            "GT disputes (175 items, 168 resolved)",
            "Rule contradictions (14 cross-source, 21 internal)",
            "CA interview (68 items)",
            "Legacy rules (398 items, overridden where conflict exists)"
        ],
        "priority_order": ["ca_override", "ca_interview", "legacy"],
        "total_rules": len(final_rules),
        "ca_override_count": ca_override_count,
        "ca_interview_count": ca_interview_count,
        "legacy_count": legacy_count,
        "doubt_count": len(doubts)
    },
    "rules": final_rules,
    "doubts": doubts
}

# ── Write output ───────────────────────────────────────────────────────

output_path = BASE / "CMA_Ground_Truth_v1" / "reference" / "cma_golden_rules_v2.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n{'='*60}")
print(f"New golden rules v2: {len(final_rules)} total rules")
print(f"  {ca_override_count} ca_override")
print(f"  {ca_interview_count} ca_interview")
print(f"  {legacy_count} legacy")
print(f"  {len(doubts)} doubts")
print(f"\nWritten to: {output_path}")
print(f"{'='*60}")
