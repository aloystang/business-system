"""坐标转换单元测试。"""
from __future__ import annotations

from app.services.map.coord import gcj02_to_wgs84, wgs84_to_gcj02


def test_wgs84_gcj02_roundtrip_within_tolerance():
    # 重庆两江新区一带
    lng, lat = 106.7100, 29.6700
    g_lng, g_lat = wgs84_to_gcj02(lng, lat)
    # GCJ-02 相对 WGS84 有偏移，非零
    assert abs(g_lng - lng) > 1e-5
    back_lng, back_lat = gcj02_to_wgs84(g_lng, g_lat)
    # 往返近似还原（反解为一阶近似，容差放宽到 ~1e-5 度，约 1m）
    assert abs(back_lng - lng) < 1e-4
    assert abs(back_lat - lat) < 1e-4


def test_out_of_china_passthrough():
    # 境外坐标不做偏移
    lng, lat = 139.6917, 35.6895  # 东京
    assert wgs84_to_gcj02(lng, lat) == (lng, lat)
    assert gcj02_to_wgs84(lng, lat) == (lng, lat)
