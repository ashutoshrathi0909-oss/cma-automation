"""Classification pipeline orchestrator.

Tier 0a — Deterministic regex rules: hard-coded pattern matches
Tier 0b — Golden rule lookup: exact + fuzzy match against 594 CA-verified rules
Tier 1  — Fuzzy match (score >= 85):  auto_classified, no AI call
Tier 2  — AI Haiku (confidence >= 0.8): auto_classified
Tier 3  — Doubt report:                 needs_review, is_doubt=True

Every item gets classified OR doubted — nothing left in 'pending' state.
"""

from __future__ import annotations

import logging
import os

from app.config import get_settings
from app.dependencies import get_service_client
from app.mappings.year_columns import get_year_column
from app.services.classification.ai_classifier import AIClassifier
from app.services.classification.fuzzy_matcher import FuzzyMatcher
from app.services.classification.scoped_classifier import ScopedClassifier
from app.services.classification.rule_engine import (
    GoldenRuleLookup,
    GoldenRuleResult,
    RuleEngine,
    RuleMatchResult,
)
from app.services.extraction._types import normalize_line_text

logger = logging.getLogger(__name__)

# Set SKIP_AI_CLASSIFICATION=true to skip Tier 2 AI calls (fuzzy + doubt only).
# Useful for testing or when Anthropic API budget is limited.
_SKIP_AI = os.getenv("SKIP_AI_CLASSIFICATION", "false").lower() == "true"

# Fuzzy score threshold for Tier 1 confident match
FUZZY_TIER1_THRESHOLD = 85.0

# Confidence bucket thresholds for summary reporting
HIGH_CONFIDENCE_FLOOR = 0.85

# Items at or above this threshold are silently approved during classification.
# The CA never sees them in the review queue (unless they toggle "Show All").
# Items between 0.80–0.84 stay as "auto_classified" for optional CA review.
AUTO_APPROVE_THRESHOLD = 0.85


def _auto_status(confidence: float) -> str:
    """Return 'approved' for high confidence, 'auto_classified' for medium."""
    return "approved" if confidence >= AUTO_APPROVE_THRESHOLD else "auto_classified"


def _doc_type_to_sheet(document_type: str) -> str | None:
    """Map document_type to golden rule source_sheet ('pl' or 'bs').

    Returns None for document types that don't map cleanly to pl/bs
    (e.g. notes_to_accounts, schedules).
    """
    dt = (document_type or "").lower()
    if "profit" in dt or dt == "pl":
        return "pl"
    if "balance" in dt or dt == "bs":
        return "bs"
    return None  # combined, notes, schedules — don't filter by sheet


class ClassificationPipeline:
    """Orchestrates the 3-tier classification pipeline for financial line items."""

    def __init__(self) -> None:
        self._rules = RuleEngine()
        self._golden = GoldenRuleLookup()
        self._fuzzy = FuzzyMatcher()
        settings = get_settings()
        if settings.classifier_mode == "legacy":
            from app.services.classification.ai_classifier import AIClassifier
            self._ai = AIClassifier()
            self._use_sync = False
        else:
            self._ai = ScopedClassifier()
            self._use_sync = True  # scoped uses classify_sync

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
        # DB stores the text as 'source_text'; API layer maps it to 'description'
        raw_desc: str = item.get("source_text") or item.get("description") or ""
        description: str = normalize_line_text(raw_desc)
        amount: float | None = item.get("amount")
        section: str | None = item.get("section")
        cma_column: str = get_year_column(financial_year, financial_year) or "B"

        # Map document_type to source_sheet for golden rule lookup
        source_sheet = _doc_type_to_sheet(document_type)

        # ── Tier 0a: Deterministic regex rules ─────────────────────────────────
        rule_result = self._rules.apply(description, amount, section, industry_type)
        if rule_result:
            logger.info(
                "Tier 0a regex rule: '%s' → %s (rule=%s)",
                description, rule_result.cma_field_name, rule_result.rule_id,
            )
            return {
                "line_item_id": item["id"],
                "client_id": client_id,
                "cma_field_name": rule_result.cma_field_name,
                "cma_sheet": rule_result.cma_sheet,
                "cma_row": rule_result.cma_row,
                "cma_column": cma_column,
                "broad_classification": rule_result.broad_classification,
                "classification_method": f"rule_{rule_result.rule_id}",
                "confidence_score": rule_result.confidence,
                "fuzzy_match_score": 0,
                "is_doubt": False,
                "doubt_reason": None,
                "ai_best_guess": rule_result.cma_field_name,
                "alternative_fields": [],
                "status": _auto_status(rule_result.confidence),
            }

        # ── Tier 0b: Golden rule lookup (594 CA-verified rules) ────────────────
        golden_result = self._golden.find_rule(
            raw_text=description,
            source_sheet=source_sheet,
            industry_type=industry_type,
        )
        if golden_result:
            method = f"rule_engine_{golden_result.priority}"
            # ca_override and ca_interview short-circuit (high confidence)
            # legacy rules pass through to fuzzy for confirmation
            if golden_result.priority in ("ca_override", "ca_interview") and golden_result.confidence >= 0.9:
                logger.info(
                    "Tier 0b golden rule (%s): '%s' → %s (rule=%s, conf=%.2f)",
                    golden_result.priority, description,
                    golden_result.canonical_field_name, golden_result.rule_id,
                    golden_result.confidence,
                )
                return {
                    "line_item_id": item["id"],
                    "client_id": client_id,
                    "cma_field_name": golden_result.canonical_field_name,
                    "cma_sheet": "input_sheet",
                    "cma_row": golden_result.canonical_sheet_row,
                    "cma_column": cma_column,
                    "broad_classification": None,
                    "classification_method": method,
                    "confidence_score": golden_result.confidence,
                    "fuzzy_match_score": 0,
                    "is_doubt": False,
                    "doubt_reason": None,
                    "ai_best_guess": golden_result.canonical_field_name,
                    "alternative_fields": [],
                    "status": _auto_status(golden_result.confidence),
                }
            elif golden_result.priority == "legacy":
                # Legacy rules: log but don't short-circuit; pass to fuzzy for confirmation
                logger.debug(
                    "Tier 0b golden rule (legacy, not short-circuiting): '%s' → %s (rule=%s)",
                    description, golden_result.canonical_field_name, golden_result.rule_id,
                )
            else:
                # ca_interview with confidence < 0.9 — still use it but mark appropriately
                logger.info(
                    "Tier 0b golden rule (%s): '%s' → %s (rule=%s, conf=%.2f)",
                    golden_result.priority, description,
                    golden_result.canonical_field_name, golden_result.rule_id,
                    golden_result.confidence,
                )
                return {
                    "line_item_id": item["id"],
                    "client_id": client_id,
                    "cma_field_name": golden_result.canonical_field_name,
                    "cma_sheet": "input_sheet",
                    "cma_row": golden_result.canonical_sheet_row,
                    "cma_column": cma_column,
                    "broad_classification": None,
                    "classification_method": method,
                    "confidence_score": golden_result.confidence,
                    "fuzzy_match_score": 0,
                    "is_doubt": False,
                    "doubt_reason": None,
                    "ai_best_guess": golden_result.canonical_field_name,
                    "alternative_fields": [],
                    "status": _auto_status(golden_result.confidence),
                }

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
                "cma_row": int(best_fuzzy.cma_row) if best_fuzzy.cma_row is not None else 0,
                "cma_column": cma_column,
                "broad_classification": best_fuzzy.broad_classification,
                "classification_method": method,
                "confidence_score": round(best_fuzzy.score / 100.0, 4),
                "fuzzy_match_score": int(round(best_fuzzy.score)),
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
                "status": _auto_status(round(best_fuzzy.score / 100.0, 4)),
            }

        # ── Tier 2: AI classification ─────────────────────────────────────────
        if _SKIP_AI:
            logger.debug("SKIP_AI_CLASSIFICATION=true — routing '%s' to doubt", description)
            return {
                "line_item_id": item["id"],
                "client_id": client_id,
                "cma_field_name": "UNCLASSIFIED",
                "cma_sheet": "input_sheet",
                "cma_row": 0,
                "cma_column": cma_column,
                "broad_classification": None,
                "classification_method": "manual",
                "confidence_score": 0.0,
                "fuzzy_match_score": int(round(best_fuzzy.score)) if best_fuzzy else 0,
                "is_doubt": True,
                "doubt_reason": "AI classification skipped (SKIP_AI_CLASSIFICATION=true)",
                "ai_best_guess": None,
                "alternative_fields": [],
                "status": "needs_review",
            }

        if self._use_sync:
            ai_result = self._ai.classify_sync(
                raw_text=description,
                amount=amount,
                section=section,
                industry_type=industry_type,
                document_type=document_type,
                fuzzy_candidates=fuzzy_results,
            )
        else:
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
                "cma_row": int(ai_result.cma_row) if ai_result.cma_row is not None else 0,
                "cma_column": cma_column,
                "broad_classification": ai_result.broad_classification,
                "classification_method": ai_result.classification_method,
                "confidence_score": ai_result.confidence,
                "fuzzy_match_score": int(round(fuzzy_score)),
                "is_doubt": False,
                "doubt_reason": None,
                "ai_best_guess": ai_result.cma_field_name,
                "alternative_fields": [
                    c.model_dump() for c in (ai_result.alternatives or [])
                ],
                "status": _auto_status(ai_result.confidence),
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
            "cma_field_name": ai_result.cma_field_name or "UNCLASSIFIED",  # NOT NULL
            "cma_sheet": "input_sheet",
            "cma_row": 0,  # NOT NULL; 0 = unresolved doubt
            "cma_column": cma_column,
            "broad_classification": None,
            "classification_method": ai_result.classification_method,
            "confidence_score": ai_result.confidence,
            "fuzzy_match_score": int(round(fuzzy_score)),
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
                        "cma_field_name": "UNCLASSIFIED",  # NOT NULL
                        "cma_sheet": "input_sheet",
                        "cma_row": 0,  # NOT NULL; 0 = unresolved/error
                        "cma_column": get_year_column(financial_year, financial_year) or "B",
                        "broad_classification": None,
                        "classification_method": "manual",  # NOT NULL column
                        "confidence_score": 0.0,
                        "fuzzy_match_score": 0,  # integer column
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
