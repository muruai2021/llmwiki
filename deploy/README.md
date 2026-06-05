# LLMwiki 部署说明

> 生产目标：腾讯云轻量 + 宝塔 + Nginx 反代 + systemd 守护 uvicorn

## 服务器假设

- 系统：Ubuntu 22.04 LTS（或任意主流 Linux）
- 宝塔已装：网站、Python 项目管理、PM2（可选）
- 已有域名 + SSL 证书（Let's Encrypt）

## 目录结构（推荐）

```
/www/wwwroot/llmwiki/                 # 项目根
├── backend/                          # FastAPI 代码
│   ├── .venv/
│   ├── app/
│   ├── .env                          # 0600
│   └── requirements.txt
├── dist/                             # 前端构建产物 (npm run build)
└── logs/

/www/vault/政策/                      # Obsidian vault (与本地 vault 同步)
├── wiki/
├── raw/
├── concepts/
├── CLAUDE.md
└── MEMORY.md

/var/log/llmwiki/                     # systemd 日志
├── backend.log
└── backend.err

/etc/systemd/system/llmwiki-backend.service
/www/server/panel/vhost/cert/llmwiki.example.com/   # SSL 证书 (宝塔)
```

## 部署步骤

### 1. 上传代码

```bash
# 本地
cd E:/project/LLMwiki
npm --prefix frontend install
npm --prefix frontend run build      # → frontend/dist/

# 同步到服务器
rsync -avz --delete \
  -e ssh \
  E:/project/LLMwiki/backend/  user@server:/www/wwwroot/llmwiki/backend/
rsync -avz --delete \
  -e ssh \
  E:/project/LLMwiki/frontend/dist/  user@server:/www/wwwroot/llmwiki/dist/
```

### 2. 后端 venv + 依赖

```bash
ssh user@server
cd /www/wwwroot/llmwiki/backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../deploy/env.production.example .env
# 编辑 .env：填 LLMWIKI_LLM_API_KEY，LLMWIKI_VAULT_ROOT=/www/vault/政策
chmod 600 .env
```

### 3. 同步 vault

```bash
# 本地 (另一终端)
LLMWIKI_SERVER_HOST=user@server \
  ./scripts/sync-vault-to-server.sh
```

### 4. systemd 守护

```bash
# 复制 unit
sudo cp /www/wwwroot/llmwiki/deploy/systemd/llmwiki-backend.service \
        /etc/systemd/system/

# 创建日志目录
sudo mkdir -p /var/log/llmwiki
sudo chown www:www /var/log/llmwiki

# 启动
sudo systemctl daemon-reload
sudo systemctl enable llmwiki-backend
sudo systemctl start llmwiki-backend
sudo systemctl status llmwiki-backend   # 应显示 active (running)
```

### 5. 宝塔 / Nginx

- 宝塔面板 → 网站 → 添加站点 → 域名 `llmwiki.example.com`
- 不需要 PHP 纯静态：选择「静态网站」
- 把 `deploy/nginx/llmwiki.conf` 内容粘到「配置文件」编辑框
- 申请 SSL 证书（Let's Encrypt 一键）
- 保存 → 重启 Nginx

### 6. 烟测

```bash
# 本地
LLMWIKI_URL=https://llmwiki.example.com ./scripts/e2e-smoke.sh
```

## 升级流程

```bash
# 本地
git pull                       # 或 rsync
npm --prefix frontend run build
rsync -avz backend/ user@server:/www/wwwroot/llmwiki/backend/

# 服务器
ssh user@server
cd /www/wwwroot/llmwiki/backend
source .venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart llmwiki-backend

# 上传新前端
# (rsync dist/ then force-refresh browser with Ctrl+Shift+R)
```

## 常见问题

| 现象 | 排查 |
|------|------|
| 502 Bad Gateway | 后端未启动 → `systemctl status llmwiki-backend` |
| 401 / no key | `.env` 没填 `LLMWIKI_LLM_API_KEY` 或文件权限不对 |
| SSE 卡住不流 | 检查 Nginx `proxy_buffering off` 是否生效；`X-Accel-Buffering: no` 头 |
| 静态资源 404 | 确认 `dist/` 目录上传完整；`index.html` 在根 |
| 中文乱码 | `PYTHONIOENCODING=utf-8` 加到 systemd unit 的 `Environment` |

## 安全建议

⚠️ **生产前必做**：

1. **加 Bearer token 鉴权**（Phase 1.5）：
   ```python
   # app/deps.py 加一个 require_auth 依赖
   ```
2. **限制 LLM 工具权限**：把 `SCRIPT_WHITELIST` 收紧到只用 `lint` 一个
3. **Nginx 加 rate limiting**：
   ```nginx
   limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
   location /api/ {
       limit_req zone=api burst=20 nodelay;
       ...
   }
   ```
4. **禁止 LLM 写 raw/**：当前已实现（`RawImmutableError`）
5. **vault 定期备份**：用 `rsync` 到对象存储
