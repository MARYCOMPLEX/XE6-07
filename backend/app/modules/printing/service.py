"""打印提交与生命周期逻辑——骨架 mock 桩版。"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.asset import AssetRevision
from app.models.base import gen_uuid
from app.models.enums import (
    ArtifactType,
    AssetRevisionStatus,
    JobStatus,
    PrintJobStatus,
)
from app.models.print import PrintChecklist, PrintJob, SliceJob

from .schemas import PrintSubmitRequest

logger = get_logger("printing")


def _stamps() -> dict[str, datetime]:
    """瞬态桩对象补 created_at/updated_at；真实场景由 DB server_default 生成。"""
    now = datetime.now(UTC)
    return {"created_at": now, "updated_at": now}


class PrintingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # -- 归属链路：清单 -> 切片任务 -> 版本 ----------------------------
    async def get_owned_checklist(
        self, checklist_id: str, owner_id: str
    ) -> tuple[PrintChecklist, SliceJob, AssetRevision]:
        logger.info(
            "printing.get_owned_checklist(mock)", checklist_id=checklist_id, owner_id=owner_id
        )
        checklist = PrintChecklist(
            id=checklist_id,
            slice_job_id=gen_uuid(),
            printer_id=gen_uuid(),
            user_confirmed_at="2026-01-01T00:00:00Z",
            confirmed_by=owner_id,
        )
        slice_job = SliceJob(
            id=gen_uuid(),
            revision_id=gen_uuid(),
            slicer_engine="mock",
            status=JobStatus.succeeded,
            gcode_uri="mock://gcode/x.gcode",
            estimate={"filament_g": 24.5},
            is_stale=False,
        )
        revision = AssetRevision(
            id=gen_uuid(),
            model_asset_id=gen_uuid(),
            artifact_type=ArtifactType.generated_model,
            status=AssetRevisionStatus.printable,
            glb_uri="mock://models/x.glb",
        )
        return checklist, slice_job, revision

    # -- 提交 -------------------------------------------------------------
    async def submit(self, owner_id: str, req: PrintSubmitRequest) -> PrintJob:
        logger.info("printing.submit(mock)", owner_id=owner_id, checklist_id=req.checklist_id)
        return PrintJob(
            id=gen_uuid(),
            checklist_id=req.checklist_id,
            printer_id=gen_uuid(),
            status=PrintJobStatus.queued,
            pickup_code=self._make_pickup_code(),
        )

    # -- 读取 -------------------------------------------------------------
    async def get(self, print_job_id: str, owner_id: str) -> PrintJob:
        logger.info("printing.get(mock)", print_job_id=print_job_id, owner_id=owner_id)
        return PrintJob(
            id=print_job_id,
            checklist_id=gen_uuid(),
            printer_id=gen_uuid(),
            status=PrintJobStatus.queued,
            progress=0.0,
            **_stamps(),
        )

    # -- 取消 -------------------------------------------------------------
    async def cancel(self, print_job_id: str, owner_id: str) -> PrintJob:
        logger.info("printing.cancel(mock)", print_job_id=print_job_id, owner_id=owner_id)
        return PrintJob(
            id=print_job_id,
            checklist_id=gen_uuid(),
            printer_id=gen_uuid(),
            status=PrintJobStatus.cancelled,
        )

    # -- 取件 -------------------------------------------------------------
    async def pickup(self, print_job_id: str, owner_id: str, code: str) -> PrintJob:
        logger.info("printing.pickup(mock)", print_job_id=print_job_id, owner_id=owner_id)
        return PrintJob(
            id=print_job_id,
            checklist_id=gen_uuid(),
            printer_id=gen_uuid(),
            status=PrintJobStatus.picked_up,
            progress=0.0,
            **_stamps(),
        )

    async def record_progress(
        self,
        print_job_id: str,
        *,
        status: PrintJobStatus,
        progress: float = 0.0,
        device_job_ref: str | None = None,
        actual_time_s: int | None = None,
        actual_filament_g: float | None = None,
        error_message: str | None = None,
    ) -> PrintJob:
        logger.info("printing.record_progress(mock)", print_job_id=print_job_id, status=status)
        return PrintJob(
            id=print_job_id,
            checklist_id=gen_uuid(),
            printer_id=gen_uuid(),
            status=status,
            progress=progress,
            device_job_ref=device_job_ref,
            actual_time_s=actual_time_s,
            actual_filament_g=actual_filament_g,
            error_message=error_message,
        )

    @staticmethod
    def _make_pickup_code() -> str:
        # 6 位人类友好的取件码，避免容易混淆的字符。
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        return "".join(secrets.choice(alphabet) for _ in range(6))
