# LLMwiki

> 把 Obsidian 上的 `政策` vault 搬进浏览器：可对话、可读写、可调用 vault 自带工具。
> LLM 复用 Claude Code 同一套配置（MiniMax-M3 via minimaxi Anthropic 兼容 API）。

## ✨ 能力

- 💬 **聊天**：在浏览器和 MiniMax-M3 流式对话
- 📁 **浏览**：文件树 + Markdown 渲染（wiki、raw、concepts）
- 🔍 **搜索**：vault 全文搜索 + wikilink 解析
- 🛠️ **工具**：LLM 可调用 9 个工具（read/write/list/search/frontmatter/wikilink/脚本）
- 📜 **脚本**：跑 vault 自带白名单脚本（`lint.py`、`graph_audit.py`、`fix_orphans.py`）
- 🧠 **上下文**：自动加载 `CLAUDE.md` + `MEMORY.md` + skills 索引

## 🏗️ 架构

```
浏览器 (React SPA) ←→ FastAPI (9 routers) ←→ Vault on disk
                       ↓
                  minimaxi / MiniMax-M3
```

详见 [docs/architecture.md](docs/architecture.md)。

## 📦 目录

| 目录 | 用途 |
|------|------|
| [`backend/`](backend/) | FastAPI 后端 |
| [`frontend/`](frontend/) | Vite + React 前端 |
| [`deploy/`](deploy/) | systemd / nginx / env 模板 |
| [`scripts/`](scripts/) | dev / build / sync / smoke |
| [`docs/`](docs/) | architecture / deployment / API / vault 约定 |

## 🚀 本地开发

```bash
# 1. 后端
cd backend
python -m venv .venv
source .venv/Scripts/activate  # Windows
# source .venv/bin/activate    # macOS / Linux
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# 2. 前端（新终端）
cd frontend
npm install
npm run dev  # http://localhost:5173
```

浏览器打开 [http://localhost:5173](http://localhost:5173) 即可。

> **API Key** 不需要手填：后端启动时自动从你的 Claude Code
> `settings.json` 读 `env.ANTHROPIC_AUTH_TOKEN`（路径通过
> `LLMWIKI_CLAUDE_SETTINGS_PATH` 配置，详见 `.env.example`）。
> `.env` 里留空即可。

## 🧪 验证

```bash
# 后端冒烟
curl http://127.0.0.1:8000/api/healthz

# 单元测试
cd backend && pytest tests/ -v

# SSE 端到端（需 key 已配）
python scripts/smoke_chat.py "海口市有什么人才引进政策？"
```

## 🌐 部署

详见 [docs/deployment.md](docs/deployment.md)。
简版：FastAPI (systemd) + 前端 dist (Nginx / 宝塔) + 手动同步 vault。

## 📜 License

MIT — 详见 [LICENSE](LICENSE)。
