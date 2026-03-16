"""Rollover service: carry forward balance sheet closing balances to a new financial year.

Two-step workflow:
  1. preview_rollover() — shows what would carry forward, no DB writes
  2. confirm_rollover() — creates new document + pre-populates opening balances
"""
from __future__ import annotations

import logging
import uuid

from app.models.schemas import (
    RolloverConfirmRequest,
    RolloverConfirmResponse,
    RolloverItem,
    RolloverPreviewResponse,
)
from app.services import audit_service

logger = logging.getLogger(__name__)

# Broad classifications that represent balance sheet positions and carry forward
# to the next year as opening balances.  P&L categories (income, expenses, etc.)
# are intentionally excluded.
BALANCE_SHEET_CATEGORIES: frozenset[str] = frozenset(
    {
        "assets",
        "liabilities",
        "net_worth",
        "capital",
        "fixed_assets",
        "current_assets",
        "current_liabilities",
        "term_liabilities",
        "investments",
        "intangible_assets",
        "total_assets",
        "total_liabilities",
    }
)


def build_rollover_items(classified_items: list[dict]) -> list[dict]:
    """Pure function: filter line items for rollover (balance sheet only).

    Only items whose broad_classification is in BALANCE_SHEET_CATEGORIES are
    included.  P&L items and items without a classification are excluded.

    Args:
        classified_items: list of dicts with at minimum:
            description, amount, cma_field_name, broad_classification

    Returns:
        list of dicts ready for RolloverItem construction.
    """
    result = []
    for item in classified_items:
        broad = (item.get("broad_classification") or "").lower().replace(" ", "_")
        if broad in BALANCE_SHEET_CATEGORIES:
            result.append(
                {
                    "description": item["description"],
                    "amount": item.get("amount"),
                    "cma_field_name": item.get("cma_field_name"),
                    "broad_classification": item.get("broad_classification"),
                }
            )
    return result


# ── Private helpers ────────────────────────────────────────────────────────


def _fetch_year_documents(service, client_id: str, year: int) -> list[dict]:
    """Fetch all documents for a given client and financial year."""
    result = (
        service.table("documents")
        .select("id,client_id,financial_year,document_type,nature,extraction_status")
        .eq("client_id", client_id)
        .eq("financial_year", year)
        .execute()
    )
    return result.data or []


def _fetch_classified_items(service, doc_ids: list[str]) -> list[dict]:
    """Fetch extracted_line_items joined with their classifications for given docs."""
    if not doc_ids:
        return []

    items_result = (
        service.table("extracted_line_items")
        .select("id,document_id,description,amount")
        .in_("document_id", doc_ids)
        .execute()
    )
    items = items_result.data or []
    if not items:
        return []

    item_ids = [i["id"] for i in items]
    clf_result = (
        service.table("classifications")
        .select("line_item_id,cma_field_name,broad_classification,is_doubt")
        .in_("line_item_id", item_ids)
        .eq("is_doubt", False)
        .execute()
    )
    clfs: dict[str, dict] = {r["line_item_id"]: r for r in (clf_result.data or [])}

    return [
        {
            "id": item["id"],
            "description": item["description"],
            "amount": item.get("amount"),
            "cma_field_name": clfs.get(item["id"], {}).get("cma_field_name"),
            "broad_classification": clfs.get(item["id"], {}).get("broad_classification"),
        }
        for item in items
    ]


# ── Pipeline functions ─────────────────────────────────────────────────────


async def preview_rollover(
    service,
    client_id: str,
    from_year: int,
    to_year: int,
) -> RolloverPreviewResponse:
    """Preview what items would be carried forward. No DB writes.

    Validates:
    - to_year must NOT already have documents (prevents duplicate year)
    - from_year MUST have documents (source data must exist)
    """
    from fastapi import HTTPException

    to_docs = _fetch_year_documents(service, client_id, to_year)
    if to_docs:
        raise HTTPException(
            status_code=400,
            detail=f"Financial year {to_year} already has documents for this client",
        )

    from_docs = _fetch_year_documents(service, client_id, from_year)
    if not from_docs:
        raise HTTPException(
            status_code=404,
            detail=f"No documents found for financial year {from_year}",
        )

    from_doc_ids = [d["id"] for d in from_docs]
    classified = _fetch_classified_items(service, from_doc_ids)
    items = build_rollover_items(classified)

    return RolloverPreviewResponse(
        client_id=client_id,
        from_year=from_year,
        to_year=to_year,
        items_to_carry_forward=[RolloverItem(**i) for i in items],
    )


async def confirm_rollover(
    service,
    request: RolloverConfirmRequest,
    user_id: str,
) -> RolloverConfirmResponse:
    """Execute the rollover: create new document + pre-populate opening balances.

    Steps:
    1. Re-validate to_year is empty (idempotency guard).
    2. Fetch from_year classified items.
    3. Create a new balance_sheet document for to_year (nature=provisional).
    4. Insert carried-forward line items into the new document.
    5. Write audit trail.
    """
    from fastapi import HTTPException

    to_docs = _fetch_year_documents(service, request.client_id, request.to_year)
    if to_docs:
        raise HTTPException(
            status_code=400,
            detail=f"Financial year {request.to_year} already has documents for this client",
        )

    from_docs = _fetch_year_documents(service, request.client_id, request.from_year)
    if not from_docs:
        raise HTTPException(
            status_code=404,
            detail=f"No documents found for financial year {request.from_year}",
        )

    from_doc_ids = [d["id"] for d in from_docs]
    classified = _fetch_classified_items(service, from_doc_ids)
    items_to_carry = build_rollover_items(classified)

    # Create a new provisional balance_sheet document for to_year
    new_doc_id = str(uuid.uuid4())
    doc_insert = (
        service.table("documents")
        .insert(
            {
                "id": new_doc_id,
                "client_id": request.client_id,
                "file_name": (
                    f"rollover_{request.from_year}_to_{request.to_year}.xlsx"
                ),
                "file_path": f"rollover/{new_doc_id}.xlsx",
                "file_type": "xlsx",
                "document_type": "balance_sheet",
                "financial_year": request.to_year,
                "nature": "provisional",
                "extraction_status": "extracted",
                "uploaded_by": user_id,
            }
        )
        .execute()
    )
    if not doc_insert.data:
        raise HTTPException(status_code=500, detail="Failed to create rollover document")

    # Pre-populate with carried-forward opening balances
    items_created = 0
    if items_to_carry:
        line_items = [
            {
                "id": str(uuid.uuid4()),
                "document_id": new_doc_id,
                "description": item["description"],
                "amount": item["amount"],
                "section": "Carried Forward",
                "raw_text": f"[Rolled over from FY{request.from_year}]",
                "is_verified": False,
            }
            for item in items_to_carry
        ]
        li_result = (
            service.table("extracted_line_items").insert(line_items).execute()
        )
        items_created = len(li_result.data or [])

    # Audit log (entity_type="client" since there's no CMA report yet for new year)
    audit_service.log_action(
        service,
        user_id,
        "rollover_confirmed",
        "client",
        request.client_id,
        before={"financial_year": request.from_year},
        after={
            "new_document_id": new_doc_id,
            "to_year": request.to_year,
            "items_created": items_created,
        },
    )

    return RolloverConfirmResponse(
        status="ok",
        document_ids=[new_doc_id],
        items_created=items_created,
    )
