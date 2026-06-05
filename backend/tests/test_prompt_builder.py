"""
Tests for the system prompt builder.
"""
from __future__ import annotations

from pathlib import Path

from app.config import Settings
from app.services import prompt_builder


def test_prompt_contains_claude_md(tmp_vault: Path):
    s = Settings(vault_root=str(tmp_vault))
    prompt = prompt_builder.build(s)
    assert "测试 Vault" in prompt or "Test Vault" in prompt
    assert "对比基准" in prompt
    assert "海南" in prompt


def test_prompt_lists_skills(tmp_vault: Path):
    s = Settings(vault_root=str(tmp_vault))
    prompt = prompt_builder.build(s)
    assert "demo-skill" in prompt


def test_prompt_size_report(tmp_vault: Path):
    s = Settings(vault_root=str(tmp_vault))
    report = prompt_builder.build_size_report(s)
    assert report["skills_count"] == 1
    assert "demo-skill" in report["skill_names"]
    assert report["claude_md_bytes"] > 0


def test_prompt_stays_under_token_budget(tmp_vault: Path):
    s = Settings(vault_root=str(tmp_vault))
    prompt = prompt_builder.build(s)
    # Rough: 1 token ≈ 4 chars (English) or 1.5 chars (Chinese)
    # Just sanity-check it's not megabytes
    assert len(prompt) < 50_000, f"Prompt too long: {len(prompt)} bytes"
