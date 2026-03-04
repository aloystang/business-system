from __future__ import annotations

import hashlib
import json
import re
import base64
import html
from datetime import datetime, timedelta
from typing import Any, Iterable, Optional
from urllib.parse import urljoin

import httpx
from sqlalchemy.orm import Session

from ..config import (
    BIDMONITOR_API_TOKEN,
    BIDMONITOR_BASE_URL,
    BIDMONITOR_PULL_PATH,
    FOLO_API_TOKEN,
    FOLO_BASE_URL,
    FOLO_PULL_PATH,
    INTEL_DEFAULT_CITY,
)
from ..models import IntelItem, IntelSyncJob, IntelWatchRule

FOLO_TITLE_KEYWORDS = [
    "商业地产",
    "商业综合体",
    "购物中心",
    "购物公园",
    "社区商业",
    "街区商业",
    "商圈",
    "招商运营",
    "品牌招商",
    "招商签约",
    "物业服务",
    "物业管理",
    "商业物业",
    "零售",
    "客流",
    "坪效",
    "租金",
    "空置率",
    "商户",
    "品牌",
    "首店",
    "开业",
    "业态",
    "城市更新",
    "存量改造",
    "文旅商业",
    "写字楼",
    "园区运营",
]

FOLO_SUMMARY_FALLBACK_KEYWORDS = [
    "商业综合体",
    "购物中心",
    "社区商业",
    "街区商业",
    "商圈",
    "招商运营",
    "品牌招商",
    "物业服务",
    "物业管理",
    "商业物业",
    "客流",
    "坪效",
    "租金",
    "空置率",
    "首店",
    "开业",
    "业态",
    "城市更新",
    "存量改造",
]


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat()


def parse_datetime_text(value: Any, *, default_now: bool = True) -> Optional[str]:
    if value is None:
        return now_iso() if default_now else None
    text = str(value).strip()
    if not text:
        return now_iso() if default_now else None
    text = text.replace("/", "-").replace("T", " ")
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S.%f",
    ):
        try:
            return datetime.strptime(text, fmt).replace(microsecond=0).isoformat()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(str(value)).replace(microsecond=0).isoformat()
    except Exception:
        return now_iso() if default_now else None


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


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


def first_value(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return None


def normalize_item_type(value: Any) -> str:
    text = normalize_text(value).lower()
    if text in {"news", "资讯", "新闻"}:
        return "news"
    if text in {"tender", "bid", "bidding", "招标", "招投标"}:
        return "tender"
    if "news" in text:
        return "news"
    return "tender"


def parse_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except Exception:
        return None


def make_dedupe_key(title: str, source_name: str, published_at: str) -> str:
    base = "|".join(
        [
            normalize_text(title).lower(),
            normalize_text(source_name).lower(),
            normalize_text(published_at),
        ]
    )
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def normalize_raw_item(raw: dict[str, Any]) -> dict[str, Any]:
    item_type = normalize_item_type(first_value(raw, "item_type", "type", "category"))
    title = normalize_text(first_value(raw, "title", "project_name", "name"))
    source_name = normalize_text(first_value(raw, "source_name", "source", "platform"))
    published_at = parse_datetime_text(
        first_value(raw, "published_at", "publish_time", "pub_time", "published"),
        default_now=True,
    )
    summary = clean_summary_text(first_value(raw, "summary", "content", "desc", "description"))
    raw_url = normalize_text(first_value(raw, "raw_url", "url", "link"))
    city = normalize_text(first_value(raw, "city", "province_city"))
    district = normalize_text(first_value(raw, "district", "county", "region"))
    issuer = normalize_text(first_value(raw, "issuer", "buyer", "purchaser"))
    deadline_at = parse_datetime_text(
        first_value(raw, "deadline_at", "deadline", "end_time"),
        default_now=False,
    )
    budget_amount = parse_float(first_value(raw, "budget_amount", "budget", "amount"))

    if not title:
        raise ValueError("missing title")
    if not source_name:
        source_name = "未知来源"

    payload_json = json.dumps(raw, ensure_ascii=False)
    dedupe_key = make_dedupe_key(title, source_name, published_at)
    if not city:
        city = (INTEL_DEFAULT_CITY or "").strip()
    return {
        "item_type": item_type,
        "title": title,
        "source_name": source_name,
        "published_at": published_at,
        "city": city or None,
        "district": district or None,
        "summary": summary or None,
        "raw_url": raw_url or None,
        "budget_amount": budget_amount,
        "deadline_at": deadline_at,
        "issuer": issuer or None,
        "payload_json": payload_json,
        "dedupe_key": dedupe_key,
    }


def parse_items_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("items", "data", "results", "rows", "entries", "articles", "list"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
    return []


def build_auth_headers(token: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    normalized = (token or "").strip()
    if not normalized:
        return headers
    lowered = normalized.lower()
    if lowered.startswith("basic "):
        headers["Authorization"] = normalized
    elif ":" in normalized:
        basic_payload = base64.b64encode(normalized.encode("utf-8")).decode("utf-8")
        headers["Authorization"] = f"Basic {basic_payload}"
    else:
        headers["Authorization"] = f"Bearer {normalized}"
        headers["X-API-Token"] = normalized
    return headers


def normalize_source_system(value: str) -> str:
    text = normalize_text(value).lower()
    if text in {"all", "both"}:
        return "all"
    if text in {"folo"}:
        return "folo"
    return "bidmonitor"


def fetch_bidmonitor_items(
    *,
    window_start: Optional[str] = None,
    window_end: Optional[str] = None,
    item_type: str = "all",
) -> list[dict[str, Any]]:
    base_url = (BIDMONITOR_BASE_URL or "").strip()
    if not base_url:
        raise RuntimeError("BIDMONITOR_BASE_URL 未配置")

    request_url = urljoin(base_url.rstrip("/") + "/", BIDMONITOR_PULL_PATH.lstrip("/"))
    headers = build_auth_headers(BIDMONITOR_API_TOKEN or "")

    params: dict[str, Any] = {"page": 1, "page_size": 500}
    if window_start:
        params["from_time"] = window_start
    if window_end:
        params["to_time"] = window_end
    if item_type in {"news", "tender"}:
        params["type"] = item_type

    response = httpx.get(request_url, params=params, headers=headers, timeout=20.0)
    response.raise_for_status()
    body = response.json()
    rows = parse_items_payload(body)
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if "published_at" not in row and "pub_date" in row:
            row["published_at"] = row.get("pub_date")
        try:
            normalized.append(normalize_raw_item(row))
        except ValueError:
            continue
    return normalized


def normalize_folo_raw_item(raw: dict[str, Any]) -> dict[str, Any]:
    candidate = dict(raw)
    candidate["item_type"] = "news"
    if "source_name" not in candidate:
        candidate["source_name"] = first_value(
            candidate,
            "source",
            "site",
            "feed_title",
            "feed_name",
            "author",
            "publisher",
        )
    if "published_at" not in candidate:
        candidate["published_at"] = first_value(
            candidate,
            "published",
            "publishedAt",
            "date_published",
            "pubDate",
            "date",
        )
    if "summary" not in candidate:
        candidate["summary"] = first_value(
            candidate,
            "summary",
            "description",
            "content_text",
            "content",
            "excerpt",
        )
    if "raw_url" not in candidate:
        candidate["raw_url"] = first_value(candidate, "url", "link", "external_url", "permalink")
    if "title" not in candidate:
        candidate["title"] = first_value(candidate, "title", "name")
    return normalize_raw_item(candidate)


def is_relevant_folo_news(item: dict[str, Any]) -> bool:
    title = (item.get("title") or "").lower()
    summary = (item.get("summary") or "").lower()
    if any(keyword.lower() in title for keyword in FOLO_TITLE_KEYWORDS):
        return True
    return any(keyword.lower() in summary for keyword in FOLO_SUMMARY_FALLBACK_KEYWORDS)


def fetch_folo_items(
    *,
    window_start: Optional[str] = None,
    window_end: Optional[str] = None,
) -> list[dict[str, Any]]:
    base_url = (FOLO_BASE_URL or "").strip()
    if not base_url:
        raise RuntimeError("FOLO_BASE_URL 未配置")

    request_url = urljoin(base_url.rstrip("/") + "/", FOLO_PULL_PATH.lstrip("/"))
    headers = build_auth_headers(FOLO_API_TOKEN or "")

    params: dict[str, Any] = {"page": 1, "page_size": 500, "type": "news"}
    if window_start:
        params["from_time"] = window_start
        params["date_from"] = window_start
    if window_end:
        params["to_time"] = window_end
        params["date_to"] = window_end

    response = httpx.get(request_url, params=params, headers=headers, timeout=20.0)
    response.raise_for_status()
    body = response.json()
    rows = parse_items_payload(body)
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if isinstance(row, dict):
            try:
                item = normalize_folo_raw_item(row)
                if is_relevant_folo_news(item):
                    normalized.append(item)
            except ValueError:
                continue
    return normalized


def split_keywords(text: str) -> list[str]:
    if not text:
        return []
    chunks = re.split(r"[,\n，；;|]+", text)
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def match_watch_rules(item: dict[str, Any], rules: Iterable[IntelWatchRule]) -> list[IntelWatchRule]:
    matched: list[IntelWatchRule] = []
    title_and_summary = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    for rule in rules:
        if rule.item_type != "all" and rule.item_type != item["item_type"]:
            continue
        if rule.city and rule.city != (item.get("city") or ""):
            continue
        if rule.district and rule.district != (item.get("district") or ""):
            continue

        budget = item.get("budget_amount")
        if rule.budget_min is not None:
            if budget is None or budget < rule.budget_min:
                continue
        if rule.budget_max is not None:
            if budget is None or budget > rule.budget_max:
                continue

        keywords = split_keywords(rule.keywords or "")
        if keywords and not any(keyword.lower() in title_and_summary for keyword in keywords):
            continue
        matched.append(rule)
    return matched


def run_sync(
    db: Session,
    *,
    created_by: Optional[int] = None,
    trigger_type: str = "manual",
    payload_items: Optional[list[dict[str, Any]]] = None,
    window_start: Optional[str] = None,
    window_end: Optional[str] = None,
    item_type: str = "all",
    source_system: str = "bidmonitor",
) -> tuple[IntelSyncJob, dict[str, Any]]:
    started_at = now_iso()
    if not window_start:
        window_start = (datetime.utcnow() - timedelta(hours=6)).replace(microsecond=0).isoformat()
    if not window_end:
        window_end = started_at

    normalized_source = normalize_source_system(source_system)
    job = IntelSyncJob(
        id=f"intel-job-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
        trigger_type=trigger_type,
        started_at=started_at,
        status="running",
        window_start=window_start,
        window_end=window_end,
        created_by=created_by,
        source_system=normalized_source,
    )
    db.add(job)
    db.flush()

    pulled = 0
    upserted = 0
    deduped = 0
    failed = 0
    matched_hits = 0
    source_errors: dict[str, str] = {}
    source_counts: dict[str, int] = {"bidmonitor": 0, "folo": 0}

    try:
        if payload_items is not None:
            normalized_items = []
            for row in payload_items:
                try:
                    normalized_items.append(normalize_raw_item(row))
                except ValueError:
                    failed += 1
        else:
            normalized_items = []
            requested_sources: list[str]
            if normalized_source == "all":
                requested_sources = ["bidmonitor", "folo"]
            else:
                requested_sources = [normalized_source]

            for source_name in requested_sources:
                try:
                    if source_name == "bidmonitor":
                        rows = fetch_bidmonitor_items(
                            window_start=window_start,
                            window_end=window_end,
                            item_type=item_type,
                        )
                    else:
                        rows = fetch_folo_items(
                            window_start=window_start,
                            window_end=window_end,
                        )
                    source_counts[source_name] = len(rows)
                    normalized_items.extend(rows)
                except Exception as source_exc:
                    source_errors[source_name] = str(source_exc)

            if not normalized_items and source_errors:
                raise RuntimeError(
                    "; ".join([f"{name}: {message}" for name, message in source_errors.items()])
                )

        pulled = len(normalized_items)
        unique_map: dict[str, dict[str, Any]] = {}
        in_batch_deduped = 0
        for row in normalized_items:
            dedupe_key = row["dedupe_key"]
            if dedupe_key in unique_map:
                in_batch_deduped += 1
            unique_map[dedupe_key] = row
        unique_rows = list(unique_map.values())
        deduped += in_batch_deduped

        rules = (
            db.query(IntelWatchRule)
            .filter(IntelWatchRule.is_enabled == 1)
            .all()
        )

        for row in unique_rows:
            try:
                existing = db.query(IntelItem).filter(IntelItem.dedupe_key == row["dedupe_key"]).first()
                matched = match_watch_rules(row, rules)
                matched_count = len(matched)
                if existing:
                    existing.item_type = row["item_type"]
                    existing.title = row["title"]
                    existing.source_name = row["source_name"]
                    existing.published_at = row["published_at"]
                    existing.city = row["city"]
                    existing.district = row["district"]
                    existing.summary = row["summary"]
                    existing.raw_url = row["raw_url"]
                    existing.budget_amount = row["budget_amount"]
                    existing.deadline_at = row["deadline_at"]
                    existing.issuer = row["issuer"]
                    existing.payload_json = row["payload_json"]
                    existing.matched_rule_count = matched_count
                    if matched_count > 0:
                        existing.follow_up_status = "pending"
                    existing.updated_at = now_iso()
                    deduped += 1
                else:
                    item_id = f"intel-item-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
                    db.add(
                        IntelItem(
                            id=item_id,
                            item_type=row["item_type"],
                            title=row["title"],
                            source_name=row["source_name"],
                            published_at=row["published_at"],
                            city=row["city"],
                            district=row["district"],
                            summary=row["summary"],
                            raw_url=row["raw_url"],
                            budget_amount=row["budget_amount"],
                            deadline_at=row["deadline_at"],
                            issuer=row["issuer"],
                            payload_json=row["payload_json"],
                            dedupe_key=row["dedupe_key"],
                            matched_rule_count=matched_count,
                            follow_up_status="pending" if matched_count > 0 else "none",
                            created_at=now_iso(),
                            updated_at=now_iso(),
                        )
                    )
                    upserted += 1
                matched_hits += matched_count
            except Exception:
                failed += 1

        job.status = "success"
        job.ended_at = now_iso()
        job.pulled_count = pulled
        job.upserted_count = upserted
        job.deduped_count = deduped
        job.failed_count = failed
        job.details_json = json.dumps(
            {
                "matched_rule_hits": matched_hits,
                "window_start": window_start,
                "window_end": window_end,
                "source_counts": source_counts,
                "source_errors": source_errors,
            },
            ensure_ascii=False,
        )
        db.flush()
        return job, {
            "pulled_count": pulled,
            "upserted_count": upserted,
            "deduped_count": deduped,
            "failed_count": failed,
            "matched_rule_hits": matched_hits,
            "source_system": normalized_source,
        }
    except Exception as exc:
        job.status = "failed"
        job.ended_at = now_iso()
        job.error_message = str(exc)
        job.pulled_count = pulled
        job.upserted_count = upserted
        job.deduped_count = deduped
        job.failed_count = failed + 1
        db.flush()
        raise
