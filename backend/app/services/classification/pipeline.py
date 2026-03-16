"""3-tier classification pipeline orchestrator.

Tier 1 — Fuzzy match (score >= 85):  auto_classified, no AI call
Tier 2 — AI Haiku (confidence >= 0.8): auto_classified
Tier 3 — Doubt report:                 needs_review, is_doubt=True

Every item gets classified OR doubted — nothing left in 'pending' state.
"""

from __future__ import annotations

import logging

from app.dependencies import get_service_client
from app.mappings.year_columns import YEAR_TO_COLUMN
from app.services.classification.ai_classifier import AIClassifier
from app.services.classification.fuzzy_matcher import FuzzyMatcher

logger = logging.getLogger(__name__)

# Fuzzy score threshold for Tier 1 confident match
FUZZY_TIER1_THRESHOLD = 85.0

# Confidence bucket thresholds for summary reporting
HIGH_CONFIDENCE_FLOOR = 0.85


class ClassificationPipeline:
    """Orchestrates the 3-tier classification pipeline for financial line items."""

    def __init__(self) -> None:
        self._fuzzy = FuzzyMatcher()
        self._ai = AIClassifier()

    def classify_item(
        self,
        item: dict,
        client_id: str,
        industry_type: str,
        document_type: str,
        financial_year: int,
    ) -> dict:
        """Classify a single line item through the 3-tier pipeline.

        Parameters
        ----------
        item:            Extracted line item row (must have 'id', 'description').
        client_id:       Client UUID for the classification record.
        industry_type:   Passed to fuzzy matcher and AI classifier.
        document_type:   e.g. 'profit_and_loss', 'balance_sheet'.
        financial_year:  Used to resolve cma_column (e.g. 2024 → 'C').

        Returns
        -------
        dict ready for insert into the classifications table.
        """
        description: str = item["description"]
        amount: float | None = item.get("amount")
        section: str | None = item.get("section")
        cma_column: str = YEAR_TO_COLUMN.get(financial_year, "B")

        # ── Tier 1: Fuzzy matching ────────────────────────────────────────────
        fuzzy_results = self._fuzzy.match(description, industry_type)
        best_fuzzy = fuzzy_results[0] if fuzzy_results else None

        if best_fuzzy and best_fuzzy.score >= FUZZY_TIER1_THRESHOLD:
            method = "learned" if best_fuzzy.source == "learned" else "fuzzy_match"
            logger.debug(
                "Tier 1 match: '%s' → %s (score=%.1f)",
                description,
                best_fuzzy.cma_field_name,
                best_fuzzy.score,
            )
            return {
                "line_item_id": item["id"],
                "client_id": client_id,
                "cma_field_name": best_fuzzy.cma_field_name,
                "cma_sheet": best_fuzzy.cma_sheet,
                "cma_row": best_fuzzy.cma_row,
                "cma_column": cma_column,
                "broad_classification": best_fuzzy.broad_classification,
                "classification_method": method,
                "confidence_score": round(best_fuzzy.score / 100.0, 4),
                "fuzzy_match_score": best_fuzzy.score,
                "is_doubt": False,
                "doubt_reason": None,
                "ai_best_guess": best_fuzzy.cma_field_name,
                "alternative_fields": [
                    {
                        "cma_field_name": r.cma_field_name,
                        "cma_row": r.cma_row,
                        "score": r.score,
                    }
                    for r in fuzzy_results[1:3]
                ],
                "status": "auto_classified",
            }

        # ── Tier 2: AI classification ─────────────────────────────────────────
        ai_result = self._ai.classify(
            raw_text=description,
            amount=amount,
            section=section,
            industry_type=industry_type,
            document_type=document_type,
            fuzzy_candidates=fuzzy_results,
        )

        fuzzy_score = best_fuzzy.score if best_fuzzy else 0.0

        if not ai_result.is_doubt:
            logger.debug(
                "Tier 2 match: '%s' → %s (confidence=%.2f)",
                description,
                ai_result.cma_field_name,
                ai_result.confidence,
            )
            return {
                "line_item_id": item["id"],
                "client_id": client_id,
                "cma_field_name": ai_result.cma_field_name,
                "cma_sheet": ai_result.cma_sheet,
                "cma_row": ai_result.cma_row,
                "cma_column": cma_column,
                "broad_classification": ai_result.broad_classification,
                "classification_method": "ai_haiku",
                "confidence_score": ai_result.confidence,
                "fuzzy_match_score": fuzzy_score,
                "is_doubt": False,
                "doubt_reason": None,
                "ai_best_guess": ai_result.cma_field_name,
                "alternative_fields": [
                    c.model_dump() for c in (ai_result.alternatives or [])
                ],
                "status": "auto_classified",
            }

        # ── Tier 3: Doubt report ──────────────────────────────────────────────
        logger.info(
            "Tier 3 doubt: '%s' — %s",
            description,
            ai_result.doubt_reason,
        )
        return {
            "line_item_id": item["id"],
            "client_id": client_id,
            "cma_field_name": None,
            "cma_sheet": "input_sheet",
            "cma_row": None,
            "cma_column": cma_column,
            "broad_classification": None,
            "classification_method": "ai_haiku",
            "confidence_score": ai_result.confidence,
            "fuzzy_match_score": fuzzy_score,
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

        Returns
        -------
        Summary dict: total, high_confidence, medium_confidence, needs_review.
        """
        service = get_service_client()

        # Fetch all verified line items for the document
        items_result = (
            service.table("extracted_line_items")
            .select("*")
            .eq("document_id", document_id)
            .eq("is_verified", True)
            .execute()
        )
        line_items = items_result.data or []

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
                    exc,
                )
                # On item-level error, create a doubt record so nothing is lost
                service.table("classifications").insert(
                    {
                        "line_item_id": item["id"],
                        "client_id": client_id,
                        "cma_field_name": None,
                        "cma_sheet": "input_sheet",
                        "cma_row": None,
                        "cma_column": YEAR_TO_COLUMN.get(financial_year, "B"),
                        "broad_classification": None,
                        "classification_method": None,
                        "confidence_score": 0.0,
                        "fuzzy_match_score": 0.0,
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
