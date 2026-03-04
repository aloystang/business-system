import os
import sys
import tempfile
from pathlib import Path

import pytest
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
        "project_name": "测算测试项目",
        "city": "重庆",
        "district": "渝中区",
        "total_area": 20000,
        "rentable_area": 1000,
        "asset_distribution": "集中",
        "ownership_structure": "甲方",
        "competition_level": "中",
        "vacancy_rate": 20,
        "rent_min": 80,
        "rent_max": 100,
    }
    resp = client.post("/api/projects", json=payload, headers=headers)
    assert resp.status_code == 200, resp.text
    project_id = resp.json()["project_id"]

    resp = client.post(f"/api/projects/{project_id}/confirm", headers=headers)
    assert resp.status_code == 200, resp.text
    return project_id


def test_calc_endpoints_and_latest():
    client = TestClient(app)
    token = login(client)
    headers = {"Authorization": f"Bearer {token}"}

    project_id = create_confirmed_project(client, headers)

    # Auto calc should be generated on confirm
    resp = client.get(f"/api/projects/{project_id}/calc/asset_owner/latest", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["calc_version"] == 1
    assert isinstance(resp.json().get("yearly"), list)

    # Asset owner manual
    resp = client.post(
        f"/api/projects/{project_id}/calc/asset_owner",
        headers=headers,
        json={"target_rent": 100, "target_occupancy": 80, "invest_cost": 100000},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["calc_version"] == 2
    assert data["annual_rent_income"] == pytest.approx(960000)
    assert data["roi"] == pytest.approx(9.6)

    resp = client.post(
        f"/api/projects/{project_id}/calc/asset_owner",
        headers=headers,
        json={"target_rent": 100, "target_occupancy": 0.8, "invest_cost": 100000},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["calc_version"] == 3

    # Internal
    resp = client.post(
        f"/api/projects/{project_id}/calc/internal",
        headers=headers,
        json={"service_fee_rate": 0.1, "manage_fee_rate": 0.05, "staff_cost": 1000, "other_cost": 2000},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["annual_rent_for_calc"] == pytest.approx(864000)
    assert data["total_income"] == pytest.approx(129600)
    assert data["total_profit"] == pytest.approx(126600)

    # Merchant
    resp = client.post(
        f"/api/projects/{project_id}/calc/merchant",
        headers=headers,
        json={
            "shop_area": 100,
            "shop_rent": 50,
            "daily_flow": 1000,
            "avg_ticket": 20,
            "annual_cost": 500000,
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["annual_revenue"] == pytest.approx(7300000)
    assert data["break_even_rent"] == pytest.approx(5666.6667, rel=1e-3)

    # Latest endpoint
    resp = client.get(f"/api/projects/{project_id}/calc/asset_owner/latest", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["calc_version"] == 3

    resp = client.get(f"/api/projects/{project_id}/calc/internal/latest", headers=headers)
    assert resp.status_code == 200, resp.text

    resp = client.get(f"/api/projects/{project_id}/calc/merchant/latest", headers=headers)
    assert resp.status_code == 200, resp.text


def test_calc_config_and_auto_endpoint():
    client = TestClient(app)
    token = login(client)
    headers = {"Authorization": f"Bearer {token}"}
    project_id = create_confirmed_project(client, headers)

    config_resp = client.get("/api/calc/config", headers=headers)
    assert config_resp.status_code == 200, config_resp.text
    config_data = config_resp.json()
    assert config_data["planning_years"] == 10
    assert len(config_data["advanced_params"]) == 5

    auto_resp = client.post(
        f"/api/projects/{project_id}/calc/auto",
        headers=headers,
        json={
            "overrides": {
                "rent_base": 120,
                "leasing_commission_months": 3,
                "operation_commission_rate": 0.1,
                "occupancy_curve": [0.7, 0.8, 0.85, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9],
                "rent_growth_curve": [0, 0, 0.05, 0, 0, 0.05, 0, 0, 0.03, 0.03],
            }
        },
    )
    assert auto_resp.status_code == 200, auto_resp.text
    auto = auto_resp.json()
    assert auto["calc_version"] >= 2
    assert auto["external"]["calc_basis"] == "owner_v1"
    assert auto["internal"]["calc_basis"] == "huarun_v1"
    assert len(auto["external"]["yearly"]) == 10
    assert len(auto["internal"]["yearly"]) == 10
    assert auto["external"]["params_used"]["rent_base"] == 120

    export_resp = client.get(f"/api/projects/{project_id}/export/json", headers=headers)
    assert export_resp.status_code == 200, export_resp.text
    export_data = export_resp.json()
    assert export_data["calc_asset_owner_latest"]["summary"]["total_revenue"] is not None
    assert len(export_data["calc_asset_owner_latest"]["yearly"]) == 10
    assert export_data["calc_internal_latest"]["summary"]["tax_after_profit"] is not None
