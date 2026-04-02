from fastapi import APIRouter

from core.config import settings

from .api_v1 import chat_ws_router
from .api_v1 import router as router_api_v1

router = APIRouter(
    prefix=settings.api.prefix,
)
router.include_router(router_api_v1)

# WebSocket router without HTTPBearer dependency
ws_router = APIRouter(
    prefix=settings.api.prefix + settings.api.v1.prefix,
)
ws_router.include_router(chat_ws_router)
