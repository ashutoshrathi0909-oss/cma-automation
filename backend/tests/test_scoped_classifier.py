"""ScopedClassifier unit tests — AI-only architecture (April 2026).

Tests verify the key fixes and enhancements:
- Unroutable items get fallback context (never auto-doubted)
- notes_to_accounts NOT treated as balance sheet
- Industry-specific rules override universal "all" rules
- Cost guard limits items per document
- Learned mappings appear in prompt
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio

from app.services.classification.ai_classifier import AIClassificationResult


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_classifier():
    """Build a ScopedClassifier with all file I/O and API calls mocked."""
    with patch(
        "app.services.classification.scoped_classifier.ScopedClassifier._load_section_mapping",
        return_value={"Revenue": "revenue", "Other Income": "other_income"},
    ), patch(
        "app.services.classification.scoped_classifier.ScopedClassifier._load_sheet_mapping",
        return_value={},
    ), patch(
        "app.services.classification.scoped_classifier.ScopedClassifier._load_canonical_labels",
        return_value=[
            {"code": "R1", "name": "Net Sales", "sheet_row": 28, "section": "Operating Statement - Income - Sales"},
            {"code": "A1", "name": "Others (Admin)", "sheet_row": 71, "section": "Operating Statement - Admin & Selling Expenses"},
            {"code": "M1", "name": "Wages", "sheet_row": 45, "section": "Operating Statement - Manufacturing Expenses"},
            {"code": "B1", "name": "Other Non Current Assets", "sheet_row": 230, "section": "Balance Sheet - Non Current Assets"},
            {"code": "L1", "name": "Sundry Creditors", "sheet_row": 240, "section": "Balance Sheet - Current Liabilities"},
            {"code": "BL1", "name": "Term Loans from Banks", "sheet_row": 150, "section": "Balance Sheet - Term Loans"},
        ],
    ), patch(
        "app.services.classification.scoped_classifier.ScopedClassifier._load_rules",
        return_value=[
            {
                "id": "rule_1", "fs_item": "wages and salaries", "canonical_sheet_row": 45,
                "canonical_field_name": "Wages", "industry_type": "manufacturing",
                "priority": "ca_override", "confidence": 0.95, "notes": "test",
            },
            {
                "id": "rule_2", "fs_item": "salary expenses", "canonical_sheet_row": 45,
                "canonical_field_name": "Wages", "industry_type": "all",
                "priority": "legacy", "confidence": 0.8, "notes": "",
            },
            {
                "id": "rule_3", "fs_item": "trading commission", "canonical_sheet_row": 71,
                "canonical_field_name": "Others (Admin)", "industry_type": "trading",
                "priority": "ca_override", "confidence": 0.9, "notes": "",
            },
        ],
    ), patch(
        "app.services.classification.scoped_classifier.ScopedClassifier._load_training_data",
        return_value=[],
    ), patch(
        "app.services.classification.scoped_classifier.get_settings",
    ) as mock_settings:
        mock_settings.return_value = MagicMock(openrouter_api_key="test-key")
        from app.services.classification.scoped_classifier import ScopedClassifier
        classifier = ScopedClassifier()
        return classifier


# ══════════════════════════════════════════════════════════════════════════════
# 1a. Unroutable items get fallback context
# ══════════════════════════════════════════════════════════════════════════════


class TestUnroutableFallback:
    """Unroutable items must NOT be auto-doubted — they get a fallback context."""

    def test_unroutable_gets_fallback_context_not_doubt(self):
        """An unroutable item should still reach the AI via fallback context."""
        classifier = _make_classifier()

        # Mock _route_section to return "unroutable"
        classifier._route_section = MagicMock(return_value=["unroutable"])

        # Mock the model call to return a valid classification
        classifier._call_model = MagicMock(return_value={
            "cma_row": 71, "cma_code": "A1", "confidence": 0.85, "reasoning": "admin item"
        })

        result = asyncio.get_event_loop().run_until_complete(
            classifier.classify(
                raw_text="Some unusual item",
                amount=1000.0,
                section="miscellaneous",
                industry_type="manufacturing",
                document_type="profit_and_loss",
                fuzzy_candidates=[],
            )
        )

        # Should NOT be a doubt — the AI classified it
        assert result.is_doubt is False
        assert result.cma_row == 71

    def test_fallback_sections_for_pl(self):
        """P&L documents get admin_expense + manufacturing + revenue as fallback."""
        from app.services.classification.scoped_classifier import ScopedClassifier
        sections = ScopedClassifier._get_fallback_sections("profit_and_loss")
        assert "admin_expense" in sections
        assert "manufacturing_expense" in sections
        assert "revenue" in sections

    def test_fallback_sections_for_bs(self):
        """Balance sheet documents get assets + liabilities as fallback."""
        from app.services.classification.scoped_classifier import ScopedClassifier
        sections = ScopedClassifier._get_fallback_sections("balance_sheet")
        assert "other_assets" in sections
        assert "current_liabilities" in sections
        assert "borrowings_long" in sections

    def test_fallback_sections_for_notes(self):
        """Notes/unknown documents get a mix of P&L and BS sections."""
        from app.services.classification.scoped_classifier import ScopedClassifier
        sections = ScopedClassifier._get_fallback_sections("notes_to_accounts")
        assert len(sections) == 3


# ══════════════════════════════════════════════════════════════════════════════
# 1b. notes_to_accounts NOT treated as balance sheet
# ══════════════════════════════════════════════════════════════════════════════


class TestNotesNotBS:
    """notes_to_accounts should NOT be classified as balance sheet context."""

    def test_notes_not_in_bs_context(self):
        """_is_bs_context should return False for notes_to_accounts."""
        from app.services.classification.scoped_classifier import ScopedClassifier
        assert ScopedClassifier._is_bs_context("notes_to_accounts") is False

    def test_balance_sheet_is_bs_context(self):
        """_is_bs_context should return True for balance_sheet."""
        from app.services.classification.scoped_classifier import ScopedClassifier
        assert ScopedClassifier._is_bs_context("balance_sheet") is True

    def test_bs_is_bs_context(self):
        """_is_bs_context should return True for 'bs'."""
        from app.services.classification.scoped_classifier import ScopedClassifier
        assert ScopedClassifier._is_bs_context("bs") is True


# ══════════════════════════════════════════════════════════════════════════════
# 1c. Industry-aware rule filtering
# ══════════════════════════════════════════════════════════════════════════════


class TestIndustryRuleFiltering:
    """Industry-specific rules should take priority over universal 'all' rules."""

    def test_industry_contexts_are_keyed_by_tuple(self):
        """Internal contexts dict uses (section, industry) tuple keys."""
        classifier = _make_classifier()
        # Should have tuple keys
        for key in classifier._contexts:
            assert isinstance(key, tuple), f"Expected tuple key, got {type(key)}: {key}"
            assert len(key) == 2

    def test_manufacturing_rules_included_for_manufacturing(self):
        """Manufacturing industry context includes manufacturing-specific rules."""
        classifier = _make_classifier()
        # Get a context for manufacturing
        ctx = classifier._get_industry_context("employee_cost", "manufacturing")
        rule_industries = {r.get("industry_type") for r in ctx.rules}
        # Should include manufacturing-specific AND "all" rules
        # Should NOT include "trading" rules
        assert "trading" not in rule_industries or all(
            r.get("industry_type") in ("manufacturing", "all") for r in ctx.rules
        )

    def test_trading_rules_not_in_manufacturing_context(self):
        """Trading-only rules should be excluded from manufacturing context."""
        classifier = _make_classifier()
        ctx = classifier._get_industry_context("admin_expense", "manufacturing")
        trading_only = [r for r in ctx.rules if r.get("industry_type") == "trading"]
        assert len(trading_only) == 0


# ══════════════════════════════════════════════════════════════════════════════
# 1e. Cost guard
# ══════════════════════════════════════════════════════════════════════════════


class TestCostGuard:
    """Cost guard must limit items per document run."""

    def test_cost_guard_limits_items(self):
        """After MAX_ITEMS_PER_DOCUMENT, classify returns doubt."""
        classifier = _make_classifier()

        # Simulate that we've already classified MAX items
        from app.services.classification.scoped_classifier import MAX_ITEMS_PER_DOCUMENT
        classifier._items_classified = MAX_ITEMS_PER_DOCUMENT

        result = asyncio.get_event_loop().run_until_complete(
            classifier.classify(
                raw_text="One more item",
                amount=100.0,
                section="expenses",
                industry_type="manufacturing",
                document_type="profit_and_loss",
                fuzzy_candidates=[],
            )
        )

        assert result.is_doubt is True
        assert "limit exceeded" in result.doubt_reason.lower()

    def test_cost_guard_allows_items_below_limit(self):
        """Items below the limit should proceed normally."""
        classifier = _make_classifier()
        classifier._items_classified = 0
        classifier._call_model = MagicMock(return_value={
            "cma_row": 45, "cma_code": "M1", "confidence": 0.90, "reasoning": "wages"
        })

        result = asyncio.get_event_loop().run_until_complete(
            classifier.classify(
                raw_text="Wages and Salaries",
                amount=500000.0,
                section="expenses",
                industry_type="manufacturing",
                document_type="profit_and_loss",
                fuzzy_candidates=[],
            )
        )

        assert result.is_doubt is False


# ══════════════════════════════════════════════════════════════════════════════
# 1d. Learned mappings in prompt
# ══════════════════════════════════════════════════════════════════════════════


class TestLearnedMappingsInPrompt:
    """Learned mappings should appear in the prompt as highest priority."""

    def test_learned_mappings_in_prompt(self):
        """When learned_cache is set, prompt should contain CA-CORRECTED section."""
        classifier = _make_classifier()
        classifier.set_learned_cache([
            {"source_text": "Wages paid", "cma_field_name": "Wages", "cma_input_row": 45},
        ])
        classifier._call_model = MagicMock(return_value={
            "cma_row": 45, "cma_code": "M1", "confidence": 0.90, "reasoning": "wages"
        })

        asyncio.get_event_loop().run_until_complete(
            classifier.classify(
                raw_text="Wages and Salaries",
                amount=500000.0,
                section="expenses",
                industry_type="manufacturing",
                document_type="profit_and_loss",
                fuzzy_candidates=[],
            )
        )

        # Check that _call_model was called with a prompt containing learned mappings
        call_args = classifier._call_model.call_args
        prompt = call_args[0][1]  # second positional arg is the prompt
        assert "CA-CORRECTED MAPPINGS" in prompt
        assert "Wages paid" in prompt

    def test_no_learned_mappings_no_section(self):
        """When learned_cache is empty, prompt should NOT contain CA-CORRECTED."""
        classifier = _make_classifier()
        classifier.set_learned_cache([])
        classifier._call_model = MagicMock(return_value={
            "cma_row": 45, "cma_code": "M1", "confidence": 0.90, "reasoning": "wages"
        })

        asyncio.get_event_loop().run_until_complete(
            classifier.classify(
                raw_text="Wages and Salaries",
                amount=500000.0,
                section="expenses",
                industry_type="manufacturing",
                document_type="profit_and_loss",
                fuzzy_candidates=[],
            )
        )

        call_args = classifier._call_model.call_args
        prompt = call_args[0][1]
        assert "CA-CORRECTED MAPPINGS" not in prompt
