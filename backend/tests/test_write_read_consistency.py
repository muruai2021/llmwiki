"""
Tests for the write-then-read consistency we lost before fixing H1+H2.

Before: frontend cached GET /api/vault/file for 5 min. After a write the
user would still see the old size / content until the TTL expired.

This test exercises the BACKEND end-to-end (write → immediate read returns
new content). It guards the invariant that needs to hold for the frontend
fix to be useful — the server has no per-key cache of its own, so a write
followed by a GET is always fresh here. We pin that down so a future "let's
add server-side caching" change doesn't silently re-introduce the bug.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client(tmp_vault: Path):
    # Point settings at the temp vault BEFORE the app boots
    get_settings.cache_clear()
    import os
    os.environ["LLMWIKI_VAULT_ROOT"] = str(tmp_vault)
    os.environ.setdefault("LLMWIKI_LLM_API_KEY", "test-key-not-real")
    get_settings.cache_clear()  # re-read env
    return TestClient(app)


def test_write_then_read_returns_new_content(client: TestClient, tmp_vault: Path):
    """End-to-end: PUT /api/vault/file then GET /api/vault/file returns the
    fresh body. Pre-H2 this could fail on the frontend (5 min cache) but
    also on the backend if anyone added response caching."""
    target = "wiki/scratch.md"
    # First write
    r1 = client.put(
        "/api/vault/file",
        json={"path": target, "content": "first version\n", "create_parents": False},
    )
    assert r1.status_code == 200, r1.text

    # Immediate read
    r2 = client.get("/api/vault/file", params={"path": target})
    assert r2.status_code == 200, r2.text
    body = r2.json()
    assert "first version" in (body.get("raw") or "")

    # Overwrite
    r3 = client.put(
        "/api/vault/file",
        json={"path": target, "content": "second version — much newer\n", "create_parents": False},
    )
    assert r3.status_code == 200, r3.text

    # Read again — must reflect the new version
    r4 = client.get("/api/vault/file", params={"path": target})
    assert r4.status_code == 200, r4.text
    body = r4.json()
    assert "second version" in (body.get("raw") or ""), (
        f"write-then-read returned stale content: {body.get('raw')[:80]!r}"
    )


def test_append_then_read_returns_combined_content(client: TestClient, tmp_vault: Path):
    """Same invariant for append_to_file."""
    target = "wiki/log.md"
    client.put(
        "/api/vault/file",
        json={"path": target, "content": "# Log\n\n", "create_parents": True},
    )
    client.post(
        "/api/vault/append",
        json={"path": target, "content": "- entry one\n", "ensure_trailing_newline": True},
    )
    r = client.get("/api/vault/file", params={"path": target})
    assert r.status_code == 200
    raw = r.json().get("raw") or ""
    assert "entry one" in raw
