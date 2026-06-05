#!/usr/bin/env bash
# End-to-end smoke test of a deployed LLMwiki instance.
# Usage:
#   LLMWIKI_URL=https://llmwiki.example.com ./scripts/e2e-smoke.sh
# or for local dev:
#   ./scripts/e2e-smoke.sh   (defaults to http://127.0.0.1:8000)
set -euo pipefail

URL="${LLMWIKI_URL:-http://127.0.0.1:8000}"

echo "→ Testing: $URL"
echo ""

# 1. Health check
echo "1. /api/healthz"
HEALTH=$(curl -sf "$URL/api/healthz" || echo "FAIL")
echo "$HEALTH" | head -c 200
echo ""
if [[ "$HEALTH" == "FAIL" ]]; then
  echo "✗ Health check failed"
  exit 1
fi
echo "✓ OK"
echo ""

# 2. Skills list
echo "2. /api/skills"
curl -sf "$URL/api/skills" | head -c 200
echo ""
echo "✓ OK"
echo ""

# 3. Vault tree (top-level)
echo "3. /api/vault/tree?path=&max_depth=1"
curl -sf "$URL/api/vault/tree?path=&max_depth=1" | head -c 200
echo ""
echo "✓ OK"
echo ""

# 4. Search
echo "4. /api/vault/search (query: 招商)"
curl -sf -X POST "$URL/api/vault/search" \
  -H "Content-Type: application/json" \
  -d '{"query":"招商","max_results":5}' | head -c 200
echo ""
echo "✓ OK"
echo ""

# 5. Chat SSE (smoke)
echo "5. /api/chat/stream (smoke — first 10 events)"
if [ -f "backend/scripts/smoke_chat.py" ]; then
  python backend/scripts/smoke_chat.py "ping" 2>&1 | head -50
else
  echo "(skipped — backend/scripts/smoke_chat.py not found)"
fi

echo ""
echo "✓ All checks passed."
