"""Extraction API endpoints.

Provides routes for:
  - Triggering background extraction (enqueues ARQ job)
  - Fetching extracted line items
  - Editing individual line items (user verification step)
  - Marking a document's extraction as verified (MANDATORY before classification)
"""

from __future__ import annotations

import logging

from arq import create_pool
from fastapi import APIRouter, Depends, HTTPException
from postgrest.exceptions import APIError

from app.dependencies import get_current_user, get_service_client
from app.models.schemas import (
    DocumentResponse,
    ExtractionTriggerResponse,
    LineItemResponse,
    LineItemUpdate,
    UserProfile,
)
from app.workers.worker import _get_redis_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["extraction"])

# Statuses that allow extraction to be triggered (or re-triggered after failure)
_TRIGGERABLE_STATUSES = {"pending", "failed"}


# ── Ownership helper ──────────────────────────────────────────────────────────


def _get_owned_document(document_id: str, current_user: UserProfile) -> dict:
    """Fetch document and verify ownership. Admins can access all documents.

    Raises
    ------
    HTTPException 404  — document not found
    HTTPException 403  — user does not own this document (non-admin)
    """
    service = get_service_client()
    try:
        result = (
            service.table("documents")
            .select("*")
            .eq("id", document_id)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="Document not found")

    if not result.data:
        raise HTTPException(status_code=404, detail="Document not found")

    doc = result.data

    # Ownership check: uploader or admin
    if current_user.role != "admin" and doc.get("uploaded_by") != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this document",
        )

    return doc


# ── Helper: require verified document ────────────────────────────────────────


async def require_verified_document(
    document_id: str,
    current_user: UserProfile | None = None,
) -> dict:
    """Return the document dict if extraction_status == 'verified'.

    Raises
    ------
    HTTPException 404  — document not found
    HTTPException 403  — document not yet verified (classification guard)
    """
    service = get_service_client()
    try:
        result = (
            service.table("documents")
            .select("*")
            .eq("id", document_id)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="Document not found")

    if not result.data:
        raise HTTPException(status_code=404, detail="Document not found")

    doc = result.data

    # Optional ownership check when caller provides user context
    if current_user is not None:
        if current_user.role != "admin" and doc.get("uploaded_by") != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this document",
            )

    if doc["extraction_status"] != "verified":
        raise HTTPException(
            status_code=403,
            detail=(
                "Document extraction has not been verified. "
                "Complete the verification step before proceeding to classification."
            ),
        )
    return doc


# ── Trigger extraction ────────────────────────────────────────────────────────


@router.post(
    "/{document_id}/extract",
    response_model=ExtractionTriggerResponse,
    status_code=202,
)
async def trigger_extraction(
    document_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> ExtractionTriggerResponse:
    """Enqueue background extraction. Atomically sets status to 'processing'."""
    # Verify document exists and belongs to an accessible client (ownership check)
    doc = _get_owned_document(document_id, current_user)

    current_status = doc["extraction_status"]

    # Only allow trigger from pending or failed states
    if current_status not in _TRIGGERABLE_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Document extraction_status is '{current_status}'. "
                f"Can only trigger from 'pending' or 'failed'."
            ),
        )

    # ATOMIC: Conditionally update to 'processing' only if still in triggerable state.
    # This prevents race conditions — only one caller wins the compare-and-swap.
    service = get_service_client()
    update_result = (
        service.table("documents")
        .update({"extraction_status": "processing"})
        .eq("id", document_id)
        .in_("extraction_status", list(_TRIGGERABLE_STATUSES))
        .execute()
    )

    if not update_result.data:
        # Another request already won the race
        raise HTTPException(
            status_code=409,
            detail="Extraction already in progress for this document.",
        )

    # Enqueue ARQ job (status is already 'processing')
    redis_settings = _get_redis_settings()
    redis_pool = await create_pool(redis_settings)
    try:
        job = await redis_pool.enqueue_job("run_extraction", document_id)
    finally:
        await redis_pool.aclose()

    logger.info(
        "Enqueued extraction for document_id=%s, task_id=%s",
        document_id,
        job.job_id,
    )

    return ExtractionTriggerResponse(
        task_id=job.job_id,
        document_id=document_id,
        message="Extraction started.",
    )


# ── Get line items ────────────────────────────────────────────────────────────


@router.get(
    "/{document_id}/items",
    response_model=list[LineItemResponse],
)
async def get_line_items(
    document_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> list[LineItemResponse]:
    """Return all extracted line items for a document."""
    # Ownership check
    _get_owned_document(document_id, current_user)

    service = get_service_client()
    items_result = (
        service.table("extracted_line_items")
        .select("*")
        .eq("document_id", document_id)
        .order("created_at")
        .execute()
    )

    return [LineItemResponse(**item) for item in (items_result.data or [])]


# ── Edit line item ────────────────────────────────────────────────────────────


@router.patch(
    "/{document_id}/items/{item_id}",
    response_model=LineItemResponse,
)
async def update_line_item(
    document_id: str,
    item_id: str,
    update: LineItemUpdate,
    current_user: UserProfile = Depends(get_current_user),
) -> LineItemResponse:
    """Edit a single extracted line item (description, amount, or section)."""
    # Ownership check
    _get_owned_document(document_id, current_user)

    # Build update payload (only include explicitly set fields)
    payload = update.model_dump(exclude_none=True)
    if not payload:
        raise HTTPException(status_code=400, detail="No fields to update")

    service = get_service_client()
    # Perform update, scoped to both document_id and item_id for safety
    result = (
        service.table("extracted_line_items")
        .update(payload)
        .eq("id", item_id)
        .eq("document_id", document_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Line item not found")

    return LineItemResponse(**result.data[0])


# ── Verify extraction ─────────────────────────────────────────────────────────


@router.post(
    "/{document_id}/verify",
    response_model=DocumentResponse,
)
async def verify_extraction(
    document_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> DocumentResponse:
    """Mark a document's extraction as verified.

    MANDATORY step before the classification pipeline can proceed.

    Validates:
      - Document must exist and be accessible by the current user.
      - extraction_status must be "extracted" (not pending/processing/failed).
      - At least 1 line item must be present.

    On success:
      - Sets is_verified=True on all extracted line items.
      - Updates document extraction_status → "verified".
    """
    # Ownership check
    doc = _get_owned_document(document_id, current_user)

    if doc["extraction_status"] != "extracted":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Document must have extraction_status='extracted' to be verified. "
                f"Current status: '{doc['extraction_status']}'."
            ),
        )

    service = get_service_client()
    # Ensure at least 1 line item exists
    items_result = (
        service.table("extracted_line_items")
        .select("id")
        .eq("document_id", document_id)
        .execute()
    )

    if not items_result.data:
        raise HTTPException(
            status_code=400,
            detail="Cannot verify: no line items have been extracted for this document.",
        )

    # Mark all items as verified
    service.table("extracted_line_items").update(
        {"is_verified": True}
    ).eq("document_id", document_id).execute()

    # Update document status → verified
    updated_result = (
        service.table("documents")
        .update({"extraction_status": "verified"})
        .eq("id", document_id)
        .execute()
    )

    return DocumentResponse(**updated_result.data[0])
