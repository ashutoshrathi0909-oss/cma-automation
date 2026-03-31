#!/bin/bash
# AutoResearch Guard Script — checks app health (exit 0 = pass, exit 1 = fail)
# Usage: bash scripts/e2e_guard.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# Check backend health endpoint
HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo "GUARD_PASS: Backend healthy"
    exit 0
else
    echo "GUARD_FAIL: Backend unreachable (HTTP $HTTP_CODE)"
    exit 1
fi
