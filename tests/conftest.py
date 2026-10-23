import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.session import Base, get_db
from app.core.config import settings
from app.models import User, Team, Membership, Note
from app.services.auth import get_password_hash, create_access_token
import uuid


TEST_DATABASE_URL = "postgresql+asyncpg://omninote:omninote@localhost:5432/omninote_test"

test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
test_async_session_maker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with test_async_session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(db_engine):
    async with test_async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def user1(db_session):
    user = User(email="user1@test.com", password_hash=get_password_hash("password123"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def user2(db_session):
    user = User(email="user2@test.com", password_hash=get_password_hash("password123"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def user3(db_session):
    user = User(email="user3@test.com", password_hash=get_password_hash("password123"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def team1(db_session, user1):
    team = Team(name="Team 1")
    db_session.add(team)
    await db_session.flush()
    membership = Membership(team_id=team.id, user_id=user1.id, role="admin")
    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(team)
    return team


@pytest_asyncio.fixture
async def team2(db_session, user2):
    team = Team(name="Team 2")
    db_session.add(team)
    await db_session.flush()
    membership = Membership(team_id=team.id, user_id=user2.id, role="admin")
    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(team)
    return team


@pytest_asyncio.fixture
async def token1(user1):
    return create_access_token({"sub": str(user1.id)})


@pytest_asyncio.fixture
async def token2(user2):
    return create_access_token({"sub": str(user2.id)})


@pytest_asyncio.fixture
async def token3(user3):
    return create_access_token({"sub": str(user3.id)})


@pytest_asyncio.fixture
async def auth_headers1(token1):
    return {"Authorization": f"Bearer {token1}"}


@pytest_asyncio.fixture
async def auth_headers2(token2):
    return {"Authorization": f"Bearer {token2}"}


@pytest_asyncio.fixture
async def auth_headers3(token3):
    return {"Authorization": f"Bearer {token3}"}