import logging

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.models import User, db_helper
from crud.services.chat_service import ChatService
from crud.services.connection_manager import manager

from .fastapi_users import current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix=settings.api.v1.chat,
    tags=["Chat"],
)


class MessageOut(BaseModel):
    id: int
    match_id: int
    sender_id: int
    text: str
    is_read: bool
    created_at: str


class HistoryResponse(BaseModel):
    messages: list[MessageOut]
    total: int


async def _get_user_by_token(
    token: str,
    session: AsyncSession,
) -> User | None:
    """Look up user by access token for WebSocket auth."""
    from core.models.access_token import AccessToken
    from sqlalchemy import select

    result = await session.execute(
        select(AccessToken).where(AccessToken.token == token)
    )
    access_token = result.scalar_one_or_none()
    if access_token is None:
        return None

    result = await session.execute(
        select(User).where(User.id == access_token.user_id)
    )
    return result.scalar_one_or_none()


@router.websocket("/ws/{match_id}")
async def websocket_chat(
    websocket: WebSocket,
    match_id: int,
    token: str = Query(...),
):
    """
    WebSocket endpoint for real-time chat.

    Connect with: ws://host/api/v1/chat/ws/{match_id}?token=<access_token>
    Send messages as JSON: {"text": "hello"}
    """
    async with db_helper.session_factory() as session:
        user = await _get_user_by_token(token, session)
        if user is None:
            await websocket.close(code=4001, reason="Invalid token")
            return

        try:
            match = await ChatService.validate_match_participant(
                session, match_id, user.id
            )
        except ValueError as e:
            await websocket.close(code=4003, reason=str(e))
            return

        await manager.connect(websocket, match_id, user.id)

        try:
            while True:
                data = await websocket.receive_json()
                text = data.get("text", "").strip()
                if not text:
                    continue

                message = await ChatService.save_message(
                    session, match_id, user.id, text
                )

                outgoing = {
                    "id": message.id,
                    "match_id": match_id,
                    "sender_id": user.id,
                    "text": message.text,
                    "is_read": False,
                    "created_at": message.created_at.isoformat(),
                }

                await manager.broadcast(match_id, outgoing)

        except WebSocketDisconnect:
            await manager.disconnect(match_id, user.id)
        except Exception:
            logger.exception("WebSocket error for match_id=%s user_id=%s", match_id, user.id)
            await manager.disconnect(match_id, user.id)


@router.get(
    "/{match_id}/history",
    response_model=HistoryResponse,
    summary="Get chat message history",
)
async def get_chat_history(
    match_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    """Get paginated message history for a match."""
    try:
        await ChatService.validate_match_participant(session, match_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e

    messages, total = await ChatService.get_history(
        session, match_id, limit=limit, offset=offset
    )

    return HistoryResponse(
        messages=[
            MessageOut(
                id=msg.id,
                match_id=msg.match_id,
                sender_id=msg.sender_id,
                text=msg.text,
                is_read=msg.is_read,
                created_at=msg.created_at.isoformat(),
            )
            for msg in messages
        ],
        total=total,
    )


@router.post(
    "/{match_id}/read",
    summary="Mark messages as read",
)
async def mark_messages_read(
    match_id: int,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    """Mark all unread messages in a match as read."""
    try:
        await ChatService.validate_match_participant(session, match_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e

    count = await ChatService.mark_as_read(session, match_id, user.id)
    return {"marked_read": count}
