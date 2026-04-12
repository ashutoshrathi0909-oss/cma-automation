# backend/tests/test_prompt_promoter.py
"""Phase 3: Prompt promoter — TDD RED phase."""

import pytest
from unittest.mock import MagicMock


class TestPromptPromoter:
    def test_import_succeeds(self):
        from app.services.prompt_promoter import PromptPromoter  # noqa: F401

    def test_promote_archives_current_version(self):
        """Promotion must archive the current prompt before overwriting."""
        from app.services.prompt_promoter import PromptPromoter
        # Will fail because module doesn't exist
        promoter = PromptPromoter()
        assert hasattr(promoter, "promote_rule")
