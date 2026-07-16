"""项目聚合的数据访问。"""

from __future__ import annotations

from collections.abc import Sequence

from app.models.project import ChatMessage, DesignIntent, Project, SessionContext
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    model = Project

    async def list_for_owner(self, owner_id: str, *, offset: int, limit: int) -> Sequence[Project]:
        return await self.list(owner_id=owner_id, offset=offset, limit=limit)


class DesignIntentRepository(BaseRepository[DesignIntent]):
    model = DesignIntent

    async def get_for_project(self, project_id: str) -> DesignIntent | None:
        return await self.get_by(project_id=project_id)


class SessionRepository(BaseRepository[SessionContext]):
    model = SessionContext

    async def get_for_project(self, project_id: str) -> SessionContext | None:
        return await self.get_by(project_id=project_id)


class ChatRepository(BaseRepository[ChatMessage]):
    model = ChatMessage

    async def list_for_project(
        self, project_id: str, *, offset: int, limit: int
    ) -> Sequence[ChatMessage]:
        return await self.list(project_id=project_id, offset=offset, limit=limit)
