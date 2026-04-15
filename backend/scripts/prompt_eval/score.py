"""Stage 4 — score Haiku predictions against expected classifications.

Reads all predictions_<agent>.json files from a run directory, joins to the
expected rows stored in batch_<agent>.json, and writes report.md.

Expected predictions_<agent>.json shape:
    {
      "agent": "pl_expense",
      "sub_batches": [
        {
          "sub_batch_id": "pl_expense_000",
          "classifications": [
            {"id": "...", "cma_row": 71, "cma_code": "...", "confidence": 0.9, ...},
            ...
          ]
        },
        ...
      ]
    }

Exit code: 0 on success, 2 if any regression-suite item failed.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = PROJECT_ROOT / "backend" / "tests" / "fixtures" / "prompt_eval"
RUNS_DIR = FIXTURES_DIR / "eval_runs"

DOUBT_CONFIDENCE_THRESHOLD = 0.80
HIGH_CONF_THRESHOLD = 0.85  # "high-confidence wrong" bucket

# Router scoring: map predicted bucket to the cma_row range that agent handles.
# A router prediction is correct if the predicted bucket contains the expected row.
AGENT_ROW_RANGES: dict[str, tuple[int, int]] = {
    "pl_income": (22, 34),
    "pl_expense": (41, 108),
    "bs_liability": (110, 160),
    "bs_asset": (161, 258),
}


def bucket_for_row(row: int) -> str | None:
    """Return the expected router bucket for a given cma_row."""
    for agent, (lo, hi) in AGENT_ROW_RANGES.items():
        if lo <= row <= hi:
            return agent
    return None


def load_run(run_dir: Path) -> dict:
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"No manifest.json in {run_dir}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def score_agent(run_dir: Path, agent: str) -> dict:
    """Score one agent's predictions. Returns a per-agent result dict."""
    batch_path = run_dir / f"batch_{agent}.json"
    pred_path = run_dir / f"predictions_{agent}.json"
    if not batch_path.exists():
        return {"agent": agent, "status": "no_batch"}
    if not pred_path.exists():
        return {"agent": agent, "status": "no_predictions", "batch": str(batch_path.name)}

    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    preds = json.loads(pred_path.read_text(encoding="utf-8"))

    # Flatten expected + meta
    expected: dict[str, int] = {}
    meta_by_id: dict[str, dict] = {}
    for sb in batch["sub_batches"]:
        expected.update({k: int(v) for k, v in sb["expected"].items()})
        for m in sb["items_meta"]:
            meta_by_id[m["id"]] = m

    # Flatten predictions — router uses 'routing' key with 'bucket';
    # specialists use 'classifications' with 'cma_row'.
    predicted: dict[str, dict] = {}
    pred_key = "routing" if agent == "router" else "classifications"
    for sb in preds.get("sub_batches", []):
        for clf in sb.get(pred_key, []):
            if "id" in clf:
                predicted[clf["id"]] = clf

    # Score
    correct = wrong = doubt = missing = 0
    high_conf_wrong = 0
    confusion: Counter = Counter()
    failures: list[dict] = []
    regression_failures: list[dict] = []

    for item_id, exp_row in expected.items():
        clf = predicted.get(item_id)
        if clf is None:
            missing += 1
            fail = {
                "id": item_id,
                "expected": exp_row,
                "predicted": None,
                "confidence": 0.0,
                "reasoning": "Missing from Haiku response",
                "regression_id": meta_by_id.get(item_id, {}).get("regression_id"),
            }
            failures.append(fail)
            if fail["regression_id"]:
                regression_failures.append(fail)
            continue
        if agent == "router":
            # Router is correct if predicted bucket contains expected row.
            pred_bucket = (clf.get("bucket") or "").strip()
            expected_bucket_val = bucket_for_row(exp_row)
            reason_txt = clf.get("reason", "")
            if not pred_bucket:
                # empty bucket -> treat as missing
                missing += 1
                fail = {
                    "id": item_id, "expected": exp_row, "predicted": None,
                    "confidence": 0.0, "reasoning": "Empty bucket in router prediction",
                    "regression_id": meta_by_id.get(item_id, {}).get("regression_id"),
                    "company": meta_by_id.get(item_id, {}).get("company"),
                }
                failures.append(fail)
                if fail["regression_id"]:
                    regression_failures.append(fail)
                continue
            if pred_bucket == expected_bucket_val:
                correct += 1
                continue
            wrong += 1
            confusion[(expected_bucket_val, pred_bucket)] += 1
            fail = {
                "id": item_id, "expected": exp_row, "predicted": pred_bucket,
                "expected_bucket": expected_bucket_val,
                "confidence": 1.0,  # router has no confidence; use 1.0 as placeholder
                "reasoning": reason_txt,
                "regression_id": meta_by_id.get(item_id, {}).get("regression_id"),
                "company": meta_by_id.get(item_id, {}).get("company"),
            }
            failures.append(fail)
            if fail["regression_id"]:
                regression_failures.append(fail)
            continue
        pred_row = int(clf.get("cma_row") or 0)
        conf = float(clf.get("confidence") or 0.0)
        is_doubt = pred_row == 0 or conf < DOUBT_CONFIDENCE_THRESHOLD
        if is_doubt:
            doubt += 1
            continue
        if pred_row == exp_row:
            correct += 1
            continue
        wrong += 1
        confusion[(exp_row, pred_row)] += 1
        if conf >= HIGH_CONF_THRESHOLD:
            high_conf_wrong += 1
        fail = {
            "id": item_id,
            "expected": exp_row,
            "predicted": pred_row,
            "confidence": conf,
            "reasoning": clf.get("reasoning", ""),
            "regression_id": meta_by_id.get(item_id, {}).get("regression_id"),
            "company": meta_by_id.get(item_id, {}).get("company"),
        }
        failures.append(fail)
        if fail["regression_id"]:
            regression_failures.append(fail)

    total = len(expected)
    return {
        "agent": agent,
        "status": "ok",
        "total": total,
        "correct": correct,
        "wrong": wrong,
        "doubt": doubt,
        "missing": missing,
        "high_conf_wrong": high_conf_wrong,
        "accuracy": round(correct / (correct + wrong) * 100, 1) if (correct + wrong) else None,
        "doubt_rate": round(doubt / total * 100, 1) if total else None,
        "confusion": confusion,
        "failures": failures,
        "regression_failures": regression_failures,
    }


def format_report(run_dir: Path, manifest: dict, results: list[dict]) -> str:
    lines = [
        f"# Prompt Eval Report — {manifest['timestamp']}",
        "",
        f"- Run dir: `{manifest['run_dir']}`",
        f"- Industry: {manifest['industry_type']}",
        f"- Companies: {', '.join(manifest['companies'])}",
        f"- Fresh items: {manifest['fresh_item_count']}   Regression items: {manifest['regression_item_count']}",
        "",
        "## Summary",
        "",
        "| Agent | Total | Correct | Wrong | Doubt | Missing | Accuracy | HighConfWrong |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        if r["status"] != "ok":
            lines.append(f"| {r['agent']} | — | — | — | — | — | {r['status']} | — |")
            continue
        lines.append(
            f"| {r['agent']} | {r['total']} | {r['correct']} | {r['wrong']} | "
            f"{r['doubt']} | {r['missing']} | "
            f"{r['accuracy'] if r['accuracy'] is not None else '—'}% | "
            f"{r['high_conf_wrong']} |"
        )
    lines.append("")

    # Regression failures (hard-fail surface)
    all_regression_failures = []
    for r in results:
        if r["status"] == "ok":
            all_regression_failures.extend(r["regression_failures"])
    if all_regression_failures:
        lines += ["## REGRESSION FAILURES (hard fail)", ""]
        for f in all_regression_failures:
            lines.append(
                f"- `{f.get('regression_id')}` expected=R{f['expected']} "
                f"predicted=R{f['predicted']} conf={f['confidence']:.2f}"
            )
        lines.append("")

    # Per-agent failure clusters
    for r in results:
        if r["status"] != "ok":
            continue
        if not r["failures"]:
            continue
        lines.append(f"## {r['agent']} — failures")
        lines.append("")
        # Cluster by (expected, predicted)
        clusters: defaultdict = defaultdict(list)
        for f in r["failures"]:
            clusters[(f["expected"], f["predicted"])].append(f)
        for (exp, pred), group in sorted(clusters.items(), key=lambda kv: -len(kv[1])):
            lines.append(f"### R{exp} → R{pred}  ({len(group)} items)")
            for f in group[:5]:
                conf = f"conf={f['confidence']:.2f}" if f["predicted"] is not None else "missing"
                company = f" [{f.get('company')}]" if f.get("company") else ""
                lines.append(f"  - `{f['id']}`{company} {conf}")
                if f.get("reasoning"):
                    snippet = f["reasoning"][:140].replace("\n", " ")
                    lines.append(f"    _reasoning_: {snippet}")
            if len(group) > 5:
                lines.append(f"  - ...and {len(group) - 5} more")
            lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(prog="prompt_eval.score")
    parser.add_argument("--run", required=True,
                        help="Run timestamp dir name (under eval_runs/)")
    parser.add_argument("--agents", default="all",
                        help="Comma-separated agents to score (default: all present).")
    args = parser.parse_args()

    run_dir = RUNS_DIR / args.run
    if not run_dir.exists():
        print(f"Run dir not found: {run_dir}", file=sys.stderr)
        sys.exit(1)

    manifest = load_run(run_dir)
    agents = (
        list(manifest.get("batches", {}).keys())
        if args.agents == "all"
        else [a.strip() for a in args.agents.split(",")]
    )

    results = [score_agent(run_dir, a) for a in agents]
    report = format_report(run_dir, manifest, results)
    report_path = run_dir / "report.md"
    report_path.write_text(report, encoding="utf-8")

    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(f"Report: {report_path.relative_to(PROJECT_ROOT)}")
    for r in results:
        if r["status"] == "ok":
            print(f"  {r['agent']:<14} acc={r['accuracy']}%  wrong={r['wrong']}  "
                  f"doubt={r['doubt']}  regression_fail={len(r['regression_failures'])}")
        else:
            print(f"  {r['agent']:<14} {r['status']}")

    # Hard-fail if any regression failed
    total_reg_fail = sum(
        len(r["regression_failures"]) for r in results if r["status"] == "ok"
    )
    if total_reg_fail:
        print(f"\nFAIL: {total_reg_fail} regression-suite item(s) regressed.", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
