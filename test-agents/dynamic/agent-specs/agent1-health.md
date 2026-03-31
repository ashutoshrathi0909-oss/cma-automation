# Agent 1: Infrastructure Health Check

## Your Job
Verify that the CMA Automation System is fully operational before any test documents are processed. Every check must pass before the orchestrator proceeds to Agent 2.

## Working Directory
`C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2`

## Checks to Run (in order)

### Check 1: Docker Containers
```bash
docker compose ps
```
**Expected:** All 4 containers show status "Up":
- `cmaproject-2-backend-1`
- `cmaproject-2-frontend-1`
- `cmaproject-2-redis-1`
- `cmaproject-2-worker-1`

If any container is Down: run `docker compose up -d` and wait 30 seconds, then re-check.

### Check 2: Backend Health Endpoint
```bash
curl -s http://localhost:8000/health
```
**Expected:** `{"status": "ok"}` or similar 200 response.

### Check 3: Frontend Responding
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3002
```
**Expected:** `200`

### Check 4: Redis Connectivity
```bash
docker compose exec redis redis-cli ping
```
**Expected:** `PONG`

### Check 5: Worker Startup (Phase 10 dependencies)
```bash
docker compose logs worker --tail=30
```
**Expected:** Must contain "Starting worker for 3 functions" — this confirms pdf2image and anthropic loaded without import errors.
If you see `ImportError` or `ModuleNotFoundError`: STOP and report to orchestrator.

### Check 6: pdf2image Installed in Backend
```bash
docker compose exec backend python -c "from pdf2image import convert_from_bytes; print('pdf2image: OK')"
```
**Expected:** `pdf2image: OK`

### Check 7: Anthropic Client Importable
```bash
docker compose exec backend python -c "import anthropic; c = anthropic.Anthropic(api_key='test'); print('anthropic: OK')"
```
**Expected:** `anthropic: OK` (may show API key error — that's fine, we just need the import to work)

### Check 8: Supabase / Database Connectivity
```bash
curl -s http://localhost:8000/api/clients/ -H "X-User-Id: 00000000-0000-0000-0000-000000000001" -H "X-User-Role: admin"
```
**Expected:** HTTP 200 with JSON array (may be empty if no clients yet)

### Check 9: pdfplumber for Text PDFs
```bash
docker compose exec backend python -c "import pdfplumber; print('pdfplumber: OK')"
```
**Expected:** `pdfplumber: OK`

## Output File
Write results to `test-results/dynamic/agent1-health.json`:

```json
{
  "agent": "1-health",
  "company": "Dynamic Air Engineering",
  "timestamp": "2026-03-19T...",
  "checks": {
    "docker_containers": "PASS",
    "backend_health": "PASS",
    "frontend_responding": "PASS",
    "redis_ping": "PASS",
    "worker_startup": "PASS",
    "pdf2image": "PASS",
    "anthropic": "PASS",
    "database": "PASS",
    "pdfplumber": "PASS"
  },
  "overall": "PASS",
  "notes": ""
}
```

## Gate Condition
Report back to orchestrator: `PASS` (all 9 checks green) or `FAIL` (any check failed).
If `FAIL`: include which check failed and the exact error output in the notes field.
**Orchestrator must NOT proceed to Agent 2 if this gate is FAIL.**
