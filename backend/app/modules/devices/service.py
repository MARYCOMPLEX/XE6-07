"""打印机与耗材卷逻辑——骨架 mock 桩版。"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.base import gen_uuid
from app.models.print import MaterialSpool, PrinterDevice

from .schemas import PrinterCreate, SpoolCreate, SpoolUpdate

logger = get_logger("devices")


def _stamps() -> dict[str, datetime]:
    """瞬态桩对象补 created_at/updated_at；真实场景由 DB server_default 生成。"""
    now = datetime.now(UTC)
    return {"created_at": now, "updated_at": now}


class DeviceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # -- 打印机 -----------------------------------------------------------
    async def register_printer(self, owner_id: str, data: PrinterCreate) -> PrinterDevice:
        logger.info("devices.register_printer(mock)", owner_id=owner_id, provider=data.provider)
        # 瞬态对象不套用列默认值；显式补 status（PrinterOut 必填）与时间戳。
        return PrinterDevice(
            id=gen_uuid(),
            owner_id=owner_id,
            status="offline",
            **data.model_dump(),
            **_stamps(),
        )

    async def get_owned_printer(self, printer_id: str, owner_id: str) -> PrinterDevice:
        logger.info("devices.get_owned_printer(mock)", printer_id=printer_id, owner_id=owner_id)
        return PrinterDevice(
            id=printer_id,
            owner_id=owner_id,
            provider="mock",
            status="idle",
            **_stamps(),
        )

    async def list_printers(
        self, owner_id: str, *, offset: int, limit: int
    ) -> tuple[Sequence[PrinterDevice], int]:
        logger.info("devices.list_printers(mock)", owner_id=owner_id, offset=offset, limit=limit)
        return [], 0

    async def refresh_status(self, printer_id: str, owner_id: str) -> tuple[str, bool]:
        # 本该调 printer adapter 拉取实时状态，桩里不调 adapter，直接返回固定值。
        logger.info("devices.refresh_status(mock)", printer_id=printer_id, owner_id=owner_id)
        return "idle", True

    # -- 耗材卷 -----------------------------------------------------------
    async def add_spool(self, owner_id: str, data: SpoolCreate) -> MaterialSpool:
        logger.info("devices.add_spool(mock)", owner_id=owner_id, material=data.material)
        return MaterialSpool(id=gen_uuid(), owner_id=owner_id, **data.model_dump(), **_stamps())

    async def get_owned_spool(self, spool_id: str, owner_id: str) -> MaterialSpool:
        logger.info("devices.get_owned_spool(mock)", spool_id=spool_id, owner_id=owner_id)
        return MaterialSpool(
            id=spool_id,
            owner_id=owner_id,
            material="PLA",
            remaining_gram=1000.0,
            warning_level=50.0,
            **_stamps(),
        )

    async def update_spool(self, spool_id: str, owner_id: str, data: SpoolUpdate) -> MaterialSpool:
        logger.info("devices.update_spool(mock)", spool_id=spool_id, owner_id=owner_id)
        # is_low 依赖 remaining_gram/warning_level，SpoolOut 需时间戳；瞬态对象全部显式补齐。
        spool = MaterialSpool(
            id=spool_id,
            owner_id=owner_id,
            material="PLA",
            diameter_mm=1.75,
            remaining_gram=1000.0,
            warning_level=50.0,
            **_stamps(),
        )
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(spool, key, value)
        return spool

    async def list_spools(
        self, owner_id: str, *, offset: int, limit: int
    ) -> tuple[Sequence[MaterialSpool], int]:
        logger.info("devices.list_spools(mock)", owner_id=owner_id, offset=offset, limit=limit)
        return [], 0

    async def preflight_print(
        self,
        *,
        printer_id: str,
        owner_id: str,
        material_id: str | None = None,
        required_filament_grams: float | None = None,
    ) -> None:
        # 本该调 printer adapter 做打印前检查，桩里不调 adapter，只 log 后返回。
        logger.info(
            "devices.preflight_print(mock)",
            printer_id=printer_id,
            owner_id=owner_id,
            material_id=material_id,
            required_filament_grams=required_filament_grams,
        )
        return None

    @staticmethod
    def is_low(spool: MaterialSpool) -> bool:
        return spool.remaining_gram <= spool.warning_level
