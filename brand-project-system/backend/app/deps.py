"""依赖：当前用户。"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import Permission, RolePermission, User, UserRole
from .security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme),
                     db: Session = Depends(get_db)) -> User:
    err = HTTPException(status.HTTP_401_UNAUTHORIZED, "登录状态无效或已过期",
                        headers={"WWW-Authenticate": "Bearer"})
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise err
    user = db.query(User).filter(User.username == payload["sub"]).first()
    if not user or not user.is_active:
        raise err
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "需要系统管理员权限")
    return user


def user_has_permission(db: Session, user: User, code: str) -> bool:
    """用户是否经其角色拥有某权限点（admin 主角色直接放行）。"""
    if user.role == "admin":
        return True
    hit = (db.query(Permission.id)
           .join(RolePermission, RolePermission.permission_id == Permission.id)
           .join(UserRole, UserRole.role_id == RolePermission.role_id)
           .filter(UserRole.user_id == user.id, Permission.code == code)
           .first())
    return hit is not None


def require_perm(code: str):
    """生成一个校验指定权限点的依赖。写操作路由统一挂它。"""
    def _dep(user: User = Depends(get_current_user),
             db: Session = Depends(get_db)) -> User:
        if not user_has_permission(db, user, code):
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"缺少权限：{code}")
        return user
    return _dep
