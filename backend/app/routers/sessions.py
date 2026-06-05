"""
Session management endpoints:
    GET    /api/sessions
    DELETE /api/sessions/{id}
    POST   /api/sessions  (create new)
    GET    /api/sessions/{id}  (detail)
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from ..deps import SessionStoreDep
from ..models.skills import SessionDeleteResponse, SessionsListResponse, SessionSummary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", response_model=SessionsListResponse)
def list_sessions(sessions: SessionStoreDep):
    items = sessions.list()
    return SessionsListResponse(
        count=len(items),
        sessions=[SessionSummary(**s.to_summary()) for s in items],
    )


@router.post("", response_model=SessionSummary)
def create_session(sessions: SessionStoreDep, title: str = "新对话"):
    s = sessions.create(title=title)
    return SessionSummary(**s.to_summary())


@router.get("/{sid}", response_model=SessionSummary)
def get_session(sid: str, sessions: SessionStoreDep):
    s = sessions.get(sid)
    if s is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "session_not_found", "message": f"Session not found: {sid}"},
        )
    return SessionSummary(**s.to_summary())


@router.delete("/{sid}", response_model=SessionDeleteResponse)
def delete_session(sid: str, sessions: SessionStoreDep):
    ok = sessions.delete(sid)
    if not ok:
        raise HTTPException(
            status_code=404,
            detail={"code": "session_not_found", "message": f"Session not found: {sid}"},
        )
    return SessionDeleteResponse(ok=True, id=sid)
