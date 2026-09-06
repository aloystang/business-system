"""高德 Web 服务实现。Key 缺失或请求失败时优雅降级为“定位失败”。"""
from __future__ import annotations

import hashlib

import httpx

from .base import GEO_AUTO, GEO_FAILED, GeocodeResult

_GEO_URL = "https://restapi.amap.com/v3/geocode/geo"
_REGEO_URL = "https://restapi.amap.com/v3/geocode/regeo"
_TIMEOUT = 6.0

# 高德 level → 精度档
_HIGH = {"门牌号", "兴趣点", "单元号", "道路"}
_MID = {"街道", "村庄", "乡镇", "热点商圈", "公交站点"}


def _accuracy(level: str | None) -> str | None:
    if not level:
        return None
    if level in _HIGH:
        return "高"
    if level in _MID:
        return "中"
    return "低"


class AmapProvider:
    name = "amap"

    def __init__(self, key: str, secret: str = "") -> None:
        self._key = key
        self._secret = secret

    def _sign(self, params: dict[str, str]) -> dict[str, str]:
        """高德数字签名：md5(按键排序拼接 + 私钥)。无 secret 则不签名。"""
        if not self._secret:
            return params
        raw = "&".join(f"{k}={params[k]}" for k in sorted(params)) + self._secret
        return {**params, "sig": hashlib.md5(raw.encode("utf-8")).hexdigest()}

    def geocode(self, address: str, city: str | None = None) -> GeocodeResult:
        if not self._key or not address:
            return GeocodeResult(status=GEO_FAILED)
        params = {"key": self._key, "address": address, "output": "JSON"}
        if city:
            params["city"] = city
        try:
            resp = httpx.get(_GEO_URL, params=self._sign(params), timeout=_TIMEOUT)
            data = resp.json()
        except (httpx.HTTPError, ValueError):
            return GeocodeResult(status=GEO_FAILED)
        return self._parse_geo(data)

    def _parse_geo(self, data: dict) -> GeocodeResult:
        if str(data.get("status")) != "1" or not data.get("geocodes"):
            return GeocodeResult(status=GEO_FAILED)
        codes = data["geocodes"]
        first = codes[0]
        loc = (first.get("location") or "").split(",")
        if len(loc) != 2:
            return GeocodeResult(status=GEO_FAILED)
        try:
            lng, lat = float(loc[0]), float(loc[1])
        except ValueError:
            return GeocodeResult(status=GEO_FAILED)
        level = first.get("level")
        return GeocodeResult(
            longitude=lng, latitude=lat, coordinate_system="GCJ-02", provider=self.name,
            level=level, accuracy=_accuracy(level), status=GEO_AUTO,
            formatted_address=first.get("formatted_address"),
            candidates=[{"formatted_address": c.get("formatted_address"),
                         "location": c.get("location"), "level": c.get("level")}
                        for c in codes[:5]],
        )

    def reverse_geocode(self, lng: float, lat: float) -> GeocodeResult:
        if not self._key:
            return GeocodeResult(status=GEO_FAILED)
        params = {"key": self._key, "location": f"{lng},{lat}", "output": "JSON"}
        try:
            resp = httpx.get(_REGEO_URL, params=self._sign(params), timeout=_TIMEOUT)
            data = resp.json()
        except (httpx.HTTPError, ValueError):
            return GeocodeResult(status=GEO_FAILED)
        if str(data.get("status")) != "1" or not data.get("regeocode"):
            return GeocodeResult(status=GEO_FAILED)
        addr = data["regeocode"].get("formatted_address")
        return GeocodeResult(longitude=lng, latitude=lat, provider=self.name,
                             status=GEO_AUTO, formatted_address=addr)
