"""批量给"待定位/定位失败"的项目补坐标（高德 Web 服务）。

前置：.env 配好 AMAP_WEB_KEY（必须是「Web服务」平台的 Key）。
遵守高德并发上限（默认 QPS 3），逐条解析，成功落 GCJ-02 坐标，失败保持"定位失败"（不落错坐标）。
    python scripts/geocode_pending.py
"""
from __future__ import annotations

import time

from app.config import get_settings
from app.database import SessionLocal
from app.models import ProjectLocation
from app.services.geocoding import apply_geocode, geocode_address


def run() -> None:
    s = get_settings()
    if not s.amap_web_key:
        print("✗ 未配置 AMAP_WEB_KEY（须为「Web服务」平台 Key）。先在 .env 配置再运行。")
        return
    interval = 1.0 / max(s.amap_geocode_qps, 1)   # 限流
    db = SessionLocal()
    ok = fail = 0
    try:
        pending = db.query(ProjectLocation).filter(
            ProjectLocation.geocoding_status.in_(["待定位", "定位失败"])).all()
        print(f"待补坐标：{len(pending)} 个，QPS≤{s.amap_geocode_qps}")
        for loc in pending:
            result = geocode_address(loc.address, loc.city)
            apply_geocode(loc, result)
            if result.ok:
                ok += 1
            else:
                fail += 1
            db.commit()
            time.sleep(interval)
        print(f"✅ 完成：成功 {ok}，失败 {fail}（失败项进数据质量中心错误清单，可人工补点）。")
    finally:
        db.close()


if __name__ == "__main__":
    run()
