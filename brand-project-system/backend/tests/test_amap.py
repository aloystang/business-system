"""高德解析与降级单元测试（不发起真实网络请求）。"""
from __future__ import annotations

from app.services.map.amap import AmapProvider
from app.services.map.base import GEO_AUTO, GEO_FAILED


def test_parse_geo_success():
    p = AmapProvider(key="x")
    data = {"status": "1", "geocodes": [
        {"location": "106.7315,29.6902", "level": "乡镇",
         "formatted_address": "重庆市两江新区龙兴镇"}]}
    r = p._parse_geo(data)
    assert r.status == GEO_AUTO
    assert (r.longitude, r.latitude) == (106.7315, 29.6902)
    assert r.coordinate_system == "GCJ-02"
    assert r.accuracy == "中"


def test_parse_geo_no_result_fails():
    p = AmapProvider(key="x")
    assert p._parse_geo({"status": "1", "geocodes": []}).status == GEO_FAILED
    assert p._parse_geo({"status": "0"}).status == GEO_FAILED


def test_geocode_without_key_degrades():
    p = AmapProvider(key="")
    assert p.geocode("任意地址").status == GEO_FAILED


def test_sign_added_when_secret_present():
    p = AmapProvider(key="k", secret="s")
    signed = p._sign({"key": "k", "address": "a"})
    assert "sig" in signed and len(signed["sig"]) == 32
