# Agent 6: E2E Critical Path

## Your Job
Run the critical user journey through the browser (Playwright) for Dynamic Air Engineering. Focus specifically on the two steps that failed in the Mehta Computers test: file upload via react-dropzone and the Generate CMA button navigation.

## What Failed in Mehta (Confirm These Are Now Fixed)
1. **File upload** — react-dropzone component didn't respond to standard Playwright `setInputFiles` → fixed by using dragover events or direct input targeting
2. **Generate button navigation** — clicking "Generate CMA" navigated to wrong route or threw JS error → fix was applied in Phase 9

## System State
- Frontend: http://localhost:3002
- Auth: admin@cma.test / CmaAdmin@2024 (real login — E2E uses real auth, not bypass headers)
- Client already created in system: "Dynamic Air Engineering" (from Agent 3)
- CMA Report already created (from Agent 3)

## Journey (9 Steps)

### Step 1: Navigate to App
```javascript
await page.goto('http://localhost:3002');
await page.waitForLoadState('networkidle');
await expect(page).toHaveTitle(/CMA/i);
```

### Step 2: Login
```javascript
await page.fill('[data-testid="email"]', 'admin@cma.test');
await page.fill('[data-testid="password"]', 'CmaAdmin@2024');
await page.click('[data-testid="login-button"]');
await page.waitForURL('**/dashboard');
```
If login selectors differ, try: `input[type="email"]`, `input[type="password"]`, `button[type="submit"]`

### Step 3: Navigate to Dynamic Air Engineering Client
```javascript
await page.click('text=Clients');
await page.waitForURL('**/clients');
await page.click('text=Dynamic Air Engineering');
await page.waitForURL('**/clients/**');
```

### Step 4: Open the CMA Report
```javascript
await page.click('text=CMA');
// or navigate directly via report URL from Agent 3
await page.click('text=Dynamic Air Engineering CMA FY22-25');
```

### Step 5: Upload ONE Document (FY25 Excel — fastest)
This is the primary test of the file upload fix.

```javascript
// Method 1: Direct input file (if input element is accessible)
const fileInput = page.locator('input[type="file"]');
await fileInput.setInputFiles('DOCS/Financials/FY2025/Provisional financial 31.03.25 (3).xlsx');

// If Method 1 fails, use drag-and-drop simulation (Method 2):
const dropzone = page.locator('[data-testid="dropzone"]');
// or: page.locator('.dropzone') or page.locator('[class*="dropzone"]')
await dropzone.dispatchEvent('dragover');
await dropzone.dispatchEvent('drop', {
  dataTransfer: { files: ['path/to/file'] }
});
```

**Expected:** File appears in upload list, upload button activates.

### Step 6: Trigger Extraction
```javascript
await page.click('text=Extract');
// Wait for extraction to complete (may take 30-60 seconds for Excel)
await page.waitForSelector('[data-testid="extraction-complete"]', { timeout: 90000 });
// or watch for status indicator
await page.waitForFunction(() => {
  const status = document.querySelector('[class*="status"]');
  return status && status.textContent.includes('completed');
}, { timeout: 90000 });
```

### Step 7: Open Verification Screen
```javascript
await page.click('text=Verify');
// or
await page.click('[data-testid="verify-button"]');
await page.waitForURL('**/verify');
// Check that line items are visible
await expect(page.locator('table tbody tr')).toHaveCount.greaterThan(0);
```

If FY25 Excel was already extracted (from Agent 3 API test), skip upload and go directly to verification screen.

### Step 8: Trigger Classification & Click Generate CMA ← KEY TEST
This was the failure point in Mehta.

```javascript
// Approve all items
await page.click('text=Approve All');
// or
await page.click('[data-testid="approve-all"]');

// Trigger classification
await page.click('text=Classify');
await page.waitForSelector('[data-testid="classification-complete"]', { timeout: 120000 });

// NOW CLICK GENERATE — this was broken in Mehta
await page.click('text=Generate CMA');
// Should navigate to generation page or trigger download
await page.waitForURL('**/generate**', { timeout: 30000 });
// OR
await page.waitForSelector('[data-testid="generate-progress"]', { timeout: 30000 });
```

**PASS if:** Navigation succeeds and no JS error in console.
**FAIL if:** Button click does nothing, or page crashes, or console shows "TypeError".

Check console for errors:
```javascript
page.on('console', msg => {
  if (msg.type() === 'error') console.log('BROWSER ERROR:', msg.text());
});
```

### Step 9: Download Generated File ← KEY TEST
```javascript
// Wait for download prompt or download button
const [download] = await Promise.all([
  page.waitForEvent('download'),
  page.click('text=Download')
  // or page.click('[data-testid="download-button"]')
]);

// Save and verify
await download.saveAs('test-results/dynamic/e2e_downloaded_cma.xlsm');
const path = await download.path();
console.log('Downloaded to:', path);
```

**PASS if:** File downloads successfully, size > 50 KB.
**FAIL if:** Download event never fires, or error toast appears.

## Screenshot Capture
Take screenshots at key moments:
```javascript
await page.screenshot({ path: 'test-results/dynamic/e2e-step3-client.png' });
await page.screenshot({ path: 'test-results/dynamic/e2e-step7-verify.png' });
await page.screenshot({ path: 'test-results/dynamic/e2e-step8-generate.png' });
await page.screenshot({ path: 'test-results/dynamic/e2e-step9-download.png' });
```

## Playwright Setup
If Playwright is not installed on host, run via Docker or use the existing e2e setup:
```bash
cd e2e
npx playwright test --headed  # headed mode to see what's happening
```

Or write a quick inline script:
```bash
npx playwright@latest cr --browser chromium "http://localhost:3002"
```

## Output File
Write to `test-results/dynamic/agent6-e2e.md`:

```markdown
# Agent 6: E2E Results

## Journey Results
| Step | Description | Result | Notes |
|------|-------------|--------|-------|
| 1 | Navigate to app | ✅/❌ | |
| 2 | Login | ✅/❌ | |
| 3 | Find client | ✅/❌ | |
| 4 | Open report | ✅/❌ | |
| 5 | Upload file (react-dropzone) | ✅/❌ | MEHTA FAILURE — fixed? |
| 6 | Trigger extraction | ✅/❌ | |
| 7 | Verification screen | ✅/❌ | |
| 8 | Generate CMA button | ✅/❌ | MEHTA FAILURE — fixed? |
| 9 | Download file | ✅/❌ | MEHTA FAILURE — fixed? |

## Mehta Failures — Status
- File upload (react-dropzone): FIXED ✅ / STILL BROKEN ❌
- Generate button: FIXED ✅ / STILL BROKEN ❌
- Download: FIXED ✅ / STILL BROKEN ❌

## Console Errors
[List any JS console errors observed]

## Screenshots
- e2e-step7-verify.png: [description]
- e2e-step8-generate.png: [description]
```

## Gate Condition
- PASS if steps 8 and 9 both succeed (Mehta failures confirmed fixed)
- PARTIAL if steps 1-7 pass but 8-9 fail (regression — report to orchestrator)
- FAIL if steps 1-4 fail (app not running properly)
