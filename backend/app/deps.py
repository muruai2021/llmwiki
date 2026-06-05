"""
FastAPI dependencies — provide Settings, SessionStore, and common headers.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from .config import Settings, get_settings
from .services.session_store import SessionStore, get_session_store


SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionStoreDep = Annotated[SessionStore, Depends(get_session_store)]
