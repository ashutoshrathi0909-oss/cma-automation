"""
vision_prompt.py
================
System prompt, tool schema, and JSON schema for vision-based financial extraction.

Exports:
- SYSTEM_PROMPT: Instruction prompt for the vision model (Gemini / Claude).
- EXTRACT_TOOL_SCHEMA: Anthropic tool_use format (Claude fallback path).
- EXTRACT_JSON_SCHEMA: Flat JSON schema for OpenRouter response_format (Gemini path).
- MAX_PAGES_PER_BATCH: Max pages sent per API call.
"""

SYSTEM_PROMPT = """You are a financial data extraction specialist for Indian CA firms.
You are analyzing scanned page images from Indian audited financial statements
(Balance Sheet, Profit & Loss Account, Trading Account, Notes to Accounts, Schedules).

YOUR TASK: Extract ALL financial line items with their amounts from each page image.

CRITICAL RULES:

1. EXTRACT ALL LINE ITEMS exactly as they appear in the document.
   Include every named financial item — revenue lines, expense lines, asset lines,
   liability lines, sub-items from Notes, individual product categories for trading firms,
   and any other line with a monetary amount. Do NOT skip items.

2. TRADING ACCOUNT: Indian firms often show a separate Trading Account before the P&L.
   Extract all lines from it — Purchases, Sales, Opening Stock, Closing Stock,
   Gross Profit/Loss, Carriage Inward, etc. Use section "income" for sales/revenue
   lines and "expenses" for purchase/cost lines.

3. TWO-COLUMN BALANCE SHEET (Liabilities | Assets): Extract each line item from
   BOTH columns separately. Do NOT merge left and right columns into one item.

4. P&L / INCOME & EXPENDITURE: Extract revenue categories, expense categories,
   and profit/loss lines. Include individual product categories if they appear
   (e.g., "Sales – Keyboards", "Sales – RAM Modules"). These are real line items
   for trading companies.

5. GST LINES: Lines like "Add: GST Paid", "Less: GST Collected", "CGST", "SGST",
   "IGST" — extract them normally with their amounts and correct section.
   Do NOT skip GST lines. Do NOT confuse them with sales revenue.

6. NOTES TO ACCOUNTS: Extract EVERY sub-item as a separate line item.
   Each sub-item (e.g., Wages, Power & Fuel, Repairs under "Manufacturing Expenses")
   maps to a different CMA row. NEVER collapse sub-items into their parent total.
   If Note 15 shows "Manufacturing Expenses: ₹5.5 Cr" broken into Wages ₹2 Cr,
   Power ₹1.5 Cr, Repairs ₹2 Cr — extract three items (Wages, Power, Repairs),
   NOT the ₹5.5 Cr total.

7. INDIAN NUMBER FORMAT: "1,23,456" = 123456. Report amounts WITHOUT commas.

8. SCALE FACTOR: If page header says "in Lakhs" → scale_factor = "in_lakhs".
   If "in Crores" → "in_crores". If "in Thousands" → "in_thousands".
   Otherwise "absolute".

9. NEGATIVE AMOUNTS: Amounts in parentheses are negative: (1,23,456) = -123456.

10. SKIP PAGES containing: auditor's report, directors' report, Form 3CA/3CB,
    corporate information, accounting policies (narrative text without amounts).
    Return an empty items array for these pages.

11. SKIP: Addresses, phone numbers, registration numbers, GSTIN, PAN, signatures,
    bank account numbers.

12. SKIP BALANCING FIGURES: "To Gross Profit", "To Net Profit", "By Gross Profit",
    "By Net Profit" — these are balancing figures, not real financial items.

13. SUB-LEDGER DETAIL PAGES (list of individual creditors/debtors): Extract ONLY
    the total line (e.g., "Sundry Creditors: ₹X"), not each individual name.

14. SECTIONS: Assign each item to one of: income / expenses / assets / liabilities / equity

AMBIGUITY DETECTION:
Flag with ambiguity_question when a single line combines amounts that the Indian CMA
format needs split into different rows. Common ambiguous items:

- "Employee Benefit Expenses" without breakdown → could be Salary (CMA R67) +
  Wages (R45) + PF/ESI contributions. Ask: "Does this include manufacturing wages
  (R45) or is it entirely admin salaries (R67)?"

- "Other Expenses" or "Miscellaneous Expenses" > ₹1 lakh without breakdown →
  could span Admin Expenses (R71), Other Manufacturing Expenses (R49), or Finance
  Costs. Ask: "Please break down Other Expenses into manufacturing vs admin vs finance."

- "Repairs & Maintenance" without context → Manufacturing Repairs (R50) vs
  Admin Repairs (R72). Ask: "Is this manufacturing (R50) or admin (R72) repairs?"

- "Depreciation" without breakdown → Manufacturing Depreciation (R56) vs
  Admin/General Depreciation (R63). Ask: "Is this on factory assets (R56) or
  admin assets (R63), or a mix?"

- "Interest & Finance Charges" as a single lump → Term Loan Interest (R83) vs
  Working Capital Interest (R84) vs Bank Charges (R85).
  Ask: "Break down into term loan interest (R83), WC interest (R84), and bank charges (R85)."

- "Wages & Other Expenses" → CMA needs Wages (R45) separate from Other Mfg Expenses (R49).

Only flag when: (a) amount > ₹1,00,000 AND (b) CMA genuinely needs different rows.
Include CMA row numbers in the question. Still extract the total amount.

FEW-SHOT EXAMPLE:
For a Balance Sheet page showing:
  Share Capital    10,00,000  |  Fixed Assets     15,00,000
  Reserves          5,00,000  |

Expected output (abbreviated):
{"page_results": [{"page_number": 1, "page_type": "balance_sheet", "scale_factor": "absolute", "items": [{"description": "Share Capital", "amount": 1000000, "section": "equity", "ambiguity_question": null}, {"description": "Reserves", "amount": 500000, "section": "equity", "ambiguity_question": null}, {"description": "Fixed Assets", "amount": 1500000, "section": "assets", "ambiguity_question": null}]}], "currency_detected": "INR", "company_name": null, "financial_year": null}

Respond with a single JSON object matching the provided schema. Do not include any text outside the JSON."""

# ---------------------------------------------------------------------------
# Anthropic tool_use schema (Claude fallback path)
# ---------------------------------------------------------------------------
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
                                "profit_and_loss",
                                "balance_sheet",
                                "trading_account",
                                "notes_to_accounts",
                                "schedules",
                                "auditor_report",
                                "other_non_financial",
                            ],
                        },
                        "scale_factor": {
                            "type": "string",
                            "enum": [
                                "absolute",
                                "in_thousands",
                                "in_lakhs",
                                "in_crores",
                            ],
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
                                        "enum": [
                                            "income",
                                            "expenses",
                                            "assets",
                                            "liabilities",
                                            "equity",
                                            "",
                                        ],
                                    },
                                    "ambiguity_question": {
                                        "type": ["string", "null"],
                                    },
                                },
                                "required": [
                                    "description",
                                    "amount",
                                    "section",
                                    "ambiguity_question",
                                ],
                            },
                        },
                    },
                    "required": [
                        "page_number",
                        "page_type",
                        "scale_factor",
                        "items",
                    ],
                },
            },
            "currency_detected": {"type": "string"},
            "company_name": {"type": ["string", "null"]},
            "financial_year": {"type": ["string", "null"]},
        },
        "required": ["page_results", "currency_detected"],
    },
}

# ---------------------------------------------------------------------------
# Flat JSON schema for OpenRouter response_format (Gemini structured output)
# ---------------------------------------------------------------------------
# No $ref — fully inlined. additionalProperties: false at every object level
# as required by strict JSON schema mode.
EXTRACT_JSON_SCHEMA = {
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
                            "profit_and_loss",
                            "balance_sheet",
                            "trading_account",
                            "notes_to_accounts",
                            "schedules",
                            "auditor_report",
                            "other_non_financial",
                        ],
                    },
                    "scale_factor": {
                        "type": "string",
                        "enum": [
                            "absolute",
                            "in_thousands",
                            "in_lakhs",
                            "in_crores",
                        ],
                    },
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {
                                    "type": "string",
                                    "description": "Financial line item name exactly as it appears.",
                                },
                                "amount": {
                                    "type": "number",
                                    "description": "Numeric amount without commas. Negative if in parentheses.",
                                },
                                "section": {
                                    "type": "string",
                                    "enum": [
                                        "income",
                                        "expenses",
                                        "assets",
                                        "liabilities",
                                        "equity",
                                        "unknown",
                                    ],
                                    "description": "Which financial statement section this item belongs to. Use 'unknown' if genuinely unclear.",
                                },
                                "ambiguity_question": {
                                    "anyOf": [{"type": "string"}, {"type": "null"}],
                                    "description": "Question for CA if line item is ambiguous for CMA classification. null if unambiguous.",
                                },
                            },
                            "required": [
                                "description",
                                "amount",
                                "section",
                                "ambiguity_question",
                            ],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": [
                    "page_number",
                    "page_type",
                    "scale_factor",
                    "items",
                ],
                "additionalProperties": False,
            },
        },
        "currency_detected": {
            "type": "string",
            "description": "Currency code detected (e.g., INR).",
        },
        "company_name": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "description": "Company name if detected on the pages, otherwise null.",
        },
        "financial_year": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "description": "Financial year if detected (e.g., 2023-24), otherwise null.",
        },
    },
    "required": ["page_results", "currency_detected", "company_name", "financial_year"],
    "additionalProperties": False,
}

# ---------------------------------------------------------------------------
# Batching
# ---------------------------------------------------------------------------
# Gemini's 1M context window handles 8 pages comfortably
# (~10,400 image tokens + prompt + output).
MAX_PAGES_PER_BATCH = 8
