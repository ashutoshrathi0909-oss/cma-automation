"""P&L Income specialist agent (CMA rows R22-R34)."""
from __future__ import annotations
from pathlib import Path
from app.services.classification.agents.base import BaseAgent

_DEFAULT_PROMPT = Path(__file__).parent / "prompts" / "pl_income_prompt.md"


class PLIncomeAgent(BaseAgent):
    """Classifies P&L income items: domestic/export sales, other income."""

    def __init__(self, prompt_path: str | None = None) -> None:
        super().__init__(name="pl_income", prompt_path=prompt_path or str(_DEFAULT_PROMPT))
