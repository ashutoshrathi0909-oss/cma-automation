"""Phase 6: CMA Report API endpoint tests.

TDD — covers all new routes in routers/cma_reports.py.

Endpoints tested:
  POST   /api/clients/{client_id}/cma-reports        (201)
  GET    /api/clients/{client_id}/cma-reports        (200)
  GET    /api/cma-reports/{report_id}                (200)
  GET    /api/cma-reports/{report_id}/confidence     (200)
  GET    /api/cma-reports/{report_id}/classifications (200)
  GET    /api/cma-reports/{report_id}/audit          (200)
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_current_user
from app.main import app
from app.models.schemas import UserProfile

# ── Constants ──────────────────────────────────────────────────────────────

CLIENT_ID = "client-uuid-aaaa"
DOC_ID_1 = "doc-uuid-1111"
DOC_ID_2 = "doc-uuid-2222"
REPORT_ID = "report-uuid-rrrr"
ITEM_ID_1 = "item-uuid-1111"
ITEM_ID_2 = "item-uuid-2222"
CLF_ID_1 = "clf-uuid-cccc"
CLF_ID_2 = "clf-uuid-dddd"
AUDIT_ID = "audit-uuid-aaaa"

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

OTHER_USER = UserProfile(
    id="other-uuid-9999",
    full_name="Other User",
    role="employee",
    created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
)

SAMPLE_CLIENT = {"id": CLIENT_ID}

SAMPLE_DOC_VERIFIED = {
    "id": DOC_ID_1,
    "client_id": CLIENT_ID,
    "extraction_status": "verified",
}

SAMPLE_DOC_NOT_VERIFIED = {
    "id": DOC_ID_1,
    "client_id": CLIENT_ID,
    "extraction_status": "extracted",
}

SAMPLE_DOC_WRONG_CLIENT = {
    "id": DOC_ID_2,
    "client_id": "other-client-uuid",
    "extraction_status": "verified",
}

SAMPLE_REPORT = {
    "id": REPORT_ID,
    "client_id": CLIENT_ID,
    "title": "FY2024 CMA Report",
    "status": "draft",
    "document_ids": [DOC_ID_1],
    "created_by": EMPLOYEE_USER.id,
    "created_at": "2025-01-01T00:00:00+00:00",
    "updated_at": "2025-01-01T00:00:00+00:00",
}

SAMPLE_REPORT_OTHER_USER = {
    **SAMPLE_REPORT,
    "created_by": OTHER_USER.id,
}

SAMPLE_LINE_ITEMS = [{"id": ITEM_ID_1}, {"id": ITEM_ID_2}]

SAMPLE_CLASSIFICATION_HIGH = {
    "id": CLF_ID_1,
    "line_item_id": ITEM_ID_1,
    "client_id": CLIENT_ID,
    "cma_field_name": "Wages",
    "cma_sheet": "input_sheet",
    "cma_row": 45,
    "cma_column": "C",
    "broad_classification": "manufacturing_expense",
    "classification_method": "fuzzy_match",
    "confidence_score": 0.92,
    "fuzzy_match_score": 92.0,
    "is_doubt": False,
    "doubt_reason": None,
    "ai_best_guess": "Wages",
    "alternative_fields": [],
    "status": "auto_classified",
    "reviewed_by": None,
    "reviewed_at": None,
    "correction_note": None,
    "created_at": "2025-01-01T00:00:00+00:00",
}

SAMPLE_CLASSIFICATION_DOUBT = {
    **SAMPLE_CLASSIFICATION_HIGH,
    "id": CLF_ID_2,
    "line_item_id": ITEM_ID_2,
    "cma_field_name": None,
    "confidence_score": 0.45,
    "is_doubt": True,
    "doubt_reason": "Ambiguous entry",
    "status": "needs_review",
}

SAMPLE_CLASSIFICATION_APPROVED = {
    **SAMPLE_CLASSIFICATION_HIGH,
    "status": "approved",
}

SAMPLE_AUDIT_ENTRY = {
    "id": AUDIT_ID,
    "cma_report_id": REPORT_ID,
    "action": "approve_classification",
    "action_details": {"entity_type": "classification"},
    "performed_by": EMPLOYEE_USER.id,
    "performed_at": "2025-01-01T00:00:00+00:00",
}


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
def other_client():
    app.dependency_overrides[get_current_user] = lambda: OTHER_USER
    return TestClient(app)


# ── Mock factory ───────────────────────────────────────────────────────────


def _make_service(**table_mocks: MagicMock) -> MagicMock:
    """Return a mock service whose .table() side_effect dispatches per table name."""
    svc = MagicMock()
    svc.table.side_effect = lambda name: table_mocks.get(name, MagicMock())
    return svc


def _clients_table(data=SAMPLE_CLIENT):
    tbl = MagicMock()
    tbl.select.return_value.eq.return_value.single.return_value.execute.return_value.data = data
    return tbl


def _documents_table(data: list):
    tbl = MagicMock()
    tbl.select.return_value.in_.return_value.execute.return_value.data = data
    return tbl


def _cma_reports_table(single_data=None, list_data=None, insert_data=None):
    """Build a cma_reports table mock supporting select (single+list) and insert."""
    tbl = MagicMock()
    # single select (for _get_owned_report)
    tbl.select.return_value.eq.return_value.single.return_value.execute.return_value.data = single_data
    # list select (for list_cma_reports)
    tbl.select.return_value.eq.return_value.order.return_value.execute.return_value.data = (
        list_data or []
    )
    # insert
    if insert_data is not None:
        tbl.insert.return_value.execute.return_value.data = [insert_data]
    return tbl


def _items_table(data: list):
    tbl = MagicMock()
    tbl.select.return_value.in_.return_value.execute.return_value.data = data
    return tbl


def _classifications_table(data: list):
    tbl = MagicMock()
    tbl.select.return_value.in_.return_value.execute.return_value.data = data
    return tbl


def _history_table(data: list):
    tbl = MagicMock()
    tbl.select.return_value.eq.return_value.order.return_value.execute.return_value.data = data
    return tbl


# ══════════════════════════════════════════════════════════════════════════
# POST /api/clients/{client_id}/cma-reports
# ══════════════════════════════════════════════════════════════════════════


class TestCreateCMAReport:
    """Tests for POST /api/clients/{client_id}/cma-reports"""

    def test_create_cma_report_returns_201(self, employee_client):
        """Happy path: valid request creates a report and returns 201."""
        svc = _make_service(
            clients=_clients_table(SAMPLE_CLIENT),
            documents=_documents_table([SAMPLE_DOC_VERIFIED]),
            cma_reports=_cma_reports_table(insert_data=SAMPLE_REPORT),
        )

        with patch("app.routers.cma_reports.get_service_client", return_value=svc):
            response = employee_client.post(
                f"/api/clients/{CLIENT_ID}/cma-reports",
                json={"title": "FY2024 CMA Report", "document_ids": [DOC_ID_1]},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == REPORT_ID
        assert data["client_id"] == CLIENT_ID
        assert data["title"] == "FY2024 CMA Report"
        assert data["status"] == "draft"

    def test_create_report_owned_by_current_user(self, employee_client):
        """created_by is set to the requesting user's ID."""
        svc = _make_service(
            clients=_clients_table(SAMPLE_CLIENT),
            documents=_documents_table([SAMPLE_DOC_VERIFIED]),
            cma_reports=_cma_reports_table(insert_data=SAMPLE_REPORT),
        )

        with patch("app.routers.cma_reports.get_service_client", return_value=svc):
            response = employee_client.post(
                f"/api/clients/{CLIENT_ID}/cma-reports",
                json={"title": "Test", "document_ids": [DOC_ID_1]},
            )

        assert response.status_code == 201
        # Verify the insert payload contained created_by = employee user id
        reports_mock = svc.table.side_effect("cma_reports")
        insert_call = reports_mock.insert.call_args
        assert insert_call is not None
        payload = insert_call[0][0]
        assert payload["created_by"] == EMPLOYEE_USER.id

    def test_create_report_requires_at_least_one_document(self, employee_client):
        """Empty document_ids list is rejected by schema validation (422)."""
        with patch("app.routers.cma_reports.get_service_client", return_value=MagicMock()):
            response = employee_client.post(
                f"/api/clients/{CLIENT_ID}/cma-reports",
                json={"title": "Test", "document_ids": []},
            )

        assert response.status_code == 422

    def test_create_report_not_found_404_for_unknown_client(self, employee_client):
        """Non-existent client returns 404."""
        svc = _make_service(clients=_clients_table(None))

        with patch("app.routers.cma_reports.get_service_client", return_value=svc):
            response = employee_client.post(
                "/api/clients/nonexistent-client/cma-reports",
                json={"title": "Test", "document_ids": [DOC_ID_1]},
            )

        assert response.status_code == 404

    def test_create_report_validates_documents_belong_to_client(self, employee_client):
        """Documents that belong to a different client cause 400."""
        svc = _make_service(
            clients=_clients_table(SAMPLE_CLIENT),
            documents=_documents_table([SAMPLE_DOC_WRONG_CLIENT]),
        )

        with patch("app.routers.cma_reports.get_service_client", return_value=svc):
            response = employee_client.post(
                f"/api/clients/{CLIENT_ID}/cma-reports",
                json={"title": "Test", "document_ids": [DOC_ID_2]},
            )

        assert response.status_code == 400

    def test_create_report_rejects_unverified_documents(self, employee_client):
        """Documents with extraction_status != 'verified' cause 400."""
        svc = _make_service(
            clients=_clients_table(SAMPLE_CLIENT),
            documents=_documents_table([SAMPLE_DOC_NOT_VERIFIED]),
        )

        with patch("app.routers.cma_reports.get_service_client", return_value=svc):
            response = employee_client.post(
                f"/api/clients/{CLIENT_ID}/cma-reports",
                json={"title": "Test", "document_ids": [DOC_ID_1]},
            )

        assert response.status_code == 400
        assert "verified" in response.json()["detail"].lower()


# ══════════════════════════════════════════════════════════════════════════
# GET /api/clients/{client_id}/cma-reports
# ══════════════════════════════════════════════════════════════════════════


class TestListCMAReports:
    """Tests for GET /api/clients/{client_id}/cma-reports"""

    def test_list_cma_reports_for_client(self, employee_client):
        """Returns a list of CMA reports for the client."""
        svc = _make_service(
            clients=_clients_table(SAMPLE_CLIENT),
            cma_reports=_cma_reports_table(list_data=[SAMPLE_REPORT]),
        )

        with patch("app.routers.cma_reports.get_service_client", return_value=svc):
            response = employee_client.get(f"/api/clients/{CLIENT_ID}/cma-reports")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == REPORT_ID

    def test_list_returns_empty_when_no_reports(self, employee_client):
        """Empty list when no reports exist for a client."""
        svc = _make_service(
            clients=_clients_table(SAMPLE_CLIENT),
            cma_reports=_cma_reports_table(list_data=[]),
        )

        with patch("app.routers.cma_reports.get_service_client", return_value=svc):
            response = employee_client.get(f"/api/clients/{CLIENT_ID}/cma-reports")

        assert response.status_code == 200
        assert response.json() == []


# ══════════════════════════════════════════════════════════════════════════
# GET /api/cma-reports/{report_id}
# ══════════════════════════════════════════════════════════════════════════


class TestGetCMAReportDetail:
    """Tests for GET /api/cma-reports/{report_id}"""

    def test_get_cma_report_detail(self, employee_client):
        """Returns report detail for the report owner."""
        svc = _make_service(
            cma_reports=_cma_reports_table(single_data=SAMPLE_REPORT),
        )

        with patch("app.routers.cma_reports.get_service_client", return_value=svc):
            response = employee_client.get(f"/api/cma-reports/{REPORT_ID}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == REPORT_ID
        assert data["document_ids"] == [DOC_ID_1]

    def test_get_report_forbidden_for_non_owner(self, other_client):
        """Non-owner non-admin cannot access another user's report."""
        svc = _make_service(
            cma_reports=_cma_reports_table(single_data=SAMPLE_REPORT),
        )

        with patch("app.routers.cma_reports.get_service_client", return_value=svc):
            response = other_client.get(f"/api/cma-reports/{REPORT_ID}")

        assert response.status_code == 403

    def test_get_report_admin_can_access_any(self, admin_client):
        """Admin can access any report regardless of creator."""
        svc = _make_service(
            cma_reports=_cma_reports_table(single_data=SAMPLE_REPORT_OTHER_USER),
        )

        with patch("app.routers.cma_reports.get_service_client", return_value=svc):
            response = admin_client.get(f"/api/cma-reports/{REPORT_ID}")

        assert response.status_code == 200


# ══════════════════════════════════════════════════════════════════════════
# GET /api/cma-reports/{report_id}/confidence
# ══════════════════════════════════════════════════════════════════════════


class TestConfidenceData:
    """Tests for GET /api/cma-reports/{report_id}/confidence"""

    def test_get_confidence_data_returns_counts(self, employee_client):
        """Confidence counts are computed from the live classifications table."""
        clfs = [SAMPLE_CLASSIFICATION_HIGH, SAMPLE_CLASSIFICATION_DOUBT]
        svc = _make_service(
            cma_reports=_cma_reports_table(single_data=SAMPLE_REPORT),
            extracted_line_items=_items_table(SAMPLE_LINE_ITEMS),
            classifications=_classifications_table(clfs),
        )

        with patch("app.routers.cma_reports.get_service_client", return_value=svc):
            response = employee_client.get(f"/api/cma-reports/{REPORT_ID}/confidence")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["high_confidence"] == 1   # score 0.92 >= 0.85, not doubt
        assert data["needs_review"] == 1       # is_doubt == True
        assert data["approved"] == 0
        assert data["corrected"] == 0

    def test_confidence_data_updates_after_approval(self, employee_client):
        """approved count reflects classifications with status='approved'."""
        clfs = [SAMPLE_CLASSIFICATION_APPROVED, SAMPLE_CLASSIFICATION_DOUBT]
        svc = _make_service(
            cma_reports=_cma_reports_table(single_data=SAMPLE_REPORT),
            extracted_line_items=_items_table(SAMPLE_LINE_ITEMS),
            classifications=_classifications_table(clfs),
        )

        with patch("app.routers.cma_reports.get_service_client", return_value=svc):
            response = employee_client.get(f"/api/cma-reports/{REPORT_ID}/confidence")

        assert response.status_code == 200
        data = response.json()
        assert data["approved"] == 1
        assert data["needs_review"] == 1

    def test_confidence_returns_zeros_for_empty_report(self, employee_client):
        """Report with no linked documents returns all-zero counts."""
        empty_report = {**SAMPLE_REPORT, "document_ids": []}
        svc = _make_service(
            cma_reports=_cma_reports_table(single_data=empty_report),
        )

        with patch("app.routers.cma_reports.get_service_client", return_value=svc):
            response = employee_client.get(f"/api/cma-reports/{REPORT_ID}/confidence")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["approved"] == 0
