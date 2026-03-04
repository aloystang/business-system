from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import html
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

import httpx
import yaml
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = Path(os.getenv("FOLO_BRIDGE_DB", str(DATA_DIR / "folo_bridge.db")))
SUBSCRIPTIONS_FILE = Path(
    os.getenv("FOLO_BRIDGE_SUBSCRIPTIONS", str(BASE_DIR / "subscriptions.yaml"))
)
API_TOKEN = os.getenv("FOLO_BRIDGE_TOKEN", "folo-bridge-token")
REFRESH_INTERVAL_MINUTES = int(os.getenv("FOLO_BRIDGE_REFRESH_MINUTES", "120"))
REQUEST_TIMEOUT_SECONDS = float(os.getenv("FOLO_BRIDGE_TIMEOUT", "15"))
DEFAULT_CITY = os.getenv("FOLO_BRIDGE_DEFAULT_CITY", "重庆市")

app = FastAPI(title="Folo Bridge", version="0.1.0")


@dataclass
class Subscription:
    id: str
    name: str
    url: str
    city: str
    district: str
    enabled: bool
    tags: list[str]


def pick_source_category(tags: list[str]) -> Optional[str]:
    for tag in tags:
        if re.match(r"^[A-E]\s", tag):
            return tag
    return tags[0] if tags else None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return utc_now().replace(microsecond=0).isoformat()


def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = db_connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bridge_item (
                id TEXT PRIMARY KEY,
                source_name TEXT NOT NULL,
                source_url TEXT NOT NULL,
                title TEXT NOT NULL,
                published_at TEXT NOT NULL,
                summary TEXT,
                raw_url TEXT NOT NULL,
                city TEXT,
                district TEXT,
                dedupe_key TEXT NOT NULL UNIQUE,
                payload_json TEXT,
                fetched_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bridge_fetch_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                item_count INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL,
                message TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def ensure_subscriptions_file() -> None:
    if SUBSCRIPTIONS_FILE.exists():
        return
    example_file = BASE_DIR / "subscriptions.example.yaml"
    if example_file.exists():
        SUBSCRIPTIONS_FILE.write_text(example_file.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        SUBSCRIPTIONS_FILE.write_text("subscriptions: []\n", encoding="utf-8")


def require_auth(authorization: Optional[str], x_api_token: Optional[str]) -> None:
    if not API_TOKEN:
        return
    bearer = ""
    if authorization and authorization.lower().startswith("bearer "):
        bearer = authorization.split(" ", 1)[1].strip()
    token = bearer or (x_api_token or "").strip()
    if token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


def stable_id(*parts: str) -> str:
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()
    return digest


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def clean_summary_text(value: Any, *, max_length: int = 240) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    text = re.sub(r"(?is)<(script|style).*?>.*?</\\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_length:
        text = text[: max_length - 1].rstrip() + "…"
    return text


def parse_datetime(value: Optional[str]) -> str:
    text = normalize_text(value)
    if not text:
        return now_iso()
    candidates = (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    )
    for fmt in candidates:
        try:
            parsed = datetime.strptime(text, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat()
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat()
    except ValueError:
        return now_iso()


def parse_feed(xml_text: str, subscription: Subscription) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    items: list[dict[str, Any]] = []

    if channel is not None:
        nodes = channel.findall("item")
        for node in nodes:
            title = normalize_text(node.findtext("title"))
            link = normalize_text(node.findtext("link")) or subscription.url
            summary = clean_summary_text(node.findtext("description"))
            published = parse_datetime(node.findtext("pubDate") or node.findtext("published"))
            if not title:
                continue
            items.append(
                {
                    "type": "news",
                    "title": title,
                    "source_name": subscription.name,
                    "published_at": published,
                    "summary": summary,
                    "raw_url": link,
                    "city": subscription.city or DEFAULT_CITY,
                    "district": subscription.district or None,
                    "source_category": pick_source_category(subscription.tags),
                    "source_tags": subscription.tags,
                }
            )
        return items

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    nodes = root.findall("atom:entry", ns) or root.findall("entry")
    for node in nodes:
        title = normalize_text(node.findtext("atom:title", default="", namespaces=ns) or node.findtext("title"))
        summary = clean_summary_text(
            node.findtext("atom:summary", default="", namespaces=ns)
            or node.findtext("summary")
            or node.findtext("atom:content", default="", namespaces=ns)
            or node.findtext("content")
        )
        published_raw = (
            node.findtext("atom:published", default="", namespaces=ns)
            or node.findtext("published")
            or node.findtext("atom:updated", default="", namespaces=ns)
            or node.findtext("updated")
        )
        link = ""
        link_node = node.find("atom:link", ns) or node.find("link")
        if link_node is not None:
            link = normalize_text(link_node.attrib.get("href") or link_node.text)
        link = link or subscription.url
        if not title:
            continue
        items.append(
            {
                "type": "news",
                "title": title,
                "source_name": subscription.name,
                "published_at": parse_datetime(published_raw),
                "summary": summary,
                "raw_url": link,
                "city": subscription.city or DEFAULT_CITY,
                "district": subscription.district or None,
                "source_category": pick_source_category(subscription.tags),
                "source_tags": subscription.tags,
            }
        )
    return items


def load_subscriptions() -> list[Subscription]:
    ensure_subscriptions_file()
    payload = yaml.safe_load(SUBSCRIPTIONS_FILE.read_text(encoding="utf-8")) or {}
    rows = payload.get("subscriptions", [])
    subscriptions: list[Subscription] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        name = normalize_text(row.get("name")) or f"Subscription {index}"
        url = normalize_text(row.get("url"))
        if not url:
            continue
        sub_id = normalize_text(row.get("id")) or stable_id(name, url)[:16]
        tags_raw = row.get("tags") or []
        tags = [normalize_text(tag) for tag in tags_raw if normalize_text(tag)]
        subscriptions.append(
            Subscription(
                id=sub_id,
                name=name,
                url=url,
                city=normalize_text(row.get("city")) or DEFAULT_CITY,
                district=normalize_text(row.get("district")),
                enabled=bool(row.get("enabled", True)),
                tags=tags,
            )
        )
    return subscriptions


def should_refresh(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT fetched_at FROM bridge_fetch_log ORDER BY fetched_at DESC LIMIT 1"
    ).fetchone()
    if not row:
        return True
    try:
        fetched_at = datetime.fromisoformat(row["fetched_at"])
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=timezone.utc)
    except ValueError:
        return True
    return utc_now() - fetched_at.astimezone(timezone.utc) > timedelta(minutes=REFRESH_INTERVAL_MINUTES)


def store_items(
    conn: sqlite3.Connection,
    subscription: Subscription,
    items: list[dict[str, Any]],
) -> int:
    inserted = 0
    fetched_at = now_iso()
    for item in items:
        dedupe_key = stable_id(
            item["title"].lower(),
            normalize_text(item["source_name"]).lower(),
            normalize_text(item["published_at"]),
        )
        item_id = stable_id(subscription.id, dedupe_key)
        payload_json = json.dumps(item, ensure_ascii=False)
        conn.execute(
            """
            INSERT INTO bridge_item (
                id, source_name, source_url, title, published_at, summary, raw_url,
                city, district, dedupe_key, payload_json, fetched_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(dedupe_key) DO UPDATE SET
                source_name=excluded.source_name,
                source_url=excluded.source_url,
                title=excluded.title,
                published_at=excluded.published_at,
                summary=excluded.summary,
                raw_url=excluded.raw_url,
                city=excluded.city,
                district=excluded.district,
                payload_json=excluded.payload_json,
                fetched_at=excluded.fetched_at
            """,
            (
                item_id,
                item["source_name"],
                subscription.url,
                item["title"],
                item["published_at"],
                item.get("summary"),
                item["raw_url"],
                item.get("city"),
                item.get("district"),
                dedupe_key,
                payload_json,
                fetched_at,
            ),
        )
        inserted += 1
    return inserted


def log_fetch(conn: sqlite3.Connection, source_name: str, status: str, item_count: int, message: str = "") -> None:
    conn.execute(
        """
        INSERT INTO bridge_fetch_log (source_name, fetched_at, item_count, status, message)
        VALUES (?, ?, ?, ?, ?)
        """,
        (source_name, now_iso(), item_count, status, message[:500]),
    )


def refresh_cache(force: bool = False) -> dict[str, Any]:
    conn = db_connect()
    subscriptions = load_subscriptions()
    stats = {"subscriptions": len(subscriptions), "fetched": 0, "errors": 0}
    try:
        if not force and not should_refresh(conn):
            total = conn.execute("SELECT COUNT(*) AS count FROM bridge_item").fetchone()["count"]
            stats["cached"] = total
            return stats

        for subscription in subscriptions:
            if not subscription.enabled:
                continue
            try:
                response = httpx.get(subscription.url, timeout=REQUEST_TIMEOUT_SECONDS)
                response.raise_for_status()
                items = parse_feed(response.text, subscription)
                fetched_count = store_items(conn, subscription, items)
                log_fetch(conn, subscription.name, "success", fetched_count)
                stats["fetched"] += fetched_count
            except Exception as exc:
                log_fetch(conn, subscription.name, "failed", 0, str(exc))
                stats["errors"] += 1
        conn.commit()
        return stats
    finally:
        conn.close()


def query_items(
    *,
    item_type: str,
    page: int,
    page_size: int,
    from_time: Optional[str],
    to_time: Optional[str],
) -> tuple[list[dict[str, Any]], int]:
    if item_type not in {"all", "news"}:
        return [], 0
    conn = db_connect()
    try:
        conditions = []
        params: list[Any] = []
        if from_time:
            conditions.append("published_at >= ?")
            params.append(parse_datetime(from_time))
        if to_time:
            conditions.append("published_at <= ?")
            params.append(parse_datetime(to_time))

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        total = conn.execute(f"SELECT COUNT(*) AS count FROM bridge_item {where_clause}", params).fetchone()[
            "count"
        ]
        offset = (page - 1) * page_size
        rows = conn.execute(
            f"""
            SELECT *
            FROM bridge_item
            {where_clause}
            ORDER BY published_at DESC, fetched_at DESC
            LIMIT ? OFFSET ?
            """,
            [*params, page_size, offset],
        ).fetchall()
        items = [
            {
                "type": "news",
                "title": row["title"],
                "source_name": row["source_name"],
                "published_at": row["published_at"],
                "summary": row["summary"],
                "raw_url": row["raw_url"],
                "city": row["city"],
                "district": row["district"],
                **(
                    json.loads(row["payload_json"])
                    if row["payload_json"]
                    else {}
                ),
            }
            for row in rows
        ]
        return items, int(total)
    finally:
        conn.close()


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    ensure_subscriptions_file()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/subscriptions")
def list_subscriptions(
    authorization: Optional[str] = Header(default=None),
    x_api_token: Optional[str] = Header(default=None, alias="X-API-Token"),
) -> dict[str, Any]:
    require_auth(authorization, x_api_token)
    return {
        "items": [
            {
                "id": sub.id,
                "name": sub.name,
                "url": sub.url,
                "city": sub.city,
                "district": sub.district,
                "enabled": sub.enabled,
                "tags": sub.tags,
            }
            for sub in load_subscriptions()
        ]
    }


@app.post("/api/refresh")
def refresh(
    authorization: Optional[str] = Header(default=None),
    x_api_token: Optional[str] = Header(default=None, alias="X-API-Token"),
) -> dict[str, Any]:
    require_auth(authorization, x_api_token)
    stats = refresh_cache(force=True)
    return {"ok": True, **stats}


@app.get("/api/intel/items")
def intel_items(
    type: str = Query(default="news"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),
    from_time: Optional[str] = Query(default=None),
    to_time: Optional[str] = Query(default=None),
    authorization: Optional[str] = Header(default=None),
    x_api_token: Optional[str] = Header(default=None, alias="X-API-Token"),
):
    require_auth(authorization, x_api_token)
    refresh_cache(force=False)
    items, total = query_items(
        item_type=type,
        page=page,
        page_size=page_size,
        from_time=from_time,
        to_time=to_time,
    )
    return JSONResponse(
        {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=9090)
