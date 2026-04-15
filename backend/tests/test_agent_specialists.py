"""Tests for the 4 specialist classification agents.

Each test class is parametrized and runs once per agent:
  pl_income, pl_expense, bs_liability, bs_asset

Settings are mocked via autouse fixture so no .env or Supabase creds are needed.
Imports of specialist classes happen inside the test body (after settings mock is active).
"""
from __future__ import annotations

import json
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
    with patch(
        "app.services.classification.agents.base.get_settings",
        return_value=MOCK_SETTINGS,
    ):
        yield


# ---------------------------------------------------------------------------
# Helpers / constants
# ---------------------------------------------------------------------------

# Each specialist must receive rows from its own whitelist; we pick the first
# two valid_rows per agent (from DOCS/cma_cell_types.json) so the new whitelist
# validator in BaseAgent leaves them untouched.
AGENT_CLASSES_NAMES = [
    ("pl_income", "app.services.classification.agents.pl_income", "PLIncomeAgent", 22, 23),
    ("pl_expense", "app.services.classification.agents.pl_expense", "PLExpenseAgent", 67, 68),
    ("bs_liability", "app.services.classification.agents.bs_liability", "BSLiabilityAgent", 116, 117),
    ("bs_asset", "app.services.classification.agents.bs_asset", "BSAssetAgent", 162, 163),
]

SAMPLE_ITEMS = [
    {
        "id": "i1",
        "description": "Staff Welfare Expenses",
        "amount": 234500,
        "section": "employee benefit expenses",
        "page_type": "notes",
        "has_note_breakdowns": True,
    },
    {
        "id": "i2",
        "description": "Sales Returns",
        "amount": 50000,
        "section": "revenue",
        "page_type": "notes",
        "has_note_breakdowns": False,
    },
]


def _build_mock_response(row1: int, row2: int) -> dict:
    """Build a mock classification response using rows valid for the agent under test."""
    return {
        "classifications": [
            {
                "id": "i1",
                "cma_row": row1,
                "cma_code": "II_D1",
                "confidence": 0.95,
                "sign": 1,
                "reasoning": "Staff welfare -> Salary",
            },
            {
                "id": "i2",
                "cma_row": row2,
                "cma_code": "II_A1",
                "confidence": 0.90,
                "sign": -1,
                "reasoning": "Sales Returns subtract from Domestic",
            },
        ]
    }


def _make_agent(module_path: str, class_name: str, tmp_path):
    """Import the specialist class and instantiate it with a tmp prompt file."""
    import importlib
    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)

    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("# Test prompt\nClassify items.", encoding="utf-8")
    return cls(prompt_path=str(prompt_file))


def _make_mock_client(response_dict: dict | None):
    """Build a mock OpenAI client.

    If *response_dict* is None the client raises RuntimeError to simulate an
    API failure.  Otherwise it returns a well-formed ChatCompletion mock.
    """
    mock_client = MagicMock()
    if response_dict is None:
        mock_client.chat.completions.create.side_effect = RuntimeError("API error")
    else:
        mock_message = MagicMock()
        mock_message.content = json.dumps(response_dict)

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_usage = MagicMock()
        mock_usage.total_tokens = 100

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        mock_client.chat.completions.create.return_value = mock_response
    return mock_client


# ---------------------------------------------------------------------------
# Parametrized test class
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name,module_path,class_name,row1,row2",
    AGENT_CLASSES_NAMES,
    ids=[a[0] for a in AGENT_CLASSES_NAMES],
)
class TestSpecialistAgent:

    def test_classify_batch_returns_classifications(
        self, name, module_path, class_name, row1, row2, tmp_path
    ):
        """API returns 2 valid classifications — verify correct parsing."""
        mock_response = _build_mock_response(row1, row2)
        with patch("app.services.classification.agents.base.OpenAI") as MockOpenAI:
            MockOpenAI.return_value = _make_mock_client(mock_response)
            agent = _make_agent(module_path, class_name, tmp_path)

        results, tokens = agent.classify_batch(SAMPLE_ITEMS, industry_type="manufacturing")

        assert len(results) == 2
        assert tokens == 100

        ids_returned = {r["id"] for r in results}
        assert ids_returned == {"i1", "i2"}

        r1 = next(r for r in results if r["id"] == "i1")
        assert r1["cma_row"] == row1
        assert r1["cma_code"] == "II_D1"
        assert r1["confidence"] == pytest.approx(0.95)
        assert r1["sign"] == 1

        r2 = next(r for r in results if r["id"] == "i2")
        assert r2["cma_row"] == row2
        assert r2["sign"] == -1

    def test_classify_batch_api_failure_returns_doubts(
        self, name, module_path, class_name, row1, row2, tmp_path
    ):
        """API raises an exception — all items must become doubt records with cma_row=0."""
        with patch("app.services.classification.agents.base.OpenAI") as MockOpenAI:
            MockOpenAI.return_value = _make_mock_client(None)  # raises RuntimeError
            agent = _make_agent(module_path, class_name, tmp_path)

        results, tokens = agent.classify_batch(SAMPLE_ITEMS, industry_type="trading")

        assert len(results) == len(SAMPLE_ITEMS)
        assert tokens == 0

        for result in results:
            assert result["cma_row"] == 0
            assert result["cma_code"] == "DOUBT"
            assert result["confidence"] == pytest.approx(0.0)

    def test_classify_batch_empty_returns_empty(
        self, name, module_path, class_name, row1, row2, tmp_path
    ):
        """Empty item list must return ([], 0) without touching the API."""
        with patch("app.services.classification.agents.base.OpenAI") as MockOpenAI:
            mock_client = MagicMock()
            MockOpenAI.return_value = mock_client
            agent = _make_agent(module_path, class_name, tmp_path)

        results, tokens = agent.classify_batch([], industry_type="services")

        assert results == []
        assert tokens == 0
        mock_client.chat.completions.create.assert_not_called()
