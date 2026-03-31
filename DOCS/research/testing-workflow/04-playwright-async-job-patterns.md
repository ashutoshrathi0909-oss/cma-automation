# Playwright Patterns for Async / Long-Running Job Workflows

*Research date: 2026-03-20 | Applies to: CMA Automation System E2E tests*

---

## The Core Problem

Our app has two background jobs that block progress:

| Job | Trigger | Expected duration |
|-----|---------|-------------------|
| OCR extraction | Upload button | 1–5 minutes |
| Classification | "Classify" button | 5–30 minutes for large docs |

A naive Playwright test clicks the button and immediately asserts a result. This always fails because the result isn't there yet. The right solution is to **poll for a completion signal** with a sensible timeout and interval.

---

## Pattern 1: `waitForSelector` with Long Timeout (Simplest)

Playwright's built-in `waitForSelector` / `locator.waitFor` polls the DOM automatically at ~100ms intervals. You just set a large timeout.

```typescript
// Wait up to 10 minutes for the "Extraction complete" text to appear
await page.getByText(/extraction complete|extracted/i).waitFor({
  state: 'visible',
  timeout: 10 * 60 * 1000, // 10 minutes
});
```

**When to use:** When your UI already shows a completion indicator (badge, toast, status text) and you just need to wait for it.

**Limitation:** If the UI never shows the indicator because of a bug, the test hangs for the full timeout before failing. Pair it with a progress check (see Pattern 3) to fail faster on errors.

Source: [Playwright docs — locator.waitFor()](https://playwright.dev/docs/api/class-locator#locator-wait-for)

---

## Pattern 2: Custom Polling Helper (Recommended for Jobs > 1 min)

For jobs that run 5–30 minutes, build a `pollUntil` helper that:
- Checks for completion every N seconds
- Detects and throws on error states
- Logs progress to the console so you can see what's happening
- Respects an absolute deadline

```typescript
// e2e/helpers/poll.ts

/**
 * Poll the page until a condition is met or the deadline is reached.
 * Checks every `intervalMs` ms. Throws if the deadline passes.
 */
export async function pollUntil(
  page: Page,
  check: () => Promise<boolean>,
  options: {
    timeoutMs: number;      // total time to wait
    intervalMs?: number;    // how often to check (default: 10s)
    label?: string;         // logged to console
  }
): Promise<void> {
  const { timeoutMs, intervalMs = 10_000, label = 'condition' } = options;
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    const done = await check();
    if (done) return;

    const remaining = Math.round((deadline - Date.now()) / 1000);
    console.log(`  [poll] waiting for ${label} — ${remaining}s remaining`);

    await page.waitForTimeout(intervalMs);
  }

  throw new Error(`Timed out waiting for: ${label} (${timeoutMs / 1000}s)`);
}
```

**Usage in a test:**

```typescript
import { pollUntil } from '../helpers/poll';

// After clicking "Extract":
await pollUntil(
  page,
  async () => {
    // Return true when the job is done
    const statusText = await page
      .getByTestId('extraction-status')
      .textContent()
      .catch(() => '');
    return /complete|extracted|verified/i.test(statusText ?? '');
  },
  {
    timeoutMs: 10 * 60 * 1000,   // 10 minutes
    intervalMs: 15_000,           // check every 15 seconds
    label: 'OCR extraction',
  }
);
```

Source: Pattern adapted from [Playwright async patterns — Gleb Bahmutov's blog](https://glebbahmutov.com/blog/tags/polling/)

---

## Pattern 3: Polling API Endpoint Directly (Most Reliable)

Rather than reading UI text (which can change), poll the backend API directly. This decouples the test from UI copy changes.

```typescript
// e2e/helpers/api-poll.ts
import type { APIRequestContext } from '@playwright/test';

export async function waitForDocumentStatus(
  request: APIRequestContext,
  documentId: string,
  targetStatus: string,
  options: { timeoutMs: number; intervalMs?: number }
): Promise<void> {
  const { timeoutMs, intervalMs = 10_000 } = options;
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    const response = await request.get(`/api/documents/${documentId}`);
    if (!response.ok()) {
      throw new Error(`API returned ${response.status()}`);
    }
    const body = await response.json();
    const status: string = body.status ?? '';

    // Detect error states immediately — don't wait for timeout
    if (/error|failed/i.test(status)) {
      throw new Error(`Job failed with status: ${status}`);
    }

    if (status === targetStatus) return;

    console.log(`  [api-poll] document ${documentId} status="${status}" — waiting for "${targetStatus}"`);
    await new Promise(resolve => setTimeout(resolve, intervalMs));
  }

  throw new Error(`Timed out: document ${documentId} never reached status="${targetStatus}"`);
}
```

**Usage:**

```typescript
// After triggering extraction:
await waitForDocumentStatus(
  request,
  documentId,
  'extracted',
  { timeoutMs: 10 * 60 * 1000, intervalMs: 15_000 }
);
```

**Why this is better than UI polling:**
- Not affected by UI rendering bugs or text changes
- Can detect error states (`failed`, `error`) and fail fast
- Works even if the page is navigated away

---

## Pattern 4: Playwright `request` Context for Pre-Check + UI Verification

Use the API to wait for completion, then switch to page-based assertions to verify the UI reflects it.

```typescript
test('extraction completes and UI shows results', async ({ page, request }) => {
  // Step 1: Trigger via UI
  await page.getByRole('button', { name: /extract/i }).click();
  await expect(page.getByText(/processing|pending/i)).toBeVisible();

  // Step 2: Wait via API (no UI dependency on wait)
  await waitForDocumentStatus(request, documentId, 'extracted', {
    timeoutMs: 10 * 60 * 1000,
    intervalMs: 15_000,
  });

  // Step 3: Reload and verify UI shows the result
  await page.reload();
  await expect(page.getByText(/extraction complete/i)).toBeVisible();
  await expect(page.getByRole('table')).toBeVisible();
});
```

---

## Pattern 5: Progress Indicator Detection

Use progress bars and status badges to fail fast if the job enters an error state, without waiting the full timeout.

```typescript
async function waitForJobWithProgressCheck(
  page: Page,
  successSelector: string,
  errorSelector: string,
  timeoutMs: number
): Promise<void> {
  const result = await Promise.race([
    // Success
    page.locator(successSelector).waitFor({ state: 'visible', timeout: timeoutMs }),
    // Error detected
    page.locator(errorSelector).waitFor({ state: 'visible', timeout: timeoutMs })
      .then(() => { throw new Error('Job entered error state'); }),
  ]);
}

// Example usage:
await waitForJobWithProgressCheck(
  page,
  '[data-testid="extraction-complete"]',  // success indicator
  '[data-testid="extraction-error"]',     // error indicator
  10 * 60 * 1000
);
```

If your app uses a shared `[data-status="error"]` attribute on a status badge:

```typescript
// Check for error badge appearing at any point during the wait
page.locator('[data-status="error"]').waitFor({ state: 'visible', timeout: timeoutMs })
  .then(() => { throw new Error('Status badge shows error'); })
  .catch(() => {}); // ignore timeout — error just never appeared

// Wait for success
await page.getByText(/complete/i).waitFor({ state: 'visible', timeout: timeoutMs });
```

---

## Playwright Config: Timeout Strategy

For a workflow with jobs that take up to 30 minutes, the default Playwright timeout (30 seconds) will fail every test. Set timeouts at multiple levels:

```typescript
// e2e/playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  // Per-test global timeout — enough for the FULL journey
  timeout: 45 * 60 * 1000, // 45 minutes

  // Per-assertion timeout (waitForSelector, etc.)
  expect: {
    timeout: 30_000, // 30 seconds for UI assertions
  },

  use: {
    baseURL: 'http://localhost:3002',
    // Give individual actions (click, fill) enough time
    actionTimeout: 15_000,
    // Give navigation (waitForURL) enough time
    navigationTimeout: 30_000,
  },
});
```

**Current config in our project** (`e2e/playwright.config.ts`) has `timeout: 60_000` — this is 1 minute, which is only sufficient for extraction on small documents. For classification it must be increased to at least 35 minutes.

---

## Pattern 6: Test Fixtures for Shared Setup / Teardown

When running multiple tests against the same long-running workflow, use fixtures to avoid repeating the upload → extract → wait cycle:

```typescript
// e2e/fixtures.ts
import { test as base, expect } from '@playwright/test';

type WorkflowFixtures = {
  extractedDocumentId: string;
};

export const test = base.extend<WorkflowFixtures>({
  extractedDocumentId: async ({ page, request }, use) => {
    // Run setup once: upload → extract → wait
    const docId = await uploadAndExtract(page, request, 'fixtures/sample-financial.pdf');

    // Pass the ready document ID to all tests that need it
    await use(docId);

    // Optional teardown: delete the test document
    await request.delete(`/api/documents/${docId}`);
  },
});

// Tests that need an already-extracted document:
test('can edit line items', async ({ page, extractedDocumentId }) => {
  await page.goto(`/documents/${extractedDocumentId}/verify`);
  // extraction already done — no waiting needed
});
```

Source: [Playwright fixtures docs](https://playwright.dev/docs/test-fixtures)

---

## Handling the Playwright Global Test Timeout

For tests that include both a classification wait (20–30 min) and the rest of the workflow, override the timeout per-test:

```typescript
test('full journey', async ({ page }) => {
  // Override the global timeout just for this test
  test.setTimeout(40 * 60 * 1000); // 40 minutes

  // ... rest of test
});
```

---

## Summary: Polling Decision Tree

```
Is the job < 30 seconds?
  → Use waitForSelector with timeout: 30_000

Is the job 30s – 5 min?
  → Use waitForSelector with timeout: 5 * 60 * 1000
  → Add data-testid to the completion element

Is the job 5 – 30 min?
  → Use custom pollUntil helper (Pattern 2)
  → OR poll the API directly (Pattern 3)
  → Increase test.setTimeout() to job_duration + 10 min buffer
  → Log progress every interval so you can see it's not hung

Does the UI show an error badge?
  → Use Promise.race() to detect error early (Pattern 5)
```

---

## Recommended for Our Project

### Immediate Changes to `e2e/playwright.config.ts`

The current `timeout: 60_000` (1 minute) is too short for classification. Update to:

```typescript
timeout: 35 * 60 * 1000,   // 35 min — covers a 30-min classification job
expect: { timeout: 20_000 },
use: {
  actionTimeout: 15_000,
  navigationTimeout: 30_000,
},
```

### Polling Strategy Per Step

| Step | Method | Timeout | Interval |
|------|--------|---------|----------|
| Upload confirmation | `waitForSelector` | 20s | — (automatic) |
| OCR extraction | `pollUntil` + API | 10 min | 15s |
| Classify trigger | `waitForSelector` | 30s | — |
| Classification complete | `pollUntil` + API | 35 min | 30s |
| Excel generation | `waitForSelector` | 2 min | — |

### Add `data-testid` Attributes

The current `ExtractionVerifier.tsx` has no `data-testid` attributes, forcing tests to match on text content (brittle). Add:

```tsx
// On the status badge showing extraction state
<span data-testid="extraction-status" data-status={status}>...</span>

// On the "Verify All" button
<Button data-testid="verify-all-btn">Verify All</Button>
```

This makes `page.getByTestId('extraction-status')` work reliably regardless of text copy changes.

### Create `e2e/helpers/` Directory

Add `poll.ts` and `api-poll.ts` helpers as described in Patterns 2 and 3 above. These are shared across all test files and prevent duplicating polling logic.
