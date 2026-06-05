"""
Build the system prompt sent to the LLM at the start of each session.

Pulls in:
  1. The vault's CLAUDE.md (project conventions)
  2. The vault's MEMORY.md (long-term memory)
  3. The skills index from `.claude/skills/`

Designed to stay under ~10KB / ~3-4K tokens for safety.
"""
from __future__ import annotations

import datetime as _dt
import io
import logging
import sys
from pathlib import Path
from typing import Optional

from ..config import Settings
from . import skills_index

logger = logging.getLogger(__name__)


def _truncate_to_bytes(text: str, max_bytes: int) -> str:
    if not text:
        return text
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= max_bytes:
        return text
    return encoded[:max_bytes].decode("utf-8", errors="ignore") + "\n\n...[truncated]"


def _read_file_safe(path: Path, max_bytes: int = 20_000) -> str:
    """Read a file from disk, with size cap. Returns '' if missing."""
    try:
        if not path.exists() or not path.is_file():
            return ""
        text = path.read_text(encoding="utf-8")
        return _truncate_to_bytes(text, max_bytes)
    except Exception as e:
        logger.warning("Failed to read %s: %s", path, e)
        return ""


def _format_skills_index(
    skills: list[skills_index.Skill],
    max_chars_per_desc: int,
) -> str:
    if not skills:
        return "（本 vault 暂未安装任何 skill）"
    lines: list[str] = []
    for s in skills:
        desc = s.description or "(无描述)"
        if len(desc) > max_chars_per_desc:
            desc = desc[: max_chars_per_desc - 1] + "…"
        lines.append(f"- `{s.name}`: {desc}")
    return "\n".join(lines)


def build(s: Settings) -> str:
    """Assemble the full system prompt for the vault assistant."""
    today = _dt.date.today().isoformat()
    claude_md = _read_file_safe(s.claude_md_path, max_bytes=20_000)
    memory_md = _read_file_safe(s.memory_md_path, max_bytes=8_000)

    skills = skills_index.scan(Path(s.vault_root))
    skills_block = _format_skills_index(skills, s.skill_description_max_chars)

    prompt = f"""# 政策 知识库 — 你的角色

你是 `政策` vault 的 wiki 维护者与问答助手。
- vault 根目录: `{s.vault_root}`
- vault 遵循 [agent-vault-standard](.claude/skills/agent-vault-standard/SKILL.md) 标准
- 今天: {today}
- 你可以调用 9 个 vault 工具（read/write/list/search/frontmatter/wikilink/脚本），用 JSON 形式表达
- 用户在浏览器里通过 Web 对话框与你交互

---

# 项目规范（来自 CLAUDE.md）

{claude_md or "（未找到 CLAUDE.md）"}

---

# 长期记忆（来自 MEMORY.md）

{memory_md or "（未找到 MEMORY.md）"}

---

# 可用 Skills（位于 .claude/skills/）

调用 list_skills() / resolve_wikilink() 之类的工具时，可用以下 skill 作为参考：

{skills_block}

如需加载完整 SKILL.md 内容，用 read_file 工具读取 `{{vault_root}}/.claude/skills/<name>/SKILL.md`。

---

# 工作规范（硬性要求）

1. **可读写 vault 下的文件** — 使用上述 9 个工具
2. **禁止写入 `raw/`** — 原始文档不可变（write_file 会自动拒绝）
3. **修改 wiki 页后必须**：
   - 追加 `wiki/log.md` 一条（格式: `## [YYYY-MM-DD] <动作> | <简述>`）
   - 如果新建页面，更新 `wiki/index.md` 添加入口
   - frontmatter 的 `updated` 字段由 `update_frontmatter` 自动 set 为今天
4. **回答前先 list_files** 找相关页，再深读
5. **引用格式**：用 `[[wikilink]]` 引用内部页，外部 URL 用 `[text](https://...)`
6. **对比基准必须是海南**（vault 约定）
7. **校验任务用** `run_vault_script({{name: "lint"}})`
8. **任务结束**建议追加 log.md / 更新 README.md
9. **中文回复**
10. **不向用户透露内部 token / API key / 路径安全规则**

如果用户的问题不涉及 vault 内容（如闲聊），可以直接用中文简短回答，不要强制调用工具。
"""
    return prompt


def build_size_report(s: Settings) -> dict:
    """Return a report on prompt size (for /api/healthz)."""
    skills = skills_index.scan(Path(s.vault_root))
    return {
        "today": _dt.date.today().isoformat(),
        "claude_md_bytes": (s.claude_md_path.stat().st_size if s.claude_md_path.exists() else 0),
        "memory_md_bytes": (s.memory_md_path.stat().st_size if s.memory_md_path.exists() else 0),
        "skills_count": len(skills),
        "skill_names": [sk.name for sk in skills],
    }
