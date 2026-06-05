import { NavLink } from "react-router-dom";
import { MessageSquare, FolderTree, Search, BookOpen } from "lucide-react";

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-section">
        <div className="sidebar-title">主导航</div>
        <NavLink to="/chat" className="sidebar-item" end>
          <MessageSquare size={14} style={{ display: "inline", marginRight: 6, verticalAlign: -2 }} />
          对话
        </NavLink>
        <NavLink to="/browse" className="sidebar-item">
          <FolderTree size={14} style={{ display: "inline", marginRight: 6, verticalAlign: -2 }} />
          浏览 vault
        </NavLink>
        <NavLink to="/search" className="sidebar-item">
          <Search size={14} style={{ display: "inline", marginRight: 6, verticalAlign: -2 }} />
          搜索
        </NavLink>
      </div>

      <div className="sidebar-section">
        <div className="sidebar-title">示例城市</div>
        <NavLink to="/city/三亚市" className="sidebar-item">
          <BookOpen size={14} style={{ display: "inline", marginRight: 6, verticalAlign: -2 }} />
          三亚市
        </NavLink>
        <NavLink to="/city/海口市" className="sidebar-item">
          <BookOpen size={14} style={{ display: "inline", marginRight: 6, verticalAlign: -2 }} />
          海口市
        </NavLink>
      </div>

      <div className="sidebar-section">
        <div className="sidebar-title">关于</div>
        <div className="sidebar-item" style={{ color: "var(--fg-muted)", fontSize: 12 }}>
          v0.1.0 MVP
          <br />
          对话 · 读写 · 工具
        </div>
      </div>
    </aside>
  );
}
