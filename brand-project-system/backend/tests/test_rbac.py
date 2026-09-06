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
