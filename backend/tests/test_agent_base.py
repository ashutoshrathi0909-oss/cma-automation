"""Unit tests for BaseAgent — the shared foundation of all classification agents.

All OpenAI client calls are mocked at the module level so no real API
requests are made.  Prompt files are created in pytest's tmp_path fixture.
Settings are mocked so no .env file or Supabase credentials are required.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Module-level settings mock — applied via autouse fixture so every test
# runs without needing real env vars or a .env file.
# ---------------------------------------------------------------------------

MOCK_SETTINGS = MagicMock(
    openrouter_api_key="test-openrouter-key",
    gemini_model="google/gemini-2.5-flash",
)


@pytest.fixture(autouse=True)
def mock_settings():
    """Patch get_settings for every test so no Supabase creds are needed."""
    with patch("app.services.classification.agents.base.get_settings", return_value=MOCK_SETTINGS):
        yield

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_prompt_file(tmp_path: Path, content: str = "You are a test agent.") -> str:
    """Write a temporary prompt markdown file and return its absolute path."""
    p = tmp_path / "test_prompt.md"
    p.write_text(content, encoding="utf-8")
    return str(p)


def _mock_api_response(json_payload: dict, total_tokens: int = 42):
    """Build a mock OpenAI ChatCompletion response object."""
    message = MagicMock()
    message.content = json.dumps(json_payload)

    choice = MagicMock()
    choice.message = message

    usage = MagicMock()
    usage.total_tokens = total_tokens

    response = MagicMock()
    response.choices = [choice]
    response.usage = usage
    return response


def _mock_api_response_raw(raw_text: str, total_tokens: int = 10):
    """Build a mock response whose content is arbitrary raw text (may be non-JSON)."""
    message = MagicMock()
    message.content = raw_text

    choice = MagicMock()
    choice.message = message

    usage = MagicMock()
    usage.total_tokens = total_tokens

    response = MagicMock()
    response.choices = [choice]
    response.usage = usage
    return response


# ---------------------------------------------------------------------------
# Tests — init
# ---------------------------------------------------------------------------


@patch("app.services.classification.agents.base.OpenAI")
def test_init_loads_prompt(mock_openai_cls, tmp_path):
    """Agent reads and stores the prompt file content at init time."""
    from app.services.classification.agents.base import BaseAgent

    content = "You are a specialist for P&L classification."
    prompt_path = _make_prompt_file(tmp_path, content)

    agent = BaseAgent(name="test-agent", prompt_path=prompt_path)

    assert agent._system_prompt == content
    assert agent.name == "test-agent"
    mock_openai_cls.assert_called_once()


@patch("app.services.classification.agents.base.OpenAI")
def test_init_missing_prompt_raises(mock_openai_cls, tmp_path):
    """FileNotFoundError is raised when the prompt file does not exist."""
    from app.services.classification.agents.base import BaseAgent

    missing_path = str(tmp_path / "does_not_exist.md")

    with pytest.raises(FileNotFoundError, match="Prompt file not found"):
        BaseAgent(name="test-agent", prompt_path=missing_path)


# ---------------------------------------------------------------------------
# Tests — _call_model
# ---------------------------------------------------------------------------


@patch("app.services.classification.agents.base.OpenAI")
def test_call_model_returns_parsed_json(mock_openai_cls, tmp_path):
    """_call_model returns (dict, tokens) on a valid JSON response."""
    from app.services.classification.agents.base import BaseAgent

    payload = {"classifications": [{"id": "item-1", "cma_row": 5}]}
    mock_instance = mock_openai_cls.return_value
    mock_instance.chat.completions.create.return_value = _mock_api_response(
        payload, total_tokens=100
    )

    agent = BaseAgent(name="test-agent", prompt_path=_make_prompt_file(tmp_path))
    result, tokens = agent._call_model("some user content")

    assert result == payload
    assert tokens == 100
    mock_instance.chat.completions.create.assert_called_once()


@patch("app.services.classification.agents.base.OpenAI")
def test_call_model_handles_malformed_json(mock_openai_cls, tmp_path):
    """_call_model returns (None, tokens) when the API returns non-JSON text."""
    from app.services.classification.agents.base import BaseAgent

    mock_instance = mock_openai_cls.return_value
    mock_instance.chat.completions.create.return_value = _mock_api_response_raw(
        "This is not JSON at all!!!", total_tokens=15
    )

    agent = BaseAgent(name="test-agent", prompt_path=_make_prompt_file(tmp_path))
    result, tokens = agent._call_model("some user content")

    assert result is None
    assert tokens == 15


@patch("app.services.classification.agents.base.OpenAI")
def test_call_model_handles_api_error(mock_openai_cls, tmp_path):
    """_call_model returns (None, 0) when the API raises an exception."""
    from app.services.classification.agents.base import BaseAgent

    mock_instance = mock_openai_cls.return_value
    mock_instance.chat.completions.create.side_effect = RuntimeError("connection refused")

    agent = BaseAgent(name="test-agent", prompt_path=_make_prompt_file(tmp_path))
    result, tokens = agent._call_model("some user content")

    assert result is None
    assert tokens == 0


# ---------------------------------------------------------------------------
# Tests — classify_batch
# ---------------------------------------------------------------------------

SAMPLE_ITEMS = [
    {
        "id": "item-001",
        "source_text": "Raw material purchases",
        "amount": 50000.0,
        "section": "expenses",
        "page_type": "profit_loss",
        "has_note_breakdowns": False,
    },
    {
        "id": "item-002",
        "source_text": "Salary expenses",
        "amount": 30000.0,
        "section": "expenses",
        "page_type": "profit_loss",
        "has_note_breakdowns": False,
    },
]

SAMPLE_CLASSIFICATIONS = [
    {
        "id": "item-001",
        "cma_row": 10,
        "cma_code": "RAW_MAT",
        "confidence": 0.95,
        "sign": 1,
        "reasoning": "Direct raw material cost",
        "alternatives": [],
    },
    {
        "id": "item-002",
        "cma_row": 20,
        "cma_code": "SALARY",
        "confidence": 0.92,
        "sign": 1,
        "reasoning": "Staff salary",
        "alternatives": [],
    },
]


@patch("app.services.classification.agents.base.OpenAI")
def test_classify_batch_returns_classifications(mock_openai_cls, tmp_path):
    """classify_batch returns model classifications and correct token count."""
    from app.services.classification.agents.base import BaseAgent

    api_payload = {"classifications": SAMPLE_CLASSIFICATIONS}
    mock_instance = mock_openai_cls.return_value
    mock_instance.chat.completions.create.return_value = _mock_api_response(
        api_payload, total_tokens=200
    )

    agent = BaseAgent(name="test-agent", prompt_path=_make_prompt_file(tmp_path))
    results, tokens = agent.classify_batch(SAMPLE_ITEMS, industry_type="manufacturing")

    assert tokens == 200
    assert len(results) == 2
    ids = {r["id"] for r in results}
    assert ids == {"item-001", "item-002"}
    # Confidence values should be passed through unchanged
    confidences = {r["id"]: r["confidence"] for r in results}
    assert confidences["item-001"] == 0.95
    assert confidences["item-002"] == 0.92


@patch("app.services.classification.agents.base.OpenAI")
def test_classify_batch_api_failure_returns_doubts(mock_openai_cls, tmp_path):
    """classify_batch returns doubt records for ALL items when the API fails."""
    from app.services.classification.agents.base import BaseAgent

    mock_instance = mock_openai_cls.return_value
    mock_instance.chat.completions.create.side_effect = ConnectionError("timeout")

    agent = BaseAgent(name="test-agent", prompt_path=_make_prompt_file(tmp_path))
    results, tokens = agent.classify_batch(SAMPLE_ITEMS, industry_type="manufacturing")

    assert tokens == 0
    assert len(results) == 2
    for r in results:
        assert r["cma_code"] == "DOUBT"
        assert r["confidence"] == 0.0
        assert r["cma_row"] == 0


@patch("app.services.classification.agents.base.OpenAI")
def test_classify_batch_empty_returns_empty(mock_openai_cls, tmp_path):
    """classify_batch returns ([], 0) immediately for an empty item list."""
    from app.services.classification.agents.base import BaseAgent

    mock_instance = mock_openai_cls.return_value

    agent = BaseAgent(name="test-agent", prompt_path=_make_prompt_file(tmp_path))
    results, tokens = agent.classify_batch([], industry_type="manufacturing")

    assert results == []
    assert tokens == 0
    mock_instance.chat.completions.create.assert_not_called()


@patch("app.services.classification.agents.base.OpenAI")
def test_classify_batch_missing_items_get_doubts(mock_openai_cls, tmp_path):
    """Items absent from the model response are appended as doubt records."""
    from app.services.classification.agents.base import BaseAgent

    # Only item-001 is returned; item-002 is missing
    partial_classifications = [SAMPLE_CLASSIFICATIONS[0]]
    api_payload = {"classifications": partial_classifications}
    mock_instance = mock_openai_cls.return_value
    mock_instance.chat.completions.create.return_value = _mock_api_response(
        api_payload, total_tokens=150
    )

    agent = BaseAgent(name="test-agent", prompt_path=_make_prompt_file(tmp_path))
    results, tokens = agent.classify_batch(SAMPLE_ITEMS, industry_type="manufacturing")

    assert tokens == 150
    assert len(results) == 2

    by_id = {r["id"]: r for r in results}

    # item-001 should have the model's classification
    assert by_id["item-001"]["cma_code"] == "RAW_MAT"
    assert by_id["item-001"]["confidence"] == 0.95

    # item-002 should be a doubt
    assert by_id["item-002"]["cma_code"] == "DOUBT"
    assert by_id["item-002"]["confidence"] == 0.0
