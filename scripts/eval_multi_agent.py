"""Offline evaluation script — tests multi-agent classification accuracy against GT.

Runs the RouterAgent + 4 specialist agents on ground-truth items and compares
predicted cma_row to the known-correct cma_row for each entry.

Usage
-----
# Single company
python scripts/eval_multi_agent.py --company BCIPL

# All 9 GT companies
python scripts/eval_multi_agent.py --all

# Single company, single agent bucket only
python scripts/eval_multi_agent.py --company BCIPL --agent pl_expense

NOTE: This script does NOT run the full Supabase pipeline.  It calls agent
      classes directly (RouterAgent.route + BaseAgent.classify_batch) using
      env-stubbed settings so no real DB connection is needed.  An actual
      OPENROUTER_API_KEY is required to make live model calls; without one the
      agents return doubt records for every item.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Bootstrap: add backend to sys.path + stub required env vars BEFORE any app
# import, because pydantic-settings validates at import time.
# ---------------------------------------------------------------------------
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

os.environ.setdefault("SUPABASE_URL", "https://placeholder.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "placeholder")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "placeholder")

# ---------------------------------------------------------------------------
# Standard + app imports
# ---------------------------------------------------------------------------
import argparse
import json
import logging
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPANIES: dict[str, dict[str, str]] = {
    "BCIPL": {"industry": "manufacturing"},
    "MSL": {"industry": "manufacturing"},
    "INPL": {"industry": "manufacturing"},
    "SLIPL": {"industry": "manufacturing"},
    "Dynamic_Air": {"industry": "services"},
    "Kurunji_Retail": {"industry": "trading"},
    "Mehta_Computer": {"industry": "trading"},
    "SR_Papers": {"industry": "manufacturing"},
    "SSSS": {"industry": "services"},
}

# Inclusive row ranges for each specialist bucket
AGENT_RANGES: dict[str, tuple[int, int]] = {
    "pl_income": (22, 34),
    "pl_expense": (41, 108),
    "bs_liability": (110, 160),
    "bs_asset": (161, 258),
}

GT_DIR = PROJECT_ROOT / "CMA_Ground_Truth_v1" / "companies"

DOUBT_CONFIDENCE_THRESHOLD = 0.80


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def expected_bucket(cma_row: int) -> str | None:
    """Return the specialist bucket name for *cma_row*, or None if unranged."""
    for bucket, (lo, hi) in AGENT_RANGES.items():
        if lo <= cma_row <= hi:
            return bucket
    return None


def load_gt_entries(company: str) -> list[dict]:
    """Load and deduplicate GT entries for *company*.

    Deduplication key: (raw_text.lower(), cma_row).  When duplicates exist
    the first occurrence is kept.
    """
    gt_path = GT_DIR / company / "ground_truth_corrected.json"
    if not gt_path.exists():
        raise FileNotFoundError(f"GT file not found: {gt_path}")

    with gt_path.open(encoding="utf-8") as fh:
        data = json.load(fh)

    raw_entries: list[dict] = data.get("database_entries", [])

    seen: set[tuple[str, int]] = set()
    deduped: list[dict] = []
    for entry in raw_entries:
        key = (entry.get("raw_text", "").lower(), int(entry.get("cma_row", 0)))
        if key not in seen:
            seen.add(key)
            deduped.append(entry)

    return deduped


def entries_to_items(entries: list[dict]) -> tuple[list[dict], dict[str, int]]:
    """Convert GT database_entries to the item format expected by agents.

    Returns
    -------
    (items, gt_lookup)
        items      — list of item dicts
        gt_lookup  — {item_id: expected_cma_row}
    """
    items: list[dict] = []
    gt_lookup: dict[str, int] = {}

    for i, entry in enumerate(entries):
        item_id = f"gt-{i:04d}"
        raw_text = entry.get("raw_text", "")
        items.append(
            {
                "id": item_id,
                "source_text": raw_text,
                "description": raw_text,
                "amount": entry.get("amount"),
                "section": entry.get("section"),
                "source_sheet": entry.get("sheet_name"),
                "page_type": "notes",
                "has_note_breakdowns": False,
            }
        )
        gt_lookup[item_id] = int(entry.get("cma_row", 0))

    return items, gt_lookup


# ---------------------------------------------------------------------------
# Result dataclass (plain dict for simplicity)
# ---------------------------------------------------------------------------

def _make_company_result() -> dict:
    return {
        "total": 0,
        "correct": 0,
        "wrong": 0,
        "doubt": 0,
        "misrouted": 0,
        "per_agent": {k: {"correct": 0, "wrong": 0, "doubt": 0} for k in AGENT_RANGES},
        "confusion": Counter(),   # (expected_row, predicted_row) -> count
    }


# ---------------------------------------------------------------------------
# Core evaluation logic
# ---------------------------------------------------------------------------

def eval_company(
    company: str,
    industry: str,
    agent_filter: str | None = None,
    prompt_dir: str | None = None,
) -> dict:
    """Run router + specialists on all GT entries for one company.

    Parameters
    ----------
    company:      Company key (matches directory name under GT_DIR)
    industry:     "manufacturing" | "trading" | "services"
    agent_filter: If set, only classify items in this bucket (others -> skipped)

    Returns
    -------
    Result dict produced by _make_company_result().
    """
    # Import here so sys.path manipulation above takes effect first
    from app.services.classification.agents.router import RouterAgent
    from app.services.classification.agents.pl_income import PLIncomeAgent
    from app.services.classification.agents.pl_expense import PLExpenseAgent
    from app.services.classification.agents.bs_liability import BSLiabilityAgent
    from app.services.classification.agents.bs_asset import BSAssetAgent

    result = _make_company_result()

    # ── 1. Load GT ────────────────────────────────────────────────────────────
    entries = load_gt_entries(company)
    items, gt_lookup = entries_to_items(entries)
    result["total"] = len(items)

    if not items:
        logger.warning("[eval] %s: no GT entries found", company)
        return result

    # ── 2. Route ─────────────────────────────────────────────────────────────
    router = RouterAgent()
    buckets, _router_tokens = router.route(items, industry, "annual_report")

    # Check routing accuracy
    for item in router.last_unrouted:
        item_id = item["id"]
        expected_row = gt_lookup.get(item_id, 0)
        expected_bkt = expected_bucket(expected_row)
        if expected_bkt is not None:
            # Item was routable but the router missed it — count as misroute
            result["misrouted"] += 1
            logger.debug("[eval] %s: item %s misrouted (expected %s)", company, item_id, expected_bkt)

    for bucket_name, bucket_items in buckets.items():
        for item in bucket_items:
            item_id = item["id"]
            expected_row = gt_lookup.get(item_id, 0)
            expected_bkt = expected_bucket(expected_row)
            if expected_bkt is not None and expected_bkt != bucket_name:
                result["misrouted"] += 1
                logger.debug(
                    "[eval] %s: item %s misrouted to %s (expected %s)",
                    company, item_id, bucket_name, expected_bkt,
                )

    # ── 3. Instantiate specialists ────────────────────────────────────────────
    if prompt_dir:
        pd = Path(prompt_dir)
        specialists: dict[str, Any] = {
            "pl_income": PLIncomeAgent(prompt_path=str(pd / "pl_income_prompt.md")),
            "pl_expense": PLExpenseAgent(prompt_path=str(pd / "pl_expense_prompt.md")),
            "bs_liability": BSLiabilityAgent(prompt_path=str(pd / "bs_liability_prompt.md")),
            "bs_asset": BSAssetAgent(prompt_path=str(pd / "bs_asset_prompt.md")),
        }
    else:
        specialists: dict[str, Any] = {
            "pl_income": PLIncomeAgent(),
            "pl_expense": PLExpenseAgent(),
            "bs_liability": BSLiabilityAgent(),
            "bs_asset": BSAssetAgent(),
        }

    # ── 4. Classify each bucket ───────────────────────────────────────────────
    for bucket_name, bucket_items in buckets.items():
        if not bucket_items:
            continue
        if agent_filter is not None and bucket_name != agent_filter:
            # Skip this bucket — still counted in total but not in per-agent
            continue

        agent = specialists[bucket_name]
        classifications, _tokens = agent.classify_batch(bucket_items, industry)

        # Build lookup: item_id -> classification dict
        clf_by_id: dict[str, dict] = {c["id"]: c for c in classifications}

        for item in bucket_items:
            item_id = item["id"]
            expected_row = gt_lookup.get(item_id, 0)
            clf = clf_by_id.get(item_id, {})
            predicted_row: int = int(clf.get("cma_row") or 0)
            confidence: float = float(clf.get("confidence") or 0.0)

            is_doubt = predicted_row == 0 or confidence < DOUBT_CONFIDENCE_THRESHOLD

            if is_doubt:
                result["doubt"] += 1
                result["per_agent"][bucket_name]["doubt"] += 1
            elif predicted_row == expected_row:
                result["correct"] += 1
                result["per_agent"][bucket_name]["correct"] += 1
            else:
                result["wrong"] += 1
                result["per_agent"][bucket_name]["wrong"] += 1
                result["confusion"][(expected_row, predicted_row)] += 1
                logger.debug(
                    "[eval] %s/%s: item %s expected=%d predicted=%d conf=%.2f",
                    company, bucket_name, item_id, expected_row, predicted_row, confidence,
                )

    return result


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _accuracy(correct: int, wrong: int) -> str:
    classified = correct + wrong
    if classified == 0:
        return "N/A"
    return f"{correct / classified * 100:.1f}%"


def _doubt_rate(doubt: int, total: int) -> str:
    if total == 0:
        return "N/A"
    return f"{doubt / total * 100:.1f}%"


def _misroute_rate(misrouted: int, total: int) -> str:
    if total == 0:
        return "N/A"
    return f"{misrouted / total * 100:.1f}%"


def print_company_report(company: str, result: dict) -> None:
    total = result["total"]
    correct = result["correct"]
    wrong = result["wrong"]
    doubt = result["doubt"]
    misrouted = result["misrouted"]

    print(f"\n{'=' * 60}")
    print(f"Company : {company}")
    print(f"Total   : {total}")
    print(f"Correct : {correct}")
    print(f"Wrong   : {wrong}")
    print(f"Doubt   : {doubt}")
    print(f"Misrouted: {misrouted}")
    print(f"Accuracy (excl. doubts) : {_accuracy(correct, wrong)}")
    print(f"Doubt rate              : {_doubt_rate(doubt, total)}")
    print(f"Misroute rate           : {_misroute_rate(misrouted, total)}")

    print("\nPer-agent breakdown:")
    for agent_name, counts in result["per_agent"].items():
        c = counts["correct"]
        w = counts["wrong"]
        d = counts["doubt"]
        if c + w + d == 0:
            continue
        print(
            f"  {agent_name:<16} correct={c:>3}  wrong={w:>3}  doubt={d:>3}"
            f"  acc={_accuracy(c, w)}"
        )

    if result["confusion"]:
        print("\nTop confusion pairs (expected_row -> predicted_row):")
        for (exp, pred), cnt in result["confusion"].most_common(10):
            print(f"  row {exp:>3} -> row {pred:>3} : {cnt} time(s)")


def print_aggregate_report(all_results: dict[str, dict]) -> None:
    agg = _make_company_result()
    for result in all_results.values():
        agg["total"] += result["total"]
        agg["correct"] += result["correct"]
        agg["wrong"] += result["wrong"]
        agg["doubt"] += result["doubt"]
        agg["misrouted"] += result["misrouted"]
        for agent_name, counts in result["per_agent"].items():
            for k in ("correct", "wrong", "doubt"):
                agg["per_agent"][agent_name][k] += counts[k]
        agg["confusion"].update(result["confusion"])

    print(f"\n{'=' * 60}")
    print("AGGREGATE (all companies)")
    print(f"Total   : {agg['total']}")
    print(f"Correct : {agg['correct']}")
    print(f"Wrong   : {agg['wrong']}")
    print(f"Doubt   : {agg['doubt']}")
    print(f"Misrouted: {agg['misrouted']}")
    print(f"Accuracy (excl. doubts) : {_accuracy(agg['correct'], agg['wrong'])}")
    print(f"Doubt rate              : {_doubt_rate(agg['doubt'], agg['total'])}")
    print(f"Misroute rate           : {_misroute_rate(agg['misrouted'], agg['total'])}")

    print("\nPer-agent aggregate:")
    for agent_name, counts in agg["per_agent"].items():
        c = counts["correct"]
        w = counts["wrong"]
        d = counts["doubt"]
        if c + w + d == 0:
            continue
        print(
            f"  {agent_name:<16} correct={c:>3}  wrong={w:>3}  doubt={d:>3}"
            f"  acc={_accuracy(c, w)}"
        )

    if agg["confusion"]:
        print("\nTop 15 confusion pairs (expected_row -> predicted_row):")
        for (exp, pred), cnt in agg["confusion"].most_common(15):
            print(f"  row {exp:>3} -> row {pred:>3} : {cnt} time(s)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eval_multi_agent",
        description=(
            "Offline evaluation: runs RouterAgent + 4 specialists against "
            "ground-truth companies and reports classification accuracy."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples
--------
  # Evaluate one company
  python scripts/eval_multi_agent.py --company BCIPL

  # Evaluate all 9 GT companies
  python scripts/eval_multi_agent.py --all

  # Only run the pl_expense specialist for one company
  python scripts/eval_multi_agent.py --company BCIPL --agent pl_expense

Notes
-----
  Requires OPENROUTER_API_KEY env var for live model calls.
  Without it the agents return doubt records for every item.
  SUPABASE_* vars are stubbed automatically — no DB connection made.
""",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--company",
        choices=list(COMPANIES.keys()),
        metavar="COMPANY",
        help=(
            "Company to evaluate. Choices: "
            + ", ".join(COMPANIES.keys())
        ),
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Run evaluation for all 9 GT companies and print aggregate results.",
    )

    parser.add_argument(
        "--agent",
        choices=list(AGENT_RANGES.keys()),
        metavar="AGENT",
        help=(
            "Only run this specialist bucket (router still runs for all items). "
            "Choices: "
            + ", ".join(AGENT_RANGES.keys())
        ),
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable DEBUG logging for per-item detail.",
    )

    parser.add_argument(
        "--prompt-dir",
        metavar="DIR",
        help=(
            "Directory containing specialist prompt .md files.  When set, "
            "agents load prompts from DIR/{agent}_prompt.md instead of the "
            "default production path.  Useful for A/B-testing prompt versions."
        ),
    )

    parser.add_argument("--json", action="store_true", help="Output results as JSON.")
    parser.add_argument("--output", "-o", metavar="FILE", help="Write results to FILE.")

    return parser


def build_json_report(all_results: dict[str, dict], prompt_dir: str | None) -> dict:
    """Build a JSON-serialisable report from eval results."""
    from datetime import datetime
    companies = {}
    for company, result in all_results.items():
        c, w, d = result["correct"], result["wrong"], result["doubt"]
        companies[company] = {
            "total": result["total"], "correct": c, "wrong": w, "doubt": d,
            "misrouted": result["misrouted"],
            "accuracy": round(c / (c + w) * 100, 1) if (c + w) > 0 else None,
            "doubt_rate": round(d / result["total"] * 100, 1) if result["total"] > 0 else None,
            "per_agent": result["per_agent"],
        }
    # Build aggregate
    agg = _make_company_result()
    for result in all_results.values():
        agg["total"] += result["total"]
        agg["correct"] += result["correct"]
        agg["wrong"] += result["wrong"]
        agg["doubt"] += result["doubt"]
        agg["misrouted"] += result["misrouted"]
        for agent_name, counts in result["per_agent"].items():
            for k in ("correct", "wrong", "doubt"):
                agg["per_agent"][agent_name][k] += counts[k]
    ac, aw, ad = agg["correct"], agg["wrong"], agg["doubt"]
    return {
        "timestamp": datetime.now().isoformat(),
        "prompt_dir": prompt_dir,
        "companies": companies,
        "aggregate": {
            "total": agg["total"], "correct": ac, "wrong": aw, "doubt": ad,
            "misrouted": agg["misrouted"],
            "accuracy": round(ac / (ac + aw) * 100, 1) if (ac + aw) > 0 else None,
            "doubt_rate": round(ad / agg["total"] * 100, 1) if agg["total"] > 0 else None,
            "per_agent": agg["per_agent"],
        },
    }


def main() -> None:
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = build_parser()
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        format="%(levelname)s [%(name)s] %(message)s",
        level=log_level,
    )

    prompt_dir = getattr(args, "prompt_dir", None)
    if prompt_dir:
        print(f"Using custom prompts from: {prompt_dir}", flush=True)

    if args.all:
        all_results: dict[str, dict] = {}
        for company, meta in COMPANIES.items():
            print(f"\nEvaluating {company} ...", flush=True)
            try:
                result = eval_company(
                    company=company,
                    industry=meta["industry"],
                    agent_filter=getattr(args, "agent", None),
                    prompt_dir=prompt_dir,
                )
                all_results[company] = result  # Save BEFORE printing
            except FileNotFoundError as exc:
                print(f"  SKIP -- {exc}")
                continue
            except Exception as exc:
                print(f"  ERROR -- {exc}")
                logger.exception("Unexpected error for %s", company)
                continue
            try:
                print_company_report(company, result)
            except Exception as exc:
                print(f"  PRINT ERROR -- {exc}")

        print_aggregate_report(all_results)

        if args.json or args.output:
            report = build_json_report(all_results, prompt_dir)
            report_json = json.dumps(report, indent=2, default=str)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(report_json)
                print(f"\nJSON report written to {args.output}")
            if args.json:
                print(report_json)

    else:
        company = args.company
        meta = COMPANIES[company]
        agent_filter: str | None = getattr(args, "agent", None)

        print(f"Evaluating {company} (industry={meta['industry']}) ...", flush=True)
        result = eval_company(
            company=company,
            industry=meta["industry"],
            agent_filter=agent_filter,
            prompt_dir=prompt_dir,
        )
        print_company_report(company, result)

        if args.json or args.output:
            report = build_json_report({company: result}, prompt_dir)
            report_json = json.dumps(report, indent=2, default=str)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(report_json)
                print(f"\nJSON report written to {args.output}")
            if args.json:
                print(report_json)


if __name__ == "__main__":
    main()
