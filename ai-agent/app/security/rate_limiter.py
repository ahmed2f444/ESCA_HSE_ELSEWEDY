"""
ESCA HSE AI Agent - High-Performance In-Memory Sliding-Window Rate Limiter.

Provides:
1. Thread-safe sliding-window rate limiting per IP or client identifier.
2. Distinct rate tiers for heavy computational endpoints (`/ask`, `/api/v1/automation/trigger`).
3. RFC-compliant rate limit response headers (`Retry-After`, `X-RateLimit-*`).
4. Automatic periodic garbage collection of expired client records to prevent memory leaks.
"""
import time
from collections import defaultdict
from dataclasses import dataclass, field
import threading
from typing import NamedTuple


class RateLimitResult(NamedTuple):
    allowed: bool
    limit: int
    remaining: int
    reset_seconds: int
    retry_after: int


@dataclass
class ClientWindow:
    timestamps: list[float] = field(default_factory=list)


class SlidingWindowRateLimiter:
    """
    Sliding window log rate limiter with microsecond precision and thread-safe locking.
    """
    def __init__(self, default_limit: int = 60, window_seconds: int = 60):
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self._clients: dict[str, ClientWindow] = defaultdict(ClientWindow)
        self._lock = threading.Lock()
        self._last_cleanup = time.time()

    def _cleanup_stale_entries(self, now: float) -> None:
        """Removes entries older than 2x window_seconds to bound memory usage."""
        if now - self._last_cleanup < 120:
            return
        self._last_cleanup = now
        stale_threshold = now - (self.window_seconds * 2)
        keys_to_delete = []
        for key, window in self._clients.items():
            window.timestamps = [t for t in window.timestamps if t > stale_threshold]
            if not window.timestamps:
                keys_to_delete.append(key)
        for k in keys_to_delete:
            del self._clients[k]

    def check_rate_limit(
        self,
        client_key: str,
        custom_limit: int | None = None,
        custom_window: int | None = None,
    ) -> RateLimitResult:
        now = time.time()
        limit = custom_limit or self.default_limit
        window_size = custom_window or self.window_seconds
        threshold = now - window_size

        with self._lock:
            self._cleanup_stale_entries(now)
            client = self._clients[client_key]
            # Prune timestamps outside current window
            client.timestamps = [t for t in client.timestamps if t > threshold]

            count = len(client.timestamps)
            if count >= limit:
                # Rate limit exceeded
                oldest = client.timestamps[0]
                retry_after = max(1, int(oldest + window_size - now))
                reset_seconds = retry_after
                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    reset_seconds=reset_seconds,
                    retry_after=retry_after,
                )

            # Record this request
            client.timestamps.append(now)
            remaining = max(0, limit - len(client.timestamps))
            reset_seconds = int(window_size)
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=remaining,
                reset_seconds=reset_seconds,
                retry_after=0,
            )

    def reset_for_key(self, client_key: str) -> None:
        """Resets rate limiting state for a key (useful in test teardowns)."""
        with self._lock:
            if client_key in self._clients:
                del self._clients[client_key]


# Global rate limiter instances for the application
global_api_limiter = SlidingWindowRateLimiter(default_limit=60, window_seconds=60)
ask_endpoint_limiter = SlidingWindowRateLimiter(default_limit=20, window_seconds=60)
automation_trigger_limiter = SlidingWindowRateLimiter(default_limit=5, window_seconds=60)
