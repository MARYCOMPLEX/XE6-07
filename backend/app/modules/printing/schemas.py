"""打印任务提交与生命周期数据模式。

提交打印是流水线最后且不可轻易撤销的一步。它受两类门禁保护：清单必须带用户确认记录，
打印前检查也必须通过。提交接口只返回任务句柄，真实设备调用异步执行。
"""

from __future__ import annotations

from app.models.enums import PrintJobStatus
from app.schemas.common import ORMModel, TimestampedOut


class PrintSubmitRequest(ORMModel):
    """把已确认清单提交给打印机。

    这里只需要 ``checklist_id``；打印机和耗材都来自用户已经确认过的清单，确保提交任务与
    审阅内容完全一致。
    """

    checklist_id: str


class PrintJobOut(TimestampedOut):
    checklist_id: str
    printer_id: str
    status: PrintJobStatus
    progress: float = 0.0
    started_at: str | None = None
    completed_at: str | None = None
    actual_time_s: int | None = None
    actual_filament_g: float | None = None
    pickup_code: str | None = None
    error_message: str | None = None


class SubmitAccepted(ORMModel):
    """202 响应载荷：用于轮询的异步打印任务句柄。"""

    print_job_id: str
    status: PrintJobStatus


class PickupRequest(ORMModel):
    """用取件码确认已完成任务被取走。"""

    pickup_code: str


class CancelResult(ORMModel):
    """取消请求被接受后的返回结果。"""

    print_job_id: str
    status: PrintJobStatus
