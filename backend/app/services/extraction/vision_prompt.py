"""
vision_prompt.py
================
System prompt and tool schema for Claude Vision financial extraction.

Follows the tool_use pattern established in ai_classifier.py:
- tool_choice forces structured JSON output
- Confidence/ambiguity fields included in schema
"""

SYSTEM_PROMPT = """You are a financial data extraction specialist for Indian CA firms.
You are analyzing scanned pages from Indian audited financial statements (Balance Sheet,
Profit & Loss Account, Notes to Accounts, Schedules).

Extract EVERY financial line item with its amount.

CRITICAL RULES:
1. For Notes to Accounts: extract DETAILED sub-breakdowns, NOT just note totals.
   Example: Note 15 shows "Manufacturing Expenses: ₹5.5 Cr" broken into Wages, Power, Repairs —
   extract each sub-item separately, not the total.
2. Indian number format: "1,23,456" = 123456. Report amounts WITHOUT commas.
3. If page header says "in Lakhs" → set scale_factor to "in_lakhs".
   If "in Crores" → "in_crores". Otherwise "absolute".
4. Amounts in parentheses are negative: (1,23,456) = -123456.
5. SKIP pages containing: auditor's report, directors' report, Form 3CA/3CB,
   corporate information, accounting policies (narrative text). Return empty items array.
6. Sections: income / expenses / assets / liabilities / equity

AMBIGUITY DETECTION:
Flag with ambiguity_question when a single line combines amounts that Indian CMA needs split.
Common cases:
- "Wages & Other Expenses" → CMA needs Wages (Row 45) vs Other Mfg Exp (Row 49)
- "Employee Benefit Expenses" without breakdown → Salary (Row 67) vs Wages (Row 45)
- "Other Expenses" > ₹1 lakh with no breakdown → ask CA to break it down

Only flag when: (a) amount > ₹1,00,000 AND (b) CMA genuinely needs different rows.
Include CMA row numbers in the question. Still extract the total amount.
"""

EXTRACT_TOOL_SCHEMA = {
    "name": "extract_financial_items",
    "description": "Extract all financial line items from the provided scanned page images.",
    "input_schema": {
        "type": "object",
        "properties": {
            "page_results": {
                "type": "array",
                "description": "One entry per page. Empty items array for non-financial pages.",
                "items": {
                    "type": "object",
                    "properties": {
                        "page_number": {"type": "integer"},
                        "page_type": {
                            "type": "string",
                            "enum": [
                                "profit_and_loss", "balance_sheet", "notes_to_accounts",
                                "schedules", "auditor_report", "other_non_financial",
                            ],
                        },
                        "scale_factor": {
                            "type": "string",
                            "enum": ["absolute", "in_thousands", "in_lakhs", "in_crores"],
                        },
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "description": {"type": "string"},
                                    "amount": {"type": "number"},
                                    "section": {
                                        "type": "string",
                                        "enum": ["income", "expenses", "assets",
                                                 "liabilities", "equity", ""],
                                    },
                                    "ambiguity_question": {"type": ["string", "null"]},
                                },
                                "required": ["description", "amount", "section", "ambiguity_question"],
                            },
                        },
                    },
                    "required": ["page_number", "page_type", "scale_factor", "items"],
                },
            },
            "currency_detected": {"type": "string"},
            "company_name": {"type": ["string", "null"]},
            "financial_year": {"type": ["string", "null"]},
        },
        "required": ["page_results", "currency_detected"],
    },
}

# Maximum pages per Claude Vision API call (stays within token limits).
# 15 pages × many items → hits 8192 token output limit; 5 pages is safer.
MAX_PAGES_PER_BATCH = 5
