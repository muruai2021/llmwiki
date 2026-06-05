"""
Chat request / response schemas.

The chat endpoint is SSE — the response body is a stream of `data: {json}\n\n`
events. These models describe the *event payloads* (sent as JSON inside `data:`)
and the POST request body.
"""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# ----- Request -----

class ChatRequest(BaseModel):
    """POST /api/chat/stream body."""
    message: str = Field(..., min_length=1, description="User message (this turn only).")
    session_id: Optional[str] = Field(
        default=None,
        description="Existing session ID; omit to start a new one.",
    )
    system_prompt_override: Optional[str] = Field(
        default=None,
        description="Advanced: replace the auto-generated system prompt.",
    )
    max_tokens: Optional[int] = Field(default=None, ge=64, le=32_000)
    model: Optional[str] = Field(
        default=None,
        description="Override the model for this turn (defaults to settings.llm_model).",
    )


# ----- SSE event payloads -----
# Each event has the shape: { event: <name>, data: <payload> }
# The frontend parses `data` as JSON.

class MessageStartData(BaseModel):
    session_id: str
    message_id: str


class ContentBlockStartData(BaseModel):
    type: Literal["text", "tool_use"]
    index: int
    # text block: only `index`
    # tool_use block: name, id
    name: Optional[str] = None
    id: Optional[str] = None


class ContentBlockDeltaData(BaseModel):
    type: Literal["text_delta", "input_json_delta"]
    index: int
    delta: str


class ContentBlockStopData(BaseModel):
    index: int


class ToolExecutingData(BaseModel):
    tool: str
    args_preview: str
    id: str


class ToolResultData(BaseModel):
    tool: str
    id: str
    ok: bool
    result_preview: str
    result_full: Optional[str] = None
    error: Optional[str] = None


class MessageDeltaData(BaseModel):
    stop_reason: Optional[str] = None


class DoneData(BaseModel):
    session_id: str
    usage: dict = Field(default_factory=dict)


class ErrorData(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class HeartbeatData(BaseModel):
    ts: float


# ----- Convenience union for stream parser -----

ChatEventData = (
    MessageStartData
    | ContentBlockStartData
    | ContentBlockDeltaData
    | ContentBlockStopData
    | ToolExecutingData
    | ToolResultData
    | MessageDeltaData
    | DoneData
    | ErrorData
    | HeartbeatData
)
