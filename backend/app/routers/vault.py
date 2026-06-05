"""
Vault filesystem endpoints:
    GET    /api/vault/tree?path=...
    GET    /api/vault/file?path=...
    PUT    /api/vault/file
    POST   /api/vault/append
    POST   /api/vault/search
    POST   /api/vault/resolve-wikilink
    GET    /api/vault/frontmatter?path=...
    POST   /api/vault/frontmatter/update

All LLMwikiError subclasses are formatted uniformly by the global handler in
`app.main` as `{"error": {"code", "message", "details"}}`. We only raise
`HTTPException` directly for cases that don't originate from a typed error.
"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from ..deps import SettingsDep
from ..errors import FileNotFoundInVault, PathSecurityError
from ..models.vault import (
    AppendRequest,
    AppendResponse,
    FileContentResponse,
    FrontmatterResponse,
    FrontmatterUpdateRequest,
    ResolveWikilinkRequest,
    ResolveWikilinkResponse,
    ResolvedWikilink,
    SearchHit,
    SearchRequest,
    SearchResponse,
    TreeResponse,
    WriteFileRequest,
    WriteFileResponse,
)
from ..services import frontmatter, search, vault_fs, wikilink

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vault", tags=["vault"])


# ----- Tree -----

@router.get("/tree", response_model=TreeResponse)
def get_tree(
    settings: SettingsDep,
    path: str = Query("", description="POSIX vault-relative path (empty = root)."),
    max_depth: int = Query(5, ge=1, le=10),
):
    # PathSecurityError / FileNotFoundInVault are caught by the global handler.
    tree = vault_fs.list_tree(Path(settings.vault_root), path, max_depth=max_depth)
    return TreeResponse(root=path, tree=tree)


# ----- Read / Write / Append file -----

@router.get("/file", response_model=FileContentResponse)
def get_file(
    settings: SettingsDep,
    path: str = Query(..., description="POSIX vault-relative path."),
):
    p = Path(settings.vault_root)
    if not vault_fs.is_file(p, path):
        raise FileNotFoundInVault(f"File not found: {path!r}", details={"path": path})
    abs_path = vault_fs.resolve(p, path)
    real_size = abs_path.stat().st_size
    # Truncate read at 512 KB to protect the LLM/front-end from huge binary files.
    text = vault_fs.read_text(p, path, max_bytes=512 * 1024)
    try:
        fm, body, has_fm = frontmatter.parse(text)
    except Exception:
        fm, body, has_fm = {}, text, False
    return FileContentResponse(
        path=path,
        exists=True,
        raw=text,
        frontmatter=fm,
        body=body,
        has_frontmatter=has_fm,
        size=real_size,
        modified=abs_path.stat().st_mtime,
    )


@router.put("/file", response_model=WriteFileResponse)
def put_file(body: WriteFileRequest, settings: SettingsDep):
    # RawImmutableError / PathSecurityError / VaultError all handled globally.
    result = vault_fs.write_text(
        Path(settings.vault_root),
        body.path,
        body.content,
        create_parents=body.create_parents,
    )
    return WriteFileResponse(
        ok=True,
        path=result["path"],
        bytes_written=result["bytes_written"],
        created_parents=result["created_parents"],
    )


@router.post("/append", response_model=AppendResponse)
def post_append(body: AppendRequest, settings: SettingsDep):
    result = vault_fs.append_text(
        Path(settings.vault_root),
        body.path,
        body.content,
        ensure_trailing_newline=body.ensure_trailing_newline,
    )
    return AppendResponse(
        ok=True,
        path=result["path"],
        bytes_appended=result["bytes_appended"],
        existed_before=result["existed_before"],
    )


# ----- Search -----

@router.post("/search", response_model=SearchResponse)
def post_search(body: SearchRequest, settings: SettingsDep):
    hits = search.search(
        Path(settings.vault_root),
        body.query,
        glob=body.glob,
        case_sensitive=body.case_sensitive,
        max_results=body.max_results,
        context_chars=body.context_chars,
    )
    return SearchResponse(
        query=body.query,
        count=len(hits),
        hits=[SearchHit(**h) for h in hits],
    )


# ----- Wikilink resolve -----

@router.post("/resolve-wikilink", response_model=ResolveWikilinkResponse)
def post_resolve(body: ResolveWikilinkRequest, settings: SettingsDep):
    fp, bi = wikilink.build_index(Path(settings.vault_root))
    result = wikilink.resolve_one(body.link, fp, bi)
    return ResolveWikilinkResponse(
        resolved=ResolvedWikilink(
            link=result.get("link", body.link),
            resolved=result.get("resolved"),
            exists=bool(result.get("exists", False)),
            is_external=bool(result.get("is_external", False)),
        )
    )


# ----- Frontmatter -----

@router.get("/frontmatter", response_model=FrontmatterResponse)
def get_frontmatter(
    settings: SettingsDep,
    path: str = Query(..., description="POSIX vault-relative path."),
):
    p = Path(settings.vault_root)
    if not vault_fs.is_file(p, path):
        raise HTTPException(
            status_code=404,
            detail={"code": "file_not_found", "message": f"File not found: {path!r}"},
        )
    text = vault_fs.read_text(p, path)
    fm, body, has = frontmatter.parse(text)
    return FrontmatterResponse(path=path, frontmatter=fm, has_frontmatter=has)


@router.post("/frontmatter/update", response_model=FrontmatterResponse)
def post_update_frontmatter(body: FrontmatterUpdateRequest, settings: SettingsDep):
    from datetime import date

    p = Path(settings.vault_root)
    if not vault_fs.is_file(p, body.path):
        raise FileNotFoundInVault(f"File not found: {body.path!r}", details={"path": body.path})
    text = vault_fs.read_text(p, body.path)
    fm, md_body, has = frontmatter.parse(text)
    merged = frontmatter.merge_update(fm, body.updates)
    merged["updated"] = date.today().isoformat()
    composed = frontmatter.compose(merged, md_body)
    vault_fs.write_text(p, body.path, composed)
    return FrontmatterResponse(path=body.path, frontmatter=merged, has_frontmatter=True)
