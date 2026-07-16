"""任务进程侧桥接：把持久化任务结果应用到项目工作流状态。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.workflow import (
    WorkflowEventKind,
    WorkflowSource,
    make_workflow_event,
)
from app.core.exceptions import InvalidStateTransitionError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.modules.projects.service import ProjectService

logger = get_logger("tasks.workflow")


async def emit_workflow_event(
    session: AsyncSession,
    *,
    kind: WorkflowEventKind,
    source: WorkflowSource,
    project_id: str,
    correlation_id: str,
    data: dict[str, Any] | None = None,
) -> None:
    """应用确定且幂等的工作流事件，同时不丢失任务输出。

    用户取消或修订项目后，旧任务完成事件仍可能稍后到达。此类领域拒绝只记录 warning，
    已持久化的 job 结果仍会保留；基础设施或数据库异常则继续向外抛出并触发回滚。
    """
    event = make_workflow_event(
        kind=kind,
        source=source,
        project_id=project_id,
        correlation_id=correlation_id,
        data=data,
    )
    try:
        await ProjectService(session).apply_workflow_event(event)
    except (InvalidStateTransitionError, NotFoundError, ValidationError) as exc:
        logger.warning(
            "workflow.event_rejected",
            event_id=event.event_id,
            project_id=project_id,
            code=exc.code,
            reason=exc.message,
        )


__all__ = ["emit_workflow_event"]
