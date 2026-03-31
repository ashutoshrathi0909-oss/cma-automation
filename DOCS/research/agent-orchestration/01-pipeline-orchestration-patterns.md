# Pipeline Orchestration Patterns for Sequential Multi-Company Runs

**Research Date:** March 2026
**Context:** CMA Automation System — FastAPI + ARQ (Redis) + Claude Sonnet Vision + Claude Haiku
**Use Case:** Running the same 5-step pipeline (Upload → OCR → Verify → Classify → Excel) for 7 companies sequentially

---

## 1. Sequential Multi-Tenant Pipeline Orchestration

### The Core Problem

When running the same pipeline for multiple "tenants" (companies) one at a time, the challenge is:
- Each run is independent but must not interfere with others
- Failures in Company 3 should not block Companies 4-7 (but should be recorded)
- Progress must survive process restarts
- Completed companies must never be re-processed unless explicitly requested

### Pattern 1: State-File-Driven Sequential Runner

The simplest, most reliable pattern for our scale (7 companies). A JSON state file acts as the ground truth for the entire batch run.

```python
# run_state.json (created at start, updated after each company)
{
  "batch_id": "2026-03-20-7co-test",
  "started_at": "2026-03-20T10:00:00Z",
  "companies": {
    "dynamic_air": {
      "status": "completed",       # pending | running | completed | failed | skipped
      "started_at": "2026-03-20T10:01:00Z",
      "completed_at": "2026-03-20T10:45:00Z",
      "documents_processed": 5,
      "line_items_extracted": 487,
      "line_items_classified": 487,
      "doubt_count": 23,
      "error": null
    },
    "company_b": {
      "status": "running",
      "started_at": "2026-03-20T10:46:00Z",
      "completed_at": null,
      "documents_processed": 2,
      "line_items_extracted": null,
      "error": null
    }
  }
}
```

**Why this works:**
- If the runner script crashes, restarting it reads the state file and skips `completed` companies
- `running` status on restart = partial failure = needs re-run from that company
- Zero dependency on Redis for cross-run state — Redis is ephemeral, the JSON file is not

**Sources:** [Dagster Checkpointing Glossary](https://dagster.io/glossary/checkpointing), [Python Checkpointing on GitHub](https://github.com/a-rahimi/python-checkpointing)

---

### Pattern 2: Process Manager Pattern (Enterprise Integration Pattern)

For more complex orchestration, the **Process Manager** pattern (from Enterprise Integration Patterns) tracks multi-step workflows per entity:

```
Company Run = sequence of steps, each with its own status
  Step 1: upload_documents        ✓ done
  Step 2: trigger_extraction      ✓ done
  Step 3: poll_until_extracted    ✓ done
  Step 4: human_verify            ⏳ waiting
  Step 5: trigger_classification  ○ not started
  Step 6: poll_until_classified   ○ not started
  Step 7: generate_excel          ○ not started
```

Each step is **idempotent** — calling it when already done is safe and a no-op.

**Source:** [Enterprise Integration Patterns — Process Manager](https://www.enterpriseintegrationpatterns.com/patterns/messaging/ProcessManager.html)

---

### Pattern 3: ARQ-Native Sequential Chaining

Since our system already uses ARQ with `max_jobs=1`, we can use ARQ's job dependency pattern. ARQ does not have native job chaining, but sequential execution is guaranteed by `max_jobs=1`. The recommended pattern is to chain jobs by enqueuing the next job at the end of the current one:

```python
# In run_extraction (arq task):
async def run_extraction(ctx: dict, document_id: str) -> dict:
    # ... extraction logic ...
    result = {"document_id": document_id, "item_count": 142, "status": "extracted"}

    # Chain: enqueue classification automatically
    # (Only do this in automated test runs, NOT in production where human verify is required)
    if ctx.get("auto_chain"):
        await ctx["redis"].enqueue_job("run_classification", document_id=document_id)

    return result
```

**Important:** In production, chaining must stop at extraction because human verification is mandatory between extraction and classification. Auto-chaining is only appropriate in test harness scripts.

**Source:** [ARQ Documentation](https://arq-docs.helpmanual.io/), [ARQ GitHub](https://github.com/python-arq/arq), [fastapi-arq patterns](https://github.com/davidmuraya/fastapi-arq)

---

## 2. Pre-Flight Check Patterns

Before triggering each company's run, always validate the environment. Catching problems early (before a 45-minute job starts) saves significant time.

### Standard Pre-Flight Checklist

```python
async def preflight_checks(company_name: str) -> tuple[bool, list[str]]:
    """Run all pre-flight checks before starting a company pipeline run.
    Returns (ok: bool, errors: list[str])
    """
    errors = []

    # --- Check 1: Redis connectivity ---
    try:
        redis = await aioredis.from_url(settings.redis_url)
        await redis.ping()
        await redis.close()
    except Exception as e:
        errors.append(f"Redis unreachable: {e}")

    # --- Check 2: ARQ worker is alive ---
    # ARQ workers heartbeat to Redis key: arq:health-check
    try:
        redis = await aioredis.from_url(settings.redis_url)
        worker_keys = await redis.keys("arq:worker:*")
        if not worker_keys:
            errors.append("No ARQ worker detected — start worker before running")
        await redis.close()
    except Exception as e:
        errors.append(f"Could not check worker status: {e}")

    # --- Check 3: No stale jobs from previous run ---
    try:
        redis = await aioredis.from_url(settings.redis_url)
        queue_len = await redis.llen("arq:queue")
        if queue_len > 0:
            errors.append(f"ARQ queue has {queue_len} pending jobs — wait for them to complete")
        await redis.close()
    except Exception as e:
        errors.append(f"Could not check queue depth: {e}")

    # --- Check 4: Supabase reachable ---
    try:
        result = supabase.table("clients").select("id").limit(1).execute()
        # If no exception, Supabase is up
    except Exception as e:
        errors.append(f"Supabase unreachable: {e}")

    # --- Check 5: Company exists in DB ---
    try:
        result = supabase.table("clients").select("id").eq("name", company_name).execute()
        if not result.data:
            errors.append(f"Company '{company_name}' not found in database")
    except Exception as e:
        errors.append(f"Could not verify company: {e}")

    # --- Check 6: Anthropic API key set ---
    if not settings.anthropic_api_key:
        errors.append("ANTHROPIC_API_KEY environment variable not set")

    return len(errors) == 0, errors
```

### Pre-Flight Check Results Pattern

```
[PRE-FLIGHT] Company: Dynamic Air Engineering
  ✓ Redis: reachable (ping=1ms)
  ✓ ARQ worker: 1 worker alive (last heartbeat: 3s ago)
  ✓ Queue: empty (0 pending jobs)
  ✓ Supabase: reachable
  ✓ Company in DB: client_id=abc123
  ✓ Anthropic API key: present
  → All checks passed. Starting pipeline...
```

**Sources:** [FastAPI Health Check Patterns](https://patrykgolabek.dev/guides/fastapi-production/health-checks/), [fastapi-health GitHub](https://github.com/Kludex/fastapi-health), [Redis health check design](https://kirshatrov.com/posts/redis-job-queue)

---

## 3. Failure Recovery and Resume Patterns

### Pattern A: Idempotent Steps (Most Important)

Every pipeline step must be safe to re-run. Our `run_extraction` task already implements this correctly:

```python
# From backend/app/workers/extraction_tasks.py (already in our codebase)
# Step 2: IDEMPOTENCY — delete prior line items before re-inserting
service.table("extracted_line_items").delete().eq("document_id", document_id).execute()
```

This is the correct approach. If extraction fails halfway and is retried, the stale partial data is wiped first, then re-inserted cleanly.

**The idempotency rule:** Every pipeline step must produce the same final state whether run once or ten times.

**Source:** [Fivetran — Idempotence in Data Pipelines](https://www.fivetran.com/blog/idempotence-failure-proofs-data-pipeline), [Prefect — Idempotent Pipelines](https://www.prefect.io/blog/the-importance-of-idempotent-data-pipelines-for-resilience)

---

### Pattern B: Checkpoint-Based Resume

The state file (Pattern 1 above) combined with a "resume from last good" strategy:

```python
def get_resume_point(state: dict, company_name: str) -> str:
    """Determine which step to resume from for a given company.

    Returns one of: 'start' | 'after_upload' | 'after_extraction' |
                    'after_verify' | 'after_classification' | 'done'
    """
    company = state["companies"].get(company_name, {})
    status = company.get("status", "pending")

    if status == "completed":
        return "done"

    # Check each step's completion flag
    if company.get("excel_generated"):
        return "done"
    if company.get("classification_done"):
        return "after_classification"
    if company.get("verification_done"):
        return "after_verify"
    if company.get("extraction_done"):
        return "after_extraction"
    if company.get("documents_uploaded"):
        return "after_upload"

    return "start"
```

---

### Pattern C: Partial Failure Handling (Don't Block the Batch)

When running 7 companies, one failure should not stop the rest:

```python
async def run_batch(companies: list[str], state_file: str) -> dict:
    """Run pipeline for all companies. Continue on failure, log everything."""
    state = load_state(state_file)

    for company in companies:
        if state["companies"][company]["status"] == "completed":
            print(f"  [SKIP] {company}: already completed")
            continue

        print(f"  [START] {company}")
        state["companies"][company]["status"] = "running"
        save_state(state, state_file)

        try:
            result = await run_company_pipeline(company)
            state["companies"][company].update({
                "status": "completed",
                "completed_at": utcnow(),
                **result
            })
        except Exception as e:
            # Log failure, continue to next company
            state["companies"][company].update({
                "status": "failed",
                "error": str(e),
                "failed_at": utcnow()
            })
            print(f"  [FAIL] {company}: {e} — continuing with next company")

        save_state(state, state_file)

    return generate_summary_report(state)
```

**Source:** [Pipeline Recovery Patterns — FasterCapital](https://fastercapital.com/content/Pipeline-Recovery--How-to-Recover-and-Resume-Your-Pipeline-from-Failures-and-Interruptions.html)

---

### Pattern D: ARQ Job Status Polling

After enqueuing an ARQ job, poll its status instead of blocking:

```python
async def wait_for_job(redis_pool, job_id: str, timeout: int = 3600, poll_interval: int = 10) -> dict:
    """Poll ARQ job until complete or timeout."""
    from arq.jobs import Job

    job = Job(job_id, redis_pool)
    start = time.time()

    while time.time() - start < timeout:
        status = await job.status()

        if status == JobStatus.complete:
            result = await job.result()
            return {"status": "complete", "result": result}
        elif status == JobStatus.not_found:
            raise RuntimeError(f"Job {job_id} not found — worker may have crashed")

        await asyncio.sleep(poll_interval)

    raise TimeoutError(f"Job {job_id} did not complete within {timeout}s")
```

---

## 4. Progress Tracking Patterns

### Real-Time Progress with Redis Pub/Sub

For live progress updates during a batch run:

```python
# Writer (in ARQ task)
async def publish_progress(redis, company: str, step: str, pct: int, detail: str):
    await redis.publish(f"progress:{company}", json.dumps({
        "step": step, "percent": pct, "detail": detail, "ts": utcnow()
    }))

# Reader (in runner script)
async def subscribe_progress(redis, company: str):
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"progress:{company}")
    async for message in pubsub.listen():
        if message["type"] == "message":
            data = json.loads(message["data"])
            print(f"  [{company}] {data['step']} ({data['percent']}%): {data['detail']}")
```

### Simple Structured Logging (Our Recommended Approach)

For a 7-company test run, structured log lines are sufficient and require no extra infrastructure:

```
2026-03-20 10:00:00 [BATCH START] batch_id=2026-03-20-7co companies=7
2026-03-20 10:00:05 [CO 1/7] dynamic_air: preflight ✓ (6/6 checks passed)
2026-03-20 10:00:10 [CO 1/7] dynamic_air: uploading 5 documents
2026-03-20 10:05:00 [CO 1/7] dynamic_air: extraction started (job_id=abc123)
2026-03-20 10:44:00 [CO 1/7] dynamic_air: extraction complete (487 items, 100 pages)
2026-03-20 10:44:01 [CO 1/7] dynamic_air: [VERIFY GATE] waiting for human verification...
2026-03-20 11:00:00 [CO 1/7] dynamic_air: verified (23 doubts resolved)
2026-03-20 11:00:05 [CO 1/7] dynamic_air: classification started
2026-03-20 11:15:00 [CO 1/7] dynamic_air: classification complete
2026-03-20 11:15:10 [CO 1/7] dynamic_air: excel generated ✓
2026-03-20 11:15:10 [CO 1/7] dynamic_air: COMPLETED (elapsed=75min)
2026-03-20 11:15:15 [CO 2/7] company_b: preflight ✓
```

---

## Recommended for Our Project

### Immediate Recommendation (Before 7-Company Test)

1. **Create `run_all_extractions.py`** — a simple sequential runner script (already exists at project root per git status) that:
   - Maintains a `test_run_state.json` next to it
   - Skips companies with `status == "completed"`
   - Runs pre-flight checks before each company
   - Polls ARQ job status with `wait_for_job()`
   - Stops at the extraction stage (human verify gate is real — cannot be automated)

2. **Use the state-file pattern** (Pattern 1) — it's the simplest and survives process restarts without any infrastructure changes

3. **Do NOT use ARQ auto-chaining** — human verification between extraction and classification is a hard requirement per `CLAUDE.md`

4. **Pre-flight checks to implement:** Redis ping, ARQ worker alive check, Supabase connectivity, Anthropic API key present

5. **Failure recovery:** The existing idempotency in `run_extraction` (delete-before-insert) is already correct. Extend the same pattern to classification tasks.

### Applicable Tools at Our Scale

| Tool | Overhead | Best For |
|------|----------|----------|
| JSON state file + Python script | Zero | 7 companies, our current scale |
| Prefect | Low | 10-100 companies, need retry UI |
| Dagster | Medium | Production multi-tenant, asset lineage |
| Airflow | High | Enterprise, 100+ daily runs |

**Verdict:** At 7 companies in a test run, a simple Python script with a JSON state file is the correct tool. Prefect or Dagster would add deployment complexity with no benefit at this scale.

---

*Sources:*
- [ARQ GitHub — python-arq/arq](https://github.com/python-arq/arq)
- [fastapi-arq — davidmuraya](https://github.com/davidmuraya/fastapi-arq)
- [Prefect — Idempotent Pipeline Resilience](https://www.prefect.io/blog/the-importance-of-idempotent-data-pipelines-for-resilience)
- [Dagster — Checkpointing](https://dagster.io/glossary/checkpointing)
- [Dagster — Multi-Tenant Pipelines (RBC Borealis)](https://rbcborealis.com/research-blogs/designing-scalable-multi-tenant-data-pipelines-with-dagsters-declarative-orchestration/)
- [Enterprise Integration Patterns — Process Manager](https://www.enterpriseintegrationpatterns.com/patterns/messaging/ProcessManager.html)
- [FastAPI Health Check Patterns](https://patrykgolabek.dev/guides/fastapi-production/health-checks/)
- [Redis Job Queue Design](https://kirshatrov.com/posts/redis-job-queue)
- [Fivetran — Idempotence in Data Pipelines](https://www.fivetran.com/blog/idempotence-failure-proofs-data-pipeline)
- [Pipeline Recovery Patterns](https://fastercapital.com/content/Pipeline-Recovery--How-to-Recover-and-Resume-Your-Pipeline-from-Failures-and-Interruptions.html)
- [ARQ Retries — davidmuraya](https://davidmuraya.com/blog/fastapi-arq-retries/)
