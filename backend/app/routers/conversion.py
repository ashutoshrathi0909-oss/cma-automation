"""Conversion router: provisional → audited document conversion endpoints.

Routes:
  POST /api/conversion/preview  — diff provisional vs audited, no writes
  POST /api/conversion/confirm  — apply audited amounts + flag for re-review
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_service_client, require_admin
from app.models.schemas import (
    ConversionConfirmRequest,
    ConversionConfirmResponse,
    ConversionDiffResponse,
    ConversionPreviewRequest,
    UserProfile,
)
from app.services import conversion_service

router = APIRouter(prefix="/api/conversion", tags=["conversion"])


@router.post("/preview", response_model=ConversionDiffResponse)
async def preview_conversion(
    body: ConversionPreviewRequest,
    current_user: UserProfile = Depends(get_current_user),
) -> ConversionDiffResponse:
    """Diff a provisional document against its audited counterpart.

    Returns changed/added/removed line items. No database writes occur.
    Any authenticated user can preview (ownership enforced by document access).
    """
    service = get_service_client()
    return await conversion_service.preview_conversion(
        service,
        body.provisional_doc_id,
        body.audited_doc_id,
    )


@router.post("/confirm", response_model=ConversionConfirmResponse)
async def confirm_conversion(
    body: ConversionConfirmRequest,
    current_user: UserProfile = Depends(require_admin),
) -> ConversionConfirmResponse:
    """Apply audited amounts to the provisional document. Admin only.

    Updates line item amounts, flags affected classifications for re-review,
    changes the document's nature to 'audited', and writes an audit entry.
    """
    service = get_service_client()
    return await conversion_service.confirm_conversion(service, body, current_user.id)
