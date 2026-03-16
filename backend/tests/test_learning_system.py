"""Phase 5D: Learning System unit tests.

TDD — RED phase: written BEFORE implementation.

Coverage target: 100% on services/classification/learning_system.py

Tests verify:
- Approve: status → 'approved', learned_mappings upserted
- Correct: classification_corrections inserted, classification updated, learned upserted
- Bulk approve: approves all or specified IDs
- Audit log written to cma_report_history
- Upsert: increment times_used on existing mapping
"""

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timezone


# ── Sample data ─────────────────────────────────────────────────────────────────

CLASSIFICATION_ID = "clf-uuid-0001"
LINE_ITEM_ID = "item-uuid-1234"
CLIENT_ID = "client-uuid-abcd"
USER_ID = "user-uuid-5678"
REPORT_ID = "report-uuid-9999"

SAMPLE_CLASSIFICATION = {
    "id": CLASSIFICATION_ID,
    "line_item_id": LINE_ITEM_ID,
    "client_id": CLIENT_ID,
    "cma_field_name": "Wages",
    "cma_row": 45,
    "cma_sheet": "input_sheet",
    "cma_column": "C",
    "broad_classification": "manufacturing_expense",
    "classification_method": "ai_haiku",
    "confidence_score": 0.72,
    "fuzzy_match_score": 65.0,
    "is_doubt": True,
    "doubt_reason": "Ambiguous between Wages and Salary",
    "ai_best_guess": "Wages",
    "alternative_fields": [],
    "status": "needs_review",
    "reviewed_by": None,
    "reviewed_at": None,
    "correction_note": None,
    "created_at": "2025-01-01T00:00:00+00:00",
}

SAMPLE_LINE_ITEM = {
    "id": LINE_ITEM_ID,
    "document_id": "doc-uuid-xyz",
    "description": "Staff Wages and Salaries",
    "amount": 500000.0,
    "section": "expenses",
    "raw_text": "Staff Wages and Salaries  5,00,000",
    "is_verified": True,
}

SAMPLE_LEARNED_EXISTING = {
    "id": "learned-uuid-001",
    "source_text": "Staff Wages and Salaries",
    "cma_field_name": "Wages",
    "cma_input_row": 45,
    "industry_type": "manufacturing",
    "times_used": 3,
    "source": "approval",
    "created_at": "2025-01-01T00:00:00+00:00",
}


def _make_service():
    """Return a spec'd MagicMock for the Supabase service client."""
    return MagicMock()


# ══════════════════════════════════════════════════════════════════════════════
# approve_classification()
# ══════════════════════════════════════════════════════════════════════════════


class TestApproveClassification:
    """Tests for LearningSystem.approve_classification()."""

    def test_approve_updates_classification_status(self):
        """approve_classification sets status → 'approved'."""
        from app.services.classification.learning_system import LearningSystem

        mock_service = _make_service()
        # fetch classification
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_CLASSIFICATION
        # fetch line item for source_text
        mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_LINE_ITEM]
        # learned_mappings select (for upsert check)
        mock_service.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        # update classification
        mock_service.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
            {**SAMPLE_CLASSIFICATION, "status": "approved", "reviewed_by": USER_ID}
        ]

        with patch(
            "app.services.classification.learning_system.get_service_client",
            return_value=mock_service,
        ):
            ls = LearningSystem()
            result = ls.approve_classification(
                classification_id=CLASSIFICATION_ID,
                user_id=USER_ID,
                industry_type="manufacturing",
            )

        # Verify update was called with approved status
        update_calls = mock_service.table.return_value.update.call_args_list
        assert any(
            call_args[0][0].get("status") == "approved"
            for call_args in update_calls
            if call_args[0]
        )

    def test_approve_creates_learned_mapping_when_new(self):
        """approve_classification upserts new entry in learned_mappings (times_used=1)."""
        from app.services.classification.learning_system import LearningSystem

        mock_service = _make_service()
        # classification fetch
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_CLASSIFICATION
        # line item fetch
        mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_LINE_ITEM]
        # learned_mappings check (no existing row)
        mock_service.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        mock_service.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [SAMPLE_CLASSIFICATION]
        mock_service.table.return_value.upsert.return_value.execute.return_value.data = [SAMPLE_LEARNED_EXISTING]

        with patch(
            "app.services.classification.learning_system.get_service_client",
            return_value=mock_service,
        ):
            ls = LearningSystem()
            ls.approve_classification(
                classification_id=CLASSIFICATION_ID,
                user_id=USER_ID,
                industry_type="manufacturing",
            )

        # Verify upsert was called on learned_mappings with times_used=1
        upsert_calls = mock_service.table.return_value.upsert.call_args_list
        assert len(upsert_calls) >= 1
        assert upsert_calls[0][0][0]["times_used"] == 1

    def test_approve_increments_times_used_on_existing(self):
        """approve_classification increments times_used when mapping exists."""
        from app.services.classification.learning_system import LearningSystem

        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_CLASSIFICATION
        mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_LINE_ITEM]
        # Existing learned mapping (times_used=3) → expect upsert with times_used=4
        mock_service.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = [SAMPLE_LEARNED_EXISTING]
        mock_service.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [SAMPLE_CLASSIFICATION]
        mock_service.table.return_value.upsert.return_value.execute.return_value.data = [{}]

        with patch(
            "app.services.classification.learning_system.get_service_client",
            return_value=mock_service,
        ):
            ls = LearningSystem()
            ls.approve_classification(
                classification_id=CLASSIFICATION_ID,
                user_id=USER_ID,
                industry_type="manufacturing",
            )

        # Verify upsert was called with times_used incremented from 3 → 4
        upsert_calls = mock_service.table.return_value.upsert.call_args_list
        times_used_incremented = any(
            call_args[0][0].get("times_used") == 4
            for call_args in upsert_calls
            if call_args[0]
        )
        assert times_used_incremented, "times_used should be incremented to 4 via upsert"

    def test_approve_logs_audit_trail(self):
        """approve_classification writes an entry to cma_report_history."""
        from app.services.classification.learning_system import LearningSystem

        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_CLASSIFICATION
        mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_LINE_ITEM]
        mock_service.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        mock_service.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [SAMPLE_CLASSIFICATION]
        mock_service.table.return_value.insert.return_value.execute.return_value.data = [{}]

        with patch(
            "app.services.classification.learning_system.get_service_client",
            return_value=mock_service,
        ):
            ls = LearningSystem()
            ls.approve_classification(
                classification_id=CLASSIFICATION_ID,
                user_id=USER_ID,
                industry_type="manufacturing",
                cma_report_id=REPORT_ID,
            )

        # Verify insert was called on cma_report_history
        insert_calls = mock_service.table.return_value.insert.call_args_list
        history_inserts = [
            c for c in insert_calls
            if c[0] and c[0][0].get("action") is not None
        ]
        assert len(history_inserts) >= 1

    def test_approve_skips_audit_when_no_report_id(self):
        """approve_classification does NOT error when cma_report_id is None."""
        from app.services.classification.learning_system import LearningSystem

        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_CLASSIFICATION
        mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_LINE_ITEM]
        mock_service.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        mock_service.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [SAMPLE_CLASSIFICATION]
        mock_service.table.return_value.insert.return_value.execute.return_value.data = [{}]

        with patch(
            "app.services.classification.learning_system.get_service_client",
            return_value=mock_service,
        ):
            ls = LearningSystem()
            # Should not raise
            ls.approve_classification(
                classification_id=CLASSIFICATION_ID,
                user_id=USER_ID,
                industry_type="manufacturing",
                cma_report_id=None,
            )


# ══════════════════════════════════════════════════════════════════════════════
# correct_classification()
# ══════════════════════════════════════════════════════════════════════════════


class TestCorrectClassification:
    """Tests for LearningSystem.correct_classification()."""

    CORRECTION = {
        "cma_field_name": "Salary and staff expenses",
        "cma_row": 67,
        "cma_sheet": "input_sheet",
        "broad_classification": "admin_expense",
        "correction_reason": "This firm is service industry, not manufacturing",
    }

    def test_correction_inserts_to_corrections_table(self):
        """correct_classification inserts a row into classification_corrections."""
        from app.services.classification.learning_system import LearningSystem

        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_CLASSIFICATION
        mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_LINE_ITEM]
        mock_service.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        mock_service.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [SAMPLE_CLASSIFICATION]
        mock_service.table.return_value.insert.return_value.execute.return_value.data = [{}]

        with patch(
            "app.services.classification.learning_system.get_service_client",
            return_value=mock_service,
        ):
            ls = LearningSystem()
            ls.correct_classification(
                classification_id=CLASSIFICATION_ID,
                correction=self.CORRECTION,
                user_id=USER_ID,
                industry_type="service",
            )

        insert_calls = mock_service.table.return_value.insert.call_args_list
        correction_inserts = [
            c for c in insert_calls
            if c[0] and c[0][0].get("original_cma_field") is not None
        ]
        assert len(correction_inserts) >= 1

    def test_correction_updates_classification_with_new_field(self):
        """correct_classification updates cma_field_name and cma_row on classification."""
        from app.services.classification.learning_system import LearningSystem

        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_CLASSIFICATION
        mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_LINE_ITEM]
        mock_service.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        mock_service.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [SAMPLE_CLASSIFICATION]
        mock_service.table.return_value.insert.return_value.execute.return_value.data = [{}]

        with patch(
            "app.services.classification.learning_system.get_service_client",
            return_value=mock_service,
        ):
            ls = LearningSystem()
            ls.correct_classification(
                classification_id=CLASSIFICATION_ID,
                correction=self.CORRECTION,
                user_id=USER_ID,
                industry_type="service",
            )

        update_calls = mock_service.table.return_value.update.call_args_list
        # Check that an update contains the new cma_field_name
        field_updated = any(
            call_args[0][0].get("cma_field_name") == "Salary and staff expenses"
            for call_args in update_calls
            if call_args[0]
        )
        assert field_updated

    def test_correction_sets_status_corrected(self):
        """correct_classification sets status → 'corrected'."""
        from app.services.classification.learning_system import LearningSystem

        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_CLASSIFICATION
        mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_LINE_ITEM]
        mock_service.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        mock_service.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [SAMPLE_CLASSIFICATION]
        mock_service.table.return_value.insert.return_value.execute.return_value.data = [{}]

        with patch(
            "app.services.classification.learning_system.get_service_client",
            return_value=mock_service,
        ):
            ls = LearningSystem()
            ls.correct_classification(
                classification_id=CLASSIFICATION_ID,
                correction=self.CORRECTION,
                user_id=USER_ID,
                industry_type="service",
            )

        update_calls = mock_service.table.return_value.update.call_args_list
        corrected_status = any(
            call_args[0][0].get("status") == "corrected"
            for call_args in update_calls
            if call_args[0]
        )
        assert corrected_status

    def test_correction_saves_to_learned_mappings(self):
        """correct_classification upserts the corrected mapping to learned_mappings."""
        from app.services.classification.learning_system import LearningSystem

        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_CLASSIFICATION
        mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_LINE_ITEM]
        mock_service.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        mock_service.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [SAMPLE_CLASSIFICATION]
        mock_service.table.return_value.upsert.return_value.execute.return_value.data = [{}]
        mock_service.table.return_value.insert.return_value.execute.return_value.data = [{}]

        with patch(
            "app.services.classification.learning_system.get_service_client",
            return_value=mock_service,
        ):
            ls = LearningSystem()
            ls.correct_classification(
                classification_id=CLASSIFICATION_ID,
                correction=self.CORRECTION,
                user_id=USER_ID,
                industry_type="service",
            )

        # Upsert must be called with source="correction"
        upsert_calls = mock_service.table.return_value.upsert.call_args_list
        learned_upserts = [
            c for c in upsert_calls
            if c[0] and c[0][0].get("source") == "correction"
        ]
        assert len(learned_upserts) >= 1

    def test_correction_logs_audit_trail(self):
        """correct_classification writes to cma_report_history."""
        from app.services.classification.learning_system import LearningSystem

        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_CLASSIFICATION
        mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_LINE_ITEM]
        mock_service.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        mock_service.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [SAMPLE_CLASSIFICATION]
        mock_service.table.return_value.insert.return_value.execute.return_value.data = [{}]

        with patch(
            "app.services.classification.learning_system.get_service_client",
            return_value=mock_service,
        ):
            ls = LearningSystem()
            ls.correct_classification(
                classification_id=CLASSIFICATION_ID,
                correction=self.CORRECTION,
                user_id=USER_ID,
                industry_type="service",
                cma_report_id=REPORT_ID,
            )

        insert_calls = mock_service.table.return_value.insert.call_args_list
        history_inserts = [
            c for c in insert_calls
            if c[0] and c[0][0].get("action") is not None
        ]
        assert len(history_inserts) >= 1


# ══════════════════════════════════════════════════════════════════════════════
# bulk_approve()
# ══════════════════════════════════════════════════════════════════════════════


class TestBulkApprove:
    """Tests for LearningSystem.bulk_approve()."""

    SAMPLE_AUTO_CLASSIFIED = [
        {
            **SAMPLE_CLASSIFICATION,
            "id": "clf-001",
            "status": "auto_classified",
            "confidence_score": 0.92,
            "is_doubt": False,
        },
        {
            **SAMPLE_CLASSIFICATION,
            "id": "clf-002",
            "status": "auto_classified",
            "confidence_score": 0.88,
            "is_doubt": False,
        },
    ]

    def test_bulk_approve_specific_ids(self):
        """bulk_approve with explicit IDs approves only those classifications."""
        from app.services.classification.learning_system import LearningSystem

        mock_service = _make_service()
        # Return classifications for the given IDs
        mock_service.table.return_value.select.return_value.in_.return_value.execute.return_value.data = self.SAMPLE_AUTO_CLASSIFIED[:1]
        mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_LINE_ITEM]
        mock_service.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        mock_service.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [SAMPLE_CLASSIFICATION]
        mock_service.table.return_value.upsert.return_value.execute.return_value.data = [{}]

        with patch(
            "app.services.classification.learning_system.get_service_client",
            return_value=mock_service,
        ):
            ls = LearningSystem()
            count = ls.bulk_approve(
                classification_ids=["clf-001"],
                user_id=USER_ID,
                industry_type="manufacturing",
                client_id=CLIENT_ID,
            )

        assert count == 1

    def test_bulk_approve_returns_count(self):
        """bulk_approve returns the number of classifications approved."""
        from app.services.classification.learning_system import LearningSystem

        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.in_.return_value.execute.return_value.data = self.SAMPLE_AUTO_CLASSIFIED
        mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_LINE_ITEM]
        mock_service.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        mock_service.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [SAMPLE_CLASSIFICATION]
        mock_service.table.return_value.upsert.return_value.execute.return_value.data = [{}]

        with patch(
            "app.services.classification.learning_system.get_service_client",
            return_value=mock_service,
        ):
            ls = LearningSystem()
            count = ls.bulk_approve(
                classification_ids=["clf-001", "clf-002"],
                user_id=USER_ID,
                industry_type="manufacturing",
                client_id=CLIENT_ID,
            )

        assert count == 2

    def test_bulk_approve_none_ids_approves_high_confidence(self):
        """bulk_approve with ids=None approves all auto_classified with confidence >= 0.85,
        scoped to the given client_id."""
        from app.services.classification.learning_system import LearningSystem

        sample_auto = self.SAMPLE_AUTO_CLASSIFIED

        # Use table-name-aware mock to avoid conflicts between:
        # - classifications bulk-fetch (3 eq: status, is_doubt, client_id)
        # - learned_mappings existing check (3 eq: source_text, field, industry)
        def table_side_effect(table_name):
            t = MagicMock()
            if table_name == "classifications":
                # None-IDs bulk fetch path
                t.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = sample_auto
                # _fetch_classification path (uses .single())
                t.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_CLASSIFICATION
                t.update.return_value.eq.return_value.execute.return_value.data = [SAMPLE_CLASSIFICATION]
            elif table_name == "extracted_line_items":
                t.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_LINE_ITEM]
            elif table_name == "learned_mappings":
                t.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
                t.upsert.return_value.execute.return_value.data = [{}]
            elif table_name == "cma_report_history":
                t.insert.return_value.execute.return_value.data = [{}]
            return t

        mock_service = MagicMock()
        mock_service.table.side_effect = table_side_effect

        with patch(
            "app.services.classification.learning_system.get_service_client",
            return_value=mock_service,
        ):
            ls = LearningSystem()
            count = ls.bulk_approve(
                classification_ids=None,
                user_id=USER_ID,
                industry_type="manufacturing",
                client_id=CLIENT_ID,
            )

        # Both sample items have confidence >= 0.85
        assert count == 2


# ══════════════════════════════════════════════════════════════════════════════
# Learned mapping upsert logic
# ══════════════════════════════════════════════════════════════════════════════


class TestLearnedMappingUpsert:
    """Tests for the learned_mappings upsert (insert new / increment existing)."""

    def test_upsert_inserts_new_mapping(self):
        """_upsert_learned_mapping upserts with times_used=1 when no existing row found."""
        from app.services.classification.learning_system import LearningSystem

        mock_service = _make_service()
        # No existing mapping
        mock_service.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        mock_service.table.return_value.upsert.return_value.execute.return_value.data = [{}]

        with patch(
            "app.services.classification.learning_system.get_service_client",
            return_value=mock_service,
        ):
            ls = LearningSystem()
            ls._upsert_learned_mapping(
                source_text="Staff Wages",
                cma_field_name="Wages",
                cma_input_row=45,
                industry_type="manufacturing",
                source="approval",
            )

        # DB-level upsert must be called (not insert)
        upsert_calls = mock_service.table.return_value.upsert.call_args_list
        assert len(upsert_calls) >= 1
        upsert_data = upsert_calls[0][0][0]
        assert upsert_data["times_used"] == 1

    def test_upsert_increments_times_used_on_existing(self):
        """_upsert_learned_mapping increments times_used when row exists."""
        from app.services.classification.learning_system import LearningSystem

        existing = {**SAMPLE_LEARNED_EXISTING, "times_used": 3}
        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = [existing]
        mock_service.table.return_value.upsert.return_value.execute.return_value.data = [{}]

        with patch(
            "app.services.classification.learning_system.get_service_client",
            return_value=mock_service,
        ):
            ls = LearningSystem()
            ls._upsert_learned_mapping(
                source_text="Staff Wages and Salaries",
                cma_field_name="Wages",
                cma_input_row=45,
                industry_type="manufacturing",
                source="approval",
            )

        # Upsert must be called with times_used incremented from 3 → 4
        upsert_calls = mock_service.table.return_value.upsert.call_args_list
        assert len(upsert_calls) >= 1
        upsert_data = upsert_calls[0][0][0]
        assert upsert_data["times_used"] == 4, "times_used should be incremented to 4"


# ══════════════════════════════════════════════════════════════════════════════
# Edge / guard coverage
# ══════════════════════════════════════════════════════════════════════════════


class TestLearningSystemEdgeCases:
    """Targeted tests for error-handling branches not covered by happy-path tests."""

    def test_fetch_classification_raises_when_not_found(self):
        """_fetch_classification raises ValueError for non-existent ID (line 312)."""
        from app.services.classification.learning_system import LearningSystem

        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None

        with patch(
            "app.services.classification.learning_system.get_service_client",
            return_value=mock_service,
        ):
            ls = LearningSystem()
            with pytest.raises(ValueError, match="Classification not found"):
                ls._fetch_classification(mock_service, "nonexistent-id")

    def test_get_source_text_returns_none_when_no_items(self):
        """_get_source_text returns None when line item not found (line 326)."""
        from app.services.classification.learning_system import LearningSystem

        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        with patch(
            "app.services.classification.learning_system.get_service_client",
            return_value=mock_service,
        ):
            ls = LearningSystem()
            result = ls._get_source_text(mock_service, "nonexistent-item-id")

        assert result is None

    def test_log_audit_does_not_crash_on_db_error(self):
        """_log_audit catches DB errors and logs them without crashing (lines 348-350)."""
        from app.services.classification.learning_system import LearningSystem

        mock_service = _make_service()
        mock_service.table.return_value.insert.return_value.execute.side_effect = Exception("DB connection error")

        with patch(
            "app.services.classification.learning_system.get_service_client",
            return_value=mock_service,
        ):
            ls = LearningSystem()
            # Must NOT raise — audit errors are swallowed
            ls._log_audit(
                service=mock_service,
                cma_report_id="report-uuid-123",
                action="test_action",
                details={"key": "value"},
                user_id="user-uuid-001",
                now="2025-01-01T00:00:00+00:00",
            )

    def test_bulk_approve_continues_after_single_item_failure(self):
        """bulk_approve logs errors on individual item failure and continues (lines 240-241)."""
        from app.services.classification.learning_system import LearningSystem

        # Two classifications; the second one will fail
        two_classifications = [
            {**SAMPLE_CLASSIFICATION, "id": "clf-a", "status": "auto_classified", "confidence_score": 0.92, "is_doubt": False},
            {**SAMPLE_CLASSIFICATION, "id": "clf-b", "status": "auto_classified", "confidence_score": 0.90, "is_doubt": False},
        ]

        call_count = [0]

        def approve_side_effect(classification_id, **kwargs):
            call_count[0] += 1
            if classification_id == "clf-b":
                raise Exception("DB error on second item")
            return {**SAMPLE_CLASSIFICATION, "status": "approved"}

        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.in_.return_value.execute.return_value.data = two_classifications

        with patch(
            "app.services.classification.learning_system.get_service_client",
            return_value=mock_service,
        ):
            ls = LearningSystem()
            # Patch approve_classification to simulate partial failure
            ls.approve_classification = approve_side_effect

            # Should not raise — should return count of successful approvals
            count = ls.bulk_approve(
                classification_ids=["clf-a", "clf-b"],
                user_id=USER_ID,
                industry_type="manufacturing",
                client_id=CLIENT_ID,
            )

        # Only 1 should succeed (clf-b raises)
        assert count == 1
