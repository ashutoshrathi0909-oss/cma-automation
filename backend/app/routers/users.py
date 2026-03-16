"""User management router: admin-only CRUD for firm user accounts.

Routes:
  GET  /api/users              — list all users (admin only)
  GET  /api/users/{id}         — get user profile (admin or self)
  PUT  /api/users/{id}         — update name/role (admin only)
  PUT  /api/users/{id}/deactivate — deactivate account (admin only, not self)

Security constraints:
  - Admin cannot change their own role (prevents self-lockout)
  - Admin cannot deactivate their own account (prevents self-lockout)
  - Employee cannot access any management endpoint
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from postgrest.exceptions import APIError

from app.dependencies import get_current_user, get_service_client, require_admin
from app.models.schemas import UserProfile, UserUpdateRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserProfile])
async def list_users(
    _: UserProfile = Depends(require_admin),
) -> list[UserProfile]:
    """List all firm user profiles. Admin only."""
    service = get_service_client()
    result = (
        service.table("user_profiles").select("*").order("created_at").execute()
    )
    return [UserProfile(**r) for r in (result.data or [])]


@router.get("/{user_id}", response_model=UserProfile)
async def get_user(
    user_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> UserProfile:
    """Get a single user profile. Accessible by admin or the user themselves."""
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    service = get_service_client()
    try:
        result = (
            service.table("user_profiles")
            .select("*")
            .eq("id", user_id)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="User not found")

    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfile(**result.data)


@router.put("/{user_id}", response_model=UserProfile)
async def update_user(
    user_id: str,
    body: UserUpdateRequest,
    current_user: UserProfile = Depends(require_admin),
) -> UserProfile:
    """Update a user's name and/or role. Admin only.

    An admin cannot change their own role to prevent accidental privilege loss.
    """
    if body.role is not None and current_user.id == user_id:
        raise HTTPException(
            status_code=400,
            detail="Admins cannot change their own role",
        )

    update_payload: dict = {}
    if body.full_name is not None:
        update_payload["full_name"] = body.full_name
    if body.role is not None:
        update_payload["role"] = body.role

    if not update_payload:
        raise HTTPException(status_code=400, detail="No fields to update")

    service = get_service_client()
    try:
        result = (
            service.table("user_profiles")
            .update(update_payload)
            .eq("id", user_id)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="User not found")

    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfile(**result.data)


@router.put("/{user_id}/deactivate", response_model=UserProfile)
async def deactivate_user(
    user_id: str,
    current_user: UserProfile = Depends(require_admin),
) -> UserProfile:
    """Deactivate a user account (set is_active=False). Admin only.

    An admin cannot deactivate their own account.
    """
    if current_user.id == user_id:
        raise HTTPException(
            status_code=400,
            detail="Admins cannot deactivate their own account",
        )

    service = get_service_client()
    try:
        result = (
            service.table("user_profiles")
            .update({"is_active": False})
            .eq("id", user_id)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="User not found")

    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfile(**result.data)
