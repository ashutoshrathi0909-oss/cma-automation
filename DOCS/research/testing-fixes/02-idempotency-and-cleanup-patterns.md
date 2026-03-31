# Idempotency, Cleanup Patterns & Supabase Connection Management

## Problems We Had

1. **ARQ job timeout restart loop**: `job_timeout=900` (15 min) killed classification mid-run.
   ARQ re-queued the job. The idempotency delete at the top of `run_classification` deleted all
   classifications, so the job re-classified everything from scratch. This loop repeated until
   the timeout was lengthened.

2. **Concurrent Supabase HTTP/2 overload**: `max_jobs=10` with a module-level singleton
   `_service_client` meant all 10 concurrent ARQ workers shared one HTTP/2 connection.
   Supabase's HTTP/2 server terminated the connection under load, causing `ConnectionTerminated`
   errors across all workers simultaneously.

3. **No idempotency across re-runs**: Re-running a failed classification job without cleanup
   could insert duplicate rows (if the delete step was skipped due to an earlier crash).

---

## Part 1: ARQ Job Idempotency Patterns

### Pattern A: Delete-then-reinsert (current approach — correct but vulnerable)

```python
# What run_classification() currently does:
# Step 3: Delete existing classifications
service.table("classifications").delete().in_("line_item_id", item_ids).execute()

# Step 4: Run pipeline (inserts fresh classifications)
pipeline.classify_document(...)
```

This is correct for idempotency but has one vulnerability: if the job is killed **between** the
delete and the re-insert (e.g., by timeout), the document is left with zero classifications and
the next run starts from scratch — identical to the first run, burning the same tokens.

**Fix**: Use checkpoint-based resumption (Pattern C below).

### Pattern B: Upsert instead of insert (database-level idempotency)

Source: Supabase docs — https://supabase.com/docs/reference/python/upsert

```python
# Instead of .insert(), use .upsert() with a unique constraint
# The unique constraint must be defined in the DB:
# UNIQUE (line_item_id)  -- one classification per line item

service.table("classifications").upsert(
    classification,
    on_conflict="line_item_id",   # Supabase/PostgREST syntax
).execute()
```

With upsert, re-running the pipeline simply overwrites existing rows. No delete step needed.
No window where the table is empty. This is the most robust pattern.

**Required DB migration**:
```sql
ALTER TABLE classifications
  ADD CONSTRAINT classifications_line_item_id_unique UNIQUE (line_item_id);
```

### Pattern C: Checkpoint / progress cursor (skip already-done items)

Instead of re-classifying everything on restart, check which items already have a classification:

```python
def classify_document(self, document_id, ...):
    service = get_service_client()

    # Fetch all verified line items
    line_items = _fetch_all_line_items(service, document_id)

    # Fetch already-classified item IDs (checkpoint)
    existing = (
        service.table("classifications")
        .select("line_item_id")
        .in_("line_item_id", [item["id"] for item in line_items])
        .execute()
    )
    already_done = {row["line_item_id"] for row in (existing.data or [])}

    # Only classify items not yet done
    pending = [item for item in line_items if item["id"] not in already_done]
    logger.info(
        "classify_document: %d total, %d already done, %d pending",
        len(line_items), len(already_done), len(pending),
    )

    for item in pending:
        classification = self.classify_item(item, ...)
        service.table("classifications").insert(classification).execute()
```

On ARQ restart, all previously completed items are skipped. Only the in-progress batch is
re-classified. This makes restarts cheap.

**Combine with upsert** for maximum safety: even if a duplicate somehow exists, the upsert
handles it gracefully.

### Pattern D: Job status tracking in Redis (ARQ-native)

ARQ stores job results in Redis. You can use this to avoid re-enqueuing a job that is already
running:

```python
from arq import ArqRedis

async def enqueue_classification(redis: ArqRedis, document_id: str):
    # Check if a job for this document is already queued or running
    job = await redis.enqueue_job(
        "run_classification",
        document_id,
        _job_id=f"classify:{document_id}",  # Deterministic job ID
    )
    # ARQ deduplicates by job_id — second enqueue with same _job_id is a no-op
    if job is None:
        logger.info("classify:%s already queued — skipping", document_id)
```

Setting `_job_id` to a deterministic value means ARQ will refuse to enqueue a duplicate job
while one with the same ID is already in the queue or running. This prevents the re-queue loop
entirely.

Source: ARQ docs — https://arq-docs.helpmanual.io/#arq.connections.ArqRedis.enqueue_job

---

## Part 2: ARQ Job Timeout — Root Cause and Fix

### Why 15-minute timeout caused the restart loop

ARQ's `job_timeout` is a wall-clock limit. When hit:
1. ARQ sends `SIGTERM` to the coroutine (cancels it).
2. ARQ marks the job as failed in Redis.
3. If `max_tries > 1` (default=1 in ARQ), the job is re-queued.
4. The re-queued job starts from scratch (because our delete-then-reinsert idempotency has
   no checkpoint).

For 2971 items at ~1s each via AI: total runtime = ~50 minutes. A 15-minute timeout is far too
short.

### Fix: Set timeout long enough for the full run

```python
class WorkerSettings:
    job_timeout = 3600   # 60 minutes — already fixed in our worker.py
    max_tries = 1        # Do NOT retry on timeout; let it fail cleanly
```

The current `worker.py` already has `job_timeout = 3600` — this was already fixed. But combine
it with checkpoint-based resumption so a genuine timeout (e.g., extended run) can resume from
where it left off rather than starting over.

### Alternative: Split into smaller sub-jobs

Instead of one job classifying all 2971 items, split into batches of 100:

```python
async def run_classification_batch(ctx, document_id, batch_start, batch_size=100):
    """Classify one batch of line items. Enqueued per-batch."""
    ...

async def run_classification_coordinator(ctx, document_id):
    """Fetch all items, enqueue one sub-job per batch."""
    items = _fetch_all_line_items(document_id)
    for i in range(0, len(items), 100):
        await ctx["redis"].enqueue_job(
            "run_classification_batch",
            document_id,
            i,
            _job_id=f"classify:{document_id}:batch:{i}",
        )
```

Each batch job takes ~2 minutes at 1.2s/item. Well within any reasonable timeout. Failed batches
are retried individually without re-doing completed batches.

**Trade-off**: More complexity. For our scale (one document at a time, max_jobs=1), the
checkpoint pattern (Pattern C) is simpler and sufficient.

---

## Part 3: Supabase Connection Management for Concurrent Workers

### Problem: Singleton HTTP/2 client shared across concurrent workers

```python
# Current code in dependencies.py — problematic at max_jobs > 1
_service_client: Client | None = None

def get_service_client() -> Client:
    global _service_client
    if _service_client is None:
        _service_client = create_client(url, key)
    return _service_client   # ALL jobs share this one client
```

The Supabase Python client uses `httpx` under the hood with HTTP/2 enabled by default. HTTP/2
multiplexes multiple requests over a single TCP connection. When 10 jobs all make concurrent
requests, the single HTTP/2 connection is overloaded, Supabase closes it, and all 10 jobs
get `ConnectionTerminated` simultaneously.

### Fix A: Set max_jobs=1 (already done in our worker.py)

```python
class WorkerSettings:
    max_jobs = 1   # Sequential — single connection never overloaded
```

This is the simplest fix and already in place. One job at a time, one connection, no contention.
At our scale (one company processed at a time), this is correct.

### Fix B: Per-job client creation (if you need max_jobs > 1)

```python
def get_service_client() -> Client:
    """Create a fresh client per call — safe for concurrent workers."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
```

Each ARQ job gets its own HTTP session. No shared state. The overhead of creating a new
`httpx.Client` per job is negligible (one TCP handshake + TLS) compared to the minutes of
work the job does.

**Downside**: If called per-item (not per-job), this creates thousands of connections per run.
The pattern should be: one client per job (instantiated in the task function, passed down).

```python
async def run_classification(ctx: dict, document_id: str) -> dict:
    # Create one client for this entire job — not shared with other jobs
    service = create_client(url, key)
    pipeline = ClassificationPipeline(service_client=service)
    ...
```

### Fix C: Connection pooling with pgBouncer (Supabase-native)

Supabase provides a PgBouncer connection pooler at port 6543. For direct DB access via
`psycopg2`/`asyncpg` (not the REST API), use the pooler URL:

```
postgresql://postgres:[password]@db.[project].supabase.co:6543/postgres?pgbouncer=true
```

The Supabase REST API (what the Python client uses) does not go through PgBouncer — it goes
through PostgREST. So this fix applies only if you switch to direct SQL queries, not to our
current client pattern.

### Fix D: Disable HTTP/2 (reduces throughput but eliminates connection sharing issues)

```python
import httpx
from supabase import create_client, ClientOptions

def get_service_client() -> Client:
    return create_client(
        url,
        key,
        options=ClientOptions(
            httpx_client_args={
                "http2": False,   # HTTP/1.1 — one request per connection, no multiplexing
            }
        ),
    )
```

HTTP/1.1 uses a separate TCP connection per request (with keep-alive), which is safer for
concurrent workloads but slower for sequential ones. Not recommended — `max_jobs=1` is simpler.

---

## Part 4: Database-Level Idempotency Summary

### Upsert vs Insert comparison

| Operation | On duplicate | Safe to re-run | DB requires |
|-----------|-------------|----------------|-------------|
| `INSERT` | Error (or duplicate row) | No | Nothing |
| `INSERT ... ON CONFLICT DO NOTHING` | Silently skip | Yes | UNIQUE constraint |
| `INSERT ... ON CONFLICT DO UPDATE` | Overwrite | Yes | UNIQUE constraint |
| `DELETE then INSERT` | Clean re-run | Partially | Nothing |

### Recommended migration for classifications table

```sql
-- Ensure one classification per line item (idempotency at DB level)
ALTER TABLE classifications
  ADD CONSTRAINT classifications_line_item_id_unique
  UNIQUE (line_item_id);

-- Now upsert works:
-- INSERT INTO classifications (...) VALUES (...)
-- ON CONFLICT (line_item_id) DO UPDATE SET
--   cma_field_name = EXCLUDED.cma_field_name,
--   ...
```

In Supabase Python client:
```python
service.table("classifications").upsert(
    classification_row,
    on_conflict="line_item_id",
).execute()
```

---

## Recommended for Our Project

### Priority 1: Already fixed
- `max_jobs=1` in `worker.py` — eliminates concurrent HTTP/2 overload.
- `job_timeout=3600` in `worker.py` — eliminates premature timeout kills.

### Priority 2: Add checkpoint-based resumption to `pipeline.py`

In `ClassificationPipeline.classify_document()`, before the item loop, fetch already-classified
item IDs and skip them. This makes restarts cheap and safe without changing the DB schema.

### Priority 3: Switch classifications insert to upsert

Add the UNIQUE constraint via a Supabase migration, then change all
`service.table("classifications").insert(...)` calls to `.upsert(..., on_conflict="line_item_id")`.
This is the strongest idempotency guarantee — re-running any number of times produces the same
final state.

### Priority 4: Use deterministic ARQ job IDs

When calling `redis.enqueue_job("run_classification", document_id, ...)`, pass
`_job_id=f"classify:{document_id}"`. This prevents duplicate jobs from being enqueued if the
API endpoint is called twice for the same document.
