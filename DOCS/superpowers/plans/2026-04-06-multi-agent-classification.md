# Multi-Agent Classification Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the single-agent DeepSeek V3 classifier (230 API calls, ~60% accuracy) with a 5-agent Gemini Flash pipeline (5 API calls, 85%+ accuracy target).

**Architecture:** 1 router agent assigns items to 4 specialist agents (P&L Income, P&L Expense, B/S Liability, B/S Asset). Each specialist sees only its section's CMA rows + golden rules, enabling focused classification. Learned_mappings checked first — items already corrected by CA skip AI entirely.

**Tech Stack:** Python, FastAPI, OpenRouter (Gemini 2.5 Flash), asyncio, Supabase (PostgreSQL)

**Spec:** `DOCS/superpowers/specs/2026-04-06-multi-agent-classification-design.md`

---

## File Structure

```
backend/app/services/classification/
├── multi_agent_pipeline.py           # NEW — orchestrator (replaces pipeline.py)
├── agents/
│   ├── __init__.py                   # NEW — package init, exports all agents
│   ├── base.py                       # NEW — shared API call logic, response parsing
│   ├── router.py                     # NEW — routes items to 4 specialist buckets
│   ├── pl_income.py                  # NEW — P&L Income specialist (R22-R34)
│   ├── pl_expense.py                 # NEW — P&L Expense specialist (R41-R108)
│   ├── bs_liability.py               # NEW — B/S Liability specialist (R110-R160)
│   └── bs_asset.py                   # NEW — B/S Asset specialist (R161-R258)
├── prompts/                          # NEW — auto-generated prompt files
│   ├── router_prompt.md
│   ├── pl_income_prompt.md
│   ├── pl_expense_prompt.md
│   ├── bs_liability_prompt.md
│   └── bs_asset_prompt.md
├── __init__.py                       # MODIFY — update docstring
├── learning_system.py                # UNCHANGED
├── pipeline.py                       # DELETE (after wire-up)
├── scoped_classifier.py              # DELETE (after wire-up)
├── ai_classifier.py                  # DELETE (after wire-up)
└── fuzzy_matcher.py                  # DELETE (after wire-up)

backend/app/
├── config.py                         # MODIFY — add gemini_model, remove classifier_mode/model
└── workers/classification_tasks.py   # MODIFY — ClassificationPipeline → MultiAgentPipeline

backend/tests/
├── test_multi_agent_pipeline.py      # NEW — orchestrator tests
├── test_agent_base.py                # NEW — base agent tests
├── test_agent_router.py              # NEW — router tests
├── test_agent_specialists.py         # NEW — specialist tests
├── test_classification_pipeline.py   # DELETE (after wire-up)
├── test_scoped_classifier.py         # DELETE (after wire-up)
└── test_ai_classifier.py            # DELETE (after wire-up)

scripts/
├── generate_agent_prompts.py         # NEW — auto-generates prompts from GT files
└── eval_multi_agent.py               # NEW — offline accuracy eval
```

---

## Task 1: Config Changes

**Files:**
- Modify: `backend/app/config.py`
- Test: `backend/tests/test_config.py` (if exists, else inline verification)

- [ ] **Step 1: Write test for new config field**

```python
# backend/tests/test_config_gemini.py
import os
import pytest


def test_gemini_model_default():
    """gemini_model should default to google/gemini-2.5-flash."""
    # Clear cached settings
    from app.config import get_settings
    get_settings.cache_clear()

    os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
    os.environ.setdefault("SUPABASE_ANON_KEY", "test")
    os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test")

    settings = get_settings()
    assert settings.gemini_model == "google/gemini-2.5-flash"
    assert not hasattr(settings, "classifier_mode") or True  # removed field
    get_settings.cache_clear()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_config_gemini.py -v`
Expected: FAIL — `gemini_model` attribute doesn't exist yet.

- [ ] **Step 3: Update config.py**

Replace in `backend/app/config.py`:
```python
    # OpenRouter (cheaper alternative for OCR + classification)
    openrouter_api_key: str = ""
    ocr_provider: str = "openrouter"          # "anthropic" or "openrouter"
    ocr_model: str = "google/gemini-2.5-flash"  # Gemini Flash via OpenRouter — all PDFs
    classifier_provider: str = "openrouter"  # "anthropic" or "openrouter"
    classifier_model: str = "deepseek/deepseek-chat-v3-0324"  # DeepSeek V3 via OpenRouter
    classifier_mode: str = "scoped"  # "scoped" (DeepSeek+Gemini debate) or "legacy" (old Haiku-only)
```

With:
```python
    # OpenRouter (all AI calls: OCR + classification)
    openrouter_api_key: str = ""
    ocr_provider: str = "openrouter"
    ocr_model: str = "google/gemini-2.5-flash"
    gemini_model: str = "google/gemini-2.5-flash"  # Multi-agent classification model
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_config_gemini.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/config.py backend/tests/test_config_gemini.py
git commit -m "feat: add gemini_model config, remove old classifier settings"
```

---

## Task 2: Base Agent Module

**Files:**
- Create: `backend/app/services/classification/agents/__init__.py`
- Create: `backend/app/services/classification/agents/base.py`
- Test: `backend/tests/test_agent_base.py`

- [ ] **Step 1: Create agents package init**

```python
# backend/app/services/classification/agents/__init__.py
"""Multi-agent classification: router + 4 specialist agents."""
```

- [ ] **Step 2: Write failing tests for base agent**

```python
# backend/tests/test_agent_base.py
"""Tests for the base agent API call + JSON parsing logic."""
from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock, patch

from app.services.classification.agents.base import BaseAgent


class TestBaseAgent:
    """Test the shared agent logic."""

    def test_init_loads_prompt(self, tmp_path):
        """Agent loads its prompt file at init."""
        prompt_file = tmp_path / "test_prompt.md"
        prompt_file.write_text("You are a test agent.\n\nClassify these items.")
        agent = BaseAgent(name="test", prompt_path=str(prompt_file))
        assert "You are a test agent" in agent.system_prompt

    def test_init_missing_prompt_raises(self):
        """Agent raises FileNotFoundError if prompt file missing."""
        with pytest.raises(FileNotFoundError):
            BaseAgent(name="test", prompt_path="/nonexistent/prompt.md")

    @patch("app.services.classification.agents.base.OpenAI")
    def test_call_model_returns_parsed_json(self, mock_openai_cls, tmp_path):
        """_call_model sends prompt to OpenRouter and parses JSON response."""
        prompt_file = tmp_path / "prompt.md"
        prompt_file.write_text("System prompt here.")

        # Mock OpenAI client and response
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            {"classifications": [{"id": "uuid-1", "cma_row": 22}]}
        )
        mock_response.usage.total_tokens = 500
        mock_client.chat.completions.create.return_value = mock_response

        agent = BaseAgent(name="test", prompt_path=str(prompt_file))
        result, tokens = agent._call_model("Classify these items")
        assert result == {"classifications": [{"id": "uuid-1", "cma_row": 22}]}
        assert tokens == 500

    @patch("app.services.classification.agents.base.OpenAI")
    def test_call_model_handles_malformed_json(self, mock_openai_cls, tmp_path):
        """_call_model returns None on malformed JSON."""
        prompt_file = tmp_path / "prompt.md"
        prompt_file.write_text("System prompt here.")

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "NOT JSON AT ALL"
        mock_response.usage.total_tokens = 100
        mock_client.chat.completions.create.return_value = mock_response

        agent = BaseAgent(name="test", prompt_path=str(prompt_file))
        result, tokens = agent._call_model("Classify these")
        assert result is None
        assert tokens == 100

    @patch("app.services.classification.agents.base.OpenAI")
    def test_call_model_handles_api_error(self, mock_openai_cls, tmp_path):
        """_call_model returns None on API errors."""
        prompt_file = tmp_path / "prompt.md"
        prompt_file.write_text("System prompt here.")

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API down")

        agent = BaseAgent(name="test", prompt_path=str(prompt_file))
        result, tokens = agent._call_model("Classify these")
        assert result is None
        assert tokens == 0
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_agent_base.py -v`
Expected: FAIL — `agents.base` module doesn't exist.

- [ ] **Step 4: Implement base agent**

```python
# backend/app/services/classification/agents/base.py
"""Shared agent logic: OpenRouter API call, JSON parsing, token tracking."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from openai import OpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for all multi-agent classification agents.

    Handles:
    - Loading system prompt from a markdown file
    - Calling Gemini 2.5 Flash via OpenRouter (openai SDK)
    - JSON response parsing with error handling
    - Token usage tracking
    """

    def __init__(self, name: str, prompt_path: str) -> None:
        self.name = name
        path = Path(prompt_path)
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        self.system_prompt = path.read_text(encoding="utf-8")

        settings = get_settings()
        self._client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
        )
        self._model = settings.gemini_model

    def _call_model(self, user_content: str) -> tuple[dict | None, int]:
        """Call the model and return (parsed_json, tokens_used).

        Returns (None, tokens) on parse failure or API error.
        """
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            tokens = response.usage.total_tokens if response.usage else 0
            raw = response.choices[0].message.content
            try:
                parsed = json.loads(raw)
                return parsed, tokens
            except (json.JSONDecodeError, TypeError):
                logger.error(
                    "Agent '%s': malformed JSON response: %.200s", self.name, raw
                )
                return None, tokens
        except Exception as exc:
            logger.error("Agent '%s': API call failed: %s", self.name, exc)
            return None, 0
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_agent_base.py -v`
Expected: PASS (all 5 tests)

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/classification/agents/__init__.py \
       backend/app/services/classification/agents/base.py \
       backend/tests/test_agent_base.py
git commit -m "feat: add base agent with OpenRouter API call + JSON parsing"
```

---

## Task 3: Prompt Generation Script

**Files:**
- Create: `scripts/generate_agent_prompts.py`
- Create: `backend/app/services/classification/prompts/` (5 markdown files, auto-generated)

**Input files (all exist):**
- `CMA_Ground_Truth_v1/reference/canonical_labels.json` — 151 CMA rows
- `CMA_Ground_Truth_v1/reference/cma_golden_rules_v2.json` — 597 rules
- `CMA_Ground_Truth_v1/database/training_data.json` — 14,000+ examples

- [ ] **Step 1: Create prompt generation script**

```python
# scripts/generate_agent_prompts.py
"""Auto-generate multi-agent classification prompts from ground truth files.

Reads canonical_labels.json, cma_golden_rules_v2.json, and training_data.json.
Produces 5 prompt markdown files in backend/app/services/classification/prompts/.

Usage:
    python scripts/generate_agent_prompts.py

Deterministic: same input files always produce the same output.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
GT_BASE = PROJECT_ROOT / "CMA_Ground_Truth_v1"
CANONICAL_PATH = GT_BASE / "reference" / "canonical_labels.json"
RULES_PATH = GT_BASE / "reference" / "cma_golden_rules_v2.json"
TRAINING_PATH = GT_BASE / "database" / "training_data.json"
OUTPUT_DIR = PROJECT_ROOT / "backend" / "app" / "services" / "classification" / "prompts"

# ── Agent definitions ────────────────────────────────────────────────────────
AGENTS = {
    "router": {"row_range": None, "description": "Routes items to specialist agents"},
    "pl_income": {"row_range": (22, 34), "description": "P&L Income specialist"},
    "pl_expense": {"row_range": (41, 108), "description": "P&L Expense specialist"},
    "bs_liability": {"row_range": (110, 160), "description": "B/S Liability specialist"},
    "bs_asset": {"row_range": (161, 258), "description": "B/S Asset specialist"},
}

# Rows that are formula cells — NEVER classify into these
FORMULA_ROWS = {200, 201}


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def filter_labels(labels: list[dict], row_min: int, row_max: int) -> list[dict]:
    """Return canonical labels within [row_min, row_max], excluding formula rows."""
    return [
        l for l in labels
        if row_min <= l["sheet_row"] <= row_max and l["sheet_row"] not in FORMULA_ROWS
    ]


def filter_rules(rules: list[dict], row_min: int, row_max: int) -> list[dict]:
    """Return golden rules for rows in [row_min, row_max]. CA-override first."""
    priority_order = {"ca_override": 0, "ca_interview": 1, "legacy": 2}
    filtered = [
        r for r in rules
        if row_min <= r["canonical_sheet_row"] <= row_max
    ]
    filtered.sort(key=lambda r: priority_order.get(r.get("priority", "legacy"), 9))
    return filtered


def filter_training(examples: list[dict], row_min: int, row_max: int) -> list[dict]:
    """Return training examples for rows in [row_min, row_max], deduplicated."""
    seen = set()
    result = []
    for ex in examples:
        if row_min <= ex["label"] <= row_max:
            key = (ex["text"].lower().strip(), ex["label"])
            if key not in seen:
                seen.add(key)
                result.append(ex)
    return result


def synthesize_domain_knowledge(
    rules: list[dict], labels: list[dict], agent_name: str
) -> str:
    """Layer 4: Synthesize domain knowledge from golden rules patterns.

    Extracts:
    - CA-override contradictions ("X goes to R{a}, NOT R{b}")
    - Industry-specific routing rules
    - Common item groupings per row
    """
    lines = []

    # 1. CA-override rules — highest priority, show as explicit directives
    ca_overrides = [r for r in rules if r.get("priority") == "ca_override"]
    if ca_overrides:
        lines.append("### CRITICAL — CA Override Rules (highest priority)")
        lines.append("These rules come directly from the Chartered Accountant and override everything else:\n")
        # Group by industry
        by_industry: dict[str, list] = defaultdict(list)
        for r in ca_overrides:
            by_industry[r.get("industry_type", "all")].append(r)
        for ind in sorted(by_industry):
            if ind != "all":
                lines.append(f"**{ind.title()} companies:**")
            for r in by_industry[ind]:
                lines.append(
                    f"- \"{r['fs_item_original']}\" → R{r['canonical_sheet_row']} "
                    f"({r['canonical_field_name']})"
                )
            lines.append("")

    # 2. Industry-specific rules (non-override)
    industry_rules = [
        r for r in rules
        if r.get("industry_type", "all") != "all" and r.get("priority") != "ca_override"
    ]
    if industry_rules:
        lines.append("### Industry-Specific Classification Rules")
        by_industry = defaultdict(list)
        for r in industry_rules:
            by_industry[r["industry_type"]].append(r)
        for ind in sorted(by_industry):
            lines.append(f"\n**{ind.title()} companies:**")
            for r in by_industry[ind][:20]:  # Cap at 20 per industry
                lines.append(
                    f"- \"{r['fs_item_original']}\" → R{r['canonical_sheet_row']} "
                    f"({r['canonical_field_name']})"
                )

    # 3. Row groupings — which items commonly land in each row
    row_items: dict[int, list[str]] = defaultdict(list)
    for r in rules:
        row_items[r["canonical_sheet_row"]].append(r["fs_item_original"])
    if row_items:
        lines.append("\n### Common Items Per Row")
        for row_num in sorted(row_items):
            items = sorted(set(row_items[row_num]))[:8]  # Top 8 unique
            label = next(
                (l["name"] for l in labels if l["sheet_row"] == row_num), "?"
            )
            lines.append(f"- **R{row_num} ({label}):** {', '.join(items)}")

    return "\n".join(lines)


def build_router_prompt(labels: list[dict]) -> str:
    """Build the router agent prompt."""
    sections = []

    # Layer 1: Identity
    sections.append("""# Router Agent — CMA Classification

You are a financial document router for Indian CMA (Credit Monitoring Arrangement) reports. Your job is to assign each line item to exactly one of four specialist agents based on what section of the CMA it belongs to.

## Your Task
Given a list of financial line items extracted from Indian company financial statements, assign each item to one of these buckets:
- **pl_income** — Revenue, sales, other income (CMA rows 22-34)
- **pl_expense** — All expenses: manufacturing, admin, selling, finance, tax (CMA rows 41-108)
- **bs_liability** — Share capital, reserves, borrowings, term loans (CMA rows 110-160)
- **bs_asset** — Fixed assets, investments, inventories, debtors, cash, current liabilities (CMA rows 161-258)

## Routing Signals (priority order)
1. **source_sheet** — strongest signal:
   - "P & L", "P&L", "Trading", "Notes to P & L", "Notes P&L" → P&L agents
   - "BS", "Balance Sheet", "Notes BS", "Notes to Balance Sheet" → B/S agents
2. **section** header from extraction:
   - "income", "revenue", "sales", "other income" → pl_income
   - "expenses", "manufacturing", "admin", "selling", "depreciation", "finance cost", "tax" → pl_expense
   - "share capital", "equity", "reserves", "borrowings", "term loan", "unsecured" → bs_liability
   - "assets", "fixed assets", "investments", "inventories", "receivables", "cash", "current liabilities", "trade payables", "creditors" → bs_asset
3. **description** keywords — tiebreaker when source_sheet and section are ambiguous

## IMPORTANT: Every item MUST get a bucket
Do NOT skip or filter any items. Every item reaches a specialist. The specialist decides if it can classify it or if it becomes a doubt.

## Face vs Notes Awareness
Items have a `page_type` field ("face" or "notes"). Pass this through — specialists handle deduplication logic.""")

    # Layer 5: I/O Format
    sections.append("""
## Input Format
```json
{
  "industry_type": "manufacturing",
  "document_type": "profit_and_loss",
  "items": [
    {
      "id": "uuid-001",
      "description": "Revenue from Operations",
      "amount": 1049700540,
      "section": "income",
      "source_sheet": "P & L Ac",
      "page_type": "face"
    }
  ]
}
```

## Output Format (JSON)
Return ONLY valid JSON with this exact structure:
```json
{
  "routing": [
    {"id": "uuid-001", "bucket": "pl_income", "reason": "Revenue line from P&L"}
  ]
}
```

Valid bucket values: "pl_income", "pl_expense", "bs_liability", "bs_asset"

Route ALL items. Do not omit any item from the output.""")

    return "\n".join(sections)


def build_specialist_prompt(
    agent_name: str,
    agent_desc: str,
    labels: list[dict],
    rules: list[dict],
    training: list[dict],
) -> str:
    """Build a specialist agent prompt with all 5 layers."""
    sections = []

    # Agent display names
    display_names = {
        "pl_income": "P&L Income",
        "pl_expense": "P&L Expense",
        "bs_liability": "B/S Liability",
        "bs_asset": "B/S Asset",
    }
    display = display_names.get(agent_name, agent_name)

    row_min = AGENTS[agent_name]["row_range"][0]
    row_max = AGENTS[agent_name]["row_range"][1]

    # ── Layer 1: Identity ────────────────────────────────────────────────────
    sections.append(f"""# {display} Specialist Agent — CMA Classification

You are a specialist CMA classifier for **{display}** items (rows R{row_min}–R{row_max}).
You classify financial line items from Indian company financial statements into the correct CMA row.

You will receive a batch of items pre-routed to your section. For each item, determine:
1. The correct **cma_row** (integer) from your allowed rows below
2. Your **confidence** (0.0–1.0) in the classification
3. The **sign** (1 = add, -1 = subtract) for how this amount contributes to the CMA row
4. A brief **reasoning** for your choice

If you are less than 80% confident, mark the item as a **doubt** (cma_row: 0, cma_code: "DOUBT") and provide your top alternatives.""")

    # ── Layer 2: CMA Rows ────────────────────────────────────────────────────
    sections.append(f"\n## Your Allowed CMA Rows ({len(labels)} rows)\n")
    sections.append("| Row | Code | Name | Section |")
    sections.append("|-----|------|------|---------|")
    for l in labels:
        sections.append(f"| {l['sheet_row']} | {l['code']} | {l['name']} | {l['section']} |")

    # ── Layer 3: Golden Rules ────────────────────────────────────────────────
    sections.append(f"\n## Classification Rules ({len(rules)} rules, CA-override first)\n")
    for r in rules:
        priority_tag = f"[{r.get('priority', 'legacy').upper()}]"
        industry_tag = f"[{r.get('industry_type', 'all')}]"
        sections.append(
            f"- {priority_tag} {industry_tag} \"{r['fs_item_original']}\" → "
            f"R{r['canonical_sheet_row']} ({r['canonical_field_name']})"
        )

    # ── Layer 4: Domain Knowledge ────────────────────────────────────────────
    domain = synthesize_domain_knowledge(rules, labels, agent_name)
    if domain.strip():
        sections.append(f"\n## Domain Knowledge\n\n{domain}")

    # ── Training examples ────────────────────────────────────────────────────
    if training:
        sections.append(f"\n## Examples From Previous Companies ({min(len(training), 40)} shown)\n")
        for ex in training[:40]:
            sections.append(
                f"- \"{ex['text']}\" [{ex.get('industry_type', 'all')}] → "
                f"R{ex['label']} ({ex['label_name']})"
            )

    # ── Layer 5: Batch I/O Format ────────────────────────────────────────────
    sections.append("""
## Input Format
```json
{
  "industry_type": "manufacturing",
  "items": [
    {
      "id": "uuid-001",
      "description": "Staff Welfare Expenses",
      "amount": 234500,
      "section": "employee benefit expenses",
      "page_type": "notes",
      "has_note_breakdowns": true
    }
  ]
}
```

## Output Format (JSON)
Return ONLY valid JSON with this exact structure:
```json
{
  "classifications": [
    {
      "id": "uuid-001",
      "cma_row": 67,
      "cma_code": "II_D1",
      "confidence": 0.95,
      "sign": 1,
      "reasoning": "Staff welfare -> Salary and staff expenses (CA override rule)"
    }
  ]
}
```

### Doubt format (confidence < 0.80):
```json
{
  "id": "uuid-012",
  "cma_row": 0,
  "cma_code": "DOUBT",
  "confidence": 0.45,
  "sign": 1,
  "reasoning": "Ambiguous: could be R71 or R49, needs CA review",
  "alternatives": [
    {"cma_row": 71, "cma_code": "II_D5", "confidence": 0.45},
    {"cma_row": 49, "cma_code": "II_C9", "confidence": 0.40}
  ]
}
```

### Rules
- **sign**: 1 (add to row total) or -1 (subtract). Examples of -1: Sales Returns, Trade Discounts, Excise Duty, Closing Stock.
- **confidence < 0.80** → MUST output as doubt with alternatives
- **FORMULA ROWS** (200, 201) → NEVER classify into these. If an item seems to belong there, use the nearest non-formula row or doubt.
- **Face vs Notes dedup**: If `has_note_breakdowns` is true AND the item's `page_type` is "face", classify as doubt (cma_row: 0) to prevent double-counting. The notes breakdown items are more granular.
- Classify ALL items in the batch. Do not omit any.""")

    return "\n".join(sections)


def main():
    """Generate all 5 prompt files."""
    print("Loading ground truth files...")
    labels = load_json(CANONICAL_PATH)
    rules_data = load_json(RULES_PATH)
    rules = rules_data["rules"]
    training = load_json(TRAINING_PATH)
    print(f"  Loaded: {len(labels)} labels, {len(rules)} rules, {len(training)} training examples")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Router prompt ────────────────────────────────────────────────────────
    router_text = build_router_prompt(labels)
    (OUTPUT_DIR / "router_prompt.md").write_text(router_text, encoding="utf-8")
    print(f"  Generated: router_prompt.md ({len(router_text)} chars)")

    # ── Specialist prompts ───────────────────────────────────────────────────
    for agent_name, agent_def in AGENTS.items():
        if agent_name == "router":
            continue
        row_min, row_max = agent_def["row_range"]
        agent_labels = filter_labels(labels, row_min, row_max)
        agent_rules = filter_rules(rules, row_min, row_max)
        agent_training = filter_training(training, row_min, row_max)

        prompt_text = build_specialist_prompt(
            agent_name=agent_name,
            agent_desc=agent_def["description"],
            labels=agent_labels,
            rules=agent_rules,
            training=agent_training,
        )
        filename = f"{agent_name}_prompt.md"
        (OUTPUT_DIR / filename).write_text(prompt_text, encoding="utf-8")
        print(
            f"  Generated: {filename} "
            f"({len(agent_labels)} rows, {len(agent_rules)} rules, "
            f"{len(agent_training)} examples, {len(prompt_text)} chars)"
        )

    print("\nDone! All prompts written to:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the script to generate prompts**

Run: `cd "$(git rev-parse --show-toplevel)" && python scripts/generate_agent_prompts.py`
Expected: Creates 5 files in `backend/app/services/classification/prompts/`.

- [ ] **Step 3: Verify output — check generated files exist and have content**

Run: `wc -l backend/app/services/classification/prompts/*.md`
Expected: Each file has substantial content (router: ~80 lines, specialists: 100-500 lines).

- [ ] **Step 4: Verify determinism — run again and diff**

Run: `python scripts/generate_agent_prompts.py && git diff backend/app/services/classification/prompts/`
Expected: No diff (same input → same output).

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_agent_prompts.py \
       backend/app/services/classification/prompts/
git commit -m "feat: add prompt generation script + auto-generated agent prompts"
```

---

## Task 4: Router Agent

**Files:**
- Create: `backend/app/services/classification/agents/router.py`
- Test: `backend/tests/test_agent_router.py`

- [ ] **Step 1: Write failing tests for router**

```python
# backend/tests/test_agent_router.py
"""Tests for the router agent."""
from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock, patch

from app.services.classification.agents.router import RouterAgent

# Minimal items for testing router output parsing
SAMPLE_ITEMS = [
    {"id": "i1", "description": "Revenue from Operations", "amount": 100, "section": "income", "source_sheet": "P & L Ac", "page_type": "face"},
    {"id": "i2", "description": "Axis Bank Term Loan", "amount": 500, "section": "long term borrowings", "source_sheet": "Notes BS (2)", "page_type": "notes"},
    {"id": "i3", "description": "Raw Material Consumed", "amount": 300, "section": "cost of materials", "source_sheet": "P & L Ac", "page_type": "face"},
    {"id": "i4", "description": "Fixed Assets - Plant", "amount": 800, "section": "property plant equipment", "source_sheet": "Notes BS (1)", "page_type": "notes"},
]


class TestRouterAgent:
    @patch("app.services.classification.agents.base.OpenAI")
    def test_route_returns_four_buckets(self, mock_openai_cls, tmp_path):
        """route() should return dict with 4 bucket keys, each a list of items."""
        # Create a minimal prompt file
        prompt_file = tmp_path / "router_prompt.md"
        prompt_file.write_text("Route items to buckets.")

        # Mock API response
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "routing": [
                {"id": "i1", "bucket": "pl_income", "reason": "Revenue"},
                {"id": "i2", "bucket": "bs_liability", "reason": "Term loan"},
                {"id": "i3", "bucket": "pl_expense", "reason": "Raw material"},
                {"id": "i4", "bucket": "bs_asset", "reason": "Fixed asset"},
            ]
        })
        mock_response.usage.total_tokens = 1000
        mock_client.chat.completions.create.return_value = mock_response

        router = RouterAgent(prompt_path=str(prompt_file))
        buckets, tokens = router.route(
            items=SAMPLE_ITEMS,
            industry_type="manufacturing",
            document_type="profit_and_loss",
        )

        assert set(buckets.keys()) == {"pl_income", "pl_expense", "bs_liability", "bs_asset"}
        assert len(buckets["pl_income"]) == 1
        assert buckets["pl_income"][0]["id"] == "i1"
        assert tokens == 1000

    @patch("app.services.classification.agents.base.OpenAI")
    def test_route_api_failure_returns_all_as_doubt(self, mock_openai_cls, tmp_path):
        """If router API fails, all items go into an empty-bucket result for doubt handling."""
        prompt_file = tmp_path / "router_prompt.md"
        prompt_file.write_text("Route items.")

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API down")

        router = RouterAgent(prompt_path=str(prompt_file))
        buckets, tokens = router.route(
            items=SAMPLE_ITEMS,
            industry_type="manufacturing",
            document_type="profit_and_loss",
        )
        # On failure, all buckets empty — orchestrator handles unrouted items
        total_routed = sum(len(v) for v in buckets.values())
        assert total_routed == 0

    @patch("app.services.classification.agents.base.OpenAI")
    def test_route_unrouted_items_tracked(self, mock_openai_cls, tmp_path):
        """Items not in router response should be tracked as unrouted."""
        prompt_file = tmp_path / "router_prompt.md"
        prompt_file.write_text("Route items.")

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        # Only route 2 of 4 items
        mock_response.choices[0].message.content = json.dumps({
            "routing": [
                {"id": "i1", "bucket": "pl_income", "reason": "Revenue"},
                {"id": "i3", "bucket": "pl_expense", "reason": "Expense"},
            ]
        })
        mock_response.usage.total_tokens = 800
        mock_client.chat.completions.create.return_value = mock_response

        router = RouterAgent(prompt_path=str(prompt_file))
        buckets, tokens = router.route(
            items=SAMPLE_ITEMS,
            industry_type="manufacturing",
            document_type="profit_and_loss",
        )
        total_routed = sum(len(v) for v in buckets.values())
        # 2 routed + 2 unrouted — unrouted items are in _unrouted
        assert total_routed == 2
        assert len(router.last_unrouted) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_agent_router.py -v`
Expected: FAIL — `agents.router` module doesn't exist.

- [ ] **Step 3: Implement router agent**

```python
# backend/app/services/classification/agents/router.py
"""Router agent: assigns each item to one of 4 specialist buckets."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from app.services.classification.agents.base import BaseAgent

logger = logging.getLogger(__name__)

VALID_BUCKETS = {"pl_income", "pl_expense", "bs_liability", "bs_asset"}

# Default prompt path (auto-generated by scripts/generate_agent_prompts.py)
_DEFAULT_PROMPT = Path(__file__).parent.parent / "prompts" / "router_prompt.md"


class RouterAgent(BaseAgent):
    """Routes all items to specialist agent buckets via a single API call."""

    def __init__(self, prompt_path: str | None = None) -> None:
        super().__init__(
            name="router",
            prompt_path=prompt_path or str(_DEFAULT_PROMPT),
        )
        self.last_unrouted: list[dict] = []

    def route(
        self,
        items: list[dict],
        industry_type: str,
        document_type: str,
    ) -> tuple[dict[str, list[dict]], int]:
        """Route items to specialist buckets.

        Returns
        -------
        (buckets, tokens_used)
        buckets: dict mapping bucket name to list of original item dicts.
        """
        buckets: dict[str, list[dict]] = {b: [] for b in VALID_BUCKETS}
        self.last_unrouted = []

        if not items:
            return buckets, 0

        # Build user content
        user_content = json.dumps({
            "industry_type": industry_type,
            "document_type": document_type,
            "items": [
                {
                    "id": it["id"],
                    "description": it.get("source_text") or it.get("description", ""),
                    "amount": it.get("amount"),
                    "section": it.get("section"),
                    "source_sheet": it.get("source_sheet"),
                    "page_type": it.get("page_type"),
                }
                for it in items
            ],
        }, ensure_ascii=False)

        result, tokens = self._call_model(user_content)
        if result is None:
            logger.error("Router API call failed — all items will become doubts")
            self.last_unrouted = list(items)
            return buckets, tokens

        # Build id → item lookup
        id_to_item = {it["id"]: it for it in items}
        routed_ids = set()

        routing = result.get("routing", [])
        for entry in routing:
            item_id = entry.get("id")
            bucket = entry.get("bucket")
            if item_id in id_to_item and bucket in VALID_BUCKETS:
                buckets[bucket].append(id_to_item[item_id])
                routed_ids.add(item_id)
            elif item_id and bucket not in VALID_BUCKETS:
                logger.warning(
                    "Router: invalid bucket '%s' for item %s", bucket, item_id
                )

        # Track unrouted items
        self.last_unrouted = [it for it in items if it["id"] not in routed_ids]
        if self.last_unrouted:
            logger.warning(
                "Router: %d items not routed (will become doubts)",
                len(self.last_unrouted),
            )

        bucket_counts = {k: len(v) for k, v in buckets.items()}
        logger.info("Router result: %s (unrouted: %d)", bucket_counts, len(self.last_unrouted))
        return buckets, tokens
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_agent_router.py -v`
Expected: PASS (all 3 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/classification/agents/router.py \
       backend/tests/test_agent_router.py
git commit -m "feat: add router agent — assigns items to specialist buckets"
```

---

## Task 5: Specialist Agents

**Files:**
- Create: `backend/app/services/classification/agents/pl_income.py`
- Create: `backend/app/services/classification/agents/pl_expense.py`
- Create: `backend/app/services/classification/agents/bs_liability.py`
- Create: `backend/app/services/classification/agents/bs_asset.py`
- Test: `backend/tests/test_agent_specialists.py`

All 4 specialists share the same interface — they differ only in prompt file and name.

- [ ] **Step 1: Write failing tests for specialists**

```python
# backend/tests/test_agent_specialists.py
"""Tests for all 4 specialist agents — they share the same interface."""
from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock, patch

from app.services.classification.agents.pl_income import PLIncomeAgent
from app.services.classification.agents.pl_expense import PLExpenseAgent
from app.services.classification.agents.bs_liability import BSLiabilityAgent
from app.services.classification.agents.bs_asset import BSAssetAgent


SAMPLE_ITEMS = [
    {"id": "i1", "description": "Staff Welfare Expenses", "amount": 234500, "section": "employee benefit expenses", "page_type": "notes", "has_note_breakdowns": True},
    {"id": "i2", "description": "Sales Returns", "amount": 50000, "section": "revenue", "page_type": "notes", "has_note_breakdowns": False},
]

MOCK_SPECIALIST_RESPONSE = {
    "classifications": [
        {"id": "i1", "cma_row": 67, "cma_code": "II_D1", "confidence": 0.95, "sign": 1, "reasoning": "Staff welfare -> Salary"},
        {"id": "i2", "cma_row": 22, "cma_code": "II_A1", "confidence": 0.90, "sign": -1, "reasoning": "Sales Returns subtract from Domestic"},
    ]
}

AGENT_CLASSES = [
    ("pl_income", PLIncomeAgent),
    ("pl_expense", PLExpenseAgent),
    ("bs_liability", BSLiabilityAgent),
    ("bs_asset", BSAssetAgent),
]


@pytest.mark.parametrize("name,cls", AGENT_CLASSES, ids=[a[0] for a in AGENT_CLASSES])
class TestSpecialistAgent:
    @patch("app.services.classification.agents.base.OpenAI")
    def test_classify_batch_returns_classifications(self, mock_openai_cls, name, cls, tmp_path):
        """classify_batch returns list of classification dicts."""
        prompt_file = tmp_path / f"{name}_prompt.md"
        prompt_file.write_text(f"You are the {name} specialist.")

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(MOCK_SPECIALIST_RESPONSE)
        mock_response.usage.total_tokens = 2000
        mock_client.chat.completions.create.return_value = mock_response

        agent = cls(prompt_path=str(prompt_file))
        results, tokens = agent.classify_batch(
            items=SAMPLE_ITEMS, industry_type="manufacturing"
        )

        assert len(results) == 2
        assert results[0]["id"] == "i1"
        assert results[0]["cma_row"] == 67
        assert results[0]["sign"] == 1
        assert results[1]["sign"] == -1
        assert tokens == 2000

    @patch("app.services.classification.agents.base.OpenAI")
    def test_classify_batch_api_failure_returns_doubts(self, mock_openai_cls, name, cls, tmp_path):
        """If API fails, all items returned as doubts."""
        prompt_file = tmp_path / f"{name}_prompt.md"
        prompt_file.write_text(f"You are the {name} specialist.")

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API down")

        agent = cls(prompt_path=str(prompt_file))
        results, tokens = agent.classify_batch(
            items=SAMPLE_ITEMS, industry_type="manufacturing"
        )

        assert len(results) == 2
        assert all(r["cma_row"] == 0 for r in results)
        assert all(r["cma_code"] == "DOUBT" for r in results)
        assert all(r["confidence"] == 0.0 for r in results)

    @patch("app.services.classification.agents.base.OpenAI")
    def test_classify_batch_empty_returns_empty(self, mock_openai_cls, name, cls, tmp_path):
        """Empty item list returns empty results without API call."""
        prompt_file = tmp_path / f"{name}_prompt.md"
        prompt_file.write_text(f"You are the {name} specialist.")
        mock_openai_cls.return_value = MagicMock()

        agent = cls(prompt_path=str(prompt_file))
        results, tokens = agent.classify_batch(items=[], industry_type="manufacturing")
        assert results == []
        assert tokens == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_agent_specialists.py -v`
Expected: FAIL — specialist modules don't exist.

- [ ] **Step 3: Create the specialist base mixin**

Add `classify_batch` to `BaseAgent` in `backend/app/services/classification/agents/base.py`:

```python
    def classify_batch(
        self, items: list[dict], industry_type: str
    ) -> tuple[list[dict], int]:
        """Classify a batch of items. Returns (classifications, tokens_used).

        On API failure, returns doubt records for all items.
        """
        if not items:
            return [], 0

        user_content = json.dumps({
            "industry_type": industry_type,
            "items": [
                {
                    "id": it["id"],
                    "description": it.get("source_text") or it.get("description", ""),
                    "amount": it.get("amount"),
                    "section": it.get("section"),
                    "page_type": it.get("page_type"),
                    "has_note_breakdowns": it.get("has_note_breakdowns", False),
                }
                for it in items
            ],
        }, ensure_ascii=False)

        result, tokens = self._call_model(user_content)

        if result is None:
            # API failure: return doubts for all items
            return [self._make_doubt(it, "API call failed") for it in items], tokens

        classifications = result.get("classifications", [])

        # Validate and normalize — ensure every input item has a result
        classified_ids = {c["id"] for c in classifications if "id" in c}
        for it in items:
            if it["id"] not in classified_ids:
                classifications.append(self._make_doubt(it, "Missing from agent response"))

        return classifications, tokens

    @staticmethod
    def _make_doubt(item: dict, reason: str) -> dict:
        """Create a doubt record for an item."""
        return {
            "id": item["id"],
            "cma_row": 0,
            "cma_code": "DOUBT",
            "confidence": 0.0,
            "sign": 1,
            "reasoning": reason,
            "alternatives": [],
        }
```

- [ ] **Step 4: Create all 4 specialist files**

Each specialist is minimal — just sets its prompt path and name.

```python
# backend/app/services/classification/agents/pl_income.py
"""P&L Income specialist agent (CMA rows R22-R34)."""
from __future__ import annotations

from pathlib import Path

from app.services.classification.agents.base import BaseAgent

_DEFAULT_PROMPT = Path(__file__).parent.parent / "prompts" / "pl_income_prompt.md"


class PLIncomeAgent(BaseAgent):
    """Classifies P&L income items: domestic/export sales, other income."""

    def __init__(self, prompt_path: str | None = None) -> None:
        super().__init__(
            name="pl_income",
            prompt_path=prompt_path or str(_DEFAULT_PROMPT),
        )
```

```python
# backend/app/services/classification/agents/pl_expense.py
"""P&L Expense specialist agent (CMA rows R41-R108)."""
from __future__ import annotations

from pathlib import Path

from app.services.classification.agents.base import BaseAgent

_DEFAULT_PROMPT = Path(__file__).parent.parent / "prompts" / "pl_expense_prompt.md"


class PLExpenseAgent(BaseAgent):
    """Classifies P&L expenses: manufacturing, admin, finance, tax."""

    def __init__(self, prompt_path: str | None = None) -> None:
        super().__init__(
            name="pl_expense",
            prompt_path=prompt_path or str(_DEFAULT_PROMPT),
        )
```

```python
# backend/app/services/classification/agents/bs_liability.py
"""B/S Liability specialist agent (CMA rows R110-R160)."""
from __future__ import annotations

from pathlib import Path

from app.services.classification.agents.base import BaseAgent

_DEFAULT_PROMPT = Path(__file__).parent.parent / "prompts" / "bs_liability_prompt.md"


class BSLiabilityAgent(BaseAgent):
    """Classifies B/S liabilities: capital, reserves, borrowings."""

    def __init__(self, prompt_path: str | None = None) -> None:
        super().__init__(
            name="bs_liability",
            prompt_path=prompt_path or str(_DEFAULT_PROMPT),
        )
```

```python
# backend/app/services/classification/agents/bs_asset.py
"""B/S Asset specialist agent (CMA rows R161-R258)."""
from __future__ import annotations

from pathlib import Path

from app.services.classification.agents.base import BaseAgent

_DEFAULT_PROMPT = Path(__file__).parent.parent / "prompts" / "bs_asset_prompt.md"


class BSAssetAgent(BaseAgent):
    """Classifies B/S assets: fixed assets, investments, inventories, debtors, cash."""

    def __init__(self, prompt_path: str | None = None) -> None:
        super().__init__(
            name="bs_asset",
            prompt_path=prompt_path or str(_DEFAULT_PROMPT),
        )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_agent_specialists.py -v`
Expected: PASS (12 tests: 3 per agent × 4 agents)

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/classification/agents/base.py \
       backend/app/services/classification/agents/pl_income.py \
       backend/app/services/classification/agents/pl_expense.py \
       backend/app/services/classification/agents/bs_liability.py \
       backend/app/services/classification/agents/bs_asset.py \
       backend/tests/test_agent_specialists.py
git commit -m "feat: add 4 specialist agents (pl_income, pl_expense, bs_liability, bs_asset)"
```

---

## Task 6: MultiAgentPipeline Orchestrator

**Files:**
- Create: `backend/app/services/classification/multi_agent_pipeline.py`
- Test: `backend/tests/test_multi_agent_pipeline.py`

This is the core — it replaces `ClassificationPipeline`.

- [ ] **Step 1: Write failing tests for orchestrator**

```python
# backend/tests/test_multi_agent_pipeline.py
"""Tests for the MultiAgentPipeline orchestrator."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.services.classification.multi_agent_pipeline import MultiAgentPipeline


# ── Fixtures ─────────────────────────────────────────────────────────────────

SAMPLE_ITEMS = [
    {"id": "i1", "source_text": "Revenue from Operations", "amount": 1000000, "section": "income", "source_sheet": "P & L", "page_type": "face", "is_verified": True},
    {"id": "i2", "source_text": "Axis Bank Term Loan", "amount": 500000, "section": "borrowings", "source_sheet": "Notes BS", "page_type": "notes", "is_verified": True},
    {"id": "i3", "source_text": "Staff Welfare", "amount": 23000, "section": "employee expenses", "source_sheet": "P & L", "page_type": "face", "is_verified": True},
]

LEARNED_MAPPINGS = [
    {"source_text": "revenue from operations", "cma_field_name": "Domestic", "cma_input_row": 22},
]


class TestLearnedMappingsCheck:
    def test_exact_match_skips_ai(self):
        """Items matching learned_mappings should be classified without AI."""
        pipeline = MultiAgentPipeline.__new__(MultiAgentPipeline)
        result = pipeline._check_learned_mappings(
            items=SAMPLE_ITEMS,
            learned_mappings=LEARNED_MAPPINGS,
        )
        assert len(result["matched"]) == 1
        assert result["matched"][0]["item"]["id"] == "i1"
        assert result["matched"][0]["cma_row"] == 22
        assert len(result["remaining"]) == 2

    def test_no_mappings_returns_all_remaining(self):
        """When no learned_mappings, all items go to remaining."""
        pipeline = MultiAgentPipeline.__new__(MultiAgentPipeline)
        result = pipeline._check_learned_mappings(
            items=SAMPLE_ITEMS,
            learned_mappings=[],
        )
        assert len(result["matched"]) == 0
        assert len(result["remaining"]) == 3


class TestBuildClassificationRecord:
    def test_confident_result(self):
        """Builds correct DB record for a high-confidence classification."""
        pipeline = MultiAgentPipeline.__new__(MultiAgentPipeline)
        record = pipeline._build_record(
            item=SAMPLE_ITEMS[0],
            classification={"id": "i1", "cma_row": 22, "cma_code": "II_A1", "confidence": 0.95, "sign": 1, "reasoning": "Revenue"},
            client_id="client-1",
            cma_column="B",
            method="multi_agent",
        )
        assert record["line_item_id"] == "i1"
        assert record["cma_row"] == 22
        assert record["confidence_score"] == 0.95
        assert record["is_doubt"] is False
        assert record["status"] == "approved"

    def test_doubt_result(self):
        """Builds correct DB record for a doubt."""
        pipeline = MultiAgentPipeline.__new__(MultiAgentPipeline)
        record = pipeline._build_record(
            item=SAMPLE_ITEMS[0],
            classification={"id": "i1", "cma_row": 0, "cma_code": "DOUBT", "confidence": 0.45, "sign": 1, "reasoning": "Ambiguous", "alternatives": [{"cma_row": 71, "cma_code": "II_D5", "confidence": 0.45}]},
            client_id="client-1",
            cma_column="B",
            method="multi_agent",
        )
        assert record["is_doubt"] is True
        assert record["status"] == "needs_review"
        assert record["cma_row"] == 0
        assert len(record["alternative_fields"]) == 1


class TestCombineResults:
    def test_combine_merges_all_sources(self):
        """Combine should merge learned + specialist results."""
        pipeline = MultiAgentPipeline.__new__(MultiAgentPipeline)
        learned = [
            {"line_item_id": "i1", "cma_row": 22, "confidence_score": 1.0, "is_doubt": False, "status": "approved"},
        ]
        specialist = [
            {"line_item_id": "i2", "cma_row": 136, "confidence_score": 0.90, "is_doubt": False, "status": "approved"},
        ]
        doubts = [
            {"line_item_id": "i3", "cma_row": 0, "confidence_score": 0.0, "is_doubt": True, "status": "needs_review"},
        ]
        combined = pipeline._combine_results(learned, specialist, doubts)
        assert len(combined) == 3
        ids = {r["line_item_id"] for r in combined}
        assert ids == {"i1", "i2", "i3"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_multi_agent_pipeline.py -v`
Expected: FAIL — `multi_agent_pipeline` module doesn't exist.

- [ ] **Step 3: Implement MultiAgentPipeline**

```python
# backend/app/services/classification/multi_agent_pipeline.py
"""Multi-agent classification orchestrator.

Replaces ClassificationPipeline with a 5-agent system:
1 router + 4 specialists (P&L Income, P&L Expense, B/S Liability, B/S Asset).

Flow:
  1. Fetch verified line items from DB
  2. Check learned_mappings — exact matches skip AI
  3. Router assigns remaining items to 4 specialist buckets (1 API call)
  4. 4 specialists classify in parallel via asyncio.gather (4 API calls)
  5. Combine all results + batch insert to classifications table
"""
from __future__ import annotations

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor

from app.config import get_settings
from app.dependencies import get_service_client
from app.mappings.year_columns import get_year_column
from app.services.extraction._types import normalize_line_text

from app.services.classification.agents.router import RouterAgent
from app.services.classification.agents.pl_income import PLIncomeAgent
from app.services.classification.agents.pl_expense import PLExpenseAgent
from app.services.classification.agents.bs_liability import BSLiabilityAgent
from app.services.classification.agents.bs_asset import BSAssetAgent

logger = logging.getLogger(__name__)

# Confidence thresholds (same as old pipeline)
AUTO_APPROVE_THRESHOLD = 0.85
HIGH_CONFIDENCE_FLOOR = 0.85
DOUBT_THRESHOLD = 0.80

# Cost guards
MAX_TOKENS_PER_RUN = 500_000
MAX_ITEMS_PER_DOCUMENT = 500

# Thread pool for running sync API calls in parallel
_executor = ThreadPoolExecutor(max_workers=5)


def _auto_status(confidence: float, is_doubt: bool) -> str:
    if is_doubt:
        return "needs_review"
    return "approved" if confidence >= AUTO_APPROVE_THRESHOLD else "auto_classified"


class MultiAgentPipeline:
    """Orchestrates multi-agent classification for financial line items."""

    def __init__(self) -> None:
        self._router = RouterAgent()
        self._specialists = {
            "pl_income": PLIncomeAgent(),
            "pl_expense": PLExpenseAgent(),
            "bs_liability": BSLiabilityAgent(),
            "bs_asset": BSAssetAgent(),
        }
        self._total_tokens = 0

    # ── Public API ───────────────────────────────────────────────────────────

    def classify_document(
        self,
        document_id: str,
        client_id: str,
        industry_type: str,
        document_type: str,
        financial_year: int,
    ) -> dict:
        """Classify all verified line items for a document.

        Returns summary: {total, high_confidence, medium_confidence, needs_review}.
        """
        service = get_service_client()
        self._total_tokens = 0
        cma_column = get_year_column(financial_year, financial_year) or "B"

        # ── 1. Fetch learned_mappings ────────────────────────────────────────
        learned_mappings = self._fetch_learned_mappings(service, industry_type)

        # ── 2. Cross-document awareness ──────────────────────────────────────
        has_note_breakdowns = self._check_note_breakdowns(
            service, document_id, client_id, financial_year
        )

        # ── 3. Fetch all verified line items ─────────────────────────────────
        line_items = self._fetch_items(service, document_id)
        if not line_items:
            return {"total": 0, "high_confidence": 0, "medium_confidence": 0, "needs_review": 0}

        # Normalize descriptions and inject has_note_breakdowns
        for item in line_items:
            raw = item.get("source_text") or item.get("description") or ""
            item["_normalized"] = normalize_line_text(raw)
            item["has_note_breakdowns"] = has_note_breakdowns

        # ── 4. Check learned_mappings ────────────────────────────────────────
        lm_result = self._check_learned_mappings(line_items, learned_mappings)
        learned_records = [
            self._build_record(
                item=m["item"],
                classification={
                    "id": m["item"]["id"],
                    "cma_row": m["cma_row"],
                    "cma_code": m.get("cma_code", ""),
                    "confidence": 1.0,
                    "sign": 1,
                    "reasoning": "Matched learned_mappings (CA-corrected)",
                },
                client_id=client_id,
                cma_column=cma_column,
                method="learned_mapping",
            )
            for m in lm_result["matched"]
        ]
        remaining = lm_result["remaining"]
        logger.info(
            "Learned mappings: %d matched, %d remaining for AI",
            len(learned_records), len(remaining),
        )

        if not remaining:
            # All items matched learned_mappings — no AI needed
            self._batch_insert(service, learned_records)
            return self._summarize(learned_records)

        # ── 5. Router call ───────────────────────────────────────────────────
        buckets, router_tokens = self._router.route(
            items=remaining,
            industry_type=industry_type,
            document_type=document_type,
        )
        self._total_tokens += router_tokens

        # Items the router couldn't route → doubts
        unrouted_records = [
            self._build_record(
                item=it,
                classification={
                    "id": it["id"], "cma_row": 0, "cma_code": "DOUBT",
                    "confidence": 0.0, "sign": 1,
                    "reasoning": "Router failed to assign bucket",
                },
                client_id=client_id,
                cma_column=cma_column,
                method="multi_agent_doubt",
            )
            for it in self._router.last_unrouted
        ]

        # ── 6. Specialist calls in parallel ──────────────────────────────────
        specialist_records = self._run_specialists(
            buckets=buckets,
            industry_type=industry_type,
            client_id=client_id,
            cma_column=cma_column,
        )

        # ── 7. Combine + save ────────────────────────────────────────────────
        all_records = self._combine_results(
            learned_records, specialist_records, unrouted_records
        )
        self._batch_insert(service, all_records)

        logger.info(
            "classify_document complete: doc=%s total=%d tokens=%d",
            document_id, len(all_records), self._total_tokens,
        )
        return self._summarize(all_records)

    # ── Learned mappings ─────────────────────────────────────────────────────

    def _check_learned_mappings(
        self, items: list[dict], learned_mappings: list[dict]
    ) -> dict:
        """Check items against learned_mappings. Returns matched + remaining."""
        if not learned_mappings:
            return {"matched": [], "remaining": list(items)}

        # Build lookup: normalized source_text → mapping
        lm_lookup = {}
        for lm in learned_mappings:
            key = (lm.get("source_text") or "").strip().lower()
            if key:
                lm_lookup[key] = lm

        matched = []
        remaining = []
        for item in items:
            normalized = (item.get("_normalized") or item.get("source_text") or "").strip().lower()
            if normalized in lm_lookup:
                lm = lm_lookup[normalized]
                matched.append({
                    "item": item,
                    "cma_row": lm.get("cma_input_row", 0),
                    "cma_field_name": lm.get("cma_field_name", ""),
                })
            else:
                remaining.append(item)

        return {"matched": matched, "remaining": remaining}

    # ── Specialist execution ─────────────────────────────────────────────────

    def _run_specialists(
        self,
        buckets: dict[str, list[dict]],
        industry_type: str,
        client_id: str,
        cma_column: str,
    ) -> list[dict]:
        """Run all specialists in parallel (asyncio + thread pool)."""
        records = []

        # Build tasks for non-empty buckets
        tasks = {}
        for bucket_name, bucket_items in buckets.items():
            if not bucket_items:
                continue
            if bucket_name not in self._specialists:
                continue
            tasks[bucket_name] = bucket_items

        if not tasks:
            return records

        # Run specialists in parallel using threads
        # (each specialist's classify_batch is synchronous — it calls OpenRouter)
        import concurrent.futures

        def run_one(bucket_name: str, items: list[dict]):
            agent = self._specialists[bucket_name]
            return bucket_name, agent.classify_batch(items, industry_type)

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            futures = {
                pool.submit(run_one, bn, bi): bn
                for bn, bi in tasks.items()
            }
            for future in concurrent.futures.as_completed(futures):
                bucket_name = futures[future]
                try:
                    _, (classifications, tokens) = future.result()
                    self._total_tokens += tokens

                    # Build id → item lookup for this bucket
                    id_to_item = {it["id"]: it for it in tasks[bucket_name]}

                    for cls in classifications:
                        item = id_to_item.get(cls.get("id"))
                        if item is None:
                            continue
                        records.append(
                            self._build_record(
                                item=item,
                                classification=cls,
                                client_id=client_id,
                                cma_column=cma_column,
                                method=f"multi_agent_{bucket_name}",
                            )
                        )
                except Exception as exc:
                    logger.error(
                        "Specialist '%s' failed: %s — items become doubts",
                        bucket_name, exc,
                    )
                    for item in tasks[bucket_name]:
                        records.append(
                            self._build_record(
                                item=item,
                                classification={
                                    "id": item["id"], "cma_row": 0, "cma_code": "DOUBT",
                                    "confidence": 0.0, "sign": 1,
                                    "reasoning": f"Specialist {bucket_name} failed: {exc}",
                                },
                                client_id=client_id,
                                cma_column=cma_column,
                                method="multi_agent_doubt",
                            )
                        )

        return records

    # ── Record building ──────────────────────────────────────────────────────

    def _build_record(
        self,
        item: dict,
        classification: dict,
        client_id: str,
        cma_column: str,
        method: str,
    ) -> dict:
        """Build a DB-ready classification record from agent output."""
        cma_row = classification.get("cma_row", 0)
        confidence = classification.get("confidence", 0.0)
        is_doubt = cma_row == 0 or classification.get("cma_code") == "DOUBT" or confidence < DOUBT_THRESHOLD

        return {
            "line_item_id": item["id"],
            "client_id": client_id,
            "cma_field_name": classification.get("cma_code", "UNCLASSIFIED") if not is_doubt else "UNCLASSIFIED",
            "cma_sheet": "input_sheet",
            "cma_row": cma_row if not is_doubt else 0,
            "cma_column": cma_column,
            "broad_classification": None,
            "classification_method": method,
            "confidence_score": confidence,
            "fuzzy_match_score": 0,
            "is_doubt": is_doubt,
            "doubt_reason": classification.get("reasoning") if is_doubt else None,
            "ai_best_guess": classification.get("cma_code"),
            "alternative_fields": classification.get("alternatives", []),
            "status": _auto_status(confidence, is_doubt),
        }

    def _combine_results(
        self, learned: list[dict], specialist: list[dict], doubts: list[dict]
    ) -> list[dict]:
        """Merge all classification records."""
        return learned + specialist + doubts

    def _summarize(self, records: list[dict]) -> dict:
        """Produce summary counts from classification records."""
        total = len(records)
        high = sum(1 for r in records if not r["is_doubt"] and r["confidence_score"] >= HIGH_CONFIDENCE_FLOOR)
        medium = sum(1 for r in records if not r["is_doubt"] and r["confidence_score"] < HIGH_CONFIDENCE_FLOOR)
        needs_review = sum(1 for r in records if r["is_doubt"])
        return {
            "total": total,
            "high_confidence": high,
            "medium_confidence": medium,
            "needs_review": needs_review,
        }

    # ── DB helpers ───────────────────────────────────────────────────────────

    def _fetch_learned_mappings(self, service, industry_type: str) -> list[dict]:
        try:
            resp = (
                service.table("learned_mappings")
                .select("source_text,cma_field_name,cma_input_row")
                .eq("industry_type", industry_type)
                .execute()
            )
            return resp.data or []
        except Exception as exc:
            logger.warning("Could not fetch learned_mappings: %s", exc)
            return []

    def _check_note_breakdowns(
        self, service, document_id: str, client_id: str, financial_year: int
    ) -> bool:
        try:
            sibling_docs = (
                service.table("documents")
                .select("id")
                .eq("client_id", client_id)
                .eq("financial_year", financial_year)
                .neq("id", document_id)
                .execute()
            )
            sibling_ids = [d["id"] for d in (sibling_docs.data or [])]
            all_doc_ids = [document_id] + sibling_ids
            notes_check = (
                service.table("extracted_line_items")
                .select("id", count="exact")
                .in_("document_id", all_doc_ids)
                .eq("page_type", "notes")
                .eq("is_verified", True)
                .limit(1)
                .execute()
            )
            return (notes_check.count or 0) > 0
        except Exception as exc:
            logger.warning("Cross-doc awareness query failed: %s", exc)
            return False

    def _fetch_items(self, service, document_id: str) -> list[dict]:
        _PAGE = 1000
        items: list[dict] = []
        offset = 0
        while True:
            page = (
                service.table("extracted_line_items")
                .select("*")
                .eq("document_id", document_id)
                .eq("is_verified", True)
                .range(offset, offset + _PAGE - 1)
                .execute()
            )
            batch = page.data or []
            items.extend(batch)
            if len(batch) < _PAGE:
                break
            offset += _PAGE
        return items

    def _batch_insert(self, service, records: list[dict]) -> None:
        """Insert classification records in batches."""
        _BATCH = 200
        for i in range(0, len(records), _BATCH):
            batch = records[i : i + _BATCH]
            service.table("classifications").insert(batch).execute()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_multi_agent_pipeline.py -v`
Expected: PASS (all 5 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/classification/multi_agent_pipeline.py \
       backend/tests/test_multi_agent_pipeline.py
git commit -m "feat: add MultiAgentPipeline orchestrator — router + 4 specialists"
```

---

## Task 7: Wire-Up — Replace Old Pipeline

**Files:**
- Modify: `backend/app/workers/classification_tasks.py`
- Modify: `backend/app/services/classification/__init__.py`

- [ ] **Step 1: Update classification_tasks.py**

Replace the import and usage:

```python
# In backend/app/workers/classification_tasks.py, line 12:
# OLD:
from app.services.classification.pipeline import ClassificationPipeline
# NEW:
from app.services.classification.multi_agent_pipeline import MultiAgentPipeline
```

```python
# In backend/app/workers/classification_tasks.py, line 100:
# OLD:
    pipeline = ClassificationPipeline()
# NEW:
    pipeline = MultiAgentPipeline()
```

- [ ] **Step 2: Update __init__.py**

```python
# backend/app/services/classification/__init__.py
"""Multi-agent classification pipeline: 1 router + 4 specialist agents."""
```

- [ ] **Step 3: Verify the worker imports correctly**

Run: `cd backend && python -c "from app.workers.classification_tasks import run_classification; print('OK')"`
Expected: "OK" (no import errors)

- [ ] **Step 4: Commit**

```bash
git add backend/app/workers/classification_tasks.py \
       backend/app/services/classification/__init__.py
git commit -m "feat: wire MultiAgentPipeline into classification worker"
```

---

## Task 8: Offline Eval Script

**Files:**
- Create: `scripts/eval_multi_agent.py`

This script tests classification accuracy against ground truth WITHOUT Supabase or PDF extraction.

- [ ] **Step 1: Create eval script**

```python
# scripts/eval_multi_agent.py
"""Offline evaluation: test multi-agent classification against ground truth.

Runs the router + specialists on GT items and compares to known-correct cma_row.
No Supabase needed — reads GT files directly and calls OpenRouter.

Usage:
    python scripts/eval_multi_agent.py --company BCIPL
    python scripts/eval_multi_agent.py --all
    python scripts/eval_multi_agent.py --company BCIPL --agent pl_expense
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Add backend to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

# Must set minimal env vars before importing app modules
os.environ.setdefault("SUPABASE_URL", "https://placeholder.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "placeholder")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "placeholder")

from app.services.classification.agents.router import RouterAgent
from app.services.classification.agents.pl_income import PLIncomeAgent
from app.services.classification.agents.pl_expense import PLExpenseAgent
from app.services.classification.agents.bs_liability import BSLiabilityAgent
from app.services.classification.agents.bs_asset import BSAssetAgent

GT_BASE = PROJECT_ROOT / "CMA_Ground_Truth_v1"

COMPANIES = {
    "BCIPL": {"industry": "manufacturing", "path": "companies/BCIPL/ground_truth_corrected.json"},
    "MSL": {"industry": "manufacturing", "path": "companies/MSL/ground_truth_corrected.json"},
    "INPL": {"industry": "manufacturing", "path": "companies/INPL/ground_truth_corrected.json"},
    "SLIPL": {"industry": "manufacturing", "path": "companies/SLIPL/ground_truth_corrected.json"},
    "Dynamic_Air": {"industry": "services", "path": "companies/Dynamic_Air/ground_truth_corrected.json"},
    "Kurunji_Retail": {"industry": "trading", "path": "companies/Kurunji_Retail/ground_truth_corrected.json"},
    "Mehta_Computer": {"industry": "trading", "path": "companies/Mehta_Computer/ground_truth_corrected.json"},
    "SR_Papers": {"industry": "manufacturing", "path": "companies/SR_Papers/ground_truth_corrected.json"},
    "SSSS": {"industry": "services", "path": "companies/SSSS/ground_truth_corrected.json"},
}

# Agent row ranges for misroute detection
AGENT_RANGES = {
    "pl_income": (22, 34),
    "pl_expense": (41, 108),
    "bs_liability": (110, 160),
    "bs_asset": (161, 258),
}


def expected_bucket(cma_row: int) -> str | None:
    """Return the correct bucket for a GT cma_row."""
    for name, (lo, hi) in AGENT_RANGES.items():
        if lo <= cma_row <= hi:
            return name
    return None


def load_gt(company: str) -> list[dict]:
    """Load ground truth entries for a company."""
    info = COMPANIES[company]
    path = GT_BASE / info["path"]
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("database_entries", [])
    # Deduplicate by (raw_text, cma_row) — keep first occurrence
    seen = set()
    unique = []
    for e in entries:
        key = (e["raw_text"].lower().strip(), e["cma_row"])
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique


def run_eval(company: str, agent_filter: str | None = None) -> dict:
    """Run full pipeline eval on one company."""
    info = COMPANIES[company]
    industry = info["industry"]
    gt_entries = load_gt(company)

    print(f"\n{'='*60}")
    print(f"Company: {company} ({industry}) — {len(gt_entries)} GT items")
    print(f"{'='*60}")

    # Convert GT entries to item format expected by agents
    items = []
    gt_lookup = {}  # id → expected cma_row
    for i, entry in enumerate(gt_entries):
        item_id = f"gt-{i:04d}"
        items.append({
            "id": item_id,
            "source_text": entry["raw_text"],
            "description": entry["raw_text"],
            "amount": entry.get("amount", 0),
            "section": entry.get("section", ""),
            "source_sheet": entry.get("sheet_name", ""),
            "page_type": "notes",  # GT items are typically from notes
            "has_note_breakdowns": False,
        })
        gt_lookup[item_id] = entry["cma_row"]

    # Step 1: Route
    router = RouterAgent()
    buckets, router_tokens = router.route(items, industry, "profit_and_loss")

    # Routing accuracy
    misrouted = 0
    for bucket_name, bucket_items in buckets.items():
        for item in bucket_items:
            expected = expected_bucket(gt_lookup[item["id"]])
            if expected and expected != bucket_name:
                misrouted += 1

    routed_total = sum(len(v) for v in buckets.values())
    print(f"\nRouter: {routed_total}/{len(items)} routed, {len(router.last_unrouted)} unrouted, {misrouted} misrouted")

    # Step 2: Run specialists (optionally filtered)
    specialists = {
        "pl_income": PLIncomeAgent(),
        "pl_expense": PLExpenseAgent(),
        "bs_liability": BSLiabilityAgent(),
        "bs_asset": BSAssetAgent(),
    }

    correct = 0
    wrong = 0
    doubt = 0
    confusion: Counter = Counter()
    per_agent: dict[str, dict] = {}
    total_tokens = router_tokens

    for bucket_name, bucket_items in buckets.items():
        if agent_filter and bucket_name != agent_filter:
            continue
        if not bucket_items:
            continue

        agent = specialists[bucket_name]
        results, tokens = agent.classify_batch(bucket_items, industry)
        total_tokens += tokens

        agent_correct = 0
        agent_wrong = 0
        agent_doubt = 0

        result_lookup = {r["id"]: r for r in results}
        for item in bucket_items:
            expected_row = gt_lookup[item["id"]]
            cls = result_lookup.get(item["id"], {})
            predicted_row = cls.get("cma_row", 0)
            conf = cls.get("confidence", 0.0)

            if predicted_row == 0 or conf < 0.80:
                doubt += 1
                agent_doubt += 1
            elif predicted_row == expected_row:
                correct += 1
                agent_correct += 1
            else:
                wrong += 1
                agent_wrong += 1
                confusion[(expected_row, predicted_row)] += 1

        total_in_agent = agent_correct + agent_wrong + agent_doubt
        agent_acc = agent_correct / max(total_in_agent - agent_doubt, 1) * 100
        per_agent[bucket_name] = {
            "correct": agent_correct,
            "wrong": agent_wrong,
            "doubt": agent_doubt,
            "accuracy": agent_acc,
        }
        print(f"  {bucket_name}: {agent_correct}/{total_in_agent} correct, {agent_doubt} doubts ({agent_acc:.1f}% acc)")

    # Summary
    classified = correct + wrong
    total_evaluated = correct + wrong + doubt
    accuracy = correct / max(classified, 1) * 100
    doubt_rate = doubt / max(total_evaluated, 1) * 100

    print(f"\n--- SUMMARY ---")
    print(f"Total items:    {total_evaluated}")
    print(f"Correct:        {correct}")
    print(f"Wrong:          {wrong}")
    print(f"Doubts:         {doubt}")
    print(f"Accuracy:       {accuracy:.1f}% (of classified items)")
    print(f"Doubt rate:     {doubt_rate:.1f}%")
    print(f"Tokens used:    {total_tokens}")

    if confusion:
        print(f"\nTop confusion pairs:")
        for (exp, pred), count in confusion.most_common(10):
            print(f"  Expected R{exp} → Predicted R{pred}: {count} times")

    return {
        "company": company,
        "total": total_evaluated,
        "correct": correct,
        "wrong": wrong,
        "doubt": doubt,
        "accuracy": accuracy,
        "doubt_rate": doubt_rate,
        "tokens": total_tokens,
        "per_agent": per_agent,
    }


def main():
    parser = argparse.ArgumentParser(description="Eval multi-agent classification against GT")
    parser.add_argument("--company", type=str, help="Company code (e.g., BCIPL)")
    parser.add_argument("--all", action="store_true", help="Run on all GT companies")
    parser.add_argument("--agent", type=str, help="Filter to one specialist agent")
    args = parser.parse_args()

    if not args.company and not args.all:
        parser.error("Provide --company NAME or --all")

    if args.all:
        all_results = []
        for company in COMPANIES:
            result = run_eval(company, args.agent)
            all_results.append(result)

        print(f"\n{'='*60}")
        print("AGGREGATE RESULTS")
        print(f"{'='*60}")
        total_correct = sum(r["correct"] for r in all_results)
        total_wrong = sum(r["wrong"] for r in all_results)
        total_doubt = sum(r["doubt"] for r in all_results)
        total = total_correct + total_wrong + total_doubt
        classified = total_correct + total_wrong
        print(f"Total items:  {total}")
        print(f"Accuracy:     {total_correct / max(classified, 1) * 100:.1f}%")
        print(f"Doubt rate:   {total_doubt / max(total, 1) * 100:.1f}%")
    else:
        run_eval(args.company, args.agent)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify script loads without errors (dry run)**

Run: `cd "$(git rev-parse --show-toplevel)" && python scripts/eval_multi_agent.py --help`
Expected: Shows usage help without import errors.

- [ ] **Step 3: Commit**

```bash
git add scripts/eval_multi_agent.py
git commit -m "feat: add offline eval script — tests multi-agent accuracy against GT"
```

---

## Task 9: Delete Old Files + Update Tests

**Files:**
- Delete: `backend/app/services/classification/pipeline.py`
- Delete: `backend/app/services/classification/scoped_classifier.py`
- Delete: `backend/app/services/classification/ai_classifier.py`
- Delete: `backend/app/services/classification/fuzzy_matcher.py`
- Delete: `backend/tests/test_classification_pipeline.py`
- Delete: `backend/tests/test_scoped_classifier.py`
- Delete: `backend/tests/test_ai_classifier.py`

- [ ] **Step 1: Verify no remaining imports of old files**

Run: `cd backend && grep -r "from app.services.classification.pipeline import\|from app.services.classification.scoped_classifier import\|from app.services.classification.ai_classifier import\|from app.services.classification.fuzzy_matcher import" app/ --include="*.py" | grep -v "__pycache__"`

Expected: Only the OLD files themselves reference each other. The worker should already import from `multi_agent_pipeline`.

- [ ] **Step 2: Delete old implementation files**

```bash
git rm backend/app/services/classification/pipeline.py
git rm backend/app/services/classification/scoped_classifier.py
git rm backend/app/services/classification/ai_classifier.py
git rm backend/app/services/classification/fuzzy_matcher.py
```

- [ ] **Step 3: Delete old test files**

```bash
git rm backend/tests/test_classification_pipeline.py
git rm backend/tests/test_scoped_classifier.py
git rm backend/tests/test_ai_classifier.py
```

- [ ] **Step 4: Check for broken imports in remaining files**

The `AIClassificationResult` dataclass was in `ai_classifier.py`. Check if anything else references it:

Run: `cd backend && grep -r "AIClassificationResult" app/ tests/ --include="*.py" | grep -v "__pycache__"`

If any files remain that import it, they need updating. The learning_system.py and any router endpoints should NOT reference it — they work with raw dicts from the DB.

- [ ] **Step 5: Run all remaining tests**

Run: `cd backend && python -m pytest tests/ -v --ignore=tests/test_fuzzy_matcher.py 2>&1 | tail -30`

Expected: All new tests pass. No import errors from deleted files.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "cleanup: delete old classification pipeline (pipeline.py, scoped_classifier.py, ai_classifier.py, fuzzy_matcher.py)"
```

---

## Task 10: Integration Verification

**Files:** None — verification only.

- [ ] **Step 1: Verify all new tests pass**

Run: `cd backend && python -m pytest tests/test_agent_base.py tests/test_agent_router.py tests/test_agent_specialists.py tests/test_multi_agent_pipeline.py -v`
Expected: All tests PASS.

- [ ] **Step 2: Verify imports are clean**

Run: `cd backend && python -c "from app.services.classification.multi_agent_pipeline import MultiAgentPipeline; from app.workers.classification_tasks import run_classification; print('All imports OK')"`
Expected: "All imports OK"

- [ ] **Step 3: Run eval on BCIPL (requires OPENROUTER_API_KEY)**

Run: `cd "$(git rev-parse --show-toplevel)" && OPENROUTER_API_KEY=$OPENROUTER_API_KEY python scripts/eval_multi_agent.py --company BCIPL`
Expected: Accuracy results printed. Target: 85%+ accuracy, <25% doubt rate.

- [ ] **Step 4: If accuracy is below target, iterate on prompts**

Re-run prompt generation script if golden rules have been updated:
```bash
python scripts/generate_agent_prompts.py
python scripts/eval_multi_agent.py --company BCIPL
```

Check per-agent accuracy to identify which specialist needs prompt improvements.

- [ ] **Step 5: Final commit with any prompt tweaks**

```bash
git add -A
git commit -m "feat: multi-agent classification pipeline — complete implementation"
```

---

## Design Decisions & Notes

### Sign Handling
Specialists return a `sign` field (1 or -1). Currently stored in the classification record's logic but not as a DB column. The `_build_record` method uses `cma_row` and `confidence` for status — sign is passed through in the response but **not applied to amounts in this implementation**. The Excel generator continues to use the raw amount from `extracted_line_items`. Sign-aware Excel generation is a follow-up task.

### No Fallback to Old Pipeline
Per spec: "No fallback to old pipeline." If router/specialist fails, affected items become doubts. Old files are deleted entirely.

### Cost Guards
- `MAX_TOKENS_PER_RUN = 500,000` — tracked via `self._total_tokens`
- `MAX_ITEMS_PER_DOCUMENT = 500` — enforced at fetch time (could add explicit guard)
- Per-call token tracking via OpenRouter `usage` response

### cma_field_name in DB Records
The old pipeline stored human-readable names like "Domestic" in `cma_field_name`. The new pipeline stores the code (e.g., "II_A1") from the specialist's `cma_code` response. The `cma_row` integer is the primary identifier — `cma_field_name` is supplementary. The learned_mappings system uses `cma_field_name` for lookups, so ensure consistency by looking up the name from canonical_labels when building learned_mapping matches.

### Prompt Regeneration
When golden rules are updated (CA corrections promoted), re-run `scripts/generate_agent_prompts.py` to update all specialist prompts. The prompts are checked into git so changes are tracked.
