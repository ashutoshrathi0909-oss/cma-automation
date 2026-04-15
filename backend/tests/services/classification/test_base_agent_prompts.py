"""Tests for BaseAgent placeholder substitution + whitelist validator."""
from __future__ import annotations
from pathlib import Path
import pytest

from app.services.classification.agents.base import BaseAgent
from app.services.classification import cell_types


@pytest.fixture(autouse=True)
def _reset_cell_types_cache():
    cell_types._reset_cache()
    yield
    cell_types._reset_cache()


@pytest.fixture
def dummy_prompt(tmp_path: Path) -> Path:
    p = tmp_path / "prompt.md"
    p.write_text(
        "You are an agent.\n"
        "=== STRUCTURE ===\n"
        "{{section_structure}}\n"
        "=== VALID ROWS ===\n"
        "{{valid_output_rows}}\n",
        encoding="utf-8",
    )
    return p


def test_placeholders_substituted_at_load(dummy_prompt: Path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy")
    agent = BaseAgent(
        name="test",
        prompt_path=str(dummy_prompt),
        agent_key="pl_income",
    )
    assert "{{section_structure}}" not in agent._system_prompt
    assert "{{valid_output_rows}}" not in agent._system_prompt
    assert "R22" in agent._system_prompt
    assert "Domestic" in agent._system_prompt


def test_agent_key_none_leaves_placeholders_untouched(dummy_prompt: Path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy")
    agent = BaseAgent(name="test", prompt_path=str(dummy_prompt))
    assert "{{section_structure}}" in agent._system_prompt


def test_whitelist_rejects_off_target_rows(dummy_prompt: Path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy")
    agent = BaseAgent(
        name="test",
        prompt_path=str(dummy_prompt),
        agent_key="pl_income",
    )
    clfs = [
        {"id": "a", "cma_row": 22, "cma_code": "II_A1", "confidence": 0.9, "sign": 1, "reasoning": ""},
        {"id": "b", "cma_row": 21, "cma_code": "II_A0", "confidence": 0.9, "sign": 1, "reasoning": "picked header"},
        {"id": "c", "cma_row": 24, "cma_code": "FORMULA", "confidence": 0.9, "sign": 1, "reasoning": ""},
        {"id": "d", "cma_row": 0, "cma_code": "DOUBT", "confidence": 0.2, "sign": 1, "reasoning": "unclear"},
    ]
    validated = agent._validate_whitelist(clfs)
    by_id = {c["id"]: c for c in validated}
    assert by_id["a"]["cma_row"] == 22
    assert by_id["a"]["cma_code"] == "II_A1"
    assert by_id["b"]["cma_code"] == "DOUBT"
    assert by_id["b"]["cma_row"] == 0
    assert by_id["c"]["cma_code"] == "DOUBT"
    assert by_id["c"]["cma_row"] == 0
    assert by_id["d"]["cma_code"] == "DOUBT"
    assert by_id["b"]["confidence"] <= 0.40
    reason_lower = by_id["b"]["reasoning"].lower()
    assert "whitelist" in reason_lower or "header" in reason_lower or "invalid" in reason_lower


def test_whitelist_passthrough_when_agent_key_none(dummy_prompt: Path, monkeypatch):
    """An agent without agent_key must not validate — backwards compat for router."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy")
    agent = BaseAgent(name="test", prompt_path=str(dummy_prompt))
    clfs = [{"id": "x", "cma_row": 21, "cma_code": "II_A0", "confidence": 0.9, "sign": 1, "reasoning": ""}]
    validated = agent._validate_whitelist(clfs)
    assert validated[0]["cma_code"] == "II_A0"  # unchanged


def test_specialist_agents_wire_agent_key(monkeypatch):
    """Each of the 4 specialists must construct with agent_key set so substitution runs."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy")
    from app.services.classification.agents.pl_income import PLIncomeAgent
    from app.services.classification.agents.pl_expense import PLExpenseAgent
    from app.services.classification.agents.bs_asset import BSAssetAgent
    from app.services.classification.agents.bs_liability import BSLiabilityAgent
    for cls, key in [
        (PLIncomeAgent, "pl_income"),
        (PLExpenseAgent, "pl_expense"),
        (BSAssetAgent, "bs_asset"),
        (BSLiabilityAgent, "bs_liability"),
    ]:
        agent = cls()
        assert agent._agent_key == key, f"{cls.__name__} did not set agent_key"
