"""P&L Expense specialist agent."""
from __future__ import annotations
from pathlib import Path
from app.services.classification.agents.base import BaseAgent

_DEFAULT_PROMPT = Path(__file__).parent / "prompts" / "pl_expense_prompt.md"


class PLExpenseAgent(BaseAgent):
    """Classifies P&L expenses: manufacturing, admin, finance, tax."""

    def __init__(self, prompt_path: str | None = None) -> None:
        super().__init__(name="pl_expense", prompt_path=prompt_path or str(_DEFAULT_PROMPT))
