# AI-Agent Browser Testing: Tools, Approaches, and Our Recommendation

*Research date: 2026-03-20 | Applies to: CMA Automation System*

---

## What Is AI-Agent Browser Testing?

Traditional Playwright tests are **scripted**: every action is hardcoded — which selector to click, what text to type, where to navigate. When the UI changes, tests break and must be manually updated.

AI-agent browser testing replaces (or augments) hardcoded scripts with an LLM that **reads the page** (screenshots, ARIA snapshots, DOM) and **decides what to do next** based on a natural-language goal. The result is tests that are more resilient to UI changes, can explore unfamiliar flows, and can report what they observe in human-readable form.

For our use case — having Claude test the CMA workflow end-to-end — this is the right mental model: **Claude operates the browser like a user would**, rather than running a scripted checklist.

---

## Tool 1: Playwright MCP (Built Into Our Stack)

**What it is:** Playwright now ships with a built-in MCP (Model Context Protocol) server. When Claude connects to it via the MCP protocol, Claude can directly call browser tools: `browser_navigate`, `browser_click`, `browser_fill_form`, `browser_take_screenshot`, `browser_snapshot` (ARIA tree), `browser_wait_for`, and more.

**This is already available in our project.** The `e2e/node_modules/playwright` package we have installed includes the MCP server at `playwright/lib/mcp/`.

### How to Start the Playwright MCP Server

```bash
# From the e2e/ directory
npx playwright run-server --port 3003

# OR using the MCP CLI entry point
node e2e/node_modules/playwright/cli.js mcp --port 3003
```

Then in a Claude conversation with the Playwright MCP tool connected, you can instruct Claude:

> "Navigate to http://localhost:3002/login, log in as admin@test.local with password testpassword, then upload the file at e2e/fixtures/sample.xlsx through the upload UI, and report every status message you see."

Claude will use `browser_navigate`, `browser_fill_form`, `browser_click`, `browser_file_upload`, and `browser_snapshot` to execute this, and will describe what it sees at each step.

### Key Playwright MCP Tools Available

| Tool | What it does |
|------|--------------|
| `browser_navigate` | Go to a URL |
| `browser_snapshot` | Get the ARIA accessibility tree (better than screenshots for decision-making) |
| `browser_take_screenshot` | Capture what the page looks like |
| `browser_click` | Click an element by description or selector |
| `browser_fill_form` | Fill form fields |
| `browser_file_upload` | Upload a file through a file input |
| `browser_wait_for` | Wait for a text/selector to appear |
| `browser_select_option` | Choose from a dropdown |
| `browser_evaluate` | Run JavaScript on the page |
| `browser_network_requests` | Inspect what API calls are being made |

Source: [Playwright MCP GitHub](https://github.com/microsoft/playwright-mcp) — built into Playwright >= 1.50

---

## Tool 2: Stagehand (Browserbase)

**What it is:** Stagehand is an open-source TypeScript SDK from Browserbase that wraps Playwright with three AI-powered primitives:

- `act("description of what to do")` — Claude/GPT decides how to interact
- `extract("what data to pull out")` — extracts structured data from the page
- `observe("what might be interactable")` — returns possible actions on the page

**GitHub:** https://github.com/browserbase/stagehand (12,000+ stars as of early 2026)

### Code Example

```typescript
import { Stagehand } from '@browserbasehq/stagehand';
import { z } from 'zod';

const stagehand = new Stagehand({
  env: 'LOCAL',      // use local browser, not Browserbase cloud
  modelName: 'claude-opus-4-5',
  modelClientOptions: { apiKey: process.env.ANTHROPIC_API_KEY },
});

await stagehand.init();
const page = stagehand.page;

// Navigate
await page.goto('http://localhost:3002/login');

// AI decides how to log in based on page content
await stagehand.act('Fill in the email field with admin@test.local and the password field with testpassword, then click the sign-in button');

// Wait for navigation
await page.waitForURL('**/dashboard');

// Extract structured data from the page
const dashboardData = await stagehand.extract({
  instruction: 'Find all client names listed on the dashboard',
  schema: z.object({
    clients: z.array(z.string()),
  }),
});

console.log(dashboardData.clients); // ['Dynamic Air Engineering', ...]
```

**Why Stagehand works well for our app:**
- `act()` is resilient to UI changes — it reads the current page state rather than using hardcoded selectors
- `extract()` is perfect for reading the verification table (variable number of rows, dynamic content)
- Works with our existing Playwright install

**Cost consideration:** Each `act()` call makes 1–3 LLM API calls. For a 13-step workflow, expect 20–40 API calls. At Claude Opus 4.5 pricing (~$15/MTok input), a full test run costs roughly $0.15–$0.40. Use Haiku for cost sensitivity.

Source: [Stagehand docs](https://docs.stagehand.dev) | [GitHub](https://github.com/browserbase/stagehand)

---

## Tool 3: Browser Use

**What it is:** Browser Use is a Python library (different ecosystem from our TypeScript frontend, but callable from Python scripts) that gives an LLM full browser control with memory, multi-tab support, and a task-oriented interface.

**GitHub:** https://github.com/browser-use/browser-use (20,000+ stars as of early 2026)

```python
import asyncio
from browser_use import Agent
from langchain_anthropic import ChatAnthropic

async def test_cma_workflow():
    agent = Agent(
        task="""
        Go to http://localhost:3002 and complete the following:
        1. Log in with email admin@test.local and password testpassword
        2. Create a new client called "Test Company 123" in the Manufacturing industry
        3. Upload the file at /path/to/sample.pdf on the upload page
        4. Wait for the upload to complete and report the status message shown
        5. Report any errors you encounter
        """,
        llm=ChatAnthropic(model="claude-haiku-3-5"),  # Use Haiku for cost
    )
    result = await agent.run()
    print(result)

asyncio.run(test_cma_workflow())
```

**Strengths:**
- Pure goal-oriented: you describe the task in plain English
- Handles multi-step flows naturally — the agent plans its own sequence
- Can handle unexpected UI states (error messages, popups) without breaking

**Weaknesses for our use case:**
- Python ecosystem — separate from our TypeScript/Playwright test stack
- Less control over exact assertions ("verify that X happened") vs goal completion
- Adding LangChain dependency (which the architecture review recommends against)

---

## Tool 4: Claude Code + Playwright MCP (The "Agent Tests the App" Pattern)

This is the approach where **Claude Code itself** (running in a conversation) uses the Playwright MCP tools to navigate our app, observe what happens, and report findings. This is different from automated CI tests — it's more like a **QA session**.

### How to Run This Pattern

1. Start the Docker dev stack: `docker compose up`
2. Start the Playwright MCP server (or use the one built into Claude Code's environment)
3. In a Claude Code session, give the instruction:

```
Using the browser tools available:
1. Navigate to http://localhost:3002
2. Log in as admin@test.local / testpassword
3. Create a new client "Ashutosh Test Co" in Manufacturing
4. Upload e2e/fixtures/sample.xlsx on the upload page
5. Navigate to the newly created CMA report
6. Trigger extraction and wait for completion (poll every 30 seconds, up to 15 minutes)
7. Screenshot the verification table and describe what you see
8. Click "Verify All"
9. Trigger classification
10. When classification completes, screenshot the review page
11. Report: what worked, what broke, any UI errors observed
```

Claude will use `browser_navigate`, `browser_click`, `browser_wait_for`, `browser_take_screenshot`, and `browser_snapshot` to execute each step, and will produce a narrative report of what it observed.

**This is essentially free testing** — Claude reads and describes what it sees, catches bugs visually, and doesn't require maintaining test code.

---

## Scripted Playwright vs AI-Agent Testing: When to Use Each

| Dimension | Scripted Playwright | AI-Agent (Stagehand / MCP) |
|-----------|--------------------|-----------------------------|
| Setup time | High (write selectors, assertions) | Low (describe in plain English) |
| Maintenance | High (breaks when UI text changes) | Low (adapts to UI changes) |
| Determinism | High (same steps every run) | Medium (LLM may take slightly different paths) |
| Cost per run | Near-zero (no API calls) | $0.05–$0.50 per run (LLM calls) |
| CI/CD suitability | Excellent | Good (with consistent model) |
| Error detection precision | High (exact assertions) | Medium (narrative description) |
| Good for long-running jobs | Needs custom polling helpers | Handles naturally via wait instructions |
| Good for table inspection | Tedious (row-by-row locators) | Excellent (`extract()` or screenshot + describe) |
| Good for first-time flow validation | Slow to set up | Excellent — just describe the flow |

**Rule of thumb:**
- Use **scripted Playwright** for regression tests that run in CI on every commit
- Use **AI-agent (MCP / Stagehand)** for exploratory testing, validating new features, and testing flows too complex to script quickly
- For our CMA app, **AI-agent is the right fit for the full journey test** because the workflow is long and the tables are variable

---

## How to Instruct Claude to Test a Specific Flow

When using Claude + Playwright MCP, the quality of the test depends entirely on how clearly you describe the task. Use this template:

```
## Test Goal
[One sentence describing what you're testing]

## Environment
- App URL: http://localhost:3002
- Login: admin@test.local / testpassword
- Test file: [absolute path]

## Steps to Execute
1. [step]
2. [step]
...

## What to Report After Each Step
- Current page URL
- What you see on the page (describe any status messages, tables, buttons)
- Any error messages or unexpected UI states

## Success Criteria
- [what must be true for the test to pass]

## Failure Conditions
- [what should immediately stop the test and report a failure]

## Time Limits
- If step [N] doesn't complete within [X] minutes, report a timeout and stop
```

### Example for Our Extraction Flow

```
## Test Goal
Verify that the OCR extraction pipeline works end-to-end on a small financial PDF

## Environment
- App URL: http://localhost:3002
- Login: admin@test.local / testpassword
- Test file: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2\e2e\fixtures\sample.xlsx

## Steps
1. Navigate to /login and log in
2. Create a new client "E2E Test [timestamp]" (Manufacturing)
3. Go to the client's upload page
4. Upload the test file and click Submit
5. Wait for the upload status to show "success" or "pending" (max 30 seconds)
6. Navigate to the CMA report page for this client
7. Find and click the "Extract" button if visible
8. Take a screenshot and describe what you see every 30 seconds, up to 10 minutes
9. When you see "extraction complete" or a table with line items, stop waiting
10. Screenshot the full line items table and describe: how many rows, what columns, any amounts visible
11. Click "Verify All" if the button is present
12. Report: did it work? What status did the page show?

## Failure Conditions
- Any toast notification saying "error" or "failed"
- A blank/empty table after extraction claims to be complete
- The browser shows a 500 error page
```

---

## Recommended for Our Project

### Phase 1: Use Claude + Playwright MCP for Manual Validation (Now)

Before investing time in scripted tests, use Claude Code with the Playwright MCP tools to **manually validate** the full 13-step journey. This takes minutes to set up (just start Docker + MCP) and gives a narrative report of what works and what breaks. This is especially valuable for validating the extraction and classification flows before the first real client run.

### Phase 2: Add Stagehand for Semi-Automated Journey Tests (After V1)

Install Stagehand alongside the existing Playwright setup:

```bash
cd e2e
npm install @browserbasehq/stagehand zod
```

Replace the brittle text-matching assertions in `full-journey.spec.ts` with Stagehand `act()` calls for the steps that are most likely to change (button names, status messages). Keep raw Playwright for navigation and URL assertions (those are stable).

### Phase 3: Keep Scripted Playwright for CI Regression Tests (Ongoing)

The existing `full-journey.spec.ts` is the right shape for CI. Fix the timeout (see File 04) and add `data-testid` attributes to the key UI elements. Run it nightly, not on every commit (the 30-minute classification job makes per-commit runs impractical).

### Recommended Model for AI-Agent Tests

Use `claude-haiku-3-5` for Stagehand's AI calls during test runs — it is fast, cheap (~$0.02 per full journey), and sufficient for browser navigation decisions. Reserve Opus/Sonnet for writing the test instructions themselves.
