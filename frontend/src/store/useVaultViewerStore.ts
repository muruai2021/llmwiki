// 文件查看器共享 state — /chat 三段式中左右两栏共用。
// selectedPath 由左栏 tree 写入，右栏 viewer 读取。

import { create } from "zustand";

export interface VaultViewerState {
  selectedPath: string | null;
  select: (path: string) => void;
  clear: () => void;
}

export const useVaultViewerStore = create<VaultViewerState>((set) => ({
  selectedPath: null,
  select(path) {
    set({ selectedPath: path });
  },
  clear() {
    set({ selectedPath: null });
  },
}));
