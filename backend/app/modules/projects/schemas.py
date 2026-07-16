"""项目、会话、设计意图和对话的输入输出数据模式。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import ProjectStatus, SessionState, SourceType
from app.schemas.common import ORMModel, TimestampedOut


# -- 项目 --------------------------------------------------------------------
class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    source_type: SourceType
    scenario: str | None = None


class ProjectOut(TimestampedOut):
    owner_id: str
    title: str
    scenario: str | None = None
    status: ProjectStatus
    source_type: SourceType
    forked_from_model_id: str | None = None


class ProjectStatusUpdate(BaseModel):
    """显式状态流转请求，最终由服务内的状态机校验。"""

    target: ProjectStatus


# -- 设计意图 ----------------------------------------------------------------
class DesignIntentUpsert(BaseModel):
    subject: str | None = None
    style: str | None = None
    use_case: str | None = None
    size_mm: dict[str, float] | None = None
    face_preference: str | None = None
    color_mode: str | None = None
    constraints: dict[str, Any] | None = None
    raw_prompt: str | None = None


class DesignIntentOut(ORMModel):
    id: str
    project_id: str
    schema_version: str
    subject: str | None = None
    style: str | None = None
    use_case: str | None = None
    size_mm: dict[str, Any] | None = None
    face_preference: str | None = None
    color_mode: str | None = None
    constraints: dict[str, Any] | None = None
    raw_prompt: str | None = None


# -- 对话 --------------------------------------------------------------------
class ChatMessageCreate(BaseModel):
    role: str = Field(pattern="^(user|assistant|system)$")
    content: str
    agent_action: dict[str, Any] | None = None


class ChatMessageOut(TimestampedOut):
    project_id: str
    role: str
    content: str
    agent_action: dict[str, Any] | None = None


class SessionOut(ORMModel):
    id: str
    project_id: str
    mode: SessionState
    active_model_id: str | None = None
    last_intent: dict[str, Any] | None = None
