from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy.exc import NoResultFound
from sqlalchemy.dialects.postgresql import UUID

from emilia.database.models import User, Call, CallParticipant

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


async def initialize_call(db: AsyncSession, workspace_id: UUID, users: list[User]) -> UUID:
    """
    This function initializes a call with a list of users and a workspace id. 
    It returns the UUID of the newly created call. It's an asynchronous function, 
    meaning it's designed to be part of an async application and must be awaited.

    Args:
        db (AsyncSession): The database session.
        workspace_id (uuid.UUID): The UUID of the workspace where the call is being initialized.
        users (list[User]): The list of users to initialize the call with.

    Returns:
        UUID: The UUID of the newly created call.
    """
    # Create a new call
    new_call = Call(
        workspace_id=workspace_id,  # Workspace id is now directly provided
        start_time=datetime.now(),
        status='initiated'
    )
    db.add(new_call)
    await db.commit()
    await db.refresh(new_call)

    # Add users as participants to the call
    for user in users:
        new_participant = CallParticipant(
            call_id=new_call.id,
            user_id=user.id,
            role='participant'  # Assuming all users are participants
        )
        db.add(new_participant)
    await db.commit()

    # Return the UUID of the newly created call
    return new_call.id