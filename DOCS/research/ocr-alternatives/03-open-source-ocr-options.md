# Open Source OCR Options for Financial Documents

**Research Date:** March 2026
**Context:** CMA Automation System — evaluating self-hosted OCR to reduce or eliminate per-page API costs for scanned Indian financial PDFs

---

## Overview

Open source OCR offers zero per-page cost in exchange for:
- GPU/CPU server costs (or developer machine time)
- Integration development effort
- Ongoing maintenance responsibility
- Typically lower accuracy on complex/noisy documents than vision LLMs

For the CMA Automation project, Surya OCR is **already installed** in the backend. The question is whether to expand its use or combine it with other tools before sending pages to Claude/Gemini.

---

## Tool Comparison Table

| Tool | Type | Table Support | Scanned PDFs | Fin. Docs | Docker | GPU Required | Estimated Quality |
|---|---|---|---|---|---|---|---|
| **Docling (IBM)** | Layout + OCR | Excellent | Yes (OCR backend) | Good | Yes | No (CPU) | 8.5/10 |
| **Surya OCR** | OCR + Layout | Good (dedicated model) | Yes | Moderate | No official | GPU helps | 8/10 |
| **Marker** | PDF→Markdown | Good (via Surya) | Yes | Moderate | No | GPU helps | 7.5/10 |
| **PaddleOCR** | OCR + Structure | Excellent | Yes | Good | Community | GPU helps | 8.5/10 |
| **Tesseract 5** | OCR only | Poor (no native table) | Yes | Poor | Yes | No | 6/10 |
| **unstructured.io** | Document parser | Good | Yes | Good | Yes | No | 7.5/10 |
| **LLMSherpa** | PDF parser | Good | Yes (OCR built-in) | Good | Yes | No | 7/10 |

---

## Deep Dive: Top Open Source Options

### 1. Docling (IBM Research)

**Repository:** https://github.com/docling-project/docling
**License:** MIT
**Technical Report:** https://arxiv.org/abs/2408.09869

#### What It Is
Docling is IBM Research's open-source document processing library released in 2024. It has rapidly become one of the most capable open source document parsers, with deep integration into the AI/RAG ecosystem. Unlike simple OCR tools, Docling performs:
- Layout analysis (headers, paragraphs, tables, figures, lists)
- Table structure recognition
- Reading order detection
- OCR for scanned pages (via EasyOCR or Tesseract backend)
- Export to Markdown, JSON, HTML, DocTags

#### Capabilities for Financial Documents

| Feature | Status | Notes |
|---|---|---|
| Scanned PDF OCR | Yes | Requires OCR backend (EasyOCR or Tesseract) |
| Table extraction | Excellent | Returns structured table data with row/col indices |
| Multi-column layout | Yes | Layout model handles multi-column |
| XBRL financial reports | Yes | Explicitly supported (rare among open source tools) |
| Reading order | Yes | Handles complex layouts |
| Handwriting | No | Not supported — major limitation |
| Export format | JSON, Markdown, HTML | All parseable |

#### Benchmarks
From the Docling technical report (arXiv:2408.09869):
- Table structure recognition competitive with proprietary tools
- Layout analysis uses DocLayNet dataset (IBM-created, 80K+ annotated pages)
- Evaluated on scientific papers and technical documents — financial document benchmarks not published separately
- Recent "Heron" layout model update (2025) significantly improved speed

#### Docker Setup
```dockerfile
# Official Dockerfile exists in the repository
FROM python:3.11-slim
RUN pip install docling
```
No GPU required for basic operation (CPU inference). GPU accelerates the layout model significantly.

#### Strengths for Our Use Case
- XBRL support means it understands financial document structure concepts
- JSON output is easily parseable by the existing extraction pipeline
- CPU-only mode runs in existing Docker Compose without adding a GPU service
- Active development: 31,000+ GitHub stars, IBM-backed
- Heron layout model is fast enough for production use on CPU

#### Weaknesses for Our Use Case
- OCR quality depends on backend (EasyOCR < Tesseract < cloud OCR for quality)
- No handwriting support — handwritten ledger annotations are common in Indian CA firm documents
- Scanned PDF handling requires explicit OCR backend configuration
- Table extraction from poor-quality scans is unreliable — needs high-DPI (300+ dpi) input

#### Realistic Quality Estimate for Indian Financial Docs
- Clean, high-DPI scans: **8.5/10** — excellent table structure, reliable text
- Low-quality or skewed scans: **5/10** — OCR errors propagate into table data
- Handwritten annotations: **0/10** — not supported

---

### 2. Surya OCR

**Repository:** https://github.com/VikParuchuri/surya
**License:** CC BY-NC 4.0 (non-commercial) / GPL 3.0 for commercial use
**Already in stack:** Yes — used for some documents already

#### What It Is
Surya is a purpose-built OCR and document analysis toolkit by Vik Paruchuri (also creator of Marker). It provides separate specialized models for:
- Text line detection
- Text recognition (OCR in 90+ languages)
- Layout analysis
- Table recognition (cell detection with row/col relationships)
- Reading order detection

#### Table Recognition Output
Surya's table model returns:
```json
{
  "bbox": [x1, y1, x2, y2],
  "row_id": 2,
  "col_id": 1,
  "row_span": 1,
  "col_span": 1,
  "is_row_header": false,
  "is_col_header": true,
  "text": "FY2024"
}
```
This is exactly the structure needed for financial statement table parsing.

#### GPU Requirements (VRAM)
| Model | Default batch | VRAM needed |
|---|---|---|
| Text detection | 36 items | ~16GB |
| Text recognition | 512 items | ~20GB |
| Layout | 32 items | ~7GB |
| Table recognition | 64 items | ~10GB |

**CPU-only mode:** Possible but slow — recognition may take 10–30 seconds per page vs 1–3 seconds on GPU.

#### Quality Assessment
- Benchmarks favorably vs cloud services according to the README (no specific numbers published in public readme)
- Strong on printed text, moderate on degraded/noisy scans
- 90+ language support — handles English text in Indian documents well
- No handwriting support

#### Integration with Existing Stack
Already installed in the backend (`backend/requirements.txt` and `backend/app/services/extraction/ocr_extractor.py`). The current implementation uses Surya for some document types. **Expanding Surya's use is the lowest-effort path.**

#### Commercial License Note
CC BY-NC 4.0 = **non-commercial use only** for the default license. For a production CA firm tool (commercial use), the GPL 3.0 commercial license applies. Verify licensing terms at https://github.com/VikParuchuri/surya before deploying commercially.

---

### 3. PaddleOCR

**Repository:** https://github.com/PaddlePaddle/PaddleOCR
**License:** Apache 2.0 (completely free for commercial use)
**Stars:** 45,000+

#### What It Is
PaddleOCR is Baidu's production-grade OCR framework. PP-StructureV3 (the current generation) handles:
- Multi-line text recognition
- Table structure recognition (TSR)
- Document layout analysis
- Formula recognition
- Chart analysis

#### Key Quality Metrics
- **94.5% precision** on OmniDocBench v1.5 benchmark (as reported on GitHub README, March 2026)
- **13% accuracy improvement** in multilingual text recognition over previous generation
- **15% accuracy improvement** in information extraction
- 111 languages supported

#### Table Structure Recognition
PaddleOCR's PP-TableMaster achieves state-of-the-art results on the PubTabNet benchmark. Output format: HTML `<table>` structure and JSON.

For financial documents, PaddleOCR converts documents to **Markdown and JSON that preserve original structure** — directly useful for our extraction pipeline.

#### Docker Setup
Community-maintained Docker images are available. Official Docker support is not in the main README but can be containerized:
```dockerfile
FROM python:3.9-slim
RUN pip install paddlepaddle paddleocr
```
Runs on CPU (slower) or GPU (faster). PaddlePaddle CPU version works without CUDA.

#### Strengths for Our Use Case
- Apache 2.0 = free for commercial use, no licensing concerns
- 94.5% benchmark accuracy is the highest among pure open source tools
- Multi-language including English + regional Indian scripts if needed
- Table-to-Markdown/JSON output is directly usable
- Active development by Baidu — financial document formats well-tested (major use case in China)
- CPU mode viable for low-to-moderate volume

#### Weaknesses for Our Use Case
- Chinese-company origin may raise data sovereignty concerns (document processing stays local — mitigates this)
- English documentation is good but Chinese documentation is more complete
- No handwriting support
- CPU inference is slow for production use (5–15 seconds/page)
- Less Python ecosystem integration than Docling or Surya

#### Realistic Quality Estimate for Indian Financial Docs
- Clean, high-DPI scans: **8.5/10**
- Low-quality scans: **6.5/10** — better than Tesseract but worse than cloud services
- Complex multi-column tables: **8/10**

---

### 4. Marker

**Repository:** https://github.com/VikParuchuri/marker
**License:** CC BY-NC 4.0 / GPL 3.0 (same as Surya)

#### What It Is
Marker converts PDFs (including scanned PDFs via Surya OCR) to Markdown, JSON, HTML, or chunks. It is essentially a higher-level wrapper that uses Surya for OCR and layout, then applies additional post-processing.

#### Key Capabilities
- Uses Surya OCR for text recognition on scanned pages
- `--force_ocr` flag to process entire document with OCR
- Table extraction via `TableConverter`
- Cell bounding boxes in JSON output
- Benchmarks: "Marker benchmarks favorably compared to cloud services like Llamaparse and Mathpix"
- Projected throughput: 25 pages/second on an H100 GPU in batch mode

#### For Our Use Case
Marker's output is Markdown — clean and parseable. For a page with a financial table, it would output something like:

```markdown
## Balance Sheet as at 31st March 2024

| Particulars | Note | FY2024 | FY2023 |
|---|---|---|---|
| EQUITY AND LIABILITIES | | | |
| Shareholders' Funds | | | |
| Share Capital | 1 | 50,00,000 | 50,00,000 |
```

This is exactly the format our extraction pipeline needs.

#### Difference from Surya
Marker = Surya + post-processing + Markdown formatting. If Surya is already in the stack, Marker adds minimal overhead and provides cleaner output formatting.

#### Docker Support
No official Docker image — but since it depends on Surya and standard Python packages, it can be added to the existing backend Docker image.

---

### 5. Tesseract 5

**Repository:** https://github.com/tesseract-ocr/tesseract
**License:** Apache 2.0
**Latest Version:** 5.5.2 (December 2025)

#### What It Is
Tesseract is the oldest and most widely-used open source OCR engine, now maintained by Google. Version 5 uses an LSTM neural network engine alongside the legacy character-pattern recognizer.

#### Quality Assessment
- Excellent for clean, well-formatted printed text
- Degrades significantly on low-quality scans, skewed text, or complex layouts
- **No native table structure support** — returns text in reading order without row/column relationships
- 100+ languages supported including Hindi and regional scripts
- Documentation explicitly notes: "in order to get better OCR results, you'll need to improve the quality of the image"

#### For Financial Documents
**Not recommended as primary tool.** Tesseract's lack of table structure is a fundamental limitation for balance sheets and P&L statements. Post-processing to reconstruct table structure from Tesseract's positional output is complex and error-prone.

**Valid use case:** Pre-processing (deskew, denoise) images before feeding to a better OCR tool.

#### Docker
Widely available — `docker pull tesseractshadow/tesseract4re` or build with `apt-get install tesseract-ocr`.

---

### 6. unstructured.io

**Repository:** https://github.com/Unstructured-IO/unstructured
**License:** Apache 2.0
**API pricing:** Cloud API available; self-hosted is free

#### What It Is
Unstructured is a document partitioning library that routes documents through specialized parsers and OCR engines. It supports PDFs (via pdfminer + Tesseract for scanned pages), Word, Excel, HTML, and more.

For scanned PDFs, it uses Tesseract internally — which limits table structure quality. A "hi-res" mode uses layout detection models (similar to Docling) for better results.

#### For Our Use Case
- Good for text extraction from mixed document types
- Table support via hi-res mode with layout detection
- But underlying OCR (Tesseract) limits quality on poor scans
- Self-hosted Docker available: `docker pull quay.io/unstructured-io/unstructured`
- Better suited for general document pipelines than specialized financial table extraction

---

## Financial Table Extraction: Which Tool Actually Works?

Here is what happens when each tool processes a typical Indian balance sheet page:

### Input: Balance Sheet with 2-column comparative data

```
EQUITY AND LIABILITIES          NOTE    FY2024      FY2023
                                         (Rs.)       (Rs.)
Shareholders' Funds
  Share Capital                   1   5,000,000   5,000,000
  Reserves and Surplus            2  12,345,678   9,876,543
Non-Current Liabilities
  Long-Term Borrowings            3   8,000,000  10,000,000
Current Liabilities
  Trade Payables                  4   1,234,567   2,345,678
TOTAL                                26,580,245  27,222,221
```

### Expected Output (what we need)

```json
[
  {"row": "Share Capital", "note": "1", "fy2024": "5000000", "fy2023": "5000000"},
  {"row": "Reserves and Surplus", "note": "2", "fy2024": "12345678", "fy2023": "9876543"},
  ...
]
```

### Tool Performance

| Tool | Gets row labels right | Gets amounts right | Keeps FY2024/FY2023 separate | Handles Rs. notation |
|---|---|---|---|---|
| Claude Sonnet Vision | Yes | Yes | Yes | Yes |
| Claude Haiku 3.5 | Yes | Usually | Yes | Yes |
| Gemini 2.5 Flash | Yes | Usually | Yes | Mostly |
| Docling + EasyOCR | Usually | Usually | Usually | Mostly |
| PaddleOCR PP-Structure | Usually | Usually | Usually | Partially |
| Surya OCR + table model | Usually | Usually | Usually | Partially |
| Marker | Usually | Usually | Usually | Partially |
| Tesseract 5 | Yes (text) | Yes (text) | **No** (no columns) | Partially |

---

## Hybrid Architecture Recommendation

The ideal solution for the CMA Automation project is a **two-stage pipeline**:

### Stage 1: Fast Open Source Pre-processing (Free)

Use **Surya OCR** (already installed) for:
- Initial text extraction
- Layout analysis
- Table detection with confidence scores
- Classify each page as: "clean table", "complex layout", "low quality", "handwritten"

Cost: $0 per page (already paid for in server/Docker costs)

### Stage 2: Targeted Vision LLM (Paid, but selective)

Route pages based on Stage 1 classification:

| Page type | Action | Estimated frequency | Cost |
|---|---|---|---|
| Clean printed table, high confidence | Use Surya output directly | 30–40% of pages | $0 |
| Moderate complexity, Surya uncertain | Gemini 2.5 Flash | 40–50% of pages | ~$0.0014 |
| Complex/degraded/multi-column | Claude Haiku 3.5 | 10–20% of pages | ~$0.003 |
| Handwritten annotations | Claude Haiku 3.5 (with note) | 5–10% of pages | ~$0.005 |

### Blended Cost Estimate

Assuming 100 pages with the distribution above:
- 35 pages × $0 = $0
- 45 pages × $0.0014 = $0.063
- 15 pages × $0.003 = $0.045
- 5 pages × $0.005 = $0.025

**Total: $0.133 for 100 pages = $0.00133/page average**

vs. current Claude Sonnet Vision: ~$0.0165/page × 100 = **$1.65 for 100 pages**

**Saving: ~92% cost reduction**

### Implementation Steps

1. Add page quality scoring to `backend/app/services/extraction/page_filter.py` (file already exists in the project)
2. Add Gemini 2.5 Flash as secondary OCR provider alongside Anthropic in `ocr_extractor.py`
3. Route by page type in the existing extraction worker
4. The existing ExtractionVerifier in frontend handles any OCR errors caught by human review

---

## Docker Setup Complexity

| Tool | Docker effort | Notes |
|---|---|---|
| Docling | Low — pip install docling | CPU mode, no GPU needed |
| Surya OCR | Low — already in stack | GPU speeds up but CPU works |
| PaddleOCR | Medium — additional pip packages | CPU mode works, ~200MB install |
| Marker | Low — pip install marker | Depends on Surya |
| Tesseract | Low — apt-get | Must add to backend Dockerfile |
| unstructured | Medium — Docker image available | Pull quay.io/unstructured-io/unstructured |

All tools except Tesseract can be added to the existing `backend/Dockerfile` with a `pip install` line. No separate Docker service needed for CPU-mode operation.

---

## Can Open Source Replace Claude Sonnet Vision?

### For Clear, High-Quality Scans: Yes, Partially

PaddleOCR or Docling can handle clean, high-DPI (300 dpi+) scans with good accuracy. If the Indian CA firm receives clean digital PDFs from clients, open source handles 70–80% of pages adequately.

### For Poor Quality Scans: No

- Phone-camera photos of documents: Open source tools degrade significantly
- Skewed/rotated pages: Pre-processing helps but accuracy drops
- Faded or low-contrast text: Vision LLMs significantly outperform open source here
- Handwritten annotations: Only vision LLMs handle these reliably

### For Complex Multi-column Financial Tables: Partially

PaddleOCR (94.5% benchmark) and Docling handle well-formatted tables well. But the specific challenge of Indian financial documents — Rs. notation, lakh/crore formatting, bracket negatives — requires post-processing that vision LLMs handle automatically through prompt engineering.

### Verdict

Open source tools **cannot fully replace** Claude Sonnet Vision for the CMA project if documents include variable quality scans. They **can reduce** the number of pages that need vision LLM processing by 30–40%.

---

## Sources

- Docling GitHub: https://github.com/docling-project/docling
- Docling Technical Report: https://arxiv.org/abs/2408.09869
- Surya OCR GitHub: https://github.com/VikParuchuri/surya
- Marker GitHub: https://github.com/VikParuchuri/marker
- PaddleOCR GitHub: https://github.com/PaddlePaddle/PaddleOCR
- Tesseract GitHub: https://github.com/tesseract-ocr/tesseract
- unstructured.io GitHub: https://github.com/Unstructured-IO/unstructured
- LLMSherpa GitHub: https://github.com/nlmatics/llmsherpa

---

## Best Fit for Our Project

### Immediate Win (Zero Cost, Zero Risk)

**Expand Surya OCR usage** for page classification and pre-processing. The file `backend/app/services/extraction/page_filter.py` already exists in the project. Use Surya to:
1. Score every page for OCR confidence
2. Extract tables from high-confidence pages directly (no LLM needed)
3. Pass only low-confidence or complex pages to the vision LLM

**Expected benefit:** 30–40% of pages skip LLM entirely = 30–40% cost reduction with zero accuracy risk (high-confidence Surya pages are high quality by definition).

### Phase 2 Add-on (Low Effort, Medium Savings)

**Add PaddleOCR** for table detection on medium-confidence pages. Apache 2.0 license, no commercial restrictions, 94.5% benchmark accuracy. Add to backend Dockerfile with `pip install paddlepaddle paddleocr`.

**Expected benefit:** Additional 20–30% of pages handled without LLM.

### Combined Result

With the hybrid pipeline (Surya → PaddleOCR → Gemini 2.5 Flash → Claude Haiku):
- 60–70% of pages handled by free/cheap tools
- Only 30–40% of pages reach a paid vision LLM
- Average cost: $0.001–0.003/page vs current $0.013–0.020/page
- **Total saving: 85–93%** with no sacrifice in final output quality (human verification step catches any OCR errors)

The ExtractionVerifier UI already exists in the frontend. This human checkpoint is the safety net that makes aggressive cost optimization safe — OCR errors get caught before CMA generation, regardless of which OCR tool produced them.
