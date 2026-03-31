"""Tier 2 classification: Scoped AI classifier with single DeepSeek V3 call.

Uses DeepSeek V3 via OpenRouter (openai package).
Dual-path routing: item text keywords + section header keywords to find the
right CMA section(s). When paths disagree, both sections' contexts are merged
so the model sees all plausible CMA rows.

Ground truth data is pre-loaded once at init from:
  /app/CMA_Ground_Truth_v1/ (Docker mount) or GT_BASE_DIR env override.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

from app.config import get_settings
from app.models.ai_schemas import ClassificationCandidate
from app.services.classification.ai_classifier import AIClassificationResult

logger = logging.getLogger(__name__)

# ─── OpenRouter model ─────────────────────────────────────────────────────────
# DeepSeek V3 (fast, no reasoning chain) — single model, no debate.
DEEPSEEK_MODEL = "deepseek/deepseek-chat"

# ─── Cost guards ─────────────────────────────────────────────────────────────
MAX_TOKENS_PER_RUN = 500_000
MAX_ITEMS_PER_DOCUMENT = 300

# ─── Confidence threshold (items below this become doubt) ────────────────────
DOUBT_THRESHOLD = 0.8

# ─── Ground truth file paths ─────────────────────────────────────────────────
# Docker mounts CMA_Ground_Truth_v1/ at /app/CMA_Ground_Truth_v1/
# Allow override via env var for local development.
_GT_BASE = Path(os.getenv("GT_BASE_DIR", Path(__file__).parents[3] / "CMA_Ground_Truth_v1"))

SECTION_MAPPING_PATH = _GT_BASE / "scripts" / "section_mapping.json"
SHEET_MAPPING_PATH = _GT_BASE / "scripts" / "sheet_name_mapping.json"
CANONICAL_LABELS_PATH = _GT_BASE / "reference" / "canonical_labels.json"
RULES_PATH = _GT_BASE / "reference" / "cma_classification_rules.json"
TRAINING_DATA_PATH = _GT_BASE / "database" / "training_data.json"

# ─── Thread pool for parallel API calls ──────────────────────────────────────
_executor = ThreadPoolExecutor(max_workers=4)

# ─── Formula rows — NEVER classify into these ────────────────────────────────
# Rows in CMA.xlsm that are formula cells — auto-calculated, not user-filled.
FORMULA_ROWS = {200, 201}  # BS Inventories: =CXX formulas

# ─── Section normalized → canonical label sections ───────────────────────────
# Each key is a section_normalized category; values are canonical label section
# names that contain the relevant CMA rows.
SECTION_NORMALIZED_TO_CANONICAL = {
    "revenue": [
        "Operating Statement - Income - Sales",
    ],
    "other_income": [
        "Operating Statement - Non Operating Income",
    ],
    "raw_materials": [
        "Operating Statement - Manufacturing Expenses",
    ],
    "employee_cost": [
        "Operating Statement - Manufacturing Expenses",
        "Operating Statement - Admin & Selling Expenses",
    ],
    "manufacturing_expense": [
        "Operating Statement - Manufacturing Expenses",
        "Operating Statement - Manufacturing Expenses (CMA)",
    ],
    "admin_expense": [
        "Operating Statement - Admin & Selling Expenses",
        "Operating Statement - Misc Amortisation",
    ],
    "selling_expense": [
        "Operating Statement - Admin & Selling Expenses",
    ],
    "depreciation": [
        "Operating Statement - Manufacturing Expenses",
        "Operating Statement - Manufacturing Expenses (CMA)",
        "Balance Sheet - Fixed Assets",
    ],
    "finance_cost": [
        "Operating Statement - Finance Charges",
    ],
    "tax": [
        "Operating Statement - Tax",
        "Balance Sheet - Deferred Tax",
    ],
    "exceptional": [
        "Operating Statement - Non Operating Expenses",
    ],
    "appropriation": [
        "Operating Statement - Profit Appropriation",
    ],
    "share_capital": [
        "Balance Sheet - Share Capital",
    ],
    "reserves": [
        "Balance Sheet - Reserves and Surplus",
    ],
    "borrowings_long": [
        "Balance Sheet - Term Loans",
        "Balance Sheet - Debentures",
        "Balance Sheet - Preference Shares",
        "Balance Sheet - Other Debts",
        "Balance Sheet - Unsecured Loans",
        "Balance Sheet - Deferred Tax",
    ],
    "borrowings_short": [
        "Balance Sheet - Working Capital Bank Finance",
    ],
    "fixed_assets": [
        "Balance Sheet - Fixed Assets",
        "Balance Sheet - Fixed Asset Movement",
        "Balance Sheet - Intangibles",
    ],
    "investments": [
        "Balance Sheet - Investments",
        "Balance Sheet - Non Current Assets - Group Exposure",
    ],
    "inventories": [
        "Balance Sheet - Inventories",
        "Balance Sheet - Inventories - Raw Material",
        "Balance Sheet - Inventories - Stores & Spares",
    ],
    "receivables": [
        "Balance Sheet - Sundry Debtors",
    ],
    "cash": [
        "Balance Sheet - Cash and Bank Balances",
    ],
    "current_liabilities": [
        "Balance Sheet - Current Liabilities",
        "Balance Sheet - Contingent Liabilities",
    ],
    "other_assets": [
        "Balance Sheet - Loans and Advances",
        "Balance Sheet - Non Current Assets",
        "Balance Sheet - Non Current Assets - Group Exposure",
    ],
}

# ─── section_normalized → broad_classification ───────────────────────────────
_SECTION_TO_BROAD: dict[str, str] = {
    "revenue": "revenue",
    "other_income": "revenue",
    "raw_materials": "manufacturing_expense",
    "employee_cost": "manufacturing_expense",
    "manufacturing_expense": "manufacturing_expense",
    "admin_expense": "admin_expense",
    "selling_expense": "admin_expense",
    "depreciation": "manufacturing_expense",
    "finance_cost": "admin_expense",
    "tax": "admin_expense",
    "exceptional": "admin_expense",
    "appropriation": "equity",
    "share_capital": "equity",
    "reserves": "equity",
    "borrowings_long": "liability",
    "borrowings_short": "liability",
    "fixed_assets": "asset",
    "investments": "asset",
    "inventories": "asset",
    "receivables": "asset",
    "cash": "asset",
    "current_liabilities": "liability",
    "other_assets": "asset",
}

# ─── Keyword routing patterns (order matters — specific first) ────────────────
_KEYWORD_ROUTES: list[tuple[str, str]] = [
    (r"(?i)(depreciation.*schedule.*gross|gross block|accumulated depreciation|written down value|WDV|block of asset)", "fixed_assets"),
    (r"(?i)(depreciation.*for the year|charge for the year)", "depreciation"),
    (r"(?i)(interest income|interest received|interest earned|interest on.*deposit|interest on.*FD)", "other_income"),
    (r"(?i)(term loan|long.?term.*borrow|secured loan|debenture|non.?current.*liabilit|unsecured.*loan|from related part|inter.?corporate|due to director|director.*loan)", "borrowings_long"),
    (r"(?i)(working capital|cash credit|short.?term.*borrow|overdraft|bill discount|demand loan|packing credit)", "borrowings_short"),
    # Bug 1: "Domestic" keywords — domestic sales/turnover/revenue → revenue
    (r"(?i)(sale of product|sale of manufacture|revenue from operation|domestic sale|domestic turnover|domestic revenue|export sale|net sales|gross sales|turnover)", "revenue"),
    (r"(?i)(other income|non.?operating income|miscellaneous income|rental income|dividend income|bad debt.*written back|profit on sale|gain on.*exchange|scrap sale)", "other_income"),
    (r"(?i)(raw material|material consumed|cost of material|purchase.*stock|purchase.*goods|cost of goods sold|changes in inventor)", "raw_materials"),
    # Bug 9: Auditor remuneration — must be BEFORE generic employee/admin patterns
    (r"(?i)(auditor.?s?\s*remuneration|audit\s*fee|statutory\s*audit|tax\s*audit\s*fee|auditor\s*fee)", "admin_expense"),
    # Bug 8: Bad Debts / Sundry Write-offs — specific routing before generic admin
    (r"(?i)(bad\s*debt.*w(ritten)?\s*/?\s*off|bad\s*debt.*w/off)", "admin_expense"),
    (r"(?i)(sundry\s*balance.*w(ritten)?\s*/?\s*off|sundry\s*balances?\s*written\s*off)", "exceptional"),
    (r"(?i)(employee|salary|salaries|wages|staff|managerial remuneration|bonus|gratuity|provident fund|esic|esi |contribution to)", "employee_cost"),
    (r"(?i)(manufacturing|direct expense|factory|processing charge|job work charge|power.*fuel|stores.*spares)", "manufacturing_expense"),
    # Bug 7: Repairs to Plant/Machinery → manufacturing (before generic repair → admin)
    (r"(?i)(repairs?\s*to\s*plant|repairs?\s*to\s*machiner|plant\s*repair|machinery\s*repair)", "manufacturing_expense"),
    # Bug 3: Selling & Distribution — explicit keywords
    (r"(?i)(selling.*expense|advertisement|marketing|distribution.*expense|freight outward|commission on sale|carriage outward|carriage\s*outward|freight\s*outward|commission\s*on\s*sales?|brokerage|discount\s*allowed)", "selling_expense"),
    # Bug 6: Rates & Taxes → admin_expense (row 68 section) — before generic admin
    (r"(?i)(rates?\s*(and|&)\s*taxes?|rate\s*&\s*tax)", "admin_expense"),
    (r"(?i)(depreciation|amortisation|amortization|deprn\b|depn\b)", "depreciation"),
    # Bug 2: Finance cost keywords — "other charges (finance)" + bank charges → finance_cost
    (r"(?i)(interest expense|finance cost|finance charge|interest on.*loan|interest on.*working|interest paid|bank interest|bank charge|other\s*charges?\s*\(finance\))", "finance_cost"),
    (r"(?i)(other expense|admin|audit|legal|professional|office|printing|telephone|travel|insurance|repair|miscellaneous exp|general expense|vehicle|conveyance)", "admin_expense"),
    # Water/fuel/power route for manufacturing
    (r"(?i)(water\s*charges?|coal|fuel|lpg|gas\s*charges?)", "manufacturing_expense"),
    # Security charges route
    (r"(?i)(security\s*(service\s*)?charges?|watchman|guard)", "manufacturing_expense"),
    (r"(?i)(income tax|provision for tax|tax expense|deferred tax|current tax|MAT credit)", "tax"),
    (r"(?i)(exceptional|extraordinary|non.?operating expense|loss on sale)", "exceptional"),
    (r"(?i)(appropriation|dividend.*paid|transfer to.*reserve|brought forward|carried forward)", "appropriation"),
    (r"(?i)(share capital|equity capital|authorized capital|paid.?up|subscribed)", "share_capital"),
    (r"(?i)(reserve|surplus|retained earning|profit.*loss.*account|p&l.*balance|capital reserve|general reserve|securities premium|revaluation reserve|other equity)", "reserves"),
    (r"(?i)(fixed asset|property.*plant|net block|capital work|tangible asset|intangible asset|furniture|vehicle|machinery|building|land|equipment)", "fixed_assets"),
    (r"(?i)(investment|mutual fund|quoted|unquoted|government securities)", "investments"),
    (r"(?i)(inventor|finished good|work.?in.?progress|stock.?in.?process|semi.?finished)", "inventories"),
    (r"(?i)(receivable|debtor|trade receivable|sundry debtor|bills receivable)", "receivables"),
    (r"(?i)(cash.*bank|bank.*balance|cash.*hand|fixed deposit|FD |cash.*equivalent)", "cash"),
    (r"(?i)(creditor|trade payable|sundry creditor|current liabilit|statutory.*due|outstanding|advance.*customer|retention money)", "current_liabilities"),
    (r"(?i)(loan.*advance|advance.*recoverable|prepaid|other current asset|other non.?current|security deposit|TDS.*receivable|MAT.*credit)", "other_assets"),
]


@dataclass
class _ScopedContext:
    """Pre-computed context for one section_normalized category."""
    section_normalized: str
    cma_rows: list[dict]   # relevant canonical label dicts
    rules: list[dict]      # relevant CA rule dicts
    examples: list[dict]   # training examples from other companies


class ScopedClassifier:
    """Classifies financial line items using a scoped single-model approach.

    Pre-loads all ground truth data once at init to avoid repeated file I/O.
    Each classify() call:
      1. Dual-path routes the item (text keywords + header) to 1-2 sections
      2. Builds a focused prompt with that section's CMA rows (merged if 2)
      3. Calls DeepSeek V3 once via OpenRouter
      4. Maps back to AIClassificationResult (same format as AIClassifier)
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._openrouter = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
        )
        self._total_tokens = 0
        self._items_classified = 0

        logger.info("ScopedClassifier: loading ground truth from %s", _GT_BASE)
        self._section_map = self._load_section_mapping()
        self._sheet_map = self._load_sheet_mapping()
        canonical_labels = self._load_canonical_labels()
        rules = self._load_rules()
        training_data = self._load_training_data()

        # Build an index: cma_row → label dict (for mapping back to field names)
        self._labels_by_row: dict[int, dict] = {
            lbl["sheet_row"]: lbl for lbl in canonical_labels
        }

        # Pre-compute scoped contexts for all 23 sections
        self._contexts = self._build_scoped_contexts(canonical_labels, rules, training_data)
        logger.info(
            "ScopedClassifier ready: %d sections, %d canonical labels, %d rules, %d training examples",
            len(self._contexts),
            len(canonical_labels),
            len(rules),
            len(training_data),
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def classify_sync(
        self,
        raw_text: str,
        amount: float | None,
        section: str | None,
        industry_type: str,
        document_type: str,
        fuzzy_candidates: list,
    ) -> AIClassificationResult:
        """Synchronous wrapper for classify(). Used by pipeline.py.

        Always creates a fresh event loop — safe to call from any thread
        (ARQ worker threads, sync endpoints, etc.).
        """
        try:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(
                    self.classify(raw_text, amount, section, industry_type, document_type, fuzzy_candidates)
                )
            finally:
                loop.close()
        except Exception as e:
            logger.error("classify_sync failed: %s", e)
            return self._make_doubt(f"Classification error: {e}")

    async def classify(
        self,
        raw_text: str,
        amount: float | None,
        section: str | None,
        industry_type: str,
        document_type: str,
        fuzzy_candidates: list,  # FuzzyMatchResult list (unused, kept for signature compat)
    ) -> AIClassificationResult:
        """Classify a line item using a single DeepSeek V3 call.

        Returns AIClassificationResult compatible with pipeline.py.
        Never raises — all failures return a doubt result.
        """
        sections = self._route_section(raw_text, section or "", document_type, industry_type)

        # Build context (merge if dual-path returned multiple sections)
        if len(sections) == 1:
            context = self._contexts.get(sections[0]) or self._contexts["admin_expense"]
        else:
            context = self._merge_contexts(sections)

        prompt = self._build_prompt(raw_text, amount, section or "not specified", context)

        # ── Single model call ─────────────────────────────────────────────────
        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(_executor, self._call_model, DEEPSEEK_MODEL, prompt)
        except Exception as e:
            logger.error("DeepSeek V3 call failed: %s", e)
            return self._make_doubt(f"AI classification failed: {e}")

        # Build result
        cma_row = int(result.get("cma_row", 0))
        confidence = float(result.get("confidence", 0.0))

        if cma_row == 0 or confidence < DOUBT_THRESHOLD:
            return self._make_doubt(result.get("reasoning", "Low confidence"))

        label = self._labels_by_row.get(cma_row)
        cma_field_name = label["name"] if label else result.get("cma_code", "UNCLASSIFIED")
        broad = _SECTION_TO_BROAD.get(sections[0], "admin_expense")

        return AIClassificationResult(
            cma_field_name=cma_field_name,
            cma_row=cma_row,
            cma_sheet="input_sheet",
            broad_classification=broad,
            confidence=confidence,
            is_doubt=False,
            doubt_reason=None,
            alternatives=[],
            classification_method="scoped_v3",
        )

    # ── Model Call ────────────────────────────────────────────────────────────

    def _call_model(self, model_id: str, prompt: str) -> dict:
        """Call a single model via OpenRouter. Returns parsed dict with cma_row, reasoning, etc.

        Runs in a thread pool (blocking). Raises on failure — caller handles exceptions.
        """
        response = self._openrouter.chat.completions.create(
            model=model_id,
            messages=[
                {
                    "role": "system",
                    "content": "You are a CMA classification expert. Respond with ONLY valid JSON.",
                },
                {
                    "role": "user",
                    "content": (
                        prompt
                        + '\n\nRespond with ONLY this JSON format:\n'
                        '{"cma_row": <integer>, "cma_code": "<code>", '
                        '"confidence": <0.0-1.0>, "reasoning": "<brief>"}'
                    ),
                },
            ],
            max_tokens=300,
            temperature=0.0,
        )

        # Cost tracking (always runs, even if JSON parsing fails below)
        usage = response.usage
        if usage:
            self._total_tokens += (usage.prompt_tokens or 0) + (usage.completion_tokens or 0)
            if self._total_tokens > MAX_TOKENS_PER_RUN:
                raise RuntimeError(
                    f"Token budget exceeded: {self._total_tokens} > {MAX_TOKENS_PER_RUN}"
                )
        self._items_classified += 1
        if self._items_classified % 10 == 0:
            logger.info(
                "Cost guard: %d items, ~%d tokens used",
                self._items_classified, self._total_tokens,
            )

        text = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        if "```" in text:
            text = text.split("```")[1].strip()
            if text.startswith("json"):
                text = text[4:].strip()

        return json.loads(text)

    # ── Context Merger ─────────────────────────────────────────────────────────

    def _merge_contexts(self, sections: list[str]) -> _ScopedContext:
        """Merge contexts from multiple sections into one expanded context."""
        all_rows: list[dict] = []
        all_rules: list[dict] = []
        all_examples: list[dict] = []
        seen_codes: set[str] = set()
        seen_texts: set[str] = set()

        for sec in sections:
            ctx = self._contexts.get(sec)
            if not ctx:
                continue
            for r in ctx.cma_rows:
                if r["code"] not in seen_codes:
                    all_rows.append(r)
                    seen_codes.add(r["code"])
            all_rules.extend(ctx.rules)
            for ex in ctx.examples:
                t = ex.get("text", "").lower()
                if t not in seen_texts:
                    all_examples.append(ex)
                    seen_texts.add(t)

        return _ScopedContext(
            section_normalized=sections[0],  # primary section
            cma_rows=all_rows,
            rules=all_rules[:30],
            examples=all_examples[:20],
        )

    # ── Result Builder ────────────────────────────────────────────────────────

    def _make_doubt(self, reason: str) -> AIClassificationResult:
        return AIClassificationResult(
            cma_field_name=None,
            cma_row=None,
            cma_sheet="input_sheet",
            broad_classification="",
            confidence=0.0,
            is_doubt=True,
            doubt_reason=reason,
            alternatives=[],
            classification_method="scoped_doubt",
        )

    # ── Section Router ────────────────────────────────────────────────────────

    @staticmethod
    def _is_pl_context(document_type: str) -> bool:
        """Return True if the document_type indicates a P&L / profit & loss source."""
        dt = (document_type or "").lower()
        return "profit" in dt or dt == "pl" or "p&l" in dt or "income" in dt

    @staticmethod
    def _is_bs_context(document_type: str) -> bool:
        """Return True if the document_type indicates a Balance Sheet source."""
        dt = (document_type or "").lower()
        return "balance" in dt or dt == "bs"

    def _route_section(
        self,
        raw_text: str,
        section_text: str,
        document_type: str,
        industry_type: str | None = None,
    ) -> list[str]:
        """Route to one or more section_normalized categories using dual-path routing.

        Path 1: Match item text against keyword patterns (strongest signal)
        Path 2: Match section header against section_mapping.json + keywords

        If both agree -> return [single_section] (narrow scope)
        If they disagree -> return [text_route, header_route] (expanded scope)
        If text route finds nothing -> return [header_route] only

        Context-aware overrides (Bugs 2, 4, 5, 10) apply AFTER keyword routing
        to fix specific mis-routes based on source_sheet / section_header / industry.
        """
        raw_lower = raw_text.lower()
        section_lower = (section_text or "").lower()
        is_pl = self._is_pl_context(document_type)
        is_bs = self._is_bs_context(document_type)

        # ── Path 1: Route by item text keywords ──────────────────────────────
        text_route: str | None = None
        for pattern, category in _KEYWORD_ROUTES:
            if re.search(pattern, raw_text):
                text_route = category
                break

        # ── Bug 2: "Other Charges" / "Bank Charges" in finance cost context ──
        # When the section header says "finance cost/charge", force finance_cost
        _finance_header = bool(re.search(
            r"(?i)(finance\s*cost|finance\s*charge|borrowing\s*cost)", section_lower
        ))
        if _finance_header and text_route in (None, "admin_expense"):
            # Items like "Other Charges", "Bank Charges" under finance header
            if re.search(r"(?i)(other\s*charges?|bank\s*charges?)", raw_lower):
                text_route = "finance_cost"

        # ── Bug 4: Deferred Tax — P&L context → tax section (rows 99-101) ────
        # Deferred Tax in P&L should go to "tax", not "borrowings_long" (BS rows)
        if re.search(r"(?i)deferred\s*tax", raw_lower):
            if is_pl:
                text_route = "tax"
            elif is_bs:
                text_route = "borrowings_long"  # BS Deferred Tax → rows 159/171

        # ── Bug 5: BS Inventories — inventory items in BS → bs inventories ────
        # Stock-in-Trade, Finished Goods, WIP on BS should NOT go to P&L rows
        if is_bs and re.search(
            r"(?i)(stock.?in.?trade|finished\s*goods?|work\s*in\s*progress|\bwip\b|semi.?finished|raw\s*material|stores.*spares)",
            raw_lower,
        ):
            text_route = "inventories"

        # ── Bug 10: Staff Welfare / PF in manufacturing → wages section ───────
        # For manufacturing companies, EPF/ESI/Gratuity/Staff Welfare → employee_cost
        # (which maps to Manufacturing Expenses row 45, Wages section)
        # For non-manufacturing, these stay in employee_cost but will route to row 67
        if (industry_type or "").lower() == "manufacturing":
            if re.search(
                r"(?i)(staff\s*welfare|epf|esi\b|esic|gratuity|pf\s*contribution|\bpf\b|provident\s*fund)",
                raw_lower,
            ):
                text_route = "employee_cost"
                # Force manufacturing context only (not admin) by returning single section
                return ["employee_cost"]

        # ── Path 2: Route by section header ───────────────────────────────────
        header_route = self._route_header(section_text, document_type)

        # ── Combine paths ─────────────────────────────────────────────────────
        if text_route is None:
            return [header_route]
        if text_route == header_route:
            return [header_route]
        # Disagree: return both so context is merged
        return [text_route, header_route]

    def _route_header(self, section_text: str, document_type: str) -> str:
        """Route section header text to a section_normalized category (original logic)."""
        section_clean = section_text.strip().rstrip(":")

        # 1. Exact match in section_mapping.json
        if section_clean in self._section_map:
            return self._section_map[section_clean]

        # 2. Case-insensitive match
        section_lower = section_clean.lower()
        for key, val in self._section_map.items():
            if key.lower() == section_lower:
                return val

        # 3. Keyword patterns on section text
        for pattern, category in _KEYWORD_ROUTES:
            if re.search(pattern, section_text):
                return category

        # 4. Combine document_type as context and try again
        combined = f"{document_type} {section_text}"
        for pattern, category in _KEYWORD_ROUTES:
            if re.search(pattern, combined):
                return category

        # 5. Document-type fallback
        if document_type in ("balance_sheet", "notes_bs"):
            return "other_assets"

        return "admin_expense"  # safe default (largest section)

    # ── Prompt Builder ────────────────────────────────────────────────────────

    @staticmethod
    def _disambiguate_row_name(row: dict, name_counts: dict[str, int]) -> str:
        """Add a parenthetical descriptor when a row name appears more than once."""
        name = row["name"]
        if name_counts.get(name, 1) <= 1:
            return name

        # Derive a short descriptor from the section
        section = row.get("section", "")
        if "Manufacturing" in section:
            return f"{name} (Manufacturing)"
        if "Admin" in section or "Selling" in section:
            return f"{name} (Admin)"
        if "CMA" in section:
            return f"{name} (CMA Adjustment)"
        if "Fixed Asset" in section:
            return f"{name} (Fixed Assets)"
        if "Non Operating" in section:
            return f"{name} (Non Operating)"
        # Fallback: use the code
        return f"{name} ({row['code']})"

    def _build_prompt(
        self,
        raw_text: str,
        amount: float | None,
        section: str,
        context: _ScopedContext,
    ) -> str:
        # Filter out formula rows — these are auto-calculated, not classified
        filtered_rows = [r for r in context.cma_rows if r.get("sheet_row") not in FORMULA_ROWS]

        # Count name occurrences for disambiguation
        name_counts = Counter(r["name"] for r in filtered_rows)

        rows_text = "".join(
            f"  Row {r['sheet_row']} | {r['code']} | {self._disambiguate_row_name(r, name_counts)}\n"
            for r in filtered_rows
        )
        rules_text = "".join(
            f"  - \"{rule['fs_item']}\" -> Row {rule['canonical_sheet_row']} ({rule['canonical_name']})"
            + (f" [{rule['remarks'][:80]}]" if rule.get("remarks") else "")
            + "\n"
            for rule in context.rules[:20]
        ) or "  (no specific rules for this section)\n"

        examples_text = "".join(
            f"  - \"{ex['text']}\" -> Row {ex['label']} ({ex['label_name']})\n"
            for ex in context.examples[:15]
        ) or "  (no examples available)\n"

        amount_str = f"Rs.{amount:,.0f}" if amount is not None else "not provided"

        return f"""Classify this financial line item into the correct CMA row.

ITEM TO CLASSIFY:
  Text: "{raw_text}"
  Section: {section}
  Amount: {amount_str}

POSSIBLE CMA ROWS (pick from ONLY these):
{rows_text}
IMPORTANT RULES:
- "Others" rows are LAST RESORT. Only pick an "Others" row if NO specific row matches.
- Before picking "Others", verify you considered every specific row above.
- If the item text contains keywords matching a specific row (e.g., "repairs" -> Repairs row, "salary" -> Wages row), pick that specific row, NOT "Others".
- When unsure between a specific row and "Others", prefer the specific row with lower confidence.
- You MUST pick from the POSSIBLE CMA ROWS listed above. Do not invent row numbers.

CA-VERIFIED DISAMBIGUATION RULES:
- "Miscellaneous Expenses" → Row 71 (Others Admin). Row 75 is ONLY for non-cash write-offs.
- "Directors Remuneration" → Row 73 (Audit Fees), NOT Row 67 (Salary).
- "Liquidated Damages" → Row 71 (Others Admin), NOT Row 83 (Interest on TL).
- "Loan Processing Fee" → Row 85 (Bank Charges), NOT Row 84 (WC Interest).
- "Bank Charges" → Row 85, NOT admin expense.
- Employee items (gratuity, EPF, ESI) → Row 45 (Wages) always.
- "Staff Welfare" / "Bonus" / "Employee Benefits" → Row 45 for manufacturing, Row 67 for trading.
- "Insurance Premium" → Row 71 (Others Admin), NOT Row 49 (Others Manufacturing).
- "Licence & Subscription" → Row 71 (Others Admin), NOT Row 68 (Rent Rates Taxes).
- P&L stock (Changes in Inventories) → P&L rows (53-59). BS stock → do NOT classify (formula rows).
- "Leave Encashment" in P&L → Row 45. In BS → Row 249.
- "Subsidy/Govt Grant" in P&L → Row 33. In BS → Row 125.
- Classify by NATURE of item, not section header in source P&L.

CA EXPERT RULES:
{rules_text}
EXAMPLES FROM OTHER COMPANIES:
{examples_text}
NOTE: Examples are from other companies and are CA-verified. Some examples may reference rows not in the list above (from other sections). Focus on the PATTERN, not the specific row number. Always pick from the POSSIBLE CMA ROWS listed above.

INSTRUCTIONS:
1. Pick the BEST matching CMA row from the list above
2. If the item does NOT belong to any of these rows, set cma_row to 0
3. Set confidence to reflect how certain you are (0.8+ = confident, below = unsure)
4. Keep reasoning under 15 words"""

    # ── Data Loaders ──────────────────────────────────────────────────────────

    @staticmethod
    def _load_section_mapping() -> dict:
        with open(SECTION_MAPPING_PATH, encoding="utf-8") as f:
            return json.load(f)["mapping"]

    @staticmethod
    def _load_sheet_mapping() -> dict:
        with open(SHEET_MAPPING_PATH, encoding="utf-8") as f:
            return json.load(f)["mapping"]

    @staticmethod
    def _load_canonical_labels() -> list[dict]:
        with open(CANONICAL_LABELS_PATH, encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _load_rules() -> list[dict]:
        with open(RULES_PATH, encoding="utf-8") as f:
            return json.load(f)["rules"]

    @staticmethod
    def _load_training_data() -> list[dict]:
        with open(TRAINING_DATA_PATH, encoding="utf-8") as f:
            data = json.load(f)
        # Exclude BCIPL (holdout test set)
        return [t for t in data if "Bagadia" not in t.get("company", "")]

    # ── Context Builder ───────────────────────────────────────────────────────

    @staticmethod
    def _build_scoped_contexts(
        canonical_labels: list[dict],
        rules: list[dict],
        training_data: list[dict],
    ) -> dict[str, _ScopedContext]:
        # Index canonical labels by their section
        labels_by_section: dict[str, list] = {}
        for lbl in canonical_labels:
            labels_by_section.setdefault(lbl["section"], []).append(lbl)

        # Index training data by section_normalized
        training_by_section: dict[str, list] = {}
        for t in training_data:
            s = t.get("section_normalized", "other")
            training_by_section.setdefault(s, []).append(t)

        contexts: dict[str, _ScopedContext] = {}
        for sec_norm, canonical_sections in SECTION_NORMALIZED_TO_CANONICAL.items():
            # Collect CMA rows (deduplicated)
            cma_rows: list[dict] = []
            row_codes: set[str] = set()
            for cs in canonical_sections:
                for lbl in labels_by_section.get(cs, []):
                    if lbl["code"] not in row_codes:
                        cma_rows.append(lbl)
                        row_codes.add(lbl["code"])

            # Collect relevant rules
            relevant_rules = [r for r in rules if r.get("canonical_code") in row_codes]

            # Collect training examples (deduplicated by text, max 30)
            seen_texts: set[str] = set()
            unique_examples: list[dict] = []
            for ex in training_by_section.get(sec_norm, []):
                txt = ex.get("text", "").lower()
                if txt not in seen_texts:
                    seen_texts.add(txt)
                    unique_examples.append(ex)
                    if len(unique_examples) >= 30:
                        break

            contexts[sec_norm] = _ScopedContext(
                section_normalized=sec_norm,
                cma_rows=cma_rows,
                rules=relevant_rules,
                examples=unique_examples,
            )

        return contexts
