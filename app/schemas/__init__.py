from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[UUID] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class TeamRead(BaseModel):
    id: UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class MembershipRead(BaseModel):
    team_id: UUID
    user_id: UUID
    role: str

    class Config:
        from_attributes = True


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    body: str = ""


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    body: Optional[str] = None
    version: str


class NoteRead(BaseModel):
    id: UUID
    team_id: UUID
    author_id: Optional[UUID]
    title: str
    body: str
    version: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NoteList(BaseModel):
    notes: list[NoteRead]
    next_cursor: Optional[str] = None


class ErrorResponse(BaseModel):
    detail: str


class UserWithTeams(BaseModel):
    user: UserRead
    teams: list[TeamRead]