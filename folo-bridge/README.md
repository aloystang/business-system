# Folo Bridge

本服务不是完整的 Folo 自托管后端。

它的职责只有一个：把你配置的新闻订阅源转换成主系统可消费的标准 JSON，作为 `新闻资讯` 的旁路数据源。

## 启动

```bash
cd /Users/aloystang/Desktop/codex/folo-bridge
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cp subscriptions.example.yaml subscriptions.yaml
FOLO_BRIDGE_TOKEN=folo-bridge-token python app.py
```

默认端口：`9090`

## 配置订阅源

编辑：

`/Users/aloystang/Desktop/codex/folo-bridge/subscriptions.yaml`

格式：

```yaml
subscriptions:
  - name: 重庆商业观察
    url: https://example.com/rss/chongqing-business.xml
    city: 重庆市
    district: 两江新区
    enabled: true
    tags: ["商业运营", "商圈"]
```

## 接口

- `GET /health`
- `GET /api/subscriptions`
- `POST /api/refresh`
- `GET /api/intel/items?page=1&page_size=20`

认证方式：

- `Authorization: Bearer <FOLO_BRIDGE_TOKEN>`
- 或 `X-API-Token: <FOLO_BRIDGE_TOKEN>`

## 与主系统对接

主系统后端 `.env`：

```env
FOLO_BASE_URL=http://127.0.0.1:9090
FOLO_API_TOKEN=folo-bridge-token
FOLO_PULL_PATH=/api/intel/items
FOLO_SYNC_ENABLED=true
```

然后重启主系统后端，在情报中心点“手动同步”即可。

如果你要走“当前本机开发，备用 Mac 线上运行”的部署方式，统一看：

- [home-hosted deployment](../ops/home-hosted/README.md)
