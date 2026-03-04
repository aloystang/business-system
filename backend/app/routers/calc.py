from __future__ import annotations

from fastapi import APIRouter, Depends

from ..deps import get_current_user
from ..schemas import CalcConfigOut
from ..services.calc_config import get_calc_config_payload

router = APIRouter(prefix="/api/calc", tags=["calc"])


@router.get("/config", response_model=CalcConfigOut)
def get_calc_config(
    user=Depends(get_current_user),
):
    _ = user
    return get_calc_config_payload()
