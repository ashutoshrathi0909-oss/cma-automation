"""Run classification accuracy test for a single company.

Usage:
    python run_company_accuracy.py COMPANY_NAME

Examples:
    python run_company_accuracy.py INPL
    python run_company_accuracy.py Dynamic_Air
    python run_company_accuracy.py SSSS

Output:
    DOCS/test-results/scoped-v2/{COMPANY}_accuracy.json
    DOCS/test-results/scoped-v2/{COMPANY}_wrong_entries.csv
"""

import csv
import json
import os
import sys
import time
from pathlib import Path

# Load .env before importing app modules
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Add backend to path so we can import the classifier
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.classification.scoped_classifier import ScopedClassifier

# ── Config ─────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent
EXTRACTIONS_DIR = PROJECT_ROOT / "DOCS" / "extractions"
GT_COMPANIES_DIR = PROJECT_ROOT / "CMA_Ground_Truth_v1" / "companies"
OUTPUT_DIR = PROJECT_ROOT / "DOCS" / "test-results" / "scoped-v2"

# Companies and their ground truth locations + formats
COMPANY_CONFIG = {
    "BCIPL": {"dir": "extractions", "row_key": "correct_cma_row", "field_key": "correct_cma_field", "amount_key": "amount_rupees"},
    "INPL": {"dir": "extractions", "row_key": "correct_cma_row", "field_key": "correct_cma_field", "amount_key": "amount_rupees"},
    "Kurunji_Retail": {"dir": "extractions", "row_key": "correct_cma_row", "field_key": "correct_cma_field", "amount_key": "amount_rupees"},
    "MSL": {"dir": "extractions", "row_key": "correct_cma_row", "field_key": "correct_cma_field", "amount_key": "amount_rupees"},
    "SLIPL": {"dir": "extractions", "row_key": "correct_cma_row", "field_key": "correct_cma_field", "amount_key": "amount_rupees"},
    "SR_Papers": {"dir": "extractions", "row_key": "correct_cma_row", "field_key": "correct_cma_field", "amount_key": "amount_rupees"},
    "SSSS": {"dir": "extractions", "row_key": "correct_cma_row", "field_key": "correct_cma_field", "amount_key": "amount_rupees"},
    "Dynamic_Air": {"dir": "companies", "row_key": "cma_row", "field_key": "cma_field_name", "amount_key": "amount"},
    "Mehta_Computer": {"dir": "companies", "row_key": "cma_row", "field_key": "cma_field_name", "amount_key": "amount"},
}

# Cost guard: stop if tokens exceed this
MAX_TOKENS = 500_000


def load_ground_truth(company: str) -> list[dict]:
    """Load ground truth items for a company."""
    config = COMPANY_CONFIG[company]

    if config["dir"] == "extractions":
        path = EXTRACTIONS_DIR / f"{company}_classification_ground_truth.json"
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else data.get("items", [])
    else:
        path = GT_COMPANIES_DIR / company / "ground_truth_normalized.json"
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        items = data.get("database_entries", [])

    # Normalize keys
    row_key = config["row_key"]
    field_key = config["field_key"]
    amount_key = config["amount_key"]

    normalized = []
    for item in items:
        normalized.append({
            "raw_text": item.get("raw_text", ""),
            "section": item.get("section", ""),
            "amount": item.get(amount_key),
            "financial_year": item.get("financial_year", ""),
            "correct_cma_row": item.get(row_key),
            "correct_cma_field": item.get(field_key, ""),
            "sheet_name": item.get("sheet_name", ""),
        })
    return normalized


def infer_document_type(section: str, sheet_name: str) -> str:
    """Infer document_type from section and sheet_name."""
    combined = f"{section} {sheet_name}".lower()
    if any(kw in combined for kw in ["balance sheet", "bs", "assets", "liabilities", "equity"]):
        return "balance_sheet"
    return "profit_and_loss"


def run_accuracy_test(company: str) -> dict:
    """Run the accuracy test for a single company. Returns results dict."""
    print(f"\n{'='*60}")
    print(f"  Testing: {company}")
    print(f"{'='*60}")

    items = load_ground_truth(company)
    print(f"  Loaded {len(items)} ground truth items")

    # Initialize classifier (loads ground truth data once)
    classifier = ScopedClassifier()

    results = []
    correct = 0
    wrong = 0
    doubt = 0
    wrong_entries = []
    start_time = time.time()

    for i, item in enumerate(items):
        raw_text = item["raw_text"]
        section = item["section"]
        amount = item["amount"]
        doc_type = infer_document_type(section, item["sheet_name"])

        try:
            result = classifier.classify_sync(
                raw_text=raw_text,
                amount=amount,
                section=section,
                industry_type="Manufacturing",
                document_type=doc_type,
                fuzzy_candidates=[],
            )
        except Exception as e:
            print(f"  ERROR on item {i}: {e}")
            result = classifier._make_doubt(f"Error: {e}")

        predicted_row = result.cma_row or 0
        correct_row = item["correct_cma_row"] or 0
        is_correct = predicted_row == correct_row
        is_doubt_item = result.is_doubt

        entry = {
            "index": i,
            "raw_text": raw_text,
            "section": section,
            "amount": amount,
            "financial_year": item["financial_year"],
            "correct_cma_row": correct_row,
            "correct_cma_field": item["correct_cma_field"],
            "predicted_cma_row": predicted_row,
            "predicted_cma_field": result.cma_field_name or "UNCLASSIFIED",
            "classification_method": result.classification_method,
            "confidence": result.confidence,
            "is_correct": is_correct,
            "is_doubt": is_doubt_item,
            "routed_section": "",  # would need internal access
        }
        results.append(entry)

        if is_doubt_item:
            doubt += 1
            wrong_entries.append({**entry, "error_type": "doubt"})
        elif is_correct:
            correct += 1
        else:
            wrong += 1
            wrong_entries.append({**entry, "error_type": "wrong_classification"})

        # Progress every 25 items
        if (i + 1) % 25 == 0:
            elapsed = time.time() - start_time
            pct = correct / (i + 1) * 100
            print(f"  [{i+1}/{len(items)}] accuracy={pct:.1f}% elapsed={elapsed:.0f}s tokens=~{classifier._total_tokens}")

        # Cost guard
        if classifier._total_tokens > MAX_TOKENS:
            print(f"  COST GUARD: stopping at {classifier._total_tokens} tokens (item {i+1}/{len(items)})")
            break

    elapsed = time.time() - start_time
    total_tested = correct + wrong + doubt
    accuracy = correct / total_tested * 100 if total_tested > 0 else 0

    print(f"\n  Results for {company}:")
    print(f"  Total: {total_tested} | Correct: {correct} | Wrong: {wrong} | Doubt: {doubt}")
    print(f"  Accuracy: {accuracy:.1f}%")
    print(f"  Time: {elapsed:.0f}s | Tokens: ~{classifier._total_tokens}")

    output = {
        "company": company,
        "total_items": total_tested,
        "correct_count": correct,
        "wrong_count": wrong,
        "doubt_count": doubt,
        "accuracy_pct": round(accuracy, 2),
        "elapsed_seconds": round(elapsed, 1),
        "tokens_used": classifier._total_tokens,
        "wrong_entries": wrong_entries,
        "all_results": results,
    }
    return output


def save_results(company: str, output: dict):
    """Save JSON results and CSV of wrong entries."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # JSON
    json_path = OUTPUT_DIR / f"{company}_accuracy.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    print(f"  Saved: {json_path}")

    # CSV of wrong entries only
    csv_path = OUTPUT_DIR / f"{company}_wrong_entries.csv"
    fieldnames = [
        "raw_text", "section", "amount", "financial_year",
        "correct_cma_row", "correct_cma_field",
        "predicted_cma_row", "predicted_cma_field",
        "classification_method", "confidence", "error_type",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for entry in output["wrong_entries"]:
            writer.writerow(entry)
    print(f"  Saved: {csv_path} ({len(output['wrong_entries'])} wrong entries)")


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_company_accuracy.py COMPANY_NAME")
        print(f"Available: {', '.join(COMPANY_CONFIG.keys())}")
        sys.exit(1)

    company = sys.argv[1]
    if company not in COMPANY_CONFIG:
        print(f"Unknown company: {company}")
        print(f"Available: {', '.join(COMPANY_CONFIG.keys())}")
        sys.exit(1)

    if company == "BCIPL":
        print("BCIPL already tested. Use the BCIPL prompt to extract wrong entries from existing results.")
        sys.exit(0)

    output = run_accuracy_test(company)
    save_results(company, output)
    print("\nDone!")


if __name__ == "__main__":
    main()
