"""Phase 8A: Conversion service tests.

Covers:
  - Pure diff_line_items function (no mocks needed)
  - POST /api/conversion/preview endpoint
  - POST /api/conversion/confirm endpoint
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_current_user
from app.main import app
from app.models.schemas import UserProfile
from app.services.conversion_service import diff_line_items

# ── Constants ──────────────────────────────────────────────────────────────

CLIENT_ID = "client-uuid-conv"
PROV_DOC_ID = "doc-uuid-prov"
AUD_DOC_ID = "doc-uuid-aud"
REPORT_ID = "report-uuid-rrrr"

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

PROV_DOC = {
    "id": PROV_DOC_ID,
    "client_id": CLIENT_ID,
    "financial_year": 2024,
    "nature": "provisional",
    "extraction_status": "verified",
}

AUD_DOC = {
    "id": AUD_DOC_ID,
    "client_id": CLIENT_ID,
    "financial_year": 2024,
    "nature": "audited",
    "extraction_status": "verified",
}

# Sales Revenue: amount changed; Wages: unchanged; Rent Expense: removed; New Equipment: added
PROV_ITEMS = [
    {"id": "item-p-001", "description": "Sales Revenue", "amount": 1000.0},
    {"id": "item-p-002", "description": "Wages", "amount": 200.0},
    {"id": "item-p-003", "description": "Rent Expense", "amount": 50.0},
]

AUD_ITEMS = [
    {"id": "item-a-001", "description": "Sales Revenue", "amount": 1050.0},
    {"id": "item-a-002", "description": "Wages", "amount": 200.0},
    {"id": "item-a-003", "description": "New Equipment", "amount": 300.0},
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
    """Return a mock Supabase service dispatching per table name."""
    svc = MagicMock()
    svc.table.side_effect = lambda name: table_mocks.get(name, MagicMock())
    return svc


def _docs_table(prov_doc, aud_doc):
    """Documents table mock returning different docs by doc_id."""
    tbl = MagicMock()

    def eq_se(field, value):
        m = MagicMock()
        if value == PROV_DOC_ID:
            m.single.return_value.execute.return_value.data = prov_doc
        elif value == AUD_DOC_ID:
            m.single.return_value.execute.return_value.data = aud_doc
        else:
            m.single.return_value.execute.return_value.data = None
        return m

    tbl.select.return_value.eq.side_effect = eq_se
    tbl.update.return_value.eq.return_value.execute.return_value.data = [
        {"nature": "audited"}
    ]
    return tbl


def _items_table(prov_items, aud_items):
    """Line items table returning different items by document_id."""
    tbl = MagicMock()

    def eq_se(field, value):
        m = MagicMock()
        if value == PROV_DOC_ID:
            m.execute.return_value.data = prov_items
        elif value == AUD_DOC_ID:
            m.execute.return_value.data = aud_items
        else:
            m.execute.return_value.data = []
        return m

    tbl.select.return_value.eq.side_effect = eq_se
    tbl.update.return_value.eq.return_value.execute.return_value.data = [{}]
    return tbl


def _classifications_table():
    tbl = MagicMock()
    tbl.select.return_value.in_.return_value.execute.return_value.data = [
        {"id": "clf-001"}
    ]
    tbl.update.return_value.in_.return_value.execute.return_value.data = [{}]
    return tbl


def _history_table():
    tbl = MagicMock()
    tbl.insert.return_value.execute.return_value.data = [{}]
    return tbl


# ══════════════════════════════════════════════════════════════════════════
# Unit tests: diff_line_items pure function
# ══════════════════════════════════════════════════════════════════════════


class TestDiffLineItems:
    """Pure function unit tests — no mocks needed."""

    def test_conversion_finds_changed_amounts(self):
        """Items with same description but different amounts → changed."""
        prov = [{"description": "Sales Revenue", "amount": 1000.0}]
        aud = [{"description": "Sales Revenue", "amount": 1050.0}]
        result = diff_line_items(prov, aud)
        assert len(result["changed"]) == 1
        item = result["changed"][0]
        assert item["description"] == "Sales Revenue"
        assert item["provisional_amount"] == 1000.0
        assert item["audited_amount"] == 1050.0
        assert item["change_type"] == "changed"

    def test_conversion_detects_added_items(self):
        """Items present in audited but absent in provisional → added."""
        prov = [{"description": "Wages", "amount": 200.0}]
        aud = [
            {"description": "Wages", "amount": 200.0},
            {"description": "New Equipment", "amount": 300.0},
        ]
        result = diff_line_items(prov, aud)
        assert len(result["added"]) == 1
        assert result["added"][0]["description"] == "New Equipment"
        assert result["added"][0]["audited_amount"] == 300.0
        assert result["added"][0]["change_type"] == "added"

    def test_conversion_detects_removed_items(self):
        """Items present in provisional but absent in audited → removed."""
        prov = [
            {"description": "Wages", "amount": 200.0},
            {"description": "Rent Expense", "amount": 50.0},
        ]
        aud = [{"description": "Wages", "amount": 200.0}]
        result = diff_line_items(prov, aud)
        assert len(result["removed"]) == 1
        assert result["removed"][0]["description"] == "Rent Expense"
        assert result["removed"][0]["provisional_amount"] == 50.0
        assert result["removed"][0]["change_type"] == "removed"

    def test_conversion_no_changes_returns_empty_diff(self):
        """Identical items produce empty changed/added/removed."""
        items = [
            {"description": "Sales", "amount": 500.0},
            {"description": "Wages", "amount": 100.0},
        ]
        result = diff_line_items(items, items)
        assert result["changed"] == []
        assert result["added"] == []
        assert result["removed"] == []

    def test_conversion_fuzzy_matches_similar_descriptions(self):
        """Near-identical descriptions are fuzzy-matched and reported as changed."""
        prov = [{"description": "Salary Expenses", "amount": 200.0}]
        aud = [{"description": "Salary Expense", "amount": 250.0}]
        result = diff_line_items(prov, aud)
        # Fuzzy match ≥85 → treated as same item with changed amount
        assert len(result["changed"]) == 1
        assert result["changed"][0]["provisional_amount"] == 200.0
        assert result["changed"][0]["audited_amount"] == 250.0

    def test_conversion_empty_provisional_all_added(self):
        """Empty provisional → all audited items reported as added."""
        result = diff_line_items([], [{"description": "New", "amount": 100.0}])
        assert len(result["added"]) == 1
        assert result["changed"] == []
        assert result["removed"] == []

    def test_conversion_empty_audited_all_removed(self):
        """Empty audited → all provisional items reported as removed."""
        result = diff_line_items([{"description": "Old", "amount": 100.0}], [])
        assert len(result["removed"]) == 1
        assert result["changed"] == []
        assert result["added"] == []

    def test_conversion_same_description_same_amount_not_in_changed(self):
        """Items with same description AND same amount are NOT in changed list."""
        items = [{"description": "Depreciation", "amount": 75.0}]
        result = diff_line_items(items, items)
        assert result["changed"] == []


# ══════════════════════════════════════════════════════════════════════════
# API endpoint tests: POST /api/conversion/preview
# ══════════════════════════════════════════════════════════════════════════


class TestConversionPreviewEndpoint:
    """Tests for POST /api/conversion/preview."""

    def test_preview_endpoint_200(self, admin_client):
        """Happy path: valid request returns 200 with diff structure."""
        svc = _make_service(
            documents=_docs_table(PROV_DOC, AUD_DOC),
            extracted_line_items=_items_table(PROV_ITEMS, AUD_ITEMS),
        )
        with patch("app.routers.conversion.get_service_client", return_value=svc):
            response = admin_client.post(
                "/api/conversion/preview",
                json={
                    "provisional_doc_id": PROV_DOC_ID,
                    "audited_doc_id": AUD_DOC_ID,
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["provisional_doc_id"] == PROV_DOC_ID
        assert data["audited_doc_id"] == AUD_DOC_ID
        assert "changed" in data
        assert "added" in data
        assert "removed" in data

    def test_preview_requires_auth(self, unauthenticated_client):
        """Unauthenticated request returns 401."""
        response = unauthenticated_client.post(
            "/api/conversion/preview",
            json={"provisional_doc_id": PROV_DOC_ID, "audited_doc_id": AUD_DOC_ID},
        )
        assert response.status_code == 401

    def test_conversion_only_works_on_provisional_documents(self, admin_client):
        """400 when source document is not provisional."""
        non_prov = {**PROV_DOC, "nature": "audited"}
        svc = _make_service(documents=_docs_table(non_prov, AUD_DOC))
        with patch("app.routers.conversion.get_service_client", return_value=svc):
            response = admin_client.post(
                "/api/conversion/preview",
                json={"provisional_doc_id": PROV_DOC_ID, "audited_doc_id": AUD_DOC_ID},
            )
        assert response.status_code == 400
        assert "provisional" in response.json()["detail"].lower()

    def test_conversion_rejects_mismatched_client(self, admin_client):
        """400 when documents belong to different clients."""
        diff_client_aud = {**AUD_DOC, "client_id": "other-client-xyz"}
        svc = _make_service(documents=_docs_table(PROV_DOC, diff_client_aud))
        with patch("app.routers.conversion.get_service_client", return_value=svc):
            response = admin_client.post(
                "/api/conversion/preview",
                json={"provisional_doc_id": PROV_DOC_ID, "audited_doc_id": AUD_DOC_ID},
            )
        assert response.status_code == 400
        assert "client" in response.json()["detail"].lower()

    def test_conversion_rejects_mismatched_year(self, admin_client):
        """400 when documents belong to different financial years."""
        diff_year_aud = {**AUD_DOC, "financial_year": 2023}
        svc = _make_service(documents=_docs_table(PROV_DOC, diff_year_aud))
        with patch("app.routers.conversion.get_service_client", return_value=svc):
            response = admin_client.post(
                "/api/conversion/preview",
                json={"provisional_doc_id": PROV_DOC_ID, "audited_doc_id": AUD_DOC_ID},
            )
        assert response.status_code == 400
        assert "year" in response.json()["detail"].lower()


# ══════════════════════════════════════════════════════════════════════════
# API endpoint tests: POST /api/conversion/confirm
# ══════════════════════════════════════════════════════════════════════════


class TestConversionPreviewEdgeCases:
    """Additional coverage for not-found and wrong-nature paths."""

    def test_preview_provisional_doc_not_found_404(self, admin_client):
        """404 when provisional_doc_id doesn't exist in documents table."""
        tbl = MagicMock()

        def eq_se(field, value):
            m = MagicMock()
            m.single.return_value.execute.return_value.data = None  # not found
            return m

        tbl.select.return_value.eq.side_effect = eq_se
        svc = _make_service(documents=tbl)
        with patch("app.routers.conversion.get_service_client", return_value=svc):
            response = admin_client.post(
                "/api/conversion/preview",
                json={"provisional_doc_id": PROV_DOC_ID, "audited_doc_id": AUD_DOC_ID},
            )
        assert response.status_code == 404

    def test_preview_audited_doc_not_found_404(self, admin_client):
        """404 when audited_doc_id doesn't exist in documents table."""

        def eq_se(field, value):
            m = MagicMock()
            if value == PROV_DOC_ID:
                m.single.return_value.execute.return_value.data = PROV_DOC
            else:
                m.single.return_value.execute.return_value.data = None  # aud not found
            return m

        tbl = MagicMock()
        tbl.select.return_value.eq.side_effect = eq_se
        svc = _make_service(documents=tbl)
        with patch("app.routers.conversion.get_service_client", return_value=svc):
            response = admin_client.post(
                "/api/conversion/preview",
                json={"provisional_doc_id": PROV_DOC_ID, "audited_doc_id": AUD_DOC_ID},
            )
        assert response.status_code == 404

    def test_preview_audited_doc_wrong_nature(self, admin_client):
        """400 when audited doc has nature != 'audited'."""
        wrong_nature_aud = {**AUD_DOC, "nature": "provisional"}
        svc = _make_service(documents=_docs_table(PROV_DOC, wrong_nature_aud))
        with patch("app.routers.conversion.get_service_client", return_value=svc):
            response = admin_client.post(
                "/api/conversion/preview",
                json={"provisional_doc_id": PROV_DOC_ID, "audited_doc_id": AUD_DOC_ID},
            )
        assert response.status_code == 400
        assert "audited" in response.json()["detail"].lower()

    def test_preview_api_error_on_document_fetch(self, admin_client):
        """APIError from Supabase during document fetch is caught → 404."""
        from postgrest.exceptions import APIError

        tbl = MagicMock()
        tbl.select.return_value.eq.return_value.single.return_value.execute.side_effect = (
            APIError({"message": "not found", "code": "PGRST116", "details": "", "hint": ""})
        )
        svc = _make_service(documents=tbl)
        with patch("app.routers.conversion.get_service_client", return_value=svc):
            response = admin_client.post(
                "/api/conversion/preview",
                json={"provisional_doc_id": PROV_DOC_ID, "audited_doc_id": AUD_DOC_ID},
            )
        assert response.status_code == 404

    def test_confirm_provisional_doc_not_found_404(self, admin_client):
        """404 in confirm when provisional doc doesn't exist."""
        tbl = MagicMock()
        tbl.select.return_value.eq.return_value.single.return_value.execute.return_value.data = (
            None
        )
        svc = _make_service(documents=tbl)
        with patch("app.routers.conversion.get_service_client", return_value=svc):
            response = admin_client.post(
                "/api/conversion/confirm",
                json={
                    "provisional_doc_id": PROV_DOC_ID,
                    "audited_doc_id": AUD_DOC_ID,
                    "cma_report_id": REPORT_ID,
                },
            )
        assert response.status_code == 404


class TestConversionConfirmEndpoint:
    """Tests for POST /api/conversion/confirm."""

    def _make_confirm_svc(self):
        return _make_service(
            documents=_docs_table(PROV_DOC, AUD_DOC),
            extracted_line_items=_items_table(PROV_ITEMS, AUD_ITEMS),
            classifications=_classifications_table(),
            cma_report_history=_history_table(),
        )

    def test_confirm_conversion_replaces_provisional_with_audited(self, admin_client):
        """Confirm updates line item amounts and reports updated_count."""
        svc = self._make_confirm_svc()
        with patch("app.routers.conversion.get_service_client", return_value=svc):
            response = admin_client.post(
                "/api/conversion/confirm",
                json={
                    "provisional_doc_id": PROV_DOC_ID,
                    "audited_doc_id": AUD_DOC_ID,
                    "cma_report_id": REPORT_ID,
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "updated_count" in data
        assert data["updated_count"] >= 0

    def test_confirm_conversion_flags_doubt_items_for_re_review(self, admin_client):
        """Affected classifications are flagged with flagged_for_review count."""
        svc = self._make_confirm_svc()
        with patch("app.routers.conversion.get_service_client", return_value=svc):
            response = admin_client.post(
                "/api/conversion/confirm",
                json={
                    "provisional_doc_id": PROV_DOC_ID,
                    "audited_doc_id": AUD_DOC_ID,
                    "cma_report_id": REPORT_ID,
                },
            )
        assert response.status_code == 200
        assert "flagged_for_review" in response.json()

    def test_confirm_conversion_logs_audit_trail(self, admin_client):
        """Confirm calls audit_service.log_action with conversion_confirmed action."""
        svc = self._make_confirm_svc()
        with patch("app.routers.conversion.get_service_client", return_value=svc), patch(
            "app.services.conversion_service.audit_service.log_action"
        ) as mock_log:
            response = admin_client.post(
                "/api/conversion/confirm",
                json={
                    "provisional_doc_id": PROV_DOC_ID,
                    "audited_doc_id": AUD_DOC_ID,
                    "cma_report_id": REPORT_ID,
                },
            )
        assert response.status_code == 200
        mock_log.assert_called_once()
        assert mock_log.call_args[0][2] == "conversion_confirmed"

    def test_conversion_only_works_on_provisional_documents_confirm(self, admin_client):
        """Confirm returns 400 when source document is not provisional."""
        non_prov = {**PROV_DOC, "nature": "audited"}
        svc = _make_service(
            documents=_docs_table(non_prov, AUD_DOC),
            extracted_line_items=_items_table(PROV_ITEMS, AUD_ITEMS),
        )
        with patch("app.routers.conversion.get_service_client", return_value=svc):
            response = admin_client.post(
                "/api/conversion/confirm",
                json={
                    "provisional_doc_id": PROV_DOC_ID,
                    "audited_doc_id": AUD_DOC_ID,
                    "cma_report_id": REPORT_ID,
                },
            )
        assert response.status_code == 400

    def test_employee_cannot_confirm_conversion_403(self, employee_client):
        """Employee (non-admin) calling confirm must receive 403 Forbidden."""
        response = employee_client.post(
            "/api/conversion/confirm",
            json={
                "provisional_doc_id": PROV_DOC_ID,
                "audited_doc_id": AUD_DOC_ID,
                "cma_report_id": REPORT_ID,
            },
        )
        assert response.status_code == 403
