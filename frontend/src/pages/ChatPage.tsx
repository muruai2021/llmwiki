import { ChatStream } from "../components/ChatStream";
import { VaultTree } from "../components/VaultTree";
import { FileViewer } from "../components/FileViewer";

/**
 * /chat — full-screen 3-column layout:
 *   left:   VaultTree (folder/file navigator)
 *   center: ChatStream (the chat itself)
 *   right:  FileViewer (preview of the currently selected file)
 *
 * The right AppShell chat-panel is automatically hidden on /chat routes
 * (see AppShell.tsx), so this is the only chat surface visible.
 */
export function ChatPage() {
  return (
    <div className="chat-3col">
      <aside className="chat-3col-tree">
        <VaultTree />
      </aside>
      <main className="chat-3col-stream">
        <ChatStream />
      </main>
      <aside className="chat-3col-viewer">
        <div className="chat-3col-viewer-head">FILE PREVIEW</div>
        <div className="chat-3col-viewer-body">
          <FileViewer />
        </div>
      </aside>
    </div>
  );
}
