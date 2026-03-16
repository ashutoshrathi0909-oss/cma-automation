"""Phase 8B: Rollover service tests.

Covers:
  - Pure build_rollover_items function (no mocks)
  - POST /api/rollover/preview endpoint
  - POST /api/rollover/confirm endpoint
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_current_user
from app.main import app
from app.models.schemas import UserProfile
from app.services.rollover_service import build_rollover_items

# ── Constants ──────────────────────────────────────────────────────────────

CLIENT_ID = "client-uuid-roll"
FROM_YEAR = 2023
TO_YEAR = 2024

ADMIN_USER = UserProfile(
    id="admin-uuid-0001",
    full_name="Test Admin",
    role="admin",
    created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
)

EMPLOYEE_USER = UserProfile(
    id="employee-uuid-0001",
    full_name="Test Employee",
    role="employee",
    created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
)

FROM_DOCS = [
    {
        "id": "doc-uuid-from",
        "client_id": CLIENT_ID,
        "financial_year": FROM_YEAR,
        "document_type": "balance_sheet",
        "nature": "audited",
        "extraction_status": "verified",
    }
]

# Mix of balance sheet items (should carry) and P&L items (should NOT carry)
ALL_CLASSIFIED_ITEMS = [
    {
        "id": "item-bs-001",
        "description": "Total Fixed Assets",
        "amount": 500_000.0,
        "cma_field_name": "Total Fixed Assets",
        "broad_classification": "fixed_assets",
    },
    {
        "id": "item-bs-002",
        "description": "Current Liabilities",
        "amount": 200_000.0,
        "cma_field_name": "Current Liabilities",
        "broad_classification": "current_liabilities",
    },
    {
        "id": "item-pl-001",
        "description": "Net Sales",
        "amount": 1_000_000.0,
        "cma_field_name": "Net Sales",
        "broad_classification": "income",  # P&L — must NOT carry forward
    },
    {
        "id": "item-pl-002",
        "description": "Raw Material Consumed",
        "amount": 400_000.0,
        "cma_field_name": "RM Consumed",
        "broad_classification": "manufacturing_expense",  # P&L — must NOT carry forward
    },
]


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client():
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    return TestClient(app)


@pytest.fixture
def employee_client():
    app.dependency_overrides[get_current_user] = lambda: EMPLOYEE_USER
    return TestClient(app)


@pytest.fixture
def unauthenticated_client():
    app.dependency_overrides.clear()
    return TestClient(app)


# ── Mock factory ────────────────────────────────────────────────────────────


def _make_service(**table_mocks) -> MagicMock:
    svc = MagicMock()
    svc.table.side_effect = lambda name: table_mocks.get(name, MagicMock())
    return svc


def _year_aware_docs_table(to_year_has_docs: bool = False, from_docs=FROM_DOCS):
    """
    Documents table that distinguishes year-specific queries.

    _fetch_year_documents calls:
      .select(...).eq("client_id", x).eq("financial_year", y).execute()

    First outer .eq() returns an inner mock; the inner mock's .eq() uses
    side_effect to return different data for TO_YEAR vs FROM_YEAR.
    """
    tbl = MagicMock()

    inner_eq_mock = MagicMock()

    def year_eq_se(field, value):
        m = MagicMock()
        if field == "financial_year" and value == TO_YEAR:
            m.execute.return_value.data = FROM_DOCS if to_year_has_docs else []
        else:
            m.execute.return_value.data = from_docs
        return m

    inner_eq_mock.eq.side_effect = year_eq_se
    tbl.select.return_value.eq.return_value = inner_eq_mock
    tbl.insert.return_value.execute.return_value.data = [{"id": "new-doc-uuid"}]
    return tbl


def _items_table(items):
    tbl = MagicMock()
    tbl.select.return_value.in_.return_value.execute.return_value.data = items
    tbl.insert.return_value.execute.return_value.data = [{}] * len(items)
    return tbl


def _classifications_table(clfs):
    tbl = MagicMock()
    tbl.select.return_value.in_.return_value.eq.return_value.execute.return_value.data = (
        clfs
    )
    return tbl


def _history_table():
    tbl = MagicMock()
    tbl.insert.return_value.execute.return_value.data = [{}]
    return tbl


# ══════════════════════════════════════════════════════════════════════════
# Unit tests: build_rollover_items pure function
# ══════════════════════════════════════════════════════════════════════════


class TestBuildRolloverItems:
    """Pure function unit tests — no mocks required."""

    def test_rollover_carries_forward_closing_balances(self):
        """Balance sheet items (assets, liabilities) are included in rollover."""
        items = [
            {
                "description": "Fixed Assets",
                "amount": 500.0,
                "cma_field_name": "Fixed Assets",
                "broad_classification": "fixed_assets",
            },
            {
                "description": "Current Assets",
                "amount": 100.0,
                "cma_field_name": "Current Assets",
                "broad_classification": "current_assets",
            },
        ]
        result = build_rollover_items(items)
        assert len(result) == 2
        descriptions = [r["description"] for r in result]
        assert "Fixed Assets" in descriptions
        assert "Current Assets" in descriptions

    def test_rollover_does_not_carry_forward_pl_items(self):
        """P&L items (income, expenses) are excluded from rollover."""
        result = build_rollover_items(ALL_CLASSIFIED_ITEMS)
        descriptions = [r["description"] for r in result]
        # P&L items must NOT appear
        assert "Net Sales" not in descriptions
        assert "Raw Material Consumed" not in descriptions
        # Balance sheet items MUST appear
        assert "Total Fixed Assets" in descriptions
        assert "Current Liabilities" in descriptions

    def test_rollover_empty_items_returns_empty(self):
        """Empty input returns empty list."""
        assert build_rollover_items([]) == []

    def test_rollover_excludes_items_without_broad_classification(self):
        """Items without a known balance sheet category are excluded."""
        items = [
            {
                "description": "Unknown Item",
                "amount": 100.0,
                "cma_field_name": None,
                "broad_classification": None,
            }
        ]
        assert build_rollover_items(items) == []

    def test_rollover_items_preserve_amounts(self):
        """Carried-forward items preserve the original amount exactly."""
        items = [
            {
                "description": "Net Worth",
                "amount": 750_000.0,
                "cma_field_name": "Net Worth",
                "broad_classification": "net_worth",
            }
        ]
        result = build_rollover_items(items)
        assert len(result) == 1
        assert result[0]["amount"] == 750_000.0


# ══════════════════════════════════════════════════════════════════════════
# API endpoint tests: POST /api/rollover/preview
# ══════════════════════════════════════════════════════════════════════════


class TestBuildRolloverItemsEdgeCases:
    """Additional coverage for _fetch_classified_items empty-items path."""

    def test_rollover_preview_with_no_line_items_returns_empty(self, admin_client):
        """When from_year docs exist but have no extracted line items, carry-forward is empty."""
        docs_tbl = _year_aware_docs_table(to_year_has_docs=False)
        items_tbl = MagicMock()
        # Return empty list for extracted_line_items
        items_tbl.select.return_value.in_.return_value.execute.return_value.data = []
        svc = _make_service(
            documents=docs_tbl,
            extracted_line_items=items_tbl,
            classifications=_classifications_table([]),
        )
        with patch("app.routers.rollover.get_service_client", return_value=svc):
            response = admin_client.post(
                "/api/rollover/preview",
                json={"client_id": CLIENT_ID, "from_year": FROM_YEAR, "to_year": TO_YEAR},
            )
        assert response.status_code == 200
        assert response.json()["items_to_carry_forward"] == []

    def test_rollover_preview_from_year_not_found(self, admin_client):
        """404 when from_year has no documents."""
        inner_eq_mock = MagicMock()
        inner_eq_mock.eq.return_value.execute.return_value.data = []
        docs_tbl = MagicMock()
        docs_tbl.select.return_value.eq.return_value = inner_eq_mock
        svc = _make_service(documents=docs_tbl)
        with patch("app.routers.rollover.get_service_client", return_value=svc):
            response = admin_client.post(
                "/api/rollover/preview",
                json={"client_id": CLIENT_ID, "from_year": FROM_YEAR, "to_year": TO_YEAR},
            )
        assert response.status_code == 404
        assert str(FROM_YEAR) in response.json()["detail"]


class TestRolloverPreviewEndpoint:
    """Tests for POST /api/rollover/preview."""

    def test_rollover_preview_shows_changes_without_committing(self, admin_client):
        """Preview returns items without making any DB writes."""
        bs_clfs = [
            {
                "line_item_id": "item-bs-001",
                "cma_field_name": "Fixed Assets",
                "broad_classification": "fixed_assets",
                "is_doubt": False,
            }
        ]
        bs_items = [{"id": "item-bs-001", "description": "Fixed Assets", "amount": 500.0}]
        docs_tbl = _year_aware_docs_table(to_year_has_docs=False)
        svc = _make_service(
            documents=docs_tbl,
            extracted_line_items=_items_table(bs_items),
            classifications=_classifications_table(bs_clfs),
        )
        with patch("app.routers.rollover.get_service_client", return_value=svc):
            response = admin_client.post(
                "/api/rollover/preview",
                json={
                    "client_id": CLIENT_ID,
                    "from_year": FROM_YEAR,
                    "to_year": TO_YEAR,
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["from_year"] == FROM_YEAR
        assert data["to_year"] == TO_YEAR
        assert "items_to_carry_forward" in data
        # No inserts should have been made during preview
        docs_tbl.insert.assert_not_called()

    def test_rollover_rejects_duplicate_year(self, admin_client):
        """400 when to_year already has documents for this client."""
        docs_tbl = _year_aware_docs_table(to_year_has_docs=True)
        svc = _make_service(documents=docs_tbl)
        with patch("app.routers.rollover.get_service_client", return_value=svc):
            response = admin_client.post(
                "/api/rollover/preview",
                json={
                    "client_id": CLIENT_ID,
                    "from_year": FROM_YEAR,
                    "to_year": TO_YEAR,
                },
            )
        assert response.status_code == 400
        assert str(TO_YEAR) in response.json()["detail"]

    def test_rollover_preview_requires_auth(self, unauthenticated_client):
        """Unauthenticated request returns 401."""
        response = unauthenticated_client.post(
            "/api/rollover/preview",
            json={"client_id": CLIENT_ID, "from_year": FROM_YEAR, "to_year": TO_YEAR},
        )
        assert response.status_code == 401


# ══════════════════════════════════════════════════════════════════════════
# API endpoint tests: POST /api/rollover/confirm
# ══════════════════════════════════════════════════════════════════════════


class TestRolloverConfirmEndpoint:
    """Tests for POST /api/rollover/confirm."""

    def _make_confirm_svc(self, to_year_has_docs: bool = False, items_created: int = 2):
        bs_clfs = [
            {
                "line_item_id": "item-bs-001",
                "cma_field_name": "Fixed Assets",
                "broad_classification": "fixed_assets",
                "is_doubt": False,
            }
        ]
        bs_items = [{"id": "item-bs-001", "description": "Fixed Assets", "amount": 500.0}]
        li_tbl = _items_table(bs_items)
        li_tbl.insert.return_value.execute.return_value.data = [{}] * items_created
        return _make_service(
            documents=_year_aware_docs_table(to_year_has_docs=to_year_has_docs),
            extracted_line_items=li_tbl,
            classifications=_classifications_table(bs_clfs),
            cma_report_history=_history_table(),
        )

    def test_rollover_adds_new_financial_year_to_client(self, admin_client):
        """Confirm creates a new document for to_year and returns document_ids."""
        svc = self._make_confirm_svc()
        with patch("app.routers.rollover.get_service_client", return_value=svc):
            response = admin_client.post(
                "/api/rollover/confirm",
                json={
                    "client_id": CLIENT_ID,
                    "from_year": FROM_YEAR,
                    "to_year": TO_YEAR,
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert len(data["document_ids"]) == 1

    def test_rollover_confirm_executes_and_logs(self, admin_client):
        """Confirm calls audit_service.log_action with rollover_confirmed."""
        svc = self._make_confirm_svc()
        with patch("app.routers.rollover.get_service_client", return_value=svc), patch(
            "app.services.rollover_service.audit_service.log_action"
        ) as mock_log:
            response = admin_client.post(
                "/api/rollover/confirm",
                json={
                    "client_id": CLIENT_ID,
                    "from_year": FROM_YEAR,
                    "to_year": TO_YEAR,
                },
            )
        assert response.status_code == 200
        mock_log.assert_called_once()
        assert mock_log.call_args[0][2] == "rollover_confirmed"

    def test_rollover_rejects_duplicate_year(self, admin_client):
        """Confirm returns 400 when to_year already has documents."""
        svc = self._make_confirm_svc(to_year_has_docs=True)
        with patch("app.routers.rollover.get_service_client", return_value=svc):
            response = admin_client.post(
                "/api/rollover/confirm",
                json={
                    "client_id": CLIENT_ID,
                    "from_year": FROM_YEAR,
                    "to_year": TO_YEAR,
                },
            )
        assert response.status_code == 400
        assert str(TO_YEAR) in response.json()["detail"]

    def test_rollover_confirm_fails_if_doc_insert_returns_empty(self, admin_client):
        """500 when document insert returns no data."""
        docs_tbl = _year_aware_docs_table(to_year_has_docs=False)
        docs_tbl.insert.return_value.execute.return_value.data = []  # insert fails
        bs_items = [{"id": "item-bs-001", "description": "Fixed Assets", "amount": 500.0}]
        bs_clfs = [
            {
                "line_item_id": "item-bs-001",
                "cma_field_name": "Fixed Assets",
                "broad_classification": "fixed_assets",
                "is_doubt": False,
            }
        ]
        svc = _make_service(
            documents=docs_tbl,
            extracted_line_items=_items_table(bs_items),
            classifications=_classifications_table(bs_clfs),
        )
        with patch("app.routers.rollover.get_service_client", return_value=svc):
            response = admin_client.post(
                "/api/rollover/confirm",
                json={"client_id": CLIENT_ID, "from_year": FROM_YEAR, "to_year": TO_YEAR},
            )
        assert response.status_code == 500

    def test_rollover_requires_source_year_to_exist(self, admin_client):
        """Confirm returns 404 when from_year has no documents."""
        # Both years return empty to simulate missing from_year
        inner_eq_mock = MagicMock()
        inner_eq_mock.eq.return_value.execute.return_value.data = []
        docs_tbl = MagicMock()
        docs_tbl.select.return_value.eq.return_value = inner_eq_mock
        svc = _make_service(documents=docs_tbl)
        with patch("app.routers.rollover.get_service_client", return_value=svc):
            response = admin_client.post(
                "/api/rollover/confirm",
                json={
                    "client_id": CLIENT_ID,
                    "from_year": FROM_YEAR,
                    "to_year": TO_YEAR,
                },
            )
        assert response.status_code == 404
        assert str(FROM_YEAR) in response.json()["detail"]

    def test_employee_cannot_confirm_rollover_403(self, employee_client):
        """Employee (non-admin) calling confirm must receive 403 Forbidden."""
        response = employee_client.post(
            "/api/rollover/confirm",
            json={"client_id": CLIENT_ID, "from_year": FROM_YEAR, "to_year": TO_YEAR},
        )
        assert response.status_code == 403
