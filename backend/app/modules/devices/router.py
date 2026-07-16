"""打印机与耗材卷 API。

注册只保存连接元数据和凭据引用，不保存 secret 值。实时打印机状态通过 PrinterAdapter
代理获取；耗材响应会带上计算得到的 ``low`` 标记，供库存 UI 使用。
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.core.deps import CurrentUserDep, DbSession, PaginationDep
from app.models.print import MaterialSpool
from app.schemas.common import OffsetPage

from .schemas import (
    PrinterCreate,
    PrinterOut,
    PrinterStatusOut,
    SpoolCreate,
    SpoolOut,
    SpoolUpdate,
)
from .service import DeviceService

router = APIRouter(prefix="/devices", tags=["devices"])


# -- 打印机 ---------------------------------------------------------------
@router.post("/printers", response_model=PrinterOut, status_code=status.HTTP_201_CREATED)
async def register_printer(body: PrinterCreate, db: DbSession, user: CurrentUserDep) -> PrinterOut:
    printer = await DeviceService(db).register_printer(user.id, body)
    return PrinterOut.model_validate(printer)


@router.get("/printers", response_model=OffsetPage[PrinterOut])
async def list_printers(
    db: DbSession, user: CurrentUserDep, pg: PaginationDep
) -> OffsetPage[PrinterOut]:
    items, total = await DeviceService(db).list_printers(user.id, offset=pg.offset, limit=pg.size)
    return OffsetPage[PrinterOut](
        items=[PrinterOut.model_validate(i) for i in items],
        total=total,
        page=pg.page,
        size=pg.size,
    )


@router.get("/printers/{printer_id}/status", response_model=PrinterStatusOut)
async def printer_status(printer_id: str, db: DbSession, user: CurrentUserDep) -> PrinterStatusOut:
    state, online = await DeviceService(db).refresh_status(printer_id, user.id)
    return PrinterStatusOut(printer_id=printer_id, status=state, online=online)


# -- 耗材卷 ---------------------------------------------------------------
@router.post("/spools", response_model=SpoolOut, status_code=status.HTTP_201_CREATED)
async def add_spool(body: SpoolCreate, db: DbSession, user: CurrentUserDep) -> SpoolOut:
    spool = await DeviceService(db).add_spool(user.id, body)
    return _spool_out(spool)


@router.patch("/spools/{spool_id}", response_model=SpoolOut)
async def update_spool(
    spool_id: str, body: SpoolUpdate, db: DbSession, user: CurrentUserDep
) -> SpoolOut:
    spool = await DeviceService(db).update_spool(spool_id, user.id, body)
    return _spool_out(spool)


@router.get("/spools", response_model=OffsetPage[SpoolOut])
async def list_spools(
    db: DbSession, user: CurrentUserDep, pg: PaginationDep
) -> OffsetPage[SpoolOut]:
    items, total = await DeviceService(db).list_spools(user.id, offset=pg.offset, limit=pg.size)
    return OffsetPage[SpoolOut](
        items=[_spool_out(i) for i in items],
        total=total,
        page=pg.page,
        size=pg.size,
    )


def _spool_out(spool: MaterialSpool) -> SpoolOut:
    out = SpoolOut.model_validate(spool)
    out.low = DeviceService.is_low(spool)
    return out
