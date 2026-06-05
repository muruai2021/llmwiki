"""
Vault-wide text search — simple substring + frontmatter tag filter.

Phase 1: literal substring (case-insensitive by default).
Phase 2: swap to whoosh or ripgrep wrapper.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from . import vault_fs


def search(
    vault_root: Path,
    query: str,
    *,
    glob: str = "**/*.md",
    case_sensitive: bool = False,
    max_results: int = 100,
    context_chars: int = 120,
) -> list[dict]:
    """Search the vault for `query`. Returns list of match records.

    Each record: {path, line, snippet, score}
    """
    if not query or not query.strip():
        return []

    flags = 0 if case_sensitive else re.IGNORECASE
    # Escape query for literal substring (regex-safe)
    pattern = re.escape(query)
    rx = re.compile(pattern, flags)

    files = vault_fs.glob_files(vault_root, glob, max_results=10_000)
    results: list[dict] = []
    for rel in files:
        try:
            text = vault_fs.read_text(vault_root, rel)
        except Exception:
            continue
        for m in rx.finditer(text):
            start, end = m.span()
            # Compute a window around the match
            window_start = max(0, start - context_chars // 2)
            window_end = min(len(text), end + context_chars // 2)
            snippet = text[window_start:window_end].replace("\n", " ")
            if window_start > 0:
                snippet = "…" + snippet
            if window_end < len(text):
                snippet = snippet + "…"
            # line number
            line = text.count("\n", 0, start) + 1
            results.append({
                "path": rel,
                "line": line,
                "snippet": snippet,
                "match_start": start - window_start,
                "match_end": end - window_start,
            })
            if len(results) >= max_results:
                return results
    return results


def search_by_tag(
    vault_root: Path,
    tag: str,
    *,
    glob: str = "**/*.md",
) -> list[str]:
    """Return all .md paths whose frontmatter `tags` list contains `tag`."""
    from . import frontmatter

    tag_norm = tag.lstrip("#").strip()
    if not tag_norm:
        return []
    files = vault_fs.glob_files(vault_root, glob, max_results=10_000)
    out: list[str] = []
    for rel in files:
        try:
            text = vault_fs.read_text(vault_root, rel)
            fm, _, has_fm = frontmatter.parse(text)
        except Exception:
            continue
        if not has_fm:
            continue
        tags = fm.get("tags") or []
        if not isinstance(tags, list):
            continue
        if any(str(t).lstrip("#").strip() == tag_norm for t in tags):
            out.append(rel)
    return out
