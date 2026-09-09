"""FastAPI 入口。"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .config import get_settings
from .database import Base, engine
from .routers import (
    adjustments, admin, approvals, assessment, auth, brands, candidates, communications,
    dashboard, dicts, export, geocode, imports, leasing, map as map_router, matches,
    operations, projects, quality, tasks, units,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # 开发期便利：确保表存在。生产用迁移工具（见 db/migrations）。
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="品牌与项目资源管理系统 API", version=__version__, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, allow_origins=settings.cors_origin_list,
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)


@app.get("/api/v1/health", tags=["系统"])
def health():
    return {"status": "ok", "version": __version__, "coordinate_system": settings.db_coordinate_system}


for _r in (auth, brands, projects, geocode, map_router, matches, candidates,
           communications, tasks, imports, dicts, approvals, quality,
           dashboard, admin, export,
           units, leasing, operations, assessment, adjustments):
    app.include_router(_r.router)
