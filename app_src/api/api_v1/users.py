import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi_users import schemas
from PIL import Image, UnidentifiedImageError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.models import User, db_helper
from core.schemas.user import UserRead, UserUpdate

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


@router.post(
    "/me/upload_photo",
    name="users:upload_photo",
)
async def upload_user_photo(
    file: UploadFile = File(...),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    # Ensure upload dir exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Limit acceptable extensions and derive from filename safely
    allowed_exts = {"jpg", "jpeg", "png"}
    filename = file.filename or "upload"
    parts = filename.rsplit(".", 1)
    extension = parts[1].lower() if len(parts) == 2 else "jpg"
    if extension not in allowed_exts:
        raise HTTPException(status_code=400, detail="FILE_EXTENSION_NOT_ALLOWED")

    # Generate server-side filename
    token_name = f"{uuid.uuid4()}.{extension}"
    generated_name = f"{UPLOAD_DIR}/{token_name}"

    # Read and enforce size limit while reading
    data = await file.read()
    if len(data) > 5_000_000:
        raise HTTPException(status_code=400, detail="UNSUPPORTED_FILE_SIZE")

    # Write to disk (blocking write kept minimal)
    with open(generated_name, "wb") as f:
        f.write(data)

    # Validate and optimize via Pillow
    try:
        img = Image.open(generated_name)
        img.verify()  # verify file integrity
        img = Image.open(generated_name)  # reopen after verify
        img.save(generated_name, optimize=True)
    except (UnidentifiedImageError, OSError):
        # Remove invalid file
        try:
            os.remove(generated_name)
        except OSError:
            pass
        raise HTTPException(status_code=400, detail="INVALID_IMAGE_FILE") from None

    user.photo = token_name
    session.add(user)
    await session.commit()
    return schemas.model_validate(UserRead, user)
