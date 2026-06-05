"""
Path-safe filesystem operations against the vault.

All public functions take **POSIX-style vault-relative paths** and translate
to absolute `pathlib.Path` internally. They raise specific exceptions from
`app.errors` for security violations.
"""
from __future__ import annotations

import io
import os
import re
import sys
from pathlib import Path
from typing import Iterable, Iterator

# Force UTF-8 stdout/stderr on Windows
from ..errors import (
    FileNotFoundInVault,
    PathSecurityError,
    RawImmutableError,
    VaultError,
)

# ----- Path policy -----

# Paths that can never be written to (but can be read for context).
_IMMUTABLE_WRITE_DIRS = (
    "raw",
    ".obsidian",
    ".claude",
)

# Paths completely off-limits (read AND write).
_FORBIDDEN_DIRS = (
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".claudian",
)


def _normalize(rel: str) -> str:
    """Normalize a vault-relative POSIX path.

    - Empty string / "." / "./" → "" (means "the vault root itself")
    - Strip leading slashes / backslashes
    - Collapse backslashes → forward slashes
    - Reject parent escape attempts
    """
    if rel is None:
        raise PathSecurityError("Path is None")
    s = str(rel).strip()
    if not s or s == ".":
        return ""
    s = s.replace("\\", "/")
    s = s.lstrip("/")
    if s == ".":
        return ""
    # Forbid parent escape
    parts = s.split("/")
    if any(p == ".." for p in parts):
        raise PathSecurityError(
            f"Path escapes vault root: {rel!r}",
            details={"path": rel},
        )
    return s


def resolve(vault_root: Path, rel: str) -> Path:
    """Resolve a vault-relative path to an absolute `Path`.

    Performs all security checks. The returned path is **not guaranteed
    to exist** — use `exists()` separately.
    """
    norm = _normalize(rel)
    root = Path(vault_root).resolve()
    target = (root / norm).resolve() if norm else root

    # Make sure the resolved target is still under root (defence in depth)
    try:
        target.relative_to(root)
    except ValueError as e:
        raise PathSecurityError(
            f"Path escapes vault root after resolve: {rel!r} → {target}",
            details={"path": rel, "resolved": str(target)},
        ) from e

    return target


def _check_forbidden_dir(rel: str) -> None:
    parts = rel.split("/") if rel else []
    for forbidden in _FORBIDDEN_DIRS:
        if forbidden in parts:
            raise PathSecurityError(
                f"Path is in forbidden directory: {rel!r}",
                details={"path": rel, "forbidden": forbidden},
            )


def _check_writable(vault_root: Path, rel: str) -> Path:
    """Resolve + check write permissions."""
    norm = _normalize(rel)
    _check_forbidden_dir(norm)

    # Check write immutability
    parts = norm.split("/") if norm else []
    if parts and parts[0] in _IMMUTABLE_WRITE_DIRS:
        if parts[0] == "raw":
            raise RawImmutableError(
                f"Cannot write to raw/ (immutable original documents): {rel!r}",
                details={"path": rel},
            )
        raise PathSecurityError(
            f"Path is in a non-writable directory: {rel!r}",
            details={"path": rel, "directory": parts[0]},
        )

    return resolve(vault_root, rel)


# ----- Read operations -----

def exists(vault_root: Path, rel: str) -> bool:
    try:
        return resolve(vault_root, rel).exists()
    except PathSecurityError:
        return False


def is_file(vault_root: Path, rel: str) -> bool:
    try:
        return resolve(vault_root, rel).is_file()
    except PathSecurityError:
        return False


def is_dir(vault_root: Path, rel: str) -> bool:
    try:
        return resolve(vault_root, rel).is_dir()
    except PathSecurityError:
        return False


def read_text(
    vault_root: Path,
    rel: str,
    encoding: str = "utf-8",
    *,
    max_bytes: int = 512 * 1024,
) -> str:
    """Read a text file from the vault.

    `max_bytes` truncates the read to that many bytes (no decode error on tail).
    For binary files (PDF, images) the caller should use `read_bytes` instead;
    this function will only return the head as best-effort text.
    """
    target = resolve(vault_root, rel)
    if not target.is_file():
        raise FileNotFoundInVault(
            f"File not found: {rel!r}",
            details={"path": rel},
        )
    try:
        size = target.stat().st_size
    except OSError:
        size = 0
    # M12 fix: OneDrive / AV / EFS sometimes lock the file mid-read and we get
    # PermissionError. Surface that as a typed VaultError (502/500) instead of
    # letting it crash the request handler with a 500 traceback.
    try:
        if size > max_bytes:
            with target.open("rb") as f:
                raw = f.read(max_bytes)
        else:
            raw = target.read_bytes()
    except PermissionError as e:
        raise VaultError(
            f"Permission denied reading {rel!r} (file may be locked by OneDrive / AV)",
            details={"path": rel},
        ) from e
    except OSError as e:
        raise VaultError(
            f"OS error reading {rel!r}: {type(e).__name__}: {e}",
            details={"path": rel},
        ) from e
    try:
        text = raw.decode(encoding, errors="replace")
    except (UnicodeDecodeError, LookupError):
        # Fall back to GBK on Windows for legacy files; "replace" still safe.
        text = raw.decode("gbk", errors="replace")
    # Sanitise so the response is always valid JSON.
    # 1) Drop control chars except \n, \r, \t (binary heads can have anything).
    # 2) Drop lone surrogates (they break strict JSON encoders).
    # 3) Drop backslash + double-quote so escaping can't be tricked.
    out_chars: list[str] = []
    for ch in text:
        cp = ord(ch)
        if ch in ("\n", "\r", "\t"):
            out_chars.append(ch)
        elif cp < 0x20 or cp == 0x7F:
            continue
        elif 0xD800 <= cp <= 0xDFFF:  # lone surrogate
            continue
        else:
            out_chars.append(ch)
    return "".join(out_chars)


def read_bytes(vault_root: Path, rel: str) -> bytes:
    target = resolve(vault_root, rel)
    if not target.is_file():
        raise FileNotFoundInVault(f"File not found: {rel!r}", details={"path": rel})
    try:
        return target.read_bytes()
    except PermissionError as e:
        raise VaultError(
            f"Permission denied reading {rel!r} (file may be locked by OneDrive / AV)",
            details={"path": rel},
        ) from e
    except OSError as e:
        raise VaultError(
            f"OS error reading {rel!r}: {type(e).__name__}: {e}",
            details={"path": rel},
        ) from e


# ----- Write operations -----

def write_text(
    vault_root: Path,
    rel: str,
    content: str,
    *,
    create_parents: bool = True,
    encoding: str = "utf-8",
) -> dict:
    """Write/overwrite a file. Returns `{path, bytes_written, created_parents}`.

    Refuses to write into raw/, .obsidian/, .claude/.
    """
    target = _check_writable(vault_root, rel)
    created_parents = False
    if not target.parent.exists():
        if not create_parents:
            raise VaultError(
                f"Parent directory does not exist: {rel!r}",
                details={"path": rel},
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        created_parents = True
    n = target.write_text(content, encoding=encoding)
    return {
        "path": rel,
        "abs_path": str(target),
        "bytes_written": n,
        "created_parents": created_parents,
    }


def append_text(
    vault_root: Path,
    rel: str,
    content: str,
    *,
    ensure_trailing_newline: bool = True,
    encoding: str = "utf-8",
) -> dict:
    """Append to a file. Creates it if missing. Creates parents if missing."""
    target = _check_writable(vault_root, rel)
    if not target.parent.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
    existed = target.exists()
    if ensure_trailing_newline and existed:
        existing = target.read_text(encoding=encoding)
        if existing and not existing.endswith("\n"):
            target.write_text(existing + "\n", encoding=encoding)
    with target.open("a", encoding=encoding) as f:
        f.write(content)
    return {
        "path": rel,
        "abs_path": str(target),
        "existed_before": existed,
        "bytes_appended": len(content.encode(encoding)),
    }


# ----- Tree operations -----

_SKIP_DIRS = frozenset({
    ".obsidian", ".git", ".venv", "node_modules", "__pycache__",
    ".claude", ".claudian",
})


def list_tree(
    vault_root: Path,
    rel: str = "",
    *,
    max_depth: int = 5,
    include_files: bool = True,
) -> dict:
    """Return a tree node `{name, path, type, children?}` for the given sub-path.

    Always uses POSIX-style relative paths.
    """
    target = resolve(vault_root, rel)
    if not target.exists():
        raise FileNotFoundInVault(
            f"Path not found: {rel!r}",
            details={"path": rel},
        )

    def _build(p: Path, rel_path: str, depth: int) -> dict:
        node = {
            "name": p.name or rel_path or ".",
            "path": rel_path,
            "type": "dir" if p.is_dir() else "file",
        }
        if p.is_dir():
            children: list[dict] = []
            if depth < max_depth:
                # Deterministic order: dirs first, then files; both alphabetical
                entries = sorted(
                    p.iterdir(),
                )
                dirs = [e for e in entries if e.is_dir() and e.name not in _SKIP_DIRS]
                files = [e for e in entries if e.is_file()] if include_files else []
                for d in dirs:
                    children.append(_build(d, f"{rel_path}/{d.name}" if rel_path else d.name, depth + 1))
                for f in files:
                    children.append(_build(f, f"{rel_path}/{f.name}" if rel_path else f.name, depth + 1))
            node["children"] = children
        else:
            try:
                node["size"] = p.stat().st_size
            except OSError:
                node["size"] = 0
        return node

    return _build(target, rel, 0)


def glob_files(
    vault_root: Path,
    pattern: str,
    *,
    max_results: int = 200,
) -> list[str]:
    """Glob files in the vault (POSIX-style relative paths).

    `pattern` is a glob like `wiki/cities/**/*.md` or `**/*.md`.
    Always returns POSIX-style paths, sorted.
    """
    # Always use absolute glob anchored at vault root
    if pattern.startswith("/"):
        pattern = pattern.lstrip("/")
    root = resolve(vault_root, "")
    matches: Iterable[Path] = root.glob(pattern) if pattern else []
    out: list[str] = []
    for p in matches:
        if not p.is_file():
            continue
        if any(part in _SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        rel = p.relative_to(root).as_posix()
        out.append(rel)
        if len(out) >= max_results:
            break
    out.sort()
    return out


# ----- Conversion helpers -----

def to_posix(rel: str) -> str:
    """Coerce a path string to POSIX style (best-effort)."""
    return _normalize(rel)


def from_posix(rel: str) -> str:
    """Coerce POSIX back to OS-native (used only for display)."""
    return rel.replace("/", os.sep)
