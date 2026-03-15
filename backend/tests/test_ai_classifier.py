"""Phase 5B: AI Classifier unit tests.

TDD — RED phase: written BEFORE implementation.

Coverage target: 100% on services/classification/ai_classifier.py

Critical constraints tested:
- confidence < 0.8 → is_doubt=True (NEVER silent guessing)
- boundary test at exactly 0.79
- API errors → doubt result (never crash pipeline)
- Industry context included in prompt
- Fuzzy candidates included in prompt
"""

import pytest
from unittest.mock import MagicMock, patch


# ── Shared test data ────────────────────────────────────────────────────────────

from app.services.classification.fuzzy_matcher import FuzzyMatchResult

FUZZY_CANDIDATES = [
    FuzzyMatchResult(
        cma_field_name="Wages",
        cma_row=45,
        cma_sheet="input_sheet",
        broad_classification="manufacturing_expense",
        score=72.0,
        source="reference",
    ),
    FuzzyMatchResult(
        cma_field_name="Salary and staff expenses",
        cma_row=67,
        cma_sheet="input_sheet",
        broad_classification="admin_expense",
        score=55.0,
        source="reference",
    ),
]

# Mock tool_use response from Anthropic API (high confidence)
HIGH_CONF_TOOL_INPUT = {
    "best_match": {
        "cma_field_name": "Wages",
        "cma_row": 45,
        "cma_sheet": "input_sheet",
        "broad_classification": "manufacturing_expense",
        "confidence": 0.92,
        "reasoning": "Clear match: wages/salaries for manufacturing operations",
    },
    "alternatives": [
        {
            "cma_field_name": "Salary and staff expenses",
            "cma_row": 67,
            "cma_sheet": "input_sheet",
            "broad_classification": "admin_expense",
            "confidence": 0.45,
            "reasoning": "Alternative if service industry",
        }
    ],
    "is_uncertain": False,
    "uncertainty_reason": None,
}

# Mock tool_use response (low confidence — doubt)
LOW_CONF_TOOL_INPUT = {
    "best_match": {
        "cma_field_name": "Others (Admin)",
        "cma_row": 71,
        "cma_sheet": "input_sheet",
        "broad_classification": "admin_expense",
        "confidence": 0.55,
        "reasoning": "Unclear item — could be multiple categories",
    },
    "alternatives": [],
    "is_uncertain": True,
    "uncertainty_reason": "Item description is too vague to classify with confidence",
}

# Boundary case: exactly 0.79 must be doubt
BOUNDARY_TOOL_INPUT = {
    "best_match": {
        "cma_field_name": "Others (Admin)",
        "cma_row": 71,
        "cma_sheet": "input_sheet",
        "broad_classification": "admin_expense",
        "confidence": 0.79,
        "reasoning": "Just below threshold",
    },
    "alternatives": [],
    "is_uncertain": True,
    "uncertainty_reason": "Confidence below threshold",
}


def _make_mock_anthropic_response(tool_input: dict):
    """Build a mock Anthropic API response with tool_use content."""
    mock_tool_block = MagicMock()
    mock_tool_block.type = "tool_use"
    mock_tool_block.input = tool_input

    mock_response = MagicMock()
    mock_response.content = [mock_tool_block]
    return mock_response


# ══════════════════════════════════════════════════════════════════════════════
# AIClassificationResult dataclass
# ══════════════════════════════════════════════════════════════════════════════


class TestAIClassificationResult:
    def test_ai_classification_result_has_required_fields(self):
        """AIClassificationResult dataclass has all expected fields."""
        from app.services.classification.ai_classifier import AIClassificationResult

        result = AIClassificationResult(
            cma_field_name="Wages",
            cma_row=45,
            cma_sheet="input_sheet",
            broad_classification="manufacturing_expense",
            confidence=0.92,
            is_doubt=False,
            doubt_reason=None,
            alternatives=[],
            classification_method="ai_haiku",
        )
        assert result.cma_field_name == "Wages"
        assert result.is_doubt is False
        assert result.confidence == 0.92


# ══════════════════════════════════════════════════════════════════════════════
# AIClassifier.classify() — happy paths
# ══════════════════════════════════════════════════════════════════════════════


class TestAIClassifierHappyPath:
    """Tests for AIClassifier.classify() in the successful case."""

    def test_classify_returns_structured_result(self):
        """classify() returns an AIClassificationResult for a clear match."""
        from app.services.classification.ai_classifier import AIClassifier

        mock_response = _make_mock_anthropic_response(HIGH_CONF_TOOL_INPUT)

        with patch("app.services.classification.ai_classifier.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            classifier = AIClassifier()
            result = classifier.classify(
                raw_text="Staff Wages and Salaries",
                amount=500000.0,
                section="expenses",
                industry_type="manufacturing",
                document_type="profit_and_loss",
                fuzzy_candidates=FUZZY_CANDIDATES,
            )

        assert result.cma_field_name == "Wages"
        assert result.cma_row == 45
        assert result.is_doubt is False
        assert result.classification_method == "ai_haiku"

    def test_classify_high_confidence_not_doubt(self):
        """confidence >= 0.8 → is_doubt=False."""
        from app.services.classification.ai_classifier import AIClassifier

        mock_response = _make_mock_anthropic_response(HIGH_CONF_TOOL_INPUT)

        with patch("app.services.classification.ai_classifier.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            classifier = AIClassifier()
            result = classifier.classify(
                raw_text="Wages",
                amount=None,
                section=None,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                fuzzy_candidates=[],
            )

        assert result.confidence >= 0.8
        assert result.is_doubt is False

    def test_classify_returns_alternatives(self):
        """classify() populates alternatives list from AI response."""
        from app.services.classification.ai_classifier import AIClassifier

        mock_response = _make_mock_anthropic_response(HIGH_CONF_TOOL_INPUT)

        with patch("app.services.classification.ai_classifier.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            classifier = AIClassifier()
            result = classifier.classify(
                raw_text="Wages",
                amount=None,
                section=None,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                fuzzy_candidates=[],
            )

        assert isinstance(result.alternatives, list)

    def test_classify_uses_haiku_model(self):
        """AI classifier calls messages.create with the Haiku model."""
        from app.services.classification.ai_classifier import AIClassifier, HAIKU_MODEL

        mock_response = _make_mock_anthropic_response(HIGH_CONF_TOOL_INPUT)

        with patch("app.services.classification.ai_classifier.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            classifier = AIClassifier()
            classifier.classify(
                raw_text="Wages",
                amount=None,
                section=None,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                fuzzy_candidates=[],
            )

        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs is not None
        model_used = call_kwargs.kwargs.get("model") or call_kwargs.args[0] if call_kwargs.args else None
        # Check model in kwargs or positional args
        create_kwargs = call_kwargs.kwargs if call_kwargs.kwargs else {}
        assert create_kwargs.get("model") == HAIKU_MODEL


# ══════════════════════════════════════════════════════════════════════════════
# Doubt flagging (critical constraint — NEVER silent guessing)
# ══════════════════════════════════════════════════════════════════════════════


class TestAIClassifierDoubt:
    """Verify the doubt constraint: confidence < 0.8 → always flagged."""

    def test_classify_low_confidence_flags_doubt(self):
        """confidence < 0.8 → is_doubt=True."""
        from app.services.classification.ai_classifier import AIClassifier

        mock_response = _make_mock_anthropic_response(LOW_CONF_TOOL_INPUT)

        with patch("app.services.classification.ai_classifier.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            classifier = AIClassifier()
            result = classifier.classify(
                raw_text="Miscellaneous Vague Entry",
                amount=None,
                section=None,
                industry_type="service",
                document_type="profit_and_loss",
                fuzzy_candidates=[],
            )

        assert result.is_doubt is True
        assert result.doubt_reason is not None
        assert len(result.doubt_reason) > 0

    def test_classify_boundary_079_is_doubt(self):
        """Confidence exactly 0.79 MUST be a doubt (boundary condition)."""
        from app.services.classification.ai_classifier import AIClassifier

        mock_response = _make_mock_anthropic_response(BOUNDARY_TOOL_INPUT)

        with patch("app.services.classification.ai_classifier.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            classifier = AIClassifier()
            result = classifier.classify(
                raw_text="Some entry",
                amount=None,
                section=None,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                fuzzy_candidates=[],
            )

        assert result.is_doubt is True, "Confidence 0.79 must be flagged as doubt"

    def test_classify_doubt_preserves_ai_best_guess(self):
        """Even when doubt, the AI's best guess field name is preserved."""
        from app.services.classification.ai_classifier import AIClassifier

        mock_response = _make_mock_anthropic_response(LOW_CONF_TOOL_INPUT)

        with patch("app.services.classification.ai_classifier.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            classifier = AIClassifier()
            result = classifier.classify(
                raw_text="Unclear Entry",
                amount=None,
                section=None,
                industry_type="service",
                document_type="profit_and_loss",
                fuzzy_candidates=[],
            )

        # AI's best guess is preserved even in doubt state
        assert result.cma_field_name is not None


# ══════════════════════════════════════════════════════════════════════════════
# Prompt content verification
# ══════════════════════════════════════════════════════════════════════════════


class TestAIClassifierPrompt:
    """Verify that industry context and fuzzy candidates appear in the prompt."""

    def test_classify_includes_industry_context_in_prompt(self):
        """Industry type appears in the messages sent to the API."""
        from app.services.classification.ai_classifier import AIClassifier

        mock_response = _make_mock_anthropic_response(HIGH_CONF_TOOL_INPUT)
        captured_messages = []

        def capture_create(**kwargs):
            captured_messages.extend(kwargs.get("messages", []))
            return mock_response

        with patch("app.services.classification.ai_classifier.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.side_effect = capture_create

            classifier = AIClassifier()
            classifier.classify(
                raw_text="Wages",
                amount=None,
                section=None,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                fuzzy_candidates=[],
            )

        full_prompt = str(captured_messages)
        assert "manufacturing" in full_prompt.lower()

    def test_classify_includes_fuzzy_candidates_in_prompt(self):
        """Top fuzzy match candidates appear in the messages sent to the API."""
        from app.services.classification.ai_classifier import AIClassifier

        mock_response = _make_mock_anthropic_response(HIGH_CONF_TOOL_INPUT)
        captured_messages = []

        def capture_create(**kwargs):
            captured_messages.extend(kwargs.get("messages", []))
            return mock_response

        with patch("app.services.classification.ai_classifier.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.side_effect = capture_create

            classifier = AIClassifier()
            classifier.classify(
                raw_text="Staff Wages",
                amount=500000.0,
                section="expenses",
                industry_type="manufacturing",
                document_type="profit_and_loss",
                fuzzy_candidates=FUZZY_CANDIDATES,
            )

        full_prompt = str(captured_messages)
        # The fuzzy candidate field name should appear in the prompt
        assert "Wages" in full_prompt


# ══════════════════════════════════════════════════════════════════════════════
# Error handling — never crash the pipeline
# ══════════════════════════════════════════════════════════════════════════════


class TestAIClassifierErrorHandling:
    """API errors must return a doubt result, never crash."""

    def test_classify_handles_api_error_gracefully(self):
        """Anthropic API error → returns doubt result instead of raising."""
        from app.services.classification.ai_classifier import AIClassifier
        import anthropic

        with patch("app.services.classification.ai_classifier.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.side_effect = Exception("API connection error")

            classifier = AIClassifier()
            result = classifier.classify(
                raw_text="Wages",
                amount=None,
                section=None,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                fuzzy_candidates=[],
            )

        # Must not raise — must return a doubt result
        assert result.is_doubt is True
        assert result.doubt_reason is not None
        assert "unavailable" in result.doubt_reason.lower() or "error" in result.doubt_reason.lower()

    def test_classify_handles_malformed_response_gracefully(self):
        """If AI response has no tool_use block, returns doubt result."""
        from app.services.classification.ai_classifier import AIClassifier

        # Response with no tool_use content
        mock_response = MagicMock()
        mock_response.content = []  # empty content

        with patch("app.services.classification.ai_classifier.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            classifier = AIClassifier()
            result = classifier.classify(
                raw_text="Wages",
                amount=None,
                section=None,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                fuzzy_candidates=[],
            )

        assert result.is_doubt is True

    def test_classify_api_key_not_in_log_messages(self):
        """API key does not appear in log output (security guard)."""
        from app.services.classification.ai_classifier import AIClassifier
        import logging

        mock_response = _make_mock_anthropic_response(HIGH_CONF_TOOL_INPUT)
        log_messages = []

        class CapturingHandler(logging.Handler):
            def emit(self, record):
                log_messages.append(self.format(record))

        handler = CapturingHandler()
        logging.getLogger("app.services.classification.ai_classifier").addHandler(handler)

        with patch("app.services.classification.ai_classifier.Anthropic") as mock_cls, \
             patch("app.services.classification.ai_classifier.get_settings") as mock_settings:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            mock_settings.return_value.anthropic_api_key = "sk-secret-key-12345"

            classifier = AIClassifier()
            classifier.classify(
                raw_text="Wages",
                amount=None,
                section=None,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                fuzzy_candidates=[],
            )

        logging.getLogger("app.services.classification.ai_classifier").removeHandler(handler)

        for msg in log_messages:
            assert "sk-secret-key-12345" not in msg, "API key must not appear in logs"
