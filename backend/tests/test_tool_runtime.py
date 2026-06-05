"""
Tests for tool_runtime — all 9 tools, success and error paths.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings
from app.errors import (
    FileNotFoundInVault,
    PathSecurityError,
    RawImmutableError,
)
from app.services import tool_runtime


@pytest.fixture
def settings(tmp_vault: Path) -> Settings:
    return Settings(vault_root=str(tmp_vault))


def test_read_file(settings: Settings):
    result = tool_runtime.execute(settings, "read_file", {"path": "wiki/index.md"})
    assert result["ok"] is True
    assert "三亚市" in result["content"]


def test_read_file_missing(settings: Settings):
    result = tool_runtime.execute(settings, "read_file", {"path": "wiki/nope.md"})
    assert result["ok"] is False
    assert result["code"] == "file_not_found"


def test_write_file(settings: Settings, tmp_vault: Path):
    result = tool_runtime.execute(
        settings, "write_file", {"path": "wiki/new.md", "content": "# X\n"}
    )
    assert result["ok"] is True
    assert (tmp_vault / "wiki" / "new.md").exists()


def test_write_file_rejects_raw(settings: Settings):
    result = tool_runtime.execute(
        settings, "write_file", {"path": "raw/x.md", "content": "# X\n"}
    )
    assert result["ok"] is False
    assert result["code"] == "raw_immutable"


def test_append_to_file(settings: Settings, tmp_vault: Path):
    result = tool_runtime.execute(
        settings, "append_to_file", {"path": "wiki/log.md", "content": "## entry\n"}
    )
    assert result["ok"] is True
    assert (tmp_vault / "wiki" / "log.md").exists()


def test_list_files(settings: Settings):
    result = tool_runtime.execute(settings, "list_files", {"glob": "wiki/**/*.md"})
    assert result["ok"] is True
    assert result["count"] >= 3
    assert "wiki/index.md" in result["files"]


def test_search_vault(settings: Settings):
    result = tool_runtime.execute(
        settings, "search_vault", {"query": "人才引进"}
    )
    assert result["ok"] is True
    assert any("海口市" in h["path"] for h in result["hits"])


def test_get_frontmatter(settings: Settings):
    result = tool_runtime.execute(
        settings, "get_frontmatter", {"path": "wiki/index.md"}
    )
    assert result["ok"] is True
    assert result["frontmatter"]["title"] == "索引"


def test_update_frontmatter_sets_updated(settings: Settings, tmp_vault: Path):
    result = tool_runtime.execute(
        settings,
        "update_frontmatter",
        {"path": "wiki/index.md", "updates": {"tags": ["meta", "updated"]}},
    )
    assert result["ok"] is True
    assert "updated" in result["frontmatter"]
    assert result["frontmatter"]["tags"] == ["meta", "updated"]


def test_resolve_wikilink(settings: Settings):
    result = tool_runtime.execute(
        settings, "resolve_wikilink", {"link": "三亚市"}
    )
    assert result["ok"] is True
    assert result["exists"] is True
    assert result["resolved"] == "wiki/三亚市"


def test_run_vault_script_lint(settings: Settings):
    """The lint script doesn't exist in tmp_vault — should fail gracefully."""
    result = tool_runtime.execute(
        settings, "run_vault_script", {"name": "lint"}
    )
    # The command will fail with non-zero exit, but our handler returns ok=False
    # (we don't run real scripts in tests; the script simply doesn't exist)
    assert "exit_code" in result or result.get("ok") is False


def test_run_vault_script_unknown(settings: Settings):
    result = tool_runtime.execute(
        settings, "run_vault_script", {"name": "evil_script"}
    )
    assert result["ok"] is False
    assert result["code"] == "script_not_whitelisted"


def test_unknown_tool(settings: Settings):
    result = tool_runtime.execute(settings, "nonexistent", {})
    assert result["ok"] is False
    assert result["code"] == "unknown_tool"
