# 招商引力场 / Atlas

> **招商政策智能体** —— 把本地 Obsidian vault 装进浏览器：可对话、可读写、可调用 vault 自带工具的 50 城招商决策中枢。
> Phase 1 MVP · 单用户 · 适合本地/小团队演示。

[![MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Node 20+](https://img.shields.io/badge/node-20%2B-339933?logo=node.js&logoColor=white)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)

> **招商引力场 (Atlas)** — 为招商决策而构建的 AI 中枢：覆盖 50 城政策、120 万字、1,335 条 wikilink，
> 让每一份判断建立在可比较的证据之上，而不是政策汇编。

---

## ✨ 能力

- **💬 流式对话** — Server-Sent Events (SSE) 实时吐字，工具调用卡片可折叠查看
- **📁 vault 浏览** — 树形目录 + Markdown 渲染（含 frontmatter / wikilink / 表格 / 代码高亮）
- **🔍 全文搜索** — 子串匹配 + 行号 + 上下文窗口
- **🔗 Wikilink 解析** — `[[目标]]` 解析为可点击 span，命中 vault 已有页面
- **🛠️ 9 个 LLM 工具** — `read_file` / `write_file` / `append_to_file` / `list_files` / `search_vault` / `get_frontmatter` / `update_frontmatter` / `resolve_wikilink` / `run_vault_script`
- **📜 白名单脚本** — `lint` / `graph_audit` / `fix_orphans`，subprocess 跑、用 `sys.executable`、拒额外参数
- **🧠 上下文自动加载** — `CLAUDE.md` + `MEMORY.md` + `.claude/skills/` 索引
- **🏙️ 50 城对比** — 加入对比（最多 3 城），并排查看区域 / 等级 / 标签 / 简介

---

## 🖼️ 截图

> 把 `docs/screenshots/` 里放 PNG，再把下面占位换掉。

<!-- 实际部署后，截图请放在 docs/screenshots/，路径示例如下 -->
<!-- ![首页](docs/screenshots/hero.png) -->
<!-- ![聊天](docs/screenshots/chat.png) -->
<!-- ![50 城](docs/screenshots/cities.png) -->
<!-- ![对比](docs/screenshots/compare.png) -->

| 首页 | 聊天 | 50 城 | 对比 |
| :---: | :---: | :---: | :---: |
| `docs/screenshots/hero.png` | `docs/screenshots/chat.png` | `docs/screenshots/cities.png` | `docs/screenshots/compare.png` |

---

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────────┐
│  浏览器 (React SPA, 静态 dist/)                          │
│  HeroPage · CitiesGridPage · CityDetailPage · ComparePage │
│  ChatPage · BrowsePage · SearchPage                      │
└────────────────────────┬────────────────────────────────┘
                         │ /api/*  (SSE for chat)
┌────────────────────────▼────────────────────────────────┐
│  FastAPI (uvicorn, 9 routers)                            │
│  chat · vault · skills · scripts · sessions · healthz   │
│  ┌────────────────────────────────────────────────┐      │
│  │ services:                                       │      │
│  │  llm · tool_runtime · prompt_builder            │      │
│  │  session_store · vault_fs · frontmatter         │      │
│  │  wikilink · search · skills_index               │      │
│  └────────────────────────────────────────────────┘      │
└────────────────────────┬────────────────────────────────┘
                         │ 直接 fs 读写
┌────────────────────────▼────────────────────────────────┐
│  Obsidian vault (本地或服务器)                           │
│  wiki/  raw/  concepts/  .claude/  .claudian/            │
└─────────────────────────────────────────────────────────┘
                         ▲
                         │ Anthropic 兼容 API
┌────────────────────────┴────────────────────────────────┐
│  base_url override (默认: api.minimaxi.com/anthropic)   │
└─────────────────────────────────────────────────────────┘
```

详见 [`docs/architecture.md`](docs/architecture.md)。

---

## 📂 目录

| 目录 | 用途 |
|------|------|
| [`backend/`](backend/) | FastAPI 后端（Python 3.11+） |
| [`frontend/`](frontend/) | Vite + React 18 + TypeScript 前端 |
| [`deploy/`](deploy/) | systemd / nginx / env 模板 |
| [`scripts/`](scripts/) | dev / build / sync / smoke 脚本 |
| [`docs/`](docs/) | architecture / deployment / API / vault 约定 |

---

## 🚀 快速开始

### 0. 了解 vault（**第一次必读**）

LLMwiki 操作的是你的 **Obsidian vault 目录**（一个普通文件夹）。
路径 / 目录约定 / 写权限 / 中文路径 / 服务器同步 / OneDrive 坑，
**5 分钟看** [`docs/knowledge-base.md`](docs/knowledge-base.md) 全部说清楚。

### 1. 准备 vault（第一次）

需要一个 Obsidian vault，建议结构：

```
<your-vault>/
├── CLAUDE.md              # 项目规范
├── MEMORY.md              # 长期记忆
├── wiki/
│   ├── cities/<城市>/     # 每个城市一个文件夹
│   ├── concepts/          # 概念页
│   ├── index.md
│   └── log.md             # 修改日志
├── raw/                   # 原始政策文档（不可写）
├── concepts/              # 概念页（与 wiki/concepts 二选一）
└── .claude/skills/        # 可选，skill 文件
```

> **空 vault 起步 / 中文路径 / 同步到服务器 / OneDrive 坑**
> 全部在 [`docs/knowledge-base.md`](docs/knowledge-base.md) §5 / §7 / §9。

### 2. 后端

```bash
cd backend
python -m venv .venv
# Windows (Git Bash):
source .venv/Scripts/activate
# macOS / Linux:
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，至少设置：
#   LLMWIKI_VAULT_ROOT=/path/to/your/obsidian-vault
#   LLMWIKI_CLAUDE_SETTINGS_PATH=/path/to/claude/settings.json
#   (LLM_API_KEY 留空 → 自动从 settings.json 读)

uvicorn app.main:app --reload --port 8000
```

> **API Key** 不需要手填：把 `LLMWIKI_CLAUDE_SETTINGS_PATH` 指向你的 Claude Code
> `settings.json`，后端启动时自动从 `env.ANTHROPIC_AUTH_TOKEN` 读。
> `.env` 留空 `LLMWIKI_LLM_API_KEY` 即可。

### 3. 前端

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

### 4. 验证

| 检查 | URL | 期望 |
|------|-----|------|
| 前端首页 | http://localhost:5173 | 招商引力场 hero 加载 |
| 健康检查 | http://127.0.0.1:8000/api/healthz | `{"ok":true, "has_api_key":true}` |
| API 文档 | http://127.0.0.1:8000/docs | FastAPI Swagger UI |

### 一行启动（推荐）

```bash
# 后端
bash scripts/dev-backend.sh

# 前端（新终端）
bash scripts/dev-frontend.sh
```

---

## 🧪 测试

```bash
# 后端单元测试（68 个 case，含 5 个 regression）
cd backend && pytest tests/ -v

# SSE 端到端（需 key 已配）
python backend/scripts/smoke_chat.py "海口市有什么人才引进政策？"

# 前端类型检查
cd frontend && npx tsc --noEmit
```

---

## ⚙️ 配置

所有配置通过 `backend/.env` 注入，详见 [`backend/.env.example`](backend/.env.example)。

| Key | 必填 | 默认 | 说明 |
|---|---|---|---|
| `LLMWIKI_VAULT_ROOT` | ✅ | `<placeholder>` | Obsidian vault 绝对路径 |
| `LLMWIKI_CLAUDE_SETTINGS_PATH` | ⚠️ dev 推荐 | `<placeholder>` | Claude Code settings.json；服务器设 `/dev/null` |
| `LLMWIKI_LLM_API_KEY` | 服务器必填 | 空（dev 自动加载） | 留空则从 settings.json 读 |
| `LLMWIKI_LLM_BASE_URL` | — | `https://api.minimaxi.com/anthropic` | Anthropic 兼容端点 |
| `LLMWIKI_LLM_MODEL` | — | `MiniMax-M3` | 模型名 |
| `LLMWIKI_LLM_MAX_TOKENS` | — | `8192` | 单次最大输出 token |
| `LLMWIKI_LLM_REQUEST_TIMEOUT` | — | `300` | 请求超时（秒） |
| `LLMWIKI_LLM_MAX_TOOL_ITERATIONS` | — | `8` | 工具循环上限（防 runaway） |
| `LLMWIKI_SESSION_MAX_MESSAGES` | — | `40` | 会话最大消息数 |
| `LLMWIKI_TOOL_RESULT_MAX_BYTES` | — | `4096` | 工具结果字节截断（省 token） |
| `LLMWIKI_SCRIPT_TIMEOUT_SECONDS` | — | `60` | 白名单脚本超时 |

---

## 🛠️ 9 个 LLM 工具

| 工具 | 用途 | 备注 |
|------|------|------|
| `read_file` | 读单个文件 | 截 512KB；删控制字符 / 孤立代理对 |
| `write_file` | 创建/覆写 | 拒 `raw/` / `.obsidian/` / `.claude/` / `.claudian/` |
| `append_to_file` | 追加 | 自动处理尾换行 |
| `list_files` | glob 列出 | 默认 `wiki/**/*.md` |
| `search_vault` | 全文搜索 | 子串匹配 + 行号 + 上下文 |
| `get_frontmatter` | 提取 YAML | 保留顺序与注释 |
| `update_frontmatter` | 合并更新 | 自动 set `updated: <today>` |
| `resolve_wikilink` | `[[link]]` → 路径 | Obsidian 风格 basename 模糊匹配 |
| `run_vault_script` | 跑白名单脚本 | 拒额外参数；用 `sys.executable` |

---

## 🔒 安全 / 健壮性

| 项 | 行为 |
|---|---|
| 路径穿越 `..` | 拒绝 (`PathSecurityError`) |
| 写 `raw/` | 拒绝 (`RawImmutableError`) |
| 写 `.obsidian/` / `.claude/` / `.claudian/` | 拒绝 |
| `run_vault_script` 注入 | 拒 LLM 提供的 extra args |
| LLM API key 暴露 | `/api/healthz` 仅显示 `has_api_key` 布尔 |
| 写后 cache 失效 | `vaultApi.putFile/append/updateFrontmatter` 自动 `invalidateCache()` |
| Session 切消息 | 只在 assistant 回合结束后，按 (user, assistant) 配对从头部删 |
| 大文件预览 | > 256KB 不渲染 Markdown；> 512KB 后端不读 |
| 二进制 / HTML | 前端 tree 灰显不可点 |
| `PermissionError` | 后端捕为 `VaultError`，不再 500 栈 |

---

## 🌐 部署

详见 [`docs/deployment.md`](docs/deployment.md) + [`deploy/README.md`](deploy/README.md)。

**简版**（生产推荐 stack：腾讯云轻量 + 宝塔 + Nginx + systemd）：

```bash
# 1. 同步代码（不含 .env / node_modules / .venv）
rsync -av --exclude='.env' --exclude='.venv' --exclude='node_modules' \
    backend/  user@server:/www/wwwroot/llmwiki/backend/

# 2. 同步前端构建产物
cd frontend && npm run build
rsync -av dist/  user@server:/www/wwwroot/llmwiki/frontend/dist/

# 3. 服务器端安装依赖
ssh user@server "cd /www/wwwroot/llmwiki/backend && \
    python3 -m venv .venv && \
    .venv/bin/pip install -r requirements.txt"

# 4. 配 systemd（模板在 deploy/systemd/llmwiki-backend.service）
ssh user@server "sudo cp deploy/systemd/llmwiki-backend.service /etc/systemd/system/ \
    && sudo systemctl daemon-reload && sudo systemctl enable --now llmwiki-backend"

# 5. 配 Nginx（模板在 deploy/nginx/llmwiki.conf；SSE 关键: proxy_buffering off）
```

同步 vault 用 [`scripts/sync-vault-to-server.sh`](scripts/sync-vault-to-server.sh)，
冒烟测试用 [`scripts/e2e-smoke.sh`](scripts/e2e-smoke.sh)。

---

## 🗺️ Phase 2 路线图

- [ ] Session 持久化（`<vault>/.claudian/sessions/<sid>.jsonl`）
- [ ] Session 切换加载历史
- [ ] 多用户 + Bearer token 鉴权
- [ ] Obsidian 写冲突 etag / 乐观锁
- [ ] 图谱可视化（Cytoscape.js）
- [ ] 政策对比表生成器
- [ ] 文件上传与二进制处理
- [ ] 移动端响应式
- [ ] 自动 vault 同步（WebSocket / watchfiles）
- [ ] 搜索升级（whoosh 替代 substring）
- [ ] 多模态：图片 OCR、PDF 解析
- [ ] 后台任务队列

---

## 📚 文档索引

| 文件 | 用途 |
|------|------|
| [`docs/knowledge-base.md`](docs/knowledge-base.md) | **vault 路径 / 目录约定 / 同步 / 排错（必读）** |
| [`docs/architecture.md`](docs/architecture.md) | 架构图 + 设计决策 + 风险表 |
| [`docs/deployment.md`](docs/deployment.md) | 部署 + 升级 + 监控 + 故障排查 |
| [`docs/api.md`](docs/api.md) | 12 endpoint 完整契约 |
| [`docs/vault-conventions.md`](docs/vault-conventions.md) | vault 写规则（自动化层） |
| [`deploy/README.md`](deploy/README.md) | 生产部署 + 安全加固 |
| [`backend/README.md`](backend/README.md) | 后端开发 |
| [`frontend/README.md`](frontend/README.md) | 前端开发 |

---

## 🤝 贡献

欢迎 PR、issue、feature request。**小步提交**，单 PR 聚焦一个改动。
代码规范参考 `.editorconfig`；后端 `pytest` 必须全过；前端 `npx tsc --noEmit` 必须 0 错。

---

## 📜 License

[MIT](LICENSE) — Copyright © 2026 石先生 / LLMwiki contributors
