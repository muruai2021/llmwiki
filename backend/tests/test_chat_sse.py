"""
End-to-end test of the FastAPI app via TestClient.
Validates: healthz, vault endpoints, chat SSE event format.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# We need to point the app at our tmp_vault BEFORE importing
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def client(tmp_vault: Path, monkeypatch, tmp_path: Path):
    monkeypatch.setenv("LLMWIKI_VAULT_ROOT", str(tmp_vault))
    monkeypatch.setenv("LLMWIKI_LLM_API_KEY", "")  # no explicit key
    # Point the auto-loader at a non-existent file so it can't fill in the
    # user's real ANTHROPIC_AUTH_TOKEN from their Claude Code settings.json.
    fake_settings = tmp_path / "claude-settings.json"
    monkeypatch.setenv("LLMWIKI_CLAUDE_SETTINGS_PATH", str(fake_settings))
    # Force fresh settings
    from app.config import get_settings
    get_settings.cache_clear()
    from app.services.session_store import get_session_store
    get_session_store.cache_clear() if hasattr(get_session_store, "cache_clear") else None
    # Reset module-level singleton
    from app.services import session_store
    session_store._instance = None

    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


def test_healthz(client):
    r = client.get("/api/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "vault_path" in body
    assert body["model"] == "MiniMax-M3"
    assert body["skills_loaded"] >= 1


def test_vault_tree(client):
    r = client.get("/api/vault/tree", params={"path": "", "max_depth": 2})
    assert r.status_code == 200
    body = r.json()
    assert body["root"] == ""
    names = {c["name"] for c in body["tree"]["children"]}
    assert "wiki" in names


def test_vault_file_get(client):
    r = client.get("/api/vault/file", params={"path": "wiki/index.md"})
    assert r.status_code == 200
    body = r.json()
    assert body["has_frontmatter"] is True
    assert body["frontmatter"]["title"] == "索引"


def test_vault_file_get_missing(client):
    r = client.get("/api/vault/file", params={"path": "wiki/nope.md"})
    assert r.status_code == 404


def test_vault_file_put(client, tmp_vault: Path):
    r = client.put(
        "/api/vault/file",
        json={"path": "wiki/created.md", "content": "# Created\n"},
    )
    assert r.status_code == 200
    assert (tmp_vault / "wiki" / "created.md").exists()


def test_vault_file_put_to_raw_rejected(client):
    r = client.put(
        "/api/vault/file",
        json={"path": "raw/x.md", "content": "# X\n"},
    )
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "raw_immutable"


def test_vault_search(client):
    r = client.post(
        "/api/vault/search",
        json={"query": "人才引进", "glob": "**/*.md"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 1


def test_vault_resolve_wikilink(client):
    r = client.post(
        "/api/vault/resolve-wikilink",
        json={"link": "三亚市"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["resolved"]["exists"] is True


def test_skills_list(client):
    r = client.get("/api/skills")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 1
    assert any(s["name"] == "demo-skill" for s in body["skills"])


def test_sessions_list_empty(client):
    r = client.get("/api/sessions")
    assert r.status_code == 200
    assert r.json()["count"] == 0


def test_sessions_create_and_list(client):
    r = client.post("/api/sessions", params={"title": "test"})
    assert r.status_code == 200
    sid = r.json()["id"]
    assert r.json()["title"] == "test"

    r2 = client.get("/api/sessions")
    assert r2.status_code == 200
    assert r2.json()["count"] == 1

    r3 = client.delete(f"/api/sessions/{sid}")
    assert r3.status_code == 200
    assert r3.json()["ok"] is True


def test_chat_stream_no_api_key(client):
    """Without an API key, /api/chat/stream should emit an error event."""
    with client.stream(
        "POST",
        "/api/chat/stream",
        json={"message": "hi"},
    ) as r:
        assert r.status_code == 200
        events = list(r.iter_lines())
    # The stream should contain a message_start and an error
    text = "\n".join(events)
    assert "event: message_start" in text
    assert "event: error" in text
