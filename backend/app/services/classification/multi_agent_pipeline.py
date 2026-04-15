"""Multi-agent CMA classification pipeline orchestrator.

Replaces the single-agent ClassificationPipeline with a four-specialist
parallel architecture:

  1. Check learned_mappings  → classify immediately (confidence=1.0)
  2. RouterAgent             → assign remaining items to 4 buckets
  3. 4 Specialist agents     → classify in parallel (ThreadPoolExecutor)
  4. Combine + batch-insert  → write all records to DB in one pass

Unrouted items and specialist failures produce doubt records instead of
silent failures, satisfying the CMA constraint: "Doubt items ALWAYS
flagged — NEVER silent guessing."
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from app.dependencies import get_service_client
from app.mappings.year_columns import get_year_column
from app.services.classification.agents.router import RouterAgent
from app.services.classification.agents.pl_income import PLIncomeAgent
from app.services.classification.agents.pl_expense import PLExpenseAgent
from app.services.classification.agents.bs_liability import BSLiabilityAgent
from app.services.classification.agents.bs_asset import BSAssetAgent
from app.services.extraction._types import normalize_line_text

logger = logging.getLogger(__name__)

# ── Thresholds ────────────────────────────────────────────────────────────────

AUTO_APPROVE_THRESHOLD: float = 0.85
HIGH_CONFIDENCE_FLOOR: float = 0.85
DOUBT_THRESHOLD: float = 0.80
MAX_TOKENS_PER_RUN: int = 500_000
MAX_ITEMS_PER_DOCUMENT: int = 500

# DB pagination page size
_PAGE: int = 1000
# Batch insert size
_BATCH_SIZE: int = 200


class MultiAgentPipeline:
    """Orchestrates learned-mapping check → router → 4 specialists → DB insert.

    Usage
    -----
    pipeline = MultiAgentPipeline()
    summary = pipeline.classify_document(
        document_id=...,
        client_id=...,
        industry_type="manufacturing",
        document_type="annual_report",
        financial_year=2024,
    )
    """

    def __init__(self) -> None:
        self._router = RouterAgent()
        self._specialists: dict[str, Any] = {
            "pl_income": PLIncomeAgent(),
            "pl_expense": PLExpenseAgent(),
            "bs_liability": BSLiabilityAgent(),
            "bs_asset": BSAssetAgent(),
        }
        self._total_tokens: int = 0

    # =========================================================================
    # Public entry point
    # =========================================================================

    def classify_document(
        self,
        document_id: str,
        client_id: str,
        industry_type: str,
        document_type: str,
        financial_year: int,
    ) -> dict:
        """Classify all verified line items for *document_id*.

        Returns
        -------
        Summary dict: total, high_confidence, medium_confidence, needs_review.
        """
        self._total_tokens = 0

        cma_column: str = get_year_column(financial_year, financial_year) or "B"
        service = get_service_client()

        # ── 1. Learned mappings ───────────────────────────────────────────────
        learned_mappings = self._fetch_learned_mappings(service, industry_type)

        # ── 2. Cross-document note awareness ─────────────────────────────────
        has_note_breakdowns = self._check_note_breakdowns(
            service, document_id, client_id, financial_year
        )

        # ── 3. Fetch all verified line items ──────────────────────────────────
        line_items = self._fetch_items(service, document_id)

        if not line_items:
            logger.info("[MultiAgentPipeline] No verified items for doc=%s", document_id)
            return {"total": 0, "high_confidence": 0, "medium_confidence": 0, "needs_review": 0}

        # Attach note-breakdown flag to every item so specialists can use it
        for item in line_items:
            item["has_note_breakdowns"] = has_note_breakdowns

        # ── 4. Learned-mapping check ──────────────────────────────────────────
        lm_result = self._check_learned_mappings(line_items, learned_mappings)
        matched_items = lm_result["matched"]
        remaining_items = lm_result["remaining"]

        # Build records for learned-mapping hits
        learned_records: list[dict] = []
        for hit in matched_items:
            classification = {
                "cma_code": hit["cma_field_name"],
                "cma_row": hit["cma_row"],
                "confidence": 1.0,
                "alternatives": [],
                "reasoning": None,
            }
            record = self._build_record(
                item=hit["item"],
                classification=classification,
                client_id=client_id,
                cma_column=cma_column,
                method="learned_mapping",
            )
            learned_records.append(record)

        # ── 5. Route remaining items ──────────────────────────────────────────
        specialist_records: list[dict] = []
        doubt_records: list[dict] = []

        if remaining_items:
            buckets, router_tokens = self._router.route(
                remaining_items, industry_type, document_type
            )
            self._total_tokens += router_tokens

            # Items the router could not assign → doubt
            for item in self._router.last_unrouted:
                doubt_records.append(
                    self._build_record(
                        item=item,
                        classification={
                            "cma_code": "DOUBT",
                            "cma_row": 0,
                            "confidence": 0.0,
                            "alternatives": [],
                            "reasoning": "Item could not be routed to a specialist bucket",
                        },
                        client_id=client_id,
                        cma_column=cma_column,
                        method="router_unrouted",
                    )
                )

            # ── 6. Specialist agents in parallel ─────────────────────────────
            specialist_records = self._run_specialists(
                buckets=buckets,
                industry_type=industry_type,
                client_id=client_id,
                cma_column=cma_column,
                document_type=document_type,
            )

        # ── 7. Combine all records ────────────────────────────────────────────
        all_records = self._combine_results(learned_records, specialist_records, doubt_records)

        # ── 8. Batch insert ───────────────────────────────────────────────────
        self._batch_insert(service, all_records)

        logger.info(
            "[MultiAgentPipeline] doc=%s total=%d tokens=%d",
            document_id,
            len(all_records),
            self._total_tokens,
        )

        return self._summarize(all_records)

    # =========================================================================
    # Pure logic helpers (tested directly — no DB dependency)
    # =========================================================================

    def _check_learned_mappings(
        self,
        items: list[dict],
        learned_mappings: list[dict],
    ) -> dict:
        """Split *items* into learned-mapping hits and remaining unknowns.

        Parameters
        ----------
        items:
            Extracted line item dicts (must have ``source_text`` or
            ``description``).
        learned_mappings:
            Rows from the ``learned_mappings`` table:
            [{source_text, cma_field_name, cma_input_row}, ...].

        Returns
        -------
        {
            "matched": [{"item": item, "cma_row": int, "cma_field_name": str}],
            "remaining": [item, ...],
        }
        """
        # Build normalized lookup: lower-stripped text → mapping row
        # Skip poisoned entries (cma_input_row=0 or UNCLASSIFIED) — these are
        # DOUBT items that were incorrectly saved to learned_mappings
        lookup: dict[str, dict] = {}
        for mapping in learned_mappings:
            row = mapping.get("cma_input_row", 0)
            field = mapping.get("cma_field_name", "")
            if not row or row <= 0 or field == "UNCLASSIFIED":
                continue
            raw = mapping.get("source_text") or ""
            key = normalize_line_text(raw).strip().lower()
            if key:
                lookup[key] = mapping

        matched: list[dict] = []
        remaining: list[dict] = []

        for item in items:
            raw = item.get("source_text") or item.get("description") or ""
            key = normalize_line_text(raw).strip().lower()
            if key and key in lookup:
                mapping = lookup[key]
                matched.append(
                    {
                        "item": item,
                        "cma_row": mapping.get("cma_input_row", 0),
                        "cma_field_name": mapping.get("cma_field_name", "UNCLASSIFIED"),
                    }
                )
            else:
                remaining.append(item)

        return {"matched": matched, "remaining": remaining}

    def _build_record(
        self,
        item: dict,
        classification: dict,
        client_id: str,
        cma_column: str,
        method: str,
    ) -> dict:
        """Build a DB-ready classification record from an agent response dict.

        Parameters
        ----------
        classification:
            Dict with keys: cma_code, cma_row, confidence, alternatives,
            reasoning.  ``cma_code`` of ``"DOUBT"`` or ``cma_row`` of 0
            triggers an is_doubt record.
        """
        cma_code: str = classification.get("cma_code") or "UNCLASSIFIED"
        cma_row: int = int(classification.get("cma_row") or 0)
        confidence: float = float(classification.get("confidence") or 0.0)

        is_doubt: bool = (
            cma_row == 0
            or cma_code == "DOUBT"
            or confidence < DOUBT_THRESHOLD
        )

        if is_doubt:
            status = "needs_review"
        elif confidence >= AUTO_APPROVE_THRESHOLD:
            status = "approved"
        else:
            status = "auto_classified"

        return {
            "line_item_id": item["id"],
            "client_id": client_id,
            "cma_field_name": "UNCLASSIFIED" if is_doubt else cma_code,
            "cma_sheet": "input_sheet",
            "cma_row": 0 if is_doubt else cma_row,
            "cma_column": cma_column,
            "broad_classification": None,
            "classification_method": method,
            "confidence_score": confidence,
            "fuzzy_match_score": 0,
            "is_doubt": is_doubt,
            "doubt_reason": classification.get("reasoning") if is_doubt else None,
            "ai_best_guess": cma_code,
            "alternative_fields": classification.get("alternatives") or [],
            "status": status,
            "cell_note": classification.get("cell_note"),
        }

    def _combine_results(
        self,
        learned: list[dict],
        specialist: list[dict],
        doubts: list[dict],
    ) -> list[dict]:
        """Concatenate learned-mapping, specialist, and doubt records."""
        return learned + specialist + doubts

    def _summarize(self, records: list[dict]) -> dict:
        """Count high_confidence, medium_confidence, and needs_review buckets."""
        high_confidence = 0
        medium_confidence = 0
        needs_review = 0

        for rec in records:
            if rec.get("is_doubt"):
                needs_review += 1
            elif (rec.get("confidence_score") or 0.0) >= HIGH_CONFIDENCE_FLOOR:
                high_confidence += 1
            else:
                medium_confidence += 1

        return {
            "total": len(records),
            "high_confidence": high_confidence,
            "medium_confidence": medium_confidence,
            "needs_review": needs_review,
        }

    def _run_specialists(
        self,
        buckets: dict[str, list[dict]],
        industry_type: str,
        client_id: str,
        cma_column: str,
        document_type: str = "annual_report",
    ) -> list[dict]:
        """Run the four specialist agents in parallel and collect records.

        Any specialist that raises an exception has all its items converted to
        doubt records so classification of the remaining buckets continues.

        Returns
        -------
        Flat list of DB-ready classification record dicts.
        """
        records: list[dict] = []

        # Only submit non-empty buckets
        non_empty = {k: v for k, v in buckets.items() if v}
        if not non_empty:
            return records

        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_bucket: dict = {}
            for bucket_name, items in non_empty.items():
                agent = self._specialists.get(bucket_name)
                if agent is None:
                    logger.warning(
                        "[MultiAgentPipeline] No specialist for bucket '%s' — doubting %d items",
                        bucket_name,
                        len(items),
                    )
                    for item in items:
                        records.append(
                            self._build_record(
                                item=item,
                                classification={
                                    "cma_code": "DOUBT",
                                    "cma_row": 0,
                                    "confidence": 0.0,
                                    "alternatives": [],
                                    "reasoning": f"No specialist agent for bucket '{bucket_name}'",
                                },
                                client_id=client_id,
                                cma_column=cma_column,
                                method=f"{bucket_name}_no_agent",
                            )
                        )
                    continue

                future = executor.submit(agent.classify_batch, items, industry_type, document_type)
                future_to_bucket[future] = (bucket_name, items)

            for future in as_completed(future_to_bucket):
                bucket_name, items = future_to_bucket[future]
                try:
                    classifications, tokens = future.result()
                    self._total_tokens += tokens

                    # Build a lookup: item id → original item dict
                    item_by_id = {item["id"]: item for item in items}

                    for clf in classifications:
                        item_id = clf.get("id")
                        item = item_by_id.get(item_id)
                        if item is None:
                            logger.warning(
                                "[MultiAgentPipeline] Specialist '%s' returned unknown id '%s'",
                                bucket_name,
                                item_id,
                            )
                            continue

                        # Map specialist response shape to _build_record shape
                        mapped_clf = {
                            "cma_code": clf.get("cma_code", "DOUBT"),
                            "cma_row": clf.get("cma_row", 0),
                            "confidence": clf.get("confidence", 0.0),
                            "alternatives": clf.get("alternatives", []),
                            "reasoning": clf.get("reasoning"),
                            "cell_note": clf.get("cell_note"),
                        }
                        record = self._build_record(
                            item=item,
                            classification=mapped_clf,
                            client_id=client_id,
                            cma_column=cma_column,
                            method=bucket_name,
                        )
                        records.append(record)

                except Exception as exc:
                    logger.error(
                        "[MultiAgentPipeline] Specialist '%s' raised %s: %s — doubting %d items",
                        bucket_name,
                        type(exc).__name__,
                        exc,
                        len(items),
                    )
                    for item in items:
                        records.append(
                            self._build_record(
                                item=item,
                                classification={
                                    "cma_code": "DOUBT",
                                    "cma_row": 0,
                                    "confidence": 0.0,
                                    "alternatives": [],
                                    "reasoning": (
                                        f"Specialist '{bucket_name}' failed: "
                                        f"{type(exc).__name__} — classify manually"
                                    ),
                                },
                                client_id=client_id,
                                cma_column=cma_column,
                                method=f"{bucket_name}_error",
                            )
                        )

        return records

    # =========================================================================
    # DB helpers
    # =========================================================================

    def _fetch_learned_mappings(self, service: Any, industry_type: str) -> list[dict]:
        """Fetch learned_mappings for *industry_type*; returns [] on error."""
        try:
            resp = (
                service.table("learned_mappings")
                .select("source_text,cma_field_name,cma_input_row")
                .eq("industry_type", industry_type)
                .execute()
            )
            return resp.data or []
        except Exception as exc:
            logger.warning("[MultiAgentPipeline] Could not fetch learned_mappings: %s", exc)
            return []

    def _check_note_breakdowns(
        self,
        service: Any,
        document_id: str,
        client_id: str,
        financial_year: int,
    ) -> bool:
        """Return True if any verified notes items exist across sibling documents."""
        try:
            sibling_resp = (
                service.table("documents")
                .select("id")
                .eq("client_id", client_id)
                .eq("financial_year", financial_year)
                .neq("id", document_id)
                .execute()
            )
            sibling_ids = [d["id"] for d in (sibling_resp.data or [])]

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
            has_notes = (notes_check.count or 0) > 0
            if has_notes:
                logger.info(
                    "[MultiAgentPipeline] Notes breakdowns found: client=%s year=%s",
                    client_id,
                    financial_year,
                )
            return has_notes
        except Exception as exc:
            logger.warning(
                "[MultiAgentPipeline] Cross-doc awareness query failed: %s — proceeding without",
                exc,
            )
            return False

    def _fetch_items(self, service: Any, document_id: str) -> list[dict]:
        """Fetch all verified line items for *document_id* (paginated)."""
        items: list[dict] = []
        offset = 0
        while True:
            try:
                page = (
                    service.table("extracted_line_items")
                    .select("*")
                    .eq("document_id", document_id)
                    .eq("is_verified", True)
                    .range(offset, offset + _PAGE - 1)
                    .execute()
                )
            except Exception as exc:
                logger.error(
                    "[MultiAgentPipeline] Failed to fetch items (offset=%d): %s",
                    offset,
                    exc,
                )
                break

            batch = page.data or []
            items.extend(batch)
            if len(batch) < _PAGE:
                break
            offset += _PAGE

        return items

    def _batch_insert(self, service: Any, records: list[dict]) -> None:
        """Insert *records* into the classifications table in batches of 200."""
        for i in range(0, len(records), _BATCH_SIZE):
            batch = records[i : i + _BATCH_SIZE]
            try:
                service.table("classifications").insert(batch).execute()
            except Exception as exc:
                logger.error(
                    "[MultiAgentPipeline] Batch insert failed (offset=%d, size=%d): %s",
                    i,
                    len(batch),
                    exc,
                )
