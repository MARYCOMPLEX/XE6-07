"""打印提交与生命周期逻辑——骨架 mock 桩版。"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ValidationError
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
from app.modules.devices.service import DeviceService

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
        # 确定性桩：用 id 前缀模拟门禁的拒绝路径，真实实现从库里读实际状态。
        confirmed = None if checklist_id.startswith("unconfirmed") else "2026-01-01T00:00:00Z"
        checklist = PrintChecklist(
            id=checklist_id,
            slice_job_id=gen_uuid(),
            printer_id=gen_uuid(),
            user_confirmed_at=confirmed,
            confirmed_by=None if confirmed is None else owner_id,
        )
        slice_job = SliceJob(
            id=gen_uuid(),
            revision_id=gen_uuid(),
            slicer_engine="mock",
            status=JobStatus.succeeded,
            gcode_uri="mock://gcode/x.gcode",
            estimate={"filament_g": 24.5},
            is_stale=checklist_id.startswith("stale"),
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
        # 确认门禁 + 打印前检查：只有已确认、切片未失效的清单才能下发。归属校验同时
        # 确保清单存在且属于当前用户（桩里恒真，真实实现会 raise NotFound/PermissionDenied）。
        checklist, slice_job, _revision = await self.get_owned_checklist(req.checklist_id, owner_id)
        if checklist.user_confirmed_at is None:
            raise ConflictError("Checklist is not confirmed; confirm before printing")
        if slice_job.is_stale:
            raise ConflictError("Slice result is stale; re-slice before printing")
        await DeviceService(self.session).preflight_print(
            printer_id=checklist.printer_id,
            owner_id=owner_id,
            material_id=checklist.material_id,
        )
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
        # 确定性桩：真实实现读取任务当前状态与提交时下发的取件码。
        # id 前缀 "notdone" 模拟未完成任务，用于覆盖"只能从已完成任务取件"的拒绝路径。
        current = (
            PrintJobStatus.printing
            if print_job_id.startswith("notdone")
            else PrintJobStatus.completed
        )
        if current is not PrintJobStatus.completed:
            raise ConflictError("Print job is not completed; cannot pick up")
        if code != self._expected_pickup_code(print_job_id):
            raise ValidationError("Pickup code does not match")
        return PrintJob(
            id=print_job_id,
            checklist_id=gen_uuid(),
            printer_id=gen_uuid(),
            status=PrintJobStatus.picked_up,
            progress=100.0,
            **_stamps(),
        )

    @staticmethod
    def _expected_pickup_code(job_id: str) -> str:
        # 桩里由 job id 确定性推导取件码；真实实现在提交时生成并存库。
        cleaned = "".join(c for c in job_id.upper() if c.isalnum())
        return (cleaned + "000000")[:6]

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
