"""
POST /api/chat/stream  —  Server-Sent Events streaming chat endpoint.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..config import Settings
from ..deps import SessionStoreDep, SettingsDep
from ..models.chat import ChatRequest
from ..services import llm
from ..services.session_store import SessionStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _format_sse(event: str, data: dict) -> str:
    """Format one SSE event block (ends with \\n\\n)."""
    payload = json.dumps(data, ensure_ascii=False, default=str)
    return f"event: {event}\ndata: {payload}\n\n"


@router.post("/stream")
async def chat_stream(
    body: ChatRequest,
    settings: SettingsDep,
    sessions: SessionStoreDep,
) -> StreamingResponse:
    """Stream chat completion with tool use.

    SSE event protocol (see docs/api.md):
        message_start → content_block_start* → content_block_delta* → content_block_stop*
        → (tool_executing → tool_result)* → message_delta → done
    """
    session = sessions.get_or_create(body.session_id)
    sessions.append_user(session.id, body.message)

    # History = all messages so far (including the user msg we just appended)
    history = list(session.messages)

    async def event_generator() -> AsyncIterator[str]:
        yield _format_sse("message_start", {
            "session_id": session.id,
            "message_id": f"msg_{int(time.time() * 1000)}",
        })

        # Track blocks for replay
        text_parts: list[tuple[int, str]] = []  # (index, accumulated text)
        tool_use_blocks: list[dict] = []
        tool_result_blocks: list[dict] = []

        try:
            async for ev in llm.stream_chat(
                settings,
                user_message=body.message,
                history=history[:-1] if history else [],
                model_override=body.model,
                system_override=body.system_prompt_override,
                max_tokens_override=body.max_tokens,
            ):
                # Track for session replay
                if ev.event == "content_block_delta":
                    if ev.data.get("type") == "text_delta":
                        idx = ev.data.get("index", 0)
                        delta = ev.data.get("delta", "")
                        # Merge into existing entry for this index
                        for i, (j, t) in enumerate(text_parts):
                            if j == idx:
                                text_parts[i] = (j, t + delta)
                                break
                        else:
                            text_parts.append((idx, delta))

                if ev.event == "tool_result":
                    tool_use_blocks.append({
                        "id": ev.data.get("id"),
                        "name": ev.data.get("tool"),
                        "input": {},
                    })
                    tool_result_blocks.append({
                        "tool_use_id": ev.data.get("id"),
                        "content": ev.data.get("result_preview", ""),
                        "is_error": not ev.data.get("ok", False),
                    })

                yield _format_sse(ev.event, ev.data)

                if ev.event in ("done", "error"):
                    break

            # Persist the assistant turn for replay
            sessions.append_assistant_turn(
                session.id,
                text_blocks=[{"text": t} for _, t in sorted(text_parts)],
                tool_use_blocks=tool_use_blocks,
                tool_result_blocks=tool_result_blocks,
            )
            # Auto-title from first user message
            if session.title == "新对话" and body.message:
                title = body.message.strip().split("\n", 1)[0][:60]
                if title:
                    sessions.update_title(session.id, title)

        except asyncio.CancelledError:
            logger.info("Client disconnected mid-stream (session=%s)", session.id)
            raise
        except Exception as e:
            logger.exception("Chat stream crashed")
            yield _format_sse("error", {
                "code": "stream_crashed",
                "message": f"{type(e).__name__}: {e}",
            })

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Nginx: don't buffer
            "Connection": "keep-alive",
        },
    )
