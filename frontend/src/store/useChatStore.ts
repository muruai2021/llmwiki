// Zustand chat state — messages, streaming, tool calls, sessions.

import { create, type StoreApi } from "zustand";
import { streamChat, type StreamHandle } from "../api/chat";
import { sessionsApi } from "../api/skills";
import type { ChatSSEEvent } from "../types/api";

export type Role = "user" | "assistant";

export interface ToolCallRecord {
  id: string;
  tool: string;
  args_preview: string;
  ok?: boolean;
  result_preview?: string;
  error?: string;
  status: "running" | "done" | "error";
}

export interface ChatMessage {
  id: string;
  role: Role;
  text: string; // accumulated text (assistant only)
  toolCalls: ToolCallRecord[];
  isStreaming: boolean; // assistant still being streamed
  error?: string;
  createdAt: number;
}

type SessionSummary = { id: string; title: string; message_count: number; updated_at: number };

export interface ChatState {
  sessionId: string | null;
  sessionTitle: string;
  messages: ChatMessage[];
  isStreaming: boolean;
  activeHandle: StreamHandle | null;
  sessions: SessionSummary[];

  // Actions
  loadSessions: () => Promise<void>;
  startNewSession: (title?: string) => Promise<void>;
  switchSession: (id: string) => void;
  deleteSession: (id: string) => Promise<void>;
  sendMessage: (text: string) => Promise<void>;
  stopStreaming: () => void;
  clearMessages: () => void;
}

function genId(): string {
  return Math.random().toString(36).slice(2, 14);
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessionId: null,
  sessionTitle: "新对话",
  messages: [],
  isStreaming: false,
  activeHandle: null,
  sessions: [],

  async loadSessions() {
    try {
      const { sessions } = await sessionsApi.list();
      set({ sessions });
    } catch {
      // ignore — sessions list is non-critical
    }
  },

  async startNewSession(title = "新对话") {
    try {
      const s = await sessionsApi.create(title);
      set({
        sessionId: s.id,
        sessionTitle: s.title,
        messages: [],
      });
      get().loadSessions();
    } catch {
      // Fallback: local-only session (no backend)
      set({
        sessionId: `local-${genId()}`,
        sessionTitle: title,
        messages: [],
      });
    }
  },

  switchSession(id) {
    const s = get().sessions.find((x) => x.id === id);
    set({
      sessionId: id,
      sessionTitle: s?.title || "对话",
      messages: [], // Phase 1: history not loaded on switch
    });
  },

  async deleteSession(id) {
    try {
      await sessionsApi.delete(id);
    } catch {
      // ignore
    }
    if (get().sessionId === id) {
      set({ sessionId: null, sessionTitle: "新对话", messages: [] });
    }
    get().loadSessions();
  },

  // Bug 1 fix: make sendMessage async and ensure a real session id is
  // committed BEFORE we open the SSE stream. Previously it kicked off
  // `sessionsApi.create(...)` and `streamChat(...)` in parallel, so the
  // chat sometimes went out with `session_id: null`, leaving the backend
  // to mint a fresh session that the frontend never tracked.
  async sendMessage(text) {
    const trimmed = text.trim();
    if (!trimmed) return;
    if (get().isStreaming) return;

    // Resolve a session id up front.
    let sid = get().sessionId;
    if (!sid) {
      try {
        const s = await sessionsApi.create(trimmed.slice(0, 30));
        sid = s.id;
        set({ sessionId: s.id, sessionTitle: s.title });
        get().loadSessions();
      } catch {
        sid = `local-${genId()}`;
        set({ sessionId: sid });
      }
    }

    const userMsg: ChatMessage = {
      id: genId(),
      role: "user",
      text: trimmed,
      toolCalls: [],
      isStreaming: false,
      createdAt: Date.now(),
    };
    const assistantMsg: ChatMessage = {
      id: genId(),
      role: "assistant",
      text: "",
      toolCalls: [],
      isStreaming: true,
      createdAt: Date.now(),
    };
    set({
      messages: [...get().messages, userMsg, assistantMsg],
      isStreaming: true,
      sessionTitle: get().sessionTitle === "新对话" ? trimmed.slice(0, 30) : get().sessionTitle,
    });

    const handle = streamChat(
      { message: trimmed, session_id: sid },
      {
        onEvent: (ev: ChatSSEEvent) => {
          applyEvent(set, get, ev);
        },
        onError: (err) => {
          set((s) => ({
            isStreaming: false,
            activeHandle: null,
            messages: s.messages.map((m) =>
              m.id === assistantMsg.id
                ? { ...m, isStreaming: false, error: String(err) }
                : m,
            ),
          }));
        },
        onDone: () => {
          set((s) => ({
            isStreaming: false,
            activeHandle: null,
            messages: s.messages.map((m) =>
              m.id === assistantMsg.id ? { ...m, isStreaming: false } : m,
            ),
          }));
          get().loadSessions();
        },
      },
    );
    set({ activeHandle: handle });
  },

  stopStreaming() {
    const h = get().activeHandle;
    if (h) h.abort();
    set((s) => ({
      isStreaming: false,
      activeHandle: null,
      messages: s.messages.map((m) => ({ ...m, isStreaming: false })),
    }));
  },

  clearMessages() {
    set({ messages: [], sessionId: null, sessionTitle: "新对话" });
  },
}));

// ----- Event application -----

type SetFn = StoreApi<ChatState>["setState"];

function applyEvent(set: SetFn, get: () => ChatState, ev: ChatSSEEvent) {
  // The last assistant message is the one being streamed
  const messages = [...get().messages];
  const lastIdx = messages.length - 1;
  const last = messages[lastIdx];
  if (!last || last.role !== "assistant") return;

  switch (ev.event) {
    case "message_start":
      // No-op for now; could capture message_id
      break;
    case "content_block_delta":
      if (ev.data.type === "text_delta") {
        const updated: ChatMessage = {
          ...last,
          text: (last.text || "") + ev.data.delta,
        };
        messages[lastIdx] = updated;
        set({ messages });
      }
      break;
    case "tool_executing":
      messages[lastIdx] = {
        ...last,
        toolCalls: [
          ...last.toolCalls,
          {
            id: ev.data.id,
            tool: ev.data.tool,
            args_preview: ev.data.args_preview,
            status: "running",
          },
        ],
      };
      set({ messages });
      break;
    case "tool_result": {
      const toolCalls: ToolCallRecord[] = last.toolCalls.map((tc) =>
        tc.id === ev.data.id
          ? {
              ...tc,
              ok: ev.data.ok,
              result_preview: ev.data.result_preview,
              error: ev.data.error ?? undefined,
              status: ev.data.ok ? "done" : "error",
            }
          : tc,
      );
      messages[lastIdx] = { ...last, toolCalls };
      set({ messages });
      break;
    }
    case "done":
    case "error":
      messages[lastIdx] = {
        ...last,
        isStreaming: false,
        ...(ev.event === "error" ? { error: ev.data.message } : {}),
      };
      set({ messages });
      break;
    default:
      break;
  }
}
