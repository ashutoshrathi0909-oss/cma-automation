# Multi-Company Testing Architecture for CMA Pipeline

**Research Date:** March 2026
**Context:** CMA Automation — running the full pipeline on 7 companies for validation testing
**Goal:** Define how to structure a test runner that handles state, verification gates, reporting, and failure recovery

---

## 1. Why a Custom Test Runner (Not pytest)

Our pipeline is **not unit-testable** in the traditional sense for this phase:
- It involves real AI model calls (Claude Sonnet Vision, Claude Haiku)
- It has a **mandatory human verification gate** between extraction and classification
- Each company run takes 30-90 minutes
- Results need to be preserved across multiple sessions (you verify today, classify tomorrow)

The right tool is an **integration test runner** — a Python script that orchestrates the real system, not mocks.

This is distinct from pytest (which tests code logic in isolation) and closer to what Airflow, Prefect, and Dagster call "pipeline runs" or "flows."

**Source:** [Testing Strategies for Data Pipelines](https://ayc-data.com/data_engineering/2020/09/30/testing-for-big-data-infrastructure.html)

---

## 2. State Tracking Architecture

### Company Status State Machine

Each company moves through these states in order:

```
pending
  → uploading        (documents being uploaded to Supabase)
  → extracting       (ARQ job running, OCR in progress)
  → extracted        (all documents extracted, awaiting verify)
  → verifying        (human reviewing line items in UI — can take hours/days)
  → verified         (human marked all docs as verified)
  → classifying      (ARQ classification job running)
  → classified       (all items classified)
  → generating       (Excel generation running)
  → completed        (done — Excel downloaded)
  → failed           (error at some step — see error field)
  → skipped          (manually excluded from this run)
```

**Important:** The transition from `extracted` → `verifying` → `verified` is entirely human-driven. The test runner cannot automate this. It can only poll Supabase and wait.

### State File Structure

```json
{
  "batch_id": "2026-03-20-7co-validation",
  "created_at": "2026-03-20T09:00:00Z",
  "updated_at": "2026-03-20T14:35:22Z",
  "runner_version": "1.0.0",
  "companies": [
    {
      "name": "Dynamic Air Engineering",
      "client_id": "uuid-from-supabase",
      "documents": [
        {"filename": "FY22_Balance_Sheet.pdf", "document_id": null, "status": "pending"},
        {"filename": "FY23_PL.pdf", "document_id": null, "status": "pending"}
      ],
      "pipeline_status": "pending",
      "steps": {
        "upload": {"status": "pending", "completed_at": null, "detail": null},
        "extraction": {"status": "pending", "job_id": null, "completed_at": null, "item_count": null},
        "verification": {"status": "pending", "completed_at": null, "doubt_count": null},
        "classification": {"status": "pending", "job_id": null, "completed_at": null},
        "excel_generation": {"status": "pending", "job_id": null, "completed_at": null, "output_path": null}
      },
      "elapsed_minutes": null,
      "error": null
    }
  ],
  "summary": {
    "total": 7,
    "completed": 0,
    "failed": 0,
    "pending": 7,
    "in_progress": 0
  }
}
```

---

## 3. Test Runner Architecture

### Directory Structure

```
CMA project -2/
├── run_all_extractions.py          # Main runner script (already exists)
├── run_extraction.py               # Single-company runner (already exists)
├── test_run_state.json             # State file (created on first run)
├── test-results/                   # Output directory
│   ├── 2026-03-20-7co-report.md    # Human-readable summary
│   ├── 2026-03-20-7co-report.json  # Machine-readable full results
│   └── logs/
│       ├── dynamic_air.log
│       ├── company_b.log
│       └── runner.log
└── DOCS/research/agent-orchestration/
    └── (these files)
```

### Runner Script Architecture (Recommended)

```python
#!/usr/bin/env python3
"""
run_all_companies.py
====================
Sequential test runner for CMA pipeline — 7 company validation.

Usage:
    python run_all_companies.py                    # Run all pending companies
    python run_all_companies.py --company "Dynamic Air"  # Run one company
    python run_all_companies.py --resume           # Skip completed, retry failed
    python run_all_companies.py --status           # Print status table, exit
"""

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = Path("test_run_state.json")
RESULTS_DIR = Path("test-results")

COMPANIES = [
    {"name": "Company 1 (Simple)",       "pages": 30,  "items": 150},
    {"name": "Company 2",                "pages": 40,  "items": 200},
    {"name": "Company 3",                "pages": 50,  "items": 250},
    {"name": "Company 4",                "pages": 60,  "items": 300},
    {"name": "Company 5",                "pages": 70,  "items": 350},
    {"name": "Company 6",                "pages": 85,  "items": 400},
    {"name": "Dynamic Air Engineering",  "pages": 100, "items": 500},
]

class PipelineRunner:
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.state = self._load_or_init_state()

    def _load_or_init_state(self) -> dict:
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return self._init_state()

    def _init_state(self) -> dict:
        state = {
            "batch_id": f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-7co",
            "created_at": utcnow_str(),
            "companies": {}
        }
        for co in COMPANIES:
            state["companies"][co["name"]] = {
                "pipeline_status": "pending",
                "steps": {step: "pending" for step in
                          ["upload", "extraction", "verification", "classification", "excel"]},
                "error": None
            }
        self._save(state)
        return state

    def _save(self, state: dict = None):
        s = state or self.state
        s["updated_at"] = utcnow_str()
        self.state_file.write_text(json.dumps(s, indent=2))

    async def run_all(self, resume: bool = False):
        """Main entry point: run all pending companies sequentially."""
        print(f"\n{'='*60}")
        print(f"CMA Pipeline — 7 Company Batch Run")
        print(f"Batch ID: {self.state['batch_id']}")
        print(f"State file: {self.state_file.absolute()}")
        print(f"{'='*60}\n")

        for co in COMPANIES:
            name = co["name"]
            status = self.state["companies"][name]["pipeline_status"]

            if status == "completed" and not resume:
                print(f"  [SKIP] {name}: already completed")
                continue

            if status == "failed" and not resume:
                print(f"  [SKIP] {name}: previously failed (use --resume to retry)")
                continue

            await self._run_company(name)

        self._print_summary()
        self._generate_report()

    async def _run_company(self, name: str):
        """Run the pipeline for one company up to the verification gate."""
        print(f"\n{'─'*50}")
        print(f"  [START] {name}")
        started = utcnow_str()
        self.state["companies"][name]["status"] = "running"
        self.state["companies"][name]["started_at"] = started
        self._save()

        # Pre-flight checks
        ok, errors = await self._preflight(name)
        if not ok:
            self._mark_failed(name, f"Pre-flight failed: {'; '.join(errors)}")
            return

        try:
            # Step 1: Upload documents
            await self._step_upload(name)

            # Step 2: Trigger and wait for extraction
            await self._step_extract(name)

            # Step 3: GATE — human verification required
            # Runner cannot proceed past here automatically
            self._mark_awaiting_verification(name)
            print(f"  [GATE] {name}: Extraction complete.")
            print(f"  [GATE] Please verify line items in the UI, then re-run with --resume")

        except Exception as e:
            self._mark_failed(name, str(e))

    def _print_summary(self):
        """Print a summary table to console."""
        companies = self.state["companies"]
        print(f"\n{'='*60}")
        print(f"BATCH SUMMARY")
        print(f"{'─'*60}")
        print(f"{'Company':<30} {'Status':<15} {'Items':>6} {'Elapsed':>10}")
        print(f"{'─'*60}")
        for name, data in companies.items():
            status = data.get("pipeline_status", "pending")
            items = data.get("steps", {}).get("extraction", {})
            elapsed = data.get("elapsed_minutes", "—")
            print(f"{name[:29]:<30} {status:<15} {str(items)[:6]:>6} {str(elapsed):>10}")
        print(f"{'='*60}\n")
```

---

## 4. The Human Verification Gate

This is the critical design decision for our test runner. The pipeline **must stop** after extraction and wait for human verification. This is not optional — it is a hard requirement per `CLAUDE.md`.

### Gate Implementation Options

**Option A: Runner stops, user re-runs with --resume (Recommended)**
```
Session 1: python run_all_companies.py
  → Runs extraction for all 7 companies
  → Prints: "Verify in UI, then run: python run_all_companies.py --resume --stage classify"

[User goes to UI, verifies all companies]

Session 2: python run_all_companies.py --resume --stage classify
  → Skips extraction (state=extracted), runs classification for all 7
```

**Option B: Runner polls Supabase and waits**
```python
async def wait_for_verification(company: str, client_id: str, timeout_hours: int = 48):
    """Poll Supabase until all documents for this company are verified."""
    deadline = time.time() + (timeout_hours * 3600)
    while time.time() < deadline:
        result = supabase.table("documents") \
            .select("extraction_status") \
            .eq("client_id", client_id) \
            .execute()

        statuses = [d["extraction_status"] for d in result.data]
        if all(s == "verified" for s in statuses):
            return True

        print(f"  [WAIT] {company}: {statuses.count('verified')}/{len(statuses)} verified")
        await asyncio.sleep(300)  # check every 5 minutes

    raise TimeoutError(f"Verification not completed within {timeout_hours} hours")
```

Option B is more elegant for overnight batch runs but requires leaving the runner process alive. Option A is more practical for manual testing sessions.

---

## 5. Report Generation Patterns

### Console Summary (During Run)

```
======================================================
CMA Pipeline — 7 Company Batch Run
Batch ID: 2026-03-20-7co
======================================================

[CO 1/7] Company 1 (Simple)
  Pre-flight: ✓ (6/6 checks)
  Upload: ✓ (3 documents, 30 pages)
  Extraction: ✓ (job=abc123, 45 min, 152 items)
  Verification: ⏸ GATE — verify in UI

[CO 2/7] Company 2
  Pre-flight: ✓
  Upload: ✓ (4 documents)
  Extraction: RUNNING (job=def456)
  ...
```

### Final Markdown Report (`test-results/2026-03-20-report.md`)

```markdown
# CMA Pipeline Test Run — 2026-03-20

**Batch ID:** 2026-03-20-7co
**Total Companies:** 7
**Completed:** 5 | **Failed:** 1 | **Pending:** 1

## Results Summary

| # | Company | Pages | Items | Doubts | OCR Time | Classify Time | Status |
|---|---------|-------|-------|--------|----------|---------------|--------|
| 1 | Company 1 | 30 | 152 | 12 | 22 min | 8 min | ✓ Complete |
| 2 | Company 2 | 40 | 203 | 18 | 31 min | 10 min | ✓ Complete |
| 3 | Company 3 | 50 | 248 | 22 | 38 min | 12 min | ✓ Complete |
| 4 | Company 4 | 60 | 297 | 25 | 45 min | 14 min | ✗ Failed |
| 5 | Company 5 | 70 | 351 | 30 | 52 min | 17 min | ✓ Complete |
| 6 | Company 6 | 85 | 403 | 35 | 63 min | 20 min | ✓ Complete |
| 7 | Dynamic Air | 100 | 487 | 44 | 74 min | 24 min | ⏸ Pending |

## Issues Found

### Company 4 — FAILED
- **Step:** Classification
- **Error:** `RateLimitError after 3 retries`
- **Action:** Re-run classification after 10 minutes

## Doubt Rate Analysis

| Avg doubts per company | 26.6 (8.9% of items) |
|------------------------|----------------------|
| Highest doubt rate | Company 7: 44 items (9.0%) |
| Lowest doubt rate | Company 1: 12 items (7.9%) |
```

---

## 6. Recommended Test Runner Architecture

### For Our Project (Practical, Immediate)

```
Phase 1: Extraction Pass (automated)
  python run_all_companies.py --stage extract
  → Runs for all 7 companies sequentially
  → State saved to test_run_state.json after each
  → Stops at verification gate for each company
  → Total time: ~6-7 hours (sequential, ~1 hour each)

[Break: user verifies all 7 companies in the UI over 1-2 days]

Phase 2: Classification Pass (automated)
  python run_all_companies.py --stage classify --resume
  → Skips companies not yet verified
  → Runs classification for all verified companies
  → Total time: ~2-3 hours

Phase 3: Excel Generation Pass (automated)
  python run_all_companies.py --stage excel --resume
  → Generates Excel for all classified companies
  → Total time: ~30 minutes
```

### Key Design Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| State storage | JSON file | No extra infra, survives restarts |
| Job polling | ARQ Job.status() | Native to our stack |
| Failure handling | Log + continue | Don't block remaining companies |
| Verification gate | Stop + re-run | Human verify cannot be simulated |
| Concurrency | Sequential only | ARQ max_jobs=1, HTTP/2 pool constraint |
| Reporting | Markdown + JSON | Markdown for reading, JSON for re-processing |

---

## Recommended for Our Project

1. **Use the existing `run_all_extractions.py`** as the base — it already exists per git status. Enhance it with the state file pattern, pre-flight checks, and structured logging described here.

2. **Three-phase approach** is better than trying to run extraction + classification in one pass, because verification can take hours or days per company.

3. **Persist state to `test_run_state.json`** at the project root. Every state transition writes to disk immediately so a crash loses at most one in-progress step.

4. **Generate a Markdown report** at the end of each phase to make it easy to share findings with the team.

5. **The doubt rate metric** (doubts / total items) is the most important quality indicator to track across all 7 companies. Aim for < 15% doubt rate on the fuzzy + Haiku pipeline.

---

*Sources:*
- [Testing Strategies for Data Pipelines](https://ayc-data.com/data_engineering/2020/09/30/testing-for-big-data-infrastructure.html)
- [pytest-pipeline — PyPI](https://pypi.org/project/pytest-pipeline/)
- [Dapr Workflow Patterns — fan-out/fan-in](https://docs.dapr.io/developing-applications/building-blocks/workflow/workflow-patterns/)
- [Dagster Multi-Tenant Pipelines (RBC Borealis)](https://rbcborealis.com/research-blogs/designing-scalable-multi-tenant-data-pipelines-with-dagsters-declarative-orchestration/)
- [Azure Document Processing Pipeline (Python)](https://learn.microsoft.com/en-us/samples/azure/ai-document-processing-pipeline/azure-ai-document-processing-pipeline-python/)
- [ARQ Job Status API](https://arq-docs.helpmanual.io/)
