"""
Execute tool calls against the vault.

Receives `{name, id, input}` from the LLM, dispatches to the right service,
returns a `{ok, result/error}` envelope. All results are pre-truncated to
`settings.tool_result_max_bytes` to save tokens.
"""
from __future__ import annotations

import datetime as _dt
import io
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from ..config import Settings
from ..errors import (
    FileNotFoundInVault,
    PathSecurityError,
    ScriptError,
    ScriptNotWhitelistedError,
    ToolArgError,
    ToolError,
)
from . import (
    frontmatter,
    search as vault_search,
    vault_fs,
    wikilink,
)

logger = logging.getLogger(__name__)

# Whitelisted scripts (relative to vault root)
SCRIPT_WHITELIST: dict[str, list[str]] = {
    "lint": ["python", ".claudian/lint.py"],
    "graph_audit": ["python", ".claudian/graph_audit.py"],
    "fix_orphans": ["python", ".claudian/fix_orphans.py"],
}


def _truncate(text: str, max_bytes: int) -> tuple[str, bool]:
    """Truncate text to <= max_bytes (UTF-8). Returns (text, was_truncated)."""
    if not text:
        return text, False
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= max_bytes:
        return text, False
    truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return truncated + "\n\n...[truncated]", True


def _today() -> str:
    return _dt.date.today().isoformat()


# ----- Tool implementations -----

def _t_read_file(s: Settings, args: dict[str, Any]) -> dict:
    path = args.get("path")
    if not path or not isinstance(path, str):
        raise ToolArgError("read_file: 'path' is required (string)")
    text = vault_fs.read_text(Path(s.vault_root), path)
    truncated, was = _truncate(text, s.tool_result_max_bytes)
    return {"path": path, "content": truncated, "truncated": was, "size": len(text)}


def _t_write_file(s: Settings, args: dict[str, Any]) -> dict:
    path = args.get("path")
    content = args.get("content")
    if not path or not isinstance(path, str):
        raise ToolArgError("write_file: 'path' is required (string)")
    if not isinstance(content, str):
        raise ToolArgError("write_file: 'content' is required (string)")
    result = vault_fs.write_text(Path(s.vault_root), path, content)
    return result


def _t_append_to_file(s: Settings, args: dict[str, Any]) -> dict:
    path = args.get("path")
    content = args.get("content")
    ensure_nl = args.get("ensure_trailing_newline", True)
    if not path or not isinstance(path, str):
        raise ToolArgError("append_to_file: 'path' is required (string)")
    if not isinstance(content, str):
        raise ToolArgError("append_to_file: 'content' is required (string)")
    result = vault_fs.append_text(
        Path(s.vault_root),
        path,
        content,
        ensure_trailing_newline=bool(ensure_nl),
    )
    return result


def _t_list_files(s: Settings, args: dict[str, Any]) -> dict:
    glob = args.get("glob", "wiki/**/*.md")
    if not isinstance(glob, str):
        raise ToolArgError("list_files: 'glob' must be a string")
    max_results = int(args.get("max_results", 200))
    matches = vault_fs.glob_files(Path(s.vault_root), glob, max_results=max_results)
    return {"glob": glob, "count": len(matches), "files": matches}


def _t_search_vault(s: Settings, args: dict[str, Any]) -> dict:
    query = args.get("query")
    if not query or not isinstance(query, str):
        raise ToolArgError("search_vault: 'query' is required (string)")
    glob = args.get("glob", "**/*.md")
    case_sensitive = bool(args.get("case_sensitive", False))
    max_results = int(args.get("max_results", 50))
    hits = vault_search.search(
        Path(s.vault_root),
        query,
        glob=glob,
        case_sensitive=case_sensitive,
        max_results=max_results,
    )
    truncated, was = _truncate(str(hits), s.tool_result_max_bytes)
    return {"query": query, "count": len(hits), "hits": hits, "truncated": was}


def _t_get_frontmatter(s: Settings, args: dict[str, Any]) -> dict:
    path = args.get("path")
    if not path or not isinstance(path, str):
        raise ToolArgError("get_frontmatter: 'path' is required (string)")
    text = vault_fs.read_text(Path(s.vault_root), path)
    fm, body, has = frontmatter.parse(text)
    return {"path": path, "frontmatter": fm, "has_frontmatter": has, "body_length": len(body)}


def _t_update_frontmatter(s: Settings, args: dict[str, Any]) -> dict:
    path = args.get("path")
    updates = args.get("updates")
    if not path or not isinstance(path, str):
        raise ToolArgError("update_frontmatter: 'path' is required (string)")
    if not isinstance(updates, dict):
        raise ToolArgError("update_frontmatter: 'updates' must be a dict")
    text = vault_fs.read_text(Path(s.vault_root), path)
    fm, body, has = frontmatter.parse(text)
    # Auto-set 'updated' field to today
    merged = frontmatter.merge_update(fm, updates)
    merged["updated"] = _today()
    composed = frontmatter.compose(merged, body)
    result = vault_fs.write_text(Path(s.vault_root), path, composed)
    return {
        "path": path,
        "frontmatter": merged,
        "had_frontmatter": has,
        "bytes_written": result["bytes_written"],
    }


def _t_resolve_wikilink(s: Settings, args: dict[str, Any]) -> dict:
    link = args.get("link")
    if not link or not isinstance(link, str):
        raise ToolArgError("resolve_wikilink: 'link' is required (string)")
    file_pages, basename_index = wikilink.build_index(Path(s.vault_root))
    return wikilink.resolve_one(link, file_pages, basename_index)


def _t_run_vault_script(s: Settings, args: dict[str, Any]) -> dict:
    name = args.get("name")
    if not name or name not in SCRIPT_WHITELIST:
        raise ScriptNotWhitelistedError(
            f"Script not in whitelist: {name!r}. Allowed: {sorted(SCRIPT_WHITELIST.keys())}",
            details={"name": name},
        )
    # C1 fix: extra args are LLM-controlled. Reject any that aren't an empty list
    # so an injected `["; rm -rf /"]` or `["../../escape.py"]` can't reach subprocess.
    extra = args.get("args", []) or []
    if not isinstance(extra, list) or not all(isinstance(x, str) for x in extra):
        raise ToolArgError("run_vault_script: 'args' must be a list of strings")
    if extra:
        raise ToolArgError(
            "run_vault_script: extra args are disabled in this build. "
            "Edit the script whitelist in tool_runtime.py to add parameters.",
            details={"name": name, "rejected_args": extra[:5]},
        )

    # C2 fix: use the Python interpreter that's actually running the backend,
    # not whatever `python` happens to resolve to in cwd's PATH. This prevents
    # OneDrive-locked cwd + a different `python` from silently picking up the
    # wrong venv (or no venv at all).
    script_rel = SCRIPT_WHITELIST[name][1]
    script_abs = Path(s.vault_root) / script_rel
    if not script_abs.is_file():
        return {
            "ok": False,
            "code": "script_missing",
            "tool": "run_vault_script",
            "error": f"Script not found: {script_rel}",
        }
    cmd = [sys.executable, str(script_abs)]
    t0 = time.time()
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(s.vault_root),
            capture_output=True,
            text=True,
            timeout=s.script_timeout_seconds,
            encoding="utf-8",
            errors="replace",
        )
        elapsed = (time.time() - t0) * 1000
        stdout, so_trunc = _truncate(completed.stdout or "", s.tool_result_max_bytes)
        stderr, se_trunc = _truncate(completed.stderr or "", s.tool_result_max_bytes)
        return {
            "name": name,
            "ok": completed.returncode == 0,
            "exit_code": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "duration_ms": int(elapsed),
            "truncated": so_trunc or se_trunc,
        }
    except subprocess.TimeoutExpired as e:
        elapsed = (time.time() - t0) * 1000
        return {
            "name": name,
            "ok": False,
            "exit_code": -1,
            "stdout": (e.stdout or b"").decode("utf-8", errors="ignore") if isinstance(e.stdout, bytes) else (e.stdout or ""),
            "stderr": (f"Timeout after {s.script_timeout_seconds}s").encode().decode(),
            "duration_ms": int(elapsed),
            "truncated": False,
        }


# ----- Dispatcher -----

_IMPL = {
    "read_file": _t_read_file,
    "write_file": _t_write_file,
    "append_to_file": _t_append_to_file,
    "list_files": _t_list_files,
    "search_vault": _t_search_vault,
    "get_frontmatter": _t_get_frontmatter,
    "update_frontmatter": _t_update_frontmatter,
    "resolve_wikilink": _t_resolve_wikilink,
    "run_vault_script": _t_run_vault_script,
}


def execute(s: Settings, name: str, args: dict[str, Any]) -> dict:
    """Execute a tool call. Returns a result envelope.

    On error, returns `{"ok": false, "error": "...", "code": "..."}`.
    Never raises (caller decides how to surface).
    """
    if name not in _IMPL:
        return {
            "ok": False,
            "code": "unknown_tool",
            "error": f"Unknown tool: {name!r}. Known: {sorted(_IMPL.keys())}",
        }
    try:
        result = _IMPL[name](s, args)
        if not isinstance(result, dict):
            result = {"value": result}
        return {"ok": True, "tool": name, **result}
    except (ToolArgError, ToolError) as e:
        logger.info("Tool %s arg/validation error: %s", name, e)
        return {"ok": False, "code": e.code, "tool": name, "error": str(e)}
    except (FileNotFoundInVault, PathSecurityError, ScriptError) as e:
        # These typed errors carry their own `code` and `details` (script_not_whitelisted,
        # path_security_error, raw_immutable, file_not_found, ...). Surface them as-is
        # instead of collapsing to `tool_crashed`.
        return {"ok": False, "code": e.code, "tool": name, "error": str(e), "details": e.details}
    except Exception as e:  # last-resort safety net
        logger.exception("Tool %s crashed", name)
        return {
            "ok": False,
            "code": "tool_crashed",
            "tool": name,
            "error": f"{type(e).__name__}: {e}",
        }


def list_tool_names() -> list[str]:
    return sorted(_IMPL.keys())
