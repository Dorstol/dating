import os
from uuid import uuid4

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.models import User, db_helper
from core.schemas.user import UserRead, UserUpdate
from .fastapi_users import fastapi_users

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

@router.post("/{user_id}/upload-photo")
async def upload_user_photo(
    user: User = Depends(fastapi_users.current_user),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    # Validate file type (e.g., allow only images)
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG and PNG are allowed.")

    # Generate a unique filename
    filename = f"{uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # Save the file
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Update the user's photo in the database
    query = select(User).where(User.id == user.id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.photo = f"/static/photos/{filename}"
    await session.commit()

    return {"message": "Photo uploaded and updated successfully", "photo_url": user.photo}