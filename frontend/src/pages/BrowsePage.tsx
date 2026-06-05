import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { vaultApi } from "../api/vault";
import { FileTree } from "../components/FileTree";
import { MarkdownView } from "../components/MarkdownView";
import type { FileContentResponse, FileNode } from "../types/api";

export function BrowsePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const pathParam = searchParams.get("path") ?? "";
  const [tree, setTree] = useState<FileNode | null>(null);
  const [selected, setSelected] = useState<FileContentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // depth 5 = root → wiki/raw/concepts → cities → <城市> → policies/tax/talent/park → file.
    // Anything shallower truncates the leaf-level `.md` files inside topics / policies.
    vaultApi
      .tree("", 5)
      .then((r) => setTree(r.tree))
      .catch((e) => setError(String(e)));
  }, []);

  // Bug 3 fix: when the URL contains `?path=...` (e.g. from a wikilink click),
  // load that file automatically. Update the URL on manual selection so the
  // page is shareable / back-button friendly.
  useEffect(() => {
    if (!pathParam) {
      setSelected(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    vaultApi
      .getFile(pathParam)
      .then((file) => {
        if (cancelled) return;
        setSelected(file);
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
  }, [pathParam]);

  const onSelect = (node: FileNode) => {
    if (node.type !== "file") return;
    setSearchParams({ path: node.path }, { replace: false });
  };

  return (
    <div className="browse-layout">
      <div className="browse-tree">
        <h3>Vault</h3>
        {error && <div className="error">{error}</div>}
        {tree && <FileTree node={tree} onSelect={onSelect} depth={0} />}
      </div>
      <div className="browse-viewer">
        {loading && <div>加载中…</div>}
        {!loading && !selected && (
          <div style={{ padding: 32, color: "var(--fg-muted)" }}>
            ← 在左侧选一个文件
          </div>
        )}
        {!loading && selected && (
          <div className="browse-file">
            <div className="browse-file-header">
              <code>{selected.path}</code>
              <span style={{ marginLeft: 12, color: "var(--fg-muted)", fontSize: 12 }}>
                {selected.size} bytes
              </span>
            </div>
            {selected.has_frontmatter && selected.frontmatter && (
              <details className="browse-frontmatter">
                <summary>frontmatter</summary>
                <pre>{JSON.stringify(selected.frontmatter, null, 2)}</pre>
              </details>
            )}
            {selected.body && <MarkdownView content={selected.body} />}
            {!selected.body && selected.raw && (
              <pre style={{ whiteSpace: "pre-wrap" }}>{selected.raw}</pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
