"""Learning loop API — father review workflow.

Endpoints for:
  - Uploading a corrected CMA file
  - Generating + viewing questionnaires
  - Submitting answers → proposed rules
  - Doubt resolution (employee resolve → father approve/reject)
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from postgrest.exceptions import APIError
from pydantic import BaseModel

from app.dependencies import get_current_user, get_service_client
from app.models.schemas import UserProfile
from app.services.doubt_resolution import DoubtResolutionService
from app.services.metrics_service import MetricsService
from app.services.excel_diff import diff_cma_files
from app.services.questionnaire_generator import generate_questionnaire
from app.services.rule_processor import process_answers

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/learning", tags=["learning"])

_ADMIN_ROLE = "admin"


def _verify_report_access(service, report_id: str, user: UserProfile) -> dict:
    """Verify user owns the report (or is admin). Returns report data."""
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
    if user.role != _ADMIN_ROLE and report.get("created_by") != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return report


class AnswerItem(BaseModel):
    question_id: str
    selected_option: str  # "A", "B", or "C"
    cma_row_correction: int | None = None
    note: str | None = None


class SubmitAnswersRequest(BaseModel):
    questionnaire_id: str
    answers: list[AnswerItem]


class ResolveDoubtRequest(BaseModel):
    classification_id: str
    resolved_cma_row: int
    resolved_cma_field: str
    note: str | None = None


class ApproveRejectRequest(BaseModel):
    resolution_id: str
    reason: str | None = None


@router.get("/system/metrics")
def get_system_metrics(
    user: UserProfile = Depends(get_current_user),
):
    """Get system-wide metrics (rules, resolutions, etc.)."""
    service = get_service_client()
    svc = MetricsService(service)
    return svc.compute_system_metrics()


@router.get("/{report_id}/metrics")
def get_report_metrics(
    report_id: str,
    user: UserProfile = Depends(get_current_user),
):
    """Get classification metrics for a specific report."""
    service = get_service_client()
    _verify_report_access(service, report_id, user)
    svc = MetricsService(service)
    return svc.compute_report_metrics(report_id)


@router.post("/{report_id}/upload-corrected")
def upload_corrected(
    report_id: str,
    file: UploadFile = File(...),
    user: UserProfile = Depends(get_current_user),
):
    """Upload a father-corrected CMA file and generate a questionnaire."""
    service = get_service_client()
    report = _verify_report_access(service, report_id, user)

    ai_output_path = report.get("output_path")
    if not ai_output_path:
        raise HTTPException(400, "No AI output file found — generate the CMA first")

    # Download AI file from storage to temp
    ai_tmp = tempfile.NamedTemporaryFile(suffix=".xlsm", delete=False)
    corrected_tmp = None
    try:
        ai_bytes = service.storage.from_("generated").download(ai_output_path)
        ai_tmp.write(ai_bytes)
        ai_tmp.close()

        # Save uploaded corrected file to temp
        corrected_tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        corrected_tmp.write(file.file.read())
        corrected_tmp.close()

        # Diff
        diffs = diff_cma_files(ai_tmp.name, corrected_tmp.name)

        if not diffs:
            return {"message": "No differences found", "questionnaire_id": None, "diff_count": 0}

        # Fetch provenance for this report
        prov_data = (
            service.table("cell_provenance")
            .select("*")
            .eq("cma_report_id", report_id)
            .execute()
        ).data or []

        provenance: dict[tuple[int, str], list[dict]] = {}
        for p in prov_data:
            key = (p["cma_row"], p["cma_column"])
            provenance.setdefault(key, []).append(p)

        # Generate questionnaire
        questions = generate_questionnaire(diffs, report_id=report_id, provenance=provenance)

        # Store questionnaire
        q_record = (
            service.table("questionnaires")
            .insert({
                "cma_report_id": report_id,
                "ai_file_path": ai_output_path,
                "corrected_file_path": f"corrected/{report_id}/{file.filename}",
                "status": "pending",
                "created_by": user.id,
            })
            .execute()
        ).data[0]

        # Store questionnaire items
        items = []
        for q in questions:
            items.append({
                "questionnaire_id": q_record["id"],
                "question_id": q["question_id"],
                "cma_row": q["cma_row"],
                "cma_column": q["cma_column"],
                "ai_value": q.get("ai_value"),
                "father_value": q.get("father_value"),
                "source_items": q.get("source_items", []),
                "options": q.get("options", []),
            })

        if items:
            # Batch insert (max 100 per batch)
            for i in range(0, len(items), 100):
                service.table("questionnaire_items").insert(items[i:i+100]).execute()

        return {
            "questionnaire_id": q_record["id"],
            "diff_count": len(diffs),
            "question_count": len(questions),
        }
    finally:
        Path(ai_tmp.name).unlink(missing_ok=True)
        if corrected_tmp is not None:
            Path(corrected_tmp.name).unlink(missing_ok=True)


@router.get("/{report_id}/questionnaire")
def get_questionnaire(
    report_id: str,
    user: UserProfile = Depends(get_current_user),
):
    """Get the latest questionnaire for a report."""
    service = get_service_client()
    _verify_report_access(service, report_id, user)

    q = (
        service.table("questionnaires")
        .select("*")
        .eq("cma_report_id", report_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    ).data

    if not q:
        raise HTTPException(404, "No questionnaire found for this report")

    questionnaire = q[0]

    items = (
        service.table("questionnaire_items")
        .select("*")
        .eq("questionnaire_id", questionnaire["id"])
        .execute()
    ).data or []

    return {
        "id": questionnaire["id"],
        "status": questionnaire["status"],
        "created_at": questionnaire["created_at"],
        "items": items,
    }


@router.post("/{report_id}/answer")
def submit_answers(
    report_id: str,
    body: SubmitAnswersRequest,
    user: UserProfile = Depends(get_current_user),
):
    """Submit answers to a questionnaire and generate proposed rules."""
    service = get_service_client()
    _verify_report_access(service, report_id, user)

    # Verify questionnaire exists and belongs to this report
    q = (
        service.table("questionnaires")
        .select("*")
        .eq("id", body.questionnaire_id)
        .eq("cma_report_id", report_id)
        .single()
        .execute()
    ).data
    if not q:
        raise HTTPException(404, "Questionnaire not found")

    # Fetch questionnaire items to get source_items for rule processing
    items = (
        service.table("questionnaire_items")
        .select("*")
        .eq("questionnaire_id", body.questionnaire_id)
        .execute()
    ).data or []

    # Convert items to the format process_answers expects
    questions = [
        {
            "question_id": item["question_id"],
            "cma_row": item["cma_row"],
            "source_items": item.get("source_items", []),
        }
        for item in items
    ]

    answers = [a.model_dump() for a in body.answers]

    # Process answers into proposed rules
    rules = process_answers(answers, questions, industry_type="manufacturing")

    # Store proposed rules
    if rules:
        rule_records = [
            {
                **rule,
                "questionnaire_id": body.questionnaire_id,
                "created_by": user.id,
                "status": "pending",
            }
            for rule in rules
        ]
        service.table("proposed_rules").insert(rule_records).execute()

    # Update answer data on questionnaire items
    answer_by_qid = {a.question_id: a for a in body.answers}
    for item in items:
        answer = answer_by_qid.get(item["question_id"])
        if answer:
            service.table("questionnaire_items").update({
                "selected_option": answer.selected_option,
                "cma_row_correction": answer.cma_row_correction,
                "note": answer.note,
            }).eq("id", item["id"]).execute()

    # Update questionnaire status
    service.table("questionnaires").update(
        {"status": "answered"}
    ).eq("id", body.questionnaire_id).execute()

    return {
        "rules_created": len(rules),
        "rules": rules,
    }


# ── Loop 1: Doubt Resolution ────────────────────────────────────────────────


@router.get("/{report_id}/doubts")
def list_doubts(
    report_id: str,
    user: UserProfile = Depends(get_current_user),
):
    """List all pending doubt items for a report."""
    service = get_service_client()
    _verify_report_access(service, report_id, user)
    svc = DoubtResolutionService(service)
    return svc.list_pending_doubts(report_id)


@router.post("/{report_id}/resolve-doubt")
def resolve_doubt(
    report_id: str,
    body: ResolveDoubtRequest,
    user: UserProfile = Depends(get_current_user),
):
    """Employee resolves a doubt item."""
    service = get_service_client()
    _verify_report_access(service, report_id, user)
    svc = DoubtResolutionService(service)
    return svc.resolve_doubt(
        classification_id=body.classification_id,
        resolved_cma_row=body.resolved_cma_row,
        resolved_cma_field=body.resolved_cma_field,
        resolved_by=user.id,
        note=body.note,
    )


@router.post("/{report_id}/approve-resolution")
def approve_resolution(
    report_id: str,
    body: ApproveRejectRequest,
    user: UserProfile = Depends(get_current_user),
):
    """Father approves a doubt resolution."""
    service = get_service_client()
    _verify_report_access(service, report_id, user)
    svc = DoubtResolutionService(service)
    return svc.approve_resolution(
        resolution_id=body.resolution_id,
        approved_by=user.id,
    )


@router.post("/{report_id}/reject-resolution")
def reject_resolution(
    report_id: str,
    body: ApproveRejectRequest,
    user: UserProfile = Depends(get_current_user),
):
    """Father rejects a doubt resolution."""
    service = get_service_client()
    _verify_report_access(service, report_id, user)
    svc = DoubtResolutionService(service)
    return svc.reject_resolution(
        resolution_id=body.resolution_id,
        rejected_by=user.id,
        reason=body.reason,
    )
