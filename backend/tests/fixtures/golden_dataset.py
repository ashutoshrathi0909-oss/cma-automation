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
        "financial_year": 2023,
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
        "financial_year": 2022,
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
        "financial_year": 2023,
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
        "financial_year": 2021,
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
        "financial_year": 2022,
        "document_type": "profit_and_loss",
        "industry_type": "trading",
    },
]


# ── Helpers ────────────────────────────────────────────────────────────────

def get_ai_only_items() -> list[dict]:
    """All items go through AI in the single-tier pipeline (April 2026).

    Previously only 12 items reached Tier 2 (DeepSeek). Now ALL items are
    classified by AI — regex/golden/fuzzy tiers were removed.
    """
    return list(GOLDEN_ITEMS)


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
