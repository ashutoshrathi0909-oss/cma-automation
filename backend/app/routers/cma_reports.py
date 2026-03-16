"""CMA Report API endpoints.

Provides routes for:
  - Creating a CMA report (linking verified documents)
  - Listing reports for a client
  - Fetching report detail
  - Live confidence summary (computed from classifications table)
  - All classifications for a report (across all linked documents)
  - Audit trail for a report

Guard: all linked documents must have extraction_status == 'verified'.
Ownership: reports are owned by their creator (created_by field);
           admins can access any report.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from postgrest.exceptions import APIError

from arq import create_pool

from app.dependencies import get_current_user, get_service_client
from app.services import audit_service
from app.models.schemas import (
    AuditEntry,
    CMAReportCreate,
    CMAReportResponse,
    ClassificationResponse,
    ConfidenceSummary,
    DownloadUrlResponse,
    GenerateTriggerResponse,
    UserProfile,
)
from app.workers.worker import _get_redis_settings

_ADMIN_ROLE = "admin"
_SIGNED_URL_TTL_SECONDS = 60

# Confidence thresholds — must match pipeline.py
_HIGH_CONFIDENCE_THRESHOLD = 0.85
_MEDIUM_CONFIDENCE_LOW = 0.6

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["cma_reports"])


# ── Private helpers ───────────────────────────────────────────────────────


def _get_client_or_404(service, client_id: str) -> dict:
    """Fetch client by ID or raise 404."""
    try:
        result = (
            service.table("clients")
            .select("id")
            .eq("id", client_id)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="Client not found")

    if not result.data:
        raise HTTPException(status_code=404, detail="Client not found")

    return result.data


def _get_owned_report(service, report_id: str, current_user: UserProfile) -> dict:
    """Fetch a CMA report and verify ownership. Raises 404/403 on failure."""
    try:
        result = (
            service.table("cma_reports")
            .select("*")
            .eq("id", report_id)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="CMA report not found")

    if not result.data:
        raise HTTPException(status_code=404, detail="CMA report not found")

    report = result.data
    if current_user.role != _ADMIN_ROLE and report.get("created_by") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return report


def _get_report_item_ids(service, document_ids: list[str]) -> list[str]:
    """Return all extracted_line_item IDs for the given document IDs."""
    if not document_ids:
        return []

    result = (
        service.table("extracted_line_items")
        .select("id")
        .in_("document_id", document_ids)
        .execute()
    )
    return [row["id"] for row in (result.data or [])]


# ── Create CMA report ─────────────────────────────────────────────────────


@router.post(
    "/clients/{client_id}/cma-reports",
    response_model=CMAReportResponse,
    status_code=201,
)
async def create_cma_report(
    client_id: str,
    body: CMAReportCreate,
    current_user: UserProfile = Depends(get_current_user),
) -> CMAReportResponse:
    """Create a new CMA report for a client, linking one or more verified documents."""
    service = get_service_client()

    # Verify client exists
    _get_client_or_404(service, client_id)

    # Fetch all specified documents in a single query
    docs_result = (
        service.table("documents")
        .select("id,client_id,extraction_status")
        .in_("id", body.document_ids)
        .execute()
    )
    docs = docs_result.data or []

    # All requested document IDs must be found
    found_ids = {d["id"] for d in docs}
    missing = set(body.document_ids) - found_ids
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"Documents not found: {sorted(missing)}",
        )

    # All documents must belong to this client
    for doc in docs:
        if doc["client_id"] != client_id:
            raise HTTPException(
                status_code=400,
                detail=f"Document {doc['id']} does not belong to client {client_id}",
            )

    # All documents must be verified
    for doc in docs:
        if doc["extraction_status"] != "verified":
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Document {doc['id']} has extraction_status='{doc['extraction_status']}'. "
                    "All documents must be verified before creating a CMA report."
                ),
            )

    insert_result = (
        service.table("cma_reports")
        .insert(
            {
                "client_id": client_id,
                "title": body.title,
                "status": "draft",
                "document_ids": body.document_ids,
                "created_by": current_user.id,
            }
        )
        .execute()
    )

    if not insert_result.data:
        raise HTTPException(status_code=500, detail="Failed to create CMA report")

    return CMAReportResponse(**insert_result.data[0])


# ── List CMA reports ──────────────────────────────────────────────────────


@router.get(
    "/clients/{client_id}/cma-reports",
    response_model=list[CMAReportResponse],
)
async def list_cma_reports(
    client_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> list[CMAReportResponse]:
    """List all CMA reports for a client."""
    service = get_service_client()

    _get_client_or_404(service, client_id)

    result = (
        service.table("cma_reports")
        .select("*")
        .eq("client_id", client_id)
        .order("created_at", desc=True)
        .execute()
    )

    return [CMAReportResponse(**r) for r in (result.data or [])]


# ── Get CMA report detail ──────────────────────────────────────────────────


@router.get(
    "/cma-reports/{report_id}",
    response_model=CMAReportResponse,
)
async def get_cma_report(
    report_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> CMAReportResponse:
    """Get a single CMA report by ID."""
    service = get_service_client()
    report = _get_owned_report(service, report_id, current_user)
    return CMAReportResponse(**report)


# ── Confidence summary ─────────────────────────────────────────────────────


@router.get(
    "/cma-reports/{report_id}/confidence",
    response_model=ConfidenceSummary,
)
async def get_confidence(
    report_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> ConfidenceSummary:
    """Live confidence counts computed from the classifications table."""
    service = get_service_client()
    report = _get_owned_report(service, report_id, current_user)
    document_ids = report.get("document_ids") or []

    item_ids = _get_report_item_ids(service, document_ids)
    if not item_ids:
        return ConfidenceSummary(
            total=0,
            high_confidence=0,
            medium_confidence=0,
            needs_review=0,
            approved=0,
            corrected=0,
        )

    clf_result = (
        service.table("classifications")
        .select("*")
        .in_("line_item_id", item_ids)
        .execute()
    )
    clfs = clf_result.data or []

    total = len(clfs)
    high_confidence = sum(
        1
        for c in clfs
        if not c.get("is_doubt")
        and (c.get("confidence_score") or 0) >= _HIGH_CONFIDENCE_THRESHOLD
    )
    medium_confidence = sum(
        1
        for c in clfs
        if not c.get("is_doubt")
        and _MEDIUM_CONFIDENCE_LOW
        <= (c.get("confidence_score") or 0)
        < _HIGH_CONFIDENCE_THRESHOLD
    )
    needs_review = sum(1 for c in clfs if c.get("is_doubt"))
    approved = sum(1 for c in clfs if c.get("status") == "approved")
    corrected = sum(1 for c in clfs if c.get("status") == "corrected")

    return ConfidenceSummary(
        total=total,
        high_confidence=high_confidence,
        medium_confidence=medium_confidence,
        needs_review=needs_review,
        approved=approved,
        corrected=corrected,
    )


# ── Classifications for a report ──────────────────────────────────────────


@router.get(
    "/cma-reports/{report_id}/classifications",
    response_model=list[ClassificationResponse],
)
async def get_report_classifications(
    report_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> list[ClassificationResponse]:
    """All classifications for a CMA report (across all linked documents)."""
    service = get_service_client()
    report = _get_owned_report(service, report_id, current_user)
    document_ids = report.get("document_ids") or []

    item_ids = _get_report_item_ids(service, document_ids)
    if not item_ids:
        return []

    result = (
        service.table("classifications")
        .select("*")
        .in_("line_item_id", item_ids)
        .order("created_at")
        .execute()
    )
    return [ClassificationResponse(**r) for r in (result.data or [])]


# ── Audit trail ────────────────────────────────────────────────────────────


@router.get(
    "/cma-reports/{report_id}/audit",
    response_model=list[AuditEntry],
)
async def get_audit_trail(
    report_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> list[AuditEntry]:
    """Full audit trail for a CMA report, newest first."""
    service = get_service_client()
    _get_owned_report(service, report_id, current_user)

    result = (
        service.table("cma_report_history")
        .select("*")
        .eq("cma_report_id", report_id)
        .order("performed_at", desc=True)
        .execute()
    )
    return [AuditEntry(**r) for r in (result.data or [])]


# ── Generate Excel ─────────────────────────────────────────────────────────


@router.post(
    "/cma-reports/{report_id}/generate",
    response_model=GenerateTriggerResponse,
    status_code=202,
)
async def generate_cma_excel(
    report_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> GenerateTriggerResponse:
    """Enqueue Excel generation. Blocked if any is_doubt=True classifications remain."""
    service = get_service_client()
    report = _get_owned_report(service, report_id, current_user)

    # Guard: block if any unresolved doubts exist
    document_ids = report.get("document_ids") or []
    item_ids = _get_report_item_ids(service, document_ids)
    if item_ids:
        doubt_result = (
            service.table("classifications")
            .select("id")
            .in_("line_item_id", item_ids)
            .eq("is_doubt", True)
            .execute()
        )
        doubts = doubt_result.data or []
        if doubts:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Cannot generate: {len(doubts)} unresolved doubt(s) remain. "
                    "Resolve all doubts before generating the Excel file."
                ),
            )

    # Atomic status transition: only update from draft/failed → generating
    # This prevents double-enqueue race conditions
    update_result = (
        service.table("cma_reports")
        .update({"status": "generating"})
        .eq("id", report_id)
        .in_("status", ["draft", "failed"])
        .execute()
    )
    if not update_result.data:
        raise HTTPException(
            status_code=409,
            detail="Report is already generating or complete. Check its current status.",
        )

    # Enqueue ARQ task
    redis_settings = _get_redis_settings()
    redis_pool = await create_pool(redis_settings)
    try:
        job = await redis_pool.enqueue_job("run_excel_generation", report_id)
    finally:
        await redis_pool.aclose()

    if job is None:
        raise HTTPException(
            status_code=409,
            detail="A generation job for this report is already queued or running.",
        )

    logger.info(
        "Enqueued Excel generation for report_id=%s task_id=%s",
        report_id,
        job.job_id,
    )

    audit_service.log_action(
        service,
        current_user.id,
        "excel_generation_triggered",
        "cma_report",
        report_id,
        after={"task_id": job.job_id},
    )

    return GenerateTriggerResponse(
        task_id=job.job_id,
        report_id=report_id,
        message="Excel generation queued.",
    )


# ── Download signed URL ────────────────────────────────────────────────────


@router.get(
    "/cma-reports/{report_id}/download",
    response_model=DownloadUrlResponse,
)
async def download_cma_excel(
    report_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> DownloadUrlResponse:
    """Return a 60-second signed Supabase Storage URL for the generated .xlsm."""
    service = get_service_client()
    report = _get_owned_report(service, report_id, current_user)

    if report.get("status") != "complete":
        raise HTTPException(
            status_code=409,
            detail=f"Report is not ready for download. Current status: '{report.get('status')}'.",
        )

    output_path: str | None = report.get("output_path")
    if not output_path:
        raise HTTPException(
            status_code=404,
            detail="Excel file not yet generated. Trigger generation first.",
        )

    result = service.storage.from_("generated").create_signed_url(
        path=output_path, expires_in=_SIGNED_URL_TTL_SECONDS
    )
    signed_url: str = result["signedURL"]

    return DownloadUrlResponse(signed_url=signed_url, expires_in=_SIGNED_URL_TTL_SECONDS)
