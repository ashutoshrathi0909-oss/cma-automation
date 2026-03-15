"""
Phase 1: Auth system tests.

RED → GREEN → REFACTOR:
  RED:   These tests are written first — they fail because the implementation doesn't exist yet.
  GREEN: Implementation in app/routers/auth.py + app/dependencies.py makes them pass.
  REFACTOR: Clean up without breaking green.
"""

from unittest.mock import MagicMock, patch

import pytest


# ── Login tests ──────────────────────────────────────────────────────────────


class TestLogin:
    def test_auth_login_returns_token(self, client):
        """Valid credentials → 200, access_token in response."""
        mock_session = MagicMock()
        mock_session.session.access_token = "valid-jwt-token"
        mock_user = MagicMock()
        mock_user.id = "user-uuid-0001"
        mock_user.email = "admin@test.com"
        mock_session.user = mock_user

        mock_profile_resp = MagicMock()
        mock_profile_resp.data = {
            "id": "user-uuid-0001",
            "full_name": "Test Admin",
            "role": "admin",
            "created_at": "2025-01-01T00:00:00+00:00",
            "updated_at": "2025-01-01T00:00:00+00:00",
        }

        with (
            patch("app.routers.auth.get_supabase_client") as mock_get_supa,
            patch("app.routers.auth.get_service_client") as mock_get_service,
        ):
            mock_supabase = MagicMock()
            mock_supabase.auth.sign_in_with_password.return_value = mock_session
            mock_get_supa.return_value = mock_supabase

            mock_service = MagicMock()
            mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = (
                mock_profile_resp
            )
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/auth/login",
                json={"email": "admin@test.com", "password": "correct-password"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["role"] == "admin"

    def test_auth_login_invalid_credentials(self, client):
        """Wrong password → 401."""
        with patch("app.routers.auth.get_supabase_client") as mock_get_supa:
            mock_supabase = MagicMock()
            mock_supabase.auth.sign_in_with_password.side_effect = Exception(
                "Invalid login credentials"
            )
            mock_get_supa.return_value = mock_supabase

            response = client.post(
                "/api/auth/login",
                json={"email": "admin@test.com", "password": "wrong-password"},
            )

        assert response.status_code == 401


# ── Register tests ───────────────────────────────────────────────────────────


class TestRegister:
    def test_auth_register_creates_user(self, admin_client):
        """Admin can register a new employee → 201."""
        new_user_mock = MagicMock()
        new_user_mock.user.id = "new-user-uuid"

        mock_profile_resp = MagicMock()
        mock_profile_resp.data = [
            {
                "id": "new-user-uuid",
                "full_name": "New Employee",
                "role": "employee",
                "created_at": "2025-01-01T00:00:00+00:00",
                "updated_at": "2025-01-01T00:00:00+00:00",
            }
        ]

        with patch("app.routers.auth.get_service_client") as mock_get_service:
            mock_service = MagicMock()
            mock_service.auth.admin.create_user.return_value = new_user_mock
            mock_service.table.return_value.insert.return_value.execute.return_value = (
                mock_profile_resp
            )
            mock_get_service.return_value = mock_service

            response = admin_client.post(
                "/api/auth/register",
                json={
                    "email": "newuser@test.com",
                    "password": "secure-password-123",
                    "full_name": "New Employee",
                    "role": "employee",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["full_name"] == "New Employee"
        assert data["role"] == "employee"

    def test_auth_register_admin_only(self, employee_client):
        """Employee cannot register users → 403."""
        response = employee_client.post(
            "/api/auth/register",
            json={
                "email": "another@test.com",
                "password": "password-123",
                "full_name": "Another User",
            },
        )
        assert response.status_code == 403


# ── Profile tests ─────────────────────────────────────────────────────────────


class TestProfile:
    def test_auth_get_profile_authenticated(self, admin_client):
        """Authenticated user can get their profile → 200."""
        response = admin_client.get("/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Test Admin"
        assert data["role"] == "admin"

    def test_auth_get_profile_unauthenticated_401(self, client):
        """No auth header → 401."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401


# ── Role enforcement tests ────────────────────────────────────────────────────


class TestRoles:
    def test_role_check_admin_passes(self, admin_client):
        """Admin accessing admin-only route → not 403."""
        with patch("app.routers.auth.get_service_client") as mock_get_service:
            mock_service = MagicMock()
            new_user = MagicMock()
            new_user.user.id = "some-uuid"
            mock_service.auth.admin.create_user.return_value = new_user
            mock_profile_resp = MagicMock()
            mock_profile_resp.data = [
                {
                    "id": "some-uuid",
                    "full_name": "X",
                    "role": "employee",
                    "created_at": "2025-01-01T00:00:00+00:00",
                    "updated_at": "2025-01-01T00:00:00+00:00",
                }
            ]
            mock_service.table.return_value.insert.return_value.execute.return_value = (
                mock_profile_resp
            )
            mock_get_service.return_value = mock_service

            response = admin_client.post(
                "/api/auth/register",
                json={"email": "x@test.com", "password": "pass123", "full_name": "X"},
            )

        assert response.status_code != 403

    def test_role_check_employee_blocked_on_admin_route(self, employee_client):
        """Employee on admin-only route → 403."""
        response = employee_client.post(
            "/api/auth/register",
            json={"email": "x@test.com", "password": "pass123", "full_name": "X"},
        )
        assert response.status_code == 403


# ── JWT validation tests ──────────────────────────────────────────────────────


class TestJWT:
    def test_jwt_expired_returns_401(self, client):
        """Expired JWT → 401."""
        with patch("app.dependencies.get_supabase_client") as mock_get_supa:
            mock_supabase = MagicMock()
            # Supabase raises AuthApiError for expired tokens
            mock_supabase.auth.get_user.side_effect = Exception("Token expired")
            mock_get_supa.return_value = mock_supabase

            response = client.get(
                "/api/auth/me",
                headers={"Authorization": "Bearer expired.jwt.token"},
            )

        assert response.status_code == 401

    def test_jwt_malformed_returns_401(self, client):
        """Malformed JWT → 401."""
        with patch("app.dependencies.get_supabase_client") as mock_get_supa:
            mock_supabase = MagicMock()
            mock_supabase.auth.get_user.side_effect = Exception("Invalid JWT")
            mock_get_supa.return_value = mock_supabase

            response = client.get(
                "/api/auth/me",
                headers={"Authorization": "Bearer not.a.real.jwt"},
            )

        assert response.status_code == 401

    def test_jwt_empty_bearer_returns_401(self, client):
        """Authorization header with 'Bearer ' but no token → 401."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer "},
        )
        assert response.status_code == 401

    def test_jwt_valid_but_user_not_returned_401(self, client):
        """Supabase returns response with user=None → 401."""
        with patch("app.dependencies.get_supabase_client") as mock_get_supa:
            mock_supabase = MagicMock()
            mock_response = MagicMock()
            mock_response.user = None
            mock_supabase.auth.get_user.return_value = mock_response
            mock_get_supa.return_value = mock_supabase

            response = client.get(
                "/api/auth/me",
                headers={"Authorization": "Bearer valid.looking.jwt"},
            )

        assert response.status_code == 401

    def test_jwt_valid_token_no_profile_in_db_returns_401(self, client):
        """Valid JWT but user has no profile row in user_profiles → 401."""
        with (
            patch("app.dependencies.get_supabase_client") as mock_get_supa,
            patch("app.dependencies.get_service_client") as mock_get_service,
        ):
            # Valid Supabase auth response
            mock_supabase = MagicMock()
            mock_auth_response = MagicMock()
            mock_auth_response.user.id = "orphan-user-uuid"
            mock_supabase.auth.get_user.return_value = mock_auth_response
            mock_get_supa.return_value = mock_supabase

            # Profile lookup returns empty
            mock_service = MagicMock()
            mock_profile_result = MagicMock()
            mock_profile_result.data = None
            mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = (
                mock_profile_result
            )
            mock_get_service.return_value = mock_service

            response = client.get(
                "/api/auth/me",
                headers={"Authorization": "Bearer valid.orphan.jwt"},
            )

        assert response.status_code == 401

    def test_jwt_valid_token_profile_fetch_error_returns_401(self, client):
        """Valid JWT but profile DB fetch raises exception → 401."""
        with (
            patch("app.dependencies.get_supabase_client") as mock_get_supa,
            patch("app.dependencies.get_service_client") as mock_get_service,
        ):
            mock_supabase = MagicMock()
            mock_auth_response = MagicMock()
            mock_auth_response.user.id = "some-user-uuid"
            mock_supabase.auth.get_user.return_value = mock_auth_response
            mock_get_supa.return_value = mock_supabase

            mock_service = MagicMock()
            mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception(
                "DB error"
            )
            mock_get_service.return_value = mock_service

            response = client.get(
                "/api/auth/me",
                headers={"Authorization": "Bearer valid.but.db.fails"},
            )

        assert response.status_code == 401
