"""打印 API：提交、监控、取消和取件。

这是流水线收口。``submit`` 由服务内的确认门禁和打印前检查保护，接口返回 ``202`` 和
可轮询的打印任务句柄；设备下发本身在任务进程中执行。
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.core.deps import CurrentUserDep, DbSession
from app.models.enums import PrintJobStatus
from app.models.print import PrintJob

from .schemas import (
    CancelResult,
    PickupRequest,
    PrintJobOut,
    PrintSubmitRequest,
    SubmitAccepted,
)
from .service import PrintingService

router = APIRouter(prefix="/print-jobs", tags=["printing"])


@router.post("", response_model=SubmitAccepted, status_code=status.HTTP_202_ACCEPTED)
async def submit_print(
    body: PrintSubmitRequest, db: DbSession, user: CurrentUserDep
) -> SubmitAccepted:
    job = await PrintingService(db).submit(user.id, body)
    return SubmitAccepted(print_job_id=job.id, status=PrintJobStatus(job.status.value))


@router.get("/{print_job_id}", response_model=PrintJobOut)
async def get_print_job(print_job_id: str, db: DbSession, user: CurrentUserDep) -> PrintJobOut:
    job = await PrintingService(db).get(print_job_id, user.id)
    return _print_job_out(job)


@router.post("/{print_job_id}/cancel", response_model=CancelResult)
async def cancel_print(print_job_id: str, db: DbSession, user: CurrentUserDep) -> CancelResult:
    job = await PrintingService(db).cancel(print_job_id, user.id)
    return CancelResult(
        print_job_id=job.id,
        status=PrintJobStatus(job.status.value),
    )


@router.post("/{print_job_id}/pickup", response_model=PrintJobOut)
async def pickup_print(
    print_job_id: str, body: PickupRequest, db: DbSession, user: CurrentUserDep
) -> PrintJobOut:
    job = await PrintingService(db).pickup(print_job_id, user.id, body.pickup_code)
    return _print_job_out(job)


def _print_job_out(job: PrintJob) -> PrintJobOut:
    if job.created_at is None or job.updated_at is None:
        raise RuntimeError("Persisted print job is missing timestamps")
    return PrintJobOut(
        id=job.id,
        created_at=job.created_at,
        updated_at=job.updated_at,
        checklist_id=job.checklist_id,
        printer_id=job.printer_id,
        status=PrintJobStatus(job.status.value),
        progress=job.progress,
        actual_time_s=job.actual_time_s,
        actual_filament_g=job.actual_filament_g,
        pickup_code=job.pickup_code,
        error_message=job.error_message,
    )
