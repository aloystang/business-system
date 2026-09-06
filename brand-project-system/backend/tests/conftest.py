"""pytest 夹具：隔离的内存 SQLite + 已鉴权客户端 + 最小种子。"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import (
    Brand, BrandExpansion, Dictionary, Project, ProjectLocation, Role, User, UserRole,
)
from app.security import hash_password

# 单连接内存库，测试间共享 schema
_engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                        poolclass=StaticPool, future=True)
TestingSessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False,
                                   future=True)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


def _seed(db):
    for code, name in [("admin", "管理员"), ("viewer", "查看者"), ("brand_bd", "拓展")]:
        db.add(Role(code=code, name=name))
    db.flush()
    admin = User(username="admin", display_name="管理员",
                 password_hash=hash_password("admin123"), role="admin")
    db.add(admin)
    db.flush()
    db.add(UserRole(user_id=admin.id,
                    role_id=db.query(Role).filter(Role.code == "admin").first().id))
    for i, label in enumerate(["体育场馆商业", "购物中心", "商业街区", "社区商业"], 1):
        db.add(Dictionary(dict_type="project_type", code=label, label=label, sort_no=i))
    for i, label in enumerate(["筹备", "招商中", "已开业"], 1):
        db.add(Dictionary(dict_type="project_status", code=label, label=label, sort_no=i))
    # 品牌 A：接受体育场馆
    ba = Brand(brand_code="B-A", brand_name="迪卡侬", l1_category="零售",
               cooperation_intent="较强")
    db.add(ba); db.flush()
    db.add(BrandExpansion(brand_id=ba.id, target_cities="重庆",
                          acceptable_project_types="体育场馆商业;购物中心",
                          accept_stadium_commercial=True, area_min=800, area_max=2500))
    # 品牌 B：不接受体育场馆
    bb = Brand(brand_code="B-B", brand_name="海底捞", l1_category="餐饮",
               cooperation_intent="一般")
    db.add(bb); db.flush()
    db.add(BrandExpansion(brand_id=bb.id, target_cities="重庆",
                          acceptable_project_types="购物中心;商业街区",
                          accept_stadium_commercial=False, area_min=600, area_max=1200))
    # 项目 1：体育场馆，有坐标
    p1 = Project(project_code="P-1", project_name="龙兴足球场", project_type="体育场馆商业",
                 project_status="招商中", business_area_m2=160958,
                 target_formats="零售;文体娱乐;餐饮", core_customers="球迷", cooperation_will="强")
    db.add(p1); db.flush()
    db.add(ProjectLocation(project_id=p1.id, province="重庆市", city="重庆市",
                           district="两江新区", address="龙兴镇", longitude=106.7315,
                           latitude=29.6902, geocoding_status="人工确认"))
    # 项目 2：购物中心，有坐标
    p2 = Project(project_code="P-2", project_name="两江悦荟城", project_type="购物中心",
                 project_status="招商中", business_area_m2=17530,
                 target_formats="餐饮;零售", core_customers="家庭", cooperation_will="较强")
    db.add(p2); db.flush()
    db.add(ProjectLocation(project_id=p2.id, province="重庆市", city="重庆市",
                           district="两江新区", address="龙兴", longitude=106.7208,
                           latitude=29.6688, geocoding_status="自动定位"))
    # 项目 3：定位失败，无坐标（应被地图排除）
    p3 = Project(project_code="P-3", project_name="御临河商业", project_type="商业街区",
                 project_status="筹备", business_area_m2=5584)
    db.add(p3); db.flush()
    db.add(ProjectLocation(project_id=p3.id, province="重庆市", city="重庆市",
                           district="两江新区", address="御临河", geocoding_status="定位失败"))
    db.commit()


@pytest.fixture(scope="session", autouse=True)
def _db():
    Base.metadata.create_all(_engine)
    db = TestingSessionLocal()
    _seed(db)
    db.close()
    yield
    Base.metadata.drop_all(_engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def token(client):
    r = client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin123"})
    return r.json()["access_token"]


@pytest.fixture
def auth(token):
    return {"Authorization": f"Bearer {token}"}
