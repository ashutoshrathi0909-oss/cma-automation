"""Centralised audit logging for CMA report history.

All writes to cma_report_history go through log_action().
Errors are swallowed so audit failures never crash the main request flow.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def log_action(
    service,
    user_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    before: dict | None = None,
    after: dict | None = None,
) -> None:
    """Write an audit entry to cma_report_history.

    Parameters
    ----------
    service      — Supabase service client
    user_id      — ID of the user performing the action
    action       — Short action label, e.g. "approve_classification"
    entity_type  — Type of entity, e.g. "classification", "cma_report"
    entity_id    — ID of the entity being acted upon (used as cma_report_id
                   when entity_type == "cma_report", otherwise as a detail)
    before       — State before the action (may be None)
    after        — State after the action (may be None)
    """
    now = datetime.now(timezone.utc).isoformat()
    try:
        service.table("cma_report_history").insert(
            {
                "cma_report_id": entity_id,
                "action": action,
                "action_details": {
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "before": before,
                    "after": after,
                },
                "performed_by": user_id,
                "performed_at": now,
            }
        ).execute()
    except Exception as exc:
        logger.error(
            "Audit log failed — action=%s entity_type=%s entity_id=%s: %s",
            action,
            entity_type,
            entity_id,
            exc,
        )
