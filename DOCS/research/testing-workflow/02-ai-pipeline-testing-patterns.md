# AI Pipeline Testing Patterns

## The Problem: Real API Calls in Tests Are Toxic

Calling Anthropic's API in tests causes four compounding problems:

1. **Cost**: Every test run burns real credits. At ~₹2.30/page for Claude Vision, a 33-page document costs ₹76 per test run. Run tests 20 times while debugging and you've spent ₹1,520 on a single document.
2. **Speed**: API calls take 5–30 seconds. A 50-test suite becomes 10–25 minutes.
3. **Flakiness**: Network errors, rate limits, and API changes cause test failures unrelated to your code.
4. **Non-determinism**: Claude gives different responses on different runs, making assertions fragile.

The solution is a layered testing strategy: pure mocks for unit tests, recorded responses for integration tests, and real API calls only for explicitly budgeted smoke tests.

---

## Layer 1: Pure Mocks (Unit Tests)

For testing `OcrExtractor._parse_response()`, `OcrExtractor.extract()`, and `ClassificationPipeline`, inject fake responses that match the exact schema Claude returns.

### Mocking the Anthropic Client

```python
# backend/tests/test_ocr_extractor.py
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from PIL import Image

from app.services.extraction.ocr_extractor import OcrExtractor


def _make_fake_claude_response(items: list[dict]) -> MagicMock:
    """
    Build a fake anthropic.Message that matches what Claude Vision returns
    when using tool_use with extract_financial_items.
    """
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.input = {
        "page_results": [
            {
                "page_number": 1,
                "page_type": "profit_and_loss",
                "scale_factor": "absolute",
                "items": items,
            }
        ]
    }

    response = MagicMock()
    response.content = [tool_block]
    return response


@pytest.fixture
def extractor():
    return OcrExtractor()


@pytest.fixture
def fake_image():
    return Image.new("RGB", (800, 600), color=(255, 255, 255))


class TestOcrExtractorParseResponse:
    def test_parses_basic_line_items(self, extractor):
        response = _make_fake_claude_response([
            {"description": "Salaries & Wages", "amount": 500000, "section": "expenses"},
            {"description": "Revenue from Operations", "amount": 1000000, "section": "income"},
        ])
        items = extractor._parse_response(response)

        assert len(items) == 2
        assert items[0].description == "Salaries & Wages"
        assert items[0].amount == pytest.approx(500000.0)
        assert items[1].description == "Revenue from Operations"

    def test_applies_scale_factor(self, extractor):
        """Amounts in_lakhs should be multiplied by 100,000."""
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.input = {
            "page_results": [
                {
                    "page_number": 1,
                    "page_type": "profit_and_loss",
                    "scale_factor": "in_lakhs",
                    "items": [
                        {"description": "Net Profit", "amount": 12.5, "section": "income"},
                    ],
                }
            ]
        }
        response = MagicMock()
        response.content = [tool_block]

        items = extractor._parse_response(response)
        assert items[0].amount == pytest.approx(1_250_000.0)  # 12.5 lakhs

    def test_skips_auditor_report_pages(self, extractor):
        """Pages classified as auditor_report should be ignored."""
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.input = {
            "page_results": [
                {
                    "page_number": 1,
                    "page_type": "auditor_report",
                    "scale_factor": "absolute",
                    "items": [{"description": "Some text", "amount": 100, "section": "other"}],
                }
            ]
        }
        response = MagicMock()
        response.content = [tool_block]

        items = extractor._parse_response(response)
        assert len(items) == 0

    def test_handles_missing_tool_use_block(self, extractor):
        """If Claude returns no tool_use block, return empty list (not exception)."""
        response = MagicMock()
        response.content = []  # No tool_use block
        items = extractor._parse_response(response)
        assert items == []

    def test_flags_ambiguous_items(self, extractor):
        """Items with ambiguity_question should have it set on the LineItem."""
        response = _make_fake_claude_response([
            {
                "description": "Wages & Salaries",
                "amount": 750000,
                "section": "expenses",
                "ambiguity_question": "Split between manufacturing wages (Row 45) and admin salaries (Row 49)?",
            }
        ])
        items = extractor._parse_response(response)
        assert items[0].ambiguity_question is not None
        assert "Row 45" in items[0].ambiguity_question


class TestOcrExtractorExtract:
    @pytest.mark.asyncio
    async def test_extract_calls_api_once_per_batch(self, extractor, fake_image):
        """For a 3-page doc (batch size 5), exactly 1 API call should be made."""
        pages = [(i, fake_image) for i in range(1, 4)]
        fake_response = _make_fake_claude_response([
            {"description": "Revenue", "amount": 1000000, "section": "income"}
        ])

        with (
            patch.object(extractor, "_process_batch", return_value=[]) as mock_batch,
            patch("app.services.extraction.ocr_extractor.filter_pages", return_value=pages),
            patch(
                "app.services.extraction.ocr_extractor.convert_from_bytes",
                return_value=[fake_image] * 3
            ),
        ):
            await extractor.extract(b"%PDF fake")
            assert mock_batch.call_count == 1  # 3 pages fit in one batch

    @pytest.mark.asyncio
    async def test_extract_returns_empty_for_blank_pdf(self, extractor):
        """All-blank PDF (no content pages) → returns [], not an error."""
        with (
            patch("app.services.extraction.ocr_extractor.convert_from_bytes", return_value=[MagicMock()]),
            patch("app.services.extraction.ocr_extractor.filter_pages", return_value=[]),
        ):
            result = await extractor.extract(b"%PDF blank")
        assert result == []
```

---

## Layer 2: VCR/Cassette Recording (Integration Tests)

The VCR (Video Cassette Recorder) pattern records a real API call once, saves it to a YAML/JSON file, and replays it in all future test runs. This gives you realistic responses without real API costs.

### Setup with `pytest-recording` (wraps `vcrpy`)

```bash
pip install pytest-recording vcrpy
```

```python
# backend/tests/test_classification_vcr.py
import pytest

# Mark this test to record on first run, then replay forever
@pytest.mark.vcr()
def test_classification_calls_anthropic(classification_pipeline, sample_line_items):
    """
    On first run with --record-mode=new_episodes: hits real Anthropic API, saves response.
    On subsequent runs: replays saved cassette, zero API calls, zero cost.
    """
    results = classification_pipeline.classify_items(sample_line_items[:5])
    assert len(results) == 5
    assert all(r.cma_field is not None for r in results)
```

```yaml
# tests/cassettes/test_classification_calls_anthropic.yaml
# Auto-generated on first --record-mode run. Commit this file to git.
interactions:
- request:
    body: '{"model":"claude-haiku-4-5","max_tokens":1024,"messages":[...]}'
    headers:
      Authorization:
      - Bearer sk-ant-REDACTED
    method: POST
    uri: https://api.anthropic.com/v1/messages
  response:
    body:
      string: '{"id":"msg_01...","content":[{"type":"text","text":"{\\"cma_field\\":\\"Row 45 - Staff Costs\\"}"}]}'
    headers:
      Content-Type:
      - application/json
    status:
      code: 200
```

**First run** (records the cassette):
```bash
pytest tests/test_classification_vcr.py --record-mode=new_episodes
```

**All subsequent runs** (free replay):
```bash
pytest tests/test_classification_vcr.py  # uses cassette, no API call
```

### Scrubbing Credentials from Cassettes

```python
# conftest.py
import pytest

@pytest.fixture(scope="module")
def vcr_config():
    return {
        "filter_headers": ["authorization", "x-api-key"],
        "filter_post_data_parameters": ["api_key"],
        "record_mode": "none",  # Never record in CI — cassettes must be pre-committed
    }
```

**Important**: Commit cassette files to git. They are your "golden responses" and should be updated intentionally (by re-recording) rather than automatically.

---

## Layer 3: Synthetic Fixtures (Best for Classification Accuracy Tests)

For testing **classification accuracy** systematically, don't use VCR. Instead, build a fixture file of known input/output pairs and test against them:

```python
# backend/tests/fixtures/classification_ground_truth.py
"""
Ground truth pairs: (source_text, expected_cma_field).
These were manually validated against the 384-item reference mapping.
"""

GROUND_TRUTH = [
    # Clear matches — fuzzy should handle these without AI
    ("Salaries & Wages", "Row 45 - Staff Costs"),
    ("Salary Expenses", "Row 45 - Staff Costs"),
    ("Rent Paid", "Row 50 - Rent, Rates & Taxes"),
    ("Revenue from Operations", "Row 1 - Net Sales"),
    ("Net Sales", "Row 1 - Net Sales"),

    # Tricky matches — AI tier needed
    ("Employee Benefit Expenses", "Row 45 - Staff Costs"),
    ("Power & Fuel", "Row 48 - Power & Fuel"),
    ("Depreciation on Fixed Assets", "Row 52 - Depreciation"),
    ("Bank Interest on CC Account", "Row 55 - Interest on Bank Borrowings"),

    # Items that should be DOUBTED (no clear mapping)
    ("GST Liability Adjustment", None),  # None = should go to doubt report
    ("Suspense Account Clearing", None),
]
```

```python
# backend/tests/test_classification_accuracy.py
import pytest
from tests.fixtures.classification_ground_truth import GROUND_TRUTH
from app.services.classification.pipeline import ClassificationPipeline


class TestClassificationAccuracy:
    """Tests classification accuracy against ground truth.

    Uses a mocked Anthropic client so no real API calls are made.
    The fuzzy matching tier (rapidfuzz) runs for real against the reference DB.
    """

    @pytest.fixture
    def pipeline_with_fuzzy_only(self, mock_service):
        """Pipeline that uses real fuzzy matching but mocked AI tier."""
        # Mock the AI client to return "doubt" for everything
        # This lets us test the fuzzy tier in isolation
        with patch("app.services.classification.pipeline.anthropic.Anthropic") as mock_anthropic:
            mock_anthropic.return_value.messages.create.return_value = MagicMock(
                content=[MagicMock(text='{"cma_field": null, "confidence": 0}')]
            )
            yield ClassificationPipeline()

    @pytest.mark.parametrize("source_text,expected_field", GROUND_TRUTH)
    def test_classification_accuracy(self, pipeline_with_fuzzy_only, source_text, expected_field):
        result = pipeline_with_fuzzy_only.classify_single(source_text)

        if expected_field is None:
            # Should be in doubt report, not force-classified
            assert result.cma_field is None or result.is_doubt, (
                f"'{source_text}' should be flagged as doubt, got: {result.cma_field}"
            )
        else:
            assert result.cma_field == expected_field, (
                f"'{source_text}' → expected '{expected_field}', got '{result.cma_field}'"
            )
```

Run the accuracy report:
```bash
pytest tests/test_classification_accuracy.py -v 2>&1 | grep -E "PASSED|FAILED"
```

This gives you a classification accuracy percentage without spending a single rupee.

---

## Mocking the Anthropic Client Correctly

There are three levels of mocking. Use the right one for the right test:

### Level 1: Mock the entire Anthropic client (most common)

```python
from unittest.mock import patch, MagicMock

def make_claude_response(text: str) -> MagicMock:
    msg = MagicMock()
    msg.content = [MagicMock(type="text", text=text)]
    return msg

with patch("app.services.classification.pipeline.anthropic.Anthropic") as MockClient:
    instance = MockClient.return_value
    instance.messages.create.return_value = make_claude_response(
        '{"cma_field": "Row 45 - Staff Costs", "confidence": 0.92}'
    )
    result = pipeline.classify_single("Salary Expenses")
```

### Level 2: Mock only the HTTP transport (realistic but controlled)

```python
import httpx
from anthropic import Anthropic

# Use Anthropic's own test utilities
with httpx.Client() as client:
    # Anthropic SDK accepts a custom httpx client for testing
    # This lets you intercept at the HTTP level without mocking Python objects
    pass
```

### Level 3: Use `anthropic`'s built-in mock stream helpers

```python
# anthropic >= 0.44.0 ships with test helpers
from anthropic import AnthropicBedrock  # or regular Anthropic
# The SDK's MockAnthropic is available in test extras:
# pip install anthropic[test]
```

For our stack, **Level 1 is the right choice**. It's simple, doesn't depend on SDK internals, and clearly separates what you're testing (your parsing and routing logic) from what you're not testing (Anthropic's API).

---

## Testing the 3-Tier Classification Pipeline

Your pipeline has three tiers: fuzzy → AI → doubt. Each tier needs its own test boundary.

```python
# backend/tests/test_classification_pipeline.py
import pytest
from unittest.mock import patch, MagicMock

from app.services.classification.pipeline import ClassificationPipeline


class TestFuzzyTier:
    """Tier 1: rapidfuzz matching. No AI, no DB — runs on pure Python."""

    def test_high_confidence_fuzzy_match_skips_ai(self, pipeline):
        """score >= 90 → classified immediately, no Anthropic call."""
        with patch.object(pipeline, "_call_ai_tier") as mock_ai:
            result = pipeline.classify_single("Salaries & Wages")
        mock_ai.assert_not_called()
        assert result.cma_field is not None

    def test_low_confidence_fuzzy_escalates_to_ai(self, pipeline):
        """score < 90 → AI tier is called."""
        with patch.object(pipeline, "_call_ai_tier", return_value=None) as mock_ai:
            pipeline.classify_single("Misc Office Sundries Exp")
        mock_ai.assert_called_once()


class TestAITier:
    """Tier 2: Claude Haiku classification."""

    def test_ai_tier_returns_cma_field(self, pipeline, mock_anthropic):
        mock_anthropic.return_value = '{"cma_field": "Row 60 - Other Expenses", "confidence": 0.85}'
        result = pipeline._call_ai_tier("Miscellaneous office expenses")
        assert result == "Row 60 - Other Expenses"

    def test_ai_tier_handles_malformed_json(self, pipeline, mock_anthropic):
        """If Claude returns non-JSON, escalate to doubt (never crash)."""
        mock_anthropic.return_value = "I cannot classify this item."
        result = pipeline._call_ai_tier("Some unknown item")
        assert result is None  # Should become a doubt item

    def test_ai_tier_handles_api_error(self, pipeline):
        """Network error → item goes to doubt, not exception."""
        with patch.object(pipeline, "_anthropic_client") as mock_client:
            mock_client.messages.create.side_effect = Exception("Connection timeout")
            result = pipeline._call_ai_tier("Revenue Item X")
        assert result is None


class TestDoubtReport:
    """Tier 3: Items that neither fuzzy nor AI could classify."""

    def test_doubt_items_are_flagged_not_silently_classified(self, pipeline):
        """Rule: NEVER silent guessing. Doubt items must be explicitly flagged."""
        with (
            patch.object(pipeline, "_fuzzy_match", return_value=(None, 0)),
            patch.object(pipeline, "_call_ai_tier", return_value=None),
        ):
            result = pipeline.classify_single("XYZ Unknown Expense ABC")

        assert result.cma_field is None
        assert result.is_doubt is True
        assert result.doubt_reason is not None

    def test_doubt_items_get_doubt_reason(self, pipeline):
        """Doubt items must include a human-readable reason for the CA to review."""
        with (
            patch.object(pipeline, "_fuzzy_match", return_value=(None, 0)),
            patch.object(pipeline, "_call_ai_tier", return_value=None),
        ):
            result = pipeline.classify_single("Suspense Account")

        assert len(result.doubt_reason) > 10  # Not an empty string
```

---

## Testing the `learned_mappings` Priority Rule

Your spec says `learned_mappings` must be checked BEFORE `reference_mappings`. This rule is easy to accidentally break during refactoring. Write an explicit test:

```python
def test_learned_mappings_checked_before_reference_mappings(pipeline, mock_service):
    """
    If learned_mappings has a match, reference_mappings must NOT be consulted.
    This enforces the spec: learned_mappings > reference_mappings.
    """
    # Seed a learned mapping
    mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {
            "source_text": "Staff Remuneration",
            "cma_field": "Row 45 - Staff Costs",
            "confidence": 1.0,
        }
    ]

    with patch.object(pipeline, "_lookup_reference_mappings") as mock_ref:
        result = pipeline.classify_single("Staff Remuneration")

    mock_ref.assert_not_called()
    assert result.cma_field == "Row 45 - Staff Costs"
```

---

## Budget-Safe CI Strategy

```
Test Pyramid for AI Pipeline:
                    ┌─────────────────────┐
                    │   SMOKE TESTS       │  ← Real API, manual only, budgeted
                    │   (2-3 per month)   │
                 ┌──┴─────────────────────┴──┐
                 │   VCR CASSETTE TESTS       │  ← Recorded once, replayed free
                 │   (integration layer)      │
             ┌───┴────────────────────────────┴───┐
             │   PURE MOCK UNIT TESTS              │  ← Run on every commit, free
             │   (classification, parsing, fuzzy)  │
             └─────────────────────────────────────┘
```

### Preventing Accidental API Calls in CI

Add this to `conftest.py` to make any accidental real API call fail loudly:

```python
# backend/tests/conftest.py
import pytest
import os


@pytest.fixture(autouse=True)
def block_real_api_calls_in_ci(monkeypatch):
    """
    In CI environments, ensure no real Anthropic API calls can be made.
    Tests that need real API access must be marked @pytest.mark.live_api.
    """
    if os.getenv("CI") == "true":
        # Override the API key with an invalid value
        # Any test that tries to call real Anthropic will get an AuthenticationError
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-blocked-in-ci")
```

For the rare tests that DO need real API access:
```python
@pytest.mark.live_api
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="No API key")
def test_actual_classification_quality():
    """Only runs locally when ANTHROPIC_API_KEY is set. Never runs in CI."""
    ...
```

---

## Recommended for Our Project

**Immediate actions (no cost, high value):**

1. Add `TestOcrExtractorParseResponse` tests — these exercise `_parse_response()` which is the most complex parsing logic and requires zero mocking of the API.

2. Add `TestClassificationAccuracy` with the parametrized ground truth fixture — start with 20 known items, grow over time. Run after every classification pipeline change to catch regressions.

3. Add the `block_real_api_calls_in_ci` autouse fixture — prevents accidentally spending money in CI.

4. Write VCR cassettes for two representative documents (one native PDF, one scanned) and commit them. These become your "golden path" integration tests.

**Do NOT do yet:**

- Do not write end-to-end tests that call real Anthropic inside Docker Compose. Save those for final QA before bank submission, with a fixed budget of 3-5 test documents.

- Do not add `httpretty` or `responses` library — they intercept at the socket level and interfere with asyncio. Use `unittest.mock.patch` at the Python object level instead.
