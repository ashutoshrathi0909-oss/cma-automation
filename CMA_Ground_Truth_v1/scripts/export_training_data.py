#!/usr/bin/env python3
"""
export_training_data.py — Export ground truth database to ML-ready training format.

Outputs:
  - training_data.json  (flat array of training examples)
  - label_reference.json (label definitions with counts)
"""

import json
import os
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE = os.path.join(BASE_DIR, "ground_truth_database.json")
LABELS_FILE = os.path.join(BASE_DIR, "canonical_labels.json")
TRAINING_OUT = os.path.join(BASE_DIR, "training_data.json")
LABEL_REF_OUT = os.path.join(BASE_DIR, "label_reference.json")

# Fields to keep in training data
KEEP_FIELDS = [
    "text",           # renamed from raw_text
    "label",          # renamed from cma_row
    "label_code",     # renamed from cma_code
    "label_name",     # renamed from cma_field_name
    "source_form",
    "section_normalized",
    "industry_type",
    "entity_type",
    "match_type",
    "company",        # renamed from company_name
    "financial_year",
]


def export_training_data(entries):
    """Convert database entries to flat training format."""
    training = []
    for e in entries:
        record = {
            "text": e["raw_text"],
            "label": e["cma_row"],
            "label_code": e["cma_code"],
            "label_name": e["cma_field_name"],
            "source_form": e.get("source_form"),
            "section_normalized": e.get("section_normalized"),
            "industry_type": e["industry_type"],
            "entity_type": e["entity_type"],
            "match_type": e["match_type"],
            "company": e["company_name"],
            "financial_year": e["financial_year"],
        }
        training.append(record)
    return training


def build_label_reference(entries, canonical_labels):
    """Build label reference with counts from training data."""
    # Count entries per label
    label_counts = Counter(e["cma_row"] for e in entries)

    # Build label definitions from canonical_labels
    labels = {}
    for cl in canonical_labels:
        row = cl["sheet_row"]
        labels[str(row)] = {
            "code": cl["code"],
            "name": cl["name"],
            "section": cl["section"],
            "train_count": label_counts.get(row, 0),
        }

    covered = sum(1 for v in labels.values() if v["train_count"] > 0)

    return {
        "labels": labels,
        "total_labels": len(labels),
        "covered_labels": covered,
        "uncovered_labels": len(labels) - covered,
    }


def main():
    print("=" * 60)
    print("CMA Training Data Export")
    print("=" * 60)

    # Load inputs
    print("\n[1/3] Loading database and canonical labels...")
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
    with open(LABELS_FILE, "r", encoding="utf-8") as f:
        canonical_labels = json.load(f)

    entries = db["entries"]
    print(f"  Database: {len(entries)} entries")
    print(f"  Canonical labels: {len(canonical_labels)} rows")

    # Export training data
    print("\n[2/3] Exporting training data...")
    training = export_training_data(entries)
    with open(TRAINING_OUT, "w", encoding="utf-8") as f:
        json.dump(training, f, indent=2, ensure_ascii=False)
    print(f"  Saved: {TRAINING_OUT}")
    print(f"  Records: {len(training)}")
    print(f"  Fields per record: {list(training[0].keys())}")

    # Build label reference
    print("\n[3/3] Building label reference...")
    label_ref = build_label_reference(entries, canonical_labels)
    with open(LABEL_REF_OUT, "w", encoding="utf-8") as f:
        json.dump(label_ref, f, indent=2, ensure_ascii=False)
    print(f"  Saved: {LABEL_REF_OUT}")
    print(f"  Total labels: {label_ref['total_labels']}")
    print(f"  Covered: {label_ref['covered_labels']}")
    print(f"  Uncovered: {label_ref['uncovered_labels']}")

    # Summary stats
    print("\n" + "-" * 60)
    print("Training Data Summary")
    print("-" * 60)
    unique_texts = len(set(r["text"] for r in training))
    unique_labels = len(set(r["label"] for r in training))
    print(f"  Unique texts: {unique_texts}")
    print(f"  Unique labels used: {unique_labels}")
    print(f"  Avg examples per label: {len(training)/unique_labels:.1f}")

    # Distribution by match_type
    mt = Counter(r["match_type"] for r in training)
    print(f"  Match types: {dict(mt)}")

    # Distribution by industry
    ind = Counter(r["industry_type"] for r in training)
    print(f"  Industry: {dict(ind)}")

    print("\n" + "=" * 60)
    print("Phase 4 complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
