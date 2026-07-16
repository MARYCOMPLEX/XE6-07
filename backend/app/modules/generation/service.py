"""生成编排（意图识别、文生图、图生图、图生 3D）——骨架 mock 桩版。

真实实现里服务层负责决策与持久化，并为每次提供方调用登记 ``GenerationJob``、计算幂等键、
把任务交给异步任务进程。骨架阶段业务逻辑被 mock 替换：每个方法只记录“确实被调用”的
日志，并返回带 id 的内存桩对象，不查库、不做归属校验、不入队真实任务。方法名、签名与
返回类型保持不变，因此上层路由、Agent 工具与脚本看到的业务入口形状与真实实现一致。

接回真实逻辑时，用被移除的仓储/任务实现替换本文件即可，调用方无需改动。
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.base import gen_uuid
from app.models.enums import GenerationKind, JobStatus
from app.models.generation import GenerationJob

from .schemas import (
    ImageToImagesRequest,
    ImageToModelRequest,
    IntentRecognizeRequest,
    IntentRecognizeResult,
    TextToImageRequest,
)

logger = get_logger("generation")


def _stamps() -> dict[str, datetime]:
    """瞬态桩对象补 created_at/updated_at。

    真实场景由数据库 server_default 生成；骨架不落库，瞬态对象这些字段为 None，
    会导致 TimestampedOut 响应校验失败。接入持久化后本辅助整体移除。
    """
    now = datetime.now(UTC)
    return {"created_at": now, "updated_at": now}


class GenerationService:
    """创建生成任务，并暴露意图识别能力。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # -- 意图识别：发生在生成前 -------------------------------------------
    async def recognize_intent(
        self, project_id: str, owner_id: str, req: IntentRecognizeRequest
    ) -> IntentRecognizeResult:
        logger.info("generation.recognize_intent(mock)", project_id=project_id, owner_id=owner_id)
        return IntentRecognizeResult(
            intent_type="generate" if req.text or req.image_uris else "chat",
            subject=(req.text or "").strip()[:64] or None,
            style=req.context.get("style"),
            use_case=req.context.get("use_case"),
            missing_fields=[],
            confidence=1.0,
        )

    # -- 文生图 -----------------------------------------------------------
    async def text_to_image(
        self, project_id: str, owner_id: str, req: TextToImageRequest
    ) -> GenerationJob:
        logger.info("generation.text_to_image(mock)", project_id=project_id, owner_id=owner_id)
        return GenerationJob(
            id=gen_uuid(),
            project_id=project_id,
            chat_message_id=req.chat_message_id,
            kind=GenerationKind.text_to_image,
            status=JobStatus.pending,
            provider="mock",
            prompt=req.prompt,
            params={"n": req.n, "style": req.style, "seed": req.seed},
        )

    # -- 图生图 -----------------------------------------------------------
    async def image_to_images(
        self, project_id: str, owner_id: str, req: ImageToImagesRequest
    ) -> GenerationJob:
        logger.info("generation.image_to_images(mock)", project_id=project_id, owner_id=owner_id)
        return GenerationJob(
            id=gen_uuid(),
            project_id=project_id,
            chat_message_id=req.chat_message_id,
            kind=GenerationKind.image_to_images,
            status=JobStatus.pending,
            provider="mock",
            prompt=req.prompt,
            params={"n": req.n, "strength": req.strength},
            input_uris=[req.source_image_uri],
        )

    # -- 图生 3D 模型 -----------------------------------------------------
    async def image_to_model(
        self, project_id: str, owner_id: str, req: ImageToModelRequest
    ) -> GenerationJob:
        logger.info("generation.image_to_model(mock)", project_id=project_id, owner_id=owner_id)
        return GenerationJob(
            id=gen_uuid(),
            project_id=project_id,
            chat_message_id=req.chat_message_id,
            kind=GenerationKind.image_to_model,
            status=JobStatus.pending,
            provider="mock",
            prompt=None,
            params={"face_preference": req.face_preference},
            input_uris=[req.source_image_uri],
        )

    # -- 读取 -------------------------------------------------------------
    async def get_job(self, job_id: str, owner_id: str) -> GenerationJob:
        logger.info("generation.get_job(mock)", job_id=job_id, owner_id=owner_id)
        # 瞬态对象未 flush，列默认值不会写入；显式补时间戳与 is_fallback/retry_count，
        # 让 202 返回的任务句柄可被 GET /jobs/{id} 成功轮询（否则响应校验 500）。
        return GenerationJob(
            id=job_id,
            project_id=gen_uuid(),
            kind=GenerationKind.text_to_image,
            status=JobStatus.pending,
            provider="mock",
            is_fallback=False,
            retry_count=0,
            **_stamps(),
        )

    async def list_jobs(
        self, project_id: str, owner_id: str, *, offset: int, limit: int
    ) -> tuple[Sequence[GenerationJob], int]:
        logger.info("generation.list_jobs(mock)", project_id=project_id, owner_id=owner_id)
        return [], 0
