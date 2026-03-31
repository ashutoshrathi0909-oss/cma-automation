"""
Scoped Classification Engine v2
================================
Tests the hypothesis that reducing LLM context (131 CMA rows → 6-15 scoped rows)
improves classification accuracy beyond the 87% baseline.

Uses Haiku via OpenRouter for classification.
"""

import json
import asyncio
import time
import os
import re
from pathlib import Path
from dataclasses import dataclass, field

# ─── Cost Guard Constants ────────────────────────────────────────────────
MAX_TOKENS_PER_RUN = 500_000
MAX_ITEMS_PER_RUN = 450
HAIKU_INPUT_COST_PER_M = 0.80   # $/M tokens for Haiku via OpenRouter
HAIKU_OUTPUT_COST_PER_M = 4.00  # $/M tokens for Haiku via OpenRouter
BATCH_SIZE = 10  # items per batch before printing cost

# ─── File Paths ──────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
GT_DIR = BASE_DIR / "CMA_Ground_Truth_v1"
SECTION_MAPPING_PATH = GT_DIR / "scripts" / "section_mapping.json"
SHEET_MAPPING_PATH = GT_DIR / "scripts" / "sheet_name_mapping.json"
CANONICAL_LABELS_PATH = GT_DIR / "reference" / "canonical_labels.json"
RULES_PATH = GT_DIR / "reference" / "cma_classification_rules.json"
TRAINING_DATA_PATH = GT_DIR / "database" / "training_data.json"
BCIPL_TEST_PATH = BASE_DIR / "DOCS" / "extractions" / "BCIPL_classification_ground_truth.json"
RESULTS_DIR = BASE_DIR / "DOCS" / "test-results" / "scoped-v2"


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: Section Router
# ═══════════════════════════════════════════════════════════════════════════

# Maps section_normalized → which canonical_labels sections contain relevant CMA rows
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
        "Operating Statement - Manufacturing Expenses",  # Wages (II_C5)
        "Operating Statement - Admin & Selling Expenses",  # Salary (II_D1)
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
        "Operating Statement - Manufacturing Expenses",  # Depreciation row II_C14
        "Operating Statement - Manufacturing Expenses (CMA)",  # II_C20
        "Balance Sheet - Fixed Assets",  # Accumulated depreciation III_A2
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

# Keyword patterns for routing when section_mapping.json doesn't have an exact match
# Order matters — more specific patterns first
KEYWORD_ROUTES = [
    # ── HIGH PRIORITY: Specific patterns that must match before generic ones ──

    # Depreciation SCHEDULE items (BS, not P&L) — must come BEFORE generic depreciation
    (r"(?i)(depreciation.*schedule.*gross|gross block|depreciation.*schedule.*accumulated|accumulated depreciation|opening balance.*depreciation|closing balance.*depreciation|written down value|WDV|block of asset)", "fixed_assets"),
    # Depreciation schedule "for the year" = the depreciation charge amount (P&L-like)
    (r"(?i)(depreciation.*schedule.*for the year|depreciation.*for the year|charge for the year)", "depreciation"),

    # Interest INCOME (P&L credit) — must come before finance_cost
    (r"(?i)(interest income|interest received|interest earned|interest on.*deposit|interest on.*FD|interest on.*fixed deposit)", "other_income"),

    # Borrowings (must come before generic "secured" / "loan" patterns)
    (r"(?i)(term loan|long.?term.*borrow|secured loan|debenture|non.?current.*liabilit|long.?term.*provision|other long.*term|due to director|director.*loan|unsecured.*loan|from related part|inter.?corporate)", "borrowings_long"),
    (r"(?i)(working capital|cash credit|short.?term.*borrow|overdraft|bill discount|demand loan|packing credit|channel financ|LC discount|ECGS|ECLG)", "borrowings_short"),

    # Revenue
    (r"(?i)(sale of product|sale of manufacture|revenue from operation|domestic sale|export sale|net sales|gross sales|turnover|sale of trading)", "revenue"),
    # Other income
    (r"(?i)(other income|non.?operating income|miscellaneous income|rental income|dividend income|bad debt.*written back|liabilities.*written back|profit on sale|gain on.*exchange|scrap sale|exchange.*gain)", "other_income"),
    # Raw materials
    (r"(?i)(raw material|material consumed|cost of material|purchase.*stock|purchase.*goods|purchase.*raw|cost of goods sold|trading account.*debit|changes in inventor)", "raw_materials"),
    # Employee cost
    (r"(?i)(employee|salary|salaries|wages|staff|managerial remuneration|bonus|gratuity|provident fund|esic|esi |staff welfare|contribution to)", "employee_cost"),
    # Manufacturing expense
    (r"(?i)(manufacturing|direct expense|factory|processing charge|job work charge|power.*fuel|coal.*water|stores.*spares|power charge|fuel charge)", "manufacturing_expense"),
    # Selling expense
    (r"(?i)(selling.*expense|selling.*distribution|advertisement|marketing|distribution.*expense|sales promotion|freight outward|commission on sale|brokerage|carriage outward|packing material)", "selling_expense"),
    # Depreciation (P&L charge — generic, after schedule-specific patterns)
    (r"(?i)(depreciation|amortisation|amortization|deprn\b|depn\b)", "depreciation"),
    # Finance cost
    (r"(?i)(interest expense|finance cost|finance charge|interest on.*loan|interest on.*term|interest on.*working|interest on.*bank|interest on.*CC|interest on.*cash credit|bank interest|processing fee|loan processing|bill discount.*charge|interest paid)", "finance_cost"),
    # Admin expense
    (r"(?i)(other expense|admin|audit|legal|professional|office|printing|stationery|telephone|travel|insurance|repair|rent.*rate|miscellaneous exp|general expense|postage|courier|computer|software|annual maintenance|bank charge|payment to auditor|conveyance|vehicle)", "admin_expense"),
    # Tax
    (r"(?i)(income tax|provision for tax|tax expense|deferred tax|current tax|MAT credit|advance tax)", "tax"),
    # Exceptional
    (r"(?i)(exceptional|extraordinary|non.?operating expense|loss on sale|loss on exchange)", "exceptional"),
    # Appropriation
    (r"(?i)(appropriation|dividend.*paid|transfer to.*reserve|brought forward|carried forward)", "appropriation"),
    # Share capital
    (r"(?i)(share capital|equity capital|authorized capital|paid.?up|subscribed)", "share_capital"),
    # Reserves
    (r"(?i)(reserve|surplus|retained earning|profit.*loss.*account|p&l.*balance|capital reserve|general reserve|share premium|securities premium|revaluation reserve|other equity)", "reserves"),
    # Fixed assets
    (r"(?i)(fixed asset|property.*plant|net block|capital work|tangible asset|intangible asset|right.?of.?use|furniture|vehicle|machinery|building|land|computer|equipment|addition.*asset|sale.*asset)", "fixed_assets"),
    # Investments
    (r"(?i)(investment|mutual fund|quoted|unquoted|government securities)", "investments"),
    # Inventories
    (r"(?i)(inventor|finished good|work.?in.?progress|stock.?in.?process|packing material|semi.?finished)", "inventories"),
    # Receivables
    (r"(?i)(receivable|debtor|trade receivable|sundry debtor|bills receivable)", "receivables"),
    # Cash
    (r"(?i)(cash.*bank|bank.*balance|cash.*hand|fixed deposit|FD |cash.*equivalent|current account|savings account)", "cash"),
    # Current liabilities
    (r"(?i)(creditor|trade payable|sundry creditor|provision.*gratuity|provision.*leave|provision.*bonus|current liabilit|statutory.*due|other.*due|outstanding|advance.*customer|security deposit.*received|earnest money|retention money)", "current_liabilities"),
    # Other assets
    (r"(?i)(loan.*advance|advance.*recoverable|prepaid|other current asset|other non.?current|security deposit|income tax.*refund|balance with.*government|cenvat|gst.*input|input.*credit|TDS.*receivable|MAT.*credit.*entitlement)", "other_assets"),
]


def load_section_mapping():
    """Load the curated section_mapping.json"""
    with open(SECTION_MAPPING_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["mapping"]


def load_sheet_mapping():
    """Load the sheet_name_mapping.json"""
    with open(SHEET_MAPPING_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["mapping"]


def route_section(section_text: str, sheet_name: str,
                  section_map: dict, sheet_map: dict) -> str:
    """
    Route a (section_text, sheet_name) pair to a section_normalized category.

    Strategy:
    1. Exact match in section_mapping.json
    2. Case-insensitive match in section_mapping.json
    3. Keyword-based matching on section_text
    4. Fall back to sheet_name hint + keyword matching
    5. Last resort: "other" (will use all rows)
    """
    section_clean = section_text.strip().rstrip(":")

    # 1. Exact match
    if section_clean in section_map:
        return section_map[section_clean]

    # 2. Case-insensitive match
    section_lower = section_clean.lower()
    for key, val in section_map.items():
        if key.lower() == section_lower:
            return val

    # 3. Keyword-based matching on section text
    for pattern, category in KEYWORD_ROUTES:
        if re.search(pattern, section_text):
            return category

    # 4. Use sheet_name as context, try keyword matching on sheet_name + section
    combined = f"{sheet_name} {section_text}"
    for pattern, category in KEYWORD_ROUTES:
        if re.search(pattern, combined):
            return category

    # 5. Sheet-based fallback: if BS sheet, guess other_assets; if P&L, guess admin_expense
    sheet_cat = sheet_map.get(sheet_name, "")
    if not sheet_cat:
        for k, v in sheet_map.items():
            if k.lower() == sheet_name.lower():
                sheet_cat = v
                break

    if sheet_cat in ("notes_bs", "balance_sheet"):
        return "other_assets"
    elif sheet_cat in ("notes_pl", "profit_and_loss"):
        return "admin_expense"

    return "admin_expense"  # safe default (largest section)


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: Scoped Prompt Builder
# ═══════════════════════════════════════════════════════════════════════════

def load_canonical_labels():
    with open(CANONICAL_LABELS_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_rules():
    with open(RULES_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["rules"]


def load_training_data():
    with open(TRAINING_DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    # Exclude BCIPL (the holdout test set)
    return [t for t in data if "Bagadia" not in t.get("company", "")]


@dataclass
class ScopedContext:
    """Pre-computed scoped context for a section_normalized category"""
    section_normalized: str
    cma_rows: list  # relevant canonical labels
    rules: list     # relevant CA rules
    examples: list  # training examples from other companies


def build_scoped_contexts(canonical_labels, rules, training_data):
    """
    Pre-compute scoped context for each section_normalized category.
    Returns dict: section_normalized → ScopedContext
    """
    # Index canonical labels by their section
    labels_by_section = {}
    for label in canonical_labels:
        s = label["section"]
        labels_by_section.setdefault(s, []).append(label)

    # Index training data by section_normalized
    training_by_section = {}
    for t in training_data:
        s = t.get("section_normalized", "other")
        training_by_section.setdefault(s, []).append(t)

    # Build context for each section_normalized
    contexts = {}
    for sec_norm, canonical_sections in SECTION_NORMALIZED_TO_CANONICAL.items():
        # Get relevant CMA rows
        cma_rows = []
        row_codes = set()
        for cs in canonical_sections:
            for label in labels_by_section.get(cs, []):
                if label["code"] not in row_codes:
                    cma_rows.append(label)
                    row_codes.add(label["code"])

        # Get relevant rules (where canonical_code matches our CMA rows)
        relevant_rules = []
        for rule in rules:
            if rule.get("canonical_code") in row_codes:
                relevant_rules.append(rule)

        # Get training examples (limit to 30 per section to keep prompt small)
        examples = training_by_section.get(sec_norm, [])
        # Deduplicate by text
        seen_texts = set()
        unique_examples = []
        for ex in examples:
            if ex["text"].lower() not in seen_texts:
                seen_texts.add(ex["text"].lower())
                unique_examples.append(ex)
        examples = unique_examples[:30]

        contexts[sec_norm] = ScopedContext(
            section_normalized=sec_norm,
            cma_rows=cma_rows,
            rules=relevant_rules,
            examples=examples,
        )

    return contexts


def build_prompt(item: dict, context: ScopedContext) -> str:
    """Build a focused classification prompt for a single item."""

    # CMA rows section
    rows_text = ""
    for row in context.cma_rows:
        rows_text += f"  Row {row['sheet_row']} | {row['code']} | {row['name']}\n"

    # Rules section (limit to 20 most relevant)
    rules_text = ""
    for rule in context.rules[:20]:
        rules_text += f"  - \"{rule['fs_item']}\" → Row {rule['canonical_sheet_row']} ({rule['canonical_name']})"
        if rule.get("remarks"):
            rules_text += f" [{rule['remarks'][:80]}]"
        rules_text += "\n"

    # Examples section (limit to 15)
    examples_text = ""
    for ex in context.examples[:15]:
        examples_text += f"  - \"{ex['text']}\" → Row {ex['label']} ({ex['label_name']})\n"

    prompt = f"""Classify this financial line item into the correct CMA row.

ITEM TO CLASSIFY:
  Text: "{item['raw_text']}"
  Sheet: {item.get('sheet_name', 'Unknown')}
  Section: {item.get('section', 'Unknown')}
  Amount: ₹{item.get('amount_rupees', 0):,.0f}

POSSIBLE CMA ROWS (pick from ONLY these):
{rows_text}
CLASSIFICATION RULES FROM CA EXPERTS:
{rules_text if rules_text else "  (no specific rules for this section)\n"}
EXAMPLES FROM OTHER COMPANIES:
{examples_text if examples_text else "  (no examples available)\n"}
INSTRUCTIONS:
1. Pick the BEST matching CMA row from the list above
2. If the item clearly does not belong to ANY of the listed rows, respond with row 0 (DOUBT)
3. Return ONLY valid JSON, nothing else

Respond with exactly this JSON format:
{{"cma_row": <row_number>, "cma_code": "<code>", "reasoning": "<15 words max>"}}"""

    return prompt


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: OpenRouter API Client with Cost Guards
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class CostTracker:
    """Tracks token usage and cost across the entire run"""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    items_processed: int = 0
    api_errors: int = 0

    def add(self, input_tokens: int, output_tokens: int):
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        input_cost = (input_tokens / 1_000_000) * HAIKU_INPUT_COST_PER_M
        output_cost = (output_tokens / 1_000_000) * HAIKU_OUTPUT_COST_PER_M
        self.total_cost += input_cost + output_cost
        self.items_processed += 1

    def check_budget(self) -> bool:
        """Returns True if we can continue, False if budget exceeded"""
        total_tokens = self.total_input_tokens + self.total_output_tokens
        if total_tokens >= MAX_TOKENS_PER_RUN:
            print(f"\n⛔ TOKEN LIMIT REACHED: {total_tokens:,} >= {MAX_TOKENS_PER_RUN:,}")
            return False
        return True

    def print_status(self):
        total_tokens = self.total_input_tokens + self.total_output_tokens
        print(f"  [{self.items_processed} items] "
              f"Tokens: {total_tokens:,} (in:{self.total_input_tokens:,} out:{self.total_output_tokens:,}) "
              f"Cost: ${self.total_cost:.4f} "
              f"Errors: {self.api_errors}")


async def call_openrouter(prompt: str, api_key: str) -> dict:
    """Call Haiku via OpenRouter. Returns dict with response and token counts."""
    import httpx

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://cma-automation.local",
    }
    payload = {
        "model": "anthropic/claude-haiku-4-5",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 150,
        "temperature": 0.0,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})

    return {
        "content": content,
        "input_tokens": usage.get("prompt_tokens", 0),
        "output_tokens": usage.get("completion_tokens", 0),
    }


def parse_classification_response(content: str) -> dict:
    """Parse the JSON response from the LLM."""
    # Try to extract JSON from the response
    content = content.strip()

    # Remove markdown code blocks if present
    if content.startswith("```"):
        content = re.sub(r"```(?:json)?\s*", "", content)
        content = content.rstrip("`").strip()

    try:
        result = json.loads(content)
        return {
            "cma_row": int(result.get("cma_row", 0)),
            "cma_code": result.get("cma_code", ""),
            "reasoning": result.get("reasoning", ""),
        }
    except (json.JSONDecodeError, ValueError, TypeError):
        # Try to find JSON in the response
        match = re.search(r'\{[^}]+\}', content)
        if match:
            try:
                result = json.loads(match.group())
                return {
                    "cma_row": int(result.get("cma_row", 0)),
                    "cma_code": result.get("cma_code", ""),
                    "reasoning": result.get("reasoning", ""),
                }
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        return {"cma_row": 0, "cma_code": "PARSE_ERROR", "reasoning": content[:100]}


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4: Classification Engine
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ClassificationResult:
    """Result for a single item"""
    raw_text: str
    correct_cma_row: int
    predicted_cma_row: int
    predicted_cma_code: str
    section_normalized: str
    reasoning: str
    is_correct: bool
    is_doubt: bool


async def classify_item(item: dict, context: ScopedContext,
                        api_key: str, cost: CostTracker) -> ClassificationResult:
    """Classify a single item using scoped prompt + Haiku."""
    prompt = build_prompt(item, context)

    try:
        response = await call_openrouter(prompt, api_key)
        cost.add(response["input_tokens"], response["output_tokens"])
        parsed = parse_classification_response(response["content"])
    except Exception as e:
        cost.api_errors += 1
        parsed = {"cma_row": 0, "cma_code": "API_ERROR", "reasoning": str(e)[:100]}

    correct_row = item.get("correct_cma_row", 0)
    predicted_row = parsed["cma_row"]

    return ClassificationResult(
        raw_text=item["raw_text"],
        correct_cma_row=correct_row,
        predicted_cma_row=predicted_row,
        predicted_cma_code=parsed["cma_code"],
        section_normalized=context.section_normalized,
        reasoning=parsed["reasoning"],
        is_correct=(predicted_row == correct_row),
        is_doubt=(predicted_row == 0),
    )


async def run_classification(items: list, contexts: dict,
                             section_map: dict, sheet_map: dict,
                             api_key: str) -> list:
    """Run classification on all items with batching and cost guards."""
    cost = CostTracker()
    results = []

    # Enforce item limit
    if len(items) > MAX_ITEMS_PER_RUN:
        print(f"⚠️  Limiting to {MAX_ITEMS_PER_RUN} items (got {len(items)})")
        items = items[:MAX_ITEMS_PER_RUN]

    print(f"\nClassifying {len(items)} items...")
    print(f"Cost guards: max {MAX_TOKENS_PER_RUN:,} tokens, max {MAX_ITEMS_PER_RUN} items\n")

    for i, item in enumerate(items):
        # Route to section
        sec_norm = route_section(
            item.get("section", ""),
            item.get("sheet_name", ""),
            section_map, sheet_map,
        )

        context = contexts.get(sec_norm)
        if not context:
            # Fallback: use admin_expense (largest section)
            context = contexts.get("admin_expense")

        # Classify
        result = await classify_item(item, context, api_key, cost)
        results.append(result)

        # Print batch status
        if (i + 1) % BATCH_SIZE == 0:
            cost.print_status()

        # Check budget after each item
        if not cost.check_budget():
            print(f"Stopping at item {i+1} due to token budget")
            break

        # Small delay to avoid rate limiting
        if (i + 1) % 5 == 0:
            await asyncio.sleep(0.5)

    # Final status
    print(f"\n{'='*60}")
    print(f"FINAL COST REPORT:")
    cost.print_status()
    print(f"{'='*60}")

    return results


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5: Analysis & Reporting
# ═══════════════════════════════════════════════════════════════════════════

def analyze_results(results: list) -> dict:
    """Compute comprehensive accuracy metrics."""
    total = len(results)
    correct = sum(1 for r in results if r.is_correct)
    doubt = sum(1 for r in results if r.is_doubt)
    classified = total - doubt
    correct_classified = sum(1 for r in results if r.is_correct and not r.is_doubt)

    # Per-section breakdown
    by_section = {}
    for r in results:
        sec = r.section_normalized
        if sec not in by_section:
            by_section[sec] = {"total": 0, "correct": 0, "doubt": 0}
        by_section[sec]["total"] += 1
        if r.is_correct:
            by_section[sec]["correct"] += 1
        if r.is_doubt:
            by_section[sec]["doubt"] += 1

    # Errors (wrong predictions that are NOT doubt)
    errors = [r for r in results if not r.is_correct and not r.is_doubt]

    metrics = {
        "total_items": total,
        "correct": correct,
        "doubt": doubt,
        "classified_non_doubt": classified,
        "correct_within_classified": correct_classified,
        "overall_accuracy": correct / total if total > 0 else 0,
        "doubt_rate": doubt / total if total > 0 else 0,
        "accuracy_within_classified": correct_classified / classified if classified > 0 else 0,
        "error_count": len(errors),
        "per_section": {},
    }

    for sec, data in sorted(by_section.items()):
        classified_sec = data["total"] - data["doubt"]
        metrics["per_section"][sec] = {
            "total": data["total"],
            "correct": data["correct"],
            "doubt": data["doubt"],
            "accuracy": data["correct"] / data["total"] if data["total"] > 0 else 0,
            "accuracy_within_classified": (
                data["correct"] / classified_sec if classified_sec > 0 else 0
            ),
        }

    return metrics


def print_report(metrics: dict, errors: list):
    """Print a human-readable report."""
    print("\n" + "=" * 70)
    print("SCOPED CLASSIFICATION v2 — BCIPL TEST RESULTS")
    print("=" * 70)

    m = metrics
    print(f"\n📊 OVERALL METRICS (baseline: 87%)")
    print(f"  Total items:           {m['total_items']}")
    print(f"  Correct:               {m['correct']}  ({m['overall_accuracy']:.1%})")
    print(f"  Doubt (flagged):       {m['doubt']}  ({m['doubt_rate']:.1%})")
    print(f"  Classified (non-doubt):{m['classified_non_doubt']}")
    print(f"  Correct within classified: {m['correct_within_classified']}  ({m['accuracy_within_classified']:.1%})")
    print(f"  Errors (wrong, not doubt): {m['error_count']}")

    print(f"\n📋 PER-SECTION BREAKDOWN:")
    print(f"  {'Section':<25} {'Total':>5} {'Correct':>7} {'Doubt':>5} {'Accuracy':>8} {'Acc(classified)':>15}")
    print(f"  {'-'*25} {'-'*5} {'-'*7} {'-'*5} {'-'*8} {'-'*15}")
    for sec, data in sorted(m["per_section"].items(), key=lambda x: -x[1]["total"]):
        print(f"  {sec:<25} {data['total']:>5} {data['correct']:>7} {data['doubt']:>5} "
              f"{data['accuracy']:>7.1%} {data['accuracy_within_classified']:>14.1%}")

    if errors:
        print(f"\n❌ TOP ERRORS (showing first 20):")
        for e in errors[:20]:
            print(f"  \"{e.raw_text[:50]}\" → predicted row {e.predicted_cma_row}, "
                  f"correct row {e.correct_cma_row} [{e.section_normalized}]")


def save_results(results: list, metrics: dict):
    """Save detailed results to DOCS/test-results/scoped-v2/"""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Save detailed results JSON
    results_json = []
    for r in results:
        results_json.append({
            "raw_text": r.raw_text,
            "correct_cma_row": r.correct_cma_row,
            "predicted_cma_row": r.predicted_cma_row,
            "predicted_cma_code": r.predicted_cma_code,
            "section_normalized": r.section_normalized,
            "reasoning": r.reasoning,
            "is_correct": r.is_correct,
            "is_doubt": r.is_doubt,
        })

    with open(RESULTS_DIR / "results_detailed.json", "w", encoding="utf-8") as f:
        json.dump(results_json, f, indent=2, ensure_ascii=False)

    with open(RESULTS_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # Save markdown report
    m = metrics
    report = f"""# Scoped Classification v2 — BCIPL Test Results

## Overall Metrics (baseline: 87%)
| Metric | Value |
|--------|-------|
| Total Items | {m['total_items']} |
| Correct | {m['correct']} ({m['overall_accuracy']:.1%}) |
| Doubt (flagged) | {m['doubt']} ({m['doubt_rate']:.1%}) |
| Classified (non-doubt) | {m['classified_non_doubt']} |
| Correct within classified | {m['correct_within_classified']} ({m['accuracy_within_classified']:.1%}) |
| Errors (wrong, not doubt) | {m['error_count']} |

## Per-Section Breakdown
| Section | Total | Correct | Doubt | Accuracy | Acc (classified) |
|---------|-------|---------|-------|----------|-----------------|
"""
    for sec, data in sorted(m["per_section"].items(), key=lambda x: -x[1]["total"]):
        report += (f"| {sec} | {data['total']} | {data['correct']} | {data['doubt']} | "
                   f"{data['accuracy']:.1%} | {data['accuracy_within_classified']:.1%} |\n")

    # Add error examples
    errors = [r for r in results if not r.is_correct and not r.is_doubt]
    if errors:
        report += f"\n## Errors ({len(errors)} total)\n"
        report += "| Item | Predicted | Correct | Section |\n"
        report += "|------|-----------|---------|--------|\n"
        for e in errors[:30]:
            report += f"| {e.raw_text[:40]} | {e.predicted_cma_row} | {e.correct_cma_row} | {e.section_normalized} |\n"

    with open(RESULTS_DIR / "report.md", "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nResults saved to {RESULTS_DIR}")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6: Main
# ═══════════════════════════════════════════════════════════════════════════

async def main():
    print("=" * 70)
    print("SCOPED CLASSIFICATION ENGINE v2")
    print("Testing: Scoped Haiku vs baseline (87%)")
    print("=" * 70)

    # Load API key
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        # Try loading from .env file
        env_path = BASE_DIR / ".env"
        if env_path.exists():
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("OPENROUTER_API_KEY="):
                        api_key = line.split("=", 1)[1].strip()
                        break

    if not api_key:
        print("ERROR: No OPENROUTER_API_KEY found in environment or .env file")
        return

    print(f"API key loaded: {api_key[:10]}...{api_key[-4:]}")

    # Step 1: Load all data
    print("\n1. Loading ground truth data...")
    section_map = load_section_mapping()
    sheet_map = load_sheet_mapping()
    canonical_labels = load_canonical_labels()
    rules = load_rules()
    training_data = load_training_data()

    print(f"   Canonical labels: {len(canonical_labels)}")
    print(f"   CA rules: {len(rules)}")
    print(f"   Training examples (non-BCIPL): {len(training_data)}")

    # Step 2: Build scoped contexts
    print("\n2. Building scoped contexts...")
    contexts = build_scoped_contexts(canonical_labels, rules, training_data)
    for sec, ctx in sorted(contexts.items()):
        print(f"   {sec}: {len(ctx.cma_rows)} rows, {len(ctx.rules)} rules, {len(ctx.examples)} examples")

    # Step 3: Load test data
    print("\n3. Loading BCIPL test data...")
    with open(BCIPL_TEST_PATH, encoding="utf-8") as f:
        test_items = json.load(f)
    print(f"   Test items: {len(test_items)}")

    # Step 4: Test section routing (dry run)
    print("\n4. Section routing dry run...")
    route_counts = {}
    unrouted = []
    for item in test_items:
        sec = route_section(item.get("section", ""), item.get("sheet_name", ""),
                           section_map, sheet_map)
        route_counts[sec] = route_counts.get(sec, 0) + 1

    for sec, count in sorted(route_counts.items(), key=lambda x: -x[1]):
        print(f"   {sec}: {count} items")

    # Step 5: Run classification
    print("\n5. Running classification...")
    results = await run_classification(test_items, contexts, section_map, sheet_map, api_key)

    # Step 6: Analyze and report
    print("\n6. Analyzing results...")
    metrics = analyze_results(results)
    errors = [r for r in results if not r.is_correct and not r.is_doubt]
    print_report(metrics, errors)

    # Step 7: Save results
    save_results(results, metrics)


if __name__ == "__main__":
    asyncio.run(main())
