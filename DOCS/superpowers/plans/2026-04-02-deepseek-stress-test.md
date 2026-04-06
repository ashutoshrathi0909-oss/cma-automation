# DeepSeek Classification Stress Test & Interview Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stress-test DeepSeek V3's classification accuracy with adversarial items (curve balls, industry traps, context switches, typos, combined lines, negative amounts), then run an "interview round" to discover gaps and improvement opportunities.

**Architecture:** A self-contained test that simulates the real app environment — feeds items to ScopedClassifier exactly as the production pipeline does, with all golden rules loaded. Tests both classification accuracy AND Excel formula output (additions AND subtractions in the same cell).

**Tech Stack:** pytest, unittest.mock, openpyxl, `ScopedClassifier`, `ExcelGenerator`

**Key fix applied before this plan:** `scoped_classifier.py` line 51 now points to `cma_golden_rules_v2.json` (594 CA-verified rules) instead of the old `cma_classification_rules.json` (385 legacy rules). All 140 ca_override rules are now visible to DeepSeek with `[CA-VERIFIED OVERRIDE]` markers in the prompt.

---

## File Structure

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `backend/tests/fixtures/golden_dataset.py` | Full adversarial dataset with formula expectations including subtractions |
| Create | `backend/tests/test_deepseek_golden.py` | Mock pipeline test + formula verification + live API stress test |
| Create | `backend/tests/test_deepseek_interview.py` | Interview round — probes DeepSeek with targeted questions to find gaps |

---

## IMPORTANT: Formula Expectations

When multiple items land in the same CMA cell, the Excel output MUST be a transparent formula showing every component — **additions AND subtractions**:

```
Items in R45 (Wages):
  Gratuity:           300,000
  EPF:                 50,000
  Staff Mess:          25,000
  Staff Welfare:       35,000
  Salary Wages Bonus: 450,000
  Leave Encashment:   -15,000  (negative — write-back)
→ Formula: "=300000+50000+25000+35000+450000-15000"
  NOT: "=845000"

Items in R22 (Domestic Sales):
  Product Sales:      500,000
  Sales Returns:      -30,000  (negative)
  Trade Discount:     -12,000  (negative)
→ Formula: "=500000-30000-12000"
  NOT: "=458000"
```

The formula builder handles negatives automatically: negative values include their `-` sign, no `+-` ever appears.

---

### Task 1: Fix and Finalize the Golden Dataset

**Files:**
- Rewrite: `backend/tests/fixtures/golden_dataset.py`

The previous dataset had bugs:
1. R45 formula didn't account for ALL items landing there (5 items, not 3)
2. Sales items (twist-007, twist-009) reached AI tier but had no mock answer
3. Vehicle HP (twist-015) was caught by regex "vehicle" → R162 instead of golden rule R148

This task fixes all issues and adds new adversarial items.

- [ ] **Step 1: Write the corrected golden dataset**

Create `backend/tests/fixtures/__init__.py` (empty) and `backend/tests/fixtures/golden_dataset.py` with this content:

```python
"""Golden test dataset for DeepSeek AI classification stress test.

Adversarial items where the AI's naive suggestion was WRONG and
the CA corrected it. Includes curve balls, industry traps, typos,
combined lines, and negative amounts (subtractions in formulas).

Sources:
  1. DOCS/ca_answers_2026-03-26.json       — 68 CA questionnaire answers
  2. DOCS/GT_disputes_responses -3.json    — 175 dispute resolutions
  3. DOCS/Rule_contradictions_responses.json — 35 contradiction decisions
"""

GOLDEN_CLIENT_ID = "golden-client-0001"
GOLDEN_DOC_ID_PL = "golden-doc-pl"
GOLDEN_DOC_ID_BS = "golden-doc-bs"
GOLDEN_YEAR = 2024


# ── Formula expectations ──────────────────────────────────────────────────
# (row, year) → expected Excel formula string
# These include BOTH additions AND subtractions.

EXPECTED_FORMULAS: dict[tuple[int, int], str] = {
    # R45 (Wages): 6 items — 5 positive + 1 negative (leave encashment write-back)
    (45, GOLDEN_YEAR): "=300000+50000+25000+35000+450000-15000",
    # R71 (Others Admin): 3 positive items
    (71, GOLDEN_YEAR): "=18000+10000+15000",
    # R22 (Domestic Sales): 1 positive + 2 negatives (returns + discount)
    (22, GOLDEN_YEAR): "=500000-30000-12000",
    # R84 (Interest on WC): 2 items — 1 positive + 1 negative (interest refund)
    (84, GOLDEN_YEAR): "=22000+45000-8000",
}

EXPECTED_PLAIN_VALUES: dict[tuple[int, int], float] = {
    (23, GOLDEN_YEAR): 200000.0,     # Export Sales: single item
    (85, GOLDEN_YEAR): 8500.0,       # Bank Charges: single item
    (73, GOLDEN_YEAR): 600000.0,     # Directors Remuneration: single item
    (148, GOLDEN_YEAR): 120000.0,    # Vehicle HP Other Debts: single item
    (149, GOLDEN_YEAR): 200000.0,    # Other LT Liabilities: single item
    (68, GOLDEN_YEAR): 28000.0,      # Rent (with typo test): single item
}


GOLDEN_ITEMS: list[dict] = [

    # ──────────────────────────────────────────────────────────────────────
    # GROUP A: WAGES (R45) — 6 items → "=300000+50000+25000+35000+450000-15000"
    # Tests: CA overrides, industry routing, combined lines, NEGATIVE amount
    # ──────────────────────────────────────────────────────────────────────
    {
        "id": "T01",
        "description": "gratuity to employees",
        "amount": 300000.0,
        "section": "employee benefits expense",
        "raw_text": "Gratuity to Employees  3,00,000",
        "expected_cma_field": "Wages",
        "expected_cma_row": 45,
        "twist": "AI suggested R67 (Salary), CA overrode to R45. Source: Q1b",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "manufacturing",
    },
    {
        "id": "T02",
        "description": "contribution to epf",
        "amount": 50000.0,
        "section": "employee benefits expense",
        "raw_text": "Contribution to EPF  50,000",
        "expected_cma_field": "Wages",
        "expected_cma_row": 45,
        "twist": "AI suggested R67, CA overrode to R45. Source: Q1c",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "manufacturing",
    },
    {
        "id": "T03",
        "description": "staff mess expenses",
        "amount": 25000.0,
        "section": "employee benefits expense",
        "raw_text": "Staff Mess Expenses  25,000",
        "expected_cma_field": "Wages",
        "expected_cma_row": 45,
        "twist": "AI suggested R67, CA overrode to R45. Source: Q1e",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "manufacturing",
    },
    {
        "id": "T04",
        "description": "staff welfare expenses",
        "amount": 35000.0,
        "section": "employee benefits expense",
        "raw_text": "Staff Welfare Expenses  35,000",
        "expected_cma_field": "Wages",
        "expected_cma_row": 45,
        "twist": "Manufacturing → R45, trading → R67. Tests industry routing. Source: Q1a",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "manufacturing",
    },
    {
        "id": "T05",
        "description": "salary wages and bonus",
        "amount": 450000.0,
        "section": "employee benefits expense",
        "raw_text": "Salary, Wages and Bonus  4,50,000",
        "expected_cma_field": "Wages",
        "expected_cma_row": 45,
        "twist": "COMBINED line item — AI suggested R67, CA says R45. Source: Q1h",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "manufacturing",
    },
    {
        # NEGATIVE amount — leave encashment write-back reduces wages
        "id": "T06",
        "description": "leave encashment written back",
        "amount": -15000.0,
        "section": "employee benefits expense",
        "raw_text": "Leave Encashment Written Back  (15,000)",
        "expected_cma_field": "Wages",
        "expected_cma_row": 45,
        "twist": "NEGATIVE amount in wages — formula must show subtraction. Source: Q1 context",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "manufacturing",
    },

    # ──────────────────────────────────────────────────────────────────────
    # GROUP B: OTHERS ADMIN (R71) — 3 items → "=18000+10000+15000"
    # Tests: CA overrides (licence ≠ rent, damages ≠ interest)
    # ──────────────────────────────────────────────────────────────────────
    {
        "id": "T07",
        "description": "tally erp subscription",
        "amount": 18000.0,
        "section": "admin expenses",
        "raw_text": "Tally ERP Subscription  18,000",
        "expected_cma_field": "Others (Admin)",
        "expected_cma_row": 71,
        "twist": "Licence/subscription → R71, NOT R68 (Rent/Rates). Source: Q3f",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "manufacturing",
    },
    {
        "id": "T08",
        "description": "liquidated damages",
        "amount": 10000.0,
        "section": "other expenses",
        "raw_text": "Liquidated Damages  10,000",
        "expected_cma_field": "Others (Admin)",
        "expected_cma_row": 71,
        "twist": "AI suggested R83 (Interest), CA says R71 (Admin). Source: Q10d",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "manufacturing",
    },
    {
        "id": "T09",
        "description": "licence and subscription fees",
        "amount": 15000.0,
        "section": "admin expenses",
        "raw_text": "Licence and Subscription Fees  15,000",
        "expected_cma_field": "Others (Admin)",
        "expected_cma_row": 71,
        "twist": "AI suggested R68, CA says R71. Source: Q3f",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "manufacturing",
    },

    # ──────────────────────────────────────────────────────────────────────
    # GROUP C: DOMESTIC SALES (R22) — 3 items → "=500000-30000-12000"
    # Tests: negative amounts (returns + discount = subtractions)
    # ──────────────────────────────────────────────────────────────────────
    {
        "id": "T10",
        "description": "sale of manufactured products",
        "amount": 500000.0,
        "section": "revenue from operations",
        "raw_text": "Sale of Manufactured Products  5,00,000",
        "expected_cma_field": "Domestic Sales",
        "expected_cma_row": 22,
        "twist": "Straightforward, but tests formula with two negative partners",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "manufacturing",
    },
    {
        "id": "T11",
        "description": "sales returns",
        "amount": -30000.0,
        "section": "revenue from operations",
        "raw_text": "Sales Returns  (30,000)",
        "expected_cma_field": "Domestic Sales",
        "expected_cma_row": 22,
        "twist": "NEGATIVE — subtraction in formula, no +-",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "manufacturing",
    },
    {
        "id": "T12",
        "description": "trade discount allowed",
        "amount": -12000.0,
        "section": "revenue from operations",
        "raw_text": "Trade Discount Allowed  (12,000)",
        "expected_cma_field": "Domestic Sales",
        "expected_cma_row": 22,
        "twist": "Second NEGATIVE in same cell — formula must handle multiple subtractions",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "manufacturing",
    },

    # ──────────────────────────────────────────────────────────────────────
    # GROUP D: INTEREST ON WC (R84) — 3 items → "=22000+45000-8000"
    # Tests: interest traps + negative (interest refund)
    # ──────────────────────────────────────────────────────────────────────
    {
        "id": "T13",
        "description": "interest on delay in payment of income tax",
        "amount": 22000.0,
        "section": "financial costs",
        "raw_text": "Interest on Delay in Payment of Income Tax  22,000",
        "expected_cma_field": "Interest on Working capital loans",
        "expected_cma_row": 84,
        "twist": "AI suggested R83 (Fixed Loans), CA says R84 (WC). Source: Q10b",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "manufacturing",
    },
    {
        "id": "T14",
        "description": "bill discounting charges",
        "amount": 45000.0,
        "section": "financial costs",
        "raw_text": "Bill Discounting Charges  45,000",
        "expected_cma_field": "Interest on Working capital loans",
        "expected_cma_row": 84,
        "twist": "AI suggested R83, CA says R84. Source: Q10e",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "manufacturing",
    },
    {
        # NEGATIVE — interest refund received
        "id": "T15",
        "description": "excess interest refund from bank",
        "amount": -8000.0,
        "section": "financial costs",
        "raw_text": "Excess Interest Refund from Bank  (8,000)",
        "expected_cma_field": "Interest on Working capital loans",
        "expected_cma_row": 84,
        "twist": "NEGATIVE interest — subtraction in formula. Refund reduces total.",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "manufacturing",
    },

    # ──────────────────────────────────────────────────────────────────────
    # GROUP E: SINGLE-ITEM CELLS (plain values, no formula)
    # ──────────────────────────────────────────────────────────────────────
    {
        "id": "T16",
        "description": "export sales revenue",
        "amount": 200000.0,
        "section": "revenue from operations",
        "raw_text": "Export Sales Revenue  2,00,000",
        "expected_cma_field": "Export Sales",
        "expected_cma_row": 23,
        "twist": "Single item → plain value, not formula",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "manufacturing",
    },
    {
        "id": "T17",
        "description": "loan processing fee",
        "amount": 8500.0,
        "section": "financial costs",
        "raw_text": "Loan Processing Fee  8,500",
        "expected_cma_field": "Bank Charges",
        "expected_cma_row": 85,
        "twist": "AI suggested R84 (WC Interest), CA says R85 (Bank Charges). Source: Q10g",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "manufacturing",
    },
    {
        "id": "T18",
        "description": "directors remuneration",
        "amount": 600000.0,
        "section": "admin expenses",
        "raw_text": "Directors Remuneration  6,00,000",
        "expected_cma_field": "Audit Fees & Directors Remuneration",
        "expected_cma_row": 73,
        "twist": "Must go to R73, NOT R67 (Salary). Source: pipeline rule BCIPL-001",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "manufacturing",
    },

    # ──────────────────────────────────────────────────────────────────────
    # GROUP F: INDUSTRY-DEPENDENT ROUTING
    # Same item, different industry → different CMA row
    # ──────────────────────────────────────────────────────────────────────
    {
        "id": "T19",
        "description": "staff welfare expenses",
        "amount": 35000.0,
        "section": "employee benefits",
        "raw_text": "Staff Welfare Expenses  35,000",
        "expected_cma_field": "Salary and staff expenses",
        "expected_cma_row": 67,
        "twist": "SAME text as T04 but TRADING → R67, not R45! Source: Q1a",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "trading",
    },
    {
        "id": "T20",
        "description": "bonus to employees",
        "amount": 40000.0,
        "section": "employee benefits expense",
        "raw_text": "Bonus to Employees  40,000",
        "expected_cma_field": "Salary and staff expenses",
        "expected_cma_row": 67,
        "twist": "Bonus in TRADING → R67. In manufacturing it would be R45. Source: Q1g",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "trading",
    },

    # ──────────────────────────────────────────────────────────────────────
    # GROUP G: BALANCE SHEET TRAPS
    # ──────────────────────────────────────────────────────────────────────
    {
        "id": "T21",
        "description": "vehicle hire purchase current maturities",
        "amount": 120000.0,
        "section": "current liabilities",
        "raw_text": "Vehicle Hire Purchase - Current Maturities  1,20,000",
        "expected_cma_field": "Other Debts Repayable in Next One year",
        "expected_cma_row": 148,
        "twist": "AI suggested R140 (Debentures), CA says R148 (Other Debts). Source: Q17",
        "financial_year": GOLDEN_YEAR,
        "document_type": "balance_sheet",
        "industry_type": "manufacturing",
    },
    {
        "id": "T22",
        "description": "other long term liabilities",
        "amount": 200000.0,
        "section": "non-current liabilities",
        "raw_text": "Other Long Term Liabilities  2,00,000",
        "expected_cma_field": "Balance Other Debts",
        "expected_cma_row": 149,
        "twist": "AI suggested R153 (Unsecured LT Debt), CA says R149. Source: Q20",
        "financial_year": GOLDEN_YEAR,
        "document_type": "balance_sheet",
        "industry_type": "manufacturing",
    },

    # ──────────────────────────────────────────────────────────────────────
    # GROUP H: CURVE BALLS — tricky edge cases
    # ──────────────────────────────────────────────────────────────────────
    {
        "id": "T23",
        "description": "miscellaneous expenses",
        "amount": 12000.0,
        "section": "other expenses",
        "raw_text": "Miscellaneous Expenses  12,000",
        "expected_cma_field": "Others (Admin)",
        "expected_cma_row": 71,
        "twist": "R75 is ONLY for non-cash write-offs. Misc cash expenses → R71.",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "manufacturing",
    },
    {
        # TYPO — common in Indian financials
        "id": "T24",
        "description": "rent rates and taxs",
        "amount": 28000.0,
        "section": "admin expenses",
        "raw_text": "Rent, Rates and Taxs  28,000",
        "expected_cma_field": "Rent, Rates and Taxes",
        "expected_cma_row": 68,
        "twist": "TYPO: 'Taxs' instead of 'Taxes'. Pipeline must handle misspellings.",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "manufacturing",
    },
    {
        # Section header says "Finance Cost" but item is actually admin
        "id": "T25",
        "description": "insurance premium",
        "amount": 42000.0,
        "section": "finance cost",
        "raw_text": "Insurance Premium  42,000",
        "expected_cma_field": "Others (Admin)",
        "expected_cma_row": 71,
        "twist": "MISLEADING SECTION: listed under finance cost, but CA says R71 Admin.",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "manufacturing",
    },
    {
        # Context-dependent: Leave Encashment in BS → R249 (not R45!)
        "id": "T26",
        "description": "provision for leave encashment",
        "amount": 55000.0,
        "section": "provisions",
        "raw_text": "Provision for Leave Encashment  55,000",
        "expected_cma_field": "Creditors for Expenses",
        "expected_cma_row": 249,
        "twist": "P&L leave encashment → R45. But BS provision → R249! Context switch.",
        "financial_year": GOLDEN_YEAR,
        "document_type": "balance_sheet",
        "industry_type": "manufacturing",
    },
    {
        # Subsidy in P&L → R33 (Extraordinary Income), not R125
        "id": "T27",
        "description": "government subsidy received",
        "amount": 75000.0,
        "section": "other income",
        "raw_text": "Government Subsidy Received  75,000",
        "expected_cma_field": "Extraordinary income",
        "expected_cma_row": 33,
        "twist": "P&L subsidy → R33 (Extraordinary income). BS subsidy → R125. Source: CA rule",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "manufacturing",
    },
    {
        # Power charges: manufacturing → R48, but TRADING → R71!
        "id": "T28",
        "description": "electricity charges",
        "amount": 65000.0,
        "section": "admin expenses",
        "raw_text": "Electricity Charges  65,000",
        "expected_cma_field": "Others (Admin)",
        "expected_cma_row": 71,
        "twist": "Manufacturing → R48 (Power/Fuel). But TRADING → R71 (Admin)! Source: Q12a",
        "financial_year": GOLDEN_YEAR,
        "document_type": "profit_and_loss",
        "industry_type": "trading",
    },
]


# ── Helpers ────────────────────────────────────────────────────────────────

def get_ai_only_items() -> list[dict]:
    """Items that should reach Tier 2 (DeepSeek) — not caught by regex/golden/fuzzy."""
    # These have phrasing that earlier tiers likely miss
    ai_tier_ids = {"T13", "T14", "T15", "T21", "T22", "T25", "T26", "T27"}
    return [i for i in GOLDEN_ITEMS if i["id"] in ai_tier_ids]


def get_industry_pairs() -> list[tuple[dict, dict]]:
    """Pairs of items that must route differently by industry."""
    pairs = []
    # Staff Welfare: T04 (manufacturing R45) vs T19 (trading R67)
    t04 = next(i for i in GOLDEN_ITEMS if i["id"] == "T04")
    t19 = next(i for i in GOLDEN_ITEMS if i["id"] == "T19")
    pairs.append((t04, t19))
    return pairs


def make_pipeline_item(item: dict) -> dict:
    """Convert to dict format for ClassificationPipeline.classify_item()."""
    return {
        "id": item["id"],
        "document_id": GOLDEN_DOC_ID_PL if item["document_type"] == "profit_and_loss" else GOLDEN_DOC_ID_BS,
        "description": item["description"],
        "source_text": item["description"],
        "amount": item["amount"],
        "section": item["section"],
        "raw_text": item["raw_text"],
        "is_verified": True,
    }


def make_cell_data_item(item: dict) -> dict:
    """Convert to dict format for ExcelGenerator._fill_data_cells()."""
    return {
        "cma_field_name": item["expected_cma_field"],
        "cma_row": item["expected_cma_row"],
        "financial_year": item["financial_year"],
        "amount": item["amount"],
        "document_id": GOLDEN_DOC_ID_PL if item["document_type"] == "profit_and_loss" else GOLDEN_DOC_ID_BS,
    }
```

- [ ] **Step 2: Verify dataset loads and formula math is correct**

```bash
cd backend && python -c "
from tests.fixtures.golden_dataset import GOLDEN_ITEMS, EXPECTED_FORMULAS, EXPECTED_PLAIN_VALUES
print(f'{len(GOLDEN_ITEMS)} items')
print(f'{len(EXPECTED_FORMULAS)} formula cells')
print(f'{len(EXPECTED_PLAIN_VALUES)} plain value cells')

# Verify formulas match actual item amounts
from collections import defaultdict
by_row = defaultdict(list)
for item in GOLDEN_ITEMS:
    by_row[(item['expected_cma_row'], item['financial_year'])].append(item['amount'])

for key, amounts in sorted(by_row.items()):
    if len(amounts) > 1:
        print(f'  R{key[0]}: {amounts} -> formula expected')
        assert key in EXPECTED_FORMULAS, f'Missing formula expectation for R{key[0]}'
    else:
        print(f'  R{key[0]}: {amounts[0]} -> plain value expected')
print('All formula expectations verified.')
"
```

Expected: `28 items`, `4 formula cells`, `6 plain value cells`, `All formula expectations verified.`

- [ ] **Step 3: Commit**

```bash
git add backend/tests/fixtures/
git commit -m "test: add adversarial golden dataset with additions and subtractions

28 items covering CA overrides, industry routing, combined lines,
typos, misleading sections, context switches (P&L vs BS), and
negative amounts. Formula expectations include subtraction."
```

---

### Task 2: Write the Mock-Based Pipeline Test

**Files:**
- Create: `backend/tests/test_deepseek_golden.py`
- Reference: `backend/app/services/classification/pipeline.py:84-337`

Tests the FULL pipeline with real RuleEngine and GoldenRuleLookup.
FuzzyMatcher is mocked (no Supabase). ScopedClassifier is mocked
to return correct answers for items that reach Tier 2.

- [ ] **Step 1: Write the test file**

Create `backend/tests/test_deepseek_golden.py`:

```python
"""DeepSeek AI Golden Test Suite — adversarial stress test.

Every item has a known correct answer from CA-verified decisions.
Many are curve balls where the AI's naive suggestion was WRONG.

Run mock tests:     pytest tests/test_deepseek_golden.py -v -k "not Live"
Run live API test:  pytest tests/test_deepseek_golden.py -v -k "Live"
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import openpyxl
import pytest
from openpyxl.utils import column_index_from_string

from tests.fixtures.golden_dataset import (
    EXPECTED_FORMULAS,
    EXPECTED_PLAIN_VALUES,
    GOLDEN_CLIENT_ID,
    GOLDEN_ITEMS,
    GOLDEN_YEAR,
    get_ai_only_items,
    get_industry_pairs,
    make_cell_data_item,
    make_pipeline_item,
)


# ── Helpers ────────────────────────────────────────────────────────────────


def _make_ai_result(item):
    from app.services.classification.ai_classifier import AIClassificationResult
    return AIClassificationResult(
        cma_field_name=item["expected_cma_field"],
        cma_row=item["expected_cma_row"],
        cma_sheet="input_sheet",
        broad_classification=None,
        confidence=0.92,
        is_doubt=False,
        doubt_reason=None,
        alternatives=[],
        classification_method="scoped_v3",
    )


def _make_doubt():
    from app.services.classification.ai_classifier import AIClassificationResult
    return AIClassificationResult(
        cma_field_name="UNCLASSIFIED", cma_row=0, cma_sheet="input_sheet",
        broad_classification=None, confidence=0.3, is_doubt=True,
        doubt_reason="No match in golden test", alternatives=[],
        classification_method="scoped_v3",
    )


def _run_pipeline(items=None):
    from app.services.classification.pipeline import ClassificationPipeline
    if items is None:
        items = GOLDEN_ITEMS
    os.environ.setdefault("PROJECT_ROOT", str(Path(__file__).parents[1].parent))

    ai_answers = {i["description"]: _make_ai_result(i) for i in get_ai_only_items()}

    class MockFuzzy:
        def match(self, description, industry_type=None):
            return []

    class MockAI:
        def classify(self, **kw):
            return ai_answers.get(kw.get("raw_text"), _make_doubt())
        def classify_sync(self, **kw):
            return ai_answers.get(kw.get("raw_text"), _make_doubt())

    with patch("app.services.classification.pipeline.FuzzyMatcher", MockFuzzy), \
         patch("app.services.classification.pipeline.ScopedClassifier", MockAI), \
         patch("app.services.classification.pipeline.AIClassifier", MockAI), \
         patch("app.services.classification.pipeline.get_settings") as ms:
        ms.return_value = MagicMock(classifier_mode="scoped", openrouter_api_key="test")
        pipeline = ClassificationPipeline()
        results = []
        for item in items:
            r = pipeline.classify_item(
                item=make_pipeline_item(item),
                client_id=GOLDEN_CLIENT_ID,
                industry_type=item["industry_type"],
                document_type=item["document_type"],
                financial_year=item["financial_year"],
            )
            r["_id"] = item["id"]
            r["_expected_row"] = item["expected_cma_row"]
            r["_expected_field"] = item["expected_cma_field"]
            r["_twist"] = item.get("twist", "")
            results.append(r)
        return results


# ═══ Test Class 1: All items classified correctly ═══

class TestGoldenClassification:

    def test_all_items_correct_row(self):
        results = _run_pipeline()
        failures = []
        for r in results:
            if r["cma_row"] != r["_expected_row"]:
                failures.append(
                    f"  {r['_id']}: expected R{r['_expected_row']}, "
                    f"got R{r['cma_row']} ({r['cma_field_name']})\n"
                    f"    Twist: {r['_twist']}"
                )
        assert not failures, f"\n{len(failures)} errors:\n" + "\n".join(failures)

    def test_no_doubts(self):
        results = _run_pipeline()
        doubts = [r for r in results if r.get("is_doubt")]
        assert not doubts, "\n".join(f"  {r['_id']}: {r.get('doubt_reason')}" for r in doubts)

    def test_count_matches(self):
        assert len(_run_pipeline()) == len(GOLDEN_ITEMS)


# ═══ Test Class 2: Industry routing ═══

class TestGoldenIndustryRouting:

    def test_staff_welfare_mfg_vs_trading(self):
        for mfg, trd in get_industry_pairs():
            mr = _run_pipeline([mfg])[0]
            tr = _run_pipeline([trd])[0]
            assert mr["cma_row"] == mfg["expected_cma_row"]
            assert tr["cma_row"] == trd["expected_cma_row"]
            assert mr["cma_row"] != tr["cma_row"], "Same item must route differently by industry"

    def test_bonus_mfg_r45_trading_r67(self):
        # T05 has "bonus" in manufacturing context → R45 via regex
        # T20 has "bonus" in trading context → R67
        t20 = next(i for i in GOLDEN_ITEMS if i["id"] == "T20")
        r = _run_pipeline([t20])[0]
        assert r["cma_row"] == 67, f"Trading bonus: expected R67, got R{r['cma_row']}"


# ═══ Test Class 3: CA Override edge cases ═══

class TestGoldenCAOverrides:

    def test_gratuity_r45(self):
        r = _run_pipeline([GOLDEN_ITEMS[0]])[0]
        assert r["cma_row"] == 45

    def test_liquidated_damages_r71(self):
        item = next(i for i in GOLDEN_ITEMS if i["id"] == "T08")
        assert _run_pipeline([item])[0]["cma_row"] == 71

    def test_loan_processing_fee_r85(self):
        item = next(i for i in GOLDEN_ITEMS if i["id"] == "T17")
        assert _run_pipeline([item])[0]["cma_row"] == 85

    def test_misc_expenses_r71_not_r75(self):
        item = next(i for i in GOLDEN_ITEMS if i["id"] == "T23")
        assert _run_pipeline([item])[0]["cma_row"] == 71

    def test_directors_remuneration_r73(self):
        item = next(i for i in GOLDEN_ITEMS if i["id"] == "T18")
        assert _run_pipeline([item])[0]["cma_row"] == 73


# ═══ Test Class 4: Formula output ═══

class TestGoldenFormulas:

    def _build_ws(self):
        from app.services.excel_generator import ExcelGenerator
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "INPUT SHEET"
        gen = ExcelGenerator(service=MagicMock(), template_path="/fake/template.xlsm")
        gen._fill_data_cells(ws, [make_cell_data_item(i) for i in GOLDEN_ITEMS], year_map={GOLDEN_YEAR: "B"})
        return ws

    def test_multi_item_formulas(self):
        ws = self._build_ws()
        col = column_index_from_string("B")
        for (row, _), expected in EXPECTED_FORMULAS.items():
            actual = ws.cell(row=row, column=col).value
            assert actual == expected, f"R{row}: expected '{expected}', got '{actual}'"

    def test_single_item_plain_values(self):
        ws = self._build_ws()
        col = column_index_from_string("B")
        for (row, _), expected in EXPECTED_PLAIN_VALUES.items():
            actual = ws.cell(row=row, column=col).value
            assert actual == expected, f"R{row}: expected {expected}, got '{actual}'"

    def test_no_sum_function(self):
        ws = self._build_ws()
        col = column_index_from_string("B")
        for (row, _), formula in EXPECTED_FORMULAS.items():
            val = str(ws.cell(row=row, column=col).value)
            assert "SUM" not in val.upper(), f"R{row}: must not use SUM()"

    def test_no_plus_minus_concatenation(self):
        """Negative amounts must show as subtraction, never +-."""
        ws = self._build_ws()
        col = column_index_from_string("B")
        for (row, _), formula in EXPECTED_FORMULAS.items():
            val = str(ws.cell(row=row, column=col).value)
            assert "+-" not in val, f"R{row}: got '+-' in '{val}'"

    def test_subtraction_present_where_expected(self):
        """Formulas with negative items must contain '-' (not just '+')."""
        ws = self._build_ws()
        col = column_index_from_string("B")
        # R45 has one negative (-15000), R22 has two negatives, R84 has one negative
        for row in [45, 22, 84]:
            val = str(ws.cell(row=row, column=col).value)
            assert "-" in val[1:], f"R{row}: expected subtraction in formula, got '{val}'"


# ═══ Test Class 5: Live DeepSeek API (Opt-in) ═══

_HAS_KEY = bool(os.environ.get("OPENROUTER_API_KEY"))

@pytest.mark.skipif(not _HAS_KEY, reason="OPENROUTER_API_KEY not set")
class TestGoldenLiveDeepSeek:
    """Calls real DeepSeek API on adversarial items. Max 8 items."""

    def test_accuracy(self):
        from app.services.classification.scoped_classifier import ScopedClassifier
        classifier = ScopedClassifier()
        ai_items = get_ai_only_items()
        assert len(ai_items) <= 10

        results = []
        for item in ai_items:
            r = classifier.classify_sync(
                raw_text=item["description"], amount=item["amount"],
                section=item["section"], industry_type=item["industry_type"],
                document_type=item["document_type"], fuzzy_candidates=[],
            )
            results.append({
                "id": item["id"], "desc": item["description"],
                "expected": item["expected_cma_row"], "got": r.cma_row,
                "conf": r.confidence, "twist": item.get("twist", ""),
            })

        correct = sum(1 for r in results if r["got"] == r["expected"])
        total = len(results)
        pct = correct / total if total else 0

        print(f"\n{'='*60}")
        print(f"DeepSeek Stress Test: {correct}/{total} ({pct:.0%})")
        print(f"{'='*60}")
        for r in results:
            s = "PASS" if r["got"] == r["expected"] else "FAIL"
            print(f"  [{s}] {r['id']}: '{r['desc']}' -> R{r['got']} (expected R{r['expected']}) conf={r['conf']:.2f}")
            print(f"       Twist: {r['twist']}")

        assert pct >= 0.75, f"Accuracy {pct:.0%} below 75%"
```

- [ ] **Step 2: Run the mock tests**

```bash
cd backend && python -m pytest tests/test_deepseek_golden.py -v --tb=short -k "not Live"
```

Expected: All mock tests PASS (16 tests). If any fail, fix the dataset or pipeline rules.

- [ ] **Step 3: Debug and fix any failures**

Common failure modes:
- Item hits wrong regex rule → check `rule_engine.py` for conflicting patterns
- Golden rule not matching → check text normalization in `GoldenRuleLookup`
- Formula expectation wrong → verify all items landing in that row

Fix the test expectations if the PIPELINE is correct but our expectation was wrong.
Fix the PIPELINE if the classification is genuinely incorrect.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_deepseek_golden.py
git commit -m "test: add adversarial classification stress test with formula verification

16 mock tests covering CA overrides, industry routing, curve balls,
typos, misleading sections, context switches, and formula output
with additions and subtractions."
```

---

### Task 3: Write the DeepSeek Interview Round

**Files:**
- Create: `backend/tests/test_deepseek_interview.py`

This is NOT a pass/fail test. It's a diagnostic that probes DeepSeek with
deliberately ambiguous items to discover GAPS in its knowledge. The output
is a report that tells you what to improve.

- [ ] **Step 1: Write the interview test**

Create `backend/tests/test_deepseek_interview.py`:

```python
"""DeepSeek Interview Round — diagnostic probe, not pass/fail.

Calls real DeepSeek API with deliberately ambiguous items to discover
gaps and improvement opportunities. Produces a diagnostic report.

Run: OPENROUTER_API_KEY=<key> pytest tests/test_deepseek_interview.py -v -s
"""

from __future__ import annotations

import json
import os

import pytest

_HAS_KEY = bool(os.environ.get("OPENROUTER_API_KEY"))

# ── Interview questions ──────────────────────────────────────────────────
# Each question tests a specific weakness area.

INTERVIEW_QUESTIONS = [
    # Q1: Does DeepSeek understand industry-dependent routing?
    {
        "id": "IQ01",
        "text": "staff welfare expenses",
        "amount": 25000,
        "section": "employee benefits",
        "industry": "manufacturing",
        "doc_type": "profit_and_loss",
        "correct_row": 45,
        "probe": "Industry routing: should be R45 for manufacturing, R67 for trading",
    },
    {
        "id": "IQ02",
        "text": "staff welfare expenses",
        "amount": 25000,
        "section": "employee benefits",
        "industry": "trading",
        "doc_type": "profit_and_loss",
        "correct_row": 67,
        "probe": "Same item, different industry — must give DIFFERENT answer",
    },

    # Q3: Context switch — P&L vs BS
    {
        "id": "IQ03",
        "text": "leave encashment",
        "amount": 30000,
        "section": "employee benefits",
        "industry": "manufacturing",
        "doc_type": "profit_and_loss",
        "correct_row": 45,
        "probe": "Leave encashment in P&L → R45. In BS → R249. Tests context awareness.",
    },
    {
        "id": "IQ04",
        "text": "provision for leave encashment",
        "amount": 30000,
        "section": "provisions",
        "industry": "manufacturing",
        "doc_type": "balance_sheet",
        "correct_row": 249,
        "probe": "Same concept, BS context → R249 (Creditors for Expenses), NOT R45",
    },

    # Q5: Subsidy context switch
    {
        "id": "IQ05",
        "text": "government grant subsidy",
        "amount": 100000,
        "section": "other income",
        "industry": "manufacturing",
        "doc_type": "profit_and_loss",
        "correct_row": 33,
        "probe": "P&L subsidy → R33 (Extraordinary income). BS → R125 (Other Reserve).",
    },

    # Q6: Misleading section header
    {
        "id": "IQ06",
        "text": "insurance premium",
        "amount": 50000,
        "section": "manufacturing overheads",
        "industry": "manufacturing",
        "doc_type": "profit_and_loss",
        "correct_row": 71,
        "probe": "Even under 'manufacturing overheads', insurance → R71 Admin. CA rule.",
    },

    # Q7: Compound ambiguity — combined line with misleading name
    {
        "id": "IQ07",
        "text": "employee benefit expenses including gratuity epf and esi",
        "amount": 500000,
        "section": "employee cost",
        "industry": "manufacturing",
        "doc_type": "profit_and_loss",
        "correct_row": 45,
        "probe": "Long combined line — must classify by nature (employee cost → R45 mfg)",
    },

    # Q8: Amount-based hint — very small amount suggests admin, not manufacturing
    {
        "id": "IQ08",
        "text": "repairs and maintenance",
        "amount": 500,
        "section": "expenses",
        "industry": "manufacturing",
        "doc_type": "profit_and_loss",
        "correct_row": 50,
        "probe": "Even tiny amount — repairs in manufacturing context → R50, not R72 (Admin)",
    },

    # Q9: Interest confusion
    {
        "id": "IQ09",
        "text": "interest on unsecured loan from directors",
        "amount": 80000,
        "section": "finance cost",
        "industry": "manufacturing",
        "doc_type": "profit_and_loss",
        "correct_row": 83,
        "probe": "Unsecured loan interest → R83 (Fixed Loans), not R84 (WC). Source: BCIPL-006",
    },

    # Q10: Negative amount confusion
    {
        "id": "IQ10",
        "text": "discount received from suppliers",
        "amount": -25000,
        "section": "other income",
        "industry": "manufacturing",
        "doc_type": "profit_and_loss",
        "correct_row": 34,
        "probe": "Negative-looking income item. Should be R34 (Others Non-Op Income).",
    },

    # Q11: The classic trap — "Other Charges"
    {
        "id": "IQ11",
        "text": "other charges",
        "amount": 15000,
        "section": "expenses",
        "industry": "manufacturing",
        "doc_type": "profit_and_loss",
        "correct_row": 71,
        "probe": "Vague 'other charges' with no context — should default to R71 (Admin Others)",
    },

    # Q12: Electricity in trading
    {
        "id": "IQ12",
        "text": "electricity charges",
        "amount": 30000,
        "section": "admin expenses",
        "industry": "trading",
        "doc_type": "profit_and_loss",
        "correct_row": 71,
        "probe": "Electricity: manufacturing → R48, trading → R71. Source: Q12a",
    },
]


@pytest.mark.skipif(not _HAS_KEY, reason="OPENROUTER_API_KEY not set")
class TestDeepSeekInterview:
    """Diagnostic interview — produces a gap analysis report."""

    def test_interview_round(self):
        from app.services.classification.scoped_classifier import ScopedClassifier

        classifier = ScopedClassifier()
        results = []

        for q in INTERVIEW_QUESTIONS:
            r = classifier.classify_sync(
                raw_text=q["text"], amount=q["amount"],
                section=q["section"], industry_type=q["industry"],
                document_type=q["doc_type"], fuzzy_candidates=[],
            )
            passed = r.cma_row == q["correct_row"]
            results.append({
                "id": q["id"],
                "text": q["text"],
                "industry": q["industry"],
                "correct": q["correct_row"],
                "got": r.cma_row,
                "got_name": r.cma_field_name,
                "conf": r.confidence,
                "passed": passed,
                "probe": q["probe"],
            })

        # ── Print diagnostic report ──
        correct = sum(1 for r in results if r["passed"])
        total = len(results)
        print(f"\n{'='*70}")
        print(f"  DEEPSEEK INTERVIEW REPORT: {correct}/{total} ({correct/total:.0%})")
        print(f"{'='*70}")

        # Group by pass/fail
        passed_items = [r for r in results if r["passed"]]
        failed_items = [r for r in results if not r["passed"]]

        if failed_items:
            print(f"\n  GAPS FOUND ({len(failed_items)}):")
            print(f"  {'-'*66}")
            for r in failed_items:
                print(f"  [{r['id']}] '{r['text']}' ({r['industry']})")
                print(f"    Expected: R{r['correct']}")
                print(f"    Got:      R{r['got']} ({r['got_name']}) conf={r['conf']:.2f}")
                print(f"    Probe:    {r['probe']}")
                print()

        if passed_items:
            print(f"\n  PASSED ({len(passed_items)}):")
            print(f"  {'-'*66}")
            for r in passed_items:
                print(f"  [{r['id']}] '{r['text']}' ({r['industry']}) -> R{r['got']} conf={r['conf']:.2f}")

        print(f"\n{'='*70}")
        print(f"  IMPROVEMENT RECOMMENDATIONS:")
        print(f"{'='*70}")

        # Auto-generate recommendations based on failures
        gap_categories = {
            "industry_routing": [],
            "context_switch": [],
            "misleading_section": [],
            "interest_confusion": [],
            "ambiguous_items": [],
            "other": [],
        }

        for r in failed_items:
            if "industry" in r["probe"].lower():
                gap_categories["industry_routing"].append(r)
            elif "context" in r["probe"].lower() or "P&L" in r["probe"] or "BS" in r["probe"]:
                gap_categories["context_switch"].append(r)
            elif "misleading" in r["probe"].lower() or "section" in r["probe"].lower():
                gap_categories["misleading_section"].append(r)
            elif "interest" in r["probe"].lower():
                gap_categories["interest_confusion"].append(r)
            elif "vague" in r["probe"].lower() or "ambig" in r["probe"].lower():
                gap_categories["ambiguous_items"].append(r)
            else:
                gap_categories["other"].append(r)

        for cat, items in gap_categories.items():
            if items:
                print(f"\n  {cat.upper().replace('_', ' ')} ({len(items)} failures):")
                if cat == "industry_routing":
                    print("    -> Add industry_type to DeepSeek prompt as a top-level instruction")
                    print("    -> Add more industry-specific examples to training data")
                elif cat == "context_switch":
                    print("    -> Add document_type (P&L vs BS) as explicit context in prompt")
                    print("    -> Add CA rules for P&L-vs-BS disambiguation to hard-coded rules")
                elif cat == "misleading_section":
                    print("    -> Add 'classify by NATURE not section header' emphasis in prompt")
                elif cat == "interest_confusion":
                    print("    -> Expand CA disambiguation rules for interest categories")
                elif cat == "ambiguous_items":
                    print("    -> For truly ambiguous items, lower confidence to trigger doubt")

        print(f"\n{'='*70}\n")

        # Save results to JSON for analysis
        report_path = os.path.join(os.path.dirname(__file__), "interview_results.json")
        with open(report_path, "w") as f:
            json.dump({"total": total, "correct": correct, "results": results}, f, indent=2)
        print(f"  Full report saved to: {report_path}")

        # Don't fail the test — this is diagnostic, not pass/fail
        # But warn if accuracy is very low
        if correct / total < 0.5:
            pytest.skip(f"DeepSeek accuracy {correct/total:.0%} — needs significant improvement")
```

- [ ] **Step 2: Commit**

```bash
git add backend/tests/test_deepseek_interview.py
git commit -m "test: add DeepSeek interview round for gap analysis

12 diagnostic probes testing industry routing, context switches,
misleading sections, interest confusion, and ambiguous items.
Produces improvement recommendations report."
```

---

### Task 4: Run All Tests and Verify

- [ ] **Step 1: Run mock tests (no API key needed)**

```bash
cd backend && python -m pytest tests/test_deepseek_golden.py -v --tb=short -k "not Live"
```

Expected: All mock tests PASS.

- [ ] **Step 2: Run existing tests for regression check**

```bash
cd backend && python -m pytest tests/test_excel_generator.py tests/test_classification_pipeline.py -v --tb=short 2>&1 | tail -20
```

Expected: No regressions.

- [ ] **Step 3: (Optional) Run live DeepSeek stress test**

```bash
cd backend && OPENROUTER_API_KEY=<key> python -m pytest tests/test_deepseek_golden.py -v -s -k "Live"
```

Expected: >=75% accuracy. Print detailed report.

- [ ] **Step 4: (Optional) Run DeepSeek interview**

```bash
cd backend && OPENROUTER_API_KEY=<key> python -m pytest tests/test_deepseek_interview.py -v -s
```

Expected: Diagnostic report with gap analysis and improvement recommendations.

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "test: complete DeepSeek stress test and interview suite

- 28 adversarial items with formula expectations (additions + subtractions)
- 16 mock tests (pipeline routing, CA overrides, industry, formulas)
- Live API stress test (opt-in, bounded to 8 items)
- 12-question diagnostic interview with auto-recommendations
- ScopedClassifier now uses golden_rules_v2.json (594 CA rules)"
```

---

## Summary

| Test File | Tests | API Required | What It Tests |
|-----------|-------|-------------|---------------|
| `test_deepseek_golden.py` (mock) | 16 | No | Pipeline routing, CA overrides, industry routing, formula output |
| `test_deepseek_golden.py` (live) | 1 | Yes | Real DeepSeek accuracy on 8 adversarial items |
| `test_deepseek_interview.py` | 1 | Yes | 12 diagnostic probes with gap analysis report |

**Formula coverage:**
- R45: 5 additions + 1 subtraction → `=300000+50000+25000+35000+450000-15000`
- R22: 1 addition + 2 subtractions → `=500000-30000-12000`
- R84: 2 additions + 1 subtraction → `=22000+45000-8000`
- R71: 3 additions → `=18000+10000+15000`

**Curve balls included:**
1. CA overrides that contradict AI's suggestion (7 items)
2. Industry-dependent routing — same item, different row (3 items)
3. Combined line items — "Salary, Wages and Bonus" (1 item)
4. Typos — "Taxs" instead of "Taxes" (1 item)
5. Misleading section headers — insurance under "finance cost" (1 item)
6. P&L vs BS context switch — leave encashment R45 vs R249 (1 item)
7. Negative amounts — returns, refunds, write-backs (4 items)
8. Electricity routing — manufacturing R48 vs trading R71 (1 item)

**ScopedClassifier fix applied:**
- `RULES_PATH` now points to `cma_golden_rules_v2.json` (594 rules)
- All 140 ca_override rules enriched with `canonical_code` and `canonical_name`
- ca_override rules sorted first, never truncated by the 20-rule prompt limit
- `[CA-VERIFIED OVERRIDE]` marker added to prompt for ca_override rules
