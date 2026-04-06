"""Unit tests for RouterAgent.

All OpenAI client calls are mocked at the module level (via base.py's import)
so no real API requests are made.  Prompt files are created with pytest's
tmp_path fixture.  Settings are mocked so no .env / Supabase credentials are
required.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Module-level settings mock — applied via autouse fixture so every test runs
# without needing real env vars or a .env file.
# ---------------------------------------------------------------------------

MOCK_SETTINGS = MagicMock(
    openrouter_api_key="test-openrouter-key",
    gemini_model="google/gemini-2.5-flash",
)


@pytest.fixture(autouse=True)
def mock_settings():
    """Patch get_settings for every test so no Supabase creds are needed."""
    with patch(
        "app.services.classification.agents.base.get_settings",
        return_value=MOCK_SETTINGS,
    ):
        yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_ITEMS = [
    {
        "id": "i1",
        "description": "Revenue from Operations",
        "amount": 100,
        "section": "income",
        "source_sheet": "P & L Ac",
        "page_type": "face",
    },
    {
        "id": "i2",
        "description": "Axis Bank Term Loan",
        "amount": 500,
        "section": "long term borrowings",
        "source_sheet": "Notes BS (2)",
        "page_type": "notes",
    },
    {
        "id": "i3",
        "description": "Raw Material Consumed",
        "amount": 300,
        "section": "cost of materials",
        "source_sheet": "P & L Ac",
        "page_type": "face",
    },
    {
        "id": "i4",
        "description": "Fixed Assets - Plant",
        "amount": 800,
        "section": "property plant equipment",
        "source_sheet": "Notes BS (1)",
        "page_type": "notes",
    },
]


def _make_prompt_file(tmp_path: Path, content: str = "You are the router agent.") -> str:
    """Write a temporary prompt markdown file and return its absolute path."""
    p = tmp_path / "router_prompt.md"
    p.write_text(content, encoding="utf-8")
    return str(p)


def _mock_api_response(json_payload: dict, total_tokens: int = 50):
    """Build a minimal mock OpenAI ChatCompletion response."""
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


# ---------------------------------------------------------------------------
# Test 1 — happy path: four items routed to four different buckets
# ---------------------------------------------------------------------------


@patch("app.services.classification.agents.base.OpenAI")
def test_route_returns_four_buckets(mock_openai_cls, tmp_path):
    """Router correctly distributes 4 items across all four buckets."""
    from app.services.classification.agents.router import RouterAgent

    api_payload = {
        "routing": [
            {"id": "i1", "bucket": "pl_income", "reason": "revenue keyword"},
            {"id": "i2", "bucket": "bs_liability", "reason": "term loan is a borrowing"},
            {"id": "i3", "bucket": "pl_expense", "reason": "raw material cost"},
            {"id": "i4", "bucket": "bs_asset", "reason": "fixed asset"},
        ]
    }
    mock_instance = mock_openai_cls.return_value
    mock_instance.chat.completions.create.return_value = _mock_api_response(
        api_payload, total_tokens=80
    )

    agent = RouterAgent(prompt_path=_make_prompt_file(tmp_path))
    buckets, tokens = agent.route(SAMPLE_ITEMS, industry_type="manufacturing", document_type="annual_report")

    assert tokens == 80
    assert len(buckets["pl_income"]) == 1
    assert buckets["pl_income"][0]["id"] == "i1"

    assert len(buckets["bs_liability"]) == 1
    assert buckets["bs_liability"][0]["id"] == "i2"

    assert len(buckets["pl_expense"]) == 1
    assert buckets["pl_expense"][0]["id"] == "i3"

    assert len(buckets["bs_asset"]) == 1
    assert buckets["bs_asset"][0]["id"] == "i4"

    # All items routed — nothing unrouted
    assert agent.last_unrouted == []


# ---------------------------------------------------------------------------
# Test 2 — API failure: all buckets empty, all items in last_unrouted
# ---------------------------------------------------------------------------


@patch("app.services.classification.agents.base.OpenAI")
def test_route_api_failure_returns_all_unrouted(mock_openai_cls, tmp_path):
    """When the API raises an exception all buckets are empty and last_unrouted holds every item."""
    from app.services.classification.agents.router import RouterAgent

    mock_instance = mock_openai_cls.return_value
    mock_instance.chat.completions.create.side_effect = ConnectionError("timeout")

    agent = RouterAgent(prompt_path=_make_prompt_file(tmp_path))
    buckets, tokens = agent.route(SAMPLE_ITEMS, industry_type="manufacturing", document_type="annual_report")

    assert tokens == 0
    # All four buckets must be empty
    for bucket_items in buckets.values():
        assert bucket_items == []

    # All four items are unrouted
    assert len(agent.last_unrouted) == 4
    unrouted_ids = {item["id"] for item in agent.last_unrouted}
    assert unrouted_ids == {"i1", "i2", "i3", "i4"}


# ---------------------------------------------------------------------------
# Test 3 — partial routing: 2 of 4 items returned; 2 tracked as unrouted
# ---------------------------------------------------------------------------


@patch("app.services.classification.agents.base.OpenAI")
def test_route_unrouted_items_tracked(mock_openai_cls, tmp_path):
    """Items absent from the model response end up in last_unrouted."""
    from app.services.classification.agents.router import RouterAgent

    # Model only routes i1 and i3; i2 and i4 are missing from the response
    api_payload = {
        "routing": [
            {"id": "i1", "bucket": "pl_income", "reason": "revenue"},
            {"id": "i3", "bucket": "pl_expense", "reason": "raw material cost"},
        ]
    }
    mock_instance = mock_openai_cls.return_value
    mock_instance.chat.completions.create.return_value = _mock_api_response(
        api_payload, total_tokens=60
    )

    agent = RouterAgent(prompt_path=_make_prompt_file(tmp_path))
    buckets, tokens = agent.route(SAMPLE_ITEMS, industry_type="manufacturing", document_type="annual_report")

    assert tokens == 60

    # Routed items land in correct buckets
    assert len(buckets["pl_income"]) == 1
    assert buckets["pl_income"][0]["id"] == "i1"
    assert len(buckets["pl_expense"]) == 1
    assert buckets["pl_expense"][0]["id"] == "i3"

    # Unused buckets are empty
    assert buckets["bs_liability"] == []
    assert buckets["bs_asset"] == []

    # i2 and i4 are unrouted
    assert len(agent.last_unrouted) == 2
    unrouted_ids = {item["id"] for item in agent.last_unrouted}
    assert unrouted_ids == {"i2", "i4"}


# ---------------------------------------------------------------------------
# Test 4 — invalid bucket name: item goes to unrouted, not a bucket
# ---------------------------------------------------------------------------


@patch("app.services.classification.agents.base.OpenAI")
def test_route_invalid_bucket_ignored(mock_openai_cls, tmp_path):
    """Items assigned an invalid bucket name are treated as unrouted."""
    from app.services.classification.agents.router import RouterAgent

    api_payload = {
        "routing": [
            {"id": "i1", "bucket": "pl_income", "reason": "revenue"},
            {"id": "i2", "bucket": "INVALID_BUCKET", "reason": "???"},
            {"id": "i3", "bucket": "pl_expense", "reason": "cost"},
            {"id": "i4", "bucket": "bs_asset", "reason": "fixed asset"},
        ]
    }
    mock_instance = mock_openai_cls.return_value
    mock_instance.chat.completions.create.return_value = _mock_api_response(
        api_payload, total_tokens=75
    )

    agent = RouterAgent(prompt_path=_make_prompt_file(tmp_path))
    buckets, tokens = agent.route(SAMPLE_ITEMS, industry_type="manufacturing", document_type="annual_report")

    assert tokens == 75

    # i1, i3, i4 should be in their respective buckets
    assert len(buckets["pl_income"]) == 1
    assert buckets["pl_income"][0]["id"] == "i1"
    assert len(buckets["pl_expense"]) == 1
    assert buckets["pl_expense"][0]["id"] == "i3"
    assert len(buckets["bs_asset"]) == 1
    assert buckets["bs_asset"][0]["id"] == "i4"

    # i2 with invalid bucket ends up unrouted
    assert len(agent.last_unrouted) == 1
    assert agent.last_unrouted[0]["id"] == "i2"


# ---------------------------------------------------------------------------
# Test 5 — empty items: returns empty buckets immediately, 0 tokens
# ---------------------------------------------------------------------------


@patch("app.services.classification.agents.base.OpenAI")
def test_route_empty_items(mock_openai_cls, tmp_path):
    """Empty item list returns all empty buckets and 0 tokens without calling the API."""
    from app.services.classification.agents.router import RouterAgent

    mock_instance = mock_openai_cls.return_value

    agent = RouterAgent(prompt_path=_make_prompt_file(tmp_path))
    buckets, tokens = agent.route([], industry_type="manufacturing", document_type="annual_report")

    assert tokens == 0
    for bucket_items in buckets.values():
        assert bucket_items == []
    assert agent.last_unrouted == []

    # API should NOT have been called
    mock_instance.chat.completions.create.assert_not_called()
