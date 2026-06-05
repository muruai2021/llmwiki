"""
Pytest fixtures: a temporary vault on disk for tests.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pytest

# Make `app` importable when running pytest from /backend
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def tmp_vault(tmp_path: Path) -> Path:
    """Create a fresh vault tree in tmp_path."""
    vault = tmp_path / "vault"
    (vault / "wiki").mkdir(parents=True)
    (vault / "raw").mkdir(parents=True)
    (vault / "concepts").mkdir(parents=True)
    (vault / ".claude" / "skills").mkdir(parents=True)
    (vault / ".claudian").mkdir(parents=True)
    # CLAUDE.md
    (vault / "CLAUDE.md").write_text(
        "# Test Vault\n\nUse 中文. 对比基准 = 海南.\n", encoding="utf-8"
    )
    # MEMORY.md
    (vault / "MEMORY.md").write_text("# Memory\n", encoding="utf-8")
    # Sample wiki page
    (vault / "wiki" / "index.md").write_text(
        "---\ntitle: 索引\nupdated: 2026-01-01\ntags: [meta]\n---\n\n# 索引\n\n- [[三亚市]]\n- [[海口市]]\n",
        encoding="utf-8",
    )
    (vault / "wiki" / "三亚市.md").write_text(
        "---\ntitle: 三亚市\nupdated: 2026-01-01\ntags: [城市, 招商]\n---\n\n# 三亚市\n\n- 对比基准：海南\n",
        encoding="utf-8",
    )
    (vault / "wiki" / "cities").mkdir()
    (vault / "wiki" / "cities" / "海口市.md").write_text(
        "---\ntitle: 海口市\nupdated: 2026-01-02\ntags: [城市, 招商]\n---\n\n# 海口市\n\n- 人才引进政策\n",
        encoding="utf-8",
    )
    # Skill
    skill_dir = vault / ".claude" / "skills" / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\ndescription: 示例 skill — 用来测试 skills 扫描\n---\n\n# Demo Skill\n\n这是测试用 skill。\n",
        encoding="utf-8",
    )
    return vault
