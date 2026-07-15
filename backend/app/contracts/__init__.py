"""跨功能模块共享的稳定契约。

这些契约是不可变的 Pydantic 值对象，刻意不携带 FastAPI、SQLAlchemy、消息队列
或具体提供方类型。这样 HTTP 处理函数、任务进程、测试以及未来新增的传输层，
都可以复用同一组模块边界。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FrozenContract(BaseModel):
    """不可变、字段封闭的跨模块 DTO 基类。"""

    model_config = ConfigDict(frozen=True, extra="forbid")


# 将少量真正跨模块的契约集中导出，方便发现。
# 这些导入留在底部，因为子模块会继承上面的 ``FrozenContract``。
from app.contracts.artifacts import ArtifactKind, ArtifactRef  # noqa: E402
from app.contracts.jobs import JobError, JobHandle, JobKind, JobResult, JobState  # noqa: E402
from app.contracts.workflow import WorkflowEvent, WorkflowEventKind, WorkflowSource  # noqa: E402

__all__ = [
    "ArtifactKind",
    "ArtifactRef",
    "FrozenContract",
    "JobError",
    "JobHandle",
    "JobKind",
    "JobResult",
    "JobState",
    "WorkflowEvent",
    "WorkflowEventKind",
    "WorkflowSource",
]
