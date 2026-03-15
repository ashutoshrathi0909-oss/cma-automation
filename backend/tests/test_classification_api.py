"""Phase 5E: Classification API endpoint tests.

TDD — RED phase: written BEFORE implementation.

Coverage target: 100% on routers/classification.py

Endpoints:
  POST   /api/documents/{doc_id}/classify       — trigger classification (202)
  GET    /api/documents/{doc_id}/classifications — get results
  GET    /api/documents/{doc_id}/doubts          — get doubt items only
  POST   /api/classifications/{id}/approve       — approve single
  POST   /api/classifications/{id}/correct       — correct single
  POST   /api/documents/{doc_id}/bulk-approve    — bulk approve
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_current_user
from app.models.schemas import UserProfile


# ── Test constants ─────────────────────────────────────────────────────────────

DOC_ID = "doc-uuid-1234"
CLIENT_ID = "client-uuid-abcd"
CLF_ID = "clf-uuid-0001"
ITEM_ID = "item-uuid-5678"
TASK_ID = "arq:job:test-classify-123"

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

OTHER_EMPLOYEE_USER = UserProfile(
    id="other-employee-uuid-9999",
    full_name="Other Employee",
    role="employee",
    created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
)

SAMPLE_DOCUMENT_VERIFIED = {
    "id": DOC_ID,
    "client_id": CLIENT_ID,
    "file_name": "financials.xlsx",
    "file_path": f"{CLIENT_ID}/test-file.xlsx",
    "file_type": "xlsx",
    "document_type": "profit_and_loss",
    "financial_year": 2024,
    "nature": "audited",
    "extraction_status": "verified",
    "uploaded_by": "admin-uuid-0001",
    "uploaded_at": "2025-01-01T00:00:00+00:00",
}

SAMPLE_DOCUMENT_NOT_VERIFIED = {
    **SAMPLE_DOCUMENT_VERIFIED,
    "extraction_status": "extracted",
}

SAMPLE_CLASSIFICATION = {
    "id": CLF_ID,
    "line_item_id": ITEM_ID,
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

SAMPLE_DOUBT_CLASSIFICATION = {
    **SAMPLE_CLASSIFICATION,
    "id": "clf-doubt-0002",
    "cma_field_name": None,
    "is_doubt": True,
    "doubt_reason": "Ambiguous entry",
    "status": "needs_review",
    "confidence_score": 0.55,
}

SAMPLE_LINE_ITEM = {
    "id": ITEM_ID,
    "document_id": DOC_ID,
    "description": "Wages and Salaries",
    "amount": 500000.0,
    "section": "expenses",
    "raw_text": "Wages and Salaries  5,00,000",
    "is_verified": True,
}


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clear_overrides():
    """Clear dependency overrides after each test."""
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
def other_employee_client():
    app.dependency_overrides[get_current_user] = lambda: OTHER_EMPLOYEE_USER
    return TestClient(app)


def _make_service():
    return MagicMock()


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/documents/{doc_id}/classify — trigger classification
# ══════════════════════════════════════════════════════════════════════════════


class TestTriggerClassification:
    """Tests for POST /api/documents/{document_id}/classify"""

    def test_trigger_returns_202_with_task_id(self, admin_client):
        """Trigger returns 202 Accepted with task_id and document_id."""
        mock_service = _make_service()
        # require_verified_document: document fetch
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT_VERIFIED

        mock_job = MagicMock()
        mock_job.job_id = TASK_ID
        mock_pool = AsyncMock()
        mock_pool.enqueue_job = AsyncMock(return_value=mock_job)

        with patch(
            "app.routers.extraction.get_service_client", return_value=mock_service
        ), patch(
            "app.routers.classification.create_pool", return_value=mock_pool
        ):
            response = admin_client.post(f"/api/documents/{DOC_ID}/classify")

        assert response.status_code == 202
        data = response.json()
        assert data["task_id"] == TASK_ID
        assert data["document_id"] == DOC_ID
        assert "message" in data

    def test_trigger_requires_verified_status_403(self, admin_client):
        """Non-verified document returns 403."""
        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT_NOT_VERIFIED

        with patch(
            "app.routers.extraction.get_service_client", return_value=mock_service
        ):
            response = admin_client.post(f"/api/documents/{DOC_ID}/classify")

        assert response.status_code == 403

    def test_trigger_document_not_found_404(self, admin_client):
        """Non-existent document returns 404."""
        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None

        with patch(
            "app.routers.extraction.get_service_client", return_value=mock_service
        ):
            response = admin_client.post(f"/api/documents/nonexistent/classify")

        assert response.status_code == 404

    def test_trigger_requires_auth_401(self):
        """Unauthenticated request returns 401."""
        client = TestClient(app)
        response = client.post(f"/api/documents/{DOC_ID}/classify")
        assert response.status_code == 401

    def test_trigger_forbidden_for_other_user(self, other_employee_client):
        """Employee cannot trigger classification on another user's document."""
        mock_service = _make_service()
        # Document uploaded by admin-uuid-0001, not other-employee-uuid-9999
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT_VERIFIED

        with patch(
            "app.routers.extraction.get_service_client", return_value=mock_service
        ):
            response = other_employee_client.post(f"/api/documents/{DOC_ID}/classify")

        assert response.status_code == 403

    def test_trigger_employee_can_classify_own_document(self, employee_client):
        """Employee can trigger classification on their own document."""
        employee_doc = {**SAMPLE_DOCUMENT_VERIFIED, "uploaded_by": "employee-uuid-0001"}
        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = employee_doc

        mock_job = MagicMock()
        mock_job.job_id = TASK_ID
        mock_pool = AsyncMock()
        mock_pool.enqueue_job = AsyncMock(return_value=mock_job)

        with patch(
            "app.routers.extraction.get_service_client", return_value=mock_service
        ), patch(
            "app.routers.classification.create_pool", return_value=mock_pool
        ):
            response = employee_client.post(f"/api/documents/{DOC_ID}/classify")

        assert response.status_code == 202


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/documents/{doc_id}/classifications
# ══════════════════════════════════════════════════════════════════════════════


class TestGetClassifications:
    """Tests for GET /api/documents/{document_id}/classifications"""

    def test_get_classifications_returns_list(self, admin_client):
        """Returns list of classifications for a document."""
        mock_service = _make_service()
        # Ownership check: _get_owned_document uses .select().eq().single().execute()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT_VERIFIED
        # _get_document_item_ids: .select().eq().execute() (no .single())
        mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{"id": ITEM_ID}]
        # Classifications query: .select().in_().order().execute()
        mock_service.table.return_value.select.return_value.in_.return_value.order.return_value.execute.return_value.data = [SAMPLE_CLASSIFICATION]

        with patch(
            "app.routers.extraction.get_service_client", return_value=mock_service
        ), patch(
            "app.routers.classification.get_service_client", return_value=mock_service
        ):
            response = admin_client.get(f"/api/documents/{DOC_ID}/classifications")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == CLF_ID

    def test_get_classifications_empty_list(self, admin_client):
        """Returns empty list when no line items (and thus no classifications) exist."""
        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT_VERIFIED
        # No line items → returns [] early without querying classifications
        mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        with patch(
            "app.routers.extraction.get_service_client", return_value=mock_service
        ), patch(
            "app.routers.classification.get_service_client", return_value=mock_service
        ):
            response = admin_client.get(f"/api/documents/{DOC_ID}/classifications")

        assert response.status_code == 200
        assert response.json() == []

    def test_get_classifications_requires_auth_401(self):
        """Unauthenticated request returns 401."""
        client = TestClient(app)
        response = client.get(f"/api/documents/{DOC_ID}/classifications")
        assert response.status_code == 401

    def test_get_classifications_document_not_found_404(self, admin_client):
        """Returns 404 when document not found."""
        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None

        with patch(
            "app.routers.extraction.get_service_client", return_value=mock_service
        ), patch(
            "app.routers.classification.get_service_client", return_value=mock_service
        ):
            response = admin_client.get(f"/api/documents/nonexistent/classifications")

        assert response.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/documents/{doc_id}/doubts
# ══════════════════════════════════════════════════════════════════════════════


class TestGetDoubts:
    """Tests for GET /api/documents/{document_id}/doubts"""

    def test_get_doubts_returns_only_doubt_items(self, admin_client):
        """Returns only is_doubt=True items."""
        mock_service = _make_service()
        # Ownership check: .select().eq().single().execute()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT_VERIFIED
        # _get_document_item_ids: .select().eq().execute() (no .single())
        mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{"id": ITEM_ID}]
        # Doubts query: .select().in_().eq().order().execute()
        mock_service.table.return_value.select.return_value.in_.return_value.eq.return_value.order.return_value.execute.return_value.data = [SAMPLE_DOUBT_CLASSIFICATION]

        with patch(
            "app.routers.extraction.get_service_client", return_value=mock_service
        ), patch(
            "app.routers.classification.get_service_client", return_value=mock_service
        ):
            response = admin_client.get(f"/api/documents/{DOC_ID}/doubts")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["is_doubt"] is True

    def test_get_doubts_empty_when_none(self, admin_client):
        """Returns empty list when no line items (and thus no doubts) exist."""
        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT_VERIFIED
        # No line items → returns [] early without querying classifications
        mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        with patch(
            "app.routers.extraction.get_service_client", return_value=mock_service
        ), patch(
            "app.routers.classification.get_service_client", return_value=mock_service
        ):
            response = admin_client.get(f"/api/documents/{DOC_ID}/doubts")

        assert response.status_code == 200
        assert response.json() == []

    def test_get_doubts_requires_auth_401(self):
        """Unauthenticated request returns 401."""
        client = TestClient(app)
        response = client.get(f"/api/documents/{DOC_ID}/doubts")
        assert response.status_code == 401


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/classifications/{id}/approve
# ══════════════════════════════════════════════════════════════════════════════


def _make_approval_service(clf_data=None, doc_data=None):
    """Build a per-table mock for approve/correct endpoints.

    The ownership chain is: classifications → extracted_line_items → documents.
    clients table is queried for industry_type.
    """
    if clf_data is None:
        clf_data = SAMPLE_CLASSIFICATION
    if doc_data is None:
        doc_data = SAMPLE_DOCUMENT_VERIFIED

    mock_service = MagicMock()

    def per_table(name):
        m = MagicMock()
        if name == "classifications":
            m.select.return_value.eq.return_value.single.return_value.execute.return_value.data = clf_data
        elif name == "extracted_line_items":
            m.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {"document_id": DOC_ID}
        elif name == "documents":
            m.select.return_value.eq.return_value.single.return_value.execute.return_value.data = doc_data
        elif name == "clients":
            m.select.return_value.eq.return_value.execute.return_value.data = [{"industry_type": "manufacturing"}]
        return m

    mock_service.table.side_effect = per_table
    return mock_service


class TestApproveClassification:
    """Tests for POST /api/classifications/{classification_id}/approve"""

    def test_approve_returns_updated_classification(self, admin_client):
        """Approve returns the updated classification with status=approved."""
        approved = {**SAMPLE_CLASSIFICATION, "status": "approved", "reviewed_by": "admin-uuid-0001"}
        mock_service = _make_approval_service()

        with patch(
            "app.routers.classification.get_service_client", return_value=mock_service
        ), patch(
            "app.routers.classification.LearningSystem"
        ) as mock_ls_cls:
            mock_ls = MagicMock()
            mock_ls_cls.return_value = mock_ls
            mock_ls.approve_classification.return_value = approved

            response = admin_client.post(
                f"/api/classifications/{CLF_ID}/approve",
                json={},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"

    def test_approve_classification_not_found_404(self, admin_client):
        """Returns 404 when classification not found."""
        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None

        with patch(
            "app.routers.classification.get_service_client", return_value=mock_service
        ):
            response = admin_client.post(
                f"/api/classifications/nonexistent/approve",
                json={},
            )

        assert response.status_code == 404

    def test_approve_requires_auth_401(self):
        """Unauthenticated request returns 401."""
        client = TestClient(app)
        response = client.post(f"/api/classifications/{CLF_ID}/approve", json={})
        assert response.status_code == 401

    def test_approve_forbidden_for_other_user(self, other_employee_client):
        """Employee cannot approve classification on another user's document."""
        # doc uploaded_by=admin-uuid-0001 ≠ other-employee-uuid-9999 → 403
        mock_service = _make_approval_service()

        with patch(
            "app.routers.classification.get_service_client", return_value=mock_service
        ):
            response = other_employee_client.post(
                f"/api/classifications/{CLF_ID}/approve",
                json={},
            )

        assert response.status_code == 403


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/classifications/{id}/correct
# ══════════════════════════════════════════════════════════════════════════════


class TestCorrectClassification:
    """Tests for POST /api/classifications/{classification_id}/correct"""

    VALID_CORRECTION = {
        "cma_field_name": "Salary and staff expenses",
        "cma_row": 67,
        "cma_sheet": "input_sheet",
        "broad_classification": "admin_expense",
        "correction_reason": "Service industry firm",
    }

    def test_correct_returns_updated_classification(self, admin_client):
        """Correct returns updated classification with new cma_field_name."""
        corrected = {
            **SAMPLE_CLASSIFICATION,
            "cma_field_name": "Salary and staff expenses",
            "cma_row": 67,
            "status": "corrected",
        }
        mock_service = _make_approval_service()

        with patch(
            "app.routers.classification.get_service_client", return_value=mock_service
        ), patch(
            "app.routers.classification.LearningSystem"
        ) as mock_ls_cls:
            mock_ls = MagicMock()
            mock_ls_cls.return_value = mock_ls
            mock_ls.correct_classification.return_value = corrected

            response = admin_client.post(
                f"/api/classifications/{CLF_ID}/correct",
                json=self.VALID_CORRECTION,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "corrected"
        assert data["cma_field_name"] == "Salary and staff expenses"

    def test_correct_forbidden_for_other_user(self, other_employee_client):
        """Employee cannot correct a classification on another user's document."""
        mock_service = _make_approval_service()

        with patch(
            "app.routers.classification.get_service_client", return_value=mock_service
        ):
            response = other_employee_client.post(
                f"/api/classifications/{CLF_ID}/correct",
                json=self.VALID_CORRECTION,
            )

        assert response.status_code == 403

    def test_correct_classification_not_found_404(self, admin_client):
        """Returns 404 when classification not found."""
        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None

        with patch(
            "app.routers.classification.get_service_client", return_value=mock_service
        ):
            response = admin_client.post(
                f"/api/classifications/nonexistent/correct",
                json=self.VALID_CORRECTION,
            )

        assert response.status_code == 404

    def test_correct_requires_auth_401(self):
        """Unauthenticated request returns 401."""
        client = TestClient(app)
        response = client.post(
            f"/api/classifications/{CLF_ID}/correct",
            json=self.VALID_CORRECTION,
        )
        assert response.status_code == 401

    def test_correct_rejects_missing_required_fields_422(self, admin_client):
        """Correct rejects request with missing required fields."""
        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_CLASSIFICATION

        with patch(
            "app.routers.classification.get_service_client", return_value=mock_service
        ):
            response = admin_client.post(
                f"/api/classifications/{CLF_ID}/correct",
                json={"correction_reason": "only reason, missing cma_field_name"},
            )

        assert response.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/documents/{doc_id}/bulk-approve
# ══════════════════════════════════════════════════════════════════════════════


class TestBulkApprove:
    """Tests for POST /api/documents/{document_id}/bulk-approve"""

    def test_bulk_approve_returns_count(self, admin_client):
        """Bulk approve returns approved_count and message."""
        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT_VERIFIED

        with patch(
            "app.routers.extraction.get_service_client", return_value=mock_service
        ), patch(
            "app.routers.classification.get_service_client", return_value=mock_service
        ), patch(
            "app.routers.classification.LearningSystem"
        ) as mock_ls_cls:
            mock_ls = MagicMock()
            mock_ls_cls.return_value = mock_ls
            mock_ls.bulk_approve.return_value = 5

            response = admin_client.post(
                f"/api/documents/{DOC_ID}/bulk-approve",
                json={},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["approved_count"] == 5
        assert "message" in data

    def test_bulk_approve_with_specific_ids(self, admin_client):
        """Bulk approve with specific classification_ids."""
        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT_VERIFIED

        with patch(
            "app.routers.extraction.get_service_client", return_value=mock_service
        ), patch(
            "app.routers.classification.get_service_client", return_value=mock_service
        ), patch(
            "app.routers.classification.LearningSystem"
        ) as mock_ls_cls:
            mock_ls = MagicMock()
            mock_ls_cls.return_value = mock_ls
            mock_ls.bulk_approve.return_value = 2

            response = admin_client.post(
                f"/api/documents/{DOC_ID}/bulk-approve",
                json={"classification_ids": ["clf-001", "clf-002"]},
            )

        assert response.status_code == 200
        assert response.json()["approved_count"] == 2

    def test_bulk_approve_requires_auth_401(self):
        """Unauthenticated request returns 401."""
        client = TestClient(app)
        response = client.post(
            f"/api/documents/{DOC_ID}/bulk-approve",
            json={},
        )
        assert response.status_code == 401

    def test_bulk_approve_document_not_found_404(self, admin_client):
        """Returns 404 when document not found."""
        mock_service = _make_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None

        with patch(
            "app.routers.extraction.get_service_client", return_value=mock_service
        ), patch(
            "app.routers.classification.get_service_client", return_value=mock_service
        ):
            response = admin_client.post(
                f"/api/documents/nonexistent/bulk-approve",
                json={},
            )

        assert response.status_code == 404
