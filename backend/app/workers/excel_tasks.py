"""Background Excel generation task for the ARQ task queue."""

from __future__ import annotations

import logging

from app.dependencies import get_service_client
from app.services.excel_generator import ExcelGenerator

logger = logging.getLogger(__name__)


async def run_excel_generation(ctx: dict, report_id: str) -> dict:
    """ARQ task: generate CMA Excel for a report.

    Flow
    ----
    1. Call ExcelGenerator.generate() — fills template, uploads to storage.
    2. On success: update report status → 'complete', store output_path.
    3. On failure: update report status → 'failed', re-raise.

    Returns
    -------
    dict — {"report_id": str, "status": "complete", "path": str}

    Raises
    ------
    Exception — any exception from the generator (after setting status='failed')
    """
    service = get_service_client()
    logger.info("run_excel_generation started for report_id=%s", report_id)

    # Idempotency: if already complete, return immediately (safe on retry)
    report = (
        service.table("cma_reports")
        .select("status,output_path")
        .eq("id", report_id)
        .single()
        .execute()
    )
    if report.data and report.data.get("status") == "complete":
        logger.info("run_excel_generation: report_id=%s already complete, skipping", report_id)
        return {
            "report_id": report_id,
            "status": "complete",
            "path": report.data.get("output_path", ""),
        }

    try:
        generator = ExcelGenerator(service=service)
        storage_path = generator.generate(report_id=report_id, user_id="system")

        service.table("cma_reports").update(
            {"status": "complete", "output_path": storage_path}
        ).eq("id", report_id).execute()

        logger.info(
            "run_excel_generation complete: report_id=%s path=%s",
            report_id,
            storage_path,
        )
        return {"report_id": report_id, "status": "complete", "path": storage_path}

    except Exception as exc:
        logger.error(
            "run_excel_generation failed: report_id=%s error=%s", report_id, exc
        )
        service.table("cma_reports").update({"status": "failed"}).eq(
            "id", report_id
        ).execute()
        raise
