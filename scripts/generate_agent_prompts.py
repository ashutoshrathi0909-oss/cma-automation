"""
scripts/generate_agent_prompts.py
----------------------------------
Auto-generates classification prompts for the 5-agent CMA pipeline from ground-truth files.
Output directory: backend/app/services/classification/agents/prompts/

Fully deterministic — same inputs always produce same outputs (all iterables are sorted).
"""

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
GT_BASE = PROJECT_ROOT / "CMA_Ground_Truth_v1"
OUTPUT_DIR = (
    PROJECT_ROOT
    / "backend"
    / "app"
    / "services"
    / "classification"
    / "agents"
    / "prompts"
)

# ---------------------------------------------------------------------------
# Agent config
# ---------------------------------------------------------------------------
AGENTS = {
    "router":       {"row_range": None},
    "pl_income":    {"row_range": (22,  34)},
    "pl_expense":   {"row_range": (41, 108)},
    "bs_liability": {"row_range": (110, 160)},
    "bs_asset":     {"row_range": (161, 258)},
}

FORMULA_ROWS = {200, 201}

PRIORITY_ORDER = {"ca_override": 0, "ca_interview": 1, "legacy": 2}


# ---------------------------------------------------------------------------
# Filter helpers
# ---------------------------------------------------------------------------

def filter_labels(labels: list, row_min: int, row_max: int) -> list:
    """Return labels in [row_min, row_max], excluding formula rows, sorted by sheet_row."""
    return sorted(
        [
            lbl for lbl in labels
            if row_min <= lbl["sheet_row"] <= row_max
            and lbl["sheet_row"] not in FORMULA_ROWS
        ],
        key=lambda x: x["sheet_row"],
    )


def filter_rules(rules: list, row_min: int, row_max: int) -> list:
    """Return rules for rows in [row_min, row_max], sorted by priority then fs_item."""
    filtered = [
        r for r in rules
        if row_min <= r["canonical_sheet_row"] <= row_max
    ]
    return sorted(
        filtered,
        key=lambda r: (
            PRIORITY_ORDER.get(r["priority"], 99),
            r["canonical_sheet_row"],
            r.get("fs_item", ""),
        ),
    )


def filter_training(examples: list, row_min: int, row_max: int) -> list:
    """Return training examples for rows in [row_min, row_max], deduplicated by (text.lower(), label)."""
    seen: set = set()
    result = []
    # Sort for determinism before dedup
    sorted_examples = sorted(
        examples,
        key=lambda e: (e["label"], e["text"].lower()),
    )
    for ex in sorted_examples:
        if row_min <= ex["label"] <= row_max:
            key = (ex["text"].lower(), ex["label"])
            if key not in seen:
                seen.add(key)
                result.append(ex)
    return result


# ---------------------------------------------------------------------------
# Domain-knowledge synthesis
# ---------------------------------------------------------------------------

def synthesize_domain_knowledge(rules: list, labels: list, agent_name: str) -> str:
    """
    Synthesize 3 sub-sections from the golden rules:
    1. CA-override directives (highest priority)
    2. Industry-specific rules (non-override, grouped by industry, capped at 20 each)
    3. Per-row common items (top 8 unique text samples per row)
    """
    lines: list[str] = []

    # --- CA overrides grouped by industry ---
    ca_overrides = [r for r in rules if r["priority"] == "ca_override"]
    if ca_overrides:
        lines.append("### CA-Override Directives (Highest Priority)")
        lines.append(
            "These rules were set by the CA after resolving contradictions and "
            "MUST be followed regardless of text similarity:"
        )
        lines.append("")
        by_industry: dict[str, list] = {}
        for r in ca_overrides:
            ind = r.get("industry_type", "all")
            by_industry.setdefault(ind, []).append(r)
        for ind in sorted(by_industry.keys()):
            lines.append(f"**Industry: {ind}**")
            for r in sorted(by_industry[ind], key=lambda x: (x["canonical_sheet_row"], x.get("fs_item", ""))):
                lines.append(
                    f'- "{r["fs_item_original"]}" -> R{r["canonical_sheet_row"]} '
                    f'({r["canonical_field_name"]})'
                )
            lines.append("")

    # --- Industry-specific rules (non-override) ---
    non_override = [r for r in rules if r["priority"] != "ca_override"]
    if non_override:
        lines.append("### Industry-Specific Rules")
        by_industry_no: dict[str, list] = {}
        for r in non_override:
            ind = r.get("industry_type", "all")
            by_industry_no.setdefault(ind, []).append(r)
        for ind in sorted(by_industry_no.keys()):
            ind_rules = sorted(
                by_industry_no[ind],
                key=lambda x: (x["canonical_sheet_row"], x.get("fs_item", "")),
            )[:20]  # cap at 20
            lines.append(f"**Industry: {ind}**")
            for r in ind_rules:
                tag = f"[{r['priority'].upper()}]"
                lines.append(
                    f'- {tag} "{r["fs_item_original"]}" -> R{r["canonical_sheet_row"]} '
                    f'({r["canonical_field_name"]})'
                )
            lines.append("")

    # --- Per-row common items ---
    lines.append("### Common Items Per CMA Row (top 8 unique text samples)")
    row_groups: dict[int, list[str]] = {}
    for r in rules:
        row = r["canonical_sheet_row"]
        row_groups.setdefault(row, [])
        text = r.get("fs_item_original", r.get("fs_item", ""))
        if text and text not in row_groups[row]:
            row_groups[row].append(text)

    # Build a label lookup for row -> field name
    label_map = {lbl["sheet_row"]: lbl["name"] for lbl in labels}

    for row in sorted(row_groups.keys()):
        field_name = label_map.get(row, "?")
        samples = sorted(row_groups[row])[:8]
        samples_str = ", ".join(f'"{s}"' for s in samples)
        lines.append(f"- **R{row} ({field_name}):** {samples_str}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Router prompt builder
# ---------------------------------------------------------------------------

def build_router_prompt(labels: list) -> str:
    """Build the hand-written router prompt."""
    return """\
# CMA Router Agent

## Role
You are the **Router** in a multi-agent CMA classification pipeline. Your sole job is to
assign each incoming financial line item to exactly one of four specialist buckets. You do
NOT classify to a specific CMA row — that is the specialist's task.

## Buckets
| Bucket | Description | Typical CMA rows |
|---|---|---|
| `pl_income` | Revenue, sales, other income items | 22–34 |
| `pl_expense` | Manufacturing, admin, selling, finance costs, tax | 41–108 |
| `bs_liability` | Share capital, reserves, borrowings, payables | 110–160 |
| `bs_asset` | Fixed assets, investments, inventory, debtors, cash, current liabilities | 161–258 |

## Routing Signals (in order of priority)
1. **source_sheet** (strongest signal):
   - `pl` or `notes_pl` -> pl_income or pl_expense
   - `bs` or `notes_bs` -> bs_liability or bs_asset
2. **section header**: Revenue/Sales -> pl_income; Expenses/Cost -> pl_expense;
   Equity/Liabilities -> bs_liability; Assets -> bs_asset
3. **description keywords**:
   - Income keywords: sales, revenue, turnover, receipts, grant, subsidy, interest received, dividend
   - Expense keywords: cost, expense, wages, depreciation, amortisation, provision, tax, duty
   - Liability keywords: capital, reserve, loan, borrowing, creditor, payable, overdraft, deposit received
   - Asset keywords: fixed asset, land, building, machinery, investment, stock, inventory, debtor, receivable, cash, bank, advance paid

## page_type Awareness
- `face`: Summary-level figures from the face of a financial statement (P&L face, Balance Sheet face)
- `notes`: Detailed breakdowns from notes to accounts

Both face and notes items must be routed. Do not skip face items — they are valid and must
be assigned to a bucket.

## Critical Rules
- **Every item MUST get a bucket** — never return an empty bucket or omit an item.
- If signals conflict, use source_sheet as the tiebreaker.
- If source_sheet is absent, use section header, then keywords.
- When completely ambiguous between two buckets, prefer `pl_expense` over `pl_income` and
  `bs_asset` over `bs_liability`.

## Input Format
```json
{
  "industry_type": "manufacturing",
  "document_type": "annual_report",
  "items": [
    {
      "id": "item_001",
      "description": "Sales of Manufactured Products",
      "amount": 5000000,
      "section": "Revenue from Operations",
      "source_sheet": "notes_pl",
      "page_type": "notes"
    }
  ]
}
```

## Output Format
Return ONLY valid JSON — no markdown, no commentary:
```json
{
  "routing": [
    {
      "id": "item_001",
      "bucket": "pl_income",
      "reason": "source_sheet=notes_pl + section header 'Revenue from Operations'"
    }
  ]
}
```

### Valid bucket values
`pl_income` | `pl_expense` | `bs_liability` | `bs_asset`

Every item in the input `items` array must appear exactly once in the `routing` array.
"""


# ---------------------------------------------------------------------------
# Specialist prompt builder
# ---------------------------------------------------------------------------

def build_specialist_prompt(
    agent_name: str,
    labels: list,
    rules: list,
    training: list,
) -> str:
    row_min, row_max = AGENTS[agent_name]["row_range"]
    agent_labels = filter_labels(labels, row_min, row_max)
    agent_rules = filter_rules(rules, row_min, row_max)
    agent_training = filter_training(training, row_min, row_max)

    # ---- Layer 1: Identity ----
    agent_display = agent_name.replace("_", " ").title()
    sections_str = {
        "pl_income":    "Revenue, Sales (R22–R34) — income side of the Operating Statement",
        "pl_expense":   "Manufacturing, Admin, Selling, Finance Expenses, Tax (R41–R108)",
        "bs_liability": "Share Capital, Reserves, Borrowings, Payables (R110–R160)",
        "bs_asset":     "Fixed Assets, Investments, Inventory, Debtors, Cash, Advances (R161–R258)",
    }[agent_name]

    layer1 = f"""\
# CMA Specialist: {agent_display}

## Role
You are the **{agent_display} Specialist** in a multi-agent CMA (Credit Monitoring Arrangement)
classification pipeline for Indian CA firms. Items have already been routed to you by the Router agent.

Your job: classify each item to a **specific CMA row number** within your range (rows {row_min}–{row_max}).

You handle: **{sections_str}**

## Output Requirements
- Classify every item — never skip.
- Return a single JSON object with a `classifications` array.
- Use `cma_row: 0` and `cma_code: "DOUBT"` for uncertain items.
- confidence < 0.80 -> must be a doubt.
- Formula rows 200 and 201 -> NEVER classify into these.
"""

    # ---- Layer 2: CMA Rows Table ----
    table_rows = ["| Row | Code | Name | Section |", "|-----|------|------|---------|"]
    for lbl in agent_labels:
        table_rows.append(
            f"| {lbl['sheet_row']} | {lbl['code']} | {lbl['name']} | {lbl['section']} |"
        )

    layer2 = "## CMA Rows in This Specialist's Range\n\n" + "\n".join(table_rows)

    # ---- Layer 3: Golden Rules ----
    rule_lines = []
    for r in agent_rules:
        priority_tag = f"[{r['priority'].upper()}]"
        industry_tag = f"[{r.get('industry_type', 'all')}]"
        orig = r.get("fs_item_original", r.get("fs_item", ""))
        rule_lines.append(
            f"- {priority_tag} {industry_tag} "
            f'"{orig}" -> R{r["canonical_sheet_row"]} ({r["canonical_field_name"]})'
        )

    layer3 = (
        "## Golden Rules\n\n"
        "Priority order: CA_OVERRIDE > CA_INTERVIEW > LEGACY\n\n"
        + ("\n".join(rule_lines) if rule_lines else "_No rules for this range._")
    )

    # ---- Layer 4: Domain Knowledge ----
    domain_knowledge = synthesize_domain_knowledge(agent_rules, agent_labels, agent_name)
    layer4 = "## Domain Knowledge\n\n" + domain_knowledge

    # ---- Layer 5: Batch I/O + Training Examples ----
    sign_note = ""
    if agent_name == "pl_income":
        sign_note = """\
### Sign Rules
- sign = **1** (add): most income items
- sign = **-1** (subtract): Sales Returns, Trade Discounts, Excise Duty, Closing Stock
"""
    elif agent_name == "pl_expense":
        sign_note = """\
### Sign Rules
- sign = **1** (add): most expense items
- sign = **-1** (subtract): items that reduce expense (e.g., opening stock)
"""
    else:
        sign_note = """\
### Sign Rules
- sign = **1** for most items.
- sign = **-1** for contra items (e.g., accumulated depreciation on assets side).
"""

    layer5 = f"""\
## Batch Input / Output Format

### Input
```json
{{
  "industry_type": "manufacturing",
  "items": [
    {{
      "id": "item_001",
      "description": "Sales of Manufactured Products",
      "amount": 5000000,
      "section": "Revenue from Operations",
      "page_type": "notes",
      "has_note_breakdowns": true
    }}
  ]
}}
```

### Output
Return ONLY valid JSON — no markdown, no commentary:
```json
{{
  "classifications": [
    {{
      "id": "item_001",
      "cma_row": 22,
      "cma_code": "II_A1",
      "confidence": 0.97,
      "sign": 1,
      "reasoning": "Matches golden rule: manufacturing sales -> R22 Domestic"
    }}
  ]
}}
```

### Doubt Format
```json
{{
  "id": "item_002",
  "cma_row": 0,
  "cma_code": "DOUBT",
  "confidence": 0.45,
  "sign": 1,
  "reasoning": "Ambiguous between R30 (dividends) and R31 (interest received)",
  "alternatives": [
    {{"cma_row": 30, "cma_code": "II_B1", "confidence": 0.45}},
    {{"cma_row": 31, "cma_code": "II_B2", "confidence": 0.40}}
  ]
}}
```

{sign_note}
### Critical Rules
1. **Classify ALL items** — never omit any item from the `classifications` array.
2. confidence < 0.80 -> must use DOUBT format.
3. **NEVER classify into rows 200 or 201** — these are Excel formula rows.
4. Face vs notes dedup: if `has_note_breakdowns=true` AND `page_type="face"` -> classify as DOUBT
   (the face total duplicates the notes breakdown; let the reviewer decide which to keep).
5. Use the golden rules above as the primary signal. Training examples are secondary.
6. If an item's industry_type is provided and a matching industry rule exists, prefer it over "all" rules.
"""

    # ---- Training examples ----
    if agent_training:
        capped = agent_training[:40]
        ex_lines = [
            "## Training Examples (up to 40, deduplicated)\n",
            "| Text | CMA Row | Code | Field | Source | Industry |",
            "|------|---------|------|-------|--------|----------|",
        ]
        for ex in capped:
            text = ex["text"].replace("|", "/")
            ex_lines.append(
                f"| {text} | {ex['label']} | {ex.get('label_code','')} | "
                f"{ex.get('label_name','')} | {ex.get('source_form','')} | "
                f"{ex.get('industry_type','')} |"
            )
        training_section = "\n".join(ex_lines)
    else:
        training_section = "## Training Examples\n\n_No training examples for this range._"

    # ---- Assemble ----
    return "\n\n".join([layer1, layer2, layer3, layer4, layer5, training_section]) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # Load input files
    labels_path = GT_BASE / "reference" / "canonical_labels.json"
    rules_path  = GT_BASE / "reference" / "cma_golden_rules_v2.json"
    train_path  = GT_BASE / "database" / "training_data.json"

    print(f"Loading labels from:   {labels_path}")
    print(f"Loading rules from:    {rules_path}")
    print(f"Loading training from: {train_path}")

    with open(labels_path, "r", encoding="utf-8") as f:
        labels: list = json.load(f)

    with open(rules_path, "r", encoding="utf-8") as f:
        rules_data: dict = json.load(f)
    rules: list = rules_data["rules"]

    with open(train_path, "r", encoding="utf-8") as f:
        training: list = json.load(f)

    print(f"  Labels loaded:   {len(labels)}")
    print(f"  Rules loaded:    {len(rules)}")
    print(f"  Training loaded: {len(training)}")

    # Ensure output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    stats: dict[str, int] = {}

    # --- Router ---
    router_prompt = build_router_prompt(labels)
    router_path = OUTPUT_DIR / "router_prompt.md"
    router_path.write_text(router_prompt, encoding="utf-8")
    stats["router"] = len(router_prompt.splitlines())
    print(f"  [router]  {stats['router']} lines -> {router_path.name}")

    # --- Specialists ---
    for agent_name in ("pl_income", "pl_expense", "bs_liability", "bs_asset"):
        row_min, row_max = AGENTS[agent_name]["row_range"]
        prompt = build_specialist_prompt(agent_name, labels, rules, training)
        out_path = OUTPUT_DIR / f"{agent_name}_prompt.md"
        out_path.write_text(prompt, encoding="utf-8")
        stats[agent_name] = len(prompt.splitlines())

        # Stats for this agent
        a_labels   = filter_labels(labels, row_min, row_max)
        a_rules    = filter_rules(rules, row_min, row_max)
        a_training = filter_training(training, row_min, row_max)
        print(
            f"  [{agent_name:<12}] rows={len(a_labels):3d}  "
            f"rules={len(a_rules):3d}  train={len(a_training):3d}  "
            f"lines={stats[agent_name]:4d} -> {out_path.name}"
        )

    print("\nAll prompts generated successfully.")
    print(f"Output directory: {OUTPUT_DIR}")
    total_lines = sum(stats.values())
    print(f"Total lines across all prompts: {total_lines}")


if __name__ == "__main__":
    main()
