# Budget Guardrails & Monitoring for LLM Pipelines

## Problem We Had

$4.99 was burned in a single test run because:
1. RateLimitErrors triggered doubt → but the API was still called for every item before
   the error, generating token charges.
2. After retries (even wrong ones), the pipeline re-queued, calling the API again for items
   that had already been attempted and charged.
3. There was no pre-run estimate, no live cost counter, and no abort threshold.

---

## Part 1: Token Counting Before the Run

### Anthropic token counting API

Source: https://docs.anthropic.com/en/api/messages-count-tokens

The Anthropic SDK (>=0.36.0) provides a `count_tokens` endpoint that counts tokens for a
messages payload **without making an inference call** (free to call):

```python
import anthropic

client = anthropic.Anthropic(api_key="...")

# Count tokens for a single classify_item prompt
response = client.messages.count_tokens(
    model="claude-haiku-4-5-20251001",
    tools=[_TOOL_SCHEMA],
    messages=[{"role": "user", "content": prompt}],
)
print(response.input_tokens)   # e.g., 850 tokens for one item
```

### Pre-run cost estimation

Run this before starting classification:

```python
from anthropic import Anthropic
from app.config import get_settings

# Claude Haiku 4.5 pricing (as of 2025):
# Input:  $0.80 per 1M tokens
# Output: $4.00 per 1M tokens
HAIKU_INPUT_PRICE_PER_TOKEN  = 0.80  / 1_000_000
HAIKU_OUTPUT_PRICE_PER_TOKEN = 4.00  / 1_000_000

# Typical output per classify call: tool_use block ≈ 300 tokens
AVG_OUTPUT_TOKENS = 300

def estimate_classification_cost(
    line_items: list[dict],
    fuzzy_pass_rate: float = 0.50,  # estimated % resolved by fuzzy (no AI call)
) -> dict:
    """Estimate the cost of classifying all line_items via AI."""
    client = Anthropic(api_key=get_settings().anthropic_api_key)

    # Sample 5 items to get average input tokens
    sample = line_items[:5]
    sample_tokens = []
    for item in sample:
        prompt = _build_prompt(item)  # use your existing prompt builder
        r = client.messages.count_tokens(
            model="claude-haiku-4-5-20251001",
            tools=[_TOOL_SCHEMA],
            messages=[{"role": "user", "content": prompt}],
        )
        sample_tokens.append(r.input_tokens)

    avg_input_tokens = sum(sample_tokens) / len(sample_tokens)

    # Items that go to AI (after fuzzy tier skips some)
    ai_items = int(len(line_items) * (1 - fuzzy_pass_rate))

    total_input_tokens  = avg_input_tokens * ai_items
    total_output_tokens = AVG_OUTPUT_TOKENS * ai_items

    cost_usd = (
        total_input_tokens  * HAIKU_INPUT_PRICE_PER_TOKEN +
        total_output_tokens * HAIKU_OUTPUT_PRICE_PER_TOKEN
    )

    return {
        "total_items": len(line_items),
        "ai_items_estimated": ai_items,
        "avg_input_tokens": round(avg_input_tokens),
        "total_input_tokens": round(total_input_tokens),
        "total_output_tokens": round(total_output_tokens),
        "estimated_cost_usd": round(cost_usd, 4),
    }
```

**Example for our 2971-item run**:
- 50% fuzzy pass rate → ~1485 AI calls
- ~850 input tokens/call → 1,261,250 input tokens = $1.01
- ~300 output tokens/call → 445,500 output tokens = $1.78
- **Total estimate: ~$2.79**

The actual $4.99 overage came from repeated re-runs due to timeout+restart loops and rate limit
retries, not from a single clean run.

---

## Part 2: Per-Run Budget Cap

### Simple budget cap in the classification pipeline

```python
import os

# Set MAX_CLASSIFICATION_COST_USD=3.00 in .env for testing
MAX_CLASSIFICATION_COST_USD = float(
    os.getenv("MAX_CLASSIFICATION_COST_USD", "999.0")  # default: no limit
)

class ClassificationPipeline:

    def classify_document(self, document_id, ...) -> dict:
        service = get_service_client()
        line_items = _fetch_all_line_items(service, document_id)

        # --- PRE-RUN ESTIMATE ---
        estimate = estimate_classification_cost(line_items)
        logger.info(
            "classify_document cost estimate: %d items → %d AI calls → $%.4f",
            estimate["total_items"],
            estimate["ai_items_estimated"],
            estimate["estimated_cost_usd"],
        )

        if estimate["estimated_cost_usd"] > MAX_CLASSIFICATION_COST_USD:
            raise BudgetExceededError(
                f"Estimated cost ${estimate['estimated_cost_usd']:.4f} exceeds "
                f"cap ${MAX_CLASSIFICATION_COST_USD:.2f}. "
                f"Set SKIP_AI_CLASSIFICATION=true or increase MAX_CLASSIFICATION_COST_USD."
            )

        # --- LIVE COST TRACKING ---
        tokens_used = {"input": 0, "output": 0}
        cost_so_far = 0.0
        aborted = False

        for item in line_items:
            if aborted:
                break

            classification = self.classify_item(item, ...)

            # Track tokens from the last AI call (if any)
            if hasattr(self._ai, "last_usage"):
                usage = self._ai.last_usage
                tokens_used["input"]  += usage.input_tokens
                tokens_used["output"] += usage.output_tokens
                cost_so_far = (
                    tokens_used["input"]  * HAIKU_INPUT_PRICE_PER_TOKEN +
                    tokens_used["output"] * HAIKU_OUTPUT_PRICE_PER_TOKEN
                )

                if cost_so_far > MAX_CLASSIFICATION_COST_USD:
                    logger.error(
                        "BUDGET CAP EXCEEDED: $%.4f > $%.2f — aborting classification",
                        cost_so_far, MAX_CLASSIFICATION_COST_USD,
                    )
                    aborted = True

            service.table("classifications").upsert(classification, ...).execute()

        return {
            "total": len(line_items),
            "cost_usd": round(cost_so_far, 4),
            "aborted": aborted,
            ...
        }
```

### Tracking actual token usage from the API response

The Anthropic SDK returns `usage` in every response:

```python
response = client.messages.create(...)
print(response.usage.input_tokens)   # actual input tokens charged
print(response.usage.output_tokens)  # actual output tokens charged
```

Capture this in `AIClassifier.classify()` and expose it:

```python
class AIClassifier:
    def __init__(self):
        self.last_usage = None   # Set after each successful call

    def classify(self, ...) -> AIClassificationResult:
        ...
        response = self._call_api_with_retry(...)
        self.last_usage = response.usage   # capture for pipeline to read
        return self._parse_response(response)
```

---

## Part 3: Logging and Observability

### Structured logging for the pipeline

Use Python's built-in `logging` with structured context — no external tools needed for V1:

```python
import logging
import json
import time

logger = logging.getLogger(__name__)

class PipelineLogger:
    """Thin wrapper that emits structured log lines for each item."""

    def __init__(self, document_id: str, total_items: int):
        self.document_id = document_id
        self.total = total_items
        self.done = 0
        self.cost = 0.0
        self.start_time = time.monotonic()

    def log_item(self, item_id: str, method: str, is_doubt: bool, cost_delta: float):
        self.done += 1
        self.cost += cost_delta
        elapsed = time.monotonic() - self.start_time
        eta_seconds = (elapsed / self.done) * (self.total - self.done) if self.done else 0

        logger.info(
            "item=%s method=%s doubt=%s progress=%d/%d cost=$%.4f eta=%.0fs",
            item_id[:8], method, is_doubt, self.done, self.total, self.cost, eta_seconds,
        )
```

Log output example:
```
item=3fa8c21a method=fuzzy_match doubt=False progress=145/2971 cost=$0.0231 eta=1834s
item=7b2d19e3 method=ai_haiku    doubt=False progress=146/2971 cost=$0.0240 eta=1833s
item=a1f0ce57 method=ai_haiku    doubt=True  progress=147/2971 cost=$0.0249 eta=1832s
```

This gives full visibility in Docker logs (`docker compose logs -f backend`) with no external
tools.

### Log the budget state periodically

```python
# Log a budget summary every 100 items
if self.done % 100 == 0:
    logger.warning(
        "BUDGET CHECKPOINT: %d/%d items done, cost=$%.4f/cap=$%.2f (%.1f%%)",
        self.done, self.total, self.cost, MAX_CAP, (self.cost/MAX_CAP)*100,
    )
```

---

## Part 4: External Monitoring Tools (for later, not V1)

### Helicone (simplest LLM cost monitor)

Source: https://helicone.ai/

Drop-in proxy — change one line:

```python
client = anthropic.Anthropic(
    api_key="...",
    base_url="https://anthropic.helicone.ai",
    default_headers={"Helicone-Auth": f"Bearer {helicone_api_key}"},
)
```

Helicone then logs every request, tracks token counts, calculates cost, and provides a
dashboard. Free tier: 100k requests/month. No code changes needed beyond the two lines above.

**Best for**: production monitoring after V1 launches.

### LangSmith (LangChain's tracing platform)

Source: https://www.langchain.com/langsmith

More heavyweight — requires wrapping calls in LangChain primitives or manually sending traces.
Overkill for our direct Anthropic SDK usage. Skip for V1.

### Simple token log file (no external service)

Write a `.jsonl` file per run:

```python
import json
from datetime import datetime, timezone
from pathlib import Path

TOKEN_LOG = Path("/app/logs/token_usage.jsonl")

def log_token_usage(document_id: str, item_id: str, usage, cost: float):
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "document_id": document_id,
        "item_id": item_id,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "cost_usd": cost,
    }
    with TOKEN_LOG.open("a") as f:
        f.write(json.dumps(record) + "\n")
```

After a run, load the file and sum costs:
```bash
python -c "
import json
total = sum(json.loads(l)['cost_usd'] for l in open('logs/token_usage.jsonl'))
print(f'Total cost: \${total:.4f}')
"
```

---

## Part 5: How Production Teams Handle LLM Cost Control

### Pattern: Pre-run estimate + manual approval gate

Many teams building LLM pipelines on batch data add a manual approval step:

```python
async def start_classification(document_id: str, auto_approve_under: float = 1.00):
    line_items = fetch_line_items(document_id)
    estimate = estimate_classification_cost(line_items)

    if estimate["estimated_cost_usd"] > auto_approve_under:
        # Block the job and ask for human approval via the UI
        await service.table("documents").update({
            "extraction_status": "awaiting_cost_approval",
            "cost_estimate_usd": estimate["estimated_cost_usd"],
        }).eq("id", document_id).execute()
        return {"status": "awaiting_approval", "estimate": estimate}

    # Under threshold: auto-proceed
    await redis.enqueue_job("run_classification", document_id)
    return {"status": "queued", "estimate": estimate}
```

The frontend shows the estimate and a "Proceed" button. This is the cleanest UX for a CA firm
where the user controls costs.

### Pattern: Daily / monthly spend caps in environment variables

```bash
# .env (test environment)
MAX_CLASSIFICATION_COST_USD=2.00    # Hard stop per classification job
MAX_DAILY_AI_SPEND_USD=10.00        # Soft alert; tracked in Redis counter
```

Track daily spend in Redis:
```python
async def check_daily_budget(redis, cost_delta: float) -> bool:
    """Increment daily spend counter. Return False if budget exceeded."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    key = f"ai_spend:{today}"
    new_total = await redis.incrbyfloat(key, cost_delta)
    await redis.expire(key, 86400 * 2)   # TTL: 2 days

    max_daily = float(os.getenv("MAX_DAILY_AI_SPEND_USD", "999"))
    if new_total > max_daily:
        logger.error("DAILY BUDGET EXCEEDED: $%.4f > $%.2f", new_total, max_daily)
        return False
    return True
```

### Pattern: Batch mode — collect all prompts, send in one API call

For classification, instead of one API call per item, send all items in a single prompt:

```python
# Batch classify: send 20 items in one Haiku call
# Tokens: 20 * 200 (description) + shared schema overhead ≈ 5000 input tokens
# Cost: 5000 * $0.80/1M = $0.004 per batch vs $0.0008 * 20 = same but fewer API calls

# Benefits: fewer API round trips, less rate-limit exposure, lower latency
# Risks: larger output, harder to parse, one item error affects all 20
```

This is an advanced optimization — not needed for V1. The per-item approach gives clearer
doubt attribution.

---

## Recommended for Our Project

### Immediate: Add cost estimation before classification starts

In `classification_tasks.py` (the ARQ task), before calling `pipeline.classify_document()`:

1. Fetch line item count.
2. Estimate cost using the sampling method above.
3. Log the estimate prominently.
4. If `estimate > MAX_CLASSIFICATION_COST_USD` (env var, default `$5.00` for testing), raise
   and set document status to `"classification_failed"` with a clear message.

### Immediate: Add `SKIP_AI_CLASSIFICATION=true` to test `.env`

Already present in `pipeline.py`. Use this for all test runs that do not specifically test
AI classification. Saves money and time. Re-enable only when testing AI behaviour.

### Short-term: Live token tracking in AIClassifier

Capture `response.usage` after each call and pass it back through the pipeline so the
orchestrator can track running cost and abort if the cap is hit mid-run.

### Short-term: Log cost summary at end of each job

Add to the `run_classification` task return dict:
```python
return {
    "document_id": document_id,
    "status": "classified",
    "cost_usd": pipeline.total_cost_usd,   # new field
    **summary,
}
```

ARQ stores this result in Redis and it appears in job logs, giving full post-run visibility
without any external tools.

### Later (post-V1): Helicone

One `base_url` change gives a hosted dashboard for all API calls. Useful once the system is
handling multiple clients per day and you need per-client cost attribution.
