# LLMwiki 部署指南

> 详细 Nginx/systemd 配置见 `deploy/` 目录。本文档给出**全流程清单**。

## 1. 本地开发

```bash
# 终端 A: 后端
cd E:\project\LLMwiki
bash scripts/dev-backend.sh
# 看到: Uvicorn running on http://127.0.0.1:8000

# 终端 B: 前端
cd E:\project\LLMwiki
bash scripts/dev-frontend.sh
# 看到: Local: http://localhost:5173/
```

打开 [http://localhost:5173](http://localhost:5173)。

Vite dev server 把 `/api/*` 反代到 `http://127.0.0.1:8000`，所以前端看到的
是同源，无 CORS 问题。

## 2. 生产部署（腾讯云轻量 + 宝塔）

### 2.1 一次性服务器准备

```bash
# SSH 到服务器
ssh ubuntu@1.2.3.4

# 系统包
sudo apt update
sudo apt install -y python3.11 python3.11-venv nginx rsync

# 宝塔面板（参考宝塔官网）
# 安装完后用 8888 端口进入
```

### 2.2 部署脚本（伪代码版）

```bash
# === 本地 ===
cd E:/project/LLMwiki
npm --prefix frontend install
npm --prefix frontend run build

# 同步代码
rsync -avz --delete -e ssh \
  backend/  ubuntu@1.2.3.4:/www/wwwroot/llmwiki/backend/

rsync -avz --delete -e ssh \
  frontend/dist/  ubuntu@1.2.3.4:/www/wwwroot/llmwiki/dist/

# 同步 vault
LLMWIKI_SERVER_HOST=ubuntu@1.2.3.4 \
  bash scripts/sync-vault-to-server.sh

# === 服务器 ===
ssh ubuntu@1.2.3.4
cd /www/wwwroot/llmwiki/backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../deploy/env.production.example .env
nano .env   # 填 LLMWIKI_LLM_API_KEY + LLMWIKI_VAULT_ROOT=/www/vault/政策
chmod 600 .env

# systemd
sudo cp ../deploy/systemd/llmwiki-backend.service /etc/systemd/system/
sudo mkdir -p /var/log/llmwiki
sudo chown www:www /var/log/llmwiki
sudo systemctl daemon-reload
sudo systemctl enable --now llmwiki-backend
sudo systemctl status llmwiki-backend

# 宝塔 / Nginx
# 1. 宝塔面板 → 网站 → 添加站点 → llmwiki.example.com
# 2. 配置文件 → 把 deploy/nginx/llmwiki.conf 内容粘进去
# 3. SSL → Let's Encrypt → 签发
# 4. 保存 → 重启 Nginx
```

### 2.3 验证

```bash
# 本地
LLMWIKI_URL=https://llmwiki.example.com bash scripts/e2e-smoke.sh
```

期望看到：
1. `/api/healthz` → `{"ok":true,...}`
2. `/api/skills` → 列出 skills
3. `/api/vault/tree?path=&max_depth=1` → 返回树
4. `/api/vault/search` → 找到结果
5. `/api/chat/stream` → SSE 事件流

## 3. 升级流程

```bash
# 本地：拉新代码 → build 前端
git pull
npm --prefix frontend run build

# 同步
rsync -avz backend/ ubuntu@server:/www/wwwroot/llmwiki/backend/
rsync -avz frontend/dist/ ubuntu@server:/www/wwwroot/llmwiki/dist/

# 服务器
ssh ubuntu@server
cd /www/wwwroot/llmwiki/backend
source .venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart llmwiki-backend

# 浏览器 Ctrl+Shift+R 强刷
```

## 4. 监控

```bash
# 看实时日志
sudo journalctl -u llmwiki-backend -f
# 或
tail -f /var/log/llmwiki/backend.log

# 健康检查
watch -n 5 'curl -s https://llmwiki.example.com/api/healthz | jq'

# /api/healthz 返回值解读
#   ok                  - 服务活着
#   vault_path          - 配置的 vault 路径
#   vault_exists        - 路径是否真存在
#   model               - 当前 LLM 模型
#   skills_loaded       - skills 数量
#   config.has_api_key  - API key 是否配了
#   prompt_report       - system prompt 大小（KB）
```

## 5. 备份

```bash
# 每日 cron 备份 vault
0 3 * * * rsync -avz --delete /www/vault/政策/ /www/vault-backup/政策-$(date +\%Y\%m\%d)/

# 或上传到对象存储（腾讯 COS / 阿里 OSS）
0 4 * * * /usr/local/bin/coscmd upload -r /www/vault/政策/ backup/政策/$(date +\%Y\%m\%d)/
```

## 6. 故障排查

| 症状 | 排查 |
|------|------|
| 502 Bad Gateway | `systemctl status llmwiki-backend` — 通常是 venv 路径错或 .env 权限问题 |
| 401 unauthorized | `.env` 里 `LLMWIKI_LLM_API_KEY` 没填或填错 |
| SSE 卡住不流 | 浏览器 DevTools → Network → 看 `event-stream` 响应是否分块到达；<br/>Nginx 配置 `proxy_buffering off` 是否生效 |
| 中文乱码 | systemd unit 加 `Environment=PYTHONIOENCODING=utf-8` |
| `LLMConfigError` | `/api/healthz` 看 `config.has_api_key`；本地看 `claude_env.llm_api_key_source` |
| skills 没扫到 | `/api/healthz` 看 `skill_names`；检查 `vault/.claude/skills/<name>/SKILL.md` 是否存在 |

## 7. 安全加固（生产前必做）

### 7.1 Bearer Token 鉴权（推荐）

编辑 `backend/app/deps.py`：

```python
from fastapi import Header, HTTPException
BEARER = os.environ.get("LLMWIKI_BEARER_TOKEN", "")

def require_auth(authorization: str | None = Header(None)):
    if not BEARER:
        return  # no token configured → dev mode
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing bearer token")
    if authorization[7:] != BEARER:
        raise HTTPException(403, "invalid token")
```

然后在 `app/routers/chat.py` 和 `app/routers/vault.py` 加 `Depends(require_auth)`。

前端在 `api/client.ts` 加 `Authorization: Bearer <token>` 头（从 localStorage 读）。

### 7.2 Nginx rate limit

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api/ {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://127.0.0.1:8000;
    ...
}
```

### 7.3 Fail2ban

```ini
# /etc/fail2ban/filter.d/llmwiki.conf
[Definition]
failregex = ^.*POST /api/chat/stream from <HOST>
ignoreregex =
```

### 7.4 审计日志

在 `main.py` 加中间件记录所有写操作：

```python
@app.middleware("http")
async def audit_log(request: Request, call_next):
    if request.method in ("PUT", "POST", "DELETE") and "/api/" in request.url.path:
        logger.info("AUDIT %s %s from %s", request.method, request.url.path, request.client.host)
    return await call_next(request)
```

## 8. 成本估算（仅供参考）

| 项 | 数量级 |
|------|------|
| 轻量服务器 | ¥50-100/月（2C2G） |
| 域名 | ¥50-100/年 |
| SSL | 免费 (Let's Encrypt) |
| LLM token (minimaxi) | ¥0.1-1/千次对话（取决于 tool 调用次数） |
| 带宽 | < 10GB/月（聊天 + 浏览） |
