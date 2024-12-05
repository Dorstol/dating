from typing import Sequence, Optional

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import User
from core.schemas.user import UserCreate, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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


async def update_user(session: AsyncSession, user_id: int, user_update: UserUpdate) -> Optional[User]:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        return None

    user_data = user_update.dict(exclude_unset=True)
    if 'password' in user_data:
        user_data['hashed_password'] = pwd_context.hash(user_data.pop('password'))

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
