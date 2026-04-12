# backend/tests/test_eval_gate.py
"""Phase 3: Eval gate — TDD RED phase.

Tests the safety mechanism that prevents accuracy regressions.
"""

import pytest


class TestEvalGateCompare:
    def test_import_succeeds(self):
        from app.services.eval_gate import EvalGate  # noqa: F401

    def test_rejects_aggregate_regression(self):
        from app.services.eval_gate import EvalGate
        baseline = {"aggregate": {"accuracy": 85.0}, "companies": {}}
        proposed = {"aggregate": {"accuracy": 78.0}, "companies": {}}
        gate = EvalGate(baseline)
        result = gate.compare(proposed)
        assert result.passed is False

    def test_rejects_per_company_regression_above_limit(self):
        from app.services.eval_gate import EvalGate
        baseline = {"aggregate": {"accuracy": 85.0}, "companies": {"BCIPL": {"accuracy": 82.0}}}
        proposed = {"aggregate": {"accuracy": 85.0}, "companies": {"BCIPL": {"accuracy": 79.0}}}
        gate = EvalGate(baseline)
        result = gate.compare(proposed)
        assert result.passed is False
        assert len(result.regressions) == 1
        assert result.regressions[0]["company"] == "BCIPL"

    def test_accepts_improvement(self):
        from app.services.eval_gate import EvalGate
        baseline = {"aggregate": {"accuracy": 82.0}, "companies": {"BCIPL": {"accuracy": 80.0}}}
        proposed = {"aggregate": {"accuracy": 86.0}, "companies": {"BCIPL": {"accuracy": 85.0}}}
        gate = EvalGate(baseline)
        result = gate.compare(proposed)
        assert result.passed is True
        assert len(result.improvements) == 1

    def test_accepts_small_per_company_drop_if_aggregate_up(self):
        from app.services.eval_gate import EvalGate
        baseline = {"aggregate": {"accuracy": 82.0}, "companies": {"BCIPL": {"accuracy": 80.0}}}
        proposed = {"aggregate": {"accuracy": 83.0}, "companies": {"BCIPL": {"accuracy": 78.5}}}
        gate = EvalGate(baseline)
        result = gate.compare(proposed)
        # 1.5% drop is within 2% limit AND aggregate improved
        assert result.passed is True

    def test_result_has_required_fields(self):
        from app.services.eval_gate import EvalGate, EvalGateResult
        baseline = {"aggregate": {"accuracy": 85.0}, "companies": {}}
        proposed = {"aggregate": {"accuracy": 86.0}, "companies": {}}
        gate = EvalGate(baseline)
        result = gate.compare(proposed)
        assert isinstance(result, EvalGateResult)
        assert hasattr(result, "passed")
        assert hasattr(result, "baseline_accuracy")
        assert hasattr(result, "proposed_accuracy")
        assert hasattr(result, "regressions")
        assert hasattr(result, "improvements")
