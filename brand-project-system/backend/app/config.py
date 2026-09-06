"""配置。默认 SQLite 本地开发；生产改 DATABASE_URL 切 Postgres/PostGIS。"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./data/bpr.db"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720
    admin_username: str = "admin"
    admin_password: str = "admin123"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    # 登录限流：同一 IP+用户名 在窗口内失败次数上限（防暴力破解；成功即清零）
    login_max_failures: int = 8
    login_window_seconds: int = 300

    # 地图（高德）——本机演示可留空，前端地图 key 走 VITE_ 变量
    map_provider: str = "amap"
    db_coordinate_system: str = "GCJ-02"
    sensitive_blur_radius_m: int = 500
    # 后端 Web 服务 Key（地理编码等）。留空时 geocode 优雅降级为“定位失败”。
    amap_web_key: str = ""
    amap_web_secret: str = ""
    amap_geocode_qps: int = 3

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
