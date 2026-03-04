import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

import app as bridge_app  # noqa: E402
from app import Subscription, parse_feed  # noqa: E402


def test_parse_rss_feed():
    xml_text = Path(__file__).with_name("sample_feed.xml").read_text(encoding="utf-8")
    subscription = Subscription(
        id="sub-1",
        name="测试源",
        url="https://example.com/rss.xml",
        city="重庆市",
        district="两江新区",
        enabled=True,
        tags=["商业运营"],
    )

    items = parse_feed(xml_text, subscription)

    assert len(items) == 2
    assert items[0]["title"] == "重庆商业运营动态"
    assert items[0]["source_name"] == "测试源"
    assert items[0]["city"] == "重庆市"
    assert items[0]["district"] == "两江新区"
    assert items[0]["raw_url"] == "https://example.com/news/1"


def test_intel_items_endpoint(monkeypatch):
    xml_text = Path(__file__).with_name("sample_feed.xml").read_text(encoding="utf-8")
    subscription = Subscription(
        id="sub-2",
        name="接口测试源",
        url="https://example.com/rss.xml",
        city="重庆市",
        district="渝北区",
        enabled=True,
        tags=["物业服务"],
    )

    class DummyResponse:
        status_code = 200
        text = xml_text

        def raise_for_status(self):
            return None

    monkeypatch.setattr(bridge_app, "load_subscriptions", lambda: [subscription])
    monkeypatch.setattr(bridge_app.httpx, "get", lambda *args, **kwargs: DummyResponse())
    monkeypatch.setattr(bridge_app, "REFRESH_INTERVAL_MINUTES", 0)
    bridge_app.init_db()

    client = TestClient(bridge_app.app)
    response = client.get(
        "/api/intel/items?page=1&page_size=5",
        headers={"Authorization": "Bearer folo-bridge-token"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 2
    assert body["items"][0]["type"] == "news"
