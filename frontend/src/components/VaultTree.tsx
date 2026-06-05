import { useEffect, useState } from "react";
import { Folder, FolderOpen, File as FileIcon, RefreshCw } from "lucide-react";
import { vaultApi } from "../api/vault";
import { useVaultViewerStore } from "../store/useVaultViewerStore";
import type { FileNode } from "../types/api";

/** Directories hidden from the user-facing tree.
 *  raw/ is kept (read-only context for LLM) but tagged so children are greyed. */
const HIDDEN_DIRS = new Set([".obsidian", ".git", ".venv", "node_modules", "__pycache__", ".claude", ".claudian"]);

/** Max size of a file the tree will let the viewer open (bytes). */
const MAX_CLICKABLE_BYTES = 1 * 1024 * 1024; // 1 MB

/** Extensions the FileViewer knows how to render as text.
 *  Anything else is shown but disabled (binary files would just be garbage). */
const RENDERABLE_EXT = /\.(md|markdown|mdx|ya?ml|json|toml|ini|conf|cfg|env|sh|bash|zsh|ps1|bat|cmd|py|js|ts|tsx|jsx|mjs|cjs|go|rs|java|kt|scala|rb|php|css|scss|less|xml|svg|sql|graphql|proto|txt|log|diff|patch)$/i;

/**
 * VaultTree — pure tree component for the left column of the 3-column chat layout.
 * Selection is shared with FileViewer via useVaultViewerStore.
 */
export function VaultTree() {
  const selectedPath = useVaultViewerStore((s) => s.selectedPath);
  const select = useVaultViewerStore((s) => s.select);
  const [tree, setTree] = useState<FileNode | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = () => {
    vaultApi
      .tree("", 5)
      .then((r) => setTree(r.tree))
      .catch((e) => setError(String(e)));
  };

  useEffect(() => {
    refresh();
  }, []);

  return (
    <div className="vault-tree">
      <div className="vault-tree-head">
        <span>VAULT TREE</span>
        <button type="button" className="vault-refresh" onClick={refresh} title="刷新">
          <RefreshCw size={11} />
        </button>
      </div>
      {error && <div className="vault-tree-error">! {error}</div>}
      {tree ? (
        <div className="vault-tree-body">
          <FileTreeNode
            node={tree}
            depth={0}
            selectedPath={selectedPath}
            onSelect={select}
            defaultOpen
          />
        </div>
      ) : (
        <div className="vault-tree-loading">加载中…</div>
      )}
    </div>
  );
}

interface FileTreeNodeProps {
  node: FileNode;
  depth: number;
  selectedPath: string | null;
  onSelect: (path: string) => void;
  defaultOpen?: boolean;
}

export function FileTreeNode({ node, depth, selectedPath, onSelect, defaultOpen }: FileTreeNodeProps) {
  // Hide non-user directories entirely
  if (node.type === "dir" && HIDDEN_DIRS.has(node.name)) return null;

  const [open, setOpen] = useState(false);
  const isDir = node.type === "dir";
  const Icon = isDir ? (open ? FolderOpen : Folder) : FileIcon;
  const isSelected = selectedPath === node.path;
  const isRaw = isDir && node.name === "raw";
  const tooBig = !isDir && (node.size ?? 0) > MAX_CLICKABLE_BYTES;
  const notRenderable = !isDir && !RENDERABLE_EXT.test(node.name);
  return (
    <div className="vault-tree-node" style={{ paddingLeft: depth * 10 }}>
      <div
        className={`vault-tree-row ${isDir ? "vault-tree-row-dir" : "vault-tree-row-file"} ${isSelected ? "selected" : ""} ${isRaw ? "vault-tree-row-raw" : ""} ${tooBig ? "vault-tree-row-toobig" : ""} ${notRenderable ? "vault-tree-row-binary" : ""}`}
        title={
          tooBig
            ? `文件过大 (${node.size} B)，请在 Obsidian 中打开`
            : notRenderable
              ? `二进制文件，不在网页预览范围内`
              : undefined
        }
        onClick={() => {
          if (isDir) setOpen(!open);
          else if (tooBig || notRenderable) return;
          else onSelect(node.path);
        }}
      >
        <Icon size={11} style={{ flexShrink: 0, marginRight: 4 }} />
        <span className="vault-tree-name">{node.name}</span>
        {tooBig && <span className="vault-tree-suffix">{(node.size! / 1024 / 1024).toFixed(1)} MB</span>}
      </div>
      {isDir && open && node.children && (
        <div className="vault-tree-children">
          {node.children.map((child) => (
            <FileTreeNode
              key={child.path}
              node={child}
              depth={depth + 1}
              selectedPath={selectedPath}
              onSelect={onSelect}
              defaultOpen={defaultOpen}
            />
          ))}
        </div>
      )}
    </div>
  );
}
