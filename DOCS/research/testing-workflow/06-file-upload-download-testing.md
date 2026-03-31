# File Upload and Download Testing in Playwright

*Research date: 2026-03-20 | Applies to: CMA Automation System E2E tests*

---

## Part 1: PDF Upload Testing

### How File Upload Works in Playwright

Playwright handles file uploads through the `setInputFiles()` method on a file `<input>` element. This bypasses the OS file picker dialog entirely — no native dialog handling needed.

```typescript
// Most direct approach — works when input[type="file"] is in the DOM
const fileInput = page.locator('input[type="file"]');
await fileInput.setInputFiles('/absolute/path/to/document.pdf');
```

This is already the pattern used in our `full-journey.spec.ts`:

```typescript
const fileInput = page.locator('input[type="file"]')
await fileInput.setInputFiles(FIXTURE_PATH)
```

Source: [Playwright docs — page.setInputFiles](https://playwright.dev/docs/api/class-locator#locator-set-input-files)

---

### Pattern 1: Direct `setInputFiles` (Simple Case)

Works when the `<input type="file">` is visible and accessible in the DOM.

```typescript
test('upload PDF document', async ({ page }) => {
  await page.goto('/upload');

  // Set the file — Playwright fills it without showing OS dialog
  await page.locator('input[type="file"]').setInputFiles(
    path.join(__dirname, 'fixtures', 'financial-statement.pdf')
  );

  // Verify file name appears in the UI
  await expect(page.getByText('financial-statement.pdf')).toBeVisible();

  // Submit
  await page.getByRole('button', { name: /upload/i }).click();
  await expect(page.getByText(/uploaded|success|pending/i)).toBeVisible({
    timeout: 20_000,
  });
});
```

---

### Pattern 2: Hidden File Input (shadcn `<Input type="file">`)

shadcn/ui's file input is sometimes visually hidden and triggered by a styled button. Playwright's `setInputFiles` works on hidden inputs too — you don't need to make it visible first.

```typescript
// Even if the input has display:none or opacity:0, this works:
await page.locator('input[type="file"]').setInputFiles(filePath, {
  // Force allows interacting with hidden elements
  // Note: in Playwright, setInputFiles() does NOT need force: true —
  // it bypasses visibility checks automatically
});
```

If there are multiple file inputs on the page, scope to the right one:

```typescript
// Within a specific upload section
const uploadSection = page.getByTestId('document-upload-zone');
await uploadSection.locator('input[type="file"]').setInputFiles(filePath);
```

---

### Pattern 3: FileChooser for Dynamic Inputs (Drop Zone or Button-Triggered)

Some upload UIs don't have a static `<input type="file">` in the DOM — the input is created dynamically when you click an "Upload" button. Use `page.waitForEvent('filechooser')`:

```typescript
test('upload via file chooser', async ({ page }) => {
  await page.goto('/upload');

  // Set up the listener BEFORE clicking the trigger
  const fileChooserPromise = page.waitForEvent('filechooser');

  // Click the button that triggers the native file dialog
  await page.getByRole('button', { name: /choose file|browse/i }).click();

  // Wait for the chooser to appear, then set the file
  const fileChooser = await fileChooserPromise;
  await fileChooser.setFiles(path.join(__dirname, 'fixtures', 'sample.pdf'));

  // Continue with upload
  await page.getByRole('button', { name: /upload/i }).click();
});
```

Source: [Playwright docs — FileChooser](https://playwright.dev/docs/api/class-filechooser)

---

### Pattern 4: Drag-and-Drop Upload Zone

If the upload UI uses a drag-and-drop zone (common in React with `react-dropzone`), Playwright can simulate a file drop using `dispatchEvent`:

```typescript
async function dropFile(page: Page, dropzone: Locator, filePath: string): Promise<void> {
  // Read the file as a base64 string via Node.js (in a test)
  const buffer = require('fs').readFileSync(filePath);
  const base64 = buffer.toString('base64');
  const fileName = require('path').basename(filePath);
  const mimeType = 'application/pdf';

  await dropzone.dispatchEvent('drop', {
    dataTransfer: await page.evaluateHandle(
      ({ base64, fileName, mimeType }) => {
        const dt = new DataTransfer();
        const blob = Blob.fromBase64(base64, mimeType); // not standard
        const file = new File([blob], fileName, { type: mimeType });
        dt.items.add(file);
        return dt;
      },
      { base64, fileName, mimeType }
    ),
  });
}
```

**Easier alternative:** Many drop zones also accept `setInputFiles` on the underlying hidden input. Try that first before implementing drag-and-drop simulation.

---

### Pattern 5: Multiple File Upload

For uploading multiple PDFs at once (e.g., multiple years of financials):

```typescript
await page.locator('input[type="file"]').setInputFiles([
  path.join(__dirname, 'fixtures', 'fy2024-balance-sheet.pdf'),
  path.join(__dirname, 'fixtures', 'fy2023-balance-sheet.pdf'),
  path.join(__dirname, 'fixtures', 'fy2022-balance-sheet.pdf'),
]);
```

This works when the `<input>` has the `multiple` attribute.

---

### Upload Fixtures: Best Practices

Place test files in `e2e/fixtures/`. For PDF testing:

```
e2e/
  fixtures/
    sample.xlsx           ← already exists in our project
    sample-small.pdf      ← small PDF for fast upload tests (< 1MB, 5 pages)
    sample-scanned.pdf    ← scanned PDF to test OCR path (10–20 pages)
    sample-digital.pdf    ← digital/text PDF (faster OCR)
    sample-corrupt.pdf    ← invalid PDF for error handling tests
```

Use real but anonymized PDFs — the extraction pipeline behavior is sensitive to actual PDF structure. A 1-page text PDF and a 20-page scanned PDF will exercise completely different code paths.

---

### Validating the Upload Response

After clicking Upload, validate both the UI state and (optionally) the API response:

```typescript
// UI validation
await expect(page.getByText(/success|uploaded|pending/i)).toBeVisible({
  timeout: 20_000,
});

// API validation (more reliable)
const [uploadResponse] = await Promise.all([
  page.waitForResponse(
    response => response.url().includes('/api/documents') && response.request().method() === 'POST'
  ),
  page.getByRole('button', { name: /upload/i }).click(),
]);

expect(uploadResponse.status()).toBe(200);
const body = await uploadResponse.json();
expect(body).toHaveProperty('id');
expect(body.status).toBe('pending');

// Capture the document ID for later steps
const documentId = body.id;
```

---

## Part 2: Excel File Download Testing

### How Playwright Handles Downloads

Playwright intercepts downloads through the `page.waitForEvent('download')` pattern. The download object gives you access to the suggested filename and a path to save the file.

```typescript
// CRITICAL: set up the download listener BEFORE clicking the download button
const downloadPromise = page.waitForEvent('download');

await page.getByRole('button', { name: /download/i }).click();

const download = await downloadPromise;
```

Source: [Playwright docs — Download](https://playwright.dev/docs/api/class-download)

---

### Pattern 1: Intercept and Verify Filename

The simplest check — verify the downloaded file has the right extension:

```typescript
test('downloads Excel file with correct extension', async ({ page }) => {
  await page.goto(reportUrl);

  const downloadPromise = page.waitForEvent('download', { timeout: 15_000 });
  await page.getByRole('button', { name: /download/i }).click();
  const download = await downloadPromise;

  // Verify filename
  expect(download.suggestedFilename()).toMatch(/\.(xlsm?|xlsx)$/i);
  expect(download.suggestedFilename()).toContain('CMA');

  console.log('Downloaded file:', download.suggestedFilename());
});
```

This is already implemented in our `full-journey.spec.ts`:

```typescript
const downloadPromise = page.waitForEvent("download", { timeout: 15_000 }).catch(() => null)
await downloadBtn.click()
const download = await downloadPromise
if (download) {
  expect(download.suggestedFilename()).toMatch(/\.(xlsm?|xlsx)$/)
}
```

---

### Pattern 2: Save File and Verify Contents

To verify the actual file content (not just the name), save the download to a temp path and inspect it:

```typescript
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

test('downloaded Excel contains expected sheets', async ({ page }) => {
  await page.goto(reportUrl);

  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: /download/i }).click();
  const download = await downloadPromise;

  // Save to a temp file
  const tmpPath = path.join(os.tmpdir(), download.suggestedFilename());
  await download.saveAs(tmpPath);

  // Verify the file exists and has content
  const stat = fs.statSync(tmpPath);
  expect(stat.size).toBeGreaterThan(10_000); // real Excel files are > 10KB

  // Optional: verify it's a valid ZIP (xlsx/xlsm are ZIP archives)
  const header = Buffer.alloc(4);
  const fd = fs.openSync(tmpPath, 'r');
  fs.readSync(fd, header, 0, 4, 0);
  fs.closeSync(fd);
  expect(header.toString('hex')).toBe('504b0304'); // PK ZIP magic bytes

  // Cleanup
  fs.unlinkSync(tmpPath);
});
```

**Why check the ZIP magic bytes?** An Excel file that fails to generate might be replaced with an error HTML page (served with the wrong Content-Type) or an empty file. The ZIP header check confirms it's actually an Excel archive.

---

### Pattern 3: Parse Excel Content with `exceljs`

For deep verification — checking that specific cells have the right values — use the `exceljs` library in the test:

```typescript
import ExcelJS from 'exceljs';
import * as path from 'path';
import * as os from 'os';

test('CMA Excel has correct sheet names and data', async ({ page }) => {
  // Download
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: /download/i }).click();
  const download = await downloadPromise;

  const tmpPath = path.join(os.tmpdir(), download.suggestedFilename());
  await download.saveAs(tmpPath);

  // Parse with exceljs
  const workbook = new ExcelJS.Workbook();
  await workbook.xlsx.readFile(tmpPath);

  // Verify expected sheets exist
  const sheetNames = workbook.worksheets.map(ws => ws.name);
  expect(sheetNames).toContain('INPUT SHEET');
  expect(sheetNames).toContain('TL Sheet');

  // Verify a specific cell value (e.g., the client name in INPUT SHEET)
  const inputSheet = workbook.getWorksheet('INPUT SHEET');
  expect(inputSheet).not.toBeNull();

  // Check that the sheet has data (at least some rows filled)
  const usedRows = inputSheet!.rowCount;
  expect(usedRows).toBeGreaterThan(10);

  // Check a specific cell — adjust row/column to match your CMA template
  // const clientNameCell = inputSheet!.getCell('B2').value;
  // expect(String(clientNameCell)).toContain('Test Company');
});
```

**Install exceljs in the e2e package:**
```bash
cd e2e && npm install exceljs
```

Source: [exceljs GitHub](https://github.com/exceljs/exceljs)

---

### Pattern 4: Handle Download via Signed URL (Supabase Storage)

Our backend serves the Excel file via a Supabase Storage signed URL. This means the download may open in a new tab or redirect rather than triggering a standard browser download event.

There are two scenarios:

**Scenario A: Button triggers `window.open(signedUrl)` or `<a href="..." download>`**
In this case, the `download` event fires and Pattern 1/2 above work as-is.

**Scenario B: Button navigates the browser to the signed URL**
The `download` event does NOT fire. Instead, the browser downloads the file directly. To handle this:

```typescript
// Use page.waitForResponse to intercept the Supabase storage request
const [response] = await Promise.all([
  page.waitForResponse(
    r => r.url().includes('supabase') && r.url().includes('.xlsm'),
    { timeout: 15_000 }
  ),
  page.getByRole('button', { name: /download/i }).click(),
]);

expect(response.status()).toBe(200);
const contentType = response.headers()['content-type'];
expect(contentType).toMatch(/spreadsheet|octet-stream|zip/i);

// Get the file bytes directly
const fileBuffer = await response.body();
expect(fileBuffer.length).toBeGreaterThan(10_000);
```

**Scenario C: Download link is a plain `<a>` tag with `download` attribute**
This is the simplest — the browser download event fires automatically.

To check which scenario your app uses, run this in a test and inspect the console output:

```typescript
// Debug: log all download events and navigation events
page.on('download', d => console.log('DOWNLOAD EVENT:', d.suggestedFilename()));
page.on('response', r => {
  if (r.url().includes('storage') || r.url().includes('.xlsm')) {
    console.log('RESPONSE:', r.status(), r.url());
  }
});
```

---

### Pattern 5: Download Without a Click — Direct API Verification

For the case where you just need to verify the file was generated correctly (not necessarily that the UI download works), call the API directly:

```typescript
test('generated Excel file is accessible via API', async ({ request }) => {
  // Get the download URL from the API
  const response = await request.get(`/api/cma-reports/${reportId}/download`);
  expect(response.status()).toBe(200);

  const body = await response.json();
  expect(body).toHaveProperty('url'); // signed URL from Supabase

  // Fetch the actual file
  const fileResponse = await request.get(body.url);
  expect(fileResponse.status()).toBe(200);

  const contentType = fileResponse.headers()['content-type'];
  expect(contentType).toMatch(/spreadsheet|octet-stream/i);

  const fileBytes = await fileResponse.body();
  expect(fileBytes.length).toBeGreaterThan(10_000);

  // Check ZIP magic bytes
  expect(fileBytes.slice(0, 4).toString('hex')).toBe('504b0304');
});
```

This is faster than UI testing (no browser rendering) and more reliable (no download dialog variability).

---

## Part 3: Table UI Testing (Verification Step)

The extraction verifier shows a table of line items extracted from the PDF. Testing this table is the most complex part of the journey because:
- Row count is variable (10–500+ rows depending on the document)
- Each row has an editable amount field (the `LineItemEditor` component)
- Rows don't have stable IDs in the DOM

### Count Table Rows

```typescript
// After extraction completes and the verify page loads:
const rows = page.locator('table tbody tr');
// OR if using a div-based table:
const rows = page.locator('[data-testid="line-item-row"]');

const rowCount = await rows.count();
console.log(`Extracted ${rowCount} line items`);
expect(rowCount).toBeGreaterThan(0);
```

### Verify Specific Row Content

```typescript
// Find a row containing specific text
const salesRow = page.locator('tr').filter({ hasText: /sales|revenue/i }).first();
await expect(salesRow).toBeVisible();

// Check the amount column in that row
const amountCell = salesRow.locator('td').nth(2); // adjust column index
await expect(amountCell).not.toHaveText('—'); // should have an amount, not null
```

### Edit a Line Item Amount (Testing `LineItemEditor`)

The `LineItemEditor` component shows the amount as text, then switches to an input when clicked:

```typescript
// Click the amount cell to enter edit mode
const firstRow = page.locator('tr').first();
const amountDisplay = firstRow.locator('[data-testid="amount-display"]');
await amountDisplay.click(); // triggers editing state

// Input field should appear
const amountInput = firstRow.locator('input[type="number"], input[inputmode="numeric"]');
await expect(amountInput).toBeVisible();

// Type a new value
await amountInput.clear();
await amountInput.fill('1500000');

// Save (click the checkmark / Save button)
await firstRow.getByRole('button', { name: /save|confirm/i }).click();
// OR press Enter
await amountInput.press('Enter');

// Verify the display shows the new value
await expect(amountDisplay).toHaveText(/1,50,000|1500000/); // Indian number format
```

### Bulk Verify All Items

```typescript
// If "Verify All" button exists, click it
const verifyAllBtn = page.getByRole('button', { name: /verify all|confirm all/i });
await verifyAllBtn.click();

// Should see success toast or status change
await expect(page.getByText(/verified|confirmed/i)).toBeVisible({ timeout: 10_000 });
```

---

## Summary: File Testing Checklist

| Test type | Playwright method | Notes |
|-----------|------------------|-------|
| Upload via file input | `locator('input[type="file"]').setInputFiles(path)` | Works on hidden inputs too |
| Upload via button (dynamic input) | `page.waitForEvent('filechooser')` | Set up before clicking |
| Verify upload success | `waitForResponse` + check `status: 'pending'` | More reliable than UI text |
| Intercept download | `page.waitForEvent('download')` | Set up before clicking |
| Verify filename | `download.suggestedFilename()` | Check extension + name pattern |
| Verify file is real Excel | Read magic bytes (504b0304) | Not an HTML error page |
| Verify Excel sheet contents | `exceljs` library | Parse and check cell values |
| Download via signed URL | `page.waitForResponse` on storage URL | Supabase-specific pattern |
| Count table rows | `locator('tr').count()` | |
| Edit table cell | Click cell → fill input → press Enter | Check edit mode triggers |

---

## Recommended for Our Project

### 1. Replace the Fixture File

The current fixture is `e2e/fixtures/sample.xlsx`. For testing the PDF extraction pipeline, we need actual PDF fixtures. Add:

```
e2e/fixtures/
  sample-financial-5pg.pdf    ← small, digital PDF for fast tests
  sample-scanned-10pg.pdf     ← scanned PDF to test OCR path
```

Use anonymized versions of real financial documents — fake/generated PDFs won't trigger the same code paths as real scanned financial statements.

### 2. Capture Document ID from Upload Response

The current `full-journey.spec.ts` does not capture the document ID from the upload API response. Without it, subsequent steps navigate by URL patterns, which is fragile. Add:

```typescript
const [uploadResponse] = await Promise.all([
  page.waitForResponse(r => r.url().includes('/api/documents') && r.request().method() === 'POST'),
  page.getByRole('button', { name: /upload/i }).click(),
]);
const { id: documentId } = await uploadResponse.json();
```

Then use `documentId` directly in `waitForDocumentStatus()` calls.

### 3. Verify the Excel File After Download

The current test only checks the filename extension. Add a ZIP header check and sheet name verification using `exceljs`. This catches the case where Excel generation silently fails and serves an error page instead.

### 4. Add `data-testid` Attributes to the Verification Table

The `ExtractionVerifier` and `LineItemEditor` components have no `data-testid` attributes. Add:
- `data-testid="line-item-row"` on each `<tr>` or row container
- `data-testid="amount-display"` on the amount display span
- `data-testid="verify-all-btn"` on the Verify All button

This makes table tests stable regardless of column ordering or CSS class changes.
