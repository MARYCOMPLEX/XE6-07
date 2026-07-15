"""连接异步模块结果与项目主工作流的事件契约。"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from enum import StrEnum

from app.contracts import FrozenContract
from app.contracts.jobs import JobResult


class WorkflowEventKind(StrEnum):
    job_accepted = "job_accepted"
    job_started = "job_started"
    job_succeeded = "job_succeeded"
    job_failed = "job_failed"
    job_cancelled = "job_cancelled"
    audit_completed = "audit_completed"
    checklist_confirmed = "checklist_confirmed"
    print_completed = "print_completed"
    print_picked_up = "print_picked_up"


class WorkflowSource(StrEnum):
    projects = "projects"
    generation = "generation"
    assets = "assets"
    audit = "audit"
    preprocess = "preprocess"
    slicing = "slicing"
    devices = "devices"
    printing = "printing"


class WorkflowEvent(FrozenContract):
    """由模块产出的不可变事实，最终交给项目工作流消费。"""

    event_id: str
    kind: WorkflowEventKind
    source: WorkflowSource
    project_id: str
    occurred_at: datetime
    correlation_id: str | None = None
    job: JobResult | None = None
    data: Mapping[str, object] | None = None


def make_workflow_event(
    *,
    kind: WorkflowEventKind,
    source: WorkflowSource,
    project_id: str,
    correlation_id: str,
    data: Mapping[str, object] | None = None,
) -> WorkflowEvent:
    """构造 API 路径和任务进程路径都能复用的确定性事件身份。"""
    return WorkflowEvent(
        event_id=f"{source.value}:{correlation_id}:{kind.value}",
        kind=kind,
        source=source,
        project_id=project_id,
        occurred_at=datetime.now(UTC),
        correlation_id=correlation_id,
        data=data,
    )


__all__ = ["WorkflowEvent", "WorkflowEventKind", "WorkflowSource", "make_workflow_event"]
