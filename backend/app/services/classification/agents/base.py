"""Base agent class for multi-agent CMA classification pipeline.

All specialist agents and the router agent inherit from BaseAgent.
Each agent:
  - Loads its system prompt from a markdown file at init time
  - Calls Gemini 2.5 Flash via OpenRouter using the OpenAI SDK
  - Returns structured JSON (via response_format=json_object)
  - Tracks token usage across every call
  - Never raises on API/parse errors — returns doubt records instead
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from openai import OpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)


class BaseAgent:
    """Shared foundation for all classification agents.

    Parameters
    ----------
    name:
        Human-readable agent name used in log messages.
    prompt_path:
        Absolute or relative path to the markdown file containing
        this agent's system prompt.  Loaded once at init time.
    """

    def __init__(
        self,
        name: str,
        prompt_path: str,
        reasoning_effort: str = "none",
        agent_key: str | None = None,
    ) -> None:
        self.name = name
        self._reasoning_effort = reasoning_effort
        self._agent_key = agent_key

        # Load system prompt — raise immediately if the file is missing so
        # misconfigurations are caught at startup, not first request.
        prompt_file = Path(prompt_path)
        if not prompt_file.exists():
            raise FileNotFoundError(
                f"[{self.name}] Prompt file not found: {prompt_path}"
            )
        raw_prompt = prompt_file.read_text(encoding="utf-8")
        self._system_prompt: str = self._substitute_placeholders(raw_prompt)

        settings = get_settings()
        self._client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        self._model: str = settings.gemini_model

    # ------------------------------------------------------------------
    # Prompt placeholder substitution + whitelist validation
    # ------------------------------------------------------------------

    def _substitute_placeholders(self, prompt: str) -> str:
        """Inject {{section_structure}} and {{valid_output_rows}} from cell_types.

        If agent_key is None (router or test stubs), return prompt unchanged.
        """
        if self._agent_key is None:
            return prompt
        # Import inside method to avoid a circular import at module load time.
        from app.services.classification import cell_types

        try:
            ctx = cell_types.get_agent_context(self._agent_key)
        except (KeyError, FileNotFoundError) as exc:
            logger.warning(
                "[%s] cell_types context unavailable (%s) — leaving placeholders raw",
                self.name, exc,
            )
            return prompt
        return (
            prompt
            .replace("{{section_structure}}", ctx["section_tree"])
            .replace("{{valid_output_rows}}", cell_types.valid_rows_csv(self._agent_key))
            .replace("{{notes_primary}}", cell_types.shared_notes_primary())
        )

    def _validate_whitelist(self, classifications: list[dict]) -> list[dict]:
        """Force-DOUBT any classification whose cma_row is not in this agent's whitelist.

        Passthrough when agent_key is None. Existing DOUBT records are not modified.
        """
        if self._agent_key is None:
            return classifications
        from app.services.classification import cell_types

        try:
            ctx = cell_types.get_agent_context(self._agent_key)
        except (KeyError, FileNotFoundError):
            return classifications
        whitelist = set(ctx["valid_rows"])
        validated: list[dict] = []
        for clf in classifications:
            cma_row = clf.get("cma_row", 0)
            code = clf.get("cma_code", "")
            if code == "DOUBT" or cma_row == 0:
                validated.append(clf)
                continue
            if cma_row in whitelist:
                validated.append(clf)
                continue
            clf_doubt = dict(clf)
            clf_doubt["cma_code"] = "DOUBT"
            clf_doubt["cma_row"] = 0
            clf_doubt["confidence"] = min(float(clf.get("confidence", 0.0)), 0.40)
            original = clf.get("reasoning", "")
            clf_doubt["reasoning"] = (
                f"Whitelist violation: agent output row {cma_row} is not a valid "
                f"target for '{self._agent_key}' (header/formula/blank/note). "
                f"Auto-converted to DOUBT. Original reasoning: {original}"
            )
            validated.append(clf_doubt)
        return validated

    # ------------------------------------------------------------------
    # Core model call
    # ------------------------------------------------------------------

    def _call_model(self, user_content: str) -> tuple[dict | None, int]:
        """Send *user_content* to the model and return (parsed_json, tokens_used).

        Returns
        -------
        (dict, tokens)  — successful parse
        (None, tokens)  — API call succeeded but response was not valid JSON
        (None, 0)       — API call itself raised an exception
        """
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                temperature=0.1,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": user_content},
                ],
                extra_body={"reasoning": {"effort": self._reasoning_effort}},
            )
        except Exception as exc:
            logger.error(
                "[%s] API call failed: %s — %s",
                self.name,
                type(exc).__name__,
                exc,
            )
            return None, 0

        tokens_used: int = 0
        if response.usage is not None:
            tokens_used = response.usage.total_tokens

        raw_text = response.choices[0].message.content or ""
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            logger.error(
                "[%s] JSON parse failed — raw response (first 200 chars): %s",
                self.name,
                raw_text[:200],
            )
            return None, tokens_used

        return parsed, tokens_used

    # ------------------------------------------------------------------
    # Batch classification
    # ------------------------------------------------------------------

    def classify_batch(
        self, items: list[dict], industry_type: str, document_type: str = "annual_report"
    ) -> tuple[list[dict], int]:
        """Classify a batch of line items.

        Sends all items in a single prompt.  On total API failure, every
        item becomes a doubt record.  If the model returns a partial list
        (some item IDs missing), the missing ones also become doubt records.

        Parameters
        ----------
        items:
            Each dict must contain at least ``id``.  Optional keys:
            ``source_text``, ``description``, ``amount``, ``section``,
            ``page_type``, ``source_sheet``, ``has_note_breakdowns``.
        industry_type:
            e.g. ``"manufacturing"``, ``"trading"``, ``"services"``.

        Returns
        -------
        (classifications, total_tokens)
        """
        if not items:
            return [], 0

        # Build structured user content
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

        user_content = json.dumps(
            {"industry_type": industry_type, "document_type": document_type, "items": payload_items},
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

        # The model should return {"classifications": [...]}
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
                    self._make_doubt(
                        item, "Item missing from model response — please classify manually"
                    )
                )

        return self._validate_whitelist(classifications), tokens

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_doubt(item: dict, reason: str) -> dict:
        """Create a doubt record for an item that could not be classified."""
        return {
            "id": item["id"],
            "cma_row": 0,
            "cma_code": "DOUBT",
            "confidence": 0.0,
            "sign": 1,
            "reasoning": reason,
            "alternatives": [],
        }
