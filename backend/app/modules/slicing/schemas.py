"""切片与打印确认门禁的数据模式。

SliceJob 来自已审计且可打印的模型版本。PrintChecklist 是产品要求的人类确认门禁：
没有确认记录时，任务不能下发到设备。切片异步执行，因此创建接口返回可轮询的 job handle。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import JobStatus
from app.schemas.common import ORMModel, TimestampedOut

SliceMode = str  # "time" | "material" | "safe"，面向新手的友好模板。


# -- 切片 -----------------------------------------------------------------
class SliceRequest(BaseModel):
    """使用新手友好模板切片一个可打印模型版本。"""

    revision_id: str
    printer_id: str
    material_id: str | None = None
    mode: SliceMode = Field(default="safe", description="time | material | safe")
    slicer_engine: str = Field(default="mock", description="mock | orca | bambu | prusa")
    overrides: dict[str, Any] = Field(default_factory=dict)


class SliceJobOut(TimestampedOut):
    revision_id: str
    slicer_engine: str
    printer_id: str | None = None
    profile: dict[str, Any] | None = None
    status: JobStatus
    report_uri: str | None = None
    gcode_uri: str | None = None
    estimate: dict[str, Any] | None = None
    is_stale: bool = False
    error_message: str | None = None


class SliceAccepted(ORMModel):
    slice_job_id: str
    status: JobStatus


# -- 打印清单：确认门禁 ----------------------------------------------------
class ChecklistBuildRequest(BaseModel):
    """基于已完成切片任务组装打印前清单。"""

    slice_job_id: str
    printer_id: str
    material_id: str | None = None


class ChecklistOut(TimestampedOut):
    slice_job_id: str
    printer_id: str
    material_id: str | None = None
    estimate: dict[str, Any] | None = None
    risks: list[dict[str, Any]] | None = None
    user_confirmed_at: str | None = None
    confirmed_by: str | None = None


class ConfirmRequest(BaseModel):
    """明确用户确认；这是任务可下发设备的唯一路径。"""

    checklist_id: str
    accept_risks: bool = Field(description="user acknowledges listed risks")
