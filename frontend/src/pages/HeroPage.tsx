import { Link } from "react-router-dom";
import { MessageSquare, Building2, ArrowRight } from "lucide-react";
import { CITIES } from "../data/cities";

const QUICK_PROMPTS = [
  "海口市有什么人才引进政策？",
  "对比三亚和海口的招商政策",
  "列出 wiki/cities/ 下所有城市",
  "雄安新区央企有什么补贴？",
];

export function HeroPage() {
  return (
    <div className="hero-page">
      <div className="hero-tag">Issue 01 · Summer 2026</div>
      <div className="hero-vert">18°08′N · TROPIC OF CANCER · 109°31′E</div>

      <div className="hero-grid">
        <div className="hero-left">
          <div className="eyebrow">招商引力场 · Atlas</div>
          <h1 className="hero-title">
            <span style={{ display: "block" }}>在 <em>50</em> 座</span>
            <span style={{ display: "block" }}>城市上</span>
            <span style={{ display: "block" }}>重建<em style={{ color: "var(--sea)" }}>招商</em>的</span>
            <span style={{ display: "block" }}>
              <span className="underline">决策引力场</span>
            </span>
          </h1>
          <p className="hero-sub">
            招商引力场 是为招商决策而构建的 <b>AI 中枢</b>——以 <b>50 城政策</b>、<b>120 万字</b>、<b>1,335 条 wikilink</b>，
            让每一份判断建立在可比较的证据之上，而不是政策汇编。
          </p>

          <div className="hero-cta">
            <Link to="/chat" className="btn btn-primary">
              启动对话 <span className="arrow"><ArrowRight size={14} /></span>
            </Link>
            <Link to="/cities" className="btn btn-ghost">
              <Building2 size={14} /> 浏览 50 城 <span className="arrow">→</span>
            </Link>
          </div>

          <div className="hero-meta">
            <div className="hero-meta-item">
              <div className="num"><em>{CITIES.length}</em></div>
              <div className="lab">覆盖城市</div>
            </div>
            <div className="hero-meta-divider" />
            <div className="hero-meta-item">
              <div className="num"><em>229</em></div>
              <div className="lab">Wiki 页面</div>
            </div>
            <div className="hero-meta-divider" />
            <div className="hero-meta-item">
              <div className="num"><em>120<small>万</small></em></div>
              <div className="lab">总字数</div>
            </div>
            <div className="hero-meta-divider" />
            <div className="hero-meta-item">
              <div className="num"><em>1,335</em></div>
              <div className="lab">内部链接</div>
            </div>
          </div>
        </div>

        <div className="hero-right">
          <Compass />
        </div>
      </div>

      <div className="coord-strip">
        <div>
          <div className="k">MD</div>
          <div className="v">322 个</div>
        </div>
        <div>
          <div className="k">RAW</div>
          <div className="v">106 个</div>
        </div>
        <div>
          <div className="k">WIKI</div>
          <div className="v">229 个 · 120 万字</div>
        </div>
        <div>
          <div className="k">LINKS</div>
          <div className="v">1,335 条</div>
        </div>
        <div>
          <div className="k">STATUS</div>
          <div className="v" style={{ color: "var(--sea)" }}>● ONLINE</div>
        </div>
        <div>
          <div className="k">COORD</div>
          <div className="v">18°08′N · 109°31′E</div>
        </div>
      </div>

      <div className="hero-quicks">
        <div className="hero-quicks-title">试试这些问题</div>
        <div className="hero-quicks-list">
          {QUICK_PROMPTS.map((p) => (
            <Link key={p} to={`/chat?q=${encodeURIComponent(p)}`}>
              <span><MessageSquare size={12} style={{ marginRight: 8, color: "var(--coral)" }} /> {p}</span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

function Compass() {
  // Decorative SVG — concentric circles + crosshair + 18° label
  return (
    <div className="compass">
      <svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <circle cx="200" cy="200" r="180" fill="none" stroke="var(--ink)" strokeWidth="0.5" />
        <circle cx="200" cy="200" r="150" fill="none" stroke="var(--rule-2)" strokeWidth="0.5" strokeDasharray="2 4" />
        <circle cx="200" cy="200" r="120" fill="none" stroke="var(--ink)" strokeWidth="0.5" />
        <circle cx="200" cy="200" r="90" fill="none" stroke="var(--rule-2)" strokeWidth="0.5" strokeDasharray="2 4" />
        <circle cx="200" cy="200" r="60" fill="none" stroke="var(--ink)" strokeWidth="0.5" />
        <circle cx="200" cy="200" r="30" fill="none" stroke="var(--coral)" strokeWidth="1" opacity="0.5" />
        {/* Crosshair lines */}
        <line x1="20" y1="200" x2="380" y2="200" stroke="var(--rule)" strokeWidth="0.5" />
        <line x1="200" y1="20" x2="200" y2="380" stroke="var(--rule)" strokeWidth="0.5" />
        {/* 18° latitude line (coral) */}
        <line x1="20" y1="160" x2="380" y2="160" stroke="var(--coral)" strokeWidth="1.2" opacity="0.6" />
        {/* N / S / E / W labels */}
        <text x="200" y="14" textAnchor="middle" fontFamily="JetBrains Mono" fontSize="9" fill="var(--mute-2)" letterSpacing="2">N</text>
        <text x="200" y="394" textAnchor="middle" fontFamily="JetBrains Mono" fontSize="9" fill="var(--mute-2)" letterSpacing="2">S</text>
        <text x="386" y="204" textAnchor="end" fontFamily="JetBrains Mono" fontSize="9" fill="var(--mute-2)" letterSpacing="2">E</text>
        <text x="14" y="204" fontFamily="JetBrains Mono" fontSize="9" fill="var(--mute-2)" letterSpacing="2">W</text>
        {/* 18° coral label */}
        <text x="206" y="156" fontFamily="JetBrains Mono" fontSize="10" fill="var(--coral)" letterSpacing="2" fontWeight="700">18°</text>
        {/* City dots (decorative) */}
        <circle cx="200" cy="200" r="3" fill="var(--coral)" />
        <circle cx="280" cy="240" r="2" fill="var(--ink)" />
        <circle cx="120" cy="180" r="2" fill="var(--ink)" />
        <circle cx="240" cy="120" r="2" fill="var(--ink)" />
        <circle cx="160" cy="280" r="2" fill="var(--ink)" />
        <circle cx="320" cy="160" r="2" fill="var(--ink)" />
      </svg>
      <div className="compass-center">
        <div className="lab">TROPIC OF CANCER</div>
        <div className="val">18°<sup>N</sup></div>
        <div className="sub">LLMWIKI · 2026</div>
      </div>
    </div>
  );
}
