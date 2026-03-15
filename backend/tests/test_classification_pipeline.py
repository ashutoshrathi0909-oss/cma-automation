"""Phase 5C: Pipeline + Worker unit tests.

TDD — RED phase: written BEFORE implementation.

Coverage target: 100% on services/classification/pipeline.py
                           workers/classification_tasks.py

Tests verify:
- Tier 1 (fuzzy >= 85): no AI call, status=auto_classified
- Tier 2 (AI >= 0.8): auto_classified, method=ai_haiku
- Tier 3 (AI < 0.8 or error): needs_review, is_doubt=True
- Pipeline resolves correct cma_row and cma_column from financial_year
- No item is left in 'pending' state after pipeline runs
- Worker guard: rejects non-verified documents
- Worker idempotency: deletes existing classifications first
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone


# ── Shared test data ──────────────────────────────────────────────────────────

DOC_ID = "doc-uuid-1234"
CLIENT_ID = "client-uuid-abcd"
ITEM_ID_1 = "item-uuid-0001"
ITEM_ID_2 = "item-uuid-0002"

SAMPLE_DOCUMENT_VERIFIED = {
    "id": DOC_ID,
    "client_id": CLIENT_ID,
    "file_name": "financials.xlsx",
    "file_path": f"{CLIENT_ID}/test-file.xlsx",
    "file_type": "xlsx",
    "document_type": "profit_and_loss",
    "financial_year": 2024,
    "nature": "audited",
    "extraction_status": "verified",
    "uploaded_by": "admin-uuid-0001",
    "uploaded_at": "2025-01-01T00:00:00+00:00",
}

SAMPLE_DOCUMENT_NOT_VERIFIED = {
    **SAMPLE_DOCUMENT_VERIFIED,
    "extraction_status": "extracted",
}

SAMPLE_CLIENT = {
    "id": CLIENT_ID,
    "name": "Test Company Ltd",
    "industry_type": "manufacturing",
}

SAMPLE_ITEM_1 = {
    "id": ITEM_ID_1,
    "document_id": DOC_ID,
    "description": "Wages and Salaries",
    "amount": 500000.0,
    "section": "expenses",
    "raw_text": "Wages and Salaries  5,00,000",
    "is_verified": True,
}

SAMPLE_ITEM_2 = {
    "id": ITEM_ID_2,
    "document_id": DOC_ID,
    "description": "Miscellaneous Vague Entry",
    "amount": 12000.0,
    "section": "expenses",
    "raw_text": "Misc  12,000",
    "is_verified": True,
}


def _make_service():
    return MagicMock()


# ══════════════════════════════════════════════════════════════════════════════
# Pipeline.classify_item() — Tier routing
# ══════════════════════════════════════════════════════════════════════════════


class TestPipelineTierRouting:
    """Tests for the 3-tier classification routing in classify_item()."""

    def test_tier1_fuzzy_match_skips_ai(self):
        """When fuzzy score >= 85, AI classifier is NOT called."""
        from app.services.classification.pipeline import ClassificationPipeline
        from app.services.classification.fuzzy_matcher import FuzzyMatchResult

        high_score_result = FuzzyMatchResult(
            cma_field_name="Wages",
            cma_row=45,
            cma_sheet="input_sheet",
            broad_classification="manufacturing_expense",
            score=92.0,
            source="reference",
        )

        with patch(
            "app.services.classification.pipeline.FuzzyMatcher"
        ) as mock_fuzzy_cls, patch(
            "app.services.classification.pipeline.AIClassifier"
        ) as mock_ai_cls:
            mock_fuzzy = MagicMock()
            mock_fuzzy.match.return_value = [high_score_result]
            mock_fuzzy_cls.return_value = mock_fuzzy

            mock_ai = MagicMock()
            mock_ai_cls.return_value = mock_ai

            pipeline = ClassificationPipeline()
            result = pipeline.classify_item(
                item=SAMPLE_ITEM_1,
                client_id=CLIENT_ID,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                financial_year=2024,
            )

        # AI should NOT be called when fuzzy score >= 85
        mock_ai.classify.assert_not_called()
        assert result["status"] == "auto_classified"
        assert result["is_doubt"] is False

    def test_tier1_miss_triggers_tier2_ai(self):
        """When fuzzy score < 85, AI classifier IS called."""
        from app.services.classification.pipeline import ClassificationPipeline
        from app.services.classification.fuzzy_matcher import FuzzyMatchResult
        from app.services.classification.ai_classifier import AIClassificationResult

        low_score_result = FuzzyMatchResult(
            cma_field_name="Wages",
            cma_row=45,
            cma_sheet="input_sheet",
            broad_classification="manufacturing_expense",
            score=60.0,
            source="reference",
        )

        ai_result = AIClassificationResult(
            cma_field_name="Wages",
            cma_row=45,
            cma_sheet="input_sheet",
            broad_classification="manufacturing_expense",
            confidence=0.87,
            is_doubt=False,
            doubt_reason=None,
            alternatives=[],
            classification_method="ai_haiku",
        )

        with patch(
            "app.services.classification.pipeline.FuzzyMatcher"
        ) as mock_fuzzy_cls, patch(
            "app.services.classification.pipeline.AIClassifier"
        ) as mock_ai_cls:
            mock_fuzzy = MagicMock()
            mock_fuzzy.match.return_value = [low_score_result]
            mock_fuzzy_cls.return_value = mock_fuzzy

            mock_ai = MagicMock()
            mock_ai.classify.return_value = ai_result
            mock_ai_cls.return_value = mock_ai

            pipeline = ClassificationPipeline()
            result = pipeline.classify_item(
                item=SAMPLE_ITEM_1,
                client_id=CLIENT_ID,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                financial_year=2024,
            )

        mock_ai.classify.assert_called_once()
        assert result["status"] == "auto_classified"

    def test_tier2_high_confidence_classifies(self):
        """AI confidence >= 0.8 → status=auto_classified, is_doubt=False."""
        from app.services.classification.pipeline import ClassificationPipeline
        from app.services.classification.fuzzy_matcher import FuzzyMatchResult
        from app.services.classification.ai_classifier import AIClassificationResult

        low_fuzzy = FuzzyMatchResult(
            cma_field_name="Wages",
            cma_row=45,
            cma_sheet="input_sheet",
            broad_classification="",
            score=50.0,
            source="reference",
        )
        ai_result = AIClassificationResult(
            cma_field_name="Salary and staff expenses",
            cma_row=67,
            cma_sheet="input_sheet",
            broad_classification="admin_expense",
            confidence=0.85,
            is_doubt=False,
            doubt_reason=None,
            alternatives=[],
            classification_method="ai_haiku",
        )

        with patch(
            "app.services.classification.pipeline.FuzzyMatcher"
        ) as mock_fuzzy_cls, patch(
            "app.services.classification.pipeline.AIClassifier"
        ) as mock_ai_cls:
            mock_fuzzy = MagicMock()
            mock_fuzzy.match.return_value = [low_fuzzy]
            mock_fuzzy_cls.return_value = mock_fuzzy

            mock_ai = MagicMock()
            mock_ai.classify.return_value = ai_result
            mock_ai_cls.return_value = mock_ai

            pipeline = ClassificationPipeline()
            result = pipeline.classify_item(
                item=SAMPLE_ITEM_1,
                client_id=CLIENT_ID,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                financial_year=2024,
            )

        assert result["is_doubt"] is False
        assert result["status"] == "auto_classified"
        assert result["classification_method"] == "ai_haiku"

    def test_tier2_low_confidence_creates_doubt(self):
        """AI confidence < 0.8 → status=needs_review, is_doubt=True."""
        from app.services.classification.pipeline import ClassificationPipeline
        from app.services.classification.fuzzy_matcher import FuzzyMatchResult
        from app.services.classification.ai_classifier import AIClassificationResult

        low_fuzzy = FuzzyMatchResult(
            cma_field_name="Others (Admin)",
            cma_row=71,
            cma_sheet="input_sheet",
            broad_classification="",
            score=40.0,
            source="reference",
        )
        ai_doubt = AIClassificationResult(
            cma_field_name="Others (Admin)",
            cma_row=71,
            cma_sheet="input_sheet",
            broad_classification="admin_expense",
            confidence=0.55,
            is_doubt=True,
            doubt_reason="Item too vague to classify confidently",
            alternatives=[],
            classification_method="ai_haiku",
        )

        with patch(
            "app.services.classification.pipeline.FuzzyMatcher"
        ) as mock_fuzzy_cls, patch(
            "app.services.classification.pipeline.AIClassifier"
        ) as mock_ai_cls:
            mock_fuzzy = MagicMock()
            mock_fuzzy.match.return_value = [low_fuzzy]
            mock_fuzzy_cls.return_value = mock_fuzzy

            mock_ai = MagicMock()
            mock_ai.classify.return_value = ai_doubt
            mock_ai_cls.return_value = mock_ai

            pipeline = ClassificationPipeline()
            result = pipeline.classify_item(
                item=SAMPLE_ITEM_2,
                client_id=CLIENT_ID,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                financial_year=2024,
            )

        assert result["is_doubt"] is True
        assert result["status"] == "needs_review"
        assert result["doubt_reason"] is not None

    def test_tier3_doubt_has_populated_doubt_reason(self):
        """Doubt items ALWAYS have doubt_reason populated — never None."""
        from app.services.classification.pipeline import ClassificationPipeline
        from app.services.classification.fuzzy_matcher import FuzzyMatchResult
        from app.services.classification.ai_classifier import AIClassificationResult

        ai_doubt = AIClassificationResult(
            cma_field_name=None,
            cma_row=None,
            cma_sheet="input_sheet",
            broad_classification="",
            confidence=0.0,
            is_doubt=True,
            doubt_reason="AI classification unavailable",
            alternatives=[],
            classification_method="ai_haiku",
        )

        with patch(
            "app.services.classification.pipeline.FuzzyMatcher"
        ) as mock_fuzzy_cls, patch(
            "app.services.classification.pipeline.AIClassifier"
        ) as mock_ai_cls:
            mock_fuzzy = MagicMock()
            mock_fuzzy.match.return_value = []
            mock_fuzzy_cls.return_value = mock_fuzzy

            mock_ai = MagicMock()
            mock_ai.classify.return_value = ai_doubt
            mock_ai_cls.return_value = mock_ai

            pipeline = ClassificationPipeline()
            result = pipeline.classify_item(
                item=SAMPLE_ITEM_2,
                client_id=CLIENT_ID,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                financial_year=2024,
            )

        assert result["is_doubt"] is True
        assert result["doubt_reason"] is not None
        assert len(result["doubt_reason"]) > 0


# ══════════════════════════════════════════════════════════════════════════════
# Pipeline.classify_item() — field resolution
# ══════════════════════════════════════════════════════════════════════════════


class TestPipelineFieldResolution:
    """Tests that cma_row, cma_column, and cma_sheet are resolved correctly."""

    def _make_pipeline_with_fuzzy(self, fuzzy_result):
        """Helper: build a pipeline with a mock fuzzy result."""
        from app.services.classification.pipeline import ClassificationPipeline

        mock_fuzzy_cls = MagicMock()
        mock_fuzzy = MagicMock()
        mock_fuzzy.match.return_value = [fuzzy_result]
        mock_fuzzy_cls.return_value = mock_fuzzy

        mock_ai_cls = MagicMock()
        mock_ai_cls.return_value = MagicMock()

        return ClassificationPipeline.__new__(ClassificationPipeline), mock_fuzzy_cls, mock_ai_cls

    def test_correct_cma_row_from_fuzzy_result(self):
        """cma_row in classification comes from the fuzzy/AI match."""
        from app.services.classification.pipeline import ClassificationPipeline
        from app.services.classification.fuzzy_matcher import FuzzyMatchResult

        wages_result = FuzzyMatchResult(
            cma_field_name="Wages",
            cma_row=45,
            cma_sheet="input_sheet",
            broad_classification="manufacturing_expense",
            score=95.0,
            source="reference",
        )

        with patch(
            "app.services.classification.pipeline.FuzzyMatcher"
        ) as mock_fuzzy_cls, patch(
            "app.services.classification.pipeline.AIClassifier"
        ):
            mock_fuzzy = MagicMock()
            mock_fuzzy.match.return_value = [wages_result]
            mock_fuzzy_cls.return_value = mock_fuzzy

            pipeline = ClassificationPipeline()
            result = pipeline.classify_item(
                item=SAMPLE_ITEM_1,
                client_id=CLIENT_ID,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                financial_year=2024,
            )

        assert result["cma_row"] == 45

    def test_financial_year_2024_maps_to_column_c(self):
        """financial_year=2024 maps to cma_column='C' per YEAR_TO_COLUMN."""
        from app.services.classification.pipeline import ClassificationPipeline
        from app.services.classification.fuzzy_matcher import FuzzyMatchResult

        result_item = FuzzyMatchResult(
            cma_field_name="Wages",
            cma_row=45,
            cma_sheet="input_sheet",
            broad_classification="manufacturing_expense",
            score=92.0,
            source="reference",
        )

        with patch(
            "app.services.classification.pipeline.FuzzyMatcher"
        ) as mock_fuzzy_cls, patch(
            "app.services.classification.pipeline.AIClassifier"
        ):
            mock_fuzzy = MagicMock()
            mock_fuzzy.match.return_value = [result_item]
            mock_fuzzy_cls.return_value = mock_fuzzy

            pipeline = ClassificationPipeline()
            result = pipeline.classify_item(
                item=SAMPLE_ITEM_1,
                client_id=CLIENT_ID,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                financial_year=2024,
            )

        assert result["cma_column"] == "C"

    def test_financial_year_2023_maps_to_column_b(self):
        """financial_year=2023 maps to cma_column='B'."""
        from app.services.classification.pipeline import ClassificationPipeline
        from app.services.classification.fuzzy_matcher import FuzzyMatchResult

        result_item = FuzzyMatchResult(
            cma_field_name="Wages",
            cma_row=45,
            cma_sheet="input_sheet",
            broad_classification="manufacturing_expense",
            score=92.0,
            source="reference",
        )

        with patch(
            "app.services.classification.pipeline.FuzzyMatcher"
        ) as mock_fuzzy_cls, patch(
            "app.services.classification.pipeline.AIClassifier"
        ):
            mock_fuzzy = MagicMock()
            mock_fuzzy.match.return_value = [result_item]
            mock_fuzzy_cls.return_value = mock_fuzzy

            pipeline = ClassificationPipeline()
            result = pipeline.classify_item(
                item=SAMPLE_ITEM_1,
                client_id=CLIENT_ID,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                financial_year=2023,
            )

        assert result["cma_column"] == "B"

    def test_learned_source_sets_method_learned(self):
        """Fuzzy result from learned_mappings sets classification_method='learned'."""
        from app.services.classification.pipeline import ClassificationPipeline
        from app.services.classification.fuzzy_matcher import FuzzyMatchResult

        learned_result = FuzzyMatchResult(
            cma_field_name="Salary and staff expenses",
            cma_row=67,
            cma_sheet="input_sheet",
            broad_classification="admin_expense",
            score=96.0,
            source="learned",  # source is 'learned'
        )

        with patch(
            "app.services.classification.pipeline.FuzzyMatcher"
        ) as mock_fuzzy_cls, patch(
            "app.services.classification.pipeline.AIClassifier"
        ):
            mock_fuzzy = MagicMock()
            mock_fuzzy.match.return_value = [learned_result]
            mock_fuzzy_cls.return_value = mock_fuzzy

            pipeline = ClassificationPipeline()
            result = pipeline.classify_item(
                item=SAMPLE_ITEM_1,
                client_id=CLIENT_ID,
                industry_type="service",
                document_type="profit_and_loss",
                financial_year=2024,
            )

        assert result["classification_method"] == "learned"

    def test_reference_source_sets_method_fuzzy_match(self):
        """Fuzzy result from cma_reference_mappings sets classification_method='fuzzy_match'."""
        from app.services.classification.pipeline import ClassificationPipeline
        from app.services.classification.fuzzy_matcher import FuzzyMatchResult

        reference_result = FuzzyMatchResult(
            cma_field_name="Wages",
            cma_row=45,
            cma_sheet="input_sheet",
            broad_classification="manufacturing_expense",
            score=92.0,
            source="reference",  # source is 'reference'
        )

        with patch(
            "app.services.classification.pipeline.FuzzyMatcher"
        ) as mock_fuzzy_cls, patch(
            "app.services.classification.pipeline.AIClassifier"
        ):
            mock_fuzzy = MagicMock()
            mock_fuzzy.match.return_value = [reference_result]
            mock_fuzzy_cls.return_value = mock_fuzzy

            pipeline = ClassificationPipeline()
            result = pipeline.classify_item(
                item=SAMPLE_ITEM_1,
                client_id=CLIENT_ID,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                financial_year=2024,
            )

        assert result["classification_method"] == "fuzzy_match"


# ══════════════════════════════════════════════════════════════════════════════
# Pipeline.classify_document() — DB persistence
# ══════════════════════════════════════════════════════════════════════════════


class TestPipelineClassifyDocument:
    """Tests for classify_document() DB interaction."""

    def test_classify_document_saves_classifications_to_db(self):
        """classify_document inserts a classification row for each line item."""
        from app.services.classification.pipeline import ClassificationPipeline
        from app.services.classification.fuzzy_matcher import FuzzyMatchResult

        good_result = FuzzyMatchResult(
            cma_field_name="Wages",
            cma_row=45,
            cma_sheet="input_sheet",
            broad_classification="manufacturing_expense",
            score=92.0,
            source="reference",
        )

        mock_service = _make_service()
        # Return 2 verified line items
        mock_service.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            SAMPLE_ITEM_1,
            SAMPLE_ITEM_2,
        ]
        mock_service.table.return_value.insert.return_value.execute.return_value.data = [{}]

        with patch(
            "app.services.classification.pipeline.FuzzyMatcher"
        ) as mock_fuzzy_cls, patch(
            "app.services.classification.pipeline.AIClassifier"
        ) as mock_ai_cls, patch(
            "app.services.classification.pipeline.get_service_client",
            return_value=mock_service,
        ):
            mock_fuzzy = MagicMock()
            mock_fuzzy.match.return_value = [good_result]
            mock_fuzzy_cls.return_value = mock_fuzzy

            mock_ai = MagicMock()
            mock_ai_cls.return_value = mock_ai

            pipeline = ClassificationPipeline()
            summary = pipeline.classify_document(
                document_id=DOC_ID,
                client_id=CLIENT_ID,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                financial_year=2024,
            )

        # Verify insert was called once per line item
        insert_calls = mock_service.table.return_value.insert.call_args_list
        assert len(insert_calls) == 2

    def test_classify_document_returns_summary(self):
        """classify_document returns a dict with total, high_confidence, etc."""
        from app.services.classification.pipeline import ClassificationPipeline
        from app.services.classification.fuzzy_matcher import FuzzyMatchResult

        good_result = FuzzyMatchResult(
            cma_field_name="Wages",
            cma_row=45,
            cma_sheet="input_sheet",
            broad_classification="manufacturing_expense",
            score=92.0,
            source="reference",
        )

        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [SAMPLE_ITEM_1]
        mock_service.table.return_value.insert.return_value.execute.return_value.data = [{}]

        with patch(
            "app.services.classification.pipeline.FuzzyMatcher"
        ) as mock_fuzzy_cls, patch(
            "app.services.classification.pipeline.AIClassifier"
        ) as mock_ai_cls, patch(
            "app.services.classification.pipeline.get_service_client",
            return_value=mock_service,
        ):
            mock_fuzzy = MagicMock()
            mock_fuzzy.match.return_value = [good_result]
            mock_fuzzy_cls.return_value = mock_fuzzy

            mock_ai = MagicMock()
            mock_ai_cls.return_value = mock_ai

            pipeline = ClassificationPipeline()
            summary = pipeline.classify_document(
                document_id=DOC_ID,
                client_id=CLIENT_ID,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                financial_year=2024,
            )

        assert "total" in summary
        assert "high_confidence" in summary
        assert "medium_confidence" in summary
        assert "needs_review" in summary
        assert summary["total"] == 1

    def test_classify_document_no_item_left_pending(self):
        """After classify_document, all items are auto_classified or needs_review (not pending)."""
        from app.services.classification.pipeline import ClassificationPipeline
        from app.services.classification.fuzzy_matcher import FuzzyMatchResult
        from app.services.classification.ai_classifier import AIClassificationResult

        low_fuzzy = FuzzyMatchResult(
            cma_field_name="Others (Admin)",
            cma_row=71,
            cma_sheet="input_sheet",
            broad_classification="",
            score=40.0,
            source="reference",
        )
        ai_doubt = AIClassificationResult(
            cma_field_name="Others (Admin)",
            cma_row=71,
            cma_sheet="input_sheet",
            broad_classification="",
            confidence=0.4,
            is_doubt=True,
            doubt_reason="Too vague",
            alternatives=[],
            classification_method="ai_haiku",
        )

        inserted_rows = []
        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [SAMPLE_ITEM_2]

        def capture_insert(row):
            inserted_rows.append(row)
            inner = MagicMock()
            inner.execute.return_value.data = [row]
            return inner

        mock_service.table.return_value.insert.side_effect = capture_insert

        with patch(
            "app.services.classification.pipeline.FuzzyMatcher"
        ) as mock_fuzzy_cls, patch(
            "app.services.classification.pipeline.AIClassifier"
        ) as mock_ai_cls, patch(
            "app.services.classification.pipeline.get_service_client",
            return_value=mock_service,
        ):
            mock_fuzzy = MagicMock()
            mock_fuzzy.match.return_value = [low_fuzzy]
            mock_fuzzy_cls.return_value = mock_fuzzy

            mock_ai = MagicMock()
            mock_ai.classify.return_value = ai_doubt
            mock_ai_cls.return_value = mock_ai

            pipeline = ClassificationPipeline()
            pipeline.classify_document(
                document_id=DOC_ID,
                client_id=CLIENT_ID,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                financial_year=2024,
            )

        # All inserted rows must NOT have status="pending"
        for row in inserted_rows:
            assert row.get("status") != "pending", (
                f"Item was left in 'pending' status: {row}"
            )


# ══════════════════════════════════════════════════════════════════════════════
# ARQ Worker: run_classification
# ══════════════════════════════════════════════════════════════════════════════


class TestClassificationWorker:
    """Tests for the run_classification ARQ background task."""

    @pytest.mark.asyncio
    async def test_worker_runs_pipeline_for_verified_document(self):
        """run_classification calls the pipeline for a verified document."""
        from app.workers.classification_tasks import run_classification

        mock_service = _make_service()
        # Document fetch
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT_VERIFIED
        # Client fetch
        mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_CLIENT]
        # Line item IDs (for delete)
        # Classifications delete
        mock_service.table.return_value.delete.return_value.in_.return_value.execute.return_value.data = []

        mock_pipeline = MagicMock()
        mock_pipeline.classify_document.return_value = {
            "total": 1,
            "high_confidence": 1,
            "medium_confidence": 0,
            "needs_review": 0,
        }

        ctx = {}

        with patch(
            "app.workers.classification_tasks.get_service_client",
            return_value=mock_service,
        ), patch(
            "app.workers.classification_tasks.ClassificationPipeline",
            return_value=mock_pipeline,
        ):
            result = await run_classification(ctx, DOC_ID)

        assert result["document_id"] == DOC_ID
        assert result["status"] == "classified"
        mock_pipeline.classify_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_worker_guard_rejects_non_verified_document(self):
        """run_classification raises ValueError for non-verified documents."""
        from app.workers.classification_tasks import run_classification

        mock_service = _make_service()
        # Return a non-verified document
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT_NOT_VERIFIED

        ctx = {}

        with patch(
            "app.workers.classification_tasks.get_service_client",
            return_value=mock_service,
        ):
            with pytest.raises(ValueError, match="verified"):
                await run_classification(ctx, DOC_ID)

    @pytest.mark.asyncio
    async def test_worker_deletes_existing_classifications_for_idempotency(self):
        """run_classification deletes existing classifications before inserting new ones."""
        from app.workers.classification_tasks import run_classification

        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT_VERIFIED
        mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_CLIENT]
        mock_service.table.return_value.delete.return_value.in_.return_value.execute.return_value.data = []

        mock_pipeline = MagicMock()
        mock_pipeline.classify_document.return_value = {
            "total": 0,
            "high_confidence": 0,
            "medium_confidence": 0,
            "needs_review": 0,
        }

        ctx = {}

        with patch(
            "app.workers.classification_tasks.get_service_client",
            return_value=mock_service,
        ), patch(
            "app.workers.classification_tasks.ClassificationPipeline",
            return_value=mock_pipeline,
        ):
            await run_classification(ctx, DOC_ID)

        # Delete must be called for idempotency
        delete_calls = mock_service.table.return_value.delete.call_args_list
        assert len(delete_calls) >= 1

    @pytest.mark.asyncio
    async def test_worker_fetches_industry_type_from_client(self):
        """run_classification passes industry_type from client record to pipeline."""
        from app.workers.classification_tasks import run_classification

        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT_VERIFIED
        mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {**SAMPLE_CLIENT, "industry_type": "service"}
        ]
        mock_service.table.return_value.delete.return_value.in_.return_value.execute.return_value.data = []

        captured_kwargs = {}

        def capture_classify_document(**kwargs):
            captured_kwargs.update(kwargs)
            return {"total": 0, "high_confidence": 0, "medium_confidence": 0, "needs_review": 0}

        mock_pipeline = MagicMock()
        mock_pipeline.classify_document.side_effect = lambda **kw: (
            captured_kwargs.update(kw) or {"total": 0, "high_confidence": 0, "medium_confidence": 0, "needs_review": 0}
        )

        ctx = {}

        with patch(
            "app.workers.classification_tasks.get_service_client",
            return_value=mock_service,
        ), patch(
            "app.workers.classification_tasks.ClassificationPipeline",
            return_value=mock_pipeline,
        ):
            await run_classification(ctx, DOC_ID)

        # Verify classify_document was called with the client's industry_type
        call_kwargs = mock_pipeline.classify_document.call_args
        assert call_kwargs is not None
        kwargs = call_kwargs.kwargs if call_kwargs.kwargs else {}
        args = call_kwargs.args if call_kwargs.args else ()
        # Check industry_type in kwargs or positional
        industry_used = kwargs.get("industry_type")
        assert industry_used == "service"

    @pytest.mark.asyncio
    async def test_worker_document_not_found_raises(self):
        """run_classification raises ValueError when document not found in DB."""
        from app.workers.classification_tasks import run_classification

        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None

        ctx = {}

        with patch(
            "app.workers.classification_tasks.get_service_client",
            return_value=mock_service,
        ):
            with pytest.raises(ValueError, match="Document not found"):
                await run_classification(ctx, "nonexistent-doc-id")


# ══════════════════════════════════════════════════════════════════════════════
# Pipeline edge / error-handler coverage
# ══════════════════════════════════════════════════════════════════════════════


class TestPipelineEdgeCases:
    """Targeted tests for branches not hit by happy-path tests."""

    def test_classify_document_medium_confidence_counted(self):
        """Items with confidence between 0 and 0.85 are counted as medium_confidence."""
        from app.services.classification.pipeline import ClassificationPipeline
        from app.services.classification.fuzzy_matcher import FuzzyMatchResult
        from app.services.classification.ai_classifier import AIClassificationResult

        low_fuzzy = FuzzyMatchResult(
            cma_field_name="Others (Admin)",
            cma_row=71,
            cma_sheet="input_sheet",
            broad_classification="",
            score=50.0,
            source="reference",
        )
        # Confident but medium-confidence (>= 0.8 but < 0.85)
        ai_medium = AIClassificationResult(
            cma_field_name="Others (Admin)",
            cma_row=71,
            cma_sheet="input_sheet",
            broad_classification="admin_expense",
            confidence=0.82,   # above doubt threshold but below high-confidence floor
            is_doubt=False,
            doubt_reason=None,
            alternatives=[],
            classification_method="ai_haiku",
        )

        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [SAMPLE_ITEM_1]
        mock_service.table.return_value.insert.return_value.execute.return_value.data = [{}]

        with patch(
            "app.services.classification.pipeline.FuzzyMatcher"
        ) as mock_fuzzy_cls, patch(
            "app.services.classification.pipeline.AIClassifier"
        ) as mock_ai_cls, patch(
            "app.services.classification.pipeline.get_service_client",
            return_value=mock_service,
        ):
            mock_fuzzy = MagicMock()
            mock_fuzzy.match.return_value = [low_fuzzy]
            mock_fuzzy_cls.return_value = mock_fuzzy

            mock_ai = MagicMock()
            mock_ai.classify.return_value = ai_medium
            mock_ai_cls.return_value = mock_ai

            pipeline = ClassificationPipeline()
            summary = pipeline.classify_document(
                document_id=DOC_ID,
                client_id=CLIENT_ID,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                financial_year=2024,
            )

        # Medium confidence item must be counted in medium_confidence bucket
        assert summary["medium_confidence"] == 1
        assert summary["high_confidence"] == 0
        assert summary["needs_review"] == 0

    def test_classify_document_item_error_creates_doubt_record(self):
        """When classify_item raises, document pipeline creates a doubt record (lines 215-241)."""
        from app.services.classification.pipeline import ClassificationPipeline

        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [SAMPLE_ITEM_1]
        mock_service.table.return_value.insert.return_value.execute.return_value.data = [{}]

        with patch(
            "app.services.classification.pipeline.FuzzyMatcher"
        ) as mock_fuzzy_cls, patch(
            "app.services.classification.pipeline.AIClassifier"
        ) as mock_ai_cls, patch(
            "app.services.classification.pipeline.get_service_client",
            return_value=mock_service,
        ):
            mock_fuzzy = MagicMock()
            mock_fuzzy.match.side_effect = Exception("DB connection error")
            mock_fuzzy_cls.return_value = mock_fuzzy

            mock_ai = MagicMock()
            mock_ai_cls.return_value = mock_ai

            pipeline = ClassificationPipeline()
            summary = pipeline.classify_document(
                document_id=DOC_ID,
                client_id=CLIENT_ID,
                industry_type="manufacturing",
                document_type="profit_and_loss",
                financial_year=2024,
            )

        # Error must produce a doubt record (needs_review=1), not crash
        assert summary["needs_review"] == 1
        assert summary["total"] == 1
        # Verify that insert was still called (for the doubt record)
        insert_calls = mock_service.table.return_value.insert.call_args_list
        assert len(insert_calls) >= 1
