from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS, EXPORT_DIR, UPLOAD_DIR
from .database import Base, engine
from .schema_patch import apply_sqlite_schema_patch
from .routers import (
    auth,
    projects,
    deliverables,
    issues,
    export,
    audit,
    rules,
    shares,
    public,
    intakes,
    base_projects,
    screening,
    calc,
    overview_map,
    survey_history,
    market,
    data_quality,
    metric_dictionary,
    intel,
)

app = FastAPI(title="Project Lifecycle Manager")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in CORS_ORIGINS if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"] ,
)


@app.on_event("startup")
def startup():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    apply_sqlite_schema_patch()


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(deliverables.router)
app.include_router(issues.router)
app.include_router(export.router)
app.include_router(audit.router)
app.include_router(rules.router)
app.include_router(shares.router)
app.include_router(public.router)
app.include_router(intakes.router)
app.include_router(base_projects.router)
app.include_router(screening.router)
app.include_router(calc.router)
app.include_router(overview_map.router)
app.include_router(survey_history.router)
app.include_router(market.router)
app.include_router(data_quality.router)
app.include_router(metric_dictionary.router)
app.include_router(intel.router)
