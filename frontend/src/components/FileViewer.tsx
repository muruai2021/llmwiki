import { useEffect, useState } from "react";
import { FolderOpen, FileText, FileCode, AlertTriangle } from "lucide-react";
import { vaultApi } from "../api/vault";
import { MarkdownView } from "./MarkdownView";
import { useVaultViewerStore } from "../store/useVaultViewerStore";
import type { FileContentResponse } from "../types/api";

/** Hard cap on what we render in the right pane (bytes).
 *  13 MB PDFs / huge CSVs would freeze the markdown parser. */
const MAX_RENDER_BYTES = 256 * 1024; // 256 KB

const MD_EXT = /\.(md|markdown|mdx)$/i;

/**
 * FileViewer — pure file-content viewer for the right column of the 3-column chat layout.
 * Reads selectedPath from the shared store and renders the file body.
 *
 * Safety: never feeds binary / oversized files to ReactMarkdown.
 *   - size > 256 KB → show a "too large" notice with raw head (first 8 KB).
 *   - non-text / non-md → render as <pre> (not markdown).
 *   - .md → ReactMarkdown.
 */
export function FileViewer() {
  const selectedPath = useVaultViewerStore((s) => s.selectedPath);
  const [file, setFile] = useState<FileContentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedPath) {
      setFile(null);
      setError(null);
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
        setFile(null);
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedPath]);

  if (!selectedPath) {
    return (
      <div className="vault-viewer-empty">
        <FolderOpen size={20} />
        <p>← 在左侧选一个文件</p>
      </div>
    );
  }
  if (loading) {
    return <div className="vault-viewer-loading">加载中…</div>;
  }
  if (error) {
    return <div className="vault-viewer-error">! {error}</div>;
  }
  if (!file) return null;

  const tooLarge = file.size > MAX_RENDER_BYTES;
  const isMd = MD_EXT.test(file.path);

  return (
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

      {tooLarge ? (
        <div className="vault-viewer-body">
          <div className="vault-viewer-warn">
            <AlertTriangle size={14} />
            <span>文件过大（{file.size} B），已跳过渲染。预览前 8 KB：</span>
          </div>
          <pre>{(file.raw || "").slice(0, 8 * 1024)}</pre>
        </div>
      ) : isMd ? (
        <div className="vault-viewer-body">
          <FileText size={12} style={{ marginRight: 4, opacity: 0.5 }} />
          {file.body ? <MarkdownView content={file.body} /> : <pre>{file.raw || ""}</pre>}
        </div>
      ) : (
        <div className="vault-viewer-body">
          <FileCode size={12} style={{ marginRight: 4, opacity: 0.5 }} />
          <pre>{file.raw || ""}</pre>
        </div>
      )}
    </>
  );
}
