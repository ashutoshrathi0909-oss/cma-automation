"""Background extraction task for the ARQ task queue.

This module contains the async task that is enqueued by the extraction API
and executed by the ARQ worker process.
"""

from __future__ import annotations

import logging

from app.dependencies import get_service_client
from app.services.extraction.extractor_factory import extract_document

logger = logging.getLogger(__name__)

STORAGE_BUCKET = "documents"


async def run_extraction(ctx: dict, document_id: str, selected_sheets: list[str] | None = None) -> dict:
    """ARQ task: extract line items from a document and persist them to the DB.

    Flow
    ----
    1. Fetch document record from DB (file_path, file_type).
       NOTE: The API handler has already set status → "processing" atomically.
    2. IDEMPOTENCY: Delete any existing line items for this document before
       re-inserting (handles rare partial-success re-runs).
    3. Download file content from Supabase Storage.
    4. Call extract_document(content, file_type, file_path) → list[LineItem].
    5. Save line items to extracted_line_items table (batch insert).
    6. Update extraction_status → "extracted".
    7. On any error: update extraction_status → "failed", re-raise.

    Returns
    -------
    dict with keys: document_id, item_count, status
    """
    service = get_service_client()
    logger.info("run_extraction started for document_id=%s", document_id)

    # ── 1. Fetch document record ──────────────────────────────────────────────
    doc_result = (
        service.table("documents")
        .select("id, file_path, file_type, client_id, financial_year, filtered_file_path, redacted_file_path")
        .eq("id", document_id)
        .single()
        .execute()
    )

    if not doc_result.data:
        raise ValueError(f"Document not found: {document_id}")

    doc = doc_result.data
    file_path: str = doc["file_path"]
    file_type: str = doc["file_type"]
    financial_year: int | None = doc.get("financial_year")

    try:
        # ── 2. IDEMPOTENCY: delete any prior line items ───────────────────────
        service.table("extracted_line_items").delete().eq(
            "document_id", document_id
        ).execute()

        # ── 3. Download from Supabase Storage (priority: redacted > filtered > original) ──
        download_path = file_path
        if doc.get("redacted_file_path"):
            download_path = doc["redacted_file_path"]
            logger.info("Using redacted PDF at %s", download_path)
        elif doc.get("filtered_file_path"):
            download_path = doc["filtered_file_path"]
            logger.info("Using filtered PDF at %s", download_path)
        logger.info("Downloading %s from storage", download_path)
        file_content: bytes = service.storage.from_(STORAGE_BUCKET).download(download_path)

        # ── 4. Extract line items ─────────────────────────────────────────────
        logger.info("Extracting line items from %s (type=%s, selected_sheets=%s)", file_path, file_type, selected_sheets)
        line_items = await extract_document(file_content, file_type, file_path, selected_sheets=selected_sheets)

        # ── 5. Save line items to DB ──────────────────────────────────────────
        # DB column is source_text (description + raw_text combined).
        # Insert in batches of 500 to avoid Supabase row limits.
        if line_items:
            rows = [
                {
                    "document_id": document_id,
                    "client_id": doc.get("client_id"),
                    "source_text": item.description,
                    "amount": item.amount,
                    "section": item.section,
                    "financial_year": financial_year,
                    "is_verified": False,
                    "ambiguity_question": item.ambiguity_question,
                }
                for item in line_items
            ]
            # Batch insert (500 rows at a time)
            batch_size = 500
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                service.table("extracted_line_items").insert(batch).execute()
            logger.info("Saved %d line items for document %s", len(rows), document_id)

        # ── 6. Update status ─────────────────────────────────────────────────
        if len(line_items) == 0:
            # Zero items extracted — this is almost certainly a failure.
            # Mark as failed so the user can retry with a different file format
            # rather than silently proceeding through the pipeline with nothing.
            logger.warning(
                "run_extraction produced 0 items for document_id=%s "
                "(file_type=%s, path=%s). Marking as FAILED. "
                "The file may be a scanned PDF without OCR support, "
                "or the format could not be parsed by PdfExtractor.",
                document_id,
                file_type,
                file_path,
            )
            service.table("documents").update(
                {"extraction_status": "failed"}
            ).eq("id", document_id).execute()

            return {
                "document_id": document_id,
                "item_count": 0,
                "status": "failed",
                "reason": "Extraction completed but found 0 line items. "
                          "The file format may not be supported or the document "
                          "may not contain recognizable financial data.",
            }

        service.table("documents").update(
            {"extraction_status": "extracted"}
        ).eq("id", document_id).execute()

        logger.info(
            "run_extraction complete: document_id=%s, item_count=%d",
            document_id,
            len(line_items),
        )
        return {
            "document_id": document_id,
            "item_count": len(line_items),
            "status": "extracted",
        }

    except Exception as exc:
        # ── 7. On error: set status → failed ─────────────────────────────────
        logger.error(
            "run_extraction failed for document_id=%s: %s", document_id, exc
        )
        try:
            service.table("documents").update(
                {"extraction_status": "failed"}
            ).eq("id", document_id).execute()
        except Exception:
            pass  # best-effort; don't mask the original error

        raise
