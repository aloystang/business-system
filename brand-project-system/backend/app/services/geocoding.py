"""定位服务：解析地址 + 强制“定位失败不落坐标”不变量（镜像 DB CHECK）。"""
from __future__ import annotations

from ..models import ProjectLocation
from .map import GeocodeResult, get_map_provider

# 携带坐标的合法状态
_COORD_STATUSES = {"自动定位", "人工确认", "人工修正"}
# 不得携带坐标的状态
_NO_COORD_STATUSES = {"定位失败", "待定位"}


class LocationInvariantError(ValueError):
    """定位状态与坐标不一致。"""


def enforce_location_invariant(
    status: str, lng: float | None, lat: float | None
) -> None:
    """状态∈成功集必须有坐标；∈失败集必须无坐标。否则抛错。"""
    has_coords = lng is not None and lat is not None
    if status in _NO_COORD_STATUSES and has_coords:
        raise LocationInvariantError(f"状态“{status}”不得携带坐标")
    if status in _COORD_STATUSES and not has_coords:
        raise LocationInvariantError(f"状态“{status}”必须携带坐标")
    if status not in _COORD_STATUSES and status not in _NO_COORD_STATUSES:
        raise LocationInvariantError(f"未知定位状态：{status}")


def geocode_address(address: str, city: str | None = None) -> GeocodeResult:
    """通过适配层解析地址（不认识具体厂商）。"""
    return get_map_provider().geocode(address, city)


def apply_geocode(loc: ProjectLocation, result: GeocodeResult) -> None:
    """把解析结果写入 ProjectLocation，保证不变量：失败则清空坐标。"""
    if result.ok:
        loc.longitude = result.longitude
        loc.latitude = result.latitude
        loc.coordinate_system = result.coordinate_system
        loc.geocoding_status = result.status
        loc.geocoding_provider = result.provider
    else:
        loc.longitude = None
        loc.latitude = None
        loc.geocoding_status = "定位失败"
        loc.geocoding_provider = result.provider
    enforce_location_invariant(loc.geocoding_status, loc.longitude, loc.latitude)
