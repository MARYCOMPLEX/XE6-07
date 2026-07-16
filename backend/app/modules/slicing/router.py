"""切片 API 与打印确认门禁。

切片创建是异步的，返回 ``202`` 和任务句柄。清单构建与确认共同构成人工门禁：只有已确认
清单才能产生可下发的打印任务，设备模块会在启动物理打印前检查它。
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.core.deps import CurrentUserDep, DbSession
from app.core.exceptions import ValidationError
from app.models.enums import JobStatus
from app.models.print import PrintChecklist
from app.modules.devices.service import DeviceService
from app.schemas.common import Message

from .schemas import (
    ChecklistBuildRequest,
    ChecklistOut,
    ConfirmRequest,
    SliceAccepted,
    SliceJobOut,
    SliceRequest,
)
from .service import SlicingService

router = APIRouter(prefix="/slicing", tags=["slicing"])


# -- 切片 -----------------------------------------------------------------
@router.post("/slice", response_model=SliceAccepted, status_code=status.HTTP_202_ACCEPTED)
async def slice_model(body: SliceRequest, db: DbSession, user: CurrentUserDep) -> SliceAccepted:
    if body.mode not in {"time", "material", "safe"}:
        raise ValidationError("Unsupported slice mode")
    if body.slicer_engine not in {"mock", "orca", "bambu", "prusa"}:
        raise ValidationError("Unsupported slicer engine")
    devices = DeviceService(db)
    await devices.get_owned_printer(body.printer_id, user.id)
    if body.material_id is not None:
        await devices.get_owned_spool(body.material_id, user.id)
    job = await SlicingService(db).slice(user.id, body)
    return SliceAccepted(slice_job_id=job.id, status=JobStatus(job.status.value))


@router.get("/jobs/{slice_job_id}", response_model=SliceJobOut)
async def get_slice_job(slice_job_id: str, db: DbSession, user: CurrentUserDep) -> SliceJobOut:
    job = await SlicingService(db).get_job(slice_job_id, user.id)
    return SliceJobOut.model_validate(job)


@router.get("/revisions/{revision_id}/jobs", response_model=list[SliceJobOut])
async def list_slice_jobs(
    revision_id: str, db: DbSession, user: CurrentUserDep
) -> list[SliceJobOut]:
    jobs = await SlicingService(db).list_for_revision(revision_id, user.id)
    return [SliceJobOut.model_validate(j) for j in jobs]


# -- 清单确认门禁 ----------------------------------------------------------
@router.post("/checklists", response_model=ChecklistOut)
async def build_checklist(
    body: ChecklistBuildRequest, db: DbSession, user: CurrentUserDep
) -> ChecklistOut:
    devices = DeviceService(db)
    await devices.get_owned_printer(body.printer_id, user.id)
    if body.material_id is not None:
        await devices.get_owned_spool(body.material_id, user.id)
    checklist = await SlicingService(db).build_checklist(user.id, body)
    return _checklist_out(checklist)


@router.post("/checklists/confirm", response_model=ChecklistOut)
async def confirm_checklist(
    body: ConfirmRequest, db: DbSession, user: CurrentUserDep
) -> ChecklistOut:
    checklist = await SlicingService(db).confirm(user.id, body)
    return _checklist_out(checklist)


@router.get("/health", response_model=Message)
async def slicing_health() -> Message:
    return Message(message="slicing ok")


def _checklist_out(checklist: PrintChecklist) -> ChecklistOut:
    if checklist.created_at is None or checklist.updated_at is None:
        raise RuntimeError("Persisted checklist is missing timestamps")
    return ChecklistOut(
        id=checklist.id,
        created_at=checklist.created_at,
        updated_at=checklist.updated_at,
        slice_job_id=checklist.slice_job_id,
        printer_id=checklist.printer_id,
        material_id=checklist.material_id,
        estimate=checklist.estimate,
        risks=checklist.risks,
        user_confirmed_at=checklist.user_confirmed_at,
        confirmed_by=checklist.confirmed_by,
    )
