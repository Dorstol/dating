import logging
import time

import uvicorn
from create_fastapi_app import create_app
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from limits import parse
from limits.storage import storage_from_string
from limits.strategies import FixedWindowRateLimiter
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from api import router as api_router
from core.config import settings
from crud.services.cache_service import CacheService
from crud.services.connection_manager import manager as ws_manager

logging.basicConfig(
    level=logging.INFO,
    format=settings.logging.log_format,
)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.rate_limit.default],
    storage_uri=settings.REDIS_URL,
)

main_app = create_app(
    create_custom_static_urls=True,
)

main_app.state.limiter = limiter


@main_app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
    )

REQUEST_COUNT = Counter(
    "fastapi_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "fastapi_request_duration_seconds", "Request latency", ["endpoint"]
)


main_app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)

main_app.include_router(
    api_router,
)


@main_app.on_event("shutdown")
async def shutdown_services():
    await CacheService.close()
    await ws_manager.close()


# Rate limits for auto-generated auth routes (fastapi-users)
# Using limits library directly since slowapi decorators can't be applied
# to fastapi-users generated endpoints.
_auth_storage = storage_from_string(settings.REDIS_URL)
_auth_limiter = FixedWindowRateLimiter(_auth_storage)
AUTH_RATE_LIMITS = {
    "/api/v1/auth/login": parse(settings.rate_limit.auth_login),
    "/api/v1/auth/register": parse(settings.rate_limit.auth_register),
}


@main_app.middleware("http")
async def auth_rate_limit_middleware(request: Request, call_next):
    """Apply rate limits to fastapi-users generated auth endpoints."""
    if request.method == "POST":
        parsed_limit = AUTH_RATE_LIMITS.get(request.url.path)
        if parsed_limit:
            client_ip = get_remote_address(request)
            key = f"{request.url.path}:{client_ip}"
            if not _auth_limiter.hit(parsed_limit, key):
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": f"Rate limit exceeded: {parsed_limit}"
                    },
                )
    return await call_next(request)


@main_app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # Prefer route template to limit label cardinality
    route = request.scope.get("route")
    endpoint_label = getattr(route, "path_format", None) or request.url.path
    REQUEST_COUNT.labels(
        request.method, endpoint_label, str(response.status_code)
    ).inc()
    REQUEST_LATENCY.labels(endpoint_label).observe(process_time)
    return response


@main_app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


main_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allowed_origins,
    allow_credentials=settings.cors.allow_credentials,
    allow_methods=settings.cors.allow_methods,
    allow_headers=settings.cors.allow_headers,
)

if __name__ == "__main__":
    uvicorn.run(
        "main:main_app",
        host=settings.run.host,
        port=settings.run.port,
        reload=True,
    )
