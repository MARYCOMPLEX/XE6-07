"""模型预处理/后处理编排——骨架 mock 桩版。

真实实现会落库 MeshProcessJob、入队任务并经门禁校验。骨架阶段每个方法只记录"确实被调用"
的日志，返回带 id 的内存桩对象，不查库、不校验。方法名、签名与返回类型保持不变，调用方
无需改动。
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.asset import AssetRevision, ModelAsset
from app.models.base import gen_uuid
from app.models.enums import ArtifactType, AssetRevisionStatus, JobStatus
from app.models.workflow import MeshProcessJob

from .schemas import PostprocessRequest, PreprocessRequest, ProcessAccepted

logger = get_logger("preprocess")


def _stamps() -> dict[str, datetime]:
    """瞬态桩对象补 created_at/updated_at；真实场景由 DB server_default 生成。"""
    now = datetime.now(UTC)
    return {"created_at": now, "updated_at": now}


class PreprocessService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_owned_revision_with_asset(
        self, revision_id: str, owner_id: str
    ) -> tuple[AssetRevision, ModelAsset]:
        logger.info(
            "preprocess.get_owned_revision_with_asset(mock)",
            revision_id=revision_id,
            owner_id=owner_id,
        )
        revision = AssetRevision(
            id=revision_id,
            model_asset_id=gen_uuid(),
            artifact_type=ArtifactType.generated_model,
            status=AssetRevisionStatus.printable,
            glb_uri="mock://models/x.glb",
        )
        asset = ModelAsset(
            id=revision.model_asset_id,
            project_id=gen_uuid(),
            owner_id=owner_id,
        )
        return revision, asset

    async def preprocess(self, owner_id: str, req: PreprocessRequest) -> ProcessAccepted:
        logger.info("preprocess.preprocess(mock)", owner_id=owner_id, revision_id=req.revision_id)
        return ProcessAccepted(
            job_ref=gen_uuid(),
            source_revision_id=req.revision_id,
            status=JobStatus.pending,
        )

    async def postprocess(self, owner_id: str, req: PostprocessRequest) -> ProcessAccepted:
        logger.info("preprocess.postprocess(mock)", owner_id=owner_id, revision_id=req.revision_id)
        return ProcessAccepted(
            job_ref=gen_uuid(),
            source_revision_id=req.revision_id,
            status=JobStatus.pending,
        )

    async def get_job(self, job_id: str, owner_id: str) -> MeshProcessJob:
        logger.info("preprocess.get_job(mock)", job_id=job_id, owner_id=owner_id)
        return MeshProcessJob(
            # 轮询句柄契约：返回被查询的 job_id，客户端才能与提交时的 job_ref 关联。
            id=job_id,
            project_id=gen_uuid(),
            owner_id=owner_id,
            source_revision_id=gen_uuid(),
            phase="normalize",
            operations=[],
            status=JobStatus.pending,
            **_stamps(),
        )


__all__ = ["PreprocessService"]
