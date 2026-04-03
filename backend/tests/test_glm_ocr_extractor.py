"""Tests for GlmOcrExtractor — GLM-OCR vision-based PDF extraction."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.extraction.glm_ocr_extractor import (
    GlmOcrExtractor,
    _parse_json_response,
)


# ── JSON parsing tests ────────────────────────────────────────────────────────


class TestParseJsonResponse:
    """Test the JSON response parser handles various GLM-OCR output formats."""

    def test_clean_json_array(self):
        text = '[{"description": "Sales", "amount": 500000, "section": "income", "ambiguity_question": null}]'
        result = _parse_json_response(text)
        assert len(result) == 1
        assert result[0]["description"] == "Sales"
        assert result[0]["amount"] == 500000

    def test_json_with_markdown_fences(self):
        text = '```json\n[{"description": "Rent", "amount": 50000, "section": "expenses", "ambiguity_question": null}]\n```'
        result = _parse_json_response(text)
        assert len(result) == 1
        assert result[0]["description"] == "Rent"

    def test_json_with_items_wrapper(self):
        text = '{"items": [{"description": "Cash", "amount": 100000, "section": "assets", "ambiguity_question": null}]}'
        result = _parse_json_response(text)
        assert len(result) == 1
        assert result[0]["description"] == "Cash"

    def test_empty_response(self):
        assert _parse_json_response("") == []
        assert _parse_json_response("No financial data found.") == []

    def test_embedded_json_in_text(self):
        text = 'Here are the items:\n[{"description": "Wages", "amount": 200000, "section": "expenses", "ambiguity_question": null}]\nEnd.'
        result = _parse_json_response(text)
        assert len(result) == 1
        assert result[0]["description"] == "Wages"


# ── Extractor integration tests (mocked Ollama) ──────────────────────────────


class TestGlmOcrExtractor:
    """Test GlmOcrExtractor with mocked Ollama responses."""

    def _mock_ollama_response(self, items: list[dict]) -> MagicMock:
        """Create a mock requests.post response with given items."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "message": {"content": json.dumps(items)}
        }
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    @pytest.mark.asyncio
    @patch("app.services.extraction.glm_ocr_extractor._convert_pdf_to_images")
    @patch("app.services.extraction.glm_ocr_extractor.requests.post")
    @patch("app.services.extraction.glm_ocr_extractor.get_settings")
    async def test_basic_extraction(self, mock_settings, mock_post, mock_convert):
        """Test that a well-formed Ollama response produces correct LineItems."""
        settings = MagicMock()
        settings.glm_ocr_model = "glm-ocr"
        settings.ollama_url = "http://ollama:11434"
        mock_settings.return_value = settings

        from PIL import Image
        mock_image = Image.new("RGB", (100, 100))
        mock_convert.return_value = [mock_image]

        mock_post.return_value = self._mock_ollama_response([
            {"description": "Domestic Sales", "amount": 5000000, "section": "income", "ambiguity_question": None},
            {"description": "Salary & Wages", "amount": 1200000, "section": "expenses", "ambiguity_question": None},
            {"description": "Sundry Debtors", "amount": 800000, "section": "assets", "ambiguity_question": None},
        ])

        extractor = GlmOcrExtractor()
        items = await extractor.extract(b"fake-pdf-bytes")

        assert len(items) == 3
        assert items[0].description == "Domestic Sales"
        assert items[0].amount == 5000000
        assert items[0].section == "income"
        assert items[1].description == "Salary & Wages"
        assert items[2].description == "Sundry Debtors"

    @pytest.mark.asyncio
    @patch("app.services.extraction.glm_ocr_extractor._convert_pdf_to_images")
    @patch("app.services.extraction.glm_ocr_extractor.requests.post")
    @patch("app.services.extraction.glm_ocr_extractor.get_settings")
    async def test_negative_amounts(self, mock_settings, mock_post, mock_convert):
        """Test that negative amounts are handled."""
        settings = MagicMock()
        settings.glm_ocr_model = "glm-ocr"
        settings.ollama_url = "http://ollama:11434"
        mock_settings.return_value = settings

        from PIL import Image
        mock_convert.return_value = [Image.new("RGB", (100, 100))]

        mock_post.return_value = self._mock_ollama_response([
            {"description": "Drawings", "amount": -91999, "section": "liabilities", "ambiguity_question": None},
        ])

        items = await GlmOcrExtractor().extract(b"fake-pdf")
        assert len(items) == 1
        assert items[0].amount == -91999

    @pytest.mark.asyncio
    @patch("app.services.extraction.glm_ocr_extractor._convert_pdf_to_images")
    @patch("app.services.extraction.glm_ocr_extractor.requests.post")
    @patch("app.services.extraction.glm_ocr_extractor.get_settings")
    async def test_skips_empty_descriptions(self, mock_settings, mock_post, mock_convert):
        """Test that items with empty descriptions are filtered out."""
        settings = MagicMock()
        settings.glm_ocr_model = "glm-ocr"
        settings.ollama_url = "http://ollama:11434"
        mock_settings.return_value = settings

        from PIL import Image
        mock_convert.return_value = [Image.new("RGB", (100, 100))]

        mock_post.return_value = self._mock_ollama_response([
            {"description": "", "amount": 1000, "section": "", "ambiguity_question": None},
            {"description": "Valid Item", "amount": 2000, "section": "income", "ambiguity_question": None},
        ])

        items = await GlmOcrExtractor().extract(b"fake-pdf")
        assert len(items) == 1
        assert items[0].description == "Valid Item"

    @pytest.mark.asyncio
    @patch("app.services.extraction.glm_ocr_extractor._convert_pdf_to_images")
    @patch("app.services.extraction.glm_ocr_extractor.requests.post")
    @patch("app.services.extraction.glm_ocr_extractor.get_settings")
    async def test_ollama_failure_returns_empty(self, mock_settings, mock_post, mock_convert):
        """Test that Ollama connection failure returns empty list."""
        settings = MagicMock()
        settings.glm_ocr_model = "glm-ocr"
        settings.ollama_url = "http://ollama:11434"
        mock_settings.return_value = settings

        from PIL import Image
        mock_convert.return_value = [Image.new("RGB", (100, 100))]

        import requests as req
        mock_post.side_effect = req.ConnectionError("Ollama not running")

        items = await GlmOcrExtractor().extract(b"fake-pdf")
        assert items == []

    @pytest.mark.asyncio
    @patch("app.services.extraction.glm_ocr_extractor._convert_pdf_to_images")
    @patch("app.services.extraction.glm_ocr_extractor.requests.post")
    @patch("app.services.extraction.glm_ocr_extractor.get_settings")
    async def test_ambiguity_detection(self, mock_settings, mock_post, mock_convert):
        """Test that ambiguity questions are passed through to LineItems."""
        settings = MagicMock()
        settings.glm_ocr_model = "glm-ocr"
        settings.ollama_url = "http://ollama:11434"
        mock_settings.return_value = settings

        from PIL import Image
        mock_convert.return_value = [Image.new("RGB", (100, 100))]

        mock_post.return_value = self._mock_ollama_response([
            {
                "description": "Employee Benefit Expenses",
                "amount": 500000,
                "section": "expenses",
                "ambiguity_question": "CMA needs Wages (Row 45) vs Salary (Row 67) — which applies?",
            },
        ])

        items = await GlmOcrExtractor().extract(b"fake-pdf")
        assert len(items) == 1
        assert items[0].ambiguity_question is not None
        assert "Row 45" in items[0].ambiguity_question
