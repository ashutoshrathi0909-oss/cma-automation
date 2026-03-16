"""Rollover router: annual financial year rollover endpoints.

Routes:
  POST /api/rollover/preview  — preview carry-forward items, no writes
  POST /api/rollover/confirm  — execute rollover, create new-year document
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_service_client, require_admin
from app.models.schemas import (
    RolloverConfirmRequest,
    RolloverConfirmResponse,
    RolloverPreviewRequest,
    RolloverPreviewResponse,
    UserProfile,
)
from app.services import rollover_service

router = APIRouter(prefix="/api/rollover", tags=["rollover"])


@router.post("/preview", response_model=RolloverPreviewResponse)
async def preview_rollover(
    body: RolloverPreviewRequest,
    current_user: UserProfile = Depends(get_current_user),
) -> RolloverPreviewResponse:
    """Preview balance sheet items that will carry forward to the new financial year.

    No database writes occur. Returns items_to_carry_forward for user review.
    Returns 400 if to_year already has documents; 404 if from_year has none.
    """
    service = get_service_client()
    return await rollover_service.preview_rollover(
        service, body.client_id, body.from_year, body.to_year
    )


@router.post("/confirm", response_model=RolloverConfirmResponse)
async def confirm_rollover(
    body: RolloverConfirmRequest,
    current_user: UserProfile = Depends(require_admin),
) -> RolloverConfirmResponse:
    """Execute the rollover: create a new document pre-populated with opening balances. Admin only.

    Creates a provisional balance_sheet document for to_year, inserts
    carried-forward line items, and writes an audit log entry.
    """
    service = get_service_client()
    return await rollover_service.confirm_rollover(service, body, current_user.id)
