from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas import TeamCreate, TeamRead, MembershipRead
from app.services.db_service import create_team, get_team, get_user_teams, is_team_member, get_user_role_in_team
from app.api.deps import get_current_user_id, authorize
from app.services.policy import Action, ResourceType

router = APIRouter(prefix="/v1/teams", tags=["teams"])


@router.post("", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
async def create_team_endpoint(
    team_in: TeamCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    team = await create_team(db, team_in, user_id)
    return team


@router.get("", response_model=list[TeamRead])
async def list_teams(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    teams = await get_user_teams(db, user_id)
    return teams


@router.get("/{team_id}", response_model=TeamRead)
async def get_team_endpoint(
    team_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(authorize(Action.READ, ResourceType.TEAM))
):
    team = await get_team(db, team_id)
    if not team:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.get("/{team_id}/members", response_model=list[MembershipRead])
async def list_team_members(
    team_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(authorize(Action.READ, ResourceType.TEAM))
):
    from app.models import Membership, User
    from sqlalchemy import select
    
    result = await db.execute(
        select(Membership, User)
        .join(User, User.id == Membership.user_id)
        .where(Membership.team_id == team_id)
    )
    memberships = []
    for membership, user in result.all():
        memberships.append(MembershipRead(
            team_id=membership.team_id,
            user_id=membership.user_id,
            role=membership.role
        ))
    return memberships