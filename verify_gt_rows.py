#!/usr/bin/env python3
"""
GT Row Verification & Fix Script
Verifies that ground truth files use correct CMA row numbers per canonical_labels.json.
Saves corrected versions as new files; originals are NOT modified.
"""
import json
import os
import sys
import io
from collections import Counter
from datetime import date

# Force UTF-8 output on Windows to avoid cp1252 errors
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.abspath(__file__))

# ─── Paths ────────────────────────────────────────────────────────────────────
CANONICAL_PATH = os.path.join(BASE, "CMA_Ground_Truth_v1", "reference", "canonical_labels.json")
COMPANIES_DIR  = os.path.join(BASE, "CMA_Ground_Truth_v1", "companies")
EXTRACTIONS_DIR = os.path.join(BASE, "DOCS", "extractions")
VALIDATION_DIR = os.path.join(BASE, "CMA_Ground_Truth_v1", "validation")

LOCATION_A_COMPANIES = [
    "BCIPL", "Dynamic_Air", "INPL", "Kurunji_Retail",
    "Mehta_Computer", "MSL", "SLIPL", "SR_Papers", "SSSS"
]

LOCATION_B_COMPANIES = [
    "BCIPL", "INPL", "Kurunji_Retail", "MSL", "SLIPL", "SR_Papers", "SSSS"
]

# Companies in BOTH locations (for cross-check)
BOTH_COMPANIES = set(LOCATION_A_COMPANIES) & set(LOCATION_B_COMPANIES)


# ─── Step 1: Build canonical lookup ──────────────────────────────────────────
def build_canonical_maps(canonical_path):
    with open(canonical_path, encoding="utf-8") as f:
        labels = json.load(f)
    code_to_row  = {}   # "II_A1" → 22
    row_to_name  = {}   # 22 → "Domestic"
    row_to_code  = {}   # 22 → "II_A1"
    for item in labels:
        row  = item["sheet_row"]
        code = item["code"]
        name = item["name"]
        code_to_row[code] = row
        row_to_name[row]  = name
        row_to_code[row]  = code
    print(f"[CANONICAL] Loaded {len(labels)} labels.")
    print(f"  Row range: {min(row_to_name)} – {max(row_to_name)}")
    return code_to_row, row_to_name, row_to_code, labels


# ─── Step 2: Verify & fix Location A ─────────────────────────────────────────
def verify_location_a(company, code_to_row, row_to_name):
    """Returns (result_dict, corrected_data_or_None)"""
    gt_path = os.path.join(COMPANIES_DIR, company, "ground_truth_normalized.json")
    if not os.path.exists(gt_path):
        print(f"  [SKIP] {gt_path} not found")
        return {"error": "file_not_found"}, None

    with open(gt_path, encoding="utf-8") as f:
        data = json.load(f)

    entries = data.get("database_entries", [])
    total = len(entries)

    offsets = []           # list of (stored_row - canonical_row) for each entry with a known code
    unknown_codes = []
    no_code_entries = 0

    for entry in entries:
        code = entry.get("cma_code")
        stored_row = entry.get("cma_row")
        if not code:
            no_code_entries += 1
            continue
        if code not in code_to_row:
            unknown_codes.append(code)
            continue
        canonical_row = code_to_row[code]
        offsets.append(stored_row - canonical_row)

    if not offsets:
        print(f"  [{company}] No entries with known cma_code — cannot detect offset")
        return {
            "total": total,
            "offset_detected": None,
            "corrected": False,
            "note": "no entries with known cma_code"
        }, None

    offset_counts = Counter(offsets)
    dominant_offset, dominant_count = offset_counts.most_common(1)[0]
    pct = dominant_count / len(offsets) * 100

    print(f"  [{company}] {total} entries | {len(offsets)} with known code | "
          f"dominant offset: {dominant_offset:+d} ({dominant_count}/{len(offsets)} = {pct:.1f}%)")
    if unknown_codes:
        unique_unknown = list(set(unknown_codes))
        print(f"    Unknown codes ({len(unique_unknown)}): {unique_unknown[:10]}")

    result = {
        "total": total,
        "entries_with_code": len(offsets),
        "unknown_codes": list(set(unknown_codes)),
        "no_code_entries": no_code_entries,
        "offset_distribution": dict(offset_counts),
        "dominant_offset": dominant_offset,
        "dominant_pct": round(pct, 1),
        "offset_detected": dominant_offset if pct >= 90 else None,
        "corrected": False,
    }

    if pct < 90:
        print(f"    WARNING: No systematic offset (dominant is only {pct:.1f}%). Manual review needed.")
        return result, None

    if dominant_offset == 0:
        print(f"    All rows CORRECT — no fix needed.")
        result["offset_detected"] = 0
        result["corrected"] = False
        result["note"] = "rows already correct"
        return result, None

    # Apply correction: subtract the dominant_offset to get canonical row
    correction = -dominant_offset  # e.g., if offset is -1, correction is +1
    corrected_entries = []
    fixed_count = 0
    for entry in entries:
        e = dict(entry)
        code = e.get("cma_code")
        if code and code in code_to_row:
            canonical_row = code_to_row[code]
            canonical_name = row_to_name[canonical_row]
            e["cma_row"] = canonical_row
            e["cma_field_name"] = canonical_name
            fixed_count += 1
        corrected_entries.append(e)

    corrected_data = dict(data)
    corrected_data["database_entries"] = corrected_entries
    if "company_metadata" not in corrected_data:
        corrected_data["company_metadata"] = {}
    corrected_data["company_metadata"]["correction_applied"] = f"{correction:+d} row offset"
    corrected_data["company_metadata"]["correction_date"] = str(date.today())
    corrected_data["company_metadata"]["original_file"] = "ground_truth_normalized.json"

    result["corrected"] = True
    result["fixed_count"] = fixed_count
    result["correction_applied"] = f"{correction:+d} row offset"
    print(f"    Fixed {fixed_count} entries (correction: {correction:+d})")
    return result, corrected_data


# ─── Step 3: Verify & fix Location B ─────────────────────────────────────────
def verify_location_b(company, code_to_row, row_to_name):
    """Returns (result_dict, corrected_data_or_None)"""
    gt_path = os.path.join(EXTRACTIONS_DIR, f"{company}_classification_ground_truth.json")
    if not os.path.exists(gt_path):
        print(f"  [SKIP] {gt_path} not found")
        return {"error": "file_not_found"}, None

    with open(gt_path, encoding="utf-8") as f:
        data = json.load(f)

    entries = data if isinstance(data, list) else data.get("items", [])
    total = len(entries)

    row_correct = 0
    row_wrong = 0
    field_name_mismatch = 0
    offsets = []
    unknown_rows = []
    corrected_entries = []
    needs_fix = False

    for entry in entries:
        stored_row   = entry.get("correct_cma_row")
        stored_field = entry.get("correct_cma_field", "")
        e = dict(entry)

        if stored_row not in row_to_name:
            unknown_rows.append(stored_row)
            corrected_entries.append(e)
            continue

        canonical_name = row_to_name[stored_row]
        offsets.append(0)  # row is itself — we're verifying row is valid

        # Check field name match (case-insensitive, partial)
        field_matches = (
            canonical_name.lower() in stored_field.lower() or
            stored_field.lower() in canonical_name.lower()
        )
        if not field_matches:
            field_name_mismatch += 1
            e["correct_cma_field"] = canonical_name
            needs_fix = True

        row_correct += 1
        corrected_entries.append(e)

    pct_correct = row_correct / total * 100 if total else 0
    print(f"  [{company}] {total} entries | {row_correct} row-valid ({pct_correct:.1f}%) | "
          f"{field_name_mismatch} field-name mismatches | {len(unknown_rows)} unknown rows")

    # Check for systematic row offset in Location B
    # (Look for entries where stored_row is off from what codes suggest)
    # Location B has no cma_code, so we check if stored rows exist in canonical
    offset_detected = 0  # 0 = correct by default

    result = {
        "total": total,
        "row_correct": row_correct,
        "row_wrong": len(unknown_rows),
        "field_name_mismatch": field_name_mismatch,
        "unknown_rows": list(set(unknown_rows)),
        "offset_detected": offset_detected,
        "corrected": False,
    }

    if needs_fix and field_name_mismatch > 0:
        corrected_data = corrected_entries
        result["corrected"] = True
        result["correction_applied"] = f"field_name_normalized ({field_name_mismatch} entries)"
        print(f"    Fixed {field_name_mismatch} field names to match canonical")
        return result, corrected_data

    return result, None


# ─── Normalize financial year to ending year integer ─────────────────────────
def normalize_fy(fy_val):
    """Normalize FY to ending year integer.
    "2022-23" → 2023, "2023-24" → 2024, 2023 → 2023
    """
    if isinstance(fy_val, int):
        return fy_val
    s = str(fy_val).strip()
    if "-" in s:
        # "2022-23" or "2022-2023"
        parts = s.split("-")
        ending = parts[-1]
        if len(ending) == 2:
            # "22-23" → 2023; "2022-23" → 2023
            return 2000 + int(ending)
        return int(ending)
    try:
        return int(s)
    except ValueError:
        return s


# ─── Step 4: Cross-check Location A corrected vs Location B ──────────────────
def cross_check(company, loc_a_corrected, loc_b_data, code_to_row):
    """Compare corrected Location A rows against Location B rows.
    Matches by (raw_text_lower, normalized_fy) since FY formats differ:
      Location A: "2022-23"  →  Location B: 2023
    """
    if loc_a_corrected is None or loc_b_data is None:
        return None

    # Build a lookup from (raw_text, normalized_fy) → canonical_row for Location A
    a_lookup = {}
    for entry in loc_a_corrected.get("database_entries", []):
        key = (entry.get("raw_text", "").strip().lower(),
               normalize_fy(entry.get("financial_year", "")))
        a_lookup[key] = entry.get("cma_row")

    b_entries = loc_b_data if isinstance(loc_b_data, list) else loc_b_data.get("items", [])

    agree = 0
    disagree = 0
    disagree_details = []

    for entry in b_entries:
        raw   = entry.get("raw_text", "").strip().lower()
        b_fy  = normalize_fy(entry.get("financial_year", ""))
        b_row = entry.get("correct_cma_row")
        key   = (raw, b_fy)
        if key in a_lookup:
            a_row = a_lookup[key]
            if a_row == b_row:
                agree += 1
            else:
                disagree += 1
                disagree_details.append({
                    "raw_text": entry.get("raw_text"),
                    "financial_year": b_fy,
                    "location_a_row": a_row,
                    "location_b_row": b_row,
                })

    total_matched = agree + disagree
    print(f"  [{company}] Cross-check: {len(b_entries)} Loc-B entries, "
          f"{total_matched} text-fy matched → {agree} agree, {disagree} disagree")

    return {"agree": agree, "disagree": disagree, "disagree_details": disagree_details[:20]}


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(VALIDATION_DIR, exist_ok=True)

    print("=" * 60)
    print("STEP 1: Load canonical labels")
    print("=" * 60)
    code_to_row, row_to_name, row_to_code, canonical_labels = build_canonical_maps(CANONICAL_PATH)

    report = {
        "date": str(date.today()),
        "canonical_labels_count": len(canonical_labels),
        "companies": {}
    }

    # ── Store corrected data for cross-check ──────────────────────────────────
    loc_a_corrected_data = {}   # company → corrected dict (or None)
    loc_b_data_store    = {}    # company → raw list (or None)

    # ──────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 2: Verify & fix Location A (companies/)")
    print("=" * 60)

    for company in LOCATION_A_COMPANIES:
        print(f"\n  Processing {company}...")
        result, corrected = verify_location_a(company, code_to_row, row_to_name)
        report["companies"].setdefault(company, {})["location_a"] = result
        loc_a_corrected_data[company] = None

        if corrected is not None:
            out_path = os.path.join(COMPANIES_DIR, company, "ground_truth_corrected.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(corrected, f, indent=2, ensure_ascii=False)
            print(f"    Saved corrected file → {out_path}")
            loc_a_corrected_data[company] = corrected

    # ──────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 3: Verify & fix Location B (extractions/)")
    print("=" * 60)

    for company in LOCATION_B_COMPANIES:
        print(f"\n  Processing {company}...")
        result, corrected = verify_location_b(company, code_to_row, row_to_name)
        report["companies"].setdefault(company, {})["location_b"] = result

        # Always load the original for cross-check
        gt_path = os.path.join(EXTRACTIONS_DIR, f"{company}_classification_ground_truth.json")
        if os.path.exists(gt_path):
            with open(gt_path, encoding="utf-8") as f:
                loc_b_data_store[company] = json.load(f)
        else:
            loc_b_data_store[company] = None

        if corrected is not None:
            out_path = os.path.join(EXTRACTIONS_DIR, f"{company}_classification_ground_truth_corrected.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(corrected, f, indent=2, ensure_ascii=False)
            print(f"    Saved corrected file → {out_path}")

    # ──────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 4: Cross-check Location A vs Location B")
    print("=" * 60)

    for company in sorted(BOTH_COMPANIES):
        print(f"\n  Cross-checking {company}...")

        # Use corrected Location A if it was fixed, else load original
        if loc_a_corrected_data.get(company):
            a_data = loc_a_corrected_data[company]
        else:
            gt_path = os.path.join(COMPANIES_DIR, company, "ground_truth_normalized.json")
            if os.path.exists(gt_path):
                with open(gt_path, encoding="utf-8") as f:
                    a_data = json.load(f)
            else:
                a_data = None

        b_data = loc_b_data_store.get(company)
        cc = cross_check(company, a_data, b_data, code_to_row)
        if cc is not None:
            report["companies"][company]["cross_check"] = cc
        else:
            report["companies"].setdefault(company, {})["cross_check"] = None

    # Make sure companies with no location_b have null
    for company in LOCATION_A_COMPANIES:
        if company not in LOCATION_B_COMPANIES:
            report["companies"][company]["location_b"] = None
            report["companies"][company]["cross_check"] = None

    # ──────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 5: Generate reports")
    print("=" * 60)

    # JSON report
    json_report_path = os.path.join(VALIDATION_DIR, "row_verification_report.json")
    with open(json_report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"  Saved JSON report → {json_report_path}")

    # Markdown summary
    md_lines = [
        "# GT Row Verification Summary",
        "",
        f"**Date:** {date.today()}  ",
        f"**Canonical labels:** {len(canonical_labels)}  ",
        "",
        "---",
        "",
        "## Location A — `CMA_Ground_Truth_v1/companies/`",
        "",
        "| Company | Entries | Dominant Offset | % Affected | Corrected? |",
        "|---------|---------|-----------------|------------|------------|",
    ]
    for company in LOCATION_A_COMPANIES:
        la = report["companies"][company].get("location_a", {})
        total   = la.get("total", "N/A")
        offset  = la.get("dominant_offset", "N/A")
        pct     = la.get("dominant_pct", "N/A")
        fixed   = "✅ Yes" if la.get("corrected") else ("—" if la.get("offset_detected") == 0 else "❌ No")
        md_lines.append(f"| {company} | {total} | {offset:+d} | {pct}% | {fixed} |"
                        if isinstance(offset, int) else
                        f"| {company} | {total} | {offset} | {pct} | {fixed} |")

    md_lines += [
        "",
        "## Location B — `DOCS/extractions/`",
        "",
        "| Company | Entries | Row Valid | Field Mismatches | Corrected? |",
        "|---------|---------|-----------|-----------------|------------|",
    ]
    for company in LOCATION_B_COMPANIES:
        lb = report["companies"][company].get("location_b", {})
        total  = lb.get("total", "N/A")
        valid  = lb.get("row_correct", "N/A")
        mismatch = lb.get("field_name_mismatch", "N/A")
        fixed  = "✅ Yes" if lb.get("corrected") else "No"
        md_lines.append(f"| {company} | {total} | {valid} | {mismatch} | {fixed} |")

    md_lines += [
        "",
        "## Cross-Check (Location A corrected vs Location B)",
        "",
        "| Company | A Entries | B Entries | Agree | Disagree |",
        "|---------|-----------|-----------|-------|----------|",
    ]
    for company in sorted(BOTH_COMPANIES):
        cc = report["companies"][company].get("cross_check")
        la = report["companies"][company].get("location_a", {})
        lb = report["companies"][company].get("location_b", {})
        a_total = la.get("total", "N/A")
        b_total = lb.get("total", "N/A")
        if cc:
            agree    = cc.get("agree", "N/A")
            disagree = cc.get("disagree", "N/A")
        else:
            agree = disagree = "N/A"
        md_lines.append(f"| {company} | {a_total} | {b_total} | {agree} | {disagree} |")

    md_lines += [
        "",
        "---",
        "",
        "## Notes",
        "",
        "- Original GT files are **not modified**. Corrected versions saved as `*_corrected.json`.",
        "- Canonical source of truth: `CMA_Ground_Truth_v1/reference/canonical_labels.json`",
        "- Cross-check matches entries by `(raw_text, financial_year)` — only exact-text matches are compared.",
        "- Field name comparison uses substring matching (canonical name inside stored field or vice versa).",
        "",
    ]

    # Disagree details
    any_disagree = False
    for company in sorted(BOTH_COMPANIES):
        cc = report["companies"][company].get("cross_check") or {}
        details = cc.get("disagree_details", [])
        if details:
            if not any_disagree:
                md_lines += ["## Disagreement Details", ""]
                any_disagree = True
            md_lines.append(f"### {company}")
            md_lines.append("| Raw Text | FY | Location A Row | Location B Row |")
            md_lines.append("|----------|----|----------------|----------------|")
            for d in details:
                rt = str(d.get("raw_text", ""))[:60]
                fy = d.get("financial_year", "")
                md_lines.append(f"| {rt} | {fy} | {d.get('location_a_row')} | {d.get('location_b_row')} |")
            md_lines.append("")

    md_path = os.path.join(VALIDATION_DIR, "ROW_VERIFICATION_SUMMARY.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"  Saved Markdown report → {md_path}")

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
