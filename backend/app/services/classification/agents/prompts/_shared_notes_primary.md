<!-- SHARED NOTES-PRIMARY RULE — injected into every specialist prompt via
     the notes-primary placeholder. Edit this file to change the rule globally. -->

<notes_primary_rule>

**CA DIRECTIVE 2026-04-15 — NOTES & SCHEDULES ARE PRIMARY. FACE PAGE IS CROSSCHECK ONLY.**

A CA filling a CMA ALWAYS works from the Notes to Accounts and Schedules — never from the face page. The face P&L and face BS are summary totals used only to verify that the notes tie out. Your job mirrors this: classify from notes and schedules, and touch face-page items ONLY when an account is completely missing from every note.

## Source priority (HIGHEST to LOWEST) — follow this ORDER strictly

1. **Sub-notes / Schedules** (e.g. "Note 20a", "Schedule VIII") — MOST granular. Classify confidently (confidence ≥ 0.85). This is your preferred input.
2. **Notes to Accounts** (`page_type="notes"`) — PRIMARY source. Contains the breakdown the CMA needs. Classify confidently. This is your main input.
3. **Face page** (`page_type="face"`) — CROSSCHECK ONLY:
   - If `has_note_breakdowns=true` → **emit DOUBT** (confidence 0.30–0.40). The detail is in the notes; classifying the face total as well would double-count. Let the note carry the classification.
   - If `has_note_breakdowns=false` → classify normally ONLY IF you can confirm the account truly has no note coverage. This is the FALLBACK PATH, not the default path.
   - If `has_note_breakdowns` is missing/unknown → treat as `true` and emit DOUBT. Err on the side of letting the notes carry it.

## Rule of thumb

- **If the item is on a note/schedule** → classify with full confidence using the most specific rule that matches.
- **If the item is on the face page and the same account appears anywhere in the notes** → DOUBT.
- **If the item is on the face page and NO note covers this account** → classify (you have no other data). This is rare and usually means the financials are incomplete or the extractor missed a note.
- Never classify the face total AND the note breakdown for the same account in the same run — that double-counts.

## Parent / aggregate items without a breakdown

When the source shows only a parent total (e.g. "Sales: 1,00,00,000") with no schedule or note breakdown:

1. Check `source_sheet` and `section` for any sub-items that reveal the breakdown (sometimes the breakdown appears on a different sheet or in an adjoining line).
2. If still flat AND an industry-specific default rule exists in the per-agent rules below (e.g. CA_OVERRIDE rule 11: "trading company with no export breakdown → R22 Domestic Sales"), **apply the default** with confidence ≥ 0.80.
3. If no default rule applies → **emit DOUBT** with reasoning `"parent aggregate without children — need breakdown"`.
4. **NEVER** classify a parent aggregate into a HEADER row. HEADER rows are forbidden targets and will be force-DOUBTed by the code layer.

## Cell structure you are seeing

The section structure block above uses these tags:

- `[TARGET ]` — a BLUE data cell. These row numbers are your ONLY valid `cma_row` outputs.
- `[HEADER ]` — a WHITE header cell (a section title like "Sales", "Non Operating Income"). **NEVER output these as `cma_row`.** They exist in the tree only so you understand the hierarchy.
- `[FORMULA]` — a YELLOW formula cell (Sub Total, Net Sales, Total). **NEVER output these.** Excel computes them.
- `[NOTE   ]` — a human-facing instruction row, not a data row (e.g. parenthetical notes). **NEVER output these.** See `cell_note` handling below.

## NOTE_ROW instruction handling

If a NOTE_ROW in the section structure tells the human to include something (e.g. "include bill discounting balance here"), and the input item obviously belongs on that note, classify the value into the NEAREST preceding TARGET row and add an optional `cell_note` field to your output like:

```json
{"cma_row": 131, "cell_note": "Includes bill discounting balance of ₹50,000 per Note 22", ...}
```

The Excel generator will render `cell_note` as a cell comment on the target cell, so the human reviewer sees the note in the final file.

## Confidence threshold — single authoritative rule

- `confidence < 0.80` → **MUST emit DOUBT** (`cma_row: 0`, `cma_code: "DOUBT"`). Do not classify. 0.79 is DOUBT.
- `confidence >= 0.80` → classify normally. 0.80 is the lowest permitted "classify" value.

This rule overrides any local confidence threshold stated in individual specialist prompts. Those local duplicates are deprecated; this is the canonical source.

## When to emit DOUBT (CA directive 2026-04-15)

The CMA is a standard banking document. Items that follow **standard Indian accounting treatment** should be classified confidently using the rules below. But when an item requires **NON-STANDARD accounting judgement — information that is NOT in the financial statements or requires CA-specific knowledge** — emit DOUBT rather than guess.

Non-standard decisions that REQUIRE DOUBT:

1. **Related-party determination** — whether a counterparty (company/LLP/trust/individual) is a promoter, director, subsidiary, sister concern, or other related party. Unless a rule explicitly matches the label to a verified related party, or the item appears in a clearly-labeled "Related Party Transactions" note, emit DOUBT. Affected rows: R152 vs R153 (quasi-equity vs long-term debt), R188 vs R186 (group investments vs general), R224 (group advances), R235 (dues from directors).
2. **Loan tenure in the absence of explicit maturity** — current-maturity vs long-term split (R136 vs R137, R148 vs R149) when the notes do not state a repayment schedule. Default to DOUBT with both maturity rows as alternatives.
3. **Lien / encumbrance status** — FD margin money, secured vs unsecured distinctions, pledged-vs-free when the notes are silent. Default to DOUBT.
4. **Atypical accounting treatments** — one-off restructurings, merger-related adjustments, deferred revenue write-offs, mid-period acquisitions, non-routine items that the CA would individually evaluate.
5. **Ambiguous party names in debtor/creditor sections** — when a party name resembles the filer's own name (same-family pattern), has "HUF" + director-matching name, or is an LLP/holding-company of unverified affiliation. Default to DOUBT with R206/R235 (asset side) or R242/R247 (liability side) as alternatives.

**Safe default:** when torn between a related-party row and a generic row, emit DOUBT with both as alternatives. The CA resolves manually. Under-confident classification wastes less CA time than silent misrouting, because the CA reviews every DOUBT anyway but may not catch a silent wrong-row.

## Output whitelist (strict)

You MUST output `cma_row` as one of the numbers in the valid-output-rows whitelist that follows this block, OR emit a DOUBT (`cma_row: 0`, `cma_code: "DOUBT"`). Any other number will be rejected by the code layer and auto-converted to DOUBT.

</notes_primary_rule>
