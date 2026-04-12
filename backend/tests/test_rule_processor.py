# backend/tests/test_rule_processor.py
"""Phase 2: Rule processor — TDD RED phase.

Converts father's questionnaire answers into proposed_rules.
Zero API calls.
"""

import pytest

# Agent row ranges (must match eval script)
AGENT_RANGES = {
    "pl_income": (22, 34),
    "pl_expense": (41, 108),
    "bs_liability": (110, 160),
    "bs_asset": (161, 258),
}


class TestProcessAnswers:
    def test_import_succeeds(self):
        from app.services.rule_processor import process_answers  # noqa: F401

    def test_correction_creates_proposed_rule(self):
        from app.services.rule_processor import process_answers

        answers = [{
            "question_id": "q-001",
            "selected_option": "B",
            "cma_row_correction": 67,
            "note": "This is salary, not raw materials",
        }]
        questions = [{
            "question_id": "q-001",
            "cma_row": 42,
            "source_items": [{"source_text": "Staff Salary Expense", "amount": 500000}],
        }]
        rules = process_answers(answers, questions, industry_type="manufacturing")
        assert len(rules) == 1
        assert rules[0]["target_cma_row"] == 67
        assert rules[0]["source_pattern"] == "Staff Salary Expense"

    def test_correct_specialist_assigned(self):
        from app.services.rule_processor import process_answers

        # Row 67 is in pl_expense range (41-108)
        answers = [{"question_id": "q-001", "selected_option": "B", "cma_row_correction": 67}]
        questions = [{"question_id": "q-001", "cma_row": 42,
                      "source_items": [{"source_text": "X", "amount": 100}]}]
        rules = process_answers(answers, questions, industry_type="manufacturing")
        assert rules[0]["specialist"] == "pl_expense"

        # Row 130 is in bs_liability range (110-160)
        answers2 = [{"question_id": "q-002", "selected_option": "B", "cma_row_correction": 130}]
        questions2 = [{"question_id": "q-002", "cma_row": 200,
                       "source_items": [{"source_text": "Y", "amount": 200}]}]
        rules2 = process_answers(answers2, questions2, industry_type="manufacturing")
        assert rules2[0]["specialist"] == "bs_liability"

    def test_ai_correct_answer_creates_no_rule(self):
        from app.services.rule_processor import process_answers

        answers = [{"question_id": "q-001", "selected_option": "A"}]
        questions = [{"question_id": "q-001", "cma_row": 45,
                      "source_items": [{"source_text": "Wages", "amount": 100}]}]
        rules = process_answers(answers, questions, industry_type="manufacturing")
        assert len(rules) == 0, "No rule needed when AI was correct"

    def test_rule_has_tier_tag(self):
        from app.services.rule_processor import process_answers

        answers = [{"question_id": "q-001", "selected_option": "B", "cma_row_correction": 67}]
        questions = [{"question_id": "q-001", "cma_row": 42,
                      "source_items": [{"source_text": "Salary", "amount": 100}]}]
        rules = process_answers(answers, questions, industry_type="manufacturing")
        assert rules[0]["tier_tag"] == "CA_VERIFIED_2026"

    def test_empty_answers_returns_empty(self):
        from app.services.rule_processor import process_answers
        rules = process_answers(answers=[], questions=[], industry_type="manufacturing")
        assert rules == []
