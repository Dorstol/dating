from typing import Optional
from typing import Sequence

from core.models.user import User
from core.schemas.user import UserCreate, UserUpdate
from core.security import verify_password
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_all_users(session: AsyncSession) -> Sequence[User]:
    result = await session.execute(select(User))
    users = result.scalars().all()
    return users


async def create_user(session: AsyncSession, user_create: UserCreate) -> User:
    hashed_password = pwd_context.hash(user_create.password)
    new_user = User(
        username=user_create.username,
        email=user_create.email,
        password_hash=hashed_password,
        gender=user_create.gender,
        age=user_create.age,
        bio=user_create.bio,
        interest=user_create.interest,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    return user


async def update_user(
    session: AsyncSession, user_id: int, user_update: UserUpdate
) -> Optional[User]:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        return None

    user_data = user_update.dict(exclude_unset=True)
    if "password" in user_data:
        user_data["hashed_password"] = pwd_context.hash(user_data.pop("password"))

    for key, value in user_data.items():
        setattr(user, key, value)

    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(session: AsyncSession, user_id: int) -> bool:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        return False

    await session.delete(user)
    await session.commit()
    return True


async def get_user(username: str, session: AsyncSession) -> Optional[User]:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def authenticate_user(username: str, password: str, session: AsyncSession):
    user = await get_user(username=username, session=session)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user
