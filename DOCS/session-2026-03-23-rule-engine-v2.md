# Rule Engine V2 — Implementation Log

**Date:** 2026-03-23
**File:** `backend/app/services/classification/rule_engine.py`
**Previous:** ~20 rules, ~559 lines
**After:** 61 unique rule IDs, 62 pattern methods, 1,021 lines

---

## Summary

Implemented 35+ new classification rules from the 7-company analysis (DOCS/rules/*.md) into the Tier 0 deterministic rule engine. The rule engine runs BEFORE fuzzy match and AI, saving API cost and eliminating known classification errors.

---

## Rules Added (by source company)

### BCIPL (Manufacturing) — 8 rules
| Rule ID | Pattern | CMA Row | CMA Field |
|---------|---------|---------|-----------|
| BCIPL-001 | Directors Remuneration | R67 | Salary and staff expenses |
| BCIPL-002 | Scrap / Other Materials Consumed | R44 | Stores and spares consumed (Indigenous) |
| BCIPL-006 | Interest on Unsecured / Director Loans | R83 | Interest on Fixed Loans / Term loans |
| BCIPL-016 | Capital Advances | R236 | Advances to suppliers of capital goods |
| BCIPL-017 | GST Input Recoverable | R219 | Advances recoverable in cash or in kind |
| BCIPL-018 | GST Electronic Cash/Credit Ledger | R237 | Security deposits with government departments |
| BCIPL-019 | MAT Credit Entitlement | R238 | Other non current assets |
| BCIPL-020 | Creditors for Capital Goods | R250 | Other current liabilities |
| BCIPL-021 | Statutory Dues Payable (ESI/PF/TDS/GST) | R246 | Other statutory liabilities (due within 1 year) |
| BCIPL-022 | Duty Drawback / Export Incentive | R34 | Others (Non-Operating Income) |

### SSSS (Steel Trading) — 7 rules
| Rule ID | Pattern | CMA Row | CMA Field |
|---------|---------|---------|-----------|
| SSSS-001 | Vendor Quantity Discounts / Rebates | R42 | Raw Materials Consumed (Indigenous) |
| SSSS-002 | Discount Receivable (BS asset) | R223 | Other Advances / current asset |
| SSSS-003 | Cutting / Slitting Labour Charges | R46 | Processing / Job Work Charges |
| SSSS-006 | Tempo/Van/Auto CHARGES (goods transport) | R47 | Freight and Transportation Charges |
| SSSS-007 | Weighment / Testing / Inspection | R49 | Others (Manufacturing) |
| SSSS-009 | Interest on Trading / Trade Credit | R84 | Interest on Working capital loans |
| SSSS-011 | Bank OD / CC Accounts | R131 | Working Capital Bank Finance - Bank 1 |
| SSSS-013 | Advance Income Tax / TDS Receivable | R221 | Advance Income Tax |

### SLIPL (Shoe Manufacturing) — 6 rules
| Rule ID | Pattern | CMA Row | CMA Field |
|---------|---------|---------|-----------|
| SLI-002 | Factory / Manufacturing Rent | R49 | Others (Manufacturing) |
| SLI-003 | Royalty / Technical Know-how | R49 | Others (Manufacturing) |
| SLI-004 | Packing Materials | R49 | Others (Manufacturing) |
| SLI-008 | Moulds / Dies / Jigs & Fixtures | R162 | Gross Block |
| SLI-009 | Capital WIP / Under Construction | R165 | Capital Work in Progress |
| SLI-012 | Service Revenue / Processing Income | R22 | Domestic Sales |

### MSL (Metal Stamping Manufacturing) — 5 rules
| Rule ID | Pattern | CMA Row | CMA Field |
|---------|---------|---------|-----------|
| MSL-001 | Stock in Trade (Manufacturing) | R201 | Finished Goods |
| MSL-003 | Provision for Gratuity (LT provision) | R153 | Unsecured Loans - Long Term Debt |
| MSL-006 | Insurance Claim Received (income) | R34 | Others (Non-Operating Income) |
| MSL-007 | Freight Outward / Discount (Mfg) | R70 | Advertisements and Sales Promotions |
| MSL-008 | Tour/Travel/Consultancy/Insurance | R71 | Others (Admin) |
| MSL-010 | Liability Written Off | R90 | Sundry Balances Written off |

### SR Papers (Trading) — 2 rules
| Rule ID | Pattern | CMA Row | CMA Field |
|---------|---------|---------|-----------|
| SRP-001 | Customs Duty on Import | R41 | Raw Materials Consumed (Imported) |
| SRP-003 | CFS / Clearing / Port Charges | R49 | Others (Manufacturing) |

### INPL (Nano/Bio Manufacturing) — 1 rule
| Rule ID | Pattern | CMA Row | CMA Field |
|---------|---------|---------|-----------|
| INPL-002 | Unbilled Services / Accrued Revenue | R206 | Domestic Receivables |

### Kurunji Retail (Partnership) — 3 rules
| Rule ID | Pattern | CMA Row | CMA Field |
|---------|---------|---------|-----------|
| KR-001 | Partners' Capital Account | R116 | Issued, Subscribed and Paid up |
| KR-002 | Partners' Salary / Remuneration | R73 | Audit Fees & Directors Remuneration |
| KR-003 | Interest to Partners | R83 | Interest on Fixed Loans / Term loans |

### Cross-Company Rules — 7 rules
| Rule ID | Pattern | CMA Row | CMA Field |
|---------|---------|---------|-----------|
| C-005 | ECGS / ECLGS government loans | R137 | Term Loan Balance Repayable after one year |
| C-006 | Sellers / Buyers / Suppliers Credit | R137 | Term Loan Balance Repayable after one year |
| C-007 | Channel Financing / Supply Chain Finance | R131 | Working Capital Bank Finance - Bank 1 |
| C-008 | Inland LC Discounting | R132 | Working Capital Bank Finance - Bank 2 |
| C-009 | Bill Discounting Charges | R84 | Interest on Working capital loans |
| DIR-001 | Director / Promoter Unsecured Loans | R152 | Unsecured Loans - Quasi Equity |
| FX-001 | Forex / Foreign Exchange Fluctuation | R32/R91 | Gain/Loss on Exchange Fluctuations |
| FRE-001 | Hamali / Cooly / Cartage / Mathadi | R47 | Freight and Transportation Charges |
| SELL-001 | Selling & Distribution / Carriage Outward | R70 | Advertisements and Sales Promotions |

---

## Architectural Decisions

### 1. Rule ordering: SSSS-006 before C-001
"Tempo Charges" (goods transport expense) contains "tempo" which matches C-001's vehicle regex. By placing SSSS-006 (transport charges pattern) BEFORE C-001 (vehicle pattern), we prevent misclassifying transport expenses as fixed assets.

### 2. 9-phase priority ordering
```
Phase 1: C-type (absolute) — highest confidence, always correct
Phase 2: Industry-specific — only fire for matching industry
Phase 3: Interest rules — specific interest type routing
Phase 4: A-type (synonym) — name pattern matches
Phase 5: D-type (aggregation) — netting rules (returns, discounts)
Phase 6: Specific patterns — medium confidence
Phase 7: Remuneration / salary / income rules
Phase 8: Admin catch-all — lowest priority content match
Phase 9: B-type (context-dependent) — need section context
```

### 3. Conflict resolution
| Conflict | Companies | Resolution |
|----------|-----------|------------|
| Duty Drawback | BCIPL→R34 vs SLIPL→R23 | R34 (more standard) |
| Directors Remuneration | BCIPL→R67 vs SLIPL→R45 | R67 (admin expense, standard) |
| R&M routing | MSL→R50 vs SLIPL→R72 | R50 (manufacturing-specific when industry=manufacturing) |
| Packing Materials | BCIPL→R70 vs SLIPL→R49 | R49 (manufacturing input, not sales) |

### 4. Helper function `_match()`
Reduced boilerplate from 6-line RuleMatchResult constructors to 1-line calls:
```python
def _match(field_name, broad, rule_id, conf=0.95) -> RuleMatchResult
```

### 5. Typo correction
Added `_TYPO_FIXES` dict for common Indian accounting misspellings (maintainance, recievable, expences, etc.) applied before pattern matching.

---

## Test Results

**Run:** `pytest tests/test_classification_pipeline.py tests/test_ai_classifier.py`
**Result:** 23 passed, 10 failed

All 10 failures are **pre-existing** (not caused by rule engine changes):
- 6 AI classifier failures: tests expect `ai_haiku` but code uses `ai_openrouter` (backend migration)
- 4 pipeline `classify_document` failures: test mock setup incomplete for current pipeline

**Smoke tests (11 items):**
- 9 items matched correct rules (Motor Car→R162, Purchase @18%→R42, Carriage Inward→R47, ECGS Loan→R137, Directors Remuneration→R67, GST Input Recoverable→R219, Cutting Labour→R46, Partners Capital→R116, Forex Loss→R91)
- 2 items correctly fell through to fuzzy/AI ("Wages and Salaries", "Miscellaneous Vague Entry")

---

## Trial Balance Filtering — Confirmed Working

Investigation confirmed that `excel_extractor.py:53-68` already filters Trial Balance sheets via `_SKIP_PATTERNS` regex (`trial\s*balance|\btb\b`). The TB noise seen in the March 23 BCIPL test was caused by pivoting to a pre-existing client (19cf7c12) whose data was uploaded before the TB filter existed — **not a code bug**.

---

## Files Modified
- `backend/app/services/classification/rule_engine.py` — Full rewrite (559 → 1,021 lines)

## Source Rule Files (read, not modified)
- `DOCS/rules/BCIPL_classification_rules.md` (22 rules)
- `DOCS/rules/SR_Papers_classification_rules.md` (22 rules)
- `DOCS/rules/SSSS_classification_rules.md` (14 rules)
- `DOCS/rules/MSL_classification_rules.md` (10 rules)
- `DOCS/rules/SLIPL_classification_rules.md` (12 rules)
- `DOCS/rules/INPL_classification_rules.md` (14 rules)
- `DOCS/rules/Kurunji_Retail_classification_rules.md` (15 rules)

---

*Log generated: 2026-03-23 | Session: rule-engine-v2-implementation*
