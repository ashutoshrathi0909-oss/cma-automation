#!/usr/bin/env python3
"""AutoResearch verify script: Live Summary + Document Context features.

Metric: % of checks passing (0-100).
Tests both backend API enrichment and feature correctness.

Usage:
    python tests/verify_new_features.py
    # Outputs a single number (0-100) to stdout as the metric.
"""

import json
import sys
import requests

BASE = "http://localhost:8000"
EMAIL = "admin@cma-automation.in"
PASSWORD = "CmaAdmin@2026"
REPORT_ID = "ef924f63-ddbe-40af-ae61-ddb5c7dc2282"

checks_passed = 0
checks_total = 0


def check(name: str, condition: bool):
    global checks_passed, checks_total
    checks_total += 1
    if condition:
        checks_passed += 1
        print(f"  PASS: {name}", file=sys.stderr)
    else:
        print(f"  FAIL: {name}", file=sys.stderr)


def main():
    # ── Auth ──
    r = requests.post(f"{BASE}/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
    if r.status_code != 200:
        print("0")
        print("FAIL: Cannot authenticate", file=sys.stderr)
        return
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    check("Auth: login succeeds", True)

    # ── Feature 1: Confidence summary endpoint ──
    r = requests.get(f"{BASE}/api/cma-reports/{REPORT_ID}/confidence", headers=headers)
    check("Confidence: endpoint returns 200", r.status_code == 200)
    if r.status_code == 200:
        summary = r.json()
        check("Confidence: total > 0", summary.get("total", 0) > 0)
        check("Confidence: has approved count", "approved" in summary)
        check("Confidence: has corrected count", "corrected" in summary)
        check("Confidence: has needs_review count", "needs_review" in summary)
        check("Confidence: counts are consistent",
              summary.get("high_confidence", 0) + summary.get("medium_confidence", 0) + summary.get("needs_review", 0) <= summary.get("total", 0))

    # ── Feature 2: Document context in classifications ──
    r = requests.get(f"{BASE}/api/cma-reports/{REPORT_ID}/classifications", headers=headers)
    check("Classifications: endpoint returns 200", r.status_code == 200)
    if r.status_code == 200:
        clfs = r.json()
        check("Classifications: has items", len(clfs) > 0)

        if clfs:
            # Check that new fields exist in the response schema
            first = clfs[0]
            check("Schema: line_item_section field exists", "line_item_section" in first)
            check("Schema: document_name field exists", "document_name" in first)
            check("Schema: document_type field exists", "document_type" in first)
            check("Schema: line_item_description field exists", "line_item_description" in first)
            check("Schema: line_item_amount field exists", "line_item_amount" in first)

            # Check that document context is actually populated (not all null)
            with_doc_name = sum(1 for c in clfs if c.get("document_name"))
            with_doc_type = sum(1 for c in clfs if c.get("document_type"))
            with_section = sum(1 for c in clfs if c.get("line_item_section"))
            total = len(clfs)

            doc_name_pct = (with_doc_name / total) * 100 if total else 0
            doc_type_pct = (with_doc_type / total) * 100 if total else 0

            check(f"Populated: document_name on >90% items ({doc_name_pct:.0f}%)", doc_name_pct > 90)
            check(f"Populated: document_type on >90% items ({doc_type_pct:.0f}%)", doc_type_pct > 90)
            check(f"Populated: line_item_section on >0% items ({with_section}/{total})", with_section > 0)

            # Verify document names are real file names (not UUIDs)
            sample_names = [c["document_name"] for c in clfs[:20] if c.get("document_name")]
            has_real_names = any(
                name.endswith((".pdf", ".xlsx", ".xls")) for name in sample_names
            )
            check("Quality: document_name contains real filenames", has_real_names)

            # Verify document_type values are valid
            valid_types = {"profit_and_loss", "balance_sheet", "notes_to_accounts",
                          "schedules", "combined_financial_statement", "loan_repayment_schedule"}
            sample_types = [c["document_type"] for c in clfs[:20] if c.get("document_type")]
            all_valid = all(t in valid_types for t in sample_types)
            check("Quality: document_type values are valid", all_valid)

            # Check that different documents are represented
            unique_doc_names = set(c.get("document_name") for c in clfs if c.get("document_name"))
            check(f"Coverage: multiple documents represented ({len(unique_doc_names)} docs)", len(unique_doc_names) >= 2)

            # Check doubts have context too
            doubts = [c for c in clfs if c.get("is_doubt")]
            if doubts:
                doubts_with_context = sum(1 for d in doubts if d.get("document_name"))
                check(f"Doubts: have document context ({doubts_with_context}/{len(doubts)})",
                      doubts_with_context > 0)

    # ── Documents endpoint (for linked docs card) ──
    r = requests.get(f"{BASE}/api/documents/?client_id=519cf01a-03f2-4f4d-b730-a4d49f53b68a", headers=headers)
    check("Documents: endpoint returns 200", r.status_code == 200)
    if r.status_code == 200:
        docs = r.json()
        check("Documents: has items", len(docs) > 0)
        if docs:
            check("Documents: have file_name", all(d.get("file_name") for d in docs))
            check("Documents: have financial_year", all(d.get("financial_year") for d in docs))
            check("Documents: have document_type", all(d.get("document_type") for d in docs))

    # ── Output metric ──
    metric = round((checks_passed / checks_total) * 100) if checks_total > 0 else 0
    print(f"\n{'='*50}", file=sys.stderr)
    print(f"RESULT: {checks_passed}/{checks_total} checks passed ({metric}%)", file=sys.stderr)
    print(f"{'='*50}", file=sys.stderr)
    print(metric)


if __name__ == "__main__":
    main()
