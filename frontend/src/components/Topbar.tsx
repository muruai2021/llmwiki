import { useEffect, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { Home, Building2, GitCompareArrows, MessageSquare } from "lucide-react";
import { systemApi } from "../api/skills";
import type { HealthzResponse } from "../types/api";

export function Topbar() {
  const [health, setHealth] = useState<HealthzResponse | null>(null);
  const loc = useLocation();

  useEffect(() => {
    systemApi.healthz().then(setHealth).catch(() => setHealth(null));
  }, []);

  return (
    <header className="topbar">
      <Link to="/" className="topbar-brand" style={{ textDecoration: "none", color: "inherit" }}>
        <div className="topbar-brand-mark" aria-hidden="true" />
        <div className="topbar-brand-text">
          <span className="zh">招商引力场</span>
          <span className="en">招商政策智能体 · Atlas · 木汝科技 Muru AI</span>
        </div>
      </Link>

      <nav className="topbar-nav" aria-label="主导航">
        <NavLink to="/" end className="topbar-nav-item">
          <Home size={14} /> <span>首页</span>
        </NavLink>
        <NavLink to="/cities" className="topbar-nav-item">
          <Building2 size={14} /> <span>50 城</span>
        </NavLink>
        <NavLink to="/compare" className="topbar-nav-item">
          <GitCompareArrows size={14} /> <span>对比</span>
        </NavLink>
        <NavLink to="/chat" className="topbar-nav-item">
          <MessageSquare size={14} /> <span>聊天</span>
        </NavLink>
      </nav>

      <div className="topbar-meta">
        {health ? (
          <>
            <span className="dot" />
            <span>ONLINE · {health.config.llm_model}</span>
            <span style={{ color: "var(--border-strong)" }}>·</span>
            <span>{health.skills_loaded} skills</span>
            <span style={{ color: "var(--border-strong)" }}>·</span>
            <span style={{ color: health.config.has_api_key ? "var(--sea)" : "var(--danger)" }}>
              {health.config.has_api_key ? "key ✓" : "no key"}
            </span>
            {!loc.pathname.startsWith("/browse") && !loc.pathname.startsWith("/search") && (
              <>
                <span style={{ color: "var(--border-strong)" }}>·</span>
                <Link to="/browse">浏览</Link>
                <span style={{ color: "var(--border-strong)" }}>·</span>
                <Link to="/search">搜索</Link>
              </>
            )}
          </>
        ) : (
          <span>connecting…</span>
        )}
      </div>
    </header>
  );
}
