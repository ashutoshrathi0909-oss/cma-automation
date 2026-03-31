# CA Answers Implementation Prompt

**Date:** 2026-03-26
**Purpose:** Apply all CA-verified classification answers to the codebase
**Source of Truth:** `DOCS/ca_answers_2026-03-26.json` (GOLDEN RULE - DO NOT ALTER)

---

## Context

We ran a 9-company accuracy test on our CMA classification system and found 201 unique genuinely wrong classifications. A model interview of 100 items revealed:
- **45% routing bugs** (correct CMA row wasn't even in the options shown to the AI)
- **55% model errors** (correct row was available but AI picked wrong)

We then created a 76-question questionnaire for our CA (Chartered Accountant). The CA answered all 76 questions. Those answers are now the **golden rule** — they represent the CA's professional judgment and must be implemented exactly as given.

### System Architecture

The classification pipeline has 4 tiers:
1. **Tier 0: Rule Engine** (`backend/app/services/classification/rule_engine.py`) — Deterministic regex rules, checked FIRST. ~55 rules, confidence 0.85-0.97. Returns immediately if matched.
2. **Tier 1: Fuzzy Match** — Matches against `training_data.json` with threshold ≥85. Returns if match found.
3. **Tier 2: Scoped AI Classifier** (`backend/app/services/classification/scoped_classifier.py`) — Routes item to CMA section(s) via `_KEYWORD_ROUTES`, then sends to DeepSeek V3 with only the relevant CMA rows. Uses `cma_classification_rules.json` as "CA EXPERT RULES" in the prompt.
4. **Tier 3: Doubt Report** — Items below confidence threshold flagged for human review.

### Key Files to Modify

| File | What Changes |
|------|-------------|
| `backend/app/services/classification/rule_engine.py` | Add new deterministic rules, fix existing rules |
| `backend/app/services/classification/scoped_classifier.py` | Fix `_KEYWORD_ROUTES` routing, expand `SECTION_NORMALIZED_TO_CANONICAL` |
| `CMA_Ground_Truth_v1/reference/cma_classification_rules.json` | Fix/add CA expert rules shown to AI in prompt |
| `CMA_Ground_Truth_v1/database/training_data.json` | Add verified examples for fuzzy matching |
| `backend/app/mappings/cma_field_rows.py` | Verify all field→row mappings exist |

### Key Files to Read (DO NOT MODIFY)

| File | Why |
|------|-----|
| `DOCS/ca_answers_2026-03-26.json` | THE GOLDEN RULE — all CA answers |
| `backend/test-results/INTERVIEW_REPORT.md` | 100 interviewed wrong items with root causes |
| `backend/test-results/INTERVIEW_RESULTS.json` | Structured data for all 100 items |

---

## GOLDEN RULE: CA Answers

The file `DOCS/ca_answers_2026-03-26.json` contains 76 answers. **These are absolute.** The CA's professional judgment overrides any AI suggestion, any existing rule, and any prior convention. When implementing, if there is ANY conflict between existing code and a CA answer, the CA answer wins.

---

## Implementation Tasks

### TASK 1: Fix Rule Engine — Directors Remuneration (BCIPL-001)

**Current (WRONG):** Rule BCIPL-001 at line ~369 maps Directors Remuneration → R67 (Salary)
**CA Answer (Q21a):** Directors Remuneration → **R73** (Audit Fees & Directors Remuneration)

```python
# CURRENT (wrong):
# BCIPL-001: Directors Remuneration → R67
if self._is_directors_remuneration(text_lower):
    return _match("Salary and staff expenses", "admin_expense", "BCIPL-001", 0.95)

# CHANGE TO:
# BCIPL-001: Directors Remuneration → R73 (CA-verified 2026-03-26)
if self._is_directors_remuneration(text_lower):
    return _match("Audit Fees & Directors Remuneration", "admin_expense", "BCIPL-001", 0.95)
```

---

### TASK 2: Add New Deterministic Rules to Rule Engine

Add these NEW rules based on CA answers. Each rule should follow the existing pattern: add the rule call in the `apply()` method AND add the corresponding regex pattern method.

#### 2a. Industry-Specific Employee Cost Rules (Q1a, Q1g, Q1i)

CA confirmed: Staff Welfare, Bonus, and Employee Benefits Expense are **industry-dependent**.

| Item | Manufacturing/Construction | Trading/Services |
|------|---------------------------|-----------------|
| Staff Welfare Expenses | R45 (Wages) | R67 (Salary) |
| Bonus | R45 (Wages) | R67 (Salary) |
| Employee Benefits Expense | R45 (Wages) | R67 (Salary) |

```python
# CA-001: Staff Welfare → industry-dependent (CA-verified 2026-03-26)
if self._is_staff_welfare(text_lower):
    if industry in ("manufacturing", "construction"):
        return _match("Wages", "manufacturing_expense", "CA-001-mfg", 0.95)
    else:
        return _match("Salary and staff expenses", "admin_expense", "CA-001-svc", 0.95)

# CA-002: Bonus (standalone) → industry-dependent (CA-verified 2026-03-26)
# IMPORTANT: Must NOT match "Salary, Wages and Bonus" combined lines — those go to R45 always (Q1h)
if self._is_standalone_bonus(text_lower):
    if industry in ("manufacturing", "construction"):
        return _match("Wages", "manufacturing_expense", "CA-002-mfg", 0.95)
    else:
        return _match("Salary and staff expenses", "admin_expense", "CA-002-svc", 0.95)

# CA-003: Employee Benefits Expense (combined) → industry-dependent (CA-verified 2026-03-26)
if self._is_employee_benefits_combined(text_lower):
    if industry in ("manufacturing", "construction"):
        return _match("Wages", "manufacturing_expense", "CA-003-mfg", 0.95)
    else:
        return _match("Salary and staff expenses", "admin_expense", "CA-003-svc", 0.95)
```

**Regex patterns needed:**
- `_is_staff_welfare`: `\bstaff\s*welfare\b`
- `_is_standalone_bonus`: `\bbonus\b` BUT NOT matching "salary.*wages.*bonus" or "wages.*bonus" combined
- `_is_employee_benefits_combined`: `\bemployee\s*benefit\w*\s*expense\b`

#### 2b. Universal Employee Cost Rules (Q1b-Q1e, Q1h, Q1j)

CA confirmed: These ALWAYS go to R45 regardless of industry.

| Item | Row | Rule ID |
|------|-----|---------|
| Gratuity | R45 | CA-004 |
| EPF / Contribution to PF | R45 | CA-005 |
| ESI / Contribution to ESI | R45 | CA-006 |
| Staff Mess Expenses | R45 | CA-007 |
| "Salary, Wages and Bonus" (combined) | R45 | CA-008 |
| Labour Charges Paid | R45 | CA-009 |

```python
# CA-004: Gratuity → always R45 (CA-verified 2026-03-26, overrides AI R67)
if self._is_gratuity_expense(text_lower):
    return _match("Wages", "manufacturing_expense", "CA-004", 0.95)

# CA-005: EPF contribution → always R45
if self._is_epf_contribution(text_lower):
    return _match("Wages", "manufacturing_expense", "CA-005", 0.95)

# CA-006: ESI contribution → always R45
if self._is_esi_contribution(text_lower):
    return _match("Wages", "manufacturing_expense", "CA-006", 0.95)

# CA-007: Staff Mess → always R45
if self._is_staff_mess(text_lower):
    return _match("Wages", "manufacturing_expense", "CA-007", 0.95)

# CA-008: Combined "Salary, Wages and Bonus" → always R45
if self._is_salary_wages_bonus_combined(text_lower):
    return _match("Wages", "manufacturing_expense", "CA-008", 0.95)

# CA-009: Labour Charges → always R45
if self._is_labour_charges(text_lower):
    return _match("Wages", "manufacturing_expense", "CA-009", 0.95)
```

**Regex patterns needed:**
- `_is_gratuity_expense`: `\bgratuity\b` (P&L expense context — NOT the provision-for-gratuity BS liability which is already MSL-003)
- `_is_epf_contribution`: `\b(epf|e\.?p\.?f|provident\s*fund)\s*(contribution)?\b` or `\bcontribution\s*to\s*(epf|e\.?p\.?f|provident\s*fund)\b`
- `_is_esi_contribution`: `\b(esi|e\.?s\.?i\.?c?)\s*(contribution)?\b` or `\bcontribution\s*to\s*(esi|e\.?s\.?i\.?c?)\b`
- `_is_staff_mess`: `\bstaff\s*mess\b|\bcanteen\s*expense\b`
- `_is_salary_wages_bonus_combined`: `\bsalar(y|ies)\s*(,|and|&)\s*wages?\b` (the combined line item)
- `_is_labour_charges`: `\blabou?r\s*charges?\b`

**IMPORTANT ORDERING:** Place CA-008 (salary+wages+bonus combined) BEFORE any generic "salary" or "bonus" patterns, because "Salary, Wages and Bonus" as a single combined line always goes to R45. The industry-specific bonus rule (CA-002) only applies to standalone "Bonus" items.

#### 2c. Leave Encashment — Context-Dependent (Q1f)

CA confirmed: P&L → R45, Balance Sheet → R249.

```python
# CA-010: Leave Encashment → context-dependent (CA-verified 2026-03-26)
if self._is_leave_encashment(text_lower):
    if self._is_liability_section(section_lower) or self._is_balance_sheet_section(section_lower):
        return _match("Creditors for Expenses", "Current Liability", "CA-010-bs", 0.93)
    else:
        return _match("Wages", "manufacturing_expense", "CA-010-pl", 0.95)
```

Pattern: `\bleave\s*encashment\b|\bleave\s*salary\b`

#### 2d. Industry-Specific Power/Electric Rules (Q12a)

CA confirmed: Manufacturing/Construction → R48, Trading/Services → R71.

```python
# CA-011: Power/Electric Charges → industry-dependent (CA-verified 2026-03-26)
if self._is_power_electric(text_lower):
    if industry in ("manufacturing", "construction"):
        return _match("Power, Coal, Fuel and Water", "manufacturing_expense", "CA-011-mfg", 0.95)
    else:
        return _match("Others (Admin)", "admin_expense", "CA-011-svc", 0.93)
```

Pattern: `\b(electric\w*\s*(charges?|expense)|power\s*(charges?|expense)|electricity)\b` — but NOT "electricity deposit" (that's a security deposit, already handled by C-004-govt)

#### 2e. Finance Cost Rules (Q10b, Q10d, Q10g)

| Item | CA Answer | Rule ID |
|------|-----------|---------|
| Interest on Delay in Payment of Taxes | R84 (WC Interest) | CA-012 |
| Liquidated Damages | R71 (Others Admin) | CA-013 |
| Loan Processing Fee | R85 (Bank Charges) | CA-014 |

```python
# CA-012: Interest on tax delay → R84 (CA chose over AI's R83)
if self._is_interest_tax_delay(text_lower):
    return _match("Interest on Working capital loans", "Interest", "CA-012", 0.93)

# CA-013: Liquidated Damages → R71 (CA chose over AI's R83)
if self._is_liquidated_damages(text_lower):
    return _match("Others (Admin)", "admin_expense", "CA-013", 0.93)

# CA-014: Loan Processing Fee → R85 (CA chose over AI's R84)
if self._is_loan_processing_fee(text_lower):
    return _match("Bank Charges", "Interest", "CA-014", 0.93)
```

#### 2f. Borrowings Rules (Q17, Q20)

| Item | CA Answer | Rule ID |
|------|-----------|---------|
| Vehicle HP Current Maturities | R148 (Other Debts - repayable next year) | CA-015 |
| Other Long Term Liabilities | R149 (Balance Other Debts) | CA-016 |

```python
# CA-015: Vehicle HP Current Maturities → R148 (CA chose over AI's R140)
if self._is_vehicle_hp_current(text_lower):
    return _match("Repayable in next one year", "Current Liability", "CA-015", 0.93)

# CA-016: Other LT Liabilities → R149 (CA chose over AI's R153)
if self._is_other_lt_liability(text_lower):
    return _match("Balance Other Debts", "Term Liabilities", "CA-016", 0.90)
```

#### 2g. Balance Sheet Items (Q33, Q35)

| Item | CA Answer | Rule ID |
|------|-----------|---------|
| Advances to Suppliers | R220 (not R219) | CA-017 |
| Security Deposits Paid (generic) | R238 (Other non-current assets) | CA-018 |

```python
# CA-017: Advances to Suppliers → R220 (CA chose over AI's R219)
if self._is_advance_to_suppliers(text_lower):
    return _match("Advance to suppliers of Raw Materials and stores etc.", "Current Assets", "CA-017", 0.93)

# CA-018: Security Deposits (generic, not govt/private specific) → R238
# NOTE: This must come AFTER the existing C-004-govt and C-004-private rules
if self._is_generic_security_deposit(text_lower):
    return _match("Other non current assets", "Non-Current Assets", "CA-018", 0.90)
```

#### 2h. Licence & Subscription → R71 (Q3f)

CA confirmed: R71 (Others Admin), NOT R68 (Rent Rates Taxes) as AI suggested.

```python
# CA-019: Licence & Subscription → R71 (CA chose over AI's R68)
if self._is_licence_subscription(text_lower):
    return _match("Others (Admin)", "admin_expense", "CA-019", 0.93)
```

Pattern: `\b(licen[cs]e|subscription)\s*(fee|charge|expense)?\b`

#### 2i. Insurance Premium → R71 (Q22)

CA confirmed: R71 (Others Admin), NOT R49 (Others Manufacturing) as AI suggested.

```python
# CA-020: Insurance Premium → R71 (CA chose over AI's R49)
if self._is_insurance_premium(text_lower):
    return _match("Others (Admin)", "admin_expense", "CA-020", 0.93)
```

**IMPORTANT:** This must override the existing `_ADMIN_CATCHALL_TERMS` pattern (MSL-008) which also catches insurance. Place CA-020 BEFORE MSL-008.

#### 2j. Subsidy/Govt Grant — Context-Dependent (Q38)

CA confirmed: P&L → R33 (Extraordinary Income), BS → R125 (Other Reserves).

```python
# CA-021: Subsidy / Govt Grant → context-dependent (CA-verified 2026-03-26)
if self._is_subsidy_grant(text_lower):
    if self._is_balance_sheet_section(section_lower) or self._is_reserves_section(section_lower):
        return _match("Other Reserves", "Equity", "CA-021-bs", 0.90)
    else:
        return _match("Extraordinary income", "Non-operating Income", "CA-021-pl", 0.93)
```

Pattern: `\b(subsidy|government\s*grant|govt\s*grant|capital\s*subsidy|revenue\s*subsidy)\b`

#### 2k. Stores & Spares — Import Check (Q12g)

CA confirmed: R44 default, but R43 if "imported" is mentioned.

```python
# CA-022: Stores & Spares → R44 default, R43 if imported (CA-verified 2026-03-26)
if self._is_stores_spares(text_lower):
    if "import" in text_lower:
        return _match("Stores and spares consumed (Imported)", "manufacturing_expense", "CA-022-imp", 0.95)
    else:
        return _match("Stores and spares consumed (Indigenous)", "manufacturing_expense", "CA-022-ind", 0.95)
```

#### 2l. Issue of Bonus Shares → ALWAYS DOUBT (Q15)

CA confirmed: No CMA impact. Always flag as doubt for manual handling.

```python
# CA-023: Issue of Bonus Shares → always flag as doubt (CA-verified 2026-03-26)
# "Issue of bonus shares has no effect on CMA directly. Closing reserves after
#  bonus shares shall be reflected under R121-R125. Paid up capital in R118
#  includes issue of bonus shares."
if self._is_bonus_share_issue(text_lower):
    return None  # Let it fall through to doubt — do NOT classify
```

Actually, returning None lets it fall to fuzzy/AI which may classify it wrong. Better approach: return a special result that forces doubt. Check how the pipeline handles this — you may need to return a result with confidence below DOUBT_THRESHOLD (0.8):

```python
if self._is_bonus_share_issue(text_lower):
    return RuleMatchResult(
        cma_field_name="DOUBT - Bonus Share Issue (manual review required)",
        cma_row=0,
        cma_sheet="input_sheet",
        broad_classification="equity",
        rule_id="CA-023",
        confidence=0.0,  # Forces doubt status
    )
```

Pattern: `\b(issue|issuance)\s*(of\s*)?bonus\s*shares?\b|\bbonus\s*shares?\s*(issue|allot)\b`

#### 2m. Row 75 Usage Rule (Q4, Q32)

CA confirmed: Row 75 is ONLY for non-cash write-offs (amortisation of preliminary expenses, pre-operative expenses). Regular "Miscellaneous Expenses" → R71.

This is already partially handled by the `_ADMIN_CATCHALL_TERMS` pattern sending `miscellaneous exp` to R71. But add a specific rule for preliminary/pre-operative expense write-offs:

```python
# CA-024: Preliminary/Pre-operative Expense write-off → R75 (CA-verified 2026-03-26)
if self._is_preliminary_expense_writeoff(text_lower):
    return _match("Miscellaneous Expenses Written off", "admin_expense", "CA-024", 0.95)
```

Pattern: `\b(preliminary|pre[\s-]?operative|incorporation)\s*(expense|cost)?\s*(written\s*off|amortis|w/?o)\b|\bmisc\w*\s*exp\w*\s*written\s*off\b`

---

### TASK 3: Fix `_KEYWORD_ROUTES` in scoped_classifier.py

The `admin_expense` regex (line 193) is a black hole — it catches items that should route elsewhere:

**Current (too broad):**
```python
(r"(?i)(other expense|admin|audit|legal|professional|office|printing|telephone|travel|insurance|repair|miscellaneous exp|general expense|bank charge|vehicle|conveyance)", "admin_expense"),
```

**Problems identified:**
- `bank charge` → should route to `finance_cost` (CA Q10a: Bank Charges → R85)
- `vehicle` → already handled by C-001 in rule engine, but this catches "vehicle expenses" that might be admin
- `repair` → should route to `manufacturing_expense` for manufacturing companies (CA Q12b: R50)
- `insurance` → should stay admin (CA Q22 confirmed R71)

**Fix:** Remove `bank charge` from admin_expense regex and add it to `finance_cost` regex:

```python
# Line 192 (finance_cost) — ADD bank charge:
(r"(?i)(interest expense|finance cost|finance charge|interest on.*loan|interest on.*working|interest paid|bank interest|bank charge)", "finance_cost"),

# Line 193 (admin_expense) — REMOVE bank charge:
(r"(?i)(other expense|admin|audit|legal|professional|office|printing|telephone|travel|insurance|repair|miscellaneous exp|general expense|vehicle|conveyance)", "admin_expense"),
```

**Also add new routing patterns:**
```python
# After the employee_cost pattern (line 188), add:
# Audit / Directors fees route — ensures audit fees, directors remuneration reach the right section
(r"(?i)(audit\w*\s*(fee|remuneration)|director\w*\s*remuneration|statutory\s*audit)", "admin_expense"),

# After the manufacturing_expense pattern (line 189), add:
# Water/fuel/power route for manufacturing
(r"(?i)(water\s*charges?|coal|fuel|lpg|gas\s*charges?)", "manufacturing_expense"),

# Security charges route
(r"(?i)(security\s*(service\s*)?charges?|watchman|guard)", "manufacturing_expense"),
```

---

### TASK 4: Expand `SECTION_NORMALIZED_TO_CANONICAL` in scoped_classifier.py

Currently, `finance_cost` only maps to `"Operating Statement - Finance Charges"`. But bank charges (R85) is in that section, and the routing fix above will send more items to `finance_cost`. Verify this section contains rows 83-91 (all finance rows). If not, no change needed — the canonical_labels.json section should already have them.

Also verify that `employee_cost` maps to both Manufacturing Expenses (for R45 Wages) and Admin & Selling (for R67 Salary). This is already the case at lines 70-73:
```python
"employee_cost": [
    "Operating Statement - Manufacturing Expenses",
    "Operating Statement - Admin & Selling Expenses",
],
```
This is correct — no change needed.

---

### TASK 5: Update `cma_classification_rules.json`

This file provides "CA EXPERT RULES" in the AI prompt. Add/fix these entries:

```json
[
  {
    "rule_id": "CA_R01",
    "source_sheet": "P&L",
    "fs_item": "Staff Welfare Expenses",
    "cma_classification_text": "Manufacturing: Row 45 Wages; Trading/Services: Row 67 Salary",
    "broad_classification": "Employee Cost",
    "remarks": "Industry-dependent. CA-verified 2026-03-26.",
    "canonical_sheet_row": 45,
    "canonical_code": "II_M5",
    "canonical_name": "Wages",
    "mapping_confidence": "certain",
    "mapping_notes": "For manufacturing/construction. Trading/services → R67."
  },
  {
    "rule_id": "CA_R02",
    "source_sheet": "P&L",
    "fs_item": "Gratuity",
    "cma_classification_text": "Item 5: Wages (Manufacturing Expenses)",
    "broad_classification": "Manufacturing Expense",
    "remarks": "Always R45 regardless of industry. CA-verified 2026-03-26.",
    "canonical_sheet_row": 45,
    "canonical_code": "II_M5",
    "canonical_name": "Wages",
    "mapping_confidence": "certain",
    "mapping_notes": ""
  },
  {
    "rule_id": "CA_R03",
    "source_sheet": "P&L",
    "fs_item": "Directors Remuneration",
    "cma_classification_text": "Item 33: Audit Fees & Directors Remuneration",
    "broad_classification": "Admin Expense",
    "remarks": "R73 NOT R67. CA overrode AI. CA-verified 2026-03-26.",
    "canonical_sheet_row": 73,
    "canonical_code": "II_A7",
    "canonical_name": "Audit Fees & Directors Remuneration",
    "mapping_confidence": "certain",
    "mapping_notes": ""
  },
  {
    "rule_id": "CA_R04",
    "source_sheet": "P&L",
    "fs_item": "Liquidated Damages",
    "cma_classification_text": "Item 31: Others (Admin & Selling)",
    "broad_classification": "Admin Expense",
    "remarks": "R71 NOT R83. CA overrode AI. CA-verified 2026-03-26.",
    "canonical_sheet_row": 71,
    "canonical_code": "II_A5",
    "canonical_name": "Others (Admin)",
    "mapping_confidence": "certain",
    "mapping_notes": ""
  },
  {
    "rule_id": "CA_R05",
    "source_sheet": "P&L",
    "fs_item": "Loan Processing Fee",
    "cma_classification_text": "Item 45: Bank Charges",
    "broad_classification": "Finance Cost",
    "remarks": "R85 NOT R84. CA overrode AI. CA-verified 2026-03-26.",
    "canonical_sheet_row": 85,
    "canonical_code": "II_F3",
    "canonical_name": "Bank Charges",
    "mapping_confidence": "certain",
    "mapping_notes": ""
  },
  {
    "rule_id": "CA_R06",
    "source_sheet": "P&L",
    "fs_item": "Licence & Subscription Fees",
    "cma_classification_text": "Item 31: Others (Admin & Selling)",
    "broad_classification": "Admin Expense",
    "remarks": "R71 NOT R68. CA overrode AI. CA-verified 2026-03-26.",
    "canonical_sheet_row": 71,
    "canonical_code": "II_A5",
    "canonical_name": "Others (Admin)",
    "mapping_confidence": "certain",
    "mapping_notes": ""
  },
  {
    "rule_id": "CA_R07",
    "source_sheet": "P&L",
    "fs_item": "Insurance Premium",
    "cma_classification_text": "Item 31: Others (Admin & Selling)",
    "broad_classification": "Admin Expense",
    "remarks": "R71 NOT R49. CA overrode AI. CA-verified 2026-03-26.",
    "canonical_sheet_row": 71,
    "canonical_code": "II_A5",
    "canonical_name": "Others (Admin)",
    "mapping_confidence": "certain",
    "mapping_notes": ""
  },
  {
    "rule_id": "CA_R08",
    "source_sheet": "Balance Sheet",
    "fs_item": "Vehicle HP Current Maturities",
    "cma_classification_text": "Item 52: Repayable in next one year (Other Debts)",
    "broad_classification": "Current Liability",
    "remarks": "R148 NOT R140. CA overrode AI. CA-verified 2026-03-26.",
    "canonical_sheet_row": 148,
    "canonical_code": "III_L8a",
    "canonical_name": "Repayable in next one year",
    "mapping_confidence": "certain",
    "mapping_notes": ""
  },
  {
    "rule_id": "CA_R09",
    "source_sheet": "Balance Sheet",
    "fs_item": "Advances to Suppliers",
    "cma_classification_text": "Row 220: Advance to suppliers of Raw Materials",
    "broad_classification": "Current Assets",
    "remarks": "R220 NOT R219. CA overrode AI. CA-verified 2026-03-26.",
    "canonical_sheet_row": 220,
    "canonical_code": "III_A10b",
    "canonical_name": "Advance to suppliers of Raw Materials and stores etc.",
    "mapping_confidence": "certain",
    "mapping_notes": ""
  },
  {
    "rule_id": "CA_R10",
    "source_sheet": "P&L",
    "fs_item": "Opening Stock Finished Goods",
    "cma_classification_text": "Row 58: Finished Goods Opening Balance",
    "broad_classification": "Manufacturing Expense",
    "remarks": "R58 NOT R57. CA overrode AI. CA-verified 2026-03-26.",
    "canonical_sheet_row": 58,
    "canonical_code": "II_M10a",
    "canonical_name": "Finished Goods Opening Balance",
    "mapping_confidence": "certain",
    "mapping_notes": ""
  },
  {
    "rule_id": "CA_R11",
    "source_sheet": "P&L",
    "fs_item": "Row 75 Usage",
    "cma_classification_text": "Row 75 is ONLY for non-cash write-offs",
    "broad_classification": "Admin Expense",
    "remarks": "Preliminary/pre-operative expense amortisation ONLY. Regular 'Miscellaneous Expenses' → R71. CA-verified 2026-03-26.",
    "canonical_sheet_row": 75,
    "canonical_code": "II_A9",
    "canonical_name": "Miscellaneous Expenses Written off",
    "mapping_confidence": "certain",
    "mapping_notes": "Non-cash expenditure only"
  },
  {
    "rule_id": "CA_R12",
    "source_sheet": "P&L",
    "fs_item": "Subsidy / Government Grant",
    "cma_classification_text": "P&L: Row 33 Extraordinary Income; BS: Row 125 Other Reserves",
    "broad_classification": "Context-dependent",
    "remarks": "CA-verified 2026-03-26.",
    "canonical_sheet_row": 33,
    "canonical_code": "II_NI4",
    "canonical_name": "Extraordinary income",
    "mapping_confidence": "certain",
    "mapping_notes": "P&L context. BS context → R125."
  },
  {
    "rule_id": "CA_R13",
    "source_sheet": "P&L",
    "fs_item": "Stores & Spares (Imported)",
    "cma_classification_text": "Row 43: Stores and spares consumed (Imported)",
    "broad_classification": "Manufacturing Expense",
    "remarks": "Only if 'imported' keyword present. Otherwise R44. CA-verified 2026-03-26.",
    "canonical_sheet_row": 43,
    "canonical_code": "II_M3",
    "canonical_name": "Stores and spares consumed (Imported)",
    "mapping_confidence": "certain",
    "mapping_notes": ""
  }
]
```

---

### TASK 6: Add Training Data Examples to `training_data.json`

Add these CA-verified examples for fuzzy matching. Format must match existing entries:

```json
[
  {"text": "Staff Welfare Expenses", "label": 45, "label_name": "Wages", "source": "CA-verified-2026-03-26", "industry": "manufacturing"},
  {"text": "Staff Welfare Expenses", "label": 67, "label_name": "Salary and staff expenses", "source": "CA-verified-2026-03-26", "industry": "trading"},
  {"text": "Gratuity to Employees", "label": 45, "label_name": "Wages", "source": "CA-verified-2026-03-26"},
  {"text": "Contribution to EPF", "label": 45, "label_name": "Wages", "source": "CA-verified-2026-03-26"},
  {"text": "Contribution to ESI", "label": 45, "label_name": "Wages", "source": "CA-verified-2026-03-26"},
  {"text": "Directors Remuneration", "label": 73, "label_name": "Audit Fees & Directors Remuneration", "source": "CA-verified-2026-03-26"},
  {"text": "Liquidated Damages", "label": 71, "label_name": "Others (Admin)", "source": "CA-verified-2026-03-26"},
  {"text": "Loan Processing Fee", "label": 85, "label_name": "Bank Charges", "source": "CA-verified-2026-03-26"},
  {"text": "Vehicle HP Current Maturities", "label": 148, "label_name": "Repayable in next one year", "source": "CA-verified-2026-03-26"},
  {"text": "Licence & Subscription", "label": 71, "label_name": "Others (Admin)", "source": "CA-verified-2026-03-26"},
  {"text": "Insurance Premium", "label": 71, "label_name": "Others (Admin)", "source": "CA-verified-2026-03-26"},
  {"text": "Advances to Suppliers", "label": 220, "label_name": "Advance to suppliers of Raw Materials", "source": "CA-verified-2026-03-26"},
  {"text": "Security Deposits Paid", "label": 238, "label_name": "Other non current assets", "source": "CA-verified-2026-03-26"},
  {"text": "Carriage Outward", "label": 70, "label_name": "Advertisements and Sales Promotions", "source": "CA-verified-2026-03-26"},
  {"text": "Brokerage and Commission", "label": 70, "label_name": "Advertisements and Sales Promotions", "source": "CA-verified-2026-03-26"},
  {"text": "Selling and Distribution Expenses", "label": 70, "label_name": "Advertisements and Sales Promotions", "source": "CA-verified-2026-03-26"},
  {"text": "Miscellaneous Expenses", "label": 71, "label_name": "Others (Admin)", "source": "CA-verified-2026-03-26"},
  {"text": "Administrative & General Expenses", "label": 71, "label_name": "Others (Admin)", "source": "CA-verified-2026-03-26"}
]
```

**NOTE:** Check the existing training_data.json format first. If it has additional fields (like `section`, `industry_type`, etc.), match that format.

---

### TASK 7: Formula Cell Exclusion

BS inventory rows R200 and R201 are formula cells (`=CXX`) in the CMA Excel template. The classifier must NEVER target these rows.

**CA Answer (Q8a, Q8b):**
- Q8a: WIP in BS → "Shouldn't be touched" (R200 is formula)
- Q8b: Finished Goods in BS → "not to be touched" (R201 is formula)

**Implementation approach:**

1. In `scoped_classifier.py`, add a `FORMULA_ROWS` set:
```python
# Rows in CMA.xlsm that are formula cells — NEVER classify into these
FORMULA_ROWS = {200, 201}  # BS Inventories: =CXX formulas
```

2. In `_build_prompt()`, filter these rows out of the `context.cma_rows` before building the prompt:
```python
# Filter out formula rows — these are auto-calculated, not classified
filtered_rows = [r for r in context.cma_rows if r["sheet_row"] not in FORMULA_ROWS]
```

3. In `canonical_labels.json`, consider adding a `"formula": true` flag to rows 200 and 201 so they're excluded upstream. But the simpler approach above is sufficient.

**IMPORTANT:** There may be MORE formula rows beyond R200/R201. Check the CMA.xlsm template (`DOCS/CMA.xlsm`) for all rows with `=CXX` formulas and add them ALL to `FORMULA_ROWS`. Common candidates:
- Total rows (subtotals, grand totals)
- Computed ratios
- Net values derived from gross - deductions

For V1, at minimum exclude R200 and R201 as confirmed by the CA. A comprehensive formula audit can follow.

---

### TASK 8: Rule Ordering in rule_engine.py

The new CA rules need to be placed carefully to avoid conflicts with existing rules. Recommended placement:

```
PHASE 1 (C-type absolute): existing rules + CA-023 (bonus shares → doubt)
↓
NEW PHASE 1.5 (CA employee rules):
  CA-008 (salary+wages+bonus combined → R45) — MUST be before generic patterns
  CA-004 (gratuity → R45)
  CA-005 (EPF → R45)
  CA-006 (ESI → R45)
  CA-007 (staff mess → R45)
  CA-009 (labour charges → R45)
  CA-001 (staff welfare → industry-dep)
  CA-002 (standalone bonus → industry-dep)
  CA-003 (employee benefits → industry-dep)
  CA-010 (leave encashment → context-dep)
↓
PHASE 2 (Industry-specific): existing rules + CA-011 (power/electric)
↓
PHASE 3 (Interest): existing rules + CA-012 (interest tax delay), CA-014 (loan processing fee)
↓
NEW PHASE 3.5 (CA finance/admin):
  CA-013 (liquidated damages → R71)
  CA-019 (licence/subscription → R71)
  CA-020 (insurance → R71)
  CA-024 (preliminary expense write-off → R75)
  CA-021 (subsidy/grant → context-dep)
  CA-022 (stores & spares → import check)
↓
PHASE 4-6: existing rules (check for conflicts)
↓
PHASE 7 (Remuneration): BCIPL-001 now routes to R73 (TASK 1 fix)
↓
NEW PHASE 7.5 (CA balance sheet):
  CA-015 (vehicle HP current → R148)
  CA-016 (other LT liability → R149)
  CA-017 (advances to suppliers → R220)
  CA-018 (security deposits generic → R238)
↓
PHASE 8-9: existing rules
```

---

### TASK 9: Verify No Conflicts with Existing Rules

Before implementing, check these potential conflicts:

1. **Gratuity (CA-004) vs MSL-003:** MSL-003 handles "Provision for Gratuity" in long-term BS section → R153. CA-004 handles "Gratuity" as P&L expense → R45. These are different items — ensure regex patterns don't overlap. MSL-003's pattern is `\bprovision\s*(for\s*)?gratuity\b` — CA-004 should use `\bgratuity\b` but NOT match "provision for gratuity". Add negative lookahead: `(?<!provision\s{1,5}(for\s{1,5})?)gratuity` or simply check the MSL-003 pattern first (it's already in PHASE 6, before PHASE 7).

2. **Insurance (CA-020) vs MSL-008:** MSL-008's `_ADMIN_CATCHALL_TERMS` includes `insurance`. CA-020 should catch insurance BEFORE MSL-008. Both route to R71, so no functional conflict — but having a specific rule is better for audit trail.

3. **Labour Charges (CA-009) vs SSSS-003:** SSSS-003 catches "cutting/slitting labour charges" → R46. CA-009 catches generic "labour charges" → R45. SSSS-003 is more specific and runs first — correct ordering.

4. **Stores & Spares (CA-022) vs BCIPL-002:** BCIPL-002 catches "scrap/other materials consumed" → R44. CA-022 catches "stores, spares" → R44/R43. Different patterns — no conflict.

5. **Security Deposits (CA-018) vs C-004-govt/C-004-private:** C-004 rules are more specific (government vs private). CA-018 is a generic fallback for unqualified "security deposit" items. Must run AFTER both C-004 rules.

---

### TASK 10: Add AI Prompt Enhancement

In `_build_prompt()` (scoped_classifier.py), add these disambiguation rules to the IMPORTANT RULES section:

```python
# Add after the existing IMPORTANT RULES section:
"""
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
"""
```

---

## Verification Plan

After implementing all changes:

### Step 1: Run existing tests
```bash
docker compose exec backend pytest backend/tests/ -v
```
All tests must pass. Fix any broken tests (they may assert old wrong behavior — update assertions to match CA answers).

### Step 2: Run accuracy test on BCIPL
```bash
docker compose exec backend python run_accuracy_bcipl.py
```
Compare accuracy before and after. Expect improvement on:
- Employee cost items (Staff Welfare, Bonus, Gratuity, EPF, ESI)
- Finance items (Bank Charges, Loan Processing Fee)
- Directors Remuneration
- Carriage Outward, Selling & Distribution

### Step 3: Run full 9-company accuracy test
```bash
docker compose exec backend python run_accuracy_test.py
```
Measure overall accuracy improvement. Target: >90% (from current ~85-87% baseline).

### Step 4: Spot-check specific CA answers
For each of these items, verify the system now classifies correctly:
- "Staff Welfare Expenses" + industry=manufacturing → R45
- "Staff Welfare Expenses" + industry=trading → R67
- "Directors Remuneration" → R73
- "Liquidated Damages" → R71
- "Bank Charges" → R85
- "Loan Processing Fee" → R85
- "Licence Fees" → R71
- "Insurance Premium" → R71
- "Vehicle HP Current Maturities" → R148
- "Advances to Suppliers" → R220

---

## Summary of All Changes

| # | File | Change | CA Source |
|---|------|--------|-----------|
| 1 | rule_engine.py | Fix BCIPL-001: Directors Remuneration R67→R73 | Q21a |
| 2 | rule_engine.py | Add CA-001 to CA-003: Industry-dep employee rules | Q1a,Q1g,Q1i |
| 3 | rule_engine.py | Add CA-004 to CA-009: Universal employee→R45 rules | Q1b-Q1e,Q1h,Q1j |
| 4 | rule_engine.py | Add CA-010: Leave Encashment context-dep | Q1f |
| 5 | rule_engine.py | Add CA-011: Power/Electric industry-dep | Q12a |
| 6 | rule_engine.py | Add CA-012: Interest on tax delay→R84 | Q10b |
| 7 | rule_engine.py | Add CA-013: Liquidated Damages→R71 | Q10d |
| 8 | rule_engine.py | Add CA-014: Loan Processing Fee→R85 | Q10g |
| 9 | rule_engine.py | Add CA-015: Vehicle HP Current→R148 | Q17 |
| 10 | rule_engine.py | Add CA-016: Other LT Liability→R149 | Q20 |
| 11 | rule_engine.py | Add CA-017: Advances to Suppliers→R220 | Q33 |
| 12 | rule_engine.py | Add CA-018: Security Deposits→R238 | Q35 |
| 13 | rule_engine.py | Add CA-019: Licence/Subscription→R71 | Q3f |
| 14 | rule_engine.py | Add CA-020: Insurance→R71 | Q22 |
| 15 | rule_engine.py | Add CA-021: Subsidy/Grant context-dep | Q38 |
| 16 | rule_engine.py | Add CA-022: Stores & Spares import check | Q12g |
| 17 | rule_engine.py | Add CA-023: Bonus Shares→doubt | Q15 |
| 18 | rule_engine.py | Add CA-024: Preliminary expense→R75 | Q32 |
| 19 | scoped_classifier.py | Fix `_KEYWORD_ROUTES` admin_expense regex | Interview |
| 20 | scoped_classifier.py | Add FORMULA_ROWS exclusion | Q8a,Q8b |
| 21 | scoped_classifier.py | Add disambiguation rules to prompt | All |
| 22 | cma_classification_rules.json | Add 13 CA expert rules | All |
| 23 | training_data.json | Add 18 CA-verified examples | All |

**Total:** 23 discrete changes across 4 files.

---

## General Rules Confirmed by CA (apply across all tasks)

These are from the `general_rules` section of the CA answers JSON:

1. **Q2 — Industry-based routing:** "This is very true" — manufacturing items under manufacturing section → R45, admin section → R67. Confirmed.
2. **Q4 — Row 75 is non-cash only:** "Row 75 is a non cash expenditure, AI suggestion is very right." Regular Miscellaneous Expenses → R71.
3. **Q9 — P&L vs BS stock:** "It is correct." P&L context → rows 53-59. BS context → rows 200-201 (but these are formula cells, don't classify).
4. **Q11 — Forex:** "AI suggestion is spot on." Forex Loss → R91, Forex Gain → R32.
5. **Q13 — Nature vs Section:** Confidence "depends" — situational.
6. **Q41 — Nature vs Section (follow-up):** "Go by nature." Confidence "usually." Classify by what the item IS, not where it appears.
7. **Q42 — Trading companies use manufacturing rows:** "It is certainly true." Confidence "certain." Manufacturing rows R41-R59 apply to trading companies too (for cost of goods).

---

## Starting Point

Read these files before making any changes:
1. `DOCS/ca_answers_2026-03-26.json` — the golden rule
2. `backend/app/services/classification/rule_engine.py` — full file
3. `backend/app/services/classification/scoped_classifier.py` — full file
4. `CMA_Ground_Truth_v1/reference/cma_classification_rules.json` — full file
5. `CMA_Ground_Truth_v1/database/training_data.json` — check format
6. `backend/app/mappings/cma_field_rows.py` — verify all needed field names exist

Begin with TASK 1 (simplest fix), then TASK 2 (bulk of new rules), then TASK 3-7, then TASK 8 (ordering verification), then TASK 9 (conflict check), then TASK 10 (prompt enhancement). Run tests after each major task group.
