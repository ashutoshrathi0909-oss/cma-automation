"""B/S Asset specialist agent."""
from __future__ import annotations
from pathlib import Path
from app.services.classification.agents.base import BaseAgent

_DEFAULT_PROMPT = Path(__file__).parent / "prompts" / "bs_asset_prompt.md"


class BSAssetAgent(BaseAgent):
    """Classifies B/S assets: fixed assets, investments, inventories, debtors, cash."""

    def __init__(self, prompt_path: str | None = None) -> None:
        super().__init__(
            name="bs_asset",
            prompt_path=prompt_path or str(_DEFAULT_PROMPT),
            agent_key="bs_asset",
        )
