"""FastAPI dependencies: Supabase clients, JWT validation, role enforcement."""

import os

from fastapi import Depends, HTTPException, Request
from supabase import Client, create_client

from app.config import get_settings
from app.models.schemas import UserProfile

# ── Auth bypass (testing only) ────────────────────────────────────────────────
# Set DISABLE_AUTH=true in .env to skip JWT validation during local testing.
# NEVER enable in production.

from datetime import datetime, timezone

_DISABLE_AUTH = os.getenv("DISABLE_AUTH", "false").lower() == "true"

if _DISABLE_AUTH:
    _env = os.getenv("ENVIRONMENT", "development").lower()
    if _env == "production":
        raise RuntimeError(
            "DISABLE_AUTH=true is forbidden in production environments. "
            "Remove it from your production environment variables immediately."
        )
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "⚠️  DISABLE_AUTH is enabled — JWT validation bypassed. Dev use only."
    )

_MOCK_ADMIN_USER = UserProfile(
    id="00000000-0000-0000-0000-000000000001",
    full_name="Dev Admin",
    role="admin",
    is_active=True,
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
)

# ── Supabase client factories ─────────────────────────────────────────────────
# Module-level functions (not FastAPI Depends) so they can be patched in tests.

_anon_client: Client | None = None
_service_client: Client | None = None


def get_supabase_client() -> Client:
    """Return the anon Supabase client (auth operations)."""
    global _anon_client
    if _anon_client is None:
        settings = get_settings()
        _anon_client = create_client(settings.supabase_url, settings.supabase_anon_key)
    return _anon_client


def get_service_client() -> Client:
    """Return the service-role Supabase client (bypasses RLS, admin ops)."""
    global _service_client
    if _service_client is None:
        settings = get_settings()
        _service_client = create_client(
            settings.supabase_url, settings.supabase_service_role_key
        )
    return _service_client


# ── Auth dependencies ─────────────────────────────────────────────────────────


async def get_current_user(request: Request) -> UserProfile:
    """
    Extract and validate the Supabase JWT from the Authorization header.
    Fetches the user profile from user_profiles table.
    Raises 401 for missing/invalid/expired tokens.

    When DISABLE_AUTH=true (dev only), skips all validation and returns a
    hardcoded mock admin user so you can test without credentials.
    """
    # ── Dev bypass ────────────────────────────────────────────────────────────
    if _DISABLE_AUTH:
        return _MOCK_ADMIN_USER
    # ── Normal auth flow (unchanged) ─────────────────────────────────────────

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header",
        )

    token = auth_header.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty token")

    # Validate JWT via Supabase (handles expiry + signature verification)
    try:
        supabase = get_supabase_client()
        response = supabase.auth.get_user(token)
        if not response.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        user_id = response.user.id
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Fetch role from user_profiles (service client bypasses RLS)
    try:
        service = get_service_client()
        result = (
            service.table("user_profiles")
            .select("*")
            .eq("id", user_id)
            .single()
            .execute()
        )
    except Exception:
        raise HTTPException(status_code=401, detail="User profile not found")

    if not result.data:
        raise HTTPException(status_code=401, detail="User profile not found")

    profile = result.data
    if not profile.get("is_active", True):
        raise HTTPException(status_code=401, detail="Account is deactivated")

    return UserProfile(**profile)


async def require_admin(
    current_user: UserProfile = Depends(get_current_user),
) -> UserProfile:
    """Dependency that enforces admin role. Chain via FastAPI Depends."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
