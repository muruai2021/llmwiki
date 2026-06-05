"""
Scan `.claude/skills/<name>/SKILL.md` and build an in-memory index.

Each skill has:
    name        (str)         — directory name
    description (str)         — first non-heading paragraph of SKILL.md (truncated)
    body        (str)         — full SKILL.md content
    path        (str)         — vault-relative path to SKILL.md
    size        (int)         — file size in bytes
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from . import vault_fs


@dataclass
class Skill:
    name: str
    description: str
    body: str
    path: str
    size: int = 0
    # Optional frontmatter (yaml at top of SKILL.md)
    frontmatter: dict = field(default_factory=dict)


def _first_paragraph(body: str, max_chars: int = 200) -> str:
    """Return the first non-empty, non-heading paragraph of the markdown body."""
    lines = body.splitlines()
    buf: list[str] = []
    for line in lines:
        s = line.strip()
        if not s:
            if buf:
                break
            continue
        if s.startswith("#"):
            continue
        if s.startswith("```"):
            continue
        if s.startswith(">"):
            continue
        buf.append(s)
        if sum(len(x) for x in buf) > max_chars * 2:
            break
    text = " ".join(buf)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_chars:
        text = text[: max_chars - 1] + "…"
    return text


def _parse_skill_md(text: str) -> tuple[dict, str]:
    """Try to parse optional YAML frontmatter from SKILL.md."""
    try:
        from . import frontmatter
        fm, body, has = frontmatter.parse(text)
        return (fm if has else {}), body
    except Exception:
        return {}, text


def scan(vault_root: Path) -> list[Skill]:
    """Scan `<vault>/.claude/skills/*/SKILL.md` and return a list of Skills."""
    skills_dir = vault_root / ".claude" / "skills"
    if not skills_dir.is_dir():
        return []
    out: list[Skill] = []
    for child in sorted(skills_dir.iterdir()):
        if not child.is_dir():
            continue
        skill_md = child / "SKILL.md"
        if not skill_md.is_file():
            continue
        try:
            text = skill_md.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = skill_md.read_text(encoding="gbk", errors="ignore")
        fm, body = _parse_skill_md(text)
        description = (
            fm.get("description")
            or _first_paragraph(body)
        )
        out.append(
            Skill(
                name=child.name,
                description=description,
                body=text,
                path=f".claude/skills/{child.name}/SKILL.md",
                size=skill_md.stat().st_size,
                frontmatter=fm,
            )
        )
    return out


def get_by_name(skills: list[Skill], name: str) -> Skill | None:
    for s in skills:
        if s.name == name:
            return s
    return None


def to_index_dicts(skills: list[Skill], *, max_chars: int = 100) -> list[dict]:
    """Lightweight dicts for /api/skills (no body)."""
    out: list[dict] = []
    for s in skills:
        desc = s.description or ""
        if len(desc) > max_chars:
            desc = desc[: max_chars - 1] + "…"
        out.append({
            "name": s.name,
            "description": desc,
            "path": s.path,
            "size": s.size,
        })
    return out
