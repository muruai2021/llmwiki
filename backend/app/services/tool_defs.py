"""
JSON Schema definitions for the 9 LLM function-calling tools.

Each definition follows Anthropic's `tools` parameter format:
    {
        "name": "...",
        "description": "...",
        "input_schema": { ... JSON Schema ... }
    }
"""
from __future__ import annotations

from typing import Any

# Note: schemas use `additionalProperties: false` where reasonable so the
# model can't smuggle in unhandled fields.

TOOL_READ_FILE: dict[str, Any] = {
    "name": "read_file",
    "description": (
        "Read a single file from the vault. Returns the full content. "
        "Use this BEFORE editing any file to know its current state. "
        "Path is POSIX-style vault-relative (e.g. 'wiki/cities/三亚市.md' or 'MEMORY.md')."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "POSIX vault-relative path to the file.",
            }
        },
        "required": ["path"],
        "additionalProperties": False,
    },
}

TOOL_WRITE_FILE: dict[str, Any] = {
    "name": "write_file",
    "description": (
        "Create or overwrite a file in the vault. Path must NOT start with 'raw/'. "
        "Use this for new pages and complete rewrites. For appending to existing files "
        "(e.g. wiki/log.md), use append_to_file instead."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "POSIX vault-relative path."},
            "content": {"type": "string", "description": "Full file content."},
        },
        "required": ["path", "content"],
        "additionalProperties": False,
    },
}

TOOL_APPEND_TO_FILE: dict[str, Any] = {
    "name": "append_to_file",
    "description": (
        "Append content to an existing file (creates it if missing). "
        "Use for log entries and incremental updates."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string", "description": "Content to append (no leading newline required)."},
            "ensure_trailing_newline": {
                "type": "boolean",
                "default": True,
                "description": "If true, prepends a newline to the appended content if the file does not end with one.",
            },
        },
        "required": ["path", "content"],
        "additionalProperties": False,
    },
}

TOOL_LIST_FILES: dict[str, Any] = {
    "name": "list_files",
    "description": (
        "List files in the vault matching a glob pattern. "
        "Default glob 'wiki/**/*.md' returns all wiki pages. "
        "Always returns POSIX-style relative paths."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "glob": {
                "type": "string",
                "default": "wiki/**/*.md",
                "description": "Glob pattern, e.g. 'wiki/cities/**/*.md' or '**/*.md'.",
            },
            "max_results": {
                "type": "integer",
                "default": 200,
                "minimum": 1,
                "maximum": 2000,
            },
        },
        "additionalProperties": False,
    },
}

TOOL_SEARCH_VAULT: dict[str, Any] = {
    "name": "search_vault",
    "description": (
        "Full-text search across vault files. Returns matching lines with snippets. "
        "Use this to find references to a topic across the wiki."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Literal substring to search for."},
            "glob": {"type": "string", "default": "**/*.md"},
            "case_sensitive": {"type": "boolean", "default": False},
            "max_results": {"type": "integer", "default": 50, "minimum": 1, "maximum": 500},
        },
        "required": ["query"],
        "additionalProperties": False,
    },
}

TOOL_GET_FRONTMATTER: dict[str, Any] = {
    "name": "get_frontmatter",
    "description": (
        "Extract the YAML frontmatter (between --- fences) from a .md file. "
        "Returns {frontmatter: {...}, has_frontmatter: bool}."
    ),
    "input_schema": {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
        "additionalProperties": False,
    },
}

TOOL_UPDATE_FRONTMATTER: dict[str, Any] = {
    "name": "update_frontmatter",
    "description": (
        "Merge-update a file's frontmatter. Pass keys with new values to set them; "
        "pass a key with value null to delete it. The 'updated' field is automatically "
        "set to today's date (YYYY-MM-DD) on every successful update."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "updates": {
                "type": "object",
                "description": "Map of frontmatter key → new value. Use null to delete.",
                "additionalProperties": True,
            },
        },
        "required": ["path", "updates"],
        "additionalProperties": False,
    },
}

TOOL_RESOLVE_WIKILINK: dict[str, Any] = {
    "name": "resolve_wikilink",
    "description": (
        "Resolve a [[wikilink]] target to its actual vault-relative path. "
        "Handles Obsidian's basename fuzzy matching. "
        "Use this before creating new pages to check if a similar name already exists."
    ),
    "input_schema": {
        "type": "object",
        "properties": {"link": {"type": "string"}},
        "required": ["link"],
        "additionalProperties": False,
    },
}

TOOL_RUN_VAULT_SCRIPT: dict[str, Any] = {
    "name": "run_vault_script",
    "description": (
        "Run a whitelisted vault maintenance script. Allowed names: 'lint', "
        "'graph_audit', 'fix_orphans'. cwd is the vault root. "
        "Output is truncated to 16KB. Use this for /lint-style verification."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "enum": ["lint", "graph_audit", "fix_orphans"],
                "description": "Script name (must be in whitelist).",
            },
            "args": {
                "type": "array",
                "items": {"type": "string"},
                "default": [],
            },
        },
        "required": ["name"],
        "additionalProperties": False,
    },
}


# ----- Aggregated exports -----

ALL_TOOLS: list[dict[str, Any]] = [
    TOOL_READ_FILE,
    TOOL_WRITE_FILE,
    TOOL_APPEND_TO_FILE,
    TOOL_LIST_FILES,
    TOOL_SEARCH_VAULT,
    TOOL_GET_FRONTMATTER,
    TOOL_UPDATE_FRONTMATTER,
    TOOL_RESOLVE_WIKILINK,
    TOOL_RUN_VAULT_SCRIPT,
]

# Map for fast lookup in tool_runtime
TOOL_BY_NAME: dict[str, dict[str, Any]] = {t["name"]: t for t in ALL_TOOLS}
