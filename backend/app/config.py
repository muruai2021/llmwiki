"""
Application configuration via pydantic-settings.

Precedence (highest → lowest):
    1. Environment variables (and .env file)
    2. Claude Code settings.json  (path configurable via LLMWIKI_CLAUDE_SETTINGS_PATH)
    3. Built-in defaults

Only the values that should be editable per-deployment live in pydantic-settings.
Everything else is derived in `settings_loader.py` and re-exposed here.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Backend configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="LLMWIKI_",
        case_sensitive=False,
        extra="ignore",
    )

    # ----- Vault -----
    # Override via env `LLMWIKI_VAULT_ROOT` or .env. The default is just
    # a placeholder for fresh clones — set it to your local Obsidian vault.
    vault_root: str = Field(
        default=r"<path-to-your-obsidian-vault>",
        description="Absolute path to the Obsidian vault on disk.",
    )

    # ----- LLM -----
    llm_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic-compatible API key. Auto-loaded from Claude Code settings.json if empty.",
    )
    llm_base_url: str = Field(
        default="https://api.minimaxi.com/anthropic",
        description="Anthropic-compatible base URL.",
    )
    llm_model: str = Field(
        default="MiniMax-M3",
        description="Model name to use for chat.",
    )
    llm_max_tokens: int = Field(
        default=8192,
        description="Max tokens for LLM response.",
    )
    llm_request_timeout: int = Field(
        default=300,
        description="Request timeout in seconds.",
    )
    llm_max_tool_iterations: int = Field(
        default=8,
        description="Max tool-use iterations per chat turn (safety cap).",
    )

    # ----- Claude Code settings.json (read-only source) -----
    # On dev machines: `C:/Users/<you>/.claude/settings.json`.
    # On Linux servers: set to `/dev/null` to disable auto-loading.
    claude_settings_path: str = Field(
        default=r"<path-to-claude-settings.json>",
        description="Path to Claude Code settings.json for auto-loading env.",
    )

    # ----- Server -----
    host: str = Field(default="127.0.0.1", description="Bind host.")
    port: int = Field(default=8000, description="Bind port.")
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
        ],
        description="CORS allowed origins (dev only).",
    )
    debug: bool = Field(default=False, description="Debug mode.")

    # ----- Sessions -----
    session_max_messages: int = Field(
        default=40,
        description="Soft cap on retained messages per session.",
    )

    # ----- Tool result truncation -----
    tool_result_max_bytes: int = Field(
        default=4096,
        description="Truncate tool_result payloads to this many bytes to save tokens.",
    )

    # ----- Prompt -----
    skill_description_max_chars: int = Field(
        default=100,
        description="First N chars of skill description shown in system prompt index.",
    )

    # ----- Script whitelist -----
    script_timeout_seconds: int = Field(
        default=60,
        description="Max runtime for whitelisted vault scripts.",
    )

    # ----- Derived paths (computed in model_post_init) -----
    @property
    def wiki_dir(self) -> Path:
        return Path(self.vault_root) / "wiki"

    @property
    def raw_dir(self) -> Path:
        return Path(self.vault_root) / "raw"

    @property
    def concepts_dir(self) -> Path:
        return Path(self.vault_root) / "concepts"

    @property
    def skills_dir(self) -> Path:
        return Path(self.vault_root) / ".claude" / "skills"

    @property
    def claudian_dir(self) -> Path:
        return Path(self.vault_root) / ".claudian"

    @property
    def claude_md_path(self) -> Path:
        return Path(self.vault_root) / "CLAUDE.md"

    @property
    def memory_md_path(self) -> Path:
        return Path(self.vault_root) / "MEMORY.md"

    def as_public_dict(self) -> dict:
        """Return a dict safe for /api/healthz (no secrets)."""
        return {
            "vault_root": str(self.vault_root),
            "llm_model": self.llm_model,
            "llm_base_url": self.llm_base_url,
            "has_api_key": bool(self.llm_api_key),
            "debug": self.debug,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton settings instance. Auto-loads from settings.json on first call."""
    from .settings_loader import hydrate_from_claude_settings

    s = Settings()
    hydrate_from_claude_settings(s)
    logger.info(
        "Settings loaded: vault=%s model=%s has_key=%s",
        s.vault_root,
        s.llm_model,
        bool(s.llm_api_key),
    )
    return s
