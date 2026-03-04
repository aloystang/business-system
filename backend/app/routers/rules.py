from __future__ import annotations

from fastapi import APIRouter, Depends

from ..deps import get_current_user
from ..services.stage_rules import load_rules

router = APIRouter(prefix="/api/rules", tags=["rules"])


@router.get("/stage")
def get_stage_rules(user=Depends(get_current_user)):
    return load_rules()
