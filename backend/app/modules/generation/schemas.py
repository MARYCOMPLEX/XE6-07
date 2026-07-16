"""生成模块的请求/响应数据模式。

命名和字段就是服务层依赖的契约：``*Request`` 表示入站载荷，``*Result`` / ``*Out``
表示响应。Agent 契约要求意图识别必须返回结构化且带数据模式版本的结果，而不是自由文本。
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.enums import GenerationKind, JobStatus
from app.schemas.common import ORMModel, TimestampedOut

FacePreference = Literal["low", "standard", "high", "custom"]


# -- 意图识别：发生在图片生成前 -------------------------------------------
class IntentRecognizeRequest(BaseModel):
    """自由输入到结构化设计意图提案。

    LLM 只负责提案；确认动作发生在 projects 模块。
    """

    project_id: str
    text: str | None = None
    image_uris: list[str] = Field(default_factory=list)
    # 前序对话或已知字段，传给适配器作为上下文。
    context: dict[str, Any] = Field(default_factory=dict)


class IntentRecognizeResult(BaseModel):
    """Agent 提出的结构化、带版本的意图。"""

    schema_version: str = "v0"
    intent_type: str = "generate"
    subject: str | None = None
    style: str | None = None
    use_case: str | None = None
    size_mm: dict[str, float] | None = None
    face_preference: FacePreference | None = None
    color_mode: str | None = None
    constraints: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class InspirationRequest(BaseModel):
    """用户还没有明确想打印什么时的灵感推荐请求。"""

    category: str | None = None
    limit: int = Field(default=6, ge=1, le=20)


class InspirationItem(BaseModel):
    title: str
    prompt: str
    category: str


# -- 文生图 / 图生图 / 图生 3D 请求 ----------------------------------------
class TextToImageRequest(BaseModel):
    project_id: str
    prompt: str = Field(min_length=1)
    chat_message_id: str | None = None
    n: int = Field(default=1, ge=1, le=4)
    style: str | None = None
    seed: int | None = None


class ImageToImagesRequest(BaseModel):
    project_id: str
    source_image_uri: str
    prompt: str | None = None
    chat_message_id: str | None = None
    n: int = Field(default=4, ge=1, le=8)
    strength: float = Field(default=0.6, ge=0.0, le=1.0)


class ImageToModelRequest(BaseModel):
    project_id: str
    source_image_uri: str
    chat_message_id: str | None = None
    face_preference: FacePreference = "standard"


# -- 响应 -----------------------------------------------------------------
class GeneratedImageOut(TimestampedOut):
    job_id: str
    project_id: str
    uri: str
    provider: str | None = None
    seed: int | None = None
    quality_score: float | None = None
    selected: bool = False


class GenerationJobOut(TimestampedOut):
    project_id: str
    chat_message_id: str | None = None
    kind: GenerationKind
    status: JobStatus
    provider: str | None = None
    is_fallback: bool = False
    prompt: str | None = None
    error_code: str | None = None
    retry_count: int = 0
    outputs: list[GeneratedImageOut] = Field(default_factory=list)


class JobAccepted(ORMModel):
    """202 响应载荷：用于轮询的异步任务句柄。"""

    job_id: str
    status: JobStatus
