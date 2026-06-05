"""
Auto-load Claude Code settings.json so users don't have to duplicate config.

Reads `<claude_settings_path>` (default points at the developer's local
`~/.claude/settings.json`; can be overridden via `LLMWIKI_CLAUDE_SETTINGS_PATH`
or set to `/dev/null` on servers) and fills in any unset LLM config fields
on the `Settings` instance.

Only fills fields that are still at their default values. Explicit .env
overrides always win.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Map of: settings.json env key  →  Settings attribute name
_ENV_TO_ATTR = {
    "ANTHROPIC_AUTH_TOKEN": "llm_api_key",
    "ANTHROPIC_BASE_URL": "llm_base_url",
    "ANTHROPIC_MODEL": "llm_model",
}


def _read_json(path: Path) -> dict | None:
    try:
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Failed to read %s: %s", path, e)
        return None


def _strip_inline_comment(value: str) -> str:
    """Some users put comments after env values; strip them."""
    return value.split("#", 1)[0].strip()


def _coerce_env_value(raw: Any) -> str | None:
    """settings.json's `env` is a dict of str→str; allow None, int, bool coerced."""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s.lower() in ("null", "none"):
        return None
    return _strip_inline_comment(s)


def hydrate_from_claude_settings(settings) -> None:
    """Fill `settings.llm_*` from Claude Code settings.json if unset.

    Mutates the passed Settings in place. Safe to call multiple times (idempotent).
    """
    path = Path(settings.claude_settings_path)
    data = _read_json(path)
    if not data:
        logger.info("Claude Code settings.json not found at %s — using env / defaults.", path)
        return

    env_block = data.get("env", {}) or {}
    if not isinstance(env_block, dict):
        logger.warning("settings.json env block is not a dict; skipping.")
        return

    # 1) env.* → Settings attributes
    for env_key, attr in _ENV_TO_ATTR.items():
        current = getattr(settings, attr, None)
        if current:  # already set via .env or pydantic default
            continue
        coerced = _coerce_env_value(env_block.get(env_key))
        if coerced:
            setattr(settings, attr, coerced)
            logger.debug("Hydrated %s from settings.json (env.%s)", attr, env_key)

    # 2) Top-level `openaiCompatible` is unused (we use Anthropic SDK shape).
    #    We only log a hint if a user accidentally set it and not env.
    if not settings.llm_api_key and data.get("openaiCompatible", {}).get("apiKey"):
        logger.info(
            "Found openaiCompatible.apiKey in settings.json but we use Anthropic SDK; "
            "set ANTHROPIC_AUTH_TOKEN in env block or LLMWIKI_LLM_API_KEY in .env to enable."
        )

    # 3) Allow env vars to override settings.json (already in pydantic, but
    #    pydantic already gives env vars precedence over field defaults — good).
    for env_key, attr in _ENV_TO_ATTR.items():
        env_value = os.environ.get(env_key) or os.environ.get(f"LLMWIKI_{attr.upper()}")
        if env_value:
            setattr(settings, attr, _strip_inline_comment(env_value))


def dump_claude_env(settings) -> dict[str, str | None]:
    """Return current effective LLM config — for /api/healthz introspection."""
    return {
        "claude_settings_path": str(settings.claude_settings_path),
        "claude_settings_exists": Path(settings.claude_settings_path).exists(),
        "llm_api_key_source": (
            "env(.env)" if os.environ.get("LLMWIKI_LLM_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
            else "settings.json" if Path(settings.claude_settings_path).exists()
            else "missing"
        ),
        "llm_model": settings.llm_model,
        "llm_base_url": settings.llm_base_url,
    }
