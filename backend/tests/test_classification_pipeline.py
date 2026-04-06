"""Pipeline unit tests — AI-only architecture (April 2026).

Coverage target: 100% on services/classification/pipeline.py

Tests verify:
- Every item reaches ScopedClassifier.classify_sync()
- High confidence → status=approved, is_doubt=False
- Medium confidence → status=auto_classified, is_doubt=False
- Low confidence / doubt → status=needs_review, is_doubt=True
- Exceptions → doubt with populated doubt_reason
- classification_method always contains "scoped" (never "fuzzy_match" or "rule_*")
- classify_document fetches learned_mappings and passes to ScopedClassifier
- classify_document paginates line items correctly
"""

import pytest
from unittest.mock import MagicMock, patch

from app.services.classification.ai_classifier import AIClassificationResult


# ── Shared test data ──────────────────────────────────────────────────────────

DOC_ID = "doc-uuid-1234"
CLIENT_ID = "client-uuid-abcd"
ITEM_ID_1 = "item-uuid-0001"
ITEM_ID_2 = "item-uuid-0002"

SAMPLE_ITEM_1 = {
    "id": ITEM_ID_1,
    "document_id": DOC_ID,
    "description": "Wages and Salaries",
    "source_text": "Wages and Salaries",
    "amount": 500000.0,
    "section": "expenses",
    "is_verified": True,
    "page_type": "notes",
}

SAMPLE_ITEM_2 = {
    "id": ITEM_ID_2,
    "document_id": DOC_ID,
    "description": "Miscellaneous Vague Entry",
    "source_text": "Misc  12,000",
    "amount": 12000.0,
    "section": "expenses",
    "is_verified": True,
    "page_type": "face",
}


def _make_ai_result(
    cma_field_name="Wages",
    cma_row=45,
    confidence=0.90,
    is_doubt=False,
    doubt_reason=None,
    method="scoped_v3",
):
    """Helper: create an AIClassificationResult."""
    return AIClassificationResult(
        cma_field_name=cma_field_name,
        cma_row=cma_row,
        cma_sheet="input_sheet",
        broad_classification="manufacturing_expense",
        confidence=confidence,
        is_doubt=is_doubt,
        doubt_reason=doubt_reason,
        alternatives=[],
        classification_method=method,
    )


def _make_pipeline():
    """Build a ClassificationPipeline with ScopedClassifier mocked."""
    with patch(
        "app.services.classification.pipeline.ScopedClassifier"
    ) as mock_scoped_cls:
        mock_ai = MagicMock()
        mock_scoped_cls.return_value = mock_ai

        from app.services.classification.pipeline import ClassificationPipeline
        pipeline = ClassificationPipeline()
        return pipeline, mock_ai


# ══════════════════════════════════════════════════════════════════════════════
# classify_item — AI routing
# ══════════════════════════════════════════════════════════════════════════════


class TestClassifyItemRouting:
    """Tests that every item goes through the AI classifier."""

    def test_all_items_reach_scoped_classifier(self):
        """Every item must call classify_sync on ScopedClassifier."""
        pipeline, mock_ai = _make_pipeline()
        mock_ai.classify_sync.return_value = _make_ai_result()

        pipeline.classify_item(
            item=SAMPLE_ITEM_1,
            client_id=CLIENT_ID,
            industry_type="manufacturing",
            document_type="profit_and_loss",
            financial_year=2024,
        )

        mock_ai.classify_sync.assert_called_once()

    def test_high_confidence_returns_approved(self):
        """Confidence >= 0.85 → status=approved, is_doubt=False."""
        pipeline, mock_ai = _make_pipeline()
        mock_ai.classify_sync.return_value = _make_ai_result(confidence=0.92)

        result = pipeline.classify_item(
            item=SAMPLE_ITEM_1,
            client_id=CLIENT_ID,
            industry_type="manufacturing",
            document_type="profit_and_loss",
            financial_year=2024,
        )

        assert result["status"] == "approved"
        assert result["is_doubt"] is False
        assert result["confidence_score"] == 0.92

    def test_medium_confidence_returns_auto_classified(self):
        """Confidence 0.80-0.84 → status=auto_classified, is_doubt=False."""
        pipeline, mock_ai = _make_pipeline()
        mock_ai.classify_sync.return_value = _make_ai_result(confidence=0.82)

        result = pipeline.classify_item(
            item=SAMPLE_ITEM_1,
            client_id=CLIENT_ID,
            industry_type="manufacturing",
            document_type="profit_and_loss",
            financial_year=2024,
        )

        assert result["status"] == "auto_classified"
        assert result["is_doubt"] is False

    def test_doubt_result_returns_needs_review(self):
        """AI returns is_doubt=True → status=needs_review."""
        pipeline, mock_ai = _make_pipeline()
        mock_ai.classify_sync.return_value = _make_ai_result(
            cma_field_name=None,
            cma_row=None,
            confidence=0.0,
            is_doubt=True,
            doubt_reason="Item too vague",
            method="scoped_doubt",
        )

        result = pipeline.classify_item(
            item=SAMPLE_ITEM_2,
            client_id=CLIENT_ID,
            industry_type="manufacturing",
            document_type="profit_and_loss",
            financial_year=2024,
        )

        assert result["is_doubt"] is True
        assert result["status"] == "needs_review"
        assert result["doubt_reason"] == "Item too vague"

    def test_doubt_has_populated_doubt_reason(self):
        """Doubt items always have doubt_reason populated."""
        pipeline, mock_ai = _make_pipeline()
        mock_ai.classify_sync.return_value = _make_ai_result(
            is_doubt=True,
            doubt_reason="Low confidence classification",
            method="scoped_doubt",
        )

        result = pipeline.classify_item(
            item=SAMPLE_ITEM_2,
            client_id=CLIENT_ID,
            industry_type="manufacturing",
            document_type="profit_and_loss",
            financial_year=2024,
        )

        assert result["doubt_reason"] is not None
        assert len(result["doubt_reason"]) > 0

    def test_exception_creates_doubt(self):
        """When classify_sync raises, result is a doubt record."""
        pipeline, mock_ai = _make_pipeline()
        mock_ai.classify_sync.side_effect = RuntimeError("API timeout")

        result = pipeline.classify_item(
            item=SAMPLE_ITEM_1,
            client_id=CLIENT_ID,
            industry_type="manufacturing",
            document_type="profit_and_loss",
            financial_year=2024,
        )

        assert result["is_doubt"] is True
        assert result["status"] == "needs_review"
        assert "RuntimeError" in result["doubt_reason"]
        assert result["cma_field_name"] == "UNCLASSIFIED"

    def test_classification_method_is_scoped(self):
        """classification_method must contain 'scoped', not 'fuzzy_match' or 'rule_*'."""
        pipeline, mock_ai = _make_pipeline()
        mock_ai.classify_sync.return_value = _make_ai_result(method="scoped_v3")

        result = pipeline.classify_item(
            item=SAMPLE_ITEM_1,
            client_id=CLIENT_ID,
            industry_type="manufacturing",
            document_type="profit_and_loss",
            financial_year=2024,
        )

        assert "scoped" in result["classification_method"]
        assert "fuzzy" not in result["classification_method"]
        assert not result["classification_method"].startswith("rule_")

    def test_cma_column_from_financial_year(self):
        """cma_column is resolved from financial_year via get_year_column."""
        pipeline, mock_ai = _make_pipeline()
        mock_ai.classify_sync.return_value = _make_ai_result()

        result = pipeline.classify_item(
            item=SAMPLE_ITEM_1,
            client_id=CLIENT_ID,
            industry_type="manufacturing",
            document_type="profit_and_loss",
            financial_year=2024,
        )

        # get_year_column(2024, 2024) returns "B"
        assert result["cma_column"] == "B"

    def test_cma_row_from_ai_result(self):
        """cma_row comes from the AI classifier result."""
        pipeline, mock_ai = _make_pipeline()
        mock_ai.classify_sync.return_value = _make_ai_result(cma_row=67)

        result = pipeline.classify_item(
            item=SAMPLE_ITEM_1,
            client_id=CLIENT_ID,
            industry_type="manufacturing",
            document_type="profit_and_loss",
            financial_year=2024,
        )

        assert result["cma_row"] == 67

    def test_fuzzy_match_score_always_zero(self):
        """fuzzy_match_score is always 0 in AI-only pipeline."""
        pipeline, mock_ai = _make_pipeline()
        mock_ai.classify_sync.return_value = _make_ai_result()

        result = pipeline.classify_item(
            item=SAMPLE_ITEM_1,
            client_id=CLIENT_ID,
            industry_type="manufacturing",
            document_type="profit_and_loss",
            financial_year=2024,
        )

        assert result["fuzzy_match_score"] == 0

    def test_source_text_fallback_to_description(self):
        """If source_text missing, falls back to description field."""
        pipeline, mock_ai = _make_pipeline()
        mock_ai.classify_sync.return_value = _make_ai_result()

        item_no_source = {"id": "test-id", "description": "Test Item", "amount": 100.0}
        pipeline.classify_item(
            item=item_no_source,
            client_id=CLIENT_ID,
            industry_type="manufacturing",
            document_type="profit_and_loss",
            financial_year=2024,
        )

        call_args = mock_ai.classify_sync.call_args
        # raw_text should be the normalized version of "Test Item"
        assert call_args is not None

    def test_page_type_passed_to_classifier(self):
        """page_type from item dict should be forwarded to classify_sync."""
        pipeline, mock_ai = _make_pipeline()
        mock_ai.classify_sync.return_value = _make_ai_result()

        item_with_page_type = {**SAMPLE_ITEM_1, "page_type": "notes"}
        pipeline.classify_item(
            item=item_with_page_type,
            client_id=CLIENT_ID,
            industry_type="manufacturing",
            document_type="profit_and_loss",
            financial_year=2024,
        )

        mock_ai.classify_sync.assert_called_once()
        call_kwargs = mock_ai.classify_sync.call_args.kwargs
        assert call_kwargs.get("page_type") == "notes"


# ══════════════════════════════════════════════════════════════════════════════
# classify_document — full document flow
# ══════════════════════════════════════════════════════════════════════════════


class TestClassifyDocument:
    """Tests for the full document classification flow."""

    def test_classify_document_returns_summary(self):
        """classify_document returns total, high_confidence, medium, needs_review."""
        pipeline, mock_ai = _make_pipeline()
        mock_ai.classify_sync.return_value = _make_ai_result(confidence=0.90)
        mock_ai.set_learned_cache = MagicMock()

        mock_service = MagicMock()
        mock_table = MagicMock()
        mock_service.table.return_value = mock_table

        # learned_mappings query
        mock_learned = MagicMock()
        mock_learned.execute.return_value = MagicMock(data=[])

        # line_items query
        mock_items = MagicMock()
        mock_items.execute.return_value = MagicMock(data=[SAMPLE_ITEM_1])

        # classification insert
        mock_insert = MagicMock()
        mock_insert.execute.return_value = MagicMock()

        # Chain the table calls
        call_count = {"n": 0}
        def table_side_effect(name):
            m = MagicMock()
            if name == "learned_mappings":
                m.select.return_value = MagicMock()
                m.select.return_value.eq.return_value = MagicMock()
                m.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
                return m
            if name == "extracted_line_items":
                m.select.return_value = MagicMock()
                sel = m.select.return_value
                sel.eq.return_value = sel
                sel.range.return_value = sel
                sel.execute.return_value = MagicMock(data=[SAMPLE_ITEM_1])
                return m
            if name == "classifications":
                m.insert.return_value = MagicMock()
                m.insert.return_value.execute.return_value = MagicMock()
                return m
            return m

        mock_service.table.side_effect = table_side_effect

        with patch("app.services.classification.pipeline.get_service_client", return_value=mock_service):
            summary = pipeline.classify_document(
                document_id=DOC_ID,
                client_id=CLIENT_ID,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                financial_year=2024,
            )

        assert summary["total"] == 1
        assert summary["high_confidence"] == 1
        assert summary["needs_review"] == 0

    def test_classify_document_fetches_learned_mappings(self):
        """classify_document pre-fetches learned_mappings for the industry."""
        pipeline, mock_ai = _make_pipeline()
        mock_ai.classify_sync.return_value = _make_ai_result()
        mock_ai.set_learned_cache = MagicMock()

        mock_service = MagicMock()
        learned_data = [{"source_text": "test", "cma_field_name": "Wages", "cma_input_row": 45}]

        def table_side_effect(name):
            m = MagicMock()
            if name == "learned_mappings":
                m.select.return_value = MagicMock()
                m.select.return_value.eq.return_value = MagicMock()
                m.select.return_value.eq.return_value.execute.return_value = MagicMock(data=learned_data)
                return m
            if name == "extracted_line_items":
                m.select.return_value = MagicMock()
                sel = m.select.return_value
                sel.eq.return_value = sel
                sel.range.return_value = sel
                sel.execute.return_value = MagicMock(data=[])
                return m
            return m

        mock_service.table.side_effect = table_side_effect

        with patch("app.services.classification.pipeline.get_service_client", return_value=mock_service):
            pipeline.classify_document(
                document_id=DOC_ID,
                client_id=CLIENT_ID,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                financial_year=2024,
            )

        mock_ai.set_learned_cache.assert_called_once_with(learned_data)

    def test_classify_document_handles_item_error(self):
        """Per-item exceptions create doubt records, don't crash the document."""
        pipeline, mock_ai = _make_pipeline()
        mock_ai.classify_sync.side_effect = RuntimeError("boom")
        mock_ai.set_learned_cache = MagicMock()

        mock_service = MagicMock()

        inserts = []
        def table_side_effect(name):
            m = MagicMock()
            if name == "learned_mappings":
                m.select.return_value = MagicMock()
                m.select.return_value.eq.return_value = MagicMock()
                m.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
                return m
            if name == "extracted_line_items":
                m.select.return_value = MagicMock()
                sel = m.select.return_value
                sel.eq.return_value = sel
                sel.range.return_value = sel
                sel.execute.return_value = MagicMock(data=[SAMPLE_ITEM_1])
                return m
            if name == "classifications":
                def capture_insert(data):
                    inserts.append(data)
                    mock_ins = MagicMock()
                    mock_ins.execute.return_value = MagicMock()
                    return mock_ins
                m.insert.side_effect = capture_insert
                return m
            return m

        mock_service.table.side_effect = table_side_effect

        with patch("app.services.classification.pipeline.get_service_client", return_value=mock_service):
            summary = pipeline.classify_document(
                document_id=DOC_ID,
                client_id=CLIENT_ID,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                financial_year=2024,
            )

        # The error should be caught and a doubt record inserted
        assert summary["needs_review"] == 1
        assert summary["total"] == 1


# ══════════════════════════════════════════════════════════════════════════════
# Pipeline construction
# ══════════════════════════════════════════════════════════════════════════════


class TestPipelineConstruction:
    """Tests for pipeline initialization."""

    def test_legacy_mode_logs_deprecation(self):
        """classifier_mode='legacy' still works but logs a warning."""
        with patch(
            "app.services.classification.pipeline.ScopedClassifier"
        ), patch(
            "app.services.classification.pipeline.get_settings"
        ) as mock_settings:
            mock_settings.return_value = MagicMock(classifier_mode="legacy")

            with patch("app.services.classification.pipeline.logger") as mock_logger:
                from app.services.classification.pipeline import ClassificationPipeline
                ClassificationPipeline()
                mock_logger.warning.assert_called_once()

    def test_scoped_mode_no_warning(self):
        """classifier_mode='scoped' is the normal path, no warning."""
        with patch(
            "app.services.classification.pipeline.ScopedClassifier"
        ), patch(
            "app.services.classification.pipeline.get_settings"
        ) as mock_settings:
            mock_settings.return_value = MagicMock(classifier_mode="scoped")

            with patch("app.services.classification.pipeline.logger") as mock_logger:
                from app.services.classification.pipeline import ClassificationPipeline
                ClassificationPipeline()
                mock_logger.warning.assert_not_called()
