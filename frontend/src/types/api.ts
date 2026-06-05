// ----- Shared API types -----

export interface FileNode {
  name: string;
  path: string;
  type: "file" | "dir";
  children?: FileNode[] | null;
  size?: number | null;
}

export interface TreeResponse {
  root: string;
  tree: FileNode;
}

export interface FileContentResponse {
  path: string;
  exists: boolean;
  raw: string | null;
  frontmatter: Record<string, unknown> | null;
  body: string | null;
  has_frontmatter: boolean;
  size: number;
  modified: number | null;
}

export interface SearchHit {
  path: string;
  line: number;
  snippet: string;
  match_start: number;
  match_end: number;
}

export interface SearchResponse {
  query: string;
  count: number;
  hits: SearchHit[];
}

export interface ResolvedWikilink {
  link: string;
  resolved: string | null;
  exists: boolean;
  is_external: boolean;
}

export interface SkillIndexEntry {
  name: string;
  description: string;
  path: string;
  size: number;
}

export interface SkillDetailResponse extends SkillIndexEntry {
  body: string;
  frontmatter: Record<string, unknown>;
}

export interface SessionSummary {
  id: string;
  title: string;
  created_at: number;
  updated_at: number;
  message_count: number;
}

export interface HealthzResponse {
  ok: boolean;
  version: string;
  vault_path: string;
  vault_exists: boolean;
  model: string;
  skills_loaded: number;
  skill_names: string[];
  config: {
    vault_root: string;
    llm_model: string;
    llm_base_url: string;
    has_api_key: boolean;
    debug: boolean;
  };
  prompt_report: {
    today: string;
    claude_md_bytes: number;
    memory_md_bytes: number;
    skills_count: number;
    skill_names: string[];
  };
}

// ----- Chat SSE events -----

export type ChatSSEEvent =
  | { event: "message_start"; data: { session_id: string; message_id: string } }
  | {
      event: "content_block_start";
      data: { type: "text" | "tool_use"; index: number; name?: string; id?: string };
    }
  | {
      event: "content_block_delta";
      data: { type: "text_delta" | "input_json_delta"; index: number; delta: string };
    }
  | { event: "content_block_stop"; data: { index: number } }
  | {
      event: "tool_executing";
      data: { tool: string; args_preview: string; id: string };
    }
  | {
      event: "tool_result";
      data: {
        tool: string;
        id: string;
        ok: boolean;
        result_preview: string;
        error?: string | null;
      };
    }
  | { event: "message_delta"; data: { stop_reason: string | null } }
  | { event: "done"; data: { usage: Record<string, number>; stop_reason?: string; iteration?: number } }
  | { event: "error"; data: { code: string; message: string } };

export interface ChatRequest {
  message: string;
  session_id?: string;
  system_prompt_override?: string;
  max_tokens?: number;
  model?: string;
}
