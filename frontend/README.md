# LLMwiki — Frontend

Vite + React 18 + TypeScript SPA for talking to the LLMwiki backend.

## 快速开始

```bash
npm install
npm run dev    # http://localhost:5173 (proxies /api → :8000)
```

## Build

```bash
npm run build  # outputs to dist/
npm run preview  # local preview of dist/
```

## 目录

```
src/
├── main.tsx           # ReactDOM 入口
├── App.tsx            # 路由
├── api/               # fetch wrappers (chat SSE, vault, skills)
├── components/        # 8 个 UI 组件
├── pages/             # 4 个页面 (Chat / Browse / CityDetail / Search)
├── store/             # Zustand chat state
├── types/             # TS 类型
└── styles/globals.css # 全局样式
```

## 关键依赖

- **react 18 / react-dom 18** — UI
- **react-router-dom 6** — 路由
- **react-markdown + remark-gfm** — Markdown 渲染
- **zustand** — 状态管理
- **lucide-react** — 图标
- **vite 5** — 构建
- **typescript 5** — 类型

## SSE 消费

`src/api/chat.ts` 用 `fetch + ReadableStream` 自己解析 SSE 事件（不能用
`EventSource`，因为 SSE 仅支持 GET）。
