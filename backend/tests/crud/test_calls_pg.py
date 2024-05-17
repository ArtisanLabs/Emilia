import pytest
import uuid
from sqlmodel import Session
from emilia.models.models import Call, CallParticipant
from emilia.crud.calls import (
    create_call,
    get_call,
    create_call_participant,
    get_call_participants,
    delete_call,
    delete_call_participant,
)
# Datos de prueba para usuarios
from datetime import datetime
from uuid import UUID

TEST_WORKSPACES = [
    {
        "id": uuid.UUID("3c4b4d7b-a70a-4304-83f7-50277c2a2e52"),
        "organization_id": uuid.UUID("cf84d3c3-f92f-457d-978d-cce5acef1b2d"),
        "name": "test",
    },
]
TEST_USERS = [
    {
        "id": uuid.UUID("470bf38d-92d7-45f5-9b3c-e767562c3e2b"),
        "workspace_id": uuid.UUID("3c4b4d7b-a70a-4304-83f7-50277c2a2e52"),
        "name": "test 1",
        "email": "1@test.test",
        "phone_number": "+573009999991",
    },
    {
        "id": uuid.UUID("f87e42bd-384e-48ad-8c43-92c95a7d9fc0"),
        "workspace_id": uuid.UUID("3c4b4d7b-a70a-4304-83f7-50277c2a2e52"),
        "name": "test 2",
        "email": "2@test.test",
        "phone_number": "+573009999992",
    },
]

@pytest.mark.asyncio
async def test_create_and_get_call(test_db: Session):
    async with test_db() as db:
        test_workspace_id = TEST_WORKSPACES[0]["id"]
        test_call = Call(workspace_id=test_workspace_id, start_time="2022-01-01T00:00:00", status="initiated")
        created_call = await create_call(db=db, call=test_call)  # Use db instead of test_db
        assert created_call.id is not None
        fetched_call = await get_call(db=db, call_id=created_call.id)  # Use db instead of test_db
        assert fetched_call == created_call

# @pytest.mark.asyncio
# async def test_create_and_get_call_participant(test_db: Session):
#     test_workspace_id = TEST_WORKSPACES[0]["id"]
#     test_user_id = TEST_USERS[0]["id"]
#     test_call = Call(workspace_id=test_workspace_id, start_time="2022-01-01T00:00:00", status="initiated")
#     created_call = await create_call(db=test_db, call=test_call)
#     participant = CallParticipant(call_id=created_call.id, user_id=test_user_id, role="host")
#     created_participant = await create_call_participant(db=test_db, participant=participant)
#     assert created_participant.id is not None
#     participants = await get_call_participants(db=test_db, call_id=created_call.id)
#     assert participant in participants

# @pytest.mark.asyncio
# async def test_delete_call_and_participant(test_db: Session):
#     test_workspace_id = TEST_WORKSPACES[0]["id"]
#     test_user_id = TEST_USERS[0]["id"]
#     test_call = Call(workspace_id=test_workspace_id, start_time="2022-01-01T00:00:00", status="initiated")
#     created_call = await create_call(db=test_db, call=test_call)
#     participant = CallParticipant(call_id=created_call.id, user_id=test_user_id, role="host")
#     created_participant = await create_call_participant(db=test_db, participant=participant)
#     await delete_call_participant(db=test_db, participant_id=created_participant.id)
#     await delete_call(db=test_db, call_id=created_call.id)
#     assert await get_call(db=test_db, call_id=created_call.id) is None
#     assert await get_call_participants(db=test_db, call_id=created_call.id) == []
