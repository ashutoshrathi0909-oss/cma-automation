# backend/tests/test_metrics.py
"""Phase 5: Metrics — TDD RED phase.

Tests metrics computation and API.
"""

import pytest
from unittest.mock import MagicMock


class TestMetricsService:
    """Metrics service computes classification accuracy and doubt rates."""

    def test_import_succeeds(self):
        from app.services.metrics_service import MetricsService  # noqa: F401

    def test_compute_report_metrics(self):
        """Computes accuracy and doubt rate for a report."""
        from app.services.metrics_service import MetricsService

        service = MagicMock()
        # Mock classifications query
        service.table("classifications").select.return_value \
            .eq.return_value.execute.return_value.data = [
                {"is_doubt": False, "status": "approved"},
                {"is_doubt": False, "status": "approved"},
                {"is_doubt": True, "status": "auto_classified"},
                {"is_doubt": False, "status": "auto_classified"},
            ]

        svc = MetricsService(service)
        metrics = svc.compute_report_metrics(report_id="rpt-001")

        assert metrics is not None
        assert "total_items" in metrics
        assert metrics["total_items"] == 4
        assert "doubt_count" in metrics
        assert metrics["doubt_count"] == 1
        assert "doubt_rate" in metrics

    def test_compute_system_metrics(self):
        """Computes system-wide metrics."""
        from app.services.metrics_service import MetricsService

        service = MagicMock()
        # Mock proposed_rules query
        service.table("proposed_rules").select.return_value \
            .execute.return_value.data = [
                {"status": "pending"},
                {"status": "promoted"},
                {"status": "approved"},
            ]

        svc = MetricsService(service)
        metrics = svc.compute_system_metrics()

        assert metrics is not None
        assert "total_rules" in metrics
        assert metrics["total_rules"] == 3
        assert "rules_by_status" in metrics
