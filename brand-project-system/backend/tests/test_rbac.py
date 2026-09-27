"""RBAC 权限点强制：无权限用户写操作应 403，有权限角色应放行。"""
from __future__ import annotations

import pytest

from app.database import get_db
from app.main import app
from app.models import Permission, Role, RolePermission, User, UserRole
from app.security import hash_password


def _session():
    return next(app.dependency_overrides[get_db]())


def _ensure_user(db, username, role_code, perm_codes=()):
    if db.query(User).filter(User.username == username).first():
        return
    role = db.query(Role).filter(Role.code == role_code).first()
    if not role:
        role = Role(code=role_code, name=role_code)
        db.add(role); db.flush()
    for pc in perm_codes:
        perm = db.query(Permission).filter(Permission.code == pc).first()
        if not perm:
            perm = Permission(code=pc, name=pc, resource=pc.split(":")[0],
                              action=pc.split(":")[1])
            db.add(perm); db.flush()
        link = db.query(RolePermission).filter(
            RolePermission.role_id == role.id,
            RolePermission.permission_id == perm.id).first()
        if not link:
            db.add(RolePermission(role_id=role.id, permission_id=perm.id))
    u = User(username=username, display_name=username,
             password_hash=hash_password("pw123456"), role=role_code)
    db.add(u); db.flush()
    db.add(UserRole(user_id=u.id, role_id=role.id))
    db.commit()


@pytest.fixture(autouse=True)
def _users():
    db = _session()
    _ensure_user(db, "viewer1", "viewer")                       # 无写权限
    _ensure_user(db, "bd1", "brand_bd", ["brand:write"])        # 有品牌写权限
    db.close()


def _token(client, username):
    r = client.post("/api/v1/auth/login", data={"username": username, "password": "pw123456"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_viewer_cannot_create_brand(client):
    r = client.post("/api/v1/brands", headers=_token(client, "viewer1"),
                    json={"brand_code": "RBAC-V1", "brand_name": "越权测试"})
    assert r.status_code == 403


def test_bd_can_create_brand(client):
    r = client.post("/api/v1/brands", headers=_token(client, "bd1"),
                    json={"brand_code": "RBAC-BD1", "brand_name": "拓展建品牌"})
    assert r.status_code == 201


def test_viewer_cannot_run_import_or_dict(client):
    h = _token(client, "viewer1")
    assert client.post("/api/v1/dicts", headers=h,
                       json={"dict_type": "x", "code": "y", "label": "y"}).status_code == 403


# ---------- 回归：seed_role_permissions 必须真正把角色→权限点写进库 ----------
# （历史 bug：roles/permissions 表已建时整段种子被跳过，role_permissions 从未写入，
#   导致除 admin 外所有角色登录后权限点为 0——这里独立验证该回填函数本身。）

def test_seed_role_permissions_backfills_from_empty(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.database import Base
    from app.models import Permission, Role, RolePermission
    from app.seed import PERMISSIONS, ROLES, seed_role_permissions

    eng = create_engine("sqlite://", connect_args={"check_same_thread": False},
                        poolclass=StaticPool, future=True)
    Base.metadata.create_all(eng)
    s = sessionmaker(bind=eng, future=True)()
    for code, name in ROLES:
        s.add(Role(code=code, name=name))
    for code, name, res, act in PERMISSIONS:
        s.add(Permission(code=code, name=name, resource=res, action=act))
    s.flush()

    assert s.query(RolePermission).count() == 0   # 回填前应为空（模拟历史坏库）
    added = seed_role_permissions(s)
    s.commit()
    assert added > 0
    viewer = s.query(Role).filter(Role.code == "viewer").first()
    viewer_perms = {p.code for p in s.query(Permission).join(
        RolePermission, RolePermission.permission_id == Permission.id
    ).filter(RolePermission.role_id == viewer.id).all()}
    assert "brand:read" in viewer_perms and "brand:write" not in viewer_perms
    # 再跑一次不应重复插入（幂等）
    assert seed_role_permissions(s) == 0
    s.close()
