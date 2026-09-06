"""认证路由。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import TokenOut, UserOut
from ..security import create_access_token, verify_password
from ..services.ratelimit import login_limiter

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])
settings = get_settings()


@router.post("/login", response_model=TokenOut)
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(),
          db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    key = f"{client_ip}:{form.username}"
    if login_limiter.is_blocked(key, settings.login_max_failures, settings.login_window_seconds):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                            "登录失败次数过多，请稍后再试")
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        login_limiter.record_failure(key, settings.login_window_seconds)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户名或密码错误")
    login_limiter.reset(key)  # 成功即清零，正常用户不受影响
    return TokenOut(access_token=create_access_token(user.username, user.role))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
