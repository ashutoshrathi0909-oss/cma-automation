<!-- SHARED NOTES-PRIMARY RULE — injected into every specialist prompt via
     the notes-primary placeholder. Edit this file to change the rule globally. -->

<notes_primary_rule>

**Indian financial statements (Schedule III, Companies Act 2013) put classifiable detail in the Notes to Accounts and their sub-notes, NOT on the face page.**

## Source priority (HIGHEST to LOWEST)

1. **Sub-notes / Schedules** — specific note references like "Note 20a", "Schedule VIII". Most granular detail. Classify confidently (confidence ≥ 0.85).
2. **Notes to Accounts** (page_type="notes") — PRIMARY source. Contains breakdowns of face totals. Classify confidently.
3. **Face page** (page_type="face") line items:
   - If `has_note_breakdowns=true` → **emit DOUBT** (confidence 0.30–0.40) so the notes carry the classification and the face total doesn't double-count.
   - If `has_note_breakdowns=false` → classify normally (it's the only data available).

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

## Output whitelist (strict)

You MUST output `cma_row` as one of the numbers in the valid-output-rows whitelist that follows this block, OR emit a DOUBT (`cma_row: 0`, `cma_code: "DOUBT"`). Any other number will be rejected by the code layer and auto-converted to DOUBT.

</notes_primary_rule>
