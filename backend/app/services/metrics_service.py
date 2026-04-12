"""Metrics service — computes classification accuracy and system health metrics.

Provides per-report and system-wide observability for the CMA automation pipeline.
"""

from __future__ import annotations

import logging
from collections import Counter

logger = logging.getLogger(__name__)


class MetricsService:
    """Computes classification and rule metrics."""

    def __init__(self, service) -> None:
        self.service = service

    def compute_report_metrics(self, report_id: str) -> dict:
        """Compute metrics for a specific CMA report.

        Returns
        -------
        dict with total_items, doubt_count, doubt_rate, approved_count, etc.
        """
        # Fetch all classifications for documents linked to this report
        result = (
            self.service.table("classifications")
            .select("id, is_doubt, status, confidence_score")
            .eq("cma_report_id", report_id)
            .execute()
        )
        items = result.data or []

        total = len(items)
        doubt_count = sum(1 for i in items if i.get("is_doubt"))
        approved_count = sum(1 for i in items if i.get("status") == "approved")
        auto_count = sum(1 for i in items if i.get("status") == "auto_classified")

        status_counts = Counter(i.get("status", "unknown") for i in items)

        return {
            "report_id": report_id,
            "total_items": total,
            "doubt_count": doubt_count,
            "doubt_rate": round(doubt_count / total * 100, 1) if total > 0 else 0,
            "approved_count": approved_count,
            "auto_classified_count": auto_count,
            "status_breakdown": dict(status_counts),
        }

    def compute_system_metrics(self) -> dict:
        """Compute system-wide metrics across all reports.

        Returns
        -------
        dict with total_rules, rules_by_status, etc.
        """
        # Proposed rules
        rules_result = (
            self.service.table("proposed_rules")
            .select("id, status")
            .execute()
        )
        rules = rules_result.data or []

        total_rules = len(rules)
        rules_by_status = Counter(r.get("status", "unknown") for r in rules)

        # Doubt resolutions
        resolutions_result = (
            self.service.table("doubt_resolutions")
            .select("id, status")
            .execute()
        )
        resolutions = resolutions_result.data or []
        resolutions_by_status = Counter(r.get("status", "unknown") for r in resolutions)

        return {
            "total_rules": total_rules,
            "rules_by_status": dict(rules_by_status),
            "total_resolutions": len(resolutions),
            "resolutions_by_status": dict(resolutions_by_status),
        }
