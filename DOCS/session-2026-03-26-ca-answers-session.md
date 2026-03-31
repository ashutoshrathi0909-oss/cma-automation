# Session Report: CA Answers & Classification Improvement Plan

**Date:** 2026-03-26
**Project:** CMA Automation System
**Participants:** Ashutosh + Claude (Opus)
**Duration:** Full afternoon → evening

---

## 1. Background — Why This Session Happened

We had previously run a **9-company accuracy test** across our entire classification pipeline and found **201 unique genuinely wrong classifications**. A follow-up **model interview** of 100 of those items revealed a critical diagnostic split:

| Error Type | Count | What It Means |
|-----------|-------|---------------|
| **Routing bugs** | 45 (45%) | The correct CMA row wasn't even shown to the AI — the item was routed to the wrong section, so the AI never had a chance to pick correctly |
| **Model errors** | 55 (55%) | The correct row WAS available, but the AI picked wrong — needs better rules/prompt/examples |

This session's goal: **get CA (Chartered Accountant) expert answers for all ambiguous classifications, then prepare an implementation plan to apply those answers to the codebase.**

---

## 2. What We Did — Step by Step

### Step 1: Created a CA Questionnaire (43 questions, 11 sections)

We identified all classification ambiguities from the interview data and organized them into a structured questionnaire covering:

| Section | Topic | # Questions |
|---------|-------|-------------|
| A | Wages vs Salary (employee items) | 10 |
| B | "Others" problem (admin vs selling vs manufacturing) | 6 |
| C | Carriage/Freight (inward vs outward) | 2 |
| D | P&L vs BS stock routing | 6 |
| E | Finance costs (interest, bank charges, forex) | 8 |
| F | Manufacturing vs Admin routing (power, repairs, security) | 7 |
| G | Reserves & Appropriation | 2 |
| H | Borrowings (current maturities, unsecured loans) | 5 |
| I | Audit fees & Directors remuneration | 3 |
| J | Specific items (insurance, professional fees, deposits, etc.) | 19 |
| K | General classification rules | 8 |

**Output:** `DOCS/CA-clarification-questions.md`

### Step 2: Created an Interactive HTML Questionnaire Prompt

Rather than giving the CA a plain text document, we designed an interactive HTML questionnaire with:
- AI suggestions pre-filled for each question (the model's best guess)
- Real-world examples from actual extraction data (collapsible)
- Confidence selectors and industry-specific answer fields
- Auto-save to localStorage
- JSON export button

We didn't build the HTML directly — we wrote a comprehensive **prompt** for a Sonnet session to build it.

**Output:** `DOCS/prompts/ca-questionnaire-html-prompt.md`

### Step 3: CA Answered All 76 Questions

Ashutosh built the HTML questionnaire (using the prompt in a separate Sonnet session), took it to the CA, and collected all answers. The CA answered 68 of 76 questions directly; the remaining 8 were resolved through discussion in this session.

**Output:** `DOCS/ca_answers_2026-03-26.json` — **THE GOLDEN RULE** (not to be altered)

### Step 4: Resolved Unanswered Questions

8 questions were initially skipped. We resolved them:

| Question | Item | Resolution |
|----------|------|------------|
| Q1a | Staff Welfare | CA chose industry-dependent: Mfg→R45, Trading→R67 |
| Q1f | Leave Encashment | CA chose context-dependent: P&L→R45, BS→R249 |
| Q1g | Bonus | CA chose industry-dependent: Mfg→R45, Trading→R67 |
| Q1i | Employee Benefits | CA chose industry-dependent: Mfg→R45, Trading→R67 |
| Q8a | WIP in BS | CA said "shouldn't be touched" — R200 is a formula cell |
| Q8b | FG in BS | CA said "not to be touched" — R201 is a formula cell |
| Q15 | Bonus Shares | CA said "no CMA impact — always flag as doubt" |
| Q38 | Subsidy/Grant | CA chose context-dependent: P&L→R33, BS→R125 |

### Step 5: Discussed and Saved Future Feature Plans

We brainstormed and documented 13 future features across 3 tiers:

**Tier 1 — High Impact (win clients):**
1. Cross-validation & sanity checks (does BS balance? does P&L match?)
2. Bank ratio dashboard (Current Ratio, DSCR, TOL/TNW)
3. Variance commentary generator ("Revenue dropped 22% because...")

**Tier 2 — Operational Efficiency:**
4. Duplicate item detection
5. Document checklist & status tracking
6. Multi-format export (Excel, PDF, comparison PDF)

**Tier 3 — Competitive Moat:**
7. Industry benchmarking (anonymized data from all CMAs processed)
8. Bank-specific CMA templates (SBI vs PNB vs HDFC format)
9. Version history & diff (like git for Excel)

Three features were saved with detailed specs to memory:
- **CA Feedback Loop** — diff AI vs CA-corrected Excel, auto-learn rules
- **PDF Security** — page removal + company name redaction
- **CMA Lifecycle** — rolling year updates, provisional→audited swap, per-client approved mappings (the killer feature for zero-error repeat clients)

**Output:** `DOCS/future-feature-ideas.md`

### Step 6: Deep Codebase Exploration

Three parallel agents explored the classification codebase to understand exact changes needed:
- `scoped_classifier.py` — 26 keyword routing patterns, section-to-canonical mapping, AI prompt builder
- `rule_engine.py` — 55 deterministic rules across 9 phases, industry-aware logic
- `pipeline.py` — 4-tier flow (Rule Engine → Fuzzy → AI → Doubt)
- Ground truth files — canonical_labels.json, cma_classification_rules.json, training_data.json

### Step 7: Created Comprehensive Implementation Prompt

The final deliverable: a complete prompt for a fresh Sonnet session to implement ALL CA answers as code changes.

**Output:** `DOCS/prompts/ca-answers-implementation-prompt.md`

---

## 3. Key CA Decisions (The Golden Rules)

These are the CA's professional judgments. They override any AI suggestion, any existing rule, and any prior convention.

### Employee Cost Items

| Item | CA Decision | Notes |
|------|------------|-------|
| Staff Welfare | **Industry-dependent** | Manufacturing/Construction → R45 (Wages); Trading/Services → R67 (Salary) |
| Gratuity | **Always R45** | Overrides AI suggestion of R67 |
| EPF / Contribution to PF | **Always R45** | Overrides AI suggestion of R67 |
| ESI / Contribution to ESI | **Always R45** | AI agreed |
| Staff Mess Expenses | **Always R45** | Overrides AI suggestion of R67 |
| Leave Encashment | **Context-dependent** | P&L → R45 (Wages); Balance Sheet → R249 (Creditors for Expenses) |
| Bonus (standalone) | **Industry-dependent** | Same split as Staff Welfare |
| "Salary, Wages and Bonus" (combined line) | **Always R45** | Combined line always goes to Wages regardless of industry |
| Employee Benefits Expense (combined) | **Industry-dependent** | Same split as Staff Welfare |
| Labour Charges | **Always R45** | AI agreed |

### Admin & Selling Expenses

| Item | CA Decision | AI Suggested | CA Overrode? |
|------|------------|-------------|-------------|
| Miscellaneous Expenses | R71 (Others Admin) | R71 | No |
| Selling & Distribution | R70 (Advt & Sales Promo) | R70 | No |
| Admin & General Expenses | R71 | R71 | No |
| Carriage Outward | R70 | R70 | No |
| Brokerage & Commission | R70 | R70 | No |
| Licence & Subscription | **R71 (Others Admin)** | R68 (Rent Rates Taxes) | **Yes** |
| Insurance Premium | **R71 (Others Admin)** | R49 (Others Mfg) | **Yes** |
| Directors Remuneration | **R73 (Audit Fees)** | R67 (Salary) | **Yes** |

### Finance Costs

| Item | CA Decision | AI Suggested | CA Overrode? |
|------|------------|-------------|-------------|
| Bank Charges | R85 | R85 | No |
| Interest on Tax Delay | **R84 (WC Interest)** | R83 (TL Interest) | **Yes** |
| Forex Loss | R91 | R91 | No |
| Liquidated Damages | **R71 (Others Admin)** | R83 (TL Interest) | **Yes** |
| Bill Discounting Charges | **R84 (WC Interest)** | R83 (TL Interest) | **Yes** |
| Loan Processing Fee | **R85 (Bank Charges)** | R84 (WC Interest) | **Yes** |
| Interest on CC | R84 | R84 | No |

### Manufacturing vs Admin Routing

| Item | CA Decision | Industry-Specific? |
|------|------------|-------------------|
| Power/Electricity | **Industry-dependent** | Mfg/Construction → R48; Trading/Services → R71 |
| Repairs to Machinery | R50 (always manufacturing) | No |
| Security Charges | R51 (always manufacturing) | No |
| Job Work | R46 (always manufacturing) | No |
| Water Charges | R48 (always manufacturing) | No |
| Coal/Fuel/LPG | R48 (always manufacturing) | No |
| Stores & Spares | **R44 default, R43 if imported** | No, but import-keyword check |

### Balance Sheet Items

| Item | CA Decision | AI Suggested | CA Overrode? |
|------|------------|-------------|-------------|
| Vehicle HP Current Maturities | **R148 (Other Debts)** | R140 (Debentures) | **Yes** |
| Other LT Liabilities | **R149 (Balance Other Debts)** | R153 (LT Debt) | **Yes** |
| Advances to Suppliers | **R220** | R219 | **Yes** |
| Security Deposits Paid | **R238 (Other non-current)** | R237 (Govt deposits) | **Yes** |

### Special Items

| Item | CA Decision | Notes |
|------|------------|-------|
| Issue of Bonus Shares | **Always flag as doubt** | No CMA impact; closing reserves after bonus shares reflected under R121-R125; paid up capital R118 includes bonus shares |
| BS Inventory (R200, R201) | **Never classify** | Formula cells in CMA Excel (=CXX); auto-calculated |
| Subsidy/Govt Grant | **Context-dependent** | P&L → R33 (Extraordinary Income); BS → R125 (Other Reserves) |
| Row 75 (Misc Exp Written Off) | **Non-cash write-offs ONLY** | Regular "Miscellaneous Expenses" → R71 |
| Forex Gain | R32 | AI agreed |

### General Rules Confirmed

1. **Nature > Section Placement** — Classify by what the item IS, not where the company placed it in their P&L. Confidence: "usually" (not always).
2. **Industry routing is real** — Manufacturing companies route employee items to R45 (Wages/Manufacturing); Trading/Services to R67 (Salary/Admin). CA confirmed: "this is very true."
3. **P&L stock vs BS stock** — P&L context (Changes in Inventories) → rows 53-59. BS context (Current Assets - Inventories) → rows 200-201 (but formula cells, don't touch).
4. **Trading companies still use manufacturing rows** — R41-R59 apply for cost of goods in trading. CA confirmed: "it is certainly true."

---

## 4. Root Cause Analysis — Why The AI Gets These Wrong

### Problem 1: Routing Black Hole (45% of errors)

The `admin_expense` regex in `_KEYWORD_ROUTES` (scoped_classifier.py line 193) is too broad:
```
bank charge|vehicle|conveyance|repair|miscellaneous exp|insurance
```
These terms catch items that should go to `finance_cost` (bank charges), `manufacturing_expense` (repairs), etc. When routed to `admin_expense`, the AI only sees admin CMA rows and can never pick the correct manufacturing or finance row.

### Problem 2: Missing Industry Context (30% of errors)

The rule engine has `industry_type` parameter but only uses it for ~5 rules. The CA confirmed that ~15 items need industry-conditional logic. The AI model doesn't receive industry context in its prompt at all.

### Problem 3: AI Defaults to "Others" (25% of errors)

"Others (Admin)" (R71) is the most common misclassification (71 occurrences across 9 companies). The AI defaults to "Others" when unsure, but many of these items have specific rows. The prompt tells the AI "Others is last resort" but doesn't give enough disambiguation rules.

---

## 5. Implementation Plan Summary

The implementation prompt (`DOCS/prompts/ca-answers-implementation-prompt.md`) specifies **23 discrete changes across 4 files**:

| File | Changes |
|------|---------|
| `backend/app/services/classification/rule_engine.py` | 1 fix (Directors Rem R67→R73) + 18 new deterministic rules (CA-001 through CA-024) |
| `backend/app/services/classification/scoped_classifier.py` | Fix `_KEYWORD_ROUTES` regex, add `FORMULA_ROWS` exclusion, add CA disambiguation rules to AI prompt |
| `CMA_Ground_Truth_v1/reference/cma_classification_rules.json` | Add 13 CA expert rules (shown to AI in prompt as "CA EXPERT RULES") |
| `CMA_Ground_Truth_v1/database/training_data.json` | Add 18 CA-verified examples for fuzzy matching |

### New Rule IDs

| Rule ID | Item | Row | Type |
|---------|------|-----|------|
| CA-001 | Staff Welfare | R45/R67 | Industry-dependent |
| CA-002 | Bonus (standalone) | R45/R67 | Industry-dependent |
| CA-003 | Employee Benefits | R45/R67 | Industry-dependent |
| CA-004 | Gratuity | R45 | Universal |
| CA-005 | EPF | R45 | Universal |
| CA-006 | ESI | R45 | Universal |
| CA-007 | Staff Mess | R45 | Universal |
| CA-008 | Salary+Wages+Bonus | R45 | Universal |
| CA-009 | Labour Charges | R45 | Universal |
| CA-010 | Leave Encashment | R45/R249 | Context-dependent |
| CA-011 | Power/Electric | R48/R71 | Industry-dependent |
| CA-012 | Interest Tax Delay | R84 | Universal |
| CA-013 | Liquidated Damages | R71 | Universal |
| CA-014 | Loan Processing Fee | R85 | Universal |
| CA-015 | Vehicle HP Current | R148 | Universal |
| CA-016 | Other LT Liability | R149 | Universal |
| CA-017 | Advances to Suppliers | R220 | Universal |
| CA-018 | Security Deposits | R238 | Universal |
| CA-019 | Licence/Subscription | R71 | Universal |
| CA-020 | Insurance Premium | R71 | Universal |
| CA-021 | Subsidy/Grant | R33/R125 | Context-dependent |
| CA-022 | Stores & Spares | R44/R43 | Import-check |
| CA-023 | Bonus Share Issue | Doubt | Always-doubt |
| CA-024 | Preliminary Exp W/O | R75 | Universal |

### Expected Impact

- **Routing fixes** (Tasks 1, 3, 7): Should eliminate ~45% of errors (the routing bugs)
- **New deterministic rules** (Task 2): Should catch items BEFORE they reach the AI, reducing API cost and eliminating model errors for these patterns
- **Prompt enhancement** (Task 10): Should reduce "Others" misclassification by giving the AI explicit disambiguation rules
- **Training data** (Task 6): Should improve fuzzy match Tier 1 catches

**Target accuracy:** >90% (up from current ~85-87% baseline across 9 companies)

---

## 6. Files Created This Session

| File | Purpose |
|------|---------|
| `DOCS/CA-clarification-questions.md` | 43 questions for the CA, organized in 11 sections |
| `DOCS/prompts/ca-questionnaire-html-prompt.md` | Prompt for Sonnet to build interactive HTML questionnaire |
| `DOCS/ca_answers_2026-03-26.json` | All 76 CA answers (the golden rule) |
| `DOCS/future-feature-ideas.md` | 13 future features across 3 tiers with priority ranking |
| `DOCS/prompts/ca-answers-implementation-prompt.md` | 10-task implementation plan for applying CA answers to code |
| `DOCS/session-2026-03-26-ca-answers-session.md` | This document |

---

## 7. Open Items & Next Steps

### Immediate Next Step
Open a fresh Sonnet session and provide the implementation prompt:
> Read `DOCS/prompts/ca-answers-implementation-prompt.md` and implement all tasks sequentially. The CA answers in `DOCS/ca_answers_2026-03-26.json` are the golden rule — do not alter them.

### Open Items
1. **Formula cell audit** — R200 and R201 confirmed as formula rows. Need to check CMA.xlsm for ALL formula rows (totals, subtotals, computed fields) and add them to the exclusion list.
2. **Remaining 101 un-interviewed items** — Only 100 of 201 wrong items were interviewed (cost guard). The other 101 may reveal additional patterns.
3. **GT row offset bug** — `gen_ground_truth.py` has a -1 offset that produces wrong row numbers in ground truth files. Needs fixing before any future benchmark runs.
4. **Post-implementation accuracy test** — After code changes, re-run the 9-company accuracy test to measure improvement.
5. **Future features analysis** — Review `DOCS/future-feature-ideas.md` with CA before committing to roadmap.
