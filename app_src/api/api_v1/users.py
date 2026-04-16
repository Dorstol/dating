import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi_users import schemas
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.models import User, UserPhoto, db_helper
from core.schemas.block import BlockResponse
from core.schemas.report import ReportCreate, ReportResponse
from core.schemas.user import UserRead, UserUpdate
from crud.services.block_report_service import BlockReportService

from .fastapi_users import current_user, fastapi_users

router = APIRouter(
    prefix=settings.api.v1.users,
    tags=["Users"],
)

router.include_router(
    fastapi_users.get_users_router(
        UserRead,
        UserUpdate,
    ),
)

UPLOAD_DIR = "static/photos"


MAX_PHOTOS = 6


async def _save_image(file: UploadFile) -> str:
    """Validate, save and return the generated filename."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    allowed_exts = {"jpg", "jpeg", "png"}
    filename = file.filename or "upload"
    parts = filename.rsplit(".", 1)
    extension = parts[1].lower() if len(parts) == 2 else "jpg"
    if extension not in allowed_exts:
        raise HTTPException(status_code=400, detail="FILE_EXTENSION_NOT_ALLOWED")

    token_name = f"{uuid.uuid4()}.{extension}"
    generated_name = f"{UPLOAD_DIR}/{token_name}"

    data = await file.read()
    if len(data) > 5_000_000:
        raise HTTPException(status_code=400, detail="UNSUPPORTED_FILE_SIZE")

    with open(generated_name, "wb") as f:
        f.write(data)

    try:
        img = Image.open(generated_name)
        img.verify()
        img = Image.open(generated_name)
        img.save(generated_name, optimize=True)
    except (UnidentifiedImageError, OSError):
        try:
            os.remove(generated_name)
        except OSError:
            pass
        raise HTTPException(status_code=400, detail="INVALID_IMAGE_FILE") from None

    return token_name


@router.post(
    "/me/upload_photo",
    name="users:upload_photo",
)
async def upload_user_photo(
    file: UploadFile = File(...),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    if len(user.photos) >= MAX_PHOTOS:
        raise HTTPException(status_code=400, detail="PHOTO_LIMIT_REACHED")

    token_name = await _save_image(file)

    next_order = max((p.order for p in user.photos), default=-1) + 1
    photo = UserPhoto(user_id=user.id, filename=token_name, order=next_order)
    session.add(photo)

    # Keep legacy single-photo field in sync with the first photo
    if not user.photo:
        user.photo = token_name
        session.add(user)

    await session.commit()
    await session.refresh(user)
    return schemas.model_validate(UserRead, user)


@router.delete(
    "/me/photos/{photo_id}",
    name="users:delete_photo",
)
async def delete_user_photo(
    photo_id: int,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    result = await session.execute(
        select(UserPhoto).where(UserPhoto.id == photo_id, UserPhoto.user_id == user.id)
    )
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(status_code=404, detail="PHOTO_NOT_FOUND")

    filepath = f"{UPLOAD_DIR}/{photo.filename}"
    try:
        os.remove(filepath)
    except OSError:
        pass

    await session.delete(photo)

    # Re-order remaining photos
    remaining = sorted(
        [p for p in user.photos if p.id != photo_id], key=lambda p: p.order
    )
    for i, p in enumerate(remaining):
        p.order = i

    # Sync legacy field to first remaining photo
    user.photo = remaining[0].filename if remaining else None
    session.add(user)

    await session.commit()
    await session.refresh(user)
    return schemas.model_validate(UserRead, user)


@router.post(
    "/{user_id}/block",
    response_model=BlockResponse,
    summary="Block a user",
)
async def block_user(
    user_id: int,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    """Заблокировать пользователя"""
    try:
        block = await BlockReportService.block_user(session, user.id, user_id)
        return block
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete(
    "/{user_id}/block",
    summary="Unblock a user",
)
async def unblock_user(
    user_id: int,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    """Разблокировать пользователя"""
    try:
        await BlockReportService.unblock_user(session, user.id, user_id)
        return {"detail": "User unblocked"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get(
    "/blocked",
    response_model=list[BlockResponse],
    summary="Get blocked users",
)
async def get_blocked_users(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    """Получить список заблокированных пользователей"""
    blocks = await BlockReportService.get_blocked_users(session, user.id)
    return blocks


@router.post(
    "/{user_id}/report",
    response_model=ReportResponse,
    summary="Report a user",
)
async def report_user(
    user_id: int,
    report_data: ReportCreate,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    """Пожаловаться на пользователя"""
    try:
        report = await BlockReportService.report_user(
            session, user.id, user_id, report_data.reason, report_data.description
        )
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
