"""
Skills endpoints:
    GET /api/skills
    GET /api/skills/{name}
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..deps import SettingsDep
from ..models.skills import SkillDetailResponse, SkillsListResponse
from ..services import skills_index

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("", response_model=SkillsListResponse)
def list_skills(settings: SettingsDep):
    skills = skills_index.scan(Path(settings.vault_root))
    return SkillsListResponse(
        count=len(skills),
        skills=skills_index.to_index_dicts(skills),
    )


@router.get("/{name}", response_model=SkillDetailResponse)
def get_skill(name: str, settings: SettingsDep):
    skills = skills_index.scan(Path(settings.vault_root))
    skill = skills_index.get_by_name(skills, name)
    if skill is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "skill_not_found", "message": f"Skill not found: {name!r}"},
        )
    return SkillDetailResponse(
        name=skill.name,
        description=skill.description,
        path=skill.path,
        size=skill.size,
        body=skill.body,
        frontmatter=skill.frontmatter,
    )
