"""项目、会话上下文与结构化设计意图。

Project 是工作台容器，承载一次创作从输入到打印完成的完整流程。SessionContext 保存
Agent 侧会话状态，DesignIntent 保存已确认或正在补全的结构化创作意图。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from app.models.enums import ProjectStatus, SessionState, SourceType


class Project(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "projects"

    owner_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    scenario: Mapped[str | None] = mapped_column(String(64), default=None)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, native_enum=False, length=32),
        default=ProjectStatus.draft,
        nullable=False,
        index=True,
    )
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, native_enum=False, length=32), nullable=False
    )
    version_id: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    # 社区派生来源，用于追踪社区血缘。
    forked_from_model_id: Mapped[str | None] = mapped_column(String(32), default=None)

    session: Mapped[SessionContext] = relationship(
        back_populates="project", uselist=False, cascade="all, delete-orphan"
    )
    design_intent: Mapped[DesignIntent] = relationship(
        back_populates="project", uselist=False, cascade="all, delete-orphan"
    )

    __mapper_args__ = {"version_id_col": version_id}


class SessionContext(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "session_contexts"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), unique=True, index=True
    )
    mode: Mapped[SessionState] = mapped_column(
        Enum(SessionState, native_enum=False, length=32),
        default=SessionState.CHAT,
        nullable=False,
    )
    active_model_id: Mapped[str | None] = mapped_column(String(32), default=None)
    last_intent: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=None)

    project: Mapped[Project] = relationship(back_populates="session")


class DesignIntent(UUIDMixin, TimestampMixin, Base):
    """结构化创作意图；``schema_version`` 用于兼容后续意图数据模式演进。"""

    __tablename__ = "design_intents"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), unique=True, index=True
    )
    schema_version: Mapped[str] = mapped_column(String(16), default="v0", nullable=False)
    subject: Mapped[str | None] = mapped_column(String(255), default=None)
    style: Mapped[str | None] = mapped_column(String(128), default=None)
    use_case: Mapped[str | None] = mapped_column(String(128), default=None)
    size_mm: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=None)  # {x,y,z}
    face_preference: Mapped[str | None] = mapped_column(String(32), default=None)
    color_mode: Mapped[str | None] = mapped_column(String(32), default=None)
    # 其他自由约束，例如孔位、底座、文字、材料等。
    constraints: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=None)
    raw_prompt: Mapped[str | None] = mapped_column(Text, default=None)

    project: Mapped[Project] = relationship(back_populates="design_intent")


class ChatMessage(UUIDMixin, TimestampMixin, Base):
    """对话轮次；生成产物会回链到触发它的消息。"""

    __tablename__ = "chat_messages"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # user/assistant/system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # 如果这是助手动作轮次，这里保存结构化 AgentAction 信封。
    agent_action: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=None)
