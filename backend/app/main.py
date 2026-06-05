"""
LLMwiki — FastAPI application entry point.
"""
from __future__ import annotations

import io
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

# Force UTF-8 on Windows
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import __version__
from .config import get_settings
from .errors import LLMwikiError
from .routers import chat, scripts, sessions, skills, vault
from .services import prompt_builder, skills_index
from .services.session_store import get_session_store
from .settings_loader import dump_claude_env

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


# ----- Lifespan: initialize singletons, validate vault -----

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Trigger settings hydration
    settings = get_settings()
    # Pre-warm session store
    _store = get_session_store()
    # Pre-scan skills
    skills = skills_index.scan(Path(settings.vault_root))
    logger.info(
        "LLMwiki %s started. vault=%s skills=%d has_key=%s",
        __version__,
        settings.vault_root,
        len(skills),
        bool(settings.llm_api_key),
    )
    yield
    # No cleanup needed for in-memory store


# ----- App factory -----

app = FastAPI(
    title="LLMwiki API",
    description="Web chat interface for the 政策 Obsidian vault.",
    version=__version__,
    lifespan=lifespan,
)

# ----- CORS (dev only — prod uses same-origin) -----
# We add the middleware at module import time using a permissive default, then
# tighten the origin list inside the lifespan once settings have loaded. This
# replaces the deprecated `@app.on_event("startup")` hook.
_DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_DEFAULT_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Accel-Buffering"],
)


# ----- Error handler -----

@app.exception_handler(LLMwikiError)
async def llmwiki_error_handler(request: Request, exc: LLMwikiError):
    return JSONResponse(
        status_code=exc.http_status,
        content={"error": exc.to_dict()},
    )


# ----- Routers -----

app.include_router(chat.router)
app.include_router(vault.router)
app.include_router(skills.router)
app.include_router(scripts.router)
app.include_router(sessions.router)


# ----- Health check -----

@app.get("/api/healthz")
def healthz() -> dict[str, Any]:
    settings = get_settings()
    skills = skills_index.scan(Path(settings.vault_root))
    return {
        "ok": True,
        "version": __version__,
        "vault_path": str(settings.vault_root),
        "vault_exists": Path(settings.vault_root).is_dir(),
        "model": settings.llm_model,
        "skills_loaded": len(skills),
        "skill_names": [s.name for s in skills],
        "config": settings.as_public_dict(),
        "claude_env": dump_claude_env(settings),
        "prompt_report": prompt_builder.build_size_report(settings),
    }


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "LLMwiki",
        "version": __version__,
        "docs": "/docs",
        "healthz": "/api/healthz",
    }
