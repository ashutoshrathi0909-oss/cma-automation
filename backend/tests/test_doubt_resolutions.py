# backend/tests/test_doubt_resolutions.py
"""Phase 4: Doubt resolution — TDD RED phase.

Tests the employee doubt resolution and father approval workflow.
"""

import pytest
from unittest.mock import MagicMock


class TestDoubtResolutionService:
    """Doubt resolution service must handle employee corrections and father approvals."""

    def test_import_succeeds(self):
        from app.services.doubt_resolution import DoubtResolutionService  # noqa: F401

    def test_resolve_doubt_creates_record(self):
        """Resolving a doubt creates a doubt_resolutions record."""
        from app.services.doubt_resolution import DoubtResolutionService

        service = MagicMock()
        # Mock classifications lookup
        service.table("classifications").select.return_value \
            .eq.return_value.single.return_value.execute.return_value.data = {
                "id": "clf-001",
                "extracted_line_items": {"source_text": "Wages & Salaries", "document_id": "doc-001"},
            }
        # Mock doubt_resolutions insert
        inserted = {
            "id": "res-001",
            "classification_id": "clf-001",
            "resolved_cma_row": 45,
            "resolved_cma_field": "Wages",
            "status": "pending",
        }
        service.table("doubt_resolutions").insert.return_value \
            .execute.return_value.data = [inserted]

        svc = DoubtResolutionService(service)

        result = svc.resolve_doubt(
            classification_id="clf-001",
            resolved_cma_row=45,
            resolved_cma_field="Wages",
            resolved_by="user-001",
            note="This is clearly wages",
        )
        assert result is not None
        assert result["id"] == "res-001"

    def test_approve_resolution_creates_proposed_rule(self):
        """Father approving a resolution creates a proposed_rule."""
        from app.services.doubt_resolution import DoubtResolutionService

        service = MagicMock()
        # Mock fetching the resolution
        service.table("doubt_resolutions").select.return_value \
            .eq.return_value.single.return_value.execute.return_value.data = {
                "id": "res-001",
                "classification_id": "clf-001",
                "original_source_text": "Wages & Salaries",
                "resolved_cma_row": 45,
                "resolved_cma_field": "Wages",
                "status": "pending",
            }

        svc = DoubtResolutionService(service)

        result = svc.approve_resolution(
            resolution_id="res-001",
            approved_by="father-001",
        )
        assert result is not None
        assert result.get("status") == "approved"

    def test_reject_resolution(self):
        """Father can reject a resolution."""
        from app.services.doubt_resolution import DoubtResolutionService

        service = MagicMock()
        svc = DoubtResolutionService(service)

        result = svc.reject_resolution(
            resolution_id="res-001",
            rejected_by="father-001",
            reason="Wrong classification",
        )
        assert result is not None
        assert result.get("status") == "rejected"

    def test_list_pending_doubts(self):
        """Can list all pending doubt items for a report."""
        from app.services.doubt_resolution import DoubtResolutionService

        service = MagicMock()
        # Mock report lookup
        service.table("cma_reports").select.return_value \
            .eq.return_value.single.return_value.execute.return_value.data = {
                "document_ids": ["doc-001"],
            }
        # Mock line items lookup
        service.table("extracted_line_items").select.return_value \
            .in_.return_value.execute.return_value.data = [
                {"id": "li-001"},
            ]
        # Mock classifications lookup
        service.table("classifications").select.return_value \
            .in_.return_value.eq.return_value.execute.return_value.data = [
                {"id": "clf-001", "line_item_id": "li-001", "cma_row": 45, "is_doubt": True},
            ]

        svc = DoubtResolutionService(service)

        result = svc.list_pending_doubts(report_id="rpt-001")
        assert isinstance(result, list)
        assert len(result) == 1
