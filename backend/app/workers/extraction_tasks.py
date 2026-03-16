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


async def run_extraction(ctx: dict, document_id: str) -> dict:
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
        .select("id, file_path, file_type, client_id")
        .eq("id", document_id)
        .single()
        .execute()
    )

    if not doc_result.data:
        raise ValueError(f"Document not found: {document_id}")

    doc = doc_result.data
    file_path: str = doc["file_path"]
    file_type: str = doc["file_type"]

    try:
        # ── 2. IDEMPOTENCY: delete any prior line items ───────────────────────
        service.table("extracted_line_items").delete().eq(
            "document_id", document_id
        ).execute()

        # ── 3. Download from Supabase Storage ────────────────────────────────
        logger.info("Downloading %s from storage", file_path)
        file_content: bytes = service.storage.from_(STORAGE_BUCKET).download(file_path)

        # ── 4. Extract line items ─────────────────────────────────────────────
        logger.info("Extracting line items from %s (type=%s)", file_path, file_type)
        line_items = await extract_document(file_content, file_type, file_path)

        # ── 5. Save line items to DB ──────────────────────────────────────────
        if line_items:
            rows = [
                {
                    "document_id": document_id,
                    "description": item.description,
                    "amount": item.amount,
                    "section": item.section,
                    "raw_text": item.raw_text,
                    "is_verified": False,
                }
                for item in line_items
            ]
            service.table("extracted_line_items").insert(rows).execute()
            logger.info("Saved %d line items for document %s", len(rows), document_id)

        # ── 6. Update status → extracted ─────────────────────────────────────
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
