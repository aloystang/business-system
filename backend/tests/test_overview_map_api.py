import os
import sys
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkstemp()[1]}"
os.environ["AMAP_WEB_KEY"] = ""
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.auth import get_password_hash  # noqa: E402
from app.models import SurveyCompetitorItem, SurveyMerchantItem, User, UserRole  # noqa: E402

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


def _create_project_with_survey(client: TestClient, headers: dict) -> str:
    payload = {
        "project_name": "地图测试项目",
        "city": "贵阳",
        "district": "观山湖区",
        "total_area": 26000,
        "asset_distribution": "集中",
        "ownership_structure": "甲方",
        "competition_level": "中",
        "merchant_rows": [
            {
                "name": "测试商家A",
                "category": "餐饮",
                "area_m2": 180,
                "rent_unit_price": 220,
                "daily_flow": 1600,
                "address": "观山湖区会展城A区1层",
                "city": "贵阳",
                "district": "观山湖区",
                "note": "样例",
            }
        ],
        "competition_rows": [
            {
                "name": "竞品广场B",
                "scale_m2": 50000,
                "avg_rent_unit_price": 260,
                "vacancy_rate": 12,
                "business_type": "购物中心",
                "distance_km": 3.2,
                "target_people": "白领家庭",
                "address": "观山湖区金融城B区",
                "city": "贵阳",
                "district": "观山湖区",
            }
        ],
    }
    resp = client.post("/api/projects", json=payload, headers=headers)
    assert resp.status_code == 200, resp.text
    project = resp.json()
    assert len(project.get("merchant_rows") or []) == 1
    assert len(project.get("competition_rows") or []) == 1
    assert project["merchant_rows"][0]["geocode_status"] in {"needs_key", "success"}
    return project["project_id"]


def test_survey_rows_saved_and_returned():
    client = TestClient(app)
    token = login(client)
    headers = {"Authorization": f"Bearer {token}"}
    project_id = _create_project_with_survey(client, headers)

    detail_resp = client.get(f"/api/projects/{project_id}", headers=headers)
    assert detail_resp.status_code == 200, detail_resp.text
    detail = detail_resp.json()
    assert len(detail.get("merchant_rows") or []) == 1
    assert len(detail.get("competition_rows") or []) == 1
    assert detail["competition_rows"][0]["geocode_status"] in {"needs_key", "success"}


def test_overview_map_endpoints():
    client = TestClient(app)
    token = login(client)
    headers = {"Authorization": f"Bearer {token}"}
    project_id = _create_project_with_survey(client, headers)

    db = SessionLocal()
    try:
        merchant = db.query(SurveyMerchantItem).filter(SurveyMerchantItem.project_id == project_id).first()
        competitor = (
            db.query(SurveyCompetitorItem).filter(SurveyCompetitorItem.project_id == project_id).first()
        )
        assert merchant is not None
        assert competitor is not None

        merchant.geocode_status = "success"
        merchant.longitude = 106.632
        merchant.latitude = 26.643
        competitor.geocode_status = "success"
        competitor.longitude = 106.635
        competitor.latitude = 26.646
        db.commit()
    finally:
        db.close()

    kpi_resp = client.get("/api/overview/map/kpis?city=贵阳", headers=headers)
    assert kpi_resp.status_code == 200, kpi_resp.text
    kpi = kpi_resp.json()
    assert kpi["total_points"] >= 2
    assert kpi["merchant_count"] >= 1
    assert kpi["competitor_count"] >= 1

    points_resp = client.get("/api/overview/map/points?city=贵阳&type=all", headers=headers)
    assert points_resp.status_code == 200, points_resp.text
    points = points_resp.json()
    assert points["total"] >= 2
    assert len(points["items"]) >= 2

    detail_resp = client.get(
        f"/api/overview/map/point/{points['items'][0]['point_id']}",
        headers=headers,
    )
    assert detail_resp.status_code == 200, detail_resp.text
    detail = detail_resp.json()
    assert detail["project_id"] == project_id


def test_hanglian_square_visible_with_manual_point():
    client = TestClient(app)
    token = login(client)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "project_name": "港莲广场项目",
        "city": "贵阳",
        "district": "观山湖区",
        "total_area": 18000,
        "asset_distribution": "集中",
        "ownership_structure": "甲方",
        "competition_level": "中",
        "merchant_rows": [
            {
                "name": "港莲广场",
                "category": "商业综合体",
                "area_m2": 32000,
                "rent_unit_price": 180,
                "daily_flow": 8500,
                "address": "观山湖区港莲广场",
                "city": "贵阳",
                "district": "观山湖区",
                "longitude": 106.624156,
                "latitude": 26.646629,
                "note": "手动选点样例",
            }
        ],
        "competition_rows": [],
    }
    create_resp = client.post("/api/projects", json=payload, headers=headers)
    assert create_resp.status_code == 200, create_resp.text
    project = create_resp.json()
    assert project["merchant_rows"][0]["geocode_status"] == "success"
    assert project["merchant_rows"][0]["geocode_message"] == "manual_pick"

    points_resp = client.get(
        "/api/overview/map/points?city=贵阳&type=merchant&keyword=港莲广场",
        headers=headers,
    )
    assert points_resp.status_code == 200, points_resp.text
    items = points_resp.json()["items"]
    assert any(item["name"] == "港莲广场" for item in items)
