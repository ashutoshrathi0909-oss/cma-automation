"""Phase 6B: Audit service tests.

TDD — RED phase: written BEFORE implementation to define expected behaviour.

Tests:
  - test_log_action_writes_to_cma_report_history
  - test_log_action_swallows_db_errors
  - test_log_action_captures_before_and_after
"""

from unittest.mock import MagicMock, call, patch

import pytest

from app.services.audit_service import log_action


# ── Fixtures ───────────────────────────────────────────────────────────────


def _make_service():
    return MagicMock()


# ══════════════════════════════════════════════════════════════════════════
# log_action()
# ══════════════════════════════════════════════════════════════════════════


class TestLogAction:
    def test_log_action_writes_to_cma_report_history(self):
        """log_action inserts a row into cma_report_history."""
        mock_service = _make_service()

        log_action(
            service=mock_service,
            user_id="user-001",
            action="approve_classification",
            entity_type="classification",
            entity_id="report-001",
        )

        # Verify the insert chain was called
        mock_service.table.assert_called_with("cma_report_history")
        mock_service.table.return_value.insert.assert_called_once()
        insert_payload = mock_service.table.return_value.insert.call_args[0][0]

        assert insert_payload["cma_report_id"] == "report-001"
        assert insert_payload["action"] == "approve_classification"
        assert insert_payload["performed_by"] == "user-001"
        assert "performed_at" in insert_payload

    def test_log_action_swallows_db_errors(self):
        """log_action never raises even when the DB insert fails."""
        mock_service = _make_service()
        mock_service.table.return_value.insert.return_value.execute.side_effect = (
            RuntimeError("DB connection lost")
        )

        # Must not raise
        log_action(
            service=mock_service,
            user_id="user-001",
            action="approve_classification",
            entity_type="classification",
            entity_id="report-001",
        )

    def test_log_action_captures_before_and_after(self):
        """log_action stores before/after state in action_details."""
        mock_service = _make_service()
        before = {"status": "auto_classified", "cma_field_name": "Wages"}
        after = {"status": "approved", "cma_field_name": "Wages"}

        log_action(
            service=mock_service,
            user_id="user-002",
            action="approve_classification",
            entity_type="classification",
            entity_id="report-002",
            before=before,
            after=after,
        )

        insert_payload = mock_service.table.return_value.insert.call_args[0][0]
        details = insert_payload["action_details"]

        assert details["before"] == before
        assert details["after"] == after
        assert details["entity_type"] == "classification"
