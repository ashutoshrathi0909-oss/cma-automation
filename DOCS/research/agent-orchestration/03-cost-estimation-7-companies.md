# Cost Estimation — CMA Pipeline, 7 Companies

**Research Date:** March 2026
**Models Used in Our Pipeline:**
- OCR: `claude-sonnet-4-6` (Vision) — used in `ocr_extractor.py`
- Classification: `claude-haiku-4-5-20251001` — used in `ai_classifier.py`

---

## 1. Confirmed Pricing (March 2026)

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Notes |
|-------|----------------------|------------------------|-------|
| Claude Sonnet 4.6 | **$3.00** | **$15.00** | Our OCR model. 1M context at standard price (no long-context premium). |
| Claude Haiku 4.5 | **$1.00** | **$5.00** | Our classifier. ~$1/$5 per 1M tokens. |

**Batch API discount (50% off):** Available if we use the Batch API instead of real-time calls.
**Prompt caching discount (90% off input):** Available if we cache the CMA field list across calls.

*Sources: [Anthropic Pricing Docs](https://platform.claude.com/docs/en/about-claude/pricing), [MetaCTO Pricing Breakdown](https://www.metacto.com/blogs/anthropic-api-pricing-a-full-breakdown-of-costs-and-integration), [IntuitionLabs Claude Pricing](https://intuitionlabs.ai/articles/claude-pricing-plans-api-costs)*

---

## 2. Token Assumptions (Per the Task Brief)

### OCR (Claude Sonnet Vision) — Per Page

| Token Type | Tokens | Rationale |
|-----------|--------|-----------|
| Input: image | ~2,000 | Standard-resolution financial document page at 1600px width |
| Input: prompt/system | ~200 | System prompt + page label overhead |
| Output | ~400 | Structured JSON with line items (tool_use response) |
| **Total per page** | **~2,600 input + 400 output** | |

*Our actual `ocr_extractor.py` uses `max_tokens=16000` per batch of pages, but the per-page output estimate of 400 tokens is reasonable for typical financial pages.*

### Classification (Claude Haiku) — Per Line Item

| Token Type | Tokens | Rationale |
|-----------|--------|-----------|
| Input | ~800 | Prompt + CMA field list (384 fields) + fuzzy candidates |
| Output | ~150 | Structured tool_use JSON with classification result |
| **Total per item** | **~800 input + 150 output** | |

### Fuzzy Match Assumption
- **40% of items** matched by fuzzy matcher (no Haiku cost)
- **60% of items** escalated to Haiku for AI classification

---

## 3. Per-Company Cost Calculations

### Formulas

```
OCR Cost = pages × (2,600 input tokens × $3/1M + 400 output tokens × $15/1M)
         = pages × ($0.0078 + $0.006)
         = pages × $0.0138

AI Classification Cost = items × 0.60 × (800 input × $1/1M + 150 output × $5/1M)
                       = items × 0.60 × ($0.0008 + $0.00075)
                       = items × 0.60 × $0.00155
                       = items × $0.00093
```

### Per-Company Breakdown

| Co | Company | Pages | Items | OCR Cost | Haiku Items | Classify Cost | Total |
|----|---------|-------|-------|----------|-------------|---------------|-------|
| 1 | Company 1 (Simplest) | 30 | 150 | $0.41 | 90 | $0.14 | **$0.56** |
| 2 | Company 2 | 40 | 200 | $0.55 | 120 | $0.19 | **$0.74** |
| 3 | Company 3 | 50 | 250 | $0.69 | 150 | $0.23 | **$0.92** |
| 4 | Company 4 | 60 | 300 | $0.83 | 180 | $0.28 | **$1.11** |
| 5 | Company 5 | 70 | 350 | $0.97 | 210 | $0.33 | **$1.30** |
| 6 | Company 6 | 85 | 400 | $1.17 | 240 | $0.37 | **$1.54** |
| 7 | Dynamic Air (Most Complex) | 100 | 500 | $1.38 | 300 | $0.47 | **$1.85** |

### Totals

| Metric | Value |
|--------|-------|
| Total pages across 7 companies | **435 pages** |
| Total line items | **2,150 items** |
| Items reaching Haiku (60%) | **1,290 items** |
| **Total OCR cost** | **$6.00** |
| **Total Classification cost** | **$2.01** |
| **TOTAL PIPELINE COST** | **$8.01** |

---

## 4. Low / High Estimate Range

Real-world costs vary from the assumptions above. Here are low and high scenarios:

### Low Estimate (Optimistic)

| Adjustment | Effect |
|-----------|--------|
| Pages average only 1,500 input tokens (simpler pages, smaller images) | −23% on OCR |
| Fuzzy match rate is 55% instead of 40% (better matching) | −25% on classification |
| Output is 300 tokens/page instead of 400 (shorter responses) | −10% on OCR |

**Low estimate total: ~$5.20** (per-company: $0.37 – $1.20)

### High Estimate (Conservative)

| Adjustment | Effect |
|-----------|--------|
| Pages average 3,000 input tokens (complex dense pages) | +50% on OCR |
| Fuzzy match rate is only 30% (worse matching, more Haiku) | +25% on classification |
| Output is 600 tokens/page (more line items per page) | +50% on OCR output |
| Re-runs needed (failed jobs, retries) | +30% overall |

**High estimate total: ~$18.00** (per-company: $1.10 – $3.80)

### Summary Range

| Scenario | Total Cost | Per-Company Avg |
|----------|-----------|-----------------|
| Low (optimistic) | ~$5.20 | ~$0.74 |
| **Mid (base estimate)** | **~$8.01** | **~$1.14** |
| High (conservative) | ~$18.00 | ~$2.57 |

---

## 5. OCR vs Classification Cost Breakdown

### Base Estimate ($8.01 total)

```
OCR (Claude Sonnet Vision):     $6.00  (74.9% of total)
Classification (Claude Haiku):  $2.01  (25.1% of total)
```

### Key Insight

**OCR dominates the cost** because:
1. Sonnet is 3× more expensive per input token than Haiku ($3 vs $1)
2. Sonnet is 3× more expensive per output token ($15 vs $5)
3. Vision images add 2,000 input tokens per page
4. Classification uses fuzzy matching first, reducing Haiku calls by 40%

This means **improving OCR efficiency has 3× the cost impact** of improving classification efficiency.

---

## 6. Cost Optimization Strategies

### Strategy 1: Use Batch API (50% discount)

If we don't need real-time results (overnight batch is fine), the Anthropic Batch API gives a flat 50% discount on both input and output tokens.

| Scenario | Standard Cost | Batch API Cost | Saving |
|---------|--------------|----------------|--------|
| Base estimate | $8.01 | $4.01 | $4.00 |
| High estimate | $18.00 | $9.00 | $9.00 |

**How to use:** Classification is the easiest candidate — we can batch all `classify_line_item` calls for a company after extraction completes. OCR requires near-real-time processing (we need the output to continue), so batch API is harder to apply there.

**Source:** [Anthropic Batch API Pricing](https://platform.claude.com/docs/en/about-claude/pricing)

---

### Strategy 2: Prompt Caching for Classification (90% input discount)

The Haiku classification prompt contains a static section: the full CMA field list (~384 fields, ~1,500 tokens). This is the same every call. Prompt caching can cache this prefix and charge only 10% of input cost for it.

**Estimated saving:** If the CMA field list is 1,500 of the 800-token average prompt, caching it saves:
- Cached portion: ~600 tokens of the 800 input = 75% of input is cacheable
- Cache read cost is 10% of normal = effectively 70% input savings on classification
- Impact: Classification input cost drops from $1.03 to ~$0.31

**Net saving with prompt caching:** ~$0.72 on classification (base estimate)

*Note: Prompt caching requires specific API usage patterns. See [Anthropic Prompt Caching Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching).*

---

### Strategy 3: Improve Fuzzy Match Rate

The fuzzy matcher in our pipeline (`fuzzy_matcher.py`) currently matches ~40% of items. If we can raise this to 60% through better reference data (the `learned_mappings` table grows with each verified classification), Haiku calls drop by 33%.

| Fuzzy Rate | Haiku Calls | Classification Cost | Saving vs Base |
|-----------|-------------|--------------------|-|
| 30% (cold start) | 1,505 | $2.35 | — |
| 40% (base assumption) | 1,290 | $2.01 | $0.34 |
| 55% (after 3 companies) | 968 | $1.51 | $0.84 |
| 70% (fully trained) | 645 | $1.00 | $1.35 |

**Action:** After each company run, verify classifications correctly update `learned_mappings`. By Company 7, fuzzy match rate should improve significantly.

---

### Strategy 4: Page Filtering (Already Implemented)

Our `page_filter.py` already filters blank pages before sending to Claude Sonnet Vision. Based on the Dynamic Air test (80+ pages after filtering from ~100 total), blank page filtering saves approximately 5-15% of OCR cost.

No action needed — this is already in the pipeline.

---

### Strategy 5: Image Compression (Already Implemented)

Our `ocr_extractor.py` already uses:
- `CONVERSION_DPI = 200` (not 300 — saves ~50% on image size vs high-DPI)
- `MAX_IMAGE_WIDTH = 1600` (resizes if larger)
- JPEG at quality 85 (not PNG — 4-5× smaller file)

No action needed — image compression is already optimized.

---

## 7. INR Cost Translation

At the current exchange rate (~₹83.5 / $1 USD as of March 2026):

| Scenario | USD | INR |
|---------|-----|-----|
| Low estimate | $5.20 | ~₹434 |
| Base estimate | $8.01 | ~₹668 |
| High estimate | $18.00 | ~₹1,503 |

The per-company note in `ocr_extractor.py` states: `Cost: ~₹2.30 per page (claude-sonnet-4-6)`. Let us verify:
- $3.00/1M input × 2,200 tokens/page = $0.0066 input
- $15.00/1M output × 400 tokens/page = $0.006 output
- Total = $0.0126/page = ~₹1.05/page (at ₹83.5/$)

The code comment of ₹2.30/page appears to use an older exchange rate or older Sonnet pricing. At March 2026 pricing it is closer to **₹1.05 per page** for OCR.

---

## 8. Budget Recommendation

### For the 7-Company Test Run

| Budget Item | Amount |
|------------|--------|
| Base pipeline cost | $8.01 |
| Re-run buffer (failed jobs, retries, testing) | $5.00 |
| Development/debugging calls | $3.00 |
| **Recommended test budget** | **$16.00 (~₹1,336)** |

### Buffer Rationale

- **2× multiplier** on base cost is standard for first-time pipeline runs
- Expect 1-2 companies to need re-extraction due to extraction errors
- Classification retries on rate limit errors add ~10-20% to Haiku cost
- Additional calls during debugging (running individual documents multiple times)

### Safe "Never Exceed" Limit

Set an Anthropic API spend limit of **$25.00** for the 7-company test. This provides a 3× buffer over base cost and covers worst-case re-runs.

To set this: Anthropic Console → Settings → Usage Limits → Monthly spend cap.

---

## 9. Full Cost Summary Table

| | Co 1 | Co 2 | Co 3 | Co 4 | Co 5 | Co 6 | Co 7 (Dynamic Air) | **TOTAL** |
|--|------|------|------|------|------|------|---------------------|-----------|
| Pages | 30 | 40 | 50 | 60 | 70 | 85 | 100 | **435** |
| Line Items | 150 | 200 | 250 | 300 | 350 | 400 | 500 | **2,150** |
| OCR cost | $0.41 | $0.55 | $0.69 | $0.83 | $0.97 | $1.17 | $1.38 | **$6.00** |
| Classify cost | $0.14 | $0.19 | $0.23 | $0.28 | $0.33 | $0.37 | $0.47 | **$2.01** |
| **Total** | **$0.56** | **$0.74** | **$0.92** | **$1.11** | **$1.30** | **$1.54** | **$1.85** | **$8.01** |
| Low est. | $0.37 | $0.49 | $0.60 | $0.72 | $0.85 | $1.00 | $1.20 | **$5.23** |
| High est. | $1.10 | $1.48 | $1.85 | $2.22 | $2.59 | $3.15 | $3.61 | **$16.00** |

---

## Recommended for Our Project

1. **Budget $16 USD (~₹1,336)** for the 7-company test. This is the realistic all-in number including retries.

2. **Set a $25 hard cap** in the Anthropic Console before starting. This prevents any accidental runaway cost from loops or bugs.

3. **OCR is the cost driver** (75% of spend). Verify that `page_filter.py` is correctly removing blank/non-financial pages before the test run — each incorrect page sent to Sonnet costs ~$0.013.

4. **Do not use real-time Classification for all 7 companies at once**. Although our ARQ worker is `max_jobs=1` (sequential), if you ever increase concurrency, rate limits will spike costs from retries. Keep sequential.

5. **After the 7-company test, consider the Batch API** for future production use — the 50% discount makes classification cost $1.00 instead of $2.01 for this same workload.

6. **The `learned_mappings` investment pays dividends.** Every correctly verified classification trains the fuzzy matcher. By the time all 7 companies are done, Company 7's classification should be faster and cheaper than Company 1's.

---

*Sources:*
- [Anthropic API Pricing Docs](https://platform.claude.com/docs/en/about-claude/pricing)
- [Claude Sonnet 4.6 Pricing — pricepertoken.com](https://pricepertoken.com/pricing-page/model/anthropic-claude-sonnet-4.6)
- [Claude Haiku 4.5 Announcement](https://www.anthropic.com/news/claude-haiku-4-5)
- [Anthropic API Pricing 2026 — MetaCTO](https://www.metacto.com/blogs/anthropic-api-pricing-a-full-breakdown-of-costs-and-integration)
- [Anthropic API Pricing Guide — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [Claude API Pricing Guide 2026 — aifreeapi.com](https://www.aifreeapi.com/en/posts/claude-api-pricing-per-million-tokens)
- [Claude Sonnet 4.6 Context Window Announcement](https://blockchain.news/ainews/anthropic-claude-opus-4-6-and-sonnet-4-6-launch-1m-token-context-at-standard-pricing-business-impact-and-2026-analysis)
