#!/usr/bin/env bash
# Pull the GLM-OCR model into the Ollama container.
# Run once after first `docker compose up`.
set -euo pipefail

echo "Pulling glm-ocr model into Ollama container..."
docker compose exec ollama ollama pull glm-ocr
echo "Done. Model ready at http://localhost:11434"
