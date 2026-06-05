import { invalidateCache, request } from "./client";
import type {
  FileContentResponse,
  ResolvedWikilink,
  SearchResponse,
  TreeResponse,
} from "../types/api";

export const vaultApi = {
  tree(path = "", maxDepth = 5): Promise<TreeResponse> {
    return request<TreeResponse>("/api/vault/tree", {
      query: { path, max_depth: maxDepth },
    });
  },
  getFile(path: string): Promise<FileContentResponse> {
    return request<FileContentResponse>("/api/vault/file", {
      query: { path },
    });
  },
  putFile(path: string, content: string, createParents = true) {
    // H2 fix: write-then-read should see the new state, not a cached GET.
    return request<{ ok: boolean; path: string; bytes_written: number; created_parents: boolean }>(
      "/api/vault/file",
      { method: "PUT", body: { path, content, create_parents: createParents } },
    ).then((r) => {
      invalidateCache();
      return r;
    });
  },
  append(path: string, content: string, ensureTrailingNewline = true) {
    return request<{ ok: boolean; path: string; bytes_appended: number; existed_before: boolean }>(
      "/api/vault/append",
      { method: "POST", body: { path, content, ensure_trailing_newline: ensureTrailingNewline } },
    ).then((r) => {
      invalidateCache();
      return r;
    });
  },
  search(query: string, opts: { glob?: string; caseSensitive?: boolean; maxResults?: number } = {}) {
    return request<SearchResponse>("/api/vault/search", {
      method: "POST",
      body: {
        query,
        glob: opts.glob ?? "**/*.md",
        case_sensitive: opts.caseSensitive ?? false,
        max_results: opts.maxResults ?? 100,
      },
    });
  },
  resolveWikilink(link: string) {
    return request<{ resolved: ResolvedWikilink }>(
      "/api/vault/resolve-wikilink",
      { method: "POST", body: { link } },
    );
  },
  getFrontmatter(path: string) {
    return request<{ path: string; frontmatter: Record<string, unknown>; has_frontmatter: boolean }>(
      "/api/vault/frontmatter",
      { query: { path } },
    );
  },
  updateFrontmatter(path: string, updates: Record<string, unknown>) {
    return request<{ path: string; frontmatter: Record<string, unknown>; has_frontmatter: boolean }>(
      "/api/vault/frontmatter/update",
      { method: "POST", body: { path, updates } },
    ).then((r) => {
      invalidateCache();
      return r;
    });
  },
};
