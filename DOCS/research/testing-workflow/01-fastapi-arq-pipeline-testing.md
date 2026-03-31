# FastAPI + ARQ Pipeline Integration Testing

## The Core Problem

Your pipeline has a fundamental testing challenge: the HTTP endpoint returns 202 Accepted immediately, but the actual work (OCR, classification, Excel generation) happens asynchronously inside an ARQ worker process. A naive test that calls the endpoint and immediately asserts the result will always fail — the job hasn't run yet.

There are three distinct approaches to solving this, ordered from fastest-to-write to most realistic:

---

## Approach 1: Direct Task Testing (Recommended for Unit + Integration)

**Concept**: Bypass the HTTP layer entirely. Call the ARQ task function directly as a normal async Python function. ARQ tasks are just `async def` functions — they don't require a running worker or real Redis to be called and tested.

```python
# backend/tests/test_extraction_task.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from app.workers.extraction_tasks import run_extraction


@pytest.fixture
def mock_service():
    """A mock Supabase service client with chained call support."""
    svc = MagicMock()

    # The chain: .table().select().eq().single().execute()
    doc_result = MagicMock()
    doc_result.data = {
        "id": "doc-123",
        "file_path": "clients/client-1/balance_sheet.pdf",
        "file_type": "pdf",
        "client_id": "client-1",
        "financial_year": 2024,
    }
    (
        svc.table.return_value
        .select.return_value
        .eq.return_value
        .single.return_value
        .execute.return_value
    ) = doc_result

    # Storage download
    svc.storage.from_.return_value.download.return_value = b"%PDF-1.4 test"

    # Delete existing line items (idempotency step)
    (
        svc.table.return_value
        .delete.return_value
        .eq.return_value
        .execute.return_value
    ) = MagicMock()

    # Insert line items
    insert_result = MagicMock()
    insert_result.data = [{"id": "item-1"}]
    svc.table.return_value.insert.return_value.execute.return_value = insert_result

    # Update status
    update_result = MagicMock()
    update_result.data = [{"id": "doc-123", "extraction_status": "extracted"}]
    svc.table.return_value.update.return_value.eq.return_value.execute.return_value = update_result

    return svc


@pytest.mark.asyncio
async def test_run_extraction_happy_path(mock_service):
    """Task completes and returns correct summary dict."""
    fake_items = [
        MagicMock(
            description="Salaries & Wages",
            amount=500000.0,
            section="expenses",
            ambiguity_question=None,
        )
    ]

    with (
        patch("app.workers.extraction_tasks.get_service_client", return_value=mock_service),
        patch(
            "app.workers.extraction_tasks.extract_document",
            new_callable=AsyncMock,
            return_value=fake_items,
        ),
    ):
        ctx = {}  # ARQ passes a context dict; empty dict is fine for testing
        result = await run_extraction(ctx, "doc-123")

    assert result["document_id"] == "doc-123"
    assert result["item_count"] == 1
    assert result["status"] == "extracted"


@pytest.mark.asyncio
async def test_run_extraction_sets_failed_on_error(mock_service):
    """When extract_document raises, task sets status=failed and re-raises."""
    with (
        patch("app.workers.extraction_tasks.get_service_client", return_value=mock_service),
        patch(
            "app.workers.extraction_tasks.extract_document",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Corrupt PDF"),
        ),
    ):
        ctx = {}
        with pytest.raises(RuntimeError, match="Corrupt PDF"):
            await run_extraction(ctx, "doc-123")

    # Verify the "failed" status update was called
    calls = mock_service.table.return_value.update.call_args_list
    status_values = [c.args[0].get("extraction_status") for c in calls if c.args]
    assert "failed" in status_values


@pytest.mark.asyncio
async def test_run_extraction_document_not_found(mock_service):
    """Raises ValueError when document does not exist in DB."""
    mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None

    with patch("app.workers.extraction_tasks.get_service_client", return_value=mock_service):
        ctx = {}
        with pytest.raises(ValueError, match="Document not found"):
            await run_extraction(ctx, "nonexistent-id")


@pytest.mark.asyncio
async def test_run_extraction_idempotency(mock_service):
    """Task deletes existing line items before inserting new ones."""
    fake_items = [MagicMock(description="Revenue", amount=1000000.0, section="income", ambiguity_question=None)]

    with (
        patch("app.workers.extraction_tasks.get_service_client", return_value=mock_service),
        patch("app.workers.extraction_tasks.extract_document", new_callable=AsyncMock, return_value=fake_items),
    ):
        await run_extraction({}, "doc-123")

    # First .delete() call should have targeted extracted_line_items
    delete_calls = mock_service.table.return_value.delete.call_args_list
    assert len(delete_calls) >= 1  # At least one delete was issued
```

### Why This Works

ARQ's `ctx` dict normally contains `{"redis": <ArqRedis>, "job_id": "...", "job_try": 1, ...}`. Your tasks only use it for logging or retry logic — they don't read `ctx` in the current implementation. Passing `{}` is safe and tests the real business logic.

---

## Approach 2: Testing the HTTP Trigger (FastAPI TestClient)

This tests that `POST /api/documents/{id}/extract` correctly:
1. Validates ownership and status
2. Sets status to `processing` atomically
3. Enqueues the ARQ job
4. Returns 202 with a task_id

```python
# backend/tests/test_extraction_router.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_current_user, get_service_client
from app.models.schemas import UserProfile
from datetime import datetime, timezone


MOCK_USER = UserProfile(
    id="user-111",
    full_name="Test CA",
    role="admin",
    is_active=True,
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
)

MOCK_DOC = {
    "id": "doc-123",
    "uploaded_by": "user-111",
    "extraction_status": "pending",
    "file_type": "pdf",
    "file_path": "clients/client-1/file.pdf",
    "client_id": "client-1",
}


@pytest.fixture
def client_with_mocks():
    """TestClient with auth and Supabase fully mocked."""
    mock_svc = MagicMock()

    # Document fetch (ownership check)
    mock_svc.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = MOCK_DOC

    # Atomic status update (returns the updated row, simulating successful CAS)
    update_result = MagicMock()
    update_result.data = [{**MOCK_DOC, "extraction_status": "processing"}]
    (
        mock_svc.table.return_value
        .update.return_value
        .eq.return_value
        .in_.return_value
        .execute.return_value
    ) = update_result

    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    app.dependency_overrides[get_service_client] = lambda: mock_svc

    # Mock the ARQ pool so no real Redis connection is needed
    mock_job = MagicMock()
    mock_job.job_id = "arq-job-abc123"

    mock_pool = AsyncMock()
    mock_pool.enqueue_job.return_value = mock_job
    mock_pool.aclose = AsyncMock()

    with patch("app.routers.extraction.create_pool", return_value=mock_pool):
        with TestClient(app) as c:
            yield c

    app.dependency_overrides.clear()


def test_trigger_extraction_returns_202(client_with_mocks):
    response = client_with_mocks.post("/api/documents/doc-123/extract")
    assert response.status_code == 202
    data = response.json()
    assert data["task_id"] == "arq-job-abc123"
    assert data["document_id"] == "doc-123"


def test_trigger_extraction_409_already_processing(client_with_mocks):
    """If atomic update returns empty data, another caller already won."""
    # Override: atomic update returns no rows (lost the race)
    empty_update = MagicMock()
    empty_update.data = []
    (
        client_with_mocks.app.dependency_overrides  # we need to reset
    )
    # Simpler: patch directly inside the test
    # ... (inject the empty update result into the mock chain)
```

### Key Insight for Testing the Atomic CAS

Your `trigger_extraction` endpoint does:
```python
.update({"extraction_status": "processing"})
.eq("id", document_id)
.in_("extraction_status", list(_TRIGGERABLE_STATUSES))
.execute()
```

When testing the 409 race condition path, simulate it by making `.in_().execute()` return `data=[]`. This forces the 409 branch without needing a real database.

---

## Approach 3: Full Integration Test with Real Redis

For true end-to-end pipeline verification, use a real Redis instance (available in Docker Compose) and run the task via ARQ's `run_worker_once` or by calling the pool directly.

```python
# backend/tests/test_pipeline_integration.py
"""
Requires: Redis running locally (or via docker compose up redis -d)
Run with: pytest tests/test_pipeline_integration.py -m integration
"""
import asyncio
import pytest
from arq import create_pool
from arq.connections import RedisSettings

REDIS_SETTINGS = RedisSettings(host="localhost", port=6379)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_extraction_pipeline():
    """
    Enqueue a real ARQ job, then poll until it completes.
    Uses a test document_id that maps to pre-seeded test data.
    """
    pool = await create_pool(REDIS_SETTINGS)

    try:
        job = await pool.enqueue_job("run_extraction", "test-doc-id-fixture")

        # Poll for completion (max 30 seconds)
        result = None
        for _ in range(30):
            await asyncio.sleep(1.0)
            info = await job.info()
            if info and info.success is not None:
                result = await job.result(timeout=5)
                break

        assert result is not None, "Job did not complete within 30 seconds"
        assert result["status"] == "extracted"
        assert result["item_count"] > 0

    finally:
        await pool.aclose()
```

**When to use Approach 3**: Reserve for CI smoke tests only. Run once per deploy, not on every commit. Mark with `@pytest.mark.integration` and exclude from normal `pytest` runs.

---

## Waiting for ARQ Jobs: The Polling Pattern

ARQ's `Job.result()` blocks until the job finishes. Pair it with a timeout to avoid hanging tests:

```python
async def wait_for_arq_job(job, timeout_seconds: int = 30) -> dict:
    """Poll an ARQ job until it succeeds or times out."""
    start = asyncio.get_event_loop().time()
    while True:
        elapsed = asyncio.get_event_loop().time() - start
        if elapsed > timeout_seconds:
            raise TimeoutError(f"ARQ job {job.job_id} did not complete in {timeout_seconds}s")

        info = await job.info()
        if info is None:
            await asyncio.sleep(0.5)
            continue

        if info.success is True:
            return await job.result(timeout=5)
        elif info.success is False:
            raise RuntimeError(f"ARQ job failed: {info.result}")

        await asyncio.sleep(0.5)
```

---

## How to Handle the `ctx` Dict in ARQ Tasks

ARQ injects `ctx` with worker metadata. Your tasks currently use it only as a dict argument — they don't read it. For tasks that do use ctx (e.g., `ctx["redis"]` for chained jobs), mock it like this:

```python
# For tasks that call ctx["redis"] to enqueue follow-up jobs
mock_redis = AsyncMock()
mock_redis.enqueue_job.return_value = MagicMock(job_id="child-job-1")
ctx = {"redis": mock_redis, "job_id": "parent-job-1", "job_try": 1}

result = await run_classification(ctx, document_id="doc-123")
mock_redis.enqueue_job.assert_called_once_with("run_excel_generation", report_id="...")
```

---

## Testing Pipeline Failure Modes

```python
@pytest.mark.asyncio
async def test_classification_rejects_unverified_document(mock_service):
    """Classification task must raise if extraction_status != 'verified'."""
    mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "id": "doc-123",
        "extraction_status": "extracted",  # NOT verified
        "client_id": "client-1",
        "document_type": "balance_sheet",
        "financial_year": 2024,
    }

    with patch("app.workers.classification_tasks.get_service_client", return_value=mock_service):
        with pytest.raises(ValueError, match="requires extraction_status='verified'"):
            await run_classification({}, "doc-123")


@pytest.mark.asyncio
async def test_extraction_handles_corrupt_pdf(mock_service):
    """ExtractionError is propagated and status set to 'failed'."""
    from app.services.extraction.extractor_factory import ExtractionError

    with (
        patch("app.workers.extraction_tasks.get_service_client", return_value=mock_service),
        patch(
            "app.workers.extraction_tasks.extract_document",
            new_callable=AsyncMock,
            side_effect=ExtractionError("Cannot parse PDF: corrupted stream"),
        ),
    ):
        with pytest.raises(ExtractionError):
            await run_extraction({}, "doc-123")
```

---

## Recommended Test Structure for This Project

```
backend/tests/
├── conftest.py                    # Shared fixtures: mock_service, mock_user, sample PDFs
├── test_extraction.py             # EXISTING — unit tests for extractors
├── test_extraction_task.py        # NEW — unit tests for run_extraction ARQ task
├── test_classification_task.py    # NEW — unit tests for run_classification ARQ task
├── test_excel_task.py             # NEW — unit tests for run_excel_generation ARQ task
├── test_extraction_router.py      # NEW — HTTP layer tests (trigger endpoint, 202/409)
├── test_pipeline_failure.py       # NEW — failure mode tests across all tasks
└── integration/
    └── test_full_pipeline.py      # SEPARATE — real Redis, real Supabase, marked `integration`
```

### conftest.py Pattern

```python
# backend/tests/conftest.py
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone
from app.models.schemas import UserProfile


@pytest.fixture
def mock_admin_user():
    return UserProfile(
        id="aaaaaaaa-0000-0000-0000-000000000001",
        full_name="Test Admin",
        role="admin",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_service():
    """Base mock Supabase service client. Override per-test as needed."""
    svc = MagicMock()
    # Default: all queries return empty data
    svc.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None
    svc.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    return svc


@pytest.fixture
def sample_xlsx_bytes():
    """Minimal valid xlsx for upload tests."""
    import openpyxl, io
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Revenue", 1000000])
    ws.append(["Expenses", 600000])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
```

---

## pytest.ini / pyproject.toml Configuration

```ini
# backend/pytest.ini
[pytest]
asyncio_mode = auto
markers =
    integration: marks tests requiring real Redis/Supabase (deselect with -m "not integration")
    slow: marks tests that take >5 seconds
```

Run unit tests only:
```bash
pytest -m "not integration" --tb=short
```

Run everything including integration:
```bash
pytest --tb=short
```

---

## Recommended for Our Project

**Priority order for implementation:**

1. **Write `test_extraction_task.py` first** — directly tests `run_extraction()`, zero infrastructure needed. This is the highest-value test file because the extraction task is the most complex.

2. **Add `test_classification_task.py`** — tests the `extraction_status == 'verified'` guard, the idempotency delete loop, and error propagation. Catches the most common pipeline bugs.

3. **Add `test_extraction_router.py`** — validates the 202/409 HTTP behavior and that `create_pool().enqueue_job()` is called with the right arguments.

4. **Add `test_excel_task.py`** — tests the already-complete idempotency check and the status=failed rollback path.

5. **Add `integration/test_full_pipeline.py` last** — run manually against `docker compose up`, not in normal CI. Mark all tests with `@pytest.mark.integration`.

**Key rule**: Never have a test that calls the HTTP endpoint AND waits for the background job in the same test. Split endpoint testing and task testing into separate test files and stitch them together only in integration tests.
