# CMA Cell-Type Awareness — Implementation Results

**Status:** Phases 0–5 complete on branch `feat/page-type-awareness`. Ready for user verification.

## What shipped

| Phase | Scope | Commit |
|---|---|---|
| 0 | `scripts/derive_cma_cell_types.py` + `DOCS/cma_cell_types.json` (248 rows classified) | `ed4562e` |
| 1 | `backend/app/services/classification/cell_types.py` loader | `dd7fc82` |
| 2 | `BaseAgent` placeholder substitution + `_validate_whitelist` | `e3d2d7e` |
| 3 | 4 specialist prompts rewritten to use `{{section_structure}}`, `{{valid_output_rows}}`, `{{notes_primary}}` | `8127d2d` |
| 4 | `cell_note` column + pipeline forward + openpyxl Comment rendering | `96aa4c8` |
| 5 | Regression test + baseline scan (this commit) | _pending_ |

## Cell-type taxonomy (from DOCS/cma_cell_types.json)

```json
{
  "BLUE": 118,
  "YELLOW": 56,
  "WHITE_HEADER": 34,
  "NOTE_ROW": 1,
  "BLANK": 34,
  "META": 5
}
```

Total: 248 rows. `BLUE` rows are input data cells (where classification must land). `YELLOW` rows are formula roll-ups (never written by classification). `WHITE_HEADER` rows are section titles, `NOTE_ROW` rows are instruction rows (e.g. R133 bill-discounting note), `BLANK` rows are spacers — none of these three should ever contain numeric data. `META` rows (R11–R15) are populated with text strings (FY, Currency, Units, Auditors, Opinion) during extraction, not classification.

## Baseline bad-fills scan

Output of `python scripts/scan_bad_fills.py --all` at the start of Phase 5:

```
=== CMA_Extraction_v2\output.xlsm: 9 bad fills ===
  R 16 [BLANK       ] [D]   = 65.69
  R 18 [BLANK       ] [F]   = 1.05
  R 18 [BLANK       ] [G]   = 1.05
  R 18 [BLANK       ] [H]   = 1.05
  R 20 [BLANK       ] [D]   = 10.65
  R 39 [BLANK       ] [D]   = -0.06
  R133 [NOTE_ROW    ] [B] (o/s bill discounting balance to be included)  = 0.01
  R217 [BLANK       ] [D]   = 38.48
  R227 [WHITE_HEADER] [D] Non Current Assets  = 16

Total bad fills across 1 file(s): 9
```

Summary: the one pre-existing output (`CMA_Extraction_v2/output.xlsm`) has 9 bad fills — small residuals (0.01 to 65.69) bleeding into BLANK spacer rows (R16, R18, R20, R39, R217), a stray 0.01 in the R133 NOTE_ROW, and a 16 that leaked into the R227 "Non Current Assets" header. These are exactly the failure modes Phase 3's section-structure + whitelist prompts are designed to eliminate. The scan currently operates on a single `.xlsm` — the rest of `CMA_Extraction_v2/` holds only source input `.xls`/`.xlsx` documents (not generated outputs).

## What the user must do

1. **Apply the DB migration** (Phase 4 did not run it):
   ```
   psql $DATABASE_URL < migrations/002_add_cell_note_to_classifications.sql
   # or paste into Supabase SQL editor
   ```
2. **Regenerate output for one test company** (e.g. BCIPL) to verify the new prompts work end-to-end. Upload the same input documents through the normal UI flow.
3. **Run the scan against the new output:**
   ```
   python scripts/scan_bad_fills.py CMA_Extraction_v2/<company>/output.xlsm
   ```
   Expected: 0 bad fills.
4. **Remove the regenerated output's path from `PRE_REGEN_OUTPUTS`** in `backend/tests/services/classification/test_no_bad_fills_regression.py` so the regression test protects it going forward.
5. **Run the regression suite:**
   ```
   cd backend && pytest tests/services/classification/test_no_bad_fills_regression.py -v
   ```

## Known behaviour changes

- Agents are now bounded: any `cma_row` outside their whitelist is auto-DOUBTed at the code layer. Older tests that hard-coded cross-agent row numbers in mocks were updated in Phase 2.
- Agents may emit `cell_note` for NOTE_ROW instructions (e.g. R133 bill-discounting). These become Excel cell comments in the generated .xlsm.
- Prompt token usage grew modestly per agent (~5–10 KB) due to the section-structure tree and notes-primary block. Gemini 2.5 Flash has ample headroom.

## Rollback

If regen reveals the new prompts degrade quality in ways the CA does not want:
```
git revert <sha-of-phase-3>  # puts prompts back, keeps the loader/validator plumbing
```
The plumbing (Phases 0–2, 4) is backwards-compatible — with no `{{placeholders}}` in the prompt, substitution is a no-op.
