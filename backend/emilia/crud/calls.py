from typing import List, Optional
from sqlmodel import Session, select
from emilia.models.models import Call, CallParticipant
import uuid

async def create_call(db: Session, call: Call) -> Call:
    db.add(call)
    await db.commit()
    await db.refresh(call)
    return call

async def get_call(db: Session, call_id: uuid.UUID) -> Optional[Call]:
    return await db.get(Call, call_id)

async def get_calls(db: Session, skip: int = 0, limit: int = 100) -> List[Call]:
    result = await db.exec(select(Call).offset(skip).limit(limit))
    return result.scalars().all()

async def update_call(db: Session, call_id: uuid.UUID, update_data: dict) -> Optional[Call]:
    db_call = await db.get(Call, call_id)
    if db_call:
        for key, value in update_data.items():
            setattr(db_call, key, value)
        await db.commit()
        await db.refresh(db_call)
    return db_call

async def delete_call(db: Session, call_id: uuid.UUID) -> Optional[Call]:
    db_call = await db.get(Call, call_id)
    if db_call:
        await db.delete(db_call)
        await db.commit()
    return db_call

async def create_call_participant(db: Session, participant: CallParticipant) -> CallParticipant:
    db.add(participant)
    await db.commit()
    await db.refresh(participant)
    return participant

async def get_call_participants(db: Session, call_id: uuid.UUID) -> List[CallParticipant]:
    result = await db.exec(select(CallParticipant).where(CallParticipant.call_id == call_id))
    return result.scalars().all()

async def delete_call_participant(db: Session, participant_id: uuid.UUID) -> Optional[CallParticipant]:
    db_participant = await db.get(CallParticipant, participant_id)
    if db_participant:
        await db.delete(db_participant)
        await db.commit()
    return db_participant