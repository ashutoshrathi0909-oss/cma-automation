"""
Phase 2: Client management tests.

RED → GREEN → REFACTOR:
  RED:   These tests are written first — they fail because the router doesn't exist yet.
  GREEN: Implementation in app/routers/clients.py makes them pass.
  REFACTOR: Clean up without breaking green.
"""

from unittest.mock import MagicMock, patch

import pytest


# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_CLIENT = {
    "id": "client-uuid-0001",
    "name": "ABC Manufacturing Ltd",
    "industry_type": "manufacturing",
    "financial_year_ending": "31st March",
    "currency": "INR",
    "notes": None,
    "created_by": "admin-uuid-0001",
    "created_at": "2025-01-01T00:00:00+00:00",
    "updated_at": "2025-01-01T00:00:00+00:00",
}

SAMPLE_CLIENT_2 = {
    "id": "client-uuid-0002",
    "name": "XYZ Services Pvt Ltd",
    "industry_type": "service",
    "financial_year_ending": "31st March",
    "currency": "INR",
    "notes": "Important client",
    "created_by": "employee-uuid-0001",
    "created_at": "2025-01-02T00:00:00+00:00",
    "updated_at": "2025-01-02T00:00:00+00:00",
}


def _mock_service(data):
    """
    Build a Supabase service mock that returns `data` for any .execute() call.

    Uses a self-returning query builder so any chain depth works:
        table().select().ilike().order().execute()  ← always hits execute()
        table().insert().execute()                  ← same
        table().select().eq().single().execute()    ← same
    """
    svc = MagicMock()
    result = MagicMock()
    result.data = data

    # Self-returning query builder: every chainable method returns itself
    q = MagicMock()
    q.execute.return_value = result
    for method in (
        "select",
        "insert",
        "update",
        "delete",
        "eq",
        "neq",
        "ilike",
        "order",
        "single",
        "limit",
        "range",
    ):
        getattr(q, method).return_value = q

    svc.table.return_value = q
    return svc


# ── Create ─────────────────────────────────────────────────────────────────────


class TestCreateClient:
    def test_create_client_valid(self, admin_client):
        """Any authenticated user can create a client → 201 with full data."""
        with patch(
            "app.routers.clients.get_service_client",
            return_value=_mock_service([SAMPLE_CLIENT]),
        ):
            response = admin_client.post(
                "/api/clients/",
                json={"name": "ABC Manufacturing Ltd", "industry_type": "manufacturing"},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "ABC Manufacturing Ltd"
        assert data["industry_type"] == "manufacturing"
        assert data["id"] == "client-uuid-0001"
        assert data["currency"] == "INR"

    def test_create_client_missing_name_400(self, employee_client):
        """Missing required 'name' field → 422 Pydantic validation error."""
        response = employee_client.post(
            "/api/clients/",
            json={"industry_type": "manufacturing"},
        )
        assert response.status_code == 422

    def test_create_client_invalid_industry_400(self, admin_client):
        """Invalid industry_type value → 422 Pydantic validation error."""
        response = admin_client.post(
            "/api/clients/",
            json={"name": "Test Co", "industry_type": "invalid_industry"},
        )
        assert response.status_code == 422


# ── List ───────────────────────────────────────────────────────────────────────


class TestListClients:
    def test_list_clients_empty(self, admin_client):
        """No clients in DB → 200 with empty list."""
        with patch(
            "app.routers.clients.get_service_client",
            return_value=_mock_service([]),
        ):
            response = admin_client.get("/api/clients/")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_clients_with_data(self, admin_client):
        """Multiple clients → 200 with all items."""
        with patch(
            "app.routers.clients.get_service_client",
            return_value=_mock_service([SAMPLE_CLIENT, SAMPLE_CLIENT_2]),
        ):
            response = admin_client.get("/api/clients/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "ABC Manufacturing Ltd"
        assert data[1]["name"] == "XYZ Services Pvt Ltd"

    def test_search_clients_by_name(self, admin_client):
        """?search=ABC → backend filters, returns matching clients."""
        with patch(
            "app.routers.clients.get_service_client",
            return_value=_mock_service([SAMPLE_CLIENT]),
        ):
            response = admin_client.get("/api/clients/?search=ABC")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "ABC" in data[0]["name"]

    def test_filter_clients_by_industry(self, admin_client):
        """?industry=manufacturing → backend filters by industry."""
        with patch(
            "app.routers.clients.get_service_client",
            return_value=_mock_service([SAMPLE_CLIENT]),
        ):
            response = admin_client.get("/api/clients/?industry=manufacturing")

        assert response.status_code == 200
        data = response.json()
        assert all(c["industry_type"] == "manufacturing" for c in data)


# ── Get by ID ──────────────────────────────────────────────────────────────────


class TestGetClient:
    def test_get_client_by_id(self, admin_client):
        """Valid client ID → 200 with client data."""
        with patch(
            "app.routers.clients.get_service_client",
            return_value=_mock_service(SAMPLE_CLIENT),
        ):
            response = admin_client.get("/api/clients/client-uuid-0001")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "client-uuid-0001"
        assert data["name"] == "ABC Manufacturing Ltd"

    def test_get_client_not_found_404(self, admin_client):
        """Non-existent client ID → 404."""
        with patch(
            "app.routers.clients.get_service_client",
            return_value=_mock_service(None),
        ):
            response = admin_client.get("/api/clients/nonexistent-id")

        assert response.status_code == 404


# ── Update ─────────────────────────────────────────────────────────────────────


class TestUpdateClient:
    def test_update_client(self, admin_client):
        """Valid partial update → 200 with updated data."""
        updated_client = {**SAMPLE_CLIENT, "name": "Updated Name"}
        with patch(
            "app.routers.clients.get_service_client",
            return_value=_mock_service([updated_client]),
        ):
            response = admin_client.put(
                "/api/clients/client-uuid-0001",
                json={"name": "Updated Name"},
            )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"


# ── Delete ─────────────────────────────────────────────────────────────────────


class TestDeleteClient:
    def test_delete_client_admin_only(self, admin_client):
        """Admin can delete a client → 204 no content."""
        with patch(
            "app.routers.clients.get_service_client",
            return_value=_mock_service([SAMPLE_CLIENT]),
        ):
            response = admin_client.delete("/api/clients/client-uuid-0001")

        assert response.status_code == 204

    def test_delete_client_employee_403(self, employee_client):
        """Employee attempting delete → 403 Forbidden."""
        response = employee_client.delete("/api/clients/client-uuid-0001")
        assert response.status_code == 403
