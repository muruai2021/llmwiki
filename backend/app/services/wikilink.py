"""
Wikilink resolution — ported from the project's `.claudian/lint.py` (see
the deployment / vault conventions docs for the source path).

The logic mirrors Obsidian's behavior:
  1. Match `[[target]]` or `[[target|alias]]`
  2. Skip http(s)/anchor targets
  3. Strip .md/.pdf/.html/.docx extensions (each only if present)
  4. Try as absolute path
  5. Try with `wiki/` prefix
  6. Fall back to basename fuzzy match (Obsidian behavior)

For each link in a source file, returns `{target, resolved?, source, original}`.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable

# Match `[[target]]` or `[[target|alias]]`. Excludes \ | ] chars in target.
# (Mirrors lint.py regex exactly.)
WIKILINK_RE = re.compile(r"\[\[([^\\|\]]+)(?:\|[^\]]*)?\]\]")

_EXTS = (".md", ".pdf", ".html", ".docx")


def _strip_ext(s: str) -> str:
    for ext in _EXTS:
        if s.endswith(ext):
            s = s[: -len(ext)]
            break
    return s


def _candidates(target: str) -> list[str]:
    """Return the list of normalized target_keys to try for `target`."""
    t = target.split("#")[0]  # remove anchor
    t = _strip_ext(t)
    if t.startswith(("http://", "https://", "#")):
        return []
    cands = [t]
    if "/" in t:
        # Try with wiki/ prefix
        cands.append("wiki/" + t.lstrip("/"))
    return cands


def build_index(vault_root: Path) -> tuple[dict[str, Path], dict[str, list[str]]]:
    """Build (file_pages, basename_index) once.

    file_pages:  target_key (no ext) → absolute Path
    basename_index:  basename → list of target_keys (sorted shortest first)
    """
    file_pages: dict[str, Path] = {}
    basenames: dict[str, list[str]] = defaultdict(list)

    exts = (".md", ".pdf", ".html", ".docx")
    for p in vault_root.rglob("*"):
        if not p.is_file():
            continue
        # Skip Obsidian / cache dirs
        if any(part in (".obsidian", ".git", ".venv", "__pycache__") for part in p.parts):
            continue
        # Skip .claude entirely (skills are not wiki pages)
        if ".claude" in p.parts:
            continue
        # Skip .claudian entirely
        if ".claudian" in p.parts:
            continue
        if p.suffix.lower() not in exts:
            continue
        rel = p.relative_to(vault_root).as_posix()
        # strip ext
        key = rel
        for ext in exts:
            if key.endswith(ext):
                key = key[: -len(ext)]
                break
        file_pages[key] = p
        basename = key.rsplit("/", 1)[-1]
        basenames[basename].append(key)

    # sort each basename list by path length (shortest first)
    for k in basenames:
        basenames[k].sort(key=len)
    return file_pages, dict(basenames)


def _resolve_target(
    target: str,
    file_pages: dict[str, Path],
    basename_index: dict[str, list[str]],
) -> str | None:
    for cand in _candidates(target):
        if cand in file_pages:
            return cand
    # Basename fuzzy match
    base = target.split("#")[0].rsplit("/", 1)[-1]
    base = _strip_ext(base)
    matches = basename_index.get(base, [])
    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]
    # Multiple — return shortest (Obsidian heuristic)
    return sorted(matches, key=len)[0]


def extract_links(text: str) -> list[str]:
    """Return all raw wikilink targets (not resolved)."""
    return [m.group(1).strip() for m in WIKILINK_RE.finditer(text)]


def resolve_links(
    text: str,
    source_path: str,
    file_pages: dict[str, Path],
    basename_index: dict[str, list[str]],
) -> list[dict]:
    """Resolve every wikilink in `text` and return one record per occurrence.

    Returns: [{source, original, target, resolved, exists}, ...]
    """
    out: list[dict] = []
    for m in WIKILINK_RE.finditer(text):
        original = m.group(1).strip()
        # Skip external/anchor
        if original.startswith(("http://", "https://", "#")):
            continue
        target_norm = original.split("#")[0]
        target_norm = _strip_ext(target_norm)
        resolved = _resolve_target(original, file_pages, basename_index)
        out.append({
            "source": source_path,
            "original": original,
            "target": target_norm,
            "resolved": resolved,
            "exists": bool(resolved and resolved in file_pages),
        })
    return out


def resolve_one(
    link: str,
    file_pages: dict[str, Path],
    basename_index: dict[str, list[str]],
) -> dict:
    """Resolve a single wikilink (used by /api/vault/resolve-wikilink)."""
    if not link:
        return {"link": link, "exists": False, "error": "empty"}
    if link.startswith(("http://", "https://")):
        return {"link": link, "is_external": True, "exists": False}
    resolved = _resolve_target(link, file_pages, basename_index)
    return {
        "link": link,
        "resolved": resolved,
        "exists": bool(resolved and resolved in file_pages),
    }
