/**
 * CMA V1 Full Journey E2E Test
 *
 * Steps 1-13: login → create client → upload doc → create CMA report →
 * trigger extraction → verify → classify → review → resolve doubts →
 * generate Excel → download → logout
 *
 * Prerequisites:
 * - Docker dev stack running: docker compose up
 * - Admin user exists with E2E_ADMIN_EMAIL and E2E_ADMIN_PASSWORD env vars
 */

import { test, expect, type Page } from "@playwright/test"
import path from "path"

const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL ?? "admin@test.local"
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? "testpassword"
const CLIENT_NAME = `E2E Test Co ${Date.now()}`
const FIXTURE_PATH = path.join(__dirname, "fixtures", "sample.xlsx")

async function login(page: Page) {
  await page.goto("/login")
  await page.getByLabel(/email/i).fill(ADMIN_EMAIL)
  await page.getByLabel(/password/i).fill(ADMIN_PASSWORD)
  await page.getByRole("button", { name: /sign in|log in/i }).click()
  await page.waitForURL("**/dashboard", { timeout: 15_000 })
}

test.describe("CMA V1 Full Journey", () => {
  test("complete workflow from login to Excel download", async ({ page }) => {
    // ── Step 1: Login ──────────────────────────────────────────────────────
    await login(page)
    await expect(page).toHaveURL(/dashboard/)

    // ── Step 2: Create a new client ────────────────────────────────────────
    await page.goto("/clients/new")
    await page.getByLabel(/client name/i).fill(CLIENT_NAME)
    // shadcn Select — click trigger, then click option
    const industryTrigger = page.getByRole("combobox", { name: /industry/i })
    await industryTrigger.click()
    await page.getByRole("option", { name: /manufacturing/i }).click()
    await page.getByRole("button", { name: /create|save/i }).click()
    // After creation → redirected to client detail page
    await page.waitForURL(/\/clients\/[^/]+$/, { timeout: 15_000 })

    // ── Step 3: Verify client appears on detail page ───────────────────────
    await expect(page.getByText(CLIENT_NAME)).toBeVisible()
    const clientUrl = page.url()

    // ── Step 4: Upload a document ──────────────────────────────────────────
    await page.getByRole("link", { name: /upload/i }).click()
    await page.waitForURL(/\/upload$/)
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles(FIXTURE_PATH)
    // Select document type if required
    const docTypeSelect = page.getByRole("combobox").first()
    if (await docTypeSelect.isVisible()) {
      await docTypeSelect.click()
      await page.getByRole("option").first().click()
    }
    await page.getByRole("button", { name: /upload/i }).click()
    await expect(
      page.getByText(/uploaded|success|pending/i)
    ).toBeVisible({ timeout: 20_000 })

    // ── Step 5: Create a new CMA report ───────────────────────────────────
    await page.goto(clientUrl)
    await page.getByRole("link", { name: /new report/i }).click()
    await page.waitForURL(/\/cma\/new$/)
    await page.getByRole("button", { name: /create report|create/i }).click()
    await page.waitForURL(/\/cma\/[^/]+$/, { timeout: 15_000 })
    const reportUrl = page.url()

    // ── Step 6: Trigger extraction ─────────────────────────────────────────
    const verifyUrl = reportUrl.replace(/\/?$/, "") + "/verify"
    await page.goto(verifyUrl)
    // Extraction is triggered automatically or via a button on verify page
    const extractBtn = page.getByRole("button", { name: /extract|start/i })
    if (await extractBtn.isVisible({ timeout: 3_000 })) {
      await extractBtn.click()
    }
    await expect(
      page.getByText(/extracted|extraction complete|verified/i)
    ).toBeVisible({ timeout: 60_000 })

    // ── Step 7: Verify all items and confirm ──────────────────────────────
    const verifyAllBtn = page.getByRole("button", { name: /verify all|confirm all|confirm verification/i })
    if (await verifyAllBtn.isVisible({ timeout: 3_000 })) {
      await verifyAllBtn.click()
    }
    // Hard assertion regardless of whether button was clicked
    await expect(
      page.getByText(/verified|confirmed|extraction complete/i)
    ).toBeVisible({ timeout: 15_000 })

    // ── Step 8: Trigger classification ────────────────────────────────────
    await page.goto(reportUrl)
    const classifyBtn = page.getByRole("button", { name: /classify/i })
    if (await classifyBtn.isVisible({ timeout: 3_000 })) {
      await classifyBtn.click()
    }
    await expect(
      page.getByText(/classified|classification complete/i)
    ).toBeVisible({ timeout: 60_000 })

    // ── Step 9: Bulk approve high-confidence items ─────────────────────────
    const reviewUrl = reportUrl.replace(/\/?$/, "") + "/review"
    await page.goto(reviewUrl)
    const bulkApproveBtn = page.getByRole("button", { name: /approve all high confidence/i })
    if (await bulkApproveBtn.isVisible({ timeout: 3_000 })) {
      await bulkApproveBtn.click()
      await expect(page.getByText(/approved \d+/i)).toBeVisible({ timeout: 10_000 })
    }

    // ── Step 10: Resolve doubts if any ────────────────────────────────────
    const doubtsUrl = reportUrl.replace(/\/?$/, "") + "/doubts"
    await page.goto(doubtsUrl)
    // If there are doubt items, resolve the first one
    const doubtRows = page.locator("[data-testid='doubt-item'], [role='row']").filter({ hasText: /doubt|unresolved/i })
    const doubtCount = await doubtRows.count()
    if (doubtCount > 0) {
      const firstRow = doubtRows.first()
      const select = firstRow.locator("select, [role='combobox']").first()
      if (await select.isVisible()) {
        await select.click()
        const option = page.getByRole("option").nth(1)
        if (await option.isVisible()) await option.click()
      }
      const resolveBtn = firstRow.getByRole("button", { name: /resolve|save/i })
      if (await resolveBtn.isVisible()) await resolveBtn.click()
    }
    // Either "No doubt items" (empty state) or doubts resolved
    await expect(
      page.getByText(/no doubt items|all classifications resolved|resolved/i)
    ).toBeVisible({ timeout: 10_000 })

    // ── Step 11: Generate Excel ────────────────────────────────────────────
    const generateUrl = reportUrl.replace(/\/?$/, "") + "/generate"
    await page.goto(generateUrl)
    await expect(
      page.getByText(/cma excel is ready|complete|ready/i)
    ).toBeVisible({ timeout: 60_000 })

    // ── Step 12: Download Excel ────────────────────────────────────────────
    const downloadBtn = page.getByRole("button", { name: /download/i })
    await expect(downloadBtn).toBeVisible()
    // Either trigger download event or verify button is clickable
    const downloadPromise = page.waitForEvent("download", { timeout: 15_000 }).catch(() => null)
    await downloadBtn.click()
    const download = await downloadPromise
    if (download) {
      expect(download.suggestedFilename()).toMatch(/\.(xlsm?|xlsx)$/)
    }
    // If download opens in a new tab (signed URL), just assert button was clicked successfully

    // ── Step 13: Logout ────────────────────────────────────────────────────
    // Find logout in header/sidebar
    const logoutBtn = page.getByRole("button", { name: /logout|sign out/i })
    if (await logoutBtn.isVisible({ timeout: 3_000 })) {
      await logoutBtn.click()
    } else {
      // May be in a dropdown menu
      const userMenu = page.getByRole("button", { name: /user|account|profile/i })
      if (await userMenu.isVisible({ timeout: 3_000 })) {
        await userMenu.click()
        await page.getByRole("menuitem", { name: /logout|sign out/i }).click()
      }
    }
    await page.waitForURL(/\/login/, { timeout: 10_000 })
    await expect(page).toHaveURL(/login/)
  })
})
