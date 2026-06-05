// 城市对比 store — 最多 3 城，跨页面共享。
// 用 zustand 单文件，模式同 useChatStore：create + set + 持久化到 sessionStorage（防刷新丢）。

import { create } from "zustand";

const STORAGE_KEY = "llmwiki.compare.slugs";
const MAX_CITIES = 3;

function readPersisted(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const arr = JSON.parse(raw);
    return Array.isArray(arr) ? arr.filter((x) => typeof x === "string") : [];
  } catch {
    return [];
  }
}

function writePersisted(slugs: string[]): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(slugs));
  } catch {
    // sessionStorage may be full or disabled; non-fatal
  }
}

export interface CompareState {
  /** 已加入对比的城市 slug 列表（按添加顺序，最多 3 个） */
  slugs: string[];

  /** 追加一个城市；超过 MAX_CITIES 自动剔除最旧的 */
  add: (slug: string) => void;
  /** 移除一个城市 */
  remove: (slug: string) => void;
  /** 切换（已存在则移除，不存在则追加） */
  toggle: (slug: string) => void;
  /** 清空 */
  clear: () => void;
  /** 是否已在对比列表 */
  has: (slug: string) => boolean;
}

export const useCompareStore = create<CompareState>((set, get) => ({
  slugs: readPersisted(),

  add(slug) {
    const cur = get().slugs;
    if (cur.includes(slug)) return;
    const next = [...cur, slug].slice(-MAX_CITIES);
    writePersisted(next);
    set({ slugs: next });
  },

  remove(slug) {
    const next = get().slugs.filter((s) => s !== slug);
    writePersisted(next);
    set({ slugs: next });
  },

  toggle(slug) {
    if (get().has(slug)) get().remove(slug);
    else get().add(slug);
  },

  clear() {
    writePersisted([]);
    set({ slugs: [] });
  },

  has(slug) {
    return get().slugs.includes(slug);
  },
}));

export const COMPARE_MAX = MAX_CITIES;
