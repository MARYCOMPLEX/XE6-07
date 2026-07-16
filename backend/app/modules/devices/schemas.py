"""打印机与耗材卷数据模式。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel, TimestampedOut


# -- 打印机 ---------------------------------------------------------------
class PrinterCreate(BaseModel):
    provider: str = Field(description="octoprint | moonraker | mock | bambu")
    model: str | None = None
    build_volume_mm: dict[str, float] | None = None
    nozzle_mm: float | None = None
    endpoint: str | None = None
    # 凭据 secret 的名称，不保存 secret 值本身。
    credential_ref: str | None = None
    capabilities: dict[str, Any] | None = None


class PrinterOut(TimestampedOut):
    owner_id: str
    provider: str
    model: str | None = None
    build_volume_mm: dict[str, float] | None = None
    nozzle_mm: float | None = None
    status: str
    capabilities: dict[str, Any] | None = None


class PrinterStatusOut(ORMModel):
    printer_id: str
    status: str
    online: bool


# -- 耗材卷 ---------------------------------------------------------------
class SpoolCreate(BaseModel):
    material: str = Field(description="PLA | PETG | ...")
    color: str | None = None
    diameter_mm: float = 1.75
    remaining_gram: float = Field(default=0.0, ge=0.0)
    location: str | None = None
    warning_level: float = 50.0


class SpoolUpdate(BaseModel):
    remaining_gram: float | None = Field(default=None, ge=0.0)
    location: str | None = None
    warning_level: float | None = None


class SpoolOut(TimestampedOut):
    owner_id: str
    material: str
    color: str | None = None
    diameter_mm: float
    remaining_gram: float
    location: str | None = None
    warning_level: float
    low: bool = False
