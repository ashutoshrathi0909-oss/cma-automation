"""Questionnaire generator — produces questions from CMA cell diffs.

Pure Python, zero API calls. Each CellDiff becomes one question asking
the father to confirm which value is correct and why.
"""

from __future__ import annotations

from app.services.excel_diff import CellDiff


def generate_questionnaire(
    diffs: list[CellDiff],
    report_id: str,
    provenance: dict[tuple[int, str], list[dict]],
) -> list[dict]:
    """Generate one question per cell diff for father review.

    Parameters
    ----------
    diffs       — list of CellDiff from diff_cma_files()
    report_id   — CMA report ID (used for question ID generation)
    provenance  — {(cma_row, cma_column): [provenance_records]} from cell_provenance

    Returns
    -------
    list[dict] — one question per diff, each with options and source items
    """
    if not diffs:
        return []

    questions: list[dict] = []
    for i, diff in enumerate(diffs):
        question_id = f"{report_id}-q-{i}"

        # Look up source items from provenance
        key = (diff.cma_row, diff.cma_column)
        source_items = provenance.get(key, [])

        options = [
            {"value": "A", "label": "AI value is correct", "description": f"Keep {diff.ai_value}"},
            {"value": "B", "label": "Father's correction is correct", "description": f"Use {diff.father_value}"},
            {"value": "C", "label": "Neither — different value needed", "description": "Specify correct row/value"},
        ]

        questions.append({
            "question_id": question_id,
            "cma_row": diff.cma_row,
            "cma_column": diff.cma_column,
            "ai_value": diff.ai_value,
            "father_value": diff.father_value,
            "options": options,
            "source_items": source_items,
        })

    return questions
