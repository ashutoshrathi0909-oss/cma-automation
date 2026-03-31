"""Phase 8C: User management router tests.

Covers:
  GET    /api/users              (admin only)
  GET    /api/users/{id}         (admin or self)
  PUT    /api/users/{id}         (admin only — role/name update)
  PUT    /api/users/{id}/deactivate (admin only — cannot deactivate self)
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_current_user
from app.main import app
from app.models.schemas import UserProfile

# ── Constants ──────────────────────────────────────────────────────────────

ADMIN_ID = "admin-uuid-0001"
EMPLOYEE_ID = "employee-uuid-0001"
OTHER_EMPLOYEE_ID = "employee-uuid-0002"

ADMIN_USER = UserProfile(
    id=ADMIN_ID,
    full_name="Test Admin",
    role="admin",
    is_active=True,
    created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
)

EMPLOYEE_USER = UserProfile(
    id=EMPLOYEE_ID,
    full_name="Test Employee",
    role="employee",
    is_active=True,
    created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
)

SAMPLE_USER_ROW = {
    "id": EMPLOYEE_ID,
    "full_name": "Test Employee",
    "role": "employee",
    "is_active": True,
    "created_at": "2025-01-01T00:00:00+00:00",
    "updated_at": "2025-01-01T00:00:00+00:00",
}

UPDATED_EMPLOYEE_ROW = {
    **SAMPLE_USER_ROW,
    "role": "admin",
}

DEACTIVATED_ROW = {
    **SAMPLE_USER_ROW,
    "is_active": False,
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
def unauthenticated_client():
    import app.dependencies as _deps
    _original = _deps._DISABLE_AUTH
    _deps._DISABLE_AUTH = False
    app.dependency_overrides.clear()
    yield TestClient(app)
    _deps._DISABLE_AUTH = _original


# ── Mock factory ────────────────────────────────────────────────────────────


def _make_service(**table_mocks) -> MagicMock:
    svc = MagicMock()
    svc.table.side_effect = lambda name: table_mocks.get(name, MagicMock())
    return svc


def _users_table(
    list_data=None,
    single_data=None,
    update_data=None,
):
    """user_profiles table mock for list / single-get / update operations."""
    tbl = MagicMock()
    # list: .select("*").order("created_at").execute()
    tbl.select.return_value.order.return_value.execute.return_value.data = list_data or []
    # single get: .select("*").eq("id", x).single().execute()
    tbl.select.return_value.eq.return_value.single.return_value.execute.return_value.data = (
        single_data
    )
    # update: .update({}).eq("id", x).single().execute()
    tbl.update.return_value.eq.return_value.single.return_value.execute.return_value.data = (
        update_data
    )
    return tbl


# ══════════════════════════════════════════════════════════════════════════
# GET /api/users
# ══════════════════════════════════════════════════════════════════════════


class TestListUsers:
    def test_list_users_admin_only(self, admin_client):
        """Admin receives a list of all user profiles."""
        svc = _make_service(user_profiles=_users_table(list_data=[SAMPLE_USER_ROW]))
        with patch("app.routers.users.get_service_client", return_value=svc):
            response = admin_client.get("/api/users")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == EMPLOYEE_ID

    def test_employee_list_users_403(self, employee_client):
        """Employee cannot list users — 403."""
        with patch("app.routers.users.get_service_client", return_value=MagicMock()):
            response = employee_client.get("/api/users")
        assert response.status_code == 403

    def test_list_users_requires_auth(self, unauthenticated_client):
        """Unauthenticated request returns 401."""
        response = unauthenticated_client.get("/api/users")
        assert response.status_code == 401


# ══════════════════════════════════════════════════════════════════════════
# GET /api/users/{user_id}
# ══════════════════════════════════════════════════════════════════════════


class TestGetUser:
    def test_get_user_admin_can_view_any(self, admin_client):
        """Admin can view any user's profile."""
        svc = _make_service(user_profiles=_users_table(single_data=SAMPLE_USER_ROW))
        with patch("app.routers.users.get_service_client", return_value=svc):
            response = admin_client.get(f"/api/users/{EMPLOYEE_ID}")
        assert response.status_code == 200
        assert response.json()["id"] == EMPLOYEE_ID

    def test_employee_can_view_own_profile(self, employee_client):
        """Employee can view their own profile."""
        svc = _make_service(user_profiles=_users_table(single_data=SAMPLE_USER_ROW))
        with patch("app.routers.users.get_service_client", return_value=svc):
            response = employee_client.get(f"/api/users/{EMPLOYEE_ID}")
        assert response.status_code == 200

    def test_employee_cannot_view_other_profile(self, employee_client):
        """Employee cannot view another user's profile — 403."""
        with patch("app.routers.users.get_service_client", return_value=MagicMock()):
            response = employee_client.get(f"/api/users/{OTHER_EMPLOYEE_ID}")
        assert response.status_code == 403


# ══════════════════════════════════════════════════════════════════════════
# PUT /api/users/{user_id}
# ══════════════════════════════════════════════════════════════════════════


class TestUpdateUser:
    def test_admin_changes_role(self, admin_client):
        """Admin can promote an employee to admin role."""
        svc = _make_service(user_profiles=_users_table(update_data=UPDATED_EMPLOYEE_ROW))
        with patch("app.routers.users.get_service_client", return_value=svc):
            response = admin_client.put(
                f"/api/users/{EMPLOYEE_ID}",
                json={"role": "admin"},
            )
        assert response.status_code == 200
        assert response.json()["role"] == "admin"

    def test_admin_changes_full_name(self, admin_client):
        """Admin can update a user's full name."""
        updated_row = {**SAMPLE_USER_ROW, "full_name": "New Name"}
        svc = _make_service(user_profiles=_users_table(update_data=updated_row))
        with patch("app.routers.users.get_service_client", return_value=svc):
            response = admin_client.put(
                f"/api/users/{EMPLOYEE_ID}",
                json={"full_name": "New Name"},
            )
        assert response.status_code == 200
        assert response.json()["full_name"] == "New Name"

    def test_employee_cannot_update_users_403(self, employee_client):
        """Employee cannot update any user — 403."""
        with patch("app.routers.users.get_service_client", return_value=MagicMock()):
            response = employee_client.put(
                f"/api/users/{OTHER_EMPLOYEE_ID}",
                json={"role": "admin"},
            )
        assert response.status_code == 403

    def test_admin_cannot_demote_self(self, admin_client):
        """Admin cannot change their own role — prevents lockout."""
        with patch("app.routers.users.get_service_client", return_value=MagicMock()):
            response = admin_client.put(
                f"/api/users/{ADMIN_ID}",
                json={"role": "employee"},
            )
        assert response.status_code == 400
        assert "role" in response.json()["detail"].lower()

    def test_admin_can_update_own_name(self, admin_client):
        """Admin CAN update their own full_name — only role change is blocked."""
        admin_row = {
            "id": ADMIN_ID,
            "full_name": "Admin Renamed",
            "role": "admin",
            "is_active": True,
            "created_at": "2025-01-01T00:00:00+00:00",
            "updated_at": "2025-01-01T00:00:00+00:00",
        }
        svc = _make_service(user_profiles=_users_table(update_data=admin_row))
        with patch("app.routers.users.get_service_client", return_value=svc):
            response = admin_client.put(
                f"/api/users/{ADMIN_ID}",
                json={"full_name": "Admin Renamed"},
            )
        assert response.status_code == 200


# ══════════════════════════════════════════════════════════════════════════
# PUT /api/users/{user_id}/deactivate
# ══════════════════════════════════════════════════════════════════════════


class TestNotFoundPaths:
    """Cover APIError / missing data paths for 404 responses."""

    def test_get_user_not_found_raises_404(self, admin_client):
        """404 when user_profiles row doesn't exist."""
        from postgrest.exceptions import APIError

        tbl = MagicMock()
        tbl.select.return_value.eq.return_value.single.return_value.execute.side_effect = (
            APIError({"message": "not found", "code": "PGRST116", "details": "", "hint": ""})
        )
        svc = _make_service(user_profiles=tbl)
        with patch("app.routers.users.get_service_client", return_value=svc):
            response = admin_client.get(f"/api/users/{EMPLOYEE_ID}")
        assert response.status_code == 404

    def test_update_user_no_fields_400(self, admin_client):
        """400 when update body contains no recognized fields."""
        with patch("app.routers.users.get_service_client", return_value=MagicMock()):
            response = admin_client.put(
                f"/api/users/{EMPLOYEE_ID}",
                json={},
            )
        assert response.status_code == 400

    def test_update_user_not_found_raises_404(self, admin_client):
        """404 when updated user doesn't exist."""
        from postgrest.exceptions import APIError

        tbl = MagicMock()
        tbl.update.return_value.eq.return_value.single.return_value.execute.side_effect = (
            APIError({"message": "not found", "code": "PGRST116", "details": "", "hint": ""})
        )
        svc = _make_service(user_profiles=tbl)
        with patch("app.routers.users.get_service_client", return_value=svc):
            response = admin_client.put(
                f"/api/users/{EMPLOYEE_ID}",
                json={"role": "admin"},
            )
        assert response.status_code == 404

    def test_deactivate_user_not_found_raises_404(self, admin_client):
        """404 when deactivated user doesn't exist."""
        from postgrest.exceptions import APIError

        tbl = MagicMock()
        tbl.update.return_value.eq.return_value.single.return_value.execute.side_effect = (
            APIError({"message": "not found", "code": "PGRST116", "details": "", "hint": ""})
        )
        svc = _make_service(user_profiles=tbl)
        with patch("app.routers.users.get_service_client", return_value=svc):
            response = admin_client.put(f"/api/users/{EMPLOYEE_ID}/deactivate")
        assert response.status_code == 404

    def test_get_user_empty_data_404(self, admin_client):
        """404 when query succeeds but returns no data (empty result)."""
        svc = _make_service(user_profiles=_users_table(single_data=None))
        with patch("app.routers.users.get_service_client", return_value=svc):
            response = admin_client.get(f"/api/users/{EMPLOYEE_ID}")
        assert response.status_code == 404

    def test_update_user_empty_data_404(self, admin_client):
        """404 when update returns no data."""
        svc = _make_service(user_profiles=_users_table(update_data=None))
        with patch("app.routers.users.get_service_client", return_value=svc):
            response = admin_client.put(
                f"/api/users/{EMPLOYEE_ID}", json={"role": "admin"}
            )
        assert response.status_code == 404

    def test_deactivate_user_empty_data_404(self, admin_client):
        """404 when deactivate returns no data."""
        svc = _make_service(user_profiles=_users_table(update_data=None))
        with patch("app.routers.users.get_service_client", return_value=svc):
            response = admin_client.put(f"/api/users/{EMPLOYEE_ID}/deactivate")
        assert response.status_code == 404


class TestDeactivateUser:
    def test_admin_deactivates_user(self, admin_client):
        """Admin can deactivate another user and is_active becomes False."""
        svc = _make_service(user_profiles=_users_table(update_data=DEACTIVATED_ROW))
        with patch("app.routers.users.get_service_client", return_value=svc):
            response = admin_client.put(f"/api/users/{EMPLOYEE_ID}/deactivate")
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_admin_cannot_deactivate_self(self, admin_client):
        """Admin cannot deactivate their own account — prevents self-lockout."""
        with patch("app.routers.users.get_service_client", return_value=MagicMock()):
            response = admin_client.put(f"/api/users/{ADMIN_ID}/deactivate")
        assert response.status_code == 400
        assert "own" in response.json()["detail"].lower()

    def test_employee_cannot_deactivate_users(self, employee_client):
        """Employee cannot deactivate any user — 403."""
        with patch("app.routers.users.get_service_client", return_value=MagicMock()):
            response = employee_client.put(
                f"/api/users/{OTHER_EMPLOYEE_ID}/deactivate"
            )
        assert response.status_code == 403
