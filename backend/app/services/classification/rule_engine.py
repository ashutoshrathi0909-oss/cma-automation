"""Tier 0 deterministic rule engine — runs BEFORE fuzzy match and AI.

These rules encode patterns that are always correct for a given industry/context.
They are checked first to save AI API cost and eliminate known error types.

Rules are ordered by confidence: absolute rules (C-type) first, then synonym
rules (A-type), then aggregation rules (D-type), then context rules (B-type).

Returns None if no rule fires — pipeline continues to fuzzy/AI.

V2 — 2026-03-23: Added 35 new rules from 7-company analysis (BCIPL, SR Papers,
SSSS, MSL, SLIPL, INPL, Kurunji Retail). Total: ~55 rules.

V3 — 2026-03-26: CA-verified rules (CA-001 through CA-024) + BCIPL-001 fix.
CA answers reference: DOCS/ca_answers_2026-03-26.json.

V4 — 2026-03-31: Added GoldenRuleLookup — loads 594 rules from
CMA_Ground_Truth_v1/reference/cma_golden_rules_v2.json with exact + fuzzy match.
Called from pipeline as Tier 0b (after regex rules, before fuzzy matcher).
"""

from __future__ import annotations

import json
import logging
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rapidfuzz import fuzz, process

from app.mappings.cma_field_rows import ALL_FIELD_TO_ROW
from app.services.extraction._types import normalize_line_text

logger = logging.getLogger(__name__)

# ── Result dataclass ──────────────────────────────────────────────────────────


@dataclass
class RuleMatchResult:
    """Result when a deterministic rule fires."""

    cma_field_name: str
    cma_row: int
    cma_sheet: str
    broad_classification: str
    rule_id: str        # e.g. "A-001" — for audit trail
    confidence: float   # always 0.97 for deterministic rules


# ── Helper ────────────────────────────────────────────────────────────────────


def _row(field_name: str) -> int:
    """Look up row number from ALL_FIELD_TO_ROW; raises if not found."""
    return ALL_FIELD_TO_ROW[field_name]


def _match(field_name: str, broad: str, rule_id: str, conf: float = 0.95) -> RuleMatchResult:
    """Shorthand to build a RuleMatchResult."""
    return RuleMatchResult(
        cma_field_name=field_name,
        cma_row=_row(field_name),
        cma_sheet="input_sheet",
        broad_classification=broad,
        rule_id=rule_id,
        confidence=conf,
    )


# ── Typo corrections for common Indian accounting misspellings ───────────────

_TYPO_FIXES = {
    "maintainance": "maintenance",
    "recievable": "receivable",
    "expences": "expenses",
    "shedule": "schedule",
    "deprication": "depreciation",
    "provison": "provision",
    "advertisment": "advertisement",
    "miscellanious": "miscellaneous",
    "miscllaneous": "miscellaneous",
    "liabilites": "liabilities",
}


def _fix_typos(text: str) -> str:
    """Replace common Indian accounting typos in lowercased text."""
    for wrong, right in _TYPO_FIXES.items():
        text = text.replace(wrong, right)
    return text


# ── Rule Engine ───────────────────────────────────────────────────────────────


class RuleEngine:
    """Applies deterministic classification rules based on text patterns.

    Call `apply(raw_text, amount, section, industry_type)`.
    Returns a RuleMatchResult if a rule fires, None otherwise.
    """

    def apply(
        self,
        raw_text: str,
        amount: float | None,
        section: str | None,
        industry_type: str,
    ) -> RuleMatchResult | None:
        """Check all rules in priority order. Return first match or None."""
        text = normalize_line_text(raw_text)
        text_lower = _fix_typos(text.lower())
        section_lower = (section or "").lower()
        industry = industry_type.lower()

        # ══════════════════════════════════════════════════════════════════
        # PHASE 1: C-type rules — Absolute (highest confidence)
        # ══════════════════════════════════════════════════════════════════

        # SSSS-006: Tempo/Van/Auto CHARGES (goods transport) → R47
        # MUST be before C-001 to prevent "Tempo Charges" matching as vehicle
        if self._is_tempo_van_charges(text_lower):
            return _match("Freight and Transportation Charges",
                          "manufacturing_expense", "SSSS-006", 0.95)

        # CA-015: Vehicle HP / Hire Purchase Current Maturities → R148
        # MUST be before C-001 — "Current Maturities - Vehicle HP" is a liability, not a vehicle asset
        # CA-verified 2026-03-26: Q17 — agreed_with_ai=false, correct row=148
        if self._is_vehicle_hp_current(text_lower):
            return _match("Other Debts Repayable in Next One year",
                          "Current Liability", "CA-015", 0.93)

        # C-001: Motor vehicles → always capitalize as Gross Block
        if self._is_vehicle(text_lower):
            return _match("Gross Block", "Fixed Assets", "C-001", 0.97)

        # C-002: Electronics/gadgets — capitalize if ≥ ₹5,000, expense if <₹5,000
        if self._is_electronic_device(text_lower):
            if amount is not None and amount >= 5000:
                return _match("Gross Block", "Fixed Assets", "C-002-capitalize", 0.95)
            elif amount is not None and amount < 5000:
                return _match("Others (Admin)", "admin_expense", "C-002-expense", 0.92)
            # amount unknown — let AI decide, don't fire rule

        # C-003: Carriage / freight INWARD items → Freight and Transportation
        if self._is_freight_inward(text_lower):
            return _match("Freight and Transportation Charges",
                          "manufacturing_expense", "C-003", 0.97)

        # C-004-govt: Government / utility deposits → R237
        if self._is_govt_security_deposit(text_lower):
            return _match("Security deposits with government departments",
                          "Non-Current Assets", "C-004-govt", 0.95)

        # C-004-private: Private party deposits (landlord, lessor, owner) → R238
        if self._is_private_security_deposit(text_lower):
            return _match("Other non current assets",
                          "Non-Current Assets", "C-004-private", 0.93)

        # C-005: ECGS / ECLGS government-guaranteed loans → R137
        if self._is_ecgs_eclgs(text_lower):
            return _match("Term Loan Balance Repayable after one year",
                          "Term Liabilities", "C-005", 0.97)

        # C-006: Sellers / Buyers / Suppliers Credit → R137
        if self._is_sellers_credit(text_lower):
            return _match("Term Loan Balance Repayable after one year",
                          "Term Liabilities", "C-006", 0.95)

        # C-007: Channel Financing / Supply Chain Finance → R131
        if self._is_channel_financing(text_lower):
            return _match("Working Capital Bank Finance - Bank 1",
                          "Current Liability", "C-007", 0.95)

        # C-008: Inland LC Discounting → R132
        if self._is_inland_lc(text_lower):
            return _match("Working Capital Bank Finance - Bank 2",
                          "Current Liability", "C-008", 0.93)

        # C-009: Bill Discounting Charges → R84
        if self._is_bill_discounting(text_lower):
            return _match("Interest on Working capital loans",
                          "Interest", "C-009", 0.95)

        # SRP-001: Customs Duty on Import → R41
        if self._is_customs_duty(text_lower):
            return _match("Raw Materials Consumed (Imported)",
                          "manufacturing_expense", "SRP-001", 0.97)

        # BCIPL-016: Capital Advances → R236
        if self._is_capital_advance(text_lower):
            return _match("Advances to suppliers of capital goods",
                          "Non-Current Assets", "BCIPL-016", 0.95)

        # BCIPL-020: Creditors for Capital Goods → R250
        if self._is_capital_goods_creditor(text_lower):
            return _match("Other current liabilities",
                          "Current Liability", "BCIPL-020", 0.95)

        # BCIPL-019: MAT Credit Entitlement → R238
        if self._is_mat_credit(text_lower):
            return _match("Other non current assets",
                          "Non-Current Assets", "BCIPL-019", 0.95)

        # BCIPL-018: GST Electronic Cash/Credit Ledger → R237
        if self._is_electronic_ledger(text_lower):
            return _match("Security deposits with government departments",
                          "Non-Current Assets", "BCIPL-018", 0.93)

        # BCIPL-017: GST Input Recoverable → R219
        if self._is_gst_input(text_lower):
            return _match("Advances recoverable in cash or in kind",
                          "Current Assets", "BCIPL-017", 0.93)

        # BCIPL-021: Statutory Dues Payable (ESI, PF, TDS, GST) → R246
        if self._is_statutory_dues(text_lower):
            return _match("Other statutory liabilities (due within 1 year)",
                          "Current Liability", "BCIPL-021", 0.95)

        # CA-023: Issue of Bonus Shares → always doubt (CA-verified 2026-03-26: Q15)
        # CA answer: not to be filled directly; capital reflects change, reserves adjust.
        # Force doubt so CA can manually handle the dual-entry adjustment.
        if self._is_bonus_share_issue(text_lower):
            return RuleMatchResult(
                cma_field_name="DOUBT - Bonus Share Issue",
                cma_row=0,
                cma_sheet="input_sheet",
                broad_classification="DOUBT",
                rule_id="CA-023",
                confidence=0.0,
            )

        # SSSS-003: Cutting / Slitting Labour Charges → R46
        if self._is_cutting_slitting(text_lower):
            return _match("Processing / Job Work Charges",
                          "manufacturing_expense", "SSSS-003", 0.95)

        # SSSS-007: Weighment / Testing / Inspection → R49
        if self._is_weighment_testing(text_lower):
            return _match("Others (Manufacturing)",
                          "manufacturing_expense", "SSSS-007", 0.93)

        # SLI-009: Capital WIP / Under Construction → R165
        if self._is_capital_wip(text_lower):
            return _match("Capital Work in Progress",
                          "Fixed Assets", "SLI-009", 0.95)

        # SLI-008: Moulds / Dies / Jigs & Fixtures → R162
        if self._is_moulds_dies(text_lower):
            return _match("Gross Block", "Fixed Assets", "SLI-008", 0.93)

        # INPL-002: Unbilled Services / Accrued Revenue → R206
        if self._is_unbilled_services(text_lower):
            return _match("Domestic Receivables",
                          "Current Assets", "INPL-002", 0.93)

        # SSSS-002: Discount Receivable (BS asset) → R223
        if self._is_discount_receivable(text_lower):
            return _match("Other Advances / current asset",
                          "Current Assets", "SSSS-002", 0.93)

        # KR-001: Partners' Capital Account → R116
        if self._is_partners_capital(text_lower):
            return _match("Issued, Subscribed and Paid up",
                          "Equity", "KR-001", 0.95)

        # SSSS-013: Advance Income Tax / TDS Receivable → R221
        if self._is_advance_tax(text_lower):
            return _match("Advance Income Tax",
                          "Current Assets", "SSSS-013", 0.93)

        # ══════════════════════════════════════════════════════════════════
        # PHASE 1b: CA employee cost rules (CA-verified 2026-03-26)
        # ══════════════════════════════════════════════════════════════════

        # CA-008: "Salary, Wages and Bonus" combined line → R45 always
        # MUST be BEFORE generic salary/bonus patterns (CA-verified: Q1h)
        if self._is_salary_wages_bonus_combined(text_lower):
            return _match("Wages", "manufacturing_expense", "CA-008", 0.95)

        # CA-004: Gratuity (standalone, NOT "provision for gratuity") → R45
        # CA-verified 2026-03-26: Q1b — agreed_with_ai=false, correct row=45
        if self._is_gratuity_standalone(text_lower):
            return _match("Wages", "manufacturing_expense", "CA-004", 0.95)

        # CA-005: EPF / Provident Fund contribution → R45
        # CA-verified 2026-03-26: Q1c — agreed_with_ai=false, correct row=45
        if self._is_epf_contribution(text_lower):
            return _match("Wages", "manufacturing_expense", "CA-005", 0.95)

        # CA-006: ESI contribution → R45
        # CA-verified 2026-03-26: Q1d — agreed_with_ai=true, correct row=45
        if self._is_esi_contribution(text_lower):
            return _match("Wages", "manufacturing_expense", "CA-006", 0.95)

        # CA-007: Staff Mess / Canteen Expense → R45
        # CA-verified 2026-03-26: Q1e — agreed_with_ai=false, correct row=45
        if self._is_staff_mess(text_lower):
            return _match("Wages", "manufacturing_expense", "CA-007", 0.95)

        # CA-009: Labour Charges (generic) → R45
        # NOTE: must be AFTER SSSS-003 (cutting/slitting labour → R46, more specific)
        # CA-verified 2026-03-26: Q1j — agreed_with_ai=true, correct row=45
        if self._is_labour_charges(text_lower):
            return _match("Wages", "manufacturing_expense", "CA-009", 0.95)

        # CA-001: Staff Welfare — industry-dependent (CA-verified 2026-03-26: Q1a)
        if self._is_staff_welfare(text_lower):
            if industry in ("manufacturing", "construction"):
                return _match("Wages", "manufacturing_expense", "CA-001-mfg", 0.95)
            else:
                return _match("Salary and staff expenses", "admin_expense", "CA-001-svc", 0.95)

        # CA-002: Standalone Bonus (NOT combined salary/wages/bonus) — industry-dependent
        # CA-verified 2026-03-26: Q1g — manufacturing→R45, trading/services→R67
        if self._is_bonus_standalone(text_lower):
            if industry in ("manufacturing", "construction"):
                return _match("Wages", "manufacturing_expense", "CA-002-mfg", 0.95)
            else:
                return _match("Salary and staff expenses", "admin_expense", "CA-002-svc", 0.95)

        # CA-003: "Employee Benefits Expense" combined — industry-dependent
        # CA-verified 2026-03-26: Q1i — manufacturing→R45, trading/services→R67
        if self._is_employee_benefits_expense(text_lower):
            if industry in ("manufacturing", "construction"):
                return _match("Wages", "manufacturing_expense", "CA-003-mfg", 0.95)
            else:
                return _match("Salary and staff expenses", "admin_expense", "CA-003-svc", 0.95)

        # CA-010: Leave Encashment — context-dependent (CA-verified 2026-03-26: Q1f)
        # BS/liability section → R249 Creditors for Expenses; P&L → R45 Wages
        if self._is_leave_encashment(text_lower):
            if self._is_liability_section(section_lower) or self._is_longterm_section(section_lower):
                return _match("Creditors for Expenses", "Current Liability", "CA-010-bs", 0.93)
            else:
                return _match("Wages", "manufacturing_expense", "CA-010-pl", 0.95)

        # ══════════════════════════════════════════════════════════════════
        # PHASE 2: Industry-specific rules
        # ══════════════════════════════════════════════════════════════════

        # JOB-001: Job Work / Processing Charges → R46 (all industries)
        if self._is_job_work(text_lower):
            return _match("Processing / Job Work Charges",
                          "manufacturing_expense", "JOB-001", 0.97)

        # RNM-001: Repairs & Maintenance in Manufacturing → R50
        if industry == "manufacturing" and self._is_repairs_maintenance(text_lower):
            return _match("Repairs & Maintenance (Manufacturing)",
                          "manufacturing_expense", "RNM-001", 0.95)

        # MSL-001: Stock in Trade in Manufacturing → R201 (Finished Goods)
        if (
            industry == "manufacturing"
            and self._is_stock_in_trade(text_lower)
            and self._is_inventory_section(section_lower)
        ):
            return _match("Finished Goods", "Current Assets", "MSL-001", 0.95)

        # SLI-002: Factory / Manufacturing Rent → R49 (manufacturing only)
        if industry == "manufacturing" and self._is_factory_rent(text_lower):
            return _match("Others (Manufacturing)",
                          "manufacturing_expense", "SLI-002", 0.93)

        # SLI-003: Royalty / Technical Know-how → R49 (manufacturing only)
        if industry == "manufacturing" and self._is_royalty(text_lower):
            return _match("Others (Manufacturing)",
                          "manufacturing_expense", "SLI-003", 0.93)

        # SLI-004: Packing Materials → R49 (manufacturing input, not sales)
        if industry == "manufacturing" and self._is_packing_materials(text_lower):
            return _match("Others (Manufacturing)",
                          "manufacturing_expense", "SLI-004", 0.93)

        # BCIPL-002: Scrap / Other Materials Consumed → R44 (manufacturing)
        if industry == "manufacturing" and self._is_scrap_materials(text_lower):
            return _match("Stores and spares consumed (Indigenous)",
                          "manufacturing_expense", "BCIPL-002", 0.93)

        # MSL-007: Freight Outward / Discount / Sales Promo (Manufacturing) → R70
        if industry == "manufacturing" and self._is_freight_outward_or_discount(text_lower):
            return _match("Advertisements and Sales Promotions",
                          "admin_expense", "MSL-007", 0.93)

        # SELL-001: Selling & Distribution / Carriage Outward → R70 (all industries)
        if self._is_selling_distribution(text_lower):
            return _match("Advertisements and Sales Promotions",
                          "admin_expense", "SELL-001", 0.93)

        # CA-011: Power / Electricity — industry-dependent (CA-verified 2026-03-26: Q12a)
        # Manufacturing/Construction → R48; Trading/Services → R71
        if self._is_power_electric(text_lower):
            if industry in ("manufacturing", "construction"):
                return _match("Power, Coal, Fuel and Water",
                              "manufacturing_expense", "CA-011-mfg", 0.95)
            else:
                return _match("Others (Admin)", "admin_expense", "CA-011-svc", 0.93)

        # ══════════════════════════════════════════════════════════════════
        # PHASE 3: Interest rules
        # ══════════════════════════════════════════════════════════════════

        # BCIPL-006: Interest on Unsecured / Director / Promoter Loans → R83
        if self._is_interest_unsecured(text_lower):
            return _match("Interest on Fixed Loans / Term loans",
                          "Interest", "BCIPL-006", 0.95)

        # KR-003: Interest to Partners / on Partners' Capital → R83
        if self._is_interest_partners(text_lower):
            return _match("Interest on Fixed Loans / Term loans",
                          "Interest", "KR-003", 0.93)

        # SSSS-009: Interest on Trading / Trade Credit → R84
        if self._is_interest_trading(text_lower):
            return _match("Interest on Working capital loans",
                          "Interest", "SSSS-009", 0.93)

        # CA-012: Interest on Delay in Payment of Taxes → R84
        # CA-verified 2026-03-26: Q10b — agreed_with_ai=false, correct row=84
        if self._is_interest_tax_delay(text_lower):
            return _match("Interest on Working capital loans",
                          "Interest", "CA-012", 0.93)

        # CA-014: Loan Processing Fee → R85 Bank Charges
        # CA-verified 2026-03-26: Q10g — agreed_with_ai=false, correct row=85
        if self._is_loan_processing_fee(text_lower):
            return _match("Bank Charges", "Interest", "CA-014", 0.93)

        # CA-013: Liquidated Damages → R71 Others (Admin)
        # CA-verified 2026-03-26: Q10d — agreed_with_ai=false, correct row=71
        if self._is_liquidated_damages(text_lower):
            return _match("Others (Admin)", "admin_expense", "CA-013", 0.93)

        # CA-019: Licence / Subscription Fees → R71 Others (Admin)
        # CA-verified 2026-03-26: Q3f — agreed_with_ai=false, correct row=71
        if self._is_licence_subscription(text_lower):
            return _match("Others (Admin)", "admin_expense", "CA-019", 0.93)

        # CA-020: Insurance Premium → R71 Others (Admin)
        # CA-verified 2026-03-26: Q22 — agreed_with_ai=false, correct row=71
        # Must be BEFORE MSL-008 admin catchall (both go to R71, but specific rule is better)
        if self._is_insurance_premium(text_lower):
            return _match("Others (Admin)", "admin_expense", "CA-020", 0.93)

        # CA-024: Preliminary / Pre-operative Expenses Written Off → R75
        # CA-verified 2026-03-26: Q32 — agreed_with_ai=true, correct row=75
        if self._is_preliminary_expense_writeoff(text_lower):
            return _match("Miscellaneous Expenses written off",
                          "admin_expense", "CA-024", 0.95)

        # CA-021: Subsidy / Government Grant — context-dependent (CA-verified 2026-03-26: Q38)
        # BS/reserves section → R125 Other Reserve; P&L → R33 Extraordinary income
        if self._is_subsidy_grant(text_lower):
            if self._is_reserves_section(section_lower):
                return _match("Other Reserve", "Equity", "CA-021-bs", 0.90)
            else:
                return _match("Extraordinary income",
                              "Non-operating Income", "CA-021-pl", 0.93)

        # CA-022: Stores & Spares — import vs indigenous (CA-verified 2026-03-26: Q12g)
        if self._is_stores_spares(text_lower):
            if "import" in text_lower:
                return _match("Stores and spares consumed (Imported)",
                              "manufacturing_expense", "CA-022-imp", 0.95)
            else:
                return _match("Stores and spares consumed (Indigenous)",
                              "manufacturing_expense", "CA-022-ind", 0.95)

        # ══════════════════════════════════════════════════════════════════
        # PHASE 4: A-type rules — Synonym / naming patterns
        # ══════════════════════════════════════════════════════════════════

        # A-001 / A-002: GST-coded purchase entries in Trading = Raw Materials
        if industry == "trading" and self._is_gst_purchase(text_lower):
            return _match("Raw Materials Consumed (Indigenous)",
                          "manufacturing_expense",
                          "A-001" if "purchase @" in text_lower else "A-002",
                          0.97)

        # SSSS-001: Vendor Quantity Discounts / Supplier Rebates → R42 (negative)
        if self._is_vendor_discount(text_lower):
            return _match("Raw Materials Consumed (Indigenous)",
                          "manufacturing_expense", "SSSS-001", 0.95)

        # ══════════════════════════════════════════════════════════════════
        # PHASE 5: D-type rules — Aggregation / netting
        # ══════════════════════════════════════════════════════════════════

        # D-001: Purchase returns → net against Raw Materials (negative amount)
        if self._is_purchase_return(text_lower) and industry == "trading":
            return _match("Raw Materials Consumed (Indigenous)",
                          "manufacturing_expense", "D-001", 0.97)

        # D-002: Sales returns → net against Domestic Sales (negative amount)
        if self._is_sales_return(text_lower):
            return _match("Domestic Sales", "revenue", "D-002", 0.97)

        # ══════════════════════════════════════════════════════════════════
        # PHASE 6: Specific pattern rules (medium confidence)
        # ══════════════════════════════════════════════════════════════════

        # MSL-010: Liability Written Off → R90
        if self._is_liability_written_off(text_lower):
            return _match("Sundry Balances Written off",
                          "Non-operating Expense", "MSL-010", 0.93)

        # MSL-003: Provision for Gratuity (LT provision) → R153
        if self._is_gratuity_provision(text_lower) and self._is_longterm_section(section_lower):
            return _match("Unsecured Loans - Long Term Debt",
                          "Term Liabilities", "MSL-003", 0.93)

        # MSL-006: Insurance Claim Received → R34
        if self._is_insurance_claim(text_lower) and self._is_income_section(section_lower):
            return _match("Others (Non-Operating Income)",
                          "Non-operating Income", "MSL-006", 0.93)

        # FRE-001: Hamali / Cooly / Cartage / Mathadi → R47
        if self._is_hamali_cartage(text_lower):
            return _match("Freight and Transportation Charges",
                          "manufacturing_expense", "FRE-001", 0.95)

        # ══════════════════════════════════════════════════════════════════
        # PHASE 7: Remuneration / salary / income rules
        # ══════════════════════════════════════════════════════════════════

        # BCIPL-001: Directors Remuneration → R73 (CA-verified 2026-03-26: Q21a)
        # CA answer: agreed_with_ai=false, correct row=73 "Audit Fees & Directors Remuneration"
        if self._is_directors_remuneration(text_lower):
            return _match("Audit Fees & Directors Remuneration",
                          "admin_expense", "BCIPL-001", 0.95)

        # KR-002: Partners' Salary / Remuneration → R73
        if self._is_partners_salary(text_lower):
            return _match("Audit Fees & Directors Remuneration",
                          "admin_expense", "KR-002", 0.95)

        # BCIPL-022: Duty Drawback / Export Incentive → R34 (income section)
        if self._is_duty_drawback(text_lower) and self._is_income_section(section_lower):
            return _match("Others (Non-Operating Income)",
                          "Non-operating Income", "BCIPL-022", 0.93)

        # SRP-003: CFS / Clearing / Port Charges → R49
        if self._is_cfs_clearing(text_lower):
            return _match("Others (Manufacturing)",
                          "manufacturing_expense", "SRP-003", 0.93)

        # CA-016: Other Long-Term Liabilities → R149 Balance Other Debts
        # CA-verified 2026-03-26: Q20 — agreed_with_ai=false, correct row=149
        if self._is_other_lt_liabilities(text_lower):
            return _match("Balance Other Debts", "Term Liabilities", "CA-016", 0.90)

        # CA-017: Advances to Suppliers (BS) → R220
        # CA-verified 2026-03-26: Q33 — agreed_with_ai=false, correct row=220
        if self._is_advance_to_suppliers(text_lower):
            return _match("Advances to suppliers of raw materials",
                          "Current Assets", "CA-017", 0.93)

        # CA-018: Security Deposits (generic) → R238 Other non current assets
        # Must be AFTER C-004-govt and C-004-private (more specific) rules above
        # CA-verified 2026-03-26: Q35 — agreed_with_ai=false, correct row=238
        if self._is_security_deposit_generic(text_lower):
            return _match("Other non current assets",
                          "Non-Current Assets", "CA-018", 0.90)

        # ══════════════════════════════════════════════════════════════════
        # PHASE 8: Admin catch-all (lowest priority content rule)
        # ══════════════════════════════════════════════════════════════════

        # MSL-008: Tour & Travel / Consultancy / General / Insurance → R71
        if self._is_admin_catchall(text_lower):
            return _match("Others (Admin)", "admin_expense", "MSL-008", 0.90)

        # ══════════════════════════════════════════════════════════════════
        # PHASE 9: B-type rules — Context-dependent (lowest confidence)
        # ══════════════════════════════════════════════════════════════════

        # B-001: "Bank Interest" on income/receipts side → Interest Received
        if "bank interest" in text_lower and self._is_income_section(section_lower):
            return _match("Interest Received",
                          "Non-operating Income", "B-001", 0.93)

        # B-003: "Interest Paid" unqualified in Trading → Working capital interest
        if text_lower in ("interest paid", "interest") and industry == "trading":
            return _match("Interest on Working capital loans",
                          "Interest", "B-003", 0.88)

        # SLI-012: Service Revenue / Processing Income → R22 (revenue section)
        if self._is_service_revenue(text_lower) and self._is_income_section(section_lower):
            return _match("Domestic Sales", "revenue", "SLI-012", 0.93)

        # SSSS-011: Bank OD / CC Accounts → R131 (liabilities section)
        if self._is_bank_od(text_lower) and self._is_liability_section(section_lower):
            return _match("Working Capital Bank Finance - Bank 1",
                          "Current Liability", "SSSS-011", 0.90)

        # DIR-001: Director / Promoter Unsecured Loans → R152 (liabilities section)
        if self._is_director_loan(text_lower) and self._is_liability_section(section_lower):
            return _match("Unsecured Loans - Quasi Equity",
                          "Term Liabilities", "DIR-001", 0.90)

        # FX-001: Forex / Foreign Exchange Fluctuation → R32 (gain) or R91 (loss)
        if self._is_forex(text_lower):
            if "loss" in text_lower or (amount is not None and amount < 0):
                return _match("Loss on Exchange Fluctuations",
                              "Non-operating Expense", "FX-001-loss", 0.93)
            else:
                return _match("Gain on Exchange Fluctuations",
                              "Non-operating Income", "FX-001-gain", 0.93)

        # B-002: ALL_CAPS vendor name in Trading balance sheet → Sundry Creditors
        if (
            industry == "trading"
            and self._is_vendor_name(text)
            and self._is_liability_section(section_lower)
        ):
            return _match("Sundry Creditors for goods",
                          "Current Liability", "B-002", 0.85)

        return None  # No rule fired — continue to fuzzy/AI

    # ══════════════════════════════════════════════════════════════════════
    # PATTERN DEFINITIONS — compiled regexes (class-level for performance)
    # ══════════════════════════════════════════════════════════════════════

    # ── Existing V1 patterns ─────────────────────────────────────────────

    _VEHICLE_TERMS = re.compile(
        r"\b(motor\s*vehicle|two[\s-]?wheeler|motorcycle|scooter|car|truck|lorry|"
        r"tempo|van|auto\s*rickshaw|vehicle)\b",
        re.IGNORECASE,
    )

    _ELECTRONIC_TERMS = re.compile(
        r"\b(cell\s*phone|mobile|laptop|computer|desktop|tablet|printer|"
        r"scanner|projector|ups|server)\b",
        re.IGNORECASE,
    )

    _FREIGHT_INWARD_TERMS = re.compile(
        r"\b(carriage\s*(inward|in)|freight\s*(inward|charges?)|"
        r"packing\s*(and\s*)?forwarding|transportation\s*charges?|"
        r"loading\s*charges?)\b",
        re.IGNORECASE,
    )

    _FREIGHT_TERMS = re.compile(
        r"\b(carriage\s*(inward|outward|in|out)|packing\s*(and\s*)?forwarding|"
        r"freight\s*(charges?|inward|outward)?|loading\s*charges?|"
        r"transportation\s*charges?)\b",
        re.IGNORECASE,
    )

    _GOVT_SECURITY_DEPOSIT_TERMS = re.compile(
        r"\b(electricity\s*deposit|telephone\s*deposit|electric(ity)?\s*deposit|"
        r"gem\s*caution\s*deposit|earnest\s*money|caution\s*deposit|"
        r"security\s*deposit\s*(with\s*)?(government|govt|electricity|telephone|gseb|bsnl|mseb))\b",
        re.IGNORECASE,
    )

    _PRIVATE_SECURITY_DEPOSIT_TERMS = re.compile(
        r"\bdeposit\b.{0,30}\b(landlord|private|lessor|owner)\b|"
        r"\b(landlord|private|lessor|owner)\b.{0,30}\bdeposit\b",
        re.IGNORECASE,
    )

    _GST_PURCHASE = re.compile(
        r"purchases?\s*@\s*\d+(\.\d+)?\s*%",
        re.IGNORECASE,
    )

    _PURCHASE_RETURN = re.compile(
        r"\b(less\s*:?\s*)?(purchase\s*return|return\s*(of|on)?\s*purchase|"
        r"purchase\s*returns?)\b",
        re.IGNORECASE,
    )

    _SALES_RETURN = re.compile(
        r"\b(less\s*:?\s*)?(sale\s*return|sales?\s*returns?|return\s*(of|on)?\s*sales?)\b",
        re.IGNORECASE,
    )

    _JOB_WORK_TERMS = re.compile(
        r"\b(job\s*work|processing\s*charges?)\b",
        re.IGNORECASE,
    )

    _REPAIRS_MAINTENANCE_TERMS = re.compile(
        r"\b(repair|r\s*&\s*m|r\s*and\s*m|maintenance)\b",
        re.IGNORECASE,
    )

    _STOCK_IN_TRADE_TERMS = re.compile(
        r"\bstock[\s-]*in[\s-]*trade\b|\btrading\s*stock\b",
        re.IGNORECASE,
    )

    _GRATUITY_PROVISION_TERMS = re.compile(
        r"\bprovision\s*(for\s*)?gratuity\b|\bgratuity\s*(liability|provision)\b",
        re.IGNORECASE,
    )

    _INSURANCE_CLAIM_TERMS = re.compile(
        r"\binsurance\s*claim\b|\bclaim\s*(from|received)\s*insurance\b",
        re.IGNORECASE,
    )

    _FREIGHT_OUTWARD_DISCOUNT_TERMS = re.compile(
        r"\bfreight\s*out(ward)?\b|"
        r"\bdiscount\s*allowed\b|\btrade\s*discount\b|\bsales?\s*promotion\b",
        re.IGNORECASE,
    )

    _ADMIN_CATCHALL_TERMS = re.compile(
        r"\btour\s*(and|&)?\s*travel\b|\bconsultancy\s*fees?\b|"
        r"\bprofessional\s*charges?\b|\bgeneral\s*expenses?\b|"
        r"\bmiscellaneous\s*exp\w*\b|\bsundry\s*expenses?\b|"
        r"^insurance$|insurance\s*(premium|charges?)\b",
        re.IGNORECASE,
    )

    _LIABILITY_WRITTEN_OFF_TERMS = re.compile(
        r"\bliabilit(y|ies)\s*written\s*(off|back)\b|"
        r"\bexcess\s*provision\s*written\s*back\b|\bold\s*payable\b",
        re.IGNORECASE,
    )

    _HAMALI_CARTAGE_TERMS = re.compile(
        r"\b(hamali|cooly|coolie|cartage|mathadi|loading\s+unloading)\b",
        re.IGNORECASE,
    )

    # ── New V2 patterns (7-company analysis, 2026-03-22) ─────────────────

    # SSSS-006: Tempo/Van/Auto CHARGES (goods transport, NOT vehicle purchase)
    _TEMPO_VAN_CHARGES_TERMS = re.compile(
        r"\btempo.{0,15}charges?\b|\bvan\s*charges?\b|\bbullock\s*cart\b|"
        r"\brickshaw\s*charges?\b|\btaxi.{0,10}tempo\b",
        re.IGNORECASE,
    )

    # C-005: ECGS / ECLGS / ECLGC government-guaranteed loans
    _ECGS_ECLGS_TERMS = re.compile(
        r"\b(ecgs|eclgs|eclgc)\b",
        re.IGNORECASE,
    )

    # C-006: Sellers / Buyers / Suppliers Credit (import financing)
    _SELLERS_CREDIT_TERMS = re.compile(
        r"\b(sellers?\s*credit|suppliers?\s*credit|buyers?\s*credit)\b",
        re.IGNORECASE,
    )

    # C-007: Channel Financing / Supply Chain Finance
    _CHANNEL_FINANCING_TERMS = re.compile(
        r"\bchannel\s*financ\w*\b|\bsupply\s*chain\s*financ\w*\b|"
        r"\bvendor\s*financ\w*\b",
        re.IGNORECASE,
    )

    # C-008: Inland LC Discounting
    _INLAND_LC_TERMS = re.compile(
        r"\binland\s*lc\b|\blc\s*discounting\b|\bletter\s*of\s*credit\s*discounting\b|"
        r"\bin\s*land\s*lc\b",
        re.IGNORECASE,
    )

    # C-009: Bill Discounting Charges
    _BILL_DISCOUNTING_TERMS = re.compile(
        r"\bbill\s*discounting\b|\bdiscount\s*(on|of)\s*bills?\b",
        re.IGNORECASE,
    )

    # SRP-001 / SSSS-014: Customs Duty on Import
    _CUSTOMS_DUTY_TERMS = re.compile(
        r"\bcustoms?\s*duty\b|\bimport\s*duty\b|\bbasic\s*customs\s*duty\b|\bbcd\b",
        re.IGNORECASE,
    )

    # BCIPL-016: Capital Advances
    _CAPITAL_ADVANCE_TERMS = re.compile(
        r"\bcapital\s*advance\b|\badvance.{0,20}capital\s*goods?\b",
        re.IGNORECASE,
    )

    # BCIPL-020: Creditors for Capital Goods / Fixed Assets
    _CAPITAL_GOODS_CREDITOR_TERMS = re.compile(
        r"\bcreditor.{0,15}capital\s*goods?\b|\bcreditor.{0,15}fixed\s*assets?\b|"
        r"\bcreditor.{0,15}machiner\w*\b",
        re.IGNORECASE,
    )

    # BCIPL-019: MAT Credit Entitlement
    _MAT_CREDIT_TERMS = re.compile(
        r"\bmat\s*credit\b|\bminimum\s*alternate\s*tax\s*credit\b",
        re.IGNORECASE,
    )

    # BCIPL-018: GST Electronic Cash/Credit Ledger
    _ELECTRONIC_LEDGER_TERMS = re.compile(
        r"\belectronic\s*(cash|credit)\s*ledger\b|\bgst\s*electronic\s*ledger\b",
        re.IGNORECASE,
    )

    # BCIPL-017: GST Input Recoverable
    _GST_INPUT_TERMS = re.compile(
        r"\bgst\s*input\b|\bigst\s*receivable\b|\bcgst\s*receivable\b|"
        r"\bsgst\s*receivable\b|\bduties?\s*(?:and|&)\s*taxes?\b",
        re.IGNORECASE,
    )

    # BCIPL-021: Statutory Dues Payable
    _STATUTORY_DUES_TERMS = re.compile(
        r"\b(bonus|esi|epf|eps|provident\s*fund|profession\s*tax|tds)\s*payable\b|"
        r"\bgst\s*payable\b|\bstatutory\s*(dues?|liabilit\w*)\b",
        re.IGNORECASE,
    )

    # SSSS-003: Cutting / Slitting Labour Charges
    _CUTTING_SLITTING_TERMS = re.compile(
        r"\bcutting\s*(labour|labor)?\s*charges?\b|\bslitting\s*(labour|labor)?\s*charges?\b|"
        r"\bpolishing\s*charges?\b",
        re.IGNORECASE,
    )

    # SSSS-007 / BCIPL-014: Weighment / Testing / Inspection
    _WEIGHMENT_TESTING_TERMS = re.compile(
        r"\bweigh(ment|bridge)\s*(charges?|expenses?)?\b|"
        r"\btesting\s*(fees?|charges?)\b|\bmaterial\s*testing\b|"
        r"\bquality\s*testing\b|\binspection\s*charges?\b",
        re.IGNORECASE,
    )

    # SLI-009: Capital WIP / Under Construction
    _CAPITAL_WIP_TERMS = re.compile(
        r"\bcapital\s*w\.?i\.?p\.?\b|\bunder\s*(construction|installation|fabrication)\b|"
        r"\bplant\s*under\s*installation\b|\bmoulds?\s*[-\u2013]\s*wip\b",
        re.IGNORECASE,
    )

    # SLI-008: Moulds / Dies / Jigs & Fixtures
    _MOULDS_DIES_TERMS = re.compile(
        r"\bmoulds?\b|\bdies\b|\bjigs?\s*(and|&)\s*fixtures?\b|"
        r"\bmanufacturing\s*tooling\b|\bshoe\s*moulds?\b",
        re.IGNORECASE,
    )

    # INPL-002: Unbilled Services / Accrued Revenue
    _UNBILLED_SERVICES_TERMS = re.compile(
        r"\bunbilled\s*(services?|revenue)\b|\brevenue\s*in\s*excess\b|"
        r"\bwork\s*completed\s*not\s*billed\b|\baccrued\s*revenue\b",
        re.IGNORECASE,
    )

    # SSSS-002: Discount Receivable (BS asset)
    _DISCOUNT_RECEIVABLE_TERMS = re.compile(
        r"\bdiscount\s*receivable\b|\bvendor\s*rebate\s*receivable\b|"
        r"\bquantity\s*discount\s*receivable\b",
        re.IGNORECASE,
    )

    # KR-001: Partners' Capital Account
    _PARTNERS_CAPITAL_TERMS = re.compile(
        r"\bpartners?\W?\s*capital\b|\bcapital\s*account\b",
        re.IGNORECASE,
    )

    # SSSS-013: Advance Income Tax / TDS Receivable
    _ADVANCE_TAX_TERMS = re.compile(
        r"\badvance\s*(income\s*)?tax\b|\bincome\s*tax\s*(paid|refund)\b|"
        r"\btds\s*(excess|receivable)\b|\btcs\s*receivable\b|"
        r"\bcash\s*with\s*income\s*tax\b",
        re.IGNORECASE,
    )

    # SLI-002: Factory / Manufacturing Rent
    _FACTORY_RENT_TERMS = re.compile(
        r"\bfactory\s*rent\b|\bplant\s*rent\b|\bproduction\s*premises?\s*rent\b",
        re.IGNORECASE,
    )

    # SLI-003: Royalty / Technical Know-how
    _ROYALTY_TERMS = re.compile(
        r"\broyalt(y|ies)\b|\bmould\s*usage\b|\btechnical\s*know[\s-]*how\b|"
        r"\btechnology\s*transfer\b",
        re.IGNORECASE,
    )

    # SLI-004: Packing Materials (manufacturing input)
    _PACKING_MATERIALS_TERMS = re.compile(
        r"\bpacking\s*materials?\b|\bpackaging\s*cost\b",
        re.IGNORECASE,
    )

    # BCIPL-002: Scrap / Other Materials Consumed
    _SCRAP_MATERIALS_TERMS = re.compile(
        r"\bother\s*materials?\s*consumed\b|\bscrap\s*consumption\b|"
        r"\bless\s*:?\s*scrap\b",
        re.IGNORECASE,
    )

    # SELL-001: Selling & Distribution / Carriage Outward
    _SELLING_DISTRIBUTION_TERMS = re.compile(
        r"\bselling\s*(?:and|&)\s*distribution\b|\bcarriage\s*outward\b|"
        r"\bscrap\s*loading\b",
        re.IGNORECASE,
    )

    # BCIPL-006 / SSSS-008: Interest on Unsecured / Director / Promoter Loans
    _INTEREST_UNSECURED_TERMS = re.compile(
        r"\binterest\s*(paid\s*)?(on\s*)?(unsecured|director|promoter)\s*loan\b|"
        r"\binterest\s*on\s*loan\s*from\s*(relatives|directors|promoters)\b",
        re.IGNORECASE,
    )

    # KR-003: Interest to Partners
    _INTEREST_PARTNERS_TERMS = re.compile(
        r"\binterest\s*to\s*partners?\b|\bpartners?\W?\s*interest\b|"
        r"\binterest\s*on\s*partners?\W?\s*capital\b|"
        r"\binterest\s*paid\s*to\s*partners?\b",
        re.IGNORECASE,
    )

    # SSSS-009: Interest on Trading / Trade Credit
    _INTEREST_TRADING_TERMS = re.compile(
        r"\binterest\s*(paid\s*)?(on\s*)?trading\b|\binterest\s*on\s*trade\s*credit\b|"
        r"\btrading\s*interest\b|\binterest\s*on\s*purchases?\b",
        re.IGNORECASE,
    )

    # SSSS-001: Vendor Quantity Discounts / Supplier Rebates
    _VENDOR_DISCOUNT_TERMS = re.compile(
        r"\bquantity\s*discount\s*received\b|\bvendor\s*rebate\b|"
        r"\bjsl.{0,10}discount\b|\bjshl.{0,10}discount\b|\bsail.{0,10}discount\b|"
        r"\bdiscount\s*(received|on\s*purchase)\b|\bpurchase\s*discount\b",
        re.IGNORECASE,
    )

    # BCIPL-001: Directors Remuneration
    _DIRECTORS_REMUNERATION_TERMS = re.compile(
        r"\bdirector.{0,15}remuneration\b|\bmanaging\s*director.{0,10}salary\b|"
        r"\bmd\s*salary\b|\bkmp\s*remuneration\b|\bmanagerial\s*remuneration\b",
        re.IGNORECASE,
    )

    # KR-002: Partners' Salary / Remuneration
    _PARTNERS_SALARY_TERMS = re.compile(
        r"\bsalary\s*to\s*partners?\b|\bpartners?\W?\s*(remuneration|salary)\b|"
        r"\bremuneration\s*to\s*partners?\b",
        re.IGNORECASE,
    )

    # BCIPL-022: Duty Drawback / Export Incentive
    _DUTY_DRAWBACK_TERMS = re.compile(
        r"\bduty\s*drawback\b|\bduty\s*credit\s*scrips?\b|"
        r"\bexport\s*incentive\b|\bmeis\b|\brodtep\b|\bdepb\b",
        re.IGNORECASE,
    )

    # SRP-003: CFS / Clearing / Port Charges
    _CFS_CLEARING_TERMS = re.compile(
        r"\bcfs\s*charges?\b|\bclearance\s*charges?\b|\bport\s*clearance\b|"
        r"\bliner\s*charges?\b|\bocean\s*freight\b|\bdetention\s*charges?\b|"
        r"\bclearing\s*expenses?\b",
        re.IGNORECASE,
    )

    # SLI-012 / INPL-001: Service Revenue
    _SERVICE_REVENUE_TERMS = re.compile(
        r"\bsale\s*of\s*services?\b|\brevenue\s*from\s*services?\b|"
        r"\bservice\s*(income|charges?)\b|\bjob\s*work\s*(income|revenue)\b|"
        r"\bcontract\s*revenue\b|\btechnical\s*services?\s*income\b|"
        r"\bprocessing\s*charges?\s*received\b|\bconversion\s*charges?\s*income\b",
        re.IGNORECASE,
    )

    # SSSS-011: Bank OD / CC Accounts
    _BANK_OD_TERMS = re.compile(
        r"\bod\s*a/?c\b|\bo/d\b|\boverdraft\b|\bcash\s*credit\s*(limit|a/?c)\b|"
        r"\bcc\s*(limit|a/?c|facility)\b|\bwcdl\b",
        re.IGNORECASE,
    )

    # DIR-001: Director / Promoter Unsecured Loans (BS liabilities)
    _DIRECTOR_LOAN_TERMS = re.compile(
        r"\bloans?\s*from\s*directors?\b|\bdirector\s*loan\b|\bpromoter\s*loan\b|"
        r"\bdue\s*to\s*directors?\b|"
        r"\bunsecured\s*loan.{0,20}(director|promoter|relative)\b",
        re.IGNORECASE,
    )

    # FX-001: Forex / Foreign Exchange Fluctuation
    _FOREX_TERMS = re.compile(
        r"\bforex\b|\bforeign\s*exchange\b|\bexchange\s*rate\s*(?:difference|fluctuation)\b|"
        r"\bforeign\s*currency\s*(?:fluctuation|translation)\b|"
        r"\bexchange\s*(?:gain|loss|fluctuation)\b",
        re.IGNORECASE,
    )

    # ── CA-verified V3 patterns (2026-03-26) ─────────────────────────────

    # CA-001: Staff Welfare (industry-dependent: mfg→R45, svc→R67)
    _STAFF_WELFARE_TERMS = re.compile(
        r"\bstaff\s*welfare\b",
        re.IGNORECASE,
    )

    # CA-002: Standalone Bonus (NOT combined with salary+wages; industry-dependent)
    _BONUS_STANDALONE_TERMS = re.compile(
        r"\bbonus\b",
        re.IGNORECASE,
    )
    # Pattern to detect combined "salary/wages and bonus" lines — used to EXCLUDE from CA-002
    _BONUS_COMBINED_TERMS = re.compile(
        r"\bsalar(y|ies).*\bwages?\b|\bwages?.*\bbonus\b|\bsalar(y|ies).*\bbonus\b",
        re.IGNORECASE,
    )

    # CA-003: Employee Benefits Expense (combined line; industry-dependent)
    _EMPLOYEE_BENEFITS_TERMS = re.compile(
        r"\bemployee\s*benefit\w*\s*expense\b",
        re.IGNORECASE,
    )

    # CA-004: Gratuity standalone (NOT "provision for gratuity" — MSL-003 handles that)
    _GRATUITY_STANDALONE_TERMS = re.compile(
        r"\bgratuity\b",
        re.IGNORECASE,
    )

    # CA-005: EPF / Provident Fund contribution
    _EPF_TERMS = re.compile(
        r"\b(epf|e\.?p\.?f|provident\s*fund)\b|"
        r"\bcontribution\s*to\s*(epf|provident\s*fund)\b",
        re.IGNORECASE,
    )

    # CA-006: ESI contribution
    _ESI_TERMS = re.compile(
        r"\b(esi|e\.?s\.?i\.?c?)\b|"
        r"\bcontribution\s*to\s*(esi|e\.?s\.?i)\b",
        re.IGNORECASE,
    )

    # CA-007: Staff Mess / Canteen
    _STAFF_MESS_TERMS = re.compile(
        r"\bstaff\s*mess\b|\bcanteen\s*expense\b",
        re.IGNORECASE,
    )

    # CA-008: "Salary, Wages and Bonus" combined line → R45 (must fire BEFORE generic bonus)
    _SALARY_WAGES_BONUS_TERMS = re.compile(
        r"\bsalar(y|ies)\s*(,|and|&)\s*wages?\b",
        re.IGNORECASE,
    )

    # CA-009: Labour Charges (generic)
    _LABOUR_CHARGES_TERMS = re.compile(
        r"\blabou?r\s*charges?\b",
        re.IGNORECASE,
    )

    # CA-010: Leave Encashment (context-dependent: BS→R249, P&L→R45)
    _LEAVE_ENCASHMENT_TERMS = re.compile(
        r"\bleave\s*encashment\b|\bleave\s*salary\b",
        re.IGNORECASE,
    )

    # CA-011: Power / Electricity (industry-dependent; NOT electricity deposit)
    _POWER_ELECTRIC_TERMS = re.compile(
        r"\b(electric\w*\s*(charges?|expense)|power\s*(charges?|expense)|electricity)\b",
        re.IGNORECASE,
    )

    # CA-012: Interest on Tax Delay → R84
    _INTEREST_TAX_DELAY_TERMS = re.compile(
        r"\binterest\s*(on\s*)?(delay|late)\s*(in\s*)?(payment\s*of\s*)?tax\b|"
        r"\binterest\s*on\s*tax\b",
        re.IGNORECASE,
    )

    # CA-013: Liquidated Damages → R71
    _LIQUIDATED_DAMAGES_TERMS = re.compile(
        r"\bliquidated\s*damages?\b",
        re.IGNORECASE,
    )

    # CA-014: Loan Processing Fee → R85 Bank Charges
    _LOAN_PROCESSING_FEE_TERMS = re.compile(
        r"\bloan\s*process\w*\s*fee\b|\bprocess\w*\s*fee\b|\bloan\s*process\w*\s*charge\b",
        re.IGNORECASE,
    )

    # CA-015: Vehicle HP / Hire Purchase Current Maturities → R148
    _VEHICLE_HP_CURRENT_TERMS = re.compile(
        r"\bvehicle\s*(hp|hire\s*purchase)\s*current\b|"
        r"\bcurrent\s*maturit\w*\s*.*vehicle\b|"
        r"\bcurrent\s*portion\s*.*vehicle\b",
        re.IGNORECASE,
    )

    # CA-016: Other Long-Term Liabilities → R149
    _OTHER_LT_LIABILITIES_TERMS = re.compile(
        r"\bother\s*(long\s*term|lt)\s*liabilit\w*\b",
        re.IGNORECASE,
    )

    # CA-017: Advances to Suppliers → R220
    _ADVANCE_TO_SUPPLIERS_TERMS = re.compile(
        r"\badvance\w*\s*(to\s*)?supplier\w*\b",
        re.IGNORECASE,
    )

    # CA-018: Security Deposit (generic — after C-004-govt and C-004-private)
    _SECURITY_DEPOSIT_GENERIC_TERMS = re.compile(
        r"\bsecurity\s*deposit\b",
        re.IGNORECASE,
    )

    # CA-019: Licence / Subscription Fees → R71
    _LICENCE_SUBSCRIPTION_TERMS = re.compile(
        r"\b(licen[cs]e|subscription)\s*(fee|charge|expense)?\b",
        re.IGNORECASE,
    )

    # CA-020: Insurance Premium → R71 (before MSL-008 catchall)
    _INSURANCE_PREMIUM_TERMS = re.compile(
        r"\binsurance\s*(premium|expense|charge)?\b",
        re.IGNORECASE,
    )

    # CA-021: Subsidy / Government Grant (context-dependent: BS→R125, P&L→R33)
    _SUBSIDY_GRANT_TERMS = re.compile(
        r"\b(subsidy|government\s*grant|govt\s*grant|capital\s*subsidy|revenue\s*subsidy)\b",
        re.IGNORECASE,
    )

    # CA-022: Stores & Spares (import vs indigenous)
    _STORES_SPARES_TERMS = re.compile(
        r"\bstores?\s*(and|&)\s*spares?\b|\bspare\s*parts?\b",
        re.IGNORECASE,
    )

    # CA-023: Issue of Bonus Shares → force doubt
    _BONUS_SHARE_ISSUE_TERMS = re.compile(
        r"\b(issue|issuance)\s*(of\s*)?bonus\s*shares?\b|"
        r"\bbonus\s*shares?\s*(issue|allot)\b",
        re.IGNORECASE,
    )

    # CA-024: Preliminary / Pre-operative Expenses Written Off → R75
    _PRELIMINARY_EXPENSE_TERMS = re.compile(
        r"\b(preliminary|pre[\s-]?operative|incorporation)\s*(expenses?|costs?)?\s*"
        r"(written\s*off|amortis|w/?o)\b|"
        r"\bmisc\w*\s*exp\w*\s*written\s*off\b",
        re.IGNORECASE,
    )

    # ══════════════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ══════════════════════════════════════════════════════════════════════

    # ── Existing V1 helpers ──────────────────────────────────────────────

    def _is_vehicle(self, text: str) -> bool:
        return bool(self._VEHICLE_TERMS.search(text))

    def _is_electronic_device(self, text: str) -> bool:
        return bool(self._ELECTRONIC_TERMS.search(text))

    def _is_freight_inward(self, text: str) -> bool:
        return bool(self._FREIGHT_INWARD_TERMS.search(text))

    def _is_freight(self, text: str) -> bool:
        return bool(self._FREIGHT_TERMS.search(text))

    def _is_govt_security_deposit(self, text: str) -> bool:
        return bool(self._GOVT_SECURITY_DEPOSIT_TERMS.search(text))

    def _is_private_security_deposit(self, text: str) -> bool:
        return bool(self._PRIVATE_SECURITY_DEPOSIT_TERMS.search(text))

    def _is_security_deposit(self, text: str) -> bool:
        return self._is_govt_security_deposit(text) or self._is_private_security_deposit(text)

    def _is_gst_purchase(self, text: str) -> bool:
        return bool(self._GST_PURCHASE.search(text))

    def _is_purchase_return(self, text: str) -> bool:
        return bool(self._PURCHASE_RETURN.search(text))

    def _is_sales_return(self, text: str) -> bool:
        return bool(self._SALES_RETURN.search(text))

    def _is_job_work(self, text: str) -> bool:
        return bool(self._JOB_WORK_TERMS.search(text))

    def _is_repairs_maintenance(self, text: str) -> bool:
        return bool(self._REPAIRS_MAINTENANCE_TERMS.search(text))

    def _is_stock_in_trade(self, text: str) -> bool:
        return bool(self._STOCK_IN_TRADE_TERMS.search(text))

    def _is_gratuity_provision(self, text: str) -> bool:
        return bool(self._GRATUITY_PROVISION_TERMS.search(text))

    def _is_insurance_claim(self, text: str) -> bool:
        return bool(self._INSURANCE_CLAIM_TERMS.search(text))

    def _is_freight_outward_or_discount(self, text: str) -> bool:
        return bool(self._FREIGHT_OUTWARD_DISCOUNT_TERMS.search(text))

    def _is_admin_catchall(self, text: str) -> bool:
        return bool(self._ADMIN_CATCHALL_TERMS.search(text))

    def _is_liability_written_off(self, text: str) -> bool:
        return bool(self._LIABILITY_WRITTEN_OFF_TERMS.search(text))

    def _is_hamali_cartage(self, text: str) -> bool:
        return bool(self._HAMALI_CARTAGE_TERMS.search(text))

    # ── Section helpers ──────────────────────────────────────────────────

    def _is_income_section(self, section: str) -> bool:
        return any(w in section for w in ("income", "receipt", "revenue", "credit"))

    def _is_liability_section(self, section: str) -> bool:
        return any(w in section for w in ("liabilit", "creditor", "payable", "sundry",
                                          "borrowing", "loan", "unsecured"))

    def _is_inventory_section(self, section: str) -> bool:
        return any(w in section for w in ("inventor", "current asset", "stock"))

    def _is_longterm_section(self, section: str) -> bool:
        return any(w in section for w in ("long", "non-current", "provision"))

    def _is_vendor_name(self, text: str) -> bool:
        """True if text looks like a vendor name: all caps, 3+ chars, no numbers."""
        words = text.split()
        if len(words) < 1 or len(text) < 4:
            return False
        return all(re.match(r"^[A-Z]+$", w) for w in words if len(w) > 1)

    # ── New V2 helpers ───────────────────────────────────────────────────

    def _is_tempo_van_charges(self, text: str) -> bool:
        return bool(self._TEMPO_VAN_CHARGES_TERMS.search(text))

    def _is_ecgs_eclgs(self, text: str) -> bool:
        return bool(self._ECGS_ECLGS_TERMS.search(text))

    def _is_sellers_credit(self, text: str) -> bool:
        return bool(self._SELLERS_CREDIT_TERMS.search(text))

    def _is_channel_financing(self, text: str) -> bool:
        return bool(self._CHANNEL_FINANCING_TERMS.search(text))

    def _is_inland_lc(self, text: str) -> bool:
        return bool(self._INLAND_LC_TERMS.search(text))

    def _is_bill_discounting(self, text: str) -> bool:
        return bool(self._BILL_DISCOUNTING_TERMS.search(text))

    def _is_customs_duty(self, text: str) -> bool:
        return bool(self._CUSTOMS_DUTY_TERMS.search(text))

    def _is_capital_advance(self, text: str) -> bool:
        return bool(self._CAPITAL_ADVANCE_TERMS.search(text))

    def _is_capital_goods_creditor(self, text: str) -> bool:
        return bool(self._CAPITAL_GOODS_CREDITOR_TERMS.search(text))

    def _is_mat_credit(self, text: str) -> bool:
        return bool(self._MAT_CREDIT_TERMS.search(text))

    def _is_electronic_ledger(self, text: str) -> bool:
        return bool(self._ELECTRONIC_LEDGER_TERMS.search(text))

    def _is_gst_input(self, text: str) -> bool:
        return bool(self._GST_INPUT_TERMS.search(text))

    def _is_statutory_dues(self, text: str) -> bool:
        return bool(self._STATUTORY_DUES_TERMS.search(text))

    def _is_cutting_slitting(self, text: str) -> bool:
        return bool(self._CUTTING_SLITTING_TERMS.search(text))

    def _is_weighment_testing(self, text: str) -> bool:
        return bool(self._WEIGHMENT_TESTING_TERMS.search(text))

    def _is_capital_wip(self, text: str) -> bool:
        return bool(self._CAPITAL_WIP_TERMS.search(text))

    def _is_moulds_dies(self, text: str) -> bool:
        return bool(self._MOULDS_DIES_TERMS.search(text))

    def _is_unbilled_services(self, text: str) -> bool:
        return bool(self._UNBILLED_SERVICES_TERMS.search(text))

    def _is_discount_receivable(self, text: str) -> bool:
        return bool(self._DISCOUNT_RECEIVABLE_TERMS.search(text))

    def _is_partners_capital(self, text: str) -> bool:
        return bool(self._PARTNERS_CAPITAL_TERMS.search(text))

    def _is_advance_tax(self, text: str) -> bool:
        return bool(self._ADVANCE_TAX_TERMS.search(text))

    def _is_factory_rent(self, text: str) -> bool:
        return bool(self._FACTORY_RENT_TERMS.search(text))

    def _is_royalty(self, text: str) -> bool:
        return bool(self._ROYALTY_TERMS.search(text))

    def _is_packing_materials(self, text: str) -> bool:
        return bool(self._PACKING_MATERIALS_TERMS.search(text))

    def _is_scrap_materials(self, text: str) -> bool:
        return bool(self._SCRAP_MATERIALS_TERMS.search(text))

    def _is_selling_distribution(self, text: str) -> bool:
        return bool(self._SELLING_DISTRIBUTION_TERMS.search(text))

    def _is_interest_unsecured(self, text: str) -> bool:
        return bool(self._INTEREST_UNSECURED_TERMS.search(text))

    def _is_interest_partners(self, text: str) -> bool:
        return bool(self._INTEREST_PARTNERS_TERMS.search(text))

    def _is_interest_trading(self, text: str) -> bool:
        return bool(self._INTEREST_TRADING_TERMS.search(text))

    def _is_vendor_discount(self, text: str) -> bool:
        return bool(self._VENDOR_DISCOUNT_TERMS.search(text))

    def _is_directors_remuneration(self, text: str) -> bool:
        return bool(self._DIRECTORS_REMUNERATION_TERMS.search(text))

    def _is_partners_salary(self, text: str) -> bool:
        return bool(self._PARTNERS_SALARY_TERMS.search(text))

    def _is_duty_drawback(self, text: str) -> bool:
        return bool(self._DUTY_DRAWBACK_TERMS.search(text))

    def _is_cfs_clearing(self, text: str) -> bool:
        return bool(self._CFS_CLEARING_TERMS.search(text))

    def _is_service_revenue(self, text: str) -> bool:
        return bool(self._SERVICE_REVENUE_TERMS.search(text))

    def _is_bank_od(self, text: str) -> bool:
        return bool(self._BANK_OD_TERMS.search(text))

    def _is_director_loan(self, text: str) -> bool:
        return bool(self._DIRECTOR_LOAN_TERMS.search(text))

    def _is_forex(self, text: str) -> bool:
        return bool(self._FOREX_TERMS.search(text))

    # ── CA-verified V3 helpers (2026-03-26) ──────────────────────────────

    def _is_staff_welfare(self, text: str) -> bool:
        return bool(self._STAFF_WELFARE_TERMS.search(text))

    def _is_bonus_standalone(self, text: str) -> bool:
        """True for standalone "Bonus" only — not when combined with salary+wages."""
        if self._BONUS_COMBINED_TERMS.search(text):
            return False
        return bool(self._BONUS_STANDALONE_TERMS.search(text))

    def _is_employee_benefits_expense(self, text: str) -> bool:
        return bool(self._EMPLOYEE_BENEFITS_TERMS.search(text))

    def _is_gratuity_standalone(self, text: str) -> bool:
        """True for gratuity but NOT provision for gratuity (MSL-003 handles that)."""
        if self._GRATUITY_PROVISION_TERMS.search(text):
            return False
        return bool(self._GRATUITY_STANDALONE_TERMS.search(text))

    def _is_epf_contribution(self, text: str) -> bool:
        return bool(self._EPF_TERMS.search(text))

    def _is_esi_contribution(self, text: str) -> bool:
        return bool(self._ESI_TERMS.search(text))

    def _is_staff_mess(self, text: str) -> bool:
        return bool(self._STAFF_MESS_TERMS.search(text))

    def _is_salary_wages_bonus_combined(self, text: str) -> bool:
        return bool(self._SALARY_WAGES_BONUS_TERMS.search(text))

    def _is_labour_charges(self, text: str) -> bool:
        return bool(self._LABOUR_CHARGES_TERMS.search(text))

    def _is_leave_encashment(self, text: str) -> bool:
        return bool(self._LEAVE_ENCASHMENT_TERMS.search(text))

    def _is_power_electric(self, text: str) -> bool:
        """True for power/electricity expenses but NOT electricity deposits."""
        if "electricity deposit" in text or "electric deposit" in text:
            return False
        return bool(self._POWER_ELECTRIC_TERMS.search(text))

    def _is_interest_tax_delay(self, text: str) -> bool:
        return bool(self._INTEREST_TAX_DELAY_TERMS.search(text))

    def _is_liquidated_damages(self, text: str) -> bool:
        return bool(self._LIQUIDATED_DAMAGES_TERMS.search(text))

    def _is_loan_processing_fee(self, text: str) -> bool:
        return bool(self._LOAN_PROCESSING_FEE_TERMS.search(text))

    def _is_vehicle_hp_current(self, text: str) -> bool:
        return bool(self._VEHICLE_HP_CURRENT_TERMS.search(text))

    def _is_other_lt_liabilities(self, text: str) -> bool:
        return bool(self._OTHER_LT_LIABILITIES_TERMS.search(text))

    def _is_advance_to_suppliers(self, text: str) -> bool:
        return bool(self._ADVANCE_TO_SUPPLIERS_TERMS.search(text))

    def _is_security_deposit_generic(self, text: str) -> bool:
        """Generic security deposit — only fires if more specific C-004 rules didn't match."""
        return bool(self._SECURITY_DEPOSIT_GENERIC_TERMS.search(text))

    def _is_licence_subscription(self, text: str) -> bool:
        return bool(self._LICENCE_SUBSCRIPTION_TERMS.search(text))

    def _is_insurance_premium(self, text: str) -> bool:
        """True for insurance premium/expense. Excludes insurance claims (MSL-006 handles those)."""
        if self._is_insurance_claim(text):
            return False
        return bool(self._INSURANCE_PREMIUM_TERMS.search(text))

    def _is_subsidy_grant(self, text: str) -> bool:
        return bool(self._SUBSIDY_GRANT_TERMS.search(text))

    def _is_stores_spares(self, text: str) -> bool:
        return bool(self._STORES_SPARES_TERMS.search(text))

    def _is_bonus_share_issue(self, text: str) -> bool:
        return bool(self._BONUS_SHARE_ISSUE_TERMS.search(text))

    def _is_preliminary_expense_writeoff(self, text: str) -> bool:
        return bool(self._PRELIMINARY_EXPENSE_TERMS.search(text))

    def _is_reserves_section(self, section: str) -> bool:
        """True if section context is reserves / equity (for CA-021 subsidy BS handling)."""
        return any(w in section for w in ("reserve", "equity", "surplus", "capital"))


# ══════════════════════════════════════════════════════════════════════════════
# Golden Rule Lookup — loads 594 rules from cma_golden_rules_v2.json
# ══════════════════════════════════════════════════════════════════════════════

# Priority ordering: ca_override > ca_interview > legacy
_PRIORITY_ORDER = {"ca_override": 0, "ca_interview": 1, "legacy": 2}

# Fuzzy match threshold for golden rule lookup
_GOLDEN_FUZZY_THRESHOLD = 90


@dataclass
class GoldenRuleResult:
    """Result when a golden rule matches."""

    canonical_sheet_row: int
    canonical_field_name: str
    priority: str          # "ca_override", "ca_interview", "legacy"
    confidence: float
    source: str            # e.g. "CA_rule_contradiction_cross_002"
    rule_id: str           # e.g. "contradiction_cross_002"
    industry_type: str     # "all", "manufacturing", etc.
    source_sheet: str      # "pl", "bs"


def _detect_rules_path() -> Path:
    """Detect the path to cma_golden_rules_v2.json.

    Tries multiple locations to work both inside Docker and locally:
    1. PROJECT_ROOT env var (if set)
    2. Relative to this file: ../../../../CMA_Ground_Truth_v1/reference/
    3. Relative to cwd: CMA_Ground_Truth_v1/reference/
    4. /app/CMA_Ground_Truth_v1/reference/ (Docker)
    """
    filename = "cma_golden_rules_v2.json"
    subpath = os.path.join("CMA_Ground_Truth_v1", "reference", filename)

    # 1. Explicit env var
    project_root = os.environ.get("PROJECT_ROOT")
    if project_root:
        p = Path(project_root) / subpath
        if p.exists():
            return p

    # 2. Relative to this file (backend/app/services/classification/ → project root)
    this_dir = Path(__file__).resolve().parent
    p = this_dir / ".." / ".." / ".." / ".." / subpath
    if p.resolve().exists():
        return p.resolve()

    # 3. Relative to cwd
    p = Path(subpath)
    if p.exists():
        return p.resolve()

    # 4. Docker path
    p = Path("/app") / subpath
    if p.exists():
        return p

    return Path(subpath)  # Return anyway; load will handle FileNotFoundError


class GoldenRuleLookup:
    """Loads and indexes the 594 golden rules from cma_golden_rules_v2.json.

    Provides `find_rule(raw_text, source_sheet, industry_type)` for exact
    and fuzzy matching against the golden rules.

    Build indexes on init:
    - Exact match index: {normalized_fs_item: [rules]}
    - By industry: {industry_type: {normalized_fs_item: [rules]}}
    - By source_sheet: {pl|bs: {normalized_fs_item: [rules]}}

    Lookup priority:
    1. Exact match on normalized text + specific industry + source_sheet
    2. Exact match on normalized text + "all" industry + source_sheet
    3. Fuzzy match (threshold=90) on text, filtered by industry + source_sheet
    4. Within matches, highest priority wins (ca_override > ca_interview > legacy)
    """

    def __init__(self) -> None:
        self._rules: list[dict] = []
        self._exact_index: dict[str, list[dict]] = defaultdict(list)
        self._by_industry: dict[str, dict[str, list[dict]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._by_sheet: dict[str, dict[str, list[dict]]] = defaultdict(
            lambda: defaultdict(list)
        )
        # All fs_item strings for fuzzy matching
        self._all_fs_items: list[str] = []
        self._fs_item_to_rules: dict[str, list[dict]] = defaultdict(list)
        self._loaded = False

        self._load_rules()

    def _load_rules(self) -> None:
        """Load rules from JSON file and build indexes."""
        rules_path = _detect_rules_path()
        try:
            with open(rules_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            raw_rules = data.get("rules", [])
        except FileNotFoundError:
            logger.warning(
                "Golden rules file not found: %s — golden rule lookup disabled",
                rules_path,
            )
            return
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            logger.warning(
                "Failed to parse golden rules file %s: %s — golden rule lookup disabled",
                rules_path,
                exc,
            )
            return

        for rule in raw_rules:
            fs_item = (rule.get("fs_item") or "").strip().lower()
            if not fs_item:
                continue

            industry = (rule.get("industry_type") or "all").strip().lower()
            sheet = (rule.get("source_sheet") or "both").strip().lower()

            # Store normalized fs_item back for lookup
            rule["_normalized"] = fs_item

            self._rules.append(rule)
            self._exact_index[fs_item].append(rule)
            self._by_industry[industry][fs_item].append(rule)
            self._by_sheet[sheet][fs_item].append(rule)
            self._fs_item_to_rules[fs_item].append(rule)

        # Deduplicate fs_items for fuzzy matching
        self._all_fs_items = list(self._fs_item_to_rules.keys())
        self._loaded = bool(self._rules)

        logger.info(
            "Loaded %d golden rules from %s (%d unique fs_items)",
            len(self._rules),
            rules_path,
            len(self._all_fs_items),
        )

    @staticmethod
    def _best_by_priority(rules: list[dict]) -> Optional[dict]:
        """Return the highest-priority rule from a list (ca_override > ca_interview > legacy)."""
        if not rules:
            return None
        return min(rules, key=lambda r: _PRIORITY_ORDER.get(r.get("priority", "legacy"), 99))

    def _filter_by_context(
        self,
        rules: list[dict],
        source_sheet: Optional[str],
        industry_type: Optional[str],
    ) -> list[dict]:
        """Filter rules by source_sheet and industry_type context."""
        filtered = rules
        if source_sheet:
            sheet_lower = source_sheet.lower()
            # Map document_type to source_sheet if needed
            if "profit" in sheet_lower or sheet_lower == "pl":
                sheet_lower = "pl"
            elif "balance" in sheet_lower or sheet_lower == "bs":
                sheet_lower = "bs"
            filtered = [
                r for r in filtered
                if r.get("source_sheet", "both") in (sheet_lower, "both")
            ]
        if industry_type:
            ind_lower = industry_type.lower()
            filtered = [
                r for r in filtered
                if r.get("industry_type", "all") in (ind_lower, "all")
            ]
        return filtered

    def find_rule(
        self,
        raw_text: str,
        source_sheet: Optional[str] = None,
        industry_type: Optional[str] = None,
    ) -> Optional[GoldenRuleResult]:
        """Find the best golden rule match for the given text.

        Parameters
        ----------
        raw_text:       The financial line item text (will be normalized).
        source_sheet:   "pl", "bs", "profit_and_loss", "balance_sheet", or None.
        industry_type:  "manufacturing", "trading", "services", "construction", or None.

        Returns
        -------
        GoldenRuleResult if a match is found, None otherwise.
        """
        if not self._loaded:
            return None

        text = raw_text.strip().lower()
        if not text:
            return None

        # ── Try 1: Exact match on normalized text + specific industry + source_sheet
        exact_rules = self._exact_index.get(text, [])
        if exact_rules:
            if industry_type:
                ind_lower = industry_type.lower()
                specific = [
                    r for r in exact_rules
                    if r.get("industry_type", "all") == ind_lower
                ]
                contextual = self._filter_by_context(specific, source_sheet, None)
                best = self._best_by_priority(contextual)
                if best:
                    return self._to_result(best)

            # ── Try 2: Exact match on normalized text + "all" industry + source_sheet
            all_industry = [
                r for r in exact_rules
                if r.get("industry_type", "all") == "all"
            ]
            contextual = self._filter_by_context(all_industry, source_sheet, None)
            best = self._best_by_priority(contextual)
            if best:
                return self._to_result(best)

            # Exact match without industry/sheet filter
            best = self._best_by_priority(exact_rules)
            if best:
                return self._to_result(best)

        # ── Try 3: Fuzzy match (threshold=90)
        if not self._all_fs_items:
            return None

        try:
            matches = process.extract(
                text,
                self._all_fs_items,
                scorer=fuzz.token_set_ratio,
                limit=5,
            )
        except Exception:
            return None

        for matched_text, score, _ in matches:
            if score < _GOLDEN_FUZZY_THRESHOLD:
                continue

            candidate_rules = self._fs_item_to_rules.get(matched_text, [])
            filtered = self._filter_by_context(candidate_rules, source_sheet, industry_type)
            if not filtered:
                # Try with "all" industry
                filtered = self._filter_by_context(candidate_rules, source_sheet, None)
                filtered = [
                    r for r in filtered
                    if r.get("industry_type", "all") == "all"
                ]
            best = self._best_by_priority(filtered)
            if best:
                result = self._to_result(best)
                # Reduce confidence slightly for fuzzy matches
                result.confidence = round(min(result.confidence, score / 100.0), 4)
                return result

        return None

    @staticmethod
    def _to_result(rule: dict) -> GoldenRuleResult:
        """Convert a raw rule dict to a GoldenRuleResult."""
        return GoldenRuleResult(
            canonical_sheet_row=rule.get("canonical_sheet_row", 0),
            canonical_field_name=rule.get("canonical_field_name", "UNCLASSIFIED"),
            priority=rule.get("priority", "legacy"),
            confidence=rule.get("confidence", 0.85),
            source=rule.get("source", ""),
            rule_id=rule.get("id", ""),
            industry_type=rule.get("industry_type", "all"),
            source_sheet=rule.get("source_sheet", "both"),
        )
