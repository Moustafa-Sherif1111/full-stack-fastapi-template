"""Simple in-process sliding-window rate limiter middleware.

Introduced in v1.1.0 to protect public endpoints (login, register) against
brute-force and credential-stuffing attacks.

Limits are applied per client IP address.  For production behind a reverse
proxy, ensure FORWARDED / X-Forwarded-For headers are trusted
(use ``uvicorn --forwarded-allow-ips`` or configure a TrustedHostMiddleware).

Configuration (env vars):
  RATE_LIMIT_REQUESTS  – max requests per window (default: 60)
  RATE_LIMIT_WINDOW    – window size in seconds (default: 60)
  RATE_LIMIT_ENABLED   – set to "false" to disable entirely (default: true)
"""
import time
from collections import defaultdict, deque
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from app.core.config import settings


class SlidingWindowRateLimiter(BaseHTTPMiddleware):
    """Token-bucket sliding-window rate limiter.

    Thread-safety note: ``deque`` operations used here (append / popleft) are
    GIL-protected in CPython, so this implementation is safe for a single
    uvicorn worker.  For multi-worker deployments, replace the in-memory store
    with a Redis backend.
    """

    def __init__(self, app: Callable, max_requests: int = 60, window_seconds: int = 60) -> None:
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # ip -> deque of request timestamps
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    def _get_client_ip(self, request: Request) -> str:
        # Respect X-Forwarded-For if present (set by trusted proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not getattr(settings, "rate_limit_enabled", True):
            return await call_next(request)

        # Only rate-limit auth-adjacent paths to keep overhead minimal
        path = request.url.path
        if not any(path.startswith(p) for p in ["/api/v1/login", "/api/v1/users/signup"]):
            return await call_next(request)

        ip = self._get_client_ip(request)
        now = time.monotonic()
        bucket = self._buckets[ip]

        # Evict timestamps outside the current window
        while bucket and bucket[0] < now - self.window_seconds:
            bucket.popleft()

        if len(bucket) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - bucket[0])) + 1
            return Response(
                content='{"detail":"Too many requests. Please slow down."}',
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "Content-Type": "application/json",
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + retry_after)),
                },
            )

        bucket.append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(self.max_requests - len(bucket))
        return response
