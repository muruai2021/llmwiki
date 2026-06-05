"""
YAML frontmatter read / write using ruamel.yaml (preserves comments & order).

Format expected at top of .md files:
    ---
    key: value
    list:
      - a
      - b
    ---

    # body markdown...
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from ..errors import FrontmatterError

_yaml = YAML(typ="rt")  # round-trip mode: preserves comments / order
_yaml.preserve_quotes = True
_yaml.indent(mapping=2, sequence=4, offset=2)
_yaml.width = 4096

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def parse(text: str) -> tuple[dict, str, bool]:
    """Split a markdown document into (frontmatter_dict, body, has_frontmatter).

    The body always starts with a single leading newline (or is empty).
    Missing frontmatter → ({}, original_text, False).
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text, False
    raw_yaml = m.group(1)
    body = text[m.end():]
    try:
        data = _yaml.load(raw_yaml)
        if data is None:
            data = {}
        if not isinstance(data, dict):
            data = {"_raw": data}
    except Exception as e:
        raise FrontmatterError(
            f"Failed to parse YAML frontmatter: {e}",
            details={"raw_yaml": raw_yaml[:200]},
        ) from e
    return _to_plain(data), body, True


def _to_plain(obj: Any) -> Any:
    """Recursively convert ruamel containers to plain dict/list for JSON safety."""
    if isinstance(obj, CommentedMap):
        return {k: _to_plain(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_plain(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _to_plain(v) for k, v in obj.items()}
    return obj


def to_plain(obj: Any) -> Any:
    return _to_plain(obj)


def dump(frontmatter: dict) -> str:
    """Serialize a frontmatter dict back to YAML text (without --- fences)."""
    buf = io.StringIO()
    _yaml.dump(_to_comment(frontmatter), buf)
    return buf.getvalue()


def _to_comment(obj: Any) -> Any:
    """Convert plain dict/list back to ruamel CommentedMap (preserves order)."""
    if isinstance(obj, dict):
        cm = CommentedMap()
        for k, v in obj.items():
            cm[k] = _to_comment(v)
        return cm
    if isinstance(obj, list):
        return [_to_comment(v) for v in obj]
    return obj


def compose(frontmatter: dict, body: str) -> str:
    """Reassemble frontmatter + body into a full document.

    - Adds `---` fences around the YAML.
    - Ensures exactly one blank line between fences and body.
    - Body leading newline is normalized.
    """
    yaml_text = dump(frontmatter)
    # Ensure body starts with exactly one newline (after the blank line)
    body = body.lstrip("\n")
    return f"---\n{yaml_text}---\n\n{body}" if body else f"---\n{yaml_text}---\n"


def merge_update(existing: dict, updates: dict) -> dict:
    """Merge updates into existing (shallow). Returns a new dict.

    Keys with value `None` are removed (so the LLM can clear a field by passing null).
    """
    result = dict(existing)
    for k, v in updates.items():
        if v is None:
            result.pop(k, None)
        else:
            result[k] = v
    return result


def read_file(path: Path) -> tuple[dict, str, bool]:
    """Convenience: read a file from disk and parse its frontmatter."""
    text = path.read_text(encoding="utf-8")
    return parse(text)


def write_file(
    path: Path,
    frontmatter: dict,
    body: str,
    *,
    encoding: str = "utf-8",
) -> None:
    """Write a file with frontmatter to disk."""
    path.write_text(compose(frontmatter, body), encoding=encoding)
