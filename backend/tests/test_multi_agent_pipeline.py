"""Tests for MultiAgentPipeline — pure logic methods only (no DB).

All tests use:
    pipeline = MultiAgentPipeline.__new__(MultiAgentPipeline)

…so __init__ (which instantiates real agents via OpenAI/OpenRouter) is never
called.  Only the pure helper methods are exercised.
"""

from __future__ import annotations

import pytest

from app.services.classification.multi_agent_pipeline import (
    AUTO_APPROVE_THRESHOLD,
    DOUBT_THRESHOLD,
    HIGH_CONFIDENCE_FLOOR,
    MultiAgentPipeline,
)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _pipeline() -> MultiAgentPipeline:
    """Return a pipeline instance without calling __init__."""
    return MultiAgentPipeline.__new__(MultiAgentPipeline)


def _item(id: str = "i1", source_text: str = "Salaries & Wages") -> dict:
    return {"id": id, "source_text": source_text, "amount": 100_000.0, "section": "expenses"}


def _mapping(source_text: str, cma_field: str, cma_row: int) -> dict:
    return {"source_text": source_text, "cma_field_name": cma_field, "cma_input_row": cma_row}


# ── TestLearnedMappingsCheck ──────────────────────────────────────────────────


class TestLearnedMappingsCheck:
    def test_exact_match_skips_ai(self):
        """Items matching learned_mappings should be classified without AI."""
        pipeline = _pipeline()
        items = [_item("i1", "Salaries & Wages")]
        mappings = [_mapping("Salaries & Wages", "STAFF_COSTS", 55)]

        result = pipeline._check_learned_mappings(items, mappings)

        assert len(result["matched"]) == 1
        assert len(result["remaining"]) == 0

        hit = result["matched"][0]
        assert hit["item"]["id"] == "i1"
        assert hit["cma_field_name"] == "STAFF_COSTS"
        assert hit["cma_row"] == 55

    def test_no_mappings_returns_all_remaining(self):
        """When no learned_mappings, all items go to remaining."""
        pipeline = _pipeline()
        items = [_item("i1"), _item("i2", "Raw Materials")]

        result = pipeline._check_learned_mappings(items, [])

        assert result["matched"] == []
        assert len(result["remaining"]) == 2

    def test_case_insensitive_match(self):
        """Matching is case-insensitive."""
        pipeline = _pipeline()
        items = [_item("i1", "SALARIES & WAGES")]
        mappings = [_mapping("salaries & wages", "STAFF_COSTS", 55)]

        result = pipeline._check_learned_mappings(items, mappings)

        assert len(result["matched"]) == 1
        assert result["remaining"] == []

    def test_partial_match_leaves_remainder(self):
        """Items with no mapping hit go to remaining while hits go to matched."""
        pipeline = _pipeline()
        items = [
            _item("i1", "Salaries & Wages"),
            _item("i2", "Interest on TL"),
        ]
        mappings = [_mapping("Salaries & Wages", "STAFF_COSTS", 55)]

        result = pipeline._check_learned_mappings(items, mappings)

        assert len(result["matched"]) == 1
        assert len(result["remaining"]) == 1
        assert result["remaining"][0]["id"] == "i2"

    def test_whitespace_stripped_before_compare(self):
        """Leading/trailing whitespace is stripped before comparison."""
        pipeline = _pipeline()
        items = [_item("i1", "  Raw Materials  ")]
        mappings = [_mapping("Raw Materials", "RAW_MAT", 40)]

        result = pipeline._check_learned_mappings(items, mappings)
        assert len(result["matched"]) == 1


# ── TestBuildClassificationRecord ─────────────────────────────────────────────


class TestBuildClassificationRecord:
    def test_confident_result(self):
        """High-confidence classification builds correct record."""
        pipeline = _pipeline()
        item = _item("item-001", "Domestic Sales")
        clf = {
            "cma_code": "DOM_SALES",
            "cma_row": 22,
            "confidence": 0.92,
            "alternatives": [],
            "reasoning": None,
        }

        rec = pipeline._build_record(item, clf, "client-1", "B", "pl_income")

        assert rec["line_item_id"] == "item-001"
        assert rec["client_id"] == "client-1"
        assert rec["cma_field_name"] == "DOM_SALES"
        assert rec["cma_row"] == 22
        assert rec["cma_column"] == "B"
        assert rec["is_doubt"] is False
        assert rec["confidence_score"] == pytest.approx(0.92)
        assert rec["status"] == "approved"
        assert rec["classification_method"] == "pl_income"
        assert rec["doubt_reason"] is None

    def test_doubt_result(self):
        """Doubt builds record with is_doubt=True, status=needs_review."""
        pipeline = _pipeline()
        item = _item("item-002", "Misc Provision")
        clf = {
            "cma_code": "DOUBT",
            "cma_row": 0,
            "confidence": 0.0,
            "alternatives": [],
            "reasoning": "Cannot determine CMA row — please classify manually",
        }

        rec = pipeline._build_record(item, clf, "client-1", "C", "pl_expense")

        assert rec["is_doubt"] is True
        assert rec["status"] == "needs_review"
        assert rec["cma_field_name"] == "UNCLASSIFIED"
        assert rec["cma_row"] == 0
        assert rec["doubt_reason"] == "Cannot determine CMA row — please classify manually"

    def test_medium_confidence(self):
        """0.80–0.84 gets status=auto_classified (not approved, not needs_review)."""
        pipeline = _pipeline()
        item = _item("item-003", "Selling Expenses")
        clf = {
            "cma_code": "SELL_EXP",
            "cma_row": 60,
            "confidence": 0.82,
            "alternatives": [],
            "reasoning": None,
        }

        rec = pipeline._build_record(item, clf, "client-1", "B", "pl_expense")

        assert rec["is_doubt"] is False
        assert rec["status"] == "auto_classified"
        assert rec["confidence_score"] == pytest.approx(0.82)

    def test_low_confidence_forces_doubt(self):
        """Confidence below DOUBT_THRESHOLD (0.80) forces is_doubt=True."""
        pipeline = _pipeline()
        item = _item("item-004", "Unexplained Entry")
        clf = {
            "cma_code": "SOME_CODE",
            "cma_row": 45,
            "confidence": 0.50,
            "alternatives": [],
            "reasoning": "Uncertain classification",
        }

        rec = pipeline._build_record(item, clf, "client-1", "B", "pl_income")

        assert rec["is_doubt"] is True
        assert rec["status"] == "needs_review"

    def test_zero_cma_row_forces_doubt(self):
        """cma_row == 0 forces is_doubt=True regardless of high confidence."""
        pipeline = _pipeline()
        item = _item("item-005", "Opening Stock")
        clf = {
            "cma_code": "STOCK",
            "cma_row": 0,
            "confidence": 0.95,
            "alternatives": [],
            "reasoning": None,
        }

        rec = pipeline._build_record(item, clf, "client-1", "B", "bs_asset")

        assert rec["is_doubt"] is True
        assert rec["status"] == "needs_review"

    def test_ai_best_guess_always_set(self):
        """ai_best_guess is populated even on doubt records."""
        pipeline = _pipeline()
        item = _item("item-006")
        clf = {
            "cma_code": "DOUBT",
            "cma_row": 0,
            "confidence": 0.0,
            "alternatives": [],
            "reasoning": "Cannot determine",
        }

        rec = pipeline._build_record(item, clf, "client-1", "B", "router_unrouted")

        assert rec["ai_best_guess"] == "DOUBT"

    def test_alternatives_included(self):
        """alternative_fields list is passed through to the record."""
        pipeline = _pipeline()
        item = _item("item-007", "Interest on CC")
        alts = [{"cma_code": "INT_TL", "confidence": 0.70}]
        clf = {
            "cma_code": "INT_CC",
            "cma_row": 80,
            "confidence": 0.88,
            "alternatives": alts,
            "reasoning": None,
        }

        rec = pipeline._build_record(item, clf, "client-1", "B", "bs_liability")

        assert rec["alternative_fields"] == alts


# ── TestCombineResults ─────────────────────────────────────────────────────────


class TestCombineResults:
    def test_combine_merges_all_sources(self):
        """Combine merges learned + specialist + doubt records."""
        pipeline = _pipeline()
        learned = [{"line_item_id": "a"}]
        specialist = [{"line_item_id": "b"}, {"line_item_id": "c"}]
        doubts = [{"line_item_id": "d"}]

        combined = pipeline._combine_results(learned, specialist, doubts)

        assert len(combined) == 4
        ids = [r["line_item_id"] for r in combined]
        assert ids == ["a", "b", "c", "d"]

    def test_combine_empty_inputs(self):
        """All-empty inputs return an empty list."""
        pipeline = _pipeline()
        assert pipeline._combine_results([], [], []) == []

    def test_combine_preserves_order(self):
        """learned → specialist → doubts order is preserved."""
        pipeline = _pipeline()
        learned = [{"line_item_id": "L1"}, {"line_item_id": "L2"}]
        specialist = [{"line_item_id": "S1"}]
        doubts = [{"line_item_id": "D1"}, {"line_item_id": "D2"}]

        combined = pipeline._combine_results(learned, specialist, doubts)
        ids = [r["line_item_id"] for r in combined]

        assert ids == ["L1", "L2", "S1", "D1", "D2"]


# ── TestSummarize ──────────────────────────────────────────────────────────────


class TestSummarize:
    def _rec(self, is_doubt: bool, confidence: float) -> dict:
        return {"is_doubt": is_doubt, "confidence_score": confidence}

    def test_summarize_counts(self):
        """Summary correctly counts high/medium/needs_review."""
        pipeline = _pipeline()
        records = [
            self._rec(False, 0.92),  # high_confidence
            self._rec(False, 0.91),  # high_confidence
            self._rec(False, 0.82),  # medium_confidence
            self._rec(True, 0.0),   # needs_review
            self._rec(True, 0.5),   # needs_review
        ]

        summary = pipeline._summarize(records)

        assert summary["total"] == 5
        assert summary["high_confidence"] == 2
        assert summary["medium_confidence"] == 1
        assert summary["needs_review"] == 2

    def test_summarize_empty(self):
        """Empty records list returns all-zero summary."""
        pipeline = _pipeline()
        summary = pipeline._summarize([])

        assert summary == {
            "total": 0,
            "high_confidence": 0,
            "medium_confidence": 0,
            "needs_review": 0,
        }

    def test_summarize_all_high_confidence(self):
        """All high-confidence records produces correct summary."""
        pipeline = _pipeline()
        records = [self._rec(False, 0.95) for _ in range(10)]

        summary = pipeline._summarize(records)

        assert summary["total"] == 10
        assert summary["high_confidence"] == 10
        assert summary["medium_confidence"] == 0
        assert summary["needs_review"] == 0

    def test_summarize_all_doubts(self):
        """All doubt records produces correct summary."""
        pipeline = _pipeline()
        records = [self._rec(True, 0.0) for _ in range(5)]

        summary = pipeline._summarize(records)

        assert summary["total"] == 5
        assert summary["high_confidence"] == 0
        assert summary["medium_confidence"] == 0
        assert summary["needs_review"] == 5

    def test_boundary_at_floor(self):
        """Confidence exactly at HIGH_CONFIDENCE_FLOOR (0.85) counts as high."""
        pipeline = _pipeline()
        records = [self._rec(False, HIGH_CONFIDENCE_FLOOR)]

        summary = pipeline._summarize(records)

        assert summary["high_confidence"] == 1
        assert summary["medium_confidence"] == 0


# ── Constants sanity check ────────────────────────────────────────────────────


class TestConstants:
    def test_threshold_ordering(self):
        """DOUBT_THRESHOLD <= AUTO_APPROVE_THRESHOLD == HIGH_CONFIDENCE_FLOOR."""
        assert DOUBT_THRESHOLD <= AUTO_APPROVE_THRESHOLD
        assert AUTO_APPROVE_THRESHOLD == HIGH_CONFIDENCE_FLOOR
