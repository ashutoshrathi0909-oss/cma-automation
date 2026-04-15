"""Stage 2 — batch preparation.

Reads ground truth + regression suite, groups items by specialist bucket, writes
one batch file per agent under eval_runs/<timestamp>/. Each batch file contains
the fully-substituted prompt plus the item payload Haiku will classify.

Example
-------
    python -m prompt_eval.prepare_batch --sample 20
    python -m prompt_eval.prepare_batch --sample 20 --company BCIPL
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path

# Bootstrap (same pattern as eval_multi_agent.py)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))
os.environ.setdefault("SUPABASE_URL", "https://placeholder.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "placeholder")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "placeholder")
os.environ.setdefault("OPENROUTER_API_KEY", "placeholder")

PROMPTS_DIR = PROJECT_ROOT / "backend" / "app" / "services" / "classification" / "agents" / "prompts"
FIXTURES_DIR = PROJECT_ROOT / "backend" / "tests" / "fixtures" / "prompt_eval"
REGRESSION_PATH = FIXTURES_DIR / "regression_suite.json"
RUNS_DIR = FIXTURES_DIR / "eval_runs"
GT_DIR = PROJECT_ROOT / "CMA_Ground_Truth_v1" / "companies"

AGENT_KEYS = ["pl_income", "pl_expense", "bs_asset", "bs_liability"]
ALL_AGENTS = ["router"] + AGENT_KEYS
SUB_BATCH_SIZE = 10

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

AGENT_RANGES: dict[str, tuple[int, int]] = {
    "pl_income": (22, 34),
    "pl_expense": (41, 108),
    "bs_liability": (110, 160),
    "bs_asset": (161, 258),
}


def expected_bucket(cma_row: int) -> str | None:
    for bucket, (lo, hi) in AGENT_RANGES.items():
        if lo <= cma_row <= hi:
            return bucket
    return None


def load_gt_entries(company: str) -> list[dict]:
    gt_path = GT_DIR / company / "ground_truth_corrected.json"
    if not gt_path.exists():
        raise FileNotFoundError(f"GT file not found: {gt_path}")
    data = json.loads(gt_path.read_text(encoding="utf-8"))
    raw = data.get("database_entries", [])
    seen: set[tuple[str, int]] = set()
    out = []
    for entry in raw:
        key = (entry.get("raw_text", "").lower(), int(entry.get("cma_row", 0)))
        if key not in seen:
            seen.add(key)
            out.append(entry)
    return out


def entries_to_items(entries: list[dict]) -> tuple[list[dict], dict[str, int]]:
    items: list[dict] = []
    gt_lookup: dict[str, int] = {}
    for i, entry in enumerate(entries):
        item_id = f"gt-{i:04d}"
        raw_text = entry.get("raw_text", "")
        items.append({
            "id": item_id,
            "source_text": raw_text,
            "description": raw_text,
            "amount": entry.get("amount"),
            "section": entry.get("section"),
            "source_sheet": entry.get("sheet_name"),
            "page_type": "notes",
            "has_note_breakdowns": False,
        })
        gt_lookup[item_id] = int(entry.get("cma_row", 0))
    return items, gt_lookup


def load_substituted_prompt(agent: str) -> str:
    """Return the fully-substituted prompt for *agent*.

    Uses BaseAgent's substitution logic without instantiating the OpenAI client.
    """
    path = PROMPTS_DIR / f"{agent}_prompt.md"
    raw = path.read_text(encoding="utf-8")
    if agent == "router":
        return raw  # router has agent_key=None -> no substitution
    from app.services.classification import cell_types
    ctx = cell_types.get_agent_context(agent)
    return (
        raw
        .replace("{{section_structure}}", ctx["section_tree"])
        .replace("{{valid_output_rows}}", cell_types.valid_rows_csv(agent))
        .replace("{{notes_primary}}", cell_types.shared_notes_primary())
    )


def load_regression_items() -> list[dict]:
    """Return items + expected from regression_suite.json (empty if file missing)."""
    if not REGRESSION_PATH.exists():
        return []
    data = json.loads(REGRESSION_PATH.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    items = []
    for e in entries:
        # Each regression entry already stores an item shape + expected cma_row
        item = dict(e["item"])
        item["id"] = e["failure_id"]  # stable id from regression entry
        item["_expected_row"] = e["expected"]["cma_row"]
        item["_regression_id"] = e["failure_id"]
        item["_agent"] = e["agent"]
        items.append(item)
    return items


def sample_gt_items(company: str, sample_size: int, seed: int) -> list[dict]:
    """Sample up to *sample_size* items from a company's ground truth.

    Returns items in the classify_batch input shape, each tagged with _expected_row.
    """
    entries = load_gt_entries(company)
    if not entries:
        return []
    random.Random(seed).shuffle(entries)
    entries = entries[:sample_size]
    items, gt_lookup = entries_to_items(entries)
    for item in items:
        item["_expected_row"] = gt_lookup[item["id"]]
        item["_company"] = company
    return items


def route_items_by_expected(items: list[dict]) -> dict[str, list[dict]]:
    """Group items by the *expected* specialist bucket.

    NOTE: This is oracle-routing (using GT). The router's own accuracy is
    measured separately by the router batch. Here we want to isolate each
    specialist's classification accuracy from router misroutes.
    """
    buckets: dict[str, list[dict]] = {a: [] for a in AGENT_KEYS}
    unrouted: list[dict] = []
    for item in items:
        bucket = expected_bucket(item.get("_expected_row", 0))
        if bucket is None:
            unrouted.append(item)
        else:
            buckets[bucket].append(item)
    if unrouted:
        # Stash for inspection but do not fail
        buckets["_unrouted"] = unrouted
    return buckets


def make_sub_batches(items: list[dict], size: int = SUB_BATCH_SIZE) -> list[list[dict]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def build_user_content(items: list[dict], industry_type: str) -> str:
    """Build the JSON payload matching BaseAgent.classify_batch's format.

    Note: we embed per-item industry_type (derived from each item's _company)
    so that mixed-industry batches do not mislead the classifier. The
    batch-level industry_type still reflects the dominant industry for
    backward compatibility.
    """
    payload_items = [
        {
            "id": item["id"],
            "description": item.get("source_text") or item.get("description", ""),
            "amount": item.get("amount"),
            "section": item.get("section"),
            "page_type": item.get("page_type"),
            "source_sheet": item.get("source_sheet", ""),
            "has_note_breakdowns": item.get("has_note_breakdowns", False),
            "industry_type": COMPANIES.get(item.get("_company", ""), {}).get("industry", industry_type),
        }
        for item in items
    ]
    return json.dumps(
        {"industry_type": industry_type, "document_type": "annual_report", "items": payload_items},
        ensure_ascii=False,
        indent=2,
    )


def write_agent_batch(run_dir: Path, agent: str, items: list[dict], industry: str) -> Path:
    """Write one batch file for *agent* containing sub-batches for Haiku dispatch."""
    if not items:
        return Path()
    prompt = load_substituted_prompt(agent)
    sub_batches = make_sub_batches(items)
    batch_doc = {
        "agent": agent,
        "industry_type": industry,
        "system_prompt": prompt,
        "sub_batches": [
            {
                "sub_batch_id": f"{agent}_{i:03d}",
                "user_content": build_user_content(batch, industry),
                "expected": {it["id"]: it["_expected_row"] for it in batch},
                "items_meta": [
                    {"id": it["id"], "company": it.get("_company"),
                     "regression_id": it.get("_regression_id")}
                    for it in batch
                ],
            }
            for i, batch in enumerate(sub_batches)
        ],
    }
    out_path = run_dir / f"batch_{agent}.json"
    out_path.write_text(json.dumps(batch_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(prog="prompt_eval.prepare_batch")
    parser.add_argument("--sample", type=int, default=20,
                        help="Max fresh GT items per company (in addition to regression suite).")
    parser.add_argument("--company", choices=list(COMPANIES.keys()),
                        help="Single company (default: all 9).")
    parser.add_argument("--seed", type=int, default=42, help="Sampling seed.")
    parser.add_argument("--agents", default="all",
                        help="Comma-separated subset of agents (default: all).")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RUNS_DIR / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    # 1. Regression items (always included for specialists only)
    regression_items = load_regression_items()

    # 2. Fresh sampled items per company
    fresh: list[dict] = []
    companies = [args.company] if args.company else list(COMPANIES.keys())
    industries: dict[str, str] = {}
    for c in companies:
        industries[c] = COMPANIES[c]["industry"]
        try:
            fresh.extend(sample_gt_items(c, args.sample, args.seed))
        except FileNotFoundError:
            print(f"SKIP {c}: ground_truth_corrected.json not found", file=sys.stderr)

    # Determine dominant industry for batch (pick manufacturing if mixed)
    industry_counts: dict[str, int] = {}
    for item in fresh:
        ind = industries.get(item.get("_company", ""), "manufacturing")
        industry_counts[ind] = industry_counts.get(ind, 0) + 1
    industry = max(industry_counts, key=industry_counts.get) if industry_counts else "manufacturing"

    # 3. Route fresh items by expected bucket; regression items already know their agent
    bucketed = route_items_by_expected(fresh)
    for ritem in regression_items:
        bucketed.setdefault(ritem["_agent"], []).append(ritem)

    # 4. Filter agents
    selected = ALL_AGENTS if args.agents == "all" else [a.strip() for a in args.agents.split(",")]

    # 5. Write per-agent batch files
    #    Router gets the FULL fresh+regression item pool (it's supposed to bucket them all)
    written: dict[str, str] = {}
    for agent in selected:
        if agent == "router":
            all_items = fresh + regression_items
            if not all_items:
                continue
            p = write_agent_batch(run_dir, "router", all_items, industry)
        else:
            items = bucketed.get(agent, [])
            if not items:
                continue
            p = write_agent_batch(run_dir, agent, items, industry)
        if p.name:
            written[agent] = str(p.relative_to(PROJECT_ROOT))

    # 6. Manifest
    manifest = {
        "timestamp": timestamp,
        "run_dir": str(run_dir.relative_to(PROJECT_ROOT)),
        "industry_type": industry,
        "sample_per_company": args.sample,
        "seed": args.seed,
        "companies": companies,
        "batches": written,
        "fresh_item_count": len(fresh),
        "regression_item_count": len(regression_items),
        "unrouted_count": len(bucketed.get("_unrouted", [])),
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(f"Run: {run_dir.relative_to(PROJECT_ROOT)}")
    print(f"Fresh items: {len(fresh)}  Regression items: {len(regression_items)}")
    print(f"Batches written: {list(written.keys())}")


if __name__ == "__main__":
    main()
