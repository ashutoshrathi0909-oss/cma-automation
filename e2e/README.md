# CMA E2E Tests

## Setup

Playwright tests target the local Docker dev stack.

## Run

```bash
# Start the dev stack first
cd ..
docker compose up -d

# Install Playwright browsers (first time only)
cd e2e
npx playwright install chromium

# Run all tests
E2E_ADMIN_EMAIL=admin@test.local E2E_ADMIN_PASSWORD=yourpassword npx playwright test

# Show last test report
npx playwright show-report
```

## Test file

- `full-journey.spec.ts` — 13-step complete V1 workflow (login → Excel download → logout)

## Fixtures

- `fixtures/sample.xlsx` — upload fixture file used in step 4
