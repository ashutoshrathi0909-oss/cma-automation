"""Classification pipeline orchestrator — AI-only (April 2026).

All items are classified by the ScopedClassifier (DeepSeek V3 via OpenRouter).
The previous 5-tier pipeline (regex → golden rules → fuzzy → AI → doubt) has
been removed. Rules now serve as AI reference context, not deterministic
lookup tables.

Every item gets classified OR doubted — nothing left in 'pending' state.
"""

from __future__ import annotations

import logging

from app.config import get_settings
from app.dependencies import get_service_client
from app.mappings.year_columns import get_year_column
from app.services.classification.scoped_classifier import ScopedClassifier
from app.services.extraction._types import normalize_line_text

logger = logging.getLogger(__name__)

# Confidence bucket thresholds for summary reporting
HIGH_CONFIDENCE_FLOOR = 0.85

# Items at or above this threshold are silently approved during classification.
# The CA never sees them in the review queue (unless they toggle "Show All").
# Items between 0.80–0.84 stay as "auto_classified" for optional CA review.
AUTO_APPROVE_THRESHOLD = 0.85


def _auto_status(confidence: float) -> str:
    """Return 'approved' for high confidence, 'auto_classified' for medium."""
    return "approved" if confidence >= AUTO_APPROVE_THRESHOLD else "auto_classified"


class ClassificationPipeline:
    """Orchestrates AI-only classification for financial line items."""

    def __init__(self) -> None:
        settings = get_settings()
        if settings.classifier_mode == "legacy":
            logger.warning(
                "classifier_mode='legacy' is deprecated (April 2026). "
                "Using ScopedClassifier. Update config to classifier_mode='scoped'."
            )
        self._ai = ScopedClassifier()

    def classify_item(
        self,
        item: dict,
        client_id: str,
        industry_type: str,
        document_type: str,
        financial_year: int,
        has_note_breakdowns: bool = False,
    ) -> dict:
        """Classify a single line item via AI.

        Parameters
        ----------
        item:            Extracted line item row (must have 'id', 'description').
        client_id:       Client UUID for the classification record.
        industry_type:   Passed to the AI classifier for context filtering.
        document_type:   e.g. 'profit_and_loss', 'balance_sheet'.
        financial_year:  Used to resolve cma_column (e.g. 2024 → 'B').

        Returns
        -------
        dict ready for insert into the classifications table.
        """
        # DB stores the text as 'source_text'; API layer maps it to 'description'
        raw_desc: str = item.get("source_text") or item.get("description") or ""
        description: str = normalize_line_text(raw_desc)
        amount: float | None = item.get("amount")
        section: str | None = item.get("section")
        page_type: str | None = item.get("page_type")
        cma_column: str = get_year_column(financial_year, financial_year) or "B"

        # ── AI classification (single tier) ───────────────────────────────────
        try:
            ai_result = self._ai.classify_sync(
                raw_text=description,
                amount=amount,
                section=section,
                industry_type=industry_type,
                document_type=document_type,
                fuzzy_candidates=[],
                page_type=page_type,
                has_note_breakdowns=has_note_breakdowns,
            )
        except Exception as exc:
            logger.error(
                "classify_item AI call failed for '%s': %s",
                description, type(exc).__name__,
            )
            return {
                "line_item_id": item["id"],
                "client_id": client_id,
                "cma_field_name": "UNCLASSIFIED",
                "cma_sheet": "input_sheet",
                "cma_row": 0,
                "cma_column": cma_column,
                "broad_classification": None,
                "classification_method": "scoped_doubt",
                "confidence_score": 0.0,
                "fuzzy_match_score": 0,
                "is_doubt": True,
                "doubt_reason": f"Classification error: {type(exc).__name__}",
                "ai_best_guess": None,
                "alternative_fields": [],
                "status": "needs_review",
            }

        if not ai_result.is_doubt:
            logger.debug(
                "AI classified: '%s' → %s (confidence=%.2f)",
                description, ai_result.cma_field_name, ai_result.confidence,
            )
            return {
                "line_item_id": item["id"],
                "client_id": client_id,
                "cma_field_name": ai_result.cma_field_name,
                "cma_sheet": ai_result.cma_sheet,
                "cma_row": int(ai_result.cma_row) if ai_result.cma_row is not None else 0,
                "cma_column": cma_column,
                "broad_classification": ai_result.broad_classification,
                "classification_method": ai_result.classification_method,
                "confidence_score": ai_result.confidence,
                "fuzzy_match_score": 0,
                "is_doubt": False,
                "doubt_reason": None,
                "ai_best_guess": ai_result.cma_field_name,
                "alternative_fields": [
                    c.model_dump() for c in (ai_result.alternatives or [])
                ],
                "status": _auto_status(ai_result.confidence),
            }

        # ── Doubt ─────────────────────────────────────────────────────────────
        logger.info("Doubt: '%s' — %s", description, ai_result.doubt_reason)
        return {
            "line_item_id": item["id"],
            "client_id": client_id,
            "cma_field_name": ai_result.cma_field_name or "UNCLASSIFIED",
            "cma_sheet": "input_sheet",
            "cma_row": 0,
            "cma_column": cma_column,
            "broad_classification": None,
            "classification_method": ai_result.classification_method,
            "confidence_score": ai_result.confidence,
            "fuzzy_match_score": 0,
            "is_doubt": True,
            "doubt_reason": ai_result.doubt_reason,
            "ai_best_guess": ai_result.cma_field_name,
            "alternative_fields": [
                c.model_dump() for c in (ai_result.alternatives or [])
            ],
            "status": "needs_review",
        }

    def classify_document(
        self,
        document_id: str,
        client_id: str,
        industry_type: str,
        document_type: str,
        financial_year: int,
    ) -> dict:
        """Classify all verified line items for a document.

        Fetches learned_mappings once (cached for the run) and passes
        them to the ScopedClassifier so the AI sees CA corrections.

        Returns
        -------
        Summary dict: total, high_confidence, medium_confidence, needs_review.
        """
        service = get_service_client()

        # Pre-fetch learned mappings for this industry (one DB call, not N)
        try:
            learned_resp = (
                service.table("learned_mappings")
                .select("source_text,cma_field_name,cma_input_row")
                .eq("industry_type", industry_type)
                .execute()
            )
            self._ai.set_learned_cache(learned_resp.data or [])
        except Exception as exc:
            logger.warning("Could not fetch learned_mappings: %s", exc)
            self._ai.set_learned_cache([])

        # ── Cross-document awareness: check for existing notes items ──────────
        # If notes/schedule breakdown items exist (in this or sibling documents),
        # face sheet totals should be skipped (cma_row=0) to prevent double-counting.
        has_note_breakdowns = False
        try:
            # Check sibling documents (same client + financial year, different doc)
            sibling_docs = (
                service.table("documents")
                .select("id")
                .eq("client_id", client_id)
                .eq("financial_year", financial_year)
                .neq("id", document_id)
                .execute()
            )
            sibling_ids = [d["id"] for d in (sibling_docs.data or [])]

            # Check current document + siblings for notes items
            all_doc_ids = [document_id] + sibling_ids
            notes_check = (
                service.table("extracted_line_items")
                .select("id", count="exact")
                .in_("document_id", all_doc_ids)
                .eq("page_type", "notes")
                .eq("is_verified", True)
                .limit(1)
                .execute()
            )
            has_note_breakdowns = (notes_check.count or 0) > 0
            if has_note_breakdowns:
                logger.info(
                    "Cross-doc awareness: notes breakdowns found for client=%s year=%s — "
                    "face sheet totals will be flagged for skipping",
                    client_id, financial_year,
                )
        except Exception as exc:
            logger.warning("Cross-doc awareness query failed: %s — proceeding without", exc)

        # Fetch all verified line items, paginated to bypass the 1000-row default limit
        _PAGE = 1000
        line_items: list[dict] = []
        offset = 0
        while True:
            page = (
                service.table("extracted_line_items")
                .select("*")
                .eq("document_id", document_id)
                .eq("is_verified", True)
                .range(offset, offset + _PAGE - 1)
                .execute()
            )
            batch = page.data or []
            line_items.extend(batch)
            if len(batch) < _PAGE:
                break
            offset += _PAGE

        total = len(line_items)
        high_confidence = 0
        medium_confidence = 0
        needs_review = 0

        for item in line_items:
            try:
                classification = self.classify_item(
                    item=item,
                    client_id=client_id,
                    industry_type=industry_type,
                    document_type=document_type,
                    financial_year=financial_year,
                    has_note_breakdowns=has_note_breakdowns,
                )
                service.table("classifications").insert(classification).execute()

                # Bucket the result for summary
                if classification["is_doubt"]:
                    needs_review += 1
                elif (classification.get("confidence_score") or 0.0) >= HIGH_CONFIDENCE_FLOOR:
                    high_confidence += 1
                else:
                    medium_confidence += 1

            except Exception as exc:
                logger.error(
                    "classify_document failed for item_id=%s: %s",
                    item.get("id"),
                    type(exc).__name__,
                )
                # On item-level error, create a doubt record so nothing is lost
                service.table("classifications").insert(
                    {
                        "line_item_id": item["id"],
                        "client_id": client_id,
                        "cma_field_name": "UNCLASSIFIED",
                        "cma_sheet": "input_sheet",
                        "cma_row": 0,
                        "cma_column": get_year_column(financial_year, financial_year) or "B",
                        "broad_classification": None,
                        "classification_method": "manual",
                        "confidence_score": 0.0,
                        "fuzzy_match_score": 0,
                        "is_doubt": True,
                        "doubt_reason": f"Classification error: {type(exc).__name__}",
                        "ai_best_guess": None,
                        "alternative_fields": [],
                        "status": "needs_review",
                    }
                ).execute()
                needs_review += 1

        logger.info(
            "classify_document complete: doc=%s total=%d high=%d medium=%d doubt=%d",
            document_id,
            total,
            high_confidence,
            medium_confidence,
            needs_review,
        )

        return {
            "total": total,
            "high_confidence": high_confidence,
            "medium_confidence": medium_confidence,
            "needs_review": needs_review,
        }
