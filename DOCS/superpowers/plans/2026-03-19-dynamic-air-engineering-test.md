# Dynamic Air Engineering — End-to-End CMA Test Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the CMA Automation System against Dynamic Air Engineering's real financial documents (FY22–FY25), validate extraction accuracy (including Phase 10 Vision OCR on a 33-page scanned PDF), compare classification results against the existing human-prepared CMA, and produce a test report mirroring the Mehta Computers test.

**Architecture:** 8 main agents + 2 parallel pre-scan agents. Pre-scan agents run in background and produce ground truth files. Main agents run sequentially with hard gates between each. Orchestrator (Agent 0) manages the sequence, enforces gates, and assembles the final report by reading agent output files — never holding full results in context.

**Tech Stack:** FastAPI backend (localhost:8000), Next.js frontend (localhost:3002), Redis + ARQ workers, Supabase PostgreSQL, Claude Sonnet Vision (FY24 scanned PDF), pdfplumber (text PDFs), openpyxl/xlrd (Excel), Docker Compose.

**Spec:** `docs/superpowers/specs/2026-03-19-dynamic-air-engineering-test-design.md`

---

## Pre-Requisites (Verify Before Starting)

- [ ] Docker is running: `docker compose ps` → backend, frontend, redis, worker all "Up"
- [ ] Pre-scan agents have completed and these files exist:
  - `test-results/dynamic/dynamic_ground_truth.md`
  - `test-results/dynamic/dynamic_cma_known_values.json`
  - `test-results/dynamic/dynamic_cma_analysis.md`
- [ ] `test-results/dynamic/` directory exists
- [ ] All Dynamic financial files are present in `DOCS/Financials/`

---

## File Map

| File | Role |
|------|------|
| `test-agents/dynamic/MASTER_EXECUTION_PROMPT.md` | Orchestrator (Agent 0) instructions |
| `test-agents/dynamic/agent-specs/agent1-health.md` | Infrastructure health check spec |
| `test-agents/dynamic/agent-specs/agent2-intelligence.md` | Document intelligence spec |
| `test-agents/dynamic/agent-specs/agent3-extraction.md` | Extraction pipeline spec |
| `test-agents/dynamic/agent-specs/agent4-classification.md` | Classification quality spec |
| `test-agents/dynamic/agent-specs/agent5-excel.md` | Excel generation & validation spec |
| `test-agents/dynamic/agent-specs/agent6-e2e.md` | E2E critical path spec |
| `test-agents/dynamic/agent-specs/agent7-comparison.md` | Three-way comparison & final report spec |
| `test-results/dynamic/dynamic_ground_truth.md` | Pre-scan: Claude's independent document scan |
| `test-results/dynamic/dynamic_cma_known_values.json` | Pre-scan: Known correct values from existing CMA |
| `test-results/dynamic/DYNAMIC_TEST_REPORT.md` | Final output: full test report |

---

## Task 1: Write MASTER_EXECUTION_PROMPT.md

**Files:**
- Create: `test-agents/dynamic/MASTER_EXECUTION_PROMPT.md`

This is the single file passed to a fresh Claude Code window to run the entire test. The orchestrator (Agent 0) reads this file and nothing else before starting. It must be completely self-contained.

- [ ] **Step 1: Create the file**

Content is defined in full in the next section of this plan (see "MASTER_EXECUTION_PROMPT Content" below).

- [ ] **Step 2: Verify the file is complete**

Read it back and confirm:
- Company name: Dynamic Air Engineering
- All 7 document paths are listed
- All 8 agent output file paths are listed
- Gate conditions are explicit
- No references to "see above" or "as discussed" — everything inline

---

## Task 2: Write Agent 1 — Infrastructure Health

**Files:**
- Create: `test-agents/dynamic/agent-specs/agent1-health.md`

- [ ] **Step 1: Create spec**

The spec must include exact bash commands and exact expected outputs. No ambiguity. Content defined below in "Agent Spec Contents".

- [ ] **Step 2: Add to MASTER_EXECUTION_PROMPT as Task 1**

---

## Task 3: Write Agent 2 — Document Intelligence

**Files:**
- Create: `test-agents/dynamic/agent-specs/agent2-intelligence.md`

- [ ] **Step 1: Create spec**

Must include: file existence check for all 7 documents, FY24 scanned PDF confirmation (pdfplumber returns empty text), industry detection from FY25 Excel.

---

## Task 4: Write Agent 3 — Extraction Pipeline

**Files:**
- Create: `test-agents/dynamic/agent-specs/agent3-extraction.md`

This is the most critical agent spec. Must include:
- Exact API calls with curl commands or Python requests
- Document upload order
- Polling logic (what to do if status stuck > 10 minutes)
- Vision OCR validation (log check, item count gate)
- Verification step (MANDATORY per CLAUDE.md)

- [ ] **Step 1: Create spec with all API calls**

---

## Task 5: Write Agent 4 — Classification Quality

**Files:**
- Create: `test-agents/dynamic/agent-specs/agent4-classification.md`

Must include:
- Manufacturing-specific CMA rows table
- Comparison logic against `dynamic_cma_known_values.json`
- Tier breakdown metrics
- Improvement rules format (same as Mehta agent5)

- [ ] **Step 1: Create spec**

---

## Task 6: Write Agent 5 — Excel Generation & Validation

**Files:**
- Create: `test-agents/dynamic/agent-specs/agent5-excel.md`

Must include:
- Generate + download API calls
- Python comparison script (row-by-row vs CMA Dynamic file)
- Scale normalization (lakhs vs absolute)
- Pass/fail thresholds

- [ ] **Step 1: Create spec**

---

## Task 7: Write Agent 6 — E2E Critical Path

**Files:**
- Create: `test-agents/dynamic/agent-specs/agent6-e2e.md`

Focus on Mehta failures: file upload via react-dropzone, generate button navigation. Must use Playwright.

- [ ] **Step 1: Create spec**

---

## Task 8: Write Agent 7 — Three-Way Comparison & Final Report

**Files:**
- Create: `test-agents/dynamic/agent-specs/agent7-comparison.md`

Must include:
- Three comparison algorithms (extraction accuracy, classification accuracy, end-to-end accuracy)
- DYNAMIC_TEST_REPORT.md template
- How to handle missing items (FY24 Vision OCR items have no ground truth from P1 scan)

- [ ] **Step 1: Create spec**

---

## Execution

Once all agent specs are written, open a NEW Claude Code window and paste the contents of `test-agents/dynamic/MASTER_EXECUTION_PROMPT.md` as the first message.

The orchestrator will:
1. Read the full prompt
2. Verify pre-requisites
3. Spawn Agent 1 → check gate → spawn Agent 2 → ... → Agent 7
4. Assemble final report

**Do NOT run the orchestrator in this window.** Fresh context is essential.

---

## MASTER_EXECUTION_PROMPT Content
*(To be written into `test-agents/dynamic/MASTER_EXECUTION_PROMPT.md`)*

See Task 1 — the file content is the next section written to disk.

---

## Agent Spec Contents
*(Written to individual files in Tasks 2-8)*

Full content for each agent spec is in the corresponding files created during Tasks 2-8.
