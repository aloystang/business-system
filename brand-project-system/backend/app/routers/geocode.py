"""地理编码路由（高德适配层）。"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..deps import get_current_user
from ..schemas import GeocodeIn, GeocodeResultOut, ReverseIn
from ..services.geocoding import geocode_address
from ..services.map import get_map_provider

router = APIRouter(prefix="/api/v1/geocode", tags=["地理编码"])


def _to_out(r) -> GeocodeResultOut:
    return GeocodeResultOut(
        longitude=r.longitude, latitude=r.latitude, coordinate_system=r.coordinate_system,
        provider=r.provider, level=r.level, accuracy=r.accuracy, geocoding_status=r.status,
        formatted_address=r.formatted_address, candidates=r.candidates,
    )


@router.post("", response_model=GeocodeResultOut)
def geocode(body: GeocodeIn, _=Depends(get_current_user)):
    """地址→坐标。失败返回 geocoding_status=定位失败，不给错误坐标。"""
    return _to_out(geocode_address(body.address, body.city))


@router.post("/reverse", response_model=GeocodeResultOut)
def reverse(body: ReverseIn, _=Depends(get_current_user)):
    return _to_out(get_map_provider().reverse_geocode(body.longitude, body.latitude))
