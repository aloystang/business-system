"""进程内失败计数限流器（防登录暴力破解）。

说明：内存实现，多 worker 不共享——作为基础防护足够；若要跨进程/分布式，
生产可换 Redis 后端。只统计“失败”尝试，登录成功即清零，正常用户不受影响。
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque


class FailureLimiter:
    def __init__(self) -> None:
        self._fails: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def is_blocked(self, key: str, limit: int, window: int) -> bool:
        now = time.monotonic()
        with self._lock:
            dq = self._fails[key]
            while dq and now - dq[0] > window:
                dq.popleft()
            return len(dq) >= limit

    def record_failure(self, key: str, window: int) -> None:
        now = time.monotonic()
        with self._lock:
            dq = self._fails[key]
            while dq and now - dq[0] > window:
                dq.popleft()
            dq.append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._fails.pop(key, None)


login_limiter = FailureLimiter()
