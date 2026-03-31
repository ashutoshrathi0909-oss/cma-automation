# Rate Limit Handling & Retry Patterns for Anthropic API

## Problem We Had

`ai_classifier.py` had a manual 3-attempt loop with hardcoded `time.sleep(5/15/30)`. When the
Anthropic API returned 429 (RateLimitError) during a 2971-item classification run:

1. The sleep delays were too short — the rate limit window did not reset.
2. After 3 exhausted retries, the item became a doubt immediately.
3. The pipeline continued calling the API for the next item, hitting the same rate limit.
4. Rapid-fire doubt + re-queue burned $4.99 in one run.

---

## How Anthropic Rate Limits Work

Source: Anthropic API docs (https://docs.anthropic.com/en/api/errors)

### Error types

| HTTP code | Class | Meaning |
|-----------|-------|---------|
| 429 | `RateLimitError` | Too many requests — back off and retry |
| 529 | `OverloadedError` | API temporarily overloaded — retry later |
| 500 | `InternalServerError` | Transient server error — retry once |
| 408 | `APITimeoutError` | Request timed out — retry |

### Rate limit headers

When a 429 is returned, Anthropic includes:
```
retry-after: 30          # seconds to wait (sometimes present)
anthropic-ratelimit-requests-remaining: 0
anthropic-ratelimit-tokens-remaining: 0
anthropic-ratelimit-tokens-reset: 2024-01-01T00:00:30Z
```

The `retry-after` header (when present) tells you the exact wait time. Our manual retry ignored
this header entirely.

### Rate limit tiers (as of 2025)

For `claude-haiku-4-5` on the lowest tier:
- **Requests per minute (RPM)**: 50
- **Tokens per minute (TPM)**: 50,000
- **Tokens per day (TPD)**: 5,000,000

For 2971 items at ~500 tokens/request: ~1.5M tokens total. That fits within TPD but easily
exceeds TPM if sent without throttling. The problem was no throttling at all.

---

## Option 1: `tenacity` Library (Recommended)

Source: https://tenacity.readthedocs.io/en/latest/ | PyPI: `tenacity>=8.2.0`

`tenacity` is the most widely used Python retry library. It supports:
- Exponential backoff with jitter
- Retry on specific exception types
- Respect for `retry-after` headers
- Before/after hooks for logging

### Basic pattern

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging
from anthropic import RateLimitError, APIStatusError

logger = logging.getLogger(__name__)

@retry(
    retry=retry_if_exception_type((RateLimitError,)),
    wait=wait_exponential(multiplier=1, min=4, max=120),
    stop=stop_after_attempt(6),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def call_anthropic(client, **kwargs):
    return client.messages.create(**kwargs)
```

### With `retry-after` header respect

```python
import time
from tenacity import retry, wait_base, stop_after_attempt

class WaitRetryAfterOrExponential(wait_base):
    """Use retry-after header if present, else exponential backoff."""

    def __call__(self, retry_state) -> float:
        exc = retry_state.outcome.exception()
        # Anthropic SDK wraps the response; check headers if available
        if hasattr(exc, "response") and exc.response is not None:
            retry_after = exc.response.headers.get("retry-after")
            if retry_after:
                try:
                    return float(retry_after) + 1.0  # +1s buffer
                except (ValueError, TypeError):
                    pass
        # Fallback: exponential backoff
        attempt = retry_state.attempt_number
        return min(4 * (2 ** (attempt - 1)), 120)  # 4, 8, 16, 32, 64, 120

@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=WaitRetryAfterOrExponential(),
    stop=stop_after_attempt(8),
    reraise=True,
)
def call_with_retry(client, **kwargs):
    return client.messages.create(**kwargs)
```

### Pattern used by Anthropic's own cookbook examples

```python
# From: https://github.com/anthropics/anthropic-cookbook
from tenacity import retry, stop_after_attempt, wait_random_exponential

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def completion_with_backoff(client, **kwargs):
    return client.messages.create(**kwargs)
```

`wait_random_exponential` adds jitter — critical when many workers all hit the limit at the same
time, as each worker wakes at a slightly different time rather than all piling on simultaneously.

---

## Option 2: `anthropic` SDK Built-in Retry

Source: https://github.com/anthropics/anthropic-sdk-python

The Anthropic Python SDK (>=0.20.0) has built-in retry with exponential backoff:

```python
client = anthropic.Anthropic(
    api_key="...",
    max_retries=4,          # default is 2
    timeout=httpx.Timeout(
        connect=5.0,
        read=120.0,
        write=10.0,
        pool=5.0,
    ),
)
```

The SDK automatically retries on:
- `RateLimitError` (429)
- `InternalServerError` (500)
- `APITimeoutError` (408)
- `OverloadedError` (529)

**Limitation**: The SDK retry uses a fixed backoff and does not expose the retry count or allow
custom wait strategies. For our use case (2971 items in sequence), the SDK retry alone is
insufficient because:

1. It retries per-request but doesn't slow down the pipeline between requests.
2. After `max_retries` exhaustion it raises — which our pipeline converts to a doubt. 2971
   doubts is not a useful outcome.

**Best practice**: Use SDK `max_retries=4` AND add a `tenacity` decorator on top, so the SDK
handles transient errors and tenacity handles sustained rate limit pressure.

---

## Option 3: Manual Retry (Our Current Approach — What's Wrong With It)

```python
# Current code in ai_classifier.py — PROBLEMATIC
_delays = [5, 15, 30]
for attempt, delay in enumerate(_delays, start=1):
    try:
        response = self._client.messages.create(...)
        return self._parse_response(response)
    except RateLimitError:
        if attempt < len(_delays):
            time.sleep(delay)
            continue
        # falls through to doubt
```

Problems:
1. **Total wait time = 5+15+30 = 50 seconds max** — far too short. Anthropic rate limit windows
   are typically 60 seconds. After 3 attempts in 50 seconds we still hit the limit.
2. **Starts over at the same delay on the next item** — no global back-off state. Item N+1 will
   immediately retry from `delay=5`.
3. **No jitter** — if two goroutines/threads hit the limit, they both sleep exactly 15s and retry
   at the same time, both hitting the limit again.
4. **Ignores `retry-after` header** — the API tells us exactly how long to wait; we don't listen.

---

## Option 4: Token-Bucket / Rate Limiter Before Each Call

Proactively throttle requests to stay under the rate limit rather than waiting for 429s.

```python
# Using the `limits` library: pip install limits
from limits import storage, strategies, parse

memory_storage = storage.MemoryStorage()
moving_window = strategies.MovingWindowRateLimiter(memory_storage)
haiku_limit = parse("40/minute")  # stay under 50 RPM with 20% headroom

def call_anthropic_throttled(client, **kwargs):
    # Block until a slot is available
    while not moving_window.hit(haiku_limit, "anthropic_haiku"):
        time.sleep(0.5)
    return client.messages.create(**kwargs)
```

This eliminates rate limit errors almost entirely by design. Best used in combination with
tenacity retry as a fallback.

---

## Comparison Table

| Approach | Handles burst | Respects retry-after | Jitter | Complexity | Our verdict |
|----------|--------------|----------------------|--------|------------|-------------|
| SDK `max_retries` | Partial | No | No | Low | Use as base layer |
| tenacity `wait_random_exponential` | Yes | No | Yes | Low | Use on top of SDK |
| tenacity + custom `WaitRetryAfterOrExponential` | Yes | Yes | Partial | Medium | Best option |
| Manual retry (current) | No | No | No | Low | Replace this |
| Token-bucket limiter | Yes (proactive) | N/A | N/A | Medium | Add as complement |

---

## Recommended for Our Project

### Immediate fix (drop-in replacement for current code)

In `backend/app/services/classification/ai_classifier.py`, replace the manual retry loop with:

```python
# requirements.txt: add tenacity>=8.2.0
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError,
)
from anthropic import RateLimitError, OverloadedError, InternalServerError

_RETRYABLE = (RateLimitError, OverloadedError, InternalServerError)

class AIClassifier:
    def __init__(self) -> None:
        settings = get_settings()
        # SDK-level: handles connection errors + 2 quick retries
        self._client = Anthropic(
            api_key=settings.anthropic_api_key,
            max_retries=2,
        )

    def _call_api(self, **kwargs):
        """Inner API call wrapped with tenacity retry."""
        return self._client.messages.create(**kwargs)

    # Tenacity retry: exponential backoff, 8 attempts, max 90s wait
    # Total max wait: ~4+8+16+32+64+90+90+90 = ~394s before giving up
    _call_api_with_retry = retry(
        retry=retry_if_exception_type(_RETRYABLE),
        wait=wait_random_exponential(multiplier=2, min=4, max=90),
        stop=stop_after_attempt(8),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )(_call_api)

    def classify(self, ...) -> AIClassificationResult:
        try:
            response = self._call_api_with_retry(
                model=HAIKU_MODEL,
                max_tokens=1024,
                tools=[_TOOL_SCHEMA],
                tool_choice={"type": "tool", "name": "classify_line_item"},
                messages=[{"role": "user", "content": prompt}],
            )
            return self._parse_response(response)
        except RetryError:
            # All 8 attempts failed — return doubt, do NOT re-raise into pipeline
            logger.error("classify '%s': exhausted all retries (rate limit)", raw_text[:60])
            return _doubt_result("Rate limit: exhausted all retries after ~6 min")
        except Exception as exc:
            logger.error("classify '%s': %s", raw_text[:60], exc)
            return _doubt_result(f"API error: {type(exc).__name__}")
```

### Also add: inter-item throttle in `pipeline.py`

After each AI call, sleep briefly to stay well under the 50 RPM limit:

```python
import time

# In classify_document() loop, after the AI classify_item() call:
time.sleep(1.2)   # ~50 items/min, stays under 50 RPM with headroom
```

With 2971 items and 50% going to fuzzy (no AI call), ~1485 AI calls at 1.2s spacing
= ~30 minutes total. This is acceptable for a background ARQ job.

### Budget protection companion

See `03-budget-guardrails-and-monitoring.md` for how to abort classification before it starts
if the estimated token cost exceeds a budget cap.
