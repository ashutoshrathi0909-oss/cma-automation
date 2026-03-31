#!/usr/bin/env python3
"""
merge_database.py — Merge 9 normalized ground truth JSON files into a single
production database, applying 3 known fixes.

Output: ground_truth_database.json
"""

import json
import os
from datetime import date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Input files ──────────────────────────────────────────────────────────────
INPUTS = [
    ("BCIPL/BCIPL_ground_truth_normalized.json", "BCIPL"),
    ("Kurunji Retail/ground_truth_normalized.json", "Kurunji Retail"),
    ("SLIPL/SLIPL_Ground_Truth_normalized.json", "SLIPL"),
    ("SR Papers/sr_papers_ground_truth_normalized.json", "SR Papers"),
    ("SSSS/ssss_ground_truth_normalized.json", "SSSS"),
    ("INPL/inpl_ground_truth_normalized.json", "INPL"),
    ("MSL - Manufacturing/MSL_ground_truth_normalized.json", "MSL"),
    ("Dynamic air engenerring/dynamic_ground_truth_normalized.json", "Dynamic Air"),
    ("Mehta computer/mehta_ground_truth_normalized.json", "Mehta Computer"),
]

OUTPUT_FILE = os.path.join(BASE_DIR, "ground_truth_database.json")


def load_all():
    """Load all 9 normalized files, return merged entries and company summaries."""
    all_entries = []
    companies_list = []

    for rel_path, short_name in INPUTS:
        full_path = os.path.join(BASE_DIR, rel_path)
        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        meta = data["company_metadata"]
        entries = data["database_entries"]

        # Add company_name to every entry
        for e in entries:
            e["company_name"] = meta["company_name"]

        all_entries.extend(entries)

        companies_list.append({
            "name": meta["company_name"],
            "short_name": short_name,
            "entries": len(entries),
            "industry": meta["industry_type"],
            "entity": meta["entity_type"],
            "financial_years": meta["financial_years"],
            "currency_unit": meta.get("currency_unit", "unknown"),
        })

        print(f"  Loaded {short_name}: {len(entries)} entries ({meta['industry_type']}, {meta['entity_type']})")

    return all_entries, companies_list


# ── Fix 1: BCIPL "Profit on Sale of Fixed Asset" row 22 → 30 ────────────────
def fix_bcipl_profit_on_sale(entries):
    fixed = 0
    for e in entries:
        if (e.get("company_name", "").startswith("Bagadia")
                and "Profit on Sale" in (e.get("raw_text") or "")
                and e.get("cma_row") == 22):
            e["cma_row"] = 30
            e["cma_code"] = "II_B3"
            e["cma_field_name"] = "Profit on sale of fixed assets / Investments"
            e["validation_issue"] = (
                "Corrected from row 22 (Exports) — original extraction error. "
                "CA placed Profit on Sale of FA under Export Sales, which inflated Net Sales."
            )
            fixed += 1
    print(f"  Fix 1 (BCIPL row 22->30): {fixed} entry corrected")
    return fixed


# ── Fix 2: SSSS row 98 collision ────────────────────────────────────────────
def fix_ssss_row98(entries):
    """Two entries with cma_row=98, FY 2024-25, different amounts.
    Entry 1 (1.967487, original_cma_row 34): NET total tax = current+previous+deferred
    Entry 2 (1.9261703, original_cma_row 35): current tax component only
    Resolution: both are valid components — set both to composite_component."""
    fixed = 0
    for e in entries:
        if (e.get("company_name", "").startswith("Salem")
                and e.get("cma_row") == 98
                and e.get("financial_year") == "2024-25"):
            e["match_type"] = "composite_component"
            if abs(e.get("amount", 0) - 1.967487) < 0.001:
                e["validation_issue"] = (
                    "Row 98 collision resolved: this entry is the NET total tax provision "
                    "(Current 1.926 + Previous 0.064 + Deferred -0.023 = 1.967). "
                    "Kept as composite_component alongside the current-tax-only entry."
                )
            elif abs(e.get("amount", 0) - 1.9261703) < 0.001:
                e["validation_issue"] = (
                    "Row 98 collision resolved: this entry is the current tax component only (1.926 Cr). "
                    "Kept as composite_component alongside the net-total entry."
                )
            fixed += 1
    print(f"  Fix 2 (SSSS row 98 collision): {fixed} entries set to composite_component")
    return fixed


# ── Fix 3: 3 "unmatched" entries → typed ────────────────────────────────────
def fix_unmatched_entries(entries):
    fixed = 0
    for e in entries:
        company = e.get("company_name", "")

        # SSSS row 92 "Loss on disposal" → direct
        if (company.startswith("Salem")
                and e.get("cma_row") == 92
                and e.get("match_type") == "unmatched"):
            e["match_type"] = "direct"
            e["validation_issue"] = (
                (e.get("validation_issue") or "") +
                " | Fixed: match_type changed from 'unmatched' to 'direct'."
            ).strip(" |")
            fixed += 1

        # INPL row 67 "Rent, Rates, Taxes" → composite_component
        if (company.startswith("IFFCO")
                and e.get("cma_row") == 67
                and e.get("match_type") == "unmatched"):
            e["match_type"] = "composite_component"
            e["validation_issue"] = (
                (e.get("validation_issue") or "") +
                " | Fixed: match_type changed from 'unmatched' to 'composite_component'."
            ).strip(" |")
            fixed += 1

        # INPL row 92 "Others Non Operating" → composite_component
        if (company.startswith("IFFCO")
                and e.get("cma_row") == 92
                and e.get("match_type") == "unmatched"):
            e["match_type"] = "composite_component"
            e["validation_issue"] = (
                (e.get("validation_issue") or "") +
                " | Fixed: match_type changed from 'unmatched' to 'composite_component'."
            ).strip(" |")
            fixed += 1

    print(f"  Fix 3 (unmatched->typed): {fixed} entries corrected")
    return fixed


def build_database(entries, companies_list, fixes_log):
    """Build the final database structure."""
    cma_rows_covered = len(set(e["cma_row"] for e in entries))

    metadata = {
        "total_entries": len(entries),
        "companies": len(companies_list),
        "cma_rows_covered": cma_rows_covered,
        "cma_rows_total": 131,
        "created_date": str(date.today()),
        "version": "1.0",
        "fixes_applied": fixes_log,
        "companies_list": companies_list,
    }

    return {"database_metadata": metadata, "entries": entries}


def main():
    print("=" * 60)
    print("CMA Ground Truth Database — Merge + Fix")
    print("=" * 60)

    # Step 1: Load all files
    print("\n[1/3] Loading 9 normalized ground truth files...")
    entries, companies_list = load_all()
    print(f"\n  Total entries loaded: {len(entries)}")

    # Step 2: Apply fixes
    print("\n[2/3] Applying known fixes...")
    fixes_log = []

    n = fix_bcipl_profit_on_sale(entries)
    if n:
        fixes_log.append(f"BCIPL row 22->30 ({n} entry)")

    n = fix_ssss_row98(entries)
    if n:
        fixes_log.append(f"SSSS row 98 collision resolved ({n} entries)")

    n = fix_unmatched_entries(entries)
    if n:
        fixes_log.append(f"3 unmatched->typed ({n} entries)")

    # Step 3: Build and save
    print("\n[3/3] Building database...")
    db = build_database(entries, companies_list, fixes_log)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

    print(f"\n  Saved: {OUTPUT_FILE}")
    print(f"  Entries: {db['database_metadata']['total_entries']}")
    print(f"  CMA rows covered: {db['database_metadata']['cma_rows_covered']}/131")
    print(f"  Fixes applied: {fixes_log}")
    print("\n" + "=" * 60)
    print("Phase 1 complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
