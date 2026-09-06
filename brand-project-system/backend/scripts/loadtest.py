"""轻量并发压测：对关键只读端点打并发请求，报 RPS 与 p50/p95/p99 延迟。

用法：先启动服务，再 `python scripts/loadtest.py [BASE] [N] [CONC]`。
默认 http://127.0.0.1:8026, 每端点 500 请求, 并发 20。仅依赖 httpx（已在 requirements）。
"""
from __future__ import annotations

import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8026"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 500
CONC = int(sys.argv[3]) if len(sys.argv) > 3 else 20

ENDPOINTS = [
    ("登录 login(POST)", "POST", "/api/v1/auth/login"),
    ("地图视口 viewport", "GET", "/api/v1/map/projects?bbox=106.3,29.4,106.9,29.9"),
    ("项目列表 list", "GET", "/api/v1/projects"),
    ("品牌列表 list", "GET", "/api/v1/brands"),
    ("项目推荐品牌 match", "GET", "/api/v1/matches/by-project/1"),
    ("工作台 dashboard", "GET", "/api/v1/dashboard/summary"),
    ("地图聚合 aggregate", "GET", "/api/v1/map/aggregate?level=city"),
]


def _pct(xs: list[float], p: float) -> float:
    xs = sorted(xs)
    k = max(0, min(len(xs) - 1, int(round(p / 100 * (len(xs) - 1)))))
    return xs[k]


def main() -> None:
    client = httpx.Client(timeout=30.0)
    tok = client.post(f"{BASE}/api/v1/auth/login",
                      data={"username": "admin", "password": "admin123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {tok}"}

    def hit(method: str, path: str) -> tuple[float, int]:
        t = time.perf_counter()
        try:
            if method == "POST":
                r = client.post(f"{BASE}{path}",
                                data={"username": "admin", "password": "admin123"})
            else:
                r = client.get(f"{BASE}{path}", headers=headers)
            return time.perf_counter() - t, r.status_code
        except httpx.HTTPError:
            return time.perf_counter() - t, 599   # 超时/连接错误计为失败，不中断压测

    print(f"BASE={BASE}  N={N}/端点  并发={CONC}\n")
    print(f"{'端点':<22}{'RPS':>8}{'p50(ms)':>10}{'p95(ms)':>10}{'p99(ms)':>10}{'错误':>6}")
    print("-" * 66)
    for name, method, path in ENDPOINTS:
        hit(method, path)  # 预热
        t0 = time.perf_counter()
        with ThreadPoolExecutor(CONC) as ex:
            res = list(ex.map(lambda _: hit(method, path), range(N)))
        wall = time.perf_counter() - t0
        lat = [r[0] * 1000 for r in res]
        errs = sum(1 for r in res if r[1] >= 400)
        rps = N / wall
        print(f"{name:<22}{rps:>8.0f}{_pct(lat,50):>10.1f}{_pct(lat,95):>10.1f}"
              f"{_pct(lat,99):>10.1f}{errs:>6}")
    client.close()


if __name__ == "__main__":
    main()
