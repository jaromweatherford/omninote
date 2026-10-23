from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.auth import decode_token
from app.services.db_service import get_user_by_id
from app.services.policy import Policy, MembershipPolicy, Action, Resource, ResourceType, AuthorizationResult

security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UUID:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = decode_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


async def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_policy(db: AsyncSession = Depends(get_db)) -> Policy:
    return MembershipPolicy(db)


async def authorize(
    action: Action,
    resource_type: ResourceType,
    resource_id: UUID,
    team_id: UUID | None = None,
    user_id: UUID = Depends(get_current_user_id),
    policy: Policy = Depends(get_policy)
) -> None:
    resource = Resource(resource_type=resource_type, resource_id=resource_id, team_id=team_id)
    result = await policy.authorize(user_id, action, resource)
    if result == AuthorizationResult.DENY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )