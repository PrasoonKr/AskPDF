"""
Lightweight in-memory rate limiter for FastAPI.
No external dependencies (no Redis, no slowapi).
Uses a sliding-window counter per IP address.
"""
import time
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Per-IP sliding-window rate limiter.
    
    Limits:
    - /api/chat endpoints: CHAT_LIMIT requests per window (expensive LLM calls)
    - /api/documents (POST): UPLOAD_LIMIT per window (expensive embedding calls)
    - All other /api routes: GENERAL_LIMIT per window
    """

    def __init__(
        self,
        app,
        chat_limit: int = 20,
        upload_limit: int = 10,
        general_limit: int = 60,
        window_seconds: int = 60,
    ):
        super().__init__(app)
        self.chat_limit = chat_limit
        self.upload_limit = upload_limit
        self.general_limit = general_limit
        self.window = window_seconds
        # { ip: [(timestamp, ...), ...] }
        self._chat_hits: dict[str, list[float]] = defaultdict(list)
        self._upload_hits: dict[str, list[float]] = defaultdict(list)
        self._general_hits: dict[str, list[float]] = defaultdict(list)

    def _is_rate_limited(self, hits: list[float], limit: int, now: float) -> bool:
        """Prune old entries and check if limit is exceeded."""
        cutoff = now - self.window
        # Remove timestamps outside the window
        while hits and hits[0] < cutoff:
            hits.pop(0)
        if len(hits) >= limit:
            return True
        hits.append(now)
        return False

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        # Only rate-limit API endpoints
        if not path.startswith("/api"):
            return await call_next(request)

        # Skip health checks
        if path.startswith("/api/health"):
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Chat endpoints (most expensive — LLM + retrieval)
        if path.startswith("/api/chat"):
            if self._is_rate_limited(self._chat_hits[ip], self.chat_limit, now):
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Max {self.chat_limit} chat requests per minute.",
                )

        # Upload endpoints (expensive — embedding + S3)
        elif path.startswith("/api/documents") and method == "POST":
            if self._is_rate_limited(self._upload_hits[ip], self.upload_limit, now):
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Max {self.upload_limit} uploads per minute.",
                )

        # All other API routes
        else:
            if self._is_rate_limited(self._general_hits[ip], self.general_limit, now):
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Max {self.general_limit} requests per minute.",
                )

        response = await call_next(request)
        return response
