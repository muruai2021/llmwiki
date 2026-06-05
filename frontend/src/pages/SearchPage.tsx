import { useState } from "react";
import { Search as SearchIcon } from "lucide-react";
import { vaultApi } from "../api/vault";
import type { SearchResponse } from "../types/api";

export function SearchPage() {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!q.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const r = await vaultApi.search(q.trim(), { maxResults: 100 });
      setResults(r);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6" style={{ maxWidth: 900, margin: "0 auto" }}>
      <h2 style={{ marginTop: 0 }}>搜索 vault</h2>
      <form onSubmit={submit} style={{ display: "flex", gap: 8 }}>
        <input
          type="text"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="输入关键词..."
          style={{
            flex: 1,
            padding: "8px 12px",
            border: "1px solid var(--border)",
            borderRadius: 6,
            background: "var(--bg-elevated)",
            color: "var(--fg)",
          }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: "8px 16px",
            background: "var(--accent)",
            color: "var(--accent-fg)",
            border: 0,
            borderRadius: 6,
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <SearchIcon size={14} /> 搜索
        </button>
      </form>
      {error && <div className="error" style={{ marginTop: 12 }}>{error}</div>}
      {results && (
        <div style={{ marginTop: 16 }}>
          <div style={{ color: "var(--fg-muted)", fontSize: 12 }}>
            找到 {results.count} 个匹配
          </div>
          {results.hits.map((h, i) => (
            <div
              key={i}
              style={{
                padding: "10px 0",
                borderBottom: "1px solid var(--border)",
              }}
            >
              <div style={{ fontSize: 13, marginBottom: 4 }}>
                <a
                  href={`#/browse?path=${encodeURIComponent(h.path)}`}
                  style={{ fontFamily: "var(--font-mono)" }}
                >
                  {h.path}:{h.line}
                </a>
              </div>
              <div style={{ fontSize: 13, color: "var(--fg-muted)" }}>{h.snippet}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
