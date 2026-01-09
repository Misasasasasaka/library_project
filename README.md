# 图书馆管理系统（Django + Vue）

## 运行环境

- Python 3.10+（推荐 3.12）
- Node.js 18+（用于构建前端）
- Nginx（反向代理 + 静态文件服务）

## 1) 获取代码与创建虚拟环境

```bash
git clone https://github.com/Misasasasasaka/library_project.git
cd library_project

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) 配置环境变量（.env）

项目启动时会读取项目根目录的 `.env`（也支持没有安装 `python-dotenv` 的情况）。

复制示例文件并填写（不要提交真实密钥）：

```bash
cp .env.example .env
```

常用配置项：

- 邮箱（注册邮箱验证码/逾期通知邮件）
  - `EMAIL_BACKEND`（开发可用 `django.core.mail.backends.console.EmailBackend`）
  - `DEFAULT_FROM_EMAIL`
  - `EMAIL_HOST` / `EMAIL_PORT` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD`
  - `EMAIL_USE_TLS` / `EMAIL_USE_SSL`
- AI 推荐
  - `AI_API_KEY`（必填，否则 AI 接口返回 503）
  - `AI_API_BASE_URL`（可选：OpenAI-compatible 服务地址）
  - `AI_MODEL`（可选）

## 3) 初始化数据库

```bash
source .venv/bin/activate
python3 manage.py migrate
python3 manage.py createsuperuser
```

默认使用 SQLite：`db.sqlite3`。生产环境建议切换到 PostgreSQL/MySQL（需自行调整 `library_project/settings.py`）。

## 4) 构建前端（生产环境必做）

生产环境不走 Vite dev server，需要先构建前端产物：

```bash
cd frontend
npm install
npm run build
cd ..
```

说明：

- 构建产物会输出到项目根目录的 `static/`
- Django 在 `DEBUG=False` 时会读取 `static/.vite/manifest.json` 来注入 hash 后的资源

## 5) 收集静态文件（用于 Nginx 直接提供 /static/）

为了让 Django Admin 等静态资源可被 Nginx 直接服务，建议执行：

```bash
source .venv/bin/activate
python3 manage.py collectstatic --noinput
```

收集目录为 `staticfiles/`（由 `STATIC_ROOT` 决定）。

> 注意：项目在生产模式下仍需要 `static/.vite/manifest.json`（不要删除项目里的 `static/` 目录）。

## 6) Gunicorn 启动（推荐）

在生产环境建议先修改 `library_project/settings.py`：

- `DEBUG = False`
- `ALLOWED_HOSTS = ["example.com", "你的服务器IP"]`

安装 Gunicorn：

```bash
source .venv/bin/activate
pip install gunicorn
```

启动（示例：绑定到本机 8001）：

```bash
source .venv/bin/activate
gunicorn library_project.wsgi:application \
  --bind 127.0.0.1:8001 \
  --workers 2 \
  --timeout 60
```

## 7) Nginx 配置示例

将下面配置保存为 `/etc/nginx/sites-available/library_project.conf`，并启用：

```nginx
server {
    listen 80;
    server_name example.com;  # 改成你的域名或服务器IP

    client_max_body_size 50m;

    # 静态资源（collectstatic 输出目录）
    location /static/ {
        alias /path/to/library_project/staticfiles/;  # 改成你的实际路径
        access_log off;
        expires 7d;
        add_header Cache-Control "public, max-age=604800";
    }

    # 上传媒体文件
    location /media/ {
        alias /path/to/library_project/media/;  # 改成你的实际路径
        access_log off;
        expires 7d;
        add_header Cache-Control "public, max-age=604800";
    }

    # 其余请求交给 Django（包括 SPA 路由与 /api）
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用并重载 Nginx：

```bash
sudo ln -s /etc/nginx/sites-available/library_project.conf /etc/nginx/sites-enabled/library_project.conf
sudo nginx -t
sudo systemctl reload nginx
```

## 8) 生产环境建议

- 生产环境建议 `DEBUG=False` 且配置好 `ALLOWED_HOSTS`
- 使用 HTTPS（建议配合 Certbot/Let’s Encrypt）
- 配置 `SECRET_KEY`（生产不要用仓库里写死的 key）
- 如果启用 HTTPS 且遇到 CSRF 报错，可按需配置 `CSRF_TRUSTED_ORIGINS = ["https://example.com"]`
- 定期备份数据库与 `media/`
