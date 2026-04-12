"""Prompt promoter — promotes approved rules into specialist prompts.

Archives the current prompt version before modification. Always
human-in-the-loop: rules must be explicitly approved before promotion.
"""

from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Base path to specialist prompt files
_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "services" / "classification" / "agents" / "prompts"
_ARCHIVE_DIR = _PROMPTS_DIR / "archive"

# Map specialist name to prompt filename
_SPECIALIST_FILES = {
    "pl_income": "pl_income_prompt.md",
    "pl_expense": "pl_expense_prompt.md",
    "bs_liability": "bs_liability_prompt.md",
    "bs_asset": "bs_asset_prompt.md",
}


class PromptPromoter:
    """Promotes approved rules into specialist prompt files."""

    def __init__(self, prompts_dir: Path | None = None) -> None:
        self.prompts_dir = prompts_dir or _PROMPTS_DIR
        self.archive_dir = self.prompts_dir / "archive"

    def promote_rule(
        self,
        specialist: str,
        source_pattern: str,
        target_cma_row: int,
        tier_tag: str = "CA_VERIFIED_2026",
    ) -> dict:
        """Append a classification rule to a specialist prompt file.

        1. Archives the current version of the prompt
        2. Appends the new rule to the <classification_rules> section
        3. Returns metadata about what was done

        Parameters
        ----------
        specialist     — which agent: pl_income, pl_expense, bs_liability, bs_asset
        source_pattern — the text pattern to match (e.g. "Staff Salary Expense")
        target_cma_row — the correct CMA row for this pattern
        tier_tag       — the rule tier (default: CA_VERIFIED_2026)

        Returns
        -------
        dict with archive_path, prompt_path, rule_text
        """
        filename = _SPECIALIST_FILES.get(specialist)
        if not filename:
            raise ValueError(f"Unknown specialist: {specialist}")

        prompt_path = self.prompts_dir / filename

        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        # 1. Archive current version
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"{prompt_path.stem}_{timestamp}{prompt_path.suffix}"
        archive_path = self.archive_dir / archive_name
        shutil.copy2(prompt_path, archive_path)
        logger.info("Archived %s -> %s", prompt_path.name, archive_path)

        # 2. Build rule text
        rule_text = (
            f"\n\n<!-- Rule added by PromptPromoter at {timestamp} -->\n"
            f"- **[{tier_tag}]** If source text matches \"{source_pattern}\", "
            f"classify to Row {target_cma_row}.\n"
        )

        # 3. Append to prompt file
        with open(prompt_path, "a", encoding="utf-8") as f:
            f.write(rule_text)

        logger.info(
            "Promoted rule: %s -> Row %d (specialist=%s, tier=%s)",
            source_pattern, target_cma_row, specialist, tier_tag,
        )

        return {
            "archive_path": str(archive_path),
            "prompt_path": str(prompt_path),
            "rule_text": rule_text.strip(),
            "specialist": specialist,
            "target_cma_row": target_cma_row,
        }
