"""Shared pytest fixtures for CMA backend tests."""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import UserProfile
from app.dependencies import get_current_user


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


@pytest.fixture
def client():
    """Unauthenticated test client."""
    app.dependency_overrides.clear()
    return TestClient(app)


@pytest.fixture
def admin_client():
    """Test client authenticated as admin."""
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def employee_client():
    """Test client authenticated as employee."""
    app.dependency_overrides[get_current_user] = lambda: EMPLOYEE_USER
    yield TestClient(app)
    app.dependency_overrides.clear()
