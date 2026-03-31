"""API-level tests for roll-forward endpoints."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def mock_auth():
    """Bypass auth for all API tests."""
    with patch("app.dependencies._DISABLE_AUTH", True):
        yield


@pytest.fixture
def mock_service():
    """Mock the service client."""
    mock = MagicMock()
    with patch("app.routers.roll_forward.get_service_client", return_value=mock):
        yield mock


class TestPreviewEndpoint:
    def test_preview_returns_200(self, client, mock_service):
        """POST /api/roll-forward/preview returns 200 with valid data."""
        with patch(
            "app.routers.roll_forward.preview_roll_forward",
            new_callable=AsyncMock,
            return_value={
                "source_report_id": "r1",
                "source_report_title": "Test",
                "source_years": [2021, 2022, 2023],
                "drop_year": 2021,
                "keep_years": [2022, 2023],
                "add_year": 2024,
                "target_years": [2022, 2023, 2024],
                "carried_documents": [],
                "dropped_documents": [],
                "carried_classifications_count": 50,
                "new_year_documents": [],
                "new_year_docs_ready": False,
                "can_confirm": False,
                "blocking_reasons": ["No FY2024 documents uploaded yet"],
            },
        ):
            resp = client.post(
                "/api/roll-forward/preview",
                json={"source_report_id": "r1", "client_id": "c1"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["source_report_id"] == "r1"
            assert data["can_confirm"] is False

    def test_preview_with_custom_add_year(self, client, mock_service):
        """POST /api/roll-forward/preview accepts optional add_year."""
        with patch(
            "app.routers.roll_forward.preview_roll_forward",
            new_callable=AsyncMock,
            return_value={
                "source_report_id": "r1",
                "add_year": 2025,
                "can_confirm": False,
                "blocking_reasons": [],
            },
        ) as mock_preview:
            resp = client.post(
                "/api/roll-forward/preview",
                json={"source_report_id": "r1", "client_id": "c1", "add_year": 2025},
            )
            assert resp.status_code == 200
            mock_preview.assert_called_once()
            call_args = mock_preview.call_args
            assert call_args[0][2] == "c1"  # client_id
            assert call_args[0][3] == 2025  # add_year


class TestConfirmEndpoint:
    def test_confirm_returns_200(self, client, mock_service):
        """POST /api/roll-forward/confirm returns 200 on success."""
        with patch(
            "app.routers.roll_forward.confirm_roll_forward",
            new_callable=AsyncMock,
            return_value={
                "new_report_id": "new-r1",
                "title": "Test Corp CMA FY2024",
                "status": "draft",
                "document_ids": ["d1", "d2", "d3"],
                "financial_years": [2022, 2023, 2024],
                "carried_classifications_count": 2,
                "pending_classification_docs": 1,
                "message": "Report created.",
            },
        ):
            resp = client.post(
                "/api/roll-forward/confirm",
                json={
                    "source_report_id": "r1",
                    "client_id": "c1",
                    "add_year": 2024,
                    "new_document_ids": ["d3"],
                    "cma_output_unit": "lakhs",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["new_report_id"] == "new-r1"
            assert data["status"] == "draft"

    def test_confirm_rejects_missing_fields(self, client, mock_service):
        """POST /api/roll-forward/confirm returns 422 on missing required fields."""
        resp = client.post(
            "/api/roll-forward/confirm",
            json={"source_report_id": "r1"},
        )
        assert resp.status_code == 422

    def test_confirm_passes_user_id(self, client, mock_service):
        """Confirm endpoint passes current_user.id to service."""
        with patch(
            "app.routers.roll_forward.confirm_roll_forward",
            new_callable=AsyncMock,
            return_value={"new_report_id": "new-r1", "status": "draft"},
        ) as mock_confirm:
            resp = client.post(
                "/api/roll-forward/confirm",
                json={
                    "source_report_id": "r1",
                    "client_id": "c1",
                    "add_year": 2024,
                    "new_document_ids": ["d3"],
                },
            )
            assert resp.status_code == 200
            # user_id should be the mock admin user ID
            call_args = mock_confirm.call_args
            assert call_args[0][7] is not None  # user_id

    def test_confirm_default_output_unit(self, client, mock_service):
        """Default cma_output_unit should be 'lakhs'."""
        with patch(
            "app.routers.roll_forward.confirm_roll_forward",
            new_callable=AsyncMock,
            return_value={"new_report_id": "new-r1"},
        ) as mock_confirm:
            resp = client.post(
                "/api/roll-forward/confirm",
                json={
                    "source_report_id": "r1",
                    "client_id": "c1",
                    "add_year": 2024,
                    "new_document_ids": ["d3"],
                },
            )
            assert resp.status_code == 200
            call_args = mock_confirm.call_args
            assert call_args[0][5] is None  # title
            assert call_args[0][6] == "lakhs"  # cma_output_unit
