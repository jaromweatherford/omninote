from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas import NoteCreate, NoteUpdate, NoteRead, NoteList
from app.services.db_service import (
    create_note, get_note, list_notes, update_note, delete_note,
    is_team_member
)
from app.api.deps import get_current_user_id, authorize
from app.services.policy import Action, ResourceType

router = APIRouter(prefix="/v1/teams", tags=["notes"])


@router.post("/{team_id}/notes", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
async def create_note_endpoint(
    team_id: UUID,
    note_in: NoteCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(authorize(Action.WRITE, ResourceType.TEAM))
):
    if not await is_team_member(db, team_id, user_id):
        raise HTTPException(status_code=404, detail="Team not found")
    note = await create_note(db, team_id, user_id, note_in)
    return note


@router.get("/{team_id}/notes", response_model=NoteList)
async def list_notes_endpoint(
    team_id: UUID,
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(authorize(Action.READ, ResourceType.TEAM))
):
    if not await is_team_member(db, team_id, user_id):
        raise HTTPException(status_code=404, detail="Team not found")
    notes, next_cursor = await list_notes(db, team_id, cursor, limit)
    return NoteList(notes=notes, next_cursor=next_cursor)


@router.get("/{team_id}/notes/{note_id}", response_model=NoteRead)
async def get_note_endpoint(
    team_id: UUID,
    note_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(authorize(Action.READ, ResourceType.NOTE))
):
    note = await get_note(db, team_id, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.patch("/{team_id}/notes/{note_id}", response_model=NoteRead)
async def update_note_endpoint(
    team_id: UUID,
    note_id: UUID,
    note_in: NoteUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(authorize(Action.WRITE, ResourceType.NOTE))
):
    note = await get_note(db, team_id, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    if note.version != note_in.version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Version conflict: note has been modified"
        )
    
    note = await update_note(db, note, note_in)
    return note


@router.delete("/{team_id}/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note_endpoint(
    team_id: UUID,
    note_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(authorize(Action.DELETE, ResourceType.NOTE))
):
    note = await get_note(db, team_id, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    await delete_note(db, note)