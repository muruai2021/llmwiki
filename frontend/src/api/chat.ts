// SSE consumer for /api/chat/stream.
// We use fetch + ReadableStream (not EventSource) because we need POST.

import type { ChatRequest, ChatSSEEvent } from "../types/api";

export interface StreamHandlers {
  onEvent: (ev: ChatSSEEvent) => void;
  onError?: (err: Error) => void;
  onDone?: () => void;
}

export interface StreamHandle {
  abort: () => void;
}

/**
 * Send a chat message and stream the SSE events.
 * Returns a handle with an `abort()` method to cancel the stream.
 */
export function streamChat(
  body: ChatRequest,
  handlers: StreamHandlers,
): StreamHandle {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      if (!res.ok || !res.body) {
        const text = await res.text().catch(() => "");
        handlers.onError?.(new Error(`HTTP ${res.status}: ${text}`));
        return;
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      // Bug 2 fix: guard against double-invocation. The server sends an
      // explicit `event: done` block at end-of-turn, AND the read loop
      // also reaches `done === true` afterwards — the previous version
      // fired onDone in both places.
      let doneFired = false;
      const fireDone = () => {
        if (doneFired) return;
        doneFired = true;
        handlers.onDone?.();
      };
      // SSE events are separated by a blank line ("\n\n")
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let sepIdx: number;
        while ((sepIdx = buffer.indexOf("\n\n")) !== -1) {
          const block = buffer.slice(0, sepIdx);
          buffer = buffer.slice(sepIdx + 2);
          const ev = parseSSEBlock(block);
          if (ev) {
            handlers.onEvent(ev);
            if (ev.event === "done") {
              fireDone();
              return;
            }
          }
        }
      }
      fireDone();
    } catch (err: any) {
      if (err?.name === "AbortError") return;
      handlers.onError?.(err instanceof Error ? err : new Error(String(err)));
    }
  })();

  return {
    abort: () => controller.abort(),
  };
}

function parseSSEBlock(block: string): ChatSSEEvent | null {
  let event = "message";
  const dataLines: string[] = [];
  for (const line of block.split("\n")) {
    if (!line) continue;
    if (line.startsWith(":")) continue; // comment / heartbeat
    if (line.startsWith("event: ")) {
      event = line.slice(7).trim();
    } else if (line.startsWith("data: ")) {
      dataLines.push(line.slice(6));
    }
  }
  if (!dataLines.length) return null;
  let data: any;
  try {
    data = JSON.parse(dataLines.join("\n"));
  } catch {
    data = { _raw: dataLines.join("\n") };
  }
  return { event, data } as ChatSSEEvent;
}
