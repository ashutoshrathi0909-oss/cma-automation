"""P&L Expense specialist agent."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from app.services.classification.agents.base import BaseAgent

logger = logging.getLogger(__name__)

_DEFAULT_PROMPT = Path(__file__).parent / "prompts" / "pl_expense_prompt.md"

_OTHER_INDUSTRIES: dict[str, str] = {
    "manufacturing": "trading/services",
    "trading": "manufacturing/services",
    "services": "manufacturing/trading",
}


class PLExpenseAgent(BaseAgent):
    """Classifies P&L expenses: manufacturing, admin, finance, tax."""

    def __init__(self, prompt_path: str | None = None) -> None:
        super().__init__(
            name="pl_expense",
            prompt_path=prompt_path or str(_DEFAULT_PROMPT),
            reasoning_effort="medium",
            agent_key="pl_expense",
        )

    # ------------------------------------------------------------------
    # Override classify_batch to inject industry emphasis
    # ------------------------------------------------------------------

    def classify_batch(
        self, items: list[dict], industry_type: str, document_type: str = "annual_report"
    ) -> tuple[list[dict], int]:
        """Classify P&L expense items with industry-specific filtering.

        Injects a ``CLASSIFICATION_CONTEXT`` key into the user content JSON
        so the model knows which industry-tagged rules to apply and which
        to ignore.
        """
        if not items:
            return [], 0

        payload_items = []
        for item in items:
            payload_items.append(
                {
                    "id": item["id"],
                    "description": item.get("source_text") or item.get("description", ""),
                    "amount": item.get("amount"),
                    "section": item.get("section"),
                    "page_type": item.get("page_type"),
                    "source_sheet": item.get("source_sheet", ""),
                    "has_note_breakdowns": item.get("has_note_breakdowns", False),
                }
            )

        ignore_list = _OTHER_INDUSTRIES.get(industry_type, "")

        user_content = json.dumps(
            {
                "CLASSIFICATION_CONTEXT": (
                    f"This batch is for a {industry_type.upper()} company. "
                    f"Apply ONLY rules tagged [{industry_type}] or [all]. "
                    f"IGNORE all rules tagged [{ignore_list}]."
                ),
                "industry_type": industry_type,
                "document_type": document_type,
                "items": payload_items,
            },
            ensure_ascii=False,
        )

        parsed, tokens = self._call_model(user_content)

        if parsed is None:
            logger.warning(
                "[%s] API/parse failure — returning doubt records for all %d items",
                self.name,
                len(items),
            )
            return (
                [self._make_doubt(item, "API/parse failure — please classify manually") for item in items],
                tokens,
            )

        classifications: list[dict] = parsed.get("classifications", [])

        # Detect missing items and fill with doubts
        returned_ids = {c.get("id") for c in classifications}
        for item in items:
            if item["id"] not in returned_ids:
                logger.warning(
                    "[%s] Item '%s' missing from model response — flagging as doubt",
                    self.name,
                    item["id"],
                )
                classifications.append(
                    self._make_doubt(item, "Item missing from model response — please classify manually")
                )

        return self._validate_whitelist(classifications), tokens
