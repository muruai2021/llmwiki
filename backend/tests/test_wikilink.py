"""
Tests for wikilink resolution (mirrors lint.py behavior).
"""
from __future__ import annotations

from pathlib import Path

from app.services import wikilink


def test_build_index(tmp_vault: Path):
    fp, bi = wikilink.build_index(tmp_vault)
    assert "wiki/index" in fp
    assert "wiki/三亚市" in fp
    assert "wiki/cities/海口市" in fp
    assert "demo-skill" not in bi  # skills excluded


def test_extract_links():
    text = "See [[三亚市]] and [[cities/海口市|海口]] and [[http://example.com]]."
    links = wikilink.extract_links(text)
    assert "三亚市" in links
    assert "cities/海口市" in links  # alias stripped
    assert "http://example.com" in links


def test_resolve_absolute_path(tmp_vault: Path):
    fp, bi = wikilink.build_index(tmp_vault)
    result = wikilink.resolve_one("wiki/三亚市", fp, bi)
    assert result["exists"] is True
    assert result["resolved"] == "wiki/三亚市"


def test_resolve_strips_md_extension(tmp_vault: Path):
    fp, bi = wikilink.build_index(tmp_vault)
    result = wikilink.resolve_one("三亚市.md", fp, bi)
    assert result["exists"] is True


def test_resolve_basename_fuzzy(tmp_vault: Path):
    fp, bi = wikilink.build_index(tmp_vault)
    result = wikilink.resolve_one("三亚市", fp, bi)
    assert result["exists"] is True
    assert result["resolved"] == "wiki/三亚市"


def test_resolve_with_wiki_prefix(tmp_vault: Path):
    fp, bi = wikilink.build_index(tmp_vault)
    # Use basename only, should still find via basename index
    result = wikilink.resolve_one("海口市", fp, bi)
    # Both "wiki/海口市.md" and "wiki/cities/海口市.md" don't exist — only cities/海口市 does
    # In our tmp_vault, 海口市 lives at wiki/cities/海口市.md, not wiki/海口市.md
    # So basename match should return the cities/ one (shorter wins)
    assert result["exists"] is True


def test_resolve_external_link():
    fp, bi = {}, {}
    result = wikilink.resolve_one("https://example.com", fp, bi)
    assert result.get("is_external") is True
    assert result["exists"] is False


def test_resolve_missing():
    fp, bi = {}, {}
    result = wikilink.resolve_one("nonexistent-page", fp, bi)
    assert result["exists"] is False
