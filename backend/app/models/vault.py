"""
Vault API request / response schemas.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class FileNode(BaseModel):
    name: str
    path: str  # POSIX vault-relative
    type: str  # "file" | "dir"
    children: Optional[list["FileNode"]] = None
    size: Optional[int] = None


FileNode.model_rebuild()


class TreeResponse(BaseModel):
    root: str
    tree: FileNode


class FileContentResponse(BaseModel):
    path: str
    exists: bool
    raw: Optional[str] = Field(default=None, description="Original file content (with frontmatter).")
    frontmatter: Optional[dict] = None
    body: Optional[str] = None
    has_frontmatter: bool = False
    size: int = 0
    modified: Optional[float] = None  # mtime as epoch


class WriteFileRequest(BaseModel):
    path: str = Field(..., min_length=1, description="POSIX vault-relative path.")
    content: str = Field(..., description="Full file content (with frontmatter if applicable).")
    create_parents: bool = True


class WriteFileResponse(BaseModel):
    ok: bool
    path: str
    bytes_written: int
    created_parents: bool


class AppendRequest(BaseModel):
    path: str
    content: str
    ensure_trailing_newline: bool = True


class AppendResponse(BaseModel):
    ok: bool
    path: str
    bytes_appended: int
    existed_before: bool


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    glob: str = "**/*.md"
    case_sensitive: bool = False
    max_results: int = Field(default=100, ge=1, le=1000)
    context_chars: int = Field(default=120, ge=20, le=2000)


class SearchHit(BaseModel):
    path: str
    line: int
    snippet: str
    match_start: int
    match_end: int


class SearchResponse(BaseModel):
    query: str
    count: int
    hits: list[SearchHit]


class ResolveWikilinkRequest(BaseModel):
    link: str


class ResolvedWikilink(BaseModel):
    link: str
    resolved: Optional[str] = None
    exists: bool
    is_external: bool = False


class ResolveWikilinkResponse(BaseModel):
    resolved: ResolvedWikilink


# ----- Frontmatter -----

class FrontmatterUpdateRequest(BaseModel):
    path: str
    updates: dict = Field(..., description="Keys to merge. Pass null to delete a key.")


class FrontmatterResponse(BaseModel):
    path: str
    frontmatter: dict
    has_frontmatter: bool
