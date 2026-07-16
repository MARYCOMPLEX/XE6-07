"""持久化工作流协调记录。

这些表让后台编排不依赖任务进程内存，并保证工作流事件消费幂等。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import JobStatus


class MeshProcessJob(UUIDMixin, TimestampMixin, Base):
    """持久化的规范化/修复任务及其产出的新版本。"""

    __tablename__ = "mesh_process_jobs"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_revision_id: Mapped[str] = mapped_column(
        ForeignKey("asset_revisions.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    phase: Mapped[str] = mapped_column(String(32), nullable=False)
    operations: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    parameters: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=None)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, native_enum=False, length=16),
        default=JobStatus.pending,
        nullable=False,
        index=True,
    )
    new_revision_id: Mapped[str | None] = mapped_column(
        ForeignKey("asset_revisions.id", ondelete="SET NULL"), default=None
    )
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    trace_id: Mapped[str | None] = mapped_column(String(64), index=True, default=None)


class WorkflowEventReceipt(TimestampMixin, Base):
    """与项目状态流转在同一事务中 claim 的 inbox 记录。"""

    __tablename__ = "workflow_event_receipts"

    event_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(128), index=True, default=None)
    applied_status: Mapped[str] = mapped_column(String(32), nullable=False)


__all__ = ["MeshProcessJob", "WorkflowEventReceipt"]
