"""
Tests for vault_fs: path safety, read/write, tree, glob.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.errors import (
    FileNotFoundInVault,
    PathSecurityError,
    RawImmutableError,
)
from app.services import vault_fs


class TestPathSecurity:
    def test_resolve_normal_path(self, tmp_vault: Path):
        p = vault_fs.resolve(tmp_vault, "wiki/index.md")
        assert p == (tmp_vault / "wiki" / "index.md").resolve()

    def test_resolve_rejects_parent_escape(self, tmp_vault: Path):
        with pytest.raises(PathSecurityError):
            vault_fs.resolve(tmp_vault, "../etc/passwd")

    def test_resolve_rejects_double_parent(self, tmp_vault: Path):
        with pytest.raises(PathSecurityError):
            vault_fs.resolve(tmp_vault, "wiki/../../outside")

    def test_resolve_empty_means_root(self, tmp_vault: Path):
        # Empty / "." / "/" all resolve to the vault root — used by list_tree / glob_files.
        p_empty = vault_fs.resolve(tmp_vault, "")
        p_dot = vault_fs.resolve(tmp_vault, ".")
        p_slash = vault_fs.resolve(tmp_vault, "/")
        expected = tmp_vault.resolve()
        assert p_empty == expected
        assert p_dot == expected
        assert p_slash == expected

    def test_resolve_rejects_none(self, tmp_vault: Path):
        # None is the only "empty" input that is rejected as a programming error.
        with pytest.raises(PathSecurityError):
            vault_fs.resolve(tmp_vault, None)  # type: ignore[arg-type]


class TestReadWrite:
    def test_read_existing_file(self, tmp_vault: Path):
        text = vault_fs.read_text(tmp_vault, "wiki/index.md")
        assert "三亚市" in text

    def test_read_missing_file_raises(self, tmp_vault: Path):
        with pytest.raises(FileNotFoundInVault):
            vault_fs.read_text(tmp_vault, "wiki/nonexistent.md")

    def test_write_creates_file(self, tmp_vault: Path):
        result = vault_fs.write_text(tmp_vault, "wiki/new.md", "# New\n")
        assert result["bytes_written"] > 0
        assert (tmp_vault / "wiki" / "new.md").exists()

    def test_write_creates_parents(self, tmp_vault: Path):
        result = vault_fs.write_text(
            tmp_vault, "wiki/deep/nested/file.md", "# X\n", create_parents=True
        )
        assert result["created_parents"] is True
        assert (tmp_vault / "wiki" / "deep" / "nested" / "file.md").exists()

    def test_write_to_raw_rejected(self, tmp_vault: Path):
        with pytest.raises(RawImmutableError):
            vault_fs.write_text(tmp_vault, "raw/original.md", "# X\n")

    def test_write_to_obsidian_rejected(self, tmp_vault: Path):
        with pytest.raises(PathSecurityError):
            vault_fs.write_text(tmp_vault, ".obsidian/config.json", "{}")

    def test_write_to_claude_rejected(self, tmp_vault: Path):
        with pytest.raises(PathSecurityError):
            vault_fs.write_text(tmp_vault, ".claude/skills/foo/SKILL.md", "# X\n")

    def test_write_to_claudian_rejected(self, tmp_vault: Path):
        """`.claudian/` holds conversation session dumps (potentially MBs of
        chat history). It must be locked from writes just like raw/ and
        .claude/ — if a future change drops it from _FORBIDDEN_DIRS, this
        test catches it.
        """
        with pytest.raises(PathSecurityError):
            vault_fs.write_text(tmp_vault, ".claudian/sessions/foo.json", "{}")

    def test_append_creates_if_missing(self, tmp_vault: Path):
        result = vault_fs.append_text(tmp_vault, "wiki/log.md", "## entry\n")
        assert result["existed_before"] is False
        assert (tmp_vault / "wiki" / "log.md").exists()


class TestTree:
    def test_list_tree_root(self, tmp_vault: Path):
        tree = vault_fs.list_tree(tmp_vault, "", max_depth=3)
        assert tree["type"] == "dir"
        names = {c["name"] for c in tree["children"]}
        assert "wiki" in names
        assert "raw" in names

    def test_list_tree_subdir(self, tmp_vault: Path):
        tree = vault_fs.list_tree(tmp_vault, "wiki", max_depth=2)
        assert tree["type"] == "dir"
        names = {c["name"] for c in tree.get("children", [])}
        assert "index.md" in names

    def test_glob_files(self, tmp_vault: Path):
        files = vault_fs.glob_files(tmp_vault, "wiki/**/*.md")
        paths = " ".join(files)
        assert "wiki/index.md" in paths
        assert "wiki/三亚市.md" in paths

    def test_list_tree_excludes_claudian(self, tmp_vault: Path):
        """`.claudian/sessions/` can hold multi-MB chat history files; the
        tree API must skip the whole dir so the front-end doesn't render
        — and more importantly the back-end doesn't stat every file in it.
        """
        # Plant a session file the bug would have exposed
        (tmp_vault / ".claudian" / "sessions").mkdir(parents=True, exist_ok=True)
        (tmp_vault / ".claudian" / "sessions" / "big.json").write_text("x" * 10_000, encoding="utf-8")
        tree = vault_fs.list_tree(tmp_vault, "", max_depth=5)
        names = {c["name"] for c in tree["children"]}
        assert ".claudian" not in names
        assert "wiki" in names

    def test_glob_excludes_claudian(self, tmp_vault: Path):
        (tmp_vault / ".claudian" / "sessions").mkdir(parents=True, exist_ok=True)
        (tmp_vault / ".claudian" / "sessions" / "x.json").write_text("{}", encoding="utf-8")
        files = vault_fs.glob_files(tmp_vault, "**/*.json")
        assert not any("x.json" in p for p in files)
