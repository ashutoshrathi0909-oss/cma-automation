"""Phase 5A: Fuzzy Matcher unit tests.

TDD — RED phase: written BEFORE implementation.

Coverage target: 100% on services/classification/fuzzy_matcher.py

Tests verify:
- Learned mappings checked BEFORE reference mappings (critical constraint)
- Score >= 85 returns confident match
- Score < 85 falls through to reference
- Industry type respected for learned queries
- Token-set-ratio handles word-order variation
"""

import pytest
from unittest.mock import MagicMock, patch


# ── Sample DB rows ──────────────────────────────────────────────────────────────

LEARNED_SALARY_SERVICE = {
    "source_text": "Salary and Wages",
    "cma_field_name": "Salary and staff expenses",
    "cma_input_row": 67,
    "industry_type": "service",
    "times_used": 5,
}

LEARNED_WAGES_MANUFACTURING = {
    "source_text": "Wages and Salaries",
    "cma_field_name": "Wages",
    "cma_input_row": 45,
    "industry_type": "manufacturing",
    "times_used": 3,
}

REFERENCE_WAGES = {
    "item_name": "Wages and Salaries",
    "cma_form_item": "Wages",
    "cma_input_row": 45,
    "broad_classification": "manufacturing_expense",
    "source_sheet": "PNL",
}

REFERENCE_SALARY = {
    "item_name": "Salary and Staff Expenses",
    "cma_form_item": "Salary and staff expenses",
    "cma_input_row": 67,
    "broad_classification": "admin_expense",
    "source_sheet": "PNL",
}

REFERENCE_RAW_MATERIALS = {
    "item_name": "Raw Materials Consumed",
    "cma_form_item": "Raw Materials Consumed (Indigenous)",
    "cma_input_row": 42,
    "broad_classification": "manufacturing_expense",
    "source_sheet": "PNL",
}

REFERENCE_DEPRECIATION = {
    "item_name": "Depreciation on Fixed Assets",
    "cma_form_item": "Depreciation (Manufacturing)",
    "cma_input_row": 56,
    "broad_classification": "manufacturing_expense",
    "source_sheet": "PNL",
}

REFERENCE_NULL_ROW = {
    "item_name": "Some Subtotal Header",
    "cma_form_item": None,
    "cma_input_row": None,  # NULL — must be skipped
    "broad_classification": None,
    "source_sheet": "PNL",
}


# ── Mock factory ────────────────────────────────────────────────────────────────


def _make_service(learned_data=None, reference_data=None):
    """Build mock Supabase service with per-table side_effect."""
    mock_service = MagicMock()
    learned = learned_data if learned_data is not None else []
    reference = reference_data if reference_data is not None else []

    def table_side_effect(table_name):
        t = MagicMock()
        if table_name == "learned_mappings":
            t.select.return_value.eq.return_value.execute.return_value.data = learned
        elif table_name == "cma_reference_mappings":
            t.select.return_value.execute.return_value.data = reference
        return t

    mock_service.table.side_effect = table_side_effect
    return mock_service


# ══════════════════════════════════════════════════════════════════════════════
# FuzzyMatchResult dataclass
# ══════════════════════════════════════════════════════════════════════════════


class TestFuzzyMatchResult:
    def test_fuzzy_match_result_has_required_fields(self):
        """FuzzyMatchResult dataclass has all expected fields."""
        from app.services.classification.fuzzy_matcher import FuzzyMatchResult

        result = FuzzyMatchResult(
            cma_field_name="Wages",
            cma_row=45,
            cma_sheet="input_sheet",
            broad_classification="manufacturing_expense",
            score=92.0,
            source="reference",
        )
        assert result.cma_field_name == "Wages"
        assert result.cma_row == 45
        assert result.cma_sheet == "input_sheet"
        assert result.score == 92.0
        assert result.source == "reference"


# ══════════════════════════════════════════════════════════════════════════════
# FuzzyMatcher.match() — core behaviour
# ══════════════════════════════════════════════════════════════════════════════


class TestFuzzyMatcherCore:
    """Tests for FuzzyMatcher.match()."""

    def test_fuzzy_exact_match_score_100(self):
        """Exact text match returns score 100."""
        from app.services.classification.fuzzy_matcher import FuzzyMatcher

        mock_service = _make_service(
            learned_data=[],
            reference_data=[REFERENCE_WAGES],
        )

        with patch(
            "app.services.classification.fuzzy_matcher.get_service_client",
            return_value=mock_service,
        ):
            matcher = FuzzyMatcher()
            results = matcher.match("Wages and Salaries", "manufacturing")

        assert len(results) > 0
        assert results[0].score == 100.0

    def test_fuzzy_close_match_above_85(self):
        """Slightly different text returns score >= 85."""
        from app.services.classification.fuzzy_matcher import FuzzyMatcher

        mock_service = _make_service(
            learned_data=[],
            reference_data=[REFERENCE_WAGES],
        )

        with patch(
            "app.services.classification.fuzzy_matcher.get_service_client",
            return_value=mock_service,
        ):
            matcher = FuzzyMatcher()
            results = matcher.match("Salary and Wages", "manufacturing")  # slight variation

        assert len(results) > 0
        assert results[0].score >= 85.0

    def test_fuzzy_no_match_returns_low_score(self):
        """Unrelated text returns low match scores."""
        from app.services.classification.fuzzy_matcher import FuzzyMatcher

        mock_service = _make_service(
            learned_data=[],
            reference_data=[REFERENCE_RAW_MATERIALS],
        )

        with patch(
            "app.services.classification.fuzzy_matcher.get_service_client",
            return_value=mock_service,
        ):
            matcher = FuzzyMatcher()
            results = matcher.match("XYZ Corporation Misc Entry 999", "manufacturing")

        # Either no results or all below threshold
        if results:
            assert results[0].score < 85.0

    def test_fuzzy_returns_top_n_matches(self):
        """top_n parameter limits result count."""
        from app.services.classification.fuzzy_matcher import FuzzyMatcher

        mock_service = _make_service(
            learned_data=[],
            reference_data=[REFERENCE_WAGES, REFERENCE_SALARY, REFERENCE_RAW_MATERIALS],
        )

        with patch(
            "app.services.classification.fuzzy_matcher.get_service_client",
            return_value=mock_service,
        ):
            matcher = FuzzyMatcher()
            results = matcher.match("Wages", "manufacturing", top_n=2)

        assert len(results) <= 2

    def test_fuzzy_skips_reference_items_with_null_cma_row(self):
        """Reference items with NULL cma_input_row are skipped."""
        from app.services.classification.fuzzy_matcher import FuzzyMatcher

        # Only NULL-row items in reference — should return nothing useful
        mock_service = _make_service(
            learned_data=[],
            reference_data=[REFERENCE_NULL_ROW],
        )

        with patch(
            "app.services.classification.fuzzy_matcher.get_service_client",
            return_value=mock_service,
        ):
            matcher = FuzzyMatcher()
            results = matcher.match("Some Subtotal Header", "manufacturing")

        # Items with NULL cma_input_row must not appear in results
        for r in results:
            assert r.cma_row is not None

    def test_fuzzy_token_set_ratio_handles_word_order(self):
        """Word-order variation still matches (token_set_ratio is order-insensitive)."""
        from app.services.classification.fuzzy_matcher import FuzzyMatcher

        mock_service = _make_service(
            learned_data=[],
            reference_data=[REFERENCE_RAW_MATERIALS],  # "Raw Materials Consumed"
        )

        with patch(
            "app.services.classification.fuzzy_matcher.get_service_client",
            return_value=mock_service,
        ):
            matcher = FuzzyMatcher()
            # Reversed word order
            results = matcher.match("Consumed Raw Materials", "manufacturing")

        assert len(results) > 0
        # token_set_ratio should give high score for word-order variants
        assert results[0].score >= 85.0

    def test_fuzzy_special_characters_handled(self):
        """Special chars (&, /, parentheses) in text do not crash the matcher."""
        from app.services.classification.fuzzy_matcher import FuzzyMatcher

        reference_with_special = {
            **REFERENCE_SALARY,
            "item_name": "Salary & Staff Expenses (Admin)",
        }
        mock_service = _make_service(
            learned_data=[],
            reference_data=[reference_with_special],
        )

        with patch(
            "app.services.classification.fuzzy_matcher.get_service_client",
            return_value=mock_service,
        ):
            matcher = FuzzyMatcher()
            # Should not raise
            results = matcher.match("Salary & Staff (Admin) Expenses", "service")

        assert isinstance(results, list)

    def test_fuzzy_empty_learned_and_reference_returns_empty(self):
        """No learned or reference data returns empty list."""
        from app.services.classification.fuzzy_matcher import FuzzyMatcher

        mock_service = _make_service(learned_data=[], reference_data=[])

        with patch(
            "app.services.classification.fuzzy_matcher.get_service_client",
            return_value=mock_service,
        ):
            matcher = FuzzyMatcher()
            results = matcher.match("Wages", "manufacturing")

        assert results == []


# ══════════════════════════════════════════════════════════════════════════════
# Learned mappings priority (critical constraint)
# ══════════════════════════════════════════════════════════════════════════════


class TestLearnedMappingPriority:
    """Verify learned_mappings are ALWAYS checked before cma_reference_mappings."""

    def test_fuzzy_checks_learned_before_reference(self):
        """Learned mappings table is queried before reference mappings table."""
        from app.services.classification.fuzzy_matcher import FuzzyMatcher

        call_order = []

        def table_side_effect(table_name):
            call_order.append(table_name)
            t = MagicMock()
            if table_name == "learned_mappings":
                t.select.return_value.eq.return_value.execute.return_value.data = []
            elif table_name == "cma_reference_mappings":
                t.select.return_value.execute.return_value.data = [REFERENCE_WAGES]
            return t

        mock_service = MagicMock()
        mock_service.table.side_effect = table_side_effect

        with patch(
            "app.services.classification.fuzzy_matcher.get_service_client",
            return_value=mock_service,
        ):
            matcher = FuzzyMatcher()
            matcher.match("Wages", "manufacturing")

        # learned_mappings must be queried BEFORE cma_reference_mappings
        assert "learned_mappings" in call_order
        assert "cma_reference_mappings" in call_order
        learned_idx = call_order.index("learned_mappings")
        reference_idx = call_order.index("cma_reference_mappings")
        assert learned_idx < reference_idx, (
            "learned_mappings must be queried before cma_reference_mappings"
        )

    def test_fuzzy_learned_match_takes_priority_over_reference(self):
        """When learned has a confident match, reference is NOT queried."""
        from app.services.classification.fuzzy_matcher import FuzzyMatcher

        call_order = []

        def table_side_effect(table_name):
            call_order.append(table_name)
            t = MagicMock()
            if table_name == "learned_mappings":
                # Return exact learned match
                t.select.return_value.eq.return_value.execute.return_value.data = [
                    LEARNED_SALARY_SERVICE
                ]
            elif table_name == "cma_reference_mappings":
                t.select.return_value.execute.return_value.data = [REFERENCE_WAGES]
            return t

        mock_service = MagicMock()
        mock_service.table.side_effect = table_side_effect

        with patch(
            "app.services.classification.fuzzy_matcher.get_service_client",
            return_value=mock_service,
        ):
            matcher = FuzzyMatcher()
            results = matcher.match("Salary and Wages", "service")

        # Result should be from learned (source="learned")
        assert len(results) > 0
        assert results[0].source == "learned"
        # Reference should NOT be queried when learned has confident match
        assert "cma_reference_mappings" not in call_order

    def test_fuzzy_learned_result_has_source_learned(self):
        """FuzzyMatchResult from learned_mappings has source='learned'."""
        from app.services.classification.fuzzy_matcher import FuzzyMatcher

        mock_service = _make_service(
            learned_data=[LEARNED_SALARY_SERVICE],
            reference_data=[],
        )

        with patch(
            "app.services.classification.fuzzy_matcher.get_service_client",
            return_value=mock_service,
        ):
            matcher = FuzzyMatcher()
            results = matcher.match("Salary and Wages", "service")

        assert len(results) > 0
        assert results[0].source == "learned"

    def test_fuzzy_reference_result_has_source_reference(self):
        """FuzzyMatchResult from cma_reference_mappings has source='reference'."""
        from app.services.classification.fuzzy_matcher import FuzzyMatcher

        mock_service = _make_service(
            learned_data=[],  # No learned matches
            reference_data=[REFERENCE_WAGES],
        )

        with patch(
            "app.services.classification.fuzzy_matcher.get_service_client",
            return_value=mock_service,
        ):
            matcher = FuzzyMatcher()
            results = matcher.match("Wages and Salaries", "manufacturing")

        assert len(results) > 0
        assert results[0].source == "reference"

    def test_fuzzy_respects_industry_type_filter(self):
        """Learned mappings query uses industry_type as filter."""
        from app.services.classification.fuzzy_matcher import FuzzyMatcher

        queries = []

        def table_side_effect(table_name):
            t = MagicMock()
            if table_name == "learned_mappings":
                def eq_side_effect(col, val):
                    queries.append((col, val))
                    inner = MagicMock()
                    inner.execute.return_value.data = []
                    return inner

                t.select.return_value.eq.side_effect = eq_side_effect
            elif table_name == "cma_reference_mappings":
                t.select.return_value.execute.return_value.data = []
            return t

        mock_service = MagicMock()
        mock_service.table.side_effect = table_side_effect

        with patch(
            "app.services.classification.fuzzy_matcher.get_service_client",
            return_value=mock_service,
        ):
            matcher = FuzzyMatcher()
            matcher.match("Wages", "service")

        # Verify industry_type was used as a filter
        assert any(col == "industry_type" and val == "service" for col, val in queries)

    def test_fuzzy_low_learned_score_falls_through_to_reference(self):
        """When learned score < 85, reference mappings ARE queried."""
        from app.services.classification.fuzzy_matcher import FuzzyMatcher

        call_order = []

        def table_side_effect(table_name):
            call_order.append(table_name)
            t = MagicMock()
            if table_name == "learned_mappings":
                # Return a learned mapping that won't match well
                t.select.return_value.eq.return_value.execute.return_value.data = [
                    {
                        "source_text": "Completely Unrelated Term ZZZZZ",
                        "cma_field_name": "Wages",
                        "cma_input_row": 45,
                        "industry_type": "manufacturing",
                    }
                ]
            elif table_name == "cma_reference_mappings":
                t.select.return_value.execute.return_value.data = [REFERENCE_WAGES]
            return t

        mock_service = MagicMock()
        mock_service.table.side_effect = table_side_effect

        with patch(
            "app.services.classification.fuzzy_matcher.get_service_client",
            return_value=mock_service,
        ):
            matcher = FuzzyMatcher()
            matcher.match("Wages and Salaries", "manufacturing")

        # Both tables must be queried when learned has low score
        assert "learned_mappings" in call_order
        assert "cma_reference_mappings" in call_order


# ══════════════════════════════════════════════════════════════════════════════
# Real CMA field mappings (integration-style with real reference data)
# ══════════════════════════════════════════════════════════════════════════════


class TestRealCMAMappings:
    """Tests using actual CMA field names to verify correct field resolution."""

    def test_wages_maps_to_correct_cma_row(self):
        """'Wages and Salaries' reference item maps to row 45 (Wages)."""
        from app.services.classification.fuzzy_matcher import FuzzyMatcher

        mock_service = _make_service(
            learned_data=[],
            reference_data=[REFERENCE_WAGES],
        )

        with patch(
            "app.services.classification.fuzzy_matcher.get_service_client",
            return_value=mock_service,
        ):
            matcher = FuzzyMatcher()
            results = matcher.match("Wages and Salaries", "manufacturing")

        assert len(results) > 0
        assert results[0].cma_field_name == "Wages"
        assert results[0].cma_row == 45

    def test_raw_materials_consumed_maps_correctly(self):
        """'Raw Materials Consumed' maps to cma_input_row 42."""
        from app.services.classification.fuzzy_matcher import FuzzyMatcher

        mock_service = _make_service(
            learned_data=[],
            reference_data=[REFERENCE_RAW_MATERIALS],
        )

        with patch(
            "app.services.classification.fuzzy_matcher.get_service_client",
            return_value=mock_service,
        ):
            matcher = FuzzyMatcher()
            results = matcher.match("Raw Materials Consumed", "manufacturing")

        assert len(results) > 0
        assert results[0].cma_row == 42

    def test_cma_sheet_is_input_sheet_for_pnl_fields(self):
        """Fields in PNL_FIELD_TO_ROW resolve to cma_sheet='input_sheet'."""
        from app.services.classification.fuzzy_matcher import FuzzyMatcher

        mock_service = _make_service(
            learned_data=[],
            reference_data=[REFERENCE_WAGES],
        )

        with patch(
            "app.services.classification.fuzzy_matcher.get_service_client",
            return_value=mock_service,
        ):
            matcher = FuzzyMatcher()
            results = matcher.match("Wages and Salaries", "manufacturing")

        assert len(results) > 0
        assert results[0].cma_sheet == "input_sheet"

    def test_reference_cma_form_item_returned_not_item_name(self):
        """Returned cma_field_name is cma_form_item, NOT item_name from reference table."""
        from app.services.classification.fuzzy_matcher import FuzzyMatcher

        mock_service = _make_service(
            learned_data=[],
            reference_data=[REFERENCE_RAW_MATERIALS],
        )

        with patch(
            "app.services.classification.fuzzy_matcher.get_service_client",
            return_value=mock_service,
        ):
            matcher = FuzzyMatcher()
            results = matcher.match("Raw Materials Consumed", "manufacturing")

        assert len(results) > 0
        # Should return cma_form_item ("Raw Materials Consumed (Indigenous)"),
        # NOT item_name ("Raw Materials Consumed")
        assert results[0].cma_field_name == "Raw Materials Consumed (Indigenous)"
        assert results[0].cma_field_name != "Raw Materials Consumed"

    def test_salary_learned_mapping_for_service_industry(self):
        """For service industry, learned mapping returns 'Salary and staff expenses' (row 67)."""
        from app.services.classification.fuzzy_matcher import FuzzyMatcher

        mock_service = _make_service(
            learned_data=[LEARNED_SALARY_SERVICE],
            reference_data=[],
        )

        with patch(
            "app.services.classification.fuzzy_matcher.get_service_client",
            return_value=mock_service,
        ):
            matcher = FuzzyMatcher()
            results = matcher.match("Salary and Wages", "service")

        assert len(results) > 0
        assert results[0].cma_field_name == "Salary and staff expenses"
        assert results[0].cma_row == 67


# ══════════════════════════════════════════════════════════════════════════════
# Edge / guard coverage
# ══════════════════════════════════════════════════════════════════════════════


class TestFuzzyMatcherEdgeCases:
    """Targeted tests to hit safety branches not covered by happy-path tests."""

    def test_learned_mapping_with_no_source_text_returns_empty(self):
        """Learned rows that all lack source_text produce no results (line 137 guard)."""
        from app.services.classification.fuzzy_matcher import FuzzyMatcher

        # Row with source_text=None should be skipped, making choices dict empty
        broken_learned = [{"source_text": None, "cma_field_name": "Wages", "cma_input_row": 45}]
        mock_service = _make_service(learned_data=broken_learned, reference_data=[])

        with patch(
            "app.services.classification.fuzzy_matcher.get_service_client",
            return_value=mock_service,
        ):
            matcher = FuzzyMatcher()
            results = matcher.match("Wages", "manufacturing")

        assert results == []

    def test_reference_mapping_with_no_item_name_returns_empty(self):
        """Reference rows that all lack item_name produce no results (line 176 guard)."""
        from app.services.classification.fuzzy_matcher import FuzzyMatcher

        broken_reference = [{"item_name": None, "cma_form_item": "Wages", "cma_input_row": 45, "broad_classification": ""}]
        mock_service = _make_service(learned_data=[], reference_data=broken_reference)

        with patch(
            "app.services.classification.fuzzy_matcher.get_service_client",
            return_value=mock_service,
        ):
            matcher = FuzzyMatcher()
            results = matcher.match("Wages", "manufacturing")

        assert results == []

    def test_reference_row_with_null_cma_form_item_is_skipped(self):
        """Reference rows with cma_form_item=None are skipped (line 191 safety guard)."""
        from app.services.classification.fuzzy_matcher import FuzzyMatcher

        # This row passes the cma_input_row != None filter but has no cma_form_item
        null_form_item_row = {
            "item_name": "Wages and Salaries",
            "cma_form_item": None,   # null form item — must be skipped
            "cma_input_row": 45,     # non-null row, passes earlier filter
            "broad_classification": "",
        }
        mock_service = _make_service(learned_data=[], reference_data=[null_form_item_row])

        with patch(
            "app.services.classification.fuzzy_matcher.get_service_client",
            return_value=mock_service,
        ):
            matcher = FuzzyMatcher()
            results = matcher.match("Wages and Salaries", "manufacturing")

        # The row with null cma_form_item must not appear in results
        for r in results:
            assert r.cma_field_name is not None
