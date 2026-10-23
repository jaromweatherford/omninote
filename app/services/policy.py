from abc import ABC, abstractmethod
from enum import Enum
from uuid import UUID


class Action(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    MANAGE_ACCESS = "manage_access"


class ResourceType(str, Enum):
    TEAM = "team"
    NOTE = "note"


class AuthorizationResult(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


class Resource:
    def __init__(self, resource_type: ResourceType, resource_id: UUID, team_id: UUID | None = None):
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.team_id = team_id


class Policy(ABC):
    @abstractmethod
    async def authorize(self, user_id: UUID, action: Action, resource: Resource) -> AuthorizationResult:
        pass


class MembershipPolicy(Policy):
    def __init__(self, db):
        self.db = db

    async def authorize(self, user_id: UUID, action: Action, resource: Resource) -> AuthorizationResult:
        from app.models import Membership
        from sqlalchemy import select

        if resource.resource_type == ResourceType.TEAM:
            team_id = resource.resource_id
        elif resource.resource_type == ResourceType.NOTE:
            team_id = resource.team_id
        else:
            return AuthorizationResult.DENY

        if team_id is None:
            return AuthorizationResult.DENY

        result = await self.db.execute(
            select(Membership).where(
                Membership.team_id == team_id,
                Membership.user_id == user_id
            )
        )
        membership = result.scalar_one_or_none()

        if membership is None:
            return AuthorizationResult.DENY

        if action == Action.READ:
            return AuthorizationResult.ALLOW
        elif action == Action.WRITE:
            return AuthorizationResult.ALLOW if membership.role in ("member", "admin") else AuthorizationResult.DENY
        elif action == Action.DELETE:
            return AuthorizationResult.ALLOW if membership.role == "admin" else AuthorizationResult.DENY
        elif action == Action.MANAGE_ACCESS:
            return AuthorizationResult.ALLOW if membership.role == "admin" else AuthorizationResult.DENY

        return AuthorizationResult.DENY