"""Router agent for the multi-agent CMA classification pipeline.

The router receives all extracted line items and assigns each one to exactly
one of four specialist buckets via a single API call:

  pl_income   — P&L revenue / income items
  pl_expense  — P&L cost / expense items
  bs_liability — Balance Sheet equity / liability items
  bs_asset    — Balance Sheet asset items

The specialist agents then handle fine-grained CMA row mapping within their
assigned bucket.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.services.classification.agents.base import BaseAgent

logger = logging.getLogger(__name__)

_DEFAULT_PROMPT_PATH = Path(__file__).parent / "prompts" / "router_prompt.md"

VALID_BUCKETS: frozenset[str] = frozenset(
    {"pl_income", "pl_expense", "bs_liability", "bs_asset"}
)


class RouterAgent(BaseAgent):
    """Routes financial line items into four specialist buckets.

    Parameters
    ----------
    prompt_path:
        Path to the router system prompt markdown file.  Defaults to the
        bundled ``prompts/router_prompt.md`` next to this module.
    """

    def __init__(self, prompt_path: str | None = None) -> None:
        resolved = str(prompt_path) if prompt_path is not None else str(_DEFAULT_PROMPT_PATH)
        super().__init__(name="router", prompt_path=resolved, reasoning_effort="medium")

        # Populated by the most recent call to route(); empty list means all
        # items were successfully routed.
        self.last_unrouted: list[dict] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def route(
        self,
        items: list[dict],
        industry_type: str,
        document_type: str,
    ) -> tuple[dict[str, list[dict]], int]:
        """Route *items* into the four specialist buckets.

        Parameters
        ----------
        items:
            Each dict must contain at least ``id``.  Optional keys:
            ``source_text``, ``description``, ``amount``, ``section``,
            ``source_sheet``, ``page_type``.
        industry_type:
            e.g. ``"manufacturing"``, ``"trading"``, ``"services"``.
        document_type:
            e.g. ``"annual_report"``, ``"provisional"``.

        Returns
        -------
        (buckets, tokens_used)
            *buckets* is a dict with keys ``pl_income``, ``pl_expense``,
            ``bs_liability``, ``bs_asset``; each value is a (possibly empty)
            list of item dicts taken from the input.
            *tokens_used* is the total token count reported by the model.
        """
        # Always reset unrouted tracker before each call
        self.last_unrouted = []

        # Prepare the empty result structure
        buckets: dict[str, list[dict]] = {
            "pl_income": [],
            "pl_expense": [],
            "bs_liability": [],
            "bs_asset": [],
        }

        if not items:
            return buckets, 0

        # Build the payload items list — normalise description field
        payload_items = []
        for item in items:
            payload_items.append(
                {
                    "id": item["id"],
                    "description": item.get("source_text") or item.get("description", ""),
                    "amount": item.get("amount"),
                    "section": item.get("section"),
                    "source_sheet": item.get("source_sheet"),
                    "page_type": item.get("page_type"),
                }
            )

        user_content = json.dumps(
            {
                "industry_type": industry_type,
                "document_type": document_type,
                "items": payload_items,
            },
            ensure_ascii=False,
        )

        parsed, tokens = self._call_model(user_content)

        if parsed is None:
            # Total API/parse failure — all items are unrouted
            logger.warning(
                "[router] API/parse failure — %d items left unrouted",
                len(items),
            )
            self.last_unrouted = list(items)
            return buckets, tokens

        routing: list[dict] = parsed.get("routing", [])

        # Build a lookup from item id -> original item dict for fast retrieval
        item_by_id: dict[str, dict] = {item["id"]: item for item in items}

        # Track which ids were handled by the model response
        routed_ids: set[str] = set()

        for entry in routing:
            item_id = entry.get("id")
            bucket = entry.get("bucket")

            if item_id not in item_by_id:
                logger.warning(
                    "[router] Model returned unknown id '%s' — ignoring",
                    item_id,
                )
                continue

            if bucket not in VALID_BUCKETS:
                logger.warning(
                    "[router] Item '%s' has invalid bucket '%s' — marking unrouted",
                    item_id,
                    bucket,
                )
                # Do NOT add to routed_ids so it ends up in last_unrouted below
                continue

            buckets[bucket].append(item_by_id[item_id])
            routed_ids.add(item_id)

        # Any item not returned (or with invalid bucket) is unrouted
        for item in items:
            if item["id"] not in routed_ids:
                logger.warning(
                    "[router] Item '%s' missing or invalid in routing response — unrouted",
                    item["id"],
                )
                self.last_unrouted.append(item)

        return buckets, tokens
