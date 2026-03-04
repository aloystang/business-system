from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..auth import authenticate_user, create_access_token
from ..deps import get_current_user, get_db
from ..schemas import LoginRequest, Token, UserOut
from ..services.audit import log_event

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user.username)
    log_event(
        db,
        action="LOGIN",
        entity_type="user",
        entity_id=user.id,
        user_id=user.id,
        ip=request.client.host if request.client else None,
    )
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def me(user=Depends(get_current_user)):
    return user
