"""地图服务适配层抽象。业务只依赖 MapProvider，不认识具体厂商。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

# geocoding_status 取值（与 DB/字典一致）
GEO_AUTO = "自动定位"
GEO_FAILED = "定位失败"


@dataclass
class GeocodeResult:
    longitude: float | None = None
    latitude: float | None = None
    coordinate_system: str = "GCJ-02"
    provider: str = "amap"
    level: str | None = None
    accuracy: str | None = None
    status: str = GEO_FAILED
    formatted_address: str | None = None
    candidates: list[dict] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status == GEO_AUTO and self.longitude is not None


class MapProvider(Protocol):
    name: str

    def geocode(self, address: str, city: str | None = None) -> GeocodeResult: ...

    def reverse_geocode(self, lng: float, lat: float) -> GeocodeResult: ...
