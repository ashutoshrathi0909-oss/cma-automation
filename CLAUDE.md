# CMA Automation System

## Project Overview
Web application that automates CMA (Credit Monitoring Arrangement) document preparation for Indian CA firms. Extracts financial data from uploaded documents, classifies line items into CMA fields using a 3-tier pipeline (fuzzy match → AI → doubt report), and generates the final CMA Excel file.

## Tech Stack
- **Backend:** Python FastAPI + Supabase + ARQ (Redis task queue)
- **Frontend:** Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui
- **Database:** PostgreSQL via Supabase (Auth + Storage + RLS)
- **AI:** Claude Haiku (classification), surya-ocr (scanned PDFs)
- **Containerization:** Docker Compose (backend + frontend + redis)

## Development Commands
```bash
# Start all services
docker compose up

# Backend only
docker compose up backend

# Frontend only
docker compose up frontend

# Run backend tests
docker compose exec backend pytest

# Run frontend tests
docker compose exec frontend npm test
```

## V1 Scope — STRICT
- Historical data extraction + CMA filling ONLY
- NO projections of any kind
- NO Details Sheet interaction
- Fills INPUT SHEET + TL Sheet only — Excel macros handle everything else

## Critical Constraints
1. Verification step is MANDATORY between extraction and classification
2. CMA Excel must preserve macros (keep_vba=True, save as .xlsm)
3. Classification uses 3-tier pipeline (fuzzy → Haiku → doubt report)
4. learned_mappings checked BEFORE reference_mappings
5. Doubt items ALWAYS flagged — NEVER silent guessing
6. All actions audit-logged to cma_report_history
7. 80%+ test coverage (100% for classification + Excel generation)

## ECC Workflow
Every phase follows: /plan → /tdd → /verify → /code-review → /checkpoint
See `.claude/plan/cma-automation-v1.md` for the full implementation plan.

## Key Reference Files
- `DOCS/CMA classification.xls` — 384 item reference mapping
- `DOCS/CMA.xlsm` — CMA Excel template with macros
- `prompt/prompt-for-multi-plan.md` — Full 1389-line specification
