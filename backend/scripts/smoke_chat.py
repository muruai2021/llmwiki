"""
SSE smoke test — connect to /api/chat/stream and print events.

Usage:
    python scripts/smoke_chat.py "海口市有什么人才引进政策？"

Requires the backend to be running on http://127.0.0.1:8000
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx


def parse_sse_events(text: str) -> list[tuple[str, dict]]:
    """Parse a raw SSE stream into (event_name, data_dict) pairs."""
    events: list[tuple[str, dict]] = []
    event_name = None
    data_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip("\r")
        if line.startswith(":"):
            continue  # comment
        if not line:
            if event_name and data_lines:
                payload = "\n".join(data_lines)
                try:
                    data = json.loads(payload)
                except json.JSONDecodeError:
                    data = {"_raw": payload}
                events.append((event_name, data))
                event_name = None
                data_lines = []
            continue
        if line.startswith("event: "):
            event_name = line[7:].strip()
        elif line.startswith("data: "):
            data_lines.append(line[6:])
    return events


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: smoke_chat.py <message>", file=sys.stderr)
        return 2
    message = sys.argv[1]
    url = os.environ.get("LLMWIKI_URL", "http://127.0.0.1:8000/api/chat/stream")
    session_id = os.environ.get("LLMWIKI_SESSION_ID")  # optional

    print(f"→ {url}")
    print(f"→ message: {message!r}")
    print("---")

    body = {"message": message}
    if session_id:
        body["session_id"] = session_id

    try:
        with httpx.Client(timeout=600) as client:
            with client.stream("POST", url, json=body) as r:
                if r.status_code != 200:
                    print(f"✗ HTTP {r.status_code}: {r.read()}", file=sys.stderr)
                    return 1
                buf = ""
                for chunk in r.iter_text():
                    buf += chunk
                    # Process complete events
                    while "\n\n" in buf:
                        block, buf = buf.split("\n\n", 1)
                        events = parse_sse_events(block + "\n\n")
                        for name, data in events:
                            print(f"[{name}]", json.dumps(data, ensure_ascii=False)[:300])
    except httpx.ConnectError as e:
        print(f"✗ Connection failed: {e}", file=sys.stderr)
        print("  Is the backend running? Try: uvicorn app.main:app --port 8000", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n(interrupted)")
    print("---")
    print("✓ done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
