"""Tier 1 classification: fuzzy matching against learned and reference mappings.

Priority rule (critical constraint):
  1. Query learned_mappings first (industry-specific, user-corrected)
  2. If best score >= 85: return immediately — never check reference
  3. Otherwise: query cma_reference_mappings (universal 384-item reference)

Uses rapidfuzz token_set_ratio which is word-order insensitive, important for
Indian financial statements where line item phrasing varies across firms.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from rapidfuzz import fuzz, process

from app.dependencies import get_service_client

logger = logging.getLogger(__name__)

# Score threshold above which a fuzzy match is considered confident (Tier 1)
CONFIDENT_THRESHOLD = 85.0


@dataclass
class FuzzyMatchResult:
    """Result of a fuzzy match against the CMA mapping tables."""

    cma_field_name: str
    cma_row: int
    cma_sheet: str  # "input_sheet" or "tl_sheet"
    broad_classification: str
    score: float  # 0–100 (rapidfuzz score)
    source: str  # "learned" or "reference"


class FuzzyMatcher:
    """Matches raw financial line item text against CMA field mappings.

    Checks learned_mappings (user corrections/approvals) BEFORE the universal
    reference table. If a confident match (>= 85) is found in learned, the
    reference table is skipped entirely.

    The reference table (384 static rows) is cached after the first DB fetch
    and reused for all subsequent match() calls on the same instance.
    """

    CONFIDENT_THRESHOLD = CONFIDENT_THRESHOLD

    def __init__(self) -> None:
        # Populated on first call to _fetch_reference_mappings; static data so safe to cache
        self._reference_cache: list[dict] | None = None

    def match(
        self,
        raw_text: str,
        industry_type: str,
        top_n: int = 5,
    ) -> list[FuzzyMatchResult]:
        """Return top-N fuzzy matches for *raw_text*, prioritising learned mappings.

        Parameters
        ----------
        raw_text:       The line item description from the extracted document.
        industry_type:  Industry filter applied to learned_mappings queries.
        top_n:          Maximum results to return.

        Returns
        -------
        Sorted (descending score) list of FuzzyMatchResult. Empty if no data.
        """
        # ── Step 1: Learned mappings (industry-specific, highest priority) ──────
        learned_rows = self._fetch_learned_mappings(industry_type)
        learned_results: list[FuzzyMatchResult] = []

        if learned_rows:
            learned_results = self._match_against_learned(raw_text, learned_rows, top_n)
            best_learned_score = max((r.score for r in learned_results), default=0.0)

            if best_learned_score >= self.CONFIDENT_THRESHOLD:
                # Confident learned match — return immediately, skip reference
                logger.debug(
                    "Learned match (%s) for '%s' (score=%.1f)",
                    learned_results[0].cma_field_name,
                    raw_text,
                    best_learned_score,
                )
                return learned_results[:top_n]

        # ── Step 2: Reference mappings (universal, no industry filter) ───────────
        reference_rows = self._fetch_reference_mappings()
        reference_results: list[FuzzyMatchResult] = []

        if reference_rows:
            reference_results = self._match_against_reference(raw_text, reference_rows, top_n)

        # ── Step 3: Combine, deduplicate, sort ───────────────────────────────────
        all_results = learned_results + reference_results
        seen: set[str] = set()
        deduped: list[FuzzyMatchResult] = []
        for r in sorted(all_results, key=lambda x: x.score, reverse=True):
            if r.cma_field_name not in seen:
                seen.add(r.cma_field_name)
                deduped.append(r)

        return deduped[:top_n]

    # ── Private helpers ───────────────────────────────────────────────────────

    def _fetch_learned_mappings(self, industry_type: str) -> list[dict]:
        """Query learned_mappings filtered by industry_type."""
        service = get_service_client()
        result = (
            service.table("learned_mappings")
            .select("source_text,cma_field_name,cma_input_row")
            .eq("industry_type", industry_type)
            .execute()
        )
        return result.data or []

    def _fetch_reference_mappings(self) -> list[dict]:
        """Return cma_reference_mappings rows, cached after the first DB fetch.

        The reference table is static at runtime (populated by migration), so
        caching it in the instance avoids N round-trips when classifying a full
        document with many line items.
        """
        if self._reference_cache is None:
            service = get_service_client()
            result = (
                service.table("cma_reference_mappings")
                .select("item_name,cma_form_item,cma_input_row,broad_classification")
                .execute()
            )
            # Filter NULL cma_input_row in Python (avoids PostgREST NULL-filter quirks)
            self._reference_cache = [
                r for r in (result.data or []) if r.get("cma_input_row") is not None
            ]
        return self._reference_cache

    def _match_against_learned(
        self,
        raw_text: str,
        mappings: list[dict],
        top_n: int,
    ) -> list[FuzzyMatchResult]:
        """Run rapidfuzz against learned_mappings rows."""
        choices = {m["source_text"]: m for m in mappings if m.get("source_text")}
        if not choices:
            return []

        matches = process.extract(
            raw_text,
            list(choices.keys()),
            scorer=fuzz.token_set_ratio,
            limit=top_n,
        )

        results = []
        for text, score, _ in matches:
            m = choices[text]
            cma_field = m["cma_field_name"]
            cma_row = m["cma_input_row"]
            results.append(
                FuzzyMatchResult(
                    cma_field_name=cma_field,
                    cma_row=cma_row,
                    cma_sheet=_determine_sheet(cma_field),
                    broad_classification="",  # not stored in learned_mappings
                    score=float(score),
                    source="learned",
                )
            )
        return results

    def _match_against_reference(
        self,
        raw_text: str,
        mappings: list[dict],
        top_n: int,
    ) -> list[FuzzyMatchResult]:
        """Run rapidfuzz against cma_reference_mappings rows.

        Note: matches against item_name but returns cma_form_item as the
        CMA field name (critical — the form item is the canonical field).

        Uses token_set_ratio (word-order insensitive) with a length penalty
        to avoid false positives where short queries like "Share Capital"
        match any long string containing those tokens (e.g. "Redeemable
        Preference Share Capital (redeemable after 1 year)").
        """
        choices = {m["item_name"]: m for m in mappings if m.get("item_name")}
        if not choices:
            return []

        # Fetch more candidates than needed so we can re-rank after penalty
        matches = process.extract(
            raw_text,
            list(choices.keys()),
            scorer=fuzz.token_set_ratio,
            limit=top_n * 3,
        )

        results = []
        query_len = len(raw_text.strip())
        for text, score, _ in matches:
            m = choices[text]
            cma_field = m["cma_form_item"]
            cma_row = m["cma_input_row"]
            if cma_field is None or cma_row is None:
                continue

            # Length penalty: if the reference item_name is much longer than
            # the query, the match is likely a false positive (subset match).
            # Penalty = min(query_len, match_len) / max(query_len, match_len)
            match_len = len(text.strip())
            length_ratio = min(query_len, match_len) / max(query_len, match_len) if max(query_len, match_len) > 0 else 1.0
            adjusted_score = score * (0.5 + 0.5 * length_ratio)

            results.append(
                FuzzyMatchResult(
                    cma_field_name=cma_field,
                    cma_row=cma_row,
                    cma_sheet=_determine_sheet(cma_field),
                    broad_classification=m.get("broad_classification") or "",
                    score=float(adjusted_score),
                    source="reference",
                )
            )

        # Re-sort by adjusted score
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_n]


def _determine_sheet(cma_field_name: str) -> str:
    """Return the CMA sheet for a given field name.

    All fields in ALL_FIELD_TO_ROW are in the INPUT SHEET.
    TL Sheet fields are not yet part of this mapping (Phase 5 scope).
    """
    # All currently known CMA fields map to the input_sheet
    return "input_sheet"
