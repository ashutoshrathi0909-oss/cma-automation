# Research Review & Recommendations
*Reviewed by: Technical Architect Agent | Date: 2026-03-20*

---

## TL;DR — The 5 Things That Actually Matter

1. **Fix the retry loop NOW** — replace the hardcoded `[5, 15, 30]` sleep array with `tenacity` + SDK `max_retries=4`. This is a two-hour code change that eliminates the $4.99 burn problem forever.

2. **Add checkpoint-based resumption to `pipeline.py`** — fetch already-classified item IDs before the loop and skip them. Without this, any timeout or crash restarts from zero and burns money again.

3. **Switch OCR model from `claude-sonnet-4-6` to `claude-haiku-3-5` immediately** — this is a one-line code change in `ocr_extractor.py` that saves 73% on OCR cost with zero integration work. Do this before the 7-company test run. Everything else in the OCR alternatives research is interesting but premature.

4. **Set the $25 hard cap in the Anthropic Console TODAY** — before running anything. This is a 30-second configuration action that prevents catastrophic runaway cost from any bug you haven't found yet.

5. **Do NOT build the hybrid pipeline before you have quality benchmarks on your own documents** — the 92% cost reduction claim in the research sounds amazing but is built on assumptions. Validate Haiku quality on Dynamic Air Engineering first. Then decide if further optimization is needed.

---

## Section 1: Rate Limiting & Retry Fixes

### The Problem Diagnosis

The research correctly identifies what went wrong: a manual retry loop with `[5, 15, 30]` sleep delays that are too short, have no jitter, ignore the `retry-after` header, and provide no global backpressure across sequential items. Burning $4.99 in one run due to a restart loop caused by timeout + delete-then-reinsert idempotency failure is a real and well-documented failure mode.

### Option 1: `tenacity` library — APPROVE

This is the right answer and the research explains it well. `tenacity` is mature, widely used, and the Anthropic cookbook itself uses it. The `wait_random_exponential` strategy with jitter is correct for rate-limited APIs. The 8-attempt, max-90-second configuration is appropriate.

**One correction to the research:** The research shows `_call_api_with_retry = retry(...)(_call_api)` as a class-level attribute wrapping an instance method. This pattern has a subtle Python bug — `self` won't be passed correctly when tenacity wraps an unbound method at class definition time. The cleaner pattern is to decorate at the method level or wrap in `__init__`. This is fixable but the developer should be aware the code sample needs adjustment before copy-pasting.

**Implementability:** High. One pip install, straightforward decorator pattern. AI assistance can implement this correctly.

**Verdict: APPROVE** — implement immediately.

### Option 2: SDK `max_retries=4` as base layer

Also correct. The combination of SDK retries (handles connection errors and transient failures) plus tenacity (handles sustained rate limit pressure) is the right layered approach. The research is accurate that SDK retry alone is insufficient for a 2971-item sequential pipeline.

**Verdict: APPROVE** — implement alongside tenacity, not instead of it.

### Option 3: Manual retry (current) — ROAST

The research correctly roasts this. Nothing to add. Replace it.

**Verdict: ROAST** — it's broken, it cost money, delete it.

### Option 4: Token-bucket proactive throttling

This is the most robust long-term approach — proactively staying under the rate limit is always better than reacting to 429s. The `limits` library suggestion is fine. However, this adds a dependency and some complexity.

**The research's recommendation of `time.sleep(1.2)` between items** is the practical version of this — simple, no extra library, and keeps throughput at 50 items/minute with headroom. This is the right call for this project's complexity budget.

**Verdict: CONDITIONAL** — implement the simple `time.sleep(1.2)` inter-item throttle now. The full token-bucket pattern is optional and can wait.

### What the retry research missed

The research does not address what happens when the pipeline gets a `429` but tenacity eventually succeeds after 5 minutes of backoff — does the current pipeline's ARQ job timeout (3600s) give it enough runway? At 8 attempts with max 90s waits, the worst case is ~8 minutes of retry delay for one item. With 1485 AI items, if 10% of them hit rate limits and each burns 5 minutes of retry, that's 1.5 hours of extra runtime. The 60-minute job timeout could still be exceeded. This is a gap in the analysis.

---

## Section 2: Idempotency & Job Management

### Pattern A: Delete-then-reinsert (current)

The research correctly identifies this as "correct but vulnerable." The vulnerability during timeout restarts is real and is exactly what caused the restart loop. Good diagnosis.

### Pattern B: Upsert with UNIQUE constraint — APPROVE

This is the correct database-level fix and should be implemented. The SQL migration is simple, the Supabase Python client supports upsert natively. The research recommendation to add `UNIQUE (line_item_id)` and switch to `.upsert()` is sound.

**One concern:** The research presents this as straightforward, but the migration needs to handle any existing duplicate rows before the constraint can be added. The SQL should include a `DELETE ... USING` dedup step first. The research skips this, which could cause the migration to fail on a database that already has duplicate data from prior failed runs.

**Verdict: APPROVE** — but add a dedup step before the constraint.

### Pattern C: Checkpoint-based resumption — APPROVE

This is the most important fix for cost protection. The implementation is clean: fetch already-classified IDs, skip them. This is a 15-line change to `pipeline.py` with massive impact — failed jobs restart from where they stopped, not from scratch.

The combination of checkpoint (Pattern C) + upsert (Pattern B) is the correct final state. Pattern C makes restarts cheap. Pattern B makes accidental duplicates impossible.

**Verdict: APPROVE** — this is Priority 1 after the retry fix.

### Pattern D: Deterministic ARQ job IDs

Useful and the implementation is correct. Setting `_job_id=f"classify:{document_id}"` prevents the API endpoint from double-enqueuing if called twice. Low complexity, high safety value.

**Verdict: APPROVE** — add this when implementing the retry/checkpoint work.

### Supabase connection management

The analysis of the HTTP/2 singleton problem is accurate. The fix (`max_jobs=1`, already implemented) is correct. The per-job client creation (Fix B) is the right approach if concurrency is ever increased.

**Fix C (PgBouncer) is irrelevant** — the project uses the REST API via the Python client, not direct PostgreSQL connections. The research correctly notes this but should have said it more forcefully: PgBouncer does nothing for this project.

**Fix D (disable HTTP/2)** — the research calls this "not recommended" and is right. Don't do it. `max_jobs=1` is the correct fix.

**Verdict: APPROVE** the existing `max_jobs=1` fix. The per-job client pattern is worth adding as defensive code.

---

## Section 3: Budget Guardrails

### Pre-run cost estimation via `count_tokens` API — APPROVE

This is a genuinely good idea and the implementation is practical. Sampling 5 items to estimate average token count is the right approach (counting all 2971 items would be slow). The Anthropic `count_tokens` endpoint is free to call and well-documented.

**One caveat the research misses:** The 50% fuzzy pass rate assumption is itself uncertain. If the fuzzy matcher is poorly calibrated, 80% of items go to AI and the estimate is off by 2x. The estimate should include a confidence note: "This assumes ~50% fuzzy pass rate. If fuzzy matching is not yet trained, actual cost may be up to 2x this estimate."

**Verdict: APPROVE** — implement before classification starts.

### Per-run budget cap — APPROVE

The `MAX_CLASSIFICATION_COST_USD` environment variable + abort logic is the right pattern. Simple, configurable, safe. The live cost tracking via `response.usage` is also the correct approach.

**The research correctly identifies** that the $4.99 burn was not from one clean run ($2.79 estimate) but from repeated re-runs due to the restart loop. Once checkpoint resumption and proper retry are in place, the cost per run becomes predictable. Budget caps are defense-in-depth for when predictions are wrong.

**Verdict: APPROVE** — implement alongside the retry and checkpoint fixes.

### Structured logging for cost visibility — APPROVE

The `PipelineLogger` pattern logging `method=fuzzy_match` vs `method=ai_haiku` per item is excellent operational visibility. It requires zero extra dependencies (Python's built-in `logging` module) and gives full pipeline observability via `docker compose logs -f backend`.

**The `time.sleep(1.2)` inter-item throttle makes this even more valuable** — the ETA calculation becomes accurate when processing time per item is predictable.

**Verdict: APPROVE** — implement this.

### Helicone (external monitoring) — CONDITIONAL

The research correctly says "post-V1." For 7 test companies with a $25 budget, a hosted dashboard is overkill. For production with multiple clients per day, it becomes relevant. One `base_url` change is genuinely low friction.

**Verdict: CONDITIONAL** — skip for V1. Revisit when processing 5+ companies per week.

### LangSmith — ROAST

The research says "skip for V1" and is correct, but understates why. LangSmith requires wrapping calls in LangChain primitives or manually building trace objects. For a project using the Anthropic SDK directly, this means rewriting the client integration. The overhead is not just "heavyweight" — it's architecturally invasive. Skip permanently unless the project migrates to LangChain, which it should not.

**Verdict: ROAST** — do not add to this project.

### What budget guardrails research missed

There is no recommendation to track cumulative spend across multiple companies during the 7-company test run. If Company 1 costs $0.56 and Company 7 costs $1.85, the researcher tracks per-run costs but not the running total against the $16 budget. The daily Redis counter pattern in Part 5 addresses this, but it's buried and not connected to the per-run budget cap logic. These two mechanisms need to talk to each other.

---

## Section 4: Agent Orchestration Architecture

### Pattern 1: JSON state file + sequential runner — APPROVE

This is the correct tool for this scale. A JSON file that persists state between sessions, skips completed companies, and logs structured output is all that's needed. No Airflow, no Dagster, no Prefect. The research gets this exactly right.

The research's own comparison table says it clearly: "JSON state file + Python script | Zero | 7 companies, our current scale." Trust this verdict.

**One practical issue:** `run_all_extractions.py` already exists at the project root. The research recommends enhancing it. Before building the state file pattern into a new script, someone should read what `run_all_extractions.py` already does. The research does not do this — it designs from scratch without auditing the existing file.

**Verdict: APPROVE** the pattern. Read the existing file before writing new code.

### Pattern 2: Process Manager (Enterprise Integration Patterns) — ROAST

Referencing the Enterprise Integration Patterns book for a 7-company test runner is academic overkill. The concept (track per-step status) is correct and IS what the state file already implements. But invoking EIP as a pattern source adds zero practical value. This is research padding.

**Verdict: ROAST** as a recommendation. The idea is fine, the framing is unnecessary.

### Pattern 3: ARQ auto-chaining — CONDITIONAL

The research correctly flags that auto-chaining **must not bypass the human verification gate** and should only be used in test harnesses. But then it proposes `if ctx.get("auto_chain"):` as a context flag — meaning the same worker code paths would be used for test-bypass runs. This is dangerous: a test configuration flag accidentally passed to production would skip the mandatory verification step.

**Better approach:** A completely separate test-only script that calls the API endpoints in sequence, not an in-worker flag. The production ARQ tasks should have no awareness of "auto_chain" mode.

**Verdict: CONDITIONAL** — the concept is valid for testing, but the implementation pattern is risky for a compliance system. Use a test-only external script, not an in-worker bypass flag.

### Pre-flight checks — APPROVE

The 6-check pre-flight pattern (Redis ping, ARQ worker alive, queue empty, Supabase reachable, company in DB, API key present) is exactly right. Catching "ARQ worker not started" before a 45-minute job begins is a real operational win.

The implementation is clean Python async code. Implementable with AI assistance in under an hour.

**Verdict: APPROVE** — implement this.

### ARQ job polling with `wait_for_job()` — APPROVE

The `Job(job_id, redis_pool)` polling pattern is the correct way to wait for ARQ jobs from an external script. The timeout and poll interval parameters make it configurable. This is native to the ARQ library, not a custom hack.

**Verdict: APPROVE** — implement in the runner script.

### Redis Pub/Sub progress tracking — ROAST for now

Publishing real-time progress events per item via Redis pub/sub is architecturally correct but adds meaningful complexity. For a test runner that runs unattended and logs to Docker logs, `docker compose logs -f backend` gives the same information. Pub/Sub is only valuable if you're building a live progress UI.

**Verdict: ROAST** for V1 test runner. Reconsider for the production frontend progress bar.

### What orchestration research missed

The verification gate is treated as a blocking human step, but the research does not describe how to detect when verification is complete programmatically. The "Option B: poll Supabase for `verified` status" is briefly mentioned but not implemented. For a multi-company test run where verification happens asynchronously over 1-2 days, the runner needs to know which companies are ready for classification without manual tracking. The Supabase polling pattern should have been fleshed out more.

---

## Section 5: Cost Estimates

### The base estimate: $8.01 for 7 companies

The methodology is sound. The per-page formula is correct:
- Sonnet input: 2,600 tokens × $3/MTok = $0.0078
- Sonnet output: 400 tokens × $15/MTok = $0.006
- Total: $0.0138/page

For 435 pages: $6.01 in OCR. This checks out.

For classification at 60% AI rate, 800 input + 150 output tokens at Haiku pricing ($1/$5):
- Per item: (800 × $1/MTok) + (150 × $5/MTok) = $0.0008 + $0.00075 = $0.00155
- 2,150 items × 60% × $0.00155 = $2.00

**The $8.01 base estimate is credible.**

### The $25 hard cap recommendation

The recommended $16 test budget and $25 hard cap are both reasonable. The 2x multiplier for first-time pipeline runs is standard and correct. Expect re-runs.

### Haiku pricing discrepancy

The pricing table in `03-cost-estimation-7-companies.md` states Claude Haiku 4.5 at **$1.00/$5.00 per MTok** (input/output). The retry research in `03-budget-guardrails-and-monitoring.md` states Haiku 4.5 at **$0.80/$4.00 per MTok**. These are inconsistent. The classification cost estimate ($2.01) uses the $1/$5 pricing.

**The $0.80/$4.00 figure appears more accurate based on known Haiku pricing tiers.** If correct, the actual classification cost is ~20% lower than estimated: ~$1.61 instead of $2.01. Total 7-company cost is closer to $7.61 base. This is a minor difference and doesn't change the $25 cap recommendation.

**Either way, verify current Haiku 4.5 pricing at the Anthropic console before the test run.**

### The ₹2.30/page comment in `ocr_extractor.py`

The research correctly calls this out: at March 2026 pricing (₹83.5/$), the actual OCR cost is ~₹1.05/page, not ₹2.30. The code comment is stale. Update it after the switch to Haiku (₹0.23/page) to keep future cost estimates accurate.

### Prompt caching claim: "70% input savings on classification"

The research claims the CMA field list is 1,500 of 800 total input tokens. This is mathematically impossible — you can't cache 1,500 tokens out of an 800-token prompt. The numbers are inconsistent. Either the average prompt is ~2,200 tokens (1,500 field list + 700 item text) or the cached portion is smaller. The cost saving claim needs to be recalculated with consistent numbers.

**This does not invalidate prompt caching as a strategy** — it's a legitimate Anthropic feature — but the specific saving estimate ($0.72) is unreliable.

### Batch API 50% discount claim

This is real and well-documented. Classification is a good candidate since results don't need to be real-time. The trade-off is that Batch API results take minutes to hours, not seconds. For a background ARQ job that already takes 30+ minutes, this is acceptable. The $4.01 vs $8.01 cost comparison is accurate.

**However:** Batch API requires significant code changes — you can't just add a flag. You need to submit all items as a batch, poll for completion, and download results. This is a meaningful architectural change. The research presents it as simple. It is not.

**Verdict:** Worth pursuing post-V1 if classification cost is still a concern. Not for the first test run.

---

## Section 6: OCR Alternatives — The Big Decision

This is the most consequential set of recommendations. Read carefully.

### The 92% cost reduction claim — examine it carefully

The hybrid pipeline (Surya → Gemini → Haiku → Sonnet escalation) promises 92% cost reduction. The blended cost calculation gives $0.133 for 100 pages vs $1.65 currently. The math is correct given the assumed page distribution:
- 35% of pages: Surya handles free ($0)
- 45% of pages: Gemini 2.5 Flash ($0.0014/page)
- 15% of pages: Haiku ($0.003/page)
- 5% of pages: Haiku for handwritten ($0.005/page)

**The problem is the 35% assumption.** The research assumes 35% of pages can be handled by Surya alone without any vision LLM. Based on the Dynamic Air Engineering test (ALL 5 PDFs were scanned, not digital), the actual percentage of pages that Surya can handle confidently may be much lower — perhaps 10-20% for scanned documents. If the distribution skews toward complex pages (which it will for a CA firm handling scanned ledgers), the actual savings may be 60-70%, not 92%.

**The 92% figure is optimistic. 60-75% is more realistic for this document mix.**

That's still a large and worthwhile saving. The claim just shouldn't be taken at face value without testing.

### Immediate fix: Switch to `claude-haiku-3-5` for OCR — APPROVE

This is the single best recommendation in all 9 documents. It is:
- One line of code change: `VISION_MODEL = "claude-haiku-3-5"` in `ocr_extractor.py`
- 73% cost reduction on OCR
- Same API, same response format, same integration
- Human verification step already catches any OCR quality degradation
- Reversible instantly if quality is unacceptable

**The mandatory human verification step before classification is the safety net that makes this safe.** The CA reviews the extracted line items before any CMA generation. If Haiku misreads a number, it gets caught at that stage. This is not guesswork — the project architecture is specifically designed to tolerate OCR imperfection.

**Verdict: APPROVE immediately.** This reduces the 7-company test cost from ~$8 to ~$3.50 before any other changes.

### Cloud OCR alternatives (Google Document AI, AWS Textract, Azure Document Intelligence)

All three are presented fairly. The pricing is accurate for March 2026:
- Azure Document Intelligence Layout: $0.010/page (39% cheaper than current Sonnet, same price as Haiku OCR)
- Google Document AI Layout Parser: $0.010/page (same)
- AWS Textract AnalyzeDocument: ~$0.015/page (basically same as Sonnet)

**The key insight the research buries:** Using Azure/Google Layout OCR at $0.010/page gives you roughly the same savings as switching to Haiku Vision ($0.003/page), but with MORE integration work (new cloud account, new SDK, new auth setup). Why would you do that?

The research's own recommendation at the bottom of file 01 is Azure Layout, then immediately says "BUT the real opportunity is the hybrid pipeline." The hybrid pipeline is the right call. Azure/Google cloud OCR by themselves are not a meaningful improvement.

**Verdict: ROAST for standalone adoption.** These services are not the right path given Haiku Vision is cheaper and requires zero new infrastructure.

### The Gemini 2.5 Flash recommendation — CONDITIONAL

Gemini 2.5 Flash at $0.0014/page vs Haiku at $0.003/page — does the 53% additional saving justify adding a second AI provider to the stack?

**Arguments for:**
- $0.0014 vs $0.003 is a real difference at scale
- Google has Mumbai region (lower latency from India)
- 1,500 free requests/day on Gemini API covers all development testing

**Arguments against:**
- Requires adding `google-generativeai` to `requirements.txt`
- Requires a Google Cloud account and API key (new secret management)
- Response format is different from Anthropic SDK — requires new prompt template and parsing code
- If Gemini API goes down or rate limits, the pipeline has a new failure mode to handle
- For 435 pages across 7 test companies, the saving is: 435 × ($0.003 - $0.0014) = $0.70
- You are adding 2-3 days of development work to save $0.70 on the test run

**The cost saving only becomes meaningful in production** when processing hundreds of companies per year. For the 7-company test, it is premature optimization.

**Verdict: CONDITIONAL** — implement after the 7-company test if quality benchmarks show Haiku is sufficient AND cost is still a concern. Not before.

### Open source OCR — Surya expansion

Surya is already in the stack. The suggestion to expand its use for page classification (scoring pages before deciding which LLM to use) is smart and has zero incremental cost. `page_filter.py` already exists. The integration path is minimal.

**One critical issue the research understates:** Surya is commented out of `backend/requirements.txt` because it "has heavy PyTorch deps, keep Docker image lean." Adding Surya back means adding PyTorch to the Docker image, which will significantly increase image build time and size. This is a real operational trade-off that the research glosses over with "already in stack."

**PyTorch in Docker on Windows adds significant complexity.** Build times, image sizes, and compatibility issues with CUDA drivers on the development machine are real concerns for a non-technical developer using Docker Compose.

**Verdict: CONDITIONAL** — expand Surya usage only after validating it works reliably in the Docker environment. Don't assume "already in stack" means "ready to use."

### PaddleOCR — ROAST

PaddleOCR is presented as a Phase 2 option. The 94.5% benchmark accuracy is real. But:
- It requires `paddlepaddle` + `paddleocr` — significant additional Docker dependencies
- PaddlePaddle is a Chinese deep learning framework that is less actively maintained for non-Chinese use cases than PyTorch
- The "Baidu origin" concern the research mentions is real from a data governance perspective for Indian CA firms (documents contain confidential client financial data)
- CPU inference at "5-15 seconds/page" means 435 pages would take 36-108 minutes of CPU time — this is a significant runtime cost that the research ignores when claiming it's "free"

The research correctly notes open source tools cannot fully replace Claude Vision for poor-quality scans. Given the Dynamic Air test showed all PDFs are scanned, PaddleOCR as a "handle 20-30% of pages" middle tier adds complexity without guaranteed payoff.

**Verdict: ROAST** for this project. The "Apache 2.0, no commercial restrictions" argument ignores the deployment complexity and the data governance question. Skip it.

### Tesseract — ROAST

The research correctly says "not recommended as primary tool." No table structure support is a fundamental blocker for financial statements.

**Verdict: ROAST** as primary tool. Valid only for image pre-processing (deskew, denoise) before feeding to a better OCR method.

### Docling — CONDITIONAL

IBM Docling is genuinely interesting. XBRL support, active development, MIT license, CPU-only mode. The concern about handwriting support (none) is the main blocker. Indian CA firm documents often have handwritten annotations, especially on older documents.

**But the Docker concern applies here too:** Even CPU-only Docling pulls significant model weights on first run. For a non-technical developer on Windows running Docker Compose, unexpected model downloads and OOM errors are support nightmares.

**Verdict: CONDITIONAL** — worth evaluating if the hybrid Surya+Gemini approach proves insufficient. Not for V1.

### The vision LLM quality rankings

The quality rankings in file 02 are based on "publicly available benchmark data, community evaluations, and model architecture analysis." This is honest. But the rankings for financial documents specifically — where Indian lakh/crore formatting, bracket negatives, and multi-year comparative tables matter — are not benchmarked on actual Indian financial documents. They are extrapolations.

**The key gap:** No research agent ran any of these alternatives on the actual Dynamic Air Engineering documents. All quality claims are theoretical. The mandatory recommendation before switching OCR provider should be: run 10 pages of the actual test data through the candidate model and compare outputs before committing.

---

## Section 7: What Was Missed

Several important topics none of the 3 research agents covered:

### 1. The Surya Docker/PyTorch issue is not resolved

Surya is commented out of `requirements.txt` with a note about heavy PyTorch deps. Multiple documents recommend "expanding Surya usage" without addressing this. For a Windows Docker Compose environment, PyTorch adds 1-2GB to the Docker image and requires careful handling of CPU vs CUDA modes. This needs a concrete resolution plan before Surya recommendations can be acted on.

### 2. No benchmarking protocol for OCR quality validation

Before switching any OCR component, someone needs to establish a baseline. None of the research documents provide a methodology for measuring OCR accuracy on this project's actual documents. Without a benchmark:
- You can't tell if Haiku is "good enough" vs Sonnet on your documents
- You can't tell if a 73% cost reduction is worth a 15% accuracy drop
- You can't compare alternatives objectively

**What's needed:** Run 20 pages from Dynamic Air through both Sonnet and Haiku, compare extracted line items manually, calculate error rate. This takes 2 hours and gives you real data instead of theoretical rankings.

### 3. No discussion of the verification step as a quality buffer

The research mentions "human verification catches OCR errors" in passing, but never quantifies how much OCR error the verification step can practically absorb. If Haiku produces 15% more errors than Sonnet, does the CA reviewing the extraction step catch all of them? What's the verification workflow like in the UI? This is critical to the cost-quality trade-off analysis.

The ExtractionVerifier UI exists in the frontend. How many line items does it show per page? How easy is it to spot a wrong number? If the UI is hard to use for catching OCR errors, the human quality backstop is weaker than assumed.

### 4. What happens when classification doubt rate is high

The 7-company test will produce a doubt rate. The research documents discuss the doubt report as a given but don't address: what does the CA actually DO with doubts? If 15% of 2,150 line items are doubts (322 items), does the CA resolve them manually? Is there a UI for this? The doubt resolution workflow directly affects whether the system is usable in practice, but it's completely absent from the research.

### 5. No discussion of the learned_mappings table growth strategy

The cost estimation correctly notes that the fuzzy match rate improves from 40% to 70% as `learned_mappings` grows. But the research doesn't describe how to ensure this actually happens. What triggers a new entry in `learned_mappings`? Only AI-classified items that are later verified? All classifications? How does the CA mark something as "confirmed correct"? The value of this system compounds over time only if the learning mechanism is correctly implemented.

### 6. Windows-specific Docker Compose issues are not addressed

The project runs on Docker Compose on Windows 11. Several recommendations add new dependencies (PaddleOCR, Docling, PyTorch, Google AI SDK). None of the research addresses:
- CPU vs GPU mode in Docker on Windows (no CUDA passthrough by default)
- Volume mount performance on Windows (can be very slow for large model files)
- WSL2 memory limits that affect model loading

For a non-technical developer, "just pip install X" can turn into a multi-day Docker debugging session on Windows. This risk is not acknowledged anywhere.

---

## Final Recommended Action Plan

Actions are ordered by impact-to-effort ratio and dependency. Do these in sequence.

### Action 1 — TODAY (15 minutes): Set the Anthropic spend cap

Go to Anthropic Console → Settings → Usage Limits. Set monthly spend cap to **$25**. This takes 2 minutes and prevents any bug from becoming a catastrophic bill. Do this before starting any test run.

### Action 2 — TODAY (1 hour): Switch OCR model to Haiku

In `/backend/app/services/extraction/ocr_extractor.py`, change line 37:
```
VISION_MODEL = "claude-sonnet-4-6"
```
to:
```
VISION_MODEL = "claude-haiku-3-5"
```

That's it. Run a single-company test on one PDF from Dynamic Air Engineering. Review the extracted line items in the ExtractionVerifier UI. If the quality is acceptable (numbers are right, table structure preserved), proceed with Haiku for the full test. If not, revert in 30 seconds.

This one change saves ~$4.50 on the 7-company test run.

### Action 3 — This week (2-4 hours): Replace the manual retry loop

In `backend/app/services/classification/ai_classifier.py`:
1. Add `tenacity>=8.2.0` to `backend/requirements.txt`
2. Replace the `[5, 15, 30]` sleep loop with a `tenacity` decorator using `wait_random_exponential(min=4, max=90)` and `stop_after_attempt(8)`
3. Set SDK `max_retries=4` in the Anthropic client constructor
4. Add `time.sleep(1.2)` inter-item throttle in the pipeline loop

This eliminates the rate limit restart loop that burned $4.99.

### Action 4 — This week (2-3 hours): Add checkpoint resumption

In `backend/app/services/classification/pipeline.py`, before the classification loop:
1. Fetch all line item IDs for the document
2. Query classifications table for which IDs already have a result
3. Skip already-classified items

This makes retries free (no re-processing, no re-billing).

### Action 5 — This week (1 hour): Add the unique constraint migration

In Supabase (via the dashboard SQL editor or a migration file):
1. Dedup any existing classification rows first
2. Add `UNIQUE (line_item_id)` constraint
3. Switch all `.insert()` calls to `.upsert(on_conflict="line_item_id")`

This makes the database idempotent at the schema level.

### Action 6 — Before the 7-company test (2 hours): Implement pre-run cost estimation

In the ARQ classification task:
1. Call `client.messages.count_tokens()` on a 5-item sample
2. Calculate estimated cost
3. Log it prominently
4. If cost exceeds `MAX_CLASSIFICATION_COST_USD` (default $5.00), fail fast with a clear message

### Action 7 — Before the 7-company test (3-4 hours): Build the state-file test runner

Enhance `run_all_extractions.py` to:
1. Maintain `test_run_state.json` at project root
2. Skip companies with `status == "completed"`
3. Run pre-flight checks (Redis, ARQ worker, Supabase, API key)
4. Log structured output with elapsed time
5. Stop at extraction gate with clear instructions for verification step

### Action 8 — After the 7-company test: Evaluate Haiku quality and decide next steps

After running all 7 companies through Haiku OCR and having the CA verify the extractions:
- If doubt rate and OCR errors are acceptable: Haiku is the production OCR model. Cost problem is largely solved.
- If OCR quality is insufficient for complex documents: evaluate Gemini 2.5 Flash as a selective fallback.
- Do NOT implement the hybrid pipeline before this quality data exists.

### What NOT to do (in priority order)

1. **Do NOT add PaddleOCR** — wrong complexity/benefit ratio for this project
2. **Do NOT add LangSmith** — invasive, irrelevant to this stack
3. **Do NOT implement Redis Pub/Sub progress tracking** — Docker logs are sufficient
4. **Do NOT use ARQ `auto_chain` flag in production code** — compliance risk
5. **Do NOT pursue Batch API for classification** — wait until post-V1 when the pipeline is proven stable
6. **Do NOT implement the full hybrid pipeline (Surya → Gemini → Haiku → Sonnet)** before benchmarking Haiku alone. That's four layers of complexity for a problem that Haiku alone might solve 80% of.

---

*The research across all 9 documents is generally accurate and well-sourced. The testing-fixes research (files 01-03) is the strongest — actionable, specific, correctly prioritized. The orchestration research (files 01-03) is solid but occasionally academic. The OCR alternatives research (files 01-03) is the most ambitious and the most speculative — useful for direction but the 92% cost reduction claim needs real-world validation before the architecture is changed.*

*The single most important insight across all 9 documents: OCR (Claude Sonnet Vision) is 75% of your cost. The one-line switch to Haiku is the highest-leverage action available. Do it first, measure quality, then decide what else needs to change.*
