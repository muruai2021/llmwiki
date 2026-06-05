#!/usr/bin/env bash
# Start the LLMwiki frontend dev server (Vite).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$ROOT_DIR/frontend"

cd "$FRONTEND_DIR"

if [ ! -d node_modules ]; then
  echo "ℹ️  node_modules missing, running npm install..."
  npm install
fi

exec npm run dev
