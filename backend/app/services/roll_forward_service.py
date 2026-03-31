"""Roll Forward service: create a new CMA report with a shifted year window.

This is DIFFERENT from rollover_service.py (which carries forward balance sheet
closing balances as opening balances). Roll Forward creates a new report that
reuses carried-year documents by reference and only requires classification
for the new year's documents.

Two-step workflow:
  1. preview_roll_forward() — shows what will happen, no DB writes
  2. confirm_roll_forward() — creates the new CMA report
"""
from __future__ import annotations

import logging

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def compute_roll_forward(existing_years: list[int], max_historical: int = 3) -> dict:
    """Pure function: compute which years to drop/keep/add.

    Args:
        existing_years: Current report years, e.g. [2021, 2022, 2023]
        max_historical: Maximum years in a CMA (default 3)

    Returns:
        {
            "drop_year": 2021 or None,
            "keep_years": [2022, 2023],
            "add_year": 2024,
            "target_years": [2022, 2023, 2024],
        }
    """
    sorted_years = sorted(existing_years)
    if len(sorted_years) < max_historical:
        return {
            "drop_year": None,
            "keep_years": sorted_years,
            "add_year": sorted_years[-1] + 1,
            "target_years": sorted_years + [sorted_years[-1] + 1],
        }
    return {
        "drop_year": sorted_years[0],
        "keep_years": sorted_years[1:],
        "add_year": sorted_years[-1] + 1,
        "target_years": sorted_years[1:] + [sorted_years[-1] + 1],
    }


async def preview_roll_forward(
    service,
    source_report_id: str,
    client_id: str,
    add_year: int | None = None,
):
    """Preview roll forward — no writes. Returns full preview data.

    1. Fetch source report, validate status = "complete"
    2. Compute year changes
    3. Partition source document_ids by financial_year → carried vs dropped
    4. Count carried classifications (non-doubt, from carried docs)
    5. Check if new year documents exist for this client and are verified
    6. Return preview with blocking_reasons if not ready
    """
    # Fetch source report
    result = (
        service.table("cma_reports")
        .select("*")
        .eq("id", source_report_id)
        .single()
        .execute()
    )
    report = result.data
    if not report:
        raise HTTPException(404, "Source report not found")
    if report["status"] != "complete":
        raise HTTPException(400, "Can only roll forward from a completed report")
    if report["client_id"] != client_id:
        raise HTTPException(403, "Report does not belong to this client")

    source_years = sorted(report.get("financial_years", []))
    if not source_years:
        raise HTTPException(400, "Source report has no financial years")

    roll = compute_roll_forward(source_years)
    if add_year is not None:
        roll["add_year"] = add_year
        roll["target_years"] = roll["keep_years"] + [add_year]

    # Fetch all source documents
    doc_ids = report.get("document_ids", [])
    docs_result = (
        service.table("documents")
        .select("id,file_name,financial_year,nature,document_type,extraction_status")
        .in_("id", doc_ids)
        .execute()
    )
    all_docs = docs_result.data or []

    # Partition by year
    carried_docs = [d for d in all_docs if d["financial_year"] in roll["keep_years"]]
    dropped_docs = [d for d in all_docs if d.get("financial_year") == roll["drop_year"]]

    # Count carried classifications
    carried_doc_ids = [d["id"] for d in carried_docs]
    carried_clf_count = 0
    if carried_doc_ids:
        items_result = (
            service.table("extracted_line_items")
            .select("id")
            .in_("document_id", carried_doc_ids)
            .execute()
        )
        item_ids = [i["id"] for i in (items_result.data or [])]
        if item_ids:
            # Batch count in chunks of 100 to avoid URL length limits
            for i in range(0, len(item_ids), 100):
                batch = item_ids[i : i + 100]
                clf_result = (
                    service.table("classifications")
                    .select("id", count="exact")
                    .in_("line_item_id", batch)
                    .eq("is_doubt", False)
                    .execute()
                )
                carried_clf_count += clf_result.count or 0

    # Check new year docs
    new_year_docs_result = (
        service.table("documents")
        .select("id,file_name,financial_year,nature,document_type,extraction_status")
        .eq("client_id", client_id)
        .eq("financial_year", roll["add_year"])
        .execute()
    )
    new_year_docs = new_year_docs_result.data or []
    all_verified = bool(new_year_docs) and all(
        d["extraction_status"] == "verified" for d in new_year_docs
    )

    blocking_reasons = []
    if not new_year_docs:
        blocking_reasons.append(f"No FY{roll['add_year']} documents uploaded yet")
    elif not all_verified:
        unverified = [
            d["file_name"]
            for d in new_year_docs
            if d["extraction_status"] != "verified"
        ]
        blocking_reasons.append(
            f"Documents not yet verified: {', '.join(unverified)}"
        )

    return {
        "source_report_id": source_report_id,
        "source_report_title": report.get("title", ""),
        "source_years": source_years,
        "drop_year": roll["drop_year"],
        "keep_years": roll["keep_years"],
        "add_year": roll["add_year"],
        "target_years": sorted(roll["target_years"]),
        "carried_documents": carried_docs,
        "dropped_documents": dropped_docs,
        "carried_classifications_count": carried_clf_count,
        "new_year_documents": new_year_docs,
        "new_year_docs_ready": all_verified,
        "can_confirm": bool(new_year_docs) and all_verified and len(blocking_reasons) == 0,
        "blocking_reasons": blocking_reasons,
    }


async def confirm_roll_forward(
    service,
    source_report_id: str,
    client_id: str,
    add_year: int,
    new_document_ids: list[str],
    title: str | None,
    cma_output_unit: str,
    user_id: str,
):
    """Execute roll forward — creates new CMA report.

    1. Validate source report (must be complete)
    2. Validate new documents (must be verified, correct year, correct client)
    3. Build combined document_ids (carried + new)
    4. Determine year_natures from all docs
    5. Create new cma_reports row
    6. Audit log
    7. Return new report details
    """
    # Fetch source report
    result = (
        service.table("cma_reports")
        .select("*")
        .eq("id", source_report_id)
        .single()
        .execute()
    )
    report = result.data
    if not report:
        raise HTTPException(404, "Source report not found")
    if report["status"] != "complete":
        raise HTTPException(400, "Can only roll forward from a completed report")
    if report["client_id"] != client_id:
        raise HTTPException(403, "Report does not belong to this client")

    source_years = sorted(report.get("financial_years", []))
    roll = compute_roll_forward(source_years)

    # Validate new documents
    new_docs_result = (
        service.table("documents")
        .select("*")
        .in_("id", new_document_ids)
        .execute()
    )
    new_docs = new_docs_result.data or []
    for doc in new_docs:
        if doc["extraction_status"] != "verified":
            raise HTTPException(
                400, f"Document '{doc['file_name']}' is not verified"
            )
        if doc["financial_year"] != add_year:
            raise HTTPException(
                400,
                f"Document '{doc['file_name']}' is FY{doc['financial_year']}, expected FY{add_year}",
            )
        if doc["client_id"] != client_id:
            raise HTTPException(
                400,
                f"Document '{doc['file_name']}' belongs to a different client",
            )

    # Build carried document IDs
    old_docs_result = (
        service.table("documents")
        .select("id,financial_year")
        .in_("id", report.get("document_ids", []))
        .execute()
    )
    carried_doc_ids = [
        d["id"]
        for d in (old_docs_result.data or [])
        if d["financial_year"] in roll["keep_years"]
    ]

    # Combine
    all_doc_ids = carried_doc_ids + new_document_ids
    target_years = sorted(roll["keep_years"] + [add_year])

    # Determine year_natures
    all_docs_result = (
        service.table("documents")
        .select("nature")
        .in_("id", all_doc_ids)
        .execute()
    )
    year_natures = sorted(
        set(
            d.get("nature", "").capitalize()
            for d in (all_docs_result.data or [])
            if d.get("nature")
        )
    )

    # Get client name for default title
    if not title:
        client_result = (
            service.table("clients")
            .select("name")
            .eq("id", client_id)
            .single()
            .execute()
        )
        client_name = (
            client_result.data.get("name", "Client") if client_result.data else "Client"
        )
        title = f"{client_name} CMA FY{add_year}"

    # Create new report
    new_report = (
        service.table("cma_reports")
        .insert(
            {
                "client_id": client_id,
                "title": title,
                "status": "draft",
                "document_ids": all_doc_ids,
                "financial_years": target_years,
                "year_natures": year_natures,
                "cma_output_unit": cma_output_unit,
                "created_by": user_id,
                "rolled_from_report_id": source_report_id,
                "roll_forward_metadata": {
                    "source_years": source_years,
                    "target_years": target_years,
                    "dropped_year": roll["drop_year"],
                    "added_year": add_year,
                    "carried_document_ids": carried_doc_ids,
                    "new_document_ids": new_document_ids,
                },
            }
        )
        .execute()
    )

    new_id = new_report.data[0]["id"]

    # Audit log
    service.table("cma_report_history").insert(
        {
            "cma_report_id": new_id,
            "action": "roll_forward_created",
            "action_details": {
                "source_report_id": source_report_id,
                "source_years": source_years,
                "target_years": target_years,
                "carried_docs": len(carried_doc_ids),
                "new_docs": len(new_document_ids),
            },
            "performed_by": user_id,
        }
    ).execute()

    return {
        "new_report_id": new_id,
        "title": title,
        "status": "draft",
        "document_ids": all_doc_ids,
        "financial_years": target_years,
        "carried_classifications_count": len(carried_doc_ids),
        "pending_classification_docs": len(new_document_ids),
        "message": (
            f"Report created. Classifications for "
            f"{', '.join(f'FY{y}' for y in roll['keep_years'])} carried forward. "
            f"FY{add_year} items need classification."
        ),
    }
