from __future__ import annotations

from datetime import datetime
import os
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import AMAP_WEB_KEY

AMAP_URL = "https://restapi.amap.com/v3/geocode/geo"
MAX_GEOCODE_PER_SUBMISSION = 100
DEFAULT_AMAP_WEB_KEY = AMAP_WEB_KEY


def geocode_address(db: Session, full_address: str) -> dict[str, Any]:
    address = (full_address or "").strip()
    if not address:
        return {
            "longitude": None,
            "latitude": None,
            "status": "skipped",
            "message": "empty address",
        }

    cached = db.execute(
        text(
            "SELECT longitude, latitude FROM geocode_cache WHERE full_address = :full_address"
        ),
        {"full_address": address},
    ).fetchone()
    if cached:
        return {
            "longitude": float(cached[0]) if cached[0] is not None else None,
            "latitude": float(cached[1]) if cached[1] is not None else None,
            "status": "success",
            "message": "from_cache",
        }

    env_key = os.getenv("AMAP_WEB_KEY")
    if env_key is None:
        api_key = (AMAP_WEB_KEY or "").strip()
    else:
        cleaned_env = env_key.strip()
        if cleaned_env:
            api_key = cleaned_env
        else:
            # Explicit empty env should disable key, unless runtime intentionally
            # overrides module key (e.g. monkeypatch in tests).
            module_key = (AMAP_WEB_KEY or "").strip()
            if module_key and module_key != (DEFAULT_AMAP_WEB_KEY or "").strip():
                api_key = module_key
            else:
                api_key = ""
    if not api_key:
        return {
            "longitude": None,
            "latitude": None,
            "status": "needs_key",
            "message": "AMAP key not configured",
        }

    try:
        response = httpx.get(
            AMAP_URL,
            params={"address": address, "key": api_key},
            timeout=5.0,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        return {
            "longitude": None,
            "latitude": None,
            "status": "failed",
            "message": str(exc),
        }

    if str(data.get("status")) != "1" or not data.get("geocodes"):
        return {
            "longitude": None,
            "latitude": None,
            "status": "failed",
            "message": str(data),
        }

    location = data["geocodes"][0].get("location") or ""
    if "," not in location:
        return {
            "longitude": None,
            "latitude": None,
            "status": "failed",
            "message": "invalid location",
        }

    lng_text, lat_text = location.split(",", 1)
    try:
        lng = float(lng_text)
        lat = float(lat_text)
    except ValueError:
        return {
            "longitude": None,
            "latitude": None,
            "status": "failed",
            "message": "invalid location numbers",
        }

    db.execute(
        text(
            """
            INSERT OR IGNORE INTO geocode_cache (full_address, longitude, latitude, created_at)
            VALUES (:full_address, :longitude, :latitude, :created_at)
            """
        ),
        {
            "full_address": address,
            "longitude": lng,
            "latitude": lat,
            "created_at": datetime.utcnow().isoformat(timespec="seconds"),
        },
    )
    db.flush()

    return {
        "longitude": lng,
        "latitude": lat,
        "status": "success",
        "message": "api_call",
    }
