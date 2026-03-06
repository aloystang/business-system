# Project Lifecycle Manager (FastAPI + React + SQLite)

本项目实现商业项目管理系统 V0：数据采集与结构化、项目筛选模型、项目测算模型（双口径自动测算：甲方/华润）。
同时保留了登录、审计日志与基础 PDF 导出等能力，便于后续扩展。

## 目录结构

```
backend/
  app/
  data/
frontend/
```

## 本地启动

### 1) 后端（初始化数据库 + 启动）

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
python3 -m app.init_db
python3 -m uvicorn app.main:app --reload --port 8000
```

如需启用地图地理编码（高德），请先设置：

```bash
cd backend
cat > .env <<'EOF'
AMAP_WEB_KEY=你的高德Web服务Key
MAP_DEFAULT_CITY=贵阳
EOF
```

如需启用 BidMonitor-AI 旁路接入（新闻 + 招投标情报），请补充：

```bash
cd backend
cat >> .env <<'EOF'
BIDMONITOR_BASE_URL=http://127.0.0.1:8080
BIDMONITOR_API_TOKEN=your_bidmonitor_user:your_bidmonitor_password
BIDMONITOR_PULL_PATH=/api/results
INTEL_DEFAULT_CITY=重庆市
EOF
```

如需接入 Folo 作为“新闻旁路数据源”（推荐与 BidMonitor 并行），再补充：

```bash
cd backend
cat >> .env <<'EOF'
FOLO_BASE_URL=http://127.0.0.1:9090
FOLO_API_TOKEN=your_folo_token
FOLO_PULL_PATH=/api/intel/items
FOLO_SYNC_ENABLED=true
EOF
```

同时需要单独启动桥接服务：

```bash
cd /Users/aloystang/Desktop/codex/folo-bridge
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp subscriptions.example.yaml subscriptions.yaml
FOLO_BRIDGE_TOKEN=folo-bridge-token python app.py
```

如果你是新克隆仓库，先初始化 `BidMonitor-AI` 子模块：

```bash
git submodule update --init --recursive BidMonitor-AI
```

默认管理员账号：`admin / admin123`
初始化脚本会创建数据库表并写入 1 条项目种子数据（PRJ-0001）。

OpenAPI 文档：启动后访问 `http://127.0.0.1:8000/docs`

### 运行测试（阶段3）
```bash
cd backend
source .venv/bin/activate
python3 -m pytest
```

#### 局域网访问（可选）

```bash
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

前端在同一局域网内访问：`http://<你的电脑IP>:3000`
如果希望分享链接也生成局域网地址，可在启动后端时设置：
`PUBLIC_SHARE_BASE=http://<你的电脑IP>:3000`

### 2) 前端（启动）

```bash
cd frontend
npm install
VITE_API_BASE=http://127.0.0.1:8000 npm run dev
```

如需启用首页真实地图（高德 JS SDK）：

```bash
VITE_API_BASE=http://127.0.0.1:8000 \
VITE_AMAP_JS_KEY=你的高德JSAPIKey \
VITE_MAP_DEFAULT_CITY=贵阳 \
npm run dev
```

浏览器访问：`http://localhost:3000`

## 核心能力

- 登录认证：`POST /api/auth/login`
- 项目基础信息：`/api/projects`（本阶段用于V0流程）
- 数据采集：`POST /api/intakes`、`POST /api/intakes/{id}/confirm`
- 项目筛选：`POST /api/projects/{project_id}/screening/calc`
- 测算配置：`GET /api/calc/config`
- 双口径自动测算：`POST /api/projects/{project_id}/calc/auto`
- 兼容测算接口：`/api/projects/{project_id}/calc/asset_owner|internal|merchant`
- 导出 JSON：`GET /api/projects/{project_id}/export/json`
- PDF 导出：`POST /api/projects/{id}/export/pdf`
- 地图看板 KPI：`GET /api/overview/map/kpis`
- 地图点位列表：`GET /api/overview/map/points`
- 地图点位详情：`GET /api/overview/map/point/{point_id}`
- 情报看板 KPI：`GET /api/intel/kpis`
- 情报列表：`GET /api/intel/items`
- 情报详情：`GET /api/intel/items/{id}`
- 情报关联项目：`POST /api/intel/items/{id}/link-project`
- 手动同步（admin/manager）：`POST /api/intel/sync/run`
  - `source_system=bidmonitor|folo|all`（推荐 `all`）
- 同步作业历史（admin/manager）：`GET /api/intel/sync/jobs`
- 订阅规则管理：`GET|POST|PUT|DELETE /api/intel/rules`

## 阶段门槛规则

规则文件：`backend/app/rules/stage_requirements.yaml`

校验逻辑：在进入下一阶段时检查目标阶段的必填字段与必备交付物类型。

## 文件与导出位置

- 上传文件：`backend/data/uploads`
- 导出 PDF：`backend/data/exports`
- SQLite：`backend/data/app.db`

## Docker Compose（可选）

本仓库暂未提供 `docker-compose.yml`，建议先按上面的本地方式启动前后端。

## 免费上线方案（开发机 + 备用 Mac）

如果你想让当前这台电脑只负责开发，而让另一台常开 Mac 负责后端、抓取和同步，可直接使用：

- [home-hosted README](./ops/home-hosted/README.md)

这套方案默认：

- 前端部署到 Vercel
- 后端、`folo-bridge`、定时同步、备份和 Cloudflare Tunnel 运行在备用 Mac
- 当前本机只负责开发、提交代码、触发发版和维护备用 Mac

## 注意事项

- `init_db` 会自动创建表，并写入默认管理员账号。
- 如需修改阶段规则，请编辑 YAML 并重启后端。
- 目前 PDF 为简单模板，后续可扩展为更复杂样式。
- BidMonitor 旁路同步默认建议每日4次：00:00 / 06:00 / 12:00 / 18:00（可用系统 cron 调 `python -m app.intel_sync_worker`）。
- macOS 若提示 `python` 不存在，请直接使用 `python3` / `pip3`，或设置别名：

```bash
echo 'alias python=python3' >> ~/.zshrc
echo 'alias pip=pip3' >> ~/.zshrc
source ~/.zshrc
```

## 最小回归步骤（从新增项目到双口径自动测算）

1. 登录系统（默认 `admin / admin123`）  
2. 进入“项目列表” → 新建项目（填写必填字段）  
3. 点击项目名称进入详情 → 保存基础信息  
4. 点击“确认数据”  
5. 系统自动触发双口径测算（甲方/华润）  
6. 进入“项目测算”页查看双口径汇总与10年明细  
7. 如需调参，展开“高级参数”后点击“重新计算并存档”  
8. 点击“计算筛选”按钮 → 查看筛选结果  
9. 如需导出 JSON：访问 `/api/projects/{project_id}/export/json`  

## 外部分享（V3）

1) 在项目详情总览页开启 `external_enabled` 并保存  
2) 点击“生成分享链接”，获得 `share_url`  
3) 浏览器打开 `/share/<token>`（无需登录）  
4) 外部页面支持查看对外字段、对外交付物列表、下载对外 PDF  

## BidMonitor-AI 旁路接入数据协议

本系统默认向 `BIDMONITOR_BASE_URL + BIDMONITOR_PULL_PATH` 拉取 JSON，并支持两种响应格式：

1. 直接数组：`[ {...}, {...} ]`  
2. 包装对象：`{ "items": [ ... ] }`（或 `data/results/rows`）

单条记录建议字段（最小集）：

```json
{
  "item_type": "news | tender",
  "title": "标题",
  "source_name": "来源",
  "published_at": "2026-02-25 10:00:00",
  "city": "重庆市",
  "district": "两江新区",
  "summary": "摘要",
  "raw_url": "https://...",
  "budget_amount": 1200,
  "deadline_at": "2026-03-05 18:00:00",
  "issuer": "发布方"
}
```

你也可以直接用手动同步接口测试：

```bash
POST /api/intel/sync/run
{
  "source_system": "all",
  "item_type": "all",
  "payload_items": [ ... ]
}
```
