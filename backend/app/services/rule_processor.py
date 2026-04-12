"""Rule processor — converts father's questionnaire answers into proposed rules.

Pure Python, zero API calls. Maps each correction answer to a proposed_rule
record that can later be promoted into the specialist prompts via the eval gate.
"""

from __future__ import annotations

# Agent row ranges — must match eval_multi_agent.py
AGENT_RANGES = {
    "pl_income": (22, 34),
    "pl_expense": (41, 108),
    "bs_liability": (110, 160),
    "bs_asset": (161, 258),
}


def _determine_specialist(cma_row: int) -> str:
    """Return the specialist agent name for a given CMA row number."""
    for agent, (lo, hi) in AGENT_RANGES.items():
        if lo <= cma_row <= hi:
            return agent
    return "unknown"


def process_answers(
    answers: list[dict],
    questions: list[dict],
    industry_type: str = "manufacturing",
) -> list[dict]:
    """Convert father's questionnaire answers into proposed classification rules.

    Parameters
    ----------
    answers       — list of answer dicts from the questionnaire UI
    questions     — list of question dicts (from generate_questionnaire)
    industry_type — industry context for the rule

    Returns
    -------
    list[dict] — proposed rules, one per correction (option B or C)
    """
    if not answers or not questions:
        return []

    # Index questions by question_id for fast lookup
    q_by_id = {q["question_id"]: q for q in questions}

    rules: list[dict] = []
    for answer in answers:
        # Option A = AI was correct — no rule needed
        if answer.get("selected_option") == "A":
            continue

        question = q_by_id.get(answer.get("question_id", ""))
        if not question:
            continue

        target_row = answer.get("cma_row_correction")
        if not target_row:
            continue

        # Get source text from the question's source items
        source_items = question.get("source_items", [])
        source_pattern = source_items[0].get("source_text", "") if source_items else ""

        specialist = _determine_specialist(target_row)

        rules.append({
            "source_pattern": source_pattern,
            "original_cma_row": question.get("cma_row"),
            "target_cma_row": target_row,
            "specialist": specialist,
            "industry_type": industry_type,
            "tier_tag": "CA_VERIFIED_2026",
            "note": answer.get("note"),
        })

    return rules
