"""Doubt resolution service — employee doubt correction + father approval.

Loop 1: Employees resolve doubt items from the classification pipeline.
Father reviews and approves/rejects. Approved resolutions become proposed rules.
"""

from __future__ import annotations

import logging
from app.services.rule_processor import _determine_specialist

logger = logging.getLogger(__name__)


class DoubtResolutionService:
    """Handles doubt resolution workflow."""

    def __init__(self, service) -> None:
        self.service = service

    def list_pending_doubts(self, report_id: str) -> list[dict]:
        """List all doubt classifications for a report that need resolution."""
        result = (
            self.service.table("classifications")
            .select("id, line_item_id, cma_field_name, cma_row, confidence_score")
            .eq("is_doubt", True)
            .execute()
        )
        return result.data or []

    def resolve_doubt(
        self,
        classification_id: str,
        resolved_cma_row: int,
        resolved_cma_field: str,
        resolved_by: str,
        note: str | None = None,
    ) -> dict:
        """Employee resolves a doubt item by providing the correct classification."""
        # Fetch the classification to get source text
        clf = (
            self.service.table("classifications")
            .select("*, extracted_line_items(source_text, document_id)")
            .eq("id", classification_id)
            .single()
            .execute()
        ).data

        line_item = clf.get("extracted_line_items", {}) or {}

        record = {
            "classification_id": classification_id,
            "original_source_text": line_item.get("source_text"),
            "resolved_cma_row": resolved_cma_row,
            "resolved_cma_field": resolved_cma_field,
            "resolved_by": resolved_by,
            "status": "pending",
            "note": note,
        }

        result = (
            self.service.table("doubt_resolutions")
            .insert(record)
            .execute()
        )
        return result.data[0] if result.data else record

    def approve_resolution(
        self,
        resolution_id: str,
        approved_by: str,
    ) -> dict:
        """Father approves a doubt resolution — creates a proposed rule."""
        # Fetch the resolution
        resolution = (
            self.service.table("doubt_resolutions")
            .select("*")
            .eq("id", resolution_id)
            .single()
            .execute()
        ).data

        # Update status
        self.service.table("doubt_resolutions").update({
            "status": "approved",
            "approved_by": approved_by,
            "updated_at": "now()",
        }).eq("id", resolution_id).execute()

        # Create proposed rule
        specialist = _determine_specialist(resolution["resolved_cma_row"])
        rule = {
            "source_pattern": resolution.get("original_source_text", ""),
            "original_cma_row": None,
            "target_cma_row": resolution["resolved_cma_row"],
            "specialist": specialist,
            "industry_type": "manufacturing",
            "tier_tag": "CA_VERIFIED_2026",
            "status": "pending",
            "created_by": approved_by,
        }
        self.service.table("proposed_rules").insert(rule).execute()

        # Also update the classification itself to no longer be a doubt
        self.service.table("classifications").update({
            "is_doubt": False,
            "cma_field_name": resolution["resolved_cma_field"],
            "cma_row": resolution["resolved_cma_row"],
            "status": "approved",
        }).eq("id", resolution["classification_id"]).execute()

        return {"status": "approved", "resolution_id": resolution_id}

    def reject_resolution(
        self,
        resolution_id: str,
        rejected_by: str,
        reason: str | None = None,
    ) -> dict:
        """Father rejects a doubt resolution."""
        self.service.table("doubt_resolutions").update({
            "status": "rejected",
            "rejected_by": rejected_by,
            "rejection_reason": reason,
            "updated_at": "now()",
        }).eq("id", resolution_id).execute()

        return {"status": "rejected", "resolution_id": resolution_id}
