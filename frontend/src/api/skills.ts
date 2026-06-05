import { request } from "./client";
import type { HealthzResponse, SessionSummary, SkillDetailResponse, SkillIndexEntry } from "../types/api";

export const skillsApi = {
  list(): Promise<{ count: number; skills: SkillIndexEntry[] }> {
    return request("/api/skills");
  },
  get(name: string): Promise<SkillDetailResponse> {
    return request(`/api/skills/${encodeURIComponent(name)}`);
  },
};

export const sessionsApi = {
  list(): Promise<{ count: number; sessions: SessionSummary[] }> {
    return request("/api/sessions");
  },
  create(title = "新对话"): Promise<SessionSummary> {
    return request("/api/sessions", { method: "POST", query: { title } });
  },
  delete(id: string): Promise<{ ok: boolean; id: string }> {
    return request(`/api/sessions/${encodeURIComponent(id)}`, { method: "DELETE" });
  },
};

export const systemApi = {
  healthz(): Promise<HealthzResponse> {
    return request("/api/healthz");
  },
};
