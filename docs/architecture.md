# LLMwiki 架构总览

> Phase 1 MVP — 单用户、无认证、本地/服务器皆可运行的 Web 聊天框架。

## 1. 系统组成

```
┌──────────────────────────────────────────────────────────┐
│  浏览器 (React SPA, 静态 dist/)                            │
│  ChatPage / BrowsePage / CityDetailPage / SearchPage       │
└────────────────────────┬─────────────────────────────────┘
                         │ /api/*  (SSE for chat)
┌────────────────────────▼─────────────────────────────────┐
│  Nginx (宝塔)                                              │
│  /api/*  →  127.0.0.1:8000  (proxy_buffering off)         │
│  /*      →  静态文件 (dist/)                                │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│  FastAPI (uvicorn, systemd)                                │
│  ┌────────────────────────────────────────────────┐      │
│  │ 9 routers: chat/vault/skills/scripts/          │      │
│  │           sessions/healthz                      │      │
│  └────────────────────────────────────────────────┘      │
│  ┌────────────────────────────────────────────────┐      │
│  │ services:                                       │      │
│  │  - llm.py           (Anthropic SDK + base_url)   │      │
│  │  - tool_defs.py     (9 tools JSON Schema)        │      │
│  │  - tool_runtime.py  (执行工具调用)                │      │
│  │  - prompt_builder.py (system prompt 组装)        │      │
│  │  - session_store.py (内存 dict)                  │      │
│  │  - vault_fs.py      (路径安全 fs)                │      │
│  │  - frontmatter.py   (YAML 读写)                  │      │
│  │  - wikilink.py      (链接解析, 复用 lint.py)      │      │
│  │  - search.py        (全文搜索)                   │      │
│  │  - skills_index.py  (扫描 .claude/skills/)        │      │
│  └────────────────────────────────────────────────┘      │
└────────────────────────┬─────────────────────────────────┘
                         │ 直接 fs 读写
┌────────────────────────▼─────────────────────────────────┐
│  Vault: <path to your Obsidian vault>                      │
│  (本地任意路径 / 服务器 /www/vault/政策 均可)              │
│  wiki/  raw/  concepts/  .claude/  .claudian/             │
└──────────────────────────────────────────────────────────┘
                         ▲
                         │ minimaxi Anthropic API
┌────────────────────────┴─────────────────────────────────┐
│  api.minimaxi.com/anthropic  (MiniMax-M3)                │
└──────────────────────────────────────────────────────────┘
```

## 2. 关键设计决策

### 2.1 LLM 接入 — Anthropic SDK + base_url 覆盖

我们用官方 `anthropic` Python SDK，但把 `base_url` 替换为 `https://api.minimaxi.com/anthropic`。
所有 Anthropic 原生概念（messages、tools、system、streaming events）都直接适用，
**唯一区别**是请求走了 minimaxi 的代理。

```python
from anthropic import Anthropic
client = Anthropic(
    api_key=LLMWIKI_LLM_API_KEY,
    base_url="https://api.minimaxi.com/anthropic",
    timeout=300,
)
```

### 2.2 配置自动从 settings.json 加载

启动时 `app/settings_loader.py` 读 `LLMWIKI_CLAUDE_SETTINGS_PATH` 指向的
`settings.json` 中的 `env.ANTHROPIC_AUTH_TOKEN`，填到 `Settings.llm_api_key`。
`.env` 可显式覆盖（优先级更高）。本机开发不需要重复填 key。

### 2.3 工具调用（function calling）

`app/services/tool_defs.py` 定义 9 个工具的 JSON Schema。
`app/services/tool_runtime.py` 是执行器，与 fs/search/wikilink 解耦。
LLM 调用工具时，`llm.py` 的流式循环会自动：
1. 解析 `tool_use` 块
2. 把工具结果作为 `tool_result` 块塞回 messages
3. 再次调用模型
4. 循环直到 `stop_reason == end_turn` 或达到 `max_tool_iterations`（默认 8）

### 2.4 System prompt 组装

`prompt_builder.py` 启动时生成，包含：
- vault 路径、今天日期
- `CLAUDE.md` 全文（≤20KB）
- `MEMORY.md` 全文（≤8KB）
- skills 索引（每条描述 ≤100 字符）
- 工作规范（10 条硬性要求）

预估大小 8-12KB（3-4K tokens），安全。

### 2.5 SSE 协议

后端用 `text/event-stream`，事件 9 种：
- `message_start` — 每次响应唯一
- `content_block_start` / `content_block_delta` / `content_block_stop` — 文本或工具块
- `tool_executing` / `tool_result` — 工具调用可视化
- `message_delta` — `stop_reason` 等
- `done` / `error` — 终止

前端用 `fetch + ReadableStream` 自己解析（不能用 `EventSource`，因为我们要 POST body）。

### 2.6 路径安全

所有写操作走 `vault_fs._check_writable()`：
- 拒绝 `raw/`（原始文档不可变）
- 拒绝 `.obsidian/`、`.claude/`（管理目录）
- 拒绝 `..` 父目录逃逸
- 拒绝 `.git/`、`.venv/` 等噪声目录

读操作走 `vault_fs.resolve()`：
- 同上 + 解析后再次验证仍在 vault 内（防御性编程）

### 2.7 Wikilink 解析

照搬 vault 自带 `.claudian/lint.py` 的逻辑：
1. 匹配 `[[target]]` 或 `[[target|alias]]`
2. 去后缀（.md/.pdf/.html/.docx）
3. 尝试绝对路径
4. 试 `wiki/` 前缀
5. 退化到 basename 模糊匹配（Obsidian 行为）

## 3. 模块依赖

```
main.py
  ├ config.py
  │   └ settings_loader.py
  ├ deps.py
  ├ routers/
  │   ├ chat.py  → services/llm.py → services/tool_runtime.py
  │   │                          → services/prompt_builder.py
  │   │                          → services/session_store.py
  │   ├ vault.py → services/vault_fs.py, frontmatter.py, search.py, wikilink.py
  │   ├ skills.py → services/skills_index.py
  │   ├ scripts.py → services/tool_runtime.py
  │   └ sessions.py → services/session_store.py
  └ errors.py
```

没有循环依赖。所有 routers 是叶子节点；services 之间也很少互相调用。

## 4. 已知风险与缓解

| 风险 | 状态 | 缓解 |
|------|------|------|
| MiniMax-M3 tool calling 兼容性 | 未验证 | 备选：解析 `<tool>...</tool>` XML（ReAct 风格）|
| SSE 经宝塔→Nginx 缓冲 | 已防 | `proxy_buffering off` + `X-Accel-Buffering: no` 头 |
| 系统 prompt 超 token | 监控中 | `/api/healthz` 报告 prompt 字节数 |
| 生产无认证 | Phase 1 接受 | Phase 1.5 加 Bearer token（见 deploy/README.md） |
| Windows 路径编码 | 已防 | 全用 `pathlib.Path`；API 返回 POSIX 风格 |
| 会话重启丢失 | Phase 1 接受 | Phase 2 落 `<vault>/.claudian/sessions/<sid>.jsonl` |
| Obsidian 与 LLM 写冲突 | Phase 1 接受 | last-write-wins；Phase 2 加 etag/optimistic lock |
| miniMax token 计费 | 已防 | tool_result 截断 4KB |

## 5. Phase 2 路线图

- [ ] 持久化 session 到 `.claudian/sessions/<sid>.jsonl`
- [ ] session 切换时加载历史
- [ ] 多用户 + Bearer token 鉴权
- [ ] 文件版本/etag/乐观锁
- [ ] 图谱可视化（前端集成 Cytoscape.js）
- [ ] 政策对比表生成器（前端表单）
- [ ] 文件上传与二进制处理
- [ ] 移动端响应式
- [ ] 自动 vault 同步（WebSocket / watchfiles）
- [ ] 搜索：whoosh 替代纯字符串扫描
- [ ] 多模态：图片 OCR、PDF 解析
- [ ] 后台任务队列（写入密集场景）
