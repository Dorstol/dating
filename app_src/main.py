import logging
import time

import uvicorn
from create_fastapi_app import create_app
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from api import router as api_router
from core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format=settings.logging.log_format,
)

main_app = create_app(
    create_custom_static_urls=True,
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
    allow_origins=["https://dev.dorstol.tech"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(
        "main:main_app",
        host=settings.run.host,
        port=settings.run.port,
        reload=True,
    )
