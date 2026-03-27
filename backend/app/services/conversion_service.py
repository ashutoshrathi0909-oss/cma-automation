"""Conversion service: provisional -> audited document diff and confirmation.

Three-step workflow:
  1. preview_conversion() -- pure diff, no DB writes
  2. confirm_conversion() -- apply audited amounts, flag classifications, audit-log

V2 uses a 4-pass diff algorithm with 5 categories:
  unchanged, amount_changed, desc_changed, added, removed
"""
from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from postgrest.exceptions import APIError
from rapidfuzz import fuzz

from app.models.schemas import (
    ConversionConfirmRequest,
    ConversionConfirmResponse,
    ConversionDiffItem,
    ConversionDiffResponse,
)
from app.services import audit_service
from app.services.extraction._types import normalize_line_text

logger = logging.getLogger(__name__)


# ── V2 enums and constants ────────────────────────────────────────────────


class DiffCategory(str, Enum):
    UNCHANGED = "unchanged"
    AMOUNT_CHANGED = "amount_changed"
    DESC_CHANGED = "desc_changed"
    ADDED = "added"
    REMOVED = "removed"


FUZZY_HIGH_THRESHOLD = 90
FUZZY_LOW_THRESHOLD = 75
AMOUNT_TOLERANCE_PCT = 0.5  # 0.5% for rounding

# Legacy constant kept for backward compatibility
FUZZY_THRESHOLD = 85


# ── V2 diff result dataclass ─────────────────────────────────────────────


@dataclass
class DiffResult:
    provisional_item_id: str | None
    audited_item_id: str | None
    provisional_desc: str | None
    audited_desc: str | None
    provisional_amount: float | None
    audited_amount: float | None
    category: DiffCategory
    match_score: float
    needs_reclassification: bool


# ── V2 helper functions ──────────────────────────────────────────────────


def _normalize(text: str) -> str:
    """Normalize text for comparison: strip prefixes, lowercase, collapse whitespace."""
    return " ".join(normalize_line_text(text).lower().split())


def _amounts_equal(a: float | None, b: float | None) -> bool:
    """Compare two amounts with tolerance for rounding differences."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if a == b:
        return True
    if a != 0:
        return abs(b - a) / abs(a) * 100 <= AMOUNT_TOLERANCE_PCT
    return False


# ── V2 primary diff function (4-pass algorithm) ─────────────────────────


def diff_financial_items(
    provisional: list[dict],
    audited: list[dict],
) -> list[DiffResult]:
    """4-pass diff algorithm producing 5 categories of results.

    Pass 1: Exact normalized-text match -> unchanged or amount_changed
    Pass 2: Fuzzy match (>=75) remaining items -> desc_changed
    Pass 3: Unmatched provisional items -> removed
    Pass 4: Unmatched audited items -> added

    Items use 'source_text' field (the actual DB column name).
    """
    results: list[DiffResult] = []

    # Index provisional by normalized description
    prov_by_norm: dict[str, dict] = {}
    for item in provisional:
        norm = _normalize(item["source_text"])
        prov_by_norm[norm] = item

    aud_by_norm: dict[str, dict] = {}
    for item in audited:
        norm = _normalize(item["source_text"])
        aud_by_norm[norm] = item

    # Pass 1: Exact normalized match
    matched_prov: set[str] = set()
    matched_aud: set[str] = set()

    for norm, p in list(prov_by_norm.items()):
        if norm in aud_by_norm:
            a = aud_by_norm[norm]
            amounts_same = _amounts_equal(p.get("amount"), a.get("amount"))
            cat = DiffCategory.UNCHANGED if amounts_same else DiffCategory.AMOUNT_CHANGED
            results.append(DiffResult(
                provisional_item_id=p["id"],
                audited_item_id=a["id"],
                provisional_desc=p["source_text"],
                audited_desc=a["source_text"],
                provisional_amount=p.get("amount"),
                audited_amount=a.get("amount"),
                category=cat,
                match_score=100.0,
                needs_reclassification=False,
            ))
            matched_prov.add(p["id"])
            matched_aud.add(a["id"])

    # Pass 2: Fuzzy match remaining
    remaining_prov = [p for p in provisional if p["id"] not in matched_prov]
    remaining_aud = [a for a in audited if a["id"] not in matched_aud]
    aud_pool = list(remaining_aud)

    for p in remaining_prov:
        if not aud_pool:
            break
        p_norm = _normalize(p["source_text"])
        best_score = 0.0
        best_aud = None
        best_idx = -1
        for idx, a in enumerate(aud_pool):
            a_norm = _normalize(a["source_text"])
            score = fuzz.token_set_ratio(p_norm, a_norm)
            if score > best_score:
                best_score = score
                best_aud = a
                best_idx = idx

        if best_score >= FUZZY_LOW_THRESHOLD and best_aud is not None:
            aud_pool.pop(best_idx)
            needs_reclass = best_score < FUZZY_HIGH_THRESHOLD
            results.append(DiffResult(
                provisional_item_id=p["id"],
                audited_item_id=best_aud["id"],
                provisional_desc=p["source_text"],
                audited_desc=best_aud["source_text"],
                provisional_amount=p.get("amount"),
                audited_amount=best_aud.get("amount"),
                category=DiffCategory.DESC_CHANGED,
                match_score=best_score,
                needs_reclassification=needs_reclass,
            ))
            matched_prov.add(p["id"])
            matched_aud.add(best_aud["id"])

    # Pass 3: Unmatched provisional -> removed
    for p in provisional:
        if p["id"] not in matched_prov:
            results.append(DiffResult(
                provisional_item_id=p["id"],
                audited_item_id=None,
                provisional_desc=p["source_text"],
                audited_desc=None,
                provisional_amount=p.get("amount"),
                audited_amount=None,
                category=DiffCategory.REMOVED,
                match_score=0.0,
                needs_reclassification=False,
            ))

    # Pass 4: Unmatched audited -> added
    for a in aud_pool:
        results.append(DiffResult(
            provisional_item_id=None,
            audited_item_id=a["id"],
            provisional_desc=None,
            audited_desc=a["source_text"],
            provisional_amount=None,
            audited_amount=a.get("amount"),
            category=DiffCategory.ADDED,
            match_score=0.0,
            needs_reclassification=True,
        ))

    return results


# ── V1 legacy diff (deprecated, kept for existing tests) ─────────────────


def _diff_line_items_v1(
    provisional_items: list[dict],
    audited_items: list[dict],
) -> dict:
    """DEPRECATED: Use diff_financial_items() instead.

    Pure function: compute changed/added/removed items between two document lists.
    Uses 'description' key (old schema).
    """
    warnings.warn(
        "_diff_line_items_v1 is deprecated, use diff_financial_items instead",
        DeprecationWarning,
        stacklevel=2,
    )
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


# Public alias so existing tests that `from ... import diff_line_items` still work
def diff_line_items(
    provisional_items: list[dict],
    audited_items: list[dict],
) -> dict:
    """DEPRECATED: backward-compatible wrapper around _diff_line_items_v1.

    Existing tests import this name. New code should use diff_financial_items().
    """
    return _diff_line_items_v1(provisional_items, audited_items)


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
    """Fetch id/source_text/amount for all line items in a document.

    Uses source_text (the actual DB column), not description.
    """
    result = (
        service.table("extracted_line_items")
        .select("id,source_text,amount")
        .eq("document_id", doc_id)
        .execute()
    )
    return result.data or []


# ── Pipeline functions ─────────────────────────────────────────────────────


async def preview_conversion(
    service,
    provisional_doc_id: str,
    audited_doc_id: str,
) -> dict:
    """Compute and return the V2 5-category diff. No DB writes.

    Validates:
    - Source must have nature="provisional"
    - Target must have nature="audited"
    - Both documents must belong to the same client and financial year.

    Returns a dict with provisional_doc_id, audited_doc_id, and diff_items (list of DiffResult).
    The router will handle conversion to the appropriate response schema.
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
    diff_items = diff_financial_items(prov_items, aud_items)

    # Return raw dict; the router (Task 2) will convert to response schema.
    # For V1 backward compatibility, also build the old 3-category format.
    changed: list[ConversionDiffItem] = []
    added: list[ConversionDiffItem] = []
    removed: list[ConversionDiffItem] = []

    for item in diff_items:
        if item.category == DiffCategory.AMOUNT_CHANGED:
            changed.append(ConversionDiffItem(
                description=item.provisional_desc or "",
                provisional_amount=item.provisional_amount,
                audited_amount=item.audited_amount,
                change_type="changed",
            ))
        elif item.category == DiffCategory.DESC_CHANGED:
            changed.append(ConversionDiffItem(
                description=item.provisional_desc or "",
                provisional_amount=item.provisional_amount,
                audited_amount=item.audited_amount,
                change_type="changed",
            ))
        elif item.category == DiffCategory.ADDED:
            added.append(ConversionDiffItem(
                description=item.audited_desc or "",
                provisional_amount=None,
                audited_amount=item.audited_amount,
                change_type="added",
            ))
        elif item.category == DiffCategory.REMOVED:
            removed.append(ConversionDiffItem(
                description=item.provisional_desc or "",
                provisional_amount=item.provisional_amount,
                audited_amount=None,
                change_type="removed",
            ))
        # UNCHANGED items are intentionally omitted from old format

    return ConversionDiffResponse(
        provisional_doc_id=provisional_doc_id,
        audited_doc_id=audited_doc_id,
        changed=changed,
        added=added,
        removed=removed,
    )


async def confirm_conversion(
    service,
    request: ConversionConfirmRequest,
    user_id: str,
) -> ConversionConfirmResponse:
    """Apply audited data to the provisional document using V2 5-category diff.

    Category-specific actions:
    - UNCHANGED: skip (no action needed)
    - AMOUNT_CHANGED: update amount only in extracted_line_items (NO is_doubt flag)
    - DESC_CHANGED (score >=90): update source_text + amount, keep classification
    - DESC_CHANGED (score 75-89): update source_text + amount, flag needs_review on classification
    - ADDED: insert new line item into extracted_line_items for provisional doc, mark for classification
    - REMOVED: set is_verified=False on the provisional item

    Also:
    - Supersede provisional doc (set superseded_at=now, superseded_by=audited_doc_id)
    - Mark audited doc (set parent_document_id=provisional_doc_id, version_number=2)
    - Update cma_reports.document_ids (swap provisional -> audited)
    - Record conversion_event in conversion_events table
    - Rich audit log with diff summary counts
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

    # Validate audited doc -- same checks as preview to prevent cross-client data mutation
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
    diff_items = diff_financial_items(prov_items, aud_items)

    now = datetime.now(timezone.utc).isoformat()
    updated_count = 0
    flagged_for_review = 0
    added_count = 0
    removed_count = 0
    unchanged_count = 0

    for item in diff_items:
        if item.category == DiffCategory.UNCHANGED:
            unchanged_count += 1
            # No action needed

        elif item.category == DiffCategory.AMOUNT_CHANGED:
            # Update amount only -- NO is_doubt flag (bug fix from V1)
            service.table("extracted_line_items").update(
                {"amount": item.audited_amount}
            ).eq("id", item.provisional_item_id).execute()
            updated_count += 1

        elif item.category == DiffCategory.DESC_CHANGED:
            # Update source_text + amount on the provisional item
            service.table("extracted_line_items").update(
                {
                    "source_text": item.audited_desc,
                    "amount": item.audited_amount,
                }
            ).eq("id", item.provisional_item_id).execute()
            updated_count += 1

            if item.match_score < FUZZY_HIGH_THRESHOLD:
                # Score 75-89: flag classification for review
                clf_result = (
                    service.table("classifications")
                    .select("id")
                    .eq("line_item_id", item.provisional_item_id)
                    .execute()
                )
                clf_ids = [r["id"] for r in (clf_result.data or [])]
                if clf_ids:
                    service.table("classifications").update(
                        {
                            "status": "needs_review",
                            "doubt_reason": (
                                f"Description changed in audited conversion "
                                f"(fuzzy score {item.match_score:.0f})"
                            ),
                        }
                    ).in_("id", clf_ids).execute()
                    flagged_for_review += len(clf_ids)
            # Score >=90: keep classification as-is

        elif item.category == DiffCategory.ADDED:
            # Insert new line item for the provisional document, mark for classification
            service.table("extracted_line_items").insert(
                {
                    "document_id": request.provisional_doc_id,
                    "source_text": item.audited_desc,
                    "amount": item.audited_amount,
                    "is_verified": False,
                    "section": "",
                    "raw_text": item.audited_desc or "",
                }
            ).execute()
            added_count += 1

        elif item.category == DiffCategory.REMOVED:
            # Mark provisional item as unverified
            service.table("extracted_line_items").update(
                {"is_verified": False}
            ).eq("id", item.provisional_item_id).execute()
            removed_count += 1

    # Supersede provisional doc
    service.table("documents").update(
        {
            "superseded_at": now,
            "superseded_by": request.audited_doc_id,
        }
    ).eq("id", request.provisional_doc_id).execute()

    # Mark audited doc with parent reference
    service.table("documents").update(
        {
            "parent_document_id": request.provisional_doc_id,
            "version_number": 2,
        }
    ).eq("id", request.audited_doc_id).execute()

    # Update cma_reports.document_ids: swap provisional -> audited
    try:
        report_result = (
            service.table("cma_reports")
            .select("document_ids")
            .eq("id", request.cma_report_id)
            .single()
            .execute()
        )
        if report_result.data:
            doc_ids = report_result.data.get("document_ids", [])
            new_doc_ids = [
                request.audited_doc_id if did == request.provisional_doc_id else did
                for did in doc_ids
            ]
            service.table("cma_reports").update(
                {"document_ids": new_doc_ids}
            ).eq("id", request.cma_report_id).execute()
    except APIError:
        logger.warning(
            "Could not update cma_reports.document_ids for report %s",
            request.cma_report_id,
        )

    # Record conversion_event
    try:
        service.table("conversion_events").insert(
            {
                "provisional_doc_id": request.provisional_doc_id,
                "audited_doc_id": request.audited_doc_id,
                "cma_report_id": request.cma_report_id,
                "performed_by": user_id,
                "performed_at": now,
                "summary": {
                    "unchanged": unchanged_count,
                    "amount_changed": updated_count,
                    "desc_changed": sum(
                        1 for d in diff_items if d.category == DiffCategory.DESC_CHANGED
                    ),
                    "added": added_count,
                    "removed": removed_count,
                    "flagged_for_review": flagged_for_review,
                },
            }
        ).execute()
    except Exception as exc:
        logger.warning("Could not record conversion_event: %s", exc)

    # Rich audit log with diff summary counts
    audit_service.log_action(
        service,
        user_id,
        "conversion_confirmed",
        "cma_report",
        request.cma_report_id,
        before={
            "provisional_doc_id": request.provisional_doc_id,
            "nature": "provisional",
        },
        after={
            "audited_doc_id": request.audited_doc_id,
            "nature": "audited",
            "summary": {
                "unchanged": unchanged_count,
                "amount_changed": updated_count,
                "desc_changed": sum(
                    1 for d in diff_items if d.category == DiffCategory.DESC_CHANGED
                ),
                "added": added_count,
                "removed": removed_count,
                "flagged_for_review": flagged_for_review,
            },
            "updated_count": updated_count,
            "flagged_for_review": flagged_for_review,
        },
    )

    return ConversionConfirmResponse(
        status="ok",
        updated_count=updated_count,
        flagged_for_review=flagged_for_review,
    )
