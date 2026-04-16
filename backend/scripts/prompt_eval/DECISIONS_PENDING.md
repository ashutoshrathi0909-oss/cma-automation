# Prompt Decisions Pending CA Review

## Resolved

| # | Decision | Date | Commit |
|---|----------|------|--------|
| 1 | Duty Drawback → R34 always | 2026-04-16 | 71e67c0 |
| 2 | Electricity [manufacturing] only → R48; trading/services → R71 | 2026-04-16 | 1d2c736 |
| 3 | R244 confirmed for Provision for Taxation | 2026-04-16 | 7b40100 |
| 4 | Vehicle HP → R136/R137 per tenure; DOUBT if tenure unclear | 2026-04-16 | 85fa247 |
| 5 | Security Deposits: government → R237, private → R238 | 2026-04-16 | 7b40100 |
| 6 | Prepaid → R222 all industries | 2026-04-16 | 7b40100 |
| 7 | R33 Extraordinary Income rule added for explicitly non-recurring items | 2026-04-16 | 71e67c0 |
| 8 | R29 MF Dividend rule kept; "Dividend from Mutual Fund" → R29 | 2026-04-16 | 71e67c0 |

---

Items surfaced during the 2026-04-15 pre-eval review (commits `c0b1b67..06815f8` on `feat/page-type-awareness`) that were NOT applied because they require a CA decision rather than a prompt-consistency fix. Each entry lists what the ambiguity is, who the stakeholders are, the options, and my best-guess recommendation — for the CA (father) to approve or overrule.

Once the CA decides on any item here, the corresponding prompt change should be made through the normal `/prompt-eval → /prompt-fix → /prompt-lock → /prompt-log` cycle so the regression suite captures the case.

---

## 1. Duty Drawback — R22 vs R34 (`pl_income`)

**Conflict:**
- LEGACY rule 21 in `pl_income_prompt.md`: `"Duty Drawback" → R22 (Domestic Sales)`
- CA_OVERRIDE rule 8 (same file): `"Duty drawback / IGST received" → R34 (Other Income)`
- `cma_golden_rules_v2.json` legacy_346 notes: *"If received towards deemed exports then classified as domestic sales otherwise as export sale."*

**Why it wasn't auto-fixed:** The two rules may both be intentional — rule 21 may cover plain "Duty Drawback" ledgers where the item is a sale-side incentive netted against domestic revenue, while rule 8 covers reclassification as Other Income. The golden rule adds a third condition (export vs non-export). A model reading only the trigger phrases picks R22 for plain labels; a CA might disagree.

**Options:**
- (a) Drop LEGACY rule 21. Treat all "Duty Drawback" → R34.
- (b) Keep LEGACY rule 21 but scope to: label is "Duty Drawback" AND the same notes section mentions export/FOB/CIF/customs → R22.
- (c) Route all variants to DOUBT; CA resolves per client.

**Recommendation:** (a). R34 "Other Income" is the cleaner CMA placement for a government incentive. Option (b) recreates the ambiguity rather than fixing it.

**CA question to resolve:** When "Duty Drawback" appears in Indian P&L, do you map it to R22 or R34 by default?

---

## 2. Power / Electricity routing in trading companies (`pl_expense`)

**Conflict:**
- Rule 3 (CA_VERIFIED_2026): `[all] "Power & Fuel" / "Electricity Expenses" / "Electricity Charges" → R48`
- `industry_directives` (Trading block): `Power/Electricity/Generator → R71, NOT R48`
- `accounting_brain` Trading table: `Power / Electricity → R71 (Others - Admin)`
- CA_OVERRIDE rules 93–96 (`[trading]`): all route electricity/power/fuel → R71

**Why it wasn't auto-fixed:** Rule 3 wins the tier contest (CA_VERIFIED_2026 beats CA_OVERRIDE), so current behaviour on trading-electricity is R48. But three separate guidance sections say R71. This is either an intentional override (CA decided all industries should use R48 for electricity in CMA) or a scoping bug (rule 3 should have been `[manufacturing]`).

**Options:**
- (a) Change rule 3 scope to `[manufacturing]`. Trading/service electricity → R71. Matches industry_directives, accounting_brain, and CA_OVERRIDE 93–96.
- (b) Delete CA_OVERRIDE rules 93–96 and the trading-electricity entries in industry_directives + accounting_brain. All industries use R48.
- (c) Keep rule 3 as-is but update all three guidance blocks to also say R48 for trading.

**Recommendation:** (a). The three independent guidance sections + four CA_OVERRIDE rules all point to R71 for trading — the simpler explanation is that rule 3's `[all]` scope is an oversight. R48 is Manufacturing Expenses → factory-floor utility; trading companies don't have a factory.

**CA question to resolve:** For a trading company, should "Electricity Expenses" go to R48 (Power & Fuel, manufacturing section) or R71 (Other Admin Expenses)?

---

## 3. Provision for Taxation — R244 vs R250 (`bs_asset`)

**Status:** Partially handled. Commit `bb8cf2d` rescoped O30 to non-income-tax provisions so T1-R30 (Provision for Taxation → R244) now has a clean run. But golden rule `Source1_rule_74` confirms R244 and there is no `ca_interview` entry refuting it — so T1-R30 should be the authoritative answer.

**Remaining question for CA:** Confirm R244 is the right destination for "Provision for Taxation" / "Provision for Income Tax" / "Income Tax Provision" on the balance sheet. If any client-specific case should go to R250 instead, add a conditional rule.

---

## 4. Vehicle HP Loans — golden rules mismatch (SCORING BUG, not prompt bug)

**Issue:**
- `cma_golden_rules_v2.json` (ca_override tier): Vehicle HP current maturities → R148, non-current → R149.
- `bs_liability_prompt.md` V8 (CA_VERIFIED_2026, higher tier): both → R136/R137, explicitly "SUPERSEDES old R148/R149 routing".

**Why it wasn't auto-fixed:** Touching `cma_golden_rules_v2.json` changes what eval calls "correct". That is a ground-truth change and must come from the CA directly. If we don't fix this before running eval, every Vehicle HP test case scores as a false negative even though the prompt is intentionally correct.

**Options:**
- (a) Update the Vehicle HP entries in `cma_golden_rules_v2.json` to R136/R137 at `ca_verified_2026` tier, citing V8's CA decision.
- (b) Add a tier-aware scoring override in `backend/scripts/prompt_eval/score.py` that honours CA_VERIFIED_2026 prompt rules over older `ca_override` golden entries.

**Recommendation:** (a), contingent on CA confirmation that V8 is the current authoritative decision. Golden rules should mirror the CA's latest word, not historical `ca_override` decisions that have been superseded.

**CA question to resolve:** Are Vehicle HP Loans (current maturities and non-current) classified as Term Loans (R136/R137) or as Other Debts (R148/R149)? If R136/R137, update the golden rules file.

---

## 5. Security Deposit — R237 vs R238 (`bs_asset`)

**Conflict:**
- O27 (CA_OVERRIDE): generic and named private deposits → R237.
- I4 (CA_INTERVIEW): `"Security Deposits Paid (to landlord, utility companies)" → R238`.
- Multiple CA_GT_dispute entries (d126, d140) and CA_interview_Q35: R238.
- Pattern-6 guidance in the prompt: "Government deposits → R237, Private deposits → R238" (which matches the CA_GT consensus).

**Why it wasn't auto-fixed:** O27 wins over I4 by tier, but I4 and the GT disputes reflect a more recent CA pattern. The guidance block agrees with R238 for private deposits, so the prompt is internally split.

**Options:**
- (a) Rescope O27 to government deposits only. Private/named deposits (telephone, electricity, MSEB, rent, gem caution) → R238 per I4.
- (b) Keep O27 as-is and remove I4 + the Pattern-6 guidance. All named deposits → R237.

**Recommendation:** (a). The Pattern-6 principle ("government → R237, private → R238") is what a CA would defend in audit, and the golden-rule disputes went for R238.

**CA question to resolve:** For security deposits to a landlord, telephone company, electricity board, or similar PRIVATE counterparty, do we use R237 or R238? For deposits with GOVERNMENT bodies (excise, licensing, customs), same question.

---

## 6. Prepaid Expenses — R222 vs R223 vs R224 (`bs_asset`)

**Conflict (three-way split):**
- O8 (CA_OVERRIDE, `[manufacturing]`): Prepaid → R222.
- O32 (CA_OVERRIDE, `[all]`): All prepaid/prepayments → R223.
- I3 (CA_INTERVIEW): BS current asset prepaid → R222.
- L32 (LEGACY): Prepaid → R223.
- Golden rule CA_interview_Q36: "Prepaid Expenses (BS current asset)" → R224.
- accounting_brain "never DOUBT" line: Prepaid anything → R222.

**Why it wasn't auto-fixed:** Three different target rows, each with some authority backing. Cannot pick one without CA input.

**Recommendation:** Route all "Prepaid Expenses" to DOUBT with alternatives [R222, R223, R224] until CA picks a single canonical row. This prevents arbitrary routing based on which rule the model matches first.

**CA question to resolve:** For a plain "Prepaid Expenses" line item on the balance sheet, should we use R222, R223, or R224? Does the industry matter?

---

## 7. R33 "Extraordinary Income" — dead row (`pl_income`)

**Issue:** R33 is listed in the `pl_income` valid_categories table but no rule in any tier produces R33 as a primary output. Golden rule `legacy_CA_R12` maps "Subsidy / Government Grant" → R33, but prompt rule 10 routes the same item → R34. Zero rules reach R33.

**Why it wasn't auto-fixed:** Without a CA decision on when "Extraordinary Income" is the correct target, any new rule is a guess.

**Recommendation:** Add a minimal rule: `"Extraordinary Income" / explicitly labelled non-recurring items (flood relief, pandemic grant, one-time windfall) → R33`. Recurring grants stay at R34.

**CA question to resolve:** When is R33 the correct row, if ever? If never, remove R33 from the valid_categories table.

---

## 8. R29 "Dividends from Mutual Funds" — dead row (`pl_income`)

**Issue:** Similar to #7. R29 is whitelisted but no rule produces it. Example ex_035 even shows R29 as a 0.60-confidence alternative for "Dividend on Shares & Unit", which teaches the model a wrong path for dividend items.

**Recommendation:** Either add a rule "Dividend from Mutual Fund" → R29, or remove R29 from valid_categories. Low priority — Indian SMEs rarely hold MF investments in regulated accounts.

**CA question to resolve:** Do any of your CMA clients report mutual fund dividends separately? If yes, they go to R29; if no, remove the row.

---

## How to act on this file

When CA provides a decision on any item:

1. Apply the resulting prompt change in a single commit: `prompt(<agent>): <one-line fix> (resolves DECISIONS_PENDING #<n>)`.
2. Update this file — cross off the resolved item under a "Resolved" section at the top (do not delete the entry; keep it as historical record).
3. After the next `/prompt-eval` run, if the resolved case now passes, lock it into `regression_suite.json` via `/prompt-lock`.
