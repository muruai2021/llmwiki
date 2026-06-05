#!/usr/bin/env bash
# Build the LLMwiki frontend for production.
# Output: frontend/dist/
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$ROOT_DIR/frontend"

cd "$FRONTEND_DIR"

if [ ! -d node_modules ]; then
  npm install
fi

npm run build
echo ""
echo "✓ Frontend built. Output: $FRONTEND_DIR/dist/"
echo "  Upload to server: scp -r dist/* user@server:/www/wwwroot/llmwiki/dist/"
