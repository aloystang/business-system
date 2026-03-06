# 免费上线逐步操作手册

这份手册按两台电脑分开写：

- 当前本机：开发机 / 发版机
- 备用 Mac：长期在线运行机

最终效果：

- 前端在 Vercel
- `BidMonitor-AI`、后端、`folo-bridge`、同步、备份、Cloudflare Tunnel 在备用 Mac
- 当前本机关机不影响网站访问

## 0. 你需要准备的账号

在开始前先准备好：

1. 一个 Git 仓库账号
2. 一个 Vercel 账号
3. 一个 Cloudflare 账号
4. 一个域名

推荐域名结构：

- 前端：`app.你的域名`
- 后端：`api.你的域名`

## 1. 当前本机要做什么

### 1.1 把代码放到 Git 仓库

如果你还没把项目放到 GitHub 或别的 Git 服务，先做这一步。

在当前本机：

```bash
cd /Users/aloystang/Desktop/codex
git init
git add .
git commit -m "Prepare home-hosted deployment"
git branch -M main
git remote add origin 你的仓库地址
git push -u origin main
```

如果仓库已经存在，只需要继续正常提交和推送。

注意：命令里的 `你的仓库地址` 是占位文字，不要带尖括号。

### 1.2 在 Vercel 创建前端项目

在浏览器里操作：

1. 打开 Vercel 控制台
2. `Add New` -> `Project`
3. 选择你的 Git 仓库
4. Root Directory 选 `frontend`
5. Build Command 填 `npm run build`
6. Output Directory 填 `dist`
7. 环境变量先不要急着填，等后端域名准备好后再补

当前官方文档：

- [Vite on Vercel](https://vercel.com/docs/frameworks/frontend/vite)

## 2. 备用 Mac 要做什么

### 2.1 安装基础工具

在备用 Mac 打开终端，先确保有这些工具：

- `git`
- `python3`
- `brew`

如果没装 Homebrew，先按 Homebrew 官网方式安装。

### 2.2 拉代码

在备用 Mac：

```bash
cd ~
git clone --recurse-submodules 你的仓库地址 codex
cd ~/codex
```

如果你的目录不想叫 `codex`，可以换，但后面命令里的路径也要一起改。

如果你之前已经用普通 `git clone` 拉过一次，也没关系，`bootstrap_spare_mac.sh` 会补做 `BidMonitor-AI` 子模块初始化。

### 2.3 执行初始化脚本

在备用 Mac：

```bash
cd ~/codex
./ops/home-hosted/scripts/bootstrap_spare_mac.sh
```

这一步会做：

- 初始化 `BidMonitor-AI` 子模块
- 自动应用 `BidMonitor-AI` 的 home-hosted 补丁
- 创建 `backend/.venv`
- 创建 `BidMonitor-AI/.venv`
- 安装 `backend` 和 `folo-bridge` 依赖
- 安装 `BidMonitor-AI` Web 服务依赖
- 复制 `.env.example` 到 `.env`（如果不存在）
- 复制 `subscriptions.example.yaml` 到 `subscriptions.yaml`
- 创建日志目录
- 初始化数据库

### 2.4 编辑备用 Mac 的环境变量

先编辑后端：

```bash
cd ~/codex
nano backend/.env
```

你至少要改这些值：

```dotenv
JWT_SECRET=换成随机长字符串
CORS_ORIGINS=https://app.你的域名,http://localhost:3000,http://127.0.0.1:3000
PUBLIC_SHARE_BASE=https://app.你的域名
DATABASE_URL=sqlite:////Users/你的用户名/codex/backend/data/app.db
UPLOAD_DIR=/Users/你的用户名/codex/backend/data/uploads
EXPORT_DIR=/Users/你的用户名/codex/backend/data/exports
BIDMONITOR_BASE_URL=http://127.0.0.1:8080
BIDMONITOR_PULL_PATH=/api/results
BIDMONITOR_USERNAME=换成新的BidMonitor用户名
BIDMONITOR_PASSWORD=换成新的BidMonitor密码
BIDMONITOR_API_TOKEN=与上面保持一致的 用户名:密码
FOLO_BASE_URL=http://127.0.0.1:9090
FOLO_API_TOKEN=换成私有token
FOLO_SYNC_ENABLED=true
CLOUDFLARED_TUNNEL_TOKEN=先留空，后面去 Cloudflare 拿
BACKUP_DIR=/Users/你的用户名/codex/backups/runtime
BACKUP_RETENTION_DAYS=14
```

注意：

- 不要继续使用默认的 `CDKJ / cdkj`
- `BIDMONITOR_API_TOKEN` 必须和 `BIDMONITOR_USERNAME:BIDMONITOR_PASSWORD` 保持一致

再编辑桥接：

```bash
nano folo-bridge/.env
```

建议至少改：

```dotenv
FOLO_BRIDGE_TOKEN=换成和后端一致或你自己的私有token
FOLO_BRIDGE_DB=/Users/你的用户名/codex/folo-bridge/data/folo_bridge.db
FOLO_BRIDGE_SUBSCRIPTIONS=/Users/你的用户名/codex/folo-bridge/subscriptions.yaml
FOLO_BRIDGE_REFRESH_MINUTES=120
```

### 2.5 配置新闻订阅源

在备用 Mac：

```bash
nano folo-bridge/subscriptions.yaml
```

按你的来源填写，例如：

```yaml
subscriptions:
  - name: 重庆商业观察
    url: https://example.com/rss/chongqing-business.xml
    city: 重庆市
    district: 两江新区
    enabled: true
    tags: ["商业运营", "商圈"]
```

## 3. 在 Cloudflare 里做什么

### 3.1 把域名接入 Cloudflare

在 Cloudflare 仪表盘：

1. `Add a Site`
2. 输入你的域名
3. 按引导把 nameserver 改成 Cloudflare 提供的值
4. 等待域名接入生效

### 3.2 创建 Named Tunnel

按 Cloudflare 当前文档的 dashboard 流程操作：

1. 登录 Cloudflare One
2. 进入 `Networks` -> `Connectors` -> `Cloudflare Tunnels`
3. 点击 `Create a tunnel`
4. 选择 `Cloudflared`
5. 给 tunnel 起名，例如 `codex-spare-mac`
6. 继续到安装步骤

Cloudflare 当前官方文档写的是：在创建 tunnel 后，选择你的运行环境，然后复制它提供的安装/运行命令到终端执行。  
参考：

- [Create a tunnel (dashboard)](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/get-started/create-remote-tunnel/)
- [cloudflared downloads](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/)

### 3.3 在备用 Mac 安装 cloudflared

在备用 Mac：

```bash
brew install cloudflared
```

Cloudflare 文档当前也明确给了 macOS 的 Homebrew 安装方式。

### 3.4 获取 Tunnel Token

在 Cloudflare tunnel 创建流程里，会给你一个 token 或运行命令。

把 token 填回备用 Mac 的：

```bash
nano ~/codex/backend/.env
```

填到：

```dotenv
CLOUDFLARED_TUNNEL_TOKEN=这里填你的 token
```

### 3.5 创建公网主机名

在 Cloudflare Tunnel 的 `Public Hostname` 或应用发布配置里，给它添加：

- Hostname: `api`
- Domain: `你的域名`
- Service Type: `HTTP`
- URL: `http://127.0.0.1:8000`

最终效果应该是：

- `https://api.你的域名` -> 备用 Mac 的本地 `8000`

## 4. 在备用 Mac 上启动线上服务

### 4.1 一键安装 launchd

在备用 Mac：

```bash
cd ~/codex
./ops/home-hosted/scripts/install_launch_agents.sh
```

这会装并加载这些服务：

- `BidMonitor-AI`
- `backend`
- `folo-bridge`
- `cloudflared`
- `intel-sync`
- `backup`

注意：`BidMonitor-AI` 不走公网暴露，只监听备用 Mac 本机的 `127.0.0.1:8080`。

### 4.2 查看状态

在备用 Mac：

```bash
cd ~/codex
API_PUBLIC_BASE=https://api.你的域名 ./ops/home-hosted/scripts/status_home_hosted.sh
```

你应该看到：

- `bidmonitor` 是 `OK`
- `backend` 是 `OK`
- `folo-bridge` 是 `OK`
- `cloudflared` 是 `OK`
- 本地 `8000` / `8080` / `9090` 健康检查通过
- 最近一次 `folo` 和 `bidmonitor` 同步作业能看到结果
- 公网 `https://api.你的域名/health` 通过

如果要看日志：

```bash
ls -lt ~/Library/Logs/codex-home-hosted
tail -f ~/Library/Logs/codex-home-hosted/bidmonitor.err.log
tail -f ~/Library/Logs/codex-home-hosted/backend.err.log
tail -f ~/Library/Logs/codex-home-hosted/cloudflared.err.log
```

## 5. 回到当前本机，完成 Vercel 配置

### 5.1 补前端环境变量

在 Vercel 项目设置里加：

```dotenv
VITE_API_BASE=https://api.你的域名
```

然后重新部署。

### 5.2 绑定前端域名

在 Vercel 项目：

1. `Settings` -> `Domains`
2. `Add Domain`
3. 输入 `app.你的域名`
4. 按 Vercel 提示添加 DNS 记录

Vercel 当前文档：

- [Add and configure domain](https://vercel.com/docs/domains/working-with-domains/add-a-domain)

如果你的 DNS 在 Cloudflare，通常会让你加一个 `CNAME` 到 Vercel 指定地址。

## 6. 做第一次线上验证

### 6.1 在备用 Mac 验证本地服务

```bash
curl -s http://127.0.0.1:8000/health
curl -u 你的BidMonitor用户名:你的BidMonitor密码 -s http://127.0.0.1:8080/api/status
curl -s http://127.0.0.1:9090/health
```

### 6.2 验证公网后端

```bash
curl -s https://api.你的域名/health
```

预期：

```json
{"status":"ok"}
```

### 6.3 验证前端

打开：

```text
https://app.你的域名
```

检查：

1. 登录是否成功
2. 首页是否正常加载
3. 情报中心是否能正常读取数据
4. 招投标是否能正常显示

## 7. 以后怎么发版

### 7.1 在当前本机开发并提交

```bash
cd /Users/aloystang/Desktop/codex
git add .
git commit -m "your change"
git push origin main
```

### 7.2 Vercel 自动更新前端

只要你绑定的是同一个仓库，Vercel 会自动重新构建前端。

### 7.3 让备用 Mac 拉代码并重启服务

在当前本机：

```bash
cd /Users/aloystang/Desktop/codex
./ops/home-hosted/scripts/remote_deploy.sh 你的用户名@备用Mac.local /Users/你的用户名/codex
```

如果你不用 `.local`，也可以直接写 IP，例如：

```bash
./ops/home-hosted/scripts/remote_deploy.sh 你的用户名@192.168.1.23 /Users/你的用户名/codex
```

这个脚本会在备用 Mac 上执行：

- `git pull --ff-only`
- 重启 `BidMonitor-AI`
- 重启 `backend`
- 重启 `folo-bridge`
- 重启 `cloudflared`
- 立即触发一次同步任务

## 8. 备份与恢复

### 8.1 自动备份

当前配置里，备用 Mac 每天 `03:30` 自动执行备份。

默认备份位置：

```text
~/codex/backups/runtime/
```

### 8.2 手动备份

在备用 Mac：

```bash
cd ~/codex
./ops/home-hosted/scripts/backup_runtime_data.sh
```

### 8.3 重要备份内容

- `backend/data/app.db`
- `backend/data/uploads/`
- `backend/data/exports/`
- `folo-bridge/data/folo_bridge.db`
- `folo-bridge/subscriptions.yaml`
- `BidMonitor-AI/server/data/bids.db`
- `BidMonitor-AI/server/server_config.json`

## 9. 常见问题

### 9.1 当前本机关机后网站打不开

不应该。  
如果发生了，说明你把某个服务错误地跑在了当前本机，而不是备用 Mac。

### 9.2 前端能打开，但登录或数据加载失败

优先检查：

1. `https://api.你的域名/health` 是否正常
2. 备用 Mac 上的 `cloudflared` 是否在线
3. `backend` 是否在线
4. Vercel 的 `VITE_API_BASE` 是否指向正确域名

### 9.3 备用 Mac 重启后服务没起来

在备用 Mac：

```bash
./ops/home-hosted/scripts/status_home_hosted.sh
launchctl print "gui/$(id -u)/com.codex.backend"
launchctl print "gui/$(id -u)/com.codex.cloudflared"
```

### 9.4 抓取没更新

先查：

```bash
tail -f ~/Library/Logs/codex-home-hosted/intel-sync.err.log
tail -f ~/Library/Logs/codex-home-hosted/folo-bridge.err.log
tail -f ~/Library/Logs/codex-home-hosted/bidmonitor.err.log
```

再确认：

- `BidMonitor-AI` 是否在线
- `subscriptions.yaml` 是否有有效 RSS/Atom 地址
- `FOLO_SYNC_ENABLED=true`
- `FOLO_BASE_URL=http://127.0.0.1:9090`
- `BIDMONITOR_BASE_URL=http://127.0.0.1:8080`
- `BIDMONITOR_PULL_PATH=/api/results`

## 10. Linear 现在怎么用最合适

现在最实用的方式是新建一个 project：

`Home Hosted Launch`

至少建这些 issue：

1. 购买域名并接入 Cloudflare
2. 创建 Vercel 前端项目
3. 创建 Cloudflare Named Tunnel
4. 备用 Mac 初始化运行环境
5. 配置 backend `.env`
6. 配置 `folo-bridge` 订阅源
7. 安装 `launchd` 服务
8. 完成首次公网验证
9. 验证远程发版流程
10. 完成备份与恢复演练
