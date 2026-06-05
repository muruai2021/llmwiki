"""
Tests for frontmatter read / write / merge.
"""
from __future__ import annotations

from app.services import frontmatter


def test_parse_with_frontmatter():
    text = "---\ntitle: Foo\ntags: [a, b]\n---\n\n# Body\n"
    fm, body, has = frontmatter.parse(text)
    assert has is True
    assert fm["title"] == "Foo"
    assert fm["tags"] == ["a", "b"]
    assert body.strip() == "# Body"


def test_parse_without_frontmatter():
    text = "# Just a heading\nSome body."
    fm, body, has = frontmatter.parse(text)
    assert has is False
    assert fm == {}
    assert body == text


def test_compose_round_trip():
    fm = {"title": "X", "tags": ["a"], "updated": "2026-06-04"}
    body = "# Body\n\nText."
    text = frontmatter.compose(fm, body)
    assert text.startswith("---\n")
    fm2, body2, has2 = frontmatter.parse(text)
    assert has2 is True
    assert fm2 == fm
    assert body2.strip() == body.strip()


def test_merge_update_set_and_delete():
    fm = {"a": 1, "b": 2, "c": 3}
    merged = frontmatter.merge_update(fm, {"b": 20, "c": None, "d": "new"})
    assert merged == {"a": 1, "b": 20, "d": "new"}


def test_compose_preserves_chinese():
    fm = {"title": "三亚市", "tags": ["城市", "招商"]}
    body = "# 三亚市\n\n对比基准：海南\n"
    text = frontmatter.compose(fm, body)
    fm2, body2, _ = frontmatter.parse(text)
    assert fm2["title"] == "三亚市"
    assert "三亚市" in body2
    assert "海南" in body2
