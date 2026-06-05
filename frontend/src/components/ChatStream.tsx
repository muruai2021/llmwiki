import { useEffect, useRef, useState } from "react";
import { Send, Square, Plus, MessageSquare } from "lucide-react";
import { useChatStore } from "../store/useChatStore";
import { MessageBubble } from "./MessageBubble";

const QUICK_PROMPTS = [
  "海口市有什么人才引进政策？",
  "列出 wiki/cities/ 下所有城市",
  "对比三亚和海口的招商政策",
];

export function ChatStream() {
  const {
    messages,
    isStreaming,
    sendMessage,
    stopStreaming,
    startNewSession,
    sessionTitle,
    sessions,
    loadSessions,
  } = useChatStore();
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const submit = () => {
    if (!input.trim() || isStreaming) return;
    sendMessage(input);
    setInput("");
  };

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="chat-title-wrap">
          <div className="chat-avatar">政</div>
          <div>
            <div className="chat-title">{sessionTitle}</div>
            <div className="chat-sub">LLMWIKI AGENT · ONLINE</div>
          </div>
        </div>
        <div className="chat-actions">
          <button
            className="btn-icon"
            onClick={() => startNewSession()}
            title="新对话"
          >
            <Plus size={11} /> 新对话
          </button>
          <span className="chat-session-count">
            <MessageSquare size={11} /> {sessions.length}
          </span>
        </div>
      </div>

      <div className="chat-messages" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="chat-empty">
            <h2>开始一个对话</h2>
            <p>试试：</p>
            <ul>
              {QUICK_PROMPTS.map((p) => (
                <li key={p} onClick={() => { setInput(p); }} style={{ cursor: "pointer" }}>
                  {p}
                </li>
              ))}
            </ul>
            <div className="quick">
              {QUICK_PROMPTS.map((p) => (
                <button key={p} type="button" onClick={() => sendMessage(p)}>
                  {p}
                </button>
              ))}
            </div>
            <p style={{ marginTop: 24, fontSize: 11, letterSpacing: ".04em" }}>
              我可以读取/修改 vault 下的任何文件（除了 raw/），
              也可以跑 lint、graph_audit 等白名单脚本。
            </p>
          </div>
        )}
        {messages.map((m) => (
          <MessageBubble key={m.id} msg={m} />
        ))}
      </div>

      <div className="chat-input-bar">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKey}
          placeholder={isStreaming ? "正在生成中..." : "输入消息，回车发送，Shift+Enter 换行"}
          rows={2}
          disabled={isStreaming}
        />
        {isStreaming ? (
          <button className="btn-stop" onClick={stopStreaming} title="停止">
            <Square size={12} /> 停止
          </button>
        ) : (
          <button className="btn-send" onClick={submit} disabled={!input.trim()}>
            <Send size={12} /> 发送
          </button>
        )}
      </div>
    </div>
  );
}
