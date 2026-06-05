# Vault Conventions — 政策

> 写给 **LLMwiki 后端与 LLM 工具层**的"vault 规矩"备忘。
> 真正的规范原文在 vault 根的 `CLAUDE.md` 与 `MEMORY.md` —— 以那两份为准。
> 本文件只摘录**对自动化层有约束力**的硬性约定。

## 路径语义

| 概念 | vault 相对路径 | 后端是否可写 |
|------|---------------|------------|
| 原始文档（不可变） | `raw/**` | ❌ 拒绝（`raw_paths_are_immutable`） |
| Wiki 页面 | `wiki/**.md` | ✅ |
| 城市目录 | `wiki/cities/<城市名>/**` | ✅ |
| 概念页面 | `concepts/**.md` | ✅ |
| 长期记忆 | `MEMORY.md` | ⚠️ 慎写（追加、不覆写） |
| 操作日志 | `wiki/log.md` | ⚠️ 慎写（追加） |
| 索引 | `wiki/index.md` | ✅ |
| Obsidian 配置 | `.obsidian/**` | ❌ 拒绝 |
| Claudian 配置 | `.claudian/**`（除 `sessions/`） | ❌ 拒绝 |
| 会话存档 | `.claudian/sessions/**` | ✅ 内部用（Phase 2） |
| Claude Skills | `.claude/**` | ❌ 拒绝（手动管理） |

> **API 层路径**：所有外部 API 一律用 **POSIX 风格的 vault 相对路径**（`wiki/cities/三亚市.md`）。
> 后端负责 `Path` 对象与字符串的双向转换。

## Frontmatter 规范

- 所有 wiki 页面（除 `wiki/log.md`）必须有 frontmatter。
- **必填字段**：
  - `title`：页面标题（中文）
  - `updated`：最近修改日期，格式 `YYYY-MM-DD`（**写文件时由后端强制 set 为 today**）
  - `tags`：`[城市, 招商, ...]`
- 写入 frontmatter 时**不破坏已有键**，合并而非替换。

## Wikilink 解析规则

参考 vault 自带 `.claudian/lint.py`（**已抄进后端** `services/wikilink.py`）：

1. 匹配 `[[target]]` 或 `[[target|alias]]`
2. 排除 `http://`、`https://`、`#anchor` 开头
3. 移除 `.md` / `.pdf` / `.html` / `.docx` 后缀（按存在性去）
4. 优先按绝对路径查找
5. 找不到时按 basename 模糊匹配（同名多页取最短路径）
6. 找不到 → 标记为 broken

## 对话框规范（注入 system prompt）

1. ❌ 不写 `raw/`
2. ✅ 修改 wiki 页面后**必须追加 `wiki/log.md` 一条**
3. ✅ 修改 frontmatter 必须 set `updated`
4. ✅ 引用用 `[[wikilink]]` 或 `https://` 原始 URL
5. ✅ 中文回复
6. ✅ "对比基准"必须是海南
7. ✅ 校验任务调用 `run_vault_script({name:"lint"})`
8. ✅ 任务结束建议追加 log.md / 更新 README.md

## 写入时序约束（Phase 1 简单版）

- **无锁、无并发控制**（单用户假设）
- last-write-wins（Obsidian 与 LLM 不会同时编辑同一文件）
- 写文件前**不**做 mtime 检查
- Phase 2 计划加 etag / 乐观锁
