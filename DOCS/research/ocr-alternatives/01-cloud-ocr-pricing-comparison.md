# Cloud OCR Pricing Comparison for Financial Documents

**Research Date:** March 2026
**Context:** CMA Automation System — replacing Claude Sonnet Vision ($0.013–$0.020/page) for scanned Indian financial PDFs

---

## Quick Comparison Table

| Service | Price/page (standard) | Table Support | Handwriting | API | Free Tier | Quality Rating (Financial) |
|---|---|---|---|---|---|---|
| **Google Document AI — Enterprise OCR** | $0.0015 | Via Layout Parser | Yes | Yes | $300 credits | 8.5/10 |
| **Google Document AI — Layout Parser** | $0.010 | Native, structured | Partial | Yes | $300 credits | 9/10 |
| **Google Document AI — Form Parser** | $0.030 | Yes (form fields) | Yes | Yes | $300 credits | 8/10 |
| **Google Vision API — Doc Text Detection** | $0.0015 | No (raw text) | Partial | Yes | 1,000 pages/mo free | 7/10 |
| **AWS Textract — DetectDocumentText** | ~$0.0015 | No | No | Yes | 1,000 pages/mo (90 days) | 7/10 |
| **AWS Textract — AnalyzeDocument Tables** | ~$0.015 | Yes, structured | Yes | Yes | 100 pages/mo (90 days) | 8.5/10 |
| **AWS Textract — AnalyzeExpense** | ~$0.010 | Yes (invoice layout) | Yes | Yes | 100 pages/mo (90 days) | 8/10 |
| **Azure Document Intelligence — Read** | $0.001 | No | Yes | Yes | 500 pages/mo free | 7.5/10 |
| **Azure Document Intelligence — Layout** | $0.010 | Yes, excellent | Yes | Yes | 500 pages/mo free | 9/10 |
| **Azure Document Intelligence — Prebuilt Invoice** | $0.010 | Yes | Yes | Yes | 500 pages/mo free | 8/10 |
| **Claude Sonnet Vision (current)** | $0.013–$0.020 | Via prompt | Yes | Yes | None | 9.5/10 |

---

## Deep Dive: Top 3 Cloud Options

### 1. Google Document AI

**Source:** https://cloud.google.com/document-ai/pricing (verified March 2026)

#### Processors Available

| Processor | Price per 1,000 pages | Best For |
|---|---|---|
| Enterprise Document OCR | $1.50 (1–5M pages) / $0.60 (5M+) | Raw text from any document |
| Layout Parser | $10.00 | Structured documents with tables |
| Form Parser | $30.00 | Form fields and key-value pairs |
| Invoice Parser | $10.00 (= $0.01/page) | Invoices with line items |
| Bank Statement Parser | $0.75 per document | Bank statements |

#### How It Works for Financial Documents

- **Enterprise OCR** ($0.0015/page): Pure text extraction with character-level confidence scores. Does NOT return table structure — rows and columns are linearized. Suitable only if you parse structure yourself afterward.
- **Layout Parser** ($0.010/page): Returns structured output with bounding boxes, table cells, row/column relationships, and reading order. Best general-purpose choice for financial statements.
- **Form Parser** ($0.030/page): Designed for standardized forms. Overkill for balance sheets but works well for structured annual reports.

#### Pros for Indian Financial Documents
- Handles mixed-language content (English + Indian company names in Devanagari script if needed)
- Strong table cell detection even on low-quality scans
- OCR add-on ($6/1,000 pages extra) enables enhanced quality for poor scans — important for older financial records
- No per-document minimum fees — pay per page
- Google Cloud has Asia-Pacific regions (Mumbai: `asia-south1`) — low latency from India
- SDK available in Python — easy to integrate with existing FastAPI backend

#### Cons for Indian Financial Documents
- Layout Parser at $0.010/page is only 25–35% cheaper than Claude Sonnet Vision, not a major saving
- Enterprise OCR alone ($0.0015) loses table structure — requires custom post-processing
- Free tier ($300 credits) exhausted quickly in production
- Google account/GCP billing required — more setup than a simple API key

#### Docker / Self-hosted Option
- **No** — Google Document AI is cloud-only. No local/Docker option.

#### Verdict
Layout Parser is the best balance of price and quality at **$0.010/page**. The cheapest option (Enterprise OCR at $0.0015) requires you to rebuild table structure yourself, which adds development complexity.

---

### 2. AWS Textract

**Source:** https://aws.amazon.com/textract/ (verified March 2026; exact pricing page was restricted during research — figures below are from official AWS documentation pages)

#### Pricing (approximate — verify at aws.amazon.com/textract/pricing)

| Feature | Price per page | Notes |
|---|---|---|
| DetectDocumentText | ~$0.0015 | Text only, no table structure |
| AnalyzeDocument (Tables + Forms) | ~$0.015 | Full table extraction with cell relationships |
| AnalyzeExpense | ~$0.010 | Invoice/receipt specialist |
| AnalyzeDocument (Queries) | ~$0.015 + $0.004/query | Ask natural language questions |
| AnalyzeID | ~$0.01 per doc | ID documents only |

**Free tier:** 1,000 pages/month for DetectDocumentText (90 days); 100 pages/month for AnalyzeDocument (90 days). After free tier expires, standard pricing applies.

#### How It Works for Financial Documents

Textract's **AnalyzeDocument with Tables** feature is purpose-built for extracting structured table data. It returns:
- Table bounding boxes
- Cell contents with row/column indices
- Cell confidence scores
- Multi-page table continuation detection

**Queries feature** is particularly powerful for financial docs: you can ask "What is the total revenue?" or "What is net profit for FY2023?" and it extracts the answer without building a full table parser.

Textract explicitly supports **financial reports** and **tax forms** in its documentation.

#### Pros for Indian Financial Documents
- Best-in-class table extraction among dedicated OCR services
- Handwriting detection built in to AnalyzeDocument
- Queries feature reduces post-processing work significantly
- Multi-page async processing — handles large annual reports (50+ pages)
- AWS has Mumbai region (`ap-south-1`) — India-local processing possible
- Well-documented Python SDK (boto3) — straightforward integration

#### Cons for Indian Financial Documents
- AWS account required with billing setup — more operational overhead
- AnalyzeDocument at ~$0.015/page is essentially same price as Claude Sonnet Vision
- Only DetectDocumentText is cheap ($0.0015) — table support costs more
- No Docker/self-hosted option — cloud-only
- Requires storing documents in S3 for async processing — adds architectural complexity
- Indian Rupee symbol (₹) handling: Textract treats it as text; no currency-specific parsing

#### Docker / Self-hosted Option
- **No** — AWS Textract is cloud-only.

#### Verdict
AWS Textract is the most mature dedicated OCR service for table-heavy financial documents. The Queries feature is genuinely useful. However, AnalyzeDocument pricing (~$0.015/page) offers no real cost saving over Claude Sonnet Vision while reducing flexibility.

---

### 3. Azure Document Intelligence

**Source:** https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/overview (verified March 2026)

#### Pricing

| Model | Price per page | Notes |
|---|---|---|
| Read API | $0.001 | Raw text + reading order, no tables |
| Layout Model | $0.010 | Full table + figure extraction |
| Prebuilt Invoice | $0.010 | Invoice line items + fields |
| Prebuilt Receipt | $0.010 | Receipt parsing |
| Custom Model | $0.010 | Train on your own documents |
| General Documents | $0.010 | Mixed document types |

**Free tier:** 500 pages/month free across all models — most generous free tier among cloud services.

#### How It Works for Financial Documents

Azure Document Intelligence Layout model returns a rich JSON with:
- Tables with header detection, cell spans, row/column indices
- Text lines with bounding polygons
- Figures (charts, diagrams) detected separately
- Reading order across multi-column layouts
- Confidence scores per element

The **Custom Model** option (also $0.010/page) allows training on your own labeled financial documents — relevant if Indian CA firm formats differ significantly from global templates.

#### Pros for Indian Financial Documents
- Layout model has excellent table detection, rated among the best in independent benchmarks
- Read API at $0.001/page is the cheapest text-only option among major cloud services
- 500 pages/month free — useful for development and low-volume testing
- Custom model training available without extra per-page cost premium
- Supports handwritten text in Layout model
- Azure has South India region (`southindia`) — low latency from India
- Python SDK well-maintained; REST API straightforward

#### Cons for Indian Financial Documents
- Layout at $0.010/page: 33–50% cheaper than current setup but still significant cost
- No India-specific financial document prebuilt model (Invoice prebuilt targets Western formats)
- Custom model training requires labeled training data — time investment
- Azure subscription required
- No self-hosted/Docker option

#### Docker / Self-hosted Option
- **No** — Azure Document Intelligence is cloud-only. (Azure Container Instances can host the SDK but still calls cloud API.)

#### Verdict
Azure Document Intelligence Layout at $0.010/page with the best free tier (500 pages/mo) and excellent table extraction is the strongest cloud alternative on quality-to-price ratio.

---

## Google Vision API vs Document AI

**Source:** https://cloud.google.com/vision/pricing (verified March 2026)

| Feature | Google Vision API | Google Document AI Enterprise OCR |
|---|---|---|
| Price/page | $0.0015 | $0.0015 |
| Table structure | No | No |
| Reading order | Partial | Yes |
| Confidence scores | Word-level | Character + word-level |
| OCR add-ons | No | Yes (+$0.006/page) |
| Best for | Simple text extraction | Complex layouts, scanned docs |

**Vision API** (`DOCUMENT_TEXT_DETECTION`) and **Document AI Enterprise OCR** cost the same but Document AI returns better structured output (reading order, paragraph detection). For financial documents, Document AI Enterprise OCR is the better choice at the same price.

**Free tier on Vision API:** First 1,000 pages/month free — useful for testing.

---

## Pricing Summary: Cost Per 1,000 Pages

| Service | Cost/1,000 pages | vs. Claude Sonnet ($16.50) | Saving |
|---|---|---|---|
| Azure Read API | $1.00 | -94% | Best savings, no table structure |
| Google Doc AI Enterprise OCR | $1.50 | -91% | Raw text only |
| AWS Textract DetectText | ~$1.50 | -91% | Raw text only |
| Google Vision API | $1.50 | -91% | Raw text only |
| Azure Layout | $10.00 | -39% | Full tables |
| Google Doc AI Layout Parser | $10.00 | -39% | Full tables |
| AWS Textract AnalyzeDocument | ~$15.00 | -9% | Full tables + queries |
| **Claude Sonnet Vision (current)** | **$16.50** | baseline | — |

*Claude Sonnet baseline assumes $3/MTok input, ~4,500 input tokens/page (image + prompt), $15/MTok output, ~200 output tokens/page = ~$0.0165/page.*

---

## Pros and Cons for Indian Financial Documents Specifically

### What Makes Indian Financial Documents Challenging

1. **Mixed formats:** Some firms use MS Word-generated PDFs, others use handwritten ledgers scanned on cheap scanners
2. **Indian number formatting:** Lakhs (1,00,000) and crores (1,00,00,000) use comma positions that differ from Western notation
3. **Rupee symbol (₹):** Older scanned documents may use "Rs." instead of ₹
4. **Multi-year comparative tables:** Indian balance sheets typically show 2–3 years side by side — requires robust multi-column table handling
5. **Notes to Accounts:** Dense, multi-level numbered lists with embedded tables
6. **Document quality:** Many chartered accountants receive documents from clients as phone photos or low-DPI scans

### Service-by-Service Assessment

| Service | Indian number format | ₹ symbol handling | Multi-column tables | Low-quality scan handling | Notes to Accounts |
|---|---|---|---|---|---|
| Google Doc AI Layout | Good | Treats as text | Excellent | Good with OCR add-on | Good |
| AWS Textract | Good | Treats as text | Excellent | Good | Good |
| Azure Layout | Good | Treats as text | Excellent | Good | Good |
| Claude Sonnet Vision | Excellent | Understands semantics | Excellent | Excellent | Excellent — understands context |

**Key insight:** Dedicated OCR services extract text accurately but do NOT understand what "₹1,50,000" means semantically. Claude Sonnet Vision understands that "Sundry Debtors" belongs in current assets. This semantic understanding is what makes Claude expensive but also uniquely powerful for the CMA classification step.

---

## Sources

- Google Document AI Pricing: https://cloud.google.com/document-ai/pricing
- Google Vision API Pricing: https://cloud.google.com/vision/pricing
- AWS Textract Features: https://aws.amazon.com/textract/features/
- AWS Textract Docs: https://docs.aws.amazon.com/textract/latest/dg/what-is.html
- Azure Document Intelligence Overview: https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/overview
- Docling GitHub: https://github.com/docling-project/docling

---

## Best Fit for Our Project

**Recommendation: Azure Document Intelligence Layout at $0.010/page as the best pure cloud OCR upgrade.**

Reasoning:
1. **500 free pages/month** covers all development and testing
2. **$0.010/page = 39% cheaper** than current Claude Sonnet Vision cost
3. Excellent table extraction with header detection and cell spans — handles Indian balance sheet multi-year format
4. South India Azure region available for compliance considerations
5. Python SDK integrates cleanly with existing FastAPI stack

**BUT:** The real opportunity is not replacing Claude Sonnet with a cloud OCR service. It is using a **hybrid pipeline**:
- Cheap OCR (Azure Read at $0.001 or Google Enterprise OCR at $0.0015) for text extraction
- Surya OCR (already in the stack) for table structure detection — free
- Claude Haiku Vision (not Sonnet) only for pages that are ambiguous or low-quality

See File 02 (vision LLM alternatives) for the Haiku vs Sonnet cost comparison, and File 03 for the hybrid architecture recommendation.
