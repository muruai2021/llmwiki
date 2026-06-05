# 知识库（Vault）配置指南

> 完整说明 LLMwiki 怎么找到、读取、写入你的 Obsidian vault。
> 适合第一次部署、或者"路径不对 / 写不进去 / 看不到文件"的时候翻。

---

## 1. 什么是 vault

**vault** = LLMwiki 操作的"政策知识库"文件夹。本质上是一个**普通目录**，
LLMwiki 把它当成一棵文件树：

- 读 = 读 `.md` 文件，按 frontmatter / wikilink 解析
- 写 = 写文件、追加、合并 frontmatter
- 跑脚本 = 在 cwd 下执行白名单 `.py`

**强烈推荐**这个目录同时被 [Obsidian](https://obsidian.md/) 打开，
这样你既能在 LLMwiki 网页里对话，又能在 Obsidian 里手工编辑 —— 同一个 vault。

---

## 2. 配置 vault 路径

LLMwiki 通过**环境变量**知道 vault 在哪里：

```env
# backend/.env
LLMWIKI_VAULT_ROOT=/path/to/your/obsidian-vault
```

### 平台示例

| OS | 路径示例 |
|---|---|
| **Windows** | `D:\Obsidian\政策` 或 `E:\Obsidian\MyVault` |
| **macOS** | `/Users/<you>/Documents/Obsidian/MyVault` |
| **Linux (本地 dev)** | `/home/<you>/obsidian/myvault` |
| **Linux (服务器)** | `/www/vault/政策` |

### 路径合法性要求

- ✅ **必须绝对路径**（不能是 `~/vault` 这种）
- ✅ **支持中文**（`D:\Obsidian\政策` 完全 OK，已实测）
- ✅ **支持空格**（`/Users/joe smith/My Vault` 没问题）
- ⚠️ **支持软链**，但用 `realpath` 解析 — 链到 vault 外的文件**会被拒**
- ❌ **不要指向系统目录**（如 `/` 或 `C:\Windows`）—— `..` 逃逸会被拦，但根目录会被 stat 几万个文件

### 路径生效优先级

`pydantic-settings` 加载顺序（高 → 低）：

1. **环境变量** `LLMWIKI_VAULT_ROOT=...`（包括 .env 文件里的）
2. `backend/app/config.py` 里的 `default`（只是占位符 `<path-to-your-obsidian-vault>`，**启动时会被 Settings 校验拦截**）

如果 `LLMWIKI_VAULT_ROOT` 没设，**后端启动会失败**或 `vault_exists=false`，
此时 `/api/healthz` 返回：

```json
{
  "ok": false,
  "vault_path": "<path-to-your-obsidian-vault>",
  "vault_exists": false
}
```

**修法**：编辑 `backend/.env`，填上正确路径，重启 uvicorn。

---

## 3. 推荐的目录结构

LLMwiki 不强制目录结构 —— 任何 `.md` 文件都能被搜索 / 读 / 写。
但要**完整用上 50 城 + wikilink + 9 个工具**，建议长这样：

```
<your-vault>/
├── CLAUDE.md                # 项目规范（自动注入到 LLM system prompt）
├── MEMORY.md                # 长期记忆（同上）
├── wiki/
│   ├── index.md             # 入口页（首页"50 城"会跳到这里）
│   ├── log.md               # 修改日志（系统提示要求 LLM 改完追加一行）
│   ├── cities/              # 每个城市一个子目录
│   │   ├── 三亚市/
│   │   │   ├── 三亚市.md    # 城市主页（必填，文件名 = 目录名）
│   │   │   ├── policies/    # 政策详情
│   │   │   ├── tax/         # 税收优惠
│   │   │   ├── talent/      # 人才引进
│   │   │   └── park/        # 园区
│   │   ├── 海口市/
│   │   │   ├── 海口市.md
│   │   │   └── ...
│   │   └── ...
│   └── concepts/            # 概念页（如"自贸港"、"营商环境"）
├── raw/                     # 原始政策文件（PDF / docx / 扫描件等）—— 不可写
├── concepts/                # 备选概念页目录（与 wiki/concepts 二选一）
└── .claude/
    └── skills/              # 可选，skill 文件夹
        └── my-skill/
            └── SKILL.md
```

### frontmatter 规范

每个 wiki 页面（除 `wiki/log.md`）**建议**有 YAML frontmatter：

```markdown
---
title: 三亚市
updated: 2026-01-15
tags: [城市, 招商, 自贸港]
---

# 三亚市

正文...
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `title` | ✅ | 中文标题（hero / 详情页用它） |
| `updated` | ✅ | `YYYY-MM-DD`，**后端写时自动 set 为今天** |
| `tags` | ⚠️ | 数组；用于标签筛选 / `search_by_tag` |

修改 frontmatter 用 `update_frontmatter` 工具，**不要直接 write_file**，
否则会丢注释和顺序（`ruamel.yaml` round-trip 保证）。

---

## 4. 哪些目录**可写**哪些**不可写**

LLMwiki 的"路径安全"是**硬约束**，不是建议：

| 路径前缀 | 可读 | 可写 | 理由 |
|---|:-:|:-:|---|
| `wiki/**` | ✅ | ✅ | 主知识库 |
| `concepts/**` | ✅ | ✅ | 概念页 |
| `MEMORY.md` / `CLAUDE.md` | ✅ | ✅ | 长期记忆 / 项目规范 |
| `.claudian/sessions/**` | ✅（内部） | ❌ | Phase 2 计划落 session 用 |
| `raw/**` | ✅ | ❌ | **原始政策文档，不可变** |
| `.obsidian/**` | ✅ | ❌ | Obsidian 配置 |
| `.claude/**` | ❌ | ❌ | 内部 skill / claude code 配置 |
| `.claudian/**`（除 `sessions/`） | ❌ | ❌ | 桌面端 Claudian 配置 |
| 任何 `..` 逃逸 | — | ❌ | 路径安全 |

**前端**会隐藏这些不可写目录（树里看不到），但**后端**也严格拒绝，
即使 LLM 被 prompt-injection 诱导调 `write_file(".claude/skills/evil/SKILL.md", ...)` 也会 403。

---

## 5. 第一次：空 vault 怎么起步

如果你**还没**有 vault：

### 选项 A：用现成 demo vault（推荐快速看效果）

```bash
# 1. 复制模板（如果你的项目里有的话）
# 2. 或者直接用 Obsidian 创建一个空 vault 在任何位置
mkdir -p ~/my-vault/wiki/cities
cd ~/my-vault

# 3. 写一个最小入口页
cat > wiki/index.md <<'EOF'
---
title: 政策索引
updated: 2026-01-15
tags: [meta]
---

# 政策索引

- [[三亚市]]
- [[海口市]]
EOF

# 4. 写一个城市页
mkdir wiki/cities/三亚市
cat > wiki/cities/三亚市/三亚市.md <<'EOF'
---
title: 三亚市
updated: 2026-01-15
tags: [城市, 招商]
---

# 三亚市

自贸港核心城市。
EOF

# 5. 在 backend/.env 指向它
# LLMWIKI_VAULT_ROOT=/home/<you>/my-vault
```

### 选项 B：从 Obsidian 已有 vault 迁过来

直接把 Obsidian vault 路径塞进 `LLMWIKI_VAULT_ROOT` 即可。
**第一次** LLMwiki 会读整个 vault 的 frontmatter / wikilink，构建 system prompt 里的 skills 索引 —— **几千个文件大概 1-2 秒**，可接受。

---

## 6. 多 vault / 多环境

LLMwiki 进程级只支持**一个 vault**。要多 vault，切环境变量重启后端：

```bash
# 启动 vault A
LLMWIKI_VAULT_ROOT=/path/to/vaultA uvicorn app.main:app --port 8000

# 启动 vault B（不同端口）
LLMWIKI_VAULT_ROOT=/path/to/vaultB uvicorn app.main:app --port 8001
```

如果想**同一进程**支持多 vault，得 fork 后端（`vault_fs.resolve()` 改成 `resolve(vault_id, rel)`）。
**Phase 1 不做**。Phase 2 看需求。

---

## 7. 部署到服务器时，vault 怎么同步

服务器 vault 通常在 `/www/vault/政策/`，本机在 `D:\Obsidian\政策`。
LLMwiki **不**自动同步（Phase 1）。三种方案：

### 方案 1：手动 rsync（最简单）

`scripts/sync-vault-to-server.sh` 已经写好：

```bash
# 本地
rsync -av --delete \
    --exclude='.trash/' \
    --exclude='.obsidian/workspace.json' \
    /d/Obsidian/政策/ \
    user@server:/www/vault/政策/
```

> **⚠️ `--delete`** 会删服务器上你本机没有的文件。**第一次**先**不带** `--delete` 看 diff。

### 方案 2：git push vault 到服务器

如果 vault 不大（< 1k 文件），把它做成 git repo，服务器 `git pull`：

```bash
# 本地
cd /d/Obsidian/政策
git init && git add . && git commit -m "init"
git remote add origin git@github.com:your-org/policy-vault.git
git push -u origin main

# 服务器
cd /www/vault/政策
git clone git@github.com:your-org/policy-vault.git .
# 加 cron 每 5 分钟 pull
echo "*/5 * * * * cd /www/vault/政策 && git pull" | crontab -
```

### 方案 3：双向同步（unison / syncthing）

unison / syncthing 适合双向编辑（Obsidian 端 + LLMwiki 端都改）。
**首次配置**略麻烦，**生产推荐**。

---

## 8. 中文路径 / 空格 / 大小写

### 中文路径

✅ **完全支持**。后端用 `pathlib.Path`，跨平台 UTF-8。
实测 `D:\Obsidian\政策\wiki\cities\三亚市\` 在 Windows + Python 3.11 上正常。

### 路径含空格

✅ **支持**。`/Users/joe smith/My Vault/` 没问题。
但 `subprocess.run(cwd=str(s.vault_root), ...)` 在 Windows 上对带空格的 cwd 历史上有怪 bug，
**当前 Python 3.11 已修**。

### 大小写

⚠️ **取决于文件系统**：
- macOS APFS / Windows NTFS = **大小写不敏感**（`三亚市.md` 和 `三亚市.MD` 视为同一文件）
- Linux ext4 = **大小写敏感**（视为不同文件）

LLMwiki 内部统一用 **POSIX 小写扩展名**（`/api/vault/file?path=wiki/三亚市.md`），
但**目录和文件名本身**保持原样。如果你从 Windows 迁到 Linux，记得 wiki link 大小写完全一致。

### Windows 反斜杠

✅ 前端发请求时**必须用正斜杠**（`wiki/三亚市.md`），后端自动转。
**不要**用 `wiki\三亚市.md` —— 虽然后端 `_normalize` 会处理，但容易踩坑。

---

## 9. 常见排错

| 现象 | 原因 | 修法 |
|---|---|---|
| `/api/healthz` 返回 `vault_exists: false` | 路径写错 / 权限不够 | 检查 `LLMWIKI_VAULT_ROOT`，确认 uvicorn 用户能读 |
| 树里看不到任何东西 | vault 空 / 全是隐藏目录 | 放一个 `wiki/index.md` |
| 写文件 403 | 路径在 `raw/` / `.obsidian/` / `.claude/` | 改写到 `wiki/` |
| 写文件 404 | 父目录不存在且 `create_parents=false` | PUT 时设 `create_parents: true` |
| 搜索 0 结果 | glob 不对 | 默认 `**/*.md`；搜索 `raw/` 用 `**/*.docx` |
| wikilink 总是 broken | `[[目标]]` 不在 vault 里 | 用 `resolve_wikilink` 工具查实际路径 |
| 启动报 `PermissionError` | OneDrive / AV 锁文件 | 见下节 |
| 中文显示乱码 | Windows GBK 终端 | 用 `chcp 65001` 切 UTF-8 |

### OneDrive / iCloud / 网盘同步目录

**不推荐**把 vault 放在 OneDrive/坚果云/iCloud 同步目录里：
- 它们会**临时锁文件**（`.tmp`、`.lock`）触发 `PermissionError`
- 同步冲突会生成 `xxx (冲突).md` 双份文件
- LLM 写文件会**触发同步流量**

LLMwiki 后端已 catch `PermissionError` 转成 `VaultError` 友好化（`HTTP 500` + 提示信息），
但**频繁被锁**会影响 `read_file` 性能。实在要放，加 vault 到同步排除列表。

---

## 10. 相关配置

| 配置 | 在哪 | 默认 |
|---|---|---|
| Vault 路径 | `LLMWIKI_VAULT_ROOT` | `<placeholder>`（必须改） |
| Claude settings.json 路径 | `LLMWIKI_CLAUDE_SETTINGS_PATH` | `<placeholder>`（dev 推荐改） |
| LLM API key | `LLMWIKI_LLM_API_KEY` 或 settings.json | dev 自动从 settings.json 读 |
| 最大工具迭代 | `LLMWIKI_LLM_MAX_TOOL_ITERATIONS` | `8` |
| Session 最大消息 | `LLMWIKI_SESSION_MAX_MESSAGES` | `40` |

完整配置见 [`backend/.env.example`](../backend/.env.example) + [`docs/architecture.md`](architecture.md) §2。

---

## 11. 进一步

- 架构决策：[`docs/architecture.md`](architecture.md)
- API 契约：[`docs/api.md`](api.md)
- 部署（含 systemd / Nginx / 同步脚本）：[`docs/deployment.md`](deployment.md) + [`deploy/README.md`](../deploy/README.md)
- Vault 写规则（自动化层硬性约定）：[`docs/vault-conventions.md`](vault-conventions.md)
