import asyncio
import uuid
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker, engine, Base
from app.services.db_service import create_user, create_team, create_note
from app.schemas import UserCreate, TeamCreate, NoteCreate
from app.models import User, Team, Membership, Note
from app.services.auth import get_password_hash


async def seed_data():
    async with async_session_maker() as db:
        # Create users
        users = []
        for i in range(3):
            email = f"user{i+1}@example.com"
            existing = await db.execute(
                text("SELECT * FROM users WHERE email = :email"),
                {"email": email}
            )
            if not existing.scalar_one_or_none():
                user = User(
                    email=email,
                    password_hash=get_password_hash("password123")
                )
                db.add(user)
                users.append(user)
            else:
                result = await db.execute(select(User).where(User.email == email))
                users.append(result.scalar_one())
        
        await db.commit()
        
        for user in users:
            await db.refresh(user)
        
        # Create teams
        team1 = Team(name="Engineering")
        team2 = Team(name="Design")
        db.add_all([team1, team2])
        await db.commit()
        await db.refresh(team1)
        await db.refresh(team2)
        
        # Create memberships
        memberships = [
            Membership(team_id=team1.id, user_id=users[0].id, role="admin"),
            Membership(team_id=team1.id, user_id=users[1].id, role="member"),
            Membership(team_id=team2.id, user_id=users[1].id, role="admin"),
            Membership(team_id=team2.id, user_id=users[2].id, role="member"),
        ]
        db.add_all(memberships)
        await db.commit()
        
        # Create notes
        note1 = Note(
            team_id=team1.id,
            author_id=users[0].id,
            title="Welcome to Engineering",
            body="This is the engineering team's shared notes.",
            version="1"
        )
        note2 = Note(
            team_id=team1.id,
            author_id=users[1].id,
            title="Sprint Planning",
            body="Sprint 1 planning notes go here.",
            version="1"
        )
        note3 = Note(
            team_id=team2.id,
            author_id=users[1].id,
            title="Design System",
            body="Design system documentation.",
            version="1"
        )
        db.add_all([note1, note2, note3])
        await db.commit()
        
        print("Seed data created successfully!")
        print(f"Users: {[u.email for u in users]}")
        print(f"Teams: {team1.name}, {team2.name}")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialized!")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        asyncio.run(init_db())
    else:
        asyncio.run(seed_data())