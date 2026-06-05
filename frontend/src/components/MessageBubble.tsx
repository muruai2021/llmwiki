import { MarkdownView } from "./MarkdownView";
import { ToolCallCard } from "./ToolCallCard";
import { User, Bot } from "lucide-react";
import type { ChatMessage } from "../store/useChatStore";

export function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";
  return (
    <div className={`bubble ${isUser ? "bubble-user" : "bubble-assistant"}`}>
      <div className="bubble-avatar">
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>
      <div className="bubble-content">
        {msg.text && (
          <div className="bubble-text">
            {isUser ? (
              <div style={{ whiteSpace: "pre-wrap" }}>{msg.text}</div>
            ) : (
              <MarkdownView content={msg.text} />
            )}
          </div>
        )}
        {msg.toolCalls.length > 0 && (
          <div className="bubble-tools">
            {msg.toolCalls.map((tc) => (
              <ToolCallCard key={tc.id} call={tc} />
            ))}
          </div>
        )}
        {msg.error && (
          <div className="bubble-error">⚠️ {msg.error}</div>
        )}
        {msg.isStreaming && !msg.text && msg.toolCalls.length === 0 && (
          <div className="bubble-typing">…</div>
        )}
      </div>
    </div>
  );
}
