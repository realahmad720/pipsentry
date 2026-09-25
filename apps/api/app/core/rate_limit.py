"""Rate limiting on public API endpoints (Section 11). A per-process,
in-memory sliding window — correct for the single-instance MVP deployment
this scaffold targets (Section 12); once the API runs on more than one
instance, this needs a shared store (Redis) instead of an in-process dict,
same caveat as the FastAPI BackgroundTask ingestion queue.
"""

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

DEFAULT_LIMIT = 60
DEFAULT_WINDOW_SECONDS = 60.0


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, limit: int = DEFAULT_LIMIT, window_seconds: float = DEFAULT_WINDOW_SECONDS) -> None:
        super().__init__(app)
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _client_key(self, request: Request) -> str:
        # Authenticated requests are rate-limited per bearer token (proxy for
        # user identity — decoding the JWT here would duplicate security.py's
        # work on every request), everything else falls back to client IP.
        auth = request.headers.get("authorization")
        if auth:
            return auth
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next) -> Response:
        key = self._client_key(request)
        now = time.monotonic()

        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self.window_seconds:
                hits.popleft()
            if len(hits) >= self.limit:
                return Response(
                    content='{"detail":"Rate limit exceeded"}',
                    status_code=429,
                    media_type="application/json",
                )
            hits.append(now)

        return await call_next(request)
