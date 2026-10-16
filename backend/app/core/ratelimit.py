import threading
import time
from collections import defaultdict, deque

from app.core.config import get_settings
from app.core.exceptions import AppError


class RateLimiter:
    """In-memory sliding window per user. Fine for one process; use Redis if you scale out."""

    def __init__(self):
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        limit, now = get_settings().rate_limit_per_minute, time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > 60:
                q.popleft()
            if len(q) >= limit:
                raise AppError(429, "rate_limited", "Too many requests. Please slow down.")
            q.append(now)


limiter = RateLimiter()
