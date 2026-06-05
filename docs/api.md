# LLMwiki — API Reference

> 12 个 endpoints，base path `/api/`。所有 JSON 走 `application/json`。
> SSE endpoint 走 `text/event-stream`。

## 0. Health

### `GET /api/healthz`

返回服务状态 + 配置 dump（**无敏感信息**）。

**Response 200**
```json
{
  "ok": true,
  "version": "0.1.0",
  "vault_path": "<path to your vault>",
  "vault_exists": true,
  "model": "MiniMax-M3",
  "skills_loaded": 2,
  "skill_names": ["agent-vault-standard", "multi-agent-llm-wiki"],
  "config": {
    "vault_root": "<path to your vault>",
    "llm_model": "MiniMax-M3",
    "llm_base_url": "https://api.minimaxi.com/anthropic",
    "has_api_key": true,
    "debug": false
  },
  "claude_env": {
    "claude_settings_path": "<path to your claude settings.json>",
    "claude_settings_exists": true,
    "llm_api_key_source": "settings.json",
    "llm_model": "MiniMax-M3",
    "llm_base_url": "https://api.minimaxi.com/anthropic"
  },
  "prompt_report": {
    "today": "2026-06-04",
    "claude_md_bytes": 3120,
    "memory_md_bytes": 2048,
    "skills_count": 2,
    "skill_names": ["agent-vault-standard", "multi-agent-llm-wiki"]
  }
}
```

## 1. Chat (SSE)

### `POST /api/chat/stream`

流式聊天，支持工具调用。

**Request**
```json
{
  "message": "海口市有什么人才引进政策？",
  "session_id": "abc123...",        // 可选；省略则新建
  "system_prompt_override": "..."   // 可选；高级
  "max_tokens": 8192,               // 可选
  "model": "MiniMax-M3"             // 可选；覆盖默认
}
```

**Response**: `Content-Type: text/event-stream`

事件流：

| 事件 | data 字段 | 说明 |
|------|----------|------|
| `message_start` | `{session_id, message_id}` | 流开始 |
| `content_block_start` | `{type, index, name?, id?}` | 文本或工具块开始 |
| `content_block_delta` | `{type, index, delta}` | 文本 / 工具参数增量 |
| `content_block_stop` | `{index}` | 块结束 |
| `tool_executing` | `{tool, args_preview, id}` | 工具开始执行 |
| `tool_result` | `{tool, id, ok, result_preview, error?}` | 工具结果 |
| `message_delta` | `{stop_reason}` | 模型停止原因 |
| `done` | `{usage, stop_reason, iteration}` | 正常结束 |
| `error` | `{code, message}` | 出错 |

**curl 示例**
```bash
curl -N https://llmwiki.example.com/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"列出 vault 城市总数"}'
```

## 2. Sessions

### `GET /api/sessions`

列出会话（按 updated_at 倒序）。

**Response 200**
```json
{
  "count": 3,
  "sessions": [
    {
      "id": "abc123",
      "title": "海口市人才政策",
      "created_at": 1749052800.0,
      "updated_at": 1749059999.0,
      "message_count": 8
    }
  ]
}
```

### `POST /api/sessions?title=新对话`

新建会话。

**Response 200**: `SessionSummary`

### `GET /api/sessions/{id}`

会话详情。

### `DELETE /api/sessions/{id}`

删除会话。

**Response 200**
```json
{ "ok": true, "id": "abc123" }
```

## 3. Vault

### `GET /api/vault/tree?path=&max_depth=5`

列出子节点。

**Query**:
- `path` (string, default `""`) — vault 相对路径，空 = 根
- `max_depth` (int, 1-10, default 5)

**Response 200**
```json
{
  "root": "",
  "tree": {
    "name": ".",
    "path": "",
    "type": "dir",
    "children": [
      { "name": "wiki", "path": "wiki", "type": "dir", "children": [...] },
      { "name": "CLAUDE.md", "path": "CLAUDE.md", "type": "file", "size": 3120 }
    ]
  }
}
```

### `GET /api/vault/file?path=wiki/cities/三亚市.md`

读文件 + 自动解析 frontmatter。

**Response 200**
```json
{
  "path": "wiki/cities/三亚市.md",
  "exists": true,
  "raw": "---\ntitle: 三亚市\n...\n---\n\n# 三亚市\n...",
  "frontmatter": { "title": "三亚市", "updated": "2026-01-01", "tags": ["城市"] },
  "body": "# 三亚市\n...",
  "has_frontmatter": true,
  "size": 1234,
  "modified": 1749052800.0
}
```

### `PUT /api/vault/file`

写/覆写文件。

**Request**
```json
{ "path": "wiki/new.md", "content": "...", "create_parents": true }
```

**Response 200**
```json
{ "ok": true, "path": "wiki/new.md", "bytes_written": 256, "created_parents": true }
```

**Errors**:
- `403 raw_immutable` — 尝试写 `raw/`
- `403 path_security_error` — 写 `.obsidian/`、`.claude/` 等
- `404 file_not_found` — 父目录不存在且 `create_parents=false`

### `POST /api/vault/append`

追加内容。

**Request**
```json
{ "path": "wiki/log.md", "content": "## entry\n", "ensure_trailing_newline": true }
```

### `POST /api/vault/search`

全文搜索。

**Request**
```json
{
  "query": "人才引进",
  "glob": "**/*.md",
  "case_sensitive": false,
  "max_results": 100,
  "context_chars": 120
}
```

**Response 200**
```json
{
  "query": "人才引进",
  "count": 5,
  "hits": [
    { "path": "wiki/cities/海口市.md", "line": 12, "snippet": "…人才引进政策…", "match_start": 5, "match_end": 9 }
  ]
}
```

### `POST /api/vault/resolve-wikilink`

解析单个 wikilink。

**Request**
```json
{ "link": "三亚市" }
```

**Response 200**
```json
{
  "resolved": {
    "link": "三亚市",
    "resolved": "wiki/三亚市",
    "exists": true,
    "is_external": false
  }
}
```

### `GET /api/vault/frontmatter?path=...`

提取 frontmatter。

### `POST /api/vault/frontmatter/update`

合并更新 frontmatter（自动 set `updated` 为今天）。

**Request**
```json
{ "path": "wiki/index.md", "updates": { "tags": ["meta", "updated"] } }
```

## 4. Skills

### `GET /api/skills`

**Response 200**
```json
{
  "count": 2,
  "skills": [
    { "name": "agent-vault-standard", "description": "vault 建设标准…", "path": ".claude/skills/agent-vault-standard/SKILL.md", "size": 8192 }
  ]
}
```

### `GET /api/skills/{name}`

**Response 200**
```json
{
  "name": "agent-vault-standard",
  "description": "...",
  "path": ".claude/skills/agent-vault-standard/SKILL.md",
  "size": 8192,
  "body": "# Skill: agent-vault-standard\n...",
  "frontmatter": { "description": "..." }
}
```

## 5. Scripts

### `POST /api/scripts/run`

跑白名单脚本。

**Request**
```json
{ "name": "lint", "args": [], "timeout": 60 }
```

**白名单**：`lint`, `graph_audit`, `fix_orphans`

**Response 200**
```json
{
  "name": "lint",
  "ok": true,
  "exit_code": 0,
  "stdout": "...",
  "stderr": "",
  "duration_ms": 1234,
  "truncated": false
}
```

### `GET /api/scripts/whitelist`

返回白名单（供前端展示）。

## 6. Error format

所有非 2xx 响应 body：

```json
{
  "error": {
    "code": "path_security_error",
    "message": "Cannot write to raw/ (immutable original documents)",
    "details": { "path": "raw/foo.md" }
  }
}
```

### Error codes

| Code | HTTP | 含义 |
|------|------|------|
| `path_security_error` | 403 | 路径不安全（父目录逃逸、禁写目录） |
| `raw_immutable` | 403 | 尝试写 `raw/` |
| `file_not_found` | 404 | 文件不存在 |
| `frontmatter_error` | 400 | YAML 解析失败 |
| `wikilink_error` | 400 | wikilink 解析失败 |
| `search_error` | 500 | 搜索失败 |
| `llm_config_error` | 503 | API key 缺失 |
| `llm_error` | 502 | LLM 调用失败 |
| `llm_rate_limit` | 429 | LLM 限流 |
| `script_not_whitelisted` | 403 | 脚本不在白名单 |
| `script_timeout` | 504 | 脚本超时 |
| `tool_arg_error` | 400 | 工具参数错误 |
| `tool_error` | 500 | 工具执行失败 |
| `session_not_found` | 404 | 会话不存在 |
