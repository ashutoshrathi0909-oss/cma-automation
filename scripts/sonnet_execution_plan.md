# Sonnet Execution Plan — CMA E2E Testing

**You are the execution agent.** Opus is the evaluator in a separate terminal.
Read this entire document before starting. Follow it step by step.

---

## 1. Project Context (Brief)

CMA Automation System — automates Credit Monitoring Arrangement document preparation for Indian CA firms.
- **Backend:** Python FastAPI + Supabase + ARQ (Redis task queue)
- **Frontend:** Next.js 16 (skip — not testing frontend this round)
- **Docker:** 4 services (backend, frontend, worker, redis)
- **Tests:** 531 pytest tests across 29 files in `backend/tests/`
- **Known issues:** ~14 test failures (asyncio fixtures, assertion mismatches)

---

## 2. Your Mission

**Get all backend tests passing and verify every feature works.**

You have 3 tools:
1. **AutoResearch** (`/autoresearch`) — autonomous fix loop
2. **Claude Peers** — communicate with Opus via `send_message` / `check_messages`
3. **Standard Claude Code tools** — read, edit, bash, etc.

---

## 3. Step-by-Step Execution

### Step 0: Git Clean State

Before anything, ensure git is clean:
```bash
git stash  # or commit current changes
```

If there are untracked files that shouldn't be committed, stash or gitignore them.

### Step 1: Start Docker

```bash
docker compose up -d
```

Wait for all services:
```bash
# Check health
curl -sf http://localhost:8000/health
docker compose exec -T backend python -c "print('backend ok')"
docker compose exec -T redis redis-cli PING
```

### Step 2: Establish Baseline

Run the eval script:
```bash
bash scripts/e2e_eval.sh
```

This outputs a single number (passing test count). Record it.

Also run pytest with details to see what's failing:
```bash
docker compose exec -T backend pytest --tb=short -q 2>&1 | tail -30
```

### Step 3: Connect to Opus via Claude Peers

Call `list_peers` to see if Opus is connected. If yes, send baseline:
```
send_message to <opus-peer-id>: "BASELINE: X/531 tests passing. Top failures: [list]"
```

If Opus is not connected yet, proceed anyway — AutoResearch is autonomous.

### Step 4: Run AutoResearch — Phase 1 (Fix Test Infrastructure)

Run `/autoresearch` with this configuration:

```
Goal: Fix all failing backend pytest tests — currently X/531 passing, target 531/531
Scope: backend/tests/**/*.py, backend/app/**/*.py
Metric: Number of passing pytest tests
Direction: up
Verify: bash scripts/e2e_eval.sh
Guard: bash scripts/e2e_guard.sh
Iterations: 20
```

**Priority order for fixes:**
1. `pytest-asyncio` mode configuration (add `asyncio_mode = "auto"` to conftest or pyproject.toml)
2. Import errors or missing fixtures
3. Assertion mismatches (`ai_openrouter` vs `ai_haiku` classification method strings)
4. Mock/fixture staleness (tests referencing old function signatures)
5. Actual app bugs revealed by tests

**Rules:**
- ONE fix per iteration
- Commit BEFORE verify
- If metric drops → auto-revert
- Never skip the guard (health check must pass)

### Step 5: Report Results to Opus

After AutoResearch completes (or hits 20 iterations), report via Claude Peers:

```
send_message to <opus-peer-id>: "PHASE 1 COMPLETE: X/531 passing. Fixed: [list of fixes]. Remaining failures: [list]"
```

### Step 6: Feature Verification Checklist

After tests pass, verify each feature area manually. Run these checks:

#### Auth (4 tests)
```bash
docker compose exec -T backend pytest tests/test_auth.py -v --tb=short
```

#### Clients (4 tests)
```bash
docker compose exec -T backend pytest tests/test_clients.py -v --tb=short
```

#### Documents (4 tests)
```bash
docker compose exec -T backend pytest tests/test_documents.py -v --tb=short
```

#### Extraction Pipeline (3 tests)
```bash
docker compose exec -T backend pytest tests/test_extraction.py tests/test_extraction_api.py -v --tb=short
```

#### Classification Pipeline — THE CORE (4 tests)
```bash
docker compose exec -T backend pytest tests/test_classification_pipeline.py tests/test_classification_api.py -v --tb=short
```

#### Fuzzy Matcher (2 tests)
```bash
docker compose exec -T backend pytest tests/test_fuzzy_matcher.py -v --tb=short
```

#### AI Classifier (2 tests)
```bash
docker compose exec -T backend pytest tests/test_ai_classifier.py -v --tb=short
```

#### Learning System (2 tests)
```bash
docker compose exec -T backend pytest tests/test_learning_system.py -v --tb=short
```

#### Excel Generation (3 tests)
```bash
docker compose exec -T backend pytest tests/test_excel_generator.py tests/test_excel_tasks.py tests/test_e2e_excel_generation.py -v --tb=short
```

#### Conversion (Provisional → Audited) (3 tests)
```bash
docker compose exec -T backend pytest tests/test_conversion_service.py tests/test_conversion_upgrade.py -v --tb=short
```

#### Roll Forward (2 tests)
```bash
docker compose exec -T backend pytest tests/test_roll_forward.py tests/test_roll_forward_api.py -v --tb=short
```

#### Redaction & Page Management (3 tests)
```bash
docker compose exec -T backend pytest tests/test_redaction.py tests/test_redaction_api.py tests/test_page_manager.py tests/test_page_filter.py tests/test_page_filter_api.py -v --tb=short
```

#### Audit Trail (1 test)
```bash
docker compose exec -T backend pytest tests/test_audit_service.py -v --tb=short
```

#### Error Handling (1 test)
```bash
docker compose exec -T backend pytest tests/test_error_handling.py -v --tb=short
```

#### Users & Roles (1 test)
```bash
docker compose exec -T backend pytest tests/test_users_router.py -v --tb=short
```

### Step 7: API Smoke Test (Live Docker Stack)

Test key endpoints against the running backend:

```bash
# Health check
curl -sf http://localhost:8000/health | python -m json.tool

# Auth endpoint exists
curl -sf -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test"}' \
  -w "\nHTTP_CODE: %{http_code}\n" 2>&1 | tail -3

# Clients endpoint (with DISABLE_AUTH=true)
curl -sf http://localhost:8000/api/clients/ \
  -H "Authorization: Bearer dev-token" \
  -w "\nHTTP_CODE: %{http_code}\n" 2>&1 | tail -3
```

### Step 8: Final Report to Opus

```
send_message to <opus-peer-id>: "FINAL REPORT:
- Unit tests: X/531 passing
- Feature areas: X/14 verified
- API health: OK/FAIL
- AutoResearch iterations: X (Y kept, Z reverted)
- Remaining issues: [list or 'none']
- Git log of changes: [brief summary]"
```

---

## 4. AutoResearch Configuration Reference

```yaml
Goal: "Get all 531 backend pytest tests passing for the CMA automation system"
Scope: "backend/**/*.py"
Metric: "Number of passing pytest tests (0-531)"
Direction: "up"
Verify: "bash scripts/e2e_eval.sh"
Guard: "bash scripts/e2e_guard.sh"
Iterations: 20
```

---

## 5. Key Files You'll Need

| File | Purpose |
|------|---------|
| `backend/tests/conftest.py` | Test fixtures (client, admin_client, employee_client) |
| `backend/app/main.py` | FastAPI app entry point |
| `backend/app/config.py` | Settings (Supabase, AI providers) |
| `backend/app/dependencies.py` | Auth, Supabase clients |
| `backend/app/services/classification/pipeline.py` | Classification orchestrator |
| `backend/app/services/classification/rule_engine.py` | Tier 0a + 0b rules |
| `backend/app/services/classification/fuzzy_matcher.py` | Tier 1 fuzzy matching |
| `backend/app/services/classification/scoped_classifier.py` | Tier 2 AI |
| `backend/app/services/excel_generator.py` | CMA Excel generation |
| `backend/app/services/conversion_service.py` | Provisional → Audited diff |
| `scripts/e2e_eval.sh` | AutoResearch verify command |
| `scripts/e2e_guard.sh` | AutoResearch guard command |
| `docker-compose.yml` | Docker service definitions |

---

## 6. Common Failure Patterns & Fixes

### asyncio fixture errors
**Symptom:** `ScopedEventLoopPolicy` or `RuntimeError: no running event loop`
**Fix:** Add to `backend/tests/conftest.py` or create `backend/pyproject.toml`:
```python
# conftest.py
import pytest
pytest_plugins = ['pytest_asyncio']

# Or pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### ai_openrouter vs ai_haiku assertion
**Symptom:** `AssertionError: 'ai_openrouter' != 'ai_haiku'`
**Fix:** Update test assertions to match current `classification_method` values. The scoped classifier uses `"ai_openrouter"` when using OpenRouter provider.

### Mock signature mismatch
**Symptom:** `TypeError: unexpected keyword argument`
**Fix:** Check if the function signature changed. Update the mock to match current parameters.

### Import errors
**Symptom:** `ModuleNotFoundError` or `ImportError`
**Fix:** Check if the module was renamed or moved. Update imports.

---

## 7. Communication Protocol

Use Claude Peers MCP tools:
- `list_peers` — discover Opus session
- `send_message(peer_id, message)` — send status to Opus
- `check_messages` — check for instructions from Opus

**Message format (keep brief — saves context):**
```
STATUS: [phase] [metric] [brief details]
```

Examples:
```
STATUS: BASELINE 517/531 passing. 14 failures in 5 files.
STATUS: ITER-5 525/531 passing. Fixed asyncio mode + 3 assertion mismatches.
STATUS: PHASE1-DONE 531/531 all green.
STATUS: FEATURES 14/14 verified. Ready for accuracy benchmark.
```

**If Opus sends you a message, follow its instructions.** Opus may redirect your focus or ask you to skip a phase.

---

## 8. Safety Rules

1. **Max 20 AutoResearch iterations** — hard cap, no exceptions
2. **Never call AI APIs in tests** — use `SKIP_AI_CLASSIFICATION=true` or mocks
3. **Never modify .env or secrets** — test infrastructure only
4. **Commit before verify** — AutoResearch does this automatically
5. **Don't touch frontend/** — out of scope for this round
6. **Don't add new features** — fix and verify only
7. **If stuck for 3 iterations on same issue** — send message to Opus for guidance

---

## 9. Success Criteria

- [ ] 531/531 pytest tests passing
- [ ] All 14 feature areas verified (Step 6 checklist)
- [ ] Backend health endpoint returns `{"status": "ok"}`
- [ ] Docker stack stable (no crashed containers)
- [ ] Clean git history (each fix is one atomic commit)
- [ ] `autoresearch-results.tsv` shows improvement trajectory
