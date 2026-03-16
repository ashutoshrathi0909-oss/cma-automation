"""Conversion service: provisional → audited document diff and confirmation.

Three-step workflow:
  1. preview_conversion() — pure diff, no DB writes
  2. confirm_conversion() — apply audited amounts, flag classifications, audit-log
"""
from __future__ import annotations

import logging

from postgrest.exceptions import APIError
from rapidfuzz import fuzz

from app.models.schemas import (
    ConversionConfirmRequest,
    ConversionConfirmResponse,
    ConversionDiffItem,
    ConversionDiffResponse,
)
from app.services import audit_service

logger = logging.getLogger(__name__)

# Minimum fuzzy score (0–100) to treat two descriptions as the same line item.
FUZZY_THRESHOLD = 85


def diff_line_items(
    provisional_items: list[dict],
    audited_items: list[dict],
) -> dict:
    """Pure function: compute changed/added/removed items between two document lists.

    Matching strategy:
      1. Exact description match
      2. Fuzzy token_sort_ratio ≥ FUZZY_THRESHOLD (85)

    Items with same description AND same amount are silently ignored (no change).

    Returns:
        dict with keys "changed", "added", "removed" — each a list of dicts with
        keys: description, provisional_amount, audited_amount, change_type.
    """
    prov_by_desc: dict[str, dict] = {item["description"]: item for item in provisional_items}
    aud_by_desc: dict[str, dict] = {item["description"]: item for item in audited_items}

    matched_prov: set[str] = set()
    matched_aud: set[str] = set()
    changed: list[dict] = []

    # Pass 1: exact description matches
    for desc in list(prov_by_desc.keys()):
        if desc in aud_by_desc:
            matched_prov.add(desc)
            matched_aud.add(desc)
            p_amt = prov_by_desc[desc].get("amount")
            a_amt = aud_by_desc[desc].get("amount")
            if p_amt != a_amt:
                changed.append(
                    {
                        "description": desc,
                        "provisional_amount": p_amt,
                        "audited_amount": a_amt,
                        "change_type": "changed",
                    }
                )

    # Pass 2: fuzzy matches for still-unmatched items
    unmatched_aud_pool: set[str] = {d for d in aud_by_desc if d not in matched_aud}

    for prov_desc in prov_by_desc:
        if prov_desc in matched_prov:
            continue

        best_score = 0
        best_aud_desc: str | None = None
        for aud_desc in unmatched_aud_pool:
            score = fuzz.token_sort_ratio(prov_desc, aud_desc)
            if score > best_score:
                best_score = score
                best_aud_desc = aud_desc

        if best_score >= FUZZY_THRESHOLD and best_aud_desc:
            matched_prov.add(prov_desc)
            matched_aud.add(best_aud_desc)
            unmatched_aud_pool.discard(best_aud_desc)
            p_amt = prov_by_desc[prov_desc].get("amount")
            a_amt = aud_by_desc[best_aud_desc].get("amount")
            if p_amt != a_amt:
                changed.append(
                    {
                        "description": prov_desc,
                        "provisional_amount": p_amt,
                        "audited_amount": a_amt,
                        "change_type": "changed",
                    }
                )

    removed = [
        {
            "description": desc,
            "provisional_amount": prov_by_desc[desc].get("amount"),
            "audited_amount": None,
            "change_type": "removed",
        }
        for desc in prov_by_desc
        if desc not in matched_prov
    ]

    added = [
        {
            "description": desc,
            "provisional_amount": None,
            "audited_amount": aud_by_desc[desc].get("amount"),
            "change_type": "added",
        }
        for desc in aud_by_desc
        if desc not in matched_aud
    ]

    return {"changed": changed, "added": added, "removed": removed}


# ── Private helpers ────────────────────────────────────────────────────────


def _fetch_document(service, doc_id: str) -> dict | None:
    """Fetch a single document by ID. Returns None if not found."""
    try:
        result = (
            service.table("documents")
            .select("*")
            .eq("id", doc_id)
            .single()
            .execute()
        )
        return result.data
    except APIError:
        return None


def _fetch_line_items(service, doc_id: str) -> list[dict]:
    """Fetch id/description/amount for all line items in a document."""
    result = (
        service.table("extracted_line_items")
        .select("id,description,amount")
        .eq("document_id", doc_id)
        .execute()
    )
    return result.data or []


# ── Pipeline functions ─────────────────────────────────────────────────────


async def preview_conversion(
    service,
    provisional_doc_id: str,
    audited_doc_id: str,
) -> ConversionDiffResponse:
    """Compute and return the diff. No DB writes.

    Validates:
    - Source must have nature="provisional"
    - Target must have nature="audited"
    - Both documents must belong to the same client and financial year.
    """
    from fastapi import HTTPException

    prov_doc = _fetch_document(service, provisional_doc_id)
    if not prov_doc:
        raise HTTPException(status_code=404, detail="Provisional document not found")

    aud_doc = _fetch_document(service, audited_doc_id)
    if not aud_doc:
        raise HTTPException(status_code=404, detail="Audited document not found")

    if prov_doc.get("nature") != "provisional":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Source document must be provisional "
                f"(got nature='{prov_doc.get('nature')}')"
            ),
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

    prov_items = _fetch_line_items(service, provisional_doc_id)
    aud_items = _fetch_line_items(service, audited_doc_id)
    diff = diff_line_items(prov_items, aud_items)

    return ConversionDiffResponse(
        provisional_doc_id=provisional_doc_id,
        audited_doc_id=audited_doc_id,
        changed=[ConversionDiffItem(**item) for item in diff["changed"]],
        added=[ConversionDiffItem(**item) for item in diff["added"]],
        removed=[ConversionDiffItem(**item) for item in diff["removed"]],
    )


async def confirm_conversion(
    service,
    request: ConversionConfirmRequest,
    user_id: str,
) -> ConversionConfirmResponse:
    """Apply audited amounts to the provisional document's line items.

    Steps:
    1. Validate source is provisional.
    2. Compute diff.
    3. Update amounts for changed items in extracted_line_items.
    4. Flag affected classifications as needs_review / is_doubt=True.
    5. Update document nature to "audited".
    6. Write audit trail to cma_report_history.
    """
    from fastapi import HTTPException

    prov_doc = _fetch_document(service, request.provisional_doc_id)
    if not prov_doc:
        raise HTTPException(status_code=404, detail="Provisional document not found")
    if prov_doc.get("nature") != "provisional":
        raise HTTPException(
            status_code=400,
            detail="Conversion only works on provisional documents",
        )

    # Validate audited doc — same checks as preview to prevent cross-client data mutation
    aud_doc = _fetch_document(service, request.audited_doc_id)
    if not aud_doc:
        raise HTTPException(status_code=404, detail="Audited document not found")
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

    prov_items = _fetch_line_items(service, request.provisional_doc_id)
    aud_items = _fetch_line_items(service, request.audited_doc_id)
    diff = diff_line_items(prov_items, aud_items)

    prov_item_map = {item["description"]: item for item in prov_items}
    updated_count = 0
    flagged_item_ids: list[str] = []

    for change in diff["changed"]:
        prov_item = prov_item_map.get(change["description"])
        if prov_item:
            service.table("extracted_line_items").update(
                {"amount": change["audited_amount"]}
            ).eq("id", prov_item["id"]).execute()
            updated_count += 1
            flagged_item_ids.append(prov_item["id"])

    # Flag affected classifications for re-review
    flagged_clf_count = 0
    if flagged_item_ids:
        clf_result = (
            service.table("classifications")
            .select("id")
            .in_("line_item_id", flagged_item_ids)
            .execute()
        )
        clf_ids = [r["id"] for r in (clf_result.data or [])]
        if clf_ids:
            service.table("classifications").update(
                {
                    "is_doubt": True,
                    "status": "needs_review",
                    "doubt_reason": "Amount changed in audited conversion",
                }
            ).in_("id", clf_ids).execute()
            flagged_clf_count = len(clf_ids)

    # Update document nature to "audited"
    service.table("documents").update({"nature": "audited"}).eq(
        "id", request.provisional_doc_id
    ).execute()

    # Audit log
    audit_service.log_action(
        service,
        user_id,
        "conversion_confirmed",
        "cma_report",
        request.cma_report_id,
        before={"provisional_doc_id": request.provisional_doc_id, "nature": "provisional"},
        after={
            "audited_doc_id": request.audited_doc_id,
            "nature": "audited",
            "updated_count": updated_count,
            "flagged_for_review": flagged_clf_count,
        },
    )

    return ConversionConfirmResponse(
        status="ok",
        updated_count=updated_count,
        flagged_for_review=flagged_clf_count,
    )
