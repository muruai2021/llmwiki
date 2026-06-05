import { useEffect, useState } from "react";
import { vaultApi } from "../api/vault";
import type { ResolvedWikilink } from "../types/api";

interface Props {
  target: string;
  /**
   * If true, do NOT pre-fetch on mount — only resolve on click. This is the
   * default for the file viewer / chat (avoids 225 simultaneous fetches when
   * rendering a file with hundreds of wikilinks).
   * If false, pre-resolve on mount (eager — for places where the resolved
   * state matters for visual styling, like chat inline links).
   */
  lazy?: boolean;
}

/**
 * Render a [[wikilink]] as a clickable span. On click, resolves the target
 * and navigates within the app.
 *
 * Default mode is `lazy`: no mount-time fetch. This is critical for
 * performance when a file has many wikilinks (e.g. wiki/index.md has 225).
 *
 * Module-level resolution cache + the API client's in-flight dedup make
 * repeated clicks for the same target O(1).
 */
export function WikilinkSpan({ target, lazy = true }: Props) {
  const [resolved, setResolved] = useState<ResolvedWikilink | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (lazy) return;
    let cancelled = false;
    setLoading(true);
    vaultApi
      .resolveWikilink(decodeURIComponent(target))
      .then((r) => {
        if (!cancelled) setResolved(r.resolved);
      })
      .catch(() => {
        if (!cancelled) setResolved({ link: target, resolved: null, exists: false, is_external: false });
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [target, lazy]);

  const handleClick = async (e: React.MouseEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const r = await vaultApi.resolveWikilink(decodeURIComponent(target));
      setResolved(r.resolved);
      navigate(r.resolved);
    } catch {
      setResolved({ link: target, resolved: null, exists: false, is_external: false });
    } finally {
      setLoading(false);
    }
  };

  const navigate = (r: ResolvedWikilink | null) => {
    if (!r?.resolved) return;
    const m =
      r.resolved.match(/^wiki\/cities\/([^/]+)$/) ||
      r.resolved.match(/^wiki\/([^/]+)$/);
    if (m) {
      window.location.hash = `#/city/${encodeURIComponent(m[1])}`;
    } else {
      window.location.hash = `#/browse?path=${encodeURIComponent(r.resolved)}`;
    }
  };

  const isResolved = resolved && !loading;
  const isBroken = resolved && !loading && !resolved.exists;
  const cls = `wikilink ${loading ? "wikilink-loading" : ""} ${isBroken ? "wikilink-broken" : ""}`;

  return (
    <a
      className={cls}
      href="#"
      onClick={handleClick}
      title={isResolved ? `→ ${resolved?.resolved}` : loading ? "解析中…" : `未解析: ${target}`}
    >
      {target}
    </a>
  );
}
