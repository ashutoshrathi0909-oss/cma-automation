# backend/tests/test_questionnaire.py
"""Phase 2: Questionnaire generator — TDD RED phase.

Zero API calls — deterministic question generation from cell diffs.
"""

import pytest


class TestGenerateQuestionnaire:
    """generate_questionnaire produces one question per diff."""

    def test_import_succeeds(self):
        from app.services.questionnaire_generator import generate_questionnaire  # noqa: F401

    def test_one_question_per_diff(self):
        from app.services.excel_diff import CellDiff
        from app.services.questionnaire_generator import generate_questionnaire

        diffs = [
            CellDiff(cma_row=42, cma_column="B", ai_value=500000, father_value=400000),
            CellDiff(cma_row=67, cma_column="C", ai_value=100000, father_value=None),
        ]
        questions = generate_questionnaire(diffs, report_id="rpt-1", provenance={})
        assert len(questions) == 2

    def test_question_has_required_fields(self):
        from app.services.excel_diff import CellDiff
        from app.services.questionnaire_generator import generate_questionnaire

        diffs = [CellDiff(cma_row=45, cma_column="B", ai_value=300000, father_value=250000)]
        questions = generate_questionnaire(diffs, report_id="rpt-1", provenance={})
        q = questions[0]
        assert "question_id" in q
        assert q["cma_row"] == 45
        assert q["cma_column"] == "B"
        assert "options" in q
        assert len(q["options"]) >= 2, "At least 2 options: AI correct, Father correct"

    def test_question_includes_provenance_source_items(self):
        from app.services.excel_diff import CellDiff
        from app.services.questionnaire_generator import generate_questionnaire

        diffs = [CellDiff(cma_row=45, cma_column="B", ai_value=300000, father_value=250000)]
        provenance = {
            (45, "B"): [
                {"source_text": "Wages Expense", "raw_amount": 300000, "line_item_id": "li-1"}
            ]
        }
        questions = generate_questionnaire(diffs, report_id="rpt-1", provenance=provenance)
        q = questions[0]
        assert "source_items" in q
        assert len(q["source_items"]) == 1
        assert q["source_items"][0]["source_text"] == "Wages Expense"

    def test_empty_diffs_returns_empty_list(self):
        from app.services.questionnaire_generator import generate_questionnaire
        questions = generate_questionnaire(diffs=[], report_id="rpt-1", provenance={})
        assert questions == []
