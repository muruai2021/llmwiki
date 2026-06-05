import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { GitCompareArrows, ArrowLeft } from "lucide-react";
import { vaultApi } from "../api/vault";
import { MarkdownView } from "../components/MarkdownView";
import { CITY_BY_SLUG } from "../data/cities";
import { useCompareStore, COMPARE_MAX } from "../store/useCompareStore";
import type { FileContentResponse } from "../types/api";

const COORDS: Record<string, string> = {
  "三亚市": "18°14′N · 109°31′E",
  "海口市": "20°02′N · 110°20′E",
  "北京市": "39°54′N · 116°23′E",
  "上海市": "31°14′N · 121°29′E",
  "重庆市": "29°33′N · 106°33′E",
  "天津市": "39°08′N · 117°11′E",
  "深圳市": "22°33′N · 114°05′E",
  "广州市": "23°08′N · 113°16′E",
};

export function CityDetailPage() {
  const { slug = "" } = useParams<{ slug: string }>();
  const decoded = decodeURIComponent(slug);
  const meta = CITY_BY_SLUG[decoded];
  const [file, setFile] = useState<FileContentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const inCompare = useCompareStore((s) => s.slugs.includes(decoded));
  const compareCount = useCompareStore((s) => s.slugs.length);
  const toggleCompare = useCompareStore((s) => s.toggle);

  useEffect(() => {
    // Vault layout: wiki/cities/<城市>/<城市>.md  (each city is a folder)
    const candidates = [
      `wiki/cities/${decoded}/${decoded}.md`,
      `wiki/cities/${decoded}.md`,
      `wiki/${decoded}.md`,
      `cities/${decoded}.md`,
    ];
    (async () => {
      for (const path of candidates) {
        try {
          const f = await vaultApi.getFile(path);
          if (f.exists) {
            setFile(f);
            setError(null);
            return;
          }
        } catch {
          // try next
        }
      }
      setError(`未找到城市: ${decoded}`);
    })();
  }, [decoded]);

  if (error) {
    return (
      <div className="p-6">
        <h1>{decoded}</h1>
        <div className="error">{error}</div>
        <p style={{ marginTop: 12, fontFamily: "var(--mono)", fontSize: 11, color: "var(--mute)", letterSpacing: ".12em" }}>
          尝试了: <code>wiki/cities/{decoded}.md</code>, <code>wiki/{decoded}.md</code>
        </p>
        <p style={{ marginTop: 12 }}>
          <Link to="/cities">← 返回 50 城</Link>
        </p>
      </div>
    );
  }
  if (!file) {
    return <div className="p-6" style={{ fontFamily: "var(--mono)", fontSize: 12, color: "var(--mute)", letterSpacing: ".12em", textTransform: "uppercase" }}>加载中…</div>;
  }

  const compareDisabled = !inCompare && compareCount >= COMPARE_MAX;
  const isFeatured = decoded === "三亚市";
  const coord = COORDS[decoded] || (meta ? `${meta.province} · CHN` : "—");

  return (
    <div className="city-detail">
      <div className="city-detail-head">
        <div className="city-detail-header-row">
          <Link to="/cities" className="city-detail-back">
            <ArrowLeft size={12} /> 50 城
          </Link>
          <button
            type="button"
            className={`city-detail-compare-btn ${inCompare ? "active" : ""}`}
            onClick={() => toggleCompare(decoded)}
            disabled={compareDisabled}
            title={
              compareDisabled
                ? `对比列表已满（${COMPARE_MAX} 城）`
                : inCompare ? "从对比中移除" : "加入对比"
            }
          >
            <GitCompareArrows size={12} />
            {inCompare ? "已加入对比" : "加入对比"}
            {compareCount > 0 && <span> · {compareCount}/{COMPARE_MAX}</span>}
          </button>
        </div>
        <div className="city-detail-coord">
          <span>{coord}</span>
          {isFeatured && <span style={{ color: "var(--coral)" }}>★ 招商旗舰</span>}
        </div>
        <h1 className="city-detail-name">{file.frontmatter?.title as string || decoded}</h1>
        {meta && (
          <div className="city-detail-en">{meta.tier} · {meta.province} · {meta.region}</div>
        )}
        <div className="city-detail-tags">
          {isFeatured && <span className="city-detail-tag host">HOST</span>}
          {meta?.tags.map((t) => (
            <span key={t} className="city-detail-tag">{t}</span>
          ))}
        </div>
      </div>

      <div className="city-detail-stats">
        <div>
          <div className="k">等级</div>
          <div className="v">{meta?.tier || "—"}</div>
        </div>
        <div>
          <div className="k">区域</div>
          <div className="v">{meta?.region || "—"}</div>
        </div>
        <div>
          <div className="k">省/直辖市</div>
          <div className="v">{meta?.province || "—"}</div>
        </div>
        <div>
          <div className="k">路径</div>
          <div className="v" style={{ fontFamily: "var(--mono)", fontSize: 12, fontWeight: 500, color: "var(--mute)", letterSpacing: ".04em" }}>
            {file.path}
          </div>
        </div>
      </div>

      <div className="city-detail-body">
        {file.body && <MarkdownView content={file.body} />}
      </div>
    </div>
  );
}
