"""B/S Liability specialist agent."""
from __future__ import annotations
from pathlib import Path
from app.services.classification.agents.base import BaseAgent

_DEFAULT_PROMPT = Path(__file__).parent / "prompts" / "bs_liability_prompt.md"


class BSLiabilityAgent(BaseAgent):
    """Classifies B/S liabilities: capital, reserves, borrowings."""

    def __init__(self, prompt_path: str | None = None) -> None:
        super().__init__(name="bs_liability", prompt_path=prompt_path or str(_DEFAULT_PROMPT), reasoning_effort="medium")
