# LLMwiki — Backend

FastAPI service that exposes the `政策` Obsidian vault to a web chat UI.

## 快速开始

```bash
# Windows (PowerShell / Git Bash)
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env   # 全部留空也行，会自动从 Claude Code settings.json 读
uvicorn app.main:app --reload --port 8000
```

打开 [http://127.0.0.1:8000/api/healthz](http://127.0.0.1:8000/api/healthz) 应返回：

```json
{
  "ok": true,
  "vault_path": "<path to your vault>",
  "model": "MiniMax-M3",
  "skills_loaded": 2
}
```

## 目录

```
app/
├── main.py            # FastAPI 入口 + lifespan + CORS
├── config.py          # pydantic-settings
├── settings_loader.py # 读 Claude Code settings.json
├── errors.py          # 自定义异常层级
├── deps.py            # FastAPI Depends
├── routers/           # 9 个 endpoint 分组
│   ├── chat.py        # POST /api/chat/stream  (SSE)
│   ├── vault.py       # GET/PUT /api/vault/*
│   ├── skills.py      # GET /api/skills/*
│   ├── scripts.py     # POST /api/scripts/run
│   └── sessions.py    # GET/DELETE /api/sessions/*
├── services/          # 业务逻辑层
│   ├── llm.py
│   ├── tool_defs.py
│   ├── tool_runtime.py
│   ├── prompt_builder.py
│   ├── session_store.py
│   ├── vault_fs.py
│   ├── frontmatter.py
│   ├── wikilink.py
│   ├── search.py
│   └── skills_index.py
└── models/            # Pydantic schemas
    ├── chat.py
    ├── vault.py
    └── skills.py
```

## 测试

```bash
pytest tests/ -v
```

## 配置优先级

LLM API key 的查找顺序（高 → 低）：

1. 环境变量 `LLMWIKI_LLM_API_KEY` 或 `ANTHROPIC_AUTH_TOKEN`
2. `.env` 文件中的 `LLMWIKI_LLM_API_KEY`
3. `LLMWIKI_CLAUDE_SETTINGS_PATH` 指向的 `settings.json` 中 `env.ANTHROPIC_AUTH_TOKEN`
4. 启动失败 — 缺 key 时 `/api/chat/stream` 返回 `llm_config_error`

> **生产环境务必用 Bearer token 或反向代理鉴权**（详见根目录 [docs/deployment.md](../docs/deployment.md)）。
