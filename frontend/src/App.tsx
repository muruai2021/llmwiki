import { Routes, Route, Navigate } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { ChatPage } from "./pages/ChatPage";
import { BrowsePage } from "./pages/BrowsePage";
import { CityDetailPage } from "./pages/CityDetailPage";
import { SearchPage } from "./pages/SearchPage";
import { HeroPage } from "./pages/HeroPage";
import { CitiesGridPage } from "./pages/CitiesGridPage";
import { ComparePage } from "./pages/ComparePage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<HeroPage />} />
        <Route path="/cities" element={<CitiesGridPage />} />
        <Route path="/cities/:slug" element={<CityDetailPage />} />
        <Route path="/compare" element={<ComparePage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/chat/:sessionId" element={<ChatPage />} />
        <Route path="/browse" element={<BrowsePage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="*" element={<div className="p-6">404 — page not found</div>} />
        <Route path="/old" element={<Navigate to="/chat" replace />} />
      </Route>
    </Routes>
  );
}
