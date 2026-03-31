"""
Phase 4B: Extraction API + ARQ worker tests.

TDD workflow — RED → GREEN → REFACTOR.
All tests written BEFORE the implementation.

Coverage targets:
  - routers/extraction.py: trigger, items, edit, verify
  - routers/tasks.py: task status polling
  - workers/extraction_tasks.py: run_extraction task
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch, call

from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_current_user, get_service_client
from app.models.schemas import UserProfile


# ── Helpers ────────────────────────────────────────────────────────────────────

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

DOC_ID = "doc-uuid-1234"
ITEM_ID = "item-uuid-5678"
TASK_ID = "arq:job:test123"
CLIENT_ID = "client-uuid-abcd"

SAMPLE_DOCUMENT = {
    "id": DOC_ID,
    "client_id": CLIENT_ID,
    "file_name": "financials.xlsx",
    "file_path": f"{CLIENT_ID}/test-file.xlsx",
    "file_type": "xlsx",
    "document_type": "profit_and_loss",
    "financial_year": 2024,
    "nature": "audited",
    "extraction_status": "pending",
    "uploaded_by": "admin-uuid-0001",
    "uploaded_at": "2025-01-01T00:00:00+00:00",
}

# Document owned by the employee user
EMPLOYEE_DOCUMENT = {
    **SAMPLE_DOCUMENT,
    "uploaded_by": "employee-uuid-0001",
}

SAMPLE_DOCUMENT_EXTRACTED = {
    **SAMPLE_DOCUMENT,
    "extraction_status": "extracted",
}

SAMPLE_DOCUMENT_VERIFIED = {
    **SAMPLE_DOCUMENT,
    "extraction_status": "verified",
}

SAMPLE_LINE_ITEM = {
    "id": ITEM_ID,
    "document_id": DOC_ID,
    "description": "Salaries & Wages",
    "amount": 500000.0,
    "section": "expenses",
    "raw_text": "Salaries & Wages  5,00,000",
    "is_verified": False,
}

SAMPLE_LINE_ITEM_VERIFIED = {
    **SAMPLE_LINE_ITEM,
    "is_verified": True,
}


def _make_admin_client():
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    return TestClient(app)


def _make_employee_client():
    app.dependency_overrides[get_current_user] = lambda: EMPLOYEE_USER
    return TestClient(app)


def _make_other_employee_client():
    app.dependency_overrides[get_current_user] = lambda: OTHER_EMPLOYEE_USER
    return TestClient(app)


def _make_mock_service():
    """Return a fully-spec'd mock Supabase service client."""
    service = MagicMock()
    return service


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clear_overrides():
    """Ensure dependency overrides are cleared after each test."""
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


# ═══════════════════════════════════════════════════════════════════════════════
# Trigger Extraction — POST /{document_id}/extract
# ═══════════════════════════════════════════════════════════════════════════════


class TestTriggerExtraction:
    """Tests for POST /api/documents/{document_id}/extract"""

    def _make_service_for_trigger(self, doc_data):
        """Build mock service that handles both the ownership fetch and atomic update."""
        mock_service = _make_mock_service()
        # _get_owned_document: .select().eq().single().execute().data
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = doc_data
        # Atomic update: .update().eq().in_().execute().data — returns non-empty list on win
        mock_service.table.return_value.update.return_value.eq.return_value.in_.return_value.execute.return_value.data = [
            {**doc_data, "extraction_status": "processing"}
        ]
        return mock_service

    def test_trigger_extraction_enqueues_task(self, admin_client):
        """POST /{id}/extract returns 202 with task_id when document is pending."""
        mock_service = self._make_service_for_trigger(SAMPLE_DOCUMENT)

        mock_job = MagicMock()
        mock_job.job_id = TASK_ID
        mock_pool = AsyncMock()
        mock_pool.enqueue_job = AsyncMock(return_value=mock_job)

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.create_pool", return_value=mock_pool):
            response = admin_client.post(f"/api/documents/{DOC_ID}/extract")

        assert response.status_code == 202
        data = response.json()
        assert data["task_id"] == TASK_ID
        assert data["document_id"] == DOC_ID
        assert "message" in data

    def test_trigger_extraction_document_not_found_404(self, admin_client):
        """POST /{id}/extract returns 404 when document does not exist."""
        mock_service = _make_mock_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service):
            response = admin_client.post(f"/api/documents/nonexistent-id/extract")

        assert response.status_code == 404

    def test_trigger_extraction_requires_auth_401(self, client):
        """POST /{id}/extract returns 401 when not authenticated."""
        response = client.post(f"/api/documents/{DOC_ID}/extract")
        assert response.status_code == 401

    def test_trigger_extraction_already_processing_409(self, admin_client):
        """POST /{id}/extract returns 409 when document is already processing."""
        processing_doc = {**SAMPLE_DOCUMENT, "extraction_status": "processing"}
        mock_service = _make_mock_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = processing_doc

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service):
            response = admin_client.post(f"/api/documents/{DOC_ID}/extract")

        assert response.status_code == 409

    def test_trigger_extraction_failed_status_allowed(self, admin_client):
        """POST /{id}/extract allows re-triggering on failed documents."""
        failed_doc = {**SAMPLE_DOCUMENT, "extraction_status": "failed"}
        mock_service = self._make_service_for_trigger(failed_doc)

        mock_job = MagicMock()
        mock_job.job_id = TASK_ID
        mock_pool = AsyncMock()
        mock_pool.enqueue_job = AsyncMock(return_value=mock_job)

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.create_pool", return_value=mock_pool):
            response = admin_client.post(f"/api/documents/{DOC_ID}/extract")

        assert response.status_code == 202

    def test_trigger_extraction_race_condition_returns_409(self, admin_client):
        """POST /{id}/extract returns 409 when atomic update finds no rows (race lost)."""
        mock_service = _make_mock_service()
        # Initial fetch shows pending
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT
        # Atomic update returns empty (another request already won)
        mock_service.table.return_value.update.return_value.eq.return_value.in_.return_value.execute.return_value.data = []

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service):
            response = admin_client.post(f"/api/documents/{DOC_ID}/extract")

        assert response.status_code == 409

    def test_trigger_extraction_forbidden_for_other_user_document(self, other_employee_client):
        """Employee cannot trigger extraction on a document uploaded by another user."""
        mock_service = _make_mock_service()
        # Document belongs to admin-uuid-0001, not other-employee-uuid-9999
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service):
            response = other_employee_client.post(f"/api/documents/{DOC_ID}/extract")

        assert response.status_code == 403

    def test_trigger_extraction_admin_can_access_any_document(self, admin_client):
        """Admin can trigger extraction on any document regardless of who uploaded it."""
        # Document was uploaded by an employee, admin should still be able to trigger
        employee_doc = {**SAMPLE_DOCUMENT, "uploaded_by": "employee-uuid-0001"}
        mock_service = _make_mock_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = employee_doc
        mock_service.table.return_value.update.return_value.eq.return_value.in_.return_value.execute.return_value.data = [
            {**employee_doc, "extraction_status": "processing"}
        ]

        mock_job = MagicMock()
        mock_job.job_id = TASK_ID
        mock_pool = AsyncMock()
        mock_pool.enqueue_job = AsyncMock(return_value=mock_job)

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.create_pool", return_value=mock_pool):
            response = admin_client.post(f"/api/documents/{DOC_ID}/extract")

        assert response.status_code == 202

    def test_trigger_extraction_employee_can_access_own_document(self, employee_client):
        """Employee can trigger extraction on their own document."""
        mock_service = _make_mock_service()
        # EMPLOYEE_DOCUMENT has uploaded_by=employee-uuid-0001
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = EMPLOYEE_DOCUMENT
        mock_service.table.return_value.update.return_value.eq.return_value.in_.return_value.execute.return_value.data = [
            {**EMPLOYEE_DOCUMENT, "extraction_status": "processing"}
        ]

        mock_job = MagicMock()
        mock_job.job_id = TASK_ID
        mock_pool = AsyncMock()
        mock_pool.enqueue_job = AsyncMock(return_value=mock_job)

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.create_pool", return_value=mock_pool):
            response = employee_client.post(f"/api/documents/{DOC_ID}/extract")

        assert response.status_code == 202


# ═══════════════════════════════════════════════════════════════════════════════
# Task Status — GET /api/tasks/{task_id}
# ═══════════════════════════════════════════════════════════════════════════════


class TestTaskStatus:
    """Tests for GET /api/tasks/{task_id}"""

    def test_task_status_queued(self, admin_client):
        """GET /api/tasks/{id} returns status=queued for a queued ARQ job."""
        from arq.jobs import JobStatus

        mock_job = AsyncMock()
        mock_job.status = AsyncMock(return_value=JobStatus.queued)

        mock_pool = AsyncMock()
        mock_pool.__aenter__ = AsyncMock(return_value=mock_pool)
        mock_pool.__aexit__ = AsyncMock(return_value=None)

        with patch("app.routers.tasks.create_pool", return_value=mock_pool), \
             patch("app.routers.tasks.Job", return_value=mock_job):
            response = admin_client.get(f"/api/tasks/{TASK_ID}")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == TASK_ID
        assert data["status"] == "queued"

    def test_task_status_in_progress(self, admin_client):
        """GET /api/tasks/{id} returns status=in_progress for a running ARQ job."""
        from arq.jobs import JobStatus

        mock_job = AsyncMock()
        mock_job.status = AsyncMock(return_value=JobStatus.in_progress)

        mock_pool = AsyncMock()

        with patch("app.routers.tasks.create_pool", return_value=mock_pool), \
             patch("app.routers.tasks.Job", return_value=mock_job):
            response = admin_client.get(f"/api/tasks/{TASK_ID}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"

    def test_task_status_complete(self, admin_client):
        """GET /api/tasks/{id} returns status=complete for a finished ARQ job."""
        from arq.jobs import JobStatus

        mock_job = AsyncMock()
        mock_job.status = AsyncMock(return_value=JobStatus.complete)

        mock_pool = AsyncMock()

        with patch("app.routers.tasks.create_pool", return_value=mock_pool), \
             patch("app.routers.tasks.Job", return_value=mock_job):
            response = admin_client.get(f"/api/tasks/{TASK_ID}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "complete"

    def test_task_status_not_found(self, admin_client):
        """GET /api/tasks/{id} returns status=not_found for unknown task_id."""
        from arq.jobs import JobStatus

        mock_job = AsyncMock()
        mock_job.status = AsyncMock(return_value=JobStatus.not_found)

        mock_pool = AsyncMock()

        with patch("app.routers.tasks.create_pool", return_value=mock_pool), \
             patch("app.routers.tasks.Job", return_value=mock_job):
            response = admin_client.get(f"/api/tasks/unknown-task-id")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_found"

    def test_task_status_requires_auth_401(self, client):
        """GET /api/tasks/{id} returns 401 when not authenticated."""
        response = client.get(f"/api/tasks/{TASK_ID}")
        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# Extraction Worker Task (unit tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestExtractionWorkerTask:
    """Unit tests for the run_extraction ARQ worker task."""

    @pytest.mark.asyncio
    async def test_extraction_saves_line_items_to_db(self):
        """run_extraction saves extracted line items to extracted_line_items table."""
        from app.services.extraction._types import LineItem
        from app.workers.extraction_tasks import run_extraction

        mock_items = [
            LineItem(description="Revenue", amount=1000000.0, section="income", raw_text="Revenue 10,00,000"),
            LineItem(description="Salaries", amount=500000.0, section="expenses", raw_text="Salaries 5,00,000"),
        ]

        mock_service = _make_mock_service()
        # Simulate document fetch
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT
        # Simulate storage download
        mock_service.storage.from_.return_value.download.return_value = b"fake-file-content"
        # Simulate status updates (update calls return something truthy)
        mock_service.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [SAMPLE_DOCUMENT]
        # Simulate insert
        mock_service.table.return_value.insert.return_value.execute.return_value.data = [SAMPLE_LINE_ITEM]
        # Simulate delete (idempotency)
        mock_service.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = []

        ctx = {}

        with patch("app.workers.extraction_tasks.get_service_client", return_value=mock_service), \
             patch("app.workers.extraction_tasks.extract_document", return_value=mock_items):
            result = await run_extraction(ctx, DOC_ID)

        assert result["document_id"] == DOC_ID
        assert result["item_count"] == 2
        assert result["status"] == "extracted"

    @pytest.mark.asyncio
    async def test_extraction_updates_document_status(self):
        """run_extraction updates status to 'extracted' on success (worker no longer sets 'processing')."""
        from app.services.extraction._types import LineItem
        from app.workers.extraction_tasks import run_extraction

        mock_items = [
            LineItem(description="Revenue", amount=100.0, section="income", raw_text="Revenue 100"),
        ]

        mock_service = _make_mock_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT
        mock_service.storage.from_.return_value.download.return_value = b"fake-bytes"
        mock_service.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [SAMPLE_DOCUMENT]
        mock_service.table.return_value.insert.return_value.execute.return_value.data = [SAMPLE_LINE_ITEM]
        mock_service.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = []

        ctx = {}

        with patch("app.workers.extraction_tasks.get_service_client", return_value=mock_service), \
             patch("app.workers.extraction_tasks.extract_document", return_value=mock_items):
            await run_extraction(ctx, DOC_ID)

        # Verify 'extracted' status was set (worker only sets extracted on success)
        update_calls = mock_service.table.return_value.update.call_args_list
        called_statuses = [c[0][0].get("extraction_status") for c in update_calls if c[0]]
        assert "extracted" in called_statuses
        # Worker should NOT set 'processing' — the API handler does that atomically
        assert "processing" not in called_statuses

    @pytest.mark.asyncio
    async def test_extraction_deletes_existing_items_for_idempotency(self):
        """run_extraction deletes existing line items before inserting new ones."""
        from app.services.extraction._types import LineItem
        from app.workers.extraction_tasks import run_extraction

        mock_items = [
            LineItem(description="Revenue", amount=100.0, section="income", raw_text="Revenue 100"),
        ]

        mock_service = _make_mock_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT
        mock_service.storage.from_.return_value.download.return_value = b"fake-bytes"
        mock_service.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [SAMPLE_DOCUMENT]
        mock_service.table.return_value.insert.return_value.execute.return_value.data = [SAMPLE_LINE_ITEM]
        mock_service.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = []

        ctx = {}

        with patch("app.workers.extraction_tasks.get_service_client", return_value=mock_service), \
             patch("app.workers.extraction_tasks.extract_document", return_value=mock_items):
            await run_extraction(ctx, DOC_ID)

        # Verify delete was called for idempotency
        delete_calls = mock_service.table.return_value.delete.call_args_list
        assert len(delete_calls) >= 1

    @pytest.mark.asyncio
    async def test_extraction_failed_status_on_error(self):
        """run_extraction sets status=failed and re-raises on extraction error."""
        from app.workers.extraction_tasks import run_extraction
        from app.services.extraction.extractor_factory import ExtractionError

        mock_service = _make_mock_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT
        mock_service.storage.from_.return_value.download.return_value = b"bad-bytes"
        mock_service.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [SAMPLE_DOCUMENT]
        mock_service.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = []

        ctx = {}

        with patch("app.workers.extraction_tasks.get_service_client", return_value=mock_service), \
             patch("app.workers.extraction_tasks.extract_document", side_effect=ExtractionError("Corrupt file")):
            with pytest.raises(ExtractionError):
                await run_extraction(ctx, DOC_ID)

        # Verify failed status was set
        update_calls = mock_service.table.return_value.update.call_args_list
        called_statuses = [c[0][0].get("extraction_status") for c in update_calls if c[0]]
        assert "failed" in called_statuses

    @pytest.mark.asyncio
    async def test_extraction_document_not_found_raises(self):
        """run_extraction raises ValueError when document is not found in DB."""
        from app.workers.extraction_tasks import run_extraction

        mock_service = _make_mock_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None

        ctx = {}

        with patch("app.workers.extraction_tasks.get_service_client", return_value=mock_service):
            with pytest.raises(ValueError, match="Document not found"):
                await run_extraction(ctx, "nonexistent-id")


# ═══════════════════════════════════════════════════════════════════════════════
# Get Line Items — GET /{document_id}/items
# ═══════════════════════════════════════════════════════════════════════════════


class TestGetLineItems:
    """Tests for GET /api/documents/{document_id}/items"""

    def test_get_line_items_returns_items(self, admin_client):
        """GET /{id}/items returns list of LineItemResponse for a document."""
        mock_service = _make_mock_service()
        # Ownership check: _get_owned_document fetch
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT_EXTRACTED
        # Items query — route uses .order().range().execute() for pagination
        mock_service.table.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value.data = [SAMPLE_LINE_ITEM]

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service):
            response = admin_client.get(f"/api/documents/{DOC_ID}/items")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["description"] == "Salaries & Wages"

    def test_get_line_items_empty_list(self, admin_client):
        """GET /{id}/items returns empty list when no items extracted yet."""
        mock_service = _make_mock_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT
        mock_service.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = []

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service):
            response = admin_client.get(f"/api/documents/{DOC_ID}/items")

        assert response.status_code == 200
        assert response.json() == []

    def test_get_line_items_document_not_found_404(self, admin_client):
        """GET /{id}/items returns 404 when document does not exist."""
        mock_service = _make_mock_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service):
            response = admin_client.get(f"/api/documents/nonexistent/items")

        assert response.status_code == 404

    def test_get_line_items_requires_auth_401(self, client):
        """GET /{id}/items returns 401 when not authenticated."""
        response = client.get(f"/api/documents/{DOC_ID}/items")
        assert response.status_code == 401

    def test_get_line_items_forbidden_for_other_user(self, other_employee_client):
        """GET /{id}/items returns 403 when user doesn't own the document."""
        mock_service = _make_mock_service()
        # Document belongs to admin-uuid-0001
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service):
            response = other_employee_client.get(f"/api/documents/{DOC_ID}/items")

        assert response.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════════
# Edit Line Item — PATCH /{document_id}/items/{item_id}
# ═══════════════════════════════════════════════════════════════════════════════


class TestEditLineItem:
    """Tests for PATCH /api/documents/{document_id}/items/{item_id}"""

    def test_edit_extracted_item_updates_amount(self, admin_client):
        """PATCH /{id}/items/{item_id} updates amount and returns updated item."""
        updated_item = {**SAMPLE_LINE_ITEM, "amount": 999999.0}

        mock_service = _make_mock_service()
        # Ownership check
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT_EXTRACTED
        # Item update
        mock_service.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value.data = [updated_item]

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service):
            response = admin_client.patch(
                f"/api/documents/{DOC_ID}/items/{ITEM_ID}",
                json={"amount": 999999.0},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 999999.0

    def test_edit_extracted_item_updates_description(self, admin_client):
        """PATCH /{id}/items/{item_id} updates description."""
        updated_item = {**SAMPLE_LINE_ITEM, "description": "Updated Description"}

        mock_service = _make_mock_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT_EXTRACTED
        mock_service.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value.data = [updated_item]

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service):
            response = admin_client.patch(
                f"/api/documents/{DOC_ID}/items/{ITEM_ID}",
                json={"description": "Updated Description"},
            )

        assert response.status_code == 200
        assert response.json()["description"] == "Updated Description"

    def test_edit_item_not_found_404(self, admin_client):
        """PATCH /{id}/items/{item_id} returns 404 when item doesn't exist."""
        mock_service = _make_mock_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT_EXTRACTED
        mock_service.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value.data = []

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service):
            response = admin_client.patch(
                f"/api/documents/{DOC_ID}/items/nonexistent-item",
                json={"amount": 100.0},
            )

        assert response.status_code == 404

    def test_edit_item_document_not_found_404(self, admin_client):
        """PATCH /{id}/items/{item_id} returns 404 when document doesn't exist."""
        mock_service = _make_mock_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service):
            response = admin_client.patch(
                f"/api/documents/nonexistent/items/{ITEM_ID}",
                json={"amount": 100.0},
            )

        assert response.status_code == 404

    def test_edit_item_requires_auth_401(self, client):
        """PATCH /{id}/items/{item_id} returns 401 when not authenticated."""
        response = client.patch(
            f"/api/documents/{DOC_ID}/items/{ITEM_ID}",
            json={"amount": 100.0},
        )
        assert response.status_code == 401

    def test_edit_item_empty_description_rejected(self, admin_client):
        """PATCH /{id}/items/{item_id} returns 422 when description is empty string."""
        mock_service = _make_mock_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT_EXTRACTED

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service):
            response = admin_client.patch(
                f"/api/documents/{DOC_ID}/items/{ITEM_ID}",
                json={"description": ""},
            )

        assert response.status_code == 422

    def test_edit_item_forbidden_for_other_user(self, other_employee_client):
        """PATCH /{id}/items/{item_id} returns 403 when user doesn't own the document."""
        mock_service = _make_mock_service()
        # Document belongs to admin-uuid-0001
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service):
            response = other_employee_client.patch(
                f"/api/documents/{DOC_ID}/items/{ITEM_ID}",
                json={"amount": 100.0},
            )

        assert response.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════════
# Verify Extraction — POST /{document_id}/verify
# ═══════════════════════════════════════════════════════════════════════════════


class TestVerifyExtraction:
    """Tests for POST /api/documents/{document_id}/verify"""

    def test_verify_marks_items_verified(self, admin_client):
        """POST /{id}/verify marks all line items as is_verified=True."""
        mock_service = _make_mock_service()
        # Ownership check + document fetch
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT_EXTRACTED
        # Items count check
        mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_LINE_ITEM]
        # Update items (is_verified=True)
        mock_service.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [SAMPLE_LINE_ITEM_VERIFIED]
        # Update document status
        mock_service.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [SAMPLE_DOCUMENT_VERIFIED]

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service):
            response = admin_client.post(f"/api/documents/{DOC_ID}/verify")

        assert response.status_code == 200
        data = response.json()
        assert data["extraction_status"] == "verified"

    def test_verify_updates_document_status(self, admin_client):
        """POST /{id}/verify updates document extraction_status to 'verified'."""
        verified_doc = {**SAMPLE_DOCUMENT_EXTRACTED, "extraction_status": "verified"}

        mock_service = _make_mock_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT_EXTRACTED
        mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_LINE_ITEM]
        mock_service.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [verified_doc]

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service):
            response = admin_client.post(f"/api/documents/{DOC_ID}/verify")

        assert response.status_code == 200
        assert response.json()["extraction_status"] == "verified"

    def test_verify_requires_extracted_status_400(self, admin_client):
        """POST /{id}/verify returns 400 if document is still pending/processing."""
        mock_service = _make_mock_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT  # status=pending

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service):
            response = admin_client.post(f"/api/documents/{DOC_ID}/verify")

        assert response.status_code == 400
        assert "extracted" in response.json()["detail"].lower()

    def test_verify_requires_at_least_one_item_400(self, admin_client):
        """POST /{id}/verify returns 400 if no line items have been extracted."""
        mock_service = _make_mock_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT_EXTRACTED
        mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []  # no items

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service):
            response = admin_client.post(f"/api/documents/{DOC_ID}/verify")

        assert response.status_code == 400
        assert "item" in response.json()["detail"].lower()

    def test_verify_document_not_found_404(self, admin_client):
        """POST /{id}/verify returns 404 when document does not exist."""
        mock_service = _make_mock_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service):
            response = admin_client.post(f"/api/documents/nonexistent/verify")

        assert response.status_code == 404

    def test_verify_requires_auth_401(self, client):
        """POST /{id}/verify returns 401 when not authenticated."""
        response = client.post(f"/api/documents/{DOC_ID}/verify")
        assert response.status_code == 401

    def test_verify_forbidden_for_other_user(self, other_employee_client):
        """POST /{id}/verify returns 403 when user doesn't own the document."""
        mock_service = _make_mock_service()
        # Document belongs to admin-uuid-0001
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT_EXTRACTED

        with patch("app.dependencies.get_service_client", return_value=mock_service), \
             patch("app.routers.extraction.get_service_client", return_value=mock_service):
            response = other_employee_client.post(f"/api/documents/{DOC_ID}/verify")

        assert response.status_code == 403

    def test_cannot_classify_before_verification(self, admin_client):
        """
        Architectural guard: require_verified_document raises 403 if not verified.
        Since classification routes don't exist yet, test the guard utility directly.
        """
        from app.routers.extraction import require_verified_document

        not_verified_doc = {**SAMPLE_DOCUMENT, "extraction_status": "extracted"}
        mock_service = _make_mock_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = not_verified_doc

        with patch("app.routers.extraction.get_service_client", return_value=mock_service):
            import asyncio
            with pytest.raises(Exception) as exc_info:
                asyncio.get_event_loop().run_until_complete(
                    require_verified_document(DOC_ID)
                )

        assert exc_info.value.status_code == 403

    def test_require_verified_document_passes_for_verified(self, admin_client):
        """require_verified_document does NOT raise for verified documents."""
        from app.routers.extraction import require_verified_document

        mock_service = _make_mock_service()
        mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_DOCUMENT_VERIFIED

        with patch("app.routers.extraction.get_service_client", return_value=mock_service):
            import asyncio
            # Should not raise
            result = asyncio.get_event_loop().run_until_complete(
                require_verified_document(DOC_ID)
            )

        assert result["extraction_status"] == "verified"


# ═══════════════════════════════════════════════════════════════════════════════
# Schema Validation Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestSchemas:
    """Tests for new Pydantic schemas."""

    def test_line_item_response_schema(self):
        """LineItemResponse schema validates correctly."""
        from app.models.schemas import LineItemResponse

        item = LineItemResponse(
            id=ITEM_ID,
            document_id=DOC_ID,
            description="Revenue",
            amount=1000.0,
            section="income",
            raw_text="Revenue 1000",
            is_verified=False,
        )
        assert item.description == "Revenue"
        assert item.amount == 1000.0
        assert item.is_verified is False

    def test_line_item_response_optional_fields(self):
        """LineItemResponse allows None for optional amount, section, raw_text."""
        from app.models.schemas import LineItemResponse

        item = LineItemResponse(
            id=ITEM_ID,
            document_id=DOC_ID,
            description="Unknown Item",
            amount=None,
            section=None,
            raw_text=None,
            is_verified=False,
        )
        assert item.amount is None
        assert item.section is None

    def test_line_item_update_schema(self):
        """LineItemUpdate schema allows partial updates."""
        from app.models.schemas import LineItemUpdate

        update = LineItemUpdate(amount=99999.0)
        assert update.amount == 99999.0
        assert update.description is None
        assert update.section is None

    def test_line_item_update_rejects_empty_description(self):
        """LineItemUpdate rejects empty string for description (min_length=1)."""
        from app.models.schemas import LineItemUpdate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            LineItemUpdate(description="")

    def test_task_status_response_schema(self):
        """TaskStatusResponse schema validates correctly."""
        from app.models.schemas import TaskStatusResponse

        resp = TaskStatusResponse(
            task_id=TASK_ID,
            status="queued",
            document_id=DOC_ID,
            progress=0,
        )
        assert resp.task_id == TASK_ID
        assert resp.status == "queued"

    def test_task_status_response_rejects_invalid_status(self):
        """TaskStatusResponse rejects invalid status strings."""
        from app.models.schemas import TaskStatusResponse
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            TaskStatusResponse(task_id=TASK_ID, status="invalid_status")

    def test_extraction_trigger_response_schema(self):
        """ExtractionTriggerResponse schema validates correctly."""
        from app.models.schemas import ExtractionTriggerResponse

        resp = ExtractionTriggerResponse(
            task_id=TASK_ID,
            document_id=DOC_ID,
            message="Extraction queued",
        )
        assert resp.task_id == TASK_ID
        assert resp.document_id == DOC_ID
