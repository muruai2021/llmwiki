import { useState } from "react";
import { MessageSquare, FolderOpen } from "lucide-react";
import { ChatStream } from "./ChatStream";
import { VaultPanel } from "./VaultPanel";

type Tab = "chat" | "vault";

/**
 * ChatPanel — right-side persistent panel.
 * Hosts two tabs:
 *   - "聊天": full chat (ChatStream) with the vault as LLM tool
 *   - "文件": VaultPanel — folder tree + file content viewer
 *
 * Switching to 文件 lets the user browse / preview the vault directly,
 * mirroring the 18°N design's KB § 005 layout.
 */
export function ChatPanel() {
  const [tab, setTab] = useState<Tab>("chat");

  return (
    <div className="chat-container">
      <div className="chat-tabs" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={tab === "chat"}
          className={`chat-tab ${tab === "chat" ? "active" : ""}`}
          onClick={() => setTab("chat")}
        >
          <MessageSquare size={11} /> 聊天
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === "vault"}
          className={`chat-tab ${tab === "vault" ? "active" : ""}`}
          onClick={() => setTab("vault")}
        >
          <FolderOpen size={11} /> 文件
        </button>
      </div>
      <div className="chat-tab-body">
        {tab === "chat" ? <ChatStream /> : <VaultPanel />}
      </div>
    </div>
  );
}
