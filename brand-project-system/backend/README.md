# 后端 · 品牌与项目资源管理系统

FastAPI + SQLAlchemy。本地开发用 SQLite（零依赖），生产改 `DATABASE_URL` 切 Postgres/PostGIS（见 `../db`）。

## 运行

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head                # 建表（迁移，见下）
python -m app.seed                  # 管理员 + 字典/角色 + 7个真实项目 + 6个模拟品牌
uvicorn app.main:app --reload --port 8020
# OpenAPI 文档：http://127.0.0.1:8020/docs
```

登录：`admin / admin123`。

## 数据库迁移（Alembic）

**Alembic 是应用库的迁移权威**（SQLite 本地 / Postgres 生产通吃），根治 schema drift。

```bash
alembic upgrade head                          # 应用到最新
alembic revision --autogenerate -m "描述"     # 改了模型后生成迁移
alembic downgrade -1                          # 回退一步
alembic current / history                     # 查看版本
```

- 迁移链：`58425d0 baseline`（从 ORM 生成的全部表）→ `25161e8 postgis`（**仅 Postgres**：给 `project_locations` 加 `geom` + 触发器 + GiST 索引 + 定位不变量 CHECK；SQLite 上 no-op）。
- 已在 **PostgreSQL 17.11 + PostGIS** 实测：`upgrade head` 建 29 表、触发器生成 geom、视口 bbox 命中、CHECK 拦截定位失败带坐标、`downgrade` 干净移除 geom。
- 注意：baseline 用 ORM 的 **Python 侧默认值**（`created_at`/`is_sensitive` 等），不是 server_default——应用经 ORM 写入无碍；**裸 SQL** 插入须自带这些 NOT NULL 列。
- `app.seed` 仍带 `create_all` 兜底（绿地便利），但**改表结构一律走 Alembic**（`create_all` 不改已存在表的列）。
- `db/migrations/*.sql` 是另一套「生产 DDL 设计稿」（手写、含更全字段），与 Alembic 的关系见 [../docs/orm-migration-alignment.md](../docs/orm-migration-alignment.md)。

高德地理编码需在 `.env` 配 `AMAP_WEB_KEY`（Web 服务 Key）；留空时 `/geocode` 优雅降级为“定位失败”。

## 已实现模块

| 模块 | 端点 |
|---|---|
| 认证 | `POST /api/v1/auth/login`、`GET /auth/me` |
| 品牌 | `GET /api/v1/brands`、`/brands/{id}` |
| 项目 | `GET /projects`、`/projects/{id}`、`POST /projects`（新建自动解析坐标）、`PUT /projects/{id}/location` |
| 地图 | `GET /map/projects?bbox=`（视口加载，排除定位失败项目） |
| 地理编码 | `POST /geocode`、`/geocode/reverse`（高德适配层） |
| 匹配 | `POST /matches/compute`、`/matches/{id}/adjust`（±10 守卫）、`GET /matches/by-project/{id}` |
| 品牌CRUD | `POST/PATCH/DELETE /brands`、联系人、拓展要求、`POST /brands/{id}/scores`（按规则算等级） |
| 项目扩展 | 项目联系人、`POST /projects/{id}/scores` |
| 候选清单 | `/candidate-lists` + 条目增删改（储备/已接触/洽谈中/已签约/已否决） |
| 沟通/任务 | `/communications`、`/tasks`（`?overdue=`、`/tasks/mine`） |
| 导入中心 | `POST /import/batches`（dry-run 校验）、`/{id}`、`/{id}/commit`、`/{id}/rollback` |
| 字典 | `/dicts`、`/brand-categories/tree`、`/tags` |
| 审核 | `/approvals`、`/approvals/{id}/decide` |
| 数据质量 | `/data-quality/summary`、`/geocode-failed` |
| 工作台 | `GET /dashboard/summary`（KPI/状态分布/匹配等级分布/我的待办逾期） |
| 地图扩展 | `/map/aggregate`（省市区聚合）、`/map/projects/{id}/nearby`（半径）、`/card`、`/layers` |

> **地图空间查询方言自适应**：`/map/projects`(视口)与`/nearby`(周边)在 **Postgres 走 geom+GiST**（`geom && ST_MakeEnvelope` / `ST_DWithin(::geography)`），SQLite 走 lng/lat+半正矢。已在真实 PostgreSQL17.11+PostGIS 端到端实测（alembic upgrade→ORM seed 触发器填 geom→app 查询）：视口命中 6、御临河定位失败被排除、周边悦荟城 2588m。在 Postgres 上跑 app：`export DATABASE_URL=postgresql+psycopg2://…` 后 `alembic upgrade head && python -m app.seed && uvicorn app.main:app`。
| 系统管理 | `/admin/users`(CRUD)、`/admin/roles`、`/admin/permissions`、`/admin/audit-logs`（仅管理员） |
| 铺位 | `/units`（CRUD + 状态：空置/在租/自营/装修） |
| 出租台账 | `/merchants`、`/leases`（建约自动置铺位在租）、`/receivables`（自动算欠租/账龄）、`/project-costs`（项目月度成本） |
| **经营台账** | `GET /projects/{id}/operations`（出租率/收入/成本/**NOI**/收缴率/欠租账龄/坪效/到期）、`GET /dashboard/operations`（首页多项目经营总览：组合KPI/收入成本结构/NOI榜/欠租Top） |
| 铺位匹配/商户评估 | `/unit-matches`（品牌×铺位五维）、`/merchant-assessments`（商户四维→升级/维持/置换） |

## 匹配引擎（`app/matching.py`）

硬门槛 + 八维加权 + 资料覆盖率。权重/阈值/覆盖率下限/调整幅度见模块常量，口径同 `db` 的 `match_rule_versions v1.0`。

## 地图服务适配层（`app/services/map/`）

- `base.MapProvider` 抽象 → `amap.AmapProvider` 实现（业务不认识具体厂商，可换商）。
- `coord.py` 坐标转换 WGS84↔GCJ-02↔BD-09。一期入库口径 GCJ-02。
- `geocoding.py` 强制“定位失败不落坐标”不变量（镜像 DB CHECK）。

## 测试

```bash
pip install -r requirements-dev.txt
python -m pytest --cov=app
```

当前：**69 passed，覆盖率 84%**（单元：匹配引擎/坐标/定位不变量/高德解析/五维评分/Excel导入校验与幂等；集成：认证/地图视口聚合周边卡片/匹配守卫/项目新建解析/品牌CRUD与评分/候选/沟通/任务/字典/审核/导入 dry-run→commit/看板/系统管理RBAC守卫/审计日志）。
