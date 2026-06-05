import { useEffect, useState } from "react";
import { systemApi } from "../api/skills";
import type { HealthzResponse } from "../types/api";

/**
 * Top-of-page terminal status bar (18°N style).
 * Black background · mono caps · coral pulse dot · brand tags.
 * Sits above the Topbar.
 */
export function StatusBar() {
  const [health, setHealth] = useState<HealthzResponse | null>(null);
  const today = new Date().toISOString().slice(0, 10);

  useEffect(() => {
    systemApi.healthz().then(setHealth).catch(() => setHealth(null));
  }, []);

  return (
    <div className="status-bar" role="status" aria-label="状态栏">
      <div className="left">
        <span className="dot" />
        <span>
          木汝科技 <span className="sep">/</span> <span className="tag">MURU AI</span>
        </span>
        <span className="sep">·</span>
        <span>LLMWIKI <span className="sep">/</span> <span className="tag">政策知识库 v3.2</span></span>
        <span className="sep hide-md">·</span>
        <span className="hide-md">SYS <span className="sep">/</span> ONLINE</span>
      </div>
      <div className="right">
        <span className="hide-md">DATA <span className="sep">/</span> {today}</span>
        <span className="sep">·</span>
        <span>
          {health ? (
            <>
              {health.config.llm_model} <span className="sep">/</span>{" "}
              <span style={{ color: health.config.has_api_key ? "var(--coral)" : "var(--mute-2)" }}>
                {health.config.has_api_key ? "key ✓" : "no key"}
              </span>
            </>
          ) : (
            <span>connecting…</span>
          )}
        </span>
        <span className="sep">·</span>
        <span>© 2026</span>
      </div>
    </div>
  );
}
