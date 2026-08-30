"""
ESCA HSE AI Agent - Security Middlewares Suite.

Includes:
1. SecurityHeadersMiddleware - Enforces CSP, HSTS, X-Content-Type-Options,
   X-Frame-Options, X-XSS-Protection, and Referrer-Policy.
2. RequestSizeLimitMiddleware - Prevents DoS/memory exhaustion by rejecting oversized payloads.
3. RateLimitMiddleware - Inspects incoming routes and applies appropriate rate limit tiers.
"""
import logging
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from app.security.rate_limiter import (
    global_api_limiter,
    ask_endpoint_limiter,
    automation_trigger_limiter,
)

logger = logging.getLogger("esca_security")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Applies production-grade HTTP security headers to all outgoing responses.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        
        headers = response.headers
        headers["X-Content-Type-Options"] = "nosniff"
        headers["X-Frame-Options"] = "SAMEORIGIN"
        headers["X-XSS-Protection"] = "1; mode=block"
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        # Only attach HSTS if on HTTPS or secure proxy
        if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https":
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy (allow necessary script/styles for local UI)
        if "Content-Security-Policy" not in headers:
            headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com data:; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https: http://localhost:* http://127.0.0.1:*;"
            )

        # Remove Server or implementation disclosures if present
        if "Server" in headers:
            del headers["Server"]
        if "X-Powered-By" in headers:
            del headers["X-Powered-By"]

        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Blocks abnormally large request payloads (default max 64 KB) to protect against memory exhaustion.
    """
    def __init__(self, app, max_body_bytes: int = 65536):
        super().__init__(app)
        self.max_body_bytes = max_body_bytes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_body_bytes:
                    logger.warning(
                        "request_body_too_large client_ip=%s size=%s limit=%s",
                        request.client.host if request.client else "unknown",
                        content_length,
                        self.max_body_bytes,
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": "Request payload too large. Maximum permitted size is 64 KB.",
                            "max_bytes": self.max_body_bytes,
                        },
                    )
            except ValueError:
                pass

        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Applies tiered sliding-window rate limiting to API endpoints.
    """
    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled

    def _get_client_key(self, request: Request) -> str:
        # Use X-Forwarded-For if available, else direct client IP
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        elif request.client:
            ip = request.client.host
        else:
            ip = "127.0.0.1"
        return ip

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self.enabled:
            return await call_next(request)

        path = request.url.path
        client_key = self._get_client_key(request)

        # Route matching for rate tiers
        if path in ("/ask", "/api/ask"):
            res = ask_endpoint_limiter.check_rate_limit(client_key)
        elif path == "/api/v1/automation/trigger":
            res = automation_trigger_limiter.check_rate_limit(client_key)
        elif path.startswith("/api/") or path.startswith("/health"):
            res = global_api_limiter.check_rate_limit(client_key)
        else:
            # Static files and root UI have generous default limiter
            res = global_api_limiter.check_rate_limit(client_key, custom_limit=120)

        if not res.allowed:
            logger.warning(
                "rate_limit_exceeded client_ip=%s path=%s retry_after=%s",
                client_key,
                path,
                res.retry_after,
            )
            response = JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded. Please throttle your requests.",
                    "retry_after_seconds": res.retry_after,
                },
            )
            response.headers["Retry-After"] = str(res.retry_after)
            response.headers["X-RateLimit-Limit"] = str(res.limit)
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(res.reset_seconds)
            return response

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(res.limit)
        response.headers["X-RateLimit-Remaining"] = str(res.remaining)
        response.headers["X-RateLimit-Reset"] = str(res.reset_seconds)
        return response
