"""系统管理：用户 / 角色 / 权限 / 操作日志。仅管理员。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_admin
from ..models import AuditLog, Permission, Role, User, UserRole
from ..schemas import (
    AuditLogOut, PermissionOut, RoleOut, UserAdminOut, UserCreate, UserUpdate,
)
from ..security import hash_password
from ..services.audit import record

router = APIRouter(prefix="/api/v1/admin", tags=["系统管理"])


def _sync_user_role(db: Session, user: User, role_code: str) -> None:
    """同步 user_roles：以 role_code 对应的 Role 为唯一角色（简化）。"""
    role = db.query(Role).filter(Role.code == role_code).first()
    db.query(UserRole).filter(UserRole.user_id == user.id).delete()
    if role:
        db.add(UserRole(user_id=user.id, role_id=role.id))


@router.get("/users", response_model=list[UserAdminOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(User).order_by(User.id).all()


@router.post("/users", response_model=UserAdminOut, status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db),
                admin: User = Depends(require_admin)):
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(409, f"用户名已存在：{body.username}")
    if not db.query(Role).filter(Role.code == body.role).first():
        raise HTTPException(400, f"角色不存在：{body.role}")
    u = User(username=body.username, display_name=body.display_name,
             password_hash=hash_password(body.password), role=body.role,
             email=body.email, phone=body.phone, is_active=True)
    db.add(u)
    db.flush()
    _sync_user_role(db, u, body.role)
    record(db, admin, "create", "user", u.id, {"username": u.username, "role": u.role})
    db.commit()
    db.refresh(u)
    return u


@router.patch("/users/{user_id}", response_model=UserAdminOut)
def update_user(user_id: int, body: UserUpdate, db: Session = Depends(get_db),
                admin: User = Depends(require_admin)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "用户不存在")
    data = body.model_dump(exclude_unset=True)
    if "role" in data and not db.query(Role).filter(Role.code == data["role"]).first():
        raise HTTPException(400, f"角色不存在：{data['role']}")
    for k, v in data.items():
        setattr(u, k, v)
    if "role" in data:
        _sync_user_role(db, u, data["role"])
    record(db, admin, "update", "user", u.id)
    db.commit()
    db.refresh(u)
    return u


@router.get("/roles", response_model=list[RoleOut])
def list_roles(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(Role).order_by(Role.id).all()


@router.get("/permissions", response_model=list[PermissionOut])
def list_permissions(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(Permission).order_by(Permission.resource, Permission.action).all()


@router.get("/audit-logs", response_model=list[AuditLogOut])
def audit_logs(entity_type: str | None = None, actor_id: int | None = None,
               action: str | None = None, limit: int = 100,
               db: Session = Depends(get_db), _: User = Depends(require_admin)):
    q = db.query(AuditLog)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if actor_id is not None:
        q = q.filter(AuditLog.actor_id == actor_id)
    if action:
        q = q.filter(AuditLog.action == action)
    return q.order_by(AuditLog.created_at.desc()).limit(min(limit, 500)).all()
