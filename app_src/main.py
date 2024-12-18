import logging

import uvicorn
from fastapi.staticfiles import StaticFiles

from api import router as api_router
from core.config import settings
from create_fastapi_app import create_app

logging.basicConfig(
    level=logging.INFO,
    format=settings.logging.log_format,
)

main_app = create_app(
    create_custom_static_urls=True,
)

main_app.mount("/static", StaticFiles(directory="static"), name="static", )

main_app.include_router(
    api_router,
)

if __name__ == "__main__":
    uvicorn.run(
        "main:main_app",
        host=settings.run.host,
        port=settings.run.port,
        reload=True,
    )
