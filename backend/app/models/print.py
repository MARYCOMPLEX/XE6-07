"""边缘设备、耗材、切片和打印任务模型。

SliceJob 来自已审计版本；PrintChecklist 是人工确认门禁，没有确认记录就不能下发设备。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import JobStatus, PrintJobStatus


class PrinterDevice(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "printer_devices"

    owner_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)  # octoprint/moonraker/mock
    model: Mapped[str | None] = mapped_column(String(128), default=None)
    build_volume_mm: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=None)
    nozzle_mm: Mapped[float | None] = mapped_column(Float, default=None)
    status: Mapped[str] = mapped_column(String(32), default="offline", nullable=False)
    capabilities: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=None)
    endpoint: Mapped[str | None] = mapped_column(String(512), default=None)
    # secret 引用，只保存名称，不保存密钥值。
    credential_ref: Mapped[str | None] = mapped_column(String(128), default=None)


class MaterialSpool(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "material_spools"

    owner_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    material: Mapped[str] = mapped_column(String(32), nullable=False)  # PLA/PETG...
    color: Mapped[str | None] = mapped_column(String(32), default=None)
    diameter_mm: Mapped[float] = mapped_column(Float, default=1.75, nullable=False)
    remaining_gram: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    location: Mapped[str | None] = mapped_column(String(64), default=None)
    warning_level: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)


class SliceJob(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "slice_jobs"

    revision_id: Mapped[str] = mapped_column(
        ForeignKey("asset_revisions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    slicer_engine: Mapped[str] = mapped_column(String(32), nullable=False)  # orca/bambu/prusa
    printer_id: Mapped[str | None] = mapped_column(
        ForeignKey("printer_devices.id", ondelete="SET NULL"), default=None
    )
    profile: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=None)  # SliceProfile
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, native_enum=False, length=16),
        default=JobStatus.pending,
        nullable=False,
        index=True,
    )
    report_uri: Mapped[str | None] = mapped_column(String(512), default=None)
    gcode_uri: Mapped[str | None] = mapped_column(String(512), default=None)
    # 切片器返回的时间、耗材和成本估算。
    estimate: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=None)
    is_stale: Mapped[bool] = mapped_column(default=False, nullable=False)
    trace_id: Mapped[str | None] = mapped_column(String(64), index=True, default=None)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)


class PrintChecklist(UUIDMixin, TimestampMixin, Base):
    """物理执行前的人工确认门禁。"""

    __tablename__ = "print_checklists"

    slice_job_id: Mapped[str] = mapped_column(
        ForeignKey("slice_jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    printer_id: Mapped[str] = mapped_column(
        ForeignKey("printer_devices.id", ondelete="RESTRICT"), nullable=False
    )
    material_id: Mapped[str | None] = mapped_column(
        ForeignKey("material_spools.id", ondelete="SET NULL"), default=None
    )
    estimate: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=None)
    risks: Mapped[list[Any] | None] = mapped_column(JSONB, default=None)
    user_confirmed_at: Mapped[str | None] = mapped_column(String(32), default=None)
    confirmed_by: Mapped[str | None] = mapped_column(String(32), default=None)


class PrintJob(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "print_jobs"
    __table_args__ = (UniqueConstraint("checklist_id", name="uq_print_job_checklist"),)

    checklist_id: Mapped[str] = mapped_column(
        ForeignKey("print_checklists.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    printer_id: Mapped[str] = mapped_column(
        ForeignKey("printer_devices.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[PrintJobStatus] = mapped_column(
        Enum(PrintJobStatus, native_enum=False, length=16),
        default=PrintJobStatus.queued,
        nullable=False,
        index=True,
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    started_at: Mapped[str | None] = mapped_column(String(32), default=None)
    completed_at: Mapped[str | None] = mapped_column(String(32), default=None)
    actual_time_s: Mapped[int | None] = mapped_column(Integer, default=None)
    actual_filament_g: Mapped[float | None] = mapped_column(Float, default=None)
    pickup_code: Mapped[str | None] = mapped_column(String(16), default=None)
    # 设备侧返回的任务引用，用于取消或追踪。
    device_job_ref: Mapped[str | None] = mapped_column(String(128), default=None)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    trace_id: Mapped[str | None] = mapped_column(String(64), index=True, default=None)
