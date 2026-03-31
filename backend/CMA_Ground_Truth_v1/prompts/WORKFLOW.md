# Ground Truth Extraction Workflow v2 — Multi-Agent, Per-Year

## Overview

The extraction is split into **two separate sessions** to prevent context overflow:

**Session 1 (This prompt — Sonnet agents):** Mechanical extraction of CMA + financial statements
**Session 2 (New window — Opus):** Reverse engineering and ground truth creation

```
SESSION 1: EXTRACTION (paste run-extraction.md)
  │
  ├─→ Parse all Excel/XLS files to JSON (scripts)
  │
  ├─→ Deploy agents IN PARALLEL:
  │     ├─ Agent: CMA Extraction (reads CMA workbook)
  │     ├─ Agent: FY1 Financial Statements (Excel or PDF)
  │     ├─ Agent: FY2 Financial Statements (Excel or PDF)
  │     ├─ Agent: FY3 Financial Statements (Excel or PDF)
  │     └─ Agent: FY4 Financial Statements (if exists)
  │
  ├─→ Validate all extraction outputs
  ├─→ Create SESSION_NOTES.md (provenance document)
  └─→ Hand off to user for Session 2

SESSION 2: REVERSE ENGINEERING (new window, paste main-opus-reverse-engineer.md)
  │
  ├─→ Read all extraction JSONs from Session 1
  ├─→ Read canonical_labels.json (131 canonical CMA rows)
  ├─→ Read cma_classification_rules.json (385 CA rules)
  ├─→ Cross-reference CMA amounts ↔ financial statement items
  ├─→ Classify: direct / composite_component / split
  ├─→ Flag industry-specific placements
  ├─→ Validate amounts
  └─→ Save {company}_ground_truth.json
```

## Why Two Sessions?

The old single-session approach failed on MSL (hit 32K token limit after 59 minutes). The problem: Opus was trying to hold CMA data + financial statements for ALL years + reverse engineering logic in one context. By splitting:
- Session 1 agents each get a fresh context with only ONE year's data
- Session 2 (Opus) gets compact extraction JSONs, not raw Excel/PDF content
- No agent ever hits context limits

## Prerequisites

1. Install dependencies: `pip install openpyxl xlrd`
2. Ensure scripts exist: `scripts/parse_excel.py` (.xlsx), `scripts/parse_xls.py` (.xls)
3. Ensure `cma_template_reference.json` exists (run `python build_cma_reference.py` if not)
4. Ensure `canonical_labels.json` exists (131 canonical CMA rows)

## Session 1: How to Run

### Option A: Full Auto
Paste `run-extraction.md` into Claude Code and tell it which company to process:
```
Process Mehta Computer using the prompts in the prompts/ folder.
```

### Option B: Manual Control
Tell Claude Code step by step:
```
1. Scan Mehta Computer folder and show me the extraction plan
2. Parse all Excel files to JSON
3. Deploy the extraction agents
4. Validate outputs
5. Create SESSION_NOTES.md
```

## Session 2: How to Run

Open a NEW Claude Code window and paste:
```
Read prompts/prompts/main-opus-reverse-engineer.md for your instructions.

You are reverse engineering CMA mappings for {Company Name}.

Read these files:
- {Company}/{company}_cma_extraction.json (CMA form data)
- {Company}/{company}_fs_2022.json (FY2021-22 financial statements)
- {Company}/{company}_fs_2023.json (FY2022-23 financial statements)
- {Company}/{company}_fs_2024.json (FY2023-24 financial statements)
- {Company}/{company}_fs_2025.json (FY2024-25 financial statements)
- canonical_labels.json (131 canonical CMA rows — use sheet_row as cma_row)
- cma_classification_rules.json (385 CA rules — use for validation)
- {Company}/SESSION_NOTES.md (extraction notes and file provenance)

Cross-reference CMA amounts with financial statement line items.
Save output as {Company}/{company}_ground_truth.json.
```

## Per-Company Source File Summary

| Company | CMA | FY Sources | Notes |
|---------|-----|------------|-------|
| Mehta Computer | `.xls` | 2022-24: Excel, 2025: PDF | Year-wise subfolders |
| MSL | `.xls` | PDFs + 1 Excel BS | Has partial extractions from failed attempt |
| Dynamic Air | `.xls` | FY22: Excel+PDF, FY23: PDF, FY24: 15MB PDF, FY25: Excel | FY24 is very large |
| INPL | `.xls` | 3 PDFs (13-18MB each) | All PDF, very large |

## Output Files Per Company

After both sessions, each company folder should contain:

| File | Created By | Purpose |
|------|-----------|---------|
| `{company}_cma_extraction.json` | Session 1 - CMA Agent | CMA row numbers and amounts |
| `{company}_fs_{year}.json` | Session 1 - Year Agents | Financial statement data per year |
| `SESSION_NOTES.md` | Session 1 - Main agent | Provenance: what was extracted from where |
| `{company}_ground_truth.json` | Session 2 - Opus | Final reverse-engineered mappings |
| `{company}_ground_truth_normalized.json` | Normalization prompt | Canonicalized version (if needed) |

## File Reference

| File | Purpose |
|------|---------|
| `prompts/run-extraction.md` | Session 1 master prompt (v2) |
| `prompts/subagent-1-sonnet-ocr.md` | PDF OCR agent instructions |
| `prompts/subagent-2-cma-extractor.md` | CMA extraction agent instructions |
| `prompts/main-opus-reverse-engineer.md` | Session 2 Opus reverse engineering instructions |
| `scripts/parse_excel.py` | .xlsx → JSON converter |
| `scripts/parse_xls.py` | .xls → JSON converter |
| `canonical_labels.json` | 131 canonical CMA rows (source of truth for cma_row integers) |
| `cma_classification_rules.json` | 385 CA rules (for validation) |
| `cma_template_reference.json` | Full CMA template (264 rows with hierarchy) |
