import os
import sys
import tempfile
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkstemp()[1]}"
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app.database import Base, engine, SessionLocal  # noqa: E402
from app.auth import get_password_hash  # noqa: E402
from app.models import User, UserRole  # noqa: E402

Base.metadata.create_all(bind=engine)


def seed_admin():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if not existing:
            db.add(
                User(
                    username="admin",
                    password_hash=get_password_hash("admin123"),
                    role=UserRole.admin,
                    is_active=True,
                )
            )
            db.commit()
    finally:
        db.close()


def login(client: TestClient) -> str:
    seed_admin()
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def create_confirmed_project(client: TestClient, headers: dict) -> str:
    payload = {
        "project_name": "筛选测试项目",
        "city": "重庆",
        "district": "渝中区",
        "total_area": 50000,
        "asset_distribution": "混合",
        "ownership_structure": "混合",
        "competition_level": "弱",
        "vacancy_rate": 35,
        "rent_min": 180,
        "rent_max": 260,
        "city_population_10k": 120,
        "population_5km_10k": 45,
        "population_3km_10k": 26,
        "city_circle_level": "二线城市核心商圈/一线城市区域商圈",
        "competition_market_level": "3km内有1个8万㎡同业定位商业项目",
        "housing_price_5km": 18000,
        "disposable_income_10k": 4.8,
        "regional_function_level": "城市级大型商务区",
        "commercial_planning_level": "城市商业区中心核心地点",
        "rail_access_level": "与轨道交通站点100m",
        "arterial_access_level": "有1条城市主干道",
        "bus_access_level": "3条以上公交站点在项目1公里范围内",
        "operation_retrofit_potential_level": "低投入可阶段提升",
        "asset_rights_complexity_level": "权属较清晰协同可控",
    }
    resp = client.post("/api/projects", json=payload, headers=headers)
    assert resp.status_code == 200, resp.text
    project_id = resp.json()["project_id"]

    resp = client.post(f"/api/projects/{project_id}/confirm", headers=headers)
    assert resp.status_code == 200, resp.text
    return project_id


def test_screening_calc_and_latest():
    client = TestClient(app)
    token = login(client)
    headers = {"Authorization": f"Bearer {token}"}

    project_id = create_confirmed_project(client, headers)

    resp = client.post(f"/api/projects/{project_id}/screening/calc", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["calc_version"] == 1
    assert isinstance(data["total_score"], float)
    assert data["conclusion"] in {"不推荐", "一般推荐", "高度推荐", "强烈推荐"}
    assert len(data["indicators"]) == 15
    assert all(item["level"] in [1, 2, 3, 4, 5] for item in data["indicators"])

    resp = client.post(f"/api/projects/{project_id}/screening/calc", headers=headers, json={})
    assert resp.status_code == 200, resp.text
    assert resp.json()["calc_version"] == 2

    resp = client.get(f"/api/projects/{project_id}/screening/latest", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["calc_version"] == 2

    export_resp = client.get(f"/api/projects/{project_id}/export/json", headers=headers)
    assert export_resp.status_code == 200, export_resp.text
    screening_latest = export_resp.json()["screening_latest"]
    assert screening_latest is not None
    assert len(screening_latest["indicators"]) == 15

    override_resp = client.post(
        f"/api/projects/{project_id}/screening/calc",
        headers=headers,
        json={"manual_scores": {"city_population": 1}},
    )
    assert override_resp.status_code == 200, override_resp.text
    city_indicator = next(
        item for item in override_resp.json()["indicators"] if item["key"] == "city_population"
    )
    assert city_indicator["level"] == 1
    assert city_indicator["manual_override"] is True


def test_screening_config_and_missing_fields():
    client = TestClient(app)
    token = login(client)
    headers = {"Authorization": f"Bearer {token}"}

    config_resp = client.get("/api/screening/config", headers=headers)
    assert config_resp.status_code == 200, config_resp.text
    config = config_resp.json()
    assert config["levels"] == [5, 4, 3, 2, 1]
    assert len(config["categories"]) == 6

    payload = {
        "project_name": "缺字段测试项目",
        "city": "重庆",
        "district": "江北区",
        "total_area": 30000,
        "asset_distribution": "集中",
        "ownership_structure": "甲方",
        "competition_level": "中",
    }
    create_resp = client.post("/api/projects", json=payload, headers=headers)
    assert create_resp.status_code == 200, create_resp.text
    project_id = create_resp.json()["project_id"]
    confirm_resp = client.post(f"/api/projects/{project_id}/confirm", headers=headers)
    assert confirm_resp.status_code == 200, confirm_resp.text

    calc_resp = client.post(f"/api/projects/{project_id}/screening/calc", headers=headers)
    assert calc_resp.status_code == 400, calc_resp.text
    detail = calc_resp.json()["detail"]
    assert isinstance(detail, dict)
    assert "missing_fields" in detail
    assert len(detail["missing_fields"]) > 0


def test_screening_history_query_and_kpis():
    client = TestClient(app)
    token = login(client)
    headers = {"Authorization": f"Bearer {token}"}

    marker = f"历史查询-{uuid.uuid4().hex[:8]}"
    payload_a = {
        "project_name": f"{marker}-A",
        "city": "重庆",
        "district": "渝中区",
        "total_area": 42000,
        "asset_distribution": "混合",
        "ownership_structure": "混合",
        "competition_level": "中",
        "city_population_10k": 110,
        "population_5km_10k": 42,
        "population_3km_10k": 24,
        "city_circle_level": "二线城市核心商圈/一线城市区域商圈",
        "competition_market_level": "3km内有1个8万㎡同业定位商业项目",
        "rent_min": 220,
        "rent_max": 300,
        "housing_price_5km": 18000,
        "disposable_income_10k": 4.6,
        "regional_function_level": "城市级大型商务区",
        "commercial_planning_level": "城市商业区中心核心地点",
        "rail_access_level": "与轨道交通站点100m",
        "arterial_access_level": "有1条城市主干道",
        "bus_access_level": "3条以上公交站点在项目1公里范围内",
        "operation_retrofit_potential_level": "低投入可阶段提升",
        "asset_rights_complexity_level": "权属较清晰协同可控",
    }
    create_a = client.post("/api/projects", json=payload_a, headers=headers)
    assert create_a.status_code == 200, create_a.text
    project_a = create_a.json()["project_id"]
    assert client.post(f"/api/projects/{project_a}/confirm", headers=headers).status_code == 200
    calc_a = client.post(f"/api/projects/{project_a}/screening/calc", headers=headers)
    assert calc_a.status_code == 200, calc_a.text
    conclusion_a = calc_a.json()["conclusion"]

    payload_b = {
        "project_name": f"{marker}-B",
        "city": "重庆",
        "district": "江北区",
        "total_area": 18000,
        "asset_distribution": "集中",
        "ownership_structure": "甲方",
        "competition_level": "弱",
    }
    create_b = client.post("/api/projects", json=payload_b, headers=headers)
    assert create_b.status_code == 200, create_b.text
    project_b = create_b.json()["project_id"]
    assert client.post(f"/api/projects/{project_b}/confirm", headers=headers).status_code == 200

    history_all = client.get(f"/api/screening/history?q={marker}", headers=headers)
    assert history_all.status_code == 200, history_all.text
    history_payload = history_all.json()
    assert history_payload["kpis"]["total_projects"] == 2
    assert history_payload["kpis"]["screened_projects"] == 1
    assert len(history_payload["items"]) == 2
    assert {item["screening_status"] for item in history_payload["items"]} == {"screened", "pending"}

    history_screened = client.get(
        f"/api/screening/history?q={marker}&status=screened", headers=headers
    )
    assert history_screened.status_code == 200, history_screened.text
    assert history_screened.json()["kpis"]["total_projects"] == 1
    assert history_screened.json()["items"][0]["project_id"] == project_a

    history_pending = client.get(
        f"/api/screening/history?q={marker}&status=pending", headers=headers
    )
    assert history_pending.status_code == 200, history_pending.text
    assert history_pending.json()["kpis"]["total_projects"] == 1
    assert history_pending.json()["items"][0]["project_id"] == project_b

    history_conclusion = client.get(
        f"/api/screening/history?q={marker}&conclusion={conclusion_a}", headers=headers
    )
    assert history_conclusion.status_code == 200, history_conclusion.text
    assert history_conclusion.json()["kpis"]["total_projects"] == 1
    assert history_conclusion.json()["items"][0]["project_id"] == project_a
