# CA-Verified Classification Answers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply 23 CA-verified classification fixes to the CMA system — adding 24 new deterministic rules to the rule engine, fixing `_KEYWORD_ROUTES`, adding FORMULA_ROWS exclusion, and enriching the AI prompt + JSON data files.

**Architecture:** Rule engine (Tier 0) gets 24 new patterns in careful priority order. Scoped classifier (Tier 2) gets routing and prompt improvements. JSON data files get 13 new CA expert rules and 18 training examples.

**Tech Stack:** Python regex, FastAPI, `CMA_Ground_Truth_v1/` JSON files

**Source of Truth:** `DOCS/ca_answers_2026-03-26.json` — CA professional judgment, never override.

---

## CRITICAL: Field Name Lookup Table

The `_match()` helper calls `ALL_FIELD_TO_ROW[field_name]` — any mismatch raises `KeyError`. Use these EXACT strings:

| CA Rule | Correct `field_name` in `_match()` | Row |
|---------|-----------------------------------|-----|
| CA-001 to CA-010 (manufacturing) | `"Wages"` | 45 |
| CA-001 to CA-003 (services) | `"Salary and staff expenses"` | 67 |
| CA-010-bs | `"Creditors for Expenses"` | 249 |
| CA-011-mfg | `"Power, Coal, Fuel and Water"` | 48 |
| CA-011-svc | `"Others (Admin)"` | 71 |
| CA-012 | `"Interest on Working capital loans"` | 84 |
| CA-013, CA-019, CA-020 | `"Others (Admin)"` | 71 |
| CA-014 | `"Bank Charges"` | 85 |
| CA-015 | `"Other Debts Repayable in Next One year"` | 148 |
| CA-016 | `"Balance Other Debts"` | 149 |
| CA-017 | `"Advances to suppliers of raw materials"` | 220 |
| CA-018 | `"Other non current assets"` | 238 |
| CA-021-pl | `"Extraordinary income"` | 33 |
| CA-021-bs | `"Other Reserve"` | 125 |
| CA-022-imp | `"Stores and spares consumed (Imported)"` | 43 |
| CA-022-ind | `"Stores and spares consumed (Indigenous)"` | 44 |
| CA-024 | `"Miscellaneous Expenses written off"` | 75 |
| BCIPL-001 fix | `"Audit Fees & Directors Remuneration"` | 73 |

---

## File Map

| File | Change Type |
|------|-------------|
| `backend/app/services/classification/rule_engine.py` | Modify — fix BCIPL-001, add 24 new rules + patterns + helpers |
| `backend/app/services/classification/scoped_classifier.py` | Modify — fix `_KEYWORD_ROUTES`, add `FORMULA_ROWS`, add prompt disambiguation |
| `CMA_Ground_Truth_v1/reference/cma_classification_rules.json` | Modify — add 13 CA expert rule entries |
| `CMA_Ground_Truth_v1/database/training_data.json` | Modify — add 18 CA-verified training examples |
| `backend/tests/test_rule_engine.py` | **Create** — new test file for CA rules (TDD first) |

---

## Task 1: Write Failing Tests for CA Rules

**Files:**
- Create: `backend/tests/test_rule_engine.py`

- [ ] **Step 1.1: Create the test file**

```python
"""Tests for CA-verified classification rules in rule_engine.py.

Written BEFORE implementation (TDD red phase).
CA source: DOCS/ca_answers_2026-03-26.json
Date: 2026-03-26
"""
import pytest
from app.services.classification.rule_engine import RuleEngine


@pytest.fixture
def engine():
    return RuleEngine()


# ── BCIPL-001 fix: Directors Remuneration → R73 (was R67) ────────────────────

class TestBCIPL001Fix:
    def test_directors_remuneration_goes_to_r73(self, engine):
        result = engine.apply("Directors Remuneration", None, None, "manufacturing")
        assert result is not None
        assert result.cma_row == 73
        assert result.rule_id == "BCIPL-001"

    def test_managing_director_salary_goes_to_r73(self, engine):
        result = engine.apply("Managing Director Salary", None, None, "services")
        assert result is not None
        assert result.cma_row == 73

    def test_kmp_remuneration_goes_to_r73(self, engine):
        result = engine.apply("KMP Remuneration", None, None, "manufacturing")
        assert result is not None
        assert result.cma_row == 73


# ── CA-008: Combined "Salary, Wages and Bonus" → R45 always ──────────────────

class TestCA008CombinedSalaryWagesBonuse:
    def test_salary_wages_bonus_combined_always_r45(self, engine):
        result = engine.apply("Salary, Wages and Bonus", None, None, "trading")
        assert result is not None
        assert result.cma_row == 45
        assert result.rule_id == "CA-008"

    def test_salaries_and_wages_combined_r45(self, engine):
        result = engine.apply("Salaries and Wages", None, None, "services")
        assert result is not None
        assert result.cma_row == 45
        assert result.rule_id == "CA-008"


# ── CA-004: Gratuity → always R45 ────────────────────────────────────────────

class TestCA004Gratuity:
    def test_gratuity_expense_pl_r45(self, engine):
        result = engine.apply("Gratuity to Employees", None, "expenses", "manufacturing")
        assert result is not None
        assert result.cma_row == 45
        assert result.rule_id == "CA-004"

    def test_gratuity_services_also_r45(self, engine):
        result = engine.apply("Gratuity", None, "expenses", "services")
        assert result is not None
        assert result.cma_row == 45

    def test_provision_for_gratuity_NOT_r45(self, engine):
        # MSL-003 handles BS provision separately → R153
        result = engine.apply("Provision for Gratuity", None, "long term provisions", "manufacturing")
        # Should NOT be CA-004 (R45); MSL-003 should catch it first
        assert result is None or result.cma_row == 153


# ── CA-005: EPF → always R45 ─────────────────────────────────────────────────

class TestCA005EPF:
    def test_epf_contribution_r45(self, engine):
        result = engine.apply("Contribution to EPF", None, None, "manufacturing")
        assert result is not None
        assert result.cma_row == 45
        assert result.rule_id == "CA-005"

    def test_provident_fund_r45(self, engine):
        result = engine.apply("Provident Fund Contribution", None, None, "trading")
        assert result is not None
        assert result.cma_row == 45


# ── CA-006: ESI → always R45 ─────────────────────────────────────────────────

class TestCA006ESI:
    def test_esi_contribution_r45(self, engine):
        result = engine.apply("Contribution to ESI", None, None, "manufacturing")
        assert result is not None
        assert result.cma_row == 45
        assert result.rule_id == "CA-006"

    def test_esic_r45(self, engine):
        result = engine.apply("ESIC Contribution", None, None, "services")
        assert result is not None
        assert result.cma_row == 45


# ── CA-007: Staff Mess → always R45 ──────────────────────────────────────────

class TestCA007StaffMess:
    def test_staff_mess_r45(self, engine):
        result = engine.apply("Staff Mess Expenses", None, None, "manufacturing")
        assert result is not None
        assert result.cma_row == 45
        assert result.rule_id == "CA-007"

    def test_canteen_expense_r45(self, engine):
        result = engine.apply("Canteen Expenses", None, None, "services")
        assert result is not None
        assert result.cma_row == 45


# ── CA-009: Labour Charges → always R45 ──────────────────────────────────────

class TestCA009LabourCharges:
    def test_labour_charges_r45(self, engine):
        result = engine.apply("Labour Charges Paid", None, None, "manufacturing")
        assert result is not None
        assert result.cma_row == 45
        assert result.rule_id == "CA-009"

    def test_labor_charges_r45(self, engine):
        # US spelling
        result = engine.apply("Labor Charges", None, None, "services")
        assert result is not None
        assert result.cma_row == 45


# ── CA-001: Staff Welfare → industry-dependent ───────────────────────────────

class TestCA001StaffWelfare:
    def test_staff_welfare_manufacturing_r45(self, engine):
        result = engine.apply("Staff Welfare Expenses", None, None, "manufacturing")
        assert result is not None
        assert result.cma_row == 45
        assert result.rule_id == "CA-001-mfg"

    def test_staff_welfare_construction_r45(self, engine):
        result = engine.apply("Staff Welfare Expenses", None, None, "construction")
        assert result is not None
        assert result.cma_row == 45

    def test_staff_welfare_trading_r67(self, engine):
        result = engine.apply("Staff Welfare Expenses", None, None, "trading")
        assert result is not None
        assert result.cma_row == 67
        assert result.rule_id == "CA-001-svc"

    def test_staff_welfare_services_r67(self, engine):
        result = engine.apply("Staff Welfare Expenses", None, None, "services")
        assert result is not None
        assert result.cma_row == 67


# ── CA-002: Standalone Bonus → industry-dependent ────────────────────────────

class TestCA002Bonus:
    def test_bonus_manufacturing_r45(self, engine):
        result = engine.apply("Bonus to Workers", None, None, "manufacturing")
        assert result is not None
        assert result.cma_row == 45
        assert result.rule_id == "CA-002-mfg"

    def test_bonus_services_r67(self, engine):
        result = engine.apply("Bonus", None, None, "services")
        assert result is not None
        assert result.cma_row == 67
        assert result.rule_id == "CA-002-svc"


# ── CA-003: Employee Benefits → industry-dependent ───────────────────────────

class TestCA003EmployeeBenefits:
    def test_employee_benefits_manufacturing_r45(self, engine):
        result = engine.apply("Employee Benefits Expense", None, None, "manufacturing")
        assert result is not None
        assert result.cma_row == 45
        assert result.rule_id == "CA-003-mfg"

    def test_employee_benefits_trading_r67(self, engine):
        result = engine.apply("Employee Benefits Expense", None, None, "trading")
        assert result is not None
        assert result.cma_row == 67
        assert result.rule_id == "CA-003-svc"


# ── CA-010: Leave Encashment → context-dependent ─────────────────────────────

class TestCA010LeaveEncashment:
    def test_leave_encashment_pl_context_r45(self, engine):
        result = engine.apply("Leave Encashment", None, "employee expenses", "manufacturing")
        assert result is not None
        assert result.cma_row == 45
        assert result.rule_id == "CA-010-pl"

    def test_leave_salary_pl_r45(self, engine):
        result = engine.apply("Leave Salary", None, "expenses", "services")
        assert result is not None
        assert result.cma_row == 45

    def test_leave_encashment_bs_context_r249(self, engine):
        result = engine.apply("Leave Encashment", None, "current liabilities", "manufacturing")
        assert result is not None
        assert result.cma_row == 249
        assert result.rule_id == "CA-010-bs"


# ── CA-011: Power/Electric → industry-dependent ──────────────────────────────

class TestCA011PowerElectric:
    def test_electricity_charges_manufacturing_r48(self, engine):
        result = engine.apply("Electricity Charges", None, None, "manufacturing")
        assert result is not None
        assert result.cma_row == 48
        assert result.rule_id == "CA-011-mfg"

    def test_power_charges_construction_r48(self, engine):
        result = engine.apply("Power Charges", None, None, "construction")
        assert result is not None
        assert result.cma_row == 48

    def test_electricity_expense_trading_r71(self, engine):
        result = engine.apply("Electricity Expense", None, None, "trading")
        assert result is not None
        assert result.cma_row == 71
        assert result.rule_id == "CA-011-svc"

    def test_electricity_deposit_not_matched(self, engine):
        # C-004-govt already handles this as security deposit → R237
        result = engine.apply("Electricity Deposit", None, None, "manufacturing")
        assert result is not None
        assert result.cma_row == 237  # not CA-011


# ── CA-012: Interest on tax delay → R84 ──────────────────────────────────────

class TestCA012InterestTaxDelay:
    def test_interest_on_tax_delay_r84(self, engine):
        result = engine.apply("Interest on Delay in Payment of Taxes", None, None, "manufacturing")
        assert result is not None
        assert result.cma_row == 84
        assert result.rule_id == "CA-012"

    def test_interest_on_income_tax_r84(self, engine):
        result = engine.apply("Interest on Income Tax", None, None, "services")
        assert result is not None
        assert result.cma_row == 84


# ── CA-013: Liquidated Damages → R71 ─────────────────────────────────────────

class TestCA013LiquidatedDamages:
    def test_liquidated_damages_r71(self, engine):
        result = engine.apply("Liquidated Damages", None, None, "manufacturing")
        assert result is not None
        assert result.cma_row == 71
        assert result.rule_id == "CA-013"


# ── CA-014: Loan Processing Fee → R85 ────────────────────────────────────────

class TestCA014LoanProcessingFee:
    def test_loan_processing_fee_r85(self, engine):
        result = engine.apply("Loan Processing Fee", None, None, "manufacturing")
        assert result is not None
        assert result.cma_row == 85
        assert result.rule_id == "CA-014"

    def test_processing_charges_loan_r85(self, engine):
        result = engine.apply("Processing Charges on Loan", None, None, "trading")
        assert result is not None
        assert result.cma_row == 85


# ── CA-015: Vehicle HP Current Maturities → R148 ─────────────────────────────

class TestCA015VehicleHP:
    def test_vehicle_hp_current_maturities_r148(self, engine):
        result = engine.apply("Vehicle HP Current Maturities", None, "current liabilities", "manufacturing")
        assert result is not None
        assert result.cma_row == 148
        assert result.rule_id == "CA-015"

    def test_hp_instalments_due_r148(self, engine):
        result = engine.apply("HP Instalments Due within one year", None, "liabilities", "trading")
        assert result is not None
        assert result.cma_row == 148


# ── CA-016: Other Long Term Liabilities → R149 ───────────────────────────────

class TestCA016OtherLTLiability:
    def test_other_long_term_liabilities_r149(self, engine):
        result = engine.apply("Other Long Term Liabilities", None, "non-current liabilities", "manufacturing")
        assert result is not None
        assert result.cma_row == 149
        assert result.rule_id == "CA-016"


# ── CA-017: Advances to Suppliers → R220 ─────────────────────────────────────

class TestCA017AdvancesToSuppliers:
    def test_advances_to_suppliers_r220(self, engine):
        result = engine.apply("Advances to Suppliers", None, "current assets", "manufacturing")
        assert result is not None
        assert result.cma_row == 220
        assert result.rule_id == "CA-017"

    def test_advance_paid_to_suppliers_r220(self, engine):
        result = engine.apply("Advance Paid to Suppliers", None, None, "trading")
        assert result is not None
        assert result.cma_row == 220


# ── CA-018: Security Deposits (generic) → R238 ───────────────────────────────

class TestCA018SecurityDeposit:
    def test_generic_security_deposit_r238(self, engine):
        result = engine.apply("Security Deposits Paid", None, "non-current assets", "manufacturing")
        assert result is not None
        assert result.cma_row == 238
        assert result.rule_id == "CA-018"

    def test_govt_deposit_still_r237(self, engine):
        # C-004-govt runs first → R237
        result = engine.apply("Electricity Deposit", None, None, "manufacturing")
        assert result is not None
        assert result.cma_row == 237

    def test_private_deposit_still_r238(self, engine):
        # C-004-private runs first
        result = engine.apply("Security Deposit with Landlord", None, None, "manufacturing")
        assert result is not None
        assert result.cma_row == 238


# ── CA-019: Licence & Subscription → R71 ─────────────────────────────────────

class TestCA019Licence:
    def test_licence_fee_r71(self, engine):
        result = engine.apply("Licence Fee", None, None, "services")
        assert result is not None
        assert result.cma_row == 71
        assert result.rule_id == "CA-019"

    def test_subscription_expense_r71(self, engine):
        result = engine.apply("Subscription Charges", None, None, "trading")
        assert result is not None
        assert result.cma_row == 71


# ── CA-020: Insurance → R71 ──────────────────────────────────────────────────

class TestCA020Insurance:
    def test_insurance_premium_r71(self, engine):
        result = engine.apply("Insurance Premium", None, None, "manufacturing")
        assert result is not None
        assert result.cma_row == 71
        assert result.rule_id == "CA-020"

    def test_insurance_charges_r71(self, engine):
        result = engine.apply("Insurance Charges", None, None, "trading")
        assert result is not None
        assert result.cma_row == 71


# ── CA-021: Subsidy/Grant → context-dependent ────────────────────────────────

class TestCA021Subsidy:
    def test_subsidy_pl_context_r33(self, engine):
        result = engine.apply("Capital Subsidy Received", None, "other income", "manufacturing")
        assert result is not None
        assert result.cma_row == 33
        assert result.rule_id == "CA-021-pl"

    def test_govt_grant_bs_context_r125(self, engine):
        result = engine.apply("Government Grant", None, "reserves and surplus", "manufacturing")
        assert result is not None
        assert result.cma_row == 125
        assert result.rule_id == "CA-021-bs"


# ── CA-022: Stores & Spares → import check ───────────────────────────────────

class TestCA022StoresSpares:
    def test_stores_spares_indigenous_r44(self, engine):
        result = engine.apply("Stores and Spares Consumed", None, None, "manufacturing")
        assert result is not None
        assert result.cma_row == 44
        assert result.rule_id == "CA-022-ind"

    def test_stores_spares_imported_r43(self, engine):
        result = engine.apply("Stores and Spares Consumed (Imported)", None, None, "manufacturing")
        assert result is not None
        assert result.cma_row == 43
        assert result.rule_id == "CA-022-imp"


# ── CA-023: Bonus Shares → always doubt ──────────────────────────────────────

class TestCA023BonusShares:
    def test_issue_of_bonus_shares_forces_doubt(self, engine):
        result = engine.apply("Issue of Bonus Shares", None, None, "manufacturing")
        assert result is not None
        assert result.confidence == 0.0
        assert result.rule_id == "CA-023"

    def test_bonus_share_allotment_forces_doubt(self, engine):
        result = engine.apply("Bonus Shares Issued", None, None, "manufacturing")
        assert result is not None
        assert result.confidence == 0.0


# ── CA-024: Preliminary Expense Write-off → R75 ──────────────────────────────

class TestCA024PreliminaryExpense:
    def test_preliminary_expense_written_off_r75(self, engine):
        result = engine.apply("Preliminary Expenses Written Off", None, None, "manufacturing")
        assert result is not None
        assert result.cma_row == 75
        assert result.rule_id == "CA-024"

    def test_pre_operative_expenses_r75(self, engine):
        result = engine.apply("Pre-Operative Expenses Amortised", None, None, "manufacturing")
        assert result is not None
        assert result.cma_row == 75

    def test_misc_expenses_written_off_r75(self, engine):
        result = engine.apply("Misc Expenses Written Off", None, None, "manufacturing")
        assert result is not None
        assert result.cma_row == 75
```

- [ ] **Step 1.2: Run tests to confirm they all FAIL (red phase)**

```bash
docker compose exec backend pytest backend/tests/test_rule_engine.py -v 2>&1 | head -60
```

Expected: All tests fail with `AssertionError` or `KeyError` (rules don't exist yet).

- [ ] **Step 1.3: Commit the failing tests**

```bash
git add backend/tests/test_rule_engine.py
git commit -m "test: add CA-verified rule engine tests (TDD red phase)"
```

---

## Task 2: Add Section Helper Methods to rule_engine.py

These helpers are needed by Task 3 rules (leave encashment, subsidy, vehicle HP).

**Files:**
- Modify: `backend/app/services/classification/rule_engine.py` (after `_is_longterm_section`, ~line 899)

- [ ] **Step 2.1: Add `_is_balance_sheet_section` and `_is_reserves_section` methods**

In `rule_engine.py`, find the block of section helpers (around line 886). After `_is_longterm_section`, add:

```python
def _is_balance_sheet_section(self, section: str) -> bool:
    return any(w in section for w in ("balance sheet", "asset", "liabilit", "equity", "capital", "reserve"))

def _is_reserves_section(self, section: str) -> bool:
    return any(w in section for w in ("reserve", "surplus", "equity", "networth"))
```

- [ ] **Step 2.2: Run existing tests to confirm no regression**

```bash
docker compose exec backend pytest backend/tests/ -v --ignore=backend/tests/test_rule_engine.py -q 2>&1 | tail -20
```

Expected: All existing tests still pass.

---

## Task 3: Fix BCIPL-001 (Directors Remuneration R67 → R73)

**Files:**
- Modify: `backend/app/services/classification/rule_engine.py` (~line 369)

- [ ] **Step 3.1: Fix the BCIPL-001 rule in `apply()`**

Find this block in `apply()`:
```python
# BCIPL-001: Directors Remuneration → R67
if self._is_directors_remuneration(text_lower):
    return _match("Salary and staff expenses",
                  "admin_expense", "BCIPL-001", 0.95)
```

Change it to:
```python
# BCIPL-001: Directors Remuneration → R73 (CA-verified 2026-03-26, was R67)
if self._is_directors_remuneration(text_lower):
    return _match("Audit Fees & Directors Remuneration",
                  "admin_expense", "BCIPL-001", 0.95)
```

- [ ] **Step 3.2: Run BCIPL-001 tests**

```bash
docker compose exec backend pytest backend/tests/test_rule_engine.py::TestBCIPL001Fix -v
```

Expected: 3 tests PASS.

---

## Task 4: Add Employee Cost Rules Phase 1.5

Insert AFTER the existing PHASE 1 block and BEFORE PHASE 2 in `apply()`. The order within this phase matters: CA-008 (combined) must be first, then universal rules, then industry-dependent.

**Files:**
- Modify: `backend/app/services/classification/rule_engine.py`

- [ ] **Step 4.1: Add Phase 1.5 in `apply()` method**

Find the comment `# ══ PHASE 2: Industry-specific rules` in `apply()` and insert the following BEFORE it:

```python
        # ══════════════════════════════════════════════════════════════════
        # PHASE 1.5: CA employee cost rules (CA-verified 2026-03-26)
        # ORDERING: CA-008 combined MUST be first (prevents standalone rules
        # from matching combined "Salary, Wages and Bonus" lines)
        # ══════════════════════════════════════════════════════════════════

        # CA-008: Combined "Salary, Wages and Bonus" → always R45
        # MUST be before CA-002 (standalone bonus) and any salary rule
        if self._is_salary_wages_bonus_combined(text_lower):
            return _match("Wages", "manufacturing_expense", "CA-008", 0.95)

        # CA-004: Gratuity (P&L expense) → always R45
        # NOTE: MSL-003 catches "Provision for Gratuity" in BS already (PHASE 6)
        # This rule runs at PHASE 1.5 ONLY if MSL-003 hasn't already fired
        # (MSL-003 is in PHASE 6 — after this phase). To prevent overlap,
        # explicitly guard: skip if "provision" is in text.
        if self._is_gratuity_expense(text_lower) and "provision" not in text_lower:
            return _match("Wages", "manufacturing_expense", "CA-004", 0.95)

        # CA-005: EPF / Provident Fund contribution → always R45
        if self._is_epf_contribution(text_lower):
            return _match("Wages", "manufacturing_expense", "CA-005", 0.95)

        # CA-006: ESI / ESIC contribution → always R45
        if self._is_esi_contribution(text_lower):
            return _match("Wages", "manufacturing_expense", "CA-006", 0.95)

        # CA-007: Staff Mess / Canteen → always R45
        if self._is_staff_mess(text_lower):
            return _match("Wages", "manufacturing_expense", "CA-007", 0.95)

        # CA-009: Labour Charges (generic) → always R45
        # NOTE: SSSS-003 already handles specific cutting/slitting labour (R46)
        # and runs in PHASE 1 before this. So only unqualified "labour charges" reach here.
        if self._is_labour_charges(text_lower):
            return _match("Wages", "manufacturing_expense", "CA-009", 0.95)

        # CA-001: Staff Welfare → industry-dependent
        if self._is_staff_welfare(text_lower):
            if industry in ("manufacturing", "construction"):
                return _match("Wages", "manufacturing_expense", "CA-001-mfg", 0.95)
            else:
                return _match("Salary and staff expenses", "admin_expense", "CA-001-svc", 0.95)

        # CA-002: Standalone Bonus → industry-dependent
        # NOTE: CA-008 (combined salary+wages+bonus) runs first, so only
        # standalone bonus lines reach here.
        if self._is_standalone_bonus(text_lower):
            if industry in ("manufacturing", "construction"):
                return _match("Wages", "manufacturing_expense", "CA-002-mfg", 0.95)
            else:
                return _match("Salary and staff expenses", "admin_expense", "CA-002-svc", 0.95)

        # CA-003: Employee Benefits Expense (combined) → industry-dependent
        if self._is_employee_benefits_combined(text_lower):
            if industry in ("manufacturing", "construction"):
                return _match("Wages", "manufacturing_expense", "CA-003-mfg", 0.95)
            else:
                return _match("Salary and staff expenses", "admin_expense", "CA-003-svc", 0.95)

        # CA-010: Leave Encashment → P&L → R45, BS → R249
        if self._is_leave_encashment(text_lower):
            if self._is_liability_section(section_lower) or self._is_balance_sheet_section(section_lower):
                return _match("Creditors for Expenses", "Current Liability", "CA-010-bs", 0.93)
            else:
                return _match("Wages", "manufacturing_expense", "CA-010-pl", 0.95)
```

- [ ] **Step 4.2: Add the new regex patterns (class-level, after the existing V2 patterns section)**

Add after the last existing pattern (around line 820, after `_FOREX_TERMS`):

```python
    # ── CA rules V3 patterns (CA-verified 2026-03-26) ────────────────────

    # CA-008: Combined "Salary, Wages and Bonus" → always R45
    _SALARY_WAGES_BONUS_COMBINED_TERMS = re.compile(
        r"\bsalar(y|ies)\s*(,|and|&)\s*wages?\b|\bwages?\s*(,|and|&)\s*salar(y|ies)\b",
        re.IGNORECASE,
    )

    # CA-004: Gratuity (P&L expense; NOT "Provision for Gratuity" which is MSL-003)
    _GRATUITY_EXPENSE_TERMS = re.compile(
        r"\bgratuity\b",
        re.IGNORECASE,
    )

    # CA-005: EPF / Provident Fund contribution
    _EPF_CONTRIBUTION_TERMS = re.compile(
        r"\b(epf|e\.?p\.?f\.?|provident\s*fund)\s*(contribution)?\b|"
        r"\bcontribution\s*to\s*(epf|e\.?p\.?f\.?|provident\s*fund)\b",
        re.IGNORECASE,
    )

    # CA-006: ESI / ESIC contribution
    _ESI_CONTRIBUTION_TERMS = re.compile(
        r"\b(esi|e\.?s\.?i\.?c?)\s*(contribution)?\b|"
        r"\bcontribution\s*to\s*(esi|e\.?s\.?i\.?c?)\b",
        re.IGNORECASE,
    )

    # CA-007: Staff Mess / Canteen
    _STAFF_MESS_TERMS = re.compile(
        r"\bstaff\s*mess\b|\bcanteen\s*expense\b|\bcanteen\s*charges?\b",
        re.IGNORECASE,
    )

    # CA-009: Labour Charges (generic, NOT cutting/slitting which is SSSS-003)
    _LABOUR_CHARGES_TERMS = re.compile(
        r"\blabou?r\s*charges?\b",
        re.IGNORECASE,
    )

    # CA-001: Staff Welfare
    _STAFF_WELFARE_TERMS = re.compile(
        r"\bstaff\s*welfare\b",
        re.IGNORECASE,
    )

    # CA-002: Standalone Bonus (not combined with salary/wages)
    _STANDALONE_BONUS_TERMS = re.compile(
        r"\bbonus\b",
        re.IGNORECASE,
    )

    # CA-003: Employee Benefits (combined line item)
    _EMPLOYEE_BENEFITS_COMBINED_TERMS = re.compile(
        r"\bemployee\s*benefit\w*\s*expense\b|\bemployee\s*benefit\w*\b",
        re.IGNORECASE,
    )

    # CA-010: Leave Encashment
    _LEAVE_ENCASHMENT_TERMS = re.compile(
        r"\bleave\s*encashment\b|\bleave\s*salary\b",
        re.IGNORECASE,
    )
```

- [ ] **Step 4.3: Add the helper methods for new patterns (after the existing V2 helpers)**

Add after `_is_forex`:

```python
    # ── CA V3 helpers ────────────────────────────────────────────────────

    def _is_salary_wages_bonus_combined(self, text: str) -> bool:
        return bool(self._SALARY_WAGES_BONUS_COMBINED_TERMS.search(text))

    def _is_gratuity_expense(self, text: str) -> bool:
        return bool(self._GRATUITY_EXPENSE_TERMS.search(text))

    def _is_epf_contribution(self, text: str) -> bool:
        return bool(self._EPF_CONTRIBUTION_TERMS.search(text))

    def _is_esi_contribution(self, text: str) -> bool:
        return bool(self._ESI_CONTRIBUTION_TERMS.search(text))

    def _is_staff_mess(self, text: str) -> bool:
        return bool(self._STAFF_MESS_TERMS.search(text))

    def _is_labour_charges(self, text: str) -> bool:
        return bool(self._LABOUR_CHARGES_TERMS.search(text))

    def _is_staff_welfare(self, text: str) -> bool:
        return bool(self._STAFF_WELFARE_TERMS.search(text))

    def _is_standalone_bonus(self, text: str) -> bool:
        return bool(self._STANDALONE_BONUS_TERMS.search(text))

    def _is_employee_benefits_combined(self, text: str) -> bool:
        return bool(self._EMPLOYEE_BENEFITS_COMBINED_TERMS.search(text))

    def _is_leave_encashment(self, text: str) -> bool:
        return bool(self._LEAVE_ENCASHMENT_TERMS.search(text))
```

- [ ] **Step 4.4: Run employee cost tests**

```bash
docker compose exec backend pytest backend/tests/test_rule_engine.py::TestCA008CombinedSalaryWagesBonuse backend/tests/test_rule_engine.py::TestCA004Gratuity backend/tests/test_rule_engine.py::TestCA005EPF backend/tests/test_rule_engine.py::TestCA006ESI backend/tests/test_rule_engine.py::TestCA007StaffMess backend/tests/test_rule_engine.py::TestCA009LabourCharges backend/tests/test_rule_engine.py::TestCA001StaffWelfare backend/tests/test_rule_engine.py::TestCA002Bonus backend/tests/test_rule_engine.py::TestCA003EmployeeBenefits backend/tests/test_rule_engine.py::TestCA010LeaveEncashment -v
```

Expected: All PASS.

- [ ] **Step 4.5: Commit**

```bash
git add backend/app/services/classification/rule_engine.py
git commit -m "feat: add CA employee cost rules CA-001 to CA-010 (R45/R67/R249)"
```

---

## Task 5: Add Industry/Finance/Admin/BS Rules (CA-011 to CA-024)

**Files:**
- Modify: `backend/app/services/classification/rule_engine.py`

### 5A: CA-011 (Power/Electric) — insert at end of PHASE 2

- [ ] **Step 5A.1: Add CA-011 at end of PHASE 2 in `apply()`**

Find the end of PHASE 2 (after `SELL-001`):
```python
        # SELL-001: Selling & Distribution / Carriage Outward → R70 (all industries)
        if self._is_selling_distribution(text_lower):
            ...
```

After `SELL-001`, add:
```python
        # CA-011: Power / Electric Charges → industry-dependent (CA-verified 2026-03-26)
        # NOTE: "Electricity Deposit" already handled by C-004-govt (PHASE 1) → R237
        if self._is_power_electric(text_lower):
            if industry in ("manufacturing", "construction"):
                return _match("Power, Coal, Fuel and Water",
                              "manufacturing_expense", "CA-011-mfg", 0.95)
            else:
                return _match("Others (Admin)", "admin_expense", "CA-011-svc", 0.93)
```

- [ ] **Step 5A.2: Add Pattern and helper**

In the class-level patterns section (after `_LEAVE_ENCASHMENT_TERMS`):
```python
    # CA-011: Power / Electric Charges
    _POWER_ELECTRIC_TERMS = re.compile(
        r"\b(electric\w*\s*(charges?|expense|bill)|power\s*(charges?|expense|bill)|electricity)\b",
        re.IGNORECASE,
    )
```

After `_is_leave_encashment`:
```python
    def _is_power_electric(self, text: str) -> bool:
        return bool(self._POWER_ELECTRIC_TERMS.search(text))
```

### 5B: CA-012, CA-013, CA-014 (Finance) — add to PHASE 3

- [ ] **Step 5B.1: Add CA-012, CA-013, CA-014 at end of PHASE 3 in `apply()`**

After `SSSS-009` in PHASE 3:
```python
        # CA-012: Interest on tax delay → R84 (CA chose over AI's R83)
        if self._is_interest_tax_delay(text_lower):
            return _match("Interest on Working capital loans",
                          "Interest", "CA-012", 0.93)

        # CA-013: Liquidated Damages → R71 (CA chose over AI's R83)
        if self._is_liquidated_damages(text_lower):
            return _match("Others (Admin)", "admin_expense", "CA-013", 0.93)

        # CA-014: Loan Processing Fee → R85 (CA chose over AI's R84)
        if self._is_loan_processing_fee(text_lower):
            return _match("Bank Charges", "Interest", "CA-014", 0.93)
```

- [ ] **Step 5B.2: Add patterns and helpers**

```python
    # CA-012: Interest on tax delay
    _INTEREST_TAX_DELAY_TERMS = re.compile(
        r"\binterest\s*(on\s*)?(delay|late)\s*(payment\s*(of\s*)?)?(tax|income\s*tax)\b|"
        r"\binterest\s*on\s*income\s*tax\b",
        re.IGNORECASE,
    )

    # CA-013: Liquidated Damages
    _LIQUIDATED_DAMAGES_TERMS = re.compile(
        r"\bliquidated\s*damages?\b",
        re.IGNORECASE,
    )

    # CA-014: Loan Processing Fee
    _LOAN_PROCESSING_FEE_TERMS = re.compile(
        r"\bloan\s*(processing|arrangement|origination)\s*(fee|charges?)\b|"
        r"\bprocessing\s*(charges?|fee)\s*(on|for)\s*loan\b",
        re.IGNORECASE,
    )
```

```python
    def _is_interest_tax_delay(self, text: str) -> bool:
        return bool(self._INTEREST_TAX_DELAY_TERMS.search(text))

    def _is_liquidated_damages(self, text: str) -> bool:
        return bool(self._LIQUIDATED_DAMAGES_TERMS.search(text))

    def _is_loan_processing_fee(self, text: str) -> bool:
        return bool(self._LOAN_PROCESSING_FEE_TERMS.search(text))
```

### 5C: CA-019, CA-020, CA-021, CA-022, CA-024 — add as PHASE 3.5 (after PHASE 3, before PHASE 4)

- [ ] **Step 5C.1: Add PHASE 3.5 block in `apply()`**

Find comment `# ══ PHASE 4: A-type rules` and insert before it:

```python
        # ══════════════════════════════════════════════════════════════════
        # PHASE 3.5: CA finance/admin/BS rules (CA-verified 2026-03-26)
        # ══════════════════════════════════════════════════════════════════

        # CA-019: Licence & Subscription → R71 (CA chose over AI's R68)
        if self._is_licence_subscription(text_lower):
            return _match("Others (Admin)", "admin_expense", "CA-019", 0.93)

        # CA-020: Insurance Premium → R71 (CA chose over AI's R49)
        # IMPORTANT: overrides MSL-008 _ADMIN_CATCHALL_TERMS which also catches insurance
        if self._is_insurance_premium(text_lower):
            return _match("Others (Admin)", "admin_expense", "CA-020", 0.93)

        # CA-021: Subsidy / Government Grant → context-dependent
        if self._is_subsidy_grant(text_lower):
            if self._is_balance_sheet_section(section_lower) or self._is_reserves_section(section_lower):
                return _match("Other Reserve", "Equity", "CA-021-bs", 0.90)
            else:
                return _match("Extraordinary income", "Non-operating Income", "CA-021-pl", 0.93)

        # CA-022: Stores & Spares → R44 default, R43 if imported
        if self._is_stores_spares(text_lower):
            if "import" in text_lower:
                return _match("Stores and spares consumed (Imported)",
                              "manufacturing_expense", "CA-022-imp", 0.95)
            else:
                return _match("Stores and spares consumed (Indigenous)",
                              "manufacturing_expense", "CA-022-ind", 0.95)

        # CA-024: Preliminary / Pre-operative Expenses written off → R75
        if self._is_preliminary_expense_writeoff(text_lower):
            return _match("Miscellaneous Expenses written off",
                          "admin_expense", "CA-024", 0.95)

        # CA-023: Issue of Bonus Shares → always flag as doubt (no CMA impact)
        if self._is_bonus_share_issue(text_lower):
            return RuleMatchResult(
                cma_field_name="DOUBT - Bonus Share Issue (manual review required)",
                cma_row=0,
                cma_sheet="input_sheet",
                broad_classification="equity",
                rule_id="CA-023",
                confidence=0.0,
            )
```

- [ ] **Step 5C.2: Add patterns and helpers**

```python
    # CA-019: Licence & Subscription
    _LICENCE_SUBSCRIPTION_TERMS = re.compile(
        r"\b(licen[cs]e|subscription)\s*(fee|charges?|expense)?\b",
        re.IGNORECASE,
    )

    # CA-020: Insurance Premium / Charges
    _INSURANCE_PREMIUM_TERMS = re.compile(
        r"\binsurance\s*(premium|policy|charges?|expense)?\b",
        re.IGNORECASE,
    )

    # CA-021: Subsidy / Government Grant
    _SUBSIDY_GRANT_TERMS = re.compile(
        r"\b(subsidy|government\s*grant|govt\s*grant|capital\s*subsidy|revenue\s*subsidy)\b",
        re.IGNORECASE,
    )

    # CA-022: Stores & Spares (generic; import check done in apply())
    _STORES_SPARES_TERMS = re.compile(
        r"\bstores?\s*(and\s*)?spares?\b",
        re.IGNORECASE,
    )

    # CA-024: Preliminary / Pre-operative Expense write-off
    _PRELIMINARY_EXPENSE_WRITEOFF_TERMS = re.compile(
        r"\b(preliminary|pre[\s-]?operative|incorporation)\s*(expense|cost)?\s*(written\s*off|amortis\w*|w/?o)\b|"
        r"\bmisc\w*\s*exp\w*\s*written\s*off\b",
        re.IGNORECASE,
    )

    # CA-023: Issue of Bonus Shares
    _BONUS_SHARE_ISSUE_TERMS = re.compile(
        r"\b(issue|issuance)\s*(of\s*)?bonus\s*shares?\b|\bbonus\s*shares?\s*(issue|allot\w*)\b",
        re.IGNORECASE,
    )
```

```python
    def _is_licence_subscription(self, text: str) -> bool:
        return bool(self._LICENCE_SUBSCRIPTION_TERMS.search(text))

    def _is_insurance_premium(self, text: str) -> bool:
        return bool(self._INSURANCE_PREMIUM_TERMS.search(text))

    def _is_subsidy_grant(self, text: str) -> bool:
        return bool(self._SUBSIDY_GRANT_TERMS.search(text))

    def _is_stores_spares(self, text: str) -> bool:
        return bool(self._STORES_SPARES_TERMS.search(text))

    def _is_preliminary_expense_writeoff(self, text: str) -> bool:
        return bool(self._PRELIMINARY_EXPENSE_WRITEOFF_TERMS.search(text))

    def _is_bonus_share_issue(self, text: str) -> bool:
        return bool(self._BONUS_SHARE_ISSUE_TERMS.search(text))
```

### 5D: CA-015, CA-016, CA-017, CA-018 — add as PHASE 7.5 (after BCIPL-001)

- [ ] **Step 5D.1: Add PHASE 7.5 in `apply()`**

Find comment `# ══ PHASE 8: Admin catch-all` and insert before it:

```python
        # ══════════════════════════════════════════════════════════════════
        # PHASE 7.5: CA balance sheet liability/asset rules
        # (CA-verified 2026-03-26)
        # ══════════════════════════════════════════════════════════════════

        # CA-015: Vehicle HP Current Maturities → R148 (CA chose over AI's R140)
        if self._is_vehicle_hp_current(text_lower):
            return _match("Other Debts Repayable in Next One year",
                          "Current Liability", "CA-015", 0.93)

        # CA-016: Other Long Term Liabilities → R149 (CA chose over AI's R153)
        if self._is_other_lt_liability(text_lower):
            return _match("Balance Other Debts",
                          "Term Liabilities", "CA-016", 0.90)

        # CA-017: Advances to Suppliers → R220 (CA chose over AI's R219)
        if self._is_advance_to_suppliers(text_lower):
            return _match("Advances to suppliers of raw materials",
                          "Current Assets", "CA-017", 0.93)

        # CA-018: Security Deposits (generic, not govt/private specific) → R238
        # NOTE: C-004-govt (R237) and C-004-private (R238) run EARLIER in PHASE 1.
        # This rule catches remaining "security deposit" items not matched by those.
        if self._is_generic_security_deposit(text_lower):
            return _match("Other non current assets",
                          "Non-Current Assets", "CA-018", 0.90)
```

- [ ] **Step 5D.2: Add patterns and helpers**

```python
    # CA-015: Vehicle HP Current Maturities
    _VEHICLE_HP_CURRENT_TERMS = re.compile(
        r"\bvehicle\s*(hp|hire\s*purchase)\s*(current\s*maturit\w*|installment|due)\b|"
        r"\bhp\s*(installment|instalment|due|maturit\w*)\b",
        re.IGNORECASE,
    )

    # CA-016: Other Long Term Liabilities
    _OTHER_LT_LIABILITY_TERMS = re.compile(
        r"\bother\s*long[\s-]?term\s*liabilit\w*\b",
        re.IGNORECASE,
    )

    # CA-017: Advances to Suppliers (generic advance; not capital goods)
    _ADVANCE_TO_SUPPLIERS_TERMS = re.compile(
        r"\badvance\w*\s*(to|paid\s*to)\s*suppliers?\b|\bsupplier\s*advance\b",
        re.IGNORECASE,
    )

    # CA-018: Security Deposits (generic — not govt or private/landlord which are handled by C-004)
    _GENERIC_SECURITY_DEPOSIT_TERMS = re.compile(
        r"\bsecurity\s*deposit\b",
        re.IGNORECASE,
    )
```

```python
    def _is_vehicle_hp_current(self, text: str) -> bool:
        return bool(self._VEHICLE_HP_CURRENT_TERMS.search(text))

    def _is_other_lt_liability(self, text: str) -> bool:
        return bool(self._OTHER_LT_LIABILITY_TERMS.search(text))

    def _is_advance_to_suppliers(self, text: str) -> bool:
        return bool(self._ADVANCE_TO_SUPPLIERS_TERMS.search(text))

    def _is_generic_security_deposit(self, text: str) -> bool:
        return bool(self._GENERIC_SECURITY_DEPOSIT_TERMS.search(text))
```

- [ ] **Step 5E: Run all new rule tests**

```bash
docker compose exec backend pytest backend/tests/test_rule_engine.py -v
```

Expected: All tests PASS. Fix any failures before proceeding.

- [ ] **Step 5F: Run full test suite to check for regressions**

```bash
docker compose exec backend pytest backend/tests/ -q 2>&1 | tail -30
```

Expected: No existing test failures. If any fail, fix them.

- [ ] **Step 5G: Commit**

```bash
git add backend/app/services/classification/rule_engine.py
git commit -m "feat: add CA rules CA-011 to CA-024 — finance/admin/BS rules verified by CA"
```

---

## Task 6: Fix scoped_classifier.py

**Files:**
- Modify: `backend/app/services/classification/scoped_classifier.py`

### 6A: Fix `_KEYWORD_ROUTES`

- [ ] **Step 6A.1: Fix `_KEYWORD_ROUTES` — remove `bank charge` from admin, add to finance**

Find line 192 (finance_cost pattern):
```python
(r"(?i)(interest expense|finance cost|finance charge|interest on.*loan|interest on.*working|interest paid|bank interest)", "finance_cost"),
```

Change to (add `bank charge`):
```python
(r"(?i)(interest expense|finance cost|finance charge|interest on.*loan|interest on.*working|interest paid|bank interest|bank charge)", "finance_cost"),
```

Find line 193 (admin_expense pattern):
```python
(r"(?i)(other expense|admin|audit|legal|professional|office|printing|telephone|travel|insurance|repair|miscellaneous exp|general expense|bank charge|vehicle|conveyance)", "admin_expense"),
```

Change to (remove `bank charge`):
```python
(r"(?i)(other expense|admin|audit|legal|professional|office|printing|telephone|travel|insurance|repair|miscellaneous exp|general expense|vehicle|conveyance)", "admin_expense"),
```

- [ ] **Step 6A.2: Add new routing patterns after the `employee_cost` pattern (line 188)**

After:
```python
(r"(?i)(employee|salary|salaries|wages|staff|managerial remuneration|bonus|gratuity|provident fund|esic|esi |contribution to)", "employee_cost"),
```

Add:
```python
(r"(?i)(audit\w*\s*(fee|remuneration)|director\w*\s*remuneration|statutory\s*audit)", "admin_expense"),
(r"(?i)(water\s*charges?|coal|lpg|gas\s*charges?)", "manufacturing_expense"),
(r"(?i)(security\s*(service\s*)?charges?|watchman|guard\s*charges?)", "manufacturing_expense"),
```

### 6B: Add `FORMULA_ROWS` exclusion

- [ ] **Step 6B.1: Add `FORMULA_ROWS` constant after `DOUBT_THRESHOLD`**

After line `DOUBT_THRESHOLD = 0.8`, add:
```python
# ─── Formula rows (auto-calculated in CMA.xlsm, NEVER classify into these) ────
# R200 = Stocks-in-process (=CXX formula in BS)
# R201 = Finished Goods (=CXX formula in BS)
# CA confirmed Q8a/Q8b: "shouldn't be touched" / "not to be touched"
FORMULA_ROWS: frozenset[int] = frozenset({200, 201})
```

- [ ] **Step 6B.2: Filter formula rows in `_build_prompt()`**

In `_build_prompt()`, find:
```python
        rows_text = "".join(
            f"  Row {r['sheet_row']} | {r['code']} | {self._disambiguate_row_name(r, name_counts)}\n"
            for r in context.cma_rows
        )
```

Change to:
```python
        # Filter out formula rows — auto-calculated cells, must never be written to
        eligible_rows = [r for r in context.cma_rows if r["sheet_row"] not in FORMULA_ROWS]
        name_counts = Counter(r["name"] for r in eligible_rows)

        rows_text = "".join(
            f"  Row {r['sheet_row']} | {r['code']} | {self._disambiguate_row_name(r, name_counts)}\n"
            for r in eligible_rows
        )
```

Also update the `name_counts = Counter(...)` line that currently appears before `rows_text` — remove the old `name_counts` line since it's now inside the new block:

```python
        # BEFORE (remove this line):
        name_counts = Counter(r["name"] for r in context.cma_rows)
```

### 6C: Add disambiguation rules to `_build_prompt()`

- [ ] **Step 6C.1: Add CA-verified disambiguation block to `_build_prompt()`**

Find in `_build_prompt()`:
```python
        return f"""Classify this financial line item into the correct CMA row.
...
INSTRUCTIONS:
1. Pick the BEST matching CMA row from the list above
2. If the item does NOT belong to any of these rows, set cma_row to 0
3. Set confidence to reflect how certain you are (0.8+ = confident, below = unsure)
4. Keep reasoning under 15 words"""
```

Change the return string to include CA rules (replace the existing IMPORTANT RULES + add CA rules):

```python
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
- P&L stock (Changes in Inventories) → P&L rows 53-59. BS stock → do NOT classify (formula rows).
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
```

- [ ] **Step 6D: Run full test suite**

```bash
docker compose exec backend pytest backend/tests/ -q 2>&1 | tail -30
```

Expected: All tests pass.

- [ ] **Step 6E: Commit**

```bash
git add backend/app/services/classification/scoped_classifier.py
git commit -m "feat: fix _KEYWORD_ROUTES routing, add FORMULA_ROWS exclusion, add CA disambiguation rules"
```

---

## Task 7: Update JSON Data Files

### 7A: Update `cma_classification_rules.json`

**Files:**
- Modify: `CMA_Ground_Truth_v1/reference/cma_classification_rules.json`

- [ ] **Step 7A.1: Append 13 CA expert rule objects to the `rules` array**

The file has `"rules": [...]`. Find the last `}` before the closing `]` of the rules array and add a comma, then append:

```json
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
      "mapping_notes": "For manufacturing/construction. Trading/services use Row 67."
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
      "cma_classification_text": "Item 52: Other Debts Repayable in next one year",
      "broad_classification": "Current Liability",
      "remarks": "R148 NOT R140. CA overrode AI. CA-verified 2026-03-26.",
      "canonical_sheet_row": 148,
      "canonical_code": "III_L8a",
      "canonical_name": "Other Debts Repayable in Next One year",
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
      "canonical_name": "Advances to suppliers of raw materials",
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
      "remarks": "Preliminary/pre-operative expense amortisation ONLY. Regular Miscellaneous Expenses go to R71. CA-verified 2026-03-26.",
      "canonical_sheet_row": 75,
      "canonical_code": "II_A9",
      "canonical_name": "Miscellaneous Expenses written off",
      "mapping_confidence": "certain",
      "mapping_notes": "Non-cash expenditure only"
    },
    {
      "rule_id": "CA_R12",
      "source_sheet": "P&L",
      "fs_item": "Subsidy / Government Grant",
      "cma_classification_text": "P&L: Row 33 Extraordinary Income; BS: Row 125 Other Reserve",
      "broad_classification": "Context-dependent",
      "remarks": "CA-verified 2026-03-26.",
      "canonical_sheet_row": 33,
      "canonical_code": "II_NI4",
      "canonical_name": "Extraordinary income",
      "mapping_confidence": "certain",
      "mapping_notes": "P&L context only. BS context goes to Row 125 Other Reserve."
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
```

- [ ] **Step 7A.2: Validate JSON is parseable**

```bash
docker compose exec backend python -c "import json; json.load(open('/app/CMA_Ground_Truth_v1/reference/cma_classification_rules.json')); print('JSON valid')"
```

Expected: `JSON valid`

### 7B: Add training data examples to `training_data.json`

**Files:**
- Modify: `CMA_Ground_Truth_v1/database/training_data.json`

- [ ] **Step 7B.1: Append 18 CA-verified examples to the training_data.json array**

The file is a JSON array `[...]`. Find the last `}` before the closing `]` and add a comma, then append:

```json
  {
    "text": "Staff Welfare Expenses",
    "label": 45,
    "label_code": "II_M5",
    "label_name": "Wages",
    "source_form": "notes_pl",
    "section_normalized": "employee_cost",
    "industry_type": "manufacturing",
    "entity_type": "private_limited",
    "match_type": "direct",
    "company": "CA-verified-2026-03-26",
    "financial_year": "CA-verified"
  },
  {
    "text": "Staff Welfare Expenses",
    "label": 67,
    "label_code": "II_A1",
    "label_name": "Salary and staff expenses",
    "source_form": "notes_pl",
    "section_normalized": "employee_cost",
    "industry_type": "trading",
    "entity_type": "private_limited",
    "match_type": "direct",
    "company": "CA-verified-2026-03-26",
    "financial_year": "CA-verified"
  },
  {
    "text": "Gratuity to Employees",
    "label": 45,
    "label_code": "II_M5",
    "label_name": "Wages",
    "source_form": "notes_pl",
    "section_normalized": "employee_cost",
    "industry_type": "manufacturing",
    "entity_type": "private_limited",
    "match_type": "direct",
    "company": "CA-verified-2026-03-26",
    "financial_year": "CA-verified"
  },
  {
    "text": "Contribution to EPF",
    "label": 45,
    "label_code": "II_M5",
    "label_name": "Wages",
    "source_form": "notes_pl",
    "section_normalized": "employee_cost",
    "industry_type": "manufacturing",
    "entity_type": "private_limited",
    "match_type": "direct",
    "company": "CA-verified-2026-03-26",
    "financial_year": "CA-verified"
  },
  {
    "text": "Contribution to ESI",
    "label": 45,
    "label_code": "II_M5",
    "label_name": "Wages",
    "source_form": "notes_pl",
    "section_normalized": "employee_cost",
    "industry_type": "manufacturing",
    "entity_type": "private_limited",
    "match_type": "direct",
    "company": "CA-verified-2026-03-26",
    "financial_year": "CA-verified"
  },
  {
    "text": "Directors Remuneration",
    "label": 73,
    "label_code": "II_A7",
    "label_name": "Audit Fees & Directors Remuneration",
    "source_form": "notes_pl",
    "section_normalized": "admin_expense",
    "industry_type": "manufacturing",
    "entity_type": "private_limited",
    "match_type": "direct",
    "company": "CA-verified-2026-03-26",
    "financial_year": "CA-verified"
  },
  {
    "text": "Liquidated Damages",
    "label": 71,
    "label_code": "II_A5",
    "label_name": "Others (Admin)",
    "source_form": "notes_pl",
    "section_normalized": "admin_expense",
    "industry_type": "manufacturing",
    "entity_type": "private_limited",
    "match_type": "direct",
    "company": "CA-verified-2026-03-26",
    "financial_year": "CA-verified"
  },
  {
    "text": "Loan Processing Fee",
    "label": 85,
    "label_code": "II_F3",
    "label_name": "Bank Charges",
    "source_form": "notes_pl",
    "section_normalized": "finance_cost",
    "industry_type": "manufacturing",
    "entity_type": "private_limited",
    "match_type": "direct",
    "company": "CA-verified-2026-03-26",
    "financial_year": "CA-verified"
  },
  {
    "text": "Vehicle HP Current Maturities",
    "label": 148,
    "label_code": "III_L8a",
    "label_name": "Other Debts Repayable in Next One year",
    "source_form": "notes_bs",
    "section_normalized": "current_liabilities",
    "industry_type": "manufacturing",
    "entity_type": "private_limited",
    "match_type": "direct",
    "company": "CA-verified-2026-03-26",
    "financial_year": "CA-verified"
  },
  {
    "text": "Licence & Subscription",
    "label": 71,
    "label_code": "II_A5",
    "label_name": "Others (Admin)",
    "source_form": "notes_pl",
    "section_normalized": "admin_expense",
    "industry_type": "services",
    "entity_type": "private_limited",
    "match_type": "direct",
    "company": "CA-verified-2026-03-26",
    "financial_year": "CA-verified"
  },
  {
    "text": "Insurance Premium",
    "label": 71,
    "label_code": "II_A5",
    "label_name": "Others (Admin)",
    "source_form": "notes_pl",
    "section_normalized": "admin_expense",
    "industry_type": "manufacturing",
    "entity_type": "private_limited",
    "match_type": "direct",
    "company": "CA-verified-2026-03-26",
    "financial_year": "CA-verified"
  },
  {
    "text": "Advances to Suppliers",
    "label": 220,
    "label_code": "III_A10b",
    "label_name": "Advances to suppliers of raw materials",
    "source_form": "notes_bs",
    "section_normalized": "other_assets",
    "industry_type": "manufacturing",
    "entity_type": "private_limited",
    "match_type": "direct",
    "company": "CA-verified-2026-03-26",
    "financial_year": "CA-verified"
  },
  {
    "text": "Security Deposits Paid",
    "label": 238,
    "label_code": "III_A13",
    "label_name": "Other non current assets",
    "source_form": "notes_bs",
    "section_normalized": "other_assets",
    "industry_type": "manufacturing",
    "entity_type": "private_limited",
    "match_type": "direct",
    "company": "CA-verified-2026-03-26",
    "financial_year": "CA-verified"
  },
  {
    "text": "Carriage Outward",
    "label": 70,
    "label_code": "II_A4",
    "label_name": "Advertisements and Sales Promotions",
    "source_form": "notes_pl",
    "section_normalized": "selling_expense",
    "industry_type": "manufacturing",
    "entity_type": "private_limited",
    "match_type": "direct",
    "company": "CA-verified-2026-03-26",
    "financial_year": "CA-verified"
  },
  {
    "text": "Brokerage and Commission",
    "label": 70,
    "label_code": "II_A4",
    "label_name": "Advertisements and Sales Promotions",
    "source_form": "notes_pl",
    "section_normalized": "selling_expense",
    "industry_type": "manufacturing",
    "entity_type": "private_limited",
    "match_type": "direct",
    "company": "CA-verified-2026-03-26",
    "financial_year": "CA-verified"
  },
  {
    "text": "Selling and Distribution Expenses",
    "label": 70,
    "label_code": "II_A4",
    "label_name": "Advertisements and Sales Promotions",
    "source_form": "notes_pl",
    "section_normalized": "selling_expense",
    "industry_type": "manufacturing",
    "entity_type": "private_limited",
    "match_type": "direct",
    "company": "CA-verified-2026-03-26",
    "financial_year": "CA-verified"
  },
  {
    "text": "Miscellaneous Expenses",
    "label": 71,
    "label_code": "II_A5",
    "label_name": "Others (Admin)",
    "source_form": "notes_pl",
    "section_normalized": "admin_expense",
    "industry_type": "manufacturing",
    "entity_type": "private_limited",
    "match_type": "direct",
    "company": "CA-verified-2026-03-26",
    "financial_year": "CA-verified"
  },
  {
    "text": "Administrative & General Expenses",
    "label": 71,
    "label_code": "II_A5",
    "label_name": "Others (Admin)",
    "source_form": "notes_pl",
    "section_normalized": "admin_expense",
    "industry_type": "trading",
    "entity_type": "private_limited",
    "match_type": "direct",
    "company": "CA-verified-2026-03-26",
    "financial_year": "CA-verified"
  }
```

- [ ] **Step 7B.2: Validate JSON is parseable**

```bash
docker compose exec backend python -c "import json; data=json.load(open('/app/CMA_Ground_Truth_v1/database/training_data.json')); print(f'training_data has {len(data)} entries — valid')"
```

Expected: Count increases by 18, JSON valid.

- [ ] **Step 7C: Commit data files**

```bash
git add "CMA_Ground_Truth_v1/reference/cma_classification_rules.json" "CMA_Ground_Truth_v1/database/training_data.json"
git commit -m "data: add 13 CA expert rules and 18 CA-verified training examples"
```

---

## Task 8: Final Verification

- [ ] **Step 8.1: Run full test suite**

```bash
docker compose exec backend pytest backend/tests/ -v 2>&1 | tail -40
```

Expected: All tests pass. If any tests still reference old wrong behavior (e.g., asserting BCIPL-001 → R67), update those assertions to match the CA answer (R73).

- [ ] **Step 8.2: Run BCIPL accuracy test**

```bash
docker compose exec backend python run_accuracy_bcipl.py
```

Check the terminal for accuracy improvement. Expected improvement on:
- Directors Remuneration (R67→R73)
- Staff Welfare, Bonus, Gratuity, EPF, ESI (→R45)
- Bank Charges, Loan Processing Fee (→R85)
- Carriage Outward, Selling & Distribution (→R70)

- [ ] **Step 8.3: Spot-check key CA answers in Python shell**

```bash
docker compose exec backend python -c "
from app.services.classification.rule_engine import RuleEngine
e = RuleEngine()
checks = [
    ('Staff Welfare Expenses', None, None, 'manufacturing', 45),
    ('Staff Welfare Expenses', None, None, 'trading', 67),
    ('Directors Remuneration', None, None, 'manufacturing', 73),
    ('Liquidated Damages', None, None, 'manufacturing', 71),
    ('Bank Charges', None, None, 'manufacturing', None),  # rule engine won't catch generic 'Bank Charges' (no rule)
    ('Loan Processing Fee', None, None, 'manufacturing', 85),
    ('Licence Fees', None, None, 'services', 71),
    ('Insurance Premium', None, None, 'manufacturing', 71),
    ('Vehicle HP Current Maturities', None, 'current liabilities', 'manufacturing', 148),
    ('Advances to Suppliers', None, 'current assets', 'manufacturing', 220),
]
for text, amount, section, industry, expected_row in checks:
    result = e.apply(text, amount, section, industry)
    row = result.cma_row if result else None
    status = 'PASS' if row == expected_row else 'FAIL'
    print(f'{status}: \"{text}\" → R{row} (expected R{expected_row})')
"
```

- [ ] **Step 8.4: Commit final adjustments if any**

```bash
git add -A
git commit -m "fix: CA-verified classification rules — 24 new rules, routing fix, formula rows, prompt enhancement"
```

---

## Quick Reference: Phase Ordering in `apply()` After Changes

```
PHASE 1   — C-type absolute rules (existing: SSSS-006, C-001 to SSSS-013)
PHASE 1.5 — CA employee rules NEW:
              CA-008 (salary+wages+bonus combined → R45) — FIRST
              CA-004 (gratuity → R45)
              CA-005 (EPF → R45)
              CA-006 (ESI → R45)
              CA-007 (staff mess → R45)
              CA-009 (labour charges → R45)
              CA-001 (staff welfare → industry)
              CA-002 (bonus standalone → industry)
              CA-003 (employee benefits → industry)
              CA-010 (leave encashment → context)
PHASE 2   — Industry-specific (existing) + CA-011 (power/electric) at end
PHASE 3   — Interest (existing) + CA-012, CA-013, CA-014 at end
PHASE 3.5 — CA finance/admin rules NEW:
              CA-019 (licence/subscription → R71)
              CA-020 (insurance → R71)
              CA-021 (subsidy/grant → context)
              CA-022 (stores & spares → import check)
              CA-024 (preliminary expense → R75)
              CA-023 (bonus shares → doubt)
PHASE 4   — A-type synonym rules (existing)
PHASE 5   — D-type aggregation rules (existing)
PHASE 6   — Specific patterns (existing, includes MSL-003 provision for gratuity)
PHASE 7   — Remuneration: BCIPL-001 NOW → R73 (was R67)
PHASE 7.5 — CA balance sheet rules NEW:
              CA-015 (vehicle HP current → R148)
              CA-016 (other LT liability → R149)
              CA-017 (advances to suppliers → R220)
              CA-018 (security deposits generic → R238)
PHASE 8   — Admin catch-all MSL-008 (existing)
PHASE 9   — B-type context rules (existing)
```
