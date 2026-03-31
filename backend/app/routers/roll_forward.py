"""Roll Forward API endpoints.

Provides routes for:
  - Previewing a roll forward (what years drop/keep/add)
  - Confirming a roll forward (creates new CMA report)
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_service_client
from app.models.schemas import (
    RollForwardPreviewRequest,
    RollForwardConfirmRequest,
    UserProfile,
)
from app.services.roll_forward_service import preview_roll_forward, confirm_roll_forward

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/roll-forward", tags=["roll-forward"])


@router.post("/preview")
async def preview(
    body: RollForwardPreviewRequest,
    current_user: UserProfile = Depends(get_current_user),
):
    service = get_service_client()
    return await preview_roll_forward(
        service, body.source_report_id, body.client_id, body.add_year
    )


@router.post("/confirm")
async def confirm(
    body: RollForwardConfirmRequest,
    current_user: UserProfile = Depends(get_current_user),
):
    service = get_service_client()
    return await confirm_roll_forward(
        service,
        body.source_report_id,
        body.client_id,
        body.add_year,
        body.new_document_ids,
        body.title,
        body.cma_output_unit,
        current_user.id,
    )
