"""工作台接口：项目、状态流转、设计意图和对话。"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.core.deps import CurrentUserDep, DbSession, PaginationDep
from app.schemas.common import OffsetPage

from .schemas import (
    ChatMessageCreate,
    ChatMessageOut,
    DesignIntentOut,
    DesignIntentUpsert,
    ProjectCreate,
    ProjectOut,
    ProjectStatusUpdate,
)
from .service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(data: ProjectCreate, current: CurrentUserDep, db: DbSession) -> ProjectOut:
    project = await ProjectService(db).create(current.id, data)
    return ProjectOut.model_validate(project)


@router.get("", response_model=OffsetPage[ProjectOut])
async def list_projects(
    current: CurrentUserDep, db: DbSession, pg: PaginationDep
) -> OffsetPage[ProjectOut]:
    items, total = await ProjectService(db).list_mine(current.id, offset=pg.offset, limit=pg.size)
    return OffsetPage(
        items=[ProjectOut.model_validate(p) for p in items],
        total=total,
        page=pg.page,
        size=pg.size,
    )


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str, current: CurrentUserDep, db: DbSession) -> ProjectOut:
    project = await ProjectService(db).get(project_id, current.id)
    return ProjectOut.model_validate(project)


@router.post("/{project_id}/transition", response_model=ProjectOut)
async def transition_project(
    project_id: str,
    data: ProjectStatusUpdate,
    current: CurrentUserDep,
    db: DbSession,
) -> ProjectOut:
    """应用明确用户决策；系统结果态只能通过事件进入。"""
    project = await ProjectService(db).transition_user_command(project_id, current.id, data.target)
    return ProjectOut.model_validate(project)


# -- 设计意图 ----------------------------------------------------------------
@router.put("/{project_id}/intent", response_model=DesignIntentOut)
async def upsert_intent(
    project_id: str,
    data: DesignIntentUpsert,
    current: CurrentUserDep,
    db: DbSession,
) -> DesignIntentOut:
    intent = await ProjectService(db).upsert_intent(project_id, current.id, data)
    return DesignIntentOut.model_validate(intent)


@router.get("/{project_id}/intent", response_model=DesignIntentOut)
async def get_intent(project_id: str, current: CurrentUserDep, db: DbSession) -> DesignIntentOut:
    intent = await ProjectService(db).get_intent(project_id, current.id)
    return DesignIntentOut.model_validate(intent)


# -- 对话 --------------------------------------------------------------------
@router.post(
    "/{project_id}/messages",
    response_model=ChatMessageOut,
    status_code=status.HTTP_201_CREATED,
)
async def post_message(
    project_id: str,
    data: ChatMessageCreate,
    current: CurrentUserDep,
    db: DbSession,
) -> ChatMessageOut:
    msg = await ProjectService(db).add_message(project_id, current.id, data)
    return ChatMessageOut.model_validate(msg)


@router.get("/{project_id}/messages", response_model=OffsetPage[ChatMessageOut])
async def list_messages(
    project_id: str,
    current: CurrentUserDep,
    db: DbSession,
    pg: PaginationDep,
) -> OffsetPage[ChatMessageOut]:
    items, total = await ProjectService(db).list_messages(
        project_id, current.id, offset=pg.offset, limit=pg.size
    )
    return OffsetPage(
        items=[ChatMessageOut.model_validate(m) for m in items],
        total=total,
        page=pg.page,
        size=pg.size,
    )
