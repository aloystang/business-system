"""敏感项目脱敏：无 map:sensitive 权限者只能看到模糊坐标 / 掩码地址。"""
from __future__ import annotations

import math

from sqlalchemy.orm import Session

from ..config import get_settings
from ..deps import user_has_permission
from ..models import User

_settings = get_settings()


def can_view_sensitive(db: Session, user: User) -> bool:
    return user_has_permission(db, user, "map:sensitive")


def blur_coord(lng: float, lat: float, radius_m: int | None = None) -> tuple[float, float]:
    """把坐标吸附到 ~radius_m 的网格中心，位移不超过约一个模糊半径，且确定性（不抖动）。"""
    radius = radius_m or _settings.sensitive_blur_radius_m
    lat_step = radius / 111_000.0
    lng_step = radius / (111_000.0 * max(math.cos(math.radians(lat)), 0.1))
    blng = round(round(lng / lng_step) * lng_step, 6)
    blat = round(round(lat / lat_step) * lat_step, 6)
    return blng, blat


def mask_point(is_sensitive: bool, allowed: bool, lng: float, lat: float):
    """返回 (lng, lat, blurred)。敏感且无权限 → 模糊坐标。"""
    if is_sensitive and not allowed:
        blng, blat = blur_coord(lng, lat)
        return blng, blat, True
    return lng, lat, False
