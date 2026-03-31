#!/bin/bash
# AutoResearch Verify Script — outputs a single number: total passing pytest tests
# Usage: bash scripts/e2e_eval.sh
# Runs inside Docker. Requires: docker compose up -d

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# Check Docker is running
if ! docker compose ps --status running 2>/dev/null | grep -q backend; then
    echo "0"
    exit 0
fi

# Run pytest, capture output
RESULT=$(docker compose exec -T backend pytest --tb=no -q 2>&1 || true)

# Extract passed count
PASSED=$(echo "$RESULT" | grep -oP '\d+(?= passed)' | head -1)

# Output just the number (AutoResearch reads this)
echo "${PASSED:-0}"
