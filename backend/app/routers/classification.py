"""Classification API endpoints.

Provides routes for:
  - Triggering background classification (enqueues ARQ job)
  - Fetching classification results
  - Fetching doubt items
  - Approving / correcting individual classifications
  - Bulk approving high-confidence items

Guard: document must have extraction_status == 'verified' before classification
can be triggered (enforced via require_verified_document from extraction router).
"""

from __future__ import annotations

import logging

from arq import create_pool
from fastapi import APIRouter, Depends, HTTPException
from postgrest.exceptions import APIError

from app.dependencies import get_current_user, get_service_client
from app.models.schemas import (
    BulkApproveRequest,
    BulkApproveResponse,
    ClassificationApproveRequest,
    ClassificationCorrectRequest,
    ClassificationResponse,
    ClassificationTriggerResponse,
    UserProfile,
)
from app.routers.extraction import _get_owned_document, require_verified_document
from app.services.classification.learning_system import LearningSystem
from app.workers.worker import _get_redis_settings

# Role that can access any user's documents
_ADMIN_ROLE = "admin"

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["classification"])


# ── Trigger classification ────────────────────────────────────────────────────


@router.post(
    "/documents/{document_id}/classify",
    response_model=ClassificationTriggerResponse,
    status_code=202,
)
async def trigger_classification(
    document_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> ClassificationTriggerResponse:
    """Enqueue background classification for a verified document.

    Raises 403 if the document is not yet verified or belongs to another user.
    """
    # require_verified_document checks ownership + verified status
    await require_verified_document(document_id, current_user)

    redis_settings = _get_redis_settings()
    redis_pool = await create_pool(redis_settings)
    try:
        job = await redis_pool.enqueue_job("run_classification", document_id)
    finally:
        await redis_pool.aclose()

    logger.info(
        "Enqueued classification for document_id=%s, task_id=%s",
        document_id,
        job.job_id,
    )

    return ClassificationTriggerResponse(
        task_id=job.job_id,
        document_id=document_id,
        message="Classification started.",
    )


# ── Get classification results ────────────────────────────────────────────────


@router.get(
    "/documents/{document_id}/classifications",
    response_model=list[ClassificationResponse],
)
async def get_classifications(
    document_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> list[ClassificationResponse]:
    """Return all classification results for a document."""
    _get_owned_document(document_id, current_user)

    service = get_service_client()
    item_ids = list(_get_document_item_ids(service, document_id))

    if not item_ids:
        return []

    # Batch queries to avoid PostgREST URL length limits with large documents
    # Join extracted_line_items to get description + amount for the UI
    _BATCH = 100
    all_rows: list[dict] = []
    id_list = list(item_ids)
    for i in range(0, len(id_list), _BATCH):
        batch = id_list[i : i + _BATCH]
        result = (
            service.table("classifications")
            .select("*, extracted_line_items(source_text, amount)")
            .in_("line_item_id", batch)
            .order("created_at")
            .execute()
        )
        all_rows.extend(result.data or [])

    # Flatten the joined data into the response model
    flat_rows: list[dict] = []
    for row in all_rows:
        line_item = row.pop("extracted_line_items", None) or {}
        row["line_item_description"] = line_item.get("source_text")
        row["line_item_amount"] = line_item.get("amount")
        flat_rows.append(row)

    return [ClassificationResponse(**r) for r in flat_rows]


# ── Get doubt items ───────────────────────────────────────────────────────────


@router.get(
    "/documents/{document_id}/doubts",
    response_model=list[ClassificationResponse],
)
async def get_doubts(
    document_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> list[ClassificationResponse]:
    """Return only doubt items (is_doubt=True) for a document."""
    _get_owned_document(document_id, current_user)

    service = get_service_client()
    item_ids = list(_get_document_item_ids(service, document_id))

    if not item_ids:
        return []

    # Batch queries to avoid PostgREST URL length limits with large documents
    # Join extracted_line_items to get description + amount for the UI
    _BATCH = 100
    all_rows: list[dict] = []
    id_list = list(item_ids)
    for i in range(0, len(id_list), _BATCH):
        batch = id_list[i : i + _BATCH]
        result = (
            service.table("classifications")
            .select("*, extracted_line_items(source_text, amount)")
            .in_("line_item_id", batch)
            .eq("is_doubt", True)
            .order("created_at")
            .execute()
        )
        all_rows.extend(result.data or [])

    # Flatten the joined data into the response model
    flat_rows: list[dict] = []
    for row in all_rows:
        line_item = row.pop("extracted_line_items", None) or {}
        row["line_item_description"] = line_item.get("source_text")
        row["line_item_amount"] = line_item.get("amount")
        flat_rows.append(row)

    return [ClassificationResponse(**r) for r in flat_rows]


# ── Approve single classification ─────────────────────────────────────────────


@router.post(
    "/classifications/{classification_id}/approve",
    response_model=ClassificationResponse,
)
async def approve_classification(
    classification_id: str,
    body: ClassificationApproveRequest,
    current_user: UserProfile = Depends(get_current_user),
) -> ClassificationResponse:
    """Approve a single classification and write to learned_mappings."""
    service = get_service_client()
    clf = _get_classification_or_404(service, classification_id)

    # Ownership guard: walk classification → line_item → document
    _verify_classification_owner(service, clf, current_user)

    # Fetch client's industry_type for the learning system
    industry_type = _get_industry_type(service, clf["client_id"])

    ls = LearningSystem()
    updated = ls.approve_classification(
        classification_id=classification_id,
        user_id=current_user.id,
        industry_type=industry_type,
        cma_report_id=body.cma_report_id,
    )

    return ClassificationResponse(**updated)


# ── Correct single classification ─────────────────────────────────────────────


@router.post(
    "/classifications/{classification_id}/correct",
    response_model=ClassificationResponse,
)
async def correct_classification(
    classification_id: str,
    body: ClassificationCorrectRequest,
    current_user: UserProfile = Depends(get_current_user),
) -> ClassificationResponse:
    """Correct a classification and write the correction to learned_mappings."""
    service = get_service_client()
    clf = _get_classification_or_404(service, classification_id)

    # Ownership guard: walk classification → line_item → document
    _verify_classification_owner(service, clf, current_user)

    industry_type = _get_industry_type(service, clf["client_id"])

    ls = LearningSystem()
    updated = ls.correct_classification(
        classification_id=classification_id,
        correction=body.model_dump(exclude_none=True),
        user_id=current_user.id,
        industry_type=industry_type,
        cma_report_id=body.cma_report_id,
    )

    return ClassificationResponse(**updated)


# ── Bulk approve ──────────────────────────────────────────────────────────────


@router.post(
    "/documents/{document_id}/bulk-approve",
    response_model=BulkApproveResponse,
)
async def bulk_approve(
    document_id: str,
    body: BulkApproveRequest,
    current_user: UserProfile = Depends(get_current_user),
) -> BulkApproveResponse:
    """Bulk approve classifications. If no IDs provided, approves all high-confidence."""
    doc = _get_owned_document(document_id, current_user)

    service = get_service_client()
    industry_type = _get_industry_type(service, doc["client_id"])

    ls = LearningSystem()
    count = ls.bulk_approve(
        classification_ids=body.classification_ids,
        user_id=current_user.id,
        industry_type=industry_type,
        client_id=doc["client_id"],
    )

    return BulkApproveResponse(
        approved_count=count,
        message=f"Approved {count} classification(s).",
    )


# ── Private helpers ───────────────────────────────────────────────────────────


def _get_classification_or_404(service, classification_id: str) -> dict:
    """Fetch a classification by ID or raise 404."""
    try:
        result = (
            service.table("classifications")
            .select("*")
            .eq("id", classification_id)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="Classification not found")

    if not result.data:
        raise HTTPException(status_code=404, detail="Classification not found")

    return result.data


def _verify_classification_owner(service, clf: dict, current_user: UserProfile) -> None:
    """Raise 403/404 if current_user does not own the document this classification belongs to.

    Walks the chain: classification.line_item_id → extracted_line_items.document_id → documents.
    Admin role bypasses the check.
    """
    try:
        li_result = (
            service.table("extracted_line_items")
            .select("document_id")
            .eq("id", clf["line_item_id"])
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="Line item not found")

    if not li_result.data:
        raise HTTPException(status_code=404, detail="Line item not found")

    document_id = li_result.data["document_id"]

    try:
        doc_result = (
            service.table("documents")
            .select("uploaded_by")
            .eq("id", document_id)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="Document not found")

    if not doc_result.data:
        raise HTTPException(status_code=404, detail="Document not found")

    if (
        current_user.role != _ADMIN_ROLE
        and doc_result.data["uploaded_by"] != current_user.id
    ):
        raise HTTPException(status_code=403, detail="Access denied")


def _get_document_item_ids(service, document_id: str) -> set[str]:
    """Return the set of extracted_line_item IDs for a document."""
    result = (
        service.table("extracted_line_items")
        .select("id")
        .eq("document_id", document_id)
        .execute()
    )
    return {row["id"] for row in (result.data or [])}


def _get_industry_type(service, client_id: str) -> str:
    """Return the industry_type for a client.

    Raises 503 on DB failure rather than silently defaulting to 'other' —
    a wrong industry label would corrupt learned_mappings for future queries.
    """
    try:
        result = (
            service.table("clients")
            .select("industry_type")
            .eq("id", client_id)
            .execute()
        )
        rows = result.data or []
        if rows:
            return rows[0].get("industry_type") or "other"
    except Exception as exc:
        logger.error(
            "Failed to fetch industry_type for client_id=%s: %s",
            client_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=503,
            detail="Database unavailable — could not fetch client industry type. Retry shortly.",
        )
    raise HTTPException(status_code=404, detail=f"Client not found: {client_id}")
