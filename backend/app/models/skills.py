"""
Skills / scripts / sessions API schemas.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class SkillIndexEntry(BaseModel):
    name: str
    description: str
    path: str
    size: int


class SkillsListResponse(BaseModel):
    count: int
    skills: list[SkillIndexEntry]


class SkillDetailResponse(BaseModel):
    name: str
    description: str
    path: str
    size: int
    body: str
    frontmatter: dict = Field(default_factory=dict)


# ----- Scripts -----

class ScriptRunRequest(BaseModel):
    name: str = Field(..., description="Script name (must be in whitelist).")
    args: list[str] = Field(default_factory=list)
    timeout: Optional[int] = Field(default=None, ge=5, le=600)


class ScriptRunResponse(BaseModel):
    name: str
    ok: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    truncated: bool = False


# ----- Sessions -----

class SessionSummary(BaseModel):
    id: str
    title: str
    created_at: float
    updated_at: float
    message_count: int


class SessionsListResponse(BaseModel):
    count: int
    sessions: list[SessionSummary]


class SessionDeleteResponse(BaseModel):
    ok: bool
    id: str
