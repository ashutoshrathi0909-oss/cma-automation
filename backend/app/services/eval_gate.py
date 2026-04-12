"""Eval gate — safety mechanism preventing accuracy regressions.

Compares a proposed eval report against a baseline. The proposed change
passes the gate if:
  1. Aggregate accuracy does NOT regress (must be >= baseline)
  2. No individual company drops more than 2% (the PER_COMPANY_LIMIT)
     UNLESS the aggregate improved

If aggregate improved but a company dropped <= 2%, it's accepted
(some companies may shift slightly when rules improve overall accuracy).
"""

from __future__ import annotations

from dataclasses import dataclass, field


# Maximum per-company accuracy drop (percentage points) tolerated
# when aggregate accuracy is improving.
PER_COMPANY_LIMIT = 2.0


@dataclass
class EvalGateResult:
    """Result of comparing proposed eval against baseline."""
    passed: bool
    baseline_accuracy: float
    proposed_accuracy: float
    regressions: list[dict] = field(default_factory=list)
    improvements: list[dict] = field(default_factory=list)
    reason: str = ""


class EvalGate:
    """Compare baseline vs proposed eval reports."""

    def __init__(self, baseline: dict) -> None:
        self.baseline = baseline

    def compare(self, proposed: dict) -> EvalGateResult:
        """Compare proposed eval report against baseline.

        Parameters
        ----------
        proposed — JSON report from build_json_report (same schema as baseline)

        Returns
        -------
        EvalGateResult with pass/fail, regressions, and improvements
        """
        baseline_acc = self.baseline.get("aggregate", {}).get("accuracy", 0.0)
        proposed_acc = proposed.get("aggregate", {}).get("accuracy", 0.0)

        regressions: list[dict] = []
        improvements: list[dict] = []

        # Check per-company accuracy changes
        baseline_companies = self.baseline.get("companies", {})
        proposed_companies = proposed.get("companies", {})

        all_companies = set(baseline_companies) | set(proposed_companies)

        for company in all_companies:
            b_acc = baseline_companies.get(company, {}).get("accuracy")
            p_acc = proposed_companies.get(company, {}).get("accuracy")

            if b_acc is None or p_acc is None:
                continue

            delta = p_acc - b_acc
            entry = {
                "company": company,
                "baseline": b_acc,
                "proposed": p_acc,
                "delta": round(delta, 1),
            }

            if delta < 0:
                regressions.append(entry)
            elif delta > 0:
                improvements.append(entry)

        # Decision logic
        aggregate_improved = proposed_acc >= baseline_acc

        if not aggregate_improved:
            return EvalGateResult(
                passed=False,
                baseline_accuracy=baseline_acc,
                proposed_accuracy=proposed_acc,
                regressions=regressions,
                improvements=improvements,
                reason=f"Aggregate accuracy regressed: {baseline_acc}% -> {proposed_acc}%",
            )

        # Check per-company regressions against limit
        severe_regressions = [
            r for r in regressions
            if abs(r["delta"]) > PER_COMPANY_LIMIT
        ]

        if severe_regressions:
            return EvalGateResult(
                passed=False,
                baseline_accuracy=baseline_acc,
                proposed_accuracy=proposed_acc,
                regressions=regressions,
                improvements=improvements,
                reason=(
                    f"Per-company regression exceeds {PER_COMPANY_LIMIT}% limit: "
                    + ", ".join(f"{r['company']} ({r['delta']}%)" for r in severe_regressions)
                ),
            )

        return EvalGateResult(
            passed=True,
            baseline_accuracy=baseline_acc,
            proposed_accuracy=proposed_acc,
            regressions=regressions,
            improvements=improvements,
            reason="All checks passed",
        )
