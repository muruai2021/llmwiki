#!/usr/bin/env bash
# Start the LLMwiki backend in dev mode (auto-reload).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$ROOT_DIR/backend"

cd "$BACKEND_DIR"

# Activate venv if it exists
if [ -d ".venv" ]; then
  # shellcheck disable=SC1091
  source .venv/Scripts/activate || source .venv/bin/activate
else
  echo "⚠️  No .venv found. Run: cd backend && python -m venv .venv && pip install -r requirements.txt"
  exit 1
fi

# Create .env from example if missing
if [ ! -f .env ]; then
  cp .env.example .env
  echo "ℹ️  Created .env from .env.example (LLMWIKI_LLM_API_KEY left blank; will auto-load from settings.json)"
fi

# Run uvicorn with reload
exec uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
