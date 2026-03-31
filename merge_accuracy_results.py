"""Merge accuracy results from all companies into one file for CA review.

Usage:
    python merge_accuracy_results.py

Reads: DOCS/test-results/scoped-v2/{COMPANY}_accuracy.json (all available)
Outputs:
    DOCS/test-results/scoped-v2/ALL_WRONG_ENTRIES.json
    DOCS/test-results/scoped-v2/ALL_WRONG_ENTRIES.csv
    DOCS/test-results/scoped-v2/ACCURACY_SUMMARY.md
"""

import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
OUTPUT_DIR = PROJECT_ROOT / "DOCS" / "test-results" / "scoped-v2"

COMPANIES = [
    "BCIPL", "INPL", "Kurunji_Retail", "MSL", "SLIPL",
    "SR_Papers", "SSSS", "Dynamic_Air", "Mehta_Computer",
]


def load_company_results(company: str) -> dict | None:
    path = OUTPUT_DIR / f"{company}_accuracy.json"
    if not path.exists():
        print(f"  SKIP: {company} (no results file)")
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    print("Merging accuracy results...\n")

    per_company = []
    all_wrong = []
    total_items = 0
    total_correct = 0

    for company in COMPANIES:
        data = load_company_results(company)
        if data is None:
            continue

        per_company.append({
            "company": company,
            "total": data["total_items"],
            "correct": data["correct_count"],
            "wrong": data["wrong_count"],
            "doubt": data["doubt_count"],
            "accuracy_pct": data["accuracy_pct"],
        })
        total_items += data["total_items"]
        total_correct += data["correct_count"]

        for entry in data.get("wrong_entries", []):
            entry["company"] = company
            all_wrong.append(entry)

    overall_acc = total_correct / total_items * 100 if total_items > 0 else 0

    # Find unique wrong patterns (same raw_text appearing across companies)
    text_groups = {}
    for entry in all_wrong:
        key = entry["raw_text"].strip().lower()
        if key not in text_groups:
            text_groups[key] = {
                "raw_text": entry["raw_text"],
                "correct_cma_row": entry["correct_cma_row"],
                "correct_cma_field": entry["correct_cma_field"],
                "companies": [],
                "predicted_rows": [],
                "error_types": [],
            }
        text_groups[key]["companies"].append(entry.get("company", "?"))
        text_groups[key]["predicted_rows"].append(entry.get("predicted_cma_row", 0))
        text_groups[key]["error_types"].append(entry.get("error_type", "?"))

    unique_patterns = sorted(text_groups.values(), key=lambda x: -len(x["companies"]))

    # Save merged JSON
    merged = {
        "generated": str(date.today()),
        "companies_tested": len(per_company),
        "total_items_tested": total_items,
        "total_correct": total_correct,
        "total_wrong": len(all_wrong),
        "overall_accuracy_pct": round(overall_acc, 2),
        "per_company": per_company,
        "unique_wrong_pattern_count": len(unique_patterns),
        "all_wrong_entries": all_wrong,
        "unique_wrong_patterns": unique_patterns,
    }
    json_path = OUTPUT_DIR / "ALL_WRONG_ENTRIES.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False, default=str)
    print(f"Saved: {json_path}")

    # Save CSV for CA review
    csv_path = OUTPUT_DIR / "ALL_WRONG_ENTRIES.csv"
    fieldnames = [
        "company", "raw_text", "section", "amount", "financial_year",
        "correct_cma_row", "correct_cma_field",
        "predicted_cma_row", "predicted_cma_field",
        "classification_method", "confidence", "error_type",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for entry in all_wrong:
            writer.writerow(entry)
    print(f"Saved: {csv_path} ({len(all_wrong)} entries)")

    # Save summary markdown
    md_lines = [
        f"# Accuracy Summary — All Companies",
        f"",
        f"Generated: {date.today()}",
        f"",
        f"## Overall",
        f"- Companies tested: {len(per_company)}",
        f"- Total items: {total_items}",
        f"- Correct: {total_correct}",
        f"- Wrong + Doubt: {len(all_wrong)}",
        f"- **Overall accuracy: {overall_acc:.1f}%**",
        f"",
        f"## Per Company",
        f"",
        f"| Company | Total | Correct | Wrong | Doubt | Accuracy |",
        f"|---------|-------|---------|-------|-------|----------|",
    ]
    for c in per_company:
        md_lines.append(
            f"| {c['company']} | {c['total']} | {c['correct']} | {c['wrong']} | {c['doubt']} | {c['accuracy_pct']:.1f}% |"
        )

    md_lines.extend([
        f"",
        f"## Top 20 Most Common Wrong Patterns",
        f"",
        f"| Raw Text | Correct Row | Predicted Rows | Companies | Count |",
        f"|----------|-------------|----------------|-----------|-------|",
    ])
    for p in unique_patterns[:20]:
        pred = ", ".join(str(r) for r in set(p["predicted_rows"]))
        comps = ", ".join(set(p["companies"]))
        md_lines.append(
            f"| {p['raw_text'][:50]} | {p['correct_cma_row']} ({p['correct_cma_field'][:30]}) | {pred} | {comps} | {len(p['companies'])} |"
        )

    md_lines.extend([
        f"",
        f"## Files for CA Review",
        f"- `ALL_WRONG_ENTRIES.csv` — open in Excel, review each entry",
        f"- `ALL_WRONG_ENTRIES.json` — full data with patterns",
        f"",
        f"## Next Step",
        f"CA reviews the CSV and confirms/corrects the `correct_cma_row` for each entry.",
        f"Verified entries become training data to improve the classifier.",
    ])

    md_path = OUTPUT_DIR / "ACCURACY_SUMMARY.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"Saved: {md_path}")

    # Print summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  Overall accuracy: {overall_acc:.1f}%")
    print(f"  Total wrong entries: {len(all_wrong)}")
    print(f"  Unique patterns: {len(unique_patterns)}")
    for c in per_company:
        print(f"  {c['company']:20s} {c['accuracy_pct']:5.1f}%  ({c['correct']}/{c['total']})")
    print(f"\n  CSV for CA review: {csv_path}")


if __name__ == "__main__":
    main()
