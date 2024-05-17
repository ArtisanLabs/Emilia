import pytest
from emilia.models.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from emilia.models.models import Call
from emilia.crud.calls import create_call
from datetime import datetime
from uuid import uuid4


@pytest.mark.asyncio
async def test_create_call_sqlite(sqlite_db: AsyncSession):
    '''
    Test create call with sqlite
    '''
    # Create a new call instance
    test_call = Call(
        id=uuid4(),
        workspace_id=uuid4(),
        start_time=datetime.now(),
        status="initiated"
    )

    # Use the provided SQLite async session to create a new call
    async with sqlite_db() as db:
        created_call = await create_call(db=db, call=test_call)
        assert created_call.id is not None
        assert created_call.workspace_id == test_call.workspace_id
        assert created_call.status == test_call.status
