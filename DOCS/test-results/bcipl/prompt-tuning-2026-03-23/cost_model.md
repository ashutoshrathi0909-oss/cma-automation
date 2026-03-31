# CMA Classification Cost Model

## Token Analysis (BCIPL, per item)

| Metric | Baseline Prompt | Optimized Prompt V1 |
|--------|----------------|---------------------|
| Input tokens (per batch of 15) | ~3,000 | ~4,430 |
| Output tokens (per batch of 15) | ~1,680 | ~1,670 |
| Total per batch | ~4,680 | ~6,100 |
| Input per item | ~200 | ~295 |
| Output per item | ~112 | ~111 |
| Total per item | ~312 | ~406 |

Note: Optimized prompt is ~47% larger on input (due to grouped fields + disambiguation rules) but output stays the same. The accuracy gain (78.4% -> 92.0%) far outweighs the marginal cost increase.

## Cost Projection (OpenRouter, Claude Haiku 4.5)

| Rate | Input: $0.80/M tokens | Output: $4.00/M tokens |
|------|----------------------|----------------------|

### Baseline Prompt

| Scenario | Items | Input Cost | Output Cost | Total |
|----------|-------|-----------|-------------|-------|
| BCIPL (all deduped, 352 items) | 352 | $0.058 | $0.161 | **$0.219** |
| BCIPL (all 448 including dupes) | 448 | $0.072 | $0.201 | **$0.273** |
| Avg company (est. ~250 items) | 250 | $0.040 | $0.112 | **$0.152** |
| 7 companies total | 1,750 | $0.280 | $0.784 | **$1.064** |

### Optimized Prompt V1

| Scenario | Items | Input Cost | Output Cost | Total |
|----------|-------|-----------|-------------|-------|
| BCIPL (all deduped, 352 items) | 352 | $0.085 | $0.160 | **$0.245** |
| BCIPL (all 448 including dupes) | 448 | $0.106 | $0.199 | **$0.305** |
| Avg company (est. ~250 items) | 250 | $0.059 | $0.111 | **$0.170** |
| 7 companies total | 1,750 | $0.413 | $0.777 | **$1.190** |

### After Rule Engine (est. 40% items handled by rules)

| Scenario | AI Items | Input Cost | Output Cost | Total | Savings |
|----------|----------|-----------|-------------|-------|---------|
| BCIPL | ~211 | $0.050 | $0.094 | **$0.144** | 41% |
| Avg company | ~150 | $0.035 | $0.067 | **$0.102** | 40% |
| 7 companies | ~1,050 | $0.248 | $0.466 | **$0.714** | 40% |

## Cost Summary

| Configuration | Per Company | 7 Companies | Accuracy |
|--------------|-------------|-------------|----------|
| Baseline prompt (no rules) | $0.152 | $1.064 | ~78% |
| Optimized prompt (no rules) | $0.170 | $1.190 | ~92% |
| Optimized + Rule Engine | $0.102 | $0.714 | ~95%+ |

## Key Insights

1. **Total experiment cost**: ~$0.90 (baseline $0.22 + retest $0.25 + interviews $0.04 + overhead ~$0.39)
2. **Haiku classification is extremely cheap** — even 7 companies costs ~$1
3. **The prompt size increase (+47%) is negligible** in absolute terms (+$0.02/company)
4. **Rule Engine is the biggest cost saver** — eliminates 40%+ of API calls
5. **Batch size 15 is optimal** — amortizes the prompt overhead across items
6. **Deduplication saves ~20%** — same item across FYs need not be re-classified
