import os
import sys
import tempfile
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


def test_create_and_confirm_project():
    client = TestClient(app)
    token = login(client)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "project_name": "测试项目",
        "city": "重庆",
        "district": "渝中区",
        "location_desc": "核心商圈",
        "total_area": 12345.678,
        "rentable_area": 8000.125,
        "core_area": 1000.555,
        "asset_distribution": "集中",
        "ownership_structure": "甲方",
        "vacancy_rate": 12.345,
        "rent_min": 80.126,
        "rent_max": 120.987,
        "main_business_type": "餐饮",
        "competitor_list": "竞品A,竞品B",
        "competition_level": "强",
        "remark": "测试",
    }

    resp = client.post("/api/projects", json=payload, headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["project_id"].startswith("PRJ-")
    assert data["total_area"] == 12345.68
    assert data["rentable_area"] == 8000.13
    assert data["core_area"] == 1000.56
    assert data["rent_min"] == 80.13
    assert data["rent_max"] == 120.99

    project_id = data["project_id"]
    resp = client.post(f"/api/projects/{project_id}/confirm", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["is_confirmed"] == 1


def test_vacancy_rate_validation():
    client = TestClient(app)
    token = login(client)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "project_name": "测试项目2",
        "city": "重庆",
        "district": "渝中区",
        "total_area": 1000,
        "asset_distribution": "集中",
        "ownership_structure": "甲方",
        "competition_level": "中",
        "vacancy_rate": 120,
    }

    resp = client.post("/api/projects", json=payload, headers=headers)
    assert resp.status_code == 400
