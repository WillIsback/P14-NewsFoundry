import asyncio
import time
from collections import defaultdict, deque
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from jose import JWTError, jwt
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from api.models import error_response
from core.config import (
    ALGORITHM,
    API_AUTH_REQUIRED_PATHS,
    API_LOGIN_RATE_LIMIT_REQUESTS,
    API_LOGIN_RATE_LIMIT_WINDOW_SECONDS,
    API_RATE_LIMIT_REQUESTS,
    API_RATE_LIMIT_WINDOW_SECONDS,
    API_V1_PREFIX,
    ENABLE_HTTPS_REDIRECT,
    SECRET_KEY,
    TRUSTED_HOSTS,
)


class InMemoryRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: defaultdict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def allow(self, key: str) -> tuple[bool, int, int]:
        now = time.monotonic()
        oldest_allowed = now - self.window_seconds

        async with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] <= oldest_allowed:
                bucket.popleft()

            if len(bucket) >= self.max_requests:
                retry_after = max(1, int(self.window_seconds - (now - bucket[0])))
                return False, retry_after, 0

            bucket.append(now)
            remaining = self.max_requests - len(bucket)
            return True, 0, remaining


def _resolve_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", maxsplit=1)[0].strip()

    if request.client and request.client.host:
        return request.client.host

    return "unknown"


def _extract_bearer_token(request: Request) -> str:
    auth_header = request.headers.get("authorization", "")
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


def _verify_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject: str | None = payload.get("sub")
        if subject is None:
            raise ValueError("Missing token subject")
        return subject
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _is_login_path(path: str) -> bool:
    return path == f"{API_V1_PREFIX}/auth/login"


def _is_auth_required_path(path: str) -> bool:
    return path in set(API_AUTH_REQUIRED_PATHS)


def register_middlewares(app: FastAPI) -> None:
    """Register API-gateway style middlewares and protections."""

    limiter = InMemoryRateLimiter(
        max_requests=API_RATE_LIMIT_REQUESTS,
        window_seconds=API_RATE_LIMIT_WINDOW_SECONDS,
    )

    login_limiter = InMemoryRateLimiter(
        max_requests=API_LOGIN_RATE_LIMIT_REQUESTS,
        window_seconds=API_LOGIN_RATE_LIMIT_WINDOW_SECONDS,
    )

    if TRUSTED_HOSTS != ["*"]:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=TRUSTED_HOSTS)

    if ENABLE_HTTPS_REDIRECT:
        app.add_middleware(HTTPSRedirectMiddleware)

    app.add_middleware(GZipMiddleware, minimum_size=500)

    @app.middleware("http")
    async def api_gateway(request: Request, call_next):
        request_id = str(uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()

        active_limit = API_RATE_LIMIT_REQUESTS
        remaining = API_RATE_LIMIT_REQUESTS

        is_api_call = request.url.path.startswith(API_V1_PREFIX)
        if request.method != "OPTIONS" and is_api_call:
            client_key = _resolve_client_ip(request)
            current_limiter = limiter

            if _is_login_path(request.url.path):
                current_limiter = login_limiter
                active_limit = API_LOGIN_RATE_LIMIT_REQUESTS

            allowed, retry_after, remaining = await current_limiter.allow(client_key)
            if not allowed:
                payload = error_response(
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                    code="RATE_LIMIT_EXCEEDED",
                    message="Too many requests",
                    details={
                        "request_id": request_id,
                        "retry_after_seconds": retry_after,
                    },
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content=payload.model_dump(),
                    headers={
                        "Retry-After": str(retry_after),
                        "X-Request-Id": request_id,
                        "X-RateLimit-Limit": str(active_limit),
                        "X-RateLimit-Remaining": "0",
                    },
                )

            if _is_auth_required_path(request.url.path):
                try:
                    token = _extract_bearer_token(request)
                    request.state.user_email = _verify_access_token(token)
                except HTTPException as exc:
                    payload = error_response(
                        status=exc.status_code,
                        code="HTTP_EXCEPTION",
                        message=str(exc.detail),
                        details={"request_id": request_id},
                    )
                    return JSONResponse(
                        status_code=exc.status_code,
                        content=payload.model_dump(),
                        headers={
                            "WWW-Authenticate": "Bearer",
                            "X-Request-Id": request_id,
                            "X-RateLimit-Limit": str(active_limit),
                            "X-RateLimit-Remaining": str(remaining),
                        },
                    )

        response = await call_next(request)
        process_time_ms = (time.perf_counter() - start) * 1000

        response.headers["X-Request-Id"] = request_id
        response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"
        response.headers["X-RateLimit-Limit"] = str(active_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response
