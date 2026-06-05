"""
Custom exception hierarchy. All errors carry a stable `code` for the API layer.
"""
from __future__ import annotations


class LLMwikiError(Exception):
    """Base error. Subclasses provide a stable `code` for the API."""

    code: str = "internal_error"
    http_status: int = 500

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


# ----- Vault / FS -----

class VaultError(LLMwikiError):
    code = "vault_error"
    http_status = 500


class PathSecurityError(VaultError):
    """Path escapes vault root, hits an immutable dir, or is malformed."""
    code = "path_security_error"
    http_status = 403


class FileNotFoundInVault(VaultError):
    code = "file_not_found"
    http_status = 404


class RawImmutableError(PathSecurityError):
    """Attempt to write into raw/."""
    code = "raw_immutable"
    http_status = 403


class FrontmatterError(VaultError):
    code = "frontmatter_error"
    http_status = 400


# ----- Wikilink / Search -----

class WikilinkError(LLMwikiError):
    code = "wikilink_error"
    http_status = 400


class SearchError(LLMwikiError):
    code = "search_error"
    http_status = 500


# ----- LLM -----

class LLMError(LLMwikiError):
    code = "llm_error"
    http_status = 502


class LLMConfigError(LLMError):
    code = "llm_config_error"
    http_status = 503


class LLMRateLimitError(LLMError):
    code = "llm_rate_limit"
    http_status = 429


# ----- Scripts -----

class ScriptError(LLMwikiError):
    code = "script_error"
    http_status = 500


class ScriptNotWhitelistedError(ScriptError):
    code = "script_not_whitelisted"
    http_status = 403


class ScriptTimeoutError(ScriptError):
    code = "script_timeout"
    http_status = 504


# ----- Tools -----

class ToolError(LLMwikiError):
    code = "tool_error"
    http_status = 500


class ToolArgError(ToolError):
    code = "tool_arg_error"
    http_status = 400


# ----- Sessions -----

class SessionError(LLMwikiError):
    code = "session_error"
    http_status = 500


class SessionNotFoundError(SessionError):
    code = "session_not_found"
    http_status = 404
