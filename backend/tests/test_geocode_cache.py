import os
import sys
import tempfile
from pathlib import Path

from sqlalchemy import text

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkstemp()[1]}"
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.services import geocode_amap as geocode_service  # noqa: E402

Base.metadata.create_all(bind=engine)


def test_geocode_cache_hit_prevents_duplicate_api_call(monkeypatch):
    calls = {"count": 0}

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "status": "1",
                "geocodes": [{"location": "106.6302,26.6470"}],
            }

    def fake_get(*args, **kwargs):
        calls["count"] += 1
        return _FakeResponse()

    monkeypatch.setattr(geocode_service, "AMAP_WEB_KEY", "mock-key")
    monkeypatch.setattr(geocode_service.httpx, "get", fake_get)

    db = SessionLocal()
    try:
        first = geocode_service.geocode_address(db, "贵阳观山湖区会展城A区")
        second = geocode_service.geocode_address(db, "贵阳观山湖区会展城A区")
        assert first["status"] == "success"
        assert first["message"] == "api_call"
        assert second["status"] == "success"
        assert second["message"] == "from_cache"
        assert calls["count"] == 1

        cache_count = db.execute(
            text("SELECT COUNT(1) FROM geocode_cache WHERE full_address = :address"),
            {"address": "贵阳观山湖区会展城A区"},
        ).scalar()
        assert int(cache_count or 0) == 1
    finally:
        db.close()
