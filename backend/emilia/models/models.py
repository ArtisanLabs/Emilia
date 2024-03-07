from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class OrganizationSchema(BaseModel):
    id: uuid.UUID
    name: str
    domain: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class WorkspaceSchema(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class UserSchema(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    email: str
    phone_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class WorkspaceRoleSchema(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class CallSchema(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class CallParticipantSchema(BaseModel):
    id: uuid.UUID
    call_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class CallRecordingSchema(BaseModel):
    id: uuid.UUID
    call_id: uuid.UUID
    recording_url: str
    duration_in_seconds: Optional[float] = None
    storage_bucket: Optional[str] = None
    storage_object_key: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ConversationSchema(BaseModel):
    id: uuid.UUID
    call_id: uuid.UUID
    transcript: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True