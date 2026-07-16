"""切片与打印确认逻辑——骨架 mock 桩版。

真实实现里切片受可打印性门禁约束、打印下发受人工确认门禁约束，并落库/入队任务。骨架
阶段每个方法只记录"确实被调用"的日志，返回带 id 的内存桩对象，不查库、不校验。方法名、
签名与返回类型保持不变，调用方无需改动。
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.asset import AssetRevision, ModelAsset
from app.models.base import gen_uuid
from app.models.enums import ArtifactType, AssetRevisionStatus, JobStatus
from app.models.print import PrintChecklist, SliceJob

from .schemas import (
    ChecklistBuildRequest,
    ConfirmRequest,
    SliceRequest,
)

logger = get_logger("slicing")


def _stamps() -> dict[str, datetime]:
    """瞬态桩对象补 created_at/updated_at；真实场景由 DB server_default 生成。"""
    now = datetime.now(UTC)
    return {"created_at": now, "updated_at": now}


class SlicingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # -- 归属校验 ---------------------------------------------------------
    async def get_owned_revision_with_asset(
        self, revision_id: str, owner_id: str
    ) -> tuple[AssetRevision, ModelAsset]:
        logger.info(
            "slicing.get_owned_revision_with_asset(mock)",
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

    # -- 切片 -------------------------------------------------------------
    async def slice(self, owner_id: str, req: SliceRequest) -> SliceJob:
        logger.info("slicing.slice(mock)", owner_id=owner_id, revision_id=req.revision_id)
        return SliceJob(
            id=gen_uuid(),
            revision_id=req.revision_id,
            slicer_engine=req.slicer_engine,
            printer_id=req.printer_id,
            status=JobStatus.succeeded,
            gcode_uri="mock://gcode/x.gcode",
            estimate={"time_s": 5400, "filament_g": 24.5},
            is_stale=False,
            **_stamps(),
        )

    async def get_job(self, slice_job_id: str, owner_id: str) -> SliceJob:
        logger.info("slicing.get_job(mock)", slice_job_id=slice_job_id, owner_id=owner_id)
        return SliceJob(
            id=slice_job_id,
            revision_id=gen_uuid(),
            slicer_engine="mock",
            printer_id=gen_uuid(),
            status=JobStatus.succeeded,
            gcode_uri="mock://gcode/x.gcode",
            estimate={"time_s": 5400, "filament_g": 24.5},
            is_stale=False,
            **_stamps(),
        )

    async def list_for_revision(self, revision_id: str, owner_id: str) -> Sequence[SliceJob]:
        logger.info("slicing.list_for_revision(mock)", revision_id=revision_id, owner_id=owner_id)
        return []

    # -- 打印清单：人工确认门禁 -------------------------------------------
    async def build_checklist(self, owner_id: str, req: ChecklistBuildRequest) -> PrintChecklist:
        logger.info(
            "slicing.build_checklist(mock)", owner_id=owner_id, slice_job_id=req.slice_job_id
        )
        return PrintChecklist(
            id=gen_uuid(),
            slice_job_id=req.slice_job_id,
            printer_id=req.printer_id,
            material_id=req.material_id,
            estimate={},
            risks=[],
            **_stamps(),
        )

    async def confirm(self, owner_id: str, req: ConfirmRequest) -> PrintChecklist:
        logger.info("slicing.confirm(mock)", owner_id=owner_id, checklist_id=req.checklist_id)
        return PrintChecklist(
            id=gen_uuid(),
            slice_job_id=gen_uuid(),
            printer_id=gen_uuid(),
            user_confirmed_at="2026-01-01T00:00:00Z",
            confirmed_by=owner_id,
            **_stamps(),
        )

    async def invalidate_revision(
        self,
        revision_id: str,
        *,
        reason: str,
        causation_id: str | None = None,
    ) -> int:
        logger.info(
            "slicing.invalidate_revision(mock)",
            revision_id=revision_id,
            reason=reason,
            causation_id=causation_id,
        )
        return 0
