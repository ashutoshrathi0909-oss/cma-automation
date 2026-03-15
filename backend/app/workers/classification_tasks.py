"""Background classification task for the ARQ task queue.

Guard: document must have extraction_status == 'verified' before classification
can proceed. This mirrors the API-level guard in require_verified_document().
"""

from __future__ import annotations

import logging

from app.dependencies import get_service_client
from app.services.classification.pipeline import ClassificationPipeline

logger = logging.getLogger(__name__)


async def run_classification(ctx: dict, document_id: str) -> dict:
    """ARQ task: classify all verified line items for a document.

    Flow
    ----
    1. Fetch document record; verify extraction_status == 'verified'.
    2. Fetch client record to get industry_type.
    3. IDEMPOTENCY: delete existing classifications for this document's line items.
    4. Run ClassificationPipeline.classify_document().
    5. Return summary dict.

    Raises
    ------
    ValueError  — document not found OR not verified.
    """
    service = get_service_client()
    logger.info("run_classification started for document_id=%s", document_id)

    # ── 1. Fetch and validate document ────────────────────────────────────────
    doc_result = (
        service.table("documents")
        .select("id,client_id,document_type,financial_year,extraction_status")
        .eq("id", document_id)
        .single()
        .execute()
    )

    if not doc_result.data:
        raise ValueError(f"Document not found: {document_id}")

    doc = doc_result.data

    if doc["extraction_status"] != "verified":
        raise ValueError(
            f"Document {document_id} has extraction_status='{doc['extraction_status']}'. "
            "Classification requires extraction_status='verified'."
        )

    client_id: str = doc["client_id"]
    document_type: str = doc["document_type"]
    financial_year: int = doc["financial_year"]

    # ── 2. Fetch client to get industry_type ──────────────────────────────────
    client_result = (
        service.table("clients")
        .select("id,industry_type")
        .eq("id", client_id)
        .execute()
    )
    clients = client_result.data or []
    if not clients:
        raise ValueError(f"Client not found for document {document_id}: {client_id}")

    industry_type: str = clients[0]["industry_type"]

    # ── 3. IDEMPOTENCY: delete existing classifications ───────────────────────
    # Get all line item IDs for this document
    items_result = (
        service.table("extracted_line_items")
        .select("id")
        .eq("document_id", document_id)
        .execute()
    )
    item_ids = [item["id"] for item in (items_result.data or [])]

    if item_ids:
        service.table("classifications").delete().in_("line_item_id", item_ids).execute()
        logger.info(
            "Deleted existing classifications for %d line items (document_id=%s)",
            len(item_ids),
            document_id,
        )

    # ── 4. Run pipeline ───────────────────────────────────────────────────────
    pipeline = ClassificationPipeline()
    summary = pipeline.classify_document(
        document_id=document_id,
        client_id=client_id,
        industry_type=industry_type,
        document_type=document_type,
        financial_year=financial_year,
    )

    logger.info(
        "run_classification complete: document_id=%s summary=%s",
        document_id,
        summary,
    )

    return {
        "document_id": document_id,
        "status": "classified",
        **summary,
    }
