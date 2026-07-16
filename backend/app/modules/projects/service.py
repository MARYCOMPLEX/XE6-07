"""项目工作台逻辑——骨架 mock 桩版。

真实实现里所有项目状态变化都必须经过状态机，并落库到 Postgres。骨架阶段业务逻辑被
mock 替换：每个方法只记录"确实被调用"的日志，并返回带 id 的内存桩对象，不查库、不做
状态机校验。方法名、签名与返回类型保持不变，因此上层路由、Agent 工具与脚本看到的
业务入口形状与真实实现一致。

接回真实逻辑时，用被移除的状态机/仓储实现替换本文件即可，调用方无需改动。
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.workflow import WorkflowEvent
from app.core.logging import get_logger
from app.models.base import gen_uuid
from app.models.enums import ProjectStatus, SourceType
from app.models.project import ChatMessage, DesignIntent, Project

from .schemas import ChatMessageCreate, DesignIntentUpsert, ProjectCreate

logger = get_logger("projects")


def _stamps() -> dict[str, datetime]:
    """瞬态桩对象补 created_at/updated_at。

    真实场景由数据库 server_default 生成；骨架不落库，瞬态对象这些字段为 None，
    会导致 TimestampedOut 响应校验失败。接入持久化后本辅助整体移除。
    """
    now = datetime.now(UTC)
    return {"created_at": now, "updated_at": now}


class ProjectService:
    """创建项目、驱动状态、管理设计意图与对话轮次（mock 桩）。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # -- 项目 -------------------------------------------------------------
    async def create(self, owner_id: str, data: ProjectCreate) -> Project:
        logger.info("projects.create(mock)", owner_id=owner_id, title=data.title)
        return Project(
            id=gen_uuid(),
            owner_id=owner_id,
            title=data.title,
            scenario=data.scenario,
            source_type=data.source_type,
            status=ProjectStatus.draft,
            **_stamps(),
        )

    async def get(self, project_id: str, owner_id: str) -> Project:
        logger.info("projects.get(mock)", project_id=project_id, owner_id=owner_id)
        return self._stub_project(project_id, owner_id)

    async def list_mine(
        self, owner_id: str, *, offset: int, limit: int
    ) -> tuple[Sequence[Project], int]:
        logger.info("projects.list_mine(mock)", owner_id=owner_id)
        return [], 0

    async def transition(self, project_id: str, owner_id: str, target: ProjectStatus) -> Project:
        logger.info(
            "projects.transition(mock)",
            project_id=project_id,
            target=target.value,
        )
        return self._stub_project(project_id, owner_id, status=target)

    async def transition_with_reason(
        self,
        project_id: str,
        owner_id: str,
        target: ProjectStatus,
        *,
        reason: str,
        causation_id: str | None = None,
    ) -> Project:
        logger.info(
            "projects.transition_with_reason(mock)",
            project_id=project_id,
            target=target.value,
            reason=reason,
            causation_id=causation_id,
        )
        return self._stub_project(project_id, owner_id, status=target)

    async def transition_user_command(
        self, project_id: str, owner_id: str, target: ProjectStatus
    ) -> Project:
        logger.info(
            "projects.transition_user_command(mock)",
            project_id=project_id,
            target=target.value,
        )
        return self._stub_project(project_id, owner_id, status=target)

    # -- 设计意图 ---------------------------------------------------------
    async def upsert_intent(
        self, project_id: str, owner_id: str, data: DesignIntentUpsert
    ) -> DesignIntent:
        logger.info("projects.upsert_intent(mock)", project_id=project_id)
        return DesignIntent(
            id=gen_uuid(),
            project_id=project_id,
            **data.model_dump(exclude_unset=True),
        )

    async def get_intent(self, project_id: str, owner_id: str) -> DesignIntent:
        logger.info("projects.get_intent(mock)", project_id=project_id)
        return DesignIntent(id=gen_uuid(), project_id=project_id)

    # -- 对话 -------------------------------------------------------------
    async def add_message(
        self, project_id: str, owner_id: str, data: ChatMessageCreate
    ) -> ChatMessage:
        logger.info("projects.add_message(mock)", project_id=project_id, role=data.role)
        return ChatMessage(id=gen_uuid(), project_id=project_id, **data.model_dump(), **_stamps())

    async def list_messages(
        self, project_id: str, owner_id: str, *, offset: int, limit: int
    ) -> tuple[Sequence[ChatMessage], int]:
        logger.info("projects.list_messages(mock)", project_id=project_id)
        return [], 0

    async def apply_workflow_event(self, event: WorkflowEvent) -> Project:
        """幂等地应用一条工作流事件（mock 桩）。

        真实实现会经状态机推进项目状态并 claim inbox 记录。桩版只记录事件已被消费，
        并回一个带 id 的项目对象，供编排层继续读取 ``.status``。
        """
        logger.info(
            "projects.apply_workflow_event(mock)",
            event_id=event.event_id,
            kind=event.kind.value,
            source=event.source.value,
            project_id=event.project_id,
        )
        return self._stub_project(event.project_id, owner_id="mock-owner")

    # -- 辅助 -------------------------------------------------------------
    @staticmethod
    def _stub_project(
        project_id: str,
        owner_id: str,
        *,
        status: ProjectStatus = ProjectStatus.draft,
    ) -> Project:
        return Project(
            id=project_id,
            owner_id=owner_id,
            title="(mock project)",
            source_type=SourceType.text,
            status=status,
            **_stamps(),
        )
