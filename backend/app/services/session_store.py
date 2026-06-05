"""
In-memory session store (Phase 1).

Phase 2 plan: persist to `<vault>/.claudian/sessions/<sid>.jsonl`.
"""
from __future__ import annotations

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Session:
    id: str
    title: str = "新对话"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    # Anthropic message format: list of {role, content}
    messages: list[dict] = field(default_factory=list)

    def to_summary(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "message_count": len(self.messages),
        }


class SessionStore:
    """Thread-safe in-memory session store."""

    def __init__(self, max_messages: int = 40) -> None:
        self._lock = threading.RLock()
        self._sessions: dict[str, Session] = {}
        self._max_messages = max_messages

    # ----- CRUD -----

    def create(self, title: str = "新对话") -> Session:
        sid = uuid.uuid4().hex[:16]
        with self._lock:
            s = Session(id=sid, title=title)
            self._sessions[sid] = s
        return s

    def get(self, sid: str) -> Optional[Session]:
        with self._lock:
            return self._sessions.get(sid)

    def get_or_create(self, sid: Optional[str]) -> Session:
        if sid is None:
            return self.create()
        s = self.get(sid)
        if s is None:
            return self.create()
        return s

    def list(self) -> list[Session]:
        with self._lock:
            return sorted(
                self._sessions.values(),
                key=lambda s: s.updated_at,
                reverse=True,
            )

    def delete(self, sid: str) -> bool:
        with self._lock:
            return self._sessions.pop(sid, None) is not None

    def clear(self) -> None:
        with self._lock:
            self._sessions.clear()

    # ----- Message append -----

    def append_user(self, sid: str, content: str) -> None:
        self._append(sid, {"role": "user", "content": content})

    def append_assistant_turn(
        self,
        sid: str,
        *,
        text_blocks: list[dict] | None = None,
        tool_use_blocks: list[dict] | None = None,
        tool_result_blocks: list[dict] | None = None,
    ) -> None:
        """Append a multi-block assistant turn and the following tool_result turn.

        Anthropic's messages API requires us to:
          - Send the assistant turn with all blocks (text + tool_use)
          - Send a user turn with tool_result blocks for each tool_use

        We mirror that structure so we can replay later.
        """
        asst_blocks: list[dict] = []
        for b in (text_blocks or []):
            asst_blocks.append({"type": "text", "text": b.get("text", "")})
        for b in (tool_use_blocks or []):
            asst_blocks.append({
                "type": "tool_use",
                "id": b.get("id"),
                "name": b.get("name"),
                "input": b.get("input", {}),
            })
        if asst_blocks:
            self._append(sid, {"role": "assistant", "content": asst_blocks})
        if tool_result_blocks:
            self._append(sid, {"role": "user", "content": tool_result_blocks})
        # M7 fix: trim only at the end of a complete assistant turn, never
        # on the bare `append_user` call. Otherwise a streaming user message
        # (no assistant reply yet) would race with the cap and we'd delete
        # the head of the conversation. End-of-turn is a safe moment because
        # at that point we know the last block is a complete user/assistant
        # pair (or assistant alone — which we still drop from the head).
        self._trim(sid)

    def update_title(self, sid: str, title: str) -> bool:
        with self._lock:
            s = self._sessions.get(sid)
            if s is None:
                return False
            s.title = title[:80]
            s.updated_at = time.time()
            return True

    # ----- Internals -----

    def _append(self, sid: str, msg: dict) -> None:
        with self._lock:
            s = self._sessions.get(sid)
            if s is None:
                return
            s.messages.append(msg)
            s.updated_at = time.time()

    def _trim(self, sid: str) -> None:
        """Drop at most ONE user/assistant pair from the head if the
        conversation is over `max_messages`. Pair-trimming is correct for
        Anthropic's API: a sequence that doesn't start with `user` is
        rejected. Trimming is called once per assistant turn, so the cap
        is enforced lazily without races against in-flight user messages.
        """
        with self._lock:
            s = self._sessions.get(sid)
            if s is None:
                return
            cap = self._max_messages
            msgs = s.messages
            if len(msgs) <= cap:
                return
            if len(msgs) < 2:
                return
            if msgs[0].get("role") == "user" and msgs[1].get("role") == "assistant":
                del msgs[0]
                del msgs[0]
            # Else: head is a leading assistant or an in-flight user message;
            # leave it alone (will resolve on the next trim call).


# ----- Singleton holder -----

_instance: SessionStore | None = None


def get_session_store() -> SessionStore:
    """Lazily create the singleton (called from app lifespan)."""
    global _instance
    if _instance is None:
        from ..config import get_settings
        s = get_settings()
        _instance = SessionStore(max_messages=s.session_max_messages)
    return _instance
