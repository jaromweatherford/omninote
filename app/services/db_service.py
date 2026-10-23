from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import User, Team, Membership, Note
from app.schemas import UserCreate, TeamCreate, NoteCreate, NoteUpdate


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    from app.services.auth import get_password_hash
    user = User(email=user_in.email, password_hash=get_password_hash(user_in.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_team(db: AsyncSession, team_in: TeamCreate, owner_id: UUID) -> Team:
    team = Team(name=team_in.name)
    db.add(team)
    await db.flush()
    membership = Membership(team_id=team.id, user_id=owner_id, role="admin")
    db.add(membership)
    await db.commit()
    await db.refresh(team)
    return team


async def get_team(db: AsyncSession, team_id: UUID) -> Team | None:
    result = await db.execute(select(Team).where(Team.id == team_id))
    return result.scalar_one_or_none()


async def get_user_teams(db: AsyncSession, user_id: UUID) -> list[Team]:
    result = await db.execute(
        select(Team)
        .join(Membership, Membership.team_id == Team.id)
        .where(Membership.user_id == user_id)
    )
    return list(result.scalars().all())


async def is_team_member(db: AsyncSession, team_id: UUID, user_id: UUID) -> bool:
    result = await db.execute(
        select(Membership).where(
            Membership.team_id == team_id,
            Membership.user_id == user_id
        )
    )
    return result.scalar_one_or_none() is not None


async def get_user_role_in_team(db: AsyncSession, team_id: UUID, user_id: UUID) -> str | None:
    result = await db.execute(
        select(Membership.role).where(
            Membership.team_id == team_id,
            Membership.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def create_note(db: AsyncSession, team_id: UUID, author_id: UUID, note_in: NoteCreate) -> Note:
    note = Note(
        team_id=team_id,
        author_id=author_id,
        title=note_in.title,
        body=note_in.body,
        version="1"
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


async def get_note(db: AsyncSession, team_id: UUID, note_id: UUID) -> Note | None:
    result = await db.execute(
        select(Note).where(Note.id == note_id, Note.team_id == team_id)
    )
    return result.scalar_one_or_none()


async def list_notes(db: AsyncSession, team_id: UUID, cursor: str | None, limit: int = 20) -> tuple[list[Note], str | None]:
    query = select(Note).where(Note.team_id == team_id).order_by(Note.updated_at.desc(), Note.id.desc()).limit(limit + 1)
    
    if cursor:
        try:
            cursor_updated_at, cursor_id = cursor.split("|")
            query = query.where(
                (Note.updated_at < cursor_updated_at) |
                ((Note.updated_at == cursor_updated_at) & (Note.id < UUID(cursor_id)))
            )
        except ValueError:
            pass

    result = await db.execute(query)
    notes = list(result.scalars().all())
    
    next_cursor = None
    if len(notes) > limit:
        notes = notes[:limit]
        last_note = notes[-1]
        next_cursor = f"{last_note.updated_at.isoformat()}|{last_note.id}"

    return notes, next_cursor


async def update_note(db: AsyncSession, note: Note, note_in: NoteUpdate) -> Note:
    if note_in.title is not None:
        note.title = note_in.title
    if note_in.body is not None:
        note.body = note_in.body
    note.version = str(int(note.version) + 1)
    await db.commit()
    await db.refresh(note)
    return note


async def delete_note(db: AsyncSession, note: Note) -> None:
    await db.delete(note)
    await db.commit()