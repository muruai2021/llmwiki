import { useEffect, useState } from "react";
import { Folder, FolderOpen, File as FileIcon, RefreshCw } from "lucide-react";
import { vaultApi } from "../api/vault";
import { MarkdownView } from "./MarkdownView";
import type { FileContentResponse, FileNode } from "../types/api";

/**
 * VaultPanel — compact folder tree + file viewer for the right-side chat panel.
 * Designed for the 420px-wide chat column.
 */
export function VaultPanel() {
  const [tree, setTree] = useState<FileNode | null>(null);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [file, setFile] = useState<FileContentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshTree = () => {
    vaultApi
      .tree("", 5)
      .then((r) => setTree(r.tree))
      .catch((e) => setError(String(e)));
  };

  useEffect(() => {
    refreshTree();
  }, []);

  useEffect(() => {
    if (!selectedPath) {
      setFile(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    vaultApi
      .getFile(selectedPath)
      .then((f) => {
        if (cancelled) return;
        setFile(f);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(String(e));
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedPath]);

  return (
    <div className="vault-panel">
      <div className="vault-tree">
        <div className="vault-tree-head">
          <span>VAULT TREE</span>
          <button type="button" className="vault-refresh" onClick={refreshTree} title="刷新">
            <RefreshCw size={11} />
          </button>
        </div>
        {error && <div className="vault-tree-error">! {error}</div>}
        {tree ? (
          <FileTree
            node={tree}
            depth={0}
            selectedPath={selectedPath}
            onSelect={setSelectedPath}
          />
        ) : (
          <div className="vault-tree-loading">加载中…</div>
        )}
      </div>
      <div className="vault-viewer">
        {!selectedPath && (
          <div className="vault-viewer-empty">
            <FolderOpen size={20} />
            <p>← 在左侧选一个文件</p>
          </div>
        )}
        {loading && <div className="vault-viewer-loading">加载中…</div>}
        {selectedPath && !loading && file && (
          <>
            <div className="vault-viewer-head">
              <code>{file.path}</code>
              <span>{file.size} B</span>
            </div>
            {file.has_frontmatter && file.frontmatter && (
              <details className="vault-viewer-fm">
                <summary>frontmatter</summary>
                <pre>{JSON.stringify(file.frontmatter, null, 2)}</pre>
              </details>
            )}
            <div className="vault-viewer-body">
              {file.body ? (
                <MarkdownView content={file.body} />
              ) : (
                <pre>{file.raw || ""}</pre>
              )}
            </div>
          </>
        )}
        {selectedPath && !loading && error && (
          <div className="vault-viewer-empty">! {error}</div>
        )}
      </div>
    </div>
  );
}

interface FileTreeProps {
  node: FileNode;
  depth: number;
  selectedPath: string | null;
  onSelect: (path: string) => void;
}

const RENDERABLE_EXT = /\.(md|markdown|mdx|ya?ml|json|toml|ini|conf|cfg|env|sh|bash|zsh|ps1|bat|cmd|py|js|ts|tsx|jsx|mjs|cjs|go|rs|java|kt|scala|rb|php|css|scss|less|xml|svg|sql|graphql|proto|txt|log|diff|patch)$/i;

function FileTree({ node, depth, selectedPath, onSelect }: FileTreeProps) {
  const [open, setOpen] = useState(false);
  const isDir = node.type === "dir";
  const notRenderable = !isDir && !RENDERABLE_EXT.test(node.name);
  const Icon = isDir ? (open ? FolderOpen : Folder) : FileIcon;
  const isSelected = selectedPath === node.path;
  return (
    <div className="vault-tree-node" style={{ paddingLeft: depth * 8 }}>
      <div
        className={`vault-tree-row ${isDir ? "vault-tree-row-dir" : "vault-tree-row-file"} ${isSelected ? "selected" : ""} ${notRenderable ? "vault-tree-row-binary" : ""}`}
        title={notRenderable ? "二进制文件，不在网页预览范围内" : undefined}
        onClick={() => {
          if (isDir) setOpen(!open);
          else if (notRenderable) return;
          else onSelect(node.path);
        }}
      >
        <Icon size={11} style={{ flexShrink: 0, marginRight: 4 }} />
        <span className="vault-tree-name">{node.name}</span>
      </div>
      {isDir && open && node.children && (
        <div className="vault-tree-children">
          {node.children.map((child) => (
            <FileTree
              key={child.path}
              node={child}
              depth={depth + 1}
              selectedPath={selectedPath}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}
