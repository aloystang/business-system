"""定位不变量与降级单元测试。"""
from __future__ import annotations

import pytest

from app.models import ProjectLocation
from app.services.geocoding import (
    LocationInvariantError,
    apply_geocode,
    enforce_location_invariant,
)
from app.services.map.base import GEO_AUTO, GEO_FAILED, GeocodeResult


def test_invariant_failed_status_rejects_coords():
    with pytest.raises(LocationInvariantError):
        enforce_location_invariant("定位失败", 106.7, 29.6)


def test_invariant_success_status_requires_coords():
    with pytest.raises(LocationInvariantError):
        enforce_location_invariant("人工确认", None, None)


def test_invariant_valid_cases_pass():
    enforce_location_invariant("定位失败", None, None)
    enforce_location_invariant("待定位", None, None)
    enforce_location_invariant("自动定位", 106.7, 29.6)


def test_invariant_unknown_status():
    with pytest.raises(LocationInvariantError):
        enforce_location_invariant("瞎猜", None, None)


def test_apply_geocode_success_writes_coords():
    loc = ProjectLocation(province="重庆市", city="重庆市", district="两江新区", address="x")
    apply_geocode(loc, GeocodeResult(longitude=106.7, latitude=29.6, status=GEO_AUTO))
    assert loc.geocoding_status == "自动定位"
    assert loc.longitude == 106.7


def test_apply_geocode_failure_clears_coords():
    loc = ProjectLocation(province="重庆市", city="重庆市", district="两江新区", address="x",
                          longitude=1.0, latitude=2.0)
    apply_geocode(loc, GeocodeResult(status=GEO_FAILED))
    assert loc.geocoding_status == "定位失败"
    assert loc.longitude is None and loc.latitude is None
