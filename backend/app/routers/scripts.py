"""
POST /api/scripts/run  —  run whitelisted vault maintenance scripts.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..config import Settings
from ..deps import SettingsDep
from ..errors import ScriptNotWhitelistedError
from ..models.skills import ScriptRunRequest, ScriptRunResponse
from ..services.tool_runtime import SCRIPT_WHITELIST, execute as run_tool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scripts", tags=["scripts"])


@router.post("/run", response_model=ScriptRunResponse)
def run_script(body: ScriptRunRequest, settings: SettingsDep):
    if body.name not in SCRIPT_WHITELIST:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "script_not_whitelisted",
                "message": f"Script not in whitelist: {body.name!r}. "
                           f"Allowed: {sorted(SCRIPT_WHITELIST.keys())}",
            },
        )
    result = run_tool(settings, "run_vault_script", {
        "name": body.name,
        "args": body.args,
    })
    if not result.get("ok"):
        raise HTTPException(
            status_code=500,
            detail={
                "code": result.get("code", "script_error"),
                "message": result.get("error", "Script failed"),
            },
        )
    return ScriptRunResponse(
        name=body.name,
        ok=bool(result.get("ok")),
        exit_code=int(result.get("exit_code", -1)),
        stdout=result.get("stdout", ""),
        stderr=result.get("stderr", ""),
        duration_ms=int(result.get("duration_ms", 0)),
        truncated=bool(result.get("truncated", False)),
    )


@router.get("/whitelist")
def get_whitelist():
    """Return the whitelist (for the UI)."""
    return {"scripts": sorted(SCRIPT_WHITELIST.keys())}
