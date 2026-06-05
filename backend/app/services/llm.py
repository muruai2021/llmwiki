"""
Anthropic SDK wrapper — handles streaming, base URL override, and tool-use loop.

We pass `base_url` to the client to swap in the minimaxi Anthropic-compatible
endpoint. Everything else (messages, tools, system prompt) uses the standard
Anthropic API shape.
"""
from __future__ import annotations

import asyncio
import io
import json
import logging
import sys
import time
from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional

from ..config import Settings
from ..errors import LLMConfigError
from . import prompt_builder, tool_runtime
from .tool_defs import ALL_TOOLS

logger = logging.getLogger(__name__)


@dataclass
class StreamEvent:
    """A single SSE event yielded to the caller."""
    event: str
    data: dict


def _truncate(text: str, max_bytes: int) -> tuple[str, bool]:
    if not text:
        return text, False
    enc = text.encode("utf-8", errors="replace")
    if len(enc) <= max_bytes:
        return text, False
    return enc[:max_bytes].decode("utf-8", errors="ignore") + "\n\n...[truncated]", True


def _get_client(s: Settings):
    """Lazily construct an Anthropic client with the configured base_url."""
    try:
        from anthropic import Anthropic
    except ImportError as e:
        raise LLMConfigError("anthropic SDK not installed") from e
    if not s.llm_api_key:
        raise LLMConfigError(
            "LLM API key is not configured. Set LLMWIKI_LLM_API_KEY in .env or "
            "populate env.ANTHROPIC_AUTH_TOKEN in Claude Code settings.json."
        )
    return Anthropic(
        api_key=s.llm_api_key,
        base_url=s.llm_base_url,
        timeout=s.llm_request_timeout,
        max_retries=2,
    )


# ----- Single-pass stream consumer -----

def _consume_stream_sync(response_stream) -> list[StreamEvent]:
    """Read all events from the blocking Anthropic stream and return StreamEvent list."""
    events: list[StreamEvent] = []
    # Mutable state via simple object
    state = {
        "current_block_type": None,
        "current_block_index": None,
        "current_tool_id": None,
        "current_tool_name": None,
        "current_tool_input_json": [],
        "collected_text": [],
        "tool_uses": [],
        "stop_reason": None,
        "usage": {},
    }

    for event in response_stream:
        et = getattr(event, "type", None)

        if et == "message_start":
            msg = getattr(event, "message", None)
            if msg is not None:
                u = getattr(msg, "usage", None)
                if u is not None:
                    state["usage"].update({
                        "input_tokens": getattr(u, "input_tokens", 0),
                        "output_tokens": getattr(u, "output_tokens", 0),
                    })

        elif et == "content_block_start":
            block = getattr(event, "content_block", None)
            idx = getattr(event, "index", 0)
            state["current_block_index"] = idx
            if block is not None:
                btype = getattr(block, "type", None)
                if btype == "text":
                    state["current_block_type"] = "text"
                    events.append(StreamEvent("content_block_start", {"type": "text", "index": idx}))
                elif btype == "tool_use":
                    state["current_block_type"] = "tool_use"
                    state["current_tool_id"] = getattr(block, "id", None)
                    state["current_tool_name"] = getattr(block, "name", None)
                    state["current_tool_input_json"] = []
                    events.append(StreamEvent("content_block_start", {
                        "type": "tool_use", "index": idx,
                        "id": state["current_tool_id"], "name": state["current_tool_name"],
                    }))

        elif et == "content_block_delta":
            delta = getattr(event, "delta", None)
            idx = getattr(event, "index", state["current_block_index"] or 0)
            if delta is None:
                continue
            dtype = getattr(delta, "type", None)
            if dtype == "text_delta":
                text = getattr(delta, "text", "")
                state["collected_text"].append(text)
                events.append(StreamEvent("content_block_delta", {
                    "type": "text_delta", "index": idx, "delta": text,
                }))
            elif dtype == "input_json_delta":
                partial = getattr(delta, "partial_json", "")
                state["current_tool_input_json"].append(partial)
                events.append(StreamEvent("content_block_delta", {
                    "type": "input_json_delta", "index": idx, "delta": partial,
                }))

        elif et == "content_block_stop":
            idx = getattr(event, "index", state["current_block_index"] or 0)
            if state["current_block_type"] == "tool_use" and state["current_tool_name"]:
                try:
                    tool_input = json.loads("".join(state["current_tool_input_json"])) if state["current_tool_input_json"] else {}
                except json.JSONDecodeError:
                    tool_input = {"_raw": "".join(state["current_tool_input_json"])}
                state["tool_uses"].append({
                    "id": state["current_tool_id"],
                    "name": state["current_tool_name"],
                    "input": tool_input,
                })
            state["current_block_type"] = None
            state["current_tool_id"] = None
            state["current_tool_name"] = None
            state["current_tool_input_json"] = []
            events.append(StreamEvent("content_block_stop", {"index": idx}))

        elif et == "message_delta":
            delta = getattr(event, "delta", None)
            if delta is not None:
                state["stop_reason"] = getattr(delta, "stop_reason", None)
            u = getattr(event, "usage", None)
            if u is not None:
                state["usage"]["output_tokens"] = getattr(
                    u, "output_tokens", state["usage"].get("output_tokens", 0)
                )
            events.append(StreamEvent("message_delta", {
                "stop_reason": state["stop_reason"],
            }))

        elif et == "message_stop":
            pass

    # Attach tool_uses / stop_reason / usage as a final pseudo-event marker
    events.append(StreamEvent("__end_of_stream__", {
        "tool_uses": state["tool_uses"],
        "collected_text": "".join(state["collected_text"]),
        "stop_reason": state["stop_reason"],
        "usage": state["usage"],
    }))
    return events


# ----- Main streaming chat -----

async def stream_chat(
    s: Settings,
    *,
    user_message: str,
    history: list[dict] | None = None,
    model_override: str | None = None,
    system_override: str | None = None,
    max_tokens_override: int | None = None,
) -> AsyncIterator[StreamEvent]:
    """Stream a chat completion with automatic tool-use loop."""
    history = history or []
    system_prompt = system_override if system_override is not None else prompt_builder.build(s)
    model = model_override or s.llm_model
    max_tokens = max_tokens_override or s.llm_max_tokens

    messages: list[dict] = []
    for m in history:
        messages.append(m)
    messages.append({"role": "user", "content": user_message})

    message_id = f"msg_{int(time.time() * 1000)}"
    yield StreamEvent("message_start", {"message_id": message_id})

    try:
        client = _get_client(s)
    except LLMConfigError as e:
        yield StreamEvent("error", {"code": e.code, "message": str(e)})
        return

    for iteration in range(s.llm_max_tool_iterations):
        # Build the streaming request (blocking call wrapped in to_thread)
        def _call():
            return client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                tools=ALL_TOOLS,
                messages=messages,
                stream=True,
            )

        try:
            response_stream = await asyncio.to_thread(_call)
            events = await asyncio.to_thread(_consume_stream_sync, response_stream)
        except Exception as e:
            logger.exception("LLM call failed")
            yield StreamEvent("error", {
                "code": "llm_error",
                "message": f"LLM call failed: {type(e).__name__}: {e}",
            })
            return

        # Yield all events except the marker
        end_marker: dict | None = None
        for ev in events:
            if ev.event == "__end_of_stream__":
                end_marker = ev.data
                continue
            yield ev

        assert end_marker is not None
        tool_uses = end_marker["tool_uses"]
        stop_reason = end_marker["stop_reason"]
        collected_text = end_marker["collected_text"]
        usage = end_marker["usage"]

        # If we got tool calls and the model wants to use them, execute and continue
        if tool_uses and stop_reason == "tool_use":
            # Append assistant turn (echo back tool_use blocks)
            asst_blocks: list[dict] = []
            if collected_text.strip():
                asst_blocks.append({"type": "text", "text": collected_text})
            for tu in tool_uses:
                asst_blocks.append({
                    "type": "tool_use",
                    "id": tu["id"],
                    "name": tu["name"],
                    "input": tu["input"],
                })
            messages.append({"role": "assistant", "content": asst_blocks})

            # Execute each tool
            tool_result_blocks: list[dict] = []
            for tu in tool_uses:
                try:
                    args_preview = json.dumps(tu["input"], ensure_ascii=False)[:200]
                except Exception:
                    args_preview = "<unserializable>"
                yield StreamEvent("tool_executing", {
                    "tool": tu["name"],
                    "args_preview": args_preview,
                    "id": tu["id"],
                })
                result = await asyncio.to_thread(
                    tool_runtime.execute, s, tu["name"], tu["input"]
                )
                preview = json.dumps(result, ensure_ascii=False)
                truncated, was = _truncate(preview, s.tool_result_max_bytes)
                yield StreamEvent("tool_result", {
                    "tool": tu["name"],
                    "id": tu["id"],
                    "ok": bool(result.get("ok")),
                    "result_preview": truncated,
                    "error": result.get("error") if not result.get("ok") else None,
                })
                tool_result_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tu["id"],
                    "content": truncated,
                    "is_error": not result.get("ok", False),
                })
            messages.append({"role": "user", "content": tool_result_blocks})
            continue  # next iteration: model sees tool results

        # No more tool calls → done
        yield StreamEvent("done", {
            "usage": usage,
            "stop_reason": stop_reason,
            "iteration": iteration,
        })
        return

    # Safety: too many iterations
    yield StreamEvent("error", {
        "code": "max_tool_iterations",
        "message": f"Exceeded max tool iterations ({s.llm_max_tool_iterations}). Aborting.",
    })
