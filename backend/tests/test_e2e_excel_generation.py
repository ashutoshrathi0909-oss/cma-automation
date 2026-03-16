"""E2E flow test for Phase 7: Excel generation + download.

Tests the complete user journey:
  1. POST /generate → 202 with task_id
  2. GET /tasks/{task_id} → poll until complete
  3. GET /download → returns signed URL for .xlsm file
  4. Verify storage path ends in .xlsm

This is an API-level E2E test. Browser-level Playwright tests are
deferred until a dedicated E2E test phase after Phase 8.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from arq.jobs import JobStatus
from fastapi.testclient import TestClient

from app.dependencies import get_current_user
from app.main import app
from app.models.schemas import UserProfile

# ── Constants ────────────────────────────────────────────────────────────────

_REPORT_ID = "e2e00000-0000-0000-0000-000000000001"
_CLIENT_ID = "e2e00000-0000-0000-0000-000000000002"
_DOC_ID = "e2e00000-0000-0000-0000-000000000003"
_TASK_ID = "e2e-task-001"
_STORAGE_PATH = f"cma_reports/{_REPORT_ID}/output.xlsm"
_SIGNED_URL = "https://storage.example.com/signed-url?token=e2e-test"

_ADMIN = UserProfile(
    id="e2e00000-0000-0000-0000-000000000099",
    full_name="E2E Admin",
    role="admin",
    created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
)

_REPORT_DRAFT = {
    "id": _REPORT_ID,
    "client_id": _CLIENT_ID,
    "title": "E2E Test Report",
    "status": "draft",
    "document_ids": [_DOC_ID],
    "created_by": _ADMIN.id,
    "output_path": None,
    "created_at": "2025-01-01T00:00:00+00:00",
    "updated_at": "2025-01-01T00:00:00+00:00",
}

_REPORT_COMPLETE = {
    **_REPORT_DRAFT,
    "status": "complete",
    "output_path": _STORAGE_PATH,
}


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def e2e_client():
    app.dependency_overrides[get_current_user] = lambda: _ADMIN
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_generate_mocks():
    """Build service + redis mocks for the /generate endpoint."""
    svc = MagicMock()

    report_chain = MagicMock()
    report_chain.select.return_value = report_chain
    report_chain.eq.return_value = report_chain
    report_chain.in_.return_value = report_chain
    report_chain.single.return_value = report_chain
    report_chain.update.return_value = report_chain
    report_chain.insert.return_value = report_chain
    report_chain.execute.side_effect = [
        MagicMock(data=_REPORT_DRAFT),   # _get_owned_report
        MagicMock(data=[_REPORT_DRAFT]), # CAS update
        MagicMock(data=[{}]),            # audit log
    ]

    items_chain = MagicMock()
    items_chain.select.return_value = items_chain
    items_chain.in_.return_value = items_chain
    items_chain.execute.return_value = MagicMock(data=[])  # no doubts

    history_chain = MagicMock()
    history_chain.insert.return_value = history_chain
    history_chain.execute.return_value = MagicMock(data=[{}])

    def _table(name):
        if name == "cma_reports":
            return report_chain
        if name == "extracted_line_items":
            return items_chain
        if name == "cma_report_history":
            return history_chain
        m = MagicMock()
        m.select.return_value = m
        m.in_.return_value = m
        m.execute.return_value = MagicMock(data=[])
        return m

    svc.table.side_effect = _table

    job = MagicMock()
    job.job_id = _TASK_ID

    redis = AsyncMock()
    redis.enqueue_job = AsyncMock(return_value=job)
    redis.aclose = AsyncMock()

    return svc, redis


def _make_task_mock(status: JobStatus) -> AsyncMock:
    """Build an ARQ Job mock that returns the given status."""
    mock_job = AsyncMock()
    mock_job.status = AsyncMock(return_value=status)
    return mock_job


def _make_download_mocks():
    """Build service mock for the /download endpoint."""
    svc = MagicMock()

    report_chain = MagicMock()
    report_chain.select.return_value = report_chain
    report_chain.eq.return_value = report_chain
    report_chain.single.return_value = report_chain
    report_chain.execute.return_value = MagicMock(data=_REPORT_COMPLETE)
    svc.table.return_value = report_chain

    svc.storage.from_.return_value.create_signed_url.return_value = {
        "signedURL": _SIGNED_URL
    }
    return svc


# ── E2E Flow Tests ─────────────────────────────────────────────────────────────


def test_e2e_generate_returns_202_with_task_id(e2e_client):
    """Step 1: POST /generate returns 202 with task_id and report_id."""
    svc, redis = _make_generate_mocks()

    with patch("app.routers.cma_reports.get_service_client", return_value=svc), \
         patch("app.routers.cma_reports.create_pool", new_callable=AsyncMock, return_value=redis):
        resp = e2e_client.post(f"/api/cma-reports/{_REPORT_ID}/generate")

    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["report_id"] == _REPORT_ID
    assert body["task_id"] == _TASK_ID
    assert "message" in body


def test_e2e_task_status_shows_complete(e2e_client):
    """Step 2: GET /tasks/{task_id} returns status=complete when ARQ job is done."""
    mock_job = _make_task_mock(JobStatus.complete)
    mock_pool = AsyncMock()

    with patch("app.routers.tasks.create_pool", return_value=mock_pool), \
         patch("app.routers.tasks.Job", return_value=mock_job):
        resp = e2e_client.get(f"/api/tasks/{_TASK_ID}")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "complete"
    assert body["progress"] == 100
    assert body["task_id"] == _TASK_ID


def test_e2e_download_returns_xlsm_signed_url(e2e_client):
    """Step 3: GET /download returns a signed URL pointing to the .xlsm file."""
    svc = _make_download_mocks()

    with patch("app.routers.cma_reports.get_service_client", return_value=svc):
        resp = e2e_client.get(f"/api/cma-reports/{_REPORT_ID}/download")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["signed_url"] == _SIGNED_URL

    # Verify the storage path used ends in .xlsm (not .xlsx)
    call_args = svc.storage.from_.return_value.create_signed_url.call_args
    path_arg = call_args[0][0] if call_args[0] else call_args[1].get("path", "")
    assert path_arg.endswith(".xlsm"), f"Storage path must end in .xlsm, got: {path_arg!r}"


def test_e2e_full_generate_download_flow(e2e_client):
    """Full sequential flow: generate → poll until complete → download .xlsm URL.

    Simulates the complete CA user journey for Phase 7 without a browser.
    """
    # ── Step 1: POST /generate ────────────────────────────────────────────
    svc, redis = _make_generate_mocks()

    with patch("app.routers.cma_reports.get_service_client", return_value=svc), \
         patch("app.routers.cma_reports.create_pool", new_callable=AsyncMock, return_value=redis):
        gen_resp = e2e_client.post(f"/api/cma-reports/{_REPORT_ID}/generate")

    assert gen_resp.status_code == 202, gen_resp.text
    task_id = gen_resp.json()["task_id"]
    assert task_id == _TASK_ID

    # ── Step 2: Poll task status → complete ───────────────────────────────
    mock_job = _make_task_mock(JobStatus.complete)
    mock_pool = AsyncMock()

    with patch("app.routers.tasks.create_pool", return_value=mock_pool), \
         patch("app.routers.tasks.Job", return_value=mock_job):
        poll_resp = e2e_client.get(f"/api/tasks/{task_id}")

    assert poll_resp.status_code == 200
    assert poll_resp.json()["status"] == "complete"
    assert poll_resp.json()["progress"] == 100

    # ── Step 3: Download .xlsm ────────────────────────────────────────────
    svc_dl = _make_download_mocks()

    with patch("app.routers.cma_reports.get_service_client", return_value=svc_dl):
        dl_resp = e2e_client.get(f"/api/cma-reports/{_REPORT_ID}/download")

    assert dl_resp.status_code == 200
    dl_body = dl_resp.json()
    assert dl_body["signed_url"] == _SIGNED_URL

    # Final assertion: the file delivered is a macro-enabled Excel workbook
    call_args = svc_dl.storage.from_.return_value.create_signed_url.call_args
    path_arg = call_args[0][0] if call_args[0] else call_args[1].get("path", "")
    assert path_arg.endswith(".xlsm"), (
        f"Phase 7 gate: generated file must be .xlsm (macro-enabled), got: {path_arg!r}"
    )
