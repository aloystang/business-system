"""地图服务工厂：按配置装配 Provider，业务代码不认识具体厂商。"""
from __future__ import annotations

from functools import lru_cache

from ...config import get_settings
from .amap import AmapProvider
from .base import GeocodeResult, MapProvider

_PROVIDERS = {"amap": AmapProvider}


@lru_cache
def get_map_provider() -> MapProvider:
    s = get_settings()
    cls = _PROVIDERS.get(s.map_provider, AmapProvider)
    return cls(key=s.amap_web_key, secret=s.amap_web_secret)


__all__ = ["get_map_provider", "MapProvider", "GeocodeResult"]
