"""生成任务：文生图、图生图和图生 3D 模型。

每次异步提供方调用对应一行任务记录，并关联到项目和触发它的对话消息，让生成产物可以
回溯到具体用户轮次。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import GenerationKind, JobStatus


class GenerationJob(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "generation_jobs"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # 回链到触发生成的对话轮次。
    chat_message_id: Mapped[str | None] = mapped_column(
        ForeignKey("chat_messages.id", ondelete="SET NULL"), default=None, index=True
    )
    kind: Mapped[GenerationKind] = mapped_column(
        Enum(GenerationKind, native_enum=False, length=32), nullable=False
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, native_enum=False, length=16),
        default=JobStatus.pending,
        nullable=False,
        index=True,
    )
    provider: Mapped[str | None] = mapped_column(String(64), default=None)
    is_fallback: Mapped[bool] = mapped_column(default=False, nullable=False)
    prompt: Mapped[str | None] = mapped_column(Text, default=None)
    params: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=None)
    input_uris: Mapped[list[Any] | None] = mapped_column(JSONB, default=None)
    # 幂等与可追踪性。
    input_hash: Mapped[str | None] = mapped_column(String(64), index=True, default=None)
    trace_id: Mapped[str | None] = mapped_column(String(64), index=True, default=None)
    latency_ms: Mapped[int | None] = mapped_column(Integer, default=None)
    error_code: Mapped[str | None] = mapped_column(String(64), default=None)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    outputs: Mapped[list[GeneratedImage]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class GeneratedImage(UUIDMixin, TimestampMixin, Base):
    """参考图或概念图，关联到生成任务和项目。"""

    __tablename__ = "generated_images"

    job_id: Mapped[str] = mapped_column(
        ForeignKey("generation_jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    uri: Mapped[str] = mapped_column(String(512), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(64), default=None)
    seed: Mapped[int | None] = mapped_column(Integer, default=None)
    quality_score: Mapped[float | None] = mapped_column(Float, default=None)
    selected: Mapped[bool] = mapped_column(default=False, nullable=False)

    job: Mapped[GenerationJob] = relationship(back_populates="outputs")
