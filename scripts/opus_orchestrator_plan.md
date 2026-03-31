# Opus Orchestrator Plan — CMA E2E Testing

**You are the evaluator.** Sonnet is executing tests in a separate terminal.
Your job: monitor, evaluate, intervene when needed. Stay lean — don't fill context.

---

## 1. Setup (First Things First)

### Connect to Sonnet
```
list_peers
```
You should see the Sonnet session. Note its peer ID.

### Send Initial Greeting
```
send_message <sonnet-peer-id> "Opus online. Proceed with sonnet_execution_plan.md. Report after baseline."
```

---

## 2. Your Workflow

```
Wait for message from Sonnet
         ↓
Evaluate: Is progress good?
         ↓
   YES → send "Continue" or stay silent
   NO  → send specific guidance
         ↓
Wait for next message
```

**Do NOT proactively run tests or read large files.** That's Sonnet's job. You evaluate brief reports.

---

## 3. What to Evaluate

When Sonnet reports results, check:

### After Baseline
- How many tests are failing? (expect ~14)
- What categories? (asyncio? assertions? real bugs?)
- Is Docker healthy?

### During AutoResearch
- Is the metric trending up?
- Are reverts happening too often? (>50% = bad signal)
- Is Sonnet stuck on one issue for 3+ iterations?

### After Phase 1
- All 531 tests green?
- Were any fixes hacky? (e.g., skipping tests, weakening assertions)
- Check `git log --oneline -20` for clean atomic commits

### After Feature Verification
- All 14 areas verified?
- Any areas with partial coverage?

---

## 4. When to Intervene

Send a message to Sonnet if:

| Situation | Message to Send |
|-----------|-----------------|
| Stuck 3+ iterations | "REDIRECT: Skip [issue]. Focus on [alternative]." |
| Hacky fix detected | "REJECT: Iteration N was hacky. Revert and try: [approach]." |
| Wrong priority | "PRIORITY: Fix [X] before [Y] because [reason]." |
| Phase complete | "NEXT: Move to Phase 2 (feature verification)." |
| Accuracy needed | "ACCURACY: Run accuracy eval with SKIP_AI_CLASSIFICATION=true." |
| Done | "COMPLETE: All criteria met. Stop and commit final state." |

---

## 5. Accuracy Evaluation (If Time Permits)

After all tests pass, you may ask Sonnet to run accuracy:
```
send_message <sonnet-peer-id> "Run accuracy benchmark: 
docker compose exec -T backend python run_accuracy_test.py 2>&1 | tail -20
Report: total items, correct, accuracy %"
```

Expected: ≥80% with golden rules v2 + routing fixes (up from ~74% pre-fix).

---

## 6. Final Sign-Off Checklist

Before declaring done:
- [ ] `531/531` tests passing (confirmed by Sonnet)
- [ ] `14/14` feature areas verified
- [ ] Docker stack healthy
- [ ] `autoresearch-results.tsv` exists and shows improvement
- [ ] No hacky fixes (skipped tests, weakened assertions)
- [ ] Git log is clean atomic commits
- [ ] No API cost overruns

---

## 7. Context Budget

**YOUR CONTEXT LIMIT: 50% MAX.**

To stay lean:
- Don't read large files (test output, source code)
- Don't run tests yourself — Sonnet does that
- Keep messages to Sonnet under 3 sentences
- Use `check_messages` only when expecting a report
- Don't duplicate Sonnet's work

---

## 8. After Testing is Complete

1. Save final results to memory
2. Tell user: "Backend E2E testing complete. X/531 tests passing. Ready for UAT."
3. Suggest next step: frontend redesign (deferred from earlier)
