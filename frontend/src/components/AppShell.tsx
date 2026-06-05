import { Outlet, useLocation } from "react-router-dom";
import { Topbar } from "./Topbar";
import { StatusBar } from "./StatusBar";
import { ChatPanel } from "./ChatPanel";

/**
 * AppShell — persistent layout for the entire SPA.
 *   StatusBar (top terminal bar) + Topbar (top nav)
 *   + <Outlet /> (left = current tab content)
 *   + ChatPanel (right = persistent chat / vault viewer)
 *
 * The right-side chat panel is hidden on `/chat*` routes because the chat fills
 * the main area there; we don't want two input bars on screen.
 *
 * Responsive: < 1100px the chat collapses (hidden).
 *
 * The full-page <div class="noise" /> overlay is a fixed-position
 * fractalNoise SVG from the 18°N design system, sitting at z-index 9999
 * to give the paper texture across the whole window.
 */
export function AppShell() {
  const { pathname } = useLocation();
  const isChatRoute = pathname.startsWith("/chat");

  return (
    <div className="app-shell">
      <div className="noise" aria-hidden="true" />
      <StatusBar />
      <Topbar />
      <div className="app-body">
        <main className="app-main">
          <Outlet />
        </main>
        {!isChatRoute && (
          <aside className="app-chat" aria-label="对话面板">
            <ChatPanel />
          </aside>
        )}
      </div>
    </div>
  );
}
