from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from .models import User
from sqlalchemy.exc import NoResultFound

async def create_user(db: AsyncSession, user_data: dict) -> User:
    new_user = User(**user_data)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def get_user(db: AsyncSession, user_id: int) -> User:
    async with db as session:
        query = select(User).filter(User.id == user_id)
        result = await session.execute(query)
        try:
            return result.scalars().one()
        except NoResultFound:
            return None

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[User]:
    async with db as session:
        query = select(User).offset(skip).limit(limit)
        result = await session.execute(query)
        return result.scalars().all()

async def update_user(db: AsyncSession, user_id: int, update_data: dict) -> User:
    async with db as session:
        query = (
            update(User).
            where(User.id == user_id).
            values(**update_data).
            execution_options(synchronize_session="fetch")
        )
        await session.execute(query)
        await db.commit()

        return await get_user(db, user_id)

async def delete_user(db: AsyncSession, user_id: int) -> None:
    async with db as session:
        query = delete(User).where(User.id == user_id)
        await session.execute(query)
        await db.commit()