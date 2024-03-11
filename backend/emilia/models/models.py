import uuid

from typing import List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class Organization(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    domain: str
    workspaces: List["Workspace"] = Relationship(back_populates="organization")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    deleted_at: datetime = Field(nullable=True)

class Workspace(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    organization_id: uuid.UUID = Field(foreign_key="organization.id")
    name: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    deleted_at: datetime = Field(nullable=True)
    organization: Organization = Relationship(back_populates="workspaces")
    users: List["User"] = Relationship(back_populates="workspace")
    workspace_roles: List["WorkspaceRole"] = Relationship(back_populates="workspace")
    calls: List["Call"] = Relationship(back_populates="workspace")

class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id")
    name: str
    email: str
    phone_number: str = Field(nullable=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    deleted_at: datetime = Field(nullable=True)
    workspace: Workspace = Relationship(back_populates="users")
    workspace_roles: List["WorkspaceRole"] = Relationship(back_populates="user")
    call_participants: List["CallParticipant"] = Relationship(back_populates="user")

class WorkspaceRole(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id")
    user_id: uuid.UUID = Field(foreign_key="user.id")
    role: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    workspace: Workspace = Relationship(back_populates="workspace_roles")
    user: User = Relationship(back_populates="workspace_roles")

class Call(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id")
    start_time: datetime
    end_time: datetime = Field(nullable=True)
    status: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    workspace: Workspace = Relationship(back_populates="calls")
    call_participants: List["CallParticipant"] = Relationship(back_populates="call")
    call_recordings: List["CallRecording"] = Relationship(back_populates="call")
    conversations: List["Conversation"] = Relationship(back_populates="call")

class CallParticipant(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    call_id: uuid.UUID = Field(foreign_key="call.id")
    user_id: uuid.UUID = Field(foreign_key="user.id")
    role: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    call: Call = Relationship(back_populates="call_participants")
    user: User = Relationship(back_populates="call_participants")

class CallRecording(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    call_id: uuid.UUID = Field(foreign_key="call.id")
    recording_url: str
    duration_in_seconds: float = Field(nullable=True)
    storage_bucket: str = Field(nullable=True)
    storage_object_key: str = Field(nullable=True)
    recording_metadata: str = Field(nullable=True)  # Assuming JSON string for simplicity
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    call: Call = Relationship(back_populates="call_recordings")

class Conversation(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    call_id: uuid.UUID = Field(foreign_key="call.id")
    transcript: str = Field(nullable=True)
    summary: str = Field(nullable=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    call: Call = Relationship(back_populates="conversations")
