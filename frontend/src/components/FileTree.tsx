import { useState } from "react";
import { Folder, FolderOpen, File as FileIcon } from "lucide-react";
import type { FileNode } from "../types/api";

interface Props {
  node: FileNode;
  depth?: number;
  onSelect?: (node: FileNode) => void;
}

const RENDERABLE_EXT = /\.(md|markdown|mdx|ya?ml|json|toml|ini|conf|cfg|env|sh|bash|zsh|ps1|bat|cmd|py|js|ts|tsx|jsx|mjs|cjs|go|rs|java|kt|scala|rb|php|css|scss|less|xml|svg|sql|graphql|proto|txt|log|diff|patch)$/i;

/**
 * Self-contained recursive file tree (~80 LOC).
 * - dirs default CLOSED (user clicks to expand)
 * - binary / oversized files are visible but not clickable
 * - clicking a file calls onSelect
 */
export function FileTree({ node, depth = 0, onSelect }: Props) {
  const [open, setOpen] = useState(false);
  const isDir = node.type === "dir";
  const notRenderable = !isDir && !RENDERABLE_EXT.test(node.name);
  const Icon = isDir ? (open ? FolderOpen : Folder) : FileIcon;
  return (
    <div className="tree-node" style={{ paddingLeft: depth * 12 }}>
      <div
        className={`tree-row ${isDir ? "tree-row-dir" : "tree-row-file"} ${notRenderable ? "tree-row-binary" : ""}`}
        title={notRenderable ? "二进制文件，不在网页预览范围内" : undefined}
        onClick={() => {
          if (isDir) setOpen(!open);
          else if (notRenderable) return;
          else onSelect?.(node);
        }}
      >
        <Icon size={13} style={{ flexShrink: 0, marginRight: 4 }} />
        <span className="tree-name">{node.name}</span>
        {!isDir && node.size != null && (
          <span className="tree-size">{formatSize(node.size)}</span>
        )}
      </div>
      {isDir && open && node.children && (
        <div className="tree-children">
          {node.children.map((child) => (
            <FileTree
              key={child.path}
              node={child}
              depth={depth + 1}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
