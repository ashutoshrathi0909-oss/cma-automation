"""Conversion router: provisional -> audited document conversion endpoints.

Routes:
  POST /api/conversion/preview     — V1 diff provisional vs audited, no writes
  POST /api/conversion/confirm     — V1 apply audited amounts + flag for re-review
  POST /api/conversion/v2/preview  — V2 diff with 5-category breakdown + match scores
  POST /api/conversion/v2/confirm  — V2 apply with rich per-category response
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user, get_service_client, require_admin
from app.models.schemas import (
    ConversionConfirmRequest,
    ConversionConfirmResponse,
    ConversionConfirmResponseV2,
    ConversionDiffItemV2,
    ConversionDiffResponse,
    ConversionPreviewRequest,
    ConversionPreviewResponseV2,
    UserProfile,
)
from app.services import conversion_service
from app.services.conversion_service import (
    DiffCategory,
    _fetch_document,
    _fetch_line_items,
    diff_financial_items,
)

router = APIRouter(prefix="/api/conversion", tags=["conversion"])


# ── V1 endpoints (backward compatible) ───────────────────────────────────


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


# ── V2 endpoints (5-category diff with match scores) ────────────────────


@router.post("/v2/preview", response_model=ConversionPreviewResponseV2)
async def preview_conversion_v2(
    body: ConversionPreviewRequest,
    current_user: UserProfile = Depends(get_current_user),
) -> ConversionPreviewResponseV2:
    """V2 preview: returns 5-category diff with match scores.

    Categories: unchanged, amount_changed, desc_changed, added, removed.
    Each item includes a match_score and needs_reclassification flag.
    No database writes occur.
    """
    service = get_service_client()

    # Validate documents
    prov_doc = _fetch_document(service, body.provisional_doc_id)
    if not prov_doc:
        raise HTTPException(status_code=404, detail="Provisional document not found")
    aud_doc = _fetch_document(service, body.audited_doc_id)
    if not aud_doc:
        raise HTTPException(status_code=404, detail="Audited document not found")
    if prov_doc.get("nature") != "provisional":
        raise HTTPException(
            status_code=400,
            detail=f"Source document must be provisional (got nature='{prov_doc.get('nature')}')",
        )
    if aud_doc.get("nature") != "audited":
        raise HTTPException(
            status_code=400,
            detail=f"Target document must be audited (got nature='{aud_doc.get('nature')}')",
        )
    if prov_doc.get("client_id") != aud_doc.get("client_id"):
        raise HTTPException(
            status_code=400,
            detail="Documents belong to different clients",
        )
    if prov_doc.get("financial_year") != aud_doc.get("financial_year"):
        raise HTTPException(
            status_code=400,
            detail="Documents belong to different financial years",
        )

    prov_items = _fetch_line_items(service, body.provisional_doc_id)
    aud_items = _fetch_line_items(service, body.audited_doc_id)
    diff_items = diff_financial_items(prov_items, aud_items)

    # Group by category
    grouped: dict[DiffCategory, list[ConversionDiffItemV2]] = {
        cat: [] for cat in DiffCategory
    }
    for item in diff_items:
        grouped[item.category].append(
            ConversionDiffItemV2(
                provisional_item_id=item.provisional_item_id,
                audited_item_id=item.audited_item_id,
                provisional_desc=item.provisional_desc,
                audited_desc=item.audited_desc,
                provisional_amount=item.provisional_amount,
                audited_amount=item.audited_amount,
                category=item.category.value,
                match_score=item.match_score,
                needs_reclassification=item.needs_reclassification,
            )
        )

    summary = {cat.value: len(grouped[cat]) for cat in DiffCategory}

    return ConversionPreviewResponseV2(
        source_doc_id=body.provisional_doc_id,
        target_doc_id=body.audited_doc_id,
        unchanged=grouped[DiffCategory.UNCHANGED],
        amount_changed=grouped[DiffCategory.AMOUNT_CHANGED],
        desc_changed=grouped[DiffCategory.DESC_CHANGED],
        added=grouped[DiffCategory.ADDED],
        removed=grouped[DiffCategory.REMOVED],
        summary=summary,
    )


@router.post("/v2/confirm", response_model=ConversionConfirmResponseV2)
async def confirm_conversion_v2(
    body: ConversionConfirmRequest,
    current_user: UserProfile = Depends(require_admin),
) -> ConversionConfirmResponseV2:
    """V2 confirm: apply audited data with rich per-category response.

    Runs the diff BEFORE calling confirm to capture per-category counts,
    then delegates to the existing confirm_conversion service for all DB writes.
    """
    service = get_service_client()

    # Capture the diff counts BEFORE confirm mutates the data
    prov_doc = _fetch_document(service, body.provisional_doc_id)
    if not prov_doc:
        raise HTTPException(status_code=404, detail="Provisional document not found")
    aud_doc = _fetch_document(service, body.audited_doc_id)
    if not aud_doc:
        raise HTTPException(status_code=404, detail="Audited document not found")

    prov_items = _fetch_line_items(service, body.provisional_doc_id)
    aud_items = _fetch_line_items(service, body.audited_doc_id)
    diff_items = diff_financial_items(prov_items, aud_items)

    # Count per category
    counts: dict[DiffCategory, int] = {cat: 0 for cat in DiffCategory}
    for item in diff_items:
        counts[item.category] += 1

    # Delegate the actual DB mutations to the existing service
    result = await conversion_service.confirm_conversion(service, body, current_user.id)

    return ConversionConfirmResponseV2(
        unchanged=counts[DiffCategory.UNCHANGED],
        amount_updated=counts[DiffCategory.AMOUNT_CHANGED],
        reclassified=result.flagged_for_review,
        added=counts[DiffCategory.ADDED],
        removed=counts[DiffCategory.REMOVED],
        message=(
            f"Conversion complete: {counts[DiffCategory.AMOUNT_CHANGED]} amounts updated, "
            f"{counts[DiffCategory.DESC_CHANGED]} descriptions changed, "
            f"{counts[DiffCategory.ADDED]} added, "
            f"{counts[DiffCategory.REMOVED]} removed, "
            f"{result.flagged_for_review} flagged for review"
        ),
    )
