"""打印机和耗材卷的数据访问。"""

from __future__ import annotations

from collections.abc import Sequence

from app.models.print import MaterialSpool, PrinterDevice
from app.repositories.base import BaseRepository


class PrinterRepository(BaseRepository[PrinterDevice]):
    model = PrinterDevice

    async def list_for_owner(
        self, owner_id: str, *, offset: int, limit: int
    ) -> Sequence[PrinterDevice]:
        return await self.list(owner_id=owner_id, offset=offset, limit=limit)


class SpoolRepository(BaseRepository[MaterialSpool]):
    model = MaterialSpool

    async def list_for_owner(
        self, owner_id: str, *, offset: int, limit: int
    ) -> Sequence[MaterialSpool]:
        return await self.list(owner_id=owner_id, offset=offset, limit=limit)
