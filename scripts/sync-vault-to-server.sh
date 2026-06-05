#!/usr/bin/env bash
# Sync the local vault to the server.
# Defaults: rsync over SSH. Customize with env vars.
#
#   LLMWIKI_VAULT_PATH — local vault path (default: E:/Obsidian/政策 on Windows)
#   LLMWIKI_SERVER_HOST — required (e.g. user@1.2.3.4)
#   LLMWIKI_SERVER_VAULT — server vault path (default: /www/vault/政策)
#   LLMWIKI_SSH_PORT — SSH port (default 22)
#
# Usage:
#   LLMWIKI_SERVER_HOST=user@1.2.3.4 ./scripts/sync-vault-to-server.sh

set -euo pipefail

VAULT_PATH="${LLMWIKI_VAULT_PATH:-E:/Obsidian/政策}"
SERVER_HOST="${LLMWIKI_SERVER_HOST:-}"
SERVER_VAULT="${LLMWIKI_SERVER_VAULT:-/www/vault/政策}"
SSH_PORT="${LLMWIKI_SSH_PORT:-22}"

if [ -z "$SERVER_HOST" ]; then
  echo "✗ LLMWIKI_SERVER_HOST not set. Example: user@1.2.3.4"
  exit 1
fi

# Convert Windows path to rsync-friendly POSIX if needed
SRC="$VAULT_PATH"
if command -v cygpath >/dev/null 2>&1; then
  SRC="$(cygpath -u "$VAULT_PATH")"
fi

echo "→ Source:      $SRC"
echo "→ Destination: $SERVER_HOST:$SERVER_VAULT"
echo ""

# Sync with rsync (use --delete to mirror; comment out to keep server-only files)
rsync -avz --delete \
  --exclude '.obsidian/workspace.json' \
  --exclude '.obsidian/workspace-mobile.json' \
  --exclude '.trash/' \
  --exclude '*.tmp' \
  -e "ssh -p $SSH_PORT" \
  "$SRC/" "$SERVER_HOST:$SERVER_VAULT/"

echo ""
echo "✓ Vault synced."
echo "  Restart the backend on server to pick up new skills:"
echo "    ssh $SERVER_HOST 'sudo systemctl restart llmwiki-backend'"
