import uuid

from PIL import Image
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_users import schemas
from core.config import settings
from core.models import User, db_helper
from core.schemas.user import UserRead, UserUpdate
from .fastapi_users import fastapi_users, current_user

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
    if file.size >= 1000000:
        return {"detail": "UNSUPPORTED_FILE_SIZE"}

    filename = file.filename
    extension = filename.split(".")[1]

    if extension not in ["jpg", "png", "jpeg", "svg"]:
        return {"detail": "FILE_EXTENSION_NOT_ALLOWED"}

    token_name = f"{uuid.uuid4()}.{extension}"
    generated_name = f"{UPLOAD_DIR}/{token_name}"
    file_content = await file.read()

    with open(generated_name, "wb") as f:
        f.write(file_content)

    # Pillow
    img = Image.open(generated_name)
    img.save(generated_name, optimize=True)

    user.photo = token_name
    session.add(user)
    await session.commit()
    return schemas.model_validate(UserRead, user)
