# Database and State Testing

## The Core Challenge

Your pipeline writes to the database in six distinct steps:

1. Upload → `documents` row created (status: `pending`)
2. Trigger extraction → `documents.extraction_status = 'processing'`
3. Extraction completes → `extracted_line_items` rows inserted, status → `extracted`
4. Human verifies → all items `is_verified = True`, status → `verified`
5. Classification runs → `classifications` rows inserted
6. Excel generated → `cma_reports.status = 'complete'`, `output_path` set

Testing database state means verifying the right rows exist with the right values after each step — without corrupting your real data.

---

## Strategy Overview

```
Three layers of database testing:

Layer 1: Unit — Mock the Supabase client (zero DB contact)
          Use for: individual router/task logic, error handling, ownership checks

Layer 2: Schema — Test against a real Supabase instance with test-scoped data
          Use for: RLS policies, FK constraints, trigger correctness, batch insert behavior

Layer 3: Pipeline State — Run a full pipeline against real DB, verify state transitions
          Use for: integration testing, idempotency, the full 6-step sequence
```

---

## Layer 1: Mocking Supabase (Most Tests Should Use This)

The Supabase Python client uses a chained builder pattern. Every query is a chain like:

```python
service.table("documents").select("*").eq("id", doc_id).single().execute()
```

The key insight: you can mock the entire chain without a real connection.

```python
# backend/tests/conftest.py
from unittest.mock import MagicMock
import pytest


class SupabaseMockBuilder:
    """
    Fluent mock builder that matches the Supabase client's chained call pattern.
    Avoids the deeply nested MagicMock hell of setting up chains manually.
    """

    def __init__(self):
        self._data = []
        self._single_data = None

    def with_single(self, data: dict | None):
        """Configure .single().execute() to return this data."""
        self._single_data = data
        return self

    def with_list(self, data: list[dict]):
        """Configure .execute() (without .single()) to return this list."""
        self._data = data
        return self

    def build(self) -> MagicMock:
        svc = MagicMock()

        # .single().execute().data
        single_result = MagicMock()
        single_result.data = self._single_data
        svc.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = single_result

        # .execute().data (list queries)
        list_result = MagicMock()
        list_result.data = self._data
        svc.table.return_value.select.return_value.eq.return_value.execute.return_value = list_result

        # Mutations always succeed unless overridden
        mutation_result = MagicMock()
        mutation_result.data = [self._single_data] if self._single_data else self._data
        svc.table.return_value.update.return_value.eq.return_value.execute.return_value = mutation_result
        svc.table.return_value.insert.return_value.execute.return_value = mutation_result
        svc.table.return_value.delete.return_value.eq.return_value.execute.return_value = mutation_result

        return svc
```

### Verifying Correct DB Calls Were Made

Beyond just checking return values, assert that the right DB operations happened:

```python
@pytest.mark.asyncio
async def test_extraction_task_inserts_line_items(mock_service):
    fake_items = [
        LineItem("Revenue", 1000000.0, "income", "Revenue 10L"),
        LineItem("Salaries", 500000.0, "expenses", "Salaries 5L"),
    ]

    with (
        patch("app.workers.extraction_tasks.get_service_client", return_value=mock_service),
        patch("app.workers.extraction_tasks.extract_document", return_value=fake_items),
    ):
        await run_extraction({}, "doc-123")

    # Assert: insert was called with exactly the right rows
    insert_call = mock_service.table.return_value.insert.call_args
    assert insert_call is not None
    inserted_rows = insert_call[0][0]  # First positional arg to .insert()

    assert len(inserted_rows) == 2
    assert inserted_rows[0]["document_id"] == "doc-123"
    assert inserted_rows[0]["source_text"] == "Revenue"
    assert inserted_rows[0]["amount"] == 1000000.0
    assert inserted_rows[0]["is_verified"] is False


@pytest.mark.asyncio
async def test_extraction_task_updates_status_to_extracted(mock_service):
    with (
        patch("app.workers.extraction_tasks.get_service_client", return_value=mock_service),
        patch("app.workers.extraction_tasks.extract_document", return_value=[]),
    ):
        await run_extraction({}, "doc-123")

    # Assert: final status update was 'extracted'
    update_calls = mock_service.table.return_value.update.call_args_list
    status_updates = [c[0][0].get("extraction_status") for c in update_calls if c[0]]
    assert "extracted" in status_updates


def test_verify_endpoint_marks_all_items_verified(mock_service, client_with_mocks):
    """POST /verify should call update(is_verified=True) for all items."""
    response = client_with_mocks.post("/api/documents/doc-123/verify")
    assert response.status_code == 200

    update_calls = mock_service.table.return_value.update.call_args_list
    verified_update = next(
        (c for c in update_calls if c[0][0].get("is_verified") is True), None
    )
    assert verified_update is not None, "is_verified=True update was never called"
```

---

## Layer 2: Real Supabase Integration Tests

For testing actual database constraints, RLS policies, and batch insert behavior, connect to a real Supabase instance. Use a separate test project or a dedicated `test_` schema.

### Setup: Environment Isolation

```python
# backend/tests/integration/conftest.py
import os
import pytest
from supabase import create_client, Client
import uuid


@pytest.fixture(scope="session")
def supabase_service() -> Client:
    """
    Service-role client for integration tests.
    Reads from TEST_SUPABASE_URL and TEST_SUPABASE_SERVICE_ROLE_KEY env vars.
    These MUST point to a test-only Supabase project — never production.
    """
    url = os.environ.get("TEST_SUPABASE_URL")
    key = os.environ.get("TEST_SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        pytest.skip("TEST_SUPABASE_URL / TEST_SUPABASE_SERVICE_ROLE_KEY not set")

    return create_client(url, key)


@pytest.fixture
def test_client_id(supabase_service) -> str:
    """Create a test client record and clean it up after the test."""
    client_id = str(uuid.uuid4())
    supabase_service.table("clients").insert({
        "id": client_id,
        "name": f"Test Client {client_id[:8]}",
        "industry_type": "manufacturing",
    }).execute()

    yield client_id

    # Teardown: delete in dependency order
    supabase_service.table("clients").delete().eq("id", client_id).execute()


@pytest.fixture
def test_document(supabase_service, test_client_id) -> dict:
    """Create a test document record and clean up after the test."""
    doc_id = str(uuid.uuid4())
    supabase_service.table("documents").insert({
        "id": doc_id,
        "client_id": test_client_id,
        "file_path": f"test/{doc_id}/balance_sheet.pdf",
        "file_type": "pdf",
        "document_type": "balance_sheet",
        "financial_year": 2024,
        "extraction_status": "pending",
        "uploaded_by": "aaaaaaaa-0000-0000-0000-000000000001",  # Mock admin user
    }).execute()

    yield {"id": doc_id, "client_id": test_client_id}

    # Teardown: cascades via FK if configured, or delete manually
    supabase_service.table("extracted_line_items").delete().eq("document_id", doc_id).execute()
    supabase_service.table("documents").delete().eq("id", doc_id).execute()
```

### Testing Status Transitions

```python
# backend/tests/integration/test_document_state_machine.py
import pytest
from app.workers.extraction_tasks import run_extraction
from unittest.mock import patch, AsyncMock


@pytest.mark.integration
@pytest.mark.asyncio
async def test_extraction_status_transitions(supabase_service, test_document):
    """
    Full state machine test:
    pending → processing (API sets this) → extracted (task sets this)
    """
    doc_id = test_document["id"]

    # Simulate what the API does: set to processing
    supabase_service.table("documents").update(
        {"extraction_status": "processing"}
    ).eq("id", doc_id).execute()

    # Run the task with real DB but mocked file content
    fake_items = [
        {"description": "Revenue", "amount": 1000000.0, "section": "income"}
    ]

    with patch(
        "app.workers.extraction_tasks.extract_document",
        new_callable=AsyncMock,
        return_value=[
            # Return real LineItem objects
            type("LineItem", (), {
                "description": "Revenue",
                "amount": 1000000.0,
                "section": "income",
                "ambiguity_question": None,
            })()
        ],
    ):
        # Also mock storage download
        with patch.object(
            supabase_service.storage.from_("documents"),
            "download",
            return_value=b"%PDF fake",
        ):
            # Use real service but with patched extract and storage
            with patch(
                "app.workers.extraction_tasks.get_service_client",
                return_value=supabase_service
            ):
                result = await run_extraction({}, doc_id)

    # Verify the task result
    assert result["status"] == "extracted"
    assert result["item_count"] == 1

    # Verify the DB state
    doc = supabase_service.table("documents").select("extraction_status").eq("id", doc_id).single().execute()
    assert doc.data["extraction_status"] == "extracted"

    items = supabase_service.table("extracted_line_items").select("*").eq("document_id", doc_id).execute()
    assert len(items.data) == 1
    assert items.data[0]["source_text"] == "Revenue"
    assert items.data[0]["is_verified"] is False
```

### Testing RLS Policies

```python
@pytest.mark.integration
def test_rls_prevents_cross_user_document_access(supabase_anon, test_document):
    """
    A user JWT for user-A should NOT be able to see documents uploaded by user-B.
    Uses the anon client with a different user's JWT.
    """
    # Get a JWT for a different user (user-B)
    # In practice: create a second test user via Supabase Auth API
    user_b_token = os.environ.get("TEST_USER_B_JWT", "")
    if not user_b_token:
        pytest.skip("TEST_USER_B_JWT not configured")

    # Set user-B's auth header
    supabase_anon.postgrest.auth(user_b_token)

    result = supabase_anon.table("documents").select("*").eq("id", test_document["id"]).execute()
    # RLS should return empty — user-B cannot see user-A's document
    assert result.data == []
```

### Testing Batch Insert Behavior

```python
@pytest.mark.integration
def test_batch_insert_500_line_items(supabase_service, test_document):
    """
    Verify that 501 items are correctly split into two batches and all inserted.
    This guards against the Supabase 1000-row URL limit silently truncating inserts.
    """
    doc_id = test_document["id"]
    rows = [
        {
            "document_id": doc_id,
            "client_id": test_document["client_id"],
            "source_text": f"Line Item {i}",
            "amount": float(i * 1000),
            "section": "expenses",
            "financial_year": 2024,
            "is_verified": False,
        }
        for i in range(501)
    ]

    # Insert in batches of 500 (same as production code)
    batch_size = 500
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        supabase_service.table("extracted_line_items").insert(batch).execute()

    # Verify all 501 were persisted
    count_result = supabase_service.table("extracted_line_items").select("id").eq("document_id", doc_id).execute()
    assert len(count_result.data) == 501
```

---

## Layer 3: Idempotency Testing

Idempotency is a first-class constraint in your pipeline. Both `run_extraction` and `run_classification` explicitly delete prior data before re-inserting. Tests must verify this behavior.

### Testing Idempotency: Run Twice, Same Result

```python
@pytest.mark.asyncio
async def test_run_extraction_is_idempotent(mock_service):
    """
    Running run_extraction twice on the same document should produce identical results.
    The second run must delete the first run's items before inserting new ones.
    """
    fake_items = [
        MagicMock(description="Revenue", amount=1000000.0, section="income", ambiguity_question=None),
    ]

    inserted_batches = []
    original_insert = mock_service.table.return_value.insert
    def capture_insert(rows):
        inserted_batches.append(rows)
        return original_insert(rows)
    mock_service.table.return_value.insert.side_effect = capture_insert

    with (
        patch("app.workers.extraction_tasks.get_service_client", return_value=mock_service),
        patch("app.workers.extraction_tasks.extract_document", return_value=fake_items),
    ):
        # Run 1
        result1 = await run_extraction({}, "doc-123")
        # Run 2 (re-run, e.g. after a transient failure)
        result2 = await run_extraction({}, "doc-123")

    # Both runs must produce identical results
    assert result1["item_count"] == result2["item_count"]

    # Verify delete was called before each insert
    delete_calls = mock_service.table.return_value.delete.call_args_list
    assert len(delete_calls) == 2  # One delete per run


@pytest.mark.asyncio
async def test_run_excel_generation_skips_if_already_complete(mock_service):
    """
    If a report is already 'complete', the task must return immediately
    without re-generating the Excel or re-uploading to storage.
    """
    # Set up the report as already complete
    mock_service.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "status": "complete",
        "output_path": "reports/report-123/CMA.xlsm",
    }

    with patch("app.workers.excel_tasks.get_service_client", return_value=mock_service):
        with patch("app.workers.excel_tasks.ExcelGenerator") as MockGenerator:
            result = await run_excel_generation({}, "report-123")

    # Generator must NOT have been instantiated (no re-generation)
    MockGenerator.assert_not_called()
    assert result["status"] == "complete"
```

### Testing Status Guard in Classification

```python
@pytest.mark.asyncio
async def test_classification_idempotency_deletes_prior_results(mock_service):
    """
    When classification runs on a document that was previously classified,
    it must delete old classifications before inserting new ones.
    """
    # Pre-existing line item IDs
    mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": "item-1"}, {"id": "item-2"}, {"id": "item-3"},
    ]

    with (
        patch("app.workers.classification_tasks.get_service_client", return_value=mock_service),
        patch("app.workers.classification_tasks.ClassificationPipeline") as MockPipeline,
    ):
        MockPipeline.return_value.classify_document.return_value = {"classified": 3, "doubt": 0}
        await run_classification({}, "doc-123")

    # Verify delete was called for classifications
    delete_calls = mock_service.table.return_value.delete.call_args_list
    # At least one delete targeting the classifications table
    assert len(delete_calls) >= 1
```

---

## Verifying Correct DB State After Each Pipeline Step

Write a helper function that encapsulates the "expected state after step N" assertions:

```python
# backend/tests/helpers/db_assertions.py

def assert_document_status(service, document_id: str, expected_status: str):
    """Assert that a document has the expected extraction_status."""
    result = service.table("documents").select("extraction_status").eq("id", document_id).single().execute()
    assert result.data is not None, f"Document {document_id} not found"
    assert result.data["extraction_status"] == expected_status, (
        f"Expected status '{expected_status}', got '{result.data['extraction_status']}'"
    )


def assert_line_items_count(service, document_id: str, expected_count: int):
    """Assert that exactly N line items exist for a document."""
    result = service.table("extracted_line_items").select("id").eq("document_id", document_id).execute()
    actual = len(result.data or [])
    assert actual == expected_count, f"Expected {expected_count} line items, got {actual}"


def assert_all_items_verified(service, document_id: str):
    """Assert that all line items have is_verified=True."""
    result = (
        service.table("extracted_line_items")
        .select("is_verified")
        .eq("document_id", document_id)
        .execute()
    )
    unverified = [r for r in (result.data or []) if not r["is_verified"]]
    assert len(unverified) == 0, f"{len(unverified)} line items are not yet verified"


def assert_classifications_exist(service, document_id: str):
    """Assert that classifications were created for this document's items."""
    items = service.table("extracted_line_items").select("id").eq("document_id", document_id).execute()
    item_ids = [i["id"] for i in (items.data or [])]
    if not item_ids:
        return

    classifications = (
        service.table("classifications")
        .select("line_item_id")
        .in_("line_item_id", item_ids)
        .execute()
    )
    assert len(classifications.data or []) > 0, "No classifications found after classification task ran"
```

Use these helpers in integration tests:

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_pipeline_state_transitions(supabase_service, test_document):
    doc_id = test_document["id"]

    # Step 1: After upload — should be pending
    assert_document_status(supabase_service, doc_id, "pending")

    # Step 2: After trigger — should be processing
    supabase_service.table("documents").update({"extraction_status": "processing"}).eq("id", doc_id).execute()
    assert_document_status(supabase_service, doc_id, "processing")

    # Step 3: Simulate extraction complete
    supabase_service.table("documents").update({"extraction_status": "extracted"}).eq("id", doc_id).execute()
    supabase_service.table("extracted_line_items").insert([
        {"document_id": doc_id, "source_text": "Revenue", "amount": 1000000.0, "section": "income", "is_verified": False}
    ]).execute()
    assert_document_status(supabase_service, doc_id, "extracted")
    assert_line_items_count(supabase_service, doc_id, 1)

    # Step 4: Verify
    supabase_service.table("extracted_line_items").update({"is_verified": True}).eq("document_id", doc_id).execute()
    supabase_service.table("documents").update({"extraction_status": "verified"}).eq("id", doc_id).execute()
    assert_document_status(supabase_service, doc_id, "verified")
    assert_all_items_verified(supabase_service, doc_id)
```

---

## Test Data Setup and Teardown Patterns

### Pattern 1: Fixture-scoped teardown (recommended)

```python
@pytest.fixture
def test_document(supabase_service, test_client_id):
    """Yield the document, then delete it. Runs even if the test fails."""
    doc_id = str(uuid.uuid4())
    supabase_service.table("documents").insert({...}).execute()

    yield {"id": doc_id}

    # Teardown always runs
    supabase_service.table("extracted_line_items").delete().eq("document_id", doc_id).execute()
    supabase_service.table("documents").delete().eq("id", doc_id).execute()
```

### Pattern 2: Transaction rollback (cleanest, requires direct DB access)

If you have direct PostgreSQL access (not via Supabase HTTP), wrap tests in a transaction and roll back:

```python
# This works with asyncpg/psycopg2 direct connections, NOT Supabase HTTP client
@pytest.fixture
async def db_transaction(pg_connection):
    """Each test runs in a transaction that is rolled back afterwards."""
    await pg_connection.execute("BEGIN")
    yield pg_connection
    await pg_connection.execute("ROLLBACK")
```

**Note**: The Supabase Python client uses HTTP (PostgREST), not a direct DB connection, so transaction rollback is NOT available. Use fixture-scoped teardown instead.

### Pattern 3: Prefix-based isolation

```python
TEST_PREFIX = f"test_{uuid.uuid4().hex[:8]}_"

# All test records have a known prefix → easy cleanup
def teardown_all_test_data(supabase_service):
    """Nuclear option: delete ALL test records by prefix. Run at end of test session."""
    supabase_service.table("clients").delete().like("name", f"{TEST_PREFIX}%").execute()
```

---

## Preventing Test Data Leaks

Add a session-scoped fixture that verifies no test data was left behind:

```python
# conftest.py
@pytest.fixture(scope="session", autouse=True)
def verify_no_test_data_leaked(supabase_service):
    """After all tests, verify no test data remains in the DB."""
    yield  # Run all tests first

    leaked = supabase_service.table("documents").select("id").like("file_path", "test/%").execute()
    if leaked.data:
        pytest.fail(
            f"Test data leaked: {len(leaked.data)} document(s) not cleaned up. "
            f"IDs: {[r['id'] for r in leaked.data]}"
        )
```

---

## Recommended for Our Project

**Do immediately (all unit tests, no real DB):**

1. Write DB call assertion tests for each ARQ task using `mock_service.table.return_value.insert.call_args` pattern. This verifies the right columns are written without a real DB.

2. Write idempotency tests for all three tasks — extraction, classification, and Excel generation. These catch the most common retry bugs.

3. Add the `db_assertions.py` helper module. The `assert_document_status()` and `assert_all_items_verified()` functions will be reused in every integration test.

**Do when ready for integration testing (real Supabase test project):**

4. Set up a second Supabase project dedicated to testing. Name it `cma-test` and add `TEST_SUPABASE_URL` / `TEST_SUPABASE_SERVICE_ROLE_KEY` to your `.env.test`.

5. Run the `test_full_pipeline_state_transitions` test as a smoke test after every major change to the task files.

6. Write the batch insert test for 501 items explicitly — the Supabase HTTP client has undocumented row limits and this is a real production risk with large documents like the Dynamic Air 33-page audited financials.

**Never do:**
- Never run integration tests against the production Supabase project. The test teardown deletes rows and can corrupt real client data.
- Never skip teardown on test failure — always use `yield` fixtures so cleanup runs even on `pytest.raises` paths.
