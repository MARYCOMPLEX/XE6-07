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
        # printer_id/material_id 由 checklist_id 确定性推导，使"打印任务绑定的是清单
        # preflight 过的打印机"这一契约可在服务级测试里断言。
        confirmed = None if checklist_id.startswith("unconfirmed") else "2026-01-01T00:00:00Z"
        # lowstock 前缀模拟耗材估算超过卷余量，覆盖 preflight 的耗材不足拒绝路径。
        filament_g = 5000.0 if checklist_id.startswith("lowstock") else 24.5
        checklist = PrintChecklist(
            id=checklist_id,
            slice_job_id=gen_uuid(),
            printer_id=self._printer_for(checklist_id),
            material_id=self._material_for(checklist_id),
            user_confirmed_at=confirmed,
            confirmed_by=None if confirmed is None else owner_id,
        )
        slice_job = SliceJob(
            id=gen_uuid(),
            revision_id=gen_uuid(),
            slicer_engine="mock",
            status=JobStatus.succeeded,
            gcode_uri="mock://gcode/x.gcode",
            estimate={"filament_g": filament_g},
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
        # 把切片的耗材估算传入 preflight，才能在下发前拒绝余量不足的卷。
        required_g = None
        if slice_job.estimate is not None:
            required_g = slice_job.estimate.get("filament_g")
        await DeviceService(self.session).preflight_print(
            printer_id=checklist.printer_id,
            owner_id=owner_id,
            material_id=checklist.material_id,
            required_filament_grams=required_g,
        )
        # 任务必须绑定清单里 preflight 过的打印机，不能另取随机设备。
        return PrintJob(
            id=gen_uuid(),
            checklist_id=req.checklist_id,
            printer_id=checklist.printer_id,
            status=PrintJobStatus.queued,
            pickup_code=self._make_pickup_code(),
        )

    # -- 读取 -------------------------------------------------------------
    async def get(self, print_job_id: str, owner_id: str) -> PrintJob:
        logger.info("printing.get(mock)", print_job_id=print_job_id, owner_id=owner_id)
        return self._load_job(print_job_id)

    def _load_job(self, print_job_id: str) -> PrintJob:
        # 确定性桩，代替"按 id 从库里读任务"。真实实现里 pickup_code 是提交时生成的
        # 随机码并存库；桩里由 id 推导作为该存储值的替身——关键是 get 与 pickup 读到
        # 的是同一个对象、同一个 code，pickup 比对的是任务存储值而非重新推导。
        # id 前缀 "notdone" 模拟进行中任务，覆盖"只能从已完成任务取件"的拒绝路径。
        status = (
            PrintJobStatus.printing
            if print_job_id.startswith("notdone")
            else PrintJobStatus.completed
        )
        progress = 40.0 if status is PrintJobStatus.printing else 100.0
        return PrintJob(
            id=print_job_id,
            checklist_id=gen_uuid(),
            printer_id=gen_uuid(),
            status=status,
            progress=progress,
            pickup_code=self._stored_pickup_code(print_job_id),
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
        # 加载任务 → 要求已完成 → 比对任务存储的取件码（GET 暴露的同一值），
        # 而非由公开 job id 重新推导。真实实现从库里读 job.pickup_code。
        job = self._load_job(print_job_id)
        if job.status is not PrintJobStatus.completed:
            raise ConflictError("Print job is not completed; cannot pick up")
        if code != job.pickup_code:
            raise ValidationError("Pickup code does not match")
        job.status = PrintJobStatus.picked_up
        return job

    @staticmethod
    def _stored_pickup_code(job_id: str) -> str:
        # 桩里由 job id 推导，作为"提交时生成的随机码已存库"的替身：get 与 pickup
        # 都经 _load_job 读到它，pickup 比对的是这个存储值。客户端从 GET 响应取码。
        cleaned = "".join(c for c in job_id.upper() if c.isalnum())
        return (cleaned + "000000")[:6]

    @staticmethod
    def _printer_for(checklist_id: str) -> str:
        # 由 checklist_id 确定性推导打印机 id，使"任务绑定 preflight 过的打印机"可测。
        cleaned = "".join(c for c in checklist_id if c.isalnum()) or "printer"
        return f"printer-{cleaned}"

    @staticmethod
    def _material_for(checklist_id: str) -> str:
        cleaned = "".join(c for c in checklist_id if c.isalnum()) or "spool"
        return f"spool-{cleaned}"

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
