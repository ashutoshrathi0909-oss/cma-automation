"""Learning system: persists user corrections and approvals into learned_mappings.

Every approve/correct action:
1. Updates the classification record status
2. Upserts to learned_mappings (insert new or increment times_used)
3. Writes an audit log entry to cma_report_history (when report_id provided)

This completes the feedback loop: next time the fuzzy matcher checks
learned_mappings first, the corrected mapping will surface at high confidence.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.dependencies import get_service_client

logger = logging.getLogger(__name__)

# Confidence floor for bulk-approve-all (items below this stay for manual review)
BULK_APPROVE_MIN_CONFIDENCE = 0.85


class LearningSystem:
    """Handles user approve/correct actions and feeds the learned_mappings table."""

    # ── Public API ────────────────────────────────────────────────────────────

    def approve_classification(
        self,
        classification_id: str,
        user_id: str,
        industry_type: str,
        cma_report_id: str | None = None,
    ) -> dict:
        """Approve a classification and write it to learned_mappings.

        Steps:
        1. Fetch classification + its line item (for source_text)
        2. Update classification status → 'approved'
        3. Upsert learned_mappings (insert or increment times_used)
        4. Audit log (when cma_report_id provided)
        """
        service = get_service_client()
        now = datetime.now(timezone.utc).isoformat()

        # ── 1. Fetch classification ───────────────────────────────────────────
        clf = self._fetch_classification(service, classification_id)
        source_text = self._get_source_text(service, clf["line_item_id"])

        # ── 2. Update classification status ──────────────────────────────────
        updated = (
            service.table("classifications")
            .update(
                {
                    "status": "approved",
                    "is_doubt": False,
                    "reviewed_by": user_id,
                    "reviewed_at": now,
                }
            )
            .eq("id", classification_id)
            .execute()
        )

        # ── 3. Upsert learned_mappings ────────────────────────────────────────
        if clf.get("cma_field_name") and source_text:
            self._upsert_learned_mapping(
                source_text=source_text,
                cma_field_name=clf["cma_field_name"],
                cma_input_row=clf["cma_row"],
                industry_type=industry_type,
                source="approval",
            )

        # ── 4. Audit log ──────────────────────────────────────────────────────
        if cma_report_id:
            self._log_audit(
                service=service,
                cma_report_id=cma_report_id,
                action="classification_approved",
                details={
                    "classification_id": classification_id,
                    "cma_field_name": clf.get("cma_field_name"),
                    "source_text": source_text,
                },
                user_id=user_id,
                now=now,
            )

        return updated.data[0] if updated.data else clf

    def correct_classification(
        self,
        classification_id: str,
        correction: dict,
        user_id: str,
        industry_type: str,
        cma_report_id: str | None = None,
    ) -> dict:
        """Apply a user correction to a classification.

        Steps:
        1. Fetch original classification + its line item
        2. Insert correction record into classification_corrections
        3. Update classification with new CMA field + status → 'corrected'
        4. Upsert learned_mappings with the correction (source="correction")
        5. Audit log (when cma_report_id provided)
        """
        service = get_service_client()
        now = datetime.now(timezone.utc).isoformat()

        # ── 1. Fetch classification ───────────────────────────────────────────
        clf = self._fetch_classification(service, classification_id)
        source_text = self._get_source_text(service, clf["line_item_id"])

        # ── 2. Insert correction record ───────────────────────────────────────
        service.table("classification_corrections").insert(
            {
                "classification_id": classification_id,
                "client_id": clf["client_id"],
                "original_cma_field": clf.get("cma_field_name"),
                "corrected_cma_field": correction["cma_field_name"],
                "original_cma_row": clf.get("cma_row"),
                "corrected_cma_row": correction["cma_row"],
                "industry_type": industry_type,
                "source_text": source_text,
                "correction_reason": correction.get("correction_reason"),
                "corrected_by": user_id,
                "corrected_at": now,
            }
        ).execute()

        # ── 3. Update classification ──────────────────────────────────────────
        updated = (
            service.table("classifications")
            .update(
                {
                    "cma_field_name": correction["cma_field_name"],
                    "cma_row": correction["cma_row"],
                    "cma_sheet": correction.get("cma_sheet", "input_sheet"),
                    "broad_classification": correction.get("broad_classification", ""),
                    "status": "corrected",
                    "reviewed_by": user_id,
                    "reviewed_at": now,
                    "correction_note": correction.get("correction_reason"),
                    "is_doubt": False,
                }
            )
            .eq("id", classification_id)
            .execute()
        )

        # ── 4. Upsert learned_mappings with the corrected field ───────────────
        if source_text:
            self._upsert_learned_mapping(
                source_text=source_text,
                cma_field_name=correction["cma_field_name"],
                cma_input_row=correction["cma_row"],
                industry_type=industry_type,
                source="correction",
            )

        # ── 5. Audit log ──────────────────────────────────────────────────────
        if cma_report_id:
            self._log_audit(
                service=service,
                cma_report_id=cma_report_id,
                action="classification_corrected",
                details={
                    "classification_id": classification_id,
                    "original_field": clf.get("cma_field_name"),
                    "corrected_field": correction["cma_field_name"],
                    "source_text": source_text,
                    "reason": correction.get("correction_reason"),
                },
                user_id=user_id,
                now=now,
            )

        return updated.data[0] if updated.data else clf

    def bulk_approve(
        self,
        classification_ids: list[str] | None,
        user_id: str,
        industry_type: str,
        client_id: str,
        cma_report_id: str | None = None,
    ) -> int:
        """Approve multiple classifications at once.

        Parameters
        ----------
        classification_ids:
            If provided, approve only these IDs.
            If None, approve all auto_classified items with confidence >= 0.85
            scoped to the requesting user's client.
        client_id:
            Required. Scopes the global query to prevent cross-client mutation.

        Returns
        -------
        Number of classifications approved.
        """
        service = get_service_client()

        # Fetch target classifications
        if classification_ids is not None:
            result = (
                service.table("classifications")
                .select("*")
                .in_("id", classification_ids)
                .execute()
            )
        else:
            # Approve all high-confidence auto-classified items scoped to this client
            result = (
                service.table("classifications")
                .select("*")
                .eq("status", "auto_classified")
                .eq("is_doubt", False)
                .eq("client_id", client_id)
                .execute()
            )

        classifications = result.data or []
        # Filter by confidence threshold when doing bulk-all
        if classification_ids is None:
            classifications = [
                c for c in classifications
                if (c.get("confidence_score") or 0.0) >= BULK_APPROVE_MIN_CONFIDENCE
            ]

        approved_count = 0
        for clf in classifications:
            try:
                self.approve_classification(
                    classification_id=clf["id"],
                    user_id=user_id,
                    industry_type=industry_type,
                    cma_report_id=cma_report_id,
                )
                approved_count += 1
            except Exception as exc:
                logger.error(
                    "bulk_approve failed for classification_id=%s: %s",
                    clf["id"],
                    exc,
                )

        logger.info(
            "bulk_approve: approved %d/%d classifications",
            approved_count,
            len(classifications),
        )
        return approved_count

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _upsert_learned_mapping(
        self,
        source_text: str,
        cma_field_name: str,
        cma_input_row: int | None,
        industry_type: str,
        source: str,  # "approval" or "correction"
    ) -> None:
        """Insert or update a learned mapping using DB-level upsert.

        Uses upsert with on_conflict to prevent duplicate rows under concurrent
        bulk-approve operations. The times_used count is fetched first for
        best-effort increment; the upsert guarantees no duplicate rows even if
        two workers race on the same (source_text, cma_field_name, industry_type).
        """
        service = get_service_client()
        now = datetime.now(timezone.utc).isoformat()

        # Fetch existing to compute incremented times_used (best-effort)
        existing_result = (
            service.table("learned_mappings")
            .select("times_used")
            .eq("source_text", source_text)
            .eq("cma_field_name", cma_field_name)
            .eq("industry_type", industry_type)
            .execute()
        )
        existing = existing_result.data
        times_used = (existing[0]["times_used"] + 1) if existing else 1

        # Upsert — on_conflict prevents duplicate rows from concurrent calls
        service.table("learned_mappings").upsert(
            {
                "source_text": source_text,
                "cma_field_name": cma_field_name,
                "cma_input_row": cma_input_row,
                "industry_type": industry_type,
                "times_used": times_used,
                "last_used_at": now,
                "source": source,
            },
            on_conflict="source_text,cma_field_name,industry_type",
        ).execute()

    def _fetch_classification(self, service, classification_id: str) -> dict:
        """Fetch a classification by ID. Raises ValueError if not found."""
        result = (
            service.table("classifications")
            .select("*")
            .eq("id", classification_id)
            .single()
            .execute()
        )
        if not result.data:
            raise ValueError(f"Classification not found: {classification_id}")
        return result.data

    def _get_source_text(self, service, line_item_id: str) -> str | None:
        """Fetch the source_text from extracted_line_items for a line_item_id."""
        result = (
            service.table("extracted_line_items")
            .select("source_text")
            .eq("id", line_item_id)
            .execute()
        )
        items = result.data or []
        if items:
            return items[0].get("source_text")
        return None

    def _log_audit(
        self,
        service,
        cma_report_id: str,
        action: str,
        details: dict,
        user_id: str,
        now: str,
    ) -> None:
        """Write an audit log entry to cma_report_history."""
        try:
            service.table("cma_report_history").insert(
                {
                    "cma_report_id": cma_report_id,
                    "action": action,
                    "action_details": details,
                    "performed_by": user_id,
                    "performed_at": now,
                }
            ).execute()
        except Exception as exc:
            # Audit logging must never crash the main flow
            logger.error("Audit log failed for action=%s: %s", action, exc)
