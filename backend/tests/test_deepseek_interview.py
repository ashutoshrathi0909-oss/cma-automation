"""DeepSeek Interview Round — diagnostic probe, not pass/fail.

Calls real DeepSeek API with deliberately ambiguous items to discover
gaps and improvement opportunities. Produces a diagnostic report.

Run: OPENROUTER_API_KEY=<key> pytest tests/test_deepseek_interview.py -v -s
"""

from __future__ import annotations

import json
import os

import pytest

_HAS_KEY = bool(os.environ.get("OPENROUTER_API_KEY"))

# ── Interview questions ──────────────────────────────────────────────────
# Each question tests a specific weakness area.

INTERVIEW_QUESTIONS = [
    # Q1: Does DeepSeek understand industry-dependent routing?
    {
        "id": "IQ01",
        "text": "staff welfare expenses",
        "amount": 25000,
        "section": "employee benefits",
        "industry": "manufacturing",
        "doc_type": "profit_and_loss",
        "correct_row": 45,
        "probe": "Industry routing: should be R45 for manufacturing, R67 for trading",
    },
    {
        "id": "IQ02",
        "text": "staff welfare expenses",
        "amount": 25000,
        "section": "employee benefits",
        "industry": "trading",
        "doc_type": "profit_and_loss",
        "correct_row": 67,
        "probe": "Same item, different industry — must give DIFFERENT answer",
    },

    # Q3: Context switch — P&L vs BS
    {
        "id": "IQ03",
        "text": "leave encashment",
        "amount": 30000,
        "section": "employee benefits",
        "industry": "manufacturing",
        "doc_type": "profit_and_loss",
        "correct_row": 45,
        "probe": "Leave encashment in P&L → R45. In BS → R249. Tests context awareness.",
    },
    {
        "id": "IQ04",
        "text": "provision for leave encashment",
        "amount": 30000,
        "section": "provisions",
        "industry": "manufacturing",
        "doc_type": "balance_sheet",
        "correct_row": 249,
        "probe": "Same concept, BS context → R249 (Creditors for Expenses), NOT R45",
    },

    # Q5: Subsidy context switch
    {
        "id": "IQ05",
        "text": "government grant subsidy",
        "amount": 100000,
        "section": "other income",
        "industry": "manufacturing",
        "doc_type": "profit_and_loss",
        "correct_row": 33,
        "probe": "P&L subsidy → R33 (Extraordinary income). BS → R125 (Other Reserve).",
    },

    # Q6: Misleading section header
    {
        "id": "IQ06",
        "text": "insurance premium",
        "amount": 50000,
        "section": "manufacturing overheads",
        "industry": "manufacturing",
        "doc_type": "profit_and_loss",
        "correct_row": 71,
        "probe": "Even under 'manufacturing overheads', insurance → R71 Admin. CA rule.",
    },

    # Q7: Compound ambiguity — combined line with misleading name
    {
        "id": "IQ07",
        "text": "employee benefit expenses including gratuity epf and esi",
        "amount": 500000,
        "section": "employee cost",
        "industry": "manufacturing",
        "doc_type": "profit_and_loss",
        "correct_row": 45,
        "probe": "Long combined line — must classify by nature (employee cost → R45 mfg)",
    },

    # Q8: Amount-based hint — very small amount suggests admin, not manufacturing
    {
        "id": "IQ08",
        "text": "repairs and maintenance",
        "amount": 500,
        "section": "expenses",
        "industry": "manufacturing",
        "doc_type": "profit_and_loss",
        "correct_row": 50,
        "probe": "Even tiny amount — repairs in manufacturing context → R50, not R72 (Admin)",
    },

    # Q9: Interest confusion
    {
        "id": "IQ09",
        "text": "interest on unsecured loan from directors",
        "amount": 80000,
        "section": "finance cost",
        "industry": "manufacturing",
        "doc_type": "profit_and_loss",
        "correct_row": 83,
        "probe": "Unsecured loan interest → R83 (Fixed Loans), not R84 (WC). Source: BCIPL-006",
    },

    # Q10: Negative amount confusion
    {
        "id": "IQ10",
        "text": "discount received from suppliers",
        "amount": -25000,
        "section": "other income",
        "industry": "manufacturing",
        "doc_type": "profit_and_loss",
        "correct_row": 34,
        "probe": "Negative-looking income item. Should be R34 (Others Non-Op Income).",
    },

    # Q11: The classic trap — "Other Charges"
    {
        "id": "IQ11",
        "text": "other charges",
        "amount": 15000,
        "section": "expenses",
        "industry": "manufacturing",
        "doc_type": "profit_and_loss",
        "correct_row": 71,
        "probe": "Vague 'other charges' with no context — should default to R71 (Admin Others)",
    },

    # Q12: Electricity in trading
    {
        "id": "IQ12",
        "text": "electricity charges",
        "amount": 30000,
        "section": "admin expenses",
        "industry": "trading",
        "doc_type": "profit_and_loss",
        "correct_row": 71,
        "probe": "Electricity: manufacturing → R48, trading → R71. Source: Q12a",
    },
]


@pytest.mark.skipif(not _HAS_KEY, reason="OPENROUTER_API_KEY not set")
class TestDeepSeekInterview:
    """Diagnostic interview — produces a gap analysis report."""

    def test_interview_round(self):
        from app.services.classification.scoped_classifier import ScopedClassifier

        classifier = ScopedClassifier()
        results = []

        for q in INTERVIEW_QUESTIONS:
            r = classifier.classify_sync(
                raw_text=q["text"], amount=q["amount"],
                section=q["section"], industry_type=q["industry"],
                document_type=q["doc_type"], fuzzy_candidates=[],
            )
            passed = r.cma_row == q["correct_row"]
            results.append({
                "id": q["id"],
                "text": q["text"],
                "industry": q["industry"],
                "correct": q["correct_row"],
                "got": r.cma_row,
                "got_name": r.cma_field_name,
                "conf": r.confidence,
                "passed": passed,
                "probe": q["probe"],
            })

        # ── Print diagnostic report ──
        correct = sum(1 for r in results if r["passed"])
        total = len(results)
        print(f"\n{'='*70}")
        print(f"  DEEPSEEK INTERVIEW REPORT: {correct}/{total} ({correct/total:.0%})")
        print(f"{'='*70}")

        # Group by pass/fail
        passed_items = [r for r in results if r["passed"]]
        failed_items = [r for r in results if not r["passed"]]

        if failed_items:
            print(f"\n  GAPS FOUND ({len(failed_items)}):")
            print(f"  {'-'*66}")
            for r in failed_items:
                print(f"  [{r['id']}] '{r['text']}' ({r['industry']})")
                print(f"    Expected: R{r['correct']}")
                print(f"    Got:      R{r['got']} ({r['got_name']}) conf={r['conf']:.2f}")
                print(f"    Probe:    {r['probe']}")
                print()

        if passed_items:
            print(f"\n  PASSED ({len(passed_items)}):")
            print(f"  {'-'*66}")
            for r in passed_items:
                print(f"  [{r['id']}] '{r['text']}' ({r['industry']}) -> R{r['got']} conf={r['conf']:.2f}")

        print(f"\n{'='*70}")
        print(f"  IMPROVEMENT RECOMMENDATIONS:")
        print(f"{'='*70}")

        # Auto-generate recommendations based on failures
        gap_categories = {
            "industry_routing": [],
            "context_switch": [],
            "misleading_section": [],
            "interest_confusion": [],
            "ambiguous_items": [],
            "other": [],
        }

        for r in failed_items:
            if "industry" in r["probe"].lower():
                gap_categories["industry_routing"].append(r)
            elif "context" in r["probe"].lower() or "P&L" in r["probe"] or "BS" in r["probe"]:
                gap_categories["context_switch"].append(r)
            elif "misleading" in r["probe"].lower() or "section" in r["probe"].lower():
                gap_categories["misleading_section"].append(r)
            elif "interest" in r["probe"].lower():
                gap_categories["interest_confusion"].append(r)
            elif "vague" in r["probe"].lower() or "ambig" in r["probe"].lower():
                gap_categories["ambiguous_items"].append(r)
            else:
                gap_categories["other"].append(r)

        for cat, items in gap_categories.items():
            if items:
                print(f"\n  {cat.upper().replace('_', ' ')} ({len(items)} failures):")
                if cat == "industry_routing":
                    print("    -> Add industry_type to DeepSeek prompt as a top-level instruction")
                    print("    -> Add more industry-specific examples to training data")
                elif cat == "context_switch":
                    print("    -> Add document_type (P&L vs BS) as explicit context in prompt")
                    print("    -> Add CA rules for P&L-vs-BS disambiguation to hard-coded rules")
                elif cat == "misleading_section":
                    print("    -> Add 'classify by NATURE not section header' emphasis in prompt")
                elif cat == "interest_confusion":
                    print("    -> Expand CA disambiguation rules for interest categories")
                elif cat == "ambiguous_items":
                    print("    -> For truly ambiguous items, lower confidence to trigger doubt")

        print(f"\n{'='*70}\n")

        # Save results to JSON for analysis
        report_path = os.path.join(os.path.dirname(__file__), "interview_results.json")
        with open(report_path, "w") as f:
            json.dump({"total": total, "correct": correct, "results": results}, f, indent=2)
        print(f"  Full report saved to: {report_path}")

        # Don't fail the test — this is diagnostic, not pass/fail
        # But warn if accuracy is very low
        if correct / total < 0.5:
            pytest.skip(f"DeepSeek accuracy {correct/total:.0%} — needs significant improvement")
